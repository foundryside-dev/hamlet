# PDR-0118 — The architecture corpus is archived wholesale; a lean five-document HLD replaces it (Strata/UAC/BAC trio)

Date: 2026-08-24   Status: **accepted** (owner-directed — John specified the shape,
the archive sweep, and the authoring process)
Author: Claude (standing product owner), decision by John
Related: `PDR-0117` (filename decision the new docs must carry), the 2026-08-24 VFS
audit, `hamlet-7a52a63e0b` (replace stale architecture docs — this is its execution
shape)
Owner framing, recorded: the last few weeks were "getting back on top of things enough
to reset the architecture and salvage what we can — which to my surprise turned out to
be everything." This HLD is the reset artifact.

## Context

`docs/architecture/` was ~16 top-level docs plus `hld/`, most design-era (2025-11) with
false "Approved for Implementation" status lines; CLAUDE.md already forbade citing them
as record. Getting on top of the corpus "would blow your context just trying" (John).
The 2026-08-24 UAC rewrite established the conceptual reset: three major compiled
subsystems — **Strata** (space) / **UAC** (world rules, ABI = VFS) / **BAC** (brain) —
with UAC promoted from its old "strata + world config" meaning.

## The calls

1. **Archive everything**: all prior `docs/architecture/` content (including the hld/
   tree, reviews, and `docs/UNIVERSE-COMPILER.md`) moves to
   `docs/architecture/archive/`. Archived docs are historical record; internal relative
   links may dangle — accepted.
2. **Five documents replace it**: `HLD.md` (over the top; carries the Strata section —
   Strata gets no standalone doc, per the owner's five-doc count), `VFS.md` (the
   existing `vfs.md` promoted as-is — "it's pretty good", audit-verified), `UAC.md`,
   `BAC.md` (honest: design target, zero code footprint, `brain.yaml` is the realized
   slice), `COMPILER.md`.
3. **Authoring process**: an Opus tech-writer agent cherry-picks the five docs from the
   archive + current sources; a Fable-tier review agent then fixes/brings them to spec
   (owner-specified two-pass process).
4. **Reference updates owed** (the change list): `CLAUDE.md` trusted-docs list and
   compiler/VFS paths; `README.md` lines referencing `docs/architecture/*` (~487,
   605-608); `docs/oracle/` or plan docs citing `vfs.md`/`UNIVERSE-COMPILER.md` paths.
   These land with or immediately after the Fable pass.

## Reversal trigger

If the five-doc set proves too coarse (a subsystem doc repeatedly grows past ~500 lines
of genuinely load-bearing content), split that doc — never resurrect the archived
corpus in place.
