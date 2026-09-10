"""End-to-end independent reproduction of BOTH confirmatory arms of frozen version 442cc4b7da691ca0.

Written from `stage-0a-contract-v3.5.md`, `sequential-ibd-spec.md` (draft 3) and `comparator-spec.md`
ALONE.  No review*/ simulation was read before this file was complete.  Every place where the specs
left a free choice is marked `# CHOICE-nn` and listed in findings.md as a spec defect.

Arms implemented
  arm1  seq_ibd                        sequential-ibd-spec.md draft 3  (sign-randomised rank-sum contrast)
  arm2  cusum_linear_channel_agnostic  comparator-spec.md sec 1-3      (passive innovation shift)
  arm3  cusum_linear_probed            comparator-spec.md sec 4        (same score on the probed stream)

Primary outcome reproduced: threshold-free AUC of the RAW per-channel statistic at offset 500,
confounder present and absent, N_x in {10, 30}, and the confounding benefit contrast
[dAUC(present) - dAUC(absent)] with paired 95% t intervals over >= 30 seeds.

Extensions (contract regions with no D-9 evidence): family N, tau = 2, N_x = 100.
Diagnostics: warm-up transient of the IBD alarm statistic; n_min_sign usability by offset;
tie-corrected rank-sum formula check.

Run:  /Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3 sim_e2e.py
"""
import math
import sys
import time
import numpy as np

# ----------------------------------------------------------------------------------------------
# Contract v3.5 section 0 registry
# ----------------------------------------------------------------------------------------------
EPS          = 0.05
H            = 3
HSET         = (1, 2, 3)
A_MAG        = 1.0            # probe magnitude, A = +- e_k
C_MIN        = 0.2
RHO_MAX      = 0.95
RHO_U        = 0.8
A_MAX        = 2.0
RHO_MIN      = 0.4
N_ORACLE     = 4096
PROBE_BUDGET = 0.05
F_CONF       = 0.5
N_B, N_D, N_W, K = 4, 2, 4, 2
SIG_B = SIG_D = SIG_W = SIG_X = 0.1
SIG_O = 0.05
SIG_A = 0.1
SIG_U = 1.0
EPISODE_LEN, EVENT_T = 2000, 1000
OFFSETS_RANK = (200, 500, 1000)
PRIMARY_OFFSET = 500
N_MIN_SIGN   = 3
RHO_CL       = 0.98
S_SAT, KAPPA, M_CLIP = 1.0, 0.1, 4.0      # family N

# ----------------------------------------------------------------------------------------------
# sequential-ibd-spec.md draft 3 constants
# ----------------------------------------------------------------------------------------------
PI_CADENCE = 20
W_STEPS    = 500
Z_CAP      = 8.0
V_FLOOR    = 0.5

# ----------------------------------------------------------------------------------------------
# comparator-spec.md constants
# ----------------------------------------------------------------------------------------------
LAM_REL     = 1e-4
W_CMP       = 500
SIG_FLOOR   = 1e-6
SIG_DEG     = 1e-3
Q_CAP       = 40.0
N_WARM      = 30
N_PRED_FIT  = 20          # episodes (comparator-spec sec 1, [prov])
KMULT       = 0.5

# CHOICE-01  n_u (dimension of the exogenous context u) is nowhere in the registry.  Set to 1.
N_U = 1
# CHOICE-02  C (observation channel count) is nowhere in the registry.  comparator-spec sec 7 quotes
#            C = 24 at N_x = 10 and C = 114 at N_x = 100, and confirmation-design.csv carries
#            n_channels = 24 at N_x = 10, so C = N_z + 4.  Composition of those 4 extra channels
#            (how many copies, how many pads, which latent is copied) is NOT specified anywhere.
#            Adopted: 2 copies (one body channel b0, one distractor x0) + 2 padding channels.
N_EXTRA = 4
# CHOICE-03  Sparsity patterns of A_b, A_d, A_w, A_x, C_d, B, W_o, W_u, G are unspecified.
# CHOICE-04  gain_t is unspecified for the baseline draw.  All gains = 1.
# CHOICE-05  Which channels the policy observes (support of W_o) is unspecified.  Body channels only.
# CHOICE-06  Burn-in before t = 1 is unspecified for scored episodes (burn_in = 2000 in the registry
#            is only for the stationary-mean estimate).  Adopted 200 steps.
BURN_IN_EP = 200
# CHOICE-07  The AUC tie convention is unspecified in both specs; both arms produce exact ties
#            (a_c = 0 for unusable channels, q_c = -Q_CAP for degenerate ones).  Mid-rank
#            Mann-Whitney AUC adopted (ties score 0.5).
# CHOICE-08  C2's expectation has no declared initial state (C4's does: z-bar).  Adopted z-bar.
# CHOICE-09  Neither spec says which instance the calibration split is drawn from
#            (confirmation-design.csv gives calibration rows seed = -1).  Adopted: the arm's frozen
#            per-channel objects are fitted on fault-free episodes of the SAME instance as the
#            scored episode.  This is the most favourable reading for the comparator; see findings.


# ==============================================================================================
#  Instance sampling (contract sec B, family L and family N)
# ==============================================================================================
def _scale_rho(M, cap):
    r = max(abs(np.linalg.eigvals(M)))
    return M * (cap / r) if r > cap else M


