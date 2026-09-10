# Research round 2: gap checks for the reframed projects

Performed 6 September 2026 after the red team, to answer "is there still a novel project here, and where?" Each item records what was searched, what was found, and what it does to the candidate.

## A. Proactive computation (R5)

| Work | Date | What it does | Effect on R5 |
|---|---|---|---|
| Muppidi, Darwish, Cope, Henriques & Foerster, "Finding the Time to Think: Learning Planning Budgets in Real-Time RL", arXiv 2606.26463 | Jun 2026 | Variable-delay real-time RL. Environment advances while the agent deliberates. A lightweight gating policy learns state-dependent planning budgets; beats fixed-budget and heuristic baselines on real-time Pac-Man, Tetris, Snake, Speed Hex, Speed Go; transfers to a two-GPU real-time setup. | Takes the "continuing world, deliberation costs environment steps" gap that survived round 1. Remaining gap: heterogeneous internal actions (retrieve, learn, consolidate, roll out) and explicit missed-event and false-alarm costs. This is now an extension, not a question. Novelty about 2. |
| "A Formal Metareasoning Model of Concurrent Planning and Execution", AAAI 2023 | 2023 | Formal model of planning while acting. | Further prior art for the framing. |

**Conclusion:** demote R5 from standalone paper to a component of the integrated agent. Use Foerster's gating policy and Jensen et al. 2024 as baselines when it is built.

## B. Self-boundary under change (R2)

| Work | Date | What it does | Effect on R2 |
|---|---|---|---|
| Kwiatkowski & Lipson, "Task-agnostic self-modeling machines", Science Robotics | 2019 | Self-model learned without morphology prior; adapts after damage. | Self-model adaptation under change exists, on physical robots, without distractors or calibration scoring. |
| Chen et al., "Fully body visual self-modeling of robot morphologies", Science Robotics | 2022 | Visual self-model as occupancy query; detects and adapts to damage. | Same. |
| Hu & Lipson, "Egocentric visual self-modeling for autonomous robot dynamics prediction and adaptation", npj Robotics; "Teaching robots to build simulations of themselves", Nature Machine Intelligence | 2025 | Self-model from one camera; detects deformed part, retrains, resumes task. | Same; damage detection but no false-alarm or calibration metrics and no spoofed contingency. |
| "Robust Embodied Self-Identification of Morphology in Damaged Multi-Legged Robots", arXiv 2506.19984 | Jun 2025 | Identifies damaged legs and updates model. | Same. |
| Hoffmann et al., "Body models in humans, animals, and robots: mechanisms and plasticity" | 2020 | Review; body-schema plasticity. | Vocabulary and framing for R2. |
| "Adapting the Behavior of RL Agents to Changing Action Spaces and Reward Functions", arXiv 2601.20714; time-varying actuator limits in MuJoCo (2604.02260) | 2026 | Non-stationary action effects in RL. | Non-stationary controllability exists as an RL adaptation problem, not as a boundary-estimation benchmark with distractors. |
| Liu, Cheng & Bogdan, IBD, arXiv 2603.18257 (round 1) | Mar 2026 | Interventional controllability mask, up to 100 distractors that mimic controllable variables. | Stationary boundary only. |

**Conclusion:** the intersection {interventional boundary estimation} x {boundary changes during deployment} x {distractors synchronised with actions} x {detection latency, false alarm, calibration metrics} is not occupied. Laptop-feasible: IBD-scale vector environments. This is the strongest remaining candidate and the closest to the stated self-awareness interest.

## C. Functional self-modeling (new thread)

| Work | Date | What it does | Gap it leaves |
|---|---|---|---|
| Premakumar et al., "Unexpected Benefits of Self-Modeling in Neural Systems", arXiv 2407.10188; Phil. Trans. R. Soc. A 2025 | Jul 2024 | Networks trained to predict their own hidden states as an auxiliary task become simpler and more regularised (narrower weight distributions, lower real log canonical threshold). MLPs, ResNets, embeddings. | Static supervised networks only. No agent, no changing body, no non-stationarity. |
| Tomaszewski, "Can Neural Networks Learn by Experimenting on Themselves? Self-Interventional Learning", arXiv 2608.14894 | Aug 2026 | Network perturbs its own structure, observes consequences, learns a predictive self-model; measured by held-out prediction error and Spearman correlation vs intervention budget. Learned self-model incomplete and not consistently better than direct empirical strategies. | Static networks; author states self-model did not beat simple baselines. |
| Binder et al., "Looking Inward: LMs can learn about themselves by introspection", arXiv 2410.13787; follow-ups "Me, Myself and pi" (2603.20276), "Emergent introspection is content-agnostic" (2603.05414) | Oct 2024 to Mar 2026 | Self-prediction as a measure of introspection in LLMs; a model predicts its own behaviour better than another model trained on its ground truth. | Frontier LLMs, prompting-based; not small agents and not embodied boundary. |
| Lipson lineage (section B) | 2019 to 2025 | Self-models of body for control. | No auxiliary self-prediction of internal state; no calibration of self-knowledge. |

**Conclusion:** "Does an auxiliary self-model (predict own hidden state, own future error, own controllability mask) improve adaptation speed and boundary calibration when the agent's body or sensors change?" appears unasked. It joins Premakumar (self-prediction as regulariser), IBD (controllability), and Lipson (change) in one laptop-scale experiment. It is the most distinctive thing this programme can do and the honest version of "self-awareness."

