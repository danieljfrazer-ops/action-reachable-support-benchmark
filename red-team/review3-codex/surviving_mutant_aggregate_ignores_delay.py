"""New round-3 mutant: aggregate_primary silently drops delay from the cell key.

This is wrong for SCM confirmation rows, which contain delay 0 and 2.  Exit zero
means the frozen assertion suite does not reject the mutant.
"""
from __future__ import annotations

from collections import defaultdict
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


def aggregate_without_delay(rows, est_a="cusum_channel_agnostic", est_b="seq_ibd"):
    cell = defaultdict(dict)
    for row in rows:
        # MUTANT: delay omitted, so the later delay overwrites the earlier one.
        cell[(row["seed"], row["level"])][row["estimator"]] = float(row["hpdt"])
    per_seed = defaultdict(list); dropped = 0
    for (seed, _level), values in cell.items():
        if est_a in values and est_b in values:
            per_seed[seed].append(values[est_a] - values[est_b])
        else:
            dropped += 1
    return {seed: float(np.mean(values)) for seed, values in per_seed.items()}, dropped


ref.aggregate_primary = aggregate_without_delay
test_gate.aggregate_primary = aggregate_without_delay

passed = failed = 0
for module in (test_gate, test_proof_theatre):
    for name in sorted(n for n in dir(module) if n.startswith("test_")):
        try:
            getattr(module, name)()
            passed += 1
        except Exception:
            failed += 1
            traceback.print_exc()

print(f"aggregate-delay-omission mutant: {passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
