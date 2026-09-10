# Publication plan for the technical report (10 September 2026)

Nothing in this plan is executed without Daniel's confirmation at each step marked **[confirm]**.

## What is published

1. **The technical report** (`technical-report.pdf`, canonical source `technical-report.md`), about 7,300 words, six references, one author, eight drafts. Contribution type: technical report of a negative result with reusable artefacts. It is not a peer-reviewed paper and does not claim novelty.
2. **The artefact bundle**: the red-team archive (`docs/archive/red-team/`) as a public repository: every prompt, review, adjudication, frozen manifest and hash, the contract and specifications, the reference generator (families L and N), the metric references, the gate (66 tests, 47 mutants), and the three round-6 implementations with captured output. Excluded: the confirmation-seed secret (it lives outside the folder and stays private), any personal notes, and the two precursor chat transcripts in `docs/` (they are not part of the work).
3. **A short README** for the repository stating what the archive is, how to run the gate, and the licence.

## Where

| Venue | Role | Why | Cost and prerequisites |
|---|---|---|---|
| **GitHub** (public repository) | artefacts | Standard home for code and a review archive; enables the report to cite a stable URL; Zenodo integrates with it for a DOI. | Daniel's GitHub account; repository name chosen after a collision check (the roadmap notes `boundary-bench` is taken); a licence (recommendation: CC BY 4.0 for documents, MIT for code). |
| **Zenodo** | DOI for the report and a versioned snapshot of the repository | Free, immediate, citable, no endorsement needed, accepts negative results and technical reports, mints a DOI per version. | Daniel's Zenodo account (ORCID login works); metadata: title, author, ORCID if any, keywords, licence, "Technical report" type. |
| **arXiv** (cs.LG, cross-list cs.AI or eess.SY) | preprint visibility | Where the IBD paper and the field's readers are; makes the negative result findable by anyone who searches the topic. | arXiv requires endorsement for a first submission in cs.LG from an author without prior arXiv history; Daniel would need an endorser, or to request one through arXiv's endorsement page. arXiv also requires disclosure of AI-generated content in the submission (the report's Section 9 already does this) and, if the PDF was produced from TeX, the TeX source; ours is HTML-to-PDF, so PDF-only is allowed. Moderation may reclassify or hold a technical report; that is acceptable. |
| **OSF Preprints** or **TechRxiv** | fallback preprint | No endorsement barrier; DOI; indexed by Google Scholar. | Account. Use if arXiv endorsement is not obtainable within a week. |

Recommendation: GitHub plus Zenodo first (a DOI within the hour of confirmation), then arXiv once an endorser is found, with the Zenodo DOI cited in the arXiv version. Do not submit to a journal or conference: three reviewers put the ceiling at a benchmark-paper level only after further work, and this report is explicitly the record of stopping before that work.

## How, in order

1. **Review and revise** [done 10 Sep]. Round 9: one fresh-context Claude review (45 items) and seven cross-model tool runs across drafts 1 to 6 (reports in `docs/archive/red-team/review9-tool/`); eight drafts; every number traced to an archive file (`file-map.md`). Draft 8 is the final candidate; the last tool run had one usable family and its checked findings were applied without a further run.
2. **AI-detector pass** [confirm the services before text is sent]. Run the revised text through at least two public detectors (candidates: GPTZero, Sapling, ZeroGPT; free tiers, no account) and record the scores in `detector-log.md`. Purpose: a check that the prose reads as specific technical writing, not a claim about authorship; the report discloses AI assistance regardless of the scores, because the AI role is part of the method. Note: text sent to a detector leaves the machine and may be retained by the service; the text is intended for publication, but this happens before publication, so it needs a yes.
3. **Prepare the repository** [confirm before it is created]. Copy the archive to a clean directory; remove `__pycache__`, the seed secret path references, and the precursor transcripts; add README and LICENSE; run the gate from the clean copy and record the exit code; record that `freeze.py` reproduces none of the historical hashes (the decision log in the manifest was overwritten after round 6 and no per-version snapshot exists); the public repository's first commit becomes the first reproducible snapshot. Initialise git locally. Do not push.
4. **Final PDF**. Rebuild from the revised Markdown; check page count, table rendering, and that the title, author and date are correct; add the Zenodo DOI placeholder to be filled after minting.
5. **Publish, in this order, each on a yes** [confirm each]: (a) push the repository to GitHub and make it public; (b) create the Zenodo record, upload the PDF, link the GitHub release, mint the DOI; (c) update the PDF footer with the DOI and re-upload as version 1.0.1 if Zenodo allows, or leave the DOI in the README; (d) arXiv submission when an endorser exists.
6. **After publication**: add the DOI and URLs to `CHECKPOINT.md` and the memory file; close the programme's Paper 1 thread; do not respond to detector scores or reviews by rewriting the archived work.

## Open items for Daniel

- Author line: name only, or name plus a contact email and ORCID?
- Licence choice for documents and code.
- Repository name (three candidates to be checked for collisions once Daniel picks a form: e.g. `self-boundary-red-team`, `action-action-reachable-support-benchmark-benchmark`, `interventional-boundary-red-team`).
- Whether to seek an arXiv endorser now, and from whom.
- Whether the two precursor transcripts and the original roadmap HTML should be included in the public archive (recommendation: the roadmap HTML yes, since the report cites it; the transcripts no).
