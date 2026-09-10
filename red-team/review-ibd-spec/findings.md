# Red-team review of `sequential-ibd-spec.md` (Draft 1) — independent, adversarial, fresh context

Date: 6–7 September 2026. Reviewer: fresh-context agent (Claude), no prior involvement. Rubric: `readiness-protocol.md` (ID, severity, claim attacked, evidence, proposed fix, fix type). Normative basis: `stage-0a-contract-v3.2.md` §§0, B, C, D, F, G, H, H2; `interface-spec-v3.md`; `roadmap-v4.md` + amendments v4.1–v4.4; `decisions-required.md` (D-6, D-7). Paper: Liu, Cheng & Bogdan, *Discovering What You Can Control: Interventional Boundary Discovery for RL*, arXiv:2603.18257 (v1 18 Mar 2026, v2 7 May 2026), read at `arxiv.org/html/2603.18257` on 6 Sep 2026.

**Executable evidence.** `review-ibd-spec/sim_ibd_review.py`; output in `review-ibd-spec/sim_ibd_review.output.txt` (two runs: registry-plausible policy scale W_u = 0.5, and a quiet-policy sensitivity W_u = 0.2). Interpreter `/Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3`, numpy 2.4.4; wall time 247 s + 260 s on 10 cores. Settings: 200 seeds per confirmation cell; 200 run lengths per ARL grid point; 400+ run lengths at the verified h* (the D-2a count); null streams capped at 900k steps. Nothing outside this folder was written.

**Folder-state note.** `review-ibd-spec/sim_ibd.py` already existed (written 22:29 by another agent, never run, no output). The brief said to use the folder only if empty and never edit existing files; I left that file untouched and named mine `sim_ibd_review.py`. I read only its header; the two implementations are independent and the adjudicator can compare them.

**Verdict in one line:** redraft. The prose is careful, but at the registry constants the detector has **no power for the confirmatory event** (the event *lowers* the alarm probability), and its ARL_0 is a **near-deterministic timer**, not a false-alarm process. Opinion is marked as such.

---

## 0. Consistency table (Task 1)

| Item | Draft | Normative | Result |
|---|---|---|---|
| `update` return | `(p, alarm)` (§1, §9) | `(p[C], stat, alarm_S)` (interface v3) | **deviation** — `stat` missing; harness cannot own thresholding |
| `request_probe(steps)` | returns `min(steps, L)` or None | `actions[steps, K] or None` | deviation (fewer than offered) |
| v3: `alarm_S = 1 iff stat > h after persistence p`; `statistic_is_monotone_in_alarm=True` | alarm has side effects (reset G, burst, 200-step blind re-estimation) that change the future `stat` path | harness calibrates from the statistic (OP-4) | **substantive deviation**: `stat` is h-independent only until the first alarm (IB-2) |
| `configure`, `calibrate`, `set_threshold`, `needs_calibration_split` | present | present | consistent |
| probe_budget 0.05, p 3, r 20, H_det 200, ε 0.05, 𝒜 ±e_k @1.0, ℋ {1,2,3}, H 3, w_T 50, event_spacing 250 | §8 | contract v3.2 §0 | **all match v3.2**; the draft's "v3.2 does not exist" paragraph is stale (file exists; §0 D-2a, H `R0_inband_linear`, H2 are as the draft assumed) |
| C4 zero-action continuation | not used; null = preceding L policy steps | C4 defines R; detector claims S^obs,ε only (C6) | permitted; but null-window overlap (IB-4) and policy dependence / misattribution (IB-5) |
| alarm bookkeeping | `raise_run` counts during refractory | `contract_ref.count_alarms` resets `run=0` in refractory | minor deviation (IB-8) |
| IBD provenance | "Following IBD §3.2, the baseline branch is the ordinary policy roll-out" | paper §3.5: "Our default π_probe is a structured random policy with sinusoidal actions and weak state feedback" — a dedicated probe policy; Alg. 1 collects both branches under π_probe, replacing every action by i.i.d. Unif(𝒜) in the intervention branch | **misattribution** (IB-5) |
| Bonferroni min-p over ℋ "transposed to a z-scale" as `max_h z_h` | §3 | min-p over two-sided tests ⇔ signed `max_h |z_h|` | **wrong transposition** (IB-1) |

