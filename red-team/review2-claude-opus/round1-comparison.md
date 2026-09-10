# Round-2 vs round-1: new category or seen category?

Written **after** `findings.md` was complete. Round 1 (`review-claude/`, `review-codex/`,
`review-gemini/`) reviewed frozen version **c197652c0d8e846b**; I reviewed **d23960e6da441de7**,
which already applies most of their findings. So "seen" below means *the category of defect was
raised in round 1*, not that the specific defect is unfixed. Where I attack a round-1 **fix**,
I say so.

## Summary

| | count |
|---|---|
| **NEW category** (no round-1 finding in this area) | 20 |
| **SEEN category, new instance** (the class was raised; this is a fresh occurrence, often a residue of the fix) | 8 |
| **SEEN category, attack on the round-1 fix itself** | 3 |

The three round-1 reviews between them covered: gate coverage of C1/C4/delay/downstream,
oracle interface shapes, R0 on T2, aggregation, cluster inference, SOEI freezing, the interaction
estimand, censoring semantics, environment reproducibility, family-N specification, probe/transition
inputs, witness eligibility, and constants-without-values (for `s, κ, m`, `ARL_0`).

They did **not** cover, anywhere: statistical **power**, the **decision rules' logic** (one-sidedness,
conjunction), the **alarm-to-event matching rule**, **ARL_0 estimation precision**, the **actual
Gymnasium action spaces and dynamics** of the two T2 environments, the **arithmetic of the probe
budget against IBD's published cost**, the **fairness of the headline contrast** (probing vs passive),
**missing dimensions and noise scales**, or the fact that the **aggregation function of the primary
estimand is untested**. That is where most of my high findings sit.

## Per-finding categorisation

