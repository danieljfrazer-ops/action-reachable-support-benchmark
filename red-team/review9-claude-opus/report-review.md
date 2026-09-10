# Review 9 — technical report, hostile referee and fact-check

Reviewer: fresh-context Claude Opus. Date: 9 September 2026. Target: `docs/report/technical-report.md` (196 lines; the PDF is built from it by `build_report.py` at the same timestamp).

**What I did.** I checked every number, hash, date, count and attribution in the report against `round5-adjudication-and-tally.md`, `round6-adjudication-and-tally.md`, `round7-adjudication.md`, `round8-adjudication.md`, `decisions-required.md`, `readiness-protocol.md`, `stage-0a-contract-v3.9.md`, `comparator-spec.md`, `sequential-ibd-spec.md`, `findings.md`, `research-round-2.md`, the `review5-*` to `review8-*` folders, and the rounds 2–4 adjudications. I executed `freeze.py` and `executable-proofs/gate/run_gate.py`. I fetched the IBD paper (arXiv:2603.18257v2) and verified its title, authors, Proposition 3.3 and the §3.2 sentence the report relies on, and verified the Heirung & Mesbah citation.

**Counts.** 9 blocking, 21 should-fix, 15 optional (45 items).

**Verdict in one line.** The report is unusually honest in substance and the large majority of its numbers are right; but it overstates the strength of the three-model record in five specific places, one table row carries the wrong hash and the wrong round type, the artefact section presents the gate as clean when the record says three reviewer mutants survive it, and the disclosure omits that the adjudications themselves were drafted by an AI in the author's chair. I would not put my name on it until items 1–9 are fixed.

---

## A. Blocking

### 1. Table 1, round 4: wrong freeze hash (blocking)

The report gives round 4's frozen version as `0468104f6431b050`, which is version 5, the round-**5** target. Version 4 is `442cc4b7da691ca0` (`readiness-protocol.md` line 70, "Frozen version 4 — `442cc4b7da691ca0` (7 Sep 2026): both arm specifications"; `round4-adjudication-and-tally.md` line 1, "frozen 442cc4b7da691ca0, both arm specifications"). The parenthetical "(candidate)" does not rescue it: the candidate hashes around round 4 were `808ab3be48001e5e` and `cdff131a33dd1c3a` (`readiness-protocol.md` lines 64, 68), neither of which is `0468104f6431b050`.

Replace, Table 1 row 4, column "Frozen version": `0468104f6431b050 (candidate)` → `442cc4b7da691ca0`

### 2. Table 1, "Type" column: rounds 3 and 4 were cross-model implementation rounds, not prose (blocking)

The report labels rounds 3 and 4 "prose + gate" and its Summary says "Rounds 5 and 6 were execution rounds". The archive says all three reviewers wrote and ran independent simulations in round 3 (`round3-adjudication-and-tally.md` line 3: "all three built independent simulations of a contract-B instance and the draft-2 detector"; `readiness-protocol.md` line 63) and implemented both arms end-to-end in round 4 (`round4-adjudication-and-tally.md` line 3: "each implemented both arms end-to-end from the two specifications alone"; `readiness-protocol.md` line 78). Round 4's headline table (`round4-adjudication-and-tally.md` lines 7–14) shows the three implementations *disagreeing* — comparator AUC 0.637 / 0.710 / 0.840, benefit +0.170 / +0.103 / +0.009, "the confounding-benefit verdict flips across models".

This matters beyond bookkeeping. The report's central methodological claim in §6 is that defects invisible in prose became obvious as soon as three systems ran code. Round 4 *was* three systems running code, and it did not catch either round-5 defect, because the generator was not yet frozen. That is a more interesting and more defensible claim than the one the report makes, and it is the one the record supports.

Replace Table 1 row 3 "prose + gate" → `prose + simulation`; row 4 "prose + gate" → `prose + implementation`.

Add to §2, after "In execution rounds each reviewer implements both estimators from the specifications alone.":
> Rounds 3 and 4 also required independent implementations, but on each reviewer's own instance of the written model. Round 4's three implementations disagreed by up to 0.20 AUC on the comparator and flipped the confounding verdict, which is why the generator itself was frozen for round 5; rounds 5 and 6 are the rounds in which three implementations ran on the same instances.

### 3. §6: "This survived four prose rounds" is false (blocking)

Two errors. (a) The comparator as "channel-agnostic CUSUM on innovations of a linear predictor" first appears in `roadmap-v4.md` line 17 and `stage-0a-contract-v3.md` line 111, so it was in the frozen set for rounds 1–4; but the *mean-shift term* whose blindness was the defect — "the second term is the two-sided standardised innovation-mean shift" — first appears in `stage-0a-contract-v3.5.md` line 143 and in `comparator-spec.md` v1, i.e. at version 4, the round-4 target. (b) Round 4 was not a prose round (item 2). So the defect survived one round, and that round was an implementation round.

