#!/usr/bin/env python3
"""Independent round-6 reproduction from comparator v3 and sequential-IBD draft 5.

Run from this directory with the frozen gate environment on sys.path, e.g.
  PYTHONPATH=../executable-proofs/gate python3 sim_frozen.py

Only threshold-free primary/secondary outcomes are simulated. Alarm calibration is
orthogonal to these outcomes and is attacked analytically in findings.md.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from reference_generator import draw_certified
from contract_ref import auc_pre_event_support, auc_prob_superiority


OFFSETS = (200, 500, 1000)
EVENT_T = 1000
T = 2000
PROBE_NS = 5477
TCRIT = {5: 2.7764451051977987, 10: 2.2621571628540993}


def round_sig(x: np.ndarray) -> np.ndarray:
    return np.array([float(f"{v:.11e}") for v in np.asarray(x).ravel()]).reshape(np.shape(x))


def episode(inst, ep: int, actions=None, event: bool = False):
    obj = copy.deepcopy(inst)
    out = obj.run(T, ep=ep, actions=actions,
                  event_t=EVENT_T if event else None,
                  event=("actuator_loss", 0) if event else None)
    return out, obj


def design(run):
    O, A = run["o"], run["a"]
    z = np.zeros_like(A)
    lag1 = np.vstack([z[:1], A[:-1]])
    lag2 = np.vstack([z[:2], A[:-2]])
    return np.column_stack([O[:-1], A, lag1, lag2]), O[1:]


class Comparator:
    def __init__(self, inst):
        self.C, self.K = inst.C, inst.cfg["K"]
        xx, yy = [], []
        for ep in range(900, 920):
            run, _ = episode(inst, ep)
            X, Y = design(run); xx.append(X); yy.append(Y)
        phi, Y = np.vstack(xx), np.vstack(yy)
        self.m = phi.mean(0)
        self.s = np.maximum(phi.std(0, ddof=0), 1e-8)
        Xt = np.column_stack([(phi - self.m) / self.s, np.ones(len(phi))])
        D = np.eye(Xt.shape[1]); D[-1, -1] = 0.0
        lam = 1e-4 * len(phi)
        gram = Xt.T @ Xt + lam * D
        chol = np.linalg.cholesky(gram)
        beta_t = np.linalg.solve(chol.T, np.linalg.solve(chol, Xt.T @ Y))
        self.beta = beta_t[:-1] / self.s[:, None]
        self.intercept = beta_t[-1] - (self.m / self.s) @ beta_t[:-1]
        R = Y - Xt @ beta_t
        self.mu = R.mean(0)
        self.sd = np.maximum(R.std(0, ddof=1), 1e-6)

        bo = self.beta[:self.C]
        ba = [self.beta[self.C + h*self.K:self.C + (h+1)*self.K] for h in range(3)]
        J = np.zeros((self.K, self.C)); loading = np.zeros(self.C)
        for h in range(3):
            J = J @ bo + ba[h]
            loading = np.maximum(loading, np.linalg.norm(J, axis=0) / self.sd)
        self.loading = round_sig(loading)

        self.ma = self.m[self.C:self.C + 3*self.K]
        self.sa = self.s[self.C:self.C + 3*self.K]
        At = (phi[:, self.C:self.C + 3*self.K] - self.ma) / self.sa
        Sigma = At.T @ At / len(At) + 1e-6 * np.eye(3*self.K)
        nu, V = np.linalg.eigh(Sigma)
        keep = nu >= 1e-4 * nu.max()
        self.whitener = (V[:, keep] / np.sqrt(nu[keep])).T
        self.q = int(keep.sum())
        self.cond = float(nu.max() / nu.min())
        degen = (self.sd < 1e-2 * np.median(self.sd)) & (loading < 1e-3)
        self.degen = degen
        self.loading[degen] = -1.0

    def scores(self, run):
        phi, Y = design(run)
        R = Y - (phi @ self.beta + self.intercept)
        rt = np.clip((R - self.mu) / self.sd, -8, 8)
        ast = (phi[:, self.C:self.C + 3*self.K] - self.ma) / self.sa
        aw = ast @ self.whitener.T
        out = {}
        for off in OFFSETS:
            t = EVENT_T + off - 1
            lo = max(0, t - 500 + 1)
            n = t - lo + 1
            acc = rt[lo:t+1].T @ aw[lo:t+1]
            delta = math.sqrt(n) * np.linalg.norm(acc / n, axis=1)
            raw = round_sig(-np.minimum(delta, 1e4))
            raw[self.degen] = -10001.0
            out[off] = raw
        return out


def probe_actions(inst, ep: int, length=T):
    rng = np.random.default_rng([PROBE_NS, inst.seed, ep, 1])
    allk = [(k, s) for k in range(inst.cfg["K"]) for s in (1, -1)]
    block, actions = [], {}
    for t in range(20, length, 20):
        if not block:
            block = [allk[i] for i in rng.permutation(2*inst.cfg["K"])]
        k, sign = block.pop(0)
        a = np.zeros(inst.cfg["K"]); a[k] = sign
        actions[t] = a
    return actions


def ranksum_z(gp, gm):
    np_, nm = len(gp), len(gm)
    if min(np_, nm) < 3:
        return None
    values = round_sig(np.r_[gp, gm])
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), float)
    tie_term = 0.0
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and values[order[j]] == values[order[i]]:
            j += 1
        ranks[order[i:j]] = (i + 1 + j) / 2.0
        q = j - i; tie_term += q**3 - q
        i = j
    N = np_ + nm
    U = ranks[:np_].sum() - np_*(np_+1)/2
    mu = np_*nm/2
    var = np_*nm/(N*(N-1)) * ((N**3-N)/12 - tie_term/12)
    if var <= 0:
        return None
    return float(np.clip((U-mu)/math.sqrt(max(0.0, var)), -8, 8))


def ibd_scores(inst, run, ep: int):
    actions = probe_actions(inst, ep)
    # The supplied run was generated with exactly these probes.
    units = []
    O = run["o"]
    for tp, a in actions.items():
        k = int(np.flatnonzero(a)[0]); sign = int(a[k])
        units.append((tp, k, sign, np.stack([O[tp+h]-O[tp] for h in (1,2,3)])))
    out = {}
    for off, emit_t in zip(OFFSETS, (1182, 1482, 1982)):
        newest = emit_t - 2
        window = [u for u in units if newest - 500 < u[0] <= newest]
        score = np.zeros(inst.C)
        for c in range(inst.C):
            zz = []
            for k in range(inst.cfg["K"]):
                for hi in range(3):
                    gp = [u[3][hi,c] for u in window if u[1] == k and u[2] > 0]
                    gm = [u[3][hi,c] for u in window if u[1] == k and u[2] < 0]
                    z = ranksum_z(gp, gm)
                    if z is not None: zz.append(abs(z))
            score[c] = max(zz, default=0.0)
        out[off] = score
    return out


def t_ci(instance_values):
    x = np.asarray(instance_values, float)
    n = len(x); mean = float(x.mean())
    if n < 2: return [mean, None, None]
    crit = TCRIT.get(n, 1.96)
    half = crit * float(x.std(ddof=1)) / math.sqrt(n)
    return [mean, mean-half, mean+half]


def run_cell(cfg, seeds, label):
    rows, lost, certs = [], [], []
    started = time.time()
    for config_seed in seeds:
        present = draw_certified(cfg, config_seed)
        lost.append(int(present.certification["n_lost"]))
        certs.append({"configuration_seed": config_seed, "instance_seed": present.seed,
                      "n_resamples": present.n_resamples, **present.certification})
        for conf in ("present", "absent"):
            inst = copy.deepcopy(present)
            if conf == "absent": inst.G[:] = 0.0
            cmp = Comparator(inst)
            pre = present.S_obs_pre_event()
            # Post labels depend only on the structural instance; force event on a copy.
            post_obj = copy.deepcopy(inst); post_obj.apply_event(("actuator_loss", 0)); post = post_obj.S_obs()
            static_auc = auc_pre_event_support(cmp.loading, pre, post)
            for ep in range(4):
                actions = probe_actions(inst, ep)
                run_probe, _ = episode(inst, ep, actions=actions, event=True)
                run_passive, _ = episode(inst, ep, actions=None, event=True)
                cs = cmp.scores(run_passive)
                ibs = ibd_scores(inst, run_probe, ep)
                for off in OFFSETS:
                    for arm, score, secondary in (
                        ("seq_ibd", ibs[off], ibs[off]),
                        ("comparator", cs[off], cmp.loading),
                    ):
                        rows.append(dict(label=label, configuration_seed=config_seed,
                                         instance_seed=present.seed, confounder=conf, episode=ep,
                                         offset=off, arm=arm,
                                         primary=auc_pre_event_support(score, pre, post),
                                         secondary=auc_prob_superiority(secondary, post),
                                         static_control=static_auc,
                                         constant_control=auc_pre_event_support(np.zeros(inst.C), pre, post),
                                         q=cmp.q, cond=cmp.cond,
                                         pre_n=int(pre.sum()), post_n=int(post.sum()),
                                         n_lost=int((pre & ~post).sum())))
        print(f"completed {label} seed={config_seed} instance={present.seed} n_lost={lost[-1]}", flush=True)
    return dict(label=label, cfg=cfg, seconds=time.time()-started, rows=rows, n_lost=lost, certifications=certs)


def summarize(blocks):
    summaries = []
    for b in blocks:
        rows = b["rows"]
        for conf in ("present", "absent"):
            for off in OFFSETS:
                entry = {"label": b["label"], "confounder": conf, "offset": off}
                for arm in ("seq_ibd", "comparator"):
                    rr = [r for r in rows if r["confounder"] == conf and r["offset"] == off and r["arm"] == arm]
                    byinst = defaultdict(list)
                    for r in rr: byinst[r["instance_seed"]].append(r)
                    entry[arm] = {
                        "primary_ci": t_ci([np.mean([z["primary"] for z in v]) for v in byinst.values()]),
                        "secondary_ci": t_ci([np.mean([z["secondary"] for z in v]) for v in byinst.values()]),
                    }
                summaries.append(entry)
        # Paired delta and confounding benefit at each offset, clustered by instance.
        for off in OFFSETS:
            inst_ids = sorted({r["instance_seed"] for r in rows})
            deltas = {c: [] for c in ("present", "absent")}
            benefits = []
            for iid in inst_ids:
                d = {}
                for conf in ("present", "absent"):
                    def mean_arm(a):
                        z = [r["primary"] for r in rows if r["instance_seed"] == iid and r["confounder"] == conf and r["offset"] == off and r["arm"] == a]
                        return float(np.mean(z))
                    d[conf] = mean_arm("seq_ibd") - mean_arm("comparator")
                    deltas[conf].append(d[conf])
                benefits.append(d["present"] - d["absent"])
            summaries.append({"label": b["label"], "offset": off,
                              "delta_present_ci": t_ci(deltas["present"]),
                              "delta_absent_ci": t_ci(deltas["absent"]),
                              "confounding_benefit_ci": t_ci(benefits)})
        # Controls are instance-level (static repeats across episodes/offsets).
        inst_static = defaultdict(list); inst_const = defaultdict(list)
        for r in rows:
            if r["confounder"] == "absent" and r["arm"] == "comparator" and r["offset"] == 500:
                inst_static[r["instance_seed"]].append(r["static_control"])
                inst_const[r["instance_seed"]].append(r["constant_control"])
        summaries.append({"label": b["label"],
                          "static_loading_control_ci": t_ci([np.mean(v) for v in inst_static.values()]),
                          "channel_constant_control_ci": t_ci([np.mean(v) for v in inst_const.values()]),
                          "n_lost_distribution": dict(Counter(b["n_lost"])),
                          "seconds": b["seconds"]})
    return summaries


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--quick", action="store_true", help="use seeds 0..1 (debug only)")
    p.add_argument("--output", default="sim_frozen.results.json")
    args = p.parse_args()
    seeds_L = range(2) if args.quick else range(10)
    seeds_N = range(2) if args.quick else range(5)
    blocks = []
    for nx in (10, 30):
        for tau in (0, 2):
            blocks.append(run_cell({"family":"L", "N_x":nx, "tau":tau}, seeds_L, f"L_Nx{nx}_tau{tau}"))
    # Full 3x3 Cartesian perturbation grid at the base N_x=10, tau=0 cell.
    for coupling in (0.5, 1.0, 2.0):
        for noise in (0.5, 1.0, 2.0):
            blocks.append(run_cell({"family":"L", "N_x":10, "tau":0,
                                    "coupling":coupling, "noise_mult":noise}, [0],
                                   f"pert_c{coupling:g}_n{noise:g}"))
    for tau in (0, 2):
        blocks.append(run_cell({"family":"N", "N_x":10, "tau":tau}, seeds_N, f"N_Nx10_tau{tau}"))
    result = {"numpy": np.__version__, "quick": args.quick,
              "choices": {"perturbation_interpretation":"full Cartesian 3x3 at family L, N_x=10, tau=0",
                          "interval":"two-sided t interval over per-instance means; episodes averaged within instance",
                          "comparator_stream":"passive task-policy stream; IBD stream carries its specified probes"},
              "summaries": summarize(blocks), "blocks": blocks}
    path = Path(args.output)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(path), "summaries": result["summaries"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
