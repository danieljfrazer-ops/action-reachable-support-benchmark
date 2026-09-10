# Roadmap v3 and phase plan (pre-execution)

**Date:** 6 September 2026. **Status:** consolidated plan for execution, superseding `roadmap-v2.md` (kept for the record). Incorporates the red team (`findings.md`), round-2 research, the Codex response (`codex-response/`), the synthesis, the timing revision, and Daniel's decisions.

## 0. Locked decisions

| # | Decision | Choice |
|---|---|---|
| D1 | Memory shakedown | Yes, strict two-week box after Phase 0A, in parallel with Phase 0B; technical note regardless of outcome; no learned router |
| D2 | Consciousness in papers | One sentence in the motivation stating what is not claimed; nowhere else |
| D3 | Observations for Paper 1 | Fixed-dimensionality vectors, padded inactive channels when the body changes |
| D4 | Execution model | Claude Code (Opus 5) and Codex (GPT-5.6) implement; each phase is built by one agent and red-teamed by the other before Daniel signs off; Daniel decides estimands, reviews results, writes the argument |
| D5 | Hardware | 32 GB M5 MacBook Air; step and operation budgets primary; wall-clock secondary and labelled; randomised interleaved runs; thermal pressure and throughput logged |
| D6 | Publication | arXiv first for every output; venue submission only against a live call; contribution type stated in every abstract |
| D7 | Claims discipline | Benchmark, finding, negative result, or method, stated explicitly; a method claim requires beating the best matched model-based and trivial baselines on held-out families |

## 1. Programme in one paragraph

An agent that runs continuously must track what it controls, how its actions map to effects, and which of its sensors mean what, while all three can change without warning and while distractors correlate with its actions. It must also store facts that change at hidden rates and decide when to spend internal compute. The programme builds a small, fully ground-truthed testbed for these questions and publishes a sequence of benchmark and empirical-finding papers, each scoped to one measured construct, with functional self-modeling as the connecting theme. No paper claims self-awareness.

## 2. Phase overview

| Phase | Output | Agentic estimate | Cumulative (from 8 Sep 2026) |
|---|---|---|---|
| 0A | Causal environment contract, generator, invariants, four baselines, IBD reproduction | 4 to 7 days | ~15 Sep |
| 0B | Sequential change protocol, detection curves, calibrator split, Bayesian baseline variants | 1 to 2 weeks | ~29 Sep |
| S | Memory shakedown technical note (parallel with 0B) | 2 weeks box + 3 to 5 days write-up | ~6 Oct |
| 1 | Paper 1: changing-boundary stress test | 6 to 9 weeks after 0B | arXiv late Nov to mid-Dec 2026 |
| 2 | Paper 2: auxiliary self-prediction and quickest re-identification | 6 to 10 weeks after Paper 1 | arXiv Feb to Mar 2027 |
| 3 | Paper 3: fast-self versus slow-world memory | 8 to 12 weeks | mid-2027 |
| 4 | Scheduling component and integrated agent report | 2027 to 2028 | |

Reserve: four weeks unallocated before the first external deadline. If Phase 0A slips past 22 September, Phase S is cut, not Paper 1.

## 3. Phase 0A: environment contract (build: Claude; red team: Codex)

**Objective.** An executable structural-causal environment whose ground truth is exact and whose invariants are tests. Specification: `stage-0a-contract-draft.md`, sections A to J.

**Deliverables.**
1. Python package (numpy) with: action channel; body state driven by a mapping M_t with delay; exogenous world state; downstream action effects that are not body; exogenous action-correlated distractors driven by a shared cause that also shapes the default policy; copied and permuted sensors; observation identity P_t; padded fixed dimensionality.
2. Three ground-truth targets exposed only to the evaluator: controllability support S_t per horizon, mapping M_t, identity P_t. The estimand scored in Paper 1 (direct controllability versus causal reachability versus body membership) declared in the README, with both reachability and body-membership supports logged.
3. Seven invariants as pytest tests (contract section E), including the interface test that evaluator fields are unreadable from the agent API.
4. Baselines as frozen algorithms with one tuning budget each: random; temporal correlation (declared lag set, window); forward-model residual (declared architecture, retraining schedule); IBD as published, reproduced to its published qualitative checks.
5. Run ledger writer: JSONL with code hash, config hash, seed, budgets, thermal pressure, throughput, metrics, outcome, including crashes.
6. Two dynamics families: linear, and one nonlinear (saturating).

**Gate.** All invariants pass on both families; IBD reproduction matches its published ordering against correlation and forward-model baselines on the static-boundary case; determinism byte-identical across two machines or two runs; Codex red team finds no high-severity issue. **Kill/redirect:** if the estimand cannot be made consistent (contract section C) within 7 days, stop and resolve it with Daniel before any further code.

## 4. Phase 0B: sequential change protocol (build: Codex; red team: Claude)

