"""
sim_ibd.py -- executable red-team check of sequential-ibd-spec.md (draft 1, 6 Sep 2026).

Implements (i) a toy family-L SCM per stage-0a-contract-v3.2 section B with registry constants,
(ii) the draft detector as written (sections 2-4, 9 pseudo-code), faithfully enough to measure
probe spend, ARL_0(h), detection delay / HPDT, blind-window overlap and the co-primary,
(iii) two mutants used only for attribution: NOBLIND (n_ref = 0) and PERH (a CUSUM per (channel,
horizon) instead of max-over-horizons feeding one CUSUM).

Usage:  python3 sim_ibd.py [--quick]      (pure numpy; ~5-10 min on 10 cores at full settings)
Nothing outside this folder is written. contract_ref.match_alarms is used for alarm matching.
"""
import sys, os, time, math, json
import numpy as np
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "executable-proofs", "gate"))
from contract_ref import match_alarms, count_alarms, hpdt  # noqa: E402

QUICK = "--quick" in sys.argv

# ----------------------------------------------------------------------------- registry (contract v3.2 section 0)
EPS, HSUP, HSET = 0.05, 3, (1, 2, 3)
RHO_U, A_MAX, SIG = 0.8, 2.0, dict(b=0.1, d=0.1, w=0.1, x=0.1, o=0.05, a=0.1, u=1.0)
P_PERSIST, R_REFRACT, H_DET, PROBE_BUDGET, F_CONF = 3, 20, 200, 0.05, 0.5
N_B, N_D, N_W, N_X, K = 4, 2, 4, 10, 2
N_PAD = 4
C = N_B + N_D + N_W + N_X + N_PAD            # 24, matches confirmation-design.csv n_channels at level 10

# ----------------------------------------------------------------------------- draft's frozen/provisional knobs (section 8)
L_BLOCK, PI_NORMAL, PI_BURST, BURST_LEN = 3, 75, 6, 100
B_MAX, ETA = 30.0, 0.8
K_SLACK, SIG_FLOOR, N_REF, W_REPORT = 0.5, 0.1, 200, 16


# ============================================================================= family-L SCM (contract B)
class SCM:
    """z = [b; d; w; x]; o = Assign z + eps_o with 4 padding channels. Actuator 0 loss at event_t (column 0 of B -> 0).
    Blocks: actuator 0 -> b0 (h=1) -> b1 (h=2) -> d0 (h=2); actuator 1 -> b2 -> b3, d1. No cross path (CL-4)."""
    def __init__(self, seed, tau=0, confounder=True):
        self.rng = np.random.default_rng(seed)
        self.tau = tau
        self.A_b = np.array([[0.7, 0.2, 0, 0], [0.2, 0.7, 0, 0], [0, 0, 0.7, 0.2], [0, 0, 0.2, 0.7]])
        self.B0 = np.array([[1.0, 0], [0, 0], [0, 1.0], [0, 0]])
        self.B = self.B0.copy()
        self.C_d = np.array([[0.5, 0, 0, 0], [0, 0, 0.5, 0]]); self.A_d = 0.8 * np.eye(N_D)
        self.A_w = 0.8 * np.eye(N_W); self.A_x = 0.8 * np.eye(N_X)
        self.G = np.zeros(N_X); self.G[: int(F_CONF * N_X)] = 1.0 if confounder else 0.0
        # policy: linear feedback on observed body channels + private cue u (W_u unchanged when confounder absent)
        self.W_o = np.zeros((K, C)); self.W_o[0, 0] = -0.3; self.W_o[0, 1] = -0.1; self.W_o[1, 2] = -0.3; self.W_o[1, 3] = -0.1
        self.W_u = np.array([0.5, 0.5])
        self.b = np.zeros(N_B); self.d = np.zeros(N_D); self.w = np.zeros(N_W); self.x = np.zeros(N_X); self.u = 0.0
        self.aq = [np.zeros(K) for _ in range(tau + 1)]   # action queue for delay
        self.o = self.observe(); self.sat = 0; self.n = 0
        for _ in range(500): self.step(None)              # burn-in (short; stationary quickly)
        self.sat = 0; self.n = 0

    def observe(self):
        z = np.concatenate([self.b, self.d, self.w, self.x, np.zeros(N_PAD)])
        return z + SIG["o"] * self.rng.standard_normal(C)

    def policy(self):
        a = self.W_o @ self.o + self.W_u * self.u + SIG["a"] * self.rng.standard_normal(K)
        return a

    def step(self, a_override):
        a = self.policy() if a_override is None else np.asarray(a_override, float)
        a = np.clip(a, -A_MAX, A_MAX); self.sat += int(np.any(np.abs(a) >= A_MAX)); self.n += 1
        self.aq.append(a); a_eff = self.aq.pop(0)
        r = self.rng
        b_new = self.A_b @ self.b + self.B @ a_eff + SIG["b"] * r.standard_normal(N_B)
        d_new = self.A_d @ self.d + self.C_d @ self.b + SIG["d"] * r.standard_normal(N_D)
        w_new = self.A_w @ self.w + SIG["w"] * r.standard_normal(N_W)
        x_new = self.A_x @ self.x + self.G * self.u + SIG["x"] * r.standard_normal(N_X)
        self.u = RHO_U * self.u + SIG["u"] * r.standard_normal()
        self.b, self.d, self.w, self.x = b_new, d_new, w_new, x_new
        self.o = self.observe()
        return a, self.o

    def lose_actuator(self, k=0):
        self.B = self.B0.copy(); self.B[:, k] = 0.0