## D. Memory under hidden volatility (R1)

| Work | Date | What it does | Effect on R1 |
|---|---|---|---|
| Poli et al., "Mechanistic Design and Scaling of Hybrid Architectures" (MAD), ICML 2024; mad-lab | 2024 | Synthetic-task suite (in-context recall, fuzzy, noisy, selective copy, compression) predicts scaled performance; standard for architecture screening. | Provides the methodology R1 should adopt and cite. No volatility or delayed-query tasks. |
| "Quantifying Memory Utilization with Effective State-Size", arXiv 2504.19561 | Apr 2025 | Effective state-size metric across MAD tasks. | Gives a principled "state budget" definition; addresses finding F4 partially. |
| MQAR, S-NIAH and MK-NIAH with overwrites; Gated DeltaNet motivation | 2024 to 2026 | Key-overwrite recall tasks exist; delta rule is framed as erase-then-write. | "Facts change" is already a standard synthetic probe. Hidden per-key hazard, delayed queries, transient anomalies and equal-budget cross-family comparison are not. |
| "A Hippocampus for Linear Attention: An Exact Memory for What the Recurrent State Forgets", arXiv 2607.02303 | Jul 2026 | Hybrid recurrent state plus exact external memory. | The fast/episodic split is being actively built by others. |
| "Learning to Remember, Learn, and Forget in Attention-Based Models", arXiv 2602.09075 | Feb 2026 | Learned remember/learn/forget in attention. | Further crowding. |

**Conclusion:** R1 remains publishable as a benchmark plus phase diagram if done quickly and with the MAD methodology and effective state-size budgets. It is the most crowded and least distinctive of the candidates, and the least connected to the stated goals. Keep it as an optional fast first preprint, not the flagship.

## E. Tooling

| Item | Finding |
|---|---|
| AutoResearch (Karpathy) and MLX port | As in round 1. Fixed wall-clock budget is unsafe on a fanless Air; use step or operation budgets. |
| ShinkaEvolve (Sakana, Apache 2.0), OpenEvolve, CodeEvolve (arXiv 2510.14150) | Open-source evolutionary program search in the AlphaEvolve style. CodeEvolve reports matching AlphaEvolve on 5 of 9 benchmark problems and beating OpenEvolve and ShinkaEvolve on 6 of 9. All can drive a frozen evaluator with an LLM mutator; ShinkaEvolve added CLI-backed mutation for subscription models in May 2026. Same caveats as AutoResearch: candidate screening only, never evaluator editing. Useful for the architecture stage (fast-self / slow-world modules), not for benchmark papers. |
| MLX on M5 | M5 GPU neural accelerators give up to 4x prefill speed-up over M4 in MLX for large matmuls. Training small dense models in MLX is fine. Custom sequential scans (Mamba-style) lack optimised MLX kernels; prefer chunked or diagonal recurrences and fast-weight layers that reduce to matmuls. For sub-10M-parameter models the framework choice is secondary; numpy or PyTorch-MPS for the environment is fine. |

## F. Venues and dates (checked 6 September 2026)

| Venue | Deadline | Fit |
|---|---|---|
| NeurIPS 2026 workshop "Continual Learning in the Era of Foundation Models and Embodied Agents" | 8 Sep 2026 | Too soon for this cycle. Note the title: the community is moving toward embodied continual learning, which favours the R2 direction. |
| CoRL 2026 workshops "Memory for Robot Foundation Models" (25 Sep), "Continually Self-Improving Robots" (29 Sep) | Sep 2026 | Too soon; same signal about where interest is. |
| ICLR 2027 main conference | 25 Sep 2026 | Too soon. |
| ICLR 2027 workshops (proposals due 1 Oct 2026; paper deadlines typically early to mid Feb 2027) | ~Feb 2027 | Primary target for paper 1. |
| CoLLAs 2027 (2024 deadline was 15 Feb; 2026 CFP announced March) | ~Feb to Mar 2027, unannounced | Primary target for paper 1 or 2. Lifelong learning agents is the exact community. |
| ICML 2027 | ~late Jan 2027 | Ambitious for paper 1. |
| arXiv | any time | Post each paper on arXiv first; the report's advice on timestamping novelty applies. |

Sources for this round (in addition to those in evidence.md):
- https://arxiv.org/abs/2606.26463
- https://arxiv.org/abs/2608.14894
- https://arxiv.org/abs/2407.10188 and https://doi.org/10.1098/rsta.2024.0531
- https://arxiv.org/abs/2410.13787
- https://www.nature.com/articles/s44182-025-00031-6
- https://www.science.org/doi/10.1126/scirobotics.aau9354
- https://arxiv.org/abs/2506.19984
- https://arxiv.org/html/2601.20714
- https://proceedings.mlr.press/v235/poli24a.html and https://github.com/athms/mad-lab
- https://arxiv.org/pdf/2504.19561
- https://arxiv.org/html/2607.02303v1
- https://github.com/SakanaAI/ShinkaEvolve , https://arxiv.org/abs/2510.14150
- https://machinelearning.apple.com/research/exploring-llms-mlx-m5
- https://aiworkshoptracker.com/ , https://lifelong-ml.cc/Conferences/2026/call
