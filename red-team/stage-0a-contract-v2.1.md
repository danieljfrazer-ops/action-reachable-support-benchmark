# Stage 0A contract v2.1: executable structural-causal environment specification

Status: version 2.1, 6 September 2026. Supersedes v2 after the Gemini audit (G1, G2, G3, G5, G6). Patched sections are marked [v2.1]. Every equation in this contract ships with an executable check in `executable-proofs/`; the building agent must run them before scaffolding.

## A. Variables and dimensions

| Symbol | Dim | Role | Action parent? |
|---|---|---|---|
| a_t | K | action | n/a |
| u_t | n_u | exogenous context; private cue to the default policy; parent of x | no |
| b_t | N_b | body latent | yes, via B_t |
| d_t | N_d | downstream latent; child of b, not body | yes, via b |
| w_t | N_w | world latent; exogenous | no |
| x_t | N_x | exogenous action-correlated distractor; child of u | no |
| z_t = [b_t; d_t; w_t; x_t] | N_z | all latents | |
| o_t | C (fixed) | observation channels, including padding and copies | |

C is fixed for the whole episode. Channels are either assigned to one latent component, or unassigned (padding). Several channels may be assigned to the same latent component (copies).

## B. Structural equations

Linear family (family L):

- u_t = ρ_u u_{t-1} + ε^u_t, ε^u ~ N(0, σ_u² I)
- a_t = π(o_t, u_t) + ε^a_t under the default policy; a_t := a* under do(a_t = a*). The default policy is a fixed linear map π(o, u) = W_o o + W_u u with W_u ≠ 0, so that a_t correlates with u_t observationally.
- b_{t+1} = A_b b_t + B_t a_{t-τ} + ε^b_t
- d_{t+1} = A_d d_t + C_d b_t + ε^d_t
- w_{t+1} = A_w w_t + ε^w_t
- x_{t+1} = A_x x_t + G u_t + ε^x_t. **x has no action parent.** This is a structural fact of the equation, testable by inspection of the declarative graph, not by simulation.
- o_t = avail_t ⊙ (gain_t ⊙ (Assign_t z_t)) + ε^o_t

where Assign_t ∈ {0,1}^{C×N_z} has at most one 1 per row (each channel reads at most one latent), gain_t ∈ R^C, avail_t ∈ {0,1}^C.

Nonlinear family (family N): replace B_t a_{t-τ} by σ(B_t a_{t-τ}) with σ a saturating elementwise map (tanh with declared scale), and A_b with a mildly nonlinear map A_b b_t + κ b_t ⊙ b_t clipped. Family N must differ structurally from L (saturation and state-dependent gain), not only by parameters.

All noise terms are independent Gaussians with declared scales. Delay τ ≥ 0 declared. Common random numbers: every noise stream is indexed by (seed, variable, t) so that observational and interventional branches can be paired.

**Faithfulness constraint [v2.1] (G5).** Every nonzero entry of A_b and B_t satisfies |entry| ≥ c_min (declared, default 0.2). After sampling, the oracle checks that for every latent component reachable in the graph the zero-noise finite-difference response over 𝒜 × ℋ exceeds ε_faith > 0; if any reachable component has a cancelled response, the matrices are resampled. This guarantees that the structural label (C1) and the operational label (C2) agree on the sampled instance.

## C. Ground-truth targets (four objects; two coordinate systems)

**C1. Structural latent support.** S^latent_{t,H} = { j : there is a directed path a_t → z_{j,t+h} in the SCM graph at time t, for some 1 ≤ h ≤ H }. Computed by graph reachability on the declarative SCM, by an oracle module that does not share code with the generator. Note b-components may reach each other through A_b, so an actuator loss does not necessarily remove a component from S^latent; the label comes from reachability, never from the event type.

**C2. Operational latent support.** S^latent,ε_{t,H} = { j : max_{h≤H} ‖E[z_{j,t+h} | do(a_t = a)] − E[z_{j,t+h} | do(a_t = 0)]‖ > ε for some a in the frozen probe set 𝒜 }. Estimated by paired common-random-number simulation. Reported sensitivity to ε and H. The structural label is used for generator correctness; the operational label is used for detection scoring.

