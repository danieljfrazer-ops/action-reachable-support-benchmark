"""
CHECK SCRIPT for review8-claude-opus/derivation.md -- NOT A RESULT.

Everything this file prints is a CHECK of algebra done by hand in derivation.md,
on one hand-written toy instance of family L-C.  It is not evidence about the
frozen generator, not a simulation of the benchmark, and no number here may be
quoted as an outcome.  Its only job is to catch sign errors and dropped terms.

Toy family L-C (tau selectable), all means zero:
    u_{t+1}   = rho_u u_t + eps^u
    a_t       = W_b (b_t + eps^{o,b}_t) + W_u u_t + eps^a_t          (no clip)
    b_{t+1}   = A_b b_t + B a_{t-tau} + G_b u_t + eps^b
    x_{t+1}   = A_x x_t + G_x u_t + eps^x
    o_t       = [b_t; x_t] + eps^o_t

Exact stationary second moments by Lyapunov; no Monte Carlo except where noted.

Run: /Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3 check_algebra.py
"""

import numpy as np

np.set_printoptions(precision=5, suppress=True, linewidth=140)

# ---------------------------------------------------------------- parameters
NB, NX, K, NU = 3, 4, 2, 1
NO = NB + NX                      # observed latents: body + distractors
NCONF = 2                         # confounded distractor channels (rows 0,1 of x)


def base_params():
    A_b = np.array([[0.60, 0.20, 0.00],
                    [0.00, 0.55, 0.25],
                    [0.15, 0.00, 0.50]])
    A_b *= 0.85 / max(abs(np.linalg.eigvals(A_b)))
    # CL-4-like: column 0 of B reaches body 0 alone.
    B = np.array([[0.70, 0.00],
                  [0.00, 0.45],
                  [0.00, 0.30]])
    W_b = np.array([[-0.30, 0.10, 0.00],
                    [0.05, -0.25, 0.15]])
    W_u = np.array([[0.80], [-0.50]])
    G_b = np.array([[0.40], [0.25], [0.00]])
    G_x = np.zeros((NX, NU))
    G_x[0, 0], G_x[1, 0] = 0.9, 0.7
    A_x = 0.9 * np.eye(NX)
    return dict(A_b=A_b, B=B, W_b=W_b, W_u=W_u, G_b=G_b, G_x=G_x, A_x=A_x,
                rho_u=0.8, sig_u=1.0, sig_b=0.1, sig_x=0.1,
                sig_o=0.05, sig_a=0.1, tau=0)


# ---------------------------------------------- state-space assembly (exact)
# s = [u ; b ; x ; a_{t-1} ; a_{t-2}]   dim NS
IU = slice(0, NU)
IB = slice(NU, NU + NB)
IX = slice(NU + NB, NU + NB + NX)
IA1 = slice(NU + NB + NX, NU + NB + NX + K)
IA2 = slice(NU + NB + NX + K, NU + NB + NX + 2 * K)
NS = NU + NB + NX + 2 * K
# v = [eps^o (NO) ; eps^a (K)]      w = [eps^u ; eps^b ; eps^x]
NV, NW = NO + K, NU + NB + NX


