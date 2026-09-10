# Round 6 independent findings — Codex

Date: 7 September 2026. Frozen version: `38d161e762a3de76` (verified with `python3 freeze.py`). Gate environment: Python 3.12.13, NumPy 2.4.4. Gate result: exit 0, 66/66 tests, 47/47 registered mutants killed. This review treated `roadmap-v4.md` plus v4.1–v4.7, contract v3.9, interface v5, comparator v3, sequential-IBD draft 5, the frozen generator/contract references, and the confirmation matrix as normative. Superseded files were not used.

## Reproduction verdict

The complete requested run finished in **17.45 minutes**, with no seed reduction. At the primary offset 500, family-L point estimates were:

| cell | seq-IBD present/absent | comparator present | comparator absent (95% t interval) | benefit (95% t interval) |
|---|---:|---:|---:|---:|
| N_x=10, tau=0 | 0.813 / 0.813 | 0.879 | 0.863 [0.702, 1.023] | -0.017 [-0.045, 0.012] |
| N_x=30, tau=0 | 0.813 / 0.813 | 0.879 | 0.863 [0.702, 1.023] | -0.017 [-0.045, 0.012] |
| N_x=10, tau=2 | 0.687 / 0.687 | 1.000 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] |
| N_x=30, tau=2 | 0.687 / 0.687 | 1.000 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] |

Thus D-10.3 fails in both tau=0 cells, the confounding-benefit lower bound does not clear 0.10 anywhere, and seq-IBD loses to the comparator in all four family-L cells. The full per-offset primary and secondary results, all nine perturbation cells, family N, controls, and `n_lost` are in `report.md`; raw rows are in `sim_frozen.results.json`.

## Findings

### R6-CX-01 — High — the stated null law for Δ_c is not the closed-loop null law

- **Claim attacked:** Comparator §3.3 says whitening by the fit-split action covariance makes `Δ_c²` approximately `χ²_q`, with residual standardisation supplying unit scale.
- **Evidence:** For `x_i = rtilde_{i,c} atilde_i`, the covariance of `sqrt(n) mean(x_i)` is a long-run covariance, `Σ_lag Cov(x_i,x_{i+l})`. The specified whitener instead uses only `E[atilde atilde']`. Equality requires conditional homoskedasticity, independence of residual and action, and no serial dependence. None holds by construction under the feedback policy: actions and lag slots are autocorrelated, adjacent 500-step windows share observations, clipping induces heteroskedasticity, and family N is nonlinear. Standardising the marginal residual variance cannot remove `E[rtilde² atilde atilde'] - E[atilde atilde']` or the HAC terms. The spec itself concedes the innovations are neither independent nor Gaussian, but this also invalidates the claimed covariance, not merely the chi-square tail calibration. Because the raw primary compares Δ magnitudes across channels, channel-dependent null scale can change the ranking even though no p-value is used.
- **Fix:** Estimate a per-channel long-run covariance of `rtilde * atilde` on the fault-free instance split (fixed bandwidth/kernel chosen without outcome labels), or empirically standardise each channel's Δ against its own fault-free distribution. Add a closed-loop null test by channel type and lag, not only a pooled median/max check.
- **Fix type:** estimand-preserving method/spec/code/test change.

### R6-CX-02 — High — the interface cannot realise the comparator's fit hierarchy

- **Claim attacked:** Interface v5 says one estimator object is constructed per `(cell, instance_seed, episode_seed, confounder, arm)`, fitted artefacts survive episodes only through `configure`, and `fit_predictor` is called once per `(cell, instance_seed, arm)`. Comparator §1.1 says β and all predictor artefacts are fitted once per instance and reused for four scored episodes.
- **Evidence:** `configure` has only regime, calibrator, and alarm-reference fields; it has no predictor-artifact field. A per-episode comparator object therefore either (i) calls `fit_predictor` four times, contradicting “once”, or (ii) cannot receive β, μ, σ, l, `W_a`, and the degeneracy mask fitted by another object. Sequential IBD needs a fresh per-episode RNG object, but the passive comparator does not; one construction rule was made to cover incompatible lifecycles.
- **Fix:** Define a per-instance fitted model object plus an explicit `new_episode(episode_seed, probe_rng_seed)`/`reset` state, or include a typed, hashed predictor-artifact bundle in `configure`. Add a black-box test spanning two scored episodes.
- **Fix type:** interface/spec/code/test correction; blocking for three literal independent implementations.

