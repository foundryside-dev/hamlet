# Townlet Variable & Feature System (VFS) — Updated Design and Integration Specification

**Document Type**: Design Specification + Integration Specification  
**Status**: Phase 1 Complete; observation path fully VFS-driven in production (shadow migration finished, old path deleted); VTC partially unified (Phase 2.x)  
**Version**: 1.1 Draft  
**Last Updated**: 25 August 2026 (re-verified against `src/townlet/` at HEAD after token-obs unit 3 / Task 5 landed: §5.1, §6, §6.2, §6.3, §7.2, §7.4, §9.3, §12.4, §14.4, §16.3, §18.2, §18.4, §20.9, §21.1, §23 — `set_engine_value` now enforces declared shapes, write-backs raise on unknown ids, relational-scope exposure refuses at compile, affordance extents joined the preflight; archived-doc path sweep after the 2026-08-24 docs recut; 22 August 2026: §14.3, §16.3, §16.4, §17 Phase 3+, §20.7, §21.1: social-residue authoring surface shipped as `transition_rules.yaml` with a no-defaults DTO, examples corrected to the shipped grammar and pinned by `tests/test_townlet/unit/config/test_vfs_doc_social_residue_examples.py`, hamlet-84cf93a1b9; §14.3, §16.3, §16.4: write-level `target` removed, hamlet-175bff4ed5; 21 August 2026 source audit against `src/townlet/`: status header, §4.3, §5.1, §6.3, §7.4, §8.1, §8.4, §11.1, §11.4, §13.2, §16.3, §17, §19, §21.1, §23, §24.2; 16 August 2026: §4.1, §4.3, §8.4 semantic-type vocabulary, `PDR-0047` / `PDR-0066`; body otherwise 15 May 2026)
**Original VFS Guide Date**: 7 November 2025  
**Audience**: Engineers integrating VFS into Townlet environments; SDA/Brain-as-Code engineers; curriculum designers; researchers building social, temporal, and multi-agent environments

---

## 0. Executive summary

The Variable & Feature System (VFS) is the formal state, feature, observation, and transition-interface layer for Townlet. It turns the environment from a mostly hardcoded vectorised reinforcement-learning world into a declarative, typed, auditable substrate for software-defined agents.

In its current Phase 1 form, VFS provides:

1. **Schema definitions** for variables and observation fields.
2. **A required experiment-level `vfs_profiles.yaml` catalog** for compiled global, agent, and item profiles.
3. **An optional experiment-level `variables_reference.yaml` static registry overlay** for non-item variables and observation marks; item-scoped variables and expressions belong in `vfs_profiles.yaml`.
4. **A runtime variable registry** that stores state tensors and enforces read/write access control.
5. **An observation-spec builder** that generates agent-facing observation layouts from declarative exposures.
6. **ActionConfig dependency tracking** through declared `reads` and `writes` fields.
7. **Dimension regression tests** to protect checkpoint compatibility.
8. **Integration tests** proving that the schema → registry → observation pipeline works end to end.

The Phase 2 goal is a general **VFS Transition Compiler (VTC)**. Actions are only one part of the world transition. To fully realise Universe as Code, the compiler should eventually execute action effects, passive decay, cascades, temporal rules, interaction progress, occupancy, reward components, terminal checks, and telemetry side effects through one typed, declarative, hashable transition graph.

The strategic role of VFS is:

```text
Universe as Code
    declares world rules, affordances, cascades, terminal conditions, values, and scenario packs

VFS
    declares typed state, features, scopes, visibility, observation contracts, and write permissions

VFS Transition Compiler
    executes declared relationships between variables over time as efficient batched tensor operations

Brain as Code
    declares the agent cognition that consumes VFS observations and chooses actions
```

In one sentence:

> VFS is the formal ABI for software-defined society: it says what exists, who can see it, who can change it, how it is exposed to agents, and how world rules compile into tensor-safe transitions.

---

## 1. Design intent

### 1.1 Why VFS exists

Townlet’s earlier runtime had hardcoded assumptions about:

- which meters exist,
- the order of those meters in tensors,
- how observations are concatenated,
- which world variables an agent can see,
- how actions read and update state,
- and where dimension compatibility is enforced.

That worked for early Hamlet curriculum levels, but it becomes brittle once Townlet expands into:

- partial observability,
- temporal mechanics,
- multi-tick actions,
- multi-zone spatial hierarchy,
- multi-agent competition,
- theory-of-mind modelling,
- emergent communication,
- role-specific visibility,
- relationship graphs,
- dynamic needs,
- and social residue effects such as trust, obligation, reputation, shame, and norm enforcement.

VFS addresses this by making the state interface explicit.

The old model was:

```text
hardcoded tensors + hardcoded observations + imperative update logic
```

The VFS model is:

```text
declarative variables + scoped registry + declarative exposures + declared dependencies + compiled transitions
```

### 1.2 Core design principles

VFS inherits and extends the two main Universe-as-Code principles:

1. **Physics are data.** The engine enforces rules; configuration specifies them.
2. **Values are data.** Rewards, terminal conditions, moral framing, and compliance policies are explicit, diffable, and auditable.

VFS adds several additional principles:

3. **State is typed.** Variables have declared type, shape, scope, access rules, and observation semantics.
4. **Visibility is modelled.** Read access is not only an anti-cheat mechanism; it represents epistemic access, partial observability, privacy, role privilege, self-knowledge, and social inference.
5. **Observation layout is an ABI.** Observation dimensions are generated and regression-tested rather than hand-counted.
6. **Relationships are first-class.** Cascades, temporal gates, affordance effects, occupancy, and social effects should be expressible as typed relationships between variables.
7. **Compiled transitions are hashable.** The compiled transition graph should be part of run provenance, just like the cognitive graph in Brain as Code.
8. **Agents learn over affordances, not hidden Python.** A trained policy should experience a consistent, inspectable relationship between internal pressures, available actions, world constraints, and future consequences.

---

## 2. System context

### 2.1 Relationship to Universe as Code

Universe as Code defines the simulated world as configuration rather than imperative logic. It already treats meters, cascades, affordances, temporal rules, terminal conditions, and reward shaping as world data rather than hardcoded gameplay tweaks.

VFS should be the typed state and feature layer underneath that world. In practical terms:

```text
bars.yaml / universe_as_code.yaml
    becomes VariableDef declarations for survival meters and lifecycle state

cascades.yaml
    becomes RuleSpec / RelationshipSpec declarations over VFS variables

affordances.yaml
    becomes ActionConfig + affordance variables + transition rules

time-of-day, operating hours, multi-tick progress
    become global, agent, or affordance-scoped VFS variables

terminal conditions and reward components
    become compiled evaluators over VFS variables
```

### 2.2 Relationship to Brain as Code

Brain as Code defines the agent’s cognition as three YAML layers:

```text
cognitive_topology.yaml
agent_architecture.yaml
execution_graph.yaml
```

VFS should be treated as the bridge between world and mind:

```text
VFS observation spec → Brain as Code input interface
VFS action definitions → Brain as Code action-space interface
VFS variable metadata → world model / social model grounding
VFS transition graph → consequence prediction target
```

The cognitive hash should eventually include the VFS observation schema and action-space schema, because changing what the agent can see or do changes the effective mind-in-world configuration even if the neural weights are unchanged.

### 2.3 Relationship to Hamlet curriculum levels

VFS supports the Hamlet progression:

| Level | VFS contribution |
|---|---|
| L0 / L1 | Fixed observation ABI, full visibility, baseline meters |
| L2 | Partial observability through exposure config rather than hardcoded observation branches |
| L3 | Time variables, operating-hour masks, interaction progress variables |
| L4 | Zone-scoped variables, hierarchical features, travel costs |
| L5 | Pairwise and affordance-scoped variables for contention, trust, proximity, blocking |
| L6 | Message variables, communication buffers, shared reward features, group scopes |

⚠️ **Correction (2026-08-15).** This section previously carried a single column of per-level
observation dimensions (38 / 78 / 93 / 54 / 93) marked "Validated". **That column conflated two
different quantities**, which is why it could never be reconciled with the other tables in the
corpus.

The observation tensor is a **fixed-width superset with a per-level activity mask**. Every level
allocates the same 124 slots; the mask decides which carry information and which are held at
zero. So "observation dim" has two answers, and only stating both is honest.

Measured by compiling `configs/default_curriculum` at each level on `project-recovery`:

| Config | Allocated (`total_dims`) | Active | Zeroed fields |
|---|---:|---:|---|
| `L0_0_minimal` | 124 | 95 | `obs_local_window` (25), `obs_temporal` (4) |
| `L0_5_dual_resource` | 124 | 95 | `obs_local_window` (25), `obs_temporal` (4) |
| `L1_full_observability` | 124 | 95 | `obs_local_window` (25), `obs_temporal` (4) |
| `L2_partial_observability` | 124 | 56 | `obs_grid_encoding` (64), `obs_temporal` (4) |
| `L3_temporal_mechanics` | 124 | 99 | `obs_local_window` (25) |

**Allocated width is constant by design** — that is precisely the mechanism behind the
"observation dim is constant across grid sizes, enabling transfer learning" claim. It is not a
sign that the levels are identical.

**Active width has three distinct values (95 / 56 / 99)**, and they line up exactly with the
three distinct universes in the pack: L0_0 / L0_5 / L1 are one universe, L2 another, L3 a third.
POMDP does not shrink the tensor — it zeroes the 64-dim grid encoding and lights up the 25-dim
local window instead, which is the reverse swap.

The old numbers were therefore *the right quantity, gone stale*, not nonsense: 93 → 95 and
54 → 56 differ by the two `obs_velocity` dims added since, and L3 moved 93 → 99 because its
temporal block is now actually active. What made the table false was labelling active width as
the total, and the L0_0 = 38 / L0_5 = 78 entries, which assumed 3×3 and 7×7 grids that no level
can express (grid size is pack-level in `stratum.yaml` and unoverridable).

**Do not re-add literals here.** Read `observation_spec.total_dims` off the compiled artifact
(see `CLAUDE.md` → State Representation for the exact call). The numbers above are a dated
measurement, not a specification, and will decay the moment the observed surface changes.

**And they are on their way out entirely.** The observation system is moving to embedded
transformers / token observations (owner, 2026-08-15; direction recorded in
`docs/product/decisions/0017-...`), under which a single total width stops being a meaningful
quantity at all. The two source documents for the old table —
`docs/zzz. archive/vfs/observation-dimension-formulas.md` and
`observation-dimension-manual-validation.md` (archived 2026-08-24) — are marked superseded in
full rather than corrected, for that reason.

The long-term aim is that level changes are expressed primarily by changing variables, exposures, scopes, rules, action definitions, and brain configuration — not by rewriting environment code.

---

## 3. Phase 1 status

### 3.1 Implemented components

Phase 1 implementation is complete.

The current repo convention is split deliberately:

- `configs/<experiment>/vfs_profiles.yaml` is required at the experiment root and is the authoritative source for compiled VFS profiles. It carries global, agent, and item profile definitions and feeds `CompiledUniverse.compiled_vfs_profiles`.
- `configs/<experiment>/variables_reference.yaml` is optional at the experiment root. When present, variables that are not already emitted by observation primitives or VFS profiles become static runtime VFS variables. Duplicate IDs act as observation metadata overlays for the existing variable. The file cannot define item-scoped variables and cannot carry expression DSL fields.
- Level directories must not contain `vfs_profiles.yaml`; profile definitions are shared across curriculum levels, while level-specific activity and masking come from the compiled level metadata.

| Component | Status | Primary verification source |
|---|---:|---|
| Schema Definitions (`VariableDef`, `ObservationField`) | Complete | `tests/test_townlet/unit/vfs/test_schema.py`, `tests/test_townlet/unit/vfs/test_observation_field_schema.py` |
| Variable Registry runtime storage + access control | Complete | `tests/test_townlet/unit/vfs/test_registry.py`, `tests/test_townlet/unit/vfs/test_scoped_registry.py`, `tests/test_townlet/unit/vfs/test_variable_registry_tensor.py` |
| Observation Spec Builder compile-time spec generation | Complete | `tests/test_townlet/unit/vfs/test_observation_builder.py`, `tests/test_townlet/unit/universe/test_evaluation_marks.py` |
| `ActionConfig` extension with `reads` / `writes` fields | Complete | `tests/test_townlet/unit/vfs/test_vtc_action_writes.py`, `tests/test_townlet/unit/vfs/test_schema_hashes.py` |
| Dimension regression coverage for checkpoint compatibility | Complete | `tests/test_townlet/unit/vfs/test_observation_dimension_regression.py` |
| Integration coverage for end-to-end VFS flows | Complete | `tests/test_townlet/integration/vfs/`, `tests/test_townlet/integration/test_vfs_runtime_evaluation.py` |

Use the current pytest and coverage artifacts as the source of truth for verification metrics. This spec intentionally does not freeze point-in-time metric snapshots.

### 3.2 What Phase 1 proves

Phase 1 proves that VFS can:

- define state variables in configuration,
- initialise runtime storage for those variables,
- enforce read/write permissions,
- generate observation specifications,
- calculate observation dimensions before runtime,
- preserve checkpoint compatibility through regression tests,
- and attach declared read/write dependencies to action definitions.

