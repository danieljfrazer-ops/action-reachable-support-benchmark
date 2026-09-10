"""Mutation run. Every mutant must make >= 1 gate test fail. Includes all 23 distinct reviewer mutants from rounds 1-2
(Claude, Codex, Gemini, Fable, Opus). Originals are captured BEFORE patching (fixes the fake-kill found by Opus)."""
import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import contract_ref as ref, test_gate
O = {k: getattr(ref, k) for k in ("open_loop_response", "jacobian_piecewise", "structural_reach", "structural_reach_full",
                                  "build_adjacency", "s_obs_eps", "max_pairwise_corr", "hpdt", "check_spacing",
                                  "count_alarms", "match_alarms", "aggregate_primary", "pairwise_corr", "auc_prob_superiority",
                                  "auc_pre_event_support", "count_alarms_timed", "run_length_from_reset")}
def failures():
    n = 0
    for name in sorted(t for t in dir(test_gate) if t.startswith("test_")):
        try: getattr(test_gate, name)()
        except Exception: n += 1
    return n
def with_patch(**kw):
    saved = {k: (getattr(ref, k), getattr(test_gate, k, None)) for k in kw}
    for k, v in kw.items(): setattr(ref, k, v); setattr(test_gate, k, v)
    try: return failures()
    finally:
        for k, (a, b) in saved.items(): setattr(ref, k, a); setattr(test_gate, k, b)

def sr_full_no_tau(A_b, B, H, tau=0, **k): return O["structural_reach_full"](A_b, B, H, 0, **k)
def sr_full_premature(A_b, B, H, tau=0, C_d=None, A_d=None, A_w=None, A_x=None):     # Gemini GM2-1
    adj, sl = O["build_adjacency"](A_b, C_d, A_d, A_w, A_x); N = adj.shape[0]; reach = np.zeros(N, bool)
    if H <= tau: return reach
    fr = np.zeros(N, bool); fr[sl["b"]] = (B != 0).any(axis=1); reach |= fr
    for _ in range(2, H + 1): fr = (adj.astype(int) @ fr.astype(int)) > 0; reach |= fr
    return reach
def adj_no_Ad(A_b, C_d=None, A_d=None, A_w=None, A_x=None):                            # Codex R2-CX-01 / Opus M15
    adj, sl = O["build_adjacency"](A_b, C_d, None, A_w, A_x); return adj, sl
def adj_mag_025(A_b, C_d=None, A_d=None, A_w=None, A_x=None):                          # Fable M13
    adj, sl = O["build_adjacency"](A_b, C_d, A_d, A_w, A_x)
    adj[sl["b"], sl["b"]] = np.abs(A_b) > 0.25; return adj, sl
def sr_full_using(adjfn):
    def f(A_b, B, H, tau=0, C_d=None, A_d=None, A_w=None, A_x=None):
        adj, sl = adjfn(A_b, C_d, A_d, A_w, A_x); N = adj.shape[0]; reach = np.zeros(N, bool)
        if H <= tau: return reach
        fr = np.zeros(N, bool); fr[sl["b"]] = (B != 0).any(axis=1); reach |= fr
        for _ in range(tau + 2, H + 1): fr = (adj.astype(int) @ fr.astype(int)) > 0; reach |= fr
        return reach
    return f
def sr_body(fullfn): return lambda A, B, H, tau=0: fullfn(A, B, H, tau)[:A.shape[0]]
def sobs_no_pad(e, assign, gain, avail, eps):                                          # Fable M3 / Opus M4
    return np.array([bool(avail[c]) and abs(gain[c]) * e[int(assign[c])] > eps for c in range(len(assign))])
def sobs_ge(e, assign, gain, avail, eps):                                               # Fable M4 / Opus M5
    return np.array([int(assign[c]) >= 0 and bool(avail[c]) and abs(gain[c]) * e[int(assign[c])] >= eps for c in range(len(assign))])
def sobs_gain_sq(e, assign, gain, avail, eps):                                          # Fable M5
    return np.array([int(assign[c]) >= 0 and bool(avail[c]) and gain[c]**2 * e[int(assign[c])] > eps for c in range(len(assign))])
