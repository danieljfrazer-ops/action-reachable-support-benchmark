# Red-team review — RT-20260909-001

**PANEL_INCOMPLETE** — only 1 model family produced a usable review; 2 required. Anything found below is still worth reading, but this is not a verdict.

1 files reviewed. 1 of 2 required model families produced a usable review (anthropic).
Nothing under review changed while they ran.

1 further claim could not be tied to the code. It is listed at the end with the reason — not deleted, because a claim this tool cannot locate is not necessarily a claim that is wrong.

## Worth knowing

- codex did not count towards diversity — reported it could not review: The report was readable, but the required source-of-truth directory `docs/archive/red-team/` is absent. The in-scope folder contains only `docs/report/technical-report.md`. Therefore I could not fact-check the report’s numbers, hashes, dates, attributions, reviewer consensus, withdrawn claims, tests, or archived references against the specified adjudications and review folders.
- antigravity did not count towards diversity — reported it could not review: I am blocked from completing this review because the required source-of-truth files are missing. The folder in scope (`/var/folders/ly/kfnwgwh53k5gfb09shb8lc640000gn/T/redteamer/RT-20260909-001/review`) only contains `docs/report/technical-report.md`; the `docs/archive/red-team/` directory does not exist. Without access to files like `round5-adjudication-and-tally.md`, `readiness-protocol.md`, and the review folders, I cannot fact-check the claims, numbers, hashes, and attributions in the techni

## Who reviewed

| Reviewer | Model that actually ran | Family | Counts | Status | Time | Kept |
| --- | --- | --- | --- | --- | --- | --- |
| claude-code | `claude-opus-5` (envelope) | anthropic | yes | ok | 261s | 8 (+1 unverified) |
| codex | `gpt-5.6-sol` (session-log) | openai | **no** | ok | 33s | 0 |
| antigravity | `gemini-3.1-pro-high` (pinned-slug) | google | **no** | ok | 50s | 0 |

## What they found

### 1. BLOCKING — The Summary's headline reproducibility claim ("agreed to three decimal places on every number") is falsified by Table 2 on the same page

`docs/report/technical-report.md:86-106`  ·  found by anthropic alone

**claude-code/F-1** (P1, blocking)

`docs/report/technical-report.md:86-94`

```
Three independent implementations agreed on every number. Table 2 gives the base cell.

| Quantity (offset 500, ten distractors, delay 0, confounder present) | Claude | Codex | Gemini |
|---|---|---|---|
| Sequential IBD AUC | 0.800 | 0.815 | 0.831 |
| Passive comparator AUC | 0.691 | 0.688 | 0.675 |
| Passive comparator AUC, confounder absent | 0.875 | 0.878 | 0.863 |
| Confounding benefit | +0.187 | +0.204 | +0.190 |
| Benefit, thirty distractors, delay 2 | +0.240 | +0.237 | +0.228 |
```

Line 16 states "all three agreed to three decimal places on every number both times", and line 86 repeats "agreed on every number". The table directly beneath disagrees in the **second** decimal place on every row: IBD AUC spans 0.800–0.831 (a spread of 0.031), the comparator spans 0.675–0.691, the benefit spans 0.187–0.204. A spread of 0.031 AUC is a third of the pre-declared 0.10 margin (line 98) and larger than the entire round-6 delay-0 benefit of −0.017 (line 112).

This is the load-bearing claim of the whole protocol — it is what licenses "Measured twice by three implementations" (line 152) and the cross-model verification rule at line 38. As written, round 5 shows three implementations that agreed *qualitatively* and disagreed numerically; only round 6 (Table 3, "identical across the three systems", line 108) supports the strong claim.

Fix: restrict the three-decimal claim to round 6, and say what round 5 actually showed — e.g. line 16 → "Round 6 reproduced to three decimal places across all three systems; in round 5 the three implementations agreed on every sign and ordering but differed by up to 0.031 AUC, which the round-5 adjudication attributes to [cause]." Then state that cause explicitly (seed handling? tie correction? interval estimator?), because an unexplained 0.031 spread from "the written specifications alone" is itself a finding about specification determinism.

**claude-code/F-4** (P2)

`docs/report/technical-report.md:91-102`

```
A per-channel vector fixed at fit time, which never saw the scored episode or the event, scored 0.975 against 0.77 to 0.83 for the two arms.
```