---

## 1. Findings

### IB-1 — high — "Two-sidedness is required … a one-sided IBD-style test sees nothing" (§4); "Max over ℋ is the IBD Bonferroni min-p rule transposed to a z-scale" (§3)
**Claim attacked.** The two-sided per-channel CUSUM on `z_c = max_h z_h` detects shrinkage of S^obs,ε (complete actuator loss).
**Evidence.** `max_h` of three median-centred, positively correlated variates has null mean ≈ +0.66 on body channels and +0.45 on distractors (output §calibration). With k = 0.5, `E[max_h z − k] > 0` on 13/24 channels: G⁺ is a positive-drift random walk under the null; G⁻ has drift −1.08 and never fires (share of alarms from G⁺ = 0.95–1.00 at every h). After the loss, the per-horizon z on the lost channel moves only to [−0.09, −0.04, −0.03] (run 1) or [−0.20, −0.09, +0.02] (run 2); `max_h` then averages +0.51 / +0.37 instead of +0.66 / +0.77 — the event *slows the timer*. Measured on the same seeds: P(alarm in (event, event+200]) **with** the event 0.10 / 0.14 (T = 2,000 / 20,000) versus **without** it 0.14 / 0.18. HPDT = 194 / 185 of a maximum 200. The signed-|z| variant (ABSMAX) restores two-sidedness (G⁺ share 0.5–0.6) but has the same nil power within H_det (0.02 / 0.17 vs null 0.02 / 0.22): see IB-3.
**Proposed fix.** Replace `max_h z_h` by a two-sided aggregate (signed `max_h |z_h|`, or one CUSUM per (channel, horizon) with the |ℋ| factor absorbed by h) and re-derive k against the null mean of the chosen aggregate. Gate test: on a null stream the mean per-epoch increment of both G⁺ and G⁻ must be < 0; on a complete-loss stream P(alarm within H_det) must exceed the no-event control by a predeclared margin.
**Fix type.** test + prose (the change is small; whether it rescues the arm is IB-3).

### IB-2 — high — "S(·) does not depend on h … the harness may bisect on h" (§4); v3 `statistic_is_monotone_in_alarm=True`; D-2a "false-alarm run lengths"
**Claim attacked.** ARL_0(h) is a well-defined, harness-calibratable function of the one knob.
**Evidence.** (i) The alarm resets G, starts a burst and re-estimates (μ, σ) from the next 200 steps; each changes the statistic path, so `stat` is h-independent only until the first alarm. The harness cannot recover run lengths at several h from one recorded `stat` stream; each h needs its own re-simulation. (ii) The draft never says which run length D-2a averages, and the two natural readings differ by 60 %: at h* = 31.2, steady-state inter-alarm ARL = 1,011 [981, 1,041] (n = 408) while fresh-start-to-first-alarm ARL = 1,605 ± 45; the h giving fresh-start ARL 1,000 is ≈ 22–24. A single-event 2,000-step run experiences the fresh-start quantity (pre-event false alarms 0.04/run, not ≈ 1); a 20,000-step run the steady-state one (8.9/run). (iii) The steady-state run length contains a mechanical 220-step (r + n_ref) floor in which alarms are impossible: for h ≤ 4 the stream ARL is 229–236 regardless of h. (iv) The fresh-start run length has CV ≈ 0.23 — a timer, not a false-alarm process; this is why the D-2a band is trivially met here (± 30 at n = 408). Monotonicity itself survived (see §2), but the argument given for it is false after the first alarm.
**Proposed fix.** Define ARL_0 for this arm explicitly (recommend fresh-start-to-first-alarm, matching a single-event episode; otherwise state that steady-state is meant and that the blind floor is inside it); return `stat` from `update`; either declare `statistic_is_monotone_in_alarm=False` or make the calibration stream alarm-free (no reset/burst/re-estimation during calibration); state whether the D-2a 2,000,000-step cap is per h value or per cell (one h value cost 370k–450k steps here).
**Fix type.** prose + test (test: the recorded `stat` stream reproduces the alarm sequence at a second h; fails as drafted).

