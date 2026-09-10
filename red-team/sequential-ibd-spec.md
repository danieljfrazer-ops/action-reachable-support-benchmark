# Sequential IBD — normative specification (DRAFT 5, informative until signed)

**Status.** Draft 5, 7 September 2026. Basis: `stage-0a-contract-v3.9.md` §§0, A0, B, C, D, F, G, H, H2, L; `interface-spec-v5.md`; `executable-proofs/gate/reference_generator.py` and `executable-proofs/gate/contract_ref.py` (the frozen generator and reference functions are the **only** environment this spec is written against); `decisions-required.md` (D-11); `round5-adjudication-and-tally.md`; `review5-codex/findings.md`, `review5-gemini/findings.md`, `review5-claude-opus/findings.md`. Supersedes draft 4 (`superseded-specs/sequential-ibd-spec.draft4.md`). **Informative until Daniel signs.** Arm identifier `seq_ibd`, `arm_id = 1`.

**Two [prov] constants are introduced here and nowhere else** (§9 rows 7 and 25): `probe_ns = 5477`, the integer namespace that domain-separates the estimator's probe RNG from the generator's noise keys, and `T_arl = 3000`, the length of a D-2a fresh-start calibration stream. Both are genuinely needed — three implementations cannot draw identical blocks without a fully specified seed, and D-2a fixes a run-length count and a step cap but no stream length — and neither is a registry constant. Everything else is either inherited from contract §0 or already in this spec's parameter table.

**What draft 5 changes, and what it does not.** The statistic (a tie-corrected rank-sum z of signed increments contrasting `+e_k` against `−e_k` probes), the trailing window `W_steps = 500`, the balanced pre-randomised (k, sign) blocks and the h-independence design are **not re-opened**: three independent round-5 implementations reproduced this arm on the frozen generator at AUC 0.800 / 0.815 / 0.831 (offset 500, N_x = 10, τ = 0, confounder present), and the adjudication records the arm as robust and reproducible. Draft 5 changes what D-11 changes and closes every choice round 5 found open:

1. **The primary becomes the pre-event-support AUC** (D-11.1a, §6). `raw_support = a_c` is unchanged and `secondary_support()` returns the same vector; what changes is the set the evaluator ranks over and therefore what the arm is credited for.
2. **The ARL_0 clock starts at reset for every arm and the warm-up prefix is charged to this one** (D-11.5, §5). Draft 4's row-19 justification, *"a run length that cannot alarm is not a run length"*, is **withdrawn by decision**, not silently dropped (§13, R5-CX-09).
3. **Every learned artefact is fitted per instance** (D-11.6, §7), on that instance's own fault-free split, with the fit-split episode seeds fixed here and disjoint from the scored seeds.
4. **The estimator's clock, probe count, RNG seed, block-consumption order and emission grid are fixed against the frozen 0-indexed generator** (§2, §3). Draft 4's "100 applied / 99 units" accounting was written for a 1-indexed environment that does not exist; the corrected count is **99 applied, 99 units** and the terminal-probe waste R4-23 declared **does not exist** (§3).
5. **Family N exists** (D-11.4) and `T-IBD-exch` runs on families L and N. Family-N results in round 6 are a **reproduction target only** and are not part of the round-6 exit condition (contract §L).

**Published IBD, cited honestly.** Liu, Cheng & Bogdan, arXiv:2603.18257 v2: two branches under a dedicated π_probe, ≈ 32k steps once, Welch t per (dimension, horizon), Bonferroni within and BH across, Props. 3.3–3.5. **This arm departs**: no baseline branch, no π_probe; the contrast is between the estimator's own probe signs, sequentially, in-task, at 5 % of steps. None of Props. 3.3–3.5 is inherited (§11).

**Numbers labelled *(diagnostic)*.** A few index tables and mixtures below were reproduced against the frozen generator by one model in one process while this draft was written (`superseded-specs/ibd-draft5-diagnostic.py`, output alongside, `PYTHONHASHSEED=0`, Python 3.12.0 / numpy 2.4.4). They are **single-model diagnostics**, never results. Every arithmetic claim they touch is also a gate test (§12) that three implementations must reproduce.

---

## 1. Interface and information set [N]

Online estimator of **action-reachable observation support** `S^obs,ε_{t,H}` (contract C3, C6) — not body membership, not R, not M. Under D-11.1a the *scored* question is narrower: which of the channels that were controllable **before** the confirmatory event are still controllable after it (§6).

- `information_set = "transitions_only; no_reward; no_oracle; own_probe_allocation_known; calibrator_injected_via_configure"`. The arm sees `Transition = (prev_obs, applied_action, obs, probe_flag, t)` only — no reward, oracle labels, P, latents, event times, **no `episode_len`**, **no τ**, and **no confounder condition**. It knows its own (k, sign) allocation because it generated it.
- **Construction [N] (closes R5-17, R5-CX-14).** The harness constructs one estimator object per `(cell, instance_seed, episode_seed, confounder, arm)` and passes the probe-RNG seed vector to the constructor: `seq_ibd(C, K, probe_rng_seed = [probe_ns, instance_seed, episode_seed, arm_id])`. This is a **constructor argument, not part of `configure`'s bundle**; interface v5 does not name it, and that gap is recorded in §14(e). The seed vector, and the sha256 of the resulting allocation, go in the ledger.
- `configure(bundle)`: `regime_model_params = None`; `calibrator_params = {g_knots}`, **fitted by the harness** (it owns the oracle labels) on **this instance's** calibrator split; `arm_reference_params = {ā[C], v[C]}`, computed by this arm on **this instance's** alarm-reference split. Hashed and logged with the key `(cell, instance_seed, confounder, arm)`.
- `fit_predictor` is a **no-op**. `fit_alarm_reference(transitions)` computes (ā, v) per §7 on this instance's own fault-free **probed** stream. `set_threshold(h)` takes the harness's per-instance ARL_0 threshold.
- `update(transition) -> (raw_support[C], p[C], stat, raise)`, once per environment step, piecewise constant between epochs. `raw_support = a[C]` is the arm's **primary statistic** (§6). `secondary_support() -> a[C]`: this arm's two statistics coincide, so the same vector is returned (contract §H(1), interface v5). `raise = 1[stat > h]` with **no persistence inside the estimator**.
- Declarations: `persistence_unit = "epochs"`; `emission_grid = "t ≡ 2 (mod Π)"` (§2); `statistic_is_monotone_in_alarm = True`; `sign_blindness = "formula"`; `preferred_probe_steps = 1`; `needs_calibration_split = True`.
- `request_probe(steps) -> actions[steps, K] or None` (§3).

## 2. Clocks, stated once [N] (contract C, R4-CX-08, R5-CX-12, R5-23)

**The environment clock is the generator's, and it is 0-indexed.** `Instance.run(T)` iterates `for t in range(T)`: it applies `actions[t]` at step t, for t = 0 … T−1. There is no step t = T. With `episode_len = 2000` the legal step indices are **0 … 1999** and the observation array holds `o_0 … o_2000`.

**The transition of step t is `(prev_obs = o_t, applied_action = a_t, obs = o_{t+1})`, and `o_t` is the PRE-action observation** — what the policy reads before choosing `a_t`. Since `b_{t+1} = A_b b_t + (drive)(a_{t−τ})`, a probe applied at `t_p` first moves the observation at `o_{t_p+τ+1}`: **first hit at h = τ + 1**.

The estimator writes `O[t] := tr.prev_obs`, `O[t+1] := tr.obs`, and forms `D_c^h(t_p) = O[t_p+h] − O[t_p]`, h ∈ ℋ = {1,2,3}.

| `update` call (τ = 0, probe `+e_k` applied at t_p = 20) | transition | contributes |
|---|---|---|
| t = 20 | (o₂₀, **+e_k**, o₂₁) | `D¹ = o₂₁ − o₂₀` — first hit, h = τ+1 = 1 |
| t = 21 | (o₂₁, policy, o₂₂) | `D² = o₂₂ − o₂₀` |
| t = 22 | (o₂₂, policy, o₂₃) | `D³ = o₂₃ − o₂₀`; **unit closes** at `t = t_p + max(ℋ) − 1` |

At τ = 2 the same probe leaves `D¹` and `D²` **zero in expectation** — on a live stream they are noise, not zero; only the deterministic zero-noise fixture makes them exactly zero (R5-18) — and the first hit is at h = 3 = τ+1. `T-IBD-horizon` asserts both on the frozen generator; *(diagnostic: at τ = 0 the maximum absolute increment is 0.795 at h = 1; at τ = 2 it is exactly 0.0 at h = 1 and h = 2 and 0.795 at h = 3.)*

**The estimator's own clock [N].** The estimator holds `t_next`, the index of the step **about to be taken**: `t_next = 0` at reset, incremented by 1 at the end of every `update`. `request_probe` is evaluated against `t_next` (§3). This removes draft 4's `tp = t + 1` construction, under which step 0 could never be probed and step 1 received two grant opportunities (R5-23).

**Epoch grid [N].** A unit anchored at `t_p` closes at the `update` for step `t = t_p + max(ℋ) − 1 = t_p + 2`, the earliest step whose `obs` supplies `O[t_p+3]`. With anchors on multiples of Π = 20 the grid is **t ≡ 2 (mod 20)**: t = 22, 42, …, 1982 — **99 epochs** in a 2,000-step episode. Outputs are recomputed at an epoch and held between epochs. **Emissions for alarm bookkeeping are exactly the epochs** (§5).

## 3. Probing, allocation and the estimator RNG [N]

**Block-periodic single-step probes, L = 1, Π = 20.** A probe step is an environment step whose applied action is **replaced** (contract §0); the generator does exactly this (`np.clip(actions[t], …)` in place of `policy(...)`), so the probe magnitude 1.0 is never clipped at `a_max = 2.0`.

**Grant rule [N].** Grant at `t_next` iff

  `used + 1 ≤ floor(probe_budget · t_next)`  **and**  `t_next − t_last ≥ Π`,

