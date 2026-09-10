# Red-team review — RT-20260909-003

**FAIL** — 2 blocking problems with checked evidence.

3487 files reviewed. 2 of 2 required model families produced a usable review (anthropic, openai).
Nothing under review changed while they ran.

## Worth knowing

- 4 symlink(s) were not followed, so the reviewers did not see what they point at: docs/archive/red-team/executable-proofs/gate/.venv/bin/python, docs/archive/red-team/executable-proofs/gate/.venv/bin/python3, docs/archive/red-team/executable-proofs/gate/.venv/bin/python3.14
- 2 directories were skipped by name and never reviewed: docs/archive/red-team/.DS_Store, docs/archive/red-team/executable-proofs/.DS_Store
- antigravity did not count towards diversity — did not produce a review (error)

## Who reviewed

| Reviewer | Model that actually ran | Family | Counts | Status | Time | Kept |
| --- | --- | --- | --- | --- | --- | --- |
| claude-code | `claude-opus-5` (envelope) | anthropic | yes | ok | 563s | 8 |
| codex | `gpt-5.6-sol` (session-log) | openai | yes | ok | 248s | 6 |
| antigravity | `gemini-3.1-pro-high` (pinned-slug) | google | **no** | error — error: Individual quota reached. Please upgrade your subscri | 556s | — |

## What they found

### 1. BLOCKING — The population-limit bias formula omits the causal-delay factor and is wrong for the report’s delay-two cells

`docs/report/technical-report.md:145-157`  ·  **found by 2 families: anthropic, openai**

**codex/F-1** (P1, blocking)

`docs/report/technical-report.md:145-157`

```
u_t = ρ_u u_{t−1} + ε^u_t,  a_t = W_o o_t + W_u u_t + ε^a_t,  b_{t+1} = A_b b_t + B a_{t−τ} + G_b u_t + ε^b_t,

with u never observed and G_b the new coupling. All three derivations reached the same four conclusions.

First, exact non-identifiability is a knife-edge, not an open set. The observational law of (o, a) at all lags contains the independent action noise ε^a, which acts as an instrument: the covariance between the body and the action has a discontinuity at the causal lag τ that the smooth AR(1) confounder path cannot produce, and it pins B separately from G_b. Exact confusion between an actuator loss and a support-preserving change in G_b requires the action noise to vanish in the affected direction. The premise I had adopted was false.

Second, what fails on an open set is the model class the working claim is about: any predictor without a latent context variable. Its fitted action coefficient converges to

  β_a → B + κ G_b W_uᵀ,  κ = Var(u | b) / (σ_a² + Var(u | b) ‖W_u‖²),
```

For `τ > 0`, the confounding path from `u_{t−τ}` in the lagged action to `u_t` in the body equation carries a `ρ_u^τ` factor. The Gemini derivation explicitly gives `B_obs = B + ρ_u^τ G_b K_a`; the displayed report formula is only the contemporaneous reduction. At the report’s `ρ_u = 0.8`, the omitted multiplier is `0.64` when `τ = 2`, so the stated probability limit overstates that bias by 56.25% in those cells.

Make the display delay-specific—either label it `τ = 0`, or include `ρ_u^τ` and define the conditioning set needed for the lagged regression. Do not present a scalar contemporaneous reduction as the limit for the full model.

**claude-code/F-5** (P2)

`docs/report/technical-report.md:155`

```
  β_a → B + κ G_b W_uᵀ,  κ = Var(u | b) / (σ_a² + Var(u | b) ‖W_u‖²),
```

The derivation this comes from defines the numerator as the residual variance of the *latent context* after projecting on the predictor's own observable regressors:

`docs/archive/red-team/review8-claude-opus/derivation.md:160`

```
Let `ũ_t = u_t − proj(u_t | o_t, …)`, `v_u := Var(ũ_t)`, and `ξ̃_t = W_u ũ_t + ε^a_t`. Then
```

