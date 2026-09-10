---
title: "Which sensors do my actions control? A negative result on sequential interventional boundary tracking under a shared-cause confounder"
author: "Daniel Frazer"
date: "September 2026"
version: "Technical report, draft 12 (15 September 2026), restructured"
---

# Which sensors do my actions control? A negative result on sequential interventional boundary tracking under a shared-cause confounder

**Daniel Frazer** (independent). Technical report, September 2026.

## Abstract

An embodied agent needs to know which of its sensors its actions actually reach, when a hidden cause makes some sensors move in step with its actions and when its actuators fail without warning. Interventional Boundary Discovery (IBD) answers the static version of this question by randomising actions. This report tests the sequential version: whether an in-task, sign-randomised probing estimator at a 5 percent probe budget tracks a changing controllable boundary better than a passive residual monitor under a shared-cause confounder. On a certified linear-Gaussian testbed, three independent implementations of both estimators agreed to within Monte Carlo error in one experiment, part of that spread being a seeding defect that gave each process different trajectories, and to three decimal places in a second after the defect was repaired. The interventional estimator was not degraded by the confounder that cost a frozen passive monitor about 0.2 AUC on the full channel set in the base cells, which reproduces IBD's principle online; that gap rests on a two-implementation secondary measure, the first experiment's version of it being inadmissible under the study's own competence rule. On the separate task of ranking which controlled channel an actuator loss removed, a passive delay-aware covariance monitor equalled or beat the probed estimator in every linear-family cell, and the ordering reversed on the one nonlinear family, on five seeds. The two endpoints were measured on different channel sets under different effective confounding regimes and do not establish a dissociation. A re-posed primary measure scored only channels the confounder never reaches, so the benefit it was meant to measure was zero by construction, and a population-limit analysis showed that moving the confounder onto the controlled channels would not yield an identifiability claim: the policy's own action noise is an instrument, and only a restricted class of passive models fails. The programme's claim is unsupported. The testbed, gate and review record are released.

## 1. Introduction

An agent that runs continuously in a body needs a working model of which observation channels its actions influence. Call this its action-reachable observed support: the set of sensors whose readings a unit action moves by more than a threshold within a short horizon. A hidden cause can drive both the agent's actions and some sensors it does not control, so those sensors correlate with actions without being reachable. Actuators and sensors fail, so the support changes without announcement.

The starting point was a research roadmap I wrote in early September 2026 for a solo programme on persistent, adaptive agents, whose second candidate project proposed an "adversarial causal self-boundary" learned by intervention. A single-model red team of that roadmap, run before the protocol of Appendix A existed, found that the central hypothesis, intervention beats correlation for discovering what an agent controls, had already been tested and confirmed: Liu, Cheng and Bogdan (2026) showed that randomising actions recovers the controllable boundary in the static case, including under distractors that mimic controllable variables, and proved the estimator's invariance to confounders. Their design is a one-shot, two-branch experiment with a dedicated probing policy. What it does not cover is a boundary that changes during deployment, distractors synchronised with the policy's actions through a shared cause in a sequential setting, and calibration of the estimate during transitions. The claim tested here sits at that intersection: that passive residual monitors detect body change quickly but attribute control wrongly under a shared-cause confounder, while a sign-randomised interventional estimator ranks the controllable support correctly at a 5 percent probe budget, insensitive to the confounder, at a measurable cost in alarm speed.

The contribution is a negative result with a reusable testbed. Two experiments and one analysis, each run by three independent implementations or derivations with the per-number exceptions flagged where they occur, show that the claim is unsupported on the testbed built to confirm it: its attribution half is IBD's result in an online form, and its adaptation half was never tested under confounding on the channels the primary scored, because the one design that put confounding and change together did so on channels the confounder could not reach. The verification protocol and the errors it caught are in the appendices. Each table and figure traces to an archived input, implementation, captured output and adjudication through a file map released with the archive; the historical freeze hashes in Table A1 are round-log assertions and are the exception.

## 2. Setting

### 2.1 Generator

The reference generator draws instances of a linear-Gaussian structural causal model from a seeded configuration family. Latents are a body block b (four components), a downstream block d (two) fed by the body, an exogenous world block w (four), and a distractor block x (ten or thirty). A scalar context u follows an AR(1) process with autocorrelation 0.8. The policy is linear feedback on the body channels plus a context term plus noise, clipped. Actions enter the body with a delay of zero or two steps. Half the distractors are children of u, so they correlate with actions through the shared cause; none has an action parent. Observation channels are one per latent plus four padding channels, all with additive observation noise. A nonlinear family N replaces the linear body drive with a saturating tanh and a clipped quadratic self-term and is certified by empirical boundedness and stationarity rather than a spectral radius. Figure 1 draws the plant.

{{figure:plant}}

Figure 1. The plant of the frozen generator (family L). Solid edges are the structural equations; the dashed grey edge is the policy's feedback from the body channels; the action noise entering a is the instrument that Section 3.3 relies on. The context u reaches the observation layer only through the confounded half of the distractors, so the pre-event support (b and d channels; b alone at delay 2) and the confounded channels are disjoint, which is the mechanism of error 3 in Appendix B and the reason Experiment 2's confounding benefit was zero by construction. The dashed red edge G_b exists only in the body-confounded plant analysed in Section 3.3 and was never built. Source: `figures/make_figures.py`, checked against the contract's structural equations.