with `used = 0`, `t_last = −Π` at reset; integer arithmetic; no reservoir, no adaptive element, no dependence on state, observations, the task policy, `u_t`, G or `ρ_u`. The invariant `used(t) ≤ floor(0.05 · t)` holds after every step (**T-IBD-budget**).

**Consequence on the frozen 0-indexed clock [N] (corrects R4-23, R5-GM-08, R5-23, R5-CX-12).** Grants fall on `t ∈ {20, 40, …, 1980}`: **99 probes applied per 2,000-step episode, fraction 99/2000 = 0.0495**, all 99 units closing at t ≤ 1982 ≤ 1999. *(diagnostic: reproduced exactly.)*

Draft 4's "100 applied, of which the probe at t = 2,000 closes no unit, leaving 99 units" described a 1-indexed environment. **On the generator there is no step t = 2000, so the terminal probe never happens and R4-23's "declared waste" does not exist.** What does exist, and is declared instead, is a **one-probe under-spend at the start**: `floor(0.05 · 0) = 0` forbids a grant at t = 0, so the arm spends 0.0495 rather than 0.0500 of the budget. The cost is 1 % of the allowance and 1 unit of 100. It is **not** repaired by a special first-step rule, because such a rule would break the `floor` invariant that makes the budget an invariant rather than an average. `T-IBD-count` asserts the count, the grant set and the fraction.

**Allocation: balanced pre-randomised blocks (D-10.4) [N].** Let `ALLK = [(0,+1), (0,−1), (1,+1), (1,−1), …, (K−1,+1), (K−1,−1)]` — the contract's frozen probe order (+e_1, −e_1, …, +e_K, −e_K), 2K entries. When a grant is made and the block is empty, refill it:

```
perm  = rng.permutation(2*K)            # a permutation of the integers 0..2K-1
block = [ALLK[i] for i in perm]         # list of (k, sign) pairs
```

and **consume `block` from index 0 upward** (FIFO). Draft 4's pseudo-code used `block.pop()`, which consumes from the right; both are uniformly random but they are **different streams**, and three implementations must draw identically. The FIFO rule is normative. The block is not carried across episodes: at reset the block is empty and the RNG is fresh.

**Estimator RNG [N] (closes R5-17, R5-CX-14).** Exactly one `numpy.random.Generator` exists in this arm:

  `rng = numpy.random.default_rng([probe_ns, instance_seed, episode_seed, arm_id])`

- `probe_ns = 5477` **[prov]**, a fixed integer namespace that domain-separates this stream from the generator's, whose keys are `[seed, 0]`, `[seed, ep, VAR_ID[var], t]`, `[seed, 555]` and `[seed, 777]`.
- `instance_seed` is the **certified sub-seed actually returned by `draw_certified`** (`inst.seed = configuration_seed · 1000 + n_resamples`), not the configuration seed: a resample changes the plant, so it must change the allocation key.
- `episode_seed` is the generator `ep` of the episode being run.
- `arm_id = 1` for `seq_ibd`. The **probed comparator** (contract §H(3), `cusum_linear_delay_aware_probed`, `arm_id = 3`) must receive *this arm's* stream, so it is generated with **`arm_id = 1`** and asserted bitwise equal to arm 1's (**T-IBD-rng**). Arm 2 draws no probes.
- The key **excludes the confounder condition**: the G = 0 run of an instance uses the identical allocation, so present/absent are within-instance contrasts on identical probe streams (contract §G, F7).
- The generator is created once, in the constructor, **never re-seeded and never re-created**; it is consumed **only** by `rng.permutation` in `request_probe`. The arm has no other stochastic element: given the transition stream and the frozen artefacts (ā, v, g, h) every output is deterministic.

**Pre-computed allocation is permitted [N].** Because the allocation is state-independent, a harness may compute the whole episode's `actions` dict before calling `Instance.run` instead of calling `request_probe` online. The two are required to be **bitwise identical**, and `T-IBD-count` asserts it. All three round-5 implementations took the pre-computed route; making it legal removes an undeclared divergence.

**Consequence.** A window of `n_u` consecutive units contains ≥ `floor(n_u/2K) − 1` complete blocks, so every (k, sign) group has at least that many members. At K = 2, `n_u = 25`: each group holds **5 to 7** units, so `min(n₊,n₋) ≥ 5 > n_min_sign = 3` in every **full** window. `n_min_sign = 3` is **retained as a guard that should never bind on a full window**, and that it never binds there is asserted, not assumed (**T-IBD-blocks**). It **does** bind on the 24 partial windows that open every episode (R5-24) — that is expected and harmless, because `stat = 0` on the whole warm-up prefix anyway (§5) and `a_c` is reported with its eligibility mask.

**Scaling rule [N].** `W_steps` must satisfy `floor(W_steps/(Π·2K)) ≥ n_min_sign + 1`, i.e. **`W_steps ≥ 8K·Π = 160K`**. Satisfied at K ≤ 3 by `W_steps = 500`; at K > 3 raise `W_steps` and recompute §8's tables. Pendulum-v1 (K = 1) and PointMass2D (K = 2) are inside the rule.

**Eligibility mask [N].** Unit closure is simultaneous across ℋ, so count-eligibility depends on k alone, but the mask is returned indexed `(k, h)` as `eligibility_mask[K][|ℋ|]`, with `n_units` and `n_eligible_cells`, in the ledger every epoch. A cell is **eligible** iff `min(n₊,n₋) ≥ n_min_sign`, **non-degenerate** iff `σ_U > 0`. `a_c = 0` from ineligibility is therefore distinguishable from `a_c = 0` on a genuinely unresponsive channel.

**Jitter: rejected, with reason.** Jitter would break the `floor(0.05·t)` invariant, the 25-unit count and the fixed epoch grid, and would make §8's offset table data-dependent. The aliasing concern — a periodic 20-step comb against a control-tier resonance — is carried as a **declared limitation** (§11) with a pilot diagnostic against the closed-loop spectrum, not repaired by jitter.

**No washout, and why — kept, with two caveats.** The argument survives: **both groups are probe units** and the label comes from a device that never reads state, so an earlier probe's slow-mode tail is a shared nuisance, not an arm asymmetry. Two caveats are normative.

1. **Residual dependence.** Units share one trajectory; the |ℋ| increments at one anchor overlap; a probe's tail enters later units. The z is therefore **not claimed to have exact level**, and the primary never uses z as a p-value. Round-4's 3,000-replicate AR(1) attack at ρ ∈ {0.8, 0.95} gave 4.4–5.4 % two-sided exceedance against nominal 5 % — a bounded check, not a proof. R5-GM-06 (settling residue at Π = 20 destroys exchangeability) was adjudicated as a **caveat, not a defect**: the sign randomisation makes both sign groups share the settling residue, so the residue adds variance, not bias; recorded in §13 as such.
2. **Balanced-block consequence.** Under i.i.d. draws the conditional history given `S_p = +` and `S_p = −` was exactly identical. Under blocks it is not: within a block a `(k,+)` probe cannot follow another `(k,+)`, so an earlier `+e_k` tail lands **preferentially in the `−` group**. The induced correlation is O(1/(2K−1)) and the carry-over is bounded by body decay over one cadence — at the generator's `rho_b = 0.85`, `0.85²⁰ = 3.9·10⁻²`, differenced further by the increment. Direction: for a channel genuinely reached by k it **attenuates** |z| (conservative, costs power); for the long-lag confusion of §11 it can flip the sign of z while leaving |z| elevated, so that failure mode is unchanged in kind. Declared, not repaired.

## 4. Statistic [N]

**Window.** Trailing `W_steps = 500` steps **on anchor time**, half-open: `t_p ∈ (t_p* − W_steps, t_p*]`, exactly **25 units** in steady state. The window **never resets** — the estimator does not know the event time, and a reset would make the statistic path h-dependent.

**Per (channel c, horizon h, actuator k).** Group `+` = signed increments `D_c^h(t_p)` of window units probed with `+e_k` (n₊); `−` likewise (n₋); N = n₊+n₋. Ineligible cells contribute nothing. Rank the N values jointly with **mid-ranks**; R₊ = rank sum of `+`.

  U = R₊ − n₊(n₊+1)/2  μ_U = n₊n₋/2

  **σ_U² = (n₊n₋ / (N(N−1))) · [ (N³−N)/12 − Σ_g (t_g³−t_g)/12 ]**,  **σ_U ← sqrt(max(0, σ_U²))**

over distinct tied values g with multiplicity t_g. **Tie rounding:** tie groups are formed on increments rounded to 12 significant decimal digits (`float(f"{v:.11e}")`); the `max(0,·)` guard makes the −10⁻¹⁷ cancellation unreachable. No continuity correction (declared). σ_U = 0 ⇒ degenerate cell, contributes nothing.

  **z_{c,k,h} = clip((U − μ_U)/σ_U, −8, +8)**;  **`a_c` = max over eligible, non-degenerate (k,h) of |z|**, else 0.

`a_c` is a max of up to K·|ℋ| = 6 values, so its null mean is positive, not zero (round-4 measurements: non-reachable ≈ 1.44–1.54, indirect ≈ 1.78–1.87, direct ≈ 2.65–2.69). Discrimination comes from separation, not from a null-centred scale. A NaN reaching any output is a hard error, never a silent 0. **Exact by construction of the randomisation device:** the allocation is independent of state, task policy, `W_u`, `ρ_u` and G. **Not claimed:** exact rank-sum level across the window.

**At τ = 2 the max is still over all K·|ℋ| cells [N] (corrects R5-18).** The information set excludes τ, so the arm cannot drop h = 1 and h = 2. At τ = 2 those two horizons carry no signal on any channel and contribute pure noise to a maximum over 6 cells, which **raises the null floor** on every channel — reachable and unreachable alike. Draft 4 §8(3) said "`a_c` is a max over K cells, not K·|ℋ|", which describes an arm that knows τ; that sentence is withdrawn. The floor inflation is a power cost, not a validity cost, and it applies symmetrically, which is why the arm's measured AUC at τ = 2 is not below its τ = 0 value.

`p_c = g(a_c)` every step from a cache refreshed at every epoch; **no state ever freezes `p_c`**.

