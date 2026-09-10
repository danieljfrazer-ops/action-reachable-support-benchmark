"""
sim_ibd_review.py -- independent adversarial red-team simulation of sequential-ibd-spec.md (Draft 1, 6 Sep 2026).

Written fresh, without reading the pre-existing review-ibd-spec/sim_ibd.py beyond its header (that file was left by
another agent at 22:29 and is not edited here; the brief said to write sim_ibd.py, but the "do not edit existing files"
rule takes precedence, hence this name).

What it does
  1. Toy family-L SCM per stage-0a-contract-v3.2 section B with registry constants (section 0): N_b=4, N_d=2, N_w=4,
     N_x=10 (f_conf=0.5), K=2, 4 padding channels -> C=24 (matches confirmation-design.csv n_channels at level 10),
     sigma_* from section 0, rho_u=0.8, a_max=2.0. Complete loss of actuator 0 at event_t (column 0 of B -> 0),
     satisfying CL-4 (b0 -> b1 -> d0 have no alternative path).
  2. The draft detector implemented as literally as the pseudo-code (section 9) allows: block-periodic reservoir-gated
     probes (L=3, Pi=75, B_max=30, burst Pi=6/100 steps), preceding-policy-steps null, |increment| paired differences at
     h in {1,2,3}, median/MAD reference with sigma_floor=0.1, z = max_h, two-sided per-channel CUSUM k=0.5, S = max_c,
     p/r alarm bookkeeping (p=3, r=20), reset + burst + n_ref=200 blind re-estimation on alarm, W=16 signed-rank z ->
     frozen isotonic p_c. The pseudo-code freezes p_cache during the blind window (the `continue` precedes the p_cache
     line); a PROSE variant that keeps updating p_c is measured for attribution only.
  3. Measurements: probe spend per run; ARL_0(h) two ways (fresh-start first false alarm; steady-state inter-alarm on a
     long null stream, which is what "false-alarm run lengths" ordinarily means); monotonicity; h* for ARL_0 = 1000 steps;
     confirmation runs at h* for episode_len 2,000 / event 1,000 and 20,000 / 10,000: delay distribution, HPDT (contract G,
     via contract_ref.hpdt / match_alarms / count_alarms), pre-event false alarms, blind-window overlap, co-primary p_c at
     offsets {10,50,200}; null bias of max_h z; the null-arm contamination by probe actions; reservoir_0 = B_max check;
     a minimal per-step innovation CUSUM comparator for context only (not the D-3a comparator, just a scale reference).

Usage: python3 sim_ibd_review.py [--quick]     pure numpy + multiprocessing; only this folder is written.
"""
import sys, os, math, time, json
import numpy as np
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "executable-proofs", "gate"))
from contract_ref import hpdt, count_alarms, match_alarms  # noqa: E402

QUICK = "--quick" in sys.argv
WU = float(sys.argv[sys.argv.index("--wu") + 1]) if "--wu" in sys.argv else 0.5   # policy u-gain (contract does not pin it)

# ------------------------------------------------------------------ registry (contract v3.2 section 0)
EPS, H_SUP, HSET = 0.05, 3, (1, 2, 3)
RHO_U, A_MAX = 0.8, 2.0
SIG = dict(b=0.1, d=0.1, w=0.1, x=0.1, o=0.05, a=0.1, u=1.0)
P_PERSIST, R_REFRACT, H_DET, PROBE_BUDGET, F_CONF = 3, 20, 200, 0.05, 0.5
N_B, N_D, N_W, N_X, K, N_PAD = 4, 2, 4, 10, 2, 4
C = N_B + N_D + N_W + N_X + N_PAD  # 24
IDX_B = list(range(0, N_B)); IDX_D = list(range(N_B, N_B + N_D))
IDX_X = list(range(N_B + N_D + N_W, N_B + N_D + N_W + N_X))
CONF_X = IDX_X[: int(F_CONF * N_X)]; UNCONF_X = IDX_X[int(F_CONF * N_X):]
# ------------------------------------------------------------------ draft knobs (section 8)
L_BLOCK, PI_NORMAL, PI_BURST, BURST_LEN = 3, 75, 6, 100
B_MAX, ETA = 30.0, 0.8
K_SLACK, SIG_FLOOR, N_REF, W_REPORT = 0.5, 0.1, 200, 16
PROBES = np.array([[1.0, 0], [-1.0, 0], [0, 1.0], [0, -1.0]])  # +-e_k, magnitude 1.0, frozen order (C4)


