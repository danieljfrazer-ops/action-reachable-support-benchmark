"""Round-2 quantitative attacks on contract v3.1 constants and roadmap v4/v4.1 statistics.
Each block prints the evidence cited in findings.md. Pure numpy; no imports from the gate.
Run: /Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3 attacks.py
"""
import numpy as np
from math import sqrt, log, exp

L = lambda s="": print(s)

# =====================================================================================
# A1. Contract E2d: "max pairwise |corr| <= delta_inv" with delta_inv = 0.05, under
#     randomised do(a). The MAX is taken over K * N_x pairs with NO multiplicity control.
#     confirmation-design.csv sweeps distractor_level in {10, 30, 100}.
#     Question: does a PERFECTLY severed instance pass T-E2d?
# =====================================================================================
L("=" * 90)
L("A1. T-E2d delta_inv = 0.05 on max |corr| over K x N_x pairs, no multiplicity control")
L("    Data are INDEPENDENT by construction (perfectly severed). Failure here = false rejection.")
L("=" * 90)
g = np.random.default_rng(11)
K = 3
for T in (4000, 20000, 100000):
    for Nx in (10, 30, 100):
        fails = 0
        reps = 200
        for _ in range(reps):
            # contract probe set A = {+-e_k, magnitude 1.0}: exactly one coordinate nonzero per step
            k_sel = g.integers(0, K, size=T); sgn = g.choice([-1.0, 1.0], size=T)
            a = np.zeros((T, K)); a[np.arange(T), k_sel] = sgn
            x = g.normal(size=(T, Nx))          # independent of a: confounding truly severed
            m = max(abs(np.corrcoef(a[:, kk], x[:, j])[0, 1]) for kk in range(K) for j in range(Nx))
            fails += (m > 0.05)
        L(f"    T={T:6d}  N_x={Nx:3d}  K={K}:  false-failure rate of T-E2d = {fails/reps:5.1%}"
          f"   (E[max|corr|] ~ sqrt(2 ln({K*Nx})/T) = {sqrt(2*log(K*Nx)/T):.3f})")
L("    -> at distractor_level=100 the severed-confounding test rejects CORRECT instances unless")
L("       T is very large; delta_inv is a fixed constant applied to a max over a growing pair set.")

# =====================================================================================
# A2. Contract 0: ARL_0 = 1000 steps, "estimated on the calibration split over >= 20,000
#     stationary steps, tolerance +-10 percent". How precise is that estimate?
# =====================================================================================
L()
L("=" * 90)
L("A2. ARL_0 = 1000 +- 10% from >= 20,000 stationary steps: attainable precision")
L("=" * 90)
g = np.random.default_rng(3)
for n_steps in (20000, 100000, 400000, 1000000):
    ests = []
    for _ in range(2000):
        # idealised: alarms are a Poisson process with rate 1/1000 (best case for the estimator)
        n_alarms = g.poisson(n_steps / 1000.0)
        ests.append(n_steps / max(n_alarms, 1))
    ests = np.array(ests)
    lo, hi = np.percentile(ests, [2.5, 97.5])
    within = np.mean((ests >= 900) & (ests <= 1100))
    L(f"    {n_steps:8d} steps: expected alarms={n_steps/1000:6.1f}  95% range of ARL_0-hat "
      f"[{lo:7.1f}, {hi:7.1f}]  P(estimate within +-10%) = {within:5.1%}")
L("    -> 20,000 steps gives ~20 alarms; relative SE ~ 1/sqrt(20) = 22%. A +-10% tolerance is")
L("       NOT verifiable at that sample size. ~385 alarms (~385,000 steps) are needed for +-10%")
L(f"       at 95% confidence: n_alarms = (1.96/0.10)^2 = {(1.96/0.10)**2:.0f}.")
L("    -> per estimator, per cell, per regime: the calibration cost is ~19x what the contract states.")

