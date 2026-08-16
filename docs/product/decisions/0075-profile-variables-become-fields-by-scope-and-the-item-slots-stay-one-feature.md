# PDR-0075 — Unit 3 decided: global and agent profile variables become one observation field each, read by declared scope; the item-slot block stays ONE compiler-emitted feature, and item variables carry no semantic type because none could reach the tensor

Date: 2026-08-17   Status: **accepted** (autonomous, within grant — an authoring-surface
design decision inside WS-4's queue, the class of `PDR-0054`/`PDR-0066`; reported to the owner
at this session's checkpoint. Not a vision, strategy or grant change.)
Author: Claude (standing product owner)
Related: `PDR-0074` (the tag this cut is measured against; the four profile-variable cells),
`PDR-0066` (the semantic-type surface; *a declaration that can reach nothing is removed, not
defaulted*), `PDR-0047` (closed vocabularies; the compiler obeys the author), `PDR-0045`
(name-blind runtime), `PDR-0037` (record-then-bind), `PDR-0019` (one system at a time),
`PDR-0056` (hash movers are measured, not predicted)
Tracker: `hamlet-f0ed709ecf` (unit 3) · follow-up filed for the item-observation question
Register: DIV-006

## Context — the issue's plan hid a fork

`hamlet-f0ed709ecf` says: *one `ObservationField` per exposed profile variable (global, agent,
and per item-slot × item-variable), each carrying the author's declared `semantic_type`.* Global
and agent are straightforward. The item sub-block is not: today it is laid out **per slot ×
(max exposed-variable width across profiles)**, and position *j* inside a slot means "the *j*-th
exposed variable of whichever profile the slotted item has" — positional and profile-dependent.
"One field per item variable" therefore has no meaning under the current layout, and giving it
one means choosing between:

1. **Per (slot, position) fields** — positional, no variable identity, so no per-variable
   `semantic_type` can attach. Fields for the sake of fields.
2. **Per (slot, variable-in-the-union) fields** — name-stable across profiles (dim
   `slot0.freshness` is freshness whether or not the item has it, zero otherwise); each carries
   its variable's declared group. Honest, but it is a **layout redesign** of item observation:
   `total_dims` changes wherever profiles differ, the runtime item path becomes a name-keyed
   gather, and same-named variables across profiles need a compile-time identity rule. That is
   its own system.
3. **Keep the item sub-block as ONE compiler-emitted feature field**, split only global and
   agent. `vfs.md` §4.3 already says a field maps *a variable or a feature*; "the exposed
   variables of the item in each of my slots" is a feature over inventory × item VFS, exactly
   as `obs_affordance_at_position` is a feature over position × affordances.

## The call

**Option 3**, on `PDR-0019`: one system at a time. The item layout question is real and is
filed, not folded (`hamlet-1ad6383186`); this unit does what its title says — the `obs_vfs`
block dies and the runtime stops knowing it by name.

Concretely:

- **Compiler.** For every *exposed* global profile variable: one `ObservationField` named
  after the variable, `scope="global"`, `dims` = the variable's observation width,
  `semantic_type` = **the author's declaration**. Same for agent profile variables with
  `scope="agent"`. If any item profile exposes variables: **one** field `obs_item_slots`,
  `dims` = slots × max profile width (unchanged layout), `semantic_type="custom"` — a
  compiler-assigned member of the closed set, the same rule as every other compiler-emitted
  block (`PDR-0047`). Fields are stable-partitioned by `SEMANTIC_GROUP_ORDER` as today. A
  field name that collides with an environment variable, a meter field, another profile
  variable, or a compiler block is a **compile error** naming both declarations
  (`PDR-0052`: underspecification and ambiguity are compile errors).
- **Authoring surface.** `semantic_type` is **re-added, REQUIRED, typed
  `townlet.vfs.semantic_type.SemanticType`**, on `GlobalVFSVariableConfig` and
  `AgentVFSVariableConfig`; `bars` is reserved to meters (compile error, DIV-005's rule).
  **Item variable configs do NOT get it** — under option 3 an item variable's declaration
  could reach nothing, and `PDR-0066` says a declaration that can reach nothing is removed,
  not defaulted. This asymmetry is stated in the schema doc rather than hidden.
- **Runtime.** `_build_observation_field_from_vfs` reads every field the same way: look up the
  compiled VFS mirror field, read its `source_variable` from the registry **by the variable's
  declared scope** — `global` → `get_global` broadcast to the batch, `agent` → `get_agent` —
  then apply the declared normalization (none for profile variables today; the mirror carries
  `None`). The `field_name != "obs_vfs"` branch is deleted. `obs_item_slots` is published each
  tick by a sync step like the other primitives (grid, temporal, affordance) into its
  engine-written registry variable, then read by the same generic path. The one remaining
  reference to the item feature's name is a single shared constant defined in the compiler
  module and imported by the encoder — one definition, not two literals — and it is the same
  shape as the sibling primitives' syncs, which the issue names as the follow-on unit.
- **`build_vfs_variables`** skips fields backed by profile variables exactly as it skips fields
  backed by `environment.yaml` variables today, so no duplicate primitive is minted for them.

## Register — DIV-006, hash-only, bound on the four profile-variable cells only

Predicted movers (to be **measured** at the cut against a worktree at the pre-cut commit,
`PDR-0056`): `observation_schema_hash` (fields change), `variable_schema_hash` (the `obs_vfs`
primitive variable disappears; `obs_item_slots` appears where items are exposed), `vfs_hash`
(derived from both). **`environment_hash` is predicted NOT to move** — `environment.yaml` is
untouched by this cut; if it moves, the prediction was wrong and the entry says so. Streams
byte-identical: `total_dims` is unchanged by construction and every value lands at the same
offset. The sixteen non-profile cells must stay `AGREE` with no declaration.

## What this deliberately leaves

- The item-observation layout (option 2) — filed as its own unit, with the design question
  stated: *should an agent's view of a slotted item be name-stable across profiles?*
- The sibling primitive name-syncs (`obs_grid_encoding`, `obs_temporal`, `obs_affordance_*`,
  `obs_effects`, now `obs_item_slots`) — the issue's "note them; same shape". The general fix
  is a typed feature discriminator on the compiled field; separate unit.
- `exposed_to` defaulting to `["agent"]` when empty in the three profile validators — a hidden
  default (No-Defaults Principle). Noted for WS-4; not this cut.

## Reversal trigger

- If a real pack wants a per-item-variable semantic group before the item-layout unit lands,
  option 3 was the wrong economy; take option 2 then, against DIV-006's successor.
- If measured movers differ from the prediction above in either direction, do not widen the
  declaration to fit — find out why first (`PDR-0056`'s standing rule).
- If any non-profile cell stops reading `AGREE`, the cut leaked past its declared surface;
  stop and diagnose before the register entry goes `built`.
