"""Round-2 mutants against frozen gate d23960e6da441de7 (reviewer: claude-fable).
Same harness as executable-proofs/gate/mutants.py: monkeypatch a contract_ref function in both
contract_ref and test_gate, run every test_gate test, count failures. 0 failures = SURVIVED."""
import sys, pathlib, numpy as np
GATE = pathlib.Path(__file__).resolve().parents[1] / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))
import contract_ref as ref, test_gate

def failures():
    bad = []
    for name in sorted(t for t in dir(test_gate) if t.startswith("test_")):
        try: getattr(test_gate, name)()
        except Exception: bad.append(name)
    return bad

def with_patch(**kw):
    saved = {k: (getattr(ref, k), getattr(test_gate, k)) for k in kw}
    for k, v in kw.items(): setattr(ref, k, v); setattr(test_gate, k, v)
    try: return failures()
    finally:
        for k, (a, b) in saved.items(): setattr(ref, k, a); setattr(test_gate, k, b)

O = {k: getattr(ref, k) for k in ("open_loop_response", "jacobian_piecewise", "structural_reach",
                                 "structural_reach_full", "s_obs_eps", "max_pairwise_corr", "hpdt", "check_spacing",
                                 "build_adjacency")}

# ---- E2c/E2d: |corr| replaced by signed corr (negative confounding invisible) ----
def corr_no_abs(a, x, witness=None):
    a = np.atleast_2d(a.T).T; x = np.atleast_2d(x.T).T
    if witness is not None:
        k, j = witness
        if a[:, k].std() == 0 or x[:, j].std() == 0: return float('nan')
    best, ok = 0.0, False
    for k in range(a.shape[1]):
        for j in range(x.shape[1]):
            if a[:, k].std() == 0 or x[:, j].std() == 0: continue
            ok = True; best = max(best, np.corrcoef(a[:, k], x[:, j])[0, 1])   # abs() dropped
    return best if ok else float('nan')

# ---- E2c/E2d: only action column 0 scanned (multivariate statistic collapsed to univariate) ----
def corr_first_action_only(a, x, witness=None):
    a = np.atleast_2d(a.T).T; x = np.atleast_2d(x.T).T
    if witness is not None:
        k, j = witness
        if a[:, k].std() == 0 or x[:, j].std() == 0: return float('nan')
    best, ok = 0.0, False
    for j in range(x.shape[1]):
        if a[:, 0].std() == 0 or x[:, j].std() == 0: continue
        ok = True; best = max(best, abs(np.corrcoef(a[:, 0], x[:, j])[0, 1]))
    return best if ok else float('nan')

# ---- C3: padding guard removed; assign = -1 silently indexes the LAST latent (python negative index) ----
def s_obs_no_padding_guard(latent_effect, assign, gain, avail, eps):
    C = len(assign); out = np.zeros(C, bool)
    for c in range(C):
        if not avail[c]: continue
        out[c] = abs(gain[c]) * latent_effect[assign[c]] > eps
    return out

# ---- C3: strict > replaced by >= at the epsilon boundary ----
def s_obs_ge(latent_effect, assign, gain, avail, eps):
    C = len(assign); out = np.zeros(C, bool)
    for c in range(C):
        j = assign[c]
        if j < 0 or not avail[c]: continue
        out[c] = abs(gain[c]) * latent_effect[j] >= eps
    return out

# ---- C3: gain squared instead of |gain| ----
def s_obs_gain_sq(latent_effect, assign, gain, avail, eps):
    C = len(assign); out = np.zeros(C, bool)
    for c in range(C):
        j = assign[c]
        if j < 0 or not avail[c]: continue
        out[c] = gain[c] ** 2 * latent_effect[j] > eps
    return out

# ---- D/G: schedule check ignores the episode end (last event may be administratively censored) ----
def spacing_no_episode_end(event_times, episode_end, horizon, match_window):
    ts = sorted(event_times)
    return all(ts[i+1] - ts[i] >= horizon + match_window for i in range(len(ts) - 1))

# ---- D/G: spacing strict > instead of >= ----
def spacing_strict(event_times, episode_end, horizon, match_window):
    ts = list(sorted(event_times)) + [episode_end]
    return all(ts[i+1] - ts[i] > horizon + match_window for i in range(len(ts) - 1))

# ---- D/G: spacing does not sort event times ----
def spacing_unsorted(event_times, episode_end, horizon, match_window):
    ts = list(event_times) + [episode_end]
    return all(ts[i+1] - ts[i] >= horizon + match_window for i in range(len(ts) - 1))