# oracle labels: S^obs,eps before / after loss of actuator 0 (H = 3, tau = 0 or 2 -> first hit tau+1; at tau=2 only h=3 exists)
def oracle_S(tau, lost):
    s = np.zeros(C, bool)
    if tau == 0:
        reach = {0, 1, 2, 3, 4, 5} if not lost else {2, 3, 5}
    else:  # tau = 2: only h = 3 = tau+1 reaches b0, b2 directly
        reach = {0, 2} if not lost else {2}
    for c in reach: s[c] = True
    return s
CONF_X = list(range(N_B + N_D + N_W, N_B + N_D + N_W + int(F_CONF * N_X)))       # channels 10..14
UNCONF_X = list(range(N_B + N_D + N_W + int(F_CONF * N_X), N_B + N_D + N_W + N_X))  # 15..19


# ============================================================================= isotonic calibrator (PAVA)
class Isotonic:
    def fit(self, s, y):
        s = np.asarray(s, float); y = np.asarray(y, float)
        o = np.argsort(s, kind="stable"); s, y = s[o], y[o]
        # PAVA
        vals, wts, lo = [], [], []
        for i in range(len(y)):
            vals.append(y[i]); wts.append(1.0); lo.append(i)
            while len(vals) > 1 and vals[-2] > vals[-1]:
                v = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / (wts[-2] + wts[-1])
                w = wts[-2] + wts[-1]; l = lo[-2]
                vals.pop(); wts.pop(); lo.pop(); vals[-1] = v; wts[-1] = w; lo[-1] = l
        self.knots = np.array([s[l] for l in lo]); self.vals = np.array(vals); return self
    def __call__(self, s):
        idx = np.searchsorted(self.knots, s, side="right") - 1
        return self.vals[np.clip(idx, 0, len(self.vals) - 1)]


def signed_rank_z(dv):
    dv = dv[dv != 0]; n = len(dv)
    if n == 0: return -4.0                         # "absent extreme" (draft section 3)
    ranks = np.argsort(np.argsort(np.abs(dv))) + 1.0
    wp = ranks[dv > 0].sum(); e = n * (n + 1) / 4; v = n * (n + 1) * (2 * n + 1) / 24
    return (wp - e) / math.sqrt(v)