def sample_instance(seed, n_x, family="L", tau=0, confounder=True):
    """Draw a contract-B instance.  Returns a dict; certification is done by certify()."""
    rng = np.random.default_rng(100000 + seed * 17 + n_x)

    def signed(shape, lo, hi):
        return rng.uniform(lo, hi, shape) * rng.choice([-1.0, 1.0], shape)

    # A_b : two uncoupled 2x2 blocks {b0,b1} and {b2,b3} so that losing actuator 0 provably
    # removes b0,b1 from reachability within H (contract D, primary-cell constraint CL-4).
    A_b = np.zeros((N_B, N_B))
    for blk in (0, 2):
        A_b[blk, blk] = rng.uniform(0.35, 0.65) * rng.choice([-1.0, 1.0])
        A_b[blk + 1, blk + 1] = rng.uniform(0.35, 0.65) * rng.choice([-1.0, 1.0])
        A_b[blk + 1, blk] = signed((), C_MIN, 0.35)          # |entry| >= c_min
    A_b = _scale_rho(A_b, RHO_MAX)

    B = np.zeros((N_B, K))                                    # rows 0,1 <- act0 ; rows 2,3 <- act1
    B[0, 0] = signed((), 0.7, 1.0); B[1, 0] = signed((), 0.4, 0.8)
    B[2, 1] = signed((), 0.7, 1.0); B[3, 1] = signed((), 0.4, 0.8)

    A_d = _scale_rho(np.diag(rng.uniform(0.3, 0.6, N_D) * rng.choice([-1.0, 1.0], N_D)), RHO_MAX)
    C_d = np.zeros((N_D, N_B))
    C_d[0, 0] = signed((), 0.4, 0.8)                          # d0 <- b0  (lost with actuator 0)
    C_d[1, 2] = signed((), 0.4, 0.8)                          # d1 <- b2  (retained)
    A_w = _scale_rho(np.diag(rng.uniform(0.3, 0.8, N_W) * rng.choice([-1.0, 1.0], N_W)), RHO_MAX)
    A_x = _scale_rho(np.diag(rng.uniform(0.3, 0.7, n_x) * rng.choice([-1.0, 1.0], n_x)), RHO_MAX)

    n_conf = int(round(F_CONF * n_x))                          # f_conf = 0.5 locked
    G = np.zeros((n_x, N_U))
    if confounder:
        G[:n_conf, :] = signed((n_conf, N_U), 0.6, 1.0)
    conf_latent = np.zeros(n_x, bool); conf_latent[:n_conf] = True

    W_u = signed((K, N_U), 0.35, 0.50)

    # observation map: b(4) d(2) w(4) x(n_x) | copy(b0) copy(x0) pad pad
    C = N_B + N_D + N_W + n_x + N_EXTRA
    N_Z = N_B + N_D + N_W + n_x
    assign = np.full(C, -1, int)
    assign[:N_Z] = np.arange(N_Z)
    assign[N_Z] = 0                                            # copy of b0
    assign[N_Z + 1] = N_B + N_D + N_W                          # copy of x0
    gain = np.ones(C); avail = np.ones(C, bool)

    W_o = np.zeros((K, C))                                     # feedback on body channels only
    W_o[0, 0] = signed((), 0.05, 0.15); W_o[0, 1] = signed((), 0.05, 0.15)
    W_o[1, 2] = signed((), 0.05, 0.15); W_o[1, 3] = signed((), 0.05, 0.15)

    return dict(A_b=A_b, B=B, A_d=A_d, C_d=C_d, A_w=A_w, A_x=A_x, G=G, W_u=W_u, W_o=W_o,
                assign=assign, gain=gain, avail=avail, C=C, N_Z=N_Z, n_x=n_x, tau=tau,
                family=family, conf_latent=conf_latent, seed=seed)


# ==============================================================================================
#  Oracle (contract C1-C4).  Separate from the estimators; never handed to them.
# ==============================================================================================
def latent_effect_L(inst, B):
    """C2 for family L: closed form, exact.  e_j = max_{h<=H, a in A} |E[z_{j,t+h}|do(a)] - E[.|do(0)]|."""
    tau = inst["tau"]; A_b, A_d, C_d = inst["A_b"], inst["A_d"], inst["C_d"]
    e = np.zeros(inst["N_Z"])
    resp_b = {}
    for h in range(1, H + 1):
        resp_b[h] = np.linalg.matrix_power(A_b, h - 1 - tau) @ B if h >= tau + 1 else np.zeros((N_B, K))
    for h in range(1, H + 1):
        e[:N_B] = np.maximum(e[:N_B], np.abs(resp_b[h] * A_MAG).max(axis=1))
        rd = np.zeros((N_D, K))
        for m in range(tau + 1, h):
            rd += np.linalg.matrix_power(A_d, h - 1 - m) @ C_d @ resp_b[m]
        e[N_B:N_B + N_D] = np.maximum(e[N_B:N_B + N_D], np.abs(rd * A_MAG).max(axis=1))
    return e                                                    # w and x stay exactly 0


def latent_effect_MC(inst, B, zbar, n=N_ORACLE):
    """C2 by paired Monte Carlo with common random numbers (used for family N)."""
    rng = np.random.default_rng(555 + inst["seed"])
    A_b, A_d, C_d = inst["A_b"], inst["A_d"], inst["C_d"]
    tau = inst["tau"]; N_Z = inst["N_Z"]
    probes = [s * np.eye(K)[k] * A_MAG for k in range(K) for s in (+1.0, -1.0)]
    eb = np.zeros(N_Z)
    noise_b = rng.normal(0, SIG_B, (n, H, N_B)); noise_d = rng.normal(0, SIG_D, (n, H, N_D))

    def roll(act):
        b = np.tile(zbar[:N_B], (n, 1)); d = np.tile(zbar[N_B:N_B + N_D], (n, 1))
        out = np.zeros((H, N_Z))
        aq = [np.zeros(K)] * (tau + 1)
        for h in range(1, H + 1):
            a_now = act if h == 1 else np.zeros(K)
            aq.append(a_now)
            a_eff = aq[len(aq) - 1 - tau]
            if inst["family"] == "N":
                drive = (b @ A_b.T + np.tanh((a_eff @ B.T) / S_SAT) * S_SAT
                         + KAPPA * np.clip(b * b, -M_CLIP, M_CLIP))
            else:
                drive = b @ A_b.T + a_eff @ B.T
            d = d @ A_d.T + b @ C_d.T + noise_d[:, h - 1]
            b = drive + noise_b[:, h - 1]
            out[h - 1, :N_B] = b.mean(0); out[h - 1, N_B:N_B + N_D] = d.mean(0)
        return out

    base = roll(np.zeros(K))
    for p in probes:
        eb = np.maximum(eb, np.abs(roll(p) - base).max(axis=0))
    eb[N_B + N_D:] = 0.0
    return eb


def s_obs_eps(e_latent, inst):
    """C3: channel c in support iff avail and assign valid and |gain_c| * e_j > eps."""
    out = np.zeros(inst["C"], bool)
    for c in range(inst["C"]):
        j = inst["assign"][c]
        if j < 0 or not inst["avail"][c]:
            continue
        out[c] = abs(inst["gain"][c]) * e_latent[j] > EPS
    return out


