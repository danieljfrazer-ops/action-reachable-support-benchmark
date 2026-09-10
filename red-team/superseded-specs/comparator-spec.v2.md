# Passive comparator and probed comparator — normative specification, VERSION 2 (informative until signed)

**Version 2, 7 September 2026.** Supersedes v1 (archived at `review4-claude-opus/comparator-spec.v1.md`). Basis: `stage-0a-contract-v3.7.md` §§0, A0, B, C, F, G, H, H2; `interface-spec-v4.md`; `d10-adjudication.md` D-10.1/2/3/6; `round4-adjudication-and-tally.md`. Ledger estimator ids: **`cusum_linear_delay_aware`** (arm 2, passive) and **`cusum_linear_delay_aware_probed`** (arm 3, D-7a). The v1 one-lag arm is retained under its old ids **`cusum_linear_channel_agnostic` / `cusum_linear_probed`** as a **labelled legacy appendix arm**, never in confirmation (D-10.2). Values marked **[prov]** are provisional until the pilot and frozen before confirmation.

**Identity (contract §H, D-10.2).** One channel-agnostic **delay-aware** linear one-step predictor `o_{t+1} = [o_t, a_t, a_{t−1}, a_{t−2}, 1] β`, every penalised feature standardised on the fit split before the ridge; a per-channel support baseline that is the **H-horizon action loading** `l_c = max_{h∈ℋ}` of the standardised iterated-prediction sensitivity of channel `c` to the action; a support score `q_c(t) = l_c − |√n · mean of standardised innovations over the trailing window|`; a harness-fitted arm-specific isotonic map to `p_c`; a CUSUM on `max_c |r̃|` for the descriptive alarm channel. This document expands that paragraph; it does not extend it.

**Notation.** Standardised innovations are written **r̃**, never `z` (`z_t` is bound to the latent vector by contract §B). `C` = observation channels, `K` = actuators, `ℋ = {1,2,3}`, `τ_max = 2`.

---

## 1. Training population and the delay-aware predictor [N]

**Population.** `n_pred_fit = 20` **[prov]** whole episodes per (environment, regime, confounder, distractor_level, delay) cell from `split_id = calibration`: fault-free, in-distribution, **non-probed**, disjoint by whole episode from the 24/16 calibrator splits of §7 and from every scored episode. 40,000 transitions per cell at `episode_len = 2000`. Delivered through `fit_predictor(transitions)` (interface v4).

**Design.** Feature row for the transition `(prev_obs = o_t, applied_action = a_t, obs = o_{t+1})`:

  **φ_t = [ o_t (C), a_t (K), a_{t−1} (K), a_{t−2} (K), 1 ] ∈ R^{C+3K+1}**

Lag depth is `τ_max = 2`, taken from the contract registry, not from the cell's `τ`: the arm uses the **same** feature layout in every cell and never reads the true delay. Target `Y_t = o_{t+1}`. One shared coefficient matrix `β ∈ R^{(C+3K+1)×C}` — channel-agnostic by construction.

**Lag handling at episode start.** Episode state holds a two-slot action buffer initialised to `0 ∈ R^K` at every boundary: at step index 0 both lag slots are zero, at index 1 the `a_{t−2}` slot is zero. Not an imputation — the generator initialises its delay queue to zeros (`Instance.run`), so a zero fill is the structurally correct pre-episode history. No transition is dropped for it; transitions are never formed across a boundary. The arm detects a boundary from the transition's `t` field (`t = 0`, or `t ≠ t_prev + 1`), since interface v4 has no `reset` call. **T-CMP-lagstart**.

**Standardisation of penalised features (R4-CX-02).** On the fit split, for each of the `C + 3K` non-intercept columns: `m_j = mean(φ_{·,j})`, `s_j = max(sd(φ_{·,j}, ddof=0), s_floor)`, `s_floor = 1e-8`. The standardised design is `X̃ = [(φ − m)/s , 1]`. The intercept column is neither standardised nor penalised. Each penalised column then has `‖x̃_j‖² = n` exactly.

**Ridge.** `β̃ = (X̃ᵀX̃ + λ D)^{-1} X̃ᵀY`, `D = diag(1,…,1,0)`, float64 Cholesky, and

  **λ = λ_rel · (1/(C+3K)) Σ_j ‖x̃_j‖² = λ_rel · n**, with **λ_rel = 1e-4 [prov]** (so at n = 40,000, λ = 4.0).

Because the penalty now acts on columns of equal norm, `λ` and every fitted loading are invariant to rescaling any observation channel or actuator — the defect Codex measured (λ 4.80 → 8038, loadings −21 % to −27 % under a ×100 channel rescale). Test **T-CMP-scale**.

**Back-transform.** Scoring uses raw features, so the coefficients are transformed back once at fit time:
`β_raw[j,:] = β̃[j,:] / s_j` for `j = 1..C+3K`; `b_raw = β̃_intercept − Σ_j (m_j / s_j) β̃[j,:]`. `X̃ β̃ ≡ φ β_raw + b_raw` identically; the back-transform is an exact reparameterisation, not an approximation (asserted to 1e-10 in **T-CMP-backtransform**).