Each instance is certified before use: closed-loop spectral radius on the delay-augmented state, saturation fraction, a confounding witness (maximum action-distractor correlation at least 0.4) that vanishes under randomised actions, a faithfulness floor on nonzero coefficients, agreement between graph reachability and zero-noise interventional response on every latent, and, from the second experiment onward, a structural guarantee that the confirmatory event removes at least one observed channel from the support. Instances failing certification are resampled at the next sub-seed and the count is recorded. The ground truth is an oracle in the evaluator: the operational effect of each unit probe on each latent at each horizon, from which the observed support follows through assignment, gain and availability. The confirmatory event is complete loss of actuator 0 at step 1000 of a 2000-step episode.

### 2.2 The two estimators

**Sequential IBD.** Every twentieth step the estimator replaces the policy's action with a unit probe on one actuator, sign and actuator drawn in balanced pre-randomised blocks independent of state. For each channel, horizon and actuator it computes a tie-corrected Mann-Whitney rank-sum statistic (Mann and Whitney, 1947) contrasting signed increments after positive probes against those after negative probes over a trailing window of 500 steps, and reports the maximum absolute statistic over horizons and actuators. Its raw statistic never sees a label, a reward or the event time; the calibrated-probability tier, which was never run, would consume a harness-fitted calibrator trained on oracle labels. This is an in-task, budgeted departure from IBD's one-shot two-branch design: there is no baseline branch and no dedicated probing policy, and none of IBD's guarantees are inherited.

**Delay-aware passive comparator.** A frozen linear one-step predictor of the observation from the previous observation, the current action and two action lags, ridge-fitted on fault-free episodes of the same instance with standardised features. Its support baseline is the iterated-prediction sensitivity of each channel to the action over horizons one to three. In Experiment 1 its change statistic was the shift in the mean of standardised innovations over a trailing window, by analogy with a CUSUM on residuals (Page, 1954; Basseville and Nikiforov, 1993). Experiment 2 replaced that, for the reason given in Section 3.1, with a score-type statistic on the covariance between innovations and lagged actions, whitened by the fit-split action covariance.

A probed variant of the comparator, run on the identical probe-carrying stream, was specified to separate having interventions from using them. It was optional and was not scored, so that mechanism is untested here; in particular the second statement of Section 4 cannot separate "probes are unnecessary on this event" from "probes are being wasted on this event".

### 2.3 Measures

The primary outcome is a threshold-free AUC of an estimator's raw per-channel statistic against the oracle support at fixed offsets after the event, primary offset 500 steps, scored per episode, paired by instance and cell, with intervals clustered by instance; ten instances and four episode seeds per cell. The confounding benefit is the difference in the two arms' AUC gap between the confounder-present and confounder-absent conditions, the absent condition being the same instance and noise streams with the confounder's coupling set to zero. A competence floor requires the comparator's AUC without confounding to have a lower interval bound of at least 0.85 in every cell, so that a benefit cannot come from a broken baseline. Experiment 1 scored the AUC over all observation channels. Experiment 2 scored it over the pre-event support only: which channels the agent controlled before the event remain controlled after it, so that a channel-constant statistic scores exactly 0.5 and the full-channel AUC becomes a secondary measure.

Each experiment was run by three independent implementations of both estimators, written from the specifications alone by three AI systems (Claude, Codex and Gemini) on one frozen generator; the protocol is in Appendix A. Where a number below comes from fewer than three implementations, it says so.

## 3. Results

### 3.1 Experiment 1: full-channel ranking

Three independent implementations agreed to within Monte Carlo error on every number. Table 1 gives the base cell.

| Quantity (offset 500, ten distractors, delay 0, confounder present) | Claude | Codex | Gemini |
|---|---|---|---|
| Sequential IBD AUC | 0.800 | 0.815 | 0.831 |
| Passive comparator AUC | 0.691 | 0.688 | 0.675 |
| Passive comparator AUC, confounder absent | 0.875 | 0.878 | 0.863 |
| Confounding benefit | +0.187 | +0.204 | +0.190 |
| Benefit, thirty distractors, delay 2 | +0.240 | +0.237 | +0.228 |

Table 1. Experiment 1 on frozen version 0468104f6431b050; ten instances, four episode seeds per cell. Lower 95 percent bounds on the base-cell benefit, clustered by instance: 0.155, 0.153, 0.158. This generator keyed its noise streams with a per-process salted string hash, so the three implementations ran the same specification and configuration seeds but not the same trajectories; one reviewer's own code moved the base-cell benefit from +0.187 to +0.210 across two hash seeds. The key was made deterministic before Experiment 2, which is why Experiment 2 agrees to three decimals and Experiment 1 only to Monte Carlo error.

The perturbation set over coupling and noise scale is in Table 1b.

