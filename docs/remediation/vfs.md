# VFS — gap analysis and remediation plan

Scope: `src/townlet/vfs/` (schema, registry, vtc, evaluator, profiles, transition_schedule,
schema_hashes), `universe/compilers/vfs.py`, `universe/validation/static_access.py`,
`environment/token_publishers.py`, and the VTC call sites in `environment/vectorized_env.py`.
Evidence: `review-2026-10-24/findings_vfs.md`, scripts `review-2026-10-24/vfs/probe1-6.py`.

## What the subsystem promises

README and `docs/config-schemas/variables.md`: one canonical variable roster; every declaration
carries scope, lifetime, initialization, semantic type and exposure; read and write policies are
checked at every access and sealed per runtime instance; action writes, passive dynamics,
cascades and terminal conditions lower into a compiled transition graph that the engine executes
in a fixed phase order; expressions over variables are evaluated each tick.

## What it does

The static-access contract holds. The reviewer tried to break it twelve ways and could not:
policy snapshot immutable and used by publishers, `writable_by: []` enforced, denied writes
refused at compile including inside delayed commands, lifetimes honoured for every scope, the
`ADVANCE` witness writing end to end. Eight of the eighteen backlog bugs in this seam are fixed
and six are obsolete. The Cut B refactor did its job on the declaration surface.

The transition and evaluation machinery behind that surface is where the gaps are. The phase
graph admits fourteen phases and the engine runs ten of them. Action writes decide which axis
is the agent axis by inspecting a tensor's shape. One of the two authored evaluation modes
evaluates against compile-time constants. The compiler accepts writes whose target scope the
runtime cannot apply, and detects a variable-versus-meter name collision only when a write
happens to touch it.

## Gaps

Full defect sites, reproductions and refutations: `review-2026-10-24/findings_vfs.md`
(referenced below as F-numbers) and the filigree ids where a backlog bug is folded in.

| id | sev | gap | source |
|---|---|---|---|
| V1 | P1 | Four graph phases never executed by `step()`; writes there compile green and never apply; five later phases compile green and crash | F1, hamlet-cebe51077a |
| V2 | P1 | Action writes infer the agent axis from `shape[0] == num_agents`; non-agent scopes silently masked or crash by `num_agents` | F2 |
| V3 | P1 | `evaluation_mode: eager` evaluates statics from compile-time literals | F3 |
| V4 | P2 | `extents.num_affordances` required and ignored | F4 |
| V5 | P2 | Variable id equal to a meter name compiles; detected only inside VTC apply | F5 |
| V6 | P2 | `reward_component_program` compiled and hashed, never run; `compile_vtc_bounds_clamps` uncalled | F6 |
| V7 | P2 | Agent-scope expressions cannot read globals, including the clock | F8 |
| V8 | P2 | Bare `vfs.X` write to an agent variable writes the whole batch per interactor | hamlet-b9a3bcbde2 |
| V9 | P2 | `zone` scope: storage, no consumer | hamlet-02bd5a3eaa |
| V10 | P2 | Unreachable registry modes and zero-caller functions; `semantic_type` required and unconsumed for hidden variables | F10 |
| V11 | P3 | Engine/VTC writes coerce dtype where `set()` validates | F7, hamlet-2ca2cb373f residual |
| V12 | P3 | `variable_schema_hash` ignores shape and initializer | F9 |
| V13 | P3 | Random initializers draw once and restore on reset | F11 |
| V14 | P3 | Expressions see `social_residue` writes one tick late | F13 |
| V15 | P3 | Residue: stale docstring, four dead whitelist lines, inert accumulators in `configs/simple`, VFS.md §6 claims | F12 |

## Remediation plan

Ordered. WP1 and WP2 are prerequisites for the strata, effects and items plans, which schedule
writes against the phase graph and the scope rules decided here.

### WP1 — Make the phase graph true (V1, V6, V14)

Decide, once, which phases exist. The engine runs ten; the graph declares fourteen. Two options:

