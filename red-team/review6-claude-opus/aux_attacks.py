#!/usr/bin/env python3
"""Round-6 auxiliary attacks (claude-opus). Mechanism checks behind the sim_frozen.py numbers.
Every number here is mine alone. Run: python3 aux_attacks.py > aux_output.txt"""
import sys, copy, math, json, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "executable-proofs" / "gate"))
sys.path.insert(0, str(HERE))
from reference_generator import draw_certified, Instance, RESERVED_EP     # noqa: E402
from contract_ref import auc_pre_event_support, auc_prob_superiority      # noqa: E402
import sim_frozen as S                                                    # noqa: E402

P = print


def hdr(t):
    P("\n" + "=" * 100); P(t); P("=" * 100)


# ---------------------------------------------------------------- A. why the confounding benefit is 0
hdr("A. MECHANISM: does G reach anything inside S_obs_eps(pre)?  (confounding benefit == 0)")
for cfg, lab in ((dict(N_x=10, tau=0), "L Nx10 tau0"), (dict(N_x=10, tau=2), "L Nx10 tau2"),
                 (dict(N_x=10, tau=0, family="N"), "N Nx10 tau0")):
    inst = draw_certified(cfg, 0)
    ab = copy.deepcopy(inst); ab.G[:] = 0.0
    r_p = copy.deepcopy(inst).run(600, ep=0)
    r_a = copy.deepcopy(ab).run(600, ep=0)
    sl = inst.sl
    same_a = np.array_equal(r_p["a"], r_a["a"])
    same_b = np.array_equal(r_p["z"][:, sl["b"]], r_a["z"][:, sl["b"]])
    same_d = np.array_equal(r_p["z"][:, sl["d"]], r_a["z"][:, sl["d"]])
    same_x = np.array_equal(r_p["z"][:, sl["x"]], r_a["z"][:, sl["x"]])
    pre = inst.S_obs_pre_event()
    conf = inst.confounded_channels()
    P(f"{lab:>14}: actions identical={same_a}  b identical={same_b}  d identical={same_d}  "
      f"x identical={same_x}")
    P(f"{'':>14}  |S_obs(pre)|={pre.sum()}  channels in pre that are confounded = "
      f"{int((pre & conf).sum())}  (G touches only the x block)")
    P(f"{'':>14}  max|o_present - o_absent| on channels IN the pre-event support = "
      f"{np.abs(r_p['o'][:, pre] - r_a['o'][:, pre]).max():.3e}")

# ---------------------------------------------------------------- B. negated static-loading arm
hdr("B. CONTROL: the NEGATED static loading (-l).  A zero-probe, event-blind arm.")
P("   auc_pre_event_support(-s, pre, post) == 1 - auc_pre_event_support(s, pre, post) exactly")
P("   (gt and lt swap, eq is unchanged, gt+lt+eq = n_pos*n_neg).  Verified numerically below,")
P("   then read off the cell means measured in report.txt section [5].")
inst = draw_certified(dict(N_x=10, tau=0), 0)
pre = inst.S_obs_pre_event(); post_i = copy.deepcopy(inst); post_i.apply_event(("actuator_loss", 0))
post = post_i.S_obs()
v = np.random.default_rng(0).normal(size=inst.C)
P(f"   check: auc(v)={auc_pre_event_support(v, pre, post):.4f}  "
  f"auc(-v)={auc_pre_event_support(-v, pre, post):.4f}  sum={auc_pre_event_support(v, pre, post)+auc_pre_event_support(-v, pre, post):.4f}")
rows, _ = S.load_all()
for cell in sorted({r["cfg"] for r in rows}):
    sel = [r for r in rows if r["cfg"] == cell and r["conf"] == "present"]
    st = np.mean([r["ctrl_static_loading"] for r in sel])
    ibd = np.mean([S.inst_mean(r, "ibd_primary_500") for r in sel])
    cmpv = np.mean([S.inst_mean(r, "cmp_primary_500") for r in sel])
    P(f"   {cell:<16} static l = {st:.3f}   NEGATED static (-l) = {1-st:.3f}   "
      f"seq_ibd@500 = {ibd:.3f}   comparator@500 = {cmpv:.3f}"
      f"{'   <-- -l BEATS seq_ibd' if 1-st > ibd else ''}")

