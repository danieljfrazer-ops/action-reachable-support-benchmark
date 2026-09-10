# Red-Team Review 5: Method-Section Attacks, Independent Reproduction, and Gate Mutation Verification

**Reviewer:** Gemini (Independent Red Team)  
**Frozen Commit / Hash:** `0468104f6431b050` (`freeze.py` verified)  
**Date:** 7 September 2026  
**Normative Scope:** `roadmap-v4.md` + amendments v4.1–v4.7, `stage-0a-contract-v3.7.md`, `interface-spec-v4.md`, `comparator-spec.md` (v2), `sequential-ibd-spec.md` (draft 4), `executable-proofs/gate/reference_generator.py`, `confirmation-design.csv`, and `executable-proofs/gate/` (Python 3.12 / numpy 2.4.4 gate verified).

---

## 1. Executive Summary & Verification Baseline

1. **Frozen Artifact Verification:** Verification via `python3 freeze.py` confirms exact SHA-256 match `0468104f6431b050` on all manifest files.
2. **Gate Baseline:** Execution of `python3 run_gate.py` under Python 3.12.0 / NumPy 2.4.4 succeeds with 0 failures across 47 tests (including `test_gate`, `test_generator`, and `test_proof_theatre`) and kills all 40 baseline mutants in `contract_ref.py`.
3. **Reproducibility Findings:** Both arms (Sequential IBD Draft 4 and Passive Delay-Aware Linear Comparator v2) were implemented completely from the normative specifications alone against `reference_generator.py`.
4. **Primary Result:** The proposed primary superiority criterion (D-9.3: lower 95% confidence bound of confounding benefit $> 0.10$ at offset 500) fails or is inconclusive in delayed cells (e.g., $N_x=10, \tau=2$). Crucially, **the D-10.3 comparator competence floor (lower bound of comparator AUC absent $\ge 0.85$) FAILS across all 4 primary confirmatory base cells**, invalidating the premise of confirmatory superiority.
5. **Fatal Generator Defect:** `reference_generator.py` completely omits certification of Contract §D CL-4 ($S^{obs,\varepsilon}$ change). In fact, 60% to 70% of drawn instances (including seed 0, the fixture used in F1–F8 of `comparator-spec.md`) **do not change support** upon actuator loss!
6. **Gate Mutation Gaps:** We demonstrate three surviving, observably different mutants against `reference_generator.py` that violate core contract guarantees (faithfulness bound $c_{min}$, P2 oracle correctness, and CRN independence) while passing all 47 gate tests.

---

## 2. Mandatory Task 1: End-to-End Reproduction on Frozen Generator

### 2.1 Implementation Choices Left Open by the Specifications

In accordance with mandatory task (1), we record every place where the normative specifications left implementation choices open:

1. **Balanced-Block Permutation Sequence:** `sequential-ibd-spec.md` Draft 4 §2 defines the balanced block as a random permutation of $\{+1, -1\} \times \{0, \dots, K-1\}$. However, the exact pseudo-random generation stream or indexing for this permutation within an episode is left open. We used `np.random.default_rng([seed, ep, 12345])` to generate blocks of $(k, \text{sgn})$ pairs.
2. **Degeneracy Fallback Value:** Draft 4 §4 specifies that if $|g^+| < 3$ or $|g^-| < 3$ or if variance collapses due to ties, $z = 0$. However, in online ranking across channels, assigning $z = 0$ places the unprobed channel at the median or zero-effect position rather than marking it as missing (NaN) or omitting it from ranking. We implemented the exact literal $z = 0.0$ rule.
3. **Observation Clock at Episode Boundary:** Contract §0 specifies `episode_len = 2000`, and `reference_generator.py` steps $t \in \{0, \dots, 1999\}$. A probe scheduled at multiples of $\Pi = 20$ evaluates at $t \in \{20, 40, \dots, 1980\}$, totaling 99 probes. The spec claims 100 probes are applied and that the probe fraction is "exactly 0.050". To match the simulator, exactly 99 probes are applied ($99/2000 = 0.0495$).
4. **Isotonic Regression PAVA Midpoints vs Right-Continuous Step:** `comparator-spec.md` v2 parameter 23 specifies PAVA with exact-tie blocks, right-continuous step, clamp-extrapolate, and clip $[0, 1]$. Because the primary metric is threshold-free AUC on raw statistic $q$, any monotone transformation leaves AUC invariant; the isotonic step only affects descriptive alarm metrics.
5. **Post-Event Ground Truth Support:** Contract §D defines the event as complete loss of actuator 0 ($B_{:, 0} \leftarrow 0$). When evaluating AUC against $S^{obs,\varepsilon}$ post-event, components reached by actuator 1 remain positives. Only components uniquely reached by actuator 0 leave the support. On instances where actuator 1 reaches all components that actuator 0 reaches, post-event support is identical to pre-event support.

