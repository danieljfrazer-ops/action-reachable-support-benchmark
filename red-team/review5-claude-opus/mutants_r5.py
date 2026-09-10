"""Round-5 mutants, modelled on executable-proofs/gate/mutants.py but aimed at
`reference_generator.py` -- the surface the frozen gate's own mutation run never
touches (gate mutants.py patches contract_ref only).

A mutant is a patch to reference_generator (or contract_ref).  It is KILLED if
at least one test in test_gate + test_generator + test_proof_theatre fails, and
SURVIVES otherwise.  Every mutant is first checked to be OBSERVABLY DIFFERENT
from the original on a declared probe, so no survivor is a no-op (the fake-kill
guard from the gate's own runner, inverted).

Run:  PYTHONHASHSEED=0 python3 mutants_r5.py
"""
import sys, os, copy, importlib, traceback
import numpy as np

GATE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                                    "executable-proofs", "gate"))
sys.path.insert(0, GATE)
import reference_generator as RG
import contract_ref as CR
import test_gate, test_generator, test_proof_theatre

MODULES = (test_gate, test_generator, test_proof_theatre)
ORIG = dict(certify=RG.Instance.certify, apply_event=RG.Instance.apply_event,
            observe=RG.Instance.observe, init=RG.Instance.__init__,
            run=RG.Instance.run, confounded_channels=RG.Instance.confounded_channels,
            draw_certified=RG.draw_certified, noise=RG.Instance._noise)


def failures():
    n, names = 0, []
    for m in MODULES:
        for t in sorted(x for x in dir(m) if x.startswith("test_")):
            try:
                getattr(m, t)()
            except Exception:
                n += 1; names.append(f"{m.__name__}.{t}")
    return n, names


def with_patch(patch):
    """patch: dict of Instance-method-name -> function, or 'draw_certified' -> fn."""
    saved = {}
    for k, v in patch.items():
        if k == "draw_certified":
            saved[k] = RG.draw_certified
            RG.draw_certified = v
            test_generator.draw_certified = v
        else:
            saved[k] = getattr(RG.Instance, k)
            setattr(RG.Instance, k, v)
    try:
        return failures()
    finally:
        for k, v in saved.items():
            if k == "draw_certified":
                RG.draw_certified = v; test_generator.draw_certified = v
            else:
                setattr(RG.Instance, k, v)


# ---------------------------------------------------------------- mutants
def _cert_drop(field):
    """certify() with one contract conjunct deleted from `ok`."""
    def f(self, T=4000):
        out = ORIG["certify"](self, T)
        c = self.cfg; K = c["K"]
        conds = dict(
            rho_cl=out["rho_cl"] <= c["rho_cl"],
            sat=out["sat"] <= c["sat_max"],
            rho_witness=out["rho_witness"] >= c["rho_min"],
            rho_severed=out["rho_severed"] <= max(0.05, 3 * np.sqrt(2 * np.log(K * c["N_x"]) / T)),
            min_margin=out["min_margin"] > 0.0)
        conds.pop(field)
        out["ok"] = all(conds.values())
        self.certification = out
        return out
    return f


def cert_short_T(self, T=4000):
    """contract E2c/E2d fix T = T_E2 = 20,000; the generator uses 4,000. This
    mutant uses 200 -- a statistically meaningless witness/severance estimate."""
    return ORIG["certify"](self, 200)


def init_no_faithfulness(self, cfg, seed):
    """contract B: nonzero entries of A_b have |entry| >= c_min = 0.2. The shipped
    generator prunes at c_min*0.5 = 0.1, which leaves entries in [0.1, 0.2)
    violating the bound. This mutant prunes at the CONTRACT value c_min, i.e. it
    is the contract-compliant version -- the gate cannot tell the two apart."""
    ORIG["init"](self, cfg, seed)
    # undo the prune by re-deriving A_b without it
    rng = np.random.default_rng([seed, 0])
    c = self.cfg
    Nb, Nd, Nw, Nx, K = c["N_b"], c["N_d"], c["N_w"], c["N_x"], c["K"]
    cm = c["c_min"]

    def sample_matrix(rows, cols, density):
        M = np.zeros((rows, cols)); mask = rng.random((rows, cols)) < density
        M[mask] = rng.choice([-1, 1], size=mask.sum()) * rng.uniform(cm, 1.0, size=mask.sum()); return M
    A_b = sample_matrix(Nb, Nb, 0.5); np.fill_diagonal(A_b, rng.uniform(0.5, 0.9, Nb))
    self.A_b = RG._spectral_scale(A_b, c["rho_b"], rng)
    self.A_b[np.abs(self.A_b) < cm] = 0.0                        # contract threshold, not cm*0.5
    return None


def event_soft_loss(self, event):
    """contract D: 'actuator loss, complete: column k of B_t <- 0'. This sets it
    to 1e-9: S^obs,eps changes exactly as before, but the SIGN PATTERN is
    unchanged, so C1 graph reachability (structural_reach_full, which tests
    `B != 0`) still calls the actuator reachable. E1b demands the two label
    derivations agree after every event; here they cannot."""
    if event is None:
        return
    kind, arg = event
    if kind == "actuator_loss":
        self.B[:, arg] *= 1e-9
    else:
        ORIG["apply_event"](self, event)