**C3. Observation-channel supports.** S^obs_{t,H} = { c : avail_t(c) = 1 and Assign_t(c) ∈ S^latent_{t,H} }, and likewise S^obs,ε. **Body-membership** support B^obs_t = { c : avail_t(c)=1 and Assign_t(c) is a b-component }. Paper 1 scores S^obs,ε as primary and reports B^obs as an alternative estimand in an appendix.

**C4. Action-effect response [v2.1].** R is defined as the **open-loop** impulse response: subsequent actions are clamped to zero so that the default policy's feedback cannot re-enter through the observation map.

R_{t,h}(a) = E[b_{t+h} | do(a_t = a, a_{t+1} = 0, …, a_{t+h-1} = 0), z_t = z̄] − E[b_{t+h} | do(a_t = 0, …, a_{t+h-1} = 0), z_t = z̄]

for a ∈ 𝒜 (frozen probe set of 2K scaled unit vectors ± e_k), h ∈ ℋ (declared horizon set), z̄ the stationary mean under the default policy. Because the policy is excluded, R is invariant to Assign, gain and avail (Table D holds). Verified numerically in `executable-proofs/gemini_checks.py` (G1): under the closed-loop definition a sensor swap changed R at h ≥ 2; under the open-loop definition it does not.

For family L this reduces to the piecewise causal Jacobian: M_{t,h} = 0 for h ≤ τ, and M_{t,h} = A_b^{h-1-τ} B_t for h > τ. Negative matrix powers are never computed (G2). Mapping error is ‖R̂ − R‖ / ‖R‖ over 𝒜 × ℋ.

**C5. Observation map.** P_t = (Assign_t, gain_t, avail_t). Identity scoring: an estimator emits, per channel, a distribution over latent components (or "unassigned"). Copies are scored as equivalence classes: predicting any member of the class of the true component is correct.

## D. Intervention semantics and change events

Estimator probes: set a_t = a* for a declared number of steps; each probe is logged with its cost. Whether probe data may train the controller is a declared regime flag.

Change events (evaluator-only timestamps), each labelled by which of the four objects it actually changes, **computed, not assumed**:

| Event | Mechanism | S^latent | S^obs | R | P |
|---|---|---|---|---|---|
| actuator remap or gain | B_t ← Π B_t or D B_t | unchanged (generic) | unchanged | changed | unchanged |
| actuator loss | column k of B_t ← 0 | changed iff reachability changes | follows S^latent | changed | unchanged |
| sensor dropout | avail_t(c) ← 0 | unchanged | changed iff c ∈ S^obs | unchanged | changed |
| sensor swap | rows c1, c2 of Assign_t exchanged | unchanged | changed iff exactly one of c1, c2 ∈ S^obs | unchanged | changed |
| sensor gain | gain_t(c) ← g' | unchanged | unchanged | unchanged | changed |
| morphology | N_b changes; padding channels assigned or freed | changed | changed | changed | changed |

The oracle recomputes all four objects after every event; the table is a prediction to be verified by the oracle, and a mutant test must catch any bookkeeping that disagrees with it.

Schedules: single unannounced change; ABA and ABC with equal dwell times and transition counts; A′ (unseen morphology structurally matched to A); Poisson and bursty schedules as held-out families, generated and hashed before development ends.

## E. Correctness gate: three classes of test plus isolation

**E1. Structural tests (exact, on the declarative SCM).**
- x has no action ancestor; w has no action ancestor; d has an action ancestor through b; every b-component has an action ancestor iff its column of B or a coupled component is nonzero.
- Two independent label derivations agree on tiny cases: (i) graph reachability on the declarative SCM; (ii) finite-difference interventions with common random numbers at zero noise. Disagreement fails the build.

