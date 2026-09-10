# Prompt for the final Codex critique before execution

Read, in this order, in `docs/archive/red-team/`: `synthesis.md`, `timing-and-shakedown-value.md`, `stage-0a-contract-draft.md`, and `roadmap-v3.md`. You have already read the earlier files and your own `codex-response/`. Do not edit any existing file. Write output to `docs/archive/red-team/codex-final/`.

`roadmap-v3.md` is the plan we intend to execute. It incorporates your C1 to C20 findings and Daniel's decisions D1 to D7. This is the last review before code is written.

Tasks:

1. **Verify your findings were applied correctly.** For each of C1 to C20, state whether v3 resolves it, partially resolves it, or misapplies it. Be specific about any misapplication.
2. **Attack the Stage 0A contract** (`stage-0a-contract-draft.md`) as the thing that will be built first. Are the three targets (S_t, M_t, P_t) well defined and separable? Is the exogenous action-correlated distractor construction (shared cause driving both the default policy and the distractor) causally sound, and can it be unit-tested as claimed in invariant 5? Is any invariant untestable or vacuous? Is anything missing that would make Paper 1's metrics ill-defined later?
3. **Attack the Paper 1 design** in v3 section 6: primary contrast choice, fractional design, smallest effect of interest, kill and redirect rules, reintroduction controls. Would a hostile reviewer at CoLLAs or an ICLR workshop accept the contribution as stated?
4. **Attack the timings** in v3 section 2 and `timing-and-shakedown-value.md`, given that two coding agents implement and one person reviews. Where is the plan still optimistic, and what is the single most likely cause of a slip?
5. **Attack the execution workflow** in section 11. Where can an agent-produced error pass through undetected?
6. **Phase S.** Confirm or dispute that the shakedown as specified is a genuine, if small, contribution, and that its two-week box is credible.

Deliver: `final-critique.md` (severity-ranked findings, each with claim attacked, evidence, fix; plus attacks that failed), `c1-c20-application-check.md` (table), and `go-no-go.md` (under 300 words: go, go-with-changes, or no-go, and the changes). Verify live sources where you rely on them; mark opinion as opinion. Today is 6 September 2026.