Table 2 (line 91) reports the passive comparator at 0.691 / 0.688 / 0.675 in the base cell, and line 98 reports the interventional arm "at 0.80 to 0.85". The claimed envelope for "the two arms" (0.77–0.83) contains neither: its floor is ~0.08 above the comparator's measured value and its ceiling is below the interventional arm's stated top. This is the number that carries the sentence's rhetorical weight — a fit-time constant "beating both arms" — so the margin over the *weaker* arm is being understated by roughly 0.09 AUC, and the reader cannot tell which cells the range aggregates over. Fix: state the cell and give both arms separately, e.g. "scored 0.975, against 0.800–0.831 for the interventional arm and 0.675–0.691 for the comparator in the same base cell (Table 2)".

**claude-code/F-3** (P2)

`docs/report/technical-report.md:106`

```
I adopted six decisions in response (D-11 in the archive): certify the event structurally so that it always removes at least one channel; score the primary over the pre-event support only, so that a channel-constant statistic scores exactly 0.5; replace the comparator's change statistic with the covariance score; seal a held-out set of confirmation seeds behind a hash commitment; implement family N; run every estimator's alarm clock from reset; and fit every learned artefact per instance.
```

Seven semicolon-separated items: (1) certify the event, (2) score pre-event support only, (3) covariance score, (4) seal confirmation seeds, (5) family N, (6) alarm clock from reset, (7) per-instance fitting. Since this sentence is the report's only public record of decision D-11, a reader auditing against the archive cannot tell whether one item was added editorially, whether two were one decision in the original, or whether the count is simply wrong — and the report's central defence is that its decisions are traceable. Fix: change to "seven decisions", or if D-11 in the archive really contains six, number them `D-11.1 … D-11.6` inline and show which two the report has split.


### 2. BLOCKING — Table 3's delay-0 row contradicts the "bitwise identical / exactly zero by construction" mechanism that Section 6 records as the programme's third error

`docs/report/technical-report.md:112-117`  ·  found by anthropic alone

**claude-code/F-2** (P1, blocking)

`docs/report/technical-report.md:112-117`

```
| Ten or thirty distractors, delay 0 | 0.813 | 0.879 | 0.863 | −0.017 |
| Ten or thirty distractors, delay 2 | 0.687 | 1.000 | 1.000 | 0.000 |

Table 3. Round 6 on frozen version 38d161e762a3de76. The channel-constant control scored exactly 0.500 in every cell. The static loading vector scored 0.422 at delay 0 and 0.200 at delay 2.

The benefit was zero because the pre-event support contains only body and downstream channels, the confounder enters only the distractor block, and the absent condition keeps the policy unchanged, so the present and absent streams are bitwise identical on every channel the primary scores. All three reviewers found this, and I confirmed it against the generator. The re-posed primary measured adaptation on channels the treatment provably cannot reach. I had recommended that primary without checking the channel sets against each other; a one-line check would have caught it.
```

If the present and absent streams are *bitwise identical* on every scored channel, then every scored statistic must be bit-identical, so the comparator's present and absent AUCs must be the same number and the benefit must be exactly `0.000`. The delay-2 row satisfies this (1.000 / 1.000 / 0.000). The delay-0 row does not: comparator present 0.879 vs absent 0.863, benefit −0.017. The IBD column header ("Sequential IBD, present and absent", line 110) asserts exact present/absent equality with a single value 0.813, which makes the comparator's 0.016 discrepancy on the *same* streams doubly anomalous — the same allegedly identical input produced identical output for one arm and different output for the other.

Separately, the tabled −0.017 does not reproduce from the definition at line 78 (`(IBD_present − comp_present) − (IBD_absent − comp_absent)` = (0.813−0.879) − (0.813−0.863) = **−0.016**), so the delay-0 row is internally unrecoverable at the precision it is reported to.

Exactly one of three things is true, and each changes the report: (i) the numbers are wrong; (ii) the streams are *not* bitwise identical at delay 0, in which case the "exactly zero by construction" claim at line 18 and the third error in Section 6 (line 168) are overstated and rest on an argument that the data falsify; or (iii) the comparator has a hidden dependence on the confounder path (state carried across the fit split, ridge standardisation fitted on all channels including distractors — see line 72, "whitened by the fit-split action covariance"), which would be a live defect in the comparator, not a property of the primary.

