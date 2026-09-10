#!/usr/bin/env python3
"""A direction-destroying aggregation mutant that the frozen gate does not reject."""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

GATE = Path(__file__).parents[1] / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))
import contract_ref as ref  # noqa: E402
import test_gate  # noqa: E402
import test_proof_theatre  # noqa: E402


def aggregate_abs(rows, est_a="cusum_channel_agnostic", est_b="seq_ibd"):
    """Mutation: erase which arm wins by taking |est_a-est_b| per cell."""
    cell = defaultdict(dict)
    for row in rows:
        cell[(row["seed"], row["level"], row["delay"])][row["estimator"]] = float(row["hpdt"])
    per_seed = defaultdict(list); dropped = 0
    for (seed, _level, _delay), values in cell.items():
        if est_a in values and est_b in values:
            per_seed[seed].append(abs(values[est_a] - values[est_b]))
        else:
            dropped += 1
    return {seed: float(np.mean(values)) for seed, values in per_seed.items()}, dropped


# Prove this is a real mutant on a direction-reversing input.
probe = [
    {"seed": 0, "level": 10, "delay": 0, "estimator": "cusum_channel_agnostic", "hpdt": 20},
    {"seed": 0, "level": 10, "delay": 0, "estimator": "seq_ibd", "hpdt": 40},
]
assert ref.aggregate_primary(probe)[0][0] == -20
assert aggregate_abs(probe)[0][0] == 20

test_gate.aggregate_primary = aggregate_abs
failed = 0; passed = 0
for module in (test_gate, test_proof_theatre):
    for name in sorted(n for n in dir(module) if n.startswith("test_")):
        try:
            getattr(module, name)(); passed += 1
        except Exception as exc:
            failed += 1; print(f"FAIL {module.__name__}.{name}: {exc}")
print(f"absolute-difference mutant: {passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
