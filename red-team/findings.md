# Findings

Ranked by severity. Each finding gives: what the report claims, the attack, the evidence found, and what to change. Links to sources are collected in [evidence.md](evidence.md).

---

## High severity

### F1. R1's novelty score (4.5) is inflated: per-item timescale assignment under unknown volatility is occupied at three levels

**Claim under attack.** "Hidden-volatility memory routing" has "no close integrated precedent" and its defensible gap is "per-item, oracle-free timescale assignment under unknown hazard rates, reversals and equal budgets." Closest territory named: Titans, TTT, Nested Learning, OAKS.

**Attack.** The report searched the long-context and LLM-memory literature but not the non-stationary learning, computational neuroscience, or agent-memory literature, where the same problem is stated almost verbatim.

**Evidence.**
- *Normative theory exists.* Learning the hazard rate of change online and adapting retention to it is a solved Bayesian problem: Wilson, Nassar & Gold, "Bayesian online learning of the hazard rate in change-point problems" (Neural Computation 2010); Behrens et al. 2007 on volatility-scaled learning rates. Humans do it implicitly: de Jong, Wilhelm & Akyürek 2024 show forgetting speed adapts to "probing hazard", which is the report's "delayed query" manipulation by another name.
- *Per-instance learned timescales exist.* Jain & Shenoy, "Instance-Conditional Timescales of Decay for Non-Stationary Learning" (AAAI 2024) trains a scorer that assigns each instance a mixture of decay timescales for drifting data and extends it to continual learning.
- *Per-parameter adaptive decay at the environment's timescale exists.* FADE (arXiv 2604.27063, Apr 2026) meta-learns per-parameter decay rates matched to the non-stationarity timescale, and explicitly frames itself as the weight-level counterpart of activation-level forget gates.
- *Per-key learned forgetting exists in sequence models.* Kimi Delta Attention, Gated DeltaNet-2 (May 2026), FG2-GDN (Apr 2026) all learn per-key or per-channel forgetting rates.
- *Learned write/update/delete decisions exist.* Memory-R1 (2026) trains a memory manager to choose ADD/UPDATE/DELETE/NOOP with RL on eventual answer reward, which is the report's "delayed-value memory writes" candidate.
- *Stale-knowledge benchmarks predate OAKS.* StreamingQA (ICML 2022) and EvolvingQA already measure updating and removal of outdated facts; the report's "stale-answer rate" has cousins there.

**What survives.** Nobody found appears to compare recurrent state, fast weights, episodic store, and slow weights *as routing targets* for the same item under matched budgets with an explicit hidden-hazard generator. That is a benchmark and phase-diagram contribution, which the report already half-concedes ("possibly a small routing method").

**Fix.** Re-score novelty to about 3. Rewrite the R1 contribution as "budget-matched phase diagram across memory families under hidden volatility" with the router as secondary. Add the Bayesian hazard-learning router and the Jain & Shenoy scorer as *baselines*, not related work. Cite the neuroscience framing so a reviewer from that field cannot say it was missed.

---

### F2. R2's primary hypothesis has already been tested and confirmed by Interventional Boundary Discovery (March 2026)

**Claim under attack.** R2 hypothesis: "intervention-aware estimates retain boundary calibration under spoofed contingency and drift better than correlation or prediction error." Closest territory named: empowerment, predictive agency, robot self-detection.

**Evidence.**
- Liu, Cheng & Bogdan, "Discovering What You Can Control: Interventional Boundary Discovery for RL" (arXiv 2603.18257, Mar 2026, revised May 2026): uses randomized actions as interventions, per-dimension two-sample tests with FDR correction, evaluated in 12 continuous-control settings with up to 100 distractors *including distractors that mimic controllable state variables*, matching an oracle in 11/12 and beating mutual information, forward-model and gradient-sensitivity baselines.
- "Proprioceptive-visual correspondence enables self-other distinction in humanoid robots" (arXiv 2606.13222, Jun 2026): self-model learned without identity labels, tested against morphologically identical robot distractors.
- Gold & Scassellati 2006 (AAAI): contingency-based robot self-recognition with mirror and other-robot conditions. The report cites a 2020 Frontiers "artificial self" paper but not this lineage.

**What survives.** IBD does not appear to test a boundary that *changes over time* (actuator remapping, sensor faults, morphology drift, re-introduction of old morphologies) or calibration of the boundary estimate as it changes. Delayed and stochastic effects are also not obviously covered. That is a real gap.

**Fix.** Rewrite R2 around non-stationarity and calibration: "Which estimators detect a *changed* self-boundary fastest, with what false-alarm rate, and how well calibrated is the estimate during transition?" Use IBD as the strongest baseline. Drop "intervention beats correlation" as the headline; it is now a known result.

---

### F3. R5 ("proactive counterfactual compute") is placed in the wrong literature and its score (4.0) is unjustified

**Claim under attack.** Closest territory named: adaptive compute, Continuous Thought Machines, proactive LLM agents. Hypothesis: value-of-computation scheduling beats periodic polling and always-think policies under equal budgets.

