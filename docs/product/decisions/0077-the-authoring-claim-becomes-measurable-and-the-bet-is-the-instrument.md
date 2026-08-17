# PDR-0077 — the authoring claim becomes measurable: the bet is the INSTRUMENT (a frozen corpus and a repeatable two-leg protocol), not another authoring unit

Date: 2026-08-17   Status: **accepted** (owner-chosen at the 2026-08-17 `/own-product` resume from
four proposed bets; the PRD's shape is autonomous within grant, with five points escalated to the
owner as multiple-choice because each changed what the instrument would mean)
Author: Claude (standing product owner)
Owner sign-off: **yes**, on the bet and on five design points (corpus provenance, N, scoring unit,
threshold, date)

Related: `PDR-0051` (Trial 002 — the two-leg method and the pre-registration discipline this
generalises), `PDR-0047` (predicted its own outcomes and was falsified — the reason predictions are
mandatory), `PDR-0007` ("not yet enabled" ≠ debt), `PDR-0012`/`PDR-0013` (the no-tech-debt
anti-goal), `PDR-0003` (obligations A and B — dogfooding and a second witness), `PDR-0019` (the
strangler's selection criterion, which this bet does NOT use — it is not a knockdown)
Tracker: `hamlet-5fa1f7bfc0` (filed this session, P1, parent milestone `hamlet-1ade187dcc`)
Artifacts: `docs/product/prds/0001-measure-the-authoring-claim.md` (PRD-0001,
`ready-for-planning`), `docs/product/prds/0001-corpus-FROZEN.md`

## Context — twenty-six checkpoints against a proxy

The north-star **Zero-Python authoring rate (world)** has never been readable. Two trials have run
and neither yields a rate: Trial 001 scored a whole idea (`1 of 1`), Trial 002 scored halves
(`3 of 4`), and **no scoring unit was ever defined**, so the two numbers are not comparable to each
other. `metrics.md` says it plainly — *"still not a rate: the corpus is undefined."*

Meanwhile twenty-six checkpoints have landed WS-4 units against the *input* metric
`Config-surface coverage`, and this bet has carried *"tracker: not yet filed"* at the top of Next
throughout. Shipping units against a proxy while the outcome metric stays unreadable is the build
trap in its textbook form. That framing — not a new opportunity — is why this was proposed first at
the resume rather than the cheapest available WS-4 unit.

## Options

1. **Take the cheapest WS-4 unit again** (the `exposed_to` hidden default). Keeps the streak,
   moves no outcome metric, extends the pattern that produced the problem.
2. **Build the instrument** — define the corpus and the protocol, so the north-star becomes a
   number with a denominator. Costs sessions, produces no authoring improvement of its own.
3. **Declare the two existence proofs sufficient.** Cheapest; but `1 of 1` and `3 of 4` cannot be
   combined, and no bet could ever be accepted or rejected on north-star grounds.

## Call — option 2, with the shape owner-decided at five points

The bet is **Next → Now**, running alongside the strangler rather than replacing it. Owner
decisions: corpus is **agent-drafted, owner-riffed** (upgraded from draft-and-veto mid-session —
a veto only subtracts from a pool the agent shaped, a riff can add what the agent failed to think
of, and it did: 7 of 15 ideas are owner-supplied); scoring is **binary headline per idea plus
facet detail underneath**, which fixes the incomparability directly; the standing bar is
**≥80%** by **2026-10-06**.

## Rationale

The instrument is worth more than any single unit it displaces because it is what lets every
*later* unit be judged. Its own acceptance is deliberately separated from the number it produces
(`PDR-0078`), and its failure taxonomy is what keeps a low reading from being misread
(`PDR-0079`).

## Reversal trigger

- **If the first reading cannot be produced by 2026-10-06**, the bet is rejected and the
  instrument is abandoned or rebuilt — a measurement apparatus that outruns its own window is
  worse than none, because it consumes the sessions the units would have used.
- **If two consecutive trials are voided** on criterion 1 or 2 (unfrozen corpus, missing
  prediction), the protocol is unusable as written and returns to design.
- **If `Gates green` or `Pre-release hygiene` degrade** because of trial packs, the bet stops
  until the guardrail is restored — the measurement does not get to damage what it measures.
