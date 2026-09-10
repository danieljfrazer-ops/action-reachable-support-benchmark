"""
Review 6 (Gemini) Clean-Room Reproduction on Frozen Version 38d161e762a3de76.
Normative:
  - sequential-ibd-spec.md (draft 5)
  - comparator-spec.md (v3)
  - stage-0a-contract-v3.9.md
  - interface-spec-v5.md
  - executable-proofs/gate/reference_generator.py (families L and N)
  - executable-proofs/gate/contract_ref.py (auc_pre_event_support, auc_prob_superiority)
"""

import sys, os, copy, time, math
from pathlib import Path
from collections import deque
import numpy as np

# Add gate directory to path for normative reference modules
gate_dir = Path(__file__).resolve().parent.parent / "executable-proofs" / "gate"
sys.path.insert(0, str(gate_dir))

from reference_generator import draw_certified, Instance
from contract_ref import auc_pre_event_support, auc_prob_superiority


# =====================================================================
# Utilities
# =====================================================================
def round_sig(val, sig=12):
    """Round to sig significant decimal digits (contract / spec tie rounding)."""
    if isinstance(val, (int, float, np.floating)):
        if val == 0.0 or not np.isfinite(val):
            return float(val)
        return float(f"{val:.11e}")
    val = np.asarray(val, float)
    out = np.zeros_like(val)
    mask = (val != 0.0) & np.isfinite(val)
    out[mask] = [float(f"{v:.11e}") for v in val[mask]]
    return out


# =====================================================================
# Arm 1: Sequential IBD (sequential-ibd-spec.md, draft 5)
# =====================================================================
def ranksum_z_tiecorrected(Gp, Gm):
    """Tie-corrected Mann-Whitney z-score for two groups Gp (+) and Gm (-).
    Rounds values to 12 significant digits and uses mid-ranks for ties.
    Returns None if degenerate or variance is 0.
    """
    np_ = len(Gp)
    nm_ = len(Gm)
    N = np_ + nm_
    if np_ == 0 or nm_ == 0 or N <= 1:
        return None

    # Round to 12 significant digits
    all_vals = [float(f"{v:.11e}") for v in Gp] + [float(f"{v:.11e}") for v in Gm]
    order = np.argsort(all_vals)
    ranks = np.zeros(N, float)

    i = 0
    tie_sum = 0.0
    while i < N:
        j = i
        while j < N and all_vals[order[j]] == all_vals[order[i]]:
            j += 1
        tg = j - i
        avg_rank = (i + 1 + j) / 2.0
        for idx in range(i, j):
            ranks[order[idx]] = avg_rank
        if tg > 1:
            tie_sum += (tg**3 - tg) / 12.0
        i = j

    R_plus = ranks[:np_].sum()
    U = R_plus - np_ * (np_ + 1) / 2.0
    mu_U = np_ * nm_ / 2.0
    var_U = (np_ * nm_ / (N * (N - 1))) * ((N**3 - N) / 12.0 - tie_sum)
    sigma_U = np.sqrt(max(0.0, var_U))
    if sigma_U == 0.0:
        return None
    z = (U - mu_U) / sigma_U
    return float(np.clip(z, -8.0, 8.0))


