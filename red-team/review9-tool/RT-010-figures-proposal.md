# Red-team review — RT-20260910-010

**PANEL_INCOMPLETE** — only 1 model family produced a usable review; 2 required. Anything found below is still worth reading, but this is not a verdict.

2 files reviewed. 1 of 2 required model families produced a usable review (anthropic).
Nothing under review changed while they ran.

## Worth knowing

- codex did not count towards diversity — did not produce a review (error)

## Who reviewed

| Reviewer | Model that actually ran | Family | Counts | Status | Time | Kept |
| --- | --- | --- | --- | --- | --- | --- |
| claude-code | `claude-opus-5` (envelope) | anthropic | yes | ok | 222s | 9 |
| codex | `gpt-5.6-sol` (session-log) | openai | **no** | error — Reading additional input from stdin... | 7s | — |

## What they found

### 1. BLOCKING — Candidate 1's plant diagram omits the policy feedback edge and the action noise, i.e. exactly the two structures the round-8 result turns on

`docs/report/figures-proposal.md:7-11`  ·  found by anthropic alone

**claude-code/F-1** (P1, blocking)

`docs/report/figures-proposal.md:7`

```
A small directed graph: context u → actions a and u → confounded distractors x; actions a → body b → downstream d; world w and padding with no parents; observations o read every latent plus noise; the confirmatory event drawn as the removal of one a → b edge; the option-C variant drawn as a dashed extra edge u → b.
```

The specified edge set gives `a` exactly one parent, `u`. The plant has two more:

`docs/report/technical-report.md:147`

```
  u_t = ρ_u u_{t−1} + ε^u_t,  a_t = W_o o_t + W_u u_t + ε^a_t,  b_{t+1} = A_b b_t + B a_{t−τ} + G_b u_t + ε^b_t,
```

`o → a` (feedback, `W_o`) and the independent action noise `ε^a`. Both are load-bearing for the report's only theoretical result: Section 4.4's first conclusion is that non-identifiability is a knife-edge *because* `ε^a` "acts as an instrument" (`technical-report.md:151`), and Section 4.2's finding that the covariance score is not blind before the event is attributed to the closed loop (`technical-report.md:122`, "because the closed loop induces action-innovation covariance the null model does not account for"). A reader given the proposed diagram sees an open-loop plant with a single exogenous driver of actions and cannot follow either argument; worse, the diagram positively asserts an instrument-free structure, from which the round-8 conclusion does not follow.

Fix: the diagram must show (a) `o → a` as a feedback edge, visually distinguished from forward edges, (b) `ε^a` as an explicit exogenous input to `a` labelled as the instrument, (c) `u → x` reaching **half** the distractor block (`technical-report.md:63`, "Half the distractors are children of u"), not all of it, and (d) the delay τ annotated on `a → b` only. It must *not* draw padding as latents: the report has "four padding channels" at the observation layer, not four parentless latents.

**claude-code/F-9** (P3)

`docs/report/figures-proposal.md:7`

```
Rendered as inline SVG, one column wide.
```

Two failure modes. Inline SVG inside a Markdown document with a YAML front matter block (`technical-report.md:1-6`, so pandoc is the likely path) does not survive a LaTeX/PDF route without a rasteriser, and the proposal specifies no fallback or alt text. Second and more serious for this particular report: the archive is already the weak point — `technical-report.md:55` records "no row is recomputable as it stands" and `technical-report.md:210` that "the archive as published has not been run from a clean checkout." Hand-drawn SVG pasted into the document adds a fifth artefact with no provenance, produced by no committed script, absent from "A file map from each table in this report to the archived input" (`technical-report.md:210`).

Fix: require every added figure to be emitted by a committed script from an archived input file, extend the file map to cover figures as well as tables, and commit the source (`.svg` plus the script) rather than pasting markup. For the plant diagram, which is hand-authored rather than data-derived, the equivalent is to commit the graph source (DOT or TikZ) and note in the file map which contract version it was checked against.

**claude-code/F-2** (P2)

`docs/report/figures-proposal.md:11`

```
Cost: about a third of a page. Risk: none of the numbers depend on it, so an error in the diagram would be an error of exposition, not evidence; it must match contract v3.9 §B exactly (block order b, d, w, x; u → x only in the frozen plant; actions delayed by τ).
```

Three problems. First, "Risk: none" is false: the proposal's own Candidate 1 rationale (line 9) makes the diagram the reader's evidence for why the third error was zero-by-construction, and F1 shows a wrong diagram breaks the round-8 argument. It is evidence, and it should be reviewed as such.

Second, "u → x only in the frozen plant" contradicts line 7 of the same proposal, which draws `u → a`. As written, an implementer told to match "u → x only" will drop the confounder's path into the policy — the path that creates the action-distractor correlation the certification requires (`technical-report.md:65`, "a confounding witness (maximum action-distractor correlation at least 0.4)"). Say instead: *u's only path to the observation layer is through the confounded half of x; u also enters the policy.*

