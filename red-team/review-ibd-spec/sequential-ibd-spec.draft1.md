# Sequential IBD — normative specification (DRAFT, informative until signed)

**Status.** Draft 1, 6 September 2026, under roadmap v4.3 §G4 (decision D-4a). **Informative until Daniel signs**; the confirmatory pair is not frozen until then. Next per D-4a: a second fresh-context agent red-teams this with executable checks.

**Source-document defect (resolve before signing).** The brief cites `stage-0a-contract-v3.2.md` §§0, C, D, F, G, H, H2. **That file does not exist here.** The latest present is `stage-0a-contract-v3.1.md`, which has no §H2. I therefore treat the normative contract as v3.1 **as amended by** `roadmap-v4.1/4.2/4.3-amendments.md` — which is what v3.2 was to consolidate (§0 gains the D-2a calibration rule; §H gains the H2 control tier and the `R0_inband_linear` comparator). Constants are from v3.1 §0, cross-checked against `confirmation-design.csv`. If v3.2 differs, re-derive.

**Published-IBD baseline.** Liu, Cheng & Bogdan, *Discovering What You Can Control: Interventional Boundary Discovery for RL*, arXiv:2603.18257 (retrieved 6 Sep 2026, `arxiv.org/html/2603.18257`). Published IBD is **one-shot and static**: §3.2 / Alg. 1 run N=80 trajectories × T=200 steps per branch (~32k env steps), intervention branch replaces each action by an i.i.d. draw from Unif(𝒜); per-dimension summary Δ^h_i(τ) = (1/K_h) Σ_r |o^(i)_{(r+1)h} − o^(i)_{rh}| (Eq. 2); Welch t-test per (dimension, horizon) over ℋ={1,5,10}; Bonferroni min-p within a dimension; Benjamini–Hochberg across dimensions at α=0.05; mask m_i = 1[q_i < α], "computed once and reused for the entire downstream training run" (§3.5). §3.1 assumes stationary causal structure; the Discussion lists non-stationarity as future work. **Everything sequential below is new engineering, per contract §H.**

---

## 1. Purpose and outputs [N]

- Online estimator of the **action-reachable observation support** S^obs,ε_{t,H} (contract C3, C6). It is *not* an estimator of body membership.
- Emits every step, via `update(transition)`: **p ∈ [0,1]^C** (p_c = P(c ∈ S^obs,ε)) and **α^S_t ∈ {0,1}** (contract F, interface v3).
- Spends randomised probe actions within `probe_budget` = **0.05** probe steps / total steps (contract §0), enforced by a token reservoir (§2) so the fraction is never exceeded, not merely met in expectation.
- Exposes **exactly one** scalar alarm threshold **h**, set by `set_threshold(h)`; the harness calibrates it to ARL_0 = 1000 steps under the D-2a rule (≥ 400 false-alarm run lengths, 95% CI inside [900, 1100], calibrated once per (environment, regime, confounder, estimator) cell and shared across seeds; a method outside the band stays in the primary under the partial-order endpoint).

## 2. Probe scheduling [N]

- **Block-periodic, deterministic, reservoir-gated**, not Bernoulli-per-step: the budget is exactly auditable, probe/null pairing is exact, and one nuisance random variable is removed from ARL_0 calibration. *(Opinion: cost is a periodic alias in the refresh clock, absorbed by per-cell calibration.)*
- **Block length L = H = 3.** Every step of a block applies a probe action drawn i.i.d. **uniformly from 𝒜 = {±e_k : k=1..K}, magnitude 1.0** (contract §0 probe set; uniform draw is the randomisation that severs C→a, contract T-E2d and IBD Prop. 3.3).
- **Normal cadence** Π = ceil(L / (η · probe_budget)) with η = 0.8 → **Π = 75 steps** (provisional). Steady-state spend 3/75 = 0.04, i.e. 80% of accrual; the remaining 20% fills the reservoir.
- **Reservoir.** Accrue `probe_budget` tokens per environment step; spend 1 token per probe step; cap **B_max = 30** tokens (provisional). A block is emitted only if reservoir ≥ L. This is a hard cap: the realised probe fraction is ≤ 0.05 on every run.
- **Burst re-probing after an alarm.** On α^S = 1, cadence switches to **Π_burst = 6** until either the reservoir falls below L or 100 steps have elapsed, then reverts to Π. This is the only adaptive element of the schedule.
- **Matched nulls are free.** Following IBD §3.2, the baseline branch is the **ordinary policy roll-out**, not a zero-action override. The null block for a probe block starting at t_b is the L steps **immediately preceding** it, [t_b−L, t_b−1], which carry `probe_flag=False`. Locality is the point: it makes the contrast insensitive to slow drift in u, w and x. Pair i ∈ {0..L−1} is (probe start t_b+i, null start t_b−L+i) → **L = 3 pairs per block**.
- **Deviation from contract C4, stated:** C4's open-loop response zeroes actions at t+1..t+h−1. This detector does not, on either arm; the contamination by subsequent policy actions is symmetric across the pair. The detector is therefore *not* an estimator of R and must not be scored as one.

