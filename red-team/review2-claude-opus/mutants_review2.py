"""Round-2 mutation attack on the frozen gate (executable-proofs/gate/, hash d23960e6da441de7).

Same harness contract as the incumbent mutants.py: monkeypatch a function on `contract_ref` AND
`test_gate` (test_gate does `from contract_ref import *`, so both bindings must be replaced), then
count how many gate tests raise. A mutant with 0 failing tests SURVIVES -> the gate does not pin
that part of the contract.

Every mutant below is a deliberate violation of a specific NORMATIVE clause of
stage-0a-contract-v3.1.md; the clause is named in the `clause` field.

Run: /Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3 mutants_review2.py
Exit 1 if any mutant survives (i.e. exit 1 == the gate has a hole).
"""
import sys, pathlib, numpy as np

GATE = pathlib.Path(__file__).resolve().parent.parent / "executable-proofs" / "gate"
sys.path.insert(0, str(GATE))
import contract_ref as ref
import test_gate


def failures(verbose=False):
    n, names = 0, []
    for name in sorted(t for t in dir(test_gate) if t.startswith("test_")):
        try:
            getattr(test_gate, name)()
        except Exception as e:
            n += 1; names.append(f"{name}({type(e).__name__})")
    if verbose and names:
        print("      killed by:", ", ".join(names))
    return n, names


def with_patch(**kw):
    saved = {k: (getattr(ref, k), getattr(test_gate, k, None)) for k in kw}
    for k, v in kw.items():
        setattr(ref, k, v)
        if hasattr(test_gate, k):
            setattr(test_gate, k, v)
    try:
        return failures()
    finally:
        for k, (a, b) in saved.items():
            setattr(ref, k, a)
            if b is not None:
                setattr(test_gate, k, b)


O = {k: getattr(ref, k) for k in
     ("open_loop_response", "jacobian_piecewise", "structural_reach", "structural_reach_full",
      "s_obs_eps", "hpdt", "check_spacing", "max_pairwise_corr", "build_adjacency")}

# =====================================================================================
# MUTANTS
# =====================================================================================

# --- OP-M1: HPDT is the MEDIAN over events, not the mean. Contract G: "mean over events". ---
def m_hpdt_median(delays, outcome, horizon):
    d = np.asarray(delays, float); o = np.asarray(outcome)
    v = np.where(o == 'detected', np.minimum(d, horizon), horizon)
    return float(np.median(v))

# --- OP-M2: check_spacing ignores the distance from the last event to episode end.
#     Contract 0/D: "minimum steps between change events AND BEFORE EPISODE END".
#     This is exactly the administrative-censoring case contract G claims cannot occur. ---
def m_spacing_no_end(event_times, episode_end, horizon, match_window):
    ts = sorted(event_times)
    return all(ts[i + 1] - ts[i] >= horizon + match_window for i in range(len(ts) - 1))

# --- OP-M3: check_spacing uses strict > instead of >=. Contract: "spacing >= event_spacing"
#     with event_spacing = H_det + w_T = 250 exactly, i.e. the boundary is the intended value. ---
def m_spacing_strict(event_times, episode_end, horizon, match_window):
    ts = list(sorted(event_times)) + [episode_end]
    return all(ts[i + 1] - ts[i] > horizon + match_window for i in range(len(ts) - 1))

# --- OP-M4: s_obs_eps drops the padding guard (assign < 0). Contract C3 requires
#     Assign_t(c) = j != empty; contract A/D3 says o contains padding channels.
#     In Python assign[c] = -1 silently indexes the LAST latent instead of being excluded. ---
def m_sobs_no_padding_guard(latent_effect, assign, gain, avail, eps):
    C = len(assign); out = np.zeros(C, bool)
    for c in range(C):
        if not avail[c]:
            continue
        out[c] = abs(gain[c]) * latent_effect[assign[c]] > eps      # no j < 0 check
    return out

# --- OP-M5: s_obs_eps uses >= eps instead of > eps. Contract C3 is strict. ---
def m_sobs_ge(latent_effect, assign, gain, avail, eps):
    C = len(assign); out = np.zeros(C, bool)
    for c in range(C):
        j = assign[c]
        if j < 0 or not avail[c]:
            continue
        out[c] = abs(gain[c]) * latent_effect[j] >= eps
    return out

# --- OP-M6: build_adjacency drops the downstream self-dynamics A_d (and A_w, A_x).
#     Contract C1: reachability "on the sign pattern of the FULL block adjacency
#     (A_b, B_t, C_d, A_d, A_w, A_x)". Chains inside d of length > 1 become invisible. ---
def m_adj_no_Ad(A_b, C_d=None, A_d=None, A_w=None, A_x=None):
    return O["build_adjacency"](A_b, C_d, None, None, None)