Fix: resolve which. If (iii), say so — an artefact-mediated leak of the confounder into a "confounder-free" scored statistic is a more interesting finding than the one currently written. If (i), correct the row and re-derive. In all cases replace "exactly zero by construction" with the measured value and state the tolerance, and drop "bitwise identical" unless a byte-level comparison was actually run (the text says only "I confirmed it against the generator").


### 3. P2 — The protocol says the author never implements or reviews, and the results section then relies on an author-run, single-model check

`docs/report/technical-report.md:36-38`  ·  found by anthropic alone

**claude-code/F-5** (P2)

`docs/report/technical-report.md:36-38`

```
- **Author adjudicates, never reviews.** I decide estimands and design decisions and write the adjudication after all three report. I do not review or implement.
- **Exit criteria are executable.** A gate directory holds assertion tests and mutants; the criterion for readiness is the gate's exit code, not prose. A normative item without a test identifier is not implemented until it has one.
- **Single-model results are unverified.** Any simulation run by one system, including the author's, is treated as unverified until a second system reproduces it.
```

Line 117 says "All three reviewers found this, and **I confirmed it against the generator**", and line 154's third caveat ("the confounder did not reach the scored channels") rests on that confirmation. Under the rule at line 36 the author does not implement; under the rule at line 38 an author-run check is unverified until a second system reproduces it. The report never says which of the two applies here, and the claim being confirmed is precisely the one the delay-0 row appears to contradict (see the P1 above). This matters beyond bookkeeping: the confirmation is a *structural* claim about the generator (which channels the confounder reaches), and structural claims are what the protocol is designed to keep out of prose and inside the gate. Fix: either cite the gate test identifier that asserts "no confounder parent is an ancestor of any pre-event-support channel" — line 37 requires one for every normative item — or restate line 117 as "I inspected the generator source and agree with the reviewers' argument; this was not independently executed."


### 4. P2 — Family N is specified, certified and listed as implemented, but no family N result is reported anywhere

`docs/report/technical-report.md:174-174`  ·  found by anthropic alone

**claude-code/F-6** (P2)

`docs/report/technical-report.md:174`

```
The generator is one linear-Gaussian family with a scalar context, plus one nonlinear variant run on five seeds.
```

Family N is defined in detail at line 62 (tanh drive, clipped quadratic self-term, certified by empirical boundedness and stationarity rather than spectral radius), adopted as a decision at line 106, shipped in the archive at line 178, and here stated to have been *run on five seeds*. Yet Section 4 reports only family L: Table 3 is labelled "the family L base cells" (line 108) and line 119 restricts its conclusion to "every family L cell and every perturbation cell". Section 5's surviving claim (line 154) says "On the plant studied" — singular — without saying whether the nonlinear plant agreed or disagreed.

Concretely: the report claims a passive monitor equals or beats probing, and the single most obvious threat to that claim is nonlinearity, which is exactly what family N was built to probe and which was apparently executed. Withholding those five seeds means the strongest available test of the headline negative result is unreported. Fix: report the family N cells in Table 3 (or a Table 3b) even if n=5 and the intervals are useless — state them as five seeds, no interval — or state plainly in Section 7 that family N was implemented and certified but its outcomes were not scored, and why.


### 5. P2 — Three of the six references are never cited; two claims that need citations have none

`docs/report/technical-report.md:186-194`  ·  found by anthropic alone

**claude-code/F-7** (P2)

`docs/report/technical-report.md:186-194`

```
Basseville, M. and Nikiforov, I. V. (1993). *Detection of Abrupt Changes: Theory and Application*. Prentice Hall.
```

`Basseville and Nikiforov (1993)`, `Mann and Whitney (1947)` (line 192) and `Page (1954)` (line 194) appear nowhere in the body — only `Liu, Cheng and Bogdan` (line 26) and `Heirung and Mesbah` / `Willsky` (line 138) are cited. Meanwhile the two places that need them are bare: line 70's "tie-corrected rank-sum statistic" (Mann–Whitney) and line 164's "specified by analogy with a CUSUM on residuals" (Page; Basseville and Nikiforov). A reference list padded with uncited works while the corresponding in-text claims are uncited is the first thing a referee grep will catch. Fix: cite them at lines 70 and 164, or delete them.

Related and unverifiable from here: line 138 attributes the attribution result to "IBD's Proposition 3.3" and asserts that "the IBD paper explicitly admits any confounder-independent probe distribution, which pre-authorises the sign-randomised variant". That is the single load-bearing novelty concession in the report — it is what demotes the surviving positive result to "a replication of IBD's principle" (line 152). It needs a page/section locator, and the word "pre-authorises" needs to be either a quotation from the paper or softened to "is covered by", since a proposition admitting a class of distributions is not the same as the paper anticipating this estimator.


