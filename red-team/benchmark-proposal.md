# Benchmark proposal: a suite for sequential controllability under confounded distractors and changing bodies

Date: 6 September 2026. Answers Daniel's question: can we define a new benchmark and run various models against it? Short answer: yes, it is feasible on the stated hardware for two of three tiers, and it is the most valuable shape Paper 1 can take. Working title only, to be replaced: **Boundary-Bench**.

## 1. What the benchmark measures

An agent acts in an environment where some observation channels respond to its actions (its body), some respond to a shared hidden cause that also shapes its own behaviour (confounded distractors), some are downstream effects, and some are exogenous. At unannounced times the body changes: an actuator is lost or remapped, a sensor drops out or is swapped. The benchmark asks each method, sequentially and online:
- which channels do you control right now (support S), with what confidence;
- when did that change (typed alarm);
- at what cost in probes, samples and compute;
- how well calibrated are you through the transition.

Ground truth for all of this is exact by construction. That is what distinguishes it from every existing suite found.

## 2. Three tiers

| Tier | Environment | Ground truth | Compute per run | Purpose |
|---|---|---|---|---|
| T1 Exact | The Stage 0A structural-causal generator (families L and N) | Exact S, R, P from the declarative SCM | seconds to a minute | Unit tests, calibration scoring, phase diagrams |
| T2 Control | Gymnasium classic control (CartPole, Pendulum, Acrobot) and MuJoCo (Reacher, HalfCheetah) wrapped with: injected confounded distractor channels driven by a hidden cause that also perturbs the policy; sensor swap, dropout, gain; actuator loss and remap at unannounced times | Exact S and P by construction of the wrapper; R by finite-difference probing of the simulator | seconds to minutes for estimators; the environment is cheap | Realism check that T1 findings transfer; the tier reviewers will look at |
| T3 World models | Same T2 environments, state-based observations, small learned world models (Dreamer-style RSSM small, Iso-Dream-style two-branch, Sensorimotor-WM-style inverse-dynamics, Dueling-WM-style) | As T2 | 1 to 3 hours per training run on the M5 with MPS; 60 runs is 5 to 8 laptop-days serialised, or 1 to 2 days on a rented GPU | Paper 2: which world-model separation criteria attribute agency to confounded distractors, and how they behave when the boundary changes |

Robust-Gymnasium (ICLR 2025, MIT) already provides perturbation wrappers on observation, action, reward and dynamics at arbitrary times across sixty tasks. It has no controllability ground truth, no confounded distractor construction, and no sensor swap or actuator dropout. T2 should be implemented as wrappers compatible with it, and cited as the platform we extend, not as a competitor.

## 3. Models to run against it

**Boundary estimators (Paper 1).**
- Observational: temporal correlation; forward-model residual; mutual information; inverse-dynamics attribution (the criterion inside Iso-Dream and Sensorimotor WM, run standalone).
- Interventional: IBD as published (batch); sequential IBD with re-probing; Bayesian change-point detectors (correctly specified reference, misspecified residual, nonparametric).
- Classical FDI: CUSUM and GLR on model residuals; an auxiliary-signal active detector. These are the control-theory baselines Gemini asked for and they will be strong.
- Random.

**World-model agents (Paper 2, T3).** Small configurations, state observations, five seeds: Dreamer-style baseline; Iso-Dream-style; Sensorimotor-WM-style; Dueling-WM-style; each with and without an interventional boundary filter that removes channels outside the estimated support from the world model's input.

## 4. Metrics (from contract v2.1)

Detection delay versus average run length to false alarm (operating curves, primary scalar as normalised partial area over the shared delay interval); support F1 at fixed offsets; per-channel Brier and log loss, raw and calibrated; probes, samples, operations, and task regret to detection where a reward is defined; for T3, additionally imagination-rollout error on controllable channels and return after a boundary change.

## 5. What is new, precisely

Found today and earlier:
- IBD (Mar 2026): interventional support discovery with up to 100 distractors, static boundary, no public suite found.
- Robust-Gymnasium, RRLS, Distracting Control Suite: perturbations and background distractors; no controllability labels; no confounding by a shared cause; no body change events.
- Body-schema robotics (Sturm 2009 onward; Lipson group): change detection and adaptation on physical robots; no standardised suite, no distractor construction, no calibration metrics.
- FDI literature: active fault detection with detection and false-alarm characterisation; linear models; no learned estimators, no learned world models.
- Iso-Dream, Denoised MDP, Sensorimotor WM, Dueling WM: controllable/uncontrollable separation in world models; all assume distractors are action-independent; Dueling WM's appendix names action-tracking distractors as out of scope.

Not found: a suite with typed controllability ground truth, confounded distractors by construction, unannounced body-change events, sequential detection metrics, and both classical and learned baselines. That is the benchmark. The contribution type is benchmark plus findings; the findings that matter are (a) the probe cost of robustness to confounding, (b) which learned separation criteria fail under confounding, and (c) how all methods behave through a boundary change.

## 6. Feasibility on the M5 Air

- T1 and T2 estimator sweeps: hours to a few days total, serialised, with cooldowns. No constraint.
- T2 MuJoCo: the `mujoco` package runs on Apple silicon; step cost is tens of microseconds. No constraint.
- T3: the only heavy tier. State-based inputs and small RSSMs keep runs to 1 to 3 hours each. Sixty runs is a week of nights on the Air or two days on a rented GPU for tens of dollars. Recommend renting for T3 confirmation and keeping the Air for development.

## 7. Deliverable shape

A pip-installable package: environments (T1 generator; T2 wrappers), evaluator with typed ground truth (separate process), metrics, baseline implementations with frozen configurations, a run ledger, and a leaderboard script that reproduces every table from the ledger. A README stating the estimand choices. Released with Paper 1.

## 8. Risks

- Scope: T3 is Paper 2, not Paper 1. Paper 1 ships T1 and T2 with estimators only.
- Ground truth in T2 depends on the wrapper being the only source of confounding; the simulator's own dynamics must not create additional action paths to the distractor channels. This is tested the same way as T1 (invariance under randomised do(a)).
- Adoption is not guaranteed; a benchmark's value is realised only if it is easy to run. The package must install and run a demo in one command.
