# Round 7 verdict: does either finding survive, and is it worth a paper?

Reviewer: fresh-context Claude Opus (`claude-opus`). Date: 8 September 2026. Reasoning only; no code, no simulation, no existing file edited.

## 0. Sources I actually checked

Web search and web fetch were available to me.

**Read in full.** Liu, Cheng & Bogdan, "Discovering What You Can Control: Interventional Boundary Discovery for Reinforcement Learning", arXiv:2603.18257v2 [cs.LG], 7 May 2026. I fetched the v2 PDF and extracted the text with `pdftotext`, and read the abstract, introduction, related work, Method (3.1 to 3.5 including Algorithm 1 and Propositions 3.2 to 3.5), Experiments (4.1 to 4.8 including Tables 1 to 4), the Discussion, and the reference list. Two earlier attempts to read it through a summarising fetch returned partly wrong content (one invented DrQ-v2/CURL/SVEA as *baselines* when they are cited only as related work, and asserted a "batch offline policy evaluation" setting that the paper does not describe in those words). Everything I attribute to this paper below comes from the extracted text, not from those summaries.

**Read in the repository.** `round6-adjudication-and-tally.md`, `round5-adjudication-and-tally.md`, `decisions-required.md`, `roadmap-v4.md` with amendments v4.1 to v4.7, `research-round-2.md`, `evidence.md`, `findings.md` (F2 in full, F1 and F3 for the re-scoring precedent). I did not open any `review*/` folder or any simulation code.

**Checked at abstract or summariser level only, and flagged as such wherever I use them.** Xu & Zhang, "Quickest Causal Change Point Detection by Adaptive Intervention", arXiv:2506.07760 (abstract page via summariser; I did not read the body). Campbell & Nikoukhah, *Auxiliary Signal Design for Failure Detection*, Princeton Series in Applied Mathematics 11 (search-result and publisher descriptions only; **I did not read this book**). The active-FDI framing sentence I quote in §1(b) below came to me through a summariser reading an International Journal of Systems Science AFDI paper (DOI 10.1080/00207721.2013.843213), not from my own reading of the page; I treat it as a characterisation of a standard position in that field, corroborated across several independent search results, rather than as a verified quotation from a specific author. "CausalDynamics" (NeurIPS 2025 Datasets and Benchmarks) I know only from a search snippet.

**Could not access / did not attempt.** I did not check ICML 2026 or NeurIPS 2026 proceedings directly, only via search. My searches were six queries deep; a scoop published in the last few months in a venue that indexes slowly would not have surfaced.

**Scoring anchors.** `findings.md` line 106 records, correctly, that the roadmap's 1-to-5 scale has no anchor descriptions. So that my numbers mean something, I use the anchors the original red team used implicitly when it re-scored R5 to "about 2" as "an incremental extension of Jensen et al., not a new question" and R1 to "about 3":

- **1** — already published, or an immediate corollary of a published theorem.
- **2** — an engineering variant of a published result: same question, same answer, new setting or metric.
- **3** — a question not posed in this form before, whose answer is predictable from existing theory.
- **4** — a question not posed before whose answer is not predictable, on a setting others will care about.
- **5** — a new question that changes what other people measure.

Everything in §§1 to 5 below that is a judgement rather than a fact is marked **[opinion]**.

---

## 1. The four candidate claims

### What the IBD paper actually contains (this governs all four)

Facts, from the extracted text:

