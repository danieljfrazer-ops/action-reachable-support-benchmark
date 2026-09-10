# Adjudication of Peer Reviews (Gemini Round 4)

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 7 September 2026  
**Target Frozen Version:** `442cc4b7da691ca0` (verified via `python3 freeze.py`)  
**Inputs Evaluated:**
- `review4-claude-opus/findings.md`, `sim_e2e.py`, `sim_e2e.output.txt`, `new_mutants.py`, `new_mutants.output.txt`
- `review4-codex/findings.md`, `independent_end_to_end.py`, `independent_end_to_end_results.json`, `method_sensitivities.py`, `method_sensitivities.json`, `surviving_mutant_absolute_primary_difference.py`

---

## Executive Summary of Round 4 Adjudication

All three independent models (Gemini, Claude Opus, Codex) achieved end-to-end simulation from the two frozen draft specifications alone without importing prior review code. There is unprecedented technical consensus across all three reviews on the critical vulnerabilities of the Round 4 architecture:

1. **Comparator Delay Misspecification at $\tau = 2$:** All three models independently discovered that the passive comparator's lag-1 model regresses on current action $a_t$, which under $\tau = 2$ has zero immediate causal impact on $o_{t+1}$. Codex demonstrated that a simple delay-aware action feature $[o_t, a_{t-2}, 1]$ elevates comparator AUC to **0.997**, entirely erasing the confounding benefit contrast.
2. **Alarm Channel Warm-Up Collapse:** Claude Opus and Gemini demonstrated that during the warm-up period ($a_c \equiv 0$), the standardized statistic takes its global maximum ($stat_{warm} \approx 5.44$–$5.68$), inducing instantaneous false alarms at step 63 for any $h \le 5.25$, rendering the target $[900, 1100]$ ARL_0 band mathematically unattainable.
3. **Decision Rule D-9.3 Brittleness & Equivalency Failure:** Claude Opus demonstrated that the R0-absent equivalence rule (90% TOST $\pm 0.05$) deterministically fails across all cells (CI $[+0.06, +0.16]$) with no declared failure protocol; Codex demonstrated that 10 seeds are severely underpowered to clear the $\delta_{AUC} = 0.10$ lower bound.
4. **Interface v3 Missing Raw Score Output:** All three reviewers identified that `update()` returns only $(p[C], stat, raise)$, with no public callable API to extract the raw support vector ($a_c$ or $q_c$) required to compute primary AUC.
5. **Surviving Gate Mutants:** Every reviewer successfully authored surviving mutants that pass all 34 frozen gate tests: Gemini's structural DAG leak (`R4-GM-M1`), Codex's direction-erasing aggregator (`aggregate_abs`), and Claude Opus's alarm matching (`R4-M1`), colliding-row aggregation (`R4-M2`), and signed-effect perturbation (`R4-M3`).

---

## 1. Adjudication of Claude Opus Findings (`review4-claude-opus/findings.md`)