**Evidence.**
- The report's own phrase "value of computation" is the name of a 35-year-old field: rational metareasoning (Russell & Wefald 1991; Hay, Russell et al. 2012; Lieder et al. 2014 on learned meta-level rewards; Budd et al. AAAI 2024 on learned VOC for planning; "Rational Metareasoning for LLMs", 2024).
- Jensen, Hennequin & Mattar, "A recurrent network model of planning explains hippocampal replay and human behavior" (Nature Neuroscience 2024): an RL agent learns *when* to run internal rollouts versus act, where rollouts cost time, and the learned policy triggers rollouts only when they improve outcomes. This is nearly the R5 design, on a laptop-scale task.

**What survives.** A *continuing* environment where missed external events have a cost during internal work, combined with consolidation and retrieval as schedulable actions, is a reasonable extension. It is an incremental extension of Jensen et al., not a new question.

**Fix.** Re-score to about 2.5. Cite metareasoning explicitly and frame R5 as "metareasoning in a continuing world with heterogeneous internal actions." Use Jensen et al. as the primary baseline.

---

### F4. "Equal state bytes and update FLOPs" is not a well-defined comparison across memory families, and the router has a structural advantage

**Claim under attack.** R1 compares learned routing against single-family baselines "at equal state bytes and update FLOPs."

**Attack.**
1. A router that can write to recurrent state, fast weights, an episodic store, *and* slow weights has access to the sum of four capacities. Unless the baselines are given the same total bytes in their single family, the router wins by capacity, not by routing. The report's own cited warning (Computationally Budgeted CL: simple uniform-memory baselines beat sophisticated methods at matched compute) applies to the report itself.
2. "State bytes" is incommensurable: KV cache bytes, a fast-weight matrix, an episodic key-value table, and slow weights have different read costs, write costs, and information density. Matching bytes does not match capacity.
3. "Update FLOPs" biases the result: writing to an episodic store is nearly free, a gradient step on slow weights is expensive. At matched update FLOPs the episodic tier will dominate, and the "router" will learn to use it for everything. That is a predictable outcome, not a finding.
4. Wall-clock is confounded by thermal state on a fanless laptop (see F8).

**Fix.** See [r1-protocol-hardening.md](r1-protocol-hardening.md). In short: match *total* bytes across all conditions, run per-tier and pairwise-tier ablations, report Pareto frontiers over (bytes, FLOPs, accuracy) rather than single points, and predeclare the expected episodic-dominance outcome as a hypothesis to test rather than a surprise.

---

## Medium severity

### F5. The "oracle hazard-aware router" is not an upper bound

Knowing each entity's true hazard rate does not determine optimal routing. Optimal routing also depends on the query-delay distribution, contention for capacity, retrieval cost, and the reversal structure. A learned router can beat the "oracle" on the training distribution, which will make the results narrative confusing. Either define the oracle as the solution of the known-hazard routing problem under the same budget (hard), or call it "hazard-informed reference policy" and drop "upper bound."

### F6. Generator leakage makes "oracle-free" weaker than it sounds

The router is meta-trained on streams from the generator family, so it can learn the generator's hazard prior and change-point statistics. It is oracle-free at test time but not at training time. The report defers a changed generator family to "after success." Move it into the primary evaluation: predeclare at least two held-out generator families (bursty non-Poisson changes, correlated entity changes, hazard distributions with different shape) and report transfer as a headline number. Otherwise a reviewer will say the router memorised the generator.

### F7. Missing baselines that could erase the contribution

- A Bayesian online change-point router with learned hazard (Wilson, Nassar & Gold 2010). Model-based, oracle-free, cheap. If it matches the learned router, there is no method contribution.
- A trivial empirical-hazard heuristic: per-entity hazard estimated as one over the mean observed inter-change interval, with time-to-live routing. Trivial baselines win embarrassingly often in this area.
- Jain & Shenoy's instance-conditional decay scorer.
- Memory-R1-style RL over memory operations.

### F8. Hardware confound: a fanless MacBook Air throttles 25 to 50 percent within 8 to 15 minutes of sustained load

The report proposes "equal wall-clock views", a "laptop energy proxy", and overnight unattended runs on a 32 GB MacBook Air. Sustained-load throttling on fanless Apple Silicon is well documented. Consequences:
- Wall-clock comparisons run sequentially are biased toward whichever condition ran first (cool chassis).
- Fixed-time AutoResearch runs (5-minute budget) are exactly the metric most affected: early trials in a session get more compute than later ones, so keep/revert decisions drift with temperature.
- "Energy proxy" numbers from a throttled versus unthrottled run are not comparable.
The report says it will *record* thermal conditions but does not address the *design* problem. Fix: interleave and randomise condition order, log clock frequency and thermal pressure per run, define a warm-up period before any timed run, report algorithmic budgets (bytes, operations, steps) as the primary comparison and wall-clock only as secondary. Consider whether the Air is the right machine for overnight work at all.