**E2. Statistical tests [v2.1] (tolerance and power declared).**
- Invariance: for each component j ∉ S^latent_{t,H}, max_{h≤H} ‖E[z_{j,t+h} | do(a_t = a)] − E[z_{j,t+h} | do(a_t = 0)]‖ ≤ δ_inv over a ∈ 𝒜, at declared power over n paired seeds. This is a mean-difference test and is valid for constant probes.
- Sensitivity: for each j ∈ S^latent,ε, the paired difference exceeds ε with declared power.
- Confounding present (observational): under the default policy, |corr(a_t, x_{t+1})| ≥ ρ_min > 0 across seeds.
- Confounding severed (interventional): under a **randomised** interventional policy do(a_t ~ Uniform(𝒜)), so that Var(a_t) > 0, |corr(a_t, x_{t+1})| ≤ δ_inv. A constant probe do(a_t = a*) has zero variance and yields NaN in a correlation; it is never used for this test (G3, verified: observational 0.86, constant probe NaN, randomised 0.00).

**E3. Mutant generators (each must be rejected by at least one test).**
- M1: leak a term of a_t into x. M2: swap bookkeeping updates S^obs without updating Assign. M3: actuator loss implemented on the observation instead of B. M4: probe noise not paired. M5: oracle reads the event type instead of recomputing reachability. M6: evaluator field readable through the agent API.

**E4. Determinism.** Same host: bitwise-identical trajectories for the same seed. Cross host: within a declared numerical tolerance, with identical configuration hashes.

**E5. Isolation.** Ground truth lives in a separate package and process; the candidate receives serialised observations and probe responses only. A canary field in the evaluator state fails the build if any candidate code path reads it.

## F. Estimator interface (typed, mandatory outputs)

Per step, every estimator returns:
1. p_c ∈ [0,1] for each channel c: probability that c ∈ S^obs,ε. From a declared probabilistic model, or from a calibrator fitted on a separate calibration split (section G). Passage through the calibrator is logged.
2. Typed alarms α^S_t, α^R_t, α^P_t ∈ {0,1}: a change in support, response, or observation map is declared. An estimator without a native mechanism for a target emits a declared constant (usually 0), which is scored as such.
3. Optional but scored if present: R̂_{t,h}(a) over 𝒜 × ℋ; per-channel assignment distributions.

**Paper 1 scoring [v2.1] (G6).** Paper 1 baselines are scored **exclusively** on p_c (support S^obs,ε) and α^S (support-change alarm). R and P remain ground-truth objects in the contract for generator and oracle verification and for the mutant tests, and are scored only for methods that natively estimate them, in later phases. No estimator emits dummy constants for scoring; a constant output has no operating curve and would produce a fictitious comparison.

## G. Metrics (sequential definitions, frozen)

- **Alarm persistence:** an alarm counts when raised on p consecutive steps (p declared per target). After a counted alarm the detector is reset by a declared rule and a refractory window r applies.
- **Detection delay** per event and target: steps from the event to the first counted alarm of that type, censored at the next event of any type or at the episode end; censored delays reported separately.
- **False alarm:** a counted alarm of type T outside a matching window [event, event + w_T] of any event that changes T. Events closer than w_T are merged for matching.
- **Average run length (ARL)** to false alarm per target: mean steps between counted false alarms in declared stationary windows, with a bootstrap interval clustered by seed.
- **Operating curve:** for each estimator, detection delay versus ARL over a predeclared threshold sweep; threshold-selection data are separate from confirmation data.
- **Support accuracy:** per-channel F1 against S^obs,ε at fixed offsets after events, via out-of-band probe queries that do not update the estimator.
- **Response error:** normalised distance as in C4.
- **Identity accuracy:** equivalence-class accuracy as in C5.
- **Calibration:** per-channel Brier and log loss, raw and calibrated, primary; reliability plots in fixed transition windows; ECE diagnostic only with fixed bins. Calibration split is by whole generator configuration and schedule, never by step or by seed within a configuration. Uncertainty clustered by seed.
- **Costs:** probes used, environment samples, operations, and, where a reward is declared, task regret to detection. Regret is reported only in regimes with a declared reward and default policy.

## H. Baselines (frozen algorithms, one tuning budget each)

