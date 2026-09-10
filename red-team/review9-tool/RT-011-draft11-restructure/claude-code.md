# Red-team review — draft 11 of `docs/report/technical-report.md` against draft 10 and the archive

I read draft 11 in full, diffed it line by line against `release/action-reachable-support-benchmark/report/technical-report.md` (draft 10), and checked the contested attributions against `docs/archive/red-team/round7-adjudication.md`, `round8-adjudication.md` and `review9-tool/`. Every table number in draft 11 (Tables 1, 1b, 2, 3) matches draft 10 exactly, and the internal cross-references (Section 3.3 for the analysis, Section 3.1 for the change-statistic reason, "the second statement of Section 4", "error 3 in Appendix B", "the third arm proposed in Section 4") all resolve correctly. The problems are in the new front matter and in the two places where the restructure anonymised or compressed a provenance claim.

### P1 — the new abstract drops three qualifiers draft 10's Summary carried, including the family-N reversal that reverses the sign of the report's second headline result

`docs/report/technical-report.md:14`

```
An embodied agent needs to know which of its sensors its actions actually reach, when a hidden cause makes some sensors move in step with its actions and when its actuators fail without warning. Interventional Boundary Discovery (IBD) answers the static version of this question by randomising actions. This report tests the sequential version: whether an in-task, sign-randomised probing estimator at a 5 percent probe budget tracks a changing controllable boundary better than a passive residual monitor under a shared-cause confounder. On a certified linear-Gaussian testbed, three independent implementations of both estimators agreed to within Monte Carlo error in one experiment and to three decimal places in a second. The interventional estimator was not degraded by the confounder that cost a frozen passive monitor about 0.2 AUC on the full channel set, which reproduces IBD's principle online. On the separate task of ranking which controlled channel an actuator loss removed, a passive delay-aware covariance monitor equalled or beat the probed estimator in every linear-family cell. The two endpoints were measured on different channel sets under different effective confounding regimes and do not establish a dissociation. A re-posed primary measure scored only channels the confounder never reaches, so the benefit it was meant to measure was zero by construction, and a population-limit analysis showed that moving the confounder onto the controlled channels would not yield an identifiability claim: the policy's own action noise is an instrument, and only a restricted class of passive models fails. The programme's claim is unsupported. The testbed, gate and review record are released.
```

Three qualifiers present in draft 10's Summary (lines 16–18 of the draft-10 file) are gone:

1. **The family-N reversal.** Draft 10: "a passive delay-aware covariance monitor equalled or beat the probed estimator in every linear-family cell, **and the ordering reversed on the one nonlinear family, on five seeds**." Draft 11 stops at "in every linear-family cell". A reader of the abstract alone now gets an unqualified "passive beats probed", while §3.2 (line 103) and §4 (line 146) both say the ordering reversed on family N. This is the one qualifier that changes the direction of the result.
2. **"in the base cells".** Draft 10: "a margin of about 0.2 AUC **in the base cells**." Draft 11 states "about 0.2 AUC on the full channel set" with no cell restriction, while Table 1b (line 80) shows the same benefit running from −0.015 to +0.25 across the perturbation grid and the aggregate lower bound failing the 0.10 margin.
3. **The seeding defect behind the Monte Carlo agreement.** Draft 10: "Round 5 agreed to within Monte Carlo error, **and part of that spread was a seeding defect in the generator that gave each process different trajectories**." Draft 11 presents "agreed to within Monte Carlo error" as a clean reproducibility claim; Table 1's own caption (line 64) says the three implementations "ran the same specification and configuration seeds but not the same trajectories".

Compounding (2) and (3): the sentence "three independent implementations ... agreed" now sits immediately before the 0.2 claim, so the abstract reads as if the 0.2 is a three-implementation result. Per §4 (line 144) the measurement that statement actually rests on is the Experiment-2 loading-only secondary, "from two implementations", and the Experiment-1 half is "inadmissible under the contract's own rule".

Fix: restore the three clauses verbatim from draft 10's Summary, and say in the abstract that the full-channel gap rests on a two-implementation secondary and an inadmissible Experiment-1 measurement — exactly as §4 does.

### P1 — Appendix A's account of the tool runs contradicts the archived run list, and deletes draft 10's disclosure that the last run had only one usable family

`docs/report/technical-report.md:205`

