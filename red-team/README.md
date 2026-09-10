# Red Team: "Persistent Adaptive AI: Novelty Review and Research Roadmap"

**Target document:** `../persistent-adaptive-ai-research-roadmap.html` (and its `.artifact.json` manifest), generated 6 September 2026.
**Red team date:** 6 September 2026.
**Reviewer:** Claude (Fable 5.1), acting as an adversarial reviewer on request of Daniel Frazer.
**Stance:** assume the roadmap is wrong and try to show it. Findings are only kept where evidence was found; where an attack failed, that is recorded too.

## What was done

1. Extracted the full prose of the report from the HTML and the manifest.
2. Verified every non-trivial citation resolves to the claimed work (22 sources, plus one uncited work named in the prose).
3. Ran prior-art searches against each of the three "strongest" candidates (R1 hidden-volatility memory, R2 adversarial self-boundary, R5 proactive counterfactual compute) looking for work the report did not find.
4. Attacked the first-paper protocol (R1) as a hostile reviewer would: budget matching, oracle definition, generator leakage, metric definitions, hardware confounds.
5. Checked the factual claims about Karpathy's AutoResearch and the MLX port.
6. Read the two precursor chat transcripts in `../` to see which motivating assumptions leak into the roadmap.

## Headline verdict

The report is well constructed and unusually honest about scope. Its citations hold. Its strongest practical advice (freeze protocol, multi-seed, locked evaluator, AutoResearch only after protocol) survives attack.

Its novelty scores do not. All three flagship candidates have closer precedents than the report's "closest occupied territory" column names:

| Candidate | Report novelty score | Red-team view | Closest precedent the report missed |
|---|---|---|---|
| Hidden-volatility memory routing (R1) | 4.5 | ~3.0 | Instance-conditional timescales of decay (AAAI 2024); FADE per-parameter adaptive decay (Apr 2026); hazard-rate learning in change-point problems (Wilson, Nassar & Gold 2010); Memory-R1 learned memory ops |
| Adversarial causal self-boundary (R2) | 4.5 | ~3.0 | Interventional Boundary Discovery (Mar 2026): interventional control-mask discovery with up to 100 distractors that mimic controllable variables, beating MI and forward-model baselines. This is R2's primary hypothesis, already tested. |
| Proactive counterfactual compute (R5) | 4.0 | ~2.5 | Rational metareasoning / value of computation (1991 onward); Jensen, Hennequin & Mattar 2024 trains an agent that learns when to roll out versus act under a time cost. Report names CTM and "proactive LLM agents" as neighbours, which is the wrong neighbourhood. |

The defensible gaps still exist but are narrower: budget-matched multi-tier comparison with a phase diagram (R1); a boundary that *changes over time* with calibration scoring (R2); scheduling under a continuing world with missed-event costs (R5). The roadmap should be re-scored and the R1 and R2 hypotheses re-worded so they are not replications.

The single most dangerous protocol flaw is that the R1 "equal budget" comparison is not well-defined across memory families, and a four-tier router trivially wins against any single-tier baseline unless total capacity is matched. See finding F4.

## Files

- [findings.md](findings.md): numbered findings ranked by severity, each with evidence, the attack, and a recommended fix.
- [evidence.md](evidence.md): citation verification table and prior-art table with links.
- [r1-protocol-hardening.md](r1-protocol-hardening.md): concrete changes to the first-paper protocol that close the holes found.
- [precursor-notes.md](precursor-notes.md): assumptions in the two archived chat transcripts that the roadmap inherits or should explicitly disown.

## Severity key

- **High**: would cause a rejection or a retracted claim if not fixed.
- **Medium**: weakens the contribution or invites an easy reviewer objection.
- **Low**: hygiene, presentation, or minor inconsistency.

## Follow-up (same day): recommendation and revised roadmap

After the red team, a second research round checked whether the reframed projects still have open ground, and produced a recommendation and a proposed roadmap. The original report is unchanged.

