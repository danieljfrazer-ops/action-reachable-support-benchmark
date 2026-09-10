"""Mutants that the frozen gate DOES catch (recorded for the 'attacks that failed' section)."""
import sys, pathlib, numpy as np
GATE = pathlib.Path(__file__).resolve().parents[1] / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))
import contract_ref as ref, test_gate
def failures():
    bad = []
    for name in sorted(t for t in dir(test_gate) if t.startswith("test_")):
        try: getattr(test_gate, name)()
        except Exception: bad.append(name)
    return bad
def with_patch(**kw):
    saved = {k: (getattr(ref, k), getattr(test_gate, k)) for k in kw}
    for k, v in kw.items(): setattr(ref, k, v); setattr(test_gate, k, v)
    try: return failures()
    finally:
        for k, (a, b) in saved.items(): setattr(ref, k, a); setattr(test_gate, k, b)
orig_srf, orig_ba = ref.structural_reach_full, ref.build_adjacency
def adj_transposed(*a, **k):
    adj, sl = orig_ba(*a, **k); return adj.T.copy(), sl
def reach_offbyone(A_b, B, H, tau=0, C_d=None, A_d=None, A_w=None, A_x=None):
    adj, sl = ref.build_adjacency(A_b, C_d, A_d, A_w, A_x); N = adj.shape[0]; reach = np.zeros(N, bool)
    if H <= tau: return reach
    frontier = np.zeros(N, bool); frontier[sl["b"]] = (B != 0).any(axis=1); reach |= frontier
    for _ in range(tau + 2, H):            # one propagation too few
        frontier = (adj.astype(int) @ frontier.astype(int)) > 0; reach |= frontier
    return reach
def olr_action_held_until_tau(A, B, a, h, tau=0, zbar=None, step_fn=None):
    n, k = B.shape; f = step_fn or (lambda b, act: A @ b + B @ act); z0 = np.zeros(n) if zbar is None else np.asarray(zbar, float)
    def roll(a0):
        b = z0.copy()
        for step in range(1, h + 1):
            b = f(b, a0 if step <= 1 + tau else np.zeros(k))   # action held for tau+1 steps instead of applied once
        return b
    return roll(np.asarray(a, float)) - roll(np.zeros(k))
def s_obs_signed_gain(latent_effect, assign, gain, avail, eps):
    C = len(assign); out = np.zeros(C, bool)
    for c in range(C):
        j = assign[c]
        if j < 0 or not avail[c]: continue
        out[c] = gain[c] * latent_effect[j] > eps
    return out
def hpdt_missed_zero(delays, outcome, horizon):
    d = np.where(np.asarray(outcome) == 'detected', np.minimum(np.asarray(delays, float), horizon), 0.0); return float(d.mean())
mutants = {
    "adjacency transposed (edge direction reversed)": dict(build_adjacency=adj_transposed),
    "reachability propagates one step too few": dict(structural_reach_full=reach_offbyone),
    "open-loop action held for tau+1 steps": dict(open_loop_response=olr_action_held_until_tau),
    "signed gain instead of |gain|": dict(s_obs_eps=s_obs_signed_gain),
    "HPDT scores missed as 0": dict(hpdt=hpdt_missed_zero),
}
for name, patch in mutants.items():
    bad = with_patch(**patch); print(f"{'KILLED  ' if bad else 'SURVIVED'} {name}: {len(bad)} failing {bad}")