| Coupling × noise scale (seed 0, ten distractors, delay 0) | Codex | Claude | Gemini |
|---|---|---|---|
| 0.5 × 0.5 | +0.204 | +0.183 | +0.175 |
| 0.5 × 1 | +0.234 | +0.221 | not run |
| 0.5 × 2 | +0.210 | +0.207 | +0.198 |
| 1 × 0.5 | +0.028 | +0.032 | not run |
| 1 × 1 | +0.101 | +0.126 | not run |
| 1 × 2 | +0.143 | +0.147 | not run |
| 2 × 0.5 | +0.075 | +0.035 | +0.067 |
| 2 × 1 | +0.128 | +0.081 | not run |
| 2 × 2 | +0.157 | +0.106 | +0.137 |

Table 1b. Experiment 1 confounding benefit per perturbation configuration at offset 500, one instance each, no interval. Aggregate over the nine configurations as clusters (Codex): +0.142 with lower bound 0.090, below the 0.10 margin; pooled over all three offsets the adjudication recorded individual values from −0.015 to +0.25. These are Experiment 1 numbers: the passive statistic was the one the same experiment found defective, the baseline failed the competence floor, and the three implementations did not share trajectories, so the table describes where the margin failed and is not evidence for the surviving claim. Gemini ran a subset of the grid.

Three things followed. The interventional arm was reproducible, at 0.80 to 0.85 across distractor levels, delays and the perturbation set, and insensitive to the confounder. The confounding benefit cleared the pre-declared margin of 0.10 in every base cell, but not on the perturbation set, where the aggregate lower bound was 0.090 and individual configurations ran from −0.015 to +0.25. And the result was inadmissible, because the competence floor failed: without confounding the comparator's lower bound was 0.64 to 0.83 against the required 0.85, in every base cell for two implementations and in ten of twelve cell-offsets for the third.

The cause was identified analytically by Codex and measured by the other two. Under a centred policy, losing an actuator does not shift the mean of the predictor's innovations; it changes their variance and their covariance with the action. The comparator's change statistic was a mean-shift test and therefore could not see the event, and the loading term alone ranked the support at 0.99 without confounding. The baseline was not weak; it was specified with a statistic blind to the change it was meant to detect.

A fourth finding, from the same runs, was worse for the design. The generator did not guarantee that losing actuator 0 removed any observed channel from the support, and on 60 to 70 percent of frozen instances it removed none; all three implementations found this. The primary was therefore mostly a test of static structure. One implementation measured what that means. With the confounder absent, on the three instances of ten where the event did change the support, a per-channel vector fixed at fit time scored 0.975. It had never seen the scored episode or the event. The interventional arm scored 0.774 in the same cell and the comparator 0.845. The delay-2 subgroup, four instances, gives 0.969 against 0.882 and 0.831. That figure is single-model and was not reproduced. What all three reported is that the event usually changes nothing.

### 3.2 Experiment 2: ranking over the pre-event support

I adopted six changes in response (decision D-11 in the archive). The first had two parts: certify the event structurally so that it always removes at least one channel, and score the primary over the pre-event support only, so that a channel-constant statistic scores exactly 0.5. The others: replace the comparator's change statistic with the covariance score; seal a held-out set of confirmation seeds behind a hash commitment; implement family N; run every estimator's alarm clock from reset; fit every learned artefact per instance. Fresh-context Claude agents redrafted both estimator specifications against the new contract, and a new version was frozen.

Experiment 2 reproduced to three decimal places across the three implementations. Table 2 gives the family L base cells.

| Cell (offset 500) | Sequential IBD, present and absent | Comparator, present | Comparator, absent | Benefit |
|---|---|---|---|---|
| Ten or thirty distractors, delay 0 | 0.813 | 0.879 | 0.863 | −0.017 |
| Ten or thirty distractors, delay 2 | 0.687 | 1.000 | 1.000 | 0.000 |

Table 2. Experiment 2 on frozen version 38d161e762a3de76; ten instances, four episode seeds per cell. Lower 95 percent bounds on the comparator's absent AUC at delay 0 were 0.70 to 0.73 depending on the implementation's interval estimator, which the contract had not fixed. The channel-constant control scored exactly 0.500 in every cell. The static loading vector scored 0.422 at delay 0 and 0.200 at delay 2.

The benefit was zero because the pre-event support contains only body and downstream channels, the confounder enters only the distractor block, and the absent condition keeps the policy unchanged. All three implementations found this and verified that the present and absent observation streams coincide on every channel the primary scores; I inspected the generator source and agree with the argument, without an independent execution. The interventional statistic, which reads each channel's increments in isolation, is therefore identical across conditions. The comparator's small present-absent difference at delay 0 comes through its fit: its predictor regresses each channel on all observation channels including the distractors, so the fitted coefficients differ between conditions even though the scored streams do not. The re-posed primary measured adaptation on channels the treatment provably cannot reach. I had recommended that primary without checking the channel sets against each other; a one-line check would have caught it (Appendix B, error 3).

