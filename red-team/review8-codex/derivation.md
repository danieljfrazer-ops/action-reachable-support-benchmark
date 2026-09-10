# Round 8 derivation — Codex

Date: 9 September 2026. This is a population derivation, not a simulation. Any numerical quantities below are arithmetic implications of the frozen constants, not experimental results. Opinion is marked explicitly.

## Verdict first

The proposed open-set non-identifiability conclusion does **not** follow for the contract-v3.9 family. A body-reaching latent common cause makes a naive or frozen passive regression confounded, but the observational law at all lags contains more information than that regression. In particular, the contract has independent action noise with `sigma_a = 0.1`. Its unpredictable component is passive excitation, and (away from singular cases) it identifies the action coefficient separately from the persistent `u` path. Exact E1/E2 observational equivalence exists when the affected action direction has no independent innovation, or when temporal separation itself degenerates, but those are knife-edges in the contract's parameter space, not an open set.

Randomised probes nevertheless identify the causal column of `B` directly and make the E1/E2 distinction without a latent-state model. Thus option C contains a useful robustness question, but the derivation does not supply the adjudication's proposed trigger for C.

## 1. Passive observational law and identifiability

### 1.1 All stationary second-order statistics in one expression

Let

\[
A_z=\begin{bmatrix}
A_b&0&0&0\\ C_d&A_d&0&0\\0&0&A_w&0\\0&0&0&A_x
\end{bmatrix},\quad
B_z=\begin{bmatrix}B\\0\\0\\0\end{bmatrix},\quad
G_z=\begin{bmatrix}G_b\\0\\0\\G_x\end{bmatrix},
\]

and write the observation map, including assignment and gain but not observation noise, as `M`, so `o_t=M z_t+epsilon^o_t`. Clipping is absent in this population analysis.

For `tau=0`, take `q_t=[z_t;u_t]`, `eta_t=[epsilon^z_t;epsilon^u_t;epsilon^o_t;epsilon^a_t]`, and define

\[
C_a=[W_oM\;W_u],\qquad D_a=[0\;0\;W_o\;I_K].
\]

Then

\[
q_{t+1}=Fq_t+L\eta_t,qquad
y_t:=\begin{bmatrix}o_t\\a_t\end{bmatrix}=Hq_t+D\eta_t,
\]

where

\[
F=\begin{bmatrix}
A_z+B_zW_oM&G_z+B_zW_u\\0&\rho_u I
\end{bmatrix},
\]

\[
H=\begin{bmatrix}M&0\\W_oM&W_u\end{bmatrix},
\]

and `L,D` place the independent innovations in the equations just displayed; in particular the top state row of `L` contains `I` for `epsilon^z`, `B_z W_o` for `epsilon^o`, and `B_z` for `epsilon^a`, while the `u` row contains `I` for `epsilon^u`. If

\[
Q=\operatorname{diag}(Q_z,Q_u,Q_o,Q_a),
\]

then stationarity gives the discrete Lyapunov equation

\[
P=FPF^\top+LQL^\top.
\]

Every requested covariance is consequently

\[
\Gamma_y(0)=HPH^\top+DQD^\top,
\]

\[
\Gamma_y(h)=\operatorname{Cov}(y_{t+h},y_t)
=HF^hPH^\top+HF^{h-1}LQD^\top,\qquad h\ge1,
\]

with `Gamma_y(-h)=Gamma_y(h)^T`. The `oo`, `oa`, `ao`, and `aa` blocks are exactly the cross-covariances of `o` and `a` at all lags. This writes them as functions of `A_b,B,G_b,W_o,W_u,rho_u`, the remaining structural blocks, observation map, and all noise scales.

For `tau>0`, augment `q_t` by `[a_{t-1};...;a_{t-tau}]`. The first lag row is `a_t=C_a q_t+D_a eta_t`, subsequent lag rows shift by identity, and the `z` row uses `B_z` times the last lag. The same Lyapunov and covariance formulas hold. Thus delay changes `F,L,H,D`, not the result.

