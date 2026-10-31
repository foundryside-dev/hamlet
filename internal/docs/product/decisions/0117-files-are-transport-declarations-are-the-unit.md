# PDR-0117 — Files are transport, declarations are the unit: pack filenames stop being mandated

Date: 2026-08-24   Status: **accepted** (owner-directed — John: "lock it in"; above-grant
surface decision made by the human owner, recorded verbatim by the standing agent)
Author: Claude (standing product owner), decision by John
Related: `PDR-0045` (declare-don't-hardcode — same instinct applied to file layout),
the 2026-08-24 VFS audit (`docs/architecture/archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md`)
Tracker: feature to be filed at implementation planning; NOT unit-3 scope

## Context

The pack layout mandates 16 distinct filenames, hardcoded across ~9 compiler modules
(parse/preflight plus error strings). The 2026-08-24 VFS audit showed the sharpest cost:
three separate files declare variables (`environment.yaml`, `vfs_profiles.yaml`,
`variables_reference.yaml`) with divergent hardcoded `lifetime`/access semantics — a
defect class created by the split itself. Filenames carry no information the content
doesn't already carry: No-Defaults + `extra="forbid"` make every declaration
self-identifying.

John's framing: "whatever files are available, we'll compile into a single profile" —
authors get their own domain model (`ship.yaml`, `weather.yaml`, `economy.yaml`, one
file per designer-facing concept spanning our subsystem taxonomy), and proper subfolder
support makes packs compose (mixins, mod-packs).

## The call

1. **Discovery replaces the manifest.** The compiler globs the pack (subfolders
   included), parses every YAML document against the closed typed schemas, and merges
   into one compiled profile. Filenames become authoring convention, never semantics.
2. **"Required file" becomes "required declaration"** — e.g. every level must declare
   exactly one `drive` block; the requirement was always about the declaration.
3. **Override/merge is by declared id, not by file shadowing**, with loud collision
   refusal (compile error naming both declaring files), matching the house fail-loud
   style and the token spec's indistinguishability check.
4. **Determinism preserved**: canonical merge order (sorted paths) so `config_hash`
   stays stable; per-declaration file:line provenance must survive into diagnostics.
5. **Sequencing**: its own unit after the token migration; pairs naturally with the
   variable-surface unification the audit demands (same compiler front-end). Nowhere
   near unit 3's cut.

## Reversal trigger

If discovery-merge measurably degrades compile-error quality (authors cannot tell where
a refused declaration came from) and per-declaration provenance cannot fix it, reinstate
a thin required manifest (pack.yaml index) — not the 16-filename mandate.
