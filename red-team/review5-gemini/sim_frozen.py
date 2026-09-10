#!/usr/bin/env python3
"""Round-5 independent reproduction on the FROZEN generator (freeze 0468104f6431b050).

Implements Sequential IBD (Draft 4) and Passive Delay-Aware Linear Comparator (v2)
from the two normative specifications alone against executable-proofs/gate/reference_generator.py.
"""
from __future__ import annotations

import copy
import math
import os
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np

GATE_DIR = Path(__file__).resolve().parents[1] / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE_DIR))

import reference_generator as rg
import contract_ref as cr

# ----------------- CONSTANTS -----------------
EPISODE_LEN = 2000
EVENT_T = 1000
EVENT = ("actuator_loss", 0)
OFFSETS = (200, 500, 1000)
HSET = (1, 2, 3)
PI = 20
W_STEPS = 500
K_ACT = 2
Z_CAP = 8.0
Q_CAP = 40.0
Q_ABSENT = -41.0
N_WARM_COMP = 30
N_PRED_FIT = 20
LAM_REL = 1e-4

# ----------------- RANK-SUM UTILS -----------------
def ranksum_z(gp: list[float], gm: list[float]) -> float | None:
    """Mid-rank tie-corrected rank-sum z statistic per sequential-ibd-spec sec 4."""
    np_ = len(gp)
    nm_ = len(gm)
    if np_ < 3 or nm_ < 3:
        return None
    N = np_ + nm_
    # Round to 12 significant decimal digits (GM-08)
    vals = [float(f"{v:.11e}") for v in (gp + gm)]
    u_idx = np.argsort(vals)
    ranks = np.empty(N, dtype=float)
    
    # Compute mid-ranks and tie sizes
    i = 0
    t_sum = 0
    while i < N:
        j = i
        while j < N - 1 and vals[u_idx[j + 1]] == vals[u_idx[i]]:
            j += 1
        tie_size = j - i + 1
        mid_rank = i + 1 + (tie_size - 1) / 2.0
        for k in range(i, j + 1):
            ranks[u_idx[k]] = mid_rank
        if tie_size > 1:
            t_sum += (tie_size**3 - tie_size)
        i = j + 1

    R_plus = sum(ranks[:np_])
    U = R_plus - np_ * (np_ + 1) / 2.0
    mu_U = np_ * nm_ / 2.0
    
    # Tie-corrected variance formula
    var_U = (np_ * nm_ / (N * (N - 1))) * ((N**3 - N) / 12.0 - t_sum / 12.0)
    var_U = max(0.0, var_U)
    if var_U <= 0.0:
        return None
    sigma_U = math.sqrt(var_U)
    return (U - mu_U) / sigma_U

# ----------------- COMPARATOR FIT -----------------
def fit_comparator(inst: rg.Instance, seed: int, confounder: bool):
    """Fit delay-aware linear predictor on 20 non-probed fault-free episodes."""
    C = inst.C
    K = inst.cfg["K"]
    n_features = C + 3 * K

    phi_list = []
    y_list = []
    
    inst_fit = copy.deepcopy(inst)
    if not confounder:
        inst_fit.G[:] = 0.0

    for ep in range(N_PRED_FIT):
        # Disjoint episode seed space: 1000 + ep
        r = inst_fit.run(EPISODE_LEN, ep=1000 + ep)
        O = r["o"]  # [T+1, C]
        A = r["a"]  # [T, K]
        
        # Build features with lag buffer
        lag = [np.zeros(K), np.zeros(K)]
        for t in range(EPISODE_LEN):
            a_t = A[t]
            phi_t = np.concatenate([O[t], a_t, lag[0], lag[1]])
            phi_list.append(phi_t)
            y_list.append(O[t + 1])
            lag = [a_t, lag[0]]

    Phi = np.array(phi_list, dtype=float)  # [n, C + 3K]
    Y = np.array(y_list, dtype=float)      # [n, C]
    n = len(Y)

    # Standardise penalised features
    m = Phi.mean(axis=0)
    s = np.maximum(Phi.std(axis=0, ddof=0), 1e-8)
    X_tilde = np.hstack([(Phi - m) / s, np.ones((n, 1))])

    # Ridge regression: penalty on non-intercept columns
    D = np.eye(n_features + 1)
    D[-1, -1] = 0.0
    lam = LAM_REL * n

    # Solve Cholesky
    XtX = X_tilde.T @ X_tilde
    XtY = X_tilde.T @ Y
    B_tilde = np.linalg.solve(XtX + lam * D, XtY)

    # Back-transform to raw feature coefficients
    beta_raw = B_tilde[:-1] / s[:, None]
    b_raw = B_tilde[-1] - (m / s) @ B_tilde[:-1]

    # Innovations on fit split
    R = Y - X_tilde @ B_tilde
    mu = R.mean(axis=0)
    sd = np.maximum(R.std(axis=0, ddof=1), 1e-6)

    # Iterated-prediction Jacobian for H-horizon loading
    beta_o = beta_raw[:C]  # [C, C]
    beta_a = [beta_raw[C + j * K : C + (j + 1) * K] for j in range(3)]  # [K, C] each

    J = np.zeros((K, C))
    l_c = np.zeros(C)
    for h in HSET:
        J = J @ beta_o + beta_a[h - 1]
        loading_h = np.linalg.norm(J, axis=0) / sd
        l_c = np.maximum(l_c, loading_h)

    # Degenerate channels
    degen = (sd < 1e-2 * np.median(sd)) & (l_c < 1e-3)

    return {
        "beta_raw": beta_raw,
        "b_raw": b_raw,
        "mu": mu,
        "sd": sd,
        "l_c": l_c,
        "degen": degen,
    }