def sobs_gain_ignored(e, assign, gain, avail, eps): return O["s_obs_eps"](e, assign, np.ones_like(gain), avail, eps)   # M8 (fixed)
def corr_no_abs(a, x, witness=None):                                                    # Fable M1
    a = np.atleast_2d(a.T).T; x = np.atleast_2d(x.T).T; best, ok = -np.inf, False
    for k in range(a.shape[1]):
        for j in range(x.shape[1]):
            if a[:, k].std() == 0 or x[:, j].std() == 0: continue
            ok = True; best = max(best, float(np.corrcoef(a[:, k], x[:, j])[0, 1]))
    return best if ok else float('nan')
def corr_col0(a, x, witness=None):                                                      # Fable M2
    a = np.atleast_2d(a.T).T; return O["max_pairwise_corr"](a[:, :1], x, None)
def corr_mean(a, x, witness=None):                                                      # Opus M8
    a = np.atleast_2d(a.T).T; x = np.atleast_2d(x.T).T; vals = []
    for k in range(a.shape[1]):
        for j in range(x.shape[1]):
            if a[:, k].std() == 0 or x[:, j].std() == 0: continue
            vals.append(abs(float(np.corrcoef(a[:, k], x[:, j])[0, 1])))
    return float(np.mean(vals)) if vals else float('nan')
def hpdt_median(delays, outcome, horizon):                                              # Fable M9 / Opus M1
    outcome = np.asarray(outcome); d = np.where(outcome == "detected", np.minimum(np.asarray(delays, float), horizon), float(horizon)); return float(np.median(d))
def hpdt_two_classes(delays, outcome, horizon):                                         # Fable M10
    outcome = np.asarray(outcome); d = np.where(np.isin(outcome, ["missed", "terminated"]), float(horizon), np.minimum(np.asarray(delays, float), horizon)); return float(d.mean())
def hpdt_censoring_excluded(delays, outcome, horizon):
    d = np.asarray(delays, float)[np.asarray(outcome) == "detected"]; return float(np.minimum(d, horizon).mean())
def spacing_no_end(ev, end, h, w): ts = sorted(ev); return all(ts[i+1]-ts[i] >= h+w for i in range(len(ts)-1))   # Fable M6 / Opus M2
def spacing_strict(ev, end, h, w): ts = sorted(ev)+[end]; return all(ts[i+1]-ts[i] > h+w for i in range(len(ts)-1))   # Fable M7 / Opus M3
def spacing_unsorted(ev, end, h, w): ts = list(ev)+[end]; return all(ts[i+1]-ts[i] >= h+w for i in range(len(ts)-1))   # Fable M8
def olr_no_zbar(A, B, a, h, tau=0, zbar=None, step_fn=None): return O["open_loop_response"](A, B, a, h, tau, None, step_fn)   # Fable M11 / Opus M7
def olr_tau_cap(A, B, a, h, tau=0, zbar=None, step_fn=None): return O["open_loop_response"](A, B, a, h, min(tau, 1), zbar, step_fn)   # Codex r1
def jac_999B(A, B, h, tau=0): return np.zeros_like(B) if h <= tau else (999.0 * B if tau > 0 else O["jacobian_piecewise"](A, B, h, tau))   # Gemini r1
def sr_skip_H2(A, B, H, tau=0): return O["structural_reach"](A, B, H, tau) if H >= 3 else O["structural_reach"](A, B, 1, tau)   # Gemini r1

def ca_no_refractory(raw, p, r):
    out, run = [], 0
    for t, v in enumerate(raw):
        run = run + 1 if v else 0
        if run >= p: out.append(t); run = 0
    return out
def ca_leaky(raw, p, r):
    out, run, block = [], 0, -1
    for t, v in enumerate(raw):
        if t <= block: run = 0; continue
        run += 1 if v else 0
        if run >= p: out.append(t); run = 0; block = t + r
    return out
