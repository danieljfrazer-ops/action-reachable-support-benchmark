# Hardening the first paper: Budgeted Continual Memory under Hidden Volatility

These are concrete changes to the R1 protocol in the report's "Recommended first paper: exact experimental shape" section. Each maps to a finding in [findings.md](findings.md). Adopt them in the two-page preregistration the report already recommends.

## 1. Reframe the contribution (F1, F11)

Primary claim: a budget-matched phase diagram of memory families (local attention, recurrent state, fast weights, episodic store, slow weights) under hidden volatility, delayed queries, transient anomalies and reversals.
Secondary claim, conditional: a learned router improves the retention/adaptation frontier beyond the best non-learned router.
Do not lead with the router. If it fails, the paper is still complete.

## 2. Fix the budget definition (F4)

- Define **total state budget** B_state in bytes as the sum over all tiers a condition may use. Every condition, including single-tier baselines, gets the same B_state. A single-tier baseline gets all of it in one tier.
- Define **total update budget** B_update in operations per event (multiply-accumulates), including write cost to any tier and any gradient computation.
- Define **read budget** separately (retrieval and attention cost per query), because tiers differ mainly in read cost.
- Report three Pareto frontiers, not three points: accuracy versus B_state, versus B_update, versus read budget. Sweep at least four budget levels.
- Run tier ablations: each single tier, each pair, all-but-one. The "router wins" claim is only valid if it beats the best pair at the same total budget.
- Predeclare the expected outcome that at matched update operations the episodic tier dominates. Test it; do not discover it.

## 3. Redefine the oracle (F5)

Replace "oracle hazard-aware routing as an upper bound" with two reference policies:
- **Hazard-informed reference**: given true per-entity hazard, route by a fixed rule (e.g. hazard above h1 to recurrent state, h1 to h2 to fast weights, below h2 to episodic store, stable entities to slow weights). Not an upper bound; a reference.
- **Query-informed reference**: additionally given the query-delay distribution. Closer to an upper bound but still heuristic. Say so.

## 4. Add the baselines that could kill the router (F7)

1. Bayesian online change-point router with hazard learning (Wilson, Nassar & Gold 2010). Model-based, no training.
2. Empirical-hazard heuristic: hazard = 1 / mean observed inter-change interval per entity; route by threshold; time-to-live eviction.
3. Instance-conditional decay scorer (Jain & Shenoy 2024) adapted to the symbolic stream.
4. Memory-R1-style RL over write/update/delete with delayed answer reward.
5. Everything in the report's existing list.
Kill criterion: if baseline 1 or 2 is within one standard error of the learned router on both held-out generator families, drop the router claim and publish benchmark plus negative result.

## 5. Move generator transfer into the primary evaluation (F6)

Predeclare three generator families:
- **Family A (development):** Poisson change-points, independent entities, geometric query delays. Used for all development and router meta-training.
- **Family B (held-out):** bursty change-points (e.g. Hawkes or on/off regimes), so surprise clusters in time.
- **Family C (held-out):** correlated entities (changes propagate along a hidden graph) and heavy-tailed query delays.
Headline results are reported on B and C. Family A results are reported as in-distribution only. Locked test seeds for B and C are generated once and hashed before any router training.

## 6. Tighten metric definitions (F9)

- Per-query outcome is one of: **correct**, **stale** (equals a previous true value), **wrong-other**, **abstain**. Report all four; "stale-answer rate" is stale over answered.
- **Adaptation lag** is measured with out-of-stream probe queries at fixed offsets after each change event (probes do not enter the stream and do not update memory). Report median and 90th percentile.
- **Retention** at delays {1, 10, 100, 1k, 10k, 100k} events; drop any bin with fewer than 200 samples per seed.
- **Calibration**: the model emits a confidence per answer; score with Brier and expected calibration error against correctness, with abstentions excluded and reported separately.
- **Budgets** as in section 2, plus wall-clock reported only under the conditions of section 7.

## 7. Control the hardware confound (F8)

- Warm the machine for 10 minutes before any timed run and log thermal pressure and CPU/GPU clock at run start and end; discard runs whose clock drifts more than a stated threshold.
- Randomise and interleave conditions across the session; never run all seeds of one condition back to back.
- Treat wall-clock and energy proxy as secondary metrics with explicit "fanless laptop, thermally variable" labelling.
- For AutoResearch-style fixed-time trials, replace fixed wall-clock with a fixed operation or step budget on MLX, and keep wall-clock only as a sanity check. This removes the throttling drift from keep/revert decisions.

## 8. Predeclare scale and seeds

- Model size 1 to 10M parameters; state budgets swept from 64 KB to 8 MB; stream lengths 100k for development and 1M for confirmation.
- 5 seeds during development, 10 for confirmation, reported with bootstrap CIs and effect sizes.
- A run ledger (JSONL) with code hash, generator hash, seed, budgets, thermal log, and outcome for every run, including failures.

## 9. Claims we will and will not make

Will: a benchmark, a phase diagram, a set of baselines, possibly a routing method, possibly a negative result about surprise-based writes.
Will not: anything about self-awareness, consciousness, interoception, or "brain-like" learning. The word "self" does not appear in the R1 paper.

## 10. Venue and time box

Pick a venue before starting: CoLLAs, the NeurIPS continual-learning workshop, or an ICLR workshop, whichever deadline gives 4 to 5 months. Time-box R0 to 3 weeks and R1 to the remaining window. If R0 gates are not met in 3 weeks, the gate result is the report.