`docs/archive/red-team/review8-claude-opus/derivation.md:172`

```
> **`B^pass = B + κ G_b W_uᵀ`,  `κ = v_u /(σ_a² + v_u ‖W_u‖²)`, `v_u = Var(u_t | conditioning set)`.**
```

"Var(u | b)" is wrong in a way that inverts the argument. `b` is a latent block the passive predictor never observes; the whole point of the derivation is the bound at line 186 — `v_u ≥ σ_u² for every past-measurable conditioning set` — which is what makes the bias irreducible ("Lag depth does not help… A deeper predictor is still past-measurable, so κ ≥ κ*", line 195). Written as a conditional variance given the body, κ looks like something a better body model could shrink, which is the opposite of the result §5's third surviving claim rests on. A referee who tries to check the one equation in the paper will not be able to.

Fix: `κ = v_u / (σ_a² + v_u ‖W_u‖²)`, with `v_u = Var(u_t | the predictor's past-measurable regressors) ≥ σ_u²`, and one clause saying that the lower bound on `v_u` is why no depth of action lags repairs the bias.


### 2. BLOCKING — Round 5's three-model agreement is presented as evidence from one frozen generator, and the report never discloses that the frozen generator produced different trajectories in every process

`docs/report/technical-report.md:87-87`  ·  found by anthropic alone

**claude-code/F-1** (P1, blocking)

`docs/report/technical-report.md:87`

```
Three independent implementations agreed to within Monte Carlo error on every number. Table 2 gives the base cell.
```

The round-5 generator keyed its noise streams with Python's salted `str.__hash__`, so the three reviewers were not running the same instances. The adjudication lists it first among the generator defects:

`docs/archive/red-team/round5-adjudication-and-tally.md:26`

```
Cross-process non-determinism from a salted string hash in the noise key; CL-4 not certified;
```

The reviewer who found it quantified it and drew the conclusion the report needs to answer:

`docs/archive/red-team/review5-claude-opus/findings.md:61`

```
Python salts `str.__hash__` per process. Three interpreter launches give `hash('b')&0xffff` = 54097 / 37798 / 42634
```

and, in the same row, `Until then no round-5 number from any reviewer is comparable to any other.`

Concretely, this is load-bearing three ways. (1) The Summary's "ran them on the same frozen simulator" (line 16) and §6's "became unmissable once three systems ran the same frozen instances" (line 187) are false for round 5 — same code, different trajectories. (2) It is the answer to the question the report's own structure raises and never answers: why round 5 agreed only "to within Monte Carlo error" (spread 0.800/0.815/0.831) while round 6 agreed to three decimals. The difference is not sampling noise; it is that the deterministic-noise-key repair landed between the two rounds (`decisions-required.md:32`, "Applied without asking … deterministic noise key"). (3) The same reviewer showed the spread is not innocuous: the base-cell benefit moves from +0.187 [0.155, 0.218] to +0.210 [0.173, 0.246] under `PYTHONHASHSEED=0` vs `=1`, i.e. Table 2's cross-model spread is partly a seeding artefact, not a Monte-Carlo one.

Fix: add one sentence to §4.1 after the Table 2 caption — "Round 5's generator keyed its noise with a per-process salted string hash, so the three implementations ran the same specification and configuration seeds but not the same trajectories; the same reviewer's code moved the base-cell benefit from +0.187 to +0.210 across two hash seeds. The key was made deterministic before version 6, which is why round 6 agrees to three decimals and round 5 only to Monte Carlo error." Then correct line 187 to say "the same frozen generator" for round 5 and "the same frozen instances" for round 6 only.


### 3. P2 — Historical freeze hashes are presented as provenance even though the archive cannot recompute them

`docs/report/technical-report.md:43-55`  ·  **found by 2 families: anthropic, openai**

**codex/F-5** (P2)

`docs/report/technical-report.md:43-55`