def ca_off_by_one(raw, p, r):
    out, run, block = [], 0, -1
    for t, v in enumerate(raw):
        if t < block: run = 0; continue
        run = run + 1 if v else 0
        if run >= p: out.append(t); run = 0; block = t + r
    return out
def ma_no_episode_end(alarm_times, event_times, H_det, episode_end):
    return O["match_alarms"](alarm_times, event_times, H_det, 10**9)
def ma_event_step_counts(alarm_times, event_times, H_det, episode_end):
    ev = sorted(event_times); al = sorted(alarm_times); used=set(); D=[]; Oc=[]
    for i, e in enumerate(ev):
        nxt = ev[i+1] if i+1 < len(ev) else episode_end; end = min(e+H_det, nxt, episode_end); hit=None
        for t in al:
            if e <= t <= end: hit=t; break
        if hit is None: D.append(H_det); Oc.append("missed")
        else: used.add(hit); D.append(hit-e); Oc.append("detected")
    return D, Oc, [t for t in al if t not in used]
def ap_median(rows, est_a="cusum_channel_agnostic", est_b="seq_ibd"):
    from collections import defaultdict
    cell = defaultdict(dict)
    for r in rows: cell[(r["seed"], r["level"], r["delay"])][r["estimator"]] = float(r["hpdt"])
    per = defaultdict(list); dropped = 0
    for k, v in cell.items():
        if est_a in v and est_b in v: per[k[0]].append(v[est_a]-v[est_b])
        else: dropped += 1
    return {s: float(np.median(v)) for s, v in per.items()}, dropped
def ap_ignores_delay(rows, est_a="cusum_channel_agnostic", est_b="seq_ibd"):
    rows2 = [dict(r, delay=0) for r in rows]; return O["aggregate_primary"](rows2, est_a, est_b)
def sobs_silent_oob(e, assign, gain, avail, eps):
    C = len(assign); out = np.zeros(C, bool)
    for c in range(C):
        j = int(assign[c])
        if j < 0 or j >= len(e) or not avail[c]: continue
        out[c] = abs(float(gain[c])) * float(e[j]) > eps
    return out
def corr_witness_only(a, x, witness=None):
    return ref.pairwise_corr(a, x, *witness) if witness is not None else O["max_pairwise_corr"](a, x)

def adj_no_world_edges(A_b, C_d=None, A_d=None, A_w=None, A_x=None):
    adj, sl = O["build_adjacency"](A_b, C_d, A_d, A_w, A_x)
    adj[sl["w"], sl["w"]] = False; adj[sl["x"], sl["x"]] = False; return adj, sl
def pc_signed(a, x, k, j):
    a = np.atleast_2d(a.T).T; x = np.atleast_2d(x.T).T
    if a[:, k].std() == 0 or x[:, j].std() == 0: return float('nan')
    return float(np.corrcoef(a[:, k], x[:, j])[0, 1])
def ma_strict_upper(alarm_times, event_times, H_det, episode_end):
    ev = sorted(event_times); al = sorted(alarm_times); used=set(); D=[]; Oc=[]
    for i, e in enumerate(ev):
        nxt = ev[i+1] if i+1 < len(ev) else episode_end; end = min(e+H_det, nxt, episode_end); hit=None
        for t in al:
            if e < t < end: hit=t; break
        if hit is None: D.append(H_det); Oc.append("missed")
        else: used.add(hit); D.append(hit-e); Oc.append("detected")
    return D, Oc, [t for t in al if t not in used]

def adj_w_to_x(A_b, C_d=None, A_d=None, A_w=None, A_x=None):                  # Gemini R4-GM-M1
    adj, sl = O["build_adjacency"](A_b, C_d, A_d, A_w, A_x)
    if A_w is not None and A_x is not None: adj[sl["x"], sl["w"]] = True
    return adj, sl
def ap_abs(rows, est_a="seq_ibd", est_b="cusum_linear_channel_agnostic", metric="auc"):   # Codex abs-difference
    d, dr, du = O["aggregate_primary"](rows, est_a, est_b, metric); return {k: abs(v) for k, v in d.items()}, dr, du
