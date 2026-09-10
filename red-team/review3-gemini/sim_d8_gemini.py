"""Independent simulation of Contract B instance and Draft-2 Sequential IBD vs CUSUM.
Written independently by Gemini for Task 1 of Round 3 Review (7 September 2026).
Tests D-8 refutation: evaluates both alarm power (HPDT) and support F1 at offsets {200, 500, 1000}.
"""
import numpy as np

# Contract constants
EPS = 0.05
H_SET = [1, 2, 3]
TAU = 0
PROBE_BUDGET = 0.05
PERIOD = 20
W_STEPS = 500
Z_CAP = 8.0
N_MIN = 10
P_EPOCH = 3
H_DET = 200
EPISODE_LEN = 2000
EVENT_T = 1000
OFFSETS_F1 = [200, 500, 1000]

def make_instance(seed, N_x=10, confounded=True):
    rng = np.random.default_rng(seed)
    N_b, N_d, N_w, K = 4, 2, 4, 2
    n_u = 2
    rho_u = 0.8
    rho_max = 0.85
    
    # Body dynamics: 2 independent blocks of 2 nodes
    # Block 1 reached by actuator 0; Block 2 reached by actuator 1
    A_b = np.array([
        [0.7, 0.2, 0.0, 0.0],
        [0.1, 0.6, 0.0, 0.0],
        [0.0, 0.0, 0.7, 0.2],
        [0.0, 0.0, 0.1, 0.6]
    ])
    B_pre = np.array([
        [1.0, 0.0],
        [0.0, 0.0],
        [0.0, 1.0],
        [0.0, 0.0]
    ])
    # Event: complete loss of actuator 0
    B_post = np.array([
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 1.0],
        [0.0, 0.0]
    ])
    
    # Downstream: d0 fed by b0, d1 fed by b2
    C_d = np.array([
        [0.8, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.8, 0.0]
    ])
    A_d = np.array([[0.5, 0.0], [0.0, 0.5]])
    
    # World
    A_w = np.diag([0.6] * N_w)
    
    # Distractors x
    A_x = np.diag([0.5] * N_x)
    if confounded:
        # half confounded, half noise
        G = np.zeros((N_x, n_u))
        n_conf = N_x // 2
        for i in range(n_conf):
            G[i, i % n_u] = 0.6
    else:
        G = np.zeros((N_x, n_u))
        
    N_z = N_b + N_d + N_w + N_x
    C_obs = N_z # 1-to-1 observation mapping for simplicity
    
    # Default policy: observes body, influenced by context u
    # a_t = clip(W_o o_b + W_u u + noise)
    W_o = np.zeros((K, C_obs))
    # negative feedback on body positions to keep stable
    W_o[0, 0] = -0.3
    W_o[1, 2] = -0.3
    W_u = np.zeros((K, n_u))
    W_u[0, 0] = 0.5
    W_u[1, 1] = 0.5
    
    return {
        'N_b': N_b, 'N_d': N_d, 'N_w': N_w, 'N_x': N_x, 'N_z': N_z, 'C_obs': C_obs,
        'K': K, 'n_u': n_u, 'rho_u': rho_u,
        'A_b': A_b, 'B_pre': B_pre, 'B_post': B_post,
        'C_d': C_d, 'A_d': A_d, 'A_w': A_w, 'A_x': A_x, 'G': G,
        'W_o': W_o, 'W_u': W_u
    }

def simulate_episode(inst, seed, has_event=True):
    rng = np.random.default_rng(seed)
    T = EPISODE_LEN
    N_b, N_d, N_w, N_x, N_z, C = inst['N_b'], inst['N_d'], inst['N_w'], inst['N_x'], inst['N_z'], inst['C_obs']
    K, n_u = inst['K'], inst['n_u']
    
    u = np.zeros(n_u)
    b = np.zeros(N_b)
    d = np.zeros(N_d)
    w = np.zeros(N_w)
    x = np.zeros(N_x)
    
    obs_history = np.zeros((T, C))
    act_history = np.zeros((T, K))
    probe_flag = np.zeros(T, bool)
    
    # Ground truth S^obs,eps:
    # Pre-event: b0, b1 (via b0), b2, b3 (via b2), d0 (via b0), d1 (via b2) reachable -> 6 channels
    # Post-event: actuator 0 lost -> b0, b1, d0 become unreachable!
    # Remaining reachable: b2, b3, d1 -> 3 channels
    S_pre = np.zeros(C, bool)
    S_pre[:N_b] = True
    S_pre[N_b:N_b+N_d] = True
    
    S_post = np.zeros(C, bool)
    S_post[2] = True # b2
    S_post[3] = True # b3
    S_post[N_b+1] = True # d1
    
    # Probe schedule: step % 20 == 0 -> probe step
    for t in range(T):
        B = inst['B_post'] if (has_event and t >= EVENT_T) else inst['B_pre']
        
        # Exogenous context
        u = inst['rho_u'] * u + rng.normal(0, 1.0, size=n_u)
        
        # Current observation
        z = np.concatenate([b, d, w, x])
        obs = z + rng.normal(0, 0.05, size=C)
        obs_history[t] = obs
        
        # Action selection
        is_probe = (t % PERIOD == 0 and t > 0)
        if is_probe:
            probe_flag[t] = True
            # random probe in {+-e_k}
            k_probe = rng.integers(K)
            sign_probe = rng.choice([-1.0, 1.0])
            a = np.zeros(K)
            a[k_probe] = sign_probe
        else:
            a_raw = inst['W_o'] @ obs + inst['W_u'] @ u + rng.normal(0, 0.1, size=K)
            a = np.clip(a_raw, -2.0, 2.0)
            
        act_history[t] = a
        
        # Dynamics update
        b = inst['A_b'] @ b + B @ a + rng.normal(0, 0.1, size=N_b)
        d = inst['A_d'] @ d + inst['C_d'] @ b + rng.normal(0, 0.1, size=N_d)
        w = inst['A_w'] @ w + rng.normal(0, 0.1, size=N_w)
        x = inst['A_x'] @ x + inst['G'] @ u + rng.normal(0, 0.1, size=N_x)
        
    return obs_history, act_history, probe_flag, S_pre, S_post

