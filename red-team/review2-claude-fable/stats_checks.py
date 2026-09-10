"""Numerical checks behind statistical findings.
(A) ARL_0 = 1000 estimated on >= 20,000 stationary steps cannot meet a +-10% tolerance.
(B) T-E2d 'max pairwise |corr| <= delta_inv = 0.05' under the null with 100 distractor channels: false-failure rate vs T.
(C) CartPole (gymnasium equations) with complete actuator loss: steps to termination -> every confirmatory event 'terminated'.
(D) Paired-t power at n=10 seeds for delta=20 HPDT steps as a function of the SD of per-seed differences."""
import numpy as np
rng = np.random.default_rng(1)

# (A) run lengths: alarms after p=3 consecutive raises with refractory r=20; model run lengths as geometric(1/1000) + r
print("(A) ARL_0 estimation precision")
for T in (20_000, 100_000, 384_000, 1_000_000):
    rel = []
    for _ in range(2000):
        rl = rng.geometric(1/1000, size=5000) + 20
        cum = np.cumsum(rl); n_alarm = int((cum <= T).sum())
        rel.append(T / max(n_alarm, 1) / 1020 - 1)          # true ARL is 1020 with the refractory
    rel = np.array(rel)
    print(f"  T={T:>9,} steps: expected alarms ~{T/1020:6.1f}; P(|rel err| <= 10%) = {np.mean(np.abs(rel) <= 0.10):.3f}; "
          f"95% rel-err band = [{np.percentile(rel,2.5):+.2f}, {np.percentile(rel,97.5):+.2f}]")
print("  -> at 20,000 steps the tolerance is met by luck (<40%); ~384k steps are needed for 95% within +-10%.")

# (B) null max |corr| with K=4 probe dims, N_x distractors
print("(B) T-E2d null false-failure rate (max |corr| > 0.05 when actions are truly randomised)")
for N_x in (10, 30, 100):
    for T in (4000, 20000, 50000):
        fails = 0; reps = 200
        for _ in range(reps):
            a = rng.uniform(-1, 1, size=(T, 4)); x = rng.normal(size=(T, N_x))
            c = np.corrcoef(a.T, x.T)[:4, 4:]
            fails += np.abs(c).max() > 0.05
        print(f"  N_x={N_x:3d} T={T:6d}: P(false fail) = {fails/reps:.2f}")

# (C) CartPole-v1 physics (gymnasium cartpole.py): g=9.8, mc=1.0, mp=0.1, l=0.5, force=10, dt=0.02, euler
print("(C) CartPole complete actuator loss (force = 0 forever) from the balanced start region")
def cartpole_steps_to_term(state, force_fn, max_steps=2000):
    x, xd, th, thd = state; g, mc, mp, l, dt = 9.8, 1.0, 0.1, 0.5, 0.02; tm = mc + mp; pml = mp * l
    for t in range(1, max_steps + 1):
        F = force_fn(t, (x, xd, th, thd)); c, s = np.cos(th), np.sin(th)
        temp = (F + pml * thd**2 * s) / tm
        thacc = (g * s - c * temp) / (l * (4/3 - mp * c**2 / tm)); xacc = temp - pml * thacc * c / tm
        x += dt * xd; xd += dt * xacc; th += dt * thd; thd += dt * thacc
        if abs(x) > 2.4 or abs(th) > 12 * 2 * np.pi / 360: return t
    return max_steps
res = np.array([cartpole_steps_to_term(rng.uniform(-0.05, 0.05, 4), lambda t, s: 0.0) for _ in range(1000)])
print(f"  from reset distribution, zero force: steps to termination median {np.median(res):.0f}, max {res.max()}, "
      f"P(term within H_det=200) = {np.mean(res <= 200):.3f}")
# from a well-balanced state (tiny angle) the fall is slower but still bounded:
res2 = np.array([cartpole_steps_to_term(np.array([0, 0, 1e-3 * rng.choice([-1, 1]), 0.0]), lambda t, s: 0.0) for _ in range(20)])
print(f"  from |theta|=1e-3 rad, zero force: steps to termination {res2.min()}..{res2.max()}")
res3 = np.array([cartpole_steps_to_term(rng.uniform(-0.05, 0.05, 4), lambda t, s: rng.choice([-10.0, 10.0])) for _ in range(1000)])
print(f"  reference: random +-10 N policy (no loss): median {np.median(res3):.0f} steps, P(<=200) = {np.mean(res3<=200):.3f}")
print("  -> with K=1, 'complete actuator loss' on CartPole terminates every episode long before H_det=200,")
print("     so HPDT = 200 for BOTH detectors, Delta = 0 exactly, and the T2 sign rule (point estimate > 0) cannot hold.")

# (D) paired t power, n=10, one-sided lower bound > delta at 95%
from math import sqrt
print("(D) power to claim R1 superiority (lower 95% bound > delta=20) with n=10 seeds")
t975 = 2.262
for true_delta in (30, 40, 60):
    for sd in (20, 40, 80):
        # lower bound > 20  <=> mean_d - t*sd/sqrt(10) > 20 ; simulate
        m = rng.normal(true_delta, sd / sqrt(10), size=20000); s = sd * np.sqrt(rng.chisquare(9, size=20000) / 9)
        power = np.mean(m - t975 * s / sqrt(10) > 20)
        print(f"  true Delta={true_delta:2d}, SD(per-seed diff)={sd:2d}: power={power:.2f}")
print("  -> no power analysis exists in the plan; with HPDT censored at 200 the per-seed SD is plausibly 40-80 steps.")
