# D-9 adjudication (verification round, 7 September 2026)

Reviewers: Codex and Gemini, each with an independent simulation of a contract-B instance and both statistics on identical probes and calibration. Author adjudicates; hash unchanged during the round (808ab3be48001e5e).

## D-9.1 — VERIFIED by two models. Adopted.

| | Opus (proposer) | Codex | Gemini |
|---|---|---|---|
| AUC at 500 / 1000, confounder present | 0.750 / 0.826 | 0.770 / 0.818 (mean of N_x 10, 30) | 0.813 / 0.732 (N_x 10); 0.811 at 500 (N_x 30) |
| Confounder sensitivity | insensitive | ΔAUC 0.01 to 0.045 | ΔAUC < 0.02 |
| Draft-2 sign inversion on reachable-indirect channels | reproduced | reproduced at N_x = 30; weakly positive at N_x = 10 (instance-dependent) | reproduced (−0.39, −0.15) |
| D-7a probed comparator closes the gap? | no | no (within 0.003 AUPRC of passive) | no |

The sign-randomised contrast works at a 5 percent budget, is insensitive to the confounder by construction, and keeps the correct class order on every instance tested. Codex's caveat is recorded: the draft-2 inversion is instance-dependent, so the robust claim about draft 2 is "weak or non-monotone ranking on admissible instances", not a universal sign.

**One material caveat, disclosed.** Against the strongest passive comparator (two-sided standardised innovation shift with an action-loading baseline, Codex's formulation), the AUPRC advantage is about +0.14 with a 30-seed interval whose lower bound is below 0.10; on AUC it is +0.20 to +0.25 with lower bounds above 0.13. Against a weaker comparator reading the AUPRC advantage is +0.43. **The comparator choice decides the margin.** The rule adopted below fixes the comparator on principle (the strongest passive reading) and the primary metric on scale (AUC), and the paper must disclose that these were frozen after pilot simulations that already showed the arm clears them. These simulations are pilots; confirmation uses the frozen matrix with fresh seeds and instances.

## D-9.2 — adopted with changes (both reviewers)

AUPRC is prevalence-dependent: chance AUPRC falls from 0.14 at N_x = 10 to 0.03 at N_x = 100, so a scalar 0.10 margin is impossible at high distractor counts, and copies or padding change the baseline without changing the causal object. Adopted: **threshold-free AUC is the primary** (scale-invariant across distractor levels), δ_AUC = 0.10; AUPRC co-reported per episode with its prevalence and lift over prevalence, with a grouped variant collapsing copies and padding as a sensitivity; F1 at an operating point chosen on a **separate** validation split is secondary. Per-episode paired scoring, equal weight over predeclared cells, never pooled across cells.

## D-9.3 — adopted with Codex's correction

"TOST non-superiority" was incoherent. Rules: confounding benefit = [Δ_AUC(present) − Δ_AUC(absent)] within regime, smallest effect 0.10; R0-present is a positive control at the same margin; R0-absent is an **equivalence** cell with TOST at ±0.05 AUC; the double-difference interaction is descriptive. Prevalence-adjusted AUPRC repeated as a sensitivity, not a gate.

## D-9.4 — adopted (both)

A normative comparator specification is a prerequisite. Frozen on principle: the passive support score is the two-sided standardised innovation-mean shift over a trailing window, oriented so higher means retained support, with the standardised action loading as the baseline support term; arm-specific isotonic calibrator; separate calibration for the probed arm because probe shocks change the null. Full field list per Codex D-9.4. Drafted by a fresh-context agent, reviewed cross-model.

## D-9.5 — adopted with changes (both)

Two tiers: (1) online support ranking, which is invariant to any monotone calibrator and therefore does not use the supervised split at all; (2) supervised probability calibration and operating-point transfer, with calibrator fit and threshold selection on **separate** episode splits (24 fit, 16 validation, half event-carrying each), evaluated leave-one-instance-out with held-out event times. "Uncalibrated proper scores" is dropped as undefined; cross-fitted Brier and log loss of the frozen calibrated probabilities are reported.

## Carried into the IBD spec draft 3 (D9-codex-3)

Minimum observations per sign group (n_min = 3, else the cell contributes zero), tie correction formula, z cap, window endpoints, epoch timing, hand fixtures.

## Gate

Three new survivors, all valid: deletion of every A_w and A_x edge in `build_adjacency` (Codex); signed instead of absolute `pairwise_corr` (Gemini); strict upper boundary in `match_alarms` at t = e + H_det (Gemini). Repaired and registered after both reported.

## Process

Rule I5/J8 satisfied for D-9.1: single-model proposal, two-model reproduction, then freeze. The disclosed caveat about pilot-informed freezing is carried into the paper's methods section as a stated limitation.
