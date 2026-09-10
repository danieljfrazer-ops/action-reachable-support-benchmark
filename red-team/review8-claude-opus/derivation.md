# Round 8 derivation: identifiability of loss-of-control under a body-reaching confounder

Reviewer: fresh-context Claude Opus (`claude-opus`), 9 September 2026.
Read: `round7-adjudication.md`, `round6-adjudication-and-tally.md` §§1–3, `decisions-required.md` (D-12),
`stage-0a-contract-v3.9.md` §§0, A0, A, B, C, D, E, F, G, `comparator-spec.md` v3 §§1–5, `sequential-ibd-spec.md` draft 5 §§3–6.
No `review*/` folder read. No existing file edited.

Everything in `check_algebra.py` in this folder is a **check of the algebra below on one hand-written toy
instance**, run to catch sign errors and dropped terms. It is **not a result**, not evidence about the frozen
generator, and no number from it may be quoted as an outcome. Where I cite it I write *(check)*.
Opinion is marked **[opinion]**.

---

## 0. Notation and standing assumptions

Family **L-C** (the proposed plant), population limit, linear-Gaussian, no clipping, zero means.
`u` scalar for exposition (`n_u = 1`); everything generalises with `W_u ∈ R^{K×n_u}`, `G_b ∈ R^{N_b×n_u}`.

```
u_{t+1} = ρ_u u_t + ε^u_t                                     Var(ε^u) = σ_u²
a_t     = W_o o_t + W_u u_t + ε^a_t                           Σ_a = σ_a² I_K
b_{t+1} = A_b b_t + B a_{t−τ} + G_b u_t + ε^b_t               Σ_b = σ_b² I
d_{t+1} = A_d d_t + C_d b_t + ε^d_t
x_{t+1} = A_x x_t + G_x u_t + ε^x_t
o_t     = z_t + ε^o_t,  z = [b; d; w; x]                      Σ_o = σ_o² I
```

Contract A0 puts `W_o` on body channels only; write `W_b ∈ R^{K×N_b}` for that block, so
`W_o o_t = W_b (b_t + ε^{o,b}_t)`. Contract v3.9 is the case **G_b = 0**; family L-C is **G_b ≠ 0**.
Contract v3.9's single matrix `G` becomes `G_x` (§6 below: this rename is load-bearing).

Two derived objects used throughout:

```
F := A_b + B W_b          closed-loop body matrix
g := B W_u + G_b          total confounder-to-body drive (policy path + direct path)
ζ_t := a_t − E[a_t | b_t, u_t] = W_b ε^{o,b}_t + ε^a_t        the EXOGENOUS part of the action
Σ_ζ = W_b Σ_{ε^o,b} W_b^T + σ_a² I_K
```

`ζ_t` is the whole story of question (1). It is an always-on, unlabelled, infinitesimal probe that the
policy injects for free. A deliberate probe is the same object made **observable** and made **large**.

The estimand is unchanged by `G_b`. Contract C2 defines the operational effect as a *difference* of two
`do(·)` expectations from the same `z̄`; `G_b u_t` is common to both arms of that difference and cancels.
So **`S^latent`, `S^obs,ε`, `R`, `M` and the E1b label check are all invariant to `G_b`** — L-C changes the
difficulty of estimation, not the thing being estimated. That matters for §6 and for the novelty question.

---

## 1. Question (1): passive identifiability

### 1.1 The post-event stationary second-order statistics

Eliminate `a` and `b`. With `τ = 0` (the `τ = 2` case is the same on the delay-augmented state
`[b_t; a_{t−1}; a_{t−2}]`, and is checked separately):

```
b_{t+1} = F b_t + g u_t + B ζ_t + ε^b_t
a_t     = W_b b_t + W_u u_t + ζ_t
x_{t+1} = A_x x_t + G_x u_t + ε^x_t
d_{t+1} = A_d d_t + C_d b_t + ε^d_t
```

In transfer-function form, with `Φ(q) = (qI − F)^{-1}`, `φ_u(q) = (1 − ρ_u q^{-1})^{-1}`:

```
b = Φ(q)[ g φ_u ε^u + B ζ + ε^b ]
a = W_b b + W_u φ_u ε^u + ζ
```

so the joint spectral density of the observables is built from exactly four functions of `ω`:

```
Φ_bb(ω) = Φ [ σ_u² |φ_u|² g gᵀ  +  B Σ_ζ Bᵀ + Σ_b ] Φ*                                   (S1)
Φ_ba(ω) = Φ_bb W_bᵀ  +  Φ g σ_u² |φ_u|² W_uᵀ  +  Φ B Σ_ζ                                  (S2)
Φ_aa(ω) = W_b Φ_bb W_bᵀ + [W_b Φ (g σ_u²|φ_u|² W_uᵀ + B Σ_ζ) + h.c.]
          + σ_u² |φ_u|² W_u W_uᵀ + Σ_ζ                                                     (S3)
Φ_bx(ω) = Φ g σ_u² φ_u φ_u* G_xᵀ ψ_x*,   ψ_x = (qI − A_x)^{-1}                            (S4)
```
(`d` adds `Φ_bd = Φ_bb C_dᵀ ψ_d*` and nothing new; `w` and the pads are independent.)

**Everything the body parameters contribute to the observational law enters through four objects only:**

| trace | expression | changed by E1 (`B ← B P_k`, `P_k = I − e_k e_kᵀ`) | changed by E2 (`G_b`, `W_u`) |
|---|---|---|---|
| T1 closed-loop dynamics | `F = A_b + B W_b` | yes, `F − β_k w_kᵀ` (`β_k = B e_k`, `w_kᵀ` = row `k` of `W_b`) | **no** |
| T2 confounder drive | `g = B W_u + G_b` | yes, `g − β_k W_{u,k}` | yes |
| T3 drive-noise covariance | `B Σ_ζ Bᵀ + Σ_b` | yes | **no** |
| T4 **instrument cross-term** | `B Σ_ζ` | yes, `B P_k Σ_ζ` | **no** |

T4 is the decisive one. It is the cross-covariance between the exogenous action noise `ζ_t` and the body's
own drive, and it is the only place in the law where `B` appears **linearly and un-mixed**.

### 1.2 The observationally-equivalent fibre

Take a perturbation `Δ ∈ R^{N_b×K}` and define the twin

