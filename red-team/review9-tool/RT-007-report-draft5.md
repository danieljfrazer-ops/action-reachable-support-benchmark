# Red-team review — RT-20260910-007

**FAIL** — 1 blocking problem with checked evidence.

286 files reviewed. 2 of 2 required model families produced a usable review (anthropic, google).
Nothing under review changed while they ran.

## Worth knowing

- 2 directories were skipped by name and never reviewed: docs/archive/red-team/.DS_Store, docs/archive/red-team/executable-proofs/.DS_Store
- codex did not count towards diversity — did not produce a review (error)
- antigravity: counted, but its model was NOT verified: "gemini-3.1-pro-high" is what was asked for, not what was observed — this tool does not report which model actually ran

## Who reviewed

| Reviewer | Model that actually ran | Family | Counts | Status | Time | Kept |
| --- | --- | --- | --- | --- | --- | --- |
| claude-code | `claude-opus-5` (envelope) | anthropic | yes | ok | 534s | 7 |
| codex | `gpt-5.6-sol` (session-log) | openai | **no** | error — Reading additional input from stdin... | 7s | — |
| antigravity | `gemini-3.1-pro-high` (pinned-slug) | google | yes | ok | 520s | 1 |

## What they found

### 1. BLOCKING — §6's newly added round-4 sentence is false: a round-4 reviewer named the mean-shift blindness with executable evidence, and the author's adjudication rejected the mechanism

`docs/report/technical-report.md:179-179`  ·  found by anthropic alone

**claude-code/F-1** (P1, blocking)

`docs/report/technical-report.md:179`

```
Round 4 did find the comparator structurally incapable, three of three, and rewrote its features and loading; the disagreement was attributed to the unspecified generator and to loading and delay misalignment, not to the change term.
```

The change term is exactly what one round-4 reviewer attacked, as a high finding backed by its own simulation:

`docs/archive/red-team/review4-gemini/findings.md:91`

```
| **R4-GM-02** | high | `comparator-spec.md` §2: innovation-mean shift detects loss of actuator support | Derivation & `sim_r4.py`: Under zero-mean policy ($E[a]=0$), actuator loss produces zero innovation-mean shift. Comparator assigns $q \approx 8.3$ to lost channels and $q \approx 7.9$ to retained channels, blind to loss. | Replace first-moment shift with covariance/variance shift score, or disclose zero-mean blindspot. | prose / decision |
```

and the adjudication that draft 5 is summarising rejected it:

`docs/archive/red-team/round4-adjudication-and-tally.md:39`

```
- Gemini GM-02 "mathematically blind under a zero-mean policy": the identity is wrong as stated (the score uses the finite-window sample mean, amplified by √n); the instance-dependent observation is valid and is subsumed by D-10.2.
```

This is not a nuance about attribution of a disagreement. §6 is the section the report offers as its transferable contribution, and its thesis for this defect is that the freeze is what made it findable ("The first defect survived a round in which three models implemented the arm on instances of their own, and fell in the first round on one frozen generator", `:187`). The record says the defect was *reported* a round earlier, at high severity, with a simulation showing lost and retained channels scoring 8.3 and 7.9, and was rejected by the adjudicating layer on the grounds that the exact-zero identity does not hold in finite windows — which is true and beside the point, since the finite-window version is precisely what round 5 then measured. The mechanism that actually let the defect through was a mis-adjudication, not a missing freeze, and RT-006 item 3 (which draft 5 was answering) did not catch this because it stopped at the two *convergent* causes in `:15-17`.

It also makes the surrounding accounting wrong: the Summary's "four errors of mine that the protocol caught" (`:20`) counts only the design errors and silently drops the adjudication error that let the first one survive an extra round.

