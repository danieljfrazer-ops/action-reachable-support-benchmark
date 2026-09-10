"""
sim_d8.py -- independent refutation attempt against decision D-8 (round 3, Claude Opus reviewer).

Written WITHOUT reading review-ibd-spec/sim_ibd_review.py or review-ibd-spec/findings.md.
Sources used: stage-0a-contract-v3.3.md (sections 0, B, C, D, G, H, H2), interface-spec-v3.md,
sequential-ibd-spec.md (DRAFT 2, sections 2-9), roadmap-v4*.md.

What it builds, from scratch:
  1. A contract-B family-L instance at registry values, with the certifications the contract
     demands (spectral radii, closed-loop radius on the delay-augmented state, saturation
     fraction, rho_min confounding floor, C2 operational effects vs epsilon, C3 S^obs,eps).
  2. The DRAFT-2 sequential-IBD detector, implemented from the section-9 pseudo-code:
     block-periodic L=1 probes at Pi=20 with the reservoir_0=0 hard cap, |increment| features
     over H={1,2,3}, matched null anchors t_p-3m (m=1..4), tie-corrected Mann-Whitney z per
     (channel,horizon), signed max-|z| clipped to +-8, W_steps=500 trailing window, frozen
     isotonic p_c, and stat = max_c |a_c - abar_c| / v_c with epoch persistence p_epoch=3.
  3. Two readings of the contract-H comparator ("CUSUM on innovations of a channel-agnostic
     linear predictor ... its per-channel support scores are innovation statistics"):
       (2a) LITERAL   : per-channel innovation CUSUM value as the support score.
       (2b) STRONGEST : windowed innovation-variance reduction attributable to the action block
                        (frozen full predictor vs frozen no-action predictor). This is still an
                        innovation statistic and is channel-agnostic, but it actually carries
                        support information, so it is the fair opponent.
     plus (3) the D-7a probed comparator: 2b run on the arm-1 probed stream.
  4. Alarm channels for both arms, thresholds bisected to the D-6b fresh-start ARL_0 = 1000
     on no-event streams, then P(detect within H_det=200) measured against a no-event control.
  5. The D-8a NEW PRIMARY: F1 of thresholded p_c (0.5) against S^obs,eps at offsets
     {200,500,1000}, paired per seed, IBD minus comparator; and P2 (mean p_c on confounded
     distractors at offsets {10,50,200}).
  6. Side experiments that attack the draft-2 spec directly (exchangeability of the rank null,
     the two-pass calibration protocol's transition band, the section-4 window table).

Interpreter: /Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3   (numpy only, nothing installed)
Runtime target: < 10 minutes. Seed counts are printed in the header of every table.
"""
import sys, os, math, time, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.normpath(os.path.join(HERE, "..", "executable-proofs", "gate"))
sys.path.insert(0, GATE)
import contract_ref as ref            # reference count_alarms / match_alarms (spec 5 delegates to it)

T0 = time.time()
def log(*a):
    print(f"[{time.time()-T0:7.1f}s]", *a); sys.stdout.flush()

# ----------------------------------------------------------------------------------------------
# Registry (stage-0a-contract-v3.3.md section 0). Nothing below may deviate from these.
# ----------------------------------------------------------------------------------------------
EPS        = 0.05
H_SUPPORT  = 3
HSET       = (1, 2, 3)
A_MAG      = 1.0          # probe set A = +-e_k, magnitude 1.0
C_MIN      = 0.2
RHO_MAX    = 0.95
RHO_U      = 0.8
A_MAX      = 2.0
RHO_MIN    = 0.4
RHO_CL     = 0.98
N_B, N_D, N_W, K = 4, 2, 4, 2
SIG_B = SIG_D = SIG_W = SIG_X = 0.1
SIG_O  = 0.05
SIG_A  = 0.1
SIG_U  = 1.0
F_CONF = 0.5
EPISODE_LEN = 2000
EVENT_T     = 1000
OFFSETS_F1  = (200, 500, 1000)
OFFSETS_P2  = (10, 50, 200)
PROBE_BUDGET = 0.05
P_PERSIST, R_REFRACT, W_T = 3, 20, 50
H_DET   = 200
ARL0    = 1000

# draft-2 arm constants (sequential-ibd-spec.md section 8)
L_BLOCK  = 1
PI       = 20                # = L / probe_budget
RESERVOIR_0 = 0
M_NULL   = 4
SP_NULL  = 3                 # = max(HSET)
W_STEPS  = 500
Z_CAP    = 8.0
A_ABSENT = -Z_CAP
V_FLOOR  = 0.5
N_MIN    = 10
P_EPOCH  = 3
R_CAL, CAL_EVENT_SHARE = 40, 0.5

# reviewer knobs (declared, not hidden)
N_SEEDS_SCORED  = 30         # scored episodes per cell per arm (paired)
N_NULL_EPISODES = 24         # no-event streams used to bisect h to ARL_0
NULL_LEN        = 6000       # length of an ARL_0 calibration stream


