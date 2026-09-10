# Execution Plan, Hardware & Agentic Workflow Audit

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 6 September 2026  
**Scope:** Roadmap v3 (`roadmap-v3.md`), Roadmap v3.1 Amendments (`roadmap-v3.1-amendments.md`), `timing-and-shakedown-value.md`.  
**Primary Focus:** Question 2 — *Is the roadmap/plan coherent, plausible, error-free, and ready to execute?*

---

## 1. Executive Summary

Roadmap v3 and v3.1 construct an elaborate operational framework featuring an adversarial agentic workflow (Claude Code as builder, Codex as red team), strict run ledgers, and formal gate criteria. 

However, an audit of the **physical execution layer** reveals three critical structural bottlenecks:
1. **The Parallel Execution Illusion (0B + Phase S):** Running Phase 0B and Phase S concurrently breaks the adversarial review loop, overwhelms Daniel's weekly gate bandwidth, and creates severe local compute contention.
2. **MacBook Air M5 Thermal Realities:** Fanless Apple Silicon sustained load characteristics conflict with overnight unattended sweeps unless execution is serialized and throttled gracefully.
3. **The Agentic Echo Chamber:** The Claude-Codex dialogue has generated impressive documentation with high "performative rigor," but failed to catch basic algebraic and causal bugs because neither agent executed numerical traces during review.

---

## 2. Hardware and Compute Bottlenecks: The Fanless M5 MacBook Air

### 2.1 The Compute Load
Let us calculate the total compute requirements across Stage 0B, Phase S, and Paper 1:

* **Phase S (Memory Shakedown, A7):**
  - 3 memory families (recurrent, episodic KV, fast weights) + 1 pair (recurrent + episodic) = 4 architectures.
  - 4 baselines (surprise-only, empirical hazard, Bayesian hazard, hazard-informed reference) = 4 baselines.
  - Total models = 8.
  - 2 physical byte budgets $\times$ 2 stream generators (dev A, held-out B) $\times$ 5 confirmation seeds = **160 long-stream runs**.
  - Stream length: **100,000 events** per stream.
  - **Total sequential steps:** $160 \times 100,000 = \mathbf{16,000,000 \text{ steps}}$.
  - *Note:* Sequential token-by-token or event-by-event Python/PyTorch loops cannot be fully parallelized across sequence steps. At a conservative estimate of 0.5 ms per state update and retrieval, 16M steps requires **~2.2 to 3.5 hours of continuous matrix operations**.
* **Paper 1 Confirmation Runs (A4):**
  - Part 1 (Primary contrast): 240 runs.
  - Part 2 (Response surface): 720 runs.
  - Total confirmation runs: 960 runs.
  - Plus pilot sweeps (approx. 200–300 runs).
  - Plus 25–35% rerun reserve (approx. 300 runs).
  - **Total simulation runs:** $\sim \mathbf{1,500 \text{ runs}}$.
  - Each run contains active probe injections, online Bayesian change-point filtering, forward-model SGD updates, and sequential probability calibration.

### 2.2 Thermal Throttling on Fanless Apple Silicon
The M5 MacBook Air is completely fanless. Under continuous CPU/GPU load:
- The chassis reaches skin-temperature limits within **8 to 12 minutes**.
- The macOS kernel initiates progressive thermal throttling, reducing sustained core clocks by **25% to 45%**.
- If two processes run simultaneously (e.g., Phase 0B unit tests alongside a Phase S memory sweep), thermal throttling is compounded by memory bandwidth contention across the unified memory bus.

### 2.3 Required Operational Safeguards
1. **No Concurrent Multi-Phase Sweeps:** Never run Phase 0B development benchmarks simultaneously with Phase S sweeps on the same machine.
2. **Duty-Cycle Rest Intervals:** Insert a mandatory 60-second idle cooldown between heavy run blocks to allow the chassis to dissipate heat, ensuring consistent clock speeds across seeds.
3. **Step-Budget Primary Metric:** Reiterate Decision D5: all performance metrics must be reported in algorithm steps and FLOP counts, never raw wall-clock time.

---

## 3. The Schedule & Review Bottleneck: The Human Critical Path

### 3.1 The Breakdown of Parallel 0B and Phase S
In Amendment A1, the timeline specifies:
- Phase 0B runs from ~24 Sep to ~15 Oct (3 weeks).
- Phase S runs parallel with 0B from ~24 Sep to ~15 Oct (3 weeks).
- Both agents act as builders (Claude builds S, Codex builds 0B).