- **It is one-shot and offline.** From the same reset distribution IBD collects N baseline and N intervention trajectories; the intervention branch replaces the action mechanism entirely with `a ~ Unif(A)`. Defaults N = 80, T = 200, "approximately 32K environment steps"; §3.2 states the mask is "computed once at a cost of 2NT environment steps and reused throughout downstream training", and §3.5 repeats that it "is a one-time cost".
- **Sign randomisation is pre-authorised, not excluded.** §3.2: "Uniform is maximum-entropy on A and maximally excites action-reachable dimensions, **but any confounder-independent distribution is valid**." A sign-randomised probe is a confounder-independent distribution. IBD's identification argument covers it as written.
- **The shared-cause confounder is the paper's central object.** Proposition 3.2's construction is a linear-Gaussian SCM with a latent `C_t` driving both the behaviour action and the distractor — structurally the same object as the programme's plant. Proposition 3.3 (Invariance to confounders) states that the estimated SoI "converges to the same set whether confounders are active or removed (up to sampling noise in finite samples)".
- **The attribution result is measured, and much larger than +0.2 AUC.** Table 3: on `reacher_hard` medium, multistep inverse dynamics reaches boundary F1 0.67 against IBD's 0.98, and the leakage of two confounded distractors drops downstream return from 929 to 28. On `finger_spin` medium, inverse dynamics F1 0.44 against IBD 0.98. Table 2: gradient attribution F1 "only 0.44-0.50". Table 1: Cond. MI, a state-conditioned forward model, collapses to near-random return in every medium and hard cell.
- **Non-stationarity is explicitly out of scope.** Assumption (iii) is "stationary causal structure during probing". The Discussion: "Our setting assumes stationary probing with appended exogenous distractors; indirect action effects, policy-dependent distractors, partial controllability, and different capacity-budget regimes remain future directions."
- **Its distractors never touch the controllable dynamics.** §4.1: appended distractors "do not alter the transition, reward, or action dynamics, so the state-only observation is a valid oracle reference." Assumption (i) is decomposability: dimensions are either fully causal or fully exogenous (relaxed in §4.7 only to a mixing coefficient on *added* dimensions, `x_{t+1} = a g(s,a) + (1-a) z_t`, i.e. partial controllability, not confounded controllability).
- **Metric and baselines.** Binary mask precision/recall/F1 plus downstream SAC/TD3 return. Baselines: MI Select, Variance Select, Cond. MI, gradient attribution, multistep inverse dynamics. **No residual-monitor or CUSUM-class comparator anywhere.** No ranking metric, no AUC, no alarm, no detection latency, no false-alarm rate.

---

### (a) Attribution only, online and sequential, with a 5 percent probe budget

**Closest prior work.** Liu, Cheng & Bogdan, arXiv:2603.18257v2, §3.2 (any confounder-independent distribution is valid), Prop. 3.3 (invariance to confounders), Tables 2 and 3 (passive model-based selectors leak confounded distractors; IBD does not). Secondarily, for the online/budgeted half: the classical dither-injection and persistent-excitation trade-off in closed-loop system identification, and active fault detection by auxiliary signal design (Campbell & Nikoukhah; *not read by me*, see §0), whose entire subject is how much excitation to spend for how much identifiability while a controller is running.

**What is exactly new against it.** Four things, all real and all mechanical rather than scientific: (i) the interventional contrast is interleaved into a continuing episode at a declared 5 percent probe fraction, whereas IBD requires an independent rollout branch from a controlled reset distribution with the action mechanism fully replaced — a resource the online setting does not have; (ii) sign-randomisation as a paired, balanced-block perturbation on the *acting* policy, which preserves closed-loop operation, rather than mechanism replacement by `Unif(A)`, which does not; (iii) a graded ranking endpoint (AUC over channels) instead of a binary FDR-controlled mask; (iv) the comparator class is a residual/CUSUM monitor from the fault-detection tradition, which IBD never tested.

**What is not new.** The claim itself. "A passive selector falsely attributes controllability to a distractor sharing a latent cause with the action; an interventional contrast does not" is Proposition 3.3 with Tables 2 and 3 as its evidence. The programme's +0.16 to +0.24 AUC is a weaker instance of an effect IBD reports as F1 0.44 to 0.98. And the paper's own sentence pre-authorises the estimator variant that carries the programme's superiority claim. **[opinion]** A referee who has read §3.2 will say the online, budgeted, ranked variant is a deployment engineering question about a settled scientific one — and will be right.