## 3. Per-channel statistic and p_c [N]

- For each pair i, channel c, horizon **h ∈ ℋ = {1,2,3}** (contract §0), form the absolute h-step increment (transition-level analogue of IBD Eq. 2): d_c^h(t) = |o_c(t+h) − o_c(t)|, and the **paired difference** δ_c^h(i) = d_c^h(probe_i) − d_c^h(null_i).
- **Two time-scales, one threshold** (the central design choice). One sliding window cannot serve both outputs: the alarm must move on the first post-change pair, while p_c needs smoothing.
  - **Reference (slow, frozen):** location μ_c^h and scale σ_c^h (median and 1.4826·MAD) of δ_c^h, estimated over the calibration split and re-estimated over the **n_ref = 200** steps after each alarm; **frozen between re-estimations**. During re-estimation the CUSUM is held at 0 and no alarm can be raised.
  - **Detection (fast):** at each pair, z_c = max_{h∈ℋ} (δ_c^h(i) − μ_c^h) / max(σ_c^h, σ_floor), σ_floor = 0.1 (frozen). Max over ℋ is the IBD Bonferroni min-p rule (§3.2) transposed to a z-scale; the |ℋ| factor is a constant absorbed by h.
  - **Reporting (windowed):** a sliding window of the last **W = 16 pairs** (provisional; swept over {8,16,32}). Raw score s_c = Wilcoxon signed-rank z of {δ_c^h(i)}_{i∈W} at the ℋ-argmax horizon. Rank-based rather than IBD's Welch t because W is small and family N clipping/saturation gives heavy tails *(opinion; the red-team should test Welch t as the alternative)*.
  - **p_c = g(s_c)**, where **g is a frozen isotonic calibrator** fitted in `calibrate()` on the calibration split against oracle S^obs,ε labels, exactly as required by roadmap v4.2 §F8. g is **never refitted online** and does not depend on h.
- **Zero-variance and NaN discipline.** Pairs with δ = 0 are dropped from the rank statistic. If all W pairs are zero (padding channels, dropped sensors), s_c is set to the *absent* extreme, not NaN; a NaN reaching the alarm path is a **hard error**, never a silent 0 (mirrors contract E2d).
- **FDR is removed from the alarm path.** Retaining BH would introduce a second threshold (α) competing with h and would break the single-knob requirement. BH at q = 0.05 across the C channels, and the hard mask m_c = 1[q_c < 0.05], are **computed and logged as a diagnostic only**, for comparability with published IBD §3.2. This is a deliberate deviation from the published method.

## 4. Change detection [N]

- **Refresh epochs.** The CUSUM advances **once per completed pair** (3 per block), never per step (a constant z would accumulate deterministically); p_c is emitted every step from cache and is piecewise constant between epochs.
- **Two-sided per-channel CUSUM** (Page, 1954) with slack **k = 0.5** (frozen): G_c^± ← max(0, G_c^± ± z_c − k) at each epoch.
- **Aggregate:** S = max_c max(G_c^+, G_c^−). Max, not sum: a single channel entering or leaving S^obs,ε must raise the score, and a sum makes the statistic scale with C.
- **Two-sidedness is required, not optional.** Sensor dropout, gain→0 and complete actuator loss *shrink* S^obs,ε and produce δ ↓; a one-sided IBD-style test sees nothing. A gain sign flip (contract K8, g′ = −1) leaves |δ| unchanged and is correctly invisible, since C3 keeps the channel.
- **Alarm bookkeeping (contract §0, G):** raw raise when S > h; **α^S = 1** at the first step on which the raw raise has held for **p = 3** consecutive steps; then suppressed for **r = 20** steps. On α^S: reset G ≡ 0, trigger burst re-probing (§2), and re-estimate (μ, σ) over n_ref steps.
- **Monotonicity (why `set_threshold` works).** {alarm by step n} is a decreasing set in h, because S(·) does not depend on h and the event is a superlevel crossing sustained for p steps. Hence the run length T(h) is stochastically increasing and **ARL_0(h) = E[T(h)] is non-decreasing**, strictly increasing wherever S has continuous support. The harness may bisect on h.