- [recommendation.md](recommendation.md): is there a programme here, what shape, what changed, decisions the author must make.
- [roadmap-v2.md](roadmap-v2.md): proposed replacement for R0 to R6 with hypotheses, baselines, metrics, kill criteria, timeline and venues.
- [research-round-2.md](research-round-2.md): evidence for the round-2 gap checks, tooling and venue dates.

## Codex response and synthesis (same day)

- `codex-response/`: the original roadmap author's response to the red team and its red team of roadmap-v2 (four files, written by Codex).
- [synthesis.md](synthesis.md): Claude's assessment of the Codex response, concessions, merged plan, and open decisions.
- [stage-0a-contract-draft.md](stage-0a-contract-draft.md): draft structural-causal environment contract, the first build artefact.

## Pre-execution plan

- [timing-and-shakedown-value.md](timing-and-shakedown-value.md): basis of the timings, revised agentic estimates, value of the memory shakedown.
- [roadmap-v3.md](roadmap-v3.md): consolidated roadmap and phase plan for execution (supersedes v2).
- [prompt-for-codex-final.md](prompt-for-codex-final.md): prompt for the final Codex critique; its output goes to `codex-final/`.

## Final critique and execution-ready spec

- `codex-final/`: Codex's final critique of roadmap-v3 (go with changes, four blocking).
- [synthesis-final.md](synthesis-final.md): disposition of every finding in the final critique.
- [stage-0a-contract-v2.md](stage-0a-contract-v2.md): repaired, executable environment contract with explicit equations, two coordinate systems and the hand-derived sensor-swap example. **This is what gets built first.**
- [roadmap-v3.1-amendments.md](roadmap-v3.1-amendments.md): amendments to roadmap-v3 (timings, frozen design, decision rules, change control, reduced Phase S).

## Gemini red team and response

- `gemini-v3.1/`: Gemini's independent review of roadmap-v3 and v3.1 (conditional go; four mathematical blockers; strategic "triviality trap" finding).
- `executable-proofs/`: scripts that execute the contract's equations. `gemini_checks.py` confirms G1, G2, G3 numerically; output in `gemini_checks.output.txt`.
- [gemini-assessment.md](gemini-assessment.md): disposition of G1 to G10 with the executed checks; answers on the maths and the laptop.
- [benchmark-proposal.md](benchmark-proposal.md): the three-tier benchmark suite, models to run against it, prior art, feasibility.
- [stage-0a-contract-v2.1.md](stage-0a-contract-v2.1.md): patched contract (open-loop R, piecewise M, randomised severing test, faithfulness margin, Paper 1 scoring restricted). **This is what gets built.**
- [roadmap-v3.2-amendments.md](roadmap-v3.2-amendments.md): pAUC estimand, re-aimed primary contrast, benchmark-shaped Paper 1, world-model Paper 2, Phase S internal, serialisation, executable-proof rule, dates.

## Second Gemini red team and response

- `gemini-v3.2/`: Gemini's follow-up review (conditional go; scope explosion; coupling breaks T2 ground truth; classical FDI dominates in clean regimes; discrete pAUC; one contract contradiction).
- `executable-proofs/gemini_v32_checks.py`: numerical demonstrations of H1 (coupling) and H3 (discrete Pareto estimand).
- [gemini-v3.2-assessment.md](gemini-v3.2-assessment.md): disposition of H1 to H8.
- [stage-0a-contract-v2.2.md](stage-0a-contract-v2.2.md): contradiction removed, coupling note added. **Build target.**
- [roadmap-v3.3-amendments.md](roadmap-v3.3-amendments.md): discrete estimand, three-regime primary contrast, T2 fenced to single-actuator systems, five baselines, four environments, schedule. **Execution plan.**

## Third Gemini red team: planning closed

