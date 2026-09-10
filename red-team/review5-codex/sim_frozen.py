#!/usr/bin/env python3
"""Independent round-5 reproduction from the two frozen method specifications.

The only instance implementation imported is gate/reference_generator.py.  Run:
    python sim_frozen.py | tee sim_frozen-output.txt
The script re-execs with PYTHONHASHSEED=0 because the frozen generator keys noise
with Python's process-randomised hash(); this makes this review's output replayable.
"""
from __future__ import annotations

import copy
import math
import os
import pathlib
import sys
import time
from dataclasses import dataclass

if os.environ.get("PYTHONHASHSEED") != "0":
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    os.execve(sys.executable, [sys.executable, *sys.argv], env)

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
GATE = HERE.parent / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))
from reference_generator import draw_certified  # noqa: E402

T = 2000
EVENT_T = 1000
OFFSETS = (200, 500, 1000)
FIT_EPISODES = tuple(range(100, 120))
SCORE_EPISODES = tuple(range(4))
HORIZONS = (1, 2, 3)
W = 500
N_MIN_SIGN = 3
T975_DF9 = 2.2621571628540993
T975_DF8 = 2.306004135204166


def auc(scores: np.ndarray, labels: np.ndarray) -> float:
    scores = np.asarray(scores, float)
    labels = np.asarray(labels, bool)
    pos, neg = scores[labels], scores[~labels]
    if not len(pos) or not len(neg):
        return float("nan")
    return float(((pos[:, None] > neg).sum() + 0.5 * (pos[:, None] == neg).sum()) / (len(pos) * len(neg)))


def stable_probe_rng(logical_seed: int, ep: int, nx: int, tau: int, coupling: float, noise: float):
    return np.random.default_rng(np.random.SeedSequence([
        0x51BD, logical_seed, ep, nx, tau, int(round(1000 * coupling)), int(round(1000 * noise))
    ]))


def balanced_probes(inst, logical_seed: int, ep: int, coupling: float, noise: float):
    """Direct generator-clock reading: action indices 20,...,1980.

    This follows the spec's O[t_p+h]-O[t_p] clock.  The spec's stated terminal
    grant t_p=2000 cannot be represented in Instance.run(T=2000); see findings.
    """
    rng = stable_probe_rng(logical_seed, ep, inst.cfg["N_x"], inst.tau, coupling, noise)
    pairs = [(k, s) for k in range(inst.cfg["K"]) for s in (+1, -1)]
    allocation, actions = {}, {}
    block = []
    for tp in range(20, T, 20):
        if not block:
            block = [pairs[i] for i in rng.permutation(len(pairs))]
        k, sign = block.pop()
        a = np.zeros(inst.cfg["K"])
        a[k] = sign
        allocation[tp] = (k, sign)
        actions[tp] = a
    return allocation, actions


def round_sig_array(x: np.ndarray, digits: int = 12) -> np.ndarray:
    x = np.asarray(x, float)
    out = x.copy()
    nz = np.isfinite(x) & (x != 0)
    places = digits - 1 - np.floor(np.log10(np.abs(x[nz]))).astype(int)
    out[nz] = np.array([round(v, int(p)) for v, p in zip(x[nz], places)])
    return out


def ranksum_z(plus: np.ndarray, minus: np.ndarray):
    vals = round_sig_array(np.concatenate([plus, minus]))
    n_plus, n_minus, n = len(plus), len(minus), len(vals)
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(n, float)
    tie_term = 0.0
    i = 0
    while i < n:
        j = i + 1
        while j < n and vals[order[j]] == vals[order[i]]:
            j += 1
        ranks[order[i:j]] = 0.5 * ((i + 1) + j)
        size = j - i
        tie_term += size ** 3 - size
        i = j
    r_plus = ranks[:n_plus].sum()
    u = r_plus - n_plus * (n_plus + 1) / 2
    mu_u = n_plus * n_minus / 2
    var = (n_plus * n_minus / (n * (n - 1))) * ((n ** 3 - n) / 12 - tie_term / 12)
    if var <= 0:
        return None
    return float(np.clip((u - mu_u) / math.sqrt(max(0.0, var)), -8, 8))


def ibd_scores(obs: np.ndarray, allocation: dict[int, tuple[int, int]], c: int):
    result = {}
    anchors = np.array(sorted(allocation))
    for offset in OFFSETS:
        read_t = EVENT_T + offset
        closed = anchors[anchors + max(HORIZONS) - 1 <= read_t]
        newest = int(closed[-1])
        window = [int(tp) for tp in closed if newest - W < tp <= newest]
        out = np.zeros(c)
        for ch in range(c):
            zvals = []
            for k in range(2):
                plus_t = [tp for tp in window if allocation[tp] == (k, +1)]
                minus_t = [tp for tp in window if allocation[tp] == (k, -1)]
                if min(len(plus_t), len(minus_t)) < N_MIN_SIGN:
                    continue
                for h in HORIZONS:
                    zp = obs[np.array(plus_t) + h, ch] - obs[plus_t, ch]
                    zm = obs[np.array(minus_t) + h, ch] - obs[minus_t, ch]
                    z = ranksum_z(zp, zm)
                    if z is not None:
                        zvals.append(abs(z))
            out[ch] = max(zvals, default=0.0)
        result[offset] = out
    return result