# ==============================================================================================
# 1. Contract-B family-L instance
# ==============================================================================================
class Instance:
    """Family L SCM per contract section B, with the contract-D 'complete actuator loss' event.

    Wiring is chosen so that the confirmatory instance constraint (CL-4) holds: actuator 0's
    column reaches components with no alternative path within H, so S^obs,eps really changes.
      b0 <- a0 ;  b1 <- b0 ;  b2 <- a1 ;  b3 <- b2 ;  d0 <- b0 ;  d1 <- b2
      x  <- u (for the confounded half) ;  w exogenous ;  a <- W_o o + W_u u  (shared cause u)
    """
    def __init__(self, N_x=10, tau=0, confounded=True, misspecify=False, seed=0):
        rng = np.random.default_rng(1000 + seed)
        self.N_x, self.tau, self.confounded, self.misspecify = N_x, tau, confounded, misspecify
        self.A_b = np.array([[0.85, 0, 0, 0],
                             [0.30, 0.85, 0, 0],
                             [0, 0, 0.85, 0],
                             [0, 0, 0.30, 0.85]])
        self.B0  = np.array([[1.0, 0.0],
                             [0.0, 0.0],
                             [0.0, 1.0],
                             [0.0, 0.0]])
        self.A_d = np.diag([0.5, 0.5])
        self.C_d = np.array([[1.0, 0, 0, 0],
                             [0, 0, 1.0, 0]])
        self.A_w = np.diag([0.90, 0.85, 0.80, 0.75])
        self.A_x = 0.50 * np.eye(N_x)   # tuned so rho_min >= 0.4 is attainable (see cert)
        n_conf   = int(round(F_CONF * N_x))
        self.G   = np.zeros((N_x, 1)); self.G[:n_conf, 0] = 1.0
        self.conf_mask_x = np.zeros(N_x, bool); self.conf_mask_x[:n_conf] = True
        # R1 misspecification transform (contract F): +10% on the diagonal of A_b and B.
        if misspecify:
            self.A_b = self.A_b + 0.10 * np.diag(np.diag(self.A_b))
            self.B0  = self.B0 * 1.10
        # policy: a = clip(W_o o + W_u u + eps_a).  W_o reads the two directly-actuated body
        # channels only (contract F11: "the policy's actual observed channels").
        self.W_u = np.array([[0.45], [0.45]])
        self.kf  = 0.15   # largest feedback gain compatible with rho_min >= 0.4 (see cert / findings R3-6)
        self.N_z = N_B + N_D + N_W + N_x
        self.C   = self.N_z + 2                     # + 2 padding channels (D3, K1)
        self.assign = np.array(list(range(self.N_z)) + [-1, -1])
        self.gain   = np.ones(self.C)
        self.avail  = np.ones(self.C, bool)
        self.ch_b   = [0, 1, 2, 3]
        self.ch_d   = [N_B, N_B + 1]
        self.ch_w   = list(range(N_B + N_D, N_B + N_D + N_W))
        self.ch_x   = list(range(N_B + N_D + N_W, self.N_z))
        self.conf_mask = np.zeros(self.C, bool)
        self.conf_mask[np.array(self.ch_x)] = self.conf_mask_x if confounded else False
        self.W_o = np.zeros((K, self.C))
        self.W_o[0, self.ch_b[0]] = -self.kf
        self.W_o[1, self.ch_b[2]] = -self.kf
        if not confounded:
            self.G[:] = 0.0                         # F7: confounder absent = G=0, W_u unchanged

    # ---- state transition helpers -------------------------------------------------------
    def F_full(self):
        """Autonomous latent block matrix F with z = [b; d; w; x] (u enters x separately)."""
        n = self.N_z; F = np.zeros((n, n))
        F[:N_B, :N_B] = self.A_b
        F[N_B:N_B+N_D, :N_B] = self.C_d
        F[N_B:N_B+N_D, N_B:N_B+N_D] = self.A_d
        s = N_B + N_D
        F[s:s+N_W, s:s+N_W] = self.A_w
        F[s+N_W:, s+N_W:] = self.A_x
        return F

    def B_z(self, B):
        Bz = np.zeros((self.N_z, K)); Bz[:N_B, :] = B; return Bz

    # ---- C2 operational latent effect e_j, exact for family L ---------------------------
    def latent_effect(self, B):
        """e_j = max over h<=H and a in A of |E[z_{j,t+h}|do(a, later 0)] - E[.|do(0)]|.
        Family L: the difference is deterministic, so no Monte Carlo interval is needed."""
        F = self.F_full(); Bz = self.B_z(B)
        e = np.zeros(self.N_z)
        for k in range(K):
            for sgn in (+1.0, -1.0):
                a = np.zeros(K); a[k] = sgn * A_MAG
                delta = np.zeros(self.N_z)
                for h in range(1, H_SUPPORT + 1):
                    delta = F @ delta
                    if h == self.tau + 1:
                        delta = delta + Bz @ a
                    e = np.maximum(e, np.abs(delta))
        return e

    def s_obs_eps(self, B):
        e = self.latent_effect(B)
        return ref.s_obs_eps(e, self.assign, self.gain, self.avail, EPS), e

    # ---- stability certifications --------------------------------------------------------
    def closed_loop_radius(self, B):
        """rho on the delay-augmented state [z_t ... ; a_{t-1}..a_{t-tau}; u_t] (contract B / F11)."""
        n, tau = self.N_z, self.tau
        Amap = np.zeros((K, n))                       # a = W_o o ~= W_o (Assign z)
        for c in range(self.C):
            j = self.assign[c]
            if j >= 0:
                Amap[:, j] += self.W_o[:, c] * self.gain[c] * self.avail[c]
        dim = n + K * tau + 1
        M = np.zeros((dim, dim))
        F, Bz = self.F_full(), self.B_z(B)
        M[:n, :n] = F
        if tau == 0:
            M[:n, :n] += Bz @ Amap
            M[:n, n:n+1] = Bz @ self.W_u
        else:
            M[:n, n + K*(tau-1): n + K*tau] = Bz       # uses a_{t-tau}
            M[n:n+K, :n] = Amap                        # a_t enters the queue head
            M[n:n+K, n+K*tau:n+K*tau+1] = self.W_u
            for i in range(1, tau):
                M[n+K*i:n+K*(i+1), n+K*(i-1):n+K*i] = np.eye(K)
        M[-1, -1] = RHO_U
        return float(np.max(np.abs(np.linalg.eigvals(M))))


def simulate(inst, seed, event_t=None, probe=False, T=EPISODE_LEN):
    """Roll one episode. Returns obs[T+1,C], act[T,K], probe_flag[T], sat_frac, S_obs pre/post.

    Probe schedule is exactly the draft-2 rule (section 2 / section 9 pseudo-code):
    a probe at step t iff used+1 <= floor(0.05*t) and t - last_probe_t >= PI.
    """
    rng = np.random.default_rng(9_000_000 + 7919 * seed + (1 if probe else 0))
    N_z, C, tau = inst.N_z, inst.C, inst.tau
    B = inst.B0.copy()
    F, Bz = inst.F_full(), inst.B_z(B)
    Assign = np.zeros((C, N_z))
    for c in range(C):
        if inst.assign[c] >= 0:
            Assign[c, inst.assign[c]] = 1.0
    sig = np.zeros(N_z)
    sig[:N_B] = SIG_B; sig[N_B:N_B+N_D] = SIG_D
    sig[N_B+N_D:N_B+N_D+N_W] = SIG_W; sig[N_B+N_D+N_W:] = SIG_X
    Gz = np.zeros((N_z, 1)); Gz[N_B+N_D+N_W:, :] = inst.G

    z = np.zeros(N_z); u = np.array([rng.normal(0.0, SIG_U / math.sqrt(1 - RHO_U**2))])
    obs = np.zeros((T + 1, C)); act = np.zeros((T, K)); pflag = np.zeros(T, bool)
    pdir = np.full(T, -1, int)
    aq = [np.zeros(K) for _ in range(tau + 1)]
    used, last_p, n_sat = 0, -PI, 0
    A_SET = [(k, s) for k in range(K) for s in (+1.0, -1.0)]
    for t in range(T + 1):
        o = inst.avail * inst.gain * (Assign @ z) + rng.normal(0, SIG_O, C)
        obs[t] = o
        if t == T:
            break
        if event_t is not None and t == event_t:
            B = inst.B0.copy(); B[:, 0] = 0.0          # complete actuator loss, actuator 0
            Bz = inst.B_z(B)
        is_probe = False
        if t >= PI and used + 1 <= math.floor(PROBE_BUDGET * t) and t - last_p >= PI and t + max(HSET) <= T:
            is_probe = probe
        if is_probe:
            di = int(rng.integers(0, 2 * K)); k, s = A_SET[di]
            a = np.zeros(K); a[k] = s * A_MAG
            used += 1; last_p = t; pflag[t] = True; pdir[t] = di
        else:
            araw = inst.W_o @ o + inst.W_u @ u + rng.normal(0, SIG_A, K)
            a = np.clip(araw, -A_MAX, A_MAX)
            n_sat += int(np.any(np.abs(araw) > A_MAX))
        act[t] = a
        aq.append(a.copy()); aq.pop(0)
        z = F @ z + Bz @ aq[0] + Gz @ u + rng.normal(0, sig)
        u = RHO_U * u + rng.normal(0, SIG_U, 1)
    return dict(obs=obs, act=act, probe=pflag, pdir=pdir, sat_frac=n_sat / T, used=used)


