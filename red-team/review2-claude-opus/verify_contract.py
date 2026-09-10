"""Round-2 independent verification of contract v3.1 equations.

Written from the CONTRACT TEXT ONLY (stage-0a-contract-v3.1.md sections B, C1, C3, C4, G, 0).
Deliberately does NOT import contract_ref.py or test_gate.py: every quantity is recomputed here
from the structural equations by brute-force simulation, then compared against the contract's
closed forms. Run with:
  /Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3 verify_contract.py
"""
import numpy as np

rng_master = np.random.default_rng(20260906)
OK = []


def check(name, cond, detail=""):
    OK.append(bool(cond))
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}")


# =====================================================================================
# V1. Contract C4, family L closed form:  M_{t,h} = 0 for h <= tau,  A_b^{h-1-tau} B_t for h > tau
#     verified by brute-force simulation of contract section B:
#       b_{t+1} = A_b b_t + B_t a_{t-tau} + eps^b_t
#     under do(a_t = a, a_{t+1..t+h-1} = 0), using COMMON RANDOM NUMBERS (contract B),
#     i.e. the SAME noise draws in the treated and control rollout.
# =====================================================================================
def simulate_L(A_b, B, tau, a0, h, noise, b0):
    """Brute-force rollout of the family-L body equation. Action a0 applied at t=0 only.
    Because of delay tau, a_{t-tau} means the action applied tau steps earlier reaches b now.
    noise[s] is eps^b at update s (common random numbers)."""
    b = b0.copy()
    K = B.shape[1]
    hist = [np.zeros(K)] * (tau + 1)          # action history buffer
    for s in range(h):                        # produce b_{0+h}
        a_now = a0 if s == 0 else np.zeros(K)
        hist.append(a_now)
        a_delayed = hist[len(hist) - 1 - tau]  # a_{s-tau}
        b = A_b @ b + B @ a_delayed + noise[s]
    return b


print("=== V1: C4 family-L open-loop response vs closed-form Jacobian (brute force, CRN) ===")
for trial in range(4):
    N_b = rng_master.integers(2, 5)
    K = rng_master.integers(1, 4)
    A_b = rng_master.normal(0, 0.4, size=(N_b, N_b))
    A_b *= 0.9 / max(abs(np.linalg.eigvals(A_b)))          # respect rho_max = 0.95
    B = rng_master.normal(0, 1.0, size=(N_b, K))
    b0 = np.zeros(N_b)                                      # z_bar = 0 is exact for family L
    for tau in (0, 1, 2, 3):
        for h in range(1, 7):
            a = rng_master.normal(size=K)
            noise = rng_master.normal(0, 0.3, size=(h, N_b))   # common random numbers
            treated = simulate_L(A_b, B, tau, a, h, noise, b0)
            control = simulate_L(A_b, B, tau, np.zeros(K), h, noise, b0)
            R_sim = treated - control
            M_closed = np.zeros_like(B) if h <= tau else np.linalg.matrix_power(A_b, h - 1 - tau) @ B
            check(f"V1 trial{trial} N_b={N_b} K={K} tau={tau} h={h}",
                  np.allclose(R_sim, M_closed @ a, atol=1e-10),
                  f"max|diff|={np.max(np.abs(R_sim - M_closed @ a)):.2e}")

# =====================================================================================
# V2. Same equation, but as a genuine EXPECTATION over independent noise (no CRN), to confirm
#     that the contract's E[.|do] - E[.|do(0)] definition converges to the same closed form
#     and to quantify how many paired samples are needed (contract C2 uses n_oracle = 4096).
# =====================================================================================
print("\n=== V2: C4 as an expectation difference, CRN vs independent sampling ===")
A_b = np.array([[0.8, 0.1], [0.0, 0.7]])
B = np.array([[1.0], [0.5]])
tau, h, a = 1, 3, np.array([1.0])
M_closed = np.linalg.matrix_power(A_b, h - 1 - tau) @ B
n = 4096
g = np.random.default_rng(7)
crn, indep = [], []
for _ in range(n):
    nz = g.normal(0, 0.3, size=(h, 2))
    nz2 = g.normal(0, 0.3, size=(h, 2))
    crn.append(simulate_L(A_b, B, tau, a, h, nz, np.zeros(2)) - simulate_L(A_b, B, tau, np.zeros(1), h, nz, np.zeros(2)))
    indep.append(simulate_L(A_b, B, tau, a, h, nz, np.zeros(2)) - simulate_L(A_b, B, tau, np.zeros(1), h, nz2, np.zeros(2)))