def build(p):
    A_b, B, W_b, W_u = p["A_b"], p["B"], p["W_b"], p["W_u"]
    G_b, G_x, A_x = p["G_b"], p["G_x"], p["A_x"]

    C_o = np.zeros((NO, NS))                       # o = C_o s + Pi_o v
    C_o[:NB, IB] = np.eye(NB)
    C_o[NB:, IX] = np.eye(NX)
    Pi_o = np.zeros((NO, NV))
    Pi_o[:, :NO] = np.eye(NO)

    K_s = np.zeros((K, NS))                        # a_t = K_s s + K_v v
    K_s[:, IB] = W_b
    K_s[:, IU] = W_u
    K_v = np.zeros((K, NV))
    K_v[:, :NB] = W_b                              # policy reads noisy body obs
    K_v[:, NO:] = np.eye(K)

    E1s = np.zeros((K, NS)); E1s[:, IA1] = np.eye(K)   # a_{t-1}
    E2s = np.zeros((K, NS)); E2s[:, IA2] = np.eye(K)   # a_{t-2}

    if p["tau"] == 0:
        drv_s, drv_v = K_s, K_v
    elif p["tau"] == 1:
        drv_s, drv_v = E1s, np.zeros((K, NV))
    elif p["tau"] == 2:
        drv_s, drv_v = E2s, np.zeros((K, NV))
    else:
        raise ValueError

    A = np.zeros((NS, NS)); L = np.zeros((NS, NV)); W = np.zeros((NS, NW))
    A[IU, IU] = p["rho_u"] * np.eye(NU)
    W[IU, :NU] = np.eye(NU)
    A[IB, IB] = A_b
    A[IB, IU] = G_b
    A[IB, :] += B @ drv_s
    L[IB, :] += B @ drv_v
    W[IB, NU:NU + NB] = np.eye(NB)
    A[IX, IX] = A_x
    A[IX, IU] = G_x
    W[IX, NU + NB:] = np.eye(NX)
    A[IA1, :] = K_s;  L[IA1, :] = K_v
    A[IA2, IA1] = np.eye(K)

    Sv = np.diag(np.r_[p["sig_o"] ** 2 * np.ones(NO), p["sig_a"] ** 2 * np.ones(K)])
    Sb = p.get("Sig_b", None)
    if Sb is None:
        Sb = p["sig_b"] ** 2 * np.eye(NB)
    Sw = np.zeros((NW, NW))
    Sw[:NU, :NU] = p["sig_u"] ** 2 * np.eye(NU)
    Sw[NU:NU + NB, NU:NU + NB] = Sb
    Sw[NU + NB:, NU + NB:] = p["sig_x"] ** 2 * np.eye(NX)
    Q = L @ Sv @ L.T + W @ Sw @ W.T
    return dict(A=A, L=L, Sv=Sv, Sw=Sw, W=W, Q=Q, C_o=C_o, Pi_o=Pi_o,
                K_s=K_s, K_v=K_v, E1s=E1s, E2s=E2s)


def dlyap(A, Q, iters=20000, tol=1e-14):
    S = Q.copy(); Ak = A.copy()
    for _ in range(60):                 # doubling
        S_new = S + Ak @ S @ Ak.T
        Ak = Ak @ Ak
        if np.max(np.abs(S_new - S)) < tol * max(1.0, np.max(np.abs(S_new))):
            S = S_new; break
        S = S_new
    return 0.5 * (S + S.T)


def moments(p):
    m = build(p)
    if max(abs(np.linalg.eigvals(m["A"]))) >= 1.0:
        raise RuntimeError("unstable toy closed loop")
    Ss = dlyap(m["A"], m["Q"])
    m["Ss"] = Ss
    return m


def gamma_y(m, kmax):
    """Exact autocovariances of y=(o,a) at lags 0..kmax."""
    C_y = np.vstack([m["C_o"], m["K_s"]])
    D_y = np.vstack([m["Pi_o"], m["K_v"]])
    A, L, Sv, Ss = m["A"], m["L"], m["Sv"], m["Ss"]
    out = [C_y @ Ss @ C_y.T + D_y @ Sv @ D_y.T]
    Ak = np.eye(NS)
    for k in range(1, kmax + 1):
        out.append(C_y @ (Ak @ A) @ Ss @ C_y.T + C_y @ Ak @ L @ Sv @ D_y.T)
        Ak = Ak @ A
    return out


def predictor(m):
    """Population OLS of o_{t+1} on phi=[o_t, a_t, a_{t-1}, a_{t-2}] (zero mean)."""
    C_phi = np.vstack([m["C_o"], m["K_s"], m["E1s"], m["E2s"]])
    D_phi = np.vstack([m["Pi_o"], m["K_v"], np.zeros((K, NV)), np.zeros((K, NV))])
    A, L, Sv, Ss, C_o, Pi_o = m["A"], m["L"], m["Sv"], m["Ss"], m["C_o"], m["Pi_o"]
    S_phi = C_phi @ Ss @ C_phi.T + D_phi @ Sv @ D_phi.T
    S_phiy = C_phi @ Ss @ A.T @ C_o.T + D_phi @ Sv @ L.T @ C_o.T
    beta = np.linalg.solve(S_phi, S_phiy)                     # (NO+3K) x NO
    S_yy = C_o @ (A @ Ss @ A.T + m["Q"]) @ C_o.T + Pi_o @ Sv @ Pi_o.T
    resid = np.diag(S_yy - S_phiy.T @ beta)
    return beta, S_phi, np.sqrt(np.maximum(resid, 1e-18))


