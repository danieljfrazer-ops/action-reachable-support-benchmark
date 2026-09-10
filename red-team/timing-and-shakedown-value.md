# Timing basis, revised estimates for agentic execution, and the value of the memory shakedown

Date: 6 September 2026. Written in answer to two questions from Daniel.

## 1. What the timing estimates were based on

Honest answer: the estimates in roadmap-v2 and in the Codex review were calendar-time judgments for one person doing the coding, reading, running and writing, at roughly part-time intensity. They were not derived from an hours model. The original report gave no timings at all; roadmap-v2 added them by analogy to how long comparable small-scale benchmark papers take a solo researcher; Codex judged them "plausible only with scope reduction" on the same basis. None of the three assumed agentic coding.

That matters because the work divides into parts that agents accelerate a lot and parts they do not.

| Component | Agents accelerate? | Why |
|---|---|---|
| Writing the environment, baselines, tests, ledger | Yes, strongly (5 to 10x) | Well-specified code from a written contract |
| Reproducing IBD and other baselines faithfully | Yes, moderately (2 to 3x) | Papers must be read and choices checked by a person |
| Deciding the estimand, targets, distractor classes | No | This is the scientific content; agents can propose, a person must decide |
| Reviewing results, spotting artefacts, rethinking | No, and it becomes the bottleneck | Agents produce plausible-but-wrong protocols quickly; every result needs human reading |
| Laptop compute for confirmation sweeps | No | Fixed by seeds x conditions x steps on an M5 Air |
| Writing the paper | Partly (2x) | Drafting is fast; the argument and figures need a person |
| Waiting for feedback, venue calls | No | External |

## 2. Revised estimates with Claude Code (Opus 5) and Codex (GPT-5.6) doing the implementation

Assumptions: Daniel spends a few hours per day reviewing and deciding; the two agents are used adversarially (one builds, the other red-teams each stage, as in this exchange); the Air runs unattended overnight with step budgets.

| Stage | Roadmap-v2 estimate (solo human) | Revised estimate (agentic) | What sets the floor now |
|---|---|---|---|
| Stage 0A: causal contract, generator, invariants, 4 baselines incl. IBD reproduction | 2 weeks | 4 to 7 days | Daniel deciding the estimand choices in the contract; checking IBD reproduction against the paper |
| Stage 0B: sequential change protocol, detection curves, calibrator split, Bayesian baselines | 2 to 4 weeks | 1 to 2 weeks | Reviewing detection-curve definitions; first overnight sweeps |
| Paper 1 pilot and power study | (inside 22 weeks) | 1 to 2 weeks | Compute: pilot sweeps, then choosing the primary contrast |
| Paper 1 confirmation runs (10 seeds, two dynamics families, fractional design) | (inside 22 weeks) | 1 to 2 weeks | Compute: roughly 1 to 3 laptop-days per family, rerun if a bug is found |
| Paper 1 write-up, figures, novelty re-check, red team by the other agent | (inside 22 weeks) | 2 to 3 weeks | Daniel's reading and revision |
| **Paper 1 total to arXiv** | **~22 weeks (mid-Feb 2027)** | **8 to 12 weeks (late Nov to mid-Dec 2026)** | Review throughput and reruns |
| Memory shakedown (hardened R1 protocol, no learned router) | 2 to 4 weeks | 1 to 2 weeks build and run, plus 3 to 5 days write-up | Compute: 1 to 10M-parameter models on 100k to 1M event streams, ~9 baselines x budgets x 5 to 10 seeds is several laptop-days |
| Paper 2 | Feb to Jun 2027 | 6 to 10 weeks after Paper 1 | Same pattern |

Two cautions. First, agentic speed shifts the risk from "not finished" to "finished but wrong." The invariant tests, the frozen evaluator, and the build-then-red-team loop between the two agents are what make the speed safe; skip them and the time saved is lost in retractions. Second, compute is now a visible fraction of the schedule. The Air's throttling means overnight sweeps take longer than a benchmark on a cool machine suggests; plan for 1.5x.

Net effect: mid-February 2027 changes from "only with aggressive scope reduction" to "comfortable, with room for the memory shakedown and a reserve."

## 3. Would the memory shakedown be a genuine contribution?

**Short answer: yes, small, real, and useful to us; modest for others. Its value depends entirely on protocol discipline.**

What would be genuinely new, assuming nobody publishes the same thing in the window:
- No published table compares recurrent state, fast weights, an episodic store and slow weights as storage choices for the *same* items under hidden per-item change rates, delayed queries, transient anomalies and reversals, at matched **total** budget. The components exist; the matched comparison does not.
- The principle-level answer is expected (fast-changing items belong in fast memory). The informative unknowns are the crossover points and the failure modes:
  1. Does the episodic store dominate everything at matched write cost, making the "routing" question moot at small scale?
  2. Do fast weights reduce forgetting or just move it into a different store?
  3. Is surprise-based writing (the Titans signal) systematically wrong under transient anomalies?
  4. Does a trivial empirical-hazard heuristic match anything learned?
  Each of those can come out either way, and each is a quotable finding.

Value to this programme:
- It builds and tests the ledger, seeds, budget matching, evaluator lock and thermal protocol on the simplest possible case.
- It gives Paper 3 its baseline numbers and tells us whether a fast-self / slow-world split is worth building into the agent at all. If the episodic store wins everywhere at small scale, Paper 3 changes shape.
- It gives Daniel a first public artefact and an arXiv record within about a month.

Value to others:
- A careful phase diagram or a crisp negative result (especially item 3, given how widely Titans is cited) is the kind of note that gets cited in related-work sections of memory papers. It will not be a headline result. Reviewers would call it a useful sanity check.
- If budget matching is sloppy the note is worthless and slightly damaging; if it is rigorous the note is credible precisely because it makes no method claim.

What it would not do:
- Advance the self-modeling direction directly.
- Protect against being scooped on any *method*; it makes no method claim, which is why it is safe.

## 4. Recommendation given agentic execution

Do the shakedown, in a strict two-week box, **after Stage 0A**, run in parallel with Stage 0B where the agents allow. With the revised schedule it no longer threatens Paper 1. Publish it as a technical note regardless of outcome, with the contribution type stated as "benchmark and negative results."