- `gemini-v3.3/`: unconditional go for Stage 0A; two non-blocking harmonisations (I1 regime decision rules, I2 disjoint-support float).
- [gemini-v3.3-assessment.md](gemini-v3.3-assessment.md): disposition.
- [roadmap-v3.4-amendments.md](roadmap-v3.4-amendments.md): decision rules by regime; I2 applied; expectation note. **Planning closed. Build target remains `stage-0a-contract-v2.2.md`.**

## Codex red team of v3.4 and consolidation (planning re-opened, then re-closed)

- `codex-v3.4-red-team/`: go with blocking changes; the executable-proof gate did not exist; R2 impossible with complete single-actuator loss; censoring and disjoint-scalar errors in the statistic; gain omitted from observed support; Paper 2 filter deletes relevant state; plan not reconstructible; name collision.
- [codex-v3.4-assessment.md](codex-v3.4-assessment.md): disposition; all accepted; two earlier Gemini patches reversed.
- **Normative set from here on:** [roadmap-v4.md](roadmap-v4.md), [stage-0a-contract-v3.md](stage-0a-contract-v3.md), [interface-spec.md](interface-spec.md), `confirmation-design.csv` (from `make_confirmation_design.py`). Everything else in this folder is history.
- `executable-proofs/gate/`: the real gate (assertions, mutants, coverage matrix, runner). Four normative groups still uncovered until Phase 0A.

## Readiness protocol
- [readiness-protocol.md](readiness-protocol.md): what "ready" means (executable criteria), the parallel-review-plus-adjudication convergence rule, the stopping rule, the round cap, and the identical prompt for the next parallel round. Contains the frozen-version hash.

## Parallel adjudicated review, round 1 (frozen c197652c0d8e846b)
- `review-claude/`, `review-codex/`, `review-gemini/`: findings and cross-adjudication from all three reviewers on the same hash.
- Applied per the convergence rule: 39 findings; 1 rejected; 2 judgment calls with defaults. Details in `review-claude/adjudication.md` and the round log in `readiness-protocol.md`.
- **Frozen version 2** (hash in `readiness-protocol.md`): [roadmap-v4.1-amendments.md](roadmap-v4.1-amendments.md), [stage-0a-contract-v3.1.md](stage-0a-contract-v3.1.md), [interface-spec-v2.md](interface-spec-v2.md), regenerated `confirmation-design.csv`, and the rebuilt gate in `executable-proofs/gate/` (17 tests; `mutants.py` kills all 8 mutants including the 4 submitted by reviewers; `run_gate.py` checks the environment).
- Round 2 prompt is at the end of `readiness-protocol.md`. One round remains under the cap.

## Parallel adjudicated review, round 2 (frozen d23960e6da441de7)
- `review2-claude-fable/`, `review2-claude-opus/` (fresh-context Claude reviewers on different models), `review2-codex/`, `review2-gemini/`.
- [round2-adjudication-and-tally.md](round2-adjudication-and-tally.md): convergence table, dispositions, five decisions for Daniel, process conclusion (prose cap reached; next round is a code review).
- [decisions-required.md](decisions-required.md): D-1 to D-5 with recommendations. **Nothing freezes until these are answered.**
- [roadmap-v4.2-amendments.md](roadmap-v4.2-amendments.md): safe corrections only (references, registry, interface entry points, roles, definitions, power gate, calibration sharing).
- `executable-proofs/gate/`: rebuilt; 23 tests; `mutants.py` kills all 23 mutants from four reviewers; `freeze-manifest.txt` + `freeze.py` define the hash.

