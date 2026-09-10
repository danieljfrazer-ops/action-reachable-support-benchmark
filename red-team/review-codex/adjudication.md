# Codex adjudication of the other frozen-version reviews

Date: 6 September 2026. Verdicts use the requested categories. Where the distinction depends on programme priorities rather than correctness, I mark **judgment call**. This adjudication was written only after `review-codex/findings.md` was completed.

## Claude findings

| Finding | Verdict | One reason |
|---|---|---|
| CL-1 | **valid** | `structural_reach` outputs only body reachability from `A,B`; it cannot test C1’s downstream `a→b→d` path, and K10 is absent. |
| CL-2 | **valid** | Time-indexed reachability within horizon H must include actuator delay; with `τ=1,H=1` the current structural reference says reachable while the contract response is zero. |
| CL-3 | **valid** | The M2/M5 tests demonstrate hand-written mismatches but do not mutate the future event handler/oracle, so “mutant covered” overstates protection against those implementation defects. |
| CL-4 | **invalid** | Roadmap v4 already normatively limits confirmatory events to complete losses “producing an S^obs change (certified by the oracle per instance)”; a redundant CSV Boolean may aid audit but is not missing scientific logic. |
| CL-5 | **valid** | A fixed channel-agnostic linear predictor cannot simultaneously be a correct dynamics model for nonlinear CartPole/Pendulum without a separate operational definition of “correct.” |
| CL-6 | **judgment call** | Complete support loss could be an easy floor effect, but noise, delay and channel anonymity may still make sequential detection nontrivial; only a pilot can settle usefulness. |
| CL-7 | **valid** | Nonlinear R is indexed by all `2K` signed probes, so the interface’s `K` axis discards generally non-odd responses. |
| CL-8 | **valid** | Partial scaling can move `|gain|e` or the latent effect across ε; the contract does not freeze a γ bound that prevents this after the event. |
| CL-9 | **valid** | Open-loop spectral-radius constraints do not guarantee closed-loop stability after policy feedback, observation gain and clipping; the certification must include the actual closed-loop system. |
| CL-10 | **valid** | “The sign holds” lacks an aggregation and uncertainty rule and can mean point estimate, per-seed majority or confidence bound. |
| CL-11 | **valid** | Repeated single-step calls could implement randomized probing, but the frozen interface does not say so or define per-call/step costs and action-sequence timing. |
| CL-12 | **invalid** | `run_gate.py` already makes exit status normative in executable behavior and intentionally substitutes for pytest; missing NumPy/locked setup is real, but installing pytest or restating exit-code semantics is not required. |

## Gemini findings

| Finding | Verdict | One reason |
|---|---|---|
| GM-1 | **valid** | The surviving `999·B` delayed-Jacobian mutant directly proves the post-arrival `h>τ>0` branch is untested. |
| GM-2 | **valid** | Existing reachability cases exercise H=1 and H=3 but not a chain whose membership first changes at H=2; the skip-H2 mutant therefore survives. |
| GM-3 | **valid** | The structural reference omits τ, contradicting the contract’s “within H steps” time-indexed support for delayed actuation. |
| GM-4 | **valid** | C1 is over all `z=[b,d,w,x]`, while the reference function has no representation for downstream or exogenous variables. |
| GM-5 | **valid** | R0’s “correct dynamics model” is undefined for T2 while the frozen fair comparator is specifically a linear predictor. |
| GM-6 | **valid** | The contract says every K case is tested, but K7 and K10 do not exist as tests; related tests do not cover the exact claims. |
| GM-7 | **judgment call** | A max-correlation witness is sufficient to instantiate confounding but not to make all 100 distractors confounded; the right prevalence depends on the intended benchmark stress profile and must be declared. |
| GM-8 | **invalid** | It relies on a superseded `gemini_v32_checks.py` implementation, contrary to the frozen-review instruction; v4/D11 and contract G explicitly make pAUC descriptive and disjoint curves a partial order with no scalar. |
| GM-9 | **valid** | The exact required command fails in the current environment before collection because NumPy is unavailable; a different interpreter’s successful run does not satisfy reproducible gate packaging. |
| GM-10 | **invalid** | Contract C4 already specifies the empirical stationary mean after `burn_in`; the zero-state reference is a valid family-L cancellation check, while family-N response remains explicitly uncovered for Phase 0A. |

## Cross-review disposition

The reviewers independently agree on four blockers: delay-aware support, delayed-response mutation coverage, full-latent/downstream reachability, and a defined T2 R0 model. Claude and Gemini also independently caught the nonlinear R shape mismatch and missing K cases. These convergences should be fixed before Stage 0A scaffolding.

My additional blocking findings remain: the public estimator API omits applied actions; `ARL_0` and probe-budget units are absent; the 2×2 interaction is not an estimand or gate; and the exact `python3 run_gate.py` command is not reproducible. Those do not conflict with either adjudicated review.
