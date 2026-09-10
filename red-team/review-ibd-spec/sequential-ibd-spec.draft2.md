# Sequential IBD — normative specification (DRAFT 2, informative until signed)

**Status.** Draft 2, 7 September 2026, from `stage-0a-contract-v3.3.md` (§§0, B, C, D, F, G, H, H2), `interface-spec-v3.md`, and the red-team review of draft 1 (`review-ibd-spec/findings.md`, IB-1..IB-12 with a 200-seed simulation). Supersedes draft 1 (kept at `review-ibd-spec/sequential-ibd-spec.draft1.md`). **Informative until Daniel signs.** Written under **D-8a**: the primary outcomes are support correctness (per-channel F1 of p_c against S^obs,ε at offsets {200, 500, 1000}, primary 500) and confounded-channel false support; HPDT is descriptive. **This estimator's job is support estimation; the alarm is secondary.**

**Published IBD, cited correctly.** Liu, Cheng & Bogdan, arXiv:2603.18257 (v1 18 Mar 2026, v2 7 May 2026), read at `arxiv.org/html/2603.18257`. Published IBD is one-shot and static. Alg. 1 collects N = 80 baseline trajectories of T = 200 steps **under a dedicated probe policy π_probe** ("a structured random policy with sinusoidal actions and weak state feedback, requiring no RL training", §3.5) and N intervention trajectories from the same reset distribution in which each action is replaced by an i.i.d. draw from Unif(𝒜) — 2NT = 32,000 steps, once. Eq. 2 is a mean absolute h-step difference over non-overlapping strides; testing is Welch t per (dimension, horizon) over ℋ = {1, 5, 10}, Bonferroni min-p within a dimension, BH across dimensions at α = 0.05; the mask is computed once and reused for the whole downstream run. Props. 3.3–3.5 (randomisation severs C→a; detectability of paths of length ≤ h; Type I/FDR control) are proved for that design; §3.5 assumes a stationary causal structure and the Discussion lists non-stationarity as future work. **Draft 1 attributed a task-policy baseline to the paper; that was wrong (IB-5) and is corrected here.** Everything sequential below is new engineering under contract §H, not a claim about the paper.

---

## 1. Outputs and information set [N]

Online estimator of **action-reachable observation support** S^obs,ε_{t,H} (C3, C6) — not body membership, not R, not M.

- `update(transition) -> (p[C] ∈ [0,1], stat: float, alarm_S ∈ {0,1})`, once per environment step and per probe step, in order (interface v3). p_c is the primary output.
- Information set: **`transitions_only_no_reward_no_oracle; calibrator_injected_via_configure`**. Sees only `Transition = (prev_obs, applied_action, obs, probe_flag, t)`. No reward, terminated/truncated, oracle labels, P = (Assign, gain, avail), latents, event times or types. No controller is trained on probe data (there is none).
- `needs_calibration_split = True`; `statistic_is_monotone_in_alarm = True` (by construction, §5).
- `configure(regime_bundle)` declares **no residual dynamics model**; `model_params` carries only the frozen calibration artefacts of §6, and `model_params_hash` is logged.

## 2. Probing [N]

**Block-periodic, block length L = 1, period Π = L / probe_budget = 20 steps.** One probe step every 20 environment steps; the applied action is an i.i.d. draw from **𝒜 = {±e_k}, magnitude 1.0** (contract §0). The uniform draw is the randomisation that severs C→a (T-E2d; IBD Prop. 3.3).

*Why L = 1, changed from draft 1's L = H = 3.* The review measured that three i.i.d. random-sign probes partially cancel across a block (IB-4: the i = 0, h = 3 contrast collapsed to 0.02), and consecutive within-block anchors give overlapping, strongly dependent increments that a two-sample test cannot count as independent units. At fixed budget the count of **independent** units is what the many-sample statistic consumes, and L = 1 maximises it: 0.05·T units rather than 0.05·T/3.

