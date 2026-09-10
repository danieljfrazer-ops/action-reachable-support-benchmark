#!/usr/bin/env python3
"""Round-6 independent reimplementation of both confirmatory arms on frozen version 38d161e762a3de76.

Author: claude-opus (round 6, one of three independent implementations). EVERY NUMBER THIS SCRIPT
PRODUCES IS MINE ALONE and is to be adjudicated against the other two implementations.

Arms implemented from the specs alone, before reading any review*/ folder:
  arm 1  seq_ibd                      -- sequential-ibd-spec.md draft 5
  arm 2  cusum_linear_delay_aware     -- comparator-spec.md v3 (passive)
  arm 3  cusum_linear_delay_aware_probed -- optional, reported separately (--arm3)

Normative sources used: roadmap-v4 + v4.1-v4.7, stage-0a-contract-v3.9.md, interface-spec-v5.md,
comparator-spec.md v3, sequential-ibd-spec.md draft 5, reference_generator.py, contract_ref.py.

Usage:  python3 sim_frozen.py <chunk>          chunk in CHUNKS below, writes results/<chunk>.json
        python3 sim_frozen.py report           aggregates results/*.json -> report.txt

SCOPE NOTE (declared, not hidden). The brief asks for the primary/secondary AUCs, the confounding
benefit, the D-10.3 floor, two controls and the n_lost distribution. NONE of those depends on the
alarm threshold h, on (a-bar, v, k), or on the isotonic calibrator g: the primary is invariant to any
monotone map and h enters only `raise`. This script therefore does NOT run fit_alarm_reference, the
D-2a ARL_0 calibration (~9.6e7 environment steps for the IBD arm alone, contract Sec.I) or the
calibrator fit. Alarm-channel numbers are consequently NOT reported. This is a deliberate scope cut
driven by the 20-minute laptop budget and is stated in findings.md.
"""
import sys, os, json, math, copy, time, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
GATE = HERE.parent / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))
from reference_generator import draw_certified, Instance, RESERVED_EP          # noqa: E402
from contract_ref import auc_pre_event_support, auc_prob_superiority           # noqa: E402

RESULTS = HERE / "results"
RESULTS.mkdir(exist_ok=True)

# ---------------------------------------------------------------- registry constants (contract Sec.0)
EPISODE_LEN = 2000
EVENT_T = 1000
EVENT = ("actuator_loss", 0)
OFFSETS = (200, 500, 1000)
PROBE_BUDGET = 0.05

# ---- comparator (comparator-spec.md v3) ----
CMP_LAM_REL = 1e-4
CMP_LAM_A = 1e-6
CMP_KAPPA_MIN = 1e-4
CMP_W = 500
CMP_ZCAP = 8.0
CMP_DCAP = 1e4
CMP_SIG_FLOOR = 1e-6
CMP_S_FLOOR = 1e-8
CMP_SIG_DEG_REL = 1e-2
CMP_L_DEG = 1e-3
CMP_TAU_MAX = 2
CMP_HORIZONS = (1, 2, 3)
CMP_TIE_SIG = 12
CMP_FIT_EPS = tuple(range(900, 920))          # predictor fit split, 20 event-free episodes
CMP_ABSENT = -(CMP_DCAP + 1.0)
CMP_L_ABSENT = -1.0

# ---- sequential IBD (sequential-ibd-spec.md draft 5) ----
IBD_PROBE_NS = 5477
IBD_ARM_ID = 1
IBD_PI = 20
IBD_W = 500
IBD_HSET = (1, 2, 3)
IBD_HMAX = 3
IBD_NMIN = 3
IBD_ZCAP = 8.0

SCORED_EPS = (0, 1, 2, 3)


def round_sig(x, sig=CMP_TIE_SIG):
    """12 significant decimal digits, exactly the specs' `float(f"{v:.11e}")` call."""
    a = np.asarray(x, float)
    flat = a.ravel()
    out = np.array([float(f"{v:.{sig - 1}e}") if np.isfinite(v) else v for v in flat])
    return out.reshape(a.shape)


# ================================================================= generator plumbing
def fresh(inst):
    """Every rollout starts from a deep copy: apply_event mutates B/avail/gain in place with no undo
    (IBD spec Sec.7 T-IBD-instance-reset; comparator spec Sec.1.1 T-CMP-freshcopy)."""
    return copy.deepcopy(inst)


def rollout(inst, ep, actions=None, with_event=False, T=EPISODE_LEN):
    c = fresh(inst)
    r = c.run(T, ep=ep, actions=actions,
              event_t=(EVENT_T if with_event else None),
              event=(EVENT if with_event else None))
    return r, c


