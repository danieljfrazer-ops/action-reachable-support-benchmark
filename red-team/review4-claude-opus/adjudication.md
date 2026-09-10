# Round 4 adjudication — Claude Opus rating `review4-codex` and `review4-gemini`

Both peer folders are **present** and both contain a finalised `findings.md` (Codex 21.7 kB, Gemini 14.4 kB),
an independent simulation, and a surviving-mutant script. I read them only after `findings.md` in this folder
was complete; nothing in my findings was altered afterwards.

I re-ran both peer mutants under the frozen gate on the pinned interpreter:

* `review4-gemini/surviving_mutant_r4.py` → "34/34 passed, 0 failed. CONFIRMED: Mutant SURVIVED". **Verified.**
* `review4-codex/surviving_mutant_absolute_primary_difference.py` → "34 passed, 0 failed". **Verified.**

Together with my three (`new_mutants.py`), **five new mutants survive the frozen gate**, in four different
functions (`build_adjacency`, `aggregate_primary` ×2, `match_alarms`, `s_obs_eps`).

---

## 0. The three reproductions side by side (the most important result of the round)

Offset 500, family L, τ = 0, confounder present, per-episode AUC of the raw statistic:

| | Opus (this folder) | Codex | Gemini |
|---|---|---|---|
| `seq_ibd`, N_x = 10 | **0.912** | **0.900** | **0.902** |
| passive comparator, N_x = 10 | **0.637** | **0.710** | **0.840** |
| confounding benefit, N_x = 10 | **+0.170** [+0.127, +0.213] | **+0.103** (SE 0.014) | **+0.009** [−0.013, +0.031] |
| confounding benefit, N_x = 30 | **+0.224** [+0.190, +0.258] | **+0.152** (SE 0.017) | **+0.030** [−0.000, +0.060] |
| D-9.3 verdict at δ_AUC = 0.10 | SUPERIORITY | marginal (pooled lb 0.098) | **FAILS** |

