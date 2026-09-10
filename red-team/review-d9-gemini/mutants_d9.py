"""
mutants_d9.py -- New mutants for D-9 review against frozen gate (e662b7429b6b347d / v3.4).
Written by Gemini for Task 3 of D-9 Review (7 September 2026).

Follows the protocol of mutants.py and mutants_r3.py:
  1. Monkeypatch contract_ref functions.
  2. Re-run the full gate suite (test_gate + test_proof_theatre).
  3. Verify that the mutant differs from the original on explicit probe input(s).
  4. Count failing tests. A mutant with 0 failing tests SURVIVES the gate.

Run with:
  /Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3 mutants_d9.py
"""

import sys, os, pathlib
import numpy as np

GATE_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "executable-proofs", "gate"))
sys.path.insert(0, GATE_DIR)

import contract_ref as ref
import test_gate, test_proof_theatre

ORIG_PW_CORR = ref.pairwise_corr
ORIG_MATCH_ALARMS = ref.match_alarms

def count_gate_failures():
    failed = 0
    failed_names = []
    for mod in (test_gate, test_proof_theatre):
        for name in sorted(n for n in dir(mod) if n.startswith("test_")):
            try:
                getattr(mod, name)()
            except Exception:
                failed += 1
                failed_names.append(f"{mod.__name__}.{name}")
    return failed, failed_names

def with_patch(**kw):
    saved_ref = {k: getattr(ref, k, None) for k in kw}
    saved_test = {k: getattr(test_gate, k, None) for k in kw}
    for k, v in kw.items():
        setattr(ref, k, v)
        setattr(test_gate, k, v)
    try:
        return count_gate_failures()
    finally:
        for k, v in saved_ref.items():
            if v is not None: setattr(ref, k, v)
        for k, v in saved_test.items():
            if v is not None: setattr(test_gate, k, v)

# --------------------------------------------------------------------------------------------------
# Mutant D9-GM-M1: pairwise_corr drops abs()
#   Contract E2c specifies: "|corr| of one declared witness pair (E2c)."
#   Dropping abs() produces negative correlation when the witness pair is anti-correlated.
#   In test_gate, pairwise_corr is only tested once in test_E2_global_max_is_not_the_witness_value,
#   where both columns have positive correlation.
# --------------------------------------------------------------------------------------------------
def pairwise_corr_no_abs(a, x, k, j):
    a = np.atleast_2d(a.T).T; x = np.atleast_2d(x.T).T
    if a[:, k].std() == 0 or x[:, j].std() == 0: return float('nan')
    return float(np.corrcoef(a[:, k], x[:, j])[0, 1])

# --------------------------------------------------------------------------------------------------
# Mutant D9-GM-M2: match_alarms strict inequality at upper attribution boundary (< end)
#   Contract section G specifies: "an alarm at delay d in (0, H_det] after event e ... is attributed".
#   The interval is (e, min(e + H_det, nxt, episode_end)].
#   Using strict inequality (< end instead of <= end) classifies an alarm exactly at e + H_det
#   as 'missed' and adds it to false_alarms, violating boundary inclusion.
#   test_gate has tests for e < t and t > end, but none on the exact upper boundary t == end.
# --------------------------------------------------------------------------------------------------
def match_alarms_strict_upper(alarm_times, event_times, H_det, episode_end):
    ev = sorted(event_times); alarms = sorted(alarm_times); used = set(); delays, outcomes = [], []
    for i, e in enumerate(ev):
        nxt = ev[i+1] if i + 1 < len(ev) else episode_end
        end = min(e + H_det, nxt, episode_end); hit = None
        for t in alarms:
            if e < t < end: hit = t; break
        if hit is None: delays.append(H_det); outcomes.append("missed")
        else: used.add(hit); delays.append(hit - e); outcomes.append("detected")
    false_alarms = [t for t in alarms if t not in used]
    return delays, outcomes, false_alarms

def run_mutant_assessment():
    print("=" * 80)
    print("mutants_d9.py: Evaluating New Mutants Against Frozen Gate")
    print("=" * 80)

    # 1. Verify clean baseline
    base_fails, base_names = count_gate_failures()
    print(f"Base gate run: {base_fails} failing tests (clean baseline required: 0)")
    assert base_fails == 0, f"Base gate is not clean: {base_names}"

    # 2. Test Mutant D9-GM-M1
    print("\n--- Mutant D9-GM-M1: pairwise_corr drops abs() ---")
    probe_a = np.array([[-1.0], [1.0]])
    probe_x = np.array([[1.0], [-1.0]])
    orig_val = ORIG_PW_CORR(probe_a, probe_x, 0, 0)
    mut_val = pairwise_corr_no_abs(probe_a, probe_x, 0, 0)
    print(f"  Probe input: negatively correlated pair")
    print(f"  Reference output : {orig_val}")
    print(f"  Mutant output    : {mut_val}")
    assert orig_val != mut_val, "Mutant did not differ from reference on probe input!"
    
    fails_m1, names_m1 = with_patch(pairwise_corr=pairwise_corr_no_abs)
    print(f"  Gate result: {fails_m1} failing tests")
    if fails_m1 == 0:
        print("  -> SURVIVED THE GATE! (Finding: test suite lacks negative-correlation witness assertion)")
    else:
        print(f"  -> KILLED by {names_m1}")

    # 3. Test Mutant D9-GM-M2
    print("\n--- Mutant D9-GM-M2: match_alarms strict upper bound (< end instead of <= end) ---")
    probe_alarms = [1200]
    probe_events = [1000]
    probe_hdet = 200
    probe_end = 2000
    orig_res = ORIG_MATCH_ALARMS(probe_alarms, probe_events, probe_hdet, probe_end)
    mut_res = match_alarms_strict_upper(probe_alarms, probe_events, probe_hdet, probe_end)
    print(f"  Probe input: alarm exactly at e + H_det (t=1200, e=1000, H_det=200)")
    print(f"  Reference output : {orig_res}")
    print(f"  Mutant output    : {mut_res}")
    assert orig_res != mut_res, "Mutant did not differ from reference on probe input!"

    fails_m2, names_m2 = with_patch(match_alarms=match_alarms_strict_upper)
    print(f"  Gate result: {fails_m2} failing tests")
    if fails_m2 == 0:
        print("  -> SURVIVED THE GATE! (Finding: test suite lacks exact upper boundary attribution test)")
    else:
        print(f"  -> KILLED by {names_m2}")

    print("\n" + "=" * 80)
    survivors = []
    if fails_m1 == 0: survivors.append("D9-GM-M1")
    if fails_m2 == 0: survivors.append("D9-GM-M2")
    print(f"Summary: {len(survivors)}/2 new mutants survived the gate: {survivors}")
    print("=" * 80)

if __name__ == "__main__":
    run_mutant_assessment()
