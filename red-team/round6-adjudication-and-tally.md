# Round 6 adjudication and tally (frozen 38d161e762a3de76, D-11 encoded)

Date: 8 September 2026 (reviews dated 7 September). Reviewers: Codex (9 findings), Gemini (10), fresh-context Claude Opus (14 plus 11 open choices). All three implemented both confirmatory arms from the two specs alone and ran them on the frozen generator: configuration seeds 0 to 9, both distractor levels, both delays, present and absent, the 3 × 3 perturbation set at seed 0, and family N at seeds 0 to 4. Runtimes 5 to 21 minutes, no seed reduction. Author adjudicates; hash unchanged throughout.

## 1. The reproduction succeeded; the exit condition failed by construction

Three implementations agree to three decimals on every primary number, every control, the lost-channel counts (1 on 32 of 40 draws, 2 on 8), the probe count (99 per episode), and the read steps (1199/1499/1999 and 1182/1482/1982). Offset 500, family L, identical across the three:

| Cell | seq-IBD present = absent | comparator present | comparator absent | Δ_AUC present | benefit |
|---|---|---|---|---|---|
| N_x 10 or 30, τ = 0 | 0.813 | 0.879 | 0.863 | −0.066 | −0.017 |
| N_x 10 or 30, τ = 2 | 0.687 | 1.000 | 1.000 | −0.312 | 0.000 |
| perturbation set (9 cells) | 0.55 to 0.80 | 1.000 | 1.000 | ≤ −0.05 | 0.000 |

Contract §L exit condition: (i) agreement to Monte Carlo error: **met**; (ii) comparator floor ≥ 0.85 on the primary, absent: **fails at τ = 0** (lower bound 0.70 to 0.73 depending on the unspecified interval estimator), passes at τ = 2 only on a zero-width interval; (iii) confounding benefit lower bound > 0.10: **fails everywhere, and cannot be met**.

## 2. Adjudicated findings (three of three unless noted)

1. **The confounding benefit on the D-11.1a primary is identically zero by construction (critical).** The pre-event support contains only body and downstream channels; the confounder enters only the distractor block; the absent condition keeps the policy unchanged; so present and absent streams are bitwise identical on every channel the primary scores, and seq-IBD's primary is bitwise identical across conditions. Verified by all three and by the author. D-11.1a moved the primary onto a channel set the treatment cannot reach. **The author's recommendation was wrong and a channel-set check would have caught it before adoption.**
2. **R0-present fails; the passive comparator beats the interventional arm on the re-posed task in every family-L cell and every perturbation cell (critical).** Contract §G's futility branch is met. Not a tuning matter: detecting that a controlled channel went quiet is easy for a frozen residual monitor with an action-residual covariance score.
3. **Comparator floor (high).** Fails at τ = 0; at τ = 2 all ten instances score 1.000 so any empirical interval is zero-width. The contract never specified the interval estimator, sidedness or the within-instance summary (Codex t interval, Claude percentile cluster bootstrap, Gemini its own); the point estimates agree, the bounds do not, and a verdict that depends on the estimator is a defect of the contract.
4. **The static loading vector, negated, is an event-blind probe-free arm that scores 0.80 at τ = 2 against seq-IBD's 0.687 (high).** Mechanism: CL-4 by construction makes the lost channel the dominant body component of actuator 0, typically the strongest pre-event channel. Both the below-chance static control and the comparator's ease are consequences of choosing the lost coordinate by construction.
5. **Loss of actuator 1 removes no observed channel on any seed (high).** The benchmark tests one hand-wired coordinate; at τ = 2 the pre-event support is exactly four channels on every draw and the delay cells score a different estimand (zero propagation hops survive at H = 3).
6. **The primary's lattice (high).** With one negative against three to five positives, per-episode AUC takes at most six values and 0.85 lies between lattice points; the floor value was transplanted from a 24-to-44-channel statistic without re-derivation.
7. **Specification and registry defects (two or three of three):** the two specs' episode-id registries collide with each other and with the generator's reserved ids (Codex, Claude, Gemini); interface v5's per-episode construction cannot transport the comparator's per-instance predictor artefacts (Codex); `instance_seed` names three objects and the matrix carries `per_instance` and `shared_per_cell` in one row (Claude, Codex); the perturbation set is not materialised as rows (three of three); the per-instance ARL budget is of order 10⁸ steps per arm (three of three); Δ_c's stated chi-square null does not hold under closed-loop dependence and the score is not blind before the event (fault-free AUC 0.55 to 0.66 in 15 of 15 cells; Codex, Claude); λ_rel was development-outcome-selected and must be disclosed as such (Codex); `sequential-ibd-spec.md` §14(d) is stale against the frozen files (Claude).
8. **Surviving mutants (gate defects):** `auc_pre_event_support` over `pre | post` survives because every fixture has post ⊆ pre (Claude, confirmed by Codex and Gemini); family-N certificate mutants survive (b-and-d-only or b-only bound; zero burn-in in the stationary mean: Codex, Gemini); the mutation framework iterates `test_gate` only, so no generator mutant is registrable (three of three).
9. **Gemini's secondary numbers at offsets 200 and 500 are wrong**: its script read `secondary_support()` after the episode ended (Codex). Its primary numbers and verdicts are unaffected. Recorded, not counted.

