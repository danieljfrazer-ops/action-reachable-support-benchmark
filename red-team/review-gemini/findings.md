# Review of Frozen Version c197652c0d8e846b (Gemini)

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 6 September 2026  
**Scope:** `roadmap-v4.md`, `stage-0a-contract-v3.md`, `interface-spec.md`, `confirmation-design.csv`, and `executable-proofs/gate/`.  
**Gate Execution:** `run_gate.py` executed via Python 3.13 with NumPy; baseline result: 15 passed, 0 failed.

---

## 1. Executable Verification of Contract Equation C4

As required by the review rubric, Equation C4 (open-loop impulse response $R_{t,h}(a)$ and piecewise causal Jacobian $M_{t,h}$) from `stage-0a-contract-v3.md` was verified by executing numerical forward simulations across multiple horizons $h \in \{1, 2, 3\}$ and actuator delays $\tau \in \{0, 1, 2\}$ with non-diagonal dynamics matrix $A_b = \begin{pmatrix} 0.85 & 0.15 \\ 0.05 & 0.70 \end{pmatrix}$, $B = \begin{pmatrix} 1.0 & 0.2 \\ 0.1 & 0.9 \end{pmatrix}$, and test probe $a = (0.5, -0.5)^T$.

Execution results from `contract_ref.py`:
- $\tau = 0$: $h=1$ max diff $= 0.00$; $h=2$ max diff $= 5.55 \times 10^{-17}$; $h=3$ max diff $= 5.55 \times 10^{-17}$. (Matches)
- $\tau = 1$: $h=1$ max diff $= 0.00$ ($M=0$); $h=2$ max diff $= 0.00$; $h=3$ max diff $= 5.55 \times 10^{-17}$. (Matches)
- $\tau = 2$: $h=1$ max diff $= 0.00$ ($M=0$); $h=2$ max diff $= 0.00$ ($M=0$); $h=3$ max diff $= 0.00$. (Matches)

The piecewise formulation $M_{t,h} = 0$ ($h \le \tau$) and $A_b^{h-1-\tau} B_t$ ($h > \tau$) is numerically identical to the open-loop clamped impulse response $R_{t,h}(a)$ across all tested delays.

---

## 2. Surviving Mutants (Adversarial Gate Attacks)

As required by the review rubric, adversarial mutants were injected into `contract_ref.py` and evaluated against `test_gate.py`. **Two distinct mutants survived the current gate without triggering any test failures (15 passed, 0 failed):**

### Mutant GM-1: Delayed Piecewise Jacobian Returns Corrupted Matrix for $h > \tau > 0$
```python
def mutant_jacobian_piecewise(A, B, h, tau=0):
    if h <= tau:
        return np.zeros_like(B)
    if tau > 0:
        return 999.0 * B  # BLATANTLY WRONG MUTANT FOR DELAYED ARRIVAL
    return np.linalg.matrix_power(A, h - 1 - tau) @ B
```
- **Gate Result:** **15 passed, 0 failed.** (GATE SURVIVED).
- **Why the gate failed to reject it:** `test_gate.py` tests `jacobian_piecewise` against `open_loop_response` in `test_G1` only with default $\tau=0$. In `test_G2`, it tests `jacobian_piecewise` only at $h=1, \tau=1$ ($h \le \tau$, returning 0). When $h=2, \tau=1$ ($h > \tau$), `test_G2` asserts `open_loop_response`, but **never evaluates `jacobian_piecewise`**. Consequently, the equivalence between open-loop response and the Jacobian for delayed systems after signal arrival ($h > \tau > 0$) is completely untested.

### Mutant GM-2: Structural Reachability Skips Intermediate Horizon $H=2$
```python
def mutant_structural_reach(A, B, H):
    n, k = B.shape
    reach = np.zeros(n, dtype=bool)
    frontier = (B != 0).any(axis=1)
    reach |= frontier
    if H >= 3:  # MUTANT: skips intermediate step H=2 completely
        frontier = ((A != 0).astype(int) @ frontier.astype(int)) > 0
        reach |= frontier
    return reach
```
- **Gate Result:** **15 passed, 0 failed.** (GATE SURVIVED).
- **Why the gate failed to reject it:** `test_gate.py` only asserts `structural_reach` at $H=1$ (`test_L12`) and $H=3$ (`test_K3`, `test_K4`, `test_M5`). Multi-hop causal propagation at intermediate horizons ($H=2$) is completely unasserted.

