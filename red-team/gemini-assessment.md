# Assessment of the Gemini red team (gemini-v3.1/)

Date: 6 September 2026. Verdict received: **conditional go, pause for patches**. Gemini's findings G1 to G4 are mathematical; I did not argue with them, I executed them. Script and output are in `executable-proofs/gemini_checks.py` and `gemini_checks.output.txt`.

## 1. The mathematics: Gemini is right on all four, and the errors are mine

| Finding | Executed check | Result | Disposition |
|---|---|---|---|
| G1 closed-loop policy feedback makes the action-effect response R depend on the sensor map P, contradicting Table D | Simulated R at horizons 1 to 3 with the default policy reading body channels, identity vs swapped assignment | h=1 identical; h=2 identity [1.2, 0.1] vs swapped [0.7, 0.4]; h=3 [1.42, 0.25] vs [0.61, 0.68]. Open-loop clamp: identical at all horizons. | **Accept.** R must be defined open-loop: do(a_t = a, a_{t+1..t+h-1} = 0). My "reduces to the Jacobian" claim was only true open-loop. |
| G2 M_{t,h} = A_b^{h-1-τ} B has a negative exponent when h ≤ τ | h=1, τ=1 | Computed A_b^{-1} B = 1.11 I, an acausal response where the truth is 0; singular A_b raises LinAlgError | **Accept.** Piecewise: 0 for h ≤ τ. |
| G3 correlation under a constant probe is NaN | corr(a, x_next) for observational policy, constant probe, randomised probe | 0.86, NaN, 0.00 | **Accept.** Severing test uses randomised do(a); invariance under a constant probe uses mean difference. |
| G4 matched-delay estimand can require extrapolation outside the observational estimator's operating curve | Reasoned, not simulated: if the observational detector cannot reach the interventional detector's median delay at any threshold, the matched point does not exist | Correct by construction | **Accept.** Primary estimand becomes normalised partial area between the delay-vs-log-ARL curves over the shared achievable delay interval; disjoint supports reported as dominance at the boundary. |
| G5 accidental path cancellation makes the graph oracle and finite differences disagree | | Correct; low probability but it would produce flaky tests | **Accept.** Margin on sampled entries; resample on faithfulness violation. |
| G6 the three-target paper is de facto single-target because baselines emit constants for R and P | | Correct. A constant output has no operating curve. My "typed constants" answer to Codex's F3 was cosmetic. | **Accept.** Paper 1 scores S^obs,ε and α^S only. R and P stay in the contract for oracle verification and later phases. |

What this means for Daniel's concern about "the math": the four errors are specification bugs of the kind found by running a twenty-line script, not flaws in the idea. They would have cost days at pilot time; they cost an hour now. Gemini's process point (G9) is the real lesson: two language models reviewing prose did not execute the equations. From here, every contract section with an equation ships with a script that runs it, and the red-teaming agent runs mutants that try to break it. That rule is now in the workflow.

## 2. The laptop: Gemini's own numbers show compute is not the constraint

Gemini's estimates: Phase S about 16 million sequential steps, roughly 2 to 3.5 hours; Paper 1 about 1,500 runs of a small SCM. My estimate for Paper 1 runs: a few seconds of simulation plus up to a minute of estimator work per run, so 15 to 30 laptop-hours total, serialised over nights. That is fine. The real constraints Gemini identified are:
- **Serialisation.** Do not run two phases' sweeps at once on one fanless machine; the throttling compounds and the review queue collapses. Accept: 0A, then the shakedown, then 0B.
- **Review bandwidth.** Daniel is the critical path, not the CPU.
- **World-model training**, if the benchmark's third tier is adopted (section 4 below). That is the only heavy item, and it can be bought: a rented GPU at a few dollars an hour for a few days removes it. The Air does not have to do everything.

So: the laptop is adequate for everything in Papers 1 and S, with duty-cycle cooldowns and step budgets. It is marginal only for training several world models, and that has a cheap escape.

## 3. The strategic finding (G5): partly right, and it points to the answer