After an event, replace the relevant entries of `B`, `G_b`, or `W_u` in these matrices, solve the post-event Lyapunov equation, and use the same formulas. Gaussianity means that equality of the mean and all these covariances is equality of the complete observational law.

### 1.2 A scalar submodel exposes what is and is not ambiguous

It is enough to inspect one body/actuator direction after partialling out observed state and feedback. Set `tau=0` for notation, write

\[
u_t=\rho u_{t-1}+\epsilon^u_t,\quad
r_t=w u_t+\eta_t,\quad
y_t=b_{t+1}-A b_t=B r_t+g u_t+\xi_t,
\]

where `r_t` is the action innovation left after the observed policy term, `eta_t` is its independent component, `g` is the relevant entry/direction of `G_b`, and

\[
q_u=\operatorname{Var}(u_t)=\frac{\sigma_u^2}{1-\rho^2}.
\]

For `ell>=1`,

\[
S_\ell:=\operatorname{Cov}(r_t,r_{t-\ell})=w^2q_u\rho^\ell,
\]

while

\[
S_0=w^2q_u+\sigma_\eta^2.
\]

Similarly,

\[
C_\ell:=\operatorname{Cov}(y_t,r_{t-\ell})=(Bw+g)wq_u\rho^\ell,\quad \ell\ge1,
\]

and

\[
C_0=(Bw+g)wq_u+B\sigma_\eta^2.
\]

For `rho != 0`, all-lag statistics identify

\[
\rho=S_2/S_1,qquad
\sigma_\eta^2=S_0-S_1/\rho,qquad
B=\frac{C_0-C_1/\rho}{\sigma_\eta^2}.
\]

For a known nonzero delay, the same argument uses the covariance at the matching action lag: the independent action innovation creates a covariance discontinuity at exactly the causal lag, whereas the `u` contribution follows the smooth AR covariance sequence. With unknown delay in the finite set `{0,1,2}`, the location of that discontinuity identifies it generically.

This calculation is deliberately a submodel: it is not offered as a complete estimator for noisy multichannel observations. It is decisive against the claimed open-set impossibility. If E1 and E2 were observationally equivalent on an open set of the full model, they would remain so on a regular submodel. Here they do not.

### 1.3 Exact E1/E2 equivalence and its size

If `sigma_eta^2=0`, then `r_t=w u_t` and

\[
y_t=(B+g/w)r_t+\xi_t.
\]

Starting from the same pre-event parameters, post-E1 has `B'=0,g'=g`. Post-E2 can retain `B` and choose

\[
g'_{E2}=g-Bw.
\]

Both post-event laws then have the same coefficient `g/w` and the same Gaussian observational law, while E1 removes the action edge and can shrink `S^{obs,epsilon}` and E2 does not. This is genuine non-identifiability.

It is, however, confined to `sigma_eta^2=0`. In the ordinary parameterisation where `Q_a` ranges over positive-definite covariance matrices, singularity in the affected action direction is a boundary of measure zero and has empty interior. `rho=0` is another temporal-separation degeneracy; it too is a knife-edge relative to the contract value `rho_u=0.8`.

In multiple dimensions the corresponding condition is:

\[
v^\top Q_{a,\mathrm{ind}}v=0
\quad\text{and}\quad
G_b\Sigma_u W_u^\top v\ne0
\]

for an affected actuator direction `v` (with the obvious lagged transfer factors). The first clause removes independent passive excitation in that direction; the second makes the latent common-cause path active. If `Q_{a,ind}` is positive definite, no such `v` exists.

The precise condition for **confounding**, as distinct from non-identifiability, is that the relevant action/body directions have a nonzero common-cause cross-transfer. At lag zero this is

\[
e_j^\top G_b\Sigma_u W_u^\top e_k\ne0,
\]

or, over all lags, that the corresponding transfer polynomial is not identically zero. Saying merely `G_b != 0` and `W_u != 0` is insufficient: their active subspaces may be orthogonal. Conversely, this nonzero product creates omitted-variable bias but does not erase the identifying information in a positive-definite `Q_a`.

