# Stage 0A contract v3.3 (consolidated, normative)

**Status:** version 3.3, 7 September 2026, after decisions D-6 (b), D-7 (a), D-8 (a). **Supersedes** `stage-0a-contract-v3.2.md`, `stage-0a-contract-v3.1.md`, `stage-0a-contract-v3.md`, `stage-0a-contract-draft.md`, `stage-0a-contract-v2.md`, `stage-0a-contract-v2.1.md`, `stage-0a-contract-v2.2.md`, and the contract-related patches in `gemini-v3.1/`, `gemini-v3.2/`, `gemini-v3.3/`. Incorporates Codex v3.4 findings L1, L4, L5, L9, L12, L13. Sections are marked **[N]** normative (implement exactly) or **[I]** informative.
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
| H_det | detection horizon for horizon-penalised detection time | 200 |
| ARL_0 | target average run length to false alarm, defined as the **fresh-start run length to first alarm** (D-6b; what a single-event episode experiences) | 1000 steps. **Calibration rule (D-2a):** on the calibration split, per (environment, regime, confounder, estimator) cell, shared across seeds, continue until ≥ 400 false-alarm run lengths are observed and the 95 percent interval for the mean run length lies inside [900, 1100]; hard cap 2,000,000 steps. A method that cannot attain the band is **never excluded**: it is reported under the predeclared partial-order endpoint (its best attainable (ARL, HPDT) pair) and the primary is not recomputed without it |
| probe_budget | fraction of environment steps on which the estimator may apply a randomised probe action | 0.05 (unit: probe steps / total steps); probe steps also charge task regret where a reward exists |
| γ_min | minimum retained effectiveness in partial actuator loss | 0.5, and instances are re-certified after the event so that γ·e_j > ε on every affected channel |
| f_conf | fraction of distractor channels that are confounded (children of u); the rest are exogenous noise | 0.5 (locked, D-5) |
| ε_faith | faithfulness margin for zero-noise responses | = ε = 0.05 |
| T_E2 | sample length for T-E2c and T-E2d | 20,000 |
| N_x | distractor channel count = `distractor_level` | {10, 30, 100} |
| N_b, N_d, N_w, K | SCM dimensions (OP-15) | 4, 2, 4, 2 [provisional] |
| σ_b, σ_d, σ_w, σ_x, σ_o, σ_a, σ_u | noise scales (OP-15) | 0.1, 0.1, 0.1, 0.1, 0.05, 0.1, 1.0 [provisional] |
| episode_len, event_t | confirmation schedule (F7) | 2,000; 1,000 (D-6b) |
| offsets_F1 | offsets after the event at which support correctness is scored | {200, 500, 1000} |
| s, κ, m | family N saturation scale, quadratic gain, clip bound | 1.0, 0.1, 4.0 |
| ρ_cl | closed-loop spectral radius bound for A_b + B W_o diag(gain⊙avail) Assign_b (before clipping) | 0.98 |
| event_spacing | minimum steps between change events and before episode end | H_det + w_T = 250 |
| δ, δ0 | smallest effect of interest (R1) and non-superiority margin (R0), in HPDT steps | 20, 10; **frozen now**; pilot variance sets seed count only (CX-16) |

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

Family N: b_{t+1} = A_b b_t + tanh(B_t a_{t−τ} / s) · s + κ · clip(b_t ⊙ b_t, −m, m) + ε^b_t, with s, κ, m in the registry once set. Family N is required to be **empirically bounded and stationary**, not contractive (CX-09): T-L9b certifies bounded trajectories from 32 random initial states over 20,000 steps and agreement of stationary-mean estimates across four independent chains within δ_inv; instances failing either are resampled. No Lipschitz claim is made.

