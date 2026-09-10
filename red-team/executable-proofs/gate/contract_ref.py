"""Reference implementations of contract v3.6 formulas (normative). Pure numpy. Used by the gate tests.
Every function maps to a contract section; see coverage-matrix.md. Rewritten in full after round 4."""
import numpy as np

OUTCOMES = frozenset({"detected", "missed", "terminated"})   # frozen vocabulary (FB-M10)
CELL_KEY = ("environment", "regime", "confounder", "distractor_level", "delay", "seed")

# ---------- C1 structural reachability over ALL latents z = [b; d; w; x], with actuator delay tau ----------
def build_adjacency(A_b, C_d=None, A_d=None, A_w=None, A_x=None):
    """Directed edge j->i iff coefficient (i,j) is nonzero (sign pattern; magnitudes irrelevant).
    Blocks: b<-b (A_b), d<-b (C_d), d<-d (A_d), w<-w (A_w), x<-x (A_x). No other edges exist by contract B."""
    N_b = A_b.shape[0]; N_d = 0 if C_d is None else C_d.shape[0]
    N_w = 0 if A_w is None else A_w.shape[0]; N_x = 0 if A_x is None else A_x.shape[0]
    N = N_b + N_d + N_w + N_x; adj = np.zeros((N, N), bool)
    sl = {"b": slice(0, N_b), "d": slice(N_b, N_b+N_d), "w": slice(N_b+N_d, N_b+N_d+N_w), "x": slice(N_b+N_d+N_w, N)}
    adj[sl["b"], sl["b"]] = A_b != 0
    if N_d:
        adj[sl["d"], sl["b"]] = C_d != 0
        if A_d is not None: adj[sl["d"], sl["d"]] = A_d != 0
    if N_w: adj[sl["w"], sl["w"]] = A_w != 0
    if N_x: adj[sl["x"], sl["x"]] = A_x != 0
    return adj, sl

def structural_reach_full(A_b, B, H, tau=0, C_d=None, A_d=None, A_w=None, A_x=None):
    """Components with a directed path from a_t within H steps; first hit at h = tau+1; one hop per step after."""
    adj, sl = build_adjacency(A_b, C_d, A_d, A_w, A_x)
    N = adj.shape[0]; reach = np.zeros(N, bool)
    if H <= tau:
        return reach
    frontier = np.zeros(N, bool); frontier[sl["b"]] = (B != 0).any(axis=1)
    reach |= frontier
    for _ in range(tau + 2, H + 1):
        frontier = (adj.astype(int) @ frontier.astype(int)) > 0
        reach |= frontier
    return reach

def structural_reach(A, B, H, tau=0):
    return structural_reach_full(A, B, H, tau)[:A.shape[0]]

# ---------- C4 open-loop response and piecewise Jacobian ----------
def open_loop_response(A, B, a, h, tau=0, zbar=None, step_fn=None):
    n, k = B.shape
    f = step_fn or (lambda b, act: A @ b + B @ act)
    z0 = np.zeros(n) if zbar is None else np.asarray(zbar, float)
    def roll(a0):
        b = z0.copy()
        for step in range(1, h + 1):
            act = a0 if step == 1 + tau else np.zeros(k)
            b = f(b, act)
        return b
    return roll(np.asarray(a, float)) - roll(np.zeros(k))

def jacobian_piecewise(A, B, h, tau=0):
    if h <= tau:
        return np.zeros_like(B)
    return np.linalg.matrix_power(A, h - 1 - tau) @ B

# ---------- C3 operational observed support including gain ----------
def s_obs_eps(latent_effect, assign, gain, avail, eps):
    if np.any(np.asarray(latent_effect, float) < 0):
        raise ValueError("latent_effect is a norm (C2) and must be non-negative")
    C = len(assign); out = np.zeros(C, bool)
    for c in range(C):
        j = int(assign[c])
        if j < 0 or not avail[c]:
            continue
        out[c] = abs(float(gain[c])) * float(latent_effect[j]) > eps
    return out

