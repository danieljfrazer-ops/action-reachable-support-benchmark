# Precursor transcripts: assumptions the roadmap inherits

The archive holds two chat transcripts that preceded the roadmap:

- `../could the newly created_born human brain work som....md` (predictive processing analogy between infant brain and LLM)
- `../couldnt these differences be closed_ how could AI....md` (how to close four gaps: continual weight updates, priors, constant input streams, interoception)

The roadmap explicitly rejects their conclusion (consciousness as an experimental outcome) and correctly reframes the work. But several claims in the transcripts are wrong or overstated, and the roadmap's vocabulary and candidate list descend from them. Listing them so they can be disowned in the preregistration rather than silently carried.

| Transcript claim | Problem | Roadmap exposure |
|---|---|---|
| "LLMs are essentially initialized as blank slates with randomized weights" versus evolutionary priors in infants | Architecture (attention, tokenisation, positional encoding, depth) is a strong inductive prior; the contrast is between kinds of prior, not prior versus none. | Low. Roadmap does not repeat it. |
| "A human can learn what a cat is from seeing three cats, while an AI might need three million images" | Outdated; few-shot and in-context learning are standard. | Low. |
| EWC "identifies critical parameters and stiffens them, allowing the model to update other weights on the fly" | EWC is a task-boundary regulariser and is known to fail under long task sequences and task-free streams; it is not an on-the-fly update mechanism. | Medium. R1 lists EWC/SI as a "persistent updates" baseline; note that it needs task boundaries the stream does not provide, and choose a task-free variant or say why EWC is expected to fail. |
| Continuous multimodal streams "forcing it to predict the next millisecond of video/audio, just like predictive processing in the brain" | Predictive-coding analogy is contested and the timescale claim is decorative. | Low. |
| "System telemetry as sensory data" plus "homeostatic reward functions" leads to "a predictive model of itself", which "is the exact mechanism neuroscientists believe gave rise to biological consciousness" | Large overclaim. Neither the identity between telemetry and interoception nor the mechanism-of-consciousness claim is established. | Medium. R4 ("viability-aware plasticity") and the candidate "allostatic failure forecasting" are direct descendants. The roadmap's own note ("do not claim that an energy variable creates interoception or consciousness") is right; it should be a hard rule in every stage's write-up, not a sentence in R4. |
| Neuromorphic hardware (Loihi) as the route to biological priors | Off-path for a laptop programme. | None; roadmap drops it. |
| "Self-awareness emerges as a byproduct of a sufficiently advanced predictor" (emergentist view) | Stated as one hypothesis, treated as motivation. | Medium. The word "self" runs through R2, R3, R4 and the umbrella name. A hostile reviewer will read the programme as consciousness research in disguise. Keep "self" out of paper titles and abstracts; use "controllability", "boundary", "resource state." |

## Recommendation

Add a short "Motivation versus claims" section to the preregistration for each paper:

- Motivation may cite predictive processing, interoception, and self-modeling.
- Claims are restricted to the measured constructs: retention/adaptation frontier (R1), boundary-estimate calibration under change (R2), adaptation latency under modular timescales (R3), scheduling quality under causal cost (R4, R5).
- No result will be described as evidence for or against consciousness, self-awareness, or phenomenal experience.