## 5. Costs [N]

- **Probe steps:** ≤ 0.05·T, hard-capped by the reservoir; realised count logged in the ledger.
- **Operations:** O(C) per ordinary step (emit cached p). Per refresh epoch: O(C·|ℋ|) for z, O(C) for the CUSUM, O(C·|ℋ|·W) for the windowed rank score in the reference implementation (O(C·|ℋ|·log W) with order-statistic deques). Amortised per step ≈ O(C·(1 + |ℋ|·W·L/Π)) ≈ O(C) at the stated defaults.
- **Memory:** O(C·|ℋ|·W) paired differences + O(C·|ℋ|) reference stats + O(C) CUSUM + O(C·(H+L)) observation ring buffer. At C = 100, |ℋ| = 3, W = 16: ~5k floats.

## 6. Information set [N]

- Declared string: **`transitions_only_no_reward_no_oracle`**. Sees only `Transition = (prev_obs, applied_action, obs, probe_flag, t)` (interface v3). No reward, no `terminated`/`truncated`, no oracle labels, no P = (Assign, gain, avail), no latent coordinates, no event times, no event types.
- `configure(regime_bundle)`: sequential IBD declares **no residual model**; it logs `model_params_hash` and **ignores `model_params`**. It is model-free by construction, which is the whole point of the R0/R1/R2 regime contrast.
- `needs_calibration_split = True` (isotonic g, reference (μ, σ), and h all come from it).

## 7. Calibration interface [N]

- `calibrate(transitions)`: fits and **freezes** g, μ_c^h, σ_c^h. Emits nothing.
- `set_threshold(h)`: sets **only** the CUSUM alarm level h in §4. It does not touch g, so p_c, the Brier/log-loss and the co-primary are invariant to h — the ARL_0 sweep cannot move the probability metrics.
- **Feasibility warning (dominant risk, must be checked in the pilot).** At Π = 75 and 3 pairs per block, 1000 steps contain only ≈ 40 refresh epochs. ARL_0 = 1000 **steps** is therefore an ARL of ≈ 40 **epochs** — a very short-memory regime for a CUSUM, implying a small h and limited power. Recommendation: the ledger should record ARL_0 in both units, and the pilot should report whether the D-2a band [900, 1100] steps is attainable at all; if not, the partial-order endpoint applies.

## 8. Free parameters [N]

| Symbol | Meaning | Default | Status |
|---|---|---|---|
| **h** | CUSUM alarm threshold | set by harness | **calibrated to ARL_0 (D-2a); the only scalar knob** |
| **W** | pairs in the p_c reporting window | 16 (provisional) | **swept descriptively** {8, 16, 32}; does not affect the alarm path |
| L | probe block length | 3 = H | frozen (contract) |
| ℋ, 𝒜, ε, H, p, r, w_T, H_det, probe_budget | — | {1,2,3}, ±e_k @1.0, 0.05, 3, 3, 20, 50, 200, 0.05 | frozen (contract §0) |
| Π | normal cadence | 75 (provisional) | frozen; derived as ceil(L/(0.8·probe_budget)) |
| η, B_max, Π_burst, burst_len | reservoir/burst | 0.8, 30, 6, 100 | frozen (provisional) |
| k | CUSUM slack | 0.5 | frozen |
| σ_floor | scale floor | 0.1 | frozen |
| n_ref | post-alarm reference window | 200 | frozen (provisional) |
| q | BH level, **diagnostic only** | 0.05 (IBD §3.2) | frozen; outside the alarm path |

Two knobs are visible to the experiment: one calibrated (h), one swept (W). All values marked *(provisional)* require a pilot before the confirmation freeze.