**Conclusion for question 1.** Under contract v3.9's `sigma_a=0.1`, independent keyed action noise, `rho_u=0.8`, and a nonsingular affected action direction, no open set of E1/E2 observational equivalences has been shown; the scalar algebra shows why the proposed construction fails. The equivalence set above is a knife-edge. Therefore “passive support tracking is non-identifiable in principle however good the detector” would overclaim. What is justified is: a passive estimator that fails to exploit the independent innovation or fit the latent dynamics can be confounded.

## 2. Frozen residual monitor

Let `r_{t,c}^{pre}` be the residual from the predictor fitted before the event, and let `L_c(theta)` be the population linear projection coefficient from the lagged-action vector to channel `c` under parameters `theta`, after projecting the other fitted regressors. With `u` omitted,

\[
L_c(theta)=L^{causal}_c(B)+L^{conf}_c(G_b,W_u,\rho_u,Q),
\]

where in the scalar contemporaneous reduction

\[
L^{conf}=g\frac{\operatorname{Cov}(u,r)}{\operatorname{Var}(r)}
=g\frac{wq_u}{w^2q_u+\sigma_\eta^2}.
\]

The pre-event fitted coefficient absorbs this second term. In a stationary post-event window,

\[
\widehat c_c\ \longrightarrow\
\operatorname{Cov}(r^{pre}_{t,c},\widetilde a_t)
=\{L_c(theta_{post})-L_c(theta_{pre})\}\operatorname{Cov}(\widetilde a_t)
\text{terms from changed projection geometry},
\]

and therefore

\[
\frac{\Delta_c}{\sqrt n}\ \longrightarrow\
\left\|\Sigma_{a,pre}^{-1/2}
\operatorname{Cov}(r^{pre}_{t,c},\widetilde a_t)\right\|_2.
\]

- Under E1, the causal part carried by column `k` disappears. Generically the limit is positive and `Delta_c` diverges as `sqrt(n)`; `raw_support=-Delta_c` falls.
- Under E2, changing `G_b` or `W_u` changes the absorbed confounding coefficient and usually the action covariance/projection geometry. Generically the same limit is positive and `raw_support` also falls. It is zero only when the event leaves the projected coefficient and geometry unchanged (for example, an orthogonal coupling change).
- Matching the **scalar score**, or even the vector residual covariance, is easy: choose the E2 change so `Delta L_conf=-L_causal(B_k)`. This does not imply equality of the complete all-lag observational law.

Thus comparator v3 does not distinguish E1 from E2. Its sign-blind score correctly reports “the pre-event action/residual relation changed,” not “the causal action edge was lost.” The statement in comparator v3 section 3.3 that the pre-event predictor is “still correct” under the null is also too strong once E2 is admitted as a support-preserving null event.

## 3. Interventional identification

Let `R_h(k,s)` be the mean observed increment after a probe replacing `a_t` by `s e_k`, `s in {+1,-1}`. Because sign is randomised independently of the state and `u`, the two sign groups have the same distribution of `(z_t,u_t)` and of every additive disturbance. At the first reachable horizon,

\[
R_{\tau+1}(k,+)-R_{\tau+1}(k,-)
=2M_bBe_k,
\]

where `M_b` is the observation assignment/gain map for the body block. Hence

\[
Be_k=\frac12 M_b^+\{R_{\tau+1}(k,+)-R_{\tau+1}(k,-)\}
\]

on observed body directions (or the contrast itself identifies the observed column when `M_b` is not inverted). `G_b u_t`, `W_u u_t`, the AR persistence, body noise, and observation noise cancel in expectation. Later horizons identify the corresponding closed-loop total response; the first-hit contrast is the clean column-`k` object.

Consequences:

- E1: the column contrast goes from `2M_bBe_k` to zero. The action-reachable body effects and their downstream propagation disappear according to C2/C3.
- E2: the first-hit contrast is unchanged because `B` is unchanged. A `G_b` or `W_u` change alters observational associations but cancels between randomised signs.
- E3: the contrast becomes `2 gamma M_bBe_k`. It detects the effectiveness reduction, while C3's support label remains unchanged by the stipulated `gamma>=gamma_min` recertification.

Draft 5's rank-sum maximum is a monotone, noisy proxy for this mean contrast, not the contrast itself. Its randomisation gives causal validity; the maximum, ranks, cadence, overlapping windows, and small sign groups determine power.

## 4. Option C endpoints and population predictions

Use one paired generator regime for both endpoints:

1. **Attribution:** full-channel AUC/AUPRC against post-event `S^{obs,epsilon}`. Confounded `x` channels are hard negatives. `G_x` is present in both cells. The treatment is only `G_b`: present means `G_b != 0`, absent means `G_b=0`; `W_u`, `G_x`, all structural action paths, and common random-number keys are held fixed.
2. **Adaptation:** after E1, rank only channels in pre-event `S^{obs,epsilon}`, positives retained and negatives lost, exactly as current C3/G. Use the same `G_b` present/absent pair as attribution.

Population predictions should be separated from hoped-for finite-sample rankings. The following table defines `-` as a fall in a channel's support evidence, `0` as invariance, `+` as retained positive causal evidence, and `?` as not sign-identified by the stated assumptions. For E3, `weaker +` means reduced effect magnitude but unchanged binary support.

| Arm | Event | `G_b=0`, `G_x` present | `G_b!=0`, `G_x` present | Endpoint implication |
|---|---|---:|---:|---|
| Sign-randomised | E1 complete loss | lost column: `0` (change `-`); other causal columns `+` | same | Attribution/adaptation target is causally identified |
| Sign-randomised | E2 `G_b`/`W_u` change | `0` | `0` | No support change and no first-hit contrast change |
| Sign-randomised | E3 partial loss | weaker `+`; binary label `0` change | same | Effect change detected; support correctly retained |
| Frozen passive `-Delta` | E1 | `-` generically | `-` generically, magnitude `?` | Can rank the constructed lost body channel, but no causal event attribution |
| Frozen passive `-Delta` | E2 | `0` if only inactive `G_b` is unchanged; otherwise `-` when `W_u` changes its projection | `-` generically | False support-loss evidence under a support-preserving event |
| Frozen passive `-Delta` | E3 | `-` generically | `-` generically | Treats effectiveness change as loss evidence although C3 label is retained |

For the named endpoint comparisons, the preregisterable directional predictions are narrower:

- Attribution: the sign-randomised arm should be invariant to the `G_b` cell and should reject confounded `x`; the passive full-channel loading should be worse with confounding than without because `G_x` makes `a` a proxy for `x`. The incremental effect of `G_b` on passive full-channel AUC is **not sign-determined**: it can raise scores on true-positive body channels while `G_x` raises hard negatives.
- Adaptation after E1: sign-randomised evidence for the lost column goes to its null level in both cells. Passive `Delta` changes in both cells. Which arm has higher pre-support AUC when `G_b!=0` is **not sign-determined** without inequalities on `G_b`, `B`, noise, and alternative paths. Consequently a confirmatory claim of a positive interventional premium in the present cell cannot yet be assigned a population `+`.

That `?` is a derivation result, not an invitation to replace it after execution. A freeze should either add scale conditions that imply a sign or define the round as an exploratory falsification of a quantitative prediction fitted elsewhere.

## 5. Finite-sample scale

With probe fraction `p`, window `W`, and `K` actuators, there are approximately `pW` probes and `pW/(2K)` observations in each `(k,sign)` group. For a direct mean contrast with per-unit increment standard deviation `sigma_D`,

\[
\operatorname{se}(\bar D_+-\bar D_-)
\approx \sigma_D\sqrt{\frac{1}{n_+}+\frac{1}{n_-}}
=\sigma_D\sqrt{\frac{4K}{pW}}.
\]

