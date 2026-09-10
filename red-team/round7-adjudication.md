# Round 7 adjudication (prose novelty re-check, 8 September 2026)

Inputs: `review7-codex/verdict.md`, `review7-gemini/verdict.md`, `review7-claude-opus/verdict.md` (reasoning only; all three read Liu, Cheng & Bogdan, arXiv:2603.18257 v2 in full; Codex and Gemini also checked the active fault-diagnosis literature). Author adjudicates, does not review.

## 1. Novelty scores (roadmap scale 1 to 5)

| Candidate claim | Codex | Gemini | Claude | Adjudicated |
|---|---|---|---|---|
| a. Attribution only, online, 5 percent probe budget | 3 | 2.0 | 2 | **2 to 3**: an online, low-duty-cycle extension of IBD; the identification principle (randomising the action breaks the confounding path) and the confounded-distractor result are IBD's (Prop. 3.3, Tables 2 and 3), and IBD's §3.2 already admits any confounder-independent probe distribution. Not a method paper. |
| b. Negative adaptation result alone | 1 | 1.5 | 1 | **1**: the textbook passive fault-detection condition (active input design is needed only when normal closed-loop data are not diagnostic; Heirung & Mesbah 2019, Willsky 1976, Basseville & Nikiforov 1993). Two of the reported numbers are products of the event construction. Not publishable alone. |
| c. Combined benchmark-and-findings paper | 3 | 3.2 | 2.5 (3 if both endpoints share one confounding regime) | **3, conditional**: publishable as a benchmark-and-findings contribution (TMLR, CoLLAs, a NeurIPS evaluations track) only after the event is repaired by topology, both endpoints are measured under a common regime, and the conclusion is stated conditionally. |
| d. Option C plant: confounder reaches controllable channels | 4 (question only, no evidence) | 3.8 | 3.5 | **3.5 to 4**: the only candidate all three call unoccupied. IBD excludes it by assumption and names policy-dependent distractors as future work; active fault diagnosis discriminates among explicit fault models rather than discovering an action-reachability mask under a latent common cause. No evidence exists for it yet. |

## 2. Recommendations

Codex: **B**, one boxed execution round, the negative result never headlined as universal; C as a separately preregistered follow-on. Gemini: **B** with strict scope boxing; A rejected because it would publish on a benchmark with admitted fatal defects. Claude: **A scoped down** (a short paper claiming the interventional premium is a property of the confounding, not of the intervention), with a cheap middle path: derive option C's population limit on paper first and switch to C if the passive monitor is genuinely non-identifiable there.

Three of three agree on: (i) the negative result cannot be a headline; (ii) "interventions do not buy adaptation" is over-generalised and must read "when the controllable channels are unconfounded and natural excitation is abundant"; (iii) the frozen version 6 cannot support a submission as it stands; (iv) the decisive test for option C is an **analytic identifiability derivation** on the confounded-body plant, which costs nothing to build (Claude's middle path; Codex's and Gemini's stated flip-to-C conditions are the same derivation).

## 3. Disputes with the round-6 adjudication, accepted

- **Not a dissociation as stated** (Claude, echoed by Codex and Gemini): attribution was measured full-channel with the confounder present; adaptation on the pre-event support where the streams are identical across conditions. Two variables changed at once. The sentence "interventions buy attribution, not adaptation" is withdrawn as a finding and kept only as a hypothesis for a common-regime design.
- **Floor at τ = 0 is "undetermined", not "fails"** (Claude): the interval estimator was never specified.
- **The comparator's win was flattered by CL-4** (Gemini): the lost channel was the dominant body component by construction; "not a tuning matter" stands, but "easy for any second-moment detector on this event" is the honest wording.
- **GM6-06 partly reinstated** (Gemini): charging the prefix is a deliberate cost decision, but the resulting test design does make the interventional arm sample-starved at the event; Codex's steady-state co-reporting remains the fix.
- **§7 wording** (Codex): roadmap v4.7 K4 does claim the attribution half; what failed is the changing-boundary superiority claim, not the attribution claim.
- **"Reproducible" means three implementations of one spec on one generator**, not external validity (Claude).

## 4. Adjudicated direction for D-12

A as worded is rejected (three of three: it ships the lowest-scoring claim on a defective benchmark). B and C are not alternatives but a sequence: the derivation that decides C is zero-build prose and should precede any freeze. Recommendation to Daniel: **D-12 = "derive, then choose"**: (1) a cross-model prose round on the confounded-body plant's identifiability (passive information sets versus sign-randomised probing, population limit, linear-Gaussian, one page); (2) if passive is non-identifiable across a non-knife-edge range and probing identifies, the next freeze is C with attribution and adaptation as two named endpoints under one confounding regime; otherwise B boxed to one execution round with the conditional (c) claim; (3) if either fails its single round, A as a narrow technical report. Daniel decides; see `decisions-required.md`.