Replace:
> This survived four prose rounds and was found in the first execution round, in one afternoon, by one reviewer's algebra and two reviewers' measurements.

With:
> The mean-shift term entered the contract at version 4 and survived the round-4 implementation round, where three reviewers built the arm on three different instances of the model and disagreed with each other by 0.20 AUC — enough noise to hide it. It was found in round 5, the first round in which the three ran on the same frozen instances, by one reviewer's algebra and two reviewers' measurements.

### 4. Summary and §4.1: round 5 did not agree to three decimal places (blocking)

Summary: "all three agreed to three decimal places on every number both times." §4.1: "Three independent implementations agreed on every number."

Round 5's own table contradicts this, and so does the report's own Table 2 three lines later: 0.800 / 0.815 / 0.831; 0.691 / 0.688 / 0.675; +0.187 / +0.204 / +0.190 (`round5-adjudication-and-tally.md` lines 9–13). The adjudication's claim is "agree to within Monte Carlo error" (line 16). Three-decimal agreement is a round-6 fact only (`round6-adjudication-and-tally.md` line 7).

Replace in the Summary:
> and all three agreed to three decimal places on every number both times.

With:
> and both times the three agreed: within Monte Carlo error in round 5, and to three decimal places on every number in round 6, once the generator as well as the specifications was frozen.

Replace in §4.1: "Three independent implementations agreed on every number." → "Three independent implementations agreed within Monte Carlo error on every number."

### 5. Table 1 caption: `freeze.py` does not recompute those hashes (blocking)

Caption: "Hashes are the first sixteen hex digits of the freeze hash; `freeze.py` in the archive recomputes them."

`freeze.py` hashes the files listed in the *current* `freeze-manifest.txt` in their current state; it has no version argument and no history. **Run today it prints `1fcd1c5784a78fda`, which is none of the eight hashes in the table.** The archive already records that this is expected: `readiness-protocol.md` line 104 and `CHECKPOINT.md` say that after round 6 closed, `decisions-required.md` (a manifest file) gained D-12 and "`freeze.py` now prints `eee1ab5834e35788`; only that file differs from version 6". D-13 has since been added, moving it again. A reader who tries the one verification step the report offers will get a mismatch and conclude the report is wrong.

Replace the caption with:
> Table 1. The eight rounds. Hashes are the first sixteen hex digits of a SHA-256 over the manifest files concatenated in order, as computed by `freeze.py`. They are historical: the manifest includes the decision log, which has been appended to since, so `freeze.py` run today reproduces none of them. Reproducing a row requires checking the manifest files out at that round's state.

(Opinion: if you want a verifiable claim here, commit the archive to git and give each row a commit id. Without that, every hash in this table is decoration.)

### 6. §4.1: the 0.975 constant-control number is one model's, on a conditioned subset (blocking)

The paragraph opens "Three independent implementations agreed on every number" and later states: "A per-channel vector fixed at fit time, which never saw the scored episode or the event, scored 0.975 against 0.77 to 0.83 for the two arms."

That number is Claude Opus's alone. `review5-claude-opus/findings.md` line 64 (R5-4): "AUC(static `l`) = **0.975** (τ=0) / **0.969** (τ=2) against seq_ibd 0.774 / 0.882 and the comparator 0.845 / 0.831 (`schange_split.output.txt`)", **confounder absent, restricted to the instances where the event actually changes S^obs,ε**. `round5-adjudication-and-tally.md` line 22 attributes it to Opus ("Opus: a fit-time constant…") and reserves "(three of three)" for the CL-4 finding, not for the number. The report's "0.77 to 0.83 for the two arms" also drops the two cells above that range (0.845 and 0.882): it reproduces the adjudication's lossy summary rather than the source.

Replace with:
> One reviewer measured the consequence directly: a per-channel vector fixed at fit time, which never saw the scored episode or the event, scored 0.975 with the confounder absent on the instances where the event did change the support, against 0.77 and 0.85 for the two arms in the same cell. That number is single-model and was not reproduced; the finding that the event usually changes nothing was reported by all three.

### 7. §5 and §4.2: the round-6 attribution numbers are not a three-implementation measurement (blocking)

§5 claims: "Measured twice by three implementations, about +0.2 AUC on the full channel set." §4.2 gives the round-6 secondary as 0.73 to 0.80 present against 0.96 to 0.98 absent, interventional arm 0.85 to 0.87.

