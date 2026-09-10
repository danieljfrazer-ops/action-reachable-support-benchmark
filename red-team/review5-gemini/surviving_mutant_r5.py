"""Round-5 surviving gate mutants against reference_generator.py and the gate test suite.

Normative tests tested: test_gate, test_generator, test_proof_theatre (all 47 tests).
Tests each candidate mutant to ensure:
1. It is observably different from the unmutated code on an explicit diagnostic probe.
2. It survives all 47 gate tests without triggering any failure.
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path
import numpy as np

GATE_DIR = Path(__file__).resolve().parents[1] / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE_DIR))

import reference_generator as rg
import contract_ref as cr
import test_gate
import test_generator
import test_proof_theatre

MODULES = (test_gate, test_generator, test_proof_theatre)


def run_all_tests() -> tuple[int, list[str]]:
    """Run all 47 gate tests and return (number_of_failures, list_of_failing_test_names)."""
    failures = []
    for mod in MODULES:
        for attr in sorted(dir(mod)):
            if attr.startswith("test_"):
                fn = getattr(mod, attr)
                try:
                    fn()
                except Exception as exc:
                    failures.append(f"{mod.__name__}.{attr}: {type(exc).__name__}: {exc}")
    return len(failures), failures


# --- Probe to ensure observable difference ---
def probe_instance():
    """Extract signatures to verify a mutant has observable operational impact."""
    # 1. Unconfounded draw
    i0 = rg.Instance({}, 0)
    o0 = i0.run(50, ep=1)["o"]
    # 2. Confounded channels
    cc = i0.confounded_channels()
    # 3. Post-event reachability and structural graph
    i1 = rg.Instance({}, 1)
    i1.apply_event(("actuator_loss", 0))
    s_obs1 = i1.S_obs()
    s_lat1 = i1.S_latent()
    # 4. Certification
    cert = i0.certify()
    return (
        np.round(o0[:10], 8).tobytes(),
        cc.tobytes(),
        s_obs1.tobytes(),
        s_lat1.tobytes(),
        cert["ok"],
        np.round(i0.A_b, 6).tobytes(),
        np.round(i1.B, 6).tobytes(),
    )


# --- Candidate Mutants ---
def mutant_unfaithful_coupling():
    """Mutant R5-GM-M1: Violates Contract B c_min faithfulness bound (|entry| >= 0.2).
    Contract B requires all nonzero entries of A_b to satisfy |entry| >= c_min = 0.2.
    The generator prunes at c_min * 0.5 = 0.1, already leaving sub-c_min entries in [0.1, 0.2).
    This mutant explicitly injects an unfaithful coupling entry A_b[0, 1] = 0.05.
    """
    orig_init = rg.Instance.__init__

    def patched_init(self, cfg, seed):
        orig_init(self, cfg, seed)
        # Inject non-faithful small coupling entry in A_b below c_min = 0.2
        self.A_b[0, 1] = 0.05

    return {"__init__": patched_init}


def mutant_actuator_loss_soft_leak():
    """Mutant R5-GM-M2: Soft actuator loss (B[:, arg] = 1e-8 instead of 0.0).
    Contract D: complete loss sets column k to 0.
    Under 1e-8, structural graph reachability (contract_ref.structural_reach_full)
    sees B[:, 0] != 0, so the actuator is considered reachable in the graph, but
    operational effect is < eps. This breaks Contract E1b (structural/operational agreement).
    """
    orig_apply = rg.Instance.apply_event

    def patched_apply_event(self, event):
        if event is not None and event[0] == "actuator_loss":
            self.B[:, event[1]] = 1e-8
        else:
            orig_apply(self, event)

    return {"apply_event": patched_apply_event}


def mutant_confounded_oracle_inversion():
    """Mutant R5-GM-M3: Oracle confounded_channels() inverted inside x block.
    Contract B / P2 defines confounded distractor channels. Inverting the oracle
    swaps confounded and unconfounded distractors for the co-primary evaluation.
    """
    def patched_confounded_channels(self):
        m = np.zeros(self.C, bool)
        for ch in range(self.C):
            j = self.assign[ch]
            if j >= 0 and self.sl["x"].start <= j < self.sl["x"].stop:
                m[ch] = not self.confounded[j - self.sl["x"].start]
        return m

    return {"confounded_channels": patched_confounded_channels}


def mutant_crn_noise_var_dropped():
    """Mutant R5-GM-M4: Common random numbers drop variable key in _noise.
    Contract B requires noise streams independent across variables.
    Dropping the variable key couples noise across all latent blocks at time t.
    """
    def patched_noise(self, var, t, shape, ep):
        return np.random.default_rng([self.seed, ep, 0, t]).normal(size=shape)

    return {"_noise": patched_noise}


def test_mutant(name: str, patch_dict: dict):
    # Baseline signature
    sig_before = probe_instance()

    # Apply patch
    saved = {}
    for attr, fn in patch_dict.items():
        saved[attr] = getattr(rg.Instance, attr)
        setattr(rg.Instance, attr, fn)

    try:
        # Check observable difference
        sig_after = probe_instance()
        is_diff = sig_before != sig_after

        # Run gate suite
        n_fails, fail_names = run_all_tests()
        survived = (n_fails == 0)
        return {
            "name": name,
            "observable_diff": is_diff,
            "n_failures": n_fails,
            "failing_tests": fail_names,
            "survived": survived,
        }
    finally:
        # Restore
        for attr, fn in saved.items():
            setattr(rg.Instance, attr, fn)


def main():
    print("Verifying baseline unmutated gate passes:")
    base_n, base_fails = run_all_tests()
    print(f"Baseline: {base_n} failures across 47 tests.")
    assert base_n == 0, "Gate must pass cleanly before mutation."

    mutants = [
        ("R5-GM-M1 (Contract B c_min faithfulness violation in A_b)", mutant_unfaithful_coupling()),
        ("R5-GM-M2 (Contract D/E1b soft actuator loss B*=1e-8)", mutant_actuator_loss_soft_leak()),
        ("R5-GM-M3 (Co-primary P2 confounded_channels inverted)", mutant_confounded_oracle_inversion()),
        ("R5-GM-M4 (Contract B CRN noise drops variable key)", mutant_crn_noise_var_dropped()),
    ]

    print("\nEvaluating Mutants against Gate:")
    results = []
    for name, patch in mutants:
        res = test_mutant(name, patch)
        status = "SURVIVED" if res["survived"] else "KILLED"
        obs = "YES" if res["observable_diff"] else "NO"
        print(f"[{status}] {name}")
        print(f"  Observable Difference: {obs} | Gate Failures: {res['n_failures']}")
        if res["failing_tests"]:
            print(f"  Failing Tests: {res['failing_tests']}")
        results.append(res)

    survivors = [r for r in results if r["survived"] and r["observable_diff"]]
    print(f"\nTotal Surviving Valid Mutants: {len(survivors)} / {len(mutants)}")
    for s in survivors:
        print(f"  * {s['name']}")


if __name__ == "__main__":
    main()