**Novelty: 2.** An engineering variant of a published and proved result; the new parts are the setting and the metric, not the answer.

---

### (b) The negative adaptation result on its own

**Closest prior work.** The active-versus-passive dichotomy in fault detection and isolation. The standard framing in that field, which recurred across several of my search results and which a summariser reported verbatim from an IJSS AFDI paper (see §0 for my access caveat), is that active FDI exists for faults that "remain undetected if they do not sufficiently excite the system or if they are masked by the controller's regulatory action". Campbell & Nikoukhah's separability index formalises the same boundary: an auxiliary signal is *required* exactly when the candidate models are not separable under the operating input, and is unnecessary when they are.

**What is exactly new against it.** As a mechanism, essentially nothing. Round 6 finding 2's own explanation — "detecting that a controlled channel went quiet is easy for a frozen residual monitor with an action-residual covariance score" — is the statement that the fault is *separable under the operating input*, which is the textbook condition under which active probing buys nothing. The programme has instantiated the easy side of a boundary the control field characterised decades ago, in a new plant, with a new estimator.

There is a second, independent problem, and it comes from the adjudication itself. Finding 5 records that loss of actuator 1 removes no observed channel on any seed, and that at tau = 2 the pre-event support is exactly four channels on every draw. Finding 4 records that the below-chance static control and the comparator's ease are both consequences of CL-4 making the lost channel the dominant body component of actuator 0. So the negative result rests on one hand-wired coordinate, on a four-channel support, with an event whose construction the adjudication has already shown to determine two of the numbers being reported. **[opinion]** A negative result whose scope is limited by an artefact the authors have themselves documented is not a contribution; it is a note in a benchmark's limitations section.

**Novelty: 1.** An instance of a published boundary condition, on a construction whose own designers have shown determines the answer.

---

### (c) Combined benchmark-and-findings paper: "interventions buy attribution, not adaptation"

**Closest prior work.** IBD for the attribution half (as in (a)); the AFDI separability literature for the adaptation half (as in (b)). For the *form* — a benchmark paper for causal structure in dynamical systems — the nearest comparator I could identify is CausalDynamics (NeurIPS 2025 Datasets and Benchmarks track), which I know only from a search snippet and cannot characterise further.

**What is exactly new against it.** The *conjunction*, posed as a designed dissociation: one plant, one estimator family, one event, two named endpoints, and an explicit statement of where the interventional premium exists and where it vanishes. The RL causal-discovery literature has IBD's attribution result and no adaptation endpoint at all; the control literature has the separability boundary and does not express it as an observation-selection benchmark for learning agents. Nobody has put the two halves on the same axis. **[opinion]** That synthesis is genuinely worth something — it is the one thing in this programme I would want to read.

**What blocks it in the current evidence, and it is fatal as posed.** Round 6 finding 1 establishes that on the D-11.1a primary the present and absent streams are *bitwise identical* on every channel the primary scores. So the adaptation endpoint cannot see confounding at all. The attribution row is measured on the full channel set with the confounder active; the adaptation row is measured on the pre-event support with the confounder provably inert. The two rows therefore differ in **both** the endpoint and the confounding regime. What the evidence licenses is the much narrower "interventions buy attribution under a shared-cause confounder, and on a separate, unconfounded event that is passively observable they buy nothing" — and the second clause, so stated, is Prop. 3.3's contrapositive plus a textbook FDI fact. The headline "interventions buy attribution, not adaptation" is not supported by these two rows. See §5, dispute 2; this is the most consequential thing I have to say.

**Novelty: 2.5 as the evidence currently stands** (3 if and only if both endpoints are measured under a common confounding regime, which is precisely what option C would provide). Justification: a real and unoccupied synthesis, currently demonstrated by a comparison that changes two variables at once.

---