# ==============================================================================================
#  Environment roll-out (contract sec B), batched over episodes
# ==============================================================================================
def rollout(inst, n_ep, T, noise_seed, probe_rng_seed=None, event=True):
    """Return o[n_ep, T+2, C] (o_t for t = 1..T+1 at index t) and a[n_ep, T+1, K], plus probe log.

    Event = complete loss of actuator 0, applied BEFORE step EVENT_T is taken
    (sequential-ibd-spec sec 4 convention).
    """
    rng = np.random.default_rng(noise_seed)
    prng = np.random.default_rng(probe_rng_seed) if probe_rng_seed is not None else None
    A_b, A_d, A_w, A_x = inst["A_b"], inst["A_d"], inst["A_w"], inst["A_x"]
    B0, C_d, G, W_u, W_o = inst["B"], inst["C_d"], inst["G"], inst["W_u"], inst["W_o"]
    tau, C, N_Z, n_x = inst["tau"], inst["C"], inst["N_Z"], inst["n_x"]
    assign, gain, avail = inst["assign"], inst["gain"], inst["avail"]
    fam = inst["family"]

    B_post = B0.copy(); B_post[:, 0] = 0.0                     # complete actuator loss, D

    b = np.zeros((n_ep, N_B)); d = np.zeros((n_ep, N_D))
    w = np.zeros((n_ep, N_W)); x = np.zeros((n_ep, n_x)); u = np.zeros((n_ep, N_U))
    aq = [np.zeros((n_ep, K)) for _ in range(tau + 1)]

    o_hist = np.zeros((n_ep, T + 2, C)); a_hist = np.zeros((n_ep, T + 2, K))
    probes = []                                                # (t, k, sign) shared schedule, per-episode signs
    probe_ks = np.zeros((n_ep, T + 2), int); probe_sg = np.zeros((n_ep, T + 2))
    is_probe = np.zeros(T + 2, bool)
    used, t_last, sat_hits, sat_n = 0, -PI_CADENCE, 0, 0

    Sel = np.zeros((C, N_Z))                                   # o = Sel z + eps^o  (sec B)
    for c in range(C):
        j = assign[c]
        if j >= 0 and avail[c]:
            Sel[c, j] = gain[c]

    def observe():
        z = np.concatenate([b, d, w, x], axis=1)
        return z @ Sel.T + rng.normal(0, SIG_O, (n_ep, C))

    total = BURN_IN_EP + T + 1
    for step in range(1, total + 1):
        t = step - BURN_IN_EP                                  # scored clock; t >= 1 is the episode
        o = observe()
        if 1 <= t <= T + 1:
            o_hist[:, t] = o
        a = np.clip(o @ W_o.T + u @ W_u.T + rng.normal(0, SIG_A, (n_ep, K)), -A_MAX, A_MAX)
        raw = o @ W_o.T + u @ W_u.T
        sat_hits += int((np.abs(raw) > A_MAX).sum()); sat_n += raw.size
        if prng is not None and 1 <= t <= T:
            # sequential-ibd-spec sec 2 budget rule, charged against the step about to be taken
            if used + 1 <= math.floor(PROBE_BUDGET * t) and t - t_last >= PI_CADENCE:
                used += 1; t_last = t; is_probe[t] = True
                kk = prng.integers(0, K, n_ep); sg = prng.choice(np.array([1.0, -1.0]), n_ep)
                a = np.zeros((n_ep, K)); a[np.arange(n_ep), kk] = sg * A_MAG
                probe_ks[:, t] = kk; probe_sg[:, t] = sg
                probes.append(t)
        if 1 <= t <= T + 1:
            a_hist[:, t] = a
        aq.append(a); a_eff = aq[len(aq) - 1 - tau]
        Bt = B_post if (event and t >= EVENT_T) else B0
        if fam == "N":
            b_new = b @ A_b.T + np.tanh((a_eff @ Bt.T) / S_SAT) * S_SAT \
                    + KAPPA * np.clip(b * b, -M_CLIP, M_CLIP) + rng.normal(0, SIG_B, (n_ep, N_B))
        else:
            b_new = b @ A_b.T + a_eff @ Bt.T + rng.normal(0, SIG_B, (n_ep, N_B))
        d = d @ A_d.T + b @ C_d.T + rng.normal(0, SIG_D, (n_ep, N_D))
        w = w @ A_w.T + rng.normal(0, SIG_W, (n_ep, N_W))
        x = x @ A_x.T + u @ G.T + rng.normal(0, SIG_X, (n_ep, n_x))
        u = RHO_U * u + rng.normal(0, SIG_U, (n_ep, N_U))
        b = b_new
    return dict(o=o_hist, a=a_hist, probes=probes, probe_k=probe_ks, probe_s=probe_sg,
                is_probe=is_probe, sat=sat_hits / max(sat_n, 1), B_post=B_post)


# ==============================================================================================
#  Arm 1: sequential IBD, draft 3
# ==============================================================================================
def ranksum_z(gp, gm):
    """Tie-corrected rank-sum z, sequential-ibd-spec sec 3.  Mid-ranks, no continuity correction."""
    n1, n2 = len(gp), len(gm)
    N = n1 + n2
    vals = np.concatenate([gp, gm])
    order = np.argsort(vals, kind="mergesort")
    sv = vals[order]
    ranks = np.empty(N)
    i = 0
    tie_term = 0.0
    while i < N:
        j = i
        while j + 1 < N and sv[j + 1] == sv[i]:
            j += 1
        mid = (i + j) / 2.0 + 1.0
        ranks[i:j + 1] = mid
        tg = j - i + 1
        if tg > 1:
            tie_term += tg ** 3 - tg
        i = j + 1
    r = np.empty(N); r[order] = ranks
    R1 = r[:n1].sum()
    U = R1 - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0
    var = (n1 * n2 / (N * (N - 1.0))) * ((N ** 3 - N) / 12.0 - tie_term / 12.0)
    if var <= 0:
        return None
    return (U - mu) / math.sqrt(var)


def ibd_a_at_epoch(roll, ep, t_epoch, inst):
    """Raw per-channel statistic a_c at the epoch whose newest anchor is t_epoch - max(HSET)."""
    tp_star = t_epoch - max(HSET)
    anchors = [t for t in roll["probes"] if tp_star - W_STEPS < t <= tp_star]
    C = inst["C"]
    o = roll["o"][ep]
    if not anchors:
        return np.zeros(C), 0
    A = np.array(anchors)
    D = np.stack([o[A + h] - o[A] for h in HSET], axis=0)        # [|H|, n_units, C]
    ks = roll["probe_k"][ep, A]; sgs = roll["probe_s"][ep, A]
    a_c = np.zeros(C); usable = 0
    cells = []; dropped_k = []
    for k2 in range(K):
        pmask = (ks == k2) & (sgs > 0); mmask = (ks == k2) & (sgs < 0)
        if min(pmask.sum(), mmask.sum()) < N_MIN_SIGN:
            dropped_k.append(k2); continue
        cells.append((k2, pmask, mmask))
    ibd_a_at_epoch.last_dropped = dropped_k
    zz = np.zeros((len(cells) * len(HSET), C)); n_used = 0
    for (k2, pmask, mmask) in cells:
        for hi in range(len(HSET)):
            for c in range(C):
                z = ranksum_z(D[hi, pmask, c], D[hi, mmask, c])
                if z is None:
                    continue
                zz[n_used, c] = min(max(z, -Z_CAP), Z_CAP)
            n_used += 1
    if n_used == 0:
        return np.zeros(C), 0
    a_c = np.abs(zz[:n_used]).max(axis=0)
    return a_c, n_used


