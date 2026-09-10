# Round 3 review — frozen version `e662b7429b6b347d`

Reviewer: fresh-context Claude Opus, 7 September 2026. Independent; no prior context on this project.

**Freeze verified.** `python3 freeze.py` -> `e662b7429b6b347d`, matching the round-3 prompt and
`freeze-manifest.txt` (18 files). No file in the manifest was modified by this review.

**Gate re-run.** `python3 run_gate.py` with `/Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3`:
`GATE PASS: tests 25/25, mutation exit 0`, exit code 0. 23/23 existing mutants killed.

**Artefacts produced by this review** (all inside `review3-claude-opus/`, nothing else touched):

| File | What it is |
|---|---|
| `sim_d8.py` | Independent simulation: contract-B family-L instance at registry values, the DRAFT-2 detector built from `sequential-ibd-spec.md` sections 2-5 and 9, two readings of the contract-H comparator, the D-7a probed arm, ARL_0 bisection, and the D-8a primary. Written **before** reading `review-ibd-spec/sim_ibd_review.py` or `review-ibd-spec/findings.md`; nothing is imported from either. |
| `sim_d8.output.txt` | Captured output. Runtime 104 s. Seed counts: 30 scored + 30 no-event control episodes per cell, 40 calibration episodes (half event-carrying, per spec section 4), 24 x 6,000-step null streams for ARL_0. Reduced from the contract's full matrix to 5 cells; stated here rather than implied. |
| `mutants_r3.py`, `mutants_r3.output.txt` | Nine new mutants against the frozen gate, modelled on `executable-proofs/gate/mutants.py`. **Seven survive.** |

Opinion is marked **[opinion]**. Everything else is either a quotation from a frozen file or an
executable measurement whose script and output are in this folder.

---

## Task 1 — the D-8 refutation attempt

**Verdict: D-8's finding is confirmed by an independent simulation, and it is worse than D-8 states.
The alarm channel has no power, AND the support-correctness primary that D-8a substituted is also at
chance for the draft-2 arm as specified. D-8 is not reopened; but D-8(a) does not by itself rescue
the confirmatory contrast.**

### 1a. The alarm channel (D-8's original claim) — reproduced

`sim_d8.py` section A, thresholds bisected to the D-6b fresh-start ARL_0 = 1000 on 24 x 6,000-step
no-event streams, 30 scored + 30 no-event control episodes per cell:

| cell | h (IBD) | attained ARL_0 | P(alarm in (event, event+H_det]) | same, **no-event control** | CUSUM P(det) | CUSUM control |
|---|---|---|---|---|---|---|
| R0, confounder present, N_x=10 | 2.020 | 982 | **0.43** | **0.43** | 1.00 | 0.03 |
| R0, confounder absent, N_x=10 | 2.020 | 982 | 0.37 | 0.40 | 1.00 | 0.20 |
| R0, present, N_x=30 | 2.063 | 1042 | 0.37 | 0.37 | 1.00 | 0.13 |
| R1, present, N_x=10 | 1.774 | 946 | 0.33 | 0.40 | 1.00 | 0.03 |
| R1, absent, N_x=10 | 1.778 | 1016 | 0.37 | 0.40 | 1.00 | 0.20 |

The interventional arm's alarm probability inside H_det is **indistinguishable from, and in two cells
below, the no-event control on the same seeds**. The passive innovation CUSUM detects the same event
with probability 1.00 at the same ARL_0. This is the `decisions-required.md` D-8 claim, reproduced
from a different instance, a different detector implementation, a different comparator
implementation and a different random-number stream. I could not refute it.

Mechanism, measured: `stat = max_c |a_c - abar_c| / v_c` is a maximum over all C channels. A complete
actuator loss moves at most the 3-6 body/downstream channels by about 1-1.5 z-units, while the
remaining C-6 channels supply a null maximum that is already about 2.0 at C = 22 and 2.06 at C = 42.
The signal is smaller than the null maximum, and it gets relatively smaller as `distractor_level`
rises. Spec section 10.6 records that ARL_0 at fixed h falls with C and says "per-cell calibration
absorbs it". Per-cell calibration absorbs the *false-alarm rate*; it cannot absorb the *power* loss,
because raising h to restore ARL_0 raises it above the signal too. That is a stronger statement than
section 10.6 makes.

### 1b. The new primary (D-8a) — the remedy does not work either

Threshold-free AUC of each arm's support score against `S^obs,eps`, plus the contract-G F1
(p_c > 0.5), at the primary offset 500 and at 1000 (the fully post-event offset), confounder-present
cell:

| arm | F1 @200 | F1 @500 | F1 @1000 | mean channels predicted @500 | AUC @500 | AUC @1000 |
|---|---|---|---|---|---|---|
| `seq_ibd` (draft 2 as specified) | 0.050 | 0.077 | 0.050 | 0.30 | **0.514** | **0.534** |
| `seq_ibd`, g fitted excluding the transition band | 0.097 | 0.093 | 0.078 | 0.50 | 0.514 | 0.534 |
| `seq_ibd`, one-sided `max_h z_h` instead of signed max-\|z\| | 0.050 | 0.077 | 0.050 | 0.30 | 0.542 | 0.506 |
| `cusum_linear` (literal per-channel innovation CUSUM) | 0.000 | 0.000 | 0.000 | 0.00 | 0.473 | 0.474 |
| `cusum_linear` (strongest innovation statistic) | 0.000 | 0.000 | 0.000 | 0.00 | 0.540 | 0.546 |
| `cusum_linear_probed` (D-7a arm 3) | 0.500 | 0.500 | 0.500 | 1.00 | 0.595 | 0.569 |
| **`seq_ibd_signrand`** (candidate fix, R3-1) | 0.435 | **0.430** | **0.566** | 2.17 | **0.750** | **0.826** |

AUC 0.51-0.54 is chance. `Delta_F1(seq_ibd - cusum_actinfo) @500 = +0.077 [+0.011, +0.142]`, which is
**inconclusive** against the pre-registered `delta_F1 = 0.10` — and the +0.077 does not come from the
interventional arm being informative (AUC 0.514); it comes from its calibrator being marginally less
degenerate than the comparator's. In the confounder-**absent** cell the same comparator reaches
AUC 0.981 and F1 0.699, so the comparator implementation is sound and the confounder does exactly
what the design predicts to it; the interventional arm simply never gets off the floor.

The cause is R3-1 below. It is not a budget problem: the candidate fix in the last row uses **the
same 99 probes, the same 5 % budget, the same window and the same isotonic protocol**, and reaches
AUC 0.750/0.826 with `Delta_F1 = +0.430 [+0.331, +0.528]` (SUPERIOR at delta_F1 = 0.10) and is
essentially confounder-insensitive (AUC 0.750 present vs 0.749 absent). So the paper's scientific
hypothesis looks supportable — but not with the statistic draft 2 specifies.

---

## Findings