def v_u_given_o(m):
    """Var(u_t | o_t) -- residual confounder variance after the observation."""
    Ss, C_o, Pi_o, Sv = m["Ss"], m["C_o"], m["Pi_o"], m["Sv"]
    S_oo = C_o @ Ss @ C_o.T + Pi_o @ Sv @ Pi_o.T
    S_uo = Ss[IU, :] @ C_o.T
    S_uu = Ss[IU, IU]
    return float((S_uu - S_uo @ np.linalg.solve(S_oo, S_uo.T))[0, 0])


def predictor_1lag(m):
    """Population OLS of o_{t+1} on phi=[o_t, a_t] only (the clean case)."""
    C_phi = np.vstack([m["C_o"], m["K_s"]])
    D_phi = np.vstack([m["Pi_o"], m["K_v"]])
    A, L, Sv, Ss, C_o = m["A"], m["L"], m["Sv"], m["Ss"], m["C_o"]
    S_phi = C_phi @ Ss @ C_phi.T + D_phi @ Sv @ D_phi.T
    S_phiy = C_phi @ Ss @ A.T @ C_o.T + D_phi @ Sv @ L.T @ C_o.T
    return np.linalg.solve(S_phi, S_phiy)


BAR = "-" * 78

# =====================================================================  C1
print(BAR)
print("C1  passive projection bias:  beta_a(lag tau) =?= B + kappa G_b W_u^T")
print("    kappa = v_u / (sigma_a^2 + v_u ||W_u||^2),  v_u = Var(u_t | o_t)")
print(BAR)
print("  (a) clean case: 1-lag regression [o_t, a_t], tau = 0 -- formula must be exact")
for sig_o in (0.0, 0.05):
    p = base_params(); p["tau"] = 0; p["sig_o"] = sig_o
    m = moments(p)
    beta_a = predictor_1lag(m)[NO:NO + K, :NB].T
    v_u = v_u_given_o(m)
    Wu = p["W_u"][:, 0]
    kap = v_u / (p["sig_a"] ** 2 + v_u * (Wu @ Wu))
    pred = p["B"] + kap * np.outer(p["G_b"][:, 0], Wu)
    print(f"      sig_o={sig_o}: v_u={v_u:.5f} kappa={kap:.5f} "
          f"max|beta_a - (B + kappa G_b W_u^T)| = {np.max(np.abs(beta_a - pred)):.3e}  "
          f"max|bias| = {np.max(np.abs(kap*np.outer(p['G_b'][:,0], Wu))):.4f}")

print("  (b) frozen design: 3 action lags, the bias splits across lag slots")
for tau in (0, 2):
    p = base_params(); p["tau"] = tau
    m = moments(p)
    beta, _, _ = predictor(m)
    v_u = v_u_given_o(m); Wu = p["W_u"][:, 0]
    kap = v_u / (p["sig_a"] ** 2 + v_u * (Wu @ Wu))
    print(f"      tau={tau}: kappa(o_t only)={kap:.4f}")
    for lag in range(3):
        blk = beta[NO + lag*K:NO + (lag+1)*K, :NB].T
        struct = p["B"] if lag == tau else np.zeros((NB, K))
        print(f"        lag {lag}: beta_a - B_struct =\n{np.array2string(blk - struct, prefix=' '*22)}")

# =====================================================================  C2
print(BAR)
print("C2  can conditioning on MORE observables remove the bias?")
print("    v_u = Var(u_t | conditioning set).  Floor for any PAST-measurable set")
print("    is sigma_u^2 = 1.0, because u_t = rho_u u_{t-1} + eps^u and eps^u_t has")
print("    no trace at time t outside a_t itself.")
print(BAR)