**Innovations.** `R = Y − X̃β̃` on the fit split; `μ_c = mean(R_{·,c})`, `σ_c = max(sd(R_{·,c}, ddof=1), σ_floor)`, `σ_floor = 1e-6`. Online `r̃_{t,c} = clip((r_{t,c} − μ_c)/σ_c, ±z_cap)`, `z_cap = 8` (the IBD arm's bound, so both calibrator domains are identical).

**Probe hygiene.** Any transition in a `fit_predictor` population carrying `probe_flag = True` is dropped **with the following `τ_max = 2`** — a probe at `t` contaminates `b` through `t+1+τ`. The confirmatory population is non-probed, so this is a guard (F5).

**Frozen online.** `β, μ, σ, l, degenerate` are computed once in `fit_predictor` and never updated during scoring: no online refit, no forgetting factor, no recursive least squares. The arm is deliberately a **frozen residual monitor** — the class of method the working claim is about.

## 2. H-horizon action loading [N] (D-10.2; fixes R4-2, R4-3, R4-CX-01)

Write the raw-unit blocks of `β_raw` as `β_o ∈ R^{C×C}` (the `o_t` block) and `β_{a,0}, β_{a,1}, β_{a,2} ∈ R^{K×C}` (the `a_t`, `a_{t−1}`, `a_{t−2}` blocks). Define the **iterated-prediction Jacobian** by rolling the fitted one-step map forward with the intercept and the noise dropped:

  **J^{(0)} = 0 ∈ R^{K×C};  J^{(h)} = J^{(h−1)} β_o + β_{a,h−1},  h = 1, 2, 3.**

`J^{(h)}_{k,c} = ∂ ô_{t+h,c} / ∂ a_{t,k}` under the fitted model. **The iterated model treats actions after the first step as exactly zero**: the impulse `a_t` is carried forward only through the lag slots it legitimately occupies (`a_{t−1}` at the second iterate, `a_{t−2}` at the third), and `a_{t+1} = a_{t+2} = 0`. This mirrors contract C2/C4's `do(a_t = a, later actions 0)`; it is a definition, not an estimate of the closed loop, and no counterfactual claim attaches to it.

  **l_c = max_{h ∈ ℋ} ‖ J^{(h)}_{:,c} ‖₂ / σ_c**,  ℋ = {1,2,3}.

Frozen at `fit_predictor`. Properties, all testable:

- **Downstream channels (R4-2).** A `d` channel has `J^{(1)} = 0` but gains loading at `h = 2` through the fitted `b → d` entries of `β_o`. On `draw_certified({}, 0)`, `τ = 0`, five fit episodes: retained `d` moves from `l = 0.017` (one-lag) to **12.80**.
- **Delay cells (R4-3, R4-CX-01).** At `τ = 2` the action reaches `b` only at `h = 3`, carried by `β_{a,2}`. Same instance: retained body channels move from `0.056 / 0.233` to **7.82 / 6.71**.
- **Scale invariance.** Rescaling channel `c'` by `γ` acts on `β_o` as a similarity transform and scales `σ_c` with the numerator, so `l_c` is unchanged (**T-CMP-scale**).
- **The confounding pathology is preserved, deliberately.** `a_t` is a contemporaneous proxy for `u_t`, which drives `x_{t+1}`, so confounded distractors keep `l ≈ 6.5–7.5` on the same instance. v2 makes the arm competent where competence is possible and leaves the shared-cause failure where the benchmark measures it.

**Informative diagnostic, scope stated.** On `draw_certified({"G_scale":0}, 0)`, `l` alone ranks `S^obs,ε` at **AUC 1.00** at both `τ = 0` and `τ = 2`, against 0.746 / 0.932 for v1's one-lag loading. This is **pre-event, loading-only, one instance** — not the D-10.3 competence floor (a scored, interval-bounded, per-cell quantity). Evidence the floor is attainable; not the floor.

## 3. Per-channel support score [N]

For every channel `c` and every environment step, with `n = min(W, t_ep)`, `W = 500`, `t_ep` the episode step index:

  **q_c(t) = l_c − | √n · (1/n) Σ_{i=t−n+1}^{t} r̃_{i,c} |**, then **q_c ← clip(q_c, −q_cap, +q_cap)**, `q_cap = 40` **[prov]**.

- **Orientation: higher = retained support.** Both terms point the same way. A channel the actions still drive has a large loading and a null-centred innovation mean; a channel whose drive was removed keeps its stale loading and acquires a mean shift that subtracts from it.
- **Why the baseline term is required (D9-codex-6).** The shift term alone is a *change* score: large for any channel whose dynamics moved, supported or not, and ≈ 0 on a fault-free control, so it cannot rank channels at all there. Membership in `S^obs,ε` is a statement about action reachability, and only `l_c` carries it.
- **Window.** Trailing, right-closed, `[t−n+1, t]`, per episode, never reset mid-episode.
- **Warm-up.** For `t_ep < n_warm = 30` **[prov]** the shift term is 0, so `q_c = l_c`. Neither warm-up nor the `min` binds at the scored offsets (`t ≥ 1200`).
- **Cadence.** Recomputed **every environment step**; a probe step is an environment step. `update` returns `raw_support = q` (the vector the evaluator computes the primary AUC on) and `p = g(q)`. `persistence_unit = "steps"`; no epoch quantisation.

## 4. Degenerate channels [N] (fixes R4-CX-04)

Contract §H2 is explicit: `ε^o` is added to **every** channel including unavailable and padding channels, so **there are no hard-silent channels** and v1's zero-variance test (`sd < 1e-3`) can never fire on a generator instance. Degeneracy is redefined jointly on **action loading and innovation scale**, both relative and therefore unit-free. Channel `c` is **degenerate** iff

  **σ_c < σ_deg_rel · median_{c'}(σ_{c'})**  **and**  **l_c < l_deg**,  `σ_deg_rel = 1e-2` **[prov]**, `l_deg = 1e-3` **[prov]**.

