# Summary

**Recommendation: merge the roadmaps.** Keep v2's boundary-under-change direction as the first full paper, but retain a sharply scoped hidden-volatility memory benchmark as the first engineering milestone and possible technical preprint. The original roadmap overestimated novelty; v2 then overcorrected by treating a precise conjunction of benchmark features as an unoccupied scientific problem. Dynamic body-model detection and adaptation already exist in robotics and fault diagnosis. What may survive is a standardized causal stress test combining sequential intervention, action-confounded but causally exogenous distractors, and honest detection/calibration operating curves.

The three changes I would make before starting are:

1. **Repair the estimand and causal generator.** Separate binary controllability support, the action-to-effect mapping, and sensor identity. An actuator remap may change the mapping without changing the mask. Define distractors with structural equations so an “effect copy” is not incorrectly labelled causally uncontrollable.
2. **Cut Stage 0 to the Paper 1 critical path.** In four weeks, one person should build a boundary-only vector testbed and reproduce IBD, then add sequential changes. Defer symbolic memory, Premakumar replication, the cost ledger, and heterogeneous internal actions. Stage 0 as written is not realistic.
3. **Rewrite Paper 1 and Paper 2 protocols.** Use sequential detection-delay/false-alarm curves; require genuine probabilistic outputs before applying Brier/log loss; make Bayesian baselines matched and misspecified variants; define auxiliary targets without evaluator-label leakage; replace the reintroduced-body test with counterbalanced ABA/ABC controls; and use real kill criteria that forbid post-hoc retuning of confirmation conditions.

Paper 1 by mid-February 2027 is plausible only as a reduced synthetic benchmark/preprint with a fractional experimental design. ICLR workshop and CoLLAs dates are provisional until their actual calls appear. The M5 Air is adequate for the small models, with step/operation budgets primary and thermal effects controlled.

**Single first action for Stage 0:** write and test an executable structural-causal environment contract—variables, equations, intervention semantics, horizon-specific ground truth, and invariants—before implementing any estimator.

No recommendation depends on, or should be presented as, a consciousness claim.