### R6-CX-03 — High — the episode registry's ARL extension collides with reserved IDs

- **Claim attacked:** Sequential-IBD §7 says ARL ids 500–899 extend upward from 900 if `n > 400` and “never overlap any other set”; both specs say all fitting ids are disjoint from generator `RESERVED_EP={996,997,998,999}`.
- **Evidence:** The specified cap permits as many as `floor(2,000,000 / 3000)=666` IBD streams. At `n=497`, the consecutive extension includes ep 996; at `n=500` it includes all four reserved oracle ids. From ep 900 it also overlaps comparator predictor ids 900–919, contrary to the cross-spec disjointness premise if the registry is global. Separately, comparator §1.1 reserves only 3000–3399 (`≤400`) although D-2a requires `n` to grow above 400 when dispersion demands it; the comparator gives no legal extension. These are outcome-relevant RNG collisions because the generator keys every noise stream by episode id.
- **Fix:** Allocate non-overlapping, arm-namespaced ranges sized to the cap (for example IBD ARL 10,000–10,665 and comparator ARL 20,000–20,665), state whether cross-arm reuse is intended, and gate the complete maximum-size registry against `RESERVED_EP` and `ep+100000` burn-in keys.
- **Fix type:** specification/registry/test correction.

### R6-CX-04 — High — the primary and 0.85 floor are dominated by a one-channel lattice

- **Claim attacked:** Contract §G/D-10.3 treats a lower 95% bound ≥0.85 as a per-cell competence test after moving the AUC from 24–44 channels to the 4–6-channel pre-event support.
- **Evidence:** The generator deliberately makes actuator 0's dominant component uniquely dependent on actuator 0. In the development reproduction, `n_lost` is usually 1 (full distribution in `sim_frozen.output.txt`). With one negative and 3–5 positives, per-episode AUC moves in jumps of 1/3, 1/4, or 1/5 (and half-jumps for ties); 0.85 lies between attainable points. The nominal floor is therefore effectively a near-perfect-rank requirement whose sampling behaviour changes with `pre_n` and `n_lost`, not the competence threshold originally justified on the full-channel AUC.
- **Fix:** Re-derive the floor by simulation under the new support sizes and report it stratified by `(pre_n,n_lost)`. **Opinion:** CL-4 should require `n_lost >= 2` and at least three retained channels for confirmatory instances; otherwise the primary hinges on one deliberately dominant coordinate. If that changes the target population too much, replace the AUC gate with an instance-level pairwise retained-minus-lost rank estimand whose precision target is explicitly powered.
- **Fix type:** design/contract/generator change; requires a new freeze.

### R6-CX-05 — High — the below-chance static control exposes outcome construction bias

- **Claim attacked:** The primary is presented as a neutral test of adaptation, with the static pre-event loading vector retained merely as a descriptive control.
- **Evidence:** CL-4 constructs the event target to be the dominant body component and removes alternative paths. A competent pre-event structural score should rank precisely that channel highly, so its post-event primary score is systematically below chance. This is not evidence that static methods are misleading in a naturally sampled loss; it is a consequence of choosing the lost coordinate by its pre-event effect. The same construction also gives the covariance comparator an unusually large lost-actuator coefficient, making change easier to detect. The reproduced static-control AUC is reported in the captured output.
- **Fix:** Balance or randomise the lost actuator/channel over the pre-event-effect rank (subject to nonempty loss), and report results by lost-channel effect quantile. Keep both controls: channel-constant (must equal 0.5) and static vector (diagnostic), but do not describe the latter's below-chance result as generic adaptation evidence.
- **Fix type:** generator/design change. The interpretation that this would concern a referee is an opinion; the mechanical anti-correlation is not.

