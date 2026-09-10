# Sequential IBD — normative specification (DRAFT 4, informative until signed)

**Status.** Draft 4, 7 September 2026. Basis: `stage-0a-contract-v3.7.md` §§0, A0, B, C, D, F, G, H, H2; `interface-spec-v4.md`; `executable-proofs/gate/reference_generator.py`; `round4-adjudication-and-tally.md`; `d10-adjudication.md`. Supersedes draft 3 (`review-ibd-spec/sequential-ibd-spec.draft3.md`). **Informative until Daniel signs.**

Draft 4 changes four things: probe allocation becomes **balanced pre-randomised (k, sign) blocks** (D-10.4); the alarm channel gains a **warm-up** so it is calibratable at all (R4-1, GM-06); the **observation clock** is fixed at transition level against the frozen generator (R4-CX-08); **offsets** move to {200, 500, 1000} (D-10.5). The statistic, the window, the tie-corrected rank-sum formula and the h-independence design are unchanged — three round-4 implementations agreed on this arm to within 0.012 AUC, so none of that is re-opened.

**Published IBD, cited honestly.** Liu, Cheng & Bogdan, arXiv:2603.18257 v2: two branches under a dedicated π_probe, ≈ 32k steps once, Welch t per (dimension, horizon), Bonferroni within and BH across, Props. 3.3–3.5. **This arm departs**: no baseline branch, no π_probe; the contrast is between the estimator's own probe signs, sequentially, in-task, at 5 % of steps. None of Props. 3.3–3.5 is inherited (§8).

---

## 1. Interface and information set [N]

Online estimator of **action-reachable observation support** `S^obs,ε_{t,H}` (C3, C6) — not body membership, not R, not M.

- `information_set = "transitions_only; no_reward; no_oracle; own_probe_allocation_known; calibrator_injected_via_configure"`. Sees `Transition = (prev_obs, applied_action, obs, probe_flag, t)` only — no reward, oracle labels, P, latents, event times, **and no `episode_len`**. It knows its own (k, sign) allocation because it generated it.
- `configure(bundle)`: `regime_model_params = None`; `calibrator_params = {g_knots}`, **fitted by the harness**, which owns the oracle labels; `arm_reference_params = {ā[C], v[C]}`. Hashed and logged.
- `fit_predictor` is a **no-op**; `fit_alarm_reference(transitions)` computes (ā, v) per §4 on the arm-specific fault-free (probed) stream; `set_threshold(h)`.
- `update(transition) -> (raw_support[C], p[C], stat, raise)`, once per environment step, piecewise constant between epochs. `raw_support = a[C]` is the raw statistic the evaluator scores; draft 3's estimator-written ledger side-channel is deleted (R4-CX-03). `raise = 1[stat > h]` with **no persistence inside the estimator**; `persistence_unit = "epochs"` is declared and the harness applies p = 3 epochs, r = 20 steps once via `count_alarms`.
- `request_probe(steps) -> actions[steps, K] or None`; `preferred_probe_steps = 1`; `needs_calibration_split = True`; `statistic_is_monotone_in_alarm = True`.

## 2. Observation clock, stated once [N] (contract C, R4-CX-08)

The transition of step t is `(prev_obs = o_t, applied_action = a_t, obs = o_{t+1})`, and **`o_t` is the PRE-action observation** — what the policy reads before choosing `a_t`. This is `reference_generator.Instance.run`: `O[t]` is computed before `a = policy(O[t], …)`, `O[t+1]` after `step_latent`. Since `b_{t+1} = A_b b_t + B a_{t−τ}`, a probe at `t_p` first moves the observation at `o_{t_p+τ+1}`: **first hit at h = τ + 1**.

The estimator writes `O[t] := tr.prev_obs`, `O[t+1] := tr.obs`, and forms `D_c^h(t_p) = O[t_p+h] − O[t_p]`, h ∈ ℋ = {1,2,3}.

| update call (τ = 0, probe `+e_k` at t_p = 20) | transition | contributes |
|---|---|---|
| t = 20 | (o₂₀, **+e_k**, o₂₁) | `D¹ = o₂₁ − o₂₀` — first nonzero, h = τ+1 = 1 |
| t = 21 | (o₂₁, policy, o₂₂) | `D² = o₂₂ − o₂₀` |
| t = 22 | (o₂₂, policy, o₂₃) | `D³ = o₂₃ − o₂₀`; **unit closes**, `t = t_p + max(ℋ) − 1` |

At τ = 2 the same probe gives `D¹ = D² = 0` and the first nonzero at h = 3 = τ+1. **T-IBD-horizon** asserts both on the reference generator. **Epoch grid: t ≡ 2 (mod 20)**, t = 22, 42, …, 1982 (99 epochs). Outputs recomputed at an epoch, held between epochs.

## 3. Probing and allocation [N]

