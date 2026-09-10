# Red team of roadmap v3.4

**Review date:** 6 September 2026  
**Effective plan reviewed:** `roadmap-v3.md`, amendments v3.1–v3.4, `stage-0a-contract-v2.2.md`, `benchmark-proposal.md`, the current executable proofs, and the latest Gemini review.  
**Verdict:** **Go with blocking changes.** The research direction is viable; the claim that Stage 0A is already “mathematically verified” and ready to scaffold is not.

Severity is my judgment. External claims were checked live where feasible; the source log is in `sources.md`.

## Technical summary

V3.4 has repaired most issues found in the prior Codex review: latent and observed support are separated, Paper 1 is narrowed to support detection, sequential metrics are more concrete, Phase S is serialised and reduced, and the technical claim no longer depends on self-awareness language. The remaining blockers arise from the repairs themselves:

1. the executable-proof gate is declared complete although the two scripts are print-only demonstrations covering a small subset of the contract;
2. the masked-fault regime cannot use complete actuator loss in the single-actuator systems chosen precisely to make support disappear;
3. the primary statistic mishandles censoring and treats non-overlapping operating curves as if a scalar boundary difference established dominance;
4. “exact ground truth” is overstated for nonlinear expectations estimated by simulation; and
5. the Paper 2 filter would discard uncontrollable but decision-relevant state that several target architectures are designed to retain.

These are repairable without abandoning the benchmark. They should be fixed in a consolidated v4 contract before code generation.

## High-severity findings

### L1. The executable proofs are not tests and do not cover the contract

**Claim attacked.** Contract v2.2 says every equation and numeric invariant ships with an executable check, the red-team agent runs all mutants before scaffolding, and the latest review calls the contract mathematically verified.

**Evidence.** The repository contains two Python scripts. They print demonstrations for G1–G3, H1, H3 and I2, but contain no `assert`, `pytest` test, failure threshold or non-zero failure path. None of mutants M1–M6 is implemented. There are no executable checks for the declarative graph, operational support, observation-map events, faithfulness resampling, calibration splits, isolation canary, determinism, stationary mean, nonlinear response, or most numeric constants. Both scripts exit 0 because they are demonstrations, not because a gate passed.

**Fix.** Before scaffolding, replace the prose claim with a coverage matrix mapping every equation/invariant to a test ID. Convert demonstrations into assertions with tolerances and explicit failure messages. Implement M1–M6 and show that each makes at least one test fail. A clean run must return non-zero when any expected property is violated. Daniel should sign the test report plus uncovered-item count, not captured print output.

### L2. R2 cannot mask the primary support-changing fault in the chosen T2 systems

**Claim attacked.** In R2, feedback masks an actuator-loss fault so passive residual detectors miss it, while probing reveals that support has disappeared; CartPole and inverted pendulum are selected because complete actuator loss unambiguously empties support.

