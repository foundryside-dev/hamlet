# PDR-0066 — the vocabulary is defined once, the declaration reaches the field where a field exists, and a declaration that can reach nothing is removed rather than defaulted

Date: 2026-08-16   Status: **accepted** (autonomous within the grant; executes the owner's
`PDR-0047` ruling — the one judgment call inside it, on the profile-variable surfaces, is stated
below and flagged for the owner's review at this checkpoint)
Author: Claude (standing product owner)
Owner sign-off: `PDR-0047` is owner-made and this PDR does not widen it. The owner chose this unit
at the 2026-08-16 resume (*"lets do 1 now"*) and pointed at `docs/architecture/VFS.md` as the
VFS north star mid-unit; that pointer is what settled the profile-variable call (§Rationale).

Related: `PDR-0047` (closed vocabularies, the declaration is authoritative, the compiler emits from
the same set), `PDR-0045` (name-blind), `PDR-0016` (do not silently add a grammar kind), `PDR-0037`
(record-then-bind), `PDR-0041` (the worked example of a knockdown), `PDR-0056` (what DIV-004's
hash-only shape costs), `PDR-0064` (a parameter the object cannot function without is required)
Tracker: `hamlet-2fe1c34ebb` (`semantic_type`, closed), `hamlet-45b35cfee5` (`interaction_type`,
closed), `hamlet-f0ed709ecf` (filed — the `obs_vfs` split this unit deliberately did not take),
`hamlet-7a52a63e0b` (WS-5, two doc gaps routed)
Register: `DIV-005` (`built`)
Evidence: 27 new tests (`test_observation_semantic_types.py`, `test_interaction_type_vocabulary.py`),
RED on the pre-cut tree by construction; matrix run `20260816-225750`, 16/16
`DIVERGED_AS_REGISTERED`, exit 0, mover set exactly DIV-004's four; pre-cut-vs-live measurement on
all five levels: only `environment_hash` moves, layout/mirror/`total_dims` identical; six gates
green (see the checkpoint's `metrics.md` reading for the full-suite count)

## Context

`PDR-0047` ruled the direction — the author picks from a closed, pre-approved vocabulary; the
declaration is authoritative; the compiler emits only from the same set — and left the unit to be
designed. Recon at the resume measured what the ruling had to land on:

- **`semantic_type` has exactly one live consumer**: the compiled `ObservationSpec` field. It is in
  the field's UUID payload, mirrored into the VFS field that feeds `observation_schema_hash`, and it
  names the field's slice in `group_slices` — which the structured encoders group by, which sizes
  the meter encoder, and into which the runtime publishes meter columns (`bars`).
- **Five schema classes declared it and none reached that consumer.** `VariableDef` (a state
  variable), the VFS `ObservationField` (compiler-authored mirror), and the three
  `vfs_profiles.yaml` variable classes — whose variables are flattened into ONE `obs_vfs` field
  carrying one value. `CompiledVariable.semantic_type` was serialized and read by nobody.
- **The compiler hardcoded a literal per block**, including `"effects"`, which no schema permitted;
  the DTO field was `str | None`, so nothing caught it. The VFS mirror silently remapped
  `effects → custom`, so `obs_effects` carried **two values on one field** (spec: `effects`; hash:
  `custom`). Verified at the oracle tag on `configs/test/effects_smoke`.
- **`environment.yaml` `variables[]` had no `semantic_type` at all** — the compiler wrote `custom`
  for them — and it is the one authoring surface that maps 1:1 to a compiled field today.
- **`interaction_type`** (the sibling, same shape): the authoring DTO permitted
  `instant | multi_tick | dual` with `default=None` and a description that *said* "defaults to
  'instant' at runtime"; `environment/affordance_config.py` also admitted `continuous`, which the
  VTC rejects and nothing implements — and that module had **zero importers**.

## The call

**Semantic type.**

1. **One vocabulary, one module.** `townlet/vfs/semantic_type.py` defines `SemanticType`
   (`bars, spatial, affordance, effects, temporal, custom`), `SEMANTIC_TYPES`, and the group layout
   order. The compiled DTO is typed **and required** and membership-checked at construction — the
   DTO now constrains the compiler, which `str | None` did not (rule 3, made mechanical). The
   compiler, the VFS mirror, and every declaring schema import it; the mirror's private allow-list
   and remap are deleted, so a field has one value.
2. **`effects` is admitted** (`PDR-0016`: an extension is a decision — this is it, recorded here
   and in DIV-005). It names a real compiled block with its own group slice; folding it into
   `custom` would have destroyed the grouping the structured encoders exist to use.
3. **The declaration reaches the field where a field exists.** `environment.yaml` variables gain
   `semantic_type`, **required, no default**; the compiler emits exactly the declared value; the
   field list is stable-partitioned by the fixed group order so *any* member is legal without
   breaking group contiguity (still asserted). Measured: the partition is the identity on every
   shipped pack. **`bars` is reserved to meters** — an authored variable declaring it is a
   compile-time error naming the rule, where before it would have been a runtime raise at the
   first observation (`Failure loudness`, moved to compile time).
4. **A declaration that can reach nothing is removed, not defaulted.** `VariableDef.semantic_type`
   is deleted (a state variable has no observation grouping — `vfs.md` §4.1/§4.3 draw exactly that
   line: variables are stored state; the observation field owns shape, normalisation, exposure,
   ordering). The three profile-variable classes lose it too, **for now**: their variables are one
   `obs_vfs` field with one value, so a per-variable declaration has no referent; making it required
   would manufacture a declaration the compiler cannot obey — a violation of rule 2 dressed as
   compliance with the No-Defaults Principle. It returns on the observation field when `obs_vfs` is
   split per variable, which is `vfs.md` §8.1's shape and is filed as `hamlet-f0ed709ecf`.
   `CompiledVariable.semantic_type` and its serialization go with it.
5. **Shipped packs declare `custom` on every environment variable** (50 lines across 11 live packs;
   `oracle_fixtures/` untouched, per DIV-004's rule). This is deliberate: a knockdown holds
   behaviour fixed, and re-authoring the demo's semantics is not this unit — see the trigger note.

**Interaction type.** `townlet/config/interaction_type.py` defines `InteractionType`
(`instant, multi_tick, dual`); the DTO field is **required**; both `or "instant"` coalesces (config
validator, `vtc.py`) are gone; the VTC checks membership against the module; the dead module that
named `continuous` is deleted. Every shipped affordance already declared it explicitly, so no pack
moved.

**Order.** `PDR-0037`'s: DIV-005 written and `tag-stamped` from a probe of the oracle worktree
*before* any code changed; predicted movers recorded first; cut; movers measured by DIV-004's method
(pre-cut worktree vs live, five levels + `effects_smoke`) — **the measurement matched the
prediction on every row**; matrix adjudicated; entry marked `built`.

## Rationale

**Why wire `environment.yaml` variables rather than only clean the vocabulary.** Because otherwise
the whole cut is fork (b) — *the compiler derives it structurally and the declared field is
deleted* — which the owner rejected. Rule 2 needs at least one author declaration that the
compiler obeys, and the environment variable is where a declaration maps to a compiled field
today. The stable partition is the price of making all six members legal there; it costs nothing
on shipped layouts (measured), and the runtime already assembles by field order.

**Why delete from the profile classes rather than make them required.** Three reasons, in order
of weight. (i) Rule 2 itself: a required declaration the compiler cannot honour is worse than none —
it reads as authoritative and is inert. (ii) The north star: `vfs.md` puts observation properties on
the observation field, one per variable; the block is the deviation, and the honest fix is to
remove the block, not to decorate it. (iii) `PDR-0047`'s own reversal trigger 2 — *"every pack
writing the same value because there is only one sensible choice"* — would have fired for those
classes exactly, and for a structural reason (one field, one value), not an authoring one.
`config-complete.yaml`'s `is_night → temporal` shows the intent is real; `hamlet-f0ed709ecf` is
where it becomes expressible.

**On `PDR-0047` trigger 2 and the 50 `custom` lines.** Every environment variable in every shipped
pack now writes `custom`. Read literally, that is the trigger's shape. It did **not** fire, and the
reason is recorded so the next reader does not have to re-derive it: the values were chosen to hold
behaviour byte-identical inside a knockdown (`deficit_energy` could honestly be argued `bars`;
`time_since_last_eat` is honestly `temporal` — and the test suite proves the latter compiles and
lands in the temporal group). The measurement is confounded by the knockdown discipline, not by
the field being structural. **The trigger stays armed** for the first pack authored fresh under this
surface: if that author, unconstrained, still writes `custom` everywhere, (b) was right for
environment variables too.

**Why admit `effects` rather than map it.** The alternative — `obs_effects → custom` — is
information-destroying for exactly the consumer the field exists for, and it would have moved the
field's UUID (a change to a shipped provenance surface for no behavioural reason). Admitting it
moves only the mirror on effect-bearing packs (`effects_smoke`: `observation_schema_hash`,
`vfs_hash`), which is the mirror becoming truthful.

## What this cut does NOT claim

- It does not make `semantic_type` authorable on VFS profile variables. That is
  `hamlet-f0ed709ecf`, and it is the larger unit (item slots, global scope, the runtime's
  `obs_vfs` name branch — itself a `PDR-0045` violation, along with the `obs_effects` /
  `obs_temporal` / `obs_affordance_at_position` name branches beside it, all noted there).
- It does not certify the harness against this cut's provenance movement *separately* from
  DIV-004's. The mover set is a subset of DIV-004's declared four, so the standing cells adjudicate
  under the existing binding without widening `hash_fields` — which is precisely the cost
  `PDR-0056` recorded, inherited once more. Behaviour is adjudicated at full strength (every stream
  byte-exact); provenance only as "still exactly the four".
- It does not re-author the demo. Every `custom` is a placeholder for a designer's later choice.

## Reversal trigger

- **Reverse the profile-class deletion if `hamlet-f0ed709ecf` is not taken within the WS-4
  horizon** and an author needs grouping on a profile variable before then. The fallback is not
  "make it required and inert" — it is to split the block for the one scope that author needs.
- **Reverse the `bars` reservation** if a designer presents a legitimate authored variable that must
  join the meter block — that would mean `bars` is a *group* and the runtime's meter sync should
  key on something else (the `obs_meter_` prefix, or a separate reserved member). Two such cases and
  the reservation is the wrong cut.
- **`PDR-0047` trigger 2 remains armed** as stated above, now with a measurement protocol: the
  first fresh pack, not the migrated ones.
- **Reverse admitting `effects`** if a second compiler-only member appears — that is the signal the
  vocabulary is mixing "author's grouping" with "compiler's block kind" and the two should be
  separated, not extended.
