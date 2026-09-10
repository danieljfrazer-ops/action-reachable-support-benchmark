"""
sim_d9.py -- Independent reproduction / refutation of D-9.1 and verification of D-9.
Written by Gemini for Task 1 of D-9 Verification (7 September 2026).
Reuses and extends our review3 simulation infrastructure. Does not import from review3-claude-opus/.

Evaluates:
  1. Draft-2 statistic: per (c, h) Mann-Whitney z of |increments| (probe vs task-policy null); a_c = signed max over horizons of |z|.
  2. D-9.1 statistic: per (c, h, k) rank-sum z of SIGNED increments (+e_k probes vs -e_k probes); a_c = max over (k, h) of |z|.
  3. Comparator: channel-agnostic linear predictor on fault-free data; per-channel support score = two-sided standardised innovation-shift statistic (Codex definition).
  4. Comparator (ActInfo): windowed innovation variance reduction (Opus definition).
  5. Probed comparators: identical comparators on probe-injected streams.
  6. Calibrators: PAVA isotonic calibrator on 40 calibration episodes (half event-carrying).
  7. Evaluation:
     - Offsets: 200, 500, 1000 after t=1000.
     - Cells: Confounder present AND absent; N_x in {10, 30}.
     - Seeds: >= 30 scored seeds + 30 no-event control seeds.
     - Metrics: Threshold-free AUC and AUPRC against S^obs,eps; F1 @ 0.5 and F1 @ optimal operating point from calibration split.
     - Mean a_c by channel class: direct (b0, b2), reachable-indirect (b1, b3, d0, d1), non-reachable (w, x, padding).
     - Ablation: W_u = 0.
"""

import sys, os, math, time
import numpy as np

# --------------------------------------------------------------------------------------------------
# Registry constants (stage-0a-contract-v3.4.md section 0)
# --------------------------------------------------------------------------------------------------
EPS = 0.05
H_SUPPORT = 3
H_SET = (1, 2, 3)
A_MAG = 1.0          # Probe magnitude
C_MIN = 0.2
RHO_MAX = 0.95
RHO_U = 0.8
A_MAX = 2.0
RHO_MIN = 0.4
RHO_CL = 0.98
N_B, N_D, N_W, K = 4, 2, 4, 2
SIG_B = SIG_D = SIG_W = SIG_X = 0.1
SIG_O = 0.05
SIG_A = 0.1
SIG_U = 1.0
F_CONF = 0.5
EPISODE_LEN = 2000
EVENT_T = 1000
OFFSETS = (200, 500, 1000)
PROBE_BUDGET = 0.05
PI = 20              # Period = 1 / 0.05
W_STEPS = 500
Z_CAP = 8.0
A_ABSENT = -Z_CAP
N_MIN = 10
R_CAL = 40           # 40 calibration episodes (half event-carrying)
N_SEEDS = 30         # 30 scored seeds + 30 no-event controls

T0 = time.time()
def log(*args):
    print(f"[{time.time()-T0:6.1f}s]", *args)
    sys.stdout.flush()

