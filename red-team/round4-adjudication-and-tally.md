# Round 4 adjudication and tally (frozen 442cc4b7da691ca0, both arm specifications)

Date: 7 September 2026. Reviewers: Codex (13 findings), Gemini (10), fresh-context Claude Opus (25); each implemented both arms end-to-end from the two specifications alone. Author adjudicates; hash unchanged during the round.

## 1. The decisive result of the round

| Offset 500, family L, τ = 0, confounder present | Opus | Codex | Gemini |
|---|---|---|---|
| Sequential IBD AUC (N_x = 10) | 0.912 | 0.900 | 0.902 |
| Passive comparator AUC (N_x = 10) | 0.637 | 0.710 | 0.840 |
| Confounding benefit (N_x = 10) | +0.170 [0.127, 0.213] | +0.103 (SE 0.014) | +0.009 [−0.013, 0.031] |
| Confounding benefit (N_x = 30) | +0.224 | +0.152 | +0.030 |
| D-9.3 verdict at δ_AUC = 0.10 | superiority | marginal | fails |

Three implementations agree about the interventional arm to within 0.012 and disagree about the comparator by 0.20, so the decision rule flips while the method under test does not move. Two causes, both convergent across reviewers:
- **The instance generator is unspecified.** Nine load-bearing quantities (policy feedback support and gain, spectral radii, coupling sparsity, distractor dynamics, observation composition, initial state, noise keying, copy and padding layout) are left to the implementer. Three models built three benchmarks.
- **The comparator is structurally incapable in two ways.** Conditioning on the full observation makes the action loading on downstream channels near zero, so the comparator cannot score channels the contract requires as positives. And at τ = 2 a one-lag predictor cannot see the body at all: Codex showed that supplying the delayed action feature raises the comparator to AUC 0.997 and erases the benefit entirely. The τ = 2 "robustness" result in my D-9 adjudication was a misspecified-comparator artefact.

The statement in `decisions-required.md` that the margin "still clears 0.10 against the strongest comparator" was true on one instance family of three. It is withdrawn.

What survives, three of three: the sign-randomised statistic is robust (AUC 0.86 to 0.93 across family L, family N, τ = 2 and N_x = 100; confounder-insensitive; correct class order); the tie formula, the probe-count derivation, the pre-event epoch count and the no-washout argument all hold; the harness must own the isotonic fit.

## 2. Convergent findings, applied or escalated

| Topic | Reviewers | Disposition |
|---|---|---|
| Generator unspecified; three benchmarks | Opus R4-19, Codex CX-06, Gemini choices 1 to 3 | **D-10.1**: freeze a reference generator as code in the gate |
| Comparator structurally incapable (downstream loading; τ = 2 delay misalignment; ridge not unit-invariant) | Opus R4-2/3, Codex CX-01/02, Gemini GM-02 (mechanism disputed, category accepted) | **D-10.2**: delay-aware, multi-horizon comparator with standardised features; re-run the margin on the frozen generator before any δ is touched |
| R0-absent equivalence fails everywhere because the comparator is weak without confounding too | Opus R4-6, Codex, Gemini | **D-10.3**: replace equivalence with a comparator-competence validity check |
| IBD alarm channel unattainable: warm-up statistic is the global maximum; ARL is a step function | Opus R4-1 (critical), Gemini GM-06 | Spec draft 4: stat = 0 until window occupancy ≥ n_warm; ARL clock starts after warm-up; gate test T-IBD-warmup |
| n_min_sign deletes an actuator in about 13 percent of windows; zero is indistinguishable from absence | Opus R4-5, Codex CX-09, Gemini GM-05 | **D-10.4**: balanced pre-randomised (k, sign) blocks, eligibility mask returned |
| Co-primary offsets 10/50/200 are pre-event for both arms' windows | Opus R4-8 | **D-10.5**: align P2 offsets to {200, 500, 1000} |
| Copies move the primary; contract C5 says equivalence classes | Codex CX-07, Opus | **D-10.6**: no copies in confirmatory instances; copies reserved for acceptance tests |
| Ten seeds underpowered; instance-level clustering absent | Codex CX-11, Opus | **D-10.7**: multi-instance confirmation with instance clusters and a power simulation |
| Raw support vector has no callable path; configure lacks calibrator parameters; probed-arm calibration has two lifecycles; anchor pre/post-action ambiguous; fixtures F3/F4 impossible under additive noise; sign blindness is a formula constraint not a data restriction; stale ARL-primary text; aggregate_primary still HPDT-keyed with a collision-prone key; AUC has no reference implementation or test ID | all three | Interface v4 and contract v3.6 (applied now, safe); gate repaired now |
| Five surviving mutants (w→x edge; absolute aggregate; last-alarm match; aggregate collision; signed effect) | all three | Registered and killed |

## 3. Rejected or judgment calls
- Gemini GM-02 "mathematically blind under a zero-mean policy": the identity is wrong as stated (the score uses the finite-window sample mean, amplified by √n); the instance-dependent observation is valid and is subsumed by D-10.2.
- Gemini's τ = 2 comparator AUC of 0.952 is the round's one unreconciled number against 0.320 and 0.313; treated as a scoring-choice difference, resolved by D-10.1.
- Gemini GM-04 (family N breaks sign symmetry): mechanism plausible, unmeasured; Opus's family-N run shows no material effect at registry values. Prose qualification only.
- Opus R4-M3 (|gain·e| vs |gain|·e): e is a norm and non-negative by definition; the reference now validates e ≥ 0 so the mutant is killed, but the finding is low.

## 4. Decision D-10 (see `decisions-required.md`)

## 5. Process note
The round count is high. Round 4 is the one that would have invalidated the paper: without it, the confirmatory margin would have been decided by which passive baseline the author happened to implement. Once the generator is frozen as code, the two arm specifications can be verified by execution against the same instances, and cross-model reproductions should agree to within Monte Carlo error. That is the exit condition for design review.
