# Red-team review — RT-20260909-002

**FAIL** — 2 blocking problems with checked evidence.

3483 files reviewed. 2 of 2 required model families produced a usable review (anthropic, openai).
**FILES MOVED WHILE THE REVIEWERS RAN: 1 appeared (docs/archive/red-team/review9-claude-opus/report-review.md)**

## Worth knowing

- 4 symlink(s) were not followed, so the reviewers did not see what they point at: docs/archive/red-team/executable-proofs/gate/.venv/bin/python, docs/archive/red-team/executable-proofs/gate/.venv/bin/python3, docs/archive/red-team/executable-proofs/gate/.venv/bin/python3.14
- 2 directories were skipped by name and never reviewed: docs/archive/red-team/.DS_Store, docs/archive/red-team/executable-proofs/.DS_Store
- antigravity did not count towards diversity — did not produce a review (error)

## Who reviewed

| Reviewer | Model that actually ran | Family | Counts | Status | Time | Kept |
| --- | --- | --- | --- | --- | --- | --- |
| claude-code | `claude-opus-5` (envelope) | anthropic | yes | ok | 460s | 9 |
| codex | `gpt-5.6-sol` (session-log) | openai | yes | ok | 167s | 7 |
| antigravity | `gemini-3.1-pro-high` (pinned-slug) | google | **no** | error — error: Individual quota reached. Please upgrade your subscri | 806s | — |

## What they found

### 1. BLOCKING — "all three agreed to three decimal places on every number both times" is false for round 5, and the report's own Table 2 disproves it two pages later

`docs/report/technical-report.md:16-20`  ·  **found by 2 families: anthropic, openai**

**claude-code/F-1** (P1, blocking)

`docs/report/technical-report.md:16`

```
Before any confirmatory experiment, the design went through eight rounds of adversarial review by three AI systems (Claude, Codex and Gemini), each round on a frozen, hashed version of the specifications and code, with the author adjudicating and never reviewing. Rounds 5 and 6 were execution rounds: each system implemented both estimators from the written specifications alone and ran them on the same frozen simulator, and all three agreed to three decimal places on every number both times.
```

The archive says "Monte Carlo error" for round 5, not three decimals:

`docs/archive/red-team/round5-adjudication-and-tally.md:9-16`

```
| Sequential IBD AUC, N_x = 10, τ = 0 | 0.800 | 0.815 | 0.831 |
```

Round 5's headline AUCs disagree in the *first* decimal (0.800 / 0.815 / 0.831), and the benefit spans +0.187 / +0.204 / +0.190. Only round 6 achieved three-decimal agreement (`round6-adjudication-and-tally.md:7`, "agree to three decimals on every number"). The report then repeats the overreach at the head of §4.1 — `technical-report.md:86` "Three independent implementations agreed on every number." — immediately above a table showing they did not.

This matters because cross-model agreement is the report's entire evidentiary warrant; overstating it in the summary is the single claim a hostile referee will check first.

Fix: in the summary write "agreed to Monte Carlo error in round 5 and to three decimal places in round 6"; in §4.1 replace "agreed on every number" with "agreed to within Monte Carlo error on every number (Table 2)".

---

**codex/F-1** (P1, blocking)

`docs/report/technical-report.md:16`

```
Rounds 5 and 6 were execution rounds: each system implemented both estimators from the written specifications alone and ran them on the same frozen simulator, and all three agreed to three decimal places on every number both times.
```

The round-5 record says only that implementations agreed within Monte Carlo error; its base-cell Sequential IBD estimates were 0.800, 0.815, and 0.831, while comparator estimates were 0.691, 0.688, and 0.675 (`docs/archive/red-team/round5-adjudication-and-tally.md:7-16`). Only round 6 agreed to three decimals (`docs/archive/red-team/round6-adjudication-and-tally.md:7-12`). This false precision also conflicts with the report’s own Table 2.

Rewrite: “In round 5, the three implementations agreed within Monte Carlo error; in round 6, they agreed to three decimal places on every primary number and control.”

**codex/F-2** (P2)

`docs/report/technical-report.md:16`

```
Before any confirmatory experiment, the design went through eight rounds of adversarial review by three AI systems (Claude, Codex and Gemini), each round on a frozen, hashed version of the specifications and code, with the author adjudicating and never reviewing.
```