## 3. What is reproducible across rounds 5 and 6

- **Interventions buy attribution.** Full-channel AUC with the confounder present: comparator 0.73 to 0.80, seq-IBD 0.85 to 0.87; without it: comparator 0.96 to 0.98. The passive monitor falsely attributes controllability to confounded distractors; the interventional arm does not. This is round 5's +0.19 to +0.24 benefit, seen again in round 6's secondary.
- **Interventions do not buy adaptation.** On tracking loss of a controlled channel, a passive delay-aware covariance monitor equals or beats interventional probing in every cell (round 6, three of three).
- Family N (five seeds, wide intervals): seq-IBD 0.84 against comparator 0.73 at τ = 0; the comparator floor fails there. Reproduction target only.

## 4. Positions on the §L open questions (three of three)

n_lost ≥ 2: yes, by changing the event or topology (an actuator whose loss costs ≥ 2 channels including a downstream one; raise H to τ_max + 2), never by rejection sampling against the outcome. The 0.85 floor: replace the AUC floor by the per-episode probability that every lost channel ranks strictly below every retained channel.

## 5. Rejected or judgment calls

Gemini GM6-06 (the charged prefix "penalises" seq-IBD): the charge is the decision D-11.5 took deliberately; Codex R6-CX-09's sharper point stands, that equal fresh-start ARL is not equal post-warm-up exposure and a steady-state hazard should be co-reported. Claude's MUT-O1 and MUT-O3 were killed by the gate and are reported as such by the reviewer.

## 6. Decision D-12 (see `decisions-required.md`)

## 7. Process note

Six rounds. The fifth showed the passive arm's change statistic was defective and the event usually changed nothing; the sixth, on the author's repair, showed the repaired primary cannot see the confounder and the repaired passive arm wins the re-posed task. Both times three models agreed to Monte Carlo error, and both times the converged answer was about the question, not the implementations. Two findings are now reproducible and neither is the claim the programme set out to confirm. The next step is a prose question, whether either finding is worth a paper, and it is put to three models before anything else is built.


## Erratum (10 September 2026)
§3 first bullet narrowed the interventional arm's round-6 secondary full-channel AUC to "0.85 to 0.87"; the reviewer outputs give 0.851/0.863 (present/absent) at delay 0 and 0.753/0.751 at delay 2 on N_x = 10, so the range over the four family-L base cells is 0.75 to 0.87, with present and absent differing by at most 0.013 in every cell. The claim that the arm is not degraded by the confounder stands; the range was wrong. Found by the round-9 report review.
