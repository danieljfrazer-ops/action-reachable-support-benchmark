# Round 6 — adjudication note, `claude-opus`

**Status: written BEFORE the other two round-6 reviews exist.** As the brief instructs, this records what I would want to check against `review6-codex/` and `review6-gemini/` when they arrive, and how I would resolve each class of disagreement. Nothing here is a verdict on another reviewer's work. Every number referred to is mine, from `report.txt` and `aux_output.txt` in this folder.

---

## 1. The three numbers that decide whether round 6 agrees at all

Contract §A0 and §L make "three independent implementations … agree to Monte Carlo error" the exit condition. The following are the specific quantities on which agreement must be checked first, because everything else is downstream of them. My values, primary offset 500, family L, 10 configuration seeds × 4 episode seeds, 95 % percentile bootstrap clustered by instance:

| quantity | L_Nx10_τ0 | L_Nx10_τ2 | L_Nx30_τ0 | L_Nx30_τ2 |
|---|---|---|---|---|
| `seq_ibd` primary, present | 0.813 [0.727, 0.896] | 0.687 [0.571, 0.808] | 0.813 [0.727, 0.896] | 0.687 [0.571, 0.808] |
| `seq_ibd` primary, absent | **0.813 (identical)** | **0.687 (identical)** | **0.813 (identical)** | **0.687 (identical)** |
| comparator primary, present | 0.879 [0.758, 1.000] | 1.000 [1.000, 1.000] | 0.879 [0.758, 1.000] | 1.000 [1.000, 1.000] |
| comparator primary, absent | 0.863 [0.725, 1.000] | 1.000 [1.000, 1.000] | 0.863 [0.725, 1.000] | 1.000 [1.000, 1.000] |
| confounding benefit | −0.017 [−0.042, 0.000] | 0.000 [0.000, 0.000] | −0.017 [−0.042, 0.000] | 0.000 [0.000, 0.000] |

**Check 1 — the present/absent identity for `seq_ibd`.** This is not a Monte-Carlo agreement question; it is a structural prediction (R6-OP-01, mechanism verified in `aux_output.txt` §A: actions, `b` and `d` are bitwise identical between conditions and `max |o_present − o_absent|` over the pre-event support is exactly `0.000e+00`). **Any implementation that reports a non-identical `seq_ibd` present/absent pair has a bug**, most likely one of: (a) it re-drew or re-certified the absent instance instead of deep-copying and setting `G[:] = 0` on the certified present one; (b) it keyed the probe allocation on the confounder condition, which draft 5 §3 forbids; (c) it used different generator `ep` ids for the two conditions. I would treat a mismatch here as decisive evidence of a harness defect in the disagreeing implementation, not as a Monte-Carlo disagreement, and I would ask for the two `raw_support` vectors at offset 500 to be diffed channel by channel.