def observe_no_gain(self, z, t, ep):
    """contract C3: 'Gain is part of the definition'. Drop it from the sensor."""
    o = np.zeros(self.C)
    for ch in range(self.C):
        j = self.assign[ch]
        if j >= 0 and self.avail[ch]:
            o[ch] = z[j]                       # gain[ch] dropped
    return o + self.cfg["sigma"]["o"] * self.cfg["noise_mult"] * self._noise("o", t, (self.C,), ep)


def confounded_inverted(self):
    """The oracle mask used by the CO-PRIMARY outcome (P2, confounded-channel
    false support), inverted inside the x block. f_conf = 0.5 is LOCKED, so the
    mask and its complement have identical cardinality."""
    m = np.zeros(self.C, bool)
    for ch in range(self.C):
        j = self.assign[ch]
        if j >= 0 and self.sl["x"].start <= j < self.sl["x"].stop:
            m[ch] = not self.confounded[j - self.sl["x"].start]
    return m


def run_event_after_action(self, T, ep=0, actions=None, event_t=None, event=None,
                           z0=None, u0=None, record_u=False):
    """Both specs' offset convention says 'the event applies BEFORE step event_t
    is taken'. This mutant applies it AFTER the action is chosen at event_t, a
    one-step shift of the event clock that every offset table depends on."""
    c = self.cfg; K = c["K"]; Nz = self.Nz
    z = np.zeros(Nz) if z0 is None else z0.copy(); u = np.zeros(1) if u0 is None else u0.copy()
    O = np.zeros((T + 1, self.C)); A = np.zeros((T, K)); Z = np.zeros((T + 1, Nz)); U = np.zeros((T + 1, 1))
    queue = [np.zeros(K)] * self.tau; sat = 0
    O[0] = self.observe(z, 0, ep); Z[0] = z; U[0] = u
    for t in range(T):
        a = self.policy(O[t], u, t, ep) if actions is None or t not in actions else np.clip(actions[t], -c["a_max"], c["a_max"])
        if event_t is not None and t == event_t:
            self.apply_event(event)                       # moved: after the action
        sat += int(np.any(np.abs(a) >= c["a_max"] - 1e-12))
        queue.append(a); a_delayed = queue.pop(0)
        z = self.step_latent(z, a_delayed, u, t, ep)
        u = c["rho_u"] * u + c["sigma"]["u"] * self._noise("u", t, (1,), ep)
        A[t] = a; Z[t + 1] = z; U[t + 1] = u; O[t + 1] = self.observe(z, t + 1, ep)
    return dict(o=O, a=A, z=Z, u=U, sat=sat / T)


def draw_ignore_ok(cfg, seed, max_tries=20):
    """Control mutant, expected to be KILLED: accept the first draw regardless."""
    inst = RG.Instance(cfg, seed * 1000); inst.certify(); inst.n_resamples = 0
    return inst


def noise_no_varkey(self, var, t, shape, ep):
    """contract B 'noise indexed by (seed, variable, t)': drop the variable."""
    return np.random.default_rng([self.seed, ep, 0, t]).normal(size=shape)


# ---- per-mutant WITNESSES: a concrete input on which the mutant's behaviour differs.
# Without one, a "survivor" might merely be a no-op. Each witness returns a value; the
# mutant is a real mutant iff the value changes under the patch.
def w_default(cseed=0):
    """generic witness: trajectory, certification, oracle masks, post-event labels."""
    i = RG.Instance({}, cseed)
    j = RG.draw_certified({}, cseed)
    k = copy.deepcopy(j); k.apply_event(("actuator_loss", 0))
    return (i.run(60, ep=1)["o"].round(10).tobytes(),
            repr({a: round(b, 10) for a, b in j.certification.items() if isinstance(b, float)}),
            j.confounded_channels().tobytes(), k.S_obs().tobytes(), k.S_latent().tobytes(),
            RG.Instance({}, cseed).A_b.round(10).tobytes())


def w_seed5():
    """seed 5 is one of the few draws where actuator 0 is the ONLY path to part of
    the support, so a soft loss and a complete loss are distinguishable there."""
    return w_default(5)


def w_sat():
    """saturating context feedback: sat -> ~1 while rho_cl, rho_witness, margin stay fine."""
    i = RG.Instance({}, 0); i.W_u = i.W_u * 1000.0
    c = i.certify(T=1500)
    return (c["ok"], round(c["sat"], 3) > 0.05)


def w_rho_cl():
    """bisect the policy gain so rho_cl lands in (0.98, 0.999): out of bound, still stable."""
    i = RG.Instance({}, 0); base = i.W_o.copy()
    lo, hi = 1.0, 200.0
    for _ in range(60):
        mid = (lo + hi) / 2; i.W_o = base * mid
        r = i.certify(T=200)["rho_cl"]
        if r < 0.9895: lo = mid
        else: hi = mid
    i.W_o = base * lo
    c = i.certify(T=1500)
    return (c["ok"], round(c["rho_cl"], 4))


