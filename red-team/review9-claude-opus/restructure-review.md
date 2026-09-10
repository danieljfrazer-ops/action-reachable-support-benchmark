# Review 9 (restructure) — draft 11 against draft 10, fact-check and referee report

Reviewer: fresh-context Claude Opus, `claude-opus`. Date: 15 September 2026.

**Targets.** New: `docs/report/technical-report.md` (draft 11, restructured). Baseline: `release/action-reachable-support-benchmark/report/technical-report.md` (draft 10, final, presumed correct after eight review passes). Source of truth for anything draft 11 adds: `docs/archive/red-team/`.

**What I did.** Read both drafts end to end. Diffed them claim by claim and mechanically diffed every numeric token in the two files. Audited draft 11's internal cross-references (sections, tables 1/1b/2/3/A1/B1, Figure 1's caption, Appendix A/B pointers, Experiment 1/2 ↔ rounds 5/6). Checked every statement draft 11 makes that draft 10 did not against the archive, in particular `round7-adjudication.md`, `round8-adjudication.md`, and the contents and reviewer tables of `review9-tool/`.

**Counts.** 3 blocking, 14 should-fix, 8 optional (25 items).

**Verdict in one line.** The restructuring moved material faithfully: every load-bearing qualifier the task named — *single-model*, *two of the three implementations*, *inadmissible*, *never run*, *not scored*, *undetermined*, *not settled*, *five seeds cannot settle the sign* — survives somewhere in draft 11, and no number changed. The three blocking items are all in the new or rewritten framing text: the abstract drops the family-N reversal that draft 10's summary carried, the introduction claims a verification coverage the report does not have, and Appendix A's new account of the report's own review describes a tool run that does not exist in the archive.

**Mechanical check, for the record.** Diffing every number in the two files returns only section numbers, the round-7 novelty scores (1.5, 3.5, 3.8), the roadmap pointer 4.7, "D-13", the date "10 September", and the erratum parenthetical's second copies of 0.85/0.87. No result, AUC, bound, count, hash or date changed. Every occurrence of 0.85 and 0.87 remaining in draft 11 is in its correct context.

---

## A. Blocking

### 1. The abstract drops the family-N reversal that draft 10's summary carried (blocking)

Draft 10, Summary:

> On a different endpoint, ranking which controlled sensor an actuator loss removed, a passive delay-aware covariance monitor equalled or beat the probed estimator in every linear-family cell, **and the ordering reversed on the one nonlinear family, on five seeds.**

Draft 11, Abstract:

> On the separate task of ranking which controlled channel an actuator loss removed, a passive delay-aware covariance monitor equalled or beat the probed estimator in every linear-family cell.

The reversal is gone. This is the qualifier that stops the sentence from reading as a general result about probing, and it is one the report's own §4 calls load-bearing ("the ordering reversed on the nonlinear family on five seeds"). The abstract is the only part of a technical report most readers read in full; carrying "in every linear-family cell" without "and reversed on the nonlinear one" is exactly the over-generalisation round 7 made the author withdraw: `round7-adjudication.md` §2 records three of three agreeing that "'interventions do not buy adaptation' is over-generalised and must read 'when the controllable channels are unconfounded and natural excitation is abundant'". The archive does not support the unqualified version; §3.2 and §4 of draft 11 itself do not support it.

**Fix**, Abstract, replace:

> On the separate task of ranking which controlled channel an actuator loss removed, a passive delay-aware covariance monitor equalled or beat the probed estimator in every linear-family cell.

with:

> On the separate task of ranking which controlled channel an actuator loss removed, a passive delay-aware covariance monitor equalled or beat the probed estimator in every linear-family cell, and the ordering reversed on the one nonlinear family, on five seeds.

### 2. Appendix A asserts a tool run on the restructured draft that the archive does not contain, miscounts the archived runs, and leaves two dependent sentences false (blocking)

Draft 11, Appendix A, "Review of this report":

