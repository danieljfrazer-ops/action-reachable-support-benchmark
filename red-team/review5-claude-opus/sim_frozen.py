"""Round-5 independent reproduction of both Stage-0A arms on the FROZEN generator.

Freeze: 0468104f6431b050 (verified with freeze.py).
Sources used, and ONLY these:
  * sequential-ibd-spec.md (draft 4)          -> arm 1, `seq_ibd`
  * comparator-spec.md (v2)                   -> arm 2, `cusum_linear_delay_aware`
  * stage-0a-contract-v3.7.md, interface-spec-v4.md
  * executable-proofs/gate/reference_generator.py, contract_ref.py
No review*/ code was read or imported before this file was written.

Run:  python3 sim_frozen.py            (writes sim_frozen.output.txt)

--------------------------------------------------------------------------
CHOICES THE SPECS LEFT OPEN  (each is flagged [Cn] and reported in findings.md)
--------------------------------------------------------------------------
[C1]  Predictor-fit scope.  comparator-spec §1 says the fit split is "per
      (environment, regime, confounder, distractor_level, delay) cell" -- a key
      that does NOT contain the instance seed, while contract_ref.CELL_KEY and
      aggregate_primary DO contain `seed`.  Instances inside one such cell are
      independent SCM draws with different A_b, B, C_d, so one shared beta is
      meaningless.  I fit ONE predictor PER INSTANCE-VARIANT (per seed, per
      confounder arm).  This is the only reading that can work.
[C2]  Fit-episode seeds.  Not specified.  I use ep = 900..900+n_fit-1, disjoint
      from the scored ep = 0..3.  Fit episodes are fault-free (no event) and
      non-probed, per §1.
[C3]  n_pred_fit.  Spec value 20 [prov] retained (40,000 transitions).
[C4]  Comparator offset-read convention.  comparator-spec defines NO read rule
      for offsets_rank; the IBD spec defines one ("last epoch <= event_t+D").
      I read the comparator's q after the update for transition
      t = event_t + D - 1  (D=200 -> t=1199, D=500 -> 1499, D=1000 -> 1999).
      Note offset 1000 == episode_len, and transition t=2000 does not exist in
      `Instance.run` (t ranges 0..T-1); the naive read t=2000 is unreachable.
      Post-event window fractions match the IBD arm at every offset (0.40/1/1).
[C5]  IBD epoch reads.  Per spec §5: epochs 1182 / 1482 / 1982 (grid t=2 mod 20).
[C6]  Probe clock.  `Instance.run` iterates t = 0..T-1 (0-indexed).  Under the
      IBD grant rule that puts probes at t in {20,40,...,1980} = 99 probes,
      budget fraction 0.0495, 99 closed units -- NOT the spec's "100 applied,
      fraction exactly 0.050, 99 units" (T-IBD-count assumes t = 1..2000).
      I implement the 0-indexed version, which is what the frozen generator has.
[C7]  Block RNG seed.  Not specified anywhere.  I use
      np.random.default_rng([instance_seed, ep, 0x1BD]).  State-independent, as
      required; results are reproducible from this line.
      `block.pop()` pops the tail of a uniform permutation (order irrelevant).
[C8]  Tie rounding to "12 significant decimal digits": implemented as
      float(f"{v:.11e}").
[C9]  Event application and instance mutation.  `Instance.apply_event` mutates
      B in place and there is NO undo, so an instance reused across episode
      seeds silently starts episode 2 with the actuator already dead.  I
      deepcopy the certified instance before every event-carrying rollout.
[C10] Confounder-absent arm: `inst.G[:] = 0` after `draw_certified`, same
      config seed, same episode seeds, same noise streams (contract F7).  The
      absent variant is NOT re-certified (it would fail rho_min by construction).
[C11] Comparator `n` in the shift term is min(W, t_ep) with t_ep = number of
      update calls completed (1-based), per §3.
[C12] Both arms are scored against `inst_post.S_obs()` -- the ONE label vector,
      computed after the event on the post-event instance, at all three offsets
      (the specs score "S^obs,eps_t" but the oracle exposes no time index and
      the only event is at t=1000, so post-event labels are constant).
[C13] Exactness optimisation: a_c (IBD) is a function of the current window
      only, and q_c (comparator) of the trailing r~ window only, so both are
      evaluated at the required offsets from the full recursion state rather
      than materialising every step/epoch.  Bitwise identical to the full loop.
"""
import sys, os, copy, time, math, json
import numpy as np

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "executable-proofs", "gate")
sys.path.insert(0, os.path.abspath(GATE))
import reference_generator as RG          # frozen instance family (D-10.1)
import contract_ref as CR                 # normative formulas

