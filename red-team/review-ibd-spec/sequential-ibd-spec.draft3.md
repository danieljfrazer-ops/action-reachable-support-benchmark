# Sequential IBD — normative specification (DRAFT 3, informative until signed)

**Status.** Draft 3, 7 September 2026. Basis: `stage-0a-contract-v3.5.md` §§0, B, C, D, F, G, H, H2; `interface-spec-v3.md`; `d9-adjudication.md`. Supersedes draft 2 (kept at `review-ibd-spec/sequential-ibd-spec.draft2.md`) and draft 1. **Informative until Daniel signs.**

The arm's statistic is replaced. Draft 2's probe-against-task-policy-null contrast is deleted; draft 3 implements the **sign-randomised contrast** defined in contract §H arm 1 and verified by two models in `d9-adjudication.md` (D-9.1). Primary scoring is **threshold-free AUC of the raw per-channel statistic `a_c`** against `S^obs,ε` at `offsets_rank` (primary 500); supervised calibration is a **secondary tier** (contract §G, D-9.5).

**Published IBD, cited honestly.** Liu, Cheng & Bogdan, *Discovering What You Can Control: Interventional Boundary Discovery for RL*, arXiv:2603.18257 (v2), read at `arxiv.org/html/2603.18257v2` on 7 Sep 2026. Verified there: Alg. 1 collects N = 80 baseline and N = 80 intervention trajectories of T = 200 steps, **both branches under a dedicated structured-random probe policy π_probe** ("sinusoidal actions and weak state feedback, requiring no RL training", §3.5), the intervention branch replacing every action with an i.i.d. draw from Unif(𝒜); Eq. 2 is a mean absolute h-step difference; testing is Welch t per (dimension, horizon) over ℋ = {1, 5, 10}, Bonferroni min-p within a dimension, BH across dimensions at α = 0.05; ≈ 32k steps, once, mask reused for the whole downstream run; Prop. 3.3 (randomisation severs C→a), 3.4 (detectability of paths of length ≤ h), 3.5 (Type I / FDR control); §3.1 assumes stationary causal structure and the Discussion lists policy-dependent distractors and indirect effects as future work. **This arm departs from the paper**: there is **no baseline branch and no π_probe**. The contrast is between the estimator's *own* probe signs (+e_k against −e_k), sequentially, inside a task run, at 5 % of steps. Nothing below is a claim about the paper, and none of Props. 3.3–3.5 is inherited (§10).

---

## 1. Information set, outputs, interface [N]

Online estimator of **action-reachable observation support** `S^obs,ε_{t,H}` (C3, C6) — not body membership, not R, not M.

- Information set string: **`transitions_only; no_reward; no_oracle; own_probe_signs_known; calibrator_injected_via_configure`**. Sees `Transition = (prev_obs, applied_action, obs, probe_flag, t)` only. No reward, terminated/truncated, oracle labels, P = (Assign, gain, avail), latents, event times or types. It **knows its own probe signs** because it generated them (`request_probe` returns them); it does not infer them from `applied_action`. No controller is trained on probe data (there is none).
- `configure(regime_bundle)` declares **no residual dynamics model**; `model_params` carries only the frozen artefacts `{g_knots, ā[C], v[C]}` of §5; `model_params_hash` logged.
- `calibrate(transitions)`; `set_threshold(h)`; `needs_calibration_split = True`; `statistic_is_monotone_in_alarm = True`; **`persistence_unit = "epochs"`**; `preferred_probe_steps = 1`.
- `update(transition) -> (p[C] ∈ [0,1], stat: float, raise ∈ {0,1})`, once per environment step. **`raise = 1[stat > h]` with no persistence applied** (contract §G, CX-05).
- `request_probe(steps) -> actions[steps, K] or None`.
- **Ledger addition (normative, unresolved in interface v3 — see §12, Open).** The primary metric is the AUC of the **raw** `a_c`, and `update` returns only `p_c`. Because `g` is non-decreasing but not strictly increasing, `AUC(g(a)) ≤ AUC(a)`, with equality only where `g` is strictly increasing on the observed range. The estimator therefore writes the raw `a[C]` vector to the ledger at every epoch, and the primary is computed on that stream. `interface-spec-v3.md` needs one line for this.

## 2. Probing [N]

**Block-periodic single-step probes, L = 1, Π = 20.** A **probe step is an environment step whose applied action is replaced** (contract §0; R3-14, CX-11) — never an inserted step. The replacement action is an i.i.d. uniform draw over the 2K elements of 𝒜 = {±e_k, magnitude 1.0}: the actuator index k and the sign are drawn together, fair and independent of everything else. The draw is the randomisation that severs C→a (T-E2d; paper Prop. 3.3).

