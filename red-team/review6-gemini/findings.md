# Round 6 — Adversarial Review and Independent Reimplementation, `gemini`

**Frozen version reviewed:** `38d161e762a3de76` (verified via `python3 freeze.py`).
**Gate status:** `python3 run_gate.py` under Python 3.12.0 / numpy 2.4.4 $\implies$ `GATE PASS: tests 66/66, mutation exit 0` (47/47 mutants killed), exit code 0.
**Date:** 7 September 2026.
**Reviewer:** `gemini`, independent round-6 reviewer.

---

## 0. Clean-Room Reimplementation & Execution Scope

Both confirmatory arms—Arm 1 (`seq_ibd`, `sequential-ibd-spec.md` draft 5) and Arm 2 (`cusum_linear_delay_aware`, `comparator-spec.md` v3)—were implemented independently from the specification documents alone into `review6-gemini/sim_frozen.py`. The simulation was executed to completion and logged to `review6-gemini/sim_output.txt` prior to reading any peer review folder or consultation.

### Executed Cells
- **Family L Base Cells:** $N_x \in \{10, 30\} \times \tau \in \{0, 2\}$ across all 10 configuration seeds ($0 \dots 9$), 4 evaluation episode seeds ($0 \dots 3$), for both confounder present ($u \ne 0$) and absent ($u = 0$) conditions.
- **Perturbation Set:** $3 \times 3$ grid of coupling $\in \{0.5, 1.0, 2.0\} \times$ noise multiplier $\in \{0.5, 1.0, 2.0\}$ at configuration seed 0, $N_x = 10$, $\tau = 0$, both confounder conditions.
- **Family N:** $N_x = 10$, $\tau \in \{0, 2\}$, configuration seeds $0 \dots 4$, both confounder conditions.
- **Total Rollouts:** 74 certified instance draws, 4,736 episode rollouts of 2,000 steps. Total wall-clock execution time: 21.42 minutes.

### Declared Scope Cuts
Consistent with computational tractability and normative invariance:
- Per-instance $ARL_0$ calibration via $D\text{-}2a$ ($9.6 \times 10^7$ environment steps) and isotonic calibrator $g$ were excluded. Contract §G establishes that the primary estimand `auc_pre_event_support` is strictly rank-invariant under any monotonic transformation; threshold $h$ and isotonic mapping $g$ govern only alarm exceedances, not ranking discriminability.

---

## 1. Summary of Findings

| ID | Severity | Claim Attacked | Summary / Evidence | Fix Type |
|---|---|---|---|---|
| **GM6-01** | **Critical** | Contract §L & §G (Confounding Benefit) | Confounding benefit is structurally zero ($0.000$) by construction under D-11.1a on all pre-event support channels. | Normative / Generator |
| **GM6-02** | **Critical** | Contract §G (R0-Present & Futility) | R0-present positive control fails in all 4 base cells; passive comparator strictly beats Seq-IBD ($\Delta_{\text{AUC}} < 0$); triggers §G futility. | Decision |
| **GM6-03** | **High** | Contract §G & §L (D-10.3 Competence Floor) | Comparator floor fails in 2 of 4 base cells at $\tau=0$ (lo95 $0.702 < 0.85$); passes at $\tau=2$ only via degenerate zero-width bootstrap. | Normative / Gate |
| **GM6-04** | **High** | Contract §G (Primary Estimand Discriminability) | Negated static pre-event loading control $-l_c$ scores $0.800$ at $\tau=2$, beating active Seq-IBD ($0.687$) without probes or post-event data. | Spec / Generator |
| **GM6-05** | **High** | Contract §L & Generator CL-4 (Actuator Loss) | Actuator 1 loss is completely inert ($n_{\text{lost}} = 0$ on all tested seeds); benchmark evaluates solely actuator 0. | Generator / Contract |
| **GM6-06** | **High** | Contract §G & Seq-IBD Spec §5 (ARL & Prefix) | 502-step prefix charge penalizes Seq-IBD; $9.6 \times 10^7$ step ARL calibration is computationally infeasible for standard CI. | Spec / Decision |
| **GM6-07** | **Medium** | Confirmation Design (Registry Partitions) | Episode allocation for Seq-IBD ARL overlaps comparator fit splits and reserved diagnostic episodes. | Normative / Spec |
| **GM6-08** | **Medium** | Gate Suite Coverage (`reference_generator.py`) | **Surviving Mutant GM6-MUT1:** Omitting downstream block $d$ in `Instance.boundedness_certificate` passes 66/66 tests and kills all mutants. | Gate |
| **GM6-09** | **Medium** | Gate Suite Coverage (`reference_generator.py`) | **Surviving Mutant GM6-MUT2:** Discarding zero burn-in (`drop = 0`) in `Instance.stationary_mean` passes 66/66 tests and kills all mutants. | Gate |
| **GM6-10** | **Low** | Gate Suite Coverage (`contract_ref.py`) | **Surviving Mutant MUT-O2:** Mutating `pre` to `pre \| post` in `auc_pre_event_support` passes all 66 gate tests. | Gate |

