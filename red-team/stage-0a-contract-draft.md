# Stage 0A: structural-causal environment contract (draft for discussion)

Status: draft skeleton, 6 September 2026. To be turned into code once agreed. Every item here is a decision to be made explicit before an estimator exists.

## A. Variables

- Actions `a_t` in R^K. Randomisable by the estimator (intervention channel).
- Body state `b_t` in R^N_b. Driven by `a_t` through the mapping `M_t` (see C).
- World state `w_t` in R^N_w. Exogenous dynamics, not action-reachable.
- Downstream effects `d_t` in R^N_d. Action-reachable through `b_t` but not body (e.g. an object the body pushes). Class (b) distractor in Codex C2.
- Exogenous action-correlated distractors `x_t` in R^N_x. Generated from a shared exogenous cause `u_t` that also shapes the *policy's* action choice, so that `x_t` correlates with `a_t` without any causal path from `a_t`. Class (a).
- Copied sensors `c_t`: duplicated or permuted copies of components of `b_t` or `w_t`. Class (c).
- Observation `o_t` = P_t · [b_t, w_t, d_t, x_t, c_t] + noise, with P_t a permutation and gain matrix (observation identity). Fixed total dimensionality across the episode, padded with inactive channels when N changes.

## B. Structural equations (to be written explicitly, one line per variable)

Linear first; a nonlinear family (e.g. saturating or piecewise) as the second dynamics family for external validity. Delays: `b_t` responds to `a_{t-τ}` with τ configurable. Noise: additive Gaussian per variable with declared scales.

## C. Ground-truth targets (three, kept separate)

1. **Controllability support** `S_t` ⊆ observation dims: dims with a directed causal path from `a_t` within horizon H. Declared per horizon. Note that `d_t` is inside S under a causal-reachability estimand and outside under a body-membership estimand. The paper declares which estimand it scores, and reports both.
2. **Action-to-effect mapping** `M_t`: the signed Jacobian of `b_{t+τ}` with respect to `a_t`. Changes under actuator remap or gain change even when `S_t` does not.
3. **Observation identity** `P_t`: which observation channel carries which underlying variable. Changes under sensor swap; `S_t` and `M_t` may not.

## D. Intervention semantics

- Estimator interventions: set `a_t` to a randomised value for a declared number of steps. The environment logs each as a probe. Probes may cost task reward.
- Environment change events (evaluator-only timestamps), each tagged with the target(s) it changes:
  - actuator remap or gain change: changes `M_t`, not `S_t`, not `P_t`
  - actuator loss: changes `S_t` and `M_t`
  - sensor dropout: changes `P_t` (channel goes inactive) and possibly `S_t` as observed
  - sensor swap: changes `P_t` only
  - morphology change: changes `S_t`, `M_t`, and padding pattern
- Change schedules: single unannounced change; ABA and ABC sequences with counterbalanced order and dwell time; bursty and Poisson schedules as held-out families.

## E. Invariants (become pytest tests)

1. With actions held at zero, `b_t` follows its passive dynamics; `x_t`, `w_t` unaffected by any action sequence (do-calculus check by simulation).
2. Randomising `a_t` changes the distribution of exactly the dims in `S_t` and no others, for each horizon H.
3. An actuator remap leaves `S_t` unchanged and changes `M_t` (asserted numerically).
4. A sensor swap leaves `S_t` and `M_t` unchanged and changes `P_t`.
5. `x_t` correlates with `a_t` under the default policy (correlation above a declared threshold) and is invariant under randomised `a_t`.
6. Determinism: same seed, same trajectory, byte-identical.
7. Evaluator-only fields are not readable from the agent-facing API (tested by interface, not convention).

## F. Estimator interface

Input: `o_t`, ability to request a probe, a fixed intervention budget. Output per step: a probability of controllability per observation dim (from a declared probabilistic model or a calibrator fitted on a separate calibration split), and an optional change alarm. Methods without native probabilities must pass through the calibrator; this is logged.

## G. Metrics (sequential definitions)

- Detection delay: steps from a change event to the first alarm satisfying a persistence rule of p consecutive steps; censored at the next event.
- False alarms: alarms during declared stationary windows; report average run length to false alarm.
- Support accuracy: per-dim F1 against `S_t` at fixed offsets after change, via out-of-band probe queries that do not update the estimator.
- Mapping error: Frobenius error of the estimated Jacobian against `M_t` where the method estimates one.
- Calibration: per-dim Brier and log loss, reliability plots in fixed transition windows; ECE secondary with fixed bins.
- Costs: probes used, environment samples, compute in operations, task regret to detection.

## H. Baselines for Stage 0A (frozen algorithms, one tuning budget each)

Random; temporal correlation at a declared lag set and window; forward-model residual with declared architecture and retraining schedule; IBD as published (randomised-action two-sample tests with FDR), reproduced to its published qualitative checks. Stage 0B adds: Bayesian change-point detector in three variants (correctly specified, misspecified residual, nonparametric), and a learned self-model with residual monitoring.

## I. Hardware protocol

Step and operation budgets primary. Randomised, interleaved condition order. Warm-up or declared cooldown before any timed run; log macOS thermal pressure and observed throughput. Wall-clock secondary and labelled.

## J. Deliverables for Stage 0A

Package with generator, contract as docstrings, pytest invariants, baseline implementations, a run ledger writer (JSONL: code hash, config hash, seed, budgets, thermal log, metrics), and a one-page README stating the estimand choices in section C.