### 6. P3 — Section 4.4 states the report's only formal result entirely in prose, and its opening sentence is a filler line that should be doing work

`docs/report/technical-report.md:144-144`  ·  found by anthropic alone

**claude-code/F-9** (P3)

`docs/report/technical-report.md:144`

```
They agreed on the substance. Exact non-identifiability is a knife-edge, not an open set. The observational law at all lags contains the policy's own independent action noise, which acts as an instrument: the covariance discontinuity at the causal lag pins the body coupling separately from the smooth AR(1) confounder path. Exact confusion between an actuator loss and a support-preserving change in the confounder's coupling needs zero action noise in the affected direction. What does fail on an open set of parameters is the model class the working claim is about, any predictor without a latent context variable: its action coefficient converges to the true coupling plus a term proportional to the product of the body coupling and the policy's context gain, and no depth of lags repairs it. The frozen comparator cannot distinguish an actuator loss from a confounder change; its change score diverges under both, and under body confounding the confuser produces the larger signal on channels the loss never touches. The sign-randomised contrast identifies the causal column at the first reachable horizon regardless of the confounder, drops to zero under loss, and is unchanged under a confounder change.
```

This paragraph is the basis of the third surviving claim (line 156) and of Round 8's entire contribution, and it contains not one symbol. "its action coefficient converges to the true coupling plus a term proportional to the product of the body coupling and the policy's context gain" is an asymptotic bias formula written out in words; a referee cannot check it, and neither can the three systems' agreement be audited against it. "Knife-edge, not an open set", "at all lags", "no depth of lags repairs it" and "at the first reachable horizon" are each precise mathematical claims stated informally. Fix: give the plant equations and the probability limit as two or three displayed equations (β̂ → β + αγ-type form, with the symbols defined against Section 3.1's blocks b, d, w, x, u), state the regularity conditions under which the limit holds, and move the prose to a one-paragraph reading of the equations. If the derivations live in the archive, cite the specific adjudication section for each of the four sub-claims.

On the machine-written register, two sentences to rewrite:

- Line 144, "They agreed on the substance." — a content-free hinge. Rewrite: "All three derivations reached the same four conclusions, which I state in the order I asked for them."
- Line 32, "Everything in this report was produced under one protocol, which I state because the protocol is what caught the errors." — circular, and it asserts the report's conclusion in its setup. Rewrite: "One protocol governed all eight rounds. I set it out here because Section 6 argues that three of the defects were caught by specific rules in it, and the reader should be able to check that claim against the rules as written."

One further item I did not raise to a separate finding but that a referee will ask about: Table 1 (lines 48–49) gives rounds 4 and 5 the identical freeze hash `0468104f6431b050`, the first labelled "(candidate)". Under the rule at line 34, repairs produce a new version — so an identical hash means round 4's review produced no file change before the first execution round ran on it. That may be deliberate, but the report never says so, and it sits oddly beside the claim that round 4 delivered "Both estimator specs; 37 tests, 40 mutants".


## Claims this tool could not tie to the code

Shown, not deleted. Each one may be a real problem the reviewer described imprecisely, or a
claim with nothing behind it — the reason says which is more likely. Judge them yourself.

- **claude-code/F-8** (P2) — the quoted text does not appear in that file
  - claimed: The report is unverifiable as published: the archive it rests on has no location, and neither do the hashes
  - cited: `docs/report/technical-report.md:178-178`

## Reviewers that could not review

- **codex** — The report was readable, but the required source-of-truth directory `docs/archive/red-team/` is absent. The in-scope folder contains only `docs/report/technical-report.md`. Therefore I could not fact-check the report’s numbers, hashes, dates, attributions, reviewer consensus, withdrawn claims, tests, or archived references against the specified adjudications and review folders.
- **antigravity** — I am blocked from completing this review because the required source-of-truth files are missing. The folder in scope (`/var/folders/ly/kfnwgwh53k5gfb09shb8lc640000gn/T/redteamer/RT-20260909-001/review`) only contains `docs/report/technical-report.md`; the `docs/archive/red-team/` directory does not exist. Without access to files like `round5-adjudication-and-tally.md`, `readiness-protocol.md`, and the review folders, I cannot fact-check the claims, numbers, hashes, and attributions in the techni
