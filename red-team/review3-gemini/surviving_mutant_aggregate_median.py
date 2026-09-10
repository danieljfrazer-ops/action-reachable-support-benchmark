"""Adversarial gate check (Gemini round 3): aggregate_primary uses median instead of mean.

Contract v3.3 / Roadmap v4.1 E2 defines the primary aggregated estimand as the
EQUAL-WEIGHT MEAN over distractor levels and delays of per-seed paired differences.

This mutant replaces `np.mean(v)` with `np.median(v)`.
In a realistic benchmark with 3 distractor levels (10, 30, 100), the median can diverge
by 100% from the mean.
However, `test_gate.py`'s `test_aggregate_primary_pairs_by_seed_and_cell` only provides
two levels for seed 0 (levels 10 and 30, yielding differences 20.0 and 50.0).
For any two numbers, mean([a, b]) == median([a, b]) == (a + b) / 2.

Furthermore, `mutants.py` does not register or test `aggregate_primary`, `count_alarms`,
or `match_alarms`.

Exit zero means all current frozen gate assertion tests still pass.
"""
import pathlib
import sys
import traceback
from collections import defaultdict
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE = ROOT / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))

import contract_ref as ref
import test_gate
import test_proof_theatre

def mutant_aggregate_median(rows, est_a="cusum_channel_agnostic", est_b="seq_ibd"):
    cell = defaultdict(dict)
    for r in rows:
        cell[(r["seed"], r["level"], r["delay"])][r["estimator"]] = float(r["hpdt"])
    per_seed = defaultdict(list); dropped = 0
    for (seed, lvl, dly), v in cell.items():
        if est_a in v and est_b in v: per_seed[seed].append(v[est_a] - v[est_b])
        else: dropped += 1
    # MUTANT: computes median instead of equal-weight mean!
    diffs = {s: float(np.median(v)) for s, v in per_seed.items()}
    return diffs, dropped

ref.aggregate_primary = mutant_aggregate_median
test_gate.aggregate_primary = mutant_aggregate_median

failed = passed = 0
for module in (test_gate, test_proof_theatre):
    for name in sorted(n for n in dir(module) if n.startswith("test_")):
        try:
            getattr(module, name)()
            passed += 1
        except Exception:
            failed += 1
            traceback.print_exc()

print(f"Aggregate-median mutant: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