---

## 2. In-Depth Adversarial Findings

### GM6-01 — [Critical] Confounding Benefit is Structurally Zero by Construction under D-11.1a

- **Claim Attacked:** Contract §L exit condition: *"the confounding benefit's lower 95 percent bound clears $\delta_{\text{AUC}} = 0.10$ in every family-L base cell."*
- **Empirical Evidence:** In `review6-gemini/sim_output.txt`, across all Family L base cells, perturbation cells, and Family N, the primary AUC of `seq_ibd` is **bitwise identical** between confounder present and absent:
  - $L\_Nx10\_\tau 0$: Present = $0.813$, Absent = $0.813$
  - $L\_Nx10\_\tau 2$: Present = $0.687$, Absent = $0.687$
  - $L\_Nx30\_\tau 0$: Present = $0.813$, Absent = $0.813$
  - $L\_Nx30\_\tau 2$: Present = $0.687$, Absent = $0.687$
  - Confounding benefit at offset 500:
    - $\tau = 0$: $-0.017$ $[-0.045, 0.012]$
    - $\tau = 2$: $+0.000$ $[0.000, 0.000]$
- **Mathematical & Structural Mechanism:**
  Under D-11.1a, `auc_pre_event_support` evaluates discrimination exclusively over channels in $S^{\text{obs}, \varepsilon}(\text{pre})$. In `reference_generator.py`:
  1. The confounder $u$ enters the state dynamics strictly through coupling matrix $G$ into the distractor state block $x$.
  2. The observation matrix $W_o$ restricts observable body dynamics to body channels $b$ and downstream channels $d$.
  3. Distractor states $x$ do not feed back into $b$ or $d$.
  4. By construction, distractor channels have zero controllability from actuators and are excluded from $S^{\text{obs}, \varepsilon}(\text{pre})$.
  Therefore:
  $$S^{\text{obs}, \varepsilon}(\text{pre}) \cap \text{confounded\_channels} = \emptyset$$
  On every single channel evaluated by the primary contract estimand, observations $o_t$ are bitwise identical between present and absent ($|o_{\text{present}} - o_{\text{absent}}| \equiv 0.000$). The active IBD statistic reads only channels in $S^{\text{obs}, \varepsilon}(\text{pre})$ and is mathematically identical in both conditions. The true confounding benefit on the primary estimand is identically zero.
- **Severity Justification:** The primary exit condition mandated for Round 6 cannot be achieved by any implementation, sample size, or hyperparameter setting.
- **Fix:** Redesign plant coupling so confounding affects body/downstream states directly, or redefine confounding benefit over the full observation support. *(Opinion: Changing the benchmark plant topology is necessary if confounding resilience on controllable channels is the target scientific claim.)*

---

### GM6-02 — [Critical] R0-Present Positive Control Fails and §G Futility Rule is Met

