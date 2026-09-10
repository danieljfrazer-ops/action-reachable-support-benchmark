# Interface spec (frozen, one page) — basis for the independent black-box acceptance suite (contract E6)

Environment: `reset(seed) -> obs[C]`; `step(action[K]) -> obs[C]`; `probe(action[K], steps) -> list[obs]` (logged, costed). No other agent-facing method. Observations are float arrays of fixed length C. Actions are clipped to [−a_max, a_max].
Oracle (separate process, evaluator only): `labels(t) -> {S_latent: bool[N_z], S_obs_eps: bool[C], R: float[N_b, K, |ℋ|], P: (assign int[C], gain float[C], avail bool[C]), events: list[(t, type)]}` with `e_interval` (99 percent bounds on operational effects). Any attempt to read oracle fields via the environment object raises.
Estimator: `update(obs) -> (p[C] in [0,1], alarm_S in {0,1})`; `request_probe(action, steps)` allowed only if the regime permits; declared `information_set` string.
Metrics (reference implementations in `executable-proofs/gate/contract_ref.py`): RMDT with censoring at H_det; ARL_0 calibration on the calibration split; Brier and log loss per channel; F1 at fixed offsets via out-of-band probes.
Ledger row: code hash, config hash, lockfile hash, seed, environment, regime, confounder, estimator, thresholds, probes used, operations, thermal pressure, outcome (complete, failed, NaN), metrics.
