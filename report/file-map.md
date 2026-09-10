# File map: report tables and claims to archived sources

All paths are relative to `docs/archive/red-team/`.

| Report item | Adjudication | Reviewer inputs and captured output |
|---|---|---|
| Table 1 (rounds, hashes, gate counts) | `readiness-protocol.md` (round log; hash and gate count at each freeze) | `freeze-manifest.txt`, `freeze.py`; `review-claude/`, `review-codex/`, `review-gemini/` (round 1); `round2-adjudication-and-tally.md`, `round3-adjudication-and-tally.md`, `round4-adjudication-and-tally.md`, `round5-adjudication-and-tally.md`, `round6-adjudication-and-tally.md` |
| Round-5 per-process non-determinism (salted hash; +0.187 vs +0.210) | `round5-adjudication-and-tally.md` §2; `decisions-required.md` ("Applied without asking": deterministic noise key) | `review5-claude-opus/findings.md` (R5-1), `review5-claude-opus/sim_frozen.hashseed1.txt` |
| Round 0 (single-model red team, prior art) | `README.md`, `findings.md` (F2), `evidence.md`, `research-round-2.md` | |
| Table 2 (round 5 base cell) | `round5-adjudication-and-tally.md` §1 | `review5-claude-opus/sim_frozen.py`, `review5-claude-opus/sim_frozen.output.txt`; `review5-codex/sim_frozen.py`, `review5-codex/sim_frozen-output.txt`; `review5-gemini/sim_frozen.py`, `review5-gemini/sim_frozen.output.txt`, `review5-gemini/sim_frozen_results.json` |
| Round-5 perturbation set, floor, 0.975 static vector, 60–70 % no-change | `round5-adjudication-and-tally.md` §1 items 2–5 | `review5-claude-opus/findings.md`, `review5-claude-opus/schange_split.output.txt` (0.975 is this reviewer's) |
| D-11 (six decisions) | `decisions-required.md` (D-11 table); `stage-0a-contract-v3.9.md` §L | |
| Table 3 (round 6 family L) | `round6-adjudication-and-tally.md` §1 | `review6-codex/report.md` (per-cell tables with t intervals), `review6-codex/sim_frozen.results.json`; `review6-gemini/sim_output.txt`; `review6-claude-opus/report.txt`, `review6-claude-opus/results/` |
| Controls (0.500; 0.422 / 0.200), n_lost | `round6-adjudication-and-tally.md` §1 | `review6-codex/report.md` "Controls and n_lost"; `review6-gemini/sim_output.txt` Tables 2–3 |
| Present/absent identity on the pre-event support | `round6-adjudication-and-tally.md` §2 item 1 | `review6-claude-opus/aux_output.txt` §A; `review6-gemini/findings.md` GM6-01; `review6-codex/findings.md` "Attacks that failed" |
| Family N reversal (0.84 vs 0.73) | `round6-adjudication-and-tally.md` §3 | `review6-codex/report.md` rows N_Nx10_tau0; `review6-gemini/sim_output.txt` Table 5 |
| Negated static vector 0.80; actuator 1 inert; Δ_c not blind (0.55–0.66) | `round6-adjudication-and-tally.md` §2 items 4, 5, 7 | `review6-claude-opus/findings.md` R6-OP-04/05/09, `review6-claude-opus/aux_output.txt`; `review6-gemini/findings.md` GM6-04/05 |
| Secondary full-channel AUC (two implementations) | `round6-adjudication-and-tally.md` §3 and §2 item 9 | `review6-codex/report.md`; `review6-claude-opus/report.txt` (Gemini's excluded: `review6-codex/adjudication.md` "Differences resolved") |
| Surviving mutants; generator mutants unregistrable | `round6-adjudication-and-tally.md` §2 item 8 | `review6-claude-opus/mutants_new.*.patch`; `review6-codex/surviving_mutant_family_n_scope.py`; `review6-gemini/findings.md` §3 |
| Table 4 (novelty scores) | `round7-adjudication.md` §1 | `review7-codex/verdict.md`, `review7-gemini/verdict.md`, `review7-claude-opus/verdict.md` |
| IBD Proposition 3.3 and §3.2 sentence | `round7-adjudication.md` §1 | `review7-claude-opus/verdict.md`, `review7-codex/verdict.md` (both read arXiv:2603.18257v2) |
| §4.4 derivation (four conclusions, limit of β_a, confuser dissociation, disputed adaptation sign) | `round8-adjudication.md` §1 | `review8-codex/derivation.md` §§1–4; `review8-gemini/derivation.md` §§1–4; `review8-claude-opus/derivation.md`, `review8-claude-opus/check_algebra.py` |
| Gate status (66 tests, 47 mutants, exit 0) | `CHECKPOINT.md`; `round6-adjudication-and-tally.md` §2 item 8 | `executable-proofs/gate/gate.output.txt`; `review6-codex/gate.output.txt` |
| Report reviews (round 9) | | `review9-claude-opus/report-review.md`; `review9-tool/` (cross-model tool runs) |
| Figure 1 (plant diagram) | `stage-0a-contract-v3.9.md` §B (structural equations); report §4.4 equations | `../report/make_figures.py` → `../report/figures/plant.svg` (hand-authored, scripted) |
| Table 2b (round-5 perturbation set) | `round5-adjudication-and-tally.md` §1 item 2 | `review5-codex/sim_frozen-output.txt` (per-configuration tables and the nine-cluster aggregate); `review5-claude-opus/sim_frozen.output.txt` (per-configuration rows at offset 500; benefit = (IBD − comparator) present minus absent); `review5-gemini/sim_frozen.output.txt` (four configurations) |
| Table 5 (confuser dissociation) | `round8-adjudication.md` §1 items 5–6 | `review8-claude-opus/derivation.md` prediction table; `review8-codex/derivation.md` §4; `review8-gemini/derivation.md` §2 |
| Table 6 (error provenance) | `round4-adjudication-and-tally.md` (R4-GM-02 rejection); `round5-`, `round6-`, `round8-adjudication` files; `round6-adjudication-and-tally.md` erratum | `review4-gemini/findings.md` R4-GM-02; `review9-claude-opus/report-review.md`; `review9-tool/RT-007-report-draft5.md` |