### (d) D-12 option C: a plant where the confounder reaches controllable channels

**Closest prior work.** I could not find a paper that does this, and I looked. IBD excludes it twice over — Assumption (i) decomposability (dimensions fully causal or fully exogenous), and §4.1's design constraint that distractors "do not alter the transition, reward, or action dynamics". Its Discussion names "policy-dependent distractors" and "indirect action effects" as open. §4.7's partial controllability mixes an exogenous OU process into an *added* dimension; it does not put the policy's own latent cause onto a channel the actuator also reaches. The nearest method-level neighbour is Xu & Zhang, arXiv:2506.07760, "Quickest Causal Change Point Detection by Adaptive Intervention" (abstract only; see §0) — sequential, adaptive-intervention, linear causal models, quickest-detection framing, with intervention-node selection by KL divergence. That is close enough that it must be cited and treated as a baseline, but its object is a change in a causal model's edge structure, not an agent's own action-reachable observation support, and it is not an RL benchmark with distractors.

**What is exactly new.** A channel that is simultaneously action-reachable and driven by the latent cause that drives the policy. Under an actuator loss on such a channel the passive residual monitor's evidence is ambiguous *by construction*: a change in the action-residual second moment is producible by either the lost actuator or a shift on the confounder path, and the passive monitor cannot separate them, while the sign-randomised contrast can. This is the first configuration in which attribution and adaptation are the *same* question rather than two questions measured under different confounding — which is exactly the defect that sinks (c). It is also the case that restores a live superiority claim, because it is the case where the fault is masked by the operating regime, which is the condition the AFDI literature identifies as the one where active probing is *required*.

**Novelty: 3.5.** The only one of the four whose scientific question I could not find answered anywhere; but the answer is derivable from existing identifiability theory before any code is written, which caps it below 4.

**The risk, stated plainly. [opinion]** This programme has now twice built a design whose answer was determined by its construction rather than by the phenomenon: round 5's event that usually changed nothing, and round 6's primary that was bitwise identical across conditions. Option C has the same failure mode waiting in the mirror image — if the confounder path is strong enough to mask an actuator loss from a passive monitor, the interventional arm may win *by construction*, and the programme will have spent a seventh round proving its own plant. The correct order of work is therefore: derive the population-limit statistic for both arms on the proposed topology **on paper, before building**, and check that the answer is not knife-edge in the coupling parameter. That derivation is free, needs no freeze, and is the same class of check that round 6 finding 1 says would have caught the last error.

---

## 2. Venue fit, and whether a referee accepts the negative finding

**Venue fit. [opinion throughout this section]**

| Candidate | Best realistic home | Why |
|---|---|---|
| (a) attribution online | Nowhere as a superiority claim. As a systems/deployment note, an ICLR or CoLLAs workshop. | The claim is IBD's. A main-track referee who reads §3.2 rejects on novelty. |
| (b) negative alone | Nothing, including ICBINB. | Wrong on two independent grounds: known boundary condition, and construction artefact. |
| (c) benchmark + findings | TMLR, or an ICLR 2027 workshop (deadlines ~Feb 2027 per `research-round-2.md` §F). | TMLR judges correctness and interest to some audience rather than novelty and significance, which is the right filter for a careful negative-plus-modest-positive paper. **I could not verify TMLR's current policy text in this session; this is from recollection.** A NeurIPS/ICLR Datasets and Benchmarks submission would be over-reaching — see the external-validity point below. |
| (d) option C | ICLR/NeurIPS main track or D&B if it works; CoLLAs 2027 is the natural community. | It has a live question and a genuine comparator in IBD. |

**Would a referee accept the negative finding as a contribution?**

For (b) standing alone: **no.** [opinion] Two rejections are available and a competent referee will find at least one. A control-literate referee: the result is the separable case of a boundary the AFDI literature characterises, and the submission does not cite that literature — `round6-adjudication-and-tally.md` contains no control-theory citation anywhere, and neither does `research-round-2.md` §B. A benchmark-literate referee: the paper's own findings 4, 5 and 6 say the event construction produced two of the reported numbers, that one hand-wired actuator is tested, and that at tau = 2 the support is four channels.

