# Roadmap v2 (proposed)

A revision of the report's R0 to R6 roadmap incorporating the red team and round-2 research. The original roadmap is unchanged in `../persistent-adaptive-ai-research-roadmap.html`; this file is a proposal for the author to adopt, edit, or reject. Rationale is in [recommendation.md](recommendation.md).

Design rules carried over from the report and kept: freeze question, hypothesis and falsification criterion before the main run; locked confirmation generator separate from development; evaluator inaccessible to candidate code; multiple seeds with effect sizes; preserve every run including failures; re-run the novelty search before any public claim; no consciousness claims.

Design rules added: total-budget matching across conditions; held-out generator families in the primary evaluation; trivial and model-based baselines before learned ones; step or operation budgets instead of wall-clock on the Air; per-stage kill criteria; venue and date per paper.

---

## Stage 0: Testbed and reproductions (weeks 1 to 4, Sep to early Oct 2026)

**Build.** A continuing vector environment, numpy, deterministic under seed:
- Agent body: N controllable observation dimensions driven by K action dimensions through a configurable mapping (linear, then nonlinear), with delay and noise options.
- Distractors: M dimensions, of three kinds: independent noise; copies of the agent's own effects with lag (spoofed contingency); externally driven signals that mimic controllable statistics.
- World entities: E symbolic facts, each with a hidden change hazard, plus transient anomalies and reversals, queried with delayed probes. (This is the R1 generator, embedded.)
- Change events: actuator remap, sensor dropout or swap, morphology change (N or the mapping changes), each with ground-truth timestamps. Old morphologies can be re-introduced.
- Cost ledger: each sensing, acting, retrieval, gradient step and simulation step has a resource cost; the world advances a configurable number of steps during internal work.
- Ground truth exposed only to the evaluator: controllability mask over time, hazard rates, change timestamps, cost totals.

**Reproduce.** Three known results, as positive controls:
1. IBD's core finding: interventional mask discovery beats mutual information and forward-model baselines under static boundary with distractors that mimic controllable variables.
2. Premakumar's regularisation effect at small scale: an auxiliary self-prediction loss narrows the weight distribution of a small supervised network.
3. One continual-learning failure: a single-tier memory forgets stable facts under high-hazard traffic at fixed budget.

**Negative control.** A random estimator and a random router, reported in every table for the rest of the programme.

**Gate.** Deterministic generation; 5 seeds; all three reproductions match the published direction of effect; evaluator hashes locked. **Kill criterion:** if the reproductions do not match after 4 weeks, the gate result is the write-up and the environment is debugged before anything else.

---

## Paper 1: Boundary calibration under change (weeks 5 to 22, Oct 2026 to mid-Feb 2027)

**Working title.** Detecting and calibrating a changing self-boundary under spoofed contingency.

**Question.** When the set of dimensions an agent controls changes without warning, and distractors are synchronised with its actions, which estimators detect the change fastest, with what false-alarm rate, and how well calibrated is their boundary estimate during the transition?

**Estimators (baselines, none new).** Temporal correlation; prediction-error (forward model residual); mutual information / empowerment proxy; IBD-style randomised-intervention two-sample test with FDR; a Lipson-style learned self-model with residual monitoring; a Bayesian change-point detector over the controllability evidence (the model-based baseline that could win); random.

**Manipulations.** Change type (remap, dropout, morphology), change magnitude, distractor kind and count (0 to 100), effect delay and noise, re-introduction of a previous morphology, intervention budget available to the estimator.

**Predeclared metrics.** Mask accuracy over time; detection latency (steps from change to mask crossing a threshold); false-alarm rate during stationary periods; calibration of per-dimension controllability probability (Brier, ECE); recovery on re-introduced morphology (does the old boundary come back faster than the first time); intervention cost consumed.

**Hypotheses (falsifiable).**
- H1: interventional estimators keep the lowest false-alarm rate under spoofed contingency but have the highest detection latency because they need intervention budget after a change.
- H2: no single estimator dominates across change types; a phase diagram over (distractor count, effect delay, change magnitude) has at least two regions with different winners.
- H3: calibration degrades for all estimators during transition, and the model-based change-point detector is best calibrated.
Any of these failing is a result.

**Controls.** 10 seeds for confirmation; two held-out environment configurations (nonlinear mapping; bursty change schedule) generated and hashed before development ends; equal intervention budget across estimators; report per-estimator compute.

**Contribution type.** Benchmark plus empirical findings. No method claim.

**Kill criterion.** If by week 14 all estimators are indistinguishable within error on all manipulations, the environment is too easy or too hard; re-tune with the change magnitude sweep and publish whatever phase structure exists.