Third, "contract v3.9 §B" and "the option-C variant" are unresolvable from the report. The report mentions the contract only as an archive artefact (`technical-report.md:210`, "the contract through version 3.9") and never letters D-13's three options (`technical-report.md:208`). A caption or a review criterion that cites §B or "option C" cannot be checked by any reader of the report. Fix: state the criterion in the report's own terms — "the dashed edge is the body-confounded plant of Section 4.4, `G_b`" — and cite the archive file map, not an unnumbered section.


### 2. P2 — Candidate 2's set diagram is wrong for half the round-6 cells

`docs/report/figures-proposal.md:17-17`  ·  found by anthropic alone

**claude-code/F-3** (P2)

`docs/report/figures-proposal.md:17`

```
Two nested sets over the observation channels of one instance: the set the round-6 primary scores (the pre-event support: body and downstream channels) and the set the confounder reaches (the confounded half of the distractors). They are disjoint. The event removes one channel from the first set.
```

"Body and downstream channels" is the delay-0 case only:

`docs/report/technical-report.md:120`

```
note that the delay-2 cells score a different estimand from the delay-0 cells, since with a support horizon of three steps and a two-step delay no propagation hop survives, so the pre-event support there is exactly the four body channels on every draw and contains no downstream channel
```

A single figure asserting one scored set erases the report's own warning that delay-0 and delay-2 score *different estimands* — the warning that makes the comparator's 1.000 at delay 2 (`technical-report.md:114`) uninterpretable as a win. It would then be reproduced in a caption right next to Table 3, whose two rows are precisely those two estimands.

Also, the proposed caption "present and absent streams coincide on the scored set" is true but invites the inference that the benefit column must be exactly 0.000; Table 3 shows −0.017 at delay 0, which arrives through the comparator's fit (`technical-report.md:118`), not through the scored streams.

Fix: keep the drop recommendation. If it is ever added, draw two panels (delay 0: b∪d; delay 2: b alone) and caption the −0.017 as a fit-path artefact, not a stream difference.


### 3. P2 — Candidate 3 would plot the static loading vector "below" chance, which is the opposite of what the report concluded about it

`docs/report/figures-proposal.md:25-25`  ·  found by anthropic alone

**claude-code/F-4** (P2)

`docs/report/figures-proposal.md:25`

```
For each of the four family-L cells and both arms, a dot for the confounder-present AUC and a dot for the confounder-absent AUC, joined by a line, with the channel-constant control at 0.5 and the static vector below it. The picture would show the interventional arm's present and absent dots coinciding exactly and the comparator's sitting above them.
```

Plotting the static vector as a low dot reads as "the trivial event-blind control fails." The report says the opposite:

`docs/report/technical-report.md:122`

```
The lost channel is, by the construction that guarantees the event changes something, the dominant body component of actuator 0, typically the strongest pre-event channel; a static loading vector therefore scores below chance, and its negation, an event-blind and probe-free statistic, scores 0.80 at delay 2 against the interventional arm's 0.687.
```

At delay 2 the *reflection* of that low dot is 0.80, beating the probed arm's 0.687 — one of the report's sharpest self-criticisms. A dot at 0.200 with no reflection shown converts a damning finding into a reassuring one.

Two further defects in the same sentence. "Four family-L cells" does not match Table 3, which reports two rows collapsing distractor count (`technical-report.md:113-114`); four dots would imply four distinct measurements where the report gives two values. And "the confounder-present AUC and the confounder-absent AUC" is ambiguous between two different quantities: on the round-6 *primary* the probed arm's present and absent coincide exactly, but on the full-channel *secondary* that Section 5's headline rests on they do not — 0.851 vs 0.863 and 0.753 vs 0.751 (`technical-report.md:167`). A chart showing exact coincidence, placed near Section 5, would contradict Section 5's own numbers.

Fix: keep the drop. The stated reason (interval estimator) is sound but secondary; the primary reason is that the axis is not one quantity. If overruled: label the axis "pre-event-support AUC", show the static vector *and* its reflection with an arrow, restrict to the two distinct cells, and add the family-N reversal (`technical-report.md:120`) or the chart asserts a comparator win the report declines to assert.


### 4. P2 — Candidate 6's four cell values are listed in an order that, read row-major from its own row/column definition, states a prediction the report never made

`docs/report/figures-proposal.md:47-49`  ·  found by anthropic alone

**claude-code/F-5** (P2)

`docs/report/figures-proposal.md:47`

```
A 2 × 2 grid: rows = plant (confounder reaches the body / does not), columns = arm (passive / probed), cells = predicted response to a support-preserving confounder change (false loss / blind / invariant / invariant). This is the one sign-fixed prediction and the proposed primary of any future round.
```

Rows are plants and columns are arms, so the natural row-major reading of `(false loss / blind / invariant / invariant)` is: body-confounded plant → passive = false loss, **probed = blind**; other plant → passive = invariant, probed = invariant. That is wrong in three of four cells. The report says:

`docs/report/technical-report.md:163`

```
the passive arm reports false loss of support on a plant where the confounder reaches the body and is exactly blind on one where it does not, while the probe arm is invariant in both
```