# ==============================================================================================
# 2. Draft-2 sequential-IBD detector (sequential-ibd-spec.md sections 2-5, 9)
# ==============================================================================================
def _avg_ranks(arr):
    """Average ranks down axis 0 for a (n, C) array. Fast path when a column has no ties."""
    n, C = arr.shape
    order = np.argsort(arr, axis=0, kind="mergesort")
    ranks = np.empty((n, C))
    base = np.broadcast_to(np.arange(1, n + 1, dtype=float)[:, None], (n, C)).copy()
    np.put_along_axis(ranks, order, base, axis=0)
    srt = np.take_along_axis(arr, order, axis=0)
    tie_cols = np.nonzero((np.diff(srt, axis=0) == 0).any(axis=0))[0]
    tie_term = np.zeros(C)
    for c in tie_cols:                                   # rare: only degenerate/constant channels
        col = srt[:, c]; i = 0
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
    return ranks, tie_term


def mw_z(P, N):
    """Tie-corrected Mann-Whitney rank-sum z of P against N, per column. Spec section 3."""
    nP, nN = P.shape[0], N.shape[0]; n = nP + nN
    arr = np.vstack([P, N])
    ranks, tie_term = _avg_ranks(arr)
    R_P = ranks[:nP].sum(axis=0)
    U = R_P - nP * (nP + 1) / 2.0
    kappa = 1.0 - tie_term / (n * (n * n - 1))
    var = nP * nN * (n + 1) / 12.0 * kappa
    z = np.zeros_like(U)
    ok = var > 0
    z[ok] = (U[ok] - nP * nN / 2.0) / np.sqrt(var[ok])
    return z


def ibd_a_trace(obs, probe_flag, T=EPISODE_LEN, aggregate="signed_maxabs"):
    """Return (epoch_times, a_trace[n_epoch, C]) for the draft-2 statistic.

    a_c = z at argmax_h |z_{c,h}| (ties -> smallest h), clipped to +-Z_CAP; a_absent for a
    channel whose window values are all identical. Warm-up: no epoch emitted until n_P >= N_MIN.
    """
    C = obs.shape[1]
    p_anchors = np.nonzero(probe_flag)[0]
    if len(p_anchors) == 0:
        return np.array([], int), np.zeros((0, C))
    # increments per horizon, precomputed
    inc = {h: np.abs(obs[h:] - obs[:-h]) for h in HSET}      # inc[h][t] = |o(t+h)-o(t)|
    times, out = [], []
    for i, t_p in enumerate(p_anchors):
        t_close = t_p + max(HSET)
        if t_close > T:
            break
        lo = t_close - W_STEPS                                # window (t-W, t]
        keep = p_anchors[(p_anchors > lo) & (p_anchors <= t_p)]
        if len(keep) < N_MIN:
            continue
        nulls = np.concatenate([keep - m * SP_NULL for m in range(1, M_NULL + 1)])
        nulls = nulls[nulls > lo]
        zs = []
        for h in HSET:
            zs.append(mw_z(inc[h][keep], inc[h][nulls]))
        Z = np.vstack(zs)                                    # (|H|, C)
        if aggregate == "max_h":                             # one-sided candidate fix (R3-2)
            a = Z.max(axis=0)
        else:                                                # spec section 3: signed max-|z|
            a = np.zeros(C); best = np.zeros(C)
            for z in zs:
                better = np.abs(z) > best + 1e-12            # ties -> smallest h (strict >)
                a[better] = z[better]; best[better] = np.abs(z[better])
        a = np.clip(a, -Z_CAP, Z_CAP)
        allP = np.vstack([inc[h][keep] for h in HSET]); allN = np.vstack([inc[h][nulls] for h in HSET])
        degen = (allP.max(axis=0) == allP.min(axis=0)) & (allN.max(axis=0) == allN.min(axis=0)) \
                & (allP.max(axis=0) == allN.max(axis=0))
        a[degen] = A_ABSENT
        times.append(t_close); out.append(a)
    if not times:
        return np.array([], int), np.zeros((0, C))
    return np.array(times, int), np.vstack(out)


def ibd_signrand_trace(obs, probe_flag, pdir, T=EPISODE_LEN):
    """CANDIDATE FIX (R3-1). Same probes, same budget, no task-policy null at all.

    For each (channel, horizon, actuator k) contrast the SIGNED increments of the probes that
    used +e_k against those that used -e_k, inside the same trailing window. The grouping variable
    is the estimator's own coin flip, so exchangeability under 'actuator k does not reach channel
    c within h' is EXACT by randomisation -- it does not depend on the task policy, on W_u, or on
    rho_u. a_c = max over (k, h) of |z|, which is monotone in reachability by construction."""
    C = obs.shape[1]
    p_anchors = np.nonzero(probe_flag)[0]
    if len(p_anchors) == 0:
        return np.array([], int), np.zeros((0, C))
    sinc = {h: obs[h:] - obs[:-h] for h in HSET}                 # SIGNED increments
    times, out = [], []
    for t_p in p_anchors:
        t_close = t_p + max(HSET)
        if t_close > T:
            break
        lo = t_close - W_STEPS
        keep = p_anchors[(p_anchors > lo) & (p_anchors <= t_p)]
        if len(keep) < N_MIN:
            continue
        d = pdir[keep]
        a = np.zeros(C)
        for k in range(K):
            pos = keep[d == 2 * k]; neg = keep[d == 2 * k + 1]
            if len(pos) < 3 or len(neg) < 3:
                continue
            for h in HSET:
                z = mw_z(sinc[h][pos], sinc[h][neg])
                a = np.maximum(a, np.abs(z))
        times.append(t_close); out.append(np.clip(a, -Z_CAP, Z_CAP))
    if not times:
        return np.array([], int), np.zeros((0, C))
    return np.array(times, int), np.vstack(out)


def ibd_stat_trace(a_times, a_tr, abar, v):
    """stat_t = max_c |a_c - abar_c| / v_c, one value per epoch (spec section 5)."""
    if len(a_times) == 0:
        return a_times, np.zeros(0)
    return a_times, np.max(np.abs(a_tr - abar[None, :]) / v[None, :], axis=1)


def epoch_alarm_stream(a_times, stat, h, T=EPISODE_LEN):
    """Per-step raw alarm_S stream: raise_run counts consecutive EPOCHS with stat > h;
    alarm_S = 1[raise_run >= P_EPOCH], held between epochs (spec section 5)."""
    raw = np.zeros(T + 1, bool)
    run, cur = 0, False
    prev = 0
    for i, t in enumerate(a_times):
        raw[prev:t] = cur
        run = run + 1 if stat[i] > h else 0
        cur = run >= P_EPOCH
        prev = t
    raw[prev:] = cur
    return raw


