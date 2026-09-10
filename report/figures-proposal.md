# Figures proposal for the technical report (10 September 2026)

The report currently has four tables and no figures. This proposal lists candidate visual aids, what each would show, what it would cost the reader, and a recommendation. It is to be red-teamed before anything is added.

## Candidate 1. Causal diagram of the plant (Section 3.1)

A small directed graph: context u → actions a and u → confounded distractors x; actions a → body b → downstream d; world w and padding with no parents; observations o read every latent plus noise; the confirmatory event drawn as the removal of one a → b edge; the option-C variant drawn as a dashed extra edge u → b. Rendered as inline SVG, one column wide.

What it shows that prose does not: the reader can see in one glance that the confounder's only path to the observations is through x, which is the whole mechanism behind the report's third error (the primary scored b and d, which u never reaches). Every finding in Sections 4.2 and 4.4 refers to this structure.

Cost: about a third of a page. Risk: none of the numbers depend on it, so an error in the diagram would be an error of exposition, not evidence; it must match contract v3.9 §B exactly (block order b, d, w, x; u → x only in the frozen plant; actions delayed by τ).

Recommendation: add.

## Candidate 2. Channel-set diagram for the third error (Section 4.2 or 6)

Two nested sets over the observation channels of one instance: the set the round-6 primary scores (the pre-event support: body and downstream channels) and the set the confounder reaches (the confounded half of the distractors). They are disjoint. The event removes one channel from the first set. A caption states that present and absent streams coincide on the scored set.

What it shows: the error in one picture. It duplicates the message of Candidate 1's dashed edge, so it is only worth adding if Candidate 1 is not.

Recommendation: add only if Candidate 1 is rejected; otherwise fold into Candidate 1's caption.

## Candidate 3. Dot plot of the round-6 primary (Table 3)

For each of the four family-L cells and both arms, a dot for the confounder-present AUC and a dot for the confounder-absent AUC, joined by a line, with the channel-constant control at 0.5 and the static vector below it. The picture would show the interventional arm's present and absent dots coinciding exactly and the comparator's sitting above them.

What it shows beyond Table 3: the identity of present and absent for the probed arm is visible as overlapping points rather than as a repeated number. Marginal, since Table 3 has eight numbers.

Cost: a third of a page plus the need to state the interval estimator, which the contract never fixed; a chart with error bars would have to choose one.

Recommendation: do not add. Table 3 is sufficient and the interval problem is real.

## Candidate 4. Bar chart of round-5 versus round-6 arm scores

Would invite comparison across two different primaries (full-channel in round 5, pre-event support in round 6), which is exactly the comparison the report warns against in Sections 4.3 and 5.

Recommendation: do not add.

## Candidate 5. Timeline of rounds and versions

Table 1 already carries dates, hashes, types and gate counts. A timeline would repeat it with less information.

Recommendation: do not add.

## Candidate 6. Sketch of the round-8 confuser dissociation (Section 4.4)

A 2 × 2 grid: rows = plant (confounder reaches the body / does not), columns = arm (passive / probed), cells = predicted response to a support-preserving confounder change (false loss / blind / invariant / invariant). This is the one sign-fixed prediction and the proposed primary of any future round.

What it shows: the prediction table that all three derivations produced, compressed. It is a table, not a chart, and belongs in Section 4.4 as Table 5 rather than as a figure.

Recommendation: add as a small table, not a figure.

## Summary of the recommendation

Add Candidate 1 (plant diagram, inline SVG) and Candidate 6 (a 2 × 2 prediction table). Do not add charts of the results: the numbers are few, the tables already carry them with their caveats, and a chart would need an interval estimator the contract never fixed.
