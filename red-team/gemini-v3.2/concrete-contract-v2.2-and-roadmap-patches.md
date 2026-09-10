# Contract v2.2 & Roadmap v3.2 Patches

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 6 September 2026  
**Purpose:** Concrete, drop-in text and mathematical replacements for `stage-0a-contract-v2.1.md`, `roadmap-v3.2-amendments.md`, and `benchmark-proposal.md` to resolve findings H1 through H6.

---

## Patch 1: Clean Section F Interface Contradiction (Resolves H4)

### Target: `stage-0a-contract-v2.1.md`, Section F

#### Replace Lines 98–104:
```markdown
Per step, every estimator returns:
1. p_c ∈ [0,1] for each channel c: probability that c ∈ S^obs,ε. From a declared probabilistic model, or from a calibrator fitted on a separate calibration split (section G). Passage through the calibrator is logged.
2. Typed alarms α^S_t, α^R_t, α^P_t ∈ {0,1}: a change in support, response, or observation map is declared. An estimator without a native mechanism for a target emits a declared constant (usually 0), which is scored as such.
3. Optional but scored if present: R̂_{t,h}(a) over 𝒜 × ℋ; per-channel assignment distributions.

**Paper 1 scoring [v2.1] (G6).** Paper 1 baselines are scored **exclusively** on p_c (support S^obs,ε) and α^S (support-change alarm). R and P remain ground-truth objects in the contract for generator and oracle verification and for the mutant tests, and are scored only for methods that natively estimate them, in later phases. No estimator emits dummy constants for scoring; a constant output has no operating curve and would produce a fictitious comparison.
```

#### With:
```markdown
Per step, every estimator returns:
1. $p_c \in [0,1]$ for each channel $c$: probability that $c \in S^{obs,\varepsilon}$. From a declared probabilistic model, or from a calibrator fitted on a separate calibration split (section G). Passage through the calibrator is logged.
2. Typed support change alarm $\alpha^S_t \in \{0,1\}$: a change in operational support is declared.
3. Optional (evaluated only in phases with structured estimators): typed alarms $\alpha^R_t, \alpha^P_t \in \{0,1\}$; response estimate $\hat{R}_{t,h}(a)$; per-channel assignment distributions.

**Paper 1 scoring [v2.2] (G6, H4).** Paper 1 baselines are scored **exclusively** on support estimates $p_c$ ($S^{obs,\varepsilon}$) and support change alarms $\alpha^S_t$. Estimators without native mechanisms for $R$ or $P$ do not emit dummy constants, and no comparisons are made on $R$ or $P$ in Paper 1. Targets $R$ and $P$ are retained in the environment contract solely for generator-oracle correctness and mutant tests.
```

---

## Patch 2: Discrete Pareto Upper-Convex-Hull Formulation for $\Delta_{pAUC}$ (Resolves H3)

### Target: `roadmap-v3.2-amendments.md`, Amendment B1

#### Replace Lines 5–8:
```markdown
## B1. Primary estimand (G4)

Replaces A4's matched-delay estimand. Δ is the normalised partial area between the delay-versus-log-ARL operating curves over the shared achievable delay interval [d_min, d_max], where d_min is the larger of the two estimators' minimum achievable median delays and d_max the smaller of their maxima, from the pilot threshold sweep. Δ_pAUC = (1/(d_max − d_min)) ∫ (log ARL_A(d) − log ARL_B(d)) dd. If the supports are disjoint, Δ is reported at the nearest boundary point and dominance declared. Smallest effect of interest δ = ln 2 in average log-ARL units, rationale unchanged. Decision rules in A5 apply to Δ_pAUC.
```

#### With:
```markdown
## B1. Primary estimand (G4, H3)

Replaces A4's matched-delay estimand. To account for discrete integer delays and non-unique threshold operating points, $\Delta$ is defined as the **normalized partial area between the Pareto-optimal delay-versus-log-ARL curves** across the shared discrete integer delay interval $[d_{min}, d_{max}]$.

1. For each estimator $m \in \{A, B\}$ and discrete threshold $\theta$, let $(\hat{d}_m(\theta), \widehat{ARL}_m(\theta))$ be the empirical median detection delay and mean run length to false alarm.
2. The Pareto-optimal performance at discrete integer delay $d \in \mathbb{N}$ is:
   $$\log ARL_m^*(d) = \max \left\{ \log \widehat{ARL}_m(\theta) : \hat{d}_m(\theta) \le d \right\}$$
3. The primary scalar estimand is the discrete normalized difference:
   $$\Delta_{pAUC} = \frac{1}{d_{max} - d_{min} + 1} \sum_{d=d_{min}}^{d_{max}} \left( \log ARL_A^*(d) - \log ARL_B^*(d) \right)$$
   where $d_{min} = \max(\min \hat{d}_A, \min \hat{d}_B)$ and $d_{max} = \min(\max \hat{d}_A, \max \hat{d}_B)$ are the bounds of the overlapping integer delay support.
4. If the empirical delay supports are completely disjoint, $\Delta$ is reported as the boundary difference at the nearest support edge and dominance is declared unconditionally. Smallest effect of interest $\delta = \ln 2$ in average log-ARL units. Decision rules in A5 apply to $\Delta_{pAUC}$.
```

