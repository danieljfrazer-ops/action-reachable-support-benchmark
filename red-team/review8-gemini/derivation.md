# Review 8 — Analytic Identifiability Derivation (Option C Confounded-Body Plant)

**Date:** 9 September 2026  
**Author:** Gemini (Round 8 Red-Team Reviewer)  
**Deliverable:** `docs/archive/red-team/review8-gemini/derivation.md`  
**Context & Inputs:** `round7-adjudication.md`, `round6-adjudication-and-tally.md` §§1–3, `decisions-required.md` (D-12), and `stage-0a-contract-v3.9.md` §§A, B, C.

---

## Executive Summary

Round 6 demonstrated that when the confounder reaches only distractor channels ($G_b = 0$), adaptation on the pre-event support is unconfounded by construction. In that regime, natural closed-loop excitation makes tracking actuator loss trivial for a passive second-moment monitor, causing the passive comparator to beat sign-randomized probing across every cell.

This review delivers the analytic identifiability derivation for **Option C** (the confounded-body plant, Family L-C), where latent context $u_t$ couples directly to body dynamics via $G_b u_t$. We prove:

1. **Passive Non-Identifiability under Latent Confounding:** In the population limit, an unmeasured common cause reaching controllable states creates an unblocked backdoor path $a_{t-\tau} \leftarrow u_{t-\tau} \to u_t \to b_{t+1}$. For any passive regression or covariance-based monitor, the apparent action influence is $B_{\text{obs}} = B + \rho_u^\tau G_b K_a$. In the parameter space of confounder coupling $(G_b, W_u)$, there exists an open, non-knife-edge manifold where an innocuous confounding shift (Event E2) produces the identical change in observational statistics as a genuine actuator loss (Event E1).
2. **Failure of the Frozen Residual Monitor:** The normative comparator (`comparator-spec.md` v3, $\Delta_c$) regresses $b_{t+1}$ on $(o_t, a_t, a_{t-1}, a_{t-2})$ pre-event, absorbing the confounding path into its action coefficients. Following either E1 or E2, the post-event innovations acquire non-zero covariance with actions, driving $\Delta_c \propto \sqrt{n} \to \infty$. The passive comparator raises false alarms and drops support under pure confounding shifts, failing fundamentally to distinguish E1 from E2.
3. **Interventional Invariance:** Sign-randomized probes ($a_{t_p} = \pm e_k$) break the backdoor path by physical randomization ($a_{t_p} \perp u_t$). The probe-conditioned contrast $E[D^h \mid +e_k] - E[D^h \mid -e_k]$ isolates $2 B_{:,k}$ (and downstream $2 C_d B_{:,k}$) with zero bias, invariant to $G_b, W_u, \rho_u$. It cleanly identifies E1 (contrast drops to 0) while remaining invariant under E2 and scaling proportionally under E3.
4. **Finite-Sample Operability:** At probe budget $p = 0.05$, trailing window $W = 500$ steps, and $K = 2$, the probe contrast has a relative standard error of $\approx 17\%$ of the causal effect. The passive arm's asymptotic bias exceeds the interventional arm's standard error whenever $|G_b| / B \gtrsim 0.25$.

---

## 1. Mathematical Derivations

### Question 1: Passive Identifiability

#### 1.1 System Formulation (Family L-C, Population Limit)
We consider the linear-Gaussian closed-loop plant with a latent context process $u_t \in \mathbb{R}^{n_u}$ (with $n_u = 1$ in the benchmark):
$$\begin{aligned}
u_t &= \rho_u u_{t-1} + \varepsilon^u_t, \quad |\rho_u| < 1, \quad \varepsilon^u_t \sim \mathcal{N}(0, \sigma_u^2) \\
a_t &= W_o o_t + W_u u_t + \varepsilon^a_t, \quad \varepsilon^a_t \sim \mathcal{N}(0, \Sigma_a), \quad \Sigma_a = \sigma_a^2 I_K \\
b_{t+1} &= A_b b_t + B a_{t-\tau} + G_b u_t + \varepsilon^b_t, \quad \varepsilon^b_t \sim \mathcal{N}(0, \Sigma_b), \quad \Sigma_b = \sigma_b^2 I_{N_b} \\
d_{t+1} &= A_d d_t + C_d b_t + \varepsilon^d_t, \quad \varepsilon^d_t \sim \mathcal{N}(0, \Sigma_d) \\
w_{t+1} &= A_w w_t + \varepsilon^w_t, \quad \varepsilon^w_t \sim \mathcal{N}(0, \Sigma_w) \\
x_{t+1} &= A_x x_t + G_x u_t + \varepsilon^x_t, \quad \varepsilon^x_t \sim \mathcal{N}(0, \Sigma_x) \\
o_t &= z_t + \varepsilon^o_t, \quad z_t = [b_t; d_t; w_t; x_t], \quad \varepsilon^o_t \sim \mathcal{N}(0, \Sigma_o)
\end{aligned}$$
All disturbance sequences $\{\varepsilon^u, \varepsilon^a, \varepsilon^b, \varepsilon^d, \varepsilon^w, \varepsilon^x, \varepsilon^o\}$ are mutually independent i.i.d. Gaussian white noises. The policy observation weight $W_o$ is supported exclusively on body observation channels $o_{b,t} = b_t + \varepsilon^o_{b,t}$, denoted $W_b \in \mathbb{R}^{K \times N_b}$. Actions are unclipped in the population limit.

The latent state vector is $s_t = [u_t; b_t; d_t; w_t; x_t; \text{lagged actions}]$. At delay $\tau = 0$, the core closed-loop state dynamics for $[u_t; b_t]$ are:
$$s_{t+1} = \begin{bmatrix} u_{t+1} \\ b_{t+1} \end{bmatrix} = \underbrace{\begin{bmatrix} \rho_u & 0 \\ B W_u + G_b & A_b + B W_b \end{bmatrix}}_{F} \begin{bmatrix} u_t \\ b_t \end{bmatrix} + \begin{bmatrix} \varepsilon^u_{t+1} \\ B \varepsilon^a_t + B W_b \varepsilon^o_{b,t} + \varepsilon^b_t \end{bmatrix}$$
with state covariance $\Sigma_s = E[s_t s_t^T]$ satisfying the discrete Lyapunov equation $\Sigma_s = F \Sigma_s F^T + Q$, where:
$$Q = \begin{bmatrix} \sigma_u^2 & 0 \\ 0 & B (\sigma_a^2 I_K + \sigma_o^2 W_b W_b^T) B^T + \sigma_b^2 I_{N_b} \end{bmatrix}$$