The repo no longer has "no transition compiler." The implemented VFS read path already parses profile expressions into ASTs, type-checks them, topologically sorts profile dependencies, and evaluates derived variables through `VFSEvaluator` in mark-and-sweep or eager mode. The action-write path also has an initial VTC slice: `ActionConfig.writes` compile into parsed, phase-ordered `VTCActionWriteProgram` rules that execute masked tensor writes during `env.step`.

The remaining VTC gap is full transition unification: write-expression type/shape validation, passive dynamics, cascades, temporal rules, rewards, terminal checks, telemetry, and non-action world physics still need to move into one validated transition graph.

---

## 4. Core concepts

### 4.1 Variables

A **variable** is stored state. It may represent a survival meter, position, time, progress counter, affordance occupancy, hidden motivation, public reputation, relationship trust, message buffer, or any other stateful element of the world or agent.

A variable definition should minimally specify:

```yaml
- id: "energy"
  type: "scalar"
  scope: "agent"
  range: [0.0, 1.0]
  initial: 1.0
  readable_by: ["agent", "engine", "bac"]
  writable_by: ["engine", "bac"]
  description: "Ability to move and act"
```

Phase 1 already supports the basic schema. Future versions should extend metadata so variables can describe more of their causal role:

```yaml
metadata:
  tags: ["need", "pivotal", "survival", "normalised"]
  semantic_class: "survival_meter"
  observation_priority: "core"
  checkpoint_critical: true
  clamp: [0.0, 1.0]
```

Note the distinction, because the names are close: `semantic_class` above is *proposed variable
metadata* — the variable's causal role, for the research/generalisation side, and it must never
be read by the compiler or runtime to decide behaviour (`PDR-0045`, name-blindness). The
**semantic group** in §4.3 (`semantic_type` in code) is an *observation-field* property with a
closed vocabulary that IS consumed — by the group slices. Until 2026-08-16 `VariableDef` also
carried a `semantic_type` that nothing read; it was removed (`PDR-0066`).

### 4.2 Features

A **feature** is a derived observation component. It may be computed from stored variables but not stored as authoritative state.

Examples:

```yaml
features:
  - id: "distance_to_nearest_food"
    source: "derived"
    reads: ["position", "affordance_positions", "affordance_categories"]
    expression: "min_distance(position, affordance_category == food)"
    readable_by: ["agent"]
    normalization: { kind: "minmax", min: 0, max: 16 }
```

This separates:

```text
VariableDef = stored world state
FeatureDef  = derived model input or diagnostic signal
RuleSpec    = transition relationship over variables
```

Phase 1 currently focuses on variables and observation fields. `FeatureDef` is a recommended future extension.

### 4.3 Observation fields

An **observation field** maps a variable or feature into an agent-facing observation tensor. Observation fields define:

- source variable or feature,
- shape,
- normalisation,
- exposure conditions,
- **semantic group** — one member of a closed vocabulary (`bars`, `spatial`, `affordance`,
  `effects`, `temporal`, `custom`; `townlet.vfs.semantic_type`), which names the field's slice
  in `observation_activity.group_slices` so structured encoders and the meter block's consumers
  can address a run of dimensions without knowing any field's name,
- and ordering in the observation ABI — fields are laid out grouped, in the fixed group order
  `spatial, bars, affordance, effects, custom, temporal`. (The order is guaranteed in the
  `full_auto` / `max_compact` observation modes; the `full_manual` mode reorders fields to the
  author's `include_fields` list, and only per-group contiguity is enforced after it.)

The compiled field additionally records **which feature fills it** — `variable` for a
registry-owned source, or one of the engine's own encoders (`grid_encoding`, `local_window`,
`position`, `velocity`, `meter` with the meter named, `affordance_at_position`, `effects`,
`temporal`, `item_slots`; one closed vocabulary, `townlet.universe.dto.observation_feature`).
That is the runtime's dispatch key: the environment publishes engine features, the structured
encoders locate their blocks, and the demo sizes the vision window by the field's feature, never
by its name (`PDR-0045`). It is not part of the ABI above — it says who fills the source, not how
the field is exposed — so it lives on the compiled DTO only and moves no hash.

The semantic group is a property of the **observation field**, never of the variable (§4.1): a
variable is stored state; how it is grouped when observed is part of how it is exposed. Where an
author declares it (today: `environment.yaml` variables and exposed global/agent profile
variables, one compiled field each) the compiler
obeys; for the blocks the compiler emits itself it assigns a member from the same closed set — a
value an author may not write is a value the compiler may not emit (`PDR-0047`). `bars` is the
meter block and is reserved to meters. Vocabulary extension is a decision (`PDR-0016`), not a
literal at a call site.

Observation fields are not mere convenience. They are the curriculum and checkpoint-compatibility boundary.

Changing which fields are exposed can create a new observation ABI and may break existing checkpoints.

### 4.4 Rules / relationships

A **rule** or **relationship** is a typed operation that reads variables and writes variables.

Examples include:

- passive depletion,
- threshold cascades,
- continuous modulations,
- action costs,
- action effects,
- operating-hour gates,
- multi-tick progress,
- occupancy claims,
- terminal checks,
- reward components,
- social visibility effects,
- reputation updates,
- obligations,
- and message propagation.

This is the most important conceptual expansion:

> The ontology is not just “needs” or “bars”. The ontology is variables plus relationship operators over time.

### 4.5 Actions and affordances

An **action** is a selected operation available to the policy. An **affordance** is a world opportunity that can be used by an action under certain preconditions.

Examples:

```text
Action: INTERACT
Affordance at tile: Hospital
Result: apply hospital interaction rules if open, affordable, and capacity available
```

In VFS terms, actions and affordances should declare:

- variables they read,
- variables they write,
- preconditions,
- costs,
- effects,
- operating hours,
- interaction type,
- capacity / exclusivity,
- interruptibility,
- and special effect handlers.

---

## 5. Variable scopes

### 5.1 Current scopes

The current repo defines **nine** canonical scope classes (`VariableScope` in `vfs/schema.py`)
— the eight below plus `message`, described at the end of this section:

| Scope | Use case | Example |
|---|---|---|
| `global` | Shared state | `time_sin`, `day_of_week`, `weather_state` |
| `agent` | Per-agent observable state | `energy`, `position`, `health` |
| `agent_private` | Per-agent hidden state | `internal_motivation`, `hidden_reward` |
| `item` | Per-item-instance state compiled from item profiles | `durability`, `charges`, `spoilage` |
| `pair` | Directed agent-agent relationship state | `trust`, `fear`, `obligation`, `resentment` |
| `group` | Group, faction, family, or team state | `group_norm_strength`, `membership`, `loyalty` |
| `affordance` | Per-affordance-instance capacity and occupancy state | `occupied_by`, `cooldown`, `is_open` |
| `zone` | Multi-zone environment state | `zone_danger`, `travel_cost`, `zone_crowding` |

`item` scope is profile-based, not loaded from `variables_reference.yaml`. The registry allocates a profile-agnostic `item_vfs[max_items, max_profile_vars]` tensor, records `item_profile_map[profile_name][var_name] -> tensor_index`, and masks unused profile slots. Item profile definitions therefore live in `vfs_profiles.yaml:item_profiles`, while item instances address rows in the shared item VFS tensor.

`pair` scope has two explicit allocation modes. `pair_storage_mode="dense"` prefixes values with `[num_agents, num_agents]`
for small all-pairs simulations. `pair_storage_mode="sparse"` requires a directed `pair_edges[num_pair_edges, 2]`
neighbourhood graph, validates that every edge is unique and in range, and stores pair values as `[num_pair_edges, ...]`.
Sparse pair registries expose the active edge list, a dense boolean neighbourhood mask, and a dense diagnostic materialisation
view; dense-shaped writes to sparse pair variables fail loudly instead of being treated as a compatibility path.

`group`, `affordance`, and `zone` scope storage is dense. These scopes require explicit positive `num_groups`,
`num_affordances`, and `num_zones` registry extents before allocation.

`message` scope is a dense L6 seed for recent communication buffers. It prefixes payload values with
`[num_agents, num_message_slots]`, requires an explicit positive `num_message_slots` registry extent, and is used by
`message_token` variables such as `recent_message_tokens`.

**Runtime wiring (2026-08-21, `hamlet-9e1ae3b7a2` — closed).** All nine scopes are reachable
end-to-end from config. `zone`, `group`, `message` — and, since 2026-08-25, `affordance`
(`hamlet-702ae15f82`) — size their storage from the optional top-level `extents:` block of
`variables_reference.yaml` (`num_zones` / `num_groups` / `num_message_slots` /
`num_affordances`, each ≥ 1; `_SCOPE_EXTENT_FIELD`, `vfs/schema.py:594-599`); the extents flow
through `UniverseMetadata` into `_initialize_vfs_subsystem`. Declaring a variable of one of
those scopes without its extent is a compile error at config load — never a green compile that
crashes at env construction. See `docs/zzz. archive/config-schemas/variables.md` (stale
2025-11, archived 2026-08-24 — schema concepts only). Note the extents allocate storage only:
there is still no agent→zone / agent→group membership mapping surface.

> ⚠ **Caveat (2026-08-24 audit,
> `archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md`):** "reachable end-to-end from
> config" holds for *storage allocation*, but not for *referenceability*.
> `variables_reference.yaml` variables never enter the compiler symbol table
> (`universe/validation/references.py:14-58` registers only `environment.yaml` and
> `vfs_profiles.yaml` variables — `hamlet-33e520cebd`), so no effect, affordance, action write
> or `drive.yaml` can reference a `pair` / `affordance` / `zone` / `group` / `message` variable
> by name. Sparse pair storage (`pair_storage_mode` / `pair_edges`) is likewise real, tested
> registry code with **no wiring from any config pack** — every environment is dense-pair.
> And the `agent_private` scope-table row above ("hidden state") describes the declared intent,
> not current behaviour: the runtime observation path bypasses the access check and treats
> `agent_private` identically to `agent` (`hamlet-83a043a9b9`; see the §6 caveat).
>
> **Re-verified 2026-08-25, with two edges hardened since the audit.** The symbol-table gap
> itself is unchanged (`universe/validation/references.py:14-58` still registers only
> `environment.yaml` and `vfs_profiles.yaml` variables). What changed: (a) attempting to
> *expose* a `pair`/`group`/`affordance`/`zone`/`message` variable as an observation field now
> refuses loudly at compile — `ObservationField.__post_init__` rejects those five scopes by
> table (`universe/dto/observation_spec.py:73,84-93`; the scope Literal was simultaneously
> widened to all nine members); (b) an affordance-scoped `variables_reference.yaml` variable
> without `extents.num_affordances` is now a compile error, not a registry-construction crash
> (see the extents paragraph above).

### 5.2 Recommended future scopes

For serious multi-agent and small-society modelling, VFS should still add richer institutional and communication scopes:

| Scope | Shape intuition | Use case | Example |
|---|---|---|---|
| `household` | `[household]` | Shared domestic resources | `shared_food`, `rent_due`, `household_mood` |
| `faction` | `[faction]` | Political or social blocs | `legitimacy`, `territory_claim` |
| `institution` | `[institution]` | Rules and enforcement | `sanction_probability`, `rule_legitimacy` |

The implemented L5/L6 seed scopes are the storage foundation for multi-agent competition and emergent communication.
Sparse pair storage is available for neighbourhood-limited relationships, and message scope can store recent
message-token payloads. Relational visibility, sender metadata, message age, and end-to-end communication semantics
remain separate follow-on work.

### 5.3 Social observability and privacy

> ⚠ **Caveat (2026-08-24 audit; re-verified line-by-line 2026-08-25): this section is design
> intent with no working authoring door today.** The examples below cannot be authored on
> either required surface — `vfs_profiles.yaml` and `environment.yaml` have **no
> `readable_by`/`writable_by` fields at all**, and the compiler hardcodes
> `["agent","engine"]` / `["engine"]` for every variable regardless of declared scope
> (`universe/compilers/vfs.py:318-320`,
> `universe/compilers/observation.py:813-815,868-870`). `exposed_to` fails open (omitted *and*
> explicitly `[]` both rewrite to `["agent"]` —
> `vfs_profiles_config.py:127-128,238-239,325-326`; the audit's pack census found only 2 of
> ~49 authored profile variables state exposure explicitly), and the one file that does accept
> these fields, `variables_reference.yaml`, is invisible to the compiler symbol table (§5.1
> caveat). Every privacy / hidden-state / social-inference mechanic this section describes is
> currently **unauthorable while appearing authorable**. Full story:
> `archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md` (Headline and Top gaps);
> tickets `hamlet-1a520475f4`, `hamlet-83a043a9b9`, `hamlet-d97b4d6b4a`, `hamlet-33e520cebd`.
>
> The same hardcoding pattern hits **`lifetime`**, in opposite directions on the two required
> surfaces: every `environment.yaml` variable is compiled `lifetime="tick"`
> (`universe/compilers/observation.py:813,868` — no counter or accumulator authored there can
> survive a step, `hamlet-4597fd5d04`), and every `vfs_profiles.yaml` profile variable is
> compiled `lifetime="persistent"` (global) / `"episode"` (agent)
> (`universe/compilers/vfs.py:105,109` — a global profile variable can never be declared to
> reset with the episode, `hamlet-0268336cd1`). Neither DTO carries a `lifetime` field. The
> registry's three-way lifetime mechanics (`tick`/`episode`/`persistent`,
> `registry.py:595-610`) are correct where they run; the author simply cannot reach them
> except through `variables_reference.yaml`.

