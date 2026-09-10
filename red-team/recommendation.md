# Recommendation

Written 6 September 2026, after the red team ([findings.md](findings.md)) and a second research round ([research-round-2.md](research-round-2.md)). Answers three questions: is there a genuine research programme here, what shape should it take, and what should change in the roadmap.

## 1. Is there a novel research programme here?

**Yes, with a specific shape.** Not "new architectures for better memory and self-awareness." That framing is where the crowded, well-funded groups are, and every architectural candidate in the report has closer precedent than it credits. What is open, laptop-feasible, and connected to the stated goals is a set of **intersection questions about an agent whose own boundary, resources and world all change while it runs**, answered with **benchmarks, phase diagrams and empirical findings** rather than new modules.

The evidence for "yes":
- The intersection {interventional boundary estimation} x {boundary changes during deployment} x {distractors synchronised with actions} x {latency, false-alarm and calibration metrics} is not occupied. Every neighbour covers two of the four (see research-round-2, section B).
- "Does an auxiliary self-model improve adaptation and calibration when the body changes?" appears unasked. Self-modeling as a regulariser (Premakumar 2024) and self-interventional learning (Aug 2026) were both done on static networks; the robotics self-model work has no self-prediction loss and no calibration metric. This is the honest, publishable version of the self-awareness interest.
- The community is moving toward this. Three workshops in September 2026 alone are titled around continual learning for embodied agents, memory for robot foundation models, and continually self-improving robots.

The evidence for caution:
- Two of the report's three flagship candidates (R1 memory routing, R5 proactive compute) are now mostly occupied. R5 lost its last gap in June 2026. R1 is publishable as a benchmark but is the most crowded and least distinctive direction, with the Titans group and a dozen linear-attention papers per quarter in the same space.
- Any *method* claim from a solo laptop programme will be scooped. Benchmark, finding and negative-result claims will not be, because they are tied to a testbed the author controls.
- "Self-awareness" cannot be a claim in any paper. It can be the motivation, and "functional self-modeling" can be the measured construct.

## 2. What changed my view since the report

| Report position | Red-team position | Reason |
|---|---|---|
| R1 (hidden-volatility memory) is the first paper and flagship | Optional fast side paper, or folded into R3 | Occupied at three levels; crowded; not connected to the self-modeling goal |
| R2 (adversarial self-boundary) is the second project, hypothesis "intervention beats correlation" | **Flagship and first paper**, hypothesis re-centred on *change* and *calibration* | IBD (Mar 2026) already confirmed the old hypothesis; the change-and-calibration gap is real and laptop-scale |
| R5 (proactive compute) is a standalone paper, novelty 4.0 | Component of the integrated agent, novelty about 2 | Metareasoning literature plus Jensen et al. 2024 plus Foerster group Jun 2026 |
| No self-modeling paper | **New paper 2: auxiliary self-model under boundary change** | Only unoccupied thread that directly serves the self-awareness interest |
| One synthetic symbolic stream, then a dynamical environment | One testbed from the start, symbolic facts embedded in it | One environment with ground truth for boundary, volatility and cost supports all papers and is itself a contribution |
| AutoResearch after protocol freeze, MLX-first | Same, plus: step budgets not wall-clock; ShinkaEvolve or CodeEvolve as alternatives; use only for the architecture stage | Fanless throttling corrupts fixed-time budgets; evolutionary search is now open-source and local |
| Audience undecided | Lifelong-learning agents and developmental/embodied AI (CoLLAs, ICLR workshops, DevAI-style workshops) | Baselines and terminology follow from this choice |

## 3. Recommended programme shape

**One testbed, five measured constructs, four papers.** Details and protocol in [roadmap-v2.md](roadmap-v2.md).

The testbed is a small continuing vector environment: an agent with N controllable dimensions (its "body"), M distractor dimensions that can be synchronised with its actions, a world with entities whose facts change at hidden per-entity rates, and an explicit cost model where sensing, acting, retrieving, learning and simulating each consume a resource and the world advances during internal work. Everything has ground truth: the true controllability mask, the true hazard rates, the true cost ledger. This is the AffectWorld and IBD scale, which is a laptop scale.

