"""Single-model, single-instance DIAGNOSTIC for comparator-spec.md v3 (D-11.2a).

NOT a result. One configuration seed, one episode seed, one implementation, no intervals.
Its only purpose is to check that the v3 statistic is computable as written on the frozen
generator and to give order-of-magnitude values for the caps in the parameter table.

Run from `executable-proofs/gate/`:
    /Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3 ../../superseded-specs/comparator-v3-diagnostic.py
"""
import sys, os, copy, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.abspath(os.path.join(HERE, "..", "executable-proofs", "gate"))
sys.path.insert(0, GATE)
import reference_generator as rg
from contract_ref import auc_pre_event_support, auc_prob_superiority

TAU_MAX, HORIZONS = 2, (1, 2, 3)
LAM_REL, W, Z_CAP = 1e-4, 500, 8.0
S_FLOOR, SIG_FLOOR, LAM_A, KAPPA_MIN = 1e-8, 1e-6, 1e-6, 1e-4
N_PRED_FIT, FIT_EP0 = 20, 900
EVENT_T, EPISODE_LEN = 1000, 2000


def features(o, a, C, K):
    """phi rows for transitions t = 0..T-1 of one episode; lags zero-filled at the boundary."""
    T = a.shape[0]
    phi = np.zeros((T, C + 3 * K + 1))
    phi[:, :C] = o[:T]
    phi[:, C:C + K] = a
    phi[1:, C + K:C + 2 * K] = a[:-1]
    phi[2:, C + 2 * K:C + 3 * K] = a[:-2]
    phi[:, -1] = 1.0
    return phi, o[1:T + 1]


def fit_predictor(inst, ep0=FIT_EP0, n_ep=N_PRED_FIT):
    C, K = inst.C, inst.cfg["K"]
    P, Y = [], []
    for j in range(n_ep):
        r = inst.run(EPISODE_LEN, ep=ep0 + j)
        p, y = features(r["o"], r["a"], C, K)
        P.append(p); Y.append(y)
    phi = np.vstack(P); Y = np.vstack(Y); n = len(Y)
    m = phi[:, :-1].mean(0); s = np.maximum(phi[:, :-1].std(0, ddof=0), S_FLOOR)
    Xt = np.hstack([(phi[:, :-1] - m) / s, np.ones((n, 1))])
    D = np.diag([1.0] * (C + 3 * K) + [0.0]); lam = LAM_REL * n
    Bt = np.linalg.solve(Xt.T @ Xt + lam * D, Xt.T @ Y)
    beta_raw = Bt[:-1] / s[:, None]; b_raw = Bt[-1] - (m / s) @ Bt[:-1]
    R = Y - Xt @ Bt
    mu = R.mean(0); sd = np.maximum(R.std(0, ddof=1), SIG_FLOOR)
    bo = beta_raw[:C]; ba = [beta_raw[C + j * K: C + (j + 1) * K] for j in (0, 1, 2)]
    J = np.zeros((K, C)); l = np.zeros(C)
    for h in HORIZONS:
        J = J @ bo + ba[h - 1]; l = np.maximum(l, np.linalg.norm(J, axis=0) / sd)
    # action-feature standardisation and whitener (D-11.2a)
    ma, sa = m[C:C + 3 * K], s[C:C + 3 * K]
    At = (phi[:, C:C + 3 * K] - ma) / sa
    Sig = (At.T @ At) / n + LAM_A * np.eye(3 * K)
    ev, V = np.linalg.eigh(Sig)
    keep = ev >= KAPPA_MIN * ev.max()
    Wa = (V[:, keep] / np.sqrt(ev[keep])).T          # q x 3K, rows = lambda^-1/2 v^T
    return dict(beta_raw=beta_raw, b_raw=b_raw, mu=mu, sd=sd, l=l, ma=ma, sa=sa, Wa=Wa,
                q=int(keep.sum()), cond=float(ev.max() / ev.min()), sd_med=float(np.median(sd)))


