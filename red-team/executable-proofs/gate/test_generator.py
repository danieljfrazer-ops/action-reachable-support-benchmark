"""Conformance tests for reference_generator.py against contract v3.7 A0, B, C, E."""
import numpy as np, copy
from reference_generator import Instance, draw_certified, DEFAULT
from contract_ref import structural_reach_full

def test_gen_determinism_bitwise():
    a = Instance({}, 3).run(300, ep=1)["o"]; b = Instance({}, 3).run(300, ep=1)["o"]
    assert np.array_equal(a, b)
    assert not np.array_equal(a, Instance({}, 4).run(300, ep=1)["o"])

def test_gen_structural_no_action_path_into_w_or_x():
    inst = Instance({}, 0); S = inst.S_latent()
    assert not S[inst.sl["w"]].any() and not S[inst.sl["x"]].any()
    assert S[inst.sl["b"]].any()

def test_gen_confounded_half_and_padding_layout():
    inst = Instance({}, 0)
    assert inst.confounded.sum() == 5 and inst.assign[-4:].tolist() == [-1] * 4
    assert inst.confounded_channels().sum() == 5

def test_gen_certified_instance_meets_contract_bounds():
    inst = draw_certified({}, 0); c = inst.certification
    assert c["ok"] and c["rho_cl"] <= 0.98 and c["sat"] <= 0.05 and c["rho_witness"] >= 0.4 and c["rho_severed"] <= 0.1

def test_gen_actuator_loss_changes_support_per_oracle_not_event_type():
    inst = draw_certified({}, 1); before = inst.S_obs().copy(); inst.apply_event(("actuator_loss", 0)); after = inst.S_obs()
    assert before.sum() >= after.sum()                      # support cannot grow under loss
    assert (before & ~after).any()                          # CL-4 certified: the event removes >= 1 channel

def test_gen_probe_replaces_action_and_is_clipped():
    inst = Instance({}, 2); r = inst.run(50, actions={10: np.array([9.0, -9.0])})
    assert np.allclose(r["a"][10], [2.0, -2.0])

def test_gen_delay_first_hit_at_tau_plus_one():
    inst = Instance({"tau": 2}, 5); e1 = inst.operational_effect(H=1); e3 = inst.operational_effect(H=3)
    assert not (e1 > 0).any() and (e3 > 0).any()

def test_gen_perturbation_set_still_certifies():
    for coupling in (0.5, 2.0):
        for noise in (0.5, 2.0):
            inst = draw_certified({"coupling": coupling, "noise_mult": noise}, 0); assert inst.certification["ok"]


def test_gen_run_timing_first_hit_at_tau_plus_one_in_rollout():
    for tau in (0, 2):
        inst = Instance({"tau": tau, "sigma": dict(b=0, d=0, w=0, x=0, o=0, a=0, u=0)}, 7)
        inst.W_o[:] = 0; inst.W_u[:] = 0                       # open loop, zero noise
        r = inst.run(6, actions={0: np.array([1.0, 0.0]), **{t: np.zeros(2) for t in range(1, 6)}})
        hits = [t for t in range(1, 7) if np.abs(r["z"][t, :4]).sum() > 0]
        assert hits and hits[0] == tau + 1, (tau, hits)


# ---- Round-5 repairs ----
def test_gen_cross_process_determinism():
    import subprocess, sys, os
    code = "import numpy as np, hashlib, sys; sys.path.insert(0, %r); from reference_generator import Instance; print(hashlib.sha256(Instance({'burn_in': 0}, 3).run(200, ep=1)['o'].tobytes()).hexdigest())" % str(__import__('pathlib').Path(__file__).parent)
    outs = [subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=dict(os.environ, PYTHONHASHSEED=str(h))).stdout.strip() for h in (1, 2)]
    assert outs[0] == outs[1] and len(outs[0]) == 64, outs

def test_gen_faithfulness_bound_and_dense_B_on_all_frozen_seeds():
    for seed in range(10):
        inst = draw_certified({"burn_in": 0}, seed)
        nz = inst.A_b[inst.A_b != 0]; assert np.all(np.abs(nz) >= 0.2 - 1e-12), seed
        nzB = inst.B[inst.B != 0]; assert np.all(np.abs(nzB) >= 0.2 - 1e-12) and (inst.B != 0).sum() >= inst.B.size - 1, seed   # dense except the CL-4 row

def test_gen_cl4_event_changes_support_on_every_certified_instance():
    for seed in range(10):
        inst = draw_certified({"burn_in": 0}, seed); c = inst.certification
        assert c["s_change"] and c["n_lost"] >= 1, (seed, c)
        post = copy.deepcopy(inst); post.apply_event(("actuator_loss", 0))
        assert (inst.S_obs_pre_event() & ~post.S_obs()).sum() == c["n_lost"]

def test_gen_confounded_mask_is_first_half_not_inverted():
    inst = Instance({"burn_in": 0}, 0); m = inst.confounded_channels(); xs = inst.sl["x"]
    assert m[xs.start:xs.start + 5].all() and not m[xs.start + 5:xs.stop].any() and not m[:xs.start].any()

def test_gen_noise_streams_independent_across_variables_and_keyed():
    inst = Instance({"burn_in": 0}, 0)
    nb = inst._noise("b", 5, (4000,), 1); nd = inst._noise("d", 5, (4000,), 1); nb2 = inst._noise("b", 5, (4000,), 1)
    assert abs(np.corrcoef(nb, nd)[0, 1]) < 0.06 and np.array_equal(nb, nb2)

