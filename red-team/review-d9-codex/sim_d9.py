"""Independent D-9.1 reproduction for the 7 September 2026 red-team review.

Only numpy is required.  The simulator is derived from the author's earlier
review3-codex infrastructure; it does not import any review3-claude-opus code.

Design: contract-B family-L, tau=0, 5% block-periodic +/-e_k replacement
probes, trailing 500-step statistics, 40 calibration episodes per cell (half
event-carrying), 30 scored event episodes and 30 matched no-event controls.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import time
from dataclasses import dataclass

import numpy as np

T = 2000
EVENT_T = 1000
OFFSETS = (200, 500, 1000)
HSET = (1, 2, 3)
K = 2
NX_VALUES = (10, 30)
W_STEPS = 500
PI = 20
M_NULL = 4
SP_NULL = 3
N_MIN = 10
Z_CAP = 8.0
EPS = 0.05
R_CAL = 40
N_SCORE = 30
SIG_B = SIG_D = SIG_W = SIG_X = 0.1
SIG_O = 0.05
SIG_A = 0.1
SIG_U = 1.0
RHO_U = 0.8
F_CONF = 0.5


def average_ranks(v: np.ndarray) -> np.ndarray:
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(len(v), float)
    i = 0
    while i < len(v):
        j = i + 1
        while j < len(v) and v[order[j]] == v[order[i]]:
            j += 1
        ranks[order[i:j]] = 0.5 * (i + 1 + j)
        i = j
    return ranks


def mw_z(x: np.ndarray, y: np.ndarray) -> float:
    """Tie-corrected Mann-Whitney rank-sum z; positive means x > y."""
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return 0.0
    v = np.concatenate((x, y))
    ranks = average_ranks(v)
    u = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    _, counts = np.unique(v, return_counts=True)
    n = n1 + n2
    tie = 1.0 - np.sum(counts**3 - counts) / (n**3 - n) if n > 1 else 0.0
    var = n1 * n2 * (n + 1) * tie / 12.0
    if var <= 0:
        return 0.0
    return float(np.clip((u - n1 * n2 / 2) / math.sqrt(var), -Z_CAP, Z_CAP))


def pava_fit(x: np.ndarray, y: np.ndarray):
    """Non-decreasing isotonic regression with exact-tie aggregation."""
    order = np.argsort(x, kind="mergesort")
    xs, ys = np.asarray(x)[order], np.asarray(y, float)[order]
    ux, inv = np.unique(xs, return_inverse=True)
    weights = np.bincount(inv).astype(float)
    means = np.bincount(inv, weights=ys) / weights
    blocks = []
    for i, (mean, weight) in enumerate(zip(means, weights)):
        blocks.append([i, i, weight, mean])
        while len(blocks) > 1 and blocks[-2][3] > blocks[-1][3]:
            b, a = blocks.pop(), blocks.pop()
            wt = a[2] + b[2]
            blocks.append([a[0], b[1], wt, (a[2] * a[3] + b[2] * b[3]) / wt])
    fitted = np.empty(len(ux))
    for lo, hi, _, mean in blocks:
        fitted[lo:hi + 1] = mean
    return ux, fitted


def pava_apply(model, x: np.ndarray) -> np.ndarray:
    knots, vals = model
    idx = np.searchsorted(knots, x, side="right") - 1
    return np.clip(vals[np.clip(idx, 0, len(vals) - 1)], 0.0, 1.0)


def auc_score(scores: np.ndarray, labels: np.ndarray) -> float:
    y = np.asarray(labels, bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    if not n1 or not n0:
        return float("nan")
    r = average_ranks(np.asarray(scores, float))
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def average_precision(scores: np.ndarray, labels: np.ndarray) -> float:
    """Non-interpolated AP: mean precision at each positive in descending rank."""
    y = np.asarray(labels, bool)
    if not y.any():
        return float("nan")
    order = np.argsort(-np.asarray(scores), kind="mergesort")
    yy = y[order]
    return float(np.sum(np.cumsum(yy)[yy] / (np.flatnonzero(yy) + 1)) / yy.sum())


def f1_score(pred: np.ndarray, labels: np.ndarray) -> float:
    pred, labels = np.asarray(pred, bool), np.asarray(labels, bool)
    tp = int(np.sum(pred & labels)); fp = int(np.sum(pred & ~labels)); fn = int(np.sum(~pred & labels))
    return float(2 * tp / (2 * tp + fp + fn)) if 2 * tp + fp + fn else 0.0


def best_f1_threshold(prob: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    """Choose one arm/cell threshold by micro-F1 on calibration observations."""
    p, y = np.asarray(prob, float), np.asarray(labels, bool)
    candidates = np.unique(np.r_[0.0, p, 1.0 + 1e-12])
    best = (-1.0, 0.5)
    for threshold in candidates:
        value = f1_score(p >= threshold, y)
        if value > best[0] + 1e-15 or (abs(value - best[0]) < 1e-15 and threshold > best[1]):
            best = (value, float(threshold))
    return best[1], best[0]


@dataclass
class Instance:
    nx: int
    confounded: bool
    wu_scale: float = 1.0

    def __post_init__(self):
        # Independently chosen from the Claude instance; inherited from review3-codex.
        self.Ab = np.array([[.62, 0, 0, 0], [0, .62, 0, 0], [.24, 0, .55, 0], [0, .24, 0, .55]])
        self.B0 = np.array([[.35, 0], [0, .35], [0, 0], [0, 0]])
        self.Ad = np.diag([.55, .55])
        self.Cd = np.array([[.25, 0, 0, 0], [0, .25, 0, 0]])
        self.Aw = np.eye(4) * .70
        self.Ax = np.eye(self.nx) * .80
        self.G = np.zeros((self.nx, 1))
        if self.confounded:
            self.G[: self.nx // 2, 0] = np.linspace(.35, .55, self.nx // 2)
        self.nz = 4 + 2 + 4 + self.nx
        self.C = self.nz + 4
        self.Wo = np.zeros((2, self.C)); self.Wo[0, 0] = -.18; self.Wo[1, 1] = -.18
        self.Wu = self.wu_scale * np.array([[.45], [-.40]])
        self.direct = np.array([0, 1])
        self.indirect = np.array([2, 3, 4, 5])
        self.nonreachable = np.arange(6, self.C)
        self.conf_mask = np.zeros(self.C, bool)
        self.conf_mask[10:10 + self.nx // 2] = self.confounded
        self.support_pre = self.support(self.B0)
        post = self.B0.copy(); post[:, 0] = 0.0
        self.support_post = self.support(post)

    def transition_matrix(self) -> np.ndarray:
        F = np.zeros((self.nz, self.nz))
        F[:4, :4] = self.Ab
        F[4:6, :4] = self.Cd; F[4:6, 4:6] = self.Ad
        F[6:10, 6:10] = self.Aw
        F[10:, 10:] = self.Ax
        return F

    def effects(self, B: np.ndarray) -> np.ndarray:
        F = self.transition_matrix()
        inj = np.zeros((self.nz, K)); inj[:4] = B
        effect = np.zeros(self.nz); power = np.eye(self.nz)
        for _h in HSET:
            response = power @ inj
            effect = np.maximum(effect, np.max(np.abs(response), axis=1))
            power = F @ power
        return effect

    def support(self, B: np.ndarray) -> np.ndarray:
        out = np.zeros(self.C, bool)
        out[:self.nz] = self.effects(B) > EPS
        return out

    def certifications(self, sample_ep: dict) -> dict:
        post = self.B0.copy(); post[:, 0] = 0.0
        Acl = self.Ab + self.B0 @ self.Wo[:, :4]
        a = sample_ep["action"][:EVENT_T]
        x = sample_ep["obs"][:EVENT_T, 10:10 + self.nx]
        corr = 0.0
        for k in range(K):
            for j in range(self.nx):
                if a[:, k].std() > 0 and x[:, j].std() > 0:
                    corr = max(corr, abs(float(np.corrcoef(a[:, k], x[:, j])[0, 1])))
        return {
            "rho_Ab": float(max(abs(np.linalg.eigvals(self.Ab)))),
            "rho_Ad": float(max(abs(np.linalg.eigvals(self.Ad)))),
            "rho_Aw": float(max(abs(np.linalg.eigvals(self.Aw)))),
            "rho_Ax": float(max(abs(np.linalg.eigvals(self.Ax)))),
            "rho_closed_loop": float(max(abs(np.linalg.eigvals(Acl)))),
            "max_abs_corr_a_x": corr,
            "rho_min_witness_met": bool(corr >= .4) if self.confounded and self.wu_scale else None,
            "saturation_fraction": float(sample_ep["saturation_fraction"]),
            "support_size_pre": int(self.support_pre.sum()),
            "support_size_post": int(self.support_post.sum()),
            "min_nonzero_effect_pre": float(np.min(self.effects(self.B0)[self.effects(self.B0) > EPS])),
            "min_nonzero_effect_post": float(np.min(self.effects(post)[self.effects(post) > EPS])),
        }


def noise_bank(seed: int, inst: Instance):
    rng = np.random.default_rng(seed)
    return {
        "u": SIG_U * rng.normal(size=(T + 1, 1)), "b": SIG_B * rng.normal(size=(T + 1, 4)),
        "d": SIG_D * rng.normal(size=(T + 1, 2)), "w": SIG_W * rng.normal(size=(T + 1, 4)),
        "x": SIG_X * rng.normal(size=(T + 1, inst.nx)), "a": SIG_A * rng.normal(size=(T + 1, K)),
        "o": SIG_O * rng.normal(size=(T + 1, inst.C)), "pdir": rng.integers(0, 2 * K, size=T + 1),
    }


def simulate(inst: Instance, seed: int, event: bool, probed: bool) -> dict:
    n = noise_bank(seed, inst)
    b = np.zeros((T + 1, 4)); d = np.zeros((T + 1, 2)); w = np.zeros((T + 1, 4))
    x = np.zeros((T + 1, inst.nx)); u = np.zeros((T + 1, 1)); o = np.zeros((T + 1, inst.C))
    action = np.zeros((T, K)); probe = np.zeros(T, bool); pdir = np.full(T, -1, int)
    saturated = 0
    for t in range(T):
        u[t] = RHO_U * (u[t - 1] if t else 0) + n["u"][t]
        latent = np.concatenate((b[t], d[t], w[t], x[t], np.zeros(4)))
        o[t] = latent + n["o"][t]
        raw = inst.Wo @ o[t] + inst.Wu @ u[t] + n["a"][t]
        saturated += int(np.any(np.abs(raw) > 2.0))
        act = np.clip(raw, -2.0, 2.0)
        if probed and t > 0 and t % PI == 0 and t <= T - max(HSET) - 1:
            direction = int(n["pdir"][t]); k = direction // 2; sign = 1.0 if direction % 2 == 0 else -1.0
            act = np.zeros(K); act[k] = sign; probe[t] = True; pdir[t] = direction
        action[t] = act
        B = inst.B0.copy()
        if event and t >= EVENT_T:
            B[:, 0] = 0.0
        b[t + 1] = inst.Ab @ b[t] + B @ act + n["b"][t]
        d[t + 1] = inst.Ad @ d[t] + inst.Cd @ b[t] + n["d"][t]
        w[t + 1] = inst.Aw @ w[t] + n["w"][t]
        x[t + 1] = inst.Ax @ x[t] + inst.G @ u[t] + n["x"][t]
    o[T] = np.concatenate((b[T], d[T], w[T], x[T], np.zeros(4))) + n["o"][T]
    return {"obs": o, "action": action, "probe": probe, "pdir": pdir,
            "saturation_fraction": saturated / T, "probe_steps": int(probe.sum())}


def statistic_traces(ep: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return common epoch times, draft-2 A, and sign-randomised B."""
    o, probe, pdir = ep["obs"], ep["probe"], ep["pdir"]
    anchors = np.flatnonzero(probe)
    times, out_a, out_b = [], [], []
    for anchor in anchors:
        close = anchor + max(HSET)
        if close > T:
            continue
        keep = anchors[(anchors > close - W_STEPS) & (anchors <= anchor)]
        keep = keep[keep >= M_NULL * SP_NULL]
        if len(keep) < N_MIN:
            continue
        za = np.zeros((len(HSET), o.shape[1]))
        for hi, h in enumerate(HSET):
            pv = np.abs(o[keep + h] - o[keep])
            nv = np.concatenate([np.abs(o[keep - m * SP_NULL + h] - o[keep - m * SP_NULL])
                                 for m in range(1, M_NULL + 1)], axis=0)
            for c in range(o.shape[1]):
                za[hi, c] = mw_z(pv[:, c], nv[:, c])
        pick = np.argmax(np.abs(za), axis=0)
        draft = za[pick, np.arange(o.shape[1])]

        signrand = np.zeros(o.shape[1])
        dirs = pdir[keep]
        for k in range(K):
            pos, neg = keep[dirs == 2 * k], keep[dirs == 2 * k + 1]
            # With 25 probes/window, 3/group is the smallest usable cell and matches R3-1's executable proposal.
            if len(pos) < 3 or len(neg) < 3:
                continue
            for h in HSET:
                dp, dn = o[pos + h] - o[pos], o[neg + h] - o[neg]
                for c in range(o.shape[1]):
                    signrand[c] = max(signrand[c], abs(mw_z(dp[:, c], dn[:, c])))
        times.append(close); out_a.append(draft); out_b.append(signrand)
    return np.asarray(times, int), np.asarray(out_a), np.asarray(out_b)