# ==============================================================================================
# 3. Comparator: channel-agnostic linear predictor + innovations (contract H)
# ==============================================================================================
class LinearPredictor:
    """Channel-agnostic linear predictor o_{t+1} ~ [o_t; a_t; 1] (contract H, R0 = fitted on
    fault-free in-distribution data). Innovations feed both the alarm CUSUM and the per-channel
    support scores. A no-action companion predictor o_{t+1} ~ [o_t; 1] is fitted at the same time;
    the difference of their innovation variances is the strongest channel-agnostic innovation
    statistic that carries support information."""
    def __init__(self):
        self.W = self.W0 = self.sd = self.sd0 = None
        self.k_glob = None; self.k_ch = None

    def fit(self, episodes):
        X, X0, Y = [], [], []
        for ep in episodes:
            o, a = ep["obs"], ep["act"]; T = a.shape[0]
            X.append(np.hstack([o[:T], a, np.ones((T, 1))]))
            X0.append(np.hstack([o[:T], np.ones((T, 1))]))
            Y.append(o[1:T + 1])
        X = np.vstack(X); X0 = np.vstack(X0); Y = np.vstack(Y)
        self.W, *_ = np.linalg.lstsq(X, Y, rcond=None)
        self.W0, *_ = np.linalg.lstsq(X0, Y, rcond=None)
        r = Y - X @ self.W; r0 = Y - X0 @ self.W0
        self.sd = np.maximum(r.std(axis=0), 1e-9); self.sd0 = np.maximum(r0.std(axis=0), 1e-9)
        # CUSUM reference values, frozen on the same fault-free split: k must exceed the null
        # drift or the statistic is a positive-drift timer rather than a change detector.
        zz = np.abs(r) / self.sd[None, :]
        zmax = zz.max(axis=1)
        self.k_glob = float(zmax.mean() + 0.5 * zmax.std())
        self.k_ch = zz.mean(axis=0) + 0.5 * zz.std(axis=0)

    def innovations(self, ep):
        o, a = ep["obs"], ep["act"]; T = a.shape[0]
        X = np.hstack([o[:T], a, np.ones((T, 1))]); X0 = np.hstack([o[:T], np.ones((T, 1))])
        return o[1:T + 1] - X @ self.W, o[1:T + 1] - X0 @ self.W0

    def _zmax(self, ep):
        r, _ = self.innovations(ep)
        return np.max(np.abs(r) / self.sd[None, :], axis=1)

    def cusum_alarm(self, ep, h, T=EPISODE_LEN):
        """Raw per-step raise stream S_t > h. k_glob exceeds the null drift, so S returns to 0
        under the null and the harness's p-consecutive rule is meaningful."""
        z = self._zmax(ep); S = 0.0; raw = np.zeros(T + 1, bool)
        for t in range(len(z)):
            S = max(0.0, S + z[t] - self.k_glob); raw[t + 1] = S > h
        return raw

    def cusum_stat(self, ep):
        """Same recursion but with the crossing threshold supplied later (for ARL bisection the
        threshold changes, so the trace is recomputed per threshold by cusum_alarm)."""
        return self._zmax(ep)

    def score_literal(self, ep, T=EPISODE_LEN):
        """(2a) LITERAL reading of contract H: the per-channel innovation CUSUM value."""
        r, _ = self.innovations(ep)
        zz = np.abs(r) / self.sd[None, :]
        S = np.zeros(r.shape[1]); out = np.zeros((T + 1, r.shape[1]))
        for t in range(zz.shape[0]):
            S = np.maximum(0.0, S + zz[t] - self.k_ch); out[t + 1] = S
        return out

    def score_actinfo(self, ep, T=EPISODE_LEN, win=W_STEPS):
        """(2b) STRONGEST reading: windowed innovation-variance reduction attributable to the
        action block. score_c(t) = 1 - SSE_full,c / SSE_noaction,c over the trailing window."""
        r, r0 = self.innovations(ep)
        s1 = np.vstack([np.zeros(r.shape[1]), np.cumsum(r**2, axis=0)])
        s0 = np.vstack([np.zeros(r.shape[1]), np.cumsum(r0**2, axis=0)])
        out = np.zeros((T + 1, r.shape[1]))
        for t in range(1, T + 1):
            lo = max(0, t - win)
            num = s1[t] - s1[lo]; den = s0[t] - s0[lo]
            out[t] = np.where(den > 1e-12, 1.0 - num / np.maximum(den, 1e-12), 0.0)
        return np.clip(out, -1.0, 1.0)


def auc(scores, labels):
    """Mann-Whitney AUC of `scores` against binary `labels` (threshold-free companion to F1)."""
    pos = np.asarray(labels, bool)
    if pos.all() or (~pos).all():
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    r = np.empty(len(scores), float); r[order] = np.arange(1, len(scores) + 1, dtype=float)
    srt = np.sort(scores); i = 0
    while i < len(srt):                                    # average ranks over ties
        j = i
        while j + 1 < len(srt) and srt[j + 1] == srt[i]:
            j += 1
        if j > i:
            r[order[i:j + 1]] = 0.5 * (i + 1 + j + 1)
        i = j + 1
    nP = int(pos.sum()); nN = len(pos) - nP
    return float((r[pos].sum() - nP * (nP + 1) / 2.0) / (nP * nN))


# ==============================================================================================
# 4. Isotonic calibrator (PAVA, spec section 4)
# ==============================================================================================
def pava_fit(x, y):
    o = np.argsort(x, kind="mergesort"); xs, ys = np.asarray(x)[o], np.asarray(y, float)[o]
    val, wt = [], []
    for v in ys:
        val.append(v); wt.append(1.0)
        while len(val) > 1 and val[-2] > val[-1]:
            v2 = val.pop(); w2 = wt.pop(); v1 = val.pop(); w1 = wt.pop()
            val.append((v1 * w1 + v2 * w2) / (w1 + w2)); wt.append(w1 + w2)
    fit = np.empty(len(ys)); i = 0
    for v, w in zip(val, wt):
        fit[i:i + int(w)] = v; i += int(w)
    return xs, fit


def pava_apply(knots_x, knots_y, v):
    idx = np.searchsorted(knots_x, v, side="right") - 1
    idx = np.clip(idx, 0, len(knots_y) - 1)
    return np.clip(knots_y[idx], 0.0, 1.0)


# ==============================================================================================
# 5. One experimental cell
# ==============================================================================================
def s_obs_at(inst, t, event_t):
    B = inst.B0.copy()
    if event_t is not None and t >= event_t:
        B[:, 0] = 0.0
    S, e = inst.s_obs_eps(B)
    return S


