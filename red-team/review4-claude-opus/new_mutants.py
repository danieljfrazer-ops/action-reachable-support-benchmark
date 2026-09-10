"""Round-4 fresh-context mutants against executable-proofs/gate/ (frozen 442cc4b7da691ca0).

Modelled on `executable-proofs/gate/mutants.py`.  Nothing in the frozen tree is modified: this file
imports the gate modules, monkey-patches `contract_ref` in memory exactly as `mutants.py` does, and
runs the same 34 assertion tests.  A mutant that produces 0 failing tests SURVIVES the gate.

Each mutant is also checked against the gate's own distinctness guard (`mutants.PROBES`), so the
report says whether the mutant would even be admitted to the registered suite as it stands.

Run: /Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3 new_mutants.py
"""
import pathlib
import sys

GATE = pathlib.Path(__file__).resolve().parent.parent / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))

import numpy as np                                    # noqa: E402
import contract_ref as ref                            # noqa: E402
import test_gate                                      # noqa: E402
import test_proof_theatre                             # noqa: E402
import contextlib, importlib.util, io                 # noqa: E402
# mutants.py is a script that ends in sys.exit(); load it as a module and swallow that.
_spec = importlib.util.spec_from_file_location("gate_mutants", GATE / "mutants.py")
gate_mutants = importlib.util.module_from_spec(_spec)
sys.modules["gate_mutants"] = gate_mutants
try:
    with contextlib.redirect_stdout(io.StringIO()):
        _spec.loader.exec_module(gate_mutants)
except SystemExit:
    pass

ORIG = {k: getattr(ref, k) for k in dir(ref) if callable(getattr(ref, k)) and not k.startswith("_")}


def failures():
    """Exactly run_gate.py's test set: test_gate + test_proof_theatre."""
    out = []
    for mod in (test_gate, test_proof_theatre):
        for name in sorted(t for t in dir(mod) if t.startswith("test_")):
            try:
                getattr(mod, name)()
            except Exception:
                out.append(f"{mod.__name__}.{name}")
    return out


def with_patch(**kw):
    saved = {k: (getattr(ref, k), getattr(test_gate, k, None)) for k in kw}
    for k, v in kw.items():
        setattr(ref, k, v); setattr(test_gate, k, v)
    try:
        return failures()
    finally:
        for k, (a, b) in saved.items():
            setattr(ref, k, a); setattr(test_gate, k, b)


# ---------------------------------------------------------------------------------------------
# R4-M1.  contract sec G: "Detection = FIRST counted alarm with event_t < alarm_t <= event_t+H_det".
#         This mutant attributes the LAST qualifying alarm instead of the first.  Every delay it
#         reports is >= the true one, so HPDT is silently inflated for the arm that alarms in
#         bursts (both confirmatory arms emit raw exceedances and the harness applies p and r,
#         so several counted alarms inside one 200-step H_det window are routine).
# ---------------------------------------------------------------------------------------------
def ma_last_in_window(alarm_times, event_times, H_det, episode_end):
    ev = sorted(event_times); al = sorted(alarm_times); used = set(); D = []; Oc = []
    for i, e in enumerate(ev):
        nxt = ev[i + 1] if i + 1 < len(ev) else episode_end
        end = min(e + H_det, nxt, episode_end); hit = None
        for t in al:
            if e < t <= end:
                hit = t                                        # no break: keeps the LAST match
        if hit is None:
            D.append(H_det); Oc.append("missed")
        else:
            used.add(hit); D.append(hit - e); Oc.append("detected")
    return D, Oc, [t for t in al if t not in used]


# ---------------------------------------------------------------------------------------------
# R4-M2.  contract sec G / v4.1 E2 / v4.6 J1: the primary cell key is
#         (environment, regime, confounder, distractor_level, delay).  `aggregate_primary` keys on
#         (seed, level, delay) only, so rows from different environments / regimes / confounder
#         arms collide and the LAST row silently wins.  This mutant keeps the FIRST row instead.
#         On well-formed input the two agree; on the input the contract actually produces they
#         disagree, and neither is right.  Surviving proves the collision is untested.
# ---------------------------------------------------------------------------------------------
def ap_first_wins(rows, est_a="cusum_channel_agnostic", est_b="seq_ibd"):
    from collections import defaultdict
    cell = defaultdict(dict)
    for r in rows:
        d = cell[(r["seed"], r["level"], r["delay"])]
        if r["estimator"] not in d:                            # FIRST wins (original: last wins)
            d[r["estimator"]] = float(r["hpdt"])
    per_seed = defaultdict(list); dropped = 0
    for _, v in cell.items():
        if est_a in v and est_b in v:
            per_seed[_[0]].append(v[est_a] - v[est_b])
        else:
            dropped += 1
    return {s: float(np.mean(v)) for s, v in per_seed.items()}, dropped


