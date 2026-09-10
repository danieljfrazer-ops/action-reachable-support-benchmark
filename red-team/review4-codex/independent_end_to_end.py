#!/usr/bin/env python3
"""Independent implementations of the two round-4 method specifications.

This file intentionally imports nothing from review folders or the gate.  It
implements one fixed family-L contract-B instance, sequential IBD draft 3, and
the passive comparator draft 1.  Only threshold-free support AUC is evaluated.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


T = 2000
EVENT_T = 1000
OFFSET = 500
K = 2
HSET = (1, 2, 3)
PI = 20
W = 500
NMIN = 3


@dataclass(frozen=True)
class Instance:
    nx: int
    tau: int
    Ab: np.ndarray
    B: np.ndarray
    Ad: np.ndarray
    Cd: np.ndarray
    Aw: np.ndarray
    Ax: np.ndarray
    G: np.ndarray

    @property
    def c(self) -> int:
        return 4 + 2 + 4 + self.nx + 4


def make_instance(nx: int, tau: int) -> Instance:
    return Instance(
        nx=nx,
        tau=tau,
        Ab=np.diag([0.65, 0.55, 0.60, 0.50]),
        B=np.array([[0.60, 0.00], [0.35, 0.00], [0.00, 0.55], [0.00, 0.35]]),
        Ad=np.diag([0.50, 0.45]),
        Cd=np.array([[0.35, 0.00, 0.00, 0.00], [0.00, 0.00, 0.35, 0.00]]),
        Aw=np.diag([0.60, 0.55, 0.50, 0.45]),
        Ax=np.diag(np.linspace(0.55, 0.75, nx)),
        G=np.r_[np.linspace(0.45, 0.65, nx // 2), np.zeros(nx - nx // 2)],
    )


def rng_stream(seed: int):
    """Common-random-number stream; shapes do not depend on confounder state."""
    rng = np.random.default_rng(seed)
    return {
        "eu": rng.normal(0, 1.0, T),
        "eb": rng.normal(0, 0.1, (T, 4)),
        "ed": rng.normal(0, 0.1, (T, 2)),
        "ew": rng.normal(0, 0.1, (T, 4)),
        "ex": rng.normal(0, 0.1, (T, 100)),
        "eo": rng.normal(0, 0.05, (T + 1, 114)),
        "ea": rng.normal(0, 0.1, (T, 2)),
    }


def observe(b, d, w, x, eo, c):
    latent = np.r_[b, d, w, x]
    out = np.empty(c)
    out[: len(latent)] = latent + eo[: len(latent)]
    out[len(latent) :] = eo[len(latent) : c]  # four noise-only padding negatives
    return out


def simulate(inst: Instance, seed: int, confounder: bool, probes: bool, event: bool):
    noise = rng_stream(seed)
    b = np.zeros(4); d = np.zeros(2); w = np.zeros(4); x = np.zeros(inst.nx); u = 0.0
    obs = observe(b, d, w, x, noise["eo"][0], inst.c)
    observations = [obs.copy()]
    actions = []
    probe_meta = []
    probe_rng = np.random.default_rng(seed + 90_000_001)
    for step in range(1, T + 1):
        u = 0.8 * u + noise["eu"][step - 1]
        task = np.array([
            -0.25 * obs[0] - 0.15 * obs[1] + 0.80 * u,
            -0.25 * obs[2] - 0.15 * obs[3] - 0.60 * u,
        ]) + noise["ea"][step - 1]
        action = np.clip(task, -2.0, 2.0)
        meta = None
        if probes and step % PI == 0:
            k = int(probe_rng.integers(K)); sign = 1 if probe_rng.integers(2) else -1
            action = np.zeros(K); action[k] = sign
            meta = (step, k, sign)
        actions.append(action.copy()); probe_meta.append(meta)

        delayed_index = len(actions) - 1 - inst.tau
        delayed = actions[delayed_index] if delayed_index >= 0 else np.zeros(K)
        Bnow = inst.B.copy()
        if event and step >= EVENT_T:
            Bnow[:, 0] = 0.0
        old_b = b.copy()
        b = inst.Ab @ b + Bnow @ delayed + noise["eb"][step - 1]
        d = inst.Ad @ d + inst.Cd @ old_b + noise["ed"][step - 1]
        w = inst.Aw @ w + noise["ew"][step - 1]
        gain = inst.G if confounder else np.zeros(inst.nx)
        x = np.diag(inst.Ax) * x + gain * u + noise["ex"][step - 1, : inst.nx]
        obs = observe(b, d, w, x, noise["eo"][step], inst.c)
        observations.append(obs.copy())
    return np.asarray(observations), np.asarray(actions), probe_meta


def support_labels(inst: Instance):
    y = np.zeros(inst.c, dtype=bool)
    # After loss of actuator 0: actuator 1 reaches b2,b3 at tau+1.
    if inst.tau + 1 <= 3:
        y[2:4] = True
    # d1 is one graph hop later and is therefore in support only when tau+2 <= H.
    if inst.tau + 2 <= 3:
        y[5] = True
    return y


def midranks_ties(values):
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), float)
    ties = []
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and values[order[j]] == values[order[i]]:
            j += 1
        ranks[order[i:j]] = (i + 1 + j) / 2.0
        if j - i > 1:
            ties.append(j - i)
        i = j
    return ranks, ties


def ranksum_z(plus, minus):
    np_, nm = len(plus), len(minus); n = np_ + nm
    vals = np.r_[plus, minus]
    ranks, ties = midranks_ties(vals)
    u = ranks[:np_].sum() - np_ * (np_ + 1) / 2
    mu = np_ * nm / 2
    bracket = (n**3 - n) / 12 - sum(t**3 - t for t in ties) / 12
    var = (np_ * nm / (n * (n - 1))) * bracket
    return 0.0 if var <= 0 else float(np.clip((u - mu) / np.sqrt(var), -8, 8))


def ibd_score(observations, probe_meta, score_step=EVENT_T + OFFSET):
    # Choice: o(t_p) is the pre-action observation for step t_p, so h=1 is
    # the first action effect when tau=0, consistent with contract C1/C4.
    newest_anchor = max(s for s in range(20, score_step + 1, 20) if s + max(HSET) <= score_step)
    anchors = [s for s in range(20, newest_anchor + 1, 20) if s > newest_anchor - W]
    units = []
    for s in anchors:
        meta = probe_meta[s - 1]
        assert meta is not None and meta[0] == s
        _, k, sign = meta
        base_index = s - 1
        increments = np.stack([observations[base_index + h] - observations[base_index] for h in HSET])
        units.append((k, sign, increments))
    c = observations.shape[1]
    scores = np.zeros(c)
    for ch in range(c):
        zs = []
        for k in range(K):
            for hi in range(len(HSET)):
                plus = [u[2][hi, ch] for u in units if u[0] == k and u[1] > 0]
                minus = [u[2][hi, ch] for u in units if u[0] == k and u[1] < 0]
                if min(len(plus), len(minus)) < NMIN:
                    continue
                zs.append(abs(ranksum_z(plus, minus)))
        scores[ch] = max(zs, default=0.0)
    return scores


def fit_comparator(inst: Instance, confounder: bool):
    xs = []; ys = []
    for ep in range(20):
        o, a, _ = simulate(inst, 10_000 + ep, confounder, probes=False, event=False)
        xs.append(np.c_[o[:-1], a, np.ones(T)]); ys.append(o[1:])
    X = np.vstack(xs); Y = np.vstack(ys)
    xtx = X.T @ X
    lam = 1e-4 * np.trace(xtx) / (inst.c + K)
    D = np.eye(X.shape[1]); D[-1, -1] = 0
    A = xtx + lam * D
    L = np.linalg.cholesky(A)
    beta = np.linalg.solve(L.T, np.linalg.solve(L, X.T @ Y))
    R = Y - X @ beta
    mu = R.mean(axis=0)
    raw_sd = R.std(axis=0, ddof=1)
    sd = np.maximum(raw_sd, 1e-6)
    degen = raw_sd < 1e-3
    loading = np.linalg.norm(beta[inst.c : inst.c + K], axis=0) / sd
    return beta, mu, sd, degen, loading


def comparator_score(observations, actions, fitted, score_step=EVENT_T + OFFSET):
    beta, mu, sd, degen, loading = fitted
    X = np.c_[observations[:-1], actions, np.ones(T)]
    rt = np.clip((observations[1:] - X @ beta - mu) / sd, -8, 8)
    window = rt[score_step - W : score_step]
    shift = np.abs(np.sqrt(len(window)) * window.mean(axis=0))
    q = np.clip(loading - shift, -40, 40)
    q[degen] = -40
    return q


def auc(y, score):
    y = np.asarray(y, bool); score = np.asarray(score, float)
    pos = score[y]; neg = score[~y]
    if not len(pos) or not len(neg):
        return float("nan")
    return float(((pos[:, None] > neg).sum() + 0.5 * (pos[:, None] == neg).sum()) / (len(pos) * len(neg)))


def run_cell(nx, tau, confounder, seeds):
    inst = make_instance(nx, tau)
    fitted = fit_comparator(inst, confounder)
    y = support_labels(inst)
    rows = []
    for seed in seeds:
        oi, _, pm = simulate(inst, seed, confounder, probes=True, event=True)
        oc, ac, _ = simulate(inst, seed, confounder, probes=False, event=True)
        ai = auc(y, ibd_score(oi, pm))
        aq = auc(y, comparator_score(oc, ac, fitted))
        rows.append({"nx": nx, "tau": tau, "confounder": "present" if confounder else "absent",
                     "seed": seed, "auc_ibd": ai, "auc_comparator": aq, "delta_auc": ai - aq,
                     "positives": int(y.sum()), "channels": inst.c})
    return rows


def summarise(rows):
    out = []
    keys = sorted({(r["nx"], r["tau"], r["confounder"]) for r in rows})
    for nx, tau, conf in keys:
        rr = [r for r in rows if (r["nx"], r["tau"], r["confounder"]) == (nx, tau, conf)]
        def ms(k):
            a = np.array([x[k] for x in rr]); return float(a.mean()), float(a.std(ddof=1) / np.sqrt(len(a)))
        mi, sei = ms("auc_ibd"); mc, sec = ms("auc_comparator"); md, sed = ms("delta_auc")
        out.append({"nx": nx, "tau": tau, "confounder": conf, "n": len(rr),
                    "auc_ibd_mean": mi, "auc_ibd_se": sei,
                    "auc_comparator_mean": mc, "auc_comparator_se": sec,
                    "delta_mean": md, "delta_se": sed})
    benefits = []
    for nx, tau in sorted({(r["nx"], r["tau"]) for r in rows}):
        rp = {r["seed"]: r for r in rows if r["nx"] == nx and r["tau"] == tau and r["confounder"] == "present"}
        ra = {r["seed"]: r for r in rows if r["nx"] == nx and r["tau"] == tau and r["confounder"] == "absent"}
        b = np.array([rp[s]["delta_auc"] - ra[s]["delta_auc"] for s in sorted(rp.keys() & ra.keys())])
        benefits.append({"nx": nx, "tau": tau, "n": len(b), "confounding_benefit_mean": float(b.mean()),
                         "confounding_benefit_se": float(b.std(ddof=1) / np.sqrt(len(b)))})
    return out, benefits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("independent_end_to_end_results"))
    args = ap.parse_args()
    seeds = list(range(100, 100 + args.seeds))
    rows = []
    for nx in (10, 30):
        for conf in (False, True):
            rows += run_cell(nx, 0, conf, seeds)
    # Required untested-region attack: tau=2 at N_x=30, both confounder states.
    for conf in (False, True):
        rows += run_cell(30, 2, conf, seeds)
    summary, benefits = summarise(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.with_suffix(".csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    payload = {"simulation": "independent family-L contract-B instance", "seeds": args.seeds,
               "cells": summary, "confounding_benefit": benefits,
               "choices": [
                   "R0 only; the mandatory prompt did not request an R1 transform.",
                   "A fixed admissible instance is shared across seeds; predictor fits are per nx/tau/confounder cell.",
                   "IBD o(t_p) means the pre-action observation at probe step t_p, matching contract C1/C4.",
                   "AUC is computed across all observation channels per episode with mid-ties and noise-only padding retained.",
                   "The passive comparator receives a non-probed stream; IBD receives its own probes; exogenous noise is keyed identically.",
                   "The comparator predictor uses 20 fault-free non-probed episodes and the specified float64 Cholesky ridge solve.",
                   "Raw statistics only: no isotonic fit, alarm threshold, or operating point is needed for the primary.",
                   "Score at offset 500 uses IBD's last closed epoch (newest anchor 1480) and comparator residual steps 1001..1500.",
               ]}
    args.out.with_suffix(".json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
