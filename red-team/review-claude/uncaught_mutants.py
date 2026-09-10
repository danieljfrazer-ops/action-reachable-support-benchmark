"""Mutants that the frozen gate (c197652c0d8e846b) does NOT reject. Each prints PASSES-GATE if undetected."""
import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "executable-proofs" / "gate"))
import contract_ref as ref, test_gate

def run_gate_with(patched):
    for k, v in patched.items(): setattr(ref, k, v); setattr(test_gate, k, v)
    fails = 0
    for name in sorted(n for n in dir(test_gate) if n.startswith("test_")):
        try: getattr(test_gate, name)()
        except Exception: fails += 1
    return fails

# UM-1: an oracle that only ever labels BODY components and reports every downstream d as unreachable.
# The reference has no notion of d at all, so the gate has nothing to compare against.
A_b = np.diag([0.9, 0.9]); B = np.eye(2); C_d = np.array([[1.0, 0.0]])   # one downstream latent fed by b0
print("UM-1 downstream latent d: contract C1 says d has an action ancestor via C_d.")
print("     reference structural_reach signature:", ref.structural_reach.__code__.co_varnames[:ref.structural_reach.__code__.co_argcount],
      "-> no C_d, no d. Gate failures when d is mislabeled:", run_gate_with({}))

# UM-2: reference ignores actuator delay tau. With tau=1 and H=1, C4 says the response is zero at h=1,
# so S^latent_{t,1} must be empty; the reference returns [True, True].
print("UM-2 delay: structural_reach(A,B,H=1) with tau=1 ->", ref.structural_reach(A_b, B, 1).tolist(),
      "| open_loop_response at h=1, tau=1 ->", ref.open_loop_response(A_b, B, np.array([1.0,0.0]), 1, tau=1).tolist())
print("     C1 and C4 disagree by construction on delayed instances; gate failures:", run_gate_with({}))

# UM-3: mutants M2 and M5 in test_gate compare hard-coded arrays; replace them with anything and nothing changes.
def bogus_M2(): return np.array([True]), np.array([False])
def bogus_M5(): return np.array([False, False])
print("UM-3 placeholder mutants: gate failures after swapping M2/M5 bodies for constants:",
      run_gate_with({"mutant_M2_swap_bookkeeping_updates_labels_but_not_assignment": bogus_M2,
                     "mutant_M5_oracle_reads_event_type_instead_of_reachability": bogus_M5}))
print("     -> M2 and M5 exercise no implementation; coverage-matrix.md overstates them as covered.")