| ID | Category | Nearest round-1 finding | Note |
|---|---|---|---|
| OP-1 HPDT mean-vs-median survives | **NEW** | — | Round 1 argued about *what* the delay estimand should be (CX-08) and got it renamed to HPDT. Nobody tested the estimand's aggregation function. All four HPDT assertions use n=2 events, where mean = median. |
| OP-2 shipped M8 mutant self-recurses | **SEEN category, new instance** | CL-3 ("`test_M2_rejected`/`test_M5_rejected` compare hard-coded arrays; the mutants test nothing") | Exactly the same disease — a mutant that does not actually mutate — in a *different* organ, and it survived the round-1 repair. That the category recurred after being fixed once is itself the finding: the mutation harness needs a structural guard, not another manual fix. |
| OP-3 `check_spacing` episode-end guard untested | **NEW** | adjacent to CX-08 (censoring) | CX-08 forced the choice "guarantee no censoring **or** use a censored estimator"; the plan chose the first and made `check_spacing` the load-bearing guarantee. Nobody then tested that guarantee, and the episode-end half of it is inert. |
| OP-4 binary `alarm_S` insufficient for ARL_0 calibration / ARL curves / pAUC | **NEW** | adjacent to CX-03, CL-11 (interface) | CX-03/CL-11 fixed the estimator's **inputs** (transitions, probe sequences). Mine is about its **outputs**: with no scalar statistic the harness cannot threshold, calibrate, or draw a delay-vs-ARL curve. Different axis of the same document. |
| OP-5 ARL_0 ±10% unattainable from 20,000 steps | **NEW** | CX-06 ("ARL_0 has no numerical value") | CX-06 asked for a number. A number was supplied. Nobody checked whether the accompanying estimation protocol can produce it: P(within ±10%) = 31.6%. |
| OP-6 CartPole is `Discrete(2)`, frozen interface is continuous `action[K]` | **NEW** | CX-13 checked the Gymnasium **API** signature | CX-13 verified `step` returns `(obs, reward, terminated, truncated, info)`. Nobody checked the **action space** of the named environments against the contract's `action[K]`, `a_max` clip, and `±e_k` probe set. |
| OP-7 CartPole terminates ~19–49 steps after actuator loss → Δ ≡ 0 | **NEW** (adjacent to CL-6) | CL-6 said single-actuator complete loss is "a floor-effect fault that both detectors catch easily" on T2 | Same instinct, different and much sharper mechanism: it is not that both detectors catch it, it is that **neither can**, because the episode ends inside the detection horizon and ARL_0 = 1000 exceeds the 500-step episode cap. CL-6's proposed remedy (the co-primary) does not fix this, and I attack that remedy separately in OP-13. |
| OP-8 probe_budget × ARL_0 × IBD's 32k probe phase | **NEW** | CX-06 ("probe_budget has no unit or semantics") | The unit was supplied (probe steps / total steps). Nobody multiplied it by the comparator's published cost. Requires the external source (arXiv 2603.18257v2), which no round-1 review consulted. |
| OP-9 no power analysis anywhere; coverage ≠ power; 6-way conjunction | **NEW** | CX-12 (few clusters), CX-16 (SOEI) | CX-12 asked for **coverage** checks and got them (v4.1 E3); CX-16 froze δ and got it (E4). Between them they closed the two levers that could have surfaced power, and left power itself unexamined. This is the single largest gap I found. |
| OP-10 R0 rule is one-sided and validates when IBD is far worse | **NEW** | — | No round-1 review audited the logic of the decision rules. |
| OP-11 `not_calibratable` exclusion breaks the paired estimand | **NEW** (consequence of a round-1 fix) | CX-06 ("no fallback is specified if ARL_0 cannot be attained") | The fallback CX-06 asked for was added — "excluded from the primary" — and it is the wrong fallback for a **paired** estimand, especially since exclusion is plausibly differential by regime. |
| OP-12 `w_T` (50) vs `H_det` (200) alarm-matching ambiguity | **NEW** | — | Nobody asked which window attributes an alarm to an event. It changes the estimand's usable range by 4×. |
| OP-13 co-primary contradicts D8; uncomputable for the channel-agnostic arm | **NEW** (attack on a round-1 fix) | CL-6 proposed the co-primary | CL-6's remedy was adopted verbatim (v4.1 E7) without noticing that (a) D8 says "nothing else is primary", and (b) one arm of the confirmatory pair is channel-agnostic and cannot emit per-channel p_c. |
| OP-14 probing vs passive confounds the headline contrast | **NEW** | — | No round-1 review questioned whether "matched ARL_0" is sufficient matching. It matches false alarms and nothing else. |
| OP-15 dimensions and all noise scales unspecified | **NEW** | CX-09 (`s, κ, m` have no values) | CX-09 found the same disease in one small place and it was fixed there. The much larger instance — `N_b, N_d, N_w, N_x, C, K, n_u` and every noise covariance — was not looked for. |
| OP-16 ρ_cl omits the b→d→o→a→b loop | **SEEN category, attack on the round-1 fix** | CL-9 ("closed loop is A_b + B W_o … its radius is unconstrained") | CL-9 identified the problem and proposed exactly the expression that was adopted. The adopted expression is incomplete: it only closes loops inside the b-block, and contract C6 *requires* an observed downstream channel. Executable counterexample: contract quantity 0.300, true radius 2.300, 100% action saturation. |
| OP-17 roadmap still says RMDT; contract says it is explicitly not an RMDT | **SEEN category, new instance** | CX-08 | Residue of CX-08's fix: the contract was rewritten, the roadmap's D11/§4/§3 were not. |
| OP-18 contract v3.1 and roadmap v4 cite superseded `interface-spec.md` / `contract-v3` | **NEW** | — | A freshly frozen normative set pointing at its own superseded parts. E6's black-box suite would be built against interface v1. |
| OP-19 `requirements.txt` is unpinned despite E9 saying "pinned" | **SEEN category, new instance** | CX-02, GM-9, CL-12 (environment reproducibility) | The category was raised three times and the fix (venv + requirements + interpreter check) landed, but the requirements are lower bounds, so the "exit code from a clean checkout" criterion still is not reproducible. |
| OP-20 D9 freezes a *linear* predictor; contract F specifies an *MLP* for R0 on T2 | **SEEN category, attack on the round-1 fix** | CL-5, GM-5 (R0 undefined on T2) | Both proposed the MLP; it was adopted into contract F without reconciling it with D9's frozen comparator, and without noticing that "regime" is now a different intervention in each of the four environments while the decision rule requires a common sign. |
| OP-21 interaction I unsized; `diagnostic_2x2` rows gate a confirmatory claim; seed pairing unspecified | **SEEN category, attack on the round-1 fix** | CX-07 (proposed the interaction contrast) | CX-07 asked for an interaction estimand "with uncertainty and a minimum effect or at least a sign gate" and got the sign gate. Its variance, its role label, and the seed correspondence across the 2×2 were never specified. |
| OP-22 `confirmation-design.csv` lacks steps/events/calibration rows; `s_change_certified` is a literal string | **SEEN category, new instance** | CL-4 (introduced `s_change_certified`), CX-06 | CL-4's column was added as the constant `REQUIRED_TRUE`, which guarantees the frozen artifact differs from the one actually run. The missing run-length and calibration columns are new. |
| OP-23 rejection sampling conditions instances away from ε | **SEEN category, new instance** | CX-15 ("resampling rejected near-threshold instances can also alter the generator distribution") | CX-15 raised this in one clause and it was answered with a rejection-rate cap. My addition is that the cap does not address the *estimand-validity* consequence, plus the point that `seed` is no longer an instance identity. |
| OP-24 δ_inv = 0.05 on a max over K×N_x pairs, no multiplicity, no T | **NEW** | GM-7 (ρ_min dilution at high distractor levels) | GM-7 attacked the **floor** (ρ_min) at `distractor_level=100` and was fixed with `f_conf` and a median report. Nobody attacked the **ceiling** (δ_inv) at the same distractor level, where the multiplicity runs the other way: 35% false-failure at T=4000. |
| OP-25 `ε_faith` has no value | **NEW** | CX-09 (same disease, different constants) | Missed by the sweep that fixed `s, κ, m` and `ARL_0`. |
| OP-26 `aggregate_primary()` referenced by a frozen spec but does not exist | **SEEN category, new instance** | CX-11 (aggregation unspecified) | CX-11's fix named a function and froze the name into `interface-spec-v2.md` before writing it. |
| OP-27 gate stdout ordering is buffering-dependent | **NEW** | — | Minor, but the gate report is a signed artefact. |
| OP-28 `test_gate.py` comment contradicts `coverage-matrix.md` on M8 | **NEW** | — | |
| OP-29 Pendulum-v1 never terminates | **NEW** | — | Same class as OP-6/OP-7: nobody checked the named environments' actual documented behaviour. |
| OP-30 co-primary offset 200 unreachable after early termination | **NEW** (consequence of CL-6's fix) | CL-6 | |
| OP-31 E6 "censored case" vs G "censoring cannot occur" | **SEEN category, new instance** | CX-08 | Residue of the CX-08 rewrite. |

## Mutants: mine vs round 1

Round 1 submitted 5 mutants (CL UM-1 no-downstream, CL UM-2 no-delay, CX τ-cap, GM-1 999·B,
GM-2 skip-H2). All 5 are now in `mutants.py` and all 5 are killed — I re-ran them and confirm
8/8. Every one of those five attacked **C1 reachability or the C4 Jacobian**, i.e. the two
functions the round-1 repair then over-tested.

My 8 survivors attack **five functions that round 1 never mutated at all**: `hpdt` (OP-M1),
`check_spacing` (OP-M2, OP-M3), `s_obs_eps`'s guards rather than its arithmetic (OP-M4, OP-M5),
`max_pairwise_corr`'s aggregation (OP-M8), and `open_loop_response`'s `zbar` argument (OP-M7).
Plus OP-M15, the residue of the C1 repair (the `A_d` block is still unpinned because no test has
a chain of length ≥ 2 inside `d`).

The pattern is worth stating plainly (**opinion**): the round-1 repair fixed exactly what round 1
mutated, and the mutation suite has therefore become a record of past attacks rather than a
measure of coverage. `mutants.py` will keep reporting 8/8 forever. The structural fix is to
require every function in `contract_ref.py` to have at least one killed mutant per *argument*
and per *aggregation choice*, and to add a guard that a mutant which raises `RecursionError` or
which is input-identical to the original does not count as killed (OP-2).

## Two things round 1 got right that I could not break

- **The delay repair is real.** CL-2/GM-3/CX-01 forced τ into C1 and C4; my independent brute-force
  simulation (`verify_contract.py`, 96 τ×h cells) confirms the resulting formulas are exactly right,
  and my two off-by-one mutants in opposite directions were both killed.
- **The downstream repair is mostly real.** CL-1/GM-4/CX-05 forced `[b; d; w; x]` into the adjacency;
  `test_K10` kills a mutant that hides `d`. Only the `A_d` sub-block escapes.
