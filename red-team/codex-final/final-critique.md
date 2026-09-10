# Final critique of roadmap v3

**Review date:** 6 September 2026  
**Scope:** `synthesis.md`, `timing-and-shakedown-value.md`, `stage-0a-contract-draft.md`, and `roadmap-v3.md`, read in that order, with live checks where external claims are used.

## Executive judgment

**Go with changes. Do not start implementation from the current Stage 0A contract.** V3 is substantially stronger than both earlier roadmaps: it has a plausible benchmark contribution, sensible modularisation, restrained framing and real stop rules. The remaining problem is not the programme’s direction; it is that the first executable contract still contains a coordinate-system contradiction and does not expose outputs for two of its three advertised targets. Fixing that now is cheap. Discovering it after pilot data would invalidate results.

The severity labels below are judgments, not empirical facts.

## High-severity findings

### F1. A sensor swap both changes and does not change `S_t`

**Claim attacked.** `S_t`, `M_t` and `P_t` are separable ground-truth targets, and a sensor swap changes only `P_t` while leaving `S_t` and `M_t` unchanged.

**Evidence.** The contract defines `S_t` as a subset of **observation dimensions** whose future distribution is changed by intervention on action. If a controllable latent variable moves from observed channel 2 to channel 7, the observation-space support moves from 2 to 7. Thus observation-space `S_t` changes with `P_t`. The “sensor swap changes `P_t` only” invariant can hold only for a support defined in latent coordinates, not for the stated observation-coordinate target.

**Fix.** Define at least:

- `S^latent_{t,H}`: causal support over latent variables; and
- `S^obs_{t,H}`: causal support over delivered observation channels, derived from the latent support and the observation map.

State which one every estimator predicts and every metric scores. If Paper 1 is about the boundary available to an agent, `S^obs` should normally be primary. Rewrite the swap and dropout invariants accordingly.

### F2. `M_t` and `P_t` are not yet identifiable, typed estimands

**Claim attacked.** The signed Jacobian `M_t` and “permutation and gain matrix” `P_t` give precise, independent labels across the proposed dynamics and sensor events.

**Evidence.** A signed Jacobian is state-, action- and horizon-dependent in nonlinear dynamics; it can be zero at saturation and undefined at discontinuities. The contract does not specify an evaluation point or reference distribution. `P_t` mixes assignment, permutation, gain and dropout, and padding makes it potentially rectangular. Copied sensors make exact channel identity non-identifiable when copies are exchangeable. Frobenius error is sensitive to scale and label permutations.

**Fix.** Define `M_{t,h}(z,a)=∂E[b_{t+h}|do(a_t=a),z_t=z]/∂a`, the set of horizons, derivative convention and evaluation distribution; alternatively score a finite interventional response function. Split `P_t` into an assignment matrix plus gain and availability masks. Score equivalent copies as equivalence classes or with an explicitly frozen matching rule. Normalise mapping error and add uncertainty targets.

### F3. The estimator API cannot support the advertised three-target paper

**Claim attacked.** Paper 1 estimates changing support, action-effect mapping and sensor identity.

**Evidence.** The mandatory Stage 0A interface returns only a per-observation-dimension probability of controllability plus an optional generic change alarm. `M_t` output is optional (“where an estimator produces one”), and no `P_t` output or identity metric is specified. This permits a nominal three-target comparison in which methods are scored only on `S_t`.

**Fix.** Either narrow Paper 1 to `S^obs` and change detection, or require a target-typed interface: support probabilities; an action-effect posterior/response with uncertainty; identity-assignment probabilities; and a typed alarm or separate stopping time for each target. No primary metric should be optional.

### F4. Several Stage 0A invariants are untestable as written, and some can pass tautologically

**Claim attacked.** All seven invariants form an executable correctness gate.