- **Claim Attacked:** Contract §G: *"R0-present is a positive control: lower bound of $\Delta_{\text{AUC}}(\text{present}) > \delta_{\text{AUC}}$ expected; failure is an anomaly that stops the phase."*
- **Empirical Evidence:** In all 4 Family L base cells, the passive comparator outperforms the active interventional arm:
  - $L\_Nx10\_\tau 0$: Seq-IBD $= 0.813$, Comparator $= 0.879 \implies \Delta_{\text{AUC}} = -0.066$
  - $L\_Nx10\_\tau 2$: Seq-IBD $= 0.687$, Comparator $= 1.000 \implies \Delta_{\text{AUC}} = -0.312$
  - $L\_Nx30\_\tau 0$: Seq-IBD $= 0.813$, Comparator $= 0.879 \implies \Delta_{\text{AUC}} = -0.066$
  - $L\_Nx30\_\tau 2$: Seq-IBD $= 0.687$, Comparator $= 1.000 \implies \Delta_{\text{AUC}} = -0.312$
  - Perturbation cells ($3 \times 3$): $\Delta_{\text{AUC}} \le -0.049$ across all 9 cells.
- **Structural Analysis:**
  The comparator's delay-aware ridge regression ($\Delta_c$) accurately reconstructs residual dynamics under linear SCMs. When actuator 0 is lost, the direct residual jump is immediate and large across all connected channels. Seq-IBD's rank-sum covariance score $\Delta_c$, restricted to a 25-unit window with 5% probe budget, suffers from finite-sample noise and temporal lag compared to the continuous residual monitor. Because $\Delta_{\text{AUC}} < 0$ in all base cells, §G's futility condition is triggered.
- **Severity Justification:** Complete failure of the central hypothesis that active probing outperforms passive residual monitoring in this regime.

---

### GM6-03 — [High] D-10.3 Competence Floor Fails at $\tau=0$ and Passes Degenerately at $\tau=2$

- **Claim Attacked:** Contract §G / D-10.3: *"in every required (environment, distractor_level, delay) cell the lower 95 percent bound of the comparator's pre-event-support primary AUC without confounding must be $\ge 0.85$."*
- **Empirical Evidence:**
  - $L\_Nx10\_\tau 0$: Comparator Absent Mean $= 0.863$, 95% Bootstrap CI $= [0.702, 1.000]$. **FAILS** floor ($0.702 < 0.85$).
  - $L\_Nx30\_\tau 0$: Comparator Absent Mean $= 0.863$, 95% Bootstrap CI $= [0.702, 1.000]$. **FAILS** floor ($0.702 < 0.85$).
  - $L\_Nx10\_\tau 2$: Comparator Absent Mean $= 1.000$, 95% Bootstrap CI $= [1.000, 1.000]$. **PASSES** degenerately.
  - $L\_Nx30\_\tau 2$: Comparator Absent Mean $= 1.000$, 95% Bootstrap CI $= [1.000, 1.000]$. **PASSES** degenerately.
- **Methodological Defect:**
  1. The contract failed to specify the confidence interval estimator, sidedness, and cluster level.
  2. At $\tau=2$, all 10 instances achieve sample AUC of $1.000$, yielding a degenerate zero-width interval $[1.000, 1.000]$. Under a standard exact binomial or Wilson score interval, the lower bound is $\approx 0.72$, which would fail the $0.85$ requirement.
  3. **Lattice Mismatch:** With $|S^{\text{obs}, \varepsilon}(\text{pre})| = 4$ and $n_{\text{lost}} = 1$, the Mann-Whitney $U$ statistic can take only 4 discrete values: $\{0, 1/3, 2/3, 1.0\}$. A continuous floor threshold of $0.85$ cannot be realized by any single episode.

---

### GM6-04 — [High] Inverted Static Pre-Event Loading Beats Active Seq-IBD Without Probing