# ---------------- registry constants (contract v3.7 sec 0) ----------------
EPISODE_LEN, EVENT_T = 2000, 1000
EVENT = ("actuator_loss", 0)
OFFSETS = (200, 500, 1000)
HSET = (1, 2, 3)
PROBE_BUDGET, PI = 0.05, 20
W_STEPS, NMIN, ZCAP, NWARM_U = 500, 3, 8, 25
# comparator constants (comparator-spec sec 12)
LAM_REL, W_CMP, Z_CAP, Q_CAP, Q_ABSENT = 1e-4, 500, 8, 40.0, -41.0
N_WARM, SIG_FLOOR, S_FLOOR, SIG_DEG_REL, L_DEG, TAU_MAX = 30, 1e-6, 1e-8, 1e-2, 1e-3, 2
N_PRED_FIT = int(os.environ.get("N_PRED_FIT", 20))
EP_FIT0 = 900
N_EP = int(os.environ.get("N_EP", 4))


# =========================================================================
# ARM 1 -- sequential IBD  (sequential-ibd-spec.md draft 4)
# =========================================================================
def probe_schedule(K, inst_seed, ep):
    """sec 3: grant at step t iff used+1 <= floor(0.05*t) and t - t_last >= PI.
    Balanced pre-randomised blocks over (k, sign), length 2K, estimator RNG. [C6][C7]"""
    rng = np.random.default_rng([inst_seed, ep, 0x1BD])
    allk = [(k, s) for k in range(K) for s in (+1, -1)]
    used, t_last, block, sched = 0, -PI, [], {}
    for t in range(EPISODE_LEN):                      # 0-indexed, as Instance.run
        if used + 1 > math.floor(PROBE_BUDGET * t) or t - t_last < PI:
            continue
        if not block:
            block = [allk[i] for i in rng.permutation(len(allk))]
        k, sgn = block.pop()
        used += 1; t_last = t
        sched[t] = (k, sgn)
    return sched


def _midrank_and_ties(V):
    """V: (N, C).  Returns mid-ranks (N, C) and per-column sum_g (t_g^3 - t_g).
    Tie groups formed on 12-significant-digit rounding [C8]."""
    N, C = V.shape
    Vr = np.vectorize(lambda v: float(f"{v:.11e}"))(V) if N else V
    ranks = np.empty((N, C)); tiesum = np.zeros(C)
    for c in range(C):
        col = Vr[:, c]; order = np.argsort(col, kind="stable"); s = col[order]
        r = np.empty(N); i = 0
        while i < N:
            j = i
            while j + 1 < N and s[j + 1] == s[i]:
                j += 1
            avg = (i + j) / 2.0 + 1.0                 # 1-based mid-rank
            r[i:j + 1] = avg
            g = j - i + 1
            if g > 1:
                tiesum[c] += g ** 3 - g
            i = j + 1
        ranks[order, c] = r
    return ranks, tiesum


def ibd_a_of_window(units, K, C):
    """sec 4: per (c,k,h) tie-corrected rank-sum z; a_c = max |z| over eligible,
    non-degenerate cells, else 0."""
    a = np.zeros(C); elig = np.zeros((K, len(HSET)), int)
    zbest = np.zeros(C); have = np.zeros(C, bool)
    for k in range(K):
        plus = [u for u in units if u[1] == k and u[2] > 0]
        minus = [u for u in units if u[1] == k and u[2] < 0]
        npl, nmi = len(plus), len(minus)
        if min(npl, nmi) < NMIN:
            continue
        elig[k, :] = 1
        N = npl + nmi
        for hi in range(len(HSET)):
            V = np.vstack([np.array([u[3][hi] for u in plus]),
                           np.array([u[3][hi] for u in minus])])       # (N, C)
            ranks, tiesum = _midrank_and_ties(V)
            Rp = ranks[:npl].sum(axis=0)
            U = Rp - npl * (npl + 1) / 2.0
            muU = npl * nmi / 2.0
            varU = (npl * nmi / (N * (N - 1.0))) * ((N ** 3 - N) / 12.0 - tiesum / 12.0)
            sdU = np.sqrt(np.maximum(0.0, varU))
            ok = sdU > 0
            z = np.zeros(C)
            z[ok] = np.clip((U[ok] - muU) / sdU[ok], -ZCAP, ZCAP)
            zbest = np.where(ok, np.maximum(zbest, np.abs(z)), zbest)
            have |= ok
    a = np.where(have, zbest, 0.0)
    return a, elig


