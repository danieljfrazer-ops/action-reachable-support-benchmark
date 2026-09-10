"""Contract gate (post round 2). Assertions only. Run: python3 run_gate.py (exit code is the criterion)."""
import numpy as np
from contract_ref import *

A_diag = np.diag([0.9, 0.9]); A_coup = np.array([[0.9, 0.0], [0.3, 0.9]]); B_full = np.eye(2)
A_nd = np.array([[0.85, 0.15], [0.05, 0.70]]); A3 = np.array([[0.8, 0.1, 0.0], [0.0, 0.7, 0.2], [0.1, 0.0, 0.6]])
B_rect = np.array([[1.0, 0.2], [0.1, 0.9], [0.0, 0.3]])
B_rect_sparse = np.array([[1.0, 0.0], [0.0, 0.0], [0.0, 0.0]])       # only b0 hit directly, so propagation matters
A_chain = np.array([[0.5, 0, 0], [0.5, 0.5, 0], [0, 0.5, 0.5]]); B_chain = np.array([[1.0], [0.0], [0.0]])

def raises(fn, exc):
    try: fn()
    except exc: return True
    return False

# ---- K cases ----
def test_K1_sensor_swap_moves_observed_support_not_latent_with_reachable_padding_target():
    eff = np.array([1.0, 1.0, 0.0, 1.0])            # last latent reachable: a padded channel must still be False (FB-M3)
    assign = np.array([0, 1, 2, 3, -1]); gain = np.ones(5); avail = np.ones(5, bool)
    assert s_obs_eps(eff, assign, gain, avail, 0.1).tolist() == [True, True, False, True, False]
    sw = assign.copy(); sw[1], sw[2] = sw[2], sw[1]
    assert s_obs_eps(eff, sw, gain, avail, 0.1).tolist() == [True, False, True, True, False]

def test_K3_actuator_remap_changes_R_not_S():
    B_swap = np.array([[0.0, 1.0], [1.0, 0.0]])
    assert structural_reach(A_diag, B_full, 3).tolist() == structural_reach(A_diag, B_swap, 3).tolist()
    assert not np.allclose(jacobian_piecewise(A_diag, B_full, 1), jacobian_piecewise(A_diag, B_swap, 1))

def test_K4_actuator_loss_label_depends_on_coupling_and_horizon():
    B_loss = np.array([[1.0, 0.0], [0.0, 0.0]])
    assert structural_reach(A_diag, B_loss, 3).tolist() == [True, False]
    assert structural_reach(A_coup, B_loss, 1).tolist() == [True, False]
    assert structural_reach(A_coup, B_loss, 2).tolist() == [True, True]
    assert structural_reach(A_coup, B_loss, 3).tolist() == [True, True]

def test_K5_sensor_dropout_changes_observed_support_only():
    eff = np.array([1.0, 1.0]); assign = np.array([0, 1]); gain = np.ones(2)
    assert s_obs_eps(eff, assign, gain, np.array([True, True]), 0.1).tolist() == [True, True]
    assert s_obs_eps(eff, assign, gain, np.array([False, True]), 0.1).tolist() == [False, True]

def test_K7_partial_actuator_loss_changes_R_not_S_above_gamma_min():
    B_part = B_full * np.array([1.0, 0.5])
    assert structural_reach(A_diag, B_part, 3).tolist() == [True, True]
    assert not np.allclose(jacobian_piecewise(A_diag, B_full, 1), jacobian_piecewise(A_diag, B_part, 1))

def test_K10_downstream_d_inside_S_and_w_x_outside():
    C_d = np.array([[1.0, 0.0]]); A_d = np.array([[0.5]]); A_w = np.array([[0.9]]); A_x = np.array([[0.9]])
    assert structural_reach_full(A_diag, B_full, 3, 0, C_d, A_d, A_w, A_x).tolist() == [True, True, True, False, False]
    assert structural_reach_full(A_diag, B_full, 1, 0, C_d, A_d, A_w, A_x).tolist() == [True, True, False, False, False]