# ---------------------------------------------------------------------------------------------
# R4-M3.  contract sec C2/C3: e_j is a magnitude (a max of norms), so it is >= 0 by construction,
#         and sec C3 tests |gain_c| * e_j > eps.  This mutant drops the abs() on gain and instead
#         takes abs() of the whole product.  Identical whenever e_j >= 0 -- which the reference
#         oracle guarantees -- but it silently changes the label whenever a caller passes a signed
#         effect (e.g. a finite-difference response, which E1b's second derivation produces).
#         Registered to pin "gain magnitude, effect magnitude" as two separate requirements.
# ---------------------------------------------------------------------------------------------
def sobs_abs_of_product(latent_effect, assign, gain, avail, eps):
    C = len(assign); out = np.zeros(C, bool)
    for c in range(C):
        j = int(assign[c])
        if j < 0 or not avail[c]:
            continue
        out[c] = abs(float(gain[c]) * float(latent_effect[j])) > eps
    return out


MUTANTS = {
    "R4-M1 match_alarms attributes the LAST alarm in the window, not the first":
        dict(match_alarms=ma_last_in_window),
    "R4-M2 aggregate_primary keeps the FIRST colliding row instead of the last":
        dict(aggregate_primary=ap_first_wins),
    "R4-M3 s_obs_eps takes |gain * e| instead of |gain| * e":
        dict(s_obs_eps=sobs_abs_of_product),
}

# Witness inputs on which each mutant provably differs from the original (these are the inputs the
# gate's own PROBES table is missing; the fix for each finding is to add them).
WITNESS = {
    "R4-M1 match_alarms attributes the LAST alarm in the window, not the first":
        ("match_alarms", ([1010, 1100, 1180], [1000], 200, 2000)),
    "R4-M2 aggregate_primary keeps the FIRST colliding row instead of the last":
        ("aggregate_primary", ([dict(seed=0, level=10, delay=0, estimator="cusum_channel_agnostic", hpdt=60.0),
                                dict(seed=0, level=10, delay=0, estimator="seq_ibd", hpdt=40.0),
                                dict(seed=0, level=10, delay=0, estimator="cusum_channel_agnostic", hpdt=150.0),
                                dict(seed=0, level=10, delay=0, estimator="seq_ibd", hpdt=50.0)],)),
    "R4-M3 s_obs_eps takes |gain * e| instead of |gain| * e":
        ("s_obs_eps", (np.array([-1.0]), np.array([0]), np.array([1.0]), np.array([True]), 0.1)),
}


def main():
    base = failures()
    assert not base, f"gate is not clean before mutation: {base}"
    n_tests = sum(len([t for t in dir(m) if t.startswith("test_")])
                  for m in (test_gate, test_proof_theatre))
    print(f"gate clean: 0 failing tests of {n_tests} (run_gate.py's full set)\n")
    survivors = []
    for name, patch in MUTANTS.items():
        fn_name, args = WITNESS[name]
        o = ORIG[fn_name](*args)
        m = list(patch.values())[0](*args)
        differs_on_witness = repr(o) != repr(m)
        # would the gate's own distinctness guard admit this mutant today?
        admitted = any(gate_mutants.differs(k, v) for k, v in patch.items())
        f = with_patch(**patch)
        status = "SURVIVED" if not f else "KILLED  "
        if not f:
            survivors.append(name)
        print(f"{status} {name}")
        print(f"          failing gate tests: {len(f)}{'  ' + str(f) if f else ''}")
        print(f"          differs from the original on the witness input: {differs_on_witness}")
        print(f"          original(witness) = {o}")
        print(f"          mutant  (witness) = {m}")
        print(f"          admitted by mutants.py's existing PROBES distinctness guard: {admitted}"
              f"{'   <-- PROBES needs the witness input above' if not admitted else ''}\n")
    print(f"{len(survivors)}/{len(MUTANTS)} mutants SURVIVED the frozen gate:")
    for s in survivors:
        print(f"  - {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