# ================================================================== family-L SCM (contract B)
class SCM:
    """Actuator 0 -> b0 -> b1 -> d0; actuator 1 -> b2 -> b3 -> d1. Losing actuator 0 removes {b0,b1,d0} from S (CL-4)."""

    def __init__(self, seed, tau=0, confounder=True, w_u=None):
        w_u = WU if w_u is None else w_u
        self.rng = np.random.default_rng(seed); self.tau = tau
        self.A_b = np.array([[0.7, 0.0, 0, 0], [0.3, 0.7, 0, 0], [0, 0, 0.7, 0.0], [0, 0, 0.3, 0.7]])
        self.B0 = np.array([[1.0, 0], [0, 0], [0, 1.0], [0, 0]]); self.B = self.B0.copy()
        self.C_d = np.array([[0.5, 0, 0, 0], [0, 0, 0.5, 0]]); self.A_d = 0.8 * np.eye(N_D)
        self.A_w = 0.8 * np.eye(N_W); self.A_x = 0.8 * np.eye(N_X)
        self.G = np.zeros(N_X); self.G[: int(F_CONF * N_X)] = (1.0 if confounder else 0.0)   # "absent" = G = 0, W_u unchanged
        self.W_o = np.zeros((K, C)); self.W_o[0, 0] = -0.3; self.W_o[0, 1] = -0.1; self.W_o[1, 2] = -0.3; self.W_o[1, 3] = -0.1
        self.W_u = np.array([w_u, w_u])
        self.b = np.zeros(N_B); self.d = np.zeros(N_D); self.w = np.zeros(N_W); self.x = np.zeros(N_X); self.u = 0.0
        self.aq = [np.zeros(K) for _ in range(tau)]
        self.o = self._observe(); self.n_sat = 0; self.n = 0
        for _ in range(400): self.step(None)
        self.n_sat = 0; self.n = 0

    def _observe(self):
        z = np.concatenate([self.b, self.d, self.w, self.x, np.zeros(N_PAD)])
        return z + SIG["o"] * self.rng.standard_normal(C)

    def policy(self):
        return self.W_o @ self.o + self.W_u * self.u + SIG["a"] * self.rng.standard_normal(K)

    def step(self, a_override):
        a = self.policy() if a_override is None else np.asarray(a_override, float)
        a = np.clip(a, -A_MAX, A_MAX); self.n_sat += int(np.any(np.abs(a) >= A_MAX)); self.n += 1
        if self.tau:
            self.aq.append(a); a_eff = self.aq.pop(0)
        else:
            a_eff = a
        r = self.rng
        b_new = self.A_b @ self.b + self.B @ a_eff + SIG["b"] * r.standard_normal(N_B)
        d_new = self.A_d @ self.d + self.C_d @ self.b + SIG["d"] * r.standard_normal(N_D)
        w_new = self.A_w @ self.w + SIG["w"] * r.standard_normal(N_W)
        x_new = self.A_x @ self.x + self.G * self.u + SIG["x"] * r.standard_normal(N_X)
        self.u = RHO_U * self.u + SIG["u"] * r.standard_normal()
        self.b, self.d, self.w, self.x = b_new, d_new, w_new, x_new
        self.o = self._observe()
        return a, self.o

    def lose_actuator(self, k=0):
        self.B = self.B0.copy(); self.B[:, k] = 0.0


def oracle_S(lost):
    s = np.zeros(C, bool)
    for c in ([2, 3, 5] if lost else [0, 1, 2, 3, 4, 5]): s[c] = True
    return s


# ================================================================== isotonic calibrator (PAVA), frozen after fit
class Isotonic:
    def fit(self, s, y):
        s = np.asarray(s, float); y = np.asarray(y, float); o = np.argsort(s, kind="stable"); s, y = s[o], y[o]
        vals, wts, lo = [], [], []
        for i in range(len(y)):
            vals.append(y[i]); wts.append(1.0); lo.append(i)
            while len(vals) > 1 and vals[-2] > vals[-1]:
                v = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / (wts[-2] + wts[-1]); w = wts[-2] + wts[-1]; l = lo[-2]
                vals.pop(); wts.pop(); lo.pop(); vals[-1] = v; wts[-1] = w; lo[-1] = l
        self.knots = np.array([s[l] for l in lo]); self.vals = np.array(vals); return self

    def __call__(self, s):
        idx = np.searchsorted(self.knots, s, side="right") - 1
        return self.vals[np.clip(idx, 0, len(self.vals) - 1)]


def signed_rank_z(dv):
    dv = np.asarray(dv, float); dv = dv[dv != 0]; n = len(dv)
    if n == 0: return -4.0                                 # draft: "absent extreme", not NaN
    ranks = np.argsort(np.argsort(np.abs(dv))) + 1.0
    wp = ranks[dv > 0].sum(); e = n * (n + 1) / 4; v = n * (n + 1) * (2 * n + 1) / 24
    return (wp - e) / math.sqrt(v)


