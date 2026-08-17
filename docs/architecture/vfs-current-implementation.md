# VFS Current Implementation

**Document Type**: Implementation Overview
**Status**: Current
**Version**: 1.0
**Last Updated**: 2026-08-17 (profile variables as fields, `PDR-0075`; feature discriminator, WS-4 unit 4 `hamlet-39e1fe3c6d`; semantic-type vocabulary 2026-08-16, `PDR-0066`; earlier body verified 2026-05-16)
**Owner**: Townlet engineering
**Audience**: Engineers and researchers working on Universe as Code, Brain as Code, environment dynamics, observations, or training reproducibility
**Technical Level**: Deep Technical

---

## Summary

The Variable & Feature System (VFS) is the typed, hashable runtime contract between Universe as Code and Brain as Code. It describes which state exists, who can read or write it, how it becomes observations, how declared world rules compile into tensor transitions, and how those contracts are bound into compiled universes and checkpoints.

VFS is not only an observation helper. In the current implementation it is a combined:

- State schema for global, agent, item, pair, group, affordance, zone, and message variables.
- Runtime tensor registry with scope-aware storage and access control.
- Observation ABI builder for fixed observation dimensions, active masks, item slots, and variable-token fields.
- Expression/profile compiler for derived global, agent, and item variables.
- VFS Transition Compiler (VTC) for declarative action writes, passive dynamics, terminal rules, reward components, affordance gates, interaction progress, threshold cascades, modulations, and social residue rules.
- Provenance layer that hashes variable, observation, action, and transition schemas into one `vfs_hash`.
- Research scaffold for dynamic needs and held-out generalisation over causal structure rather than label memorisation.

The core idea is simple: if a world property can affect an agent, be observed by an agent, be written by an action, be used in reward/terminal logic, or be needed for reproducibility, it should be represented as a typed VFS contract rather than as hidden imperative state.

## Why VFS Exists

Townlet is built around a separation of concerns:

```text
Universe as Code
  declares worlds, meters, affordances, items, rules, transitions, rewards
        |
        v
VFS
  declares typed state, feature exposure, access control, observation shape,
  transition effects, provenance hashes, and runtime tensor storage
        |
        v
Brain as Code
  declares agent networks that consume the observation ABI and choose actions
```

Without VFS, the environment has three recurring failure modes:

1. Hidden state changes: environment code mutates meters, affordances, items, or terminal state in code paths the config cannot see.
2. Observation drift: a config change silently changes observation dimensions or ordering, invalidating existing networks and checkpoints.
3. Poor transfer tests: agents can learn labels such as `hunger` or `shop` instead of learning the underlying causal structure of needs and affordances.

VFS addresses those failure modes by making state and features explicit, typed, access-controlled, compiled, and hashed.

## What Makes This Implementation Distinctive

### VFS Is An ABI, Not A Convenience Layer

Most codebases treat observations as an array built near the environment boundary. Townlet's VFS treats observations, actions, world state, and transition rules as one ABI. The same compiled universe carries:

- `vfs_variables`
- `vfs_observation_fields`
- `vfs_observation_spec`
- `variable_schema_hash`
- `observation_schema_hash`
- `action_schema_hash`
- `transition_graph_hash`
- `vfs_hash`

That makes VFS part of run identity. A checkpoint does not just resume against "an environment"; it resumes against a specific state/action/observation/transition contract.

### Transitions Are Declared And Compiled

Action effects and passive world dynamics flow through VTC programs rather than remaining as scattered imperative handlers. The current VTC supports:

- Action writes from `ActionConfig.writes`
- Affordance access and occupancy gates
- Multi-tick interaction progress and completion bonuses
- Passive depletion
- Continuous modulations
- Threshold cascades
- Terminal conditions
- Reward components
- Social residue and institutional effects

The transition phase graph orders rules explicitly. The current default phase graph contains:

```text
ingest_actions
advance_global_time
compute_action_legality_masks
apply_movement_and_wait_costs
resolve_affordance_access_and_occupancy
apply_action_costs
advance_interaction_progress
apply_action_effects
apply_completion_bonuses
apply_passive_depletion
apply_modulations
apply_threshold_cascades
apply_social_residue_effects
clamp_and_validate
evaluate_terminal_conditions
compute_rewards
emit_observation_features
emit_telemetry
```

