# Roadmap v4.1: amendments to roadmap-v4 after the first parallel adjudicated review

Date: 6 September 2026. Applies findings with two-of-three validity or executable evidence (see `review-claude/adjudication.md`, `review-codex/adjudication.md`, `review-gemini/adjudication.md`). `roadmap-v4.md` stands except as amended. This file plus `stage-0a-contract-v3.1.md`, `interface-spec-v2.md`, `confirmation-design.csv` and `executable-proofs/gate/` form frozen version 2.

## E1. Interaction estimand and gate for the 2×2 diagnostic (CX-07)

Define Δ(regime, confounder) as the primary effect (HPDT difference, contract G) in each cell. The interaction I = [Δ(R1, present) − Δ(R1, absent)] − [Δ(R0, present) − Δ(R0, absent)]. R1 superiority is claimed only if, in addition to the R1 rule, the lower bound of I is > 0 on both SCM families (sign gate; a minimum interaction effect of δ/2 = 10 steps is reported descriptively). This separates the confounding contribution from generic misspecification.

## E2. Aggregation over primary rows (CX-11)

The primary estimand per (environment, regime, confounder) is the equal-weight mean over distractor levels and, for SCMs, over delays, of per-seed paired differences (CUSUM minus IBD, same seed, same cell). Worst-case over distractor levels is reported descriptively. Frozen as `aggregate_primary()` in the gate before the pilot, with a worked CSV example.

## E3. Inference with few clusters (CX-12)

Ten seeds are the independent clusters. Primary intervals are seed-level paired-difference intervals with a t-distribution (9 degrees of freedom); a wild cluster bootstrap is the secondary check. A simulation coverage check under the frozen design runs in the pilot; if coverage of the primary interval is below 93 percent, seeds increase to 20 before confirmation.

## E4. Effect sizes frozen now (CX-16)

δ = 20 and δ0 = 10 HPDT steps are frozen as of this file. Pilot variance may change seed count only. Any later change to δ requires an external domain argument and the original thresholds are still reported.

## E5. Decision rule wording (CL-10)

"Sign holds on both T2 environments" means: point estimate > 0 and lower bound > −δ0 on each.

## E6. Baseline roles and descriptive matrix (CX-10)

Confirmatory pair: sequential IBD versus channel-agnostic CUSUM. Descriptive matrix: random, temporal correlation, forward-model residual on the same cells at 3 seeds, frozen in `confirmation-design.csv` with `role=descriptive`. Appendix references: oracle-coordinate CUSUM, Bayesian model-informed.

## E7. Judgment calls recorded for Daniel, with defaults adopted

- CL-6: co-primary outcome = confounded-channel false support (mean p_c on distractor channels at fixed offsets). Default: adopted.
- GM-7: confounded fraction of distractor channels f_conf. Default: 0.5.

## E8. Interface (CX-03, CX-13, CX-17, CL-11)

`interface-spec-v2.md` replaces v1: transition-based estimator update with applied action and probe marker; `probe(actions[steps, K])`; Gymnasium-style `step` return with reward, terminated, truncated, info to the evaluator; evaluator-only snapshot-and-branch scoring API with no-mutation test.

## E9. Environment reproducibility (CX-02, GM-9)

The gate command is defined from a clean checkout with the documented venv; `run_gate.py` exits 2 with instructions if dependencies are missing; requirements pinned in `requirements.txt`. Phase 0R creates the venv; nothing is installed into system Pythons.

## E10. Phase 0R scope update

Phase 0R now also closes: full-latent reachability with delay (done), K7/K10 (done), mutation run with all reviewer mutants (done, 8/8 killed), aggregation function, coverage-check simulation script, interface v2 acceptance stubs. Uncovered normative groups remaining for 0A: M2 to M6, C2 certification, family N boundedness, E4 determinism, E5 isolation, E6 black-box suite, T-OOB.

## Unchanged

D1 to D13; phases and dates in v4 section 3 (subject to the runtime pilot); Paper 2 design; workflow; risks.