# ==============================================================================================
#  Arm 2/3: passive and probed comparator
# ==============================================================================================
def fit_comparator(inst, noise_seed):
    """comparator-spec sec 1: penalised LS on n_pred_fit fault-free, in-distribution, non-probed episodes."""
    r = rollout(inst, N_PRED_FIT, EPISODE_LEN, noise_seed, probe_rng_seed=None, event=False)
    o = r["o"]; a = r["a"]; C = inst["C"]
    X = np.concatenate([o[:, 1:EPISODE_LEN + 1].reshape(-1, C),
                        a[:, 1:EPISODE_LEN + 1].reshape(-1, K),
                        np.ones((N_PRED_FIT * EPISODE_LEN, 1))], axis=1)
    Y = o[:, 2:EPISODE_LEN + 2].reshape(-1, C)
    XtX = X.T @ X
    lam = LAM_REL * np.trace(XtX) / (C + K)
    Dm = np.eye(C + K + 1); Dm[-1, -1] = 0.0                    # intercept never penalised
    beta = np.linalg.solve(XtX + lam * Dm, X.T @ Y)
    R = Y - X @ beta
    mu = R.mean(0); sd_raw = R.std(0, ddof=1)
    sd = np.maximum(sd_raw, SIG_FLOOR)
    degen = sd_raw < SIG_DEG
    l = np.linalg.norm(beta[C:C + K, :], axis=0) / sd
    Rt = np.clip((R - mu) / sd, -Z_CAP, Z_CAP)
    live = ~degen
    m = np.abs(Rt[:, live]).max(axis=1) if live.any() else np.zeros(len(Rt))
    kref = m.mean() + KMULT * m.std(ddof=1)
    return dict(beta=beta, mu=mu, sd=sd, l=l, degen=degen, k=kref)


def cmp_q_at(roll, ep, t, fit, inst):
    """comparator-spec sec 2 score at environment step t.  q_c = l_c - |sqrt(n) * mean(r~)| over [t-n+1, t]."""
    C = inst["C"]
    n = min(W_CMP, t)
    lo = t - n + 1
    o = roll["o"][ep]; a = roll["a"][ep]
    X = np.concatenate([o[lo:t + 1], a[lo:t + 1], np.ones((n, 1))], axis=1)
    R = o[lo + 1:t + 2] - X @ fit["beta"]
    Rt = np.clip((R - fit["mu"]) / fit["sd"], -Z_CAP, Z_CAP)
    shift = 0.0 if t < N_WARM else np.abs(math.sqrt(n) * Rt.mean(0))
    q = np.clip(fit["l"] - shift, -Q_CAP, Q_CAP)
    q[fit["degen"]] = -Q_CAP
    return q


# ==============================================================================================
#  Scoring
# ==============================================================================================
def auc(scores, labels):
    """Mid-rank Mann-Whitney AUC (CHOICE-07)."""
    labels = np.asarray(labels, bool); s = np.asarray(scores, float)
    npos, nneg = labels.sum(), (~labels).sum()
    if npos == 0 or nneg == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort"); sv = s[order]
    ranks = np.empty(len(s)); i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and sv[j + 1] == sv[i]:
            j += 1
        ranks[i:j + 1] = (i + j) / 2.0 + 1.0
        i = j + 1
    r = np.empty(len(s)); r[order] = ranks
    return float((r[labels].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))


def t_ci(v, level=0.95):
    v = np.asarray(v, float); v = v[~np.isnan(v)]
    n = len(v)
    if n < 2:
        return float("nan"), float("nan"), float("nan")
    m = v.mean(); se = v.std(ddof=1) / math.sqrt(n)
    # two-sided t quantile without scipy (Hill's approximation is unnecessary: use a table + interp)
    tq = _tquant(0.5 + level / 2.0, n - 1)
    return m, m - tq * se, m + tq * se


_T_TABLE = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
            9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086, 24: 2.064, 29: 2.045,
            30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980, 100000: 1.960}
_T_TABLE90 = {9: 1.833, 29: 1.699, 30: 1.697, 100000: 1.645}


def _tquant(p, df):
    tab = _T_TABLE if abs(p - 0.975) < 1e-9 else _T_TABLE90
    ks = sorted(tab)
    for i, kk in enumerate(ks):
        if df <= kk:
            return tab[kk]
    return tab[ks[-1]]


