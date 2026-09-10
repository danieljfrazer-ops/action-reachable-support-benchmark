# Red-team review — RT-20260910-008

**FAIL** — 1 blocking problem with checked evidence.

287 files reviewed. 2 of 2 required model families produced a usable review (anthropic, google).
Nothing under review changed while they ran.

## Worth knowing

- 2 directories were skipped by name and never reviewed: docs/archive/red-team/.DS_Store, docs/archive/red-team/executable-proofs/.DS_Store
- codex did not count towards diversity — did not produce a review (error)
- antigravity: counted, but its model was NOT verified: "gemini-3.1-pro-high" is what was asked for, not what was observed — this tool does not report which model actually ran
- antigravity: "No findings" gave no P0-P3, so it was read as P2

## Who reviewed

| Reviewer | Model that actually ran | Family | Counts | Status | Time | Kept |
| --- | --- | --- | --- | --- | --- | --- |
| claude-code | `claude-opus-5` (envelope) | anthropic | yes | ok | 520s | 7 |
| codex | `gpt-5.6-sol` (session-log) | openai | **no** | error — Reading additional input from stdin... | 7s | — |
| antigravity | `gemini-3.1-pro-high` (pinned-slug) | google | yes | ok | 311s | 0 |

## What they found

### 1. BLOCKING — §2 and §9 both claim the estimator specifications were redrafted by agents "that had not seen the adjudications"; both redrafts name the round-5 adjudication in their own basis line

`docs/report/technical-report.md:36-37`  ·  found by anthropic alone

**claude-code/F-1** (P1, blocking)

`docs/report/technical-report.md:36`

```
- **Adjudication separate from review.** The roadmap, contract, interface specification, prompts and adjudications were drafted by one Claude session acting as my agent; the two estimator specifications were drafted, and after round 5 redrafted, by separate fresh-context Claude agents that had not seen the adjudications; I set the question, made every design decision and estimand choice from that session's recommendations, and directed each step.
```

This is the one mitigation the report offers for the fact that everything else — roadmap, contract, interface, prompts, adjudications — came out of a single Claude session, and §9 repeats it verbatim at `:215`. It is contradicted by the two specifications themselves.

`docs/archive/red-team/comparator-spec.md:3`

```
Basis: `stage-0a-contract-v3.9.md` §§0, A0, B, C, E, F, G, H, H2, L; `interface-spec-v5.md`; `decisions-required.md` D-11 (all six parts adopted); `round5-adjudication-and-tally.md`; `executable-proofs/gate/reference_generator.py` and `contract_ref.py` as frozen at contract v3.9.
```

`docs/archive/red-team/sequential-ibd-spec.md:3` is the same: "`decisions-required.md` (D-11); `round5-adjudication-and-tally.md`; `review5-codex/findings.md`, `review5-gemini/findings.md`, `review5-claude-opus/findings.md`". Both redrafting agents worked *from* the round-5 adjudication and from D-11, which is the adjudicating session's own decision record — and it shows: `comparator-spec.md:5` reproduces the adjudication's numbers ("subtracting it cost 0.12 to 0.27 AUC, which is why the D-10.3 competence floor failed"), and `sequential-ibd-spec.md:395-411` is a row-by-row disposition of round-5 findings against D-11.

Concretely, what goes wrong: a reader is told the two specifications are an independent channel that the adjudicating session could not contaminate. They are not; they were written to implement that session's adjudicated decisions. The error propagates — §6's third error ("A primary the treatment could not reach") is presented as an error that only the *next execution round* could catch, but the redrafting agents that encoded D-11.1a had the adjudication in front of them and were the last human-independent chance to notice the channel-set mismatch before the freeze.

Fix: say what happened. In `:36` and `:215`, replace "that had not seen the adjudications" with "that worked from the contract, the interface specification, the round-5 adjudication and D-11, and did not review or adjudicate", and add the resulting weakness to the `:203` limitation, which currently records only the adjudicator/reviewer family overlap.

**claude-code/F-3** (P2)

`docs/report/technical-report.md:37`

```
Conditions 1 and 6 were exercised, with the gate's exit code as the operational test of condition 1 and of condition 2's mutant clause, and the convergence rule ran in rounds 1 to 8. Condition 2's historical-bug clause and conditions 3, 4 and 5 were never done, so no version was readiness-certified.
```

Condition 1 is "Coverage matrix: zero uncovered normative items" (`readiness-protocol.md:12`). Two things are wrong. First, nothing in the gate reads `coverage-matrix.md`: `run_gate.py:16` iterates `("test_gate", "test_generator", "test_proof_theatre")` and `mutants.py:12` iterates `test_gate` only; the string "coverage" appears in the gate directory only in a docstring comment and in the matrix file itself. The exit code cannot test condition 1 under any input. Second, condition 1 does not merely lack a test — it fails:

`docs/archive/red-team/executable-proofs/gate/coverage-matrix.md:29`