| ID | Peer Severity | Gemini Verdict | Rationale (One Line) |
|---|:---:|:---:|---|
| **R4-1** | Critical | **Valid** | During warm-up $a_c \equiv 0$, causing $stat_{warm} = \max_c \bar{a}_c / v_c \approx 5.5 > null_{max}$, triggering immediate false alarms at step 63 for all $h \le 5.25$ and making $ARL_0 \in [900, 1100]$ unattainable. |
| **R4-2** | High | **Valid** | Conditioning on full observed state $o_t$ explains downstream observations $d_{t+1}$ entirely through $C_d b_t$, forcing action coefficients $\beta_{a,d} \approx 0$ by construction and blinding the comparator to downstream support. |
| **R4-3** | High | **Valid** | Under $\tau = 2$, current action $a_t$ has zero causal effect on $o_{t+1}$, rendering the lag-1 comparator structurally misspecified and collapsing its AUC to $\le 0.540$ even in the absence of confounders. |
| **R4-4** | High | **Valid** | $n\_min\_sign = 3$ is evaluated over the entire 25-unit window (which retains 6/6 usable cells at offset 200); the observed attenuation is driven purely by 60% pre-event unit dilution. |
| **R4-5** | High | **Valid** | Partitioning 25 probes across 4 $(k, sign)$ bins yields $P(\min(n_+, n_-) < 3) \approx 12.7\%$, dropping entire actuators and creating an irreducible variance floor that zeroes out surviving actuator support in ~10% of episodes. |
| **R4-6** | High | **Valid** | Confirmed across all models: IBD significantly outperforms the comparator in confounder-absent cells ($\Delta_{AUC} \approx +0.09$ to $+0.11$), causing deterministic failure of the 90% TOST $\pm 0.05$ equivalence test without a defined contingency branch. |
| **R4-7** | High | **Valid** | In instances with numerous negative distractor and padding channels, baseline loadings maintain comparator AUC $> 0.5$ in 85–100% of episodes, causing F1 as a hard $< 0.5$ assertion to fail across standard instance draws. |
| **R4-8** | High | **Valid** | The trailing 500-step evaluation window is predominantly pre-event at offsets 10 (96%), 50 (88%), and 200 (60%), causing the D-5-locked co-primary to measure pre-event baseline behavior rather than post-event adaptation. |
| **R4-9** | Medium | **Valid** | Predictor coefficients $\beta$ and baseline loadings $l_c$ depend on instance-specific matrices and cannot be shared across distinct instance draws without destroying calibration validity. |
| **R4-10** | Medium | **Valid** | Confirmed by witness: `test_gate.py` never exercises multiple alarms within a single event window, allowing a mutant returning the latest alarm to pass all gate tests. |
| **R4-11** | Medium | **Valid** | Confirmed by witness: `aggregate_primary` keys solely on `(seed, level, delay)`, causing silent row collisions across environments, regimes, and confounders where first-wins or last-wins mutants pass undetected. |
| **R4-12** | Medium | **Valid** | Finite-difference perturbation derivations can produce signed effects $e$, which bypass thresholding under $|gain \cdot e|$ when test fixtures only supply positive effect magnitudes. |
| **R4-13** | Medium | **Valid** | The evaluator has full access to oracle labels; the genuine mathematical rationale for pooling isotonic regression is preventing degeneracies on static channel labels within episodes. |
| **R4-14** | Medium | **Valid** | Pooling all epochs into the isotonic fit pairs transition-band mixed windows with post-event labels, injecting label noise into the empirical calibrator grid. |
| **R4-15** | Medium | **Valid** | Consecutive epochs share 96% of trailing window samples; counting 200 channel-epochs over-represents independent sample size by ~25× and fails to guarantee calibration stability. |
| **R4-16** | Medium | **Judgment Call** | While probe signs are mathematically decodable from continuous actions, enforcing formulaic sign-blindness via architectural constraints remains a viable alternative to discarding sign-blindness. *(Opinion: Behavioral flag permutation is ineffective, but formulaic verification remains enforceable).* |
| **R4-17** | Medium | **Valid** | The harness must own oracle-dependent isotonic regression, but `interface-spec-v3` lacks a method to pass fitted calibrator knots into the estimator. |
| **R4-18** | Medium | **Valid** | Although `raw_support_stat_stream` is named in the ledger, `update()` returns only $(p, stat, raise)$, preventing external evaluators from accessing the raw scores needed for primary AUC. |
| **R4-19** | Medium | **Valid** | The lack of a normative instance generator allows reviewers to test disparate matrix structures, causing AUC variation (0.75–0.93) to reflect generator artifacts rather than estimator properties. |
| **R4-20** | Medium | **Valid** | Discontinuous statistics yield mass ties at $a_c = 0$ and $q_c = -40$, yet tie-handling conventions are omitted and AUC computation has no test ID in the gate coverage matrix. |
| **R4-21** | Medium | **Valid** | `comparator-spec` uses `cusum_linear_channel_agnostic` while `contract_ref.aggregate_primary` defaults to `cusum_channel_agnostic`, silently dropping all rows upon execution. |
| **R4-22** | Low | **Valid** | Clamping extreme live residuals to $-q_{cap} = -40$ merges valid low-support channels with degenerate channels at the boundary knot. |
| **R4-23** | Low | **Valid** | Probes applied at $t = 2000$ cannot close observation units within a $T = 2000$ horizon, needlessly expending 1% of the probe budget. |
| **R4-24** | Low | **Valid** | Variables $stat$, $a_c$, and $p\_cache$ are unassigned before epoch 1 ($t < 23$), causing initial `update()` calls to fail hard NaN assertions. |
| **R4-25** | Low | **Valid** | Amendment J7 explicitly mandated GM3-7 (optional jitter) among carried-forward requirements, but draft 3 dropped it without documenting a formal rejection decision. |

---

