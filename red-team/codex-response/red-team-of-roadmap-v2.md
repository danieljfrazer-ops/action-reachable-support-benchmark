# Red team of `roadmap-v2.md` and `recommendation.md`

**Review date:** 6 September 2026  
**Stance:** assume v2's contribution claims and protocol are wrong until they survive a hostile reading. “Not found” means not found in the live searches and sources recorded in [sources.md](sources.md), not proof of absence. Statements about likely review outcomes or project duration are my opinion.

## Technical summary

V2 chooses the better long-term direction, but its first paper does not yet have a coherent estimand: a binary controllability mask cannot register every actuator remap, and a lagged copy of an action-caused effect may itself be causally action-reachable. Its “unoccupied intersections” also overstate novelty because probabilistic body-schema adaptation, fault detection, and auxiliary self-prediction already occupy the parent questions. What survives is a narrower benchmark contribution. Stage 0 should be reduced to a causal boundary generator plus IBD reproduction; Paper 1 needs sequential operating curves and comparable probabilistic outputs; Paper 2 needs non-leaking, temporally defined auxiliary targets. With those changes, a February 2027 preprint is plausible on the M5 Air, while venue submission remains contingent on actual workshop calls.

## High severity

### C1. The benchmark's target changes are not all changes to its target variable

**Claim attacked.** Paper 1 detects when “the set of dimensions an agent controls changes”; manipulations include actuator remap, sensor dropout/swap, and morphology change; the ground truth is a time-varying binary controllability mask.

**Evidence/attack.** A permutation or gain change in the action-to-effect mapping can leave exactly the same observation dimensions controllable. A sensor swap can permute representation while preserving physical controllability. These are changes to a causal mechanism, not necessarily to its support. Mask accuracy and “mask crossing a threshold” can therefore report no change when the body mapping genuinely changed. Conversely, “morphology change (N changes)” changes tensor shape and can make comparison architecture-dependent.

**Recommended fix.** Define three separate targets: (1) direct/horizon-specific controllability support; (2) the signed action-to-effect Jacobian or conditional effect model; and (3) observation identity/alignment. Assign each intervention type to the target it actually changes. Keep input dimensionality fixed with inactive/padded channels for the first paper. Do not call a remap a mask change unless its support changes.

### C2. “Spoofed distractor” generation can accidentally make the distractor causally controllable

**Claim attacked.** Distractors include “copies of the agent's own effects with lag” but are evaluated as outside the true boundary.

**Evidence/attack.** If a distractor is literally generated from an action-caused state, then there is a directed causal path from action to distractor. Under IBD's action-reachable Sphere of Influence definition it belongs inside the mask, even if semantically it is “world” or a duplicate display. IBD's hard distractors instead share exogenous causes or action-correlated statistics while having no incoming causal path from action. Without an explicit structural causal model, the proposed ground truth is contradictory.

**Recommended fix.** Publish the structural equations and causal graph first. Separate (a) exogenous action-correlated distractors, (b) downstream action effects that are not body variables, and (c) copied sensors. Decide whether the estimand is causal reachability, direct controllability, agency, or body membership; those are not synonyms. Unit-test each variable with interventions against the evaluator's declared target.

### C3. The first “unoccupied intersection” is narrower than v2 claims and vulnerable to novelty-by-conjunction

**Claim attacked.** The intersection of interventional boundary estimation, deployment-time boundary change, action-synchronised distractors, and latency/false-alarm/calibration metrics is unoccupied.

**Evidence/attack.** IBD occupies interventional mask discovery under confounded distractors. Sturm, Plagemann & Burgard (2009) learn a probabilistic body schema from action signals and visual self-observation, test model validity, detect blocked/deformed joints, localize mismatch, and adapt the model over its lifetime. Online Bayesian change-point detection has been applied to articulated motion models. Fault detection and isolation (FDI) routinely studies actuator/sensor changes using command-to-observation residuals and evaluates detection/false-alarm trade-offs. The full four-clause benchmark may still be new, but the scientific question “detect and adapt an internal body/action model when it changes” is occupied.

