# Roadmap v4 (consolidated, normative)

**Status:** 6 September 2026. **Supersedes** `roadmap-v2.md`, `roadmap-v3.md`, `roadmap-v3.1-amendments.md`, `roadmap-v3.2-amendments.md`, `roadmap-v3.3-amendments.md`, `roadmap-v3.4-amendments.md`, the roadmap patches in the three `gemini-v3.*` folders, and `benchmark-proposal.md` sections 2 and 3. Earlier files remain as history only; an implementing agent reads **this file, `stage-0a-contract-v3.md`, `confirmation-design.csv`, and `interface-spec.md`** and nothing else as instructions. Sections marked [N] are normative.

## 1. Locked decisions [N]

| # | Decision |
|---|---|
| D1 | Phase S is a one-week internal shakedown between 0A and 0B; diagnostic only; public note only for a predeclared surprising result and only after Paper 1 is on arXiv |
| D2 | Consciousness appears in one motivation sentence as a non-claim; nowhere else |
| D3 | Fixed-dimensionality vector observations with padding |
| D4 | Two agents build and red-team alternately; Daniel decides estimands, reviews gate reports (test output plus uncovered-item count), writes the argument |
| D5 | Step and operation budgets primary; serial heavy runs; cooldowns; thermal log; runtime pilot before dates |
| D6 | arXiv first; venues only against live calls |
| D7 | Contribution type stated in every abstract; a method claim needs the matched model-based and trivial baselines on held-out families |
| D8 | Paper 1 primary target: action-reachable observation support S^obs,ε (probabilities p_c) and support-change alarm α^S. Nothing else is primary |
| D9 | Primary comparator: **channel-agnostic CUSUM on innovations of a linear predictor** versus **sequential IBD**. Oracle-coordinate CUSUM is a labelled reference, not the comparator |
| D10 | Confirmatory regimes: **R0 clean** (negative control with non-superiority margin) and **R1 misspecified**. **R2 masked** is exploratory, scored on R-change with partial actuator loss, appendix only, until a redundant-actuator environment exists |
| D11 | Primary statistic: difference in restricted mean detection time at matched ARL_0 (contract G); pAUC descriptive; no disjoint-support scalar |
| D12 | Paper 2 treatment is **typed routing** (controllable, exogenous-but-relevant, uncertain), not deletion; framing is a cross-architecture changing-boundary stress test plus a routing remedy, not discovery of the blind spot |
| D13 | Package and paper names chosen after a collision check; `boundary-bench` is not available |

## 2. Programme [I]

An agent that runs continuously must track which observation channels its actions reach, while distractors correlate with its actions through a shared cause and while its actuators and sensors change without warning. The programme builds a fully ground-truthed testbed for this and publishes benchmark and empirical-finding papers, then a world-model stress test with a routing remedy. Functional self-modeling is the connecting theme; no paper claims self-awareness.

## 3. Phases and gates [N]

| Phase | Content | Gate | Target |
|---|---|---|---|
| 0R | **Contract and test repair** (this week): contract v3, gate tests with mutants passing and failing as required, coverage matrix, interface spec, runtime pilot on a toy cell | Daniel signs the gate report | 13 Sep 2026 |
| 0A | Generator (L, N), separate oracle, E1 to E6, four baselines, IBD static reproduction to numerical anchors | all tests pass; all mutants rejected; uncovered-item count 0; black-box acceptance suite passes | 4 Oct |
| S | Internal memory shakedown (three families, one pair, two budgets, 5 seeds) | internal diagnostic report with intervals | 11 Oct |
| 0B | Sequential protocol: events, schedules, RMDT and ARL_0 calibration, CUSUM variants, Bayesian reference, calibrator split, censoring | positive and negative controls; 2×2 diagnostic (dynamics correct/misspecified × confounder absent/present) shows the confounding interaction separately from model error | 1 Nov |
| T2 | CartPole (u injected into action logits) and Pendulum-v1 (u added to torque; `TimeLimit` replaced by a declared 1000-step horizon, disclosed); early termination recorded as a competing outcome | wrapper invariance tests (randomised do(a) leaves distractor channels unchanged) pass on both | 15 Nov |
| P1 pilot | variance and runtime only; thresholds calibrated to ARL_0 on the calibration split; frozen after | pilot report | 29 Nov |
| P1 confirm | cells in `confirmation-design.csv`; 10 seeds; evaluator hash held by Daniel outside the tree | data freeze | 3 Jan 2027 |
| P1 write-up | novelty re-check; other-agent red team; Daniel writes | arXiv | **late Feb 2027** (4-week slip reserve included) |
| P2 | coupled MuJoCo; world models on rented GPU; typed routing | | Mar to Jul 2027 |

