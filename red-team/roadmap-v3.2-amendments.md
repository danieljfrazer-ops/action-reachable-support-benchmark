# Roadmap v3.2: amendments after the Gemini red team

Date: 6 September 2026. `roadmap-v3.md` and `roadmap-v3.1-amendments.md` stand except where amended here. IDs B1 to B9 map to Gemini findings in `gemini-assessment.md`.

## B1. Primary estimand (G4)

Replaces A4's matched-delay estimand. Δ is the normalised partial area between the delay-versus-log-ARL operating curves over the shared achievable delay interval [d_min, d_max], where d_min is the larger of the two estimators' minimum achievable median delays and d_max the smaller of their maxima, from the pilot threshold sweep. Δ_pAUC = (1/(d_max − d_min)) ∫ (log ARL_A(d) − log ARL_B(d)) dd. If the supports are disjoint, Δ is reported at the nearest boundary point and dominance declared. Smallest effect of interest δ = ln 2 in average log-ARL units, rationale unchanged. Decision rules in A5 apply to Δ_pAUC.

## B2. Re-aimed primary contrast (G5)

The old primary contrast (interventional beats observational under confounding) follows from the do-calculus and is not informative. The new primary contrast is **quantitative**: the probe budget at which sequential interventional detection matches the best classical FDI detector (CUSUM or GLR on model residuals) on Δ_pAUC under confounding. Secondary descriptive findings: which learned observational criteria (forward-model residual, inverse-dynamics attribution) fail under confounding, and how every method behaves through a boundary change. Reviewers get a number they did not have, not a theorem they already had.

## B3. Paper 1 shape (G5, Pivot 2 and 3)

Paper 1 is the benchmark suite in `benchmark-proposal.md`, tiers T1 and T2, with the estimator families listed there, released as a package. Positioning: a bridge between active fault detection and isolation and interventional causal discovery, with a standardised sequential protocol. Tier T2 wrappers are built to be compatible with Robust-Gymnasium and cite it as the platform extended. Title and abstract avoid "self-boundary"; motivation carries the one non-claim sentence (D2).

## B4. Paper 2 replaced (G5, Pivot 1; G10)

Paper 2 is now: **do controllability-separating world models attribute agency to confounded distractors, and what happens when the boundary changes?** Victims with a testable failure prediction: Iso-Dream and Sensorimotor World Models (inverse-dynamics criteria keep a distractor that predicts the action); Dueling World Models (its own appendix names action-tracking distractors as out of scope); Denoised MDP (assumes action-independent noise). Intervention: an interventional boundary filter in front of the world model. Tier T3, small state-based models, five seeds; confirmation runs on a rented GPU if the Air's schedule cannot absorb them. The former Paper 2 (auxiliary latent self-prediction) survives only as one ablation inside this paper.

## B5. Phase S demoted with an upgrade clause (G7, G8)

Phase S is an internal one-week harness shakedown, serialised **between 0A and 0B**, using the reduced scope of A7. Output: an internal report that seeds Paper 3's baseline table. A public note is written only if a predeclared surprising result appears (a clean negative on surprise-based writes, or fast weights relocating rather than reducing forgetting), and only after Paper 1 is on arXiv.

## B6. Serialisation and duty cycle (G8)

No two phases run sweeps concurrently on the Air. Sixty-second cooldown between heavy run blocks. Thermal pressure and throughput logged per block. Step and operation budgets remain primary (D5).

## B7. Executable-proof workflow rule (G9)

Added to the workflow in v3 section 11, between steps 2 and 3: the building agent delivers, for every contract section with an equation or numeric invariant, a script that runs it with numbers including edge cases; the red-teaming agent runs mutant generators against it; Daniel signs off on the script output. No phase gate passes on prose alone. `executable-proofs/gemini_checks.py` is the first instance.

## B8. Timeline (G8, G13-equivalent)

| Milestone | v3.1 | v3.2 |
|---|---|---|
| Contract v2.1 patches | | done 6 Sep 2026 |
| Stage 0A | to ~24 Sep | 8 to 26 Sep |
| Phase S internal shakedown | parallel with 0B | 27 Sep to 4 Oct |
| Stage 0B | to ~15 Oct | 5 to 26 Oct |
| Paper 1 pilot | 15 to 31 Oct | 27 Oct to 10 Nov |
| Paper 1 confirmation | Nov | 11 Nov to 10 Dec |
| Paper 1 write-up and arXiv | mid-Dec to mid-Jan | 11 Dec to late Jan 2027 |
| Venue submission | Feb 2027 | Feb to Mar 2027, against live calls |
| Paper 2 (T3) | Feb to Mar 2027 | Feb to May 2027 |

## B9. Paper 3 made conditional (G10)

Paper 3 proceeds only if the Phase S shakedown shows that no single memory family dominates at matched total budget. If the episodic store dominates everywhere at small scale, Paper 3 is reframed around that finding or dropped.

## Unchanged

D1 to D8; A2, A3, A5 (applied to Δ_pAUC), A6, A8, A9; Phases 3 and 4 otherwise; the capability framing; the risk table.