Fix: replace the quoted clause with something the record supports, e.g. *"Round 4 found the comparator structurally incapable, three of three, and D-10.2 rewrote its features and loading. One reviewer (Gemini R4-GM-02, high) also named the change term itself, showing by simulation that a zero-mean policy leaves lost and retained channels indistinguishable; I rejected the mechanism because the stated identity is exact only in the population and the statistic uses a finite-window mean, and folded the finding into D-10.2. That rejection was wrong, and it is why the blindness survived into version 5, where round 5 — the first round on a single frozen generator — measured it."* Then add a fifth entry, or an explicit note, to §6's count and to the Summary at `:20`: the adjudicating layer is a failure point too, and this is the report's own evidence for it.


### 2. P2 — §6 and the Summary count four errors and omit the one the archive corrected on the day of this draft

`docs/report/technical-report.md:20-20`  ·  found by anthropic alone

**claude-code/F-5** (P2)

`docs/report/technical-report.md:20`

```
and four errors of mine that the protocol caught, three within one execution round each and one in round 8's cross-model derivation and adjudication, before anything was built.
```

`docs/archive/red-team/round6-adjudication-and-tally.md:50-51`

```
## Erratum (10 September 2026)
§3 first bullet narrowed the interventional arm's round-6 secondary full-channel AUC to "0.85 to 0.87"; the reviewer outputs give 0.851/0.863 (present/absent) at delay 0 and 0.753/0.751 at delay 2 on N_x = 10, so the range over the four family-L base cells is 0.75 to 0.87, with present and absent differing by at most 0.013 in every cell. The claim that the arm is not degraded by the confounder stands; the range was wrong. Found by the round-9 report review.
```

Draft 5 silently adopts the corrected numbers at `:124` and `:167` — which is the right call — but never says that the number it had published came from an adjudication that misread its own reviewer outputs, that the error stood in the archive for two days, and that it was found by a review of the *report*, not by any of the eight rounds. Together with the round-4 rejection in the P1 finding above, that is two documented errors in the adjudication layer, neither of them in §6's list of four, in a report whose Section 2 sells "Adjudication separate from review" as a protocol strength and whose Section 6 is titled "Four errors, and what caught them".

Fix: add a fifth item to §6, or a paragraph after it: *"Two further errors were mine as adjudicator rather than as designer: rejecting the round-4 finding that named the comparator's change term, and narrowing the round-6 secondary AUC to a delay-0 read in the round-6 adjudication (corrected by erratum on 10 September 2026, found by a review of this report rather than by any round). Neither was caught by a cross-model round; the reviewers had the evidence in both cases and the adjudicating step lost it."* Then reword `:20` to say five, or to say four design errors and two adjudication errors.


### 3. P2 — §2's restatement of the readiness conditions drops half of condition 2 and half of condition 4, then asserts condition 2 was exercised, and overstates the convergence rule's reach

`docs/report/technical-report.md:37-39`  ·  found by anthropic alone

**claude-code/F-6** (P3)

`docs/report/technical-report.md:37`

```
The readiness protocol set six conditions for a version: zero normative items without a test identifier; every registered mutant makes at least one test fail; an independent black-box acceptance suite, written by an agent other than the builder from the interface specification alone, passes; a hand-computed reference case matches the pipeline; a runtime pilot has recorded per-cell durations; and the three-reviewer convergence rule is satisfied. Conditions 1, 2 and 6 were exercised: the gate's exit code was the operational test of the first two, and the convergence rule ran in every round.
```

Against `readiness-protocol.md:13-15`, condition 2 is "Every mutant makes at least one test fail; **a reintroduced historical bug fails the gate**" and condition 4 is "matches both the pipeline **and `contract_ref.py`**". The report drops both halves and then says condition 2 "was exercised" — nothing in `gate.output.txt:71-119` is a reintroduced historical bug rather than a registered mutant, so the second half of condition 2 has the same status as conditions 3–5. And "the convergence rule ran in every round" is contradicted by the report's own Table 1 row 0 (`:45`), which records round 0 as `single-model prose`; RT-006's suggested wording was "in every round from 1 to 8" and the qualifier was dropped in transcription.