---

## Patch 3: Re-Aim Primary Contrast across Model Misspecification (Resolves H2)

### Target: `roadmap-v3.2-amendments.md`, Amendment B2

#### Replace Lines 9–12:
```markdown
## B2. Re-aimed primary contrast (G5)

The old primary contrast (interventional beats observational under confounding) follows from the do-calculus and is not informative. The new primary contrast is **quantitative**: the probe budget at which sequential interventional detection matches the best classical FDI detector (CUSUM or GLR on model residuals) on Δ_pAUC under confounding. Secondary descriptive findings: which learned observational criteria (forward-model residual, inverse-dynamics attribution) fail under confounding, and how every method behaves through a boundary change. Reviewers get a number they did not have, not a theorem they already had.
```

#### With:
```markdown
## B2. Re-aimed primary contrast (G5, H2)

The primary contrast evaluates **the efficiency and robustness of interventional probing versus model-based residual monitoring under confounding**:
1. **The Core Question:** Under what levels of **model misspecification** (unmodeled nonlinearities or parameter drift) does active interventional boundary tracking outperform passive classical FDI (CUSUM/GLR on model residuals)?
2. **Confirmatory Hypothesis H1:** When the predictive model is well-specified, classical CUSUM achieves high ARL at zero probe cost ($P=0$). As model misspecification increases, passive residual detectors suffer a collapse in ARL due to spurious distractor residual spikes, whereas sequential interventional detection (Sequential IBD) maintains calibrated false-alarm rejection at the cost of a declared probe budget $P$.
3. **Primary Estimand:** $\Delta_{pAUC}$ between Sequential IBD and CUSUM across clean vs misspecified model regimes.
```

---

## Patch 4: Scope-Fence Tier T2 and Prune Baselines to 5 Core Algorithms (Resolves H1 and H6)

### Target: `benchmark-proposal.md`, Sections 2 & 3

#### Replace Section 2 (Lines 16–24):
```markdown
## 2. Two tiers for Paper 1 (Scope-Fenced MVP)

| Tier | Environment | Ground truth | Compute per run | Purpose |
|---|---|---|---|---|
| **T1 Exact** | Stage 0A structural-causal generator (families L and N) | Exact S, R, P from the declarative SCM | < 1 second | Unit tests, calibration scoring, mathematical phase diagrams |
| **T2 Robust Control MVP** | Gymnasium classic control (**CartPole** and **Inverted Pendulum**) wrapped with injected confounded distractors; sensor swap, dropout, and motor loss | Exact S by construction (single-actuator systems have unambiguous reachability) | seconds | Realism transfer check; proves algorithms operate on continuous non-linear Gym environments |

*(Note on Multi-Joint Systems: Articulated multi-joint robots such as Reacher and HalfCheetah involve dense inertial dynamic coupling where actuator loss does not decouple joint reachability. To preserve rigorous ground truth, coupled multi-joint robotics are deferred to Paper 2, where world models are explicitly evaluated).*
```

#### Replace Section 3 (Lines 26–34):
```markdown
## 3. Five Core Baselines for Paper 1 (Pruned from 12)

To preserve review bandwidth and ensure code verification under Rule B7, Paper 1 confirmation evaluates **five conceptually orthogonal baselines**:

1. **Random:** Uniform random support probability $p_c \sim \text{Uniform}(0, 1)$ and Poisson change alarm (Negative control).
2. **Temporal Correlation:** Sliding-window Pearson correlation with thresholding (Observational baseline; vulnerable to confounding).
3. **Forward-Model Prediction Residual:** Online neural/linear predictor tracking observation errors (Standard deep RL representation baseline).
4. **Sequential IBD:** Randomized action probes with two-sample Kolmogorov-Smirnov / FDR tests and sequential re-probing (Primary interventional baseline).
5. **Classical CUSUM / GLR:** Page’s cumulative sum test running on predictive model innovation residuals (Optimal classical control-theory baseline).

*(Deferred algorithms: Standalone Inverse Dynamics is reserved for Paper 2; Mutual Information and Bayesian variants are retained as exploratory appendices).*
```
