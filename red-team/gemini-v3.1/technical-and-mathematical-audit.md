# Technical & Mathematical Audit

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 6 September 2026  
**Scope:** Stage 0A Contract v2 (`stage-0a-contract-v2.md`), Roadmap v3.1 Amendments (`roadmap-v3.1-amendments.md`).  
**Primary Focus:** Question 2 — *Is the roadmap/plan coherent, plausible, error-free, and ready to execute?*

---

## 1. Executive Summary

A meticulous forensic audit of the mathematical equations, causal graphs, statistical invariants, and metric definitions reveals **four high-severity blocking errors** and **two structural inconsistencies**. 

If implementation begins from `stage-0a-contract-v2.md` and `roadmap-v3.1-amendments.md` as currently written, the test suite will throw $\text{NaN}$ runtime errors, matrix inversion crashes, and fatal interpolation failures during the pilot phase.

---

## 2. Detailed Findings

### G1. Closed-Loop Policy Feedback Contaminates Action-Effect Response $R_{t,h}$ and Breaks Table D
* **Severity:** **High (Blocker)**
* **Target:** `stage-0a-contract-v2.md`, Section B, Section C4, and Table D.
* **The Error:**
  In Section B (lines 25–30), the default policy is defined as a closed-loop linear state feedback:
  $$a_t = \pi(o_t, u_t) + \varepsilon^a_t = W_o o_t + W_u u_t + \varepsilon^a_t$$
  where $o_t = \text{avail}_t \odot (\text{gain}_t \odot (\text{Assign}_t z_t)) + \varepsilon^o_t$.
  
  In Section C4 (lines 46–47), the action-effect response is defined as:
  $$R_{t,h}(a) = \mathbb{E}[b_{t+h} \mid do(a_t = a), z_t = \bar{z}] - \mathbb{E}[b_{t+h} \mid do(a_t = 0), z_t = \bar{z}]$$
  The contract states: *"For family L this reduces to the Jacobian $M_{t,h} = A_b^{h-1-\tau} B_t$."*
  
  **This is mathematically false for any closed-loop system when $h \ge 2$.**
  
  Let us trace the dynamics at horizon $h=2$ (assuming $\tau=0$ for simplicity):
  - At step $t$, action $a_t = a$ is forced. State transitions to:
    $$b_{t+1} = A_b \bar{b} + B_t a + \varepsilon^b_t$$
  - At step $t+1$, an observation $o_{t+1}$ is emitted, which contains $b_{t+1}$ via channel assignment $\text{Assign}_{t+1}$.
  - Under the default policy, the agent takes action $a_{t+1} = \pi(o_{t+1}, u_{t+1}) = W_o o_{t+1} + W_u u_{t+1} + \varepsilon^a_{t+1}$.
  - The next body state is:
    $$b_{t+2} = A_b b_{t+1} + B_{t+1} a_{t+1} + \varepsilon^b_{t+1} = \left(A_b + B_{t+1} W_o \text{diag}(\text{gain} \odot \text{avail}) \text{Assign}_b\right) b_{t+1} + \dots$$
  
  Notice that the effective closed-loop transition matrix is:
  $$A_{cl} = A_b + B_{t+1} W_o \text{diag}(\text{gain} \odot \text{avail}) \text{Assign}_b$$
  
  **The Contradiction:**
  1. If the policy operates closed-loop between $t+1$ and $t+h$, then $\frac{\partial \mathbb{E}[b_{t+h}]}{\partial a_t} = A_{cl}^{h-1} B_t \ne A_b^{h-1} B_t$.
  2. Crucially, $A_{cl}$ depends directly on $\text{Assign}_t$, $\text{gain}_t$, and $\text{avail}_t$ (the observation map $P$).
  3. Therefore, under closed-loop execution, **a sensor swap or sensor gain change alters $R_{t,h}$!**
  4. This directly violates Table D (line 56), which explicitly claims that under a sensor swap, *"R is unchanged."*
* **The Fix:**
  The contract must state explicitly whether $R_{t,h}$ is an **open-loop** or **closed-loop** response. To preserve Table D and ensure that $R$ isolates the body dynamics from the observation mapping $P$, $R_{t,h}$ must be defined as an **open-loop impulse response under action clamping**:
  $$do(a_t = a, \; a_{t+1} = 0, \; \dots, \; a_{t+h-1} = 0)$$
  Section C4 must be updated to state this intervention sequence explicitly.

---