def v_u_general(m, extra_lags=0, smoother=False):
    """Var(u_t | o_t, o_{t-1}, ..., [o_{t+1} if smoother])."""
    Ss, C_o, Pi_o, Sv, A, L = m["Ss"], m["C_o"], m["Pi_o"], m["Sv"], m["A"], m["L"]
    # stack Z = [o_t; o_{t-1}; ...; o_{t-extra_lags}] (+ o_{t+1})
    blocks = []                       # each entry: (Cs, Dv_lag_index) handled via covs
    # build covariance of Z and cross-cov with u_t directly from Gamma-type formulas
    def cov_oo(k):                    # Cov(o_{t+k}, o_t), k >= 0
        if k == 0:
            return C_o @ Ss @ C_o.T + Pi_o @ Sv @ Pi_o.T
        Ak = np.linalg.matrix_power(A, k)
        Akm1 = np.linalg.matrix_power(A, k - 1)
        return C_o @ Ak @ Ss @ C_o.T + C_o @ Akm1 @ L @ Sv @ Pi_o.T
    def cov_uo(k):                    # Cov(u_t, o_{t+k}) for k <= 0 and k = +1
        if k <= 0:
            j = -k                    # Cov(u_t, o_{t-j}) = Cov(u_{t'+j}, o_{t'})
            Aj = np.linalg.matrix_power(A, j)
            if j == 0:
                return (Ss[IU, :] @ C_o.T)
            Ajm1 = np.linalg.matrix_power(A, j - 1)
            return (Aj @ Ss @ C_o.T + Ajm1 @ L @ Sv @ Pi_o.T)[IU, :]
        else:                         # Cov(u_t, o_{t+1}) = (Cov(o_{t+1}, u_t))^T
            return (C_o @ A @ Ss[:, IU] + C_o @ L @ Sv @ np.zeros((NV, NU))).T
    lags = list(range(0, extra_lags + 1))
    idx = [-l for l in lags]
    if smoother:
        idx = [1] + idx
    n = len(idx)
    Z = np.zeros((n * NO, n * NO)); cu = np.zeros((NU, n * NO))
    for i, ki in enumerate(idx):
        cu[:, i*NO:(i+1)*NO] = cov_uo(ki)
        for j, kj in enumerate(idx):
            d = ki - kj
            Z[i*NO:(i+1)*NO, j*NO:(j+1)*NO] = cov_oo(d) if d >= 0 else cov_oo(-d).T
    Z += 1e-12 * np.eye(n * NO)
    return float((Ss[IU, IU] - cu @ np.linalg.solve(Z, cu.T))[0, 0])


p_ = base_params(); p_["sig_o"] = 0.0
m_ = moments(p_)
Wu_ = p_["W_u"][:, 0]
print(f"    sigma_u^2 = {p_['sig_u']**2:.3f}, Var(u_t) stationary = "
      f"{m_['Ss'][IU, IU][0,0]:.4f}, 1/||W_u||^2 = {1/(Wu_@Wu_):.4f}")
for label, kw in [("o_t only", dict()), ("o_t..o_{t-2}", dict(extra_lags=2)),
                  ("o_t..o_{t-8}", dict(extra_lags=8)),
                  ("SMOOTHER: + o_{t+1}", dict(extra_lags=8, smoother=True))]:
    vu = v_u_general(m_, **kw)
    kap = vu / (p_["sig_a"] ** 2 + vu * (Wu_ @ Wu_))
    print(f"      {label:22s} v_u = {vu:8.5f}   kappa = {kap:.5f}   "
          f"max|kappa G_b W_u^T| = {np.max(np.abs(kap*np.outer(p_['G_b'][:,0], Wu_))):.4f}")
print("    -> the number of confounded distractors is irrelevant to a causal predictor:")
for nconf in (0, 2, 4):
    q = base_params(); q["sig_o"] = 0.0
    Gx = np.zeros((NX, NU))
    for i in range(nconf):
        Gx[i, 0] = 0.9 if i % 2 == 0 else 0.7
    q["G_x"] = Gx
    mq = moments(q)
    vu = v_u_general(mq, extra_lags=8)
    bet = predictor_1lag(mq)[NO:NO + K, :NB].T
    print(f"      n_conf={nconf}: v_u(8 lags)={vu:.5f}  max|beta_a - B| = "
          f"{np.max(np.abs(bet - q['B'])):.4f}")