class SeqIBDEstimator:
    """Sequential IBD estimator (Draft 5)."""

    def __init__(self, C, K, probe_rng_seed):
        self.C = C
        self.K = K
        # Exactly one RNG in this arm
        self.rng = np.random.default_rng(probe_rng_seed)
        self.ALLK = [(k, s) for k in range(K) for s in (+1, -1)]

        self.PB = 0.05
        self.PI = 20
        self.W_steps = 500
        self.HMAX = 3
        self.HSET = [1, 2, 3]
        self.NMIN = 3
        self.ZCAP = 8.0

        self.reset()

    def reset(self):
        self.t_next = 0
        self.used = 0
        self.t_last = -self.PI
        self.block = []
        self.pending = {}  # t_p -> (t_p, k, sgn)
        self.units = []    # list of {'tp', 'k', 'sgn', 'D': [D1, D2, D3]}
        self.O = {}        # t -> obs
        self.a = np.zeros(self.C)

    def precompute_probes(self, T=2000):
        """State-independent pre-computed probe allocation."""
        actions = {}
        used = 0
        t_last = -self.PI
        block = []
        for t_next in range(T):
            if used + 1 <= int(math.floor(self.PB * t_next)) and (t_next - t_last >= self.PI):
                if not block:
                    perm = self.rng.permutation(2 * self.K)
                    block = [self.ALLK[i] for i in perm]
                k, sgn = block.pop(0)
                used += 1
                t_last = t_next
                act = np.zeros(self.K)
                act[k] = float(sgn)
                actions[t_next] = (act, k, sgn)
        return actions

    def update(self, t, prev_obs, applied_action, obs, probe_info=None):
        """Update step at environment step t."""
        assert t == self.t_next
        self.O[t] = prev_obs.copy()
        self.O[t + 1] = obs.copy()

        if probe_info is not None:
            _, k, sgn = probe_info
            self.pending[t] = (t, k, sgn)

        # Unit closing at t = t_p + HMAX - 1 = t_p + 2
        close_tp = t - (self.HMAX - 1)
        if close_tp in self.pending:
            tp, k, sgn = self.pending.pop(close_tp)
            D = [self.O[tp + hz] - self.O[tp] for hz in self.HSET]
            self.units.append({'tp': tp, 'k': k, 'sgn': sgn, 'D': D})

            # Drop units with tp <= tp_curr - W_steps (half-open window on anchor time)
            self.units = [u for u in self.units if u['tp'] > tp - self.W_steps]

            # Eligibility per actuator: min(n+, n-) >= 3
            elig = np.zeros(self.K, bool)
            for k2 in range(self.K):
                np_ = sum(1 for u in self.units if u['k'] == k2 and u['sgn'] > 0)
                nm_ = sum(1 for u in self.units if u['k'] == k2 and u['sgn'] < 0)
                elig[k2] = (min(np_, nm_) >= self.NMIN)

            # Compute rank sum across channels
            for c in range(self.C):
                zz = []
                for k2 in range(self.K):
                    if not elig[k2]:
                        continue
                    for h_idx in range(len(self.HSET)):
                        Gp = [u['D'][h_idx][c] for u in self.units if u['k'] == k2 and u['sgn'] > 0]
                        Gm = [u['D'][h_idx][c] for u in self.units if u['k'] == k2 and u['sgn'] < 0]
                        z = ranksum_z_tiecorrected(Gp, Gm)
                        if z is not None:
                            zz.append(z)
                self.a[c] = max([abs(z) for z in zz], default=0.0)

        self.t_next += 1
        return self.a.copy(), self.secondary_support()

    def secondary_support(self):
        return self.a.copy()