| ID | Sev | Claim attacked | Evidence | Proposed fix | Fix type |
|---|---|---|---|---|---|
| **R3-1** | **high** | `sequential-ibd-spec.md` sections 3-4: that `a_c` = signed max-\|z\| of probe against task-policy null is a support score, so that `p_c = g(a_c)` with **g non-decreasing** estimates P(c in S^obs,eps). | `sim_d8.py` section G. Mean `a_c` over 12 episodes at registry values (rho_u = 0.8, policy loaded on u so that rho_min >= 0.4 is met): **direct action children +1.04, indirect but action-reachable channels (b1, b3, d0, d1) -0.39, non-reachable channels -0.03.** The reachable-but-indirect channels rank **below** the distractors. Ablation isolates the cause: with W_u = 0 (policy not driven by the shared cause) the ordering is +3.68 / +3.20 / -0.03 and the arm works; with rho_u = 0 it is +1.11 / +0.78 / -0.07. The mechanism is the C4 deviation the spec declares "symmetric across the two arms" (section 2.5 item 4): it is not symmetric. In the null arm a_t, a_{t+1}, a_{t+2} are all about W_u*u_t and add **coherently** over h = 2, 3 because rho_u = 0.8; in the probe arm a_t is i.i.d. and partially cancels against the subsequent policy actions. So the null arm produces *larger* \|increments\| than the probe arm on exactly the channels the action drives indirectly — including the downstream `d` channels that C6/K10 make mandatory. A monotone calibrator cannot repair a non-monotone score. Consequence: AUC 0.514 at the primary offset (1b). Section 2.5.3's registered mitigation does not detect it: the logged `probe_magnitude / policy_action_RMS` was **1.65 in the inverted cell and 3.50 in a monotone cell**, i.e. the ratio is favourable precisely where the statistic is wrong. | Replace the task-policy null with the estimator's **own randomisation**: for each (channel, horizon, actuator k), rank-sum the **signed** increments of probes that used +e_k against those that used -e_k, and set a_c = max over (k, h) of \|z\|. Exchangeability is then exact by construction under "actuator k does not reach c within h", independent of the task policy, of W_u and of rho_u. Same probes, same budget, no extra information. Measured: AUC 0.750 @500 / 0.826 @1000, F1 0.430/0.566, confounder-insensitive (`seq_ibd_signrand` in `sim_d8.output.txt`). Alternatively adopt the paper's own design and run both branches under a dedicated pi_probe, which costs budget the spec already rejected in section 2.5.5. | decision (which statistic) + prose (2.5, 3, 10) |
| **R3-2** | **high** | `roadmap-v4.5-amendments.md` I5 flags D-8's basis as "unverified until another model has attempted to refute it"; `decisions-required.md` D-8(a) claims re-aiming to support correctness "makes the confirmatory contrast one whose outcome is not known in advance". | 1a and 1b above. D-8's alarm finding replicates exactly (P(detect) = P(detect given no event), 0.43 vs 0.43). But the substitute primary is also at chance for the arm as drafted: AUC 0.514, F1 0.077, `Delta_F1 = +0.077 [+0.011, +0.142]` — inconclusive. Meanwhile the *literal* reading of contract H's comparator ("per-channel support scores are innovation statistics") is a change score, not a support score, and scores AUC 0.473 with **zero** channels above the 0.5 threshold in every cell: against that comparator any arm with a non-degenerate calibrator wins by construction. **[opinion]** D-8(a) as written replaces a foregone loss with a contrast that is either degenerate (both arms at zero) or foregone in the other direction, depending on which reading of the comparator is implemented. | Do not freeze D-8(a) on the current spec. Either (i) adopt the R3-1 statistic and re-run the pilot before freezing the primary, or (ii) keep HPDT descriptive and make the primary the **threshold-free** support ranking (AUPRC or AUC) so the outcome is not destroyed by a degenerate calibrator. Separately, define the comparator's per-channel support score explicitly in contract H — "innovation statistics through the calibrator" admits at least two implementations whose F1 differs by 0.70 (AUC 0.473 vs 0.981 in the confounder-absent cell). | decision |
| **R3-3** | **high** | `stage-0a-contract-v3.3.md` section G under D-8a: "R0 validated by TOST inside (-delta0_F1, +delta0_F1) with delta0_F1 = 0.05; interaction I on Delta_F1 within environment as in v4.1 E1"; `roadmap-v4.1-amendments.md` E1 gates R1 superiority on the lower bound of I being > 0. | The R0/interaction rules were carried over from the HPDT design without re-derivation, and they now contradict the working claim stated in `roadmap-v4.5-amendments.md` I1 ("passive residual monitors ... attribute control wrongly under a shared-cause confounder"). (a) **Every confirmatory row in `confirmation-design.csv` has `confounder=present`** (`role=confirmatory_effect` iff present, 1080 rows). In that cell the design *predicts* a large positive Delta_F1, so the R0 non-superiority rule must fail: measured `Delta_F1(R0, present) = +0.077 [+0.011,+0.142]` with the drafted statistic and `+0.430 [+0.331,+0.528]` with a working one — **"NOT validated -> anomaly" in every configuration I ran** (`sim_d8.output.txt` section D). (b) The interaction I = [Delta(R1,pres) - Delta(R1,abs)] - [Delta(R0,pres) - Delta(R0,abs)] is a *double* difference; confounding damages the comparator in **both** regimes, so I cancels: measured **I = -0.242** (drafted arm) and **-0.194** (fixed arm) while the quantity that actually is the confounding effect, [Delta(R0,pres) - Delta(R0,abs)], is **+0.742 / +0.695**. Requiring `lower bound of I > 0` therefore blocks the claim the study exists to make. (c) The seq-IBD arm declares "no residual dynamics model" (spec section 1), so nothing about arm 1 changes between R0 and R1; the R0/R1 contrast is entirely a comparator property and is not an interaction in the usual sense. | Re-derive the decision rules for Delta_F1 from scratch: make the primary contrast the **simple confounding contrast** [Delta_F1(present) - Delta_F1(absent)] within regime, keep R0-present as a *positive* control (large Delta_F1 expected) and R0-**absent** as the non-superiority cell, and demote the double-difference I to descriptive. Add the confounder-absent cells to `role=confirmatory_effect` so both halves of the contrast are confirmatory. | decision |
| **R3-4** | **high** | `stage-0a-contract-v3.3.md` section G: "(P1) Support correctness: per-channel F1 of the **thresholded p_c (threshold 0.5)** against S^obs,eps". | Two defects. (i) **Degeneracy.** `p_c` comes from an isotonic calibrator fitted at a pooled base rate of 0.235 (N_x=10) or 0.123 (N_x=30) — `sim_d8.output.txt` section E. At those rates the fitted probability exceeds 0.5 only in the extreme upper tail, so at the scored offsets the mean number of channels predicted was **0.00** for both comparator arms in three of five cells and 0.10-0.50 for the interventional arm. F1 is then identically 0 for both arms and the primary compares two zeros; `Delta_F1 = +0.000 [+0.000, +0.000]` in the R1 cells. The metric is destroyed before any science happens, and the failure gets worse as `distractor_level` rises, i.e. exactly along the axis the benchmark varies. (ii) **"Per-channel F1" is not operationally defined.** With one scored time point per channel per episode, a genuinely *per-channel* F1 needs a confusion matrix accumulated over seeds, giving C separate F1 values with no stated aggregation; the alternative reading (F1 over the channel set at one time) is what I implemented and is well defined. The two give different numbers. `contract_ref.py` implements neither — `coverage-matrix.md` lists "F1 at offsets" as uncovered. | Score threshold-free (AUPRC primary, AUC secondary) or fix the operating point on the calibration split rather than at 0.5, and state which of the two F1 aggregations is meant, with a worked example, before the pilot. Add `f1_at_offsets` to `contract_ref.py` with a hand-checked fixture so the estimand is executable, per the contract's own rule that an item without a test ID is not implemented. | decision + test |
| **R3-5** | **high** | `stage-0a-contract-v3.3.md` section E3 and `roadmap-v4.4-amendments.md` H6: "each mutant must make >= 1 test fail"; the gate's `23/23 mutants killed`. | `mutants_r3.py` — **7 of 9 new mutants survive with 0 failing tests**, all in the three reference functions added after round 2, none of which the round-2 mutation set touches. Each is shown to differ from the original on an explicit probe input (printed in `mutants_r3.output.txt`). **R3-M1** `count_alarms` ignores the refractory `r` entirely (`[3]` vs `[3, 9]` on `[0,1,1,1,1,1,0,1,1,1,0], p=3, r=20`) — the single fixture places the second raise burst outside both windows, so `r` is never exercised, and ARL_0 under D-2a is computed from this function. **R3-M8** off-by-one refractory (`t < block_until`) -> `[2]` vs `[2, 24]`. **R3-M2** persistence made leaky instead of consecutive (`[]` vs `[5]` on an alternating stream), violating contract section G's "p **consecutive** raises". **R3-M4** `match_alarms` drops `episode_end` from the attribution bound -> a truncated episode scores `detected` where the reference scores `missed` (`([100],['detected'])` vs `([200],['missed'])`), which is contract L11's competing-outcome rule. **R3-M5** `aggregate_primary` uses the median over cells instead of v4.1-E2's equal-weight mean (`{0: 20.0}` vs `{0: 40.0}` on a three-level fixture) — the two-cell fixture has mean = median, so it cannot see this; the identical substitution *is* caught for HPDT (mutant FB-M9/OP-M1). **R3-M7** `s_obs_eps` turns an out-of-range `assign` index from an `IndexError` into a silent `False` (relevant to the morphology event, where `N_b` changes with padding). **R3-M9** `max_pairwise_corr` returns the declared witness pair's correlation instead of the global maximum (0.0 vs 1.0) — the gate cannot distinguish the two readings, so contract E2c's certification is ambiguous in the reference itself. | Add fixtures that exercise each: a `count_alarms` case with a raise burst inside the refractory window and one on its exact boundary; a leaky-persistence case with an alternating stream; a `match_alarms` case whose episode ends inside H_det; an `aggregate_primary` case with >= 3 cells and mean != median; an `s_obs_eps` case with an out-of-range assign; and an E2c case where the witness pair is *not* the maximal pair (then decide which contract E2c means and say so). Then add these seven to `mutants.py`. | test (+ prose for E2c) |
| **R3-6** | **high** | `stage-0a-contract-v3.3.md` gate rule: "A normative item without a test ID is not implemented until it has one"; `readiness-protocol.md` criterion 1, "Coverage matrix: zero uncovered normative items". | `sequential-ibd-spec.md` names seven gate tests — **T-IBD-budget, T-IBD-null-overlap, T-IBD-replay, T-IBD-mono, T-IBD-cal-1, T-IBD-cal-2, T-IBD-cal-3** — and rests three of its four "Resolved" dispositions on them (section 11, IB-2/IB-6/IB-9). `grep -ril` over `executable-proofs/gate/` returns **0 files** for each of the seven. They are also absent from `coverage-matrix.md`, so they do not appear in the uncovered count either: the spec's normative items are invisible to the readiness criterion in both directions. Related: `coverage-matrix.md` is headed "contract v3.1 (+v4.2)" while the frozen contract is v3.3, and it still lists "alarm bookkeeping (p, r, w_T)" as **uncovered** although `count_alarms` and `match_alarms` exist in `contract_ref.py` and have two tests. | Add a row per T-IBD-* id to `coverage-matrix.md` marked uncovered (0A), re-head the matrix at v3.3, and move alarm bookkeeping to covered. Implement T-IBD-budget, T-IBD-null-overlap and T-IBD-mono now — all three are pure-function checks that need no generator (`sim_d8.py` contains a working T-IBD-mono: 252 (stream, h) comparisons, 0 violations). | test + prose |
| **R3-7** | med | `stage-0a-contract-v3.3.md` section 0: ARL_0 calibration "per (environment, regime, confounder, estimator) cell, shared across seeds". | The threshold is **not** constant across `distractor_level` or `delay`, both of which are outside that cell definition. Measured: h = 2.020 at N_x = 10 and h = 2.063 at N_x = 30 for the same (environment, regime, confounder, estimator) — and spec section 10.6 says outright that "h is not transferable across distractor levels". `confirmation-design.csv` in fact emits one `role=calibration` row per (environment, regime, confounder, **level**, **delay**, estimator) — 216 rows over 72 cells — i.e. the matrix already contradicts section 0's cell definition. Whichever is intended, the frozen documents disagree, and the ARL_0 budget accounting (F10, "charged once per cell") is wrong by a factor of 6 under one of them. | Redefine the calibration cell in section 0 as (environment, regime, confounder, distractor_level, delay, estimator) to match the matrix and section 10.6, and restate F10's budget accordingly. | prose |
| **R3-8** | med | `stage-0a-contract-v3.3.md` section G, OP-11: "if either arm of a (seed, cell) pair is outside the ARL band ... a maximum tolerable rate of 10 percent is predeclared (above it **the primary is inconclusive**)". | Under D-8a the primary is Delta_F1, and spec section 6 makes `p_c` provably invariant to h ("set_threshold touches nothing but the comparison in section 5") — I verified this holds in my implementation. So a failure of the ARL_0 band, which is now a purely *descriptive* calibration, can declare the *primary* inconclusive even though the primary does not depend on h at all. Section G's neighbouring sentence, "the primary comparison is made at matched ARL_0, so operating-curve supports cannot be disjoint", is likewise vestigial: the F1 primary is not made at any operating point. Given that the arm's attained band is fragile (my bisection needed 24 x 6,000 steps to hit [946, 1063] and D-2a demands a 95 % interval inside [900, 1100] from >= 400 run lengths), this is a live route to an inconclusive primary for a reason unrelated to the primary. | Restrict OP-11's exclusion rule and the "matched ARL_0" sentence to the **descriptive** HPDT outcome; state that P1 and P2 are computed on all pairs regardless of ARL band, and record band attainment as a covariate. | prose |
| **R3-9** | med | `stage-0a-contract-v3.3.md` section G: "reference `match_alarms(alarm_times, event_times, H_det, r, p) -> (delays, outcomes)` in `contract_ref.py`, tested". | The implemented signature is `match_alarms(alarm_times, event_times, H_det, episode_end)` returning **three** values `(delays, outcomes, false_alarms)`. It takes neither `r` nor `p` (those belong to `count_alarms`) and it takes `episode_end`, which the contract does not mention. An independent black-box acceptance suite written from the contract per E6/L16 would fail to call it. | Correct section G to the implemented signature and state that `count_alarms(raw, p, r)` is the upstream stage. | prose |
| **R3-10** | med | `interface-spec-v3.md`: "`alarm_S = 1 iff stat > h` **after persistence p**"; `sequential-ibd-spec.md` section 5: "`raise_run` counts consecutive **epochs**... Refractory r and alarm counting belong to the harness: the estimator emits the raw persisted raise and the harness calls `contract_ref.count_alarms`". | Contract section 0's `p = 3` is applied **twice, in two different units**: once over epochs inside the estimator (`p_epoch = 3`, spanning 60 steps) and again over steps in `count_alarms(raw, p=3, r=20)`. Because `alarm_S` is held constant between epochs, the second application is nearly vacuous but not exactly so: it adds 3 steps of latency and shifts every counted alarm time, which propagates into HPDT and into the fresh-start ARL_0. The interface says persistence is already applied when `alarm_S` is emitted, so the harness applying it again is a contradiction between two frozen normative files. | Decide where p lives. Recommended: the estimator emits the raw per-epoch raise (`stat > h`, unpersisted) and the harness owns both p and r, with p expressed in epochs for epoch-quantised estimators and the unit recorded in the ledger. | prose + decision |
| **R3-11** | med | `sequential-ibd-spec.md` section 8: "**Count: 19 rows** ... no swept parameter in the confirmatory configuration"; section 11 IB-10 "Resolved ... previously unlisted knobs ... all appear". | Undeclared choices that change the numbers remain. (i) **kappa_tie is used in the section-3 variance formula and never defined** — the tie correction has at least two conventions in circulation and the spec picks neither. (ii) **The "pre-event sub-split" that freezes abar and v (section 5) is not defined**: R_cal is 40 episodes of which half carry an event, so "pre-event sub-split" could be the 20 event-free episodes or the pre-event segments of all 40; the two give different abar, hence different `stat`, hence different h. (iii) **Whether g is pooled across channels or fitted per channel is never stated** — section 4 says "a frozen ... isotonic calibrator", singular, but pooling across heterogeneous channel types (direct body, downstream d, exogenous, padding) is precisely the assumption R3-1 breaks. (iv) The trailing-window convention `(t-W, t]` vs `[t-W, t)` and whether the drop rule applies to unit time or anchor time; with the pseudo-code's anchor-time rule the counts happen to come out at exactly 25/100 (I verified: oldest null anchor is t_p-492 > t_close-500), but that is a coincidence of Pi = 20, M_null = 4 and SP = 3 and it is not stated as a derivation. (v) "Endpoint clamping" of g is named without saying to what values. Also, "19 rows" counts table rows, not parameters: row 1 bundles five constants and rows 3-4 bundle seven more, so the honest count is about 26. | Define kappa_tie by formula; define the pre-event sub-split; state explicitly that g is a single pooled calibrator over channels (and see R3-1 for why that is load-bearing); state the window half-open convention and derive the 25/100 counts; give the clamp values; and label the table "19 rows / 26 parameters". | prose |
| **R3-12** | med | `roadmap-v4.5-amendments.md` I3: "`cusum_linear_probed` added to the confirmation matrix"; F6/H5: the matrix carries roles enabling the interaction gate. | `confirmation-design.csv` (2,700 rows) was regenerated with the third arm but **not** re-aimed for D-8a: `make_confirmation_design.py`'s own docstring still reads "roadmap v4 + amendments v4.1-v4.4 ... D-6 and D-7 pending: episode_len/event_t provisional", every row carries `aggregation=equal_weight_mean_over_levels_and_delays_per_seed` (the HPDT aggregation) and there is **no column for `offsets_F1`, for the primary offset, or for the P2 offsets** — the new primary is nowhere in the frozen run matrix. Separately the role topology is still `role = confirmatory_effect if confounder=="present" else confirmatory_interaction`, so the four cells the interaction needs are split across two role labels and every `confirmatory_effect` row is confounder-present; a selector keyed on role cannot assemble I, and `select_interaction_cells` does not exist in the gate. (Round 2 recorded this; it is unrepaired in the frozen version.) | Regenerate with `offsets_F1`, `primary_offset`, `p2_offsets` and `outcome=F1_vs_S_obs_eps` columns; set `role=confirmatory_effect` for all four (regime x confounder) cells and carry a separate `interaction_group` key; update the generator docstring to v4.5. | prose + test |
| **R3-13** | med | `stage-0a-contract-v3.3.md` section 0 constants registry. | **tau (actuator delay) is not in the registry**, yet C1's "counting delay tau so the first hit is at h = tau+1", C4, `structural_reach_full`, and `sequential-ibd-spec.md` section 2's null guard ("tau_max + max(H) = 5 ... for tau_max = 2") all depend on it. Its only frozen home is the `delay` column of `confirmation-design.csv` ({0, 2}). A reader implementing from the contract alone cannot know that tau_max = 2, and the spec's null-guard proof silently fails at tau = 3. | Add tau and tau_max to section 0 with values {0, 2} and 2, and make `sequential-ibd-spec.md` section 2's guard a stated function of tau_max rather than a fixed 5. | prose |
| **R3-14** | low | `stage-0a-contract-v3.3.md` section 0: "probe_budget = fraction of **environment steps** on which the estimator may apply a randomised probe action (**unit: probe steps / total steps**)". | The parenthesis contradicts the definition: 0.05 of environment steps and 0.05 of total steps differ whenever probe steps are additional. `sequential-ibd-spec.md` section 1 says `update` is called "once per environment step **and** per probe step", which reads as probes being extra, while section 7 asserts "exactly `floor(0.05*T)` ... 100 per 2,000-step episode", which only holds if probes replace policy steps. I implemented the replacing reading and reproduced 99-100 probes per episode with the invariant `n_probe <= floor(0.05*t)` holding at every step. | Pick one and say it once: recommended "a probe step *is* an environment step whose applied action is replaced", which makes section 7 exact and `interface-spec-v3.md`'s `probe(actions)` cost accounting unambiguous. | prose |
| **R3-15** | low | `sequential-ibd-spec.md` section 4 table, "Window memory against offsets ... reported beside every offset", and section 3's "W_steps = 500 is chosen so that at the primary F1 offset 500 the window is **exactly** 100 % post-event". | Recomputed from the actual epoch grid (`sim_d8.output.txt`, header table), every entry is optimistic, because an epoch closes at t_p + max(H) and p_c is read from the most recent epoch <= t: offset 10 -> **0.006** (spec 0.02); 50 -> **0.086** (0.10); 200 -> **0.366** (0.40); 500 -> **0.966**, not 1.00 (the epoch at t = 1483 still holds one probe unit whose four null anchors at 988-997 are pre-event); 1000 -> 1.000 (correct). The "exactly 100 %" claim is false by four null increments. | Recompute the table from the epoch grid and replace "exactly 100 %" with ">= 96 %, reaching 100 % from offset 520". | prose |
| **R3-16** | low | `executable-proofs/gate/mutants.py`, the OP-2 guard added by `roadmap-v4.4-amendments.md` H7: "each mutant differs from the original on at least one input before the run". | The guard is **vacuous for every function added after round 2**. `differs()` short-circuits with `if o is None or name not in PROBES: return True`, and `count_alarms`, `match_alarms` and `aggregate_primary` are in neither `O` nor `PROBES`. Any future mutant of those three is auto-admitted without evidence that it is a mutant at all. Relatedly, my R3-M3 (`match_alarms` with the `t not in used` guard removed) survives the gate **and is an equivalent mutant**: because the attribution bound is `min(e + H_det, next_event, episode_end)`, the per-event windows are disjoint by construction, so the `used` guard is unreachable dead code. That is worth knowing before someone "fixes" a test to kill it. | Add the three functions to `O` and to `PROBES`, and either delete the unreachable `used` guard in `match_alarms` or add a comment recording why it can never fire. | test |
| **R3-17** | low | `freeze-manifest.txt` / version identity. | `confirmation-design.csv` carries `probe_config_hash = f0bc46ab558f`, which `make_confirmation_design.py` computes as `sha256(b"sequential-ibd-spec.md:PENDING_SIGNATURE")`. The frozen version therefore hashes a placeholder for a document the manifest also contains and whose header says "informative until Daniel signs". Signing the spec changes the CSV, which changes `e662b7429b6b347d`, so version 3's identity is not stable across the very event it is waiting for. | Hash the spec's file digest rather than the string "PENDING_SIGNATURE", and regenerate the matrix as part of signature, recording both hashes in the ledger. | prose |
| **R3-18** | low | `sequential-ibd-spec.md` section 5 closing note: "the harness can also report the p_epoch = 1 sequence from the same stream at zero cost, and should". | It is not in `confirmation-design.csv` and not in the ledger row of `interface-spec-v3.md`, so the "should" has no home. Same for section 2.5.3's normative ledger addition (action RMS and `probe_magnitude / policy_action_RMS` per cell) — the ledger row lists neither. My results make the second one worth having even though R3-1 shows it is not sufficient: it was 1.65-3.50 across my cells. | Add `p_epoch_1_alarm_times`, `policy_action_rms` and `probe_mag_over_action_rms` to the ledger row in `interface-spec-v3.md`. | prose |
| **R3-19** | low | `stage-0a-contract-v3.3.md` section J: "the documented command is `python3 -m venv .venv && ... pip install -r requirements.txt && python run_gate.py`. **The readiness criterion is the exit code of that command from a clean checkout**"; `roadmap-v4.2-amendments.md` F2 pins "numpy==2.4.4, pytest==8.3.5, Python 3.12.x". | `run_gate.py` prints the interpreter and numpy version but **enforces neither pin**: it exits 2 only if numpy is unimportable. So the readiness criterion is satisfiable on any interpreter with any numpy. Live evidence from this very round: `review3-gemini/findings.md` records "`run_gate.py` executed cleanly via Python 3.14.7 venv with NumPy 2.5.3 ... Exit code 0 (Success criterion met)" — two minor Python versions and a minor numpy version outside the pins, reported as the criterion being met. (My own run was compliant: Python 3.12.0, numpy 2.4.4.) Contract E4 determinism ("same host bitwise; cross host within tolerance with identical config hash") is listed uncovered, so nothing else catches this. | Have `run_gate.py` compare `platform.python_version()` and `numpy.__version__` against `requirements.txt` and exit 2 with the documented venv instructions on a mismatch, and print the comparison in the one-line summary so a gate report records the environment it was earned in. | test |