Rounds 7 and 8 were prose-only reviews over an assembled documentary record, not reviews of a newly frozen specification-and-code hash. The report’s own table calls their frozen versions merely “as reviewed” (`docs/report/technical-report.md:51-52`), while the archive explicitly describes round 7 as “prose only” and round 8 as a “prose derivation” (`docs/archive/red-team/readiness-protocol.md:106-118`). This makes the protocol sound more uniform and tamper-evident than it was.

Rewrite: “Rounds 1–6 reviewed frozen versions; rounds 7 and 8 were cross-model prose reviews of the cited archived record.”

**claude-code/F-2** (P1, blocking)

`docs/report/technical-report.md:18`

```
On adaptation, the task of noticing which controlled sensor has gone quiet after an actuator loss, a passive delay-aware covariance monitor equalled or beat the probed estimator in every cell.
```

`docs/archive/red-team/round6-adjudication-and-tally.md:33`

```
- Family N (five seeds, wide intervals): seq-IBD 0.84 against comparator 0.73 at τ = 0; the comparator floor fails there. Reproduction target only.
```

Confirmed in the raw round-6 output — family N, τ = 0, offset 500 on the *primary* (pre-event-support) AUC:

`docs/archive/red-team/review6-codex/report.md:88`

```
| N_Nx10_tau0 | present | 500 | 0.840 [0.729, 0.951] | 0.728 [0.363, 1.092] | 0.860 [0.761, 0.960] | 0.794 [0.705, 0.882] |
```

The adjudication's own wording is carefully scoped — "in every family-L cell and every perturbation cell" (`round6-adjudication-and-tally.md:20`) — and §4.2 of the report preserves that scope. But the summary (line 18) and the surviving-claims section (line 154, "On the plant studied, a passive delay-aware covariance monitor equals or beats sign-randomised probing") drop it, and §7 mentions family N only as "one nonlinear variant run on five seeds" without saying the sign flipped there. The one nonlinear cell in the whole programme reverses the report's headline negative result, and a reader of the summary and §5 alone would never learn it.

Fix: scope both sentences to family L ("in every linear-family cell and every perturbation cell"), and add one sentence to §4.2 or §7: "On family N (five seeds, wide intervals) the ordering reversed: sequential IBD 0.84 against the comparator's 0.73 at delay 0, with the comparator floor also failing there. Family N was a reproduction target, not part of the exit condition, and five seeds cannot settle the sign."

---

**codex/F-5** (P2)

`docs/report/technical-report.md:18-20`

```
What the numbers showed is not what the programme hoped. The interventional advantage is real but is confined to attribution: under a shared-cause confounder, the passive monitor wrongly credits the agent with control over confounded distractor sensors and the probed estimator does not, a margin of about 0.2 AUC. That is the result the IBD paper already proved for the static case. On adaptation, the task of noticing which controlled sensor has gone quiet after an actuator loss, a passive delay-aware covariance monitor equalled or beat the probed estimator in every cell.
```

Round 7 explicitly withdrew “interventions buy attribution, not adaptation” because attribution and adaptation were measured on different channel sets under different confounding regimes (`docs/archive/red-team/round7-adjudication.md:20-25`). Although later sections acknowledge this problem, the summary still juxtaposes the results as if they establish that the advantage is “confined to attribution.” Many readers will rely principally on the summary, so the later caveat does not cure the overclaim.

Rewrite: “The full-channel attribution endpoint favored probing, while a different, unconfounded pre-event-support endpoint favored the passive monitor. Because the endpoints used different channel sets and effective regimes, these experiments do not establish an attribution–adaptation dissociation.”


### 2. BLOCKING — Table 1 gives round 4 the hash of frozen version 5, invents a "(candidate)" label, quotes post-repair gate counts, and the caption's reproduction instruction does not work

`docs/report/technical-report.md:47-54`  ·  found by anthropic alone

**claude-code/F-3** (P1, blocking)

`docs/report/technical-report.md:47-54`

```
| 3 | 7 Sep | prose + gate | e662b7429b6b347d | Contract v3.3, interface v3, IBD spec draft 2; 31 tests |
| 4 | 7 Sep | prose + gate | 0468104f6431b050 (candidate) | Both estimator specs; 37 tests, 40 mutants |
| 5 | 7 Sep | execution | 0468104f6431b050 | Three implementations on the frozen generator |
```

Round 4 was reviewed on a different frozen version:

`docs/archive/red-team/readiness-protocol.md:70`