- Determined **once, at `fit_predictor`**, from the fault-free fit split. Never re-evaluated online, so a mid-episode dropout is a live channel whose innovation mean shifts and whose `q` falls — which is the behaviour the benchmark wants — not a channel that silently leaves the scoring set.
- A degenerate channel gets **`q_c ≡ q_absent = −(q_cap + 1) = −41` at every step**, strictly below any live value (live `q` is clipped to `[−q_cap, +q_cap]`). This makes `q_absent` a genuinely separate isotonic knot; v1's collision of "dead" with "clipped live" is R4-22, adopted here.
- Degenerate channels are **excluded from `𝒞*`**, the set over which the alarm maximum is taken. Without the exclusion a channel with `σ_c` at the floor would produce an unbounded `r̃` and a permanent alarm.
- **Padding channels are not degenerate.** On `draw_certified({}, 0)` pads have `σ ≈ 0.049` against a median `σ ≈ 0.12` (ratio 0.4, far above 1e-2) and `l ≈ 0.09–0.22`. They are ordinary negatives, scored as such, and stay in `𝒞*`. **[Opinion]** on the reference generator the degeneracy rule should never fire; it is a numerical guard for hand-built fixtures and for morphology events, and if the pilot shows it firing on a generator instance that is a defect to investigate, not a result.

## 5. Alarm channel [N]

- **Recursion.** `S_0 = 0`; `m_t = max_{c ∈ 𝒞*} |r̃_{t,c}|`; `S_t = max(0, S_{t−1} + m_t − k)`. `S ← 0` at every episode boundary (D-6b: the calibrated quantity is the fresh-start run length).
- **Reference value.** `fit_alarm_reference(transitions)` consumes the **arm-specific** fault-free stream (non-probed for arm 2, probed for arm 3) and sets `ā = mean(m)`, `v = sd(m, ddof=1)`, **`k = ā + 0.5 · v`** **[prov]**. It may change **only** `(ā, v, k)`; `β, μ, σ, l, degenerate` are asserted bitwise unchanged across the call (**T-CMP-lifecycle**). This is the two-call split that removes v1's contradictory single `calibrate` (R4-CX-05).
- **Outputs.** `stat = S_t` **every step**; **`raise = 1 iff S_t > h`, no persistence applied**. `statistic_is_monotone_in_alarm = True`. Persistence `p = 3` and refractory `r = 20` belong to the harness (`contract_ref.count_alarms`), contract §G.
- **Threshold.** `h` arrives via `set_threshold(h)` from the harness's ARL_0 calibration under the D-2a rule (per environment, regime, confounder, distractor_level, delay, estimator; ≥ 400 fresh-start run lengths; 95 % interval for the mean inside [900, 1100]; cap 2e6 steps). `h` is not transferable across cells or arms.
- **Scope.** Contract §G (R3-8): ARL-band attainment governs the **descriptive alarm outcomes only**. P1 (AUC on raw `q`) and P2 are computed on all pairs regardless of band.

## 6. Probed variant, D-7a [N]