**Failure modes.**
1. **Probe starvation after the event.** Within H_det = 200 steps the detector gets ≈ 2–3 blocks (≈ 8 pairs) before the burst engages. Expected latency floor ≈ Π/2 + max(ℋ) + p ≈ 43 steps before any statistical delay. If the pilot shows HPDT near H_det, Π must fall (raising η toward 1.0) or L must fall to 1.
2. **Co-primary floor at short offsets.** The co-primary reads mean p_c on confounded distractor channels at offsets {10, 50, 200}. At offset 10, and often at 50, **no probe block has occurred**, so p_c is necessarily its pre-event value. This is a property of any probe-budgeted method, not a defect; it must be reported as a floor.
3. **Feedback compensation (regime R2)** shrinks the probe-versus-policy contrast on body channels; power drops. This is the intended difficulty of R2, but it can drive HPDT to H_det.
4. **Policy-arm asymmetry.** An aggressive stabilising policy can make baseline |Δ| exceed probe |Δ|; the two-sided CUSUM is required for this reason too, and the isotonic g must be fitted per cell.
5. **C-dependence of max_c.** ARL_0 at fixed h falls as C grows; per-cell calibration (D-2a, roadmap v4.2 §F10) absorbs this, but h is **not** transferable across distractor levels.
6. **Sign-flip blindness** (§4) — correct behaviour, but a red-team mutant should confirm it is intended and not accidental.
7. **Reference re-estimation blind window.** No alarm can be raised for n_ref = 200 steps after an alarm; under `event_spacing` = 250 this is safe, but only just.

## 9. Pseudo-code [N]

```
state: t, reservoir, mode, blk_ctr, ring[C][H+L], pairs[C][|H|] (deque W),
       mu[C][|H|], sig[C][|H|], Gp[C], Gn[C], g (isotonic), h, raise_run, refract, p_cache

def request_probe(steps):                      # harness offers `steps`; we take L or none
    period = PI_BURST if mode == BURST else PI
    if reservoir < L or (t - last_block_t) < period: return None
    n = min(steps, L); reservoir -= n; last_block_t = t
    return [ A[randint(2K)] for _ in range(n) ]     # i.i.d. Uniform(A = +-e_k, |a| = 1.0)

def update(tr):                                # once per env step AND per probe step
    t += 1; reservoir = min(B_MAX, reservoir + PROBE_BUDGET); push(ring, tr.obs)
    for (i_p, i_n) in pairs_completed_at(t):   # probe start / matched null start, +max(H) lag
        z = -inf
        for hz in H_SET:
            d_p = abs(ring[:, i_p + hz] - ring[:, i_p]); d_n = abs(ring[:, i_n + hz] - ring[:, i_n])
            delta = d_p - d_n; pairs[hz].append(delta)          # W-window, for p_c only
            z = maximum(z, (delta - mu[hz]) / maximum(sig[hz], SIG_FLOOR))   # per-channel
        if in_reference_window():  continue                     # CUSUM frozen at 0
        Gp = maximum(0, Gp + z - K_SLACK); Gn = maximum(0, Gn - z - K_SLACK)
        p_cache = g(signed_rank_z(pairs))                       # frozen isotonic map
    alarm = 0; S = max(max(Gp), max(Gn))
    raise_run = raise_run + 1 if S > h else 0                   # h: the ONE scalar knob
    if refract > 0: refract -= 1
    elif raise_run >= P_PERSIST:
        alarm = 1; refract = R_REFRACT; raise_run = 0
        Gp[:] = 0; Gn[:] = 0; mode = BURST; start_reference_window(N_REF)
    return clip(p_cache, 0, 1), alarm
```

## 10. Claims we do not make [N]

This is an **engineering baseline derived from IBD**, not a new method and not a contribution of this project. It makes no identifiability, optimality, FDR-control or ARL-optimality claim in the sequential setting: IBD's Props. 3.3–3.5 (arXiv:2603.18257 §3.4) are proved for the one-shot two-branch design and **do not carry over** to overlapping windows, adaptive re-probing, or a policy-roll-out null. No claim is made that this is the best sequentialisation of IBD; it is the one we froze so the confirmatory contrast against `R0_inband_linear` CUSUM is well defined. It estimates S^obs,ε only — not R, not M, not body membership (contract C6).

**References.** Liu, Cheng & Bogdan, arXiv:2603.18257, §§3.1–3.5, Alg. 1, Eq. 2, Props. 3.3–3.5, App. C. Page (1954), CUSUM. Wilcoxon (1945), signed-rank. Benjamini & Hochberg (1995), FDR. Contract `stage-0a-contract-v3.1.md` §§0, C, D, F, G, H; `roadmap-v4.1/4.2/4.3-amendments.md`; `interface-spec-v3.md`; `confirmation-design.csv`.