def ap_last_wins(rows, est_a="seq_ibd", est_b="cusum_linear_channel_agnostic", metric="auc"):   # Opus R4-M2 (silent overwrite)
    from collections import defaultdict
    cell = defaultdict(dict)
    for r in rows: cell[tuple(r[f] for f in ref.CELL_KEY)][r["estimator"]] = float(r[metric])
    per = defaultdict(list); dropped = 0
    for k, v in cell.items():
        if est_a in v and est_b in v: per[k[:3] + (k[5],)].append(v[est_a] - v[est_b])
        else: dropped += 1
    return {k: float(np.mean(v)) for k, v in per.items()}, dropped, 0
def ma_last_alarm(alarm_times, event_times, H_det, episode_end):             # Opus R4-M1
    ev = sorted(event_times); al = sorted(alarm_times); used=set(); D=[]; Oc=[]
    for i, e in enumerate(ev):
        nxt = ev[i+1] if i+1 < len(ev) else episode_end; end = min(e+H_det, nxt, episode_end)
        hits = [t for t in al if e < t <= end]
        if not hits: D.append(H_det); Oc.append("missed")
        else: used.add(hits[-1]); D.append(hits[-1]-e); Oc.append("detected")
    return D, Oc, [t for t in al if t not in used]
def sobs_abs_product(e, assign, gain, avail, eps):                           # Opus R4-M3
    return np.array([int(assign[c]) >= 0 and bool(avail[c]) and abs(gain[c] * e[int(assign[c])]) > eps for c in range(len(assign))])

# ---- v3.9 / D-11 mutants (author) ----
def apes_all_channels(scores, pre_S, post_S):                                  # D-11.1: forgets to restrict to the pre-event support
    return O["auc_prob_superiority"](scores, post_S)
def apes_inverted(scores, pre_S, post_S):                                      # D-11.1: positives = lost channels
    s = np.asarray(scores, float); pre = np.asarray(pre_S, bool); post = np.asarray(post_S, bool); return O["auc_prob_superiority"](s[pre], ~post[pre])
def apes_no_half_credit(scores, pre_S, post_S):
    s = np.asarray(scores, float); pre = np.asarray(pre_S, bool); post = np.asarray(post_S, bool); pos, neg = s[pre][post[pre]], s[pre][~post[pre]]
    if len(pos) == 0 or len(neg) == 0: return float('nan')
    return float((pos[:, None] > neg[None, :]).sum() / (len(pos) * len(neg)))
def cat_refractory_in_emissions(raises, times, p, r):                          # D-11.5: refractory counted in the arm's unit, not steps
    counted, run, skip = [], 0, 0
    for v, t in zip(raises, times):
        if skip: skip -= 1; run = 0; continue
        run = run + 1 if v else 0
        if run >= p: counted.append(t); run = 0; skip = r
    return counted
def cat_leaky(raises, times, p, r):                                            # D-11.5: a zero emission does not break the run
    counted, run, block = [], 0, -float("inf")
    for v, t in zip(raises, times):
        if t <= block: run = 0; continue
        run += 1 if v else 0
        if run >= p: counted.append(t); run = 0; block = t + r
    return counted
def cat_strict_refractory(raises, times, p, r):                                # D-11.5: boundary t == t_a + r wrongly admitted
    counted, run, block = [], 0, -float("inf")
    for v, t in zip(raises, times):
        if t < block: run = 0; continue
        run = run + 1 if v else 0
        if run >= p: counted.append(t); run = 0; block = t + r
    return counted
def rl_no_censor_flag(counted, stream_end): return (int(min(counted)) if counted else int(stream_end), False)