# ============================================================================= the draft detector (sections 2-4, 9)
class SeqIBD:
    def __init__(self, rng, variant="DRAFT", reservoir0=0.0):
        self.rng = rng; self.variant = variant
        self.h = math.inf; self.t = 0; self.reservoir = reservoir0; self.mode = "NORMAL"; self.last_block_t = -10**9
        self.burst_start = -10**9; self.blocks = []; self.obs = {}
        self.mu = np.zeros((len(HSET), C)); self.sig = np.ones((len(HSET), C))
        self.Gp = np.zeros(C); self.Gn = np.zeros(C)
        self.Gp_h = np.zeros((len(HSET), C)); self.Gn_h = np.zeros((len(HSET), C))
        self.raise_run = 0; self.refract = 0; self.ref_until = -1; self.ref_pairs = []
        self.win = [[[] for _ in range(C)] for _ in HSET]   # W-window of deltas per (h, c)
        self.p_cache = np.full(C, 0.5); self.g = None; self.calib = None
        self.n_probe = 0; self.n_epochs = 0; self.alarms = []; self.blind = []; self.ref_sizes = []
        self.zlog = []; self.epoch_times = []

    # ---- interface v3
    def set_threshold(self, h): self.h = h
    def request_probe(self, steps=L_BLOCK):
        if self.mode == "BURST" and (self.reservoir < L_BLOCK or self.t - self.burst_start >= BURST_LEN): self.mode = "NORMAL"
        period = PI_BURST if self.mode == "BURST" else PI_NORMAL
        if self.reservoir < L_BLOCK or (self.t - self.last_block_t) < period or self.t < L_BLOCK: return None
        n = min(steps, L_BLOCK); self.reservoir -= n; self.last_block_t = self.t; self.blocks.append(self.t)
        acts = np.zeros((n, K)); idx = self.rng.integers(0, 2 * K, size=n)
        for i, j in enumerate(idx): acts[i, j // 2] = 1.0 if j % 2 == 0 else -1.0
        return acts

    def update(self, obs_next, probe_flag):
        self.t += 1; self.reservoir = min(B_MAX, self.reservoir + PROBE_BUDGET); self.n_probe += int(probe_flag)
        self.obs[self.t] = obs_next
        for k in [k for k in self.obs if k < self.t - 12]: del self.obs[k]
        in_ref = self.t <= self.ref_until
        for tb in list(self.blocks):
            for i in range(L_BLOCK):
                if self.t != tb + i + HSUP: continue
                z = np.full(C, -np.inf); zh = np.zeros((len(HSET), C)); delta_h = []
                for hi, hz in enumerate(HSET):
                    ip, inn = tb + i, tb - L_BLOCK + i
                    d_p = np.abs(self.obs[ip + hz] - self.obs[ip]); d_n = np.abs(self.obs[inn + hz] - self.obs[inn])
                    delta = d_p - d_n; delta_h.append(delta)
                    for c in range(C):
                        w = self.win[hi][c]; w.append(delta[c]);
                        if len(w) > W_REPORT: w.pop(0)
                    zh[hi] = (delta - self.mu[hi]) / np.maximum(self.sig[hi], SIG_FLOOR)
                    z = np.maximum(z, zh[hi])
                if self.calib is not None: self.calib.append((np.array(delta_h), self.t))
                if in_ref: self.ref_pairs.append(np.array(delta_h))
                else:
                    self.n_epochs += 1; self.zlog.append(z.copy()); self.epoch_times.append(self.t)
                    if self.variant == "PERH":
                        self.Gp_h = np.maximum(0, self.Gp_h + zh - K_SLACK); self.Gn_h = np.maximum(0, self.Gn_h - zh - K_SLACK)
                    else:
                        self.Gp = np.maximum(0, self.Gp + z - K_SLACK); self.Gn = np.maximum(0, self.Gn - z - K_SLACK)
                # reporting p_c at the argmax horizon of the latest z
                if self.g is not None:
                    arg = np.argmax(zh, axis=0)
                    s = np.array([signed_rank_z(np.array(self.win[arg[c]][c])) for c in range(C)])
                    self.p_cache = np.clip(self.g(s), 0, 1)
            if self.t >= tb + L_BLOCK + HSUP: self.blocks.remove(tb)
        if self.t == self.ref_until and self.ref_pairs:   # end of re-estimation window
            arr = np.array(self.ref_pairs); self.ref_sizes.append(len(arr))
            self.mu = np.median(arr, axis=0); self.sig = 1.4826 * np.median(np.abs(arr - self.mu), axis=0)
            self.ref_pairs = []
        if self.variant == "PERH": S = max(self.Gp_h.max(), self.Gn_h.max())
        else: S = max(self.Gp.max(), self.Gn.max())
        alarm = 0
        self.raise_run = self.raise_run + 1 if S > self.h else 0
        if self.refract > 0: self.refract -= 1
        elif self.raise_run >= P_PERSIST:
            alarm = 1; self.refract = R_REFRACT; self.raise_run = 0; self.alarms.append(self.t)
            self.Gp[:] = 0; self.Gn[:] = 0; self.Gp_h[:] = 0; self.Gn_h[:] = 0
            self.mode = "BURST"; self.burst_start = self.t
            if self.variant != "NOBLIND":
                self.ref_until = self.t + N_REF; self.ref_pairs = []; self.blind.append((self.t, self.t + N_REF))
        return self.p_cache, S, alarm

    def set_reference_from(self, pairs):
        arr = np.array(pairs); self.mu = np.median(arr, axis=0); self.sig = 1.4826 * np.median(np.abs(arr - self.mu), axis=0)


# ============================================================================= harness loop
def run_stream(env, det, T, event_t=None, record=None):
    """Drive env + detector for T steps; probe blocks override the policy for L_BLOCK steps."""
    pending = []
    for t in range(T):
        if event_t is not None and t == event_t: env.lose_actuator(0)
        if not pending:
            acts = det.request_probe(L_BLOCK)
            if acts is not None: pending = list(acts)
        if pending: a_over = pending.pop(0); flag = True
        else: a_over = None; flag = False
        _, o = env.step(a_over)
        p, S, alarm = det.update(o, flag)
        if record is not None: record(t + 1, p, S, alarm)
    return det


def make_calibrated(seed, variant, tau, confounder=True, calib_steps=20000):
    """Fit reference (mu, sigma) and isotonic g on a fault-free calibration split; returns (env_rng, ref, g)."""
    env = SCM(seed, tau, confounder); det = SeqIBD(np.random.default_rng(seed + 7), variant); det.calib = []
    run_stream(env, det, calib_steps)
    pairs = [d for d, _ in det.calib]; det.set_reference_from(pairs)
    # second pass over the same deltas to produce s_c samples for the isotonic map
    det2 = SeqIBD(np.random.default_rng(seed + 11), variant); det2.mu, det2.sig = det.mu, det.sig; det2.calib = []
    env2 = SCM(seed + 1, tau, confounder); run_stream(env2, det2, calib_steps)
    lab = oracle_S(tau, lost=False); s_all, y_all = [], []
    win = [[[] for _ in range(C)] for _ in HSET]
    for d, _ in det2.calib:
        zh = (d - det2.mu) / np.maximum(det2.sig, SIG_FLOOR); arg = np.argmax(zh, axis=0)
        for hi in range(len(HSET)):
            for c in range(C):
                win[hi][c].append(d[hi][c]); win[hi][c] = win[hi][c][-W_REPORT:]
        if len(win[0][0]) >= W_REPORT:
            s = [signed_rank_z(np.array(win[arg[c]][c])) for c in range(C)]
            s_all.extend(s); y_all.extend(lab.astype(float))
    g = Isotonic().fit(s_all, y_all)
    return det.mu, det.sig, g, np.array(s_all).reshape(-1, C)


def null_run_lengths(args):
    """ARL_0 measurement: long fault-free stream, run lengths between counted alarms, until n_target alarms or cap."""
    h, variant, tau, mu, sig, seed, n_target, cap = args
    env = SCM(seed, tau); det = SeqIBD(np.random.default_rng(seed + 3), variant); det.mu, det.sig = mu.copy(), sig.copy(); det.set_threshold(h)
    pending = []; t = 0
    while t < cap and len(det.alarms) < n_target:
        if not pending:
            acts = det.request_probe(L_BLOCK)
            if acts is not None: pending = list(acts)
        a_over = pending.pop(0) if pending else None; flag = a_over is not None
        _, o = env.step(a_over); det.update(o, flag); t += 1
    al = np.array(det.alarms)
    rl = np.diff(np.concatenate([[0], al])) if len(al) else np.array([])
    zl = np.array(det.zlog)
    return dict(h=h, variant=variant, n=len(rl), steps=t, mean=float(rl.mean()) if len(rl) else float("nan"),
                se=float(rl.std(ddof=1) / math.sqrt(len(rl))) if len(rl) > 1 else float("nan"),
                med=float(np.median(rl)) if len(rl) else float("nan"), min=float(rl.min()) if len(rl) else float("nan"),
                epochs=det.n_epochs, probe_frac=det.n_probe / t,
                ref_sizes=(float(np.mean(det.ref_sizes)) if det.ref_sizes else float("nan"), float(np.min(det.ref_sizes)) if det.ref_sizes else float("nan")),
                mean_z_body=float(zl[:, :N_B].mean()) if len(zl) else float("nan"),
                mean_z_x=float(zl[:, CONF_X].mean()) if len(zl) else float("nan"),
                sat=env.sat / env.n)


def confirm_run(args):
    h, variant, tau, mu, sig, g, seed, T, event_t = args
    env = SCM(seed, tau); det = SeqIBD(np.random.default_rng(seed + 3), variant); det.mu, det.sig = mu.copy(), sig.copy(); det.g = g; det.set_threshold(h)
    offs = (10, 50, 200); snaps = {}
    def rec(t, p, S, alarm):
        for o_ in offs:
            if t == event_t + o_: snaps[o_] = p.copy()
    run_stream(env, det, T, event_t, rec)
    delays, outcomes, fa = match_alarms(det.alarms, [event_t], H_DET, T)
    pre_fa = sum(1 for a in det.alarms if a <= event_t)
    in_blind = any(a < event_t <= b for a, b in det.blind)
    blind_frac = sum(min(b, T) - a for a, b in det.blind) / T
    lost = [0, 1, 4]; kept = [2, 3, 5]
    return dict(seed=seed, delay=delays[0], outcome=outcomes[0], pre_fa=pre_fa, n_alarms=len(det.alarms), in_blind=in_blind,
                blind_frac=blind_frac, probe_steps=det.n_probe, probe_frac=det.n_probe / T, epochs=det.n_epochs,
                p_conf={o_: float(snaps[o_][CONF_X].mean()) for o_ in offs}, p_unconf={o_: float(snaps[o_][UNCONF_X].mean()) for o_ in offs},
                p_lost={o_: float(snaps[o_][lost].mean()) for o_ in offs}, p_kept={o_: float(snaps[o_][kept].mean()) for o_ in offs},
                ref_sizes=det.ref_sizes, sat=env.sat / env.n)


def ci95(x):
    x = np.asarray(x, float); m = x.mean(); se = x.std(ddof=1) / math.sqrt(len(x)) if len(x) > 1 else float("nan")
    return m, m - 1.96 * se, m + 1.96 * se


# ============================================================================= main
def main():
    t0 = time.time(); pool = Pool(min(10, os.cpu_count() or 2))
    n_target, cap = (150, 250_000) if QUICK else (400, 700_000)
    n_seeds = 60 if QUICK else 200
    print("=" * 100); print("sim_ibd.py  --  C =", C, " QUICK =", QUICK); print("=" * 100)

    # ---- E2c sanity: confounding present under policy, severed under probes
    env = SCM(0); A, X = [], []
    for _ in range(20000):
        a, o = env.step(None); A.append(a); X.append(env.x.copy())
    A, X = np.array(A), np.array(X)
    cc = max(abs(np.corrcoef(A[:, k], X[:, j])[0, 1]) for k in range(K) for j in range(N_X))
    print(f"[SCM] max |corr(a_k, x_j)| under policy = {cc:.2f} (contract rho_min = 0.4); saturation fraction = {env.sat/env.n:.3f} (must be < 0.05)")

    results = {}
    for tau in ([0] if QUICK else [0, 2]):
        for variant in ["DRAFT", "NOBLIND", "PERH"]:
            if tau == 2 and variant != "DRAFT": continue
            mu, sig, g, s_cal = make_calibrated(100 + tau, variant, tau)
            print(f"\n{'-'*100}\n[tau={tau} variant={variant}] reference from calibration split: "
                  f"mu(h=1) body={mu[0,:N_B].round(2)} x={mu[0,CONF_X].round(2)}; sigma(h=1) body={sig[0,:N_B].round(2)} x={sig[0,CONF_X].round(2)}")
            print(f"    isotonic g knots={g.knots.round(2)} vals={g.vals.round(3)}  (fitted on a fault-free split: labels constant per channel)")
            print(f"    calibration-split s_c: body mean={s_cal[:, :N_B].mean():.2f}, x mean={s_cal[:, CONF_X].mean():.2f}, max attainable |z| at W=16 = {signed_rank_z(np.arange(1,17.)):.2f}")

            # ---- ARL_0(h) curve on a null stream
            hs = [0.5, 1, 2, 3, 4, 6, 8, 12, 16, 24] if not QUICK else [0.5, 1, 2, 4, 8, 16]
            res = pool.map(null_run_lengths, [(h, variant, tau, mu, sig, 500 + i, n_target, cap) for i, h in enumerate(hs)])
            print(f"    ARL_0 on null stream (n run lengths, mean +/- 1.96 se, median, min, epochs/1000 steps, probe frac, mean z body/x, ref n pairs mean/min):")
            for r in res:
                print(f"      h={r['h']:5.1f}  n={r['n']:3d}  ARL={r['mean']:8.1f} +/- {1.96*r['se']:6.1f}  med={r['med']:7.1f} min={r['min']:6.0f}  "
                      f"epochs/1k={1000*r['epochs']/r['steps']:5.1f}  probe={r['probe_frac']:.4f}  z_body={r['mean_z_body']:+.2f} z_x={r['mean_z_x']:+.2f}  ref={r['ref_sizes'][0]:.0f}/{r['ref_sizes'][1]:.0f}")
            # monotonicity check
            means = [r["mean"] for r in res]; mono = all(means[i] <= means[i + 1] + 2 * (res[i]["se"] + res[i + 1]["se"]) for i in range(len(means) - 1))
            print(f"    monotone in h within 2 se: {mono}")
            # pick h for ARL_0 = 1000 by log-linear interpolation, then verify
            hs_ok = [(r["h"], r["mean"]) for r in res if not math.isnan(r["mean"])]
            hstar = None
            for (h1, m1), (h2, m2) in zip(hs_ok, hs_ok[1:]):
                if m1 <= 1000 <= m2: hstar = h1 + (h2 - h1) * (math.log(1000) - math.log(m1)) / (math.log(m2) - math.log(m1)); break
            if hstar is None: hstar = hs_ok[-1][0]
            for _ in range(2):  # two secant refinements
                v = null_run_lengths((hstar, variant, tau, mu, sig, 900, n_target, cap))
                print(f"    verify h*={hstar:.3f}: ARL_0 = {v['mean']:.1f} +/- {1.96*v['se']:.1f} (n={v['n']}, band [900,1100] {'MET' if 900 <= v['mean']-1.96*v['se'] and v['mean']+1.96*v['se'] <= 1100 else 'NOT met'}), median={v['med']:.0f}, min={v['min']:.0f}")
                if abs(v["mean"] - 1000) < 40: break
                hstar *= (1000 / v["mean"]) ** 0.5
            results[(tau, variant)] = dict(h=hstar, arl=v)

            # ---- confirmation runs at h* for both D-6 episode lengths
            for T, ev in [(2000, 1000), (20000, 10000)]:
                rr = pool.map(confirm_run, [(hstar, variant, tau, mu, sig, g, 1000 + s, T, ev) for s in range(n_seeds)])
                d = [r["delay"] for r in rr]; oc = [r["outcome"] for r in rr]
                det_d = [r["delay"] for r in rr if r["outcome"] == "detected"]
                H = hpdt(d, oc, H_DET); m, lo, hi = ci95([min(x, H_DET) if o == "detected" else H_DET for x, o in zip(d, oc)])
                pf = [r["probe_frac"] for r in rr]; ps = [r["probe_steps"] for r in rr]
                print(f"    [T={T} event={ev}] seeds={n_seeds}  HPDT={H:.1f} [{lo:.1f},{hi:.1f}]  P(detect<=200)={np.mean([o=='detected' for o in oc]):.2f}  "
                      f"delay|detected: mean={np.mean(det_d) if det_d else float('nan'):.1f} med={np.median(det_d) if det_d else float('nan'):.0f} p90={np.percentile(det_d,90) if det_d else float('nan'):.0f} min={min(det_d) if det_d else float('nan')}")
                print(f"        probe steps/run: mean={np.mean(ps):.1f} max={max(ps)} (fraction mean={np.mean(pf):.4f} max={max(pf):.4f}; cap 0.05)  epochs/run={np.mean([r['epochs'] for r in rr]):.0f}")
                print(f"        pre-event false alarms/run: mean={np.mean([r['pre_fa'] for r in rr]):.2f}  P(>=1)={np.mean([r['pre_fa']>0 for r in rr]):.2f}  "
                      f"P(event inside a blind window)={np.mean([r['in_blind'] for r in rr]):.2f}  blind fraction of run={np.mean([r['blind_frac'] for r in rr]):.3f}")
                rs = [x for r in rr for x in r["ref_sizes"]]
                print(f"        post-alarm reference re-estimations: n={len(rs)}, pairs per re-estimation mean={np.mean(rs) if rs else float('nan'):.1f} min={min(rs) if rs else float('nan')}")
                for key, name in [("p_conf", "confounded x"), ("p_unconf", "unconfounded x"), ("p_lost", "lost body/d"), ("p_kept", "kept body/d")]:
                    print(f"        mean p_c {name:15s}: " + "  ".join(f"off{o_}={np.mean([r[key][o_] for r in rr]):.3f}" for o_ in (10, 50, 200)))
                results[(tau, variant, T)] = dict(hpdt=H, ci=(lo, hi), pdet=float(np.mean([o == 'detected' for o in oc])), probe_max=max(pf),
                                                  in_blind=float(np.mean([r['in_blind'] for r in rr])), pre_fa=float(np.mean([r['pre_fa'] for r in rr])))

    # ---- reservoir initial-condition check (section 2 "hard cap" claim)
    print(f"\n{'-'*100}\n[reservoir] initial reservoir = B_max (unspecified in draft) on a 2000-step run with one alarm burst:")
    mu, sig, g, _ = make_calibrated(100, "DRAFT", 0)
    env = SCM(5); det = SeqIBD(np.random.default_rng(5), "DRAFT", reservoir0=B_MAX); det.mu, det.sig = mu, sig; det.set_threshold(results[(0,'DRAFT')]['h'])
    run_stream(env, det, 2000, 1000)
    print(f"    probe steps used = {det.n_probe} of 2000 -> fraction {det.n_probe/2000:.4f} (budget 0.05 -> {'VIOLATED' if det.n_probe/2000 > 0.05 else 'ok'}); alarms at {det.alarms}")
    print(f"\nTotal wall time {time.time()-t0:.0f} s")
    print("\nSUMMARY:", json.dumps({str(k): v for k, v in results.items() if len(k) == 3}, indent=1, default=float))


if __name__ == "__main__":
    main()