def w_margin():
    """B = 0 -> S_latent empty -> min_margin == 0.0 -> only `min_margin` fails."""
    i = RG.Instance({}, 0); i.B = np.zeros_like(i.B)
    return i.certify(T=600)["ok"]


def w_severed():
    """leak the action into x (gate mutant M1's mechanism) -> only rho_severed fails."""
    i = RG.Instance({}, 0)
    base = RG.Instance.step_latent

    def leaky(self, z, a_delayed, u, t, ep):
        z2 = base(self, z, a_delayed, u, t, ep)
        z2[self.sl["x"]] += 2.0 * a_delayed[0]
        return z2
    saved = RG.Instance.step_latent
    RG.Instance.step_latent = leaky
    try:
        return i.certify(T=1500)["ok"]
    finally:
        RG.Instance.step_latent = saved


def w_faithfulness():
    """A_b sparsity pattern and the smallest surviving |entry| on the frozen seeds."""
    out = []
    for s in range(10):
        A = RG.Instance({}, s).A_b; nz = A[A != 0]
        out.append((int(nz.size), round(float(np.abs(nz).min()), 6)))
    return tuple(out)


def w_gain():
    """the gain path is only reachable through a sensor_gain event."""
    i = RG.Instance({}, 0); i.apply_event(("sensor_gain", (0, 7.0)))
    return round(float(i.observe(np.ones(i.Nz), 5, 1)[0]), 10)


def w_event_clock():
    i = RG.Instance({}, 0)
    return i.run(1200, ep=2, event_t=1000, event=("actuator_loss", 0))["o"].round(10).tobytes()


MUTANTS = {
    "R5-M1 certify drops sat<=0.05 (contract B / OP-16)":        (dict(certify=_cert_drop("sat")), w_sat),
    "R5-M2 certify drops min_margin>0 (contract C2 eps-margin)": (dict(certify=_cert_drop("min_margin")), w_margin),
    "R5-M3 certify drops rho_severed bound (contract E2d)":      (dict(certify=_cert_drop("rho_severed")), w_severed),
    "R5-M4 certify drops rho_cl bound (contract B stability)":   (dict(certify=_cert_drop("rho_cl")), w_rho_cl),
    "R5-M5 certify uses T=200 not 4000 (contract T_E2=20000)":   (dict(certify=cert_short_T), w_default),
    "R5-M6 A_b prune at c_min not c_min/2 (contract B faithfulness)": (dict(__init__=init_no_faithfulness), w_faithfulness),
    "R5-M7 actuator_loss -> 1e-9 not 0 (contract D / E1b)":      (dict(apply_event=event_soft_loss), w_seed5),
    "R5-M8 observe() ignores gain (contract C3)":                (dict(observe=observe_no_gain), w_gain),
    "R5-M9 confounded_channels INVERTED (co-primary P2 oracle)": (dict(confounded_channels=confounded_inverted), w_default),
    "R5-M10 event applied AFTER the action at event_t":          (dict(run=run_event_after_action), w_event_clock),
    "R5-M11 [control] draw_certified ignores cert['ok']":        (dict(draw_certified=draw_ignore_ok), w_default),
    "R5-M12 _noise drops the variable key (contract B CRN)":     (dict(_noise=noise_no_varkey), w_default),
}


def observable(patch, witness):
    """The mutant is a real mutant iff `witness` changes under the patch."""
    before = witness()
    saved = {}
    for kk, v in patch.items():
        if kk == "draw_certified":
            saved[kk] = RG.draw_certified; RG.draw_certified = v
        else:
            saved[kk] = getattr(RG.Instance, kk); setattr(RG.Instance, kk, v)
    try:
        after = witness()
    except Exception:
        return True                                     # raising is a difference
    finally:
        for kk, v in saved.items():
            if kk == "draw_certified":
                RG.draw_certified = v
            else:
                setattr(RG.Instance, kk, v)
    return before != after


def main():
    base_n, base_names = failures()
    print(f"baseline failures on the unmutated tree: {base_n}  {base_names}")
    assert base_n == 0, "the gate must be green before mutation"
    survivors, killed, noop = [], [], []
    for name, (patch, witness) in MUTANTS.items():
        obs = observable(patch, witness)
        n, names = with_patch(patch)
        tag = "KILLED  " if n else "SURVIVED"
        note = "" if obs else "   [!! witness shows NO behavioural difference - not a real mutant]"
        print(f"{tag} {name}: {n} failing tests{note}")
        if names:
            print(f"           -> {names}")
        if n:
            killed.append(name)
        elif not obs:
            noop.append(name)
        elif n == 0:
            survivors.append(name)
    print(f"\n{len(killed)} killed, {len(survivors)} SURVIVED, {len(noop)} were behaviourally"
          f" indistinguishable from the original (reported as failed attacks, not survivors).")
    for s in survivors:
        print(f"  SURVIVOR  {s}")
    for s in noop:
        print(f"  NOT-A-MUTANT (no witness difference)  {s}")
    return 0 if not survivors else 1


if __name__ == "__main__":
    sys.exit(main())