# =====================================================================================
# A3. Contract B stability: only the b-block closed loop is bounded
#     rho(A_b + B W_o diag(gain*avail) Assign_b) <= rho_cl = 0.98.
#     But the policy also reads channels assigned to d, and d is a CHILD of b, so
#     b -> d -> o -> a -> b is a genuine feedback loop that the constraint never sees.
# =====================================================================================
L()
L("=" * 90)
L("A3. rho_cl bounds only the b-block loop; the b->d->o->a->b loop is unconstrained")
L("=" * 90)
A_b = np.array([[0.30, 0.0], [0.0, 0.30]])
A_d = np.array([[0.30]])
C_d = np.array([[2.0, 0.0]])                 # d is driven strongly by b_0
B = np.array([[1.0], [0.0]])                 # one actuator into b_0
# observation: channel 0 <- b_0, channel 1 <- d_0 ; unit gain, available
Assign_b = np.array([[1.0, 0.0], [0.0, 0.0]])           # C x N_b
Assign_d = np.array([[0.0], [1.0]])                     # C x N_d
W_o = np.array([[0.0, 2.0]])                            # K x C : policy reads ONLY the d channel
contract_M = A_b + B @ W_o @ Assign_b                   # exactly the contract's expression
rho_contract = max(abs(np.linalg.eigvals(contract_M)))
# full closed loop on z = [b; d]
F = np.block([[A_b + B @ W_o @ Assign_b, B @ W_o @ Assign_d],
              [C_d,                      A_d]])
rho_full = max(abs(np.linalg.eigvals(F)))
L(f"    contract quantity rho(A_b + B W_o diag(gain*avail) Assign_b) = {rho_contract:.4f}   (<= 0.98 PASSES)")
L(f"    true closed-loop rho over z = [b; d]                        = {rho_full:.4f}   (> 1 => DIVERGES)")
z = np.array([0.01, 0.0, 0.0])
traj = [np.abs(z).max()]
for _ in range(60):
    z = F @ z; traj.append(np.abs(z).max())
L(f"    UNCLIPPED simulation |z|_inf at t=0,20,40,60: {traj[0]:.3g}, {traj[20]:.3g}, {traj[40]:.3g}, {traj[60]:.3g}")
L("    -> the LINEARISED closed loop of an instance passing every stability clause is unstable.")
L()
L("    Now with the contract's action clip a_max = 2.0 in place (honest correction: the clip DOES")
L("    keep the latents bounded, so the failure mode is PERMANENT SATURATION, not divergence):")
gg = np.random.default_rng(5)
a_max = 2.0
b = np.array([0.01, 0.0]); d = np.array([0.0]); u = 0.0
sat, corr_a, corr_x = 0, [], []
Tsim = 20000
for t in range(Tsim):
    u = 0.8 * u + gg.normal(0, 1.0)                     # rho_u = 0.8
    o = np.array([b[0], d[0]])
    a_raw = (W_o @ o)[0] + 0.5 * u + gg.normal(0, 0.1)  # a = clip(W_o o + W_u u + eps^a)
    a = float(np.clip(a_raw, -a_max, a_max))
    sat += abs(a_raw) > a_max
    x_t = 0.8 * u + gg.normal(0, 0.3)                   # x is a child of u: the confounder
    corr_a.append(a); corr_x.append(x_t)
    b = A_b @ b + B[:, 0] * a
    d = A_d @ d + C_d @ b
L(f"    action saturation fraction over {Tsim} steps = {sat/Tsim:.1%}   (contract B: 'saturation fraction logged',")
L("      but NO bound on it anywhere in the contract)")
L(f"    |corr(a, x)| in the saturated closed loop = {abs(np.corrcoef(corr_a, corr_x)[0,1]):.3f}"
  f"   vs contract rho_min = 0.40 required by T-E2c")
L("    -> the instance passes rho_cl <= 0.98 but is unusable: the policy is pinned at the clip,")
L("       the confounding witness collapses, and probes on a saturated actuator move nothing.")
L("       rho_cl as written is NOT a closed-loop bound: it omits every loop that leaves the")
L("       b-block (b -> d -> o -> a -> b), which exists whenever any d channel is observed.")