### R6-CX-06 — Medium — “no outcome-dependent tuning” is false as written

- **Claim attacked:** Comparator header/§11 says there is no outcome-dependent tuning clause and presents `lambda_rel=1e-4` as a conditioning guard.
- **Evidence:** Comparator §11 row 8 and §14 disclose that 1e-4 was the best of `{1e-4,1e-2,1}` on round-5 AUC. The old score is superseded, but β and its residuals feed both the new covariance statistic and the retained loading, so the selection is not independent of current outcomes. Moreover `kappa_min` and `Delta_cap` are simultaneously labelled `[prov]` and “frozen” pending a pilot that reports performance-adjacent behaviour. Sealed confirmation seeds prevent direct confirmatory leakage, but do not make development-time outcome selection disappear.
- **Fix:** Say plainly that λ was development-outcome-selected and locked before confirmation. For future constants, use outcome-blind numerical criteria (condition number, truncation stability, cap-hit rate only), with the rule frozen before any AUC is computed; otherwise use nested development/validation instances.
- **Fix type:** disclosure plus tuning protocol correction.

### R6-CX-07 — High — family N certification is finite-horizon evidence, and the gate misses its full-state requirement

- **Claim attacked:** T-L9b certifies family N boundedness/stationarity and the gate's 47-mutant result supports the frozen generator.
- **Evidence:** `boundedness_certificate` is a finite 32-chain/20,000-step screen, not a boundedness proof or an invariant-distribution certificate. Four group means can agree while chains mix slowly or share bias; the absolute 0.05 tolerance has no uncertainty calculation despite disclosed stationary offsets up to order 40. The non-negative `kappa * b^2` term creates a nonzero operating point, so the saturated `tanh(Ba)` response to `+e_k` and `-e_k` need not be opposite; this directly attacks the IBD sign contrast, not just calibration. More concretely, `surviving_mutant_family_n_scope.py` changes the bound from all `z` to only the b/d blocks, violating contract §0's `||z||<=100 at every step`; the frozen gate still exits 0 (captured output). No `T-IBD-*` implementation test runs, so family N's acknowledged nonlinear sign-asymmetry is also untested end to end.
- **Fix:** Assert the max separately for b,d,w,x against a fixture that makes each block violate the bound; add independent-chain uncertainty/mixing diagnostics and the specified family-N exchangeability test; label T-L9b an empirical stress certificate, not boundedness certification.
- **Fix type:** claim/spec/test hardening; generator mutant added.

### R6-CX-08 — Medium — the perturbation set still leaves a configuration choice

- **Claim attacked:** Contract §0 says the perturbation set is “coupling × {0.5,1,2}, noise × {0.5,1,2}” and the round-6 exit condition expects three implementations to agree without choices.
- **Evidence:** Neither the contract nor `confirmation-design.csv` says whether this is a 3×3 Cartesian grid or two one-factor sweeps, nor which `(family,N_x,tau,confounder)` base is perturbed; the CSV has no coupling/noise columns. This implementation chose the full 3×3 Cartesian grid at family L, `N_x=10,tau=0`, with both confounder conditions. Another literal implementation can choose all four base cells or six one-factor points.
- **Fix:** Materialise every perturbation row in a frozen CSV with family, N_x, tau, coupling, noise, confounder, instance seed, and episode seeds.
- **Fix type:** registry/design-file correction; this is a genuine choice left by the specs.

### R6-CX-09 — Medium — fresh-start ARL equality does not equal equal post-warm-up exposure

