# Execution Capacity & Scope-Fencing Audit (v3.2)

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 6 September 2026  
**Target Scope:** `benchmark-proposal.md`, `roadmap-v3.2-amendments.md`, `timing-and-shakedown-value.md`.  
**Primary Focus:** Question 2 — *Is the roadmap/plan coherent, plausible, error-free, and ready to execute?*

---

## 1. Executive Summary: The Scope Trap

The team has reacted to the charge of "toy SCM triviality" by swinging to the opposite extreme: **An uncontrolled explosion of engineering scope.**

In Roadmap v3.2 and `benchmark-proposal.md`, Paper 1 has expanded into an immense software and empirical undertaking:
- **7 Environments:** 2 SCM dynamics families (L and N) in Tier T1, plus 3 Classic Control (CartPole, Pendulum, Acrobot) and 2 MuJoCo environments (Reacher, HalfCheetah) in Tier T2.
- **12 Baseline Algorithms:** Spanning observational, interventional, Bayesian, and classical control-theory methods.
- **Packaging:** Full pip-installable library (`boundary-bench`), Robust-Gymnasium compatibility wrappers, leaderboard generator, and CLI demo scripts.

All of this is scheduled to be built, tested under the new mandatory "executable-proof" rule (B7), confirmed across 1,500+ runs, and written up for arXiv by **late January 2027** by a **solo unaffiliated researcher working part-time on a fanless MacBook Air**.

This schedule is an operational impossibility unless strict **scope-fencing** is enforced immediately.

---

## 2. Quantitative Review Bandwidth Breakdown: The Real Critical Path

Roadmap v3.1 Amendment A1 explicitly established Daniel's human review capacity:
> *"Daniel reviews at most one phase gate and one draft per week."*

Now consider the review requirements imposed by Roadmap v3.2 and Rule B7 (*"Every section containing an equation or baseline is accompanied by an executable script and mutant tests; Daniel signs off on script outputs"*):

| Work Item | Components | Executable Reviews Required |
|---|---|:---:|
| **Stage 0A SCM Contract** | Families L & N, Invariants E1–E5 | 2 reviews |
| **Phase S (Demoted)** | Internal shakedown script | 1 review |
| **Tier T1 Baselines (12 algorithms)** | Random, Corr, FM, MI, InvDyn, 3x Bayes, Seq-IBD, CUSUM, GLR, AuxFDI | 12 reviews |
| **Tier T2 Gymnasium Wrappers** | CartPole, Pendulum, Acrobot, Reacher, HalfCheetah distractor wrappers | 5 reviews |
| **Tier T2 Simulator Probing** | Ground-truth reachability and response scripts | 3 reviews |
| **Sequential Metrics & Ledger** | $\Delta_{pAUC}$, persistence, censoring, Pareto curves | 2 reviews |
| **Pilot Sweeps & Calibration** | Shared delay interval $[d_{min}, d_{max}]$ freeze | 2 reviews |
| **Confirmation Summaries** | Part 1 (240 runs) + Part 2 (720 runs) audit | 2 reviews |
| **Paper Draft & Figures** | Benchmark paper writing and revisions | 4 reviews |
| **TOTAL REVIEWS REQUIRED** | | **33 phase reviews** |

There are **20 calendar weeks** between 8 September 2026 and late January 2027.  
Attempting to complete 33 rigorous gate and code reviews at a rate of 1 review per week will take **33 weeks**, pushing the Paper 1 milestone to **May 2027** and delaying Paper 2 into late 2027!

---

## 3. The "Two-Tier MVP" Scope Fence for Paper 1

To preserve the late January 2027 arXiv target without sacrificing the scientific upgrade of Boundary-Bench, Daniel must apply the **"Two-Tier MVP" Scope Fence**:

```
[Boundary-Bench Scope Fence]

    ┌─────────────────────────────────────────────────────────────┐
    │  TIER T1 (EXACT SCM)                                        │
    │  - Families L & N (linear and tanh)                         │
    │  - Complete ground-truth S, R, P                            │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  TIER T2 (ROBUST CONTROL MVP)                               │
    │  - CartPole & Inverted Pendulum ONLY                        │
    │  - Single-actuator systems (no multi-joint coupling errors)  │
    │  - Injected distractor wrapper compatible with Gym          │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
    [DEFERRED TO PAPER 2]          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  TIER T2b (COUPLED MUJOCO) & TIER T3 (WORLD MODELS)         │
    │  - Reacher, HalfCheetah, Ant                                │
    │  - Delusions of Agency in Iso-Dream / Sensorimotor WM       │
    └─────────────────────────────────────────────────────────────┘
```

### 3.1 Baseline Suite Pruning (12 down to 5)
Do not implement 12 algorithms for Paper 1. Focus on **five primary, conceptually orthogonal algorithms**:

1. **Random** (Negative baseline control).
2. **Temporal Correlation** (Observational correlational baseline; vulnerable to confounding).
3. **Forward-Model Prediction Residual** (Standard deep RL representation baseline).
4. **Sequential IBD** (Primary interventional baseline; robust to confounding).
5. **Classical CUSUM/GLR on Model Residuals** (Control theory benchmark; optimal zero-probe upper bound in linear settings).

*What is cut from Paper 1's confirmatory core:*
- Cut Mutual Information (redundant with Temporal Correlation).
- Cut Standalone Inverse Dynamics (retained exclusively for Paper 2).
- Cut the 3 Bayesian variants from confirmation (retain 1 Bayesian model-informed reference in Stage 0B as an oracle benchmark).
- Cut Auxiliary-Signal Active FDI (redundant with Sequential IBD).

### 3.2 Environment Pruning (7 down to 4)
- **Keep:** SCM Family L, SCM Family N, Gymnasium CartPole, Gymnasium Inverted Pendulum.
- **Cut/Defer:** Acrobot, Reacher, HalfCheetah. (Deferred to Paper 2 where multi-joint continuous control is required for world models).

---

## 4. Revised Feasible Schedule

With the Two-Tier MVP scope fence applied, Daniel's review queue is reduced from 33 items down to **18 items**, bringing the plan into perfect alignment with calendar realities:

| Phase | Scope-Fenced Work Items | Target Completion | Review Gate |
|---|---|---|---|
| **Stage 0A** | SCM Contract v2.1 (L & N), Invariants E1–E5, 4 baselines | 26 Sep 2026 | Gate 0A |
| **Phase S** | 1-week internal harness shakedown (3 families, bytes budget) | 4 Oct 2026 | Internal note |
| **Stage 0B** | Sequential metrics ($\Delta_{pAUC}$ Pareto), CUSUM/GLR detector | 24 Oct 2026 | Gate 0B |
| **Tier T2 MVP** | CartPole & Pendulum distractor wrappers, stability tuning | 7 Nov 2026 | Gate T2 |
| **Paper 1 Pilot** | Threshold sweeps across 4 environments, shared delay intervals | 21 Nov 2026 | Pilot sign-off |
| **Confirmation** | 240 primary runs + 360 response surface runs (reduced grid) | 15 Dec 2026 | Data freeze |
| **Write-up** | Daniel writes Paper 1 (Boundary-Bench MVP); release on arXiv | **Late Jan 2027** | arXiv submission |
| **Paper 2 (T3)** | World Models (Iso-Dream / Delusions of Agency on MuJoCo) | Feb – May 2027 | Conference target |

**Conclusion:** The Two-Tier MVP protects Daniel's cognitive bandwidth, keeps the MacBook Air from overheating on unmanageable simulation sweeps, and delivers a clean, high-impact benchmark paper on arXiv by late January 2027.