**Clock convention, stated once.** Environment steps are numbered t = 1 … T. Before step t is taken the harness calls `request_probe(1)`; at that moment `update` has consumed t − 1 transitions. The budget is charged against **the step about to be taken**. Grant a probe at step t iff

  `used + 1 ≤ floor(probe_budget · t)`  **and**  `t − t_last ≥ Π`,

with `reservoir_0 = 0`, `used = 0`, `t_last = −Π` at reset. Integer arithmetic, not an expectation. Hard cap: the invariant `used(t) ≤ floor(0.05 · t)` holds after every step of every run (**T-IBD-budget**). No reservoir, no burst, no adaptive element.

**Exact probe count per episode (derivation).** The first grant needs `floor(0.05 t) ≥ 1`, i.e. t ≥ 20; cadence then admits t = 20, 40, …. At t = 20m the budget test is `m ≤ floor(0.05 · 20m) = m`: satisfied with equality. So probes fall on **every multiple of 20**, and for `episode_len` = 2,000 there are **100 applied probe steps** = `floor(0.05 · 2000)`, realised fraction exactly 0.050. The probe at t = 2,000 **closes no unit** (a unit needs observations to t + max(ℋ)), so **99 units** are ever available for the statistic. Codex's independent implementation with completed-step indexing granted 99 probes (`review-d9-codex/findings.md`); the two conventions differ by that one terminal probe and agree on every scored quantity. **T-IBD-count** asserts the applied set, the count 100, and the usable count 99 by exhaustive replay over t = 1…2000.

**No washout, and why (disposes CX-04).** Draft 2 needed a washout guard because its two arms had *different* histories: probe increments followed a probe, null increments followed ordinary policy steps, so a slow mode surviving from an earlier probe entered one arm preferentially. Here **both groups are probe units** and the sign label `S_p ∈ {+, −}` is drawn *after* the history exists and independently of it. The conditional history distribution given `S_p = +` and given `S_p = −` is therefore identical, and a contaminating tail from an earlier probe is equally likely to land in either group. Draft 2's `null guard = τ_max + max(ℋ)` is deleted, along with CX-04's counterexample (`A = 0.95, B = 0.2` leaves 0.140 at lag 7): that residue is now a *shared* nuisance, not an arm asymmetry.

**Residual dependence, stated and not more.** (i) Units are not independent: they share one trajectory, and the |ℋ| increments at one anchor overlap. (ii) A probe's slow-mode tail enters *later* units, so unit p and unit p+1 both depend on `S_p`; the dependence is symmetric in the labels but the rank-sum variance is not the i.i.d. value. (iii) An actuator that reaches c only at lag > max(ℋ) can raise `a_c` above the non-reachable floor — a genuine confusion with the H = 3 estimand (§10.8). Consequences: we do **not** claim exact level for the z (§3), and the primary metric never uses z as a p-value.

## 3. Statistic [N]

**Increment.** For a probe anchored at t_p and h ∈ ℋ = {1,2,3}: `D_c^h(t_p) = o_c(t_p + h) − o_c(t_p)` — **signed**, not absolute (draft 2 used |·|; the sign is the whole point here).

**Window.** Trailing **W_steps = 500 environment steps on anchor time**, half-open: at an epoch whose newest anchor is `t_p*`, the window holds units with `t_p ∈ (t_p* − W_steps, t_p*]`. With Π = 20 that is anchors `t_p* − 20j`, j = 0…24: **exactly 25 units** in steady state. The window **never resets** — the estimator does not know the event time, and resetting would make the statistic path depend on h.

**Epoch timing.** A unit closes at `t = t_p + max(ℋ)`. Epochs therefore occur at t ≡ 3 (mod 20), i.e. t = 23, 43, …, 1983. All outputs are recomputed at an epoch and **held constant between epochs**.

**Per (channel c, horizon h, actuator k).** Let group `+` be the signed increments `D_c^h(t_p)` of window units whose probe used `+e_k`, size n₊; group `−` likewise, size n₋; N = n₊ + n₋. **If min(n₊, n₋) < n_min_sign = 3 the cell contributes zero.** Rank the N values jointly using **mid-ranks** for ties; let R₊ be the rank sum of group `+`.

  U = R₊ − n₊(n₊+1)/2  μ_U = n₊n₋/2

  **σ_U² = (n₊ n₋ / (N(N−1))) · [ (N³ − N)/12 − Σ_g (t_g³ − t_g)/12 ]**

