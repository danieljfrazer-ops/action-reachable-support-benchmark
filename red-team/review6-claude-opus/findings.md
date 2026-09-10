# Round 6 — adversarial review and independent reimplementation, `claude-opus`

**Frozen version reviewed:** `38d161e762a3de76` (verified with `python3 freeze.py`).
**Gate:** `python3 run_gate.py`, Python 3.12.0 / numpy 2.4.4 → `GATE PASS: tests 66/66, mutation exit 0`, exit code 0, 45.9 s.
**Date:** 7 September 2026. **Reviewer:** `claude-opus`, one of three independent round-6 implementations.

**Every number in this document is mine alone.** All of it comes from `sim_frozen.py` (→ `report.txt`, `results/*.json`) and `aux_attacks.py` (→ `aux_output.txt`), both in this folder, both run on the frozen generator with the frozen interpreter. Nothing has been reconciled against the other two implementations; that is `adjudication.md`'s job. Opinion is marked *(opinion)*.

**Order of work.** Both arms were implemented from `sequential-ibd-spec.md` draft 5 and `comparator-spec.md` v3 alone, and both scripts were written and run to completion, before any `review*/` folder was opened. `review5-*/findings.md` was then read, and only for §5's new-category statement.

---

## 0. What I ran, and what I did not

| | |
|---|---|
| Arms | 1 `seq_ibd`; 2 `cusum_linear_delay_aware`; 3 `cusum_linear_delay_aware_probed` (reported separately, §3 item 11 and `report.txt` §[11]) |
| Base cells | family L × N_x ∈ {10, 30} × τ ∈ {0, 2}; configuration seeds 0–9; confounder present and absent; episode seeds 0–3 |
| Perturbation set | coupling × {0.5, 1, 2} **cross** noise × {0.5, 1, 2} = 9 cells; seed 0; N_x = 10; τ = 0; both confounder conditions |
| Family N | N_x = 10, τ ∈ {0, 2}, seeds 0–4, both conditions — reported separately, **not** in the exit condition |
| Scale | 74 certified draws, ≈ 5,000 rollouts of 2,000 steps; wall clock **5 min 4 s** across 7 parallel processes on this laptop |
| Seeds reduced? | **No.** All 10 configuration seeds in every family-L base cell, as specified. |

**Declared scope cut.** I did **not** run `fit_alarm_reference`, the D-2a ARL_0 calibration or the isotonic calibrator `g`. None of the mandated outputs depends on them: the primary is invariant to any monotone map (contract §G), `h` enters only `raise`, and (ā, v, k) enter only the alarm channel. The D-2a calibration alone is ≈ 9.6 × 10⁷ environment steps for arm 1 (draft 5 §5) and cannot run inside a 20-minute budget. **Consequence: no ARL_0, HPDT, P2 or alarm number is reported here, and R6-OP-08 below is arithmetic, not measurement.**

---

## 1. Findings

Severity: **critical** = the round-6 exit condition or a §G decision rule cannot mean what it says; **high** = a normative claim is false, or a required quantity is unmeasurable as specified; **medium** = a real defect with a bounded consequence; **low** = text, arithmetic or labelling.
Fix type: **decision** (Daniel) · **normative** (contract/registry) · **spec** (arm spec) · **generator** · **artefact** · **gate**.

---

### R6-OP-01 — [critical] The confounding benefit, which *is* the round-6 exit criterion, is identically zero by construction under D-11.1a

**Claim attacked.** Contract §L: *"the confounding benefit's lower 95 percent bound clears δ_AUC = 0.10 in every family-L base cell."* Contract §G: *"Confounding benefit = [Δ_AUC(present) − Δ_AUC(absent)] within regime: superiority if the lower 95 percent bound > δ_AUC …"*

**Evidence 1 — the outcome.** In every family-L cell, every family-N cell and all nine perturbation cells, the `seq_ibd` primary AUC is **bitwise identical** between confounder present and absent, at all three offsets (`report.txt` §[1]): L_Nx10_tau0 @500 = 0.813 / 0.813; L_Nx10_tau2 = 0.687 / 0.687; L_Nx30 identical; N_Nx10_tau0 = 0.840 / 0.840. Measured benefit at offset 500, 95 % percentile bootstrap clustered by instance (`report.txt` §[3]):

| cell | Δ_AUC(pres) | Δ_AUC(abs) | **benefit** | lo95 | hi95 |
|---|---|---|---|---|---|
| L_Nx10_tau0 | −0.066 | −0.049 | **−0.017** | −0.042 | 0.000 |
| L_Nx10_tau2 | −0.312 | −0.312 | **0.000** | 0.000 | 0.000 |
| L_Nx30_tau0 | −0.066 | −0.049 | **−0.017** | −0.042 | 0.000 |
| L_Nx30_tau2 | −0.312 | −0.312 | **0.000** | 0.000 | 0.000 |
| 9 / 9 perturbation cells | — | — | **0.000** | 0.000 | 0.000 |

**Evidence 2 — the mechanism, verified** (`aux_output.txt` §A). `W_o` is supported on body channels only; `u` enters the plant **only** through `G` into the `x` block; `x` feeds nothing. So for one instance, present vs absent:

```
actions identical = True   b identical = True   d identical = True   x identical = False
channels in S_obs(pre) that are confounded = 0
max |o_present − o_absent| over channels IN the pre-event support = 0.000e+00
```

at τ = 0, τ = 2 and family N alike. **Every channel the D-11.1a primary ranks over is bit-for-bit unchanged by the confounder.** The IBD arm, whose statistic reads only those channels, cannot differ. The comparator differs in the third decimal only because its ridge is fitted over all `C` channels, so confounded distractors perturb `β` — a fit-noise effect, not a causal one.

**Why critical.** The confounding benefit is a double difference whose first factor D-11.1a moved onto a channel set from which the confounding has been removed by construction. §L asks round 6 to clear δ_AUC = 0.10 on a quantity that this generator makes structurally zero: no seed count, no sample size and no implementation can produce it. D-11.1a fixed R5-4 (the primary was not really an online quantity) and in the same move deleted the mechanism the whole benchmark exists to measure, while §L went on requiring it.

**Fix.** One of, or 1 + 2 together:
1. **Generator** — give at least one confounded channel action-reachability (an edge `b → x` on the confounded half), re-certify, so confounded channels enter `S^obs,ε(pre)` and the double difference has something to difference.
2. **Normative** — let the co-primary **P2** (confounded-channel false support) carry the confounding endpoint, and remove the confounding benefit from §L's exit condition, keeping Δ_AUC as the adaptation endpoint only.
3. **Normative** — revert the primary to the full-channel AUC and demote the pre-event-support AUC to co-primary (this re-opens R5-4, which D-11.1a exists to close).

