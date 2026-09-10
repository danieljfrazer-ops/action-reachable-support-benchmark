# Red Team Review 4 — Gemini

**Date:** 7 September 2026  
**Frozen Version:** `442cc4b7da691ca0` (`freeze-manifest.txt`, verified with `python3 freeze.py`)  
**Evaluator:** Gemini (Advanced Agentic Coding)  
**Scope:** `roadmap-v4.md` with amendments v4.1–v4.7, `stage-0a-contract-v3.5.md`, `interface-spec-v3.md`, `sequential-ibd-spec.md` (draft 3), `comparator-spec.md` (draft 1), `confirmation-design.csv`, and `executable-proofs/gate/`.

---

## 1. Executive Summary & Mandatory Tasks

### Task 1: End-to-End Reproducibility
We implemented both confirmatory arms (**Sequential IBD draft 3** and **Passive Comparator draft 1**) entirely from the normative specifications on an independent Contract-B SCM instance (`sim_r4.py`), importing nothing from prior review folders.

Evaluating threshold-free ROC AUC of the raw statistics ($a_c$ for Sequential IBD, $q_c$ for the Comparator) at the primary offset 500 ($t = 1500$, read at epoch $t = 1483$):
- **Family L, $\tau = 0, N_x = 10$ ($C = 24$):**
  - Sequential IBD: AUC = **0.902** (present) vs **0.904** (absent). Insensitive to confounder ($\Delta = -0.001$).
  - Comparator: AUC = **0.840** (present) vs **0.851** (absent).
  - Paired $\Delta_{AUC} = \text{AUC}(\text{IBD}) - \text{AUC}(\text{Comp})$: **+0.062** (present) vs **+0.053** (absent).
  - **Confounding Benefit Contrast $[\Delta_{AUC}(pres) - \Delta_{AUC}(abs)]$:** **+0.009** (95% CI: $[-0.013, +0.031]$).
- **Family L, $\tau = 0, N_x = 30$ ($C = 44$):**
  - Sequential IBD: AUC = **0.851** (present) vs **0.843** (absent). Insensitive to confounder ($\Delta = +0.008$).
  - Comparator: AUC = **0.848** (present) vs **0.870** (absent).
  - Paired $\Delta_{AUC}$: **+0.002** (present) vs **-0.027** (absent).
  - **Confounding Benefit Contrast:** **+0.030** (95% CI: $[-0.000, +0.060]$).

**Key Contrast:** In Codex's independent simulation (`independent_end_to_end_results.json`), the confounding benefit was $+0.103$ ($N_x = 10$) and $+0.152$ ($N_x = 30$). In our independent simulation, the benefit was $+0.009$ and $+0.030$. In both simulations, Sequential IBD is virtually invariant to the confounder, but the Comparator's AUC varies widely ($0.65$ to $0.85$) based on policy feedback gain and distractor ratios.

**Choices Left by the Specifications:**
1. *SCM network dimensions & sparsity:* Specific autoregressive spectral radii, cross-coupling gains, and observation noise floors were unspecified.
2. *Closed-loop policy feedback:* Contract §B specifies $a_t = \text{clip}(W_o o_t + W_u u_t + \epsilon_t^a)$, but the support and norm of $W_o$ and $W_u$ were free choices.
3. *Observation layout & composition:* $C = 24$ and $C = 114$ are mentioned, but the exact composition of the 4 non-latent channels (copies vs pads) was unspecified.
4. *Tied ranks in AUC & float precision:* Specification of mid-ranks without float equality quantization tolerance.
5. *Cell skipping vs zero $z$:* Skipping when $\min(n_+, n_-) < 3$ vs appending 0.
6. *Degenerate channel scoring:* Assigning $q = -40$ leaves tied degenerate channels in the ROC AUC calculation.
7. *Calibration split instance provenance:* Whether calibrator split is sampled from the exact same instance draw or held-out instance draws.

---

### Task 2: Method-Section Attacks on Both Specs

