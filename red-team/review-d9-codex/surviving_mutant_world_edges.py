"""New gate mutant: silently omit A_w and A_x edges from the full adjacency.

Exit zero means the current gate does not reject the mutant.  The explicit
distinctness assertion prevents an equivalent/no-op mutation claim.
"""
from __future__ import annotations

import pathlib
import sys
import traceback

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
GATE = HERE.parent / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))

import contract_ref as ref
import test_gate
import test_proof_theatre

original = ref.build_adjacency


def adjacency_without_world_or_distractor_edges(A_b, C_d=None, A_d=None, A_w=None, A_x=None):
    adjacency, slices = original(A_b, C_d, A_d, A_w, A_x)
    # MUTANT: family-L A_w and A_x structure disappears from the declared full block graph.
    if A_w is not None:
        adjacency[slices["w"], slices["w"]] = False
    if A_x is not None:
        adjacency[slices["x"], slices["x"]] = False
    return adjacency, slices


A = np.eye(1) * .5; Aw = np.eye(1) * .7; Ax = np.eye(1) * .8
base, _ = original(A, A_w=Aw, A_x=Ax)
mutated, _ = adjacency_without_world_or_distractor_edges(A, A_w=Aw, A_x=Ax)
assert not np.array_equal(base, mutated), "mutant must differ from the reference on an explicit input"

ref.build_adjacency = adjacency_without_world_or_distractor_edges
test_gate.build_adjacency = adjacency_without_world_or_distractor_edges

passed = failed = 0
for module in (test_gate, test_proof_theatre):
    for name in sorted(n for n in dir(module) if n.startswith("test_")):
        try:
            getattr(module, name)(); passed += 1
        except Exception:
            failed += 1; traceback.print_exc()

print(f"world/distractor-edge omission mutant: {passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