# ================================================================== the draft detector (sections 2-4, 9)
class SeqIBD:
    """variant: 'DRAFT' (pseudo-code literal: p_cache frozen in blind window), 'PROSE' (p_c updated in blind window),
    'ABSMAX' (z = signed max_h |z_h| instead of max_h z_h; attribution only)."""

    def __init__(self, seed, variant="DRAFT", reservoir0=0.0, blind=True):
        self.rng = np.random.default_rng(seed); self.variant = variant; self.blind = blind
        self.h = math.inf; self.t = -1; self.reservoir = reservoir0; self.mode = "NORMAL"
        self.last_block_t = -10 ** 9; self.burst_start = -10 ** 9
        self.obs = {}                       # t -> obs (ring buffer, pruned)
        self.pending = []                   # (t_b, i) pairs not yet completed
        self.mu = np.zeros((3, C)); self.sig = np.ones((3, C))
        self.Gp = np.zeros(C); self.Gn = np.zeros(C)
        self.raise_run = 0; self.refract = 0; self.ref_until = -1; self.ref_buf = []
        self.win = [[[] for _ in range(C)] for _ in HSET]; self.last_argmax = np.zeros(C, int)
        self.p_cache = np.full(C, 0.5); self.g = None
        self.n_probe = 0; self.n_epochs = 0; self.alarms = []; self.blind_windows = []; self.ref_sizes = []
        self.S = 0.0; self.zlog = []; self.dlog = []; self.epoch_t = []

    # ---- interface v3
    def set_threshold(self, h): self.h = h

    def request_probe(self, steps):
        period = PI_BURST if self.mode == "BURST" else PI_NORMAL
        if self.mode == "BURST" and (self.reservoir < L_BLOCK or self.t - self.burst_start >= BURST_LEN):
            self.mode = "NORMAL"; period = PI_NORMAL
        if self.reservoir < L_BLOCK or (self.t - self.last_block_t) < period: return None
        n = min(steps, L_BLOCK); self.reservoir -= n; self.last_block_t = self.t
        self.n_probe += n
        t_b = self.t + 1                                   # first probe transition will carry index t+1
        for i in range(n): self.pending.append((t_b, i))
        return PROBES[self.rng.integers(0, 2 * K, size=n)]

    def _delta(self, t_b, i):
        """paired differences delta[h, c] for pair i of the block starting at t_b (probe start t_b+i, null start t_b-L+i).
        o(t) = observation at time t. Returns None if the ring lacks an index."""
        tp, tn = t_b + i, t_b - L_BLOCK + i
        need = [tp, tn] + [tp + hz for hz in HSET] + [tn + hz for hz in HSET]
        if any(k not in self.obs for k in need): return None
        out = np.empty((3, C))
        for j, hz in enumerate(HSET):
            out[j] = np.abs(self.obs[tp + hz] - self.obs[tp]) - np.abs(self.obs[tn + hz] - self.obs[tn])
        return out

    def update(self, tr):
        prev_obs, a, obs, probe_flag, t = tr
        self.t = t; self.reservoir = min(B_MAX, self.reservoir + PROBE_BUDGET)
        if prev_obs is not None and (t - 1) not in self.obs: self.obs[t - 1] = np.asarray(prev_obs, float)
        self.obs[t] = np.asarray(obs, float)
        for k in [k for k in self.obs if k < t - 12]: del self.obs[k]
        done = [(t_b, i) for (t_b, i) in self.pending if t_b + i + max(HSET) <= t]
        for pr in done:
            self.pending.remove(pr); dl = self._delta(*pr)
            if dl is None: continue
            self.n_epochs += 1
            zh = (dl - self.mu) / np.maximum(self.sig, SIG_FLOOR)
            if self.variant == "ABSMAX":
                am = np.argmax(np.abs(zh), axis=0); z = zh[am, np.arange(C)]
            else:
                am = np.argmax(zh, axis=0); z = zh[am, np.arange(C)]
            self.last_argmax = am
            for j in range(3):
                for c in range(C):
                    w = self.win[j][c]; w.append(dl[j, c])
                    if len(w) > W_REPORT: del w[0]
            self.dlog.append((pr[1], dl.copy())); self.zlog.append(z.copy()); self.epoch_t.append(t)
            in_ref = self.blind and t <= self.ref_until
            if in_ref:
                self.ref_buf.append(dl.copy())
                if self.variant == "PROSE": self._refresh_p()
                continue                                    # CUSUM frozen at 0; pseudo-code also skips p_cache
            self.Gp = np.maximum(0, self.Gp + z - K_SLACK); self.Gn = np.maximum(0, self.Gn - z - K_SLACK)
            self._refresh_p()
        if self.blind and self.ref_until >= 0 and t == self.ref_until: self._finish_reference()
        alarm = 0; self.S = float(max(self.Gp.max(), self.Gn.max()))
        self.raise_run = self.raise_run + 1 if self.S > self.h else 0
        if self.refract > 0:
            self.refract -= 1
        elif self.raise_run >= P_PERSIST:
            alarm = 1; self.refract = R_REFRACT; self.raise_run = 0; self.alarms.append(t)
            self.Gp[:] = 0; self.Gn[:] = 0; self.mode = "BURST"; self.burst_start = t
            if self.blind:
                self.ref_until = t + N_REF; self.ref_buf = []; self.blind_windows.append((t, t + N_REF))
        return np.clip(self.p_cache, 0, 1), self.S, alarm      # NB draft returns (p, alarm); interface v3 wants stat too

    def _refresh_p(self):
        if self.g is None: return
        s = np.array([signed_rank_z(self.win[self.last_argmax[c]][c]) for c in range(C)])
        self.p_cache = self.g(s)

    def _finish_reference(self):
        n = len(self.ref_buf); self.ref_sizes.append(n)
        if n >= 2:                                          # draft does not say what to do with too few pairs
            arr = np.array(self.ref_buf)                    # [n, 3, C]
            self.mu = np.median(arr, axis=0); self.sig = 1.4826 * np.median(np.abs(arr - self.mu), axis=0)
        self.ref_until = -1

    # ---- calibration (section 7) on a fault-free split
    def calibrate_from(self, deltas, s_scores, labels):
        arr = np.array(deltas)
        self.mu = np.median(arr, axis=0); self.sig = 1.4826 * np.median(np.abs(arr - self.mu), axis=0)
        self.g = Isotonic().fit(np.asarray(s_scores).ravel(), np.asarray(labels).ravel())


# ================================================================== harness
def run_stream(env, det, T, event_t=None, log_p_offsets=None, t0=0):
    """Drives env+detector for T steps starting at absolute step index t0. Returns dict of logs."""
    t = t0; obs = env.o.copy(); p_hist = {}; stat_hist = []; alarms = []
    while t < t0 + T:
        if event_t is not None and t == event_t: env.lose_actuator(0)
        acts = det.request_probe(L_BLOCK)
        if acts is not None:
            for a in acts:
                if event_t is not None and t == event_t: env.lose_actuator(0)
                t += 1; prev = obs; a_ap, obs = env.step(a)
                p, S, al = det.update((prev, a_ap, obs.copy(), True, t)); stat_hist.append(S)
                if al: alarms.append(t)
                if log_p_offsets and t in log_p_offsets: p_hist[t] = p.copy()
        else:
            t += 1; prev = obs; a_ap, obs = env.step(None)
            p, S, al = det.update((prev, a_ap, obs.copy(), False, t)); stat_hist.append(S)
            if al: alarms.append(t)
            if log_p_offsets and t in log_p_offsets: p_hist[t] = p.copy()
    return dict(alarms=alarms, p=p_hist, stat=stat_hist, t_end=t)