At `p=0.05`, `W=500`, `K=2`, there are 25 total units and about 6.25 per sign for a given actuator, giving

\[
\operatorname{se}\approx0.566\,\sigma_D.
\]

The first-hit population contrast is `2|M_b B e_k|`, so

\[
\frac{\operatorname{se}}{|\text{effect}|}
\approx0.283\frac{\sigma_D}{|M_bBe_k|}.
\]

Serial dependence and draft 5's balanced-block carry-over inflate the effective `sigma_D`; ranks and the max over six cells further reduce power. A basic design condition for the population advantage not to be variance-swamped is therefore `|M_bBe_k|` comfortably larger than `0.283 sigma_D` (and preferably several times that threshold), not merely above the contract's operational epsilon.

In the scalar residualised model the passive omitted-variable coefficient is

\[
bias_{pass}=g\frac{wq_u}{w^2q_u+\sigma_\eta^2}.
\]

It exceeds the intervention's one-standard-error uncertainty in column units when

\[
\left|g\frac{wq_u}{w^2q_u+\sigma_\eta^2}\right|
>\frac12\sigma_D\sqrt{\frac{4K}{pW}}
=0.283\sigma_D.
\]

Equivalently, relative to the causal column,

\[
\frac{|bias_{pass}|}{|B|}>
0.283\frac{\sigma_D}{|B|}.
\]

The multivariate replacement is the norm of `G_b Sigma_u W_u^T` after residual-action covariance normalisation and projection onto the tested channel/actuator direction. This is the scale regime option C should certify. Merely requiring `G_b != 0` does not guarantee that the passive bias exceeds even one interventional standard error.

## 6. Minimal generator/contract change

The minimal normative redline for family L is:

### Section A (variables)

- Change `u_t` role from “parent of x” to “parent of x and, in the confounder-present L-C cell, b.” Its action-ancestor entry remains “no.”
- The roles and action-ancestor entries of `b,d,w,x` do not change. In particular, a common cause into `b` is not an action edge.

### Section B (structural equations and stability)

- Replace the family-L body line by

  `b_{t+1} = A_b b_t + B_t a_{t-tau} + G_b u_t + epsilon^b_t`.

- Retain the `x` line but rename its coupling `G_x`:

  `x_{t+1} = A_x x_t + G_x u_t + epsilon^x_t`.

- Change the stability state to include `u_t` in the delay-augmented closed loop and construct the actual augmented `F` above. Certify `rho(F)<=rho_cl` after sampling and after every event. Because `u` is exogenous, the matrix is block triangular under a correct ordering and its eigenvalues are the old closed-loop eigenvalues plus `rho_u`; nevertheless the current certificate does not construct this model and must not silently reuse the old matrix.

- Replace “`rho_min` certified after `W_o,W_u` are sampled” by two named witnesses after `G_b,G_x,W_o,W_u` are sampled: an `x` witness and a `b` witness. The body witness must be based on an observational association conditional on the declared observed regressors, or explicitly named as a marginal correlation; the two are not interchangeable.

### Section A0 (sampling and certification)

- Replace “`G` on the confounded half of `x`” by: `G_x` is sampled exactly as the current `G`; independently sample `G_b` on a declared nonempty set of body rows with Rademacher signs and magnitudes bounded below by `c_min`, using a frozen `G_b_scale` (and perturbation multiplier) declared in section 0. Reject draws with an all-zero active action/body cross-product `G_b Sigma_u W_u^T`.
- Present/absent pairing sets only `G_b=0`; it keeps `G_x`, `W_u`, the plant, and noise keys fixed. This differs from current F7, which removes `G` from `x`; the new regime must be named separately to avoid changing two treatments under one label.
- Certify both `rho_min` witnesses: `max_{k,j in confounded x}|corr(a_k,x_j)|>=rho_min` and `max_{k,j in confounded b}|corr(a_k,b_j)|>=rho_min` (or their explicitly conditional versions). Report the witness pairs and values. Under randomised `do(a)`, require both maxima to fall below the multiplicity-adjusted tolerance.
- Re-run operational margins, E1b, E1/E2/E3 post-event label certification, and resampling-rate checks under both `G_b` cells.

