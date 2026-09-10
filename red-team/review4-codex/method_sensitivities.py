#!/usr/bin/env python3
"""Executable checks supporting review4-codex findings."""
from __future__ import annotations

import json
import numpy as np

import independent_end_to_end as base


def delayed_actions(actions, tau):
    if tau == 0:
        return actions
    return np.vstack([np.zeros((tau, actions.shape[1])), actions[:-tau]])


def fit_delay_aware(inst, confounder):
    xs, ys = [], []
    for ep in range(20):
        o, a, _ = base.simulate(inst, 10_000 + ep, confounder, False, False)
        xs.append(np.c_[o[:-1], delayed_actions(a, inst.tau), np.ones(base.T)])
        ys.append(o[1:])
    X, Y = np.vstack(xs), np.vstack(ys)
    xtx = X.T @ X; lam = 1e-4 * np.trace(xtx) / (inst.c + base.K)
    D = np.eye(X.shape[1]); D[-1, -1] = 0
    beta = np.linalg.solve(xtx + lam * D, X.T @ Y)
    residual = Y - X @ beta
    mu = residual.mean(0); raw_sd = residual.std(0, ddof=1); sd = np.maximum(raw_sd, 1e-6)
    loading = np.linalg.norm(beta[inst.c : inst.c + base.K], axis=0) / sd
    return beta, mu, sd, raw_sd < 1e-3, loading


def score_delay_aware(o, a, fit, inst):
    beta, mu, sd, degen, loading = fit
    X = np.c_[o[:-1], delayed_actions(a, inst.tau), np.ones(base.T)]
    rt = np.clip((o[1:] - X @ beta - mu) / sd, -8, 8)
    q = np.clip(loading - np.abs(np.sqrt(500) * rt[1000:1500].mean(0)), -40, 40)
    q[degen] = -40
    return q


def ibd_after_action(o, probe_meta, score_step=1500):
    newest = max(t for t in range(20, score_step + 1, 20) if t + 3 <= score_step)
    anchors = [t for t in range(20, newest + 1, 20) if t > newest - 500]
    units = []
    for t in anchors:
        _, k, sign = probe_meta[t - 1]
        increments = np.stack([o[t + h] - o[t] for h in base.HSET])
        units.append((k, sign, increments))
    scores = np.zeros(o.shape[1])
    for c in range(o.shape[1]):
        zs = []
        for k in range(2):
            for hi in range(3):
                plus = [u[2][hi, c] for u in units if u[0] == k and u[1] > 0]
                minus = [u[2][hi, c] for u in units if u[0] == k and u[1] < 0]
                if min(len(plus), len(minus)) >= 3:
                    zs.append(abs(base.ranksum_z(plus, minus)))
        scores[c] = max(zs, default=0)
    return scores