- **Claim attacked:** D-11.5 says charging the 502-step IBD prefix makes both arms face the same exposure at matched `ARL_0=1000`.
- **Evidence:** IBD cannot count an alarm before t=542, so a mean run length of 1000 allocates only about 458 mean steps beyond its structural floor. The passive arm can alarm from t=0. Matching the two fresh-start means therefore forces different post-eligibility hazards and different false-alarm probabilities near the event at t=1000. The rule honestly charges cost, but it does not make the alarm processes comparable. Per-instance calibration magnifies the cost to about 9.6e7 steps for IBD across the four base cells and confounder conditions, before the comparator; the contract no longer says what to do when only one arm hits the cap beyond the partial-order reporting fallback.
- **Fix:** Preserve fresh-start ARL as the cost-accounting endpoint, but co-calibrate/report steady-state or conditional post-warm-up hazard and false-alarm probability in the event window. Do not call fresh-start ARL alone “same exposure.”
- **Fix type:** analysis/reporting addition. The recommendation to add a steady-state endpoint is opinion.

## Attacks that failed

- I tried to invalidate the lag attribution by tracing the generator queue and observation indexing. It holds: a probe at `t_p` first reaches `o[t_p+tau+1]`; the comparator's causal coefficient is in lag slot 0 at tau=0 and lag slot 2 at tau=2, while neighbouring slots can light up through closed-loop autocorrelation.
- I tried to find present/absent common-random-number drift. The generator's body/action process is unchanged by `G[:] = 0` because policy feedback reads body channels only, and the probe seed intentionally excludes confounder status. Separate fits are still required because the observed x regressors differ.
- I tried to break the offset-1000 read. Contract §G and both arm specs consistently select comparator t=1999 and IBD epoch t=1982; no fabricated t=2000 transition is needed. The 17-step cross-arm gap is real but declared.
- I tried the obvious pre-event-AUC mutants (all-channel scoring, inverted positives, and no tie credit). The frozen gate rejects all three.
- I tried to treat the static-vector score as mathematically required to equal 0.5. Contract v3.9 has already corrected that overstatement: only a channel-constant vector is forced to chance.

## Choices required during reproduction

- **Interval procedure (finding R6-CX-04):** the contract says only “95 percent intervals clustered by instance.” I averaged the four episode values within each instance and used a two-sided t interval over the 10 (family L) or 5 (family N) instance means, with 9 or 4 degrees of freedom. Perturbation cells have one instance and therefore a point estimate but no interval. Sidedness, interval family, and the within-cluster summary were not specified.
- **Perturbation shape/base (finding R6-CX-08):** full 3x3 Cartesian coupling/noise grid at family L, `N_x=10`, `tau=0`, both confounder conditions.
- **Object lifecycle (finding R6-CX-02):** I followed comparator §1.1 by fitting one comparator per instance/condition and reusing its frozen artefacts across the four fresh scored episodes, rather than following interface v5's literal per-episode construction sentence.
- **Scope cut:** alarm-reference fitting, isotonic calibration, threshold calibration, and arm 3 were not run. None enters the requested primary AUC, secondary AUC, controls, `n_lost`, D-10.3 floor, or confounding benefit. The estimated ARL work is attacked analytically under R6-CX-09. This is a declared scope choice, not a statistic choice.

No development instance or episode seeds were reduced.

## New-category statement versus rounds 1–5

R6-CX-01 (incorrect closed-loop covariance/null geometry), R6-CX-02 (impossible cross-episode object lifecycle), R6-CX-03 (ARL extension colliding with reserved episode IDs), R6-CX-07's full-state T-L9b surviving mutant, and R6-CX-08 (unmaterialised perturbation design) are new categories rather than restatements of the round-1–5 issues listed in the two method specs. R6-CX-04/05/06/09 extend concerns already disclosed in draft 5 or inherited from round 5, but add an explicit position or a new consequence rather than claiming novelty.

## Reproduction files

- `sim_frozen.py`: independent implementation of both confirmatory arms.
- `sim_frozen.output.txt` and `sim_frozen.results.json`: captured execution and machine-readable rows/summaries.
- `gate.output.txt`: pinned gate output.
- `surviving_mutant_family_n_scope.py` and `surviving_mutant.output.txt`: isolated mutant and gate run.

The simulation's perturbation-grid interpretation is disclosed under R6-CX-08. No confirmation seeds were derived or inspected.
