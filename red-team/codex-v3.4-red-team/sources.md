# Live-source audit

Checked on 6 September 2026. “Supports” means the source supports the limited proposition listed, not the roadmap as a whole.

| URL | Checked for | Result |
|---|---|---|
| https://arxiv.org/html/2603.18257 | IBD’s estimand, confounded-distractor construction, static probing protocol, FDR and probe cost | **Supports with limits.** IBD already tests shared-confounder distractors and uses randomised-action two-sample tests. It computes one mask after a roughly 32k-step probing phase; it does not supply the proposed sequential changing-boundary benchmark. No code link was visible in the arXiv HTML checked. |
| https://www.sciencedirect.com/science/article/pii/S1367578819300070 | Whether feedback can mask faults and active test inputs are established FDI ideas | **Supports.** The review says feedback can mask fault effects and active input design can reveal diagnostic information. This supports R2’s motivation, but not masking complete loss in a single-actuator plant. |
| https://www.sciencedirect.com/science/article/pii/S0925231219309920 | Whether closed-loop compensation can diminish evidence of small faults | **Supports with limits.** The paper concerns small faults under closed-loop control, reinforcing that R2 naturally fits partial/incidental loss rather than zero authority. |
| https://pmc.ncbi.nlm.nih.gov/articles/PMC13205647/ | Standard quickest-change trade-off | **Supports.** It describes minimising detection delay subject to ARL-to-false-alarm control. It does not endorse the roadmap’s disjoint-support scalar. |
| https://gymnasium.farama.org/v0.27.0/environments/classic_control/cart_pole/ | CartPole action type and horizon | **Contradicts implementation assumptions.** CartPole uses `Discrete(2)` and a 500-step truncation, so additive continuous action perturbation and a median length above 500 are not valid without changing the environment. |
| https://gymnasium.farama.org/v0.26.3/environments/classic_control/pendulum/ | Pendulum action type and horizon | **Clarifies.** Pendulum-v1 uses one bounded continuous torque and truncates at 200 steps. |
| https://gymnasium.farama.org/main/environments/mujoco/inverted_pendulum/ | Whether “inverted pendulum” could mean a different Gymnasium environment | **Clarifies ambiguity.** MuJoCo InvertedPendulum has one continuous force action in `[-3,3]`; it is distinct from classic Pendulum-v1. |
| https://proceedings.iclr.cc/paper_files/paper/2025/hash/fcc22e5b7d5d2155d994da22d045f0a6-Abstract-Conference.html | Robust-Gymnasium’s scope and status | **Supports.** It is an ICLR 2025 benchmark with observation, action, reward and environment disruptions across more than sixty tasks. The exact proposed controllability protocol was not established by this source. |
| https://proceedings.mlr.press/v162/wang22c/wang22c.pdf | Whether uncontrollable information can still be reward-relevant | **Contradicts hard filtering.** Denoised MDP explicitly includes an uncontrollable-but-reward-relevant category. |
| https://arxiv.org/abs/2205.13817 | Whether Iso-Dream discards all noncontrollable dynamics | **Contradicts hard filtering.** Iso-Dream models and leverages noncontrollable dynamics for planning. It supports the claim that inverse dynamics is used to encourage separation. |
| https://arxiv.org/abs/2606.20104 | Sensorimotor World Models’ method and claimed controllability bias | **Supports with limits.** The preprint uses inverse-dynamics regularisation to preserve action-aligned information and reject uncontrollable distractors. This makes shared-confounder stress testing relevant. |
| https://arxiv.org/abs/2608.06706 | Dueling World Models’ boundary and Paper 2 novelty | **Contradicts the strongest novelty framing.** The August 2026 preprint already identifies action-tracking distractors as a measured boundary. Changing boundaries, cross-model evaluation and a successful typed remedy may still survive. |
| https://github.com/boundary-bench/boundary-bench | Name collision for `boundary-bench` | **Contradicts name availability.** An active coding-agent benchmark already uses the name and has a public site. |

## Claims not verified live

- I did not establish the absence of every competing benchmark; the novelty conclusion is from a bounded search, not a systematic review.
- I did not verify current PyPI ownership of every candidate package name.
- I did not independently reproduce published IBD numerical tables because no implementation package exists in this repository and no visible official code link was found on the checked arXiv page.
- The 12–18-hour confirmation runtime and “tens of dollars” GPU estimate have no measured local benchmark in the plan and remain unsupported estimates.