def main():
    out = {}
    # Tie-corrected hand anchor.
    plus, minus = [1.0, 1.0, 2.0], [1.0, 3.0, 3.0]
    ranks, ties = base.midranks_ties(np.r_[plus, minus])
    out["tie_fixture"] = {"ranks": ranks.tolist(), "tie_sizes": ties,
                          "variance": 4.5, "z": base.ranksum_z(plus, minus)}

    grants = []; used = 0; last = -20
    for t in range(1, 2001):
        if used + 1 <= int(0.05 * t) and t - last >= 20:
            grants.append(t); used += 1; last = t
    out["probe_clock"] = {"applied": len(grants), "usable": sum(t + 3 <= 2000 for t in grants),
                          "first": grants[:3], "last": grants[-3:]}

    # Probability that at least one actuator has an unusable sign group at the primary window.
    nrep = 200_000; any_bad = 0; actuator_usable = 0
    for seed in range(nrep):
        rng = np.random.default_rng(seed + 90_000_001); bins = np.zeros((2, 2), int)
        for t in range(20, 1481, 20):
            k = int(rng.integers(2)); sign = int(rng.integers(2))
            if t >= 1000:
                bins[k, sign] += 1
        usable = bins.min(axis=1) >= 3
        any_bad += int(not usable.all()); actuator_usable += int(usable.sum())
    out["nmin_randomness"] = {"per_actuator_usable": actuator_usable / (2 * nrep),
                              "at_least_one_actuator_unusable": any_bad / nrep}

    # The equally plausible after-action o(t_p) interpretation.
    anchor = []
    for nx in (10, 30):
        for conf in (False, True):
            inst = base.make_instance(nx, 0); y = base.support_labels(inst); vals = []
            for seed in range(100, 140):
                o, _, pm = base.simulate(inst, seed, conf, True, True)
                vals.append(base.auc(y, ibd_after_action(o, pm)))
            anchor.append({"nx": nx, "confounder": "present" if conf else "absent",
                           "mean_auc": float(np.mean(vals)),
                           "se": float(np.std(vals, ddof=1) / np.sqrt(len(vals)))})
    out["after_action_anchor"] = anchor

    # Delay-aware passive comparator at tau=2.
    delayed = []
    inst = base.make_instance(30, 2); y = base.support_labels(inst)
    for conf in (False, True):
        fit = fit_delay_aware(inst, conf); vals = []
        for seed in range(100, 140):
            o, a, _ = base.simulate(inst, seed, conf, False, True)
            vals.append(base.auc(y, score_delay_aware(o, a, fit, inst)))
        delayed.append({"confounder": "present" if conf else "absent", "mean_auc": float(np.mean(vals)),
                        "se": float(np.std(vals, ddof=1) / np.sqrt(len(vals)))})
    out["delay_aware_comparator_tau2_nx30"] = delayed

    # Ridge unit-scaling counterexample.
    rng = np.random.default_rng(11); n = 40_000; C = 3; K = 2
    xo = rng.normal(size=(n, C)); act = rng.normal(size=(n, K))
    Y = 0.6 * xo + act @ np.array([[0.4, 0.0, 0.2], [0.0, 0.3, 0.1]]) + rng.normal(0, 0.2, (n, C))
    def ridge_loading(x, y):
        X = np.c_[x, act, np.ones(n)]; xx = X.T @ X; lam = 1e-4 * np.trace(xx) / (C + K)
        D = np.eye(C + K + 1); D[-1, -1] = 0; beta = np.linalg.solve(xx + lam * D, X.T @ y)
        sd = (y - X @ beta).std(0, ddof=1)
        return lam, np.linalg.norm(beta[C:C + K], axis=0) / sd
    lam0, load0 = ridge_loading(xo, Y); scale = np.array([100.0, 1.0, 1.0])
    lam1, load1 = ridge_loading(xo * scale, Y * scale)
    out["ridge_unit_scaling"] = {"lambda_before": lam0, "lambda_after": lam1,
                                 "loading_before": load0.tolist(), "loading_after": load1.tolist(),
                                 "relative_change": (load1 / load0 - 1).tolist()}

    # Independent observation noise makes equal-gain copies non-identical.
    rng = np.random.default_rng(7); n = 40_000; z = np.zeros(n + 1); act = rng.normal(size=n)
    for t in range(n):
        z[t + 1] = 0.7 * z[t] + 0.4 * act[t] + rng.normal(0, 0.1)
    obs = np.c_[z + rng.normal(0, 0.05, n + 1), z + rng.normal(0, 0.05, n + 1)]
    X = np.c_[obs[:-1], act, np.ones(n)]; Y = obs[1:]; xx = X.T @ X
    D = np.diag([1, 1, 1, 0]); beta = np.linalg.solve(xx + 1e-4 * np.trace(xx) / 3 * D, X.T @ Y)
    R = Y - X @ beta; mu = R.mean(0); sd = R.std(0, ddof=1)
    loading = np.abs(beta[2]) / sd; rt = np.clip((R - mu) / sd, -8, 8)
    q = loading - np.abs(np.sqrt(500) * np.array([rt[i - 499:i + 1].mean(0) for i in range(499, n)]))
    diff = np.abs(q[:, 0] - q[:, 1])
    out["copy_noise"] = {"median_abs_q_difference": float(np.median(diff)),
                         "max_abs_q_difference": float(diff.max()),
                         "fraction_below_1e-6": float(np.mean(diff < 1e-6))}
    pad = rng.normal(0, 0.05, n + 1)
    out["noise_padding"] = {"transition_sd": float(np.std(pad[1:], ddof=1)),
                            "degenerate_under_1e-3": bool(np.std(pad[1:], ddof=1) < 1e-3)}

    path = __file__.replace("method_sensitivities.py", "method_sensitivities.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2); f.write("\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