class LinearPredictor:
    """One shared multivariate linear predictor; no channel-specific model class."""
    def fit(self, episodes: list[dict]):
        X, Y = [], []
        for ep in episodes:
            X.append(np.column_stack((ep["obs"][:-1], ep["action"], np.ones(T))))
            Y.append(ep["obs"][1:])
        X, Y = np.concatenate(X), np.concatenate(Y)
        self.coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
        residual = Y - X @ self.coef
        self.mu = residual.mean(axis=0)
        self.sd = np.maximum(residual.std(axis=0, ddof=1), 1e-6)
        self.action_loading = np.linalg.norm(self.coef[-K - 1:-1], axis=0) / self.sd
        zmax = np.max(np.abs((residual - self.mu) / self.sd), axis=1)
        self.cusum_k = float(zmax.mean() + 0.5 * zmax.std(ddof=1))

    def standardized_innovations(self, ep: dict) -> np.ndarray:
        X = np.column_stack((ep["obs"][:-1], ep["action"], np.ones(T)))
        return (ep["obs"][1:] - X @ self.coef - self.mu) / self.sd

    def support_trace(self, ep: dict, times: np.ndarray) -> np.ndarray:
        """q_c(t)=||beta_a,c||/sigma_c-|sqrt(n)*mean(z_c)| over trailing W.

        This is a two-sided standardized innovation-mean shift, oriented so
        larger q means retained support, with the pre-fault standardized action
        loading supplying the support baseline.
        """
        z = self.standardized_innovations(ep)
        cs = np.vstack((np.zeros(z.shape[1]), np.cumsum(z, axis=0)))
        out = []
        for t in times:
            lo = max(0, int(t) - W_STEPS); n = int(t) - lo
            mean = (cs[int(t)] - cs[lo]) / n
            out.append(self.action_loading - np.abs(math.sqrt(n) * mean))
        return np.asarray(out)

    def cusum_alarm_times(self, ep: dict, threshold: float) -> list[int]:
        z = self.standardized_innovations(ep)
        S = 0.0; raw = np.zeros(T + 1, bool)
        for t, value in enumerate(np.max(np.abs(z), axis=1), start=1):
            S = max(0.0, S + value - self.cusum_k)
            raw[t] = S > threshold
        alarms, run, blocked = [], 0, -1
        for t, raised in enumerate(raw):
            if t <= blocked:
                run = 0; continue
            run = run + 1 if raised else 0
            if run >= 3:
                alarms.append(t); run = 0; blocked = t + 20
        return alarms