**Venue.** arXiv first; ICLR 2027 workshop (deadline expected early to mid Feb 2027) and/or CoLLAs 2027 (deadline expected Feb to Mar 2027). Fallback: DevAI or embodied-continual-learning workshops at NeurIPS 2027.

---

## Paper 2: Does a self-model help an agent adapt to its own change? (Feb to Jun 2027)

**Question.** Does an auxiliary self-prediction objective (predict own hidden state, own next-step error, own controllability mask) speed re-estimation of the boundary, reduce forgetting of a previous body, and improve calibration, and at what resource cost?

**Conditions.** Agent policy or forward model trained with: no auxiliary loss; hidden-state self-prediction (Premakumar); error self-prediction; mask self-prediction; all three. Matched parameter count and compute. Plus the best Paper 1 estimator as the non-learned reference.

**Predeclared metrics.** Paper 1 metrics, plus: weight-distribution width and effective parameter count (to test whether the regularisation effect transfers to agents); resource consumed by the auxiliary head; performance on the task itself (so the self-model is not free).

**Hypotheses.** H1: self-prediction narrows weights in the agent as in static nets. H2: mask self-prediction reduces detection latency after change. H3: hidden-state self-prediction does not help adaptation (the Aug 2026 self-interventional paper reported an incomplete self-model that did not beat direct strategies; a null here is expected and publishable).

**Contribution type.** Empirical finding, plausibly negative on H3. First test of self-modeling in a changing agent.

**Venue.** NeurIPS 2027 workshops (deadlines around Sep 2027) or CoLLAs 2027 if timing allows.

---

## Paper 3: Fast-self versus slow-world memory under hidden volatility (mid-2027 onward)

**Question.** When self mappings and world facts both change at hidden rates, does giving them separate memory timescales improve the retention/adaptation frontier at matched total budget, and where is the phase boundary?

This absorbs the report's R1 and R3. Use the hardened R1 protocol in [r1-protocol-hardening.md](r1-protocol-hardening.md): total-budget matching using effective state-size, MAD-style synthetic methodology, Bayesian hazard-learning and empirical-hazard baselines, Jain & Shenoy instance-conditional decay, held-out generator families, four-way answer confusion, probe-based lag.

**Contribution type.** Benchmark plus phase diagram; a routing method only if it beats the model-based baselines on held-out families.

This is the only stage where an AutoResearch-style or ShinkaEvolve-style loop is worth attaching, and only to screen candidate routing modules against the frozen evaluator with step budgets.

---

## Paper 4 or integration: Resource-costed internal scheduling (2028)

Metareasoning over heterogeneous internal actions (retrieve, learn, consolidate, roll out) in the continuing testbed, with the cost ledger live. Baselines: fixed schedules, surprise gates, Foerster et al. 2026 gating policy, Jensen et al. 2024 rollout policy. Contribution is incremental; publish only if a clear interaction with Papers 1 to 3 appears (for example, scheduling changes which boundary estimator wins). Otherwise it is a section of the integrated-agent report.

---

## Integrated persistent agent (2028)

Combine validated components. Every component keeps its independent ablation. The claim is narrower than the umbrella name.

---

## Cross-cutting

**Timeline summary.**

| Stage | Window | Output |
|---|---|---|
| Stage 0 | Sep to early Oct 2026 | Testbed, three reproductions, locked evaluator |
| Paper 1 | Oct 2026 to mid-Feb 2027 | arXiv preprint; workshop or CoLLAs submission |
| Paper 2 | Feb to Jun 2027 | arXiv preprint; workshop submission |
| Paper 3 | mid-2027 onward | arXiv preprint |
| Paper 4 / integration | 2028 | Technical report or paper |

**Hardware protocol.** 32 GB M5 MacBook Air, fanless. Warm-up before any timed run; log thermal pressure and clocks; randomise condition order; step and operation budgets as primary; wall-clock secondary and labelled. Models under 10M parameters. Environment in numpy; models in MLX (dense and fast-weight layers) or PyTorch-MPS (if custom recurrences are needed).

**Run ledger.** Append-only JSONL: code hash, environment config hash, seed, budgets, thermal log, metrics, outcome, including crashes.

**Novelty re-check.** Before each arXiv post, repeat the search for the exact task, metric and mechanism; add anything found to the related-work section and re-score.

**Claims discipline.** Each paper states its contribution type (benchmark, finding, negative result, method). Motivation may mention self-modeling and predictive processing. Claims mention only the measured constructs. The words "self-aware" and "conscious" do not appear outside the motivation paragraph, and there only as what is *not* claimed.
