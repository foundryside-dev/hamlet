# PDR-0050 — The authority grant's review stamp is corrected to 2026-08-15, with explicit owner approval; scope unchanged

Date: 2026-08-15   Status: **accepted** (owner-approved in session — a factual correction to
`vision.md`, offered and approved before the edit, never a silent rewrite)
Author: Claude (standing product owner)
Owner sign-off: **yes**, asked directly at the `/own-product` grant re-confirmation and answered
*"Yes — fix the date with an amendment-log entry"*. The grant itself was re-confirmed in the same
exchange as **"Confirmed, unchanged"**.
Related: `PDR-0038` (the precedent: a factual correction offered at a grant re-confirmation and
approved in the same session), `PDR-0046` (the push/merge boundary the restated grant now names)
Tracker: none — workspace bookkeeping

## Context

`vision.md`'s authority-grant block read `Last reviewed: 2026-08-11` while the owner had
re-confirmed the grant verbally on **2026-08-14**. The fifteenth checkpoint recorded the mismatch
and deferred it — *"bookkeeping still owed to `vision.md` (never edited silently); fix at next
approved touch"* — and it then survived a second checkpoint unfixed.

The deferral was correct in principle and was becoming a defect in practice. `vision.md` is
ENDORSED and any change to it escalates, so the agent may not fix even a stale date unilaterally.
But a grant block whose own review date is wrong is the `Documentation truth` failure sitting
inside the document that governs the agent's authority — the most consequential possible place for
it, and the row already recorded (2026-08-14) that its scope was never restricted to engineering
docs.

## The call

**Correct the stamp to `2026-08-15`, with an amendment-log entry, having asked first.**

The ask was bundled into the `/own-product` grant re-confirmation rather than raised separately —
that is exactly the moment the deferral named ("the next approved touch"), and it is the
`PDR-0038` pattern. The owner confirmed the grant unchanged and approved the correction in the
same exchange.

What changed:
- `Last reviewed: 2026-08-11` → `2026-08-15`.
- The `Status:` line now names all three confirmations (2026-08-11 original, 2026-08-14, and the
  2026-08-15 `/own-product` resume) and states the scope was identical each time.
- It now cross-references `PDR-0046` so the push/merge boundary is legible from the grant itself,
  rather than only from a PDR a reader must know to look for.
- An amendment-log entry records it as a factual correction with no section's meaning changed.

**The grant's scope is untouched** — same autonomous list, same escalation taxonomy. That is what
makes this a correction rather than a vision change: a vision change alters what the agent may do;
this altered only the record of when the owner last said so.

## Rationale

The alternative was to keep deferring. Two checkpoints had already shown where that leads: the
note migrates forward, gets shorter each time, and eventually reads as background rather than as
debt. The cost of asking was one bundled question inside a confirmation the command runs anyway.

The general practice worth keeping: **when a document may only be edited with approval, batch the
approval request into the ritual that already touches it.** A correction that needs permission and
has no natural moment to ask will not get asked.

## Reversal trigger

- **Reverse if the owner states the grant was not in force on any of the three dates now claimed
  in the `Status:` line.** The correction asserts continuity of scope across them; if that is
  wrong, the line overstates the mandate and must be narrowed to only the dates actually confirmed.
- **Re-open at the review cadence.** The grant is monthly-or-on-any-vision-change; the next review
  is due **2026-09-15**. If a checkpoint passes that date with the stamp unmoved, this PDR's own
  failure mode has recurred and the fix is a standing agenda item in `/own-product`, not another
  deferral note.