```
### Frozen version 4 — `442cc4b7da691ca0` (7 Sep 2026): both arm specifications
```

`0468104f6431b050` is version 5 (`readiness-protocol.md:84`), which the table also — correctly — assigns to round 5. So two different rounds are shown reviewing the same bytes, and the true round-4 hash `442cc4b7da691ca0` appears nowhere in the report. "(candidate)" is not in the record either: the post-round-4 candidate was `9af01507bc5f6618` (`readiness-protocol.md:79`).

The gate counts are also off by one repair cycle. Version 4 as frozen carried 34 tests / 35 mutants (`readiness-protocol.md:68`); "37 tests, 40 mutants" is the *post*-round-4 repair state (`readiness-protocol.md:79`), and version 5 as frozen had 47 tests / 40 mutants (`readiness-protocol.md:85`). Likewise round 3's "31 tests" is the post-round-3 number; the version reviewed in round 3 had 23 (`readiness-protocol.md:49`). The table therefore credits each round with a gate built in response to it.

Finally the caption's verification recipe is wrong:

`docs/archive/red-team/CHECKPOINT.md:22`

```
1. Verify: `cd executable-proofs/gate && python3 run_gate.py` (Python 3.12, numpy 2.4.4), expect exit 0; `python3 ../../freeze.py` must print `eee1ab5834e35788` (version 6 plus the D-12 entry in `decisions-required.md`); anything else means a normative file was edited and that is a process breach to record.
```

`freeze.py` hashes the folder's *current* state against the current manifest and prints exactly one hash — today `eee1ab5834e35788`, none of the eight in Table 1. A reader following "`freeze.py` in the archive recomputes them" gets one number that matches no row.

Fix: set row 4's hash to `442cc4b7da691ca0` and drop "(candidate)"; give each row the gate counts of the version *as frozen* (23 for v3, 34/35 for v4, 47/40 for v5, 66/47 for v6) or drop the counts from the table; rewrite the caption as "Hashes are the first sixteen hex digits of the SHA-256 over each version's manifest, in manifest order; `freeze.py` recomputes the hash of the archive as it currently stands (`eee1ab5834e35788`, version 6 plus the later D-12 entry in `decisions-required.md`), not of earlier versions." Also disclose in §2 or §8 that the archived folder no longer hashes to the round-6 review target for this reason.

---


### 3. P2 — The report has no traceable data-and-code availability map for its quantitative claims

`docs/report/technical-report.md:96-102`  ·  **found by 2 families: anthropic, openai**

**codex/F-6** (P2)

`docs/report/technical-report.md:96-98`

```
Table 2. Round 5 on frozen version 0468104f6431b050. Intervals clustered by instance are in the archive; the benefit's lower bounds were 0.153 to 0.158.

Three things followed. The interventional arm was robust and reproducible, at 0.80 to 0.85 across distractor levels, delays and a perturbation set over coupling and noise scale, and insensitive to the confounder.
```

“The archive” is not a usable citation in a directory containing thousands of files and multiple superseded specifications and outputs. The report similarly provides no repository URL, persistent identifier, commit, exact manifest path, or per-table source-file map. Consequently, a reader cannot reliably determine which scripts and outputs support each table or reconstruct the stated intervals without already understanding the internal archive.

Add a reproducibility appendix mapping every table and major numerical claim to exact archived input, implementation, captured-output, and adjudication paths, plus the full freeze hash and environment. Add a public repository URL or archival DOI if this report is distributed outside the current tree.

**claude-code/F-5** (P2)

`docs/report/technical-report.md:98-102`

```
Three things followed. The interventional arm was robust and reproducible, at 0.80 to 0.85 across distractor levels, delays and a perturbation set over coupling and noise scale, and insensitive to the confounder. The confounding benefit cleared the pre-declared margin of 0.10 in every base cell. And the result was inadmissible, because the competence floor failed in every cell: without confounding the comparator's lower bound was 0.64 to 0.83 against the required 0.85.

The cause was identified analytically by Codex and measured by the other two. Under a centred policy, losing an actuator does not shift the mean of the predictor's innovations; it changes their variance and their covariance with the action. The comparator's change statistic was a mean-shift test and therefore could not see the event, and the loading term alone ranked the support at 0.99 without confounding. The baseline was not weak; it was specified with a statistic blind to the change it was meant to detect.

The third finding was worse for the design. The generator did not guarantee that losing actuator 0 removed any observed channel from the support, and on 60 to 70 percent of frozen instances it removed none. The primary was therefore mostly a test of static structure. A per-channel vector fixed at fit time, which never saw the scored episode or the event, scored 0.975 against 0.77 to 0.83 for the two arms.
```