*(Opinion: 1 + 2. Option 3 trades one known defect for another.)* **Fix type:** generator + normative + decision.

---

### R6-OP-02 — [critical] R0-present fails and §G's futility condition is met: the passive comparator beats the interventional arm on the primary in all four family-L base cells

**Claim attacked.** Contract §G: *"R0-present is a positive control: lower bound of Δ_AUC(present) > δ_AUC expected; failure is an anomaly that stops the phase."*

**Evidence** (`report.txt` §[1], §[3]), primary offset 500, confounder present:

| cell | seq_ibd [lo95, hi95] | comparator [lo95, hi95] | Δ_AUC(present) |
|---|---|---|---|
| L_Nx10_tau0 | 0.813 [0.727, 0.896] | 0.879 [0.758, 1.000] | **−0.066** |
| L_Nx10_tau2 | 0.687 [0.571, 0.808] | **1.000 [1.000, 1.000]** | **−0.312** |
| L_Nx30_tau0 | 0.813 [0.727, 0.896] | 0.879 [0.758, 1.000] | **−0.066** |
| L_Nx30_tau2 | 0.687 [0.571, 0.808] | **1.000 [1.000, 1.000]** | **−0.312** |
| 9 / 9 perturbation | 0.55 – 0.80 | **1.000** | −0.20 to −0.45 |

At offset 200 the gap widens to −0.268 (τ = 0) and −0.537 (τ = 2). The **upper** bound of the benefit is below δ_AUC in every family-L cell, which is §G's **futility** branch; and R0-present, the positive control whose failure §G says stops the phase, fails in all four base cells.

Family N is the only place the sign reverses: `seq_ibd` 0.840 vs comparator 0.728 at τ = 0, and a benefit of +0.133 [0.017, 0.283] at τ = 2 on 5 seeds — below δ_AUC, wide, and outside the exit condition.

**Reading.** D-11.2's repair of the comparator worked, and then some. *(Opinion: on a linear SCM with a centred policy and a complete actuator loss, a frozen linear residual monitor with delay-aware features is at or near the information bound for "which channel lost its drive", and a probe-budgeted rank-sum over 25 units at 5 % of steps has nothing to add. The regime where interventions should win is the one `comparator-spec.md` §3.4 already names — events that remove only downstream channels — and the benchmark does not currently generate one; see R6-OP-05.)*

**Fix.** Not a code fix; this is D-10's fallback branch (negative result, or the indirect/downstream claim) and belongs with Daniel before any further specification work. **Fix type:** decision.

---

### R6-OP-03 — [high] The D-10.3 competence floor fails at τ = 0 and passes at τ = 2 only on a zero-width interval, decided by an estimator the contract never names

**Claim attacked.** Contract §G / D-10.3: *"in every required (environment, distractor_level, delay) cell the lower 95 percent bound of the comparator's pre-event-support primary AUC without confounding must be ≥ 0.85"*; §L, *"the comparator competence floor … is met in every required family-L cell"*.

**Evidence** (`report.txt` §[4]), comparator, confounder absent, all three offsets identical within cell:

| cell | mean | **lo95** | verdict |
|---|---|---|---|
| L_Nx10_tau0 | 0.863 | **0.725** | **FAIL** |
| L_Nx30_tau0 | 0.863 | **0.725** | **FAIL** |
| L_Nx10_tau2 | 1.000 | 1.000 | PASS — **degenerate interval** |
| L_Nx30_tau2 | 1.000 | 1.000 | PASS — **degenerate interval** |
| N_Nx10_tau0 | 0.728 | 0.495 | FAIL (family N, outside the exit condition) |
| N_Nx10_tau2 | 0.900 | 0.700 | FAIL (family N) |
| 9 / 9 perturbation | 1.000 | 1.000 | PASS — degenerate |

The floor **fails in two of the four required family-L base cells**, and passes in the other two only because all ten instances score exactly 1.000, so the bootstrap returns `[1.000, 1.000]`.

**The second half is the procedure.** Contract §G says only *"intervals clustered by instance"*. It names **no interval estimator, no within-instance summary, and no sidedness**; I had to choose all three (percentile cluster bootstrap over instance means, 20,000 resamples, `default_rng(12345)`; instance = mean of its 4 episode AUCs; 2.5th percentile of a two-sided interval). A zero-width interval for a bounded mean estimated from ten clusters is not a defensible confidence statement, and it is what "PASS" rests on. A Wilson or Agresti–Coull interval on the same ten-of-ten data gives a lower bound near 0.72–0.74 and the cell fails. A one-sided 95 % bound (5th percentile) lifts the τ = 0 figure from 0.725. **In every cell where the floor passes, the verdict is an artefact of an unstated methodological choice.**

**Fix.** (a) Name the interval estimator, the within-instance summary and the sidedness in contract §0/§G. (b) Forbid a degenerate interval from constituting a PASS. (c) Re-derive the 0.85 value for a 3-to-5-positive / 1-to-2-negative AUC — see my position in R6-OP-05. **Fix type:** normative + gate.

---

### R6-OP-04 — [high] A zero-probe, event-blind statistic beats the confirmatory interventional arm on the primary at τ = 2 and in 8 of 9 perturbation cells

**Claim attacked.** Contract §G, primary-outcome properties: *"a fit-time constant, or any statistic that never sees the scored episode, scores exactly 0.5."* And the v3.9 patch, which discloses only that the static loading scores **below** chance.

**Evidence.** `auc_pre_event_support(−s, pre, post) ≡ 1 − auc_pre_event_support(s, pre, post)` **exactly**: `gt` and `lt` swap, `eq` is unchanged, `gt + lt + eq = n₊n₋`. Verified numerically (`aux_output.txt` §B: `auc(v)=0.4000, auc(−v)=0.6000, sum=1.0000`). So the negation of any fit-time vector is itself a legal arm, and its score is one minus the disclosed control's. From `report.txt` §[5] and §[1], offset 500:

| cell | static `l` | **negated `−l`** | seq_ibd | comparator |
|---|---|---|---|---|
| L_Nx10_tau0 | 0.422 | 0.578 | 0.813 | 0.879 |
| L_Nx10_tau2 | 0.200 | **0.800** | **0.687** | 1.000 |
| L_Nx30_tau2 | 0.200 | **0.800** | **0.687** | 1.000 |
| P_cp0.5_nm{0.5,1,2} | 0.000 | **1.000** | 0.675 / 0.600 / 0.550 | 1.000 |
| P_cp1.0_nm{0.5,1,2} | 0.200 | **0.800** | 0.750 / 0.750 / 0.550 | 1.000 |
| P_cp2.0_nm{0.5,1,2} | 0.200 | 0.800 | 0.800 / 0.800 / 0.800 | 1.000 |
| N_Nx10_tau0 | 0.655 | 0.345 | 0.840 | 0.728 |

