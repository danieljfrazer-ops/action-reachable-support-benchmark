# Assessment of the second Gemini red team (gemini-v3.2/)

Date: 6 September 2026. Verdict received: **conditional go with mandatory scope fencing**; Stage 0A cleared to code from contract v2.1 minus one contradiction. Checks executed in `executable-proofs/gemini_v32_checks.py`.

## Disposition

| Finding | Executed check | Disposition |
|---|---|---|
| H1 joint coupling in articulated simulators keeps a lost joint reachable, so "S by wrapper construction" is false for MuJoCo | Linear analogue: with off-diagonal coupling, actuator loss leaves both components reachable at horizon 3 (uncoupled: second component drops out) | **Accept.** This is the physical version of my own contract example K.4. T2 in Paper 1 fenced to single-actuator systems; coupled bodies deferred to Paper 2 with actuator loss classified as an R-change. Contract v2.2 section D notes it. |
| H2 classical CUSUM/GLR at zero probe cost dominates in a well-specified linear system, so the re-aimed primary contrast could report interventional probing as strictly wasteful | Reasoned; consistent with FDI theory | **Accept.** Primary contrast now runs across three regimes: clean (anchor, classical wins), misspecified, and masked by feedback compensation. The hypothesis is the regime boundary at which probing becomes worth its cost. One nuance kept: support correctness on distractor channels fails for observational methods under confounding in every regime; that stays as a secondary descriptive finding. |
| H3 delays are integers and threshold-to-delay is a step function, so a continuous integral is ill-defined | Implemented the discrete Pareto envelope; overlapping case gives Δ = 2.50 over delays 4..8; disjoint case handled | **Accept.** Amendment C1; reference implementation in the proofs folder. |
| H4 contract v2.1 line 100 still allows dummy constants, contradicting line 103 | grep confirmed both lines | **Accept; my error in the v2.1 patch.** Fixed in contract v2.2. |
| H5 injected confounding noise can destabilise a control policy and truncate episodes | | **Accept.** Robust policy training, bounded injection, episode-length floor, exclusions reported. |
| H6 twelve baselines across seven environments cannot be reviewed by late January | Gemini's review-count table (33 items at one per week) | **Accept.** Five baselines, four environments. About 18 reviews. |
| H7 T3 compute belongs on a rented GPU | | **Accept.** Already my recommendation; now a declared budget line. |
| H8 Robust-Gymnasium as an optional extra | | **Accept.** |

## Where Gemini is right that I over-corrected

Between v3.1 and v3.2 I answered "too small" with "too big": three tiers, twelve baselines, seven environments, packaging and a leaderboard, all for one paper on one laptop with one reviewer. Gemini's scope fence keeps the benchmark contribution and the FDI-to-causal-ML bridge, cuts the parts that cannot be ground-truthed (coupled bodies) or reviewed (seven extra baselines), and moves them to Paper 2 where they belong. The fenced Paper 1 is still the benchmark Daniel wanted: exact tier plus a control tier, five orthogonal methods, three regimes, released as a package.

## Where I hold a nuance

Gemini's H2 says classical FDI is "optimal" and interventional probing "strictly inferior" in the clean regime. True for the alarm. Not true for the support estimate: a residual detector on the body says the body changed; it does not say whether the distractor is controllable, and under confounding an observational model of the distractor is wrong in every regime. So the clean regime is a sanity anchor for alarms and still a failure case for observational support estimation. Both findings go in the paper.

## Net position

Direction unchanged since v3.2. Scope fenced. Contract v2.2 is the build target. No open decisions for Daniel beyond confirming the fence (single-actuator T2, five baselines), which I have adopted as default.
