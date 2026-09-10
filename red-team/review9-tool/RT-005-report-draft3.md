# Red-team review — RT-20260909-005

**FAIL** — 1 blocking problem with checked evidence.

305 files reviewed. 2 of 2 required model families produced a usable review (anthropic, openai).
Nothing under review changed while they ran.

## Worth knowing

- 2 directories were skipped by name and never reviewed: docs/archive/red-team/.DS_Store, docs/archive/red-team/executable-proofs/.DS_Store
- antigravity did not count towards diversity — did not produce a review (error)

## Who reviewed

| Reviewer | Model that actually ran | Family | Counts | Status | Time | Kept |
| --- | --- | --- | --- | --- | --- | --- |
| claude-code | `claude-opus-5` (envelope) | anthropic | yes | ok | 617s | 8 |
| codex | `gpt-5.6-sol` (session-log) | openai | yes | ok | 205s | 7 |
| antigravity | `gemini-3.1-pro-high` (pinned-slug) | google | **no** | error — error: Individual quota reached. Please upgrade your subscri | 648s | — |

## What they found

### 1. BLOCKING — §9 claims the report itself was reviewed by three AI reviewers; the archive records that the third model family failed to produce a review on all three attempts

`docs/report/technical-report.md:203-203`  ·  found by anthropic alone

**claude-code/F-1** (P1, blocking)

`docs/report/technical-report.md:203`

```
I am responsible for the four errors in Section 6. This report was drafted by the same Claude session from the archived adjudications, reviewed by three AI reviewers against the archive, and revised and edited by me.
```

The round-9 prompt did ask for three (`readiness-protocol.md:123`):

```
### Round 9 — review of the technical report (9 September 2026; identical prompt for Codex, Gemini, and a fresh-context Claude on Opus)
```

But the archive contains no `review9-codex/` and no `review9-gemini/`. The only round-9 artefacts are `review9-claude-opus/report-review.md` and three tool runs, and in every one of those the Google-family reviewer errored out:

`docs/archive/red-team/review9-tool/RT-003-report-draft2.md:20`

```
| antigravity | `gemini-3.1-pro-high` (pinned-slug) | google | **no** | error — error: Individual quota reached. Please upgrade your subscri | 556s | — |
```

`RT-002-report-draft1.md:20` records the identical failure for draft 1, and `RT-001-report-panel-incomplete.md:3` is worse still — `PANEL_INCOMPLETE — only 1 model family produced a usable review; 2 required`, with both non-Anthropic reviewers reporting they could not fact-check because `docs/archive/red-team/` was not in scope. So "reviewed by three AI reviewers **against the archive**" is false twice over: two families, not three, and the first pass could not read the archive at all.

This is the one claim in the report a hostile referee is most likely to check, because §2 makes cross-model independence the whole warrant, and §2 already volunteers a weaker version of this admission ("a weakness of the design as run and is stated here for that reason"). Draft 3 applies that standard everywhere except to its own review.

Fix: `"…reviewed against the archive by a fresh-context Claude Opus agent and by a cross-model review tool in which the Anthropic and OpenAI reviewers reported and the Google reviewer failed on quota on each of three runs, so the report's own review is two model families, one of them the family that drafted it."`

---


### 2. P2 — The report still misstates the readiness protocol as an exit-code criterion

`docs/report/technical-report.md:34-37`  ·  **found by 2 families: anthropic, openai**

**codex/F-1** (P2)

`docs/report/technical-report.md:34-37`

```
- **Freeze.** A version is a listed set of files with one SHA-256 hash over their concatenation. No file in a frozen version is edited while any reviewer is working on it. Repairs land only after all reviewers have reported, and produce a new version. Rounds 1 to 6 reviewed frozen versions; rounds 7 and 8 reviewed the archived record without a new freeze.
- **Three model families, one prompt.** Each round the identical prompt went to Codex (OpenAI), Gemini (Google) and a fresh-context Claude agent (Anthropic), Opus in every round whose adjudication names the model. Round 2 used a fourth Claude-family reviewer on a different model (Fable, the model that ran round 0); the round-3 prompt asked for a different Claude model, although the round-3 adjudication records Opus. The Claude reviewer was started without memory of previous rounds each time; the Codex and Gemini sessions were run by me and were not certified fresh. Reviewers could read each other's reports only after writing their own. In execution rounds each reviewer implemented both estimators from the specifications alone.
- **Adjudication separate from review.** The roadmap, contract, specifications, prompts and adjudications were drafted by one Claude session acting as my agent; I set the question, made every design decision and estimand choice from that session's recommendations, and directed each step. The adjudicating session never reviewed or implemented. It shares a model family with one of the three reviewers, which is a weakness of the design as run and is stated here for that reason.
- **Executable exit criteria.** A gate directory holds assertion tests and mutants; the criterion for a version's readiness was the gate's exit code, not prose. A normative item without a test identifier was not counted as implemented. The full readiness protocol also required an independent black-box acceptance suite, a hand-computed reference case and a runtime pilot; none of the three was done.
```

