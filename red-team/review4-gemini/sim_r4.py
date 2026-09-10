"""Independent simulation script for Stage 0A Review 4.
Pure NumPy implementation of BOTH arms (sequential IBD draft 3 and comparator draft 1)
from the normative specifications alone on Contract-B SCM instances.
Runs Family L (tau=0, Nx in {10, 30}), Family N, tau=2, and Nx=100.
"""

import numpy as np

def rankdata_midranks(a):
    a = np.asarray(a)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), dtype=float)
    sorted_a = a[order]
    n = len(a)
    i = 0
    while i < n:
        j = i
        while j < n and sorted_a[j] == sorted_a[i]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        ranks[order[i:j]] = avg_rank
        i = j
    return ranks

def compute_roc_auc(scores, labels):
    pos = scores[labels]
    neg = scores[~labels]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    comp = np.subtract.outer(pos, neg)
    u_stat = np.sum(comp > 0) + 0.5 * np.sum(comp == 0)
    return float(u_stat / (len(pos) * len(neg)))

def make_contract_b_instance(seed=0, family="L", tau=0, Nx=10, confounded=True):
    rng = np.random.default_rng(seed)
    Nb = 4
    Nd = 2
    Nw = 4
    K = 2
    nu = 2
    
    Ab = np.diag([0.65, 0.55, 0.60, 0.50])
    B0 = np.array([
        [0.60, 0.00],
        [0.35, 0.00],
        [0.00, 0.55],
        [0.00, 0.35]
    ])
    
    Cd = np.array([
        [0.35, 0.00, 0.00, 0.00],
        [0.00, 0.00, 0.35, 0.00]
    ])
    Ad = np.diag([0.50, 0.45])
    Aw = np.diag([0.60, 0.55, 0.50, 0.45])
    Ax = np.diag(np.linspace(0.55, 0.75, Nx))
    
    G = np.zeros((Nx, nu))
    n_conf = Nx // 2
    if confounded:
        for i in range(n_conf):
            G[i, i % nu] = 0.65
            
    rho_u = 0.8
    
    Wu = np.zeros((K, nu))
    Wu[0, 0] = 0.80
    Wu[1, 1] = -0.60

    # 14 base channels + Nx distractors
    C = 14 + Nx
    Nz = Nb + Nd + Nw + Nx
    
    assign = np.full(C, -1, dtype=int)
    assign[0:4] = np.arange(0, 4)
    assign[4:6] = np.arange(4, 6)
    assign[6:10] = np.arange(6, 10)
    assign[10] = 0 # copy b0
    assign[11] = 4 # copy d0
    assign[14:14+Nx] = np.arange(10, 10+Nx)
    
    gain = np.ones(C)
    avail = np.ones(C, dtype=bool)
    
    # Ground truth support post actuator 0 loss:
    gt_support_post = np.zeros(C, dtype=bool)
    if tau == 0:
        gt_support_post[2] = True # b2
        gt_support_post[3] = True # b3
        gt_support_post[5] = True # d1
    elif tau == 2:
        gt_support_post[2] = True
        gt_support_post[3] = True
    
    params = dict(
        family=family, tau=tau, Nx=Nx, C=C, Nz=Nz, Nb=Nb, Nd=Nd, Nw=Nw, K=K, nu=nu,
        Ab=Ab, B0=B0, Cd=Cd, Ad=Ad, Aw=Aw, Ax=Ax, G=G, rho_u=rho_u, Wu=Wu,
        assign=assign, gain=gain, avail=avail, gt_support_post=gt_support_post,
        confounded=confounded
    )
    return params