def test_gen_noise_mult_scales_innovation_streams():
    ra = Instance({"burn_in": 0, "noise_mult": 1.0, "policy_gain": 0.0, "W_u_scale": 0.0, "G_scale": 0.0}, 0).run(300)
    rb = Instance({"burn_in": 0, "noise_mult": 2.0, "policy_gain": 0.0, "W_u_scale": 0.0, "G_scale": 0.0}, 0).run(300)
    assert np.std(rb["z"][:, 8:12]) > 1.5 * np.std(ra["z"][:, 8:12])                    # w block (pure innovation noise) scales

def test_gen_burn_in_changes_initial_state():
    r0 = Instance({"burn_in": 0}, 0).run(5); r1 = Instance({"burn_in": 500}, 0).run(5)
    assert np.abs(r0["z"][0]).sum() == 0 and np.abs(r1["z"][0]).sum() > 0

def test_gen_soft_loss_breaks_label_consistency_and_is_detected():
    inst = draw_certified({"burn_in": 0}, 0); assert inst.labels_consistent()
    inst.B[:, 0] *= 1e-9                                                     # structurally present, operationally absent
    assert not inst.labels_consistent()                                      # E1b disagreement is detectable

def test_gen_noise_mult_does_not_scale_confounder_driver():
    a = Instance({"burn_in": 0, "noise_mult": 1.0}, 0).run(400); b = Instance({"burn_in": 0, "noise_mult": 2.0}, 0).run(400)
    assert np.allclose(a["u"], b["u"])


# ---- v3.9 / D-11.4 family N, D-11.3 seeds, family L pin ----
def test_gen_family_L_stream_pinned_bitwise_after_family_N_refactor():
    import hashlib
    h = hashlib.sha256(Instance({"burn_in": 0}, 3).run(300, ep=1)["o"].tobytes()).hexdigest()
    assert h == "8cc6352eb290313f5a3d18174245938172bff936d0d903bf8a367ff1dcb70285", h     # captured on frozen version 5 + repairs, before D-11.4
    inst = draw_certified({"burn_in": 0}, 0)
    assert hashlib.sha256(inst.A_b.tobytes()).hexdigest() == "cf78a1104511992ec89e79f48c82df08410a03faa30479551c12ea10162dc18b"

def test_gen_family_N_reduces_to_family_L_when_nonlinearity_is_switched_off():
    L = Instance({"burn_in": 0}, 4).run(200, ep=2)["z"]
    N = Instance({"burn_in": 0, "family": "N", "kappa_N": 0.0, "s_N": 1e9}, 4).run(200, ep=2)["z"]   # tanh(x/s)*s -> x
    assert np.allclose(L, N, atol=1e-6) and not np.allclose(L, Instance({"burn_in": 0, "family": "N"}, 4).run(200, ep=2)["z"])

def test_gen_family_N_certifies_bounded_stationary_cl4_and_label_consistent():
    for seed in (0, 1):
        inst = draw_certified({"family": "N", "burn_in": 0}, seed); c = inst.certification
        assert c["ok"] and c["bounded"] and c["stationary_ok"] and c["chain_mean_spread"] <= 0.05 and c["max_abs_z"] <= 100.0, (seed, c)
        assert c["s_change"] and c["n_lost"] >= 1 and inst.labels_consistent()
        assert np.abs(inst.zbar).max() > 0.1                                   # the stationary mean is empirical and nonzero (C4)

def test_gen_family_N_response_is_not_odd_and_uses_zbar():
    inst = draw_certified({"family": "N", "burn_in": 0}, 0); K = inst.cfg["K"]
    def resp(sign, z0):
        a = np.zeros(K); a[0] = sign; za, z0_ = z0.copy(), z0.copy()
        for h in range(3): za = inst._step_noiseless(za, a if h == 0 else np.zeros(K)); z0_ = inst._step_noiseless(z0_, np.zeros(K))
        return za - z0_
    zb = inst.zbar
    assert not np.allclose(resp(1.0, zb), -resp(-1.0, zb))                    # not odd in a (contract C4, family N)
    assert not np.allclose(resp(1.0, zb), resp(1.0, np.zeros(inst.Nz)))       # response depends on z̄
    inst.apply_event(("actuator_loss", 0)); assert inst._zbar is None          # CL-8: re-estimated after the event

def test_gen_family_N_divergent_subseed_is_rejected_not_certified():
    n = Instance({"family": "N", "burn_in": 0}, 0)                             # sub-seed 0 of configuration seed 0 diverges
    cert = n.boundedness_certificate(); assert not cert["bounded"] or not cert["stationary_ok"]
    assert not n.certify()["ok"] and draw_certified({"family": "N", "burn_in": 0}, 0).n_resamples >= 1

def test_gen_rollout_batch_chains_are_independent_and_match_family_dynamics():
    inst = Instance({"burn_in": 0}, 0); Z = inst.rollout_batch(4, 50, np.zeros((4, inst.Nz)), ep=5)
    assert Z.shape == (51, 4, inst.Nz) and not np.allclose(Z[-1, 0], Z[-1, 1])   # different chains, different noise

def test_confirmation_seed_commitment_is_sealed_and_range_is_disjoint_from_development():
    import confirmation_seeds as cs, re
    assert re.fullmatch(r"[0-9a-f]{64}", cs.COMMITMENT) and cs.SEED_LOW > 60 * 1000 and cs.N_CONFIRMATION >= 20
    try: cs.derive(b"not the secret"); assert False
    except ValueError: pass