`round6-adjudication-and-tally.md` line 27 (finding 9): "**Gemini's secondary numbers at offsets 200 and 500 are wrong**: its script read `secondary_support()` after the episode ended (Codex). Its primary numbers and verdicts are unaffected. Recorded, not counted." The secondary is exactly the measure that carries the attribution result at offset 500, so the round-6 replication of the attribution finding rests on two implementations, not three. The primary — the adaptation result — is genuinely three of three; the attribution half is not.

Replace in §5:
> Measured twice by three implementations, about +0.2 AUC on the full channel set.

With:
> Measured by three implementations in round 5 on the then-primary full-channel measure, and again in round 6 as a secondary, where one reviewer's script read the support after the episode ended and its secondary numbers were discarded, leaving two implementations for the second measurement.

Add to §4.2, after "…while the interventional arm scored 0.85 to 0.87 in both.":
> One of the three round-6 secondary implementations was excluded: its script read the support after the episode ended. Its primary numbers, and therefore every verdict above, are unaffected.

### 8. §8 and the Summary: the gate is presented as clean; the record says three mutants survive it and generator mutants cannot be registered at all (blocking)

Summary: "a certified generator and test gate that others can reuse". §8: "the test gate (66 tests and 47 mutants at version 6; exit code 0 under Python 3.12 and NumPy 2.4.4)".

I ran it: 66 tests, 47/47 mutants killed, exit 0 — confirmed. But `round6-adjudication-and-tally.md` line 26 records, as an adjudicated finding, that three reviewer-written mutants survive the gate, one against the primary metric itself: "`auc_pre_event_support` over `pre | post` survives because every fixture has post ⊆ pre (Claude, confirmed by Codex and Gemini); family-N certificate mutants survive… the mutation framework iterates `test_gate` only, so **no generator mutant is registrable** (three of three)". `CHECKPOINT.md` repeats it. "47 mutants, exit code 0" is true and, without that sentence, misleading: the 47 are the ones the gate's authors registered, and the framework structurally cannot register a mutant against the generator — the artefact the report offers for reuse.

Replace in §8:
> the test gate (66 tests and 47 mutants at version 6; exit code 0 under Python 3.12 and NumPy 2.4.4)

With:
> the test gate (66 tests and 47 registered mutants at version 6; exit code 0 under Python 3.12 and NumPy 2.4.4, verified again for this report), together with the three reviewer-written mutants that survive it — one against the primary metric, two against the family-N certificate — and the structural gap that lets them survive: the mutation runner iterates the test module only, so no mutant against the reference generator can be registered

Change the Summary phrase "a certified generator and test gate that others can reuse" → "a certified generator and a test gate, with the gate's own blind spots recorded".

### 9. §2 and §9: the adjudications were drafted by an AI in the author's chair, and the disclosure does not say so (blocking)

§2: "**Author adjudicates, never reviews.** I decide estimands and design decisions and write the adjudication after all three report." §9: "I set the question, decided every estimand and design change, adjudicated each round… This report was drafted with AI assistance from the archived adjudications and edited by me."

The archive's own headers contradict "I … write the adjudication":
- `round2-adjudication-and-tally.md` line 3: "**Author of the artefacts: Claude (this context).** Reviewers: Fable (fresh context), Codex, Gemini, Opus (fresh context)… Per the readiness protocol, the author adjudicates but does not review."
- `round3-adjudication-and-tally.md` line 3: "**Author (Claude, this context) adjudicates and does not review.**"