**Block-periodic single-step probes, L = 1, Π = 20.** A probe step is an environment step whose applied action is **replaced** (contract §0). Grant at step t iff `used + 1 ≤ floor(probe_budget·t)` **and** `t − t_last ≥ Π`, with `used = 0`, `t_last = −Π` at reset; integer arithmetic, no reservoir, no adaptive element. The invariant `used(t) ≤ floor(0.05·t)` holds after every step (**T-IBD-budget**). Probes therefore fall on every multiple of 20: **100 applied per 2,000-step episode**, fraction exactly 0.050, of which the probe at t = 2,000 closes no unit, leaving **99 units** (**T-IBD-count**). *(R4-23: that waste is accepted, not repaired — a terminal grant condition would need `episode_len`, which the information set excludes. Cost: 1 % of the budget, declared.)*

**Allocation: balanced pre-randomised blocks (D-10.4).** The estimator holds a block of length **2K** containing each (actuator k, sign) pair exactly once in **uniformly random order from its own RNG**; each grant consumes the next entry; an empty block is refilled by a fresh independent permutation. The draw is **independent of state, observations, task policy, `u_t`, G and `ρ_u`** — pre-randomised, not adaptive. This replaces draft 3's i.i.d. draw and is the randomisation severing C→a (T-E2d).

**Consequence.** A window of `n_u` consecutive units contains ≥ `floor(n_u/2K) − 1` complete blocks, so every (k, sign) group has at least that many members. At K = 2, `n_u` = 25: each group holds **5 to 7** units, so `min(n₊,n₋) ≥ 5 > n_min_sign = 3` **always** (verified exhaustively over 5·10⁴ windows). Codex's 12.7 % per-window actuator loss (R4-CX-09) and Opus's 8–12 % episodes with a deleted actuator (R4-5) go to **zero by construction**. `n_min_sign = 3` is **retained as a guard that should never bind**, and that it never binds is asserted, not assumed (**T-IBD-blocks**).

**Scaling rule [N].** `W_steps` must satisfy `floor(W_steps/(Π·2K)) ≥ n_min_sign + 1`, i.e. **`W_steps ≥ 8K·Π = 160K`**. Satisfied at K ≤ 3 by `W_steps = 500`; at K > 3 raise `W_steps` and recompute §5's table. Pendulum-v1 (K = 1) and PointMass2D (K = 2) are inside the rule. This replaces GM-05's `W_steps ≥ 120K` with a derivation.

**Eligibility mask [N].** Unit closure is simultaneous across ℋ, so count-eligibility depends on k alone, but the mask is returned indexed `(k, h)` as `eligibility_mask[K][|ℋ|]`, with `n_units` and `n_eligible_cells`, in the ledger every epoch. A cell is **eligible** iff `min(n₊,n₋) ≥ n_min_sign`, **non-degenerate** iff `σ_U > 0`. `a_c = 0` from ineligibility is now distinguishable from `a_c = 0` on a genuinely unresponsive channel — the defect R4-5 and R4-CX-09 both named.

**Jitter: rejected, with reason** (closes roadmap v4.6 J7 / GM3-7 / R4-25). Jitter would break the `floor(0.05·t)` invariant, the 25-unit count and the fixed epoch grid, and make the offset table data-dependent. GM3-7's aliasing concern — a periodic 20-step comb against a control-tier resonance — is carried as a **declared limitation** (§8) with a pilot diagnostic against the closed-loop spectrum, not repaired by jitter.

**No washout, and why — kept, with two caveats.** The argument survives: **both groups are probe units** and the label comes from a device that never reads state, so an earlier probe's slow-mode tail is a shared nuisance, not an arm asymmetry. Draft 2's `null guard` stays deleted. Two caveats are normative.

1. **Residual dependence.** Units share one trajectory; the |ℋ| increments at one anchor overlap; a probe's tail enters later units. The z is therefore **not claimed to have exact level**, and the primary never uses z as a p-value. Codex's 3,000-replicate AR(1) attack at ρ ∈ {0.8, 0.95} gave 4.4–5.4 % two-sided exceedance against nominal 5 % — a bounded check, not a proof.
2. **Balanced-block consequence (new).** Under i.i.d. draws the conditional history given `S_p = +` and `S_p = −` was exactly identical. Under blocks it is not: within a block a `(k,+)` probe cannot follow another `(k,+)`, so an earlier `+e_k` tail lands **preferentially in the `−` group**. The induced correlation is O(1/(2K−1)) and the carry-over is bounded by body decay over one cadence — at the generator's `rho_b = 0.85`, `0.85²⁰ = 3.9·10⁻²`, differenced further by the increment. Direction: for a channel genuinely reached by k it **attenuates** |z| (conservative, costs power); for the long-lag confusion of §8 it can flip the sign of z while leaving |z| elevated, so that failure mode is unchanged in kind. Declared, not repaired.

## 4. Statistic and alarm channel [N]

**Window.** Trailing `W_steps = 500` steps **on anchor time**, half-open: `t_p ∈ (t_p* − W_steps, t_p*]`, exactly **25 units** in steady state. The window **never resets** — the estimator does not know the event time, and a reset would make the statistic path h-dependent.