## 2. Adjudication of Codex Findings (`review4-codex/findings.md`)

| ID | Peer Severity | Gemini Verdict | Rationale (One Line) |
|---|:---:|:---:|---|
| **R4-CX-01** | High | **Valid** | Confirmed by Codex's executable sensitivity: feeding $a_{t-2}$ to the comparator raises its AUC to 0.997, proving that IBD's apparent advantage at $\tau = 2$ is an artifact of comparator misspecification. |
| **R4-CX-02** | High | **Valid** | Ridge regression penalizes unstandardized coefficients against a global trace penalty; rescaling a single channel altered $\lambda$ by $>1600\times$ and shifted loadings by 21–27%. |
| **R4-CX-03** | High | **Valid** | `update()` returns only $(p[C], stat, raise)$, providing no public API method for an independent evaluation harness to extract the raw support vector needed for primary AUC. |
| **R4-CX-04** | High | **Valid** | Additive sensor noise ($\sigma_o = 0.05$) ensures padding channels have residual SD $\approx 0.05 \gg \sigma_{deg} = 0.001$, and sensor copies with independent noise produce $|q_1 - q_2| \approx 0.35$, violating fixtures F3 and F4. |
| **R4-CX-05** | High | **Valid** | Comparator specifications define two conflicting calibration paths (shared non-probed fit vs arm-specific probed threshold calibration) with no supporting interface signatures. |
| **R4-CX-06** | High | **Valid** | The leave-one-instance-out calibration scheme lacks instance count definitions, fold assignments, seed hierarchies, and diverse event times in `confirmation-design.csv`. |
| **R4-CX-07** | High | **Valid** | Computing raw per-channel AUC violates Contract C5's equivalence class principle: duplicating redundant sensors alters AUC and its variance without changing the underlying causal graph. |
| **R4-CX-08** | Medium | **Valid** | Indexing the post-transition observation in pseudocode shifts the anchor horizon by one step ($h \to h-1$), reducing measured IBD AUC by ~0.05–0.06. |
| **R4-CX-09** | Medium | **Valid** | Multinomial sign variance across 25 probes causes 12.7% of episodes to drop an actuator under $n\_min\_sign = 3$, returning $a_c = 0$ and misrepresenting sample sparsity as absence of support. |
| **R4-CX-10** | Medium | **Valid** | Continuous actions directly reveal probe timing and sign ($\pm e_k$), rendering behavioral flag-permutation tests unable to enforce sign-blindness. |
| **R4-CX-11** | Medium | **Valid** | With confounding benefit effects of $\approx 0.103$–$0.127$ and standard error $\approx 0.015$, 10 seeds are mathematically insufficient to place the lower 95% endpoint above $\delta_{AUC} = 0.10$. |
| **R4-CX-12** | Medium | **Valid** | Confirmed by executable mutant `surviving_mutant_absolute_primary_difference.py`: taking $|est_a - est_b|$ destroys comparison direction yet passes all 34 gate tests. |
| **R4-CX-13** | Medium | **Valid** | Contract v3.5 §G retains obsolete requirements for matched-ARL primary comparisons and 10% out-of-band exclusions that directly contradict threshold-free AUC. |

---

## 3. Consensus Recommendations for Daniel & Core Team

1. **Fix Comparator Delay Alignment:** Update `comparator-spec.md` to include delayed action features $[o_t, a_{t-\tau}, \dots, a_t, 1]$ or remove $\tau = 2$ from the confirmatory conjunction. Counting a structural misspecification as evidence of interventional superiority compromises scientific integrity.
2. **Resolve Alarm Warm-Up Collapse:** Suppress alarm raising ($stat = 0.0$) until trailing windows contain the minimum required units, and exclude the warm-up prefix from ARL_0 bisection.
3. **Expose Raw Vectors in Interface v3:** Update `interface-spec-v3.md` to have `update()` return `(p[C], raw_stat[C], stat, raise)` or provide an explicit `get_raw_support()` method.
4. **Harden Gate Coverage:** Register all five surviving mutants discovered in Round 4 (`R4-GM-M1`, `aggregate_abs`, `R4-M1`, `R4-M2`, `R4-M3`), extend cell aggregation keys to all dimensions, and implement explicit AUC tests.
5. **Freeze Instance Generator:** Standardize the generative distributions and sparsity patterns for $A_b, B, C_d, G, W_o$ in a versioned script before executing Stage 0A confirmation.