# ==============================================================================================
#  One (seed, cell) evaluation
# ==============================================================================================
def eval_cell(seed, n_x, family="L", tau=0, confounder=True, offsets=(500,), want_diag=False):
    inst = sample_instance(seed, n_x, family, tau, confounder)
    # ---- certification (contract sec B / C2) --------------------------------------------------
    B_post = inst["B"].copy(); B_post[:, 0] = 0.0
    if family == "L":
        e_pre = latent_effect_L(inst, inst["B"]); e_post = latent_effect_L(inst, B_post)
    else:
        zbar = np.zeros(inst["N_Z"])
        e_pre = latent_effect_MC(inst, inst["B"], zbar); e_post = latent_effect_MC(inst, B_post, zbar)
    s_post = s_obs_eps(e_post, inst); s_pre = s_obs_eps(e_pre, inst)
    if s_post.tolist() == s_pre.tolist():
        return None                                            # CL-4: S must change; resample
    if min(abs(e_pre[e_pre > 0] - EPS).min(), abs(e_post[e_post > 0] - EPS).min()) < 0.02:
        return None                                            # C2 near-threshold rejection

    # ---- streams ------------------------------------------------------------------------------
    ns = 900000 + seed * 31 + n_x * 7 + tau * 3 + (1 if family == "N" else 0)
    probed = rollout(inst, 1, EPISODE_LEN, ns, probe_rng_seed=7000 + seed, event=True)
    passive = rollout(inst, 1, EPISODE_LEN, ns, probe_rng_seed=None, event=True)
    fit = fit_comparator(inst, ns + 500000)

    # ---- rho_min certification on the passive stream (E2c) ------------------------------------
    aa = passive["a"][0, 1:EPISODE_LEN + 1]
    xx = passive["o"][0, 1:EPISODE_LEN + 1][:, N_B + N_D + N_W:N_B + N_D + N_W + n_x]
    best = 0.0
    for kk in range(K):
        for jj in range(min(n_x, 10)):
            if aa[:, kk].std() > 0 and xx[:, jj].std() > 0:
                best = max(best, abs(np.corrcoef(aa[:, kk], xx[:, jj])[0, 1]))
    rho_obs = best

    if confounder and rho_obs < RHO_MIN:
        return None                                            # contract sec 0 rho_min floor
    if passive["sat"] > 0.05:
        return None                                            # OP-16 saturation rejection

    out = dict(seed=seed, n_x=n_x, family=family, tau=tau, confounder=confounder,
               n_pos=int(s_post.sum()), C=inst["C"], rho_min_obs=rho_obs,
               sat=passive["sat"], degen=int(fit["degen"].sum()))
    for off in offsets:
        t_read = EVENT_T + off
        t_epoch = max(t for t in range(23, t_read + 1) if (t - 23) % PI_CADENCE == 0)
        a_c, ncells = ibd_a_at_epoch(probed, 0, t_epoch, inst)
        q2 = cmp_q_at(passive, 0, t_read, fit, inst)
        q3 = cmp_q_at(probed, 0, t_read, fit, inst)
        out[f"auc_ibd@{off}"] = auc(a_c, s_post)
        out[f"auc_cmp@{off}"] = auc(q2, s_post)
        out[f"auc_prb@{off}"] = auc(q3, s_post)
        out[f"cells@{off}"] = ncells
        out[f"dropped_live_k@{off}"] = int(1 in getattr(ibd_a_at_epoch, "last_dropped", []))
        out[f"azero@{off}"] = int((a_c == 0).sum())
    # ---- comparator-spec sec 9 fixtures F1 and F2, evaluated on this instance ----------------
    lost = np.zeros(inst["C"], bool); lost[[0, 1]] = True; lost[inst["N_Z"]] = True   # b0,b1,copy(b0)
    lost[N_B] = True                                                                  # d0
    live = np.zeros(inst["C"], bool); live[[2, 3]] = True; live[N_B + 1] = True       # b2,b3,d1
    xsl = slice(N_B + N_D + N_W, N_B + N_D + N_W + n_x)
    out["l_max_conf_x"] = float(fit["l"][xsl][inst["conf_latent"]].max())
    out["l_min_true_pos"] = float(fit["l"][s_post].min())
    out["F1_l_pathology"] = bool(out["l_max_conf_x"] > out["l_min_true_pos"])
    q_pre = cmp_q_at(passive, 0, EVENT_T - 1, fit, inst)
    q_post = cmp_q_at(passive, 0, EVENT_T + 500, fit, inst)
    out["dq_lost"] = float((q_post - q_pre)[lost].mean())
    out["dq_live"] = float((q_post - q_pre)[live].mean())
    out["shift_lost"] = float((fit["l"] - q_post)[lost].mean())
    out["shift_live"] = float((fit["l"] - q_post)[live].mean())
    # class-resolved baseline support term l_c  (comparator-spec sec 2)
    NZ = inst["N_Z"]; cx = np.arange(n_x)[inst["conf_latent"]] + N_B + N_D + N_W
    ux = np.arange(n_x)[~inst["conf_latent"]] + N_B + N_D + N_W
    out["l_b_live"] = float(fit["l"][[2, 3]].mean()); out["l_b_lost"] = float(fit["l"][[0, 1]].mean())
    out["l_d_live"] = float(fit["l"][N_B + 1]);       out["l_d_lost"] = float(fit["l"][N_B])
    out["l_w"] = float(fit["l"][N_B + N_D:N_B + N_D + N_W].mean())
    out["l_conf_x"] = float(fit["l"][cx].mean());     out["l_unconf_x"] = float(fit["l"][ux].mean())
    out["l_pad"] = float(fit["l"][NZ + 2:NZ + 4].mean())
    # comparator AUC with downstream (d) positives removed from the label set
    keep = np.ones(inst["C"], bool); keep[N_B:N_B + N_D] = False
    out["auc_cmp_no_d"] = auc(q_post[keep], s_post[keep])
    out["auc_ibd_no_d"] = None
    if want_diag:
        out["diag"] = warmup_diag(inst, fit, ns, seed)
    return out


# ==============================================================================================
#  Diagnostic: warm-up transient of the IBD alarm statistic (sequential-ibd-spec sec 5)
# ==============================================================================================
def warmup_diag(inst, fit, ns, seed):
    """Compute a_bar, v on pre-event segments of event-free episodes, then compare
    (i) the warm-up value of stat  vs  (ii) the largest post-event excursion of stat."""
    n_free = 6
    free = rollout(inst, n_free, EPISODE_LEN, ns + 11, probe_rng_seed=7000 + seed, event=False)
    epochs_full = [t for t in range(23, EPISODE_LEN + 1, PI_CADENCE) if t - max(HSET) >= W_STEPS]
    A = []
    for ep in range(n_free):
        for te in epochs_full:
            A.append(ibd_a_at_epoch(free, ep, te, inst)[0])
    A = np.array(A)
    a_bar = np.median(A, axis=0)
    mad = np.median(np.abs(A - a_bar), axis=0)
    v = np.maximum(1.4826 * mad, V_FLOOR)
    # warm-up: a_c = 0 for every channel
    stat_warm = float(np.max(np.abs(0.0 - a_bar) / v))
    stat_null = np.array([float(np.max(np.abs(a - a_bar) / v)) for a in A])
    ev = rollout(inst, 1, EPISODE_LEN, ns + 12, probe_rng_seed=7000 + seed, event=True)
    post = [t for t in range(23, EPISODE_LEN + 1, PI_CADENCE) if t - max(HSET) >= EVENT_T]
    stat_post = np.array([float(np.max(np.abs(ibd_a_at_epoch(ev, 0, te, inst)[0] - a_bar) / v)) for te in post])
    # first epoch at which a_c stops being identically zero on a fresh start
    first_usable = None
    for te in range(23, EPISODE_LEN + 1, PI_CADENCE):
        if ibd_a_at_epoch(free, 0, te, inst)[1] > 0:
            first_usable = te; break
    return dict(stat_warm=stat_warm, stat_null_q99=float(np.quantile(stat_null, 0.99)),
                stat_null_max=float(stat_null.max()), stat_post_max=float(stat_post.max()),
                stat_post_mean=float(stat_post.mean()), first_usable_epoch=first_usable)