@dataclass
class Predictor:
    beta: np.ndarray
    intercept: np.ndarray
    mu: np.ndarray
    sd: np.ndarray
    loading: np.ndarray
    degenerate: np.ndarray


def features(obs: np.ndarray, actions: np.ndarray):
    n, k = actions.shape
    lag1 = np.vstack([np.zeros((1, k)), actions[:-1]])
    lag2 = np.vstack([np.zeros((2, k)), actions[:-2]])
    return np.hstack([obs[:-1], actions, lag1, lag2])


def fit_predictor(inst) -> Predictor:
    xs, ys = [], []
    for ep in FIT_EPISODES:
        r = copy.deepcopy(inst).run(T, ep=ep)
        xs.append(features(r["o"], r["a"]))
        ys.append(r["o"][1:])
    phi, y = np.vstack(xs), np.vstack(ys)
    mean = phi.mean(axis=0)
    scale = np.maximum(phi.std(axis=0, ddof=0), 1e-8)
    xt = np.hstack([(phi - mean) / scale, np.ones((len(phi), 1))])
    gram = xt.T @ xt
    penalty = np.eye(xt.shape[1])
    penalty[-1, -1] = 0
    chol = np.linalg.cholesky(gram + (1e-4 * len(phi)) * penalty)
    rhs = xt.T @ y
    beta_tilde = np.linalg.solve(chol.T, np.linalg.solve(chol, rhs))
    beta = beta_tilde[:-1] / scale[:, None]
    intercept = beta_tilde[-1] - (mean / scale) @ beta_tilde[:-1]
    residual = y - xt @ beta_tilde
    mu = residual.mean(axis=0)
    sd = np.maximum(residual.std(axis=0, ddof=1), 1e-6)
    c, k = inst.C, inst.cfg["K"]
    beta_o = beta[:c]
    beta_a = [beta[c + j * k:c + (j + 1) * k] for j in range(3)]
    jac = np.zeros((k, c))
    loading = np.zeros(c)
    for h in HORIZONS:
        jac = jac @ beta_o + beta_a[h - 1]
        loading = np.maximum(loading, np.linalg.norm(jac, axis=0) / sd)
    degenerate = (sd < 1e-2 * np.median(sd)) & (loading < 1e-3)
    return Predictor(beta, intercept, mu, sd, loading, degenerate)


def comparator_scores(pred: Predictor, rollout: dict):
    phi = features(rollout["o"], rollout["a"])
    residual = rollout["o"][1:] - (phi @ pred.beta + pred.intercept)
    rt = np.clip((residual - pred.mu) / pred.sd, -8, 8)
    csum = np.vstack([np.zeros((1, rt.shape[1])), np.cumsum(rt, axis=0)])
    out = {}
    for offset in OFFSETS:
        # There is no transition with tr.t == 2000 in a 2,000-transition run;
        # the offset-1000 read therefore uses the last emitted score (t=1999).
        t = min(T - 1, EVENT_T + offset)
        lo = max(0, t - W + 1)
        n = t - lo + 1
        mean = (csum[t + 1] - csum[lo]) / n
        q = np.clip(pred.loading - np.abs(math.sqrt(n) * mean), -40, 40)
        q[pred.degenerate] = -41
        out[offset] = q
    return out


def one_condition(inst0, logical_seed: int, present: bool, coupling: float, noise: float):
    train = copy.deepcopy(inst0)
    if not present:
        train.G[:] = 0
    pred = fit_predictor(train)
    episode_rows = []
    for ep in SCORE_EPISODES:
        # Passive arm.
        passive_inst = copy.deepcopy(train)
        passive = passive_inst.run(T, ep=ep, event_t=EVENT_T, event=("actuator_loss", 0))
        labels = passive_inst.S_obs()
        q = comparator_scores(pred, passive)
        # Interventional arm, on its own matched probe stream.
        ibd_inst = copy.deepcopy(train)
        allocation, actions = balanced_probes(ibd_inst, logical_seed, ep, coupling, noise)
        probed = ibd_inst.run(T, ep=ep, actions=actions, event_t=EVENT_T, event=("actuator_loss", 0))
        assert np.array_equal(labels, ibd_inst.S_obs())
        a = ibd_scores(probed["o"], allocation, ibd_inst.C)
        episode_rows.append({off: (auc(a[off], labels), auc(q[off], labels)) for off in OFFSETS})
    return episode_rows, pred, labels


def ci_cluster(values: np.ndarray, crit: float):
    values = np.asarray(values, float)
    mean = float(values.mean())
    half = crit * float(values.std(ddof=1)) / math.sqrt(len(values))
    return mean, mean - half, mean + half