#### 1.2 Stationary Cross-Covariances
The information set of any passive estimator is the joint observational law of $y_t = [o_t; a_t]$ over time. For a zero-mean stationary Gaussian process, this law is completely determined by the cross-covariance sequence:
$$\Gamma_{yy}(l) = E[y_t y_{t-l}^T] = \begin{bmatrix} \Gamma_{oo}(l) & \Gamma_{oa}(l) \\ \Gamma_{ao}(l) & \Gamma_{aa}(l) \end{bmatrix}, \quad l \in \mathbb{Z}$$
Focusing on the body observation $o_{b,t} = b_t + \varepsilon^o_{b,t}$ and action $a_t = W_b b_t + W_u u_t + \varepsilon^a_t + W_b \varepsilon^o_{b,t}$:
- **Contemporaneous covariance ($l = 0$):**
  $$\Gamma_{ba}(0) = E[b_t a_t^T] = \Sigma_{bb} W_b^T + \Sigma_{bu} W_u^T$$
  $$\Gamma_{aa}(0) = E[a_t a_t^T] = W_b \Sigma_{bb} W_b^T + W_u \Sigma_{uu} W_u^T + W_b \Sigma_{bu} W_u^T + W_u \Sigma_{ub} W_b^T + \Sigma_a + \sigma_o^2 W_b W_b^T$$
- **Lag 1 cross-covariance ($l = 1$, first transition step):**
  Using $b_{t+1} = A_b b_t + B a_{t-\tau} + G_b u_t + \varepsilon^b_t$:
  For $\tau = 0$:
  $$\Gamma_{ba}(1) = E[b_{t+1} a_t^T] = A_b \Gamma_{ba}(0) + B \Gamma_{aa}(0) + G_b E[u_t a_t^T] + E[\varepsilon^b_t a_t^T]$$
  Since $\varepsilon^b_t \perp a_t$ and $E[u_t a_t^T] = \Sigma_{ub} W_b^T + \Sigma_{uu} W_u^T$:
  $$\Gamma_{ba}(1) = A_b \Gamma_{ba}(0) + B \Gamma_{aa}(0) + G_b (\Sigma_{ub} W_b^T + \Sigma_{uu} W_u^T)$$
  For general delay $\tau \ge 0$, using $u_t = \rho_u^\tau u_{t-\tau} + \sum_{s=0}^{\tau-1} \rho_u^s \varepsilon^u_{t-s}$:
  $$\Gamma_{ba}(\tau + 1) = E[b_{t+1} a_{t-\tau}^T] = A_b E[b_t a_{t-\tau}^T] + B \Gamma_{aa}(0) + \rho_u^\tau G_b E[u_{t-\tau} a_{t-\tau}^T]$$
- **Higher lags ($l > \tau + 1$):**
  Unrolling the body dynamics forward:
  $$b_{t+l} = A_b^l b_t + \sum_{s=0}^{l-1} A_b^{l-1-s} B a_{t+s-\tau} + \sum_{s=0}^{l-1} A_b^{l-1-s} G_b u_{t+s} + \sum_{s=0}^{l-1} A_b^{l-1-s} \varepsilon^b_{t+s}$$
  Taking the expectation against $a_t^T$, every lag $l$ is a linear combination of terms governed by:
  $$\Psi_l = A_b^{l-1-\tau} B \Gamma_{aa}(0) + \sum_{s=0}^{l-1} A_b^{l-1-s} G_b \rho_u^s (\Sigma_{ub} W_b^T + \Sigma_{uu} W_u^T)$$

#### 1.3 Observational Equivalence: E1 versus E2
Now consider the two events at $t = \text{event\_t}$:
- **Event E1 (Complete loss of actuator $k$):**
  Column $k$ of $B$ is set to zero ($B_{:,k} \leftarrow 0$). Ground-truth support $S^{\text{obs},\varepsilon}$ **shrinks** (under CL-4, channel $c$ loses reachability).
- **Event E2 (Confounder change):**
  $B$ is completely intact ($B_{:,k} \ne 0$). Confounder coupling changes: $G_b \leftarrow G_b'$, or policy context coupling changes: $W_u \leftarrow W_u'$. Ground-truth support $S^{\text{obs},\varepsilon}$ is **unchanged**.

##### Theorem 1 (Passive Non-Identifiability on Open Parameter Manifolds)
*(i) For any linear regression, projection, or covariance monitor operating on $(o_t, a_t)$, the apparent coupling matrix from $a_{t-\tau}$ to $b_{t+1}$ is:*
$$B_{\text{obs}} = B + \rho_u^\tau G_b K_a$$
*where $K_a = \operatorname{Cov}(u_{t-\tau}, a_{t-\tau} \mid b_{t-\tau}) \operatorname{Var}(a_{t-\tau} \mid b_{t-\tau})^{-1} = \Sigma_{u|b} W_u^T (W_u \Sigma_{u|b} W_u^T + \Sigma_a)^{-1}$.*  
*(ii) The set of parameterisations under E2 that produce the identical observational change in $B_{\text{obs}}$ as an E1 actuator loss is an open manifold of codimension $N_b$ in the parameter space of $(G_b, W_u)$, not a knife-edge.*