- **Stream.** Arm 3 runs on episodes carrying the **exact probe injections used by `seq_ibd`** — same balanced pre-randomised (actuator, sign) blocks of length `2K` (contract §0, D-10.4), same seed, same eligibility mask, same replaced-action semantics. The two arms are matched transition-for-transition; only the estimator differs.
- **Predictor.** **Bitwise identical `β, μ, σ, l, degenerate`** to arm 2, from the same non-probed fault-free population of §1. The score function is literally identical across arms 2 and 3, so the arm-3 − arm-2 difference isolates the effect of probes on the *stream*, not on the *fit*. **T-CMP-identity**.
- **Re-derived per arm:** `(ā, v, k)` via `fit_alarm_reference` on the **probed** fault-free stream; `h`; the isotonic map `g`; the operating point `θ*`. Probe injections replace the applied action with a ±unit vector, which changes the innovation distribution through clipping, delay and (family N) saturation; sharing `h` would confound "probes help" with "probes are out of the null" (F5(d)).
- **Probe transitions in the fit:** excluded with their two successors (§1). **In scoring:** included, unmarked, no gap, no down-weighting, no window reset — a probe step is an ordinary environment step whose action happened to be a unit vector.
- **Budget.** `request_probe(steps) → None` for both arms; the harness injects. Arm 3 is nonetheless **charged the full `probe_budget = 0.05`** and task regret where a reward exists, so the cost comparison against `seq_ibd` is honest.
- **Sign blindness is a formula-level constraint (R4-CX-10, R4-16).** Declared `sign_blindness = formula`. Arm 3 *does* see the probe sign — the sign **is** the applied action, a legitimate feature — and withholding it is impossible. The constraint is on the frozen statistic: **`q` and `S` are functions of `(r̃, l)` only, `l` is fitted offline on a non-probed split, and neither conditions on `probe_flag` nor on any randomisation-stratified grouping of the action.** Enforced by (i) the spec digest and source hash in the ledger row; (ii) **T-CMP-marker** — permuting `probe_flag` leaves `(raw_support, p, stat, raise)` bitwise identical, which proves *marker* blindness only and is no longer claimed to prove more; (iii) **T-CMP-sign-metamorphic** — insert unit actions `±e_k` at scheduled steps of a fault-free stream **with `probe_flag = False`** and assert (a) outputs bitwise identical to the same stream with those steps flagged `True`, and (b) negating every inserted sign leaves `l` bitwise unchanged and the window innovation-mean term unchanged in distribution (paired two-sided test, declared tolerance, `n ≥ 400` windows). Together: the output depends on the action only through its numeric value in `φ_t`, never through its provenance or sign group.
- **What this arm is for.** It separates *having* interventions from *using them causally*. Round-4 reproductions put arm 3 within 0.01 AUC of arm 2 across four configurations; v2 is frozen with that expectation stated in advance.

## 7. Calibration tier [N] (secondary, contract §G tier 2)

- **Splits.** Per cell and **per arm**: 24 episodes to fit the calibrator, 16 disjoint episodes to choose the operating point, each half event-carrying (12/12, 8/8), all disjoint from the 20 predictor-fit episodes and from every scored episode. Both artefacts frozen before scoring.
- **Who fits it — normative, not opinion (R4-17).** `g` needs oracle labels `1[c ∈ S^obs,ε]`, and contract E5 puts the oracle in a process the estimator may never import. **So the harness fits `g` and `θ*` and injects them through `configure(bundle.calibrator_params)`** (interface v4), hashed and logged; the estimator fits no calibrator (`fit_predictor` → `β, μ, σ, l, degenerate`; `fit_alarm_reference` → `ā, v, k`). v1 marked this `[Opinion]`; interface v4 made it the only legal channel, so it is now normative.
- **Fit.** Non-decreasing PAVA on `(q_c(t), label_c(t))` pooled over eligible steps and channels of the 24 fit episodes, with **exact-tie aggregation** (identical `q` values form one weighted block). Degenerate channels contribute at `q_absent`, a real knot.
- **Apply.** Right-continuous step `g(q) = v[searchsorted(knots, q, "right") − 1]`, index clamped, output clipped to `[0,1]`. No interpolation, no smoothing.
- **Operating point.** `θ*` = the **largest** tied maximiser of micro-F1 on the **16-episode validation split only**, never on the fit split (D9-codex-7). Frozen; reported F1 is at `θ*`.
- **Scoring.** Leave-one-instance-out with held-out event times; cross-fitted Brier and log loss of calibrated `p_c`; no "uncalibrated proper score" (D9-codex-8).
- **The primary is untouched.** AUC on raw `q` is invariant to any monotone `g`, so it uses no supervised data.

## 8. Information set and timing [N]

- **Arm 2:** `"channels=all_observed(C); applied_action=visible; action_lags=own_buffer(2); t=visible; probe_flag=delivered_not_consumed; reward=not_visible; terminated_truncated=not_visible; oracle=never; P=(Assign,gain,avail)=never; true_delay_tau=never; regime_bundle={hash only, params unused}; calibration_split=used(predictor fit + alarm reference; harness-fitted isotonic + operating point injected via configure); probes_requested=none"`.
- **Arm 3:** identical, plus `"probe_stream=externally_injected_identical_to_seq_ibd(blocks,seed); probe_flag=delivered_not_consumed; probe_signs=visible_as_action_not_stratified; sign_blindness=formula; probe_budget_charged=0.05"`.
- **Never seen:** oracle labels, `S^latent`, `S^obs,ε`, `e_j`, `R`, `M`, `P`, event types, event times, reward, termination flags, the cell's true `τ`, the other arm's state.
- **Timing.** At an episode boundary the arm clears `S`, the `r̃` ring, the running window sum, the action lag buffer and the step counter; `β, μ, σ, l, degenerate, ā, v, k, g, θ*, h` survive (arm state, not episode state). Outputs are emitted on every transition from the first; while `t_ep < n_warm`, `raw_support = l`, `p = g(l)`. Nothing is emitted before the first transition.

## 9. Costs [N]

