# Round 4 red team — Claude Opus, independent, fresh context

**Frozen version reviewed:** `442cc4b7da691ca0`, verified with `python3 freeze.py` at the start and end of
this review (unchanged throughout — rule H6 held). `python3 executable-proofs/gate/run_gate.py` exits **0**
(34/34 tests, 35/35 registered mutants killed).

**What I built.** `sim_e2e.py` — an end-to-end reproduction of both confirmatory arms, written from
`stage-0a-contract-v3.5.md`, `sequential-ibd-spec.md` (draft 3) and `comparator-spec.md` **alone**, on my own
contract-B family-L instance at registry values. No `review*/` simulation or findings file was opened until
this document was complete except section 5, which says so. Captured output `sim_e2e.output.txt` (77 s).
New mutants: `new_mutants.py`, `new_mutants.output.txt`.

---

## 1. Primary outcome, reproduced

Threshold-free mid-rank AUC of the **raw** per-channel statistic against `S^obs,ε` at **offset 500**
(epoch 1483 for arm 1, step 1500 for arms 2/3); family L, τ = 0, R0 in-band linear; complete loss of
actuator 0 at t = 1000, `s_change` certified per instance; one fresh instance draw per seed; 40 seeds drawn,
40 admissible after the ρ_min (≥ 0.4) and saturation (≤ 0.05) rejections. Paired 95 % t intervals on
per-seed differences (df = 39).

| | N_x = 10 (C = 24) | N_x = 30 (C = 44) |
|---|---|---|
| AUC `seq_ibd`, confounder **present** | **0.912** [0.856, 0.969] | **0.933** [0.882, 0.985] |
| AUC `seq_ibd`, confounder **absent** | 0.925 [0.874, 0.977] | 0.929 [0.877, 0.981] |
| AUC `cusum_linear_channel_agnostic`, **present** | **0.637** [0.610, 0.663] | **0.599** [0.572, 0.627] |
| AUC `cusum_linear_channel_agnostic`, **absent** | 0.819 [0.788, 0.851] | 0.818 [0.788, 0.849] |
| AUC `cusum_linear_probed`, **present** | 0.645 [0.617, 0.672] | 0.617 [0.587, 0.646] |
| ΔAUC(present) = IBD − passive | **+0.276** [+0.210, +0.342] | **+0.334** [+0.281, +0.388] |
| ΔAUC(absent) | +0.106 [+0.046, +0.166] | +0.110 [+0.054, +0.167] |
| **Confounding benefit [ΔAUC(pres) − ΔAUC(abs)]** | **+0.170** [+0.127, +0.213] | **+0.224** [+0.190, +0.258] |
| D-9.3 rule at δ_AUC = 0.10 | **SUPERIORITY** (lb > 0.10) | **SUPERIORITY** (lb > 0.10) |
| R0-present positive control (lb ΔAUC present > 0.10) | PASS (+0.210) | PASS (+0.281) |
| R0-absent equivalence, 90 % TOST ±0.05 | **FAIL** [+0.057, +0.155] | **FAIL** [+0.064, +0.156] |

Offsets 200 and 1000 are in `sim_e2e.output.txt`; the confounding benefit is +0.165/+0.167 (N_x = 10) and
+0.221/+0.214 (N_x = 30) there, so the primary is not offset-fragile.

**The headline reproduces on a third model and a third instance family.** D-9.1's conclusion — the
sign-randomised contrast ranks the controllable support well at a 5 % budget, is confounder-insensitive
(0.912 present vs 0.925 absent), and the probed comparator does not close the gap (0.645 vs 0.637) — is
verified. My AUCs exceed the D-9 numbers (0.75–0.83) because my `A_b` is block-structured, so the lost
actuator's channels become exactly unreachable; that is a property of my instance draw, not of the arm, and
it is exactly the problem R4-19 describes.

**The decomposition, however, is not the one the working claim asserts.** More than a third of the arm's
advantage is present with **no confounder at all**, and the R0-absent equivalence cell fails in every
configuration I ran, by +0.08 to +0.34 AUC. That is finding **R4-6**; its causes are **R4-2** (the passive
comparator is structurally blind to downstream channels) and **R4-3** (at τ = 2 it is structurally blind
to everything).

## 2. Untested regions (all D-9 evidence is family L, τ = 0, N_x ≤ 30)

40 seeds each (34 at N_x = 100), offset 500:

| Region | AUC IBD (pres) | AUC passive (pres) | AUC passive (abs) | Confounding benefit | Rule |
|---|---|---|---|---|---|
| family L, **τ = 2**, N_x = 10 | 0.883 [0.831, 0.934] | **0.320** [0.263, 0.378] | 0.540 [0.426, 0.655] | +0.225 [+0.101, +0.349] | SUPERIORITY |
| **family N**, τ = 0, N_x = 10 | 0.921 [0.864, 0.979] | 0.562 [0.533, 0.591] | 0.807 [0.761, 0.853] | +0.266 [+0.212, +0.319] | SUPERIORITY |
| family L, τ = 0, **N_x = 100** | 0.927 [0.882, 0.973] | 0.547 [0.519, 0.575] | 0.841 [0.806, 0.875] | +0.301 [+0.250, +0.353] | SUPERIORITY |

**The primary holds in all three.** Three qualifications, all new:

* **τ = 2 makes the comparator vacuous, not merely weaker** (R4-3), so the τ = 2 superiority is an artefact
  of the comparator's lag order and is not independent evidence.
