# Red-team review — RT-20260910-009

**PANEL_INCOMPLETE** — only 1 model family produced a usable review; 2 required. Anything found below is still worth reading, but this is not a verdict.

288 files reviewed. 1 of 2 required model families produced a usable review (anthropic).
Nothing under review changed while they ran.

1 further claim could not be tied to the code. It is listed at the end with the reason — not deleted, because a claim this tool cannot locate is not necessarily a claim that is wrong.

## Worth knowing

- 2 directories were skipped by name and never reviewed: docs/archive/red-team/.DS_Store, docs/archive/red-team/executable-proofs/.DS_Store
- codex did not count towards diversity — did not produce a review (error)
- antigravity did not count towards diversity — nothing readable came back — this is not the same as a clean review
- antigravity: the reply had no finding headings in it

## Who reviewed

| Reviewer | Model that actually ran | Family | Counts | Status | Time | Kept |
| --- | --- | --- | --- | --- | --- | --- |
| claude-code | `claude-opus-5` (envelope) | anthropic | yes | ok | 594s | 6 (+1 unverified) |
| codex | `gpt-5.6-sol` (session-log) | openai | **no** | error — Reading additional input from stdin... | 7s | — |
| antigravity | `gemini-3.1-pro-high` (pinned-slug) | google | **no** | ok | 218s | 0 |

## What they found

### 1. P2 — §5's headline surviving result rests half on a round-5 measurement the contract's own competence floor declared inadmissible, and §5 does not say so

`docs/report/technical-report.md:167-167`  ·  found by anthropic alone

**claude-code/F-3** (P2)

`docs/report/technical-report.md:167`

```
**Sign-randomised probing, online and at a 5 percent probe budget, was not degraded by the shared-cause confounder that reduced a frozen passive residual monitor's full-channel AUC by about 0.2 in the base cells.** The passive monitor's loss came from crediting confounded distractors with control; the probed estimator's own score barely moved between conditions, 0.851 against 0.863 at delay 0 and 0.753 against 0.751 at delay 2 on ten distractors in round 6. The gap was measured on the full channel set twice, on different passive statistics: by three implementations in round 5 on the comparator's full score (0.691 against 0.875 in the base cell; the probed arm 0.80 to 0.83; the benefit did not clear its margin on the perturbation set), and by two implementations in round 6 on the loading-only secondary, a fit-time vector that never sees the scored episode (0.73 to 0.80 against 0.96 to 0.98).
```

The 0.875 quoted here is the number that failed the pre-declared floor. §4.1 says so in terms:

`docs/report/technical-report.md:99`

```
And the result was inadmissible, because the competence floor failed: without confounding the comparator's lower bound was 0.64 to 0.83 against the required 0.85, in every base cell for two reviewers and in ten of twelve cell-offsets for the third.
```

and §3.3 gives the reason the floor exists: "so that a benefit could not come from a broken baseline" (`:79`). `round5-adjudication-and-tally.md:20` states it as the operative verdict ("The result is inadmissible because the D-10.3 competence floor fails first"). Concretely, the round-5 passive score was dominated by a mean-shift term that cost it 0.12–0.27 AUC on the ranking task itself (`round5-adjudication-and-tally.md:21`; the report repeats it at `:101`), so part of the 0.184 gap the sentence attributes to the confounder is the crippled statistic, not the confounder. §5 presents the two measurements as symmetric ("two estimators measured once each") without saying that one of the two was ruled out by the contract for exactly the reason a reader would worry about.

Fix: in `:167`, mark the round-5 half — "(0.691 against 0.875 in the base cell, on a statistic the same round found defective and a baseline that failed the pre-declared competence floor, so this half is not admissible under the contract's own rule)" — and rest the claim on the round-6 loading-only measurement, stating that it is two implementations, not three.


### 2. P2 — §2 and §6 still say round 6 was the first chance anyone had to examine the re-posed primary, which §2's own new sentence and both spec redrafts contradict

`docs/report/technical-report.md:187-187`  ·  found by anthropic alone

**claude-code/F-2** (P2)

`docs/report/technical-report.md:187`

```
The third was introduced by the post-round-5 repair and fell in the execution round that followed, the first opportunity anyone had to see it.
```

`docs/report/technical-report.md:39`

```
- **Design changes need a round.** No change to what is measured was treated as confirmed without a cross-model round on it. The rule did not require a round before adoption, and the third error in Section 6 is what that cost: the re-posed primary was decided, encoded and frozen, and round 6 was the first time anyone examined it.
```

