# PDR-0026 — The flagship demonstrator is unfinished intent, not a broken claim; the packs change, not the vision's ambition

Date: 2026-08-13   Status: **accepted** (owner-resolved escalation)
Author: Claude (standing product owner)
Owner statement: *"its one of several 'tech demos' we'll provide at the end, the fact it never
worked was because we 'never finished' - the idea outran the codebase and we pivotd a few times."*
Related: `PDR-0018` (the packs are test infrastructure, not a curriculum), `PDR-0003` (Townlet
Town is the first-class tech demo), `PDR-0007` (options not yet enabled)
Tracker: `hamlet-e979f2ba37` (author the curriculum — now the delivery vehicle for this)

## Context

`vision.md` called the Sims-flavoured survival universe — naming "Low Energy Delirium"
specifically — *"the flagship demonstrator of the substrate: the proof that the thing works."*
Measured 2026-08-12 (`PDR-0018`): **it is not implemented and never was.** `L0_0` and `L0_5`
`drive.yaml` are byte-identical; no shipped level declares a `multiplicative` extrinsic; the
contrast the lesson depends on has never existed. The 2026-08-12 checkpoint escalated: *does
that change the vision, or the packs?*

## The call (the owner's)

**Neither retreats.** The demonstrator claim was always *intent* — the idea outran the codebase
through several pivots, and the project never finished it. Two clarifications land with the
resolution:

1. **The claim is re-tagged, not withdrawn.** The vision's present-tense "is the flagship
   demonstrator … the proof that the thing works" becomes explicit delivery intent. The
   ambition is unchanged; what was wrong was the tense.
2. **Townlet Town is one of several tech demos to be provided at the end.** The demonstrator
   plan is a *suite*, not a single artefact. The obvious members already on the board: Townlet
   Town with the LED contrast actually authored, the "Sims in six dimensions" substrate witness
   (Trial 001, already passed), and the still-wanted domain-varying witness. This does not
   demote Townlet Town's *first-class* status among them (`PDR-0003` stands, dogfooding rule
   and both claims untouched).

## Consequences

- **`vision.md` is amended** (owner-resolved escalation; amendment log cites this PDR): a
  status paragraph under the tech-demo section marks the demonstrator role as delivery intent
  and records "one of several tech demos."
- **The gap is unfinished work with a vehicle**: `hamlet-e979f2ba37` (author the curriculum,
  WS-4, downstream of the oracle freeze) is where LED gets implemented for the first time.
  It inherits a sharper acceptance shape from this PDR: the LED contrast (multiplicative
  extrinsic on one level, `constant_base_with_shaped_bonus` on the next) must be expressible
  and demonstrable.
- **Documentation-truth guardrail**: the vision's claim is corrected at source rather than
  standing as a counted false claim. The row's principle survives intact — this was the *docs
  lie about the code* class, resolved by fixing the doc's tense rather than the code, because
  the doc was recording intent.
- **Roadmap gains a Later intent at next checkpoint**: *the tech-demo suite at release* —
  what "we'll provide at the end" means concretely. Intent only; anything distributable is
  outward-facing and gates to the owner (same boundary as `PDR-0025`'s locked showcase).

## Rationale for recording this as a decision

The escalation offered two doors (vision changes / packs change) and the owner opened a third:
the claim was mis-tensed, not mis-aimed. That reading matters durably because it sets the
precedent for the *"code ignores the docs"* class `metrics.md` now tracks — when an ENDORSED
document describes something that does not exist, the question is whether it is a false claim
or an unbuilt intention, and only the owner can say which. Here it is intention, and the fix is
to say so in the document.

## Reversal trigger

Reopen if **any** of the following:

- **Authoring the LED contrast turns out to require Python** when `hamlet-e979f2ba37` is
  attempted. Then the flagship demo is an authorability *counterexample* — a far more serious
  finding than a missing pack, and one that would put the central thesis in question exactly
  where the vision stakes it.
- **The tech-demo suite is descoped at release** to fewer than two members. "One of several"
  was load-bearing in the owner's resolution; a suite of one collapses back into the single
  fragile flagship this PDR was supposed to dissolve.
- **`PDR-0003`'s two-claims tension resurfaces**: if the suite's members start getting
  special-cased to look impressive, obligation A (dogfooding) is being traded away and the
  demonstrator plan is buying claim 1 with claim 2 again.