def test_K11_downstream_chain_through_A_d_with_and_without_delay():        # CX R2-01, GM2-2, OP-M15
    C_d = np.array([[1.0, 0.0], [0.0, 0.0]]); A_d = np.array([[0.0, 0.0], [0.5, 0.0]])   # b0->d0->d1
    for tau in (0, 1):
        r = lambda H: structural_reach_full(A_diag, B_full, H, tau, C_d, A_d)[2:].tolist()
        assert r(tau + 1) == [False, False]
        assert r(tau + 2) == [True, False]
        assert r(tau + 3) == [True, True]

# ---- C1 delay and chains ----
def test_C1_delay_empties_support_until_arrival():
    for tau in (0, 1, 2, 3):
        for H in range(1, 6):
            r = structural_reach(A3, B_rect, H, tau)
            assert (not r.any()) if H <= tau else (r[0] and r[1]), (tau, H)

def test_C1_chain_reaches_at_exactly_H2():
    assert structural_reach(A_chain, B_chain, 1).tolist() == [True, False, False]
    assert structural_reach(A_chain, B_chain, 2).tolist() == [True, True, False]
    assert structural_reach(A_chain, B_chain, 3).tolist() == [True, True, True]

def test_C1_delayed_chain_one_hop_per_step():                           # GM2-1
    for tau in (1, 2):
        r = lambda H: structural_reach(A_chain, B_chain, H, tau).tolist()
        assert r(tau) == [False, False, False]
        assert r(tau + 1) == [True, False, False]
        assert r(tau + 2) == [True, True, False]
        assert r(tau + 3) == [True, True, True]

def test_C1_reachability_is_sign_pattern_not_magnitude():              # FB-M12/M13
    A_small = np.array([[0.5, 0.0], [0.05, 0.5]]); B1 = np.array([[1.0], [0.0]])   # edge 0.05 < c_min: still an edge
    assert structural_reach(A_small, B1, 2).tolist() == [True, True]
    assert structural_reach(A3, B_rect_sparse, 2).tolist() == [True, False, True]  # via the 0.1 entry A3[2,0]

# ---- C4 ----
def test_C4_open_loop_equals_piecewise_jacobian_over_tau_h_grid_rectangular():
    a = np.array([0.5, -0.5])
    for tau in (0, 1, 2, 3):
        for h in range(1, 6):
            r = open_loop_response(A3, B_rect, a, h, tau)
            assert np.allclose(r, jacobian_piecewise(A3, B_rect, h, tau) @ a), (tau, h)

def test_C4_family_N_response_depends_on_zbar_and_is_not_odd():         # FB-M11, OP-M7, GM2-10
    step = lambda b, act: A_nd @ b + np.tanh(B_full @ act) + 0.1 * np.clip(b * b, -4, 4)
    z1, z2 = np.array([0.3, -0.2]), np.array([-0.5, 0.4]); a = np.array([1.0, 0.0])
    r1 = open_loop_response(A_nd, B_full, a, 2, 0, z1, step); r2 = open_loop_response(A_nd, B_full, a, 2, 0, z2, step)
    r0 = open_loop_response(A_nd, B_full, a, 2, 0, None, step)
    assert not np.allclose(r1, r2) and not np.allclose(r1, r0)
    # hand-rolled two-step check at z1
    b1 = step(z1, a); b2 = step(b1, np.zeros(2)); c1 = step(z1, np.zeros(2)); c2 = step(c1, np.zeros(2))
    assert np.allclose(r1, b2 - c2)
    assert not np.allclose(r1, -open_loop_response(A_nd, B_full, -a, 2, 0, z1, step))

# ---- E2 confounding statistic ----
def test_E2_witness_negative_sign_and_nonzero_column_and_max_not_mean():   # FB-M1, FB-M2, OP-M8
    rng = np.random.default_rng(0); T = 20000
    u = rng.normal(size=(T, 1)); noise = lambda n: 0.3 * rng.normal(size=(T, n))
    x = np.hstack([0.8 * u, noise(1), noise(1), noise(1)]) + 0.1 * rng.normal(size=(T, 4))   # x0 confounded, x1..3 not
    a = np.hstack([noise(1), -0.7 * u, noise(1)]) + 0.1 * rng.normal(size=(T, 3))            # witness is (1,0), negative
    assert max_pairwise_corr(a, x, witness=(1, 0)) >= 0.4
    pair_mean = np.mean([abs(np.corrcoef(a[:, k], x[:, j])[0, 1]) for k in range(3) for j in range(4)])
    assert pair_mean < 0.4                                                     # so mean-not-max would fail the floor
    assert max_pairwise_corr(rng.uniform(-1, 1, size=(T, 3)), x) <= 0.05

