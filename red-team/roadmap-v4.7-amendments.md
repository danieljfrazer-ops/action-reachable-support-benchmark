# Roadmap v4.7: D-9 adopted as adjudicated

Date: 7 September 2026. Basis: `d9-adjudication.md` (two-model verification of D-9.1; convergent changes to D-9.2 to D-9.5).

## K1. Primary and rules
Contract v3.5 section G: online support ranking (AUC) primary at offset 500; AUPRC co-reported with prevalence lift and a grouped sensitivity; supervised calibration tier secondary with separate fit and validation splits; decision rules on the within-regime confounding contrast with R0-present positive control and R0-absent equivalence (±0.05 AUC). Pilot-informed freeze disclosed.

## K2. Arms
Sequential IBD = sign-randomised contrast (draft 3 pending); passive comparator frozen on principle as the strongest passive reading with a normative `comparator-spec.md` (pending); probed comparator calibrated separately.

## K3. Confirmation matrix
`ranking_metric=AUC`, `secondary=AUPRC|F1_at_validated_op`, `cal_split=24|16`; regenerated.

## K4. Working claim (restated)
Passive residual monitors detect body change quickly but attribute control wrongly under a shared-cause confounder; a sign-randomised interventional estimator ranks the controllable support correctly at a 5 percent probe budget, insensitive to the confounder, at a measurable cost in alarm speed. The benchmark quantifies that trade-off across regimes and distractor levels, and reports the probed passive comparator to show that the gain comes from using the randomisation causally, not from having it.

## K5. Next
Fresh-context agents draft `comparator-spec.md` and `sequential-ibd-spec.md` draft 3 from contract v3.5; cross-model review of both (round 4); freeze version 4; Stage 0A.