The archived protocol defines readiness as six conjunctive conditions, including the three omitted activities and cross-model convergence—not as the gate’s exit code alone. The paragraph contradicts itself by first calling the exit code “the criterion” and then acknowledging additional required criteria. This makes the protocol sound more executable and complete than it was, even though Section 7 later correctly says no version was readiness-certified.

Replace the first two sentences under “Executable exit criteria” with a faithful list of the six conditions and state that only the gate and convergence components were exercised.

**claude-code/F-3** (P2)

`docs/report/technical-report.md:36`

```
- **Adjudication separate from review.** The roadmap, contract, specifications, prompts and adjudications were drafted by one Claude session acting as my agent; I set the question, made every design decision and estimand choice from that session's recommendations, and directed each step. The adjudicating session never reviewed or implemented.
```

`docs/report/technical-report.md:203`

```
The roadmap, contract, specifications, simulator, gate, round prompts and adjudications were drafted by a Claude (Anthropic) session acting as my agent;
```

Both are contradicted by the report's own §4.2 and by the archive:

`docs/report/technical-report.md:107`

```
Fresh-context Claude agents redrafted both specifications against the new contract, and version 6 was frozen.
```

`docs/archive/red-team/readiness-protocol.md:74`

```
> Review frozen version `442cc4b7da691ca0` of `docs/archive/red-team/` (`freeze-manifest.txt`; verify with `python3 freeze.py`). Normative: `roadmap-v4.md` + amendments v4.1–v4.7, `stage-0a-contract-v3.5.md`, `interface-spec-v3.md`, `sequential-ibd-spec.md` (draft 3), `comparator-spec.md` (new), `confirmation-design.csv`, `executable-proofs/gate/` (run `python3 run_gate.py` under Python 3.12 / numpy 2.4.4; exit code is the criterion). Superseded files are history. Both specs were drafted by fresh-context Claude agents and have not been seen by any other model.
```

`readiness-protocol.md:52` says the same of the first IBD spec ("Draft by a fresh-context Opus agent"). The estimator specifications — the two documents from which every round-5 and round-6 implementation was built — were written by sessions with no memory of the adjudications, which is a *stronger* independence property than the report claims. As drafted, §2 and §9 concentrate authorship in one session that the archive says did not hold it, and §4.2 then says the opposite forty lines earlier. A referee checking the disclosure against the archive finds the report wrong about its own process in the section whose job is to be right about it.

Fix, §2 and §9: `"…the roadmap, contract, interface specification, prompts and adjudications were drafted by one Claude session acting as my agent; the two estimator specifications were drafted, and after round 5 redrafted, by separate fresh-context Claude agents that had not seen the adjudications."`

---


### 3. P2 — Table 1's caption now asserts that version 6 is reconstructible from the archive; it is not, and draft 3 deleted draft 2's correct disclosure that `freeze.py` reproduces none of the tabled hashes

`docs/report/technical-report.md:55-55`  ·  **found by 2 families: anthropic, openai**

**claude-code/F-2** (P2)

`docs/report/technical-report.md:55`

```
No per-version snapshot was retained: files were superseded in place, so rows 1 to 5 are assertions from the round log, and only version 6 is reconstructible from the archive, which today hashes to version 6 plus decision entries added after round 6.
```

`decisions-required.md` is a manifest file (`freeze-manifest.txt:4`), and it was overwritten in place twice after round 6 closed. The archive says so itself:

`docs/archive/red-team/CHECKPOINT.md:22`

```
1. Verify: `cd executable-proofs/gate && python3 run_gate.py` (Python 3.12, numpy 2.4.4), expect exit 0; `python3 ../../freeze.py` prints the hash of version 6 plus the current `decisions-required.md` (a manifest file that carries the decision log; `1fcd1c5784a78fda` after D-13 was added on 9 Sep). Every other manifest file is byte-identical to version 6 `38d161e762a3de76`; if that ever stops being true it is a process breach to record.
```