def test_E2_eligibility_and_nan_guard():
    rng = np.random.default_rng(0); T = 20000
    u = rng.normal(size=(T, 2)); x = u @ np.array([[0.8, 0.0], [0.0, 0.5]]) + 0.3 * rng.normal(size=(T, 2))
    a = u @ np.array([[0.7, 0.1, 0.0], [0.0, 0.6, 0.2]]) + 0.3 * rng.normal(size=(T, 3)); a[:, 2] = 0.0
    assert max_pairwise_corr(a, x, witness=(0, 0)) >= 0.4
    assert np.isnan(max_pairwise_corr(a, x, witness=(2, 0)))
    assert np.isnan(max_pairwise_corr(np.ones((T, 3)), x))

# ---- C3 gain, boundary, padding ----
def test_C3_gain_boundary_and_functional_form():                          # FB-M4, FB-M5, OP-M5
    eff = np.array([1.0, 0.3, 0.03]); assign = np.array([0, 1, 2]); avail = np.ones(3, bool)
    assert s_obs_eps(np.array([0.1]), np.array([0]), np.array([1.0]), np.array([True]), 0.1).tolist() == [False]  # exact boundary is False
    assert s_obs_eps(eff, assign, np.array([1.0, 0.5, 2.0]), avail, 0.1).tolist() == [True, True, False]   # |g|e: 1.0, 0.15, 0.06
    assert s_obs_eps(eff, assign, np.array([-1.0, -0.5, -2.0]), avail, 0.1).tolist() == [True, True, False]
    assert s_obs_eps(np.array([1.0]), np.array([0]), np.array([0.0]), np.array([True]), 0.1).tolist() == [False]

def test_L12_rectangular_B_indexes_rows():
    A = np.diag([0.9, 0.9, 0.9]); B = np.array([[1.0, 0.0], [0.0, 0.0], [0.0, 1.0]])
    assert structural_reach(A, B, 1).tolist() == [True, False, True]

# ---- G HPDT, vocabulary, spacing ----
def test_G_hpdt_mean_three_events_and_outcomes():                        # FB-M9, FB-M10, OP-M1
    assert hpdt([1, 2, 30], ["detected"] * 3, 100) == 11.0                  # median would be 2
    assert hpdt([5, 0, 0], ["detected", "missed", "terminated"], 100) == (5 + 100 + 100) / 3
    assert hpdt([5, 250], ["detected", "detected"], 100) == 52.5
    assert raises(lambda: hpdt([5], ["censored"], 100), ValueError)
    assert raises(lambda: hpdt([5], ["next_event"], 100), ValueError)

def test_G_spacing_episode_end_strictness_and_order():                    # FB-M6/M7/M8, OP-M2/M3
    assert check_spacing([100, 400], 700, 200, 50)
    assert not check_spacing([100, 400], 600, 200, 50)                      # 200 before episode end < 250
    assert check_spacing([100, 400], 650, 200, 50)                          # exactly 250 is allowed (>=)
    assert check_spacing([400, 100], 700, 200, 50) == check_spacing([100, 400], 700, 200, 50)
    assert not check_spacing([100, 300], 700, 200, 50)

# ---- v4.1 E2 aggregation ----
def test_aggregate_primary_full_key_signed_and_duplicates():
    def row(env, reg, conf, lvl, dly, seed, est, auc):
        return dict(environment=env, regime=reg, confounder=conf, distractor_level=lvl, delay=dly, seed=seed, estimator=est, auc=auc)
    rows = [row("scm_L","R0","present",10,0,0,"seq_ibd",0.9), row("scm_L","R0","present",10,0,0,"cusum_linear_channel_agnostic",0.7),
            row("scm_L","R0","present",30,0,0,"seq_ibd",0.8), row("scm_L","R0","present",30,0,0,"cusum_linear_channel_agnostic",0.9),   # IBD worse here
            row("scm_L","R0","present",10,2,0,"seq_ibd",0.85), row("scm_L","R0","present",10,2,0,"cusum_linear_channel_agnostic",0.35),
            row("scm_L","R0","absent",10,0,0,"seq_ibd",0.9), row("scm_L","R0","absent",10,0,0,"cusum_linear_channel_agnostic",0.88),
            row("scm_L","R0","present",10,0,1,"seq_ibd",0.9)]                                                                          # unpaired
    diffs, dropped, dups = aggregate_primary(rows)
    assert abs(diffs[("scm_L","R0","present",0)] - np.mean([0.2, -0.1, 0.5])) < 1e-12     # signed; absolute would give 0.2667
    assert abs(diffs[("scm_L","R0","absent",0)] - 0.02) < 1e-12                          # confounder is part of the key
    assert dropped == 1 and dups == 0
    diffs2, _, dups2 = aggregate_primary(rows + [row("scm_L","R0","present",10,0,0,"seq_ibd",0.1)])
    assert dups2 == 1 and abs(diffs2[("scm_L","R0","present",0)] - diffs[("scm_L","R0","present",0)]) < 1e-12   # first row kept, dup counted