Draft 7 accepted RT-008's correction that the redrafting agents worked from the round-5 adjudication and D-11 (`:36`), but kept the inference that correction was aimed at. Two fresh-context agents read D-11.1a and encoded it before the freeze:

`docs/archive/red-team/sequential-ibd-spec.md:9`

```
1. **The primary becomes the pre-event-support AUC** (D-11.1a, §6). `raw_support = a_c` is unchanged and `secondary_support()` returns the same vector; what changes is the set the evaluator ranks over and therefore what the arm is credited for.
```

`docs/archive/red-team/comparator-spec.md:5` carries the same ("the primary AUC is now computed over the pre-event support (D-11.1a, §4.4)"). Both agents examined the re-posed primary, and both had the channel sets in front of them — the same one-line check the report says would have caught it (`:118`). So "the first opportunity anyone had to see it" is false, and it makes the protocol look tighter than it was: the report's own lesson is that the encoding step is a checkpoint that was not used as one.

Fix at `:187`: "The third was introduced by the post-round-5 repair; the two redrafting agents encoded it from the adjudication without checking the channel sets, and the execution round that followed was the first place it was checked." Same correction at `:39`.


### 3. P2 — §7 says the round-6 per-episode primary had one negative; on 6 of 40 draws it had two, and the "at most six values" lattice claim does not hold there

`docs/report/technical-report.md:197-202`  ·  found by anthropic alone

**claude-code/F-6** (P3)

`docs/report/technical-report.md:197`

```
- The per-episode primary in round 6 was an AUC with one negative against three to five positives, a lattice of at most six values, and the interval estimator was unspecified, which is why the competence-floor verdict at delay 0 is undetermined rather than failed.
```

All three reviewer outputs record two lost channels on three of ten instances in each delay-0 cell:

`docs/archive/red-team/review6-claude-opus/report.txt:402-405`

```
  L_Nx10_tau0      n_lost={1: 7, 2: 3}  |pre|={5: 3, 6: 7}  C=[24]  n_resamples={0: 9, 1: 1}
  L_Nx10_tau2      n_lost={1: 10}  |pre|={4: 10}  C=[24]  n_resamples={0: 9, 1: 1}
  L_Nx30_tau0      n_lost={1: 7, 2: 3}  |pre|={5: 3, 6: 7}  C=[44]  n_resamples={0: 9, 1: 1}
  L_Nx30_tau2      n_lost={1: 10}  |pre|={4: 10}  C=[44]  n_resamples={0: 9, 1: 1}
```

`review6-codex/report.md:156-159` and `review6-gemini/sim_output.txt:63-66` give the same distributions. With two negatives against four positives the AUC lattice has nine values, not six — which matters because the sentence's purpose is to justify calling the delay-0 floor verdict "undetermined". (The wording is inherited from `round6-adjudication-and-tally.md:24`, which also states a 32/8 split over 40 draws where all three reviewer outputs give 34/6; the report should not carry the looser version.)

Fix: "an AUC with one or two negatives against three to five positives, a lattice of at most six values when one channel is lost and nine when two are".

**claude-code/F-5** (P2)

`docs/report/technical-report.md:202`

```
- The readiness protocol's independent acceptance suite, hand-computed reference case and runtime pilot were never done, so no version was readiness-certified.
```

§2 was corrected and now says condition 1 failed as well:

`docs/report/technical-report.md:37`

```
The gate's exit code was the operational test of condition 2's mutant clause only; nothing in the gate reads the coverage matrix, which at version 6 still lists four uncovered normative groups, so condition 1 was not met. Condition 2's historical-bug clause and conditions 3, 4 and 5 were never done. No version was readiness-certified.
```

confirmed by `executable-proofs/gate/coverage-matrix.md:29` ("Uncovered normative groups: 4 … Phase 0A gate requires 0"). A reader who reads §7 alone — which is what a referee scanning limitations does — is told three of six conditions are outstanding when the true count is five of six (conditions 1, 2b, 3, 4, 5). RT-008 asked for this correction at `:202` explicitly and it did not land.

The same section is also missing the RT-008 item-3 addition. The weak-instrument caveat now appears at `:151` and `:171`, but §7 has no bullet for it, even though it is the limitation of the only result §5 calls new, and §8 (`:207`) proposes building the latent-modelling arm that `review8-gemini/derivation.md:109` predicts will not separate the two laws at σ_a = 0.1.