---

## Attacks that failed

Recorded so the next reviewer does not repeat them.

1. **"The rank null is not exact under exchangeability."** Section 3 claims the Mann-Whitney null is
   exact, but the 100 null increments are 25 clusters of 4 anchors inside a 12-step stretch, all
   driven by an rho_u = 0.8 process — I expected serious over-dispersion. Measured on channels with
   no action parent, no event (`sim_d8.output.txt`): z_h1 = (mean +0.064, sd 1.046),
   z_h2 = (+0.050, 0.995), z_h3 = (+0.004, 0.985). At most 5 % over-dispersion, and the h = 1 mean
   bias of +0.06 is absorbed into abar. The aggregate a_c has sd 1.420 and P(|a| > 1.96) = 0.137,
   which is exactly what three *independent* z's would give (1 - 0.95^3 = 0.143, sd of the signed
   max about 1.45). The clustering is not the problem; the sign is (R3-1). **The spec's
   null-validity claim survives.**
2. **"`stat` is not really h-independent, so T-IBD-replay and the ARL_0 bisection are unsound."**
   Replicated T-IBD-mono directly: 12 null streams x 22 thresholds = 252 (stream, h-pair)
   comparisons, **0 violations** of "first counted alarm is non-decreasing in h", including through
   `contract_ref.count_alarms` with p = 3 and r = 20. `p_c` was likewise invariant to h. Section 5's
   claims hold as written.