def run_episode(params, rng, probe_arm=False, event_t=1000, episode_len=2000):
    Nb, Nd, Nw, Nx, K, nu, C = params['Nb'], params['Nd'], params['Nw'], params['Nx'], params['K'], params['nu'], params['C']
    tau = params['tau']
    family = params['family']
    
    b = np.zeros(Nb)
    d = np.zeros(Nd)
    w = np.zeros(Nw)
    x = np.zeros(Nx)
    u = np.zeros(nu)
    
    action_ring = [np.zeros(K) for _ in range(tau + 1)]
    B_curr = params['B0'].copy()
    
    obs_history = []
    action_history = []
    probe_flag_history = []
    probe_info_history = {}
    
    used_probes = 0
    t_last_probe = -20
    o = np.zeros(C)
    
    for t in range(1, episode_len + 1):
        if event_t is not None and t >= event_t:
            B_curr[:, 0] = 0.0
            
        u = params['rho_u'] * u + rng.normal(0, 1.0, size=nu)
        
        # Closed loop task policy: Wo feedback + Wu context
        a_task = np.array([
            -0.25 * o[0] - 0.15 * o[1] + params['Wu'][0] @ u,
            -0.25 * o[2] - 0.15 * o[3] + params['Wu'][1] @ u
        ]) + rng.normal(0, 0.1, size=K)
        a_task = np.clip(a_task, -2.0, 2.0)
        
        is_probe = False
        applied_a = a_task
        if probe_arm:
            if (used_probes + 1 <= int(0.05 * t)) and (t - t_last_probe >= 20):
                is_probe = True
                used_probes += 1
                t_last_probe = t
                k_probe = rng.choice(K)
                sgn_probe = rng.choice([1.0, -1.0])
                applied_a = np.zeros(K)
                applied_a[k_probe] = sgn_probe
                probe_info_history[t] = (k_probe, sgn_probe)
                
        probe_flag_history.append(is_probe)
        action_history.append(applied_a.copy())
        
        action_ring.append(applied_a.copy())
        a_delayed = action_ring.pop(0)
        
        if family == "L":
            b_next = params['Ab'] @ b + B_curr @ a_delayed + rng.normal(0, 0.1, size=Nb)
        else:
            b_next = params['Ab'] @ b + np.tanh(B_curr @ a_delayed / 1.0) * 1.0 + 0.1 * np.clip(b * b, -4.0, 4.0) + rng.normal(0, 0.1, size=Nb)
            
        d_next = params['Ad'] @ d + params['Cd'] @ b + rng.normal(0, 0.1, size=Nd)
        w_next = params['Aw'] @ w + rng.normal(0, 0.1, size=Nw)
        x_next = params['Ax'] @ x + params['G'] @ u + rng.normal(0, 0.1, size=Nx)
        
        b, d, w, x = b_next, d_next, w_next, x_next
        z = np.concatenate([b, d, w, x])
        
        o = np.zeros(C)
        for c in range(C):
            j = params['assign'][c]
            if j >= 0 and params['avail'][c]:
                o[c] = params['gain'][c] * z[j]
        o += rng.normal(0, 0.05, size=C)
        obs_history.append(o.copy())
        
    return {
        'obs': np.array(obs_history),
        'actions': np.array(action_history),
        'probe_flags': np.array(probe_flag_history),
        'probe_info': probe_info_history
    }

# ----------------- Arm 1: Sequential IBD (Draft 3) -----------------
def run_seq_ibd_at_offset500(ep, params, W_steps=500, n_min_sign=3, z_cap=8.0):
    obs = ep['obs']
    probe_info = ep['probe_info']
    C = params['C']
    K = params['K']
    HSET = [1, 2, 3]
    
    tp_star = 1480
    window_anchors = [tp for tp in probe_info if (tp > tp_star - W_steps and tp <= tp_star)]
    
    a_scores = np.zeros(C)
    
    for c in range(C):
        zz = []
        for k in range(K):
            for h in HSET:
                Gp = []
                Gm = []
                for tp in window_anchors:
                    k_p, sgn_p = probe_info[tp]
                    if k_p == k:
                        D = obs[tp + h - 1, c] - obs[tp - 1, c]
                        if sgn_p > 0:
                            Gp.append(D)
                        else:
                            Gm.append(D)
                            
                np_len = len(Gp)
                nm_len = len(Gm)
                if min(np_len, nm_len) < n_min_sign:
                    continue
                    
                vals = np.array(Gp + Gm)
                N = np_len + nm_len
                ranks = rankdata_midranks(vals)
                R_plus = np.sum(ranks[:np_len])
                
                U = R_plus - np_len * (np_len + 1) / 2.0
                mu_U = np_len * nm_len / 2.0
                
                _, counts = np.unique(vals, return_counts=True)
                tie_sum = np.sum(counts**3 - counts) / 12.0
                
                var_U = (np_len * nm_len / (N * (N - 1.0))) * ((N**3 - N) / 12.0 - tie_sum)
                if var_U <= 1e-12:
                    continue
                    
                sigma_U = np.sqrt(var_U)
                z = np.clip((U - mu_U) / sigma_U, -z_cap, z_cap)
                zz.append(abs(z))
                
        if len(zz) > 0:
            a_scores[c] = max(zz)
        else:
            a_scores[c] = 0.0
            
    return a_scores