# =====================================================================================
# A4. T2 feasibility: CartPole-v1 after complete actuator loss.
#     Gymnasium CartPole-v1: Discrete(2), force_mag 10.0, tau 0.02, terminates at |theta| > 12 deg
#     or |x| > 2.4, truncates at 500 steps. Contract: H_det = 200, event_spacing = 250.
# =====================================================================================
L()
L("=" * 90)
L("A4. CartPole-v1 after complete actuator loss: how long until termination?")
L("=" * 90)
def cartpole_free_fall(theta0, thetadot0=0.0, x0=0.0, xdot0=0.0, force=0.0, max_steps=600):
    g_, mc, mp, l, tau = 9.8, 1.0, 0.1, 0.5, 0.02
    mt, pml = mc + mp, mp * l
    x, xd, th, thd = x0, xdot0, theta0, thetadot0
    for t in range(1, max_steps + 1):
        ct, st = np.cos(th), np.sin(th)
        temp = (force + pml * thd ** 2 * st) / mt
        thacc = (g_ * st - ct * temp) / (l * (4.0 / 3.0 - mp * ct ** 2 / mt))
        xacc = temp - pml * thacc * ct / mt
        x += tau * xd; xd += tau * xacc; th += tau * thd; thd += tau * thacc
        if abs(th) > 12 * np.pi / 180 or abs(x) > 2.4:
            return t
    return None
for th0 in (0.001, 0.01, 0.05, 0.10):
    n = cartpole_free_fall(th0)
    L(f"    initial pole angle {th0:6.3f} rad ({np.degrees(th0):5.2f} deg), zero force: terminates at step {n}")
L("    -> after complete actuator loss CartPole terminates in ~30-60 steps, far inside H_det = 200.")
L("       Contract G scores 'terminated' as H_det for BOTH arms, so HPDT = 200 for both and")
L("       Delta = RMDT(CUSUM) - RMDT(IBD) is identically 0 on CartPole by construction.")
L("       roadmap v4 requires the sign to hold on both T2 environments (v4.1 E5: point estimate > 0).")
L("       Also: ARL_0 = 1000 steps exceeds the CartPole-v1 episode cap of 500 steps entirely,")
L("       and event_spacing = 250 permits at most ONE event per 500-step episode.")

# =====================================================================================
# A5. IBD probe-budget arithmetic (external fact: arXiv 2603.18257 states the probing phase
#     is 2NT = 2*80*200 = 32,000 environment steps and is 'a one-time cost').
#     Contract: probe_budget = 0.05 = probe steps / total steps.
# =====================================================================================
L()
L("=" * 90)
L("A5. probe_budget = 0.05 vs the published IBD probe phase of 32,000 steps")
L("=" * 90)
for masks in (1, 2, 4):
    probe = 32000 * masks
    total = probe / 0.05
    L(f"    {masks} IBD mask estimation(s) at published config: {probe:8,d} probe steps "
      f"=> {total:11,.0f} environment steps per run at a 5% budget")
    L(f"        at ARL_0 = 1000 steps that single run contains ~{total/1000:8,.0f} EXPECTED FALSE ALARMS")
L(f"    confirmation-design.csv has 1764 rows; at 1 mask/run that is "
  f"{1764*32000/0.05:,.0f} environment steps of simulation.")
