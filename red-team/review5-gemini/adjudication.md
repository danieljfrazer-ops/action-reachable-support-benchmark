# Round-5 Cross-Review Adjudication — Gemini

**Reviewer:** Gemini (Independent Red Team)  
**Date:** 7 September 2026  
**Frozen Version Reviewed:** `0468104f6431b050` (`freeze.py` verified)  
**Peer Artefacts Reviewed:** [`review5-codex/findings.md`](file:///Users/danielfrazer/Documents/Personal/Persistent%20Adaptive%20AI/docs/archive/red-team/review5-codex/findings.md) (17 findings) and [`review5-claude-opus/findings.md`](file:///Users/danielfrazer/Documents/Personal/Persistent%20Adaptive%20AI/docs/archive/red-team/review5-claude-opus/findings.md) (29 findings).

---

## 1. Adjudication of Codex Findings (R5-CX-01 to R5-CX-17)

| ID | Severity | Claim Attacked | Verdict | One Reason |
| :--- | :---: | :--- | :---: | :--- |
| **R5-CX-01** | High | Reference generator implements dense, faithful $B$, and gate rejects generator mutants | **valid** | Mutating generator density survives all 47 gate tests, and certified seeds contain nonzero $A_b$ entries below $c_{min} = 0.20$ due to 0.5 pre-scaling. |
| **R5-CX-02** | High | `draw_certified` enforces CL-4 support change upon actuator loss | **valid** | Post-event support change is omitted from `certify()`, leaving 60%–70% of drawn instances with zero change in observable reachability. |
| **R5-CX-03** | High | D-10.3 passive comparator competence floor ($\ge 0.85$ absent) is attainable | **valid** | All three independent reproductions demonstrate that the comparator-absent lower 95% bound fails 0.85 across all primary base cells. |
| **R5-CX-04** | High | Confounding-benefit superiority margin ($\delta > 0.10$) is settled across perturbations | **valid** | Perturbation aggregate lower bound (0.090) falls below 0.10, and individual seed-0 perturbation cells lack multi-instance replication. |
| **R5-CX-05** | High | Residual mean-shift statistic $q_c$ is competent for complete actuator loss | **valid** | Under zero-mean policy actions, losing an actuator alters residual variance and action covariance rather than residual mean shift. |
| **R5-CX-06** | High | D-10.7 10x4 replication hierarchy has a defined fit and calibration lifecycle | **valid** | The specifications leave unspecified whether predictor models and isotonic maps are fitted per drawn instance or pooled across the cell. |
| **R5-CX-07** | High | `confirmation-design.csv` implements the current arms and replication matrix | **valid** | The design matrix contains only 10 rows per cell without episode seeds and still references demoted legacy appendix estimator IDs. |
| **R5-CX-08** | High | Frozen generator is deterministic across independent processes | **valid** | Using `hash(var) & 0xffff` introduces Python process-randomized string hash salts into trajectory generation, breaking cross-process determinism. |
| **R5-CX-09** | High | Sequential IBD calibration matches Contract §0 fresh-start ARL_0 exposure | **valid** | Starting IBD scoring and the ARL clock at $t=502$ leaves only 498 pre-event steps and exposes the two arms to unequal evaluation horizons. |
| **R5-CX-10** | High | Harness can evaluate mixed persistence ($p=3$ epochs) and refractory ($r=20$ steps) via `count_alarms` | **valid** | The single-integer indexing in `count_alarms` cannot reconcile epoch-stream persistence with step-stream refractory intervals. |
| **R5-CX-11** | High | Frozen generator covers the roadmap SCM confirmation family | **valid** | `reference_generator.py` implements Family L only, leaving Family N and control-tier environments (67% of CSV rows) unexecutable. |
| **R5-CX-12** | Medium | Observation clock, terminal probe count, and offset-1000 read are fully specified | **valid** | Step $t=2000$ does not exist in a 2000-step rollout (0..1999), truncating the 100th probe and leaving the offset-1000 transition read undefined. |
| **R5-CX-13** | High | Passing gate supplies the D-10 exit condition for both arms | **valid** | The gate runs no implementation of either detector and leaves specification-conformance assertions uncovered. |
| **R5-CX-14** | Medium | Balanced pre-randomized probes have a defined estimator RNG lifecycle | **valid** | Interface v4 and Draft 4 omit estimator seed injection, reset protocol, and probe stream synchronization for Arm 3. |
| **R5-CX-15** | High | Frozen generator implements declared burn-in and perturbation axes | **valid** | `burn_in = 2000` is unused dead code, and `noise_mult` scales state/observation noise while leaving policy and confounder noise unscaled. |
| **R5-CX-16** | High | Confirmation can reuse seeds 0–9 as fresh instance draws | **judgment call** | While evaluating seeds 0–9 in development voids strictly held-out status, whether to re-seed or treat them as a fixed benchmark is an experimental governance choice. |
| **R5-CX-17** | Medium | Normative set has a single unambiguous precedence chain | **valid** | Contract v3.7, Interface v4, and Comparator v2 contain direct cross-referencing contradictions regarding interface versions and estimator IDs. |

---

## 2. Adjudication of Claude Opus Findings (R5-1 to R5-29)

| ID | Severity | Claim Attacked | Verdict | One Reason |
| :--- | :---: | :--- | :---: | :--- |
| **R5-1** | Critical | Contract §E4 Bitwise determinism across processes | **valid** | Replicated independently: Python's salted `hash(var)` produces divergent trajectories across processes unless `PYTHONHASHSEED=0` is externally forced. |
| **R5-2** | Critical | D-10.3 Comparator absent lower bound $\ge 0.85$ floor | **valid** | Replicated across all three reviews: 10/12 confirmatory cell-offsets fail, including all 4 base cells at primary offset 500. |
| **R5-3** | High | Score $q = \text{clip}(l - \|\sqrt{n}\text{mean}\tilde{r}\|)$ improves on baseline loading $l$ | **valid** | Decisive empirical demonstration: static loading $l$ alone achieves $\ge 0.987$ absent AUC, whereas subtracting the mean-shift term costs 0.12–0.27 AUC. |
| **R5-4** | High | Contract §G primary metric measures online sequential support recovery | **valid** | A static pre-event loading vector $l$ that never observes the event outranks both online arms because the task predominantly tests static reachability. |
| **R5-5** | High | Contract §D CL-4 support change is certified in generator and CSV | **valid** | Verified by all reviewers: `reference_generator.py` never checks CL-4, the CSV lacks `s_change_certified`, and 60%–70% of seeds exhibit zero support change. |
| **R5-6** | High | Gate mutation suite prevents uncertified generator behavior | **valid** | Confirmed by our independent mutants: multiple contract-violating generator mutations pass all 47 gate tests because only $\rho_{witness}$ binds. |
| **R5-7** | High | Contract §B Faithfulness: nonzero entries have $\|entry\| \ge c_{min} = 0.20$ | **valid** | Generator prunes at $0.5 \times c_{min} = 0.10$, so certified frozen seeds 1, 3, 4, 6, 7 contain non-faithful entries in $[0.10, 0.20)$. |
| **R5-8** | High | Contract §E1b label agreement post-event is enforced by the gate | **valid** | Soft actuator loss mutant R5-M7 breaks post-event reachability agreement between graph and numerical labels without triggering any gate failure. |
| **R5-9** | Medium | Contract §G co-primary P2 oracle mask correctness is policed by gate | **valid** | Identical to Gemini mutant R5-GM-M3: inverting `confounded_channels()` preserves cardinality under $f_{conf} = 0.5$ and passes all gate tests. |
| **R5-10** | Medium | Contract §C3 sensor gain and §B CRN stream separation are enforced | **valid** | Sensor gain scaling and variable-domain separation in `_noise` are unexercised by gate tests, allowing both features to be dropped without gate failure. |
| **R5-11** | High | Reference generator fulfills Contract §A0 scope across families and environments | **valid** | Identical to R5-CX-11: Family N and control-tier environments are missing from `reference_generator.py`, stranding 67% of confirmatory design rows. |
| **R5-12** | High | Demoted v1 comparator arm is excluded from confirmatory design | **valid** | Identical to R5-CX-07: `confirmation-design.csv` and `aggregate_primary` still explicitly bind to the legacy channel-agnostic comparator. |
| **R5-13** | High | Comparator-spec §2 diagnostic on `G_scale=0` is executable | **valid** | Direct execution of `draw_certified({"G_scale": 0}, 0)` crashes with `RuntimeError` because confounding witness $\rho_{witness}$ collapses without $G$. |
| **R5-14** | Medium | D-2a $n=400$ streams suffices for ARL_0 interval under step cap | **valid** | Run-length overdispersion and asymmetric 502-step warm-up deductions cause $n=400$ to fail interval width bounds or hit step caps unevenly. |
| **R5-15** | Medium | Comparator degeneracy ($q_{absent} = -41$) and clipping ($q_{cap} = 40$) are active | **valid** | Measured minimum channel standard deviation is 20–40x above the degeneracy threshold and maximum shift is 3.98, rendering both branches dead code. |
| **R5-16** | Medium | Symmetry of calibrator fitting protocol between arms | **valid** | Sequential IBD explicitly purges event-straddling windows from isotonic training, whereas the comparator specification omits this exclusion. |
| **R5-17** | Medium | Estimator RNG seeding and Arm 3 probe matching are specified | **valid** | Identical to R5-CX-14: Interface v4 lacks probe seed parameters, preventing verifiable replay of identical probe sequences in Arm 3. |
| **R5-18** | Medium | Sequential IBD §8 internal consistency on delay horizons | **valid** | §8 claims the detector maxes over $K$ cells under $\tau=2$, whereas §4 and §7 max over all $K \cdot \|\mathcal{H}\|$ cells because $\tau$ is unobserved. |
| **R5-19** | Medium | Internal consistency across normative documents | **valid** | Comprehensive catalog of discrepancies across P2 offsets, cited draft/interface versions, dead parameters, and unpoliced bounds. |
| **R5-20** | Medium | Predictor fitting key in comparator §1 omits instance seed | **valid** | Identical to R5-CX-06: Omitting seed from the fitting key creates ambiguity between per-instance regression and pooled cross-plant regression. |
| **R5-21** | Medium | Provisional constant $\lambda_{rel}$ has an outcome-dependent effect $> \delta_{AUC}$ | **valid** | Sweeping $\lambda_{rel}$ across orders of magnitude moves loading AUC by $>0.11$, demonstrating that a provisional constant exerts large outcome leverage. |
| **R5-22** | Medium | In-place mutation in `apply_event` corrupts multi-episode reuse | **valid** | `apply_event` permanently alters generator matrices without snapshot/restore, silently poisoning subsequent episodes with pre-existing faults. |
| **R5-23** | Low | Draft 4 §3 probe count of 100 on 0-indexed clock is inaccurate | **valid** | Identical to R5-GM-08 and R5-CX-12: An episode running $t \in [0, 1999]$ executes exactly 99 probes at multiples of 20 (fraction 0.0495). |
| **R5-24** | Low | T-IBD-blocks minimum sign assertion fails on prefix windows | **valid** | Partial windows during the initial 24 steps naturally have fewer than $n_{min\_sign} = 3$ samples, causing an unconditioned assertion to fail. |
| **R5-25** | Low | Parameter row 16 justification conflates residual cap with calibrator domain | **valid** | $z_{cap} = 8$ clips residuals, whereas the comparator calibrator domain is $[-40, 40] \cup \{-41\}$; the justification does not follow. |
| **R5-26** | Low | Paired offset evaluation lacks a uniform read convention for the comparator | **valid** | IBD defines offset reads at the latest closed epoch, while the comparator has no specified convention, creating timing offsets at $t=2000$. |
| **R5-27** | Low | Replications across distractor levels are treated as independent draws | **judgment call** | Coupling $N_x=10$ and $N_x=30$ to the same latent body draw is a standard matched-pair variance reduction design, though independence should not be claimed. |
| **R5-28** | Low | Generator certification uses abbreviated sample $T=4000$ instead of $T_{E2}=20000$ | **valid** | Shortened certification rollouts loosen statistical bounds and replace keyed witness pairs with unkeyed global maxima. |
| **R5-29** | Medium | Headline confounding benefit is driven by comparator collapse rather than IBD robustness | **valid** | Benefit decomposition proves that 85%–97% of the contrast is comparator degradation under confounding, while IBD AUC shifts by only +0.001 to +0.030. |

---

## 3. Cross-Model Consensus and Synthesis

### 3.1 Unanimous Tri-Model Agreement on Fatal Defects

All three independent reviews ([Gemini](file:///Users/danielfrazer/Documents/Personal/Persistent%20Adaptive%20AI/docs/archive/red-team/review5-gemini/findings.md), [Codex](file:///Users/danielfrazer/Documents/Personal/Persistent%20Adaptive%20AI/docs/archive/red-team/review5-codex/findings.md), and [Claude Opus](file:///Users/danielfrazer/Documents/Personal/Persistent%20Adaptive%20AI/docs/archive/red-team/review5-claude-opus/findings.md)) have converged on four critical system-level conclusions:

1. **D-10.3 Comparator Competence Floor Fails Universally:**
   - Decision D-10.3 requires the lower 95% confidence bound of the passive comparator AUC absent confounding to be $\ge 0.85$ at offset 500.
   - All three independent implementations found that the comparator **fails this binding requirement in every single confirmatory base cell**:
     - $N_x=10, \tau=0$: Gemini 0.810; Codex 0.824; Claude 0.829 (all $< 0.85$).
     - $N_x=10, \tau=2$: Gemini 0.710; Codex 0.767; Claude 0.774 (all $< 0.85$).
     - $N_x=30, \tau=0$: Gemini 0.813; Codex 0.822; Claude 0.829 (all $< 0.85$).
     - $N_x=30, \tau=2$: Gemini 0.710; Codex 0.765; Claude 0.772 (all $< 0.85$).
   - Under Contract §G, this triggers the mandatory stop rule: *"the comparator specification, not the rule, is defective and the phase stops."*

2. **Contract §D CL-4 Support-Change Failure:**
   - In `reference_generator.py`, `Instance.certify()` completely omits post-event support change verification.
   - On 60%–70% of certified seeds, complete actuator 0 loss produces **zero change** in observable reachability $S^{obs,\varepsilon}$.
   - Evaluating actuator fault detection on instances where the fault induces zero reachability change fundamentally invalidates the empirical estimand.

3. **Cross-Process Non-Determinism in Generator:**
   - `reference_generator._noise()` hashes variable names using Python's built-in `hash(var) & 0xffff`.
   - Because Python salts string hashes per process launch, trajectories generated from the exact same seed diverge across independent process invocations unless `PYTHONHASHSEED=0` is set externally.

4. **Mutation Escapes in Reference Generator:**
   - Multiple distinct mutants of `reference_generator.py` (faithfulness bound $c_{min}$ pruning, co-primary P2 oracle inversion, CRN variable key omission) survive all 47 gate tests without failure.

### 3.2 Key Mechanistic Insight: Baseline Loading Dominance

Claude Opus's finding **R5-3** provides the mathematical explanation for the failure of D-10.3:
- In `comparator-spec.md` v2, the score $q = \text{clip}(l - \|\sqrt{n}\text{mean}\tilde{r}\|)$ subtracts a noisy windowed residual mean shift from the static pre-event loading vector $l$.
- Offline static loading $l$ alone achieves $\ge 0.987$ AUC absent across all cells. Subtracting the mean shift term degrades ranking accuracy by $0.12$–$0.27$ AUC, directly causing the D-10.3 failure.
- Furthermore (finding **R5-29**), 85%–97% of the measured confounding benefit $[\Delta_{pres} - \Delta_{abs}]$ is driven by the comparator degrading under confounding, while the interventional IBD arm's AUC remains virtually unchanged between present and absent (+0.001 to +0.030).

### 3.3 Exit Condition Assessment

The proposed exit condition for design review (three independent models agreeing to Monte Carlo error on one frozen generator) is **NOT MET**:
1. Cross-process hash salting introduces variance across different environments.
2. Open specification ambiguities (probe RNG lifecycle, per-instance vs. pooled predictor fitting, observation clock endpoints) caused implementation choices to diverge.
3. Substantively, the phase cannot exit because the D-10.3 prerequisite has failed, halting confirmatory execution under Contract §G.
