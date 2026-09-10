# Roadmap v4.3: decisions D-1 to D-5 applied

Date: 6 September 2026. Daniel's decisions: D-1 (a), D-2 (a), D-3 (a), D-4 (a), D-5 lock. Applied in `stage-0a-contract-v3.2.md`, `interface-spec-v3.md`, and the regenerated `confirmation-design.csv`.

## G1. Control tier (D-1a)
PointMass2D (two independent thrusters, non-terminating, in-repo) and Pendulum-v1 with a disclosed 2,000-step horizon replace CartPole. Contract H2.

## G2. Calibration (D-2a)
≥ 400 false-alarm run lengths and a 95 percent interval inside [900, 1100], per cell, shared across seeds, hard cap; no exclusion; partial-order endpoint for methods outside the band. Contract §0.

## G3. Comparator (D-3a)
CUSUM on innovations of a channel-agnostic linear predictor in every cell; R0 renamed `R0_inband_linear`; "correct model" wording removed. Contract H.

## G4. Sequential IBD specification (D-4a)
A fresh-context agent drafts `sequential-ibd-spec.md` from the IBD paper (arXiv 2603.18257) and the contract; a second fresh-context agent red-teams it with executable checks; Daniel signs. Until signed, the spec is informative and the confirmatory pair is not frozen.

## G5. Locked defaults (D-5)
Co-primary on oracle-labelled confounded channels; f_conf = 0.5. Provisional wording removed.

## G6. Next review round
A **code review**, not a prose round: fresh-context agents on different models write mutants against the rebuilt gate and, once Stage 0A produces them, against the generator and oracle. The frozen set for that round is defined by `freeze-manifest.txt`.

## Normative set after this file
`roadmap-v4.md` + amendments v4.1, v4.2, v4.3; `stage-0a-contract-v3.2.md`; `interface-spec-v3.md`; `sequential-ibd-spec.md` (once signed); `confirmation-design.csv`; `executable-proofs/gate/`.
