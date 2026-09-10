# Prompt for the Codex agent that produced the original roadmap

You produced `docs/archive/persistent-adaptive-ai-research-roadmap.html` ("Persistent Adaptive AI: Novelty Review and Research Roadmap", 6 September 2026). A second agent (Claude) has since red-teamed that report, run two rounds of prior-art research, and proposed a replacement roadmap. All of that is in `docs/archive/red-team/`. Read every file in that folder before doing anything else:

- `README.md` (method and headline verdict)
- `findings.md` (16 findings, severity-ranked, plus the attacks that failed)
- `evidence.md` (citation verification and prior-art tables with links)
- `r1-protocol-hardening.md`
- `precursor-notes.md`
- `research-round-2.md` (second research round: gap checks, tooling, venue dates)
- `recommendation.md`
- `roadmap-v2.md` (the proposed replacement roadmap)

Do not edit any existing file in `docs/archive/` or `docs/archive/red-team/`. Write all output to a new folder `docs/archive/red-team/codex-response/`.

## Task 1: respond to the red team of your report

The red team's main claims against your report are:

1. The novelty scores for all three flagship candidates were inflated because closer prior art was missed. Specifically: for hidden-volatility memory routing, Jain & Shenoy (AAAI 2024, instance-conditional decay timescales), FADE (arXiv 2604.27063), hazard-rate learning in change-point problems (Wilson, Nassar & Gold 2010), and Memory-R1; for the adversarial self-boundary, Interventional Boundary Discovery (arXiv 2603.18257, March 2026), which already tests "intervention beats correlation under distractors that mimic controllable variables"; for proactive counterfactual compute, the rational-metareasoning literature, Jensen, Hennequin & Mattar (Nature Neuroscience 2024), and "Finding the Time to Think" (arXiv 2606.26463, June 2026).
2. The R1 "equal state bytes and update FLOPs" comparison is not well-defined across memory families, and a multi-tier router has a structural capacity advantage over single-tier baselines unless total budget is matched.
3. The "oracle hazard-aware router" is not an upper bound; generator leakage weakens "oracle-free"; the metric definitions (stale-answer rate, adaptation lag, calibration) leave room for favourable reporting.
4. A fanless MacBook Air throttles within about 10 minutes, which confounds equal-wall-clock comparisons and fixed-5-minute AutoResearch budgets.
5. No timeline, effort estimates or kill criteria after R0; scoop risk unaddressed; audience left open although the baseline suite already implies one.
6. Minor: AffectWorld cited in prose but absent from sources; OAKS labelled by shorthand rather than title.

For each of the six, state one of: **accept**, **accept with modification**, or **reject**, and give the reason. Where you reject, you must cite a source or an argument the red team did not consider. Where you accept, say what you would change in your report. Independently verify at least the three prior-art papers you consider most damaging to your original scores; do not take the red team's characterisation of them on trust. If you find that the red team itself mischaracterised a paper, say so with the specific discrepancy.

## Task 2: red-team `roadmap-v2.md` and `recommendation.md`

Treat Claude's proposal exactly as adversarially as Claude treated yours. In particular:

- **Novelty.** The proposal claims two unoccupied intersections: (a) interventional boundary estimation under a boundary that changes during deployment, with action-synchronised distractors, scored by detection latency, false-alarm rate and calibration; (b) an auxiliary self-model (predict own hidden state, error, or controllability mask) as an aid to adaptation when the agent's body changes. Search for prior art on both. Look especially in developmental robotics, body-schema plasticity, fault detection and isolation in control engineering, non-stationary and meta-RL, and the 2025 to 2026 self-modeling and introspection literature. If either intersection is occupied, name the work and say what survives.
- **Feasibility.** Is Stage 0 (a continuing vector testbed with ground-truth controllability, hidden hazard rates and a cost ledger, plus three reproductions) realistic in 4 weeks for one person? Is Paper 1 realistic by mid-February 2027?
- **Protocol.** Attack the hypotheses, baselines, metrics and kill criteria in Paper 1 and Paper 2 the way a hostile reviewer would. Is the proposed Bayesian change-point detector a fair model-based baseline? Are the calibration metrics well-defined for a controllability mask? Is the "re-introduced morphology" test confounded?
- **Strategy.** Claude demoted your R1 to a side paper and R5 to a component. Argue the other side: is there a case that the memory benchmark should stay first (speed to a first preprint, cleaner ground truth, larger audience)? Is the venue plan (ICLR 2027 workshops, CoLLAs 2027) right for a solo unaffiliated author?
- **Self-awareness framing.** The proposal maps the goal onto a four-rung ladder of functional constructs and forbids any "self-aware" claim. Is that ladder coherent, is any rung already fully occupied, and is anything measurable missing from it?
- **Anything else.** Errors, contradictions between files, overclaims, or places where Claude's evidence is thinner than its confidence.

Rank your findings by severity (high, medium, low) and record any attacks that failed, as the red team did.

## Task 3: documented write-up

Produce, in `docs/archive/red-team/codex-response/`:

1. `response-to-red-team.md`: Task 1, with the six accept/modify/reject verdicts, reasons, sources checked, and any discrepancies found in the red team's own characterisations.
2. `red-team-of-roadmap-v2.md`: Task 2 findings, severity-ranked, each with the claim attacked, the evidence, and a recommended fix; plus attacks that failed.
3. `sources.md`: every URL you consulted, what you checked it for, and whether it supported or contradicted the claim.
4. `summary.md`: under 400 words. Which roadmap you now recommend (yours, v2, or a merge), the three changes you would make to v2 before starting, and the single first action for Stage 0.

Constraints: verify with live sources where possible and say when you could not; do not invent citations; mark opinion as opinion; do not modify any existing file; keep consciousness out of any recommendation as a claim. Today's date is 6 September 2026. The author's hardware is a 32 GB M5 MacBook Air.