## Decisions D-1 to D-5 applied; Opus review folded in
- [stage-0a-contract-v3.2.md](stage-0a-contract-v3.2.md), [interface-spec-v3.md](interface-spec-v3.md), [roadmap-v4.3-amendments.md](roadmap-v4.3-amendments.md) (decisions), [roadmap-v4.4-amendments.md](roadmap-v4.4-amendments.md) (Opus findings; no-repair-during-review rule).
- `review2-claude-opus/`: 31 findings, 106 independent algebra checks, 8 mutants (all now killed). Adjudicated in section 7 of the tally.
- [decisions-required.md](decisions-required.md): **D-6** (false-alarm unit and episode length) and **D-7** (third arm to isolate probing) pending.
- Gate: 25 tests; 23 reviewer mutants killed; alarm counting and matching added; recursion and identity guards on mutants.
- `sequential-ibd-spec.md`: being drafted by a fresh-context agent (D-4a); to be red-teamed and signed before it is normative.
- Candidate frozen version 3: `f694022256fe497e` (not a review target until D-6, D-7 and the IBD spec are settled; the next round is a code review).

## Sequential IBD spec and its review
- [sequential-ibd-spec.md](sequential-ibd-spec.md): draft 1 (to be redrafted under D-8).
- `review-ibd-spec/`: fresh-context review with simulation; verdict redraft; the design-level finding is recorded as **D-8** in [decisions-required.md](decisions-required.md), which also re-recommends D-6 to (b).

## Frozen version 3 and round 3 (design re-baseline, cross-model)
- Decisions D-6 (b), D-7 (a), D-8 (a) applied: [stage-0a-contract-v3.3.md](stage-0a-contract-v3.3.md), [roadmap-v4.5-amendments.md](roadmap-v4.5-amendments.md), matrix with the third arm (2,700 rows), [sequential-ibd-spec.md](sequential-ibd-spec.md) draft 2 (draft 1 preserved in `review-ibd-spec/`).
- **Frozen version 3: `e662b7429b6b347d`.** Round-3 prompt at the end of `readiness-protocol.md`. Reviewers: Codex, Gemini, fresh-context Claude (Opus). No manifest file changes until all three report.

## Round 3 (design re-baseline) and its outcome
- `review3-codex/`, `review3-gemini/`, `review3-claude-opus/`: three independent simulations. D-8's direction confirmed; its F1 operationalisation refuted by all three; a candidate fix (sign-randomised contrast) from one model, unverified.
- [round3-adjudication-and-tally.md](round3-adjudication-and-tally.md); [decisions-required.md](decisions-required.md) now holds **D-9** (five parts, with mandatory cross-model verification of D-9.1).
- Applied after all reviewers reported: [stage-0a-contract-v3.4.md](stage-0a-contract-v3.4.md), interface v3 amendments, [roadmap-v4.6-amendments.md](roadmap-v4.6-amendments.md), regenerated matrix, gate with nine more mutants killed and pins enforced.

## D-9 verification and adoption
- `review-d9-codex/`, `review-d9-gemini/`: independent reproductions of the sign-randomised statistic; both adopt D-9.1; convergent changes to D-9.2 to D-9.5.
- [d9-adjudication.md](d9-adjudication.md): verification table, adopted changes, disclosed caveat (comparator choice moves the AUPRC margin; freeze is pilot-informed).
- [stage-0a-contract-v3.5.md](stage-0a-contract-v3.5.md), [roadmap-v4.7-amendments.md](roadmap-v4.7-amendments.md): D-9 encoded. Gate: 34 tests, 35 mutants killed. Pending: `comparator-spec.md` and IBD spec draft 3 (fresh-context drafts, then round 4 cross-model).

## Frozen version 4: `442cc4b7da691ca0` (both arm specs)
- [comparator-spec.md](comparator-spec.md) (new, fresh-context draft) and [sequential-ibd-spec.md](sequential-ibd-spec.md) draft 3 (drafts 1–2 preserved in `review-ibd-spec/`). Round-4 prompt at the end of `readiness-protocol.md`; reviewers Codex, Gemini, fresh Claude.

## Round 4 (both arm specs, cross-model)
- `review4-codex/`, `review4-gemini/`, `review4-claude-opus/`: three end-to-end implementations. [round4-adjudication-and-tally.md](round4-adjudication-and-tally.md). **D-10** in [decisions-required.md](decisions-required.md): freeze the generator as code; fix comparator capacity; replace the R0-absent rule; balanced probe blocks; offsets; no copies; instance-clustered replication. D-9 margin claim withdrawn pending re-run on the frozen generator.