### G2. Negative Matrix Exponents and Acausal Delay in $M_{t,h}$
* **Severity:** **High (Blocker)**
* **Target:** `stage-0a-contract-v2.md`, Section C4 (line 46).
* **The Error:**
  Section C4 defines the linear Jacobian as:
  $$M_{t,h} = A_b^{h-1-\tau} B_t$$
  where $\tau \ge 0$ is the actuator delay declared in Section B (line 36).
  
  Consider an actuator with a 1-step transmission delay ($\tau = 1$). Evaluated at horizon $h = 1$:
  $$h - 1 - \tau = 1 - 1 - 1 = -1 \implies M_{t,1} = A_b^{-1} B_t$$
  
  This produces two fatal errors:
  1. **Acausal Physics:** If there is a delay of $\tau = 1$ step, an action taken at time $t$ has not yet arrived at the body at time $t+1$. The true causal response at $h=1$ is strictly zero ($0$). Computing $A_b^{-1} B_t$ asserts an acausal, retroactive effect before the signal arrives!
  2. **Code Crash (`LinAlgError`):** If $A_b$ is rank-deficient, singular, or non-invertible (e.g., contains nilpotent lag blocks or zero eigenvalues), `np.linalg.matrix_power(A_b, -1)` will raise a fatal `LinAlgError: Singular matrix`.
* **The Fix:**
  $M_{t,h}$ must be defined piecewise:
  $$M_{t,h} = \begin{cases} 0 & \text{if } h \le \tau \\ A_b^{h - 1 - \tau} B_t & \text{if } h > \tau \end{cases}$$

---

### G3. Division by Zero and $\text{NaN}$ in Invariant Test E2
* **Severity:** **High (Blocker)**
* **Target:** `stage-0a-contract-v2.md`, Section E2 (line 78).
* **The Error:**
  Section E2 specifies:
  > *"Confounding present: observational correlation between $a_t$ and $x_t$ exceeds a floor $\rho_{min}$ across seeds ... and vanishes under $do(a)$."*
  
  Look at the intervention semantics declared in Section B (line 25) and Section D (line 52):
  - Section B: *"a_t := a\* under do(a_t = a\*)"*
  - Section D: *"Estimator probes: set $a_t = a^*$ for a declared number of steps"*
  
  When an estimator applies an intervention probe, $a_t$ is clamped to a fixed constant vector $a^*$ (e.g., a unit probe $+e_k$).
  
  Now compute the Pearson correlation between a constant probe sequence $a^*$ and the distractor sequence $x$:
  $$\text{Var}(a^*) = 0 \implies \text{corr}(a^*, x) = \frac{\text{Cov}(a^*, x)}{\sqrt{\text{Var}(a^*)} \sqrt{\text{Var}(x)}} = \frac{0}{0} = \mathbf{NaN}$$
  
  When `pytest` executes invariant test E2, `np.corrcoef(a_stream, x_stream)` will raise:
  `RuntimeWarning: invalid value encountered in divide` and return `NaN`. Any assertion `assert abs(corr) < tol` will fail immediately.
* **The Fix:**
  The contract must distinguish between a single probe and an interventional distribution:
  1. For testing that confounding vanishes, the test must use a **randomized interventional stream**: $do(a_t \sim \mathcal{N}(0, \Sigma_a))$ or $do(a_t \sim \text{Uniform}(\mathcal{A}))$, ensuring $\text{Var}(a) > 0$.
  2. Alternatively, test **mean invariance**: verify that $\mathbb{E}[x_{t+1} \mid do(a_t = a_1)] = \mathbb{E}[x_{t+1} \mid do(a_t = a_2)]$, which directly reflects Pearl's condition without computing correlation.

---

### G4. Operating-Curve Extrapolation in Primary Estimand Definition
* **Severity:** **High (Blocker)**
* **Target:** `roadmap-v3.1-amendments.md`, Amendment A4 (line 32).
* **The Error:**
  Amendment A4 defines the primary scalar estimand as:
  $$\Delta = \log ARL_{int} - \log ARL_{obs} \quad \text{at matched median detection delay}$$
  where:
  > *"the matching delay is fixed in advance as the smaller estimator's median delay at its declared default threshold on the pilot, and both operating curves are interpolated to that delay."*
  
  In sequential quickest change detection, detection delay ($D$) and average run length to false alarm ($ARL$) are governed by the detection threshold:
  - Low threshold: Fast detection (low delay), but frequent false alarms (low $ARL$).
  - High threshold: Slow detection (high delay), but rare false alarms (high $ARL$).
  
  Suppose on the pilot, the interventional estimator (IBD) achieves a median detection delay of $D^* = 8$ steps at its default threshold.  
  Now suppose the observational forward-model residual detector, under heavy confounding, cannot achieve a median delay of 8 steps without triggering an alarm on literally every single step (i.e., its minimum achievable median delay across its entire valid threshold sweep is $D_{obs}^{min} = 15$ steps).
  
  To evaluate $\log ARL_{obs}$ at $D^* = 8$, the pipeline must **extrapolate outside the empirical operating curve**. Linear or spline extrapolation below an empirical curve minimum is mathematically undefined and yields negative run lengths, producing complex numbers or $\text{NaN}$ when taking $\log ARL$!