def value_at(times: np.ndarray, trace: np.ndarray, t: int) -> np.ndarray:
    idx = np.searchsorted(times, t, side="right") - 1
    return trace[max(0, idx)]


def calibrate_alarm_threshold(model: LinearPredictor, episodes: list[dict]) -> tuple[float, float]:
    grid = np.linspace(0.5, 80.0, 240)
    best = (float("inf"), 0.5, 0.0)
    for h in grid:
        run_lengths = []
        for ep in episodes:
            alarms = model.cusum_alarm_times(ep, float(h))
            run_lengths.append(alarms[0] if alarms else T)
        mean = float(np.mean(run_lengths))
        candidate = (abs(mean - 1000.0), float(h), mean)
        if candidate < best:
            best = candidate
    return best[1], best[2]


def labels_at(inst: Instance, t: int, event: bool) -> np.ndarray:
    return inst.support_post if event and t > EVENT_T else inst.support_pre


def build_calibration(inst: Instance):
    probed, passive, traces = [], [], []
    for i in range(R_CAL):
        event = i < R_CAL // 2
        pe = simulate(inst, 10_000 + i, event, True)
        ne = simulate(inst, 10_000 + i, event, False)
        probed.append((pe, event)); passive.append((ne, event))
        traces.append((*statistic_traces(pe), event))
    predictor = LinearPredictor()
    predictor.fit([ep for ep, event in passive if not event])
    raw = {name: [] for name in ("draft2", "signrand", "comparator", "comparator_probed")}
    lab = []
    for (times, a, b, event), (pep, _), (nep, _) in zip(traces, probed, passive):
        comp = predictor.support_trace(nep, times)
        comp_p = predictor.support_trace(pep, times)
        raw["draft2"].append(a); raw["signrand"].append(b)
        raw["comparator"].append(comp); raw["comparator_probed"].append(comp_p)
        lab.append(np.vstack([labels_at(inst, int(t), event) for t in times]))
    y = np.concatenate(lab).ravel().astype(float)
    models, thresholds, cal_f1 = {}, {}, {}
    for name, chunks in raw.items():
        x = np.concatenate(chunks).ravel()
        models[name] = pava_fit(x, y)
        prob = pava_apply(models[name], x)
        thresholds[name], cal_f1[name] = best_f1_threshold(prob, y)
    null_passive = [ep for ep, event in passive if not event]
    null_probed = [ep for ep, event in probed if not event]
    h_passive, arl_passive = calibrate_alarm_threshold(predictor, null_passive)
    h_probed, arl_probed = calibrate_alarm_threshold(predictor, null_probed)
    return models, thresholds, cal_f1, predictor, (h_passive, arl_passive), (h_probed, arl_probed)


