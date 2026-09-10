"""Single-model diagnostic for sequential-ibd-spec.md DRAFT 5. NOT a result.

Run from executable-proofs/gate/ so that reference_generator and contract_ref import.
Every number printed here comes from one model, one process, one implementation; it exists
to check that draft 5's index tables, mixture tables and CL-4 statements are arithmetically
reproducible on the frozen generator, not to measure the arm.

    cd executable-proofs/gate && PYTHONHASHSEED=0 python3 ../../superseded-specs/ibd-draft5-diagnostic.py
"""
import sys, os, time, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath("."))
from reference_generator import Instance, draw_certified
from contract_ref import auc_pre_event_support, count_alarms_timed, run_length_from_reset

PB, PI, W, HSET, HMAX, NW, NMIN, ZCAP = 0.05, 20, 500, [1, 2, 3], 3, 25, 3, 8.0
EPISODE_LEN, EVENT_T = 2000, 1000
OFFSETS = [200, 500, 1000]


# ---------------------------------------------------------------- D1 probe clock
def grant_times(T=EPISODE_LEN):
    """Draft 5 §3 grant rule on the generator's 0-indexed clock: t_next is the index of the
    step ABOUT to be taken, t_next = 0..T-1."""
    used, t_last, out = 0, -PI, []
    for t in range(T):
        if used + 1 <= math.floor(PB * t) and t - t_last >= PI:
            used += 1; t_last = t; out.append(t)
    return out


def d1():
    g = grant_times()
    closes = [tp + HMAX - 1 for tp in g]
    print("== D1 probe clock (0-indexed, t = 0..1999) ==")
    print(f"  grants          : n={len(g)} first={g[0]} last={g[-1]} stride={g[1]-g[0]}")
    print(f"  budget fraction : {len(g)}/{EPISODE_LEN} = {len(g)/EPISODE_LEN:.4f}  (cap {PB})")
    print(f"  invariant used(t) <= floor(0.05 t) holds: "
          f"{all(i + 1 <= math.floor(PB * tp) for i, tp in enumerate(g))}")
    print(f"  unit closure    : first={closes[0]} last={closes[-1]} (max legal step {EPISODE_LEN-1})")
    print(f"  units closing in-episode: {sum(1 for c in closes if c <= EPISODE_LEN-1)} of {len(g)}")
    print(f"  epoch grid      : t = {closes[0]}, {closes[1]}, ..., {closes[-1]}  "
          f"(t = {closes[0] % PI} mod {PI}); n_epochs={len(closes)}")
    # occupancy at each epoch: units with anchor in (tp*-W, tp*]
    occ = []
    for i, c in enumerate(closes):
        tps = g[i]
        occ.append(sum(1 for tp in g[:i + 1] if tps - W < tp <= tps))
    first25 = closes[occ.index(NW)]
    print(f"  first epoch holding {NW} units (t_warm) : {first25}   (anchor {g[occ.index(NW)]})")
    print(f"  occupancy is monotone then saturated at {max(occ)}: {occ[:5]} ... {occ[-3:]}")
    # earliest counted alarm from reset with p=3 epochs, r=20 steps
    raises = [0] * occ.index(NW) + [1] * (len(closes) - occ.index(NW))
    ca = count_alarms_timed(raises, closes, 3, 20)
    print(f"  earliest counted alarm from reset (all-raise after warm-up, p=3 epochs, r=20 steps): "
          f"{run_length_from_reset(ca, EPISODE_LEN)}")
    print(f"  refractory r=20 steps vs epoch stride 20 steps -> suppresses exactly one epoch: "
          f"alarms at {ca[:4]} (stride {ca[1]-ca[0]} steps)")
    return g, closes


# ---------------------------------------------------------------- D2 offsets and mixture
def d2(g, closes):
    print("\n== D2 offset table and pre/post window mixture (event_t = 1000) ==")
    print("  offset | epoch read | newest anchor | oldest anchor | post units / 25 | post fraction")
    for D in OFFSETS:
        target = EVENT_T + D
        idx = max(i for i, c in enumerate(closes) if c <= target)
        c, tps = closes[idx], g[idx]
        win = [tp for tp in g if tps - W < tp <= tps]
        npost = sum(1 for tp in win if tp >= EVENT_T)
        print(f"   {D:5d} |    {c:5d}   |     {tps:5d}     |     {min(win):5d}     |"
              f"      {npost:2d} / {len(win):2d}     |    {npost/len(win):.2f}")
    print("  post-event ramp (epoch -> post units): first fully post-event epoch =", end=" ")
    ramp = []
    for i, c in enumerate(closes):
        tps = g[i]
        win = [tp for tp in g if tps - W < tp <= tps]
        if len(win) < NW: continue
        npost = sum(1 for tp in win if tp >= EVENT_T)
        ramp.append((c, npost))
    full = [c for c, n in ramp if n == NW]
    print(f"{full[0]}  (offset {full[0]-EVENT_T} from the event)")
    print("  ramp sample:", [(c, n) for c, n in ramp if EVENT_T <= c <= 1120] , "...")