**Objective.** Turn the static environment into a sequential detection benchmark.

**Deliverables.**
1. Change events tagged by target: remap or gain (M only), actuator loss (S and M), sensor dropout (P, observed S), sensor swap (P only), morphology change (S, M, padding).
2. Schedules: single unannounced change; ABA and ABC with counterbalanced order and dwell; Poisson and bursty as held-out families, generated and hashed before development ends.
3. Sequential metrics with definitions frozen: detection delay with persistence rule and censoring; average run length to false alarm; support F1 at fixed offsets via out-of-band probes; mapping Frobenius error; per-dimension Brier and log loss with reliability plots in fixed transition windows; ECE secondary with fixed bins; probes used, samples, operations, task regret to detection.
4. Calibrator: every estimator emits a probability from a declared model or a calibrator fitted on a separate split; passage through the calibrator logged.
5. Bayesian change-point detector in three variants: correctly specified (labelled model-informed reference), misspecified scalar residual, nonparametric.
6. Learned self-model with residual monitoring (one frozen architecture).
7. Intervention regimes: passive policy, shared exploration data, active probing; declared whether intervention data may train the controller.

**Gate.** Positive control: IBD with re-probing detects an S change; negative control: random has no detection advantage; correlation-based estimator shows false alarms under exogenous action-correlated distractors (the confound is real in the environment). Claude red team finds no high-severity issue.

## 5. Phase S: memory shakedown (build: Claude; red team: Codex; two-week box, parallel with 0B)

**Objective.** A budget-matched comparison of memory families under hidden per-item volatility, using `r1-protocol-hardening.md` in full. Contribution type: benchmark and negative results. No learned router.

**Deliverables.**
1. Symbolic stream generator: entities with hidden hazard; stable, fast, transient anomaly, reversal, irrelevant surprise; delayed probe queries. Family A development; Families B (bursty) and C (correlated entities, heavy-tailed delays) held out and hashed.
2. Memory families at matched **total** budget with effective state-size as the budget measure: local attention; recurrent state; fast weights (TTT-linear style); episodic key-value store; slow weights with online updates. Single, pair, and leave-one-out configurations.
3. Baselines: surprise-only routing; fixed multi-timescale routing; empirical-hazard heuristic (1 / mean inter-change interval, TTL eviction); Bayesian hazard-learning router (Wilson, Nassar & Gold 2010); hazard-informed and query-informed reference policies (not "oracle").
4. Metrics: four-way outcome (correct, stale, wrong-other, abstain); probe-based adaptation lag; retention at log-spaced delays with minimum bin sizes; Brier and log loss; budgets; wall-clock secondary.
5. Four predeclared questions: does the episodic store dominate at matched write cost; do fast weights reduce or relocate forgetting; is surprise-based writing wrong under transient anomalies; does the empirical-hazard heuristic match anything better.

**Gate and stop.** Box ends at 14 days of build and run regardless of state; write-up covers whatever is complete, with incomplete cells reported as incomplete. Output: technical note on arXiv, contribution type stated.

## 6. Phase 1: Paper 1 (build: alternating per experiment; red team: the other agent)

**Working title.** A standardised stress test for changing self-boundaries: sequential estimation of controllability, action-effect mapping and sensor identity under action-correlated distractors.

**Contribution type.** Benchmark plus empirical findings. No method claim.

**Related work to be cited as occupying the parent problem.** IBD (static interventional mask); Gold & Scassellati 2006; Sturm, Plagemann & Burgard 2009 and iCub online body-schema adaptation (probabilistic body schema monitored and adapted after failure); Bongard, Zykov & Lipson 2006; Chen et al. 2022; Hu & Lipson 2025; online Bayesian change-point detection for articulated motion (ICRA 2015); actuator and sensor fault detection and isolation with detection and false-alarm characterisation; MORPHIN and non-stationary RL. The surviving gap, stated precisely: sequential, action-intervention-based estimation of three separable targets under causally non-responsive action-confounded observations, scored with a common quickest-detection and probabilistic protocol.

**Design.**
- Pilot (weeks 1 to 2): full grid at 3 seeds on Family A to estimate effect sizes; choose **one primary contrast** and one operating point by a simulation-based power study; freeze a pilot-only tuning region.
- Confirmation (weeks 3 to 4): fractional factorial over estimator (6), change type (5), distractor count (3 levels), delay (2), regime (3); 10 seeds; both dynamics families; held-out schedules B and C. Smallest effect of interest predeclared for the primary contrast.
- Hypotheses. H1 (primary): under exogenous action-correlated distractors, interventional estimators achieve a lower false-alarm rate at matched detection delay than observational estimators, by at least the smallest effect of interest. H2: no estimator dominates across change types; reported as a multiple-comparison-controlled response surface, with "no meaningful phase boundary" an allowed outcome. H3: calibration in the transition window degrades for all estimators by a predeclared minimum, and the correctly specified change-point reference is the best calibrated.
- Reintroduction: ABA versus ABC, counterbalanced; explicit-library retrieval separated from parameter savings by ablation; identification and adaptation measured separately.