**Recommended fix.** Claim a **standardized stress test and comparative evaluation**, not a new problem. State the surviving gap precisely: sequential, action-intervention-based estimation under causally non-responsive action-confounded observations, with a common quickest-detection and probabilistic-scoring protocol. Compare to body-schema adaptation and FDI, not only RL feature selection.

### C4. Paper 2's “first test” claim does not survive adjacent work

**Claim attacked.** “First test of self-modeling in a changing agent” and the broader claim that an auxiliary self-model aiding adaptation after body change appears unasked.

**Evidence/attack.** Self-models have been used for damage detection and recovery since at least Bongard et al. (2006) and Sturm et al. (2009); Chen et al. (2022), Hu et al. (2025), and Farghdani et al. (2025) explicitly update or use self-models after damage. Fu et al. (CoRL 2025) integrate a forward predictor and prediction-error comparator into RL for fault-tolerant legged locomotion. Voelcker et al. (2024) already study latent self-prediction as an auxiliary RL objective under distractors. These do not exactly test Premakumar-style internal-activation prediction plus mask calibration after an abrupt support change, but they occupy the broad causal claim that predictive self/body models can aid adaptation.

**Recommended fix.** Delete “first test of self-modeling in a changing agent.” Narrow the question to a predeclared auxiliary target and mechanism, e.g. whether *temporally predictive latent dynamics*, beyond an equal-compute forward-model control, improves quickest re-identification of a changed causal support. Include Voelcker et al., robotics self-models, world-model-feedback continual RL, and fault-tolerant control.

### C5. Two Paper 2 targets are undefined or leak evaluator truth

**Claim attacked.** Auxiliary heads predict “own hidden state, own next-step error, own controllability mask.”

**Evidence/attack.** Predicting a current hidden state from that same state is an identity shortcut; predicting a future state needs a horizon, inputs, stop-gradient rule, and anti-collapse control. Next-step error is only defined after the next observation and can become an uncertainty/novelty predictor rather than a body model. The true controllability mask is said to be evaluator-only: supervised mask prediction therefore leaks privileged labels, while pseudo-label prediction merely distils whichever estimator generated them and is circular.

**Recommended fix.** Specify information sets and targets mathematically. Use future-latent prediction with stop-gradient and a matched non-self auxiliary control; separate error forecasting from state prediction. For the mask head, either declare privileged supervision and test sample efficiency honestly, or use estimator pseudo-labels and call it distillation. Do not combine all three until each has an identifiable causal pathway.

### C6. Calibration is not currently a common, well-defined comparison

**Claim attacked.** Score every estimator's “per-dimension controllability probability” with Brier and ECE.

**Evidence/attack.** IBD returns FDR-adjusted hypothesis decisions; a p-value or `1-p` is not a posterior probability of controllability. Correlation, residual, and MI baselines also emit incomparable scores. Thresholding them for latency and then treating them as calibrated probabilities invites post-hoc favourable tuning. ECE adds arbitrary bins and can look good under severe class imbalance (many distractors) or long stationary periods.

**Recommended fix.** Require every method to output a probability produced by a declared probabilistic model or by a calibrator fitted on a separate calibration split. Report per-dimension Brier and log loss, class-conditional calibration/reliability plots, calibration during fixed transition windows, and uncertainty intervals. Keep ECE secondary with fixed bins. For non-probabilistic IBD, report sequential test operating characteristics unless a separately trained calibration map is used.

### C7. Stage 0 is not a realistic four-week solo gate as written

**Claim attacked.** One person can build the full continuing environment—with body changes, three distractor families, symbolic hidden-hazard memory, delays, anomalies, reversals, resource ledger, and asynchronous world advance—plus reproduce IBD, Premakumar, and a continual-memory failure in four weeks.

**Evidence/attack.** These are three different research stacks and validation targets. Reproducing only a direction of effect is too weak to validate implementation; reproducing enough detail to diagnose a failure is substantial. The integrated environment also introduces unused Paper 3/4 machinery into Paper 1's critical path. In my judgment, four weeks is plausible for a boundary-only vector generator plus one faithful IBD reproduction, not the listed scope.

