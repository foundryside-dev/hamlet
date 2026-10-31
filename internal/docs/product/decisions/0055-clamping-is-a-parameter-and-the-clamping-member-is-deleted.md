# PDR-0055 — clamping becomes a parameter, and the member that clamped is deleted

Date: 2026-08-15   Status: **accepted** (the capability was owner-approved; the vocabulary
deletion is my call, made under the owner's standing "clean them all up" directive and reported
to them before the next unit began)
Author: Claude (standing product owner)
Owner sign-off: **yes** on the capability —

> *"1. yes approved"*

— against `hamlet-fba56feca5`, whose body recommended option (2), a `clip` parameter, over a new
member. The **deletion of `clipped_log_scaled` is beyond that option text** and is recorded here
as an autonomous call; it was reported to the owner, who acknowledged it (*"1-3 are all noted"*)
before W2/W3 started.

Implements: `PDR-0054` ruling 3
Related: `PDR-0047` (rule 1 — a member does what its name says), `PDR-0053` (the taxonomy;
parameterized members over member proliferation), `PDR-0016` (grammar extensions are owner-gated)
Tracker: `hamlet-fba56feca5` (closed), `hamlet-1dba1910c0` (closed, `bf0f2fe4`)
Commits: `ecc37241`

## Context

Removing the false `clip` **member** (`hamlet-1dba1910c0`) did not give authors clamping. They
never had it: `minmax` is `(v - min) / (max - min)`, pure affine rescaling, so an author
declaring `clip` on `[0, 1]` and feeding `7.0` got `7.0` back. The removal deleted a lie without
supplying the truth, and that was recorded honestly at the time rather than papered over.

## Options

| | | |
|---|---|---|
| (1) | a `clipped_minmax` **member** | symmetric with the existing `clipped_log_scaled` |
| (2) | a `clip` **parameter** on the range-based kinds | fewer members; the `PDR-0053` precedent |
| (3) | decide clamping is not the framework's job | authors clamp at the source |

## The call — (2), and then one step further

`clip` is a **required** boolean on `minmax` and `log_scaled`, forbidden on the rest. Omitting it
is a compile error, not a silent `false`.

**And `clipped_log_scaled` is deleted, taking the vocabulary from ten kinds to nine.** This is the
part not in the approved option text, and the reasoning is the directive itself: adding `clip` to
`minmax` while leaving a clamping *member* elsewhere would author `PDR-0053` taxonomy **shape #3 —
two members, one behaviour** — by hand, inside the change whose purpose is removing that shape.
`log_scaled` + `clip: true` is exactly what `clipped_log_scaled` did.

`docs/architecture/VFS.md` §9.2 had carried the tell the whole time: its own money example passed
`clip: true` to a kind whose name already implied it. A redundant parameter on a member is the
signature of a member that should have been a parameter.

The gain is not symmetry. It is that a **plain linear clamp** — bound this observation to its
declared range, linearly — had **no member at all** and was therefore unauthorable. It is now
`minmax` + `clip: true`.

## Consequences

1. Nine kinds, each distinct, each doing what its name says.
2. `docs/architecture/VFS.md` and `vfs-current-implementation.md` corrected — both are on
   `CLAUDE.md`'s current-and-trustworthy list, which is exactly what makes a stale entry there
   expensive.
3. Behaviour-preserving by construction: all 85 in-tree declarations migrated to `clip: false`,
   which is what the compiler did before. Verified by the oracle matrix with every trace stream
   byte-identical — not by inspection.

## Reversal trigger

- Reverse to a `clipped_minmax` **member** if a **second** boolean parameter ever appears on
  `minmax`. At two flags the member is a discriminated union in disguise and should be split.
- Reverse the deletion if a use case appears for clamping that is **not** expressible as
  clamp-then-scale — i.e. if clamping needs to compose with a kind in some order other than
  first. That would mean clamping is genuinely a different operation, not a modifier.
