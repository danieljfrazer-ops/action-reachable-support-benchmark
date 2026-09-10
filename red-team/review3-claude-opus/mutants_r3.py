"""New mutants for frozen version e662b7429b6b347d (round 3, Claude Opus reviewer).

Modelled on executable-proofs/gate/mutants.py: monkeypatch contract_ref, re-run the whole gate
suite (test_gate + test_proof_theatre, exactly what run_gate.py runs), count failing tests.
A mutant with 0 failing tests SURVIVES the gate and is a high finding.

Every mutant here is a semantically WRONG implementation of a normative contract item, and each is
shown to differ from the original on at least one explicit probe input (the OP-2 guard in
mutants.py is vacuous for count_alarms / match_alarms / aggregate_primary, because those three
functions are absent from that file's O dict AND from its PROBES dict, so `differs()` short-circuits
to True for them; the probe evidence below is supplied here instead).

Run: /Users/danielfrazer/.pyenv/versions/3.12.0/bin/python3 mutants_r3.py
Exit code 1 if any mutant survives (i.e. if this reviewer found a gate hole).
"""
import sys, os, pathlib
import numpy as np

GATE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "executable-proofs", "gate"))
sys.path.insert(0, GATE)
import contract_ref as ref
import test_gate, test_proof_theatre

ORIG = {k: getattr(ref, k) for k in ("count_alarms", "match_alarms", "aggregate_primary",
                                     "hpdt", "s_obs_eps", "structural_reach_full",
                                     "max_pairwise_corr")}
ORIG_CORR = ORIG["max_pairwise_corr"]


def failures():
    n, names = 0, []
    for mod in (test_gate, test_proof_theatre):
        for name in sorted(t for t in dir(mod) if t.startswith("test_")):
            try:
                getattr(mod, name)()
            except Exception:
                n += 1; names.append(f"{mod.__name__}.{name}")
    return n, names


def with_patch(**kw):
    saved = {k: (getattr(ref, k), getattr(test_gate, k, None)) for k in kw}
    for k, v in kw.items():
        setattr(ref, k, v); setattr(test_gate, k, v)
    try:
        return failures()
    finally:
        for k, (a, b) in saved.items():
            setattr(ref, k, a); setattr(test_gate, k, b)


# ------------------------------------------------------------------------------------------
# R3-M1  count_alarms: refractory r is ignored entirely.
#   Contract section G ("Alarm counted after p consecutive raises; refractory r") and section 0
#   (r = 20). Dropping r inflates the counted-alarm rate and therefore corrupts every ARL_0
#   calibration under D-2a, which is the quantity the whole matched-false-alarm comparison rests on.
# ------------------------------------------------------------------------------------------
def count_alarms_no_refractory(raw, p, r):
    counted, run = [], 0
    for t, v in enumerate(raw):
        run = run + 1 if v else 0
        if run >= p:
            counted.append(t); run = 0
    return counted


# ------------------------------------------------------------------------------------------
# R3-M2  count_alarms: persistence is leaky, not consecutive.
#   Contract section G says p CONSECUTIVE raises. This mutant decays the run counter by one on a
#   non-raise instead of resetting it, so an alternating raise pattern eventually alarms. Under a
#   noisy statistic this materially lowers ARL_0 at fixed h.
# ------------------------------------------------------------------------------------------
def count_alarms_leaky_persistence(raw, p, r):
    counted, run, block_until = [], 0, -1
    for t, v in enumerate(raw):
        if t <= block_until:
            run = 0; continue
        run = run + 1 if v else max(run - 1, 0)
        if run >= p:
            counted.append(t); run = 0; block_until = t + r
    return counted


# ------------------------------------------------------------------------------------------
# R3-M3  match_alarms: the `used` guard is dropped, so one alarm can be attributed to two events.
#   Contract section G / OP-12: an alarm is attributed to ONE event. Double attribution inflates
#   detection probability and shortens HPDT whenever events are closer together than H_det.
# ------------------------------------------------------------------------------------------
def match_alarms_double_attribution(alarm_times, event_times, H_det, episode_end):
    ev = sorted(event_times); alarms = sorted(alarm_times); used = set()
    delays, outcomes = [], []
    for i, e in enumerate(ev):
        nxt = ev[i + 1] if i + 1 < len(ev) else episode_end
        end = min(e + H_det, nxt, episode_end); hit = None
        for t in alarms:
            if e < t <= end:                     # <-- `and t not in used` removed
                hit = t; break
        if hit is None:
            delays.append(H_det); outcomes.append("missed")
        else:
            used.add(hit); delays.append(hit - e); outcomes.append("detected")
    return delays, outcomes, [t for t in alarms if t not in used]