```
| Round | Date | Type | Frozen version reviewed | Gate as frozen | What it did |
|---|---|---|---|---|---|
| 0 | 6 Sep | single-model prose | none | none | Red team of the original roadmap; prior-art check; found IBD |
| 1 | 6 Sep | prose | c197652c0d8e846b | gate present; count not logged | Review of the re-aimed plan (roadmap v4, contract v3) |
| 2 | 6 Sep | prose + gate | d23960e6da441de7 | 17 tests, 8 mutants | Contract v3.1, interface v2; four reviewers |
| 3 | 7 Sep | prose + implementation | e662b7429b6b347d | 23 tests, 23 mutants | Contract v3.3, IBD spec draft 2; each reviewer built its own simulation |
| 4 | 7 Sep | prose + implementation | 442cc4b7da691ca0 | 34 tests, 35 mutants | Both estimator specs; each reviewer implemented both arms on instances of its own |
| 5 | 7 Sep | execution | 0468104f6431b050 | 47 tests, 40 mutants | Three implementations on one frozen generator |
| 6 | 7 Sep | execution | 38d161e762a3de76 | 66 tests, 47 mutants | Same, on the re-posed primary; families L and N |
| 7 | 8 Sep | prose | archived record | | Novelty of what survived, against the literature |
| 8 | 9 Sep | derivation | archived record | | Identifiability under a body-reaching confounder |

Table 1. The rounds. Hashes are the first sixteen hex digits of the SHA-256 over each version's manifest in manifest order, as recorded in the archive's round log at the time of the freeze. The archive's `freeze.py` hashes the folder as it currently stands, which is version 6 plus decision entries added after round 6, so it does not reproduce earlier rows.
```

A recorded digest without the exact historical bytes is not a reproducible freeze. `freeze.py` has no version argument, the manifest-bearing decision log was subsequently modified, and the report concedes that running the verifier reproduces none of the tabled hashes. A reader cannot distinguish a valid historical freeze from a mistyped digest.

Archive immutable snapshots or commits for every row and attach the commit/tree identifier. Alternatively publish per-version manifests containing individual file hashes so each retained superseded file can be checked independently.

**claude-code/F-4** (P2)

`docs/report/technical-report.md:55`

```
Table 1. The rounds. Hashes are the first sixteen hex digits of the SHA-256 over each version's manifest in manifest order, as recorded in the archive's round log at the time of the freeze.
```

The manifest mechanism was a round-2 reviewer finding, applied as a post-round-2 repair:

`docs/archive/red-team/readiness-protocol.md:49`

```
Freeze manifest and `freeze.py` introduced (FB-19). **Candidate frozen version 3 hash: `2945e545818839ea`** (manifest order).
```

Version 3 is the first hash the round log annotates "(manifest order)", and `freeze.py` (line 1: "sha256 over the files in freeze-manifest.txt, concatenated in order") is what produces that form. `c197652c0d8e846b` (round 1) and `d23960e6da441de7` (round 2) predate both artefacts, so they cannot have been computed the way the caption says, and the report gives a reader no way to know which rows are reconstructible in principle and which are bare assertions. This compounds the caption's other, correct disclosure that `freeze.py` reproduces none of them today.

Fix: append to the caption — "The manifest and `freeze.py` were introduced as a repair after round 2 (`readiness-protocol.md`), so rows 1 and 2 record hashes taken before that convention existed and are not manifest-order digests."


### 4. P2 — The advertised one-command environment is not reproducible because the command does not provision the required Python version

`docs/report/technical-report.md:193-197`  ·  **found by 2 families: anthropic, openai**

**codex/F-4** (P2)

`docs/report/technical-report.md:193-197`

