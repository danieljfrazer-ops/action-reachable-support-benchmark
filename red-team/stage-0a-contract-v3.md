# Stage 0A contract v3 (consolidated, normative)

**Status:** version 3, 6 September 2026. **Supersedes** `stage-0a-contract-draft.md`, `stage-0a-contract-v2.md`, `stage-0a-contract-v2.1.md`, `stage-0a-contract-v2.2.md`, and the contract-related patches in `gemini-v3.1/`, `gemini-v3.2/`, `gemini-v3.3/`. Incorporates Codex v3.4 findings L1, L4, L5, L9, L12, L13. Sections are marked **[N]** normative (implement exactly) or **[I]** informative.
**Gate:** `executable-proofs/gate/` contains assertion tests and mutants; `coverage-matrix.md` maps every normative item to a test ID. A normative item without a test ID is not implemented until it has one.

## 0. Constants registry [N]

| Name | Meaning | Value (provisional until pilot; frozen before confirmation) |
|---|---|---|
| ε | operational effect threshold | 0.05 (in observation units after gain) |
| H | support horizon | 3 |
| ℋ | response horizons | {1, 2, 3} |
| 𝒜 | probe set | ± e_k, magnitude 1.0, k = 1..K |
| c_min | faithfulness margin on nonzero entries | 0.2 |
| ρ_max | spectral radius bound for A_b, A_d, A_w, A_x | 0.95 |
| ρ_u | context autocorrelation | 0.8 (|ρ_u| < 1 required) |
| a_max | action clip | 2.0 |
| ρ_min | confounding floor, max pairwise |corr(a_k, x_j)| | 0.4 |
| δ_inv | invariance tolerance | 0.05 |
| n_oracle | paired Monte Carlo samples for operational labels | 4096 |
| burn_in | steps before stationary mean estimate | 2000 |
| p, r, w_T | alarm persistence, refractory, event-matching window | 3, 20, 50 |
| H_det | detection horizon for restricted mean detection time | 200 |

## A. Variables [N]

| Symbol | Dim | Role | Action ancestor? |
|---|---|---|---|
| a_t | K | action, clipped to [−a_max, a_max] | n/a |
| u_t | n_u | exogenous context; private cue to the default policy; parent of x | no |
| b_t | N_b | body latent | yes, via B_t |
| d_t | N_d | downstream latent; child of b; not body | yes, via b |
| w_t | N_w | exogenous world latent | no |
| x_t | N_x | exogenous action-correlated distractor; child of u | no |
| z_t = [b; d; w; x] | N_z | all latents | |
| o_t | C (fixed) | observation channels incl. padding and copies | |

N_b ≠ K is permitted and must be tested (rectangular B).

## B. Structural equations [N]

Family L:
- u_t = ρ_u u_{t−1} + ε^u_t
- a_t = clip(W_o o_t + W_u u_t + ε^a_t) under the default policy; a_t := a* under do(a_t = a*)
- b_{t+1} = A_b b_t + B_t a_{t−τ} + ε^b_t
- d_{t+1} = A_d d_t + C_d b_t + ε^d_t
- w_{t+1} = A_w w_t + ε^w_t
- x_{t+1} = A_x x_t + G u_t + ε^x_t (no action parent; structural fact, tested by graph inspection T-E1a)
- o_t = avail_t ⊙ gain_t ⊙ (Assign_t z_t) + ε^o_t, Assign_t ∈ {0,1}^{C×N_z} with at most one 1 per row

Family N: b_{t+1} = A_b b_t + tanh(B_t a_{t−τ} / s) · s + κ · clip(b_t ⊙ b_t, −m, m) + ε^b_t, with s, κ, m in the registry once set. Family N must be **contractive on the reachable set**: certified empirically by T-L9b (bounded trajectories from 32 random initial states over 20,000 steps, and stationary-mean estimates from two independent burn-ins agreeing within δ_inv).