```
B'   = B + Δ,      A_b' = A_b − Δ W_b,      G_b' = G_b − Δ W_u,
Σ_b' = Σ_b − (Δ Σ_ζ Bᵀ + B Σ_ζ Δᵀ + Δ Σ_ζ Δᵀ)                                             (TW)
```

Then T1 and T2 match identically, and T3 matches by the `Σ_b'` correction, which is a legitimate PSD matrix
for `‖Δ‖` small enough because `Σ_b = σ_b² I ≻ 0` is interior. T4 does **not** match:
`B' Σ_ζ − B Σ_ζ = Δ Σ_ζ`, and by (S2) this contributes `Φ(ω) Δ Σ_ζ` to `Φ_ba(ω)`, a nonzero rational
function of `ω` unless `Δ Σ_ζ = 0`.

**Therefore:**

> **Proposition 1.** In family L-C the observationally-equivalent fibre through `θ` that leaves `(F, g, T3)`
> fixed and moves `B` is exactly `{Δ : Δ Σ_ζ = 0}`. If `Σ_ζ ≻ 0` the fibre is `{0}` and `B` — hence
> `S^obs,ε` — is **identified from the observational law**, whatever `G_b`, `W_u`, `ρ_u`, `A_b`.
> If `Σ_ζ = 0` the fibre is all of `R^{N_b×K}`, of dimension `N_b·K`, and `B` is completely unidentified.

*(check C3: with `σ_a = σ_o = 0`, a support-flipping twin — turning two structural zeros of `B` into 0.18 and
0.22, both above `ε = 0.05` — matches `Γ_y(k)`, `k = 0..12`, to `1e-16`. With `σ_a = 0.1` the relative gap is
`3.0e-5`; with `σ_a = 0`, `σ_o = 0.05` it is `1.9e-6`.)*

`Σ_ζ = W_b Σ_{ε^o,b} W_bᵀ + σ_a² I` is zero only if **both** `σ_a = 0` (deterministic policy) **and**
`W_b Σ_{ε^o,b} W_bᵀ = 0` (the policy reads noiseless observations, or reads none). Two independent
knife-edges. **So exact non-identifiability is a knife-edge, not an open set.**

### 1.3 How far from the knife-edge — the quantitative answer

The knife-edge verdict is nearly vacuous on its own, so I computed how much passive information there is.
For two stationary Gaussian processes the per-step Kullback–Leibler rate is
`(1/4π) ∫ [tr(Φ₂⁻¹Φ₁) − log det(Φ₂⁻¹Φ₁) − m] dω`. Profiling it over the nuisances `(A_b', G_b', Σ_b')`
with `B' = B + Δ` held at the support-flipping value gives the true statistical distance between "channel is
reachable" and "channel is not":

*(check C3c, toy instance, contract-scale noises)*

| `σ_a` | `σ_o` | profiled KL rate | steps for one nat |
|---|---|---|---|
| 0.10 | 0.05 | `1.08e-2` /step | ≈ **93** |
| 0.02 | 0.05 | `3.21e-4` /step | ≈ **3 100** |
| 0 | 0 | `0` | ∞ |

The rate falls roughly as `σ_a²` (25× less exploration variance → 34× less information). At the contract's
own `σ_a = 0.1`, **a correctly specified passive maximum-likelihood estimator — one that carries a latent
AR(1) `u` with a free `G_b` in its state — identifies the support inside a single 2 000-step episode.**

This is the finding that most matters for D-12, and it is the opposite of the premise round 7 wrote down.

### 1.4 Where the non-identifiability actually lives: the estimator class, not the information set

The frozen comparator is not a latent-variable model. It is a one-step-ahead linear predictor on
`φ_t = [o_t, a_t, a_{t−1}, a_{t−2}, 1]`. Everything in `φ_t` is measurable with respect to the past. For that
class the answer flips, and flips hard.

Project `u_t` on the non-action regressors. Because `W_o o_t` is itself observable, the exogenous residual of
the action is available exactly:

```
ξ_t := a_t − W_o o_t = W_u u_t + ε^a_t
```

Let `ũ_t = u_t − proj(u_t | o_t, …)`, `v_u := Var(ũ_t)`, and `ξ̃_t = W_u ũ_t + ε^a_t`. Then
`π_ξ = Var(ξ̃)^{-1} Cov(ξ̃, ũ)`, and by Sherman–Morrison

```
π_ξ = v_u W_u / (σ_a² + v_u ‖W_u‖²)  =:  κ · W_u / ‖W_u‖² · (…),      κ := v_u /(σ_a² + v_u ‖W_u‖²)
```

Substituting `u_t = π_bᵀ o_t + π_ξᵀ ξ_t + η_t` into the structural equation and re-expressing in `(o_t, a_t)`:

> **Proposition 2 (the passive bias).** The population action coefficient of any past-measurable linear
> one-step predictor converges to
>
> **`B^pass = B + κ G_b W_uᵀ`,  `κ = v_u /(σ_a² + v_u ‖W_u‖²)`, `v_u = Var(u_t | conditioning set)`.**
>
> The bias is **rank one**: the outer product of the confounder's *body* loading with the confounder's
> *policy* loading. It is a fixed-point property, not a finite-sample effect: no amount of data removes it.

*(check C1a: exact to `1.7e-14` at `σ_o = 0`. At `σ_o = 0.05` a second, smaller bias channel appears —
`9.8e-4` — from the errors-in-variables correlation between `ε^{o,b}_t` and `ξ̃_t`. It is real and should be
declared, not ignored.)*

**The crucial fact about `v_u`.** `u_t = ρ_u u_{t−1} + ε^u_t`, and `x_{t+1}` carries `u_t`, not `u_{t−1}`.
So at time `t` no observable dated `≤ t` contains any trace of the innovation `ε^u_t` **except `a_t` itself**.
Hence

```
v_u ≥ σ_u²   for every past-measurable conditioning set,      κ ≥ σ_u² /(σ_a² + σ_u² ‖W_u‖²)  =: κ*
```

*(check C2: `v_u` = 1.043 conditioning on `o_t`; 1.003 on `o_t..o_{t−8}`; **1.002 with four confounded
distractors instead of none**; and it collapses to **0.005** the moment one non-causal regressor `o_{t+1}` is
allowed, taking `κ` from 1.111 to 0.352.)*

Three consequences, all load-bearing for the design:

1. **Lag depth does not help.** A deeper predictor is still past-measurable, so `κ ≥ κ*`.
2. **The number of confounded distractors does not help.** This kills the design tension I expected to find:
   `N_x = 100` hard negatives for the attribution endpoint do **not** deconfound the adaptation endpoint.
   The two endpoints really can share one regime at one `N_x`.
3. **Only a smoother helps** — an estimator allowed to read `o_{t+1}` and later. That is precisely the class
   the working claim excludes ("frozen residual monitor", `comparator-spec.md` §1), and it is also not a
   monitor: it cannot alarm at `t` on evidence from `t+1`.

### 1.5 Verdict on question (1), with the condition stated precisely

> **Exact observational non-identifiability of `S^obs,ε` is a KNIFE-EDGE** — the set `{Σ_ζ = 0}`, i.e.
> `σ_a = 0` **and** `W_b Σ_{ε^o,b} W_bᵀ = 0`, which is measure zero and excluded by the contract's own
> constants. At `σ_a = 0.1` the support-flipped twin is ≈ 93 steps of evidence away *(check C3c)*.
>
> **Non-identifiability of the support by the past-measurable, latent-`u`-free estimator class is an OPEN
> SET**, and this is the operative statement. Its condition is: there exists a pair `(j, k)` with
>
> **`κ* · |G_{b,j}| · |W_{u,k}| > ε`  and  `|B_{jk}| ≤ ε`   (false positive: an unreachable channel labelled reachable)**
>
> or, in the sign-cancelling direction,
>
> **`κ* · |G_{b,j}| · |W_{u,k}| > |B_{jk}| + ε`  with `sign(G_{b,j} W_{u,k}) = −sign(B_{jk})`   (false negative)**
>
> with `κ* = σ_u² /(σ_a² + σ_u² ‖W_u‖²)`. Substituting the contract's `σ_a = 0.1, σ_u = 1.0, ε = 0.05`, the
> false-positive condition reduces to
>
> **`|G_{b,j}| · |W_{u,k}| > 0.05 · (0.01 + ‖W_u‖²)`, i.e. `|G_{b,j}| ≳ 0.05 ‖W_u‖` for `|W_{u,k}| ≈ ‖W_u‖`.**
>
> Every inequality here is strict on an open set of `(G_b, W_u, σ_a, σ_u, B)`. It has non-empty interior, it
> contains the contract's own operating point once `G_b` is switched on at any scale comparable to `B`, and it
> is stable to perturbations of every other parameter. *(check C1: at `G_{b,0} = 0.4`, `W_{u,0} = 0.8`, the
> bias is 0.356 — 7× `ε` and half the largest entry of `B`; a structural zero `B_{1,0} = 0` acquires a fitted
> coefficient of 0.222, 4.4× `ε`.)*

**[opinion]** The honest one-sentence version, which is what any paper must say: *this is not an
identifiability result, it is a conditioning-and-model-class result.* Round 7's flip-to-C condition —
"passive is non-identifiable across a non-knife-edge range" — is never met and, read literally, routes D-12
to B. Read as intended — "is the passive arm of the class we are studying systematically wrong on an open
set?" — it is met decisively. §7 disputes the wording.

### 1.6 The information ratio, which sets expectations

Both arms ultimately learn `B` from exogenous variation in `a`. Per step per actuator:

- passive: `diag(Σ_ζ) = W_b Σ_{ε^o,b} W_bᵀ + σ_a² ≈ 0.0103` *(check C7: `σ_a² = 0.0100` plus `0.00025` from
  the policy reading noisy observations)*
- probe: variance `1.0` on a fraction `p/K = 0.025` of steps → `0.025`

**Ratio ≈ 2.4 : 1** *(check C7)*. The deliberate probe buys a factor of about two in raw exogenous variation,
not a factor of a hundred. **[opinion]** Any claim that the interventional premium is an *information*
premium is therefore wrong at these constants. The premium is that the probe's instrument is **labelled**
(no deconvolution of a coloured latent from a white one is required) and **unconfounded by construction**
(§3). That is a claim about estimator design and robustness, and it should be stated as one.

---

## 2. Question (2): what the frozen `Δ_c` converges to

### 2.1 Master formula

Let `β^pre` be the population projection of `o_{t+1}` on `φ_t` under the pre-event law, `β^post` the same
under the post-event law, and `Σ_φ^post` the post-event second moment of `φ`. The frozen predictor's
innovation satisfies, exactly,

```
E^post[ φ_t r_{t,c} ] = Σ_φ^post ( β^post_{:,c} − β^pre_{:,c} )
```

so with `ǎ` the fit-split-whitened action-lag block and `σ_c` the fit-split innovation scale,

> **Proposition 3.**
> **`Δ_c(t)/√n  →  ‖ (Σ_ã^{fit})^{−1/2} [ Σ_φ^post ( β^post − β^pre ) ]_{ã-block, c} ‖₂ / σ_c^{fit}`**
>
> `Δ_c` measures the **norm of the whitened action-block of the change in the best linear predictor**.
> It grows as `√n` under *any* event that moves that block, and it is `O(√(3K)) = 2.449` under none.

Because `β_a = B(slot τ) + κ G_b W_uᵀ(slot 0)` by Proposition 2, the action block has **two** additive
sources — the structural `B` in the lag-`τ` slot and the confounder bias in the lag-`0` slot
*(check C1b: at both `τ = 0` and `τ = 2` the bias 0.356 sits in the lag-0 slot while `B` sits in the lag-`τ`
slot)*. `Δ_c` is the norm of their **sum**. It cannot tell them apart.

### 2.2 The three events

Write `j` for the latent behind channel `c`, `k` for the event actuator.

**E1, complete loss of actuator `k`.** `B → B P_k`, `G_b` unchanged.
Leading term: `Δβ_a = −B_{jk}` in slot `(τ, k)`; secondary term: `κ` is re-optimised because the closed loop
changed, so the lag-0 bias moves too. Hence

```
Δ_c(E1)/√n  ≈  |B_{jk}| · sd(a_k) / σ_c   +   O(|Δκ| |G_{b,j}| |W_{u,k}| sd(a_k)/σ_c)
```

Note this is `|B_{jk}|`, the **structural** entry — **not** `|β_{a,k,c}|`, the fitted one, which is what
`comparator-spec.md` §3.3 writes. Under `G_b = 0` the two coincide, which is why the error is invisible in
version 6. Under `G_b ≠ 0` they differ by `κ G_{b,j} W_{u,k}`, and the two terms **partially cancel**:
*(check C5, `τ = 0`, `σ_o = 0`)* `Δ_c/√n` on the lost channel falls from **24.5** at `G_b = 0` to **9.2** at
`G_b ≠ 0`. **The confounder attenuates the passive arm's true signal by ≈ 2.7×.** §7 records this as a
correction to the frozen spec.