> The tool ran **seven times on the earlier drafts, once on each of drafts 1 to 6** and once more on draft 1 with the archive out of scope, **and once more on the restructured draft**; every run's report is archived, and one run number is unused because I aborted that run before any reviewer reported. … The Google reviewer reported from draft 4 onward …

Draft 10 said only: "The tool ran seven times, once on each of drafts 1 to 6 and once more on draft 1 with the archive out of scope."

What `docs/archive/red-team/review9-tool/` actually holds (nine files, newest mtime 10 Sep 15:42):

| File | What it reviewed |
|---|---|
| `RT-001-report-panel-incomplete.md` | draft 1, archive out of scope (1 file reviewed; Codex declined for lack of the archive) |
| `RT-002-report-draft1.md` … `RT-008-report-draft6.md` | drafts 1 to 6 |
| `RT-009-report-draft7.md` | **report draft 7** — dated `RT-20260910-009`, and its findings are indexed to draft-10-era section numbers (§4.1, §4.4, §5, §7, §9), so it is pre-restructure |
| `RT-010-figures-proposal.md` | `docs/report/figures-proposal.md`, 2 files — not a report draft |
| `RT-004` | absent (the aborted run) |

Three separate errors follow.

(a) **There is no tool run on the restructured draft.** The restructure is dated 15 September; the newest file in `review9-tool/` is 10 September 15:42, and it is the figures-proposal run. The claim "and once more on the restructured draft" is unsupported.

(b) **"once on each of drafts 1 to 6" is now an undercount.** With RT-009 the archive holds runs on drafts 1 to 7, i.e. eight runs on the report (seven numbered drafts plus the out-of-scope draft-1 pass), not seven. Draft 10's count was correct as of draft 10; draft 11 keeps the stale enumeration while adding an eighth run that does not exist.

(c) **Two dependent sentences become false once RT-009 is in scope.** "The Google reviewer reported from draft 4 onward" — RT-009's reviewer table gives `antigravity | google | **no** | ok | 218s | 0`, and its "Worth knowing" list says "antigravity did not count towards diversity — nothing readable came back". Google reported on drafts 4, 5 and 6 only. And the §5 limitation "this report's own review had two model families, not three (Appendix A)" is wrong for the restructured draft specifically: the restructured draft has been reviewed by one model family — this review — with no tool run at all.

**Fix**, Appendix A, replace the first two sentences of "Review of this report":

> Two things reviewed it against the archive: a fresh-context Claude Opus agent, and a cross-model review tool. The tool ran seven times on the earlier drafts, once on each of drafts 1 to 6 and once more on draft 1 with the archive out of scope, and once more on the restructured draft; every run's report is archived, and one run number is unused because I aborted that run before any reviewer reported.

with:

> Two things reviewed it against the archive: fresh-context Claude Opus agents, and a cross-model review tool. The tool ran eight times on the report, once on each of drafts 1 to 7 and once more on draft 1 with the archive out of scope; a ninth run reviewed the figures proposal rather than the report. Every run's report is archived, and one run number is unused because I aborted that run before any reviewer reported. The restructured draft was reviewed by a fresh-context Claude Opus agent only; no tool run covers it.

and in the same paragraph replace "The Google reviewer reported from draft 4 onward, having been out of scope on the first run and quota-exhausted on drafts 1 to 3." with "The Google reviewer reported on drafts 4 to 6, having been out of scope on the first run, quota-exhausted on drafts 1 to 3, and unreadable on draft 7."

and in §5 replace the last clause of the final bullet, "and this report's own review had two model families, not three (Appendix A)", with "and this report's own review had at most two model families and, on the restructured draft, one (Appendix A)".

*If a tool run on the restructured draft is in fact underway, the sentence still cannot stand as written until its report is archived; the number of runs and the per-family outcome are not predictable in advance.*

### 3. The introduction claims a verification coverage the report does not have (blocking)

Draft 11, §1, final sentence:

> The verification protocol and the errors it caught are in the appendices; **every number in the report traces to an archived file.**

Draft 10 made no such claim. What §6 of draft 11 actually says is narrower:

