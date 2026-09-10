"""Generates confirmation-design.csv (roadmap v4 + amendments v4.1-v4.7, contract v3.9 / D-11). One row per run, plus calibration rows.
Primary outcome: support correctness at offsets (D-8a; ranking metric per D-9.2 pending). All four regime x confounder cells are
confirmatory_effect with an interaction_group key (R3-12). Third arm per D-7a. episode_len 2000 / event_t 1000 per D-6b."""
import csv, itertools, pathlib, hashlib
THIRD_ARM = True   # D-7 (a) confirmed 7 Sep 2026
envs = [("scm_L", "L", [0, 2], 3), ("scm_N", "N", [0, 2], 3), ("pointmass_2d", "T2", [0], 3), ("pendulum_v1", "T2", [0], 3)]
regimes = ["R0_inband_linear", "R1_misspecified"]; confounder = ["present", "absent"]; levels = [10, 30, 100]
conf_est = ["seq_ibd", "cusum_linear_delay_aware"] + (["cusum_linear_delay_aware_probed"] if THIRD_ARM else [])
desc_est = ["random", "temporal_correlation", "forward_model_residual"]
probe_cfg = hashlib.sha256((pathlib.Path(__file__).parent / "sequential-ibd-spec.md").read_bytes()).hexdigest()[:12]   # spec file digest (R3-17)
common = dict(event="actuator_loss_complete", target="S_obs_eps", schedule="single_unannounced", episode_len=2000, event_t=1000,
              steps_per_run=2000, n_events=1, probe_budget_fraction=0.05, ARL_0=1000,
              calibration_rule="D2a_400_runlengths_CI_in_band_shared_per_cell", calibration_steps="per_cell_until_rule_met_cap_2e6",
              aggregation="equal_weight_mean_over_levels_and_delays_per_seed", outcome="AUC_over_pre_event_support_retained_vs_lost (D-11.1a, contract_ref.auc_pre_event_support)", secondary_outcome="full_channel_AUC_of_secondary_support_vs_S_obs_eps_post", offsets_F1="200|500|1000", primary_offset=500, p2_offsets="200|500|1000", ranking_metric="AUC", secondary_metrics="AUPRC_with_prevalence|F1_at_validated_operating_point", cal_split="24|16", s_change_required=True, instance_seed_set="development_0..9;confirmation=confirmation_seeds.py(sealed,commitment_89a262a9)", fit_hierarchy="per_instance(cell,instance_seed,arm)", f_conf=0.5, H_det=200,
              probe_config_hash=probe_cfg)
rows = []
for env, fam, delays, H in envs:
    for reg, conf, lvl, delay in itertools.product(regimes, confounder, levels, delays):
        n_channels = (4 + 2 + 4 if fam != "T2" else 4) + lvl + 4          # body(+d)+w + distractors + padding (provisional)
        base = dict(environment=env, family=fam, regime=reg, confounder=conf, distractor_level=lvl, delay=delay, H=H,
                    n_channels=n_channels, split_id="confirmation", in_confirmatory_conjunction=(fam != "N"), **common)   # D-11.4: family N out until reproduced cross-model
        role = "confirmatory_effect"; interaction_group = f"{env}|{reg}"
        for est in conf_est:
            for inst in range(10):                                                   # D-10.7: 10 instance draws x 4 episode seeds
                rows.append(dict(base, estimator=est, instance_seed=inst, episode_seed=-1, seed=f"i{inst}", role="calibration", split_id="calibration", interaction_group=""))   # D-11.6: one calibration row per (cell, instance, arm); instance index into the sealed confirmation set
                for ep in range(4):
                    rows.append(dict(base, estimator=est, instance_seed=inst, episode_seed=ep, seed=f"i{inst}e{ep}", role=role, interaction_group=interaction_group))
        if conf == "present":
            for est, inst in itertools.product(desc_est, range(3)):
                rows.append(dict(base, estimator=est, instance_seed=inst, episode_seed=0, seed=f"i{inst}e0", role="descriptive", interaction_group=""))
out = pathlib.Path(__file__).parent / "confirmation-design.csv"
with out.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
from collections import Counter; print(Counter(r["role"] for r in rows), "->", out.name)