# =====================================================================
# Arm 2: Passive Delay-Aware Comparator (comparator-spec.md, v3)
# =====================================================================
class PassiveDelayAwareComparator:
    """Delay-aware passive comparator with D-11.2a action-residual covariance score."""

    def __init__(self, C, K):
        self.C = C
        self.K = K
        self.LAM_REL = 1e-4
        self.LAM_A = 1e-6
        self.KAPPA_MIN = 1e-4
        self.W = 500
        self.Z_CAP = 8.0
        self.D_CAP = 1e4
        self.RAW_ABSENT = -(self.D_CAP + 1.0)
        self.L_ABSENT = -1.0
        self.N_WARM = max(30, 5 * 3 * K)
        self.SIG_FLOOR = 1e-6
        self.S_FLOOR = 1e-8
        self.SIG_DEG_REL = 1e-2
        self.L_DEG = 1e-3
        self.TAU_MAX = 2
        self.HORIZONS = (1, 2, 3)

        # Learned artefacts (frozen at fit_predictor)
        self.beta_raw = None
        self.b_raw = None
        self.mu = None
        self.sd = None
        self.l = None
        self.degen = None
        self.m_a = None
        self.s_a = None
        self.W_a = None
        self.q = None
        self.sec_static = None

        self.reset_online()

    def fit_predictor(self, transitions_by_ep):
        """Fit linear predictor on fault-free non-probed split (episodes 900..919)."""
        phi_list = []
        Y_list = []
        for ep_data in transitions_by_ep:
            O = ep_data['o']
            A = ep_data['a']
            T_ep = len(A)
            lag = [np.zeros(self.K), np.zeros(self.K)]
            for t in range(T_ep):
                phi_t = np.concatenate([O[t], A[t], lag[0], lag[1], [1.0]])
                phi_list.append(phi_t)
                Y_list.append(O[t + 1])
                lag = [A[t], lag[0]]

        phi = np.array(phi_list)
        Y = np.array(Y_list)
        n = len(Y)

        m = phi[:, :-1].mean(axis=0)
        s = np.maximum(phi[:, :-1].std(axis=0, ddof=0), self.S_FLOOR)
        Xt = np.hstack([(phi[:, :-1] - m) / s, np.ones((n, 1))])

        # Intercept unpenalised
        D = np.diag([1.0] * (self.C + 3 * self.K) + [0.0])
        lam = self.LAM_REL * n
        Bt = np.linalg.solve(Xt.T @ Xt + lam * D, Xt.T @ Y)

        self.beta_raw = Bt[:-1] / s[:, None]
        self.b_raw = Bt[-1] - (m / s) @ Bt[:-1]

        R = Y - (phi[:, :-1] @ self.beta_raw + self.b_raw)
        self.mu = R.mean(axis=0)
        self.sd = np.maximum(R.std(axis=0, ddof=1), self.SIG_FLOOR)

        bo = self.beta_raw[:self.C]
        ba = [self.beta_raw[self.C + j * self.K : self.C + (j + 1) * self.K] for j in (0, 1, 2)]
        J = np.zeros((self.K, self.C))
        l = np.zeros(self.C)
        for h in self.HORIZONS:
            J = J @ bo + ba[h - 1]
            l = np.maximum(l, np.linalg.norm(J, axis=0) / self.sd)
        self.l = l

        self.degen = (self.sd < self.SIG_DEG_REL * np.median(self.sd)) & (self.l < self.L_DEG)

        self.m_a = m[self.C : self.C + 3 * self.K]
        self.s_a = s[self.C : self.C + 3 * self.K]
        At = (phi[:, self.C : self.C + 3 * self.K] - self.m_a) / self.s_a
        Sig = (At.T @ At) / n + self.LAM_A * np.eye(3 * self.K)

        nu, V = np.linalg.eigh(Sig)
        keep = nu >= self.KAPPA_MIN * nu.max()
        self.q = int(keep.sum())
        self.W_a = (V[:, keep] / np.sqrt(nu[keep])).T

        self.sec_static = round_sig(self.l, 12)
        self.sec_static[self.degen] = self.L_ABSENT

    def reset_online(self):
        self.t_ep = 0
        self.lag = [np.zeros(self.K), np.zeros(self.K)]
        self.ring_r = deque()
        self.ring_a = deque()
        if self.q is not None:
            self.acc = np.zeros((self.C, self.q))
        else:
            self.acc = None

    def update(self, t, prev_obs, applied_action, obs):
        if t == 0:
            self.reset_online()
        self.t_ep += 1

        phi_t = np.concatenate([prev_obs, applied_action, self.lag[0], self.lag[1]])
        res = obs - (phi_t @ self.beta_raw + self.b_raw)
        rt = np.clip((res - self.mu) / self.sd, -self.Z_CAP, self.Z_CAP)
        a_std = (phi_t[self.C : self.C + 3 * self.K] - self.m_a) / self.s_a
        a_w = self.W_a @ a_std

        self.lag = [applied_action, self.lag[0]]

        if len(self.ring_r) == self.W:
            r_old = self.ring_r.popleft()
            a_old = self.ring_a.popleft()
            self.acc -= np.outer(r_old, a_old)

        self.ring_r.append(rt)
        self.ring_a.append(a_w)
        self.acc += np.outer(rt, a_w)

        n = min(self.W, self.t_ep)
        if self.t_ep < self.N_WARM:
            Delta = np.zeros(self.C)
        else:
            Delta = np.sqrt(n) * np.linalg.norm(self.acc / n, axis=1)

        Dhat = np.minimum(Delta, self.D_CAP)
        raw = round_sig(-Dhat, 12)
        raw[self.degen] = self.RAW_ABSENT

        return raw, self.secondary_support()

    def secondary_support(self):
        return self.sec_static.copy()