def make_calibrated(seed, variant="DRAFT", tau=0, T_cal=12000):
    """Fault-free calibration split: reference (mu, sigma) + isotonic g on (s_c, oracle label)."""
    env = SCM(seed, tau); det = SeqIBD(seed, variant); det.set_threshold(math.inf)
    det.g = None
    run_stream(env, det, T_cal)
    deltas = [d for (_, d) in det.dlog]
    # s_c per epoch after W pairs exist, at the draft's argmax horizon: recompute windowed scores from the log
    arr = np.array(deltas)                                    # [n, 3, C]
    mu = np.median(arr, axis=0); sig = np.maximum(1.4826 * np.median(np.abs(arr - mu), axis=0), SIG_FLOOR)
    zs = (arr - mu) / sig; am = np.argmax(zs, axis=1) if variant != "ABSMAX" else np.argmax(np.abs(zs), axis=1)
    s_all, y_all = [], []
    lab = oracle_S(False).astype(float)
    for n in range(W_REPORT, len(arr), 3):
        for c in range(C):
            s_all.append(signed_rank_z(arr[n - W_REPORT:n, am[n, c], c])); y_all.append(lab[c])
    det2 = SeqIBD(seed, variant); det2.calibrate_from(deltas, s_all, y_all)
    diag = dict(mu=det2.mu, sig=det2.sig, s_body=np.mean([s for s, y in zip(s_all, y_all) if y == 1]),
                s_x=np.mean([s for s, y in zip(s_all, y_all) if y == 0]), n_pairs=len(arr),
                zbar=np.array([z.mean(0) for z in [np.array(det.zlog)]])[0],
                sat=env.n_sat / env.n, deltas=arr, g=det2.g)
    return det2.mu, det2.sig, det2.g, diag


def fresh_detector(mu, sig, g, seed, variant, h, reservoir0=0.0, blind=True):
    d = SeqIBD(seed, variant, reservoir0, blind); d.mu, d.sig, d.g = mu.copy(), sig.copy(), g; d.set_threshold(h); return d


# ---- ARL_0 two ways
def arl_fresh(args):
    """fresh-start run length to FIRST alarm (h-independent path before the alarm), n_rl replicates."""
    h, variant, mu, sig, g, seed, n_rl, cap = args
    out = []
    for i in range(n_rl):
        env = SCM(seed * 1000 + i); det = fresh_detector(mu, sig, g, seed * 1000 + i, variant, h)
        t = 0; obs = env.o.copy(); hit = None
        while t < cap and hit is None:
            acts = det.request_probe(L_BLOCK)
            seq = list(acts) if acts is not None else [None]
            for a in seq:
                t += 1; prev = obs; a_ap, obs = env.step(a)
                _, _, al = det.update((prev, a_ap, obs.copy(), a is not None, t))
                if al: hit = t; break
        out.append(hit if hit is not None else cap)
    out = np.array(out, float); return dict(h=h, mean=out.mean(), se=out.std(ddof=1) / math.sqrt(len(out)), n=len(out), cens=int((out >= cap).sum()))


def arl_stream(args):
    """steady-state inter-alarm run lengths on one long null stream (includes blind windows, bursts, re-estimation)."""
    h, variant, mu, sig, g, seed, n_target, cap = args
    env = SCM(seed); det = fresh_detector(mu, sig, g, seed, variant, h)
    t = 0; obs = env.o.copy(); alarms = []; nplus = 0; total_epochs = 0
    while t < cap and len(alarms) < n_target + 1:
        acts = det.request_probe(L_BLOCK)
        seq = list(acts) if acts is not None else [None]
        for a in seq:
            t += 1; prev = obs; a_ap, obs = env.step(a)
            gp_before = det.Gp.max(); gn_before = det.Gn.max()
            _, _, al = det.update((prev, a_ap, obs.copy(), a is not None, t))
            if al:
                alarms.append(t); nplus += int(gp_before >= gn_before)
    rl = np.diff([0] + alarms) if alarms else np.array([cap], float)
    rl = np.array(rl, float)
    return dict(h=h, mean=rl.mean(), se=rl.std(ddof=1) / math.sqrt(len(rl)) if len(rl) > 1 else float("nan"), n=len(rl),
                med=float(np.median(rl)), min=float(rl.min()), steps=t, epochs=det.n_epochs, probe_frac=det.n_probe / t,
                frac_plus=nplus / max(1, len(alarms)), ref_sizes=(np.mean(det.ref_sizes) if det.ref_sizes else float("nan"),
                                                                  np.min(det.ref_sizes) if det.ref_sizes else float("nan")))


