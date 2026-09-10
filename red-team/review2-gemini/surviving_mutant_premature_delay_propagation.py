"""Adversarial gate check (Gemini round 2): premature graph propagation during actuator delay.

Contract v3.1 C1 defines structural reachability over all latents with delay tau:
first arrival occurs at h = tau + 1, and each additional hop across edges in A_b
or C_d requires an additional step (h = tau + 2, tau + 3, ...).

This mutant replaces `range(tau + 2, H + 1)` with `range(2, H + 1)`.
For any delayed system (tau >= 1), this allows multi-hop graph propagation to
occur immediately as if tau == 0, violating causality by letting information leapfrog
the delay queue.

Exit zero means all current frozen gate assertion tests still pass.
"""
import pathlib
import sys
import traceback
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE = ROOT / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))

import contract_ref as ref
import test_gate
import test_proof_theatre

orig_srf = ref.structural_reach_full

def mutant_premature_propagation(A_b, B, H, tau=0, C_d=None, A_d=None, A_w=None, A_x=None):
    adj, sl = ref.build_adjacency(A_b, C_d, A_d, A_w, A_x)
    N = adj.shape[0]; reach = np.zeros(N, bool)
    if H <= tau:
        return reach
    frontier = np.zeros(N, bool); frontier[sl['b']] = (B != 0).any(axis=1)
    reach |= frontier
    # MUTANT: propagates for H-1 hops regardless of tau!
    for _ in range(2, H + 1):
        frontier = (adj.astype(int) @ frontier.astype(int)) > 0
        reach |= frontier
    return reach

ref.structural_reach_full = mutant_premature_propagation
ref.structural_reach = lambda A, B, H, tau=0: mutant_premature_propagation(A, B, H, tau)[:A.shape[0]]
test_gate.structural_reach_full = mutant_premature_propagation
test_gate.structural_reach = lambda A, B, H, tau=0: mutant_premature_propagation(A, B, H, tau)[:A.shape[0]]

failed = passed = 0
for module in (test_gate, test_proof_theatre):
    for name in sorted(n for n in dir(module) if n.startswith('test_')):
        try:
            getattr(module, name)()
            passed += 1
        except Exception:
            failed += 1
            traceback.print_exc()

print(f"Premature-delay-propagation mutant: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