### IB-3 — high — §7 "Feasibility warning" and §8 failure mode 1 understate the problem
**Claim attacked.** The arm is *budget*-limited (the D-6 framing) and a pilot can repair it by adjusting Π or L.
**Evidence.** Within H_det = 200 the detector completes 9–11 pairs (measured 9.3 / 10.7 epochs; reservoir at the event ≈ 10 tokens, so the burst funds 3 blocks, not 10, and the burst lands inside the blind window anyway). The per-pair effect of a complete loss on the lost channel is ≤ 0.3 σ (IB-1). A CUSUM calibrated to ARL_0 = 1,000 steps ≈ 50 epochs needs h ≈ 22–34 here; 10 epochs × 0.3 cannot reach it. Raising episode_len ×10 (D-6a) changes nothing inside H_det (post-event epochs 9.3 → 10.7; P(detect) stays at the null floor) and raises blind-window collisions from 4 % to 15 %. The quiet-policy sensitivity (W_u = 0.2; corr(a, x) = 0.39, i.e. *below* ρ_min, so outside the contract) doubles the raw contrast and still gives P(detect) 0.04 / 0.15 vs null 0.07 / 0.24. Context only (not the D-3a arm): a per-step innovation CUSUM on a linear predictor fitted on the same split gives HPDT 5–9 with P(detect) = 1.00 at a comparable null ARL. The confirmatory contrast Δ = HPDT(CUSUM) − HPDT(IBD) is therefore a foregone ≈ −190 steps: R1 futility and the R0 "probing cost dominates" flag by construction. Opinion: this is a design outcome, not an empirical finding, and must not enter a confirmatory run.
**Proposed fix.** A decision, not pilot tuning: (a) change the arm's statistic from a per-pair CUSUM to a windowed two-sample rank test over *all* post-block pairs against the frozen reference (the paper's Welch-t idea, which needs many samples — the point of its 2·N·T = 32k steps), with ARL_0 calibrated on that statistic; or (b) change the constants the arm is judged under (H_det, probe_budget, block design — e.g. L = 1 at every reservoir opportunity triples the epochs; simultaneous probes on all K actuators double the per-pair effect on each body channel); or (c) keep the arm as a documented negative result and stop calling the pair "confirmatory". Each is a redraft.
**Fix type.** decision.

### IB-4 — medium — "The null block … is the L steps immediately preceding it" (§2); "Locality is the point"
**Claim attacked.** The matched null is a policy-only contrast.
**Evidence.** Null start t_b − L + i with horizon h ends at o(t_b − L + i + h); for (i = 1, h = 3) and (i = 2, h ≥ 2) the endpoint lies *inside* the probe block, so the "null" increment contains the probe's own effect (τ = 0). Measured mean δ on the lost body channel by (pair i, horizon h), run 2: i = 0: [0.37, 0.46, 0.02]; i = 1: [0.35, −0.01, −0.05]; i = 2: [−0.08, −0.05, −0.04]. Three of nine (i, h) cells carry no contrast; because `z = max_h`, they add noise to every pair. (The i = 0, h = 3 collapse is a separate effect — three i.i.d. random-sign probes partially cancel over three steps while autocorrelated policy actions, lag-1 r = 0.49 induced by ρ_u = 0.8, accumulate; see IB-5.)
**Proposed fix.** Null start t_b − L − max(ℋ) + i (shift by τ as well when τ > 0) so every null increment ends at or before t_b; test that no null increment window overlaps [t_b, t_b + L + τ + max(ℋ)).
**Fix type.** test.

