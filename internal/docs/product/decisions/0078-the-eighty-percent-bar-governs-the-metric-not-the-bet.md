# PDR-0078 — ≥80% is the standing bar on the north-star, NOT this bet's pass/fail; the bet is accepted on the instrument

Date: 2026-08-17   Status: **accepted** (owner-decided, from three options, before any trial ran)
Author: Claude (standing product owner)
Owner sign-off: **yes**

Related: `PDR-0077` (the bet this amends, same session, before any trial), `PDR-0058` (the
precedent: an exit condition that fires on an *output* rather than the outcome is mis-stated and
gets restated), `PDR-0049` (a defect counts only if it executes)
Tracker: `hamlet-5fa1f7bfc0`

## Context — a conflation I wrote into my own PRD

PRD-0001 as first written made criterion 5 *"the rate reaches ≥80% or the bet is rejected."* That
conflates two different questions: **does the instrument work**, and **does the substrate score
well**. Under that wording a perfectly good instrument reporting honest bad news counts as a failed
bet.

The failure mode is not hypothetical, it is an incentive: if a low reading rejects the bet, the
rational move is to pick an easy corpus — the exact gaming the origin-tracking, source-diversity
and pre-registration rules exist to prevent. The instrument would have been built with a motive to
flatter itself.

This surfaced when the owner's riff expanded the corpus and the agent's own pre-registered
predictions implied a reading far below the bar — i.e. the bet was near-certainly buying a
rejection while the instrument worked perfectly.

## Options

1. **Keep ≥80% as the bet's gate.** Simple, harsh, and rewards a soft corpus.
2. **Standing metric target; bet accepted on the instrument** — criteria 1–4, 6, 7 (corpus frozen,
   predictions pre-registered, verdicts reproducible, both legs enforced, guardrails intact).
3. **Both, split** — instrument acceptance plus a separate floor clause with teeth.

## Call — option 2, with a retained escalation clause

The bet is accepted on the instrument. **≥80% (8 of 9) becomes the standing bar the substrate is
measured against over time**; the first run establishes where it actually stands. A reading below
the bar does **not** reject the bet — the number is the finding, and every gap it names routes to
WS-4. The escalation clause survives but is retargeted by `PDR-0079`.

## Rationale

Timing is the legitimising fact: this was amended **before any trial ran**, which is the only
window in which a pre-committed target can move without it being tuning. After the first trial the
same edit would be indefensible, and this PDR is the record that it was not.

## Reversal trigger

- **If the instrument passes criteria 1–4, 6, 7 and the reading is still not trusted** — i.e. the
  bet is "accepted" but nobody acts on the number — then instrument-acceptance is hollow and the
  gate returns to the reading itself.
- **If the standing bar is ever moved after a trial has run**, that is tuning; the entire reading
  is void and this PDR has failed in its purpose.