def run_ibd(inst_post, inst_seed, ep, epochs_wanted):
    """Rollout with probes injected (replaced actions) and event at EVENT_T.
    Returns {epoch -> a[C]} and diagnostics."""
    K, C = inst_post.cfg["K"], inst_post.C
    sched = probe_schedule(K, inst_seed, ep)
    acts = {t: (s * np.eye(K)[k]) for t, (k, s) in sched.items()}
    r = inst_post.run(EPISODE_LEN, ep=ep, actions=acts, event_t=EVENT_T, event=EVENT)
    O = r["o"]                                    # O[t] is the PRE-action obs of step t (sec 2)
    units = []                                    # (t_p, k, sgn, D[3][C])
    out = {}
    for tp in sorted(sched):
        if tp + max(HSET) > EPISODE_LEN:          # unit cannot close inside the episode
            continue
        k, sgn = sched[tp]
        D = [O[tp + h] - O[tp] for h in HSET]
        units.append((tp, k, sgn, D))
    for ep_t in epochs_wanted:
        tpstar = ep_t - (max(HSET) - 1)           # newest anchor closing at ep_t
        win = [u for u in units if tpstar - W_STEPS < u[0] <= tpstar]
        a, elig = ibd_a_of_window(win, K, C)
        out[ep_t] = dict(a=a, n_units=len(win), elig=int(elig.sum()),
                         n_post=sum(1 for u in win if u[0] >= EVENT_T))
    return out, dict(n_probes=len(sched), n_units=len(units), sat=r["sat"])


# =========================================================================
# ARM 2 -- passive comparator  (comparator-spec.md v2)
# =========================================================================
def _design(O, A, C, K):
    """phi_t = [o_t (C), a_t, a_{t-1}, a_{t-2}, 1]; Y = o_{t+1}. Lags zero-filled
    at episode start (sec 1, param 6). One episode at a time; never across
    boundaries."""
    T = A.shape[0]
    phi = np.zeros((T, C + 3 * K + 1))
    phi[:, :C] = O[:T]
    phi[:, C:C + K] = A
    phi[1:, C + K:C + 2 * K] = A[:-1]
    phi[2:, C + 2 * K:C + 3 * K] = A[:-2]
    phi[:, -1] = 1.0
    return phi, O[1:T + 1]


def fit_predictor(inst, C, K, n_fit):
    """sec 1: standardised penalised columns, ridge lam = LAM_REL * n, exact
    back-transform, innovations -> mu, sd; sec 2: iterated-prediction loading;
    sec 4: joint relative degeneracy."""
    PH, YY = [], []
    for i in range(n_fit):
        r = inst.run(EPISODE_LEN, ep=EP_FIT0 + i)          # fault-free, non-probed [C2]
        p, y = _design(r["o"], r["a"], C, K)
        PH.append(p); YY.append(y)
    phi = np.vstack(PH); Y = np.vstack(YY); n = len(Y)
    m = phi[:, :-1].mean(0)
    s = np.maximum(phi[:, :-1].std(0, ddof=0), S_FLOOR)
    Xt = np.hstack([(phi[:, :-1] - m) / s, np.ones((n, 1))])
    D = np.diag([1.0] * (C + 3 * K) + [0.0])
    lam = LAM_REL * n
    Bt = np.linalg.solve(Xt.T @ Xt + lam * D, Xt.T @ Y)
    beta_raw = Bt[:-1] / s[:, None]
    b_raw = Bt[-1] - (m / s) @ Bt[:-1]
    assert np.allclose(Xt @ Bt, phi[:, :-1] @ beta_raw + b_raw, atol=1e-8)   # T-CMP-backtransform
    R = Y - Xt @ Bt
    mu = R.mean(0); sd = np.maximum(R.std(0, ddof=1), SIG_FLOOR)
    bo = beta_raw[:C]                                       # (C, C)
    ba = [beta_raw[C + j * K: C + (j + 1) * K] for j in (0, 1, 2)]   # (K, C) each
    J = np.zeros((K, C)); l = np.zeros(C)
    for h in HSET:
        J = J @ bo + ba[h - 1]
        l = np.maximum(l, np.linalg.norm(J, axis=0) / sd)
    degen = (sd < SIG_DEG_REL * np.median(sd)) & (l < L_DEG)
    return dict(beta=beta_raw, b=b_raw, mu=mu, sd=sd, l=l, degen=degen, n=n, lam=lam)