# =====================================================================  C3
print(BAR)
print("C3  exact observational equivalence needs a ZERO exogenous action part.")
print("    theta' = (A_b - D W_b, B + D, G_b - D W_u); compare Gamma_y(0..12).")
print(BAR)


def twin(p, Delta, compensate=True):
    """theta' with F, g and (if compensate) the b-driving-noise covariance matched."""
    q = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in p.items()}
    q["A_b"] = p["A_b"] - Delta @ p["W_b"]
    q["B"] = p["B"] + Delta
    q["G_b"] = p["G_b"] - Delta @ p["W_u"]
    if compensate:
        S_zeta = p["W_b"] @ (p["sig_o"] ** 2 * np.eye(NB)) @ p["W_b"].T \
                 + p["sig_a"] ** 2 * np.eye(K)
        B_, D_ = p["B"], Delta
        corr = D_ @ S_zeta @ B_.T + B_ @ S_zeta @ D_.T + D_ @ S_zeta @ D_.T
        q["Sig_b"] = p["sig_b"] ** 2 * np.eye(NB) - corr
    return q


def equivalence_gap(sig_a, sig_o, Delta, compensate=True):
    p = base_params(); p["sig_a"] = sig_a; p["sig_o"] = sig_o
    q = twin(p, Delta, compensate)
    g1, g2 = gamma_y(moments(p), 12), gamma_y(moments(q), 12)
    scale = max(np.max(np.abs(g)) for g in g1)
    return max(np.max(np.abs(a - b)) for a, b in zip(g1, g2)) / scale


D = np.array([[0.00, 0.22], [0.18, 0.00], [0.00, 0.00]])   # flips B_{0,1}: 0 -> 0.22 > eps
print(f"Delta (support-flipping, |entry| up to {np.max(np.abs(D)):.2f} > eps=0.05):\n{D}")
for sa, so in [(0.0, 0.0), (0.1, 0.0), (0.0, 0.05), (0.1, 0.05)]:
    print(f"  sigma_a={sa:.2f} sigma_o={so:.2f}:  rel. max |Gamma_y diff| lags 0..12 = "
          f"{equivalence_gap(sa, so, D):.3e}  (Sigma_b uncompensated: "
          f"{equivalence_gap(sa, so, D, False):.3e})")

# =====================================================================  C3b
print(BAR)
print("C3b how far from the knife-edge?  per-step Kullback-Leibler rate between")
print("     the true law and the support-flipped twin (Gaussian spectral formula).")
print(BAR)


def spectral_density(m, w):
    A, L, W_, Sv = m["A"], m["L"], None, m["Sv"]
    C_y = np.vstack([m["C_o"], m["K_s"]])
    D_y = np.vstack([m["Pi_o"], m["K_v"]])
    Sw = m["Sw"]; Wm = m["W"]
    R = np.linalg.inv(np.exp(1j * w) * np.eye(NS) - A)
    Tv = C_y @ R @ L + D_y
    Tw = C_y @ R @ Wm
    return Tv @ Sv @ Tv.conj().T + Tw @ Sw @ Tw.conj().T


def kl_rate_exact(m1, m2, n=1024, reg=1e-4):
    """(1/4pi) int [tr(P2^-1 P1) - logdet(P2^-1 P1) - m] dw, via a Hermitian
    generalised eigenproblem so it is numerically non-negative.  reg is an
    isotropic observer-noise floor added to BOTH laws (both spectra are
    singular when sigma_a = sigma_o = 0)."""
    mdim = m1["C_o"].shape[0] + K
    acc = 0.0
    for i in range(n):
        w = -np.pi + 2 * np.pi * (i + 0.5) / n
        P1 = spectral_density(m1, w) + reg * np.eye(mdim)
        P2 = spectral_density(m2, w) + reg * np.eye(mdim)
        P1 = 0.5 * (P1 + P1.conj().T); P2 = 0.5 * (P2 + P2.conj().T)
        Lc = np.linalg.cholesky(P2)
        Li = np.linalg.inv(Lc)
        M = Li @ P1 @ Li.conj().T
        lam = np.linalg.eigvalsh(0.5 * (M + M.conj().T))
        lam = np.maximum(lam, 1e-300)
        acc += float(np.sum(lam - np.log(lam) - 1.0))
    return acc / n / 4.0