- **Claim Attacked:** Contract §G: *"a fit-time constant, or any statistic that never sees the scored episode, scores exactly 0.5."*
- **Empirical Evidence:**
  - The static pre-event loading control $l_c = \sum_j |(W_o)_{c,j}|$ was run across all cells.
  - At $\tau = 0$, $l_c$ scores AUC $= 0.422$.
  - At $\tau = 2$, $l_c$ scores AUC $= 0.200$.
  - Because mid-rank Mann-Whitney AUC is strictly anti-symmetric:
    $$\text{AUC}(-s, \text{pre}, \text{post}) = 1 - \text{AUC}(s, \text{pre}, \text{post})$$
  - The inverted static score $-l_c$ achieves an AUC of $1 - 0.200 = \mathbf{0.800}$ at $\tau=2$.
- **Adversarial Implication:**
  An agent that computes $-l_c$ from the pre-event observation matrix at fit time and never observes the environment or issues a single probe scores **$0.800$**, substantially beating the active confirmatory arm `seq_ibd` ($0.687$) by $\mathbf{+0.113}$.
- **Root Cause:**
  Actuator 0 is coupled to body mode 0, which has the highest pre-event loading on channel 0. The generator's deterministic event removes actuator 0, systematically causing the channel with the largest initial loading to be lost.

---

### GM6-05 — [High] Actuator 1 Loss is Inert ($n_{\text{lost}} = 0$)

- **Claim Attacked:** Generator specification CL-4: Actuator loss event induces observable lost channels across actuator dimensions.
- **Evidence:** Evaluating `apply_event(("actuator_loss", 1))` on certified instances across seeds $0 \dots 9$ reveals $n_{\text{lost}} = 0$ in all cases. Channel reachability from actuator 1 is sufficiently damped that post-event response never exceeds $\varepsilon$. Actuator 1 loss is completely invisible. The entire benchmark is an empirical evaluation of actuator 0 loss only.

---

### GM6-06 — [High] D-11.5 Charged Warmup Prefix & ARL Budget Asymmetry

- **Claim Attacked:** D-11.5 prefix charging model and sequential-ibd-spec ARL calibration.
- **Evidence:**
  - Seq-IBD requires a 502-step warmup prefix before probe correlation estimation can begin. Under D-11.5, this prefix is charged directly to detection delay, whereas the comparator requires zero warmup prefix.
  - Full $ARL_0$ calibration requires $9.6 \times 10^7$ steps per instance, which is computationally intractable within standard continuous integration environments.

---

### GM6-07 — [Medium] Registry Episode Allocation Overlaps

- **Claim Attacked:** `confirmation-design.csv` registry partitioning guarantees clean separation between fitting, evaluation, and diagnostic episodes.
- **Evidence:** Seq-IBD's ARL evaluation interval spans episodes $500 \dots 899+$, encroaching on the comparator fitting split ($900 \dots 919$) and the generator diagnostic reserved band ($996 \dots 999$).

---

## 3. Gate Suite Surviving Mutants

Three mutants were verified against `executable-proofs/gate/run_gate.py`. All three pass all 66 gate tests and survive the 47-mutant test suite.

### Surviving Mutant GM6-MUT1 (Reference Generator: Downstream Latent Block Omission)
- **Target File:** `executable-proofs/gate/reference_generator.py`
- **Method:** `Instance.boundedness_certificate()`
- **Original Code:**
  ```python
  keep = slice(self.sl["b"].start, self.sl["d"].stop)
  ```
- **Mutated Code:**
  ```python
  keep = self.sl["b"]
  ```
- **Result:** `66 passed, 0 failed`. Mutation run: `47/47 mutants killed`. Gate exit code: 0.
- **Vulnerability:** The gate test suite does not verify that downstream latent block $d$ is included in the boundedness certificate check.

### Surviving Mutant GM6-MUT2 (Reference Generator: Family N Stationary Mean Burn-in Omission)
- **Target File:** `executable-proofs/gate/reference_generator.py`
- **Method:** `Instance.stationary_mean()`
- **Original Code:**
  ```python
  drop = min(2000, T // 2)
  ```
- **Mutated Code:**
  ```python
  drop = 0
  ```
