# Round 5 adjudication and tally (frozen 0468104f6431b050, frozen generator)

Date: 7 September 2026. Reviewers: Codex (17 findings), Gemini (9), fresh-context Claude Opus (29). All three implemented both arms from the specifications and ran them on the frozen generator, configuration seeds 0 to 9, both distractor levels, both delays, and the perturbation set. Author adjudicates; hash unchanged.

## 1. The convergence test passed, and the converged answer changes the design

| Offset 500, confounder present | Opus | Codex | Gemini |
|---|---|---|---|
| Sequential IBD AUC, N_x = 10, τ = 0 | 0.800 | 0.815 | 0.831 |
| Passive comparator AUC, same cell | 0.691 | 0.688 | 0.675 |
| Comparator AUC, confounder absent | 0.875 | 0.878 | 0.863 |
| Confounding benefit, N_x = 10, τ = 0 | +0.187 [0.155, 0.218] | +0.204 [0.153, 0.254] | +0.190 [0.158, 0.223] |
| Benefit, N_x = 30, τ = 2 | +0.240 | +0.237 | +0.228 |
| D-10.3 comparator floor (lower bound ≥ 0.85) | fails 10 of 12 cell-offsets | fails all 4 base cells | fails all 4 base cells |

Three implementations now agree to within Monte Carlo error on every number. The exit condition for design review is met. What they agree on:

1. **The interventional arm is robust and reproducible.** AUC 0.80 to 0.85 across both distractor levels, both delays and the perturbation set; confounder-insensitive; three of three.
2. **The confounding benefit clears the margin in every base cell** (+0.15 to +0.28), but the perturbation set does not (aggregate lower bound 0.090; individual configurations from −0.015 to +0.25).
3. **The result is inadmissible because the D-10.3 competence floor fails first**, three of three: the comparator's lower bound without confounding is 0.64 to 0.83 against the required 0.85, worst at delay 2. The contract's own rule applies: the comparator specification is defective and the phase stops.
4. **The cause is identified and is not a tuning matter.** Opus and Codex show the specified score is strictly dominated by its own loading term: the action loading alone ranks the support at AUC 0.99 without confounding, and the innovation-mean-shift term costs 0.12 to 0.27 because under a centred policy an actuator loss changes the residual variance and action-residual covariance, not the residual mean. Codex reached this theoretically; Opus and Gemini measured it.
5. **The task as posed mostly measures static reachability, not adaptation to change.** Opus: a fit-time constant that never sees the scored episode or the event beats both confirmatory arms (0.975 versus 0.77 to 0.83), because the event removes at most 3 of 24 to 44 channels and, on 60 to 70 percent of frozen instances, removes none: the CL-4 constraint that the event must change the support is not certified by the generator (three of three). The primary as frozen is over 90 percent answerable offline.

## 2. Generator defects (three of three unless noted)

Cross-process non-determinism from a salted string hash in the noise key; CL-4 not certified; nonzero A_b entries below c_min on half the certified instances and B not dense (Codex, Opus); burn-in declared and never used; the noise multiplier applied to some streams and not others (Codex); family N absent although the matrix has family-N rows (Codex); eight to eleven surviving mutants against the generator, including droppable certification conjuncts, an invertible confounded mask, a droppable CRN variable key, and a soft actuator loss that makes the structural and operational labels disagree (Opus 8, Gemini 3, Codex 1; overlapping). Configuration seeds 0 to 9 are now exhausted as development instances and a disjoint confirmation set must be reserved (Codex).

## 3. Specification defects

IBD warm-up gives the two arms different alarm exposure (Codex); persistence in epochs and refractory in steps cannot both go through one integer-indexed counter (Codex); estimator RNG lifecycle and probe-stream seeding undefined (Codex); terminal probe at t = 2000 cannot be applied by the generator (Codex, Gemini); fit hierarchy per instance versus pooled undefined (Codex); the matrix has one seed column, not instance and episode seeds, and stale arm identifiers (Codex); the H-horizon loading is an open-loop sensitivity and must be labelled so (Gemini); the comparator fixtures are pinned to seed 0, an instance on which the event changes nothing (Gemini); normative cross-references still point at interface v3 and draft 3 (Codex).

## 4. Rejected or judgment calls
Gemini GM-06 (probe spacing violates exchangeability because of settling): the sign randomisation makes both sign groups share the settling residue, so exchangeability under "actuator does not reach c" holds; the residue adds variance, not bias. Recorded as a caveat, not a defect. Gemini GM-07 (zero statistic for unprobed cells): superseded by balanced blocks, which make the case unreachable.

## 5. Decision D-11 (see `decisions-required.md`)

## 6. Process note
Five rounds and three reviewers produced, at the end, three identical answers to a question the author had posed incorrectly. The interventional method works. The passive comparator was specified with a change statistic that cannot see the change. And the benchmark's event, as generated, usually changes nothing, so the primary measured static structure that a constant solves. None of that was visible until three models ran the same frozen instances. The corrective is a re-posing of the task, which is D-11, followed by one more cross-model execution round.
