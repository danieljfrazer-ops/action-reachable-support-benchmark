# Round 7 verdict: what survives after attribution and adaptation separate

**Reviewer:** Codex  
**Date:** 8 September 2026  
**Scope:** reasoning and literature review only; no code or simulation. I did not use review-folder material or simulation code as evidence. I read the requested local documents in the specified order. I accessed and read Liu, Cheng & Bogdan, arXiv:2603.18257v2, including its method, assumptions, experiments and appendices. Source-access details are at the end.

## Bottom line

**Opinion.** The claim that survives is narrower than “interventions improve adaptation”:

> Under a shared-cause confounder, sparse sign-randomised action probes provide an online, channel-level attribution signal that rejects false controllability assigned by a frozen passive residual model; when an actuator loss already leaves an obvious action–residual signature, however, a delay-aware passive monitor can track the lost channel at least as well without spending probes.

That is worth a paper **as a benchmark-and-findings contribution**, not as a new causal-discovery principle and not as the negative adaptation result alone. The scientifically useful object is the separation of two tasks that the earlier design conflated: (i) attributing whether a channel is action-reachable in the presence of confounding, and (ii) detecting that a previously reachable channel has become unreachable. IBD already establishes the principle behind (i); classical active fault diagnosis already establishes that test inputs are useful only when ordinary closed-loop data are not sufficiently diagnostic. The paper's new contribution would therefore be a sequential, budgeted evaluation protocol and an empirical map of when intervention is necessary.

**Recommendation:** D-12 **B**, with one final, tightly bounded execution only. Do not headline the adaptation result as a universal negative. Option C is the more novel *next scientific question*, but it currently has no evidence and would restart the project rather than finish Paper 1.

## 1. Candidate claims

The scores use the roadmap's 1–5 convention: 1 is essentially occupied or unsurprising; 3 is a defensible incremental or benchmark contribution; 5 is a clearly unoccupied central contribution.

### (a) Attribution only: online and sequential at a 5% probe budget