# ---------------------------------------------------------------- D3 CL-4 on the frozen family
def d3(taus=(0, 2), seeds=range(10), N_x=10):
    print("\n== D3 CL-4 certification on the frozen family (N_x=%d) ==" % N_x)
    print("  tau | seed | n_resamples | |S_pre| | n_lost | lost ch | rank of lost ch in "
          "pre-event e (1 = largest)")
    summary = {}
    for tau in taus:
        for s in seeds:
            inst = draw_certified(dict(N_x=N_x, tau=tau), s)
            pre = inst.S_obs_pre_event()
            e = inst.operational_effect()
            import copy
            post_i = copy.deepcopy(inst); post_i.apply_event(("actuator_loss", 0))
            post = post_i.S_obs()
            lost = np.where(pre & ~post)[0]
            # rank of the lost channel among pre-event support channels by latent effect
            idx = [c for c in np.where(pre)[0]]
            eff = {c: e[inst.assign[c]] for c in idx}
            order = sorted(idx, key=lambda c: -eff[c])
            ranks = [order.index(c) + 1 for c in lost]
            static = np.array([e[inst.assign[c]] if inst.assign[c] >= 0 else 0.0
                               for c in range(inst.C)])
            auc_static = auc_pre_event_support(static, pre, post)
            summary[(tau, s)] = (int(pre.sum()), len(lost), list(lost), ranks, auc_static)
            print(f"   {tau}  |  {s}   |      {inst.n_resamples}      |   {int(pre.sum()):2d}    |"
                  f"   {len(lost)}    | {list(lost)} | {ranks} of {int(pre.sum())} | "
                  f"AUC_pre(static pre-event effect) = {auc_static:.3f}")
    nl = [v[1] for v in summary.values()]
    print(f"  n_lost over {len(nl)} certified draws: min={min(nl)} max={max(nl)} "
          f"mean={np.mean(nl):.2f}; |S_pre| range "
          f"{min(v[0] for v in summary.values())}-{max(v[0] for v in summary.values())}")
    allranks = [r for v in summary.values() for r in v[3]]
    print(f"  rank of the lost channel in the pre-event effect ordering: {sorted(allranks)}")
    st = [v[4] for v in summary.values()]
    print(f"  AUC_pre of a fit-time vector monotone in the pre-event effect: "
          f"mean {np.mean(st):.3f}, range [{min(st):.3f}, {max(st):.3f}] over {len(st)} draws")
    print("  -> a fit-time PER-CHANNEL VECTOR does NOT score 0.5; only a vector constant ACROSS")
    print("     the channels of S_pre does. CL-4's construction makes the loss anti-exchangeable.")
    return summary


# ---------------------------------------------------------------- D4 horizon fixture
def d4():
    print("\n== D4 first-hit horizon on a deterministic impulse (T-IBD-horizon) ==")
    for tau in (0, 2):
        cfg = dict(N_x=10, tau=tau, sigma=dict(b=0.0, d=0.0, w=0.0, x=0.0, o=0.0, a=0.0, u=0.0),
                   burn_in=0)
        inst = Instance(cfg, 5000)
        tp = 20
        base = inst.run(30, ep=1, actions={})
        pr = inst.run(30, ep=1, actions={tp: np.array([1.0, 0.0])})
        d = np.abs(pr["o"] - base["o"])
        hits = [h for h in range(1, 6) if d[tp + h].max() > 1e-12]
        print(f"  tau={tau}: first nonzero increment at h = {hits[0]} (expected tau+1 = {tau+1});"
              f"  |D^h| for h=1..4: {[float(d[tp+h].max()) for h in range(1,5)]}")


# ---------------------------------------------------------------- D5 family N
def d5():
    print("\n== D5 family N draw (D-11.4) ==")
    for s in (0, 5):
        t0 = time.time()
        try:
            inst = draw_certified(dict(N_x=10, tau=0, family="N"), s)
            c = inst.certification
            print(f"  seed {s}: certified in {time.time()-t0:.1f}s, n_resamples={inst.n_resamples}, "
                  f"bounded={c['bounded']} max|z|={c['max_abs_z']:.2f} spread={c['chain_mean_spread']:.4f} "
                  f"n_lost={c['n_lost']} |S_pre|={int(inst.S_obs_pre_event().sum())} "
                  f"zbar[b,d]={np.round(inst.zbar[:6], 3).tolist()}")
        except Exception as ex:
            print(f"  seed {s}: FAILED after {time.time()-t0:.1f}s: {type(ex).__name__}: {ex}")