```
**Review of this report.** Two things reviewed it against the archive: a fresh-context Claude Opus agent, and a cross-model review tool. The tool ran seven times on the earlier drafts, once on each of drafts 1 to 6 and once more on draft 1 with the archive out of scope, and once more on the restructured draft; every run's report is archived, and one run number is unused because I aborted that run before any reviewer reported. The Anthropic reviewer reported on every run. The OpenAI reviewer reported on drafts 1 to 3; it declined the first run for lack of the archive and errored from draft 4 onward. The Google reviewer reported from draft 4 onward, having been out of scope on the first run and quota-exhausted on drafts 1 to 3. No single run had all three families. On every draft, one of the two families that reviewed it is the family that drafted it.
```

The sentence accounts for eight runs (seven on drafts 1–6 plus out-of-scope draft 1, then one on the restructured draft) and asserts "every run's report is archived". `docs/archive/red-team/review9-tool/` contains **nine** reports: `RT-001-report-panel-incomplete.md`, `RT-002-report-draft1.md`, `RT-003-report-draft2.md`, `RT-005-report-draft3.md`, `RT-006-report-draft4.md`, `RT-007-report-draft5.md`, `RT-008-report-draft6.md`, **`RT-009-report-draft7.md`** and **`RT-010-figures-proposal.md`**. Two runs are unaccounted for — a run on a draft 7, which the sentence's "drafts 1 to 6 ... and once more on the restructured draft" denies exists, and a figures-proposal run — and there is no archived report on the restructured draft at all, so "every run's report is archived" cannot be true as written.

Two further specifics the archive contradicts:

- Draft 10 disclosed "The run on draft 6 had one usable family; its findings with checked evidence went into this final draft, which was not re-run." Draft 11 deletes this sentence. It is true and material: `review9-tool/RT-009-report-draft7.md:3` reads `**PANEL_INCOMPLETE** — only 1 model family produced a usable review; 2 required.` and `RT-010-figures-proposal.md:3` says the same. Deleting the caveat while adding an unevidenced run on the restructured draft moves the disclosure in exactly the wrong direction.
- "The Google reviewer reported from draft 4 onward" is false for the draft-7 run: `RT-009-report-draft7.md:23` records `antigravity | gemini-3.1-pro-high ... | google | **no** | ok | 218s | 0`, and line 14 says `antigravity did not count towards diversity — nothing readable came back`.

Fix: enumerate the runs against the `review9-tool/` file list (RT-001 to RT-010, RT-004 unused), state that the draft-7 and figures-proposal runs each had one usable family, and either drop the claim of a run on the restructured draft or cite its archived report.

### P2 — §3.4 asserts the body-confounded plant "was scored at the same level" when only two of three reviewers rescored it, and the table that carried the scores has been deleted

`docs/report/technical-report.md:140`

```
Three reviewers scored the surviving claims against the literature after reading the IBD paper in full and, in two cases, the active fault-diagnosis literature. The attribution result is IBD's Proposition 3.3 (invariance to confounders) in an online form; the IBD paper's Section 3.2 states that any confounder-independent probe distribution is valid, which covers the sign-randomised variant. The negative adaptation result is the textbook condition of passive fault detection: active input design earns its cost only when normal closed-loop data are not diagnostic (Willsky, 1976; Heirung and Mesbah, 2019). A combined benchmark-and-findings paper was scored as an incremental contribution only after the event is repaired and both endpoints are measured under one confounding regime, and the body-confounded plant of Section 3.3 was scored at the same level once its identifiability premise fell. All three rejected the sentence "interventions buy attribution, not adaptation" as a finding: the two results were measured on different channel sets under different regimes, so they do not constitute a dissociation.
```