**Hard budget cap (IB-9).** `reservoir_0 = 0`. A probe is emitted at step t only if `probe_steps_used + 1 ≤ floor(probe_budget · t)` **and** `t − last_probe_t ≥ Π`. Integer arithmetic, not an expectation: the invariant `n_probe ≤ floor(0.05·t)` holds at every step of every run (gate test **T-IBD-budget**); 100 probe steps in a 2,000-step episode. There is no reservoir cap, no burst and no adaptive element — draft 1's burst is deleted because it made the statistic path depend on h (IB-2).

**`request_probe(steps)`** returns an `actions[steps, K]` array only when `steps == 1` and both conditions hold; otherwise **None** (interface v3's declared alternative, not a deviation; IB-11). `preferred_probe_steps = 1` is logged.

**Null construction (IB-4).** For a probe at t_p the matched null anchors are t_n(m) = t_p − 3m, m = 1..4 (M_null = 4, spacing max(ℋ) = 3). Every null increment window [t_n, t_n + h], h ≤ 3, therefore **ends at or before t_p**, and the earliest anchor t_p − 12 starts after the previous probe's influence horizon t_p − Π + τ_max + max(ℋ) = t_p − 15 for τ_max = 2. **T-IBD-null-overlap** asserts both bounds on every emitted unit.

**What the null actually is (IB-5), stated rather than hidden.** It is the **ordinary task-policy continuation** — not π_probe, not a zero-action continuation.

1. It is not what the paper does; no property proved in §3.4 of the paper is inherited.
2. Its **validity** under the shared-cause confounder survived the review's attack: x-channels have no action parent, so the contrast is mean-zero whatever u does, and confounded vs unconfounded distractors got indistinguishable p_c (0.255/0.253; 0.221/0.219).
3. Its **power** depends on the task policy: moving W_u from 0.5 to 0.2 moved the reference contrast on a body channel from 0.088 to 0.165 at h = 1 and from 0.147 to 0.009 at h = 3. Contract H2 fixes only "additive action noise" and a saturation bound. **Normative addition:** the ledger records, per (environment, regime, confounder) cell, the default policy's action RMS and the ratio `probe_magnitude / policy_action_RMS`, measured on the calibration split; cross-environment power comparisons that ignore it are inadmissible.
4. It deviates from C4 (which zeroes a_{t+1..t+h−1}); the contamination by later policy actions is symmetric across the two arms. The detector is therefore **not** an estimator of R and must not be scored as one.
5. A C4-faithful variant (probe unit [a*, 0, 0], null unit [0, 0, 0], six probe steps per unit, Π = 120) is an **appendix arm only**: it leaves four units in a 500-step window, which cannot support the primary. *(Opinion: the C4-faithful variant is the cleaner object and the budget-feasible one is an honest compromise; the appendix arm exists so the gap is measured, not asserted.)*

## 3. Statistic: windowed many-sample two-sample test [N]

Draft 1's per-pair CUSUM is deleted (fix IB-3a).

**Increments.** d_c^h(t) = |o_c(t + h) − o_c(t)| for h ∈ ℋ = {1, 2, 3} — the transition-level analogue of IBD Eq. 2, with strides non-overlapping by construction (§2).

**Window.** A trailing window of **W_steps = 500 environment steps**, defined in steps not pairs (IB-6 ii), holding n_P = 25 probe and n_N = 100 null increments per (channel, horizon). W_steps = 500 is chosen so that at the **primary F1 offset 500 the window is exactly 100 % post-event**. It never resets: the estimator does not know the event time, and resetting on an alarm would reintroduce an h-dependent path.

**Per (channel, horizon).** The tie-corrected Mann–Whitney rank-sum z of probe against null:
z_{c,h} = (U − n_P n_N/2) / sqrt(n_P n_N (n_P + n_N + 1)/12 · κ_tie).
Its null is exact under exchangeability, so **no location or scale reference is estimated online at all** — draft 1's re-estimation machinery and the blind window it implied disappear (IB-7).

**Aggregate over ℋ (IB-1).** Signed max-|z|: h*_c = argmax_h |z_{c,h}| (ties to the smallest h), **a_c = z_{c,h*_c}** clipped to [−z_cap, z_cap], z_cap = 8. Two-sided by construction: a channel losing its response drives a_c down as surely as one gaining it drives a_c up. The |ℋ| Bonferroni factor is absorbed into h (alarm) and into g (probability); **this is not a min-p test and is not called one.** Draft 1's `max_h z_h` had a measured null mean of +0.45..+0.66, which made its CUSUM a positive-drift timer that the confirmatory event *slowed*; it is deleted.

**Degenerate channels.** If all n_P + n_N values are identical (padding, dropped sensor, zero gain), set a_c = **a_absent = −z_cap**: a channel with no variation cannot be shown to respond. A NaN reaching any output is a hard error, never a silent 0 (mirrors E2d).

**Warm-up.** Until n_P ≥ n_min = 10 (≈ 200 steps), stat = 0 and p_c = g(0). The warm-up is inside the run length, not excluded from ARL_0.

**Diagnostics only, outside every scored path.** Two-sided p per channel, Bonferroni min-p over ℋ, BH at q = 0.05 and the hard mask m_c = 1[q_c < 0.05], logged for comparability with IBD §3.2. FDR is kept off the alarm path: it would add a second threshold competing with h.

## 4. p_c: the primary output [N]

**p_c = g(a_c)**, g a **frozen non-decreasing isotonic calibrator** (PAVA) on [−z_cap, z_cap] with endpoint clamping. Emitted **every step** from a cache refreshed at every epoch; **no state ever freezes p_c** (draft 1's blind-window `continue` froze it for 200 steps after each alarm, IB-6 iii).

**Calibration split (IB-6 i), normative.** g is fitted on a declared split that **must contain post-event states**: per (environment, regime, confounder) cell, R_cal = 40 calibration episodes of registry length, **half carrying an event** from the cell's schedule at the registry `event_t`. Training pairs are (a_c(t), 1[c ∈ S^obs,ε_t]) at every epoch of both segments. Gates: **T-IBD-cal-1** g takes ≥ 2 distinct values; **T-IBD-cal-2** both label classes present with ≥ 5 % minority share; **T-IBD-cal-3** g non-decreasing. A cell failing any gate is reported as *calibrator degenerate* with p_c a constant predictor, never repaired by refitting on another split. *(Opinion: draft 1's fault-free-only split is why the review saw p_c ≈ 0.25 on every channel group; this is the single most important fix for P1.)*

**Reporting horizon** is the signed max-|z| rule above; the horizon vector is logged. Draft 1's "Wilcoxon z at the ℋ-argmax horizon" was undefined for a window statistic (IB-6 iv) and is deleted. There is **one null**, the two-sample exchangeability null, so draft 1's mismatch between a median-zero rank null and a μ_ref-centred z (IB-6 v) cannot arise.

**Window memory against offsets (IB-6 ii), reported beside every offset.**

| Offset after event | 10 | 50 | 200 | 500 | 1000 |
|---|---|---|---|---|---|
| Post-event fraction of window | 0.02 | 0.10 | 0.40 | **1.00** | 1.00 |
| Post-event probe units in window | 0–1 | 2 | 10 | 25 | 25 |

Offsets 10 and 50 (co-primary P2) are **pre-event by construction** for this arm and reported as floors with this table; offset 200 (P1) is 60 % pre-event and reported as attenuated; only 500 and 1000 are clean. This is a property of any probe-budgeted windowed estimator, and must not be repaired by shortening W_steps after seeing outcomes.

## 5. Alarm channel: a statistic whose path does not depend on h [N]

Frozen at `calibrate()` from the **pre-event sub-split only**: ā_c = median a_c, v_c = max(1.4826·MAD(a_c), v_floor), v_floor = 0.5.

**stat_t = max_c |a_c(t) − ā_c| / v_c**, recomputed at each epoch and held between epochs. Two-sided by construction, with **no accumulation, reset, burst, online re-estimation or blind window**; `stat` is a deterministic function of the stream and the frozen artefacts alone. Consequences, all of which draft 1 failed (IB-2, IB-7):

- The harness records **one** `stat` stream per calibration episode and evaluates every h offline by replay. **T-IBD-replay**: the alarm sequence at a second h is reproduced exactly from the recorded stream (draft 1 fails this).
- `statistic_is_monotone_in_alarm = True` **by construction**: {alarm by step n} is decreasing in h because the path is h-invariant, so ARL_0(h) is non-decreasing and the harness may bisect. **T-IBD-mono** verifies it numerically rather than arguing it.
- **ARL_0 is the fresh-start run length to first counted alarm** (contract §0, D-6b) — what a single-event 2,000-step episode experiences. The D-2a 2,000,000-step cap is **per cell, not per h**, since one stream serves all h.
- If the run-length CV exceeds 1 and the band [900, 1100] is not attained at ≥ 400 run lengths, the cell goes to the predeclared partial-order endpoint; the band is never met by moving a hidden knob.

**Persistence, in epochs (IB-8).** `raise_run` counts **consecutive epochs** with stat > h; `alarm_S = 1[raise_run ≥ p_epoch]`, p_epoch = 3. Step-unit persistence would be vacuous, since stat is piecewise constant between epochs 20 steps apart. Refractory r = 20 and alarm counting belong to the harness: the estimator emits the raw persisted raise and the harness calls `contract_ref.count_alarms` (no re-implementation). Latency floor ≈ 2Π + max(ℋ) + p_epoch·Π ≈ 100 steps, charged to the descriptive HPDT. *(Opinion: consecutive epochs share 24 of 25 window units, so the raise sequence is strongly autocorrelated and p_epoch filters little — h does essentially all the work. Because `stat` is h- and p-independent, the harness can also report the p_epoch = 1 sequence from the same stream at zero cost, and should.)*

## 6. Calibration interface: two passes inside the frozen API [N]

The estimator never sees oracle labels, yet p_c must be calibrated.

- **Pass 0 (calibration split).** `configure({hash, model_params: None})`; `calibrate(transitions)` computes and stores the a_c trace and fits (ā_c, v_c) on the pre-event sub-split. During pass 0 the estimator emits the declared default map p_c = clip((a_c + z_cap)/(2 z_cap), 0, 1), which is never scored. The **evaluator** pairs the a_c trace with oracle labels at the same t and fits g — the shared isotonic p_c calibrator named in interface v3's deliverables, the same object used for the comparator arms, so the co-primary stays comparable (contract G, OP-13).
- **Pass 1 (scored runs).** `configure({hash, model_params: {g_knots, ā, v}})` — the interface's only privileged input, logged; then `set_threshold(h)`; then the run. `set_threshold` touches nothing but the comparison in §5, so p_c, Brier, log loss and the co-primary are invariant to h and the ARL_0 sweep cannot move the probability metrics.

## 7. Costs [N]

**Probe steps** exactly `floor(0.05·T)`, hard-capped (100 per 2,000-step episode); they also charge task regret where a reward exists. **Operations:** O(C) per ordinary step (emit cached p); per epoch O(C·|ℋ|·(n_P+n_N)·log(n_P+n_N)) ≈ 2.6·10⁵ float ops at C = 100, amortised over Π = 20 to ≈ 1.3·10⁴ ops/step (≈ 1.3·10³ at C = 10). **Memory:** window increments C·|ℋ|·125 = 3.75·10⁴ floats at C = 100, plus a 32-step observation ring (3.2·10³) and O(C) frozen artefacts ≈ 340 kB.

## 8. Parameters [N] (IB-10)

No parameter may change after the pilot without re-running ARL_0 calibration, the isotonic fit and the black-box acceptance suite (E6). **There is no outcome-dependent tuning clause**; draft 1's "if the pilot shows HPDT near H_det, Π must fall" is deleted.

| # | Symbol | Value | Status | Justification |
|---|---|---|---|---|
| 1 | ε, H, ℋ, 𝒜, a_max | 0.05, 3, {1,2,3}, ±e_k @1.0, 2.0 | contract §0 | Normative; not this spec's to choose. |
| 2 | probe_budget | 0.05 | contract §0 | Normative; enforced as a hard cap, not an expectation. |
| 3 | p, r, w_T, H_det | 3, 20, 50, 200 | contract §0 | Normative; p applied in epochs (§5). |
| 4 | episode_len, event_t, offsets_F1 | 2000, 1000, {200,500,1000} | contract §0 (D-6b, D-8a) | Normative; fixes W_steps below. |
| 5 | L | 1 | frozen | Multi-step i.i.d.-sign blocks cancel (IB-4); L = 1 maximises independent units at fixed budget. |
| 6 | Π | 20 | frozen, derived | = L / probe_budget: the unique period spending the budget exactly with reservoir_0 = 0. |
| 7 | reservoir_0 | 0 | frozen | Makes `n_probe ≤ floor(0.05·t)` an invariant, not an average (IB-9). |
| 8 | M_null | 4 | frozen | 4:1 null:probe keeps two-sample variance within 25 % of the infinite-null limit and fits the Π−1 gap. |
| 9 | null spacing | 3 = max(ℋ) | frozen | Smallest spacing giving non-overlapping increment windows. |
| 10 | null guard | τ_max + max(ℋ) = 5 | frozen | Clears both the current and the previous probe (IB-4). |
| 11 | W_steps | 500 | frozen | Makes the window exactly 100 % post-event at the primary offset 500. |
| 12 | z_cap | 8 | frozen | Bounds the calibrator domain and the change statistic; the rank z saturates anyway. |
| 13 | a_absent | −z_cap | frozen | No variation ⇒ no demonstrable response; makes the absent extreme a knot of g, not a NaN. |
| 14 | v_floor | 0.5 | frozen | A z-scale MAD below 0.5 marks a degenerate channel, not a sensitive one. |
| 15 | n_min | 10 | frozen | Minimum probe units for a rank-sum at n_N = 40; below it the statistic is suppressed, not approximated. |
| 16 | p_epoch | 3 | frozen | Contract p in this arm's natural unit (IB-8); the step-unit version is vacuous. |
| 17 | R_cal, event share | 40 episodes, 0.5 | frozen | Guarantees post-event states in the isotonic fit (IB-6). |
| 18 | q (BH) | 0.05 | frozen, diagnostic | IBD §3.2 comparability only; outside every scored path. |
| 19 | **h** | set by harness | **calibrated** | The single scalar knob; fresh-start ARL_0 = 1000 under D-2a. |

**Count: 19 rows — 4 contract blocks, 14 frozen arm parameters, 1 calibrated (h); no swept parameter in the confirmatory configuration.** Three fitted objects are frozen at calibrate: g, ā[C], v[C]. Draft 1's η, B_max, Π_burst, burst_len, k, σ_floor and n_ref are **deleted**, not re-tuned. W_steps ∈ {250, 1000} is an appendix sensitivity with its own re-calibrated h, never substituted for the confirmatory arm.

## 9. Pseudo-code [N]

```
# frozen after calibrate(): g (isotonic, monotone), a_bar[C], v[C]
# contract: HSET = {1,2,3}, PB = 0.05, A = {+-e_k, |a| = 1.0}
# consts:   L=1, PI=20, M_NULL=4, SP=3, W_STEPS=500, Z_CAP=8, N_MIN=10, P_EPOCH=3
# state:    t, used, last_probe_t, ring[32][C], P[|H|], N[|H|] (deques of (t, vec[C])),
#           pending (probe anchors), stat, p_cache[C], raise_run, h

def request_probe(steps):                          # interface v3: actions[steps,K] or None
    if steps != 1: return None                     # declared preferred_probe_steps = 1 (IB-11)
    if used + 1 > floor(PB * t): return None        # hard cap, reservoir_0 = 0        (IB-9)
    if t - last_probe_t < PI: return None           # block-periodic, exact budget
    used += 1; last_probe_t = t; pending.append(t)
    return [ A[randint(2*K)] ]                      # i.i.d. Uniform(A); severs C -> a

def update(tr):                                     # once per env step AND per probe step
    t += 1; ring.push(tr.obs)
    for t_p in pending.due(t - max(HSET)):           # a unit closes max(H) steps after its probe
        for hz in HSET:
            P[hz].append((t_p, abs(ring[t_p+hz] - ring[t_p])))            # 1 probe increment
            for m in 1..M_NULL:                                            # 4 null increments
                t_n = t_p - m*SP                                           # windows end <= t_p
                N[hz].append((t_n, abs(ring[t_n+hz] - ring[t_n])))         #            (IB-4)
        drop(P, N, older_than = t - W_STEPS)         # trailing 500-step window; never reset
        if len(P[1]) < N_MIN: continue               # warm-up: stat 0, p_c = g(0), inside ARL_0
        for c in channels:                           # many-sample two-sample test    (IB-3a)
            zz   = [ mannwhitney_z(P[hz][:,c], N[hz][:,c]) for hz in HSET ]  # tie-corrected
            a[c] = clip(zz[argmax_abs(zz)], -Z_CAP, Z_CAP)                   # signed max|z| (IB-1)
            if all_values_equal(P, N, c): a[c] = -Z_CAP                       # absent extreme
        p_cache = g(a)                               # frozen isotonic; refreshed EVERY epoch
        stat    = max_c(abs(a[c] - a_bar[c]) / v[c]) # frozen ref; no reset/burst  (IB-2, IB-7)
        raise_run = raise_run + 1 if stat > h else 0 # persistence counted in EPOCHS  (IB-8)
    alarm = 1 if raise_run >= P_EPOCH else 0         # refractory r and counting: harness
    assert not isnan(p_cache).any() and not isnan(stat)                       # hard error
    return clip(p_cache, 0, 1), stat, alarm          # (p[C], stat, alarm_S)   interface v3
```

## 10. Failure modes [N]

1. **Low alarm power, acknowledged not hidden.** Twenty-five units of ≤ 0.3 σ each do not give a fast alarm at ARL_0 = 1000 steps. Under D-8a that is charged to the descriptive HPDT; the pilot must report P(alarm within H_det) against a no-event control on the same seeds, and a value at or below the control is reported, not repaired.
2. **Offsets 10, 50, 200 are window-attenuated** (§4 table); reported as floors with their post-event fractions.
3. **Delay τ = 2** removes the probe effect from h ∈ {1, 2} (first hit at h = τ + 1), leaving one usable horizon; those cells are reported separately.
4. **Regime R2 (feedback compensation)** shrinks the probe-vs-policy contrast; the C4-faithful appendix arm (§2.5) measures how much of the loss is closed-loop cancellation.
5. **Calibrator degeneracy** — detected by T-IBD-cal-1/2, reported, never repaired by refitting.
6. **C-dependence of max_c in `stat`:** ARL_0 at fixed h falls as C grows; per-cell calibration absorbs it, but h is not transferable across distractor levels.
7. **Sign-flip blindness** (K8, g′ = −1): |increments| unchanged, correctly invisible since C3 keeps the channel; a mutant must confirm this is intended.
8. **Task-policy dependence of power** (§2.5.3): registered via the action-RMS ratio, not eliminated.

## 11. Disposition of draft-1 findings [N]

| ID | Sev | Disposition in draft 2 | Where |
|---|---|---|---|
| IB-1 | high | **Resolved.** `max_h z_h` deleted; signed max-\|z\| over ℋ; CUSUM and slack k deleted, so no null-drift timer exists. | §3 |
| IB-2 | high | **Resolved.** No reset, burst or online re-estimation; `stat` deterministic in stream + frozen artefacts; one recorded stream calibrates every h (T-IBD-replay); ARL_0 = fresh-start (D-6b); D-2a cap declared per cell. | §5 |
| IB-3 | high | **Addressed by design change, not tuning.** Per-pair CUSUM → windowed many-sample two-sample statistic (fix IB-3a); primary re-aimed to support correctness (D-8a). **Not fully resolved:** the alarm channel's power at these constants stays low, and draft 2 declares it. | §3, §10.1 |
| IB-4 | med | **Resolved.** Null anchors t_p − 3m, m = 1..4; every window ends at or before t_p and clears the previous probe; T-IBD-null-overlap. L = 3 abandoned partly on this evidence. | §2 |
| IB-5 | med | **Partly resolved.** Attribution corrected (the paper's baseline is a dedicated π_probe over both branches). Task-policy dependence **declared and registered** (action-RMS ratio) and a C4-faithful zero-action variant specified as an appendix arm; not removed from the confirmatory arm, which would cost 6× budget per unit. | §2.5, §10.8 |
| IB-6 | med | **Resolved.** Split composition declared and required to contain post-event states, with three gates; horizon rule deterministic; one null; no state freezes p_c; window step-memory tabulated per offset. | §4 |
| IB-7 | med | **Resolved.** Reference frozen at calibration, never re-estimated; the rank-sum's exact null removes any online scale estimate; no blind window; band failure routed to the partial-order endpoint. | §3, §5 |
| IB-8 | med | **Resolved.** Persistence counted in epochs and stated; counting and refractory delegated to `contract_ref.count_alarms`; p_epoch = 1 reported alongside. | §5 |
| IB-9 | low | **Resolved.** reservoir_0 = 0; integer cap rule; invariant tested at every step (T-IBD-budget). | §2 |
| IB-10 | low | **Resolved.** Table renamed "Parameters", 19 rows with status and a one-line reason each; previously unlisted knobs (reservoir_0, tie handling, absent extreme, split composition, warm-up) all appear; tuning clause deleted. | §8 |
| IB-11 | low | **Resolved.** Contract v3.3 is the basis and the stale "v3.2 does not exist" paragraph is gone; `update` returns `(p, stat, alarm)`; `request_probe` returns `steps` actions or None. | header, §1, §2 |
| IB-12 | med | **Accepted as decision D-6b + D-8a.** Episodes stay at 2,000 with the event at 1,000; ARL_0 is the fresh-start run length; the arm is no longer judged primarily on speed, which is what made the contrast a foregone loss. | header, §5 |

## 12. Claims we do not make [N]

An **engineering baseline derived from IBD**, not a new method and not a contribution of this project. No identifiability, optimality, FDR-control or ARL-optimality claim is made in the sequential setting: IBD's Props. 3.3–3.5 are proved for a one-shot two-branch design under a dedicated probe policy and **do not carry over** to a sliding window, a task-policy null, or a change statistic. We do not claim this is the best sequentialisation of IBD, nor that it detects change quickly — §10.1 says the opposite. We do not claim the p_c reported at offsets 10, 50 or 200 reflects the post-event support; §4 says how much of the window is pre-event. We do not claim the null is causally equivalent to C4. It estimates S^obs,ε only — not R, not M, not body membership (C6).

**References.** Liu, Cheng & Bogdan, arXiv:2603.18257, §§3.1–3.5, Alg. 1, Eq. 2, Props. 3.3–3.5, App. C. Mann & Whitney (1947); Wilcoxon (1945). Barlow et al. (1972), isotonic regression / PAVA. Benjamini & Hochberg (1995), FDR (diagnostic use only). `stage-0a-contract-v3.3.md` §§0, B, C, D, F, G, H, H2; `interface-spec-v3.md`; `roadmap-v4.5-amendments.md`; `review-ibd-spec/findings.md` (IB-1..IB-12) and `review-ibd-spec/sim_ibd_review.py`; `confirmation-design.csv`.