**Evidence.** In stochastic systems, “unaffected under action” and “randomised actions affect exactly `S_t`” are distributional statements, not exact sample assertions. Finite tests cannot prove absence of a causal path; weak effects, cancellation, saturation or inadequate action coverage can make a real path invisible. “Mapping changes numerically” has no norm or tolerance. Byte-identical results across machines are generally too strong for floating-point/BLAS execution, while two identical same-machine runs are too weak to establish portability. Evaluator privacy inside the same process is only an interface convention, not isolation. Most seriously, if the generator, oracle and invariant tests reuse the same mistaken support-transform function, they can agree perfectly and all be wrong.

**Fix.** Separate structural tests from statistical tests. Inspect an independently constructed causal graph/Jacobian oracle for path claims; use paired common random numbers and predeclared tolerances/power for distributional checks; add deliberately broken “mutant” generators that each test must reject. Require same-host bitwise determinism and cross-host numerical/configuration equivalence. Put evaluator ground truth in a separate process/package and test that the candidate receives serialised observations only.

### F5. Paper 1’s primary estimand, SOEI and fractional design are not frozen

**Claim attacked.** The pilot leads to a clean, adequately powered confirmation of one primary interventional-versus-observational contrast.

**Evidence.** “Interventional estimator versus observational estimator” does not name an exact method pair or aggregation. Selecting the contrast and operating point after pilot inspection creates a winner’s-curse path unless the rule and data split are fixed in advance. “False-alarm rate at matched detection delay” requires a threshold sweep or explicitly defined operating curve, not one threshold. The smallest effect of interest (SOEI) has no units or value. The proposed full grid has 540 base cells (`6×5×3×2×3`), or 21,600 runs at 10 seeds, two dynamics families and two held-out schedules before threshold/calibration multiplicity. Calling it fractional does not define a run matrix, resolution or alias structure. NIST’s design guidance stresses that resolution and aliasing determine whether main effects and interactions can be interpreted; low-resolution fractions are screening designs, while response-surface/interaction claims need stronger designs ([NIST on fractional factorial resolution](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3345.htm), [NIST on alias structure](https://itl.nist.gov/div898/handbook/pri/section3/pri3344.htm)).

**Fix.** Before pilot execution, name the exact primary method pair, target, change family, cost regime and scalar estimand—for example, log average-run-length ratio at a predeclared median detection delay, or partial area under a false-alarm-versus-delay curve. Set the SOEI in those units with a decision rationale. Publish the fractional run matrix, resolution and alias table; protect estimator×target, estimator×distractor and estimator×dynamics interactions. Use pilot data only for variance/sample-size estimation, or use a separate predeclared selection dataset.

### F6. The kill rule’s CI logic is ambiguous and can invert the decision

**Claim attacked.** Redirect if the 95% CI excludes the SOEI on both dynamics families.

**Evidence.** A CI entirely above the SOEI and one entirely below it both “exclude” the SOEI. They imply opposite decisions. The rule does not define the sign of the effect, what happens when only one family clears the threshold, or whether “both” is required for the paper’s generality claim.

**Fix.** Define a signed effect `Δ` so positive is beneficial. Declare superiority if the lower confidence bound exceeds `δ` on both required families; futility if the upper bound is below `δ` on either family if the claim requires both; otherwise label the result inconclusive. Run positive-control gates before confirmation, not as part of the confirmatory decision.

### F7. The evaluator has no genuinely independent ground-truth implementation

**Claim attacked.** Builder/red-team alternation plus tests and Daniel’s sign-off will catch agent-produced errors.

**Evidence.** The same codebase appears to generate worlds, expose oracle labels, calculate metrics and test invariants. A reviewing agent can inspect the same mistaken abstraction and reproduce its assumptions. “Qualitative ordering” against IBD is not a numerical reproduction and can pass when the environment was tuned to make that ordering occur. The evaluator hash is not meaningful protection if the same agents can edit and regenerate both artifact and expected hash. The statistical analysis and ledger also lack an independent reference path.

**Fix.** Have one implementation derive labels analytically from a compact declarative SCM and a separate implementation derive them by exhaustive/finite-difference interventions on tiny cases. Daniel signs off their agreement and stores the confirmation evaluator hash outside the writable experiment tree. Add golden numerical cases, mutant generators, canary leakage tests, metric calculations duplicated in a small reference notebook/script, and reproduction anchors from official prior-art code where available.

### F8. Phase S’s published scope does not fit its two-week box

**Claim attacked.** Five memory families, singletons/pairs/leave-one-out combinations, several budgets, three generator families, multiple baselines, 5–10 seeds and long streams can be built and run in 14 days, with a publishable technical note.

**Evidence.** Five families produce 20 singleton/pair/leave-one-out configurations before budgets, generators, baselines and seeds. The timing memo itself allows one to two weeks for build/run **plus** three to five days for writing, so the advertised two-week box is not end-to-end. Phase S also overlaps Stage 0B and competes for the same two coding agents, one reviewer and one 32 GB fanless laptop. The proposed “effective state size” source describes a utilisation metric for input-invariant and input-varying linear operators, not a universal physical budget across episodic stores, recurrent state and slow weights ([Effective State Size](https://arxiv.org/abs/2504.19561)).

**Fix.** For a true two-week shakedown, cap the confirmatory scope now: three representative families, singleton comparisons plus one predeclared pair, two physical budgets, three development seeds and five confirmation seeds, bounded streams, and one held-out generator. Use total allocated bytes, bytes read/written and update/inference operations as primary budget axes; report effective state size only where mathematically applicable. Publish only if a minimum completeness and validation gate is met; otherwise retain an internal shakedown report. Give an arXiv-quality five-family note four to six weeks.

## Medium-severity findings

### F9. The shared-cause distractor is causally sound, but the contract omits what makes it sound

**Claim attacked.** A shared exogenous cause driving both the default policy and distractor produces an action-correlated but causally action-invariant observation and can be unit-tested by invariant 5.

**Evidence.** This construction is valid in principle. IBD uses essentially the same SCM: an exogenous confounder drives action and a distractor, while intervention on action severs the confounder-to-action link and leaves the distractor distribution unchanged ([IBD abstract](https://arxiv.org/abs/2603.18257), [IBD full text](https://arxiv.org/html/2603.18257)). The draft, however, does not state whether the default policy observes `u_t`, whether `u_t` is independent of agent state and past actions, or how noise is coupled between observational and interventional branches. “Correlated” has no minimum magnitude; “unchanged” has no tolerance. A simulation cannot prove absence of a structural action path.

**Fix.** Freeze explicit equations, for example `u_t∼p(u)`, `a_t=π(o_t,q_t(u_t))+ε_a`, `x_{t+1}=g(u_t,ε_x)`, with no action parent of `x`. State what private cue exposes `u` to the default policy. Test structural parentage directly, then use paired common random numbers to test invariance under `do(a)` and a predeclared confidence/tolerance test. Require a nontrivial observational correlation interval across seeds so the test cannot pass with a nearly zero distractor.

### F10. Structural support and detectable distribution shift are being conflated

**Claim attacked.** Directed-path reachability and “distribution changes under action” are interchangeable definitions of `S_t`.

**Evidence.** A path can exist while a chosen intervention distribution produces a negligible or cancelling effect. Conversely, detectability depends on horizon, excitation and statistic. IBD defines its state-of-interest operationally through future-distribution changes and explicitly relies on stationarity plus faithfulness/statistic sensitivity; it probes fixed horizons rather than proving graph reachability ([IBD full text](https://arxiv.org/html/2603.18257)).

**Fix.** Keep two labels: structural reachability and an effect-above-`ε` operational estimand under a frozen intervention distribution and horizon set. Use the structural label for generator correctness and the operational label for statistical detection scoring. Publish sensitivity to `ε` and horizon.

### F11. Sequential metrics and calibration remain underspecified

**Claim attacked.** Detection latency, false alarms, calibration and support metrics are ready to freeze.

**Evidence.** The contract does not define typed alarms, persistence length, reset after detection, censoring, event matching, or close-event handling. “Average run length or equivalent” leaves room to choose whichever presentation is favourable. Calibration observations are correlated across channels and time, while the held-out calibration split is not defined at generator/schedule/seed level. ECE is highly sensitive to binning and formulation, and can change conclusions across variants ([Nixon et al., *Measuring Calibration in Deep Learning*](https://arxiv.org/abs/1904.01685)).

**Fix.** Predefine one sequential primary metric and stopping rule per target, with threshold-selection data separated from confirmation. Cluster uncertainty by independent episode/seed. Split calibration by whole generator configurations and schedules, report raw and calibrated scores, make log loss/Brier primary, and freeze ECE bins as a diagnostic only. Define task regret only after defining a reward, default policy and intervention accounting; otherwise use step/intervention cost.

### F12. Reintroduction controls reduce but do not isolate cached recognition

**Claim attacked.** ABA/ABC counterbalancing and the morphology-library ablation isolate recognition of a reintroduced morphology from generic faster relearning.

**Evidence.** A second encounter with A differs in exposure count and chronology; persistent optimiser, detector or recurrent state can make A faster without a morphology-specific stored representation. ABC controls order but not similarity or exact-instance recognition.

**Fix.** Equalise dwell times and transition counts; declare which model/optimiser/detector states reset; include `A'`, an unseen morphology matched to A’s structural class, and compare return to exact A against transfer to `A'`. Report recognition latency separately from relearning slope.

### F13. The dates omit the most likely rerun loop

**Claim attacked.** 0A is a 4–7-day task, 0B a 1–2-week task, Phase S a two-week parallel task, and Paper 1 can begin immediately afterward.

**Evidence.** 0A includes two dynamics families, a faithful IBD reproduction, four baselines, seven gates, deterministic replay and an adversarial review. 0B adds three Bayesian variants, a learned model, calibration, several probe regimes and sequential metrics. The agents are builder and red team in each phase, not two independent implementers working at full parallel speed. During simultaneous 0B/S work both are builders, reducing independent review capacity. Daniel’s few-hours-per-day review is on the critical path. The MacBook Air is also a shared compute bottleneck; algorithmic budgets avoid thermal unfairness but do not make two overlapping sweeps finish faster.

**Fix.** Plan 0A as 1.5–2 calendar weeks and 0B as 2–3 weeks including one repair cycle. Add explicit review queues and a rerun reserve of 25–35% after the pilot. Keep the February 2027 Paper 1 target as a planning target, not a promise; late November/December is possible only if the contract is repaired before coding and Phase S is reduced.

**Most likely cause of slip (opinion).** A mismatch among latent coordinates, observation coordinates and evaluator labels will be discovered during the first serious pilot, forcing generator, metrics and baseline outputs to change and invalidating earlier runs. F1 is therefore both a scientific and schedule blocker.

### F14. The workflow lacks change control after freezing

**Claim attacked.** Hashing the evaluator and logging runs prevents post hoc drift.

**Evidence.** V3 does not specify what happens when a bug is found after pilot or confirmation begins, which artifacts a hash covers, whether dependencies/container state are frozen, how partial/failed runs and NaNs enter the ledger, or which cells must be rerun. Agent-produced logs can be internally consistent while silently omitting crashes.

**Fix.** Hash source, configuration schema, environment lockfile, dataset/generator version and metric code. Use append-only manifests with atomic completion markers and explicit failed-run records. Define a change-classification policy: any semantic change to generator, oracle, metric or baseline reruns all affected cells; presentation-only changes do not. Daniel approves exceptions before unblinding confirmation summaries.

### F15. A hostile reviewer would not yet accept the three-target contribution, but the benchmark core is viable

**Claim attacked.** The Paper 1 contribution is ready for a CoLLAs or ICLR-workshop submission as stated.

**Evidence.** In its current form, a reviewer can object that two targets are not obligatorily estimated, synthetic validity depends on self-certified invariants, the primary comparison is selected after a pilot, and the fractional design is undefined. The novelty is an intersection/benchmark contribution rather than a new causal principle, so protocol credibility must carry the paper. The two dynamics families also need to differ structurally, not merely by parameterisation.

**Fix.** Position the paper as a benchmark and failure-map contribution; avoid relying on “self-boundary” language in the technical claim. Repair F1–F7, release executable contracts and golden cases, use two genuinely different dynamics families, and report negative results. On that basis, **opinion:** an ICLR workshop is a reasonable early feedback target and CoLLAs is plausible for a mature paper, but arXiv-first is the right dependency-independent milestone for a solo unaffiliated author.

## Low-severity findings

### F16. H3 is partly guaranteed by comparator construction

**Claim attacked.** All methods degrade under misspecification and the correctly specified Bayesian reference degrades least.

**Evidence.** A correctly specified Bayesian reference is deliberately advantaged on calibration under its own model, and “all degrade” need not hold monotonically for flexible or conservative methods. This is informative benchmarking, not a strong confirmatory scientific hypothesis.

**Fix.** Make H3 secondary/descriptive. Report excess proper score relative to the correctly specified reference, sharpness and failure modes, without requiring every method to degrade.

### F17. The shakedown is a genuine but conditional contribution

**Claim attacked.** Phase S is either merely infrastructure or unquestionably a publishable novelty.

**Evidence.** A limited live search found close adjacent systems—Effective State Size, MEMTIER’s tripartite memory architecture ([MEMTIER](https://arxiv.org/abs/2605.03675)) and HOLA’s exact-cache/recurrent hybrid ([HOLA](https://arxiv.org/abs/2607.02303))—but not the exact matched-budget, cross-family table under hidden per-item hazard schedules described by V3. Absence from a bounded search is not proof of absence.

**Fix.** Call it a small empirical methods contribution conditional on a documented final prior-art pass and complete matched-budget evidence. Its strongest immediate value is shakedown of ledgers, seed discipline, budget accounting and thermal scheduling; it does not validate the causal ground-truth machinery of Stage 0A.

## Attacks that failed

1. **“The action-correlated distractor is causally invalid.” — Failed.** A shared exogenous cause can create observational action correlation without an action-to-distractor causal path. IBD uses the same causal pattern. The draft needs explicit equations and stronger tests, but the construction itself is sound.

2. **“V3 ignored the earlier C1–C20 critique.” — Failed.** Nine items are resolved at roadmap level, ten are partly resolved and one is misapplied; all twenty are visibly engaged. The remaining failures are mostly incomplete operationalisation, not disregard.

3. **“The memory shakedown has no research value.” — Failed.** A rigorously matched cross-family table under hidden item-specific volatility would be useful and appears not to be directly supplied by the adjacent works checked. The full proposed scope, not the core question, is the problem.

4. **“The two-week shakedown can produce nothing useful.” — Failed.** Two weeks is credible for a reduced internal benchmark and a decision-quality report. It is not credible for the complete five-family publishable design plus write-up.

5. **“Paper 1 must retain self-awareness or consciousness framing to be motivated.” — Failed.** The orthogonal capability axes are more coherent and testable. Nothing in the contribution requires a consciousness claim.

6. **“A solo unaffiliated author should not target CoLLAs or an ICLR workshop.” — Failed.** Affiliation is not a scientific objection. The practical risks are protocol credibility, compute/review capacity and live venue eligibility; arXiv-first and live checks address the dependency risk.

7. **“A fanless laptop makes fair experiments impossible.” — Failed.** Algorithmic budgets, thermal logging and serialised runs can preserve comparison fairness. They affect elapsed time and scheduling, which must be budgeted honestly.

## Source-check note

Live sources were used only for the causal construction, experimental-design principles, calibration caution and Phase S adjacency. I could not prove the absence of an exact prior benchmark from a bounded web search; that claim remains provisional. Venue dates are deliberately not asserted here because V3 correctly requires checking the live calls when a submission decision is made.