L("    HONEST CORRECTION (see throughput.py, measured on this arm64 host at 168,190 bare SCM")
L("    steps/s): 1.13e9 bare SCM steps is only ~1.9 h, so raw stepping is NOT the binding")
L("    constraint and a 'too slow' claim here would be wrong. The binding problem is STATISTICAL:")
L("      * a run long enough for one published-configuration IBD mask contains ~640 expected")
L("        false alarms at ARL_0 = 1000 steps, against ~1 change event. No one operates a change")
L("        detector at that point; the HPDT event-matching machinery (p=3, r=20, w_T=50) is")
L("        swamped -- P(a false alarm lands inside w_T=50 of the event) ~ 50/1000 = 5% per event,")
L("        which is spurious 'detection' at zero delay for BOTH arms.")
L("      * either ARL_0 must scale with the run length (e.g. a fixed false-alarm probability over")
L("        the run), or the run must be short and sequential IBD must run at a probe configuration")
L("        far below the published one -- at which point 'IBD as published, reproduced to numerical")
L("        anchors' (contract H) no longer describes the confirmatory arm.")
L("    confirmation-design.csv declares no steps_per_run and no events_per_run column, so this")
L("    trade-off is currently invisible in the frozen run matrix.")

# =====================================================================================
# A9. Oracle certification cost (contract C2): n_oracle = 4096 PAIRED samples, over all
#     (component, horizon, probe) triples, repeated AFTER EVERY CHANGE EVENT (CL-8).
# =====================================================================================
L()
L("=" * 90)
L("A9. Oracle C2 certification cost, measured")
L("=" * 90)
import time
n_oracle = 4096
for N_z, K_, Hh in ((20, 3, 3), (60, 3, 3), (120, 4, 3)):
    A = np.eye(N_z) * 0.9
    Bm = np.zeros((N_z, K_)); Bm[:K_, :] = np.eye(K_)
    gg2 = np.random.default_rng(0)
    probes = [(k, s) for k in range(K_) for s in (1.0, -1.0)]
    t0 = time.perf_counter()
    for (k, s) in probes:
        a0 = np.zeros(K_); a0[k] = s
        noise = gg2.normal(0, 0.1, size=(n_oracle, Hh, N_z))
        zt = np.zeros((n_oracle, N_z)); zc = np.zeros((n_oracle, N_z))
        for h in range(Hh):
            act_t = a0 if h == 0 else np.zeros(K_)
            zt = zt @ A.T + act_t @ Bm.T + noise[:, h]
            zc = zc @ A.T + noise[:, h]
    dt = time.perf_counter() - t0
    L(f"    N_z={N_z:3d} K={K_} |H|={Hh}: one full C2 certification = {dt*1000:7.1f} ms (vectorised, CRN)")
    L(f"        1764 rows x 1 event each: {1764*dt:8.1f} s ; x 4 events/run: {1764*4*dt:8.1f} s")
L("    -> C2 certification is cheap when vectorised. The FEASIBILITY risk is not arithmetic:")
L("       it is the T2 arm (Gymnasium python stepping, MLP residual models trained to")
L("       convergence on 200,000 steps per contract F, per cell) and the ~19x calibration")
L("       inflation from A2 -- none of which has a measured number anywhere in the plan.")

# =====================================================================================
# A6. Power of the roadmap's conjunctive decision rule at 10 seeds.
#     v4.1 E3 checks INTERVAL COVERAGE, never power. v4.1 E4 freezes delta = 20 and says
#     "pilot variance sets seed count only" -- but the only rule that can raise the seed
#     count is the coverage rule (< 93%), which is insensitive to power.
# =====================================================================================
L()
L("=" * 90)
L("A6. Required true effect for 80% power, and the conjunctive rule")
L("=" * 90)
from statistics import NormalDist
try:
    from scipy import stats  # noqa
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False
# t quantiles for df = 9 and df = 19, hard-coded (no scipy dependency)
T95 = {9: 1.8331, 19: 1.7291}
T80 = {9: 0.8834, 19: 0.8610}
for n, df in ((10, 9), (20, 19)):
    for sd in (10, 20, 40, 60):
        need = 20 + (T95[df] + T80[df]) * sd / sqrt(n)
        L(f"    n={n:2d} seeds, between-seed SD of the paired HPDT difference = {sd:3d} steps:"
          f"  need a TRUE effect of {need:6.1f} steps for 80% power on 'lower bound > delta=20'")
