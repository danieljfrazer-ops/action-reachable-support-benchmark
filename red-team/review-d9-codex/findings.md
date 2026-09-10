# D-9 independent review — Codex

**Date:** 7 September 2026  
**Scope:** only `docs/archive/red-team/`; new work is confined to `review-d9-codex/`.  
**Evidence:** `sim_d9.py`, captured `sim_d9.output.txt`, `gate_baseline.output.txt`, and the surviving-mutant script/output in this folder.  
**Environment:** Python 3.12.0, NumPy 2.4.4. The full five-cell simulation took 362.2 seconds. No seed-count reduction was needed: every cell used 40 calibration episodes (20 event-carrying) plus 30 event and 30 no-event scored seeds.

## One-line verdicts

- **D-9.1 — adopt with changes.** The independent instance reproduces the candidate statistic's useful ranking and confounder robustness at the frozen 5% probe budget; the mean AUC is 0.770 at offset 500 and 0.818 at 1000 across the two confounder-present distractor levels. The draft must specify small-group handling and weaken its exchangeability wording.
- **D-9.2 — adopt with changes.** AUPRC is the right headline family for rare support, but raw channel-weighted AUPRC is not comparable across padding/copy prevalence and must not be pooled across cells.
- **D-9.3 — adopt with changes.** The simple within-regime confounding contrast is coherent; “TOST non-superiority” is not. Use equivalence or one-sided non-superiority deliberately, with different margins.
- **D-9.4 — adopt.** A normative comparator specification is a prerequisite, not optional documentation.
- **D-9.5 — adopt with changes.** “Supervised calibration plus online estimation” is honest, but the calibrator fit and operating-point selection need separate splits; “uncalibrated proper score” is not a coherent metric unless a probability link is frozen.

## Technical summary

D-9.1 is independently reproduced in direction and approximately in magnitude. At `N_x=10`, statistic B obtains AUC 0.743/0.773 at offsets 500/1000 with the confounder present, versus Claude's 0.750/0.826. At `N_x=30`, it obtains 0.797/0.862. Equal-weighting those two cells gives 0.770/0.818, reasonably close to the claimed 0.75/0.83. Removing the confounder changes AUC by only 0.010–0.045 at offset 500 and 0.020 at offset 1000. Under confounding, B's AUPRC advantage over the passive comparator is 0.352 (`N_x=10`) and 0.453 (`N_x=30`) at offset 500—comfortably beyond an absolute 0.10 margin. The D-7a probed comparator is essentially unchanged and does not close the gap.

The exact R3-1 sign inversion is not universal. In the fault-free `N_x=10` cell, draft-2 mean `a_c` is 1.700/0.144/−0.017 for direct/reachable-indirect/non-reachable classes: indirect channels remain weakly above non-reachable ones. At `N_x=30`, it is 1.661/−0.169/−0.066, reproducing the inversion. Thus the causal critique survives, but the sign itself depends on instance and finite-sample composition. Statistic B maintains the correct class order in both cells.