The passive comparator beat the interventional arm in every family L cell and every perturbation cell. With the covariance score, noticing that a controlled channel has gone quiet is a matter of watching innovations correlate with actions, which the passive arm does at every step while the probed arm sees about six probes per sign per actuator in its window. At delay 2 the comparator was perfect on every instance; note that the delay-2 cells score a different estimand from the delay-0 cells, since with a support horizon of three steps and a two-step delay no propagation hop survives, so the pre-event support there is exactly the four body channels on every draw and contains no downstream channel. On family N, five seeds with wide intervals, the ordering reversed: sequential IBD 0.84 against the comparator's 0.73 at delay 0, with the comparator's competence floor failing there. Family N was a reproduction target, not part of the exit condition, and five seeds cannot settle the sign.

Two further defects were found three of three. The lost channel is, by the construction that guarantees the event changes something, the dominant body component of actuator 0, typically the strongest pre-event channel; a static loading vector therefore scores below chance, and its negation, an event-blind and probe-free statistic, scores 0.80 at delay 2 against the interventional arm's 0.687. And losing actuator 1 removes no channel on any seed, so the benchmark tests one hand-wired coordinate. Two implementations also showed that the covariance score is not blind before the event: on fault-free episodes it ranked the support at 0.55 to 0.66 in every cell, above chance, because the closed loop induces action-innovation covariance the null model does not account for.

The confounding effect was still visible, but only in the secondary full-channel measure: the comparator's static loading ranked confounded distractors as controlled, scoring 0.73 to 0.80 with the confounder present against 0.96 to 0.98 without it, while the interventional arm scored 0.75 to 0.87 across the four base cells and moved by at most 0.013 between conditions (the Experiment 2 adjudication's earlier figure of 0.85 to 0.87 was a delay-0 read, corrected by erratum). These secondary numbers are from two of the three implementations; the third's secondary read was found to be taken at the wrong step and was excluded.

### 3.3 Analysis: identifiability when the confounder reaches the body

The natural repair is a plant in which the context also drives the body, so that confounding and change act on the same channels. I had routed the programme toward it on the premise that passive support tracking would then be non-identifiable in principle, and before building it asked the three systems to derive, in the population limit, whether passive support tracking is then non-identifiable in principle, what the frozen comparator converges to, what the probe contrast identifies, and what a single execution round could confirm. Write the body-confounded plant as

  u_t = ρ_u u_{t−1} + ε^u_t,  a_t = W_o o_t + W_u u_t + ε^a_t,  b_{t+1} = A_b b_t + B a_{t−τ} + G_b u_t + ε^b_t,

with u never observed and G_b the new coupling. The three derivations were reconciled to the same four conclusions in adjudication: Codex and Claude derived them directly; Gemini's stated theorem concerned the apparent coefficient of a no-latent estimator, and its accompanying remark conceded the same knife-edge condition for equality of the full observational law.

First, exact non-identifiability is a knife-edge, not an open set. The observational law of (o, a) at all lags contains the independent action noise ε^a, which acts as an instrument: the covariance between the body and the action has a discontinuity at the causal lag τ that the smooth AR(1) confounder path cannot produce, and it pins B separately from G_b. Exact confusion between an actuator loss and a support-preserving change in G_b requires the action noise to vanish in the affected direction. The premise I had adopted was false. The instrument is weak at the contract's own constants, action noise 0.1 against context noise 1.0, so identifiability in the population limit says little about what a latent-modelling passive method would achieve at the window sizes used here; one derivation put the support-flipped twin about ninety steps of evidence away, another noted that in finite samples the two laws are close to indistinguishable.