Stability [N] (L9): spectral radius of A_b, A_d, A_w, A_x ≤ ρ_max; |ρ_u| < 1; actions clipped; sampling rejects violations.
Faithfulness [N] (G5): nonzero entries of A_b, B_t have |entry| ≥ c_min; after sampling and after **every change event**, T-E1b checks that structurally reachable components have zero-noise open-loop responses above ε_faith; otherwise resample.
Common random numbers [N]: noise indexed by (seed, variable, t).

## C. Ground-truth objects [N]

C1 **Structural latent support** S^latent_{t,H}: components with a directed path from a_t within H steps, by graph reachability on the sign pattern of (A_b, B_t, C_d, ...). Exact. Test T-C1.

C2 **Operational latent effect** e_{j,t} = max_{h≤H, a∈𝒜} ‖E[z_{j,t+h} | do(a_t = a, later actions 0)] − E[z_{j,t+h} | do(0)]‖, estimated by n_oracle paired samples with common random numbers. The oracle reports e_j with a 99 percent interval; an instance whose interval for any channel contains ε is **rejected and resampled** (L4). Labels are "structurally exact, numerically certified".

C3 **Operational observed support** (L5): S^obs,ε_{t,H} = { c : avail_t(c) = 1, Assign_t(c) = j ≠ ∅, |gain_t(c)| · e_{j,t} > ε }. Gain is part of the definition; a gain event may change S^obs,ε. Test T-C3, T-L5.

C4 **Open-loop response** R_{t,h}(a) = E[b_{t+h} | do(a_t = a, a_{t+1..t+h−1} = 0), z_t = z̄] − E[b_{t+h} | do(0, ..., 0), z_t = z̄], a ∈ 𝒜, h ∈ ℋ, z̄ the stationary mean estimated after burn_in. Family L closed form: M_{t,h} = 0 for h ≤ τ, A_b^{h−1−τ} B_t for h > τ. Tests T-G1, T-G2.

C5 **Observation map** P_t = (Assign_t, gain_t, avail_t). Copies scored as equivalence classes.

C6 **Estimand naming** (L13): the primary quantity is **action-reachable observation support**, not body membership. Body membership B^obs (channels assigned to b) is an oracle-only construct reported in an appendix and never inferred from reachability. Downstream channels d are inside S and outside B by design; examples must include one.

## D. Events and schedules [N]

Events with their **computed** effect on the four objects (the oracle decides; the table is a prediction checked by T-D):

| Event | Mechanism | Predicted effect |
|---|---|---|
| actuator remap / gain | B_t ← Π B_t or D B_t | R changes; S^latent generically unchanged |
| actuator loss, complete | column k of B_t ← 0 | S changes iff reachability changes (coupling, horizon); R changes |
| actuator loss, partial | column k of B_t ← γ · column, 0 < γ < 1 | R changes; S unchanged (structural); S^obs,ε may change only if e_j crosses ε, which certified instances exclude |
| sensor dropout | avail_t(c) ← 0 | S^obs changes iff c ∈ S^obs; P changes |
| sensor swap | rows c1, c2 of Assign_t exchanged | S^obs changes iff exactly one of c1, c2 ∈ S^obs; P changes |
| sensor gain | gain_t(c) ← g′ | P changes; S^obs,ε changes iff |g′| e_j crosses ε (T-L5 covers 0, near-0, sign flip) |
| morphology | N_b changes with padding | all may change |

Schedules: single unannounced change; ABA, ABC with equal dwell and transition counts; A′ (unseen, structurally matched); Poisson and bursty held-out families, generated and hashed before development ends.

## E. Correctness gate [N]