Read access should represent what an actor may know, not merely what code may inspect.

Examples:

```yaml
- id: "true_health"
  type: "scalar"
  scope: "agent"
  readable_by: ["engine", "doctor_role"]
  writable_by: ["engine", "vtc"]

- id: "perceived_health"
  type: "scalar"
  scope: "agent_private"
  readable_by: ["agent"]
  writable_by: ["perception_model", "vtc"]

- id: "public_distress_signal"
  type: "scalar"
  scope: "agent"
  readable_by: ["agent", "other_agents", "social_model", "engine"]
  writable_by: ["engine", "vtc"]
```

This allows divergence between:

```text
true state
self-perceived state
publicly signalled state
socially inferred state
engine-only ground truth
```

That divergence is the basis for partial observability, role-based knowledge, misperception, privacy, deception, and social inference.

---

## 6. Access control

> ⚠ **Caveat (2026-08-24 audit; re-verified 2026-08-25): the enforcement machinery below is
> real in `registry.py` but is not currently a live policy layer.** Three qualifications, each
> verified at line level: (1) the checked `get()`/`set()` path this chapter documents is
> **bypassed on the observation path** — observations are built through
> `get_agent()`/`get_global()`, which perform no access check and treat `agent_private`
> identically to `agent` (`registry.py:754-796`; `observation_builder.py:359,374`;
> `observation_encoder.py:86`; `hamlet-83a043a9b9`), so the `PermissionError` examples below
> never fire for observation reads — the one real `agent_private` block, inside `get()`
> (`registry.py:514-517`), is never on the observation route; (2) no runtime call site
> anywhere passes a reader/writer role other than `"engine"` (`vectorized_env.py:1282`;
> `hamlet-1a520475f4`), so the role vocabulary is binary in practice; (3) there is **no
> authoring surface** for `readable_by`/`writable_by` on either required config file (§5.3
> caveat). The enforcement code is correct where it runs; it is not yet wired to an author's
> intent. Fix vehicle: the token-observation migration's explicit-exposure work plus a
> registry-read-path/role-wiring unit. Source of truth:
> `archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md`.
>
> A neighbouring hazard from the same audit is **fixed** (2026-08-25, `hamlet-0ddc83e377`):
> the three VFS write-back sites in `environment/vectorized_env.py` that silently dropped
> writes to unknown variable ids now raise `KeyError` naming the id and the write source
> (global-profile write-back `:1099`, agent-profile write-back `:1138`,
> `_commit_vtc_transition_state` `:1271`). That is a loudness fix, not access control — the
> three qualifications above are untouched by it.

### 6.1 Purpose

VFS access control serves four roles:

1. **Engineering safety** — prevent invalid writes such as an agent directly setting its own energy.
2. **Epistemic modelling** — represent who is allowed to know what.
3. **Governance** — make visibility and authority auditable.
4. **Curriculum control** — expose or hide variables by level.

### 6.2 Reading variables

```python
# Agent reads energy meter (access control enforced)
energy = registry.get("energy", reader="agent")
# Returns: torch.Tensor shape [num_agents] on correct device

# Engine reads position for rendering
position = registry.get("position", reader="engine")
# Returns: torch.Tensor shape [num_agents, 2]

# Attempt unauthorized read (raises PermissionError)
try:
    private_reward = registry.get("internal_motivation", reader="agent")
except PermissionError as e:
    print(f"Access denied: {e}")
```

Key points:

- `reader` enforces access control.
- `PermissionError` is raised if access is denied.
- Runtime cost is dictionary lookup plus permission check.
- Access policies should be part of run provenance.
- **`item`-scoped variables never enter this surface at all** (2026-08-25 note): the registry
  actively excludes them from `_definitions` (`registry.py:717-721`), so `registry.get()` on an
  item variable id raises `KeyError`. Item state is reached only through the separate
  `read_item` / `write_item` / `register_item_instance` API (`registry.py:821+`), which takes
  no reader/writer role and is not checked against `readable_by`/`writable_by`
  (`hamlet-f2a37a8c8a`).

### 6.3 Writing variables

```python
# Update energy after action costs
new_energy = current_energy - action_costs
registry.set("energy", new_energy, writer="engine")

# Update position after movement
new_position = current_position + action_delta
registry.set("position", new_position, writer="actions")

# Attempt unauthorized write (raises PermissionError)
try:
    registry.set("energy", hacked_values, writer="agent")
except PermissionError as e:
    print(f"Write denied: {e}")
```

Key points:

- `writer` enforces write permissions.
- Tensors are automatically moved to the registry device.
- `registry.set()` validates shape and dtype against the declaration and raises on mismatch.
- `set_engine_value()` — the engine/VTC writeback path (§7.2) — **also enforces the declared
  element shape since 2026-08-25** (`hamlet-d970ef83f0`); it differs from `set()` in that the
  writer role is fixed to `"engine"` and dtype is coerced rather than rejected.
- Future compiler stages should perform shape validation at compile time.

### 6.4 Principle of least privilege

```yaml
# Good: agent can read energy but not write it
- id: "energy"
  readable_by: ["agent", "engine"]
  writable_by: ["engine", "vtc"]

# Bad: agent can directly write its own energy
- id: "energy"
  readable_by: ["agent", "engine"]
  writable_by: ["agent", "engine"]
```

For multi-agent worlds, also avoid granting generic `other_agents` access to private or exact internal state unless that exposure is an intentional part of the scenario.

---

## 7. Registry initialisation and runtime storage

### 7.1 Initialising the registry

```python
from pathlib import Path

from townlet.universe.compiler import UniverseCompiler
from townlet.vfs import VariableRegistry

# Compile the experiment-root VFS profile catalog.
compiled = UniverseCompiler().compile(
    Path("configs/default_curriculum"),
    primary_level="L1_full_observability",
    use_cache=False,
)

# Initialize registry from compiled VFS variables, not by reopening YAML at runtime.
registry = VariableRegistry(
    variables=compiled.vfs_variables,
    num_agents=population_size,
    device=device,  # torch.device("cuda" if cuda_available else "cpu")
)

# Registry is now ready for get/set operations
```

Key points:

- Registry manages GPU tensors automatically.
- Access control is enforced at runtime.
- Shape management is handled by scope semantics.
- Registry initialisation should be deterministic and hashable.

### 7.2 Repo-side registry surfaces

The current repo has two registry surfaces:

- `VariableRegistry` is the compiled runtime registry used by `VectorizedHamletEnv`. It owns declared VFS variables, permission checks, lifetime resets, item-profile tensor storage, and engine writeback.
- `ScopedVariableRegistry` is a simpler global/agent/item utility registry that implements the same protocol shape for observation-builder tests, item-observation tests, and component benchmarks. It is not the environment hot path, but it is still an intentional adapter/test surface rather than dead code.

Runtime VFS evaluation uses `VariableRegistry.set_engine_value()` for evaluator writeback. This method is deliberately narrower than direct storage mutation: it requires the variable to exist and requires `engine` write permission, with dtype coerced to the declaration rather than rejected.

> **Corrected 2026-08-25** (`hamlet-d970ef83f0`, token-obs unit 3 Task 5b). This paragraph
> previously said `set_engine_value()` "bypasses declaration-shape checks so derived global VFS
> variables may store batched per-agent results". That carve-out is gone:
> `set_engine_value()` now validates `value.shape` against the declared element shape for
> **every** variable (`registry.py:563-593`) — a global scalar can no longer hold a
> `[num_agents]` batch, which previously let storage drift permanently from the declared
> schema (`hamlet-2ca2cb373f`). A variable whose expression is genuinely per-agent must be
> declared agent-scoped; `configs/test/vfs_bar_access` was re-scoped exactly this way as part
> of the fix (zero-backcompat: old configs fail loudly and get corrected).

Runtime add/remove of top-level registry variables is gated behind
`VariableRegistry(dynamic_variable_mode=True)`. Callers must use
`add_variable(...)` / `remove_variable(...)` with an explicit
`network_shape_effect`:

- `shape_stable_internal` for variables that do not change the agent
  observation schema.
- `observation_schema_changed` for observable variables or variables whose
  addition/removal must fork the observation/network ABI.

The registry rejects dynamic mutations by default, rejects observable variables
unless the caller acknowledges `observation_schema_changed`, and records a
`DynamicVariableMutation` audit entry containing the post-mutation
`variable_schema_hash`.

### 7.3 Recommended registry invariants

The registry should guarantee:

- all declared variables exist after initialisation,
- all tensors are on the configured device,
- global variables have global shape,
- agent variables have leading dimension `num_agents`,
- pair variables have shape `[num_agents, num_agents, ...]` or an equivalent sparse representation,
- all values respect declared dtype,
- optional clamps are applied after transition phases,
- access control is enforced consistently, including `set_engine_value()` engine permission checks,
- variable definitions are immutable during a run unless dynamic-variable mode is explicitly enabled.

### 7.4 Shape validation

Current state (re-audited 2026-08-25): manual `registry.set()` is strict — shape and dtype
are validated against the declaration — and `set_engine_value()` is now strict on shape too
(`hamlet-d970ef83f0`; dtype is coerced, not rejected — see §7.2). The remaining gap is
compile-time: VTC write expressions validate their candidates against the **phase-snapshot
tensor's** shape mid-phase, not the declared schema (`vtc.py:504-513`,
`_coerce_expression_tensor`). Because the commit boundary now enforces declared shapes, a
mis-shaped candidate can no longer be silently stored — it raises at commit — but the error
surfaces at the first `env.step`, not at compile. Phase 2+ should move declared-schema checks
into the compiler.

Suggested rule:

```text
Manual registry.set() in engine code:
    strict (shape + dtype against the declaration)

Engine/VTC writeback (set_engine_value):
    strict on shape since 2026-08-25; dtype coerced

Compiler-generated writes:
    validate against the declared schema at compile time (still open);
    today they fail loudly at the commit boundary instead

External tooling / tests:
    always strict
```

---

## 8. Observation specifications

### 8.1 Building observation specs

> **Corrected 2026-08-21.** An earlier draft of this section showed a
> `VFSObservationSpecBuilder` class; no such class exists in the tree and it never shipped.
> Observation specs are built by the universe compiler, not by hand.

```python
from pathlib import Path

from townlet.universe.compiler import UniverseCompiler

# ObservationCompiler (townlet.universe.compilers.observation) lays out the
# engine feature blocks and every exposed global/agent profile variable into
# one grouped, fixed-width spec at compile time.
u = UniverseCompiler().compile(
    Path("configs/default_curriculum"),
    primary_level="L1_full_observability",
)

obs_spec = u.observation_spec            # ObservationSpec: ordered .fields + .total_dims
obs_dim = u.observation_spec.total_dims  # allocated width, known before runtime
activity = u.observation_activity        # per-level active_mask + group_slices
```

At runtime, `townlet.vfs.observation_builder.build_vfs_observation` materialises each
VFS-sourced field and `ObservationEncoder` (`src/townlet/environment/observation_encoder.py`)
drives the full per-field loop.

Key points:

- Specs are generated at compile time.
- Observation dimension is calculated before network construction.
- Normalisation specs are preserved for observation generation.
- Dimension regression protects checkpoint compatibility.

### 8.2 Generating observations from registry

```python
def get_observations(registry, obs_spec):
    """Generate observations from VFS registry using observation spec."""
    obs_tensors = []

    for field in obs_spec:
        # Read variable from registry
        value = registry.get(field.source_variable, reader="agent")

        # Apply normalization if specified
        if field.normalization:
            value = apply_normalization(value, field.normalization)

        # Flatten if needed (registry tensors are [num_agents] or [num_agents, dims])
        if len(value.shape) == 1:
            value = value.unsqueeze(-1)  # [num_agents] → [num_agents, 1]

        obs_tensors.append(value)

    # Concatenate all observation components
    observations = torch.cat(obs_tensors, dim=-1)  # [num_agents, obs_dim]
    return observations
```

Key points:

- Each field is read with access control.
- Normalisation is applied as specified.
- Outputs concatenate into `[num_agents, obs_dim]`.
- The sketch above is illustrative; the production implementation of this loop is
  `ObservationEncoder._get_observations` (`src/townlet/environment/observation_encoder.py`).
- Future versions may cache derived features or precompile observation generation.

### 8.3 Observation exposure as curriculum

Observation exposure is not only a data-pipeline concern. It is a curriculum mechanism.

The same world can be presented through different exposure specs:

```text
full observability
partial observability
hidden health
noisy health
hidden money
visible exact time
cyclical time features only
public reputation only
private relationships visible
relationship graph hidden but inferable
```

This enables controlled experiments:

```text
same world, different epistemic access
same brain, different observation schema
same variable definitions, different exposure policies
same policy architecture, different visibility rules
```

