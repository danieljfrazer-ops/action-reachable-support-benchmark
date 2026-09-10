# Roadmap v4.4: Opus round-2 findings applied; process rule added

Date: 6 September 2026.

## H1. Clean-regime rule (OP-10)
R0 is validated iff the 90 percent interval for Δ lies inside (−δ0, +δ0) (two one-sided tests). A lower bound < −δ is flagged "probing cost dominates in clean conditions" and reported.

## H2. Power of the conjunctive rule (OP-9, FB-14)
The pilot estimates the between-seed SD of paired HPDT differences per family and reports, by simulation, the power of the **full R1 conjunction** (Δ on both SCM families, I on both, sign on both control-tier environments). Minimum acceptable power 0.8 at true effect 2δ; otherwise seeds rise (to 20, then 30) before confirmation; if still below 0.8 the study is pre-committed to report as underpowered rather than re-freeze δ.

## H3. Two co-primaries with hierarchical testing (OP-13; amends D8)
Primary: HPDT contrast. Co-primary: confounded-channel false support, tested only if the primary rule passes (hierarchical, no alpha split). For the channel-agnostic CUSUM arm, p_c is derived from per-channel innovation statistics through the frozen isotonic calibrator; the arm predicts every channel, so channel-resolved statistics exist even though it does not know which channels are body.

## H4. Interaction within environment (OP-20)
I is defined and tested within each environment; the cross-environment requirement is the sign rule only. Under D-3a the regimes are the same predictor class with and without the frozen misspecification transform, so R1 − R0 is commensurable within an environment.

## H5. Confirmation matrix (OP-22)
Columns added: `steps_per_run`, `calibration_steps` (per cell, shared), `split_id`, `n_channels`, `probe_config_hash`; `s_change_required` (design intent, frozen) replaces the runtime certification field, which lives in the ledger. Calibration runs appear as rows with `role=calibration`. Third arm per D-7 when confirmed.

## H6. Process rule: no repair during a review (Opus addendum)
A frozen hash is not modified while any reviewer is working on it. Repairs land in a new version after all reviewers report, and each reviewer's findings are adjudicated against the version they ran. Violation recorded: the gate was rebuilt at 22:08 on 6 September while the Opus review of d23960e6da441de7 was in progress. The mutation suite is acknowledged to record past attacks rather than measure coverage; a fresh-context mutant attempt is therefore a standing requirement at every gate, not a one-off.

## H7. Gate hygiene (OP-2, OP-27)
`mutants.py` asserts that no mutant raises RecursionError and that each mutant differs from the original on at least one input before the run; `run_gate.py` flushes before the subprocess and ends with a one-line summary and exit code.

## Normative set after this file
`roadmap-v4.md` + amendments v4.1 to v4.4; `stage-0a-contract-v3.2.md`; `interface-spec-v3.md`; `sequential-ibd-spec.md` (once signed); `confirmation-design.csv`; `executable-proofs/gate/`. Decisions D-6 and D-7 pending.
