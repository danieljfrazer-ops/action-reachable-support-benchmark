# Technical, Causal & Physical Audit (v3.2)

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 6 September 2026  
**Target Scope:** `benchmark-proposal.md`, `stage-0a-contract-v2.1.md`, `roadmap-v3.2-amendments.md`.  
**Primary Focus:** Question 2 — *Is the roadmap/plan coherent, plausible, error-free, and ready to execute?*

---

## 1. Executive Summary

While [`stage-0a-contract-v2.1.md`](file:///Users/danielfrazer/Documents/Personal/Persistent%20Adaptive%20AI/docs/archive/red-team/stage-0a-contract-v2.1.md) successfully eliminated the four mathematical bugs in the synthetic SCM tier (G1–G4), the introduction of **Tier T2 (Gymnasium and MuJoCo continuous control)** in `benchmark-proposal.md` introduces serious physical and algorithmic failure modes that must be resolved before proceeding past Stage 0A.

---

## 2. Detailed Technical & Physical Findings

### H1. Physical Dynamic Coupling Breaks "Exact $S$ by Wrapper Construction" in Tier T2 (MuJoCo)
* **Severity:** **High (Blocker for Tier T2)**
* **Target:** `benchmark-proposal.md`, Section 2 (line 20).
* **The Claim Under Attack:**
  > *"Exact $S$ and $P$ by construction of the wrapper; $R$ by finite-difference probing of the simulator."*
* **The Physical Proof of Failure:**
  In classical rigid-body dynamics (governing MuJoCo environments like HalfCheetah or Reacher), the equations of motion are given by the coupled manipulator equation:
  $$M(q) \ddot{q} + C(q, \dot{q})\dot{q} + g(q) = B \tau + J(q)^T f_{ext}$$
  where:
  - $q \in \mathbb{R}^n$ are joint angles,
  - $M(q) \in \mathbb{R}^{n \times n}$ is the symmetric, positive-definite **mass inertia matrix**,
  - $\tau \in \mathbb{R}^m$ are actuator torques,
  - $B \in \mathbb{R}^{n \times m}$ is the actuator mapping matrix.
  
  Solving for joint accelerations:
  $$\ddot{q} = M(q)^{-1} \left( B \tau - C(q, \dot{q})\dot{q} - g(q) + J(q)^T f_{ext} \right)$$
  
  Crucially, **the mass matrix inverse $M(q)^{-1}$ is dense**: its off-diagonal terms are non-zero due to cross-joint inertial coupling (e.g., accelerating the thigh mechanically exerts reaction torques on the shin and torso).
  
  Now, suppose an unannounced **actuator-loss event** occurs on HalfCheetah, zeroing out the back-thigh motor (column $k$ of $B \leftarrow 0$).
  
  **Does the observation channel corresponding to the back thigh angle $q_k$ exit the controllable support $S^{obs,\varepsilon}$?**
  
  Recall the formal definition of operational support from Contract v2.1 Section C2:
  $$S^{latent,\varepsilon}_{t,H} = \left\{ j : \max_{h \le H} \|\mathbb{E}[z_{j,t+h} \mid do(a_t = a)] - \mathbb{E}[z_{j,t+h} \mid do(a_t = 0)]\| > \varepsilon \right\}$$
  
  Because $M(q)^{-1}$ has non-zero off-diagonal entries, **firing the remaining 5 actuators will physically move the back-thigh joint $q_k$!**  
  If that displacement exceeds $\varepsilon$ over horizon $H$, then:
  $$q_k \in S^{latent,\varepsilon}_{t,H} \quad \text{both BEFORE and AFTER the actuator loss!}$$
  
  Therefore, for coupled multi-joint robots (HalfCheetah, Reacher, Ant), **an actuator loss does NOT necessarily change $S^{obs}$!** It alters the control authority and the response mapping $R$, but the joint remains causally reachable.
  
  The assertion that ground-truth support $S$ is known *"by construction of the wrapper"* is **physically false** for coupled multi-joint robots. The wrapper cannot know whether $q_k \in S^{obs,\varepsilon}$ without performing numerical reachability integration or evaluating the state-dependent controllability Gramian.

* **The Scope-Fencing Fix:**
  1. **For Paper 1:** Restrict Tier T2 strictly to **un-coupled or single-actuator systems** where reachability is unambiguous:
     - *CartPole* ($K=1$): losing the cart motor drops control authority from 1 to 0; all states become uncontrolled.
     - *Inverted Pendulum* ($K=1$): losing the motor reduces controllability to empty set.
     - *Acrobot* ($K=1$): actuated only at the elbow.
  2. **For Coupled MuJoCo (HalfCheetah/Reacher):** Defer multi-actuator articulated systems to **Paper 2**, where full world models are evaluated, and classify actuator loss as an $R$-change rather than an $S$-change.

---

### H2. Classical FDI (CUSUM/GLR) Threatens to Trivialise the Primary Contrast
* **Severity:** **High (Theoretical Risk)**
* **Target:** `roadmap-v3.2-amendments.md`, Amendment B2.
* **The Issue:**
  Amendment B2 establishes the new primary contrast:
  > *"the probe budget at which sequential interventional detection matches the best classical FDI detector (CUSUM or GLR on model residuals) on $\Delta_{pAUC}$ under confounding."*
  
  In classical control theory, an optimal Fault Detection & Isolation (FDI) observer monitors the output innovation/residual $r_t = y_t - \hat{y}_t$.
  
  In the SCM:
  - The observational predictor for the distractor learns $\hat{x}_{t+1} = \hat{A}_x x_t + \hat{W} a_t$. Under stationary confounding, the residual $r_x(t) = x_{t+1} - \hat{x}_{t+1}$ is stationary Gaussian white noise.
  - When an actuator loss occurs, the body residual $r_b(t)$ experiences a persistent deterministic step change.
  - The distractor residual $r_x(t)$ experiences **zero shift**.
  
  A classical Generalized Likelihood Ratio (GLR) or Page’s CUSUM test running on $r_b(t)$ will detect the change in minimum time with zero distractor false alarms, **using a probe budget of EXACTLY ZERO ($P=0$).**
  
  Sequential interventional testing (sequential IBD) must actively inject perturbation probes, paying a cost in action deviation and task regret. In a clean linear Gaussian setting, **sequential IBD will be strictly outperformed by classical CUSUM at zero probe budget.**
* **The Fix:**
  Do not pit interventional probing against classical FDI in clean, well-specified linear environments where classical FDI is mathematically optimal.  
  Frame the contrast across **levels of model misspecification** and **closed-loop feedback compensation**. Interventional probing is justified only when:
  (a) The observer's model is misspecified (causing classical FDI to false-alarm on distractors); or
  (b) An active feedback controller compensates for the fault, masking the residual shift from passive observers.

---

### H3. Discrete Integer Delays vs Continuous Integration in $\Delta_{pAUC}$
* **Severity:** **Medium (Metric Math)**
* **Target:** `roadmap-v3.2-amendments.md`, Amendment B1.
* **The Error:**
  Amendment B1 defines:
  $$\Delta_{pAUC} = \frac{1}{d_{max} - d_{min}} \int_{d_{min}}^{d_{max}} \left(\log ARL_A(d) - \log ARL_B(d)\right) dd$$
  
  In sequential change detection, detection delay $d$ is an **integer number of discrete time steps** ($d \in \{1, 2, 3, \dots, H\}$).
  
  Furthermore, when sweeping detection thresholds $\theta$:
  - The mapping from continuous threshold $\theta$ to empirical median delay $\hat{d}(\theta)$ is a **step function**.
  - Multiple distinct threshold values $\theta_1 < \theta_2 < \theta_3$ often yield the exact same integer median delay (e.g., $\hat{d} = 4$).
  - For a given delay $d$, there are multiple empirical values of $ARL$.
  
  Therefore, $ARL(d)$ is **not a single-valued continuous function**. An implementation attempting standard numerical integration (e.g., `scipy.integrate.quad`) will fail.
* **The Fix:**
  Formulate $\Delta_{pAUC}$ formally using the **Pareto upper convex hull**:
  1. For each estimator, define $ARL^*(d) = \max \{ ARL(\theta) : \text{median delay under } \theta \le d \}$.
  2. Compute $\Delta_{pAUC}$ as a discrete Riemann sum over integer delays $d \in \{d_{min}, d_{min}+1, \dots, d_{max}\}$:
     $$\Delta_{pAUC} = \frac{1}{d_{max} - d_{min} + 1} \sum_{d=d_{min}}^{d_{max}} \left(\log ARL_A^*(d) - \log ARL_B^*(d)\right)$$

---

### H4. Textual Contradiction in `stage-0a-contract-v2.1.md` (Lines 100 vs 103)
* **Severity:** **Medium (Contract Hygiene)**
* **Target:** `stage-0a-contract-v2.1.md`, Section F.
* **The Conflict:**
  - **Line 100 (retained from v2):**  
    > *"An estimator without a native mechanism for a target emits a declared constant (usually 0), which is scored as such."*
  - **Line 103 (added in v2.1):**  
    > *"No estimator emits dummy constants for scoring; a constant output has no operating curve and would produce a fictitious comparison."*
* **The Fix:**
  Delete line 100 completely. Ensure Section F states unambiguously that Paper 1 baselines are evaluated exclusively on $S^{obs,\varepsilon}$ and $\alpha^S$.

---

### H5. Policy Stability Fragility under Confounded Perturbation in Tier T2
* **Severity:** **Medium (Physical / RL)**
* **Target:** `benchmark-proposal.md`, Section 2 (Tier T2).
* **The Issue:**
  In Tier T2, the default continuous-control policy is perturbed by the hidden cause:
  $$a_t = \text{clip}\left(\pi(s_t) + W_u u_t, \; a_{min}, \; a_{max}\right)$$
  In environments like CartPole or Pendulum, continuous RL policies operate near unstable equilibria. If $W_u u_t$ is sized large enough to create a strong distractor correlation ($|\rho| \ge 0.4$), the injected noise risks driving the pole into terminal failure within 10–20 steps.
  
  If the episode terminates early, sequential change detection is truncated, censoring the detection delay and inflating variance.
* **The Fix:**
  Specify in Tier T2 that the default policy $\pi(s_t)$ must be trained under domain randomization / additive action noise to ensure policy robustness, and set an explicit stability bound on $\|W_u\|$.