# --------------------------------------------------------------------------------------------------
# SCM Instance & Environment (Contract B, Family L)
# --------------------------------------------------------------------------------------------------
class Instance:
    def __init__(self, N_x=10, confounded=True, W_u_val=0.45, seed=0):
        self.N_x = N_x
        self.confounded = confounded
        self.W_u_val = W_u_val
        self.N_b, self.N_d, self.N_w, self.K = N_B, N_D, N_W, K
        self.N_z = self.N_b + self.N_d + self.N_w + N_x
        self.C = self.N_z + 2  # 2 padding channels

        # Dynamics matrices
        # Block 0 (b0, b1) driven by a0; Block 1 (b2, b3) driven by a1
        self.A_b = np.array([
            [0.85, 0.00, 0.00, 0.00],
            [0.30, 0.85, 0.00, 0.00],
            [0.00, 0.00, 0.85, 0.00],
            [0.00, 0.00, 0.30, 0.85]
        ])
        self.B_pre = np.array([
            [1.0, 0.0],
            [0.0, 0.0],
            [0.0, 1.0],
            [0.0, 0.0]
        ])
        # Complete loss of actuator 0
        self.B_post = np.array([
            [0.0, 0.0],
            [0.0, 0.0],
            [0.0, 1.0],
            [0.0, 0.0]
        ])

        # Downstream latents d: d0 <- b0, d1 <- b2
        self.C_d = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0]
        ])
        self.A_d = np.diag([0.50, 0.50])

        # World latents w
        self.A_w = np.diag([0.90, 0.85, 0.80, 0.75])

        # Distractor latents x
        self.A_x = 0.50 * np.eye(N_x)

        # Confounder coupling G: f_conf fraction of x are children of u
        self.n_conf = int(round(F_CONF * N_x))
        self.G = np.zeros((N_x, 1))
        if confounded:
            self.G[:self.n_conf, 0] = 1.0

        # Policy: a = clip(W_o o + W_u u + noise)
        self.W_o = np.zeros((self.K, self.C))
        self.W_o[0, 0] = -0.15  # negative feedback on b0
        self.W_o[1, 2] = -0.15  # negative feedback on b2
        self.W_u = np.array([[W_u_val], [W_u_val]])

        # Observation mapping: 1-to-1 for latents, -1 for padding
        self.assign = np.array(list(range(self.N_z)) + [-1, -1])
        self.gain = np.ones(self.C)
        self.avail = np.ones(self.C, bool)

        # Channel groups
        self.ch_direct = [0, 2]                 # b0, b2
        self.ch_indirect = [1, 3, 4, 5]         # b1, b3, d0, d1
        self.ch_w = list(range(6, 10))
        self.ch_x = list(range(10, 10 + N_x))
        self.ch_pad = [self.C - 2, self.C - 1]
        self.ch_nonreach = self.ch_w + self.ch_x + self.ch_pad

        # Ground truth support S^obs,eps
        self.S_pre = np.zeros(self.C, bool)
        self.S_pre[self.ch_direct + self.ch_indirect] = True  # 6 channels

        self.S_post = np.zeros(self.C, bool)
        self.S_post[[2, 3, 5]] = True  # b2, b3, d1 remain reachable; b0, b1, d0 lost

    def closed_loop_radius(self, B):
        n = self.N_z
        F = np.zeros((n, n))
        F[:4, :4] = self.A_b
        F[4:6, :4] = self.C_d
        F[4:6, 4:6] = self.A_d
        F[6:10, 6:10] = self.A_w
        F[10:, 10:] = self.A_x

        Bz = np.zeros((n, self.K))
        Bz[:4, :] = B

        Amap = np.zeros((self.K, n))
        for c in range(self.C):
            j = self.assign[c]
            if j >= 0:
                Amap[:, j] += self.W_o[:, c] * self.gain[c] * self.avail[c]

        M = np.zeros((n + 1, n + 1))
        M[:n, :n] = F + Bz @ Amap
        M[:n, n:n+1] = Bz @ self.W_u + np.vstack([np.zeros((10, 1)), self.G])
        M[n, n] = RHO_U
        return float(np.max(np.abs(np.linalg.eigvals(M))))


def simulate_episode(inst, seed, has_event=True, probe=True, T=EPISODE_LEN):
    rng = np.random.default_rng(seed)
    N_z, C, K = inst.N_z, inst.C, inst.K
    
    z = np.zeros(N_z)
    u = rng.normal(0.0, SIG_U / math.sqrt(1.0 - RHO_U**2))
    
    obs = np.zeros((T + 1, C))
    act = np.zeros((T, K))
    probe_flag = np.zeros(T, bool)
    probe_dir = np.full(T, -1, int)  # 0: +e0, 1: -e0, 2: +e1, 3: -e1
    
    A_PROBES = [(0, +1.0), (0, -1.0), (1, +1.0), (1, -1.0)]
    
    used_probes = 0
    last_probe_t = -PI
    n_sat = 0
    
    F = np.zeros((N_z, N_z))
    F[:4, :4] = inst.A_b
    F[4:6, :4] = inst.C_d
    F[4:6, 4:6] = inst.A_d
    F[6:10, 6:10] = inst.A_w
    F[10:, 10:] = inst.A_x
    
    noise_sig = np.zeros(N_z)
    noise_sig[:4] = SIG_B
    noise_sig[4:6] = SIG_D
    noise_sig[6:10] = SIG_W
    noise_sig[10:] = SIG_X
    
    G_full = np.zeros(N_z)
    G_full[10:] = inst.G[:, 0]
    
    for t in range(T + 1):
        o = np.zeros(C)
        for c in range(C):
            j = inst.assign[c]
            if j >= 0 and inst.avail[c]:
                o[c] = inst.gain[c] * z[j]
        o += rng.normal(0.0, SIG_O, C)
        obs[t] = o
        
        if t == T:
            break
            
        B_curr = inst.B_post if (has_event and t >= EVENT_T) else inst.B_pre
        
        is_probe = False
        if probe and t >= PI and (used_probes + 1 <= math.floor(PROBE_BUDGET * t)) and (t - last_probe_t >= PI) and (t + max(H_SET) <= T):
            is_probe = True
            
        if is_probe:
            di = int(rng.integers(0, 4))
            k_act, sgn = A_PROBES[di]
            a = np.zeros(K)
            a[k_act] = sgn * A_MAG
            used_probes += 1
            last_probe_t = t
            probe_flag[t] = True
            probe_dir[t] = di
        else:
            a_raw = inst.W_o @ o + inst.W_u @ np.array([u]) + rng.normal(0.0, SIG_A, K)
            a = np.clip(a_raw, -A_MAX, A_MAX)
            if np.any(np.abs(a_raw) > A_MAX):
                n_sat += 1
                
        act[t] = a
        
        Bz = np.zeros(N_z)
        Bz[:4] = B_curr @ a
        z = F @ z + Bz + G_full * u + rng.normal(0.0, noise_sig, N_z)
        u = RHO_U * u + rng.normal(0.0, SIG_U)
        
    return {
        "obs": obs,
        "act": act,
        "probe": probe_flag,
        "pdir": probe_dir,
        "sat_frac": n_sat / T,
        "used": used_probes
    }