# ==============================================================================================
#  Diagnostic 2: ARL_0(h) for the IBD alarm channel (contract sec 0 D-2a; spec sec 5, T-IBD-mono)
# ==============================================================================================
def count_alarms_epochs(raw, p=3, r=1):
    """contract_ref.count_alarms semantics, applied in EPOCHS (spec sec 5, persistence_unit)."""
    counted, run, block = [], 0, -1
    for i, v in enumerate(raw):
        if i <= block:
            run = 0; continue
        run = run + 1 if v else 0
        if run >= p:
            counted.append(i); run = 0; block = i + r
    return counted


def arl_sweep(seed, n_x=10, n_free=25, n_ev=25):
    """Fresh-start ARL_0(h) on event-free streams, and P(detect within H_det) on event streams."""
    inst = sample_instance(seed, n_x, "L", 0, True)
    ns = 900000 + seed * 31 + n_x * 7
    fit_free = rollout(inst, n_free, EPISODE_LEN, ns + 21, probe_rng_seed=7100 + seed, event=False)
    epochs = list(range(23, EPISODE_LEN + 1, PI_CADENCE))
    A = np.array([[ibd_a_at_epoch(fit_free, ep, te, inst)[0] for te in epochs] for ep in range(n_free)])
    full = [i for i, te in enumerate(epochs) if te - max(HSET) >= W_STEPS]
    pool = A[:, full].reshape(-1, inst["C"])
    a_bar = np.median(pool, axis=0)
    v = np.maximum(1.4826 * np.median(np.abs(pool - a_bar), axis=0), V_FLOOR)
    stat_free = np.max(np.abs(A - a_bar) / v, axis=2)                        # [n_free, n_epoch]
    ev = rollout(inst, n_ev, EPISODE_LEN, ns + 22, probe_rng_seed=7100 + seed, event=True)
    Ae = np.array([[ibd_a_at_epoch(ev, ep, te, inst)[0] for te in epochs] for ep in range(n_ev)])
    stat_ev = np.max(np.abs(Ae - a_bar) / v, axis=2)
    warm = float(np.max(np.abs(0.0 - a_bar) / v))
    ncells_full = np.array([[ibd_a_at_epoch(fit_free, ep, epochs[i], inst)[1] for i in full]
                            for ep in range(n_free)])
    zero_frac = float((ncells_full == 0).mean())
    post_null = stat_free[:, [i for i, te in enumerate(epochs) if te >= 500]]
    rows = []
    for h in np.arange(1.0, 9.01, 0.25):
        rl = []
        for ep in range(n_free):
            c = count_alarms_epochs(stat_free[ep] > h)
            rl.append(epochs[c[0]] if c else None)
        obs = [x for x in rl if x is not None]
        cens = len(rl) - len(obs)
        det = 0
        for ep in range(n_ev):
            c = count_alarms_epochs(stat_ev[ep] > h)
            det += any(EVENT_T < epochs[i] <= EVENT_T + 200 for i in c)
        rows.append((h, np.mean(obs) if obs else float('nan'), cens / len(rl), det / n_ev))
    return warm, float(post_null.max()), rows, zero_frac


# ==============================================================================================
#  Diagnostic 3: is the comparator's sqrt(n)*mean(r~) term a standardised statistic?
# ==============================================================================================
def shift_null_diag(seed, n_x=10, tau=0, n_ep=12):
    inst = sample_instance(seed, n_x, "L", tau, True)
    ns = 900000 + seed * 31 + n_x * 7 + tau * 3
    fit = fit_comparator(inst, ns + 500000)
    free = rollout(inst, n_ep, EPISODE_LEN, ns + 31, probe_rng_seed=None, event=False)
    vals = []
    for ep in range(n_ep):
        for t in (1000, 1200, 1500, 1800):
            n = min(W_CMP, t); lo = t - n + 1
            o = free["o"][ep]; a = free["a"][ep]
            X = np.concatenate([o[lo:t + 1], a[lo:t + 1], np.ones((n, 1))], axis=1)
            R = o[lo + 1:t + 2] - X @ fit["beta"]
            Rt = np.clip((R - fit["mu"]) / fit["sd"], -Z_CAP, Z_CAP)
            vals.append(math.sqrt(n) * Rt.mean(0))
    V = np.array(vals)
    NZ = inst["N_Z"]; cx = np.arange(n_x)[inst["conf_latent"]] + N_B + N_D + N_W
    ux = np.arange(n_x)[~inst["conf_latent"]] + N_B + N_D + N_W
    return dict(body=float(V[:, :N_B].std()), d=float(V[:, N_B:N_B + N_D].std()),
                w=float(V[:, N_B + N_D:N_B + N_D + N_W].std()),
                conf_x=float(V[:, cx].std()), unconf_x=float(V[:, ux].std()),
                pad=float(V[:, NZ + 2:NZ + 4].std()))


