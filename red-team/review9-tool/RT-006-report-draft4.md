# Red-team review — RT-20260910-006

**FAIL** — 2 blocking problems with checked evidence.

306 files reviewed. 2 of 2 required model families produced a usable review (anthropic, google).
Nothing under review changed while they ran.

## Worth knowing

- 2 directories were skipped by name and never reviewed: docs/archive/red-team/.DS_Store, docs/archive/red-team/executable-proofs/.DS_Store
- codex did not count towards diversity — did not produce a review (error)
- antigravity: counted, but its model was NOT verified: "gemini-3.1-pro-high" is what was asked for, not what was observed — this tool does not report which model actually ran

## Who reviewed

| Reviewer | Model that actually ran | Family | Counts | Status | Time | Kept |
| --- | --- | --- | --- | --- | --- | --- |
| claude-code | `claude-opus-5` (envelope) | anthropic | yes | ok | 553s | 8 |
| codex | `gpt-5.6-sol` (session-log) | openai | **no** | error — Reading additional input from stdin... | 9s | — |
| antigravity | `gemini-3.1-pro-high` (pinned-slug) | google | yes | ok | 674s | 3 |

## What they found

### 1. BLOCKING — §9 still concentrates the estimator specifications in the adjudicating session; RT-005's fix was applied to §2 only

`docs/report/technical-report.md:213-214`  ·  **found by 2 families: anthropic, google**

**claude-code/F-2** (P2)

`docs/report/technical-report.md:213`

```
The roadmap, contract, specifications, simulator, gate, round prompts and adjudications were drafted by a Claude (Anthropic) session acting as my agent; the reviews, implementations and derivations in each round were produced by Codex (OpenAI), Gemini (Google) and a separate fresh-context Claude agent, working from identical prompts under the protocol of Section 2.
```

RT-005 item 2 (`claude-code/F-3`) asked for the correction in "§2 and §9". §2 took it:

`docs/report/technical-report.md:36`

```
- **Adjudication separate from review.** The roadmap, contract, interface specification, prompts and adjudications were drafted by one Claude session acting as my agent; the two estimator specifications were drafted, and after round 5 redrafted, by separate fresh-context Claude agents that had not seen the adjudications;
```

§9 did not. The unqualified plural "specifications" in the disclosure section reads across the two estimator specs, which the archive says were written elsewhere:

`docs/archive/red-team/readiness-protocol.md:74`

```
Both specs were drafted by fresh-context Claude agents and have not been seen by any other model.
```

So §2 and §9 now disagree with each other about who wrote the two documents from which every round-5 and round-6 implementation was built, and §9 understates the independence the programme actually had. This is the section whose only job is to be right about process. Fix: in line 213, replace "contract, specifications, simulator" with `"contract, interface specification, simulator"` and append after "acting as my agent" the §2 clause: `"; the two estimator specifications were drafted, and after round 5 redrafted, by separate fresh-context Claude agents that had not seen the adjudications"`.

**claude-code/F-3** (P2)

`docs/report/technical-report.md:213`

```
Its review against the archive was by a fresh-context Claude Opus agent and by a cross-model review tool in which the Anthropic and OpenAI reviewers reported and the Google reviewer failed on quota on each of three runs, so the report's own review covered two model families, one of them the family that drafted it.
```

The archive holds four tool runs: `review9-tool/RT-001-report-panel-incomplete.md`, `RT-002-report-draft1.md`, `RT-003-report-draft2.md`, `RT-005-report-draft3.md` — the last being the one draft 4 answers. Three of the sentence's assertions fail on RT-001:

`docs/archive/red-team/review9-tool/RT-001-report-panel-incomplete.md:19-21`

```
| claude-code | `claude-opus-5` (envelope) | anthropic | yes | ok | 261s | 8 (+1 unverified) |
| codex | `gpt-5.6-sol` (session-log) | openai | **no** | ok | 33s | 0 |
| antigravity | `gemini-3.1-pro-high` (pinned-slug) | google | **no** | ok | 50s | 0 |
```

The OpenAI reviewer did **not** report on that run (`Counts: no`, 0 kept), and the Google reviewer did not fail on quota there — both returned status `ok` and declined because the archive was out of scope (`RT-001…:12-13`). RT-001's verdict line is `PANEL_INCOMPLETE — only 1 model family produced a usable review; 2 required` (`RT-001…:3`). Quota failure is specific to RT-002, RT-003 and RT-005.