# ----------------- Arm 2: Passive Comparator -----------------
def fit_comparator(params, cal_episodes):
    X_rows = []
    Y_rows = []
    C = params['C']
    K = params['K']
    
    for ep in cal_episodes:
        obs = ep['obs']
        actions = ep['actions']
        T = len(obs)
        for t in range(T - 1):
            X_rows.append(np.concatenate([obs[t], actions[t], [1.0]]))
            Y_rows.append(obs[t + 1])
            
    X = np.array(X_rows)
    Y = np.array(Y_rows)
    
    XtX = X.T @ X
    lam = 1e-4 * np.trace(XtX) / (C + K)
    D = np.eye(C + K + 1)
    D[-1, -1] = 0.0
    
    beta = np.linalg.solve(XtX + lam * D, X.T @ Y)
    
    R = Y - X @ beta
    mu_c = np.mean(R, axis=0)
    sd_c = np.maximum(np.std(R, axis=0, ddof=1), 1e-6)
    degen = np.std(R, axis=0, ddof=1) < 1e-3
    
    beta_a = beta[C:C+K, :]
    l_c = np.linalg.norm(beta_a, axis=0) / sd_c
    
    return {
        'beta': beta,
        'mu_c': mu_c,
        'sd_c': sd_c,
        'degen': degen,
        'l_c': l_c
    }

def run_comparator_at_offset500(ep, comp_fit, params, W=500, q_cap=40.0):
    obs = ep['obs']
    actions = ep['actions']
    C = params['C']
    beta = comp_fit['beta']
    mu_c = comp_fit['mu_c']
    sd_c = comp_fit['sd_c']
    degen = comp_fit['degen']
    l_c = comp_fit['l_c']
    
    t_target = 1500
    rt_window = []
    for step in range(t_target - W, t_target):
        feat = np.concatenate([obs[step], actions[step], [1.0]])
        r = obs[step + 1] - feat @ beta
        rt = np.clip((r - mu_c) / sd_c, -8.0, 8.0)
        rt_window.append(rt)
        
    rt_window = np.array(rt_window)
    n = len(rt_window)
    mean_rt = np.mean(rt_window, axis=0)
    shift = np.abs(np.sqrt(n) * mean_rt)
    
    q_c = np.clip(l_c - shift, -q_cap, q_cap)
    q_c[degen] = -q_cap
    return q_c