**Per (channel c, horizon h, actuator k).** Group `+` = signed increments `D_c^h(t_p)` of window units probed with `+e_k` (n₊); `−` likewise (n₋); N = n₊+n₋. Ineligible cells contribute nothing. Rank the N values jointly with **mid-ranks**; R₊ = rank sum of `+`.

  U = R₊ − n₊(n₊+1)/2  μ_U = n₊n₋/2

  **σ_U² = (n₊n₋ / (N(N−1))) · [ (N³−N)/12 − Σ_g (t_g³−t_g)/12 ]**,  **σ_U ← sqrt(max(0, σ_U²))**

over distinct tied values g with multiplicity t_g. **Tie rounding (GM-08):** tie groups are formed on increments rounded to 12 significant decimal digits; the `max(0,·)` guard makes the −10⁻¹⁷ cancellation unreachable. No continuity correction (declared). σ_U = 0 ⇒ degenerate cell, contributes nothing.

  **z_{c,k,h} = clip((U − μ_U)/σ_U, −8, +8)**;  **`a_c` = max over eligible, non-degenerate (k,h) of |z|**, else 0.

`a_c` is a max of up to K·|ℋ| = 6 values, so its null mean is positive, not zero (round-4: non-reachable ≈ 1.44–1.54, indirect ≈ 1.78–1.87, direct ≈ 2.65–2.69). Discrimination comes from separation. A NaN reaching any output is a hard error, never a silent 0. **Exact by construction of the randomisation device:** the allocation is independent of state, task policy, `W_u`, `ρ_u` and G — the property draft 2 lacked. **Not claimed:** exact rank-sum level across the window (caveats above).

**Alarm reference.** Frozen at pass 0: `ā_c` = median `a_c`, `v_c` = max(1.4826·MAD, v_floor = 0.5), over the **pre-event segments** — definition **unchanged from draft 3 and it survives**: full-window epochs with newest anchor `t_p* ∈ {500,…,980}` (25 per event-carrying fit episode) and `t_p* ∈ {500,…,1980}` (75 per event-free one) = **1,200 epochs per cell**, pooled per channel.

**Warm-up [N] (fixes R4-1, GM-06).** **`n_warm = W_steps/Π = 25` complete units.** `stat_t = 0` — hence `raise = 0`, the harness's h grid being strictly positive — **until the window holds ≥ n_warm complete units**. Thereafter `stat_t = max_c |a_c(t) − ā_c|/v_c`, recomputed each epoch, held between. The first eligible epoch is **`t_warm = 502`** (25th unit anchored at 500, closing at 502), required to satisfy `t_warm < event_t = 1000` (**T-IBD-warmup**).

This removes the draft-3 defect exactly. There, `a_c ≡ 0` on every channel during warm-up while `ā_c` was fitted on full windows, so `stat_warm = max_c ā_c/v_c` was the **largest value the statistic ever took** (5.44–5.68 measured, against a post-event max of 4.25–4.67); ARL_0(h) was a two-valued step function pinned at 63 steps and the D-2a band [900, 1100] was unattainable at any h. With `stat = 0` on the prefix, and balanced blocks guaranteeing eligible cells after it, the post-warm-up `stat` has a continuous distribution, so **ARL_0(h) is continuous and non-decreasing and the bisection has a root** (**T-IBD-mono**, **T-IBD-arl**). Defensively, an epoch with zero eligible cells on every channel holds `stat`, forces `raise = 0`, and is flagged `degenerate_epoch`.

**ARL_0 clock starts at `t_warm`**, not at reset; the prefix is a declared **non-scoring prefix excluded from ARL_0**. Consequence for the harness: to observe ≥ 400 fresh-start run lengths of mean ≈ 1,000 under D-2a, use **400 independent event-free streams of ≥ 4,000 steps** (1.6·10⁶ ≤ the 2·10⁶ cap), of which 400 × 502 ≈ 2.0·10⁵ steps (12.6 %) are warm-up; end-of-stream censoring (≈ 3 %) is reported, never dropped.

**h-independence.** `stat` is a deterministic function of the stream and the frozen artefacts — no accumulation, reset, burst or online re-estimation — so the harness records **one** `stat` stream per calibration episode and evaluates every h by offline replay (**T-IBD-hindep**); the D-2a cap is per cell, not per h. *(Opinion: consecutive epochs share 24 of 25 units, so the raise sequence is strongly autocorrelated and p = 3 filters little — h does essentially all the work. The harness should also report the p = 1 epoch sequence from the same stream, at zero cost.)*

`p_c = g(a_c)` every step from a cache refreshed at every epoch; **no state ever freezes `p_c`**.

## 5. Calibrator, offsets, window memory [N]