Probe steps 0 for arm 2; 0 requested and `probe_budget = 0.05` charged for arm 3. Per step: one dense mat-vec `φ_t β_raw` at `C·(C+3K+1)` multiply-adds plus O(C) for standardisation, ring, running sum, score and max — ≈ 7.4·10² at `C = 24` and ≈ 1.4·10⁴ at `C = 114`, the same order as the IBD arm's amortised ≈ 1.3·10⁴, which keeps the cost comparison fair. The `J^{(h)}` recursion is `|ℋ|` `C×C` mat-mats **once, at fit time**, never online. Memory ≈ 0.13 MB at `C = 24` and ≈ 0.6 MB at `C = 114` (`β` ≈ 108 kB, the `W = 500` ring ≈ 456 kB, plus O(C) frozen vectors and the isotonic knots). No growth in `t`.

## 10. Parameters [N]

No parameter may change after the pilot without re-running ARL_0 calibration, the isotonic fit and the black-box acceptance suite (contract E6). There is no outcome-dependent tuning clause.

| # | Symbol | Value | Status | One-line justification |
|---|---|---|---|---|
| 1 | ε, H, ℋ, a_max, τ_max | 0.05, 3, {1,2,3}, 2.0, 2 | contract §0 | Normative; ℋ and τ_max fix the feature depth and the loading horizons. |
| 2 | p, r, H_det, ARL_0 | 3, 20, 200, 1000 | contract §0 | Normative; p and r applied by the harness, never by the arm. |
| 3 | episode_len, event_t, offsets_rank | 2000, 1000, {200,500,1000}, primary 500 | contract §0 | Normative; fixes `W` below. |
| 4 | cal_split, probe_budget | 24/16, 0.05 | contract §0 | Normative; arm 3 is charged the budget it does not request. |
| 5 | feature layout | `[o_t (C), a_t, a_{t−1}, a_{t−2}, 1]` | frozen | Contract §H, D-10.2; depth = `τ_max`, identical in every cell, so the arm never reads `τ`. |
| 6 | lag fill at episode start | zeros | frozen | The generator's delay queue starts at zero, so this is exact, not imputed. |
| 7 | feature standardisation | mean-centred, `sd(ddof=0)`, penalised columns only | frozen | Makes the ridge and every loading invariant to channel and actuator units (R4-CX-02). |
| 8 | λ_rel | 1e-4 **[prov]** (⇒ λ = 1e-4·n) | frozen | Conditioning guard on equal-norm columns; λ = 4.0 at n = 40,000. |
| 9 | intercept | present, unstandardised, unpenalised | frozen | Penalising it would bias `μ_c` away from 0. |
| 10 | s_floor | 1e-8 | frozen | Guards a constant feature column; never reached by a live feature. |
| 11 | n_pred_fit | 20 episodes **[prov]** | frozen | 40,000 transitions ≫ `C + 3K + 1 = 121` even at `C = 114`. |
| 12 | probe-drop guard | probe transition + next `τ_max` | frozen | A probe at `t` contaminates `b` through `t+1+τ`. |
| 13 | iterated-action convention | actions after the first step = **0** | frozen | Mirrors contract C2/C4 `do(a_t=a, later actions 0)`; makes `J^{(h)}` a definition, not an estimate. |
| 14 | loading aggregation | ℓ2 over `k`, then `max` over `h ∈ ℋ` | frozen | Matches C2's max-over-horizon operational effect; no new registry constant. |
| 15 | σ_floor | 1e-6 | frozen | Numerical guard; never reached by a live channel. |
| 16 | z_cap | 8 | frozen | Same bound as the IBD arm, so both calibrator domains are bounded identically. |
| 17 | W | 500 | frozen | Exactly 100 % post-event at the primary offset 500 (same choice as the IBD arm). |
| 18 | n_warm | 30 **[prov]** | frozen | Below it `√n·mean` is a single noisy draw; never binds at scored offsets. |
| 19 | q_cap, q_absent | 40 **[prov]**, −41 | frozen | Bounds the isotonic domain; `q_absent` is strictly below every live value, so dead ≠ clipped (R4-22). |
| 20 | σ_deg_rel, l_deg | 1e-2 **[prov]**, 1e-3 **[prov]** | frozen | Degeneracy is joint and relative, because `ε^o` makes no channel silent (R4-CX-04, contract §H2). |
| 21 | degeneracy timing | fit-time only, never online | frozen | A mid-episode dropout must move `q`, not leave the scoring set. |
| 22 | CUSUM k multiplier | 0.5 **[prov]** | frozen | `k = ā + 0.5 v` on `max_c|r̃|`; the only free constant in the recursion. |
| 23 | isotonic rule | PAVA non-decreasing, exact-tie blocks, right-continuous step, clamp-extrapolate, clip [0,1] | frozen | Deterministic and monotone; leaves the primary AUC untouched. |
| 24 | operating-point rule | largest tied micro-F1 maximiser on the 16-episode validation split | frozen | Separates knot fitting from threshold choice (D9-codex-7). |
| 25 | persistence_unit | `"steps"` | frozen | The arm updates every step; no epoch quantisation. |
| 26 | **h** | set by harness, per arm and per cell | **calibrated** | The single scalar knob; fresh-start ARL_0 = 1000 under D-2a. |