3. **"The 500-step window cannot actually hold 25 probe and 100 null increments."** It can: with
   Pi = 20, M_null = 4 and spacing 3, the oldest null anchor in the window is t_p - 492, inside
   t_close - 500. The stated counts are exact (though not derived in the spec — R3-11 iv).
4. **"M_null = 4 does not keep the two-sample variance within 25 % of the infinite-null limit."**
   It does: 1/n_P + 1/n_N with n_N = 4*n_P gives exactly 1.25x. Section 8 row 8 is correct.
5. **"The hard budget cap can be violated."** It cannot, with `reservoir_0 = 0`: I instrumented
   `n_probe <= floor(0.05*t)` at every step of every episode and it never failed; 99 probes in a
   2,000-step episode. IB-9 is genuinely resolved.
6. **"rho_min >= 0.4 and a closed-loop feedback policy are incompatible."** I first measured
   max|corr(a_k, x_j)| = 0.079 and thought the confounding floor was unreachable under negative
   feedback (which cancels the u-component of the action). It is reachable — but only for
   fast-mixing distractors: at rho_x = 0.9 the best I could do at a realistic feedback gain was
   0.19, while at rho_x = 0.5 the same policy reaches 0.47. **[opinion]** This is not a defect but it
   is a silent selection effect worth one sentence in the paper: the rho_min rejection sampler will
   preferentially retain instances with fast-mixing distractors and weakly-fed-back policies.