# ------------------------------------------------------------------------------------------
# R3-M4  match_alarms: episode_end dropped from the attribution bound.
#   Contract section G / L11: early termination and episode end are competing outcomes. Without
#   episode_end an alarm recorded past the end of the episode can still be counted as a detection.
# ------------------------------------------------------------------------------------------
def match_alarms_no_episode_end(alarm_times, event_times, H_det, episode_end):
    ev = sorted(event_times); alarms = sorted(alarm_times); used = set()
    delays, outcomes = [], []
    for i, e in enumerate(ev):
        nxt = ev[i + 1] if i + 1 < len(ev) else float("inf")     # <-- episode_end dropped
        end = min(e + H_det, nxt); hit = None
        for t in alarms:
            if e < t <= end and t not in used:
                hit = t; break
        if hit is None:
            delays.append(H_det); outcomes.append("missed")
        else:
            used.add(hit); delays.append(hit - e); outcomes.append("detected")
    return delays, outcomes, [t for t in alarms if t not in used]


# ------------------------------------------------------------------------------------------
# R3-M5  aggregate_primary: median over cells instead of the equal-weight mean.
#   roadmap v4.1 E2 (and contract G under D-8a): "the equal-weight mean over distractor levels
#   and, for SCMs, over delays, of per-seed paired differences". A median is a different estimand
#   and is exactly the substitution the gate already forbids for HPDT (mutant FB-M9/OP-M1).
# ------------------------------------------------------------------------------------------
def aggregate_primary_median(rows, est_a="cusum_channel_agnostic", est_b="seq_ibd"):
    from collections import defaultdict
    cell = defaultdict(dict)
    for r in rows:
        cell[(r["seed"], r["level"], r["delay"])][r["estimator"]] = float(r["hpdt"])
    per_seed = defaultdict(list); dropped = 0
    for (seed, lvl, dly), v in cell.items():
        if est_a in v and est_b in v:
            per_seed[seed].append(v[est_a] - v[est_b])
        else:
            dropped += 1
    return {s: float(np.median(v)) for s, v in per_seed.items()}, dropped