**Honest count: 26 rows = 4 contract blocks carrying 14 inherited constants + 21 frozen arm parameters + 1 calibrated (`h`). Zero swept parameters in the confirmatory configuration.** Fitted objects: `β (C+3K+1 × C)`, `μ[C]`, `σ[C]`, `l[C]`, `degenerate[C]`, `(ā, v, k)`, and the harness-supplied `g`, `θ*`. The probed arm introduces **no new parameter names**; it re-values `ā, v, k, h, g, θ*` only. Seven values are provisional (`λ_rel, n_pred_fit, n_warm, q_cap, σ_deg_rel, l_deg, k`-multiplier) and must be frozen before confirmation. `W ∈ {250, 1000}` is an appendix sensitivity with its own re-calibrated `h`, never substituted for the confirmatory arm. v2 adds **five** frozen parameters over v1 (rows 6, 7, 10, 13, 14) and **retires** v1's `σ_deg`; the capacity increase is in the feature layout and the loading definition, both mandated by D-10.2, not in tuning surface.

## 11. Executable fixtures [N]

Deterministic tests in `executable-proofs/gate/test_comparator.py`, mapped in `coverage-matrix.md`. **F1–F4 and F6–F8 are pinned to a named `reference_generator` configuration and seed** and assert an ordering on *that* instance. This is the R4-7 fix: v1 stated population properties as gate assertions (its F1 "AUC below 0.5" held on 0 % of instances in one configuration and 82 % in another), and now that D-10.1 has frozen the generator as code, determinism comes from the pinned draw. Population statements move to §13 and to reported quantities with intervals.

- **F1 — confounded false support (T-CMP-conf).** `draw_certified({}, 0)`, fault-free. Assert `l` on each confounded distractor exceeds `l` on at least one channel of `S^obs,ε`, and that the episode `q`-AUC at offset 500 on this pinned instance falls in a stated interval.
- **F2 — actuator-loss true positive (T-CMP-loss).** Pinned instance with `s_change_certified`; `apply_event(("actuator_loss", 0))` at `t = 1000`. Assert `q` falls on channels leaving `S^obs,ε`, is flat on channels remaining, and the CUSUM raises within `H_det` at the calibrated `h`.
- **F3 — padding and dropout under additive noise (T-CMP-pad).** The generator's four `assign = −1` pads are **noise-only negatives**, not silent (contract §H2). Assert each pad is **non-degenerate** (`σ ≈ 0.049` vs median `≈ 0.12`, `l ≈ 0.09–0.22`), is scored as an ordinary negative, and stays in `𝒞*`. Dropout is tested **separately** as an availability change: after `sensor_dropout` on a supported channel, assert it is *not* reclassified degenerate and its `q` falls. No hard-silent case exists and none is asserted.
- **F4 — copies, equality in distribution (T-CMP-copy).** Two `Assign` rows on one latent with equal gain. `ε^o` is keyed per channel, so the traces are **not** identical and v1's `|q₁−q₂| < 1e-6` is unsatisfiable. Assert instead `|mean(q₁−q₂)|` below a declared powered tolerance over ≥ 20,000 paired steps, a two-sample distributional test above a declared level, and a finite ridge solve (the fixture that justifies λ). Confirmatory instances have no copies (D-10.6).
- **F5 — probe-shock null (T-CMP-probe-null).** Fault-free stream carrying the `seq_ibd` probe blocks. Assert (a) probe transitions and their `τ_max` successors are dropped from any `fit_predictor` population containing them; (b) `β, μ, σ, l, degenerate` bitwise identical to arm 2; (c) `k` and `h` differ between arms on family N or `τ = 2`; (d) the probed arm's fresh-start ARL under `h_passive` lies **outside** [900, 1100] — the evidence that separate calibration is necessary, not tidy.
- **F6 — delay competence (T-CMP-delay).** `draw_certified({"tau": 2}, 0)`: `l` on each retained body channel exceeds 1.0 while the one-lag loading is below 0.3. Regression guard for R4-3 / R4-CX-01.
- **F7 — unit invariance (T-CMP-scale).** Multiply one channel's `gain` by 100 and refit: `λ`, the whole `l` vector and the `q` ranking unchanged to 1e-8. Strictly stronger than v1's single-scale `‖β_λ − β_OLS‖_∞ < 1e-6` (**T-CMP-ridge**, retained).
- **F8 — downstream competence (T-CMP-downstream).** `draw_certified({}, 0)`: every `d` channel in `S^obs,ε` has `l` above every pad's `l` by a stated margin, and its one-lag loading does not. Regression guard for R4-2.
- Plus **T-CMP-lagstart**, **T-CMP-backtransform** (§1), **T-CMP-lifecycle** (§5), **T-CMP-identity**, **T-CMP-marker**, **T-CMP-sign-metamorphic** (§6).

## 12. Pseudo-code [N]