# ---------- E2c/E2d multivariate confounding statistic ----------
def max_pairwise_corr(a, x, witness=None):
    a = np.atleast_2d(a.T).T; x = np.atleast_2d(x.T).T
    if witness is not None:
        k, j = witness
        if a[:, k].std() == 0 or x[:, j].std() == 0:
            return float('nan')
    best, any_eligible = 0.0, False
    for k in range(a.shape[1]):
        for j in range(x.shape[1]):
            if a[:, k].std() == 0 or x[:, j].std() == 0:
                continue
            any_eligible = True
            best = max(best, abs(float(np.corrcoef(a[:, k], x[:, j])[0, 1])))
    return best if any_eligible else float('nan')

def pairwise_corr(a, x, k, j):
    """|corr| of one declared witness pair (E2c). NaN if either column is constant."""
    a = np.atleast_2d(a.T).T; x = np.atleast_2d(x.T).T
    if a[:, k].std() == 0 or x[:, j].std() == 0: return float('nan')
    return abs(float(np.corrcoef(a[:, k], x[:, j])[0, 1]))

# ---------- G horizon-penalised detection time; schedule spacing ----------
def hpdt(delays, outcome, horizon):
    outcome = np.asarray(outcome)
    bad = set(outcome.tolist()) - OUTCOMES
    if bad:
        raise ValueError(f"unknown outcome class(es): {sorted(bad)}; allowed: {sorted(OUTCOMES)}")
    delays = np.asarray(delays, float)
    d = np.where(outcome == "detected", np.minimum(delays, horizon), float(horizon))
    return float(d.mean())

def check_spacing(event_times, episode_end, horizon, match_window):
    ts = sorted(event_times) + [episode_end]
    return all(ts[i+1] - ts[i] >= horizon + match_window for i in range(len(ts) - 1))

# ---------- G alarm counting and matching (OP-12) ----------
def count_alarms(raw, p, r):
    """Counted alarm times: an alarm counts at the step completing p consecutive raises; refractory r follows."""
    counted, run, block_until = [], 0, -1
    for t, v in enumerate(raw):
        if t <= block_until: run = 0; continue
        run = run + 1 if v else 0
        if run >= p:
            counted.append(t); run = 0; block_until = t + r
    return counted

def match_alarms(alarm_times, event_times, H_det, episode_end):
    """For each event e: the FIRST alarm with e < t <= min(e + H_det, next_event, episode_end) is its detection,
    else 'missed'. Windows are disjoint by construction. Unattributed alarms are false alarms (third return)."""
    ev = sorted(event_times); alarms = sorted(alarm_times); used = set(); delays, outcomes = [], []
    for i, e in enumerate(ev):
        nxt = ev[i+1] if i + 1 < len(ev) else episode_end
        end = min(e + H_det, nxt, episode_end); hit = None
        for t in alarms:
            if e < t <= end: hit = t; break
        if hit is None: delays.append(H_det); outcomes.append("missed")
        else: used.add(hit); delays.append(hit - e); outcomes.append("detected")
    false_alarms = [t for t in alarms if t not in used]
    return delays, outcomes, false_alarms

# ---------- G primary metric: per-episode AUC of a raw statistic vs S_obs_eps (R4-20) ----------
def auc_prob_superiority(scores, labels):
    """Threshold-free AUC = P(score_pos > score_neg) + 0.5 P(tie), over channel pairs. NaN if one class is empty."""
    s = np.asarray(scores, float); y = np.asarray(labels, bool)
    pos, neg = s[y], s[~y]
    if len(pos) == 0 or len(neg) == 0: return float('nan')
    gt = (pos[:, None] > neg[None, :]).sum(); eq = (pos[:, None] == neg[None, :]).sum()
    return float((gt + 0.5 * eq) / (len(pos) * len(neg)))

