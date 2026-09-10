# Adjudication of Peer Reviews (Gemini)

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 6 September 2026  
**Target Version:** Frozen version `c197652c0d8e846b`  
**Inputs Evaluated:** `review-claude/findings.md`, `review-codex/mutant_tau_cap.py`.

---

## 1. Adjudication of Claude's Review (`review-claude/findings.md`)

| Finding ID | Peer Severity | Gemini Verdict | Reason (One Line) |
|---|:---:|:---:|---|
| **CL-1** | High | **Valid** | Confirmed by our finding GM-4: `structural_reach` completely omits $C_d$ and downstream variables $d$, and test K10 is missing. |
| **CL-2** | High | **Valid** | Confirmed by our finding GM-3: `structural_reach` has no delay parameter, asserting non-empty support at $H=1$ when delay $\tau \ge 1$ makes the true response identically zero. |
| **CL-3** | High | **Valid** | `test_M2_rejected` and `test_M5_rejected` test hardcoded arrays and do not execute generators or oracle logic, creating an illusion of mutant coverage. |
| **CL-4** | Medium | **Valid** | In coupled dynamics, actuator loss does not necessarily alter graph reachability; primary confirmation cells require a certified $S$-change instance filter. |
| **CL-5** | Medium | **Valid** | Confirmed by our finding GM-5: `roadmap-v4.md` defines R0 and R1 only for linear and saturating SCMs, leaving the predictive model for CartPole and Pendulum undefined. |
| **CL-6** | Medium | **Judgment Call** | *(Opinion)* Whether to add distractor $p_c$ as a co-primary metric or keep RMDT alone is Daniel's decision; single-actuator complete loss does create a floor effect on alarm timing. |
| **CL-7** | Medium | **Valid** | Probe set $\mathcal{A}$ has $2K$ signed unit vectors ($\pm e_k$), and nonlinear Family N is not an odd function ($\tanh(x) \ne -\tanh(-x)$ when combined with quadratic terms), so array shape $[N_b, K, |\mathcal{H}|]$ truncates half the response data. |
| **CL-8** | Medium | **Valid** | Partial loss scaling $\gamma$ can push marginal operational effects below $\varepsilon$, converting a nominal $R$-only event into an $S$-event unless dynamic re-certification is enforced. |
| **CL-9** | Medium | **Valid** | The open-loop spectral radius bound on $A_b$ does not constrain the closed-loop state matrix $A_{cl} = A_b + B W_o \dots$, which can cause saturation and shift the stationary operating point $\bar{z}$. |
| **CL-10** | Low | **Valid** | "Sign holds on both T2 environments" lacks statistical operationalization; defining it as point estimate $> 0$ with lower bound $> -\delta_0$ resolves ambiguity. |
| **CL-11** | Low | **Valid** | Sequential IBD requires injecting time-varying randomized probe trajectories, whereas `probe(action[K], steps)` holds a single constant action across all steps. |
| **CL-12** | Low | **Valid** | The current test runner relies on custom reflection and stdout capture; installing and executing standard `pytest` in Phase 0R is necessary for robust CI. |

---

## 2. Status of Codex's Review (`review-codex/`)

* At the time of this evaluation, `review-codex/findings.md` is **not yet present** in the repository.
* However, Codex committed an adversarial check script: `review-codex/mutant_tau_cap.py`.
* **Execution Verification:** When executed against the frozen gate, `mutant_tau_cap.py` passed with **15 passed, 0 failed**, proving that an adversarial mutant capping all actuator delays $\tau \ge 1$ at 1 step survives the gate completely undetected.
* This execution independently corroborates our findings **GM-1** and **GM-3**, and Claude's finding **CL-2**: multi-step delay dynamics ($\tau \ge 2$) are completely unasserted by the current test suite.
* Full adjudication of Codex's individual findings rows will be added once `review-codex/findings.md` is committed.