# ----------------- IBD & COMPARATOR RUNNER -----------------
def run_scored_episode(
    inst: rg.Instance,
    comp_fit: dict,
    ep: int,
    confounder: bool,
):
    """Run one scored episode, evaluating IBD and Comparator at offsets {200, 500, 1000}."""
    C = inst.C
    K = inst.cfg["K"]
    
    inst_run = copy.deepcopy(inst)
    if not confounder:
        inst_run.G[:] = 0.0

    # 1. Probing schedule for IBD
    # Balanced pre-randomised blocks over (k, sign) of length 2K = 4
    pairs = [(int(k), float(sgn)) for k in range(K) for sgn in (1.0, -1.0)]
    rng_block = np.random.default_rng([inst.seed, ep, 0x1BD])
    
    probe_actions = {}
    probe_meta = {}  # t_p -> (k, sign)
    block = []
    for tp in range(PI, EPISODE_LEN, PI):
        if not block:
            block = copy.deepcopy(pairs)
            rng_block.shuffle(block)
        k, sgn = block.pop()
        k = int(k)
        sgn = float(sgn)
        act = np.zeros(K)
        act[k] = sgn
        probe_actions[tp] = act
        probe_meta[tp] = (k, sgn)

    # 2. Run interventional stream for IBD
    r_ibd = inst_run.run(
        EPISODE_LEN,
        ep=ep,
        actions=probe_actions,
        event_t=EVENT_T,
        event=EVENT,
    )
    O_ibd = r_ibd["o"]  # [T+1, C]

    # Pre-compute probe increments: D_c^h(t_p) = O[t_p + h] - O[t_p]
    units = []
    for tp in sorted(probe_meta.keys()):
        if tp + 3 <= EPISODE_LEN:
            k, sgn = probe_meta[tp]
            diffs = [O_ibd[tp + h] - O_ibd[tp] for h in HSET]  # 3 x C
            units.append({"tp": tp, "k": k, "sgn": sgn, "D": diffs})

    # 3. Evaluate IBD scores at target epochs: 1182 (offset 200), 1482 (offset 500), 1982 (offset 1000)
    # Newest anchor t_p* is 1180, 1480, 1980
    ibd_scores = {}
    offset_anchors = {200: 1180, 500: 1480, 1000: 1980}
    for off, tp_star in offset_anchors.items():
        w_units = [u for u in units if (tp_star - W_STEPS < u["tp"] <= tp_star)]
        a_c = np.zeros(C)
        for c in range(C):
            zz = []
            for k in range(K):
                gp = [u["D"] for u in w_units if u["k"] == k and u["sgn"] > 0]
                gm = [u["D"] for u in w_units if u["k"] == k and u["sgn"] < 0]
                for hi in range(3):
                    p_vals = [d[hi][c] for d in gp]
                    m_vals = [d[hi][c] for d in gm]
                    z = ranksum_z(p_vals, m_vals)
                    if z is not None:
                        zz.append(np.clip(z, -Z_CAP, Z_CAP))
            a_c[c] = max([abs(z) for z in zz], default=0.0)
        ibd_scores[off] = a_c

    # 4. Run non-probed stream for Comparator
    r_comp = inst_run.run(
        EPISODE_LEN,
        ep=ep,
        actions=None,
        event_t=EVENT_T,
        event=EVENT,
    )
    O_comp = r_comp["o"]
    A_comp = r_comp["a"]

    # Compute comparator innovations and q_c
    beta_raw = comp_fit["beta_raw"]
    b_raw = comp_fit["b_raw"]
    mu = comp_fit["mu"]
    sd = comp_fit["sd"]
    l_c = comp_fit["l_c"]
    degen = comp_fit["degen"]

    comp_scores = {}
    offset_steps = {200: 1200, 500: 1500, 1000: 2000}
    
    # Step-by-step update for comparator
    lag = [np.zeros(K), np.zeros(K)]
    rt_ring = deque(maxlen=W_STEPS)
    
    for t in range(EPISODE_LEN):
        o_t = O_comp[t]
        a_t = A_comp[t]
        o_next = O_comp[t + 1]
        
        phi_t = np.concatenate([o_t, a_t, lag[0], lag[1]])
        pred = phi_t @ beta_raw + b_raw
        r = o_next - pred
        rt = np.clip((r - mu) / sd, -Z_CAP, Z_CAP)
        rt_ring.append(rt)
        lag = [a_t, lag[0]]
        
        step_idx = t + 1  # 1-indexed count of updates
        for off, target_step in offset_steps.items():
            if step_idx == target_step:
                n = min(W_STEPS, step_idx)
                mean_rt = np.mean(list(rt_ring), axis=0)
                shift = np.abs(math.sqrt(n) * mean_rt)
                q = np.clip(l_c - shift, -Q_CAP, Q_CAP)
                q[degen] = Q_ABSENT
                comp_scores[off] = q

    return ibd_scores, comp_scores