Second, what fails on an open set is the model class the claim is about: any predictor without a latent context variable. Its fitted action coefficient converges to

  β_a → B + κ G_b W_uᵀ  (delay 0),  κ = v_u / (σ_a² + v_u ‖W_u‖²),  v_u = Var(u_t | the predictor's own past-measurable regressors) ≥ σ_u²,

so a channel with a small true entry of B and a large entry of G_b W_uᵀ is labelled controlled when it is not, on a set of parameters with non-empty interior. With a causal delay the confounding term is spread across the predictor's lag slots and attenuated by the confounder's persistence over each lag; the three derivations bookkeep that case differently and only the delay-0 form is reproduced here. The lower bound on v_u holds for every past-measurable conditioning set, which is why no depth of action lags repairs the bias.

Third, the frozen comparator cannot distinguish an actuator loss from a change in G_b: its change score diverges as √n under both, and under body confounding the confuser's signal is comparable to or larger than the loss's, on channels the loss never touches.

Fourth, the sign-randomised contrast identifies the column of B at the first reachable horizon regardless of G_b, W_u and ρ_u, drops to zero under loss, and is unchanged under a change in G_b.

The one prediction whose sign all three fixed in advance is the confuser dissociation of Table 3.

| Plant | Frozen passive monitor | Sign-randomised probing |
|---|---|---|
| Confounder reaches the body (G_b ≠ 0) | reports false loss of support | invariant |
| Confounder does not reach the body (G_b = 0) | exactly blind to the change | invariant |

Table 3. Population-limit response to a support-preserving change in the confounder's coupling, in G_b or in the policy's context gain W_u, by plant and arm. Derived by three systems and reconciled in adjudication, one having initially concluded the opposite on the identifiability question. The table covers a confounder-coupling change only. The response to an actual actuator loss under body confounding was not settled: one system predicted the passive arm still wins, one predicted the probe arm wins, and one said the sign is not determined without further inequalities. Two of the three rescored the body-confounded plant at 3 on the roadmap's five-point novelty scale, the same as the repaired benchmark paper, and the third reframed what is unoccupied about it as body confounding plus a restricted estimator; one of the three made the referee's obvious rebuttal, why not fit a state-space model with the confounder as a latent AR(1), a design requirement, and proposed answering it with a deconfounded passive third arm.

### 3.4 Relation to prior work

Three reviewers scored four candidate claims on the roadmap's one-to-five novelty scale after reading the IBD paper in full and, in two cases, the active fault-diagnosis literature (Table 4).

| Candidate claim | Codex | Gemini | Claude |
|---|---|---|---|
| Attribution only, online, at a 5 percent probe budget | 3 | 2 | 2 |
| The negative adaptation result on its own | 1 | 1.5 | 1 |
| A combined benchmark-and-findings paper | 3 | 3.2 | 2.5 (3 if both endpoints share one regime) |
| A plant in which the confounder reaches the controlled channels | 4 (the question only; no evidence) | 3.8 | 3.5 |

Table 4. Novelty scores from the prior-art review (round 7 in Appendix A). After the identifiability analysis of Section 3.3, two of the three rescored the last row at 3 and the third reframed its unoccupied condition.

The attribution result is IBD's Proposition 3.3 (invariance to confounders) in an online form; the IBD paper's Section 3.2 states that any confounder-independent probe distribution is valid, which covers the sign-randomised variant. The negative adaptation result is the textbook condition of passive fault detection: active input design earns its cost only when normal closed-loop data are not diagnostic (Willsky, 1976; Heirung and Mesbah, 2019). The combined benchmark-and-findings paper reaches a 3 only after the event is repaired and both endpoints are measured under one confounding regime; after Section 3.3, two of the three rescored the body-confounded plant at the same level and the third reframed what is unoccupied about it. All three rejected the sentence "interventions buy attribution, not adaptation" as a finding: the two results were measured on different channel sets under different regimes, so they do not constitute a dissociation. After the identifiability analysis, no candidate claim scored above 3 with any reviewer, which is the basis for stopping at a technical report.

## 4. What the results support

**Sign-randomised probing, online and at a 5 percent probe budget, was not degraded by the shared-cause confounder that reduced a frozen passive residual monitor's full-channel AUC by about 0.2 in the base cells.** The passive monitor's loss came from crediting confounded distractors with control; the probed estimator's own score barely moved between conditions, 0.851 against 0.863 at delay 0 and 0.753 against 0.751 at delay 2 on ten distractors in Experiment 2. The gap was measured on the full channel set twice, on different passive statistics: by three implementations in Experiment 1 on the comparator's full score (0.691 against 0.875 in the base cell; the probed arm 0.80 to 0.83; the benefit did not clear its margin on the perturbation set), on a statistic the same experiment found defective and a baseline that failed the pre-declared competence floor, so that half is inadmissible under the contract's own rule; and by two implementations in Experiment 2 on the loading-only secondary, a fit-time vector that never sees the scored episode (0.73 to 0.80 against 0.96 to 0.98), which is the measurement the statement rests on. These are two estimators measured once each, not one quantity replicated. This is a replication of IBD's principle in a sequential setting, not a new result.

**On the linear family studied, a passive delay-aware covariance monitor equals or beats sign-randomised probing at ranking which controlled channel an actuator loss removed.** Measured once by three implementations. The caveats are load-bearing: the confounder did not reach the scored channels, the lost coordinate was chosen by construction to be dominant, the event usually removed one channel, the delay-2 cells where the passive arm is perfect score a four-channel body-only estimand, and the ordering reversed on the nonlinear family on five seeds. The result is best read as a diagnosis of the event, and of the value of probes when ordinary closed-loop data are already diagnostic, rather than as a general fact about interventions.

**When a body-reaching confounder is present, the failure of passive support tracking is a property of a model class, not of the information set.** Derived by three systems in the population limit. Predictors without a latent context variable are systematically wrong on an open set; a passive method that models the context can in principle recover the coupling through the policy's own action noise, which at the contract's constants is a weak instrument, so the practical gap is a finite-sample question the derivations did not settle.

What the results do not support is the claim the programme was built to test: that an interventional estimator tracks a changing controllable boundary better than a passive one under confounding. On this generator the claim is unsupported. Its attribution half is IBD's result, and its adaptation half was never tested under confounding on the scored channels, because the only design that put confounding and change together did so on channels the confounder could not reach. What would reopen the question is a preregistered execution round on a plant where the confounder reaches the scored channels, with the confuser dissociation of Table 3 as the primary and a latent-modelling passive third arm whose finite-sample power at the contract's weak action-noise instrument would itself be a result. Nothing in this report is evidence for how that round would come out.

## 5. Limitations

- The generator is one linear-Gaussian family with a scalar context, plus one nonlinear variant run on five seeds whose result reversed the linear family's ordering.
- All results are on development seeds; the sealed confirmation set was never opened, and no confirmatory run exists.
- Agreement between implementations of one specification on one generator is evidence that the specification is implementable, not evidence of external validity.
- The alarm channel, its false-alarm calibration and the calibrated-probability tier were never run; every result here is a threshold-free ranking. The probed comparator was not scored.
- The per-episode primary in Experiment 2 was an AUC with one or two negatives against three to five positives. Its lattice has at most six values when one channel is lost and nine when two are. The interval estimator was never specified. That is why the competence-floor verdict at delay 0 is undetermined rather than failed.
- The comparator's ridge constant was selected on development outcomes in Experiment 1, and its covariance score ranks above chance before any event.
- The Experiment 1 attribution benefit did not clear its margin on the perturbation set, and Experiment 1's implementations did not run the same trajectories.
- The gate at the final frozen version exits 0, but three reviewer-written mutants survive it. One widens the primary metric's channel set undetected, because every fixture happens to satisfy the containment the metric assumes. The mutation runner iterates the metric tests only, so no mutant against the generator can be registered.
- Specification defects found in Experiment 2, including colliding episode-seed registries between the two estimators and an interface that could not carry per-instance artefacts across episodes, were recorded but not repaired, because no further version was frozen.
- Five of the readiness protocol's six conditions were never satisfied (Appendix A). No version was readiness-certified.
- The identifiability result of Section 3.3 is a population-limit statement. The instrument it relies on, the policy's own action noise, is weak at the contract's constants, so the finite-sample gap between a latent-modelling passive method and the probed estimator is unmeasured, and the third arm proposed in Section 4 is a proposal, not a prediction.
- The adjudicating session that drafted the contract, the prompts and the adjudications shares a model family with one of the three reviewers, and no run of this report's own review had more than two model families (Appendix A).

## 6. Reproducibility and availability

The archive contains every prompt, review, adjudication, frozen manifest and hash; the contract through version 3.9; the interface specification through version 5; both estimator specifications with their superseded drafts; the reference generator with families L and N; the reference implementations of the metrics; the test gate (66 tests and 47 mutants at the final frozen version, with the surviving mutants listed in the Experiment 2 adjudication); and the three Experiment 2 implementations of both estimators with their captured output. A file map traces each table and figure in this report to the archived input, implementation, captured output and adjudication. The confirmation-seed commitment is recorded; the secret was never opened.

The gate runs under a Python 3.12 interpreter with the pinned NumPy from the requirements file and refuses any other interpreter; the requirements file cannot install Python itself, so a reader must provide 3.12. A stale Python 3.14 virtual environment that a reviewer had left inside the gate directory, and the bytecode caches from three interpreters, were removed before publication; the archive as published has not been run from a clean checkout, and the gate result quoted above is from the author's machine. No per-version snapshot of the archive was retained, so the historical freeze hashes in Table A1 are assertions from the round log and are not recomputable from the archive as it stands; the archive today hashes to the final frozen version plus the decision entries added after it. A public release should be accompanied by a repository whose commits fix this from that point on.

Repository: `github.com/danieljfrazer-ops/action-reachable-support-benchmark` (archival DOI via Zenodo to be minted on release). Documents are under CC BY 4.0, code under MIT.

## 7. Disclosure

The specifications, simulator, gate, round prompts and adjudications were drafted by a Claude (Anthropic) session acting as my agent; the two estimator specifications were drafted by separate fresh-context Claude agents from that session's adjudicated decisions; the reviews, implementations and derivations in each round came from Codex (OpenAI), Gemini (Google) and another fresh-context Claude agent, working from identical prompts under the protocol of Appendix A. I set the question, made every design decision and estimand choice from the adjudicating session's recommendations, ran the Codex and Gemini sessions, and directed each step. This report was drafted by the same Claude session from the archived adjudications, reviewed against the archive by a fresh-context Claude agent and by a cross-model review tool (Appendix A), and edited and approved by me. The errors in Appendix B are mine. No part of the work was funded.

## Appendix A. Verification protocol

One protocol governed the eight review rounds. Its rules, as they ran (round 9, the review of this report, is listed in Table A1 for completeness and did not run under the three-family rule):

- **Freeze.** A version is a listed set of files with one SHA-256 hash over their concatenation. No file in a frozen version is edited while any reviewer is working on it. Repairs land only after all reviewers have reported, and produce a new version. Rounds 1 to 6 reviewed frozen versions; rounds 7 and 8 reviewed the archived record without a new freeze.
- **Three model families, one prompt.** Each round the identical prompt went to Codex (OpenAI), Gemini (Google) and a fresh-context Claude agent (Anthropic), Opus in every round whose adjudication names the model. Round 2 used a fourth Claude-family reviewer on a different model (Fable, the model that ran round 0); the round-3 prompt asked for a different Claude model, although the round-3 adjudication records Opus. The Claude reviewer was started without memory of previous rounds each time; the Codex and Gemini sessions were run by me and were not certified fresh. Reviewers could read each other's reports only after writing their own. In execution rounds each reviewer implemented both estimators from the specifications alone.
- **Adjudication separate from review.** One Claude session, acting as my agent, drafted the roadmap, the contract, the interface specification, the prompts and the adjudications. Separate fresh-context Claude agents drafted the two estimator specifications and redrafted them after round 5; they worked from the contract, the interface specification, the round-5 adjudication and the D-11 decision record, and they neither reviewed nor adjudicated. That session never reviewed or implemented. Two weaknesses of the design as run: the adjudicating session shares a model family with one of the three reviewers, and the specification agents implemented its adjudicated decisions rather than forming an independent channel.
- **Executable exit criteria.** The readiness protocol set six conditions for a version. (1) No normative item lacks a test identifier. (2) Every registered mutant makes at least one test fail, and a reintroduced historical bug fails the gate. (3) An independent black-box acceptance suite, written by an agent other than the builder from the interface specification alone, passes. (4) A hand-computed reference case matches both the pipeline and the reference implementation. (5) A runtime pilot has recorded per-cell durations. (6) The three-reviewer convergence rule is satisfied. Only condition 6 was met: the convergence rule ran in rounds 1 to 8. The gate's exit code tested condition 2's mutant clause and nothing else. Nothing in the gate reads the coverage matrix, which at the final frozen version still lists four uncovered normative groups, so condition 1 failed. The historical-bug clause and conditions 3, 4 and 5 were never attempted. No version was readiness-certified.
- **Single-model results are unverified.** Any simulation run by one system, including by the adjudicating session, was treated as unverified until a second system reproduced it.
- **Design changes need a round.** No change to what is measured was treated as confirmed without a cross-model round on it. The rule did not require a round before adoption, and error 3 in Appendix B is what that cost.

| Round | Date | Type | Frozen version reviewed | Gate as frozen | What it did |
|---|---|---|---|---|---|
| 0 | 6 Sep | single-model prose | none | none | Red team of the original roadmap; prior-art check; found IBD |
| 1 | 6 Sep | prose | version 1, c197652c0d8e846b | gate present; count not logged | Review of the re-aimed plan (roadmap v4, contract v3) |
| 2 | 6 Sep | prose + gate | version 2, d23960e6da441de7 | 17 tests, 8 mutants | Contract v3.1, interface v2; four reviewers |
| 3 | 7 Sep | prose + implementation | version 3, e662b7429b6b347d | 25 tests, 23 mutants | Contract v3.3, IBD spec draft 2; each reviewer built its own simulation |
| 4 | 7 Sep | prose + implementation | version 4, 442cc4b7da691ca0 | 34 tests, 35 mutants | Both estimator specs; each reviewer implemented both arms on instances of its own |
| 5 | 7 Sep | execution (Experiment 1) | version 5, 0468104f6431b050 | 47 tests, 40 mutants | Three implementations on one frozen generator |
| 6 | 7 Sep | execution (Experiment 2) | version 6, 38d161e762a3de76 | 66 tests, 47 mutants | Same, on the re-posed primary; families L and N |
| 7 | 8 Sep | prose | archived record | | Novelty of what survived, against the literature (Section 3.4) |
| 8 | 9 Sep | derivation | archived record | | Identifiability under a body-reaching confounder (Section 3.3) |
| 9 | 9 to 15 Sep | prose, outside the protocol | archived record | | Review of this report (two model families per run) |

Table A1. The rounds. Hashes are the first sixteen hex digits of the SHA-256 over each version's manifest in manifest order, as recorded in the round log at the time of the freeze. The manifest and `freeze.py` were introduced as a repair after round 2, so rows 1 and 2 record hashes taken before that convention existed and are not manifest-order digests. No per-version snapshot was retained: files were superseded in place, so every row is an assertion from the round log. Running `freeze.py` on the archive today prints 1fcd1c5784a78fda, which reproduces no row, because the manifest includes the decision log, which gained two entries after round 6 closed and was overwritten in place; every other version-6 manifest file is byte-identical to the reviewed version. Gate counts are for the version as frozen, not after the repairs the round prompted; row 3's count is confirmed by a round-3 reviewer's run on that hash. The whole programme ran on one laptop; the round-6 runs took 5 to 21 minutes each, and reviewer implementation and analysis time was not recorded.

**Review of this report.** Two things reviewed it against the archive: a fresh-context Claude Opus agent, and a cross-model review tool. The tool ran ten times: once on draft 1 with the archive out of scope, once on each of drafts 1 to 7, once on a proposal for the figures, and once on the restructured draft; every run's report is archived under `review9-tool/`, and one run number is unused because I aborted that run before any reviewer reported. The Anthropic reviewer reported on every run. The OpenAI reviewer reported on drafts 1 to 3 only; it declined the first run for lack of the archive and errored on every later run. The Google reviewer reported on drafts 4, 5 and 6 and on the restructured draft, was out of scope on the first run, quota-exhausted on drafts 1 to 3, and returned nothing readable on draft 7 and the figures proposal, so those two runs had one usable family. No single run had all three families. On every draft, one of the two families that reviewed it is the family that drafted it. The Claude agent that fact-checked the restructured draft against draft 10 and the archive was a fresh context, and its findings with checked evidence were applied before this version was built.

## Appendix B. Errors and their provenance

The execution rounds and the derivation round exposed four design errors of mine, each of which changed the benchmark's estimand or its verdict. The review of this report identified two further errors in the adjudication step, one of them a rejection made in round 4 of a finding that round 5 established. Table B1 gives the provenance of all six.

| Error | Entered | Named | Established | Rejected in adjudication first | Cost |
|---|---|---|---|---|---|
| 1. Change score blind to the change | version 4 | round 4 (Gemini, R4-GM-02) | round 5, three of three | yes | one extra round |
| 2. Event not certified to change the support | the first generator, frozen at version 5 | round 5, three of three | round 5 | no | the Experiment 1 primary measured static structure |
| 3. Primary scored channels the treatment cannot reach | version 6 (D-11.1a) | round 6, three of three | round 6 | no | Experiment 2's exit condition unattainable |
| 4. Premise that passive tracking is non-identifiable in principle | D-12 (8 September) | round 8 (Codex and Claude) | round 8 adjudication | no | none built |
| 5. Adjudication: rejecting R4-GM-02 | round-4 adjudication | round 9 (report review) | round 5 had established the finding | not applicable | error 1's extra round |
| 6. Adjudication: secondary range narrowed to a delay-0 read | round-6 adjudication | round 9 (report review) | erratum, 10 September | not applicable | a wrong range in the archive for two days |

Table B1. Provenance of the six errors: the version or step in which each entered, the round that first named it, the round that established it, whether the adjudication step rejected it before it was established, and what it cost.

**1. A change score that could not see the change.** The comparator's innovation-mean-shift statistic was specified by analogy with a CUSUM on residuals. Under a centred policy an actuator loss leaves the residual mean unchanged. The statistic entered at version 4 and survived round 4, where three models implemented both arms on instances of their own and disagreed by 0.2 AUC on the comparator. Round 4 found the comparator structurally incapable, three of three, and the next version rewrote its features and loading. One round-4 reviewer (Gemini, finding R4-GM-02, high) also named the change term itself, showing by simulation that under a zero-mean policy lost and retained channels receive the same score. I rejected the mechanism in adjudication, on the ground that the identity is exact only in the population while the statistic uses a finite-window mean, and folded the observation into the structural rewrite. The finding was correct and the rejection was wrong. The blindness was established in round 5, the first round on a single frozen generator, by one reviewer's algebra and two reviewers' measurements.

**2. A primary that mostly measured static structure.** The generator's event was not certified to change anything, and on most instances it did not. A fit-time vector beat both arms. Found in round 5, which was the first round in which the generator was frozen and the event therefore testable. Any change-detection benchmark needs a control that never sees the change and must be shown to score at chance.

**3. A primary the treatment could not reach.** My repair restricted scoring to the pre-event support, which contains no confounded channels, so the benefit was identically zero. The two redrafting agents encoded it from the adjudication without checking the channel sets, and the execution round that followed was the first place it was checked, by all three reviewers. Before adopting a primary, confirm on the generator that the treatment changes the streams the primary scores.

**4. A premise a derivation refuted.** I routed the programme toward a body-reaching confounder on the belief that passive support tracking would be non-identifiable there in principle. All three systems showed it is not: the policy's own action noise is an instrument, so exact non-identifiability is a knife-edge. Found in round 8, a prose round whose three derivations ran to several hundred lines each and initially disagreed on whether the equivalence set was open before adjudication reconciled them; the cheapest of the four, since nothing was built.

**5 and 6. Adjudication errors.** No cross-model round caught either, because the adjudication step is the one place in the protocol with a single model. The first is the rejection of R4-GM-02 above. The second is that the round-6 adjudication narrowed the interventional arm's secondary full-channel AUC to 0.85 to 0.87, a delay-0 read of outputs that also contain 0.75 at delay 2; the range stood in the archive for two days and was found by the review of this report, not by any round (erratum of 10 September 2026 appended to the round-6 tally). In both cases the reviewers had produced the evidence and the adjudicating step misread it.

## References

Basseville, M. and Nikiforov, I. V. (1993). *Detection of Abrupt Changes: Theory and Application*. Prentice Hall.

Heirung, T. A. N. and Mesbah, A. (2019). Input design for active fault diagnosis. *Annual Reviews in Control*, 47, 35–50.

Liu, J., Cheng, A. and Bogdan, P. (2026). Discovering what you can control: Interventional boundary discovery for reinforcement learning. arXiv:2603.18257v2.

Mann, H. B. and Whitney, D. R. (1947). On a test of whether one of two random variables is stochastically larger than the other. *Annals of Mathematical Statistics*, 18(1), 50–60.

Page, E. S. (1954). Continuous inspection schemes. *Biometrika*, 41(1/2), 100–115.

Willsky, A. S. (1976). A survey of design methods for failure detection in dynamic systems. *Automatica*, 12(6), 601–611.