# --------------------------------------------------------------------------------------------------
# Fast Vectorized Mann-Whitney U & Rank-Sum Statistics
# --------------------------------------------------------------------------------------------------
def fast_mann_whitney_z(P, N):
    nP, C = P.shape
    nN = N.shape[0]
    n = nP + nN
    arr = np.vstack([P, N])
    
    order = np.argsort(arr, axis=0, kind="mergesort")
    ranks = np.empty((n, C), dtype=float)
    base = np.broadcast_to(np.arange(1, n + 1, dtype=float)[:, None], (n, C))
    np.put_along_axis(ranks, order, base, axis=0)
    
    srt = np.take_along_axis(arr, order, axis=0)
    tie_diff = np.diff(srt, axis=0) == 0
    tie_cols = np.nonzero(tie_diff.any(axis=0))[0]
    tie_term = np.zeros(C)
    
    for c in tie_cols:
        col = srt[:, c]
        i = 0
        while i < n:
            j = i
            while j + 1 < n and col[j + 1] == col[i]:
                j += 1
            if j > i:
                avg = 0.5 * (i + 1 + j + 1)
                idx = order[i:j + 1, c]
                ranks[idx, c] = avg
                m = j - i + 1
                tie_term[c] += m**3 - m
            i = j + 1
            
    R_P = ranks[:nP].sum(axis=0)
    U = R_P - nP * (nP + 1) / 2.0
    kappa = 1.0 - tie_term / (n * (n * n - 1.0) + 1e-12)
    var = (nP * nN * (n + 1) / 12.0) * kappa
    
    z = np.zeros(C)
    valid = var > 1e-12
    z[valid] = (U[valid] - nP * nN / 2.0) / np.sqrt(var[valid])
    return z


# --------------------------------------------------------------------------------------------------
# (A) Draft-2 Statistic: probe vs task-policy null
# --------------------------------------------------------------------------------------------------
def compute_draft2_a(obs, pflag, t_target, win=W_STEPS):
    C = obs.shape[1]
    p_anchors = np.nonzero(pflag)[0]
    
    closes = p_anchors + max(H_SET)
    valid_closes = closes[closes <= t_target]
    if len(valid_closes) == 0:
        return np.full(C, A_ABSENT)
    t_close = valid_closes[-1]
    lo = t_close - win
    
    keep = p_anchors[(p_anchors > lo) & (p_anchors <= t_close - max(H_SET))]
    if len(keep) < N_MIN:
        return np.full(C, A_ABSENT)
        
    nulls = []
    for m in range(1, 5):
        nulls.append(keep - m * max(H_SET))
    nulls = np.concatenate(nulls)
    nulls = nulls[nulls > lo]
    if len(nulls) == 0:
        return np.full(C, A_ABSENT)
        
    zs = []
    for h in H_SET:
        P_inc = np.abs(obs[keep + h] - obs[keep])
        N_inc = np.abs(obs[nulls + h] - obs[nulls])
        zh = fast_mann_whitney_z(P_inc, N_inc)
        zs.append(zh)
        
    a = np.zeros(C)
    best_abs = np.zeros(C)
    for zh in zs:
        better = np.abs(zh) > best_abs + 1e-12
        a[better] = zh[better]
        best_abs[better] = np.abs(zh[better])
        
    a = np.clip(a, -Z_CAP, Z_CAP)
    
    all_P = np.vstack([np.abs(obs[keep + h] - obs[keep]) for h in H_SET])
    all_N = np.vstack([np.abs(obs[nulls + h] - obs[nulls]) for h in H_SET])
    degen = (all_P.max(0) == all_P.min(0)) & (all_N.max(0) == all_N.min(0)) & (all_P.max(0) == all_N.max(0))
    a[degen] = A_ABSENT
    return a