# ---------- D-9 aggregation of the primary effect: paired by seed within a full cell key ----------
def aggregate_primary(rows, est_a="seq_ibd", est_b="cusum_linear_channel_agnostic", metric="auc"):
    """rows: dicts with CELL_KEY fields, estimator, and `metric`. Returns per-(env, regime, confounder, seed) equal-weight
    mean over (distractor_level, delay) of est_a - est_b (signed), the count of unpaired cells, and the count of
    duplicate rows (a duplicate is an error and is counted, never silently overwritten)."""
    from collections import defaultdict
    cell = defaultdict(dict); dups = 0
    for r in rows:
        k = tuple(r[f] for f in CELL_KEY)
        if r["estimator"] in cell[k]: dups += 1; continue
        cell[k][r["estimator"]] = float(r[metric])
    per = defaultdict(list); dropped = 0
    for k, v in cell.items():
        if est_a in v and est_b in v: per[k[:3] + (k[5],)].append(v[est_a] - v[est_b])
        else: dropped += 1
    return {k: float(np.mean(v)) for k, v in per.items()}, dropped, dups

# ---------- D-11.1 primary: ranking over the PRE-EVENT support (contract G, v3.9) ----------
def auc_pre_event_support(scores, pre_S, post_S):
    """Primary outcome (D-11.1a). Restrict to channels in the pre-event support S^obs,eps(pre); positive = the channel is STILL
    in S^obs,eps after the event, negative = the event removed it. Mid-rank Mann-Whitney (ties half credit), so a fit-time
    constant scores exactly 0.5 and a statistic that ignores the event cannot exceed chance. Channels outside the pre-event
    support (padding, distractors, world) never enter the primary; they are scored by the secondary full-channel AUC.
    NaN if the restricted set has no positive or no negative; CL-4 certification guarantees >= 1 negative."""
    s = np.asarray(scores, float); pre = np.asarray(pre_S, bool); post = np.asarray(post_S, bool)
    if s.shape != pre.shape or pre.shape != post.shape: raise ValueError("scores, pre_S and post_S must have one entry per channel")
    return auc_prob_superiority(s[pre], post[pre])

# ---------- D-11.5 timestamp-aware alarm bookkeeping (contract G, v3.9) ----------
def count_alarms_timed(raises, times, p, r):
    """Counted alarm times for an arm that emits at its own cadence. `raises[i]` is the raw exceedance at the i-th emission and
    `times[i]` its environment step (strictly increasing; every step for a step arm, epoch steps for an epoch arm).
    Persistence p counts CONSECUTIVE EMISSIONS, i.e. the arm's declared unit; refractory r is in ENVIRONMENT STEPS: after a
    counted alarm at step t_a, emissions at times <= t_a + r are ignored and the run resets. Both arms' clocks start at reset
    (D-11.5); a warm-up prefix that cannot raise is simply a stretch with no emissions or with raise = 0.
    count_alarms(raw, p, r) == count_alarms_timed(raw, range(len(raw)), p, r)."""
    raises = list(raises); times = list(times)
    if len(raises) != len(times): raise ValueError("one time per emission")
    if any(times[i] >= times[i + 1] for i in range(len(times) - 1)): raise ValueError("emission times must be strictly increasing")
    counted, run, block_until = [], 0, -float("inf")
    for v, t in zip(raises, times):
        if t <= block_until: run = 0; continue
        run = run + 1 if v else 0
        if run >= p:
            counted.append(t); run = 0; block_until = t + r
    return counted

def run_length_from_reset(counted_alarm_times, stream_end):
    """Fresh-start run length (D-6b, D-11.5): environment steps from reset (t = 0) to the first counted alarm, INCLUDING any
    warm-up prefix the arm needs; (stream_end, True) if no alarm occurred, i.e. right-censored at the end of the stream."""
    if len(counted_alarm_times) == 0: return int(stream_end), True
    return int(min(counted_alarm_times)), False
