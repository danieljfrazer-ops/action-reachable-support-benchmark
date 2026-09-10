# Round 3 adjudication and tally (frozen e662b7429b6b347d, design re-baseline)

Date: 7 September 2026. Reviewers: Codex (14 findings), Gemini (9), fresh-context Claude Opus (19); all three built independent simulations of a contract-B instance and the draft-2 detector. Author (Claude, this context) adjudicates and does not review. Hash verified unchanged before and after the round.

## 1. Headline: D-8's direction survives independent refutation; its operationalisation does not

All three simulations reproduce the alarm-channel result that motivated D-8: at the frozen constants the interventional arm's alarm probability inside the detection horizon is indistinguishable from a no-event control (Opus 0.43 vs 0.43; Gemini 0.35 vs 0.37; Codex 0.33 vs 0.23), while the passive residual CUSUM detects with probability 1. Demoting detection time to descriptive stands.

All three also find that the substitute primary, F1 of thresholded support probabilities, fails under draft 2, for three distinct reasons that compound:
- **The statistic is anti-monotone in the estimand on contract-mandated instances** (Opus R3-1, adjudicated valid by Codex). Under the autocorrelated shared cause and the confounding floor, the contrast between probe steps and task-policy steps ranks action-reachable indirect channels, including the mandatory downstream ones, below the unreachable distractors. A monotone calibrator cannot repair an inverted score. Discrimination against the true support is at chance (AUC 0.51). With the confounder removed the ordering is correct and the arm works.
- **The fixed 0.5 threshold on a calibrator at a low base rate makes F1 identically zero for both arms** in most cells (Opus R3-4, Codex CX-01/12, Gemini GM3-4). Codex shows a permitted high-distractor cell where the calibration split cannot meet the spec's own minority-share gate, forcing a constant predictor by construction.
- **The comparator's per-channel support score is unspecified** (Codex CX-02, Opus R3-2, Gemini GM3-2 as judgment). Two permitted readings differ by 0.7 in F1. Gemini's reported comparator advantage used an oracle mask the roadmap excludes and is inadmissible as a number; its conclusion still agrees.

**Constructive result.** Opus found a budget-neutral statistic that removes the task-policy null entirely: rank-sum the signed increments of probes using +e_k against those using −e_k, using only the estimator's own randomisation. Exchangeability then holds by construction under "actuator k does not reach c", independent of the policy and the confounder. Measured with the same probes, budget, window and calibration protocol: discrimination 0.75 at offset 500 and 0.83 at 1000, F1 0.43 and 0.57, insensitive to the confounder, and a clear advantage over the comparator. Codex adjudicated the reasoning valid. **It has been simulated by one model only and is flagged unverified until a second model reproduces it** (rule I5).

## 2. Convergent findings applied (two-of-three or executable)