The current repo also supports dimension-preserving curriculum masking through `ObservationField.curriculum_active`. When `curriculum_active=false`, the field remains in the observation ABI and contributes padding dimensions, but `ObservationActivity.active_mask` marks those dimensions inactive and omits them from `active_field_uuids`. Use this for per-level activation/masking without changing `obs_dim`; adding or removing fields still creates a new observation schema.

### 8.4 Observation ABI and schema hashes

Every observation spec should have an `observation_schema_hash` computed over:

- ordered field list,
- source variables/features,
- shapes,
- normalisation rules,
- exposure conditions,
- semantic group,
- `curriculum_active` masks,
- dtype information,
- and version metadata.

The checkpoint should store this hash. Resume must refuse to attach a checkpoint to an incompatible observation ABI; changed VFS schemas create a new run fork.

Current state (2026-08-21): `compute_observation_schema_hash` (`townlet/vfs/schema_hashes.py`)
covers everything above **except version metadata**, which is not yet in the payload.
Checkpoints stamp both `observation_schema_hash` and the combined `vfs_hash`
(`training/checkpoint_utils.py`); resume compares `vfs_hash` plus the per-field UUIDs and the
other config hashes rather than `observation_schema_hash` directly — enforcement is real but
indirect.

---

## 9. Normalisation

### 9.1 Current strategy

Inputs should generally be normalised to `[0, 1]` or `[-1, 1]` for stable learning.

```yaml
# Good: meter normalised to [0, 1]
- id: "obs_energy"
  normalization:
    kind: "minmax"
    min: 0.0
    max: 1.0

# Warning: unbounded money may harm learning
- id: "obs_money"
  normalization: null
```

The existing Townlet convention keeps survival meters in `[0.0, 1.0]`. Money is also normalised in baseline packs, where `1.0` approximates `$100`.

### 9.2 Recommended extensions

Supported normalisation types should include:

```text
none
minmax
zscore
cyclical_sin_cos
one_hot
binary
log_scaled
rank_scaled
masked_value
```

Examples:

```yaml
- source_variable: "time_of_day"
  normalization:
    kind: "cyclical_sin_cos"
    period: 24

- source_variable: "money"
  normalization:
    kind: "log_scaled"
    min: 0.0
    max: 1000.0
    clip: true
```

> **Corrected 2026-08-15** (`PDR-0054`, `hamlet-fba56feca5`). This section listed **ten**
> kinds including `clipped_log_scaled`, and its own money example then passed `clip: true`
> to it — a parameter the kind's name already implied. That redundancy was the tell:
> clamping is a *parameter*, not a member. It is now required on the two range-based kinds
> (`minmax`, `log_scaled`) and forbidden on the rest, `clipped_log_scaled` is deleted, and
> the example above is the same declaration with the member folded into the parameter.
> The gain is that a **plain linear clamp** — which no member offered, so it was
> unauthorable — is `minmax` + `clip: true`.

Normalisation must be part of the observation schema hash.

### 9.3 Where normalisation lives (2026-08-25 note)

Only **`ObservationField.normalization`** is applied at runtime
(`observation_encoder.py:109-148` — all nine §9.2 kinds implemented and reachable).
`VariableDef.normalization` is a separate object that validates at parse time and contributes
its min/max range to `variable_schema_hash` (`schema_hashes.py:149`) but is **read by nothing
at runtime** — declaring it on a `variables_reference.yaml` variable normalises nothing
(2026-08-24 audit finding, unticketed). Normalisation is a property of how a variable is
*exposed*, not of the variable; the dead field should eventually be deleted or wired, not
relied on.

---

## 10. ActionConfig dependency tracking

### 10.1 Current use

Action definitions declare dependencies and may carry compiled VTC write rules. The current write path parses `WriteSpec.expression` and optional `condition` into ASTs, orders writes by the transition phase graph, and applies masked tensor updates for selected active agents during `env.step`.

```python
from townlet.environment.action_config import ActionConfig
from townlet.vfs import WriteSpec

# Movement action with VFS dependencies
action = ActionConfig(
    id=0,
    name="MOVE_UP",
    type="movement",
    delta=[0, -1],
    costs={"energy": 0.005},
    effects={},
    enabled=True,
    description="Move up one cell",
    icon="⬆️",
    source="substrate",
    source_affordance=None,

    # VFS Integration (Phase 1)
    reads=["position", "energy", "grid_encoding"],
    writes=[
        WriteSpec(
            variable_id="position",
            expression="position + delta",  # Parsed and executed by the action-write VTC slice
        ),
    ],
)

# Validation: Ensure all read/write variables exist in registry
for var_id in action.reads:
    assert var_id in registry.variables, f"Variable {var_id} not found in registry"

for write_spec in action.writes:
    assert write_spec.variable_id in registry.variables, \
        f"Variable {write_spec.variable_id} not found in registry"
```

Key points:

- Action dependencies remain useful for static analysis and schema hashing.
- The implemented action-write path covers selected-action writes with phase ordering, composition, clamps, and masks.
- The remaining VTC work is broader than action writes: unified type/shape validation and non-action transition rules still need compiler coverage.

### 10.2 Recommended WriteSpec fields

Future `WriteSpec` objects should include conflict and provenance metadata:

```yaml
writes:
  - variable_id: "energy"
    expression: "energy - 0.005"
    condition: "agent_mask & action_is_move"
    composition: "additive_delta"
    clamp: [0.0, 1.0]
    priority: 10
    phase: "action_costs"
    telemetry_label: "movement_energy_cost"
```

Recommended fields:

| Field | Purpose |
|---|---|
| `variable_id` | Target variable |
| `expression` | Safe DSL expression |
| `condition` | Optional mask or predicate |
| `composition` | How to combine with other writes |
| `phase` | Transition phase where the write occurs |
| `priority` | Ordering within phase where required |
| `clamp` | Optional post-write bounds |
| `telemetry_label` | Human-readable audit label |

---

## 11. VFS Transition Compiler naming and scope

### 11.1 Naming note

The repo standard is **VFS Transition Compiler (VTC)** for transition-rule compilation. **BAC** remains reserved for **Brain as Code**, so transition compiler documentation, telemetry, hashes, and code reviews should use VTC terminology.

Recommendation:

```text
Use: VFS Transition Compiler (VTC)
Do not introduce aliases for this component.
```

This document uses **VTC** for the compiler family that executes VFS transition rules.

Current implementation is partial but real:

- `VFSProfileCompiler` compiles profile expressions on the read/derived-variable path: AST parsing, dependency graph construction, topological sorting, cycle detection, and expression type checking.
- `VFSEvaluator` evaluates compiled profile variables in dependency order, with mark-and-sweep evaluation for observed variables plus dependencies and eager mode when all variables are needed.
- `VTCActionWriteProgram` executes the first write-path slice for `ActionConfig.writes`: parsed expressions, phase ordering, composition modes, clamps, conditions, active-agent masks, and atomic per-phase commit batches.
- Generated VTC programs own passive depletion, threshold cascades, affordance modulation, operating-hour gates, interaction progress, terminal checks, and the reward-component contract. (The reward slice is a *contract*: `VTCRewardProgram` validates the tensors and components the DAC engine returns against the declared contract; the reward math itself still lives in `DACEngine`.)
- `vtc_kernels.py` contains TorchScript kernels for generated hot transition paths: masked action-write commits, passive depletion, threshold cascades, linear affordance modulation, and terminal-condition checks. Arbitrary action-write expressions still evaluate through the typed expression AST before entering scripted tensor composition.
- Generated transition programs have no interpreter fallback helpers. Unsupported generated-rule forms fail loudly instead of silently routing through an old imperative executor.

The remaining VTC work is now scope expansion and hardening: full action write validation, occupancy and contention, relational/social scopes, dynamic variables, and telemetry side-effect compilation.

### 11.2 Why the compiler should cover transitions, not only actions

The current VTC action-write compiler handles declared action writes. That is useful but incomplete.

Townlet world physics also includes:

- passive decay,
- cascade effects,
- depletion modulations,
- time-of-day updates,
- operating-hour masks,
- multi-tick progress,
- interaction completion bonuses,
- occupancy and contention,
- terminal checks,
- reward components,
- lifecycle progression,
- social residue effects,
- and telemetry side effects.

If only action writes are compiled, the system risks becoming split:

```text
compiled actions
+ imperative legacy logic for everything else
```

The stronger target is:

```text
current VFS state
+ selected actions
+ world rules
→ next VFS state
+ observations
+ rewards
+ dones
+ telemetry
```

### 11.3 VTC architecture

Implemented pieces already cover the front half of this architecture for profile reads and the first action-write slice. The target architecture below is the full transition compiler, where all world updates share the same validated graph.

```text
World / Action / Rule Definitions (YAML)
    ↓
Expression Parser
    ↓
Type + Shape Inference
    ↓
Dependency Analysis
    ↓
Transition Phase Graph
    ↓
Tensor Operation Compiler
    ↓
Batched Execution
    ↓
Registry Updates + Rewards + Dones + Telemetry
```

### 11.4 Recommended transition phases

A full tick should eventually compile into an ordered phase graph:

```text
0. ingest_actions
1. advance_global_time
2. compute_action_legality_masks
3. apply_movement_and_wait_costs
4. resolve_affordance_access_and_occupancy
5. apply_action_costs
6. advance_interaction_progress
7. apply_action_effects
8. apply_completion_bonuses
9. apply_passive_depletion
10. apply_modulations
11. apply_threshold_cascades
12. apply_social_residue_effects
13. clamp_and_validate
14. evaluate_terminal_conditions
15. compute_rewards
16. emit_observation_features
17. emit_telemetry
```

The exact sequence can be tuned, but it must be explicit, configured, validated, and hashable. Execution order materially changes the world.

`clamp_and_validate` carries compiled bounds rules (`hamlet-f46e2b381a`): one
`bounds_clamp:<meter>` rule per declared meter, sourced from `bars.*.bounds`, compiled into
`VTCBoundsClampProgram`, hashed into `transition_graph_hash`, and dispatched by
`VTCTransitionRunner` at the already-scheduled slot after the effect-manager tick. It is the
end-of-transition invariant net — before it, an effect's `bar.*` write could carry a meter
past its declared bounds into terminal/reward/observation reads. The per-write clamps
(`action_executor`, `affordance_engine`, and the per-rule VTC clamps) are retained
deliberately (PDR-0014 B3 / PDR-0015): a mid-tick ceiling is semantic — a 0.5 ceiling with
`passive: 0.01` reads back 0.49, not 0.5 — and those sites die only when their write paths
migrate into VTC action writes, not before.

### 11.5 Remaining Phase 2 capabilities

The remaining Phase 2 compiler work should complete:

1. **Expression compilation**
   - Profile read expressions already parse, type-check, and evaluate through the VFS profile compiler/evaluator.
   - Action write expressions already parse and execute for selected actions.
   - Finish write-expression type/shape validation and generated/batched operations for all transition rule sources.

2. **Dependency resolution**
   - Profile variables already build a dependency graph, topologically sort, and reject cycles.
   - Extend dependency analysis across action writes, passive rules, cascades, temporal rules, reward components, and terminal checks.
   - Optimise full phase execution order for minimal memory overhead.

3. **Type checking**
   - Preserve existing profile-expression type checking.
   - Add full type checking for write expressions and cross-rule targets.
   - Ensure shape compatibility such as scalar + scalar, vector + vector, mask + tensor.
   - Reject invalid operations before runtime.

4. **Effect composition**
   - Resolve multiple writes to the same variable.
   - Support additive, multiplicative, overwrite, priority, min/max, and claim-style composition.
   - Apply atomic updates for consistency.

5. **Batched execution**
   - Apply rules to all agents in parallel.
   - Use masks for selected actions, active agents, occupancy winners, open affordances, and non-terminal agents.

6. **Telemetry generation**
   - Emit structured records for applied rules, vetoed writes, terminal triggers, reward components, and social side effects.

### 11.6 Example: compiling an interaction

Input YAML:

```yaml
- id: 5
  name: "INTERACT_BED"
  type: "interaction"
  reads: ["energy", "mood", "interaction_progress"]
  writes:
    - variable_id: "energy"
      expression: "energy + 0.3 * interaction_progress"
      composition: "overwrite"
    - variable_id: "mood"
      expression: "mood + 0.1 * interaction_progress"
      composition: "overwrite"
```

Compiled tensor operation, conceptually:

```python
@torch.jit.script
def execute_INTERACT_BED(registry: VariableRegistry, agent_mask: Tensor):
    # Read dependencies
    energy = registry.get("energy", reader="vtc")
    mood = registry.get("mood", reader="vtc")
    progress = registry.get("interaction_progress", reader="vtc")

    # Compute updates only for agents in mask
    new_energy = torch.where(
        agent_mask,
        energy + 0.3 * progress,
        energy,
    )
    new_mood = torch.where(
        agent_mask,
        mood + 0.1 * progress,
        mood,
    )

    # Write results
    registry.set("energy", new_energy, writer="vtc")
    registry.set("mood", new_mood, writer="vtc")
```

### 11.7 Phase 2 milestone plan