The environment still orchestrates the step loop, item manager, effect manager, and tensor synchronization. VTC owns the declared transition rules and their ordering, composition, masks, clamps, and provenance identity.

At runtime, compiled transition programs are carried on `CompiledUniverse.transition_schedule` and each level's `LevelMetadata.transition_schedule`. `VectorizedHamletEnv` consumes that schedule through `VTCTransitionRunner`; it does not branch on rule-family semantics such as social residue, trust, reputation, or institutional effects. Social residue rules come from experiment-level `transition_rules.yaml`, compile into the schedule, participate in `transition_graph_hash` and `vfs_hash`, and write only through the generic VTC phase runner into `VariableRegistry` state.

### Hashes Make World Semantics Resume-Safe

VFS computes deterministic hashes for each part of the ABI:

| Hash | Meaning |
|------|---------|
| `variable_schema_hash` | Identity of typed state variables: ids, types, scopes, dimensions, lifetimes, access metadata, and normalization ranges. |
| `observation_schema_hash` | Identity of ordered observation fields, shapes, normalization, semantic type, exposure, and curriculum activity. |
| `action_schema_hash` | Identity of runtime actions, costs, effects, reads, writes, and source affordance metadata. |
| `transition_graph_hash` | Identity of the transition phase graph plus compiled transition rules. |
| `vfs_hash` | Combined identity over variable, observation, action, and transition hashes. |

Both checkpoint consumers — `DemoRunner` (training resume) and `LiveInferenceServer` (the serving path) — route through the shared `assert_checkpoint_identity()` gate, which composes the format-version check, `assert_checkpoint_vfs_hash()`, `assert_checkpoint_dimensions()` (dimensions, field UUIDs, `drive_hash`, effective `brain_hash`, and the four per-level content hashes), and the `primary_level` equality check. If the checkpoint's `vfs_hash` differs from the current compiled universe hash, resume fails loudly unless the caller explicitly requests a new VFS branch with `force_new_vfs`; every other identity mismatch fails loudly with no override.

### Scopes Include Social And Relational State

VFS is not limited to per-agent meters. `VariableScope` currently supports:

| Scope | Storage meaning |
|-------|-----------------|
| `global` | One value shared by all agents. |
| `agent` | Per-agent public state. |
| `agent_private` | Per-agent state hidden from normal agent observations. |
| `item` | Per-item-instance VFS state. |
| `pair` | Directed agent-agent state, dense or sparse. |
| `group` | Group, faction, or institution state. |
| `affordance` | Per-affordance-instance state. |
| `zone` | Per-zone state. |
| `message` | Recent per-agent message-token buffers. |

That scope vocabulary lets Townlet model social worlds as first-class state rather than as special-case tensors. The repo includes canonical relational variables for `trust`, `obligation`, `public_reputation`, and `norm_legitimacy`, plus canonical message variables for recent message tokens.

### Dynamic Needs Are Represented As Structure

The current implementation supports two dynamic-need representations:

- Fixed-slot need dimensions such as `intensity`, `growth_rate`, `urgency`, `recurrence`, `substitutability`, `visibility`, `status_value`, `social_mediation`, `contagion`, and `catastrophe_curve`.
- A set-encoder token representation through `dynamic_need_tokens`, shaped as `[max_slots, token_width]`.

The set-encoder path is designed for generalisation experiments where names and labels change but causal structure stays comparable. Brain config supports `architecture.type: set_encoder`, which reshapes the flattened token observation field, encodes each token row, masks all-zero rows, pools token embeddings, and feeds the result into the Q head.

### Generalisation Is Tested Directly

The generalisation harness compares train and test VFS packs where variable names and affordance labels are held out. It builds surface-insensitive signatures that erase names while preserving:

- Causal profiles
- Expression operator structure
- Constants when needed for causal comparison
- Composition modes
- Phases
- Rule kinds

This gives Townlet a direct way to test whether an agent or configuration family can transfer over relationship structure rather than over memorised labels.

## Source Map

