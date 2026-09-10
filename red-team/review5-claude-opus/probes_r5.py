"""Targeted numerical probes behind individual round-5 findings.
Run: PYTHONHASHSEED=0 python3 probes_r5.py   (writes probes_r5.output.txt via tee)
"""
import sys, os, copy, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("N_PRED_FIT", "10")
import sim_frozen as S
import reference_generator as RG
import contract_ref as CR

SEEDS = range(5)


def hr(t):
    print("\n" + "=" * 100); print(t); print("=" * 100)


# ---------------------------------------------------------------- R5: lambda_rel sensitivity
hr("P1  lambda_rel is [prov] and moves the PRIMARY: AUC of the loading l vs S^obs,eps")
print(f"{'cell':<14}{'conf':<9}" + "".join(f"{f'lam_rel={x:g}':>16}" for x in (1e-8, 1e-6, 1e-4, 1e-2, 1e0)))
for tau in (0, 2):
    for conf in ("present", "absent"):
        row = []
        for lr in (1e-8, 1e-6, 1e-4, 1e-2, 1e0):
            S.LAM_REL = lr
            vals = []
            for s in SEEDS:
                inst = RG.draw_certified({"tau": tau}, s)
                if conf == "absent":
                    inst.G[:] = 0.0
                f = S.fit_predictor(inst, inst.C, inst.cfg["K"], 10)
                post = copy.deepcopy(inst); post.apply_event(S.EVENT)
                vals.append(CR.auc_prob_superiority(f["l"], post.S_obs()))
            row.append(np.nanmean(vals))
        print(f"{'tau='+str(tau):<14}{conf:<9}" + "".join(f"{v:>16.3f}" for v in row))
S.LAM_REL = 1e-4

# ---------------------------------------------------------------- R5: q_cap reachability
hr("P2  q_cap = 40 [prov]: is the clip reachable?  (range of the shift term at the scored offsets)")
print(f"{'cell':<10}{'conf':<9}{'off':>6}{'max shift':>12}{'min q':>10}{'frac q at -q_cap':>20}{'frac q ties':>13}")
for tau in (0, 2):
    for conf in ("present", "absent"):
        inst = RG.draw_certified({"tau": tau}, 0)
        if conf == "absent":
            inst.G[:] = 0.0
        f = S.fit_predictor(inst, inst.C, inst.cfg["K"], 10)
        post = copy.deepcopy(inst)
        r = post.run(S.EPISODE_LEN, ep=0, event_t=S.EVENT_T, event=S.EVENT)
        phi, Y = S._design(r["o"], r["a"], inst.C, inst.cfg["K"])
        res = Y - (phi[:, :-1] @ f["beta"] + f["b"])
        rt = np.clip((res - f["mu"]) / f["sd"], -S.Z_CAP, S.Z_CAP)
        cs = np.vstack([np.zeros((1, inst.C)), np.cumsum(rt, axis=0)])
        for d in S.OFFSETS:
            t_ep = S.EVENT_T + d
            nn = min(S.W_CMP, t_ep)
            shift = np.abs(np.sqrt(nn) * (cs[t_ep] - cs[t_ep - nn]) / nn)
            q = np.clip(f["l"] - shift, -S.Q_CAP, S.Q_CAP)
            fr = float(np.mean(np.isclose(q, -S.Q_CAP)))
            _, cnt = np.unique(np.round(q, 12), return_counts=True)
            ties = float((cnt[cnt > 1].sum()) / len(q))
            print(f"{'tau='+str(tau):<10}{conf:<9}{d:>6}{shift.max():>12.2f}{q.min():>10.2f}{fr:>20.3f}{ties:>13.3f}")

# ---------------------------------------------------------------- R5: degeneracy rule reachability
hr("P3  degeneracy rule (sigma_c < 1e-2 * median sigma  AND  l_c < 1e-3): can it EVER fire?")
print(f"{'cfg':<28}{'min sigma_c':>14}{'1e-2*median':>14}{'min l_c':>12}{'fires?':>9}")
for cfg, nm in [({}, "default"), ({"noise_mult": 0.5}, "noise_mult=0.5"),
                ({"noise_mult": 2.0}, "noise_mult=2.0"), ({"N_x": 30}, "N_x=30"),
                ({"tau": 2}, "tau=2")]:
    inst = RG.draw_certified(cfg, 0)
    f = S.fit_predictor(inst, inst.C, inst.cfg["K"], 10)
    thr = 1e-2 * np.median(f["sd"])
    print(f"{nm:<28}{f['sd'].min():>14.5f}{thr:>14.5f}{f['l'].min():>12.5f}{str(bool(f['degen'].any())):>9}")