## D-10 decided; reference generator built
- `review-d10-codex/`, `review-d10-gemini/`: reasoning-only verdicts; adopt on all seven parts. [d10-adjudication.md](d10-adjudication.md).
- [stage-0a-contract-v3.7.md](stage-0a-contract-v3.7.md): D-10 encoded (generator family, delay-aware multi-horizon comparator, per-cell competence floor, balanced probe blocks, offsets, no copies, instance-clustered replication, amended exit condition).
- `executable-proofs/gate/reference_generator.py` + `test_generator.py`: the frozen instance family (certification, oracle, probe injection, events, perturbation set). Gate: 47 tests, 40 mutants killed.
- Pending: comparator spec v2 and IBD spec draft 4 (fresh-context drafts in progress), then freeze version 5 and round 5 on the frozen generator.

## Frozen version 5: `0468104f6431b050` (frozen generator + both arm specs)
- [comparator-spec.md](comparator-spec.md) v2 and [sequential-ibd-spec.md](sequential-ibd-spec.md) draft 4 (earlier versions preserved). Round-5 prompt at the end of `readiness-protocol.md`. This round runs on the frozen generator; agreement to Monte Carlo error is the exit condition for design review.

## Round 5 (frozen generator): convergence reached; task re-posed
- `review5-codex/`, `review5-gemini/`, `review5-claude-opus/`: three implementations agree to Monte Carlo error. Interventional arm reproducible; comparator competence floor fails three-of-three (its change term cannot see an actuator loss); the event changes no channel on most frozen instances, so the primary mostly measured static reachability.
- [round5-adjudication-and-tally.md](round5-adjudication-and-tally.md); **D-11** in [decisions-required.md](decisions-required.md) (primary over the pre-event support with CL-4 certified; second-moment comparator statistic; held-out confirmation seeds; family N; alarm exposure; fit hierarchy).
- Applied: generator repaired (deterministic noise namespace, faithfulness bound, dense B, burn-in, uniform noise multiplier, CL-4 certification); matrix with instance and episode seeds and current arm identifiers; contract v3.8 cross-references.

## PAUSED — see [CHECKPOINT.md](CHECKPOINT.md)


## After D-11 (7 September 2026, resumed from `CHECKPOINT.md`)

- [stage-0a-contract-v3.9.md](stage-0a-contract-v3.9.md): D-11 encoded (§L summarises); supersedes v3.8.
- [interface-spec-v5.md](interface-spec-v5.md): `secondary_support()`, per-instance fit keys, emission-timed alarm bookkeeping, `S_obs_eps_pre` in the oracle labels.
- `executable-proofs/gate/`: family N in `reference_generator.py` (T-L9b), `auc_pre_event_support`, `count_alarms_timed`, `run_length_from_reset` in `contract_ref.py`, `confirmation_seeds.py` (sealed commitment), 66 tests, 47 mutants.
- `superseded-specs/`: comparator v2 and IBD draft 4 (history); the canonical `comparator-spec.md` (v3) and `sequential-ibd-spec.md` (draft 5) are the round-6 targets.
- `readiness-protocol.md`: frozen version 6 and the round-6 prompt at the end.

## Round 6 and after (8 September 2026)

- [round6-adjudication-and-tally.md](round6-adjudication-and-tally.md): three models reproduced to three decimals; the D-11.1a primary cannot see the confounder; the passive arm wins the re-posed task; two reproducible findings; D-12 open.
- `review6-codex/`, `review6-gemini/`, `review6-claude-opus/`: the round-6 reports.
- Round 7 (prose, novelty re-check): prompt at the end of `readiness-protocol.md`; verdicts in `review7-*/verdict.md`.