### F9. Metric definitions leave room for favourable reporting

- "Stale-answer rate" conflates ignorance with staleness. Use a four-way confusion: correct / stale (previously correct value) / wrong-other / abstain.
- "Adaptation lag" needs a definition when queries are delayed: lag measured from change event to first correct answer is only observable if queries arrive; report it conditional on query timing or use probe queries that do not enter the stream.
- "Calibration" on a symbolic stream: calibration of what output? Define it as the confidence assigned to the reported value against empirical correctness, and specify the proper scoring rule.
- "Retention at log-spaced delays" needs a stated maximum delay relative to stream length, or the longest bins will have too few samples to bound.

### F10. Scoring rubric has two axes, no anchors, and false precision

Novelty and feasibility are the only criteria. Missing: probability the hypothesis is true, value of the null result, scoop risk, and venue fit. Scores are author-assigned with no anchor descriptions for 1 versus 5, then rendered as a bar chart with a synthetic SQL "source." That presentation implies measurement. The report's own disclaimer is good; the chart works against it. Either add anchored rubric text or replace the chart with a plain table.

### F11. Scoop risk is high and unaddressed

Titans, Nested Learning, and Language Models Need Sleep are the same Google group (Behrouz et al.), publishing multi-timescale memory plus consolidation work at roughly quarterly cadence through 2026. FADE, Gated DeltaNet-2, KDA, Memory-R1, MemTier, MemRouter all landed in the first half of 2026. A solo laptop researcher on R1 or R4 will be scooped on any *method* claim. Benchmark, phase-diagram, and negative-result contributions are scoop-resilient; the roadmap should say so and shape R1 accordingly.

### F12. No timeline, effort estimate, or per-stage kill criteria beyond R0

Seven stages, R0 to R6, with no duration, no effort estimate, and no "stop if" condition after R0. For a solo researcher this is the most common way a roadmap dies. Add: target venue and deadline for R1 (e.g. CoLLAs, NeurIPS or ICLR continual-learning workshops), a time box, and a predeclared kill criterion (e.g. "if the trivial hazard heuristic is within one standard error of the learned router on two generator families, publish the benchmark and negative result and do not pursue the router").

### F13. Audience choice is listed as an open question but has already been made by the baseline suite

The report asks whether the audience is continual learning, long-context LM, developmental robotics, or artificial life. The R1 baseline list (Transformer-XL, RMT, SSM, TTT, Titans-style surprise, EWC/SI) is a long-context plus continual-learning suite. R2 is developmental robotics. The two first papers therefore target different reviewer communities with different expectations. Decide per paper and say so; do not leave it open.

---

## Low severity

### F14. Citation hygiene

- AffectWorld is named in the prose ("A 2026 interoceptive-attention study") but absent from the sources list. It is arXiv 2608.04232, "Interoceptive Attention as Dynamic Homeostatic Prioritization in a Foraging Agent" (Aug 2026).
- The OAKS source label uses a shorthand; the paper's title is "Can Large Language Models Keep Up? Benchmarking Online Adaptation to Continual Knowledge Streams" (Kim et al., ACL 2026; arXiv 2603.07392).
- Nested Learning is cited via a Google Research blog post rather than the paper.
- The "artificial self" and Gold & Scassellati lineage is under-cited for R2.

### F15. Precursor-transcript assumptions leak into the framing

The roadmap correctly refuses consciousness claims. But the two archived chats it grew from contain claims the roadmap never explicitly disowns, and they shape the vocabulary ("self-boundary", "viability", "interoception"). See [precursor-notes.md](precursor-notes.md). Recommend a "claims we will not make" section in the preregistration.

### F16. Presentation

The HTML renders the screening chart three times (responsive variants) and labels the artifact a "Data Analytics report." Harmless, but a reader skimming the archive may take the chart for data. The plain table version is better for a research document.

---

## Attacks that failed (kept for the record)

- **Citations.** All 22 listed sources resolve to the claimed works, including the three 2026 items most likely to be hallucinated (OAKS at ACL 2026, Language Models Need Sleep at arXiv 2606.03979, the autoresearch-mlx repo).
- **AutoResearch claims.** Verified against the repo: single editable `train.py`, fixed 5-minute wall-clock budget, validation bits-per-byte metric, NVIDIA GPU required and tested on H100, explicit note that results are not comparable across platforms. The MLX port has a `rigor.py` multi-seed bootstrap gate and documents run-to-run noise of about 0.03, as the report says. The port is young (6 commits at time of check, 1.8k stars).
- **"The original PoC is a replication."** Correct, and if anything understated; AffectWorld (Aug 2026) is even closer than the report says.
- **Protocol advice.** Freeze question and falsification criterion, separate exploratory from confirmation generators, locked evaluator, multi-seed, effect sizes, preserve null results, re-run novelty search before claims. Nothing to attack; this is the strongest part of the document.
- **Rejection of AI Scientist v2 as a starting point.** Reasonable and well argued.