def confirm_run(args):
    h, variant, mu, sig, g, seed, T, ev, blind = args[:9]; do_event = args[9] if len(args) > 9 else True
    env = SCM(seed); det = fresh_detector(mu, sig, g, seed, variant, h, blind=blind)
    offs = {ev + o for o in (10, 50, 200)}
    r = run_stream(env, det, T, event_t=(ev if do_event else None), log_p_offsets=offs)
    post = [(dl - det.mu) / np.maximum(det.sig, SIG_FLOOR) for (tt, (_, dl)) in zip(det.epoch_t, det.dlog) if ev < tt <= ev + H_DET]
    zh_lost = np.mean([zz[:, 0] for zz in post], axis=0) if post else np.full(3, np.nan)      # per-h z on b0
    zmax_lost = float(np.mean([zz[:, 0].max() for zz in post])) if post else float("nan")
    n_post_epochs = len(post)
    counted = r["alarms"]                                  # detector applies p, r itself
    delays, outcomes, fa = match_alarms(counted, [ev], H_DET, T)
    pre_fa = sum(1 for a in counted if a <= ev)
    in_blind = any(a <= ev < b for (a, b) in det.blind_windows)
    blind_at_event_remaining = max([b - ev for (a, b) in det.blind_windows if a <= ev < b], default=0)
    res = dict(delay=delays[0], outcome=outcomes[0], pre_fa=pre_fa, in_blind=in_blind, blind_rem=blind_at_event_remaining,
               probe_steps=det.n_probe, probe_frac=det.n_probe / T, epochs=det.n_epochs, res_at_event=None,
               ref_sizes=det.ref_sizes, n_alarms=len(counted), first_alarm_after=(min([a for a in counted if a > ev], default=None)),
               zh_lost=zh_lost, zmax_lost=zmax_lost, n_post_epochs=n_post_epochs, stat_at_event=r["stat"][ev - 1] if ev - 1 < len(r["stat"]) else float("nan"))
    for name, idx in [("p_conf", CONF_X), ("p_unconf", UNCONF_X), ("p_lost", [0, 1, 4]), ("p_kept", [2, 3, 5])]:
        res[name] = {o: float(np.mean(r["p"][ev + o][idx])) if (ev + o) in r["p"] else float("nan") for o in (10, 50, 200)}
    return res


# ---- context-only comparator: per-step two-sided CUSUM on standardised innovations of a linear predictor (NOT the D-3a arm)
def fit_linear_predictor(seed, T=12000):
    env = SCM(seed); X, Y = [], []; obs = env.o.copy()
    for t in range(T):
        prev = obs; a, obs = env.step(None); X.append(np.concatenate([prev, a, [1.0]])); Y.append(obs)
    X = np.array(X); Y = np.array(Y); Th = np.linalg.lstsq(X, Y, rcond=None)[0]
    e = Y - X @ Th; return Th, e.std(0)


def cusum_lin_run(args):
    Th, sd, h, seed, T, ev = args
    env = SCM(seed); obs = env.o.copy(); Gp = np.zeros(C); Gn = np.zeros(C); raw = []
    for t in range(1, T + 1):
        if t - 1 == ev: env.lose_actuator(0)
        prev = obs; a, obs = env.step(None)
        e = (obs - np.concatenate([prev, a, [1.0]]) @ Th) / sd
        z = (np.abs(e) - 0.798) / 0.603                     # standardised |innovation| (E|N|=0.798, sd=0.603)
        Gp = np.maximum(0, Gp + z - K_SLACK); Gn = np.maximum(0, Gn - z - K_SLACK)
        raw.append(max(Gp.max(), Gn.max()) > h)
    counted = count_alarms(raw, P_PERSIST, R_REFRACT)
    counted = [c + 1 for c in counted]
    if ev is None: return counted, T
    delays, outcomes, fa = match_alarms(counted, [ev], H_DET, T)
    return delays[0], outcomes[0], sum(1 for a in counted if a <= ev)


def ci95(x):
    x = np.asarray(x, float); m = x.mean(); s = 1.96 * x.std(ddof=1) / math.sqrt(len(x)); return m, m - s, m + s