def score_episode(inst, fit, ep, event=None):
    """Return Delta_c(t) at every step of one episode, plus the standardised innovations."""
    C, K = inst.C, inst.cfg["K"]
    r = inst.run(EPISODE_LEN, ep=ep, event_t=(EVENT_T if event else None), event=event)
    phi, Y = features(r["o"], r["a"], C, K)
    res = Y - (phi[:, :-1] @ fit["beta_raw"] + fit["b_raw"])
    rt = np.clip((res - fit["mu"]) / fit["sd"], -Z_CAP, Z_CAP)              # T x C
    at = (phi[:, C:C + 3 * K] - fit["ma"]) / fit["sa"]
    av = at @ fit["Wa"].T                                                    # T x q
    T = rt.shape[0]; q = av.shape[1]
    Delta = np.zeros((T, C))
    for t in range(T):
        t_ep = t + 1; n = min(W, t_ep); lo = t_ep - n
        chat = (rt[lo:t_ep].T @ av[lo:t_ep]) / n                             # C x q
        Delta[t] = np.sqrt(n) * np.linalg.norm(chat, axis=1)
    return Delta, rt


def report(tag, inst, fit, Delta_ff, Delta_ev, pre, post):
    print(f"\n--- {tag} ---")
    print("  fit: q(retained) =", fit["q"], " cond(Sigma_a) = %.3g" % fit["cond"],
          " median sd_c = %.4f" % fit["sd_med"])
    print("  l_c            :", np.array2string(fit["l"], precision=2, max_line_width=200))
    print("  pre-event S    :", pre.astype(int))
    print("  post-event S   :", post.astype(int))
    for off, t in ((200, 1200), (500, 1500), (1000, 1999)):
        d_ff, d_ev = Delta_ff[t], Delta_ev[t]
        raw = -d_ev; sec = fit["l"] - d_ev
        print(f"  offset {off:>4} (read t={t}):")
        print("      Delta fault-free  max %7.2f  median %6.2f  on-support %s"
              % (d_ff.max(), np.median(d_ff), np.array2string(d_ff[pre], precision=1)))
        print("      Delta post-event  max %7.2f  median %6.2f  on-support %s"
              % (d_ev.max(), np.median(d_ev), np.array2string(d_ev[pre], precision=1)))
        print("      AUC_pre_event_support(-Delta) = %.3f   AUC_full(l - Delta) = %.3f   AUC_full(l) = %.3f"
              % (auc_pre_event_support(raw, pre, post), auc_prob_superiority(sec, post),
                 auc_prob_superiority(fit["l"], post)))