where the sum runs over distinct tied values g with multiplicity t_g (untied values contribute 0). Equivalently σ_U² = (n₊n₋/12)·[(N+1) − Σ_g(t_g³−t_g)/(N(N−1))]. **No continuity correction** (a convention, declared). If σ_U = 0 (all N values identical) the cell contributes zero.

  **z_{c,k,h} = clip( (U − μ_U)/σ_U , −8, +8 )**

**Aggregate.** `a_c = max over usable (k, h) of |z_{c,k,h}|`, and `a_c = 0` if no cell is usable. Range [0, 8]. A channel with no variation (padding, dropped sensor, zero gain) has every cell degenerate, hence `a_c = 0`, the bottom of the range — draft 2's separate `a_absent = −z_cap` knot is deleted. A NaN reaching any output is a hard error, never a silent 0.

**What is exact and what is not (disposes CX-10, D9-codex-3).** Exact **by construction of the coin flip**: `S_p` is an i.i.d. fair Bernoulli drawn from the estimator's own RNG, independent of the state, the task policy, the context `u_t`, the confounder gain G and `ρ_u`. Hence for a *single* fixed unit, under "actuator k does not reach c within h" **and** no residual influence of earlier ±e_k probes on that increment, the increment's conditional law is the same under either label. That is the property draft 2 lacked — its contrast's null depended on `W_u` and `ρ_u` (R3-1). **Not claimed:** exactness of the rank-sum level across the window. The 25 units are dependent (§2), so the normal approximation's variance is not certified. Codex's 3,000-replicate AR(1) attack at ρ = 0.8 and 0.95 found two-sided 1.96 exceedance of 4.4–5.4 % against a nominal 5 % — no material tail inflation, but a bounded empirical check, not a proof (CX-10). The mitigation that matters: the **primary** metric is a threshold-free AUC of the raw `a_c`, invariant to any monotone transform, so it does not depend on the z being calibrated at all.

**Non-zero null floor, declared.** `a_c` is a max of up to 6 |z| values, so its null mean is positive, not zero: the D-9 verification measured non-reachable ≈ 1.44–1.54, reachable-indirect ≈ 1.78–1.87, direct ≈ 2.65–2.69. Discrimination comes from separation, not from a zero null.

## 4. Outputs and window memory [N]

- **`a_c` every step**, piecewise constant between epochs (last epoch value held). Written to the ledger every epoch (§1).
- **`p_c = g(a_c)`** every step, from the cache refreshed at every epoch; **no state ever freezes `p_c`**. `g` is a **single pooled** non-decreasing isotonic (PAVA) map over all channels — not per channel (R3-11 iii) — on domain [0, 8], fitted **by the evaluator** on the **24-episode fit split** (`cal_split`, 12 event-carrying), on pairs `(a_c(t), 1[c ∈ S^obs,ε_t])` at every epoch. Endpoint clamping: `g(x) = g(0)` for x < 0, `g(8)` for x > 8, and the fitted values are clamped into **[0.001, 0.999]** so log loss is finite (R3-11 v). The operating point for secondary F1 is chosen on the **separate 16-episode validation split**; both artefacts frozen before scoring and injected via `configure`. **The primary tier uses neither.**

**Window memory against offsets, recomputed from the epoch grid (disposes R3-15).** `p_c` at offset Δ is read at the last epoch ≤ `event_t + Δ`, i.e. at t ≡ 3 (mod 20); the read lag is ≤ 19 steps. Convention: the event applies before step `event_t` is taken, so a unit anchored at `t_p ≥ event_t` is post-event.

| Offset after event | 10 | 50 | 200 | **500** | 1000 |
|---|---|---|---|---|---|
| Epoch read (event_t = 1000) | 1003 | 1043 | 1183 | 1483 | 1983 |
| Newest anchor in window | 1000 | 1040 | 1180 | 1480 | 1980 |
| Post-event units / 25 | 1 | 3 | 10 | **25** | 25 |
| Post-event fraction | 0.04 | 0.12 | 0.40 | **1.00** | 1.00 |