crn = np.array(crn); indep = np.array(indep)
truth = M_closed @ a
check("V2 CRN estimator is exact (zero variance)", np.allclose(crn.std(axis=0), 0),
      f"sd={crn.std(axis=0)}")
check("V2 independent-noise estimator is unbiased", np.allclose(indep.mean(axis=0), truth, atol=0.02),
      f"mean={indep.mean(axis=0)} truth={truth} se={indep.std(axis=0)/np.sqrt(n)}")

# =====================================================================================
# V3. Contract C1 structural reachability WITH DELAY, verified against a numerical
#     finite-difference derivation (the contract's own T-E1b "two independent derivations").
#     Component j is reachable within H iff exists h<=H, probe a in A, with |R_{h}(a)_j| > 0
#     at zero noise. Uses the FULL latent stack z = [b; d; w; x] from section B.
# =====================================================================================
print("\n=== V3: C1 reachability over full latent stack, numeric vs graph, incl. delay ===")


def step_full(z, a_delayed, A_b, C_d, A_d, A_w, A_x, B, dims):
    nb, nd, nw, nx = dims
    b, d, w, x = z[:nb], z[nb:nb + nd], z[nb + nd:nb + nd + nw], z[nb + nd + nw:]
    b2 = A_b @ b + B @ a_delayed
    d2 = A_d @ d + C_d @ b
    w2 = A_w @ w
    x2 = A_x @ x                       # NO action parent (contract A / T-E1a)
    return np.concatenate([b2, d2, w2, x2])


def numeric_reach(A_b, B, C_d, A_d, A_w, A_x, H, tau):
    nb, nd, nw, nx = A_b.shape[0], C_d.shape[0], A_w.shape[0], A_x.shape[0]
    dims = (nb, nd, nw, nx)
    N = sum(dims)
    K = B.shape[1]
    reach = np.zeros(N, bool)
    for k in range(K):
        for sign in (+1.0, -1.0):
            a0 = np.zeros(K); a0[k] = sign * 1.0        # probe set A = +-e_k, magnitude 1.0
            for h in range(1, H + 1):
                def roll(a_first):
                    z = np.zeros(N); hist = [np.zeros(K)] * (tau + 1)
                    for s in range(h):
                        hist.append(a_first if s == 0 else np.zeros(K))
                        z = step_full(z, hist[len(hist) - 1 - tau], A_b, C_d, A_d, A_w, A_x, B, dims)
                    return z
                reach |= np.abs(roll(a0) - roll(np.zeros(K))) > 1e-12
    return reach


def graph_reach(A_b, B, C_d, A_d, A_w, A_x, H, tau):
    """Independent re-implementation of C1 from the contract text (NOT imported from contract_ref)."""
    nb, nd, nw, nx = A_b.shape[0], C_d.shape[0], A_w.shape[0], A_x.shape[0]
    N = nb + nd + nw + nx
    adj = np.zeros((N, N), bool)
    adj[:nb, :nb] = A_b != 0
    adj[nb:nb + nd, :nb] = C_d != 0
    adj[nb:nb + nd, nb:nb + nd] = A_d != 0
    adj[nb + nd:nb + nd + nw, nb + nd:nb + nd + nw] = A_w != 0
    adj[nb + nd + nw:, nb + nd + nw:] = A_x != 0
    reach = np.zeros(N, bool)
    if H <= tau:
        return reach
    front = np.zeros(N, bool); front[:nb] = (B != 0).any(axis=1)   # first hit at h = tau + 1
    reach |= front
    for _h in range(tau + 2, H + 1):
        front = adj @ front
        reach |= front
    return reach