Draft 10's Table 5 caption said: "Two of the three rescored the body-confounded plant at 3, the same as the repaired benchmark paper, and the third reframed what is unoccupied about it as body confounding plus a restricted estimator." The archive backs draft 10, not draft 11 — `docs/archive/red-team/round8-adjudication.md:20` reads: `Disputes with round 7 accepted: option C's novelty is **3, not 3.5 to 4** (Claude, Gemini; Codex reframes the unoccupied condition as body confounding plus a restricted estimator or insufficient excitation)`. Draft 11's "was scored at the same level" turns a two-of-three result into an unattributed consensus, dropping a qualifier the report's own three-of-three convention makes load-bearing.

Separately, draft 11 deletes draft 10's Table 4 (the round-7 scores) without replacement, so the remaining prose has no evidence base. The archive shows the deleted numbers were per-reviewer and non-uniform — `round7-adjudication.md:11`: `| c. Combined benchmark-and-findings paper | 3 | 3.2 | 2.5 (3 if both endpoints share one confounding regime) |`. Draft 11's "was scored as an incremental contribution only after the event is repaired" presents one reviewer's conditional as the panel's verdict, and the one-to-five scale is never introduced in draft 11, so "an incremental contribution" is now uncheckable. (The sentence is also the most machine-sounding in the report: a past-tense "was scored ... only after the event **is** repaired" mixing two tenses, and two unrelated verdicts welded with "and".)

Fix: restore "two of the three ... and the third reframed", and either restore Table 4 or cite `round7-adjudication.md` for the per-reviewer scores.

### P2 — the new introduction claims every number traces to an archived file, which Appendix A and §6 both contradict

`docs/report/technical-report.md:22`

```
The contribution is a negative result with a reusable testbed. Two experiments and one analysis, each verified by three independent implementations or derivations, show that the claim is unsupported on the testbed built to confirm it: its attribution half is IBD's result in an online form, and its adaptation half was never tested under confounding on the channels the primary scored, because the one design that put confounding and change together did so on channels the confounder could not reach. Section 2 describes the testbed and the two estimators, Section 3 the experiments and the analysis, Section 4 what the results support, Section 5 the limitations. The verification protocol and the errors it caught are in the appendices; every number in the report traces to an archived file.
```

Two new assertions, neither carried by draft 10:

- **"every number in the report traces to an archived file"** is refuted by the report's own §6 (line 171): "the historical freeze hashes in Table A1 are assertions from the round log and are not recomputable from the archive as it stands". Those hashes are numbers in the report. §6 promises only "A file map traces each table and figure in this report to the archived input" — table-level, not number-level — and no file map exists anywhere in the folder under review (`release/` contains only `report/technical-report.md`; no file matches `*file-map*`).
- **"each verified by three independent implementations or derivations"** is contradicted by §3.1 (line 86): "That figure is single-model and was not reproduced", by §3.2 (line 107): "These secondary numbers are from two of the three implementations; the third's secondary read was found to be taken at the wrong step and was excluded", and by §3.3 (line 136): "one having initially concluded the opposite on the identifiability question". §2.3 line 48 correctly says "Where a number below comes from fewer than three implementations, it says so" — the introduction overstates what that sentence concedes.

Fix: change to "each table and figure traces to an archived input, implementation, captured output and adjudication, except the Table A1 hashes, which are round-log assertions", and change "each verified by" to "each run by three independent implementations or derivations, with per-number exceptions flagged in Section 2.3".

### P2 — Appendix A extends the protocol to nine rounds, so its "three model families, one prompt" rule now asserts something the same appendix denies

`docs/report/technical-report.md:181`

```
One protocol governed the nine review rounds. Its rules, as they ran:
```

Draft 10 said "One protocol governed the eight rounds" and kept round 9 out of its Table 1 (rows 0–8); round 9 was described separately in §9. Draft 11 raises the count to nine and adds row 9 to Table A1 (line 201, `| 9 | 9 to 15 Sep | prose | archived record | | Review of this report |`). The rules stated immediately below are then claimed to have governed round 9, and they did not:

- Line 184: "**Three model families, one prompt.** Each round the identical prompt went to Codex (OpenAI), Gemini (Google) and a fresh-context Claude agent (Anthropic)". Line 205 in the same appendix says of round 9: "No single run had all three families", and the limitation at line 165 says "this report's own review had two model families, not three (Appendix A)".
- Line 183: "Rounds 1 to 6 reviewed frozen versions; rounds 7 and 8 reviewed the archived record without a new freeze." Round 9 is now inside the count but outside the taxonomy.
- Line 186: "the convergence rule ran in rounds 1 to 8" — unchanged from draft 10, so with nine rounds the "only condition 6 was met" claim no longer covers the last round.

Fix: revert to "One protocol governed the eight review rounds" and mark round 9 in Table A1 as outside the protocol, or add an explicit clause to the three-families bullet stating that round 9 ran with two families.

### P2 — §3.3 anonymises the derivation attributions, erasing that the adjudicator's own model family was one of the two that derived the result directly

`docs/report/technical-report.md:115`

```
with u never observed and G_b the new coupling. The three derivations were reconciled to the same four conclusions in adjudication: two derived them directly; the third's stated theorem concerned the apparent coefficient of a no-latent estimator, and its accompanying remark conceded the same knife-edge condition for equality of the full observational law.
```

Draft 10 named them: "Codex and Claude derived them directly; Gemini's stated theorem concerned the apparent coefficient of a no-latent estimator". The archive confirms draft 10 — `docs/archive/red-team/round8-adjudication.md:7`: `Codex and Claude state this directly; Gemini's "Theorem 1" is a statement about the apparent regression coefficient of a no-latent estimator and its own remark concedes that matching the full law requires σ_a → 0.`