# --------------------------------------------------------------------------------------------------
# (B) D-9.1 Statistic: signed contrast (+e_k probes vs -e_k probes)
# --------------------------------------------------------------------------------------------------
def compute_d9_signrand_a(obs, pflag, pdir, t_target, win=W_STEPS):
    C = obs.shape[1]
    p_anchors = np.nonzero(pflag)[0]
    closes = p_anchors + max(H_SET)
    valid_closes = closes[closes <= t_target]
    if len(valid_closes) == 0:
        return np.zeros(C)
    t_close = valid_closes[-1]
    lo = t_close - win
    
    keep = p_anchors[(p_anchors > lo) & (p_anchors <= t_close - max(H_SET))]
    if len(keep) < N_MIN:
        return np.zeros(C)
        
    d = pdir[keep]
    a = np.zeros(C)
    
    for k in range(K):
        pos_idx = keep[d == 2 * k]      # +e_k
        neg_idx = keep[d == 2 * k + 1]  # -e_k
        if len(pos_idx) < 3 or len(neg_idx) < 3:
            continue
            
        for h in H_SET:
            P_inc = obs[pos_idx + h] - obs[pos_idx]
            N_inc = obs[neg_idx + h] - obs[neg_idx]
            z = fast_mann_whitney_z(P_inc, N_inc)
            a = np.maximum(a, np.abs(z))
            
    a = np.clip(a, 0.0, Z_CAP)
    return a


# --------------------------------------------------------------------------------------------------
# Comparators: Channel-Agnostic Linear Predictor
# --------------------------------------------------------------------------------------------------
class LinearPredictorComparator:
    """
    Fitted on fault-free in-distribution data: o_{t+1} ~ W [o_t; a_t; 1].
    Provides two support score statistics:
      1. score_shift (Codex): s_c - Delta_c, where s_c = ||W_{a,c}||_2 / sd_c,
         Delta_c = |mean(z_{win,c})| + |ln max(std(z_{win,c}), 1e-3)|.
      2. score_actinfo (Opus): 1 - SSE_full,c / SSE_noaction,c over trailing window.
    """
    def __init__(self):
        self.W = None
        self.W0 = None
        self.sd = None
        self.action_sens = None
        
    def fit(self, episodes):
        X, X0, Y = [], [], []
        for ep in episodes:
            o, a = ep["obs"], ep["act"]
            T = a.shape[0]
            X.append(np.column_stack([o[:T], a, np.ones(T)]))
            X0.append(np.column_stack([o[:T], np.ones(T)]))
            Y.append(o[1:T + 1])
        X = np.vstack(X)
        X0 = np.vstack(X0)
        Y = np.vstack(Y)
        
        self.W, *_ = np.linalg.lstsq(X, Y, rcond=None)
        self.W0, *_ = np.linalg.lstsq(X0, Y, rcond=None)
        
        pred = X @ self.W
        self.sd = np.maximum((Y - pred).std(axis=0), 1e-4)
        
        W_a = self.W[-K-1:-1, :]  # (K, C)
        self.action_sens = np.linalg.norm(W_a, axis=0) / self.sd
        
    def compute_support_score(self, ep, t_target, win=W_STEPS):
        """Two-sided standardised innovation-shift score."""
        o, a = ep["obs"], ep["act"]
        T = a.shape[0]
        t = min(t_target, T)
        lo = max(0, t - win)
        X_win = np.column_stack([o[lo:t], a[lo:t], np.ones(t - lo)])
        Y_win = o[lo + 1:t + 1]
        pred = X_win @ self.W
        res = (Y_win - pred) / self.sd[None, :]
        
        mean_z = np.abs(res.mean(axis=0))
        std_z = np.abs(np.log(np.maximum(res.std(axis=0), 1e-3)))
        delta = mean_z + std_z
        score = self.action_sens - delta
        return np.clip(score, -Z_CAP, Z_CAP)

    def compute_actinfo_score(self, ep, t_target, win=W_STEPS):
        """Windowed variance reduction score (Opus R3-1 baseline)."""
        o, a = ep["obs"], ep["act"]
        T = a.shape[0]
        t = min(t_target, T)
        lo = max(0, t - win)
        X_win = np.column_stack([o[lo:t], a[lo:t], np.ones(t - lo)])
        X0_win = np.column_stack([o[lo:t], np.ones(t - lo)])
        Y_win = o[lo + 1:t + 1]
        
        r = Y_win - X_win @ self.W
        r0 = Y_win - X0_win @ self.W0
        
        num = np.sum(r**2, axis=0)
        den = np.sum(r0**2, axis=0)
        score = np.where(den > 1e-12, 1.0 - num / np.maximum(den, 1e-12), 0.0)
        return np.clip(score, -1.0, 1.0)


# --------------------------------------------------------------------------------------------------
# PAVA Isotonic Calibrator
# --------------------------------------------------------------------------------------------------
def pava_fit(x, y):
    order = np.argsort(x, kind="mergesort")
    xs = np.asarray(x)[order]
    ys = np.asarray(y, float)[order]
    
    val, wt = [], []
    for v in ys:
        val.append(v)
        wt.append(1.0)
        while len(val) > 1 and val[-2] > val[-1]:
            v2 = val.pop(); w2 = wt.pop()
            v1 = val.pop(); w1 = wt.pop()
            val.append((v1 * w1 + v2 * w2) / (w1 + w2))
            wt.append(w1 + w2)
            
    fit = np.empty(len(ys))
    i = 0
    for v, w in zip(val, wt):
        fit[i:i + int(w)] = v
        i += int(w)
    return xs, fit

