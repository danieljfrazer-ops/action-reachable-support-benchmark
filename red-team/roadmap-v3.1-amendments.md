# Roadmap v3.1: amendments to roadmap-v3 after the Codex final critique

Date: 6 September 2026. `roadmap-v3.md` stands except where amended below. Amendment IDs A1 to A9 map to the Codex findings listed in `synthesis-final.md`.

## A1. Timings (F13)

| Phase | v3 | v3.1 | Note |
|---|---|---|---|
| 0A | 4 to 7 days | 1.5 to 2 weeks, to ~24 Sep 2026 | includes one repair cycle and Codex review of the built package |
| 0B | 1 to 2 weeks | 2 to 3 weeks, to ~15 Oct | three Bayesian variants, learned self-model, sequential metrics, calibrator |
| S | 2 weeks parallel with 0B | starts after the 0A gate; 2 weeks build and run, 1 week write-up, to ~15 Oct | reduced scope (A7); publish only if the completeness gate is met |
| Paper 1 pilot | | ~15 to 31 Oct | variance estimation only |
| Paper 1 confirmation | | Nov, with a 25 to 35 percent rerun reserve | |
| Paper 1 write-up and arXiv | late Nov to mid-Dec | mid-Dec 2026 to mid-Jan 2027 | February 2027 remains the planning target for any venue |

Review queues are explicit: Daniel reviews at most one phase gate and one draft per week. During overlapping 0B and S both agents are builders, so cross-review is scheduled at the 0B and S gates rather than continuously.

## A2. Locked decision D8 (F3)

Paper 1's primary claim concerns the observation-channel operational support S^obs,ε and typed change detection for all three targets. Estimation of the response R and the observation map P is secondary. Every estimator emits every output in contract v2 section F; a declared constant is permitted and is scored. The title and abstract do not use "self-boundary" in the technical claim; the term appears in the motivation only.

## A3. Positioning (F15)

Contribution type: benchmark and failure map for sequential estimation of changing controllability under action-correlated exogenous distractors. Two structurally different dynamics families (L and N in contract v2). Executable contract, golden cases and mutants released with the paper. Negative results reported.

## A4. Frozen confirmation design (F5, F16)

Frozen before the pilot runs, and recorded in the ledger with a hash:

- **Primary method pair:** sequential IBD (randomised-probe two-sample tests with FDR, re-probed on a declared schedule) versus the forward-model residual detector. Both are frozen algorithms with one tuning budget each.
- **Primary target and event family:** S^obs,ε change under actuator-loss events, in the active-probing regime with equal probe budget, under exogenous action-correlated distractors at the middle distractor level.
- **Primary scalar estimand:** Δ = log ARL_int − log ARL_obs at matched median detection delay, where the matching delay is fixed in advance as the smaller estimator's median delay at its declared default threshold on the pilot, and both operating curves are interpolated to that delay.
- **Smallest effect of interest:** δ = ln 2. Rationale: a doubling of the run length to false alarm at equal delay is the smallest improvement that would change a practitioner's choice of estimator; smaller differences are dominated by tuning. Marked provisional until the pilot variance is known; the value may be lowered only before confirmation and only with a written reason.
- **Run matrix:** two parts, published as CSV before the pilot. Part 1, primary contrast: full sub-grid {2 methods} × {actuator loss} × {3 distractor levels} × {2 delays} × {active regime} × {2 families} × 10 seeds = 240 runs. Part 2, exploratory response surface: a space-filling (Latin-hypercube) subset of 120 cells from the 540-cell grid, balanced across estimator × target, estimator × distractor and estimator × family margins, at 3 seeds per family = 720 runs. Part 2 is descriptive with multiple-comparison control and no confirmatory claim.
- **Hypotheses:** H1 (confirmatory) is the primary contrast. H2 (descriptive) is the response surface, with "no meaningful phase boundary" allowed. H3 (descriptive) reports excess proper score relative to the correctly specified reference; no requirement that all methods degrade.
- **Pilot use:** variance and sample-size estimation only; no selection of contrast, operating point or threshold from pilot outcomes.

## A5. Decision rules (F6)

Δ is signed so that positive favours the interventional estimator. With 95 percent intervals clustered by seed:
- **Superiority:** lower bound > δ on both families.
- **Futility:** upper bound < δ on either family (the claim requires both).
- **Inconclusive:** otherwise; reported as a benchmark result with descriptive findings and no efficacy claim.
- **Positive-control gate** (IBD detects a static support; random has no advantage; correlation shows false alarms under the confound) runs before confirmation and is not part of the confirmatory decision. Failure stops the phase.

## A6. Independent ground truth and change control (F4, F7, F14)

- Two label derivations must agree (contract v2 E1). The confirmation evaluator's hash is stored by Daniel outside the writable experiment tree.
- Golden numerical cases from contract v2 section K are committed as tests; a reference metric script, separate from the pipeline, recomputes every primary metric on one confirmation cell.
- Hash set: source, configuration schema, environment lockfile, generator version, metric code. Manifests are append-only with atomic completion markers; failed runs and NaNs are recorded as failed rows.
- Change classification: a semantic change to generator, oracle, metric or baseline reruns all affected cells; presentation-only changes do not. Daniel approves any exception before confirmation summaries are unblinded.

## A7. Phase S reduced scope (F8, F17)

- Families: recurrent state; episodic key-value store; fast weights (TTT-linear style). Singletons plus one predeclared pair (recurrent + episodic).
- Budgets: two physical budgets, defined as total allocated bytes, with bytes read and written and update and inference operations reported; effective state-size reported only where the operator definition applies.
- Streams: 100k events; Family A for development; Family B (bursty) held out and hashed.
- Seeds: 3 development, 5 confirmation.
- Baselines: surprise-only routing; empirical-hazard heuristic; Bayesian hazard-learning router; hazard-informed reference (not "oracle").
- Questions: the four predeclared questions in v3 section 5, answered for three families.
- Gate to publish: all confirmation cells complete, matched-budget accounting audited by the non-building agent, and a final prior-art pass documented. If not met by day 21, the output is an internal shakedown report and the memory question returns in Paper 3.
- Contribution type when published: small empirical methods contribution, conditional on the documented prior-art pass.

## A8. Reintroduction controls (F12)

ABA and ABC with equal dwell times and transition counts; A′ (unseen, structurally matched to A) as a third condition; declared resets of optimiser, detector and recurrent state as ablations; explicit-library retrieval separated from parameter savings; recognition latency reported separately from relearning slope.

## A9. Related-work discipline (F15, C20)

Every 2026 preprint cited is labelled with its first-posted date and status. The claim that no prior work supplies the exact benchmark or table is stated as the result of a bounded search on a given date, never as a systematic-review conclusion.

## Unchanged

Phases 2 to 4, the capability framing, the execution workflow (with A6 added), the risk table, and decisions D1 to D7.