def run_cmp(inst_post, fit, ep, offsets):
    """sec 3: q_c(t) = clip(l_c - |sqrt(n) mean_win(r~)|, +-Q_CAP); degen -> Q_ABSENT."""
    C, K = inst_post.C, inst_post.cfg["K"]
    r = inst_post.run(EPISODE_LEN, ep=ep, event_t=EVENT_T, event=EVENT)
    phi, Y = _design(r["o"], r["a"], C, K)
    res = Y - (phi[:, :-1] @ fit["beta"] + fit["b"])
    rt = np.clip((res - fit["mu"]) / fit["sd"], -Z_CAP, Z_CAP)     # (T, C)
    cs = np.vstack([np.zeros((1, C)), np.cumsum(rt, axis=0)])      # prefix sums
    out = {}
    for d in offsets:
        t = EVENT_T + d - 1                    # transition index [C4]
        t_ep = t + 1                           # update calls completed [C11]
        nn = min(W_CMP, t_ep)
        shift = 0.0 if t_ep < N_WARM else np.abs(np.sqrt(nn) * (cs[t_ep] - cs[t_ep - nn]) / nn)
        q = np.clip(fit["l"] - shift, -Q_CAP, Q_CAP)
        q = np.where(fit["degen"], Q_ABSENT, q)
        out[d] = q
    return out, dict(sat=r["sat"])


# =========================================================================
# harness
# =========================================================================
def cluster_ci(values_by_instance, B=5000, seed=12345):
    """Nonparametric cluster bootstrap over instances; percentile 95% interval
    of the grand mean (equal weight per instance)."""
    keys = sorted(values_by_instance)
    per = np.array([np.mean(values_by_instance[k]) for k in keys], float)
    per = per[~np.isnan(per)]
    if len(per) == 0:
        return float("nan"), float("nan"), float("nan"), 0
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(per), size=(B, len(per)))
    bs = per[idx].mean(axis=1)
    return float(per.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), len(per)


def evaluate_variant(inst_clean, inst_seed, C, K, n_fit, n_ep):
    """Returns per-episode AUCs for both arms at each offset, plus label info."""
    fit = fit_predictor(inst_clean, C, K, n_fit)
    post = copy.deepcopy(inst_clean); post.apply_event(EVENT)      # [C9]
    labels = post.S_obs()
    pre_labels = inst_clean.S_obs()
    epochs = {200: 1182, 500: 1482, 1000: 1982}                    # [C5]
    rows = []
    for ep in range(n_ep):
        i1 = copy.deepcopy(inst_clean)
        ibd_out, ibd_diag = run_ibd(i1, inst_seed, ep, sorted(epochs.values()))
        i2 = copy.deepcopy(inst_clean)
        cmp_out, _ = run_cmp(i2, fit, ep, OFFSETS)
        row = dict(ep=ep, n_probes=ibd_diag["n_probes"], n_units=ibd_diag["n_units"])
        for d in OFFSETS:
            row[f"ibd_{d}"] = CR.auc_prob_superiority(ibd_out[epochs[d]]["a"], labels)
            row[f"cmp_{d}"] = CR.auc_prob_superiority(cmp_out[d], labels)
            row[f"units_{d}"] = ibd_out[epochs[d]]["n_units"]
            row[f"post_{d}"] = ibd_out[epochs[d]]["n_post"]
        rows.append(row)
    return rows, dict(n_pos=int(labels.sum()), n_pos_pre=int(pre_labels.sum()),
                      C=C, s_change=bool((labels != pre_labels).any()),
                      l=fit["l"], degen=int(fit["degen"].sum()),
                      auc_l_post=CR.auc_prob_superiority(fit["l"], labels),
                      auc_l_pre=CR.auc_prob_superiority(fit["l"], pre_labels),
                      qmax=float(np.max(fit["l"])))