```python
# frozen by fit_predictor: beta_raw, b_raw, mu[C], sd[C], l[C], degen[C]; by fit_alarm_reference: k
# installed by configure(): g, theta*; by set_threshold(): h
# consts: LAM_REL=1e-4, W=500, Z_CAP=8, Q_CAP=40, Q_ABSENT=-41, N_WARM=30,
#         SIG_FLOOR=1e-6, S_FLOOR=1e-8, SIG_DEG_REL=1e-2, L_DEG=1e-3, KMULT=0.5, TAU_MAX=2, HORIZONS=(1,2,3)

def fit_predictor(transitions):                       # arms 2 and 3 receive the SAME non-probed fault-free split
    tr   = drop_probe_and_successors(transitions, TAU_MAX)        # guard; no-op on the confirmatory split
    phi  = rows([o_t, a_t, a_{t-1}, a_{t-2}, 1]) within episodes, lags zero-filled at episode start
    Y    = rows(o_{t+1});  n = len(Y)
    m, s = phi[:, :-1].mean(0), maximum(phi[:, :-1].std(0, ddof=0), S_FLOOR)
    Xt   = hstack([(phi[:, :-1] - m) / s, ones(n, 1)])            # penalised cols now have ||x||^2 == n
    D    = diag([1]*(C+3*K) + [0]);  lam = LAM_REL * n
    Bt   = cho_solve(Xt.T @ Xt + lam * D, Xt.T @ Y)               # intercept unpenalised
    beta_raw, b_raw = Bt[:-1] / s[:, None], Bt[-1] - (m / s) @ Bt[:-1]
    R    = Y - Xt @ Bt
    mu, sd = R.mean(0), maximum(R.std(0, ddof=1), SIG_FLOOR)
    bo, ba = beta_raw[:C], [beta_raw[C+j*K : C+(j+1)*K] for j in (0, 1, 2)]
    J, l = zeros(K, C), zeros(C)
    for h in HORIZONS:                                            # iterated prediction, later actions == 0
        J = J @ bo + ba[h-1];  l = maximum(l, norm(J, axis=0) / sd)
    degen = (sd < SIG_DEG_REL * median(sd)) & (l < L_DEG)         # joint, relative, fit-time only

def fit_alarm_reference(transitions):                 # arm 2: non-probed stream; arm 3: PROBED stream
    m_stream = [max(abs(rtilde(tr))[~degen]) for tr in transitions]      # may change (abar, v, k) ONLY
    abar, v = mean(m_stream), std(m_stream, ddof=1);  k = abar + KMULT * v

def new_episode():  S, ring, n, t_ep, lag = 0.0, empty_ring(W, C), 0, 0, [zeros(K), zeros(K)]

def update(tr):                                       # every environment step; probe steps included, unmarked
    if tr.t == 0 or tr.t != t_prev + 1: new_episode()
    t_ep += 1
    r   = tr.obs - (concat([tr.prev_obs, tr.applied_action, lag[0], lag[1]]) @ beta_raw + b_raw)
    lag = [tr.applied_action, lag[0]]
    rt  = clip((r - mu) / sd, -Z_CAP, Z_CAP);  ring.push(rt);  n = min(W, t_ep)
    shift = 0.0 if t_ep < N_WARM else abs(sqrt(n) * ring.mean_last(n))   # vector over C
    q   = clip(l - shift, -Q_CAP, Q_CAP);  q[degen] = Q_ABSENT
    S   = max(0.0, S + max(abs(rt)[~degen]) - k)                        # CUSUM on max_c |r~| over C*
    return (q, g(q), S, 1 if S > h else 0)                              # harness owns persistence p and refractory r
```

## 13. Claims we do not make [N]

An **engineering baseline**: the strongest passive reading we could find at the capacity the contract permits, frozen on principle so the confirmatory margin is decided by the science and not by the baseline's specification (round 4 showed the choice moves the margin by ≈ 0.2 AUC — enough to flip the D-9.3 verdict three ways across three implementations). We do **not** claim it is the strongest possible passive comparator, the best linear residual monitor, or optimal in any sense. No identifiability, consistency, FDR-control or ARL-optimality claim: the ARL_0 is *calibrated*, not derived, and the innovations are neither independent nor Gaussian under the closed-loop policy. `J^{(h)}` is a sensitivity of the fitted predictor, **not** an estimate of the causal Jacobian `M` (C4) and not a counterfactual; that it recovers reachable structure on family L is an empirical convenience, not an identification result. `q` does not estimate `e_j`, `R`, `M` or body membership (C6) — only a ranking against `S^obs,ε`. Arm 3's showing would not prove probes useless: it is evidence that *this* statistic cannot use them, which is what a mechanism control is. We do **not** claim above-chance ranking under confounding — §2 says in advance that confounded distractors keep a large loading, reported as a result, not repaired. We do **not** claim v2 clears the D-10.3 competence floor: §2's `AUC = 1.00` is loading-only on one instance, and the floor is a scored per-cell interval that **round 5 must execute** before any δ is touched. We do **not** carry v1's numbers forward: they were measured on a different feature layout and three unfrozen generators, and are superseded. Finally, we disclose that this specification and the primary metric were frozen **after** pilot simulations had shown the interventional arm clears them (contract §G Disclosure); confirmation uses fresh seeds and instance draws.

## 14. Disposition of round-4 findings [N]