## 4. Paper 1 design [N]

**Working claim.** A standardised sequential benchmark for action-reachable observation support under confounded distractors and unannounced actuator and sensor changes, with classical and learned detectors compared at matched false-alarm control. Contribution: benchmark plus findings.

**Environments.** SCM family L, SCM family N, CartPole, Pendulum-v1.
**Baselines (five).** Random; temporal correlation; forward-model residual; sequential IBD; channel-agnostic CUSUM. Each with a declared information set. Oracle-coordinate CUSUM and one Bayesian reference in the appendix.
**Regimes.** R0: correct dynamics model for the residual detectors. R1: residual detectors use a misspecified model (linear model on family N; drifted parameters on family L). Diagnostic 2×2 in both families: confounder absent and present, so that R1's effect is attributable to the confounding interaction.
**Events.** Confirmatory: complete actuator loss producing an S^obs change (certified by the oracle per instance). Exploratory appendix: partial loss (R-change) and gain events.
**Primary estimand.** Δ = RMDT(CUSUM) − RMDT(seq-IBD) at matched ARL_0, positive favouring IBD, in steps, with 95 percent intervals clustered by seed. Detection probability within H_det reported with it.
**Effect sizes.** δ = 20 steps (smallest effect of interest, R1); δ0 = 10 steps (non-superiority margin, R0). Both provisional until the pilot variance is known; frozen before confirmation with a written reason for any change.
**Decision rules.** R0: validated if the upper bound of Δ < δ0 and the CUSUM implementation detects the fault in the diagnostic; anomaly otherwise. R1: superiority if the lower bound > δ on both SCM families and the sign holds on both T2 environments; futility if the upper bound < δ on either SCM family; inconclusive otherwise, reported without an efficacy claim. Positive-control gate runs before, not within, confirmation.
**Probe budget.** One declared budget for the confirmatory test; a budget sweep in the appendix estimates the break-even budget descriptively.
**Pilot use.** Variance, runtime and threshold calibration only; no contrast selection.
**Run matrix.** `confirmation-design.csv`, generated by `make_confirmation_design.py`; one row per run.

## 5. Paper 2 design [N]

Question: when a shared cause drives both the policy and a distractor, do inverse-dynamics and action-conditioned separation criteria in world models (Iso-Dream, Sensorimotor World Models, Dueling World Models, Denoised MDP) attribute the distractor to the controllable branch, and how does each behave when actuators or sensors change? Treatment: typed routing with soft weights, compared against hard deletion and each architecture's native mechanism, measuring controllability leakage and retention of reward-relevant exogenous information separately. Environments: coupled MuJoCo (Reacher, HalfCheetah) where actuator loss is an R-change. Compute: rented GPU, declared budget, measured before commitment.

## 6. Workflow [N]

1. Daniel confirms scope (one page). 2. Builder implements from the contract and interface spec. 3. **Gate**: tests pass, mutants rejected, coverage matrix has zero uncovered normative items, black-box acceptance suite passes; report signed by Daniel. 4. Red-teaming agent reviews with the repository and adds mutants. 5. Sweeps serial with ledger on. 6. Results against predeclared hypotheses; no post-hoc rescue. 7. Novelty re-check; write-up; red team of the draft; arXiv.
Change control: hashes of source, config schema, lockfile, generator version, metric code; append-only manifests; semantic changes rerun affected cells; Daniel approves exceptions before unblinding.

## 7. Risks [I]

Contract still inconsistent after 0R: stop and resolve. Runtime pilot shows cells slower than estimated: cut exploratory cells, not seeds. Scooped on the benchmark: contribution is the protocol and findings. Scooped on Paper 2's failure mode: framing is already a stress test, not a discovery. Agent-certified shared mistake: E6 black-box suite and Daniel's hand case.