**E2, confounder-coupling change (`G_b → G_b'` or `W_u → W_u'`).** `B` unchanged, so `S` unchanged.

```
Δβ_a = κ' G_b' W_u'ᵀ − κ G_b W_uᵀ   in the lag-0 slot
Δ_c(E2)/√n  ≈  ‖ κ' G_{b,j}' W_u' − κ G_{b,j} W_u ‖ · sd(a)/σ_c
```

This is **zero if and only if `G_b = G_b' = 0`** (up to the `σ_o` errors-in-variables channel).
*(check C5, `σ_o = 0`, `τ = 0`: under `G_b`-doubling, `Δ_c/√n` on the body block is exactly `0.000` in the
`G_b = 0` regime and `10.6 / 6.96 / 0.00` in the `G_b ≠ 0` regime — against E1's `9.18 / 0.011 / 0.00`.)*

Two things to see in those numbers. First, **E2's `Δ_c` is larger than E1's** on the channel the event
actuator drives. Second, **E2's second-largest `Δ_c` is on `b1`, a channel E1 leaves untouched** (`B_{1,0}=0`,
`G_{b,1} = 0.25`). Because the primary orders channels by `−Δ_c` with "large `Δ` = lost", **under E2 the
frozen arm ranks the most-confounded retained channels as the lost ones.** There are no true negatives under
E2, so the AUC is undefined; the right endpoint is a false-support-alarm rate, and it converges to 1.

**E3, partial loss, column `k` scaled by `γ ≥ γ_min = 0.5`.** `S` unchanged by contract (post-event
re-certification guarantees `γ e_j > ε`).

```
Δ_c(E3)/√n ≈ (1 − γ)|B_{jk}| · sd(a_k)/σ_c   →   Δ_c(E3) < Δ_c(E1),  same channel, same slot, same sign
```

*(check C5, `τ = 0`, `σ_o = 0`: E3 gives 5.43 against E1's 24.5 at `G_b = 0` (ratio 0.22) and 3.39 against
9.18 at `G_b ≠ 0` (ratio 0.37); the naive `(1−γ) = 0.5` is not the ratio because `σ_c` and `Σ_φ` also move.)*
So **`Δ_c` cannot distinguish "the support shrank" from "the gain halved and the support did not"** except
by magnitude, and the confounder compresses that magnitude gap from 4.5× to 2.7×.

### 2.3 Does `Δ_c` distinguish E1 from E2? No.

Under both, `Δ_c → ∞` at rate `√n`. `Δ_c` is one non-negative, sign-blind scalar per channel: the *norm* of a
`3K`-vector. The information that would separate the two is thrown away by the norm:

| | pattern of `Δβ_a` in (channel × lag-slot) |
|---|---|
| E1 | rank one: `B_{:,k} ⊗ e_{(τ,k)}` — one actuator, the lag the plant uses, sign fixed by `−B` |
| E2 | rank one: `ΔG_b ⊗ (κ W_u profile)` — **all** actuators weighted by `W_u`, concentrated at **lag 0** |

These two rank-one patterns are generically distinguishable **from the raw `ĉ_c` vector** (which the spec
computes and then discards): they differ unless the slot profiles coincide (`τ = 0`) *and* the channel
profiles are parallel (`B_{:,k} ∥ G_b`) *and* `W_u ∝ e_k`. That triple coincidence is a knife-edge.

> **Answer to (2).** `Δ_c` converges to `√n × ‖whitened change in the action-block of the best linear
> predictor‖ / σ_c`, which is `√n |B_{jk}| sd(a_k)/σ_c` under E1 (attenuated by the confounder),
> `√n ‖Δ(κ G_b W_uᵀ)‖ sd(a)/σ_c` under E2 (**zero iff `G_b ≡ 0`**), and `√n (1−γ)|B_{jk}| sd(a_k)/σ_c` under
> E3. **It does not distinguish E1 from E2.** It diverges under all three, and under E2 it ranks the most
> confounded *retained* channels highest. The information that would distinguish them survives in the
> un-normed `ĉ_c` (lag profile plus sign), and taking the norm is exactly what destroys it — which is a
> defensible design choice for a *change* detector and a fatal one for a *support* estimator.

---

## 3. Question (3): interventional identifiability

### 3.1 The one-line proof

At an anchor `t_p`, the harness replaces the applied action with `a_{t_p} = S e_k`, `S = ±1` drawn from a
device that is independent of `(z_{t_p}, u_{t_p}, ε^·, history)` — `sequential-ibd-spec.md` §3 constructs it
from a pre-randomised balanced block on a private RNG keyed by `(probe_ns, instance_seed, episode_seed, arm)`
with no state input. Then for any `h`:

```
E[ b_{t_p+h} | S=+1 ] − E[ b_{t_p+h} | S=−1 ]
```

Expand `b_{t_p+1+τ} = A_b b_{t_p+τ} + B a_{t_p} + G_b u_{t_p+τ} + ε^b`. Every term other than `B a_{t_p}` has
the **same conditional expectation in both sign groups**, because `S ⫫ (b, u, ε)`. Therefore at the first hit
`h = τ + 1`:

```
E[D^{τ+1}_c | S=+] − E[D^{τ+1}_c | S=−]  =  2 (B e_k)_j · gain_c        exactly
```

(the `− o_{t_p}` term in the increment also cancels between groups, by the same independence). Propagating
under the default policy thereafter,

```
E[D^{h}|+] − E[D^{h}|−] = 2 (F^{h−1−τ} B e_k)_j   for the body,  and the corresponding C_d-chain for d.
```

> **Proposition 4.** The probe-conditioned sign contrast at `h = τ+1` identifies `2 B e_k` **exactly**,
> for every `k`, with **no dependence on `G_b`, `W_u`, `ρ_u`, `A_b`, `σ_a`, `σ_u`, or the policy at all**.
> Hence the support change under E1 — `B e_k → 0`, contrast `→ 0` on every channel of the lost set — is
> identified irrespective of the confounding.

*(check C4: Monte Carlo, `τ ∈ {0,2}`, `G_b` scaled by 0, 1 and 4. The contrast recovers `2B_{:,0} = [1.4,0,0]`
to ≤ 0.064 even at `4×` the body confounding, with ≈ 10 000 units per sign group.)*

