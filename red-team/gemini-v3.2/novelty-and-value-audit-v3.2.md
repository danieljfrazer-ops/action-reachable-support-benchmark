# Novelty & Scientific Value Assessment (v3.2)

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 6 September 2026  
**Target Scope:** `roadmap-v3.2-amendments.md`, `benchmark-proposal.md`, `gemini-assessment.md`.  
**Primary Focus:** Question 1 — *Is the research genuinely novel and valuable?*

---

## 1. Overview: The Strategic Transformation

In Roadmap v3.2, the research program has undergone a profound and highly constructive pivot. By taking the Gemini v3.1 red team findings seriously, the authors moved from a purely defensive stance (retreating into a 5-variable linear SCM) to an **offensive scientific strategy**:

1. **Paper 1** has been transformed from a narrow mathematical proof into **Boundary-Bench**: a standardized benchmark suite bridging classical Fault Detection & Isolation (FDI) and Interventional Causal Discovery, spanning exact SCMs (Tier T1) and standard control environments (Tier T2).
2. **Paper 2** has been completely reimagined around **"Delusions of Agency in World Models"**, directly attacking the vulnerability of inverse-dynamics world models (Iso-Dream, Sensorimotor WM, Dueling WM) under unobserved confounding.

This transition elevates the scientific promise of the overall program from a **2.5 / 5** (at risk of the "Unassailable Triviality Trap") to a **4.5 / 5** (high-impact publication potential).

---

## 2. Assessment of Paper 2: "Delusions of Agency in World Models"

### 2.1 Why Paper 2 is an Outstanding Scientific Concept
The new framing for Paper 2 (Amendment B4) is the single strongest research contribution across the entire project. It meets all criteria for a major machine learning publication (NeurIPS, ICLR, or ICML):

1. **Named Theoretical Phenomenon:**  
   It addresses **Delusions of Agency**—the failure of an autonomous agent to distinguish between states it genuinely controls and external environmental states that merely correlate with its behavior (Ortega et al., 2021).
2. **Attacking High-Profile, Named Literature:**  
   The paper directly targets leading world-model architectures:
   - *Iso-Dream (NeurIPS 2022)* and *Sensorimotor World Models (Ivashkov et al., June 2026)* rely on **inverse dynamics** ($s_t, s_{t+1} \to a_t$) to separate controllable latents from uncontrollable latents.  
     **The Vulnerability:** When an exogenous confounder $u_t$ drives both the policy $a_t$ and a distractor $x_{t+1}$, the distractor $x_{t+1}$ statistically predicts action $a_t$. An inverse-dynamics objective will inevitably categorize the distractor as *controllable*, causing the world model to suffer from delusions of agency.
   - *Dueling World Models (Li et al., August 2026)* explicitly assumes in its appendix that action-tracking distractors are out of scope.
   - *Denoised MDPs (ICML 2022)* assumes noise latents are strictly independent of actions.
3. **Constructive Algorithmic Solution:**  
   The paper does not merely point out a flaw; it introduces a solution: an **active interventional boundary discovery filter** that purges confounded latents before state representation learning, demonstrating measurable improvements in policy adaptation after unannounced boundary changes.

### 2.2 Recommendation for Paper 2
Protect this paper at all costs. It has clear conference-track potential. Daniel must ensure that the heavy engineering load of Paper 1 does not delay or derail this research.

---

## 3. Assessment of Paper 1: "Boundary-Bench" (Tiers T1 and T2)

### 3.1 The Value of an Open Benchmark Suite
Paper 1’s transition to **Boundary-Bench** (`benchmark-proposal.md`) successfully addresses the "Unassailable Triviality Trap":
- **Standardized Infrastructure:** Extending *Robust-Gymnasium (ICLR 2025)* with typed controllability ground truth, confounded distractor injection, and sequential change events gives the community a tool it currently lacks.
- **Empirical Bridge:** Linking control theory (CUSUM, GLR, auxiliary signals) with modern causal machine learning establishes an intellectually rigorous foundation.

### 3.2 The Critical Risk in the New Primary Contrast (Finding H2)
In Amendment B2, the authors re-aimed the primary confirmatory contrast:
> *"The new primary contrast is quantitative: the probe budget at which sequential interventional detection matches the best classical FDI detector (CUSUM or GLR on model residuals) on $\Delta_{pAUC}$ under confounding."*

**The Theoretical Hazard:**
Let us analyze what happens when a classical FDI detector runs on a linear or mildly nonlinear dynamical system under stationary confounding:
1. In an un-faulted system, the observational model learns the steady-state mapping. The distractor channel $x_{t+1} = A_x x_t + G u_t + \varepsilon$ correlates with $a_t$ via $u_t$, but the residual $r_x(t) = x_{t+1} - \hat{x}_{t+1}$ remains stationary zero-mean Gaussian noise.
2. When an **actuator loss** occurs:
   - The body state $b_{t+1}$ deviates sharply from the model prediction, causing the body residual $r_b(t)$ to spike.
   - The distractor state $x_{t+1}$ is completely unaffected by the actuator loss. Its residual $r_x(t)$ does **not** spike.
3. A classical CUSUM or Generalized Likelihood Ratio (GLR) detector monitoring $r_b(t)$ will detect the actuator loss with near-optimal delay and near-infinite ARL to false alarm on $x$, **with a probe budget of EXACTLY ZERO ($P=0$)!**

**The Paradox:**  
Sequential interventional testing (sequential IBD) must inject active perturbation probes into the action stream, incurring task regret and probe costs. If the system dynamics are open-loop or the model is well-specified, **classical model-based FDI at $P=0$ will outperform active interventional probing at all probe budgets!**

If the authors frame the hypothesis as *"interventional probing matches or beats classical FDI"*, the confirmation study may report that interventional probing is strictly inferior and wasteful.

### 3.3 How to Save the Primary Contrast
Interventional probing beats classical model-based residual monitoring in two specific, well-documented regimes:
1. **Under Model Misspecification:** When the observer’s forward model is misspecified or slowly drifting, residual monitoring produces high false alarm rates, whereas active interventions provide invariant, distribution-free statistical separation.
2. **Under Closed-Loop Fault Masking:** When an active controller rapidly compensates for actuator degradation (e.g., ramping up remaining motors to track a trajectory), the tracking residual remains small, masking the fault from passive observers. Active probing exposes the lost authority.

**The Fix:** The primary contrast in Paper 1 must explicitly evaluate performance **across levels of model misspecification or active feedback compensation**, rather than assuming active probes will magically beat an optimal Kalman-filter CUSUM detector on a clean linear Gaussian system.

---

## 4. Summary Scorecard (Post-v3.2)

| Dimension | v3.1 Rating | v3.2 Rating | Commentary |
|---|:---:|:---:|---|
| **Novelty (Paper 1 Benchmark)** | 3 / 5 | **4 / 5** | Strong benchmark framing; bridges FDI and Causal RL cleanly. |
| **Novelty (Paper 2 World Models)**| 2 / 5 | **5 / 5** | Outstanding. Directly attacks delusions of agency in Iso-Dream/Dueling-WM. |
| **Scientific Value (Community)** | 2.5 / 5 | **4.5 / 5** | High community interest if benchmark is pip-installable and easy to run. |
| **Theoretical Soundness** | 2 / 5 | **4 / 5** | SCM math is patched; physical coupling in MuJoCo requires scope-fencing. |
| **Execution Feasibility** | 3 / 5 | **2.5 / 5** | **Severe scope explosion.** 12 baselines across 3 tiers threatens schedule. |
