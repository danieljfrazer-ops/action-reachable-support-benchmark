# Response to the red team

**Date:** 6 September 2026  
**Scope:** response to the six claims about *Persistent Adaptive AI: Novelty Review and Research Roadmap*. I read all eight files in `docs/archive/red-team/` before beginning this review. I then checked the papers listed under “Independent checks” against live publisher, proceedings, or arXiv pages and, where needed, the paper text. Assessments of research value and feasibility are explicitly my judgment.

## Bottom line

The red team is right that the report's three numerical novelty scores were too high and that the R1 protocol was under-specified. I would withdraw the 4.5/4.5/4.0 scores rather than merely lower them: the unanchored scale communicates more precision than the literature search can support. The corrected contributions are narrower:

- R1: a budget-matched benchmark and phase diagram across memory families under hidden, per-entity volatility; a learned router is conditional, not the lead claim.
- R2: sequential estimation of a changing action–effect boundary under causally non-responsive but action-correlated distractors; not the already-established claim that interventions beat observational association.
- R5: heterogeneous metareasoning actions in a continuing agent, only if interactions with memory or boundary adaptation add something beyond real-time planning-budget work.

## 1. Missed prior art and inflated novelty scores

**Verdict: accept with modification.**

The central criticism is correct. The original search stayed too close to long-context neural memory and missed relevant non-stationary learning, Bayesian change-point inference, causal feature selection, robotics, and rational metareasoning.

What I would change:

1. Remove the numerical novelty chart and replace it with claim-level statements of what is known, what is adjacent, and what exact comparison remains untested.
2. Reframe R1 as a cross-family, total-budget-matched benchmark. Add Wilson–Nassar–Gold, MuScaTeL, FADE, Memory-R1, OAKS, and simple empirical-hazard policies as related work or baselines.
3. Reframe R2 around *online change*, but separate a binary controllability set from the action-to-effect mapping. IBD becomes the principal static-boundary baseline.
4. Demote R5 to an incremental extension or integrated-agent component. Add rational metareasoning, Jensen–Hennequin–Mattar, and *Finding the Time to Think* as the actual neighbourhood.

The modification matters because several red-team descriptions compress important differences:

- **Jain & Shenoy / MuScaTeL:** the paper learns instance-dependent mixtures of age-decay kernels, but its primary formulation is repeated, weighted training over large offline/batch windows; its continual-learning extension uses recent windows. It does **not** infer a persistent entity's hazard online or route that entity among recurrent, fast-weight, episodic, and slow-weight stores. It is damaging prior art for the *principle of instance-conditional timescales*, not a direct implementation of R1.
- **FADE:** it adapts per-parameter decay online and demonstrates fast/slow/stable targets, but the derivation is for online linear learning and the neural experiments apply FADE to the final layer. It is not per-item routing or a cross-memory-family system. The red team's phrase “matched to the environment's timescale” is fair as a result, but broader than the implemented scope.
- **Wilson, Nassar & Gold:** this is an online hierarchical Bayesian estimator of a stream-level, time-varying hazard. It supplies a strong normative/change-point baseline, but does not solve resource-constrained memory placement.
- **Memory-R1:** the technical characterization is right, but its arXiv submission is from August **2025** and it later appeared at ACL 2026; calling it simply “Memory-R1 (2026)” obscures that chronology. It learns CRUD operations over an external natural-language memory bank, not routing across memory families under hidden hazards.
- **IBD:** IBD does show that randomized action interventions beat observational selectors under confounded distractors, and assumes a stationary causal structure during its one-time probing phase. But the original R2 hypothesis explicitly included drift. Therefore “R2's primary hypothesis has already been tested” is too strong: the static “intervention beats correlation” half is occupied; sequential detection and calibration through an unannounced boundary change are not tested there.
- **Jensen et al.:** the learned agent chooses rollout versus physical action and pays a temporal opportunity cost, so it is close prior art. It does not model a fully exogenous world continuing during a rollout; *Finding the Time to Think* closes that remaining planning-budget gap much more directly. Neither schedules heterogeneous retrieve/learn/consolidate/rollout operations.

## 2. R1 budget matching and structural capacity advantage

**Verdict: accept.**

“Equal state bytes and update FLOPs” is insufficient as written. If the router receives four stores whose capacities are summed while a baseline receives only one store of the nominal size, the comparison is confounded. Even at equal total bytes, bytes do not equal usable information capacity and write FLOPs do not equal read/retrieval cost.

What I would change: match **total** allocated bytes across all stores; account separately for update operations, query/read operations, and persistent parameter bytes; sweep budgets and report Pareto frontiers; include single-tier, pairwise-tier, and leave-one-tier-out ablations; and supplement physical bytes with task-based effective state-size where defensible. A method claim would require beating the best same-budget pair, not merely each single tier.

## 3. Oracle, generator leakage, and metrics

**Verdict: accept.**