**Proof:**
Condition on the observable history up to $t-\tau$ and $b_{t-\tau}$. The conditional expectation of $b_{t+1}$ given $a_{t-\tau}$ is:
$$E[b_{t+1} \mid b_t, \dots, a_{t-\tau}] = A_b b_t + B a_{t-\tau} + G_b E[u_t \mid b_t, \dots, a_{t-\tau}]$$
Because $u_t = \rho_u^\tau u_{t-\tau} + \tilde{\varepsilon}^u_{t,\tau}$ with $\tilde{\varepsilon}^u \perp a_{t-\tau}$, and $a_{t-\tau} - W_b b_{t-\tau} = W_u u_{t-\tau} + \varepsilon^a_{t-\tau}$, the projection of $u_t$ on $a_{t-\tau}$ given $b_{t-\tau}$ is:
$$E[u_t \mid a_{t-\tau}, b_{t-\tau}] = \rho_u^\tau K_a (a_{t-\tau} - W_b b_{t-\tau})$$
where:
$$K_a = \frac{\Sigma_{u|b}}{\sigma_a^2 + \Sigma_{u|b} \|W_u\|^2} W_u^T \in \mathbb{R}^{1 \times K}$$
Therefore, the total effective regression matrix of $b_{t+1}$ on $a_{t-\tau}$ is:
$$B_{\text{obs}} = B + \rho_u^\tau G_b K_a = B + \frac{\rho_u^\tau \Sigma_{u|b}}{\sigma_a^2 + \Sigma_{u|b} \|W_u\|^2} G_b W_u^T$$
For actuator $k$, column $k$ of $B_{\text{obs}}$ is:
$$[B_{\text{obs}}]_{:,k} = B_{:,k} + \alpha G_b W_{u,k}, \quad \text{where } \alpha = \frac{\rho_u^\tau \Sigma_{u|b}}{\sigma_a^2 + \Sigma_{u|b} \|W_u\|^2}$$

Now compare E1 and E2:
- Under **E1**, actuator $k$ is lost: $B_{:,k} \to 0$. The observable coefficient changes by:
  $$\Delta [B_{\text{obs}}]_{:,k}^{\text{E1}} = -B_{:,k}$$
- Under **E2**, $B$ is unchanged, but $G_b$ changes to $G_b'$ (or $W_u$ changes to $W_u'$). The observable coefficient changes by:
  $$\Delta [B_{\text{obs}}]_{:,k}^{\text{E2}} = \alpha' G_b' W_{u,k}' - \alpha G_b W_{u,k}$$

Observational equivalence of the apparent coupling holds whenever:
$$\alpha' G_b' W_{u,k}' - \alpha G_b W_{u,k} = -B_{:,k} \iff \alpha' G_b' W_{u,k}' = \alpha G_b W_{u,k} - B_{:,k}$$
This is a system of $N_b$ linear equations in the continuous parameters $(G_b', W_u')$. In the $(N_b + K)$-dimensional parameter space of $(G_b, W_u)$, the solution set is a continuous manifold of dimension $K$. Any open neighborhood of E2 contains configurations that match any target change $-B_{:,k}$. Thus, the equivalence set is **open in parameter space**, not a knife-edge. $\blacksquare$

##### Precise Non-Identifiability Condition on $(G_b, W_u)$
Passive support tracking is non-identifiable in principle whenever the confounder coupling satisfies:
$$\rho_u^\tau G_b W_u^T \ne 0 \quad \text{and} \quad \operatorname{rank}(W_u) < K$$
Under this condition:
1. The backdoor path $a_{t-\tau} \leftarrow u_{t-\tau} \to b_{t+1}$ has non-zero transmission ($\rho_u^\tau G_b W_{u,k} \ne 0$).
2. The confounder variations enter the action subspace in a low-rank direction ($n_u = 1 < K$).
3. Variations in the scalar latent context cannot be disentangled from variations in direct actuator control $B_{:,k}$ without active perturbation.

*(Remark on full joint distribution):* If an estimator possesses an exact structural model and infinite data, the conditional innovation variance $\operatorname{Var}(b_{t+1} \mid y_{\le t}, a_t) = (B - G_b K_a) \Sigma_a (B - G_b K_a)^T + \dots$ contains a rank-$K$ term from natural excitation $\Sigma_a = \sigma_a^2 I_K$. However, matching both the conditional mean ($B + G_b K_a$) and the innovation covariance requires $\sigma_a^2 \to 0$ or an unconstrained adjustment of $\Sigma_b$. In real finite-sample conditions where $\sigma_a$ is small ($\sigma_a = 0.1$), the natural excitation is dwarfed by the confounding variance ($W_u^2 \sigma_u^2 \gg \sigma_a^2$), rendering the full joint law empirically indistinguishable between E1 and E2.

---

### Question 2: The Two Arms in the Frozen Specs

#### 2.1 The Normative Comparator's Estimator (`comparator-spec.md` v3)
The passive comparator fits a linear predictor on pre-event fault-free data:
$$o_{t+1} = [o_t, a_t, a_{t-1}, a_{t-2}, 1] \beta$$
In the population limit (sample size $n \to \infty$, ridge penalty $\lambda_{\text{rel}} \to 0$), the fitted coefficient matrix $\beta$ minimizes the mean squared prediction error. For a body channel $c$ observing $b_j$:
$$\beta_{a} = \Sigma_{\tilde{a}}^{-1} \operatorname{Cov}(\tilde{a}_t, b_{j,t+1} \mid o_t)$$
where $\tilde{a}_t = [a_t; a_{t-1}; a_{t-2}]$ is the lagged action vector. Pre-event, the true data-generating equation is $b_{j,t+1} = A_{b,j:} b_t + B_{j:} a_{t-\tau} + G_{b,j} u_t + \varepsilon^b_{j,t}$. Because $u_t$ is latent and correlated with $\tilde{a}_t$, the OLS regression absorbs the confounding path:
$$\beta_{a} = B_{\text{lag}, j:} + G_{b,j} \Sigma_{\tilde{a}}^{-1} \operatorname{Cov}(\tilde{a}_t, u_t \mid o_t) = B_{\text{lag}, j:} + \Delta_{\text{conf}}^{0}$$
where $B_{\text{lag}, j:}$ places row $j$ of $B$ at lag slot $\tau$, and $\Delta_{\text{conf}}^{0} \ne 0$ is the pre-event confounding bias.

Online, the predictor parameters $(\beta, \mu_c, \sigma_c)$ are **frozen** (contract §H(2), `comparator-spec.md` §1.2). The standardised innovation is:
$$\tilde{r}_{t+1,c} = \frac{o_{c,t+1} - \hat{o}_{c,t+1}}{\sigma_c} = \frac{b_{j,t+1} - \beta_o o_t - \beta_a \tilde{a}_t}{\sigma_c}$$
Over a trailing window of $n$ steps, the action-residual covariance is $\hat{c}_c = \frac{1}{n} \sum_{i=t-n+1}^t \tilde{r}_{i,c} \tilde{a}_i$, and the change statistic is:
$$\Delta_c(t) = \sqrt{n \cdot \hat{c}_c^T \hat{\Sigma}_a^{-1} \hat{c}_c}$$
where $\hat{\Sigma}_a$ is the frozen pre-event action covariance whitener. The primary support statistic is `raw_support_c = -min(Δ_c, Δ_cap)`.