mism = 0
for trial in range(200):
    g = np.random.default_rng(1000 + trial)
    nb, nd, nw, nx, K = 3, 2, 2, 2, 2
    # all-positive entries with magnitude >= c_min = 0.2 so that no path cancellation can occur
    mask = lambda sh, p: (g.random(sh) < p)
    A_b = np.where(mask((nb, nb), .5), g.uniform(.2, .5, (nb, nb)), 0.0)
    B = np.where(mask((nb, K), .6), g.uniform(.2, 1.0, (nb, K)), 0.0)
    C_d = np.where(mask((nd, nb), .5), g.uniform(.2, .6, (nd, nb)), 0.0)
    A_d = np.where(mask((nd, nd), .4), g.uniform(.2, .5, (nd, nd)), 0.0)
    A_w = np.where(mask((nw, nw), .4), g.uniform(.2, .5, (nw, nw)), 0.0)
    A_x = np.where(mask((nx, nx), .4), g.uniform(.2, .5, (nx, nx)), 0.0)
    for tau in (0, 1, 2):
        for H in (1, 2, 3, 4):
            n_r = numeric_reach(A_b, B, C_d, A_d, A_w, A_x, H, tau)
            g_r = graph_reach(A_b, B, C_d, A_d, A_w, A_x, H, tau)
            if not np.array_equal(n_r, g_r):
                mism += 1
                if mism < 4:
                    print("   mismatch", trial, tau, H, n_r.astype(int), g_r.astype(int))
check("V3 graph == finite-difference on 200 sign-positive instances x tau x H", mism == 0,
      f"mismatches={mism}")

# ---- V3b: the same check WITHOUT the all-positive restriction (path cancellation allowed) ----
mism_signed = 0
for trial in range(400):
    g = np.random.default_rng(50000 + trial)
    nb, nd, nw, nx, K = 3, 2, 1, 1, 2
    sgn = lambda sh, p: np.where(g.random(sh) < p, g.choice([-1.0, 1.0], sh) * g.uniform(.2, .6, sh), 0.0)
    A_b = sgn((nb, nb), .6); B = sgn((nb, K), .7); C_d = sgn((nd, nb), .6)
    A_d = sgn((nd, nd), .4); A_w = sgn((nw, nw), .4); A_x = sgn((nx, nx), .4)
    for tau in (0, 1):
        for H in (1, 2, 3, 4):
            if not np.array_equal(numeric_reach(A_b, B, C_d, A_d, A_w, A_x, H, tau),
                                  graph_reach(A_b, B, C_d, A_d, A_w, A_x, H, tau)):
                mism_signed += 1
print(f"NOTE  V3b signed-entry instances where numeric != graph (path cancellation): {mism_signed} "
      f"of {400*2*4} (contract B faithfulness margin c_min=0.2 does NOT prevent this)")

# =====================================================================================
# V4. Contract C3:  S^obs,eps = { c : avail=1, assign=j!=None, |gain_c| * e_j > eps }
#     Recomputed from the text and cross-checked on the contract's own K8 case
#     (gain 0, 0.01, -1 on a controllable channel -> removed, removed, kept).
# =====================================================================================
print("\n=== V4: C3 observed support incl. gain (contract K8 case) ===")
def s_obs(e, assign, gain, avail, eps):
    return [bool(avail[c] and assign[c] is not None and abs(gain[c]) * e[assign[c]] > eps)
            for c in range(len(assign))]
e = [1.0]
check("V4 K8 gain=0 removed", s_obs(e, [0], [0.0], [True], 0.05) == [False])
check("V4 K8 gain=0.01 removed", s_obs(e, [0], [0.01], [True], 0.05) == [False], "0.01*1.0=0.01 !> 0.05")
check("V4 K8 gain=-1 kept", s_obs(e, [0], [-1.0], [True], 0.05) == [True], "sign flip keeps membership")

# =====================================================================================
# V5. Contract G, HPDT: "mean over events of min(delay, H_det) for detected events and
#     H_det for missed or terminated events". Recomputed by hand and checked.
# =====================================================================================
print("\n=== V5: G horizon-penalised detection time, hand-computed ===")
def hpdt_mine(delays, outcomes, H_det):
    vals = [min(d, H_det) if o == 'detected' else H_det for d, o in zip(delays, outcomes)]
    return sum(vals) / len(vals)
check("V5 all detected", hpdt_mine([5, 7], ['detected'] * 2, 100) == 6.0)
check("V5 one missed", hpdt_mine([5, 0], ['detected', 'missed'], 100) == 52.5)
check("V5 delay beyond horizon is capped", hpdt_mine([5, 250], ['detected'] * 2, 100) == 52.5)
check("V5 three events, one terminated",
      abs(hpdt_mine([10, 20, 999], ['detected', 'detected', 'terminated'], 200) - (10 + 20 + 200) / 3) < 1e-12,
      f"={hpdt_mine([10,20,999],['detected','detected','terminated'],200):.4f}")

print(f"\n{sum(OK)}/{len(OK)} checks passed")
raise SystemExit(0 if all(OK) else 1)