**Calibrator.** `g` is a **single pooled** non-decreasing isotonic (PAVA) map over all channels on [0, 8], **fitted by the harness** — which owns the labels — on the **24-episode fit split**, on `(a_c(t), 1[c ∈ S^obs,ε_t])`, injected via `configure(calibrator_params)`. **Post-event states are included**, because the post-event label distribution is what the calibrator must map; **straddling epochs are excluded**, applying §4's window-purity rule to `g` (R4-14, thereby dispositioning GM3-4). Retained per event-carrying episode: `t_p* ∈ {500,…,980}` (25, all pre-event) ∪ `{1480,…,1980}` (26, all post-event) = **51**; per event-free episode **75**; total **12·51 + 12·75 = 1,512 epochs per cell**, per channel. Fitted values clamped into [0.001, 0.999] so log loss is finite. The operating point for secondary F1 is chosen on the **separate 16-episode validation split**; both artefacts frozen before scoring. **The primary tier uses neither.**

Pooling is justified because **a channel's label is near-constant within an episode**, so a per-channel isotonic map would be degenerate — not because the estimator cannot see labels; the harness does (draft 3 row 15's reason was a non-sequitur, R4-13). The cost is declared: pooling across heterogeneous channel types (padding, live w, confounded x, body b, downstream d) is **mis-calibrated per type**. This affects **tier 2 only** — the primary AUC is monotone-invariant — and per-type reliability is a tier-2 diagnostic.

**AUC tie rounding [N] (R4-20).** The primary is **mid-rank Mann-Whitney: ties receive half credit.** Load-bearing here, because this arm assigns `a_c = 0` to every unresponsive channel by design.

**Offsets (D-10.5).** Primary AUC at **offsets_rank = {200, 500, 1000}**, primary 500; co-primary P2 at the **same** offsets. Draft 3's P2 offsets {10, 50, 200} are deleted: R4-8 showed they measured a **pre-event** quantity for both arms (1/25 and 3/25 post-event units) while being reported as post-event. `p_c` at offset Δ is read at the last epoch ≤ `event_t + Δ`. Convention: the event applies before step `event_t` is taken, so an anchor `t_p ≥ event_t` is post-event.

| Offset after event | **200** | **500** | **1000** |
|---|---|---|---|
| Epoch read (event_t = 1000; grid t ≡ 2 mod 20) | 1182 | 1482 | 1982 |
| Newest anchor in window | 1180 | 1480 | 1980 |
| Post-event units / 25 | **10** | 25 | 25 |
| Post-event fraction | **0.40** | 1.00 | 1.00 |

**Offset 200 is labelled a transition window: 0.60 pre-event, 0.40 post-event**, reported with those fractions and never as a clean post-event outcome. Boundary sensitivity declared: under the opposite convention the fractions are 0.36 / 0.96 / 1.00. This is a property of any probe-budgeted windowed estimator and must not be repaired by shortening `W_steps` after seeing outcomes. **R4-4 correction:** the offset-200 attenuation mechanism is **dilution** (15 of 25 window units are pre-event), **not** `n_min_sign` — which applies to the window's 25 units, never to a post-event subset the estimator cannot identify, and which under balanced blocks cannot bind at all. **T-IBD-offsets** asserts mixture and eligibility separately so the two are never conflated again.

**Passes.** *Pass 0:* `configure({None,None,None})`; `fit_predictor` no-op; `fit_alarm_reference` computes (ā, v); the estimator emits `p_c = a_c/8` clipped, never scored; the harness fits `g` from the returned `raw_support` stream and the oracle labels. *Pass 1:* `configure({None,{g_knots},{ā,v}})`; `set_threshold(h)`; run. `set_threshold` touches nothing but the comparison in §4, so `raw_support`, `p_c`, the primary and the co-primary are invariant to h and to the ARL_0 sweep.

## 6. Parameters [N]

No parameter may change after the pilot without re-running ARL_0 calibration, the isotonic fit and the acceptance suite (E6). **There is no outcome-dependent tuning clause.**

**Inherited from contract §0, not this spec's to choose (18):** ε, H, ℋ, 𝒜, a_max, probe_budget, p, r, w_T, H_det, ARL_0, episode_len, event_t, offsets_rank, offsets_P2, n_min_sign, cal_split, τ.