---

## 3. Findings Table

| ID | Sev | Claim Attacked | Evidence (Live Sources where External) | Proposed Fix | Fix Type |
|---|:---:|---|---|---|:---:|
| **GM-1** | High | The gate verifies equivalence of open-loop response and piecewise Jacobian for delayed dynamics ($M_{t,h}$, T-G1/G2). | Mutant GM-1 returning $999.0 \times B$ for $h > \tau > 0$ passes all 15 tests in `run_gate.py` with 0 failures. Equivalence is tested only at $\tau=0$. | Add assertion in `test_G2` comparing `open_loop_response` against `jacobian_piecewise` across a full grid of $(h, \tau) \in \{1..4\} \times \{0..2\}$ with non-diagonal $A$. | test |
| **GM-2** | High | The gate verifies multi-step causal graph reachability across horizons up to $H$ (T-C1, T-K4). | Mutant GM-2 skipping horizon $H=2$ passes all 15 tests in `run_gate.py` with 0 failures. Only $H=1$ and $H=3$ are asserted. | Add test asserting reachability on a 3-node linear chain ($0 \to 1 \to 2$) at $H=1, 2, 3$, proving node 2 is reached at $H=2$ and $H=3$, but not $H=1$. | test |
| **GM-3** | High | Structural reachability $S^{latent}_{t,H}$ (Contract C1) matches operational support $S^{latent,\varepsilon}_{t,H}$ (Contract C2). | `structural_reach(A, B, H)` in `contract_ref.py` has no $\tau$ argument. When $\tau=1$, at $H=1$ the action has not arrived, so true response is 0 ($S^{latent,\varepsilon} = \emptyset$), but `structural_reach` returns rows of $B$ ($S^{latent} \ne \emptyset$). E1b agreement fails by construction on delayed instances. | Add delay $\tau$ to `structural_reach(A, B, H, tau=0)`. For $H \le \tau$, return all False. For $H > \tau$, traverse $H - \tau$ steps. Add tests for $\tau \ge 1$. | test + prose |
| **GM-4** | High | Contract C1 structural support covers all latents $z = [b; d; w; x]$, including downstream $d$ via $C_d$ (Section A, C1, C6). | `contract_ref.structural_reach` accepts only $(A, B, H)$ and outputs an $N_b$-vector. Downstream matrix $C_d$ and variables $d, w, x$ are ignored. An oracle labeling $d$ unreachable passes the gate. Case K10 named in Contract K line 123 has no test in `test_gate.py`. | Extend `structural_reach` to accept full block adjacency $(A_b, B, C_d, A_d)$ and output an $N_z$-vector. Implement `test_K10_downstream_channel_d`. | test |
| **GM-5** | Medium | `confirmation-design.csv` fully specifies all 1,440 confirmation runs, including 480 runs for CartPole and Pendulum-v1 across R0 and R1. | `roadmap-v4.md` line 47 defines R0 and R1 only for SCM Families L and N. CartPole and Pendulum are nonlinear; a linear predictor (D9) is misspecified on both. What constitutes a "correct model" in `R0_clean` for CartPole/Pendulum is undefined in all normative docs. | Formally specify the predictive model for T2 in R0 (e.g., an MLP trained to convergence on fault-free data with whiteness check) versus R1 (linear autoregressive model). | prose |
| **GM-6** | Medium | All hand-derived cases named in Contract Section K are tests in `test_gate.py` (Contract Section K line 123). | `stage-0a-contract-v3.md` line 123 claims cases K7, K8, K9, K10 are all tests in `test_gate.py`. Grep confirms `test_K7` (partial actuator loss) and `test_K10` (downstream channel $d$) do not exist. | Implement `test_K7_partial_loss_changes_R_not_S` and `test_K10_downstream_d_in_S_not_B` in `test_gate.py`. | test |
| **GM-7** | Medium | Observational confounding floor $\rho_{min} = 0.4$ ensures distractors are actively confounded across distractor levels up to 100 (Contract 0, E2c). | Contract Section 0 line 18 defines floor as $\max_{k,j} |\text{corr}(a_k, x_j)| \ge 0.4$. At `distractor_level=100`, 99 distractor channels can have correlation 0.0 while 1 channel has 0.41, diluting the confounding challenge into unconfounded noise. | Require a quantile floor (e.g., median pairwise correlation $\ge 0.2$ or at least $k$ witnesses exceeding $\rho_{min}$). | prose + test |
| **GM-8** | Medium | Primary estimand $\Delta$ at matched $ARL_0$ eliminates disjoint-support scalar failures (Roadmap v4 D11, Contract G). | In `executable-proofs/gemini_v32_checks.py`, `delta_pauc()` returns `None` on disjoint supports. If pilot variance creates disjoint operating delay supports on any seed, multi-seed bootstrap aggregation crashes with `TypeError`. | Ensure the metric implementation returns a concrete signed float (boundary difference) rather than `None`. | test |
| **GM-9** | Low | The gate suite is runnable directly via `python3 run_gate.py` (Readiness protocol line 30). | Default shell environment (`/opt/homebrew/bin/python3`, Python 3.14) lacks NumPy. Running the bare command `python3 run_gate.py` crashes with `ModuleNotFoundError`. Works only when directed to an environment with NumPy installed. | Add an interpreter check in `run_gate.py` and document the virtual environment requirement in the root instructions. | prose |
| **GM-10**| Low | Contract C4 open-loop impulse response definition subtracts response at stationary mean $\bar{z}$. | `contract_ref.py` evaluates at zero state $\bar{z}=0$. In Family L, the affine terms cancel algebraically, but in Family N with saturating nonlinearities and quadratic clipping, evaluating at $\bar{z} \ne 0$ yields state-dependent Jacobians. | State explicitly in Contract C4 whether Family N response is evaluated at $\bar{z}=0$ or empirical stationary mean $\hat{\bar{z}}$. | prose |

