# Contract v2.1 & Roadmap Patches

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 6 September 2026  
**Purpose:** Concrete, drop-in textual and mathematical replacements for `stage-0a-contract-v2.md` and `roadmap-v3.1-amendments.md` to resolve blocking findings G1 through G6.

---

## Patch 1: Fix Action-Effect Response and Jacobian (Resolves G1 and G2)

### Target: `stage-0a-contract-v2.md`, Section C4

#### Replace Lines 46–47:
```markdown
**C4. Action-effect response.** R_{t,h}(a) = E[b_{t+h} | do(a_t = a), z_t = z̄] − E[b_{t+h} | do(a_t = 0), z_t = z̄], for a ∈ 𝒜 (a frozen probe set of 2K unit vectors ± e_k scaled by a declared magnitude), h ∈ ℋ (declared horizon set), evaluated at z̄ = the stationary mean under the default policy. For family L this reduces to the Jacobian M_{t,h} = A_b^{h-1-τ} B_t. Mapping error is a normalised distance ‖R̂ − R‖ / ‖R‖ over 𝒜 × ℋ.
```

#### With the following corrected formulation:
```markdown
**C4. Action-effect response.** R_{t,h}(a) is defined strictly as the **open-loop impulse response** under an intervention that clamps subsequent actions to zero, preventing closed-loop feedback contamination from the default policy:
$$R_{t,h}(a) = \mathbb{E}[b_{t+h} \mid do(a_t = a, \; a_{t+1} = 0, \; \dots, \; a_{t+h-1} = 0), \; z_t = \bar{z}] - \mathbb{E}[b_{t+h} \mid do(a_t = 0, \; \dots, \; a_{t+h-1} = 0), \; z_t = \bar{z}]$$
for $a \in \mathcal{A}$ (frozen probe set of $2K$ scaled unit vectors $\pm e_k$), $h \in \mathcal{H}$ (declared horizon set), evaluated at stationary state $\bar{z}$. Clamping future actions ensures that $R_{t,h}$ reflects internal body dynamics alone, remaining invariant under sensor permutations and observation map changes (preserving Table D).

For Family L, this reduces to the piecewise causal Jacobian:
$$M_{t,h} = \begin{cases} 0_{N_b \times K} & \text{if } h \le \tau \\ A_b^{h - 1 - \tau} B_t & \text{if } h > \tau \end{cases}$$
where $\tau \ge 0$ is the actuator delay. Note: $M_{t,h}$ is strictly zero for $h \le \tau$ due to causality; matrix powers with negative exponents are invalid and must not be computed. Mapping error is the normalized distance $\| \hat{R} - R \| / \| R \|$ evaluated over $\mathcal{A} \times \mathcal{H}$.
```

---

## Patch 2: Fix Statistical Invariance and Confounding Tests (Resolves G3)

### Target: `stage-0a-contract-v2.md`, Section E2

#### Replace Lines 75–79:
```markdown
**E2. Statistical tests (tolerance and power declared).**
- Invariance: for each non-reachable component j, the paired difference between do(a) and do(0) trajectories over 𝒜 × ℋ is within tolerance δ_inv with a test of declared power at n paired seeds.
- Sensitivity: for each reachable component in S^latent,ε, the paired difference exceeds ε with declared power.
- Confounding present: observational correlation between a_t and x_t exceeds a floor ρ_min across seeds (so the distractor is a real confound, not a near-zero one), and vanishes under do(a).
```

#### With the following corrected formulation:
```markdown
**E2. Statistical tests (tolerance and power declared).**
- **Invariance:** for each non-reachable component $j \notin S^{latent}_{t,H}$, the paired difference between $do(a_t = a)$ and $do(a_t = 0)$ trajectories over $\mathcal{A} \times \mathcal{H}$ satisfies $\max_{h \le H} |\mathbb{E}[z_{j,t+h} \mid do(a)] - \mathbb{E}[z_{j,t+h} \mid do(0)]| \le \delta_{inv}$ at declared power across $n$ paired seeds.
- **Sensitivity:** for each reachable component $j \in S^{latent,\varepsilon}_{t,H}$, the paired difference exceeds $\varepsilon$ with declared power.
- **Confounding present (Observational):** under the default policy, the Pearson correlation across observation steps between action $a_t$ and distractor $x_{t+1}$ satisfies $|\text{corr}(a_t, x_{t+1})| \ge \rho_{min} > 0$ across seeds (confirming the confounder $u_t$ is active).
- **Confounding severed (Interventional):** under a **randomized interventional policy** $do(a_t \sim \text{Uniform}(\mathcal{A}))$ where $\text{Var}(a_t) > 0$, the correlation $|\text{corr}(a_t, x_{t+1})| \le \delta_{inv}$ vanishes within tolerance. (Note: constant probes $do(a_t = a^*)$ have zero variance and produce $\text{NaN}$ in correlation calculations; invariance under constant probes is verified by the mean difference test $\max_a \|\mathbb{E}[x_{t+1} \mid do(a_t=a)] - \mathbb{E}[x_{t+1} \mid do(a_t=0)]\| \le \delta_{inv}$).
```