| Milestone | Description | Estimated Effort |
|---|---|---:|
| M1: Expression Parser | Parse arithmetic expressions and variable references | 2–3 days |
| M2: Type System | Static type checking and shape inference | 2–3 days |
| M3: Dependency Graph | Topological sort and circular dependency detection | 1–2 days |
| M4: Tensor Compiler | Generate PyTorch operations | 3–4 days |
| M5: Effect Composition | Multi-action conflict resolution | 2–3 days |
| M6: Optimisation | JIT compilation and memory optimisation | 2–3 days |
| M7: Integration Testing | End-to-end validation with training | 2–3 days |

Original estimated effort: 14–21 days. With the broadened transition-compiler scope, the first production compiler should still target action effects plus simple passive rules. Full transition unification should be staged.

### 11.8 Revised implementation phases

| Phase | Goal |
|---|---|
| 1.0 | VFS state and observation ABI, already complete |
| 1.5 | Shadow-mode equivalence against hardcoded observations |
| 2.0 | Compile action writes and simple masks |
| 2.1 | Compile passive decay and simple cascades |
| 2.2 | Compile temporal rules and multi-tick progress |
| 2.3 | Compile terminal conditions and reward components |
| 2.5 | Optimise, JIT, benchmark, and delete old imperative update paths |
| 3.0 | Add relational scopes for multi-agent social state |
| 3.5 | Add social residue effects and role-based visibility |
| 4.0 | Dynamic variables / variable-token observations |

---

## 12. Safe expression language

### 12.1 Avoid arbitrary Python

The VTC expression language must not evaluate arbitrary Python. It should be a small, typed, closed DSL.

Disallow:

```text
eval
exec
imports
reflection
attribute access to arbitrary objects
unregistered function calls
filesystem access
random runtime code generation
```

Allow a controlled operator set.

### 12.2 Recommended operator set

Arithmetic:

```text
+  -  *  /  abs  min  max  clamp
```

Comparison:

```text
<  <=  >  >=  ==  !=
```

Boolean:

```text
and  or  not  all  any
```

Tensor/mask:

```text
where
masked_add
masked_set
gather
scatter
one_hot
argmin
argmax
```

Spatial:

```text
distance
manhattan_distance
within_radius
nearest
```

Temporal:

```text
time_in_window
phase_sin
phase_cos
elapsed_ticks
```

Social / relational future operators:

```text
visible_to
observed_by
pair_value
group_value
claim_if_free
capacity_remaining
```

### 12.3 Expression examples

Passive depletion:

```yaml
- id: "energy_base_depletion"
  phase: "passive_depletion"
  reads: ["energy"]
  writes:
    - variable_id: "energy"
      expression: "energy - 0.005"
      composition: "overwrite"
      clamp: [0.0, 1.0]
```

Threshold cascade:

```yaml
- id: "low_satiation_hits_energy"
  phase: "threshold_cascades"
  reads: ["satiation", "energy"]
  condition: "satiation < 0.2"
  writes:
    - variable_id: "energy"
      expression: "energy - 0.015 * ((0.2 - satiation) / 0.2)"
      composition: "overwrite"
      clamp: [0.0, 1.0]
```

Temporal operating-hour gate:

```yaml
- id: "job_open_window"
  phase: "compute_action_legality_masks"
  reads: ["time_of_day"]
  writes:
    - variable_id: "job_is_open"
      expression: "time_in_window(time_of_day, 9, 18)"
      composition: "overwrite"
```

Interaction progress:

```yaml
- id: "advance_interaction_progress"
  phase: "advance_interaction_progress"
  reads: ["interaction_progress", "same_affordance", "affordance_is_open", "chosen_interact"]
  writes:
    - variable_id: "interaction_progress"
      expression: "where(same_affordance & affordance_is_open & chosen_interact, interaction_progress + 1, 0)"
      composition: "overwrite"
```

### 12.4 Ambient engine names (2026-08-25 note)

Profile expressions may reference one ambient engine-provided name without declaring it as a
variable: **`tick`** (float). It is admitted into the expression type schema but excluded from
dependency-graph edges (`AMBIENT_ENGINE_NAMES`, `vfs/profiles.py:35`; dependency exclusion at
`:124`). This was shipped-but-undocumented authoring surface until the 2026-08-24 audit
surfaced it; any extension of the ambient set is a design decision, not a call-site literal.

---

## 13. Effect composition and conflict resolution

### 13.1 Why composition matters

Multiple rules may write to the same variable in the same tick:

```text
movement drains energy
sleep restores energy
low mood drains energy
hunger drains energy
panic relocates position
movement also writes position
two agents attempt to claim the same bed
```

Conflict semantics must be explicit.

### 13.2 Recommended composition modes

| Composition mode | Meaning | Example |
|---|---|---|
| `overwrite` | Set target to expression result | `position = new_position` |
| `additive_delta` | Add expression as delta | `money += wage - cost` |
| `multiplicative_modifier` | Multiply current value | `health_decay *= fitness_factor` |
| `min` | Take minimum | Cap maximum access |
| `max` | Take maximum | Emergency stabilisation floor |
| `clamp` | Apply bounds after writes | Bars remain `[0,1]` |
| `priority_write` | Highest-priority writer wins | Panic relocation beats movement |
| `last_write_wins` | Later phase wins | Rare; use sparingly |
| `claim_if_free` | First valid claimant gets resource | Bed occupancy |
| `capacity_claim` | Up to N agents acquire slots | Hospital beds, queue slots |
| `append_event` | Add event to event buffer | Telemetry, messages, rumours |

The action-write VTC slice implements these advanced modes inside the normal
per-phase snapshot/accumulator boundary:

- `claim_if_free` writes only rows that are still free in the phase accumulator.
  Boolean rows are free when false; numeric/reference rows are free when every
  row element is negative, matching `-1` reference sentinels. Later same-phase
  claim writes therefore cannot overwrite an earlier successful claim.
- `capacity_claim` uses binary/numeric claim rows and requires `clamp` with an
  integer high value declaring the total capacity for that write. Rows already
  greater than zero count against capacity, and remaining eligible claimants are
  accepted deterministically in action-batch order without over-allocation.
- `append_event` targets bounded event buffers shaped `[agents, event_slots, ...]`.
  The expression must produce either a scalar payload or `[agents, ...]`; the
  VTC appends into the first zero/false slot for each selected active agent and
  leaves full buffers unchanged.

Affordance occupancy uses the same action-write machinery with source-affordance
row targeting. `compile_vtc_affordance_occupancy(...)` resolves each
`source_affordance` to an affordance-scope row before runtime, exposes `agent_id`
as an action-batch payload expression, and applies writes scheduled in
`resolve_affordance_access_and_occupancy` as deterministic contention:

- `claim_if_free` writes the first active claimant's payload into the targeted
  affordance row only when the row is still free.
- `capacity_claim` targets `[affordances, slots, ...]` storage, requires an
  integer `clamp` high value declaring capacity, and fills the first free slots
  with active claimants in action-batch order without over-allocation.

**Wiring status (2026-08-21, second pass).** Wired end-to-end (hamlet-ef6699ab2a).
`build_vtc_transition_schedule` compiles ALL action writes through
`compile_vtc_affordance_occupancy_with_phase_graph`, so any action carrying a
`source_affordance` gets its claim writes bound to that affordance's registry row.
The authoring surface is `actions.yaml`: a custom action declares `source_affordance`
plus `writes` (WriteSpec entries); claim compositions without a `source_affordance`
are rejected at parse, unknown affordances and unknown write targets are rejected at
compile. `env.step` executes the writes in `resolve_affordance_access_and_occupancy`
through the generic VTC runner. Config-in/behaviour-out coverage:
`tests/test_townlet/unit/vfs/test_occupancy_wiring.py` (two agents contending for a
capacity-1 affordance resolve deterministically through a real `env.step`).

### 13.3 Example

```yaml
writes:
  - variable_id: "health"
    expression: "0.25"
    composition: "additive_delta"
    phase: "action_effects"

  - variable_id: "position"
    expression: "hospital_position"
    composition: "priority_write"
    priority: 100
    phase: "emergency_relocation"

  - variable_id: "money"
    expression: "-ambulance_cost"
    composition: "additive_delta"
    phase: "action_costs"

  - variable_id: "affordance_occupancy"
    expression: "agent_id"
    composition: "claim_if_free"
    phase: "resolve_affordance_access_and_occupancy"
```

### 13.4 Atomic update semantics

Within a phase, the compiler should distinguish:

```text
read snapshot variables
compute all writes
resolve conflicts
commit writes atomically
```

This prevents one rule from accidentally seeing another rule’s partial update unless the phase ordering explicitly allows it.

The action-write VTC path implements this as a mechanical boundary: one phase
snapshot feeds all write-mask and expression evaluation, candidate tensors are
validated against their target shape, composition resolves against a phase
accumulator, and the completed accumulator becomes visible only to the next
phase.

---

## 14. Relationship operators

### 14.1 Relationships as operator classes

Relationships can be more than simple value deltas. A relationship can:

```text
A drains B
A gates B
A delays B
A unlocks B
A masks B
A modifies B's rate
A changes B only if a threshold is crossed
A changes B only during a time window
A changes B only while action is sustained
A changes B only if another agent observes it
A changes B only if an affordance has capacity
A changes B only if a norm applies
```

### 14.2 Core relationship types

| Type | Description | Example |
|---|---|---|
| `depletion` | Passive reduction over time | hygiene decays per tick |
| `modulation` | Source changes target rate | fitness modifies health decay |
| `threshold_delta` | Penalty/bonus once source crosses threshold | low satiation hits health |
| `temporal_gate` | Time controls availability | job open 09:00–18:00 |
| `capacity_gate` | Affordance use limited by occupancy | one bed user only |
| `progress_accumulator` | Multi-tick commitment | sleep progress |
| `completion_bonus` | Reward after sustained progress | work shift bonus |
| `terminal_condition` | Ends run or marks state | health <= 0 |
| `reward_component` | Adds reward term | retirement score |
| `visibility_effect` | Observation changes social state | theft witnessed by neighbour |
| `social_residue` | Action leaves relationship/norm effect | debt, trust loss, reputation gain |
| `communication_event` | Message or symbol update | broadcast token |
| `institutional_rule` | Rule alters legality/sanction | ambulance abuse penalty |

### 14.3 RelationshipSpec proposal

```yaml
rules:
  - id: "low_social_hits_mood"
    phase: "threshold_cascades"
    kind: "threshold_delta"
    reads: ["social", "mood"]
    condition: "social < 0.2"
    writes:
      - variable_id: "mood"
        expression: "mood - 0.010 * ((0.2 - social) / 0.2)"
        composition: "overwrite"
        clamp: [0.0, 1.0]
```

Social residue example, in the shipped `transition_rules.yaml` grammar
(pack root; schema `townlet.config.transition_rules_config.TransitionRulesConfig`,
`extra="forbid"` — `condition`, `clamp`, `effect`, `scope` are required-nullable
per the No-Defaults Principle):

```yaml
version: "1.0"
social_residue:
  - id: "seen_stealing_damages_trust"
    phase: "apply_social_residue_effects"
    kind: "visibility_effect"
    reads: ["chosen_action", "observer_mask", "trust"]
    condition: "observer_mask and chosen_action == STEAL"
    writes:
      - variable_id: "trust"
        effect: "trust_delta"
        scope: "pair"
        expression: "-0.15"
        composition: "additive_delta"
        condition: null
        clamp: [0.0, 1.0]
```

Institutional rule example:

```yaml
version: "1.0"
social_residue:
  - id: "ambulance_abuse_social_penalty"
    phase: "apply_social_residue_effects"
    kind: "institutional_rule"
    reads: ["chosen_action", "health", "mood", "public_reputation"]
    condition: "chosen_action == CALL_AMBULANCE and health >= 0.7 and mood >= 0.8"
    writes:
      - variable_id: "public_reputation"
        effect: "reputation_delta"
        scope: "agent"
        expression: "-0.10"
        composition: "additive_delta"
        condition: null
        clamp: [0.0, 1.0]
```

### 14.4 Modulation rules are narrower than these examples (2026-08-25 caveat)

⚠ The `RelationshipSpec` examples above show `condition:` freely, but the shipped
**modulation** family does not support it: a modulation rule carrying any `condition:`, or any
composition other than `multiplicative_modifier`, **compiles green and raises
`NotImplementedError` at the first `env.step`**
(`vtc.py:1165-1168`, `compute_affordance_multiplier` — the scripted-kernel path covers only
the one composition it was written for). This violates the project's fail-loud-at-compile
discipline and was flagged as a new finding in the 2026-08-24 audit
(`archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md`, "Fail-at-runtime seams"); until it
is fixed at compile time, treat conditioned modulations as unauthorable.

---

## 15. Software-defined needs

### 15.1 Bars are variables, not the whole ontology

The current eight canonical bars are a stable baseline ABI for early worlds:

```text
energy
hygiene
satiation
money
mood
social
health
fitness
```

VFS allows these to be represented as config-defined variables, but the long-term design should not treat them as the only possible needs.

A need can be modelled as a variable with causal metadata:

```yaml
- id: "N_042"
  type: "scalar"
  scope: "agent"
  range: [0.0, 1.0]
  initial: 0.0
  readable_by: ["agent", "engine"]
  writable_by: ["engine", "vtc"]
  metadata:
    tags: ["need", "recurring", "socially_visible", "status_mediated", "mimetic"]
    growth: "triggered_by_observation"
    satisfaction_selector: ["displayable", "peer_recognised"]
```

The agent does not need to know that `N_042` means “fashion novelty” or “makeup desire”. It needs to learn:

```text
this variable grows under certain observations
this class of affordance reduces it
reduction depends on visibility
satisfaction may affect reputation
attempts cost money
norms may judge it
```

### 15.2 Need dimensions

Dynamic needs should be describable by causal dimensions rather than human labels:

| Dimension | Meaning |
|---|---|
| `intensity` | Current pressure |
| `growth_rate` | How fast pressure increases |
| `urgency` | How soon action is required |
| `recurrence` | Whether the need returns |
| `substitutability` | Whether multiple affordance classes satisfy it |
| `exclusivity` | Whether one agent’s satisfaction blocks another’s |
| `visibility` | Whether satisfaction is observed |
| `status_value` | Whether satisfaction affects rank/reputation |
| `social_mediation` | Whether another agent is required |
| `contagion` | Whether observing satisfaction creates similar need |
| `catastrophe_curve` | What happens if unmet |
| `dependency` | Whether satisfying it creates future reliance |
| `satisfaction_tags` | Affordance tags that can resolve it |

### 15.3 Dynamic variable strategy

There are two approaches:

1. **Fixed dynamic slots**

```yaml
dynamic_needs:
  max_slots: 16
  representation: "fixed_slots"
  fields:
    - intensity
    - growth_rate
    - urgency
    - recurrence
    - substitutability
    - visibility
    - status_value
    - social_mediation
    - contagion
    - catastrophe_curve
```

2. **Variable-token / set-encoder representation**

```yaml
dynamic_needs:
  max_slots: 32
  representation: "set_encoder"
  token_fields:
    - id_embedding
    - intensity
    - growth_rate
    - urgency
    - tag_embedding
    - satisfaction_embedding
```

Fixed slots are easier for checkpoint compatibility. Token/set representations are more flexible and better for arbitrary software-defined needs.
The repo exposes option 1 as `canonical_fixed_slot_dynamic_need_variables(max_slots)`.
It returns one agent-scoped `vecNf` variable per causal field, with `dims=max_slots`
so storage and observations stay shape-stable while individual slots can represent
abstract software-defined needs.
The repo exposes option 2 as `canonical_set_encoder_dynamic_need_variables(...)`,
which creates an agent-scoped `dynamic_need_tokens` `tensor2d` variable shaped as
`[max_slots, token_width]`. `dynamic_need_token_layout(...)` defines the token
field offsets for `id_embedding`, `intensity`, `growth_rate`, `urgency`,
`tag_embedding`, and `satisfaction_embedding`. `SetEncoderQNetwork` can reshape
the flattened observation field back into token rows and mean-pool non-empty rows,
so token order does not become part of the learned meaning.

The runtime registry now also exposes a deliberately gated dynamic-variable
mode for experiments that truly add/remove variable definitions during a run.
This mode is off by default. Enabling it does not hide the network-shape
consequence: each mutation must declare whether it is
`shape_stable_internal` or `observation_schema_changed`, and observable
variables require the latter.

### 15.4 Experiment enabled by VFS

A clean research experiment:

```text
Train worlds:
    random variable names
    stable operator grammar
    varied surface affordance labels
    shared causal profiles

Test worlds:
    unseen variable names
    unseen affordance labels
    held-out relationship combinations
    same underlying operator types
```

If the agent generalises, it is learning relationship structure rather than labels.

Repo support for this experiment lives in `townlet.vfs.generalisation`:

- `VFSGeneralisationPack` groups the variable, affordance, and rule surfaces for
  one train or test pack.
- `build_vfs_generalisation_signature(...)` turns those surfaces into a
  deterministic signature that erases variable names and affordance labels while
  retaining causal fields, expression operators, constants, phases, and
  composition modes.
- `assert_held_out_generalisation_split(train, test)` fails if train and test
  reuse variable names or affordance labels, or if their surface-erased causal
  profiles / operator grammars drift apart.
- `operator_grammar_signature(expression)` exposes the expression-level check
  for smaller assertions and diagnostics.

---

## 16. Social-state modelling

### 16.1 From social meter to relationship graph

A scalar `social` meter can model loneliness or social deficit. It cannot fully model:

```text
I trust Alice but fear Bob.
I owe rent to the landlord.
The hospital is occupied.
My family shares food access.
This group punishes norm violations.
That agent saw me steal.
```

For small-society simulation, social state should include:

```text
agent internal social need
pairwise relationships
public reputation
group membership
group norms
institutional rules
observation / witness state
communication messages
```

### 16.2 Suggested relational variables

```yaml
variables:
  - id: "trust"
    type: "scalar"
    scope: "pair"
    range: [0.0, 1.0]
    initial: 0.5
    readable_by: ["engine", "social_model"]
    writable_by: ["vtc"]

  - id: "obligation"
    type: "scalar"
    scope: "pair"
    range: [0.0, 1.0]
    initial: 0.0
    readable_by: ["engine", "social_model"]
    writable_by: ["vtc"]

  - id: "public_reputation"
    type: "scalar"
    scope: "agent"
    range: [0.0, 1.0]
    initial: 0.5
    readable_by: ["agent", "other_agents", "social_model", "engine"]
    writable_by: ["vtc"]

  - id: "norm_legitimacy"
    type: "scalar"
    scope: "group"
    range: [0.0, 1.0]
    initial: 0.5
    readable_by: ["engine", "social_model"]
    writable_by: ["vtc"]
```

The repo exposes this canonical set as `canonical_l5_relational_variables()`,
returning `VariableDef` records for storage allocation and schema hashing. Pair
and group extents remain explicit: callers allocate storage with the relevant
`num_agents` and `num_groups` instead of relying on hidden default groups.

### 16.3 Social residue effect types

The VTC social-residue compiler accepts `visibility_effect`, `social_residue`,
and `institutional_rule` relationship rules in the canonical
`apply_social_residue_effects` phase. Rule-level conditions and write-level
conditions are combined before commit. Pair-scope writes are masked by the
symmetric active-agent mask (`active[i] & active[j]`); observer→actor
directionality is encoded by the author inside `condition` / `expression`
via pair-scope data (e.g. an `[observer, actor]` observer mask), and a
pair write conditioned on such a mask moves `trust[i, j]` without touching
`trust[j, i]`. The former write-level `target` role annotation
(e.g. `observer -> actor`) was removed 2026-08-22 (hamlet-175bff4ed5): it was
stored but never consumed, and a role string carries no data a directed mask
could be derived from — direction lives in the declared reads. Configs that
set `target` are rejected at compile time. If a first-class directional
grammar returns, it belongs to the authoring-surface DTO design
(hamlet-84cf93a1b9), with roles bound to declared reads.
Agent-scope writes use agent vectors such as `chosen_action` or derived
visibility vectors such as `was_observed`. As with other VTC writes,
`additive_delta` expressions are deltas, not post-update values.

The authoring surface is a pack-root `transition_rules.yaml` with a
`social_residue:` list, validated at load by the no-defaults DTO
`townlet.config.transition_rules_config.TransitionRulesConfig`
(`extra="forbid"`: a stray or typo'd key fails at parse; `condition`, `clamp`,
`effect`, and `scope` must be set explicitly, `null` included) and compiled by
the universe compiler through `compile_vtc_social_residue_rules` into the
transition schedule. The compiler and the `apply_social_residue_effects` phase
are wired into `env.step`'s executed phase range;
`tests/test_townlet/integration/test_vtc_transition_schedule_runtime.py`
proves a declared rule mutates a pair-scope variable during `env.step`. No
shipped pack declares rules yet, so current scenarios still compile an empty
rule set (see §21.1, item 7).

⚠ **Composition coverage (2026-08-24 audit, re-verified 2026-08-25):** the social-residue
executor supports **8 of the 11** §13.2 composition modes. `claim_if_free`,
`capacity_claim`, and `append_event` validate at the schema layer
(`transition_rules_config.py` mirrors all 11) but raise `NotImplementedError` at execution
(`vtc.py:1606-1607`) — another compile-green/runtime-crash seam. A contested-claim or
witnessed-event social rule cannot currently use claim-style composition; nothing warns the
author until the first `env.step`.

| Effect | Description |
|---|---|
| `trust_delta` | Increase/decrease directed trust |
| `fear_delta` | Increase/decrease directed fear |
| `obligation_create` | Create debt/favour relation |
| `obligation_discharge` | Clear debt/favour relation |
| `reputation_delta` | Change public reputation |
| `status_signal` | Emit status-bearing signal |
| `shame_signal` | Emit norm-violation signal |
| `norm_reinforce` | Strengthen perceived norm |
| `norm_violate` | Weaken or challenge perceived norm |
| `imitation_seed` | Increase chance other agents develop similar need |
| `gossip_event` | Add event to communication/rumour buffer |

### 16.4 Example: helping another agent

```yaml
version: "1.0"
social_residue:
  - id: "help_creates_obligation_and_reputation"
    phase: "apply_social_residue_effects"
    kind: "social_residue"
    reads: ["chosen_action", "recipient_actor_mask", "was_observed", "public_reputation", "obligation"]
    condition: "chosen_action == HELP"
    writes:
      - variable_id: "obligation"
        effect: "obligation_create"
        scope: "pair"
        condition: "recipient_actor_mask"
        expression: "0.20"
        composition: "additive_delta"
        clamp: [0.0, 1.0]
      - variable_id: "public_reputation"
        effect: "reputation_delta"
        scope: "agent"
        condition: "was_observed"
        expression: "0.05"
        composition: "additive_delta"
        clamp: [0.0, 1.0]
```

---

## 17. Migration path: hardcoded to VFS-driven environment

> **Corrected 2026-08-21.** This migration is complete. The environment is fully VFS-driven;
> the hardcoded path in §17.1 and the shadow system of Phase 1.5 were deleted. The section is
> kept as the record of what was replaced and why; per-phase status is marked below.

### 17.1 Pre-migration hardcoded observation generation (historical)

Before the cutover, `VectorizedHamletEnv` used hardcoded concatenation:

```python
def _get_observations(self):
    # Hardcoded substrate encoding
    substrate_obs = self.substrate.get_observation(...)  # 66 dims for L1

    # Hardcoded meters
    meter_values = torch.stack([
        self.meters["energy"],
        self.meters["health"],
        # ... 8 meters total
    ], dim=-1)  # 8 dims

    # Hardcoded affordance at position
    affordance_one_hot = self._get_affordance_at_position()  # 15 dims

    # Hardcoded temporal features
    time_features = torch.stack([
        self.time_sin,
        self.time_cos,
        self.interaction_progress,
        self.lifetime_progress,
    ], dim=-1)  # 4 dims

    # Concatenate (66 + 8 + 15 + 4 = 93 dims for L1)
    return torch.cat([substrate_obs, meter_values, affordance_one_hot, time_features], dim=-1)
```

Problems:

- Observation dimension calculation is scattered.
- Checkpoint compatibility is hard to verify.
- Adding/removing observations requires code changes.
- Dependency tracking is unclear.
- Observability curriculum is harder to configure.

### 17.2 Shipped VFS-driven observation generation

```python
def _initialize_vfs(self):
    """Initialize VFS registry and observation spec once at startup."""
    # Use the compiled universe artifact. The compiler has already loaded
    # vfs_profiles.yaml and the optional variables_reference.yaml static overlay.
    variables = self.compiled_universe.vfs_variables
    obs_fields = self.compiled_universe.vfs_observation_fields

    # Initialize registry
    self.registry = VariableRegistry(
        variables=variables,
        num_agents=self.num_agents,
        device=self.device,
    )

    # Use the compiled observation layout and VFS contribution dimensions.
    self.obs_fields = obs_fields
    self.vfs_obs_spec = self.compiled_universe.vfs_observation_spec

    # Validate dimension
    obs_dim = self.compiled_universe.observation_spec.total_dims
    assert obs_dim == self.expected_obs_dim, \
        f"VFS dimension mismatch! Expected {self.expected_obs_dim}, got {obs_dim}"


def _get_observations(self):
    """Generate observations from VFS registry."""
    obs_tensors = []

    for field in self.obs_fields:
        value = self.registry.get(field.source_variable, reader="agent")

        if field.normalization:
            value = self._apply_normalization(value, field.normalization)

        if len(value.shape) == 1:
            value = value.unsqueeze(-1)

        obs_tensors.append(value)

    return torch.cat(obs_tensors, dim=-1)
```

Benefits:

- Observation dimension calculated at compile time.
- Declarative configuration controls exposure.
- Dependency tracking is explicit.
- Checkpoint compatibility is regression-tested.
- Curriculum can alter observability without changing Python.

This is now the only path. In the shipped implementation
(`src/townlet/environment/observation_encoder.py`), `ObservationEncoder._get_observations`
iterates `observation_spec.fields`; engine-computed features (grid, local window, position,
velocity, meters, affordance-at-position, effects, temporal, item slots) are published into
the VFS registry through a dispatch table keyed on each field's `feature` — never its name
(`PDR-0045`) — before the per-field loop reads them back. The code above is illustrative; no
hardcoded concatenation or shadow path remains in the tree.