def test_auc_prob_superiority_ties_and_degenerate():
    assert auc_prob_superiority([0.9, 0.8, 0.1, 0.2], [1, 1, 0, 0]) == 1.0
    assert auc_prob_superiority([0.5, 0.5, 0.5], [1, 0, 0]) == 0.5
    assert auc_prob_superiority([0.9, 0.5, 0.5, 0.1], [1, 1, 0, 0]) == 0.875
    assert np.isnan(auc_prob_superiority([0.1, 0.2], [0, 0]))


# ---- Mutants executable today ----
def test_M1_rejected_action_leaks_into_distractor():
    rng = np.random.default_rng(1); T = 4000
    a = rng.uniform(-1, 1, size=(T, 1)); x = 0.5 * a + 0.3 * rng.normal(size=(T, 1))
    assert not (max_pairwise_corr(a, x) <= 0.05)

def test_M7_rejected_negative_power_formula():
    assert not np.allclose(np.linalg.matrix_power(A_diag, -1) @ B_full, jacobian_piecewise(A_diag, B_full, 1, tau=1))


# ---- G alarm counting and matching (OP-12) ----
def test_G_count_alarms_persistence_and_refractory():
    raw = [0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0]
    assert count_alarms(raw, 3, 20) == [3, 27]          # counted at the 3rd consecutive raise; next raise inside r ignored

def test_G_match_alarms_attribution_and_false_alarms():
    delays, outcomes, fa = match_alarms([50, 1010, 1300, 1900], [1000, 1500], 200, 2000)
    assert delays == [10, 200] and outcomes == ["detected", "missed"] and fa == [50, 1300, 1900]
    delays, outcomes, fa = match_alarms([1150], [1000, 1100], 200, 2000)   # alarm after the next event belongs to it
    assert outcomes == ["missed", "detected"] and delays == [200, 50] and fa == []


# ---- Round-3 survivors (Opus R3-M1/M2/M4/M5/M7/M8/M9, Gemini GM3-1/5/6, Codex aggregate-ignores-delay) ----
def test_G_count_alarms_refractory_blocks_burst_inside_window_and_exact_boundary():
    raw = [0,1,1,1,1,1,0,1,1,1,0]                       # second burst at t=7..9 is inside r=20 after the alarm at t=3
    assert count_alarms(raw, 3, 20) == [3]
    raw2 = [0]*30; raw2[1:4] = [1,1,1]; raw2[24:27] = [1,1,1]; raw2[27:30] = [1,1,1]
    # alarm at t=3; block_until = 23; raises at 24,25,26 count -> alarm at 26 (exact boundary t=24 is allowed, t=23 is not)
    assert count_alarms(raw2, 3, 20) == [3, 26]
    raw3 = [0]*30; raw3[1:4] = [1,1,1]; raw3[23:26] = [1,1,1]                  # burst starting exactly at block_until
    assert count_alarms(raw3, 3, 20) == [3]                                     # t=23 blocked, run restarts at 24 -> only 2 raises

def test_G_count_alarms_persistence_is_consecutive_not_leaky():
    assert count_alarms([1,0,1,0,1,0,1,0,1], 3, 20) == []                       # alternating never reaches 3 consecutive
    assert count_alarms([0,0,1,1,1], 3, 20) == [4]