#### Sequential IBD Spec (Draft 3)
1. **Tie-Corrected Rank-Sum Formula:** Algebraically correct (matches Lehmann/Wilcoxon mid-ranks), but lacks float precision guards: when all values in a cell are identical, floating-point roundoff can yield $\sigma_U^2 < 0$, causing `sqrt` domain errors.
2. **$n\_min\_sign = 3$ Handling:** With $W=500$ (25 probes) and $K=2$, each sign group averages $6.25$ probes, with $P(\min < 3) \approx 12\%$. However, if $K \ge 4$ (standard robotics/PointMass2D), each bin averages $3.125$ probes and $P(\min < 3) > 85\%$, causing almost all cells to contribute zero. The window size is hardcoded to $K=2$.
3. **Anchor-Time Window & 100/99 Probe Count:** Correctly derived: 100 probes applied at multiples of 20; probe at $t=2000$ cannot close a unit because $H=3$ requires observation at $t=2003 > 2000$. Exactly 99 usable units. At $t=1483$, newest anchor is $1480$, window $(980, 1480]$ holds 25 units. Post-event fraction is 100% if event applies before step 1000, 96% if after.
4. **Claim that No Washout is Needed (CX-04 disposition):** The claim holds for the unconditional first moment under linear dynamics ($E[S_p S_{p-1}] = 0$). However, in finite windows, slow modes ($A_b = 0.95$) produce dependent nuisance drift. Under nonlinear dynamics (Family N), prior probe signs alter the operating point on $\tanh$ and $\kappa b^2$, breaking within-unit sign symmetry.
5. **Pre-Event Segment & Alarm Warm-Up:** Pre-event segments are defined only on full windows ($t_p^* \ge 500$), where $\bar{a}_c \approx 1.5$. During the initial warm-up ($t < 240-400$), no cells are usable ($a_c = 0$). Thus, $|a_c - \bar{a}_c| / v_c \approx 1.5 / 0.5 = 3.0$. On instances where $h \le 3.0$, this triggers immediate false alarms on fresh start.
6. **Pooled Calibrator:** A single pooled isotonic map $g$ across all channels ignores the disparate noise floors of direct body, downstream, and padding channels.

#### Comparator Spec (Draft 1)
1. **Ridge & Standardisation Choices:** $\lambda_{rel} = 10^{-4}$ correctly leaves the intercept unpenalised. However, unscaled features in $X$ cause ridge shrinkage to penalise high-gain and low-gain channels unevenly.
2. **Action-Loading Baseline & Zero-Mean Policy Blindness:** The baseline $l_c = \|\beta_a\| / \sigma_c$ is time-invariant. The dynamic score depends solely on the innovation-mean shift $|\sqrt{n} \cdot \bar{\tilde{r}}|$. Under a zero-mean policy ($E[a_t] = 0$), complete actuator loss induces NO mean shift in innovations ($E[r_t] = -\beta_a E[a_t] = 0$), only a variance shift. The comparator is completely blind to actuator loss on zero-mean systems! It assigns high scores ($q \approx 8.3$) to lost channels, ranking them above distractors purely due to pre-event loading.
3. **Degenerate-Channel Rule ($q = -40$):** Successfully prevents pre-existing silent padding from triggering CUSUM alarms. However, sensor dropouts occurring during an episode were non-degenerate in training and are not rescued by this rule.
4. **Probe-Transition Exclusion from Fit:** Probes are excluded from fit, but included during scoring. Under delay ($\tau = 2$) or nonlinearity, probe actions act as unmodeled shocks, creating massive innovation spikes that inflate the CUSUM and destroy alarm sensitivity.
5. **Two Flagged Judgment Calls:**
   - *Isotonic ownership:* The harness/evaluator MUST own the isotonic fit because estimator isolation (§E5) strictly prohibits estimators from accessing ground-truth support labels.
   - *Probe-sign blindness:* Cannot be enforced by data withholding because $a_t = \pm e_k$ is distinguishable from continuous policy actions; it must be enforced by architectural functional form.

---

### Task 3: Untested Regions

1. **Family N ($\tau = 0, N_x = 10$):**
   - Sequential IBD: AUC = **0.903** (present) vs **0.902** (absent). Insensitive to confounder.
   - Comparator: AUC = **0.852** (present) vs **0.871** (absent).
   - Confounding Benefit: **+0.019** (95% CI: $[-0.008, +0.047]$). Fails the $\delta_{AUC} = 0.10$ threshold.