**Three independent implementations agree about the IBD arm to within 0.012 AUC and disagree about the
passive comparator by 0.20 AUC.** The decision rule therefore flips across models while the *method* under
test does not move at all. That is decisive evidence for the claim in my R4-19 (the instance family is
unspecified) and R4-2/R4-3/R4-CX-01 (the comparator's structural capacity is what the margin is measuring).
`decisions-required.md`'s stated basis for freezing the comparator on principle — "knowing from pilots that
the arm's AUC margin still clears 0.10 against it" — is **not supported** by the round-4 evidence: it clears
0.10 on one of three independent instance families.

---

## 1. `review4-codex` findings

| ID | Rating | Reason (one line) |
|---|---|---|
| R4-CX-01 (τ = 2 comparator forced onto `a_t`; delay-aware feature raises it to 0.997 and erases the benefit) | **valid** | Independently reproduced: I measure the same collapse (l[b] = 0.089 vs l[conf-x] = 7.150; AUC 0.320 present / 0.540 absent) as my R4-3, and Codex's delay-aware sensitivity converts a "robustness cell" into a comparator misspecification — the strongest finding either of us has. |
| R4-CX-02 (trace-scaled ridge λ is not unit-invariant; rescaling one channel ×100 moved λ 4.80 → 8038 and the loadings 21–27 %) | **valid** | I did not test this and it is correct as a matter of ridge algebra; it is live rather than hypothetical because contract §D gain events change a channel's scale mid-episode and `gain_t` is unspecified at sampling (my R4-19), so channel scales genuinely differ. |
| R4-CX-03 (the primary raw vector is named in the ledger but has no callable path out of `update`) | **valid** | Same defect as my R4-18 and Gemini R4-GM-09, and Codex states it best: an E6 black-box harness written from interface v3 alone cannot compute the primary metric at all. |
| R4-CX-04 (F3's "hard-silent pad" and F4's `\|q1−q2\| < 1e-6` are impossible under contract §B's additive ε^o) | **valid** | I confirmed the algebra: `o = avail ⊙ gain ⊙ (Assign z) + ε^o` adds noise even when `avail = 0`, and two copies get independent ε^o, so neither fixture can pass; I observed the first half (my padding channels were live negatives with l ≈ 0.035) but missed that F3/F4 are therefore unsatisfiable. |
| R4-CX-05 (arm 3 has two incompatible calibration lifecycles: §§1/10 give both arms the same non-probed `calibrate`, §§3/4 require `k` re-derived on a probed stream, and interface v3 exposes one `calibrate`) | **valid** | Verified by reading: the contradiction is textual and the interface has no second entry point; my R4-17 found the neighbouring hole (no channel for the harness-fitted `g`) and Codex found this one. |
| R4-CX-06 (the LOIO calibration tier has no manifest: instance count, fold membership, seed nesting, eligible steps, held-out event times all undefined) | **valid** | Superset of my R4-9; `confirmation-design.csv` carries a single `event_t = 1000` and `cal_split = 24\|16` with `seed = -1`, so "leave-one-instance-out with held-out event times" is unimplementable as written. |
| R4-CX-07 (C5 scores copies as equivalence classes; contract §G's primary AUC is per channel, so duplicating a channel moves the primary) | **valid** | Correct and I missed it: my own instance carries a copy of b0 and a copy of x0 (CHOICE-02), and under C5 those should be collapsed, which changes both the numerator and the variance of the primary. |
| R4-CX-08 (prose implies a pre-action anchor `o(t_p)`; the §9 pseudo-code pushes `tr.obs` and indexes `ring[t_p]`, implying a post-action anchor; worth 0.05–0.06 AUC) | **valid** | I checked the pseudo-code against `Transition = (prev_obs, applied_action, obs)` and Codex is right — the post-action reading makes the anchor the first responding observation and silently deletes the h = 1 cell at τ = 0; I resolved it the other way without noticing the conflict. |
| R4-CX-09 (`n_min_sign`: 12.7 % chance at least one actuator is unusable at the primary offset; `a_c = 0` is indistinguishable from evidence of absence and no eligibility mask is returned) | **valid** | Converges with my R4-5 from a different direction — Codex computes the probability analytically for *either* actuator (12.7 %), I measure the consequential case, the *surviving* actuator (8–12 %), and show AUC collapses to 0.238 when it happens. |
| R4-CX-10 (T-CMP-probe-blind proves marker blindness, not sign blindness; formula blindness is the defensible control) | **valid** | Identical conclusion to my R4-16, reached independently, and their framing ("no explicit randomisation-stratified statistic") is the better wording for the fix. |
| R4-CX-11 (10 seeds cannot put the lower bound above δ_AUC = 0.10 for an effect of this size) | **valid** | Their own 40-seed pooled lower endpoint of 0.098 demonstrates it, and the three-model spread in §0 makes the point far stronger than a single-instance power argument; the caveat that one instance cannot estimate population power is correctly stated by them. |
| R4-CX-12 (surviving mutant: `aggregate_primary` replaces signed cell differences by absolute differences; coverage matrix still says 23 mutants while the runner executes 35) | **valid** | Re-ran it: 34 passed, 0 failed — confirmed survivor, and the coverage-matrix count is verifiably stale (I read "23/23 killed" against a 35-mutant run). Different survivor from my R4-M2 in the same function, so both should be registered. |
| R4-CX-13 (contract §G still says "the primary comparison is made at matched ARL_0" and OP-11 still makes the primary inconclusive above 10 % out-of-band, contradicting the R3-8 scoping in the same section) | **valid** | Verified verbatim at line 132 of `stage-0a-contract-v3.5.md`; this is R3-8 re-appearing in the consolidated contract, so a round-3 accepted finding was applied in one paragraph and not in its neighbour. |
| R4-AF-01…09 (attacks that failed) | **valid** | All nine are correctly classified; R4-AF-03 (tie formula), R4-AF-04 (100/99), R4-AF-05 (no washout needed), R4-AF-06 (1 200 pre-event epochs) and R4-AF-08 (harness owns PAVA) are the same five conclusions I reached independently, which is meaningful convergence. |

**Codex's new-category claim.** I accept R4-CX-01, R4-CX-02, R4-CX-04, R4-CX-05 and R4-CX-10 as new
categories. R4-CX-03 and R4-CX-09 I would class as continuations (of CX-03/IB-11 and of D9-codex-3
respectively) rather than new categories, but the concrete failures are new in both cases — a **judgment call**
on labelling, not on substance.

## 2. `review4-gemini` findings

| ID | Rating | Reason (one line) |
|---|---|---|
| R4-GM-01 (surviving mutant: illegal `w → x` edge in `build_adjacency`; `test_C1_build_adjacency_keeps_w_and_x_self_edges` never tests cross-edges between exogenous blocks) | **valid** | Re-ran it: 34/34 pass, mutant survives, and the root-cause analysis is exactly right — the reachability frontier starts at b and never reaches w, so edges out of w are unreachable by any current test. |
| R4-GM-02 (the comparator is "completely blind" to actuator loss under a zero-mean policy because `E[r_t] = −β_a E[a_t] = 0`) | **judgment call** | The derivation is wrong as stated — the score uses `√n ×` the *finite-window sample* mean, not the population mean, and with ρ_u = 0.8 the 500-step sample mean of `a` is O(0.13·W_u), amplified by √500; I measure a shift of 6.66 on channels leaving the support against 0.85 on retained ones, i.e. decisively not blind — but their own instance (q ≈ 8.3 lost vs 7.9 retained) shows the effect is real when the policy has little low-frequency content, so the finding is a valid *instance-dependent* observation dressed as a mathematical identity, and their claimed "new category" rests on the identity. |
| R4-GM-03 (the confounding benefit fails δ_AUC = 0.10: +0.009 and +0.030) | **valid** | Their numbers are real and, set beside Codex's +0.103/+0.152 and my +0.170/+0.224, they establish the round's most consequential fact (§0); I disagree only with their proposed fix (a design-matrix average contrast), which trades a failing rule for a looser one instead of fixing the comparator (R4-2, R4-3, R4-CX-01) — that half is a **judgment call**. |
| R4-GM-04 (family N breaks sign symmetry because prior probe signs move the operating point on `tanh` and `κb²`) | **judgment call** | The mechanism is real in principle and worth a prose qualification, but it is asserted, not measured; at registry values (s = 1.0, κ = 0.1, m = 4.0) my 40-seed family-N run shows no material effect — IBD AUC 0.921 present / 0.900 absent, statistically indistinguishable from family L's 0.912 / 0.925. |
| R4-GM-05 (`n_min_sign = 3` does not scale: at K ≥ 4, P(min < 3) > 85 % and `a_c` collapses to 0) | **valid** | The scaling argument is right and the spec has no rule tying `W_steps` to K — but the cited instance is wrong: contract H2 gives PointMass2D **K = 2** and Pendulum-v1 **K = 1**, so K ≥ 4 does not occur in the frozen design; the finding stands because `K` is marked [provisional] in the registry. |
| R4-GM-06 (warm-up: `a_c = 0` while `ā_c ≈ 1.5`, so `stat ≈ 3.0` triggers immediate false alarms if h ≤ 3.0) | **valid** | Same defect as my R4-1, found independently by derivation; my measurement makes it much worse than their estimate — `stat_warm` is 5.44–5.68, it is the *global maximum* of the whole stat stream, the fresh-start ARL_0 is exactly 63.0 steps for every h below it and infinite above, so the D-2a band is unattainable at any h rather than merely "at risk". |
| R4-GM-07 (probe shocks at τ = 2 spike the probed comparator's innovations, degrading AUC to 0.31–0.62 and inflating h by 25) | **judgment call** | The direction is consistent with my run (arm 3 0.259 vs arm 2 0.320 at τ = 2), but the effect is not separable from the structural collapse of R4-GM-01's neighbour finding R4-CX-01/my R4-3 — the comparator is already at chance at τ = 2 before any probe enters — and the "h by 25" figure is carried over from `d9-adjudication.md` rather than measured here. |
| R4-GM-08 (floating-point guard: `σ_U²` can round to −1e-17 and raise in `sqrt`) | **judgment call** | Defensively sensible, but for N ≤ 25 both terms are `(integer)/12` computed from exactly representable integers, and when all values tie the two terms are the *same* float, so the difference is exactly 0 and the §3 "if σ_U = 0 the cell contributes zero" branch catches it; the guard costs nothing but the stated failure mode does not arise at the frozen window size. |
| R4-GM-09 (`configure()` has no field to inject `{g_knots, θ*}`) | **valid** | Identical to my R4-17 and the missing half of Codex R4-CX-03; verified against interface v3, whose `configure` is typed for "the declared regime's residual model" while the IBD spec simultaneously declares it has no residual model. |
| R4-GM-10 (`aggregate_primary` expects `hpdt` and `cusum_channel_agnostic` instead of `auc` and `cusum_linear_channel_agnostic`) | **valid** | Verified; identical to my R4-21 and half of Codex R4-CX-12, and it is a round-3 finding (R3-CX-03) still unfixed in the frozen version. |
| Gemini's four "attacks that failed" | **valid** | All four are correctly classified as killed by the gate; the fourth ("world-to-body edges triggered recursion in the test harness") is worth flagging to the author because it means a legitimate mutant hit the H7 RecursionError guard, which is a gate-usability issue rather than a finding. |

**Gemini's new-category claim.** Their claimed new category (R4-GM-02/R4-GM-07, "linear residual monitor
structural blindness under zero-mean invariance") is a **judgment call**: the *category* — structural
blindness of the frozen comparator — is genuinely new this round and I agree with it (it is where my R4-2 and
R4-3 and Codex's R4-CX-01 all live), but the specific zero-mean-invariance mechanism they name for it is not
the one that operates, and their own τ = 2 comparator AUC of 0.952 (versus 0.320 in mine and 0.313 in
Codex's, both at τ = 2 present) is the round's one unreconciled numerical disagreement and should be resolved
before either number is quoted.

## 3. Where the three reviews converge, and what that means

**Unanimous, three of three:** the comparator's specification — not the method — decides the margin
(my R4-2/R4-3, CX-01/CX-02, GM-02/GM-03); the harness must own the isotonic fit (my R4-17, CX-AF-08, GM-05
judgement call 1); probe-sign blindness is unenforceable and the flag-permutation test does not test it
(my R4-16, CX-10, GM judgement call 2); the raw statistic has no callable path out of `update`
(my R4-18, CX-03, GM-09); `aggregate_primary` is stale (my R4-21/R4-M2, CX-12, GM-10); the warm-up breaks the
alarm channel (my R4-1, GM-06); `n_min_sign` deletes actuators (my R4-5, CX-09, GM-05); the tie formula,
the 100/99 derivation, the 1 200-epoch pre-event count and the "no washout" argument all survive attack
(my §4, CX-AF-03/04/05/06).

**Two of three, and I side with the majority:** the comparator collapses at τ = 2 (mine 0.320, Codex 0.313,
Gemini 0.952). Gemini is the outlier and its own §2 finding R4-GM-07 reports 0.31–0.62 for the same region,
so I read the 0.952 as a different scoring choice rather than a contradiction of the mechanism.

**My single most important disagreement with a peer:** Gemini R4-GM-02's claim that the comparator is
*mathematically* blind to actuator loss. It is not, at these registry values, and the reason matters —
the shift term is driven by the low-frequency content of the policy's action stream, which is a property of
`W_u`, `ρ_u` and the unspecified `W_o` support. That is R4-19 again: three models, three generators, three
answers.

**Opinion.** Given five surviving mutants in four functions, a critical alarm-channel defect, a comparator
that two of three reviewers find structurally incapable in two separate ways, and a decision rule whose
verdict flips across three independent reproductions, my recommendation is that version 4 is **not ready to
freeze for Stage 0A**. The ordering that would fix the most with the least churn is: (1) freeze the generator
and instance family (R4-19 / CX-06); (2) fix the comparator's structural capacity — H-step loading and
delay-aware features (R4-2, R4-3, CX-01); (3) re-run the D-9 margin on the frozen generator before touching
δ_AUC; (4) fix the IBD alarm channel's warm-up or formally retire its HPDT (R4-1); (5) register all five
mutants and add the AUC to `contract_ref.py` and the coverage matrix (R4-20).