Draft 2's 0.966 at offset 500 (R3-15) was caused by null anchors reaching 12 steps behind each probe; draft 3 has no null anchors, so the window at offset 500 is entirely post-event. Boundary sensitivity, declared: under the opposite convention (the event applies *after* step 1000) the anchor at 1000 is pre-event and the fractions become 0/25, 2/25, 9/25, 24/25, 25/25 — offset 500 is then 0.96. Offsets 10 and 50 (co-primary P2) are **pre-event by construction** and reported as floors with this table; offset 200 is 60 % pre-event and reported as attenuated. This is a property of any probe-budgeted windowed estimator and must not be repaired by shortening `W_steps` after seeing outcomes. At offset 200 the 10 post-event units split over 4 signed groups average 2.5 — below `n_min_sign` — which is the mechanism of the attenuation.

## 5. Alarm channel: an h-independent statistic [N]

Frozen at `calibrate()`: `ā_c` = median `a_c`, `v_c` = max(1.4826·MAD(a_c), v_floor), v_floor = 0.5, both over the fit split's **pre-event segments**.

**"Pre-event segment", defined exactly (disposes R3-11 ii).** For each of the 24 fit-split episodes, the pre-event segment is the set of **epochs whose window is entirely pre-event and entirely full**: epochs whose newest anchor `t_p*` satisfies `W_steps ≤ t_p* < event_t` in the 12 event-carrying episodes (`t_p* ∈ {500, 520, …, 980}`, 25 epochs each) and `W_steps ≤ t_p* ≤ episode_len` in the 12 event-free episodes (`t_p* ∈ {500, …, 1980}`, 75 epochs each). Total 12·25 + 12·75 = **1,200 epochs per cell**, pooled per channel. The warm-up cut at `t_p* ≥ W_steps` is deliberate: `ā, v` are moments of the full-window statistic only.

**`stat_t = max_c |a_c(t) − ā_c| / v_c`**, recomputed each epoch, held between epochs. Two-sided by construction. **No accumulation, reset, burst, online re-estimation or blind window**: `stat` is a deterministic function of the stream and the frozen artefacts alone. Therefore:

- **h-independence.** The harness records **one** `stat` stream per calibration episode and evaluates every h offline by replay (**T-IBD-hindep**). The D-2a 2,000,000-step cap is per cell, not per h.
- **Monotonicity.** `{alarm by step n}` is decreasing in h because the path is h-invariant, so ARL_0(h) is non-decreasing and the harness may bisect (**T-IBD-mono** verifies numerically).
- **ARL_0** is the fresh-start run length to first counted alarm (contract §0, D-6b). The warm-up (`a_c = 0` until some cell is usable, in expectation ≈ 12–20 probes, t ≈ 240–400) is inside the run length, not excluded.

**Persistence ownership (disposes CX-05).** The estimator returns the **raw** exceedance. `persistence_unit = "epochs"` is declared, so the harness applies `p = 3` as three consecutive **epochs** and `r = 20` steps (= one epoch) through `contract_ref.count_alarms`, once. Persistence is never applied inside the estimator. *(Opinion: consecutive epochs share 24 of 25 units, so the raise sequence is strongly autocorrelated and p filters little; h does essentially all the work. Because `stat` is h- and p-independent, the harness can and should report the p = 1 epoch sequence from the same stream at zero cost — `p_epoch_1_alarm_times` is in the interface v3 ledger row.)*

## 6. Calibration passes [N]

**Pass 0 (calibration split).** `configure({hash, model_params: None})`; `calibrate(transitions)` computes the `a_c` trace and fits `(ā, v)` on the pre-event segments above. During pass 0 the estimator emits the default map `p_c = a_c / 8` clipped to [0,1]; it is never scored. The **evaluator** pairs the logged `a_c` trace with oracle labels at the same t and fits `g` on the 24-episode fit split, then selects the operating point on the 16-episode validation split.

**Pass 1 (scored runs).** `configure({hash, model_params: {g_knots, ā, v}})`; `set_threshold(h)`; run. `set_threshold` touches nothing but the comparison in §5, so `a_c`, `p_c`, the primary AUC and the co-primary are invariant to h and to the ARL_0 sweep.

## 7. Costs [N]

**Probe steps** exactly `floor(0.05·T)` = 100 per 2,000-step episode, hard-capped; they also charge task regret where a reward exists. **Operations:** O(C) per ordinary step (emit the cache); per epoch O(C·|ℋ|·K·N log N) with N ≈ 12.5, ≈ 3·10⁴ float ops at C = 100, amortised over Π = 20 to ≈ 1.5·10³ ops/step (≈ 1.5·10² at C = 10). **Memory:** 25 units × |ℋ| × C increments = 7.5·10³ floats at C = 100, plus 25 (t_p, k, sign) triples, a 4-vector observation ring, and O(C) frozen artefacts — under 100 kB. **Samples:** no additional environment access beyond the probe steps.