7. **"Sign-flip blindness (K8, g' = -1) is a bug."** Section 10.7 predicts the arm is correctly blind
   to it because increments are absolute and C3 keeps the channel. That is right, and
   `test_C3_gain_*` already pins the C3 side.

---

## Which findings are in NEW categories relative to rounds 1-2

Judged against the category list in `readiness-protocol.md`'s round log (rounds 1-2 opened: prior
art; estimand; mathematics; physics and scope; proofs-were-not-tests; interface completeness;
statistical inference design; oracle certification statistics; comparator identity; confirmatory-
estimator specification; statistical power; amendment drift; freeze integrity; rare-event calibration
precision; role topology; post-termination missingness). I read no round-1 or round-2 `findings.md`
before writing the above.

**New categories opened this round (three):**

- **Estimand-estimator sign validity (R3-1, R3-2).** Round 2's "confirmatory-estimator specification"
  was that the arm had no specification. This is different: the arm now *has* a specification, and
  its per-channel statistic is provably **anti-monotone** in the estimand on instances the contract
  itself mandates (rho_u = 0.8 plus rho_min >= 0.4). No previous round asked whether a specified
  estimator's score is ordered the same way as the ground truth it is calibrated against.
- **Primary-metric operationalisation (R3-4).** That a fixed 0.5 threshold on a calibrated
  probability at a 0.12-0.24 base rate makes the primary identically zero for both arms — and that
  "per-channel F1" has two inequivalent readings — is a defect in the *measurement instrument*, not
  in power, inference design or the estimand.