# --- OP-M15: SHAPE-PRESERVING version of OP-M6: keep every block except zero out the d->d
#     self-dynamics A_d. Chains INSIDE the downstream block (d_i -> d_j) become invisible.
#     OP-M6 above is killed only because dropping A_w/A_x changes the vector LENGTH. ---
def m_adj_zero_Ad_block(A_b, C_d=None, A_d=None, A_w=None, A_x=None):
    adj, sl = O["build_adjacency"](A_b, C_d, A_d, A_w, A_x)
    adj = adj.copy()
    adj[sl["d"], sl["d"]] = False
    return adj, sl

# --- OP-M7: open_loop_response ignores z_bar and always anchors at zero.
#     Contract C4: "z_bar the stationary mean estimated after burn_in (family L: z_bar = 0 is
#     exact; family N: the EMPIRICAL z_bar is used)". For family N the response at 0 != at z_bar. ---
def m_olr_ignore_zbar(A, B, a, h, tau=0, zbar=None, step_fn=None):
    return O["open_loop_response"](A, B, a, h, tau, None, step_fn)

# --- OP-M8: max_pairwise_corr returns the MEAN over eligible pairs, not the max.
#     Contract 0/E2d: rho_min is "max pairwise |corr(a_k, x_j)|"; E2d bounds the MAX. ---
def m_corr_mean(a, x, witness=None):
    a = np.atleast_2d(a.T).T; x = np.atleast_2d(x.T).T
    if witness is not None:
        k, j = witness
        if a[:, k].std() == 0 or x[:, j].std() == 0:
            return float('nan')
    vals = []
    for k in range(a.shape[1]):
        for j in range(x.shape[1]):
            if a[:, k].std() == 0 or x[:, j].std() == 0:
                continue
            vals.append(abs(np.corrcoef(a[:, k], x[:, j])[0, 1]))
    return float(np.mean(vals)) if vals else float('nan')

# --- OP-M9: hpdt counts 'terminated' as a *detected* event at its recorded delay.
#     Contract G/L11: early termination is a competing outcome scored as H_det. ---
def m_hpdt_terminated_as_detected(delays, outcome, horizon):
    d = np.asarray(delays, float); o = np.asarray(outcome)
    v = np.where((o == 'detected') | (o == 'terminated'), np.minimum(d, horizon), horizon)
    return float(v.mean())

# --- OP-M10: structural_reach_full treats the delay as applying to the WHOLE horizon budget,
#     i.e. propagates H - tau times instead of H - tau - 1 (over-reach by one step). ---
def m_reach_offbyone(A_b, B, H, tau=0, C_d=None, A_d=None, A_w=None, A_x=None):
    adj, sl = O["build_adjacency"](A_b, C_d, A_d, A_w, A_x)
    N = adj.shape[0]; reach = np.zeros(N, bool)
    if H <= tau:
        return reach
    front = np.zeros(N, bool); front[sl["b"]] = (B != 0).any(axis=1)
    reach |= front
    for _ in range(tau + 1, H + 1):
        front = (adj.astype(int) @ front.astype(int)) > 0
        reach |= front
    return reach

# --- OP-M11: jacobian_piecewise ignores the delay entirely for the boundary case h == tau
#     (returns the h=1 Jacobian rather than zero) -- a "control arrives one step early" bug. ---
def m_jac_early(A, B, h, tau=0):
    if h < tau:
        return np.zeros_like(B)
    return np.linalg.matrix_power(A, max(h - 1 - tau, 0)) @ B

# --- OP-M12: hpdt drops the min(delay, horizon) cap for detected events but keeps everything
#     else -- i.e. an unbounded delay estimand. Contract G caps at H_det. ---
def m_hpdt_uncapped(delays, outcome, horizon):
    d = np.asarray(delays, float); o = np.asarray(outcome)
    return float(np.where(o == 'detected', d, horizon).mean())

# --- OP-M13: s_obs_eps ignores avail (sensor dropout invisible). Contract C3/D. ---
def m_sobs_ignore_avail(latent_effect, assign, gain, avail, eps):
    return O["s_obs_eps"](latent_effect, assign, gain, np.ones_like(np.asarray(avail), bool), eps)

# --- OP-M14: the incumbent M8 mutant, written CORRECTLY (the shipped one self-recurses). ---
def m_gain_ignored_correct(latent_effect, assign, gain, avail, eps):
    C = len(assign); out = np.zeros(C, bool)
    for c in range(C):
        j = assign[c]
        if j < 0 or not avail[c]:
            continue
        out[c] = latent_effect[j] > eps          # gain dropped from the definition
    return out


