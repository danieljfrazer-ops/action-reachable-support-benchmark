# Evidence

All checks performed 6 September 2026 by fetching the URL or searching the web. "Verified" means the URL resolves to the work the report describes and the report's characterisation of it is accurate.

## 1. Citation verification for the report's source list

| # | Report label | Status | Notes |
|---|---|---|---|
| 1 | Literature screening synthesis, 6 Sep 2026 | n/a | Author's own screening; no external source. |
| 2 | World Models and Predictive Coding for Cognitive and Developmental Robotics (arXiv 2301.05832) | Verified | Survey. |
| 3 | Sensorimotor Contingencies as a Key Drive of Development (Frontiers Neurorobotics 2019) | Verified | |
| 4 | Resilient Machines Through Continuous Self-Modeling (Bongard, Zykov, Lipson; Science 2006; PubMed 17110570) | Verified | |
| 5 | Homeostatic Reinforcement Learning (Keramati & Gutkin, eLife 2014) | Verified | |
| 6 | Neural Homeostat (NeurIPS 2021) | Verified | |
| 7 | Continual-Dreamer (Kessler et al., PMLR v232, 2023) | Verified | |
| 8 | Prerequisites for an Artificial Self (Frontiers Neurorobotics 2020) | Verified | |
| 9 | Transformer-XL (arXiv 1901.02860) | Verified | |
| 10 | Recurrent Memory Transformer (arXiv 2207.06881) | Verified | |
| 11 | Infini-attention (arXiv 2404.07143) | Verified | |
| 12 | Learning to Learn at Test Time (arXiv 2407.04620) | Verified | TTT layers. |
| 13 | Titans (arXiv 2501.00663) | Verified | |
| 14 | OAKS (ACL 2026, 2026.acl-long.1956) | Verified, label imprecise | Actual title: "Can Large Language Models Keep Up? Benchmarking Online Adaptation to Continual Knowledge Streams", Kim, Lee, Zhou, Park, Yoon, Bui, Dernoncourt, Cha, Seo. Also arXiv 2603.07392. 14 models, OAKS-BABI and OAKS-Novel, finds state-tracking lag and distraction failures, as the report states. |
| 15 | Nested Learning (Google Research blog) | Verified | Blog, not paper. |
| 16 | Language Models Need Sleep (arXiv 2606.03979) | Verified | Behrouz, Hashemi, Javanmard, Mirrokni; submitted 2 Jun 2026, revised 10 Jul 2026. Two-stage consolidation: distillation into larger nets, then RL self-improvement. |
| 17 | Computationally Budgeted Continual Learning (arXiv 2303.11165) | Verified | |
| 18 | Continuous Thought Machines (arXiv 2505.05522) | Verified | |
| 19 | Karpathy AutoResearch (github.com/karpathy/autoresearch) | Verified | Agent edits only `train.py`; fixed 5-minute wall-clock budget excluding startup; metric val_bpb; NVIDIA GPU required, tested on H100; README states runs are "not comparable to other people running on other compute platforms." |
| 20 | AutoResearch MLX port (github.com/trevin-creator/autoresearch-mlx) | Verified | About 1.8k stars, 6 commits on main at check time. README section "Rigorous keep/discard (optional)" documents about 0.03 single-run noise and a `rigor.py` multi-seed bootstrap gate. |
| 21 | Optuna | Verified | |
| 22 | AI Scientist v2 (SakanaAI) | Verified | |

**Uncited work named in prose:** "A 2026 interoceptive-attention study ... (AffectWorld)". This is arXiv 2608.04232, "Interoceptive Attention as Dynamic Homeostatic Prioritization in a Foraging Agent", 4 August 2026: four-channel foraging gridworld, active-inference agent reallocates a fixed interoceptive-precision budget to the most urgent need; more than doubles learning-phase survival versus uniform precision at matched budget. Should be added to the source list.

## 2. Prior art the report did not cite

### 2a. Hidden-volatility memory routing (R1)