The listed order is column-major. A table built from this specification without going back to Section 4.4 will publish a prediction that the probe arm is blind under body confounding — the exact reverse of Section 4.4's fourth conclusion (`technical-report.md:161`, the contrast "is unchanged under a change in G_b"). Fix: write the cells as explicit pairs — `(body-confounded, passive) = false loss; (body-confounded, probed) = invariant; (not body-confounded, passive) = blind; (not body-confounded, probed) = invariant` — and have the table's row/column headers name the plant by its coupling (`G_b ≠ 0` / `G_b = 0`).

**claude-code/F-6** (P2)

`docs/report/figures-proposal.md:49`

```
What it shows: the prediction table that all three derivations produced, compressed. It is a table, not a chart, and belongs in Section 4.4 as Table 5 rather than as a figure.
```

"All three derivations produced" it is not what the report records. Agreement was manufactured in adjudication by a single-model step the report itself flags as the protocol's weak point:

`docs/report/technical-report.md:187`

```
The fourth never needed a build: it was a claim about a population limit, and three derivations settled it, after being reconciled, since one initially concluded the opposite.
```

and `technical-report.md:149` notes Gemini's stated theorem concerned a different object. Publishing a unanimity claim in a caption, in a report whose Section 6 confesses two adjudication errors, is the one place a referee will push hardest.

Separately, the table must carry a visible boundary: `technical-report.md:163` states "The sign of adaptation after real actuator loss under body confounding was not settled," with one system predicting each way and one declining. A 2 × 2 about a *support-preserving confounder change*, placed as "the proposed primary of any future round," will be read as covering actuator loss too. Fix the caption to say: derived by three systems and **reconciled in adjudication, one initially concluding the opposite**; predictions cover support-preserving confounder changes only; the actuator-loss cells are undetermined and are deliberately absent.


### 5. P2 — The summary's justification for adding no charts is factually wrong about the perturbation set, which is the one quantity no table carries

`docs/report/figures-proposal.md:55-55`  ·  found by anthropic alone

**claude-code/F-7** (P2)

`docs/report/figures-proposal.md:55`

```
Add Candidate 1 (plant diagram, inline SVG) and Candidate 6 (a 2 × 2 prediction table). Do not add charts of the results: the numbers are few, the tables already carry them with their caveats, and a chart would need an interval estimator the contract never fixed.
```

"The tables already carry them" is false for the perturbation set. Table 2 gives base cells and one thirty-distractor row; the perturbation-set result exists only as prose:

`docs/report/technical-report.md:99`

```
The confounding benefit cleared the pre-declared margin of 0.10 in every base cell, but not on the perturbation set, where the aggregate lower bound was 0.090 and individual configurations ran from −0.015 to +0.25.
```

That range — spanning zero — is the single most important qualification on the surviving attribution claim, and Section 5 restates it parenthetically (`technical-report.md:167`, "the benefit did not clear its margin on the perturbation set") with no distribution behind it. A one-column strip plot of per-configuration benefit against the 0.10 margin line adds information genuinely absent from all four tables, and needs **no** interval estimator, because it plots point estimates per configuration, so the proposal's own objection does not apply to it.

It must be captioned with the two things that make it non-comparable to Table 3: these are round-5 numbers, taken on a statistic the same round found defective and against a baseline that failed the competence floor (`technical-report.md:167`, "so that half is inadmissible under the contract's own rule"), and round 5's implementations did not share trajectories (`technical-report.md:97`). It must not show a mean, a fitted trend, or any round-6 point on the same axis. If the author judges that plotting inadmissible numbers gives them undue prominence, that is a defensible reason to drop it — but it is a different reason from the one the proposal gives, and the proposal should say so rather than assert the tables already carry it.


### 6. P2 — The proposal never considers Section 6, and a provenance table there would expose a live contradiction in the report

`docs/report/technical-report.md:177-177`  ·  found by anthropic alone

**claude-code/F-8** (P2)

`docs/report/technical-report.md:177`

```
The execution rounds and the derivation round exposed four design errors of mine, each of which changed the benchmark's estimand or its verdict; the review of this report exposed two adjudication errors.
```

`docs/report/technical-report.md:189`

```
The second is that the round-6 adjudication narrowed the interventional arm's secondary full-channel AUC to 0.85 to 0.87, a delay-0 read of outputs that also contain 0.75 at delay 2; the range stood in the archive for two days and was found by the review of this report, not by any round (erratum of 10 September 2026 appended to the round-6 tally).
```

Line 177 attributes *both* adjudication errors to the review of this report; line 189 attributes only the second to it, the first being the rejection of R4-GM-02, which was named by a round-4 reviewer and established in round 5 (`technical-report.md:179`). The report's central claim is about which mechanism caught which error, so this is not a wording slip — it inflates the self-audit's yield and understates the protocol's.

Section 6 is the load-bearing section of a negative-result report and the proposal offers nothing for it. A referee will expect a compact table with one row per error and columns: *what it was · version it entered · round that named it · round that established it · whether adjudication rejected it first · what it cost*. Six rows, quarter page, and it is the only candidate on the table that would have caught the 177/189 contradiction before publication. It must include the two adjudication rows with an explicit "caught by: no round — single-model adjudication step" cell, since `technical-report.md:189` makes that the point.