def summarize_metrics(records: list[dict]) -> dict:
    out = {}
    for control in (False, True):
        cohort = "no_event" if control else "event"
        out[cohort] = {}
        for offset in OFFSETS:
            out[cohort][str(offset)] = {}
            rr = [r for r in records if r["control"] == control and r["offset"] == offset]
            for arm in ("draft2", "signrand", "comparator", "comparator_probed"):
                aa = [r for r in rr if r["arm"] == arm]
                out[cohort][str(offset)][arm] = {
                    key: float(np.mean([r[key] for r in aa]))
                    for key in ("auc", "auprc", "f1_05", "f1_best", "brier", "logloss")
                }
    return out


def run_cell(nx: int, confounded: bool, wu_scale: float = 1.0) -> dict:
    start = time.time(); inst = Instance(nx, confounded, wu_scale)
    models, thresholds, cal_f1, predictor, passive_alarm_cal, probed_alarm_cal = build_calibration(inst)
    h_passive, arl_passive = passive_alarm_cal
    h_probed, arl_probed = probed_alarm_cal
    records, class_values = [], {"draft2": [], "signrand": []}
    alarm = {"passive_event": [], "passive_control": [], "probed_event": [], "probed_control": []}
    for s in range(N_SCORE):
        for control in (False, True):
            event = not control
            pep = simulate(inst, 200_000 + s, event, True)
            nep = simulate(inst, 200_000 + s, event, False)
            times, stat_a, stat_b = statistic_traces(pep)
            traces = {
                "draft2": stat_a, "signrand": stat_b,
                "comparator": predictor.support_trace(nep, times),
                "comparator_probed": predictor.support_trace(pep, times),
            }
            for kind, ep, threshold in (("passive", nep, h_passive), ("probed", pep, h_probed)):
                hit = any(EVENT_T < t <= EVENT_T + 200 for t in predictor.cusum_alarm_times(ep, threshold))
                alarm[f"{kind}_{'control' if control else 'event'}"].append(hit)
            for offset in OFFSETS:
                t = EVENT_T + offset; truth = labels_at(inst, t, event)
                for arm, trace in traces.items():
                    score = value_at(times, trace, t)
                    prob = pava_apply(models[arm], score)
                    clipped = np.clip(prob, 1e-12, 1 - 1e-12)
                    records.append({
                        "seed": s, "control": control, "offset": offset, "arm": arm,
                        "auc": auc_score(score, truth), "auprc": average_precision(score, truth),
                        "f1_05": f1_score(prob >= .5, truth),
                        "f1_best": f1_score(prob >= thresholds[arm], truth),
                        "brier": float(np.mean((prob - truth) ** 2)),
                        "logloss": float(-np.mean(truth * np.log(clipped) + (~truth) * np.log(1 - clipped))),
                    })
            if control:
                # Fault-free late-window means directly test R3-1's inversion mechanism.
                for arm, trace in (("draft2", stat_a), ("signrand", stat_b)):
                    score = value_at(times, trace, 1500)
                    class_values[arm].append([
                        float(score[inst.direct].mean()), float(score[inst.indirect].mean()),
                        float(score[inst.nonreachable].mean()),
                    ])
    cert_ep = simulate(inst, 99_999, False, False)
    return {
        "cell": {"nx": nx, "confounded": confounded, "wu_scale": wu_scale},
        "certifications": inst.certifications(cert_ep),
        "probe_steps": simulate(inst, 88_888, False, True)["probe_steps"],
        "calibration": {"episodes": R_CAL, "event_share": .5, "best_threshold": thresholds,
                        "micro_f1_at_selected_threshold": cal_f1},
        "comparator_formula": "q_c(t)=||beta_action,c||_2/sigma_c - |sqrt(n)*mean_{i in trailing min(500,t)}((innovation_i,c-mu_c)/sigma_c)|",
        "cusum": {"passive_threshold": h_passive, "passive_approx_calibration_ARL": arl_passive,
                  "probed_threshold": h_probed, "probed_approx_calibration_ARL": arl_probed,
                  **{key: float(np.mean(value)) for key, value in alarm.items()}},
        "metrics": summarize_metrics(records),
        "fault_free_class_mean_a": {
            arm: dict(zip(("direct_action_children", "reachable_indirect", "non_reachable"),
                          np.mean(values, axis=0).tolist())) for arm, values in class_values.items()
        },
        "runtime_seconds": time.time() - start,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Nx=10 confounder-present only")
    args = parser.parse_args()
    print(json.dumps({"date": "2026-09-07", "python": platform.python_version(),
                      "numpy": np.__version__, "R_CAL": R_CAL, "N_SCORE": N_SCORE,
                      "definition": "AUC/AP and F1 are computed across channels within each episode/offset, then averaged across seeds."}))
    cells = [(10, True, 1.0)] if args.quick else [
        (10, True, 1.0), (10, False, 1.0), (30, True, 1.0), (30, False, 1.0),
        (10, True, 0.0),  # requested W_u=0 diagnostic ablation
    ]
    results = []
    for cell in cells:
        result = run_cell(*cell); results.append(result)
        print(json.dumps(result, sort_keys=True)); print("CELL_DONE", cell, f"{result['runtime_seconds']:.1f}s", flush=True)
    print(json.dumps({"all_cells_runtime_seconds": float(sum(r["runtime_seconds"] for r in results))}))


if __name__ == "__main__":
    main()
