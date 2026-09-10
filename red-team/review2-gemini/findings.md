# Review of Frozen Version d23960e6da441de7 (Gemini Round 2)

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 6 September 2026  
**Scope Under Review:** `roadmap-v4.md` as amended by `roadmap-v4.1-amendments.md`, `stage-0a-contract-v3.1.md`, `interface-spec-v2.md`, `confirmation-design.csv`, and `executable-proofs/gate/`.  
**Clean Gate Execution:** Venv created per `run_gate.py` instructions (`python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && python run_gate.py`).  
- **Exit code:** 0.  
- **Test suite:** 17 passed, 0 failed.  
- **Mutation runner (`mutants.py`):** 8/8 registered mutants killed (CX tau-cap, GM-1 999B, GM-2 skip-H2, CL UM-2 no-delay, CL UM-1 no-downstream, M8 gain-ignored, HPDT censoring-excluded, M7 negative-power).

---

## 1. Executable Verification of Contract Equation C4

Contract Equation C4 from `stage-0a-contract-v3.1.md` was executed on a rectangular delayed system with non-diagonal state dynamics:
- Matrix $A_3 \in \mathbb{R}^{3 \times 3}$: `[[0.8, 0.1, 0.0], [0.0, 0.7, 0.2], [0.1, 0.0, 0.6]]`
- Matrix $B_{rect} \in \mathbb{R}^{3 \times 2}$: `[[1.0, 0.2], [0.1, 0.9], [0.0, 0.3]]`
- Delay $\tau = 1$, horizon $h = 3$, probe action $a = (0.5, -0.5)^T$.

Numerical execution in `contract_ref.py`:
- `open_loop_response(A3, B_rect, a, h=3, tau=1)` = `[0.32, 0.444, 0.062]`
- `jacobian_piecewise(A3, B_rect, h=3, tau=1) @ a` = `[0.32, 0.444, 0.062]`
- Maximum absolute difference: $< 5.55 \times 10^{-17}$ (exact to machine precision).
- At $h \le \tau$ ($h \in \{1\}$), both identically evaluate to $\mathbf{0}$.

Equation C4 is mathematically exact and verified on delayed rectangular systems.

---

## 2. Surviving Adversarial Mutant (Adversarial Gate Attack)

As required by the review instructions, we constructed and executed a new adversarial mutant against the frozen gate:

### Mutant GM2-1: Premature Graph Propagation During Actuator Delay Queue
**Script:** `review2-gemini/surviving_mutant_premature_delay_propagation.py`
```python
def mutant_premature_propagation(A_b, B, H, tau=0, C_d=None, A_d=None, A_w=None, A_x=None):
    adj, sl = ref.build_adjacency(A_b, C_d, A_d, A_w, A_x)
    N = adj.shape[0]; reach = np.zeros(N, bool)
    if H <= tau:
        return reach
    frontier = np.zeros(N, bool); frontier[sl['b']] = (B != 0).any(axis=1)
    reach |= frontier
    # MUTANT: propagates for H-1 hops regardless of tau!
    # Replaces `range(tau + 2, H + 1)` with `range(2, H + 1)`:
    for _ in range(2, H + 1):
        frontier = (adj.astype(int) @ frontier.astype(int)) > 0
        reach |= frontier
    return reach
```
- **Execution Result:** **17 passed, 0 failed. Exit code 0 (SURVIVED).**
- **Causal Violation:** In a delayed system ($\tau \ge 1$), the control action only arrives at the body latents at $h = \tau + 1$. Traversing an edge $b_0 \to b_1$ in $A_b$ requires an additional step, so $b_1$ cannot be reached until $H \ge \tau + 2$. The mutant executes multi-hop propagation immediately at $H = \tau + 1$, allowing causal signals to leapfrog the physical actuator delay queue and travel faster than 1 hop per step.
- **Why the gate failed to reject it:**
  1. `test_C1_delay_empties_support_until_arrival` tests delayed reachability using `B_rect`, where all 3 rows of $B$ are non-zero (`(B_rect != 0).any(axis=1)` is `[True, True, True]`). Because all nodes are directly reached by $B$ on step $\tau + 1$, there are no unreached nodes in $b$, so downstream propagation through $A$ is never tested with delay!
  2. `test_C1_chain_reaches_at_exactly_H2` tests a 3-node chain $b_0 \to b_1 \to b_2$, but runs with default $\tau = 0$.
  3. `test_K4` and `test_K10` test multi-hop reachability, but both run with default $\tau = 0$.
  Consequently, **the interaction between actuator delay $\tau \ge 1$ and multi-hop network reachability is completely untested in the gate.**