| Area | Main files |
|------|------------|
| Public VFS exports | `src/townlet/vfs/__init__.py` |
| Core schemas | `src/townlet/vfs/schema.py` |
| Observation semantic-type vocabulary (the ONE definition) | `src/townlet/vfs/semantic_type.py` |
| Runtime registry and scoped storage | `src/townlet/vfs/registry.py` |
| Observation spec and tensor builder | `src/townlet/vfs/observation_builder.py` |
| Profile compiler and dependency sorting | `src/townlet/vfs/profiles.py` |
| Runtime expression evaluator | `src/townlet/vfs/evaluator.py` |
| Transition phase graph | `src/townlet/vfs/transition_graph.py` |
| Runtime transition schedule and runner | `src/townlet/vfs/transition_schedule.py` |
| VTC programs and rule compilers | `src/townlet/vfs/vtc.py` |
| TorchScript VTC kernels | `src/townlet/vfs/vtc_kernels.py` |
| Schema/provenance hashes | `src/townlet/vfs/schema_hashes.py` |
| Dynamic needs and token layout | `src/townlet/vfs/dynamic_needs.py` |
| Held-out generalisation harness | `src/townlet/vfs/generalisation.py` |
| Canonical relational variables | `src/townlet/vfs/relational.py` |
| Canonical communication variables | `src/townlet/vfs/communication.py` |
| Compiler boundary | `src/townlet/universe/compilers/vfs.py` |
| Universe compile orchestration | `src/townlet/universe/compiler.py` |
| Compiled artifact shape | `src/townlet/universe/compiled.py` |
| Runtime environment integration | `src/townlet/environment/vectorized_env.py` |
| Checkpoint VFS hash validation | `src/townlet/training/checkpoint_utils.py` |

## Core Data Model

### `VariableDef`

`VariableDef` is the schema for a state variable. It defines:

- `id`: stable variable identifier.
- `scope`: storage and visibility shape.
- `type`: scalar, vector, tensor, reference, or message-token type.
- `dims` or `shape`: dimensional metadata for vectors and tensors.
- `lifetime`: `tick`, `episode`, or `persistent`.
- `readable_by`: access-control readers.
- `writable_by`: access-control writers.
- `default`, `initial_value_mode`, and `initial_value_params`: initialization source.
- `normalization`: observation normalization metadata.
- `observable`: whether mark-and-sweep observation extraction should include the variable.

`VariableDef` does **not** carry a semantic type. It did until 2026-08-16 (`default="custom"`,
read by nothing); a state variable has no observation grouping — that is a property of the
observation field that reads it (`vfs.md` §4.1/§4.3), so the field was removed rather than made
required-and-inert (`PDR-0066`).

Supported runtime types include scalar values, booleans, fixed and N-dimensional vectors, reference ids, tensor variables, and message tokens. Tensor variables require explicit shape metadata. `message_token` uses `dims`, not `shape`.

`variables_reference.yaml` remains a static registry input. It must define static variables only. Expressions belong in `vfs_profiles.yaml` or effect/action specifications, and item-scoped variables belong in item VFS profiles rather than `variables_reference.yaml`.

### `NormalizationSpec`

`NormalizationSpec` defines observation normalization. Current kinds are:

- `none`
- `minmax`
- `zscore`
- `cyclical_sin_cos`
- `one_hot`
- `binary`
- `log_scaled`
- `rank_scaled`
- `masked_value`

Nine, not ten: `clipped_log_scaled` was deleted when clamping became a **parameter** (`hamlet-fba56feca5`, `PDR-0054`). `clip` is required on the two range-based kinds (`minmax`, `log_scaled`) and forbidden on the rest, so `log_scaled` + `clip: true` is exactly what `clipped_log_scaled` did — and a plain linear clamp, which had no member at all, is now `minmax` + `clip: true`.

The schema validates required parameters. For example, `minmax` requires ordered `min` and `max` **and an explicit `clip`**, `zscore` requires non-zero `std`, `one_hot` requires at least two categories, and `cyclical_sin_cos` requires a positive period.

### `ObservationField`

`ObservationField` maps a source variable to an observation field. It carries:

- Field id
- Source variable id
- Exposure targets
- Shape
- Optional normalization
- Semantic type — **required**, one member of the closed vocabulary in
  `townlet.vfs.semantic_type`: `bars`, `spatial`, `affordance`, `effects`, `temporal`, `custom`
- `curriculum_active` flag

The active flag lets the compiler preserve stable observation dimensions while masking inactive curriculum features.

