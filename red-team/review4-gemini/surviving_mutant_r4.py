"""Surviving mutant for Round 4 gate review.
Target: contract_ref.build_adjacency (Contract B SCM DAG specification).

Claim attacked:
Contract §B and §C1 specify that exogenous world latents w and distractor latents x
are causally independent exogenous processes (w has no action or distractor parents;
x has only u and self parents). There is NO causal path w -> x in the SCM.

In contract_ref.build_adjacency, directed edge j -> i exists iff coefficient (i, j)
is nonzero. However, the gate's test test_C1_build_adjacency_keeps_w_and_x_self_edges
only checks self-edges (adj[w, w] and adj[x, x]) and absence of action paths from b
(adj[w, b] and adj[x, b]). It never checks cross-edges between exogenous latents (adj[x, w]).
Furthermore, because w and x have no incoming edges from b, structural_reach_full
(which starts its reachability frontier at b) never traverses any edge out of w.

Therefore, an illegal cross-edge w -> x can be inserted into the adjacency matrix,
violating the SCM DAG specification of Contract §B, and all 34 gate tests pass
with 0 failures. This mutant differs on PROBES['build_adjacency'][2] and survives
the gate.
"""

import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "executable-proofs" / "gate"))
import contract_ref as ref
import test_gate

# Capture originals
O = {k: getattr(ref, k) for k in ("open_loop_response", "jacobian_piecewise", "structural_reach", "structural_reach_full",
                                  "build_adjacency", "s_obs_eps", "max_pairwise_corr", "hpdt", "check_spacing",
                                  "count_alarms", "match_alarms", "aggregate_primary", "pairwise_corr")}

def adj_leak_w_into_x(A_b, C_d=None, A_d=None, A_w=None, A_x=None):
    adj, sl = O["build_adjacency"](A_b, C_d, A_d, A_w, A_x)
    if A_w is not None and A_x is not None:
        # Illegally leak world latent w into distractor latent x
        adj[sl["x"], sl["w"]] = True
    return adj, sl

def run_verification():
    # 1. Verify that the mutant differs on at least one probe in mutants.PROBES
    mutants_code = open(pathlib.Path(__file__).parent.parent / "executable-proofs" / "gate" / "mutants.py").read()
    loc = {}
    exec("import numpy as np\n" + mutants_code[mutants_code.index("A_ch ="):mutants_code.index("def _eq")], loc)
    PROBES = loc["PROBES"]

    def _eq(a, b):
        try: a, b = np.asarray(a, float), np.asarray(b, float)
        except (TypeError, ValueError): return a == b
        if a.shape != b.shape: return False
        return bool(np.all((a == b) | (np.isnan(a) & np.isnan(b))))

    def same(a, b):
        if isinstance(a, tuple) and isinstance(b, tuple):
            return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
        return _eq(a, b)

    differs = any(not same(adj_leak_w_into_x(*args), O["build_adjacency"](*args))
                  for args in PROBES.get("build_adjacency", []))
    assert differs, "Mutant failed OP-2 guard: did not differ on any probe!"
    print("OP-2 Guard Passed: Mutant differs on probe inputs.")

    # 2. Verify that all 34 gate tests pass with the patch applied
    saved_ref = getattr(ref, "build_adjacency")
    saved_test = getattr(test_gate, "build_adjacency", None)
    setattr(ref, "build_adjacency", adj_leak_w_into_x)
    setattr(test_gate, "build_adjacency", adj_leak_w_into_x)
    
    failures = 0
    failing_names = []
    for name in sorted(t for t in dir(test_gate) if t.startswith("test_")):
        try:
            getattr(test_gate, name)()
        except Exception as e:
            failures += 1
            failing_names.append(name)
            
    setattr(ref, "build_adjacency", saved_ref)
    setattr(test_gate, "build_adjacency", saved_test)

    print(f"Gate test results under mutant: {34 - failures}/34 passed, {failures} failed.")
    if failures == 0:
        print("CONFIRMED: Mutant SURVIVED the gate! (0 failing tests)")
    else:
        print(f"FAILED: Mutant was killed by: {failing_names}")
    return failures == 0

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