def pava_apply(knots_x, knots_y, v):
    idx = np.searchsorted(knots_x, v, side="right") - 1
    idx = np.clip(idx, 0, len(knots_y) - 1)
    return np.clip(knots_y[idx], 0.0, 1.0)


# --------------------------------------------------------------------------------------------------
# Evaluation Metrics: AUC, AUPRC (with exact tie handling), F1
# --------------------------------------------------------------------------------------------------
def compute_auc(scores, labels):
    pos = np.asarray(labels, bool)
    nP = int(pos.sum())
    nN = len(pos) - nP
    if nP == 0 or nN == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    r = np.empty(len(scores), float)
    r[order] = np.arange(1, len(scores) + 1, dtype=float)
    
    srt = np.sort(scores)
    i = 0
    while i < len(srt):
        j = i
        while j + 1 < len(srt) and srt[j + 1] == srt[i]:
            j += 1
        if j > i:
            r[order[i:j + 1]] = 0.5 * (i + 1 + j + 1)
        i = j + 1
    U = r[pos].sum() - nP * (nP + 1) / 2.0
    return float(U / (nP * nN))

def compute_auprc(scores, labels):
    """Average Precision with exact threshold grouping for ties (standard scikit-learn equivalent)."""
    pos = np.asarray(labels, bool)
    P = int(pos.sum())
    if P == 0:
        return float("nan")
    if P == len(labels):
        return 1.0
        
    order = np.argsort(-scores, kind="mergesort")
    scores_sorted = scores[order]
    y_sorted = pos[order]
    
    distinct = np.where(np.diff(scores_sorted))[0]
    threshold_idxs = np.r_[distinct, len(scores) - 1]
    
    tp = np.cumsum(y_sorted)[threshold_idxs]
    fp = np.cumsum(~y_sorted)[threshold_idxs]
    
    recall = tp / P
    precision = tp / (tp + fp)
    
    rec_diff = np.diff(np.concatenate([[0.0], recall]))
    return float(np.sum(rec_diff * precision))

def compute_f1(pred, labels):
    pred = np.asarray(pred, bool)
    pos = np.asarray(labels, bool)
    tp = np.sum(pred & pos)
    fp = np.sum(pred & ~pos)
    fn = np.sum(~pred & pos)
    denom = 2 * tp + fp + fn
    return float(2 * tp / denom) if denom > 0 else 0.0


