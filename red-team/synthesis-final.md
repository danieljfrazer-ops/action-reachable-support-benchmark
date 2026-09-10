# Final synthesis: disposition of the Codex final critique

Date: 6 September 2026. Inputs: `codex-final/` (three files). Verdict received: **go with changes**, four blocking. My disposition below; all four blocking changes are accepted and implemented in `stage-0a-contract-v2.md` and `roadmap-v3.1-amendments.md`.

## Disposition

| Codex finding | Severity | Disposition | Where applied |
|---|---|---|---|
| F1 sensor swap both changes and does not change S_t (observation vs latent coordinates) | High | **Accept. Correct and blocking.** Two supports: S^latent and S^obs. Sensor swap leaves S^latent and M unchanged; changes P; changes S^obs iff a controllable channel is involved. Hand-derived example included. | Contract v2, sections C and K |
| F2 M_t and P_t not typed, identifiable estimands | High | **Accept.** M defined as finite interventional response over a frozen probe set and horizon set, with Jacobian as the linear special case; P split into assignment, gain, availability; copies scored as equivalence classes. | Contract v2, section C |
| F3 estimator API cannot support a three-target paper | High | **Accept, resolved by narrowing.** Paper 1 primary: S^obs support and typed change alarms for all three targets. Estimation of M and P is secondary; every estimator must emit a declared output for every target (a constant is allowed and scored). | Contract v2 section F; amendments A3 |
| F4 invariants untestable or tautological | High | **Accept.** Structural tests on an independent graph oracle; statistical tests with common random numbers and tolerances; mutant generators; same-host bitwise determinism plus cross-host tolerance; evaluator isolation with a canary. | Contract v2, section E |
| F5 primary estimand, SOEI and design not frozen | High | **Accept.** Frozen now: method pair, target, change family, regime, scalar estimand, SOEI with rationale, run matrix construction. Pilot used for variance only. | Amendments A4 |
| F6 kill rule CI logic inverts | High | **Accept. This was my error.** Signed effect, superiority/futility/inconclusive rules. | Amendments A5 |
| F7 no independent ground-truth implementation | High | **Accept.** Two label derivations (declarative SCM analytic; finite-difference interventions on tiny cases) must agree; hash stored outside the writable tree; golden cases; reference metric script. | Contract v2 section E; amendments A6 |
| F8 Phase S scope does not fit two weeks | High | **Accept.** Reduced to three families, singletons plus one predeclared pair, two physical budgets, one held-out generator; publish only if completeness gate met. | Amendments A7 |
| F9 shared-cause distractor sound but equations omitted | Medium | **Accept.** Explicit equations, no action parent of x, private cue for the policy, correlation floor and invariance tolerance. | Contract v2, sections A, B, E |
| F10 structural support vs detectable shift conflated | Medium | **Accept.** Structural label for generator correctness; operational effect-above-epsilon label for detection scoring; sensitivity to epsilon and horizon reported. | Contract v2, section C |
| F11 sequential metrics and calibration underspecified | Medium | **Accept.** Persistence length, typed alarms, reset, censoring, event matching, close-event rule fixed; calibration split by whole configuration; raw and calibrated reported; ECE diagnostic only. | Contract v2, section G |
| F12 reintroduction does not isolate cached recognition | Medium | **Accept.** Equal dwell and transition counts; declared state resets; unseen structurally matched A' condition; recognition latency vs relearning slope. | Amendments A8 |
| F13 dates omit the rerun loop | Medium | **Accept.** 0A 1.5 to 2 weeks; 0B 2 to 3 weeks; 25 to 35 percent rerun reserve after pilot; February 2027 retained as planning target. | Amendments A1 |
| F14 no change control after freeze | Medium | **Accept.** Hash set, manifests with completion markers, failed-run records, rerun classification, Daniel approves exceptions before unblinding. | Amendments A6 |
| F15 hostile reviewer would not accept three-target claim yet | Medium | **Accept.** Positioned as benchmark and failure map; "self-boundary" kept out of the technical claim; two structurally different dynamics families. | Amendments A3, A9 |
| F16 H3 partly guaranteed by construction | Low | **Accept.** H3 secondary and descriptive. | Amendments A4 |
| F17 shakedown is a conditional contribution | Low | **Accept.** Called a small empirical methods contribution conditional on a final prior-art pass and complete matched-budget evidence. | Amendments A7 |

## Where I disagree

Nothing material. Two notes:
- Codex's "single first action" (revise the contract with explicit equations and two coordinate systems, hand-derive a sensor swap) is exactly right and is done in contract v2. I add: the actuator-loss example shows that whether a loss changes S^latent depends on body-internal coupling, which is why the label must come from graph reachability and not from the event type. That strengthens F7.
- Codex asks for the fractional run matrix with resolution and alias structure. Our factors have 2 to 6 levels, so a classical two-level fraction does not apply cleanly. I substitute a two-part design (full sub-grid for the primary contrast; space-filling subset for the exploratory surface) that is easier to audit and does not need alias tables. Codex can object to this in review of the run matrix CSV.

## Net position

Direction unchanged. Contract repaired. Design frozen. Timings lengthened. Phase S reduced. Ready to implement Stage 0A from contract v2 once Daniel confirms decision D8 (Paper 1 narrowed to S^obs plus typed change detection as primary).