For (c): **conditionally yes**, at TMLR or a workshop, and only if the dissociation is measured under a common confounding regime. A negative result is publishable when it bounds a positive result that the same paper establishes. Here the positive half is IBD's, so the paper's actual standing is "we bound someone else's result" — which is a legitimate and respectable contribution, but it must be *framed* that way, not as "interventions buy attribution".

**A referee risk the adjudication does not name.** Three independent implementations agreeing to three decimals on one frozen generator is evidence that the *specification* is unambiguous. It is not evidence of external validity. Every number in rounds 5 and 6 comes from one synthetic linear-Gaussian family (L, with N partly built), one hand-wired actuator loss, and a pre-event support of four channels at tau = 2. A D&B referee will ask why the benchmark does not include at least one of the DeepMind Control Suite settings IBD used — `reacher_hard` medium is the sharpest cell in Table 3 — so that the two papers are comparable. Answering that is a large amount of work that is not in `roadmap-v4.md` §3 and does not fit the Feb 2027 target. [opinion]

---

## 3. Recommendation among D-12 A, B, C

### Recommendation: A — stop building, and write the modest paper that the evidence actually supports.

This follows the author's own stated conditional in `decisions-required.md` ("B if the online attribution claim clears the novelty check against IBD; otherwise A"). My novelty check says it does not clear: the claim is Proposition 3.3, and §3.2 pre-authorises the estimator variant.

But A must be scoped down from what D-12 currently describes. The deliverable should **not** be "the benchmark, with the passive-wins result as the negative headline". It should be a short paper whose claim is the one thing rounds 5 and 6 jointly support:

> **The interventional premium is a property of the confounding, not of the intervention.** On a plant where a shared latent cause drives both the policy and a set of distractors, a sign-randomised interventional contrast recovers action-reachable support that a passive residual monitor does not (reproducing, on a new plant and against a comparator class IBD did not test, the confounder-invariance of Liu et al. Prop. 3.3). On a change event that is passively observable in the closed-loop action-residual second moment, the same probing buys nothing over a delay-aware passive monitor — the classical separability condition of active fault detection, instantiated for a learning agent.

That is true, defensible, correctly attributed, and worth a TMLR note or a workshop paper. It is not worth a flagship, and no further building makes it one.

**Single strongest reason for A:** the only positive result the programme holds is Proposition 3.3 and Table 3 of Liu, Cheng & Bogdan (2026), and no seventh, eighth or ninth round of building changes that — so every further round spends the programme's genuinely scarce resource (one person's calendar against a ~Feb 2027 workshop window, on a thermally throttled laptop) accumulating evidence that cannot become a superiority claim.

**Single strongest reason against A:** A ships as its headline the candidate I scored lowest — the negative finding is both an instance of a boundary condition the active-fault-detection field settled decades ago and, by the adjudication's own findings 4 to 6, contaminated by the benchmark's event construction — so option A's deliverable, as D-12 currently words it, is the one thing here a referee has two independent grounds to reject.

**On B and C, briefly.** B is dominated: it re-freezes for a seventh round around an attribution endpoint whose superiority claim is a reproduction, so it pays a full build cycle for a novelty score of 2. C is the only branch with a live question and the only score above 3 — but it invalidates the certification design, and it carries the same "answer determined by construction" failure mode that has now cost two rounds. **If Daniel's objective is the research programme rather than the publication**, the right move is neither A-as-written nor C-as-written, but: do C's *derivation* now, on paper, at zero build cost, and let the result decide. If the derivation shows the passive monitor is genuinely non-identifiable on the confounded-controllable topology across a non-knife-edge range of the coupling parameter, take C and I would revise my recommendation. If it does not, take A and write the short paper. That derivation is a one-page piece of algebra on a linear-Gaussian plant and it is the cheapest decision-relevant thing available. [opinion]