The measured constructs, in the order they are safest to publish:

1. **Boundary calibration under change.** How fast and how reliably does each estimator (correlation, prediction error, mutual information, IBD-style intervention, Lipson-style self-model) detect that the boundary changed, at what false-alarm rate under spoofed contingency, and how well calibrated is its confidence during the transition? Paper 1. Benchmark plus findings.
2. **Self-model as an aid to adaptation.** Add an auxiliary self-prediction head (own hidden state, own next-step error, own controllability mask). Does it speed boundary re-estimation, reduce forgetting of the old body, and improve calibration, at what cost? Paper 2. Finding, possibly negative. Extends Premakumar and the Aug 2026 self-interventional work into a changing agent.
3. **Fast-self versus slow-world memory.** With self mappings and world facts both changing at hidden rates, does routing them to different timescales help, and where is the phase boundary? Paper 3. Absorbs R1's routing question and R3, in a setting where the two timescales have a reason to differ. Uses MAD-style synthetic methodology and effective state-size as the budget.
4. **Resource-costed scheduling.** Which internal action to run, when, under causal cost. Paper 4 or part of the integrated agent. Baselines: Foerster gating policy, Jensen et al. 2024 rollouts, fixed schedules.
5. **Integrated persistent agent.** Only after 1 to 3 have independent results.

Optional side paper at any point: the R1 symbolic-stream phase diagram, if a fast first preprint is wanted for momentum. Hardened protocol is in [r1-protocol-hardening.md](r1-protocol-hardening.md).

## 4. How the self-awareness goal maps onto measurable work

A ladder of functional constructs, each with a metric and a literature. Climb it; never claim the top rung.

| Rung | Construct | Metric | Nearest literature |
|---|---|---|---|
| 1 | Boundary: what I control | Controllability-mask accuracy, detection latency, false alarms, calibration | IBD 2026; Gold & Scassellati 2006 |
| 2 | Body: how my actions map to effects | Self-model prediction error after change; recovery time | Lipson group 2019 to 2025 |
| 3 | State: what will happen to me | Calibrated forecast of own future error and resource state | Homeostatic RL; AffectWorld 2026 |
| 4 | Introspection: what I will do and what I know | Self-prediction beats other-prediction; abstention calibration | Binder et al. 2024; Premakumar 2024 |
| 5 | Phenomenal self-awareness | No agreed test | Not a claim in this programme |

The programme covers rungs 1 to 4 with ground truth. That is as close to the stated goal as honest science currently gets, and it is a coherent story for a paper series.

## 5. Decisions that need the author, not me

1. **Flagship choice.** Boundary-under-change first (recommended) or R1 memory first (faster to build, more crowded).
2. **Environment representation.** Vector observations with explicit distractor dimensions (recommended, IBD-comparable) versus pixel observations (more general, much slower on a laptop).
3. **Framework.** MLX-first (recommended for models; M5 accelerators help) versus PyTorch-MPS (easier custom recurrences). Environment in numpy either way.
4. **Time box.** Paper 1 by mid-February 2027 for ICLR workshops and CoLLAs; that gives about 22 weeks including R0.
5. **Whether to keep the umbrella name "Persistent Adaptive AI."** It is fine for the repository. For papers, the safer umbrella is "self-modeling under non-stationary embodiment" or similar; it says what is measured.

## 6. What not to do

- Do not build the fully integrated agent first.
- Do not claim a routing or self-modeling *method* is new without the baselines listed in the roadmap; the trivial baselines are the ones that kill method claims.
- Do not run fixed-wall-clock experiments on the Air; use step or operation budgets.
- Do not use the word "self-aware" in a title, abstract or claim.
- Do not start an AutoResearch loop before the evaluator is frozen and the R0 positive and negative controls pass.
