# Codex review 3 adjudication

Review date: 7 September 2026. I completed `review3-codex/findings.md` before reading either peer file. I then read `review3-claude-opus/findings.md` and `review3-gemini/findings.md` in full. Verdicts concern the frozen hash `e662b7429b6b347d`; they do not endorse every proposed fix.

## Claude Opus

| Finding | Verdict | One reason |
|---|---|---|
| R3-1 | **valid** | The executable ablations isolate a load-bearing sign failure: under autocorrelated shared-cause policy actions, reachable indirect channels rank below non-reachable channels, which a non-decreasing calibrator cannot repair. |
| R3-2 | **valid** | Its alarm result independently confirms weak power, while near-chance AUC and degenerate F1 show that changing the endpoint did not validate the drafted estimator; this converges with my D-8 finding. |
| R3-3 | **valid** | The F1 rules were copied from a regime logic in which R0-present was a negative control, but the v4.5 working claim now predicts comparator attribution failure under confounding in R0 too, so TOST and the double interaction can reject the intended mechanism. |
| R3-4 | **valid** | Both the fixed-0.5 prevalence collapse and the two inequivalent readings of “per-channel F1” are real; my permitted `N_x=100` instance makes the calibration gate fail deterministically at 4.605% positives. |
| R3-5 | **valid** | Seven supplied non-equivalent mutants survive, including mean-to-median aggregation and refractory/persistence mutations that the current fixtures cannot distinguish. |
| R3-6 | **valid** | All seven normative T-IBD test IDs are absent from both gate code and the coverage matrix, so the stated uncovered count cannot certify draft 2. |
| R3-7 | **valid** | The contract's calibration key omits level/delay, the CSV materialises them, and draft 2 explicitly says h is not transferable across distractor levels. |
| R3-8 | **valid** | F1 and p_c are threshold-invariant, so making the new primary inconclusive because the descriptive alarm misses its ARL band contradicts D-8/I2. |
| R3-9 | **valid** | The normative callable has the wrong arguments and arity relative to `contract_ref.py`, which would break an independently written acceptance client. |
| R3-10 | **valid** | Draft 2 applies persistence internally in epochs and then delegates its already-persisted raise to a harness function that applies p again in steps. |
| R3-11 | **valid** | Tie correction, pre-event reference subset, pooled-versus-per-channel PAVA, window endpoints and clamp values are all consequential choices missing from a purportedly complete parameterisation. |
| R3-12 | **valid** | The frozen CSV contains no F1/P2 offset fields and its roles do not directly encode the four-cell claim gate; the matrix is not executable for D-8 as written. |
| R3-13 | **valid** | Delay values exist only in the CSV even though the contract and null guard depend normatively on tau and tau_max. |
| R3-14 | **valid** | The interface does not settle whether probe transitions replace or add environment steps; the two readings change the denominator and the claimed 100-probe count. |
| R3-15 | **valid** | Accounting for epoch closure and the null anchors leaves pre-event increments at offset 500, so “exactly 100% post-event” is false under the spec's own clock. |
| R3-16 | **valid** | The mutant-distinctness guard returns true automatically for new functions absent from `O`/`PROBES`, making the safeguard vacuous for precisely those functions. |
| R3-17 | **invalid** | The claim about how `probe_config_hash` was generated relies on `make_confirmation_design.py`, which is outside the frozen manifest; the CSV value alone does not prove it hashes a placeholder. |
| R3-18 | **valid** | The normative diagnostic and action-RMS fields have no corresponding ledger fields, so they cannot be recorded consistently through interface v3. |
| R3-19 | **valid** | The gate checks only NumPy importability; I demonstrated exit 0 under Python 3.14/NumPy 2.5.3 despite the frozen Python 3.12/NumPy 2.4.4 constraints. |

## Gemini

| Finding | Verdict | One reason |
|---|---|---|
| GM3-1 | **valid** | Mean and median are identical for the two-cell fixture; the supplied three-level mutant survives all 25 tests and directly violates equal-weight mean aggregation. |
| GM3-2 | **judgment call** | Reopening D-8 is supported, but the reported `CUSUM F1=0.857` depends on one of several comparator interpretations that the frozen spec does not choose; it is not a decisive arm comparison until the comparator is frozen. |
| GM3-3 | **invalid** | Its 13.7% max-absolute tail is approximately the expected `1-0.95^3=14.3%` when maximising three near-nominal z statistics, not evidence that autocorrelation tripled the per-h Type-I rate; my and Opus's per-h simulations were near nominal. |
| GM3-4 | **valid** | The 0.5-threshold prevalence collapse is executable and severe, although calling mixed-window calibration pairs “contamination” is debatable because they deliberately train the lagged estimator against current support. |
| GM3-5 | **valid** | No existing fixture places an alarm exactly at the event, so changing the strict lower boundary survives and changes attribution. |
| GM3-6 | **valid** | The current fixture does not exercise the exact refractory boundary, allowing an off-by-one implementation to survive. |
| GM3-7 | **judgment call** | Periodic aliasing is plausible in oscillatory control, but no frozen-cell counterexample is executed and random jitter changes the estimator design and budget timing. |
| GM3-8 | **judgment call** | A 500-step window can attenuate ABA/ABC changes, but “blinds” is not demonstrated and alarm-triggered reset would reintroduce the threshold-dependent path the spec intentionally removed. |
| GM3-9 | **invalid** | Interface v3 requires an output every step, not recomputation every step; draft 2 explicitly emits cached piecewise-constant p_c/stat between epochs. |

## Cross-review conclusion

The strongest convergence is on four blockers: D-8's replacement endpoint is not ready, the comparator is under-specified, fixed-threshold isotonic calibration degenerates, and the gate remains vulnerable to fresh aggregation/alarm mutants. Opus additionally demonstrates a more fundamental estimator problem than my simulation isolated: the task-policy null can reverse the score ordering on mandatory indirect/downstream channels. That finding should be addressed before tuning budget or thresholds.