```
The archive contains the rounds in full: every prompt, every review, every adjudication, the frozen manifests and hashes, the contract through version 3.9, the interface specification through version 5, both estimator specifications with their superseded drafts, the reference generator with families L and N, the reference implementations of the metrics, the test gate (66 tests and 47 mutants at version 6, with the surviving mutants listed in the round-6 adjudication), and the three round-6 implementations of both estimators with their captured output. A file map from each table in this report to the archived input, implementation, captured output and adjudication is included with the archive. The confirmation-seed commitment is recorded; the secret was never opened. The gate runs under a Python 3.12 environment built from the pinned requirements file with one command and refuses any other interpreter. The archive as it stands hashes to version 6 plus the decision entries added after round 6; earlier versions are documented by hash in the round log.

Location and licence: [to be filled at publication: repository URL, archival DOI, CC BY 4.0 for documents and MIT for code].
```

The requirements file pins NumPy and pytest but cannot pin or install Python 3.12. The documented `python3 -m venv .venv ...` command therefore builds whatever `python3` is on the machine; with Python 3.14—the version recorded in the bundled `.venv`—`run_gate.py` deliberately exits 2. Thus a concrete clean-checkout sequence using the documented command can fail before any test runs.

Provide a launcher that provisions 3.12 explicitly (`uv`, `pyenv`, Conda, or a container), pin the patch version, and report the tested platform. Remove the bundled machine-specific `.venv`.

**claude-code/F-6** (P2)

`docs/report/technical-report.md:195`

```
The gate runs under a Python 3.12 environment built from the pinned requirements file with one command and refuses any other interpreter.
```

`docs/archive/red-team/executable-proofs/gate/.venv/pyvenv.cfg:1-4`

```
home = /opt/homebrew/opt/python@3.14/bin
include-system-site-packages = false
version = 3.14.7
```

with `numpy-2.5.3.dist-info/` in its `site-packages`, against `requirements.txt`'s `numpy==2.4.4` and:

`docs/archive/red-team/executable-proofs/gate/run_gate.py:9-10`

```
    if numpy.__version__ != pins.get("numpy", numpy.__version__) or not platform.python_version().startswith("3.12."):
        print(f"ERROR: environment does not match pins (need python 3.12.x, numpy=={pins.get('numpy')}); create the documented venv"); sys.exit(2)
```

A reader who follows the archive's own resume instruction (`CHECKPOINT.md:22`, `cd executable-proofs/gate && python3 run_gate.py`) with the environment that is sitting in the directory gets exit 2 before a single test runs. The gate really does pass (`gate.output.txt:120`, `GATE PASS: tests 66/66, mutation exit 0`), so this is not a claim about the gate's correctness — it is that the one reusable artefact the report advertises is shipped in a state that fails on first contact, and the report says nothing about it. "With one command" is also not what `run_gate.py:12-14` documents (venv creation, pip install, then run).

Fix: "The gate runs under a Python 3.12 virtualenv built from the pinned `requirements.txt`; the runner refuses any other interpreter. The `.venv` directory left in the archive is a Python 3.14 environment and will be rejected — delete it and rebuild before running." Or delete the stale `.venv` from the archive and keep the sentence as written.


### 5. P2 — The companion file map uses a nonexistent abbreviated path and does not provide the promised claim-level audit trail

`docs/report/file-map.md:5-12`  ·  found by openai alone

**codex/F-6** (P2)

`docs/report/file-map.md:5-12`

```
| Report item | Adjudication | Reviewer inputs and captured output |
|---|---|---|
| Table 1 (rounds, hashes, gate counts) | `readiness-protocol.md` (round log; hash and gate count at each freeze) | `freeze-manifest.txt`, `freeze.py`; `round2-…round6-adjudication-and-tally.md` |
| Round 0 (single-model red team, prior art) | `README.md`, `findings.md` (F2), `evidence.md`, `research-round-2.md` | |
| Table 2 (round 5 base cell) | `round5-adjudication-and-tally.md` §1 | `review5-claude-opus/sim_frozen.py`, `sim_frozen.output.txt`; `review5-codex/sim_frozen.py`, `sim_frozen-output.txt`; `review5-gemini/sim_frozen.py`, `sim_frozen.output.txt`, `sim_frozen_results.json` |
| Round-5 perturbation set, floor, 0.975 static vector, 60–70 % no-change | `round5-adjudication-and-tally.md` §1 items 2–5 | `review5-claude-opus/findings.md`, `schange_split.output.txt` (0.975 is this reviewer's) |
| D-11 (six decisions) | `decisions-required.md` (D-11 table); `stage-0a-contract-v3.9.md` §L | |
| Table 3 (round 6 family L) | `round6-adjudication-and-tally.md` §1 | `review6-codex/report.md` (per-cell tables with t intervals), `sim_frozen.results.json`; `review6-gemini/sim_output.txt`; `review6-claude-opus/report.txt`, `results/` |
```