mutants = {
    "D11-M1 pre-event AUC over all channels": dict(auc_pre_event_support=apes_all_channels),
    "D11-M2 pre-event AUC positives inverted": dict(auc_pre_event_support=apes_inverted),
    "D11-M3 pre-event AUC no tie credit": dict(auc_pre_event_support=apes_no_half_credit),
    "D11-M4 timed refractory in emissions": dict(count_alarms_timed=cat_refractory_in_emissions),
    "D11-M5 timed leaky persistence": dict(count_alarms_timed=cat_leaky),
    "D11-M6 timed refractory strict boundary": dict(count_alarms_timed=cat_strict_refractory),
    "D11-M7 run length drops censoring flag": dict(run_length_from_reset=rl_no_censor_flag),
    "R4-GM-M1 w->x edge": dict(build_adjacency=adj_w_to_x),
    "R4-CX abs aggregate": dict(aggregate_primary=ap_abs),
    "R4-M2 aggregate last-wins": dict(aggregate_primary=ap_last_wins),
    "R4-M1 match last alarm": dict(match_alarms=ma_last_alarm),
    "R4-M3 |gain*e|": dict(s_obs_eps=sobs_abs_product),
    "D9-CX world/distractor edges dropped": dict(build_adjacency=adj_no_world_edges),
    "D9-GM-M1 pairwise_corr signed": dict(pairwise_corr=pc_signed),
    "D9-GM-M2 match_alarms strict upper": dict(match_alarms=ma_strict_upper),
    "R3-M1 count_alarms ignores refractory": dict(count_alarms=ca_no_refractory),
    "R3-M2 leaky persistence": dict(count_alarms=ca_leaky),
    "R3-M8/GM3-6 refractory off by one": dict(count_alarms=ca_off_by_one),
    "R3-M4 match_alarms drops episode_end": dict(match_alarms=ma_no_episode_end),
    "GM3-5 alarm at event step counted": dict(match_alarms=ma_event_step_counts),
    "R3-M5/GM3-1 aggregate median": dict(aggregate_primary=ap_median),
    "CX3 aggregate ignores delay": dict(aggregate_primary=ap_ignores_delay),
    "R3-M7 s_obs silent out-of-range": dict(s_obs_eps=sobs_silent_oob),
    "R3-M9 corr returns witness not max": dict(max_pairwise_corr=corr_witness_only),
    "CL r1 no-delay reachability": dict(structural_reach_full=sr_full_no_tau, structural_reach=sr_body(sr_full_no_tau)),
    "CL r1 no-downstream": dict(structural_reach_full=lambda *a, **k: (lambda r: (r.__setitem__(slice(a[0].shape[0], None), False), r)[1])(O["structural_reach_full"](*a, **k))),
    "GM r1 999B": dict(jacobian_piecewise=jac_999B),
    "GM r1 skip-H2": dict(structural_reach=sr_skip_H2),
    "CX r1 tau-cap": dict(open_loop_response=olr_tau_cap),
    "GM2-1 premature delayed propagation": dict(structural_reach_full=sr_full_premature, structural_reach=sr_body(sr_full_premature)),
    "CX2/OP-M15 A_d omitted": dict(build_adjacency=adj_no_Ad, structural_reach_full=sr_full_using(adj_no_Ad), structural_reach=sr_body(sr_full_using(adj_no_Ad))),
    "FB-M13 magnitude>0.25 edges": dict(build_adjacency=adj_mag_025, structural_reach_full=sr_full_using(adj_mag_025), structural_reach=sr_body(sr_full_using(adj_mag_025))),
    "FB-M3/OP-M4 padding guard dropped": dict(s_obs_eps=sobs_no_pad),
    "FB-M4/OP-M5 >= at boundary": dict(s_obs_eps=sobs_ge),
    "FB-M5 gain squared": dict(s_obs_eps=sobs_gain_sq),
    "M8 gain ignored": dict(s_obs_eps=sobs_gain_ignored),
    "FB-M1 abs dropped": dict(max_pairwise_corr=corr_no_abs),
    "FB-M2 column 0 only": dict(max_pairwise_corr=corr_col0),
    "OP-M8 mean not max": dict(max_pairwise_corr=corr_mean),
    "FB-M9/OP-M1 HPDT median": dict(hpdt=hpdt_median),
    "FB-M10 two outcome classes only": dict(hpdt=hpdt_two_classes),
    "HPDT censoring excluded": dict(hpdt=hpdt_censoring_excluded),
    "FB-M6/OP-M2 spacing ignores episode end": dict(check_spacing=spacing_no_end),
    "FB-M7/OP-M3 spacing strict": dict(check_spacing=spacing_strict),
    "FB-M8 spacing unsorted": dict(check_spacing=spacing_unsorted),
    "FB-M11/OP-M7 zbar ignored": dict(open_loop_response=olr_no_zbar),
    "M7 negative power": dict(jacobian_piecewise=lambda A, B, h, tau=0: np.linalg.matrix_power(A, h-1-tau) @ B),
}
base = failures(); assert base == 0, f"gate not clean before mutation: {base} failing"
# OP-2 guards: a mutant must not recurse into itself and must differ from the original on at least one probe input
A_ch = np.array([[0.5,0,0],[0.5,0.5,0],[0,0.5,0.5]]); B_ch = np.array([[1.0],[0.0],[0.0]])
C_d2 = np.array([[1.0,0.0],[0.0,0.0]]); A_d2 = np.array([[0.0,0.0],[0.5,0.0]])
PROBES = {
  "hpdt": [([1, 2, 30], ["detected"]*3, 100), ([5, 0], ["detected", "missed"], 100), ([5, 7], ["detected", "censored"], 100)],
  "check_spacing": [([100, 400], 600, 200, 50), ([100, 350], 600, 200, 50), ([400, 100], 700, 200, 50)],
  "s_obs_eps": [(np.array([1.0, 1.0, 1.0]), np.array([0, 1, -1]), np.array([1.0, 0.5, 1.0]), np.ones(3, bool), 0.1),
                (np.array([0.1]), np.array([0]), np.array([1.0]), np.array([True]), 0.1),
                (np.array([0.3]), np.array([0]), np.array([0.5]), np.array([True]), 0.1),
                (np.array([0.3]), np.array([0]), np.array([0.2]), np.array([True]), 0.1),   # |g|e = 0.06 < eps; gain-ignored says 0.3 > eps
                (np.array([1.0]), np.array([3]), np.array([1.0]), np.array([True]), 0.1),   # out-of-range assign: original raises
                (np.array([-1.0]), np.array([0]), np.array([1.0]), np.array([True]), 0.1)],  # negative effect: original raises
  "max_pairwise_corr": [(np.array([[1.,0.],[2.,0.],[3.,0.],[4.,0.]]), np.array([[-1.],[-2.],[-3.],[-4.]])),
                        (np.array([[0.,1.],[0.,2.],[0.,3.],[0.,4.]]), np.array([[1.],[2.],[3.],[4.]])),
                        (np.array([[1.,0.],[2.,1.],[3.,0.],[4.,1.],[5.,0.]]), np.array([[1.],[2.],[3.],[4.],[5.]])),   # two pairs, mean != max
                        (np.array([[1.,0.],[2.,1.],[3.,0.],[4.,1.],[5.,0.]]), np.array([[1.],[2.],[3.],[4.],[5.]]), (1, 0))],   # witness is not the max pair
  "jacobian_piecewise": [(np.diag([0.9, 0.9]), np.eye(2), 2, 1), (np.diag([0.9, 0.9]), np.eye(2), 1, 1)],
  "open_loop_response": [(np.diag([0.9,0.9]), np.eye(2), np.array([1.0,0.0]), 3, 2),
                         (np.diag([0.9,0.9]), np.eye(2), np.array([1.0,0.0]), 2, 0, np.array([0.3,-0.2]), lambda b, a: np.diag([0.9,0.9]) @ b + np.tanh(a) + 0.1*np.clip(b*b,-4,4))],
  "structural_reach": [(A_ch, B_ch, 2, 0), (A_ch, B_ch, 3, 1), (A_ch, B_ch, 2, 1)],
  "structural_reach_full": [(np.diag([0.9,0.9]), np.eye(2), 3, 0, C_d2, A_d2), (A_ch, B_ch, 3, 1)],
  "build_adjacency": [(np.diag([0.9,0.9]), C_d2, A_d2), (np.array([[0.5,0.0],[0.1,0.5]]),), (np.diag([0.9,0.9]), None, None, np.array([[0.9]]), np.array([[0.7]])),
                      (np.diag([0.9,0.9]), C_d2, A_d2, np.array([[0.9]]), np.array([[0.7]]))],
  "count_alarms": [([0,1,1,1,1,1,0,1,1,1,0], 3, 20), ([1,0,1,0,1,0,1], 3, 20), ([0]*23 + [1,1,1] + [0]*5, 3, 20),
                   ([0,1,1,1] + [0]*19 + [1,1,1] + [0]*4, 3, 20)],   # burst starting exactly at block_until (off-by-one)
  "match_alarms": [([150], [100], 200, 120), ([100], [100], 200, 2000), ([50, 1010], [1000], 200, 2000), ([1200], [1000], 200, 2000), ([1030, 1120], [1000], 200, 2000)],
  "pairwise_corr": [(np.array([[1.],[2.],[3.],[4.]]), np.array([[-1.],[-2.],[-3.],[-4.]]), 0, 0)],
  "aggregate_primary": [([dict(environment="e", regime="r", confounder="present", distractor_level=l, delay=0, seed=0, estimator=est, auc=v) for l, est, v in
                          ((10,"seq_ibd",0.9),(10,"cusum_linear_channel_agnostic",0.7),(30,"seq_ibd",0.8),(30,"cusum_linear_channel_agnostic",0.9))],),
                        ([dict(environment="e", regime="r", confounder="present", distractor_level=10, delay=0, seed=0, estimator=est, auc=v) for est, v in
                          (("seq_ibd",0.9),("cusum_linear_channel_agnostic",0.7),("seq_ibd",0.1))],)],
  "auc_prob_superiority": [([0.9, 0.5, 0.5, 0.1], [1, 1, 0, 0])],
  "auc_pre_event_support": [([0.9, 0.5, 0.5, 0.1, 5.0, -5.0], [1, 1, 1, 1, 0, 0], [1, 1, 0, 0, 0, 0]),
                            ([0.9, 0.8, 0.2, 0.1, 5.0, -5.0], [1, 1, 1, 1, 0, 0], [1, 1, 0, 0, 0, 0])],
  "count_alarms_timed": [([1,1,1,1,1,1,1,1], [2 + 20*i for i in range(8)], 3, 20), ([1,1,0,1,1,1,1,1], [2 + 20*i for i in range(8)], 3, 20),
                         ([1,1,1,1,1,1,1,1], [2 + 20*i for i in range(8)], 3, 19)],
  "run_length_from_reset": [([542], 4000), ([], 4000)],
  "aggregate_primary_neg": [([dict(environment="e", regime="r", confounder="present", distractor_level=10, delay=0, seed=0, estimator=est, auc=v) for est, v in
                          (("seq_ibd",0.7),("cusum_linear_channel_agnostic",0.9))],)],
}
def _eq(a, b):
    try:
        a, b = np.asarray(a, float), np.asarray(b, float)
    except (TypeError, ValueError):
        return a == b                                   # e.g. lists of strings
    if a.shape != b.shape: return False
    return bool(np.all((a == b) | (np.isnan(a) & np.isnan(b))))
def same(a, b):
    if isinstance(a, tuple) and isinstance(b, tuple):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))   # compare EVERY element (D9-GM-M2 lesson)
    return _eq(a, b)
def differs(name, fn):
    o = O.get(name)
    if o is None or name not in PROBES: return True
    for args in PROBES[name] + PROBES.get(name + "_neg", []):
        try:
            if not same(fn(*args), o(*args)): return True
        except RecursionError:
            raise AssertionError(f"mutant for {name} recursed into itself (fake kill)")
        except Exception:
            return True
    return False
_indist = [name for name, patch in mutants.items() if not any(differs(k, v) for k, v in patch.items())]
assert not _indist, f"mutants identical to the original on every probe input: {_indist}"
survivors = []
for name, patch in mutants.items():
    f = with_patch(**patch); print(f"{'KILLED  ' if f else 'SURVIVED'} {name}: {f} failing tests")
    if not f: survivors.append(name)
print(f"\n{len(mutants)-len(survivors)}/{len(mutants)} mutants killed"); sys.exit(1 if survivors else 0)
