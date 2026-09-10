# Roadmap v4.2: amendments after round 2 (safe corrections only; design decisions are in `decisions-required.md`)

Date: 6 September 2026. Applies convergent, low-risk findings from round 2. No new design content: anything that changes what is measured waits for Daniel's decisions D-1 to D-5.

## F1. Normative file list (FB-16, CX-02, GM2-9)
Roadmap v4 §1's list is replaced by: `roadmap-v4.md` + `roadmap-v4.1-amendments.md` + this file; `stage-0a-contract-v3.1.md` as amended here; `interface-spec-v2.md` as amended here; `confirmation-design.csv`; `executable-proofs/gate/`. Contract E6 and J read "`interface-spec-v2.md`". Every "RMDT" in v4 §3 and §4 reads "HPDT (contract G)". A freeze manifest (`freeze-manifest.txt`) lists the hashed files in order and includes the coverage matrix, requirements and the proof-theatre test (FB-19).

## F2. Registry corrections (CX-09, GM2-11, CX-10)
ε_faith = ε = 0.05. "Daniel may change" and "pending Daniel" are removed from contract §0 and §G; f_conf = 0.5 and the co-primary are locked unless D-5 says otherwise. requirements are pinned exactly: numpy==2.4.4, pytest==8.3.5, Python 3.12.x (CX-08, GM2-8).

## F3. Interface additions (FB-9, FB-23)
`configure(regime_bundle)` (the only privileged input: hashed residual-model parameters for the declared regime, or None), `calibrate(transitions) -> None`, `set_threshold(h)`. Reward, terminated and truncated are removed from the estimator-facing Transition unless the information set declares "reward visible".

## F4. Reference implementations (FB-12, CX-12, GM2-7)
`aggregate_primary` now exists and is tested. ARL_0 calibration, Brier, log loss, F1 at offsets and alarm bookkeeping (p, r, w_T) are 0A deliverables and listed as uncovered in the coverage matrix; the interface spec no longer calls them existing.

## F5. Alarm matching (FB-20)
Detection = first counted alarm with event_t < alarm_t ≤ event_t + H_det. w_T is used only to match alarms to the nearest event when several exist. The "merge events closer than w_T" rule is deleted (unreachable under event_spacing).

## F6. Roles in the confirmation matrix (CX-06, GM2-5)
Rows carry `role ∈ {confirmatory_effect, confirmatory_interaction, descriptive}`; the interaction I consumes the four (regime × confounder) cells of the confirmatory pair via a frozen selector in `aggregate_primary`'s companion `select_interaction_cells`. Regenerated only after the generator exists so `s_change_certified` is real (FB-11); the CSV also gains `schedule`, `episode_len`, `event_t`, `n_events`, `H`, `tau`.

## F7. Definitions missing from the contract (FB-11)
`distractor_level` = number of distractor channels N_x. "Confounder absent" = G = 0 with W_u unchanged and identical seeds, so the policy's u-dependence is held fixed and only the u → x path is removed. Schedule for confirmation = single unannounced change at event_t = 1,000 in an episode of 2,000 steps; n_events = 1 per run (HPDT is then per run; seeds supply replication).

## F8. Co-primary (CX-07, GM2-6, FB-18)
Defined on oracle-labelled confounded distractor channels only; unconfounded distractors reported as a negative control; per-offset values reported with the fraction of runs for which the offset exists; the CUSUM-to-p_c and IBD-to-p_c mappings are frozen as isotonic calibrators fitted on the calibration split.

## F9. Statistical tests and power (FB-15, FB-14, FB-24)
T ≥ 20,000 for T-E2c and T-E2d. Pilot gate: estimate the SD of per-seed paired differences; require power ≥ 0.8 at Δ = 2δ, otherwise raise seeds (to 20) before confirmation; report the achieved minimum detectable effect. Secondary bootstrap: restricted wild cluster bootstrap with Webb six-point weights, 9,999 draws.

## F10. Calibration sharing (FB-21)
ARL_0 calibration is performed once per (environment, regime, confounder, estimator) cell on the calibration split and shared across seeds; the calibration budget is charged once per cell.

## F11. Closed-loop stability (FB-17, CX-03, GM2-3)
Certified on the delay-augmented state [b_t, …, b_{t−τ}; d; a-queue] with the policy's actual observed channels, at sampling and after every event; family N empirically. Test in 0A.

## F12. R0 rule wording (FB-25)
One-sided as intended; a lower bound < −δ is flagged "probing cost dominates in clean conditions".

## Not amended here (awaiting decisions)
T2 environment (D-1); calibration precision rule and exclusion (D-2); comparator identity (D-3); sequential IBD specification (D-4); locking the two defaults (D-5).