`round2-…round6-adjudication-and-tally.md` is not a real file or a resolvable glob, and the row omits round 1’s source entirely. Several filenames are only meaningful by positional inheritance from the preceding directory, making automated resolution ambiguous. More importantly, Table 1’s hashes cannot be derived from any mapped immutable input.

List every exact relative path separately, add line/section anchors, and map each hash to an immutable snapshot or per-file checksum manifest.


### 6. P2 — Calling round 8 a “one-page derivation” materially understates the review that supports the report’s only formal result

`docs/report/technical-report.md:18-20`  ·  found by openai alone

**codex/F-3** (P2)

`docs/report/technical-report.md:18-20`

```
A derivation in round 8, agreed by all three systems, showed that moving the confounder onto the controlled channels would not rescue an identifiability claim either: the policy's own action noise is an instrument, so only a restricted class of passive models fails, and only on an open set of parameters.

No path to a claim above "benchmark plus findings" survived. This report records what did: two empirical results with their construction caveats, one population-limit result on where passive tracking fails, a generator and test gate with their known gaps stated, and four errors of mine that the protocol caught, three within one execution round each and one within a one-page derivation.
```

The prompt requested one page, but the archived reviewer derivations are long technical documents containing distinct spectral, regression, identifiability, finite-sample and generator analyses; they also contained a substantive initial disagreement over whether observational equivalence was open-set or knife-edge that adjudication had to reconcile. Describing this as “one-page” makes the discovery appear dramatically cheaper and simpler than the evidence record.

Replace “within a one-page derivation” with “in round 8’s cross-model derivation and adjudication,” and state that the reviewers’ derivations were substantially longer than the requested page.


### 7. P2 — §2 says round 3 used a non-Opus Claude reviewer; the round-3 adjudication says Opus, and it was round 2 that used a different Claude model

`docs/report/technical-report.md:35-35`  ·  found by anthropic alone

**claude-code/F-3** (P2)

`docs/report/technical-report.md:35`

```
- **Three model families, one prompt.** Each round the identical prompt went to Codex (OpenAI), Gemini (Google) and a Claude agent (Anthropic; Opus in every round except round 3, which used a different Claude model). Round 2 used a fourth reviewer from the Claude family.
```

`docs/archive/red-team/round3-adjudication-and-tally.md:3`

```
Date: 7 September 2026. Reviewers: Codex (14 findings), Gemini (9), fresh-context Claude Opus (19); all three built independent simulations of a contract-B instance and the draft-2 detector.
```

`readiness-protocol.md:63` agrees ("Codex 14, Gemini 9, Opus 19 findings"). The round-3 *prompt* (`readiness-protocol.md:57`) asked for "a fresh-context Claude on a different model", but the record of who actually reviewed names Opus — an internal archive contradiction the report resolves silently in the wrong direction. Meanwhile the round that genuinely used a different Claude model is round 2:

`docs/archive/red-team/round2-adjudication-and-tally.md:3`

```
Reviewers: Fable (fresh context), Codex, Gemini, Opus (fresh context; executed evidence in `review2-claude-opus/`, narrative findings pending at time of writing).
```

