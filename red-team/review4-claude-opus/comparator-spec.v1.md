# Passive comparator and probed comparator — normative specification (DRAFT 1, informative until signed)

Basis: `stage-0a-contract-v3.5.md` §§0, B, C, F, G, H, H2; `interface-spec-v3.md`; `d9-adjudication.md` D-9.4/D-9.5; `review-d9-codex/findings.md` §"Scope, statistic, comparator, and scoring definitions" + D9-codex-6/7; `review-d9-gemini/findings.md` §3.3 (D9-GM-4). Ledger estimator ids: **`cusum_linear_channel_agnostic`** (arm 2, passive) and **`cusum_linear_probed`** (arm 3, D-7a). Values marked **[prov]** are provisional until the pilot and frozen before confirmation; all others are inherited from the contract or fixed here.

**Identity (unchanged from contract §H).** One channel-agnostic linear one-step predictor fitted by penalised least squares on fault-free in-distribution calibration data; a per-channel support score that is the standardised action loading minus the two-sided standardised innovation-mean shift over a trailing window; an arm-specific frozen isotonic map to p_c; a CUSUM on the cross-channel maximum standardised innovation for the descriptive alarm channel. This document expands that paragraph; it does not change it.

**Notation.** The contract already binds `z_t = [b; d; w; x]` to the latent vector, so standardised innovations are written **r̃**, never z. Contract §H's phrase "CUSUM on max_c |z|" means max_c |r̃_{t,c}| here.

---

## 1. Training population and the linear predictor [N]