**Recommended fix.** Split Stage 0A (two weeks: structural equations, deterministic generator, random/observational/IBD baselines, invariant tests) from Stage 0B (two to four weeks: sequential change protocol). Defer facts/hazards and the cost ledger until Papers 3/4. Make Premakumar a Paper 2 gate. Require agreement on a small set of published numeric or qualitative checks, not just sign.

### C8. The Paper 1 kill criterion authorizes post-hoc rescue

**Claim attacked.** If estimators are indistinguishable by week 14, “re-tune with the change magnitude sweep and publish whatever phase structure exists.”

**Evidence/attack.** That is not a kill criterion. It changes task difficulty after seeing outcomes and promises a phase structure whether or not one exists. “Any hypothesis failing is a result” similarly confuses falsifiability with publishability.

**Recommended fix.** Freeze a pilot-only tuning region before confirmation. Kill or redirect if positive controls fail, if the best methods are below a minimum useful mask/effect-model accuracy, or if confidence intervals exclude a predeclared practically meaningful difference across the confirmation grid. A null can be published, but publication is not guaranteed by declaration.

## Medium severity

### C9. The Bayesian change-point baseline can be unfair in either direction

**Claim attacked.** A Bayesian change-point detector over “controllability evidence” is a fair model-based baseline and is hypothesized to be best calibrated.

**Evidence/attack.** No observation model, hazard prior, evidence statistic, or output-to-mask update is specified. Give it the true likelihood family and it may have an oracle structural advantage; give it a misspecified scalar residual and it may be a straw man. It also detects a distribution change, not which dimensions changed. The hypothesis that it will be best calibrated follows from how it is parameterized, not from a neutral comparison.

**Recommended fix.** Implement matched versions: known-family/unknown-parameter, deliberately misspecified, and nonparametric sequential detectors, all consuming the same samples and intervention budget. Report detection-delay versus false-alarm curves or average run length, not one threshold. Call the correctly specified version a model-informed reference, not an ordinary baseline.

### C10. “Equal intervention budget” does not equalize information or total cost

**Claim attacked.** Estimators receive equal intervention budget and per-estimator compute is reported.

**Evidence/attack.** Observational methods need no special intervention; IBD changes the data-collection policy and may lose task reward. A learned self-model may exploit every policy action as data. Equal counts therefore neither equalize samples nor opportunity cost.

**Recommended fix.** Compare Pareto frontiers over task regret, randomized probes, environment samples, and compute. Include passive-policy, shared-exploration-data, and active-probing regimes. Predeclare whether intervention data may train the controller.

### C11. Detection latency and false alarms need sequential definitions

**Claim attacked.** Latency is “steps from change to mask crossing a threshold”; false-alarm rate is measured during stationary periods.

**Evidence/attack.** Which dimension or aggregate must cross? Does a transient crossing count? How are repeated alarms handled? A detector can lower latency by raising false alarms. Delay/noise and active probes make calendar steps, observations, and interventions inequivalent.

**Recommended fix.** Define a stopping rule, persistence requirement, event matching window, missed-detection censoring, reset policy, and units. Report detection-delay/average-run-length or time-dependent ROC curves, plus probe count and regret to detection.

### C12. “Re-introduced morphology” is heavily confounded

**Claim attacked.** Faster recovery when an old morphology returns measures reduced forgetting.

**Evidence/attack.** It can instead measure a cached morphology classifier, retained optimizer state, replay, more total exposure, or easier second-position curriculum. A method explicitly storing old models has a structural advantage. If the same morphology is seen twice during training, the result also says little about novel recurrence.

**Recommended fix.** Use matched ABA and ABC sequences, counterbalance order and dwell time, reset optimizer/detector state in declared ablations, separate explicit-library retrieval from parameter savings, and test a held-out but structurally similar morphology. Measure identification and adaptation separately.

### C13. The hypotheses invite a phase diagram rather than risk a clear null

**Claim attacked.** H2 predicts at least two winner regions; H1/H3 predict intuitive ordering and calibration degradation.

**Evidence/attack.** With enough axes and threshold choices, finding two winner regions is likely and analytically flexible. H1 need not hold: a strong intervention effect can be detected faster than passive drift, while IBD as published is a one-time batch procedure rather than a sequential detector. H3's “all degrade” lacks a minimum effect and window.