Fix: restore the two elided clauses, and write `"Conditions 1 and 6 were exercised — the gate's exit code was the operational test of condition 1 and of condition 2's mutant clause, and the convergence rule ran in rounds 1 to 8; round 0 was single-model. Condition 2's reintroduced-historical-bug clause and conditions 3, 4 and 5 were never done, so no version was readiness-certified."` The same count is repeated at `:200` and should follow.

**claude-code/F-3** (P2)

`docs/report/technical-report.md:39`

```
- **Design changes need a round.** No change to what is measured was adopted without a cross-model round on it.
```

`docs/report/technical-report.md:187`

```
The third was introduced by the post-round-5 repair and fell in the execution round that followed, the first opportunity anyone had to see it.
```

Both cannot be true. D-11.1a changed what is measured — from full-channel AUC to AUC over the pre-event support — and the archive shows it was decided, encoded and frozen before any reviewer saw it: `decisions-required.md:19` ("D-11: Daniel adopted all six recommendations on 7 September 2026 … encoded in `stage-0a-contract-v3.9.md` §L, `interface-spec-v5.md`, the gate"), with round 6 then run *on* the frozen result. The recommendation text itself only asks for "cross-model execution round before freezing" as a condition on D-11.2 (`decisions-required.md:26`), which is a rule about confirming a change, not about adopting one. As written, `:39` tells a reader that the estimand change got cross-model scrutiny before adoption, which is the precise failure that §6's third error is about — and it weakens §6, because the honest version of the rule is the lesson the programme actually learned.

Fix: `"**Design changes need a round.** No change to what is measured was treated as confirmed without a cross-model round on it. The rule did not require a round before *adoption*, and the third error in Section 6 is what that cost: the re-posed primary was decided, encoded and frozen, and round 6 was the first time anyone examined it."`


### 4. P2 — §4.4's "all three noted" is over-attributed; only one of the three derivations raises the latent state-space rebuttal or a third arm

`docs/report/technical-report.md:163-167`  ·  found by anthropic alone

**claude-code/F-2** (P2)

`docs/report/technical-report.md:163`

```
all three noted that a referee's first question, why not fit a latent state-space model, would have to be answered by a third arm.
```

This clause was carried over verbatim from RT-006's suggested fix and was never checked. In the three round-8 derivations, only Claude's raises it: `review8-claude-opus/derivation.md:435` ("A third arm is required [opinion, strongly held]: a *deconfounded passive* arm"), `:461`, `:636` and `:651-652` ("A referee who asks 'why not fit a state-space model with a latent AR(1) confounder?'"). `review8-codex/derivation.md` contains no occurrence of "third arm", "state-space", "Kalman" or "referee"; its nearest statement is `:352` ("A win could be a comparator-misspecification result"), which is a different objection. `review8-gemini/derivation.md` mentions state-space models only at `:395`, and there as a reason to *cut* option C's novelty score, not as a design requirement. The round-8 adjudication puts the third-arm point in its own §3 conclusion, unattributed, not in the "three of three" list of §1.

The report is elsewhere scrupulous about saying how many systems produced each statement, and §8 leans on this one when it makes "a latent-modelling passive third arm" part of the condition that would reopen the question (`:205`). Fix: `"…as body confounding plus a restricted estimator; one of the three made the referee's obvious rebuttal, why not fit a latent state-space model with the confounder as a latent AR(1), a design requirement, and proposed answering it with a deconfounded passive third arm."` and soften `:205` to match.

**claude-code/F-4** (P2)

`docs/report/technical-report.md:167`

```
**Sign-randomised probing, online and at a 5 percent probe budget, was not degraded by the shared-cause confounder that reduced a frozen passive residual monitor's full-channel AUC by about 0.2 in the base cells.** The passive monitor's loss came from crediting confounded distractors with control; the probed estimator's own score barely moved between conditions, 0.851 against 0.863 at delay 0 and 0.753 against 0.751 at delay 2 on ten distractors in round 6. The gap was measured on the full channel set by three implementations in round 5, where the probed arm scored 0.80 to 0.83 in the base cell and the benefit did not clear its margin on the perturbation set, and by two implementations in round 6.
```