# ================================================================= arm 2/3: comparator
def build_design(O, A, C, K):
    """phi_t = [o_t (C), a_t (K), a_{t-1} (K), a_{t-2} (K), 1]; Y_t = o_{t+1}; lags zero-filled at the
    episode boundary (exact: Instance.run re-initialises its delay queue to zeros after burn-in)."""
    T = A.shape[0]
    phi = np.zeros((T, C + 3 * K + 1))
    phi[:, :C] = O[:T]
    phi[:, C:C + K] = A
    phi[1:, C + K:C + 2 * K] = A[:-1]
    phi[2:, C + 2 * K:C + 3 * K] = A[:-2]
    phi[:, -1] = 1.0
    return phi, O[1:T + 1]


def cho_solve(Ao, Bo):
    L = np.linalg.cholesky(Ao)
    y = np.linalg.solve(L, Bo)            # L is triangular; np.linalg.solve is exact here to 1e-14
    return np.linalg.solve(L.T, y)


def fit_predictor(streams, C, K, lam_rel=CMP_LAM_REL, kappa_min=CMP_KAPPA_MIN, lam_a=CMP_LAM_A):
    phis, Ys = [], []
    for O, A in streams:
        p, y = build_design(O, A, C, K)
        phis.append(p); Ys.append(y)
    phi = np.vstack(phis); Y = np.vstack(Ys); n = len(Y)
    m = phi[:, :-1].mean(0)
    s = np.maximum(phi[:, :-1].std(0, ddof=0), CMP_S_FLOOR)
    Xt = np.hstack([(phi[:, :-1] - m) / s, np.ones((n, 1))])
    D = np.diag([1.0] * (C + 3 * K) + [0.0])
    lam = lam_rel * n
    Bt = cho_solve(Xt.T @ Xt + lam * D, Xt.T @ Y)
    beta_raw = Bt[:-1] / s[:, None]
    b_raw = Bt[-1] - (m / s) @ Bt[:-1]
    R = Y - Xt @ Bt
    mu = R.mean(0)
    sd = np.maximum(R.std(0, ddof=1), CMP_SIG_FLOOR)
    bo = beta_raw[:C]
    ba = [beta_raw[C + j * K:C + (j + 1) * K] for j in range(3)]
    J = np.zeros((K, C)); l = np.zeros(C)
    for h in CMP_HORIZONS:
        J = J @ bo + ba[h - 1]
        l = np.maximum(l, np.linalg.norm(J, axis=0) / sd)
    degen = (sd < CMP_SIG_DEG_REL * np.median(sd)) & (l < CMP_L_DEG)
    m_a = m[C:C + 3 * K]; s_a = s[C:C + 3 * K]
    At = (phi[:, C:C + 3 * K] - m_a) / s_a
    Sig = At.T @ At / n + lam_a * np.eye(3 * K)
    nu, V = np.linalg.eigh(Sig)
    keep = nu >= kappa_min * nu.max()
    q = int(keep.sum())
    W_a = (V[:, keep] / np.sqrt(nu[keep])).T
    sec = round_sig(l).copy(); sec[degen] = CMP_L_ABSENT
    return dict(beta_raw=beta_raw, b_raw=b_raw, mu=mu, sd=sd, l=l, degen=degen, m_a=m_a, s_a=s_a,
                W_a=W_a, q=q, sec=sec, cond=float(nu.max() / nu.min()), nu=nu.tolist(),
                nu_min_over_cut=float(nu.min() / (kappa_min * nu.max())), C=C, K=K)


def cmp_streams(O, A, art):
    """Per-step standardised innovations r~ and whitened action features a_w over one episode."""
    C, K = art["C"], art["K"]
    phi, Y = build_design(O, A, C, K)
    r = Y - (phi[:, :-1] @ art["beta_raw"][: C + 3 * K] + art["b_raw"])
    rt = np.clip((r - art["mu"]) / art["sd"], -CMP_ZCAP, CMP_ZCAP)
    a_std = (phi[:, C:C + 3 * K] - art["m_a"]) / art["s_a"]
    aw = a_std @ art["W_a"].T
    return rt, aw, a_std


