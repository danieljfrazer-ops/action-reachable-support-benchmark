# Round 6 adjudication — Codex

Date: 7 September 2026. This file was written only after `sim_frozen.py` and the independent findings were drafted. I then read Opus's findings/adjudication and Gemini's completed implementation/captured report. At adjudication time Gemini had not created separate `findings.md` or `adjudication.md` files, so no nonexistent prose is attributed to it.

## Outcome

**Round 6 does not meet the contract §L exit condition.** The point estimates reproduce across implementations, but the criterion they reproduce is structurally incapable of showing the required confounding benefit, the passive comparator beats sequential IBD on family L, and the comparator competence floor fails at tau=0. These are design outcomes, not Monte Carlo disagreement.

## Cross-review reproduction

The three implementations agree on the decisive family-L offset-500 point estimates (table completed from the captured runs):

| Cell | seq-IBD present | comparator present | comparator absent | confounding benefit |
|---|---:|---:|---:|---:|
| L, N_x=10, tau=0 | 0.813 | 0.879 | 0.863 | -0.017 |
| L, N_x=30, tau=0 | 0.813 | 0.879 | 0.863 | -0.017 |
| L, N_x=10, tau=2 | 0.687 | 1.000 | 1.000 | 0.000 |
| L, N_x=30, tau=2 | 0.687 | 1.000 | 1.000 | 0.000 |

Present/absent seq-IBD is identical, not merely close. The generator gives `G` only to the x distractors; x is not an ancestor of body/action, and no x channel lies in the pre-event support. D-11.1a therefore removes the confounder from the set ranked by the primary. Any residual comparator present/absent difference comes through fitting a multivariate ridge with x regressors, not through a changed controlled-channel stream. The required lower bound above 0.10 is unattainable under this generator/primary combination.

## Adjudicated findings

1. **Accept as critical:** the confounding-benefit exit condition is orthogonal to the confounder after D-11.1a. Fix the endpoint: use the false-support co-primary for the confounding claim, or change the generator so some confounded channels enter the pre-event support. Prefer both, with adaptation and attribution named as separate endpoints.
2. **Accept as critical:** R0-present fails and the passive comparator wins in all four family-L base cells. This invokes D-10's negative-result/fallback branch; it is not a reason to weaken the comparator or tune the IBD arm on these development outcomes.
3. **Accept as high:** D-10.3 fails at tau=0. The point estimate is 0.863 but the clustered lower bound is below 0.85. At tau=2 all instance values are 1.0; because the contract never fixes the interval estimator, treating a zero-width empirical bootstrap/t interval as proof of population competence is not defensible.
4. **Accept as high:** CL-4 creates an essentially one-coordinate estimand. `n_lost=1` on 32/40 family-L draws and 2 on 8/40; tau=2 always has four pre-event channels. I agree that `n_lost>=2` is desirable, but it should be achieved by redesigning and balancing events, not outcome-conditioned rejection sampling. Raise H if downstream loss is meant to be tested at tau=2.
5. **Accept as high:** the static vector exposes generator bias. A pre-event loading ranks the deliberately dominant lost coordinate high and scores below chance; negating it creates an event-blind above-chance arm. Add both static orientations as controls and balance lost-channel pre-event rank.
6. **Accept as high:** episode-id extension collides with comparator fitting and `RESERVED_EP`. This was found independently in R6-CX-03 and R6-OP-06. Allocate explicit disjoint maximum-size ranges.
7. **Accept as high:** the frozen CSV still says `shared_per_cell` while D-11.6 says per instance, and `instance_seed` ambiguously means a design index or certified sub-seed. Regenerate it with `instance_index` and runtime `certified_sub_seed` separated.
8. **Accept:** aggregate ARL cost is no longer bounded by the apparent 2e6 cap. Add a total programme budget and scope the descriptive alarm comparison down by default.
9. **Accept my R6-CX-01:** Δ_c's chi-square/null-geometry claim is not valid under closed-loop serial dependence and heteroskedasticity. The other reviews' observed fault-free AUC near 0.60 in every cell is consistent with channel-dependent null scale. Use a long-run covariance or empirical per-channel null normalisation.
10. **Accept my R6-CX-02:** interface v5's per-episode construction and configure bundle cannot transport the comparator's per-instance predictor artefacts. Add an explicit per-instance fitted model plus episode reset, or a predictor-artifact bundle.
11. **Accept family-N caution:** T-L9b is a finite stress screen, its label zbar estimator differs from the batch object being certified, and the IBD family-N sign symmetry is knowingly false in principle. Keep N outside the gate until end-to-end arm tests and uncertainty/mixing checks exist.
12. **Accept perturbation ambiguity:** all reviewers who ran it chose a 3x3 grid at L/N_x=10/tau=0, but the frozen files do not specify that. Agreement by convention does not remove the choice; materialise the rows.

## Mutants

- Codex mutant: restrict family-N `max_abs_z` to b/d, ignoring w/x. It violates the full-state T-L9b bound and the full frozen gate exits 0.
- Opus mutant: make `auc_pre_event_support` rank over `pre | post`. It survives because every gate fixture has `post` as a subset of `pre`; it fails for support-gain events.

Both are valid and non-duplicative. Add block-specific T-L9b violation fixtures and a primary-metric fixture with `post` not a subset of `pre`.

## Differences resolved

- Interval bounds differ because the contract says only “clustered by instance.” Codex used a two-sided t interval over four-episode instance means; Opus used a percentile cluster bootstrap; Gemini used its own clustered implementation. Point estimates agree. The absence of a fixed interval procedure is itself a high finding because the 0.85 verdict can depend on it.
- **Gemini's IBD secondary summaries are wrong at offsets 200 and 500.** In its `sim_frozen.py`, lines 438–439 read `ibd.secondary_support()` only after the entire 2,000-step episode has finished, inside the later loop over offsets. The same final (offset-1000) vector is consequently assigned to all offsets. Contract/interface say IBD secondary equals the raw `a_c` vector as of each offset. Codex and Opus captured it at each read and agree (for example L/N_x=10/tau=0/present: 0.817, 0.851, 0.871 at offsets 200, 500, 1000); Gemini reports 0.871 for the offset-500 summary. This does not affect Gemini's correctly captured primary or the exit verdict, but its secondary table should not be used.
- The 17-step cross-arm offset gap is correctly specified by contract §G/comparator §4.5. Draft-5 text saying “up to 18” is stale, not a computational disagreement.
- The family-N results are reproduction-only and do not rescue the family-L exit failure.

## Recommended decision

Stop the current design-review exit and do not tune either arm. Re-freeze only after: separating adaptation from confounded false-support claims; redesigning CL-4/event balance and the competence criterion; fixing registry/interface/CSV contradictions; specifying inference; and adding implementation-level gate coverage for both arms. The current results are useful as a negative design result, but they do not support the planned superiority claim.