**Evidence.** Both T2 systems have one actuator. Once that actuator has zero authority, a feedback controller has no remaining control channel with which to compensate. Feedback can mask an **incipient or partial** loss of effectiveness, a known active-diagnosis motivation, but partial gain loss leaves graph reachability—and therefore binary support—unchanged. The active-fault-diagnosis literature explicitly discusses feedback masking fault effects and test inputs revealing them, but that does not make complete single-actuator loss compensable ([overview of active input design](https://www.sciencedirect.com/science/article/pii/S1367578819300070); [closed-loop small-fault detection](https://www.sciencedirect.com/science/article/pii/S0925231219309920)).

**Fix.** Split the hypotheses by target:

- use complete actuator loss for `S^obs` change detection in R0/R1, without claiming feedback compensation;
- use partial effectiveness loss for an `R`-change experiment in R2; or
- add a redundant multi-actuator environment and score loss of an action channel/effect map rather than disappearance of state support.

Do not make R2 confirmatory for `α^S` unless an environment can both retain task control and genuinely change the declared support.

### L3. The primary statistic rewards selectively detected cases and has no valid disjoint-support scalar

**Claim attacked.** Discrete `Δ_pAUC` yields one comparable signed effect for overlapping and disjoint delay supports and can be bootstrapped across seeds.

**Evidence.** Contract G censors detection delay at the next event or episode end, but C1 builds the Pareto envelope from empirical median delays without saying how censored events enter the median. Calculating delay only among detected events makes a detector that fires quickly on a few easy cases and misses the rest appear fast. For disjoint supports, the code returns an ARL difference at two **different delays** and declares dominance solely from delay ordering. A faster curve with much worse false-alarm control need not dominate a slower curve. Mixing that boundary number with overlapping-interval pAUC values during bootstrap combines different estimands. The executable example proves only that the code returns a float.

**Fix.** Define delay with censoring using a survival estimand—predeclared restricted mean detection time is the simplest—or assign a fixed failure horizon and report detection probability separately. Design thresholds to cover a frozen common delay grid. If curves still do not overlap, report a partial order/two-coordinate result; do not aggregate it with pAUC. A scalar alternative must attach an explicit utility or cost function to delay and false alarms.

### L4. “Exact ground truth” is false for the nonlinear operational labels

**Claim attacked.** T1 supplies exact `S`, `R` and `P` labels by construction.

**Evidence.** Structural graph reachability and the discrete assignment map can be exact. But `S^latent,ε` is explicitly **estimated** through paired simulation, and the nonlinear `R` is an expectation conditioned on a stationary mean. No closed form, Monte Carlo sample size, numerical error bound or confidence rule is supplied. The nonlinear process may not even have a unique stationary distribution under the current unconstrained parameters. Consequently, the primary `S^obs,ε` label can flip near ε because of oracle estimation noise.

**Fix.** Say “structurally exact, numerically certified operational labels.” Constrain the model so the required stationary distribution exists; define how `z̄` is estimated; attach a high-precision oracle budget and uncertainty interval; reject instances whose label interval intersects ε. Validate selected nonlinear cases against much larger independent simulations. Keep structural labels as the exact correctness target.

### L5. Sensor gain can change operational support despite the event table saying it cannot

**Claim attacked.** A sensor-gain event changes `P` only; `S^obs,ε` is unchanged.

**Evidence.** The observation is multiplied by `gain_t`. If a gain becomes zero, the delivered channel contains no action effect. If it becomes sufficiently small, its intervention effect falls below ε. Yet C3’s explicit `S^obs` formula checks only assignment and availability, and Table D marks gain events as support-invariant. “Likewise `S^obs,ε`” is not a definition of how gain scales the operational effect.

**Fix.** Define operational observed support directly from the distribution of `o`, including assignment, gain, availability and observation noise. Either allow gain changes to alter `S^obs,ε`, or constrain all gain events to a prevalidated interval that cannot cross ε. Add zero-, near-zero- and sign-flip-gain cases to the hand derivation and mutant suite.

### L6. Paper 2’s proposed filter deletes information its own victims need

**Claim attacked.** Removing channels outside the estimated controllable support before world-model training is a general remedy for confounded distractors.

**Evidence.** “Uncontrollable” is not equivalent to “irrelevant.” Denoised MDP explicitly distinguishes uncontrollable but reward-relevant information, and Iso-Dream predicts noncontrollable dynamics so the policy can anticipate them ([Denoised MDP](https://proceedings.mlr.press/v162/wang22c/wang22c.pdf); [Iso-Dream](https://arxiv.org/abs/2205.13817)). Filtering all non-support channels can remove weather, obstacles or other agents that actions do not cause but decisions must use. It could make the proposed treatment worse for a trivial reason unrelated to confounded agency attribution.

**Fix.** Replace deletion with typed routing: controllable channels to an action-conditioned branch; noncontrollable but predictive/reward-relevant channels to an exogenous branch; uncertain channels retained with soft weights. Compare hard deletion, soft gating and two-branch routing. Measure controllability leakage separately from reward-relevant information retention.

### L7. The effective Paper 1 design is not reconstructible from the amendment stack

**Claim attacked.** Planning is closed and the confirmation design is frozen.

**Evidence.** A4 freezes a 240-run primary sub-grid based on two methods, three distractor levels, two delays, two SCM families and one regime. C2 later replaces the contrast with three regimes; C5 expands Paper 1 to four environments; C8 again says “240 primary runs” without publishing a replacement cell formula. A2 says typed change detection for all three targets is primary, while contract v2.2/H4 makes only support probabilities and support alarms primary. B2 describes estimating the **probe budget at which** methods match; C2/D1 test superiority at one declared budget. “CUSUM or GLR” also leaves the primary comparator unresolved.

**Fix.** Publish one consolidated roadmap and one machine-readable `confirmation-design.csv` that supersede all layered prose. Each row should name environment, family, regime, event, target, distractor level, delay, probe budget, estimator, threshold policy and seed. State the exact primary comparator—CUSUM, GLR, or a predeclared best-of rule with multiplicity handling—and reconcile break-even-budget estimation with the fixed-budget hypothesis.

## Medium-severity findings

### L8. The clean-regime “match” rule almost never validates equality

**Claim attacked.** R0 is validated when the upper 95% confidence bound of `Δ_pAUC` is at most zero, “confirming the classical detector dominates or matches.”

**Evidence.** If the true effect is exactly zero, a conventional two-sided 95% interval will usually straddle zero; its upper bound will be at most zero only in a small tail of repeated samples. The rule can establish strict non-superiority under its chosen one-sided interpretation, but it cannot reasonably validate “matches.”

**Fix.** Choose a negative-control margin `δ0`. Validate the sanity anchor with a non-inferiority/equivalence rule appropriate to the intended claim, for example upper bound `< δ0` if the only requirement is that probing not meaningfully outperform, plus diagnostics that the classical implementation detects the known fault. Do not use a zero-width practical-equivalence region.

### L9. Stability and stationarity required by the oracle are not contractual

**Claim attacked.** `z̄`, stationary baselines and long sequential windows are well-defined for both SCM families.

**Evidence.** The equations do not require `|ρ_u|<1` or spectral radii below one for `A_b`, `A_d`, `A_w` and `A_x`. The nonlinear quadratic term plus clipping has no specified clip location/range and may produce multiple invariant regimes. The default linear policy is unbounded unless actions are explicitly clipped, which also changes intervention responses.

**Fix.** Freeze stability constraints, action bounds, clip semantics, burn-in, convergence diagnostics and reset distributions. For family N, provide either a contractive construction or an empirical stationarity certification with failure criteria. Recheck faithfulness after every generated change event, not only at initial sampling.

### L10. The classical baseline’s information advantage and failure mechanism are unclear

**Claim attacked.** Sequential IBD versus CUSUM/GLR cleanly measures robustness to action-confounded distractors.

**Evidence.** A residual detector needs a declared observation/state model and must know which innovations to monitor. If it receives oracle body coordinates or `P`, it has privileged information unavailable to IBD; if it models all anonymous channels, its formulation is different and must be specified. In R1, omitting family-N nonlinearity can create false alarms even without the confounded distractor, so an observed advantage may measure generic model misspecification rather than deconfounding.

**Fix.** Give every baseline an explicit information set. Add a 2×2 diagnostic: correct/misspecified dynamics × confounder absent/present. This separates a confounding interaction from ordinary model error. Include an oracle-coordinate CUSUM as a labelled reference and a channel-agnostic residual method as the fair competitor.

### L11. The T2 wrapper specification contains immediate implementation ambiguities

**Claim attacked.** CartPole and inverted pendulum can be wrapped under the same policy-confounding and stability protocol with minimal tuning.

**Evidence.** CartPole has a discrete two-action interface, while Pendulum and MuJoCo InvertedPendulum have bounded one-dimensional continuous actions ([CartPole documentation](https://gymnasium.farama.org/v0.27.0/environments/classic_control/cart_pole/); [Pendulum documentation](https://gymnasium.farama.org/v0.26.3/environments/classic_control/pendulum/); [MuJoCo InvertedPendulum documentation](https://gymnasium.farama.org/main/environments/mujoco/inverted_pendulum/)). `W_u u_t` cannot simply be added to CartPole’s action. CartPole-v1 is truncated at 500 steps, so requiring median episode length **above** a 500-step floor is impossible under the standard wrapper. Pendulum truncates at 200 steps. Excluding all episodes that terminate before the event can condition the sample on fault tolerance and bias delay estimates.

**Fix.** Specify whether “inverted pendulum” means classic Pendulum or MuJoCo InvertedPendulum. For CartPole, inject `u` into action logits or flip probability, not the discrete action value. Set environment-specific horizons below truncation or deliberately replace `TimeLimit` and disclose it. Treat early termination as a competing failure/censored outcome and report it, rather than excluding it from the estimand.

### L12. Several apparently scalar invariants are undefined for vector variables

**Claim attacked.** E1/E2 are executable for arbitrary declared dimensions.

**Evidence.** E1 says a body component has an action ancestor iff “its column of `B`” is nonzero, but body components index rows of an `N_b×K` matrix; columns index actions. E2 writes `|corr(a_t,x_{t+1})|` although both can be vectors. Different choices—maximum pairwise correlation, canonical correlation, Frobenius norm or a fixed component—give different pass/fail results. The proof script checks only a scalar special case.

**Fix.** Correct row/column language and define the multivariate confounding statistic. Prefer a generated witness mapping that identifies which action–distractor pairs must exceed `ρ_min`, plus an aggregate secondary statistic. Add rectangular `B` tests with `N_b≠K` so index mistakes cannot hide behind a square identity matrix.

### L13. Downstream causal effects are counted as “controllable channels” without resolving the semantic cost

**Claim attacked.** `S^obs,ε` answers “which channels do you control right now (its body).”

**Evidence.** The contract intentionally gives `d` an action ancestor through `b`, so downstream world effects enter causal support. That is consistent with IBD’s broader sphere-of-influence estimand, but not with body membership. A moved object, reward display or exhaust plume may be action-reachable without being part of the agent. The appendix-only `B^obs` result does not cure a title or interpretation that equates reachability with body boundary.

**Fix.** Use “action-reachable observation support” in the technical title and primary claim. Report body membership as a separate oracle-only construct, and do not infer it from causal reachability. Include downstream channels in all examples so reviewers see that the distinction is deliberate.

### L14. The latest schedule still omits protocol-repair and faithful-baseline risk

**Claim attacked.** Stage 0A can finish by 26 September and Stage 0B by 24 October with planning closed.

**Evidence.** Stage 0A still must build the missing executable gate, nonlinear numerical certification, isolation process, four baselines and a faithful IBD reproduction. IBD’s published default probe is about 32k environment steps and produces a static binary mask; sequential adaptation is new engineering rather than a direct reproduction ([IBD full text](https://arxiv.org/html/2603.18257)). T2 then needs two different action interfaces and policy stability tuning. The claimed 12–18-hour confirmation runtime has no benchmark measurement or cell-level duration model.

**Fix.** Add a one-week contract/test repair before Stage 0A and a measured runtime pilot before calendar commitments. Make dates conditional on throughput and independent review gates. Preserve late January as a target, but add a four-week slip reserve rather than treating planning closure as schedule evidence.

### L15. Paper 2’s novelty is promising but materially overstated

**Claim attacked.** Paper 2 identifies and proves a previously unknown “fundamental blind spot” in world models and is already tier-one material.

**Evidence.** IBD already formalises observational non-identifiability under shared confounding. Dueling World Models explicitly names action-tracking distractors as its measured boundary ([Dueling World Models](https://arxiv.org/abs/2608.06706)). Iso-Dream and Sensorimotor World Models openly use inverse dynamics to preserve action-aligned state ([Iso-Dream](https://arxiv.org/abs/2205.13817); [Sensorimotor World Models](https://arxiv.org/abs/2606.20104)). Applying the confounded-distractor failure across those architectures, adding boundary changes and testing a routing remedy could still be new, but the vulnerability’s core logic is no longer an unoccupied theoretical discovery.

**Fix.** Frame Paper 2 as a systematic cross-architecture stress test plus a method, not discovery of the general blind spot. Claim a method contribution only if the typed router beats hard deletion and architecture-native controls while retaining reward-relevant exogenous information. Keep “tier-one” as a contingent aspiration, as v3.4 D3 correctly says.

### L16. Agent review can still certify a shared mistake

**Claim attacked.** Builder/red-team alternation and executable proofs neutralise the agentic echo chamber.

**Evidence.** Both agents work from the same prose, repository and generated tests. A second agent can verify internal consistency while missing a wrong estimand or jointly inherited assumption. The latest Gemini audit called every section fully verified despite the absence of assertions and mutants, demonstrating this exact failure mode.

**Fix.** Require one independent black-box acceptance suite derived from a short frozen interface spec, not from implementation code. Daniel should manually calculate a small rectangular, noisy, censored case and compare both pipeline and reference implementation. For confirmation, freeze evaluator artifacts outside the agents’ writable area and require an explicit checklist of untested assumptions.

## Low-severity findings

### L17. The working package name already collides with active benchmarks

**Claim attacked.** `boundary-bench` is a safe package and paper identity.

**Evidence.** An active August 2026 project already uses Boundary-Bench for coding agents, with a repository and public site; other BoundaryBench datasets exist in table QA and geospatial evaluation ([coding-agent Boundary-Bench](https://github.com/boundary-bench/boundary-bench)). The proposal already calls the title provisional, so this is not a scientific defect, but retaining it into package scaffolding creates search and packaging confusion.

**Fix.** Rename before creating the Python package or public repository. Candidate names should foreground sequential causal controllability rather than generic “boundary.” Perform PyPI, GitHub, arXiv and web collision checks before freezing.

### L18. Phase S is now correctly small, but it no longer answers all four original questions robustly

**Claim attacked.** One week with three families and one pair will seed a defensible Paper 3 baseline table across four questions.

**Evidence.** This is a shakedown, not a powered comparison. Five confirmation seeds and one held-out family may expose gross failures but cannot reliably map crossovers or establish that no family dominates. The plan appropriately makes the report internal, so the residual problem is expectation rather than validity.

**Fix.** Label every result diagnostic; report intervals and incomplete cells; use it to estimate variance/runtime and test budget accounting. Do not use absence of dominance in this small run as the sole Paper 3 go criterion—require an uncertainty-aware criterion or a larger pre-Paper-3 pilot.

## Attacks that failed

1. **“The latent/observation support contradiction remains.” — Failed.** Contract v2.2 correctly separates `S^latent` and `S^obs`, computes event effects rather than assuming them, and includes the sensor-swap derivation.

2. **“The shared-cause distractor is causally invalid.” — Failed.** The explicit SCM severs the `u→a` path under intervention while leaving `x` driven by `u`; this is causally sound and aligned with IBD.

3. **“Paper 1 still claims three mandatory estimation tasks.” — Failed.** Contract v2.2 explicitly narrows primary scoring to support probabilities and support-change alarms. The remaining problem is inconsistent older amendment prose, not the current contract’s interface.

4. **“The laptop makes fair comparisons impossible.” — Failed.** Serial runs, operation budgets, interleaving and thermal logs can make comparisons fair. The laptop affects elapsed time, not validity, if the protocol is followed.

5. **“Phase S still displaces Paper 1.” — Failed.** V3.2 demotes it to a serial one-week internal shakedown with no automatic publication.

6. **“The benchmark has no novelty after IBD and Robust-Gymnasium.” — Failed.** IBD is static and Robust-Gymnasium supplies broad disruptions without this exact sequential, confounded, calibrated controllability protocol. A bounded search did not find the complete intersection. This supports a provisional benchmark contribution, not a “first ever” claim.

7. **“The programme still makes a consciousness claim.” — Failed.** The current technical claims are functional and measurable; the explicit non-claim is appropriately confined to motivation.

## Recommended next step

Do not produce environment code next. Produce a consolidated `roadmap-v4.md` and `stage-0a-contract-v3.md` that resolve L1–L7, accompanied by a real failing/passing pytest suite for the hand-derived cases and mutants. The first acceptance test should demonstrate that the current print-only proof would pass even after a deliberately wrong formula, and that the replacement test fails.

## Remaining questions

- Is Paper 1 fundamentally about action-reachable observations or body membership? The current estimand supports the former.
- Is R2 essential to the primary paper, or can it become an `R`-target appendix until a redundant-actuator environment exists?
- Does the contribution require one scalar ranking of operating curves, or would a predeclared two-objective Pareto analysis be more honest?
- Which noncontrollable information must Paper 2 retain for task performance, and how will that relevance be labelled without reward leakage?