### IB-5 — medium — "Following IBD §3.2, the baseline branch is the ordinary policy roll-out" (§2); "Deviation from contract C4, stated"
**Claim attacked.** The policy-step null is (a) what IBD does and (b) causally sound under the shared-cause confounder u.
**Evidence.** (a) Paper §3.5: "Our default π_probe is a structured random policy with sinusoidal actions and weak state feedback, requiring no RL training"; both branches are collected from the same reset distribution under the *probe* policy, the intervention branch replacing each action by an i.i.d. Unif(𝒜) draw (Alg. 1). The draft's null is the *task* policy — the one thing the paper does not use. (b) Validity: x-channel increments have no action parent, so δ is mean-zero whatever u does, and the local pairing (3 steps apart under ρ_u = 0.8) *reduces* variance; confounded vs unconfounded distractor p_c: 0.255 vs 0.253 (run 1), 0.221 vs 0.219 (run 2) — no leak; the C4 deviation does not confound S^obs,ε (that attack failed). Power: on body channels the null arm's increment law is the policy's, whose action scale and autocorrelation are set by W_u u_t. Changing W_u 0.5 → 0.2 moved the h = 1 reference median δ on b0 from 0.088 to 0.165 and the h = 3 median from 0.147 to 0.009: the size *and horizon structure* of the contrast the detector must lose at the event are functions of the confounder's gain into the policy. The contract fixes probe magnitude (1.0) and ρ_min but not the policy's action scale (H2: "additive action noise", saturation bound only). "Confounder absent" keeps W_u (F7), so the 2×2 interaction is unaffected, but the arm's power across environments (PointMass2D linear controller vs Pendulum energy-shaping) is uncontrolled.
**Proposed fix.** Correct the attribution. Either register the default policy's action RMS (or the ratio probe magnitude / policy RMS) in §0 per environment, or give the arm a null that does not depend on the task policy (zero-action continuation per C4, or a dedicated π_probe baseline block as in the paper). State in §10 that the detector's power, unlike its validity, depends on the task policy.
**Fix type.** prose + decision.

### IB-6 — medium — p_c path: frozen isotonic g (§3), W = 16, "ℋ-argmax horizon", "p_c is emitted every step" (§4), §9 pseudo-code
**Claim attacked.** p_c is a calibrated probability that c ∈ S^obs,ε and the co-primary is measurable at offsets {10, 50, 200}.
**Evidence.** (i) On a fault-free calibration split labels are constant per channel; the isotonic fit learns P(body | s). In run 1 the body and distractor s-distributions overlap (means 0.12 vs −0.03), g spans 0.23–0.60 and p_c ≈ 0.25 = 6/24 on every channel group (lost 0.266, kept 0.267, confounded x 0.255): a constant predictor. In run 2 g separates (body 0.43, x 0.22) but the lost channels decay only to 0.33 at offset 50 and 0.28 at offset 200. (ii) W = 16 pairs = 5.3 blocks = **400 steps of memory** at Π = 75: offsets 10 and 50 read the pre-event value in essentially every run (lost 0.434 vs kept 0.436 at offset 10); offset 200 reads a half-refreshed window. The sweep {8, 16, 32} is a memory sweep {200, 400, 800} steps, all ≥ the offsets. (iii) The pseudo-code's `continue` in the reference window precedes `p_cache = g(...)`, so p_c is frozen for 200 steps after every alarm — contradicting §4 — and a detection at delay d freezes the co-primary from d to d + 200 (measured effect small here only because p_c is uninformative). (iv) "Wilcoxon z at the ℋ-argmax horizon" is undefined for a window statistic (which pair's argmax? it flips between epochs). (v) The Wilcoxon tests median δ = 0 while the CUSUM z is centred on μ_ref: two nulls. (vi) With W = 16, |z| ≤ 3.52.
**Proposed fix.** Specify the composition of the split g is fitted on (it must contain post-event states or the fit is degenerate); define the reporting horizon (fixed h, or pooled over ℋ); centre the rank statistic on μ_ref or say why not; move the `p_cache` refresh outside the blind-window `continue`; report the window's step-memory next to each offset, and report offsets 10 and 50 as "pre-event by construction" for this arm.
**Fix type.** prose + test (tests: p_c changes during the blind window; g fitted on the declared split takes ≥ 2 distinct values on body channels).