# ---------------------------------------------------------------- C. CL-4 construction: event on actuator 1
hdr("C. CL-4 BY CONSTRUCTION: the same event applied to actuator 1 (NOT the protected actuator).")
P("   reference_generator zeroes B[dom, k!=ea] and A_b[dom, j!=dom] with dom = 2*event_actuator % N_b,")
P("   so actuator 0's dominant body component is structurally isolated. Actuator 1 has no such row.")
P(f"   {'cell':<14}{'seed':>5}{'n_lost(a1)':>11}{'cmp@500':>9}{'ibd@500':>9}{'static':>8}")
for cfg, lab in ((dict(N_x=10, tau=0), "L Nx10 tau0"), (dict(N_x=10, tau=2), "L Nx10 tau2")):
    cm, ib, stt, nl = [], [], [], []
    for sd in range(5):
        base = draw_certified(cfg, sd)
        pre = base.S_obs_pre_event()
        pi = copy.deepcopy(base); pi.apply_event(("actuator_loss", 1)); post = pi.S_obs()
        n_lost = int((pre & ~post).sum())
        nl.append(n_lost)
        if n_lost == 0:
            continue
        C, K = base.C, base.cfg["K"]
        fit = []
        for ep in S.CMP_FIT_EPS:
            r, _ = S.rollout(base, ep, with_event=False)
            fit.append((r["o"], r["a"]))
        art = S.fit_predictor(fit, C, K)
        for ep in S.SCORED_EPS:
            cc = copy.deepcopy(base)
            r2 = cc.run(2000, ep=ep, event_t=1000, event=("actuator_loss", 1))
            rt, aw, _ = S.cmp_streams(r2["o"], r2["a"], art)
            raw, _ = S.cmp_raw_support(rt, aw, art, 1499)
            cm.append(auc_pre_event_support(raw, pre, post))
            acts, alloc = S.ibd_allocation(base.seed, ep, K)
            cc2 = copy.deepcopy(base)
            r1 = cc2.run(2000, ep=ep, actions=acts, event_t=1000, event=("actuator_loss", 1))
            a_c, _ = S.ibd_a_at_epoch(r1["o"], alloc, 1482, C, K)
            ib.append(auc_pre_event_support(a_c, pre, post))
        stt.append(auc_pre_event_support(art["sec"], pre, post))
    P(f"   {lab:<14}{'0-4':>5}{str(nl):>11}{np.mean(cm) if cm else float('nan'):>9.3f}"
      f"{np.mean(ib) if ib else float('nan'):>9.3f}{np.mean(stt) if stt else float('nan'):>8.3f}")
P("   (n_lost per seed listed; seeds with n_lost=0 contribute nothing -- CL-4 is NOT certified for actuator 1.)")

# ---------------------------------------------------------------- D. family N: zbar Monte Carlo -> labels
hdr("D. FAMILY N: S_obs depends on a 2000-step single-chain Monte Carlo estimate of z-bar.")
P("   Instance.stationary_mean(T=4000) discards 2000 and averages 2000 steps of an AR process.")
P("   operational_effect is evaluated at that z-bar and the label is e_j > eps = 0.05.")
P(f"   {'seed':>5}{'spread':>9}{'|zbar|max':>11}{'min|e-eps|':>12}{'S_obs stable over 5 re-estimates?':>36}")
for sd in range(5):
    inst = draw_certified(dict(N_x=10, tau=0, family="N"), sd)
    base_S = inst.S_obs().copy()
    e = inst.operational_effect()
    margin = float(np.min(np.abs(e[inst.S_latent()] - inst.cfg["eps"])))
    stable, seen = True, []
    for T in (2000, 4000, 8000, 16000, 32000):
        inst._zbar = None
        inst._zbar = inst.stationary_mean(T=T)
        s2 = inst.S_obs()
        seen.append(int(s2.sum()))
        if not np.array_equal(s2, base_S):
            stable = False
    inst._zbar = None
    P(f"   {sd:>5}{inst.certification['chain_mean_spread']:>9.4f}"
      f"{np.abs(inst.zbar).max():>11.3f}{margin:>12.4f}"
      f"{('YES  |S|=' + str(seen)) if stable else ('NO   |S|=' + str(seen)):>36}")
P("   delta_inv (the T-L9b agreement tolerance) = 0.05; contract eps = 0.05.")

# ---------------------------------------------------------------- E. family L margin
hdr("E. FAMILY L: label margin min|e_j - eps| over reachable latents on the 10 development seeds.")
for cfg, lab in ((dict(N_x=10, tau=0), "tau0"), (dict(N_x=10, tau=2), "tau2")):
    ms = []
    for sd in range(10):
        i = draw_certified(cfg, sd)
        ms.append(i.certification["min_margin"])
    P(f"   {lab}: min={min(ms):.4f} median={np.median(ms):.4f} max={max(ms):.4f}  (eps = 0.05)")

# ---------------------------------------------------------------- F. N_x=10 vs N_x=30 are one experiment
hdr("F. N_x = 10 and N_x = 30 share the body blocks (IBD spec Sec.11(e), R5-27) -- verified.")
for sd in range(10):
    a = draw_certified(dict(N_x=10, tau=0), sd)
    b = draw_certified(dict(N_x=30, tau=0), sd)
    same = (np.array_equal(a.A_b, b.A_b) and np.array_equal(a.B, b.B) and np.array_equal(a.C_d, b.C_d))
    if sd < 3 or not same:
        P(f"   seed {sd}: sub-seed {a.seed} vs {b.seed}; A_b/B/C_d identical = {same}; "
          f"pre-support on the first 10 channels identical = "
          f"{np.array_equal(a.S_obs_pre_event()[:10], b.S_obs_pre_event()[:10])}")