# ==============================================================================================
#  Self-checks on the two specs' formulas
# ==============================================================================================
def formula_checks():
    print("\n--- spec formula checks ---")
    # (1) tie-corrected rank-sum: untied case must reduce to n1 n2 (N+1) / 12
    rng = np.random.default_rng(0)
    gp = rng.normal(size=7); gm = rng.normal(size=6)
    n1, n2 = 7, 6; N = 13
    z = ranksum_z(gp, gm)
    vals = np.concatenate([gp, gm]); order = np.argsort(vals); r = np.empty(N); r[order] = np.arange(1, N + 1)
    U = r[:n1].sum() - n1 * (n1 + 1) / 2
    z_ref = (U - n1 * n2 / 2) / math.sqrt(n1 * n2 * (N + 1) / 12)
    print(f"  untied reduction:      spec z={z:+.9f}  textbook z={z_ref:+.9f}  diff={abs(z-z_ref):.2e}")
    # (2) tied case, hand fixture: groups {1,1,2} vs {1,2,3}
    gp = np.array([1.0, 1.0, 2.0]); gm = np.array([1.0, 2.0, 3.0])
    n1 = n2 = 3; N = 6
    # ranks: value1 x3 -> midrank 2 ; value2 x2 -> midrank 4.5 ; value3 -> 6
    R1 = 2 + 2 + 4.5
    U = R1 - n1 * (n1 + 1) / 2
    tie = (3 ** 3 - 3) + (2 ** 3 - 2)
    var = (n1 * n2 / (N * (N - 1))) * ((N ** 3 - N) / 12 - tie / 12)
    z_hand = (U - n1 * n2 / 2) / math.sqrt(var)
    print(f"  tied hand fixture:     spec z={ranksum_z(gp, gm):+.9f}  hand z={z_hand:+.9f}"
          f"  diff={abs(ranksum_z(gp,gm)-z_hand):.2e}")
    # (3) equivalence of the two forms the spec gives for sigma_U^2
    v1 = (n1 * n2 / (N * (N - 1))) * ((N ** 3 - N) / 12 - tie / 12)
    v2 = (n1 * n2 / 12.0) * ((N + 1) - tie / (N * (N - 1)))
    print(f"  sigma_U^2 form1={v1:.12f}  form2={v2:.12f}  equal={abs(v1-v2) < 1e-12}")
    # (4) probe grant rule -> 100 applied, 99 usable, all multiples of 20
    used, t_last, granted = 0, -PI_CADENCE, []
    for t in range(1, EPISODE_LEN + 1):
        if used + 1 <= math.floor(PROBE_BUDGET * t) and t - t_last >= PI_CADENCE:
            used += 1; t_last = t; granted.append(t)
    usable = [t for t in granted if t + max(HSET) <= EPISODE_LEN]
    print(f"  probe grants: n={len(granted)} first={granted[0]} last={granted[-1]} "
          f"all_mult_20={all(t % 20 == 0 for t in granted)} usable={len(usable)} "
          f"realised_fraction={len(granted)/EPISODE_LEN}")
    # (5) window / epoch grid and the sec 4 post-event-fraction table
    print("  offset  epoch  newest_anchor  units  post_event_units  fraction")
    for off in (10, 50, 200, 500, 1000):
        tr = EVENT_T + off
        te = max(t for t in range(23, tr + 1) if (t - 23) % PI_CADENCE == 0)
        tps = te - max(HSET)
        anchors = [t for t in range(20, EPISODE_LEN + 1, 20) if tps - W_STEPS < t <= tps]
        pe = sum(1 for t in anchors if t >= EVENT_T)
        print(f"   {off:5d} {te:6d} {tps:14d} {len(anchors):6d} {pe:17d} {pe/len(anchors):9.2f}")


# ==============================================================================================
#  Main
# ==============================================================================================
def run_block(name, seeds, n_x, family="L", tau=0, offsets=(500,), diag_seeds=0):
    rows = {"present": [], "absent": []}
    diags = []
    for s in seeds:
        for conf in (True, False):
            r = eval_cell(s, n_x, family, tau, conf, offsets,
                          want_diag=(conf and len(diags) < diag_seeds))
            if r is None:
                continue
            if r.get("diag"):
                diags.append(r["diag"])
            rows["present" if conf else "absent"].append(r)
    return rows, diags


def report(name, rows, offsets=(500,)):
    print(f"\n================ {name} ================")
    pres = {r["seed"]: r for r in rows["present"]}
    absn = {r["seed"]: r for r in rows["absent"]}
    common = sorted(set(pres) & set(absn))
    print(f"  admissible paired seeds: {len(common)}   C={pres[common[0]]['C']}  "
          f"positives={pres[common[0]]['n_pos']}  degenerate_channels={pres[common[0]]['degen']}")
    print(f"  rho_min observed (present) median = "
          f"{np.median([pres[s]['rho_min_obs'] for s in common]):.3f}  "
          f"(contract floor {RHO_MIN}); saturation fraction median = "
          f"{np.median([pres[s]['sat'] for s in common]):.4f}")
    for off in offsets:
        print(f"  --- offset {off} ---")
        for arm, key in (("seq_ibd", "auc_ibd"), ("cusum_linear_channel_agnostic", "auc_cmp"),
                         ("cusum_linear_probed", "auc_prb")):
            for cond, tab in (("present", pres), ("absent", absn)):
                v = [tab[s][f"{key}@{off}"] for s in common]
                m, lo, hi = t_ci(v)
                print(f"    AUC {arm:32s} {cond:8s} n={len(v):3d}  {m:.3f}  [{lo:.3f}, {hi:.3f}]")
        d_pres = np.array([pres[s][f"auc_ibd@{off}"] - pres[s][f"auc_cmp@{off}"] for s in common])
        d_absn = np.array([absn[s][f"auc_ibd@{off}"] - absn[s][f"auc_cmp@{off}"] for s in common])
        for lbl, v in (("dAUC(present)", d_pres), ("dAUC(absent) ", d_absn)):
            m, lo, hi = t_ci(v)
            print(f"    {lbl}  paired n={len(v)}  {m:+.3f}  95% [{lo:+.3f}, {hi:+.3f}]")
        cb = d_pres - d_absn
        m, lo, hi = t_ci(cb)
        gate = "SUPERIORITY (lb > 0.10)" if lo > 0.10 else ("FUTILITY (ub < 0.10)" if hi < 0.10 else "INCONCLUSIVE")
        print(f"    CONFOUNDING BENEFIT [dAUC(pres) - dAUC(abs)]  {m:+.3f}  95% [{lo:+.3f}, {hi:+.3f}]  -> {gate}")
        # D-9.3 R0-present positive control and R0-absent equivalence
        m2, lo2, hi2 = t_ci(d_pres)
        print(f"    R0-present positive control: lb(dAUC present) = {lo2:+.3f}  "
              f"({'PASS' if lo2 > 0.10 else 'FAIL'} at delta_AUC = 0.10)")
        m3, lo3, hi3 = t_ci(d_absn, level=0.90)
        eq = (lo3 > -0.05) and (hi3 < 0.05)
        print(f"    R0-absent equivalence (90% TOST +-0.05): [{lo3:+.3f}, {hi3:+.3f}] -> "
              f"{'EQUIVALENT' if eq else 'NOT EQUIVALENT'}")
        dk = [pres[s][f"dropped_live_k@{off}"] for s in common]
        print(f"    n_min_sign dropped the SURVIVING actuator's cells in "
              f"{100.0*np.mean(dk):.0f}% of present episodes at this offset")
        cells = [pres[s][f"cells@{off}"] for s in common]
        az = [pres[s][f"azero@{off}"] for s in common]
        print(f"    IBD usable (k,h) cells at this epoch: median {np.median(cells):.0f} of {K*len(HSET)}"
              f"   channels with a_c == 0: median {np.median(az):.0f} of {pres[common[0]]['C']}")
    print("  --- comparator-spec sec 9 fixtures on these instances ---")
    f1 = [pres[s]["F1_l_pathology"] for s in common]
    print(f"    F1 (l_c on a confounded distractor exceeds l_c on a true positive): "
          f"holds in {100.0*np.mean(f1):.0f}% of present episodes")
    aucs = [pres[s][f"auc_cmp@{PRIMARY_OFFSET}"] for s in common]
    print(f"    F1 (episode AUC of q below 0.5 at offset 500, confounder present): "
          f"holds in {100.0*np.mean([a < 0.5 for a in aucs]):.0f}% ; mean AUC {np.mean(aucs):.3f}")
    print(f"    F2 (q falls on channels LEAVING S_obs,eps, flat on channels remaining): "
          f"mean dq on lost = {np.mean([pres[s]['dq_lost'] for s in common]):+.4f}, "
          f"on retained = {np.mean([pres[s]['dq_live'] for s in common]):+.4f}")
    print(f"    innovation-shift term magnitude at offset 500: lost channels "
          f"{np.mean([pres[s]['shift_lost'] for s in common]):.3f}, retained "
          f"{np.mean([pres[s]['shift_live'] for s in common]):.3f}  (q = l - shift)")
    print("    baseline support term l_c by oracle channel class (present cells, mean over seeds):")
    for lbl, key in (("b retained (POSITIVE)", "l_b_live"), ("b lost (negative)", "l_b_lost"),
                     ("d retained (POSITIVE)", "l_d_live"), ("d lost (negative)", "l_d_lost"),
                     ("w exogenous (negative)", "l_w"), ("x confounded (negative)", "l_conf_x"),
                     ("x unconfounded (negative)", "l_unconf_x"), ("padding (negative)", "l_pad")):
        print(f"      l[{lbl:28s}] = {np.mean([pres[s][key] for s in common]):8.3f}")
    a_all = np.mean([pres[s][f"auc_cmp@{PRIMARY_OFFSET}"] for s in common])
    a_nod = np.mean([pres[s]["auc_cmp_no_d"] for s in common])
    print(f"    comparator AUC at 500 with downstream d channels dropped from the label set: "
          f"{a_nod:.3f} (vs {a_all:.3f} with them) -> l_c cannot see downstream support")
    return dict(common=common, pres=pres, absn=absn)