def run_cell(N_x=10, tau=0, confounded=True, misspecify=False, tag="", verbose=True):
    inst = Instance(N_x=N_x, tau=tau, confounded=confounded, misspecify=misspecify)
    C = inst.C
    S_pre = s_obs_at(inst, 0, EVENT_T); S_post = s_obs_at(inst, EVENT_T, EVENT_T)
    res = dict(tag=tag, N_x=N_x, tau=tau, confounded=confounded, misspecify=misspecify)

    # ---------- certifications ----------
    B_post = inst.B0.copy(); B_post[:, 0] = 0.0
    e_pre = inst.latent_effect(inst.B0); e_post = inst.latent_effect(B_post)
    cert = dict(
        rho_Ab=float(max(abs(np.linalg.eigvals(inst.A_b)))),
        rho_Ad=float(max(abs(np.linalg.eigvals(inst.A_d)))),
        rho_Aw=float(max(abs(np.linalg.eigvals(inst.A_w)))),
        rho_Ax=float(max(abs(np.linalg.eigvals(inst.A_x)))),
        rho_cl_pre=inst.closed_loop_radius(inst.B0),
        rho_cl_post=inst.closed_loop_radius(B_post),
        min_margin_pre=float(np.min(np.abs(e_pre - EPS))),
        min_margin_post=float(np.min(np.abs(e_post - EPS))),
        S_pre=int(S_pre.sum()), S_post=int(S_post.sum()),
        s_change_certified=bool((S_pre != S_post).any()),
    )
    # calibration episodes (R_CAL, half carrying the event) -- spec section 4
    log(f"cell {tag}: simulating {R_CAL} calibration episodes ...")
    cal_probe, cal_plain = [], []
    for i in range(R_CAL):
        ev = EVENT_T if i < int(R_CAL * CAL_EVENT_SHARE) else None
        cal_probe.append((simulate(inst, 10_000 + i, event_t=ev, probe=True), ev))
        cal_plain.append((simulate(inst, 10_000 + i, event_t=ev, probe=False), ev))
    # certifications that need a stream
    ep0 = cal_plain[R_CAL - 1][0]
    a_rms = float(np.sqrt(np.mean(ep0["act"]**2)))
    ax = ep0["obs"][:EVENT_T, np.array(inst.ch_x)]
    aa = ep0["act"][:EVENT_T]
    cert["sat_frac"] = float(ep0["sat_frac"])
    cert["policy_action_RMS"] = a_rms
    cert["probe_mag_over_action_RMS"] = A_MAG / a_rms
    cert["max_corr_a_x"] = float(ref.max_pairwise_corr(aa, ax))
    cert["probe_steps_used"] = int(cal_probe[0][0]["used"])
    cert["budget_ok"] = bool(cal_probe[0][0]["used"] <= math.floor(PROBE_BUDGET * EPISODE_LEN))
    res["cert"] = cert
    if verbose:
        log(f"  cert {tag}: rho_cl={cert['rho_cl_pre']:.3f}/{cert['rho_cl_post']:.3f} "
            f"sat={cert['sat_frac']:.4f} max|corr(a,x)|={cert['max_corr_a_x']:.3f} "
            f"|S|={cert['S_pre']}->{cert['S_post']} probe/RMS={cert['probe_mag_over_action_RMS']:.2f} "
            f"probes={cert['probe_steps_used']}")

    # ---------- pass 0: a-traces on the calibration split, abar/v, isotonic g ----------
    log(f"cell {tag}: pass-0 a-traces ...")
    cal_a, cal_a1, cal_a2 = [], [], []
    for ep, ev in cal_probe:
        ts, A = ibd_a_trace(ep["obs"], ep["probe"])
        cal_a.append((ts, A, ev))
        ts1, A1 = ibd_a_trace(ep["obs"], ep["probe"], aggregate="max_h")
        cal_a1.append((ts1, A1, ev))
        ts2, A2 = ibd_signrand_trace(ep["obs"], ep["probe"], ep["pdir"])
        cal_a2.append((ts2, A2, ev))
    pre = [A[ts < (ev if ev is not None else EPISODE_LEN + 1)] for ts, A, ev in cal_a]
    pre = np.vstack([p for p in pre if len(p)])
    abar = np.median(pre, axis=0)
    v = np.maximum(1.4826 * np.median(np.abs(pre - abar[None, :]), axis=0), V_FLOOR)

    # isotonic training pairs, every epoch of both segments (spec section 4)
    xs, ys, xs_clean, ys_clean = [], [], [], []
    for ts, A, ev in cal_a:
        for i, t in enumerate(ts):
            lab = s_obs_at(inst, t, ev)
            xs.append(A[i]); ys.append(lab.astype(float))
            if ev is None or t < ev or t >= ev + W_STEPS:      # transition band excluded
                xs_clean.append(A[i]); ys_clean.append(lab.astype(float))
    xs = np.concatenate(xs); ys = np.concatenate(ys)
    xs_clean = np.concatenate(xs_clean); ys_clean = np.concatenate(ys_clean)
    kx, ky = pava_fit(xs, ys)
    kxc, kyc = pava_fit(xs_clean, ys_clean)
    xs1, ys1 = [], []
    for ts, A, ev in cal_a1:
        for i, t in enumerate(ts):
            xs1.append(A[i]); ys1.append(s_obs_at(inst, t, ev).astype(float))
    kx1, ky1 = pava_fit(np.concatenate(xs1), np.concatenate(ys1))
    xs2, ys2 = [], []
    for ts, A, ev in cal_a2:
        for i, t in enumerate(ts):
            xs2.append(A[i]); ys2.append(s_obs_at(inst, t, ev).astype(float))
    kx2, ky2 = pava_fit(np.concatenate(xs2), np.concatenate(ys2))
    res["cal_gates"] = dict(
        T_IBD_cal_1_distinct_values=int(len(np.unique(np.round(ky, 9)))),
        T_IBD_cal_2_minority_share=float(min(ys.mean(), 1 - ys.mean())),
        T_IBD_cal_3_monotone=bool(np.all(np.diff(ky) >= -1e-12)),
        g_max=float(ky.max()), g_max_cleanband=float(kyc.max()),
        frac_pairs_in_transition_band=float(1 - len(xs_clean) / len(xs)),
    )

    # ---------- comparator fit (R0 = fault-free in-distribution) ----------
    fitset = [ep for ep, ev in cal_plain if ev is None]
    lp = LinearPredictor(); lp.fit(fitset)
    lp_probed = LinearPredictor(); lp_probed.fit([ep for ep, ev in cal_probe if ev is None])

    # comparator isotonic calibrators, same evaluation grid as the IBD arm
    grid = np.arange(PI + max(HSET), EPISODE_LEN + 1, PI)
    def fit_cal(score_fn, eps_and_ev):
        X, Y = [], []
        for ep, ev in eps_and_ev:
            sc = score_fn(ep)
            for t in grid:
                X.append(sc[t]); Y.append(s_obs_at(inst, t, ev).astype(float))
        return pava_fit(np.concatenate(X), np.concatenate(Y))
    kx_lit, ky_lit = fit_cal(lambda e: lp.score_literal(e), cal_plain)
    kx_act, ky_act = fit_cal(lambda e: lp.score_actinfo(e), cal_plain)
    kx_prb, ky_prb = fit_cal(lambda e: lp_probed.score_actinfo(e), cal_probe)

    # ---------- ARL_0 = 1000 fresh-start threshold bisection (D-6b) ----------
    log(f"cell {tag}: ARL_0 bisection on {N_NULL_EPISODES} null streams ...")
    null_ibd, null_cus = [], []
    for i in range(N_NULL_EPISODES):
        ep = simulate(inst, 50_000 + i, event_t=None, probe=True, T=NULL_LEN)
        ts, A = ibd_a_trace(ep["obs"], ep["probe"], T=NULL_LEN)
        _, st = ibd_stat_trace(ts, A, abar, v)
        null_ibd.append((ts, st))
        epp = simulate(inst, 50_000 + i, event_t=None, probe=False, T=NULL_LEN)
        null_cus.append(lp.cusum_stat(epp))          # z_max trace; thresholded below

    def arl_ibd(h):
        rl = []
        for ts, st in null_ibd:
            raw = epoch_alarm_stream(ts, st, h, T=NULL_LEN)
            ca = ref.count_alarms(raw.tolist(), P_PERSIST, R_REFRACT)
            rl.append(ca[0] if ca else NULL_LEN)
        return float(np.mean(rl))

    def arl_cus(h):
        rl = []
        for z in null_cus:
            S = 0.0; raw = np.zeros(NULL_LEN + 1, bool)
            for t in range(len(z)):
                S = max(0.0, S + z[t] - lp.k_glob); raw[t + 1] = S > h
            ca = ref.count_alarms(raw.tolist(), P_PERSIST, R_REFRACT)
            rl.append(ca[0] if ca else NULL_LEN)
        return float(np.mean(rl))

    def bisect(fn, lo, hi, target=ARL0, iters=40):
        for _ in range(iters):
            mid = 0.5 * (lo + hi)
            if fn(mid) < target: lo = mid
            else: hi = mid
        return 0.5 * (lo + hi)
    h_ibd = bisect(arl_ibd, 0.0, 60.0)
    h_cus = bisect(arl_cus, 0.0, 200.0)
    res["arl"] = dict(h_ibd=h_ibd, arl_ibd=arl_ibd(h_ibd), h_cus=h_cus, arl_cus=arl_cus(h_cus))
    if verbose:
        log(f"  ARL_0: IBD h={h_ibd:.3f} -> {res['arl']['arl_ibd']:.0f} | "
            f"CUSUM h={h_cus:.2f} -> {res['arl']['arl_cus']:.0f}")

    # ---------- pass 1: scored runs ----------
    log(f"cell {tag}: {N_SEEDS_SCORED} scored + {N_SEEDS_SCORED} control episodes ...")
    rows = []
    det_ibd, det_cus, det_ibd0, det_cus0 = [], [], [], []
    for s in range(N_SEEDS_SCORED):
        for ev, store in ((EVENT_T, True), (None, False)):
            epP = simulate(inst, 200_000 + s, event_t=ev, probe=True)
            epN = simulate(inst, 200_000 + s, event_t=ev, probe=False)
            ts, A = ibd_a_trace(epP["obs"], epP["probe"])
            _, A1 = ibd_a_trace(epP["obs"], epP["probe"], aggregate="max_h")
            ts2, A2 = ibd_signrand_trace(epP["obs"], epP["probe"], epP["pdir"])
            _, st = ibd_stat_trace(ts, A, abar, v)
            raw = epoch_alarm_stream(ts, st, h_ibd)
            ca_i = ref.count_alarms(raw.tolist(), P_PERSIST, R_REFRACT)
            raw_c = lp.cusum_alarm(epN, h_cus)
            ca_c = ref.count_alarms(raw_c.tolist(), P_PERSIST, R_REFRACT)
            if ev is None:
                det_ibd0.append(any(EVENT_T < t <= EVENT_T + H_DET for t in ca_i))
                det_cus0.append(any(EVENT_T < t <= EVENT_T + H_DET for t in ca_c))
                continue
            det_ibd.append(any(EVENT_T < t <= EVENT_T + H_DET for t in ca_i))
            det_cus.append(any(EVENT_T < t <= EVENT_T + H_DET for t in ca_c))
            # ---- p_c per arm at each offset ----
            sc_lit = lp.score_literal(epN); sc_act = lp.score_actinfo(epN)
            sc_prb = lp_probed.score_actinfo(epP)
            for off in sorted(set(OFFSETS_F1) | set(OFFSETS_P2)):
                t = EVENT_T + off
                if t > EPISODE_LEN:
                    continue
                j = np.searchsorted(ts, t, side="right") - 1
                a_now = A[j] if j >= 0 else np.zeros(C)
                a1_now = A1[j] if j >= 0 else np.zeros(C)
                j2 = np.searchsorted(ts2, t, side="right") - 1
                a2_now = A2[j2] if j2 >= 0 else np.zeros(C)
                truth = s_obs_at(inst, t, EVENT_T)
                pc = {
                    "seq_ibd":            pava_apply(kx, ky, a_now),
                    "seq_ibd_cleanband":  pava_apply(kxc, kyc, a_now),
                    "seq_ibd_onesided":   pava_apply(kx1, ky1, a1_now),
                    "seq_ibd_signrand":   pava_apply(kx2, ky2, a2_now),
                    "cusum_literal":      pava_apply(kx_lit, ky_lit, sc_lit[t]),
                    "cusum_actinfo":      pava_apply(kx_act, ky_act, sc_act[t]),
                    "cusum_probed":       pava_apply(kx_prb, ky_prb, sc_prb[t]),
                }
                raw_scores = {"seq_ibd": a_now, "seq_ibd_cleanband": a_now,
                              "seq_ibd_onesided": a1_now, "seq_ibd_signrand": a2_now,
                              "cusum_literal": sc_lit[t],
                              "cusum_actinfo": sc_act[t], "cusum_probed": sc_prb[t]}
                for arm, p in pc.items():
                    pred = p > 0.5
                    tp = int((pred & truth).sum()); fp = int((pred & ~truth).sum()); fn = int((~pred & truth).sum())
                    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
                    rows.append(dict(seed=s, offset=off, arm=arm, f1=f1, tp=tp, fp=fp, fn=fn,
                                     npred=int(pred.sum()),
                                     auc=auc(raw_scores[arm], truth),
                                     p_conf=float(p[inst.conf_mask].mean()) if inst.conf_mask.any() else float("nan"),
                                     p_unconf=float(p[np.array(inst.ch_x)][~inst.conf_mask_x].mean())
                                              if (~inst.conf_mask_x).any() else float("nan")))
    res["rows"] = rows
    res["alarm"] = dict(P_detect_ibd=float(np.mean(det_ibd)), P_detect_ibd_control=float(np.mean(det_ibd0)),
                        P_detect_cusum=float(np.mean(det_cus)), P_detect_cusum_control=float(np.mean(det_cus0)))
    return res, inst, (abar, v, cal_a)


