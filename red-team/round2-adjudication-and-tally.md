# Round 2 adjudication and tally (frozen d23960e6da441de7)

Date: 6 September 2026. Author of the artefacts: Claude (this context). Reviewers: Fable (fresh context), Codex, Gemini, Opus (fresh context; executed evidence in `review2-claude-opus/`, narrative findings pending at time of writing). Per the readiness protocol, the author adjudicates but does not review.

## 1. Headline

The stopping rule is not met and the round cap is reached. The direction of the programme is not attacked by any reviewer. The executable specification is not ready, and the failure mode is now precisely identified: **each repair round adds normative prose and tests faster than they can be verified, and the gate's fixtures exercise only the corner of the contract that the author happened to write examples for.** Four independent reviewers wrote 23 distinct mutants that the "8/8 killed" gate does not reject, and Opus showed that one of the eight shipped kills was fake: the M8 mutant recursed into itself and was "killed" by a RecursionError, not by any test.

## 2. Convergent findings (two or more reviewers, or executable evidence)

| Topic | Reviewers | Verdict | Disposition |
|---|---|---|---|
| Gate blind spots: delayed multi-hop reachability; downstream chain through A_d; padding guard; ε boundary; gain functional form; spacing (episode end, strict, unsorted); HPDT median vs mean; outcome vocabulary; z̄ ignored; sign-blind and column-0 confounding statistic; mean-not-max; magnitude-vs-sign reachability | Fable (13 mutants), Opus (8), Codex (1), Gemini (1); overlaps | valid, executable | **Gate rebuilt**: all 23 reviewer mutants registered in `mutants.py` and killed by new tests; fake-kill M8 fixed. See `executable-proofs/gate/`. |
| ARL_0 ±10 percent at 20,000 steps is unattainable (≈20 false alarms, 22 percent relative SE, P(within band) ≈ 0.34); "not calibratable" exclusion is method-dependent selection | Fable FB-10, Codex CX-04/05, Gemini GM2-4 | valid, executable | **Decision D-2 for Daniel** (precision rule and no-exclusion partial order). Draft: calibrate until the ARL confidence interval lies inside the band, ≥ 400 renewal intervals, hard cap; a method that cannot attain the band is reported under a predeclared partial-order endpoint and never dropped from the primary. |
| Closed-loop stability must be certified on the delay-augmented state including d and re-certified after events | Fable FB-17, Codex CX-03, Gemini GM2-3 | valid | Prose + test in 0A: augmented matrix [b_t..b_{t−τ}; d; a-queue]; family N empirical. |
| CSV role topology breaks the interaction gate (absent rows are "diagnostic") | Codex CX-06, Gemini GM2-5 | valid | Roles `confirmatory_effect` and `confirmatory_interaction`; frozen row selector; test. (v4.2) |
| Co-primary "confounded-channel false support" is diluted by f_conf and undefined after termination | Codex CX-07, Gemini GM2-6, Fable FB-18 | valid | Define on oracle-labelled confounded channels; unconfounded as negative control; post-termination offsets are missing by design and the metric is reported per available offset with the availability rate. (v4.2) |
| Stale normative references (v4 §1, contract E6 and J name superseded files; RMDT vs HPDT) | Fable FB-16, Codex CX-02, Gemini GM2-9 | valid | Fixed in v4.2 and a freeze manifest. |
| Promised reference implementations absent (aggregate_primary, ARL_0 calibration, Brier, log loss, F1, alarm bookkeeping) | Fable FB-12, Codex CX-12, Gemini GM2-7 | valid | Interface spec corrected to call them 0A deliverables; coverage matrix rows added; `aggregate_primary` implemented and tested in this rebuild. |
| requirements not pinned; ε_faith missing from registry; provisional phrasing in a frozen design | Codex CX-08/09/10, Gemini GM2-8/11 | valid | v4.2: exact pins; ε_faith = ε; provisional phrases removed, defaults locked unless Daniel overrides (D-5). |
| Misspecification and training registry underspecified | Codex CX-11, Fable FB-8 (related) | valid | 0A deliverable: machine-readable registry hashed into ledger rows. |

