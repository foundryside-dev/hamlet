# PDR-0088 — The authority grant is re-confirmed unchanged, and the `Last reviewed` stamp is corrected at an approved touch

Date: 2026-08-19   Status: **accepted** (owner-approved in session, BEFORE the edit was made)
Author: Claude (standing product owner)

Related: `PDR-0038` (the precedent: factual correction at an approved touch), `PDR-0046`
(push boundary, read together with the grant), `PDR-0067` (the same correction, 2026-08-16)
Artifacts: `docs/product/vision.md` — authority grant block + amendment log entry

## Context

`/own-product` surfaced the grant for confirmation, as it must. Two facts were in tension:
the grant block read `Last reviewed: 2026-08-16`, while `current-state.md` recorded the owner
re-confirming it unchanged at sessions after that date. Not past the monthly review cadence, so
not a lapse — but a stale stamp that had already been carried as debt twice (2026-08-15,
2026-08-16), each time under the rule the amendment log sets: **the stamp is corrected only at
an approved touch.**

## Options

1. **Confirm and correct the stamp** — treat this confirmation as the approved touch.
2. **Confirm and leave the stamp** — carry the debt a third time, as on 2026-08-16.
3. **Confirm with a scope change** — a genuine vision change, escalating properly.

## The call

**Option 1.** The owner confirmed the grant **unchanged** and explicitly approved the stamp
correction, choosing it over carrying the debt a third time. `vision.md` now reads
`Last reviewed: 2026-08-19`, with an amendment-log entry recording the correction, the
intervening re-confirmations, and that the scope is untouched.

## Rationale

The grant's **scope is identical** — same autonomous list (prioritize, write PRDs, dispatch,
accept against criteria, reprioritize, kill a failing bet), same escalation taxonomy
(vision/strategy/grant change, public release or announcement, feature deprecation, pricing,
data deletion, external parties), and `PDR-0046` still governs the push. Only a review date
moved. That makes this a **factual correction, not a vision change**, exactly as `PDR-0038`
established and `PDR-0067` repeated.

The authority gate was satisfied in the order it demands: the correction was **offered and
approved before the file was touched**, not written and reported afterwards. A stamp that
disagrees with the record is a small defect, but it is the kind that makes a governance
artifact untrustworthy — the whole point of a reviewed grant is that the review date means
something.

## Reversal trigger

If the owner states the grant's scope has changed in any respect — a widened or narrowed
autonomous list, or a changed escalation taxonomy — that is a **vision change** and escalates
under the grant itself; it is recorded as a new PDR with `Status: proposed` and is not written
into `vision.md` until signed off. Separately: if `Last reviewed` falls more than one month
behind the current date, the monthly cadence has lapsed and the grant must be re-confirmed
before the agent acts autonomously on anything non-trivial.