def evaluate_cell(family="L", tau=0, Nx=10, n_seeds=20):
    auc_ibd_pres = []
    auc_ibd_abs = []
    auc_comp_pres = []
    auc_comp_abs = []
    
    # Fit comparator per cell per comparator-spec.md section 1
    # 1. Fault-free present split
    p_cal_pres = make_contract_b_instance(seed=999, family=family, tau=tau, Nx=Nx, confounded=True)
    cal_rng_pres = np.random.default_rng(12345)
    cal_eps_pres = [run_episode(p_cal_pres, cal_rng_pres, probe_arm=False, event_t=None) for _ in range(20)]
    comp_fit_pres = fit_comparator(p_cal_pres, cal_eps_pres)
    
    # 2. Fault-free absent split
    p_cal_abs = make_contract_b_instance(seed=999, family=family, tau=tau, Nx=Nx, confounded=False)
    cal_rng_abs = np.random.default_rng(54321)
    cal_eps_abs = [run_episode(p_cal_abs, cal_rng_abs, probe_arm=False, event_t=None) for _ in range(20)]
    comp_fit_abs = fit_comparator(p_cal_abs, cal_eps_abs)
    
    for s in range(n_seeds):
        # Confounder present
        p_pres = make_contract_b_instance(seed=s, family=family, tau=tau, Nx=Nx, confounded=True)
        rng_pres_ibd = np.random.default_rng(1000 + s)
        ep_pres_ibd = run_episode(p_pres, rng_pres_ibd, probe_arm=True, event_t=1000)
        
        rng_pres_comp = np.random.default_rng(1000 + s)
        ep_pres_comp = run_episode(p_pres, rng_pres_comp, probe_arm=False, event_t=1000)
        
        a_pres = run_seq_ibd_at_offset500(ep_pres_ibd, p_pres)
        q_pres = run_comparator_at_offset500(ep_pres_comp, comp_fit_pres, p_pres)
        
        gt_pres = p_pres['gt_support_post']
        auc_ibd_pres.append(compute_roc_auc(a_pres, gt_pres))
        auc_comp_pres.append(compute_roc_auc(q_pres, gt_pres))
        
        # Confounder absent
        p_abs = make_contract_b_instance(seed=s, family=family, tau=tau, Nx=Nx, confounded=False)
        rng_abs_ibd = np.random.default_rng(1000 + s)
        ep_abs_ibd = run_episode(p_abs, rng_abs_ibd, probe_arm=True, event_t=1000)
        
        rng_abs_comp = np.random.default_rng(1000 + s)
        ep_abs_comp = run_episode(p_abs, rng_abs_comp, probe_arm=False, event_t=1000)
        
        a_abs = run_seq_ibd_at_offset500(ep_abs_ibd, p_abs)
        q_abs = run_comparator_at_offset500(ep_abs_comp, comp_fit_abs, p_abs)
        
        gt_abs = p_abs['gt_support_post']
        auc_ibd_abs.append(compute_roc_auc(a_abs, gt_abs))
        auc_comp_abs.append(compute_roc_auc(q_abs, gt_abs))
        
    delta_pres = np.array(auc_ibd_pres) - np.array(auc_comp_pres)
    delta_abs = np.array(auc_ibd_abs) - np.array(auc_comp_abs)
    benefit = delta_pres - delta_abs
    
    return {
        'auc_ibd_pres': float(np.mean(auc_ibd_pres)),
        'auc_ibd_abs': float(np.mean(auc_ibd_abs)),
        'auc_comp_pres': float(np.mean(auc_comp_pres)),
        'auc_comp_abs': float(np.mean(auc_comp_abs)),
        'delta_pres': float(np.mean(delta_pres)),
        'delta_abs': float(np.mean(delta_abs)),
        'benefit': float(np.mean(benefit)),
        'benefit_std': float(np.std(benefit, ddof=1)),
        'benefit_ci': (float(np.mean(benefit) - 1.96 * np.std(benefit, ddof=1)/np.sqrt(n_seeds)),
                       float(np.mean(benefit) + 1.96 * np.std(benefit, ddof=1)/np.sqrt(n_seeds)))
    }

if __name__ == "__main__":
    print("=== TASK 1: End-to-end Reproducibility ===")
    res_l10 = evaluate_cell(family="L", tau=0, Nx=10, n_seeds=20)
    print("Family L, tau=0, Nx=10:")
    for k, v in res_l10.items(): print(f"  {k}: {v}")
    
    res_l30 = evaluate_cell(family="L", tau=0, Nx=30, n_seeds=20)
    print("\nFamily L, tau=0, Nx=30:")
    for k, v in res_l30.items(): print(f"  {k}: {v}")
    
    print("\n=== TASK 3: Untested Regions ===")
    print("1. Family N (tau=0, Nx=10):")
    res_n10 = evaluate_cell(family="N", tau=0, Nx=10, n_seeds=20)
    for k, v in res_n10.items(): print(f"  {k}: {v}")

    print("\n2. tau=2 (Family L, Nx=10):")
    res_tau2 = evaluate_cell(family="L", tau=2, Nx=10, n_seeds=20)
    for k, v in res_tau2.items(): print(f"  {k}: {v}")

    print("\n3. Nx=100 (Family L, tau=0):")
    res_nx100 = evaluate_cell(family="L", tau=0, Nx=100, n_seeds=20)
    for k, v in res_nx100.items(): print(f"  {k}: {v}")