| # | Symbol / choice | Value | Status | Justification |
|---|---|---|---|---|
| 1 | L (probe block length in steps) | 1 | frozen | Maximises independent units at fixed budget. |
| 2 | Π (cadence) | 20 | frozen, derived | = L / probe_budget; spends the budget exactly. |
| 3 | reservoir_0 | 0 | frozen | Makes `used ≤ floor(0.05·t)` an invariant, not an average. |
| 4 | Clock convention | charge the step about to be taken; no terminal grant condition | frozen | `episode_len` is outside the information set (R4-23). |
| 5 | **Probe allocation** | **balanced pre-randomised blocks over (k,sign), length 2K, uniform order, estimator RNG, state-independent** | **frozen (new, D-10.4)** | Removes the 8–13 % actuator-deletion rate; keeps C→a severance. |
| 6 | Cadence jitter | none | frozen | Would break the budget invariant, the 25-unit count, the epoch grid (R4-25). |
| 7 | W_steps | 500, subject to `W_steps ≥ 160K` | frozen + derived rule | 100 % post-event at offset 500; rule guarantees `min(n₊,n₋) ≥ 5` (GM-05). |
| 8 | Window endpoint rule | half-open on anchor time | frozen | Gives exactly 25 units; removes endpoint ambiguity. |
| 9 | Observation anchor | `O[t] = prev_obs`; `D^h = O[t_p+h] − O[t_p]` | frozen (new) | Matches contract C and the generator; first hit at h = τ+1 (R4-CX-08). |
| 10 | Epoch trigger | `t = t_p + max(ℋ) − 1`; grid t ≡ 2 (mod 20) | frozen (new) | Earliest step whose `obs` supplies `O[t_p+3]`. |
| 11 | Increment sign | signed | frozen | Absolute increments discard the contrast the randomisation creates. |
| 12 | Tie correction | mid-ranks, §4 formula | frozen | One of two conventions in circulation; declared. |
| 13 | Tie rounding / variance guard | 12 significant digits; `sqrt(max(0,σ_U²))` | frozen (new) | Removes the −10⁻¹⁷ `ValueError` (GM-08). |
| 14 | Continuity correction | none | frozen | Immaterial to a rank-preserving primary. |
| 15 | z_cap | 8 | frozen | Bounds the calibrator domain and `stat`. |
| 16 | Aggregation | max over eligible, non-degenerate (k,h) of \|z\| | frozen | Contract §H; two-sided per cell. |
| 17 | `a_c` with no eligible cell | 0, with the eligibility mask returned | frozen | Bottom knot of g, not a NaN; the mask makes 0 interpretable (R4-5). |
| 18 | **n_warm** | **25 complete units (t_warm = 502)** | **frozen (new)** | `stat = 0` before it; makes ARL_0(h) continuous (R4-1, GM-06). |
| 19 | ARL_0 clock start | `t_warm`; prefix excluded | frozen (new) | A run length that cannot alarm is not a run length. |
| 20 | g | single pooled isotonic (PAVA), harness-fitted | frozen | Labels near-constant within an episode ⇒ per-channel fits degenerate (R4-13). |
| 21 | g fit domain | non-straddling epochs; post-event included | frozen (new) | Applies §4's purity rule to `g` (R4-14, GM3-4). |
| 22 | g clamp | [0.001, 0.999] | frozen | Keeps log loss finite. |
| 23 | ā_c | median over pre-event segment | frozen | Robust centre; MAD's partner. |
| 24 | v_c / v_floor | max(1.4826·MAD, 0.5) | frozen | A MAD below 0.5 marks a degenerate channel. |
| 25 | Pre-event segment | full-window epochs, `W_steps ≤ t_p* < event_t` (or ≤ episode_len if event-free) | frozen, unchanged | No post-event leakage into the alarm reference. |
| 26 | **h** | set by harness | **calibrated** | The single scalar knob; fresh-start ARL_0 = 1000 under D-2a. |

**Honest count: 26 arm parameters on 26 rows — 25 frozen, 1 calibrated (h).** Plus 18 inherited contract constants and 3 fitted objects frozen before pass 1: `g` (harness), `ā[C]`, `v[C]` (estimator, exported and re-injected). Draft 3's 21 rows grow by 5 net: allocation, jitter, anchor, epoch trigger, tie rounding, n_warm, ARL clock start and g fit domain are added, and draft 3's separate probe-draw and epoch-timing rows are absorbed. Nothing is deleted or re-tuned. `W_steps ∈ {250, 1000}` remains an appendix sensitivity with its own re-calibrated h.

## 7. Pseudo-code [N]

```
# reset():  t=0; used=0; t_last=-PI; block=[]; pending=[]; units=deque(); O={}
#           a=zeros(C); stat=0.0; p_cache=g(0)*ones(C); elig=zeros((K,3))   # R4-24
# frozen:   g (harness, pooled isotonic), a_bar[C], v[C], h
# consts:   HSET=[1,2,3]; HMAX=3; PB=0.05; PI=20; W=500; NW=25; NMIN=3; ZCAP=8
# ALLK    = [(k,s) for k in range(K) for s in (+1,-1)]         # 2K pairs

def request_probe(steps):
    if steps != 1: return None                                 # preferred_probe_steps = 1
    tp = t + 1                                                 # the step about to be taken
    if used + 1 > floor(PB*tp) or tp - t_last < PI: return None
    if not block: block = list(rng.permutation(ALLK))          # balanced, state-independent
    k, sgn = block.pop()
    used += 1; t_last = tp; pending.append((tp, k, sgn))
    return [sgn * e[k]]                                        # magnitude 1.0

def update(tr):                                                # once per environment step
    t = tr.t; O[t] = tr.prev_obs; O[t+1] = tr.obs              # o[t] is PRE-action (C)
    for (tp, k, sgn) in pending.due(t - HMAX + 1):             # unit closes at tp+HMAX-1
        units.append((tp, k, sgn, [O[tp+hz] - O[tp] for hz in HSET]))
        units.drop_while(lambda u: u.tp <= tp - W)             # half-open on anchor time
        for k2 in range(K):                                    # eligibility is h-invariant
            np_, nm_ = counts(units, k2)
            elig[k2][:] = 1 if min(np_, nm_) >= NMIN else 0    # guard; never binds (T-IBD-blocks)
        for c in channels:
            zz = []
            for k2 in range(K):
                for i in range(len(HSET)):
                    if not elig[k2][i]: continue
                    Gp = [u.D[i][c] for u in units if u.k==k2 and u.sgn>0]
                    Gm = [u.D[i][c] for u in units if u.k==k2 and u.sgn<0]
                    z = ranksum_z_tiecorrected(Gp, Gm)         # mid-ranks; sqrt(max(0,var))
                    if z is not None: zz.append(clip(z, -ZCAP, ZCAP))   # None = degenerate
            a[c] = max([abs(z) for z in zz], default=0.0)      # 0 = no eligible/usable cell
        p_cache = g(a)                                         # harness-fitted, every epoch
        stat = 0.0 if len(units) < NW else max_c(abs(a[c]-a_bar[c]) / v[c])    # WARM-UP
        ledger_epoch(t, elig, len(units), n_eligible_cells)    # eligibility mask (D-10.4)
    assert not isnan(p_cache).any() and not isnan(stat)        # hard error, never a silent 0
    return a.copy(), clip(p_cache,0,1), stat, int(stat > h)    # raw raise; harness owns p, r
```