This is the entire interventional advantage, and it is worth being precise about what it is *not*. It is not
that the passive law lacks the information (§1.3 says it does not). It is that the probe converts a
**deconvolution problem** — separate a white instrument from a coloured latent inside the same observed
scalar `ξ_t` — into a **two-sample mean difference on a known label**. No model of `u` is needed, no `ρ_u`,
no `G_x`, no spectral factorisation.

### 3.2 Under E2 and E3

- **E2.** `G_b` and `W_u` do not appear in Proposition 4. The population contrast is **exactly unchanged**
  pre- and post-event, on every channel, at every horizon. The interventional arm correctly reports *no
  support change*. Its `a_c` statistic (a rank-sum `z` over the same units) is likewise unchanged in
  distribution. **This is the cell the whole of option C rests on.**
- **E3.** The contrast at `(k, τ+1)` becomes `2 γ B_{jk}`: it moves, proportionally and detectably, but the
  *label* rule (`in S iff effect > ε`) is unchanged as long as `γ|B_{jk}| > ε`, which contract `γ_min` plus
  post-event re-certification guarantees. So the interventional arm detects a change in `R` while leaving `S`
  correct — which is exactly what contract §D's E3 row predicts. The frozen `a_c` (a rank statistic) falls by
  roughly the ratio of standardised effects but stays above the null floor.

### 3.3 A mismatch to declare, not to repair

Contract C2/C4 define the operational effect with **later actions set to zero** (`do(a_t = a, later actions
0)`). The spec's probes are single-step (`L = 1`) and the policy resumes at `t_p+1`, so the contrast at
`h > τ+1` measures the **closed-loop** impulse response `F^{h−1−τ}B`, not the open-loop `A_b^{h−1−τ}B` the
ground truth uses. At `h = τ+1` they coincide exactly, so identification of `B` (and of the E1 support change)
is unaffected; at `h = τ+2, τ+3` the arm and the oracle are measuring different objects. `sequential-ibd-spec.md`
§4 takes a max over `h`, so this leaks in. It is a limitation of the estimand-to-statistic mapping, not an
identification failure, and it should be stated in the spec rather than fixed by zeroing post-probe actions
(which would change the plant).

---

## 4. Question (4): the endpoint pair for option C, and the prediction table

### 4.1 The design

Two arms × three events × two confounding regimes, **all cells on the same instance draws, the same noise
streams, and the same `N_x`**, so that no comparison ever changes two variables at once (round 6 §3's defect).

- Regimes: **C+** = `G_b ≠ 0, G_x ≠ 0`; **C−** = `G_b = 0, G_x ≠ 0`. `G_x` present in both, so the
  attribution hard negatives exist in both and the only thing that moves is the body confounding.
  (Note this is a *different and better* "absent" construction than v3.9's `absent.G[:] = 0`, which zeroes
  `G_x` and thereby collapses the `ρ_min` witness — `comparator-spec.md` §1.1. See §6.)
- Endpoints, both read at the same offsets on the same episodes:
  - **ATT** — full-channel AUC of the arm's secondary statistic against `S^obs,ε(post)` over all `C`
    channels, confounded distractors as hard negatives.
  - **ADA** — pre-event-support AUC of the arm's primary statistic after **E1** (positives = retained,
    negatives = lost), i.e. contract D-11.1a.
  - **FSA** — for **E2** and **E3**, where `S` does not change, ADA is undefined and the endpoint is the
    **false support-alarm rate**: the proportion of pre-event-support channels the arm moves past its own
    ARL₀-matched operating point within `w_T` of the event. FSA must be predeclared as the E2/E3 endpoint,
    not substituted after the fact.
- **A third arm is required [opinion, strongly held]:** a *deconfounded passive* arm — the same frozen
  residual monitor whose predictor additionally carries `L` lags of the confounded distractor block. §1.4
  predicts it changes **nothing** (`v_u` floors at `σ_u²`). If it closes the gap, the finding is about
  predictor design and the paper collapses; preregistering it is the cheapest way to make the claim
  attackable in advance rather than in review.

### 4.2 Prediction table (population-level signs, one execution round to confirm or refute)

`P` = frozen passive residual monitor (`Δ_c` primary, loading `l` secondary).
`I` = sign-randomised probe arm. `Δregime` = value in C+ minus value in C−.
"↑ / ↓ / 0" are signs of the population quantity; `I − P` is the signed arm difference on that endpoint.

| # | Endpoint | Event | Regime | P (frozen passive) | I (probe) | **sign of `I − P`** | basis |
|---|---|---|---|---|---|---|---|
| 1 | ATT | E1 | C− | depressed (confounded `x` keep a large loading) | high | **+** | round 5/6 reproducible +0.16…+0.24; spec §2 |
| 2 | ATT | E1 | C+ | depressed; `G_b` slightly *raises* loadings on body positives | **identical to C−** | **+**, magnitude ≤ row 1 | Prop. 4 ⇒ `ΔregimeI = 0` |
| 3 | ATT | E2/E3 | either | unchanged (`l` is frozen at fit time) | unchanged | **+** | spec §4.2 |
| 4 | **ATT invariance** | any | C+ vs C− | `ΔregimeP ≠ 0` | **`ΔregimeI = 0`** | — | Prop. 4; the sharpest falsifier in the design |
| 5 | ADA | E1 | C− | **high** (0.88–1.00 in round 6) | lower (0.69–0.81) | **−** | reproduces round 6 §1; must be reproduced or the round is broken |
| 6 | ADA | E1 | C+ | **strictly lower than row 5** | **identical to row 5's `I`** | **−**, strictly less negative | Prop. 2 + `Δ_c(E1)` attenuation 24.5→9.2 *(check C5)* |
| 7 | ADA | E1 | C+ vs C− | **`ΔregimeP < 0`** — the **primary prediction** | `ΔregimeI = 0` | — | two mechanisms: signal attenuation and rank contamination |
| 8 | **FSA** | **E2** | **C−** | **0** — exactly blind | **0** | **0** | `Δ_c ≡ 0.000` at `σ_o = 0` *(check C5)*; Prop. 4 |
| 9 | **FSA** | **E2** | **C+** | **→ 1** — alarms, and ranks retained confounded channels as lost | **at nominal level** | **+ (large)** | `Δ_c/√n = 10.6` on `b0`, **6.96 on `b1` which E1 does not touch** *(check C5)*; Prop. 4 |
| 10 | **FSA arm × regime** | E2 | C+ vs C− | **`ΔregimeP > 0`, large** | **`ΔregimeI = 0`** | — | **the headline: a 2×2 crossover for P, a flat line for I** |
| 11 | FSA | E3 | C− | fires (`Δ_c ∝ (1−γ)\|B_{jk}\|`), 5.4 vs E1's 24.5 | fires (contrast `→ 2γB`), label unchanged | ≈ **0** | both are wrong to alarm; E3 is the control event |
| 12 | FSA | E3 | C+ | fires, 3.4 vs E1's 9.2 — **gap compressed** | unchanged from C− | ≈ **0**, gap narrower for P | *(check C5)* |
| 13 | ADA/ATT | E1 | either | third arm (deconfounded passive) **= P**, no improvement | — | — | `v_u ≥ σ_u²` *(check C2)*; refutes the "just add lags" objection |