# =====================================================================
# Simulation Runner & Evaluator
# =====================================================================
def run_cell_simulation(cfg, seeds=range(10), episode_seeds=range(4), run_arm3=False):
    """Run simulation for one cell configuration across specified seeds and episodes."""
    results = {
        "cfg": cfg,
        "seeds": list(seeds),
        "instances": {},
    }

    offsets_step = {200: 1199, 500: 1499, 1000: 1999}
    offsets_epoch = {200: 1182, 500: 1482, 1000: 1982}

    for seed in seeds:
        # Draw certified present instance
        inst_pres = draw_certified(cfg, seed)
        # Confounder absent is deep copy with G[:] = 0.0, identical seed
        inst_abs = copy.deepcopy(inst_pres)
        inst_abs.G[:] = 0.0

        inst_data = {
            "n_resamples": inst_pres.n_resamples,
            "s_change": inst_pres.certification["s_change"],
            "n_lost": inst_pres.certification["n_lost"],
            "pre_S_count": int(inst_pres.S_obs_pre_event().sum()),
            "present": {},
            "absent": {},
        }

        for cond_name, inst in [("present", inst_pres), ("absent", inst_abs)]:
            C = inst.C
            K = inst.cfg["K"]

            # 1. Fit comparator on episodes 900..919
            fit_episodes = []
            for ep_fit in range(900, 920):
                # Fresh deep copy for each rollout
                inst_copy = copy.deepcopy(inst)
                r = inst_copy.run(2000, ep=ep_fit)
                fit_episodes.append({'o': r['o'], 'a': r['a']})

            comp = PassiveDelayAwareComparator(C, K)
            comp.fit_predictor(fit_episodes)

            # 2. Scored episodes 0..3
            ep_results = []
            for ep in episode_seeds:
                # Arm 1 (seq_ibd) setup
                ibd = SeqIBDEstimator(C, K, probe_rng_seed=[5477, inst.seed, ep, 1])
                probes = ibd.precompute_probes(2000)
                probe_actions_for_gen = {t: act for t, (act, k, sgn) in probes.items()}

                # Scored rollout for Arm 1 (probed)
                inst_ep_ibd = copy.deepcopy(inst)
                r_ibd = inst_ep_ibd.run(2000, ep=ep, actions=probe_actions_for_gen,
                                        event_t=1000, event=("actuator_loss", 0))

                # Scored rollout for Arm 2 (unprobed)
                inst_ep_comp = copy.deepcopy(inst)
                r_comp = inst_ep_comp.run(2000, ep=ep, actions=None,
                                         event_t=1000, event=("actuator_loss", 0))

                # Labels
                pre_S = inst.S_obs_pre_event()
                post_S = inst_ep_comp.S_obs()

                # Step-by-step update for Arm 1
                O_ibd, A_ibd = r_ibd['o'], r_ibd['a']
                ibd_raw_at_offsets = {}
                ibd.reset()
                for t in range(2000):
                    p_info = probes.get(t, None)
                    raw, _ = ibd.update(t, O_ibd[t], A_ibd[t], O_ibd[t + 1], p_info)
                    if t in offsets_epoch.values():
                        ibd_raw_at_offsets[t] = raw.copy()

                # Step-by-step update for Arm 2
                O_comp, A_comp = r_comp['o'], r_comp['a']
                comp_raw_at_offsets = {}
                comp.reset_online()
                for t in range(2000):
                    raw, _ = comp.update(t, O_comp[t], A_comp[t], O_comp[t + 1])
                    if t in offsets_step.values():
                        comp_raw_at_offsets[t] = raw.copy()

                # Optional Arm 3 (probed comparator)
                comp3_raw_at_offsets = {}
                if run_arm3:
                    comp3 = PassiveDelayAwareComparator(C, K)
                    comp3.fit_predictor(fit_episodes)
                    comp3.reset_online()
                    for t in range(2000):
                        raw, _ = comp3.update(t, O_ibd[t], A_ibd[t], O_ibd[t + 1])
                        if t in offsets_step.values():
                            comp3_raw_at_offsets[t] = raw.copy()

                # Metrics at each offset
                ep_metric = {"ep": ep, "offsets": {}}
                for off in [200, 500, 1000]:
                    t_ep_comp = offsets_step[off]
                    t_ep_ibd = offsets_epoch[off]

                    ibd_raw = ibd_raw_at_offsets[t_ep_ibd]
                    comp_raw = comp_raw_at_offsets[t_ep_comp]

                    auc_ibd = auc_pre_event_support(ibd_raw, pre_S, post_S)
                    auc_comp = auc_pre_event_support(comp_raw, pre_S, post_S)

                    sec_ibd = auc_prob_superiority(ibd.secondary_support(), post_S)
                    sec_comp = auc_prob_superiority(comp.secondary_support(), post_S)

                    # Controls on primary
                    const_control = auc_pre_event_support(np.zeros(C), pre_S, post_S)
                    static_control = auc_pre_event_support(comp.secondary_support(), pre_S, post_S)

                    off_res = {
                        "auc_ibd": auc_ibd,
                        "auc_comp": auc_comp,
                        "sec_ibd": sec_ibd,
                        "sec_comp": sec_comp,
                        "const_control": const_control,
                        "static_control": static_control,
                    }
                    if run_arm3:
                        comp3_raw = comp3_raw_at_offsets[t_ep_comp]
                        off_res["auc_comp3"] = auc_pre_event_support(comp3_raw, pre_S, post_S)
                        off_res["sec_comp3"] = auc_prob_superiority(comp3.secondary_support(), post_S)

                    ep_metric["offsets"][off] = off_res

                ep_results.append(ep_metric)

            inst_data[cond_name]["episodes"] = ep_results

        results["instances"][seed] = inst_data

    return results