Two problems against the record.

`docs/archive/red-team/round5-adjudication-and-tally.md:19-22`

```
2. **The confounding benefit clears the margin in every base cell** (+0.15 to +0.28), but the perturbation set does not (aggregate lower bound 0.090; individual configurations from −0.015 to +0.25).
```

(a) The report keeps the half of item 2 that supports the surviving claim and drops the half that qualifies it. On the perturbation set the benefit's aggregate lower bound was 0.090 — below the 0.10 margin — with individual configurations as low as −0.015. Since §5 sells the attribution result as the programme's main survivor, the fact that it did not clear its own pre-declared margin outside the base cells belongs in §4.1 and in §7.

(b) "scored 0.975" is a single-model measurement. The same adjudication line attributes it to one reviewer ("Opus: a fit-time constant … beats both confirmatory arms (0.975 versus 0.77 to 0.83)"), with the "(three of three)" attaching to the CL-4 non-certification, not to the number. The report places it under the heading "Three independent implementations agreed on every number", which converts a single-model figure into an agreed one — exactly the failure mode §2's own rule ("Single-model results are unverified") exists to prevent.

Fix: append to the second sentence "…in every base cell, though not on the perturbation set, where the aggregate lower bound was 0.090 and individual configurations ran from −0.015 to +0.25"; and change the last sentence to "A per-channel vector fixed at fit time … scored 0.975 in one reviewer's run (the other two measured the same qualitative result; the exact figure is single-model)."

---


### 4. P2 — the report enumerates three author errors but omits the fourth, which round 8 states in bold; and §8 gives no location for the artefacts it asks readers to reuse

`docs/report/technical-report.md:160-170`  ·  **found by 2 families: anthropic, openai**

**claude-code/F-8** (P2)

`docs/report/technical-report.md:160-162`

```
## 6. Three errors, and what caught them

The errors are more useful than the results.
```

`docs/archive/red-team/round8-adjudication.md:7`

```
1. **Exact passive non-identifiability is a knife-edge, not an open set.** The observational law of (o, a) at all lags contains the policy's own independent action noise (σ_a = 0.1 in the contract), which acts as an instrument: the covariance discontinuity at the causal lag pins B separately from the smooth AR(1) confounder path. Exact E1/E2 equivalence needs σ_a = 0 in the affected actuator direction (or ρ_u = 0). Codex and Claude state this directly; Gemini's "Theorem 1" is a statement about the apparent regression coefficient of a no-latent estimator and its own remark concedes that matching the full law requires σ_a → 0. **The D-12 practice premise as the author wrote it, "passive support tracking is non-identifiable in principle", is false on this plant.**
```

Round 8 records a fourth author error in the same register as the three in §6: the premise on which D-12 routed the programme toward option C — "passive support tracking is non-identifiable in principle" — was false, and the derivation round that tested it before any build is precisely the kind of process win §6 is about. §4.4 conveys the technical conclusion but never says the premise was the author's and was wrong; §6 and §9 ("am responsible for the errors in Section 6") therefore under-report. Given the report's stated purpose is that the errors are the contribution, omitting one is a substantive gap, not a stylistic one.

Separately, §8 describes the archive at length but never says where it is — no URL, DOI, repository, or licence — and §5 offers the generator and gate "that others can reuse". Table 3 reports AUCs with no n and no intervals ("Intervals clustered by instance are in the archive"), while the contract fixes replication at "10 × 4 by default" (`stage-0a-contract-v3.9.md:38`). Three of the six references (Basseville & Nikiforov 1993, Mann & Whitney 1947, Page 1954) are never cited in the text.

Fix: retitle §6 "Four errors, and what caught them" and add: "**A premise that a derivation refuted.** I routed the programme toward a body-reaching confounder on the belief that passive support tracking would be non-identifiable there in principle. All three systems showed it is not: the policy's own action noise is an instrument, so exact non-identifiability is a knife-edge. Found by a one-page prose round that cost nothing to run — the cheapest of the four." Add an availability line to §8 with the archive's location and licence; add "n = 10 instances × 4 episode seeds per cell" and the interval bounds to Tables 2 and 3; either cite Basseville, Mann–Whitney and Page at the points they are used (§4.3, §3.2, §6) or drop them.

