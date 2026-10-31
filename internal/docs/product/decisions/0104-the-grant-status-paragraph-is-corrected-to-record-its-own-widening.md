# PDR-0104 — The authority grant's Status paragraph is corrected to record its own widening

Date: 2026-08-20   Status: **accepted** (owner-approved in-session at the `/own-product` grant
re-confirmation: *"Confirmed — fix the stale prose"*)
Author: Claude (standing product owner)

Amends: the authority grant's Status paragraph in `vision.md` — **factual correction, no scope
moves**
Follows the pattern of: `PDR-0038` (public-repo URL), `PDR-0088` and the 2026-08-15/16/19 stamp
corrections — *a false claim in the grant block is corrected at the next approved touch, never
silently and never by carrying it indefinitely*
Related: `PDR-0099` and `PDR-0101` (the two scope changes this records), `PDR-0093` (the stamp
debt that the 2026-08-20 touch discharged)

## Context

Found at `/own-product` ORIENT. The authority grant's Status paragraph read:

> Status: **CONFIRMED** by the owner on 2026-08-19, unchanged from the 2026-08-11 grant
> (… ; scope identical every time).

Both emphasised clauses were **false as of the previous day**. `PDR-0099` widened the grant to
cover pushing `project-recovery*`, and `PDR-0101` widened it again to cover merging to `main` —
the **first two scope changes since the grant was granted on 2026-08-11**.

The failure mode is specific and worth naming: at the 2026-08-20 touch the `Last reviewed` stamp
**was** corrected (to 2026-08-20) while this prose was **not**. So the block ended up internally
contradictory in two directions at once — the Status line contradicted the amendment log directly
above it, and contradicted the autonomous list directly below it, which by then already granted
push and merge in plain terms.

This is the same class of defect the project keeps finding elsewhere and has a name for: a
**green gate over a hole**. The grant *looked* confirmed and unchanged; the machinery underneath
had moved twice.

## Options

1. **Correct the prose at this approved touch** — offered at the grant re-confirmation, owner
   approves, `vision.md` is touched once and the amendment log gains a fourth 2026-08-20 entry.
2. Carry it as stamp-style debt, correct at the next approved touch. This is what `PDR-0093` did
   for the stamp one day earlier.
3. Rewrite the Status paragraph wholesale for clarity while in there.

## Decision

**Option 1.** Offered to the owner at the grant re-confirmation alongside option 2, and the owner
chose to fix it rather than carry it a second time — the same choice made at the 2026-08-19
resume when the stamp debt came up for the third time.

Option 3 was **explicitly declined**, and the reason is recorded in the file itself: the first
draft of the correction compressed the enumerated re-confirmation history (2026-08-14, the
08-15 resume, twice on 08-16 with the ordering note, each resume through 08-19) into a single
summary clause. That is a *shortening of the provenance trail*, which is not what the owner
approved — they approved **correcting a false claim**. The enumeration was restored and only the
two false clauses removed. A note in the paragraph now says so explicitly, so a future reader can
see the trail was preserved deliberately rather than surviving by luck.

## Rationale

The grant is the document that gates every other autonomous act. A grant block that misdescribes
its own scope is worse than a stale stamp: a stamp being a day old is a hygiene matter, but a Status
line asserting *"scope identical every time"* directly beneath a list granting two brand-new
powers invites exactly one reading — that the agent widened its own authority and papered over it.
Nothing of the sort happened (both widenings are owner-ruled and PDR'd), which is precisely why
the record must not read as though it might have.

The `PDR-0038` pattern is now well-established and was followed without deviation: **do not touch
`vision.md` unbidden; offer the correction at a re-confirmation; take it only if approved; record
it in the amendment log with its provenance.**

## Reversal trigger

If any future reader — owner or agent — reads the corrected Status paragraph and cannot tell from
it alone (a) that the grant's scope changed on 2026-08-20, (b) that both changes were owner-ruled,
and (c) that the pre-widening re-confirmations were scope-identical, then this correction failed at
the job it was made for and the paragraph is rewritten.

Additionally: if a **third** scope change lands and the Status paragraph is not updated in the same
touch, the "correct at the next approved touch" pattern has stopped working for scope (as distinct
from stamps) and the grant block needs a structural fix — most likely a scope-history table rather
than prose.