P("   -> the two distractor levels are one matched design, not two independent replicates.")

# ---------------------------------------------------------------- G. tau = 2 empties the downstream block
hdr("G. tau = 2 exhausts the H = 3 horizon: structural_reach_full does ZERO propagation hops.")
P("   structural_reach_full: frontier = rows of B; then `for _ in range(tau+2, H+1)`.")
P("   tau=0 -> range(2,4): 2 hops (b -> b -> d).   tau=2 -> range(4,4): 0 hops (direct drive only).")
for cfg, lab in ((dict(N_x=10, tau=0), "tau0"), (dict(N_x=10, tau=2), "tau2")):
    sizes, dsz = [], []
    for sd in range(10):
        i = draw_certified(cfg, sd)
        pre = i.S_obs_pre_event()
        sizes.append(int(pre.sum()))
        dsz.append(int(pre[i.sl["d"]].sum()))
    P(f"   {lab}: |S_obs(pre)| = {sizes}; downstream d channels inside the support = {dsz}")
P("   -> at tau = 2 the primary contains no downstream channel at all; contract K10's case is untestable there.")

# ---------------------------------------------------------------- H. episode-id registry collisions
hdr("H. EPISODE-ID REGISTRIES: the two specs against each other and against RESERVED_EP.")
ibd = dict(scored=set(range(0, 4)), alarm_ref=set(range(200, 224)), calib=set(range(300, 324)),
           opval=set(range(400, 416)), arl=set(range(500, 900)))
cmp_ = dict(scored=set(range(0, 4)), pred=set(range(900, 920)), alarm2=set(range(920, 940)),
            alarm3=set(range(940, 960)), calib=set(range(2000, 2024)), opval=set(range(2100, 2116)),
            arl=set(range(3000, 3400)))
res = set(RESERVED_EP.values())
P(f"   generator RESERVED_EP = {sorted(res)}")
clash = [(a, b, sorted(x & y)[:6]) for a, x in ibd.items() for b, y in cmp_.items()
         if a != "scored" and b != "scored" and (x & y)]
P(f"   IBD x comparator clashes at the DECLARED sizes: {clash if clash else 'none'}")
P("   BUT sequential-ibd-spec Sec.7: 'If the observed run-length dispersion forces n > 400, the ARL")
P("   split extends upward from ep = 900; it never overlaps any other set.'  Sec.5 contemplates n up to 666.")
for n in (450, 500, 600, 666):
    ext = set(range(500, 900)) | set(range(900, 900 + (n - 400)))
    P(f"     n={n:>3}: ARL ids 500..{899 + (n-400)};  hits comparator predictor-fit 900-919: "
      f"{bool(ext & cmp_['pred'])};  arm-2 alarm ref 920-939: {bool(ext & cmp_['alarm2'])};  "
      f"arm-3 alarm ref 940-959: {bool(ext & cmp_['alarm3'])};  RESERVED_EP 996-999: {bool(ext & res)}")
P("   Any n > 496 collides with the generator's oracle-only reserved ids; any n > 400 collides with the")
P("   comparator's predictor-fit split.  The IBD spec's disjointness claim is false as written.")

# ---------------------------------------------------------------- I. offset read gap arithmetic
hdr("I. OFFSET READ GAP: the two specs disagree on the number.")
cmp_reads, ibd_reads = S.read_steps()
for d in (200, 500, 1000):
    P(f"   offset {d:>4}: comparator reads t={cmp_reads[d]}, seq_ibd reads t={ibd_reads[d]}, "
      f"gap = {cmp_reads[d]-ibd_reads[d]} steps")
P("   comparator-spec v3 Sec.4.5 and contract Sec.G say 17.  sequential-ibd-spec Sec.13/Sec.14(g) say")
P("   'up to 18 steps apart' at offset 1000.  The correct value is 17 at every offset.")

# ---------------------------------------------------------------- J. S_obs_pre_event silent fallback
hdr("J. Instance.S_obs_pre_event() has a SILENT fallback where a hard error belongs.")
i = Instance(dict(N_x=10, tau=0), 0)          # constructed directly, never through draw_certified
P(f"   Instance(...) built directly: has _pre_S = {hasattr(i, '_pre_S')}")
before = i.S_obs_pre_event().astype(int)
i.apply_event(("actuator_loss", 0))
after = i.S_obs_pre_event().astype(int)
P(f"   S_obs_pre_event() BEFORE the event: {before.sum()} channels")
P(f"   S_obs_pre_event() AFTER  the event: {after.sum()} channels   <-- it silently returns the POST support")
P("   auc_pre_event_support(scores, pre, post) then ranks over the post support and can return NaN or a")
P("   quietly wrong number.  The certified path (draw_certified) sets _pre_S; nothing enforces it.")