---

## 4. Evidence that would change my verdict

Ordered by how much it would move me.

1. **A population-limit derivation for option C's topology** showing the passive action-residual covariance statistic is not identifiable between "actuator lost" and "confounder path shifted", while the sign-randomised contrast is, and that this holds across a range of the coupling parameter rather than at a knife edge. This flips (d) to 4 and my recommendation to C. A derivation, not a simulation — the last two rounds show that on this plant a simulation confirms whatever the construction encoded.
2. **Evidence that the online, budgeted constraint changes IBD's conclusion rather than its constant.** The programme has never run IBD-as-published on its own plant; it has only run a re-derived sequential arm. If a 5 percent interleaved probe with the policy retained in the loop attains materially *different* attribution accuracy from the 32K-step reset-based branch — not merely lower, but qualitatively different, e.g. a regime where the online arm fails and the offline one does not — then (a) becomes a real finding about the deployability of interventional discovery and moves from 2 to 3.
3. **Replication of the attribution finding on at least one environment IBD used**, showing that the residual/CUSUM comparator class — which IBD did not test and which is the strongest passive reading in the fault-detection tradition — also leaks confounded distractors there. That converts the comparator from an incidental design choice into the paper's contribution and moves (c) to 3.
4. **Removal of the CL-4 construction artefact.** If, with the lost channel balanced over its pre-event rank (D-12's own sub-decision), the passive monitor still equals or beats the interventional arm, the negative finding becomes a finding rather than a construction: (b) moves from 1 to 2, (c) from 2.5 to 3.
5. **A paper I missed.** My search was six queries deep and I did not read ICML 2026 or NeurIPS 2026 proceedings directly. Anything doing online maintenance of a controllability mask under a changing boundary would eliminate (a) entirely and damage (d). Conversely, if a thorough proceedings sweep confirms nothing exists, (d)'s 3.5 is firmer.
6. **A negative on Xu & Zhang.** I read only the abstract of arXiv:2506.07760. If its body turns out to cover the agent's own action-reachable support rather than edge weights in a monitored causal model, (d) drops to about 2.5 and there is no branch above 3.

---

## 5. What I dispute in `round6-adjudication-and-tally.md`

**Dispute 1 — §3 bullet 1 states a reproduction as a programme finding.** "Interventions buy attribution" is written as an output of rounds 5 and 6. It is a reproduction of Liu et al. Proposition 3.3 and §4.5, on a new plant and against a comparator class that paper did not test. The document nowhere says so; `research-round-2.md` §B and `findings.md` F2 both knew this in September and F2 explicitly instructed "Drop 'intervention beats correlation' as the headline; it is now a known result." Meanwhile `decisions-required.md` D-12 still treats the novelty of the attribution claim as an *open* question while §3 already writes it as established. **The bullet should read:** "reproduces, on a new plant and against a comparator class IBD did not test, the confounder-invariance property proved in Liu et al. Prop. 3.3." That framing gap is the mechanism by which a programme talks itself into a seventh round.

**Dispute 2 — §3's two bullets do not constitute a dissociation, and the headline they license is weaker than the one stated.** This is the most consequential item, because option A's entire deliverable is the sentence "interventions buy attribution, not adaptation". Bullet 1 is measured on the full channel set with the confounder active. Bullet 2 is measured on the pre-event support, where §2 finding 1 establishes that the present and absent streams are bitwise identical. The two rows differ in the endpoint **and** in the confounding regime, so a difference between them cannot be attributed to the endpoint. What the evidence supports is: "interventions buy attribution under a shared-cause confounder; on a separate, unconfounded event that is passively observable they buy nothing." The strong form appears in §3, again in §7, and again in D-12 option A's wording, and it should be corrected in all three.

**Dispute 3 — §1's table reports a determination where §2 finding 3 says none is available.** Finding 3 correctly holds that "a verdict that depends on the estimator is a defect of the contract" and records that the three reviewers' bounds disagree because the interval estimator was never specified. The §1 exit-condition line nonetheless reports the comparator floor as "**fails at tau = 0**". If the estimator is unspecified, the honest entry is *undetermined*, and the failure is the contract's. Minor, but it is the same class of error the document is otherwise very good at catching, sitting in the document's most-read paragraph.

**Dispute 4 — the framing of §2 finding 2, not its verdict.** The parenthetical "Not a tuning matter: detecting that a controlled channel went quiet is easy for a frozen residual monitor with an action-residual covariance score" is correct, and is presented as something the programme discovered. It is the standard passive-FDI detectability condition: active input design is required precisely when a fault is masked by insufficient excitation or by the controller's regulatory action, and is unnecessary otherwise. Neither this adjudication nor `research-round-2.md` §B nor `evidence.md` §2b cites the fault-detection literature at all — the prior-art tables reach for robot self-recognition, empowerment and causal representation learning, and never reach for the field that owns actuator-fault detection. **[opinion]** This is why option A looks more attractive inside the document than it is: the document is scoring the negative finding against the RL literature, where it is surprising, rather than against the control literature, where it is expected.

**Dispute 5 — "reproducible" is doing more work than the evidence supports.** §3's heading, §7's "Two findings are now reproducible", and §1's "Three implementations agree to three decimals" all describe three independent implementations *of the same specification* on *the same frozen generator*. That establishes the specification is unambiguous and the arithmetic is right — a genuine and unusual achievement, and the strongest thing about this process. It establishes nothing about whether either finding survives a different plant, and §2 finding 5 gives concrete reason to doubt it does (one hand-wired actuator; a four-channel pre-event support at tau = 2; the delay cells scoring a different estimand). Readers of §3 and §7 will take the stronger sense. The document should distinguish implementation agreement from external validity explicitly, because the D-12 decision turns on the difference.

**Not disputed.** §5's handling of Gemini GM6-06, Codex R6-CX-09 and the Claude mutants: I have no basis to reopen any of them. §2 finding 1's core conclusion — that the D-11.1a primary cannot see the confounder by construction, and that a channel-set check would have caught it — is correct, is the single most valuable finding in the document, and the author's willingness to record "the author's recommendation was wrong" in the adjudication is the reason this process is producing usable answers at all.

---

## Summary table

| Candidate | Closest prior work | Novelty | One-line justification |
|---|---|---|---|
| (a) attribution, online, sequential, 5% probe | Liu, Cheng & Bogdan arXiv:2603.18257v2 §3.2, Prop. 3.3, Tables 2-3; classical dither/persistent-excitation trade-off | **2** | Same question, same answer, new setting and metric; §3.2 pre-authorises the sign-randomised variant. |
| (b) negative adaptation result alone | Active-vs-passive FDI: active probing needed only when the fault is masked by low excitation or the controller's regulatory action (Campbell & Nikoukhah lineage; *not read by me*) | **1** | An instance of a settled boundary condition, on a construction the adjudication itself shows determines the answer. |
| (c) combined benchmark-and-findings | (a) + (b) together; CausalDynamics (NeurIPS 2025 D&B) for the form | **2.5** | Genuinely unoccupied synthesis, currently demonstrated by a comparison that changes endpoint and confounding at once. |
| (d) D-12 option C plant | Nothing found; nearest is Xu & Zhang arXiv:2506.07760 (abstract only). IBD excludes it by Assumption (i) and §4.1 and names it as future work. | **3.5** | The only live question of the four; capped below 4 because the answer is derivable from identifiability theory before any code is written. |

**Recommendation: A**, scoped to the narrow claim in §3, with C's population-limit derivation done first on paper because it is free and it is the only thing that could justify a seventh build.