* **τ = 2 also empties the downstream class from the estimand.** With H = 3 and τ = 2, C1's "first hit at
  h = τ+1" plus one hop per step leaves only directly-driven body components reachable, so `d` falls out of
  `S^obs,ε` (my instances go from 3 positives to 2, prevalence 0.083). Contract C6 says "examples must
  include one" downstream channel inside S; at delay 2 no such example exists. Nothing in the contract, the
  matrix or either spec records this.
* **N_x = 100 does not degrade either arm's ranking** (IBD 0.927; passive-absent 0.841), so D9-codex-4's
  prevalence worry is correctly handled by moving to AUC. Positives stay at 3 of 114, prevalence 0.026.

**`n_min_sign` and the window do NOT make early offsets degenerate in the way the IBD spec says** (R4-4):
at offset 200 the median usable-cell count is 6 of 6 at every N_x and τ, identical to offset 500, and the
AUC attenuation is small. The window is degenerate in two other, unrecorded ways — R4-5 (whole-actuator
deletion, 8–12 % of episodes at *every* offset) and R4-1 (the warm-up, which destroys the alarm channel).

---

## 3. Findings

Severity: **critical** = makes a declared operating point unreachable or invalidates a normative claim;
**high** = changes a headline number or a decision rule; **medium** = would produce a wrong or
unreproducible run; **low** = correctness or hygiene.