Rows 8–10 are the paper. Rows 1–4 are the attribution half, already reproducible, now measured under the
same regime as the adaptation half. Rows 5–7 are the adaptation half, whose sign is *predicted to stay
negative* — the passive arm still wins the E1 tracking task — with the regime effect, not the arm ordering,
carrying the claim. Row 13 is the pre-registered self-attack.

**[opinion]** Do **not** design the round around flipping row 6's sign. Making `I − P` positive on ADA needs
`κ*‖G_b‖‖W_u‖ ≳ ‖B_{:,k}‖` (§5), which pushes `G_b` into a range where the saturation certification starts
rejecting instances (§6). Rows 8–10 need only `G_b` large enough to clear the null scale, which is far
cheaper. A round designed to produce a crossover will fail; a round designed to produce a dissociation will
succeed or cleanly fail.

---

## 5. Question (5): finite-sample caveat at `p = 0.05`, `W = 500`, `K = 2`

### 5.1 The probe contrast's standard error relative to its population effect

A 500-step window at `p = 0.05` with the spec's `Π = 20` cadence holds exactly **25 probe units**
(`sequential-ibd-spec.md` §4). Balanced blocks over `2K = 4` cells give **≈ 6.25 units per (actuator, sign)
group**. For the two-group mean difference at `h = τ+1`:

```
SE( contrast )  =  sd(D^{τ+1}_c) · sqrt(1/n₊ + 1/n₋)  =  sd(D) · sqrt(2/6.25)  =  0.566 · sd(D)
population effect  =  2 |B_{jk}| · gain_c   ≥  2 c_min = 0.40
```

The controlling quantity is `sd(D^{τ+1}_c)`, and the point that matters is that it is **`O(sd(b))`, not
`O(σ_b)`**: the increment `o_{t_p+h} − o_{t_p}` carries the state's own excursion, and under confounding the
state's variance is dominated by the `u`-path `g u_t` with `Var(u) = σ_u²/(1−ρ_u²) = 2.78`.

*(check C6, toy instance, contract-scale noises)*

| | `sd(D^{τ+1})` on the driven channel | effect `2\|B\|` | SE | **SE / effect** |
|---|---|---|---|---|
| `τ = 0` | 1.06 | 1.40 | 0.60 | **0.43** |
| `τ = 2` | 2.61 | 1.40 | 1.48 | **1.05** |

> **Order of the answer: SE / effect is `O(1)` per window — roughly 0.4 at `τ = 0` and 1.0 at `τ = 2`.**

This is consistent with the spec's own measured `z` values (round 4: direct channels 2.65–2.69 against a null
floor of 1.44–1.54, i.e. ≈ 1.2 `z`-units of separation), which is an independent cross-check that the order
is right and not an artefact of my toy.

Pooling: `4` scored episodes × `10` instances, with intervals clustered by instance, buys `√40 ≈ 6.3` on the
cell margin, giving **≈ 7σ at `τ = 0` and ≈ 3σ at `τ = 2` on the cell mean, and ≈ 1σ per episode.** That
per-episode `1σ` is the same fact as round 6's coarse AUC lattice, seen from the other side; it is not a new
problem, but it does mean the design cannot rest on any single-episode statement.

### 5.2 The regime where the passive bias exceeds the interventional standard error

Put both on the scale of the action coefficient `B_{jk}`:

```
passive bias           =  κ* |G_{b,j}| |W_{u,k}|,      κ* = σ_u²/(σ_a² + σ_u²‖W_u‖²)
interventional SE(B̂)   =  0.283 · sd(D^{τ+1}_c) / √N_w        (N_w = independent windows pooled)
```

> **Condition:  `κ* |G_{b,j}| |W_{u,k}|  >  0.283 · sd(D^{τ+1}_c) / √N_w`.**

Evaluated at the check's toy scales (`κ* ≈ 1.11`, `|W_{u,k}| = 0.8`, `sd(D) = 1.06 / 2.61`,
`‖B_{:,k}‖_∞ = 0.70`), and expressing `G_b` relative to `B` as the brief asks:

| pooling | `τ = 0` | `τ = 2` |
|---|---|---|
| single 500-step window (`N_w = 1`) | `‖G_b‖_∞ ≳ 0.85 ‖B_{:,k}‖_∞` | `≳ 2.1 ‖B_{:,k}‖_∞` |
| pooled cell (`N_w = 40`) | `‖G_b‖_∞ ≳ 0.13 ‖B_{:,k}‖_∞` | `≳ 0.33 ‖B_{:,k}‖_∞` |

> **Recommended sampling regime: `‖G_b‖_∞ ≈ ‖B_{:,event_actuator}‖_∞` (ratio 1), with a declared sensitivity
> arm at `0.5×` and `2×`.** At ratio 1 the passive bias sits ≈ 7× the pooled interventional SE at `τ = 0` and
> ≈ 3× at `τ = 2`, and ≈ 1.2× / 0.5× the single-window SE. Below ratio ≈ 0.15 the identifiability advantage
> is swamped by variance at every pooling level and the round has no power. Above ratio ≈ 2 the saturation
> certification starts to bind (§6).

Note the `τ = 2` column is uniformly worse, by a factor `sd(D³)/sd(D¹) ≈ 2.5`: the increment at `h = 3` has
absorbed three steps of closed-loop state excursion. **[opinion]** If the round must be boxed, run `τ = 0`
as primary and `τ = 2` as a declared secondary, and say so before seeing outcomes.