* **The Fix:**
  Replace single-point delay matching with an integrated performance metric:
  **Use the partial Area Under the Delay-vs-Log(ARL) Curve (pAUC):**
  $$\Delta_{pAUC} = \int_{d_{min}}^{d_{max}} \left(\log ARL_{int}(d) - \log ARL_{obs}(d)\right) dd$$
  where $[d_{min}, d_{max}]$ is the shared interval of achievable median delays across both estimators. If the interval is disjoint, report maximum separation at the boundary.

---

### G5. Faithfulness and Accidental Path Cancellation in Invariants E1 & E2
* **Severity:** **Medium**
* **Target:** `stage-0a-contract-v2.md`, Section E1 and E2.
* **The Error:**
  Section E1 requires that two independent label derivations agree:
  1. Directed graph reachability on the declarative SCM.
  2. Finite-difference interventions with common random numbers at zero noise.
  
  In dynamical systems with feedback or coupling (e.g., $A_b$ with off-diagonal elements), multiple directed paths connect an action to a body component. If randomly sampled transition matrices happen to have canceling coefficients (e.g., path 1 has weight $+0.4$, path 2 has weight $-0.4$), the net finite difference is zero, even though a directed path exists in the graph.
  
  Graph reachability will label the component as controllable ($1$), while finite differences will label it as uncontrollable ($0$), causing test E1 to fail intermittently on certain random seeds.
* **The Fix:**
  Add an explicit condition on matrix generation:
  Ensure all sampled edge weights in $A_b$ and $B$ are strictly positive or bounded away from zero by a minimum spectral margin ($|\lambda_{ij}| \ge c > 0$), preventing pathological cancellation (enforcing causal faithfulness).

---

### G6. Baseline API Mismatch (Codex Finding F3 Was Bypassed, Not Solved)
* **Severity:** **Medium**
* **Target:** `stage-0a-contract-v2.md`, Section F & H; `roadmap-v3.1-amendments.md`, A2.
* **The Error:**
  In Codex final critique, finding F3 noted that the baseline algorithms cannot estimate $M$ or $P$. In response, the authors added a clause in Contract v2 Section F:
  > *"An estimator without a native mechanism for a target emits a declared constant (usually 0), which is scored as such."*
  
  Consider the consequence:
  - Sequential IBD emits constant 0 for $\alpha^R$ and $\alpha^P$.
  - Forward-model residual emits constant 0 for $\alpha^P$.
  - Temporal correlation emits constant 0 for $\alpha^R$ and $\alpha^P$.
  
  When an estimator emits a constant 0, its True Positive Rate is 0, its False Alarm Rate is 0, and its detection delay is censored at infinity. **You cannot construct an operating curve, calculate ARL, or compute an estimand for any target where a method emits a constant 0.**
  
  This reveals that the "three-target paper" is a fiction. Paper 1 cannot evaluate or compare baselines on $R$ and $P$; it is exclusively an evaluation of $S^{obs,\varepsilon}$ (support change).
* **The Fix:**
  Formally drop targets $R$ and $P$ from the Paper 1 baseline comparison table entirely. Explicitly state in the contract that Paper 1 baselines are evaluated exclusively on $S^{obs,\varepsilon}$ and typed change alarms $\alpha^S$, and that $R$ and $P$ are deferred to Phase 2/3 when structured architecture variants are introduced.

---

## 3. Summary of Required Contract Patches

| Finding | Impacted File | Specific Section | Nature of Fix |
|---|---|---|---|
| **G1** | `stage-0a-contract-v2.md` | Section C4 & B | Clamp actions to zero ($a_{t+1\dots t+h-1} = 0$) during $R_{t,h}$ evaluation to prevent closed-loop policy leakage. |
| **G2** | `stage-0a-contract-v2.md` | Section C4 | Piecewise definition of $M_{t,h}$ ($0$ for $h \le \tau$) to prevent negative matrix powers. |
| **G3** | `stage-0a-contract-v2.md` | Section E2 | Replace constant probe correlation with randomized intervention correlation or mean-invariance test. |
| **G4** | `roadmap-v3.1-amendments.md` | Amendment A4 | Replace single-point pilot delay matching with partial AUC (pAUC) across shared delay intervals. |
| **G5** | `stage-0a-contract-v2.md` | Section B & E1 | Enforce strictly sign-consistent / non-canceling weight generation for causal faithfulness. |
| **G6** | `stage-0a-contract-v2.md` | Section F & H | Officially restrict Paper 1 baseline scoring to $S^{obs,\varepsilon}$ and $\alpha^S$, removing cosmetic 0-emitting targets. |

*(For full drop-in text and code replacements, see [Contract v2.1 Patches](file:///Users/danielfrazer/Documents/Personal/Persistent%20Adaptive%20AI/docs/archive/red-team/gemini-v3.1/concrete-contract-v2.1-patches.md).)*