| Work | Year | Why it matters |
|---|---|---|
| Behrens et al., "Learning the value of information in an uncertain world", Nature Neuroscience | 2007 | Learning rate scales with estimated volatility. The normative framing of "adapt to how fast things change." |
| Wilson, Nassar & Gold, "Bayesian online learning of the hazard rate in change-point problems", Neural Computation | 2010 | Online hazard-rate inference. A natural oracle-free, model-based router baseline. https://pubmed.ncbi.nlm.nih.gov/20569174/ |
| Wilson et al., "A mixture of delta-rules approximation to Bayesian inference in change-point problems", PLOS Comp Bio | 2013 | Multi-timescale delta rules, i.e. cheap multi-tier memory with learned weighting. |
| de Jong, Wilhelm & Akyürek, "Adaptive forgetting speed in working memory", Psychonomic Bulletin & Review | 2024 | Humans adapt forgetting rate to "probing hazard" (probability an item is queried at delay t). Directly parallels the report's delayed-query manipulation. https://pmc.ncbi.nlm.nih.gov/articles/PMC11680658/ |
| Jain & Shenoy, "Instance-Conditional Timescales of Decay for Non-Stationary Learning", AAAI | 2024 | Learns per-instance mixture of decay timescales for drifting data; extended to continual learning. https://arxiv.org/abs/2212.05908 |
| "Learning to Forget: Continual Learning with Adaptive Weight Decay" (FADE) | Apr 2026 | Per-parameter decay rates meta-learned to match environment non-stationarity timescale; positions itself against activation-level forget gates. https://arxiv.org/abs/2604.27063 |
| Kimi Delta Attention; Gated DeltaNet-2; FG2-GDN | 2025 to May 2026 | Per-key and per-channel learned forgetting and write rates in linear attention. https://arxiv.org/abs/2605.22791 , https://arxiv.org/pdf/2604.19021 |
| Memory-R1 | 2026 | RL-trained memory manager choosing ADD/UPDATE/DELETE/NOOP on eventual answer reward. Covers "delayed-value memory writes." |
| MemTier; MemRouter; H-MEM | 2026 | Tiered agent memory with asynchronous consolidation and learned retrieval policy. https://arxiv.org/pdf/2605.03675 , https://arxiv.org/abs/2605.00356 , https://aclanthology.org/2026.eacl-long.15/ |
| StreamingQA (ICML 2022); EvolvingQA | 2022 to 2024 | Benchmarks for updating and removing outdated knowledge over time; predecessors of OAKS. https://arxiv.org/abs/2205.11388 |
| "Temporal Memory for Resource-Constrained Agents: Continual Learning via Stochastic Compress-Add-Smooth" | Apr 2026 | Resource-constrained continual memory, multi-timescale. https://arxiv.org/html/2604.00067 |

### 2b. Adversarial causal self-boundary (R2)

| Work | Year | Why it matters |
|---|---|---|
| Gold & Scassellati, "Robot self-recognition using conditional probability-based contingency", AAAI | 2006 | Contingency-based self/other detection with mirror and other-robot conditions; lists four contingency-detection methods. |
| Liu, Cheng & Bogdan, "Discovering What You Can Control: Interventional Boundary Discovery for RL" | Mar 2026 | Randomised actions as interventions, per-dimension two-sample tests with FDR correction, binary controllability mask. 12 continuous-control settings, up to 100 distractors including ones that mimic controllable variables. Matches oracle in 11/12, beats MI, forward-model and gradient-sensitivity baselines. https://arxiv.org/abs/2603.18257 |
| "Proprioceptive-visual correspondence enables self-other distinction in humanoid robots" | Jun 2026 | Self-model without identity labels, evaluated against morphologically identical robot distractors. https://arxiv.org/abs/2606.13222 |
| Lanillos et al., "Robot self/other distinction: active inference meets neural networks learning in a mirror" | 2020 | Active-inference self/other distinction. |
| Seitzer et al., "Causal Influence Detection for Improving Efficiency in RL", NeurIPS | 2021 | Detecting when actions causally influence state variables. |

**Gap that survives:** none of these test a boundary that changes during deployment (actuator remap, sensor fault, morphology drift) or score calibration of the boundary estimate through the transition.

### 2c. Proactive counterfactual compute (R5)

| Work | Year | Why it matters |
|---|---|---|
| Russell & Wefald, "Principles of metareasoning" | 1991 | Defines value of computation. |
| Hay, Russell, Tolpin & Shimony, "Selecting computations: theory and applications", UAI | 2012 | Metareasoning for selecting internal computations. |
| Lieder et al., reward shaping for metacognitive learning, RLDM | 2014 | Learned meta-level reward for when to think. |
| Budd et al., "Metareasoning for probabilistic planning using learned VOC", AAAI | 2024 | Learned value-of-computation features. https://www.robots.ox.ac.uk/~nickh/papers/budd24aaai.pdf |
| "Rational Metareasoning for Large Language Models" | 2024 | Same idea applied to LLM inference. https://arxiv.org/pdf/2410.05563 |
| Jensen, Hennequin & Mattar, "A recurrent network model of planning explains hippocampal replay and human behavior", Nature Neuroscience | 2024 | RL agent learns when to perform internal rollouts versus act; rollouts cost time; the learned gate triggers only when rollouts improve outcomes. Laptop-scale. https://www.nature.com/articles/s41593-024-01675-7 |

**Gap that survives:** heterogeneous internal actions (retrieve, roll out, consolidate, learn) scheduled in a continuing world where missed events cost, evaluated with false-alarm and missed-intervention rates.

## 3. Hardware claims

- Fanless Apple Silicon MacBook Air throttles under sustained load. Reports across M2, M3 and M5 Airs: clocks reduced within roughly 8 to 15 minutes of sustained inference or training, with 25 to 50 percent throughput reduction at thermal equilibrium versus a fan-cooled MacBook Pro. Sources: SolidAITech M5 Air thermal analysis (Apr 2026); Notebookcheck and TechRadar M2 Air throttling tests; Hacker News thread 43266992.
- Implication for the report's "equal wall-clock" comparisons and for fixed-5-minute AutoResearch budgets is discussed in findings F8.