---

## Patch 3: Fix Causal Faithfulness in Matrix Sampling (Resolves G5)

### Target: `stage-0a-contract-v2.md`, Section B

#### Add to the end of Section B (after line 36):
```markdown
**Causal Faithfulness & Non-Cancellation Constraint:**
When generating random matrices for Family L and Family N:
1. Every non-zero entry in $A_b$ and $B_t$ must satisfy $|A_{b,ij}| \ge c_{min} > 0$ and $|B_{t,ik}| \ge c_{min} > 0$ with $c_{min} = 0.2$.
2. Matrix entries must be strictly sign-consistent or conditioned such that for any reachable node $j$ with multiple directed paths from action $k$, the total causal derivative $\left|\frac{\partial \mathbb{E}[b_{j,t+h}]}{\partial a_k}\right| \ge \varepsilon_{faith} > 0$ at zero noise. Pathological accidental parameter cancellations that cause graph reachability to disagree with finite differences fail matrix generation and trigger resampling.
```

---

## Patch 4: Fix Primary Scalar Estimand to Avoid Extrapolation (Resolves G4)

### Target: `roadmap-v3.1-amendments.md`, Amendment A4

#### Replace Lines 32–34:
```markdown
- **Primary scalar estimand:** Δ = log ARL_int − log ARL_obs at matched median detection delay, where the matching delay is fixed in advance as the smaller estimator's median delay at its declared default threshold on the pilot, and both operating curves are interpolated to that delay.
- **Smallest effect of interest:** δ = ln 2. Rationale: a doubling of the run length to false alarm at equal delay is the smallest improvement that would change a practitioner's choice of estimator; smaller differences are dominated by tuning. Marked provisional until the pilot variance is known; the value may be lowered only before confirmation and only with a written reason.
```

#### With the following corrected formulation:
```markdown
- **Primary scalar estimand:** To eliminate fatal extrapolation outside empirical delay supports, $\Delta$ is defined as the **normalized partial Area Under the Delay-vs-Log(ARL) Curve (pAUC)** across the shared achievable delay interval:
  $$\Delta_{pAUC} = \frac{1}{d_{max} - d_{min}} \int_{d_{min}}^{d_{max}} \left(\log ARL_{int}(d) - \log ARL_{obs}(d)\right) dd$$
  where $[d_{min}, d_{max}]$ is the overlapping range of median detection delays achieved by both estimators on the pilot threshold sweep:
  $$d_{min} = \max\left(\min(D_{int}), \min(D_{obs})\right), \quad d_{max} = \min\left(\max(D_{int}), \max(D_{obs})\right)$$
  If the empirical delay supports are completely disjoint (i.e., the interventional detector dominates across all operating points such that $D_{int}^{max} < D_{obs}^{min}$ at matched false-alarm rates), $\Delta$ is reported as the boundary log ARL ratio at the nearest valid boundary point, and dominance is declared unconditionally.
- **Smallest effect of interest (SOEI):** $\delta = \ln 2 \approx 0.693$ in average log-ARL units. Rationale: an average doubling of the mean run length to false alarm across the shared operating delay regime is the minimum meaningful gain required to justify interventional probing overhead.
```

---

## Patch 5: Clarify Baseline Target Scope (Resolves G6)

### Target: `roadmap-v3.1-amendments.md`, Amendment A2 & A4

#### Add to Amendment A2:
```markdown
**Scope of Baseline Comparison:**
Paper 1 baselines (Sequential IBD, Temporal Correlation, Forward-Model Residual) are evaluated and scored **exclusively on observation support $S^{obs,\varepsilon}$ and support change alarms $\alpha^S$**. Because standard baselines possess no native architecture for estimating observation mapping $P$ or parametric response $R$, they are not required to emit dummy zero outputs for $R$ and $P$. The targets $R$ and $P$ are retained in the environment contract for generator-oracle verification and are evaluated as exploratory targets in Phase 2 and 3 when structured architectural baselines are introduced.
```

---

## Patch 6: Demote Phase S to an Internal Engineering Milestone (Resolves G7)

### Target: `roadmap-v3.1-amendments.md`, Amendment A7

#### Replace Line 61–63:
```markdown
- Gate to publish: all confirmation cells complete, matched-budget accounting audited by the non-building agent, and a final prior-art pass documented. If not met by day 21, the output is an internal shakedown report and the memory question returns in Paper 3.
- Contribution type when published: small empirical methods contribution, conditional on the documented prior-art pass.
```

#### With:
```markdown
- **Output and Framing:** Phase S is classified strictly as an **Internal Engineering Milestone** (harness, ledger, and thermal validation). No public arXiv technical note will be written. The phase duration is boxed to **1 calendar week** (build and run only). Results are summarized in an internal technical markdown report (`docs/archive/shakedown-report.md`) to establish baseline reference tables for Paper 3, completely preserving Daniel's writing and review bandwidth for Paper 1.
```