Gemini's "unassailable triviality trap" charge has two parts.
- **"Intervention beats correlation under confounding is axiomatic."** True. That is why Codex and I made it the primary contrast: it was the safest claim. Gemini is right that a confirmatory hypothesis whose truth follows from the do-calculus is not informative. What is informative is quantitative: the probe cost paid for that robustness, the detection delay it buys, and which modern learned methods fall into the trap. The primary contrast should be re-aimed at that.
- **"A five-variable linear SCM after IBD did MuJoCo is a step backward."** Partly true. The SCM tier is needed because it is the only place where the three targets have exact ground truth and calibration can be scored. But it cannot be the whole paper. Gemini's Pivot 2, a benchmark suite with a realistic tier, is the fix, and it is also what Daniel asked for. See `benchmark-proposal.md`.

Gemini's three pivots, assessed:
- **Pivot 2, open benchmark suite:** adopt. Build on Gymnasium and, where useful, on Robust-Gymnasium (ICLR 2025, MIT licence), which already supports observation, action, reward and dynamics perturbations at arbitrary times but has **no ground-truth controllability labels and no sensor swap or actuator dropout**. Our contribution is the typed ground truth, the confounded distractor wrapper, and the sequential metrics.
- **Pivot 3, bridge FDI and causal ML:** adopt as framing. Cite Basseville & Nikoforov, Campbell & Nikoukhah, CUSUM and GLR detectors as baselines, not just related work.
- **Pivot 1, "delusion of agency" in world models:** adopt as **Paper 2**, replacing the auxiliary self-prediction null-result paper, which Gemini rightly called unpublishable on a toy environment. Prior-art check today makes this pivot sharper than Gemini stated it:
  - Iso-Dream (NeurIPS 2022) and Sensorimotor World Models (Ivashkov, Balestriero, Schölkopf, June 2026) separate controllable from uncontrollable dynamics using **inverse dynamics**. Under a shared cause that drives both the policy and a distractor, the distractor predicts the action, so an inverse-dynamics criterion will keep it as "controllable." That is a precise, testable failure prediction.
  - Dueling World Models (Li et al., August 2026) rejects action-independent "common-mode" distractors and **states in its appendix that distractors whose motion tracks the action are a boundary of the method**.
  - Denoised MDPs (ICML 2022) and identifiable factorisation (NeurIPS 2023) assume the uncontrollable factor is action-independent.
  - None handle a boundary that changes during deployment.
  So Paper 2 has named victims, a named failure mode, and an August 2026 paper that concedes the gap. Theoretical framing: Ortega et al. 2021, "Shaking the foundations: delusions in sequence models for interaction and control" (arXiv 2110.10819; verify before citing).

## 4. Phase S (G7): a judgment call, settled by bandwidth

Gemini: internal only, one week, no write-up. Codex: small conditional contribution. Me earlier: small but real. The deciding fact is Daniel's writing bandwidth, which is the critical path. Decision proposed: run it as a one-week internal shakedown; write it up publicly only if a result is surprising (for example a clean negative on surprise-based writes). Default is internal.

## 5. Disposition table

| ID | Sev | Disposition |
|---|---|---|
| G1 | High | Accept; verified by execution; patched in contract v2.1 |
| G2 | High | Accept; verified; patched |
| G3 | High | Accept; verified; patched |
| G4 | High | Accept; pAUC estimand in v3.2 amendments |
| G5 | High (strategic) | Accept the diagnosis; adopt Pivots 2 and 3 for Paper 1, Pivot 1 for Paper 2 |
| G6 | Medium | Accept; Paper 1 scores S^obs and α^S only |
| G7 | Medium | Accept with an upgrade clause |
| G8 | Medium | Accept; serialise 0A, S, 0B; duty-cycle cooldowns |
| G9 | Medium | Accept; executable-proof rule added to the workflow |
| G10 | Low | Accept; Paper 2 replaced by Pivot 1; Paper 3 made conditional on Phase S |

Where Gemini overreached: the claim that Paper 1 "mirrors 1980s FDI" is true of the linear SCM tier only; FDI theory does not cover learned estimators, high-dimensional distractors, or calibration scoring, which is why the benchmark tier matters. And "very low value" for Phase S is an opinion about citations, not about the information; the demotion is justified by bandwidth, not by worthlessness.
