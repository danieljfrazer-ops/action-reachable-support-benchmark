# Final Harmonization Patches (v3.3)

**Reviewer:** Gemini (Antigravity Red Team)  
**Date:** 6 September 2026  
**Purpose:** Drop-in textual and code updates to resolve findings I1 and I2 before Stage 0B confirmation sweeps.

---

## Patch 1: Decision Rule Alignment for C2 Regimes (Resolves I1)

### Target: `roadmap-v3.3-amendments.md`, Amendment C2

#### Add to the end of Section C2:
```markdown
### Decision Rules by Regime (Harmonizing A5 with C2)
With 95% bootstrap intervals clustered by seed:
1. **Regime R0 (Clean Anchor):**
   - **Pass / Validated:** 95% CI upper bound of $\Delta_{pAUC} \le 0$ (confirming the classical residual detector dominates or matches interventional probing at zero probe cost).
   - **Unexpected / Anomaly:** 95% CI lower bound $> 0$ (investigate why classical FDI failed on a clean linear system).
2. **Regimes R1 (Misspecified) & R2 (Masked):**
   - **Superiority:** 95% CI lower bound $> \delta = \ln 2$ on both dynamics families (confirming interventional robustness justifies its probe budget).
   - **Futility:** 95% CI upper bound $< \delta$ on either dynamics family.
   - **Inconclusive:** Otherwise (reported as a benchmark finding without efficacy claims).
```

---

## Patch 2: Explicit Numerical Float for Disjoint Delay Supports (Resolves I2)

### Target: `executable-proofs/gemini_v32_checks.py`

#### Replace Lines 27–34:
```python
def delta_pauc(dA, aA, dB, aB):
    dsA, lA = pareto_logarl(dA, aA); dsB, lB = pareto_logarl(dB, aB)
    dmin, dmax = max(dsA.min(), dsB.min()), min(dsA.max(), dsB.max())
    if dmin > dmax:
        return None, "disjoint supports: report boundary difference and declare dominance"
    fA = {d: v for d, v in zip(dsA, lA)}; fB = {d: v for d, v in zip(dsB, lB)}
    ds = range(dmin, dmax+1)
    return float(np.mean([fA[d]-fB[d] for d in ds])), f"shared integer delays {dmin}..{dmax}"
```

#### With the following robust implementation:
```python
def delta_pauc(dA, aA, dB, aB):
    """
    Computes normalized partial area under the Pareto log(ARL) envelope.
    Returns a signed float across both overlapping and disjoint operating regimes.
    """
    dsA, lA = pareto_logarl(dA, aA)
    dsB, lB = pareto_logarl(dB, aB)
    dmin, dmax = max(dsA.min(), dsB.min()), min(dsA.max(), dsB.max())
    
    if dmin <= dmax:
        # Overlapping delay support: compute discrete Riemann mean difference
        fA = {d: v for d, v in zip(dsA, lA)}
        fB = {d: v for d, v in zip(dsB, lB)}
        ds = range(dmin, dmax + 1)
        val = float(np.mean([fA[d] - fB[d] for d in ds]))
        return val, f"shared integer delays {dmin}..{dmax}"
    else:
        # Disjoint delay support: compute boundary difference
        if dsA.max() < dsB.min():
            # Estimator A is strictly faster than Estimator B across all thresholds
            # Compare A at its maximum delay with B at its minimum delay
            val = float(lA[-1] - lB[0])
            return val, f"disjoint (A strictly faster; boundary diff {val:.3f})"
        else:
            # Estimator B is strictly faster than Estimator A across all thresholds
            val = float(lA[0] - lB[-1])
            return val, f"disjoint (B strictly faster; boundary diff {val:.3f})"
```
