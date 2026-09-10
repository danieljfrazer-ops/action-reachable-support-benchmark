# D-10 verdict

Date: 7 September 2026

## Decisions

**D-10.1 — Adopt with a stated change.** Freezing one executable generator is necessary because round 4 produced near-identical IBD AUCs but comparator AUCs differing by 0.20, enough to reverse the decision. Also freeze a small distribution of generator configurations or seeds, not a single realised instance: agreement on one draw would establish implementation agreement but not robustness across admissible instances.

**D-10.2 — Adopt with a stated change.** The delay-aware, standardised, multi-horizon comparator directly repairs all three convergent defects: delay misalignment, unit-sensitive ridge, and downstream channels scored near zero by construction. Define its multi-horizon loading and training split mathematically before simulation, and retain both current and corrected comparator results as an audit trail rather than silently replacing the failed baseline.

**D-10.3 — Adopt with a stated change.** A competence floor is more coherent than requiring equivalence between methods when the passive arm was structurally weak. Apply the `AUC ≥ 0.85` floor per required absent-confounder environment and distractor level, with uncertainty, rather than only after aggregation; otherwise weak cells can be hidden by easy ones.

**D-10.4 — Adopt.** Balanced pre-randomised `(actuator, sign)` blocks remove the observed 13% actuator-starvation mechanism while preserving independence from state. Returning an eligibility mask also prevents insufficient evidence from being encoded as support absence.

**D-10.5 — Adopt with a stated change.** Dropping offsets 10 and 50 is justified because the relevant windows are overwhelmingly pre-event. Keep 200 as a labelled transition-window outcome, not an equally mature post-change estimate, because the evidence says its IBD window is still 60% pre-event.

**D-10.6 — Adopt.** Excluding copies prevents multiplicity from changing the primary AUC without changing the causal object. Acceptance fixtures should retain noisy copies, using distributional tolerances rather than trace equality, as round 4 showed additive observation noise makes exact equality impossible.

**D-10.7 — Adopt with a stated change.** Instance-level clustering is essential because the three round-4 implementations effectively sampled different benchmarks. Interpret “up to 30 seeds per instance” as episode seeds, predefine the instance-by-episode hierarchy, and base power on the number of independent instances; more episodes cannot substitute for too few generator draws.

## Questions

**(a)** The proposed exit condition is necessary but incomplete. Require agreement to Monte Carlo error across several frozen generator draws plus successful specification-conformance tests; one generator realisation can conceal instance sensitivity even when all implementations agree.

**(b)** **Opinion:** either fallback leaves a publishable benchmark-and-findings paper if declared before confirmation. I prefer the negative result that a correctly specified passive detector is adequate, because it is broader and harder to dismiss than narrowing the claim post hoc to indirect/downstream channels; the latter is preferable only if predeclared channel-stratified evidence clearly supports it.

**(c)** Yes. D-10.2 changes the comparator and therefore the primary contrast, D-10.3 changes a confirmatory decision rule, D-10.4 changes the intervention schedule, D-10.5 changes a co-primary's measurement times, and D-10.7 changes the sampling and inferential unit. Those changes should be frozen only after the proposed cross-model execution round; D-10.1 and D-10.6 mainly remove ambiguity but should travel in the same freeze for consistency.