**Recommended fix.** Choose one primary contrast and one primary operating point based on a power/simulation study. Treat the rest as a multiple-comparison-controlled response surface. Predeclare smallest effects of interest and explicitly allow “no meaningful phase boundary.”

### C14. Several baselines are labels, not reproducible algorithms

**Claim attacked.** “Temporal correlation,” “prediction-error,” “MI/empowerment proxy,” “Lipson-style learned self-model,” and “IBD-style” constitute a baseline suite.

**Evidence/attack.** Window length, lag set, conditioning variables, estimator, retraining schedule, sequential reset, and threshold can reverse rankings. “Lipson-style” spans evolutionary, kinematic, visual occupancy, and egocentric dynamics models. An empowerment proxy is not automatically a per-dimension boundary estimator.

**Recommended fix.** Freeze one cited algorithm and hyperparameter-selection budget per family. Separate feature scoring, change detection, and causal-effect estimation into composable stages. Release configurations and give every baseline the same development budget.

### C15. Mid-February 2027 is possible only after aggressive scope reduction

**Claim attacked.** Stage 0 plus Paper 1 is realistic by mid-February 2027, with ICLR 2027 workshops and/or CoLLAs 2027 as targets.

**Evidence/attack.** Roughly 23 weeks remain, which can support a small synthetic benchmark preprint. The stated factorial space—six estimators, three change types, magnitudes, up to 100 distractors, delay, noise, reintroduction, intervention budgets, two held-out configurations, ten confirmation seeds—will explode without a fractional design. As of this review, official ICLR 2027 **main-conference** deadlines are September 2026; workshop topics and paper deadlines are not yet established. I found no official CoLLAs 2027 CFP. The venue dates in v2 are appropriately labelled “expected,” but they are planning assumptions, not verified targets. CoLLAs 2027 also likely cannot take a June Paper 2 if its deadline resembles prior years.

**Recommended fix.** Target an arXiv-quality minimal benchmark by mid-February, with venue submission contingent on actual CFPs. Use a power analysis and fractional factorial design. Add four weeks of schedule reserve and a workshop-length fallback with a smaller claim.

### C16. There is a credible case for memory first

**Claim attacked.** R1 should be only an optional side paper because it is crowded and less connected to the programme's motivation.

**Evidence/attack.** The opposite strategy has real advantages: symbolic streams give cleaner ground truth, no causal-boundary definitional dispute, much less environment engineering, and a faster reproducible negative-result/benchmark preprint. Continual learning, online adaptation, and sequence memory form a larger audience than developmental body-schema work. Since R1 is at higher scoop risk, doing a narrowly scoped benchmark first may be rational. The costs are weaker distinctiveness and demanding budget normalization.

**Recommended fix.** Use a merge strategy: make a two-to-four-week memory microbenchmark the engineering shakedown and possible technical note, while the first full paper remains boundary-under-change only after C1–C6 are resolved. Do not build a learned router unless simple hazard baselines leave a gap.

### C17. One universal testbed creates coupling without yet creating validity

**Claim attacked.** A single environment supporting boundary, hidden volatility, resource cost, memory, and scheduling is itself a contribution and should exist from the start.

**Evidence/attack.** Shared code is useful, but a synthetic environment containing every future mechanism can make later results artifacts of one arbitrary generator. The Paper 1 estimand does not need symbolic facts or simulated thinking costs. A benchmark becomes a contribution through external validity, documented task families, and adoption—not merely breadth.

**Recommended fix.** Build a small common event/logging interface and separate environment modules. Validate boundary findings on at least two independently structured dynamics families before calling the testbed a contribution.

### C18. The functional “ladder” is not a ladder

**Claim attacked.** Boundary → body → own future state → introspection forms four ascending functional constructs, all covered with ground truth.

**Evidence/attack.** A body dynamics model can be learned without a prior binary boundary; a generic predictor can forecast resource variables without modelling body or agency; behavioral self-prediction in LLMs is methodologically different from hidden-state prediction in a small agent. Rungs 1 and 2 are substantially occupied by IBD/body-schema robotics; latent self-prediction in RL and LLM self-prediction occupy parts of rung 4. The rows mix representation content, uncertainty, intervention method, and evaluation criterion. Ground truth for “what I know” is not supplied merely by a simulator.