Stability [N] (L9, CL-9, FB-17, CX-03, GM2-3): spectral radius of A_b, A_d, A_w, A_x ≤ ρ_max; **closed-loop radius on the delay-augmented state** [b_t, …, b_{t−τ}; d_t; a_{t−1}, …, a_{t−τ}] with the policy's actual observed channels ≤ ρ_cl, certified at sampling and after every event (family N: empirical boundedness on the same augmented loop); |ρ_u| < 1; actions clipped; saturation fraction logged and **instances with saturation fraction > 0.05 are rejected** (OP-16); ρ_min certified after W_o, W_u are sampled; sampling rejects violations.
Faithfulness [N] (G5): nonzero entries of A_b, B_t have |entry| ≥ c_min; after sampling and after **every change event**, T-E1b checks that structurally reachable components have zero-noise open-loop responses above ε_faith; otherwise resample.
Common random numbers [N]: noise indexed by (seed, variable, t).

## C. Ground-truth objects [N]

C1 **Structural latent support** S^latent_{t,H}: components of z = [b; d; w; x] with a directed path from a_t within H steps, **counting delay τ so the first hit is at h = τ + 1** (empty for H ≤ τ), by graph reachability on the sign pattern of the full block adjacency (A_b, B_t, C_d, A_d, A_w, A_x). Exact. Reference `structural_reach_full`; tests T-C1-delay, T-C1-chain, T-K10.

C2 **Operational latent effect** e_{j,t} = max_{h≤H, a∈𝒜} ‖E[z_{j,t+h} | do(a_t = a, later actions 0)] − E[z_{j,t+h} | do(0)]‖, estimated by n_oracle paired samples with common random numbers. The oracle reports e_j with a simultaneous 99 percent interval over all (component, horizon, probe) triples by Bonferroni on paired-difference t-intervals (CX-15); an instance whose interval for any channel contains ε is **rejected and resampled**; certification is **repeated after every change event** (CL-8); the resampling rate and the distribution of min_j |e_j − ε| are logged and reported in the paper as a limitation (OP-23); `n_resamples` per instance enters the config hash; an appendix cell keeps near-threshold instances and scores them separately; a generator configuration with rejection rate above 20 percent is itself rejected (L4). Labels are "structurally exact, numerically certified".

C3 **Operational observed support** (L5): S^obs,ε_{t,H} = { c : avail_t(c) = 1, Assign_t(c) = j ≠ ∅, |gain_t(c)| · e_{j,t} > ε }. Gain is part of the definition; a gain event may change S^obs,ε. Test T-C3, T-L5.

C4 **Open-loop response** R_{t,h}(a) = E[b_{t+h} | do(a_t = a, a_{t+1..t+h−1} = 0), z_t = z̄] − E[b_{t+h} | do(0, ..., 0), z_t = z̄], a ∈ 𝒜, h ∈ ℋ, z̄ the stationary mean estimated after burn_in (family L: z̄ = 0 is exact; family N: the empirical z̄ is used and the response is not odd in a, T-C4-N). **R is indexed by all |𝒜| = 2K probes in the frozen order (+e_1, −e_1, …, +e_K, −e_K)**; the Jacobian M is a separate object exposed for family L only (CL-7, CX-04). Family L closed form: M_{t,h} = 0 for h ≤ τ, A_b^{h−1−τ} B_t for h > τ. Tests T-G1, T-G2.

C5 **Observation map** P_t = (Assign_t, gain_t, avail_t). Copies scored as equivalence classes.

C6 **Estimand naming** (L13): the primary quantity is **action-reachable observation support**, not body membership. Body membership B^obs (channels assigned to b) is an oracle-only construct reported in an appendix and never inferred from reachability. Downstream channels d are inside S and outside B by design; examples must include one.

## D. Events and schedules [N]

Events with their **computed** effect on the four objects (the oracle decides; the table is a prediction checked by T-D):

| Event | Mechanism | Predicted effect |
|---|---|---|
| actuator remap / gain | B_t ← Π B_t or D B_t | R changes; S^latent generically unchanged |
| actuator loss, complete | column k of B_t ← 0 | S changes iff reachability changes (coupling, horizon); R changes |
| actuator loss, partial | column k of B_t ← γ · column, γ_min ≤ γ < 1 | R changes; S unchanged (structural); post-event re-certification guarantees S^obs,ε unchanged (CL-8) |
| sensor dropout | avail_t(c) ← 0 | S^obs changes iff c ∈ S^obs; P changes |
| sensor swap | rows c1, c2 of Assign_t exchanged | S^obs changes iff exactly one of c1, c2 ∈ S^obs; P changes |
| sensor gain | gain_t(c) ← g′ | P changes; S^obs,ε changes iff |g′| e_j crosses ε (T-L5 covers 0, near-0, sign flip) |
| morphology | N_b changes with padding | all may change |