At τ = 2 an arm that **spends zero probes, is fitted only on fault-free episodes, never sees the scored episode and does nothing online** scores **0.800** against the confirmatory interventional arm's **0.687** — a margin larger than δ_AUC. In the perturbation set it ties or beats `seq_ibd` in **8 cells of 9**; at `coupling = 0.5` it scores a perfect 1.000.

**Why the v3.9 patch is not enough.** The contract records that the static *vector* scores below chance and retains it as a descriptive arm. It never draws the consequence: **below chance is above chance under negation**, and nothing forbids an arm defined as `raw_support = −l`. The property D-11.1a is sold on — "nothing that ignores the scored episode can score above chance" — holds only for statistics constant **across channels**, and §G still asserts the general version two clauses before it qualifies it. A referee will build this arm in ten minutes.

**Root cause** is R6-OP-05: on this generator the lost channel is nearly a deterministic function of the pre-event ordering, so the primary is nearly a relabelling of a fit-time quantity.

**Fix.** (a) Make the **negated** static loading a mandatory reported control alongside the channel-constant control, in §G and in both arm specs' fixtures. (b) Rewrite §G's property sentence so the general claim is never made. (c) The real fix is R6-OP-05's. **Fix type:** normative + spec + gate.

---

### R6-OP-05 — [high] CL-4-by-construction makes the estimand degenerate: losing the *other* actuator removes nothing at all, and the primary is nearly a relabelling of the pre-event ordering

**Claim attacked.** Contract §A0 / D-11.1, "CL-4 certified by construction"; and §L's open question, *"whether CL-4 should require n_lost ≥ 2"* — on which reviewers are asked to take a position with evidence.

**Evidence 1 — the construction.** `reference_generator.Instance.__init__`, with `ea = event_actuator = 0` and `dom = 2·ea mod N_b = 0`:
`self.B[dom, [k for k in range(K) if k != ea]] = 0.0` and `self.A_b[dom, [j for j in range(N_b) if j != dom]] = 0.0`.
Body component 0 is driven by actuator 0 alone and fed by no other body component. It is the channel the event removes, in every instance, by construction.

**Evidence 2 — the other actuator is invisible** (`aux_output.txt` §C). Applying the *identical* event to actuator 1, which has no protecting row, on seeds 0–4 at both delays:

```
L Nx10 tau0   n_lost(actuator 1) = [0, 0, 0, 0, 0]
L Nx10 tau2   n_lost(actuator 1) = [0, 0, 0, 0, 0]
```

**Complete loss of actuator 1 removes no observed channel from the support, on 10 of 10 draws.** `B` is otherwise dense, structural reachability is a union over actuators, so every body channel is still reached by actuator 0. The benchmark's estimand `S^obs,ε` is therefore **generically insensitive to actuator loss**; the only reason the primary has a non-empty negative class at all is the hard-wired isolation row. That is a fact about the *estimand*, not only about the generator, and neither arm spec nor the contract states it.

**Evidence 3 — coarseness and the delay factor** (`report.txt` §[6], `aux_output.txt` §G). `n_lost = 1` in 32 of 40 family-L draws, 2 in 8. `|S^obs,ε(pre)| = 4` at τ = 2 on **all 20** draws, and 5–6 at τ = 0. At τ = 2 the support contains **zero downstream channels**, on all 10 seeds: `structural_reach_full` runs `for _ in range(tau+2, H+1)`, which at τ = 2, H = 3 is **empty** — no propagation hop survives the delay, so the reachable set is exactly the rows of `B`. At τ = 0 the same loop runs twice and 1–2 `d` channels enter.

**Consequences.**
- The per-episode primary is an AUC over 3–5 positives against 1 negative — at τ = 2, a 4-point lattice {0, ⅓, ⅔, 1}. Per episode it asks one question: *is the structurally isolated channel ranked last?*
- That channel is also the largest-loading channel, so the reversed pre-event ordering is a near-sufficient statistic (R6-OP-04).
- **τ = 0 and τ = 2 are not two levels of one nuisance factor.** They are different estimands: one includes a downstream hop, the other does not. Contract §K10 ("downstream `d` inside `S`") is untestable at τ = 2. §L's *"both delays"* is therefore not a robustness check.

