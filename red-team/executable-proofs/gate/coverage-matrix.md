# Coverage matrix: contract v3.9 normative items → gate tests (post round 5, D-11 encoded)

| Contract item | Test(s) | Status |
|---|---|---|
| C1 reachability over all latents, delay, one hop per step, downstream chain via A_d, sign pattern not magnitude | test_C1_*, test_K4_*, test_K10_*, test_K11_*, test_L12_* | covered |
| C3 observed support: padding, availability, gain magnitude, strict ε boundary | test_K1_*, test_K5_*, test_C3_* | covered |
| C4 open-loop response, piecewise Jacobian, τ∈{0..3}, rectangular; family N at z̄, non-odd | test_C4_* | covered |
| D remap R-not-S; complete loss coupling; partial loss ≥ γ_min | test_K3_*, test_K4_*, test_K7_* | covered |
| E2c/E2d witness pair (negative sign, non-zero column), eligibility, NaN guard, max not mean | test_E2_* | covered |
| G HPDT mean, frozen outcome vocabulary, cap; spacing incl. episode end, ≥, unsorted | test_G_* | covered |
| G alarm bookkeeping: count_alarms (consecutive persistence, refractory incl. exact boundary), match_alarms (episode end, event step excluded) | test_G_count_alarms_*, test_G_match_alarms_* | covered |
| v4.1 E2 aggregation: ≥3 cells mean≠median; delay in key | test_aggregate_primary_* | covered |
| E2c witness vs global max | test_E2_global_max_* | covered |
| T-IBD-budget, T-IBD-null-overlap, T-IBD-replay, T-IBD-mono, T-IBD-cal-1..3 (sequential-ibd-spec) | — | **uncovered** (spec draft 3 / 0A) |
| v4.1 E2 aggregate_primary (paired by seed and cell; unpaired dropped) | test_aggregate_primary_* | covered |
| E3 executable mutants (40 from five reviewers and the author through round 5, plus 7 D-11 mutants) | mutants.py, 47/47 killed; originals captured before patching | covered |
| E3 mutants M2, M3, M4, M5, M6 (need generator and oracle) | — | **uncovered** (0A) |
| C2 certification: margin > 0 on every reachable latent, CL-4 (event removes ≥ 1 observed channel), faithfulness floor, label consistency (E1b), re-certification after events (family N z̄) | test_gen_cl4_*, test_gen_faithfulness_*, test_gen_soft_loss_*, test_gen_certified_* | covered (Bonferroni intervals and the 20 % rejection-rate cap remain 0A) |
| B family N (D-11.4): tanh/quadratic body step; T-L9b boundedness from 32 random initial states over 20,000 steps and four-group stationary-mean agreement within δ_inv; empirical z̄ used by C2/C4 and re-estimated after every event (CL-8); reduces to family L when the nonlinearity is off; divergent draws rejected | test_gen_family_N_*, test_gen_rollout_batch_* | covered (single-model until round 6 reproduces) |
| A0 family L stream unchanged by the D-11.4 refactor (bitwise pin of the round-5 generator) | test_gen_family_L_stream_pinned_* | covered |
| A0 / D-11.3 confirmation seeds: sealed commitment, range disjoint from development seeds and sub-seeds | test_confirmation_seed_commitment_* | covered |
| G primary (D-11.1a): AUC over the pre-event support, retained = positive, mid-rank ties, constant = 0.5, channels outside the pre-event support excluded | test_G_auc_pre_event_support_*; mutants D11-M1..M3 | covered |
| G alarm bookkeeping (D-11.5): persistence in the arm's emission unit, refractory in environment steps, clock from reset, run length includes the warm-up prefix, censoring reported | test_G_count_alarms_timed_*, test_G_run_length_from_reset_*; mutants D11-M4..M7 | covered |
| B delay-augmented closed-loop radius (family L) and saturation fraction at certification | test_gen_certified_instance_meets_contract_bounds | covered |
| E4 determinism; E5 isolation canary; E6 black-box suite; T-OOB no-mutation | — | **uncovered** (0A) |
| ARL_0 calibration (precision rule per D-2); Brier; log loss; F1 at offsets; alarm bookkeeping (p, r, w_T); select_interaction_cells; coverage simulation | — | **uncovered** (0A / 0R) |
| L1 print-only scripts were not a gate | test_proof_theatre.py | covered |

Uncovered normative groups: 4 (T-IBD/T-CMP spec fixtures; mutants M2–M6; E4–E6 isolation and acceptance; ARL_0 calibration and tier-2 metrics). Phase 0A gate requires 0. Everything marked single-model is unverified until round 6 reproduces it.