| Finding | Claim against v1 | Disposition in v2 | Where |
|---|---|---|---|
| **R4-CX-01** (high) | forcing the action feature to `a_t` when the plant uses `a_{t−τ}` is misspecification, not a robustness cell; supplying `a_{t−2}` raises the arm to 0.997 and erases the benefit | **Accepted in full.** Feature row `[o_t, a_t, a_{t−1}, a_{t−2}, 1]` at fixed depth `τ_max`, identical in every cell so no delay knowledge is used. Reproduced: retained body `l` 0.056/0.233 → 7.82/6.71 at `τ = 2`. The v1 `τ = 2` robustness result is withdrawn. | §1, §2, F6, params 5/13 |
| **R4-CX-02** (high) | trace-scaled ridge is not unit-invariant; a ×100 channel rescale moved λ 4.80 → 8038 and the loadings 21–27 % | **Accepted in full.** Penalised features standardised on the fit split (equal column norms), λ = `λ_rel·n`, coefficients transformed back exactly; an invariance fixture on `l` and the `q` ranking replaces the single-scale `β_λ ≈ β_OLS` check. | §1, F7, params 7/8 |
| **R4-CX-04** (high) | F3's hard-silent pad and F4's `\|q₁−q₂\| < 1e-6` are impossible under additive `ε^o` (pad residual sd 0.04997; copy median `\|q₁−q₂\|` 0.346) | **Accepted in full.** Degeneracy redefined jointly on **relative innovation scale and loading**; pads are noise-only negatives that stay in `𝒞*`; dropout tested as an availability change; copies tested as equality in distribution. | §4, F3, F4, params 20/21 |
| **R4-CX-05** (high) | two incompatible calibration lifecycles inside one `calibrate` | **Accepted in full.** `fit_predictor` (non-probed; sets `β, μ, σ, l, degen`) and `fit_alarm_reference` (arm-specific; may set **only** `ā, v, k`) per interface v4; field-level invariant asserted by T-CMP-lifecycle. | §1, §5, §6 |
| **R4-CX-10** (medium) | flag permutation proves marker blindness only; formula blindness is the defensible control | **Accepted in full.** `sign_blindness = formula`; the claim is restated as "no randomisation-stratified statistic", enforced by source/spec hash plus a metamorphic fixture over **non-probe** unit actions; T-CMP-marker retained with its claim narrowed. | §6, F-suite |
| **R4-2** (high) | `l_c ≈ 0` on downstream `d` channels, which C6 requires as positives; concedes 0.09–0.14 AUC | **Accepted in full**, via the reviewer's own fix generalised to iterated prediction (no new registry constant; `H`, `ℋ` already frozen). Reproduced: retained `d` channel `l` 0.017 → 12.80. | §2, F8, params 13/14 |
| **R4-3** (high) | one-lag predictor is vacuous at `τ = 2`; §H's "correct only on family L" was false there; 900/2700 confirmatory rows are delay cells | **Accepted in full**; same fix as R4-CX-01. v1 §8 row 5 ("adding lags would make it a different arm") is deleted; the one-lag arm becomes a labelled legacy appendix arm (D-10.2). | §1, §2, F6, header |
| **R4-7** (high) | F1/F2 assert population properties as deterministic gates; F1's "AUC < 0.5" held on 0 %–82 % of draws by configuration | **Accepted.** Instance fixtures are pinned to a named generator configuration and seed; population statements move to §13 and to reported quantities with intervals. **Deviation from the exact remedy:** the pinning is a frozen generator draw, not a hand-written matrix — stronger, and unavailable when the finding was written. | §11, F1, F2 |
| **R4-16** (medium) | T-CMP-probe-blind cannot detect the leak §6 names; sign blindness is not enforceable | **Accepted**, converging with R4-CX-10; the reviewer's own test (replay with every probe sign negated, window-mean term unchanged in distribution) is clause (b) of T-CMP-sign-metamorphic. | §6 |
| **R4-17** (medium) | the harness must own the isotonic fit (forced by E5); interface v3 had no legal channel to inject it | **Accepted in full.** Interface v4's `configure(bundle.calibrator_params)` is that channel; v1's `[Opinion]` note is promoted to normative text. | §7 |
| **R4-22** (low) | `q_absent = −q_cap` collides with a clipped live channel in the isotonic domain and the ranking | **Accepted in full.** Live `q` clipped to `[−q_cap, +q_cap]`; `q_absent = −41`, strictly below every live value, so it is a genuine separate knot. | §4, param 19 |

**References.** `stage-0a-contract-v3.7.md`; `interface-spec-v4.md`; `d10-adjudication.md`; `round4-adjudication-and-tally.md`; `review4-codex/findings.md`; `review4-claude-opus/findings.md` and `adjudication.md`; `d9-adjudication.md`; `executable-proofs/gate/reference_generator.py` and `contract_ref.py`; `sequential-ibd-spec.md`; `confirmation-design.csv`. Page (1954), CUSUM. Barlow, Bartholomew, Bremner & Brunk (1972), isotonic regression / PAVA. Hoerl & Kennard (1970), ridge regression.