# ---- G: HPDT uses the median instead of the mean over events ----
def hpdt_median(delays, outcome, horizon):
    delays = np.asarray(delays, float); outcome = np.asarray(outcome)
    d = np.where(outcome == 'detected', np.minimum(delays, horizon), horizon)
    return float(np.median(d))

# ---- G: unknown outcome classes (e.g. 'censored', 'next_event', 'episode_end') scored as detected ----
def hpdt_unknown_as_detected(delays, outcome, horizon):
    delays = np.asarray(delays, float); outcome = np.asarray(outcome)
    d = np.where(np.isin(outcome, ['missed', 'terminated']), horizon, np.minimum(delays, horizon))
    return float(d.mean())

# ---- C4: family N response evaluated at z = 0 instead of the stationary mean zbar ----
def olr_ignore_zbar(A, B, a, h, tau=0, zbar=None, step_fn=None):
    return O["open_loop_response"](A, B, a, h, tau, None, step_fn)

# ---- C1: sign pattern replaced by a magnitude threshold (entries below thr treated as absent edges) ----
def make_thresholded_reach(thr):
    def build_adj(A_b, C_d=None, A_d=None, A_w=None, A_x=None):
        N_b = A_b.shape[0]; N_d = 0 if C_d is None else C_d.shape[0]
        N_w = 0 if A_w is None else A_w.shape[0]; N_x = 0 if A_x is None else A_x.shape[0]
        N = N_b + N_d + N_w + N_x; adj = np.zeros((N, N), bool)
        sl = {"b": slice(0, N_b), "d": slice(N_b, N_b+N_d), "w": slice(N_b+N_d, N_b+N_d+N_w), "x": slice(N_b+N_d+N_w, N)}
        adj[sl["b"], sl["b"]] = np.abs(A_b) > thr
        if N_d: adj[sl["d"], sl["b"]] = np.abs(C_d) > thr; adj[sl["d"], sl["d"]] = (np.abs(A_d) > thr) if A_d is not None else False
        if N_w: adj[sl["w"], sl["w"]] = np.abs(A_w) > thr
        if N_x: adj[sl["x"], sl["x"]] = np.abs(A_x) > thr
        return adj, sl
    def reach_full(A_b, B, H, tau=0, C_d=None, A_d=None, A_w=None, A_x=None):
        adj, sl = build_adj(A_b, C_d, A_d, A_w, A_x)
        N = adj.shape[0]; reach = np.zeros(N, bool)
        if H <= tau: return reach
        frontier = np.zeros(N, bool); frontier[sl["b"]] = (np.abs(B) > thr).any(axis=1)
        reach |= frontier
        for _ in range(tau + 2, H + 1):
            frontier = (adj.astype(int) @ frontier.astype(int)) > 0; reach |= frontier
        return reach
    return reach_full

mutants = {
    "FB-M1 E2 corr abs() dropped (negative confounding invisible)": dict(max_pairwise_corr=corr_no_abs),
    "FB-M2 E2 only action column 0 scanned": dict(max_pairwise_corr=corr_first_action_only),
    "FB-M3 C3 padding guard removed (assign=-1 -> last latent)": dict(s_obs_eps=s_obs_no_padding_guard),
    "FB-M4 C3 boundary >= instead of >": dict(s_obs_eps=s_obs_ge),
    "FB-M5 C3 gain^2 instead of |gain|": dict(s_obs_eps=s_obs_gain_sq),
    "FB-M6 G spacing ignores episode end": dict(check_spacing=spacing_no_episode_end),
    "FB-M7 G spacing strict > instead of >=": dict(check_spacing=spacing_strict),
    "FB-M8 G spacing does not sort events": dict(check_spacing=spacing_unsorted),
    "FB-M9 G HPDT median instead of mean": dict(hpdt=hpdt_median),
    "FB-M10 G HPDT unknown outcome classes scored as detected": dict(hpdt=hpdt_unknown_as_detected),
    "FB-M11 C4 family N response ignores zbar": dict(open_loop_response=olr_ignore_zbar),
    "FB-M12 C1 magnitude threshold 0.15 instead of sign pattern": dict(structural_reach_full=make_thresholded_reach(0.15)),
    "FB-M13 C1 magnitude threshold 0.25 (> c_min) instead of sign pattern": dict(structural_reach_full=make_thresholded_reach(0.25)),
}
surv = []
for name, patch in mutants.items():
    bad = with_patch(**patch)
    print(f"{'KILLED  ' if bad else 'SURVIVED'} {name}: {len(bad)} failing tests {bad if bad else ''}")
    if not bad: surv.append(name)
print(f"\n{len(surv)}/{len(mutants)} mutants SURVIVED the frozen gate:")
for s in surv: print("  -", s)
sys.exit(0)