def main():
    t_start = time.time()
    print(f"# review5-claude-opus  sim_frozen.py   freeze 0468104f6431b050")
    print(f"# numpy {np.__version__}  python {sys.version.split()[0]}")
    print(f"# n_pred_fit={N_PRED_FIT}  episode seeds={N_EP}  offsets={OFFSETS}")
    print()

    results = {}      # (cellname, conf) -> {inst_seed: [rows]}
    meta = {}
    configs = []
    for Nx in (10, 30):
        for tau in (0, 2):
            configs.append((f"Nx{Nx}_tau{tau}", dict(N_x=Nx, tau=tau), range(10)))
    for coup in (0.5, 1.0, 2.0):
        for nm in (0.5, 1.0, 2.0):
            if coup == 1.0 and nm == 1.0:
                continue
            configs.append((f"pert_c{coup}_n{nm}", dict(coupling=coup, noise_mult=nm), [0]))
    configs.append(("pert_c1.0_n1.0", dict(coupling=1.0, noise_mult=1.0), [0]))

    for cellname, cfg, seeds in configs:
        for conf in ("present", "absent"):
            results[(cellname, conf)] = {}
            meta[(cellname, conf)] = {}
        for s in seeds:
            base = RG.draw_certified(cfg, s)
            C, K = base.C, base.cfg["K"]
            for conf in ("present", "absent"):
                inst = copy.deepcopy(base)
                if conf == "absent":
                    inst.G[:] = 0.0                                  # [C10]
                rows, info = evaluate_variant(inst, s, C, K, N_PRED_FIT, N_EP)
                results[(cellname, conf)][s] = rows
                meta[(cellname, conf)][s] = info
            print(f"  done {cellname} seed={s} conf both  "
                  f"n_pos={meta[(cellname,'present')][s]['n_pos']}/"
                  f"{meta[(cellname,'present')][s]['C']} "
                  f"s_change={meta[(cellname,'present')][s]['s_change']}  "
                  f"[{time.time()-t_start:.0f}s]", flush=True)

    # ---------------- per-cell tables ----------------
    print("\n" + "=" * 118)
    print("PER-CELL RAW-STATISTIC AUC  (mean over instances of the per-instance mean over episode seeds)")
    print("cluster-bootstrap 95% intervals over instances, B=5000")
    print("=" * 118)
    hdr = f"{'cell':<18}{'conf':<9}{'off':>5} {'AUC_ibd [95% CI]':<30}{'AUC_cmp [95% CI]':<30}{'dAUC [95% CI]':<28}"
    summary = {}
    for cellname, cfg, seeds in configs:
        for conf in ("present", "absent"):
            print()
            print(hdr)
            for d in OFFSETS:
                by_i = {s: [r[f"ibd_{d}"] for r in results[(cellname, conf)][s]] for s in seeds}
                bc = {s: [r[f"cmp_{d}"] for r in results[(cellname, conf)][s]] for s in seeds}
                bd = {s: [r[f"ibd_{d}"] - r[f"cmp_{d}"] for r in results[(cellname, conf)][s]] for s in seeds}
                mi, li, ui, ni = cluster_ci(by_i)
                mc, lc, uc, _ = cluster_ci(bc)
                md, ld, ud, _ = cluster_ci(bd)
                summary[(cellname, conf, d)] = dict(ibd=(mi, li, ui), cmp=(mc, lc, uc), d=(md, ld, ud), n=ni)
                print(f"{cellname:<18}{conf:<9}{d:>5} "
                      f"{mi:6.3f} [{li:6.3f},{ui:6.3f}]      "
                      f"{mc:6.3f} [{lc:6.3f},{uc:6.3f}]      "
                      f"{md:+6.3f} [{ld:+6.3f},{ud:+6.3f}]")

    # ---------------- confounding benefit ----------------
    print("\n" + "=" * 118)
    print("CONFOUNDING BENEFIT  =  dAUC(present) - dAUC(absent),  paired within instance and episode seed")
    print("cluster bootstrap over instances; decision rule D-9.3: superiority iff lower bound > delta_AUC = 0.10")
    print("=" * 118)
    print(f"{'cell':<18}{'off':>5}  {'benefit':>8}  {'95% CI':>20}   {'verdict vs delta=0.10':<28}")
    for cellname, cfg, seeds in configs:
        for d in OFFSETS:
            bb = {}
            for s in seeds:
                rp = results[(cellname, "present")][s]; ra = results[(cellname, "absent")][s]
                bb[s] = [(rp[i][f"ibd_{d}"] - rp[i][f"cmp_{d}"]) - (ra[i][f"ibd_{d}"] - ra[i][f"cmp_{d}"])
                         for i in range(len(rp))]
            m, lo, hi, n = cluster_ci(bb)
            if n < 2:
                v = "n=1 point est., NO interval"
            elif lo > 0.10:
                v = "SUPERIORITY"
            elif hi < 0.10:
                v = "FUTILITY"
            else:
                v = "INCONCLUSIVE"
            star = "  <-- primary" if d == 500 else ""
            ci = f"[{lo:+7.3f},{hi:+7.3f}]" if n >= 2 else "        --        "
            print(f"{cellname:<18}{d:>5}  {m:+8.3f}  {ci:>20}   {v:<28}{star}")

    # ---------------- D-10.3 competence floor ----------------
    print("\n" + "=" * 118)
    print("D-10.3 COMPARATOR COMPETENCE FLOOR: lower 95% bound of comparator AUC, confounder ABSENT, >= 0.85")
    print("=" * 118)
    print(f"{'cell':<18}{'off':>5}  {'AUC_cmp_absent':>15}  {'lower bound':>12}  {'floor':<8}{'n_inst':>7}")
    fails = tot = 0
    conf_cells = [c for c in configs if c[0].startswith("Nx")]
    for cellname, cfg, seeds in configs:
        for d in OFFSETS:
            m, lo, hi = summary[(cellname, "absent", d)]["cmp"]
            n = summary[(cellname, "absent", d)]["n"]
            ok = lo >= 0.85
            if cellname.startswith("Nx"):
                tot += 1; fails += (0 if ok else 1)
            print(f"{cellname:<18}{d:>5}  {m:15.3f}  {lo:12.3f}  {'PASS' if ok else 'FAIL':<8}{n:>7}")
    print(f"\nD-10.3 floor over the FOUR confirmatory cells x 3 offsets: {fails} FAIL out of {tot}.")
    prim = [(c[0], summary[(c[0], 'absent', 500)]['cmp']) for c in conf_cells]
    print("At the PRIMARY offset 500: " + "; ".join(f"{k} lb={v[1]:.3f}" for k, v in prim))

    # ---------------- loading-only diagnostic (comparator-spec sec 2 claims AUC 1.00) ----------------
    print("\n" + "=" * 118)
    print("LOADING-ONLY RANKING (comparator-spec sec 2 claims l alone gives AUC 1.00 without confounding)")
    print("=" * 118)
    print(f"{'cell':<18}{'conf':<9}{'AUC(l) vs post-event S_obs':>28}{'AUC(l) vs pre-event S_obs':>28}")
    for cellname, cfg, seeds in configs:
        if not cellname.startswith("Nx"):
            continue
        for conf in ("present", "absent"):
            ap = [meta[(cellname, conf)][s]["auc_l_post"] for s in seeds]
            aq = [meta[(cellname, conf)][s]["auc_l_pre"] for s in seeds]
            print(f"{cellname:<18}{conf:<9}{np.nanmean(ap):>28.3f}{np.nanmean(aq):>28.3f}")

    # ---------------- label / instance diagnostics ----------------
    print("\n" + "=" * 118)
    print("INSTANCE DIAGNOSTICS  (contract sec D CL-4 requires the event to CHANGE S^obs,eps in confirmatory cells)")
    print("=" * 118)
    for cellname, cfg, seeds in configs:
        ch = [s for s in seeds if meta[(cellname, "present")][s]["s_change"]]
        print(f"{cellname:<18} instances whose S^obs,eps changes under actuator_loss(0): "
              f"{len(ch)}/{len(list(seeds))}  seeds={ch}")

    print(f"\ntotal wall clock: {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main()