- **Decision rules inconsistent with the stated working claim (R3-3, R3-8).** Round 2's "amendment
  drift" was textual staleness. This is a logical inconsistency: rules carried over from the HPDT
  design would, if executed as written, classify the paper's own predicted result as an anomaly and
  gate it on a double difference the mechanism predicts to be about 0.

**Not new in category, but unrepaired or newly instantiated:** R3-5 and R3-16 (gate blind spots
outside the author's fixtures — round 2); R3-6, R3-12, R3-17 (freeze integrity / amendment drift —
round 2); R3-7 (rare-event calibration precision — round 2, here as a cell-granularity mismatch);
R3-9, R3-10, R3-18 (interface completeness — round 1); R3-19 (environment reproducibility — round 1, CX-02/GM-9, here as non-enforcement); R3-11, R3-13, R3-14, R3-15 (mathematics and
specification precision — rounds 1-2).

**[opinion]** The stopping rule in `readiness-protocol.md` "Convergence rule" item 5 is not met and
is not close: this round produced three high findings in one previously-unopened category and seven
surviving mutants. The specific thing I would not do is sign `sequential-ibd-spec.md` — R3-1 is a
property of the statistic, not of the constants, and no amount of threshold or budget tuning fixes a
score whose sign is wrong on the downstream channels the contract makes mandatory.
