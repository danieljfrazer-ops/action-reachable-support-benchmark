# Round-5 cross-review adjudication — Codex

**Date:** 7 September 2026. **Frozen version:** `0468104f6431b050`.  
I wrote `review5-codex/findings.md` before reading peer findings. At adjudication time, `review5-gemini/findings.md` was present; no second peer `review5-*/findings.md` was present. I will not infer findings from Gemini's references to another review that is not available as an artefact.

## Gemini findings

| Finding | Verdict | One reason |
|---|---|---|
| R5-GM-01 | **valid** | Direct execution agrees: `certify()` never checks the planned loss and only 3/10 τ=0 and 4/10 τ=2 draws change `S^obs,ε`, violating CL-4. |
| R5-GM-02 | **invalid** | The alleged omission of closed-loop feedback attacks a different estimand: comparator §2 explicitly defines an open-loop fitted-model sensitivity with later actions zero, matching contract C2/C4, and expressly disclaims a causal/closed-loop Jacobian. Multicollinearity can hurt empirical competence, but does not make this recurrence internally wrong. |
| R5-GM-03 | **valid** | Both independent reproductions put the comparator-absent 95% lower bound below 0.85 in every primary base cell, which triggers the contract's stated stop rule. |
| R5-GM-04 | **valid** | The three mutants target real uncovered properties: the `c_min` bound, correctness (not just cardinality) of the confounded mask, and variable-domain separation of keyed noise. The suggested `c_min` assertion should cover `A_b` and `B`; adding `C_d` would exceed contract B as written. |
| R5-GM-05 | **valid** | Draft 4 itself requires longer event-free calibration streams; 2,000-step event episodes cannot supply 400 uncensored conditional run lengths near 1,000 after a 502-step prefix. The stronger unresolved issue is that excluding the prefix also conflicts with the contract's fresh-start clock. |
| R5-GM-06 | **invalid** | Draft 4 explicitly does **not** claim independent units or exact rank-sum level and uses `|z|` as a ranking score, not a p-value. The proposed settling-time objection therefore attacks a disclaimed guarantee; it also misstates `0.98^20≈0.668` as leaving only ≈33% residual. |
| R5-GM-07 | **invalid** | With the adopted K=2 balanced blocks, every full 25-unit window has 5–7 observations per `(k,sign)` group, so the insufficient-count fallback cannot occur after warm-up; true tie degeneracy is separately flagged by the returned mask. |
| R5-GM-08 | **valid** | A 2,000-step `Instance.run` accepts action indices 0…1999, so the draft's t=2000 terminal grant is unrepresentable and the literal 20,…,1980 schedule applies 99 probes. |
| R5-GM-09 | **valid** | Python's salted `hash(var)` makes otherwise identical generator runs differ across processes; my two-process SHA-256 check independently reproduced it. |

## Cross-review consistency check

The D-10 exit condition is **not met**. Even where the qualitative verdict converges, fixed-cell values do not agree to Monte Carlo error: on the seed-0 `(coupling=1, noise=1, N_x=10, τ=0)` perturbation at offset 500, Codex obtained IBD/comparator present AUC `0.962/0.825`, while Gemini reports `0.784/0.762`; absent values were `0.960/0.925` versus `0.784/0.833`. The unspecified probe RNG, fit/episode seed allocation, and generator's process-salted noise key are plausible sources; this is an inference, not a proven decomposition.

## Peer availability

No other peer findings file was present when this adjudication was written. If one appears later, this file should be extended rather than treating second-hand numbers or summaries as its findings.
