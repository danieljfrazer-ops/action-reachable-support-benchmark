# Codex round-2 adjudication

Review date: 6 September 2026. I read `review2-gemini/findings.md` in full after completing my independent findings. The second peer round-2 file (expected from Claude) was not present under `docs/archive/red-team/review2-*/findings.md` at adjudication time, so there are no Claude findings to classify yet. This is an availability statement, not an adjudication of absent work.

## Gemini findings

| Finding | Verdict | One reason |
|---|---|---|
| GM2-1 | **valid** | The supplied premature-propagation mutant passes all 17 tests, and the delayed test uses a `B` whose every body row is already directly reached, so delay and graph depth never interact. |
| GM2-2 | **valid** | I independently executed the same `A_d`-omission mutant: it passes all 17 assertions because the only downstream test has a one-dimensional, directly reached `d`. |
| GM2-3 | **valid** | The frozen radius formula is the zero-delay body block; delayed feedback and observed downstream state require an augmented closed-loop transition matrix. |
| GM2-4 | **valid** | At true ARL 1000, 20,000 steps supply only about 20 renewal events, giving approximately 22.4% relative sampling error versus the claimed 10% tolerance; exclusion then becomes method-dependent selection. |
| GM2-5 | **valid** | The interaction is a claim gate but its absent-confounder rows are labelled `diagnostic_2x2`, so a role-based primary selector either omits required cells or silently promotes diagnostics. |
| GM2-6 | **valid** | The named confounded-channel endpoint averages all distractors despite `f_conf=0.5`, and the contract has no value rule for offsets occurring after early termination. |
| GM2-7 | **valid** | `aggregate_primary()` is promised by the amendment/interface, absent from `contract_ref.py`, and explicitly uncovered in the coverage matrix. |
| GM2-8 | **valid** | `>=` lower bounds are not pins; the clean run demonstrably resolved different versions from the committed gate output. |
| GM2-9 | **valid** | Three normative implementation/acceptance references still name superseded contract or interface files despite the amendment's new frozen set. |
| GM2-10 | **valid** | I executed the family-N case with `zbar=0`; the non-odd assertion still passes, so the test does not establish that the required empirical stationary mean was used. |
| GM2-11 | **valid** | `epsilon_faith` is normative in the faithfulness rule but absent from the constants registry. |

## Claude findings

No `review2-claude/findings.md` (or other second peer round-2 findings file) was present when this document was written. It should be appended and adjudicated before the three-review synthesis is treated as complete.