**Recommended fix.** Replace the hierarchy with orthogonal capabilities: causal support, action-to-effect dynamics, change/continuity tracking, uncertainty/metacognitive monitoring, and use of those estimates to improve decisions under cost. Add missing measures: selective risk or abstention, calibration resolution, OOD generalization, causal usefulness (ablation/intervention), and persistence versus reacquisition. Keep phenomenal or consciousness constructs outside the programme entirely, including motivation claims.

## Low severity

### C19. The Stage 0 positive controls validate unrelated components

**Claim attacked.** IBD, Premakumar weight narrowing, and a single-tier memory failure jointly gate one environment.

**Evidence/attack.** Passing these signs does not validate cross-component integration, sequential detection, or calibration. Weight-distribution narrowing can occur while task adaptation worsens.

**Recommended fix.** Put each reproduction immediately before the paper it validates and add invariant/property tests for the shared simulator.

### C20. The recommendation understates chronology and evidence quality

**Claim attacked.** The cited 2026 self-interventional work supports a mature new thread; venue dates and some tool claims support scheduling choices.

**Evidence/attack.** Self-Interventional Learning is a single-author August 2026 arXiv preprint submitted to JMLR, not settled literature. Memory-R1 was first posted in 2025. CoLLAs 2027 dates were not live-verifiable. The Science Robotics page was access-blocked during this review, although independent publisher/project and bibliographic pages supported its broad description.

**Recommended fix.** Mark publication status and first-posted dates consistently; distinguish peer-reviewed evidence from fresh preprints; attach “unannounced as of 6 September 2026” to venue assumptions.

## Feasibility judgment

- **Stage 0 as written:** no, not credibly in four weeks for one person. A boundary-only Stage 0 with one reproduction is credible.
- **Paper 1 by mid-February 2027:** plausible as a scoped synthetic benchmark/preprint, not with the full testbed and Cartesian sweep. Workshop acceptance is unknowable before CFPs; a main-conference paper is not realistic on that schedule.
- **Hardware:** the 32 GB M5 Air is adequate for the proposed sub-10M models and vector simulation. Use algorithmic budgets and randomized/interleaved runs; thermal throttling affects throughput, not the scientific possibility.

## Strategic judgment

My opinion is to merge the roadmaps. Keep v2's boundary-under-change programme as the main scientific direction, but use a sharply limited R1 benchmark as the first engineering and dissemination milestone. For a solo unaffiliated author, arXiv plus code and a tightly matched specialist workshop are sensible. CoLLAs is a strong topical fit if its 2027 call appears; ICLR workshops are not a venue plan until specific workshop calls exist. The work should be written to survive as a benchmark or careful null, rather than depend on a new-method win.

## Attacks that failed

- **“IBD already covers deployment-time boundary change.”** Failed. The paper assumes stationary causal structure during probing and computes one mask.
- **“The exact dynamic-boundary plus causally confounded-distractor benchmark is already published.”** Failed. I found close components and an occupied parent problem, but not the exact standardized combination. Absence is not proven.
- **“Paper 1 is too computationally large for the M5 Air.”** Failed. The compute is laptop-feasible after scope reduction; protocol breadth and labour are the constraint.
- **“R5 should remain a flagship.”** Failed. *Finding the Time to Think* directly covers learned planning budgets while the environment/clock advances; only a narrower heterogeneous-operation interaction remains.
- **“The thermal protocol in v2 is still fundamentally invalid.”** Failed. Step/operation budgets, interleaving, and thermal logging address the main scientific confound, though steady-state/cooldown rules should be clearer.
- **“A functional framing necessarily makes an unsupported consciousness claim.”** Failed. V2 expressly disallows that inference. My recommendation is stronger: omit the construct entirely rather than place it as an unreachable rung.
- **“Memory must remain the first full paper.”** Failed. There is a strategic case for a fast memory milestone, but its crowded novelty landscape still favours boundary-under-change as the first full paper once the estimand is repaired.