**My position on `n_lost ≥ 2` (§L asks for one, with evidence).** **Yes, but not by rejection sampling.** Filtering instances until `n_lost ≥ 2` selects the instance family against the outcome — precisely what §0 forbids elsewhere. Change the **event**, not the **filter**: drop the `dom` isolation rows; certify CL-4 per instance by choosing an actuator (or a partial loss, K7) whose removal costs ≥ 2 observed channels including at least one downstream `d`; and raise `H` to `τ_max + 2 = 4` so a downstream channel is reachable at every delay. Evidence that this de-saturates the comparator: `comparator-spec.md` §3.4 predicts `d` channels move an order of magnitude less than `b` channels, and my §[8] separation numbers agree (Δ on the lost body channel 139–149 vs the retained-body median 88–90; the spec's own diagnostic puts `d` at 8.6/19.9 against 270.8).

**My position on the 0.85 floor value (§L's other open question).** It cannot mean what it meant. On a 4-channel/1-negative episode the attainable AUCs are {0, ⅓, ⅔, 1}; on a 6-channel/1-negative episode {0, 0.2, …, 1}. 0.85 lies strictly between two adjacent lattice points in both, so a cell mean of 0.85 is not a competence level but a mixture weight between "always right" and "sometimes badly wrong" — and with ten clusters its interval is either degenerate or very wide (R6-OP-03). **Recommendation: replace the AUC floor with a quantity that is well behaved on this lattice — the per-episode probability that every lost channel is ranked strictly below every retained channel, with the floor stated on that proportion** (e.g. ≥ 0.80 with a stated lower bound). It is a proportion with a standard interval and it does not change meaning when `|S^obs,ε(pre)|` changes.

**Fix type:** generator + normative + decision.

---

### R6-OP-06 — [high] Cross-spec episode-id collision: the IBD ARL split overruns the comparator's fit splits and the generator's reserved oracle ids

**Claim attacked.** `sequential-ibd-spec.md` §7: *"If the observed run-length dispersion forces n > 400 (§5), the ARL split extends upward from `ep = 900`; **it never overlaps any other set**."* §9 row 27: *"Disjoint by construction and from the generator's reserved ids {996–999}."*

**Evidence** (`aux_output.txt` §H). At the declared sizes the two registries are disjoint. §5 explicitly contemplates `n` up to 666 (the D-2a cap at `T_arl = 3000`):

| n | IBD ARL ids | comparator predictor-fit 900–919 | arm-2 alarm ref 920–939 | arm-3 alarm ref 940–959 | `RESERVED_EP` 996–999 |
|---|---|---|---|---|---|
| 450 | 500–949 | **hit** | **hit** | **hit** | — |
| 500 | 500–999 | **hit** | **hit** | **hit** | **hit** |
| 666 | 500–1165 | **hit** | **hit** | **hit** | **hit** |

Any `n > 400` collides with the comparator's predictor-fit split; any `n > 496` collides with the oracle-only ids (`witness` 999, `severed` 998, `zbar` 997, `bound` 996). Because the generator keys noise by `(seed, ep, variable, t)` and **not** by arm, a collision means the two arms draw the identical noise realisation; at 996–999 an ARL calibration stream would share its noise with the certification witness rollout.

**Fix.** Move the IBD ARL split to a disjoint high range with slack (e.g. `ep ∈ [4000, 4999]`), delete the false disjointness sentence, and add a gate test asserting that the union of every declared split in both arm specs is pairwise disjoint and disjoint from `RESERVED_EP`. One spec line plus one test. **Fix type:** spec + gate.

---

### R6-OP-07 — [high] `confirmation-design.csv`, the frozen design of record, contradicts D-11.6 inside its own rows, and "instance_seed" names three different objects

**Claim attacked.** Contract §L, D-11.6 *"encoded in §0, §F, §H; interface v5"*; the CSV is a frozen manifest artefact.

**Evidence 1.** All 11,124 rows carry simultaneously:
- `fit_hierarchy = per_instance(cell,instance_seed,arm)` — D-11.6; and
- `calibration_rule = D2a_400_runlengths_CI_in_band_shared_per_cell` — the **pre-D-11.6** rule; and
- `calibration_steps = per_cell_until_rule_met_cap_2e6` — a cap stated per **cell**, while the file emits one calibration row per (cell, instance, arm).

`make_confirmation_design.py`'s inline comment on the calibration row reads *"D-11.6: one calibration row per (cell, instance, arm)"* while the `common` dict two lines above still writes `shared_per_cell`. `sequential-ibd-spec.md` §14(b) reports this conflict as contract-side; neither arm spec notices that it is also baked into the frozen design file, which is the artefact a harness actually reads.

**Evidence 2.** `instance_seed` takes values 0…9, and `instance_seed_set` documents them as an *index* into the sealed confirmation set. `sequential-ibd-spec.md` §3 pins the probe-RNG key to `instance_seed = inst.seed = configuration_seed·1000 + n_resamples` (the certified sub-seed). `comparator-spec.md` §1.1 keys artefacts on `(cell, instance_seed, arm)` without saying which. My run shows the sub-seeds actually differ from the configuration seeds (seed 0 → sub-seed 1 at N_x = 10 and 30; family N seeds needed 1, 1, 2, 5, 7 resamples). **A harness that fed the CSV's `instance_seed` into `probe_rng_seed` would draw a different, wrong probe allocation — silently, reproducibly, and identically in every implementation that made the same reading.**

**Fix.** Regenerate the CSV with a per-instance calibration rule and an aggregate step budget; rename the column `instance_index`; add a `certified_sub_seed` column populated at draw time; and state in contract §0 that the ledger's `instance_seed` **is** `Instance.seed`. **Fix type:** artefact + normative + spec.

---

### R6-OP-08 — [high] D-2a's 2 × 10⁶ step cap stopped bounding anything when D-11.6 multiplied the calibration key count

**Claim attacked.** Contract §0, ARL_0 row: *"hard cap 2,000,000 steps"*, written when calibration was *"shared across seeds"*; D-11.6 makes `h` per instance.

**Evidence (arithmetic).** Development design: 4 base cells × 10 instances × 2 confounder conditions × 3 arms = **240 calibration keys**, each capped at 2 × 10⁶ → **4.8 × 10⁸** environment steps. At D-10.7's confirmation floor of 20 instances it is **9.6 × 10⁸**. My measured generator throughput on this laptop is 2,000 steps in 0.235 s single-core (family L, N_x = 10) ≈ 8,500 steps/s, so 9.6 × 10⁸ steps is **≈ 31 hours of generator time alone**, one core, before any estimator cost. Contract §I says "of order 10⁸ environment steps per arm over the four base cells"; the aggregate is an order larger because §I's figure omits the confounder condition and the third arm.

The cap is not wrong; it is *per key*, and the key count grew twentyfold without the cap or §I being restated as an aggregate.

**Fix.** State an **aggregate** step budget in §0 beside the per-key cap, and make "the descriptive alarm comparison is scoped down" (contract §I's own sentence) the **default plan** rather than a contingency. **Fix type:** normative.

---

### R6-OP-09 — [medium] Δ_c is not blind before the change; the comparator spec's F1 band is wide enough to hide the bias and is exceeded in one perturbation cell

**Claim attacked.** `comparator-spec.md` §3.3, *"the fault-free values on supported and unsupported channels are indistinguishable, which is exactly what a change statistic should do before a change"*; §12 F1, *"AUC of −Δ against `S^obs,ε` within [0.35, 0.65] — a change statistic must be blind before the change."*

**Evidence** (`report.txt` §[10]), fault-free episodes, 500-step window, one seed per cell:

| cell | null Δ median | null Δ max | **fault-free AUC(−Δ vs S_obs)** |
|---|---|---|---|
| L_Nx10_tau0 | 2.35 | 5.93 | **0.623** |
| L_Nx10_tau2 | 2.34 | 5.05 | 0.547 |
| L_Nx30_tau0 | 2.42 | 6.01 | **0.621** |
| N_Nx10_tau0 | 2.37 | 5.97 | **0.606** |
| **P_cp0.5_nm0.5** | 2.41 | 7.25 | **0.657 — outside F1's band** |
| all 15 cells | 2.33 – 2.42 | 4.89 – 7.25 | **0.547 – 0.657, mean ≈ 0.60, above 0.5 in 15 of 15** |

The **level** claim survives: the null median 2.33–2.42 against the predicted `√(3K) = 2.449`. The **blindness** claim does not: the fault-free AUC is above 0.5 in every cell, never once below, and F1's `[0.35, 0.65]` band is wide enough to accept a systematic 0.10 bias and is nonetheless exceeded at `coupling = 0.5, noise = 0.5`.

*(Opinion on the mechanism, not measured to attribution.)* Under the closed loop `a_t = W_o o_t + W_u u_t + ε^a`, so `a_t` is a near-deterministic function of a regressor already in the design; the observation noise `ε^o_t` enters both `o_t` and, through `W_o`, the action, and ridge attenuation on the observation block leaves an action-correlated component in the innovation of exactly the channels the policy feeds back from — the body channels, which are the support. `E[r̃ ã] ≠ 0` under the null on those channels. The same collinearity explains `cond(Σ̂_a) = 155–274` at τ = 0 and why the comparator is markedly worse at τ = 0 (0.863) than at τ = 2 (1.000), where `a_{t−2}` is not collinear with `o_t`.

**Fix.** Replace F1's band with a powered two-sided test against 0.5 at a declared tolerance; add the fault-free Δ profile **by channel type** to the ledger; if the bias survives, declare it as a closed-loop property instead of asserting blindness. **Fix type:** spec + gate.

---

### R6-OP-10 — [medium] The two distractor levels are one matched design; "both distractor levels" is not two pieces of evidence

**Claim attacked.** Contract §L, *"on both distractor levels"*. `sequential-ibd-spec.md` §11(e) declares the sharing and calls the result "nearly a duplicate"; it is closer than that.

**Evidence** (`aux_output.txt` §F; `report.txt` §[1], §[6]). The configuration RNG draws `A_b`, `B`, `C_d` before its first `N_x`-dependent consumption (`G`), so the body blocks are identical at both levels; `n_resamples` and the certified sub-seed are identical for all ten seeds; `|S^obs,ε(pre)|`, `n_lost` and the lost set are identical. Measured:

| cell | seq_ibd @200/@500/@1000 | comparator @200/@500/@1000 |
|---|---|---|
| L_Nx10_tau0 | 0.601 / 0.813 / 0.854 | 0.869 / 0.879 / 0.879 |
| L_Nx30_tau0 | **0.601 / 0.813 / 0.854** | 0.869 / 0.879 / **0.882** |
| L_Nx10_tau2 | 0.463 / 0.687 / 0.796 | 1.000 / 1.000 / 1.000 |
| L_Nx30_tau2 | **0.463 / 0.687 / 0.796** | **1.000 / 1.000 / 1.000** |

The IBD primary is identical to three decimals at both levels; the comparator differs in one cell in the third decimal. §L's four family-L base cells are **two** independent experiments.

**Fix.** Re-order the configuration RNG so the body blocks are drawn after `N_x` (making the levels independent replicates), or state in §L that the distractor level is a within-instance factor and the effective cell count is two. **Fix type:** generator or normative.

---

### R6-OP-11 — [medium] `Instance.S_obs_pre_event()` fails open where it must fail closed

**Claim attacked.** Interface v5's oracle contract: `S_obs_eps_pre` is *"the support certified before the confirmatory event; the primary support set"*.

**Evidence** (`aux_output.txt` §J). `S_obs_pre_event()` is `return self._pre_S.copy() if hasattr(self, "_pre_S") else self.S_obs()`, and `_pre_S` is set **only** inside `draw_certified`. On an `Instance` built directly:

```
has _pre_S = False
S_obs_pre_event() BEFORE the event: 6 channels
S_obs_pre_event() AFTER  the event: 5 channels   <-- silently returns the POST support
```

`auc_pre_event_support` then ranks over the wrong set — `NaN` if the two coincide, a quietly wrong number otherwise. Both arm specs mandate a deep-copy discipline (`T-IBD-instance-reset`, `T-CMP-freshcopy`) precisely because `apply_event` mutates in place with no undo; the generator's own accessor then removes that discipline's protection by failing open.

**Fix.** `raise RuntimeError("_pre_S not set: draw through draw_certified")` when `_pre_S` is absent, plus a gate test. Two lines. **Fix type:** generator + gate.

---

### R6-OP-12 — [low, structural] Family N: the certified z̄ estimator and the used z̄ estimator are different objects

**Claim attacked.** Contract §0 T-L9b row; `reference_generator.boundedness_certificate` vs `stationary_mean`.

**Evidence** (`aux_output.txt` §D). Labels come from `operational_effect`, evaluated at `zbar = stationary_mean(T=4000)`: a **single chain**, 2,000 steps discarded, 2,000 averaged. T-L9b instead certifies four-group agreement of a **32-chain batch** over 18,000 retained steps. The estimator that sets the labels is never certified, and `apply_event` invalidates the cache so the post-event support is a second, independent Monte Carlo draw.

**But the attack fails empirically, and I record that.** On seeds 0–4, `S_obs()` is bit-identical under re-estimation at `T ∈ {2000, 4000, 8000, 16000, 32000}` (`|S| = 6` throughout), and the label margin `min|e_j − ε|` is **0.21 – 0.42**, an order above any plausible Monte Carlo error. Family L margins are 0.18 – 0.55 (`aux_output.txt` §E). The labels are robust. What remains is that nothing *guarantees* it: the certification does not bound the margin against the estimator's own error, and the T-L9b tolerance is tight — measured four-group spreads are 0.0185, 0.0308, 0.0352, 0.0363, 0.0401 against `δ_inv = 0.05`, i.e. seed 4 sits at **80 % of the bound**, and `δ_inv` is contract §0's *invariance tolerance* reused verbatim with no derivation for this use.

**Fix.** Estimate `z̄` from the 32-chain batch T-L9b already runs (free), and require `min|e_j − ε|` to exceed a stated multiple of the Monte Carlo standard error of `ẑ̄`; add both to `certify()`. **Fix type:** generator + normative.

---

### R6-OP-13 — [medium] §G's decision rule requires control-tier evidence that does not exist anywhere in the frozen package

**Claim attacked.** Contract §G: *"superiority if the lower 95 percent bound > δ_AUC on both SCM families **and the sign holds on both control-tier environments**"*; §L's exit condition, which is family-L only.

**Evidence.** `confirmation-design.csv` contains 2,880 rows with `family = T2` (`pointmass_2d`, `pendulum_v1`). No generator for either exists in the frozen package; `reference_generator.Instance` raises on any family other than `"L"` or `"N"`. Neither arm spec mentions PointMass2D or Pendulum-v1 in any normative section. The superiority branch of §G's rule is unreachable, and §L's exit condition is strictly weaker than the rule it feeds.

**Fix.** State in §L that round 6 closes design review for the SCM tier only, and that the control tier is a separate later gate with its own generator deliverable. **Fix type:** normative.

---

### R6-OP-14 — [low] λ_rel's disclosed round-5 selection is probably inert, but the round-6 sensitivity evidence is void; κ_min is inert everywhere and is mislabelled "provisional"

**Claim attacked.** `comparator-spec.md` header, *"There is no outcome-dependent tuning clause"*; §11 row 8, *"round 5 measured 1e-4 as the best of {1e-4, 1e-2, 1} on the old statistic; v3 does not re-select"*; §11 row 20, κ_min *"provisional until the pilot confirms both margins at every C and τ"*; §11, *"Zero swept parameters in the confirmatory configuration."*

**Evidence** (`report.txt` §[9], §[7]).
- λ_rel ∈ {1e-5, 1e-4, 1e-3} and κ_min ∈ {1e-8, 1e-4, 1e-2}: the primary at offset 500 is **1.000 at every value in every one of the 15 cells** at seed 0, and the static control is unchanged to three decimals.
- **But seed 0's comparator saturates at 1.000 everywhere, so this check has no power to detect anything.** I report it as measured and label it uninformative rather than as evidence of robustness. A powered version must run at a non-saturating instance, which on my data means τ = 0 seeds other than 0.
- κ_min genuinely never binds: `q = 3K = 6` in **15 of 15** cells, with the smallest retained eigenvalue between **8.3×** (worst case `coupling = 0.5, noise = 0.5`, where `cond(Σ̂_a) = 1205`) and **346×** the cutoff. No configuration in the design or the perturbation set truncates.

**Position.** The λ_rel disclosure is honest and the value is very likely inert, but the evidence offered in round 6 is void; and "zero swept parameters" describes the confirmatory run, not the provenance of the constant, which *was* swept on a related outcome. κ_min should be relabelled **"inert on the frozen family and its perturbation set; retained as a guard for hand-built and morphology fixtures, worst measured margin 8.3×"** rather than "provisional pending pilot confirmation" — the pilot has nothing left to confirm. **Fix type:** spec + gate.

---

### R6-OP-15 — [low] The two specs disagree on the offset read gap, and `sequential-ibd-spec.md` §14(d)'s open-items list is stale against the frozen files

**Evidence** (`aux_output.txt` §I and direct inspection of the frozen files).
- Read gap: comparator 1199 / 1499 / 1999, IBD 1182 / 1482 / 1982 → **17 steps at every offset**. `comparator-spec.md` §4.5 and contract §G say 17. `sequential-ibd-spec.md` §13 (R5-26 row) and §14(g) say *"up to 18 steps apart"*. 17 is correct.
- §14(d): *"contract §G's P2 paragraph still says offsets {10, 50, 200}"* — contract v3.9 §G says `{200, 500, 1000}`.
- §14(d): *"`confirmation-design.csv` carries `10|50|200`"* — the frozen CSV carries `p2_offsets = 200|500|1000` and `offsets_F1 = 200|500|1000` on **every** row.
- §14(d): the `n_oracle` item — contract §0's row already declares the constant dead and not a contract constant.

All of §14(d) and part of §14(g) are already fixed in the frozen files. A stale open-items list is not harmless in a document whose function is to say what remains open. **Fix type:** spec text.

---

### R6-OP-16 — [low] The perturbation set is ambiguous and under-specified

Contract §0: *"perturbation set: coupling × {0.5, 1, 2}, noise × {0.5, 1, 2}"*. This reads either as a 3 × 3 **cross product** (9 cells; my reading) or as two **marginal sweeps** (5 distinct cells). `test_gen_perturbation_set_still_certifies` iterates the 2 × 2 cross of the non-unit values, which suggests the cross but does not settle it and never tests the marginal cells. The registry also does not say at which `τ`, `N_x`, seed set or confounder conditions the set is run. I chose the 3 × 3 cross at `N_x = 10`, `τ = 0`, seed 0, both conditions. **Fix type:** normative (one clause).

---

## 2. Choices the specs left open

The brief says there should be none. I found **eleven**.

| # | Choice | What the specs say | What I chose | Changes a verdict? |
|---|---|---|---|---|
| 1 | Interval estimator for "95 % intervals clustered by instance" | contract §G names none | percentile cluster bootstrap over instance means, 20,000 resamples, `default_rng(12345)` | **Yes** — decides the τ = 2 floor (R6-OP-03) |
| 2 | Within-instance summary before clustering | "scored per episode, paired by instance … clustered by instance" | mean of the 4 episode AUCs; instance is the resampling unit | Yes — a cluster-robust variance over episodes gives a different width |
| 3 | Sidedness of "lower 95 percent bound" | §G says both "lower 95 percent bound" and "95 percent interval" | 2.5th percentile (two-sided) | **Yes** — a one-sided bound is the 5th percentile and lifts 0.725 |
| 4 | Perturbation set: cross vs marginal, and its τ / N_x / seeds / confounder conditions | contract §0, unstated | 3 × 3 cross, N_x = 10, τ = 0, seed 0, both conditions | Changes the cell count, 9 vs 5 |
| 5 | ARL calibration stream length for the comparator | IBD fixes `T_arl = 3000`; comparator §6 gives only "≈ 3 × ARL_0" | n/a (scope cut) | Matched-ARL comparison with unmatched, one unspecified, stream lengths |
| 6 | What "instance_seed" denotes | CSV index 0–9 / configuration seed / `inst.seed` — three objects, one name | `inst.seed`, per the IBD spec's pin | **Yes** — wrong probe allocation if read from the CSV (R6-OP-07) |
| 7 | The ridge solve | comparator §1.2 says "float64 Cholesky", not which substitution | `np.linalg.cholesky` + two triangular solves | ~1e-14, within an order of the declared 12-significant-digit tie tolerance |
| 8 | Whether arms 1 and 2 must use the **same** generator `ep` for the scored episodes | both say "scored 0–3"; neither says the pairing requires it | same eps 0–3 | The paired Δ_AUC is undefined if they differ — noise is keyed by `ep` |
| 9 | Offsets at which the **secondary** full-channel AUC is read | IBD says "at each offset"; §G does not restate | all three | No (the comparator's secondary is static in `t`) |
| 10 | Whether the confounder-absent deep copy inherits `_pre_S` | both specs say "not re-certified"; neither mentions `_pre_S` | inherited | No on this generator (`S_obs` does not depend on `G`), but unstated |
| 11 | Whether `q` may differ between the present and absent fits of one instance | comparator §3.2 logs `q` per fit, requires no equality | allowed to differ; measured equal (6) everywhere | No, as measured |

---

## 3. Attacks that failed

Recorded so the adjudication can distinguish "not attacked" from "attacked and survived".

1. **Probe accounting.** Draft 5 §3's "99 applied, 99 units, fraction 0.0495" against the 0-indexed generator is **exactly right**. My independent grant loop gives `{20, 40, …, 1980}`, 99 probes, 0.0495, and 25 units in every window at every read offset (`report.txt` §[12]). The start-of-episode under-spend is real and correctly declared.
2. **Offset read rule and epoch grid.** 1182 / 1482 / 1982 and 1199 / 1499 / 1999 fall out of §G's single rule with no interpretation. §6's mixture table (25 units, oldest anchor 1000 at offset 500) reproduces exactly.
3. **Lag-slot attribution.** `comparator-spec.md` §3.3's un-whitened ĉ on the lost channel reproduces **to the last digit** in my independent implementation: `[−7.30, −5.38, −6.25, −4.66, −5.00, −3.76]` at τ = 0 (largest slot `a_t, k = 0`) and `[−4.53, −3.46, −5.55, −4.40, −6.67, −5.33]` at τ = 2 (largest slot `a_{t−2}, k = 0`). The claim that the arm needs no knowledge of τ holds. I note without calling it a defect that all six slots load within a factor of ~2, so slot identity is decorative — the quadratic form is driven by joint magnitude.
4. **Whitener conditioning and rank.** `cond(Σ̂_a) = 212.6` on the pinned draw against the spec's 213; `q = 3K` everywhere. §3.2's rank argument survives.
5. **The null level of Δ.** `√(3K) = 2.449` holds (2.33–2.42 across 15 cells). Only the blindness half fails (R6-OP-09).
6. **The channel-constant control.** Exactly `0.500000` in all 15 cells, both conditions, as §G asserts. `auc_pre_event_support`'s mid-rank tie handling is correct.
7. **Estimator-RNG domain separation.** I tried to construct a collision between `default_rng([5477, instance_seed, episode_seed, 1])` and the generator's `[seed, ep, VAR_ID, t]`, `[seed, 0]`, `[seed, 555]`, `[seed, 777]`. It requires generator `seed = 5477`, which is not a development sub-seed (`{0..59} ∪ {1000..1059} ∪ … ∪ {9000..9059}`) and is below the sealed confirmation range `[100000, 999999]`. **No collision is reachable.** *(Opinion: it holds by accident of the seed ranges, not by construction; a `probe_ns` above 10⁶ would make it structural.)*
8. **Burn-in namespace.** `ep + 100000` against ids all below 100000 — no main stream collides with another episode's burn-in prefix, as `comparator-spec.md` §1.1 claims. Correct for both registries **as declared** (R6-OP-06 attacks the extension clause, not this).
9. **Degeneracy rule.** Declared unreachable, measured unreachable: `degenerate = 0` channels in all 15 cells, including the four padding channels. §5's claim survives.
10. **Δ_cap.** The largest Δ at any scored read across the whole run is ≈ 677 (`coupling = 2, noise = 0.5`), 15× below `Δ_cap = 1e4`. The cap never binds. §4.3 survives, though the margin is 15× rather than the spec's quoted 37×, because the spec's figure comes from the unperturbed family.
11. **Arm 3 identity and effect.** Arm 3's predictor artefacts are bitwise identical to arm 2's by construction, and arm 3's primary at seed 0 is **1.000** in all four family-L base cells, both conditions — identical to arm 2 (`report.txt` §[11]). No probe effect is detectable at the ceiling; §7's refusal to predict the arm-3 − arm-2 difference is vindicated, and the measurement is uninformative for the same reason R6-OP-14's sensitivity is.
12. **Family-N label stability.** See R6-OP-12: I attacked the single-chain z̄ and the attack failed on the evidence.

---

## 4. New mutants the gate does not reject

I copied the gate into `mutant_gate/` and `mutant_gate2/` — **no existing file was edited** — and ran the **full** `run_gate.py` (all 66 tests plus the 47-mutant run) on each mutated copy. A mutant survives only if that whole command exits 0.

### MUT-O2 — SURVIVOR (confirmed). `contract_ref.auc_pre_event_support` ranks over `pre | post` instead of `pre`

```python
sel = pre | post
return auc_prob_superiority(s[sel], post[sel])       # instead of s[pre], post[pre]
```

**Gate result:** `tests: 66 passed, 0 failed` … `47/47 mutants killed` … **`GATE PASS: tests 66/66, mutation exit 0`**, exit code 0. Log: `logs/mut_o2_gate.log`. Patch: `mutants_new.MUT-O2.contract_ref.py.patch` (apply to a *copy* of `executable-proofs/gate/` and run `run_gate.py` there; no frozen file was modified).

**Why it survives.** Every fixture in `test_gate.test_G_auc_pre_event_support_…` and every tuple in `mutants.PROBES["auc_pre_event_support"]` has `post ⊆ pre`, so `pre | post == pre` and the mutant is bit-identical on all of them.

**Why it matters.** `post ⊆ pre` is a property of the **actuator-loss** event alone. Contract §D and §K8 both admit events that *add* observed support — `sensor_gain` with a large or negative `g` on a sub-threshold channel, and re-certified `actuator_partial` (K7). Under any of those a channel can be in `post` and not in `pre`, and the mutant silently redefines the contract's **central metric**. Demonstrated: with `pre = [1,1,1,0]`, `post = [1,0,0,1]`, `scores = [9, 1, 2, −99]`, the original returns **1.0** and MUT-O2 returns **0.5**.

**Fix.** Add a `test_gate` case with `post ⊄ pre` (a `sensor_gain` fixture) and a matching tuple in `mutants.PROBES["auc_pre_event_support"]`, so that any variation in the restriction set is distinguishable. One assert plus one probe. **Fix type:** gate.

### MUT-O1 — KILLED. `reference_generator.boundedness_certificate` checks the wrong blocks

```python
keep = slice(self.sl["w"].start, self.sl["x"].stop)    # instead of b .. d
```

T-L9b's four-group stationary-mean agreement is contract §0's family-N ergodicity criterion, specified on *"the stationary mean of the **b and d** blocks (the nonlinear loop)"*; `w` and `x` are linear AR(1) with exact zero mean and are excluded by the generator's own comment for exactly that reason. Under the mutant the agreement test is **vacuous** — evaluated on blocks that are zero-mean by construction — so `stationary_ok` is true for any instance whose linear blocks converge and the nonlinear loop's invariance is never checked. **Verdict: KILLED**, and I report it as a failed mutant. `run_gate.py` gives `tests: 63 passed, 3 failed` (`logs/mut_o1_gate.log`): `test_gen_family_N_certifies_bounded_stationary_cl4_and_label_consistent`, `test_gen_family_N_divergent_subseed_is_rejected_not_certified` and `test_gen_family_N_response_is_not_odd_and_uses_zbar` all fail, because loosening the agreement criterion changes which sub-seed `draw_certified` accepts and the accepted instance then violates the z̄ assertions. My prediction that the three tests would tolerate it was wrong.

**But note where the kill comes from.** All three failures are in `test_generator.py`, and `mutants.py`'s `failures()` iterates **`test_gate` only**. So MUT-O1 is killed by the *test suite* and would be scored `SURVIVED` by the *mutation criterion*, which is the half of the gate that readiness criterion 2 is stated against.

**The structural point stands.** `mutants.py`'s `failures()` iterates **`test_gate` only** — not `test_generator`, not `test_proof_theatre`. The 47-mutant kill criterion therefore covers `contract_ref.py` alone, and **no mutant of `reference_generator.py` is expressible in the framework at all**, although the generator is normative under §A0 and D-10.1 and is where CL-4, T-L9b and the family-N labels live. (Round-5 codex found a generator mutant that passed the whole gate, R5-CX-01; the framework gap that allowed it has not been closed.) **Fix:** extend `failures()` to all three test modules and add a generator-mutant section to `mutants.py`. **Fix type:** gate.

---

## 5. New-category statement against rounds 1–5

*(Written after the simulation had run and §1–§4 were drafted, and after reading only `review5-*/findings.md`.)*

**Genuinely new categories, made possible by version 6 and by the D-11 repairs themselves:**

1. **Estimand–treatment orthogonality** (R6-OP-01). The primary is measured on a channel set the treatment provably cannot reach, so the exit criterion is structurally zero. Round 5's benefit was *positive* (R5-CX-04 argued about its size on the perturbation aggregate; opus and gemini measured it clearing δ_AUC in the base cells). D-11.1a created this; no round-5 finding is of this kind.
2. **Sign-reversal of a disclosed control** (R6-OP-04). A control disclosed as *below* chance is an *above*-chance arm under negation, and it beats the confirmatory arm. R5-4 argued the primary was not genuinely online; nobody negated the control.
3. **Estimand non-comparability across the delay factor** (R6-OP-05, R6-OP-11 discussion). At τ = 2 the H = 3 horizon leaves zero propagation hops, so `S^obs,ε` contains no downstream channel and the two delay cells score different estimands. Not in any round-5 finding.
4. **Structural invisibility of the non-protected actuator** (R6-OP-05, `aux` §C: `n_lost = 0` for actuator 1 on 10 of 10 draws). Round 5 found CL-4 *uncertified* (R5-CX-02, R5-GM-01, R5-5); nobody asked what CL-4-by-construction implies about the estimand in general. The answer — that `S^obs,ε` is generically insensitive to actuator loss and the negative class exists only because of a hard-wired isolation row — is new and is an attack on the round-5 *repair*.
5. **A cap invalidated by a scope change** (R6-OP-08). D-11.6 multiplied the calibration key count twentyfold and D-2a's per-key cap was left untouched, so nothing bounds the aggregate. R5-CX-06 raised the fit hierarchy; nobody costed the repair against the existing cap.
6. **A surviving mutant in the contract's own primary-metric reference** (MUT-O2). Round 5's surviving mutant (R5-CX-01) was in the generator, exploiting the framework gap. MUT-O2 is inside `contract_ref.py`, inside the 47-mutant run's own probe set, on a function that did not exist before v3.9, and it exploits a fixture family that only ever exercises `post ⊆ pre`.

**Repeats or continuations of round-5 categories, with new manifestations:**

- **D-10.3 floor failure** (R6-OP-03) repeats R5-2 / R5-CX-03 / R5-GM-03, now on the *new* statistic and with two new halves: the interval estimator is unspecified, and where the floor passes it does so on a zero-width interval.
- **Distractor levels are not independent** (R6-OP-10) repeats R5-27, now with the measurement that the IBD primary is identical to three decimals.
- **The gate covers neither arm** (MUT-O1 discussion) repeats R5-CX-13 and R5-CX-01; unchanged in v6.
- **Registry-versus-prose drift** (R6-OP-15) is the R5-19 / R5-CX-17 category, now inverted: the *specs'* open-items lists have gone stale against a contract that fixed them.
- **Constant provenance** (R6-OP-14) is R5-21's category; my contribution is that the round-6 sensitivity evidence for λ_rel is measured at the ceiling and is void.
- **Cross-artefact inconsistency in `confirmation-design.csv`** (R6-OP-07) is R5-CX-07's category applied to the regenerated file; the "`instance_seed` names three objects" half is new.

---

## 6. Verdicts recorded after drafting

- **MUT-O2:** SURVIVES the full gate (66/66 tests, 47/47 mutants killed, exit 0). Confirmed.
- **MUT-O1:** **KILLED** — `tests: 63 passed, 3 failed`, all three in `test_generator.py` (`logs/mut_o1_gate.log`). Reported as a failed mutant. The framework gap it targets (`mutants.failures()` runs `test_gate` only, so the mutation criterion would have scored it SURVIVED) is independent of the verdict and stands.
- **MUT-O3** (`reference_generator.boundedness_certificate`: `np.array_split(np.arange(n), 4)` → `..., 2)`, against contract §0's explicit "four chain groups of 8"): **KILLED** — `tests: 63 passed, 3 failed`, the same three `test_generator.py` family-N tests as MUT-O1 (`logs/mut_o3_gate.log`). Reported as a failed mutant.

**Net mutant result: 1 survivor of 3 attempted.** Both attempts against family N's T-L9b certification were killed, and killed for the same reason — any loosening of the agreement criterion changes which sub-seed `draw_certified` accepts, and the accepted instance then violates the pinned z̄ assertions. `test_generator.py`'s family-N block is tighter than I expected and I record that as a strength of the frozen gate. The survivor is against `contract_ref.auc_pre_event_support`, i.e. against the contract's own primary-metric reference.

**Reproduction.** The three mutant patches are in this folder as `mutants_new.MUT-O{1,2,3}.*.patch`. Apply each to a **copy** of `executable-proofs/gate/` and run `run_gate.py` inside the copy; the working copies have been deleted to keep this folder small. No file outside `review6-claude-opus/` was modified at any point, and `python3 freeze.py` still returns `38d161e762a3de76` after all of this work.