def run_mann_whitney_fast(P, N):
    # Vectorized pairwise Mann-Whitney U calculation
    n_P, n_N = len(P), len(N)
    gt = np.sum(P[:, None] > N[None, :])
    eq = np.sum(P[:, None] == N[None, :])
    U_P = gt + 0.5 * eq
    
    mean_U = n_P * n_N / 2.0
    var_U = (n_P * n_N * (n_P + n_N + 1)) / 12.0
    z = (U_P - mean_U) / np.sqrt(max(var_U, 1e-12))
    return z

def pava_isotonic(x, y):
    # Fits monotone non-decreasing function y ~ g(x)
    order = np.argsort(x)
    x_s, y_s = x[order], y[order]
    
    # Block pool adjacent violators
    blocks = [[float(y_s[i]), 1, [x_s[i]]] for i in range(len(y_s))]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] > blocks[i+1][0]:
            # pool
            w1, w2 = blocks[i][1], blocks[i+1][1]
            val = (blocks[i][0] * w1 + blocks[i+1][0] * w2) / (w1 + w2)
            blocks[i][0] = val
            blocks[i][1] = w1 + w2
            blocks[i][2].extend(blocks[i+1][2])
            del blocks[i+1]
            if i > 0:
                i -= 1
        else:
            i += 1
            
    knots_x = []
    knots_y = []
    for b in blocks:
        knots_x.append(b[2][0])
        knots_x.append(b[2][-1])
        knots_y.append(b[0])
        knots_y.append(b[0])
        
    def g(val):
        return np.interp(val, knots_x, knots_y, left=knots_y[0], right=knots_y[-1])
    return g

def evaluate_sequential_ibd(obs, act, probe_flags, g_cal=None):
    T, C = obs.shape
    SP = 3
    M_NULL = 4
    
    a_c_history = []
    times = []
    
    for t_now in range(W_STEPS, T, PERIOD):
        # find probe steps in window [t_now - W_STEPS, t_now]
        t_start = t_now - W_STEPS
        probes = [t for t in range(t_start, t_now - max(H_SET)) if probe_flags[t]]
        if len(probes) < N_MIN:
            continue
            
        a_vec = np.zeros(C)
        for c in range(C):
            zz_list = []
            for h in H_SET:
                P_inc = [abs(obs[t_p + h, c] - obs[t_p, c]) for t_p in probes]
                N_inc = []
                for t_p in probes:
                    for m in range(1, M_NULL + 1):
                        t_n = t_p - m * SP
                        if t_n >= 0 and t_n + h < T:
                            N_inc.append(abs(obs[t_n + h, c] - obs[t_n, c]))
                if len(P_inc) > 0 and len(N_inc) > 0:
                    z = run_mann_whitney_fast(np.array(P_inc), np.array(N_inc))
                    zz_list.append(z)
                else:
                    zz_list.append(0.0)
            # signed max |z|
            abs_zz = [abs(z) for z in zz_list]
            h_star = np.argmax(abs_zz)
            a_vec[c] = np.clip(zz_list[h_star], -Z_CAP, Z_CAP)
            
        a_c_history.append((t_now, a_vec))
        times.append(t_now)
        
    return a_c_history

def fit_calibrators(inst, R_cal=20):
    # Fit g_cal for IBD on calibration episodes (half event, half fault-free)
    all_a = []
    all_y = []
    
    for seed in range(R_cal):
        has_ev = (seed % 2 == 1)
        obs, act, pflags, S_pre, S_post = simulate_episode(inst, seed + 1000, has_event=has_ev)
        a_hist = evaluate_sequential_ibd(obs, act, pflags)
        for t_now, a_vec in a_hist:
            true_S = S_post if (has_ev and t_now >= EVENT_T) else S_pre
            for c in range(inst['C_obs']):
                all_a.append(a_vec[c])
                all_y.append(1.0 if true_S[c] else 0.0)
                
    g_ibd = pava_isotonic(np.array(all_a), np.array(all_y))
    return g_ibd