"Every **other** manifest file is byte-identical" is precisely the statement that version 6 is *not* reconstructible: the round-6 bytes of `decisions-required.md` exist nowhere in the archive, so `38d161e762a3de76` cannot be recomputed either. Row 6 is in the same position as rows 1 to 5, not a different one.

Concretely, a reader who follows the archive's own verification step gets `1fcd1c5784a78fda`, which matches none of the eight hashes in Table 1, and draft 3 never states that number or warns them. Draft 2's caption did (`RT-003-report-draft2.md:131`: "The archive's `freeze.py` hashes the folder as it currently stands … so it does not reproduce earlier rows"). Removing that sentence and replacing it with a reconstructibility claim is a regression on the one item both draft-2 reviewers agreed on.

Fix: `"…so every row is an assertion from the round log. Running freeze.py today prints 1fcd1c5784a78fda, which reproduces no row in the table: the manifest includes the decision log, which gained D-12 and D-13 after round 6 closed and was overwritten in place. Every other version-6 manifest file is byte-identical to the reviewed version, so row 6 differs from the archive in exactly one file, but no row is recomputable as it stands."`

---

**codex/F-2** (P2)

`docs/report/technical-report.md:55`

```
Table 1. The rounds. Hashes are the first sixteen hex digits of the SHA-256 over each version's manifest in manifest order, as recorded in the archive's round log at the time of the freeze. The manifest and `freeze.py` were introduced as a repair after round 2, so rows 1 and 2 record hashes taken before that convention existed and are not manifest-order digests. No per-version snapshot was retained: files were superseded in place, so rows 1 to 5 are assertions from the round log, and only version 6 is reconstructible from the archive, which today hashes to version 6 plus decision entries added after round 6. A public release should be accompanied by a repository whose commits fix this from that point on. Gate counts are for the version as frozen, not after the repairs the round prompted.
```

Version 6 is not reconstructible from the archive: `decisions-required.md` was part of its manifest and was subsequently changed, while the version-6 bytes of that file were not retained. Knowing that it is the only changed file does not recover its old contents or reproduce `38d161e762a3de76`. Running the current verifier produces `1fcd1c5784a78fda`, not the tabled digest.

Change “only version 6 is reconstructible” to “none of the historical frozen hashes is reproducible from the archive as published; for version 6, the archive records which manifest file changed but does not retain its frozen bytes.” Preserve future freezes as immutable snapshots or per-file checksum manifests.


### 4. P2 — The optional probed comparator is introduced as a mechanism control but its available result is never reported

`docs/report/technical-report.md:69-75`  ·  **found by 2 families: anthropic, openai**

**codex/F-3** (P2)

`docs/report/technical-report.md:69-75`

```
### 3.2 The two estimators

**Sequential IBD.** Every twentieth step the estimator replaces the policy's action with a unit probe on one actuator, sign and actuator drawn in balanced pre-randomised blocks independent of state. For each channel, horizon and actuator it computes a tie-corrected Mann-Whitney rank-sum statistic (Mann and Whitney, 1947) contrasting signed increments after positive probes against those after negative probes over a trailing window of 500 steps, and reports the maximum absolute statistic over horizons and actuators. Its raw statistic never sees a label, a reward or the event time; the calibrated-probability tier, which was never run, would consume a harness-fitted calibrator trained on oracle labels. This is an in-task, budgeted departure from IBD's one-shot two-branch design: there is no baseline branch and no dedicated probing policy, and none of IBD's guarantees are inherited.

**Delay-aware passive comparator.** A frozen linear one-step predictor of the observation from the previous observation, the current action and two action lags, ridge-fitted on fault-free episodes of the same instance with standardised features. Its support baseline is the iterated-prediction sensitivity of each channel to the action over horizons one to three. In version 5 its change statistic was the shift in the mean of standardised innovations over a trailing window, by analogy with a CUSUM on residuals (Page, 1954; Basseville and Nikiforov, 1993). Version 6 replaced that, for reasons given below, with a score-type statistic on the covariance between innovations and lagged actions, whitened by the fit-split action covariance.

A probed variant of the comparator, run on the identical probe-carrying stream, separates having interventions from using them.
```

This promises a control that separates the intervention stream from the estimator mechanism, but the results section never says that arm 3 was optional, reports its limited seed-0 results, or explains why they are excluded. A reader can reasonably infer that the advertised separation was established across the reported experiment when it was not.