## 3. Single-reviewer findings with executable evidence or clear demonstration (applied or escalated)

| ID | Verdict | Disposition |
|---|---|---|
| FB-7 CartPole: complete loss terminates every episode in median 37 steps; Δ ≡ 0; TimeLimit 500 not replaced; discrete actions undefined for the interface | valid, executable, **design-killing for T2 as written** | **Decision D-1 for Daniel.** |
| FB-8 comparator identity differs across regimes (linear in D9, "correct model" in §4, MLP in F) | valid, contradiction created by a round-1 fix | **Decision D-3 for Daniel.** |
| FB-9 no regime, calibration or threshold entry point in interface v2 | valid | Interface v3 adds `configure(regime_bundle)`, `calibrate(transitions)`, `set_threshold(h)`; `regime_bundle` is the only privileged input and is logged. (v4.2) |
| FB-11 CSV lacks schedule, episode length, event time, n_events, T2 H/τ; `distractor_level` and "confounder absent" undefined; `s_change_certified` is a placeholder | valid | v4.2 defines the terms; CSV regenerated only after the generator exists so the certification column is real. |
| FB-13 sequential IBD has no frozen specification; the paper's treatment is undefined | valid | **Decision D-4 for Daniel** (one-page spec must be written and reviewed before 0B; it is a design object, not an implementation detail). |
| FB-14 no power analysis; n = 10 gives power 0.06 to 0.29 for plausible SDs | valid, executable | Pilot gate: require power ≥ 0.8 at Δ = 2δ or raise seeds and events per run; report achieved MDE. (v4.2) |
| FB-15 T-E2d false-failure 46 percent at 100 distractors, T = 4,000 | valid, executable | T ≥ 20,000 declared; Bonferroni null bound alternative. (v4.2) |
| FB-19 freeze hash excludes coverage matrix, requirements, proof-theatre test | valid | `freeze-manifest.txt` and `freeze.py`. |
| FB-20 w_T vs H_det unreconciled; dead merge rule | valid | v4.2 definition of detection and matching. |
| FB-21 feasibility floors | valid as floors; Opus throughput shows the bare SCM at 168k steps/s, so compute is dominated by estimator work, not simulation | Runtime pilot before dates (unchanged); calibration shared per cell, not per seed (v4.2). |
| FB-22, FB-23, FB-24, FB-25 | valid, low | v4.2. |
| Opus: shipped M8 mutant killed by its own recursion | valid, executable | Fixed; mutants now capture the original function before patching. |

## 4. Rejected or judgment calls

None rejected this round. Judgment calls: D-1 to D-5 below.

## 5. Decisions required from Daniel

- **D-1 T2 confirmatory environment.** CartPole cannot host complete actuator loss as a detection event. Options: (a) replace CartPole with a continuous, non-terminating, K ≥ 2 task (a 2-D point-mass with two independent thrusters is the simplest; losing one changes the support without termination); (b) make all of T2 exploratory and let Paper 1 rest on the two SCM families; (c) keep CartPole exploratory with partial loss only. Recommendation: (a).
- **D-2 Calibration rule.** Adopt the precision-based rule and the no-exclusion partial-order endpoint. Recommendation: yes.
- **D-3 Comparator identity.** (a) CUSUM on a linear predictor in every cell, with R0 meaning "linear predictor fitted in-distribution" (correct only on family L); or (b) CUSUM on the regime's residual model. Recommendation: (a), because it keeps one detector constant across regimes so the interaction I is interpretable; the "correct model" wording is dropped.
- **D-4 Sequential IBD specification.** Must be written as a one-page design object and reviewed before 0B. Recommendation: Daniel signs off the spec; a fresh-context agent writes the first draft from the IBD paper plus the contract, another red-teams it.
- **D-5 Lock the two round-1 defaults.** Co-primary on confounded channels; f_conf = 0.5. Recommendation: lock.

