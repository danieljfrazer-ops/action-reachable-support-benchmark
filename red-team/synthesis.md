# Synthesis: Claude's assessment of the Codex response and the merged plan

**Date:** 6 September 2026. **Inputs:** `codex-response/` (four files), `roadmap-v2.md`, `findings.md`, `research-round-2.md`.

## 1. Assessment of the Codex response

The response is careful, well sourced, and in several places better than the work it reviewed. It accepted the red team's six criticisms (four outright, two with modification), and its red team of roadmap-v2 found real defects. I verified the two citations most damaging to v2:

- Voelcker, Kastner, Gilitschenski & Farahmand, "When does Self-Prediction help?" (arXiv 2406.17718, Jun 2024): latent self-prediction as an auxiliary RL objective, analysed under distractors. Verified. No body change. It does make "auxiliary hidden-state prediction" an occupied objective.
- Sturm, Plagemann & Burgard 2009 (body schema learned from action and self-observation, monitored and adapted after failure): the PubMed page was cookie-walled, but the description matches the paper as known. Accepted.

Where I concede, in order of importance:

| Codex finding | Verdict | What changes |
|---|---|---|
| C1 estimand: an actuator remap can change the action-to-effect mapping without changing the controllability mask; a sensor swap can permute identity without changing physical controllability | **Concede. This is the most important finding in the whole exchange.** | Three separate ground-truth targets: controllability support, action-to-effect mapping, observation identity. Each intervention type is labelled by the target it actually changes. |
| C2 a lagged copy of the agent's own effects is causally action-reachable, so labelling it "outside the boundary" is contradictory | **Concede.** | Distractors defined by structural equations. Three classes: exogenous action-correlated, downstream action effects that are not body, copied sensors. Estimand declared explicitly (direct controllability vs causal reachability vs body membership). |
| C4 "first test of self-modeling in a changing agent" overclaims; Sturm 2009, Voelcker 2024, Fu et al. CoRL 2025 occupy the parent claim | **Concede.** | Paper 2 question narrowed: does temporally predictive latent dynamics, beyond an equal-compute forward-model control, improve quickest re-identification of a changed causal support? |
| C5 auxiliary targets undefined or leaking evaluator truth | **Concede.** | Information sets and horizons specified; mask head is either declared privileged supervision or called distillation. |
| C6 calibration not defined for non-probabilistic estimators | **Concede.** | Every method emits a probability from a declared model or a calibrator fitted on a separate split; Brier and log loss primary; ECE secondary with fixed bins. |
| C7 Stage 0 not feasible in 4 weeks | **Concede.** | Stage 0A (2 weeks): causal contract, generator, invariants, random/observational/IBD baselines. Stage 0B (2 to 4 weeks): sequential change protocol. Memory, cost ledger and Premakumar deferred to the papers that need them. |
| C8 kill criterion authorises post-hoc rescue | **Concede.** | Frozen pilot tuning region; kill/redirect if positive controls fail or CIs exclude a predeclared smallest effect of interest. |
| C9 to C14 baseline fairness, intervention budget, sequential definitions, reintroduction confound, hypothesis flexibility, baselines as labels | **Concede all.** | Matched Bayesian variants (correct, misspecified, nonparametric); Pareto over regret, probes, samples, compute; stopping rule and ARL/detection-delay curves; counterbalanced ABA/ABC; one primary contrast plus smallest effect of interest; one frozen algorithm and tuning budget per baseline family. |
| C15 mid-February 2027 only with scope reduction; venues provisional | **Concede.** | arXiv-quality minimal benchmark by mid-February; fractional design; four weeks reserve; venue submission contingent on live CFPs. |
| C16 credible case for a memory benchmark first | **Partly concede.** | See open decision 1 below. |
| C17 one universal testbed couples without validating | **Concede.** | Shared logging interface, separate environment modules; boundary findings validated on two dynamics families before "testbed" is called a contribution. |
| C18 the ladder is not a ladder | **Concede the structure, not the conclusion about consciousness.** | Replace with orthogonal capabilities: causal support, action-effect dynamics, change tracking, uncertainty monitoring, use of estimates under cost. See open decision 2. |
| C19, C20 controls validate unrelated components; chronology and evidence quality | **Concede.** | Reproductions placed before the paper they validate; preprint vs peer-reviewed status marked; Memory-R1 dated Aug 2025 / ACL 2026. |

Where I push back:

- **Codex's own surviving-gap statement is my Paper 1 with the estimand repaired.** It describes "sequential, action-intervention-based estimation under causally non-responsive action-confounded observations, with a common quickest-detection and probabilistic-scoring protocol" as what survives. Agreed. The direction is unchanged; the specification was wrong.
- **"Omit consciousness from the programme entirely, including motivation."** That is a stylistic opinion, and Daniel's stated goal includes it. A single sentence in the motivation stating what is *not* claimed is standard and honest. Keep it unless Daniel prefers Codex's stricter line.
- **Thermal precision.** Codex is right that "25 to 50 percent within 8 to 15 minutes" was stated with more confidence than the sources support. The design remedy is unchanged.

Both agents now agree on: boundary-under-change is the first full paper; R1 memory is a benchmark, not a method; R5 is a component; no self-awareness claims; step budgets not wall-clock; arXiv first.

## 2. Merged plan

**Stage 0A (weeks 1 to 2).** Write and test an executable structural-causal environment contract before any estimator: variables, structural equations, intervention semantics, horizon-specific ground truth for the three targets, invariants as tests. Deterministic numpy generator. Baselines: random, temporal correlation, one forward-model residual, IBD reproduced faithfully against its published qualitative checks. Draft contract: [stage-0a-contract-draft.md](stage-0a-contract-draft.md).

**Stage 0B (weeks 3 to 6).** Sequential change protocol: change events for each of the three targets, exogenous action-correlated distractors, stopping rule, detection-delay versus false-alarm curves, calibrator split. Positive control: IBD detects a support change after re-probing; negative control: random.

**Optional shakedown (decision 1).** A two-week symbolic hidden-volatility memory microbenchmark using the hardened R1 protocol, as an engineering shakedown and possible technical note. Only if it does not push Paper 1 past mid-February.

**Paper 1 (to mid-February 2027).** Standardised stress test and comparative evaluation of changing-boundary estimators. Contribution: benchmark plus findings. One primary contrast chosen by a pilot power study; response surface secondary. Two dynamics families. arXiv first; workshop or CoLLAs if a matching CFP appears.

**Paper 2 (2027).** Narrowed auxiliary-objective question with defined information sets, equal-compute forward-model control, no privileged labels unless declared. Premakumar reproduction as its gate.

**Paper 3 and later.** Unchanged from roadmap-v2: fast-self versus slow-world memory with the hardened R1 protocol; scheduling as a component; integration last.

## 3. Open decisions for Daniel

1. **Memory shakedown before Paper 1?** Codex says yes (momentum, cleaner ground truth, larger audience). I say only if it fits in two weeks after Stage 0A; otherwise defer to Paper 3. Default if no answer: defer.
2. **Consciousness in the motivation paragraph?** Codex: omit entirely. Me: one sentence stating it is not claimed. Default: one sentence.
3. **Vector observations with fixed dimensionality and padded channels for Paper 1** (both agents agree). Confirm.

## 4. First action

Draft the Stage 0A contract, then implement it as a numpy package with pytest invariants. Nothing else starts until the invariants pass.