## 8. Failure modes, limitations, claims we do not make [N]

**Failure modes.** (1) **Low alarm power at ARL_0 = 1000, declared not hidden**: 25 units give 5–7 per sign group and a complete actuator loss moves `a_c` by ≈ 1 z-unit against a `max_c` over 24–114 channels. The pilot reports P(alarm within H_det) against a no-event control on the same seeds; a value at or below the control is reported, not repaired. The arm is scored on support ranking; HPDT is descriptive. (2) **Offset 200 is a transition window** (§5), reported with its 0.60 pre-event fraction. (3) **τ = 2 leaves one usable horizon** (first hit at h = 3), so `a_c` is a max over K cells, not K·|ℋ|; reported separately, h not transferable. (4) **Multi-event schedules are exploratory**: the window never resets, so a second event within `W_steps` is read through a mixed window; no reset is added, since it would reintroduce h-dependence. (5) **C-dependence of `max_c`**: ARL_0 at fixed h falls as C grows; per-cell calibration absorbs it, but h is not transferable across distractor levels. (6) **Sign-flip blindness** (K8, g′ = −1): both groups flip, U → n₊n₋ − U, |z| unchanged — correctly invisible, since C3 keeps the channel. (7) **Long-lag confusion**: an actuator reaching c only at lag > max(ℋ) can lift `a_c` above the non-reachable floor through §3's residual dependence; under blocks the sign of z may flip but |z| stays elevated. A genuine false positive against the H = 3 estimand; reported, not suppressed. (8) **Power (not validity) depends on the task policy** through `probe_magnitude / policy_action_RMS`, logged per cell; comparisons ignoring it are inadmissible.

**Limitations.** (a) **Family N operating-point asymmetry (GM-04).** The washout argument is about **linear first moments**. On family N, `tanh(B a/s)·s` and `κ·clip(b⊙b)` make the response to `+e_k` and `−e_k` asymmetric about a state-dependent operating point that prior probe signs shift, so the sign contrast is not exactly symmetric under the null there. Round-4 family-N runs showed no material effect at registry values (AUC 0.921 against 0.912 on family L), so this is **prose, not a design change**; `T-IBD-exch` runs on family N as well as L, and a failure there is reported, not repaired. (b) **Tier-2 calibration is pooled across heterogeneous channel types and mis-calibrated per type**; the primary is unaffected. (c) **Strictly periodic probing can alias with a closed-loop resonance** on the control tier; declared, monitored, not jittered. (d) **The rank-sum level is not exact** across a dependent window.

**Claims we do not make.** An **engineering baseline derived from IBD**, not a new method and not a contribution of this project. Props. 3.3–3.5 hold for a one-shot two-branch design under a dedicated π_probe and **do not carry over** to a sliding window or a within-randomisation sign contrast; no identifiability, optimality, FDR-control or ARL-optimality claim is made. We do not claim exact rank-sum level. We do not claim exchangeability beyond the randomisation device's construction — and under balanced blocks, not even draft 3's per-unit conditional-history identity (§3 caveat 2). We do not claim fast detection: failure mode 1 says the opposite. We do not claim `p_c` at offset 200 reflects post-event support. We do not claim this is the best sequentialisation of IBD. It estimates `S^obs,ε` only. *(Opinion: the C4-faithful design — probe unit against a zero-action unit — remains the cleaner causal object; the sign contrast is chosen because it is budget-feasible and its validity does not depend on the task policy, the failure that killed draft 2. Second opinion: `n_warm = 25` costs 502 steps of every episode and 12.6 % of the ARL_0 calibration budget; a smaller `n_warm` with an occupancy-corrected reference would be cheaper but reintroduces a window-size-dependent `ā, v`, and I judge that exchange bad.)*

## 9. Gate tests [N]