```
Uncovered normative groups: 4 (T-IBD/T-CMP spec fixtures; mutants M2–M6; E4–E6 isolation and acceptance; ARL_0 calibration and tier-2 metrics). Phase 0A gate requires 0.
```

`sequential-ibd-spec.md:410` records the same thing from the spec side, as an open high finding: "`coverage-matrix.md` has no row for any `T-IBD-*` id". As written, the report tells a reader that of the six conditions only 2's second clause and 3–5 are outstanding; in fact condition 1 is outstanding too, and is the one the report claims was operationally green. Fix: "Condition 6 was exercised: the convergence rule ran in rounds 1 to 8. The gate's exit code was the operational test of condition 2's mutant clause only; condition 1 was never mechanically checked and `coverage-matrix.md` still records four uncovered normative groups against a required zero. Condition 2's historical-bug clause and conditions 1, 3, 4 and 5 were never satisfied, so no version was readiness-certified." The same correction is needed at `:202`, which lists only conditions 3–5.


### 2. P2 — the delay-2 cells, where the passive arm is perfect and the negated static vector wins, score a different estimand, and the report drops that caveat from both places it matters

`docs/report/technical-report.md:120-120`  ·  found by anthropic alone

**claude-code/F-5** (P2)

`docs/report/technical-report.md:120`

```
The passive comparator beat the interventional arm in every family L cell and every perturbation cell. With the covariance score, noticing that a controlled channel has gone quiet is a matter of watching innovations correlate with actions, which the passive arm does at every step while the probed arm sees about six probes per sign per actuator in its window. At delay 2 the comparator was perfect on every instance.
```

`docs/archive/red-team/round6-adjudication-and-tally.md:23`

```
5. **Loss of actuator 1 removes no observed channel on any seed (high).** The benchmark tests one hand-wired coordinate; at τ = 2 the pre-event support is exactly four channels on every draw and the delay cells score a different estimand (zero propagation hops survive at H = 3).
```

The report carries the first half of this finding (`:122`, "losing actuator 1 removes no channel on any seed") and drops the second half. The dropped half is load-bearing: half the family-L cells are τ = 2, and it is exactly in those cells that the comparator scores 1.000 against sequential IBD's 0.687 and that the negated static loading vector scores 0.80 against 0.687 — the two most quotable numbers in §4.2 and the basis of §5's second surviving result. If at τ = 2 the pre-event support is four channels with zero propagation hops surviving at H = 3, then "the comparator was perfect" and "equals or beats … in every linear-family cell" are being asserted across two different questions. Fix: state it where the number appears — "at delay 2 the comparator was perfect on every instance, in cells where the pre-event support is exactly four channels and no propagation hop survives at the scored horizon, so the delay cells score a different estimand from the delay-0 cells (round-6 adjudication §2 item 5)" — and add it to the caveat list at `:169`, which currently names four caveats and not this one.


### 3. P2 — §4.4 and §5 report the round-8 knife-edge result without the one finite-sample caveat the derivations attached to it, and §8 then proposes building the arm that caveat is about

`docs/report/technical-report.md:151-151`  ·  found by anthropic alone

**claude-code/F-4** (P2)

`docs/report/technical-report.md:151`

```
First, exact non-identifiability is a knife-edge, not an open set. The observational law of (o, a) at all lags contains the independent action noise ε^a, which acts as an instrument: the covariance between the body and the action has a discontinuity at the causal lag τ that the smooth AR(1) confounder path cannot produce, and it pins B separately from G_b. Exact confusion between an actuator loss and a support-preserving change in G_b requires the action noise to vanish in the affected direction. The premise I had adopted was false.
```

The adjudicated conclusion is right, but the derivation the adjudication leans on for reconciling Gemini says more than the report carries:

`docs/archive/red-team/review8-gemini/derivation.md:109`

```
*(Remark on full joint distribution):* If an estimator possesses an exact structural model and infinite data, the conditional innovation variance $\operatorname{Var}(b_{t+1} \mid y_{\le t}, a_t) = (B - G_b K_a) \Sigma_a (B - G_b K_a)^T + \dots$ contains a rank-$K$ term from natural excitation $\Sigma_a = \sigma_a^2 I_K$. However, matching both the conditional mean ($B + G_b K_a$) and the innovation covariance requires $\sigma_a^2 \to 0$ or an unconstrained adjustment of $\Sigma_b$. In real finite-sample conditions where $\sigma_a$ is small ($\sigma_a = 0.1$), the natural excitation is dwarfed by the confounding variance ($W_u^2 \sigma_u^2 \gg \sigma_a^2$), rendering the full joint law empirically indistinguishable between E1 and E2.
```

