# PDR-0120 — The VFS audit is adjudicated: the wobble is concentrated in doors, and the epistemic-access unit is shaped

Date: 2026-08-24   Status: **accepted** (within grant — commissioning, adjudicating, and
shaping intent; the owner asked for the eval: "I want to understand the gaps")
Author: Claude (standing product owner)
Related: `PDR-0114` (unit-3 cut closes two of the audit's top gaps), `PDR-0117` (the
declaration-store unit closes a third), `PDR-0045` (declare-don't-hardcode)
Audit record: `docs/architecture/archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md`
(two independent line-level auditors, ~70 claims, file:line evidence)
Tracker: 6 new tickets — compiler-hardcoded access control (P1), sparse-pair
unreachable, modulation runtime-crash, social-residue 8/11 modes, dead
`VariableDef.normalization`, vfs-current-implementation.md doc-drift; comment 245 on
`hamlet-fa6bb6da4a`

## Context

The owner assessed VFS/UAC as "mostly done, a bit wobbly in places" and asked for a
spec-vs-implementation eval. Two independent auditors verified ~48 claims IMPLEMENTED,
16 DIVERGED, 1 MISSING, 4 DOC-DRIFT. Nothing was absent — every diverged claim is real
machinery behind a broken or nonexistent authoring door.

## The calls

1. **The audit is accepted as the wobble map.** Headline adopted: the systemic gap is
   one story — declared epistemic state has no working door (authoring: no
   `readable_by`/`writable_by` fields, `exposed_to` fails open; runtime: observation
   path bypasses the checked accessor, only `"engine"` roles ever passed; escape
   hatch: `variables_reference.yaml` invisible to the symbol table). `lifetime`
   hardcoding is the same pattern. Fail-at-runtime seams and dead surface are
   secondary.
2. **Unit 3's cut already closes two top gaps** (explicit exposure required;
   normalization-at-exposure required) — confirmed, no scope change.
3. **An epistemic-access unit is SHAPED into Next (intent, not scheduled)**: the static
   doors (authoring fields on the required surfaces, fail-closed exposure, the
   `get_agent` bypass, symbol-table unification `hamlet-33e520cebd`), designed with
   awareness of the owner's declared-propagation proposal (the dynamic counterpart) so
   the two land as one coherent epistemic design. Sequenced after the token cut.

## Reversal trigger

If unit 4's token-side work shows the exposure/normalization fixes in the cut do NOT
compose with per-token access gating (i.e. the epistemic unit would need to redo the
cut's exposure surface), the epistemic unit's sequencing moves UP — designed before
further token units rather than after.