| ID | Definition |
|---|---|
| **T-IBD-budget** | `used(t) ≤ floor(0.05·t)` after every step of every run. |
| **T-IBD-count** | Exhaustive replay t = 1…2000: granted = {20,…,2000}, 100 applied, 99 closing a unit. |
| **T-IBD-blocks** | Over ≥ 10⁵ windows at K = 2: every (k,sign) group holds 5–7 units, `min(n₊,n₋) ≥ n_min_sign` in **every** window, the guard never binds; block draws reproduce from the RNG seed and are unchanged when the trajectory is perturbed (state-independence). |
| **T-IBD-horizon** | Deterministic impulse on the reference generator at τ ∈ {0,2}: first nonzero increment at **h = τ+1**; §2's index table reproduced. |
| **T-IBD-warmup** | `stat = 0` and `raise = 0` at every epoch with `< n_warm` units; `t_warm = 502 < event_t`; the draft-3 pathology (`stat_warm` = global max) asserted absent; a degenerate epoch holds `stat` and forces `raise = 0`. |
| **T-IBD-arl** | Fresh-start ARL_0 **attains** [900, 1100] at some h, clock starting at `t_warm`, censoring reported (R4-1). |
| **T-IBD-mono** | ARL_0 non-decreasing over an h grid computed from one recorded stream. |
| **T-IBD-hindep** | The raise sequence at a second h reproduces bitwise from that same stream. |
| **T-IBD-window** | Half-open membership on anchor time; exactly 25 units once `t_p* ≥ 500`; hand fixture of grid t ≡ 2 (mod 20). |
| **T-IBD-offsets** | §5's table reproduced from the epoch grid under both boundary conventions, asserting pre/post mixture **and** cell eligibility **separately** (R4-4). |
| **T-IBD-tie** | Tied cell reproduces §4's σ_U² to 1e-12; untied cell reduces to n₊n₋(N+1)/12; a cancellation fixture yielding σ_U² < 0 naïvely returns 0, not `ValueError` (GM-08). |
| **T-IBD-elig** | A cell with `min(n₊,n₋) = 2` contributes nothing and is flagged in the mask; `a_c = 0` from ineligibility and from a degenerate channel are distinguishable in the ledger. |
| **T-IBD-exch** | Sign-group exchangeability on a null channel (an x distractor), family L **and** N: ≥ 3,000 replicates give two-sided \|z\| > 1.96 in [0.03, 0.07], mean z within ±0.1; re-seeding the sign RNG leaves the null AUC inside its Monte Carlo interval. |
| **T-IBD-cal-1** | `g` takes ≥ 2 distinct values on the fit split. |
| **T-IBD-cal-2** | Label floor **in independent units** (R4-15): ≥ 24 fit episodes each contributing ≥ 1 positive and ≥ 1 negative channel-epoch, and ≥ 2 non-overlapping retained windows per episode. Draft 3's "≥ 200 positive/negative channel-epochs" is deleted: it counted dependent duplicates sharing 24 of 25 units. |
| **T-IBD-cal-3** | `g` non-decreasing, clamped into [0.001, 0.999], fitted only on non-straddling epochs, §5's counts (51 / 75 / 1,512) reproduced. |
| **T-IBD-persist** | Shared end-to-end fixture: the estimator returns a raw exceedance; `count_alarms` applies p once, in epochs. |
| **T-IBD-primary** | The evaluator recomputes the primary AUC **solely from `update`'s public `raw_support`**, with **mid-rank** ties; `AUC(g(a)) ≤ AUC(a)` asserted on the fit split. |

Every row needs a `coverage-matrix.md` entry before this spec is implemented (contract gate rule).

## 10. Disposition of round-4 findings [N]