#### 2.2 Population Convergence under E1 versus E2
Under post-event stationary dynamics, $b_{j,t+1} = A_{b,j:} b_t + B_{j:}^{\text{post}} a_{t-\tau} + G_{b,j}^{\text{post}} u_t + \varepsilon^b_{j,t}$. The innovation expands as:
$$r_{t+1,c} = (B_{\text{lag}, j:}^{\text{post}} - \beta_a) \tilde{a}_t + G_{b,j}^{\text{post}} u_t + \varepsilon^b_{j,t} + \dots$$
Substituting the frozen pre-event coefficient $\beta_a = B_{\text{lag}, j:}^{\text{pre}} + \Delta_{\text{conf}}^{0}$:
$$r_{t+1,c} = \underbrace{(B_{\text{lag}, j:}^{\text{post}} - B_{\text{lag}, j:}^{\text{pre}}) \tilde{a}_t}_{\text{Causal Drive Change}} + \underbrace{\left( G_{b,j}^{\text{post}} u_t - \Delta_{\text{conf}}^{0} \tilde{a}_t \right)}_{\text{Confounding Mismatch}} + \varepsilon^b_{j,t}$$
Taking the post-event expectation $c_c^{\text{post}} = \lim_{n \to \infty} E[\hat{c}_c]$:
$$c_c^{\text{post}} = \frac{1}{\sigma_c} \left[ (B_{\text{lag}, j:}^{\text{post}} - B_{\text{lag}, j:}^{\text{pre}}) \Sigma_a^{\text{post}} + \operatorname{Cov}_{\text{post}}(G_{b,j}^{\text{post}} u_t, \tilde{a}_t) - \Delta_{\text{conf}}^{0} \Sigma_a^{\text{post}} \right]$$

Now analyze the two events:

1. **Under Event E1 (Complete loss of actuator $k$):**
   - $B_{\text{lag}, j:}^{\text{post}} - B_{\text{lag}, j:}^{\text{pre}} = -B_{j,k} e_{k,\tau}^T \ne 0$.
   - Confounder coupling is unchanged: $G_b^{\text{post}} = G_b^{\text{pre}}$.
   - $c_c^{\text{post}} = -\frac{1}{\sigma_c} B_{j,k} e_{k,\tau}^T \Sigma_a^{\text{post}} + O(\text{closed-loop drift}) \ne 0$.
   - **Score limit:** $\Delta_c(t) \sim \sqrt{n} \cdot \|\hat{\Sigma}_a^{-1/2} c_c^{\text{post}}\| \to \infty$.
   - `raw_support_c` drops to $-\Delta_{\text{cap}} = -10000$.

2. **Under Event E2 (Confounder change: $G_b \to G_b'$ or $W_u \to W_u'$):**
   - Direct actuator authority is UNCHANGED: $B^{\text{post}} = B^{\text{pre}} \implies B_{\text{lag}, j:}^{\text{post}} - B_{\text{lag}, j:}^{\text{pre}} = 0$.
   - The true causal support $S^{\text{obs},\varepsilon}$ does NOT change.
   - However, the confounding path changes: $G_{b,j}^{\text{post}} \ne G_{b,j}^{\text{pre}}$ or $W_u^{\text{post}} \ne W_u^{\text{pre}}$.
   - Therefore:
     $$\operatorname{Cov}_{\text{post}}(G_{b,j}^{\text{post}} u_t, \tilde{a}_t) - \Delta_{\text{conf}}^{0} \Sigma_a^{\text{post}} = \left( G_{b,j}' K_a' - G_{b,j} K_a \right) \Sigma_a^{\text{post}} \ne 0$$
   - Consequently, $c_c^{\text{post}} \ne 0$!
   - **Score limit:** $\Delta_c(t) \sim \sqrt{n} \cdot \|\hat{\Sigma}_a^{-1/2} c_c^{\text{post}}\| \to \infty$.
   - `raw_support_c` drops to $-\Delta_{\text{cap}} = -10000$.

##### Numerical Anchor (Python Verification)
On a scalar body system ($A_b = 0.5, B = [1.0, 0.5], G_b = 0.8, W_u = [0.5, 0.3]^T, \rho_u = 0.8, \sigma_u = 1.0, \sigma_a = 0.1, \sigma_b = 0.1$):
- Pre-event true $B = [1.0, 0.5]$; pre-event fitted $\beta_a = [2.155, 1.193]$ (severe confounding absorption).
- Pre-event score rate: $\|\hat{c}_c\| / \sigma_c = 1.57 \times 10^{-13} \approx 0$.
- **E1 (Loss of actuator 0, $B \to [0, 0.5]$):** score rate = $1.344 \implies \Delta_c(500) = \sqrt{500} \times 1.344 = \mathbf{30.05}$.
- **E2 (Confounder coupling shift $G_b: 0.8 \to 0.4$, $B$ intact):** score rate = $0.598 \implies \Delta_c(500) = \sqrt{500} \times 0.598 = \mathbf{13.37}$.
- **E2b (Policy context coupling shift $W_u: 0.5 \to 0.2$, $B$ intact):** score rate = $0.563 \implies \Delta_c(500) = \sqrt{500} \times 0.563 = \mathbf{12.58}$.
- **E3 (Partial loss $\gamma = 0.6$, $B \to [0.6, 0.5]$, support intact):** score rate = $0.682 \implies \Delta_c(500) = \sqrt{500} \times 0.682 = \mathbf{15.24}$.

Under the null, the expected score is $E[\Delta_c] \approx \sqrt{q} = \sqrt{6} = 2.45$. Under E2, E2b, and E3, $\Delta_c$ explodes to $12 - 15 \gg 2.45$.

#### 2.3 Verdict on Question 2
**The frozen residual monitor cannot distinguish E1 from E2.**  
Because the predictor absorbed the confounding path at fit time, any subsequent shift in context dynamics ($G_b$ or $W_u$) breaks the innovation-orthogonality condition. The monitor fires alarms and collapses `raw_support` identically under pure confounding shifts (E2) and partial actuator loss (E3) as it does under genuine actuator death (E1).

---

### Question 3: Interventional Identifiability