---

## 6. Question (6): minimal generator change, and what breaks

### 6.1 Lines that change

**§B, family L, third bullet** — the one substantive line:

```
- b_{t+1} = A_b b_t + B_t a_{t−τ} + ε^b_t
+ b_{t+1} = A_b b_t + B_t a_{t−τ} + G_b u_t + ε^b_t
```

**§B, family L, fifth bullet** — rename, and this rename is load-bearing:

```
- x_{t+1} = A_x x_t + G u_t + ε^x_t
+ x_{t+1} = A_x x_t + G_x u_t + ε^x_t
```

`comparator-spec.md` §1.1 constructs the confounder-absent arm by `absent.G[:] = 0.0`. Under L-C that
attribute is ambiguous and would silently zero **both** couplings, destroying the "`G_x` present in both
regimes" requirement of §4.1 and reproducing round 6's error in mirror image. The rename must land in the
generator, the two specs and the gate together.

**§B, family N** — `+ G_b u_t` **outside** the `tanh`, so the confounder is not saturated and family N
reduces to L-C at `κ_N = 0, s → ∞`. State the choice; the alternative (inside) makes the confounder path
nonlinear and is a different plant.

**§A0** — `"G on the confounded half of x"` → `"G_x on the confounded half of x; G_b on the body block"`,
plus the sampling rule:

```
G_b = g_scale · ‖B_{:, event_actuator}‖_∞ · s ⊙ v,   v ~ Unif(S^{N_b−1}),  s ~ Rademacher,
      supported on a declared subset of body components that MUST include the CL-4 component (see 6.2),
g_scale ∈ {0 (absent), 1 (present)}, sensitivity {0.5, 2}
```

Draw `G_b` from a **dedicated, appended noise key**, not by inserting it into the shared configuration
stream. Otherwise every seed 0–9 draws a different `A_b, B, C_d, W_o, W_u` and **every number in rounds 5 and
6 becomes non-comparable**. With an appended key, `g_scale = 0` reproduces frozen version 6 bitwise and L-C is
a strict superset.

**§0 registry** — `ρ_min` → `ρ_min,x` (0.4, unchanged); new rows `g_scale`, `β_min` (see 6.2).

**§D events table** — E2 has no row today. Add:

| Event | Mechanism | Predicted effect |
|---|---|---|
| confounder-coupling change | `G_b ← G_b'` or `W_u ← W_u'` | `R` unchanged; `S^latent`, `S^obs,ε` unchanged (C2's `do`-difference cancels `G_b u`); the observational law changes |

**§A variables table** — `u`'s "Action ancestor? no" is still correct, but `u` is now a parent of `b`, so
**T-E1a** (which asserts the graph shape) must be widened from "`u`'s children are the confounded `x`" to
"`u`'s children are the confounded `x` and the declared body components". If the gate hard-codes the former,
it fails on every L-C instance.

**§G confounder-absent construction** — `absent.G_b[:] = 0.0`, `G_x` untouched, no re-certification needed.

### 6.2 The `ρ_min` witness "on `b` as well as `x`" — the naive version certifies nothing

`ρ_min` is `max_{k,j} |corr(a_k, x_j)| ≥ 0.4`. Transplanting it to the body — `max |corr(a_k, b_j)| ≥ ρ_min`
— **is vacuous**: `a_k` and `b_j` are correlated through the causal path `B` and the feedback `W_o` whether or
not `G_b` is zero, so every version-6 instance already passes it. It would certify the presence of control,
not the presence of confounding.

The witness that means something is the **passive-bias witness**, which is exactly the quantity Proposition 2
identifies and is computable in closed form at draw time from the Lyapunov solution:

```
β_witness := max_{j,k}  κ* |G_{b,j}| |W_{u,k}|,     κ* = σ_u² / (σ_a² + σ_u² ‖W_u‖²)
certify:   β_witness ≥ β_min,   with β_min ≥ 2ε = 0.10 recommended (§5.2 sets the operative floor)
```

Equivalently and more directly: fit the population one-step projection on `(o_t, a_t)` from the exact
stationary covariance and certify `max_{j,k} |β_a[j,k] − B[j,k]| ≥ β_min`. That is a handful of matrix
operations, it is exact, it needs no Monte Carlo, and it certifies the thing the benchmark is about.

### 6.3 What breaks in the current certification

| item | verdict |
|---|---|
| **Closed-loop radius** | **Does not break.** `G_b` does not enter the closed-loop `A`-matrix on `[b_t,…,b_{t−τ}; d_t; a_{t−1},…,a_{t−τ}]`; `u` is exogenous with `\|ρ_u\| < 1`. `ρ_cl ≤ 0.98` is untouched. |
| **Saturation fraction ≤ 0.05 (OP-16)** | **This is what binds.** `G_b u` adds `‖G_b‖·σ_u/√(1−ρ_u²) ≈ 1.67‖G_b‖` of body sd, amplified by `1/(1−ρ_cl)`, which feeds `W_o` and pushes `\|a\|` toward `a_max = 2`. The body already carries a `u`-path through `B W_u`, so at `g_scale = 1` this is roughly a doubling, not a new phenomenon — but the resampling rate rises and contract L4's "generator configuration with rejection rate above 20 percent is itself rejected" is the live risk. **Measure the rejection rate at `g_scale ∈ {0.5, 1, 2}` before freezing.** |
| **Family N `T-L9b`** (`\|z\| ≤ 100`, four-group stationary-mean agreement within `δ_inv`) | Tightens for the same reason; the quadratic term's non-negative offset now sits on top of a larger `u`-driven excursion. Expect more sub-seed rejections. |
| **CL-4 construction** | **Breaks in the sense that matters, and this is the single most important item.** CL-4 currently certifies that the dominant body component `j*` of `event_actuator` is driven by no other actuator and fed by no other body component. Under L-C it must **additionally require `G_{b,j*} ≠ 0`**. Without that, the passive arm's bias never touches the channel the primary scores, `Δ_c` behaves exactly as it does in version 6, and option C reproduces round 6's fatal defect — a primary the treatment cannot reach — with the roles of the two arms swapped. Add `G_b` support ∩ CL-4 component ≠ ∅ to `draw_certified`, and add a gate fixture for the violation. |
| **Label consistency E1b, C1, C2, C3, C4** | **Do not break.** The zero-noise finite-difference and the graph reachability are both `do`-differences from the same `z̄`; `G_b u_t` is identical in both arms and cancels. Family N's `z̄` moves (it must be re-estimated, as CL-8 already requires), but the labels themselves are invariant. This is the reassuring half of L-C: **the ground truth is untouched, only the estimation problem changes.** |
| **T-E2d** (confounding severed under randomised `do(a)`) | Unaffected as written — it tests `(a_k, x_j)` pairs. Do **not** extend it to `(a_k, b_j)`: under randomised `do(a)` the action–body correlation is causal and must not be severed. |
| **`freeze-manifest.txt` / hash `38d161e762a3de76`** | Invalidated regardless. With the appended-key discipline of §6.1, `g_scale = 0` reproduces version 6 bitwise, so the invalidation is a version bump rather than a new benchmark. Without it, rounds 5 and 6 are not comparable to anything L-C produces. |

---

## 7. Verdict, disputes, and falsifiers

### 7.1 Is option C worth one execution round?

**[opinion] Yes — re-scoped, boxed to one round, with the primary moved from E1-adaptation to the E2 × regime
dissociation, and with the deconfounded-passive third arm preregistered.**

**The single strongest reason FOR.** Rows 8–10 of §4.2 are a genuine double dissociation with signs fixed in
advance by closed-form population limits on both arms, and the two cells that carry it are exactly the two
cells that are `0.000` and `10.6` *(check C5)* — a contrast that cannot be produced by tuning, cannot be
produced by the event construction (unlike round 6's CL-4 flattery), and is invariant to the estimator's
implementation because it follows from Propositions 2 and 4 rather than from a statistic's details. It costs
one term in one structural equation, one events-table row, and one certification predicate. Nothing else in
six rounds has had its sign known before the run.

**The single strongest reason AGAINST.** The premise D-12 was written on is false. §1.3 shows the passive
information set *does* identify the support, and at `σ_a = 0.1` identifies it inside one episode (≈ 93 steps
per nat). So option C cannot claim an identifiability result; it can only claim that **one frozen
model class** — a past-measurable predictor with no latent `u` — is systematically wrong on an open set.
That is a real claim and a correct one, but it is a claim about a baseline's misspecification, which sits
closer to round 7's (b)/(c) scores than to the 3.5–4 the tally gave the *question*. A referee who asks "why
not fit a state-space model with a latent AR(1) confounder?" has a complete answer, and the paper must
concede it in the abstract rather than in the rebuttal.

### 7.2 Evidence that would change my verdict

1. **The rejection rate.** If certifying `β_witness ≥ 2ε` at `g_scale = 1` pushes the generator's resampling
   rate above contract L4's 20 percent — most likely through the saturation clause (§6.3) — the family is not
   certifiable at a useful `G_b` and I would go to **B**.
2. **The null scale.** If a population computation on the *actual* generator (not my toy) shows `Δ_c`'s E2
   response in C+ is within Monte Carlo of the `√(3K) = 2.449` null at the certifiable `G_b`, row 9 is
   unreachable and I would go to **B**.
3. **The third arm.** If a passive predictor carrying lags of the confounded distractors closes the ADA or
   FSA gap, §1.4's `v_u ≥ σ_u²` argument is wrong somewhere and the finding is about predictor design, not
   about intervention. I would go to **A** and write it up as a short note on residual-monitor
   misspecification.
4. **Row 5 failing to reproduce.** If the E1/C− adaptation cell does not reproduce round 6's `P > I`, the
   generator changed under us and nothing in the round is interpretable.

### 7.3 Disputes with `round7-adjudication.md`

- **§4, the D-12 decision rule (principal dispute).** "If passive is non-identifiable across a non-knife-edge
  range and probing identifies: freeze C … otherwise B." The derivation says passive *is* identifiable
  (Prop. 1) and probing *does* identify (Prop. 4), so the rule as written routes to **B** — which I do not
  think is what the adjudication intended. The condition should be restated as a **conditioning and
  model-class** condition: *"if the frozen residual-monitor class carries an asymptotic support-labelling
  bias exceeding `ε` on an open set of `(G_b, W_u)`, and the probe contrast is exactly invariant to that
  path"* — which **is** met, with the explicit inequality in §1.5.
- **§1, row (d), scored 3.5–4.** Partly on the ground that IBD "excludes it by assumption". The derivation
  shows *why* it can be excluded harmlessly: `G_b` leaves `S^latent`, `S^obs,ε`, `R` and `M` all invariant
  (C2's `do`-difference cancels it). L-C is therefore not a new estimand, only a harder estimation problem
  for one estimator class. **[opinion] (d) is a 3, not a 3.5–4**, and the novelty properly belongs to the
  E2 × regime dissociation, not to the plant.
- **§2, "the decisive test for option C is an analytic identifiability derivation … which costs nothing to
  build".** The cost was never the issue. The issue is that a binary identifiability question does not have
  a binary answer here — the answer is "identified, with `O(σ_a^{-2})` conditioning" — and a decision rule
  built on the binary framing cannot consume it. **[opinion]** Process note: the same failure mode as
  D-11.1a. A decision rule was written before anyone checked that the quantity it names is two-valued.
- **§3, "the comparator's win was flattered by CL-4".** Accepted and *sharpened*: under L-C, CL-4 must be
  crossed with `G_b`'s support or the same flattery recurs in the opposite direction (§6.3). Nothing in
  round 7 flags this, and it is the most likely way option C fails by construction rather than by evidence.
- **Not disputed:** §3's withdrawal of the dissociation sentence, the `τ = 0` floor being "undetermined",
  GM6-06's partial reinstatement, the §7 wording correction, and the "reproducible means three
  implementations of one spec" reading. All four are right.

### 7.4 One correction to a frozen spec, for the record

`comparator-spec.md` v3 §3.3 states that after complete loss of actuator `k`, `Δ_c` grows as
`√n · |β_{a,k,c}| · sd(a_k) / σ_c` — the **fitted** coefficient. The correct population limit uses the
**structural** entry `|B_{jk}|` (Prop. 3). Under `G_b = 0` the two coincide, so version 6 is unaffected and
nothing in round 6 is invalidated. Under L-C they differ by `κ G_{b,j} W_{u,k}` and the difference is not a
detail: it is the mechanism by which the confounder both **attenuates** the passive arm's E1 signal
(24.5 → 9.2, *check C5*) and **mimics** it under E2 (0.000 → 10.6). The sentence should be amended before any
L-C freeze.