### IB-7 — medium — n_ref = 200; "re-estimated over the n_ref steps after each alarm"; failure mode 7 ("safe, but only just")
**Claim attacked.** Post-alarm re-estimation is benign and the blind window is a bounded cost.
**Evidence.** 200 steps yield 9–20 pairs (mean 17.6, min 9 at T = 20,000) against 480 at calibration; a median/MAD from 9–20 pairs has ≈ 25–35 % relative scale error and a too-small σ inflates every later z. This self-excitation is why the steady-state ARL is 37 % below the fresh-start ARL (IB-2). The blind window sits under the event in 15 % of T = 20,000 runs (mean remaining blind 92–99 steps) and 4 % of T = 2,000 runs. D-2a's band [900, 1,100] at ≥ 400 run lengths is met for the draft only because its run length is a low-variance timer; for the two-sided ABSMAX variant, whose run length is heavy-tailed (median 839, mean 1,105), 408 run lengths give ± 190 and the band was **not met** in three verification attempts. No fall-back is specified for too few pairs.
**Proposed fix.** Do not re-estimate the reference from post-alarm data (freeze the calibration reference, as the residual arms do), or require ≥ N_min pairs before replacing it; if a blind window is kept, exclude it from the run length or state that ARL_0 includes it; say how D-2a's band is handled when the run-length CV exceeds 1.
**Fix type.** prose + decision.