The instrument the whole result rests on is, at the contract's own σ_a = 0.1 against σ_u = 1.0, weak. That matters twice. §5's third surviving result (`:171`, "a passive method that models the context can in principle recover the coupling through the policy's own action noise") is hedged with "in principle" but a reader will take it as a design recommendation; and §8 (`:207`) makes "a latent-modelling passive third arm" part of the condition that would reopen the question — i.e. it proposes building precisely the arm that one of the three derivations predicts will not separate E1 from E2 at the frozen noise scales. Fix: add one clause at `:151` or `:171` — "the instrument is weak at the contract's noise scales (σ_a = 0.1 against σ_u = 1.0), so one of the three derivations expects the two laws to be empirically indistinguishable in finite samples even though they differ in the limit" — and add the same as a bullet to §7, since it is a limitation of the only result the report claims is new.


### 4. P2 — §9's account of this report's own review is one run out of date and misstates two reviewers' participation

`docs/report/technical-report.md:215-215`  ·  found by anthropic alone

**claude-code/F-2** (P2)

`docs/report/technical-report.md:215`

```
Its review against the archive was by a fresh-context Claude Opus agent and by a cross-model review tool run five times across drafts 1 to 4: the Anthropic reviewer reported on every run; the OpenAI reviewer reported on three (it declined the first for lack of the archive in scope and errored on the fifth); the Google reviewer reported on the fifth only (out of scope on the first, quota-exhausted on the other three).
```

That description fits RT-001 through RT-006 exactly. It omits RT-007 — the review this draft was written to answer, and the review that produced the `:189` erratum paragraph and the `:167` rewrite. The archive holds six runs (`review9-tool/RT-001`, `-002`, `-003`, `-005`, `-006`, `-007`), covering drafts 1 to 5, and in the sixth:

`docs/archive/red-team/review9-tool/RT-007-report-draft5.md:19-20`

```
| codex | `gpt-5.6-sol` (session-log) | openai | **no** | error — Reading additional input from stdin... | 7s | — |
| antigravity | `gemini-3.1-pro-high` (pinned-slug) | google | yes | ok | 520s | 1 |
```

So the OpenAI reviewer errored on the fifth *and sixth*, and the Google reviewer reported on the fifth *and sixth*, not "the fifth only". In a disclosure section whose whole point is exact provenance, and in a report that elsewhere counts reviewers per number, this is the sentence a referee will check first. Fix: "run six times across drafts 1 to 5: … the OpenAI reviewer reported on three (it declined the first for lack of the archive in scope and errored on the fifth and sixth); the Google reviewer reported on the fifth and sixth (out of scope on the first, quota-exhausted on the other three)." Note also that RT-004 is absent from the archive; if it exists it should be added, and if it does not, the numbering gap should be stated.


### 5. P3 — Table 1's caption says row 3's as-frozen gate count was not recorded; a round-3 reviewer recorded it, on that hash, and it is the number the row already gives

`docs/report/technical-report.md:55-55`  ·  found by anthropic alone

**claude-code/F-6** (P3)

`docs/report/technical-report.md:55`

```
Gate counts are for the version as frozen, not after the repairs the round prompted; row 3's is the last count logged before that freeze, since the gate gained tests with interface v3 and the IBD draft and the as-frozen count was not recorded.
```

The row itself ("25 tests, 23 mutants (last logged before the freeze)", `:48`) is right, but the hedge is wrong:

`docs/archive/red-team/review3-gemini/findings.md:156`

```
Version `e662b7429b6b347d` represents a massive step forward in test harness hygiene (25 tests, 23 mutants killed, clean freeze verification). 
```

That is a reviewer reporting the gate it ran on frozen version 3, and `review3-gemini/findings.md:84` confirms it independently ("an adversarial mutant that survives all 25 tests in the frozen gate"). So 25/23 *is* the as-frozen count, directly evidenced rather than inferred. Fix: drop the hedge and cite the evidence — "row 3's count is confirmed by a round-3 reviewer's run on that hash (`review3-gemini/findings.md:156`)" — and remove "(last logged before the freeze)" from the row. This also removes a self-inflicted weakness: the report currently makes its own table look less reliable than the archive supports.


### 6. P3 — the two-word sentence carrying §6's central admission has an ambiguous antecedent, and §6's heading still says four errors while the Summary says six

`docs/report/technical-report.md:179-179`  ·  found by anthropic alone

**claude-code/F-7** (P3)

`docs/report/technical-report.md:179`

```
I rejected the mechanism in adjudication, on the ground that the identity is exact only in the population while the statistic uses a finite-window mean, and folded the observation into the structural rewrite. It was correct.
```

"It" has three candidate antecedents in the preceding clause — the finding, the rejection, and the structural rewrite — and the two readings that matter are opposites. A reader who takes "It" as the rejection gets the reverse of what `:189` says ("Two further errors were mine as adjudicator … The first is the rejection of R4-GM-02 above"). This is the sentence the section's transferable lesson depends on; it should not need the reader to reach `:189` to disambiguate. Fix: "The finding was correct, and rejecting it is why the blindness survived into version 5."

Related, same section: `:175` is headed "Four errors, and what caught them" and `:177` opens "exposed four errors of mine", while `:20` now says six. Either retitle to "Six errors, and what caught them" with the two adjudication errors as items five and six, or make the heading "Four design errors, and what caught them" so the count in the title and the count in the Summary agree.