def test_G_match_alarms_episode_end_bounds_attribution_and_event_step_is_not_detection():
    delays, outcomes, fa = match_alarms([150], [100], 200, 120)                 # episode ends inside H_det, alarm after end
    assert outcomes == ["missed"] and delays == [200] and fa == [150]
    delays, outcomes, fa = match_alarms([100], [100], 200, 2000)                # alarm exactly at the event step: not attributed
    assert outcomes == ["missed"] and fa == [100]

def _retired_test_aggregate_primary_three_cells_mean_not_median_and_delay_kept_in_key():
    rows = []
    for lvl, d in ((10, 10.0), (30, 20.0), (100, 90.0)):
        rows += [dict(seed=0, level=lvl, delay=0, estimator="cusum_channel_agnostic", hpdt=50.0 + d),
                 dict(seed=0, level=lvl, delay=0, estimator="seq_ibd", hpdt=50.0)]
    diffs, dropped = aggregate_primary(rows)
    assert diffs == {0: 40.0} and dropped == 0                                   # median would be 20
    rows2 = [dict(seed=0, level=10, delay=0, estimator="cusum_channel_agnostic", hpdt=60.0),
             dict(seed=0, level=10, delay=0, estimator="seq_ibd", hpdt=40.0),
             dict(seed=0, level=10, delay=2, estimator="cusum_channel_agnostic", hpdt=90.0),
             dict(seed=0, level=10, delay=2, estimator="seq_ibd", hpdt=30.0)]
    assert aggregate_primary(rows2)[0] == {0: 40.0}                              # (20 + 60)/2; ignoring delay would overwrite

def test_C3_out_of_range_assign_raises_not_silent():
    assert raises(lambda: s_obs_eps(np.array([1.0]), np.array([3]), np.array([1.0]), np.array([True]), 0.1), IndexError)

def test_E2_global_max_is_not_the_witness_value():
    rng = np.random.default_rng(3); T = 5000
    u = rng.normal(size=(T, 1))
    x = np.hstack([0.9 * u, 0.15 * u]) + 0.1 * rng.normal(size=(T, 2))
    a = np.hstack([0.9 * u, 0.15 * u]) + 0.1 * rng.normal(size=(T, 2))
    assert max_pairwise_corr(a, x, witness=(1, 1)) > pairwise_corr(a, x, 1, 1) + 0.1   # witness (1,1) is not the max pair


# ---- D-9 verification round survivors (Codex world-edges; Gemini signed pairwise_corr; Gemini upper boundary) ----
def test_C1_build_adjacency_keeps_w_and_x_self_edges():
    A_w = np.array([[0.9, 0.0], [0.2, 0.8]]); A_x = np.array([[0.7]])
    adj, sl = build_adjacency(A_diag, None, None, A_w, A_x)
    assert adj[sl["w"], sl["w"]].tolist() == [[True, False], [True, True]]
    assert adj[sl["x"], sl["x"]].tolist() == [[True]]
    assert not adj[sl["w"], sl["b"]].any() and not adj[sl["x"], sl["b"]].any()   # no action path into w or x

def test_E2_pairwise_corr_is_absolute():
    rng = np.random.default_rng(5); T = 4000
    u = rng.normal(size=(T, 1)); a = -0.9 * u + 0.1 * rng.normal(size=(T, 1)); x = 0.9 * u + 0.1 * rng.normal(size=(T, 1))
    assert pairwise_corr(a, x, 0, 0) >= 0.4

def test_G_match_alarms_upper_boundary_inclusive():
    delays, outcomes, fa = match_alarms([1200], [1000], 200, 2000)
    assert outcomes == ["detected"] and delays == [200] and fa == []
    delays, outcomes, fa = match_alarms([1201], [1000], 200, 2000)
    assert outcomes == ["missed"] and fa == [1201]


# ---- Round-4 survivors ----
def test_C1_no_cross_edges_between_exogenous_blocks():                      # Gemini R4-GM-M1
    A_w = np.array([[0.9]]); A_x = np.array([[0.7]]); C_d = np.array([[1.0, 0.0]]); A_d = np.array([[0.5]])
    adj, sl = build_adjacency(A_diag, C_d, A_d, A_w, A_x)
    assert not adj[sl["x"], sl["w"]].any() and not adj[sl["w"], sl["x"]].any()
    assert not adj[sl["x"], sl["d"]].any() and not adj[sl["w"], sl["d"]].any() and not adj[sl["d"], sl["x"]].any()