for sa, so in [(0.0, 0.0), (0.1, 0.0), (0.0, 0.05), (0.1, 0.05), (0.4, 0.05)]:
    pp = base_params(); pp["sig_a"] = sa; pp["sig_o"] = so
    qq = twin(pp, D, compensate=True)
    ev = np.linalg.eigvalsh(qq["Sig_b"])
    if ev.min() <= 0:
        print(f"  sigma_a={sa} sigma_o={so}: compensated Sigma_b not PSD "
              f"(min eig {ev.min():.2e}) -- twin infeasible at this Delta")
        continue
    m1, m2 = moments(pp), moments(qq)
    r = kl_rate_exact(m1, m2)
    print(f"  sigma_a={sa:.2f} sigma_o={so:.2f}: KL rate = {r:.3e} nats/step "
          f"-> ~{(1.0/max(r,1e-300)):.3g} steps for one nat of evidence")

# =====================================================================  C3c
print(BAR)
print("C3c PROFILE distinguishability: minimise the KL rate over the nuisances")
print("    (A_b', G_b', Sigma_b') holding B' = B + Delta fixed.  This is how much")
print("    passive information about the SUPPORT really survives.")
print(BAR)
from scipy.optimize import minimize


def profile_kl(sig_a, sig_o, Delta, restarts=1):
    p0 = base_params(); p0["sig_a"] = sig_a; p0["sig_o"] = sig_o
    m1 = moments(p0)
    q0 = twin(p0, Delta, compensate=True)
    Sb0 = q0["Sig_b"]
    ev = np.linalg.eigvalsh(Sb0)
    if ev.min() <= 1e-9:
        Sb0 = p0["sig_b"] ** 2 * np.eye(NB)
    Lb0 = np.linalg.cholesky(Sb0)
    tril = np.tril_indices(NB)
    x0 = np.r_[q0["A_b"].ravel(), q0["G_b"].ravel(), Lb0[tril]]

    def unpack(x):
        q = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in p0.items()}
        q["B"] = p0["B"] + Delta
        q["A_b"] = x[:NB * NB].reshape(NB, NB)
        q["G_b"] = x[NB * NB:NB * NB + NB * NU].reshape(NB, NU)
        Lb = np.zeros((NB, NB)); Lb[tril] = x[NB * NB + NB * NU:]
        q["Sig_b"] = Lb @ Lb.T + 1e-9 * np.eye(NB)
        return q

    def obj(x):
        q = unpack(x)
        if max(abs(np.linalg.eigvals(build(q)["A"]))) >= 0.999:
            return 1e3
        try:
            return kl_rate_exact(m1, moments(q), n=64)
        except Exception:
            return 1e3

    best = (obj(x0), x0)
    for r in range(restarts):
        xs = x0 if r == 0 else x0 * (1 + 0.05 * np.random.default_rng(r).standard_normal(x0.shape))
        res = minimize(obj, xs, method="Nelder-Mead",
                       options=dict(maxiter=4000, maxfev=4000, xatol=1e-7, fatol=1e-11))
        if res.fun < best[0]:
            best = (res.fun, res.x)
    return best[0], unpack(best[1])


for sa, so in [(0.1, 0.05), (0.02, 0.05)]:
    val, qbest = profile_kl(sa, so, D)
    print(f"  sigma_a={sa:.2f} sigma_o={so:.2f}: min KL rate over nuisances = {val:.3e} "
          f"nats/step -> ~{1/max(val,1e-300):.4g} steps for one nat")
    print(f"      best G_b' = {qbest['G_b'].ravel()}   (true G_b = "
          f"{base_params()['G_b'].ravel()})")

