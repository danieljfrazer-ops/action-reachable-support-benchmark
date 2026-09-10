# Roadmap v3.4: harmonisation after the third Gemini red team (gemini-v3.3/)

Date: 6 September 2026. Verdict received: unconditional go for Stage 0A; two non-blocking harmonisations for Stage 0B (I1, I2). Both accepted. All earlier amendments stand.

## D1. Decision rules by regime (I1; supersedes A5 for the primary contrast)

Δ_pAUC is signed so that positive favours sequential interventional detection over the classical residual detector. 95 percent bootstrap intervals clustered by seed.

- **Regime R0, clean (sanity anchor).** Validated if the upper bound of Δ_pAUC ≤ 0, confirming the classical detector dominates or matches at zero probe cost. Anomaly if the lower bound > 0: stop and investigate the environment or the detector before any confirmation claim.
- **Regimes R1 (misspecified) and R2 (masked).** Superiority if the lower bound > δ = ln 2 on both dynamics families. Futility if the upper bound < δ on either family. Inconclusive otherwise, reported as a benchmark finding with no efficacy claim.
- The positive-control gate (A5) still runs before confirmation and is not part of this decision.

## D2. Disjoint delay supports return a signed float (I2)

`delta_pauc()` returns the boundary difference as a float with dominance declared when the achievable delay supports do not overlap, so that multi-seed aggregation never encounters a null. Applied and re-executed in `executable-proofs/gemini_v32_checks.py`; the output file shows the disjoint case and a mixed-seed mean.

## D3. Expectation management (Claude's note, not a Gemini finding)

Gemini's scorecard rates Paper 2 as tier-one conference material and gives several 5 out of 5 marks. That is a reviewer's enthusiasm about a plan, not evidence. Paper 2's potential is real: it has named methods, a testable failure prediction and a fresh concession of the gap. It will be judged on results that do not yet exist. The honest planning assumption remains arXiv first, then a workshop or CoLLAs for Paper 1, and a main-track attempt for Paper 2 only if the confirmed effect is large and the filter demonstrably fixes it.

## Status

Planning is closed. Stage 0A begins from `stage-0a-contract-v2.2.md` under the workflow in v3 section 11 plus B7 (executable proofs). Next review gate: Gate 0A, target 26 September 2026.
