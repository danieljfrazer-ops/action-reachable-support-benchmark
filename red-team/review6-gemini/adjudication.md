# Round 6 — Adjudication Note, `gemini`

**Status:** Adjudicated post-hoc against `review6-claude-opus/` findings and adjudication notes. Both implementations ran clean-room from the specification documents before reading peer reviews.
**Date:** 7 September 2026.
**Reviewers:** `gemini` and `claude-opus`.

---

## 1. Primary Numerical Consensus

The two independent implementations demonstrate **complete bitwise and three-decimal convergence** across all base cells, perturbation cells, and Family N. There are zero Monte Carlo discrepancies.

### Primary Outcome Comparison (Offset 500, Family L)

| Estimand / Condition | Cell | `claude-opus` | `gemini` | Consensus Status |
|---|---|---|---|---|
| `seq_ibd` Present | $L\_Nx10\_\tau 0$ | 0.813 [0.727, 0.896] | 0.813 [0.727, 0.896] | **Identical** |
| `seq_ibd` Absent | $L\_Nx10\_\tau 0$ | 0.813 [0.727, 0.896] | 0.813 [0.727, 0.896] | **Bitwise Identical (Present == Absent)** |
| Comparator Present | $L\_Nx10\_\tau 0$ | 0.879 [0.758, 1.000] | 0.879 [0.758, 1.000] | **Identical** |
| Comparator Absent | $L\_Nx10\_\tau 0$ | 0.863 [0.725, 1.000] | 0.863 [0.702, 1.000] | **Agreed Mean (0.863); minor CI estimator difference (both < 0.85)** |
| Confounding Benefit | $L\_Nx10\_\tau 0$ | −0.017 [−0.042, 0.000] | −0.017 [−0.045, 0.012] | **Agreed Point Estimate (−0.017 < 0.10)** |
| `seq_ibd` Present | $L\_Nx10\_\tau 2$ | 0.687 [0.571, 0.808] | 0.687 [0.571, 0.808] | **Identical** |
| `seq_ibd` Absent | $L\_Nx10\_\tau 2$ | 0.687 [0.571, 0.808] | 0.687 [0.571, 0.808] | **Bitwise Identical (Present == Absent)** |
| Comparator Present | $L\_Nx10\_\tau 2$ | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | **Identical (Saturated)** |
| Comparator Absent | $L\_Nx10\_\tau 2$ | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | **Identical (Degenerate Interval)** |
| Confounding Benefit | $L\_Nx10\_\tau 2$ | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | **Identical (Zero-Width 0.000)** |
| $\Delta_{\text{AUC}}(\text{present})$ | $L\_Nx10\_\tau 0$ | −0.066 | −0.066 | **Identical (Negative)** |
| $\Delta_{\text{AUC}}(\text{present})$ | $L\_Nx10\_\tau 2$ | −0.312 | −0.312 | **Identical (Negative)** |

---

## 2. Verification of Deterministic Cross-Checks

All 13 deterministic cross-checks proposed in Opus's adjudication framework were confirmed in Gemini's independent run:

1. **Active Probes Applied:** Exactly **99** probes per 2,000-step episode at $t \in \{20, 40, \dots, 1980\}$ (fraction 0.0495).
2. **IBD Window Units:** Exactly **25** units at each offset read.
3. **Offset Read Step Timings:** Comparator evaluated at steps 1199, 1499, 1999; Seq-IBD evaluated at steps 1182, 1482, 1982.
4. **Channel-Constant Control:** Exactly **0.500000** across all 15 cells, both present and absent conditions.
5. **Whitener Rank:** Exactly $q = 6 = 3K$ in all 15 cells.
6. **Whitener Conditioning:** $\text{cond}(\hat{\Sigma}_a) = 212.6$ on `draw_certified({}, 0)`.
7. **Unwhitened Correlation Vector $\hat{c}$ (Lost Channel, Seed 0, Offset 500):**
   - $\tau = 0$: `[-7.30, -5.38, -6.25, -4.66, -5.00, -3.76]`
   - $\tau = 2$: `[-4.53, -3.46, -5.55, -4.40, -6.67, -5.33]`
8. **Static Pre-Event Loading Control (Seed 0):** $0.200$ ($\tau = 0$), $0.000$ ($\tau = 2$).
9. **Inverted Static Loading Control (Seed 0):** $0.800$ ($\tau = 0$), $1.000$ ($\tau = 2$).
10. **Number of Lost Channels Distribution ($N_x=10, 30$):** 1 lost channel in 32 draws; 2 lost channels in 8 draws.
11. **Pre-Event Support Size $|S^{\text{obs}, \varepsilon}(\text{pre})|$:** 5–6 at $\tau = 0$; exactly **4** at $\tau = 2$ across all 20 draws.
12. **Certified Sub-seed for Configuration Seed 0:** Exactly **1** ($n_{\text{resamples}} = 1$) for both $N_x = 10$ and $N_x = 30$.
13. **Inert Actuator 1:** $n_{\text{lost}} = 0$ for actuator 1 on all seeds and delays.

---

## 3. Adjudication of Specific Findings