The wording was taken verbatim from RT-005's own suggested fix, which was already loose and is now one run stale. Fix: `"…and by a cross-model review tool run four times, in which the Google reviewer never produced a review — out of scope on the first run, quota-exhausted on the other three — and the OpenAI reviewer produced none on the first run either, so the report's own review covered two model families, one of them the family that drafted it."`

**antigravity/F-1** (P1, blocking)

`docs/report/technical-report.md:213-214`
```markdown
The roadmap, contract, specifications, simulator, gate, round prompts and adjudications were drafted by a Claude (Anthropic) session acting as my agent; the reviews, implementations and derivations in each round were produced by Codex (OpenAI), Gemini (Google) and a separate fresh-context Claude agent, working from identical prompts under the protocol of Section 2.
```

Draft 3 finding 2 explicitly flagged that lumping "specifications" together with the roadmap and adjudications is false, because the estimator specifications were drafted by separate fresh-context Claude agents that had not seen the adjudications. Draft 4 corrected Section 2 to reflect this separation but left Section 9 uncorrected, ignoring the required fix and creating a direct contradiction within the report.

Fix: `"The roadmap, contract, interface specification, simulator, gate, round prompts and adjudications were drafted by a Claude (Anthropic) session acting as my agent; the two estimator specifications were drafted, and after round 5 redrafted, by separate fresh-context Claude agents; the reviews, implementations and derivations in each round were produced by Codex (OpenAI), Gemini (Google) and a separate fresh-context Claude agent, working from identical prompts under the protocol of Section 2."`


### 2. BLOCKING — §4.4 attributes the option-C rescore to "the reviewers"; the round-8 adjudication attributes it to two of three

`docs/report/technical-report.md:163-167`  ·  found by anthropic alone

**claude-code/F-8** (P3)

`docs/report/technical-report.md:163`

```
The reviewers rescored the body-confounded plant at 3, the same as the repaired benchmark paper, and noted that a referee's first question, why not fit a latent state-space model, would have to be answered by a third arm.
```

`docs/archive/red-team/round8-adjudication.md:20`

```
Disputes with round 7 accepted: option C's novelty is **3, not 3.5 to 4** (Claude, Gemini; Codex reframes the unoccupied condition as body confounding plus a restricted estimator or insufficient excitation); the D-12 flip rule "C if non-identifiable in principle" is the wrong trigger and, applied honestly, routes away from C (three of three).
```

Two reviewers rescored; the third reframed the condition rather than restating a number. The round log at `readiness-protocol.md:121` says "C's novelty 3 (three of three)", so the report is following the looser of two archive statements — but the adjudication is the more specific record, and the report elsewhere is careful to say how many implementations produced each figure. Fix: `"Two of the three rescored the body-confounded plant at 3, the same as the repaired benchmark paper, and the third reframed what is unoccupied about it as body confounding plus a restricted estimator; all three noted that a referee's first question, why not fit a latent state-space model, would have to be answered by a third arm."`

---

**Checked and clean, for the record.** Table 2 and its clustered lower bounds (0.155 / 0.153 / 0.158) against `round5-adjudication-and-tally.md:12`; the +0.187→+0.210 hash-seed spread against `review5-claude-opus/sim_frozen.hashseed1.txt:196`; 0.975 / 0.774 / 0.845 against `review5-claude-opus/schange_split.output.txt:7`; Table 3 and the 0.70–0.73 bounds against `round6-adjudication-and-tally.md:11-15`; controls 0.500 / 0.422 / 0.200 and the negated-vector 0.80 against `review6-codex/report.md:156-159`; family N 0.84 vs 0.73 against `round6-adjudication-and-tally.md:33`; Δ_c's 0.55–0.66 pre-event ranking and "two reviewers" against `round6-adjudication-and-tally.md:25`; Table 4 and both parenthetical conditions against `round7-adjudication.md:9-12`; all six §4.4 conclusions and the disputed adaptation sign against `round8-adjudication.md:7-13`; the β_a limit and κ, which I re-derived and which is correct including the Sherman-Morrison reduction of Var(a)⁻¹; ρ_u = 0.8, ρ_min = 0.4, the 4/2/4/10 block sizes and four padding channels, CL-4 by construction and the severed-action witness against `executable-proofs/gate/reference_generator.py:9-12`, `:33-36`, `:204-217`; 66 tests / 47 mutants / exit 0 against `executable-proofs/gate/gate.output.txt:70-121`; the six D-11 parts against `decisions-required.md:21-30`; all six references against `review9-claude-opus/report-review.md:250`. Every path in `file-map.md` resolves, including `review5-gemini/sim_frozen_results.json`, `review6-claude-opus/results/`, `review8-claude-opus/check_algebra.py` and `findings.md` F2 — I have no findings against it.