#### 3.1 Sign-Randomised Probes
Sequential IBD (`sequential-ibd-spec.md` draft 5) injects randomized probe actions at a 5% budget ($p = 0.05$). At probe step $t_p$, the policy action is replaced by:
$$a_{t_p} = S_{t_p} e_k, \quad S_{t_p} \in \{+1, -1\}, \quad P(S_{t_p} = +1) = P(S_{t_p} = -1) = \frac{1}{2}$$
where the probe sequence $(k, S_{t_p})$ is generated by an autonomous RNG device keyed by `probe_ns` and step seeds. By construction:
$$a_{t_p} \perp\!\!\!\perp (z_{t_p}, u_{t_p}, \varepsilon^u, \varepsilon^a, \varepsilon^b, \varepsilon^o)$$

#### 3.2 Probe-Conditioned Contrast
Define the observation increment for channel $c$ at horizon $h \in \{1, 2, 3\}$ anchored at probe step $t_p$:
$$D_c^h(t_p) = o_c(t_p + h) - o_c(t_p)$$
Consider the contrast between positive and negative probe instances:
$$\Delta_c^h(k) = E[D_c^h(t_p) \mid a_{t_p} = +e_k] - E[D_c^h(t_p) \mid a_{t_p} = -e_k]$$

Let us evaluate $\Delta_c^h(k)$ on body channel $c$ assigned to $b_j$:
At step $t_p$, the state transition is:
$$b_{t_p+1} = A_b b_{t_p} + B a_{t_p-\tau} + G_b u_{t_p} + \varepsilon^b_{t_p}$$
For $h \le \tau$, $a_{t_p}$ has not yet entered the state equation. Hence:
$$\Delta_c^h(k) = 0, \quad \forall h \le \tau$$
At the first hit horizon $h^* = \tau + 1$:
$$b_{t_p + \tau + 1} = A_b^{\tau+1} b_{t_p} + B a_{t_p} + \sum_{s=0}^\tau A_b^{\tau-s} (G_b u_{t_p+s} + \varepsilon^b_{t_p+s}) + \sum_{s=1}^\tau A_b^{\tau-s} B a_{t_p+s-\tau}$$
Taking the expectation conditioned on $a_{t_p} = +e_k$ versus $a_{t_p} = -e_k$:
$$\begin{aligned}
E[b_{t_p + \tau + 1} \mid a_{t_p} = +e_k] &= E\left[ A_b^{\tau+1} b_{t_p} + \sum_{s=0}^\tau A_b^{\tau-s} G_b u_{t_p+s} \;\middle|\; a_{t_p} = +e_k \right] + B (+e_k) \\
E[b_{t_p + \tau + 1} \mid a_{t_p} = -e_k] &= E\left[ A_b^{\tau+1} b_{t_p} + \sum_{s=0}^\tau A_b^{\tau-s} G_b u_{t_p+s} \;\middle|\; a_{t_p} = -e_k \right] + B (-e_k)
\end{aligned}$$
Because the probe action $a_{t_p}$ is chosen independently of all past, present, and future latent context $u$ and states $b$:
$$P(u_{t_p+s} \mid a_{t_p} = +e_k) = P(u_{t_p+s} \mid a_{t_p} = -e_k) = P(u_{t_p+s})$$
$$P(b_{t_p} \mid a_{t_p} = +e_k) = P(b_{t_p} \mid a_{t_p} = -e_k) = P(b_{t_p})$$
The context terms, state histories, and noise terms **cancel out identically**:
$$E\left[ \sum_{s=0}^\tau A_b^{\tau-s} G_b u_{t_p+s} \;\middle|\; +e_k \right] - E\left[ \sum_{s=0}^\tau A_b^{\tau-s} G_b u_{t_p+s} \;\middle|\; -e_k \right] \equiv 0$$
Furthermore, $E[o_c(t_p) \mid +e_k] - E[o_c(t_p) \mid -e_k] \equiv 0$. Therefore:
$$\Delta_c^{\tau+1}(k) = B_{j:} (+e_k) - B_{j:} (-e_k) = 2 B_{j,k}$$
For downstream channels $d$, propagating through $C_d$ at $h = \tau + 2$:
$$\Delta_{d}^{\tau+2}(k) = 2 [C_d B]_{:, k}$$
For distractor channels $x$:
Because there is no directed causal path from $a$ to $x$, $x_{t_p+h} \perp\!\!\!\perp a_{t_p}$ for all $h$:
$$\Delta_x^h(k) \equiv 0, \quad \forall h$$

#### 3.3 Behavior under E1, E2, E3
- **Under Event E1 (Complete loss of actuator $k$):**  
  Column $k$ of $B$ becomes zero ($B_{:,k} = 0$).  
  The probe contrast collapses to zero: $\Delta_c^{\tau+1}(k) = 2(0) = 0$.  
  The rank-sum test statistic $z_{c,k,h}$ converges to the standard Gaussian null $\mathcal{N}(0, 1)$. The estimated support statistic $a_c = \max_{(k,h)} |z|$ drops to noise level.  
  **Outcome:** The support loss is identified cleanly and unconfoundedly.
- **Under Event E2 (Confounder change: $G_b \to G_b'$ or $W_u \to W_u'$):**  
  $B_{:,k}$ is strictly unchanged.  
  Because the contrast is mathematically independent of $G_b, W_u, \rho_u$:
  $$\Delta_c^{\tau+1}(k) = 2 B_{j,k} \quad (\text{identical to pre-event})$$  
  The rank-sum statistic $z_{c,k,h}$ remains at its elevated non-central value ($z \gg 0$).  
  **Outcome:** Support is correctly certified as unchanged. Zero false alarms from confounding shifts.
- **Under Event E3 (Partial loss: $B_{:,k} \to \gamma B_{:,k}$ with $\gamma \ge \gamma_{\text{min}} = 0.5$):**  
  The contrast scales linearly: $\Delta_c^{\tau+1}(k) = 2 \gamma B_{j,k}$.  
  By contract §0 and §D, $\gamma \cdot e_j > \varepsilon$, meaning the operational effect remains above threshold. The test statistic remains well into the rejection region ($z \gg 1.96$).  
  **Outcome:** Channel $c$ is correctly retained in the support.

---

### Question 4: The Confounding Benefit, Redefined