### 17.3 Migration strategy

#### Phase 1.5: Parallel/shadow systems — completed, then dismantled

1. Keep current hardcoded observations in production.
2. Add VFS observation generation as a shadow system.
3. Compare outputs for equivalent configs.
4. Validate dimension compatibility.
5. Run training experiments with both systems.
6. Store observation schema hash in telemetry.

#### Phase 2.0: Initial compiler integration — completed

1. Replace hardcoded observation generation with VFS.
2. Compile simple action writes.
3. Keep old meter update logic for non-action world physics.
4. Run equivalence tests.

#### Phase 2.1–2.3: Transition unification — completed (rewards run through the VTC contract; the math stays in `DACEngine`, §11.1)

1. Move passive depletion into VTC.
2. Move cascades and modulations into VTC.
3. Move temporal gates and multi-tick progress into VTC.
4. Move terminal conditions and reward components into VTC.

#### Phase 2.5: Optimisation and cutover — largely completed (kernels scripted, fallbacks deleted, benchmark guardrail in place)

1. Profile registry get/set overhead.
2. Cache static observation fields.
3. JIT compile hot transition paths. Current scripted kernels cover generated passive depletions, threshold cascades, linear modulations, terminal checks, and masked action-write commits.
4. Benchmark against hardcoded baseline.
5. Delete old imperative paths after equivalence is proven. Generated transition interpreter fallbacks are removed; equivalence evidence remains as tests.

#### Phase 3+: Social/relational expansion — storage landed, wiring open (§5.1, §16.3)

1. Add pair/group/affordance/zone scopes. Dense and sparse runtime storage now exists; VTC relational rule coverage follows separately.
2. Add social residue rules. **Done 2026-08-22**: authorable via pack-root `transition_rules.yaml` (§16.3).
3. Add communication variables.
4. Add dynamic needs or variable-token observations.

---

## 18. Provenance, hashes, and run identity

### 18.1 Why VFS must be hashed

Brain as Code already treats a mind as a snapshot plus compiled cognitive graph. VFS must participate in the same provenance boundary.

Changing any of these can change behaviour:

```text
variable definitions
variable scopes
read/write permissions
observation exposures
normalisation rules
action definitions
compiled transition phases
relationship rules
terminal conditions
reward components
```

Even with identical neural weights, these are different experimental objects:

```text
same weights + health exact
same weights + health noisy
same weights + health hidden
same weights + money visible
same weights + money hidden
```

### 18.2 Recommended hashes

| Hash | Contents | Purpose |
|---|---|---|
| `variable_schema_hash` | Variable definitions, scopes, types, permissions | State ABI identity |
| `observation_schema_hash` | Ordered observation fields and normalisation | Checkpoint compatibility |
| `action_schema_hash` | Action IDs, names, masks, dependencies | Policy/action-space compatibility |
| `transition_graph_hash` | Compiled rules, phases, expressions, composition | World physics identity |
| `vfs_hash` | Combined VFS schema + observation + action + transition hashes | VFS identity |
| `run_hash` / `cognitive_hash` extension | Brain configs + world configs + VFS hash | Mind-in-world identity |

One deliberate-or-not boundary worth knowing (2026-08-24 audit, unadjudicated):
`variable_schema_hash` covers id/type/scope/dims/lifetime/access/normalization range
(`schema_hashes.py:140-150`) but **not** a variable's `default`/initial value — an author can
change every initial value in a pack with zero movement in `variable_schema_hash`/`vfs_hash`.
Whether initial values are part of the ABI is a product call that has not been made; do not
assume provenance catches default drift.

### 18.3 Snapshot layout

Recommended run bundle:

```text
configs/<run_name>/
  actions.yaml
  brain.yaml
  environment.yaml
  experiment.yaml
  items.yaml
  stratum.yaml
  vfs_profiles.yaml
  effects.yaml
  variables_reference.yaml  # optional static variable and observation metadata overlay
  levels/<level_name>/
    curriculum.yaml
    bars.yaml
    affordances.yaml
    drive.yaml
    training.yaml
    items.yaml              # optional level appearance state
  transition_rules.yaml
  cognitive_topology.yaml
  agent_architecture.yaml
  execution_graph.yaml
```

Snapshot:

```text
runs/<run_name>__<timestamp>/
  config_snapshot/
    actions.yaml
    brain.yaml
    environment.yaml
    experiment.yaml
    items.yaml
    stratum.yaml
    vfs_profiles.yaml
    effects.yaml
    variables_reference.yaml  # optional static variable/metadata overlay if present in the source pack
    levels/
    transition_rules.yaml
    cognitive_topology.yaml
    agent_architecture.yaml
    execution_graph.yaml
  compiled/
    observation_spec.json
    action_spec.json
    transition_graph.json
    hashes.json
  checkpoints/
  telemetry/
  logs/
```

### 18.4 Resume rule

Resume must use checkpoint snapshot and compiled specs, not mutable live configs.

If any VFS component changes, the run is a fork, not a continuation.

The shipped gate (verified 2026-08-25): both checkpoint consumers — `DemoRunner` (training
resume) and `LiveInferenceServer` (serving) — route through the shared
`assert_checkpoint_identity()` (`training/checkpoint_utils.py:224`), which composes the
format-version check, `assert_checkpoint_vfs_hash()` (`:197`), the dimension/field-UUID/
`drive_hash`/`brain_hash`/per-level content-hash checks, and the `primary_level` equality
check. A `vfs_hash` mismatch fails resume unless the caller explicitly requests a new VFS
branch with `force_new_vfs`; every other identity mismatch fails loudly with no override.

---

## 19. Testing and validation

### 19.1 Existing Phase 1 tests

Unit tests:

```bash
# Schema validation
uv run pytest tests/test_townlet/unit/vfs/test_schema.py -v

# Registry operations
uv run pytest tests/test_townlet/unit/vfs/test_registry.py -v

# Observation builder
uv run pytest tests/test_townlet/unit/vfs/test_observation_builder.py -v

# Dimension regression (critical)
uv run pytest tests/test_townlet/unit/vfs/test_observation_dimension_regression.py -v
```

Integration tests:

```bash
# End-to-end pipeline
uv run pytest tests/test_townlet/integration/vfs/test_variable_to_observation_flow.py -v

# Runtime evaluation
uv run pytest tests/test_townlet/integration/test_vfs_runtime_evaluation.py -v

# Full VFS suite
uv run pytest tests/test_townlet/unit/vfs/ tests/test_townlet/integration/vfs/ -v
```

### 19.2 VTC tests

> **Corrected 2026-08-21.** The file names previously listed here were the planned names;
> the suites landed under different names. The commands below are the ones that exist.

Compiler and expression tests:

```bash
uv run pytest tests/test_townlet/unit/vfs/test_expression_integration.py -v
uv run pytest tests/test_townlet/unit/vfs/test_expression_spatial.py tests/test_townlet/unit/vfs/test_expression_temporal.py tests/test_townlet/unit/vfs/test_expression_noise.py -v
uv run pytest tests/test_townlet/unit/vfs/test_vfs_evaluator.py -v
uv run pytest tests/test_townlet/unit/vfs/test_transition_graph.py -v
uv run pytest tests/test_townlet/unit/vfs/test_vtc_action_writes.py -v
```

Per-domain VTC rule tests (these carry the equivalence coverage):

```bash
uv run pytest tests/test_townlet/unit/vfs/test_vtc_passive_depletions.py tests/test_townlet/unit/vfs/test_vtc_threshold_cascades.py tests/test_townlet/unit/vfs/test_vtc_modulations.py -v
uv run pytest tests/test_townlet/unit/vfs/test_vtc_affordance_gates.py tests/test_townlet/unit/vfs/test_vtc_interaction_progress.py -v
uv run pytest tests/test_townlet/unit/vfs/test_vtc_terminal_conditions.py tests/test_townlet/unit/vfs/test_vtc_reward_components.py -v
uv run pytest tests/test_townlet/unit/vfs/test_vtc_passive_dynamics_equivalence.py -v
```

Provenance tests:

```bash
uv run pytest tests/test_townlet/unit/vfs/test_schema_hashes.py -v
uv run pytest tests/test_townlet/integration/test_checkpointing.py tests/test_townlet/integration/test_content_hash_checkpoint_guard.py -v
```

Multi-agent tests:

```bash
uv run pytest tests/test_townlet/unit/vfs/test_relational_variables.py tests/test_townlet/unit/vfs/test_message_variables.py -v
uv run pytest tests/test_townlet/unit/vfs/test_vtc_affordance_occupancy.py -v
uv run pytest tests/test_townlet/unit/vfs/test_vtc_social_residue.py -v
uv run pytest tests/test_townlet/integration/test_l5_multi_agent_config.py -v
```

### 19.3 Behavioural equivalence tests

When migrating old environment logic into VFS/VTC, preserve legacy behaviour unless explicitly changing it.

Test pattern:

```text
Given same initial state
and same action sequence
and same config pack
old imperative engine and VTC engine should produce equivalent:
    variables
    rewards
    done flags
    legality masks
    telemetry-critical events
within tolerance
```

Equivalence should cover:

- base depletion,
- cascade order,
- health decay modulation,
- multi-tick progress,
- operating-hour masks,
- affordability failure,
- hospital/doctor/ambulance effects,
- terminal conditions,
- lifecycle and retirement semantics.

### 19.4 Property tests

Useful invariants:

```text
normalised variables stay in range after clamp
terminal agents do not continue changing unless explicit post-terminal mode is enabled
unauthorised reads fail
unauthorised writes fail
observation dimensions match spec
compiled and interpreted expressions agree
transition graph hash changes when rule order changes
same snapshot gives same schema hashes
capacity_claim never over-allocates affordance capacity
pair-scope trust[i,j] may differ from trust[j,i]
```

### 19.5 Performance benchmarks

```python
# Benchmark registry access
def benchmark_registry_get(registry, iterations=10000):
    start = time.time()
    for _ in range(iterations):
        value = registry.get("energy", reader="agent")
    elapsed = time.time() - start
    print(f"Registry get: {elapsed / iterations * 1e6:.2f} µs/call")

# Benchmark observation generation
def benchmark_observation_generation(env, iterations=1000):
    start = time.time()
    for _ in range(iterations):
        obs = env._get_observations()
    elapsed = time.time() - start
    print(f"Observation generation: {elapsed / iterations * 1e3:.2f} ms/call")
```

Additional VTC benchmarks:

```python
def benchmark_transition_step(env, iterations=1000):
    start = time.time()
    for _ in range(iterations):
        actions = env.sample_actions()
        env.step(actions)
    elapsed = time.time() - start
    print(f"VTC env.step: {elapsed / iterations * 1e3:.2f} ms/call")
```

Implemented guardrail:

```bash
uv run pytest tests/test_townlet/performance/test_vtc_jit_kernels.py -q
```

This compares the scripted threshold-cascade kernel against the equivalent hardcoded tensor equation and fails if scripted execution exceeds the configured tolerance (`SCRIPTED_KERNEL_TOLERANCE = 1.50`).

---

## 20. Best practices

### 20.1 Checkpoint compatibility

Always run dimension regression tests before committing variable or exposure changes:

```bash
uv run pytest tests/test_townlet/unit/vfs/test_observation_dimension_regression.py -v
```

If tests fail:

- fix the variable/exposure change,
- create a new config version and treat existing runs as forks,
- or document the intentional breaking change and update all in-repo references.

### 20.2 Stable IDs

Do not rename variable IDs casually. A rename is usually a schema break.

Use:

```yaml
id: "satiation"
label: "Food level"
```

Rather than treating `id` as presentation text.

### 20.3 Types

Prefer compact and semantically correct types:

```yaml
# Good: integer coordinates for grid positions
- id: "grid_position"
  type: "vec2i"
  dims: 2

# Less good: float vector for discrete coordinates
- id: "grid_position"
  type: "vecNf"
  dims: 2
```

Suggested type set:

```text
scalar
bool
int
categorical
vec2i
vec2f
vecNf
one_hot
mask
matrix
message_token
```

### 20.4 Access control

Only grant required permissions.

Use role-specific readers/writers:

```text
agent
other_agents
engine
vtc
renderer
world_model
social_model
ethics_filter
panic_controller
doctor_role
auditor
```

Avoid broad permissions such as `*` except in debug tooling.

### 20.5 Observation dimensions

Treat observation dimensions as an ABI.

Any change to field count, order, shape, or normalisation must be considered checkpoint-relevant.

### 20.6 Transition rule safety

- Use a closed DSL.
- Reject unknown functions.
- Reject circular dependencies.
- Require explicit composition mode.
- Require explicit transition phase.
- Hash compiled graphs.
- Prefer debug-mode runtime assertions until the compiler matures.

### 20.7 Social effects

Social effects should not be hidden inside action handlers.

Prefer explicit rules (`transition_rules.yaml`):