def cmp_raw_support(rt, aw, art, t):
    """raw_support at emission t (comparator Sec.4: window [t-n+1, t], n = min(W, t_ep), t_ep = t+1)."""
    t_ep = t + 1
    n = min(CMP_W, t_ep)
    sl = slice(t - n + 1, t + 1)
    if t_ep < max(30, 5 * 3 * art["K"]):
        Delta = np.zeros(art["C"])
    else:
        acc = rt[sl].T @ aw[sl]                        # normative: sum over the window in increasing i
        Delta = np.sqrt(n) * np.linalg.norm(acc / n, axis=1)
    raw = round_sig(-np.minimum(Delta, CMP_DCAP)).copy()
    raw[art["degen"]] = CMP_ABSENT
    return raw, Delta


def cmp_chat_unwhitened(rt, a_std, t):
    """Un-whitened c-hat over the window ending at t (for the lag-slot attribution check, F3)."""
    t_ep = t + 1
    n = min(CMP_W, t_ep)
    sl = slice(t - n + 1, t + 1)
    return (rt[sl].T @ a_std[sl]) / n


# ================================================================= arm 1: sequential IBD
def ibd_allocation(instance_seed, episode_seed, K, arm_id=IBD_ARM_ID, T=EPISODE_LEN):
    """Balanced pre-randomised (k, sign) blocks, FIFO, one Generator per (instance, episode, arm).
    Grant at t_next iff used+1 <= floor(0.05*t_next) and t_next - t_last >= PI."""
    rng = np.random.default_rng([IBD_PROBE_NS, int(instance_seed), int(episode_seed), int(arm_id)])
    ALLK = [(k, s) for k in range(K) for s in (1, -1)]
    used, t_last, block = 0, -IBD_PI, []
    acts, alloc = {}, []
    for t in range(T):
        if used + 1 <= math.floor(PROBE_BUDGET * t) and t - t_last >= IBD_PI:
            if not block:
                block = [ALLK[i] for i in rng.permutation(2 * K)]
            k, sgn = block.pop(0)
            used += 1; t_last = t
            a = np.zeros(K); a[k] = float(sgn)
            acts[t] = a; alloc.append((t, k, sgn))
    return acts, alloc


def ranksum_z(gp, gm):
    """Tie-corrected mid-rank rank-sum z, clipped to +-8. None on a degenerate cell (sigma_U == 0)."""
    n1, n2 = len(gp), len(gm)
    if n1 == 0 or n2 == 0:
        return None
    vals = np.concatenate([np.asarray(gp, float), np.asarray(gm, float)])
    rv = np.array([float(f"{v:.11e}") for v in vals])          # 12 significant digits, normative
    N = n1 + n2
    order = np.argsort(rv, kind="mergesort")
    sv = rv[order]
    ranks = np.empty(N)
    tie_term = 0.0
    i = 0
    while i < N:
        j = i
        while j + 1 < N and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        g = j - i + 1
        tie_term += (g ** 3 - g) / 12.0
        i = j + 1
    Rp = ranks[:n1].sum()
    U = Rp - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0
    var = (n1 * n2 / (N * (N - 1))) * ((N ** 3 - N) / 12.0 - tie_term)
    sig = math.sqrt(max(0.0, var))
    if sig == 0.0:
        return None
    return float(np.clip((U - mu) / sig, -IBD_ZCAP, IBD_ZCAP))


def ibd_a_at_epoch(O, alloc, epoch_t, C, K):
    """a_c at the epoch whose update index is epoch_t (t_p* = epoch_t - (HMAX-1))."""
    tps = epoch_t - (IBD_HMAX - 1)
    units = [(tp, k, sgn) for (tp, k, sgn) in alloc if tps - IBD_W < tp <= tps]
    a = np.zeros(C)
    elig = {}
    for k in range(K):
        npv = sum(1 for (_, kk, s) in units if kk == k and s > 0)
        nmv = sum(1 for (_, kk, s) in units if kk == k and s < 0)
        elig[k] = (min(npv, nmv) >= IBD_NMIN)
    zz = np.full((C, K * len(IBD_HSET)), np.nan)
    col = 0
    for k in range(K):
        if not elig[k]:
            col += len(IBD_HSET); continue
        plus = [tp for (tp, kk, s) in units if kk == k and s > 0]
        minus = [tp for (tp, kk, s) in units if kk == k and s < 0]
        for h in IBD_HSET:
            Gp = np.array([O[tp + h] - O[tp] for tp in plus])      # (n1, C)
            Gm = np.array([O[tp + h] - O[tp] for tp in minus])     # (n2, C)
            for c in range(C):
                z = ranksum_z(Gp[:, c], Gm[:, c])
                if z is not None:
                    zz[c, col] = abs(z)
            col += 1
    for c in range(C):
        v = zz[c][~np.isnan(zz[c])]
        a[c] = float(v.max()) if len(v) else 0.0
    return a, dict(n_units=len(units), elig={str(k): bool(v) for k, v in elig.items()})


