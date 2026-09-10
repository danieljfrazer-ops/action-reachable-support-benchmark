"""Adversarial gate check: cap every positive actuator delay at one step.

Contract v3 permits delays beyond one. The current gate exercises only tau=0 and
tau=1. This mutant is therefore wrong for tau>=2. Exit zero means the frozen
gate did not reject it.
"""
import pathlib
import sys
import traceback

import numpy as np

GATE = pathlib.Path(__file__).resolve().parents[1] / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))

import test_gate
import test_proof_theatre


def mutant_open_loop_response(A, B, a, h, tau=0):
    """Wrong: all tau>=1 are treated as tau=1."""
    n, k = B.shape
    b = np.zeros(n)
    arrival = 1 if tau == 0 else 2
    for step in range(1, h + 1):
        act = a if step == arrival else np.zeros(k)
        b = A @ b + B @ act
    return b


test_gate.open_loop_response = mutant_open_loop_response

failed = passed = 0
for module in (test_gate, test_proof_theatre):
    for name in sorted(n for n in dir(module) if n.startswith("test_")):
        try:
            getattr(module, name)()
            passed += 1
        except Exception:
            failed += 1
            traceback.print_exc()

print(f"mutated gate: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
