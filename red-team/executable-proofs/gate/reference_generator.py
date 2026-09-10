"""Reference generator for contract v3.9 families L and N (D-10.1, D-11.4). Pure numpy, deterministic under seed.
Instances are drawn from the frozen configuration family, certified, and expose an evaluator-only oracle.
Latent order z = [b (N_b); d (N_d); w (N_w); x (N_x)]. Observation channels: one per latent, then `n_pad` padding.
Noise is keyed by (seed, variable, t) via independent Generators so observational and interventional branches pair."""
import numpy as np, copy
from contract_ref import structural_reach_full, s_obs_eps, max_pairwise_corr
VAR_ID = {"b": 1, "d": 2, "w": 3, "x": 4, "o": 5, "a": 6, "u": 7, "burn": 8}   # deterministic noise namespace (R5-CX-08)

DEFAULT = dict(N_b=4, N_d=2, N_w=4, N_x=10, K=2, n_pad=4, f_conf=0.5, rho_b=0.85, rho_ar=0.9, c_min=0.2, tau=0,
               sigma=dict(b=0.1, d=0.1, w=0.1, x=0.1, o=0.05, a=0.1, u=1.0), rho_u=0.8, a_max=2.0,
               policy_gain=0.15, W_u_scale=0.5, G_scale=0.8, coupling=1.0, noise_mult=1.0,
               burn_in=2000, eps=0.05, H=3, rho_cl=0.98, sat_max=0.05, rho_min=0.4, n_oracle=256,
               family="L", s_N=1.0, kappa_N=0.1, m_N=4.0,                       # contract B family N (D-11.4): s, kappa, m
               n_chains_N=32, T_bound_N=20000, z_init_N=4.0, z_bound_N=100.0, delta_inv=0.05)   # T-L9b certification
RESERVED_EP = dict(witness=999, severed=998, zbar=997, bound=996)   # oracle-only episode ids; scored episodes use small ids

def _spectral_scale(A, rho, rng):
    ev = max(abs(np.linalg.eigvals(A))); return A * (rho / ev) if ev > 0 else A

