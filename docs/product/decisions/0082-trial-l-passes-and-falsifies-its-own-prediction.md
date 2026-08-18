# PDR-0082 — Trial L runs first, PASSES, and falsifies its own pre-registered prediction: the north-star has its first reading

Date: 2026-08-18   Status: **accepted** (owner chose the session's bet item — "Run Trial L",
option 1 of the resume brief's proposals, at the same session's grant re-confirmation; the
verdict itself is the protocol's, not a judgment call)
Author: Claude (standing product owner)
Owner sign-off: **yes** on the bet item; the trial executed under the ACTIVE protocol
autonomously within grant

Related: `PDR-0077` (the bet), `PDR-0078` (the bar governs the metric), `PDR-0079` (the miss
taxonomy — L was drawn expecting to be its first live test and was not), `PDR-0080` (the corpus),
`PDR-0081` (the protocol this trial is the first execution of), `PDR-0047` (falsified
predictions are stated, not smoothed)
Tracker: `hamlet-5fa1f7bfc0` (comment 162); by-catch filed `hamlet-d45331a367`,
`hamlet-6b24c0bd83` (both routed WS-4, label `prd-0001-trial`)
Artifacts: trial record `docs/product/trials/0001/L-20260818.md` (pin `fb8c6148`, executor the
standing agent, not blind); pack `configs/trial_l_cooldown/` (+ probe); commit `484976d3`,
pushed per `PDR-0046`. Full suite green 3281/16/0 before the commit (protocol §10).

## Context

The instrument became whole at the twenty-eighth checkpoint (`PDR-0081`). Trial L (cooldown
management, owner-supplied idea) was the designated first draw — the highest-information trial
because its pre-registered prediction was the corpus's only INERT call, making it the first live
test of the ABSENT/INERT distinction.

## What the trial established

**Headline PASS on all four pre-committed facets, both legs** (zero `src/townlet/` diff; every
declared behavior observed at runtime): per-affordance per-agent timers, +1/tick advance,
reset-on-use, elapsed-time gating (`if target.bar.since_X >= K` — nothing spends the timer), and
policy-visible observation fields at the compiled offsets.

**The prediction (PARTIAL, landing INERT) is falsified.** Two nuances recorded, not smoothed:
the trial *did* hit a live INERT surface first (`recovery.natural` — required in every pack by
no-defaults, consumed by zero runtime sites), but a second declared surface
(`depletion.passive: -1.0`) expresses the same facet, so the idea passes; and the predicted
collision with `hamlet-dc8f887cd5`'s zero-writer fields never occurred because a fresh pack has
no reason to touch those declarations. Lesson for the remaining eight predictions: they were
made against the *first surface an author would reach for*, not against the space of declared
surfaces — expect further misses in the optimistic direction as well as the pessimistic.

**North-star state after this trial: 1 of 1 run (denominator 9, no voids), 0 ABSENT / 0 INERT /
0 BLOCKED misses.** The INERT escalation counter (threshold 3) stands at 0 — by-catch INERT
findings are filed as defects but do not count ideas.

## Rationale for accepting the verdict

The protocol was followed to the letter on its first outing: preflight pasted, facets and
evidence pre-committed before authoring, the one mid-authoring discovery appended as a dated
note (the timer's storage-in-meter nuance), stopping rule not needed (all facets settled inside
one session), gaps filed rather than fixed, guardrails run before the commit. No
protocol-ambiguity of the kind `PDR-0081`'s reversal triggers watch for arose: the one loud
error (stale copied `.compiled` cache) was unambiguously a pack mistake, named as such by the
error text itself.

## Reversal trigger

- This PDR records an executed measurement; the *instrument's* reversal triggers live in
  `PDR-0081` and none fired: 0 budget-limited records in 1 trial, no blind re-run yet, no
  ambiguous BLOCKED call. If a future blind re-run of **L** disagrees with this record, the
  verdict is not defended — the instrument is rejected per `PDR-0081` and this reading is
  withdrawn with it.
- If the pack disposition (promote to fixture or delete) is still OUTSTANDING on 2026-10-06,
  the `Pre-release hygiene` guardrail is breached and the bet's acceptance is rejected
  (PRD-0001 criterion 7).