*(Note: We also verified Codex's surviving mutant `review2-codex/surviving_mutant_ad_omission.py`, which deletes internal downstream edges $A_d \to d$ and survives with 17 passed, 0 failed because case K10 tests only a 1-dimensional $d$ component).*

---

## 3. Findings Table

| ID | Severity | Claim Attacked | Evidence (Live Sources where External) | Proposed Fix | Fix Type |
|---|:---:|---|---|---|:---:|
| **GM2-1** | **High** | The gate verifies C1 structural reachability with delay over multi-hop networks (T-C1-delay, T-C1-chain). | `surviving_mutant_premature_delay_propagation.py` replaces `range(tau + 2, H + 1)` with `range(2, H + 1)` and exits 0 (17 passed, 0 failed). `test_C1_delay_*` uses `B_rect` where all rows are nonzero, never asserting delayed multi-hop propagation. | Add a test with a linear chain $b_0 \to b_1 \to b_2$ at $\tau = 1$, asserting that at $H = 2$, reach is $[1, 0, 0]$, at $H = 3$ reach is $[1, 1, 0]$, and at $H = 4$ reach is $[1, 1, 1]$. Register this mutant in `mutants.py`. | `test` |
| **GM2-2** | **High** | Downstream latent reachability covers multi-hop internal dynamics through $A_d$ (Contract A, C1, K10). | `review2-codex/surviving_mutant_ad_omission.py` sets `adj[slices['d'], slices['d']] = False` and exits 0 (17 passed, 0 failed). Case K10 in `test_gate.py` defines $N_d = 1$ ($C_d = [[1, 0]]$, $A_d = [[0.5]]$), so multi-hop propagation $d_0 \to d_1$ through $A_d$ is never asserted. | Extend test K10 or add test K11 with $N_d = 2$, $C_d: b_0 \to d_0$, $A_d: d_0 \to d_1$, asserting $d_0$ is reached at $h = \tau + 2$ and $d_1$ at $h = \tau + 3$. | `test` |
| **GM2-3** | **High** | The closed-loop spectral radius bound $\rho_{cl} \le 0.98$ certifies stability for all SCM configurations including delayed and downstream cells (Contract 0 line 29, Contract B line 61). | Contract B defines $\rho_{cl}$ on $A_b + B W_o \text{diag}(\text{gain} \odot \text{avail}) \text{Assign}_b$. For $\tau \ge 1$, the feedback control system is augmented with state-delay queue $a_{t-1}, \dots, a_{t-\tau}$. A matrix with zero-delay $\rho < 0.98$ can have augmented closed-loop eigenvalues $|\lambda| > 1$ (delay-induced instability). Moreover, if the policy observes downstream latents $d$, the loop $b \to d \to o \to a \to b$ is excluded from the check. | Formulate the exact augmented closed-loop state transition matrix over $[b_t; d_t; a_{t-1}; \dots; a_{t-\tau}]$ and certify its spectral radius $\le \rho_{cl}$. Resample if violated. | `test + prose` |
| **GM2-4** | **High** | A target $ARL_0 = 1000 \pm 10\%$ can be calibrated over $\ge 20,000$ stationary steps, and uncalibratable methods are fairly excluded (Contract 0 line 24, Contract G line 114). | Elementary renewal theory: in 20,000 steps with true $ARL_0 = 1000$, expected false alarms $N = 20$. Relative standard error is $1/\sqrt{20} \approx 22.4\%$. The probability of falling within $\pm 10\%$ ($19 \le N \le 22$) is only $\approx 34\%$ under Poisson arrivals. Over $65\%$ of runs will fail the tolerance purely from finite-sample variance. Labeling these "not calibratable" and excluding them from the primary creates severe survivorship and selection bias. | Replace the fixed 20,000 step minimum with a sequential stopping rule that accumulates a target number of false alarms (e.g. $\ge 100$ events) to bound standard error within $\pm 10\%$. Prohibit dropping methods from primary comparisons; report uncalibrated regimes under a partial-order endpoint. | `decision + prose` |
| **GM2-5** | **High** | `confirmation-design.csv` correctly aligns row roles with the primary confirmatory claim and interaction gate $I$ (Roadmap v4.1 E1, E2, Contract G). | Amendment E1 mandates that R1 superiority requires the interaction $I = [\Delta(R1, \text{present}) - \Delta(R1, \text{absent})] - [\Delta(R0, \text{present}) - \Delta(R0, \text{absent})] > 0$. In `confirmation-design.csv`, all `present` rows have `role=primary`, while all `absent` rows have `role=diagnostic_2x2`. An automated harness filtering by `role=primary` lacks the `absent` rows and cannot compute $I$; conversely, treating `diagnostic_2x2` rows as confirmatory compromises role semantics. | Introduce explicit role values: `role=confirmatory_interaction` or declare in Amendment E1 that the confirmatory evaluation consumes both `primary` and `diagnostic_2x2` rows according to a frozen query. | `decision` |
| **GM2-6** | **High** | The adopted co-primary outcome "confounded-channel false support" is well-defined as mean $p_c$ on distractor channels at offsets $\{10, 50, 200\}$ (Roadmap v4.1 E7, Contract G line 113). | Contract Section 0 line 27 sets $f_{conf} = 0.5$, meaning half of distractor channels are unconfounded noise. Averaging over all distractor channels dilutes the confounding effect by $50\%$. Furthermore, when an episode terminates early before step 200, post-termination values of $p_c$ do not exist, and missingness handling is unspecified. | Define the metric strictly on the oracle-identified confounded distractor subset (with unconfounded channels reported as a negative control). Specify missing-data handling for early-terminated episodes (e.g. carry-forward, imputation, or conditional evaluation). | `decision + prose` |
| **GM2-7** | **Medium** | The primary estimand aggregation function `aggregate_primary()` is frozen and part of the gate (Roadmap v4.1 E2, E10, Interface v2 line 19). | `interface-spec-v2.md` line 19 lists `aggregate_primary()` in `contract_ref.py`. However, `contract_ref.py` contains no such function, and `coverage-matrix.md` line 17 admits it is uncovered. The mathematical order of operations (seed-level pairing, distractor-level averaging, delay averaging) is not yet executable. | Implement `aggregate_primary(df)` in `contract_ref.py` and add a gate test verifying it on a hand-computed CSV test fixture. | `test` |
| **GM2-8** | **Medium** | Dependencies are pinned in `requirements.txt` (Roadmap v4.1 E9). | `requirements.txt` contains open-ended lower bounds `numpy>=1.26` and `pytest>=8`. A clean run on Python 3.14 installed NumPy 2.5.3 and PyTest 9.1.1, whereas committed gate logs used NumPy 2.4.4. This allows floating upstream releases to alter behavior. | Pin exact version constraints with hashes (or commit a `requirements.lock` / `poetry.lock`). | `test` |
| **GM2-9** | **Medium** | Active normative specifications point unambiguously to v3.1 and v2 files. | `stage-0a-contract-v3.1.md` lines 103 and 135 still reference `interface-spec.md` instead of `interface-spec-v2.md`. `roadmap-v4.md` line 3 still directs implementers to `stage-0a-contract-v3.md` and `interface-spec.md`. | Update lines 103 and 135 of `stage-0a-contract-v3.1.md` and line 3 of `roadmap-v4.md` to reference `interface-spec-v2.md` and `stage-0a-contract-v3.1.md`. | `prose` |
| **GM2-10**| **Low** | `test_C4_family_N_response_evaluated_at_zbar_is_not_odd` tests the empirical stationary mean $\bar{z}$. | The test asserts `assert not np.allclose(rp, -rm)`. Setting $\bar{z} = \mathbf{0}$ in `open_loop_response` yields the exact same assertion pass because Family N's quadratic clipping term $0.1 \cdot b^2$ is inherently non-odd. The test never verifies that passing $\bar{z}$ actually shifts the trajectory. | Assert that `open_loop_response` with $\bar{z} \ne 0$ produces a significantly different numerical trajectory than with $\bar{z} = 0$. | `test` |
| **GM2-11**| **Low** | The faithfulness margin $\varepsilon_{faith}$ used in T-E1b is declared in the constants registry (Contract B line 62). | Contract B line 62 references $\varepsilon_{faith}$ for post-event open-loop response checks, but $\varepsilon_{faith}$ is omitted from Section 0 (Constants Registry). | Add $\varepsilon_{faith} = 0.05$ (or desired value) to the Section 0 table. | `prose` |

---

## 4. Statement on New Categories (Not Seen in Round 1)

As required by the review instructions, we explicitly declare that **four findings are in categories not seen in Round 1**:

1. **Augmented Closed-Loop State Space Dynamics under Delay (GM2-3):**  
   In Round 1, stability discussions focused on bounding the open-loop matrix $A_b$ and adding a nominal closed-loop check. GM2-3 addresses the mathematical feedback formulation: in delayed discrete-time systems, feedback stability cannot be determined from the zero-delay matrix; it requires computing the spectral radius of the state-space augmented by the delay queue and downstream latents.
2. **Finite-Sample Rare-Event Calibration Feasibility and Bias (GM2-4):**  
   In Round 1, calibration was discussed in terms of threshold matching at $ARL_0$. GM2-4 introduces a statistical power and estimation precision analysis demonstrating that a 20,000-step calibration budget has an intrinsic $\pm 22.4\%$ relative standard error, making a $\pm 10\%$ tolerance mathematically unattainable $\approx 66\%$ of the time and causing unwarranted estimator disqualification.
3. **Experimental Role Topology vs. Claim-Gating Estimands (GM2-5):**  
   In Round 1, the 2x2 diagnostic was evaluated as a concept. GM2-5 analyzes the data-engineering schema: partitioning runs into disjoint `primary` and `diagnostic_2x2` roles breaks automated evaluators that compute the confirmatory sign gate $I$ by filtering on `role=primary`.
4. **Multi-Horizon Metric Survivorship and Post-Termination Missingness (GM2-6):**  
   In Round 1, metric discussion centered on scalar HPDT censoring. GM2-6 addresses trajectory-based fixed-offset metrics ($p_c$ at offsets 10, 50, 200) under competing early-termination events, where observations after episode termination are ill-defined.

---

## 5. Attacks That Failed

1. **"The v2 interface does not provide transition-based history to the estimator." — Failed.**  
   `interface-spec-v2.md` line 8 defines immutable `Transition = (prev_obs, applied_action, obs, reward, terminated, truncated, probe_flag, t)` and passes it to `update()`, resolving the information-set flaw.
2. **"Mutants from round 1 still survive in `run_gate.py`." — Failed.**  
   Execution of `.venv/bin/python run_gate.py` runs `mutants.py`, which rigorously executes all 8 mutants from Round 1 and kills 8/8.
3. **"Rectangular delayed Jacobians have dimension or indexing mismatches." — Failed.**  
   `test_C4_open_loop_equals_piecewise_jacobian_over_tau_h_grid_rectangular` runs across $\tau \in \{0..3\}$ and $h \in \{1..5\}$ with $3 \times 2$ matrix $B_{rect}$ and $3 \times 3$ matrix $A_3$, passing with exact equality.
4. **"The confirmation CSV has missing seeds or invalid parameter combinations." — Failed.**  
   Programmatic inspection of all 1,764 rows in `confirmation-design.csv` verified that seeds $0..9$ are present for all confirmatory pairs, seeds $0..2$ are present for descriptive baselines, and all parameter fields match normative specifications.

---

## 6. Reviewer Summary & Opinion

*(Opinion marked as opinion)*:  
Version 2 (`d23960e6da441de7`) represents substantial progress. Adopting the interaction sign gate $I$, formalizing the v2 transition interface, integrating Round 1 mutants into the automated gate runner, and adopting the co-primary endpoint put the benchmark on solid footing.

However, three critical vulnerabilities remain:
1. **Gate Blindspots on Graph Dynamics:** The test gate does not test delayed multi-hop reachability (GM2-1) or multi-hop downstream reachability through $A_d$ (GM2-2). Both surviving mutants prove that the gate can be satisfied by causally broken code.
2. **Mathematical Feedback Stability under Delay:** Bounding the zero-delay matrix $\rho(A_b + B K)$ does not guarantee stability when feedback is delayed by $\tau \ge 1$ steps (GM2-3).
3. **Finite-Sample Calibration Feasibility:** Requiring $ARL_0 = 1000 \pm 10\%$ over 20,000 steps requires estimating an event that occurs only $\sim 20$ times, leading to massive random failure and unjustified method exclusion (GM2-4).

Closing these issues will make Phase 0R truly complete and ready for code scaffolding.