## 8. Parameters [N]

No parameter may change after the pilot without re-running ARL_0 calibration, the isotonic fit and the black-box acceptance suite (E6). **There is no outcome-dependent tuning clause.**

**Inherited from contract §0, not this spec's to choose (17):** ε, H, ℋ, 𝒜, a_max, probe_budget, p, r, w_T, H_det, ARL_0, episode_len, event_t, offsets_rank, n_min_sign, cal_split, τ.

**Arm parameters — one per row (21):**

| # | Symbol / choice | Value | Status | One-line justification |
|---|---|---|---|---|
| 1 | L (probe block length) | 1 | frozen | Maximises independent units at fixed budget; multi-step i.i.d.-sign blocks partially cancel. |
| 2 | Π (cadence) | 20 | frozen, derived | = L / probe_budget: the unique period spending the budget exactly with reservoir_0 = 0. |
| 3 | reservoir_0 | 0 | frozen | Makes `used ≤ floor(0.05·t)` an invariant, not an average. |
| 4 | Clock convention | charge the step about to be taken | frozen | Gives exactly `floor(0.05·T)` probes and an unambiguous `probe(actions)` cost (R3-14, CX-11). |
| 5 | Probe draw | i.i.d. Unif over 2K elements of 𝒜 | frozen | Fair coin on the sign is the whole validity argument (§3). |
| 6 | W_steps | 500 | frozen | Makes the window 100 % post-event at the primary offset 500 (§4). |
| 7 | Window endpoint rule | half-open on anchor time, (t_p*−W, t_p*] | frozen | Gives exactly 25 units; removes the (t−W, t] / [t−W, t) ambiguity (R3-11 iv). |
| 8 | Epoch trigger | t = t_p + max(ℋ) | frozen | Earliest time a unit is complete; fixes the epoch grid t ≡ 3 (mod 20). |
| 9 | Increment sign | signed | frozen | Absolute increments discard the contrast the sign randomisation creates. |
| 10 | Tie correction | mid-ranks, formula in §3 | frozen | One of two conventions in circulation; declared to remove R3-11 i. |
| 11 | Continuity correction | none | frozen | Declared convention; immaterial to a rank-preserving primary. |
| 12 | z_cap | 8 | frozen | Bounds the calibrator domain and `stat`; the rank z saturates near this anyway. |
| 13 | Aggregation | max over (k,h) of \|z\| | frozen | Contract §H; two-sided per cell; the \|ℋ\|·K multiplicity is absorbed into h and g. |
| 14 | a_c when no cell usable | 0 | frozen | No variation ⇒ no demonstrable response; the bottom knot of g, not a NaN. |
| 15 | g | single pooled isotonic (PAVA) over channels | frozen | Per-channel fits would need per-channel labels the estimator never sees (R3-11 iii). |
| 16 | g clamp | [0.001, 0.999] | frozen | Keeps log loss finite at the endpoints (R3-11 v). |
| 17 | ā_c | median over pre-event segment | frozen | Robust centre; MAD's natural partner. |
| 18 | v_c | max(1.4826·MAD, v_floor) | frozen | Robust scale on a heavy-tailed max statistic. |
| 19 | v_floor | 0.5 | frozen | A z-scale MAD below 0.5 marks a degenerate channel, not a sensitive one. |
| 20 | Pre-event segment | epochs with W_steps ≤ t_p* < event_t (or ≤ episode_len if event-free) | frozen | Full windows only, and no post-event leakage into the alarm reference (R3-11 ii). |
| 21 | **h** | set by harness | **calibrated** | The single scalar knob; fresh-start ARL_0 = 1000 under D-2a. |