---

**codex/F-7** (P3)

`docs/report/technical-report.md:160-164`

```
## 6. Three errors, and what caught them

The errors are more useful than the results.

**A change score that could not see the change.**
```

“The errors are more useful than the results” is unmeasured, generic evaluative prose and has the machine-written cadence the requested review asks to flag. It also obscures the concrete contribution of the section.

Rewrite: “The execution rounds exposed three design failures that materially changed the benchmark’s estimand or verdict.”

**claude-code/F-9** (P3)

`docs/report/technical-report.md:164-170`

```
**A change score that could not see the change.** The comparator's innovation-mean-shift statistic was specified by analogy with a CUSUM on residuals. Under a centred policy an actuator loss leaves the residual mean unchanged. This survived four prose rounds and was found in the first execution round, in one afternoon, by one reviewer's algebra and two reviewers' measurements.

**A primary that mostly measured static structure.** The generator's event was not certified to change anything, and on most instances it did not. A constant beat both arms. Found in the same round. The lesson is that any change-detection benchmark needs a control that never sees the change and must be shown to score at chance.

**A primary the treatment could not reach.** My repair restricted scoring to the pre-event support, which contains no confounded channels, so the benefit was identically zero. Found in the next execution round by all three reviewers. The lesson is a one-line check: before adopting a primary, confirm on the generator that the treatment changes the streams the primary scores.

In each case the defect was invisible in prose, including to three reviewers, and became obvious within minutes of three systems running the same frozen instances. The cost of an execution round was under twenty minutes of laptop time per reviewer.
```

"in one afternoon" (line 164) and "within minutes" (line 170) describe the same event and cannot both stand. "Under twenty minutes" is also just outside the record:

`docs/archive/red-team/round6-adjudication-and-tally.md:3`

```
Date: 8 September 2026 (reviews dated 7 September). Reviewers: Codex (9 findings), Gemini (10), fresh-context Claude Opus (14 plus 11 open choices). All three implemented both confirmatory arms from the two specs alone and ran them on the frozen generator: configuration seeds 0 to 9, both distractor levels, both delays, present and absent, the 3 × 3 perturbation set at seed 0, and family N at seeds 0 to 4. Runtimes 5 to 21 minutes, no seed reduction. Author adjudicates; hash unchanged throughout.
```

Rewrite line 170 as: "In each case the defect was invisible in prose, including to three reviewers, and was unmissable once three systems ran the same frozen instances: 5 to 21 minutes of laptop time per reviewer, and the diagnosis written up the same day."

Three further sentences read as generic and can be cut or sharpened:

- Line 24, "Two things make the estimate hard in practice." → delete; the two sentences that follow already carry "First…Second…".
- Line 32, "Everything in this report was produced under one protocol, which I state because the protocol is what caught the errors." → "One protocol governed all eight rounds. It is worth stating because it, not the design, is what caught the errors."
- Line 150, "Three statements are supported by the evidence, each with its caveat." → delete and let the three bolded claims stand; the caveats are already attached to each.
- Line 20, "one identifiability picture" → "one population-limit result on where passive tracking actually fails" ("picture" is doing no work).

**codex/F-4** (P2)

`docs/report/technical-report.md:170`

```
In each case the defect was invisible in prose, including to three reviewers, and became obvious within minutes of three systems running the same frozen instances. The cost of an execution round was under twenty minutes of laptop time per reviewer.
```

Round 6 records runtimes of 5 to 21 minutes (`docs/archive/red-team/round6-adjudication-and-tally.md:3`), so “under twenty minutes … per reviewer” is false for at least one reviewer. It also conflates runtime with total execution-round cost: implementation, analysis, mutant construction, and adjudication time are not measured by the simulation runtime.

Rewrite: “The round-6 simulations took 5–21 minutes each; reviewer implementation and analysis time was not recorded.”


### 5. P2 — The report presents the gate and generator as reusable certified artefacts without disclosing that the gate accepted known surviving mutants

`docs/report/technical-report.md:176-178`  ·  **found by 2 families: anthropic, openai**

**codex/F-3** (P2)

`docs/report/technical-report.md:176-178`