# ----------------- MAIN SIMULATION LOOP -----------------
def main():
    print(f"# review5-gemini  sim_frozen.py  freeze 0468104f6431b050")
    print(f"# numpy {np.__version__}  python {sys.version.split()[0]}")
    t0 = time.time()

    configs = [
        {"name": "Nx10_tau0", "cfg": {"N_x": 10, "tau": 0}, "seeds": list(range(10))},
        {"name": "Nx10_tau2", "cfg": {"N_x": 10, "tau": 2}, "seeds": list(range(10))},
        {"name": "Nx30_tau0", "cfg": {"N_x": 30, "tau": 0}, "seeds": list(range(10))},
        {"name": "Nx30_tau2", "cfg": {"N_x": 30, "tau": 2}, "seeds": list(range(10))},
        # Perturbation set at seed 0 (coupling x {0.5, 1, 2}, noise x {0.5, 1, 2})
        {"name": "pert_c0.5_n0.5", "cfg": {"N_x": 10, "tau": 0, "coupling": 0.5, "noise_mult": 0.5}, "seeds": [0]},
        {"name": "pert_c0.5_n2.0", "cfg": {"N_x": 10, "tau": 0, "coupling": 0.5, "noise_mult": 2.0}, "seeds": [0]},
        {"name": "pert_c2.0_n0.5", "cfg": {"N_x": 10, "tau": 0, "coupling": 2.0, "noise_mult": 0.5}, "seeds": [0]},
        {"name": "pert_c2.0_n2.0", "cfg": {"N_x": 10, "tau": 0, "coupling": 2.0, "noise_mult": 2.0}, "seeds": [0]},
    ]

    all_results = {}

    for cell in configs:
        c_name = cell["name"]
        cfg = cell["cfg"]
        seeds = cell["seeds"]
        print(f"\n=== Cell {c_name} ({len(seeds)} instance seeds) ===")

        instance_results = []

        for s in seeds:
            inst = rg.draw_certified(cfg, s)
            
            # Post-event ground truth labels
            inst_post = copy.deepcopy(inst)
            inst_post.apply_event(EVENT)
            y_post = inst_post.S_obs()
            n_pos = int(y_post.sum())
            s_change = bool((inst.S_obs() != y_post).any())

            # Fit comparator on present and absent
            fit_pres = fit_comparator(inst, s, confounder=True)
            fit_abs = fit_comparator(inst, s, confounder=False)

            ep_data = []
            for ep in range(4):
                # Present
                ibd_p, comp_p = run_scored_episode(inst, fit_pres, ep, confounder=True)
                # Absent
                ibd_a, comp_a = run_scored_episode(inst, fit_abs, ep, confounder=False)

                row = {}
                for off in OFFSETS:
                    auc_ibd_p = cr.auc_prob_superiority(ibd_p[off], y_post)
                    auc_ibd_a = cr.auc_prob_superiority(ibd_a[off], y_post)
                    auc_cmp_p = cr.auc_prob_superiority(comp_p[off], y_post)
                    auc_cmp_a = cr.auc_prob_superiority(comp_a[off], y_post)
                    
                    row[off] = {
                        "ibd_p": auc_ibd_p,
                        "ibd_a": auc_ibd_a,
                        "cmp_p": auc_cmp_p,
                        "cmp_a": auc_cmp_a,
                        "delta_p": auc_ibd_p - auc_cmp_p,
                        "delta_a": auc_ibd_a - auc_cmp_a,
                        "benefit": (auc_ibd_p - auc_cmp_p) - (auc_ibd_a - auc_cmp_a),
                    }
                ep_data.append(row)

            # Average over 4 episodes for this instance
            inst_summary = {
                "seed": s,
                "n_pos": n_pos,
                "C": inst.C,
                "s_change": s_change,
                "offsets": {},
            }
            for off in OFFSETS:
                inst_summary["offsets"][off] = {
                    "ibd_p": float(np.mean([e[off]["ibd_p"] for e in ep_data])),
                    "ibd_a": float(np.mean([e[off]["ibd_a"] for e in ep_data])),
                    "cmp_p": float(np.mean([e[off]["cmp_p"] for e in ep_data])),
                    "cmp_a": float(np.mean([e[off]["cmp_a"] for e in ep_data])),
                    "delta_p": float(np.mean([e[off]["delta_p"] for e in ep_data])),
                    "delta_a": float(np.mean([e[off]["delta_a"] for e in ep_data])),
                    "benefit": float(np.mean([e[off]["benefit"] for e in ep_data])),
                }
            instance_results.append(inst_summary)
            print(f"  done {c_name} seed={s} n_pos={n_pos}/{inst.C} s_change={s_change}  "
                  f"IBD(500)={inst_summary['offsets'][500]['ibd_p']:.3f}  "
                  f"CMP(500)={inst_summary['offsets'][500]['cmp_p']:.3f}  "
                  f"benefit={inst_summary['offsets'][500]['benefit']:+.3f}")

        # Summary across instances
        n_inst = len(instance_results)
        cell_summary = {"name": c_name, "n_instances": n_inst, "offsets": {}}
        t_crit = 2.262 if n_inst == 10 else (12.706 if n_inst == 2 else 1.96)

        for off in OFFSETS:
            b_vals = [ir["offsets"][off]["benefit"] for ir in instance_results]
            cmp_a_vals = [ir["offsets"][off]["cmp_a"] for ir in instance_results]
            ibd_p_vals = [ir["offsets"][off]["ibd_p"] for ir in instance_results]
            ibd_a_vals = [ir["offsets"][off]["ibd_a"] for ir in instance_results]
            cmp_p_vals = [ir["offsets"][off]["cmp_p"] for ir in instance_results]

            mean_b = float(np.mean(b_vals))
            se_b = float(np.std(b_vals, ddof=1) / math.sqrt(n_inst)) if n_inst > 1 else 0.0
            ci_b = (mean_b - t_crit * se_b, mean_b + t_crit * se_b) if n_inst > 1 else (mean_b, mean_b)

            mean_cmp_a = float(np.mean(cmp_a_vals))
            se_cmp_a = float(np.std(cmp_a_vals, ddof=1) / math.sqrt(n_inst)) if n_inst > 1 else 0.0
            ci_cmp_a = (mean_cmp_a - t_crit * se_cmp_a, mean_cmp_a + t_crit * se_cmp_a) if n_inst > 1 else (mean_cmp_a, mean_cmp_a)

            cell_summary["offsets"][off] = {
                "ibd_p": float(np.mean(ibd_p_vals)),
                "ibd_a": float(np.mean(ibd_a_vals)),
                "cmp_p": float(np.mean(cmp_p_vals)),
                "cmp_a": mean_cmp_a,
                "cmp_a_lb": ci_cmp_a[0],
                "benefit_mean": mean_b,
                "benefit_se": se_b,
                "benefit_ci": ci_b,
            }

        all_results[c_name] = {"cell": cell_summary, "instances": instance_results}
        
        # Print summary for offset 500
        s500 = cell_summary["offsets"][500]
        print(f"-> Summary {c_name} @ offset 500: "
              f"IBD_p={s500['ibd_p']:.3f}, IBD_a={s500['ibd_a']:.3f}, "
              f"CMP_p={s500['cmp_p']:.3f}, CMP_a={s500['cmp_a']:.3f} [lb={s500['cmp_a_lb']:.3f}], "
              f"Benefit={s500['benefit_mean']:+.3f} (SE={s500['benefit_se']:.3f}, CI=[{s500['benefit_ci'][0]:+.3f}, {s500['benefit_ci'][1]:+.3f}])")

    total_time = time.time() - t0
    print(f"\nTotal simulation runtime: {total_time:.1f} s")
    
    # Write JSON results for easy inspection
    import json
    out_json = Path(__file__).parent / "sim_frozen_results.json"
    with open(out_json, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Saved results to {out_json}")

if __name__ == "__main__":
    main()
