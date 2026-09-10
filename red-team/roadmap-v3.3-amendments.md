# Roadmap v3.3: amendments after the second Gemini red team (gemini-v3.2/)

Date: 6 September 2026. `roadmap-v3.md`, `v3.1`, and `v3.2` amendments stand except where amended here. IDs C1 to C8 map to Gemini findings H1 to H8 in `gemini-v3.2-assessment.md`. This is the plan that goes to execution.

## C1. Primary estimand, discrete form (H3; replaces B1)

Detection delay is an integer. For each estimator m and threshold θ, record the empirical median delay d̂_m(θ) and mean run length to false alarm ARL_m(θ). Define the Pareto envelope log ARL*_m(d) = max{ log ARL_m(θ) : d̂_m(θ) ≤ d } over integer d. The primary scalar estimand is

Δ_pAUC = (1 / (d_max − d_min + 1)) Σ_{d = d_min}^{d_max} ( log ARL*_A(d) − log ARL*_B(d) ),

with d_min = max(min d̂_A, min d̂_B) and d_max = min(max d̂_A, max d̂_B). Disjoint supports: report the boundary difference and declare dominance. Smallest effect of interest δ = ln 2. Decision rules in A5 apply. Reference implementation and a worked case with non-unique thresholds: `executable-proofs/gemini_v32_checks.py`.

## C2. Primary contrast across misspecification regimes (H2; replaces B2)

In a well-specified linear system, a classical residual detector (CUSUM or GLR on model innovations) detects an actuator loss at zero probe cost and is the reference, not a competitor. Interventional probing earns its cost only where passive monitoring fails. The primary contrast is therefore run across **three predeclared regimes**:
- R0 clean: well-specified model, open loop. Expected: classical detector dominates; this is the sanity anchor.
- R1 misspecified: the observer's model omits the nonlinearity of family N or has drifted parameters. Expected: residual detectors false-alarm on distractor residuals; interventional detection holds.
- R2 masked: a feedback controller compensates for the fault so the tracking residual stays small. Expected: passive residual detectors miss or delay; probing exposes the lost authority.

Confirmatory hypothesis H1: Δ_pAUC(sequential IBD vs classical CUSUM/GLR) is ≤ 0 in R0 and ≥ δ in R1 and R2, at the declared probe budget. Secondary descriptive finding: support correctness (p_c on distractor channels) under confounding, where observational methods fail regardless of regime. Reviewers get the regime boundary at which probing becomes worth paying for.

## C3. Tier T2 scope fence (H1, H5)

Paper 1's T2 is **CartPole and inverted pendulum only**: single-actuator systems where losing the actuator empties the support unambiguously and reachability is not confounded by joint coupling. Acrobot (one actuator, two coupled links), Reacher and HalfCheetah are deferred to Paper 2, where actuator loss is classified as an R-change and world models are the object of study.

Policy stability (H5): the default T2 policy is trained with additive action noise and mild domain randomisation; the confounding injection W_u u_t is bounded so that median episode length under the default policy stays above a declared floor (for example 500 steps for CartPole); episodes that terminate before a change event are excluded and the exclusion rate reported. The observational correlation floor ρ_min is set after the stability bound, not before.

## C4. Baselines pruned to five for Paper 1 confirmation (H6)

1. Random. 2. Temporal correlation. 3. Forward-model residual. 4. Sequential IBD (randomised probes, two-sample tests with FDR, re-probing schedule). 5. Classical CUSUM/GLR on model innovations.
Retained as exploratory appendix material, not confirmation: one Bayesian model-informed reference (built in 0B), mutual information. Deferred to Paper 2: standalone inverse-dynamics attribution. Cut: auxiliary-signal active FDI (redundant with sequential IBD at this scale).

## C5. Environments for Paper 1 (H6)

SCM family L, SCM family N, CartPole, inverted pendulum. Four, not seven.

## C6. Tier T3 compute (H7)

Paper 2 world-model confirmation runs on a rented GPU with a declared budget (order of tens of dollars). The Air is for development and estimator sweeps only.

## C7. Packaging (H8)

Robust-Gymnasium compatibility is an optional extra (`pip install boundary-bench[robust]`), not a core dependency. Core depends on numpy and gymnasium only.

## C8. Schedule (H6; replaces B8)

| Milestone | Target |
|---|---|
| Stage 0A: SCM contract v2.2, families L and N, invariants E1 to E5 with mutants, four baselines | 26 Sep 2026 |
| Phase S: one-week internal shakedown | 4 Oct |
| Stage 0B: sequential metrics with discrete Pareto Δ_pAUC, CUSUM/GLR detector, calibrator, one Bayesian reference | 24 Oct |
| Tier T2 MVP: CartPole and pendulum wrappers, stability tuning | 7 Nov |
| Paper 1 pilot: threshold sweeps on four environments and three regimes; freeze [d_min, d_max] | 21 Nov |
| Confirmation: 240 primary runs plus a reduced 360-run response surface | 15 Dec |
| Write-up and arXiv | late Jan 2027 |
| Paper 2 (T3, coupled MuJoCo, world models) | Feb to May 2027 |

Review load with this fence: about 18 gate reviews over 20 weeks, within the one-per-week budget.

## Unchanged

D1 to D8; B3 (benchmark shape, fenced as above), B4 (Paper 2), B5 (Phase S internal), B6 (serialisation), B7 (executable proofs), B9 (Paper 3 conditional); A2, A3, A5, A6, A8, A9.