| ID | Sev | Claim attacked | Evidence | Proposed fix | Type |
|---|---|---|---|---|---|
| **R4-1** | critical | `sequential-ibd-spec` §5: "ARL_0(h) is non-decreasing and the harness may bisect" (T-IBD-mono); §5 "the warm-up … is inside the run length, not excluded"; §10.1 "low alarm power, declared not hidden". §12 marks IB-2 **resolved**. | `sim_e2e.py::arl_sweep`. During warm-up `a_c ≡ 0` on **every** channel (§3: "0 if no cell is usable"), while `ā_c` is fitted on full windows, so `stat_warm = max_c ā_c/v_c` is the **largest value the statistic ever takes**: 5.48 / 5.68 / 5.44 on three instances, against a full-window null max of 5.48 / 5.68 / 5.14 and a post-event max of 4.67 / 4.25 / 4.29. Measured fresh-start ARL_0 over 25 event-free episodes: **exactly 63.0 steps with 0 % censoring for every h ≤ 5.25**, and **no alarm at all in 2 000 steps** for every h above the plateau. P(detect within H_det) ≤ 0.24 and only at h where ARL_0 = 63. ARL_0(h) is therefore a two-valued step function; the D-2a band [900, 1100] is **unattainable at any h**; the §5 bisection has no root. The plateau is deterministic (p = 3 epochs fires at epoch 3, t = 63, on every fresh start). Worse, the **null** stream contains the same maximum: 0.1 % of full-window null epochs have zero usable cells under `n_min_sign`, giving `a_c ≡ 0` and `stat = stat_warm` with nothing wrong. This is a **regression introduced by draft 3**: review3 bisected draft 2 successfully to attained ARL_0 in [946, 1063]. | Make `stat` non-raising while any actuator's cells are unusable, and declare the warm-up an explicit non-scoring prefix excluded from ARL_0. If instead the warm-up is kept inside the run length by decision, then: change T-IBD-mono from "monotone" to "**attains** ARL_0 ∈ [900,1100] at some h"; pre-declare the arm as a D-2a partial-order endpoint with best attainable pair ≈ (63, —); and delete the descriptive HPDT contrast for this arm, because roadmap v4.7 K4's "at a measurable cost in alarm speed" is then unmeasurable. Re-open IB-2's disposition. | decision + test |
| **R4-2** | high | `comparator-spec` §2 and D-9.4 / `decisions-required.md`: the comparator is "the strongest passive reading", frozen on principle so the margin is decided by the science and not by the baseline's specification. | `l_c = ‖β_{a,c}‖₂/σ_c` is **structurally ≈ 0 on downstream (d) channels**, which contract C6 requires to be positives. Measured (family L, N_x = 10, present, mean over 40 seeds): l[b retained] = 6.365, l[**d retained**] = **0.048**, l[x confounded] = 7.147, l[padding] = 0.035. Dropping d channels from the label set raises the comparator's AUC 0.637 → **0.776** (N_x = 10), 0.599 → 0.726 (N_x = 30), 0.562 → 0.652 (family N), 0.547 → 0.670 (N_x = 100). Mechanism: a one-lag predictor that conditions on the whole observed state explains `d_{t+1}` entirely by `C_d b_t`, so `β_{a,d} = 0` by construction. The comparator concedes 0.09–0.14 AUC — 0.9 to 1.4 × δ_AUC — on exactly the channel class the estimand (C6) is named for. | Replace `l_c` by the H-step cumulative loading `l_c = max_{h ≤ H} ‖β^{(h)}_{a,c}‖₂ / σ^{(h)}_c` from H separate one-shot regressions of `o_{t+h}` on `[o_t, a_t, 1]` — still passive, still channel-agnostic, no new registry constant (H is already frozen). If that is refused, `comparator-spec` §11 must state that downstream support is conceded by construction, and the primary AUC must be reported with and without d channels as a mandatory sensitivity. | decision |
| **R4-3** | high | `comparator-spec` §8 row 5: "lag order 1 … adding lags would make it a different arm"; contract §H: "R0 = the linear predictor fitted on in-distribution fault-free data (**correct only on family L**)". | At τ = 2, `o_{t+1}` does not depend on `a_t` at all (a_t enters b_{t+3}), so `β_a ≈ 0` on every body channel, while confounded distractors keep `β_a ≠ 0` because `a_t` is a contemporaneous proxy for `u_t` which drives `x_{t+1}`. Measured (family L, τ = 2, N_x = 10): l[b retained] = **0.089**, l[b lost] = 0.075, l[x confounded] = **7.150**. Comparator AUC 0.320 (present) and **0.540 (absent)** — at or below chance even with no confounder; IBD 0.883/0.878; ΔAUC(present) = +0.562. `confirmation-design.csv` has **900 of 2 700 rows at delay = 2**, and they enter `aggregate_primary`'s equal-weight mean over delays (v4.1 E2). Contract §H's "correct only on family L" is false: the predictor is not correct on family L at τ = 2. | The comparator's feature row must be `[o_t, a_{t−τ_max}, …, a_t, 1]` (τ is a declared cell property already carried in `regime_bundle`, not oracle knowledge), or delay = 2 cells must be removed from the confirmatory conjunction and reported as "comparator not applicable". Either way §8 row 5 and contract §H must stop asserting one-lag in-distribution correctness. | decision |
| **R4-4** | high | `sequential-ibd-spec` §4: "At offset 200 the 10 post-event units split over 4 signed groups average 2.5 — below `n_min_sign` — **which is the mechanism of the attenuation**." | The mechanism is wrong. §3 applies `n_min_sign` to the **window's** 25 units, not to a post-event subset — the estimator does not know the event time and cannot subset by it. Measured at offset 200 in every configuration: median usable cells **6 of 6** (identical to offset 500), `a_c = 0` on 0 channels; AUC 0.897 / 0.916 / 0.863 / 0.872 (L10 / L30 / τ=2 / N) against 0.912 / 0.933 / 0.883 / 0.921 at offset 500. The real mechanism is **dilution**: 15 of 25 window units are pre-event. | Correct §4 to state dilution as the mechanism (the fraction table itself is right — I reproduce 1/25, 3/25, 10/25, 25/25, 25/25 exactly). Extend T-IBD-offsets to assert cell usability **and** the pre/post mixture separately, so the two are never conflated again. | prose + test |
| **R4-5** | high | `sequential-ibd-spec` §3 `n_min_sign` handling; §10's failure-mode list (which covers τ = 2 cell loss but not sign-imbalance cell loss). | With 25 units split over K × 2 = 4 signed groups (mean 6.25), `min(n₊,n₋) < 3` deletes **an entire actuator's cells** in 8–12 % of episodes at every offset and every configuration. When the deleted actuator is the **surviving** one, `a_c` is computed only from the dead actuator and is pure null: seed 0, N_x = 10, offset 500 → AUC **0.238** (against a block mean of 0.912). The rate is a deterministic function of Π, W_steps and K, so it is a permanent variance floor that will not shrink with seeds. §10 does not list it. | Log the usable-cell count per epoch in the ledger — today `a_c` alone hides whether it came from 6 cells or 3 — and pre-declare handling of zero-usable-actuator epochs. `W_steps = 1000` roughly halves the rate but destroys §8 row 6's "100 % post-event at the primary offset" property, so this is a genuine trade-off for Daniel, not a free fix. | test + decision |
| **R4-6** | high | Contract §G / D-9.3: "R0-absent is an equivalence cell: two one-sided tests, 90 % interval for Δ_AUC(absent) inside (−δ0_AUC, +δ0_AUC)"; roadmap v4.7 K4's working claim. | The equivalence **fails in every configuration**: 90 % TOST intervals [+0.057,+0.155] (L10), [+0.064,+0.156] (L30), [+0.028,+0.158] (family N), [+0.026,+0.132] (N_x = 100), [+0.237,+0.438] (τ = 2). D-9.3 assigns a consequence to R0-present failure ("an anomaly that stops the phase") but **none at all** to R0-absent failure, so a pre-registered rule can fail with no pre-registered response. Substantively the arm's advantage is not mainly a confounding story: it wins by 0.08–0.34 AUC with G = 0. | State the consequence before the pilot. **Opinion:** if R0-absent equivalence fails, restate the working claim as "the interventional arm dominates the strongest passive reading on support ranking, and the gap widens under a shared-cause confounder", demoting the confounding-benefit contrast from headline to mechanism. Note the ordering: fixing R4-2 and R4-3 first will shrink ΔAUC(absent) and may make the equivalence attainable, so those decisions must precede this one. | decision + prose |
| **R4-7** | high | `comparator-spec` §9 F1: "assert … episode AUC of `q` against `S^obs,ε` is **below 0.5** at offset 500. This pins the pathology the benchmark exists to measure; if it stops holding, the comparator has silently changed." Also §2's "the arm's AUC falls to or below chance". | It is a family-level property asserted as a deterministic gate fixture, and it is false on most admissible instances. Share of present episodes with AUC < 0.5 at offset 500: **0 %** (family L, N_x = 10, mean AUC 0.637), 15 % (N_x = 30), 24 % (N_x = 100), 12 % (family N), 82 % (τ = 2). Every other gate fixture in the repo (K1–K10, T-C1-*, T-C4-*) pins fixed matrices; F1 and F2 pin a distribution. A gate test that fails between 0 % and 88 % of the time depending on the instance draw is not a gate. F2 fares better on my instances (mean Δq = −5.82 on channels leaving the support vs +0.10 on channels retained) but is stated the same way. | Rewrite F1 and F2 as **fixed hand-constructed instances** with pinned `A_b, B, C_d, G, W_u, W_o, Assign` and a stated expected ordering, exactly as K1–K10 are. Move the population statement out of §9 into a reported quantity with an interval and a named instance family. | test + prose |
| **R4-8** | high | Contract §G co-primary (locked, D-5): "confounded-channel false support = mean p_c over oracle-labelled confounded distractor channels at offsets **{10, 50, 200}** after the event", tested hierarchically after the primary. | At those offsets **neither arm's window is post-event**. Arm 1 (`W_steps = 500` on anchor time): 1/25, 3/25, 10/25 post-event units — the spec's own §4 table. Arm 2/3 (`W = 500` on steps, `[t−499, t]`): 11/500, 51/500, 201/500 post-event steps. So a co-equal, D-5-locked outcome measures the **pre-event** false support of both arms at two of its three offsets and 60 % pre-event at the third. `sequential-ibd-spec` §4 concedes it for arm 1 ("pre-event by construction … reported as floors") and lists it as failure mode 2; the contract never moved the offsets, and `comparator-spec` never notices that arm 2 has the identical problem. | Move the co-primary to `offsets_rank` = {200, 500, 1000}, or {500, 1000}; or define it on a causally recent sub-window instead of the full trailing window. As it stands, hierarchical testing after the primary would report a pre-event quantity as a post-event finding. | decision |
| **R4-9** | medium | Contract §0 D-2a / v4.2 F10 / v4.6 J1: calibration per (environment, regime, confounder, distractor_level, delay, estimator) cell, "shared across seeds"; `confirmation-design.csv` gives calibration rows `seed = -1`. | Every frozen object in **both** arms is instance-specific and channel-indexed: comparator `β` ((C+K+1)×C), `μ_c`, `σ_c`, `l_c`, `degen_c`, `k`; IBD `ā_c`, `v_c`, and the pooled `g` over a channel axis. `l_c` is the action loading of *this* draw's B and Assign; `ā_c` is the null level of *this* draw. If calibration episodes come from a different draw than the scored episode, `l_c` and `ā_c` are meaningless; if from the same draw, "shared across seeds" is false and F10/J1's budget accounting (charged once per cell) is wrong by a factor of the seed count. Neither spec resolves it. I had to choose (CHOICE-09: same instance — the reading most favourable to the comparator). | Add `instance_id` to the calibration cell key; state that the arms' frozen objects are per instance; correct F10/J1's budget statement and the `calibration_steps` column. | decision + prose |
| **R4-10** | medium | Contract §G: "Detection = **first** counted alarm with event_t < alarm_t ≤ event_t + H_det." | **Surviving mutant R4-M1.** No test in `test_gate.py` places two alarms inside one event's window, so a `match_alarms` returning the **last** qualifying alarm passes all 34 gate tests. Witness: `match_alarms([1010,1100,1180],[1000],200,2000)` → original `([10],['detected'],[1100,1180])`, mutant `([180],['detected'],[1010,1100])`. The mutant inflates HPDT by up to H_det for any arm that alarms in bursts — which both confirmatory arms do, since they emit raw exceedances and the harness applies `p = 3`, `r = 20`, admitting up to 9 counted alarms inside one 200-step window. `mutants.PROBES["match_alarms"]` also lacks a discriminating input, so the mutant would today be rejected by the distinctness guard rather than registered. | Add the witness above to `test_gate.py` **and** to `mutants.PROBES["match_alarms"]`, then register R4-M1. | test |
| **R4-11** | medium | v4.1 E2 / v4.2 F6 / v4.6 J1: the primary cell is (environment, regime, confounder, distractor_level, delay). | **Surviving mutant R4-M2.** `contract_ref.aggregate_primary` keys cells on `(seed, level, delay)` only. Fed the confirmation matrix as generated (4 environments × 2 regimes × 2 confounder arms at the same seed/level/delay), rows **collide** and the last one silently wins, with `dropped = 0` and no diagnostic. A first-wins mutant survives all 34 tests: original `{0: 100.0}` vs mutant `{0: 20.0}` on colliding rows. Neither is correct. This is R3-CX-03's next step: that finding fixed the `delay` key and left the other three cell dimensions out. | Extend the key to `(seed, environment, regime, confounder, level, delay)`; add a test with two environments at the same (seed, level, delay); add the witness to PROBES. | test |
| **R4-12** | medium | Contract C2/C3 vs E1b: "two independent label derivations (graph reachability; **zero-noise finite-difference**) agree on every sampled instance". | **Surviving mutant R4-M3.** `s_obs_eps` computes `|gain_c| · e_j > ε`; a mutant computing `|gain_c · e_j| > ε` survives all 34 tests, because every probe input and every fixture passes a non-negative `e`. But E1b's second derivation is a **finite difference**, which is signed, and C4's `R` is explicitly signed. "Take the magnitude of the gain" and "the effect is already a magnitude" are two separate requirements and only one is pinned. This mutant **is** admitted by the existing PROBES distinctness guard, so it can be registered today with no other change. | Add `s_obs_eps(np.array([-1.0]), [0], [1.0], [True], 0.1) == [False]` to `test_gate.py` (or make `s_obs_eps` reject negative effects explicitly), and register R4-M3. | test |
| **R4-13** | medium | `sequential-ibd-spec` §8 row 15: "`g` = single pooled isotonic … per-channel fits would need per-channel labels **the estimator never sees**". | A non-sequitur: §6 pass 0 says the **evaluator** fits `g`, and the evaluator does see labels, so per-channel fitting is available. The real reason to pool is that a channel's label is (almost) constant within an episode, so a per-channel isotonic map would be degenerate — a different and better argument. Separately, pooling across heterogeneous channel types (padding, live w, confounded x, body, downstream d) is a real per-type mis-calibration; it affects tier 2 only, because AUC is monotone-invariant. | Replace row 15's justification with the correct one. State in §4 that tier-2 calibration is pooled across heterogeneous channel types and therefore mis-calibrated per type, and report per-type reliability as a tier-2 diagnostic. | prose |
| **R4-14** | medium | `sequential-ibd-spec` §4 (fit of `g`) versus §5 (fit of `ā`, `v`). Also re-opens **GM3-4**, which draft 3's §12 disposition table does not mention at all. | §5 restricts `ā`, `v` to epochs whose window is "entirely pre-event and entirely full". §4 fits `g` on "`(a_c(t), 1[c ∈ S^obs,ε_t])` at **every** epoch". In each of the 12 event-carrying fit episodes, 25 epochs have a window straddling the event and are therefore paired with a post-event label against a mixed-window statistic — designed-in label noise, in the same file that excludes exactly those epochs from the other frozen artefact. GM3-4 (round 3, high) raised transition-band contamination of `g`; the D-9 move from F1-at-0.5 to AUC removed its primary consequence, but the tier-2 consequence survives and is undisposed. | Apply §5's window-purity rule to `g`: exclude straddling epochs, or fit on pre-event and fully-post-event epochs separately and say which is used, with the resulting epoch counts stated as §5 does. Add GM3-4 to §12 with its disposition. | prose + test |
| **R4-15** | medium | `sequential-ibd-spec` §11 T-IBD-cal-2: "≥ 200 positive and ≥ 200 negative channel-epochs in the fit split" (which explicitly **replaces** draft 2's 5 % minority-share gate that CX-01 killed). | The count is over dependent duplicates. Consecutive epochs share 24 of 25 units; a channel contributes ~100 epochs per episode; the label is constant within an episode. The number of independent (channel, label) observations is nearer 24 episodes × 4 non-overlapping windows × C than 24 × 100 × C, so the floor is met roughly 25× over by duplication and certifies nothing about the isotonic fit's stability. The replacement inherits the weakness it was meant to remove. | Restate the floor in independent units, e.g. "≥ 24 episodes each contributing ≥ 1 positive and ≥ 1 negative channel, and ≥ 4 non-overlapping windows per episode". | test |
| **R4-16** | medium | `comparator-spec` §6 (flagged judgement call 2): probe-sign blindness "is enforced by T-CMP-probe-blind, which permutes the `probe_flag` field of every transition and asserts bitwise-identical `(p, stat, raise)`". | The test cannot detect the leak §6 itself names. §6 correctly says the sign is readable from `applied_action`; permuting `probe_flag` proves nothing about that path, and `applied_action` **is** consumed (it is a block of X). **My answer: probe-sign blindness is not enforceable and should not be attempted.** Arm 3 is *supposed* to see the probes; the mechanism control is that its statistic aggregates them sign-symmetrically — the ± contributions to the window innovation mean cancel — which my run confirms (arm 3 vs arm 2 AUC 0.645/0.637, 0.617/0.599, 0.582/0.562, 0.606/0.547 across the four configurations). | Replace T-CMP-probe-blind with a test of the property that actually carries the argument: replay a probed stream with every probe sign negated and assert the window-mean innovation term is unchanged in distribution and `q` moves by less than a declared tolerance. Rewrite §6 to say the arm consumes the sign and that the control rests on sign-symmetric aggregation, not on withholding. | decision + test |
| **R4-17** | medium | `comparator-spec` §5 "Who fits it" (marked **[Opinion]** in the spec — flagged judgement call 1) and `interface-spec-v3.md` `configure(regime_bundle)`. | **My answer: yes, the harness must own the isotonic fit, and this is forced rather than optional.** Contract E5 puts the oracle in a separate process, never importable by the estimator; `g` requires oracle labels; therefore the estimator cannot fit it. Both specs already assign it there (`comparator-spec` §5, `sequential-ibd-spec` §6 pass 0), so no disagreement exists. The defect is elsewhere: interface v3 defines `configure(regime_bundle)` as carrying "`{model_params_hash, model_params\|None}` for the declared regime's **residual model**", while `sequential-ibd-spec` §1/§6 pushes `{g_knots, ā, v}` through it and §1 simultaneously declares "**no residual dynamics model**". There is no legal interface channel for a harness-fitted calibrator. | Amend interface v3: add `install_calibrator(g_knots, operating_point)` (harness → estimator, logged in the ledger), or widen `configure`'s contract to "frozen artefacts declared by the arm's spec, hashed". Promote `comparator-spec` §5's `[Opinion]` note to normative text. | decision |
| **R4-18** | medium | `sequential-ibd-spec` §12 "Open" item (a): "`interface-spec-v3.md` has **no field** for the raw `a_c` stream". | Half wrong, and the correct half is worse. The interface v3 **ledger row** already lists `raw_support_stat_stream (a_c per channel per epoch; the primary AUC is computed on this, never on p_c)`. What is missing is a **producer**: `update(transition) -> (p[C], stat, raise)` returns no `a`, so nothing normative obliges or even permits the estimator to emit it, and the E6 black-box acceptance suite — written from the interface spec alone — cannot obtain the stream on which the primary metric is defined. A stale open-items list also means roadmap v4.7 K5's tracking of remaining work is wrong. | Extend `update`'s return to `(p, a, stat, raise)` or add `raw_support_stat() -> float[C]`; correct §12(a). | prose + decision |
| **R4-19** | medium | Contract §0 registry, §A, §B, and rule J8 ("a decision whose basis is one model's simulation is not frozen until a second model reproduces it **on its own instance**"). | Nine load-bearing quantities are absent from the normative set and I had to invent them (`CHOICE-01`…`CHOICE-09` in `sim_e2e.py`): `n_u`; `C` and the composition of the C − N_z extra channels (I inferred C = N_z + 4 from `comparator-spec` §7 and `n_channels` in the matrix, but not how many are copies vs padding, nor which latent is copied); the sparsity patterns of `A_b, B, C_d, A_d, A_w, A_x, G, W_u`; the support of `W_o` (which observation channels the policy sees — this decides whether a second confounding path o_x → a exists at all); baseline `gain_t`; the scored-episode burn-in; and the initial state for C2's expectation (C4 declares z̄, C2 declares nothing). Every AUC in D-9 and in this review is a function of these. The measured spread across the four reproductions (0.75–0.93 for the same arm at the same offset) is instance-family variation, not Monte Carlo error. Consequence: J8's "own instance" is currently "own **invented** instance", so the three reproductions agree about the statistic and say nothing about the benchmark. | Add a normative generator block (or `instance-family.md`) fixing the sampling distributions, sparsity patterns and channel layout, hashed into `config_hash`, **before** Stage 0A. Until then, cross-model verification under J8 is weaker than it is being relied on to be. | prose |
| **R4-20** | medium | Contract §G primary: "threshold-free AUC of the estimator's raw per-channel support statistic". | The **tie convention is undeclared in all three normative files**, and both arms produce mass ties by design: arm 1 gives `a_c = 0` to every channel when no cell is usable (all channels during warm-up and in 0.1 % of full-window null epochs); arm 2 gives `q_c = −q_cap` to every degenerate channel. Under "ties → 0", "mid-rank" and "ties → 1" the primary AUC differs by up to the tied mass, precisely in the stressed cases. I adopted mid-rank Mann-Whitney (CHOICE-07). Separately: the AUC computation appears **nowhere** in `contract_ref.py` or `coverage-matrix.md`, although it has been the primary since roadmap v4.5. | Declare mid-rank Mann-Whitney in contract §G; add `auc(scores, labels)` to `contract_ref.py` with a tied fixture; add a coverage-matrix row (currently the primary metric has no test ID, which the contract's own gate rule forbids: "a normative item without a test ID is not implemented"). | prose + test |
| **R4-21** | medium | Estimator identifiers. | `comparator-spec` fixes `cusum_linear_channel_agnostic`; `confirmation-design.csv` uses the same; `contract_ref.aggregate_primary`'s default is `est_a="cusum_channel_agnostic"`; roadmap v4.1 E2 and `coverage-matrix.md` say "CUSUM". Passing matrix rows straight into `aggregate_primary` drops **every** pair and returns `({}, n_cells)` with no error. R3-CX-03 reported the same mismatch in round 3 and it is still present in the frozen version. | One name, asserted by a test that feeds a real `confirmation-design.csv` row. | test |
| **R4-22** | low | `comparator-spec` §2 and §8 row 16: `q = clip(l − shift, −q_cap, +q_cap)` then `q[degen] = q_absent = −q_cap`; "`q_absent` puts degenerate channels at the bottom knot". | `q_absent` is **not** a separate knot: a live channel with `l − shift ≤ −40` is clipped to exactly −40 and becomes indistinguishable from a dead one in the isotonic domain and in the AUC ranking. My measured shift reaches ≈ 8 on lost channels with `l ≈ 7`, so −40 is not reached at these registry values — but `q_cap` is `[prov]` and the margin is argued nowhere. | Clip live channels to `[−q_cap + 1, q_cap]` with `q_absent = −q_cap`, or add an explicit degeneracy indicator to the calibrator domain. | prose |
| **R4-23** | low | `sequential-ibd-spec` §2, §8 row 4, T-IBD-count. | The probe at t = 2 000 is granted, charged 1 % of the probe budget, replaces the last environment step (and its task regret), and **closes no unit** — §2 says so. A grant condition `t + max(ℋ) ≤ episode_len` returns the step at a realised fraction of 0.0495. T-IBD-count as written freezes the waste into the gate. | Add the terminal condition, or state explicitly that the waste is accepted so the count stays a round 100. | decision |
| **R4-24** | low | `sequential-ibd-spec` §9 pseudo-code and §5. | `stat`, `a` and `p_cache` are only assigned inside the epoch branch, but `update` returns `clip(p_cache,0,1), stat, int(stat > h)` at **every** step and runs `assert not isnan(p_cache).any() and not isnan(stat)` every step. For t = 1…22 no epoch has occurred and they are unbound (or NaN, which the spec makes a hard error). | Initialise `stat = 0.0`, `a = zeros(C)`, `p_cache = g(0)` at reset and say so in §5. | prose |
| **R4-25** | low | `roadmap-v4.6-amendments.md` J7 lists ten requirements "carried forward" into spec draft 3, including "**optional jitter (GM3-7)**". | Nine of the ten are addressed in draft 3 (I checked each). The tenth is not: the words "jitter" and "GM3-7" do not appear in `sequential-ibd-spec.md` or `comparator-spec.md`, and §8 rows 1–2 freeze `L = 1, Π = 20` strictly periodic with no mention of aliasing. GM3-7's concern (strictly periodic probing can alias with a closed-loop resonance) is live for the control tier: PointMass2D and Pendulum-v1 have well-defined natural frequencies, and a fixed 20-step cadence in a 2 000-step episode is a comb. | Record the decision explicitly in §8 — jitter rejected, with the reason (a jittered cadence breaks the exact `floor(0.05·t)` invariant and the 25-unit window count) — or add it. Either way J7's item must be closed rather than dropped. | prose |

---

## 4. Attacks that failed

Recorded because a failed attack is evidence for the spec.

1. **"The comparator's `√n·mean(r̃)` needs a long-run-variance correction."** With ρ_u = 0.8 driving both the
   policy and the distractors, I expected serially correlated innovations and a null SD far above 1,
   heterogeneous by channel type — which would have biased the ranking. Measured null SD of the shift term on
   fault-free streams: τ = 0 — body 0.97, d 1.04, w 1.01, confounded x 1.07, unconfounded x 1.06, padding
   1.07; τ = 2 — body 1.22, d 0.93, w 0.99, conf x 1.06, unconf x 1.09, pad 0.94. The one-lag predictor
   whitens enough. No correction needed; the τ = 2 body inflation is a footnote, not a finding.
2. **"A complete actuator loss is a variance change, not a mean change, so the innovation-mean shift term is
   blind to it."** Wrong. Measured at offset 500: shift = 6.66 on channels leaving `S^obs,ε` vs 0.85 on
   channels retained; Δq = −5.82 vs +0.10. The u-driven drift of `a_t` over a 500-step window, amplified by
   `√500`, supplies the mean. `comparator-spec` §9 F2's *direction* holds on my instances (its *form* does
   not — R4-7).
3. **"'No washout' is false: the previous probe's sign contaminates the anchor `o_c(t_p)`."** The residue is
   real — with ρ ≤ 0.95 and Π = 20, ≈ 0.95¹⁷ = 0.42 of a probe's effect survives to the next anchor and does
   **not** cancel in `D = o(t_p+h) − o(t_p)` (it contributes `ρ¹⁷(ρ^h − 1)R`). But `S_{p−1} ⊥ S_p`, so it
   enters both sign groups with the same conditional law. §2's marginal argument is correct as written, and
   §3 correctly declines to claim window-level exchangeability, which is the property that actually fails.
   Attack fails; the spec's honesty here is well judged.
4. **"h-independence of `stat` is false."** `request_probe` is block-periodic and deterministic, the
   estimator's sign RNG is independent of h, no alarm is fed back to the environment, and the window never
   resets — so the `a_c` path and hence `stat` are h-invariant. ARL_0(h) is also genuinely monotone: the
   first time p consecutive raises occur is monotone in the raise sequence, and the refractory only affects
   *subsequent* alarms, never the first. Both §5 claims hold. What fails is the *usefulness* of the
   bisection (R4-1), not its validity — an important distinction, because R4-1's fix must not be presented
   as fixing this.
5. **"The tie-corrected σ_U² formula is wrong, or the two forms §3 gives are not equivalent."** Both forms
   agree to 1e-12; the untied case reduces exactly to `n₊n₋(N+1)/12` (spec z = textbook z, difference
   0.00e+00); a hand fixture with two tie groups ({1,1,2} vs {1,2,3}) matches a hand computation to 0.
   The formula is correct as printed, in both forms.
6. **"The 100/99 probe derivation is wrong."** Exhaustive replay over t = 1…2000 of §2's grant rule gives
   exactly `{20, 40, …, 2000}`, 100 applied, 99 closing a unit, realised fraction exactly 0.050.
7. **"The §4 window-memory table is wrong."** Recomputed from the epoch grid: epoch reads
   1003 / 1043 / 1183 / 1483 / 1983 and post-event fractions 0.04 / 0.12 / 0.40 / 1.00 / 1.00 — matches the
   spec exactly. (What is wrong is the *explanation* of the 200 column — R4-4.)
8. **"The pre-event-segment epoch counts are wrong."** {500,…,980} = 25 epochs, {500,…,1980} = 75 epochs,
   12·25 + 12·75 = 1200. Correct.
9. **"The probed comparator (arm 3) is contaminated by probe shocks entering its fitted window."** 25 of the
   500 window steps are probes at magnitude 1.0 against a policy RMS ≈ 0.7, but the signs cancel in the
   window mean: arm 3 AUC 0.645 vs arm 2 0.637 (N_x = 10), 0.617 vs 0.599 (N_x = 30), 0.582 vs 0.562
   (family N), 0.606 vs 0.547 (N_x = 100). D-7a's conclusion — probes alone do not close the gap — holds on
   my instances, and §4's decision to re-derive only `k, h, g, θ*` (not `β, μ, σ, l`) is right.
10. **"The degenerate-channel rule (`q = −40`, excluded from the alarm max) is wrong or unnecessary."**
    It is necessary — without it an `avail = 0` channel gives an unbounded `r̃` and a permanent alarm, as §1
    says — and it never mis-fired on my instances (0 degenerate channels; noise-only padding is correctly a
    live negative with `l ≈ 0.035`, exactly as §1's "padding and copies" paragraph predicts). Only the
    knot-collision survives, at low severity (R4-22).
11. **"The ridge λ changes β materially."** `λ_rel = 1e-4 · trace(XᵀX)/(C+K)` against 40 000 rows left the
    Cholesky solve well conditioned at C = 24, 44 and 114, with no degenerate channels and no numerical
    warnings in 296 fits. The spec's framing of λ as a conditioning guard rather than a modelling choice is
    accurate.

---

## 5. Which findings are in new categories relative to rounds 1–3

*(Written after everything above, having then read `review-claude/`, `review-codex/`, `review-gemini/`,
`review2-*/`, `review3-*/`, `review-ibd-spec/`, `review-d9-codex/`, `review-d9-gemini/` findings and the two
round tallies. Nothing above was altered afterwards.)*

**New categories** — no round-1/2/3 finding and no item in either spec's disposition table occupies this
space:

* **R4-2 / R4-3 — structural capacity of the baseline.** D9-codex-6 established that a support score needs an
  action-loading baseline term; D9-GM-4 showed the comparator choice moves the margin by ≈ 0.29 AUPRC.
  Neither asked *what the chosen loading term can represent*. "The comparator cannot represent downstream
  support at any τ, and cannot represent anything at τ = 2" is a new kind of objection: not that the
  baseline is weak or badly calibrated, but that its functional form excludes part of the estimand.
* **R4-8 — a window convention invalidating a locked outcome, across both arms.** R3-15 and IB-6 examined
  arm 1's window memory; the step to "therefore the D-5-locked co-primary measures a pre-event quantity, for
  the passive arm as well" was not taken.
* **R4-6 — pre-registered rules with undefined failure branches.** D9-codex-5 repaired the incoherent "TOST
  non-superiority" wording. Nobody asked what happens when the repaired rule fails, and on my instances it
  fails everywhere.
* **R4-19 — the cross-model verification protocol verifies the statistic, not the benchmark.** Rounds 1–3
  closed registry gaps one at a time (CX-09, GM2-11, OP-15, FB-11, R3-13). None observed that the *instance
  family itself* is unspecified, which is what makes rule J8's "reproduces it on its own instance" much
  weaker than it reads.
* **R4-12 and R4-20 — the sign of `e`, and the primary metric's own computation.** The 35 registered mutants
  cover reachability, gain, HPDT, spacing, correlation and alarm bookkeeping. None touches the sign of the
  latent effect. And the AUC — the primary since roadmap v4.5 — is absent from `contract_ref.py` and from
  `coverage-matrix.md` entirely, so the contract's own rule ("a normative item without a test ID is not
  implemented") is violated by the primary outcome.
* **R4-25 — a carried-forward requirement silently dropped.** Checking roadmap v4.6 J7's ten items against
  draft 3 one by one is, as far as I can tell, new; nine are addressed and the tenth (jitter, GM3-7) is not
  mentioned at all.

**Same category, new mechanism** (I claim partial novelty only):

* **R4-1** sits in IB-2's category (the alarm channel's calibratability and the bisection argument). IB-2
  concerned draft 1's resets and re-estimation, concluded that monotonicity survived and that the D-2a band
  *was* attainable; draft 3 deleted those mechanisms and §12 marks IB-2 resolved. My result is that the fix
  introduced a **new and worse obstruction** — the warm-up plateau is the statistic's global maximum, so the
  band is unattainable at any h and detection power is ≈ 0. That is a regression, measured, in a
  disposition marked closed. It is the most serious thing I found and it is not a new *category*.
* **R4-4, R4-5, R4-13, R4-14, R4-15, R4-24** continue the R3-11 / D9-codex-3 / GM3-4 line on `n_min_sign`,
  window conventions and calibrator hygiene, with new evidence (and R4-14 re-opens GM3-4, which draft 3's
  disposition table omits).
* **R4-10, R4-11** continue OP-12 / R3-M4 / R3-CX-03 on alarm matching and aggregation keys.
* **R4-21** is R3-CX-03's naming half, unfixed in the frozen version.
* **R4-16, R4-17, R4-18** continue CX-03 / FB-9 / IB-11 on the interface; their content is the two judgement
  calls the comparator spec explicitly asked a reviewer to settle, which I answer above.
* **R4-7, R4-9, R4-22, R4-23** are refinements of items the specs flag themselves.

**Process observation (opinion).** Rule H6 held: the hash was unchanged from the start of this review to the
end. Rule J8 also held in form — D-9.1 now has three independent reproductions and all three agree. But
R4-19 shows J8 is weaker than it is being relied on to be: three models built three different generators
from the same contract, and the 0.75–0.93 spread in the same arm's AUC at the same offset is instance-family
variation, not Monte Carlo error. Freezing the generator before Stage 0A would make J8 do the work it was
written to do; until then, "two-model verification" certifies the estimator, not the benchmark.