def summarize_cell(results):
    """Aggregate per-cell primary AUC, confounding benefit with clustered 95% CI,
    comparator floor, secondary AUC, controls, and n_lost."""
    seeds = results["seeds"]
    n_inst = len(seeds)

    # 1. Distribution of n_lost
    n_lost_vals = [results["instances"][s]["n_lost"] for s in seeds]
    pre_S_counts = [results["instances"][s]["pre_S_count"] for s in seeds]

    summary = {
        "cfg": results["cfg"],
        "n_instances": n_inst,
        "n_lost_dist": {v: n_lost_vals.count(v) for v in sorted(set(n_lost_vals))},
        "pre_S_mean": float(np.mean(pre_S_counts)),
        "offsets": {},
    }

    t_crit = 2.262 if n_inst == 10 else (2.776 if n_inst == 5 else 1.96)

    for off in [200, 500, 1000]:
        off_sum = {}
        for cond in ["present", "absent"]:
            ibd_means_per_inst = []
            comp_means_per_inst = []
            sec_ibd_per_inst = []
            sec_comp_per_inst = []
            const_per_inst = []
            static_per_inst = []

            for s in seeds:
                eps = results["instances"][s][cond]["episodes"]
                ibd_vals = [e["offsets"][off]["auc_ibd"] for e in eps]
                comp_vals = [e["offsets"][off]["auc_comp"] for e in eps]
                sec_ibd_vals = [e["offsets"][off]["sec_ibd"] for e in eps]
                sec_comp_vals = [e["offsets"][off]["sec_comp"] for e in eps]
                const_vals = [e["offsets"][off]["const_control"] for e in eps]
                static_vals = [e["offsets"][off]["static_control"] for e in eps]

                ibd_means_per_inst.append(np.mean(ibd_vals))
                comp_means_per_inst.append(np.mean(comp_vals))
                sec_ibd_per_inst.append(np.mean(sec_ibd_vals))
                sec_comp_per_inst.append(np.mean(sec_comp_vals))
                const_per_inst.append(np.mean(const_vals))
                static_per_inst.append(np.mean(static_vals))

            ibd_mean = float(np.mean(ibd_means_per_inst))
            comp_mean = float(np.mean(comp_means_per_inst))
            comp_se = float(np.std(comp_means_per_inst, ddof=1) / np.sqrt(n_inst)) if n_inst > 1 else 0.0
            comp_ci_lo = comp_mean - t_crit * comp_se

            off_sum[f"{cond}_ibd_primary"] = ibd_mean
            off_sum[f"{cond}_comp_primary"] = comp_mean
            off_sum[f"{cond}_comp_ci_lo"] = comp_ci_lo
            off_sum[f"{cond}_ibd_sec"] = float(np.mean(sec_ibd_per_inst))
            off_sum[f"{cond}_comp_sec"] = float(np.mean(sec_comp_per_inst))
            off_sum[f"{cond}_const_ctrl"] = float(np.mean(const_per_inst))
            off_sum[f"{cond}_static_ctrl"] = float(np.mean(static_per_inst))

        # Confounding benefit: [Delta_AUC(present) - Delta_AUC(absent)] clustered by instance
        benefit_per_inst = []
        for s in seeds:
            eps_pres = results["instances"][s]["present"]["episodes"]
            eps_abs = results["instances"][s]["absent"]["episodes"]
            d_pres = np.mean([e["offsets"][off]["auc_ibd"] - e["offsets"][off]["auc_comp"] for e in eps_pres])
            d_abs = np.mean([e["offsets"][off]["auc_ibd"] - e["offsets"][off]["auc_comp"] for e in eps_abs])
            benefit_per_inst.append(d_pres - d_abs)

        b_mean = float(np.mean(benefit_per_inst))
        b_se = float(np.std(benefit_per_inst, ddof=1) / np.sqrt(n_inst)) if n_inst > 1 else 0.0
        b_ci_lo = b_mean - t_crit * b_se
        b_ci_hi = b_mean + t_crit * b_se

        off_sum["benefit_mean"] = b_mean
        off_sum["benefit_se"] = b_se
        off_sum["benefit_ci"] = (b_ci_lo, b_ci_hi)

        summary["offsets"][off] = off_sum

    return summary