class Instance:
    def __init__(self, cfg, seed):
        self.cfg = c = dict(DEFAULT, **cfg); self.seed = seed
        rng = np.random.default_rng([seed, 0])          # configuration stream
        Nb, Nd, Nw, Nx, K = c["N_b"], c["N_d"], c["N_w"], c["N_x"], c["K"]
        cm = c["c_min"]
        def sample_matrix(rows, cols, density):
            M = np.zeros((rows, cols)); mask = rng.random((rows, cols)) < density
            M[mask] = rng.choice([-1, 1], size=mask.sum()) * rng.uniform(cm, 1.0, size=mask.sum()); return M
        A_b = sample_matrix(Nb, Nb, 0.5); np.fill_diagonal(A_b, rng.uniform(0.5, 0.9, Nb))
        self.A_b = _spectral_scale(A_b, c["rho_b"], rng)
        small = (self.A_b != 0) & (np.abs(self.A_b) < cm); self.A_b[small] = np.sign(self.A_b[small]) * cm   # faithfulness: |entry| >= c_min after scaling
        self.B = rng.choice([-1, 1], size=(Nb, K)) * rng.uniform(cm, 0.6, size=(Nb, K))   # dense (A0), |entry| >= c_min
        for k in range(K): self.B[2*k % Nb, k] = rng.uniform(0.6, 1.0)          # each actuator has a dominant body component
        ea = c.get("event_actuator", 0); dom = 2*ea % Nb                            # CL-4 by construction (round 5):
        self.B[dom, [k for k in range(K) if k != ea]] = 0.0                           # only actuator `ea` drives its dominant component
        self.A_b[dom, [j for j in range(Nb) if j != dom]] = 0.0                       # and no other body component feeds it
        self.B *= c["coupling"]; nzB = self.B != 0; self.B[nzB] = np.sign(self.B[nzB]) * np.maximum(np.abs(self.B[nzB]), cm)   # floor after perturbation
        self.C_d = sample_matrix(Nd, Nb, 0.5) * c["coupling"]; nzC = self.C_d != 0; self.C_d[nzC] = np.sign(self.C_d[nzC]) * np.maximum(np.abs(self.C_d[nzC]), cm)
        self.A_d = np.diag(np.full(Nd, c["rho_ar"]))
        self.A_w = np.diag(np.full(Nw, c["rho_ar"])); self.A_x = np.diag(np.full(Nx, c["rho_ar"]))
        n_conf = int(round(c["f_conf"] * Nx)); self.confounded = np.zeros(Nx, bool); self.confounded[:n_conf] = True
        self.n_u = 1; self.G = np.zeros((Nx, 1)); self.G[self.confounded, 0] = rng.choice([-1, 1], n_conf) * c["G_scale"]
        Nz = Nb + Nd + Nw + Nx; self.Nz, self.C = Nz, Nz + c["n_pad"]
        self.assign = np.array(list(range(Nz)) + [-1] * c["n_pad"]); self.gain = np.ones(self.C); self.avail = np.ones(self.C, bool)
        self.W_o = np.zeros((K, self.C)); self.W_o[:, :Nb] = -c["policy_gain"] * self.B.T          # body-only feedback
        self.W_u = np.full((K, 1), c["W_u_scale"]); self.tau = c["tau"]
        self.sl = dict(b=slice(0, Nb), d=slice(Nb, Nb+Nd), w=slice(Nb+Nd, Nb+Nd+Nw), x=slice(Nb+Nd+Nw, Nz))
        if c["family"] not in ("L", "N"): raise ValueError(f"unknown family {c['family']!r}")
        self.family = c["family"]; self._zbar = None; self.certification = None

    # ---- dynamics ----
    def _noise(self, var, t, shape, ep):
        return np.random.default_rng([self.seed, ep, VAR_ID[var], t]).normal(size=shape)
    def _body_drive(self, b, a_delayed):
        """Deterministic part of b_{t+1}. Family L: A_b b + B a. Family N (contract B): A_b b + tanh(B a / s) s + kappa clip(b*b, -m, m).
        Works on a single state (Nb,) or a batch (n, Nb) with actions (K,) or (n, K)."""
        lin = b @ self.A_b.T; drive = a_delayed @ self.B.T
        if self.family == "L": return lin + drive
        c = self.cfg; return lin + np.tanh(drive / c["s_N"]) * c["s_N"] + c["kappa_N"] * np.clip(b * b, -c["m_N"], c["m_N"])
    def step_latent(self, z, a_delayed, u, t, ep):
        c = self.cfg; s = {k: v * c["noise_mult"] for k, v in c["sigma"].items()}; sl = self.sl
        b, d, w, x = z[sl["b"]], z[sl["d"]], z[sl["w"]], z[sl["x"]]
        b2 = self._body_drive(b, a_delayed) + s["b"] * self._noise("b", t, b.shape, ep)
        d2 = self.A_d @ d + self.C_d @ b + s["d"] * self._noise("d", t, d.shape, ep)
        w2 = self.A_w @ w + s["w"] * self._noise("w", t, w.shape, ep)
        x2 = self.A_x @ x + self.G @ u + s["x"] * self._noise("x", t, x.shape, ep)
        return np.concatenate([b2, d2, w2, x2])
    def observe(self, z, t, ep):
        o = np.zeros(self.C)
        for ch in range(self.C):
            j = self.assign[ch]
            if j >= 0 and self.avail[ch]: o[ch] = self.gain[ch] * z[j]
        return o + self.cfg["sigma"]["o"] * self.cfg["noise_mult"] * self._noise("o", t, (self.C,), ep)
    def policy(self, o, u, t, ep):
        a = self.W_o @ o + self.W_u @ u + self.cfg["sigma"]["a"] * self.cfg["noise_mult"] * self._noise("a", t, (self.cfg["K"],), ep)
        return np.clip(a, -self.cfg["a_max"], self.cfg["a_max"])

    def run(self, T, ep=0, actions=None, event_t=None, event=None, z0=None, u0=None, record_u=False):
        """Roll out T steps under the default policy; `actions` maps t -> action to apply instead (probes).
        Returns dict with o[T+1, C], a[T, K], z[T+1, Nz], u[T+1], sat (saturation fraction)."""
        c = self.cfg; K = c["K"]; Nz = self.Nz
        z = np.zeros(Nz) if z0 is None else z0.copy(); u = np.zeros(1) if u0 is None else u0.copy()
        if z0 is None and c["burn_in"] > 0:                              # burn-in with a separate keyed prefix (R5-CX-15)
            queue0 = [np.zeros(K)] * self.tau
            for tb in range(c["burn_in"]):
                ob = self.observe(z, tb, ep + 100000); ab = self.policy(ob, u, tb, ep + 100000); queue0.append(ab); ad = queue0.pop(0)
                z = self.step_latent(z, ad, u, tb, ep + 100000); u = c["rho_u"] * u + c["sigma"]["u"] * self._noise("u", tb, (1,), ep + 100000)
        O = np.zeros((T+1, self.C)); A = np.zeros((T, K)); Z = np.zeros((T+1, Nz)); U = np.zeros((T+1, 1))
        queue = [np.zeros(K)] * self.tau; sat = 0          # a_t reaches b at t+tau+1 (contract B)
        O[0] = self.observe(z, 0, ep); Z[0] = z; U[0] = u
        for t in range(T):
            if event_t is not None and t == event_t: self.apply_event(event)
            a = self.policy(O[t], u, t, ep) if actions is None or t not in actions else np.clip(actions[t], -c["a_max"], c["a_max"])
            sat += int(np.any(np.abs(a) >= c["a_max"] - 1e-12))
            queue.append(a); a_delayed = queue.pop(0)
            z = self.step_latent(z, a_delayed, u, t, ep)
            u = c["rho_u"] * u + c["sigma"]["u"] * self._noise("u", t, (1,), ep)             # noise_mult does NOT scale the confounder driver u (A0)
            A[t] = a; Z[t+1] = z; U[t+1] = u; O[t+1] = self.observe(z, t+1, ep)
        return dict(o=O, a=A, z=Z, u=U, sat=sat / T)

    def apply_event(self, event):
        if event is None: return
        self._zbar = None                                   # CL-8: the stationary state is re-estimated after every event
        kind, arg = event
        if kind == "actuator_loss": self.B[:, arg] = 0.0; self.event_applied = True
        elif kind == "actuator_partial": self.B[:, arg[0]] *= arg[1]
        elif kind == "sensor_dropout": self.avail[arg] = False
        elif kind == "sensor_gain": self.gain[arg[0]] = arg[1]
        else: raise ValueError(kind)

    # ---- oracle (evaluator only) ----
    def S_latent(self, H=None, tau=None):
        c = self.cfg; return structural_reach_full(self.A_b, self.B, c["H"] if H is None else H, c["tau"] if tau is None else tau,
                                                   self.C_d, self.A_d, self.A_w, self.A_x)
    def operational_effect(self, H=None):
        """e_j = max_h max_{a in A} |E[z_j(t+h)|do(a)] - E[z_j(t+h)|do(0)]| at zero noise from z̄ (C2/C4). Family L: z̄ = 0, exact.
        Family N: z̄ empirical (`zbar`), the response is not odd in a, both signs are taken (T-C4-N)."""
        c = self.cfg; H = c["H"] if H is None else H; K = c["K"]; e = np.zeros(self.Nz); zb = self.zbar
        for k in range(K):
            for sign in (1.0, -1.0):
                a = np.zeros(K); a[k] = sign
                z_a = zb.copy(); z_0 = zb.copy(); qa = [np.zeros(K)] * self.tau; q0 = [np.zeros(K)] * self.tau
                for h in range(1, H + 1):
                    qa.append(a if h == 1 else np.zeros(K)); q0.append(np.zeros(K))
                    z_a = self._step_noiseless(z_a, qa.pop(0)); z_0 = self._step_noiseless(z_0, q0.pop(0))
                    e = np.maximum(e, np.abs(z_a - z_0))
        return e
    def _step_noiseless(self, z, a_delayed):
        sl = self.sl; b, d, w, x = z[sl["b"]], z[sl["d"]], z[sl["w"]], z[sl["x"]]
        return np.concatenate([self._body_drive(b, a_delayed), self.A_d @ d + self.C_d @ b, self.A_w @ w, self.A_x @ x])

    # ---- family N stationary state and boundedness (contract B, C4, T-L9b) ----
    @property
    def zbar(self):
        """Stationary mean z̄ (C4). Family L: exactly 0. Family N: empirical, estimated once per structural state and cached;
        every apply_event invalidates the cache (CL-8: re-certified after events)."""
        if self.family == "L": return np.zeros(self.Nz)
        if self._zbar is None: self._zbar = self.stationary_mean()
        return self._zbar
    def stationary_mean(self, T=4000):
        r = self.run(T, ep=RESERVED_EP["zbar"]); drop = min(2000, T // 2)
        return r["z"][1 + drop:].mean(axis=0)
    def rollout_batch(self, n, T, z0, ep):
        """n independent closed-loop chains from initial states z0[n, Nz] under the default policy; returns z[T+1, n, Nz].
        Noise is keyed by (seed, ep, variable, t) and drawn with shape (n, dim), so chains are independent."""
        c = self.cfg; K = c["K"]; s = {k: v * c["noise_mult"] for k, v in c["sigma"].items()}; sl = self.sl
        z = np.array(z0, float); u = np.zeros((n, 1)); Z = np.zeros((T + 1, n, self.Nz)); Z[0] = z
        obs_idx = np.where(self.assign >= 0, self.assign, 0); obs_mask = ((self.assign >= 0) & self.avail) * self.gain
        queue = [np.zeros((n, K))] * self.tau
        for t in range(T):
            o = z[:, obs_idx] * obs_mask + s["o"] * self._noise("o", t, (n, self.C), ep)
            a = np.clip(o @ self.W_o.T + u @ self.W_u.T + s["a"] * self._noise("a", t, (n, K), ep), -c["a_max"], c["a_max"])
            queue.append(a); ad = queue.pop(0)
            b, d, w, x = z[:, sl["b"]], z[:, sl["d"]], z[:, sl["w"]], z[:, sl["x"]]
            z = np.concatenate([self._body_drive(b, ad) + s["b"] * self._noise("b", t, b.shape, ep),
                                d @ self.A_d.T + b @ self.C_d.T + s["d"] * self._noise("d", t, d.shape, ep),
                                w @ self.A_w.T + s["w"] * self._noise("w", t, w.shape, ep),
                                x @ self.A_x.T + u @ self.G.T + s["x"] * self._noise("x", t, x.shape, ep)], axis=1)
            u = c["rho_u"] * u + c["sigma"]["u"] * self._noise("u", t, (n, 1), ep); Z[t + 1] = z
        return Z
    def boundedness_certificate(self):
        """T-L9b (family N): n_chains_N chains from random initial states in [-z_init_N, z_init_N] over T_bound_N steps must stay
        within z_bound_N, and the stationary means of the b and d blocks (the nonlinear loop), estimated on four groups of
        n_chains_N/4 chains after discarding the first 2000 steps, must agree within delta_inv. w and x are linear AR(1)
        with exact zero mean and are not part of the agreement test."""
        c = self.cfg; n, T = c["n_chains_N"], c["T_bound_N"]
        rng = np.random.default_rng([self.seed, 555]); z0 = rng.uniform(-c["z_init_N"], c["z_init_N"], (n, self.Nz))
        Z = self.rollout_batch(n, T, z0, RESERVED_EP["bound"]); max_abs = float(np.max(np.abs(Z)))
        keep = slice(self.sl["b"].start, self.sl["d"].stop); post = Z[min(2000, T // 2) + 1:, :, keep]
        groups = np.array_split(np.arange(n), 4); means = np.stack([post[:, g, :].mean(axis=(0, 1)) for g in groups])
        spread = float(np.max(means.max(axis=0) - means.min(axis=0)))
        return dict(bounded=bool(np.isfinite(max_abs) and max_abs <= c["z_bound_N"]), max_abs_z=max_abs, chain_mean_spread=spread,
                    stationary_ok=bool(spread <= c["delta_inv"]))
    def labels_consistent(self, H=None):
        """E1b: structural reachability and the operational effect must agree on every latent (effect > eps iff reachable)."""
        e = self.operational_effect(H); S = self.S_latent(H); return bool(np.all((e > self.cfg["eps"]) == S))
    def S_obs(self):
        return s_obs_eps(self.operational_effect(), self.assign, self.gain, self.avail, self.cfg["eps"])
    def S_obs_pre_event(self):
        """Support before the confirmatory event (for the D-11.1 primary over the pre-event support)."""
        return self._pre_S.copy() if hasattr(self, "_pre_S") else self.S_obs()
    def confounded_channels(self):
        m = np.zeros(self.C, bool)
        for ch in range(self.C):
            j = self.assign[ch]
            if j >= 0 and self.sl["x"].start <= j < self.sl["x"].stop: m[ch] = self.confounded[j - self.sl["x"].start]
        return m

    # ---- certification (contract B, C2, E2) ----
    def certify(self, T=4000):
        c = self.cfg; out = {}
        Nb, Nd, K = c["N_b"], c["N_d"], c["K"]
        # augmented closed-loop matrix on [b; d; a_{t-1..t-tau}] with the policy reading body channels
        Wb = self.W_o[:, :Nb]; n = Nb + Nd + K * self.tau; M = np.zeros((n, n))
        M[:Nb, :Nb] = self.A_b; M[Nb:Nb+Nd, :Nb] = self.C_d; M[Nb:Nb+Nd, Nb:Nb+Nd] = self.A_d
        if self.tau == 0: M[:Nb, :Nb] += self.B @ Wb
        else:
            M[:Nb, Nb+Nd+K*(self.tau-1):] = self.B                       # b receives the oldest queued action
            M[Nb+Nd:Nb+Nd+K, :Nb] = Wb                                    # newest action from body feedback
            for i in range(1, self.tau): M[Nb+Nd+K*i:Nb+Nd+K*(i+1), Nb+Nd+K*(i-1):Nb+Nd+K*i] = np.eye(K)
        out["rho_cl"] = float(max(abs(np.linalg.eigvals(M))))   # linearised loop; the family N criterion is T-L9b below
        if self.family == "N":
            out.update(self.boundedness_certificate()); self._zbar = None
        r = self.run(T, ep=RESERVED_EP["witness"]); out["sat"] = r["sat"]
        xs = r["z"][1:, self.sl["x"]]; out["rho_witness"] = max_pairwise_corr(r["a"][:-1], xs[1:])
        # severing: randomised do(a)
        rng = np.random.default_rng([self.seed, 777]); acts = {t: rng.choice([-1.0, 1.0], K) for t in range(T)}
        r2 = self.run(T, ep=RESERVED_EP["severed"], actions=acts); xs2 = r2["z"][1:, self.sl["x"]]; out["rho_severed"] = max_pairwise_corr(r2["a"][:-1], xs2[1:])
        e = self.operational_effect(); out["min_margin"] = float(np.min(np.abs(e[self.S_latent()] - c["eps"]))) if self.S_latent().any() else 0.0
        # CL-4: the confirmatory event (loss of actuator `event_actuator`) must remove >= 1 observed channel from S_obs (R5-GM-01, R5-CX-02)
        post = copy.deepcopy(self); post.apply_event(("actuator_loss", c.get("event_actuator", 0)))
        before, after = self.S_obs(), post.S_obs(); out["s_change"] = bool((before & ~after).any()); out["n_lost"] = int((before & ~after).sum())
        out["min_entry_ok"] = bool(np.all(np.abs(self.A_b[self.A_b != 0]) >= c["c_min"] - 1e-12) and np.all(np.abs(self.B[self.B != 0]) >= c["c_min"] - 1e-12))   # nonzero entries only (CL-4 rows contain zeros)
        stable = out["rho_cl"] <= c["rho_cl"] if self.family == "L" else (out["bounded"] and out["stationary_ok"])   # B: L radius; N empirical (CX-09)
        out["ok"] = (stable and out["sat"] <= c["sat_max"] and out["rho_witness"] >= c["rho_min"]
                     and out["rho_severed"] <= max(0.05, 3 * np.sqrt(2 * np.log(K * c["N_x"]) / T)) and out["min_margin"] > 0.0
                     and out["s_change"] and out["min_entry_ok"] and self.labels_consistent())
        self.certification = out; return out

def draw_certified(cfg, seed, max_tries=60):
    """Draw instances at consecutive sub-seeds until one certifies; records n_resamples (C2). Configuration seeds 0..9 are
    development instances; confirmation seeds come from confirmation_seeds.py (D-11.3) and are never used before the freeze."""
    for i in range(max_tries):
        inst = Instance(cfg, seed * 1000 + i); cert = inst.certify()
        if cert["ok"]: inst.n_resamples = i; inst._pre_S = inst.S_obs().copy(); return inst
    raise RuntimeError(f"no certified instance for seed {seed} after {max_tries} tries: last {cert}")