Either report the archived arm-3 results with their single-seed scope, or append: “This optional arm was run only on seed 0 of each family-L base cell and is not scored as a reproduced result, so the mechanism-versus-instrument distinction remains untested at the report’s main sample size.”

**claude-code/F-4** (P2)

`docs/report/technical-report.md:75`

```
A probed variant of the comparator, run on the identical probe-carrying stream, separates having interventions from using them.
```

This is the only arm in the report that isolates the mechanism from the instrument — whether the interventional arm's behaviour comes from *having* probes in the stream or from *using* the probe labels. It is stated as a fact of the testbed, in the present tense, in the methods section, and then never appears again: no number in Table 2 or Table 3, no mention in §4, §5, §6 or §7. It was optional in the round-6 prompt and reported separately if at all (`readiness-protocol.md:101`: "arm 3, the probed comparator, is optional and reported separately"), and no round-6 reviewer folder carries an arm-3 result.

Concretely, this weakens §5's second surviving statement. That statement attributes the passive arm's win to natural excitation being diagnostic; the probed comparator is exactly the control that would separate that explanation from "the probes are in the stream either way". A referee who reads §3.2 will look for it in §4.2 and conclude either that it was run and buried, or that the methods section describes apparatus that was never used. This was flagged in `review9-claude-opus/report-review.md:224-226` and not acted on.

Fix: append to line 75 — `"It was optional in the execution rounds and was not scored; the mechanism it controls for is therefore untested, and §5's second statement cannot separate 'probes are unnecessary here' from 'probes are being wasted here'."`

---


### 5. P2 — §4.3's "the one candidate scored above 3" is contradicted by Table 4 on the same page

`docs/report/technical-report.md:143-151`  ·  **found by 2 families: anthropic, openai**

**claude-code/F-5** (P3)

`docs/report/technical-report.md:143`

```
The one candidate scored above 3 was a plant in which the context also drives the body.
```

Table 4, eight lines earlier, shows two candidates scored above 3:

`docs/report/technical-report.md:134`

```
| A combined benchmark-and-findings paper | 3 | 3.2 | 2.5 (3 if both endpoints share one regime) |
```

Gemini scored the combined paper 3.2. The sentence is true of the *adjudicated* band (`round7-adjudication.md:11` adjudicates the combined paper at "3, conditional" and the option-C plant at "3.5 to 4"), but as written it is a claim about the raw scores in the table directly above it, and it is false of them. Flagged in `review9-claude-opus/report-review.md:295`; unfixed.

Fix: `"The one candidate adjudicated above 3 was…"`.

---

**codex/F-5** (P2)

`docs/report/technical-report.md:145-151`

```
Write the body-confounded plant as

  u_t = ρ_u u_{t−1} + ε^u_t,  a_t = W_o o_t + W_u u_t + ε^a_t,  b_{t+1} = A_b b_t + B a_{t−τ} + G_b u_t + ε^b_t,

with u never observed and G_b the new coupling. All three derivations reached the same four conclusions.

First, exact non-identifiability is a knife-edge, not an open set. The observational law of (o, a) at all lags contains the independent action noise ε^a, which acts as an instrument: the covariance between the body and the action has a discontinuity at the causal lag τ that the smooth AR(1) confounder path cannot produce, and it pins B separately from G_b. Exact confusion between an actuator loss and a support-preserving change in G_b requires the action noise to vanish in the affected direction. The premise I had adopted was false.
```

The adjudication records that Codex and Claude stated the full-law knife-edge conclusion directly, while Gemini’s stated theorem concerned only the apparent coefficient of a no-latent estimator; Gemini conceded the full-law limitation only in a remark. “All three derivations reached” erases the distinction between deriving the result and being reconciled to it during adjudication.

Replace it with: “Codex and Claude derived these conclusions directly; Gemini’s theorem addressed the restricted estimator, but its accompanying remark conceded the same knife-edge condition for equality of the full observational law.”


### 6. P2 — §4.4's confuser-dissociation sentence is incoherent in the regime it is meant to describe

`docs/report/technical-report.md:163-169`  ·  **found by 2 families: anthropic, openai**

**claude-code/F-6** (P3)

`docs/report/technical-report.md:163`

```
The one prediction whose sign all three fixed in advance is a confuser dissociation: under a change in G_b, the passive arm reports false loss of support when G_b is nonzero and is exactly blind when it is zero, while the probe arm is invariant in both regimes.
```

