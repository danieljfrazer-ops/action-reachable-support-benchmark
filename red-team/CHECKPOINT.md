# CHECKPOINT — 10 September 2026 (D-13 = A chosen; technical report draft 8 final candidate; publication pending Daniel's confirmation)

Read this first when resuming. The README index and `readiness-protocol.md` round log carry the history.

## What this folder is
A red team of the original research roadmap (`../persistent-adaptive-ai-research-roadmap.html`) that grew, over six cross-model rounds, into a re-aimed research plan plus the executable infrastructure needed to test whether its central experiment can work. Nothing here is the research product. No paper exists. Stage 0A has not started.

## Where the science stands (plain terms)
- Original plan: not novel as written. Re-aimed plan: a benchmark for "which of my sensors do my actions actually control, when a hidden cause confounds me and my body changes".
- Two findings are reproducible, three models each, rounds 5 and 6: **interventions buy attribution** (probing removes the confounded false support a passive monitor shows, about +0.2 AUC on the full channel set) and **interventions do not buy adaptation** (a passive covariance monitor equals or beats probing at tracking loss of a controlled channel).
- The claim the programme set out to confirm (interventional tracking of a changing controllable boundary under confounding) is false as posed on this generator. D-11.1a, the author's re-posing, could not see the confounder by construction; round 6 found it in one round.
- Round 8 (prose derivation, three models): passive identifiability under a body confounder is lost only on a knife-edge; the no-latent model class fails on an open set; the confuser dissociation is sign-fixed; option C is a 3 with the highest cost. No path above novelty 3 survived eight rounds.
- Round 7 (prose, three models) answered the prior-art question: the attribution result is IBD's principle in an online form (2 to 3); the negative adaptation result alone is textbook fault-detection (1); the combined benchmark paper is a 3 only after repair; the confounded-body plant (option C) is the only unoccupied question (3.5 to 4) and can be tested by a one-page identifiability derivation before anything is built. Adjudicated direction: derive, then choose C or B, else A. `round7-adjudication.md`; D-12 in `decisions-required.md`.
- Laptop: never the constraint.

## Frozen and in review
- Frozen version 6, hash `38d161e762a3de76`, reviewed by all three in round 6; **no repair until D-12**. After round 6 closed, `decisions-required.md` (in the manifest) gained D-12 and then D-13, so `freeze.py` now prints `1fcd1c5784a78fda`; only that file differs from version 6. The stale Python 3.14 `.venv` inside the gate directory (not a manifest file) was deleted on 9 Sep before publication. Gate: 66 tests, 47/47 mutants, exit 0; three reviewer mutants survive and are recorded for the next version.
- Round 7 prompt: end of `readiness-protocol.md`. Fresh Claude (Opus) writes `review7-claude-opus/verdict.md`; Daniel gives the identical prompt to Codex (`review7-codex/`) and Gemini (`review7-gemini/`).
- The confirmation-seed secret is at a file held privately by the author outside this repository; commitment in `executable-proofs/gate/confirmation_seeds.py`. Never derive before constants freeze.

## Technical report (D-13, option A)
- `docs/report/technical-report.md` (canonical), `.pdf`, `file-map.md`, `publication-plan.md`, `build_report.py`. Reviewed in round 9 (`review9-claude-opus/`, `review9-tool/`). Not published; publication steps each need Daniel's yes (plan in `docs/report/publication-plan.md`). Pending from Daniel: AI-detector pass permission; author line; licences; repository name; arXiv endorser; archive contents.

## How to resume (in order)
1. Verify: `cd executable-proofs/gate && python3 run_gate.py` (Python 3.12, numpy 2.4.4), expect exit 0; `python3 ../../freeze.py` prints the hash of version 6 plus the current `decisions-required.md` (a manifest file that carries the decision log; `1fcd1c5784a78fda` after D-13 was added on 9 Sep). Every other manifest file is byte-identical to version 6 `38d161e762a3de76`; if that ever stops being true it is a process breach to record.
2. Round 8 done (`round8-adjudication.md`): the identifiability premise for option C failed cross-model; C's novelty is 3, the same as B; no path above 3 survived. D-13 (`decisions-required.md`): A technical report recommended, B available, not C. Wait for Daniel. Under A: write the report from rounds 1 to 8; nothing else is built. Under B: apply the round-6 safe corrections, repair the event by topology, freeze version 7, one execution round, adjudicate.

## Rules that must survive
- No repair to a frozen version while any reviewer is working on it.
- No design change without a cross-model round; single-model simulations are unverified until reproduced.
- Author adjudicates, does not review; fresh-context agents on a different model review.
- The gate's exit code, not prose, is the readiness criterion.
- Before adopting any re-posed primary, check on the generator that the treatment can reach the channels it scores (the round-6 lesson).