Primary-cell instance constraint (CL-4): for confirmatory cells the lost actuator's column must reach ≥ 1 component with no alternative path within H, so that S^obs,ε changes; the oracle certifies and `confirmation-design.csv` carries `s_change_certified`.
Schedules (spacing ≥ event_spacing, T-G-spacing; administrative censoring is thereby excluded): single unannounced change; ABA, ABC with equal dwell and transition counts; A′ (unseen, structurally matched); Poisson and bursty held-out families, generated and hashed before development ends.

## E. Correctness gate [N]

E1 **Structural tests** (exact): T-E1a graph has no action ancestor for x or w and has one for d; T-E1b two independent label derivations (graph reachability; zero-noise finite-difference) agree on every sampled instance and after every event.
E2 **Statistical tests** (tolerance, power, n_oracle declared): T-E2a invariance for non-reachable components (mean-difference, valid for constant probes); T-E2b sensitivity for reachable components; T-E2c confounding present observationally (T = T_E2): a generated witness pair (k, j) with |corr(a_k, x_j)| ≥ ρ_min, both columns non-degenerate; zero-variance non-witness pairs are skipped, not failed (CX-14); a fraction f_conf of distractor channels are children of u and the median |corr| over confounded channels is reported (GM-7); T-E2d confounding severed under randomised do(a ~ Uniform(𝒜)), T = T_E2: max pairwise |corr| ≤ max(δ_inv, 3·sqrt(2 ln(K·N_x) / T)) (multiplicity-aware, OP-24); constant probes return NaN and are rejected by the test, never silently passed.
E3 **Mutants** (each must make ≥ 1 test fail; `mutants.py` runs them and exits non-zero on any survivor): executable today: M1 leak a into x; M7 negative-power Jacobian; M8 gain ignored; delay cap (Codex); 999·B delayed Jacobian (Gemini); skip-H2 reachability (Gemini); no-delay and no-downstream reachability (Claude); censoring excluded from HPDT. **Uncovered until the generator and oracle exist:** M2 swap bookkeeping; M3 loss on observation; M4 unpaired noise; M5 oracle reads event type; M6 evaluator readable (CL-3).
E4 **Determinism**: same host bitwise; cross host within tolerance with identical config hash.
E5 **Isolation**: oracle in a separate process; candidate receives serialised observations only; canary field test.
E6 **Independent acceptance** (L16): a black-box acceptance suite written from `interface-spec-v3.md` (a one-page frozen interface), not from the implementation; plus one hand-computed rectangular, noisy case exercising every outcome class (detected, missed, terminated) that Daniel checks against both the pipeline and `contract_ref.py` (OP-31).

## F. Estimator interface [N]

Per step: p_c ∈ [0,1] per channel (probability c ∈ S^obs,ε; from a declared probabilistic model or a calibrator fitted on a separate split; logged); α^S_t ∈ {0,1}. Optional, scored only in later phases or appendices: α^R_t, R̂, assignment distributions. **Paper 1 scores p_c and α^S only.** Every baseline declares its **information set** (L10): which channels, whether oracle coordinates or P are visible, whether probe data may train the controller. The estimator receives full transitions (`interface-spec-v3.md`), including the applied action and probe marker (CX-03). **Misspecification registry** (CX-18): R1 transforms are frozen and hashed: family L drift = parameters of the residual model fitted on pre-drift data then held while A_b, B_t are perturbed by +10 percent on the diagonal; family N = linear residual model fitted on family N data; T2 = linear autoregressive residual model. R0 on T2 (CL-5, GM-5) = an MLP residual model trained to convergence on 200,000 fault-free in-distribution steps with a Ljung-Box whiteness test on innovations at the pilot.

## G. Metrics [N]