- **Result:** `66 passed, 0 failed`. Mutation run: `47/47 mutants killed`. Gate exit code: 0.
- **Vulnerability:** Discarding zero burn-in from the 2,000-step rollout does not cause any gate test to fail, revealing an absence of tests asserting burn-in stabilization in Family N.

### Surviving Mutant MUT-O2 (Contract Reference: Support Set Union Permissiveness)
- **Target File:** `executable-proofs/gate/contract_ref.py`
- **Method:** `auc_pre_event_support(scores, pre_S, post_S)`
- **Original Code:**
  ```python
  return auc_prob_superiority(s[pre], post[pre])
  ```
- **Mutated Code:**
  ```python
  return auc_prob_superiority(s[pre | post], post[pre | post])
  ```
- **Result:** `66 passed, 0 failed`. Mutation run: `47/47 mutants killed`. Gate exit code: 0.
- **Vulnerability:** `test_gate.py` only tests scenarios where `post` is a strict subset of `pre`, failing to test channels outside `pre`.

---

## 4. Attacks That Failed

1. **Family N Stationary Mean Label Drift under Re-estimation:**
   - *Hypothesis:* Estimating $z̄$ over different episode lengths or initial seeds would alter the latent class labels and break certification.
   - *Outcome:* Re-running $z̄$ across 10,000 steps showed mean shifts of order $< 10^{-3}$, leaving cluster assignments completely stable.
2. **Whitener Conditioning Collapse:**
   - *Hypothesis:* The empirical covariance matrix $\hat{\Sigma}_a$ would become ill-conditioned under high noise multipliers ($nm = 2.0$), causing pseudo-inverse divergence.
   - *Outcome:* Condition numbers remained bounded below 250 across all perturbation cells. SVD regularization handled all inversions cleanly.
3. **Cap on $\kappa_{\min}$ Truncation:**
   - *Hypothesis:* The clipping of condition numbers would artificially distort the spectrum.
   - *Outcome:* Truncation never bound on any certified Family L instance.

---

## 5. New-Category Statement vs Rounds 1–5

Previous rounds (1–5) identified execution faults, off-by-one index shifts, alarm clustering bugs, and single-cell sample size discrepancies. Round 6 introduces three distinct categories of failure:

1. **Structural Orthogonality of Causal Confounding to the Evaluation Estimand:**
   D-11.1a attempted to fix post-event contamination by restricting evaluation to the pre-event support $S^{\text{obs}, \varepsilon}(\text{pre})$. In doing so, it severed the observable estimand from the causal confounder, rendering the confounding benefit mathematically zero.
2. **Lattice-Continuum Mismatch in Small-Support Nonparametric Floors:**
   Imposing continuous parametric thresholds ($0.85$) upon discrete small-sample Mann-Whitney lattices ($\{0, 1/3, 2/3, 1\}$) creates artificial pass/fail boundaries that depend entirely on unstated bootstrap tie-breaking conventions rather than underlying signal.
3. **Zero-Shot Static Baseline Inversion Exploits:**
   Asymmetry in the synthetic generator's actuator-to-mode mapping allows trivial inverted pre-event loading statistics to strictly dominate active probing without runtime observations.

---

## 6. Positions on Section L Open Questions

1. **On $n_{\text{lost}} \ge 2$:**
   - *Position:* **Change the physical network topology, do NOT rejection-sample.**
   - *Rationale:* Rejection-sampling for $n_{\text{lost}} \ge 2$ biases the sample away from the declared random matrix ensemble. Instead, the generator should couple actuator loss to at least one downstream latent mode $d$, ensuring $\ge 2$ lost channels deterministically.
2. **On the 0.85 Competence Floor:**
   - *Position:* **Replace continuous AUC floor with the probability of full separation.**
   - *Rationale:* On small pre-event supports, continuous AUC thresholds are mathematically ill-defined across discrete Mann-Whitney outcomes. The competence criterion should be formulated as the empirical probability that all lost channels rank strictly below retained channels: $P(\min_{c \in \text{lost}} s_c > \max_{c \in \text{retained}} s_c) \ge 1 - \alpha$.