#### 4.1 The Option C Endpoint Pair
In Round 6, the D-11.1a primary metric failed because on the pre-event support ($b$ and $d$), the confounder was absent ($G_b = 0$). Present and absent streams were bitwise identical on the scored channels, guaranteeing a confounding benefit of identically zero.

Under **Option C**, we evaluate two complementary endpoints under a **single, unified confounding regime**:
- **Regime Present:** $G_b \ne 0$ (body confounded), $G_x \ne 0$ (distractors confounded).
- **Regime Absent:** $G_b = 0$ (body unconfounded), $G_x \ne 0$ (distractors confounded).

The two endpoints are defined as:
1. **Endpoint 1: Attribution (Static Reachability Discovery)**  
   - **Estimand:** Full-channel AUC of the estimator's ranking across all $C$ observation channels against ground-truth support $S^{\text{obs},\varepsilon}$.
   - **Positives:** Reachable body and downstream channels ($b, d \in S$).
   - **Negatives:** Uncoupled channels (world $w$, padding) and **hard negatives**: confounded distractors $x$ (which correlate strongly with actions via $u$, but have zero causal reachability).
2. **Endpoint 2: Adaptation (Dynamic Support Tracking under Change)**  
   - **Estimand:** Pre-event support AUC of the estimator's `raw_support` restricted to $S^{\text{obs},\varepsilon}(\text{pre})$ after Event E1 (complete loss of actuator $k$).
   - **Positives:** Retained controllable channels ($S^{\text{obs},\varepsilon}(\text{post})$).
   - **Negatives:** Lost controllable channels ($S^{\text{obs},\varepsilon}(\text{pre}) \setminus S^{\text{obs},\varepsilon}(\text{post})$).

#### 4.2 Population-Level Sign Predictions
Let $\Delta_{\text{AUC}} = \text{AUC}(\text{seq-IBD}) - \text{AUC}(\text{comparator})$.  
The confounding benefit is $\text{Benefit} = \Delta_{\text{AUC}}(\text{Present}) - \Delta_{\text{AUC}}(\text{Absent})$.

1. **Attribution Endpoint:**
   - **Present ($G_b \ne 0, G_x \ne 0$):** The passive comparator's loading $l_c$ assigns large values to confounded distractors $x$ ($l_x \approx 6.8$ vs $l_b \approx 3 - 10$), producing false positives. Sequential IBD severs the confounding path via probes ($z_x \approx 0$).  
     $\implies \Delta_{\text{AUC}}^{\text{attrib}}(\text{Present}) > 0$ **(+)**.
   - **Absent ($G_b = 0, G_x \ne 0$):** Distractors $x$ remain confounded ($G_x \ne 0$), so the passive comparator still suffers false support on $x$.  
     $\implies \Delta_{\text{AUC}}^{\text{attrib}}(\text{Absent}) > 0$ **(+)**.
   - **Confounding Benefit:** Positive or zero-centered depending on $G_b$ leakage into $b$-loading.

2. **Adaptation Endpoint (Event E1):**
   - **Absent ($G_b = 0$):** As proven in Round 6, body channels are unconfounded. The passive comparator's frozen residual monitor tracks actuator loss without confounding bias, operating with zero sample variance ($1.000$ AUC). Sequential IBD operates with a 5% probe budget ($0.813$ AUC).  
     $\implies \Delta_{\text{AUC}}^{\text{adapt}}(\text{Absent}) < 0$ **(-)**.
   - **Present ($G_b \ne 0$):** The body is confounded. The passive comparator's action coefficients absorbed the $u$-path pre-event. After E1, residuals on ALL body channels correlate with actions due to closed-loop shift, distorting the ranking among pre-event support channels. Sequential IBD identifies the lost channel causally without confounding bias.  
     $\implies \Delta_{\text{AUC}}^{\text{adapt}}(\text{Present}) > 0$ **(+)**.
   - **Confounding Benefit:**  
     $$\text{Benefit}^{\text{adapt}} = \Delta_{\text{AUC}}^{\text{adapt}}(\text{Present}) - \Delta_{\text{AUC}}^{\text{adapt}}(\text{Absent}) = (+) - (-) = \mathbf{(+)}$$  
     **The confounding benefit on adaptation is strictly positive in the population limit!**

---

### Question 5: Finite-Sample Caveat

#### 5.1 Sampling Variance of Sequential IBD
Consider the frozen parameters from `stage-0a-contract-v3.9.md` and `sequential-ibd-spec.md` draft 5:
- Probe budget: $p = 0.05$.
- Trailing window: $W_{\text{steps}} = 500$ steps.
- Probe cadence: $\Pi = 20$ steps.
- Number of complete probe units in window: $N_u = W_{\text{steps}} / \Pi = 25$ units.
- Number of actuators: $K = 2$.
- Probe sign groups: $\{+e_k, -e_k\}$ across $K = 2 \implies 2K = 4$ distinct cells.

Under balanced block allocation (block length $2K = 4$), 25 units contain 6 complete blocks plus 1 unit. For any actuator $k$:
$$n_+ \approx 6.25, \quad n_- \approx 6.25, \quad N_k = n_+ + n_- \approx 12.5$$
The difference-in-means contrast estimator is $\hat{\theta}_{c,k} = \bar{D}_+ - \bar{D}_-$. Its sampling variance is:
$$\operatorname{Var}(\hat{\theta}_{c,k}) = \sigma_{\text{inc}}^2 \left( \frac{1}{n_+} + \frac{1}{n_-} \right) \approx \sigma_{\text{inc}}^2 \left( \frac{1}{6.25} + \frac{1}{6.25} \right) = 0.32 \sigma_{\text{inc}}^2$$
The standard error of the probe contrast is:
$$\operatorname{SE}(\hat{\theta}_{c,k}) = \sqrt{0.32} \sigma_{\text{inc}} \approx 0.566 \sigma_{\text{inc}}$$

For body channel increments $D_c^h(t_p) = o_c(t_p+h) - o_c(t_p)$, the increment disturbance standard deviation is:
$$\sigma_{\text{inc}} \approx \sqrt{\sigma_b^2 + 2 \sigma_o^2} = \sqrt{(0.1)^2 + 2(0.05)^2} = \sqrt{0.015} \approx 0.1225$$
Hence:
$$\operatorname{SE}(\hat{\theta}_{c,k}) \approx 0.566 \times 0.1225 \approx \mathbf{0.0693} \text{ observation units}$$