def main():
    t0 = time.time()
    print("SINGLE-MODEL, SINGLE-INSTANCE DIAGNOSTIC (not a result). numpy", np.__version__)
    base = rg.draw_certified({}, 0)
    print("draw_certified({}, 0): n_resamples =", base.n_resamples, " certification:", base.certification)
    pre = base.S_obs_pre_event().copy()
    post_inst = copy.deepcopy(base); post_inst.apply_event(("actuator_loss", 0))
    post = post_inst.S_obs().copy()
    print("lost set (pre & ~post):", np.where(pre & ~post)[0], " assign:", base.assign[pre & ~post])

    # ---- confounder PRESENT ----
    fit_inst = copy.deepcopy(base)                       # fault-free, no event ever applied
    fit = fit_predictor(fit_inst)
    ff = copy.deepcopy(base); D_ff, _ = score_episode(ff, fit, ep=0, event=None)
    ev = copy.deepcopy(base); D_ev, _ = score_episode(ev, fit, ep=0, event=("actuator_loss", 0))
    report("confounder PRESENT", base, fit, D_ff, D_ev, pre, post)

    # ---- confounder ABSENT: same draw, same noise streams, G = 0, separate fit ----
    absent = copy.deepcopy(base); absent.G[:] = 0.0
    fit_a = fit_predictor(copy.deepcopy(absent))
    ff_a = copy.deepcopy(absent); D_ff_a, _ = score_episode(ff_a, fit_a, ep=0, event=None)
    ev_a = copy.deepcopy(absent); D_ev_a, _ = score_episode(ev_a, fit_a, ep=0, event=("actuator_loss", 0))
    pre_a = absent.S_obs().copy()
    post_a_inst = copy.deepcopy(absent); post_a_inst.apply_event(("actuator_loss", 0))
    report("confounder ABSENT (G=0, refit)", absent, fit_a, D_ff_a, D_ev_a, pre_a, post_a_inst.S_obs())

    # ---- which lag slot carries the signal (tau = 0 vs tau = 2) ----
    for tau in (0, 2):
        inst = rg.draw_certified({"tau": tau}, 0)
        f = fit_predictor(copy.deepcopy(inst))
        C, K = inst.C, inst.cfg["K"]
        e = copy.deepcopy(inst); r = e.run(EPISODE_LEN, ep=0, event_t=EVENT_T, event=("actuator_loss", 0))
        phi, Y = features(r["o"], r["a"], C, K)
        res = Y - (phi[:, :-1] @ f["beta_raw"] + f["b_raw"])
        rt = np.clip((res - f["mu"]) / f["sd"], -Z_CAP, Z_CAP)
        at = (phi[:, C:C + 3 * K] - f["ma"]) / f["sa"]
        lo, hi = 1000, 1500
        cbar = (rt[lo:hi].T @ at[lo:hi]) / (hi - lo)          # C x 3K, UNwhitened, post-event window
        pre_i = inst.S_obs_pre_event(); post_i = copy.deepcopy(inst); post_i.apply_event(("actuator_loss", 0))
        lost = np.where(pre_i & ~post_i.S_obs())[0]
        print(f"\n--- lag-slot attribution, tau = {tau} (post-event window t=1000..1499) ---")
        print("   slots = [a_t k0, a_t k1, a_t-1 k0, a_t-1 k1, a_t-2 k0, a_t-2 k1]")
        for c in lost:
            print("   lost channel %2d: c_hat = %s" % (c, np.array2string(cbar[c], precision=3)))
        keep = np.where(pre_i & post_i.S_obs())[0]
        print("   retained channel %2d: c_hat = %s" % (keep[0], np.array2string(cbar[keep[0]], precision=3)))

    # ---- static fit-time-constant control on the D-11.1 primary ----
    print("\n--- static fit-time-constant control (l as raw_support) on auc_pre_event_support ---")
    print("   present: %.3f   absent: %.3f   (tau = 0, seed 0)"
          % (auc_pre_event_support(fit["l"], pre, post), auc_pre_event_support(fit_a["l"], pre_a, post_a_inst.S_obs())))

    # ---- tau = 2 primary, plus caps and degeneracy inputs ----
    for tau in (0, 2):
        inst = rg.draw_certified({"tau": tau}, 0)
        f = fit_predictor(copy.deepcopy(inst))
        pre_i = inst.S_obs_pre_event().copy()
        pi = copy.deepcopy(inst); pi.apply_event(("actuator_loss", 0)); post_i = pi.S_obs().copy()
        Dff, _ = score_episode(copy.deepcopy(inst), f, ep=0, event=None)
        Dev, _ = score_episode(copy.deepcopy(inst), f, ep=0, event=("actuator_loss", 0))
        print(f"\n--- tau = {tau}, seed 0: primary and caps ---")
        print("   q = %d  cond(Sigma_a) = %.4g   n_lost = %d" % (f["q"], f["cond"], int((pre_i & ~post_i).sum())))
        print("   AUC_pre_event_support(-Delta): " + "  ".join(
            "offset %d: %.3f" % (o, auc_pre_event_support(-Dev[t], pre_i, post_i)) for o, t in ((200, 1200), (500, 1500), (1000, 1999))))
        print("   static l control on the same primary: %.3f" % auc_pre_event_support(f["l"], pre_i, post_i))
        warm = slice(30, None)
        print("   Delta fault-free over the whole episode (t_ep >= 30): median %.2f  max %.2f  (sqrt(3K) = %.3f)"
              % (np.median(Dff[warm]), Dff[warm].max(), np.sqrt(3 * inst.cfg["K"])))
        print("   Delta post-event   over the whole episode: max %.1f" % Dev[warm].max())
        pads = inst.assign < 0
        print("   sd_c: median %.4f  pads %s  min %.4f  (degeneracy needs sd < 1e-2 * median = %.5f)"
              % (np.median(f["sd"]), np.array2string(f["sd"][pads], precision=4), f["sd"].min(), 1e-2 * np.median(f["sd"])))
        print("   l on pads: %s" % np.array2string(f["l"][pads], precision=3))

    # ---- rank handling under exact collinearity ----
    n = 4000; rngz = np.random.default_rng(0)
    A = rngz.normal(size=(n, 6)); A[:, 3] = A[:, 0]                    # exactly collinear lag column
    A = (A - A.mean(0)) / A.std(0, ddof=0)
    Sig = (A.T @ A) / n + LAM_A * np.eye(6)
    ev, V = np.linalg.eigh(Sig)
    print("\n--- rank handling, exactly collinear action column ---")
    print("   eigenvalues:", np.array2string(ev, precision=8))
    for kap in (1e-8, 1e-4):
        keep = ev >= kap * ev.max()
        print("   kappa_min = %g -> cutoff %.3g, retained q = %d, largest whitening factor %.4g"
              % (kap, kap * ev.max(), int(keep.sum()), 1 / np.sqrt(ev[keep].min())))

    print("\nelapsed %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