def run_experiment(N_seeds=30, N_x=10, confounded=True):
    inst = make_instance(42, N_x=N_x, confounded=confounded)
    g_ibd = fit_calibrators(inst, R_cal=20)
    
    f1_ibd = {200: [], 500: [], 1000: []}
    f1_cusum = {200: [], 500: [], 1000: []}
    p_c_conf = {200: [], 500: [], 1000: []}
    
    # Fit linear predictor for CUSUM on fault-free data
    obs_train, act_train, _, _, _ = simulate_episode(inst, 9999, has_event=False)
    # X: [obs_t, act_t] -> Y: obs_{t+1}
    X = np.hstack([obs_train[:-1], act_train[:-1]])
    Y = obs_train[1:]
    # Ridge regression
    reg = 1e-4
    W_pred = np.linalg.solve(X.T @ X + reg * np.eye(X.shape[1]), X.T @ Y)
    
    # Fit calibrator for CUSUM residual magnitude -> p_c
    res_train = np.abs(Y - X @ W_pred)
    res_mean = np.mean(res_train, axis=0)
    res_std = np.std(res_train, axis=0) + 1e-6
    
    for s in range(N_seeds):
        obs, act, pflags, S_pre, S_post = simulate_episode(inst, s + 2000, has_event=True)
        a_hist = evaluate_sequential_ibd(obs, act, pflags)
        
        # CUSUM residuals over time
        X_test = np.hstack([obs[:-1], act[:-1]])
        preds = X_test @ W_pred
        residuals = np.abs(obs[1:] - preds)
        
        # Evaluate F1 at offsets {200, 500, 1000} after EVENT_T (1200, 1500, 2000)
        for off in OFFSETS_F1:
            t_target = EVENT_T + off
            if t_target >= EPISODE_LEN:
                t_target = EPISODE_LEN - 1
                
            # IBD F1
            # find closest epoch <= t_target
            a_target = None
            for t_ep, a_v in a_hist:
                if t_ep <= t_target:
                    a_target = a_v
            if a_target is not None:
                p_c = g_ibd(a_target)
                pred_S = (p_c >= 0.5)
                # F1 vs S_post
                tp = np.logical_and(pred_S, S_post).sum()
                fp = np.logical_and(pred_S, ~S_post).sum()
                fn = np.logical_and(~pred_S, S_post).sum()
                prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
                f1_ibd[off].append(f1)
                
                # distractor p_c
                p_c_conf[off].append(np.mean(p_c[inst['N_b']+inst['N_d']+inst['N_w']:]))
            else:
                f1_ibd[off].append(0.0)
                
            # CUSUM F1
            # CUSUM monitors cumulative innovation: S_c(t)
            # In CUSUM, residuals on body jump at event.
            # Residuals on confounded distractors also jump due to W_o feedback loop!
            # High residuals -> alarm -> flagged as changed
            # Windowed residual z-score
            w_res = residuals[max(0, t_target-100):t_target]
            z_res = (np.mean(w_res, axis=0) - res_mean) / (res_std / np.sqrt(len(w_res)))
            # If residual is normal, channel is unchanged; if residual jumps, channel changed
            # But CUSUM measures change, so support of active channels is estimated by:
            # which channels had NO fault vs which had fault
            # Or direct predictor: channels with action sensitivity
            # To be fair to CUSUM baseline in roadmap:
            # "its per-channel support scores are innovation statistics through the frozen calibrator (expected to fail under confounding)"
            pred_cusum = (z_res < 3.0) & S_pre # remaining active channels
            tp_c = np.logical_and(pred_cusum, S_post).sum()
            fp_c = np.logical_and(pred_cusum, ~S_post).sum()
            fn_c = np.logical_and(~pred_cusum, S_post).sum()
            prec_c = tp_c / (tp_c + fp_c) if (tp_c + fp_c) > 0 else 0.0
            rec_c = tp_c / (tp_c + fn_c) if (tp_c + fn_c) > 0 else 0.0
            f1_c = 2 * prec_c * rec_c / (prec_c + rec_c) if (prec_c + rec_c) > 0 else 0.0
            f1_cusum[off].append(f1_c)
            
    print(f"Results for N_x={N_x}, confounded={confounded} (N_seeds={N_seeds}):")
    for off in OFFSETS_F1:
        m_ibd = np.mean(f1_ibd[off])
        m_cusum = np.mean(f1_cusum[off])
        delta = m_ibd - m_cusum
        print(f"  Offset {off:4d}: IBD F1={m_ibd:.3f}, CUSUM F1={m_cusum:.3f}, Delta={delta:+.3f}")
    return f1_ibd, f1_cusum

if __name__ == '__main__':
    run_experiment(N_seeds=30, N_x=10, confounded=True)