# ==============================================================================================
# 6. Spec attacks that need their own measurement
# ==============================================================================================
def attack_exchangeability(inst, n_ep=12):
    """Spec section 3: 'Its null is exact under exchangeability.' Measure the empirical mean and
    sd of z_{c,h} and of a_c on channels with NO action parent (w and x), under no event."""
    zs = {h: [] for h in HSET}; asr = []
    noact = np.array(inst.ch_w + inst.ch_x)
    for i in range(n_ep):
        ep = simulate(inst, 700_000 + i, event_t=None, probe=True)
        ts, A = ibd_a_trace(ep["obs"], ep["probe"])
        if len(ts) == 0:
            continue
        asr.append(A[:, noact].ravel())
        # recompute per-horizon z for the same windows
        p_anchors = np.nonzero(ep["probe"])[0]
        inc = {h: np.abs(ep["obs"][h:] - ep["obs"][:-h]) for h in HSET}
        for t_close in ts[::5]:
            t_p = t_close - max(HSET); lo = t_close - W_STEPS
            keep = p_anchors[(p_anchors > lo) & (p_anchors <= t_p)]
            nulls = np.concatenate([keep - m * SP_NULL for m in range(1, M_NULL + 1)])
            nulls = nulls[nulls > lo]
            for h in HSET:
                zs[h].append(mw_z(inc[h][keep], inc[h][nulls])[noact])
    out = {}
    for h in HSET:
        v = np.concatenate(zs[h]); out[f"z_h{h}"] = (float(v.mean()), float(v.std()))
    a = np.concatenate(asr)
    out["a_signed_maxabs"] = (float(a.mean()), float(a.std()))
    out["P(|a|>1.96)"] = float(np.mean(np.abs(a) > 1.96))
    return out