So the parenthetical is inverted, and the round-2 sentence omits the fact that makes the fourth reviewer interesting (it was a different model, Fable — the same model that ran round 0, per `README.md:5`). This is a model-diversity claim in a report whose whole warrant is cross-model independence; a referee will check it first.

Fix: "…and a fresh-context Claude agent (Anthropic), Opus in every round whose adjudication names the model. Round 2 used a fourth Claude-family reviewer on a different model (Fable), and the round-3 prompt asked for a different model although the round-3 adjudication records Opus."


### 8. P2 — §4.1's 0.975 static-control number drops the "confounder absent" condition, and credits the other two reviewers with a result neither of their findings files contains

`docs/report/technical-report.md:103-103`  ·  found by anthropic alone

**claude-code/F-2** (P2)

`docs/report/technical-report.md:103`

```
In one reviewer's run, on the instances where the event did change the support, a per-channel vector fixed at fit time, which never saw the scored episode or the event, scored 0.975 against 0.77 to 0.88 for the two arms; the other two reported the same qualitative result, and the exact figure is single-model.
```

The source states two conditions, and the report carries only one:

`docs/archive/red-team/review5-claude-opus/findings.md:64`

```
Confounder absent, restricted to the instances where the event actually changes `S^obs,ε`: AUC(static `l`) = **0.975** (τ=0) / **0.969** (τ=2) against seq_ibd 0.774 / 0.882 and the comparator 0.845 / 0.831
```

Dropping "confounder absent" matters because the comparator's present-condition base-cell AUC is 0.675–0.691 (Table 2): a reader who assumes the same condition as the surrounding paragraph will read the static vector as beating arms that are 0.09 AUC weaker than the ones actually compared.

Second, "the other two reported the same qualitative result" is not supported. `round5-adjudication-and-tally.md:22` attributes the fit-time-constant result to Opus by name and attaches "(three of three)" to the CL-4 non-certification clause only. Grepping the other two reviewers' findings for `static`, `fit-time`, `constant`, `both arms`, `never sees`, `answerable` and any AUC ≥ 0.9 returns nothing in `review5-codex/findings.md`; `review5-gemini/findings.md:16` and `:97` report the CL-4 defect and the 60–70 % prevalence but no static-control measurement. The three-of-three fact is "the event usually changes nothing"; the constant-beats-both-arms fact is one model's. This is the exact failure mode §2's "Single-model results are unverified" rule exists to prevent, and it was flagged as blocking last round (item 6); draft 2 adopted half the fix.

Fix: "…scored 0.975 with the confounder absent, on the instances where the event did change the support, against 0.774 for the interventional arm and 0.845 for the comparator in the same cell. That number is single-model and was not reproduced; the finding that the event usually changes nothing was reported by all three."


### 9. P2 — The claim that three defects were “invisible in prose to three reviewers” describes review rounds that never occurred

`docs/report/technical-report.md:175-187`  ·  found by openai alone

**codex/F-2** (P2)

`docs/report/technical-report.md:175-187`

```
The execution rounds and the derivation round exposed four errors of mine, each of which changed the benchmark's estimand or its verdict.

**A change score that could not see the change.** The comparator's innovation-mean-shift statistic was specified by analogy with a CUSUM on residuals. Under a centred policy an actuator loss leaves the residual mean unchanged. The statistic entered at version 4, survived round 4, in which three models implemented both arms on instances of their own and disagreed by 0.2 AUC on the comparator, a disagreement that was blamed on the unspecified generator, and was found in round 5, the first round on one frozen generator, by one reviewer's algebra and two reviewers' measurements.

**A primary that mostly measured static structure.** The generator's event was not certified to change anything, and on most instances it did not. A fit-time vector beat both arms. Found in the same round. Any change-detection benchmark needs a control that never sees the change and must be shown to score at chance.

**A primary the treatment could not reach.** My repair restricted scoring to the pre-event support, which contains no confounded channels, so the benefit was identically zero. Found in the next execution round by all three reviewers. Before adopting a primary, confirm on the generator that the treatment changes the streams the primary scores.

**A premise a derivation refuted.** I routed the programme toward a body-reaching confounder on the belief that passive support tracking would be non-identifiable there in principle. All three systems showed it is not: the policy's own action noise is an instrument, so exact non-identifiability is a knife-edge. Found by a one-page prose round before anything was built, the cheapest of the four.

In the first three cases the defect was invisible in prose to three reviewers and became unmissable once three systems ran the same frozen instances.
```

