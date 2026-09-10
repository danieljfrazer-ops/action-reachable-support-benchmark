# Interface spec v2 (frozen, one page) — basis for the independent black-box acceptance suite (contract E6)

Supersedes `interface-spec.md` (CX-03, CX-13, CX-17, CL-11).

**Environment (agent-facing).**
- `reset(seed) -> (obs[C], info)`; `step(action[K]) -> (obs[C], reward, terminated, truncated, info)`. Actions clipped to [−a_max, a_max]. `info` carries only `t` and `probe_flag`.
- `probe(actions[steps, K]) -> list[Transition]`: applies the given randomised sequence; cost = `steps` probe steps against `probe_budget`; each returned transition has `probe_flag=True`.
- `Transition = (prev_obs, applied_action, obs, reward, terminated, truncated, probe_flag, t)`; immutable.

**Estimator.**
- `update(transition) -> (p[C] in [0,1], alarm_S in {0,1})`, called once per environment step and once per probe step in order; at reset, `update` receives a transition with `prev_obs=None`.
- `request_probe(steps) -> actions[steps, K] or None`: the estimator proposes a randomised probe sequence; the harness applies it via `probe` if the regime permits and the budget allows, and returns the transitions to `update`.
- Declared `information_set` string; declared `needs_calibration_split` flag.

**Oracle (evaluator process only; never importable by the estimator).**
- `labels(t) -> {S_latent: bool[N_z], S_obs_eps: bool[C], e_interval: (lo[N_z], hi[N_z]), R: float[N_b, 2K, |ℋ|] in probe order (+e_1, −e_1, …), M: float[N_b, K, |ℋ|] (family L only), P: (assign int[C], gain float[C], avail bool[C]), events: list[(t, type, targets_changed)], s_change_certified: bool}`.
- `score_support(t, offsets) -> F1 per offset` via snapshot-and-branch with common random numbers; asserted not to mutate live state, RNG, or estimator bytes (T-OOB).

**Metrics** (reference implementations in `executable-proofs/gate/contract_ref.py`): HPDT with outcome classes; ARL_0 calibration on the calibration split; per-channel Brier and log loss; F1 at fixed offsets; aggregation per `aggregate_primary()`.

**Ledger row**: code hash, config hash, lockfile hash, interpreter, seed, environment, regime, confounder, estimator, information_set, threshold, ARL_0 attained, probe steps used, operations, thermal pressure, outcome (complete, failed, NaN, not_calibratable), metrics.