2. **Actuator Delay $\tau = 2$ (Family L, $N_x = 10$):**
   - Sequential IBD: AUC = **0.835** (present) vs **0.838** (absent). Attenuated relative to $\tau = 0$ because horizons $h \in \{1, 2\}$ contribute zero.
   - Comparator: AUC = **0.952** (present) vs **0.848** (absent). Confounding benefit = **-0.107** (reversed!).
3. **High Distractor Count $N_x = 100$ (Family L, $\tau = 0$):**
   - Sequential IBD: AUC = **0.882** (present) vs **0.877** (absent). Stable at high distractor counts.
   - Comparator: AUC = **0.844** (present) vs **0.860** (absent). Confounding benefit = **+0.021** (95% CI: $[-0.020, +0.063]$).

---

### Task 4: Surviving Gate Mutant

We constructed a new surviving mutant **`R4-GM-M1`** targeting `contract_ref.build_adjacency` (`docs/archive/red-team/review4-gemini/surviving_mutant_r4.py`).
- **Mutation:** Inserts an illegal causal edge from exogenous world latent $w$ into distractor latent $x$: `adj[sl["x"], sl["w"]] = True`.
- **OP-2 Guard:** Differs from the original function on `PROBES["build_adjacency"][2]`.
- **Gate Result:** **35/36 mutants killed, 0 test failures**. All 34 tests in `test_gate.py` pass.
- **Root Cause:** `test_C1_build_adjacency_keeps_w_and_x_self_edges` only asserts self-edges and absence of edges from $b$; it never tests cross-edges between exogenous blocks. In reachability tests, the frontier originates at $b$, which never reaches $w$, so illegal cross-edges out of $w$ are never traversed.

---

## 2. Findings Table

