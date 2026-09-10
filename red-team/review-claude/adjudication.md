# Claude adjudication of the Codex and Gemini reviews (frozen c197652c0d8e846b)

Date: 6 September 2026. Written after my own findings and after reading both peer reviews. Verdicts: valid | invalid | judgment call, one reason each.

## Codex findings

| ID | Verdict | Reason |
|---|---|---|
| CX-01 | valid | `mutant_tau_cap.py` executed: 15 passed against the frozen gate; τ ≥ 2 is untested. |
| CX-02 | valid | The mandated command resolves to a different interpreter in the reviewers' shells; my `gate.output.txt` came from a pyenv Python with numpy. Reproducibility of the gate command is part of the gate. |
| CX-03 | valid | The estimator never receives the applied action or a transition; sequential IBD and any residual detector cannot be implemented from the public interface alone. I missed this entirely. |
| CX-04 | valid | Same defect as my CL-7; the interface shape drops the probe sign. |
| CX-05 | valid | Same as my CL-1 and Gemini GM-4. |
| CX-06 | valid | ARL_0 has no value; probe budget has no unit. Neither is reproducible from a string. |
| CX-07 | valid | The 2×2 cells exist in the CSV but no interaction estimand or gate is declared; R1 superiority could pass on misspecification alone. |
| CX-08 | valid | My "RMDT" assigns H_det to every censored event, which is a horizon-penalised composite outcome, not a restricted mean over right-censored times. Rename and separate administrative censoring from misses. |
| CX-09 | valid | s, κ, m have no values and "contractive" is not what the described test certifies. |
| CX-10 | valid | Three of the five advertised baselines have no rows. |
| CX-11 | valid | Aggregation over distractor levels and delays is unspecified. |
| CX-12 | valid | Ten clusters; bootstrap variant unspecified. |
| CX-13 | valid | The interface omits reward, terminated, truncated; contract G needs them. |
| CX-14 | valid | Returning NaN when any column is constant is stricter than the witness-pair rule. |
| CX-15 | valid | Interval construction and simultaneous error control undefined. |
| CX-16 | valid | I wrote "provisional until pilot variance is known", which invites tuning the margin to power. Freeze now. |
| CX-17 | valid | No evaluator-only out-of-band query exists in the interface. |
| CX-18 | valid | "Misspecified" is a label, not a transform. |

## Gemini findings

| ID | Verdict | Reason |
|---|---|---|
| GM-1 | valid | The 999·B mutant survives because G1 tests equivalence only at τ = 0. |
| GM-2 | valid | H = 2 is never asserted; a chain test kills it. |
| GM-3 | valid | Same as my CL-2. |
| GM-4 | valid | Same as my CL-1. |
| GM-5 | valid | Same as my CL-5. |
| GM-6 | valid | K7 and K10 are named as tests in the contract and do not exist. |
| GM-7 | judgment call | Whether one witness pair or a declared fraction of confounded channels defines the stress profile is a design choice for Daniel; my proposed default is a declared confounded fraction of 0.5 with at least one witness above ρ_min. |
| GM-8 | invalid | Relies on the superseded `gemini_v32_checks.py`; the frozen D11 and contract G make pAUC descriptive and the statistic is taken at matched ARL_0, so disjoint supports cannot arise in the primary. Codex also rates it invalid. |
| GM-9 | valid | Same as CX-02. |
| GM-10 | valid, low | Contract C4 specifies z̄ after burn-in; the reference evaluates at zero, which is exact for family L only. The reference should take z̄ as an argument and family N remains uncovered. |

## Cross-review tally (applied = two-of-three valid, or executable evidence)

Applied: CL-1..5, CL-7..12; CX-01..18; GM-1..6, GM-9, GM-10. Parked with dissent: none. Rejected: GM-8 (two invalid). Judgment calls to Daniel: CL-6 (distractor-channel p_c as co-primary or K ≥ 2 SCM partial loss as primary; default adopted: co-primary p_c on distractor channels at fixed offsets), GM-7 (confounded fraction; default 0.5).

Convergent blockers found independently by all three: delay-aware structural support; delayed-response test coverage; full-latent reachability with downstream d; a defined R0 model for T2. Two of three: nonlinear R shape; missing K cases; environment reproducibility.