```
## 8. Artefacts

The archive contains the eight rounds in full: every prompt, every review, every adjudication, the frozen manifests and hashes, the contract through version 3.9, the interface specification through version 5, both estimator specifications with their superseded drafts, the reference generator with families L and N, the reference implementations of the metrics, the test gate (66 tests and 47 mutants at version 6; exit code 0 under Python 3.12 and NumPy 2.4.4), and the three round-6 implementations of both estimators with their captured output. The confirmation-seed commitment is recorded; the secret was never opened. The gate runs from a clean checkout with one command.
```

The numerical gate status is real, but materially misleading without the adjudicated result that three new mutants survived and generator mutants were not registrable (`docs/archive/red-team/round6-adjudication-and-tally.md:25-26`). The readiness protocol requires every mutant to fail and also requires an independent acceptance suite, a hand-computed case, and a runtime pilot (`docs/archive/red-team/readiness-protocol.md:11-17`). A downstream user can therefore mistake exit code 0 for specification conformance even though the archive establishes the opposite.

State explicitly that version 6 was not readiness-certified, list the surviving coverage gaps, and describe the gate as a historical/research artefact rather than a certified reusable gate.

**claude-code/F-6** (P2)

`docs/report/technical-report.md:178`

```
The archive contains the eight rounds in full: every prompt, every review, every adjudication, the frozen manifests and hashes, the contract through version 3.9, the interface specification through version 5, both estimator specifications with their superseded drafts, the reference generator with families L and N, the reference implementations of the metrics, the test gate (66 tests and 47 mutants at version 6; exit code 0 under Python 3.12 and NumPy 2.4.4), and the three round-6 implementations of both estimators with their captured output. The confirmation-seed commitment is recorded; the secret was never opened. The gate runs from a clean checkout with one command.
```

`docs/archive/red-team/round6-adjudication-and-tally.md:26`

```
8. **Surviving mutants (gate defects):** `auc_pre_event_support` over `pre | post` survives because every fixture has post ⊆ pre (Claude, confirmed by Codex and Gemini); family-N certificate mutants survive (b-and-d-only or b-only bound; zero burn-in in the stationary mean: Codex, Gemini); the mutation framework iterates `test_gate` only, so no generator mutant is registrable (three of three).
```

`CHECKPOINT.md:17` says the same: "Gate: 66 tests, 47/47 mutants, exit 0; three reviewer mutants survive and are recorded for the next version." The report's §2 protocol bullet makes the gate's exit code *the* readiness criterion, and §5/§8 offer it for reuse — so the fact that the exit code provably cannot express a generator defect (no generator mutant is registrable) is load-bearing, not a footnote. Note the survivor is not hypothetical: a mutant that changes `auc_pre_event_support` to score over `pre | post` passes the whole suite, because every fixture happens to satisfy post ⊆ pre — i.e. the primary-metric test passes for the wrong reason and would still pass under a metric that scores post-event-only channels.

Second, "runs from a clean checkout with one command" fails against the shipped archive:

`docs/archive/red-team/executable-proofs/gate/run_gate.py:9-14`

```
    if numpy.__version__ != pins.get("numpy", numpy.__version__) or not platform.python_version().startswith("3.12."):
        print(f"ERROR: environment does not match pins (need python 3.12.x, numpy=={pins.get('numpy')}); create the documented venv"); sys.exit(2)
except ImportError:
    print("ERROR: numpy not importable in this interpreter. Create the documented environment:\n"
          "  python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt\n"
          "then run: python run_gate.py"); sys.exit(2)
```

`docs/archive/red-team/executable-proofs/gate/.venv/pyvenv.cfg:3`

```
version = 3.14.7
```

The venv committed inside the archive is Python 3.14.7 with numpy 2.5.3 (`.venv/lib/python3.14/site-packages/numpy-2.5.3.dist-info/`), while `requirements.txt` pins `numpy==2.4.4` and the runner hard-refuses anything but 3.12.x. Running the one documented command against the archive as shipped exits 2 before a single test runs.

Fix: change the parenthetical to "(66 tests and 47 mutants at version 6; exit code 0 under Python 3.12 and NumPy 2.4.4. Three reviewer-written mutants survive it — including one that widens the primary metric's channel set undetected because every fixture has post ⊆ pre — and the mutation runner iterates `test_gate` only, so generator mutants cannot be registered at all.)" Replace the last sentence with "The gate runs under a Python 3.12 virtualenv built from `requirements.txt`; the runner refuses any other interpreter. The `.venv` directory left in the archive is a 3.14 environment and will be rejected — delete it and rebuild." Also soften §Summary line 20's "a certified generator and test gate that others can reuse".