Random; temporal correlation (lag set, window, statistic declared); forward-model residual (architecture, optimiser, retraining schedule declared); IBD as published (randomised-action two-sample tests with FDR), reproduced against **numerical anchors** taken from its released code or paper tables on a static-boundary case, not qualitative ordering only. Stage 0B adds the sequential Bayesian change-point detector in three variants (correctly specified model-informed reference; misspecified scalar residual; nonparametric), each with likelihood, prior, update rule and tuning budget frozen in a config file, and a learned self-model with residual monitoring.

## I. Hardware protocol

Step and operation budgets primary. Randomised interleaved condition order. Declared cooldown before timed runs. macOS thermal pressure and observed throughput logged. Wall-clock secondary and labelled.

## J. Deliverables

**Executable-proof rule [v2.1] (G9).** Every section containing an equation or a numeric invariant is accompanied by a short script in `executable-proofs/` that instantiates it with numbers, including the edge cases (h ≤ τ, singular A_b, constant probes, cancelled paths). The red-teaming agent runs the mutant generators against these scripts before any phase gate. Daniel signs off on the script output, not on the prose.


Package `boundary_env` with: declarative SCM (a small data structure, not code paths); generator; oracle package (separate); invariant tests E1 to E5 with mutants; baselines; run ledger with manifests and completion markers; reference metric script; README stating the estimands chosen in section C and the frozen constants (ε, H, ℋ, 𝒜, p, r, w_T, ρ_min, δ_inv).

## K. Hand-derived example (the check Codex asked for)

Setup: K = 2, N_b = 2, N_d = 0, N_w = 1, N_x = 1, C = 5. Latent index: z = [b0, b1, w0, x0]. A_b = diag(0.9, 0.9) (no coupling), B = I, τ = 0. Assign: ch0 ← b0, ch1 ← b1, ch2 ← w0, ch3 ← x0, ch4 ← unassigned (padding). All gains 1, all available. H = 1.

Baseline labels: S^latent = {b0, b1}; S^obs = {0, 1}; R_1(±e_k) = ±e_k (Jacobian I); P as stated.

1. **Sensor swap ch1 ↔ ch2.** Assign becomes ch1 ← w0, ch2 ← b1. S^latent = {b0, b1} unchanged. S^obs = {0, 2}: changed, because exactly one swapped channel was in S^obs. R unchanged. P changed. So the draft's invariant "sensor swap leaves S unchanged" is true for S^latent and false for S^obs. Contract v2 states both.
2. **Sensor swap ch2 ↔ ch3.** Neither channel is controllable. S^obs unchanged, P changed. The typed alarm α^P should fire; α^S should not.
3. **Actuator remap B ← [[0,1],[1,0]].** S^latent, S^obs unchanged; R changes (Jacobian becomes the swap matrix); P unchanged. α^R should fire alone.
4. **Actuator loss, column 1 of B ← 0.** With A_b diagonal, b1 has no action ancestor: S^latent = {b0}, S^obs = {0}, R changed. Now set A_b = [[0.9, 0],[0.3, 0.9]] instead: b1 is reachable through b0, so S^latent is unchanged at H ≥ 2 and R changes. The label depends on coupling and horizon, which is why the oracle computes it from the graph.
5. **Sensor dropout ch0.** S^latent unchanged; S^obs = {1}; R unchanged; P changed. Both α^S and α^P should fire under the observation-coordinate estimand; only α^P under the latent estimand. Paper 1 uses the observation-coordinate estimand, so both.
6. **Exogenous distractor.** With W_u ≠ 0 and G ≠ 0, corr(a_t, x_{t+1}) ≠ 0 observationally. Under do(a_t = a*), a_t no longer depends on u_t, and x_{t+1} = A_x x_t + G u_t + ε is unchanged in distribution. x0 is never in S^latent. This is the E1 structural fact and the E2 invariance test.

Every target, invariant and metric in this contract agrees with the six cases above. The generator is not to be scaffolded until this section has been re-derived by the building agent from the equations in B and C without reference to this section, and the two derivations match.