This is not a neutral compression. The report's own limitation (line 165) is that "The adjudicating session ... shares a model family with one of the three reviewers", and Appendix A line 185 lists that as a weakness of the design. Whether the two reviewers who derived the result directly *included* the adjudicator's family is exactly the fact a reader needs to weigh the "three of three" claim, and draft 11 removes it. The same de-attribution runs through §3.1 line 84 ("identified analytically by one implementation", draft 10: "by Codex") and Table 3's caption, while Appendix B's Table B1 still names models (`round 4 (Gemini, R4-GM-02)`, `round 8 (Codex and Claude)`) — so the report is now inconsistent about whether reviewers are named.

Fix: restore the names in §3.1, §3.3 and Table 3, matching Appendix B's convention.

### P3 — the restructure converts the author's first-person error ownership into passive voice in the results sections, leaving it only in Appendix B

`docs/report/technical-report.md:90`

```
Six changes were made in response (decision D-11 in the archive). The first had two parts: certify the event structurally so that it always removes at least one channel, and score the primary over the pre-event support only, so that a channel-constant statistic scores exactly 0.5. The others: replace the comparator's change statistic with the covariance score; seal a held-out set of confirmation seeds behind a hash commitment; implement family N; run every estimator's alarm clock from reset; fit every learned artefact per instance. Both estimator specifications were redrafted against the new contract, and a new version was frozen.
```

Draft 10 line 127 read "I adopted six decisions in response, recorded as D-11 in the archive" and "Fresh-context Claude agents redrafted both specifications". The same de-personalisation recurs at line 101 ("a one-line check of the channel sets before adoption would have caught it", draft 10: "I had recommended that primary without checking the channel sets against each other"), at line 111 ("three systems were asked to derive", draft 10: "I had routed the programme toward it on the premise that ... and asked the three systems"), and draft 10's flat sentence "The premise I had adopted was false." is deleted from §3.3 entirely. Appendix B still says "My repair restricted scoring" and "I routed the programme toward a body-reaching confounder", so the body and the appendix now disagree in register on who made each call, and "Both estimator specifications were redrafted" also drops that the redrafters were Claude agents — the same family as the adjudicator, which is the design weakness the report flags twice.

Fix: keep draft 10's first person in §3.2 and §3.3, and restore "Fresh-context Claude agents redrafted both specifications" and "The premise I had adopted was false."

### P3 — §6 converts draft 10's recommendation about a future repository into a statement of fact about a repository that has not been released

`docs/report/technical-report.md:171`

```
The gate runs under a Python 3.12 interpreter with the pinned NumPy from the requirements file and refuses any other interpreter; the requirements file cannot install Python itself, so a reader must provide 3.12. A stale Python 3.14 virtual environment that a reviewer had left inside the gate directory, and the bytecode caches from three interpreters, were removed before publication; the archive as published has not been run from a clean checkout, and the gate result quoted above is from the author's machine. No per-version snapshot of the archive was retained, so the historical freeze hashes in Table A1 are assertions from the round log and are not recomputable from the archive as it stands; the public repository's first commit is the first reproducible snapshot.
```

Draft 10 wrote this as advice: "A public release should be accompanied by a repository whose commits fix this from that point on." Draft 11 states it as an accomplished fact, in a report whose very next paragraph (line 173) says the archival DOI is "to be minted on release" — i.e. the repository is not yet published, and its first commit cannot have been verified as a reproducible snapshot. Draft 11 also drops draft 10's compensating statement "The archive as it stands hashes to version 6 plus the decision entries added after round 6; earlier versions are documented by hash in the round log."

Fix: restore draft 10's conditional phrasing, or state the commit hash of the first commit and that `freeze.py` reproduces its manifest digest.