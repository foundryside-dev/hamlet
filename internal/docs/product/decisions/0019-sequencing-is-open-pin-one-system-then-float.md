# PDR-0019 — Work-stream numbering is an inventory, not an order: pin one system, then float

Date: 2026-08-12   Status: accepted
Author: Claude (standing product owner)
Owner sign-off: **yes** — stated directly: *"once we lock in the VFS system, we can pick another system to pin (e.g. migrating the obs to a better system or something else entirely, as long as we're replacing, refactoring and fixing I'm happy for us to float from system to system."*
Related: PDR-0006 (strangler; §2b knockdown units), PDR-0017 (token observations), PDR-0007 (options not yet enabled)
Tracker: milestone `hamlet-1ade187dcc`, streams WS-0…WS-7

## Context

`PDR-0006` established the strangler and, in §2b, that a knockdown unit is *"any slice with a
definable contract at its edge … regardless of whether it maps to one package."* What it did
**not** settle is what governs the order those slices are taken in. In practice the WS-0…WS-7
numbering has been read as a sequence, and the recovery has proceeded down it.

The owner has now said explicitly that it is not one.

## Options considered

1. **Keep WS-N as the running order.** Predictable, and the dependencies encoded in the tracker
   (WS-1 blocks WS-7, etc.) stay meaningful. But it sequences by an artifact of how the
   assessment was written up, not by where the defect density actually is — and the numbering
   was drawn for *analysis*, the same criticism `PDR-0006` §2b already made of SG1–SG8.
2. **Fully open sequencing** — pick anything, any time. Rejected: it permits several systems
   half-pinned at once, which is exactly the state the recovery exists to escape.
3. **One system pinned at a time, next one chosen on the selection criterion** — taken.

## The call

**Option 3.** WS-N numbering is an **inventory**, not a required order. When a system is pinned,
the next is chosen on the strangler's selection criterion — *where does the runtime still know
what the game is?* — rather than by stream number.

Two constraints the owner's framing carries, and they are not optional:

- **One system at a time.** "Pin, then float" — not "float between several".
- **The work must be replacing, refactoring, or fixing.** New capability is not a floating
  destination. This restates `PDR-0007`'s second reversal trigger from the sequencing side.

## Rationale

The value is that it stops a genuinely-better next target losing to a lower stream number.
Observation encoding (`PDR-0017`) is the live example: it sits in WS-4, behind streams whose
only claim to precedence is that they were numbered earlier.

It also matches how the last three units actually went. Task 3a was not "the next item in a
list" — it was chosen because bounds and normalization turned out to be one feature. Recording
this makes explicit a discipline the work has already been following.

**What this does not do** is dissolve real dependencies. WS-1 blocks WS-7 because the oracle
must be correct before it is frozen (`PDR-0006` precondition 2). Floating is about choosing
among *available* systems, not about ignoring the blocking edges the tracker records.

## Consequences

- **`current-state.md` carries the framing** so a future session does not silently revert to
  stream order.
- **The freeze question sharpens rather than softens.** If sequencing is open, "when do we stop
  adding to WS-1" is no longer answerable by "when the list ends" — it needs a deliberate call.
  That escalation stays open.
- **The next unit after WS-1 is a live product decision**, not a lookup. Candidates on the
  criterion today: observation encoding (`hamlet-fa6bb6da4a`), the curriculum packs
  (`hamlet-e979f2ba37`), the nine dead hashes (`hamlet-2dde1015fe`).

## Reversal trigger

Reopen if **any** of the following:

- **Two systems end up part-pinned simultaneously.** The constraint is one at a time; if the
  practice drifts, the numbering was doing useful work and should be restored.
- **A float lands on something that is neither replacing, refactoring nor fixing.** That is
  capability work wearing the strangler's clothes, and it trips `PDR-0007`'s trigger too.
- **A blocking edge is crossed because sequencing "is open".** Floating chooses among available
  systems; it does not license starting a blocked one.