## 5. Alarm channel, warm-up, and the ARL_0 clock from reset [N] (D-11.5)

**Warm-up.** **`n_warm = W_steps/Π = 25` complete units.** `stat_t = 0` — hence `raise = 0`, the harness's h grid being strictly positive — **until the window holds ≥ n_warm complete units**. Thereafter `stat_t = max_c |a_c(t) − ā_c| / v_c`, recomputed at each epoch and held between epochs. The 25th unit is anchored at `t_p = 500` and closes at **`t_warm = 502`**, which is on the epoch grid and satisfies `t_warm < event_t = 1000`. *(diagnostic: the first epoch holding 25 units is exactly t = 502.)* An epoch with zero eligible cells on every channel holds `stat`, forces `raise = 0`, and is flagged `degenerate_epoch`.

The warm-up exists because without it `a_c ≡ 0` on every channel during the prefix while `ā_c` is fitted on full windows, so `stat_warm = max_c ā_c/v_c` was the largest value the statistic ever took and ARL_0(h) was a two-valued step function with no root in the D-2a band. With `stat = 0` on the prefix, and balanced blocks guaranteeing eligible cells after it, the post-warm-up `stat` has a continuous distribution, so **ARL_0(h) is continuous and non-decreasing and the bisection has a root** (**T-IBD-mono**, **T-IBD-arl**).

**Emissions and alarm bookkeeping [N] (closes R5-CX-10).** The arm declares `persistence_unit = "epochs"` and `emission_grid = "t ≡ 2 (mod 20)"`. The harness takes the arm's returns **at those steps only** as its emission sequence — `raises[i]` = the `raise` returned at epoch step `times[i]`, `times = (22, 42, …, 1982)` — and applies

  `contract_ref.count_alarms_timed(raises, times, p = 3, r = 20)`

with **persistence p = 3 in epochs (consecutive emissions)** and **refractory r = 20 in environment steps**. Draft 4's claim that this can be done "once via `count_alarms`" is false: `count_alarms` runs `t`, `run` and `block_until` in one index space, so on an epoch stream `r = 20` would mean 20 epochs ≈ 400 steps. `count_alarms` is retained only as the step-cadence special case, and `count_alarms(raw, p, r) == count_alarms_timed(raw, range(len(raw)), p, r)` is asserted (**T-IBD-timed**).

**Declared consequence of r = 20 steps at Π = 20 steps.** The epoch stride equals the refractory, and `count_alarms_timed` blocks emissions at `t ≤ t_a + r`, so a counted alarm suppresses **exactly one** subsequent epoch. For this arm the refractory is therefore worth one epoch, not a meaningful dead time; `r = 20` was chosen in the registry for step-cadence arms. Under continuous raising the counted alarms are 80 steps apart (3 epochs to re-accumulate p plus 1 suppressed). *(diagnostic: counted alarms at 542, 622, 702, 782.)* This is declared, not repaired: changing `r` for one arm would break the matched-ARL_0 comparison.

**ARL_0 clock starts at RESET (t = 0) and the prefix is charged [N] (D-11.5).** The fresh-start run length is `contract_ref.run_length_from_reset(counted_alarm_times, stream_end)`: environment steps from t = 0 to the first counted alarm, **including the 502-step warm-up prefix**, or `(stream_end, True)` if right-censored. Draft 4's row-19 justification — *"a run length that cannot alarm is not a run length"* — is **withdrawn by decision** (§13). The honest statement is the one D-11.5 adopts: an arm that needs 502 steps before it can raise pays for them, because a user who resets the monitor is exposed for those steps.

**Structural floor.** The earliest possible counted alarm from reset is at **t = 542**: epochs 502, 522, 542 are the first three that can raise, and p = 3 completes at 542. *(diagnostic: `run_length_from_reset` returns (542, False) on an all-raise-after-warm-up stream.)* So ARL_0(h) ∈ [542, T_arl] for every h, the target band [900, 1100] is not structurally excluded, and h is smaller under D-11.5 than it would have been under draft 4's convention — the arm must run at a **more sensitive** operating point to reach the same fresh-start ARL_0.