# ================================================================= per-instance evaluation
def read_steps():
    """Contract Sec.G offset read rule: last emission with transition index t <= event_t + D - 1."""
    cmp_reads = {d: EVENT_T + d - 1 for d in OFFSETS}                       # 1199 / 1499 / 1999
    ibd_reads = {}
    for d in OFFSETS:
        lim = EVENT_T + d - 1
        ibd_reads[d] = max(t for t in range(2, EPISODE_LEN, IBD_PI) if t <= lim)   # 1182/1482/1982
    return cmp_reads, ibd_reads


def eval_instance(base, cfg_label, conf_label, want_extras=False):
    """base: a certified Instance (present) or its G=0 deep copy (absent). Returns a dict of rows."""
    C, K = base.C, base.cfg["K"]
    pre_S = base.S_obs_pre_event()
    post_inst = fresh(base); post_inst.apply_event(EVENT)
    post_S = post_inst.S_obs()
    cmp_reads, ibd_reads = read_steps()

    # ---- comparator fit (per instance, per confounder condition; event-free, non-probed) ----
    fit_streams = []
    for ep in CMP_FIT_EPS:
        r, _ = rollout(base, ep, with_event=False)
        fit_streams.append((r["o"], r["a"]))
    art = fit_predictor(fit_streams, C, K)
    lam_art = {}
    if want_extras:
        for lr in (1e-5, 1e-4, 1e-3):
            lam_art[lr] = fit_predictor(fit_streams, C, K, lam_rel=lr)
        for km in (1e-8, 1e-2):
            lam_art[("kappa", km)] = fit_predictor(fit_streams, C, K, kappa_min=km)

    out = dict(cfg=cfg_label, conf=conf_label, seed=int(base.seed), C=int(C),
               pre_S=pre_S.astype(int).tolist(), post_S=post_S.astype(int).tolist(),
               n_lost=int((pre_S & ~post_S).sum()), pre_size=int(pre_S.sum()),
               q=art["q"], cond=art["cond"], nu_min_over_cut=art["nu_min_over_cut"],
               degen=int(art["degen"].sum()), episodes=[])

    # controls, fixed per instance (statistics that never see the scored episode)
    out["ctrl_channel_constant"] = float(auc_pre_event_support(np.ones(C), pre_S, post_S))
    out["ctrl_static_loading"] = float(auc_pre_event_support(art["sec"], pre_S, post_S))
    out["sec_static_full_auc"] = float(auc_prob_superiority(art["sec"], post_S))

    # ---- scored episodes ----
    for ep in SCORED_EPS:
        row = dict(ep=ep)
        # arm 2: passive, non-probed, event-carrying
        r2, _ = rollout(base, ep, with_event=True)
        rt, aw, a_std = cmp_streams(r2["o"], r2["a"], art)
        for d in OFFSETS:
            raw, Delta = cmp_raw_support(rt, aw, art, cmp_reads[d])
            row[f"cmp_primary_{d}"] = float(auc_pre_event_support(raw, pre_S, post_S))
            row[f"cmp_secondary_{d}"] = float(auc_prob_superiority(art["sec"], post_S))
            if d == 500:
                lost = np.where(pre_S & ~post_S)[0]
                kept = np.where(pre_S & post_S)[0]
                row["cmp_delta_lost"] = [float(Delta[i]) for i in lost]
                row["cmp_delta_kept"] = [float(Delta[i]) for i in kept]
                row["cmp_delta_median_all"] = float(np.median(Delta))
        # arm 1: probed, event-carrying
        acts, alloc = ibd_allocation(base.seed, ep, K)
        r1, _ = rollout(base, ep, actions=acts, with_event=True)
        row["n_probes"] = len(alloc)
        for d in OFFSETS:
            a_c, meta = ibd_a_at_epoch(r1["o"], alloc, ibd_reads[d], C, K)
            row[f"ibd_primary_{d}"] = float(auc_pre_event_support(a_c, pre_S, post_S))
            row[f"ibd_secondary_{d}"] = float(auc_prob_superiority(a_c, post_S))
            if d == 500:
                row["ibd_a_lost"] = [float(a_c[i]) for i in np.where(pre_S & ~post_S)[0]]
                row["ibd_a_kept"] = [float(a_c[i]) for i in np.where(pre_S & post_S)[0]]
                row["ibd_units"] = meta["n_units"]
        if want_extras:
            # lambda_rel / kappa_min sensitivity on the primary at offset 500
            for key, a2 in lam_art.items():
                rt2, aw2, _ = cmp_streams(r2["o"], r2["a"], a2)
                raw2, _ = cmp_raw_support(rt2, aw2, a2, cmp_reads[500])
                row[f"cmp_primary_500_{key}"] = float(auc_pre_event_support(raw2, pre_S, post_S))
                row[f"ctrl_static_{key}"] = float(auc_pre_event_support(a2["sec"], pre_S, post_S))
                row[f"q_{key}"] = a2["q"]
            # lag-slot attribution on the lost channel, offset 500 (comparator Sec.3.3 / F3)
            lost = np.where(pre_S & ~post_S)[0]
            if len(lost):
                ch = cmp_chat_unwhitened(rt, a_std, cmp_reads[500])
                row["chat_lost_unwhitened"] = [float(v) for v in ch[lost[0]]]
            # fault-free null scale of Delta (F1): event-free episode, same ep id
            rff, _ = rollout(base, ep, with_event=False)
            rtf, awf, _ = cmp_streams(rff["o"], rff["a"], art)
            dvals = []
            for t in range(200, EPISODE_LEN, 100):
                _, Dl = cmp_raw_support(rtf, awf, art, t)
                dvals.append(Dl)
            dvals = np.array(dvals)
            row["null_delta_median"] = float(np.median(dvals))
            row["null_delta_max"] = float(dvals.max())
            _, Dff = cmp_raw_support(rtf, awf, art, 1499)
            row["null_full_auc_negDelta"] = float(auc_prob_superiority(-Dff, base.S_obs()))
        out["episodes"].append(row)
    return out