"Under a change in G_b … when it is zero" cannot happen: if the event is a change in `G_b`, then `G_b` is not zero. The archive's E2 is broader than a `G_b` change:

`docs/archive/red-team/readiness-protocol.md:116`

```
E2, a confounder-coupling change (G_b, or the policy's W_u, changed; S unchanged);
```

and `round8-adjudication.md:11` states the dissociation over regimes, not over the event: "passive arm reports false loss of support under a confounder change **when the confounder reaches the body**, is exactly blind to it **when it does not**". The `G_b = 0` arm of the dissociation is the case where the confounder-coupling change is in `W_u`, on a plant where the confounder does not reach the body at all. As the report renders it, the single sign-fixed prediction that §8 nominates as the primary of any future round is unimplementable as stated.

Fix: `"…under a confounder-coupling change — in G_b or in the policy's context gain W_u — the passive arm reports false loss of support on a plant where the confounder reaches the body and is exactly blind on one where it does not, while the probe arm is invariant in both."`

---

**codex/F-4** (P2)

`docs/report/technical-report.md:165-169`

```
## 5. What survived

**Sign-randomised probing removes confounded false support that a frozen passive residual monitor shows, online and at a 5 percent probe budget.** About +0.2 AUC on the full channel set in the base cells: measured by three implementations in round 5, where it did not clear its margin on the perturbation set, and by two in round 6. This is a replication of IBD's principle in a sequential setting, not a new result.

**On the linear family studied, a passive delay-aware covariance monitor equals or beats sign-randomised probing at ranking which controlled channel an actuator loss removed.** Measured once by three implementations. The caveats are load-bearing: the confounder did not reach the scored channels, the lost coordinate was chosen by construction to be dominant, the event usually removed one channel, and the ordering reversed on the nonlinear family on five seeds. The result is best read as a diagnosis of the event, and of the value of probes when ordinary closed-loop data are already diagnostic, rather than as a general fact about interventions.
```

The interventional arm scored approximately 0.85–0.87 AUC, not 1.0, so the experiment shows resistance to degradation and better ranking—not that false support was “removed.” The wording converts a continuous ranking improvement into a claim of error elimination.

Replace the heading with: “Sign-randomised probing was not degraded by the shared-cause confounder that reduced the frozen passive monitor’s full-channel AUC by about 0.2 in the base cells.”


### 7. P3 — §4.1 promises three findings and then numbers a fourth as "the third"

`docs/report/technical-report.md:99-103`  ·  **found by 2 families: anthropic, openai**

**claude-code/F-7** (P3)

`docs/report/technical-report.md:99-103`

```
The third finding was worse for the design.
```

Line 99 opens "Three things followed" and enumerates exactly three: the arm was reproducible; the benefit cleared the margin in the base cells; the result was inadmissible because the competence floor failed. Line 101 gives the cause of the third. Line 103 then labels the CL-4 generator defect — which is not one of the three — "the third finding". A reader tracking the enumeration reads it as a restatement of the inadmissibility item and then finds it is about something else. The only reading that works is that "the third finding" refers to the third clause of the section *heading*, three paragraphs and one list earlier. Flagged in `review9-claude-opus/report-review.md:252-254`; unfixed.

Fix: `"A fourth finding, and the worst for the design, came from the same runs."`

---

**codex/F-6** (P3)

`docs/report/technical-report.md:99-103`

```
Three things followed. The interventional arm was reproducible, at 0.80 to 0.85 across distractor levels, delays and a perturbation set over coupling and noise scale, and insensitive to the confounder. The confounding benefit cleared the pre-declared margin of 0.10 in every base cell, but not on the perturbation set, where the aggregate lower bound was 0.090 and individual configurations ran from −0.015 to +0.25. And the result was inadmissible, because the competence floor failed: without confounding the comparator's lower bound was 0.64 to 0.83 against the required 0.85, in every base cell for two reviewers and in ten of twelve cell-offsets for the third.

The cause was identified analytically by Codex and measured by the other two. Under a centred policy, losing an actuator does not shift the mean of the predictor's innovations; it changes their variance and their covariance with the action. The comparator's change statistic was a mean-shift test and therefore could not see the event, and the loading term alone ranked the support at 0.99 without confounding. The baseline was not weak; it was specified with a statistic blind to the change it was meant to detect.

The third finding was worse for the design. The generator did not guarantee that losing actuator 0 removed any observed channel from the support, and on 60 to 70 percent of frozen instances it removed none; all three reviewers found this.
```

