# Assessment of the Codex red team of roadmap v3.4 (codex-v3.4-red-team/)

Date: 6 September 2026. Verdict received: **go with blocking changes**; "unconditional go" unsupported. I agree. This review corrected both me and the previous Gemini pass.

## The central finding, L1, and what I did about it

Codex is right that the "executable-proof gate" did not exist. My two scripts print numbers and exit 0; they contain no assertion, no mutant, and no failure path. A wrong formula would have passed them. Gemini's third review certified the contract as "fully verified" on that basis, which is exactly the shared-mistake failure mode Codex describes in L16.

Done now, in `executable-proofs/gate/`:
- `contract_ref.py`: reference implementations of the contract formulas.
- `test_gate.py`: assertion tests for the hand-derived cases, the open-loop response, the delay rule, multivariate confounding with a NaN guard, gain in observed support, rectangular B, censored detection time; plus mutants M1, M2, M5 and the old negative-power formula, each asserted to be rejected.
- `test_proof_theatre.py`: demonstrates that a print-only script exits 0 with a wrong formula (Codex's requested first action).
- `run_gate.py`: minimal runner because pytest is not installed in this Python; `coverage-matrix.md` lists four uncovered normative groups that Phase 0A must close before its gate.
- A separate check reintroduced the v2 negative-power bug into the reference and confirmed the gate fails on it.

## Disposition of the rest

| ID | Disposition | Where |
|---|---|---|
| L2 R2 masking impossible with complete loss in single-actuator systems | **Accept.** R2 is exploratory, R-target, partial loss, appendix; confirmatory regimes are R0 and R1 | v4 D10 |
| L3 censoring absent from delay median; disjoint-support scalar invalid | **Accept.** This reverses Gemini I2, which I had applied. Primary statistic is restricted mean detection time at matched ARL_0, so supports cannot be disjoint; pAUC descriptive only | contract G; v4 D11 |
| L4 "exact" overstated for nonlinear operational labels | **Accept.** Structural exact; operational numerically certified with n_oracle, intervals, and rejection of instances near ε | contract C2 |
| L5 gain can change observed support | **Accept.** Gain is in the definition; gain events may change S^obs,ε; cases 0, near-0, sign flip tested | contract C3; test_L5 |
| L6 Paper 2 filter deletes reward-relevant uncontrollable state | **Accept.** Typed routing with soft weights; leakage and retention measured separately | v4 D12, section 5 |
| L7 design not reconstructible; comparator unfrozen; budget hypothesis inconsistent | **Accept.** Single roadmap v4; `confirmation-design.csv` (1,440 rows: 720 primary, 720 diagnostic 2×2); comparator frozen as channel-agnostic CUSUM; fixed budget confirmatory, break-even descriptive | v4 D9, section 4 |
| L8 R0 "match" rule cannot validate equality | **Accept.** This reverses Gemini I1. Non-superiority margin δ0 | v4 section 4 |
| L9 stability and stationarity not contractual | **Accept.** Spectral radius bound, |ρ_u| < 1, action clip, burn-in, contractivity certification for family N, faithfulness re-check after every event | contract 0, B |
| L10 classical baseline information set unclear; misspecification confounded with confounding | **Accept.** Information sets declared; 2×2 diagnostic; oracle-coordinate CUSUM as labelled reference | contract F, H; v4 section 4 |
| L11 CartPole is discrete; horizons; exclusion bias | **Accept.** u into action logits for CartPole; Pendulum-v1 with `TimeLimit` replaced and disclosed; early termination is a competing outcome | v4 section 3 |
| L12 row/column error; vector correlation undefined | **Accept.** Max pairwise correlation with a witness pair; rectangular B tested | contract E2; tests |
| L13 reachability is not body membership | **Accept.** "Action-reachable observation support" in the claim; body membership oracle-only | contract C6 |
| L14 schedule omits repair and runtime pilot | **Accept.** Phase 0R this week; runtime pilot before dates; Paper 1 arXiv target moved to late February 2027 with reserve | v4 section 3 |
| L15 Paper 2 novelty overstated | **Accept.** Stress test plus routing remedy framing | v4 D12 |
| L16 agents can certify a shared mistake | **Accept.** Black-box acceptance suite from a frozen interface spec; Daniel's hand case; evaluator hash held outside the tree | contract E6; interface-spec.md |
| L17 `boundary-bench` name taken | **Accept.** Name deferred to a collision check | v4 D13 |
| L18 Phase S is diagnostic, not a Paper 3 gate | **Accept.** | v4 D1 |

## Where I differ

Only on emphasis. Codex's "do not produce environment code next" is right for the generator; producing the gate tests first was itself code, and it was the correct first code. On Paper 2, I keep the interventional filter as one arm of the comparison rather than dropping it: it is the hard-deletion control that typed routing must beat.

## Lesson recorded for the workflow

Three reviewers and four rounds did not catch that the proof scripts were not tests. The fix is structural, not another review: no normative item exists without a test ID, and no gate passes on a captured print. That rule is in contract v3 section 0 and roadmap v4 section 6.