E1 **Structural tests** (exact): T-E1a graph has no action ancestor for x or w and has one for d; T-E1b two independent label derivations (graph reachability; zero-noise finite-difference) agree on every sampled instance and after every event.
E2 **Statistical tests** (tolerance, power, n_oracle declared): T-E2a invariance for non-reachable components (mean-difference, valid for constant probes); T-E2b sensitivity for reachable components; T-E2c confounding present observationally: **max pairwise** |corr(a_k, x_j)| ≥ ρ_min, with a generated witness pair (k, j) that must exceed ρ_min (L12); T-E2d confounding severed under randomised do(a ~ Uniform(𝒜)): max pairwise |corr| ≤ δ_inv; constant probes return NaN and are rejected by the test, never silently passed.
E3 **Mutants** (each must make ≥ 1 test fail): M1 leak a into x; M2 swap bookkeeping without Assign update; M3 loss applied to observation not B; M4 unpaired probe noise; M5 oracle reads event type instead of reachability; M6 evaluator field readable through the agent API; M7 negative-power Jacobian; M8 gain ignored in S^obs,ε.
E4 **Determinism**: same host bitwise; cross host within tolerance with identical config hash.
E5 **Isolation**: oracle in a separate process; candidate receives serialised observations only; canary field test.
E6 **Independent acceptance** (L16): a black-box acceptance suite written from `interface-spec.md` (a one-page frozen interface), not from the implementation; plus one hand-computed rectangular, noisy, censored case that Daniel checks against both the pipeline and `contract_ref.py`.

## F. Estimator interface [N]

Per step: p_c ∈ [0,1] per channel (probability c ∈ S^obs,ε; from a declared probabilistic model or a calibrator fitted on a separate split; logged); α^S_t ∈ {0,1}. Optional, scored only in later phases or appendices: α^R_t, R̂, assignment distributions. **Paper 1 scores p_c and α^S only.** Every baseline declares its **information set** (L10): which channels, whether oracle coordinates or P are visible, whether probe data may train the controller.

## G. Metrics [N]

- Alarm counted after p consecutive raises; refractory r; matching window w_T; events closer than w_T merged.
- **Detection outcome per event**: detected within H_det steps, or censored (missed, next event, episode end, early termination). Early termination is a competing outcome and is reported, never excluded (L11).
- **Primary delay estimand** (L3): restricted mean detection time RMDT = mean over events of min(delay, H_det), with censored events counted at H_det. Detection probability within H_det reported alongside.
- **False-alarm control**: thresholds calibrated on a separate calibration split to a predeclared ARL_0; the primary comparison is made **at matched ARL_0**, so operating-curve supports cannot be disjoint. Full delay-versus-log-ARL curves reported descriptively; pAUC secondary only; disjoint curves reported as a partial order, never as a scalar.
- Support F1 at fixed offsets via out-of-band probes; Brier and log loss raw and calibrated; calibration split by whole configuration and schedule; ECE diagnostic with fixed bins.
- Costs: probes, samples, operations; task regret only where a reward is declared.

## H. Baselines for Stage 0A [N]

Random; temporal correlation (lag set, window, statistic frozen); forward-model residual (architecture, optimiser, retraining schedule frozen); IBD as published, reproduced to numerical anchors from its paper on a static case, noting its ~32k-step probe phase; sequential re-probing is new engineering and is labelled as such. Stage 0B adds: **channel-agnostic CUSUM on innovations of a linear predictor** (the frozen fair classical competitor), an **oracle-coordinate CUSUM** (labelled reference with privileged information), and one Bayesian model-informed reference.

## I. Hardware protocol [N]

Step and operation budgets primary; serial heavy runs; 60 s cooldown between blocks; thermal pressure and throughput logged; wall-clock secondary. **A runtime pilot (T-I) measures per-cell duration before any calendar commitment** (L14).

## J. Deliverables [N]

`interface-spec.md` (frozen, one page); package with declarative SCM, generator, separate oracle package, gate tests and mutants, baselines, ledger with manifests; `coverage-matrix.md`; runtime pilot report. Package name: **to be chosen after a collision check** (L17); `boundary-bench` is taken.

## K. Hand-derived cases [I, tested]

As in v2.2 section K (six cases), plus: K7 partial actuator loss γ = 0.5 (R changes, S unchanged); K8 sensor gain 0, 0.01, −1 on a controllable channel (S^obs,ε: removed, removed, kept); K9 rectangular B with N_b = 3, K = 2; K10 downstream channel d inside S and outside B. Each case is a test in `executable-proofs/gate/test_gate.py`.