**Check 2 — the comparator's 1.000 at τ = 2.** If the other two also report a saturated comparator at τ = 2, the D-10.3 floor "passes" there on a zero-width interval in all three and R6-OP-03's procedural half becomes a joint finding. If one of them reports a non-saturated value, the first thing to compare is the ridge design: the feature layout `[o_t, a_t, a_{t−1}, a_{t−2}, 1]` with `τ_max = 2` (never the cell's τ), the standardisation reused verbatim for `ã`, and `λ = 1e-4·n` on equal-norm columns. A τ = 2 comparator below 1.0 most likely means the `a_{t−2}` slot was mis-aligned by one.

**Check 3 — the sign of Δ_AUC.** Mine is negative in all four family-L base cells at all three offsets, and negative in 9/9 perturbation cells. If either of the other two reports a positive Δ_AUC, that is the single most consequential disagreement in round 6 and I would want, in this order: their comparator primary in the absent condition (is their comparator weaker than mine?), their `n_lost` and `|S^obs,ε(pre)|` distributions (did they read the pre-event support from a mutated instance? — R6-OP-11), and their offset read step (1499 vs 1482 confusion between the arms).

---

## 2. Cross-checks that should agree exactly, not to Monte Carlo error

These are deterministic and any difference is a defect in one implementation:

| item | my value | where |
|---|---|---|
| probes applied per 2,000-step episode | **99**, at `t ∈ {20, …, 1980}`, fraction 0.0495 | `report.txt` §[12] |
| IBD window units at every read offset | **25** | `report.txt` §[12] |
| offset read steps, comparator / IBD | 1199, 1499, 1999 / 1182, 1482, 1982 | `aux_output.txt` §I |
| channel-constant control on the primary | **exactly 0.500000**, all 15 cells, both conditions | `report.txt` §[5] |
| whitener rank `q` | **6 = 3K** in 15 of 15 cells | `report.txt` §[7] |
| `cond(Σ̂_a)` on `draw_certified({}, 0)` | **212.6** (spec quotes 213) | smoke check |
| un-whitened ĉ on the lost channel, seed 0, offset 500, τ = 0 | `[−7.30, −5.38, −6.25, −4.66, −5.00, −3.76]` | `report.txt` §[10] |
| … τ = 2 | `[−4.53, −3.46, −5.55, −4.40, −6.67, −5.33]` | `report.txt` §[10] |
| static loading control, seed 0 | 0.200 (τ = 0), 0.000 (τ = 2) | `report.txt` §[9] |
| `n_lost` over 40 family-L draws | 1 in 32, 2 in 8 | `report.txt` §[6] |
| `\|S^obs,ε(pre)\|` | 5–6 at τ = 0; **4 at τ = 2 on all 20 draws** | `report.txt` §[6], `aux` §G |
| certified sub-seed for configuration seed 0 | **1** (`n_resamples = 1`), at both N_x | `aux_output.txt` §F |
| `n_lost` for a loss of actuator **1** | **0 on 5/5 seeds at both delays** | `aux_output.txt` §C |

The last row is the one I most want independently confirmed, because R6-OP-05 and much of R6-OP-01/04 rest on it.

---

## 3. Where I expect the three implementations to legitimately differ, and how I would resolve it

1. **The interval estimator** (open choice #1, R6-OP-03). Contract §G names none. I used a percentile cluster bootstrap over instance means, 20,000 resamples, `default_rng(12345)`, two-sided. If the other two used a t-interval on instance means or a BCa, the *point estimates* must still agree; only the bounds may differ. **Resolution rule I propose: adjudicate on the point estimates and on a common re-computation of the intervals from the three implementations' per-instance means, which every implementation should publish.** If a floor verdict flips between estimators, that is itself the finding (it is mine, R6-OP-03), not a disagreement between reviewers.
2. **The perturbation set's shape** (open choice #4). I ran the 3 × 3 cross at N_x = 10, τ = 0, seed 0. If another ran 5 marginal cells or included τ = 2, the overlapping cells (`cp1.0_nm1.0`, `cp0.5_nm1.0`, `cp2.0_nm1.0`, `cp1.0_nm0.5`, `cp1.0_nm2.0`) must agree exactly; the rest is not comparable and should be reported as such rather than aggregated.
3. **The scope cut.** I did not run the alarm channel, ARL_0 or the calibrator (§0 of `findings.md`). If either of the other two did, their ARL and HPDT numbers are uncontested by me and should be adjudicated between the two of them only. My R6-OP-08 is arithmetic and can be checked without running anything.
4. **`instance_seed`** (open choice #6). If another implementation keyed `probe_rng_seed` on the configuration seed (0–9) rather than `inst.seed`, its IBD probe allocation differs from mine on every instance where `n_resamples > 0` — which on my draws is seed 0 at both N_x (sub-seed 1), and family-N seeds 0–4 (resamples 1, 1, 2, 5, 7). The IBD primaries would then differ by more than Monte Carlo error for a reason that is a **specification ambiguity, not an implementation error in either party** (R6-OP-07). I would want this checked before any IBD disagreement is attributed to a bug.
5. **Cholesky vs general solve** (open choice #7). Differences of order 1e-14 in `β`. These cannot move an AUC over 4–6 channels and should be ignored unless a rank is at a tie boundary; the specs' 12-significant-digit tie rounding covers it.

---

## 4. Findings I would specifically ask the other two to confirm or refute

Ordered by how much of my report collapses if they refute it.

1. **R6-OP-01** — that `S^obs,ε(pre)` contains **zero** confounded channels on every draw, and that `seq_ibd`'s primary is identical present/absent. If both confirm, the round-6 exit condition is unattainable as written and that is round 6's headline. *(One line to check: `(inst.S_obs_pre_event() & inst.confounded_channels()).sum()`.)*
2. **R6-OP-05 / `aux` §C** — that `apply_event(("actuator_loss", 1))` removes no observed channel. *(One line: `pre & ~post` after the event on actuator 1.)*
3. **R6-OP-02** — the sign of Δ_AUC. See §1 Check 3.
4. **R6-OP-04** — that `1 − AUC(static l)` exceeds the `seq_ibd` primary at τ = 2. This needs only their static-control number; no new run.
5. **R6-OP-09** — the fault-free `AUC(−Δ vs S_obs)`. Mine is 0.547–0.657, above 0.5 in 15 of 15 cells. If they also see it above 0.5 everywhere, the comparator spec's F1 blindness assertion should be rewritten rather than re-banded.
6. **MUT-O2** — that `pre → pre|post` in `auc_pre_event_support` passes the whole gate. This is deterministic and should reproduce exactly.

---

## 5. Positions I have taken on §L's two open questions, for adjudication

Contract §L asks reviewers to take a position with evidence. Mine, in full in `findings.md` R6-OP-05:

- **`n_lost ≥ 2`: yes, but change the event, not the filter.** Rejection-sampling instances until `n_lost ≥ 2` selects the instance family against the outcome. Drop the generator's `dom` isolation rows, certify CL-4 by choosing an actuator (or a partial loss) whose removal costs ≥ 2 observed channels including at least one downstream `d`, and raise `H` to `τ_max + 2 = 4` so a downstream channel is reachable at every delay.
- **The 0.85 floor: it cannot mean what it meant, and re-valuing it is the wrong repair.** On a 4-channel/1-negative episode the attainable AUCs are {0, ⅓, ⅔, 1} and 0.85 lies strictly between two lattice points. Replace the AUC floor with the per-episode probability that every lost channel ranks strictly below every retained channel, and state the floor on that proportion.

If either of the other two reviewers takes the opposite position on `n_lost ≥ 2` — in particular, if one recommends rejection sampling — the deciding evidence should be whether the resulting instance family is still a sample from the frozen configuration family or a filtered sub-family, and `n_resamples` should be reported per cell in all three implementations to show how much filtering is already happening (mine: 0 or 1 for family L, up to 7 for family N).

---

## 6. What I would revise in my own report if contradicted

- If either implementation shows a **non-zero** `seq_ibd` present/absent difference on a correctly built absent arm, R6-OP-01 drops from critical to a claim about magnitude and I would want to see the mechanism, since `aux` §A's bitwise identity is hard to argue with.
- If either shows the comparator **below** 0.85 in the τ = 2 cells, R6-OP-03's "degenerate interval" half survives but the "passes only degenerately" framing changes, and the floor becomes a straightforward four-of-four failure.
- If either finds `n_lost > 0` for actuator 1 on some seed, R6-OP-05's strongest sentence weakens from "generically insensitive" to "insensitive on 10 of 10 draws I tested", and I would want the union-over-actuators reachability argument re-examined.
- R6-OP-14's λ_rel sensitivity is measured at the ceiling and is **void as evidence**; if another implementation ran it at a non-saturating instance, their number supersedes mine and I withdraw mine.
- MUT-O1 is **killed** by `run_gate.py` (3 `test_generator` failures, `logs/mut_o1_gate.log`) and I report it as a failed mutant. The framework gap it targets — `mutants.failures()` iterates `test_gate` only, so no `reference_generator.py` mutant is registered or expressible — is independent of that verdict and I would like it adjudicated on its own.