# =====================================================================  C4
print(BAR)
print("C4  probe sign-contrast at h = tau+1 equals 2*B[:,k], whatever G_b (MC).")
print(BAR)


def probe_contrast_mc(G_b_scale, tau, k=0, T=400_000, seed=7):
    p = base_params(); p["tau"] = tau
    p["G_b"] = G_b_scale * base_params()["G_b"]
    rng = np.random.default_rng(seed)
    A_b, B, W_b, W_u = p["A_b"], p["B"], p["W_b"], p["W_u"]
    G_b, G_x, A_x = p["G_b"], p["G_x"], p["A_x"]
    b = np.zeros(NB); x = np.zeros(NX); u = 0.0
    aq = [np.zeros(K) for _ in range(max(tau, 1))]
    h = tau + 1
    # ring buffer of (probe sign at anchor, b at anchor) with h-step lookahead
    pend = []
    acc = {+1: [np.zeros(NB), 0], -1: [np.zeros(NB), 0]}
    for t in range(T):
        eo = p["sig_o"] * rng.standard_normal(NO)
        probe = (t % 20 == 0)
        sgn = 0
        if probe:
            sgn = 1 if rng.random() < 0.5 else -1
            a = np.zeros(K); a[k] = sgn                       # replaces the action
        else:
            a = W_b @ (b + eo[:NB]) + W_u[:, 0] * u + p["sig_a"] * rng.standard_normal(K)
        ob = b + eo[:NB]
        if probe:
            pend.append([h, sgn, ob.copy()])
        drive = a if tau == 0 else aq[-tau]
        b = A_b @ b + B @ drive + G_b[:, 0] * u + p["sig_b"] * rng.standard_normal(NB)
        x = A_x @ x + G_x[:, 0] * u + p["sig_x"] * rng.standard_normal(NX)
        u = p["rho_u"] * u + p["sig_u"] * rng.standard_normal()
        aq.append(a); aq.pop(0)
        nxt = []
        for item in pend:
            item[0] -= 1
            if item[0] == 0:
                eo2 = p["sig_o"] * rng.standard_normal(NB)
                acc[item[1]][0] += (b + eo2) - item[2]
                acc[item[1]][1] += 1
            else:
                nxt.append(item)
        pend = nxt
    return acc[+1][0] / acc[+1][1] - acc[-1][0] / acc[-1][1], acc[+1][1], acc[-1][1]


for tau in (0, 2):
    for gs in (0.0, 1.0, 4.0):
        d, np_, nm = probe_contrast_mc(gs, tau)
        truth = 2 * base_params()["B"][:, 0]
        print(f"tau={tau} G_b scale={gs:>4}: contrast={d}  2*B[:,0]={truth}  "
              f"max err={np.max(np.abs(d-truth)):.4f}  (n+={np_}, n-={nm})")

# =====================================================================  C5
print(BAR)
print("C5  Delta_c population limit:  Delta_c/sqrt(n) = || S_a^{-1/2} [S_phi^post")
print("    (beta^post - beta^pre)]_a || / sigma_c   under E1 / E2 / E3.")
print(BAR)


def delta_c_limit(p_pre, p_post):
    m_pre = moments(p_pre)
    beta_pre, S_phi_pre, sig_pre = predictor(m_pre)
    m_post = moments(p_post)
    beta_post, S_phi_post, _ = predictor(m_post)
    d = S_phi_post @ (beta_post - beta_pre)          # E[phi r_c] under post law
    da = d[NO:NO + 3 * K, :]                          # action-lag block
    S_a = S_phi_pre[NO:NO + 3 * K, NO:NO + 3 * K]     # fit-split action geometry
    ev, V = np.linalg.eigh(S_a)
    ev = np.maximum(ev, 1e-12 * ev.max())
    Whit = V @ np.diag(ev ** -0.5) @ V.T
    return np.linalg.norm(Whit @ da, axis=0) / sig_pre     # per observed channel


