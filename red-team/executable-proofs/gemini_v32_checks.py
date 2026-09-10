"""Executable checks for Gemini v3.2 findings H1 (coupling) and H3 (discrete pAUC)."""
import numpy as np
np.set_printoptions(precision=3, suppress=True)

# ---- H1: in a coupled linear body, losing an actuator need not remove a joint from the reachable set ----
def reachable_set(A, B, H):
    """Latent components with a nonzero open-loop response to some action within H steps."""
    n, k = B.shape
    reach = np.zeros(n, dtype=bool)
    for h in range(1, H+1):
        M = np.linalg.matrix_power(A, h-1) @ B      # open-loop response at horizon h (tau=0)
        reach |= (np.abs(M).sum(axis=1) > 1e-9)
    return reach
A_diag = np.diag([0.9, 0.9]);                 A_coup = np.array([[0.9, 0.0],[0.3, 0.9]])
B_full = np.eye(2);                            B_loss = np.array([[1.0, 0.0],[0.0, 0.0]])  # actuator 1 lost
for name, A in (("uncoupled", A_diag), ("coupled", A_coup)):
    print(f"H1 {name:9s} H=1: full={reachable_set(A,B_full,1)}  after-loss={reachable_set(A,B_loss,1)}")
    print(f"H1 {name:9s} H=3: full={reachable_set(A,B_full,3)}  after-loss={reachable_set(A,B_loss,3)}")
print("H1: with coupling and H>=2, actuator loss changes R but not S. Label must come from reachability, not the event type.")

# ---- H3: discrete Pareto-hull pAUC over integer delays, including a disjoint-support case ----
def pareto_logarl(delays, arls):
    """log ARL*(d) = max{log ARL(theta): median delay(theta) <= d}, over integer d."""
    delays = np.asarray(delays); logarl = np.log(np.asarray(arls, float))
    ds = np.arange(delays.min(), delays.max()+1)
    return ds, np.array([logarl[delays <= d].max() for d in ds])
def delta_pauc(dA, aA, dB, aB):
    """Normalised partial area between Pareto log-ARL envelopes over shared integer delays.
    Always returns a signed float (I2): on disjoint supports, the boundary difference."""
    dsA, lA = pareto_logarl(dA, aA); dsB, lB = pareto_logarl(dB, aB)
    dmin, dmax = max(dsA.min(), dsB.min()), min(dsA.max(), dsB.max())
    if dmin <= dmax:
        fA = {d: v for d, v in zip(dsA, lA)}; fB = {d: v for d, v in zip(dsB, lB)}
        val = float(np.mean([fA[d]-fB[d] for d in range(dmin, dmax+1)]))
        return val, f"shared integer delays {dmin}..{dmax}"
    if dsA.max() < dsB.min():   # A strictly faster at every threshold
        val = float(lA[-1] - lB[0]); return val, f"disjoint (A faster); boundary diff {val:.3f}; declare dominance"
    val = float(lA[0] - lB[-1]);     return val, f"disjoint (B faster); boundary diff {val:.3f}; declare dominance"
# non-unique thresholds -> same integer delay, different ARL (the case Gemini raised)
dA = [3,3,4,4,5,6,8];   aA = [50, 80, 120, 200, 400, 900, 2000]
dB = [4,5,5,6,7,9,12];  aB = [10, 20, 35, 60, 150, 400, 1200]
val, note = delta_pauc(dA, aA, dB, aB); print(f"H3 overlapping: Delta_pAUC={val:.3f} ({note}); SOEI ln2={np.log(2):.3f}")
val, note = delta_pauc([2,3,4], [100,300,900], [9,10,12], [50,90,200]); print(f"H3/I2 disjoint: Delta_pAUC={val:.3f} ({note})")
vals = [delta_pauc(dA, aA, dB, aB)[0], delta_pauc([2,3,4], [100,300,900], [9,10,12], [50,90,200])[0]]
print("I2 aggregation over mixed seeds works:", float(np.mean(vals)).__round__(3))