def run_cell(group: str, nx: int, tau: int, coupling: float, noise: float, seeds: list[int]):
    rows = []
    for seed in seeds:
        cfg = dict(N_x=nx, tau=tau, coupling=coupling, noise_mult=noise)
        inst = draw_certified(cfg, seed)
        support_before = inst.S_obs().copy()
        lost = copy.deepcopy(inst)
        lost.apply_event(("actuator_loss", 0))
        support_after = lost.S_obs().copy()
        cond = {}
        for present in (True, False):
            eps, pred, labels = one_condition(inst, seed, present, coupling, noise)
            cond[present] = eps
            assert np.array_equal(labels, support_after)
        rows.append(dict(group=group, nx=nx, tau=tau, coupling=coupling, noise=noise,
                         seed=seed, present=cond[True], absent=cond[False],
                         support_changed=bool(np.any(support_before != support_after))))
    return rows


def summarize(rows, have_ci=True):
    result = []
    crit = T975_DF9 if len(rows) == 10 else T975_DF8
    for off in OFFSETS:
        per_inst = []
        for row in rows:
            vals = {}
            for key in ("present", "absent"):
                vals[key] = np.mean([ep[off] for ep in row[key]], axis=0)
            per_inst.append([*vals["present"], *vals["absent"],
                             (vals["present"][0] - vals["present"][1]) -
                             (vals["absent"][0] - vals["absent"][1])])
        x = np.asarray(per_inst)
        means = x.mean(axis=0)
        if have_ci and len(rows) > 1:
            _, lo, hi = ci_cluster(x[:, 4], crit)
            _, cmp_lo, _ = ci_cluster(x[:, 3], crit)
        else:
            lo = hi = cmp_lo = float("nan")
        result.append((off, *means, lo, hi, cmp_lo))
    return result


def f(x):
    return "NA" if not np.isfinite(x) else f"{x:.3f}"


def print_table(rows):
    print("| offset | IBD present | comparator present | IBD absent | comparator absent | confounding benefit | 95% cluster CI | comparator-absent 95% lower |")
    print("|---:|---:|---:|---:|---:|---:|:---:|---:|")
    for off, ip, cp, ia, ca, benefit, lo, hi, cmp_lo in rows:
        print(f"| {off} | {f(ip)} | {f(cp)} | {f(ia)} | {f(ca)} | {f(benefit)} | [{f(lo)}, {f(hi)}] | {f(cmp_lo)} |")


def main():
    started = time.time()
    print("# Frozen-generator reproduction (review5-codex)")
    print(f"python={sys.version.split()[0]} numpy={np.__version__} PYTHONHASHSEED={os.environ['PYTHONHASHSEED']}")
    print("instances=10 x episodes=4 for each base cell; no seed reduction")
    print("perturbations=full 3x3 coupling/noise Cartesian product at Nx=10,tau=0,logical seed=0")
    print("choices: predictor fitted separately per instance and confounder condition on episode ids 100..119; scored ids 0..3")
    print("choices: probe RNG is a domain-separated SeedSequence keyed by logical config seed, episode, Nx, tau, coupling, noise")
    print("choices: generator clock used literally (probe action indices 20..1980); impossible terminal t=2000 grant omitted")
    print("choices: passive offset 1000 uses last emitted transition score t=1999; IBD uses last closed epoch <= t=2000")
    print("choices: full post-event S_obs labels; mid-rank AUC; episodes averaged within instance; two-sided t(9) cluster intervals")
    print("choices: no isotonic/operating-point/alarm fit because the requested primary uses raw statistics only")
    all_base = []
    for nx in (10, 30):
        for tau in (0, 2):
            print(f"running base Nx={nx} tau={tau}...", flush=True)
            cell = run_cell("base", nx, tau, 1.0, 1.0, list(range(10)))
            all_base.extend(cell)
            print(f"\n## Base cell Nx={nx}, tau={tau}; support-change certified empirically {sum(r['support_changed'] for r in cell)}/{len(cell)}")
            print_table(summarize(cell))

    perturb = []
    for coupling in (0.5, 1.0, 2.0):
        for noise in (0.5, 1.0, 2.0):
            print(f"running perturb coupling={coupling} noise={noise}...", flush=True)
            cell = run_cell("perturb", 10, 0, coupling, noise, [0])
            perturb.extend(cell)
            print(f"\n## Perturbation coupling={coupling}, noise={noise}, Nx=10, tau=0, seed=0")
            print_table(summarize(cell, have_ci=False))

    print("\n## Perturbation-set aggregate (nine configurations treated as instance clusters)")
    print_table(summarize(perturb, have_ci=True))
    print("\n## Verdict checks at primary offset 500")
    for nx in (10, 30):
        for tau in (0, 2):
            cell = [r for r in all_base if r["nx"] == nx and r["tau"] == tau]
            primary = {r[0]: r for r in summarize(cell)}[500]
            benefit, lo, hi, cmp_lo = primary[5], primary[6], primary[7], primary[8]
            print(f"Nx={nx} tau={tau}: benefit={benefit:.3f} CI=[{lo:.3f},{hi:.3f}] "
                  f"margin={'PASS' if lo > 0.10 else 'NO'}; comparator absent lower={cmp_lo:.3f} "
                  f"competence={'PASS' if cmp_lo >= 0.85 else 'FAIL'}")
    print(f"elapsed_seconds={time.time()-started:.1f}")


if __name__ == "__main__":
    main()