def test_G_match_alarms_takes_first_alarm_in_window():                     # Opus R4-M1
    delays, outcomes, fa = match_alarms([1030, 1120], [1000], 200, 2000)
    assert delays == [30] and outcomes == ["detected"] and fa == [1120]

def test_C3_negative_effect_rejected():                                    # Opus R4-M3
    assert raises(lambda: s_obs_eps(np.array([-1.0]), np.array([0]), np.array([1.0]), np.array([True]), 0.1), ValueError)


def test_aggregate_primary_keeps_negative_sign():                           # Codex abs-difference mutant
    def row(seed, est, auc):
        return dict(environment="scm_L", regime="R0", confounder="present", distractor_level=10, delay=0, seed=seed, estimator=est, auc=auc)
    diffs, _, _ = aggregate_primary([row(0, "seq_ibd", 0.6), row(0, "cusum_linear_channel_agnostic", 0.9)])
    assert abs(diffs[("scm_L", "R0", "present", 0)] - (-0.3)) < 1e-12


# ---- v3.9 / D-11 ----
def test_G_auc_pre_event_support_restricts_to_pre_support_and_orients_retained_positive():
    from contract_ref import auc_pre_event_support
    pre  = np.array([1, 1, 1, 1, 0, 0], bool)          # channels 0..3 controllable before the event
    post = np.array([1, 1, 0, 0, 0, 0], bool)          # the event removes 2 and 3
    scores = np.array([0.9, 0.8, 0.2, 0.1, 5.0, -5.0]) # channels 4, 5 carry extreme scores and must be ignored
    assert auc_pre_event_support(scores, pre, post) == 1.0
    assert auc_pre_event_support(-scores, pre, post) == 0.0                       # orientation: higher = retained
    assert auc_pre_event_support(np.full(6, 3.0), pre, post) == 0.5              # a constant scores exactly 0.5
    assert auc_pre_event_support(np.array([0.9, 0.5, 0.5, 0.1, 0, 0]), pre, post) == 0.875  # mid-rank tie half credit: (1+1+0.5+1)/4
    assert np.isnan(auc_pre_event_support(scores, pre, pre))                     # nothing lost: undefined, not 1.0
    try: auc_pre_event_support(scores[:5], pre, post); assert False
    except ValueError: pass

def test_G_count_alarms_timed_persistence_in_emissions_refractory_in_steps():
    from contract_ref import count_alarms_timed, count_alarms
    raw = [0,1,1,1,1,1,0,1,1,1,0] + [0]*15 + [1,1,1]
    assert count_alarms_timed(raw, range(len(raw)), 3, 20) == count_alarms(raw, 3, 20)     # step arm reduces to count_alarms
    times = [2 + 20*i for i in range(8)]                                                   # epoch arm, grid t = 2 mod 20
    assert count_alarms_timed([1,1,1,1,1,1,1,1], times, 3, 20) == [42, 122]                # alarm at the 3rd epoch; t=62 blocked (62 <= 42+20); run restarts at 82
    assert count_alarms_timed([1,1,1,1,1,1,1,1], times, 3, 19) == [42, 102]                # r=19: t=62 > 61 is admitted and counts toward the next run
    assert count_alarms_timed([1,1,1,1,1,1,1,1], times, 3, 0) == [42, 102]
    assert count_alarms_timed([1,1,0,1,1,1,1,1], times, 3, 20) == [102]                    # a zero breaks the run in emissions, not steps
    assert count_alarms_timed([0,0,0,0,0,0,0,0], times, 3, 20) == []
    try: count_alarms_timed([1,1], [5, 5], 1, 0); assert False
    except ValueError: pass

def test_G_run_length_from_reset_includes_warm_up_prefix_and_reports_censoring():
    from contract_ref import run_length_from_reset, count_alarms_timed
    times = [502 + 20*i for i in range(6)]                                  # an epoch arm whose first emission is after a 502-step warm-up
    counted = count_alarms_timed([1,1,1,0,0,0], times, 3, 20)
    assert counted == [542] and run_length_from_reset(counted, 4000) == (542, False)      # the prefix is charged to the arm
    assert run_length_from_reset([], 4000) == (4000, True)