```yaml
version: "1.0"
social_residue:
  - id: "public_help_increases_reputation"
    phase: "apply_social_residue_effects"
    kind: "social_residue"
    reads: ["was_observed", "public_reputation"]
    condition: "was_observed"
    writes:
      - variable_id: "public_reputation"
        effect: "reputation_delta"
        scope: "agent"
        expression: "0.05"
        composition: "additive_delta"
        condition: null
        clamp: [0.0, 1.0]
```

This keeps social meaning inspectable and teachable.

### 20.8 Derived features

Do not store every computed quantity as a variable. Use `FeatureDef` for derived observations where possible.

Store state when it must persist or be authoritative. Derive features when they are observation conveniences.

### 20.9 Extension recipes

Condensed from the archived implementation overview
(`archive/vfs-current-implementation.md`, "How To Extend VFS Safely"), with the current
caveats bound in:

**Add a static runtime variable** (`variables_reference.yaml`): keep it static (no
expressions); set explicit `readable_by`, `writable_by`, `lifetime`, `scope`, and default;
declare the matching `extents:` entry for zone/group/message/affordance scopes (§5.1). ⚠ Know
the door you are using: this is the only surface where `readable_by`/`writable_by`/`lifetime`
are author-settable, and its variables are invisible to the compiler symbol table — no effect,
affordance, action write, or `drive.yaml` can reference them (§5.1 caveat,
`hamlet-33e520cebd`).

**Add a derived profile variable** (`vfs_profiles.yaml`): choose global/agent/item profile
scope; provide exactly one initialization source (`initial_value` / `initial_value_mode` /
`expression` — item profiles refuse `expression` at compile); the profile compiler parses,
type-checks, and topologically sorts dependencies. If it should be observed, declare
`exposed_to` and `semantic_type` — and remember `exposed_to: []` currently fails open to
`["agent"]` (§5.3 caveat).

**Add a new transition rule family** (`vtc.py`): compile source config into immutable
`CompiledVTC...` records with parsed expression ASTs; sort by
`TransitionPhaseGraph.sort_key()`, priority, stable tiebreaker; execute with
read-snapshot/commit-batch phase semantics (§13.4); include the family in
`canonical_transition_graph_schema()` / `compute_transition_graph_hash()`; test compilation,
execution, hash movement, and failure modes. Refuse unsupported rule shapes at **compile**
time — §14.4 and §16.3 document the two families that currently get this wrong.

**Add runtime dynamic variables**: construct `VariableRegistry(dynamic_variable_mode=True)`
and follow §7.2's `network_shape_effect` contract; treat the post-mutation schema
hash/generation as a new ABI identity.

---

## 21. Known limitations

### 21.1 Phase 1 limitations

1. **Remaining VTC coverage gaps.** Profile reads, action writes, passive dynamics, cascades, temporal gates, interaction progress, rewards, terminal checks, occupancy/contention, and social residue rules now run through VFS/VTC components. Remaining gaps are action-write type/shape validation depth, telemetry side-effect compilation, relational observation exposure, environment-level social-rule wiring, message observation/runtime communication wiring, and dynamic variables.
2. **Manual observation generation.** Observation construction still requires explicit registry reads and concatenation.
3. **Partial write validation.** `WriteSpec` expressions are parsed and executed for action writes, but full write-path type/shape validation is still incomplete.
4. **Compile-time write-shape validation is still missing** (narrowed 2026-08-25). The runtime half of this item is discharged: `set_engine_value()` now enforces the declared element shape for every variable (`hamlet-d970ef83f0`, §7.2), so storage can no longer drift from the declared schema. What remains is that VTC write expressions are validated mid-phase against phase-snapshot shapes only (`vtc.py:504-513`); a mis-shaped candidate now fails loudly at the commit boundary rather than at compile (§7.4).
5. **Limited social-scope integration.** Dense and sparse `pair` storage exists alongside `group`, `affordance`, and `zone` storage, canonical relational `VariableDef` surfaces exist, and social-residue rules compile as VTC programs. Relational observation exposure and scenario-level environment wiring remain incomplete.
6. **Dynamic variables are registry-level only.** The gated `dynamic_variable_mode` (§7.2, §15.3) exists and is audited, but it is off by default and no config surface or runtime scenario drives it; for every shipped pack, variables are fixed at initialisation.
7. **Relationship rules are authorable but not yet authored.** Social rule kinds are declarable in a pack-root `transition_rules.yaml` (no-defaults DTO, 2026-08-22, hamlet-84cf93a1b9), compile into the transition schedule, and mutate pair-scope variables during `env.step` (proven config-in/behaviour-out). No shipped pack declares rules yet, and group-scope rules remain gated on relational observation exposure and the group-extents runtime wiring.
8. **Two VTC families refuse unsupported rule shapes at runtime, not compile time** (2026-08-24 audit): modulation rules with `condition:` or non-`multiplicative_modifier` composition (§14.4), and social-residue writes using the three claim-style compositions (§16.3). Both compile green and raise `NotImplementedError` at the first `env.step` — each costs a designer a training run to discover.

### 21.2 Design risks

| Risk | Mitigation |
|---|---|
| Compiler becomes too permissive | Small closed DSL, no arbitrary Python |
| Observation ABI churn breaks checkpoints | Schema hashes and dimension regression tests |
| VFS overhead slows training | JIT, caching, batched reads, compiled transition graph |
| Social variables explode in size | Implemented sparse pair scopes, neighbourhood masks, limited active relationships |
| Dynamic variables break network shapes | Fixed slots first; set encoders later |
| Meaning becomes hidden in config complexity | Telemetry labels, rule IDs, documentation, visual rule inspector |
| BAC naming collision | Use VTC for compiler; reserve BAC for Brain as Code |

---

## 22. Future enhancements

### 22.1 Dynamic variables

Variables that can be added, removed, activated, or deactivated during runtime.

Use cases:

- new needs induced by observation,
- diseases or injuries,
- debts and obligations,
- temporary goals,
- rumours,
- event memory,
- institutional states.

### 22.2 Hierarchical scopes

Nested scopes:

```text
world → zone → institution → group → household → agent → private
```

This supports richer social and spatial simulations.

### 22.3 Variable versioning

Track schema evolution:

```yaml
id: "energy"
schema_version: "1.2"
previous_ids: []
compatible_with: ["1.1"]
```

### 22.4 Observation caching

Cache derived features that are expensive but stable across ticks or phases.

### 22.5 Multi-agent communication

Represent communication through VFS variables:

```yaml
- id: "recent_message_tokens"
  type: "message_token"
  scope: "message"
  dims: 20
  readable_by: ["agent", "social_model"]
  writable_by: ["vtc"]
```

The repo exposes the seed definition as `canonical_l6_message_variables(message_token_dims=...)`.
Runtime storage requires the caller to provide `num_message_slots`; `dims` is the token vocabulary size or embedding
dimension for each message-slot payload.

### 22.6 Intrinsic reward shaping

Track novelty, curiosity, uncertainty, and exploration through VFS-visible or VFS-private state.

### 22.7 Curriculum progression

Gradually expose variables:

```text
L1: exact meters
L2: local spatial observations
L3: time and progress
L4: zone summaries
L5: other-agent positions and occupancy
L6: messages and inferred relationship features
```

### 22.8 Visual rule inspector

A developer tool that renders:

```text
variables → rules → writes → observation fields → telemetry
```

This would make VFS teachable and debuggable.

---

## 23. Resources

### Documentation

- `docs/architecture/VFS.md` (this document — formerly `vfs.md`, promoted 2026-08-24 per PDR-0118)
- `docs/architecture/archive/vfs-current-implementation.md` — implementation overview, accurate
  per the 2026-08-24 audit except its access-control and `agent_private` claims
- `docs/architecture/archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md` — the two-auditor
  claim-by-claim verdict tables behind this document's §5/§6 caveats
- `docs/zzz. archive/config-schemas/vfs-profiles.md` (archived 2026-08-24; schema concepts
  remain useful)
- `docs/zzz. archive/config-schemas/variables.md` — optional static variable and observation
  metadata overlay (⚠ broadly stale, 2025-11: three scopes, dead file paths, retracted
  dimension counts)
- `docs/zzz. archive/plans/archive/vfs_uplift/2025-11-18-items-and-vfs-profiles.md`
- `docs/zzz. archive/plans/archive/vfs_uplift/master_requirements.md`
- `CLAUDE.md` VFS section
- `Townlet v2.5: Universe as Code`
- `Townlet v2.5: Brain as Code`
- `Hamlet Training Levels - Formal Specification`

### Code

- `src/townlet/config/vfs_profiles_config.py`
- `src/townlet/config/transition_rules_config.py`
- `src/townlet/universe/raw_configs_v21.py`
- `src/townlet/universe/compilers/vfs.py`
- `src/townlet/universe/compilers/observation.py`
- `src/townlet/universe/compiled.py`
- `src/townlet/vfs/schema.py`
- `src/townlet/vfs/semantic_type.py`
- `src/townlet/vfs/registry.py`
- `src/townlet/vfs/observation_builder.py`
- `src/townlet/vfs/profiles.py`
- `src/townlet/vfs/evaluator.py`
- `src/townlet/vfs/vtc.py`
- `src/townlet/vfs/vtc_kernels.py`
- `src/townlet/vfs/transition_schedule.py`
- `src/townlet/vfs/schema_hashes.py`
- `src/townlet/vfs/transition_graph.py`
- `src/townlet/vfs/dynamic_needs.py`
- `src/townlet/vfs/generalisation.py`
- `src/townlet/vfs/relational.py`
- `src/townlet/vfs/communication.py`
- `src/townlet/environment/action_config.py`
- `src/townlet/environment/observation_encoder.py`
- `src/townlet/training/checkpoint_utils.py`

### Tests

- `tests/test_townlet/unit/vfs/`
- `tests/test_townlet/unit/config/test_vfs_profiles_dto.py`
- `tests/test_townlet/unit/universe/test_vfs_profile_compilation.py`
- `tests/test_townlet/unit/universe/test_evaluation_marks.py`
- `tests/test_townlet/unit/vfs/test_observation_dimension_regression.py`
- `tests/test_townlet/integration/test_vfs_runtime_evaluation.py`
- `tests/test_townlet/integration/test_item_vfs_observations.py`

### Reference configs

- `configs/default_curriculum/vfs_profiles.yaml`
- `configs/reference/model_pack/vfs_profiles.yaml`
- `configs/simple/vfs_profiles.yaml`
- `configs/aspatial_test/vfs_profiles.yaml`
- `configs/test/model_config/vfs_profiles.yaml`
- `configs/L5_multi_agent/variables_reference.yaml` — static pair and affordance runtime variable example
- `configs/test/model_config/variables_reference.yaml` — optional observation metadata example
- `configs/test/vfs_bar_access/variables_reference.yaml` — optional observation metadata example

---

## 24. Revised success criteria

### 24.1 Phase 1 success: achieved

- VFS schema definitions implemented.
- Variable registry implemented.
- Observation spec builder implemented.
- ActionConfig dependency tracking implemented.
- VFS regression tests cover schema definitions, runtime storage, observation generation, action write compilation, checkpoint dimensions, and integration flows.
- All five current curriculum configs dimension-validated.

### 24.2 Phase 1.5 success: achieved (shadow system since deleted)

- VFS observations run in shadow mode.
- VFS and hardcoded observations match for equivalent configs.
- Observation schema hash appears in telemetry.
- No training regression from VFS observation generation.

### 24.3 Phase 2 success

- VTC compiles simple action expressions.
- Type and shape errors are caught before runtime.
- Multiple writes to the same variable require explicit composition.
- Compiled action execution matches old imperative action execution.
- Transition graph hash is stored in run metadata.

### 24.4 Phase 2.5 success

- Passive depletion, cascades, temporal rules, multi-tick progress, terminal checks, and rewards can be run through VTC.
- Old imperative update paths are deleted; equivalence evidence remains as tests, not runtime compatibility branches.
- Performance is within acceptable tolerance of the hardcoded baseline.

### 24.5 Phase 3 success

- Pair, affordance, zone, and group scopes exist.
- Multi-agent occupancy and contention compile through VTC.
- Social residue rules can update trust, obligation, reputation, and norm variables.
- L5 multi-agent worlds can be configured without bespoke environment rewrites.

### 24.6 Phase 4 success

- Dynamic need variables or variable-token observations exist.
- Agents can train on abstract software-defined needs.
- Held-out variable names / affordance labels can be used to test generalisation over causal structure.

---

## 25. Conclusion

VFS Phase 1 is a strong foundation for declarative RL environment configuration. It already delivers typed variable schemas, registry-backed state, access control, observation-spec generation, action dependency tracking, compiled profile read evaluation, initial action-write execution, dimension regression, and integration tests.

The key architectural refinement is to treat VFS not merely as an observation system but as the **state and transition ABI** for Townlet.

The next major step should complete the VFS Transition Compiler so all declared relationships between variables compile into safe, efficient tensor operations. Action writes are the first implemented write-path slice, but the complete system should eventually compile passive dynamics, cascades, temporal gates, interaction progress, occupancy, social residue, terminal conditions, and reward logic.

The strongest long-term interpretation is:

```text
Universe as Code declares the society.
VFS declares its typed state, visibility, and observation/action ABI.
The VFS Transition Compiler executes the society’s relationships.
Brain as Code defines the minds that learn inside it.
```