# --------------------------------------------------------------------------------------------------
# Calibration & Tuning of Operating Points
# --------------------------------------------------------------------------------------------------
def run_calibration(inst, lp, lp_probed):
    ep_probed_list = []
    ep_plain_list = []
    
    for i in range(R_CAL):
        has_ev = (i < R_CAL // 2)
        ep_p = simulate_episode(inst, 100_000 + i, has_event=has_ev, probe=True)
        ep_n = simulate_episode(inst, 100_000 + i, has_event=has_ev, probe=False)
        ep_probed_list.append((ep_p, has_ev))
        ep_plain_list.append((ep_n, has_ev))
        
    fault_free_plain = [ep for ep, ev in ep_plain_list if not ev]
    fault_free_probe = [ep for ep, ev in ep_probed_list if not ev]
    lp.fit(fault_free_plain)
    lp_probed.fit(fault_free_probe)
    
    grid = np.arange(PI * 2, EPISODE_LEN + 1, PI * 5)
    
    X_d2, Y_d2 = [], []
    X_d9, Y_d9 = [], []
    X_comp, Y_comp = [], []
    X_act, Y_act = [], []
    X_prb, Y_prb = [], []
    
    for ep_p, has_ev in ep_probed_list:
        for t in grid:
            y = inst.S_post if (has_ev and t >= EVENT_T) else inst.S_pre
            a_d2 = compute_draft2_a(ep_p["obs"], ep_p["probe"], t)
            a_d9 = compute_d9_signrand_a(ep_p["obs"], ep_p["probe"], ep_p["pdir"], t)
            s_prb = lp_probed.compute_support_score(ep_p, t)
            
            X_d2.append(a_d2); Y_d2.append(y.astype(float))
            X_d9.append(a_d9); Y_d9.append(y.astype(float))
            X_prb.append(s_prb); Y_prb.append(y.astype(float))
            
    for ep_n, has_ev in ep_plain_list:
        for t in grid:
            y = inst.S_post if (has_ev and t >= EVENT_T) else inst.S_pre
            s_comp = lp.compute_support_score(ep_n, t)
            s_act = lp.compute_actinfo_score(ep_n, t)
            X_comp.append(s_comp); Y_comp.append(y.astype(float))
            X_act.append(s_act); Y_act.append(y.astype(float))
            
    kx_d2, ky_d2 = pava_fit(np.concatenate(X_d2), np.concatenate(Y_d2))
    kx_d9, ky_d9 = pava_fit(np.concatenate(X_d9), np.concatenate(Y_d9))
    kx_comp, ky_comp = pava_fit(np.concatenate(X_comp), np.concatenate(Y_comp))
    kx_act, ky_act = pava_fit(np.concatenate(X_act), np.concatenate(Y_act))
    kx_prb, ky_prb = pava_fit(np.concatenate(X_prb), np.concatenate(Y_prb))
    
    def find_best_threshold(scores_list, y_list, kx, ky):
        best_th, best_f1 = 0.5, -1.0
        candidate_ths = np.linspace(0.05, 0.95, 19)
        for th in candidate_ths:
            f1s = []
            for sc, y in zip(scores_list, y_list):
                p = pava_apply(kx, ky, sc)
                f1s.append(compute_f1(p >= th, y))
            mf1 = np.mean(f1s)
            if mf1 > best_f1:
                best_f1 = mf1
                best_th = th
        return best_th
        
    th_d2 = find_best_threshold(X_d2, Y_d2, kx_d2, ky_d2)
    th_d9 = find_best_threshold(X_d9, Y_d9, kx_d9, ky_d9)
    th_comp = find_best_threshold(X_comp, Y_comp, kx_comp, ky_comp)
    th_act = find_best_threshold(X_act, Y_act, kx_act, ky_act)
    th_prb = find_best_threshold(X_prb, Y_prb, kx_prb, ky_prb)
    
    calibrators = {
        "draft2": (kx_d2, ky_d2, th_d2),
        "d9_signrand": (kx_d9, ky_d9, th_d9),
        "comparator": (kx_comp, ky_comp, th_comp),
        "comparator_actinfo": (kx_act, ky_act, th_act),
        "comparator_probed": (kx_prb, ky_prb, th_prb),
    }
    return calibrators


# --------------------------------------------------------------------------------------------------
# Experiment Runner for One Cell
# --------------------------------------------------------------------------------------------------
def run_cell_experiment(N_x=10, confounded=True, W_u_val=0.45, n_seeds=N_SEEDS, tag=""):
    log(f"Starting cell: {tag} (N_x={N_x}, confounded={confounded}, W_u={W_u_val})")
    inst = Instance(N_x=N_x, confounded=confounded, W_u_val=W_u_val)
    
    rho_cl = inst.closed_loop_radius(inst.B_pre)
    ep_check = simulate_episode(inst, seed=999, has_event=False, probe=False)
    corr_ax = 0.0
    if confounded:
        aa = ep_check["act"]
        xx = ep_check["obs"][:EPISODE_LEN, inst.ch_x]
        for k in range(K):
            for j in range(inst.n_conf):
                corr_ax = max(corr_ax, abs(np.corrcoef(aa[:, k], xx[:, j])[0, 1]))
    sat_frac = ep_check["sat_frac"]
    log(f"  Certifications: rho_cl={rho_cl:.3f} (<=0.98), sat_frac={sat_frac:.4f} (<0.05), max|corr(a,x)|={corr_ax:.3f} (>=0.40)")

    lp = LinearPredictorComparator()
    lp_probed = LinearPredictorComparator()
    cal = run_calibration(inst, lp, lp_probed)
    log(f"  Calibration complete. Optimal thresholds: draft2={cal['draft2'][2]:.2f}, d9={cal['d9_signrand'][2]:.2f}, comp={cal['comparator'][2]:.2f}, actinfo={cal['comparator_actinfo'][2]:.2f}, prb={cal['comparator_probed'][2]:.2f}")

    results = []
    
    for s in range(n_seeds):
        ep_p = simulate_episode(inst, 200_000 + s, has_event=True, probe=True)
        ep_n = simulate_episode(inst, 200_000 + s, has_event=True, probe=False)
        
        ep_p_ctrl = simulate_episode(inst, 300_000 + s, has_event=False, probe=True)
        ep_n_ctrl = simulate_episode(inst, 300_000 + s, has_event=False, probe=False)
        
        for off in OFFSETS:
            t = EVENT_T + off
            
            # --- Event evaluation ---
            a_d2 = compute_draft2_a(ep_p["obs"], ep_p["probe"], t)
            a_d9 = compute_d9_signrand_a(ep_p["obs"], ep_p["probe"], ep_p["pdir"], t)
            s_comp = lp.compute_support_score(ep_n, t)
            s_act = lp.compute_actinfo_score(ep_n, t)
            s_prb = lp_probed.compute_support_score(ep_p, t)
            
            p_d2 = pava_apply(cal["draft2"][0], cal["draft2"][1], a_d2)
            p_d9 = pava_apply(cal["d9_signrand"][0], cal["d9_signrand"][1], a_d9)
            p_comp = pava_apply(cal["comparator"][0], cal["comparator"][1], s_comp)
            p_act = pava_apply(cal["comparator_actinfo"][0], cal["comparator_actinfo"][1], s_act)
            p_prb = pava_apply(cal["comparator_probed"][0], cal["comparator_probed"][1], s_prb)
            
            y_post = inst.S_post
            
            scores_arms = {
                "draft2": (a_d2, p_d2, cal["draft2"][2]),
                "d9_signrand": (a_d9, p_d9, cal["d9_signrand"][2]),
                "comparator": (s_comp, p_comp, cal["comparator"][2]),
                "comparator_actinfo": (s_act, p_act, cal["comparator_actinfo"][2]),
                "comparator_probed": (s_prb, p_prb, cal["comparator_probed"][2]),
            }
            
            for arm_name, (raw_sc, p_sc, opt_th) in scores_arms.items():
                results.append({
                    "seed": s,
                    "offset": off,
                    "control": False,
                    "arm": arm_name,
                    "auc": compute_auc(raw_sc, y_post),
                    "auprc": compute_auprc(raw_sc, y_post),
                    "f1_05": compute_f1(p_sc >= 0.5, y_post),
                    "f1_opt": compute_f1(p_sc >= opt_th, y_post),
                    "a_direct": float(raw_sc[inst.ch_direct].mean()),
                    "a_indirect": float(raw_sc[inst.ch_indirect].mean()),
                    "a_nonreach": float(raw_sc[inst.ch_nonreach].mean()),
                })
                
            # --- No-event control evaluation ---
            a_d2_c = compute_draft2_a(ep_p_ctrl["obs"], ep_p_ctrl["probe"], t)
            a_d9_c = compute_d9_signrand_a(ep_p_ctrl["obs"], ep_p_ctrl["probe"], ep_p_ctrl["pdir"], t)
            s_comp_c = lp.compute_support_score(ep_n_ctrl, t)
            s_act_c = lp.compute_actinfo_score(ep_n_ctrl, t)
            s_prb_c = lp_probed.compute_support_score(ep_p_ctrl, t)
            
            p_d2_c = pava_apply(cal["draft2"][0], cal["draft2"][1], a_d2_c)
            p_d9_c = pava_apply(cal["d9_signrand"][0], cal["d9_signrand"][1], a_d9_c)
            p_comp_c = pava_apply(cal["comparator"][0], cal["comparator"][1], s_comp_c)
            p_act_c = pava_apply(cal["comparator_actinfo"][0], cal["comparator_actinfo"][1], s_act_c)
            p_prb_c = pava_apply(cal["comparator_probed"][0], cal["comparator_probed"][1], s_prb_c)
            
            y_pre = inst.S_pre
            ctrl_arms = {
                "draft2": (a_d2_c, p_d2_c, cal["draft2"][2]),
                "d9_signrand": (a_d9_c, p_d9_c, cal["d9_signrand"][2]),
                "comparator": (s_comp_c, p_comp_c, cal["comparator"][2]),
                "comparator_actinfo": (s_act_c, p_act_c, cal["comparator_actinfo"][2]),
                "comparator_probed": (s_prb_c, p_prb_c, cal["comparator_probed"][2]),
            }
            for arm_name, (raw_sc, p_sc, opt_th) in ctrl_arms.items():
                results.append({
                    "seed": s,
                    "offset": off,
                    "control": True,
                    "arm": arm_name,
                    "auc": compute_auc(raw_sc, y_pre),
                    "auprc": compute_auprc(raw_sc, y_pre),
                    "f1_05": compute_f1(p_sc >= 0.5, y_pre),
                    "f1_opt": compute_f1(p_sc >= opt_th, y_pre),
                    "a_direct": float(raw_sc[inst.ch_direct].mean()),
                    "a_indirect": float(raw_sc[inst.ch_indirect].mean()),
                    "a_nonreach": float(raw_sc[inst.ch_nonreach].mean()),
                })
                
    return {
        "tag": tag,
        "inst": inst,
        "results": results
    }


# --------------------------------------------------------------------------------------------------
# Main Orchestration & Reproduction Report
# --------------------------------------------------------------------------------------------------
def summarize_cell(cell_data):
    tag = cell_data["tag"]
    res = cell_data["results"]
    arms = ["draft2", "d9_signrand", "comparator", "comparator_actinfo", "comparator_probed"]
    
    print("\n" + "=" * 120)
    print(f"CELL: {tag}")
    print("=" * 120)
    
    print(f"\n--- Event-carrying Performance (Offsets 200, 500, 1000) ---")
    print(f"{'Offset':>7s} | {'Arm':>19s} | {'AUC':>7s} | {'AUPRC':>7s} | {'F1@0.5':>7s} | {'F1@opt':>7s} | {'Direct':>7s} | {'Indirect':>8s} | {'Non-reach':>9s}")
    print("-" * 120)
    
    for off in OFFSETS:
        for arm in arms:
            rows = [r for r in res if r["offset"] == off and r["arm"] == arm and not r["control"]]
            m_auc = np.nanmean([r["auc"] for r in rows])
            m_prc = np.nanmean([r["auprc"] for r in rows])
            m_f1_05 = np.mean([r["f1_05"] for r in rows])
            m_f1_opt = np.mean([r["f1_opt"] for r in rows])
            m_dir = np.mean([r["a_direct"] for r in rows])
            m_ind = np.mean([r["a_indirect"] for r in rows])
            m_non = np.mean([r["a_nonreach"] for r in rows])
            print(f"{off:7d} | {arm:>19s} | {m_auc:7.3f} | {m_prc:7.3f} | {m_f1_05:7.3f} | {m_f1_opt:7.3f} | {m_dir:7.2f} | {m_ind:8.2f} | {m_non:9.2f}")
        print("-" * 120)

    # Paired Differences: D-9.1 vs Comparators @ offset 500
    print(f"\n--- Paired Difference @ Offset 500 (D-9.1 minus Comparators) ---")
    rows_d9 = {r["seed"]: r for r in res if r["offset"] == 500 and r["arm"] == "d9_signrand" and not r["control"]}
    
    for comp_name in ["comparator", "comparator_actinfo", "comparator_probed"]:
        rows_comp = {r["seed"]: r for r in res if r["offset"] == 500 and r["arm"] == comp_name and not r["control"]}
        diff_auc = [rows_d9[s]["auc"] - rows_comp[s]["auc"] for s in rows_d9]
        diff_prc = [rows_d9[s]["auprc"] - rows_comp[s]["auprc"] for s in rows_d9]
        diff_f1 = [rows_d9[s]["f1_opt"] - rows_comp[s]["f1_opt"] for s in rows_d9]
        
        m_auc, se_auc = np.mean(diff_auc), np.std(diff_auc, ddof=1) / math.sqrt(len(diff_auc))
        m_prc, se_prc = np.mean(diff_prc), np.std(diff_prc, ddof=1) / math.sqrt(len(diff_prc))
        m_f1, se_f1 = np.mean(diff_f1), np.std(diff_f1, ddof=1) / math.sqrt(len(diff_f1))
        
        tcrit = 2.045  # df=29, 95% CI
        print(f"  Delta(D-9.1 - {comp_name:<18s}):")
        print(f"    Delta_AUPRC = {m_prc:+.3f} [{m_prc - tcrit*se_prc:+.3f}, {m_prc + tcrit*se_prc:+.3f}]  (Target margin > 0.10: {'PASS' if m_prc - tcrit*se_prc > 0.10 else 'FAIL/INCONCLUSIVE'})")
        print(f"    Delta_AUC   = {m_auc:+.3f} [{m_auc - tcrit*se_auc:+.3f}, {m_auc + tcrit*se_auc:+.3f}]")
        print(f"    Delta_F1opt = {m_f1:+.3f} [{m_f1 - tcrit*se_f1:+.3f}, {m_f1 + tcrit*se_f1:+.3f}]")

    # No-Event Control
    print(f"\n--- No-Event Control Performance @ Offset 500 ---")
    for arm in arms:
        rows_c = [r for r in res if r["offset"] == 500 and r["arm"] == arm and r["control"]]
        m_auc = np.nanmean([r["auc"] for r in rows_c])
        m_prc = np.nanmean([r["auprc"] for r in rows_c])
        m_f1 = np.mean([r["f1_opt"] for r in rows_c])
        print(f"  {arm:>19s}: AUC={m_auc:.3f}, AUPRC={m_prc:.3f}, F1@opt={m_f1:.3f}")


def run_all_experiments():
    cells = [
        ("Nx10_conf_present", 10, True, 0.45),
        ("Nx10_conf_absent",  10, False, 0.45),
        ("Nx30_conf_present", 30, True, 0.45),
        ("Nx30_conf_absent",  30, False, 0.45),
        ("Nx10_ablation_Wu0", 10, True, 0.0),
    ]
    
    all_res = {}
    for tag, nx, conf, wu in cells:
        cell_data = run_cell_experiment(N_x=nx, confounded=conf, W_u_val=wu, n_seeds=N_SEEDS, tag=tag)
        all_res[tag] = cell_data
        summarize_cell(cell_data)
        
    print("\n" + "=" * 120)
    print("ALL CELLS COMPLETE")
    print("=" * 120)

if __name__ == "__main__":
    run_all_experiments()