L("    The R1 superiority rule is a CONJUNCTION of 6 conditions (v4 sec.4 + v4.1 E1/E5):")
L("      LB(Delta) > 20 on scm_L and scm_N; LB(I) > 0 on scm_L and scm_N; sign on cartpole and pendulum.")
for p in (0.9, 0.8, 0.7):
    L(f"      if each condition independently had power {p:.2f}, joint power = {p**6:.3f}")
L("    The interaction I is a difference of FOUR cell means; if the four Delta estimates were")
L(f"    independent its SD would be ~{2.0:.0f}x that of a single Delta (var x 4), so LB(I) > 0 is the")
L("    weakest link, and nothing in the plan sizes it.")
L("    Note also: HPDT is bounded in [0, H_det=200] with an atom at 200, so the between-seed SD")
L("    is driven by the MISS RATE, not by delay. delta = 20 HPDT steps == a 10 percentage-point")
L("    difference in miss rate at zero delay difference: the 'detection delay' framing is not")
L("    what the primary estimand measures.")

# =====================================================================================
# A7. R0 decision rule is one-sided: "validated if the UPPER bound of Delta < delta0".
#     Delta = RMDT(CUSUM) - RMDT(IBD), positive favouring IBD.
# =====================================================================================
L()
L("=" * 90)
L("A7. R0 negative control admits an unbounded failure in the other direction")
L("=" * 90)
for true_delta in (0, -5, -50, -150):
    sd, n = 20.0, 10
    se = sd / sqrt(n)
    ub = true_delta + T95[9] * se
    L(f"    true Delta = {true_delta:5d} steps (IBD {'slower' if true_delta<0 else 'faster'} than CUSUM):"
      f" expected upper bound = {ub:7.1f}  -> R0 rule 'UB < delta0 = 10' says "
      f"{'VALIDATED' if ub < 10 else 'anomaly'}")
L("    -> R0 'validates' even when sequential IBD is 150 steps SLOWER than the classical")
L("       comparator in the clean regime. A negative control needs two-sided equivalence")
L("       (TOST: |Delta| bounded by delta0), not one-sided non-superiority.")

# =====================================================================================
# A8. T-E1b: graph reachability vs zero-noise finite difference. c_min = 0.2 does not
#     prevent NEAR-cancellation, and epsilon_faith has no value in the constants registry.
# =====================================================================================
L()
L("=" * 90)
L("A8. Near-cancellation rate: how often is a structurally reachable component's")
L("    zero-noise response tiny? (contract B: 'above eps_faith ... otherwise resample';")
L("    eps_faith is NOT in the section 0 constants registry)")
L("=" * 90)
g = np.random.default_rng(99)
for nb, K_ in ((4, 2), (6, 3), (8, 3)):
    mins = []
    for _ in range(4000):
        sgn = lambda sh, p: np.where(g.random(sh) < p, g.choice([-1.0, 1.0], sh) * g.uniform(0.2, 0.6, sh), 0.0)
        A = sgn((nb, nb), 0.5); Bm = sgn((nb, K_), 0.6)
        adj = (A != 0)
        reach = (Bm != 0).any(axis=1).copy()
        for _h in range(2, 4):
            reach |= (adj @ reach)
        best = np.zeros(nb)
        for k in range(K_):
            for s in (1.0, -1.0):
                a0 = np.zeros(K_); a0[k] = s
                b = Bm @ a0
                for h in range(1, 4):
                    best = np.maximum(best, np.abs(b))
                    b = A @ b
        if reach.any():
            mins.append(best[reach].min())
    mins = np.array(mins)
    for thr in (0.05, 0.02, 0.01):
        L(f"    N_b={nb} K={K_}: P(min response over reachable comps < {thr:.2f}) = "
          f"{np.mean(mins < thr):5.1%}")
L("    -> the resample rate depends entirely on eps_faith, which has no value. Contract L4 caps")
L("       the rejection rate at 20%; at eps = 0.05 that cap is already close to binding, and the")
L("       rejection ALSO conditions the instance population on effects being far from eps --")
L("       a selection effect that removes exactly the hard cases the estimand is about.")

L()
L("done.")
