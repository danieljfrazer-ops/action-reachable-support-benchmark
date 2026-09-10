# Source ledger

**Checked:** 6 September 2026.  
This lists the live URLs I actively used for the response. “Supported” means the source supported the particular proposition checked, not every claim made about the work. ArXiv papers are marked as preprints unless another proceedings/publisher record was checked. Search-result snippets were used only to locate sources; claims in the two review documents rely on the linked paper, publisher, proceedings, or bibliographic page wherever available.

## Original-report prior art

| URL | What I checked | Outcome |
|---|---|---|
| https://arxiv.org/abs/2603.18257 | IBD's estimand, intervention procedure, distractor construction, stationarity assumption, output, experiments | **Supported with qualification.** It produces a one-time binary action-reachability mask using randomized actions and FDR-controlled tests under a stationary causal structure. It supports the red team's static-boundary criticism but contradicts the stronger implication that deployment-time drift/calibration was already tested. |
| https://arxiv.org/abs/2212.05908 | Jain & Shenoy/MuScaTeL's “instance-conditional timescales” | **Supported with qualification.** It learns instance-feature-dependent mixtures of decay kernels. The paper is mainly weighted batch/offline-window learning, with a continual-learning adaptation; it is not an online per-entity hazard router across memory stores. |
| https://arxiv.org/abs/2604.27063 | FADE's unit of adaptation, online setting, neural scope, experiments | **Supported with qualification.** Online per-parameter adaptive decay is real; the derivation is linear and neural application is to the final layer. It is adjacent rather than equivalent to per-item multi-tier routing. Preprint. |
| https://pmc.ncbi.nlm.nih.gov/articles/PMC2966286/ | Wilson, Nassar & Gold's hazard inference | **Supported.** The hierarchical Bayesian model learns an online, potentially changing hazard rate; it does not perform memory routing. Peer-reviewed Neural Computation article. |
| https://arxiv.org/abs/2508.19828 | Memory-R1 operations, training, and first-posted date | **Supported with correction.** ADD/UPDATE/DELETE/NOOP and outcome-driven RL are accurate. First arXiv submission was August 2025, not 2026. |
| https://aclanthology.org/2026.acl-long.583/ | Memory-R1's ACL publication status | **Supported.** ACL 2026 publication; this explains why it may be described as a 2026 paper despite the 2025 preprint. |
| https://www.nature.com/articles/s41593-024-01675-7 | Jensen, Hennequin & Mattar's learned rollout decision and temporal cost | **Supported with qualification.** The meta-RL agent chooses rollout versus physical action and time advances differently; this is learned planning allocation, but not the same as an exogenous real-time world advancing during all deliberation. Peer reviewed. |
| https://arxiv.org/abs/2606.26463 | *Finding the Time to Think*: variable planning budgets and real-time world/clock | **Supported.** A lightweight learned gate chooses state-dependent MCTS budgets; environments or clocks advance; fixed/heuristic baselines are beaten. It schedules planning depth, not heterogeneous internal operations. Preprint. |
| https://arxiv.org/abs/2608.04232 | AffectWorld identity, date, and report-source omission | **Supported.** The title and August 2026 submission match; it should have been in the original numbered source list. Preprint/accepted SAB 2026 according to arXiv metadata. |
| https://aclanthology.org/2026.acl-long.1956/ | OAKS's full title, venue, and basic result | **Supported.** The paper is *Can Large Language Models Keep Up? Benchmarking Online Adaptation to Continual Knowledge Streams*, ACL 2026, and reports lag/distraction failures. |

## Dynamic body models, fault detection, and adaptation

