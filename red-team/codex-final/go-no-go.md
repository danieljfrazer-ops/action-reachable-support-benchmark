# Go/no-go

## **GO WITH CHANGES**

Roadmap v3 is the right plan, but code should not begin from the current Stage 0A contract. Four changes are blocking:

1. **Repair the estimands.** Separate latent support from observation-channel support; specify nonlinear, horizon-dependent `M`; split sensor assignment, gain and availability in `P`; and define how copied sensors are scored.
2. **Make the interface and gates match the paper.** Either narrow Paper 1 to support/change detection or require outputs and non-optional metrics for all three targets. Replace statistical “proofs” of graph properties with an independent structural oracle, paired intervention tests, tolerances and mutant generators.
3. **Freeze the confirmation design now.** Name the exact primary method pair and scalar operating-curve estimand, give the SOEI units/value, publish the fractional run matrix and alias structure, and rewrite the signed CI kill/futility rules.
4. **Reduce Phase S or extend it.** A two-week box is credible for three representative memory families and a decision-quality internal report. The five-family combinatorial study plus publishable write-up needs roughly four to six weeks. Use physical bytes and operations as primary budgets.

**Single first action:** revise `stage-0a-contract-draft.md` into a versioned executable specification containing explicit SCM equations and two coordinate systems—`S^latent` and `S^obs`—then hand-derive one sensor-swap example. Do not scaffold the generator until that example makes every target, invariant and metric agree.

**Opinion:** with those changes, Paper 1 is a credible benchmark/failure-map project for arXiv-first release and later workshop/CoLLAs submission. Without them, the first pilot is likely to expose an evaluator contradiction and force a costly rewrite.