**claude-code/F-1** (P1, blocking)

`docs/report/technical-report.md:167`

```
**Sign-randomised probing, online and at a 5 percent probe budget, was not degraded by the shared-cause confounder that reduced a frozen passive residual monitor's full-channel AUC by about 0.2 in the base cells.** The passive monitor's loss came from crediting confounded distractors with control; the probed estimator scored 0.85 to 0.87 with and without the confounder: measured by three implementations in round 5, where it did not clear its margin on the perturbation set, and by two in round 6.
```

Two errors in one sentence.

First, "measured by three implementations in round 5". Round 5's primary *was* the full-channel AUC, and the three implementations put the probed arm at 0.800 / 0.815 / 0.831 in the base cell — Table 2 of this same report, eighty lines earlier:

`docs/report/technical-report.md:91`

```
| Sequential IBD AUC | 0.800 | 0.815 | 0.831 |
```

`round5-adjudication-and-tally.md:9` gives the same three numbers, and `round5-adjudication-and-tally.md:18` characterises the arm as "AUC 0.80 to 0.85". No round-5 implementation produced 0.85–0.87.

Second, 0.85–0.87 is the round-6 *secondary*, and it is the delay-0 subset only. Both round-6 implementations that reported a secondary give ~0.75 at delay 2:

`docs/archive/red-team/review6-claude-opus/report.txt:209-224`

```
L_Nx10_tau0     seq_ibd   present      0.851    0.810    0.891
L_Nx10_tau0     seq_ibd   absent       0.863    0.830    0.897
L_Nx10_tau0     comparatorpresent      0.795    0.758    0.829
L_Nx10_tau0     comparatorabsent       0.964    0.953    0.972
L_Nx10_tau2     seq_ibd   present      0.753    0.666    0.836
L_Nx10_tau2     seq_ibd   absent       0.751    0.661    0.836
```

`review6-codex/report.md:16-19` agrees (0.753 / 0.751 at `L_Nx10_tau2`, 0.768 / 0.756 at `L_Nx30_tau2`). The true two-implementation range across the four family-L base cells is 0.751 to 0.869, not 0.85 to 0.87. The report's own `file-map.md:18` points a reader at exactly these two files for this number.

The same range is asserted again at `docs/report/technical-report.md:124` ("while the interventional arm scored 0.85 to 0.87 in both"). Both sentences inherit `round6-adjudication-and-tally.md:31`, which is where the range was first narrowed; the report is faithful to the adjudication and the adjudication is wrong against the reviewer output it summarises.

The substantive claim — present ≈ absent, so the probed arm is not degraded — survives intact and is stronger evidence than the range: the present/absent pairs differ by ≤ 0.013 in every cell. Fix: drop the round-5 attribution for this number and widen the range. `"…the probed estimator's own score barely moved between conditions — 0.851 against 0.863 at delay 0 and 0.753 against 0.751 at delay 2, over the four family-L base cells: measured on the full channel set by three implementations in round 5 (0.80 to 0.83 in the base cell, where it did not clear its margin on the perturbation set) and by two in round 6."` Correct line 124 the same way, and record that the adjudication's "0.85 to 0.87" was a delay-0 read.


### 3. P2 — §6 says the round-4 comparator disagreement was blamed on the generator; the round-4 record names two convergent causes and repaired the comparator for the second

`docs/report/technical-report.md:179-179`  ·  **found by 2 families: anthropic, google**

**claude-code/F-7** (P3)

`docs/report/technical-report.md:179`

```
**A change score that could not see the change.** The comparator's innovation-mean-shift statistic was specified by analogy with a CUSUM on residuals. Under a centred policy an actuator loss leaves the residual mean unchanged. The statistic entered at version 4, survived round 4, in which three models implemented both arms on instances of their own and disagreed by 0.2 AUC on the comparator, a disagreement that was blamed on the unspecified generator, and was found in round 5, the first round on one frozen generator, by one reviewer's algebra and two reviewers' measurements.
```

`docs/archive/red-team/round4-adjudication-and-tally.md:15`

```
Three implementations agree about the interventional arm to within 0.012 and disagree about the comparator by 0.20, so the decision rule flips while the method under test does not move. Two causes, both convergent across reviewers:
```

and `round4-adjudication-and-tally.md:28-29` record the second cause as a convergent three-reviewer finding with its own decision:

```
| Comparator structurally incapable (downstream loading; τ = 2 delay misalignment; ridge not unit-invariant) | Opus R4-2/3, Codex CX-01/02, Gemini GM-02 (mechanism disputed, category accepted) | **D-10.2**: delay-aware, multi-horizon comparator with standardised features; re-run the margin on the frozen generator before any δ is touched |
| R0-absent equivalence fails everywhere because the comparator is weak without confounding too | Opus R4-6, Codex, Gemini | **D-10.3**: replace equivalence with a comparator-competence validity check |
```

Round 4 did diagnose the comparator, three of three, and rewrote it; what it missed was the specific mean-shift blindness. §6 is the section the report offers as its transferable contribution, so the mechanism claim ("the freeze is what made it findable") should not be built on a version of round 4 in which the comparator went unquestioned. Fix: `"…and disagreed by 0.2 AUC on the comparator. Round 4 found the comparator structurally incapable, three of three, and D-10.2 rewrote it — but the disagreement was attributed to the unspecified generator and to loading and delay misalignment, not to the change term, and the specific blindness survived into version 5, where it was found by one reviewer's algebra and two reviewers' measurements in the first round on one frozen generator."`

**antigravity/F-2** (P2)

`docs/report/technical-report.md:179`
```markdown
The statistic entered at version 4, survived round 4, in which three models implemented both arms on instances of their own and disagreed by 0.2 AUC on the comparator, a disagreement that was blamed on the unspecified generator, and was found in round 5, the first round on one frozen generator, by one reviewer's algebra and two reviewers' measurements.
```

The sentence chains six distinct clauses together with commas and "and", making it very difficult to parse the chronological facts. It reads like a machine-written summary struggling to condense a timeline into one thought.

Fix: Break it into two sentences: `"The statistic entered at version 4 and survived round 4, where three models implemented both arms on their own instances and disagreed by 0.2 AUC on the comparator — a disagreement blamed at the time on the unspecified generator. It was finally caught in round 5, the first round on a single frozen generator, by one reviewer's algebra and two reviewers' measurements."`


### 4. P2 — §2's "six conditions" are not the readiness protocol's six: the convergence rule is dropped and replaced by an unlisted one

`docs/report/technical-report.md:37-37`  ·  found by anthropic alone

**claude-code/F-4** (P2)

`docs/report/technical-report.md:37`

```
- **Executable exit criteria.** The readiness protocol set six conditions for a version: the gate directory of assertion tests and mutants exits 0 from a clean checkout; every registered mutant is killed; the count of normative items without a test identifier is zero; an independent black-box acceptance suite written from the interface specification passes; a hand-computed reference case matches the pipeline; and a runtime pilot has measured per-cell duration. Only the first three were exercised, and the gate's exit code was the criterion used in practice; the acceptance suite, the reference case and the pilot were never done, so no version was readiness-certified.
```

The protocol's six are:

`docs/archive/red-team/readiness-protocol.md:11-17`

```
A frozen version is ready when all of the following are green, none of which is an opinion:
1. Coverage matrix: zero uncovered normative items.
2. Every mutant makes at least one test fail; a reintroduced historical bug fails the gate.
3. Black-box acceptance suite, written by an agent other than the builder, from `interface-spec.md` only, passes.
4. Daniel's hand-computed rectangular, noisy, censored case matches both the pipeline and `contract_ref.py`.
5. Runtime pilot has run and per-cell durations are recorded.
6. Convergence rule below is satisfied.
```

Condition 6, the three-reviewer convergence rule, is missing from the report's list, and "the gate directory … exits 0 from a clean checkout" appears in the list although it is not one of the six (it is the *mechanism* for conditions 1 and 2). Consequently "Only the first three were exercised" is also wrong in the other direction: the convergence rule is the one condition the programme exercised most thoroughly, in eight rounds, and it is the entire warrant for Sections 4.1 and 4.2. This is the same misstatement RT-005 item 2 flagged (`codex/F-1`: "six conjunctive conditions, including the three omitted activities **and cross-model convergence**"), reworded rather than repaired. It also matters for `technical-report.md:200`, which repeats the count.

Fix: list the six as the protocol states them (zero uncovered normative items; every mutant kills; independent acceptance suite; hand-computed reference case; runtime pilot; convergence rule), then: `"Conditions 1, 2 and 6 were exercised — the gate's exit code was the operational test of the first two, and the convergence rule ran in every round from 1 to 8. Conditions 3, 4 and 5 were never done, so no version was readiness-certified."`


### 5. P2 — Table 1's gate count for frozen version 3 is taken from two revisions before the version that was actually frozen, against the caption's own rule

`docs/report/technical-report.md:48-48`  ·  found by anthropic alone