# =====================================================================
# Main Execution: Base Cells, Perturbations, Family N
# =====================================================================
def run_all_and_report():
    print("=" * 80)
    print("REVIEW 6 (GEMINI) REPRODUCTION: FROZEN SUITE (38d161e762a3de76)")
    print("=" * 80)
    start_total = time.time()

    # 1. Base Cells (Family L, seeds 0..9)
    base_cells = [
        {"family": "L", "N_x": 10, "tau": 0},
        {"family": "L", "N_x": 30, "tau": 0},
        {"family": "L", "N_x": 10, "tau": 2},
        {"family": "L", "N_x": 30, "tau": 2},
    ]

    base_summaries = []
    print("\n>>> RUNNING FAMILY L BASE CELLS (Seeds 0..9, 4 cells) <<<")
    for cfg in base_cells:
        t0 = time.time()
        print(f"Running cell: N_x={cfg['N_x']}, tau={cfg['tau']} ...", flush=True)
        res = run_cell_simulation(cfg, seeds=range(10), episode_seeds=range(4))
        summ = summarize_cell(res)
        base_summaries.append(summ)
        t1 = time.time()
        print(f"Done in {t1 - t0:.1f}s. Primary offset 500: Seq-IBD={summ['offsets'][500]['present_ibd_primary']:.3f}, Comp={summ['offsets'][500]['present_comp_primary']:.3f}, Benefit={summ['offsets'][500]['benefit_mean']:+.3f} [{summ['offsets'][500]['benefit_ci'][0]:.3f}, {summ['offsets'][500]['benefit_ci'][1]:.3f}]")

    # 2. Perturbation Set at Seed 0 (Family L, N_x=10, tau=0)
    print("\n>>> RUNNING PERTURBATION SET AT SEED 0 <<<")
    perturb_summaries = []
    for coupling in [0.5, 1.0, 2.0]:
        for noise in [0.5, 1.0, 2.0]:
            cfg_pert = {"family": "L", "N_x": 10, "tau": 0, "coupling": coupling, "noise_mult": noise}
            res_pert = run_cell_simulation(cfg_pert, seeds=[0], episode_seeds=range(4))
            summ_pert = summarize_cell(res_pert)
            perturb_summaries.append((coupling, noise, summ_pert))
            off500 = summ_pert['offsets'][500]
            print(f"Perturbation coupling={coupling}, noise={noise}: offset 500 IBD(pres)={off500['present_ibd_primary']:.3f}, Comp(pres)={off500['present_comp_primary']:.3f}, Comp(abs)={off500['absent_comp_primary']:.3f}, Benefit={off500['benefit_mean']:+.3f}")

    # 3. Family N (seeds 0..4, N_x=10, tau in {0, 2})
    print("\n>>> RUNNING FAMILY N (N_x=10, tau in {0, 2}, seeds 0..4) <<<")
    family_N_summaries = []
    for tau in [0, 2]:
        t0 = time.time()
        cfg_N = {"family": "N", "N_x": 10, "tau": tau}
        print(f"Running Family N tau={tau} seeds 0..4 ...", flush=True)
        res_N = run_cell_simulation(cfg_N, seeds=range(5), episode_seeds=range(4))
        summ_N = summarize_cell(res_N)
        family_N_summaries.append(summ_N)
        t1 = time.time()
        print(f"Done in {t1 - t0:.1f}s. Primary offset 500: Seq-IBD={summ_N['offsets'][500]['present_ibd_primary']:.3f}, Comp={summ_N['offsets'][500]['present_comp_primary']:.3f}, Benefit={summ_N['offsets'][500]['benefit_mean']:+.3f}")

    total_time = time.time() - start_total
    print(f"\nAll simulations completed in {total_time:.1f}s ({total_time / 60.0:.2f} min).")

    # =================================================================
    # Formatted Reporting Tables
    # =================================================================
    print("\n" + "=" * 80)
    print("DETAILED RESULTS REPORT")
    print("=" * 80)

    print("\n--- TABLE 1: BASE CELLS (FAMILY L, SEEDS 0..9) PRIMARY PRE-EVENT SUPPORT AUC ---")
    print(f"{'Cell':<18} | {'Offset':<6} | {'IBD(pres)':<9} | {'Comp(pres)':<10} | {'Comp(abs)':<9} | {'Comp(abs) Lo':<12} | {'Floor>=0.85?':<12} | {'Benefit [95% CI]':<22}")
    print("-" * 115)
    for s in base_summaries:
        cell_name = f"Nx={s['cfg']['N_x']}, tau={s['cfg']['tau']}"
        for off in [200, 500, 1000]:
            o = s["offsets"][off]
            floor_pass = "PASS" if o["absent_comp_ci_lo"] >= 0.85 else "FAIL"
            ci_str = f"{o['benefit_mean']:+.3f} [{o['benefit_ci'][0]:+.3f}, {o['benefit_ci'][1]:+.3f}]"
            print(f"{cell_name:<18} | {off:<6} | {o['present_ibd_primary']:<9.3f} | {o['present_comp_primary']:<10.3f} | {o['absent_comp_primary']:<9.3f} | {o['absent_comp_ci_lo']:<12.3f} | {floor_pass:<12} | {ci_str:<22}")

    print("\n--- TABLE 2: CONTROLS & SECONDARY FULL-CHANNEL AUC (OFFSET 500) ---")
    print(f"{'Cell':<18} | {'Const Ctrl':<10} | {'Static Ctrl(pres)':<18} | {'Static Ctrl(abs)':<16} | {'Sec IBD(pres)':<14} | {'Sec Comp(pres)':<14} | {'Sec Comp(abs)':<14}")
    print("-" * 115)
    for s in base_summaries:
        cell_name = f"Nx={s['cfg']['N_x']}, tau={s['cfg']['tau']}"
        o = s["offsets"][500]
        print(f"{cell_name:<18} | {o['present_const_ctrl']:<10.3f} | {o['present_static_ctrl']:<18.3f} | {o['absent_static_ctrl']:<16.3f} | {o['present_ibd_sec']:<14.3f} | {o['present_comp_sec']:<14.3f} | {o['absent_comp_sec']:<14.3f}")

    print("\n--- TABLE 3: INSTANCE SUPPORT & LOST CHANNELS DISTRIBUTION ---")
    for s in base_summaries:
        cell_name = f"Nx={s['cfg']['N_x']}, tau={s['cfg']['tau']}"
        print(f"{cell_name}: Pre-event support mean={s['pre_S_mean']:.1f}, n_lost distribution: {s['n_lost_dist']}")

    print("\n--- TABLE 4: PERTURBATION SET (SEED 0, FAMILY L, Nx=10, tau=0, OFFSET 500) ---")
    print(f"{'Coupling':<8} | {'Noise':<6} | {'IBD(pres)':<9} | {'Comp(pres)':<10} | {'Comp(abs)':<9} | {'Benefit':<10} | {'Sec IBD(pres)':<14} | {'Sec Comp(abs)':<14}")
    print("-" * 95)
    for coupling, noise, sp in perturb_summaries:
        o = sp["offsets"][500]
        print(f"{coupling:<8.1f} | {noise:<6.1f} | {o['present_ibd_primary']:<9.3f} | {o['present_comp_primary']:<10.3f} | {o['absent_comp_primary']:<9.3f} | {o['benefit_mean']:<+10.3f} | {o['present_ibd_sec']:<14.3f} | {o['absent_comp_sec']:<14.3f}")

    print("\n--- TABLE 5: FAMILY N REPRODUCTION TARGET (SEEDS 0..4, Nx=10) ---")
    print(f"{'Cell':<18} | {'Offset':<6} | {'IBD(pres)':<9} | {'Comp(pres)':<10} | {'Comp(abs)':<9} | {'Benefit':<10} | {'Sec IBD(pres)':<14} | {'Sec Comp(abs)':<14}")
    print("-" * 95)
    for s in family_N_summaries:
        cell_name = f"Family N, tau={s['cfg']['tau']}"
        for off in [200, 500, 1000]:
            o = s["offsets"][off]
            print(f"{cell_name:<18} | {off:<6} | {o['present_ibd_primary']:<9.3f} | {o['present_comp_primary']:<10.3f} | {o['absent_comp_primary']:<9.3f} | {o['benefit_mean']:<+10.3f} | {o['present_ibd_sec']:<14.3f} | {o['absent_comp_sec']:<14.3f}")

    print("\n" + "=" * 80)
    print("EXIT CONDITION EVALUATION (Contract v3.9 Section L)")
    print("=" * 80)
    # Check D-10.3 floor and confounding benefit
    floor_all_pass = True
    benefit_all_pass = True
    for s in base_summaries:
        cell_name = f"Nx={s['cfg']['N_x']}, tau={s['cfg']['tau']}"
        o500 = s["offsets"][500]
        lo_floor = o500["absent_comp_ci_lo"]
        if lo_floor < 0.85:
            floor_all_pass = False
            print(f"FAIL: D-10.3 competence floor failed in {cell_name} at offset 500: lower bound {lo_floor:.3f} < 0.85")
        else:
            print(f"PASS: D-10.3 competence floor met in {cell_name} at offset 500: lower bound {lo_floor:.3f} >= 0.85")

        lo_ben = o500["benefit_ci"][0]
        if lo_ben < 0.10:
            benefit_all_pass = False
            print(f"FAIL: Confounding benefit lower bound < 0.10 in {cell_name} at offset 500: {lo_ben:.3f} < 0.10")
        else:
            print(f"PASS: Confounding benefit lower bound >= 0.10 in {cell_name} at offset 500: {lo_ben:.3f} >= 0.10")

    print(f"\nOverall Competence Floor (Absent Lower Bound >= 0.85): {'MET' if floor_all_pass else 'FAILED'}")
    print(f"Overall Confounding Benefit (Lower Bound >= 0.10): {'MET' if benefit_all_pass else 'FAILED'}")
    print("=" * 80)


if __name__ == "__main__":
    run_all_and_report()