Fix: replace `:202` with "The readiness protocol's coverage-matrix condition, historical-bug clause, independent acceptance suite, hand-computed reference case and runtime pilot were never satisfied — five of the six conditions — so no version was readiness-certified", and add a bullet: "The round-8 identifiability result is a population-limit statement; the instrument it relies on is weak at the contract's constants (σ_a = 0.1 against σ_u = 1.0) and one of the three derivations expects the two laws to be empirically indistinguishable in finite samples."


### 4. P2 — §9's account of the report's own tool reviews is still wrong: the archive holds seven runs for six drafts, and one numbered run is missing

`docs/report/technical-report.md:215-215`  ·  found by anthropic alone

**claude-code/F-4** (P2)

`docs/report/technical-report.md:215`

```
Its review against the archive was by a fresh-context Claude Opus agent and by a cross-model review tool run once per draft from draft 1 onward, with every run's report archived: the Anthropic reviewer reported on every run; the OpenAI reviewer reported on drafts 1 to 3 (it declined the first run for lack of the archive in scope and errored from draft 4 onward); the Google reviewer reported from draft 4 onward (out of scope on the first run, quota-exhausted on drafts 1 to 3).
```

The per-family attributions are now all correct (I checked RT-001/002/003/005/006/007/008 reviewer tables individually). Two other claims in the same sentence are not.

"Once per draft" is false: `review9-tool/` holds seven reports for six drafts, because the first run was a second pass at the same draft with the archive out of scope —

`docs/archive/red-team/review9-tool/RT-001-report-panel-incomplete.md:3-5`

```
**PANEL_INCOMPLETE** — only 1 model family produced a usable review; 2 required. Anything found below is still worth reading, but this is not a verdict.

1 files reviewed. 1 of 2 required model families produced a usable review (anthropic).
```

— a run that reviewed one file (the report alone) and is not a draft in the "drafts 1 to 6" sequence that RT-002…RT-008 cover.

"With every run's report archived" is unsupported: the archive numbering runs RT-001, -002, -003, -005, -006, -007, -008, with no RT-004. RT-008 flagged this and asked for it to be stated either way; draft 7 instead asserts the opposite. In a disclosure paragraph this is the sentence a referee checks first.

Fix: "…by a cross-model review tool run seven times, once on each of drafts 1 to 6 plus one earlier run on draft 1 that had the archive out of scope; every run's report is archived except RT-004, whose number is unused/whose report was not retained [say which]."


### 5. P3 — the 0.975 fit-time-vector number in §4.1 is computed on three instances, and the report gives it to three decimals with no n

`docs/report/technical-report.md:103-103`  ·  found by anthropic alone

**claude-code/F-7** (P3)

`docs/report/technical-report.md:103`

```
In one reviewer's run, with the confounder absent and on the instances where the event did change the support, a per-channel vector fixed at fit time, which never saw the scored episode or the event, scored 0.975 against 0.774 for the interventional arm and 0.845 for the comparator in the same cell. That number is single-model and was not reproduced; what all three reported is that the event usually changes nothing.
```

The three figures are exact, and they come from a three-instance subgroup:

`docs/archive/red-team/review5-claude-opus/schange_split.output.txt:4-7`

```
cell      conf     group           n   AUC(l)  AUC(q@500)  AUC(ibd@500)
tau=0     present  S CHANGED       3    0.814       0.643         0.801
tau=0     present  S unchanged     7    0.837       0.702         0.756
tau=0     absent   S CHANGED       3    0.975       0.845         0.774
```

The report already says the number is single-model and unreproduced, but "on the instances where the event did change the support" hides that this is n = 3 of 10, and the neighbouring τ = 2 row (n = 4) gives 0.969 / 0.831 / 0.882, where the interventional arm is *not* beaten by the comparator. A referee who pulls the file will see a three-instance subgroup quoted to three decimals in support of a design-level claim.

Fix: "…on the three instances of ten where the event did change the support, scored 0.975 against 0.774 … (the corresponding delay-2 subgroup, four instances, gives 0.969 against 0.882)".


## Claims this tool could not tie to the code

Shown, not deleted. Each one may be a real problem the reviewer described imprecisely, or a
claim with nothing behind it — the reason says which is more likely. Judge them yourself.

- **claude-code/F-1** (P1) — the quoted text does not appear in that file
  - claimed: §4.4's displayed population limit inserts a ρ_u^τ factor that two of the three derivations contradict, and the third's own numerical check refutes it for the predictor class the report names
  - cited: `docs/report/technical-report.md:153-157`