# ------------------------------------------------------------------------------------------
# R3-M6  aggregate_primary: weight cells by how many rows they contain instead of equally.
#   v4.1 E2 says equal weight over (level, delay) cells. Row-count weighting silently upweights
#   whichever cells the confirmation matrix happens to replicate more.
# ------------------------------------------------------------------------------------------
def aggregate_primary_rowweighted(rows, est_a="cusum_channel_agnostic", est_b="seq_ibd"):
    from collections import defaultdict
    per_seed = defaultdict(list); seen = defaultdict(dict); dropped = 0
    cell = defaultdict(dict)
    for r in rows:
        cell[(r["seed"], r["level"], r["delay"])][r["estimator"]] = float(r["hpdt"])
    for (seed, lvl, dly), v in cell.items():
        if est_a in v and est_b in v:
            per_seed[seed].extend([v[est_a] - v[est_b]] * max(1, int(lvl) // 10))   # level-weighted
        else:
            dropped += 1
    return {s: float(np.mean(v)) for s, v in per_seed.items()}, dropped


# ------------------------------------------------------------------------------------------
# R3-M7  s_obs_eps: a channel whose assignment points past the end of the latent vector is
#   silently treated as absent instead of raising. Contract C5/E2d style: a NaN or an out-of-range
#   index reaching an output must be a hard error, not a silent False.
# ------------------------------------------------------------------------------------------
def s_obs_eps_silent_oob(latent_effect, assign, gain, avail, eps):
    C = len(assign); out = np.zeros(C, bool)
    for c in range(C):
        j = int(assign[c])
        if j < 0 or j >= len(latent_effect) or not avail[c]:
            continue
        out[c] = abs(float(gain[c])) * float(latent_effect[j]) > eps
    return out


# ------------------------------------------------------------------------------------------
# R3-M8  count_alarms: off-by-one refractory (window is r-1 steps, not r).
#   Contract section 0 fixes r = 20. The single gate fixture places the next raise burst outside
#   both windows, so the boundary of the refractory window is never exercised.
# ------------------------------------------------------------------------------------------
def count_alarms_offbyone_refractory(raw, p, r):
    counted, run, block_until = [], 0, -1
    for t, v in enumerate(raw):
        if t < block_until:                       # <-- was t <= block_until
            run = 0; continue
        run = run + 1 if v else 0
        if run >= p:
            counted.append(t); run = 0; block_until = t + r
    return counted


# ------------------------------------------------------------------------------------------
# R3-M9  max_pairwise_corr: when a witness (k, j) is declared, return THAT pair's correlation
#   instead of the maximum over all pairs. Contract E2c reads "a generated witness pair (k, j)
#   with |corr(a_k, x_j)| >= rho_min"; the reference instead returns the global max, so the
#   rho_min floor can be met by a pair other than the declared witness. The gate cannot tell the
#   two readings apart, so E2c's certification is ambiguous in the reference itself.
# ------------------------------------------------------------------------------------------
def corr_witness_only(a, x, witness=None):
    a = np.atleast_2d(a.T).T; x = np.atleast_2d(x.T).T
    if witness is None:
        return ORIG_CORR(a, x, None)
    k, j = witness
    if a[:, k].std() == 0 or x[:, j].std() == 0:
        return float("nan")
    return abs(float(np.corrcoef(a[:, k], x[:, j])[0, 1]))


MUTANTS = {
    "R3-M1 count_alarms: refractory r ignored":            dict(count_alarms=count_alarms_no_refractory),
    "R3-M2 count_alarms: leaky (non-consecutive) p":       dict(count_alarms=count_alarms_leaky_persistence),
    "R3-M3 match_alarms: one alarm, two events":           dict(match_alarms=match_alarms_double_attribution),
    "R3-M4 match_alarms: episode_end dropped":             dict(match_alarms=match_alarms_no_episode_end),
    "R3-M5 aggregate_primary: median over cells":          dict(aggregate_primary=aggregate_primary_median),
    "R3-M6 aggregate_primary: level-weighted cells":       dict(aggregate_primary=aggregate_primary_rowweighted),
    "R3-M7 s_obs_eps: out-of-range assign silently False": dict(s_obs_eps=s_obs_eps_silent_oob),
    "R3-M8 count_alarms: off-by-one refractory window":    dict(count_alarms=count_alarms_offbyone_refractory),
    "R3-M9 max_pairwise_corr: witness pair, not global max": dict(max_pairwise_corr=corr_witness_only),
}

# ---- evidence that each mutant really differs from the original somewhere -------------------
PROBES = {
    "count_alarms": [([0,1,1,1,1,1,0,1,1,1,0], 3, 20),
                     ([0,1,1,0,1,1,0,1,1,0,1,1], 3, 20),
                     ([1,1,1] + [0]*17 + [1]*5, 3, 20)],       # raise burst on the refractory edge
    "match_alarms": [([1900], [1800], 200, 1850),            # episode truncated inside H_det
                     ([1050], [1000, 1000], 200, 2000),      # duplicate event times
                     ([1010, 1050], [1000, 1005], 200, 2000)],
    "aggregate_primary": [([dict(seed=0, level=10, delay=0, estimator="cusum_channel_agnostic", hpdt=10.0),
                            dict(seed=0, level=10, delay=0, estimator="seq_ibd", hpdt=0.0),
                            dict(seed=0, level=30, delay=0, estimator="cusum_channel_agnostic", hpdt=20.0),
                            dict(seed=0, level=30, delay=0, estimator="seq_ibd", hpdt=0.0),
                            dict(seed=0, level=100, delay=0, estimator="cusum_channel_agnostic", hpdt=90.0),
                            dict(seed=0, level=100, delay=0, estimator="seq_ibd", hpdt=0.0)],)],
    "s_obs_eps": [(np.array([1.0]), np.array([0, 5]), np.ones(2), np.ones(2, bool), 0.1)],
    "max_pairwise_corr": [(np.array([[1., 0.], [2., 5.], [3., 0.], [4., 5.], [5., 0.]]),
                           np.array([[1.], [2.], [3.], [4.], [5.]]), (1, 0))],
}


def probe_evidence(name, fn):
    orig = ORIG[name]
    for args in PROBES.get(name, []):
        try:
            a = fn(*args)
        except Exception as e:
            return f"differs on {args!r}: mutant raises {type(e).__name__}"
        try:
            b = orig(*args)
        except Exception as e:
            return f"differs on {args!r}: ORIGINAL raises {type(e).__name__}, mutant returns {a!r}"
        if repr(a) != repr(b):
            return f"differs on {args!r}: original {b!r} vs mutant {a!r}"
    return None


if __name__ == "__main__":
    base, _ = failures()
    assert base == 0, f"gate not clean before mutation: {base} failing"
    print(f"gate clean: 0 failing tests before mutation\n")
    survivors = []
    for name, patch in MUTANTS.items():
        fn_name = list(patch)[0]
        ev = probe_evidence(fn_name, patch[fn_name])
        n, which = with_patch(**patch)
        status = "KILLED  " if n else "SURVIVED"
        print(f"{status} {name}: {n} failing tests")
        if ev:
            print(f"           evidence it is a real mutant -- {ev}")
        else:
            print(f"           WARNING: indistinguishable from the original on every probe input")
        if which:
            print(f"           failing: {', '.join(which)}")
        if not n:
            survivors.append(name)
    print(f"\n{len(MUTANTS) - len(survivors)}/{len(MUTANTS)} killed; {len(survivors)} SURVIVED")
    for s in survivors:
        print(f"  SURVIVOR: {s}")
    sys.exit(1 if survivors else 0)