**Closest prior work.** Liu, Cheng & Bogdan, [“Discovering What You Can Control: Interventional Boundary Discovery for Reinforcement Learning,” arXiv:2603.18257v2](https://arxiv.org/abs/2603.18257v2), 2026. IBD randomises the action mechanism, compares baseline and interventional rollouts dimension by dimension, applies multiple-testing correction, and demonstrates that passive selectors retain confounded distractors while IBD recovers an action-reachable mask. Its default is a one-time, batch probing phase of 80 baseline and 80 intervention trajectories of length 200 (about 32,000 environment steps), after which the mask is fixed. It explicitly assumes that the causal structure is stationary during probing.

A relevant but less task-specific neighbour is Elahi et al., [“Adaptive Online Experimental Design for Causal Discovery,” ICML 2024](https://proceedings.mlr.press/v235/elahi24a.html), which makes intervention selection sequential and sample-efficient for fixed-confidence DAG recovery, but does not estimate an RL agent's observed-space controllability boundary or handle a changing plant.

**What is actually new.** The present result turns IBD's separate batch experiment into an always-on estimator embedded in task interaction: only 5% of environment steps are replaced by signed probes; support is ranked continuously; causal delays are handled explicitly; and the result is evaluated at fixed offsets under a deployment-time change. The +0.19 to +0.24 full-channel AUC advantage is also a direct comparison with a frozen passive residual monitor under a shared-cause confounder, rather than IBD's downstream-return comparison with feature selectors. What is *not* new is the reason it works: randomising the action breaks the confounding path. That is IBD's central proposition and experiment.

**Novelty: 3/5.** A material online, low-duty-cycle and sequential extension of IBD, but the causal identification claim and confounded-distractor result are already occupied.

### (b) The negative adaptation result on its own

**Closest prior work.** Heirung & Mesbah, [“Input design for active fault diagnosis,” *Annual Reviews in Control* 47 (2019), 35–50](https://doi.org/10.1016/j.arcontrol.2019.03.002). This review distinguishes passive diagnosis from active diagnosis by injected test signals, treats change detection and fault isolation as established problems, and stresses that usefulness depends jointly on the test signal, diagnostic algorithm, uncertainty and information already present in normal closed-loop data. It covers online/moving-horizon designs and CUSUM/SPRT-based diagnosis. In other words, the field does not claim that active probing must beat a competent passive detector on every readily diagnosable fault.

**What is actually new.** Within this particular action-reachability benchmark, a simple delay-aware action–residual covariance statistic equals or beats the sign-randomised probe statistic at ranking which previously controlled channel was lost. The result is reproducible across three independent implementations. But the event removes one channel in 32/40 draws, the lost coordinate is selected to be a dominant pre-event loading, and the confounder does not reach any channel in the scored set. Thus the result is better read as a benchmark diagnosis—“this event gives the passive arm an easy sufficient statistic”—than as a general fact about interventions.

**Novelty: 1/5.** Reproducible and useful internally, but unsurprising against active-fault-diagnosis theory and inseparable from the current event construction.

### (c) Combined benchmark and findings: “interventions buy attribution, not adaptation”

**Closest prior work.** No single checked paper combines both halves. The closest pair is Liu et al. 2026 for interventional attribution under confounded distractors and Heirung & Mesbah 2019 for the conditional value of injected signals in online fault diagnosis. Kocacoban & Cussens, [“Online Causal Structure Learning in the Presence of Latent Variables,” arXiv:1904.13247v2](https://arxiv.org/abs/1904.13247), also tracks changing causal structure online with latent variables, but uses observational causal-structure updating rather than sparse action interventions and does not target controllability support.

**What is actually new.** The benchmark makes attribution and adaptation separately scoreable against channel-level ground truth, puts passive and interventional estimators on the same online stream and probe budget, and exposes an estimand-dependent reversal: interventions suppress confounded false support over the full channel set, while passive covariance suffices for the present controlled-channel loss. The repeated redesign failures are themselves evidence for a methodological lesson: a support score can be mostly static, a change score can ignore the confounder by construction, and selecting the lost coordinate by pre-event dominance can make static controls anti-predictive. A publishable version would convert those lessons into reusable benchmark invariants and mandatory controls, not narrate the project's debugging history as if it established generality.

**Novelty: 3/5.** The synthesis and evaluation design are plausibly new and useful, while each underlying mechanism is known; significance depends on correcting the event bias and demonstrating the reversal beyond one easy linear construction.

### (d) Option C: the confounder reaches controllable channels, so adaptation under confounding is the test

**Closest prior work.** The nearest combination remains Liu et al. 2026 plus the active-fault-diagnosis literature represented by Heirung & Mesbah 2019. Liu et al. tests latent common causes of action and *exogenous* distractors, but assumes stationary causal structure during probing. Active fault diagnosis tests changing actuator/sensor modes under disturbance and feedback, but is generally formulated as discrimination among explicit plant/fault models rather than online discovery of an observed-space action-reachability mask under a latent common cause. Kocacoban & Cussens 2019 supplies the closest “changing structure plus latent variables” formulation, without action interventions or the RL boundary target.

**What is actually new.** If a latent cause drives both the policy action and a body channel, and actuator loss removes the action-to-channel edge while leaving the latent path intact, passive action–residual association may falsely preserve support precisely on the channels whose status changed. A randomised action probe can, in principle, identify the disappearance of the causal action edge. This makes confounding affect the adaptation estimand rather than only irrelevant distractors. The decisive quantity would be an interaction: the intervention advantage for post-change support tracking with the shared cause present minus that advantage with it absent. This is the cleanest continuation of the original R2 gap.

**Novelty: 4/5 (question/design only, not a result).** The exact intersection of sparse interventional boundary tracking, deployment-time edge deletion and latent common causes appears unoccupied in the sources checked, but the present rounds provide no evidence for it and the adjacent control literature is mature.

## 2. Venue fit and the status of the negative finding

**Opinion.** In its current evidential state, this is not an ICLR-main-track method paper: the attribution mechanism is too close to IBD, the ICLR 2027 full-paper deadline is 25 September 2026, and the adaptation evidence is still tied to a biased event. The official [ICLR 2027 author guidance](https://iclr.cc/Conferences/2027/AuthorGuidelines) confirms that deadline.

The best fits are:

- **TMLR**, for a careful benchmark-and-empirical-study paper. Its [scope](https://www.jmlr.org/tmlr/editorial-policies.html) explicitly includes experimental studies that yield insight into learning-system behaviour, applications that expose strengths and weaknesses, new learning tasks, and reproducibility studies. Its correctness-over-fashion posture suits an honest null/reversal, provided the claims are narrow.
- A future **NeurIPS Evaluations & Datasets track**, if the generator, oracle, event-balancing rules, estimands and controls become a reusable artifact. The [2026 track statement](https://blog.neurips.cc/2026/03/23/introducing-the-evaluations-datasets-track-at-neurips-2026/) explicitly welcomed negative results, critical analyses, benchmark failure studies and evaluation redesign. The 2026 deadline has passed; this is venue fit, not a claim about a currently open 2027 call.
- An **ICLR or continual-learning/embodied-agents workshop** for the smaller attribution-only paper. I did not find an announced ICLR 2027 workshop-paper call as of 8 September 2026, so no deadline should be asserted.
- **IFAC SAFEPROCESS** becomes a plausible audience for Option C only if the work engages fault-diagnosis baselines and control assumptions seriously. The [2027 symposium](https://conferences.ifac-control.org/safeprocess2027/general-information/) is explicitly centred on fault detection, diagnosis, supervision and safety.

Would a referee accept the negative finding? **Opinion: not by itself, and not with the universal wording “interventions do not buy adaptation.”** A referee could accept it as one result in (c) if three conditions hold: the event is topology-designed with at least two lost channels and balanced pre-event rank; the same conclusion survives across multiple plant families/event types with a fair batch-IBD and active-fault-diagnosis baseline; and the paper states the conditional conclusion—passive data suffice when the fault creates a direct residual-covariance signature. Without those changes, the obvious review is that the benchmark made the passive problem easy and removed confounding from the scored channels.

## 3. D-12 recommendation

**Recommendation (opinion): choose B.** Freeze two named endpoints, repair the event by topology and rank balancing, implement the already-adopted specification fixes, and allow exactly one more execution round. Predeclare that its purpose is validation of the benchmark-and-findings paper, not another opportunity to invent a superiority claim.

**Single strongest reason for B:** it is the only option that preserves the reproduced +0.2-AUC attribution result while removing the known construction that makes the adaptation conclusion scientifically weak; it can turn two task-specific observations into a defensible estimand-separation benchmark.

**Single strongest reason against B:** after six rounds and several outcome-informed redefinitions, another freeze risks looking like adaptive benchmark design around observed results; a referee may regard even a clean round 7/8 confirmation as development evidence unless genuinely untouched instances, environments and analysis choices are held out now.

Why not A: it stops the design churn, but the negative headline is not strong enough under the current biased event. Why not C: it is the most novel next experiment, but it discards the certification design and asks a new question before Paper 1 has converted its existing result into a reliable artifact. If B fails its final frozen run or does not generalise beyond family L, choose A and write a narrower technical report rather than repairing again. C should then be a separately preregistered Paper 2/Paper 1b project.

## 4. Evidence that would change this verdict

I would raise (a) from 3 to 4 and consider an attribution-led paper if a frozen evaluation showed all of the following: comparable accuracy to batch IBD at a much lower *total interventional-step* budget; valid anytime or sequential error control; robustness across nonlinear control tasks and multiple delays; a probe-budget/accuracy/control-cost frontier; and downstream benefit or avoided false routing, not AUC alone. A fair comparison must charge IBD's baseline and intervention rollouts and must also compare a batch version of the sign contrast at the same samples.

I would raise (c), and accept the negative adaptation result as central, if the passive win survived untouched seeds on rank-balanced topology-designed losses with `n_lost >= 2`, at least two qualitatively different plants, multiple loss/remap/gain events, and controls showing that neither a static pre-event vector nor event time alone predicts the answer. The conclusion should vary in the predicted direction when diagnostic information is removed; otherwise “when passive data suffice” has not been identified.

I would switch the D-12 recommendation from B to C if either (i) an exact prior work were found that already performs sparse online IBD under the same deployment and budget constraints, collapsing (a)'s novelty, or (ii) a small preregistered analytic construction established that the shared-cause-to-body plant creates non-identifiability for every stated passive information set but identifiability under sign randomisation, with a feasible safety/probe budget. Conversely, a literature example already doing online active diagnosis of a changing action-to-observation edge under latent common cause would reduce (d) below 4.

I would abandon the paper claim and choose A-as-technical-report if the +0.2 attribution benefit failed on untouched generator families, disappeared against a stronger passive method with the same information set, or depended on development-selected constants/instance construction. Evidence that the event-balancing repair reverses the passive adaptation result would not be a failure; it would show that the current negative was a construction artifact and should be removed from the headline.

## 5. Disputes with `round6-adjudication-and-tally.md`

1. **The phrase “interventions do not buy adaptation” is too broad.** The evidence supports: “on this actuator-0 loss, in this plant, with confounding excluded from the scored pre-event support, the passive covariance monitor equals or beats this 5% sign-probing estimator.” Active fault diagnosis gives strong prior reason to expect the value of probes to depend on whether normal inputs are already diagnostic. The unqualified sentence reads like a domain-level conclusion that was not tested.

2. **Section 7's statement that neither reproduced finding is the claim the programme set out to confirm conflicts with the current roadmap claim.** Roadmap v4.7 K4 explicitly claims that passive residual monitors attribute control wrongly under a shared-cause confounder and that sign-randomised intervention ranks support correctly at a 5% budget, with a cost. Round 5/6's full-channel result is direct evidence for that attribution half. It is fair to say the repaired D-11 adaptation primary failed, or that the *original programme motivation* sought changing-boundary superiority; it is not fair to say the attribution result is absent from the current Paper 1 claim.

3. **“The passive comparator wins the re-posed task” is numerically correct but needs the construction qualifier whenever used as synthesis.** Round 6 itself documents why: present and absent streams are identical on the scored channels; loss usually removes one dominant coordinate; the static control is therefore biased below chance; and delay changes the effective estimand. Those are not side limitations—they bound the external meaning of the win.

I do **not** dispute the arithmetic reproduction, the zero confounding benefit on the D-11.1a primary, the comparator-floor failure, the lost-channel counts, the mutant findings, or the conclusion that the D-11 exit condition is unattainable as posed.

## Sources checked and access limitations

- Liu, Cheng & Bogdan, [arXiv:2603.18257v2](https://arxiv.org/html/2603.18257v2): HTML and PDF accessible; I read the paper's main text, stated assumptions, experiments and appendices relevant to probing cost and boundary recovery.
- Heirung & Mesbah, [2019 review](https://doi.org/10.1016/j.arcontrol.2019.03.002): I accessed a complete author-hosted PDF and checked its treatment of passive versus active diagnosis, change detection, sequential tests, online/moving-horizon input design and closed-loop control. The ScienceDirect landing page itself returned HTTP 403 when opened directly.
- Elahi et al., [ICML 2024](https://proceedings.mlr.press/v235/elahi24a.html): PMLR page and paper text accessible; checked the problem statement, algorithm and claims.
- Kocacoban & Cussens, [arXiv:1904.13247](https://arxiv.org/abs/1904.13247): arXiv text accessible; checked the abstract, scope and method description.
- Venue pages linked in section 2 were accessible and checked on 8 September 2026. I could not find an official CoLLAs 2027 CFP or an ICLR 2027 workshop-paper call, so I do not state dates for them.
