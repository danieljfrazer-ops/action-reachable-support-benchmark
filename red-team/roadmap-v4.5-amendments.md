# Roadmap v4.5: decisions D-6 (b), D-7 (a), D-8 (a) applied; cross-model review re-instated

Date: 7 September 2026.

## I1. Primary estimand re-aimed (D-8a; amends D8, D11, v4 §4, v4.1 E1/E2/E4, v4.4 H1/H3)
Paper 1's primary outcomes are support correctness (per-channel F1 against S^obs,ε at offsets {200, 500, 1000}, primary 500) and confounded-channel false support, co-equal and hierarchical. HPDT is descriptive: the speed cost of causal identification. Decision rules, effect sizes (δ_F1 = 0.10, δ0_F1 = 0.05, provisional until the pilot power arm) and the interaction gate are restated for Δ_F1 in contract G. Working claim: passive residual monitors detect body change fast but attribute control wrongly under a shared-cause confounder; interventional estimators attribute correctly at a measurable cost in speed and probes; the benchmark quantifies that trade-off across regimes.

## I2. False-alarm control (D-6b)
Episodes stay at 2,000 steps with the event at 1,000. ARL_0 is the fresh-start run length to first alarm. It governs the alarm channel and the descriptive HPDT only.

## I3. Third arm (D-7a)
`cusum_linear_probed` added to the confirmation matrix (720 rows plus calibration rows). Arm 2 vs 1 is the headline; arm 3 vs 1 the mechanism control.

## I4. Sequential IBD spec, draft 2
Redrafted by a fresh-context agent under D-8a and contract v3.3 (windowed many-sample statistic; support estimation primary; alarm secondary; fixes IB-1 to IB-11). Reviewed in the cross-model round below, not by Claude-family agents alone.

## I5. Process correction (Daniel, 7 Sep)
Since round 2, repairs, the D-6 to D-8 analysis, and the IBD spec draft and review were done by Claude-family agents only. That violates the protocol's purpose. Rule added: **no design change is applied to a frozen version without a cross-model round, and any decision whose basis is a single-family simulation is flagged as unverified until another model has attempted to refute it.** D-8's basis (`review-ibd-spec/sim_ibd_review.py`) is so flagged. The prose-round cap is set aside for one **design re-baseline round** because D-8 changed what is measured; the round reviews the frozen set including the redrafted spec, and each reviewer is asked to refute the D-8 simulation with its own.

## Normative set after this file
`roadmap-v4.md` + amendments v4.1 to v4.5; `stage-0a-contract-v3.3.md`; `interface-spec-v3.md`; `sequential-ibd-spec.md` (draft 2); `confirmation-design.csv`; `executable-proofs/gate/`.