The same context also wrote the roadmap, the contract, the interface spec and the round prompts. The honest description is: a fourth AI session held the author-and-adjudicator role and wrote the adjudications; a human set the question and took the decisions recorded in `decisions-required.md` (line 19 records Daniel's actual words, "Adopt all six recommendations, proceed to Step 3"). That is still a defensible protocol — arguably a more interesting one — but a report that says "I write the adjudication" while the archive says Claude wrote it is a disclosure failure, and it is the thing a hostile reader will seize on.

Replace in §2:
> - **Author adjudicates, never reviews.** I decide estimands and design decisions and write the adjudication after all three report. I do not review or implement.

With:
> - **The author role is separate from the reviewer role.** After all three reviewers report, the adjudication — the tally of findings, the recommendation, the tabled decisions — is drafted in a separate AI session that holds the author role and does not review or implement. I take every decision it puts to me, and the decision log records what I chose. No reviewer implements the repairs it recommends.

Replace in §9:
> I set the question, decided every estimand and design change, adjudicated each round, and am responsible for the errors in Section 6. This report was drafted with AI assistance from the archived adjudications and edited by me.

With:
> The specifications, the contract, the round prompts and the adjudications were also written by an AI session holding the author role, distinct from the three reviewer sessions; the archive records which session wrote what. I set the question, took every decision put to me — including the two re-posings that produced the errors in Section 6, which are mine — and edited this report, which was drafted with AI assistance from the archived adjudications.

---

## B. Should-fix — fact-check and overreach

### 10. Table 1, gate counts for rounds 3 and 4 are post-repair figures (should-fix)

Row 2's "17 tests" is the gate in the version round 2 reviewed (`readiness-protocol.md` line 38). Rows 3 and 4 are not: the version round 3 reviewed carried the 23-test gate rebuilt after round 2 (line 49), and 31 tests is the *post*-round-3 repair (line 64); the version round 4 reviewed carried 34 tests and 35 mutants (line 68, "Post-D-9 repair: gate 34 tests, 35 mutants killed"), and 37 tests / 40 mutants is the *post*-round-4 repair (line 79). The column mixes two conventions without saying so.

Fix: use as-reviewed counts — row 3 "…IBD spec draft 2; 23 tests"; row 4 "Both estimator specs; 34 tests, 35 mutants" — or add to the caption: "Test and mutant counts are the gate as frozen for that round; the repair that followed each round raised them."

### 11. Table 1, row 1 mislabels round 1 (should-fix)

Row 1 reads "Red team of the original roadmap; prior-art check". Round 1, frozen `c197652c0d8e846b`, reviewed `roadmap-v4.md`, `stage-0a-contract-v3.md`, `interface-spec.md`, `confirmation-design.csv` and the gate (`readiness-protocol.md` line 21) — the *already re-aimed* plan. The red team of the original roadmap, and the prior-art check that killed the original hypothesis, was a separate single-model pass by one Claude model on 6 September, before the protocol started (`README.md` lines 3–6: "Target document: `../persistent-adaptive-ai-research-roadmap.html`… Reviewer: Claude (Fable 5.1)"; `findings.md` line 29 F2; `research-round-2.md` line 24). §1 gets this right ("A first red-team pass"); Table 1 does not, and as it stands implies the prior-art finding is one of the eight three-model rounds.

Replace row 1's "What it did" with: `Red team of the roadmap as re-aimed after the prior-art pass; first cross-model round`. Add under the table: "The prior-art pass that re-aimed the programme (§1) preceded round 1 and was single-model; it is in the archive as `findings.md` and `research-round-2.md`."

### 12. Summary: "each round on a frozen, hashed version" is contradicted by the report's own table (should-fix)

Table 1 gives rounds 7 and 8 the frozen version "as reviewed" — prose rounds on the existing archive, with no new freeze (`readiness-protocol.md` lines 106–121). Replace "each round on a frozen, hashed version of the specifications and code" with "six of them on a frozen, hashed version of the specifications and code and two on the archive as it stood".

### 13. §6: the execution-round cost is understated (should-fix)

"The cost of an execution round was under twenty minutes of laptop time per reviewer." `round6-adjudication-and-tally.md` line 3: "Runtimes 5 to 21 minutes, no seed reduction." Replace "under twenty minutes" with "5 to 21 minutes".

### 14. §4.4: "the three systems predicted three different signs" is wrong (should-fix)

`round8-adjudication.md` line 12: "Claude predicts the passive arm still wins (less so), **Codex says not sign-determined** without inequalities on G_b, B, noise and paths, Gemini predicts the probe arm wins." Confirmed at source: `review8-codex/derivation.md` line 255, "Which arm has higher pre-support AUC when `G_b!=0` is **not sign-determined**". `readiness-protocol.md` line 121 records "(Claude −, Codex ?, Gemini +)". Two opposite predictions and one refusal is not three signs.

Replace with:
> two systems predicted opposite signs and the third showed the sign is not determined without inequalities on the couplings, the noise scales and the alternative paths.

### 15. §4.4: "the confuser produces the larger signal" overstates the derivation (should-fix)

`round8-adjudication.md` line 9: "under E2 with G_b ≠ 0 the signal is **comparable to or larger than** E1's and lands on channels the loss never touches." Replace "the confuser produces the larger signal on channels the loss never touches" with "the confuser's signal is comparable to or larger than the loss's, and lands on channels the loss never touches".

### 16. §4.2: "six decisions" followed by seven clauses (should-fix)

The sentence lists: certify the event structurally; score over the pre-event support; replace the change statistic; seal confirmation seeds; implement family N; run the alarm clock from reset; fit per instance. That is seven. D-11 has six parts because the first two are both D-11.1(a) (`decisions-required.md` line 25). Merge the first two: "certify the event structurally and score the primary over the resulting pre-event support only, so that a channel-constant statistic scores exactly 0.5;".

### 17. §4.2: the specs were redrafted by fresh-context agents, not by reviewers (should-fix)

"Fresh reviewers redrafted both specifications against the new contract" conflicts with §2's own role separation. The archive says fresh-context Claude agents drafted the specs (`readiness-protocol.md` line 74: "Both specs were drafted by fresh-context Claude agents and have not been seen by any other model"). Replace "Fresh reviewers redrafted" with "Fresh-context agents, none of them a round-5 reviewer, redrafted".

### 18. §2: "the identical prompt goes to Claude (Opus), Codex and Gemini" is not true of every round (should-fix)

Round 2 had four reviewers, two of them Claude models: "Reviewers: Fable (fresh context), Codex, Gemini, Opus (fresh context)" (`round2-adjudication-and-tally.md` line 3; `readiness-protocol.md` line 45). Round 3's prompt asks for "a fresh-context Claude on a different model" (line 57). Replace with "the identical prompt goes to a fresh-context Claude, to Codex and to Gemini (round 2 had two Claude reviewers on different models, so four reviews)".

### 19. §2: "Three reviewers, fresh context" claims more than the archive records (should-fix)

The archive documents fresh context only for the Claude reviewer — every round header names "fresh-context Claude Opus" and says nothing of the kind about Codex or Gemini (`round5-adjudication-and-tally.md` line 3; `round6-adjudication-and-tally.md` line 3; `round3-adjudication-and-tally.md` line 3). The report's argument rests on reviewer independence, and a referee will ask how it was enforced on the two systems the author does not control.

Replace "Each reviewer starts without memory of previous rounds and may read earlier reviews only after writing its own." with:
> The Claude reviewer is a fresh context each round; Codex and Gemini are given the identical prompt in their own sessions, and the prompt forbids reading the other reviews, or any earlier review folder, before their own findings are written. Whether their sessions carried context from earlier rounds is not something I can certify.

### 20. §2: readiness had six conditions, not one (should-fix)

"the criterion for readiness is the gate's exit code, not prose" compresses `readiness-protocol.md` lines 11–17, where "ready" requires all of: zero uncovered normative items; every mutant killed; a black-box acceptance suite written by an agent other than the builder from the interface spec only; the author's hand-computed rectangular, noisy, censored case matching the pipeline and `contract_ref.py`; a runtime pilot with recorded per-cell durations; and the convergence rule. Three were never done (item 30). As written, the report both overstates the rigour and hides the gap.

Replace with:
> **Exit criteria are executable.** Readiness is defined by six conditions in the protocol, five of them executable — full coverage of normative items, every mutant killed, an independently written black-box acceptance suite, a hand-computed reference case, a recorded runtime pilot — plus the cross-model convergence rule. Three were met; Section 7 says which were not.

### 21. §4.1: "the competence floor failed in every cell" is one reviewer's weaker claim generalised (should-fix)

`round5-adjudication-and-tally.md` line 14 records "fails **10 of 12** cell-offsets" (Opus) against "fails all 4 base cells" (Codex, Gemini). "In every cell" is true of the four base cells and false of the twelve cell-offsets. Replace with "the competence floor failed in every base cell, and at ten of the twelve cell-offsets one reviewer scored".

### 22. §4.1 and §5: the perturbation set failed the margin, and the report does not say so (should-fix)

The report says "The confounding benefit cleared the pre-declared margin of 0.10 in every base cell" and stops. `round5-adjudication-and-tally.md` line 19 continues: "**but the perturbation set does not** (aggregate lower bound 0.090; individual configurations from −0.015 to +0.25)". The Summary's "a margin of about 0.2 AUC" and §5's "about +0.2 AUC" inherit the omission.

Append: "…in every base cell, but not on the perturbation set, where the aggregate lower bound was 0.090 and individual configurations ran from −0.015 to +0.25." Add to §5's first surviving statement: "The margin is a base-cell figure; over the coupling-and-noise perturbation set it ranged from about zero to +0.25."

### 23. §7: the winning comparator's statistic was shown not to be blind before the event (should-fix)

Two or three of three reviewers found that Δ_c's stated null does not hold and that the score already ranks the support before anything changes: "Δ_c's stated chi-square null does not hold under closed-loop dependence and the score is not blind before the event (fault-free AUC 0.55 to 0.66 in 15 of 15 cells; Codex, Claude)" (`round6-adjudication-and-tally.md` line 25; source `review6-claude-opus/findings.md` lines 229–238: "the fault-free AUC is above 0.5 in every cell, never once below"). This is the arm that wins the adaptation comparison, so part of its win may be static ranking leaking through the change statistic.

Add to §7:
> The comparator's change statistic was also shown not to be blind before the event: on fault-free data it ranked the support above chance in fifteen of fifteen cells (AUC 0.55 to 0.66), so an unknown part of its margin on the adaptation task is static ranking rather than change detection.

### 24. §5: "removes confounded false support" is stronger than the measurement (should-fix)

The interventional arm scored 0.85 to 0.87 on the full-channel measure with the confounder present, against 0.96 to 0.98 for the comparator without it (`round6-adjudication-and-tally.md` line 31). It is not degraded by the confounder; it does not remove anything to zero. Replace the bolded claim with:
> **Sign-randomised probing is not degraded by a shared-cause confounder that costs a frozen passive residual monitor about 0.2 AUC of false support, online and at a 5 percent probe budget.**

### 25. §5: "On this generator that claim is false as posed" (should-fix; opinion where marked)

The archive uses this wording (`CHECKPOINT.md`), so the report is faithful to the record — but the record is loose, and this report is where it gets fixed. *Opinion:* the programme's claim contains "under confounding", and the report itself establishes two paragraphs earlier that the adaptation endpoint scored only channels the confounder provably cannot reach; round 7 accepted that the two halves were measured under different regimes and so are not a dissociation (`round7-adjudication.md` line 22). "False" claims more than an untested conjunction supports.

Replace with:
> On this generator the superiority half is refuted where it was measured — the passive arm wins the adaptation task — and the "under confounding" half was never tested on the channels that were scored. A design that tests the conjunction is Section 4.4's, and it was not built.

### 26. Summary and §5: the programme's own claim already conceded speed to the passive arm (should-fix)

The Summary says the intended contribution was probing that "would track a changing controllable boundary better than a passive residual monitor under such confounding". K4, quoted in §1 and at `roadmap-v4.7-amendments.md` line 15, says something weaker and partly opposite: "Passive residual monitors **detect body change quickly** but attribute control wrongly under a shared-cause confounder; a sign-randomised interventional estimator ranks the controllable support correctly at a 5 percent probe budget, insensitive to the confounder, **at a measurable cost in alarm speed**." Round 7 accepted the point: "roadmap v4.7 K4 does claim the attribution half; what failed is the changing-boundary superiority claim, not the attribution claim" (`round7-adjudication.md` line 26). As drafted, the Summary lets a reader think the programme predicted the opposite of what it found on speed, which inflates the fall.

Add to §5's closing paragraph:
> K4 had already conceded that the passive monitor detects change quickly and that probing costs alarm speed; what failed is the superiority claim for tracking a changing boundary, not the attribution claim, which held.

### 27. §3.2: the probed comparator is introduced and never reported (should-fix)

"A probed variant of the comparator, run on the identical probe-carrying stream, separates having interventions from using them." Arm 3 was optional in round 6 and reported separately (round-6 prompt, `readiness-protocol.md` line 101). The report never returns to it, though it is the arm that distinguishes the mechanism from the instrument. Either report it or close it: append "It was optional in the execution rounds and is not scored here; the mechanism it controls for is therefore untested."

### 28. Table 4: two scores carry conditions the table drops (should-fix)

`round7-adjudication.md` line 9 gives Codex's 4 as "4 (question only, no evidence)"; line 11 gives Claude's 2.5 as "2.5 (3 if both endpoints share one confounding regime)". Both conditions are load-bearing — the second is the repair the report recommends against itself. Add a caption sentence: "Codex's 4 was scored on the question alone, no evidence existing for it; Claude's 2.5 becomes 3 if both endpoints are measured under one confounding regime."

### 29. §8: no availability statement (should-fix)

The report offers "a certified generator and test gate that others can reuse" and an archive containing "the eight rounds in full", and never says where any of it is, under what licence, or whether it will be released. As it stands nothing here is reproducible by a reader. Add to §8:
> The archive is at ⟨URL⟩, released under ⟨licence⟩; `executable-proofs/gate/` runs with `python3 run_gate.py` under the pinned Python 3.12 and NumPy 2.4.4 (the runner refuses other versions). The confirmation-seed commitment is `89a262a92313233bcb037c1c12fd5b9703917296f36feeac3069a5ead2649d01`; the secret is unopened and is not in the archive.

### 30. §7: the readiness conditions that were never met are not stated (should-fix)

Three of the six conditions in `readiness-protocol.md` lines 11–17 were never satisfied and the report does not say so: the black-box acceptance suite written by an agent other than the builder from the interface spec alone; the hand-computed rectangular, noisy, censored case matched against the pipeline and `contract_ref.py`; and the runtime pilot with recorded per-cell durations. Add to §7:
> Three of the protocol's six readiness conditions were never met: no independent black-box acceptance suite was written from the interface specification alone, the hand-computed reference case was never carried out, and no runtime pilot was recorded. The gate's exit code was the only executable readiness signal actually used.

---

## C. Should-fix — referee and prose

### 31. References: three of six are never cited in the text (should-fix)

Basseville and Nikiforov (1993), Mann and Whitney (1947) and Page (1954) appear only in the list. Fix by citation, not deletion: §3.2 "a tie-corrected rank-sum statistic (Mann and Whitney, 1947)"; §6 "by analogy with a CUSUM on residuals (Page, 1954; Basseville and Nikiforov, 1993)"; §4.3 "(Heirung and Mesbah, 2019; Willsky, 1976; Basseville and Nikiforov, 1993)", which is also how `round7-adjudication.md` line 10 cites them.

*Reference check, for the record — all six verified, no errors found.* Liu, Cheng and Bogdan: arXiv:2603.18257, title exactly "Discovering What You Can Control: Interventional Boundary Discovery for Reinforcement Learning", Jiaxin Liu / Anzhe Cheng / Paul Bogdan, v1 18 March 2026, v2 7 May 2026 — the report's initials, year, title and v2 are all right. I verified both substantive claims §4.3 makes about it: the paper's Proposition 3.3 is "Invariance to confounders", stating that replacing the action mechanism with a confounder-independent randomised policy severs C→a and leaves the non-SoI test statistic invariant to confounders; and §3.2 states that "Uniform is maximum-entropy on A and maximally excites action-reachable dimensions, but **any confounder-independent distribution is valid**". Heirung and Mesbah (2019), *Annual Reviews in Control* 47, 35–50: verified. Willsky (1976) *Automatica* 12(6) 601–611; Mann and Whitney (1947) *Ann. Math. Statist.* 18(1) 50–60; Page (1954) *Biometrika* 41(1/2) 100–115; Basseville and Nikiforov (1993) Prentice Hall: all correct as given. Add an access date to the arXiv entry.

### 32. §4.1: "Three things followed" is followed by four things (should-fix)

The paragraph promises three, lists three (robust arm; margin cleared; inadmissible), then gives the cause, then "The third finding was worse for the design" introduces a fourth item that was not in the list of three. Replace "The third finding was worse for the design." with "A fourth finding, and the worst for the design, came from the same runs."

### 33. §4.2: "Two further defects were found three of three" (should-fix)

Archive shorthand that does not parse for an outside reader. Replace with "Two further defects were reported independently by all three reviewers."

### 34. §4.4: "body coupling" names two different objects in one paragraph (should-fix)

"the covariance discontinuity at the causal lag pins the body coupling separately from the smooth AR(1) confounder path" — here it is B, the action-to-body matrix. Four lines later, "a term proportional to the product of the body coupling and the policy's context gain" — here it is G_b, the confounder-to-body coupling (`round8-adjudication.md` line 8: "converges to B plus a confounding term proportional to G_b W_uᵀ"). A reader tracking the argument cannot tell them apart, and the second is the point of the section. Replace the second occurrence with "the product of the confounder's coupling into the body and the policy's context gain", and consider naming both couplings explicitly.

### 35. §4.4 has no algebra at all (should-fix; opinion)

The section reports an identifiability result — the report's third surviving statement — in prose only. *Opinion:* a referee will not accept "its action coefficient converges to the true coupling plus a term proportional to…" without the expression. One display line suffices: the no-latent predictor's action coefficient converging to B + κ G_b Σ_u W_uᵀ (constant defined), plus the strict inequality with non-empty interior that `round8-adjudication.md` line 8 records (Claude: κ|G_{b,j}||W_{u,k}| > ε; Codex: nonzero cross-transfer in the affected directions). Without it, §5's third bullet is an assertion.

### 36. Table 3 reports no uncertainty, and does not explain why the two distractor levels coincide (should-fix)

Round 6 produced intervals — `review6-codex/report.md` lines 156–159 give the static-loading control as 0.422 [0.249, 0.594] and 0.200 [0.077, 0.323] — and the report gives bare point estimates. It also merges "Ten or thirty distractors" into one row without saying why they coincide, which is the section's most striking fact and is explained only two paragraphs later. Add intervals to the controls at least, and add to the caption: "The two distractor levels give identical numbers because the pre-event support contains no distractor channels, so N_x cannot enter the primary."

### 37. There is no statement of what happens next (should-fix)

The report ends on §9 and references. `decisions-required.md` line 5 records D-13 as **open**, with A (this report), B (one boxed execution round at novelty 3) and C (the body-confounded plant) still on the table. A report that documents eight rounds and stops should say whether the programme stopped and what would restart it. Add three or four sentences after §5 or at the end of §7: the decision to write this rather than build a version 7; that option B remains available at novelty 3 if the event is repaired by topology and both endpoints share one confounding regime; and that the evidence that would reopen it is §4.4's E2 confuser dissociation measured on a plant where the confounder reaches the body.

---

## D. Optional

### 38. Summary: "three methodological errors that a cross-model execution round caught within a day each" (optional)
Nothing in the archive times the errors to the day. Say "each caught by the next cross-model round" and drop the clock.

### 39. §6: "became obvious within minutes of three systems running the same frozen instances" (optional)
Runtimes were 5 to 21 minutes and the diagnosis took a full round of reviewer analysis plus an adjudication. "Became visible in the first cross-model run on the same frozen instances" is what the record supports.

### 40. §6: "in one afternoon" (optional)
Unverifiable from the archive. Cut.

### 41. §3.2: "It never sees a label, a reward or the event time" (optional)
True of the raw statistic and of the primary, which is invariant to any monotone calibrator; but the arm's probability tier consumes a harness-fitted isotonic calibrator trained on oracle labels (`sequential-ibd-spec.md` line 213). Write "its raw statistic never sees…".

### 42. §3.2: "three lags of the action" (optional)
The feature block is [o_t, a_t, a_{t−1}, a_{t−2}] (`comparator-spec.md` line 315) — the current action and two lags, 3K columns. Say "the current action and two lags".

### 43. §4.3: "The one candidate scored above 3" (optional)
Gemini scored the combined paper 3.2. Say "the one candidate adjudicated above 3".

### 44. §4.4: "They agreed on the substance." (optional)
Flat, and slightly generous: `round8-adjudication.md` line 7 notes Gemini's "Theorem 1" is a statement about a no-latent estimator's apparent regression coefficient rather than about the full law, and only its remark concedes the σ_a → 0 requirement. Rewrite: "The two direct derivations agreed and the third conceded the same point in a remark: exact non-identifiability is a knife-edge."

### 45. Presentation and small things (optional)
- Front matter says "draft 1"; the byline says "Technical report, September 2026". Make them agree and put the date in the byline.
- The PDF is built with `--no-pdf-header-footer`, so it has no page numbers, and its `<title>` is "Technical report" rather than the paper's title. Both are one-line fixes in `build_report.py`, and both matter if this circulates as a PDF.
- §7 is a single eleven-line block containing eight distinct limitations. As a list it will be read; as a block it will not.
- §2's "which I state because the protocol is what caught the errors" nudges the reader; the section proves it without the nudge. Cut the clause.
- Summary's "What the numbers showed is not what the programme hoped." — mild personification plus a hedge. "The numbers did not support the claim the programme was built to test." is shorter and states the fact.
- §5's "The caveat is load-bearing" is the best sentence in the report. Keep it.

---

## E. What I would change before putting my own name on it

1. Fix the nine blocking items. Six are single-sentence repairs; two (the gate's surviving mutants, the authorship disclosure) require adding a fact the report currently omits.
2. Adopt one rule and apply it to every number: **state how many implementations produced it.** Round-5 numbers are three-model within Monte Carlo error; the round-5 constant control is single-model on a conditioned subset; the round-6 primary and its controls are three-model to three decimals; the round-6 secondary is two-model. The report currently makes all of them sound alike, and the one asset this programme has that most reports do not is the ability to say which is which.
3. Rewrite Table 1 as the report's spine. It is at present the least reliable object in the document — wrong hash, wrong round types, mixed test-count conventions, a mislabelled first row, and a caption offering a verification that fails — and it is the first thing a hostile reader will check. Everything it needs is in `readiness-protocol.md`.
4. Add the availability statement, or drop every claim about reusable artefacts. Both are respectable; the current position is not.
5. Add four to six sentences of status: what was decided after round 8, what would reopen it, and that D-13 was still open in the archive when this was written.
6. *Opinion, and the change I would most want:* give §6 room and make it the report's contribution. The three errors, and the specific structural feature that caught each — a control that never sees the change, a channel-set check before adopting a primary, a frozen generator so that three implementations are comparable — are the transferable result. The AUC tables are the evidence for them. As drafted, §6 is eleven lines and reads as an appendix to a negative result; it should read as the thing the reader takes away.

Marked as opinion where it is opinion: items 5 (git-based verification), 25, 35, and point 6 above are my judgement. Everything else numbered in sections A and B is a check against a named file and line.