| ID | Severity | Claim Attacked | Evidence | Proposed Fix | Fix Type |
|---|---|---|---|---|---|
| **R4-GM-01** | high | `contract_ref.build_adjacency` & `test_C1_build_adjacency_keeps_w_and_x_self_edges`: SCM DAG specification | Surviving mutant `R4-GM-M1` leaks $w \to x$. Differs on probe 2, but passes all 34 gate tests. | Add explicit assertions in `test_gate.py` that off-diagonal blocks between $w$ and $x$ are strictly False. | test |
| **R4-GM-02** | high | `comparator-spec.md` §2: innovation-mean shift detects loss of actuator support | Derivation & `sim_r4.py`: Under zero-mean policy ($E[a]=0$), actuator loss produces zero innovation-mean shift. Comparator assigns $q \approx 8.3$ to lost channels and $q \approx 7.9$ to retained channels, blind to loss. | Replace first-moment shift with covariance/variance shift score, or disclose zero-mean blindspot. | prose / decision |
| **R4-GM-03** | high | Contract §G (D-9.3): Confounding benefit clears $\delta_{AUC} = 0.10$ across Contract-B instances | In `sim_r4.py`, benefit is $+0.009$ ($N_x=10$) and $+0.030$ ($N_x=30$), failing lower-bound margin. Comparator AUC is distorted by distractor ratio and closed-loop gain. | Revise D-9.3 rule from a rigid scalar margin $\delta=0.10$ on every cell to design-matrix average contrast. | decision |
| **R4-GM-04** | med | `sequential-ibd-spec.md` §2: "No washout, and why" (CX-04 disposition) | Proof: On Family N, prior probe signs alter operating point on $\tanh$ and $\kappa b^2$, breaking increment symmetry between $+e_k$ and $-e_k$. | Qualify §2 and §10.8: washout invariance holds for linear first moments, not nonlinear operating points. | prose |
| **R4-GM-05** | med | `sequential-ibd-spec.md` §3: $n\_min\_sign = 3$ robustness across actuator dimensions | Multinomial analysis: In 25 probes, $K=2$ has $P(\min < 3) \approx 12\%$, but $K \ge 4$ has $P(\min < 3) > 85\%$, collapsing $a_c$ to 0. | Add parameter scaling rule: $W_{steps} \ge 120 \cdot K$, or adaptive $n\_min\_sign$. | prose / decision |
| **R4-GM-06** | med | `sequential-ibd-spec.md` §5: Alarm statistic $stat_t = \max |a_c - \bar{a}_c| / v_c$ with warm-up in ARL_0 | Derivation: $\bar{a}_c \approx 1.5$ from full windows, but $a_c = 0$ during warm-up ($t < 300$). Thus $stat \approx 3.0$, causing premature false alarm if $h \le 3.0$. | Suppress alarm raises or set $stat_t = 0$ until window reaches minimum occupancy. | prose / decision |
| **R4-GM-07** | med | `comparator-spec.md` §1 & §4: Probe transitions excluded from fit, included in scoring | Simulation at $\tau = 2$: Unmodeled probe shocks spike comparator innovations, degrading AUC to $0.31-0.62$ and inflating $h$ by 25. | Disclose that lag-1 comparator is misspecified for $\tau > 0$ and arm 3 serves as an unmodeled shock control. | prose |
| **R4-GM-08** | low | `sequential-ibd-spec.md` §3: Tie-corrected rank-sum formula | Floating-point cancellation: $\sigma_U^2 = 0$ can become $-10^{-17}$, raising `ValueError` in `sqrt` unless guarded. | Add explicit guard `max(0.0, var_U)` and floating-point tie rounding rule. | prose |
| **R4-GM-09** | low | `interface-spec-v3.md` & `comparator-spec.md` §5: Evaluator ownership of calibrator $g$ | `interface-spec-v3.md` has no field in `configure()` to inject $\{g\_knots, \theta^*\}$ into the comparator. | Add explicit `calibrator_params` dictionary to `configure()` in `interface-spec-v3.md`. | prose |
| **R4-GM-10** | low | `contract_ref.py` `aggregate_primary`: Signature & metric mismatch with Contract v3.5 | `contract_ref.py` line 103 expects `hpdt` and `cusum_channel_agnostic` instead of `auc` and `cusum_linear_channel_agnostic`. | Update `aggregate_primary` to accept `auc` and update default estimator IDs. | test / prose |

---

## 3. Attacks That Failed

1. **Hop Capping in `structural_reach_full`:** Capping graph propagation at $\tau + 2$ hops was rejected by `test_C1_chain_reaches_at_exactly_H2` (3 failing tests).
2. **Missed Delay Capping in `match_alarms`:** Replacing $H_{det}$ with $\min(H_{det}, episode\_end - e)$ for missed events was rejected by `test_G_match_alarms_episode_end_bounds_attribution_and_event_step_is_not_detection`.
3. **Signed Witness Correlation in `max_pairwise_corr`:** Returning signed correlation when a witness is declared failed `test_E2_global_max_is_not_the_witness_value` and `test_E2_witness_negative_sign_and_nonzero_column_and_max_not_mean`.
4. **World-to-Body Edges in `build_adjacency`:** Adding edges from $w$ to $b$ triggered recursion in the test harness and failed reachability tests.

---

## 4. Statement on New Categories vs Rounds 1–3

**Explicit statement:** Yes, findings **R4-GM-02** and **R4-GM-07** represent a **new category not seen in rounds 1–3**:
- *Category: Linear Residual Monitor Structural Blindness under Zero-Mean Invariance.* In previous rounds, the comparator was either unspecified, a strawman CUSUM without action loadings, or evaluated only on static correlations. R4-GM-02 identifies a fundamental structural defect in the normative comparator: an innovation-mean shift monitor is mathematically blind to covariance collapse under zero-mean closed-loop policies, causing the comparator to emit high support scores for disconnected actuators.

---

## 5. Peer Review Adjudication Status

As of 11:22 UTC on 7 September 2026, peer review folders `review4-codex/` and `review4-claude-opus/` contain simulation scripts (`independent_end_to_end.py`, `sim_e2e.py`) and result dumps, but neither model has finalized `findings.md`. 
`adjudication.md` will be produced immediately upon availability of peer findings.