**Honest count: 21 arm parameters on 21 rows — 20 frozen, 1 calibrated (h); no swept parameter in the confirmatory configuration.** Plus 17 inherited contract constants (listed above, not re-counted as this spec's choices) and 3 fitted objects frozen at `calibrate`: `g`, `ā[C]`, `v[C]`. Draft 2's M_null, null spacing, null guard, n_min = 10, a_absent, p_epoch, R_cal, q(BH) and the signed-max rule are **deleted**, not re-tuned. `W_steps ∈ {250, 1000}` is an appendix sensitivity with its own re-calibrated h, never substituted for the confirmatory arm.

## 9. Pseudo-code [N]

```
# frozen after calibrate(): g (pooled isotonic), a_bar[C], v[C]
# contract: HSET={1,2,3}, PB=0.05, A={+-e_k, |a|=1.0}, N_MIN_SIGN=3
# consts:   PI=20, W_STEPS=500, Z_CAP=8, V_FLOOR=0.5
# state:    t, used, t_last, ring[4][C], units (deque of (t_p,k,sign,D[|H|][C])),
#           pending, a[C], stat, p_cache[C], h, rng (estimator-owned)

def request_probe(steps):                       # interface v3: actions[steps,K] or None
    if steps != 1: return None                  # preferred_probe_steps = 1
    tt = t + 1                                  # the step about to be taken
    if used + 1 > floor(PB * tt): return None   # hard cap, reservoir_0 = 0
    if tt - t_last < PI:        return None     # block-periodic
    k, sgn = rng.choice(K), rng.choice([+1,-1]) # i.i.d. fair; severs C -> a
    used += 1; t_last = tt; pending.append((tt, k, sgn))
    return [ sgn * e[k] ]                       # magnitude 1.0

def update(tr):                                 # once per environment step
    t += 1; ring.push(tr.obs)
    for (t_p, k, sgn) in pending.due(t - max(HSET)):        # unit closes at t_p+max(H)
        D = [ ring[t_p+hz] - ring[t_p] for hz in HSET ]     # SIGNED increments
        units.append((t_p, k, sgn, D))
        units.drop_while(lambda u: u.t_p <= t_p - W_STEPS)  # half-open on anchor time
        for c in channels:
            zz = []
            for k2 in range(K):
              for i, hz in enumerate(HSET):
                Gp = [u.D[i][c] for u in units if u.k==k2 and u.sgn>0]
                Gm = [u.D[i][c] for u in units if u.k==k2 and u.sgn<0]
                if min(len(Gp), len(Gm)) < N_MIN_SIGN: continue      # cell contributes 0
                zz.append(clip(ranksum_z_tiecorrected(Gp, Gm), -Z_CAP, Z_CAP))
            a[c] = max([abs(z) for z in zz], default=0.0)            # 0 if no usable cell
        p_cache = g(a)                          # frozen pooled isotonic, EVERY epoch
        stat    = max_c(abs(a[c] - a_bar[c]) / v[c])                 # frozen ref only
        log_ledger_epoch(t, a)                  # raw a_c is the primary-scored stream
    assert not isnan(p_cache).any() and not isnan(stat)              # hard error
    return clip(p_cache, 0, 1), stat, int(stat > h)   # RAW raise; harness owns p and r
```

## 10. Failure modes and claims we do not make [N]

**Failure modes.** (1) **Low alarm power at ARL_0 = 1000, declared not hidden.** 25 units give ≈ 6 per sign group; a complete actuator loss moves `a_c` on affected channels by ≈ 1 z-unit, against a `max_c` over 24–114 channels. The pilot must report P(alarm within H_det) against a no-event control on the same seeds; a value at or below the control is reported, not repaired. The arm is scored on support ranking; HPDT is descriptive. (2) **Offsets 10, 50, 200 window-attenuated** (§4 table), reported as floors with their fractions. (3) **τ = 2 leaves one usable horizon** (first hit at h = τ + 1 = 3), so `a_c` is a max over K cells rather than K·|ℋ|; those cells are reported separately and their h is not transferable. (4) **Multi-event schedules (ABA, ABC, Poisson, bursty) are exploratory**: the window never resets, so a second event within `W_steps` of the first is read through a mixed window; no reset is added, because a reset would reintroduce h-dependence in `stat`. (5) **Calibrator degeneracy** — detected by T-IBD-cal-*, reported, never repaired by refitting elsewhere. (6) **C-dependence of `max_c` in `stat`:** ARL_0 at fixed h falls as C grows; per-cell calibration absorbs it, but h is not transferable across distractor levels. (7) **Sign-flip blindness** (K8, g′ = −1): both groups' increments flip, so U → n₊n₋ − U and |z| is unchanged — correctly invisible, since C3 keeps the channel. (8) **Long-lag confusion:** an actuator reaching c only at lag > max(ℋ) can lift `a_c` above the non-reachable floor through the residual dependence of §2; this is a genuine false positive against the H = 3 estimand and is reported, not suppressed. (9) **Power (not validity) depends on the task policy** through `probe_magnitude / policy_action_RMS`; the ledger records it per cell and cross-environment power comparisons that ignore it are inadmissible.

**Claims we do not make.** An **engineering baseline derived from IBD**, not a new method and not a contribution of this project. Props. 3.3–3.5 are proved for a one-shot two-branch design under a dedicated π_probe and **do not carry over** to a sliding window or to a within-randomisation sign contrast; no identifiability, optimality, FDR-control or ARL-optimality claim is made. We do not claim the rank-sum null is exact across the window (§3). We do not claim exchangeability beyond the coin flip's construction. We do not claim fast detection — §10.1 says the opposite. We do not claim the `p_c` at offsets 10, 50, 200 reflects post-event support. We do not claim this is the best sequentialisation of IBD. It estimates `S^obs,ε` only — not R, not M, not body membership (C6). *(Opinion: the C4-faithful design — probe unit against a zero-action unit — remains the cleaner causal object; the sign contrast is chosen because it is budget-feasible and its validity does not depend on the task policy, which is the failure that killed draft 2.)*

## 11. Gate tests [N]

| ID | One-line definition |
|---|---|
| **T-IBD-budget** | `used(t) ≤ floor(0.05·t)` asserted after every step of every run; realised fraction ≤ 0.05. |
| **T-IBD-count** | Exhaustive replay over t = 1…2000: granted set = {20, 40, …, 2000}, 100 applied, 99 closing a unit. |
| **T-IBD-window** | Window membership is half-open on anchor time; exactly 25 units once t_p* ≥ 500; hand fixture of the epoch grid t ≡ 3 (mod 20). |
| **T-IBD-offsets** | The §4 post-event-fraction table is reproduced from the epoch grid, both boundary conventions. |
| **T-IBD-tie** | Hand fixture: a cell with ties reproduces the §3 σ_U² to 1e-12; a cell with no ties reduces to n₊n₋(N+1)/12. |
| **T-IBD-nmin** | A cell with min(n₊,n₋) = 2 contributes zero; `a_c = 0` when no cell is usable and when all values are identical. |
| **T-IBD-hindep** | Replay: the raise sequence at a second h is reproduced bitwise from one recorded `stat` stream. |
| **T-IBD-mono** | Fresh-start ARL_0 is non-decreasing over an h grid computed from that single stream. |
| **T-IBD-exch** | Sign-group exchangeability on a null channel: on an x distractor (no action parent), ≥ 3,000 replicates give two-sided \|z\| > 1.96 in [0.03, 0.07] and mean z within ±0.1; re-seeding the estimator's sign RNG leaves the null AUC within its Monte Carlo interval. |
| **T-IBD-cal-1** | Non-degeneracy: `g` takes ≥ 2 distinct values on the fit split. |
| **T-IBD-cal-2** | Absolute label floor: ≥ 200 positive and ≥ 200 negative channel-epochs in the fit split (replaces draft 2's 5 % minority-share gate, which CX-01 showed fails deterministically at N_x = 100). |
| **T-IBD-cal-3** | `g` non-decreasing and clamped into [0.001, 0.999]. |
| **T-IBD-persist** | End-to-end alarm-time fixture shared by estimator, interface and harness: the estimator returns a raw exceedance and `count_alarms` applies p once, in epochs. |
| **T-IBD-primary** | The ledger's raw `a_c` stream reproduces the primary AUC; `AUC(g(a)) ≤ AUC(a)` asserted on the fit split. |

## 12. Disposition of carried-forward findings [N]

| ID | Source | Severity | Disposition in draft 3 | Where |
|---|---|---|---|---|
| **R3-1** | review3-claude-opus | high | **Resolved by design change.** The task-policy null is deleted; the statistic is the sign-randomised contrast, whose validity does not depend on W_u, ρ_u or G. Verified by two models (D-9.1): AUC 0.750/0.826 (Opus), 0.770/0.818 (Codex), 0.813/0.732 (Gemini) at offsets 500/1000. Codex's caveat recorded: draft 2's inversion is instance-dependent, so the claim about draft 2 is "weak or non-monotone ranking on admissible instances", not a universal negative sign. | §3, §10 |
| **R3-11** | review3-claude-opus | med | **Resolved, five parts.** (i) κ_tie replaced by an explicit σ_U² formula. (ii) "Pre-event segment" defined exactly, with counts. (iii) `g` stated to be a single **pooled** map over channels. (iv) Window declared half-open on **anchor** time, and the 25-unit count derived rather than asserted. (v) Clamp values given ([0.001, 0.999]). Count relabelled honestly: 21 arm parameters on 21 rows plus 17 inherited constants. | §3, §4, §5, §8 |
| **R3-14** | review3-claude-opus | low | **Resolved.** Contract v3.5 §0 now defines a probe step as an environment step whose action is replaced; this spec says it once, and `update` is called once per **environment** step (draft 2's "and per probe step" is deleted). | §1, §2 |
| **R3-15** | review3-claude-opus | low | **Resolved and superseded.** The table is recomputed from the epoch grid (0.04 / 0.12 / 0.40 / 1.00 / 1.00). The residual four-unit contamination at offset 500 came from draft 2's null anchors, which no longer exist; the boundary-convention sensitivity (1.00 vs 0.96) is declared instead of asserting "exactly". | §4 |
| **R3-CX-04** | review3-codex | high | **Resolved by removing the asymmetry, not by a washout.** Both groups are probe units drawn after the history, so a slow-mode residue (CX-04's 0.2·0.95⁷ = 0.140) enters both equally. Draft 2's `null guard = τ_max + max(ℋ)` and the false equation of H with physical washout are deleted. The residual dependence and the long-lag false positive are declared, not claimed away. | §2, §10.8 |
| **R3-CX-05** | review3-codex | high | **Resolved.** The estimator returns the **raw** exceedance; `persistence_unit = "epochs"` is declared; the harness applies p = 3 (epochs) and r once via `count_alarms`. No double application, no undocumented exemption. T-IBD-persist is the shared end-to-end fixture CX-05 asked for. | §1, §5, §11 |
| **R3-CX-10** | review3-codex | med | **Resolved as a prose/validity fix.** "Exact" is removed. What holds is stated precisely (the coin flip's construction, per unit) and no more; the window-level dependence is named; CX-10's own AR(1) attack result (4.4–5.4 % at nominal 5 %) is cited as a bounded check, not a proof. The primary metric never uses z as a p-value. | §3 |
| **R3-CX-11** | review3-codex | med | **Resolved.** One clock convention is frozen and stated once; probing **replaces** a task action; `used` is charged against the step about to be taken. The exact count is derived (100 applied, 99 usable) and reconciled with Codex's 99 under completed-step indexing. T-IBD-count is the exhaustive t = 0…2000 test. | §2, §11 |
| **D9-codex-3** | review-d9-codex | med | **Resolved, all six items.** `n_min_sign = 3` per sign group with zero contribution below it; zero/absent behaviour (`a_c = 0`); tie correction by formula; z cap ±8; window endpoints half-open on anchor time; epoch timing at t_p + max(ℋ). Hand fixtures: T-IBD-tie, T-IBD-nmin, T-IBD-window. | §3, §11 |

**Carried forward from draft 1 (`review-ibd-spec/findings.md`), still resolved:** IB-1 (no `max_h z_h`), IB-2 (no reset/burst/re-estimation; fresh-start ARL_0), IB-3 (windowed many-sample statistic; alarm power declared low), IB-6 (split composition, one null, nothing freezes `p_c`, window memory tabulated), IB-7 (reference frozen at calibration), IB-8 (persistence in epochs, now harness-applied), IB-9 (reservoir_0 = 0, invariant tested), IB-10 (honest parameter table, no tuning clause), IB-11 (interface signatures), IB-12 (D-6b). IB-4 and IB-5 are **obsolete**: they concerned the null construction, which no longer exists.

**Open, not resolved here.** (a) `interface-spec-v3.md` has no field for the raw `a_c` stream on which the primary AUC is computed; §1 declares a ledger addition that needs a one-line interface amendment. (b) The D-9.1 evidence is family L, τ = 0, N_x ∈ {10, 30}, one instance draw per model; family N, τ = 2, N_x = 100 and leave-one-instance-out replication are untested, and Codex's stated confidence-raiser — a multi-instance estimate of the fraction of admissible draws clearing the margin — has not been run. (c) `comparator-spec.md` (D-9.4) does not yet exist, so the headline contrast is not yet reproducible end to end.

**References.** Liu, Cheng & Bogdan, arXiv:2603.18257 v2, §§3.1–3.5, Alg. 1, Eq. 2, Props. 3.3–3.5. Mann & Whitney (1947); Wilcoxon (1945); Lehmann, *Nonparametrics* (tie-corrected rank-sum variance). Barlow et al. (1972), isotonic regression / PAVA. `stage-0a-contract-v3.5.md` §§0, B, C, D, F, G, H, H2; `interface-spec-v3.md`; `d9-adjudication.md`; `review3-claude-opus/findings.md`; `review3-codex/findings.md`; `review-d9-codex/findings.md`; `review-ibd-spec/findings.md`; `confirmation-design.csv`.