MUTANTS = [
    ("OP-M1  HPDT median-not-mean", "G primary estimand: 'mean over events'", dict(hpdt=m_hpdt_median)),
    ("OP-M2  spacing ignores episode end", "0/D event_spacing '...and before episode end'; G no-admin-censoring", dict(check_spacing=m_spacing_no_end)),
    ("OP-M3  spacing strict > not >=", "B/D 'spacing >= event_spacing' (=250 exactly)", dict(check_spacing=m_spacing_strict)),
    ("OP-M4  S_obs drops padding guard", "C3 'Assign_t(c) = j != empty'; A/D3 padding channels", dict(s_obs_eps=m_sobs_no_padding_guard)),
    ("OP-M5  S_obs uses >= eps", "C3 '|gain| * e_j > eps' (strict)", dict(s_obs_eps=m_sobs_ge)),
    ("OP-M6  adjacency drops A_d/A_w/A_x", "C1 'full block adjacency (A_b, B_t, C_d, A_d, A_w, A_x)'", dict(build_adjacency=m_adj_no_Ad)),
    ("OP-M7  response ignores z_bar", "C4 'z_bar the stationary mean...family N: empirical z_bar'", dict(open_loop_response=m_olr_ignore_zbar)),
    ("OP-M8  corr mean-not-max", "0/E2d rho_min = 'max pairwise |corr|'", dict(max_pairwise_corr=m_corr_mean)),
    ("OP-M9  terminated scored as detected", "G/L11 competing outcome scored as H_det", dict(hpdt=m_hpdt_terminated_as_detected)),
    ("OP-M10 reachability over-reach by 1", "C1 'first hit is at h = tau + 1'", dict(structural_reach_full=m_reach_offbyone)),
    ("OP-M11 Jacobian arrives one step early", "C4 'M = 0 for h <= tau'", dict(jacobian_piecewise=m_jac_early)),
    ("OP-M12 HPDT uncapped delay", "G 'min(delay, H_det)'", dict(hpdt=m_hpdt_uncapped)),
    ("OP-M13 S_obs ignores avail", "C3 'avail_t(c) = 1'", dict(s_obs_eps=m_sobs_ignore_avail)),
    ("OP-M14 gain ignored (correct M8)", "C3 gain is part of the definition (L5)", dict(s_obs_eps=m_gain_ignored_correct)),
    ("OP-M15 adjacency zeroes A_d block only", "C1 full block adjacency incl. A_d (shape preserved)", dict(build_adjacency=m_adj_zero_Ad_block)),
]

print(f"gate under test: {GATE}")
print(f"numpy {np.__version__}  python {sys.version.split()[0]}\n")
base_n, _ = failures()
print(f"baseline failing tests (unmutated): {base_n}\n")

survivors = []
for name, clause, patch in MUTANTS:
    n, killed_by = with_patch(**patch)
    tag = "KILLED " if n > 0 else "SURVIVED"
    print(f"{tag} {name:38s} -> {n} failing tests   [{clause}]")
    if n:
        print(f"         killed by: {', '.join(killed_by)}")
    else:
        survivors.append(name)

print(f"\n{len(MUTANTS) - len(survivors)}/{len(MUTANTS)} killed;  {len(survivors)} SURVIVORS:")
for s in survivors:
    print("   *", s)

# =====================================================================================
# Separate defect: the SHIPPED M8 mutant in mutants.py self-recurses instead of mutating.
# =====================================================================================
print("\n--- audit of the shipped mutants.py M8 mutant ---")
def shipped_m8(latent_effect, assign, gain, avail, eps):
    return ref.s_obs_eps(latent_effect, assign, np.ones_like(gain), avail, eps)   # verbatim from mutants.py
saved = ref.s_obs_eps, test_gate.s_obs_eps
ref.s_obs_eps = test_gate.s_obs_eps = shipped_m8
try:
    shipped_m8(np.array([1.0]), np.array([0]), np.array([1.0]), np.array([True]), 0.1)
    print("shipped M8: returned normally (no recursion)")
except RecursionError:
    print("shipped M8: RecursionError -- the mutant calls the PATCHED ref.s_obs_eps, i.e. ITSELF.")
    print("            It is 'killed' by its own infinite recursion, not by the gate's discrimination.")
finally:
    ref.s_obs_eps, test_gate.s_obs_eps = saved

sys.exit(1 if survivors else 0)