### What breaks today

- **Closed-loop radius:** the current augmented state omits `u` and the `G_b` block. The numerical radius may happen to equal `max(old radius,|rho_u|)`, but the implemented certificate is for the wrong transition matrix.
- **CL-4:** its graph statement can survive—`G_b` is not an alternative action path—but its motivating observational construction does not. After E1 the isolated body coordinate need not go quiet; it remains driven by `G_b u`. CL-4 must certify loss by interventional C2/C3 only and should no longer imply ease for a second-moment detector. The target body row should not be chosen by outcome-dependent `G_b` strength.
- **E1b label consistency:** the action-reachability graph and zero-noise intervention must include the new parent but must not count it as an action path. If the finite-difference branch uses common `u` (or fixes the same `u` path) in probe and zero branches, `G_b u` cancels and E1b should still pass. If it redraws or zeros `u` asymmetrically, it will confuse association with reachability. Add a mutant that treats `u -> b` as `a -> b`, and one that uses unmatched `u` paths.
- **E1 label consistency:** after complete loss, a body channel can remain observationally variable and action-correlated while being outside `S`; tests that infer a label from variance/correlation now fail conceptually.
- **E3 label consistency:** partial loss changes the contrast magnitude but, by contract, not the label. Re-certification must check `gamma e_j>epsilon` with `G_b` cancelled under paired interventions; observational covariance is not a valid substitute.

Best-practice enhancement directly relevant to the freeze: add an explicit lower bound on the independent action-innovation covariance in every actuator direction. Without it, the generator can drift toward the knife-edge where passive identification becomes ill-conditioned, and the intended comparison silently changes from finite-sample robustness to structural impossibility.

## One-round decision

**Opinion — verdict: do not freeze option C for a confirmatory execution round yet.** It is worth a small design/power pilot or a further analytic specification pass, but this derivation does not establish the promised open-set passive-identifiability gap under the current positive action-noise contract.

- Strongest reason **for** one round: E2 gives a sharp mechanism control. Randomised first-hit contrasts are invariant while the frozen passive residual score generically fires on a support-preserving confounder change. That would cleanly demonstrate causal robustness even though an optimal passive estimator remains possible.
- Strongest reason **against**: the headline premise is false as stated, and the frozen 500-step window has only about six observations per actuator/sign group. A win could be a comparator-misspecification result; a loss could simply be probe variance. Neither resolves passive identifiability in principle.

Evidence that would change this verdict:

1. An exact E1/E2 observational-equivalence construction satisfying `sigma_a=0.1`, independent noises, `rho_u=0.8`, the observation equation, and equality of all pre/post lag covariances on a neighbourhood, not just equality of the frozen monitor's score; or
2. a preregistered scale certificate showing, for every confirmatory draw, that the projected passive bias exceeds (say) two probe-contrast standard errors while the direct probe effect has a fixed signal-to-noise margin, followed by a topology-balanced E1 design; and
3. a population prediction for the arm-level adaptation AUC whose sign follows from those constraints rather than being selected after execution.

## Disputes with round 7

I agree with round 7's “derive, then choose” procedure and with its withdrawal of the cross-regime dissociation.

I dispute two implications:

1. **Opinion:** “body-reaching confounding” is not by itself the unoccupied scientific condition. The relevant condition is body-reaching confounding **plus insufficient independent natural action excitation, or a deliberately restricted passive estimator**. Round 7 does not state this distinction, and it matters because contract v3.9 fixes nonzero independent action noise.
2. **Opinion:** the derivation is not a mere one-page switch test if the information set is the complete noisy closed-loop observational law. Equality of a residual-covariance score is much weaker than equality of that law. The next adjudication should reject any argument that proves only that comparator v3 confuses E1 and E2 and then labels the plant non-identifiable.