| URL | What I checked | Outcome |
|---|---|---|
| https://pubmed.ncbi.nlm.nih.gov/17110570/ | Bongard, Zykov & Lipson (2006): continuous self-modeling after damage | **Supported.** A four-legged robot infers structure from actuation–sensation relationships, updates self-models after a leg part is removed, and generates compensatory gaits. Peer-reviewed Science article. |
| https://pubmed.ncbi.nlm.nih.gov/19665561/ | Sturm, Plagemann & Burgard (2009): learned body schema, change monitoring, adaptation | **Supported.** The abstract states that a Bayesian-network kinematic model is learned from action/self-observation and monitored/adapted after failure, repair, or fatigue. Peer reviewed. |
| https://doi.org/10.1016/j.jphysparis.2009.08.005 | Publisher record/full-page details for the same 2009 paper | **Supported.** The page further describes detecting blocked/deformed joints, localizing mismatch, and lifelong model revision. This is the most important omission in v2's second-round gap check. |
| https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2016.00007/full | Online body-schema adaptation on iCub | **Supported.** Sequential Monte Carlo updates an internal kinematic model online from prediction mismatch and multisensory feedback. It does not provide v2's adversarial distractor benchmark. Peer reviewed. |
| https://www.science.org/doi/10.1126/scirobotics.abn1944 | Chen et al. full-body visual self-model and damage recovery | **Supported through indexed page/search content, but direct fetch was blocked (403).** I did not rely on inaccessible details beyond damage detection, identification, and model update, which were also visible on the authors' project page. |
| https://robot-morphology.cs.columbia.edu/ | Author project page for Chen et al. | **Supported.** Confirms learned visual self-model, damage localization/recovery, and released paper/code. Author source, not independent peer review. |
| https://www.nature.com/articles/s44182-025-00031-6 | Hu, Chen & Lipson (2025) egocentric self-model | **Supported.** A self-supervised action-conditioned future-state model detects anomalies and is retrained after damage to recover locomotion. Peer reviewed. |
| https://arxiv.org/abs/2506.19984 | Damaged multi-legged robot morphology identification | **Supported.** Identifies damaged legs, updates the model, and integrates it into control. Preprint. |
| https://proceedings.mlr.press/v305/fu25b.html | Forward-prediction auxiliary/model component in fault-tolerant RL | **Supported.** A forward predictor plus error comparator is integrated with a controller and evaluated under joint damage. CoRL 2025 proceedings. |
| https://arxiv.org/abs/2406.17718 | Latent self-prediction as an auxiliary task in RL and interaction with distractors | **Supported.** This directly weakens v2's novelty wording for auxiliary hidden-state prediction, although it does not study body changes. Preprint. |
| https://arxiv.org/abs/2603.04029 | World-model residuals triggering online continual RL adaptation | **Supported from abstract/indexed record.** Prediction residuals detect deployment OOD events and trigger fine-tuning. Preprint; I did not inspect all experimental details. |
| https://arxiv.org/abs/2101.07599 | Meta-RL/model adaptation under changing robot dynamics | **Supported at a broad level.** Online interaction-model adaptation and latent context selection are established neighbours; not the same boundary estimand. Preprint. |
| https://arxiv.org/abs/2601.20714 | Adaptation to action-space/reward changes | **Supported with qualification.** MORPHIN handles expansion of available actions and reward drift, not actuator remapping or causal-boundary calibration. The red-team round-2 table described it only broadly, but its relevance to physical boundary change is weaker than implied. |
| https://doi.org/10.1109/ICRA.2015.7139383 | Online Bayesian change-point detection for articulated motion models | **Supported from IEEE/indexed metadata; full text was not available through the browser.** Establishes a direct robotics precedent for online mechanism-change detection. |
| https://doi.org/10.1016/j.conengprac.2014.01.013 | Actuator FDI using command/observation residuals and change detection | **Supported from publisher/indexed abstract.** Demonstrates actuator fault detection/isolation and a cumulative change test; it does not address action-confounded distractors. |
| https://doi.org/10.1049/cth2.12032 | Probabilistic fault detection and false-alarm/missed-detection characterization | **Supported from publisher-indexed content.** Shows that detection/false-alarm probability is standard in model-based fault diagnosis. It is not a direct RL boundary benchmark. |
| https://ora.ox.ac.uk/objects/uuid%3A2ba81bc6-ab24-4e5e-bd19-abc7f65fdef5 | Bayesian sensor-fault residuals and fault-tolerant control | **Supported from repository abstract/indexed content.** Another close probabilistic FDI neighbour; not used to claim occupation of the exact v2 intersection. |