# ================================================================= arm 3 (optional, separate)
def eval_arm3(base):
    """Probed comparator: comparator predictor artefacts bitwise identical to arm 2, run on arm 1's
    exact probe stream. Reported separately; not part of the exit condition."""
    C, K = base.C, base.cfg["K"]
    pre_S = base.S_obs_pre_event()
    post_inst = fresh(base); post_inst.apply_event(EVENT); post_S = post_inst.S_obs()
    cmp_reads, _ = read_steps()
    fit_streams = []
    for ep in CMP_FIT_EPS:
        r, _ = rollout(base, ep, with_event=False)
        fit_streams.append((r["o"], r["a"]))
    art = fit_predictor(fit_streams, C, K)
    rows = []
    for ep in SCORED_EPS:
        acts, alloc = ibd_allocation(base.seed, ep, K, arm_id=IBD_ARM_ID)   # arm 3 replays arm 1's stream
        r3, _ = rollout(base, ep, actions=acts, with_event=True)
        rt, aw, _ = cmp_streams(r3["o"], r3["a"], art)
        row = dict(ep=ep)
        for d in OFFSETS:
            raw, _ = cmp_raw_support(rt, aw, art, cmp_reads[d])
            row[f"arm3_primary_{d}"] = float(auc_pre_event_support(raw, pre_S, post_S))
        rows.append(row)
    return rows


# ================================================================= chunk drivers
def make_cells(chunk):
    if chunk == "baseL_10_0":  return [(dict(N_x=10, tau=0), "L_Nx10_tau0", list(range(10)))]
    if chunk == "baseL_10_2":  return [(dict(N_x=10, tau=2), "L_Nx10_tau2", list(range(10)))]
    if chunk == "baseL_30_0":  return [(dict(N_x=30, tau=0), "L_Nx30_tau0", list(range(10)))]
    if chunk == "baseL_30_2":  return [(dict(N_x=30, tau=2), "L_Nx30_tau2", list(range(10)))]
    if chunk == "N_10_0":      return [(dict(N_x=10, tau=0, family="N"), "N_Nx10_tau0", list(range(5)))]
    if chunk == "N_10_2":      return [(dict(N_x=10, tau=2, family="N"), "N_Nx10_tau2", list(range(5)))]
    if chunk == "perturb":
        cells = []
        for cp in (0.5, 1.0, 2.0):
            for nm in (0.5, 1.0, 2.0):
                cells.append((dict(N_x=10, tau=0, coupling=cp, noise_mult=nm),
                              f"P_cp{cp}_nm{nm}", [0]))
        return cells
    raise SystemExit(f"unknown chunk {chunk}")


