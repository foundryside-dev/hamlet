# PDR-0090 — The substrate is frozen for the duration of the corpus: `spawn_item` is fixed AFTER the nine, not during

Date: 2026-08-19   Status: **accepted** (owner-ruled at this session's resume)
Author: Claude (standing product owner)

Related: `PDR-0087` (Trial B, which filed it), `PDR-0086` (the construct preamble),
`PDR-0080` (the drawn nine), `PDR-0089` (blind re-runs, which the freeze also protects)
Tracker: `hamlet-1b9af9088c` (P1, `triage` — deliberately unworked)

## Context

Trial B filed `hamlet-1b9af9088c` as a P1: `spawn_item` is unreachable end-to-end from config
— coordinates refused at parse by both DTOs, string strategies refused at runtime because the
one production call site never threads `agent_positions`, while the docs call it "fully
implemented and production-ready". The brief carried it as an open question phrased as
*sequencing*: "worth sequencing soon — it unblocks B's re-run story, J's durable-posting facet
and the items-as-world-state family at once."

ORIENT established a fact that changes the question's category. Measured this session:

```
$ git log --oneline fb8c6148..HEAD -- src/townlet/
(empty)
```

**`src/townlet/` has not moved once across the entire corpus.** All twelve intervening commits
are `product:`-prefixed workspace state. File-never-fix held so completely that the readings
share a substrate *de facto*, not merely by convention — the trials are pinned at different
commits but at the same engine.

That makes landing this P1 mid-corpus **the first substrate change during measurement**, and J
— still pending — has a durable-posting facet in the same surface family. Later trials would
then be measured against a better substrate than earlier ones.

## Options

1. **Fix after the corpus.** One frozen substrate for all nine + the re-runs.
2. **Fix now, declare it in the construct preamble.** Land the P1; state that trials 6–9 ran
   against a repaired substrate.
3. **Fix now and re-run B.** Most rigorous, most expensive; B becomes a before/after pair.
4. **Escalate as a metric-construct change** with a full PDR before anything lands.

## The call

**Option 1 — fix after the corpus.** `hamlet-1b9af9088c` stays filed and unworked until the
nine trials and both blind re-runs are complete. The substrate is frozen for the duration of
the measurement.

## Rationale

The north-star's denominator is nine ideas measured against *one* substrate. Repairing the
engine partway converts that into two samples of unequal size against two different artifacts,
and the comparison that matters — which ideas the substrate can express — stops being a single
reading. The cost is a delayed P1 on a pre-release product with zero users; the benefit is a
publishable number. `PDR-0078` already established that a low reading is a finding rather than
a failed bet, so there is no incentive to improve the substrate mid-measurement.

`PDR-0087`'s existing trigger already handles the verdict question — if the wiring lands later
and a re-run turns B's facets, the FAIL stands for that reading and the flip is Trend content,
not a re-scoring. What that trigger did **not** cover is the corpus's *internal comparability*,
which is what this PDR settles.

This also protects `PDR-0089`: blind re-runs execute at their first run's pinned commit
precisely so criterion 3 tests the protocol rather than substrate drift. A frozen substrate
makes that guarantee structural instead of procedural.

**This decision was escalated, not assumed.** The agent had the evidence that made the answer
predictable and took it to the owner anyway, because the choice determines what the headline
number means.

## Scope of the freeze

Applies to **`src/townlet/`** only. Trial packs under `configs/`, the product workspace, docs,
and tests remain freely editable — the leg-(a) claim is a zero-`src/townlet/`-diff claim and
nothing else. Gap filing continues unchanged under file-never-fix; the queue simply grows.

## Reversal trigger

Two conditions reopen this:

1. **A trial is BLOCKED by a defect that makes the remaining trials unrunnable** — not merely
   unable to express their idea, but unable to execute the protocol at all. Then the freeze
   costs more than it buys and the repair is escalated immediately.
2. **The 2026-10-06 date is reached with trials outstanding.** The freeze is bounded by the
   corpus, and the corpus is bounded by that date; it must not become an open-ended excuse to
   leave P1s unworked. If the corpus is not closed by then, the freeze is re-litigated rather
   than silently extended.

Otherwise the freeze lifts when the ninth trial and the second blind re-run are recorded, at
which point `hamlet-1b9af9088c` becomes an ordinary WS-4 sequencing question.
