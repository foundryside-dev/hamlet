# PDR-0020 — `docs/architecture/vfs.md` is design authority; the money-scale diagnosis was wrong and is corrected

Date: 2026-08-12   Status: accepted (with one **escalation** — the money unit — awaiting owner)
Author: Claude (standing product owner)
Owner sign-off: the **pointer** is the owner's: *"docs/architecture/vfs.md — this is probably worthwhile in the VFS review; chapter 9 provides a lot of detail on normalisation and how it should work."* Plus the framing: *"the entire point of VFS is that end users don't need to think too hard about the mechanics under the hood, it's effectively like a 'complex type' that they can trust to be enforced mechanically."*
Related: PDR-0016 (bounds + normalization), PDR-0017 (structure vs scale), PDR-0007 (options not yet enabled)
Tracker: `hamlet-365e996511` (retitled and re-scoped by this PDR)

## Context

Task 3a wired the declared VFS normalization and measured a consequence: with
`money.bounds.max: 999999.0`, a realistic balance of `22.5` enters the observation at
`2.25e-05` beside meters at `5e-01` — a ~22,000× scale gap, with no LayerNorm anywhere
downstream.

I filed that as *"the ceiling is an authoring error; declare a truthful one; it belongs to
curriculum authoring."* That diagnosis was reached from the runtime plus `PDR-0016`, and it
never consulted `docs/architecture/vfs.md`, which is the design authority for VFS. The owner
surfaced the document immediately afterwards. Reading chapter 9 overturns it.

## What the design actually says (measured against the tree)

1. **`range_type` is a declared surface that drives nothing.** Every pack's `environment.yaml`
   declares `range_type` per meter — `normalized` for seven, **`unbounded` for money**.
   `grep -rn "range_type" src/townlet/ --include=*.py` returns **exactly one hit**: the Pydantic
   field definition (`config/environment_config.py:27`). The one declaration that says *money is
   not a bounded fraction* is inert.
2. **The design names the correct normalizer.** `vfs.md:766-772` gives money as
   `clipped_log_scaled` (min 0, max 1000, clip: true). `apply_normalization` already implements
   it. This is a wiring job, not a design question.
3. **The money unit is contradictory across the system.** `vfs.md:739` states money is normalised
   *"where `1.0` approximates `$100`"*, and `frontend/src/utils/formatting.js:26` renders
   `value * 100`. The shipped configs denominate in dollars (EAT 5.0, DOCTOR 20.0, WORK +22.5).
   Under the doc, WORK pays $2250; under the configs, the frontend shows $22.50 as "$2250".

## The call

**Two decisions, one escalation.**

**Accepted — `docs/architecture/` is consulted before shipped behaviour is called wrong.** Much
of what looks like an authoring accident in this codebase is a documented intention that was
never wired. This is now standing practice and is recorded in `current-state.md`.

**Accepted — the money-scale fix routes through `range_type`, not through the ceiling.** The
mechanical rule the design implies: `range_type: normalized` → minmax against declared bounds;
`range_type: unbounded` → the log-scaled family. That drives behaviour from a **declared
surface**, so it does not trip `PDR-0016`'s first reversal trigger — it is the same strangle,
one layer up.

**ESCALATED — the money unit is the owner's call.** Dollars or fractions? It is a curriculum and
presentation decision, it makes config/docs/frontend agree, and it is not decidable in-flight.

## Rationale

The owner's "complex type" framing is what makes the corrected diagnosis obviously right. If an
author declares **intent** (`unbounded`) and trusts VFS to enforce the mechanics, then the system
choosing a bounded normalizer for an unbounded resource is a VFS defect — not an authoring
error to be worked around by picking a friendlier ceiling. My original fix would have improved
the symptom while leaving the declared surface just as dead, which is the exact failure this
whole recovery exists to remove.

Worth recording plainly: **the contradiction was masked by the defect WS-1(e) fixed.** While the
hardcoded `[0,1]` clamp held money at `1.0` forever, the value sat where both unit conventions
could coexist. Fixing the clamp is what made the disagreement observable. That is the fix
working, not a regression — and it also retires the separate *"frontend renders money as
`value*100`"* defect noted during 3a recon: `formatting.js` is faithful to the documented
convention.

## Consequences

- **`hamlet-365e996511` is retitled and re-scoped** from "the ceiling is an authoring error" to
  "`range_type: unbounded` is inert, and the money unit is ambiguous". Its original framing is
  preserved in the comment thread rather than overwritten.
- **Its dependency is now only half right.** Layer 1 (honour `range_type`) is VFS-layer wiring
  and does **not** need the curriculum authored first; layer 3 (the unit) does. Left blocked to
  avoid re-doing the work against an undecided unit, but a future session may split it.
- **This is the second confident diagnosis in two days corrected by a design doc that existed
  the whole time** (the first: the "L0_0 vs L0_5 delirium" contrast, `PDR-0018`). Recorded as
  standing practice, not as a one-off.
- **`PDR-0017`'s structure/scale split is reinforced**, not weakened: tokens would fix
  observation *structure* and would not fix this.

## Reversal trigger

Reopen if **any** of the following:

- **`docs/architecture/vfs.md` turns out to be materially stale** on a question where it is
  treated as binding. It is dated and pre-dates several landed changes; if it is wrong somewhere
  load-bearing, its authority needs qualifying rather than assuming. The HLD-vs-implementation
  divergence map is the instrument for this.
- **Honouring `range_type` requires a branch on a variable name** — same limiting principle as
  `PDR-0014`/`PDR-0016`: presumptively no, and it escalates as a grammar question.
- **The owner resolves the money unit toward fractions.** Then the shipped configs are wrong
  rather than the docs, and the fix is a pack edit plus a `bounds.max` change, not a normalizer
  selection — a materially different piece of work.