**D-2a protocol consequence, recomputed [N] (replaces draft 4 §4's paragraph; closes R5-GM-05, R5-14).**

- Calibration uses dedicated **event-free** streams of length **`T_arl = 3000` [prov]** from the instance's ARL split (§7), probed exactly as a scored episode is. Nothing in this arm depends on `episode_len`, so a 3,000-step stream is legal: grants continue at t ∈ {20, …, 2980}, epochs at t ≡ 2 (mod 20) up to 2982.
- The number of fresh starts is `n = max(400, ceil((1.96 · ŝd / 100)²))`, where `ŝd` is the observed run-length standard deviation, and D-2a's band condition (95 % interval for the mean inside [900, 1100], i.e. half-width ≤ 100) is checked on the realised interval. D-2a's fixed floor of 400 suffices only if `ŝd ≤ 1020`; the arm's run lengths are over-dispersed relative to a geometric because consecutive epochs share 24 of 25 units, so the fixed floor is treated as a floor and not as the answer (R5-14).
- Budget: at n = 400 and `T_arl = 3000` the cost is 1.2 × 10⁶ steps, 60 % of D-2a's 2 × 10⁶ cap; the cap permits n ≤ 666 at that stream length, which covers `ŝd ≤ 1317`. Above that the arm does **not** attain the band and is reported as the predeclared D-2a **partial-order endpoint** (its best attainable (ARL, HPDT) pair), never excluded.
- Censoring: with a target mean of 1,000 from reset the conditional post-warm-up mean is ≈ 498, so under a geometric approximation P(no alarm by 3,000) ≈ exp(−(3000 − 542)/498) ≈ 0.7 %. That is an estimate; the **realised censoring fraction is measured and reported per cell and never dropped**.
- Prefix overhead: 400 × 502 / 1.2 × 10⁶ = **16.7 %** of this arm's calibration budget is warm-up in which it cannot alarm. It is **charged, reported, and never subtracted**.
- Under D-11.6 the threshold h is per `(cell, instance_seed, confounder, arm)`, so the calibration is repeated per instance: 4 base cells × 10 instances × 2 confounder conditions × 1.2 × 10⁶ ≈ **9.6 × 10⁷ environment steps for this arm's alarm channel alone**. Contract §0's ARL_0 row still says calibration is "shared across seeds", which contradicts D-11.6's per-instance h; §14(b) records the conflict and this spec follows D-11.6, the later decision. The cost belongs in the runtime pilot (contract §I) and is flagged there. **The primary and co-primary do not depend on h at all**, so if this budget binds, what is lost is the descriptive alarm comparison, not the outcome the arm is confirmed on.

**h-independence.** `stat` is a deterministic function of the stream and the frozen artefacts — no accumulation, reset, burst or online re-estimation — so the harness records **one** `stat` stream per calibration episode and evaluates every h by offline replay (**T-IBD-hindep**); the D-2a cap is per calibration key, not per h. *(Opinion: consecutive epochs share 24 of 25 units, so the raise sequence is strongly autocorrelated and p = 3 filters little — h does essentially all the work. The harness should also report the p = 1 epoch sequence from the same stream, at zero cost.)*

## 6. Primary outcome: the pre-event support [N] (D-11.1a)

**What is scored.** At each offset in `offsets_rank` (primary 500) after the confirmatory event, the evaluator computes

  `contract_ref.auc_pre_event_support(raw_support, S_obs_eps_pre, S_obs_eps_post)`

— the mid-rank Mann-Whitney AUC of `raw_support = a_c` **restricted to the channels of S^obs,ε(pre)**, with **positives = channels still in S^obs,ε(post)** and **negatives = the lost set S^obs,ε(pre) \ S^obs,ε(post)**. `S_obs_eps_pre` is `Instance.S_obs_pre_event()`, stored at draw time; `S_obs_eps_post` is `S_obs()` re-certified after the event. CL-4 is now certified by construction and by `certify()` (`s_change`, `n_lost`), so the negative class is non-empty. Ties receive **half credit** — load-bearing, because this arm assigns `a_c = 0` to unresponsive and ineligible channels by design.

`secondary_support()` returns the same vector; the **secondary full-channel AUC** is `auc_prob_superiority(a_c, S^obs,ε(post))` over all C channels, co-reported with AUPRC and prevalence (contract §G). Channels outside the pre-event support — padding, world, confounded and unconfounded distractors — **do not enter the primary at all**.

**What `a_c` does on a lost channel [N, mechanism].** The window never resets and holds 25 units spanning 500 steps of anchor time. A channel c in the lost set was reached by the event actuator (`event_actuator = 0`) and by no other, so:

- **Pre-event units** anchored at `t_p < event_t` carry a genuine sign contrast at (k = 0, h) on channel c: the `+e_0` group's increments are systematically displaced from the `−e_0` group's, so |z_{c,0,h}| is elevated and `a_c` sits well above the null floor.
- **Post-event units** anchored at `t_p ≥ event_t` carry none: column 0 of B is zero, so both sign groups are draws from the same distribution at every (k, h).
- Between them the window is a **mixture**. As post-event units replace pre-event ones at one unit per 20 steps, the fraction of the rank-sum's evidence that carries the contrast falls linearly from 1 to 0, and `a_c` **decays from its pre-event level toward the null max-of-|z| floor** — the same floor a never-reachable channel sits on (round-4: ≈ 1.44–1.54 at K = 2, |ℋ| = 3). It does not decay to zero; `a_c` is a maximum of six |z| values and its null mean is positive.
- **Retained channels do not decay**: they are still reached by some surviving actuator, so their (k, h) cells keep their contrast in both halves of the mixture.

The primary is exactly the separation this creates: after the event the lost channels fall toward the floor while the retained channels stay above it.

**Expected pre/post mixture at each offset, from the epoch grid [N].** The read at offset Δ is the **last epoch ≤ event_t + Δ**; the window is `(t_p* − 500, t_p*]`, whose anchors are `t_p* − 480, …, t_p*`; and the post-event count is `n_post(t_p*) = clip(floor((t_p* − event_t)/20) + 1, 0, 25)` for `t_p* ≥ event_t`.

| Offset after event | **200** | **500** | **1000** |
|---|---|---|---|
| Epoch read (event_t = 1000; grid t ≡ 2 mod 20) | 1182 | 1482 | 1982 |
| Newest anchor in window | 1180 | 1480 | 1980 |
| Oldest anchor in window | 700 | 1000 | 1500 |
| **Post-event units / 25** | **10** | **25** | **25** |
| Post-event fraction | **0.40** | **1.00** | **1.00** |
| Expected `a_c` on a lost channel | 60 % pre-event evidence: **elevated, partially decayed** | floor | floor |

*(diagnostic: table reproduced exactly. The post-event ramp is n_post = 1 at epoch 1002 and +1 every 20 steps, so the **first fully post-event epoch is 1482 — offset 482** — and offset 500 is the earliest offset in `offsets_rank` at which the window carries no pre-event evidence at all.)*

**Offset 200 is a transition window** and is reported with its 0.60 pre-event fraction, never as a clean post-event outcome; the primary at 200 is expected to be *lower* than at 500 for exactly this reason. Boundary sensitivity is declared: under the opposite convention (an anchor at `t_p = event_t` counted as pre-event) the fractions are 0.36 / 0.96 / 1.00. This is a property of any probe-budgeted windowed estimator and **must not be repaired by shortening `W_steps` after seeing outcomes**. The offset-1000 read is the last epoch of the episode (1982); there is no transition at t = 2000 and none is invented (R5-CX-12, R5-26).

**Why a fit-time constant scores 0.5, and this arm does not [N].** A statistic that is **constant across the channels of S^obs,ε(pre)** ties on every positive–negative pair, and the mid-rank rule gives every tie half credit, so its AUC is **exactly 0.5** — deterministically, per episode, in every cell. That is the property contract §G asserts, and it is the reason D-11.1a makes this the primary: nothing that ignores the scored episode can score above chance by being good at static structure. This arm scores above 0.5 because `a_c` is recomputed from the trailing window at every epoch: the lost channel's evidence is *removed by the event* and the window forgets it over 500 steps, while the retained channels' evidence is not. The arm is credited for the decay, and for nothing else.

**Honest qualification, which contract §G does not make [N].** The 0.5 result holds for a statistic constant **across channels**, not for every "fit-time constant". A per-channel vector fixed before the scored episode (the static loading `l_c`, or any pre-event ranking) is constant in *time* but not across channels, and its pre-event-support AUC is whatever its own ordering gives — a number fixed per instance, not 0.5. On the frozen generator it is systematically **below** 0.5, because CL-4 is enforced structurally by making `event_actuator = 0` the sole driver of its dominant body component, so the channel the event removes is typically one of the *strongest* pre-event channels. *(diagnostic, 20 certified draws, N_x = 10, τ ∈ {0,2}: the lost channel's rank in the pre-event operational-effect ordering is 1st in 10 of 23 lost channels and ≤ 2nd in 17 of 23; the pre-event-support AUC of a vector monotone in the pre-event effect is mean 0.212, range [0.000, 0.600].)* Contract §G's harness assertion that the static-structure control "must score 0.5 ± Monte Carlo in every cell" is therefore **correct only under the constant-across-channels reading**; under the round-5 reading (a static loading *vector*) it will fail. §14(a) records this as a contract-side item. This spec asserts the version that is true: **`T-IBD-primary` asserts exactly 0.5 for a channel-constant, and asserts that a per-channel fit-time vector reproduces its own pre-event ordering's AUC — not 0.5.**

**Granularity, declared [N].** On the frozen generator *(diagnostic, seeds 0–9)*, `|S^obs,ε(pre)|` is **4 to 6** channels and `n_lost` is **1** (occasionally 2), so the per-episode primary is an AUC over 3–5 positives against 1–2 negatives and takes values on a lattice of at most six points (plus tie half-credits). It is coarse and noisy at the episode level. **The confirmatory margin is assessed on intervals clustered by instance, never on a single episode**, and cells are never pooled. Contract §D says the same. A consequence the contract does not state, and this spec declares: the D-10.3 competence floor of 0.85 was set against the old full-channel statistic over 24–44 channels and has been transplanted onto a 4–6-channel statistic without re-derivation; on a 6-channel/1-negative episode the attainable values straddling it are 0.8 and 1.0. §14(c).

## 7. Per-instance fitting: splits, alarm reference, calibrator [N] (D-11.6)

**Nothing is pooled across instances.** Every learned artefact of this arm — `ā[C]`, `v[C]`, the harness-fitted calibrator `g`, the tier-2 operating point `θ*`, and the threshold `h` — is fitted on **that instance's own fault-free fit split**, and the ledger records the key `(cell, instance_seed, confounder, arm)` together with the fit-split episode seeds on every artefact. An artefact fitted on instance A is never applied to instance B; a fixed set of ten instances in one cell has ten independent sets of artefacts, because they are ten independent SCM draws with different `A_b`, `B` and `C_d` (R5-CX-06, R5-20).

**Confounder-absent rule [N].** The G = 0 arm of an instance is the **same instance draw and the same noise streams** with `G[:] = 0` and `W_u` unchanged (contract §G, F7), and it gets its **own separate fit** of every artefact on the same fit-split episode seeds. Present and absent share the probe allocation (§3) and differ only in G. Present/absent artefacts are never shared or averaged.

**Episode-seed rule [N].** Fixed here so three implementations use the same data. All sets are disjoint from each other, from the scored seeds, and from the generator's reserved oracle episode ids `{996, 997, 998, 999}`.

| Split | generator `ep` | count | event | used by |
|---|---|---|---|---|
| **Scored** | 0 … 3 | 4 | event-carrying at `event_t = 1000` | the primary, co-primary, secondary |
| **Alarm reference** | 200 … 223 | 24 | **event-free** | `fit_alarm_reference` → (ā, v) |
| **Calibrator fit** | 300 … 323 | 24 | event-carrying | harness fits `g` (contract `cal_split` first half) |
| **Operating-point validation** | 400 … 415 | 16 | event-carrying | harness picks `θ*` (contract `cal_split` second half) |
| **ARL_0 calibration** | 500 … 899 | 400 | **event-free**, length `T_arl = 3000` | harness bisects `h` (§5) |

If the observed run-length dispersion forces `n > 400` (§5), the ARL split extends upward from `ep = 900`; it never overlaps any other set.

**Instance reuse is a trap and is closed [N] (R5-22).** `Instance.apply_event` mutates `self.B`, `self.avail` and `self.gain` **in place with no undo**, and `run(..., event_t=...)` calls it mid-rollout. **Every event-carrying rollout must start from a fresh `copy.deepcopy` of the certified draw**, and `S^obs,ε(post)` must be read from the mutated copy while `S^obs,ε(pre)` is read from the certified object's `S_obs_pre_event()`. A harness that loops `for ep in range(4)` on one instance silently runs episodes 1–3 with the actuator already dead from t = 0, giving a pre-event segment that is not fault-free and corrupting the alarm reference, the ARL clock and every offset. **T-IBD-instance-reset** asserts that two consecutive event-carrying rollouts on one certified draw have identical pre-event segments.

**Alarm reference [N].** Frozen at pass 0, per instance and confounder condition: `ā_c` = median `a_c`, `v_c` = max(1.4826 · MAD, `v_floor` = 0.5), over the **full-window epochs of the 24 event-free alarm-reference episodes**: `t_p* ∈ {500, …, 1980}` = **75 epochs per episode**, **1,800 epochs per instance per channel**, pooled per channel. Draft 4 pooled pre-event segments of both event-carrying and event-free episodes across a whole cell (1,200 epochs per cell); draft 5 uses only fault-free streams, per instance, as interface v5's `fit_alarm_reference` requires ("the instance's own arm-specific fault-free stream, probed for the probed arm"). No post-event data reaches (ā, v) by construction.

**Calibrator [N].** `g` is a **single pooled** non-decreasing isotonic (PAVA) map over all channels on [0, 8], **fitted by the harness** — which owns the labels — **per instance and confounder condition** on the 24 **calibrator-fit** episodes, on pairs `(a_c(t), 1[c ∈ S^obs,ε_t])`, injected via `configure(calibrator_params)`. **Post-event states are included**, because the post-event label distribution is what the calibrator must map; **straddling epochs are excluded**, applying §4's window-purity rule to `g`. Retained per event-carrying episode: `t_p* ∈ {500,…,980}` (25, all pre-event) ∪ `{1480,…,1980}` (26, all post-event) = **51**; **24 × 51 = 1,224 epochs per instance per channel**. Fitted values clamped into [0.001, 0.999] so log loss is finite. The operating point `θ*` for secondary F1 is chosen on the separate 16-episode validation split; both artefacts frozen before scoring. **The primary tier uses neither** — the pre-event-support AUC is invariant to any monotone calibrator, so it consumes no supervised data.

Pooling over channels within an instance is justified because **a channel's label is near-constant within an episode**, so a per-channel isotonic map would be degenerate. The cost is declared: pooling across heterogeneous channel types (padding, live w, confounded x, body b, downstream d) is **mis-calibrated per type**. This affects **tier 2 only**; per-type reliability is a tier-2 diagnostic.

**Passes [N].** *Pass 0:* `configure({None, None, None})`; `fit_predictor` no-op; `fit_alarm_reference` on the instance's alarm-reference split computes (ā, v); the estimator emits `p_c = a_c/8` clipped, never scored; the harness runs the calibrator-fit split and fits `g` from the returned `raw_support` stream and the oracle labels; the harness runs the ARL split and bisects `h`. *Pass 1:* `configure({None, {g_knots}, {ā, v}})`; `set_threshold(h)`; run the four scored episodes. `set_threshold` touches nothing but the comparison in §5, so `raw_support`, `p_c`, the primary and the co-primary are invariant to h and to the ARL_0 sweep.

## 8. Offsets and window memory [N]

Primary and co-primary at **`offsets_rank` = `offsets_P2` = {200, 500, 1000}, primary 500** (contract §0; note that contract §G's P2 paragraph still names {10, 50, 200}, §14(d)). The read convention is stated once, in §6: **the last epoch ≤ `event_t + Δ`**, giving 1182 / 1482 / 1982, with the window mixture in §6's table. The event applies **before** step `event_t` is taken (`Instance.run` calls `apply_event` at the top of the iteration for `t == event_t`), so an anchor `t_p ≥ event_t` is post-event.

`p_c` at offset Δ is read at the same epoch. The co-primary P2 (mean `p_c` over oracle-labelled confounded distractor channels) is unaffected by D-11.1a's restriction, because it is defined on distractor channels, which are outside `S^obs,ε(pre)` by construction; unconfounded distractors remain the negative control, and each offset is reported with the fraction of runs for which it exists.

**Window memory, declared.** The window never resets, so a second event within `W_steps` is read through a mixed window and multi-event schedules are exploratory for this arm (§11). No reset is added: it would reintroduce h-dependence and make the ARL_0 replay in §5 invalid.

## 9. Parameters [N]

No parameter may change after the pilot without re-running ARL_0 calibration, the isotonic fit and the acceptance suite (contract E6). **There is no outcome-dependent tuning clause.** `[prov]` marks a value this spec introduces that is not in the registry and is not yet pilot-justified.

**Inherited from contract §0, not this spec's to choose (20):** ε, H, ℋ, 𝒜, a_max, probe_budget, p, r, w_T, H_det, ARL_0, episode_len, event_t, offsets_rank, offsets_P2, n_min_sign, cal_split, τ, replication (10 × 4), primary support set (S^obs,ε(pre)).

| # | Symbol / choice | Value | Status | Justification |
|---|---|---|---|---|
| 1 | L (probe block length in steps) | 1 | frozen | Maximises independent units at fixed budget. |
| 2 | Π (cadence) | 20 | frozen, derived | = L / probe_budget; spends the budget to the `floor`. |
| 3 | reservoir_0 | 0 | frozen | Makes `used ≤ floor(0.05·t)` an invariant, not an average. |
| 4 | **Estimator clock** | **`t_next` = index of the step about to be taken; `t_next = 0` at reset, +1 per `update`; grant tested at `t_next`; 0-indexed against `Instance.run`** | **frozen (changed)** | Removes draft 4's `tp = t+1` off-by-one (R5-23, R5-CX-12). |
| 5 | Probe allocation | balanced pre-randomised blocks over (k, sign), length 2K, uniform order, estimator RNG, state-independent | frozen | Removes whole-actuator deletion in a window; keeps C→a severance (T-E2d). |
| 6 | **Block RNG seed** | **`numpy.random.default_rng([probe_ns, instance_seed, episode_seed, arm_id])`; one Generator per (instance, episode, arm), never re-seeded; `instance_seed = inst.seed` (the certified sub-seed); key excludes the confounder condition** | **frozen (new)** | Three implementations must draw identical blocks (R5-17, R5-CX-14). |
| 7 | **`probe_ns`** | **5477** | **[prov] (new)** | Namespace separating this stream from the generator's `[seed,0]`, `[seed,ep,VAR_ID,t]`, `[seed,555]`, `[seed,777]`. Arbitrary but frozen; no registry constant exists. |
| 8 | **`arm_id`** | **`seq_ibd` = 1; the probed comparator replays this arm's stream using `arm_id = 1`; arm 2 draws none** | **frozen (new)** | Makes arm 3's defining property ("bitwise the same stream as arm 1") testable (R5-17). |
| 9 | **Block consumption order** | **`block = [ALLK[i] for i in rng.permutation(2K)]`, consumed from index 0 upward (FIFO); `ALLK` in the contract's probe order (+e_1, −e_1, …)** | **frozen (new)** | Draft 4's `block.pop()` is a different stream; the choice must be fixed, not left to taste. |
| 10 | Cadence jitter | none | frozen | Would break the budget invariant, the 25-unit count and the epoch grid. |
| 11 | W_steps | 500, subject to `W_steps ≥ 160K` | frozen + derived rule | 100 % post-event at offset 500 (first fully post-event epoch 1482); rule guarantees `min(n₊,n₋) ≥ 5` on full windows. |
| 12 | Window endpoint rule | half-open on anchor time, `t_p ∈ (t_p* − W, t_p*]` | frozen | Gives exactly 25 units; removes endpoint ambiguity. |
| 13 | Observation anchor | `O[t] = prev_obs`; `D^h = O[t_p+h] − O[t_p]` | frozen | Matches contract C and the generator; first hit at h = τ+1. |
| 14 | Epoch trigger | `t = t_p + max(ℋ) − 1`; grid t ≡ 2 (mod 20); 99 epochs per 2,000 steps | frozen | Earliest step whose `obs` supplies `O[t_p+3]`. |
| 15 | **Emission grid and units** | **one emission per epoch; `persistence_unit = "epochs"`; harness applies `count_alarms_timed(raises, times, p = 3, r = 20)` — p in epochs, r in environment steps** | **frozen (new)** | `count_alarms` cannot express mixed units (R5-CX-10). |
| 16 | Increment sign | signed | frozen | Absolute increments discard the contrast the randomisation creates. |
| 17 | Tie correction | mid-ranks, §4 formula | frozen | One of two conventions in circulation; declared. |
| 18 | Tie rounding / variance guard | 12 significant digits (`float(f"{v:.11e}")`); `sqrt(max(0, σ_U²))` | frozen | Removes the −10⁻¹⁷ `ValueError`; fixes the rounding call so implementations tie identically. |
| 19 | Continuity correction | none | frozen | Immaterial to a rank-preserving primary. |
| 20 | z_cap | 8 | frozen | Bounds the calibrator domain and `stat`. |
| 21 | Aggregation | max over eligible, non-degenerate (k, h) of \|z\|, **all K·\|ℋ\| cells at every τ** | frozen | Contract §H; the arm does not know τ (R5-18). |
| 22 | `a_c` with no eligible cell | 0, with the eligibility mask returned | frozen | Bottom knot of g, not a NaN; the mask makes 0 interpretable. |
| 23 | n_warm | 25 complete units (`t_warm = 502`) | frozen | `stat = 0` before it; makes ARL_0(h) continuous. |
| 24 | **ARL_0 clock start** | **reset, t = 0; the 502-step prefix is CHARGED, never subtracted; `run_length_from_reset`** | **frozen (changed, D-11.5)** | Both arms face the same exposure; draft 4's exclusion is withdrawn by decision (§13). |
| 25 | **`T_arl`** | **3000 steps per fresh-start calibration stream; `n = max(400, ceil((1.96 ŝd/100)²))`** | **[prov] (new)** | D-2a fixes a run-length count and a step cap but no stream length; 3,000 gives ≈ 0.7 % expected censoring at the target mean (R5-GM-05, R5-14). |
| 26 | **Fit hierarchy** | **every artefact per `(cell, instance_seed, confounder, arm)`; nothing pooled across instances or confounder conditions** | **frozen (new, D-11.6)** | Ten instances in a cell are ten different plants (R5-CX-06, R5-20). |
| 27 | **Fit-split episode seeds** | **scored 0–3; alarm reference 200–223 (event-free); calibrator fit 300–323; operating point 400–415; ARL 500–899 (event-free, extends from 900)** | **frozen (new)** | Disjoint by construction and from the generator's reserved ids {996–999}. |
| 28 | g | single pooled isotonic (PAVA) over channels, harness-fitted, **per instance** | frozen | Labels near-constant within an episode ⇒ per-channel fits degenerate. |
| 29 | g fit domain | non-straddling full-window epochs; post-event included; 51 per episode, 1,224 per instance per channel | frozen | Applies §4's purity rule to `g`. |
| 30 | g clamp | [0.001, 0.999] | frozen | Keeps log loss finite. |
| 31 | ā_c | median over the instance's **event-free** alarm-reference split | frozen (changed) | Interface v5's `fit_alarm_reference` takes a fault-free stream; no post-event leakage by construction. |
| 32 | v_c / v_floor | max(1.4826 · MAD, 0.5) | frozen | A MAD below 0.5 marks a degenerate channel. |
| 33 | Alarm-reference segment | full-window epochs `t_p* ∈ {500,…,1980}` of 24 event-free episodes = 75 per episode, 1,800 per instance per channel | frozen (changed) | Per-instance replacement for draft 4's per-cell pool of 1,200. |
| 34 | h | set by harness per `(cell, instance_seed, confounder, arm)` | **calibrated** | The single scalar knob; fresh-start ARL_0 = 1000 from reset under D-2a + D-11.5. |

**Honest count: 34 arm parameters on 34 rows — 31 frozen, 2 [prov] (`probe_ns`, `T_arl`), 1 calibrated (`h`).** Plus 20 inherited contract constants and **4 fitted objects** frozen before pass 1, all per instance and confounder condition: `g` and `θ*` (harness), `ā[C]` and `v[C]` (estimator, exported and re-injected). Draft 4's 26 rows grow by 8: the estimator clock is restated (row 4), and rows 6, 7, 8, 9, 15, 25, 26, 27 are new; rows 24, 31 and 33 change value or scope. Nothing is deleted and nothing is re-tuned. `W_steps ∈ {250, 1000}` remains an appendix sensitivity with its own re-calibrated `h`.

## 10. Pseudo-code [N]

```
# construction: seq_ibd(C, K, probe_rng_seed=[probe_ns, instance_seed, episode_seed, arm_id])
#               rng = default_rng(probe_rng_seed)            # the ONLY RNG in this arm
# reset():      t_next=0; used=0; t_last=-PI; block=[]; pending=[]; units=deque(); O={}
#               a=zeros(C); stat=0.0; p_cache=g(0)*ones(C); elig=zeros((K,3))
# frozen:       g (harness, per instance), a_bar[C], v[C], h   -- all keyed (cell, instance_seed, confounder, arm)
# consts:       HSET=[1,2,3]; HMAX=3; PB=0.05; PI=20; W=500; NW=25; NMIN=3; ZCAP=8
# ALLK        = [(k,s) for k in range(K) for s in (+1,-1)]      # 2K pairs, contract probe order

def request_probe(steps):                                       # called BEFORE the step t_next
    if steps != 1: return None                                  # preferred_probe_steps = 1
    if used + 1 > floor(PB*t_next) or t_next - t_last < PI: return None
    if not block:
        block = [ALLK[i] for i in rng.permutation(2*K)]          # balanced, state-independent
    k, sgn = block.pop(0)                                        # FIFO, normative (param 9)
    used += 1; t_last = t_next; pending.append((t_next, k, sgn))
    return [sgn * e[k]]                                          # magnitude 1.0, never clipped

def update(tr):                                                  # once per environment step
    assert tr.t == t_next                                        # one clock (param 4)
    O[tr.t] = tr.prev_obs; O[tr.t+1] = tr.obs                    # o[t] is PRE-action (contract C)
    if (tr.t - (HMAX-1)) in pending:                             # a unit closes at tp + HMAX - 1
        (tp, k, sgn) = pending.pop(tr.t - (HMAX-1))
        units.append((tp, k, sgn, [O[tp+hz] - O[tp] for hz in HSET]))
        units.drop_while(lambda u: u.tp <= tp - W)               # half-open on anchor time
        for k2 in range(K):                                      # eligibility is h-invariant
            np_, nm_ = counts(units, k2)
            elig[k2][:] = 1 if min(np_, nm_) >= NMIN else 0      # guard; never binds on a full window
        for c in channels:
            zz = []
            for k2 in range(K):
                for i in range(len(HSET)):                       # ALL K*|H| cells, every tau (param 21)
                    if not elig[k2][i]: continue
                    Gp = [u.D[i][c] for u in units if u.k==k2 and u.sgn>0]
                    Gm = [u.D[i][c] for u in units if u.k==k2 and u.sgn<0]
                    z  = ranksum_z_tiecorrected(Gp, Gm)          # mid-ranks; sqrt(max(0,var)); 12 sig digits
                    if z is not None: zz.append(clip(z, -ZCAP, ZCAP))     # None = degenerate cell
            a[c] = max([abs(z) for z in zz], default=0.0)        # 0 = no eligible/usable cell
        p_cache = g(a)                                           # harness-fitted, refreshed every epoch
        stat = 0.0 if len(units) < NW else max_c(abs(a[c]-a_bar[c]) / v[c])   # WARM-UP (param 23)
        ledger_epoch(tr.t, elig, len(units), n_eligible_cells)   # emission: t = tp + HMAX - 1
    t_next += 1
    assert not isnan(p_cache).any() and not isnan(stat)          # hard error, never a silent 0
    return a.copy(), clip(p_cache,0,1), stat, int(stat > h)      # raw raise; harness owns p, r

# secondary_support() -> a.copy()                                # identical to raw_support (contract H(1))
#
# harness side, per episode:
#   emissions = [(t, raise) for t in {22,42,...,1982}]           # emission_grid, param 15
#   alarms    = contract_ref.count_alarms_timed(raises, times, p=3, r=20)     # epochs / steps
#   run_len   = contract_ref.run_length_from_reset(alarms, stream_end)        # from t = 0, D-11.5
#   primary   = contract_ref.auc_pre_event_support(raw_support_at_offset,
#                                                  oracle.S_obs_eps_pre, oracle.S_obs_eps)   # D-11.1a
#   secondary = contract_ref.auc_prob_superiority(secondary_support_at_offset, oracle.S_obs_eps)
```

## 11. Failure modes, limitations, claims we do not make [N]

**Failure modes.**

1. **Low alarm power at ARL_0 = 1000 measured from reset, declared not hidden — and lower than draft 4 implied.** 25 units give 5–7 per sign group and a complete actuator loss moves `a_c` by ≈ 1 z-unit against a `max_c` over 24–114 channels. D-11.5 makes this worse in the direction that matters for honesty: charging the 502-step prefix forces a **smaller** `h` to reach the same fresh-start ARL_0, so the post-warm-up false-alarm rate within a 2,000-step episode is materially higher than under draft 4's convention. The pilot reports P(alarm within H_det) against a no-event control on the same seeds; a value at or below the control is reported, not repaired. The arm is confirmed on support ranking; HPDT is descriptive.
2. **The primary is coarse and noisy per episode.** 3–5 positives against 1–2 negatives (§6); a single episode's AUC carries almost no information and is never interpreted alone.
3. **Offset 200 is a transition window** (§6): 0.60 pre-event, so the lost channel's `a_c` is still substantially driven by pre-event evidence and the primary at 200 is expected below its value at 500.
4. **The decay is slow relative to the window and noisy.** `a_c` on a lost channel is a maximum of six rank-sum statistics on 25 units; it reaches the null floor only in distribution, and single-epoch excursions above the retained channels' level occur. *(diagnostic, one instance, one episode: `a_c` on the lost channel wandered between 0.96 and 2.86 after the event while the retained channels averaged 2.4–2.6.)* This is why offsets are read at fixed epochs and clustered, not searched.
5. **τ = 2 raises the null floor on every channel** (§4): two of six cells carry no signal and the arm cannot drop them, because τ is outside the information set. A power cost, symmetric, not a validity cost.
6. **Multi-event schedules are exploratory**: the window never resets, so a second event within `W_steps` is read through a mixed window.
7. **C-dependence of `max_c`**: ARL_0 at fixed `h` falls as C grows; per-instance calibration absorbs it, but `h` is not transferable across distractor levels.
8. **Sign-flip blindness** (contract K8, g′ = −1): both groups flip, U → n₊n₋ − U, |z| unchanged — correctly invisible, since C3 keeps the channel.
9. **Long-lag confusion**: an actuator reaching c only at lag > max(ℋ) can lift `a_c` above the non-reachable floor through §3's residual dependence; under blocks the sign of z may flip but |z| stays elevated. A genuine false positive against the H = 3 estimand; reported, not suppressed.
10. **Power (not validity) depends on the task policy** through `probe_magnitude / policy_action_RMS`, logged per cell; comparisons ignoring it are inadmissible.

**Limitations.**

(a) **Family N operating-point asymmetry.** The washout argument is about **linear first moments**, and family N is not linear in the drive. Contract §B's family N is `b_{t+1} = A_b b_t + tanh(B_t a_{t−τ}/s)·s + κ·clip(b_t ⊙ b_t, −m, m) + ε^b`, with s = 1.0, κ = 0.1, m = 4.0. Two mechanisms break the sign symmetry the contrast assumes. First, `tanh(B a / s)·s` is **saturating**: at |B a| comparable to s the response to `+e_k` and to `−e_k` about a **displaced** operating point are not equal and opposite, because the two probes sample opposite sides of a curved map. Second, the quadratic term `κ·clip(b ⊙ b, −m, m)` is **non-negative elementwise**, so certified family-N instances have **nonzero stationary offsets** in b, amplified through `C_d/(1 − ρ_ar)` into d — the contract discloses order 1 to 40 on development seeds and rejects sub-seeds whose offsets exceed the T-L9b bound. A nonzero `z̄` is exactly the displaced operating point the first mechanism needs, and prior probes shift it further, so the sign contrast is **not exactly symmetric under the null on family N**. *(diagnostic: `draw_certified({"family":"N"}, 0)` certified in 6.1 s at `n_resamples = 1` with `max|z| = 33.5` and four-group stationary-mean spread 0.036; seed 5 needed 8 resamples and 27 s; the stationary offsets on the b and d blocks of those two draws were ≤ 0.86 in magnitude — well inside the contract's disclosed range but not zero.)* Round-4 family-N runs on a different generator showed no material effect at registry values, so this remains **prose, not a design change**; `T-IBD-exch` runs on family N as well as L, and a failure there is **reported, not repaired**. Family-N cells in round 6 are a **reproduction target only** and are not part of contract §L's exit condition (D-11.4a).
(b) **Tier-2 calibration is pooled across heterogeneous channel types and mis-calibrated per type**; the primary is unaffected, being monotone-invariant.
(c) **Strictly periodic probing can alias with a closed-loop resonance** on the control tier; declared, monitored, not jittered.
(d) **The rank-sum level is not exact** across a dependent window; the primary never uses z as a p-value.
(e) **N_x = 10 and N_x = 30 share body dynamics.** The configuration RNG draws `A_b`, `B`, `C_d` before anything N_x-dependent, so the same configuration seed gives identical body blocks at both distractor levels, and therefore an identical `S^obs,ε(pre)`, lost set, and — up to observation noise on the extra channels — an identical primary. The two distractor levels are a **matched design, not independent replicates**, and this arm's primary is nearly a duplicate across them (R5-27). Declared here; the choice belongs to the contract.

**Claims we do not make.** An **engineering baseline derived from IBD**, not a new method and not a contribution of this project. Props. 3.3–3.5 hold for a one-shot two-branch design under a dedicated π_probe and **do not carry over** to a sliding window or a within-randomisation sign contrast; no identifiability, optimality, FDR-control or ARL-optimality claim is made. We do not claim exact rank-sum level. We do not claim exchangeability beyond the randomisation device's construction — and under balanced blocks, not even the per-unit conditional-history identity (§3 caveat 2). We do not claim fast detection: failure mode 1 says the opposite, and D-11.5 makes the price explicit. We do not claim `p_c` at offset 200 reflects post-event support. We do not claim that a *per-channel* fit-time vector scores 0.5 on the primary (§6). We do not claim this is the best sequentialisation of IBD. It estimates `S^obs,ε` only, and the primary credits it only for tracking the change in `S^obs,ε`. *(Opinion: the C4-faithful design — a probe unit against a zero-action unit — remains the cleaner causal object; the sign contrast is chosen because it is budget-feasible and its validity does not depend on the task policy. Second opinion: `n_warm = 25` costs 502 steps of every episode and, now that D-11.5 charges it, 16.7 % of the ARL calibration budget and a lower operating point; a smaller `n_warm` with an occupancy-corrected reference would be cheaper but reintroduces a window-size-dependent `ā, v`, and I still judge that exchange bad — but D-11.5 has raised its price, and if `T-IBD-arl` fails, revisiting `n_warm` is the first thing to try, before anything about the statistic.)*

## 12. Gate tests [N]

| ID | Definition |
|---|---|
| **T-IBD-budget** | `used(t) ≤ floor(0.05·t)` after every step of every run. |
| **T-IBD-count** | Exhaustive replay on the generator's 0-indexed clock, t = 0…1999: grants = {20, 40, …, 1980}, **99 applied**, fraction 0.0495, **99 units**, all closing at t ≤ 1982; no grant at t = 0; the pre-computed-allocation implementation is **bitwise identical** to the online `request_probe` implementation. |
| **T-IBD-rng** | Block stream reproduces from `[probe_ns, instance_seed, episode_seed, arm_id]`; unchanged when the trajectory is perturbed (state-independence); unchanged between confounder present and absent; changed by a different `episode_seed`; the probed comparator's injected stream is bitwise equal to arm 1's. |
| **T-IBD-horizon** | Deterministic impulse on the reference generator at τ ∈ {0, 2}: first nonzero increment at **h = τ+1**; §2's index table reproduced. |
| **T-IBD-blocks** | Over ≥ 10⁵ **full (25-unit)** windows at K = 2: every (k, sign) group holds 5–7 units and `min(n₊,n₋) ≥ n_min_sign` in every such window, the guard never binds. Stated separately: on the 24 partial windows that open an episode the guard **does** bind and `stat ≡ 0` there. |
| **T-IBD-warmup** | `stat = 0` and `raise = 0` at every epoch with `< n_warm` units; `t_warm = 502 < event_t`; the draft-3 pathology (`stat_warm` = global max) asserted absent; a degenerate epoch holds `stat` and forces `raise = 0`. |
| **T-IBD-timed** | `count_alarms_timed(raises_at_epochs, epoch_times, p = 3, r = 20)` reproduces a hand fixture; the refractory suppresses **exactly one** epoch at Π = 20; `count_alarms(raw, p, r) == count_alarms_timed(raw, range(len(raw)), p, r)`; a unit-conversion mutant (r read as epochs) fails. |
| **T-IBD-arl** | `run_length_from_reset` measured **from t = 0**, prefix included, ≥ 542 always; ARL_0 attains [900, 1100] at some `h` on `T_arl = 3000` streams; realised censoring fraction reported; the prefix is never subtracted (a mutant that subtracts it fails). |
| **T-IBD-mono** | ARL_0 non-decreasing over an `h` grid computed from one recorded stream. |
| **T-IBD-hindep** | The raise sequence at a second `h` reproduces bitwise from that same stream. |
| **T-IBD-window** | Half-open membership on anchor time; exactly 25 units once `t_p* ≥ 500`; hand fixture of the grid t ≡ 2 (mod 20). |
| **T-IBD-mixture** | §6's offset table reproduced from the epoch grid under **both** boundary conventions, asserting the pre/post unit mixture **and** cell eligibility **separately**; the first fully post-event epoch is 1482. |
| **T-IBD-primary** | The evaluator recomputes the primary **solely from `update`'s public `raw_support`** via `contract_ref.auc_pre_event_support`, with mid-rank ties. A vector **constant across the channels of S^obs,ε(pre)** scores **exactly 0.5**. A **per-channel** fit-time vector scores the AUC implied by its own pre-event ordering and is asserted **against that value, not against 0.5**. `AUC(g(a)) == AUC(a)` (monotone invariance) on the fit split. |
| **T-IBD-tie** | Tied cell reproduces §4's σ_U² to 1e-12; untied cell reduces to n₊n₋(N+1)/12; a cancellation fixture yielding σ_U² < 0 naïvely returns 0, not `ValueError`; the 12-significant-digit rounding call is exercised. |
| **T-IBD-elig** | A cell with `min(n₊,n₋) = 2` contributes nothing and is flagged in the mask; `a_c = 0` from ineligibility and from a degenerate channel are distinguishable in the ledger. |
| **T-IBD-exch** | Sign-group exchangeability on a null channel (an x distractor), family **L and N**: ≥ 3,000 replicates give two-sided \|z\| > 1.96 in [0.03, 0.07], mean z within ±0.1; re-seeding the sign RNG leaves the null AUC inside its Monte Carlo interval. A family-N failure is **reported, not repaired**. |
| **T-IBD-fit** | Every artefact carries the key `(cell, instance_seed, confounder, arm)` and its fit-split episode seeds; the five splits of §7 are pairwise disjoint and disjoint from {996–999}; no artefact fitted on one instance is applied to another or across confounder conditions; the alarm-reference split contains no event. |
| **T-IBD-instance-reset** | Two consecutive event-carrying rollouts from one certified draw have **identical pre-event segments**; a harness that omits the deep copy fails. |
| **T-IBD-cal-1** | `g` takes ≥ 2 distinct values on the instance's fit split. |
| **T-IBD-cal-2** | Label floor **in independent units**: ≥ 24 fit episodes each contributing ≥ 1 positive and ≥ 1 negative channel-epoch, and ≥ 2 non-overlapping retained windows per episode. |
| **T-IBD-cal-3** | `g` non-decreasing, clamped into [0.001, 0.999], fitted only on non-straddling epochs; §7's counts reproduced (51 per event-carrying episode, 1,224 per instance; 75 and 1,800 for the alarm reference). |
| **T-IBD-persist** | Shared end-to-end fixture: the estimator returns a raw exceedance; the harness applies p once, in epochs, through `count_alarms_timed`. |

Every row needs a `coverage-matrix.md` entry before this spec is implemented (contract gate rule). None exists today (§14(f)).

## 13. Disposition of round-5 findings [N]

IBD-related items only, by the IDs used in the three round-5 findings files. Generator and comparator defects are dispositioned in the generator's own tests and in `comparator-spec.md` v3.

| ID | Sev | Disposition in draft 5 | Where |
|---|---|---|---|
| **R5-CX-09** (= R5-14 in part) | high | **Superseded by decision D-11.5, and draft 4's justification is withdrawn, not dropped.** Draft 4 row 19 said "a run length that cannot alarm is not a run length" and excluded the prefix. D-11.5 rejects that: both arms count from reset and this arm is charged its 502-step prefix. Row 24 now records the change, §5 recomputes the protocol, and `T-IBD-arl` asserts the prefix is not subtracted. | §5, §9 row 24, §12 |
| **R5-CX-10** | high | **Resolved.** `count_alarms_timed(raises, times, p = 3, r = 20)` with persistence in epochs and refractory in steps; `emission_grid` declared; the "once via `count_alarms`" claim deleted; the r = 20-at-Π = 20 consequence (exactly one epoch suppressed) declared. | §1, §5, §9 row 15, T-IBD-timed |
| **R5-CX-14**, **R5-17** | med / med | **Resolved.** One RNG per (instance, episode, arm) from `[probe_ns, instance_seed, episode_seed, arm_id]`, delivered as a constructor argument; lifecycle, domain separation, confounder-invariance and arm-3 replay all fixed; block consumption order fixed (FIFO). The interface-v5 gap (no channel for the seed) is recorded, not hidden. | §1, §3, §9 rows 6–9, T-IBD-rng, §14(e) |
| **R5-CX-12**, **R5-23**, **R5-GM-08** | med / low / low | **Accepted; the count was wrong and is corrected.** On the generator's 0-indexed clock there are **99 probes and 99 units**, fraction 0.0495. Draft 4's "100 applied / 99 units" and its terminal probe at t = 2000 described an environment that does not exist. **R4-23's "declared waste" is therefore withdrawn as a non-event**; the declared cost is instead a one-probe under-spend at the start, which is not repaired because a special first-step rule would break the `floor` invariant. The estimator clock is restated on `t_next`. | §2, §3, §9 row 4, T-IBD-count |
| **R5-CX-06**, **R5-20** | high / med | **Resolved by D-11.6.** Every artefact per `(cell, instance_seed, confounder, arm)`; the five episode-seed sets are fixed in §7; nothing pooled across instances or confounder conditions; the ledger key is asserted. | §7, §9 rows 26–27, T-IBD-fit |
| **R5-4** | high | **Resolved by D-11.1a, with one correction to the contract's framing.** The primary is now the pre-event-support AUC, on which a statistic constant across the scored channels scores exactly 0.5. The correction: a *per-channel* fit-time vector does **not** score 0.5, and on this generator scores well below it, because CL-4 is enforced by making the lost channel the dominant body component of actuator 0. `T-IBD-primary` asserts the true statement, and §14(a) reports the contract's over-strong one. | §6, §12, §14(a) |
| **R5-5**, **R5-GM-01** | high / high | **Resolved upstream and consumed here.** `draw_certified` now certifies CL-4 (`s_change`, `n_lost`) and stores `S_obs_pre_event` at draw time; this spec's primary reads both. Consequence declared: `n_lost` is 1 (occasionally 2) and `|S^obs,ε(pre)|` is 4–6, so the primary is coarse. | §6 |
| **R5-1**, **R5-GM-09** | critical | **Resolved upstream** (`VAR_ID` integer namespace replaces the salted string hash). Consumed here as a precondition: without it no cross-implementation agreement is meaningful, and the estimator's own RNG is separately domain-separated by `probe_ns` so the two can never collide. | §3 |
| **R5-CX-11**, **R5-11** | high | **Resolved upstream** (family N implemented and certified, D-11.4). Consumed here: `T-IBD-exch` runs on L and N; the operating-point asymmetry is restated against the generator's actual mechanism (tanh saturation plus the non-negative quadratic term's stationary offsets) rather than as a generic nonlinearity worry; family-N round-6 results are a reproduction target, not a gate. | §11(a), T-IBD-exch |
| **R5-CX-16** | high | **Resolved upstream** (D-11.3 sealed confirmation seed set; seeds 0–9 development only). No action in this spec; §7's episode seeds are episode-level and orthogonal to the instance seed set. | §7 |
| **R5-GM-05** | med | **Resolved, by the opposite fix to the one proposed.** The proposal was to shorten `n_warm` or lengthen the confirmation episode; draft 5 keeps `n_warm = 25` and `episode_len = 2000`, and moves ARL_0 calibration onto **dedicated event-free streams of `T_arl = 3000`**, so no run length is censored by the confirmatory episode schedule. Expected censoring ≈ 0.7 %; realised censoring reported. | §5, §9 row 25, T-IBD-arl |
| **R5-14** | med | **Partly resolved, partly escalated.** D-11.5 removes the asymmetry in the *rule* — both arms now use one clock, one stream length and one `n`. What remains is arithmetic: `n = 400` suffices only if `ŝd ≤ 1020`, so §5 makes `n` a function of the observed dispersion with 400 as a floor, and states the cap consequence (`ŝd ≤ 1317` at `T_arl = 3000`) and the partial-order fallback. The per-instance-`h` budget (≈ 9.6 × 10⁷ steps for this arm) is stated and referred to the runtime pilot. | §5, §14(b) |
| **R5-18** | med | **Accepted; prose corrected in both places.** §4 now states that the max is over **all** K·\|ℋ\| cells at every τ, of which K carry signal at τ = 2, and that the consequence is a raised null floor on every channel. §2 states that `D¹` and `D²` at τ = 2 are **zero in expectation**, not zero on a live stream. | §2, §4, §11(5) |
| **R5-22** | med | **Resolved by a normative harness rule.** Every event-carrying rollout starts from a `deepcopy` of the certified draw; `S^obs,ε(pre)` from the certified object, `S^obs,ε(post)` from the mutated copy; `T-IBD-instance-reset` asserts identical pre-event segments across consecutive rollouts. | §7, §12 |
| **R5-24** | low | **Accepted; the test was unsatisfiable and is restated.** `T-IBD-blocks` now asserts the 5–7 range and the never-binding guard on **full 25-unit windows only**, and states separately that the guard binds on the 24 partial windows where `stat ≡ 0` anyway. | §3, §12 |
| **R5-26** | low | **Resolved for this arm; the cross-arm half is contract-side.** §6 states one read convention — the last epoch ≤ `event_t + Δ`, giving 1182 / 1482 / 1982 — and states that there is no transition at t = 2000. That the comparator has no stated convention, so the two arms are read up to 18 steps apart at offset 1000, is recorded in §14(g). | §6, §8, §14(g) |
| **R5-27** | low | **Declared, not repaired.** The two distractor levels share body dynamics by construction, so this arm's primary is nearly a duplicate across them; declared as a matched design in §11(e). Whether to re-draw the body blocks per `N_x` is a contract question. | §11(e) |
| **R5-GM-06** | med | **Rejected by adjudication, recorded as a caveat.** The settling residue is shared by both sign groups because the sign is randomised, so it adds variance, not bias; exchangeability under "actuator k does not reach c" holds. Π is **not** raised to 40 (it would halve the unit count and break the offset table). Carried as §3 caveat 1 and §11(d). | §3, §11(d) |
| **R5-GM-07** | low | **Rejected by adjudication, with the reason restated.** Balanced blocks make `min(n₊,n₋) < 3` unreachable on a full window, so the case the finding describes does not arise where the primary is read; on partial windows `stat ≡ 0` by the warm-up rule. `a_c = 0` from ineligibility remains distinguishable from `a_c = 0` on an unresponsive channel through the returned eligibility mask, so no imputation is added. | §3, §12 |
| **R5-CX-17**, **R5-19(b,c)** | med | **Fixed for this document.** Draft 5's basis line names contract v3.9, interface v5, `contract_ref.py` and `reference_generator.py`; contract §H now names draft 5. The remaining registry-vs-prose disagreements are contract-side, §14(d). | header, §14(d) |
| **R5-CX-13** | high | **Open, contract-side.** The gate still runs no implementation of either arm and `coverage-matrix.md` has no row for any `T-IBD-*` id. This spec cannot fill it; §12 lists what the matrix must gain. | §14(f) |
| **R5-CX-01/02/03/04/05/07/08/15**, **R5-2/3/6/7/8/9/10/12/13/15/16/21/25/28/29**, **R5-GM-02/03/04** | — | Not IBD-arm items: generator conformance and mutation coverage, comparator statistic and constants, the confirmation design file, and the D-10.3 verdict. Dispositioned in the generator's tests, `comparator-spec.md` v3, and the contract. R5-3 and R5-GM-03 are the direct cause of D-11.2, on which this arm takes no position. | — |

**Carried forward, still resolved:** R4-1, R4-4, R4-5, R4-8, R4-13, R4-14, R4-15, R4-20, R4-24, R4-25, R4-CX-03, R4-CX-08, R4-CX-09, R4-GM-04, R4-GM-05, R4-GM-06, R4-GM-08; R3-1, R3-11 (i–v), R3-14, R3-15, R3-CX-04, R3-CX-05, R3-CX-10, R3-CX-11, D9-codex-3, GM3-4; draft-1 items IB-1, IB-2, IB-3, IB-6 to IB-12. **R4-23 is withdrawn as a non-event** (see the R5-CX-12 row): it described a terminal probe the 0-indexed generator cannot apply and therefore never grants. IB-4 and IB-5 remain obsolete.

## 14. Open, not resolved here

Draft 4's §11 items (a) and (b) are **closed**: the mid-rank AUC reference now exists — `contract_ref.auc_prob_superiority` (secondary) and `contract_ref.auc_pre_event_support` (primary, D-11.1a) — and the ARL protocol is now stated by D-11.5 and computed for this arm in §5. What remains open:

(a) **Contract §G's static-structure assertion is over-strong.** "A fit-time constant, or any statistic that never sees the scored episode, scores exactly 0.5", and the harness assertion that the round-5 static-loading control "must score 0.5 ± Monte Carlo in every cell", are true for a statistic **constant across the channels of S^obs,ε(pre)** and false for a per-channel fit-time **vector**. *(diagnostic: mean 0.212, range [0.000, 0.600], over 20 certified draws.)* The mechanism is CL-4's structural enforcement, which makes the lost channel one of the strongest pre-event channels, so the static control is **anti-correlated with the primary**, not uninformative. This spec asserts the true version (§12, `T-IBD-primary`) and does not amend the contract.

(b) **Contract §0 contradicts itself on the scope of ARL_0 calibration.** The ARL_0 row says calibration is "per (environment, regime, confounder, distractor_level, delay, estimator) cell … **shared across seeds**"; the fit-hierarchy row (D-11.6) lists "threshold h" among the artefacts that are "**per instance**". This spec follows D-11.6 as the later decision, at a cost of ≈ 9.6 × 10⁷ environment steps for this arm's alarm channel across the four base cells, which no runtime pilot has yet budgeted (contract §I). D-2a's fixed floor of `n = 400` fresh starts is also insufficient at run-length dispersion above `ŝd = 1020`, which §5 handles locally by making `n` dispersion-dependent.

(c) **The D-10.3 competence floor of 0.85 has not been re-derived for the pre-event-support primary.** It was set against a full-channel AUC over 24–44 channels; the new primary is an AUC over 3–5 positives and 1–2 negatives, on a lattice whose points straddle 0.85. Whether the floor's numerical value still means what it meant is a contract question, not this spec's.

(d) **Registry-versus-prose disagreements that survive into v3.9.** Contract §0 sets `offsets_P2 = {200, 500, 1000}` (D-10.5) while contract §G's P2 paragraph still says "offsets {10, 50, 200}"; `confirmation-design.csv` carries `10|50|200`. This spec follows §0. Also unresolved: `n_oracle = 4096` in §0 against `reference_generator.DEFAULT["n_oracle"] = 256`, which is never read.

(e) **Interface v5 has no channel for the probe seed.** §1 delivers it as a constructor argument and §3 fixes its derivation, so three implementations agree; but interface v5's `configure(bundle)` carries only `{regime_model_params, calibrator_params, arm_reference_params}` and its ledger row has no probe-seed field. Interface v5 should gain the constructor signature (or an estimator `reset(episode_seed, probe_rng_seed)`) and a `probe_rng_seed` ledger field. Recorded, not assumed.

(f) **No `T-IBD-*` row exists in `coverage-matrix.md`, and the gate runs no implementation of this arm.** Every row of §12 needs a matrix entry before this spec is implemented; the contract's own gate rule ("a normative item without a test ID is not implemented until it has one") is therefore unmet for this whole document today.

(g) **Only this arm has a stated offset read convention.** §6 fixes it here; the comparator's is fixed in `comparator-spec.md` v3. That contract §G states no single cross-arm convention means the paired difference `Δ_AUC` is defined by two specs rather than one, and at offset 1000 the two arms may be read up to 18 steps apart.

(h) **All evidence for this arm on the frozen generator is round 5's.** Three independent implementations from draft 4 reported the pre-event-*unrestricted* full-channel AUC at offset 500, N_x = 10, τ = 0, confounder present, as **0.800 (Opus), 0.815 (Codex), 0.831 (Gemini)**, and agreed to Monte Carlo error across both distractor levels, both delays and the perturbation set — that is what licenses draft 5 to leave the statistic, window, tie correction and block design untouched. **No number in this document has been measured under D-11.1a's primary, D-11.5's clock or D-11.6's fit hierarchy**; the diagnostics labelled as such are one model's index-table checks, not results. Round 6 is the measurement, and contract §L's exit condition is the test.

**References.** Liu, Cheng & Bogdan, arXiv:2603.18257 v2 (§§3.1–3.5, Alg. 1, Eq. 2, Props. 3.3–3.5). Mann & Whitney (1947); Wilcoxon (1945); Lehmann, *Nonparametrics*. Barlow et al. (1972), PAVA. `stage-0a-contract-v3.9.md`; `interface-spec-v5.md`; `decisions-required.md` (D-11); `executable-proofs/gate/reference_generator.py`; `executable-proofs/gate/contract_ref.py`; `round5-adjudication-and-tally.md`; `review5-codex/findings.md`; `review5-gemini/findings.md`; `review5-claude-opus/findings.md`; `superseded-specs/sequential-ibd-spec.draft4.md`; `comparator-spec.md`.