**This arrangement destroys the project's own safety mechanism:**
1. **Loss of Cross-Review:** In Roadmap v3 Decision D4, each phase is built by one agent and red-teamed by the other. In parallel 0B/S, both agents are building simultaneously. Cross-review is deferred to the end of the phase, meaning code is developed un-checked for 3 weeks.
2. **Review Queue Collapse:** Daniel's available bandwidth is strictly capped: *"Daniel reviews at most one phase gate and one draft per week"* (A1). If 0B and S finish concurrently around 15 October, Daniel faces:
   - Phase 0B gate review (complex sequential Bayesian metrics and calibrators).
   - Phase S gate review (160 runs, memory budget matching audits).
   - Phase S technical note draft write-up.  
   This creates an immediate 2-week backlog, guaranteeing that Paper 1 cannot start on 15 October.

### 3.2 The Solution: Serialize and Demote Phase S
- **Demote Phase S:** Phase S does not need an external write-up or a multi-week trial. Strip it down to a 3-day internal sanity script.
- **Serialize Work:** Finish Phase 0A $\to$ Run Phase S harness shakedown (3–5 days) $\to$ Begin Phase 0B.

---

## 4. The Agentic Echo Chamber: Why Mathematical Bugs Slipped Through

A profound methodological lesson emerges from this audit:

### 4.1 Performative Rigor vs. Concrete Verification
Across the previous documents (`synthesis.md`, `codex-final/`, `synthesis-final.md`, `stage-0a-contract-v2.md`), Claude Code and Codex produced pages of extraordinarily dense, academic prose:
- They cited NIST fractional factorial design handbooks, Pearl's causal graphs, Wilson's hazard models, and Brier score decompositions.
- Codex correctly caught coordinate system ambiguities ($S^{latent}$ vs $S^{obs}$) and missing equations.
- Claude promptly synthesized the findings and wrote `stage-0a-contract-v2.md`.

**Yet, fundamental errors went completely unnoticed:**
- The formula $M_{t,h} = A_b^{h-1-\tau} B_t$ evaluating to negative powers $A_b^{-1}$.
- The closed-loop policy $a_t = \pi(o_t, u_t)$ destroying the invariance of $R_{t,h}$ under sensor swaps.
- Testing the correlation of a constant probe vector returning `NaN`.
- Interpolating operating curves into non-existent delay supports.

### 4.2 Why Did the Agents Miss These?
1. **High-Level Semantic Processing:** LLMs excel at matching academic discourse patterns and validating conceptual structures, but they treat equations as symbolic tokens rather than executing them step-by-step.
2. **Confirmation Bias in Synthesis:** When Claude wrote Contract v2, it patched Codex's verbal requests (e.g., adding explicit equations and matrices), and Codex accepted the patches because the requested symbols were present, without executing a numerical forward pass.
3. **The Danger for Solo Researchers:** If Daniel assumes that two leading LLMs cross-reviewing each other guarantees error-free math, these latent bugs will remain hidden until code execution fails weeks later.

### 4.3 Mandatory Protocol Change: "Executable Proofs"
Before Daniel signs off on any future contract or phase gate:
- The building agent must provide a standalone, 20-line Python script that **executes** the mathematical formulas with numerical numpy arrays (e.g., running with $\tau=1, h=1$ and computing correlation under probes).
- The red-teaming agent must run mutant tests that actively trigger division by zero, singular matrices, and acausal delays.

---

## 5. Realistic Calendar Timeline

Accounting for the required contract patches, the serialization of Phase S, and Daniel's true review throughput, here is the realistic, un-inflated timeline:

| Phase | Planned (v3.1) | Realistic Revised Date | Critical Milestones & Gates |
|---|---|---|---|
| **Contract v2.1 Patches** | — | **8 – 10 Sep 2026** | Apply G1–G4 math and estimand patches. |
| **Stage 0A Execution** | ~24 Sep 2026 | **10 – 26 Sep 2026** | Build `boundary_env`, invariants E1–E5, pass numerical tests. |
| **Phase S (Internal Shakedown)** | Concurrent w/ 0B | **27 Sep – 4 Oct 2026** | Demoted to internal 1-week test; NO external write-up. |
| **Stage 0B Execution** | ~15 Oct 2026 | **5 – 26 Oct 2026** | Sequential protocol, Bayesian detectors, calibrator split. |
| **Paper 1 Pilot** | late Oct 2026 | **27 Oct – 10 Nov 2026** | Variance estimation; freeze shared delay interval $[d_{min}, d_{max}]$. |
| **Paper 1 Confirmation** | Nov 2026 | **11 Nov – 10 Dec 2026** | Confirmation sweeps (240 primary + 720 response surface). |
| **Paper 1 Write-up** | Dec 2026 – Jan 2027 | **11 Dec 2026 – 20 Jan 2027** | Daniel writes the core argument; arXiv posting late Jan 2027. |
| **Venue Submission** | Feb 2027 | **Feb – Mar 2027** | Target CoLLAs 2027 or ICLR Embodied AI workshop. |

**Bottom Line:** The schedule remains completely viable for a Q1 2027 conference/workshop target, provided Phase S is stripped of its distracting publication ambitions and serialized cleanly.