The opening paragraph already enumerates three consequences; the event-does-nothing result is therefore a fourth finding, not the third. This makes it unclear whether the causal diagnosis is intended as part of the third item or a separate result.

Change the transition to: “A fourth finding was worse for the design.”


### 8. P2 — The file map still uses context-dependent basenames instead of mechanically resolvable paths

`docs/report/file-map.md:10-13`  ·  found by openai alone

**codex/F-7** (P2)

`docs/report/file-map.md:10-13`

```
| Table 2 (round 5 base cell) | `round5-adjudication-and-tally.md` §1 | `review5-claude-opus/sim_frozen.py`, `sim_frozen.output.txt`; `review5-codex/sim_frozen.py`, `sim_frozen-output.txt`; `review5-gemini/sim_frozen.py`, `sim_frozen.output.txt`, `sim_frozen_results.json` |
| Round-5 perturbation set, floor, 0.975 static vector, 60–70 % no-change | `round5-adjudication-and-tally.md` §1 items 2–5 | `review5-claude-opus/findings.md`, `schange_split.output.txt` (0.975 is this reviewer's) |
| D-11 (six decisions) | `decisions-required.md` (D-11 table); `stage-0a-contract-v3.9.md` §L | |
| Table 3 (round 6 family L) | `round6-adjudication-and-tally.md` §1 | `review6-codex/report.md` (per-cell tables with t intervals), `sim_frozen.results.json`; `review6-gemini/sim_output.txt`; `review6-claude-opus/report.txt`, `results/` |
```

Paths such as `sim_frozen.output.txt`, `schange_split.output.txt`, `sim_frozen.results.json`, and `results/` do not resolve relative to the archive root promised on line 3. Their intended parent directories can only be inferred from punctuation and preceding entries, defeating the file map’s audit purpose and automated checking.

Write every entry as a complete archive-relative path, for example `review5-claude-opus/sim_frozen.output.txt`, `review5-claude-opus/schange_split.output.txt`, `review6-codex/sim_frozen.results.json`, and `review6-claude-opus/results/`.


### 9. P3 — two prose items flagged last round survive verbatim, including the Summary's one hedged sentence

`docs/report/technical-report.md:18-18`  ·  found by anthropic alone

**claude-code/F-8** (P3)

`docs/report/technical-report.md:18`

```
What the numbers showed is not what the programme hoped.
```

Programmes do not hope, and the sentence defers the fact to the next clause. `review9-claude-opus/report-review.md:306` proposed "The numbers did not support the claim the programme was built to test." and it was not taken. This matters more than usual here because it is the hinge sentence of a report whose subject is stating negative results plainly; the rest of the Summary does that and this sentence does not.

`docs/report/technical-report.md:191`

```
The generator is one linear-Gaussian family with a scalar context, plus one nonlinear variant run on five seeds whose result reversed the linear family's ordering.
```

§7 is now a single unbroken paragraph carrying twelve distinct limitations — generator scope, development seeds, external validity, the unrun alarm channel, the AUC lattice, the unspecified interval estimator, the tuned ridge constant, Δ_c's pre-event ranking, the perturbation-set margin, three surviving mutants plus the unregistrable generator mutants, unrepaired round-6 spec defects, and three unmet readiness conditions. Every one of them is load-bearing and several are the report's most creditable disclosures. As one block they will be skimmed; the same content flagged in `review9-claude-opus/report-review.md:304` and unchanged since. Make it a list.

---

## On `file-map.md`

No findings. Every path I sampled resolves — `review5-claude-opus/sim_frozen.hashseed1.txt`, `review5-gemini/sim_frozen_results.json`, `review6-codex/sim_frozen.results.json`, `review6-claude-opus/results/`, `review6-claude-opus/findings.md` R6-OP-04/05/09, `review6-codex/adjudication.md` "Differences resolved" (line 44), `review8-claude-opus/check_algebra.py`, `executable-proofs/gate/gate.output.txt`, `review9-tool/`. The draft-2 finding about the fake `round2-…round6-adjudication-and-tally.md` glob is fixed, and the round-1 reviewer folders and the round-5 non-determinism row are new and correct. Its one remaining gap is the one it inherits from Table 1: no row maps a hash to an immutable input, because none exists (see P2 above).