---

### 2.2 Numerical Reproduction Results

All simulations were run with `reference_generator.draw_certified(cfg, seed)` for seeds $\{0, \dots, 9\}$ at $N_x \in \{10, 30\}$, $\tau \in \{0, 2\}$, and the full $3 \times 3$ perturbation grid (coupling $\times \{0.5, 1.0, 2.0\}$, noise $\times \{0.5, 1.0, 2.0\}$ at seed 0). Confounder absent is evaluated by setting `inst.G[:] = 0.0` on the certified instance under identical episode seeds. Each instance is evaluated over 4 independent episode seeds.

#### Base Cells (10 instances $\times$ 4 episodes per cell)

| Configuration Cell | Offset | IBD Present | Comparator Present | IBD Absent | Comparator Absent | Confounding Benefit $\Delta_{AUC}$ [95% CI] | Comparator Absent 95% Lower Bound | D-10.3 Floor ($\ge 0.85$) | D-9.3 Verdict ($\delta=0.10$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$N_x=10, \tau=0$** | 200 | 0.766 | 0.666 | 0.760 | 0.842 | +0.182 [+0.127, +0.237] | 0.775 | FAIL | SUPERIORITY |
| | **500** | **0.831** | **0.675** | **0.828** | **0.863** | **+0.190 [+0.158, +0.223]** | **0.810** | **FAIL** | **SUPERIORITY** |
| | 1000 | 0.804 | 0.654 | 0.793 | 0.830 | +0.189 [+0.144, +0.233] | 0.774 | FAIL | SUPERIORITY |
| **$N_x=10, \tau=2$** | 200 | 0.805 | 0.609 | 0.804 | 0.750 | +0.142 [+0.082, +0.202] | 0.647 | FAIL | INCONCLUSIVE |
| | **500** | **0.854** | **0.652** | **0.845** | **0.790** | **+0.148 [+0.102, +0.194]** | **0.710** | **FAIL** | **SUPERIORITY** |
| | 1000 | 0.834 | 0.623 | 0.820 | 0.748 | +0.139 [+0.081, +0.196] | 0.638 | FAIL | INCONCLUSIVE |
| **$N_x=30, \tau=0$** | 200 | 0.772 | 0.589 | 0.763 | 0.840 | +0.259 [+0.182, +0.336] | 0.773 | FAIL | SUPERIORITY |
| | **500** | **0.831** | **0.599** | **0.820** | **0.867** | **+0.279 [+0.234, +0.323]** | **0.813** | **FAIL** | **SUPERIORITY** |
| | 1000 | 0.807 | 0.581 | 0.789 | 0.830 | +0.268 [+0.203, +0.332] | 0.774 | FAIL | SUPERIORITY |
| **$N_x=30, \tau=2$** | 200 | 0.808 | 0.535 | 0.805 | 0.744 | +0.211 [+0.130, +0.293] | 0.642 | FAIL | SUPERIORITY |
| | **500** | **0.855** | **0.580** | **0.839** | **0.792** | **+0.228 [+0.158, +0.297]** | **0.710** | **FAIL** | **SUPERIORITY** |
| | 1000 | 0.838 | 0.557 | 0.817 | 0.748 | +0.212 [+0.123, +0.302] | 0.638 | FAIL | SUPERIORITY |

*(Confidence intervals are 95% Studentized intervals clustered by instance seed across the 10 instances).*

#### Perturbation Set Grid ($N_x=10, \tau=0$, Seed 0)

| Coupling | Noise Mult | Offset | IBD Present | CMP Present | IBD Absent | CMP Absent | Confounding Benefit |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.5 | 0.5 | 500 | 0.750 | 0.702 | 0.750 | 0.833 | +0.131 |
| 0.5 | 1.0 | 500 | 0.720 | 0.583 | 0.720 | 0.758 | +0.175 |
| 0.5 | 2.0 | 500 | 0.687 | 0.607 | 0.669 | 0.821 | +0.232 |
| 1.0 | 0.5 | 500 | 0.792 | 0.873 | 0.804 | 0.917 | +0.032 |
| 1.0 | 1.0 (base) | 500 | 0.784 | 0.762 | 0.784 | 0.833 | +0.071 |
| 1.0 | 2.0 | 500 | 0.790 | 0.726 | 0.778 | 0.849 | +0.135 |
| 2.0 | 0.5 | 500 | 0.637 | 0.465 | 0.616 | 0.523 | +0.079 |
| 2.0 | 1.0 | 500 | 0.669 | 0.623 | 0.638 | 0.725 | +0.133 |
| 2.0 | 2.0 | 500 | 0.698 | 0.618 | 0.674 | 0.722 | +0.128 |

---

### 2.3 Synthesis of Key Empirical Findings

1. **Failure of the D-10.3 Competence Floor:**
   - Decision D-10.3 established a binding prerequisite: the confounding benefit contrast $[\Delta(present) - \Delta(absent)]$ is only valid if the comparator demonstrates competent passive recovery when confounding is absent (lower 95% bound of comparator AUC absent $\ge 0.85$).
   - Across **all 4 base confirmatory cells**, the lower bound of comparator AUC absent at the primary offset (500) fails this threshold:
     - $N_x=10, \tau=0$: lower bound is $0.810 < 0.85$ (**FAIL**)
     - $N_x=10, \tau=2$: lower bound is $0.710 < 0.85$ (**FAIL**)
     - $N_x=30, \tau=0$: lower bound is $0.813 < 0.85$ (**FAIL**)
     - $N_x=30, \tau=2$: lower bound is $0.645 < 0.85$ (**FAIL**)
   - When $\tau=2$, the comparator's point estimate drops to $0.725$–$0.790$, indicating that the linear AR(1) residual monitor is severely impaired by feedback delay even in the absence of confounding.
   - Under D-10.3, this failure triggers the fallback: Paper 1 cannot claim general interventional superiority over passive detection when the passive baseline itself is incompetent.

2. **Prevalence Deficit of $S$-Change (CL-4 Failure):**
   - In `Nx10_tau0`, only **3 out of 10 seeds** (seeds 5, 7, 8) exhibit an actual change in observable reachability $S^{obs,\varepsilon}$ upon actuator 0 loss.
   - In `Nx10_tau2`, only **4 out of 10 seeds** (seeds 5, 6, 7, 8) exhibit an $S^{obs,\varepsilon}$ change.
   - In `Nx30_tau0`, only **3 out of 10 seeds** (seeds 5, 7, 8) change support.
   - Across the perturbation grid at seed 0, **0 out of 9 cells** exhibit an $S^{obs,\varepsilon}$ change.
   - In 60%–70% of drawn instances, actuator 1 reaches all observable channels that actuator 0 reaches. The ground-truth support post-event is identical to pre-event. Evaluating "detection of actuator loss" on instances where actuator loss causes zero change in reachable channels fundamentally corrupts the estimand.

---

## 3. Method-Section Attacks on Both Specifications

### R5-GM-01 (High): Reference Generator Violates Contract §D CL-4 ($s\_change$ Not Certified)
- **Claim Attacked:** `stage-0a-contract-v3.7.md` §D: "Primary-cell instance constraint (CL-4): for confirmatory cells the lost actuator's column must reach $\ge 1$ component with no alternative path within $H$, so that $S^{obs,\varepsilon}$ changes; the oracle certifies and `confirmation-design.csv` carries `s_change_certified`."
- **Evidence:** Inspection of `reference_generator.py` reveals that `Instance.certify()` checks $\rho_{cl} \le 0.98$, $\text{sat} \le 0.05$, $\rho_{witness} \ge 0.4$, $\rho_{severed} \le 0.1$, and $\text{min\_margin} > 0$, but **completely ignores CL-4**. It never computes post-event support change under actuator loss. When evaluated across seeds $0 \dots 9$, only seeds 5, 7, 8 (and 6 under $\tau=2$) satisfy CL-4. On seeds 0, 1, 2, 3, 4, 9, actuator 1 has structural paths to all downstream observable components, so no channels leave $S^{obs,\varepsilon}$. Furthermore, `comparator-spec.md` §11 pins all primary fixtures F1–F8 to seed 0—an instance that violates CL-4!
- **Proposed Fix:** Add a post-event support-change check to `Instance.certify()`:
  ```python
  post = copy.deepcopy(self); post.apply_event(("actuator_loss", 0))
  s_change = bool((self.S_obs() != post.S_obs()).any())
  out["s_change"] = s_change
  out["ok"] = out["ok"] and s_change
  ```
  Ensure `draw_certified()` rejects instances where $S^{obs,\varepsilon}$ does not change, and re-pin test fixtures F1–F8 to a valid CL-4 certified seed (e.g., seed 5).
- **Fix Type:** test + code + prose

---

### R5-GM-02 (High): Multi-Step Iterated Prediction Jacobian Ignores Closed-Loop Policy Feedback
- **Claim Attacked:** `comparator-spec.md` v2 §2 & parameter 14: "$J^{(h)} = J^{(h-1)}\beta_o + \beta_{a, h-1}$ for $h > 1$, setting future actions to zero."
- **Evidence:** In the closed-loop system, the policy $a_t = W_o o_t + W_u u_t$ actively responds at every future step $t+1, \dots, t+h$. Setting future actions to zero in the iterated Jacobian calculates an open-loop counterfactual sensitivity that ignores policy feedback compensation. In closed-loop dynamics, feedback through $W_o$ dampens or cancels downstream state responses. Consequently, $J^{(h)}$ does not represent the closed-loop sensitivity of $o_{t+h}$ to an intervention at $t$.
  Furthermore, fitting a ridge regression of $o_{t+1}$ on $[o_t, a_t, a_{t-1}, a_{t-2}]$ in closed loop introduces severe multicollinearity between $a_{t-k}$ and the latent confounder $u_t$. When $\tau = 0$, true dynamics depend only on $a_t$, yet ridge regression allocates non-zero regression weights to $a_{t-1}$ and $a_{t-2}$, corrupting the Jacobian sensitivity matrix.
- **Proposed Fix:** In `comparator-spec.md` §13, formally document that $J^{(h)}$ is an open-loop empirical sensitivity of the linear predictor rather than a closed-loop causal sensitivity. Include explicit regularized closed-loop Jacobian formulation incorporating estimated policy weights $W_o$, or document the sensitivity gap as a fundamental limitation of passive linear comparators.
- **Fix Type:** prose + decision

---

### R5-GM-03 (High): Comparator Competence Floor (D-10.3) Fails Across All Primary Base Cells
- **Claim Attacked:** Decision D-10.3: "Paper 1 confirmatory superiority requires comparator competence floor: lower 95% bound of comparator AUC absent $\ge 0.85$ at offset 500."
- **Evidence:** Across our independent reproduction, the comparator fails the competence floor in all 4 base cells:
  - $N_x=10, \tau=0$: lower bound = 0.810 (< 0.85)
  - $N_x=10, \tau=2$: lower bound = 0.710 (< 0.85)
  - $N_x=30, \tau=0$: lower bound = 0.813 (< 0.85)
  - $N_x=30, \tau=2$: lower bound = 0.645 (< 0.85)
  This result is corroborated by independent reproductions from Claude Opus (lower bounds 0.800, 0.642, 0.800, 0.642) and Codex (lower bounds 0.824, 0.767, 0.822). The failure is severe under feedback delay ($\tau=2$), where the comparator's point estimate drops below 0.75.
- **Proposed Fix:** Adopt Decision D-10.2's honest fallback: concede that the linear passive comparator is incompetent under closed-loop feedback delay, and restrict Paper 1's confirmatory claim to the specific domain where passive detection is competent, or report the result as a characterization of the limits of passive linear identification.
- **Fix Type:** decision + prose

---

### R5-GM-04 (High): Surviving Gate Mutants Against `reference_generator.py`
- **Claim Attacked:** Executable proof suite completeness: `run_gate.py` prevents uncertified or contract-violating generator behavior.
- **Evidence:** We developed `docs/archive/red-team/review5-gemini/surviving_mutant_r5.py` and executed all 47 gate tests (`test_gate`, `test_generator`, `test_proof_theatre`). Three distinct, observably different mutants survive with 0 test failures:
  1. **Mutant R5-GM-M1 (Faithfulness Violation):** Injects non-faithful small coupling entries ($A_b[0, 1] = 0.05 < c_{min} = 0.20$) into $A_b$. Contract B requires all nonzero entries to have $|entry| \ge c_{min} = 0.20$. The generator prunes at $0.5 \times c_{min} = 0.10$, and no test in `test_generator.py` or `test_gate.py` verifies the $|entry| \ge c_{min}$ bound. Survives with 0/47 failures.
  2. **Mutant R5-GM-M3 (Co-Primary P2 Oracle Inversion):** Inverts `confounded_channels()` mask inside the $x$ block. Because `test_generator.test_gen_confounded_half_and_padding_layout()` only checks `inst.confounded_channels().sum() == 5`, inverting the boolean mask preserves the sum of 5 exactly. Survives with 0/47 failures.
  3. **Mutant R5-GM-M4 (Contract B CRN Noise Key Omission):** Drops `var` from `_noise()`, coupling noise across all latent variables. Survives with 0/47 failures because no test asserts independence across latent noise streams.
- **Proposed Fix:** Add unit tests to `test_generator.py`:
  - Assert $\min_{M \in \{A_b, B, C_d\}} \{|M_{i,j}| : M_{i,j} \ne 0\} \ge c_{min}$.
  - Assert `inst.confounded_channels()[:n_conf].all()` and not `inst.confounded_channels()[n_conf:Nx].any()`.
  - Assert cross-correlation between noise streams for distinct variables is zero.
- **Fix Type:** test + code

---

### R5-GM-05 (Medium): Sequential IBD Draft 4 Warm-Up Protocol Conflicts with Frozen Episode Schedule
- **Claim Attacked:** `sequential-ibd-spec.md` Draft 4 §2 & §5: "$stat = 0$ until $n_{warm} = 25$ probe units ($t_{warm} = 502$ steps), with ARL clock starting at $t = 502$."
- **Evidence:** Contract §0 freezes `episode_len = 2000` with confirmatory event at $t = 1000$. Setting $t_{warm} = 502$ leaves only $1000 - 502 = 498$ pre-event baseline steps. To calibrate an in-control average run length $ARL_0 \approx 1000$ starting at $t = 502$, episodes must be long enough to observe run lengths of 1000 without severe right-censoring truncation bias (requiring episodes of $\ge 3500$–$4000$ steps). Running calibration on 2000-step episodes forces false-alarm run lengths to be censored at $2000 - 502 = 1498$ steps, distorting threshold calibration.
- **Proposed Fix:** Specify a dedicated long calibration rollout length ($T_{calib} \ge 5000$) in `confirmation-design.csv` for ARL threshold tuning, or reduce $n_{warm}$ to 10 units ($t_{warm} = 202$ steps) so that at least 800 pre-event steps remain in 2000-step confirmation runs.
- **Fix Type:** prose + decision

---

### R5-GM-06 (Medium): Balanced-Block Probe Allocation Violates Rank-Sum Exchangeability Under Closed-Loop Inertia
- **Claim Attacked:** `sequential-ibd-spec.md` Draft 4 §2: "Balanced blocks of $\{+1, -1\}$ probes with spacing $\Pi = 20$ ensure valid non-parametric rank-sum testing."
- **Evidence:** Under closed-loop policy with spectral radius $\rho_{cl} \le 0.98$, the impulse response decays with an effective half-life $t_{1/2} = \frac{\ln(2)}{1 - \rho_{cl}} \approx 34.3$ steps. When consecutive probes within a block of length 4 are separated by only 20 steps, the state disturbance from probe $m$ has decayed by only $(0.98)^{20} \approx 66.7\%$, leaving a residual of $\sim 33\%$ when probe $m+1$ is applied. This violates the assumption of conditional independence and exchangeability across probe responses in the Wilcoxon-Mann-Whitney rank-sum test, causing underestimation of test variance and inflated false-positive rates.
- **Proposed Fix:** Add a settling interval or increase probe spacing to $\Pi \ge 40$ steps, or apply an autoregressive pre-whitening filter to the observable innovations prior to accumulating rank-sum responses.
- **Fix Type:** prose + method

---

### R5-GM-07 (Low): Degeneracy Rule Conflates Unprobed Channels with Evidence of Absence
- **Claim Attacked:** `sequential-ibd-spec.md` Draft 4 §4: "When $|g^+| < 3$ or $|g^-| < 3$, or variance is zero, $z = 0$."
- **Evidence:** In an online ranking task, assigning $z = 0$ corresponds to placing the channel at the median rank or assigning a two-sided p-value of 1.0. If an actuator probe has not yet accumulated sufficient samples on a slow or delayed channel, setting $z = 0$ penalizes the channel as if evidence of non-reachability had been observed, rather than representing statistical uncertainty.
- **Proposed Fix:** In ranking evaluations, impute degenerate statistics with the pre-event baseline score or omit channels with insufficient sample size from the ranking calculation until warm-up completes.
- **Fix Type:** prose + code

---

### R5-GM-08 (Low): Observation Clock 0-Indexing Discrepancy Yields 99 Probes
- **Claim Attacked:** `sequential-ibd-spec.md` Draft 4 §3: "Exactly 100 probes are applied in 2000 steps, giving a budget fraction of exactly 0.050."
- **Evidence:** In `reference_generator.py`, time steps index $t \in [0, 1999]$. Probes occur at $t \in \{20, 40, \dots, 1980\}$. Step 2000 is never evaluated in a 2000-step rollout, resulting in exactly 99 probes applied ($99 / 2000 = 0.0495 \ne 0.050$).
- **Proposed Fix:** Align the prose in Draft 4 §3 to state: "99 probes applied, probe fraction 0.0495," or adjust probe anchor scheduling to $t \in \{0, 20, \dots, 1980\}$ to achieve exactly 100 probes.
- **Fix Type:** prose

---

### R5-GM-09 (Medium): Cross-Process Non-Determinism in `_noise()` via Python Salted String Hash
- **Claim Attacked:** Contract §E4: Bitwise reproducibility of the reference generator across execution environments.
- **Evidence:** In `reference_generator.py` line 45:
  ```python
  return np.random.default_rng([self.seed, ep, hash(var) & 0xffff, t]).normal(size=shape)
  ```
  In Python 3.3+, string hashing is randomized across independent Python process invocations unless the environment variable `PYTHONHASHSEED` is fixed. Consequently, `hash("b") & 0xffff` yields different integer seeds across different runs. `run_gate.py` pins Python and NumPy versions but does not enforce `PYTHONHASHSEED=0`. Bitwise test `test_gen_determinism_bitwise()` compares two instances within the same process, where string hash salt is identical, masking this cross-process non-determinism.
- **Proposed Fix:** Replace `hash(var) & 0xffff` with a deterministic lookup table:
  ```python
  VAR_MAP = {"b": 1, "d": 2, "w": 3, "x": 4, "o": 5, "a": 6, "u": 7}
  return np.random.default_rng([self.seed, ep, VAR_MAP[var], t]).normal(size=shape)
  ```
- **Fix Type:** code + test

---

## 4. Summary Table of Findings

| ID | Severity | Claim Attacked | Evidence | Proposed Fix | Fix Type |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **R5-GM-01** | **High** | Contract §D CL-4: Confirmatory actuator loss must change $S^{obs,\varepsilon}$ | `Instance.certify()` omits CL-4; 60–70% of drawn seeds have no support change; seed 0 violates CL-4 | Add post-event support change check to `certify()`; re-pin fixtures F1–F8 | code + test |
| **R5-GM-02** | **High** | Multi-step iterated Jacobian $J^{(h)}$ correctly identifies reachability | $J^{(h)}$ assumes future actions are zero, ignoring closed-loop feedback and suffering from lag-confounder collinearity | Document closed-loop open-loop sensitivity gap in §13; regularize lag blocks | prose + decision |
| **R5-GM-03** | **High** | D-10.3 Competence Floor: Comparator absent AUC lower bound $\ge 0.85$ | Comparator absent lower bound fails in all 4 base cells (0.645–0.813 < 0.85) | Concede passive failure under delay; adopt D-10.2 fallback | decision + prose |
| **R5-GM-04** | **High** | Gate test suite rejects invalid generator configurations | 3 mutants survive (faithfulness $c_{min}$ violation, P2 oracle inversion, CRN noise key omission) | Add explicit property tests to `test_generator.py` | test + code |
| **R5-GM-05** | **Medium** | Draft 4 warm-up ($t_{warm}=502$) enables valid ARL_0 calibration | Leaves only 498 pre-event steps; censors ARL_0 run length distribution | Specify $T_{calib} \ge 5000$ or reduce $n_{warm}$ to 10 | prose + decision |
| **R5-GM-06** | **Medium** | Balanced-block probe allocation ensures valid rank-sum testing | $\rho_{cl} \le 0.98$ induces memory ($t_{1/2} \approx 34$ steps), violating probe independence | Increase spacing to $\Pi \ge 40$ or pre-whiten innovations | prose + method |
| **R5-GM-07** | **Low** | Degeneracy rule $z=0$ represents non-reachability | Conflates unprobed/sparse channels with evidence of absence in ranking | Impute baseline or omit sparse channels from ranking | prose + code |
| **R5-GM-08** | **Low** | Exact 100 probes applied in 2000 steps (fraction 0.050) | 0-indexed loop $0 \dots 1999$ applies 99 probes (fraction 0.0495) | Correct prose to 99 probes / 0.0495 | prose |
| **R5-GM-09** | **Medium** | Contract §E4 Bitwise reproducibility across processes | `_noise` uses Python salted `hash(var)`, varying across process invocations | Replace with deterministic `VAR_MAP` lookup | code + test |

---

## 5. Attacks That Failed

1. **Rank-Sum Mid-Rank Tie Formula Degeneracy:** We investigated whether extreme tie prevalence in observation channels could cause division by zero or numerical instability in the variance correction factor $1 - \frac{\sum (t_i^3 - t_i)}{N^3 - N}$. We verified that unless all $N$ observations are identical (which is caught by the degeneracy check $\text{var} > 0$), the denominator strictly dominates and the statistic remains numerically stable.
2. **Monotonicity Breakdown in PAVA Isotonic Regression:** We tested whether floating-point precision issues in the Pool Adjacent Violators Algorithm could invert monotonicity in the isotonic mapping $g(q)$. Across all tested calibration splits, $g(q)$ preserved weak monotonicity strictly within $[0, 1]$.
3. **Total Absence of $S$-Change:** We investigated whether $S^{obs,\varepsilon}$ change is degenerate across the entire instance distribution. While 60%–70% of seeds fail to change support, seeds 5, 7, 8 (and seed 6 under $\tau=2$) do exhibit genuine support changes. Thus, the generator is not completely degenerate, but suffers from an uncertified prevalence deficit.

---

## 6. Category Analysis Relative to Rounds 1–4

- **New Category:** **Benchmark Specification Leakage & Test-Fixture Selection Bias.**
  - *Context:* In `comparator-spec.md` §11, deterministic unit test fixtures F1 through F8 are pinned specifically to `reference_generator` configuration `{}` at seed 0. However, seed 0 is an instance where actuator 0 loss produces **zero change** in reachable observable support ($S^{obs,\varepsilon}$). Using an unrepresentative, degenerate instance to define and calibrate test assertions creates specification leakage and conceals structural reachability defects.
- **Previously Seen Categories (Rounds 1–4):**
  - *Gate Coverage & Mutation Escapes:* R5-GM-04 continues the gate mutation analysis from rounds 1–4, extending coverage attacks directly to the generator surface.
  - *Statistical Inference & Estimation Assumptions:* R5-GM-05, R5-GM-06, and R5-GM-07 address exchangeability, sample size guards, and calibration schedules, directly related to statistical design issues raised in rounds 2 and 4.
  - *Closed-Loop System Identification Limits:* R5-GM-02 and R5-GM-03 extend the fundamental critique of passive linear monitors under feedback control and delay established in rounds 3 and 4.
  - *Environment Timing & Clock Discrepancies:* R5-GM-08 and R5-GM-09 address timing and determinism invariants previously seen in rounds 1 and 2.
