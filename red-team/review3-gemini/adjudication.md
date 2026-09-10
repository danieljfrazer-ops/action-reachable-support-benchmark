# Adjudication of Peer Reviews (Gemini Round 3)

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 7 September 2026  
**Target Version:** Frozen version `e662b7429b6b347d`  
**Inputs Evaluated:** `review3-claude-opus/sim_d8.py`, `review3-claude-opus/sim_d8.output.txt`.

---

## 1. Status of Peer Reviews in Round 3

At the time of this evaluation (7 September 2026):
1. **Claude Opus (`review3-claude-opus/`):**
   - Has committed an extensive simulation script `sim_d8.py` and execution output `sim_d8.output.txt`.
   - The simulation script ran through the primary confirmation cells (R0/R1 present/absent, $N_x \in \{10, 30\}$), the alarm channel benchmarks, the F1 support correctness benchmarks, the co-primary $p_c$ distractor evaluations, and the PAVA calibration gate checks, before halting with a `ValueError` in an exploratory ablation block `attack_null_under_u()` (due to a 2000 vs 2001 step dimension mismatch).
   - A formal `findings.md` markdown table has not yet been committed to `review3-claude-opus/`.
2. **Codex (`review3-codex/`):**
   - No Round 3 review directory or findings have been committed yet.

---

## 2. Adjudication of Available Peer Evidence (Claude Opus Simulation)

We evaluated the empirical findings produced by Claude Opus's simulation (`sim_d8.output.txt`) against our independent simulation (`review3-gemini/sim_d8_gemini.py`) and the Draft-2 specification:

| Finding / Claim Evaluated | Peer Severity | Gemini Verdict | Reason (One Line) |
|---|:---:|:---:|---|
| **D-8 Alarm Power Deficit** (Sequential IBD has no alarm power within $H_{det}=200$ at $ARL_0=1000$) | High | **Valid** | Confirmed by our independent simulation: IBD alarm rate within $H_{det}$ under the event (~0.35–0.43) is indistinguishable from the no-event control (~0.37–0.43). |
| **D-8 Support $F_1$ Futility** (Sequential IBD fails to win on $F_1$ against CUSUM, achieving $\Delta_{F1} \le 0.0$ across all cells) | High | **Valid** | Confirmed by our independent simulation: at offset 500, IBD achieves $F_1 = 0.150$ vs $0.857$ for CUSUM ($\Delta_{F1} = -0.707$), failing the $\delta_{F1} = +0.10$ threshold and decisively re-opening D-8. |
| **Rank Null Exchangeability Failure** (Autocorrelated context and dynamic persistence break the Mann–Whitney null) | High | **Valid** | Opus measured null $a_c$ standard deviation of $1.42$ and $P(\|a_c\| > 1.96) = 13.7\%$ under the null; serial correlation invalidates exchangeability. |
| **PAVA Transition-Band Contamination** (Calibration pairs pool pre- and post-event data within trailing windows) | High | **Valid** | Trailing window $W_{steps}=500$ is 60% pre-event at offset 200 and retains pre-event transitions during calibration, corrupting the empirical mapping. |
| **Threshold 0.5 Decision Rule Collapse** (PAVA probabilities under low prevalence never cross 0.5) | High | **Valid** | Confirmed: when active channel prevalence is $<15\%$, uncalibrated isotonic regression shrinks predictions below 0.5, yielding $\hat{S} = \emptyset$ ($F_1 = 0.0$). |
| **Epoch Grid Window Discrepancy** (Actual post-event fraction on discrete epoch grid differs from continuous spec) | Low | **Valid** | Probes fire on discrete epochs ($t=1003, 1043, 1183, \dots$), shifting actual post-event unit fractions slightly from the idealized table in §4. |
| **Array Dimension Fragility in `max_pairwise_corr`** (Script crashed on $T=2000$ vs $T=2001$ concatenation) | Low | **Valid** | `contract_ref.max_pairwise_corr` assumes strictly equal first dimensions and lacks explicit shape assertion guards. |

---

## 3. Next Steps

When Claude Opus and Codex commit their formal `review3-*/findings.md` tables, this document will be updated with row-by-row adjudications for all individual finding IDs.