The round-5 number (0.691 present against 0.875 absent, Table 2) is the comparator's **full score** `q`. The round-6 number (0.73–0.80 against 0.96–0.98, `round6-adjudication-and-tally.md:31`) is the **loading-only secondary**, which comparator spec v3 made a frozen fit-time vector — `readiness-protocol.md:97` records "comparator-spec v3 (D-11.2 covariance score; secondary = loading alone)". The two are demonstrably different quantities on the same runs: `review5-claude-opus/schange_split.output.txt:7-8` gives AUC(l) = 0.975 / 1.000 against AUC(q@500) = 0.845 / 0.890 on the same cells.

So "measured … by three implementations in round 5 … and by two implementations in round 6" reads as one quantity replicated twice, when it is two estimators measured once each. §4.2 does disclose it ("only in the secondary full-channel measure: the comparator's static loading", `:124`), but §5 is the section a reader quotes, and it is also the one place the report needs to be strictest — the report's own §4.3 withdraws the dissociation claim precisely because two endpoints under different constructions were pooled.

Fix: `"…The gap was measured on the full channel set twice, on different passive statistics: by three implementations in round 5 on the comparator's full score (0.691 against 0.875 in the base cell; the probed arm 0.80 to 0.83, and the benefit did not clear its margin on the perturbation set), and by two implementations in round 6 on the loading-only secondary, a fit-time vector that never sees the scored episode (0.73 to 0.80 against 0.96 to 0.98)."` Add the same qualification to the Limitations list.


### 5. P3 — §4.2 omits the requested delay-0 clarification when fixing the round-6 secondary range

`docs/report/technical-report.md:124-124`  ·  found by google alone

**antigravity/F-1** (P3)

`docs/report/technical-report.md:124`

```
scoring 0.73 to 0.80 with the confounder present against 0.96 to 0.98 without it, while the interventional arm scored 0.75 to 0.87 across the four base cells and moved by at most 0.013 between conditions.
```

Draft 4 Item 2 (`claude-code/F-1`) explicitly instructed the author to "Correct line 124 the same way, and record that the adjudication's '0.85 to 0.87' was a delay-0 read." 

Draft 5 correctly widens the range to 0.75 to 0.87 across the four base cells, but it completely drops the requested explanation. Because the previously reported 0.85–0.87 range is no longer in the sentence at all, a reader comparing this text to the adjudication or earlier drafts has no explanation for the change.

Fix: append the clarification: `"…moved by at most 0.013 between conditions (the adjudication's earlier '0.85 to 0.87' figure was a delay-0 read)."`


### 6. P3 — §6's closing paragraph promises the mechanisms of four errors and accounts for three

`docs/report/technical-report.md:187-187`  ·  found by anthropic alone

**claude-code/F-7** (P3)

`docs/report/technical-report.md:187`

```
The mechanisms differ. The first defect survived a round in which three models implemented the arm on instances of their own, and fell in the first round on one frozen generator. The second became testable only once the generator was frozen, because it is a property of the generator's event. The third was introduced by the post-round-5 repair and fell in the execution round that followed, the first opportunity anyone had to see it.
```

The paragraph is the analytic payload of the section the report offers as its transferable contribution, and it stops at three. The fourth error — the refuted premise — has the most interesting mechanism of the four (it was killed by prose at zero build cost, and the three derivations initially disagreed about the answer), and its bullet at `:185` states the cost but not the mechanism. As it stands the paragraph reads as an enumeration that ran out, which is the kind of shape a referee reads as machine-written.

Fix: add a fourth sentence, e.g. *"The fourth never needed a build: it was a claim about a population limit, and three derivations of one page's algebra settled it — though they had to be reconciled first, since one of them initially concluded the opposite."*

