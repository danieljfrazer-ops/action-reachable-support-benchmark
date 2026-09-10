### P1 — Dropped qualifier in the Abstract: ordering reversal on the nonlinear family

`docs/report/technical-report.md:14`

```markdown
On the separate task of ranking which controlled channel an actuator loss removed, a passive delay-aware covariance monitor equalled or beat the probed estimator in every linear-family cell. The two endpoints were measured on different channel sets under different effective confounding regimes and do not establish a dissociation.
```

Draft 11 completely drops the finding that the ordering reversed on the nonlinear family from the abstract. In draft 10's abstract, this was explicitly stated: "and the ordering reversed on the one nonlinear family, on five seeds." Dropping this qualifier makes the summary of the adaptation result more positive than the body of the report supports. Restore the qualifier regarding the nonlinear family.

### P1 — Dropped qualifier and changed attribution: single-model red team

`docs/report/technical-report.md:20`

```markdown
Liu, Cheng and Bogdan (2026) showed that randomising actions recovers the controllable boundary in the static case, including under distractors that mimic controllable variables, and proved the estimator's invariance to confounders.
```

Draft 11 drops the "single-model" qualifier and changes the attribution. Draft 10 stated that a "single-model red team of that roadmap ... found that the central hypothesis ... had already been tested and confirmed by Liu, Cheng and Bogdan". Draft 11 presents this as if the author directly cites Liu, Cheng and Bogdan, omitting the red team's role and the unverified single-model nature of that initial finding. Restore the attribution to the single-model red team.

### P2 — Dropped cross-reference to the error log in Figure 1 caption

`docs/report/technical-report.md:32`

```markdown
Figure 1. The plant of the frozen generator (family L). Solid edges are the structural equations; the dashed grey edge is the policy's feedback from the body channels; the action noise entering a is the instrument that Section 3.3 relies on. The context u reaches the observation layer only through the confounded half of the distractors, so the pre-event support (b and d channels; b alone at delay 2) and the confounded channels are disjoint, which is why Experiment 2's confounding benefit was zero by construction. The dashed red edge G_b exists only in the body-confounded plant analysed in Section 3.3 and was never built. Source: `figures/make_figures.py`, checked against the contract's structural equations.
```

In draft 10, the caption ended the sentence describing disjoint channels with "which is the mechanism of the third error in Section 6". Draft 11 replaces this with "which is why Experiment 2's confounding benefit was zero by construction", completely dropping the cross-reference to the error log (now Appendix B). The text should point the reader to the error log for full context. Change the end of the sentence to "...which is the mechanism of error 3 in Appendix B."

### P2 — Dropped erratum reference and numbers in adaptation result

`docs/report/technical-report.md:107`

```markdown
The confounding effect was still visible, but only in the secondary full-channel measure: the comparator's static loading ranked confounded distractors as controlled, scoring 0.73 to 0.80 with the confounder present against 0.96 to 0.98 without it, while the interventional arm scored 0.75 to 0.87 across the four base cells and moved by at most 0.013 between conditions. These secondary numbers are from two of the three implementations; the third's secondary read was found to be taken at the wrong step and was excluded.
```

Draft 11 completely drops the parenthetical `(the round-6 adjudication's earlier figure of 0.85 to 0.87 was a delay-0 read, corrected by erratum)` that was present in draft 10. This deletes specific numbers (0.85 to 0.87) and a cross-reference to an erratum correction, which is important context for how the `0.75 to 0.87` figure was revised. Restore the parenthetical to accurately reflect the erratum.

### P2 — Number dropped: scores for the body-confounded plant

`docs/report/technical-report.md:136`

```markdown
Table 3. Population-limit response to a support-preserving change in the confounder's coupling, in G_b or in the policy's context gain W_u, by plant and arm. Derived by three systems and reconciled in adjudication, one having initially concluded the opposite on the identifiability question. The table covers a confounder-coupling change only. The response to an actual actuator loss under body confounding was not settled: one system predicted the passive arm still wins, one predicted the probe arm wins, and one said the sign is not determined without further inequalities. One of the three made the referee's obvious rebuttal, why not fit a state-space model with the confounder as a latent AR(1), a design requirement, and proposed answering it with a deconfounded passive third arm.
```

Table 3 in draft 11 (formerly Table 5) drops the sentence "Two of the three rescored the body-confounded plant at 3, the same as the repaired benchmark paper, and the third reframed what is unoccupied about it as body confounding plus a restricted estimator". This drops a specific numerical finding from the derivation round. Restore the sentence describing how the systems scored the plant.

### P3 — Machine-sounding transition paragraph in the Introduction

`docs/report/technical-report.md:22`

```markdown
The contribution is a negative result with a reusable testbed. Two experiments and one analysis, each verified by three independent implementations or derivations, show that the claim is unsupported on the testbed built to confirm it: its attribution half is IBD's result in an online form, and its adaptation half was never tested under confounding on the channels the primary scored, because the one design that put confounding and change together did so on channels the confounder could not reach. Section 2 describes the testbed and the two estimators, Section 3 the experiments and the analysis, Section 4 what the results support, Section 5 the limitations. The verification protocol and the errors it caught are in the appendices; every number in the report traces to an archived file.
```

The sentence "Section 2 describes the testbed and the two estimators, Section 3 the experiments and the analysis, Section 4 what the results support, Section 5 the limitations." is a classic machine-generated formulaic outline that was absent in draft 10. Given the prompt's instruction to flag machine-sounding sentences, this stands out as artificially generated filler. Remove or rewrite this sentence to be less mechanical.
