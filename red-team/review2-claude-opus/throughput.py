"""Measure raw per-step throughput of a small family-L SCM on this machine, to ground
the feasibility arithmetic in attacks.py A5. No estimator, no oracle, no logging: an
absolute upper bound on achievable speed."""
import numpy as np, time, platform
N_z, C, K = 20, 120, 3
A = np.eye(N_z)*0.9; B = np.zeros((N_z,K)); B[:3,:] = np.eye(3)
Assign = np.zeros((C,N_z)); 
for c in range(C): Assign[c, c % N_z] = 1.0
W_o = np.random.default_rng(0).normal(0,0.05,size=(K,C))
z = np.zeros(N_z); rng = np.random.default_rng(0)
STEPS = 200_000
t0 = time.perf_counter()
for _ in range(STEPS):
    o = Assign @ z + rng.normal(0,0.1,size=C)
    a = np.clip(W_o @ o, -2, 2)
    z = A @ z + B @ a + rng.normal(0,0.1,size=N_z)
dt = time.perf_counter() - t0
sps = STEPS/dt
print(f"host: {platform.machine()} {platform.system()}  numpy {np.__version__}")
print(f"bare SCM (N_z={N_z}, C={C}, K={K}): {sps:,.0f} steps/s  ({dt/STEPS*1e6:.1f} us/step)")
for label, total in [("1 run @ 640,000 steps (1 IBD mask at 5% budget)", 640_000),
                     ("1764 rows x 640,000 steps", 1764*640_000),
                     ("1764 rows x 385,000 calibration steps only (ARL_0 +-10%)", 1764*385_000)]:
    s = total/sps
    print(f"  {label}: {s:,.0f} s = {s/3600:,.1f} h = {s/86400:,.1f} days  (bare SCM, no estimator/oracle/IO)")