> A file map traces **each table and figure** in this report to the archived input, implementation, captured output and adjudication.

And the report itself documents numbers that do *not* trace cleanly: Table A1's historical freeze hashes are "assertions from the round log and are not recomputable from the archive as it stands"; the gate counts are "from the author's machine" on an archive that "has not been run from a clean checkout"; §3.1's 0.975 / 0.774 / 0.845 / 0.969 / 0.882 / 0.831 figures are single-model and unreproduced. "Every number traces to an archived file" is a stronger and different claim from "each table and figure has a file-map entry", and it is the precise class of over-statement of the record that earlier passes were convened to remove.

**Fix**, §1, replace:

> The verification protocol and the errors it caught are in the appendices; every number in the report traces to an archived file.

with:

> The verification protocol and the errors it caught are in the appendices; a file map in the archive ties each table and figure to the inputs, implementations and adjudications it came from, and Section 6 states where that trail is incomplete.

---

## B. Should-fix

### 4. §3.4 drops "two of the three" from the body-confounded plant's rescore

Draft 10, Table 5 caption: "**Two of the three** rescored the body-confounded plant at 3, the same as the repaired benchmark paper, and the third reframed what is unoccupied about it as body confounding plus a restricted estimator".

Draft 11, §3.4: "and the body-confounded plant of Section 3.3 **was scored at the same level** once its identifiability premise fell."

The archive supports both readings and they are in tension inside it. `round8-adjudication.md:20` is the precise one: "option C's novelty is **3, not 3.5 to 4** (Claude, Gemini; Codex reframes the unoccupied condition as body confounding plus a restricted estimator or insufficient excitation)" — two rescored, one reframed. `round8-adjudication.md:24` is the loose one draft 11 followed: "Three models put that at the same novelty (3) as the repaired benchmark-and-findings paper of option B." Draft 10 chose the precise version and eight passes let it stand; the restructure should not quietly adopt the looser one.

**Fix**, §3.4, replace "and the body-confounded plant of Section 3.3 was scored at the same level once its identifiability premise fell" with "and two of the three rescored the body-confounded plant of Section 3.3 at the same level once its identifiability premise fell, the third reframing what is unoccupied about it as body confounding plus a restricted estimator".

### 5. §3.4 replaces the round-7 scores with an unsourced gloss, and Table 4 is gone with nothing standing in for it