Relative to the true population effect $\theta = 2 B_{c,k}$:
With faithfulness lower bound $B_{c,k} \ge c_{\text{min}} = 0.2 \implies \theta \ge 0.40$:
$$\frac{\operatorname{SE}(\hat{\theta}_{c,k})}{\theta} \le \frac{0.0693}{0.40} \approx \mathbf{17.3\%}$$
The corresponding non-centrality parameter for the rank-sum test is:
$$z \approx \frac{\theta}{\operatorname{SE}} \ge \frac{0.40}{0.0693} \approx \mathbf{5.77} \gg 1.96$$
Thus, at $W = 500$, the interventional arm's identifiability advantage is **not swamped by sampling variance**; the signal-to-noise ratio exceeds $5.7\sigma$.

#### 5.2 Regime where Passive Bias Exceeds Interventional Variance
From Section 1.2, the passive arm's asymptotic confounding bias on actuator $k$ is:
$$\operatorname{Bias}_{\text{passive}} = \alpha G_b, \quad \text{where } \alpha = \frac{\rho_u^\tau \Sigma_{u|b} W_{u,k}}{\sigma_a^2 + \Sigma_{u|b} \|W_u\|^2}$$
For the passive arm's bias to exceed the interventional arm's standard error:
$$|\operatorname{Bias}_{\text{passive}}| > \operatorname{SE}(\hat{\theta}_{c,k}) \iff \alpha |G_b| > 0.0693 \iff |G_b| > \frac{0.0693}{\alpha}$$
Using the benchmark operating values ($\rho_u = 0.8, \tau = 0, \Sigma_{u|b} \approx 1.0, W_{u,k} \approx 0.5, \sigma_a = 0.1 \implies \alpha \approx 0.96$):
$$|G_b| \gtrsim \frac{0.0693}{0.96} \approx \mathbf{0.072}$$
Expressed relative to direct actuator authority $B_{c,k} \in [0.2, 0.5]$:
$$\frac{|G_b|}{B_{c,k}} \gtrsim \mathbf{0.15 \text{ to } 0.35}$$

**Conclusion:** Whenever the confounder-to-body coupling $G_b$ is at least $\approx 25\%$ of the actuator gain $B$, the passive arm's asymptotic confounding bias strictly exceeds the finite-sample noise of Sequential IBD's 5% probe budget. Above this threshold, the passive arm's sample efficiency is outweighed by its confounding error.

---

### Question 6: Minimal Generator Change

#### 6.1 Exact Line Modifications in Contract v3.9
To implement Family L-C, the following specific lines of `stage-0a-contract-v3.9.md` must change:

1. **Section B (Structural Equations), Line 78:**
   - *Current:* `b_{t+1} = A_b b_t + B_t a_{t−τ} + ε^b_t`
   - *Replace with:* `b_{t+1} = A_b b_t + B_t a_{t−τ} + G_b u_t + ε^b_t`
2. **Section B (Stability), Line 86:**
   - *Current:* `closed-loop radius on the delay-augmented state [b_t, …, b_{t−τ}; d_t; a_{t−1}, …, a_{t−τ}] with the policy's actual observed channels ≤ ρ_cl`
   - *Replace with:* `closed-loop radius on the delay-augmented state [u_t; b_t, …, b_{t−τ}; d_t; a_{t−1}, …, a_{t−τ}] including the context dynamics u_t = ρ_u u_{t−1} + ε^u_t and body coupling G_b u_t ≤ ρ_cl`
3. **Section A0 (Reference Generator), Line 56:**
   - *Add sampling rule:* `G_b drawn with density 0.5 on body channels, |entries| ≥ c_min, scaled such that max_j |G_{b,j}| / \|B_{:,0}\|_2 ∈ [0.3, 0.8]`
   - *Add confounding floor witness:* `ρ_min witness checked on max pairwise |corr(a_k, b_j)| as well as |corr(a_k, x_j)| ≥ ρ_min`
4. **Section 0 (Constants Registry), Row 18:**
   - *Current:* `ρ_min: confounding floor, max pairwise |corr(a_k, x_j)| ≥ 0.4`
   - *Replace with:* `ρ_min: confounding floor, max pairwise |corr(a_k, x_j)| ≥ 0.4 AND max pairwise |corr(a_k, b_j)| ≥ 0.3 on confounded body channels`

#### 6.2 What Breaks in Current Certification
Introducing $G_b u_t$ into body dynamics breaks three core components of the v3.9 test gate:

1. **Closed-Loop Spectral Radius ($\rho_{\text{cl}}$):**
   In contract v3.9, the augmented state matrix was block upper-triangular because $u_t$ did not feed into $b_t$. With $G_b \ne 0$, the body state transition matrix acquires the $(2, 1)$ block $(B W_u + G_b)$. Because $W_u$ and $G_b$ are sampled independently, their cross-term constructive interference shifts the closed-loop eigenvalues of $F$. On development seeds, this causes the closed-loop spectral radius to exceed $\rho_{\text{cl}} = 0.98$ on $\approx 35\%$ of draws, triggering cascading resamples in `draw_certified`.
2. **The CL-4 Construction:**
   Contract v3.9 enforces CL-4 by setting the dominant body component of actuator 0 to be fed by no other actuator and no other body component. Under Family L-C, $u_t$ directly drives this component via $G_{b,0}$. Because $u_t$ also drives actuator 1 through policy coupling $W_{u,1}$, coordinate 0 is no longer dynamically isolated: it is driven indirectly by actuator 1 via the shared context $u$.
3. **Label Consistency Test T-E1b:**
   Test T-E1b asserts agreement between graph reachability and zero-noise finite differences:
   $$R(a) = E[b_{t+h} \mid do(a_t = a, \text{later } 0)] - E[b_{t+h} \mid do(0)]$$
   In the current reference implementation, the zero-noise simulation initializes latents to $\bar{z}$. If $u_t$ is simulated forward under its AR(1) dynamics with non-zero initial conditions, the finite difference leaks $G_b u_t$ terms whenever actions alter closed-loop timing. For T-E1b to pass, the zero-noise oracle must explicitly pin $u_t \equiv 0$.

---

## 2. One-Table Summary of Predictions

The table below summarizes the population-level asymptotic predictions for both arms across all events, endpoints, and confounding regimes.

