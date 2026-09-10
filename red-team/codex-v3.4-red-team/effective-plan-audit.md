# Effective-plan audit

The latest plan is not a single document. This table reconstructs the material rule currently in force and identifies where consolidation is required.

| Area | Latest effective rule | Audit status | Required clarification |
|---|---|---|---|
| Stage 0A contract | `stage-0a-contract-v2.2.md` | **Blocked** | Executable-proof coverage is claimed but absent; fix L1, L4, L5, L9 and L12 before scaffolding. |
| Paper 1 primary target | `S^obs,ε` probabilities and typed support-change alarm only (contract F/H4) | **Usable after consolidation** | This supersedes v3.1 A2’s “typed change detection for all three targets.” State it once. |
| Response and identity targets | Ground truth retained; optional later estimator outputs; not compared in Paper 1 | **Resolved** | Remove older three-target Paper 1 wording from the effective plan. |
| Primary comparator | Sequential IBD versus “CUSUM or GLR” | **Unfrozen** | Choose one, or freeze a best-of rule and account for selection. |
| Primary event | Complete actuator loss causing observed support change | **Valid in R0/R1** | Incompatible with R2 masking in a single-actuator system. |
| Regimes | R0 clean; R1 dynamics misspecified; R2 feedback-masked | **Partly invalid** | Make R2 an action-effect/partial-loss study or use redundant actuation. |
| Primary scalar | Discrete delay–log-ARL pAUC over shared delay support | **Partly defined** | Define censored delay; remove the invalid scalar for disjoint supports. |
| R0 rule | Upper CI ≤ 0 validates classical dominance or match | **Misapplied** | Use a practical-equivalence/non-superiority margin. |
| R1/R2 rule | Lower CI > ln 2 on both dynamics families; futility if upper CI < ln 2 on either | **Clear once R2 is repaired** | Clarify whether “families” means SCM L/N only and how T2 enters the claim. |
| Confirmation matrix | A4’s 240-run grid, modified by C2/C5/C8 | **Not reconstructible** | Publish the superseding CSV and exact cell formula. |
| Environments | SCM L/N, CartPole, inverted pendulum | **Plausible** | Name the pendulum implementation; specify discrete versus continuous confound injection and episode horizons. |
| Baselines | Five: random, temporal correlation, forward residual, sequential IBD, classical CUSUM/GLR | **Plausible** | Freeze information sets and exact classical detector. |
| Phase S | One-week serial internal shakedown between 0A and 0B | **Resolved** | Treat results as diagnostic, not a powered Paper 3 gate. |
| Paper 2 | Stress inverse/action-conditioned world models with confounded distractors and boundary change; add interventional filter | **Promising but method flawed** | Route rather than delete noncontrollable reward-relevant state. Narrow novelty claim. |
| Hardware | Serial heavy runs; operation budgets primary; cooldown and thermal log | **Resolved for fairness** | Benchmark runtime before committing calendar dates. |
| Workflow | Builder, executable proofs, adversarial review, Daniel sign-off, frozen confirmation | **Partly resolved** | Add independent black-box acceptance tests and protected evaluator artifacts. |
| Publication | arXiv first; venue only against live call | **Resolved** | Rename the package before public scaffolding because “Boundary-Bench” is occupied. |

## Supersession problems to eliminate

1. V3.1 A4’s run matrix is not explicitly replaced after three regimes and four environments are introduced.
2. V3.1 A2 and contract v2.2 disagree about whether all three typed alarms are primary.
3. V3.2 B2 asks for a break-even probe budget; v3.3 C2 and v3.4 D1 test one declared budget.
4. V3.3 C1 and v3.4 D2 turn disjoint curves into a number, but do not define a scientifically comparable estimand.
5. The base v3 schedule and Phase S publication decision are obsolete but remain easy for an implementing agent to read as live instructions.

## Proposed consolidation rule

Create a clean v4 rather than another amendment. Include a “supersedes” header naming every retired file, a normative-vs-informative marker on each section, and machine-readable registries for constants, baselines, test coverage and confirmation cells. Agents should implement only from those registries and the consolidated contract.