- Alarm counted after p consecutive raises; refractory r. **Detection** = first counted alarm with event_t < alarm_t ≤ event_t + H_det. w_T is used only to match alarms to the nearest event when several exist (F5; the merge rule is deleted).
- **Confounder absent (F7, OP-21)** = the **same instance draw and the same noise streams** as the matching present cell, with G = 0 and W_u unchanged; present/absent differences are within-instance contrasts.
- **Detection outcome per event**: detected within H_det steps, or censored (missed, next event, episode end, early termination). Early termination is a competing outcome and is reported, never excluded (L11).
- **Primary outcomes (D-8a).** (P1) **Support correctness**: per-channel F1 of the thresholded p_c (threshold 0.5) against S^obs,ε at offsets_F1 after the event, via out-of-band probes that do not update the estimator; reported per offset, primary offset 500. (P2) **Confounded-channel false support** (below). Both co-equal, tested hierarchically: P1 first, P2 only if P1 passes. Decision rules for P1: Δ_F1 = F1(seq-IBD) − F1(comparator) at the primary offset, per-seed paired, equal-weight over levels and delays; R1 superiority if the lower bound > δ_F1 = 0.10 on both SCM families and the sign holds on both control-tier environments; R0 validated by TOST inside (−δ0_F1, +δ0_F1) with δ0_F1 = 0.05; interaction I on Δ_F1 within environment as in v4.1 E1; futility if the upper bound < δ_F1 on either SCM family. Effect sizes provisional until the pilot's power arm, then frozen; the pilot may change seed count only.
- **Descriptive delay outcome** (formerly primary): **horizon-penalised detection time** HPDT = mean over events of min(delay, H_det) for detected events and H_det for missed or terminated events (a composite outcome by decision, not a restricted mean over right-censored times). Administrative censoring cannot occur because schedules satisfy event_spacing (T-G-spacing). Detection probability within H_det and the early-termination rate are reported alongside. (P2) Co-primary outcome (locked, D-5; CX-07, GM2-6): **confounded-channel false support** = mean p_c over oracle-labelled confounded distractor channels at offsets {10, 50, 200} after the event; unconfounded distractors reported as a negative control; each offset reported with the fraction of runs for which it exists; the estimator-to-p_c mapping is a frozen isotonic calibrator fitted on the calibration split (FB-18). For the channel-agnostic CUSUM arm, p_c is derived from per-channel innovation statistics through the same calibrator (OP-13).
- **False-alarm control**: thresholds calibrated on a separate calibration split to a predeclared ARL_0; the primary comparison is made **at matched ARL_0**, so operating-curve supports cannot be disjoint. Full delay-versus-log-ARL curves reported descriptively; pAUC secondary only; disjoint curves reported as a partial order, never as a scalar.
- Support F1 at fixed offsets via out-of-band probes; Brier and log loss raw and calibrated; calibration split by whole configuration and schedule; ECE diagnostic with fixed bins.
- **Alarm matching (OP-12):** reference `match_alarms(alarm_times, event_times, H_det, r, p) -> (delays, outcomes)` in `contract_ref.py`, tested; an alarm at delay d ∈ (0, H_det] after event e and before the next event is attributed to e.
- **Pairwise handling of out-of-band methods (OP-11):** if either arm of a (seed, cell) pair is outside the ARL band, the pair is reported in the partial-order endpoint, the exclusion rate is reported by regime and arm, a maximum tolerable rate of 10 percent is predeclared (above it the primary is inconclusive), and a sensitivity analysis imputes such pairs at H_det.
- **Per-environment outcome classes (OP-29/30):** Pendulum-v1 and PointMass2D never terminate, so `terminated` is structurally zero there and is reported as such; offsets that do not exist for a run are reported with their denominator.
- Costs: probes (in probe steps, see probe_budget), samples, operations; task regret only where a reward is declared.
- **Out-of-band scoring queries** (CX-17): the evaluator scores support via a snapshot-and-branch API with common random numbers; the live environment state, RNG and estimator bytes are asserted unchanged after scoring (T-OOB).

## H. Baselines for Stage 0A [N]

