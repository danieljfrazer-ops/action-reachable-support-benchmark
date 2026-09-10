"""New round-2 mutant: delete every d->d edge from the full SCM adjacency.

This is wrong when one downstream component reaches another through A_d.  The
frozen K10 case contains only one directly reached d component, so it cannot
detect the omission.  Exit zero means all current assertion tests still pass.
"""
import pathlib
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE = ROOT / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))

import contract_ref as ref
import test_gate
import test_proof_theatre

original = ref.build_adjacency


def omit_downstream_internal_edges(A_b, C_d=None, A_d=None, A_w=None, A_x=None):
    adj, slices = original(A_b, C_d, A_d, A_w, A_x)
    adj[slices["d"], slices["d"]] = False
    return adj, slices


ref.build_adjacency = omit_downstream_internal_edges
test_gate.build_adjacency = omit_downstream_internal_edges

failed = passed = 0
for module in (test_gate, test_proof_theatre):
    for name in sorted(n for n in dir(module) if n.startswith("test_")):
        try:
            getattr(module, name)()
            passed += 1
        except Exception:
            failed += 1
            traceback.print_exc()

print(f"A_d-omission mutant: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