The simulation follows the paper's central distinction: observational association can be confounded, whereas randomized action interventions target causal reach. The original IBD method uses separate baseline and randomized-action branches and dimension-wise two-sample tests; this review tests the budget-neutral within-randomization sign contrast proposed for the sequential setting, not a reproduction of the paper's full algorithm ([Liu, Cheng & Bogdan, *Discovering What You Can Control*, arXiv:2603.18257v2](https://arxiv.org/abs/2603.18257)).

## Scope, statistic, comparator, and scoring definitions

The independently chosen family-L instance uses `N_b=4`, `N_d=2`, `N_w=4`, `K=2`, `N_x∈{10,30}`, registry noise scales, `rho_u=0.8`, `f_conf=0.5`, `tau=0`, four padding channels, and a complete loss of actuator 0 at `t=1000`. Pre/post operational observed support sizes are 6/3. The confounder-present certification gives `max |corr(a_k,x_j)|=0.501/0.505` and saturation 0.0030/0.0015 for `N_x=10/30`; all stability bounds and the operational-effect margin pass. Each 2,000-step probed episode uses 99 replacement probes (the first admissible probe is step 20), drawn i.i.d. from the four signed unit basis vectors.

- **A, draft 2:** for each channel and `h∈{1,2,3}`, tie-corrected Mann–Whitney `z` compares absolute probe increments with the four matched task-policy null increments anchored 3, 6, 9, and 12 steps before each probe. `a_c` is the signed `z` having maximum absolute value.
- **B, D-9.1:** for each channel, horizon, and actuator, tie-corrected Mann–Whitney `z` compares signed increments after `+e_k` probes with signed increments after `−e_k` probes. `a_c=max_{k,h}|z|`. A cell is usable with at least three observations of each sign; otherwise its contribution is zero. This small-group rule is currently missing from D-9.
- **Window:** both statistics use the same probe epochs and trailing 500 environment steps.
- **Calibration:** each arm gets its own non-decreasing PAVA isotonic map, fitted over all eligible calibration epochs and channels from 40 whole episodes, half event-carrying. The “best” operating threshold is the largest tied maximizer of micro-F1 on that same calibration split. This faithfully exposes the current protocol's optimism; it is not endorsed below.
- **Comparator:** one multivariate linear predictor `o_(t+1)=[o_t,a_t,1] beta` is least-squares fitted on the 20 fault-free, in-distribution, non-probed calibration episodes. Let innovations be `r_tc`, training mean/scale be `mu_c,sigma_c`, and the standardized action loading be `l_c=||beta_(a,c)||_2/sigma_c`. Its declared raw support score is

  `q_c(t) = l_c - | sqrt(n) × mean_{i=t-n,...,t-1} ((r_ic-mu_c)/sigma_c) |`, with `n=min(500,t)`.

  This is a two-sided standardized innovation-mean shift, oriented so higher means retained support. The baseline action loading is necessary: a shift alone detects change, not membership in support. The D-7a arm applies the identical fitted predictor, score, and CUSUM to the stream containing the exact probe injections used by A/B. Each comparator arm has a separate isotonic map and alarm threshold.
- **Scoring unit:** AUC, non-interpolated average precision (reported as AUPRC), F1, Brier, and log loss are calculated across channels within each episode/offset and then averaged over 30 seeds. This avoids allowing large-`N_x` cells to dominate by row count. `F1@0.5` thresholds calibrated probability at 0.5; `F1*` uses the calibration-selected threshold.

## Reproduction table — event-carrying episodes

Each entry is **AUC / AUPRC / F1@0.5 / F1\***. `Cmp` is passive; `Cmp+P` is D-7a on the identically probed stream.

| confounder | N_x | offset | A draft 2 | B sign-randomized | Cmp | Cmp+P |
|---|---:|---:|---:|---:|---:|---:|
| present | 10 | 200 | .570 / .371 / .174 / .230 | .761 / .558 / .379 / .407 | .497 / .167 / .000 / .232 | .507 / .184 / .000 / .232 |
| present | 10 | 500 | .625 / .412 / .157 / .270 | .743 / .538 / .406 / .388 | .562 / .186 / .000 / .233 | .565 / .188 / .000 / .229 |
| present | 10 | 1000 | .578 / .389 / .190 / .267 | .773 / .578 / .367 / .467 | .530 / .180 / .000 / .232 | .547 / .217 / .000 / .233 |
| absent | 10 | 200 | .574 / .355 / .177 / .224 | .740 / .538 / .358 / .392 | .649 / .477 / .450 / .450 | .648 / .469 / .457 / .453 |
| absent | 10 | 500 | .606 / .386 / .150 / .252 | .733 / .537 / .410 / .381 | .706 / .535 / .450 / .466 | .708 / .532 / .447 / .469 |
| absent | 10 | 1000 | .569 / .367 / .143 / .245 | .753 / .578 / .363 / .470 | .662 / .505 / .487 / .467 | .661 / .503 / .487 / .462 |
| present | 30 | 200 | .584 / .302 / .130 / .221 | .761 / .465 / .317 / .304 | .428 / .078 / .000 / .129 | .448 / .087 / .000 / .131 |
| present | 30 | 500 | .599 / .303 / .100 / .247 | .797 / .536 / .356 / .390 | .463 / .083 / .000 / .130 | .474 / .086 / .000 / .130 |
| present | 30 | 1000 | .605 / .310 / .133 / .265 | .862 / .600 / .339 / .441 | .443 / .081 / .000 / .134 | .461 / .089 / .000 / .132 |
| absent | 30 | 200 | .613 / .284 / .117 / .192 | .767 / .446 / .322 / .319 | .673 / .426 / .447 / .447 | .671 / .417 / .447 / .440 |
| absent | 30 | 500 | .588 / .259 / .083 / .215 | .752 / .468 / .349 / .319 | .701 / .431 / .450 / .450 | .704 / .427 / .453 / .453 |
| absent | 30 | 1000 | .607 / .292 / .117 / .245 | .842 / .555 / .332 / .387 | .658 / .439 / .483 / .483 | .660 / .448 / .483 / .483 |

The comparator's `F1@0.5=0` under confounding repeats the base-rate/calibration pathology; calibration-selected F1 remains secondary and unstable. In several test cells `F1*` is below `F1@0.5`, showing that choosing the threshold on the same data used to fit the isotonic map does not guarantee transfer.

## No-event control

The same pseudo-offsets are scored with no actuator event and the six-channel pre-event support. Entries again are **AUC / AUPRC / F1@0.5 / F1\***.

| confounder | N_x | offset | A draft 2 | B sign-randomized | Cmp | Cmp+P |
|---|---:|---:|---:|---:|---:|---:|
| present | 10 | 200 | .567 / .477 / .180 / .353 | .774 / .691 / .410 / .555 | .487 / .271 / .000 / .404 | .499 / .291 / .000 / .403 |
| present | 10 | 500 | .621 / .526 / .198 / .403 | .781 / .699 / .431 / .550 | .527 / .286 / .000 / .406 | .531 / .288 / .000 / .404 |
| present | 10 | 1000 | .614 / .509 / .197 / .426 | .773 / .689 / .424 / .566 | .487 / .273 / .000 / .403 | .509 / .312 / .000 / .404 |
| absent | 10 | 200 | .571 / .464 / .171 / .349 | .747 / .654 / .401 / .546 | .674 / .606 / .493 / .513 | .671 / .602 / .493 / .504 |
| absent | 10 | 500 | .599 / .487 / .176 / .383 | .766 / .685 / .436 / .542 | .726 / .645 / .493 / .513 | .728 / .647 / .500 / .507 |
| absent | 10 | 1000 | .602 / .488 / .169 / .407 | .760 / .691 / .425 / .568 | .682 / .627 / .500 / .505 | .684 / .630 / .500 / .500 |
| present | 30 | 200 | .555 / .351 / .120 / .281 | .766 / .585 / .340 / .429 | .416 / .130 / .000 / .239 | .435 / .140 / .000 / .236 |
| present | 30 | 500 | .581 / .366 / .108 / .293 | .779 / .587 / .340 / .443 | .433 / .134 / .000 / .245 | .442 / .136 / .000 / .245 |
| present | 30 | 1000 | .621 / .412 / .129 / .360 | .839 / .664 / .391 / .501 | .407 / .129 / .000 / .239 | .421 / .134 / .000 / .238 |
| absent | 30 | 200 | .579 / .334 / .094 / .256 | .769 / .558 / .344 / .442 | .681 / .511 / .493 / .493 | .682 / .511 / .493 / .493 |
| absent | 30 | 500 | .582 / .326 / .090 / .266 | .728 / .522 / .333 / .386 | .717 / .539 / .493 / .493 | .717 / .536 / .493 / .493 |
| absent | 30 | 1000 | .614 / .379 / .121 / .342 | .812 / .619 / .388 / .464 | .673 / .515 / .500 / .500 | .675 / .517 / .500 / .500 |

## Direct sign-inversion check and W_u=0 ablation

These are fault-free late-window raw `a_c` means, so all direct and indirect channels are truly supported. B's non-reachable null is positive because it maximizes six finite-sample `|z|` values; discrimination depends on separation, not a zero null mean.

| condition | statistic | direct action children | reachable-indirect (incl. d) | non-reachable |
|---|---|---:|---:|---:|
| conf present, N_x=10 | A draft 2 | 1.700 | 0.144 | −0.017 |
| conf present, N_x=10 | B sign-randomized | 2.694 | 1.869 | 1.457 |
| conf absent, N_x=10 | A draft 2 | 1.700 | 0.144 | 0.063 |
| conf absent, N_x=10 | B sign-randomized | 2.694 | 1.869 | 1.529 |
| conf present, N_x=30 | A draft 2 | 1.661 | **−0.169** | **−0.066** |
| conf present, N_x=30 | B sign-randomized | 2.650 | **1.777** | **1.437** |
| conf absent, N_x=30 | A draft 2 | 1.661 | **−0.169** | **−0.095** |
| conf absent, N_x=30 | B sign-randomized | 2.650 | **1.777** | **1.541** |
| W_u=0, G retained, N_x=10 | A draft 2 | 3.170 | 0.275 | −0.017 |
| W_u=0, G retained, N_x=10 | B sign-randomized | 2.793 | 2.065 | 1.457 |

With `W_u=0`, the measured action/distractor correlation falls from 0.501 to 0.045, so this is deliberately an ablation outside the `rho_min` witness cell. At offset 500, A improves to AUC/AUPRC 0.743/0.589 and B to 0.848/0.682, from 0.625/0.412 and 0.743/0.538 respectively. At offsets 200/500/1000, B's event AUC is 0.794/0.848/0.824 and AUPRC is 0.616/0.682/0.645.

## D-7a probed CUSUM

The global CUSUM uses `S_t=max(0,S_(t-1)+max_c|z_tc|-k)`, where `z` is the frozen predictor's standardized innovation and `k` is the fault-free mean plus 0.5 standard deviations of `max_c|z_tc|`. Passive and probed thresholds are separately selected to approximate fresh-start ARL 1000, because probe shocks change the null distribution. These 20-control calibrations are diagnostic, not contract-grade D-2a calibrations.

| condition | passive event/control detection by 200 | probed event/control detection by 200 | approximate calibration ARL, passive/probed |
|---|---:|---:|---:|
| conf present, N_x=10 | 1.00 / 0.00 | 1.00 / 0.13 | 1069 / 986 |
| conf absent, N_x=10 | 1.00 / 0.13 | 1.00 / 0.13 | 947 / 895 |
| conf present, N_x=30 | 1.00 / 0.13 | 1.00 / 0.40 | 900 / 978 |
| conf absent, N_x=30 | 1.00 / 0.13 | 1.00 / 0.10 | 916 / 919 |
| W_u=0, N_x=10 | 0.17 / 0.13 | 0.40 / 0.13 | 967 / 992 |

The support-ranking result is the relevant D-7a control: under confounding at offset 500, B exceeds Cmp+P AUPRC by 0.350 (`N_x=10`) and 0.450 (`N_x=30`). Merely receiving the probes does not reproduce the causal use of their randomized signs.

## Assessment of D-9.2 to D-9.5

### D-9.2 — valid direction, changes required

**[Opinion]** AUPRC is preferable to accuracy or thresholded F1 as the primary ranking metric because only 3 of 24 channels are positive after the event at `N_x=10`, and 3 of 44 at `N_x=30`. It emphasizes the quality of the high-score region where a mask would operate. But average precision's chance baseline is prevalence, and copies or padding change both prevalence and observation weights without changing the underlying causal object. Duplicating an easy positive can improve AP; adding padding negatives changes the baseline and may worsen it. Therefore do not pool channels or compare raw AP across distractor/morphology cells. Compute AP per episode, pair arms by seed, equal-weight predeclared cells, publish prevalence and `AP−prevalence`, and add a co-reported grouped AP in which sensor copies mapping to the same latent are one equivalence class and padding is one declared negative class. Keep raw observed-channel AP as the contract-facing primary and AUC secondary. This preserves the stated observed-space estimand while making gaming visible.

### D-9.3 — judgment call, coherent after terminology and margins are fixed

The simple confounding contrast `[(AP_B−AP_cmp)_present − (AP_B−AP_cmp)_absent]` within regime directly targets the claim that interventions help when passive association is confounded. R0-present is a sensible positive control, and the R0/R1 interaction is properly descriptive because B has no residual-model regime change. However, TOST tests equivalence, not “non-superiority.” If R0-absent is meant to show practical parity, use a two-sided equivalence interval of **±0.05 absolute AUPRC**. If it is only meant to rule out a material B advantage, use a one-sided upper-margin test at **+0.05**, while separately guarding against B inferiority at **−0.05**. For the confounding benefit and R0-present positive control, use **0.10 absolute AUPRC** as the smallest effect of interest, with a paired confidence bound; it is large enough to matter and is the requested stress margin. Because AP prevalence varies, repeat the decision on prevalence-adjusted AP as a sensitivity, not a second gate. This run's point contrasts at offset 500 are 0.350 (`N_x=10`) and 0.416 (`N_x=30`), while R0-absent B-minus-comparator is 0.002 and 0.037, consistent with those margins.

### D-9.4 — valid

A headline cannot be reproduced from “channel-agnostic linear predictor” plus “innovation statistic.” A normative comparator spec must freeze: training population and episode count; fault/event/probe eligibility; complete feature vector and lags; intercept; regularization and solver; treatment of padding/copies; standardization and zero-scale floors; the exact per-channel score formula, orientation, window, warm-up, clipping, and update cadence; whether action loading is part of support; whether model parameters remain frozen online; probe handling; separate passive/probed calibration; isotonic tie/extrapolation behavior; operating-point selection; CUSUM recursion, drift/reference, persistence ownership, and ARL threshold protocol; random-seed/common-random-number rules; information set and output timing; ledger hashes; and executable fixtures including a confounded false-positive, an actuator-loss true-positive, padding, a copy, and a probe-shock null. The formula used here is one defensible reading, not a normative recommendation.

### D-9.5 — valid task description, invalid current validation protocol

“Supervised calibration on a declared split plus online estimation” honestly names the task: oracle support labels from event-carrying episodes supervise the probability map. But the current 40 episodes both fit isotonic knots and select the best F1 threshold, and event episodes expose the exact event type/time and transition mixture later scored. Split by whole episode into, for example, 24 calibration-fit episodes (12 event) and 16 operating-point validation episodes (8 event); freeze both artifacts before scoring. More importantly, make confirmation leave-one-instance-draw-out, and include held-out event times or loss targets, or call the task supervised within-instance transfer. A “proper score” applies to probability forecasts: raw `a_c` is not a probability, so “uncalibrated Brier/log loss” is undefined unless a predeclared, unfitted link is supplied. Report raw AP/AUC, plus cross-fitted Brier/log loss of the frozen calibrated probabilities. The captured output includes calibrated Brier/log loss for audit, but they are not used as evidence for D-9.1.

## Findings in the usual rubric

| ID | Severity | Claim attacked | Evidence | Proposed fix | Fix type |
|---|---|---|---|---|---|
| **D9-codex-1** | low | D-9.1's single-model evidence is not independently reproduced. | Independent instance, implementation, seeds, and comparator reproduce B at AUC .770/.818 averaged across confounder-present `N_x` cells at 500/1000; AUPRC advantage over passive is .352–.453 at 500. | Adopt B, then encode its missing edge rules and run the complete frozen matrix. | decision + spec + test |
| **D9-codex-2** | medium | R3-1's class sign inversion is a general property of draft 2. | Inversion appears at `N_x=30` (indirect −.169 vs non-reachable −.066) but not `N_x=10` (.144 vs −.017). `W_u=0` improves A, confirming policy-load sensitivity without reproducing Claude's exact class magnitudes. | State the robust claim as weak/non-monotone ranking on admissible instances, not universal negative sign; require a generator-wide failure-rate estimate. | prose + experiment |
| **D9-codex-3** | medium | D-9.1 is operationally complete. | With roughly 25 probes/window, each `(k,sign)` group has about six samples. D-9 specifies no minimum per sign, empty-cell behavior, tie handling, or `z` cap. Different choices materially change early-offset scores. | Freeze `n_min` per sign (or an exact small-sample test), zero/absent behavior, tie correction, clipping, window endpoints, and epoch timing; add hand fixtures. | spec + test |
| **D9-codex-4** | medium | Raw AUPRC is comparable across class imbalance, copies, and padding. | Post-event prevalence is .125 at `N_x=10` and .068 at `N_x=30`; AP chance baselines and weights therefore differ. Sensor copies can reweight either class without changing latent support. | Per-episode paired AP, equal cell weighting, publish prevalence and AP lift, and add grouped/copy-collapsed AP sensitivity. | metric + decision rule |
| **D9-codex-5** | high | “TOST non-superiority” is a coherent inferential rule. | TOST establishes equivalence within two margins; non-superiority is one-sided. The phrase permits incompatible implementations of the gate. | Use equivalence ±.05 AUPRC for R0-absent parity, or explicitly use a one-sided +.05 test plus a −.05 non-inferiority guard; use .10 for the confounding benefit. | decision + prose |
| **D9-codex-6** | high | The comparator is reproducible from the current description. | A support score needs an orientation and a baseline support term; a two-sided innovation shift alone is a change score. Probe shocks also require arm-specific null calibration (here passive/probed thresholds differ by up to about 25). | Write and test the normative comparator fields listed in D-9.4 before estimand selection uses comparator results. | spec + test |
| **D9-codex-7** | high | One 40-episode split can both fit isotonic calibration and choose the “best” operating point without qualification. | This run's calibration-selected `F1*` is sometimes worse than F1@0.5 on scored seeds. The same labeled episodes determine knots and threshold, and exact event timing/type is transferred. | Separate calibrator-fit and threshold-validation episodes; evaluate unseen instance draws/events; freeze before score. | protocol + decision |
| **D9-codex-8** | medium | “Uncalibrated proper scores” are defined. | Brier and log loss require probability-valued forecasts; raw rank statistics have no probability semantics. | Report raw AP/AUC and cross-fitted proper scores of calibrated probabilities, or freeze a parameter-free probability link and name it. | metric + prose |
| **D9-codex-9** | medium | The executable gate rejects graph-structure omissions in the declared full block adjacency. | `surviving_mutant_world_edges.py` deletes every `A_w` and `A_x` edge from `build_adjacency`; an explicit input proves it differs, yet all 31 gate tests pass. Baseline gate is green with 32/32 registered mutants killed. | Add a direct block-equality fixture for `build_adjacency(A_b,C_d,A_d,A_w,A_x)`, register this mutant, and map the test to C1/B graph fidelity. | test |

## Attacks that failed

- **B loses its advantage under the shared-cause confounder — failed.** Its AUC changes little when `G` is removed, while its AUPRC advantage over the comparator is large only when the comparator is confounded, as intended.
- **B's result is a low-dimensional `N_x=10` accident — failed.** At `N_x=30`, B improves to AUC .797/.862 at 500/1000 with the confounder present.
- **The result is caused only by the actuator-loss transition — failed.** B retains useful ranking on no-event controls at all pseudo-offsets.
- **Giving the comparator identical probes closes the gap — failed.** D-7a AUPRC remains within .003 of passive at offset 500 under confounding and trails B by .350/.450.
- **R3-1's exact negative indirect-class sign must reproduce in every admissible cell — failed.** It reproduces at `N_x=30`, but the independent `N_x=10` instance has weakly positive indirect `a_c`. This narrows, rather than overturns, the criticism of draft 2.
- **W_u=0 makes B unnecessary — failed.** Draft 2 improves materially, but B still ranks better at every event offset in the ablation.

## Final judgment

**[Opinion] Yes:** the interventional arm is now demonstrably viable at a 5% budget for support **ranking** on this contract-B family-L instance, because an independent implementation reproduces the claimed scale, robustness to confounding, larger-distractor behavior, no-event behavior, and a >0.10 AUPRC advantage over both passive and identically probed comparators. This is not yet evidence for calibrated probabilities, universal instances, family N, delay 2, or the complete confirmation matrix. The single change that would most raise my confidence is a frozen D-9.1/statistical protocol followed by a multi-instance, leave-one-instance-out replication that estimates the fraction of admissible generator draws on which B clears the 0.10 paired-AUPRC margin.
