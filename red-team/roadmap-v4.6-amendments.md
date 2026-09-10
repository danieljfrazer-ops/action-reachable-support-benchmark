# Roadmap v4.6: round-3 safe corrections (D-9 pending)

Date: 7 September 2026. Applies convergent round-3 findings that do not change what is measured. Everything that does is in `decisions-required.md` D-9.

## J1. Calibration cell (R3-7, CX-06)
Per (environment, regime, confounder, distractor_level, delay, estimator); F10's "once per cell" budget restated on that key. Matrix calibration rows already match.

## J2. ARL eligibility scoped to descriptive outcomes (R3-8, CX-08)
P1 and P2 are computed on all pairs; band attainment is a covariate.

## J3. Persistence ownership (R3-10, CX-05)
Estimators emit raw exceedance; harness owns p (unit declared) and r. Interface v3 amended.

## J4. Gate (R3-5/16, GM3-1/5/6, CX-03, CX-13)
Nine round-3 mutants registered and killed; `count_alarms`, `match_alarms`, `aggregate_primary` added to the distinctness guard; pins enforced by `run_gate.py` (exit 2 on Python or numpy mismatch); coverage matrix re-headed with T-IBD rows uncovered.

## J5. Matrix re-aimed for the support-correctness primary (R3-12, CX-03)
Columns `outcome`, `offsets_F1`, `primary_offset`, `p2_offsets`; all four (regime × confounder) cells are `confirmatory_effect` with an `interaction_group` key; generator docstring updated. Aggregation column names the ranking metric pending D-9.2.

## J6. Registry (R3-13, R3-14)
τ ∈ {0, 2}, τ_max = 2; probe step defined as a replaced environment step.

## J7. Spec draft 3 requirements carried forward (not applied until D-9)
Define tie correction, the pre-event sub-split, pooled vs per-channel calibrator, window convention with derived counts, clamp values (R3-11); washout from the instance's impulse response, not the support horizon (CX-04); remove "exact" from the rank-null claim (CX-10, GM3-3); state that multi-event schedules are exploratory for this arm and declare a window policy (GM3-8); optional jitter (GM3-7); recompute the window-memory table from the epoch grid (R3-15).

## J8. Process rule addition
A decision whose basis is one model's simulation is not frozen until a second model reproduces it on its own instance (applied to D-9.1). Verification runs are part of the round, not after it.
