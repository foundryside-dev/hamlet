# PDR-0123 — 9.0× measured at design time: the 8× cap is not moved, and its measurement is brought forward to the cut's adjudication

Date: 2026-08-25   Status: **accepted** (within grant: it tightens a trigger's
evaluation, never loosens the trigger)
Author: Claude (standing product owner)
Related: `PDR-0114` (trigger 3), `PDR-0033` (narrowness), unit-3 plan Task 6/Task 11
Evidence: Task 6 report's L1 worked width table (seed commit `ab5897e4`, table
re-verified by review)

## Context

Task 6's TokenSpec derivations, run against the real compiled L1, measure
`total_dims = 1080` — **9.0×** the pre-cut allocated 120. `PDR-0114` trigger 3 reads:
"a shipped pack's serialization exceeds 8× its pre-cut allocated width
(post-disposition, post-explicit-exposure)" — evaluated at unit 5. 86% of the width is
the affordance type (14 × 66): the K=4 effect summary carries an 8-wide target-meter
signature per entry (review confirmed this is the spec's literal reading, not an
over-reading), and absolute + egocentric positions are each rank-8 padded (18 dims on a
2D grid, the cross-substrate layout contract).

## Options

1. Raise the cap to fit the measurement.
2. Tune the constants now (narrower signature, K=3, tighter padding) to duck under 8×.
3. Keep the cap and the constants; bring the trigger's measurement forward.

## The call

Option 3. The cap stays 8×. Constants stay as specced (single definitions,
`encoding_version`-carried). **Task 11 must re-measure `total_dims` on the actual
compiled post-cut artifact and, if ≥8×, treat trigger 3 as FIRED at that checkpoint** —
reopening `PDR-0114` there, not at unit 5. The design levers to drill with data at that
point: signature variance across L1's meters, position-padding policy, K.

## Rationale

Moving a reversal trigger to fit the first measurement is the anti-pattern triggers
exist to prevent. Tuning constants pre-wiring would be redesigning the spec without the
variance data the compiled artifact provides for free at Task 11. A known-exceeded
trigger left un-evaluated until unit 5 is a quietly-deferred signal; naming the
checkpoint where it must be confronted keeps it honest. Pre-release, a later constant
change costs one ABI re-hash.

## Reversal trigger

If Task 11's re-measurement lands ≥8× and the drilled levers cannot bring it under
while preserving the spec's identity-by-declared-parameters property, `PDR-0114` is
reopened for an explicit owner decision on the cap itself — the cap is never silently
edited.
