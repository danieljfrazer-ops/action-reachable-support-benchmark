# Decision D-10 Verdict — Gemini

**Date:** 7 September 2026  
**Target:** Decision D-10 (Parts 1–7), evaluated against `decisions-required.md` and `round4-adjudication-and-tally.md` (§1–§3).

---

## 1. Verdicts on D-10.1 through D-10.7

### D-10.1 (Freeze Instance Generator as Code): Adopt
Round 4 proved interventional AUC was consistent across implementations (0.900–0.912), while comparator AUC varied widely (0.637–0.840) because nine generative parameters were left unpinned. Freezing the reference generator as deterministic NumPy code eliminates instance-family discrepancies and ensures all models test an identical benchmark. Without this code anchor, cross-model replication certifies only estimator mechanics rather than benchmark validity.

### D-10.2 (Comparator Capacity): Adopt
Round 4 revealed two structural baseline defects: conditioning on full state blinded it to downstream channels ($l_c \approx 0$), and omitting delay history collapsed its AUC to $\le 0.540$ at $\tau = 2$. Codex showed supplying $a_{t-2}$ elevated comparator AUC to 0.997, proving the earlier $\tau=2$ benefit was an artifact of baseline misspecification. Adopting multi-horizon loading, delay-aware features, and feature standardisation establishes a competent baseline and prevents defeating a strawman.

### D-10.3 (R0-Absent Rule): Adopt
The round-4 simulations proved that the two-one-sided equivalence test ($\pm 0.05$) failed deterministically in every tested cell because IBD systematically beats the unconfounded comparator. Retaining an equivalence test with guaranteed failure and no registered consequence stalls the project on a false premise. Replacing it with a competence check ($\text{AUC} \ge 0.85$ absent confounding) verifies baseline adequacy while keeping confounding benefit as the primary estimand.

### D-10.4 (Probe Allocation): Adopt
Round 4 established that unconstrained probe-sign sampling starved actuator sign bins in ~13% of 25-probe windows, artificially zeroing out causal statistics on surviving actuators. Pre-randomising balanced blocks over $(k, sign)$ guarantees sample sufficiency across all cells without introducing state dependence. Returning an explicit eligibility mask ensures data scarcity is never conflated with absent causal support.

### D-10.5 (Co-Primary Offsets): Adopt
Trailing 500-step windows contain 96% pre-event data at offset 10 and 88% at offset 50 for both arms, as confirmed in round 4. Scoring co-primary false support at these early horizons evaluated pre-event baseline behavior rather than post-event causal adaptation. Restricting the evaluation grid to $\{200, 500, 1000\}$ ensures the metric measures actual post-event adaptation.

### D-10.6 (Copies): Adopt
Round 4 proved that duplicating observation channels shifts raw per-channel AUC arbitrarily without altering the causal ground truth, contradicting Contract C5. Excluding copies from confirmatory instances removes this uninformative degree of freedom from the primary benchmark. Retaining copies exclusively in acceptance fixtures properly isolates sensor redundancy testing from hypothesis testing.

### D-10.7 (Confirmation Replication): Adopt with a Stated Change
*Stated change:* Empower the pilot power simulation to scale the number of independent *instances* (with a floor of $\ge 20$ instances if the margin is near 0.10), rather than only scaling episode seeds per instance. Round 4 demonstrated that instance variation dwarfs within-instance episode noise. Sizing clusters at only 10 instances risks severe underpowering if the true margin lies close to 0.10.

---

## 2. Responses to Strategic Questions

**(a) Proposed Exit Condition:** Necessary but incomplete. Agreement to Monte Carlo error on a single frozen generator proves implementation fidelity, but misses parameter sensitivity. A bounded perturbation check across coupling strength and noise scale is required to ensure the design does not overfit a single hand-tuned instance.

**(b) Honest Fallback & Publication:** Both fallbacks leave Paper 1 fully publishable, as establishing the exact boundary where passive detection fails and active intervention becomes mandatory is a rigorous, high-impact scientific contribution. *[Opinion]* I prefer the indirect/downstream claim: it delivers an affirmative, actionable theorem-backed result that delineates precisely where active probing provides unique causal identifiability.

**(c) Measurement Scope & Cross-Model Review:** Yes. D-10.2 substantially modifies the measurement instrument by adding multi-horizon iterated predictions and delay-aware features to the comparator. This fundamentally shifts the baseline against which the primary margin $\delta_{AUC}$ is evaluated and must undergo Round 5 cross-model evaluation before freezing.