**Semantic type is defined once and is load-bearing three ways** (`PDR-0047`, `DIV-005`): it is
in the compiled field's provenance UUID payload, it is mirrored into this VFS field and so into
`observation_schema_hash`, and it names the field's slice in `observation_activity.group_slices`
— how the structured encoders address a group, how the meter encoder is sized, and where the
runtime publishes meter columns (`bars`). The compiled DTO
(`universe/dto/observation_spec.py::ObservationField`) is typed and required on the same
vocabulary, so the compiler is held to the set an author is. Rules:

- The compiler assigns the type for the blocks it emits (`spatial`, `bars`, `affordance`,
  `effects`, `temporal`), only from this set. `effects` was admitted 2026-08-16 — before that the
  compiler emitted it while no schema permitted it, and the VFS mirror silently remapped it to
  `custom`, so one field carried two values.
- Authored `environment.yaml` variables declare `semantic_type` (required, no default) and the
  compiler emits exactly that value. Fields are stable-partitioned by the fixed group order
  `spatial, bars, affordance, effects, custom, temporal` (the identity on every shipped pack), so
  any member is legal without breaking group contiguity, which the compiler still asserts.
  `bars` is reserved to meters — an authored variable declaring it is a compile-time error.
- Exposed global and agent VFS profile variables (`vfs_profiles.yaml`) each compile to their
  own observation field, named after the variable, in the declared scope, and **must** declare
  `semantic_type` (`PDR-0075`, 2026-08-17; `bars` reserved, collisions a compile error). Item
  profile variables carry none: they are observed through the one compiler-emitted feature
  `obs_item_slots` (slot × profile-position layout; the layout question is `hamlet-1ad6383186`).

**The compiled DTO also carries a `feature` — who fills the field — and it is what the runtime
dispatches on** (WS-4 unit 4, `hamlet-39e1fe3c6d`, 2026-08-17). One closed vocabulary,
`townlet.universe.dto.observation_feature`: `variable` (registry-owned — an `environment.yaml`
variable or an exposed profile variable, read by declared scope), and the engine-published
features `grid_encoding`, `local_window`, `position`, `velocity`, `meter` (whose `feature_ref`
names the meter), `affordance_at_position`, `effects`, `temporal`, `item_slots`. Required, no
default. It lives on the compiled DTO **only**, not on this VFS mirror field: it says nothing
about how the field is exposed (id, source, shape, normalization, group, activity — all
unchanged), so it is in no provenance hash and no field UUID, and the differential harness reads
the cut as invisible. Before it, `environment/observation_encoder.py` found each feature's field
by a hardcoded `obs_<x>` string, the meter step parsed the meter's name back out of the field
name, `RecurrentSpatialQNetwork` located its slices by literal name, and two demo entry points
sized the vision window from a field literally called `obs_local_window` — the `PDR-0045` name
branch, in nine places. A field's name is now a label the compiler chose; nothing branches on it.

### `WriteSpec`

`WriteSpec` is the declarative write contract used by actions and VTC rules. It includes:

- `variable_id`
- `expression`
- Optional `condition`
- `composition`
- `phase`
- `priority`
- Optional `clamp`
- `telemetry_label`

Current composition modes are:

- `overwrite`
- `additive_delta`
- `multiplicative_modifier`
- `min`
- `max`
- `clamp`
- `priority_write`
- `last_write_wins`
- `claim_if_free`
- `capacity_claim`
- `append_event`

The important part is that a write is not only "set variable X". It declares how to compose with other writes, where it runs in the phase graph, how it is masked, how it clamps, and how it should be identified in telemetry.

## Compile-Time Flow

The compiler turns config packs into a `CompiledUniverse`. VFS participates in both shared artifact compilation and per-level compilation.

### Shared VFS Artifacts

During shared artifact preparation, `UniverseCompiler`:

1. Compiles `vfs_profiles.yaml` through `VFSCompiler.compile_profiles()`.
2. Validates item profile bindings from `items.yaml`.
3. Collects temporal history requirements from VFS expressions.
4. Builds the effects expression schema with VFS variables included.
5. Compiles the effects catalog.
6. Builds `VFSObservationSpec` from compiled VFS profiles.

### Per-Level VFS Artifacts

For each curriculum level, the compiler:

1. Builds the level observation spec.
2. Builds runtime action metadata and runtime action space.
3. Builds VFS observation fields.
4. Builds registry-ready VFS variables from base observation/environment variables, compiled VFS profiles, and static variables.
5. Computes `observation_schema_hash`.
6. Computes `variable_schema_hash`.
7. Compiles VTC programs for action writes, affordance gates, interaction progress, terminal conditions, passive depletions, modulations, threshold cascades, and reward components.
8. Computes `transition_graph_hash`.
9. Computes the combined `vfs_hash`.
10. Stores all of the above in per-level `CompiledUniverse.LevelMetadata`.