| Topic | Reviewers | Disposition |
|---|---|---|
| Decision rules never re-derived for the F1 primary; clean regime would flag the expected result as an anomaly; the double-difference interaction cancels the confounding effect it should detect | Opus R3-3, Codex CX-09 | **D-9** (design); rules to be re-derived around the simple confounding contrast |
| Seven new surviving mutants, all in functions added after round 2; mutant-distinctness guard vacuous for those functions; two-cell aggregation fixture cannot separate mean from median; exact-boundary alarm and refractory cases untested | Opus R3-5/16, Gemini GM3-1/5/6, Codex CX-03 | **Gate repaired**: fixtures added, all registered, guard extended |
| T-IBD-* tests named by the spec do not exist and are invisible to the coverage count; matrix still headed v3.1; alarm bookkeeping mislabelled | Opus R3-6 | Coverage matrix corrected; T-IBD-mono and T-IBD-budget implementable now, others 0A |
| Calibration cell omits distractor level and delay although the threshold depends on both and the matrix already emits per-level rows | Opus R3-7, Codex CX-06 | Contract §0 cell redefined; budget accounting restated |
| ARL-band eligibility must not gate the F1 primary, which is threshold-invariant | Opus R3-8, Codex CX-08 | Contract G restricted to the descriptive outcome |
| `match_alarms` normative signature wrong; persistence applied twice in two units (estimator epochs, harness steps) | Opus R3-9/10, Codex CX-05/14 | Signature corrected; persistence ownership decided: estimator emits raw exceedance, harness owns p (in epochs for epoch-quantised arms) and r |
| Hidden knobs in the spec (tie correction, pre-event sub-split, pooled vs per-channel calibrator, window convention, clamp values); τ absent from the registry; probe-step unit ambiguous (replace vs insert) | Opus R3-11/13/14, Codex CX-11 | Registry: τ ∈ {0, 2}, τ_max = 2; "a probe step is an environment step whose action is replaced"; spec draft 3 must define the rest |
| Matrix not re-aimed for F1 (no offsets columns; role split hides the four interaction cells; stale generator docstring) | Opus R3-12, Codex CX-03 | Regenerated with outcome and offset columns, all four cells confirmatory, `interaction_group` key |
| Environment pins not enforced by the runner (Gemini's own run passed on Python 3.14 / numpy 2.5.3) | Opus R3-19, Codex CX-13 | `run_gate.py` now exits 2 on a pin mismatch |
| Support horizon H is not a physical washout; prior probe effects can persist above ε into the next null window in slow instances | Codex CX-04 | Spec draft 3 must define washout from the impulse response per instance, or use snapshot-and-branch nulls |
| Oracle-labelled isotonic calibration on event-carrying episodes makes the task partly supervised event transfer | Codex CX-07 | D-9: state the task honestly; report threshold-free and uncalibrated proper scores beside F1 |
| Probe-config hash is a placeholder string | Opus R3-17 | Hash the spec file digest at signature |
| Ledger lacks fields the spec declares | Opus R3-18 | Interface v3 ledger row extended |

## 3. Rejected or held

- Gemini GM3-3 ("rank null broken by autocorrelation, 13.7 percent tail"): **invalid** as a statistical failure. Codex and Opus both measured near-nominal per-horizon tails; the 13.7 percent is the expected maximum-of-three effect. The word "exact" is removed from the spec (prose).
- Gemini GM3-9 (stale per-step outputs): **invalid**; piecewise-constant outputs are permitted; interface wording clarified.
- Gemini GM3-7 (periodic probing aliasing) and GM3-8 (window memory under multi-event schedules): **judgment calls**. Confirmation uses a single-event schedule; the spec must state that multi-event schedules are exploratory for this arm and declare a window policy if used. Jitter is deferred to draft 3 as an option.
- Gemini GM3-2's number (comparator F1 0.857): inadmissible (oracle mask); its conclusion is recorded as agreeing.

## 4. Decision required: D-9 (supersedes the operationalisation in D-8a; direction unchanged)

| Element | Proposal | Basis |
|---|---|---|
| Statistic | Sign-randomised contrast: per (channel, horizon, actuator), rank-sum signed increments after +e_k probes against −e_k probes; a_c = max over (k, h) of |z|. No task-policy null. | Opus R3-1; Codex valid; **single-model simulation, unverified** |
| Primary outcome | Threshold-free support ranking (AUPRC primary, AUC secondary) at offsets {200, 500, 1000}; F1 reported at an operating point chosen on the calibration split, not 0.5 | R3-2, R3-4, CX-12, GM3-4 |
| Decision rules | Primary contrast = [Δ(present) − Δ(absent)] within regime on the ranking metric; R0-present is a positive control; R0-absent is the non-superiority (TOST) cell; the double-difference interaction is descriptive | R3-3, CX-09 |
| Comparator | A normative comparator spec parallel to the IBD spec: per-channel support score defined (two-sided standardised innovation shift), calibration protocol, arm-specific calibrator | CX-02, R3-2 |
| Task statement | "Supervised calibration on a declared split plus online estimation"; uncalibrated proper scores reported beside the primary | CX-07 |
| Verification before freeze | A second model reproduces the sign-randomised result on its own instance before D-9 is frozen; then spec draft 3 | rule I5 |

Recommendation: adopt D-9 as proposed, with the verification step mandatory.

## 5. Round outcome against the stopping rule

Not met: high findings present and three new categories opened (estimand-estimator sign validity; primary-metric operationalisation; decision rules inconsistent with the working claim). But the round did what the protocol is for: three models converged on the same defects, refuted the author's operationalisation of D-8 while confirming its direction, and one produced a candidate fix that another rated sound. What the author writes next is smaller than what it was asked to write last time, and all of it is either a decision for Daniel or a test.