### IB-8 — medium — "α^S = 1 at the first step on which the raw raise has held for p = 3 consecutive steps" (§4)
**Claim attacked.** Alarm bookkeeping is the same operation as for the comparator (contract G), so alarms are comparable at matched ARL_0.
**Evidence.** S is piecewise constant: it changes on 3 consecutive steps per block, then holds for ≈ 72 steps. Once the third epoch exceeds h the persistence condition is met automatically two steps later — p adds a fixed 2-step delay and filters nothing; for the per-step comparator p = 3 is a real filter. The draft's `raise_run` also counts during the refractory window while `contract_ref.count_alarms` resets it, so the two can differ on the step after a refractory ends.
**Proposed fix.** Apply persistence in *epochs* for this arm and say so (or state that p is vacuous here and report the comparator's effective persistence alongside); count alarms by calling `contract_ref.count_alarms` on the raw raise sequence rather than re-implementing it.
**Fix type.** test.

### IB-9 — low — "This is a hard cap: the realised probe fraction is ≤ 0.05 on every run" (§2)
**Evidence.** True only if the reservoir starts at 0; the draft does not say. Starting at B_max = 30 gives 105 probe steps in a 2,000-step run = 0.0525 (run 1). Starting at 0 gives 90–96 (≤ 0.048). At T = 2,000 the reservoir never reaches B_max (≈ 10 tokens at the event), so B_max is inert in the confirmation schedule and the post-alarm burst funds ≈ 3 blocks, not 10.
**Proposed fix.** State reservoir_0 = 0; test the invariant `n_probe ≤ floor(0.05 · t)` at every step.
**Fix type.** test + prose.

### IB-10 — low — "Two knobs are visible to the experiment: one calibrated (h), one swept (W)" (§8)
**Evidence.** The table lists η, B_max, Π_burst, burst_len, k, σ_floor, n_ref as "frozen (provisional)", and §7/§8 say Π, η or L will change if the pilot shows HPDT near H_det — outcome-dependent tuning of hidden knobs. Unlisted: reservoir_0 (IB-9); minimum pairs for re-estimation (IB-7); the argmax rule and centring for the rank statistic (IB-6); calibration-split length and composition; tie handling; the "absent extreme" value for all-zero windows (a knot of g). Default justification: k = 0.5 is the textbook slack for a unit shift in N(0,1) and is wrong for `max_h z` whose null mean is 0.66 (IB-1); n_ref = 200 gives 9–20 pairs (IB-7); Π_burst = 6 fires only inside the blind window, so its pairs never reach the CUSUM and it empties the reservoir for the post-blind period; B_max = 30 is unreachable at T = 2,000 (IB-9); σ_floor = 0.1 binds on 21 % of (h, c) cells (padding, w) and is defensible; W = 16 is a 400-step memory (IB-6).
**Proposed fix.** Rename the table "parameters"; mark which are frozen before the pilot with a written reason each; forbid post-pilot changes to any without re-running calibration and the black-box suite.
**Fix type.** prose.

### IB-11 — low — Source-document paragraph and interface signatures
**Evidence.** The draft says contract v3.2 "does not exist here" — it does (20,926 bytes; §0 with D-2a, H with `R0_inband_linear`, H2). Every §8 value matches v3.2 §0 and the H roles match; nothing needs re-deriving, but the paragraph must go. `update` must return `(p, stat, alarm)`; `request_probe` should return `steps` actions or None (or the interface should say "up to `steps`").
**Fix type.** prose.

### IB-12 — medium — D-6 (decision): "The constants are mutually inconsistent unless sequential IBD is a windowed detector with small samples"
**Evidence (Task 3, both episode lengths, run 1, n = 200 each).**

| | T = 2,000, event 1,000 | T = 20,000, event 10,000 |
|---|---|---|
| probe steps / run (mean, max) | 90.1, 96 (fraction ≤ 0.048) | 991, 996 (≤ 0.0498) |
| refresh epochs / run | 90 | 991 |
| epochs inside H_det after the event | 9.3 | 10.7 |
| pre-event false alarms / run | 0.04 | 8.9 |
| P(event inside a blind window) | 0.04 | 0.15 |
| P(detect within H_det) vs no-event control | 0.10 vs 0.14 | 0.14 vs 0.18 |
| HPDT [95 % CI] | 194.1 [190.5, 197.6] | 184.8 [178.5, 191.0] |
| median delay of first alarm after the event | 569 (the timer) | 620 (the timer) |
| ARL_0 = 1,000 steps attainable at Π = 75? | yes as steady-state: 1,011 [981, 1,041] at h = 31.2, n = 408 — but as a timer (fresh-start 1,605 ± 45, CV ≈ 0.23) | same h; the run is the steady state |

Reading. D-6's premise — the arm is starved of probe steps — is not what limits it. Detection must occur within H_det = 200 and both lengths give the same ≈ 10 post-event pairs; option (a)'s extra 900 probe steps all land before the event or after H_det, while adding ≈ 9 pre-event alarms and a 15 % chance that the event lands in a blind window, which *worsens* HPDT. Option (c) raises the null floor, already 14–18 % per 200-step window at ARL_0 = 1,000. The numbers support **(b)** for episode length, *with the calibration quantity redefined as the fresh-start run length* (what a single-event 2,000-step episode experiences; IB-2), and reject (c). None of (a)/(b)/(c) makes the arm as drafted a competitor; that requires IB-1 and IB-3. Opinion: answer D-6 "(b), and re-open the IBD arm's design", not "(a)".
**Fix type.** decision.

---

## 2. Attacks that failed (claims that survived)

1. **ARL_0 monotone in h.** Both run-length definitions were monotone at all ten grid points (point estimates, and within 2 se), for the draft and the ABSMAX variant. No counter-example from reservoir, burst or re-estimation dynamics; the draft's *argument* is wrong after the first alarm (IB-2), the conclusion held here.
2. **Confounder leak through the policy-step null into distractor p_c.** None: δ on x-channels has no action parent; the local pairing only reduces variance; confounded and unconfounded distractors get identical p_c (0.255 vs 0.253; 0.221 vs 0.219). Prop. 3.3's logic (a randomised probe severs C → a) carries over for the *validity* of the x-channel contrast; its power implications do not (IB-5).
3. **Hard probe cap.** With reservoir_0 = 0 the realised fraction never exceeded 0.048 (T = 2,000) or 0.0498 (T = 20,000) over 800 runs.
4. **§7 "≈ 40 epochs per 1,000 steps"** — measured 40 in normal cadence, 50 including bursts. **§8 latency floor ≈ 43 steps** — smallest detected delay at T = 2,000 was 42.
5. **Constants.** Every §8 value matches contract v3.2 §0; the D-2a and H2 wording the draft reconstructed from the amendments is what v3.2 says.
6. **The toy SCM is a legitimate contract-B instance** at W_u = 0.5: saturation 0.0008 (< 0.05), corr(a, x) = 0.43 ≥ ρ_min, ρ(A_b) = 0.7, nonzero entries ≥ c_min, CL-4 satisfied (b0 → b1 → d0 with no alternative path). The W_u = 0.2 run (corr 0.39) is outside the contract and used only to bound what a quieter policy could buy: not enough.
7. **Not tested:** sign-flip blindness (K8), family N, τ = 2 cells, distractor levels 30/100, R2. τ = 2 removes the probe-arm effect from h ∈ {1, 2} entirely (first hit at h = τ + 1 = 3), which can only reduce the per-pair effect further.

---

## 3. Task 4 in one place — statistical soundness

- **Wilcoxon signed-rank z, W = 16:** |z| ≤ 3.52; uncentred; 400-step memory; horizon selection undefined; fine as a descriptive score, not as a probability without a non-degenerate calibration split (IB-6).
- **Isotonic p_c:** fitted on constant-per-channel labels it collapses toward the channel base rate (run 1: 0.23–0.60); frozen, so it cannot follow a post-alarm reference change; the same machinery serves the comparator (H3), so *comparability* of the co-primary is preserved but *informativeness* is not (IB-6).
- **Two-sided CUSUM on `max_h z`, k = 0.5:** effectively one-sided with positive drift; the negative side is dead; the run length is a timer (IB-1, IB-2).
- **Median/MAD reference:** sound at calibration (480 pairs); unsound when re-estimated from 9–20 pairs (IB-7); σ_floor binding on 21 % of cells is fine.
- **Offsets 10 and 50:** no probe block in most runs; with W = 16 even offset 200 is half-refreshed; report as floors, as the draft says, and report the memory (IB-6).
- **Non-comparability with the comparator arm:** persistence semantics (IB-8); statistic cadence 50/1,000 vs 1,000/1,000; alarm side effects inside the statistic path (IB-2); a 220-step blind floor inside the measured ARL_0 (IB-7). Matched ARL_0 in *steps* does not match false-alarm *behaviour*.

## 4. Recommendation

**Redraft.** Interface and constants are prose fixes (IB-9, IB-10, IB-11) and the null-window overlap is a one-line change (IB-4), but three findings go to the detector's identity: the horizon aggregate makes the alarm one-sided and blind to the only confirmatory event type (IB-1); the statistic path is not threshold-independent and the run-length quantity is undefined, so `set_threshold` does not do what interface v3 promises (IB-2); and at probe_budget 0.05, H_det 200, ARL_0 1,000 steps the arm sees ≈ 10 post-event pairs of ≤ 0.3 σ each, which no per-pair CUSUM turns into a detection — the event makes an alarm *less* likely, and the confirmatory contrast against a per-step residual CUSUM is a foregone loss of ≈ 190 steps (IB-3, IB-12). Signing as-is would freeze a confirmatory arm whose result is already known. The redraft should choose — as Daniel's decision, not a pilot outcome — between a many-sample windowed test statistic for the arm, different constants for the arm to be judged under, or re-labelling the pair as a documented negative result. Opinion: answer D-6 with (b) and a fixed run-length definition; D-7(a) becomes more important, not less, because probing-versus-passive is exactly what these numbers are about.