# ---------------------------------------------------------------- D6 a_c trajectory
def ranksum_z(gp, gm):
    gp, gm = np.asarray(gp, float), np.asarray(gm, float)
    np_, nm_ = len(gp), len(gm)
    if np_ < NMIN or nm_ < NMIN: return None
    allv = np.concatenate([gp, gm]); N = np_ + nm_
    key = np.array([float(f"{v:.11e}") for v in allv])
    order = np.argsort(key, kind="mergesort"); ranks = np.empty(N)
    srt = key[order]; i = 0; ties = []
    while i < N:
        j = i
        while j + 1 < N and srt[j + 1] == srt[i]: j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        ties.append(j - i + 1); i = j + 1
    Rp = ranks[:np_].sum(); U = Rp - np_ * (np_ + 1) / 2.0; mu = np_ * nm_ / 2.0
    var = (np_ * nm_ / (N * (N - 1.0))) * ((N**3 - N) / 12.0 - sum(t**3 - t for t in ties) / 12.0)
    sd = math.sqrt(max(0.0, var))
    if sd == 0.0: return None
    return float(np.clip((U - mu) / sd, -ZCAP, ZCAP))


def d6(seed=5, tau=0, N_x=10, ep=0):
    import copy
    print(f"\n== D6 a_c trajectory around the event (single instance seed {seed}, tau={tau}, ep={ep}) ==")
    base = draw_certified(dict(N_x=N_x, tau=tau), seed)
    pre = base.S_obs_pre_event()
    inst = copy.deepcopy(base)
    K, C = inst.cfg["K"], inst.C
    g = grant_times()
    rng = np.random.default_rng([5477, inst.seed, ep, 1])
    ALLK = [(k, s) for k in range(K) for s in (+1, -1)]
    block, alloc = [], {}
    for tp in g:
        if not block:
            block = [ALLK[i] for i in rng.permutation(len(ALLK))]
        alloc[tp] = block.pop(0)
    actions = {tp: (sgn * np.eye(K)[k]) for tp, (k, sgn) in alloc.items()}
    r = inst.run(EPISODE_LEN, ep=ep, actions=actions, event_t=EVENT_T,
                 event=("actuator_loss", 0))
    post = inst.S_obs()
    lost = np.where(pre & ~post)[0]; kept = np.where(pre & post)[0]
    O = r["o"]
    units = [(tp, alloc[tp][0], alloc[tp][1],
              np.stack([O[tp + h] - O[tp] for h in HSET])) for tp in g]
    rows = []
    for i, tp in enumerate(g):
        tstar, epoch = tp, tp + HMAX - 1
        win = [u for u in units[:i + 1] if tstar - W < u[0] <= tstar]
        if len(win) < NW: continue
        a = np.zeros(C)
        for c in range(C):
            zz = []
            for k in range(K):
                for hi in range(len(HSET)):
                    gp = [u[3][hi][c] for u in win if u[1] == k and u[2] > 0]
                    gm = [u[3][hi][c] for u in win if u[1] == k and u[2] < 0]
                    z = ranksum_z(gp, gm)
                    if z is not None: zz.append(abs(z))
            a[c] = max(zz) if zz else 0.0
        npost = sum(1 for u in win if u[0] >= EVENT_T)
        rows.append((epoch, npost, a.copy()))
    print(f"  |S_pre|={int(pre.sum())} kept={list(kept)} lost={list(lost)}")
    print("  epoch | post/25 | a_c lost | mean a_c kept | mean a_c outside S_pre | AUC_pre")
    for epoch, npost, a in rows:
        if epoch < 940 or epoch % 100 not in (2, 22, 42, 62, 82) or epoch > 1990:
            if epoch not in (942, 1002, 1102, 1182, 1282, 1382, 1482, 1682, 1982): continue
        outside = np.ones(C, bool); outside[pre] = False
        auc = auc_pre_event_support(a, pre, post)
        print(f"  {epoch:5d} |   {npost:2d}    |  {a[lost].mean():6.3f}  |     {a[kept].mean():6.3f}    |"
              f"        {a[outside].mean():6.3f}        |  {auc:.3f}")
    for D in OFFSETS:
        target = EVENT_T + D
        cand = [row for row in rows if row[0] <= target]
        epoch, npost, a = cand[-1]
        print(f"  offset {D}: epoch {epoch}, post {npost}/25, "
              f"AUC_pre = {auc_pre_event_support(a, pre, post):.3f}, "
              f"AUC_pre of a fit-time constant vector = "
              f"{auc_pre_event_support(np.arange(C, dtype=float), pre, post):.3f} "
              f"(arbitrary constant-in-time per-channel vector), "
              f"AUC_pre of a channel-constant = {auc_pre_event_support(np.ones(C), pre, post):.3f}")


if __name__ == "__main__":
    t0 = time.time()
    g, closes = d1()
    d2(g, closes)
    d4()
    d3()
    d6()
    d5()
    print(f"\ntotal {time.time()-t0:.1f}s  |  numpy {np.__version__}  python {sys.version.split()[0]}")