def run_chunk(chunk):
    t0 = time.time()
    rows, arm3 = [], []
    extras_done = set()
    for cfg, label, seeds in make_cells(chunk):
        for sd in seeds:
            inst = draw_certified(cfg, sd)
            cert = dict(n_lost=int(inst.certification["n_lost"]),
                        n_resamples=int(inst.n_resamples), inst_seed=int(inst.seed),
                        rho_cl=float(inst.certification.get("rho_cl", float("nan"))),
                        sat=float(inst.certification["sat"]),
                        rho_witness=float(inst.certification["rho_witness"]),
                        max_abs_z=float(inst.certification.get("max_abs_z", float("nan"))),
                        chain_mean_spread=float(inst.certification.get("chain_mean_spread", float("nan"))),
                        zbar_absmax=float(np.abs(inst.zbar).max()))
            absent = fresh(inst); absent.G[:] = 0.0
            want = (label, sd) not in extras_done and sd == 0
            for conf, obj in (("present", inst), ("absent", absent)):
                r = eval_instance(obj, label, conf, want_extras=want)
                r.update(cert)
                rows.append(r)
            extras_done.add((label, sd))
            if sd == 0 and chunk.startswith("baseL"):
                arm3.append(dict(cfg=label, conf="present", seed=int(inst.seed), rows=eval_arm3(inst)))
                arm3.append(dict(cfg=label, conf="absent", seed=int(inst.seed), rows=eval_arm3(absent)))
            print(f"[{chunk}] {label} seed {sd} done  t={time.time()-t0:.0f}s", flush=True)
    (RESULTS / f"{chunk}.json").write_text(json.dumps(dict(chunk=chunk, rows=rows, arm3=arm3,
                                                           seconds=time.time() - t0), indent=1))
    print(f"[{chunk}] wrote {len(rows)} rows in {time.time()-t0:.0f}s")


