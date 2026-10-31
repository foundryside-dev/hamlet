# PDR-0093 — The authority grant is re-confirmed unchanged, and its one-day stamp debt is carried rather than fixed

Date: 2026-08-20   Status: **accepted** (the re-confirmation is the owner's)
Author: Claude (standing product owner)

Related: `PDR-0038` (the pattern: stamp corrected only at an approved touch), `PDR-0088`
(the 2026-08-19 stamp correction), `PDR-0046` (push authority on this branch)
Artifacts: `docs/product/vision.md` — authority grant, unchanged

## Context

The grant was surfaced at the `/own-product` resume and the owner re-confirmed it **unchanged**:
same autonomous list, same escalation taxonomy, `PDR-0046` still governing the push. The session
then ran past midnight, so `vision.md`'s `Last reviewed: 2026-08-19` is one day stale by the time
the session closed.

## Options

1. Correct the stamp to 2026-08-20 as a factual correction, citing the `PDR-0038` precedent.
2. Leave it and carry the debt, per the 2026-08-15 rule: the stamp is corrected **only at an
   approved `vision.md` touch**.

## Call

**Option 2.** The stamp stands at 2026-08-19; the debt is recorded here and offered at the next
resume.

## Rationale

The rule exists precisely so that `vision.md` — the file carrying the authority grant — is never
edited on the agent's own initiative, however factual the edit looks. The owner approved a stamp
correction on 2026-08-19 (`PDR-0088`); they did not approve a `vision.md` touch on 2026-08-20. A
one-day-stale review date is a smaller cost than eroding the rule that keeps the grant's file
owner-touched, and this session's whole shape — escalating the K bucket, escalating four protocol
amendments, escalating the Trial F question rather than self-adjudicating — depends on that rule
holding when it is inconvenient.

Note this is the **second** consecutive session to carry the debt into the next day; `PDR-0088`
records the owner explicitly choosing correction over carrying it a third time in the prior chain.

## Reversal trigger

If the debt reaches **three consecutive resumes uncorrected**, stop treating it as a carried debt
and escalate it as its own question: either the review cadence is wrong, or the correction rule
needs a standing exception for a pure date field. Track it in `current-state.md`'s flagged list.