def attack_window_table(event_t=EVENT_T):
    """Spec section 4 table: 'post-event fraction of window' and 'post-event probe units'."""
    rows = {}
    for off in (10, 50, 200, 500, 1000):
        t = event_t + off
        closes = np.arange(PI + max(HSET), EPISODE_LEN + 1, PI)
        cl = closes[closes <= t]
        if len(cl) == 0:
            rows[off] = (0.0, 0); continue
        tc = cl[-1]; lo = tc - W_STEPS
        frac = max(0.0, min(1.0, (tc - max(lo, event_t)) / W_STEPS))
        anchors = np.arange(PI, EPISODE_LEN, PI)
        keep = anchors[(anchors > lo) & (anchors <= tc - max(HSET))]
        rows[off] = (round(frac, 3), int((keep >= event_t).sum()), int(len(keep)), int(tc))
    return rows


def attack_null_under_u(n_ep=12):
    """Is the two-sample contrast MONOTONE IN SUPPORT under the contract's own shared cause?

    Ablation over the two properties of the task-policy null that the draft-2 spec treats as a
    power nuisance (section 2.5.3) rather than a validity threat:
      (i) W_u  -- how strongly the shared cause drives the policy (rho_min >= 0.4 forces W_u > 0);
      (ii) rho_u -- how persistent that shared cause is (registry fixes rho_u = 0.8).
    A probe action is i.i.d.; a policy action is a persistent low-frequency drive, so over
    h = 2, 3 steps the NULL arm accumulates larger |increments| on reachable channels than the
    PROBE arm does. If that dominates, z goes NEGATIVE on reachable channels."""
    global RHO_U
    out = []
    settings = [("registry: W_u=0.45, rho_u=0.8", 0.45, 0.8),
                ("W_u=0   (policy not confounded; violates rho_min)", 0.0, 0.8),
                ("rho_u=0 (shared cause white; violates registry)", 0.45, 0.0),
                ("W_u=0.20 (weaker confounding)", 0.20, 0.8)]
    saved = RHO_U
    for label, wu, ru in settings:
        RHO_U = ru
        inst = Instance(N_x=6, tau=0, confounded=True)
        inst.W_u = np.array([[wu], [wu]])
        acc = []
        for i in range(n_ep):
            ep = simulate(inst, 610_000 + i, event_t=None, probe=True)
            ts, A = ibd_a_trace(ep["obs"], ep["probe"])
            if len(ts):
                acc.append(A.mean(axis=0))
        A = np.vstack(acc)
        S = s_obs_at(inst, 0, None)
        direct = A[:, [0, 2]].mean()                       # b0, b2: direct action children
        indirect = A[:, [1, 3, 4, 5]].mean()               # b1, b3, d0, d1: reachable via one hop
        nonreach = A[:, ~S].mean()
        aa = simulate(inst, 999, event_t=None, probe=False)
        xs = aa["obs"][:, np.array(inst.ch_x)]
        rho = float(ref.max_pairwise_corr(aa["act"], xs[:EPISODE_LEN]))
        ratio = A_MAG / float(np.sqrt(np.mean(aa["act"]**2)))
        out.append((label, direct, indirect, nonreach, rho, ratio))
    RHO_U = saved
    return out


# ==============================================================================================
# 7. Reporting helpers
# ==============================================================================================
def paired(rows, arm_a, arm_b, offset):
    A = {r["seed"]: r["f1"] for r in rows if r["arm"] == arm_a and r["offset"] == offset}
    B = {r["seed"]: r["f1"] for r in rows if r["arm"] == arm_b and r["offset"] == offset}
    ks = sorted(set(A) & set(B))
    d = np.array([A[k] - B[k] for k in ks])
    n = len(d)
    if n < 2:
        return float(d.mean() if n else 0.0), float("nan"), float("nan"), n
    se = d.std(ddof=1) / math.sqrt(n)
    tcrit = {9: 2.262, 19: 2.093, 29: 2.045}.get(n - 1, 2.093)
    return float(d.mean()), float(d.mean() - tcrit * se), float(d.mean() + tcrit * se), n


def mean_f1(rows, arm, offset):
    v = [r["f1"] for r in rows if r["arm"] == arm and r["offset"] == offset]
    return float(np.mean(v)) if v else float("nan")


def mean_key(rows, arm, offset, key):
    v = [r[key] for r in rows if r["arm"] == arm and r["offset"] == offset]
    return float(np.nanmean(v)) if v else float("nan")


