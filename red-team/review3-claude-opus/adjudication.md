# Adjudication — round 3, frozen version `e662b7429b6b347d`

Reviewer: Claude Opus. Written after `review3-claude-opus/findings.md` was complete, per the round-3
protocol. One line of reason per finding.

## Availability of the other reviewers' findings

- **`review3-gemini/findings.md` — present** (163 lines, 9 findings GM3-1..GM3-9). Adjudicated below.
- **`review3-codex/findings.md` — ABSENT at the time of writing.** The folder contains simulation
  artefacts (`independent_d8_simulation.py`, five `independent_d8_summary*.json`, five row CSVs) and
  `surviving_mutant_aggregate_ignores_delay.py`, but no findings document, so there is nothing to
  adjudicate. **[opinion]** For the record, two of Codex's numbers corroborate findings of mine
  without my having read any prose from them: `independent_d8_summary_nx10.json` reports
  `event_alarm_probability_200 = 0.36` against `no_event_alarm_probability_same_window = 0.26`
  (the D-8 alarm-power finding, my §1a), and `calibrator_max_probability.cusum = 0.306` with
  `cusum_positive_fraction = 0.0` at all three offsets (the fixed-0.5-threshold degeneracy, my R3-4).
  Their `surviving_mutant_aggregate_ignores_delay.py` is a third independent `aggregate_primary`
  survivor, distinct from mine (R3-M5) and Gemini's (GM3-1), which strengthens R3-5/GM3-1 rather
  than duplicating it.

## Gemini (`review3-gemini/findings.md`)

| Their ID | Verdict | Reason (one line) |
|---|---|---|
| **GM3-1** — `aggregate_primary` median mutant survives; two-cell fixture has mean ≡ median | **valid** | Independently reproduced and executed as my R3-M5: 0 failing tests, and the mutant differs from the reference (`{0: 20.0}` vs `{0: 40.0}`) on a three-level fixture. |
| **GM3-2** — re-aiming to F1 does not rescue the arm; reopen D-8 (evidence: IBD F1 0.150 vs CUSUM 0.857, Δ_F1 = −0.707) | **judgment call** | The *conclusion* that D-8(a) does not rescue the arm is right and I reached it independently (my AUC 0.51 at offset 500), but the *evidence* is not admissible: `sim_d8_gemini.py` line 336 computes `pred_cusum = (z_res < 3.0) & S_pre`, masking the comparator's predictions with the oracle's ground-truth pre-event support, so no distractor can ever be a false positive and the confounding failure mode the benchmark exists to measure is switched off — that is the appendix "oracle-coordinate CUSUM" that roadmap D9 and contract H explicitly exclude from the confirmatory pair; with a channel-agnostic comparator I measured Δ_F1 = **+0.077**, not −0.707, and Codex's independent run gives `cusum_f1 = 0.0`. |
| **GM3-3** — the Mann–Whitney null is not exact; a_c has sd 1.42 and P(\|a_c\|>1.96) ≈ 13.7 % | **invalid** | The measurement is right and the inference from it is wrong: a_c is by construction a signed max-\|z\| over three horizons, for which three *independent* standard normals already give sd ≈ 1.45 and P = 1 − 0.95³ = 0.143 — I measured the per-horizon z's directly and got sd 1.046 / 0.995 / 0.985, i.e. ≤ 5 % over-dispersion, so this is the expected multiplicity (which spec §3 says is absorbed into h and g), not an exchangeability violation. |
| **GM3-4** — isotonic calibration is contaminated by the transition band, and the fixed 0.5 threshold collapses F1 to zero under low prevalence | **valid** | Both halves independently reproduced: refitting g with the [event, event+W_steps) band excluded changed F1 from 0.077 to 0.093 (contamination is real but second-order), and at a pooled base rate of 0.123–0.235 the comparator arms predicted **0.00** channels at every scored offset in three of five cells — my R3-4, and Codex's `calibrator_max_probability.cusum = 0.306` shows the same thing. |
| **GM3-5** — `match_alarms` mutant with `e <= t` (alarm at the event step counts as a detection) survives the gate | **valid** | Executed it myself: 0 failing tests, and it differs from the reference on `([1000],[1000],200,2000)` — `([200],['missed'])` vs `([0],['detected'])`. This is an eighth surviving mutant that I did not attempt; it belongs in the repair set alongside my seven. |
| **GM3-6** — `count_alarms` with `block_until = t + r − 1` survives | **valid** | Identical to my R3-M8, independently found and executed: 0 failing tests, `[2]` vs `[2, 24]` on a raise burst placed on the refractory boundary. |
| **GM3-7** — deterministic Π = 20 probing causes stroboscopic aliasing with periodic dynamics (Pendulum limit cycle) | **judgment call** | Mechanically plausible for Pendulum-v1 and worth a sensitivity cell, but no evidence is offered and it is not what carries identifiability — spec §2 severs C→a by randomising the probe *action*, not its timing; the proposed jitter also breaks the `reservoir_0 = 0` exact-budget invariant that IB-9 was created to guarantee, a cost the finding does not price. |
| **GM3-8** — the never-resetting 500-step window blinds the arm on multi-event (ABA/ABC) schedules | **valid** | Contract D admits ABA and ABC schedules with `event_spacing = H_det + w_T = 250`, which is **less than** `W_steps = 500`, so two consecutive events provably share a window; spec §3 states "it never resets" and §4 tabulates window memory only for a single event at t = 1000, so the consequence for the contract's own multi-event schedules is undeclared. I missed this. |
| **GM3-9** — `update` returns stale cached p_c and stat on 19 of every 20 steps, against interface v3's per-step semantics | **judgment call** | The behaviour is disclosed, not hidden — spec §4 says p_c is "emitted every step from a cache refreshed at every epoch" — so this is a documentation disagreement between two frozen files rather than a spec violation; their proposed fix (say so in `interface-spec-v3.md`) is the right one, and it overlaps my R3-10 on where persistence lives. |

## Where Gemini and I disagree materially, and what would settle it

**[opinion]** The only substantive disagreement is GM3-2's sign. Gemini reports the passive
comparator beating the interventional arm by 0.71 F1; I report the two arms both at chance in the
confirmatory (confounder-present) cells, with the comparator reaching AUC 0.981 only when the
confounder is switched **off**. The difference is entirely attributable to the oracle mask on line
336 of their script. This matters for Daniel's decision: under their number the right conclusion is
"the interventional approach loses on every outcome"; under mine it is "the drafted *statistic* is
broken, the approach is not" — my `seq_ibd_signrand` variant, same budget and same probes, reaches
AUC 0.750/0.826 and Δ_F1 = +0.430 against a channel-agnostic comparator. The settling experiment is
cheap and I recommend it before any decision on D-8: re-run Gemini's script with
`pred_cusum = (z_res < 3.0)` (no `& S_pre`) and report both numbers.

## Convergence across the three round-3 reviewers, so far

Convergent with executable evidence from at least two of us: the D-8 alarm-power finding (me,
Gemini, Codex); the fixed-0.5-threshold degeneracy of the new primary (me R3-4, Gemini GM3-4, Codex
`cusum_positive_fraction = 0.0`); surviving mutants in the post-round-2 reference functions
`aggregate_primary`, `count_alarms` and `match_alarms` (me 7, Gemini 3, Codex ≥ 1, with three
*distinct* `aggregate_primary` survivors between us); and the conclusion that D-8(a) as written does
not rescue the confirmatory contrast (me, Gemini).