**Confirmatory arms (D-3a, D-7a).** (1) **Sequential IBD**, a windowed many-sample two-sample test over post-block probe pairs against a frozen reference, specified in `sequential-ibd-spec.md` (draft 2, under D-8). (2) **Passive comparator**: CUSUM on innovations of a channel-agnostic linear predictor in every cell; its per-channel support scores are innovation statistics through the frozen calibrator (expected to fail under confounding). (3) **Probed comparator** (D-7a): the same CUSUM run on streams carrying the identical randomised probe injections (same schedule and seed) as arm 1, separating "having interventions" from "using them causally". Arm 2 vs arm 1 is the headline; arm 3 vs arm 1 is the mechanism control. R0 = the linear predictor fitted on in-distribution fault-free data (correct only on family L; on family N and T2 it is the best linear model). R1 = the same predictor class under the frozen misspecification transform. The words "correct model" are dropped everywhere. Sequential IBD is specified in `sequential-ibd-spec.md` (D-4a), normative once signed by Daniel. Every estimator's `update` returns a **continuous statistic** alongside the binary alarm so the harness can calibrate a threshold (OP-4; interface v3).


Roles (CX-10): confirmatory pair = sequential IBD and channel-agnostic CUSUM; descriptive (frozen matrix, 3 seeds) = random, temporal correlation, forward-model residual; appendix references = oracle-coordinate CUSUM, Bayesian model-informed.


Random; temporal correlation (lag set, window, statistic frozen); forward-model residual (architecture, optimiser, retraining schedule frozen); IBD as published, reproduced to numerical anchors from its paper on a static case, noting its ~32k-step probe phase; Sequential re-probing is specified in `sequential-ibd-spec.md`.

## H2. Control-tier environments for Paper 1 [N] (D-1a)

- **PointMass2D** (new, in-repo, numpy): a 2-D point mass with two independent thrusters (K = 2), mass 1, linear drag 0.1, dt 0.05, continuous actions clipped to [−a_max, a_max]; body channels = (x, y, vx, vy); no termination; episode per registry. The axes are uncoupled, so losing thruster k removes (x_k, v_k) from the reachable support without ending the episode. Confounded distractors and exogenous channels are appended exactly as in the SCM. Ground truth by construction and certified by the oracle.
- **Pendulum-v1** (Gymnasium): one continuous torque in [−2, 2]; `TimeLimit` replaced by the registry episode length (disclosed); no natural termination; complete loss empties the support without termination. Distractors appended as above.
- CartPole is **not** used (FB-7, OP-6/7): a single-actuator balancing task terminates under complete loss and has a discrete action space.
- Default policies: a linear feedback controller for PointMass2D and an energy-shaping controller for Pendulum, each with additive action noise; the confounding injection is bounded so the saturation fraction stays below 0.2.

## I. Hardware protocol [N]

Step and operation budgets primary; serial heavy runs; 60 s cooldown between blocks; thermal pressure and throughput logged; wall-clock secondary. **A runtime pilot (T-I) measures per-cell duration before any calendar commitment** (L14).

## J. Deliverables [N]

Environment (CX-02, GM-9): `executable-proofs/gate/requirements.txt`; `run_gate.py` verifies the interpreter and dependencies and exits 2 if numpy is missing; the documented command is `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && python run_gate.py`. The readiness criterion is the exit code of that command from a clean checkout.


`interface-spec-v3.md` (frozen, one page); package with declarative SCM, generator, separate oracle package, gate tests and mutants, baselines, ledger with manifests; `coverage-matrix.md`; runtime pilot report. Package name: **to be chosen after a collision check** (L17); `boundary-bench` is taken.

## K. Hand-derived cases [I, tested]

All of K1, K3, K4, K5, K7, K10 are tests in `test_gate.py` (GM-6); K2, K6, K8, K9 are covered by T-K1, T-E2, T-L5, T-L12 respectively.

As in v2.2 section K (six cases), plus: K7 partial actuator loss γ = 0.5 (R changes, S unchanged); K8 sensor gain 0, 0.01, −1 on a controllable channel (S^obs,ε: removed, removed, kept); K9 rectangular B with N_b = 3, K = 2; K10 downstream channel d inside S and outside B. Each case is a test in `executable-proofs/gate/test_gate.py`.