True hazard alone cannot upper-bound a policy whose optimum also depends on query timing, capacity contention, change structure, and read/write costs. “Hazard-informed reference” is the honest label. Meta-training on the generator makes the system test-time oracle-free, not distribution-free; held-out generator families belong in confirmation, not post-success exploration.

What I would change:

- Define correct/stale/wrong-other/abstain as mutually exclusive query outcomes.
- Measure change recovery with non-learning probe queries at fixed offsets and report conditional-on-opportunity operational latency separately.
- Require answer probabilities and score Brier/log loss plus reliability diagrams; treat ECE as secondary and predeclare binning.
- Predeclare maximum retention delay and minimum samples per bin.
- Use at least two structurally held-out generators, not merely unseen seeds.

## 4. MacBook Air thermal confounding

**Verdict: accept with modification.**

The design concern is valid. A live M5 Air stress test reported Cinebench falling from 3,415 to the low 2,300s under repeated load, and the chassis is fanless. That is large enough to invalidate sequential equal-wall-clock trials unless thermal state is controlled.

The red team's precise universal claim—“25 to 50 percent within 8 to 15 minutes”—is more confident than the evidence supports. Throttling onset and magnitude depend on 13-inch versus 15-inch chassis, ambient temperature, CPU/GPU mix, power mode, and workload. A five-minute run is not necessarily already throttled; repeated five-minute runs without cooldown are the stronger confound.

What I would change: make step/operation budgets primary; randomize and interleave conditions; begin timing from a declared steady thermal state or enforce a cooldown protocol; log macOS thermal pressure and observed throughput rather than claiming inaccessible clocks; and report wall-clock only as hardware-specific secondary evidence. The 32 GB capacity helps model fit, not sustained thermals.

## 5. Timeline, kill criteria, scoop risk, and audience

**Verdict: accept with modification.**

The report needed a staged schedule, effort envelope, and genuine stop/redirect rules. It also understated fast-moving memory-method scoop risk. I would add a four-week calibration gate, a scoped first-paper window, and per-paper criteria that redirect the output to a benchmark/negative result when a trivial or model-based baseline matches the learned method.

The audience criticism is only partly right. Asking the author to choose an audience was legitimate because R1 and R2 genuinely address different communities; the baseline list did, however, already commit **R1** mainly to continual learning plus sequence memory. The correction is to name an audience and venue per paper, not infer one umbrella audience from every stage.

## 6. AffectWorld and OAKS citation hygiene

**Verdict: accept.**

AffectWorld was linked in prose but absent from the numbered sources, and OAKS was labelled by the benchmark acronym rather than the ACL paper's title. I would add AffectWorld as a numbered source and cite OAKS as *Can Large Language Models Keep Up? Benchmarking Online Adaptation to Continual Knowledge Streams*. I would also replace the Nested Learning blog citation with the paper when available and add the earlier body-schema/self-recognition lineage.

## Independent checks of the most damaging papers

| Work checked | What the source establishes | Effect on the original report |
|---|---|---|
| Liu, Cheng & Bogdan, *Discovering What You Can Control* (arXiv:2603.18257) | Randomized-action intervention, per-dimension testing with FDR, binary action-reachable mask, confounded distractors, 12 continuous-control settings; explicitly assumes stationary causal structure during probing and computes the mask once. | Directly occupies the static core of R2, but not sequential change/calibration. |
| Jain & Shenoy, *Instance-Conditional Timescales of Decay* (AAAI 2024; arXiv:2212.05908) | Instance features select a mixture of temporal decay kernels for importance weighting; mainly batch/offline windows, with a continual-learning adaptation. | Invalidates “no close principle-level precedent,” but is not an online hazard-aware multi-store router. |
| Ramesh, Lewandowski & Schmidhuber, *FADE* (arXiv:2604.27063) | Approximate meta-gradients adapt per-parameter decay online; neural use is restricted to the final layer; experiments include fast, slow, and stable outputs. | Strong weight-level neighbour; not the same unit of routing or budget comparison. |
| Wilson, Nassar & Gold, *Bayesian On-line Learning of the Hazard Rate* (Neural Computation 2010) | Hierarchical Bayesian online inference learns a changing hazard rather than assuming it fixed. | Makes an oracle-free model-based hazard baseline mandatory. |
| Jensen, Hennequin & Mattar, *A recurrent network model of planning…* (Nature Neuroscience 2024) | A meta-RL agent learns when to run imagined rollouts versus act under different time costs. | Places R5 squarely inside learned metareasoning. |
| Muppidi et al., *Finding the Time to Think* (arXiv:2606.26463) | A gate chooses state-dependent planning budgets while real-time environments or clocks advance; it beats fixed and heuristic budgets. | Occupies R5's continuing-world planning-budget formulation; only heterogeneous internal operations remain. |
| Yan et al., *Memory-R1* (arXiv:2508.19828; ACL 2026) | RL-trained ADD/UPDATE/DELETE/NOOP memory management and outcome-trained answer selection. | Occupies delayed-reward learned external-memory operations, not hidden-hazard multi-tier routing. |

Full URLs and access outcomes are recorded in [sources.md](sources.md).