def scen(tau, gb_scale, sig_o=0.05):
    def bp():
        q = base_params(); q["tau"] = tau; q["sig_o"] = sig_o
        q["G_b"] = gb_scale * base_params()["G_b"]
        return q
    pre = bp()
    e1 = bp(); e1["B"] = pre["B"].copy(); e1["B"][:, 0] = 0.0             # E1
    e2 = bp(); e2["G_b"] = 2.0 * pre["G_b"]                               # E2: G_b x2
    e2w = bp(); e2w["W_u"] = np.array([[0.40], [-0.90]])                  # E2': W_u change
    e3 = bp(); e3["B"] = pre["B"].copy(); e3["B"][:, 0] *= 0.5            # E3, gamma = 0.5
    return pre, {"E1 (lose act 0)": e1, "E2 (G_b x2)": e2,
                 "E2' (W_u change)": e2w, "E3 (gamma=0.5)": e3}


for tau in (0, 2):
    for gb_scale, tag in [(0.0, "G_b = 0  (regime C-)"), (1.0, "G_b != 0 (regime C+)")]:
      for sig_o in (0.0, 0.05):
        tag2 = tag + f"  sigma_o={sig_o}"
        pre, evs = scen(tau, gb_scale, sig_o)
        print(f"\n  tau={tau}  {tag2}   [per-channel Delta_c/sqrt(n)]")
        print(f"    {'event':20s} " + " ".join(f"b{j}    " for j in range(NB))
              + " " + " ".join(f"x{j}    " for j in range(NX)))
        for name, pp in evs.items():
            dl = delta_c_limit(pre, pp)
            print(f"    {name:20s} " + " ".join(f"{v:6.3f}" for v in dl))

# =====================================================================  C6
print("\n" + BAR)
print("C6  finite-sample scale: sd of the h=tau+1 increment vs the 2*B effect,")
print("    at p=0.05, W=500 steps, K=2  ->  25 units, ~6.25 per (k,sign) cell.")
print(BAR)
for tau in (0, 2):
    p = base_params(); p["tau"] = tau
    m = moments(p)
    Ss, C_o, Pi_o, Sv, A, Q = m["Ss"], m["C_o"], m["Pi_o"], m["Sv"], m["A"], m["Q"]
    S_oo = C_o @ Ss @ C_o.T + Pi_o @ Sv @ Pi_o.T
    h = tau + 1
    Ah = np.linalg.matrix_power(A, h)
    Ahm1 = np.linalg.matrix_power(A, h - 1)
    cov_h = C_o @ Ah @ Ss @ C_o.T + C_o @ Ahm1 @ m["L"] @ Sv @ Pi_o.T   # Cov(o_{t+h}, o_t)
    var_D = np.diag(S_oo) + np.diag(S_oo) - 2 * np.diag(cov_h)
    sd_D = np.sqrt(np.maximum(var_D, 0))[:NB]
    eff = 2 * np.abs(base_params()["B"][:, 0])
    se = sd_D * np.sqrt(1 / 6.25 + 1 / 6.25)
    print(f"tau={tau}: sd(D^{h}) body = {sd_D}, 2|B[:,0]| = {eff}")
    print(f"        SE(contrast) = {se},  SE/effect = "
          + " ".join(f"{s/e:.2f}" if e > 0 else "  inf" for s, e in zip(se, eff)))

# =====================================================================  C7
print(BAR)
print("C7  exogenous action variation: policy noise vs deliberate probe")
print(BAR)
p = base_params()
S_zeta = p["W_b"] @ (p["sig_o"] ** 2 * np.eye(NB)) @ p["W_b"].T + p["sig_a"] ** 2 * np.eye(K)
print(f"Cov(zeta) = W_b Sigma_eo W_b^T + sigma_a^2 I  diag = {np.diag(S_zeta)}")
print(f"  of which sigma_a^2 = {p['sig_a']**2:.5f}, policy-read obs noise = "
      f"{np.diag(p['W_b'] @ (p['sig_o']**2*np.eye(NB)) @ p['W_b'].T)}")
print(f"probe: variance 1.0 on fraction p/K = {0.05/K:.4f} of steps per actuator "
      f"-> {0.05/K:.4f} per step")
print(f"ratio probe:passive per step per actuator = "
      f"{(0.05/K)/np.diag(S_zeta)[0]:.2f} : 1")
print(BAR)
print("END OF CHECKS -- nothing above is a result.")