**Kill and redirect.** Kill if positive controls fail on the confirmation grid. Redirect to "benchmark and null" if the primary contrast's confidence interval excludes the smallest effect of interest on both families. No re-tuning of confirmation conditions after the pilot freeze.

**Write-up (weeks 5 to 7).** Novelty re-check immediately before posting; the non-building agent red-teams the draft; Daniel writes the argument. Figures: detection-delay versus false-alarm curves per change type; reliability plots in transition windows; Pareto over regret, probes, compute.

**Venue.** arXiv. Then whichever of CoLLAs 2027, an ICLR 2027 workshop on continual or embodied learning, or a robotics learning workshop has a live call that matches; none is assumed.

## 7. Phase 2: Paper 2

**Question (narrowed).** Does temporally predictive latent dynamics as an auxiliary objective, beyond an equal-compute forward-model control, improve quickest re-identification of a changed causal support, and at what cost to task performance?

**Design.** Conditions: no auxiliary; future-latent self-prediction with stop-gradient and anti-collapse control (Voelcker et al. 2024 as the reference formulation); error forecasting head (defined on next observation, separated from state prediction); mask head under **declared privileged supervision**, reported as a sample-efficiency probe, not as a method; matched non-self auxiliary control. Equal parameters and compute. Gate: Premakumar weight-narrowing reproduction at small scale, placed immediately before this paper.

**Hypotheses.** H1: latent self-prediction reduces detection delay for S changes relative to the equal-compute forward-model control. H2: it does not improve M estimation. H3 (expected null): hidden-state self-prediction narrows weights but does not improve adaptation. Contribution type: empirical finding, plausibly negative.

**Related work to be cited.** Premakumar 2024; Tomaszewski 2026 (single-author preprint, marked as such); Voelcker 2024; Fu et al. CoRL 2025; Binder 2024 (behavioural self-prediction in LLMs, distinguished from this setting).

## 8. Phase 3: Paper 3

Fast-self versus slow-world memory under hidden volatility, using Phase S as its baseline table and the Phase 0 environment with symbolic world facts added. Question: when self mappings and world facts change at different hidden rates, does timescale-separated storage improve the retention and adaptation frontier at matched total budget, and where is the crossover? A routing method only if it beats the Bayesian hazard-learning and empirical-hazard baselines on held-out families. This is the only phase where an AutoResearch-style or ShinkaEvolve-style loop is attached, to screen candidate routing modules against the frozen evaluator with step budgets.

## 9. Phase 4: scheduling and integration

Metareasoning over heterogeneous internal actions (retrieve, learn, consolidate, roll out) with the cost ledger live. Baselines: fixed schedules, surprise gates, Muppidi et al. 2026 gating policy, Jensen et al. 2024 rollout policy. Publish only if an interaction with Papers 1 to 3 appears; otherwise a section of the integrated-agent technical report. Integration keeps every component's independent ablation.

## 10. Capability framing (replaces the ladder)

Orthogonal capabilities, each with a metric: causal support estimation; action-effect dynamics; change and continuity tracking; uncertainty and metacognitive monitoring (selective risk, abstention, calibration resolution); use of these estimates to improve decisions under cost; persistence versus reacquisition; out-of-distribution generalisation across dynamics families. Phenomenal consciousness appears once, in the motivation paragraph, as what is not claimed.

## 11. Execution workflow per phase

1. Daniel confirms the phase's estimand and scope (one page).
2. Building agent implements from the written contract; every metric and baseline is a frozen, named algorithm with a tuning budget.
3. Invariant and positive/negative control tests must pass before any sweep.
4. Red-teaming agent reviews code, protocol and first results; high-severity findings block the phase.
5. Sweeps run interleaved and randomised with the ledger on; overnight runs on the Air with step budgets.
6. Daniel reviews results against predeclared hypotheses; no post-hoc rescue of confirmation conditions.
7. Novelty re-check; write-up; the other agent red-teams the draft; arXiv.

## 12. Risks and responses

| Risk | Response |
|---|---|
| Estimand still inconsistent after Phase 0A | Stop; resolve with Daniel; nothing else starts |
| Scooped on the exact Paper 1 benchmark | Low likelihood; contribution is the standardised protocol and findings, which remain citable |
| Scooped on Phase S | Likely on components; the note makes no method claim and remains a valid sanity check |
| Agent-produced protocol errors | Adversarial build/red-team loop; invariants; frozen evaluator; human review of every result |
| Compute overrun on the Air | Fractional design; 1.5x allowance for throttling; cut cells, not seeds |
| Venue calls do not match | arXiv is the primary output; venues are opportunistic |
| Motivation drift toward consciousness claims | D2 and D7; the red-teaming agent checks every abstract |