## 6. Process conclusion

The prose round cap is reached. The protocol said the gate then becomes the reviewer; Fable is right that a gate with 23 known survivors cannot play that role. The rebuilt gate kills all 23 and adds property-style fixtures outside the author's examples, which is the minimum for trust. What comes next is not a third prose round but a **code review round**: fresh-context agents review the rebuilt gate and, once built, the generator and oracle, by writing mutants against the code. That is a different activity from reviewing prose, and it is where every remaining category (certification statistics, augmented closed-loop stability, aggregation, calibration precision) becomes testable rather than arguable.

Opus's narrative findings will be appended to this tally when they arrive.

## 7. Opus findings (appended after arrival)

Opus (fresh context) delivered 31 findings, 15 high, with 106 independent checks confirming the contract algebra and 8 surviving mutants (all now killed). Its addendum records that the gate was modified while its review of the frozen hash was in progress. That is correct and was my doing; the rule in `roadmap-v4.4-amendments.md` H6 prevents it recurring.

| ID | Verdict | Disposition |
|---|---|---|
| OP-1, 2, 3, M1..M15 | valid, executable | Closed by the gate rebuild; recursion and identity guards added (H7). |
| OP-4 binary alarm cannot be calibrated | valid | Interface v3: `update` returns a continuous statistic; harness owns thresholding. |
| OP-5 ARL_0 precision | valid, executable (converges with FB-10, CX-04, GM2-4) | D-2a applied. |
| OP-6, OP-7 CartPole discrete and terminating | valid, executable | D-1a applied: CartPole removed. |
| OP-8 probe budget × ARL_0 × IBD 32k inconsistency | valid | **D-6 for Daniel**; sequential IBD spec drafted under the constraint. |
| OP-9 no power; six-way conjunction | valid, executable | H2: conjunctive-rule power by simulation, minimum 0.8, pre-committed underpowered reporting. |
| OP-10 one-sided R0 rule validates a catastrophic loss | valid, executable | H1: TOST. |
| OP-11 exclusion breaks pairing | valid | Contract G pairwise rule. |
| OP-12 alarm matching undefined | valid | `count_alarms` and `match_alarms` in the gate with tests. |
| OP-13 co-primary contradiction and computability | valid | H3: hierarchical co-primary; per-channel innovation statistics for the CUSUM arm. |
| OP-14 probing vs passive confound | valid | **D-7 for Daniel** (third arm). |
| OP-15 no dimensions or noise scales anywhere | valid | Registry: provisional values added; a prerequisite for the runtime pilot. |
| OP-16 closed-loop bound misses d-loop; saturation | valid, executable | Contract B: augmented state; saturation > 5 percent rejects. |
| OP-17, 18, 19, 25, 26, 27, 28 | valid | Applied (naming, references, pins, ε_faith, aggregate_primary, flush, comment). |
| OP-20 regime not commensurable across environments | valid | H4: I within environment; D-3a makes regimes the same class. |
| OP-21 present/absent pairing undefined | valid | Contract F7: same instance and noise streams. |
| OP-22 matrix non-executable; certification placeholder | valid | Regenerated: calibration rows, steps, split, channels, probe config hash; `s_change_required` is design intent. |
| OP-23 rejection sampling deletes hard cases | valid | Contract C2: rejection rate reported; near-threshold appendix cell; n_resamples in config hash. |
| OP-24 severing bound needs multiplicity | valid, executable | Contract E2d bound. |
| OP-29, 30, 31 | valid | Contract G and E6. |

Round-2 totals across four reviewers: 79 findings; 0 rejected; judgment calls resolved by D-1 to D-5 and pending as D-6, D-7. The mathematics of the contract survived four independent executions. Everything else that failed was specification, statistics, or coverage, and each is now either applied or a named decision.