# ================================================================== main
def main():
    t0 = time.time(); np.set_printoptions(precision=3, suppress=True, linewidth=160)
    n_seeds = 40 if QUICK else 200
    n_rl_grid = 60 if QUICK else 200
    n_rl_verify = 120 if QUICK else 400
    cap_stream = 400_000 if QUICK else 900_000
    print(f"sim_ibd_review.py  quick={QUICK}  W_u(policy u-gain)={WU}  seeds={n_seeds}  run lengths: grid {n_rl_grid}, verify {n_rl_verify}  (reduced from the D-2a 400 where noted for runtime)")
    print("=" * 110)

    # ---- 0. SCM certification prints (contract B / section 0)
    env = SCM(1); A = []; Xs = []; obs = env.o.copy()
    for _ in range(20000):
        a, obs = env.step(None); A.append(a); Xs.append(env.x.copy())
    A = np.array(A); Xs = np.array(Xs)
    cc = np.array([[abs(np.corrcoef(A[:, k], Xs[:, j])[0, 1]) for j in range(N_X)] for k in range(K)])
    print(f"[SCM] saturation fraction {env.n_sat/env.n:.4f} (reject > 0.05); max |corr(a_k, x_j)| confounded = {cc[:, :5].max():.3f} (rho_min 0.4), "
          f"unconfounded = {cc[:, 5:].max():.3f}; sd(a) = {A.std(0).round(3)}; E|a| = {np.abs(A).mean(0).round(3)} vs probe |a| = 1.0")
    print(f"[SCM] rho(A_b) = {max(abs(np.linalg.eigvals(env.A_b))):.2f}; oracle S^obs before loss = channels {np.where(oracle_S(False))[0].tolist()}, after = {np.where(oracle_S(True))[0].tolist()}")
    # policy action autocorrelation (u leaks into multi-step increments)
    ac = [np.corrcoef(A[:-l, 0], A[l:, 0])[0, 1] for l in (1, 2, 3)]
    print(f"[SCM] policy-action autocorrelation at lags 1,2,3 = {np.round(ac, 3)} (probe actions are i.i.d.: 0)")

    # ---- 1. calibration split: reference, isotonic g, null statistics of the draft's z
    mu, sig, g, diag = make_calibrated(100, "DRAFT")
    arr = diag["deltas"]                                    # [n, 3, C]
    print(f"\n[calibration] {diag['n_pairs']} pairs from a fault-free 12k-step split (~{diag['n_pairs']/12:.1f} pairs / 1000 steps)")
    print(f"  reference median delta  h=1 body={mu[0, IDX_B]}  d={mu[0, IDX_D]}  conf-x={mu[0, CONF_X]}")
    print(f"  reference median delta  h=3 body={mu[2, IDX_B]}  d={mu[2, IDX_D]}  conf-x={mu[2, CONF_X]}")
    print(f"  reference MAD-sigma     h=1 body={sig[0, IDX_B]}  conf-x={sig[0, CONF_X]}  (floor 0.1 binds where sigma < 0.1)")
    print(f"  fraction of (h, c) with sigma < sigma_floor: {(sig < SIG_FLOOR).mean():.2f}")
    # contamination of the null arm by probe actions: mean delta on body ch 0 by (pair i, h)
    by_i = {i: np.array([d for (ii, d) in zip([x for x in range(len(arr))], arr)]) for i in range(3)}
    # recompute with pair index from a fresh detector log
    det_tmp = SeqIBD(100, "DRAFT"); det_tmp.set_threshold(math.inf); env_tmp = SCM(100); run_stream(env_tmp, det_tmp, 12000)
    tab = np.zeros((3, 3))
    for i in range(3):
        sel = np.array([d for (ii, d) in det_tmp.dlog if ii == i])
        for j in range(3): tab[i, j] = sel[:, j, 0].mean()
    print(f"  mean delta on body channel 0 by pair i (rows 0..2) x horizon h (cols 1..3):\n{tab}")
    print(f"  -> null start t_b-3+i with h reaches o(t_b-3+i+h): for (i=1,h=3),(i=2,h>=2) the 'null' increment ends INSIDE the probe block (tau=0)")
    # null bias of z = max_h z_h
    zs = (arr - mu) / np.maximum(sig, SIG_FLOOR); zmax = zs.max(1); zabs_signed = np.take_along_axis(zs, np.abs(zs).argmax(1)[:, None, :], 1)[:, 0, :]
    print(f"  null mean of z = max_h z_h  : body={zmax[:, IDX_B].mean(0)}  conf-x={zmax[:, CONF_X].mean():.3f}  pad={zmax[:, -4:].mean():.3f}  (k = 0.5)")
    print(f"  null mean of per-h z_h      : {zs.mean((0, 2)).round(3)} (median-centred, so ~0 by construction)")
    print(f"  E[max_h z - k] > 0 on {((zmax.mean(0) - K_SLACK) > 0).sum()}/{C} channels -> G+ has POSITIVE drift under the null; G- drift = {(-zmax.mean() - K_SLACK):.3f}")
    print(f"  attainable |signed-rank z| at W=16: max = {signed_rank_z(np.arange(1, 17.)):.2f}; window turnover = W/L blocks = {W_REPORT/L_BLOCK:.1f} blocks = {W_REPORT/L_BLOCK*PI_NORMAL:.0f} steps at Pi=75")
    print(f"  isotonic g: knots={g.knots.round(2)} vals={g.vals.round(3)}; mean s_c on body={diag['s_body']:.2f}, on x={diag['s_x']:.2f} (labels constant per channel on a fault-free split)")

    with Pool(min(10, os.cpu_count() or 2)) as pool:
        results = {}
        for variant in (["DRAFT"] if QUICK else ["DRAFT", "ABSMAX"]):
            if variant != "DRAFT": mu, sig, g, diag = make_calibrated(100, variant)
            print(f"\n{'-'*110}\n[variant={variant}]")
            hs = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
            # 1a fresh-start first-alarm ARL (monotone by construction)
            rf = pool.map(arl_fresh, [(h, variant, mu, sig, g, 7 + i, n_rl_grid, 20000) for i, h in enumerate(hs)])
            # 1b steady-state inter-alarm ARL
            rs = pool.map(arl_stream, [(h, variant, mu, sig, g, 31 + i, n_rl_grid, cap_stream) for i, h in enumerate(hs)])
            print(f"  ARL_0(h): fresh-start-to-first-alarm vs steady-state inter-alarm (mean +/- 1.96 se; n; med; min; alarms from G+; ref pairs mean/min)")
            for a, b in zip(rf, rs):
                print(f"   h={a['h']:4.1f}  fresh={a['mean']:7.1f}+/-{1.96*a['se']:5.1f} (n={a['n']},cens={a['cens']})   "
                      f"stream={b['mean']:7.1f}+/-{1.96*b['se']:5.1f} (n={b['n']}) med={b['med']:6.0f} min={b['min']:4.0f}  G+ share={b['frac_plus']:.2f}  "
                      f"epochs/1k={1000*b['epochs']/b['steps']:.1f} probe={b['probe_frac']:.4f} ref={b['ref_sizes'][0]:.0f}/{b['ref_sizes'][1]:.0f}")
            m_f = [r["mean"] for r in rf]; m_s = [r["mean"] for r in rs]
            print(f"  monotone (fresh): {all(m_f[i] <= m_f[i+1] for i in range(len(m_f)-1))};  monotone (stream, point estimates): {all(m_s[i] <= m_s[i+1] for i in range(len(m_s)-1))}; "
                  f"within 2se: {all(m_s[i] <= m_s[i+1] + 2*(rs[i]['se']+rs[i+1]['se']) for i in range(len(m_s)-1))}")
            print(f"  mechanical floor of stream run length = r + n_ref = {R_REFRACT + N_REF} steps (blind); min observed stream RL above = {min(b['min'] for b in rs):.0f}")
            # h* for ARL_0 = 1000 (stream definition), log-linear interpolation + verification at n_rl_verify
            pts = [(r["h"], r["mean"]) for r in rs if not math.isnan(r["mean"])]
            hstar = pts[-1][0]
            for (h1, m1), (h2, m2) in zip(pts, pts[1:]):
                if m1 <= 1000 <= m2: hstar = h1 + (h2 - h1) * (math.log(1000) - math.log(m1)) / (math.log(m2) - math.log(m1)); break
            for it in range(3):
                vs = pool.map(arl_stream, [(hstar, variant, mu, sig, g, 500 + j, n_rl_verify // 4 + 1, cap_stream) for j in range(4)])
                # pool the four streams' run lengths
                n = sum(v["n"] for v in vs); mean = sum(v["mean"] * v["n"] for v in vs) / n
                se = math.sqrt(sum((v["se"] ** 2) * v["n"] ** 2 for v in vs if not math.isnan(v["se"]))) / n
                lo, hi = mean - 1.96 * se, mean + 1.96 * se
                print(f"  verify h*={hstar:.3f}: stream ARL_0 = {mean:.1f} [{lo:.1f}, {hi:.1f}] (n={n})  band [900,1100] {'MET' if lo >= 900 and hi <= 1100 else 'NOT met'};  "
                      f"steps used = {sum(v['steps'] for v in vs):,} (D-2a cap 2,000,000 per cell; this is ONE h value)")
                if abs(mean - 1000) < 30: break
                hstar *= (1000 / mean) ** 0.7
            vf = arl_fresh((hstar, variant, mu, sig, g, 999, n_rl_grid, 20000))
            print(f"  at that h*, fresh-start first-alarm ARL = {vf['mean']:.1f} +/- {1.96*vf['se']:.1f}  (differs from stream ARL by the blind/burst/re-estimation dynamics)")
            results[(variant, "h")] = hstar

            # 2. confirmation runs
            for T, ev in [(2000, 1000), (20000, 10000)]:
                rr = pool.map(confirm_run, [(hstar, variant, mu, sig, g, 1000 + s, T, ev, True) for s in range(n_seeds)])
                d = [r["delay"] for r in rr]; oc = [r["outcome"] for r in rr]; det_d = [r["delay"] for r in rr if r["outcome"] == "detected"]
                Hp = hpdt(d, oc, H_DET); m, lo, hi = ci95([min(x, H_DET) if o == "detected" else H_DET for x, o in zip(d, oc)])
                ps = [r["probe_steps"] for r in rr]; pf = [r["probe_frac"] for r in rr]
                print(f"\n  [T={T}, event={ev}] n={n_seeds}: HPDT = {Hp:.1f} [{lo:.1f}, {hi:.1f}]   P(detect within H_det) = {np.mean([o=='detected' for o in oc]):.2f}")
                rn = pool.map(confirm_run, [(hstar, variant, mu, sig, g, 1000 + s, T, ev, True, False) for s in range(n_seeds)])
                p_null = np.mean([r["outcome"] == "detected" for r in rn])
                print(f"     NULL CONTROL (same seeds, no event): P(alarm inside (event_t, event_t+200]) = {p_null:.2f}  <- detection floor to compare with the line above")
                print(f"     post-event epochs within H_det: mean {np.mean([r['n_post_epochs'] for r in rr]):.1f}; mean per-h z on lost channel b0 = {np.nanmean([r['zh_lost'] for r in rr], axis=0).round(2)}; "
                      f"mean max_h z = {np.nanmean([r['zmax_lost'] for r in rr]):+.2f} (null ~{zmax[:, 0].mean():+.2f}); mean S at event = {np.nanmean([r['stat_at_event'] for r in rr]):.1f} of h* = {hstar:.1f}")
                if det_d: print(f"     delay | detected: mean {np.mean(det_d):.1f}, median {np.median(det_d):.0f}, p10 {np.percentile(det_d, 10):.0f}, p90 {np.percentile(det_d, 90):.0f}, min {min(det_d)}")
                fa_after = [r["first_alarm_after"] - ev for r in rr if r["first_alarm_after"] is not None]
                print(f"     first alarm after event (any delay): exists in {len(fa_after)/n_seeds:.2f} of runs; median delay {np.median(fa_after) if fa_after else float('nan'):.0f}")
                print(f"     probe steps/run: mean {np.mean(ps):.1f}, max {max(ps)}; fraction mean {np.mean(pf):.4f}, max {max(pf):.4f} (cap 0.05); epochs/run {np.mean([r['epochs'] for r in rr]):.0f}; alarms/run {np.mean([r['n_alarms'] for r in rr]):.2f}")
                print(f"     pre-event false alarms: mean {np.mean([r['pre_fa'] for r in rr]):.2f}/run, P(>=1) = {np.mean([r['pre_fa']>0 for r in rr]):.2f}; "
                      f"P(event falls inside a blind window) = {np.mean([r['in_blind'] for r in rr]):.2f}, mean remaining blind at event | inside = "
                      f"{np.mean([r['blind_rem'] for r in rr if r['in_blind']]) if any(r['in_blind'] for r in rr) else 0:.0f} steps")
                rsz = [x for r in rr for x in r["ref_sizes"]]
                if rsz: print(f"     post-alarm reference re-estimations: {len(rsz)}, pairs per re-estimation mean {np.mean(rsz):.1f}, min {min(rsz)} (calibration used {diag['n_pairs']})")
                for key, name in [("p_conf", "confounded x"), ("p_unconf", "unconfounded x"), ("p_lost", "lost {b0,b1,d0}"), ("p_kept", "kept {b2,b3,d1}")]:
                    print(f"     mean p_c {name:16s}: " + "   ".join(f"off {o}: {np.nanmean([r[key][o] for r in rr]):.3f}" for o in (10, 50, 200)))
                results[(variant, T)] = dict(hpdt=Hp, ci=(lo, hi), pdet=float(np.mean([o == 'detected' for o in oc])), pre_fa=float(np.mean([r['pre_fa'] for r in rr])),
                                             in_blind=float(np.mean([r['in_blind'] for r in rr])), probe_max=max(pf))

            # 3. p_c freezing during the blind window: PROSE variant (p_c updated) vs DRAFT pseudo-code, T=2000 only
            if variant == "DRAFT":
                rr2 = pool.map(confirm_run, [(hstar, "PROSE", mu, sig, g, 1000 + s, 2000, 1000, True) for s in range(n_seeds)])
                print(f"\n  [pseudo-code vs prose] p_c updated during the 200-step blind window (PROSE) vs frozen (DRAFT pseudo-code), T=2000:")
                for key in ("p_lost", "p_conf"):
                    print(f"     {key:7s} off200: DRAFT {np.nanmean([r[key][200] for r in rr]):.3f}  PROSE {np.nanmean([r[key][200] for r in rr2]):.3f}")
                # 4. no-blind variant for attribution: what does the 200-step blind window cost in HPDT?
                rr3 = pool.map(confirm_run, [(hstar, "DRAFT", mu, sig, g, 1000 + s, 2000, 1000, False) for s in range(n_seeds)])
                Hp3 = hpdt([r["delay"] for r in rr3], [r["outcome"] for r in rr3], H_DET)
                print(f"  [attribution] same h*, blind window disabled (reference never re-estimated): HPDT = {Hp3:.1f}, P(detect) = {np.mean([r['outcome']=='detected' for r in rr3]):.2f} "
                      f"(vs {results[(variant, 2000)]['hpdt']:.1f} / {results[(variant, 2000)]['pdet']:.2f} with the blind window; ARL_0 differs, so this is attribution only)")

        # 5. reservoir initial condition (section 2 'hard cap' claim)
        mu, sig, g, diag = make_calibrated(100, "DRAFT")
        env = SCM(5); det = fresh_detector(mu, sig, g, 5, "DRAFT", results[("DRAFT", "h")], reservoir0=B_MAX)
        run_stream(env, det, 2000, 1000)
        print(f"\n[reservoir_0 = B_max = 30, unspecified in the draft] 2000-step run: probe steps = {det.n_probe} -> fraction {det.n_probe/2000:.4f} "
              f"({'VIOLATES' if det.n_probe/2000 > PROBE_BUDGET else 'within'} the 0.05 cap); alarms at {det.alarms}")
        env = SCM(5); det = fresh_detector(mu, sig, g, 5, "DRAFT", results[("DRAFT", "h")], reservoir0=0.0)
        run_stream(env, det, 2000, 1000)
        print(f"[reservoir_0 = 0] same run: probe steps = {det.n_probe} -> fraction {det.n_probe/2000:.4f}; reservoir at t=1000 would be ~{min(B_MAX, 1000*(PROBE_BUDGET - L_BLOCK/PI_NORMAL)):.0f} tokens -> burst can fund ~{int(min(B_MAX, 1000*(PROBE_BUDGET - L_BLOCK/PI_NORMAL))//3)} blocks, not {int(B_MAX//3)}")

        # 6. context-only comparator scale: per-step innovation CUSUM (not the D-3a arm)
        Th, sd = fit_linear_predictor(100)
        # calibrate its h to ARL ~1000 steps on null streams (coarse)
        for hc in (6, 8, 10, 12, 14, 16, 20, 24):
            nulls = pool.map(cusum_lin_run, [(Th, sd, hc, 5000 + j, 60000, None) for j in range(4)])
            n_al = sum(len(c) for c, T in nulls); arl = sum(T for c, T in nulls) / max(1, n_al)
            if arl >= 1000: break
        rr = pool.map(cusum_lin_run, [(Th, sd, hc, 1000 + s, 2000, 1000) for s in range(n_seeds)])
        dl = [r[0] for r in rr]; oc = [r[1] for r in rr]
        print(f"\n[context only] per-step innovation CUSUM (linear predictor fitted on the same split), h={hc}, null ARL ~{arl:.0f} steps: "
              f"HPDT = {hpdt(dl, oc, H_DET):.1f}, P(detect) = {np.mean([o=='detected' for o in oc]):.2f}, median delay {np.median([d for d,o in zip(dl,oc) if o=='detected']) if any(o=='detected' for o in oc) else float('nan'):.0f}, "
              f"pre-event FA/run {np.mean([r[2] for r in rr]):.2f}.  Its statistic updates every step; the IBD arm's ~40 times per 1000 steps.")

    print(f"\nTotal wall time {time.time()-t0:.0f} s")
    print("SUMMARY", json.dumps({str(k): v for k, v in results.items()}, default=float, indent=1))


if __name__ == "__main__":
    main()