The report itself says round 4 was an implementation round, not prose. The frozen generator implicated by the second defect did not exist in round 4. The third defect was introduced by the post-round-5 repair and went directly into round 6, so no three-reviewer prose round ever had an opportunity to inspect it. The sentence invents a prose-versus-execution comparison that the chronology cannot support.

Replace it with the actual mechanisms: the first defect survived implementations run on different instances; the generator defect became testable only after the generator was frozen; and the third defect was first exposed in the execution round immediately after it was introduced.


### 10. P3 — §3.2's "never sees a label" is contradicted by the arm's own information-set declaration

`docs/report/technical-report.md:71-73`  ·  found by anthropic alone

**claude-code/F-8** (P3)

`docs/report/technical-report.md:71`

```
It never sees a label, a reward or the event time.
```

`docs/archive/red-team/sequential-ibd-spec.md:27`

```
- `configure(bundle)`: `regime_model_params = None`; `calibrator_params = {g_knots}`, **fitted by the harness** (it owns the oracle labels) on **this instance's** calibrator split;
```

The spec's own `information_set` string (line 25) ends `calibrator_injected_via_configure`. The raw statistic and the primary are label-free; the probability tier consumes a calibrator fitted on oracle labels. §7 says the calibrated tier was never run, so nothing in the results changes — but the sentence as written is a stronger blindness claim than the specification makes, and it appears in the section a referee reads to decide whether the arm is fairly matched against the comparator. Flagged last round (item 41); not fixed. Fix: "Its raw statistic never sees a label, a reward or the event time; the probability tier, which was never run, would consume a harness-fitted calibrator trained on oracle labels."

---

**On `file-map.md`:** every path I sampled resolves — `review6-claude-opus/results/`, `review6-codex/surviving_mutant_family_n_scope.py`, `review8-claude-opus/check_algebra.py`, `executable-proofs/gate/gate.output.txt`, `superseded-specs/`, `freeze-manifest.txt`. No findings against it. Its one gap is that it maps tables to sources but not the §4.1 numbers whose provenance is contested above (the 0.975 line correctly says "0.975 is this reviewer's"; the round-5 non-determinism has no row at all).

**Two previous should-fix items remain unaddressed and I record them without raising separate findings, since both are judgement rather than fact:** the report still never states that D-13 was open when it was written or what would reopen the programme (`decisions-required.md:5`, "## D-13 (open)"); and §5's "On this generator that claim is false as posed" (line 173) still asserts falsity of a conjunction whose "under confounding" half the report itself shows was never tested on the scored channels.

**claude-code/F-7** (P3)

`docs/report/technical-report.md:73`

```
**Delay-aware passive comparator.** A frozen linear one-step predictor of the observation from the previous observation and three lags of the action, ridge-fitted on fault-free episodes of the same instance with standardised features.
```

`docs/archive/red-team/comparator-spec.md:47`

```
  **φ_t = [ o_t (C), a_t (K), a_{t−1} (K), a_{t−2} (K), 1 ] ∈ R^{C+3K+1}**
```

Three action *blocks* (3K columns), but the current action plus two lags — the spec is explicit at line 49 that "Lag depth is `τ_max = 2` from the contract registry". "Three lags" implies `a_{t−1..t−3}`, which would put the arm's deepest lag one step past the maximum delay it is meant to cover, and quietly changes the delay-alignment story that §4.2 uses to explain the delay-2 cells. Flagged last round (item 42); not fixed. Fix: "the previous observation, the current action and two action lags".

