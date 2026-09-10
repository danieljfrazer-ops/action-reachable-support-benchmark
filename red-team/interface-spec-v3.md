# Interface spec v3 (frozen, one page; v3.2 semantics after D-9) — basis for the independent black-box acceptance suite (contract E6)

Supersedes `interface-spec-v2.md` (FB-9, FB-23, F3, F4).

**Environment (agent-facing).**
- `reset(seed) -> (obs[C], info)`; `step(action[K]) -> (obs[C], info)`. Actions clipped to [−a_max, a_max]. `info` carries only `t` and `probe_flag`. Reward, terminated and truncated are **evaluator-side** fields in the ledger transition, not visible to the estimator unless its information set declares "reward visible".
- `probe(actions[steps, K]) -> list[Transition]`: applies the sequence; cost = `steps` probe steps against `probe_budget`; `probe_flag=True` on each.
- `Transition = (prev_obs, applied_action, obs, probe_flag, t)`; immutable. The evaluator's ledger transition additionally carries reward, terminated, truncated.

**Estimator.**
- `configure(regime_bundle)`: the **only privileged input**: `{model_params_hash, model_params | None}` for the declared regime's residual model; logged in the ledger.
- `calibrate(transitions: list[Transition]) -> None`: consumes the calibration split; `set_threshold(h)`: sets the alarm threshold chosen by the harness's ARL_0 calibration (contract §0).
- `update(transition) -> (p[C] in [0,1], stat: float, raise: {0,1})`, once per environment step (a probe step is an environment step whose action was replaced); outputs may be piecewise constant between epochs (GM3-9). `raise = 1 iff stat > h` with **no persistence applied**; the harness owns persistence p (in the estimator's declared unit, steps or epochs) and refractory r via `contract_ref.count_alarms` (R3-10). Declared flag `statistic_is_monotone_in_alarm=True`; declared `persistence_unit`.
- `request_probe(steps) -> actions[steps, K] or None`.
- Declared `information_set` string; `needs_calibration_split` flag.

**Oracle (evaluator process only; never importable by the estimator).**
- `labels(t) -> {S_latent: bool[N_z], S_obs_eps: bool[C], confounded_mask: bool[C], e_interval: (lo, hi), R: float[N_b, 2K, |ℋ|] in probe order, M: float[N_b, K, |ℋ|] (family L only), P: (assign, gain, avail), events: list[(t, type, targets_changed)], s_change_certified: bool}`.
- `score_support(t, offsets) -> F1 per offset` via snapshot-and-branch with common random numbers; asserted not to mutate live state, RNG, or estimator bytes (T-OOB).

**Metrics.** Existing in `contract_ref.py`: HPDT with frozen outcomes, `check_spacing`, `aggregate_primary`. 0A deliverables (uncovered): ARL_0 calibration per the D-2a rule, Brier, log loss, F1 at offsets, alarm bookkeeping (p, r), `select_interaction_cells`, isotonic p_c calibrator.

**Ledger row.** code hash, config hash, lock hash, interpreter, seed, environment, regime, confounder, distractor_level, delay, estimator, information_set, regime_bundle hash, spec file digest (replaces the placeholder probe-config hash, R3-17), threshold, persistence_unit, ARL_0 attained with interval, probe steps used, policy_action_rms, probe_mag_over_action_rms, p_epoch_1_alarm_times, raw_support_stat_stream (a_c per channel per epoch; the primary AUC is computed on this, never on p_c), operations, thermal pressure, outcome (complete, failed, NaN, not_in_band), metrics (R3-18).