## Self-modeling and introspection

| URL | What I checked | Outcome |
|---|---|---|
| https://arxiv.org/abs/2407.10188 | Premakumar et al.'s auxiliary internal-state prediction and regularization results | **Supported.** Static classification networks with self-prediction have narrower weights and lower RLCT; no agent or body change. Preprint page checked; v2's described scope is accurate. |
| https://doi.org/10.1098/rsta.2024.0531 | Peer-reviewed version/status of Premakumar et al. | **Supported from the DOI cited in the red-team packet; not independently full-text inspected.** Included for publication provenance only. |
| https://arxiv.org/abs/2608.14894 | Self-Interventional Learning scope and results | **Supported with qualification.** Predictive self-knowledge, interventions, and action use are present; it is a single-author August 2026 preprint submitted to JMLR, and simple empirical memory remains competitive. |
| https://arxiv.org/abs/2410.13787 | Binder et al.'s operational definition and limits of LLM introspection | **Supported.** Behavioral self-prediction advantage after fine-tuning is shown on simple tasks, with failures on harder/OOD tasks. This is not hidden-state prediction in embodied RL. Preprint. |

## Hardware and venues

| URL | What I checked | Outcome |
|---|---|---|
| https://www.tomshardware.com/laptops/macbooks/apple-macbook-air-13-inch-m5-review | M5 Air sustained-load throttling | **Supported.** Cinebench reportedly fell from 3,415 to the low 2,300s over repeated runs in the fanless 13-inch chassis. Supports the confound, not a universal onset time. Independent review, not a scientific benchmark. |
| https://www.rtings.com/laptop/reviews/apple/macbook-air-13-m5-2026 | Independent confirmation of sustained-workload throttling | **Supported at summary level.** Reports thermal throttling under sustained workloads; no universal “8–15 minute” rule established. |
| https://www.laptopmedia.com/au/review/apple-macbook-air-15-3-m5-the-best-15-inch-laptop-for-everyday-use/ | Chassis/workload dependence and sustained throttling | **Supported at summary level.** Reports significant sustained-load throttling on the 15-inch M5 Air. |
| https://iclr.cc/Conferences/2027/AuthorGuidelines | Official ICLR 2027 main-conference dates | **Supported.** Abstract and paper deadlines are 18 and 25 September 2026. This page does not establish any particular workshop topic or February 2027 workshop-paper deadline. |
| https://iclr.cc/ | ICLR 2027 official site | **Supported only as general conference source.** No specific Paper 1 workshop target was verifiable from it at review time. |
| https://lifelong-ml.cc/Conferences/2026/call | Historical CoLLAs call linked by the red-team packet | **Did not support a 2027 deadline.** Useful only as historical context. I found no official CoLLAs 2027 CFP on 6 September 2026, so v2's date remains an explicitly speculative estimate. |

## Sources encountered but not used as decisive evidence

- https://arxiv.org/abs/1805.03104 — predictive-coding robot body learning; relevant background, but older robotics sources above were enough for the findings.
- https://pmc.ncbi.nlm.nih.gov/articles/PMC7461994/ — forward sensory prediction for damage adaptation; corroborative only.
- https://pmc.ncbi.nlm.nih.gov/articles/PMC8840082/ — meta-learning fault-tolerant vehicle control; corroborative only.
- https://ojs.aaai.org/index.php/AAAI/article/view/25760 — meta-auxiliary learning for adaptive pose prediction; adjacent but not a robot-body self-model.
- https://www.biorxiv.org/content/10.64898/2026.06.11.731593v2.full — active calibration under changing tool/contact conditions; recent preprint and not needed for the core conclusion.
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7345456 — August 2026 active self-diagnosis preprint; too recent and not necessary to establish the occupied parent problem.
- https://arxiv.org/abs/2005.07404 — planning/learning compute trade-off; background only.