The primary level's metadata becomes the top-level `CompiledUniverse` metadata. Multi-level compiled universes also preserve per-level VFS hashes and schemas.

## Runtime Flow

### Environment Initialization

`VectorizedHamletEnv` consumes the compiled artifact directly. It does not reopen YAML to rebuild VFS state.

At initialization, the environment:

1. Reads `universe.vfs_variables`.
2. Creates `VariableRegistry` with the compiled variables, agent count, device, item capacity, affordance count, and compiled item profiles.
3. Reads `universe.vfs_observation_spec`.
4. Creates `VFSEvaluator` if compiled VFS profiles are present.
5. Stores `vfs_observation_marks` for mark-and-sweep evaluation.
6. Compiles runtime VTC programs from the level's actions, bars, affordances, and drive config.

### Variable Storage

`VariableRegistry` owns runtime tensor storage. Storage shape depends on scope:

- `global`: unbatched singleton or vector/tensor.
- `agent` and `agent_private`: leading `num_agents` dimension.
- `item`: item VFS tensor managed through compiled item profiles.
- `pair`: dense `[num_agents, num_agents, ...]` or sparse edge rows.
- `group`: leading `num_groups` dimension.
- `affordance`: leading `num_affordances` dimension.
- `zone`: leading `num_zones` dimension.
- `message`: `[num_agents, num_message_slots, ...]`.

The registry enforces duplicate-id rejection, tensor allocation guardrails, expected shape checks, dtype checks, access control on `get()` and `set()`, and instance-local storage for fresh environments.

### Dynamic Variable Mutation

Runtime variable add/remove is disabled by default. A registry must be constructed with `dynamic_variable_mode=True` before callers can add or remove variable definitions during a run.

Each dynamic mutation must declare `network_shape_effect`:

- `shape_stable_internal`: the mutation does not change the agent observation/network ABI.
- `observation_schema_changed`: the mutation changes observable agent-facing state.

Observable or agent-exposed variables require `observation_schema_changed`. The registry records each mutation as a `DynamicVariableMutation` with the operation, variable id, network shape effect, shape, dtype, and post-mutation variable schema hash. It also increments `variable_schema_generation`.

This design deliberately prevents accidental observation-shape drift. If a mutation can change the network contract, the caller must say so explicitly.

### VFS Expression Evaluation

`VFSEvaluator` evaluates compiled VFS profile expressions. It supports two modes:

- `MARK_AND_SWEEP`: evaluate only marked variables plus their in-profile dependencies.
- `EAGER`: evaluate every variable in the profile.

Mark-and-sweep mode requires explicit marks. This avoids accidentally evaluating everything when the caller expected a narrow observation set.

The evaluator builds an expression `ExecutionContext` with bars, VFS state, affordances, affordance positions, agent positions, temporal values, VFS types, item VFS storage, item profile maps, and temporal history. It evaluates variables in topological order so later variables can depend on earlier derived values.

### Observation Building

`VFSObservationSpec` computes the VFS contribution to the agent observation dimension:

- Global VFS dimension
- Agent VFS dimension
- Item VFS dimension
- Variable ordering metadata
- Per-section active masks
- Item slot/profile layout

`build_vfs_observation()` reads tensors from the registry, flattens them into `[batch, dim]` components, applies active masks, resolves item inventory slots against item VFS profile metadata, and concatenates all components.

The runtime assembles the full observation by walking the compiled `ObservationSpec` fields **in
order** (`environment/observation_encoder.py::_get_observations`), building every field the same
way — compiled VFS mirror field → its source variable → read from the registry by the variable's
**declared scope** → declared normalization — which is why the compiler's group-order layout
needs no runtime special case (`PDR-0075`). Before assembly, one dispatch
(`_sync_observation_primitives_to_vfs`) publishes each engine-filled feature into its
engine-written registry variable, keyed by the compiled field's declared **`feature`**
(`_FEATURE_PUBLISHERS`, one publisher per engine-published member of the vocabulary; `variable`
fields are registry-owned and skipped; an unknown feature raises). No sync step, network slice
lookup or demo entry point compares a field's name to a literal any more (unit 4,
`hamlet-39e1fe3c6d`); `obs_vfs` no longer exists (unit 3, `hamlet-f0ed709ecf`).

