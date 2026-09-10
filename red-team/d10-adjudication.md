# D-10 adjudication (7 September 2026)

Inputs: `review-d10-codex/verdict.md`, `review-d10-gemini/verdict.md` (reasoning only, no code, per the brief), and the author's recommendations. Three-of-three adopt on every part; stated changes integrated below. No dissent requires Daniel.

| Part | Codex | Gemini | Author | Integrated decision |
|---|---|---|---|---|
| D-10.1 generator as code | adopt + freeze a small distribution of configurations, not one instance | adopt | adopt | **Adopt.** The reference generator draws instances from a seeded configuration family; the frozen set is a declared list of configuration seeds plus a bounded perturbation set over coupling strength and noise scale (Gemini (a)). |
| D-10.2 comparator capacity | adopt + define multi-horizon loading mathematically before simulation; keep the old comparator's results as an audit trail | adopt | adopt with consequence stated | **Adopt.** Comparator spec v2 defines the loading; the round-4 comparator is retained as a labelled legacy arm in the appendix, never in confirmation. |
| D-10.3 competence floor | adopt + apply per environment and distractor level with uncertainty, not after aggregation | adopt | adopt | **Adopt** per cell: lower 95 percent bound of comparator AUC(absent) ≥ 0.85 in every required cell. |
| D-10.4 balanced blocks | adopt | adopt | adopt | **Adopt.** |
| D-10.5 offsets | adopt + keep 200 labelled as a transition-window outcome | adopt | adopt | **Adopt**; 200 reported as "transition window (about 60 percent pre-event for the interventional arm)". |
| D-10.6 no copies | adopt; fixtures use distributional tolerances | adopt | adopt | **Adopt.** |
| D-10.7 replication | adopt + instance-by-episode hierarchy predefined; power on instances | adopt + floor of 20 instances if the margin is near 0.10 | adopt | **Adopt.** 10 instances × 4 episodes by default; the pilot power simulation scales instances first (floor 20 if the estimated margin is within 0.05 of δ); intervals clustered by instance. |

Questions. (a) Exit condition amended: agreement to Monte Carlo error across the frozen configuration set and the perturbation set, plus specification-conformance tests, not a single realisation. (b) Both say either fallback is publishable; they prefer different ones (Codex the negative result as broader; Gemini the indirect/downstream claim as affirmative). Recorded as a judgment for Daniel only if the fallback is needed after round 5. (c) Both say D-10.2 (and, per Codex, D-10.3/4/5/7) change what is measured and must pass an execution round before freezing. Agreed; that is round 5.