| ID | Sev | Disposition in draft 4 | Where |
|---|---|---|---|
| **R4-1** | critical | **Resolved by design change.** `n_warm = 25`, `stat = 0` on the prefix, ARL_0 clock from `t_warm`, prefix excluded, degenerate-epoch guard. `T-IBD-mono` kept **and** `T-IBD-arl` added for attainment, as R4-1 asked. IB-2 re-closed on the new construction. | §4, §9 |
| **R4-4** | high | **Accepted; prose corrected.** Offset-200 mechanism is **dilution**, not `n_min_sign`; the fraction table was right and is kept; `T-IBD-offsets` separates mixture from eligibility. | §5, §9 |
| **R4-5** | high | **Resolved by D-10.4.** Balanced blocks make whole-actuator deletion impossible (min group 5 at K = 2); eligibility mask, `n_units` and `n_eligible_cells` returned per epoch. `W_steps` unchanged, so the offset-500 property survives. | §3, §6 |
| **R4-8** | high | **Resolved by D-10.5.** P2 offsets moved to {200, 500, 1000}; 200 labelled a transition window with its 0.60 pre-event fraction. | §5 |
| **R4-13** | med | **Accepted.** Row 20's justification replaced (labels near-constant within an episode); per-type mis-calibration declared as a tier-2 limitation with per-type reliability as a diagnostic. | §5, §6, §8 |
| **R4-14** | med | **Accepted.** §4's purity rule now applies to `g`: straddling epochs excluded, post-event retained, counts stated (51 / 75 / 1,512). GM3-4 thereby dispositioned. | §5, §9 |
| **R4-15** | med | **Accepted.** `T-IBD-cal-2` restated in independent units; the dependent-duplicate floor deleted. | §9 |
| **R4-20** | med | **Accepted.** Mid-rank Mann-Whitney (half credit) declared for the primary. The `auc()` reference in `contract_ref.py` and its coverage row are a **contract-side action**, recorded as open. | §5, §11 |
| **R4-23** | low | **Accepted as declared waste.** The terminal probe closes no unit; a grant condition needs `episode_len`, outside the information set. Cost stated; count stays 100 / 99. | §3 |
| **R4-24** | low | **Fixed.** `stat`, `a`, `p_cache`, `elig` initialised at reset and stated in the pseudo-code header, so the every-step return and assertion are always bound. | §7 |
| **R4-25** | low | **Closed by explicit decision.** Jitter **rejected**, with reason; aliasing carried as a declared limitation with a pilot diagnostic. J7's tenth item no longer dropped. | §3, §8 |
| **R4-CX-03** | high | **Resolved upstream.** `update` returns `raw_support[C]` (interface v4); the estimator-written side-channel is deleted; `T-IBD-primary` recomputes AUC from public returns only. | §1, §9 |
| **R4-CX-08** | med | **Resolved.** One clock, with a transition-level index table against contract C and `reference_generator.run`; the epoch grid moves from t ≡ 3 to **t ≡ 2 (mod 20)**; `T-IBD-horizon` added. | §2, §9 |
| **R4-CX-09** | med | **Resolved by D-10.4**, exactly as recommended: pre-randomised balanced blocks retaining state-independence, plus a returned eligibility mask; `T-IBD-blocks` tests the primary-window allocation distribution. | §3, §9 |
| **R4-GM-04** | med | **Accepted as prose.** Family N breaks increment symmetry via a probe-history-dependent operating point; the washout argument is qualified to linear first moments; effect immaterial at registry values; `T-IBD-exch` extended to family N. | §8 |
| **R4-GM-05** | med | **Resolved by a derived rule** rather than `W_steps ≥ 120K`: blocks give `min(n₊,n₋) ≥ floor(n_u/2K) − 1`, hence `W_steps ≥ 8K·Π = 160K`, satisfied at K ≤ 3. | §3, §6 |
| **R4-GM-06** | med | **Resolved** with R4-1: `stat = 0` until occupancy ≥ `n_warm`. | §4 |
| **R4-GM-08** | low | **Fixed.** `σ_U ← sqrt(max(0,σ_U²))` plus a 12-significant-digit tie-rounding rule; `T-IBD-tie` gains a cancellation fixture. | §4, §9 |

**Carried forward, still resolved:** R3-1, R3-11 (i–v), R3-14, R3-15, R3-CX-04, R3-CX-05, R3-CX-10, R3-CX-11, D9-codex-3, GM3-4 (now dispositioned, §5), and draft-1 items IB-1, IB-3, IB-6 to IB-12. IB-2 is re-closed on the new warm-up construction; IB-4 and IB-5 remain obsolete.

## 11. Open, not resolved here

(a) **`auc(scores, labels)` with mid-rank ties has no reference implementation, test ID or coverage-matrix row** in `contract_ref.py`, though it has been the primary since roadmap v4.5 — a contract-side gap this spec can declare but not fill. (b) The **ARL_0 protocol consequence** of the warm-up (400 fresh starts × ≥ 4,000 steps, 12.6 % prefix overhead, ≈ 3 % censoring) is a harness requirement that D-2a does not yet state. (c) **All existing evidence for this arm predates the frozen generator**: the round-4 AUCs (0.86–0.93) came from three different instance families, and **no number in this spec has been reproduced on `reference_generator.py`'s configuration set or perturbation set** — round 5's job and the exit condition for design review. (d) **The alarm channel's attainment of the D-2a band is argued, not measured**: continuity of ARL_0(h) follows from `stat` having a continuous post-warm-up distribution, but the run-length distribution is coarse (≈ 3 non-overlapping windows per 2,000-step episode) and `T-IBD-arl` may still fail — in which case the arm becomes a predeclared D-2a partial-order endpoint and the descriptive HPDT contrast for it is deleted, not repaired.

**References.** Liu, Cheng & Bogdan, arXiv:2603.18257 v2 (§§3.1–3.5, Alg. 1, Eq. 2, Props. 3.3–3.5). Mann & Whitney (1947); Wilcoxon (1945); Lehmann, *Nonparametrics*. Barlow et al. (1972), PAVA. `stage-0a-contract-v3.7.md`; `interface-spec-v4.md`; `executable-proofs/gate/reference_generator.py`; `round4-adjudication-and-tally.md`; `d10-adjudication.md`; `review4-claude-opus/findings.md`; `review4-codex/findings.md`; `review4-gemini/findings.md`; `comparator-spec.md`.
