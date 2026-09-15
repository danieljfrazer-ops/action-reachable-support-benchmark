# action-reachable-support-benchmark

Which sensors do an agent's actions actually control, when a hidden cause confounds it and its body changes? This repository is the record of an attempt to build a benchmark for that question, and of the cross-model red team that showed the benchmark's central claim was not supported.

**Cite:** Frazer, D. (2026). Which sensors do my actions control? A negative result on sequential interventional boundary tracking under a shared-cause confounder. Technical report, version 1.0. DOI 10.5281/zenodo.22775827.

**Start with the technical report:** [`report/technical-report.pdf`](report/technical-report.pdf) (source: [`report/technical-report.md`](report/technical-report.md)). It states what was tried, what three AI systems found when they each implemented the estimators and ran them on one frozen simulator, what survived, and six errors of the author's that the process caught or missed. [`report/file-map.md`](report/file-map.md) traces every table and claim in the report to the archived files.

## Layout

- `report/` — the technical report (Markdown, HTML, PDF), its file map and build script.
- `red-team/` — the full archive of the nine review rounds: prompts, reviews, adjudications, frozen manifests and hashes, the Stage 0A contract (v3.9), the interface specification (v5), both estimator specifications and their superseded drafts, the reference generator (families L and N), the metric references, the test gate, and every reviewer's implementation with captured output. `red-team/CHECKPOINT.md` is the entry point to the archive; `red-team/readiness-protocol.md` is the round log.
- `roadmap/original-roadmap.html` — the research roadmap the red team started from.

## Running the gate

The gate needs Python 3.12 and the pinned NumPy; the runner refuses any other interpreter.

```
cd red-team/executable-proofs/gate
python3.12 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python run_gate.py
```

Expected: 66 tests passed, 47 of 47 registered mutants killed, exit 0. Three reviewer-written mutants that survive the gate are listed in `red-team/round6-adjudication-and-tally.md`; the mutation runner cannot register mutants against the generator. `red-team/freeze.py` prints the hash of the archive as it stands, which does not reproduce the historical freeze hashes in the round log (see the report's Table 1 caption); this repository's first commit is the first reproducible snapshot.

## Status

The programme's Paper 1 claim was not supported and no confirmatory experiment was run. The report is a technical report of a negative result with reusable artefacts, not a peer-reviewed paper. Follow-up work, if any, would live in this repository under new directories; the archive here is frozen as of 10 September 2026.

## Licence

Documents: CC BY 4.0 (`LICENSE-DOCS`). Code: MIT (`LICENSE`).

## Disclosure

The specifications, simulator, gate, simulations, reviews, derivations and adjudications were produced by three AI systems (Claude, Codex, Gemini) under the author's direction, as described in Section 9 of the report.