print("\nAlso: a DROPPED-OUT sensor (avail=0) after the event -- is it reclassified? (fit-time rule, so no)")
inst = RG.draw_certified({}, 0)
f = S.fit_predictor(inst, inst.C, inst.cfg["K"], 10)
post = copy.deepcopy(inst); post.apply_event(("sensor_dropout", 0))
r = post.run(600, ep=0)
print("  sd of channel 0's raw obs after dropout:", round(float(r["o"][:, 0].std()), 5),
      " (pad channel sd:", round(float(r["o"][:, -1].std()), 5), ")")

# ---------------------------------------------------------------- R5: balanced-block guarantees
hr("P4  balanced blocks: group sizes per (k,sign) over every window, and the FIRST-500-STEPS claim")
K = 2
bad_full = bad_any = 0
mins = []
for ep in range(200):
    sch = S.probe_schedule(K, 0, ep)
    anchors = sorted(sch)
    units = [(t, sch[t][0], sch[t][1]) for t in anchors if t + 3 <= S.EPISODE_LEN]
    for i, (tp, _, _) in enumerate(units):
        win = [u for u in units if tp - S.W_STEPS < u[0] <= tp]
        for k in range(K):
            npl = sum(1 for u in win if u[1] == k and u[2] > 0)
            nmi = sum(1 for u in win if u[1] == k and u[2] < 0)
            if len(win) == 25:
                mins.append(min(npl, nmi))
                if min(npl, nmi) < S.NMIN:
                    bad_full += 1
            elif min(npl, nmi) < S.NMIN:
                bad_any += 1
print(f"  full (25-unit) windows: min(n+,n-) range = [{min(mins)}, {max(mins)}]; violations of n_min_sign=3: {bad_full}")
print(f"  PARTIAL windows (< 25 units, i.e. every episode's first 24 epochs): violations = {bad_any}")
print("  -> T-IBD-blocks says the guard never binds 'in EVERY window'; it binds in every episode prefix.")

# ---------------------------------------------------------------- R5: probe count / budget
hr("P5  probe count and budget fraction on the frozen generator's 0-indexed 2000-step run")
sch = S.probe_schedule(2, 0, 0)
anchors = sorted(sch)
closing = [t for t in anchors if t + 3 <= S.EPISODE_LEN]
print(f"  granted probe steps: {len(anchors)}  first={anchors[0]} last={anchors[-1]}")
print(f"  budget fraction = {len(anchors)}/2000 = {len(anchors)/2000:.4f}   (spec sec 3 claims 100 and 'exactly 0.050')")
print(f"  units that close inside the episode: {len(closing)}   (spec claims 99)")

# ---------------------------------------------------------------- R5: cross-process determinism
hr("P6  contract E4 determinism: the noise key uses Python's salted str hash")
print("  reference_generator._noise -> np.random.default_rng([seed, ep, hash(var)&0xffff, t])")
for v in ("b", "d", "w", "x", "o", "a", "u"):
    print(f"    hash({v!r}) & 0xffff = {hash(v) & 0xffff}")
print("  These change every process unless PYTHONHASHSEED is fixed; run_gate.py pins numpy and")
print("  python but NOT PYTHONHASHSEED, and test_gen_determinism_bitwise compares two instances")
print("  INSIDE one process, so it cannot see this.")

# ---------------------------------------------------------------- R5: D-2a arithmetic
hr("P7  D-2a arithmetic: is the [900,1100] band attainable inside the 2e6-step cap?")
print("  Band half-width 100 on a mean of 1000 => need 1.96*sd/sqrt(n) <= 100 => n >= (1.96*sd/100)^2")
for sd in (700, 1000, 1400, 1800, 2200):
    n = math.ceil((1.96 * sd / 100) ** 2)
    print(f"    run-length sd={sd:>5}: n>={n:>5} run lengths; "
          f"IBD cost n*(502 warm-up + 1000) = {n*1502/1e6:>6.3f}M steps"
          f"{'  EXCEEDS 2e6 CAP' if n*1502 > 2e6 else ''};  "
          f"comparator cost n*1000 = {n*1000/1e6:.3f}M{'  EXCEEDS CAP' if n*1000 > 2e6 else ''}")
print("  => the same D-2a cap buys the two arms different dispersion tolerance (sd<=1861 vs <=2282),")
print("     and n=400 (the rule's floor) only meets the band if sd <= 1020.")