Item observation handling is deliberately strict. Missing item storage, bad inventory shape, out-of-range item indices, unknown item profiles, or missing exposed variables fail loudly instead of silently returning partial observations.

### VTC Execution Model

VTC programs follow a read-snapshot/commit-batch model within phases:

1. Group compiled writes by transition phase.
2. Create a snapshot for the phase.
3. Evaluate each expression and mask against that snapshot.
4. Compose candidate values according to each write's composition mode.
5. Commit the phase values.
6. Move to the next phase.

This matters because two writes in the same phase see the same input state. Ordering within a phase controls conflict resolution, not hidden read-after-write side effects.

`VTCActionWriteProgram` handles action-conditioned writes and capacity/occupancy composition. Other VTC programs handle specialized rule families:

- `VTCAffordanceGateProgram`
- `VTCInteractionProgressProgram`
- `VTCTerminalConditionProgram`
- `VTCPassiveDepletionProgram`
- `VTCModulationProgram`
- `VTCThresholdCascadeProgram`
- `VTCSocialResidueProgram`
- `VTCRewardProgram`

Hot path operations use TorchScript kernels for masked candidates, passive depletion, threshold cascades, modulation multipliers, and terminal conditions.

## Dynamic Needs And Variable Tokens

Dynamic needs are represented as VFS variables rather than as hardcoded bars. The fixed-slot representation creates one vector variable per causal dimension:

```text
dynamic_need_intensity
dynamic_need_growth_rate
dynamic_need_urgency
dynamic_need_recurrence
dynamic_need_substitutability
dynamic_need_visibility
dynamic_need_status_value
dynamic_need_social_mediation
dynamic_need_contagion
dynamic_need_catastrophe_curve
```

Each variable is agent-scoped, episode-lifetime, readable by agent/engine/social_model, writable by engine/VTC, observable, and normalized to the unit interval.

The set-encoder representation exposes a single `dynamic_need_tokens` tensor. Its per-token layout is:

```text
id_embedding
intensity
growth_rate
urgency
tag_embedding
satisfaction_embedding
```

`DynamicNeedTokenLayout` computes the stable token width and field slices. `canonical_set_encoder_dynamic_need_variables()` emits the corresponding `VariableDef`.

On the Brain as Code side, `architecture.type: set_encoder` consumes a flattened token field, reshapes it to `[max_tokens, token_dim]`, masks empty rows, mean-pools token embeddings, and joins that token representation with non-token observation features.

## Generalisation Harness

The generalisation harness is implemented in `townlet.vfs.generalisation`. It exists to validate train/test splits for experiments where surface labels differ but causal structure should remain comparable.

The main API is:

```python
from townlet.vfs import (
    VFSGeneralisationPack,
    assert_held_out_generalisation_split,
    build_vfs_generalisation_signature,
    operator_grammar_signature,
)
```

`assert_held_out_generalisation_split()` verifies that:

- Train and test packs both contain required variable names and affordance labels.
- Variable names do not overlap between train and test.
- Affordance labels do not overlap between train and test.
- Names/labels are not duplicated within a split.
- Surface-insensitive causal profiles match.
- Operator grammar signatures match.

The implementation erases labels such as variable ids, affordance ids, action names, and target/source names while preserving equality relationships inside a profile. It parses expressions into ASTs, records operators/functions/paths structurally, and can compare constants when causal profiles require them.

This makes generalisation tests more than a naming convention. They become a structural check that the held-out test world is causally analogous to the training world.

## Relationship To UAC, BAC, DAC, And Effects

### Universe as Code

Universe as Code declares the world. VFS is the part of that declaration that becomes typed, readable/writable state and transition semantics. The compiler treats VFS profiles, variables, actions, bars, affordances, effects, drive config, and item profiles as sources for compiled runtime artifacts.

### Brain as Code

Brain as Code consumes the observation ABI. The brain config must match the compiled observation shape and representation. For variable-token dynamic needs, the set-encoder architecture is the BAC counterpart to the VFS token layout.

### Drive as Code

Drive as Code can reference VFS variables for reward modifiers and bonuses. VTC reward components also include reward-phase rules in the transition graph hash, which ties reward semantics to VFS identity.