- **Delete the four phantom phases** from `TransitionPhaseGraph.default()` and from every
  compile_vtc_* phase check. `reward_component_program` goes with `compute_rewards` (rewards are
  DAC's; the VTC program has never run). This is the recommended option: it removes dead
  capability and makes "the graph is the schedule" literally true.
- Or make the env run all fourteen, which means giving `apply_modulations`,
  `emit_observation_features` and `emit_telemetry` executors they have never had.

Then make the compiler refuse at compile what the runtime refuses at step: an action write at a
phase that `run_phases` is called with `actions=None` for. The runtime check at
`transition_schedule.py:133` stays as a guard; the diagnostic belongs in
`compile_vtc_affordance_occupancy_with_phase_graph` with a `file:line` origin.

Fix the one-tick lag (V14) in the same change: either run profile evaluation after the residue
phase, or document the ordering in `variables.md` and leave it. The reviewer's `mas_control`
probe is the acceptance either way.

Verification: `probe6.py` and `probe1.py` D become `tests/test_townlet/unit/vfs/test_phase_graph_truth.py`:
every phase the graph admits must either apply a write or refuse it at compile; no phase may do
neither. Size: M.

### WP2 — Scope-typed action writes (V2, V9)

An action write must carry its target's declared scope and refuse non-agent scopes at compile.
`_validate_action_write_targets` is name-only today; it has the symbol table and can look the
scope up. Delete the `shape[0] == num_agents` heuristic in `_broadcast_agent_mask`; after WP2 the
only targets that reach it are agent-scoped, and the check becomes an assertion.

Then decide `zone`. It is nine lines of storage with no consumer. Delete the scope from
`VariableScope`, the extent from `variables.extents`, and the registry arena, or give it a
publisher and a write path with a declared zone-of-agent mapping. The plan recommends deletion;
the group scope already carries the "per-partition state" idea and has the same gaps, so decide
both together.

Verification: `probe1.py` F and `probe2.py` G. A global tensor target must refuse at compile with
a message naming the scope; `num_agents` must not change whether a pack runs. Size: M.

### WP3 — Delete `eager` (V3)

`EvaluationMode.EAGER` is annotated "(debug mode)" and produces wrong values. Delete the enum
member, the `evaluation_mode` field (it becomes a single-valued required field, which is the
no-defaults antipattern in reverse), the branch at `evaluator.py:184-200`, and the clause in
`variables.md`. Every shipped pack declares `mark_and_sweep`; update them.

Verification: `probe2.py` F `eager_stale` must refuse at parse as an unknown key. Size: S.

### WP4 — Symbol table refuses meter collisions (V5)

Add the meter vocabulary to the symbol table's uniqueness check so a variable id equal to a meter
name refuses at Stage 4 with both origins. Delete the runtime check at `vtc.py:446-449` once the
compiler owns it. Verification: `probe4.py` A refuses at compile; `probe5.py` refuses at compile.
Size: S.

### WP5 — Agent expressions can read globals (V7)

Seed the agent profile schema with every global id as a scalar, the way
`_build_spawn_condition_schema` already does. The clock is the motivating case: an agent-scope
`is_night: day_phase > 0.5` should compile. Verification: `probe2.py` A `expr_agent_reads_global`
compiles and tracks. Size: S.

### WP6 — Delete required-but-inert and unreachable surface (V4, V10)

- `extents.num_affordances`: delete the field and the DTO validator; the level's affordance
  count is the authority.
- `semantic_type`: either consume it for hidden variables or make it required only when
  `exposed_to` is non-empty or the variable is the clock. Deleting the enum's unused members and
  `SEMANTIC_GROUP_ORDER`/`METER_BLOCK_SEMANTIC` is the recommended first cut.
- Registry: delete `pair_storage_mode`, `pair_edges`, `dynamic_variable_mode`, `add_variable`,
  `remove_variable`, `dynamic_variable_mutations`, `variable_schema_generation`,
  `VariableDef.observable`, `materialize_pair_dense` and the four pair-edge accessors. Nothing
  constructs the registry with them and no pack can.
- Delete `evaluate_all`, `run_phase`, `passive_rate_for`, `duration_for`,
  `compile_vtc_bounds_clamps`, `VectorizedHamletEnv._apply_vtc_action_writes`.

Verification: vulture over `vfs/` shows no remaining zero-caller public methods; the test suite
for `test_dynamic_variable_mode.py` and `test_registry_scope_arenas.py` is deleted or rewritten
against the surviving surface. Size: M.

### WP7 — Validate on engine writes (V11, V12, V13)

`set_engine_value` and the VTC commit path should validate dtype the way `set()` does; a float
candidate into a bool target is a compile-time type error once write expressions are type-checked
against the declared type. Add `shape`, `initial_value_mode` and `initial_value` to
`_canonical_variable_entry`. Decide and document random initializers: "drawn once, restored on
reset" is defensible as reset identity, but then rename the modes to say so, or redraw on reset
using the env's seeded generator. Verification: `probe2.py` D and H, `probe4.py` C, `probe1.py`
G. Size: S.

### WP8 — Bare `vfs.X` writes (V8) and residue (V15)

V8 is shared with the effects plan (its context write is `effects/context.py`). Decision: a bare
`vfs.X` write to an agent-scoped variable inside an affordance or agent-scoped effect means the
interacting agent's row, never the batch. Implement by resolving bare `vfs.X` to
`target.vfs.X` when the context has a target index, and refusing at compile when it does not.
Then delete the residue: the docstring at `token_publishers.py:186`, the four whitelist lines,
the two inert accumulators in `configs/simple`, and correct `VFS.md` §6. Size: S.

## Docs to correct in the same changes

- `docs/config-schemas/variables.md`: delete the eager clause (WP3); state the phase set and the
  rule that writes after `apply_completion_bonuses` refuse (WP1); state that agent expressions may
  read globals (WP5); state the random-initializer reset semantics (WP7).
- `docs/architecture/VFS.md` §6: delete the bypass caveat and the `["engine","vtc"]` example;
  `read_item`/`write_item` take roles.

## Round 2 (2026-10-24, after WP1–WP8 landed)

A second first-principles review, `review-2026-10-24/findings_vfs_round2.md` (scripts under
`review-2026-10-24/vfs_round2/`), found 14 implementation findings (5 P1, 8 P2, 1 P3) and 10 spec
problems that WP1–WP8 did not reach. Its work packages continue the numbering here; full
definitions, acceptance scripts and the S1–S10 spec problems are in that file.

| WP | content | closes | size | executed by a shipped level? |
|---|---|---|---|---|
| WP9 | Clock and reset truth: evaluate profiles at the end of `reset()`; `tick`, `day_phase` and `time_of_day` agree in every observation | F1, F2 | S | yes (L3 `day_phase`) |
| WP10 | Profile identity (expression source, type, order, `semantic_type`) into `vfs_hash`; `variables_hash` beside the pack hashes | F5 | S | yes |
| WP12 | Shape-proved writes; refuse writes to expression-owned targets; one spawn schema; token-spec errors located; agent-shaped values into pair targets refused | F6, F7, F11, F12 | M | yes (compile-time) |
| WP11 | One per-slot visibility mask shared by the item and item-state publishers | F3 | S | no (no shipped items) |
| WP13 | Rule S1 (batch = N independent worlds), then per-world `global` axis; refuse `pair`/`message` until agents-per-world is declarable | F4, S1 | M–L | yes (L5 globals) |
| WP14 | History operators admitted as pointwise, collected from both profiles, `lag`-only self-edges; or the pipeline deleted | F9, S9 | M | no |
| WP15 | Scope surface: `agent_private`, `message`, `pair` deleted or given readers and addressing; L5 pack cleaned | F8, F14, S2, S6, S7 | M | partly (L5) |
| WP16 | `persistent`-lifetime registry state checkpointed under the `vfs_hash` gate | F13 | S | yes (L3 `day_phase`) |
| WP17 | Spec text: identity rule gated on brain type; one-spelling resolver; transition-rule `reads`/`kind`/name; expression variables inlined into writes; doc corrections; `temporal.is_night` deleted | S3, S4, S5, S8, S10, F14 | M | yes |

Ordering (approved 2026-10-24): WP9, WP10, WP12 first, with the compiler's remaining WP5–WP7
folded into the same sprint; WP13's ruling before WP15; WP12 before WP14. The "executed by a
shipped level" column orders the work; it does not cut it. VFS is called green when a fresh
first-principles review finds no P1/P2 and no unworkable spec gap.
