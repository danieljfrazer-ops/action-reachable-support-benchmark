"""Independent execution of contract equations (not via test_gate).
(1) C4 closed form M_{t,h} = A_b^{h-1-tau} B for h > tau, 0 otherwise, checked by simulating the FULL noisy
    family-L system with common random numbers (noise indexed by (seed, variable, t)) and taking paired means.
(2) C1 graph reachability vs the numeric nonzero pattern of the delayed Jacobians (agree under faithfulness).
(3) C2 for family L: with CRN the paired difference is exactly deterministic -> certification intervals have zero width."""
import numpy as np, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "executable-proofs" / "gate"))
import contract_ref as ref
rng = np.random.default_rng(20260906)
N_b, N_d, K, tau, H = 3, 2, 2, 2, 5
A_b = np.array([[0.6, 0.25, 0.0], [0.0, 0.5, 0.3], [0.2, 0.0, 0.55]]); B = np.array([[1.0, 0.0], [0.0, 0.8], [0.0, 0.0]])
C_d = np.array([[0.7, 0.0, 0.0], [0.0, 0.0, 0.9]]); A_d = np.diag([0.4, 0.3])
assert max(abs(np.linalg.eigvals(A_b))) <= 0.95

def simulate(a0, noise_b, noise_d, h):
    """b_{t+1} = A_b b_t + B a_{t-tau} + eps_b ; d_{t+1} = A_d d_t + C_d b_t + eps_d ; z_t = 0 (z̄ exact for family L)."""
    b = np.zeros(N_b); d = np.zeros(N_d); actions = [np.zeros(K)] * (tau + 1)   # a_{t-tau..t}
    actions[-1] = a0                                                             # a_t = a0, later actions 0
    for step in range(1, h + 1):
        a_delayed = actions[0]
        d = A_d @ d + C_d @ b + noise_d[step]
        b = A_b @ b + B @ a_delayed + noise_b[step]
        actions = actions[1:] + [np.zeros(K)]
    return b, d

n = 4096; probes = [s * np.eye(K)[k] for k in range(K) for s in (+1, -1)]   # frozen order +e1,-e1,+e2,-e2
max_err = 0.0
for h in range(1, H + 1):
    for a in probes:
        diffs = []
        for i in range(n):
            nb = rng.normal(size=(h + 1, N_b)) * 0.3; nd = rng.normal(size=(h + 1, N_d)) * 0.3
            b1, _ = simulate(a, nb, nd, h); b0, _ = simulate(np.zeros(K), nb, nd, h)   # common random numbers
            diffs.append(b1 - b0)
        diffs = np.array(diffs)
        closed = ref.jacobian_piecewise(A_b, B, h, tau) @ a
        assert np.allclose(diffs.std(axis=0), 0.0), "CRN paired difference must be deterministic in family L"
        max_err = max(max_err, np.abs(diffs.mean(axis=0) - closed).max())
print(f"(1) C4 closed form vs paired-CRN simulation over h=1..{H}, tau={tau}, 2K={2*K} probes: max abs error {max_err:.2e}")
print(f"    h<=tau responses are exactly zero: {all(np.allclose(ref.jacobian_piecewise(A_b,B,h,tau),0) for h in range(1,tau+1))}")

# (2) graph reachability vs numeric pattern of the delayed Jacobians on [b; d]
def numeric_reach(H):
    r = np.zeros(N_b + N_d, bool)
    for h in range(tau + 1, H + 1):
        Mb = ref.jacobian_piecewise(A_b, B, h, tau)
        # d_{t+h} response: sum_{s} A_d^{h-1-s} C_d (b response at s)
        Md = np.zeros((N_d, K))
        for s in range(tau + 1, h):
            Md += np.linalg.matrix_power(A_d, h - 1 - s) @ C_d @ ref.jacobian_piecewise(A_b, B, s, tau)
        r[:N_b] |= (np.abs(Mb) > 1e-12).any(axis=1); r[N_b:] |= (np.abs(Md) > 1e-12).any(axis=1)
    return r
ok = True
for Hh in range(1, 8):
    g = ref.structural_reach_full(A_b, B, Hh, tau, C_d, A_d)
    nu = numeric_reach(Hh); ok &= (g == nu).all()
    print(f"(2) H={Hh} tau={tau}: graph {g.astype(int).tolist()} numeric {nu.astype(int).tolist()} agree={(g==nu).all()}")
print(f"(2) graph reachability == numeric Jacobian pattern for all H: {ok}")
print("(3) family L CRN paired difference has zero variance (asserted above): certification intervals are degenerate for L;"
      " the n_oracle=4096 / Bonferroni machinery only does work on family N.")