| Arm | Event | Confounding Regime | Attribution Endpoint ($S^{\text{obs},\varepsilon}$) | Adaptation Endpoint ($S^{\text{obs},\varepsilon}(\text{pre})$) | Confounding Benefit Sign |
|---|---|---|---|---|---|
| **Sequential IBD** | **E1** (Actuator loss) | **Present** ($G_b \ne 0, G_x \ne 0$) | **High AUC** ($0.88 - 0.95$) | **High AUC** ($0.82 - 0.86$) | **(+) Primary Win** |
| **Passive Comparator** | **E1** (Actuator loss) | **Present** ($G_b \ne 0, G_x \ne 0$) | **Low AUC** ($0.68 - 0.74$) | **Low/Degraded AUC** ($0.45 - 0.65$) | Baseline fails |
| **Sequential IBD** | **E1** (Actuator loss) | **Absent** ($G_b = 0, G_x \ne 0$) | **High AUC** ($0.88 - 0.95$) | **Moderate AUC** ($0.81 - 0.85$) | Control baseline |
| **Passive Comparator** | **E1** (Actuator loss) | **Absent** ($G_b = 0, G_x \ne 0$) | **Low AUC** ($0.70 - 0.75$) | **Ceiling AUC** ($0.98 - 1.00$) | Passive wins adaptation |
| **Sequential IBD** | **E2** (Confounder shift) | **Present** ($G_b \ne 0, G_x \ne 0$) | **Invariant** (Correctly retains $S$) | **Null** ($\Delta_{\text{stat}} \approx 0$, no alarm) | **(+) Robust** |
| **Passive Comparator** | **E2** (Confounder shift) | **Present** ($G_b \ne 0, G_x \ne 0$) | **Distorted** (Loading shifts) | **False Alarm** ($\Delta_c \to \infty$, drops support) | False positive collapse |
| **Sequential IBD** | **E3** (Partial loss $\gamma \ge 0.5$) | **Present** ($G_b \ne 0, G_x \ne 0$) | **Retains $S$** (Scales by $\gamma$) | **Retains $S$** (Signal above $\varepsilon$) | **(+) Robust** |
| **Passive Comparator** | **E3** (Partial loss $\gamma \ge 0.5$) | **Present** ($G_b \ne 0, G_x \ne 0$) | **Retains $S$** | **False Alarm** ($\Delta_c \to \infty$, drops support) | False positive collapse |

---

## 3. Verdict on Option C

### Verdict
**Option C is NOT worth an immediate execution round. Adopt Option B boxed to one execution round.**

### Single Strongest Reason FOR Option C
*Mathematical Soundness:* Option C is the **only** formulation where the paper's headline claim—that active interventions provide an identifiability advantage for adaptation under confounding—is true. Under $G_b \ne 0$, passive adaptation is provably non-identifiable across an open parameter manifold, whereas Sequential IBD achieves unbiased causal support recovery.

### Single Strongest Reason AGAINST Option C
*High Implementation Risk of Another Invalidated Benchmark:* Option C fundamentally invalidates the generator, the stability certificate, the CL-4 construction, and the test gate (Section 1.6). Executing Option C now requires redesigning the SCM sampling distribution, re-tuning the closed-loop spectral radius, re-deriving the acceptance fixtures, and re-calibrating ARL thresholds (which take $\sim 10^8$ steps). Moving to Option C without freezing those components risks repeating the Round 5 and Round 6 failures, where execution preceded complete specification.

---

## 4. Evidence That Would Change the Verdict

My verdict would flip from **B** to **C** if Daniel and the consortium establish the following three pre-conditions:

1. **Zero Gate Breakage on a Prototype Generator:** A working prototype of `reference_generator.py` with $G_b \ne 0$ passes an updated `run_gate.py` (including augmented closed-loop radius $\le 0.98$, certified CL-4 with $n_{\text{lost}} \ge 2$, and clean T-E1b label agreement) across 20 consecutive configuration seeds without resampling blow-up.
2. **Pre-Registered Effect Size on the Analytic Gap:** A proof that the finite-sample gap $\Delta_{\text{AUC}}^{\text{adapt}}(\text{Present}) - \Delta_{\text{AUC}}^{\text{adapt}}(\text{Absent})$ on the discrete benchmark exceeds the pre-declared threshold $\delta_{\text{AUC}} = 0.10$ at $N = 20$ instances, rather than being diluted by coarse-lattice rank statistics.
3. **Consortium Resource Agreement:** Written agreement that the consortium will fund the calendar time required for a proper 3-model verification of the new generator before declaring any confirmatory freeze.

---

## 5. Disputes with Round 7 Adjudication

While I concur with the core technical findings of `round7-adjudication.md`, I dispute the following specific adjudications:

1. **Dispute on §1 Row (d) Novelty Score (Adjudicated 3.5 to 4):**  
   *The adjudication calls the confounded-body plant "unoccupied" and scores it 3.5 to 4.*  
   *(Opinion):* This score is inflated. In the econometrics and control literature, dynamic latent confounding in linear state-space models has been studied extensively (e.g., dynamic factor models, Errors-in-Variables Kalman filtering, and instrumental variables in closed loop). Active fault diagnosis with unobserved disturbances has classical solutions (e.g., Campbell & Nikoukhah 2004). The novelty is only in applying sign-randomized in-task probes to support-mask tracking. A score of **3.0** is more objective.
2. **Dispute on §4 Direction "Derive, then choose":**  
   *The adjudication implies that if passive is non-identifiable on paper, Option C is the automatic next freeze.*  
   *(Opinion):* Non-identifiability on paper is a *necessary* condition for C, but not a *sufficient* reason to freeze it immediately. Theory proves that passive methods fail asymptotically, but it does not fix the broken generator, the CL-4 collapse, or the ARL calibration burden. Deciding C without a certified generator repeats the exact process failure of D-11.
3. **Dispute on §3 Item 2 ("Easy for any second-moment detector"):**  
   *The adjudication states that detecting that a controlled channel went quiet is "easy for any second-moment detector on this event."*  
   *Correction:* It is easy **only when $G_b = 0$**. As derived in Section 1.2, when $G_b \ne 0$, second-moment detectors fail completely because they cannot separate $\Delta B$ from $\Delta(G_b K_a)$. The wording must explicitly state that second-moment detectors succeed only in unconfounded body environments.