- **Population.** `n_pred_fit = 20` **[prov]** whole episodes per (environment, regime, confounder, distractor_level, delay) cell, drawn from `split_id = calibration`, all **fault-free** (no change event), **in-distribution** (the cell's declared regime, R0 or R1), **non-probed**, and **disjoint by whole episode** from the 24 fit / 16 validation calibrator splits of §5. At `episode_len = 2000` this is 40,000 transitions per cell.
- **Design.** Feature row for transition t is `X_t = [o_t (C), a_t (K), 1]`, dimension `C + K + 1`. **Exactly one lag**; no o_{t−1}, no interactions, no basis expansion. Target `Y_t = o_{t+1}` (C). One shared coefficient matrix `β ∈ R^{(C+K+1)×C}` — channel-agnostic by construction.
- **Estimator.** Penalised least squares on the normal equations, float64 Cholesky: `β = (XᵀX + λ·D)^{-1} XᵀY`, with `D = diag(1,…,1,0)` (the **intercept column is never penalised**) and `λ = λ_rel · trace(XᵀX)/(C+K)`, `λ_rel = 1e-4` **[prov]**. λ is a **conditioning guard**, not a modelling choice: silent or perfectly copied channels make XᵀX singular. T-CMP-ridge asserts ‖β_λ − β_OLS‖_∞ < 1e-6 on a well-conditioned fixture, so the contract's "least squares" reading is preserved.
- **Intercept.** Present, unpenalised, fitted. No centering of features; observations are used in raw units.
- **Standardisation.** None on features. Innovations only: on the training population, `r_{t,c} = o_{t+1,c} − (X_t β)_c`, then `μ_c = mean(r_{·,c})`, `σ_c = max(sd(r_{·,c}, ddof=1), σ_floor)`, `σ_floor = 1e-6`. Online: `r̃_{t,c} = clip((r_{t,c} − μ_c)/σ_c, −z_cap, +z_cap)`, `z_cap = 8` (same cap as the IBD arm, so both arms present the same bounded domain to their calibrators).
- **Zero-scale floors and degenerate channels.** A channel with training `sd(r_{·,c}) < σ_deg = 1e-3` **[prov]** is declared **degenerate** (dropped sensor, constant pad). Degenerate channels: are excluded from the set 𝒞\* over which the CUSUM maximum is taken; receive `q_c ≡ q_absent = −q_cap` at every step; and are never rescued online. Rationale: without this, the floor turns a zero-variance channel into an unbounded r̃ and a permanent alarm.
- **Padding and copies.** No special-casing beyond the degeneracy rule. A padding channel that carries observation noise (`ε^o` only, per §B) is a legitimate non-degenerate negative and is scored as one. Copies are separate columns in X and Y; the arm is expected to emit near-identical q for them, and the harness — not the arm — collapses them into equivalence classes for the grouped-AUPRC sensitivity (§C5, §G).
- **Boundaries and probe hygiene.** Transitions are never formed across an episode boundary. If any transition in the training population carries `probe_flag = True`, that transition **and the following `τ_max = 2` transitions** are dropped, because a probe action at t contaminates b through t+1+τ. The confirmatory training population is non-probed, so this rule is a guard, exercised only by fixture F5.
- **Frozen online.** `β, μ, σ, l, k` are computed once inside `calibrate()` and **never updated during scoring**. There is no online refit, no forgetting factor, no recursive least squares. This is deliberate: the comparator is a frozen residual monitor, which is the class of method the working claim is about.

## 2. Per-channel support score [N]

- **Baseline support term.** `l_c = ‖β_{a,c}‖_2 / σ_c`, where `β_{a,c} ∈ R^K` is the block of β mapping `a_t` to `o_{t+1,c}` — the standardised action loading. Time-invariant, frozen at calibrate.
- **Score.** For every channel c and every step t, with `n = min(W, t)`, `W = 500`:

  **q_c(t) = l_c − | √n · (1/n) Σ_{i=t−n+1}^{t} r̃_{i,c} |**, then `q_c(t) ← clip(q_c(t), −q_cap, +q_cap)`, `q_cap = 40` **[prov]**.

- **Orientation.** Higher q means **retained support**. Both terms point the same way: a channel the actions still drive has a large loading and a null-centred innovation mean; a channel whose drive was removed keeps its (stale) loading but acquires a mean shift that subtracts from it.
- **Why the baseline term is required (D9-codex-6).** The second term alone is a **change** score: it is large for any channel whose dynamics moved, supported or not, and it is identically ~0 in a fault-free episode, so it cannot rank channels at all on the no-event control. Membership in S^obs,ε is a statement about action reachability, which only `l_c` carries. A comparator without `l_c` is a strawman and was rejected on that ground.
- **Window and warm-up.** Trailing, right-closed, endpoints `[t−n+1, t]`. For `t < n_warm = 30` **[prov]** the shift term is set to 0, so `q_c = l_c`. At the contract's scored offsets (t ≥ 1200) neither warm-up nor the `min` binds; they matter only for the alarm channel and the fixtures.
- **Cadence.** Recomputed **every environment step** (a probe step is an environment step). `p_c(t) = g(q_c(t))`, `α^S` is not emitted by this arm's score path (see §3). Outputs are step-quantised: `persistence_unit = "steps"`.
- **Expected qualitative behaviour, stated in advance.** Under the shared-cause confounder, `β` loads `a_t` onto confounded distractors x (children of u, correlated with a through W_u), so `l_c` is large on channels that are **not** action-reachable and the arm's AUC falls to or below chance (Codex measured 0.428–0.463 at N_x = 30, present). **This is the phenomenon the benchmark measures, not a defect of the comparator**, and the spec is frozen with that behaviour visible.

## 3. Alarm channel [N]

- **Recursion.** `S_0 = 0`; for t ≥ 1, `m_t = max_{c ∈ 𝒞*} |r̃_{t,c}|`, `S_t = max(0, S_{t−1} + m_t − k)`.
- **Reference value.** `k = mean(m) + 0.5 · sd(m, ddof=1)` over the arm's own fault-free calibration stream (non-probed for arm 2, probed for arm 3 — §4). The 0.5 multiplier is frozen **[prov]**; it is the only free constant in the recursion.
- **Outputs.** `update` returns `(p[C], stat, raise)` with **`stat = S_t` every step** and **`raise = 1 iff S_t > h`, no persistence applied**. `statistic_is_monotone_in_alarm = True`.
- **Ownership.** Persistence `p = 3` and refractory `r = 20` belong to the harness (`contract_ref.count_alarms`), per contract §G and interface v3. The arm applies neither.
- **Threshold.** `h` is supplied by `set_threshold(h)` from the harness's ARL_0 calibration under the §0 D-2a rule: per (environment, regime, confounder, distractor_level, delay, estimator) cell, shared across seeds, ≥ 400 fresh-start run lengths, 95 % interval for the mean inside [900, 1100], hard cap 2e6 steps. `S` resets to 0 at every episode reset, so the calibrated quantity is the fresh-start run length (D-6b).
- **Separate calibration for the probed arm.** `k` and `h` are recomputed for `cusum_linear_probed` on probed fault-free streams. Probe injections replace the applied action with a ±e_k unit vector, which changes the innovation distribution through action clipping, delay τ, and (family N) saturation; Codex measured passive/probed thresholds differing by up to ≈ 25. Sharing `h` across the two arms would confound "probes help" with "probes are out of the null".
- **Scope.** Per contract §G (R3-8), ARL-band attainment governs the descriptive alarm outcomes only. P1 (AUC on q) and P2 are computed on all pairs regardless of band.

## 4. Probed variant, D-7a [N]

- **Stream.** `cusum_linear_probed` runs on episodes carrying the **exact probe injections used by `seq_ibd`** — same schedule, same period Π, same reservoir, same seed, same signed unit vectors, same replaced-action semantics. The two arms are matched transition-for-transition; only the estimator differs.
- **Predictor.** **Bitwise identical `β, μ_c, σ_c, l_c`** to the passive arm, fitted on the same non-probed fault-free population of §1. This makes the score function literally identical across arms 2 and 3, so the arm-3 minus arm-2 difference isolates the effect of the probes on the *stream*, not on the *fit*. T-CMP-identity asserts the equality.
- **Re-calibrated objects.** Only the null-dependent ones: `k`, `h`, the isotonic map `g`, the operating point `θ*`. Justification as in §3.
- **Probe transitions in the fit:** excluded (§1 probe hygiene). **In scoring:** included, unmarked, with no gap, no down-weighting, and no reset of the window — the probe step is an ordinary environment step whose action happened to be ±e_k.
- **Probe budget accounting.** `request_probe` returns `None` for both arms; the harness injects. Arm 3 is nonetheless **charged the full `probe_budget = 0.05`** in the ledger, and charged task regret where a reward exists, so the cost comparison against `seq_ibd` is honest.
- **What this arm is for.** It separates *having* interventions from *using them causally*. Codex's reproduction found arm 3 within 0.003 AUPRC of arm 2 and 0.350–0.450 below `seq_ibd` at offset 500 under confounding. The spec is frozen with that result known and disclosed (contract §G Disclosure).

## 5. Calibration tier [N] (secondary, contract §G tier 2)

- **Splits.** Per cell and **per arm**: 24 episodes to fit the calibrator, 16 disjoint episodes to choose the operating point, each half event-carrying (12/12 and 8/8), all disjoint by whole episode from the 20 predictor-fit episodes of §1 and from every scored episode. Both artefacts are **frozen before any scoring**.
- **Who fits it.** The isotonic map needs oracle labels `1[c ∈ S^obs,ε]`, which the estimator may never see (§E5 isolation). The harness fits `g` from the arm's raw `q` values and installs the frozen map; the estimator's `calibrate()` computes only `β, μ, σ, l, k`. **[Opinion]** interface v3 should say this explicitly; today it is implied by §G listing "isotonic p_c calibrator" among harness metrics deliverables.
- **Fit.** Non-decreasing PAVA on pairs `(q_c(t), label_c(t))` pooled over eligible steps and channels of the 24 fit episodes, with **exact-tie aggregation** (identical q values form one block before pooling, weighted by count). Degenerate channels contribute at `q = q_absent`, so the absent extreme is a knot, not a NaN.
- **Apply / extrapolation.** Right-continuous step function: `g(q) = v[searchsorted(knots, q, side="right") − 1]`, index clamped to `[0, len−1]`; below the first knot returns the first value, above the last returns the last; output clipped to `[0,1]`. No linear interpolation, no smoothing.
- **Operating point.** `θ*` = the **largest** tied maximiser of micro-F1 on the **16-episode validation split only** (never on the fit split — D9-codex-7). Frozen. Reported F1 is at `θ*`.
- **Scoring.** Leave-one-instance-out with held-out event times; cross-fitted Brier and log loss of the calibrated `p_c`. No "uncalibrated proper score" is reported (D9-codex-8).
- **Primary is untouched by all of this.** AUC on raw `q` is invariant to any monotone `g`, so the primary uses no supervised data.

## 6. Information set and timing [N]

- **Declared string, arm 2:** `"channels=all_observed(C); applied_action=visible; t=visible; probe_flag=delivered_not_consumed; reward=not_visible; terminated_truncated=not_visible; oracle=never; P=(Assign,gain,avail)=never; regime_bundle={hash only, params unused}; calibration_split=used(predictor fit; harness-fitted isotonic+operating point); probes_requested=none"`.
- **Declared string, arm 3:** identical, plus `"probe_stream=externally_injected_identical_to_seq_ibd(schedule,seed); probe_signs=not_consumed; probe_budget_charged=0.05"`.
- **Never seen:** oracle labels, `S^latent`, `S^obs,ε`, `e_j`, `R`, `M`, `P`, event types, event times, reward, termination flags, the other arm's state.
- **Probe flags — decision and justification.** Arm 2 declares `probe_flag` **delivered but not consumed**; on its own stream the flag is always False, so this is free. Arm 3 sees the same transitions as `seq_ibd` and therefore *could* read both the flag and, from `applied_action`, the probe sign — the sign is the action. Withholding it is not possible and pretending otherwise would be dishonest. Instead the constraint is **on the frozen formula**: `q` and `S` are functions of `(r̃, l)` only, and `l` is fitted offline; neither conditions on the marker or the sign. This is enforced by T-CMP-probe-blind, which permutes the `probe_flag` field of every transition and asserts bitwise-identical `(p, stat, raise)`, and by code review at freeze — not by data withholding.
- **Timing at reset.** `reset` clears `S ← 0`, the r̃ ring, and `t ← 0`; `β, μ, σ, l, k, g, θ*, h` survive (they are arm state, not episode state), and the harness owns persistence across the reset. The first `update` is at t = 1 and returns values computed from innovations up to and including t. `p_c` is emitted every step; while `t < n_warm` it is the constant vector `g(l)`. Nothing is emitted before the first transition.
- **Persistence.** `persistence_unit = "steps"`; no epoch quantisation.

## 7. Costs [N]

- **Probe steps:** 0 for arm 2; 0 requested and `probe_budget = 0.05` charged for arm 3.
- **Operations per step:** one dense mat-vec `X_t β` at `C·(C+K+1)` multiply-adds, plus O(C) for standardisation, ring update, running window sum, score, and the max. ≈ 6.8·10² at C = 24 (N_x = 10) and ≈ 1.4·10⁴ at C = 114 (N_x = 100) — the same order as the IBD arm's amortised ≈ 1.3·10⁴, which keeps the cost comparison fair.
- **Memory:** `β` at `(C+K+1)·C` floats (13.4 k ≈ 107 kB at C = 114), the W = 500 r̃ ring at `500·C` floats (57 k ≈ 456 kB at C = 114), plus O(C) frozen vectors and the isotonic knots. ≈ 0.6 MB at C = 114, ≈ 0.13 MB at C = 24. No growth in t.

## 8. Parameters [N]

No parameter may change after the pilot without re-running ARL_0 calibration, the isotonic fit and the black-box acceptance suite (§E6). There is no outcome-dependent tuning clause.

| # | Symbol | Value | Status | Justification |
|---|---|---|---|---|
| 1 | ε, H, a_max, τ_max | 0.05, 3, 2.0, 2 | contract §0 | Normative; not this spec's to choose. |
| 2 | p, r, H_det, ARL_0 | 3, 20, 200, 1000 | contract §0 | Normative; p and r applied by the harness. |
| 3 | episode_len, event_t, offsets_rank | 2000, 1000, {200,500,1000}, primary 500 | contract §0 | Normative; fixes W below. |
| 4 | cal_split, probe_budget | 24/16, 0.05 | contract §0 | Normative; arm 3 is charged the budget it does not request. |
| 5 | lag order | 1 | frozen | Contract §H says `[o_t, a_t, 1]`; adding lags would make it a different arm. |
| 6 | feature layout | `[o_t (C), a_t (K), 1]` | frozen | Fixes the `β_{a,c}` block that defines `l_c`. |
| 7 | λ_rel | 1e-4 **[prov]** | frozen | Conditioning guard against silent/copied columns; scale-relative so it is invariant to gain and units. |
| 8 | intercept penalised? | no | frozen | Penalising it would bias `μ_c` away from 0. |
| 9 | n_pred_fit | 20 episodes **[prov]** | frozen | 40,000 transitions ≫ (C+K+1) even at C = 114; matches the reproduced pilot. |
| 10 | probe-drop guard | probe + next τ_max | frozen | A probe at t contaminates b through t+1+τ. |
| 11 | σ_floor | 1e-6 | frozen | Numerical guard only; never reached by a live channel. |
| 12 | σ_deg | 1e-3 **[prov]** | frozen | Below this a channel is dead, not sensitive; prevents a permanent alarm from a dropped sensor. |
| 13 | z_cap | 8 | frozen | Same bound as the IBD arm, so both calibrator domains are bounded identically. |
| 14 | W | 500 | frozen | Exactly 100 % post-event at the primary offset 500 (same choice as the IBD arm). |
| 15 | n_warm | 30 **[prov]** | frozen | Below it `√n·mean` is a single noisy draw; never binds at scored offsets. |
| 16 | q_cap, q_absent | 40 **[prov]**, −40 | frozen | Bounds the isotonic domain; `q_absent` puts degenerate channels at the bottom knot, mirroring the IBD arm's `a_absent = −z_cap`. |
| 17 | CUSUM k multiplier | 0.5 **[prov]** | frozen | `mean + 0.5 sd` of `max_c\|r̃\|`; the only free constant in the recursion. |
| 18 | isotonic rule | PAVA non-decreasing, exact-tie blocks, right-continuous step, clamp-extrapolate, clip [0,1] | frozen | Deterministic and monotone; leaves the primary AUC untouched. |
| 19 | operating point rule | largest tied micro-F1 maximiser on the 16-episode validation split | frozen | Separates knot fitting from threshold choice (D9-codex-7). |
| 20 | persistence_unit | "steps" | frozen | The arm updates every step; no epoch quantisation. |
| 21 | **h** | set by harness, per arm and cell | **calibrated** | The single scalar knob; fresh-start ARL_0 = 1000 under D-2a. |

**Count: 21 rows — 4 contract blocks (12 inherited constants), 16 frozen arm parameters, 1 calibrated (`h`). Zero swept parameters in the confirmatory configuration.** Fitted objects frozen at calibrate: `β`, `μ[C]`, `σ[C]`, `l[C]`, `k`, `g`, `θ*`. The probed arm introduces **no new parameter names** — it re-values `k, h, g, θ*` only. Six values are provisional (`λ_rel, n_pred_fit, σ_deg, n_warm, q_cap, k`-multiplier) and must be frozen before confirmation. `W ∈ {250, 1000}` is an appendix sensitivity with its own re-calibrated `h`, never substituted for the confirmatory arm.

## 9. Executable fixtures [N] (described, not implemented here)

Each is a deterministic test in `executable-proofs/gate/test_comparator.py` with a hand-checkable expected ordering, mapped in `coverage-matrix.md`.

- **F1 — confounded false positive (T-CMP-conf).** Family L, `f_conf = 0.5`, `|corr(a_k, x_j)| ≥ ρ_min`, fault-free. Assert `l_c` on at least one confounded distractor exceeds `l_c` on at least one genuinely reachable downstream channel d, and that episode AUC of `q` against `S^obs,ε` is **below 0.5** at offset 500. This pins the pathology the benchmark exists to measure; if it stops holding, the comparator has silently changed.
- **F2 — actuator-loss true positive (T-CMP-loss).** Complete loss of actuator 0 at t = 1000 on a cell with `s_change_certified = True`. Assert `q` falls on channels leaving `S^obs,ε` and is flat on channels remaining; assert the CUSUM raises within `H_det` at the calibrated `h`; assert confounder-absent AUC at offset 500 ≥ 0.6.
- **F3 — padding channel (T-CMP-pad).** One noise-only pad (`ε^o` only) and one hard-silent pad (`avail = 0`). Assert the noise pad is non-degenerate, is scored as an ordinary negative, and never enters 𝒞\* by accident; assert the silent pad is flagged degenerate, gets `q = q_absent` at every t, and is excluded from `max_c |r̃|` — with the exclusion removed, the test must fail with a permanent alarm.
- **F4 — copied channel (T-CMP-copy).** Two rows of `Assign` mapping to the same latent with equal gain. Assert `|q_{c1}(t) − q_{c2}(t)| < 1e-6` at every t and that the ridge solve is finite (this is the fixture that justifies λ). Assert grouped scoring is the harness's job, not the arm's.
- **F5 — probe-shock null (T-CMP-probe-null).** Fault-free stream carrying the `seq_ibd` probe schedule. Assert (a) probe transitions and their `τ_max` successors are dropped from any training population that contains them; (b) `β, μ, σ, l` are bitwise identical to the passive arm; (c) `k_probed ≠ k_passive` and `h_probed ≠ h_passive` on family N or τ = 2; (d) the probed arm's fresh-start ARL under `h_passive` is **outside** [900, 1100], which is the evidence that separate calibration is necessary rather than merely tidy.
- Plus **T-CMP-probe-blind** (§6), **T-CMP-ridge** (§1), **T-CMP-identity** (§4).

## 10. Pseudo-code [N]

```
# frozen after calibrate(): beta, mu[C], sd[C], l[C], k, degen[C]; g, theta* installed by harness
# consts: LAM_REL=1e-4, W=500, Z_CAP=8, Q_CAP=40, N_WARM=30, SIG_FLOOR=1e-6, SIG_DEG=1e-3, KMULT=0.5

def calibrate(transitions):                      # arm 2 and arm 3 receive the SAME fault-free non-probed split
    tr = drop_probe_and_successors(transitions, tau_max=2)     # guard; no-op on the confirmatory split
    X  = rows([o_t, a_t, 1] for tr, within-episode only); Y = rows(o_{t+1})
    lam = LAM_REL * trace(X.T @ X) / (C + K)
    beta = cho_solve(X.T @ X + lam * diag(1..1, 0), X.T @ Y)   # intercept unpenalised
    R    = Y - X @ beta
    mu, sd = mean(R, axis=0), maximum(std(R, axis=0, ddof=1), SIG_FLOOR)
    degen  = std(R, axis=0, ddof=1) < SIG_DEG                  # dead channels
    l      = norm(beta[C:C+K, :], axis=0) / sd                 # standardised action loading, frozen
    Rt     = clip((R - mu) / sd, -Z_CAP, Z_CAP)
    m      = max(abs(Rt[:, ~degen]), axis=1)
    k      = mean(m) + KMULT * std(m, ddof=1)                  # arm 3 recomputes k on its PROBED null stream
    reset_episode()

def reset_episode():  S = 0.0; ring = empty_ring(W, C); n = 0; t = 0

def update(transition):                          # every environment step; probe steps included, unmarked
    t += 1
    r   = transition.obs - [transition.prev_obs, transition.applied_action, 1] @ beta
    rt  = clip((r - mu) / sd, -Z_CAP, Z_CAP)
    ring.push(rt); n = min(W, t)                                # running sum kept incrementally
    shift = 0.0 if t < N_WARM else abs(sqrt(n) * ring.mean_last(n))   # vector over C
    q   = clip(l - shift, -Q_CAP, Q_CAP)
    q[degen] = -Q_CAP
    S   = max(0.0, S + max(abs(rt[~degen])) - k)                # CUSUM on max_c |r~|
    return (g(q), S, 1 if S > h else 0)                         # no persistence: harness owns p and r

# probed arm (cusum_linear_probed): identical code path and identical beta/mu/sd/l.
# The harness feeds it the seq_ibd probe stream (same schedule, same seed). Only k, h, g, theta*
# are re-derived on probed calibration streams. request_probe(steps) -> None for both arms.
```

## 11. Claims we do not make [N]

This is an **engineering baseline**: the strongest passive reading we could find, frozen on principle so that the confirmatory margin is decided by the science and not by the baseline's specification (D9-GM-4 showed the choice moves the margin by ≈ 0.29 AUPRC). We do **not** claim it is the strongest possible passive comparator, nor the best linear residual monitor, nor optimal in any sense. We make no identifiability, consistency, FDR-control or ARL-optimality claim; the CUSUM's ARL_0 is *calibrated*, not *derived*, and the innovations are neither independent nor Gaussian under the closed-loop policy. We do **not** claim `q` estimates `e_j`, `R`, `M`, body membership (§C6), or anything but a ranking against `S^obs,ε`. We do **not** claim that arm 3's poor showing proves probes are useless — it is evidence that *this* statistic cannot use them, which is exactly the mechanism control it was built to be. We do **not** claim the comparator is well calibrated: §2 states in advance that under confounding it ranks below chance, and that is reported as a result, not repaired. Finally, we disclose that this specification and the primary metric were frozen **after** pilot simulations had shown the interventional arm clears them (contract §G Disclosure); confirmation uses fresh seeds and fresh instance draws.

**References.** `stage-0a-contract-v3.5.md`; `interface-spec-v3.md`; `d9-adjudication.md`; `review-d9-codex/findings.md` and `sim_d9.py`; `review-d9-gemini/findings.md` and `sim_d9.py`; `sequential-ibd-spec.md`; `confirmation-design.csv`. Page (1955), CUSUM. Barlow et al. (1972), isotonic regression / PAVA.