# ================================================================= aggregation
def boot_ci(vals, n=20000, seed=12345):
    """Percentile bootstrap over INSTANCES (the clustering unit; contract Sec.G)."""
    v = np.asarray([x for x in vals if np.isfinite(x)], float)
    if len(v) == 0:
        return (float("nan"),) * 3
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), size=(n, len(v)))
    means = v[idx].mean(axis=1)
    return float(v.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def load_all():
    rows, arm3 = [], []
    for f in sorted(RESULTS.glob("*.json")):
        d = json.loads(f.read_text())
        rows += d["rows"]; arm3 += d.get("arm3", [])
    return rows, arm3


def inst_mean(row, key):
    v = [e[key] for e in row["episodes"] if np.isfinite(e.get(key, float("nan")))]
    return float(np.mean(v)) if v else float("nan")


def report():
    rows, arm3 = load_all()
    L = []
    P = L.append
    P("=" * 118)
    P("ROUND-6 INDEPENDENT REIMPLEMENTATION -- claude-opus.  Frozen version 38d161e762a3de76.")
    P("ALL NUMBERS BELOW ARE MINE ALONE (one of three implementations).  Python 3.12.0 / numpy "
      + np.__version__)
    P("=" * 118)

    cells = sorted({r["cfg"] for r in rows})
    # ---------------- headline table ----------------
    P("\n[1] PRIMARY pre-event-support AUC (auc_pre_event_support), per cell, per arm, per condition.")
    P("    Per-episode AUC -> instance mean -> cell mean; 95% percentile bootstrap CLUSTERED BY INSTANCE.")
    P(f"\n{'cell':<16}{'arm':<10}{'cond':<9}{'off':>5}"
      f"{'mean':>9}{'lo95':>9}{'hi95':>9}{'#inst':>7}")
    P("-" * 118)
    for cell in cells:
        for arm, pfx in (("seq_ibd", "ibd"), ("comparator", "cmp")):
            for cond in ("present", "absent"):
                for d in OFFSETS:
                    sel = [r for r in rows if r["cfg"] == cell and r["conf"] == cond]
                    vals = [inst_mean(r, f"{pfx}_primary_{d}") for r in sel]
                    m, lo, hi = boot_ci(vals)
                    P(f"{cell:<16}{arm:<10}{cond:<9}{d:>5}{m:>9.3f}{lo:>9.3f}{hi:>9.3f}{len(vals):>7}")
        P("-" * 118)

    P("\n[2] SECONDARY full-channel AUC of secondary_support() vs S_obs_eps(post), offset 500.")
    P(f"{'cell':<16}{'arm':<10}{'cond':<9}{'mean':>9}{'lo95':>9}{'hi95':>9}")
    for cell in cells:
        for arm, pfx in (("seq_ibd", "ibd"), ("comparator", "cmp")):
            for cond in ("present", "absent"):
                sel = [r for r in rows if r["cfg"] == cell and r["conf"] == cond]
                vals = [inst_mean(r, f"{pfx}_secondary_500") for r in sel]
                m, lo, hi = boot_ci(vals)
                P(f"{cell:<16}{arm:<10}{cond:<9}{m:>9.3f}{lo:>9.3f}{hi:>9.3f}")

    P("\n[3] CONFOUNDING BENEFIT = [dAUC(present) - dAUC(absent)], dAUC = IBD - comparator on the")
    P("    primary, paired within instance and cell.  95% percentile bootstrap clustered by instance.")
    P(f"{'cell':<16}{'off':>5}{'dAUC_pres':>11}{'dAUC_abs':>11}{'benefit':>10}{'lo95':>9}{'hi95':>9}"
      f"{'>0.10?':>8}")
    for cell in cells:
        for d in OFFSETS:
            pres = {r["seed"]: r for r in rows if r["cfg"] == cell and r["conf"] == "present"}
            absn = {r["seed"]: r for r in rows if r["cfg"] == cell and r["conf"] == "absent"}
            ben, dp, da = [], [], []
            for s in sorted(set(pres) & set(absn)):
                a = inst_mean(pres[s], f"ibd_primary_{d}") - inst_mean(pres[s], f"cmp_primary_{d}")
                b = inst_mean(absn[s], f"ibd_primary_{d}") - inst_mean(absn[s], f"cmp_primary_{d}")
                dp.append(a); da.append(b); ben.append(a - b)
            m, lo, hi = boot_ci(ben)
            P(f"{cell:<16}{d:>5}{np.nanmean(dp):>11.3f}{np.nanmean(da):>11.3f}"
              f"{m:>10.3f}{lo:>9.3f}{hi:>9.3f}{'YES' if lo > 0.10 else 'no':>8}")

    P("\n[4] D-10.3 COMPETENCE FLOOR (R0-absent): lower 95% bound of the COMPARATOR's primary AUC,")
    P("    confounder ABSENT, must be >= 0.85 in every required family-L cell.  Primary offset 500.")
    P(f"{'cell':<16}{'off':>5}{'mean':>9}{'lo95':>9}{'verdict':>12}")
    for cell in cells:
        for d in OFFSETS:
            sel = [r for r in rows if r["cfg"] == cell and r["conf"] == "absent"]
            vals = [inst_mean(r, f"cmp_primary_{d}") for r in sel]
            m, lo, hi = boot_ci(vals)
            P(f"{cell:<16}{d:>5}{m:>9.3f}{lo:>9.3f}{('PASS' if lo >= 0.85 else 'FAIL'):>12}")

    P("\n[5] CONTROLS on the primary (both are fit-time objects that never see the scored episode).")
    P(f"{'cell':<16}{'cond':<9}{'channel-const':>15}{'static-loading l':>19}{'lo95(static)':>14}")
    for cell in cells:
        for cond in ("present", "absent"):
            sel = [r for r in rows if r["cfg"] == cell and r["conf"] == cond]
            cc = [r["ctrl_channel_constant"] for r in sel]
            st = [r["ctrl_static_loading"] for r in sel]
            m, lo, hi = boot_ci(st)
            P(f"{cell:<16}{cond:<9}{np.mean(cc):>15.6f}{m:>19.3f}{lo:>14.3f}")

    P("\n[6] n_lost and |S_obs_eps(pre)| distribution over every certified draw used.")
    from collections import Counter
    for cell in cells:
        sel = [r for r in rows if r["cfg"] == cell and r["conf"] == "present"]
        P(f"  {cell:<16} n_lost={dict(sorted(Counter(r['n_lost'] for r in sel).items()))}"
          f"  |pre|={dict(sorted(Counter(r['pre_size'] for r in sel).items()))}"
          f"  C={sorted({r['C'] for r in sel})}"
          f"  n_resamples={dict(sorted(Counter(r['n_resamples'] for r in sel).items()))}")

    P("\n[7] Whitener rank / conditioning (comparator Sec.3.2), and degenerate-channel count.")
    for cell in cells:
        sel = [r for r in rows if r["cfg"] == cell]
        P(f"  {cell:<16} q={sorted({r['q'] for r in sel})}  cond(Sigma_a) in "
          f"[{min(r['cond'] for r in sel):.0f}, {max(r['cond'] for r in sel):.0f}]"
          f"  min_eig/cutoff in [{min(r['nu_min_over_cut'] for r in sel):.1f},"
          f" {max(r['nu_min_over_cut'] for r in sel):.1f}]"
          f"  degenerate={sorted({r['degen'] for r in sel})}")

    P("\n[8] Separation diagnostics at offset 500 (present arm): Delta on lost vs kept channels;")
    P("    a_c on lost vs kept channels.")
    for cell in cells:
        sel = [r for r in rows if r["cfg"] == cell and r["conf"] == "present"]
        dl = [v for r in sel for e in r["episodes"] for v in e.get("cmp_delta_lost", [])]
        dk = [v for r in sel for e in r["episodes"] for v in e.get("cmp_delta_kept", [])]
        al = [v for r in sel for e in r["episodes"] for v in e.get("ibd_a_lost", [])]
        ak = [v for r in sel for e in r["episodes"] for v in e.get("ibd_a_kept", [])]
        if dl:
            P(f"  {cell:<16} Delta lost med={np.median(dl):8.2f} kept med={np.median(dk):8.2f} | "
              f"a_c lost med={np.median(al):5.2f} kept med={np.median(ak):5.2f} "
              f"a_c overlap frac(lost>=min kept)={np.mean([x >= min(ak) for x in al]):.2f}")

    P("\n[9] SENSITIVITY (seed 0 of each cell only): lambda_rel and kappa_min on the primary at 500.")
    for cell in cells:
        sel = [r for r in rows if r["cfg"] == cell and r["seed"] % 1000 >= 0]
        for cond in ("present", "absent"):
            for r in [x for x in sel if x["conf"] == cond]:
                e0 = r["episodes"][0]
                ks = [k for k in e0 if k.startswith("cmp_primary_500_")]
                if not ks:
                    continue
                bits = ", ".join(f"{k.replace('cmp_primary_500_','')}="
                                 f"{np.mean([ep[k] for ep in r['episodes']]):.3f}" for k in sorted(ks))
                stat = ", ".join(f"{k.replace('ctrl_static_','')}="
                                 f"{np.mean([ep[k] for ep in r['episodes']]):.3f}"
                                 for k in sorted(k for k in e0 if k.startswith("ctrl_static_")))
                P(f"  {cell:<16}{cond:<9} primary: {bits}")
                P(f"  {'':<16}{'':<9} static : {stat}")
                break

    P("\n[10] Null-scale and lag-slot diagnostics (seed 0, present).")
    for cell in cells:
        for r in [x for x in rows if x["cfg"] == cell and x["conf"] == "present"]:
            e = r["episodes"][0]
            if "null_delta_median" in e:
                nm = np.mean([ep["null_delta_median"] for ep in r["episodes"]])
                nx = np.max([ep["null_delta_max"] for ep in r["episodes"]])
                na = np.mean([ep["null_full_auc_negDelta"] for ep in r["episodes"]])
                ch = e.get("chat_lost_unwhitened")
                P(f"  {cell:<16} null Delta median={nm:.2f} max={nx:.2f} (predicted sqrt(3K)=2.449); "
                  f"fault-free AUC(-Delta vs S_obs)={na:.3f}")
                if ch:
                    lab = ["a_t k0", "a_t k1", "a_t-1 k0", "a_t-1 k1", "a_t-2 k0", "a_t-2 k1"]
                    top = int(np.argmax(np.abs(ch)))
                    P(f"  {'':<16} un-whitened c-hat on lost channel @500: "
                      + ", ".join(f"{l}={v:.2f}" for l, v in zip(lab, ch))
                      + f"   -> largest slot: {lab[top]}")
            break

    P("\n[11] ARM 3 (probed comparator, optional, seed 0 of each family-L base cell), primary @500.")
    for a in arm3:
        v = np.mean([r["arm3_primary_500"] for r in a["rows"]])
        P(f"  {a['cfg']:<16}{a['conf']:<9} arm3 primary@500 = {v:.3f}")

    P("\n[12] Probe accounting (arm 1): probes applied per 2000-step episode.")
    ns = sorted({e["n_probes"] for r in rows for e in r["episodes"]})
    P(f"  n_probes per episode = {ns}  (fraction {ns[0]/2000:.4f});  IBD window units at reads = "
      f"{sorted({e['ibd_units'] for r in rows for e in r['episodes']})}")

    txt = "\n".join(L)
    (HERE / "report.txt").write_text(txt)
    print(txt)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "report":
        report()
    else:
        run_chunk(sys.argv[1])