if __name__ == "__main__":
    t0 = time.time()
    print("Independent end-to-end reproduction, frozen version 442cc4b7da691ca0")
    print(f"numpy {np.__version__}  python {sys.version.split()[0]}")
    formula_checks()

    SEEDS = list(range(40))                 # >= 30 admissible pairs required
    OFFS = (200, 500, 1000)

    r10, d10 = run_block("L10", SEEDS, 10, "L", 0, OFFS, diag_seeds=3)
    report("PRIMARY  family L, tau=0, N_x=10, R0 (in-band linear)", r10, OFFS)
    r30, d30 = run_block("L30", SEEDS, 30, "L", 0, OFFS, diag_seeds=0)
    report("PRIMARY  family L, tau=0, N_x=30, R0 (in-band linear)", r30, OFFS)

    print("\n================ IBD ALARM-CHANNEL WARM-UP DIAGNOSTIC (family L, N_x=10) ================")
    print("  stat_warm  = max_c |0 - a_bar_c| / v_c, the value of stat at every epoch before any")
    print("               (k,sign) cell is usable, i.e. on EVERY fresh start (spec sec 5 keeps it in ARL_0)")
    for i, d in enumerate(d10):
        print(f"   instance {i}: first usable epoch t={d['first_usable_epoch']}  stat_warm={d['stat_warm']:.2f}  "
              f"null q99={d['stat_null_q99']:.2f}  null max={d['stat_null_max']:.2f}  "
              f"post-event max={d['stat_post_max']:.2f}  mean={d['stat_post_mean']:.2f}")

    print("\n================ IBD ALARM CHANNEL: ARL_0(h) IS A TWO-VALUED STEP FUNCTION ================")
    print("  p = 3 epochs, r = 1 epoch (spec sec 5).  Fresh-start run length to the first counted alarm,")
    print("  25 event-free episodes; detection = counted alarm in (event_t, event_t + H_det].")
    for sd in (0, 1, 2):
        warm, nullmax, rows, zf = arl_sweep(sd)
        print(f"   instance {sd}: stat_warm={warm:.2f}  max stat over full-window null epochs={nullmax:.2f}"
              f"  -> {'warm-up dominates' if warm > nullmax else 'equal: the null stream CONTAINS the warm-up value'}")
        print(f"      full-window NULL epochs at which n_min_sign leaves 0 usable cells "
              f"(a_c == 0 everywhere, stat = stat_warm): {100*zf:.1f}%")
        print("      h     mean ARL_0 (observed)  censored@2000   P(detect within H_det)")
        for h, m, c, d in rows:
            if h in (3.0, 4.0, 4.5, 5.0, 5.25, 5.5, 5.75, 6.0, 7.0):
                print(f"    {h:5.2f}   {m if m == m else float('nan'):18.1f}   {c:11.2f}   {d:20.2f}")

    print("\n================ COMPARATOR: IS sqrt(n)*mean(r~) A STANDARDISED STATISTIC? ================")
    print("  Null SD of the shift term on fault-free streams; a correctly standardised term has SD 1.")
    for tau_ in (0, 2):
        agg = {}
        for sd in (0, 1, 2):
            d = shift_null_diag(sd, 10, tau_)
            for k_, v_ in d.items():
                agg.setdefault(k_, []).append(v_)
        print(f"   tau={tau_}: " + "  ".join(f"{k_}={np.mean(v_):.2f}" for k_, v_ in agg.items()))

    print("\n================ UNTESTED REGIONS (no D-9 evidence exists for any of these) ================")
    rt2, _ = run_block("Ltau2", SEEDS, 10, "L", 2, OFFS)
    report("family L, tau=2, N_x=10", rt2, OFFS)
    rN, _ = run_block("N10", SEEDS, 10, "N", 0, OFFS)
    report("family N, tau=0, N_x=10", rN, OFFS)
    r100, _ = run_block("L100", list(range(34)), 100, "L", 0, (500,))
    report("family L, tau=0, N_x=100", r100, (500,))

    print(f"\ntotal runtime {time.time() - t0:.1f} s")