---

## 4. Attacks That Failed

1. **"RMDT with censoring is mathematically invalid." — Failed.**  
   `rmdt()` in `contract_ref.py` correctly censors undetected events at the detection horizon $H_{det}$ and is verified by `test_L3`. This properly penalizes missed detections without requiring ad hoc delay penalties.
2. **"Confounding test fails on rectangular matrices ($K \ne N_x$)." — Failed.**  
   `test_G3_L12` explicitly tests rectangular actions ($K=3, N_x=2$) with max pairwise correlation, and correctly triggers `NaN` on constant zero-variance probes.
3. **"Negative matrix exponents remain in piecewise Jacobian." — Failed.**  
   `jacobian_piecewise` cleanly branches at $h \le \tau$ to return zeros, and `test_wrong_formula_rejected` confirms that evaluating negative matrix powers fails the gate.
4. **"The two-tier scope fence invalidates the benchmark." — Failed.**  
   Restricting Paper 1 to single-actuator systems (CartPole, Pendulum) eliminates the dense dynamic coupling ambiguity of multi-joint MuJoCo while providing a valid, continuous non-linear transfer check.

---

## 5. Reviewer Summary & Opinion

*(Opinion marked as opinion)*:  
Roadmap v4 and Stage 0A Contract v3 are substantially closer to a clean, executable engineering specification than any previous iteration. The primary comparator (channel-agnostic CUSUM vs Sequential IBD), the 2x2 diagnostic grid, and the discrete RMDT estimand at matched $ARL_0$ are statistically and scientifically sound.

However, the "gate" built in `executable-proofs/gate/` still contains serious coverage blind spots:
1. It does not test delayed piecewise Jacobians after signal arrival ($h > \tau > 0$).
2. It does not test multi-step reachability at intermediate horizons ($H=2$).
3. It completely omits downstream variables $d$ and actuator delay $\tau$ from `structural_reach`.

Phase 0R (Contract and test repair) must close these specific test holes before Stage 0A code is scaffolded.