# ==============================================================================================
# MAIN
# ==============================================================================================
if __name__ == "__main__":
    print("=" * 100)
    print("sim_d8.py -- independent D-8 refutation attempt, review3-claude-opus")
    print(f"seeds: scored={N_SEEDS_SCORED}, calibration episodes={R_CAL} (half with event), "
          f"null streams={N_NULL_EPISODES} x {NULL_LEN} steps")
    print("=" * 100)

    print("\n--- spec section 4 window table, recomputed from the epoch grid ---")
    print("offset | spec frac | actual frac | post-event units / total units | epoch time")
    spec_tab = {10: 0.02, 50: 0.10, 200: 0.40, 500: 1.00, 1000: 1.00}
    for off, val in attack_window_table().items():
        print(f"{off:6d} | {spec_tab[off]:9.2f} | {val[0]:11.3f} | {val[1]:9d} / {val[2]:<6d}      | {val[3]}")

    CELLS = [
        dict(N_x=10, tau=0, confounded=True,  misspecify=False, tag="R0-conf-present-Nx10"),
        dict(N_x=10, tau=0, confounded=False, misspecify=False, tag="R0-conf-absent-Nx10"),
        dict(N_x=30, tau=0, confounded=True,  misspecify=False, tag="R0-conf-present-Nx30"),
        dict(N_x=10, tau=0, confounded=True,  misspecify=True,  tag="R1-conf-present-Nx10"),
        dict(N_x=10, tau=0, confounded=False, misspecify=True,  tag="R1-conf-absent-Nx10"),
    ]
    all_res = {}
    for cfg in CELLS:
        r, inst, extra = run_cell(**cfg)
        all_res[cfg["tag"]] = r
        if cfg["tag"] == "R0-conf-present-Nx10":
            print("\n--- attack: is the rank null exact under exchangeability? "
                  "(channels with no action parent, no event) ---")
            ex = attack_exchangeability(inst)
            for k, val in ex.items():
                print(f"  {k}: {val}")
            print("  (exact exchangeability would give mean 0, sd 1 for each z_h, "
                  "and P(|a|>1.96) ~ 0.05 only if a were a single z)")

    print("\n" + "=" * 100)
    print("A. ALARM CHANNEL  (D-8's original claim: no power for the confirmatory event)")
    print("=" * 100)
    print(f"{'cell':26s} {'h_IBD':>7s} {'ARL0':>7s} {'P(det<=H_det)':>14s} {'control':>9s} "
          f"| {'h_CUS':>8s} {'ARL0':>7s} {'P(det)':>8s} {'control':>9s}")
    for tag, r in all_res.items():
        a = r["alarm"]; q = r["arl"]
        print(f"{tag:26s} {q['h_ibd']:7.3f} {q['arl_ibd']:7.0f} {a['P_detect_ibd']:14.2f} "
              f"{a['P_detect_ibd_control']:9.2f} | {q['h_cus']:8.2f} {q['arl_cus']:7.0f} "
              f"{a['P_detect_cusum']:8.2f} {a['P_detect_cusum_control']:9.2f}")

    print("\n" + "=" * 100)
    print("B. NEW PRIMARY (D-8a): F1 of thresholded p_c vs S^obs,eps, per offset")
    print("=" * 100)
    ARMS = ["seq_ibd", "seq_ibd_cleanband", "seq_ibd_onesided", "seq_ibd_signrand",
            "cusum_literal", "cusum_actinfo", "cusum_probed"]
    for tag, r in all_res.items():
        print(f"\ncell {tag}   |S_post| = {r['cert']['S_post']} of {r['cert']['S_pre']} pre-event, "
              f"C = {r['N_x'] + N_B + N_D + N_W + 2} channels")
        print(f"  {'offset':>7s} " + " ".join(f"{a:>18s}" for a in ARMS))
        for off in OFFSETS_F1:
            print(f"  {off:7d} " + " ".join(f"{mean_f1(r['rows'], a, off):18.3f}" for a in ARMS))
        print(f"  {'npred':>7s} " + " ".join(f"{mean_key(r['rows'], a, 500, 'npred'):18.2f}" for a in ARMS))
        print(f"  {'AUC@500':>7s} " + " ".join(f"{mean_key(r['rows'], a, 500, 'auc'):18.3f}" for a in ARMS))
        print(f"  {'AUC@1000':>7s} " + " ".join(f"{mean_key(r['rows'], a, 1000, 'auc'):18.3f}" for a in ARMS))
        for ibd_arm in ("seq_ibd", "seq_ibd_signrand"):
            for comp in ("cusum_literal", "cusum_actinfo", "cusum_probed"):
                m, lo, hi, n = paired(r["rows"], ibd_arm, comp, 500)
                verdict = "SUPERIOR" if lo > 0.10 else ("futile" if hi < 0.10 else "inconclusive")
                print(f"    Delta_F1({ibd_arm:16s} - {comp:15s}) @500 = {m:+.3f}  "
                      f"[{lo:+.3f},{hi:+.3f}] n={n}  -> vs delta_F1=0.10: {verdict}")

    print("\n" + "=" * 100)
    print("C. CO-PRIMARY P2: mean p_c on oracle-labelled confounded distractors (negative control "
          "= unconfounded)")
    print("=" * 100)
    for tag, r in all_res.items():
        if not r["confounded"]:
            continue
        print(f"\ncell {tag}")
        print(f"  {'offset':>7s} " + " ".join(f"{a:>18s}" for a in ARMS))
        for off in OFFSETS_P2:
            print(f"  {off:7d} " + " ".join(f"{mean_key(r['rows'], a, off, 'p_conf'):18.3f}" for a in ARMS))
        print(f"  {'unconf':>7s} " + " ".join(f"{mean_key(r['rows'], a, 200, 'p_unconf'):18.3f}" for a in ARMS))

    print("\n" + "=" * 100)
    print("D. R0 / R1 decision-rule check (contract G under D-8a)")
    print("=" * 100)
    def d500(tag, comp="cusum_actinfo", arm="seq_ibd"):
        return paired(all_res[tag]["rows"], arm, comp, 500)
    for arm_i, comp in (("seq_ibd", "cusum_actinfo"), ("seq_ibd", "cusum_literal"),
                        ("seq_ibd_signrand", "cusum_actinfo")):
        print(f"\ninterventional arm = {arm_i}   comparator = {comp}")
        for tag in ("R0-conf-present-Nx10", "R0-conf-absent-Nx10",
                    "R1-conf-present-Nx10", "R1-conf-absent-Nx10"):
            if tag not in all_res: continue
            m, lo, hi, n = d500(tag, comp, arm_i)
            print(f"  Delta_F1 @500 {tag:24s} = {m:+.3f} [{lo:+.3f},{hi:+.3f}]")
        try:
            r1p = d500("R1-conf-present-Nx10", comp, arm_i)[0]; r1a = d500("R1-conf-absent-Nx10", comp, arm_i)[0]
            r0p = d500("R0-conf-present-Nx10", comp, arm_i)[0]; r0a = d500("R0-conf-absent-Nx10", comp, arm_i)[0]
            I = (r1p - r1a) - (r0p - r0a)
            print(f"  interaction I (v4.1 E1, restated for Delta_F1) = {I:+.3f}   "
                  f"[simple confounding contrast in R0 = {r0p - r0a:+.3f}]")
            m, lo, hi, n = d500("R0-conf-present-Nx10", comp, arm_i)
            tost = (lo > -0.05 and hi < 0.05)
            print(f"  contract-G R0 rule (TOST inside +-delta0_F1=0.05) on the confounder-PRESENT "
                  f"cell: {'validated' if tost else 'NOT validated -> classified an anomaly'}")
        except Exception as e:
            print("  interaction not computable:", e)

    print("\n" + "=" * 100)
    print("E. CALIBRATION-PROTOCOL GATES AND THE TRANSITION BAND")
    print("=" * 100)
    for tag, r in all_res.items():
        g = r["cal_gates"]
        print(f"  {tag:26s} distinct g values={g['T_IBD_cal_1_distinct_values']:5d} "
              f"minority={g['T_IBD_cal_2_minority_share']:.3f} monotone={g['T_IBD_cal_3_monotone']} "
              f"max g={g['g_max']:.3f} (clean band {g['g_max_cleanband']:.3f}) "
              f"pairs in transition band={g['frac_pairs_in_transition_band']:.3f}")

    print("\n" + "=" * 100)
    print("G. IS a_c MONOTONE IN SUPPORT? ablation of the task-policy null (12 episodes each)")
    print("=" * 100)
    print(f"  {'setting':52s} {'direct':>8s} {'indirect':>9s} {'non-reach':>10s} "
          f"{'max|corr(a,x)|':>15s} {'probe/RMS':>10s}")
    for label, d, i2, nr, rho, ratio in attack_null_under_u():
        print(f"  {label:52s} {d:+8.2f} {i2:+9.2f} {nr:+10.2f} {rho:15.3f} {ratio:10.2f}")
    print("  (support-monotone would need direct > indirect > non-reach; p_c = g(a_c) with g "
          "non-decreasing can only be correct if that ordering holds)")

    print("\n" + "=" * 100)
    print("F. CERTIFICATIONS")
    print("=" * 100)
    for tag, r in all_res.items():
        c = r["cert"]
        print(f"  {tag:26s} rho_cl {c['rho_cl_pre']:.3f}/{c['rho_cl_post']:.3f} (<= {RHO_CL}) "
              f"sat {c['sat_frac']:.4f} (<0.05) max|corr(a,x)| {c['max_corr_a_x']:.3f} "
              f"(>= {RHO_MIN} required when confounded) probes {c['probe_steps_used']} "
              f"(<= {math.floor(PROBE_BUDGET*EPISODE_LEN)}) s_change {c['s_change_certified']} "
              f"min|e-eps| {min(c['min_margin_pre'], c['min_margin_post']):.3f} "
              f"probe/RMS {c['probe_mag_over_action_RMS']:.2f}")
    log("done")