**claude-code/F-5** (P2)

`docs/report/technical-report.md:48`

```
| 3 | 7 Sep | prose + implementation | e662b7429b6b347d | 23 tests, 23 mutants | Contract v3.3, IBD spec draft 2; each reviewer built its own simulation |
```

`docs/report/technical-report.md:55`

```
Gate counts are for the version as frozen, not after the repairs the round prompted.
```

23 tests / 23 mutants is the post-round-2 repair state, which the archive attaches to a *different*, superseded candidate hash:

`docs/archive/red-team/readiness-protocol.md:49`

```
- Post-round-2 repair: gate rebuilt (23 tests; 23/23 reviewer and author mutants killed; fake-kill fixed; `aggregate_primary` added); `roadmap-v4.2-amendments.md` applies safe corrections only; `decisions-required.md` holds D-1 to D-5. Freeze manifest and `freeze.py` introduced (FB-19). **Candidate frozen version 3 hash: `2945e545818839ea`** (manifest order). Not a review target until D-1 to D-5 are answered and contract v3.2 / interface v3 are produced.
```

Two gate revisions then landed before `e662b7429b6b347d` was frozen. The archive records the intermediate one explicitly:

`docs/archive/red-team/README.md:123`

```
- Gate: 25 tests; 23 reviewer mutants killed; alarm counting and matching added; recursion and identity guards on mutants.
```

That state precedes candidate `f694022256fe497e` (`README.md:125`), which itself precedes frozen version 3 (`README.md:133`), and frozen version 3 added interface v3 and the IBD spec draft 2 to the normative set. Row 3 therefore reports a count from before D-1 to D-5, D-6, D-7 and D-8 were applied. The as-frozen count for `e662b7429b6b347d` is between 25 and the 31 recorded after the round-3 repair (`readiness-protocol.md:64`) and is not logged anywhere as 23.

Rows 2, 4, 5 and 6 check out against `readiness-protocol.md:38`, `:68`, `:85` and `:97`. Fix row 3 to `25 tests, 23 mutants (last logged before the freeze)` and add to the caption: `"Row 3's count is the last one logged before that freeze; the gate gained tests with interface v3 and the IBD spec draft and the as-frozen count was not recorded."`


### 6. P3 — Section 6 ends with a padded non sequitur about laptop runtimes

`docs/report/technical-report.md:188-188`  ·  found by google alone

**antigravity/F-3** (P3)
Citation: the cited lines are out by 1 (the text is at 187-187, cited as 188-188)

`docs/report/technical-report.md:188`
```markdown
The round-6 simulations took 5 to 21 minutes each on a laptop; reviewer implementation and analysis time was not recorded, and the diagnoses were written up the same day.
```

This sentence is tacked onto the end of a paragraph analyzing the logical mechanisms of the four defects. Execution time and process details belong in the process overview (Section 2, where laptop runtimes are already mentioned), not as a trailing thought in the error diagnosis section. It reads as a padded, generic transition.

Fix: Delete the sentence entirely from Section 6.


### 7. P3 — §8 says the stale Python 3.14 environment was removed; three 3.14 bytecode caches (and three 3.13 ones) are still in the gate directory

`docs/report/technical-report.md:207-207`  ·  found by anthropic alone

**claude-code/F-6** (P3)

`docs/report/technical-report.md:207`

```
The stale Python 3.14 environment that a reviewer had left inside the gate directory was removed before publication.
```

The archive's own note is narrower — it deletes a `.venv`, not "the environment":

`docs/archive/red-team/CHECKPOINT.md:17`

```
The stale Python 3.14 `.venv` inside the gate directory (not a manifest file) was deleted on 9 Sep before publication.
```

`executable-proofs/gate/__pycache__/` still ships `contract_ref.cpython-314.pyc`, `test_gate.cpython-314.pyc`, `test_proof_theatre.cpython-314.pyc`, plus `contract_ref.cpython-313.pyc`, `run_gate.cpython-313.pyc`, `test_gate.cpython-313.pyc` and `test_proof_theatre.cpython-313.pyc`. A reader who opens the gate directory to check the report's Python-3.12-only claim finds compiled artefacts from three interpreters, two of which `run_gate.py:9` refuses to run under. It also makes "exits 0 from a clean checkout" (`technical-report.md:37`) untested as published — nothing in the archive is a clean checkout. Fix: either delete `__pycache__/` from the published archive, or say `"the stale Python 3.14 virtual environment was removed before publication; bytecode caches from other interpreters remain in the gate's `__pycache__` and are not part of the freeze manifest."`