Draft 10 carried Table 4 (four candidate claims × three reviewers, on the roadmap's one-to-five scale) and the sentence "The combined paper reaches a 3 only after the event is repaired…". Draft 11 has no table and says "A combined benchmark-and-findings paper was **scored as an incremental contribution** only after the event is repaired…".

Two problems. "Incremental contribution" is an interpretation of the number 3 that I cannot locate anywhere in the archive; `round7-adjudication.md`'s adjudicated wording for candidate (c) is "**3, conditional**: publishable as a benchmark-and-findings contribution (TMLR, CoLLAs, a NeurIPS evaluations track) only after the event is repaired by topology, both endpoints are measured under a common regime, and the conclusion is stated conditionally." And with the table gone, "the same level" in the next clause (item 4) has no referent a reader can check — the reader is never told what scale, what range, or what number.

**Fix**, §3.4, replace "A combined benchmark-and-findings paper was scored as an incremental contribution only after…" with "A combined benchmark-and-findings paper scored 3 on the roadmap's one-to-five scale, and conditionally: publishable as a benchmark-and-findings contribution only after the event is repaired, both endpoints are measured under one confounding regime, and the conclusion is stated conditionally." Either restore draft 10's Table 4 as a new Table 4 in §3.4, or add its four adjudicated rows to Appendix A.

### 6. §3.4 drops the round-8 conclusion that no path above a 3 survived

Draft 10's Summary stated it ("No path to a claim above 'benchmark plus findings' survived") and `round8-adjudication.md:24` states it in terms: "After eight rounds, no path above a 3 has survived cross-model review." Draft 11 states it nowhere. It is the sentence that explains why the programme stopped, and §4's "What would reopen the question…" paragraph presumes it.

**Fix**, §3.4, append after the sentence fixed in item 5: "After eight rounds no candidate above that level survived cross-model review."

### 7. §3.4 calls the round-7 candidates "the surviving claims"

Draft 10: "Three reviewers scored **four candidate claims** on the roadmap's one-to-five scale…". Draft 11: "Three reviewers scored **the surviving claims** against the literature…". One of the four candidates was a plant that was never built and had no evidence behind it (`round7-adjudication.md`, row d: "No evidence exists for it yet"), so it was not a surviving claim; and the number four is what makes item 6's "no path above a 3" meaningful.

**Fix**, §3.4, replace "Three reviewers scored the surviving claims against the literature" with "Three reviewers scored four candidate claims against the literature".

### 8. §1 states "each verified by three independent implementations or derivations" without the caveat §2.3 adds

> Two experiments and one analysis, **each verified by three independent implementations or derivations**, show that the claim is unsupported…

True at the granularity of experiments and rounds, but the report's own results rest in places on fewer: the §4 attribution statement's load-bearing measurement is "from two of the three implementations", the 0.975 fit-time-vector figure is "single-model and was not reproduced", and family N is five seeds. §2.3 carries the correct hedge ("Where a number below comes from fewer than three implementations, it says so") but the introduction does not, and a referee reads the introduction first.

**Fix**, §1, replace "each verified by three independent implementations or derivations" with "each run by three independent implementations or derivations, though several individual numbers rest on fewer, as the text says in each case".

### 9. §1 says the testbed was "built to confirm" the claim; §4 says "built to test" it

Draft 11 §1: "show that the claim is unsupported on the testbed **built to confirm it**". Draft 11 §4: "the claim **the programme was built to test**". Draft 10 used "test" throughout. "Built to confirm" concedes a confirmation-seeking design the archive does not describe — the contract pre-declared a margin, a competence floor and a sealed confirmation set, which is the opposite posture.

**Fix**, §1, replace "on the testbed built to confirm it" with "on the testbed built to test it".

### 10. §1 calls the testbed "reusable" without support

> The contribution is a negative result with a **reusable** testbed.

Nothing in the report supports reusability and §6 and §5 argue against it: no version was readiness-certified, the coverage matrix still lists four uncovered normative groups, three reviewer mutants survive the gate, the mutation runner cannot register a generator mutant, "the archive as published has not been run from a clean checkout", and known specification defects "were recorded but not repaired". Draft 10 made no such claim.

**Fix**, §1, replace "The contribution is a negative result with a reusable testbed." with "The contribution is a negative result, with the generator, gate and full review record released so the result can be checked; Section 6 states what is and is not reproducible from them."

### 11. §5's limitation bullet contradicts Appendix A and §7 on who drafted the specifications

Draft 10: "The adjudicating session shares a model family with one of the three reviewers…". Draft 11: "The adjudicating session **that drafted the specifications and adjudications** shares a model family…".

Appendix A and §7 both say the opposite of the natural reading: "Separate fresh-context Claude agents drafted the two estimator specifications and redrafted them after round 5 … they neither reviewed nor adjudicated". The added clause reads as crediting the adjudicating session with the estimator specifications, and it is precisely the independence question the bullet is about, so the ambiguity is not harmless.

**Fix**, §5, replace "The adjudicating session that drafted the specifications and adjudications shares a model family with one of the three reviewers" with "The adjudicating session that drafted the contract, the interface specification, the prompts and the adjudications shares a model family with one of the three reviewers, and with the agents that drafted the two estimator specifications".

### 12. §6 and the abstract state the release as accomplished when §6's own next sentence says it is not

Draft 10: "A public release should be accompanied by a repository whose commits fix this from that point on." Draft 11: "**the public repository's first commit is the first reproducible snapshot.**" And the abstract: "The testbed, gate and review record **are released**." Both are present-tense assertions about a repository whose "archival DOI via Zenodo [is] to be minted on release", in a report whose own reproducibility section says the published archive has never been run from a clean checkout. Draft 10 stated it as a recommendation, which is what the record supports.

**Fix**, §6, replace "the public repository's first commit is the first reproducible snapshot" with "the public repository's first commit will be the first reproducible snapshot". **Fix**, Abstract, replace "The testbed, gate and review record are released." with "The testbed, gate and full review record are released with this report."

### 13. §3.3 loses the fact that the analysis refuted the author's own premise, and gains an editorial framing in its place

Draft 10, §4.4: "I had routed the programme toward it on the premise that passive support tracking would then be non-identifiable in principle, and asked the three systems to derive…", and, inside the first conclusion, "**The premise I had adopted was false.**"

Draft 11, §3.3: "**The natural repair** is a plant in which the context also drives the body. Before building it, three systems were asked to derive…" — and the sentence "The premise I had adopted was false" is gone from the main text entirely.

It survives in Appendix B error 4, so this is not a lost fact. But §3.3 now reads as neutral due diligence before a build, and "the natural repair" asserts as obvious the very design choice the section goes on to undercut. A referee reading §3 and §4 without the appendix gets a population-limit result with no sign that it overturned the premise that routed the programme — and the programme's stopping decision turns on that.

**Fix**, §3.3, replace the opening two sentences:

> The natural repair is a plant in which the context also drives the body, so that confounding and change act on the same channels. Before building it, three systems were asked to derive, in the population limit, whether passive support tracking is then non-identifiable in principle, …

with:

> I had routed the programme toward a plant in which the context also drives the body, so that confounding and change act on the same channels, on the premise that passive support tracking would then be non-identifiable in principle. Before building it, three systems were asked to derive, in the population limit, whether that premise holds, …

and restore, after "requires the action noise to vanish in the affected direction.": "The premise I had adopted was false."

### 14. The restructure converts the author's own decisions into agentless passives in three places

| Draft 10 | Draft 11 |
|---|---|
| §3.3 "After round 5 **I changed the primary** to score only the pre-event support" | §2.3 "Experiment 2 scored it over the pre-event support only" |
| §4.2 "**I adopted six decisions** in response, recorded as D-11" | §3.2 "Six changes **were made** in response (decision D-11 in the archive)" |
| §4.2 "**I had recommended that primary** without checking the channel sets against each other; a one-line check would have caught it" | §3.2 "a one-line check of the channel sets before adoption would have caught it (Appendix B)" |
| §4.2 "**Fresh-context Claude agents** redrafted both specifications" | §3.2 "Both estimator specifications **were redrafted**" |

Ownership survives in Appendix B ("My repair restricted scoring to the pre-event support") and Appendix A, so no fact is lost. But a report whose distinguishing feature is that the author names his own errors in the main text should not push all four instances into an appendix in the same pass. This is opinion, held firmly: the passive voice here costs the report the credibility it spent nine rounds earning.

**Fix**, §3.2, replace "Six changes were made in response (decision D-11 in the archive)." with "I adopted six changes in response, recorded as decision D-11 in the archive." Replace "Both estimator specifications were redrafted against the new contract, and a new version was frozen." with "Fresh-context Claude agents redrafted both estimator specifications against the new contract, and a new version was frozen." Replace "a one-line check of the channel sets before adoption would have caught it (Appendix B)" with "I had recommended that primary without checking the channel sets against each other; a one-line check would have caught it (Appendix B)."

### 15. Appendix A says "nine review rounds" but its rules still describe eight

The opening line is "One protocol governed the **nine** review rounds", and Table A1 now has a row 9. But the Freeze bullet still reads "Rounds 1 to 6 reviewed frozen versions; **rounds 7 and 8** reviewed the archived record without a new freeze", and the "Three model families, one prompt" bullet asserts a three-family rule that round 9 did not meet (the "Review of this report" paragraph says so four paragraphs later, which is where a referee will notice the contradiction).

**Fix**, Appendix A, Freeze bullet: replace "rounds 7 and 8 reviewed the archived record without a new freeze" with "rounds 7 to 9 reviewed the archived record without a new freeze". "Three model families" bullet: append "Round 9, the review of this report, did not meet this rule; see 'Review of this report' below."

### 16. Appendix B cites version numbers 4, 5 and 6 that draft 11 no longer defines anywhere

Table B1's "Entered" column reads "version 4", "the first generator, frozen at version 5", "version 6 (D-11.1a)", and §2.2 and §3.1 of draft 10 anchored those numbers ("In version 5 its change statistic was…", "version 6 was frozen"). Draft 11 systematically replaced those anchors with "Experiment 1" / "Experiment 2" / "the final frozen version", but Appendix B still uses the version numbers, and Table A1's "Frozen version reviewed" column carries hashes only. A reader of draft 11 cannot resolve "version 4".

**Fix**, Table A1, change the column header to "Frozen version reviewed" → keep, and prefix each hash with its version number: row 1 "v1 `c197652c0d8e846b`", row 2 "v2 `d23960e6da441de7`", row 3 "v3 `e662b7429b6b347d`", row 4 "v4 `442cc4b7da691ca0`", row 5 "v5 `0468104f6431b050`", row 6 "v6 `38d161e762a3de76`".

### 17. §7 drops the disclosure that the last tool run had one usable family and the final draft was not re-run

Draft 10, §9, final sentences: "The run on draft 6 had one usable family; its findings with checked evidence went into this final draft, which was not re-run." Draft 11 drops this. Combined with blocking item 2, draft 11 now asserts a run on the restructured draft and omits the admission that the previous final draft went out un-re-reviewed — the disclosure moves in exactly the flattering direction.

**Fix**, Appendix A, "Review of this report", append: "The last run on a report draft had one usable family; its findings with checked evidence went into the draft that followed, which was not re-run."

---

## C. Optional

### 18. The restructure anonymises implementations in the main text but names them in Appendix B

§3.1 "identified analytically by **one implementation**" (draft 10: "by Codex"); §3.3 "**two** derived them directly; **the third's** stated theorem…" (draft 10: "Codex and Claude derived them directly; Gemini's stated theorem…"). Meanwhile Table B1 still names "round 4 (Gemini, R4-GM-02)" and "round 8 (Codex and Claude)", and Appendix B's error-1 narrative names Gemini twice. Pick one convention. Anonymising the main text is defensible for a report whose point is cross-model agreement rather than model comparison; if you keep it, make Table B1 read "round 4 (one reviewer, finding R4-GM-02)".

### 19. §1's section roadmap stops at Section 5

"Section 2 describes the testbed and the two estimators, Section 3 the experiments and the analysis, Section 4 what the results support, Section 5 the limitations." Sections 6 and 7 exist and are not mentioned; the next clause mentions the appendices. Append ", Section 6 reproducibility and Section 7 disclosure".

### 20. §3.1's heading loses the section's verdict

Draft 10: "Round 5: the method works, the baseline was defective, and the task was posed wrongly". Draft 11: "Experiment 1: full-channel ranking". Conventional shape argues for the neutral heading; but the report is a negative result, and a heading that says what the experiment found is not unconventional in a results section. Taste. If you want it back: "Experiment 1: full-channel ranking, on a defective baseline".

### 21. §4 drops the open decision D-13

Draft 10 §8 opened with the programme's live decision — stop here, run one boxed round, or build the body-confounded plant. Draft 11 keeps only the "what would reopen the question" paragraph. Losing the decision is defensible in a report (a report is the answer to it), but a reader who reaches "What would reopen the question" is not told whether the author has chosen. One sentence at the end of §4 would settle it.

### 22. Figure 1's caption loses the pointer to the error it illustrates

Draft 10: "…which is the mechanism of the third error in Section 6." Draft 11: "…which is why Experiment 2's confounding benefit was zero by construction." The new version is clearer standing alone, but the figure is the best single illustration of error 3 and no longer points at it. Append "(error 3, Appendix B)".

### 23. The abstract drops two hedges from the identifiability sentence

Draft 10: "A derivation in round 8, **agreed by all three systems**, showed … so only a restricted class of passive models fails, **and only on an open set of parameters**." Draft 11: "a population-limit analysis showed…". Neither omission is an overclaim — if anything the open-set clause was the stronger half — but "agreed by all three systems" is the abstract's only chance to say the analysis was cross-model, and the abstract makes that point for the two experiments.

### 24. Table A1's "Gate as frozen" cells are empty for rounds 7 to 9

Empty cells in a published table read as an omission rather than a non-applicable. Put "n/a (no freeze)" in rows 7, 8 and 9.

### 25. Table A1 row 9's date range "9 to 15 Sep" is only half evidenced

`review9-claude-opus/report-review.md` is 9 September and the `review9-tool/` files run to 10 September 15:42. Nothing dated between 10 and 15 September exists in the round-9 folders. The range is defensible if this review is what closes it, but it will be defensible only once this review is archived. Not a problem today; a problem if the 15th end of the range is meant to cite a tool run (see blocking item 2).

---

## D. Referee's read of the new abstract and introduction (task item 3)

**Is the thesis clear in the first paragraph?** Yes. The abstract's second and third sentences state the question and the test cleanly, and "This report tests the sequential version: whether an in-task, sign-randomised probing estimator at a 5 percent probe budget tracks a changing controllable boundary better than a passive residual monitor under a shared-cause confounder" is a better one-sentence statement of the object than draft 10 had. The title already carries "negative result", so a referee knows the direction before the first sentence.

**Is the contribution stated?** Yes, in §1 paragraph 3, and it is the right contribution (a negative result plus the testbed and record). Item 10 is the only defect: "reusable" is the one word in it the report does not earn.

**Is anything in them unsupported by the results section?** Three things, all listed above: "every number in the report traces to an archived file" (blocking 3), "reusable testbed" (10), and "The testbed, gate and review record are released" (12). One thing is *under*-supported in the other direction: the abstract drops the family-N reversal (blocking 1).

**One structural observation, opinion.** The abstract carries the attribution result ("was not degraded by the confounder that cost a frozen passive monitor about 0.2 AUC") without the word *inadmissible*, and so did draft 10's summary, so this is not a regression. But §4 makes clear that half of that measurement failed the contract's own competence floor and the surviving half is two implementations on a secondary. In a report whose whole method is refusing to overstate, an abstract that gives the 0.2 without a clause is the one place a hostile referee will land. I would add six words: "…that cost a frozen passive monitor about 0.2 AUC on the full channel set — half of that measurement inadmissible under the contract's own competence floor — which reproduces IBD's principle online." Offered as a suggestion, not a finding.

---

## E. Appendix material a referee would want in the main text (task item 4)

Checked every fact the main text now depends on against where draft 11 states it.

- **Error 3's ownership and mechanism.** §3.2's argument stands on its own; ownership is appendix-only. Covered by item 14.
- **The refuted premise behind §3.3.** The main text no longer says the analysis overturned the premise that routed the programme. Covered by item 13. This is the strongest of the four.
- **The round-7 novelty scores.** Not in the main text, not in an appendix, not anywhere. §3.4's "scored at the same level" has no referent. Covered by items 4 and 5. This is the only fact the restructure deleted outright rather than moved.
- **The version numbering.** Appendix B uses it; the main text no longer defines it. Covered by item 16.
- **The readiness protocol's six conditions.** §5 says "Five of the readiness protocol's six conditions were never satisfied (Appendix A)" and Appendix A enumerates them. This is correct appendix placement; no change needed.
- **The three-model protocol itself.** §2.3 says "the protocol is in Appendix A". Correct placement; the main text states the one thing it depends on (three independent implementations per experiment).

---

## F. Cross-reference audit (task item 2)

All clean except where noted.

- **Sections.** §2.2 → "Section 3.1" for the reason the change statistic was replaced: correct, §3.1 gives the mean-shift argument. §2.2 → "the second statement of Section 4": correct, that is the passive-beats-probing statement. §5 → "the third arm proposed in Section 4": correct. §5 → "the identifiability result of Section 3.3": correct. §3.2 → "(Appendix B)": correct, error 3. §5 → "(Appendix A)" twice: correct. §1's roadmap: incomplete, item 19.
- **Tables.** 1, 1b, 2, 3, A1, B1 all exist, all are introduced by an in-text reference before they appear, all captions match their contents. No orphan and no dangling reference. Table 1b's label survives the renumbering from draft 10's 2b consistently.
- **Figure 1.** Caption's three cross-references — "Section 3.3" for the instrument, "Experiment 2's confounding benefit was zero by construction", "Section 3.3" for G_b — are all correct under the new numbering. Item 22 is a suggestion, not an error.
- **Appendix A / B pointers.** All four resolve. Appendix A's own internal consistency: item 15.
- **Experiment ↔ round mapping.** Experiment 1 = round 5 = `0468104f6431b050` and Experiment 2 = round 6 = `38d161e762a3de76` are consistent across §3.1's and §3.2's table captions, Table A1 rows 5 and 6, and every "Experiment 1"/"Experiment 2" substitution in §2.2, §2.3, §4, §5 and §6. I checked each of the fourteen substitutions against draft 10's "round 5"/"round 6"/"version 5"/"version 6" and found no mis-mapping. §2.1's "from the second experiment onward" correctly renders draft 10's "from version 6".

---

## G. Sentences that read as generic or machine-written (task item 5)

Rewrites for items already raised above are given with those items (9, 10, 12, 13, 14). Two more, both optional.

**G1. §3.4, opening.** "Three reviewers scored the surviving claims against the literature after reading the IBD paper in full and, in two cases, the active fault-diagnosis literature." — "the surviving claims" is vague and, per item 7, wrong. The fix in item 7 also fixes the prose.

**G2. §4, closing of the second paragraph.** "The result is best read as a diagnosis of the event, and of the value of probes when ordinary closed-loop data are already diagnostic, rather than as a general fact about interventions." — this is carried verbatim from draft 10 and survived eight passes, so it is not a restructure defect; but "is best read as" is the one hedge-construction in §4 that does not name who is doing the reading. Optional rewrite: "This diagnoses the event, and the value of probes when ordinary closed-loop data are already diagnostic. It is not a general fact about interventions."

**G3. Abstract, closing.** "The programme's claim is unsupported. The testbed, gate and review record are released." — two flat declaratives after a long, dense paragraph. The first is right and should stay flat. The second is the one fixed in item 12; the replacement there also fixes the rhythm.

---

## H. Qualifiers checked and found intact

Recorded so the next pass does not re-check them. Every one of these survives the restructure in the main text, not only in an appendix:

*inadmissible* (§3.1, §4) · *the competence floor failed* (§3.1, §3.2 for family N) · *undetermined rather than failed* (§5) · *single-model and was not reproduced* (§3.1) · *two of the three implementations* (§3.2, §4) · *the third's secondary read was excluded* (§3.2) · *never run* for the alarm channel, the false-alarm calibration and the calibrated-probability tier (§2.2, §5) · *was not scored* for the probed comparator (§2.2, §5) · *five seeds cannot settle the sign* and the family-N reversal (§3.2, §4, §5 — but not the abstract, blocking item 1) · *the delay-2 cells score a different estimand* (§3.2, §4) · *did not clear its margin on the perturbation set* (§3.1, §4, §5) · *did not run the same trajectories* (§3.1, §5) · *not settled* for the actuator-loss sign under body confounding (Table 3 caption) · *the sealed confirmation set was never opened* (§5) · *no version was readiness-certified* (§5, Appendix A) · *three reviewer-written mutants survive* (§5) · *none of IBD's guarantees are inherited* (§2.2) · *not a dissociation* (Abstract, §3.4, §4) · *this is a replication of IBD's principle, not a new result* (§4) · *Nothing in this report is evidence for how that round would come out* (§4) · *without an independent execution* for the author's own check of the generator source (§3.2).