### Effects System

The effects compiler receives a schema that includes bars, environment variables, and compiled VFS variables. Runtime effects can read and write through the VFS registry, but the registry remains the authority for access, shape, and storage.

## Testing Coverage

The current VFS implementation has focused unit tests under `tests/test_townlet/unit/vfs/` covering:

- Schema validation
- Registry storage, shapes, access, scoped variables, and dynamic mutation mode
- Variable registry tensor behavior
- Observation builder and dimension regression
- Item VFS observations and item storage
- VFS evaluator behavior
- Transition phase graph validation
- Expression integration, spatial operators, temporal operators, and noise
- VTC action writes, passive depletion, threshold cascades, modulations, interaction progress, terminal conditions, reward components, affordance gates, occupancy, social residue, and JIT kernels
- Relational variables and message variables
- Dynamic needs and dynamic need tokens
- Held-out generalisation harness

The VFS milestone closeout recorded these final verification commands:

```bash
uv run ruff check
uv run black --check .
uv run mypy src
git diff --check
uv run pytest
```

The full test suite result at milestone closeout was:

```text
2872 passed, 25 skipped, 33 deselected
```

## How To Extend VFS Safely

### Add A Static Runtime Variable

1. Add a `VariableDef` in `variables_reference.yaml`.
2. Keep it static. Do not put expressions in `variables_reference.yaml`.
3. Set explicit `readable_by`, `writable_by`, `lifetime`, `scope`, and default.
4. If it should affect observations, set `observable` and ensure an observation field is emitted.
5. Run the VFS unit slice and the compiler tests that cover the relevant config pack.

### Add A Derived Profile Variable

1. Add the variable to `vfs_profiles.yaml`.
2. Choose global, agent, or item profile scope.
3. Provide exactly one initialization source: `initial_value`, `initial_value_mode`, or `expression`.
4. Let the profile compiler parse, type-check, and topologically sort dependencies.
5. If it should be observed, ensure the resulting variable is marked and reflected in `VFSObservationSpec`.

### Add A New Transition Rule Family

1. Define a source protocol or DTO boundary in `vtc.py`.
2. Compile source config into immutable `CompiledVTC...` records with parsed expression ASTs.
3. Sort records by `TransitionPhaseGraph.sort_key()`, priority, and a stable tiebreaker.
4. Add execution semantics using read-snapshot/commit-batch phase behavior.
5. Include the new rule family in `canonical_transition_graph_schema()` and `compute_transition_graph_hash()`.
6. Add tests for compilation, execution, hash changes, and failure modes.

### Add Runtime Dynamic Variables

1. Construct `VariableRegistry(dynamic_variable_mode=True)`.
2. Call `add_variable()` or `remove_variable()` with an explicit `network_shape_effect`.
3. Use `shape_stable_internal` only when observation/network shape cannot change.
4. Use `observation_schema_changed` when the mutation affects observable agent-facing state.
5. Treat the resulting schema hash/generation as a new ABI identity.

## Current Boundaries

The current implementation is intentionally strict in several places:

- `vfs_profiles.yaml` supports version `1.0`.
- `variables_reference.yaml` is static only.
- `variables_reference.yaml` cannot define item-scoped variables.
- Item profile variables reject tensor types until item tensor layout is explicitly supported.
- Mark-and-sweep evaluation requires explicit marks.
- Runtime variable mutation is disabled unless explicitly enabled.
- Observable dynamic variable changes require an explicit observation-schema-change acknowledgement.
- Checkpoints without `vfs_hash` fail resume.
- Checkpoints with mismatched `vfs_hash` fail resume unless the caller explicitly starts a new VFS branch.

These constraints are part of the design. They keep the ABI visible and force schema changes to be deliberate.

## Related Documents

- `docs/architecture/vfs.md`: full VFS design and integration specification.
- `docs/config-schemas/vfs-profiles.md`: VFS profile config reference. Some status text is older, but the schema concepts remain relevant.
- `docs/config-schemas/variables.md`: static VFS variable config reference. Some status text is older, but the variable concepts remain relevant.
- `docs/config-schemas/brain.md`: includes the set-encoder architecture used by dynamic need token observations.
- `docs/vfs/observation-dimension-formulas.md`: observation dimension formulas.
- `docs/vfs/observation-dimension-manual-validation.md`: manual observation-dimension validation notes.