---


### 6. P2 — §2 states a protocol that rounds 2, 3 and 4 did not follow, and §6 calls round 4 a prose round when three models implemented both arms in it

`docs/report/technical-report.md:35-35`  ·  found by anthropic alone

**claude-code/F-7** (P2)

`docs/report/technical-report.md:35`

```
- **Three reviewers, fresh context.** Each round, the identical prompt goes to Claude (Opus), Codex and Gemini. Each reviewer starts without memory of previous rounds and may read earlier reviews only after writing its own. In execution rounds each reviewer implements both estimators from the specifications alone.
```

Round 2 had four reviewers, and "fresh context" is attached in the record only to the Claude-family ones:

`docs/archive/red-team/readiness-protocol.md:45`

```
- Reviewers: Fable (fresh context, 25 findings, 13 surviving mutants), Codex (12 findings, 1 surviving mutant), Gemini (11 findings, 1 surviving mutant), Opus (fresh context; 8 surviving mutants and a fake-kill audit; narrative pending).
```

Round 3's Claude reviewer was explicitly "a fresh-context Claude on a different model" (`readiness-protocol.md:57`), not Opus. So neither "three reviewers" nor "Claude (Opus)" nor "each reviewer starts without memory" holds uniformly; the archive marks fresh context only where it was true.

And the "prose rounds could not catch it" narrative mis-labels round 4:

`docs/archive/red-team/readiness-protocol.md:78`

```
- Three end-to-end implementations from the specs alone. Interventional arm agrees to 0.012 AUC and is robust across family N, τ = 2, N_x = 100. Comparator disagrees by 0.20 because the generator is unspecified and the comparator is structurally incapable (downstream loading; delay misalignment). The confounding-benefit verdict flips across models. D-9's "clears the margin" claim withdrawn. Alarm channel of the IBD arm unattainable (warm-up). Five surviving mutants. **D-10** with Daniel.
```

Round 4 was an execution round in all but name (three models implemented both arms; the comparator already disagreed by 0.20 AUC across them), yet Table 1 calls it "prose + gate" and §6 line 164 says the mean-shift defect "survived four prose rounds". The honest distinction is *frozen generator*, not prose: round 4's implementations each drew their own instances, which is why the comparator diverged.

Fix: rewrite the bullet as "Each round the identical prompt goes to Codex, Gemini and a fresh-context Claude agent (Opus except in round 3); round 2 additionally used a fourth Claude-family reviewer. The Claude reviewer starts without memory of previous rounds; the Codex and Gemini sessions were not certified fresh." In §6, replace "survived four prose rounds" with "survived three prose rounds and a fourth round in which three models implemented both arms on instances of their own — the disagreement there was blamed on the unspecified generator, which is why version 5 froze one."

---


### 7. P2 — "Measured twice by three implementations" overstates the round-6 replication: one of the three reviewers' secondary numbers was found wrong and excluded

`docs/report/technical-report.md:152-152`  ·  found by anthropic alone

**claude-code/F-4** (P2)

`docs/report/technical-report.md:152`

```
**Sign-randomised probing removes confounded false support that a frozen passive residual monitor shows, online and at a 5 percent probe budget.** Measured twice by three implementations, about +0.2 AUC on the full channel set. This is a replication of IBD's principle in a sequential setting, not a new result.
```

The second measurement lives in round 6's *secondary* full-channel score, and the adjudication discounts one reviewer's secondary numbers at exactly the offsets in question:

`docs/archive/red-team/round6-adjudication-and-tally.md:27`

```
9. **Gemini's secondary numbers at offsets 200 and 500 are wrong**: its script read `secondary_support()` after the episode ended (Codex). Its primary numbers and verdicts are unaffected. Recorded, not counted.
```

The primary offset is 500 (`stage-0a-contract-v3.9.md:34`). So the round-6 leg of the attribution result rests on two implementations, not three — and the numbers the report quotes in §4.2 ("0.73 to 0.80 … 0.96 to 0.98 … 0.85 to 0.87") come from that same secondary measure.

Fix: "Measured twice: by three implementations in round 5 (to Monte Carlo error) and by two in round 6, where the third reviewer's secondary numbers at the scored offsets were found defective and excluded." Add the same caveat to the §4.2 sentence carrying those ranges.

---