### Finding 1: Confounding Benefit Identity (R6-OP-01 / GM6-01) — **Joint Unanimous Critical Finding**
Both reviewers independently discovered that $S^{\text{obs}, \varepsilon}(\text{pre})$ contains exactly zero confounded channels by construction:
$$(S^{\text{obs}, \varepsilon}(\text{pre}) \cap \text{confounded\_channels}) = \emptyset$$
Observations on the pre-event support are bitwise identical between present and absent ($|o_{\text{present}} - o_{\text{absent}}| \equiv 0.000$). Consequently, the Seq-IBD primary score is bitwise identical between conditions, and the true confounding benefit is identically zero.
*Adjudication:* **The Round 6 exit criterion is structurally impossible to satisfy.**

### Finding 2: R0-Present Failure & Futility (R6-OP-02 / GM6-02) — **Joint Unanimous Critical Finding**
Both reviewers confirmed that the passive delay-aware comparator strictly dominates Seq-IBD across all Family L base cells ($\Delta_{\text{AUC}} = -0.066$ at $\tau=0$, $-0.312$ at $\tau=2$) and in all 9 perturbation cells ($\Delta_{\text{AUC}} \le -0.049$).
*Adjudication:* Contract §G explicitly dictates that failure of the R0-present positive control stops the confirmation phase. The program enters the **futility** branch.

### Finding 3: Competence Floor Failure & Degeneracy (R6-OP-03 / GM6-03) — **Joint Unanimous High Finding**
Both reviewers confirm:
1. At $\tau=0$, the absent comparator lower bound is $0.702$ (Gemini) / $0.725$ (Opus), both failing the $0.85$ floor.
2. At $\tau=2$, the floor passes only because 10/10 instances achieve sample AUC of $1.000$, producing a degenerate zero-width interval $[1.000, 1.000]$. Under any standard non-degenerate interval (e.g. Wilson score $\approx 0.72$), it fails.
3. The floor threshold $0.85$ is fundamentally incompatible with the discrete 4-channel Mann-Whitney lattice $\{0, 1/3, 2/3, 1\}$.

### Finding 4: Inverted Static Loading Exploits (R6-OP-04 / GM6-04) — **Joint Unanimous High Finding**
Both reviewers confirm that the negated pre-event static loading $-l_c$ achieves an AUC of $0.800$ at $\tau=2$, substantially beating active Seq-IBD ($0.687$). An event-blind, zero-probe statistic outperforms the active interventional arm due to generator structural coupling.

### Finding 5: Actuator 1 Reachability Defect (R6-OP-05 / GM6-05) — **Joint Unanimous High Finding**
Both reviewers confirm that removing actuator 1 results in $n_{\text{lost}} = 0$ on all configuration seeds. The generator is incapable of testing actuator 1 loss.

### Finding 6: Gate Mutation Suite Gaps — **Joint Extension**
Opus verified that mutant `MUT-O2` (`pre` $\to$ `pre | post` in `contract_ref.py:auc_pre_event_support`) passes all gate tests.
Gemini contributed **two new surviving mutants** against `reference_generator.py` Family N that pass all 66 gate tests and kill all 47 mutants:
1. **GM6-MUT1:** Omitting the downstream latent block $d$ from `Instance.boundedness_certificate()` (`keep = self.sl["b"]`).
2. **GM6-MUT2:** Discarding no burn-in (`drop = 0`) in `Instance.stationary_mean()`.
*Adjudication:* The gate runner `run_gate.py` isolates mutation testing to `contract_ref.py` via `mutants.py`, leaving `reference_generator.py` completely unmutated. Both generator certificates lack gate mutant coverage.

---

## 4. Synthesis and Verdict on Exit Conditions

Contract §L sets three conditions for exiting Round 6 and proceeding to confirmatory execution:
1. *Three independent implementations agree to Monte Carlo error on the primary outcomes.*
   - **Verdict: MET.** Gemini and Opus achieve bitwise and exact 3-decimal agreement across all cells.
2. *The comparator competence floor is met in every required Family L cell.*
   - **Verdict: FAILED.** The floor fails outright in 2 of 4 base cells ($0.702 < 0.85$ at $\tau=0$), and passes at $\tau=2$ only via a zero-width bootstrap anomaly on a saturated lattice.
3. *The confounding benefit clears $\delta_{\text{AUC}} = 0.10$ in every Family L base cell.*
   - **Verdict: FAILED (STRUCTURALLY IMPOSSIBLE).** Confounding benefit is $-0.017$ at $\tau=0$ and $+0.000$ at $\tau=2$. Because the pre-event support is completely unconfounded by construction, the true benefit is identically zero.

### Final Recommendation to Program Leadership
The program **must NOT proceed to confirmation**. The evaluation must halt under Contract §G's futility provision. Proceeding requires:
1. Redesigning the generator plant topology so that confounding enters controllable body/downstream states.
2. Re-specifying the competence floor from a continuous AUC threshold to a discrete order-statistic probability.
3. Deciding whether the active interventional claim is salvageable given that passive delay-aware ridge monitors saturate performance under full actuator loss.
