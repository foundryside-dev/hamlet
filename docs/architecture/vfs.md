# Townlet Variable & Feature System (VFS) — Updated Design and Integration Specification

**Document Type**: Design Specification + Integration Specification  
**Status**: Phase 1 Complete; Phase 1.5 Shadow Migration; Phase 2+ Roadmap  
**Version**: 1.1 Draft  
**Last Updated**: 15 May 2026
**Original VFS Guide Date**: 7 November 2025  
**Audience**: Engineers integrating VFS into Townlet environments; SDA/Brain-as-Code engineers; curriculum designers; researchers building social, temporal, and multi-agent environments

---

## 0. Executive summary

The Variable & Feature System (VFS) is the formal state, feature, observation, and transition-interface layer for Townlet. It turns the environment from a mostly hardcoded vectorised reinforcement-learning world into a declarative, typed, auditable substrate for software-defined agents.

In its current Phase 1 form, VFS provides:

1. **Schema definitions** for variables and observation fields.
2. **A required experiment-level `vfs_profiles.yaml` catalog** for compiled global, agent, and item profiles.
3. **An optional experiment-level `variables_reference.yaml` metadata overlay** for static observation marks only; item-scoped variables and expressions belong in `vfs_profiles.yaml`.
4. **A runtime variable registry** that stores state tensors and enforces read/write access control.
5. **An observation-spec builder** that generates agent-facing observation layouts from declarative exposures.
6. **ActionConfig dependency tracking** through declared `reads` and `writes` fields.
7. **Dimension regression tests** to protect checkpoint compatibility.
8. **Integration tests** proving that the schema → registry → observation pipeline works end to end.

The Phase 2 goal should be broadened from a narrow **Behavioural Action Compiler** into a more general **VFS Transition Compiler**. Actions are only one part of the world transition. To fully realise Universe as Code, the compiler should eventually execute action effects, passive decay, cascades, temporal rules, interaction progress, occupancy, reward components, terminal checks, and telemetry side effects through one typed, declarative, hashable transition graph.

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

The immediate Phase 1 validated observation dimensions already demonstrate this role:

| Config | Observation Dims | Status |
|---|---:|---|
| `L0_0_minimal` | 38 | Validated |
| `L0_5_dual_resource` | 78 | Validated |
| `L1_full_observability` | 93 | Validated |
| `L2_partial_observability` | 54 | Validated |
| `L3_temporal_mechanics` | 93 | Validated |

The long-term aim is that level changes are expressed primarily by changing variables, exposures, scopes, rules, action definitions, and brain configuration — not by rewriting environment code.

---

## 3. Phase 1 status

### 3.1 Implemented components

Phase 1 implementation is complete.

The current repo convention is split deliberately:

- `configs/<experiment>/vfs_profiles.yaml` is required at the experiment root and is the authoritative source for compiled VFS profiles. It carries global, agent, and item profile definitions and feeds `CompiledUniverse.compiled_vfs_profiles`.
- `configs/<experiment>/variables_reference.yaml` is optional at the experiment root. When present, the loader treats it as static VFS observation metadata; it cannot define item-scoped variables and cannot carry expression DSL fields.
- Level directories must not contain `vfs_profiles.yaml`; profile definitions are shared across curriculum levels, while level-specific activity and masking come from the compiled level metadata.

| Component | Status | Tests | Coverage |
|---|---:|---:|---:|
| Schema Definitions (`VariableDef`, `ObservationField`) | Complete | 23 | 93% |
| Variable Registry runtime storage + access control | Complete | 25 | 83% |
| Observation Spec Builder compile-time spec generation | Complete | 22 | 92% |
| `ActionConfig` extension with `reads` / `writes` fields | Complete | 14 | 78% |
| Dimension Regression Tests for checkpoint compatibility | Complete | 6 | — |
| Integration Tests end-to-end pipeline | Complete | 12 | — |

**Total**: 88 tests passing, approximately 90% average coverage.

### 3.2 What Phase 1 proves

Phase 1 proves that VFS can:

- define state variables in configuration,
- initialise runtime storage for those variables,
- enforce read/write permissions,
- generate observation specifications,
- calculate observation dimensions before runtime,
- preserve checkpoint compatibility through regression tests,
- and attach declared read/write dependencies to action definitions.

The repo no longer has "no transition compiler." The implemented VFS read path already parses profile expressions into ASTs, type-checks them, topologically sorts profile dependencies, and evaluates derived variables through `VFSEvaluator` in mark-and-sweep or eager mode. The action-write path also has an initial VTC slice: `ActionConfig.writes` compile into parsed, phase-ordered `CompiledActionWriteProgram` rules that execute masked tensor writes during `env.step`.

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
- and ordering in the observation ABI.

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

The current repo defines four canonical scope classes:

| Scope | Use case | Example |
|---|---|---|
| `global` | Shared state | `time_sin`, `day_of_week`, `weather_state` |
| `agent` | Per-agent observable state | `energy`, `position`, `health` |
| `agent_private` | Per-agent hidden state | `internal_motivation`, `hidden_reward` |
| `item` | Per-item-instance state compiled from item profiles | `durability`, `charges`, `spoilage` |

`item` scope is profile-based, not loaded from `variables_reference.yaml`. The registry allocates a profile-agnostic `item_vfs[max_items, max_profile_vars]` tensor, records `item_profile_map[profile_name][var_name] -> tensor_index`, and masks unused profile slots. Item profile definitions therefore live in `vfs_profiles.yaml:item_profiles`, while item instances address rows in the shared item VFS tensor.

These scopes are sufficient for Phase 1–3 style single-agent survival, temporal mechanics, and item-bearing environments.

### 5.2 Recommended future scopes

For serious multi-agent and small-society modelling, VFS should add relational and institutional scopes:

| Scope | Shape intuition | Use case | Example |
|---|---|---|---|
| `pair` | `[agent_i, agent_j]` | Directed relationships | `trust`, `fear`, `obligation`, `resentment` |
| `group` | `[group]` or `[agent, group]` | Factions, families, teams | `group_norm_strength`, `membership`, `loyalty` |
| `household` | `[household]` | Shared domestic resources | `shared_food`, `rent_due`, `household_mood` |
| `faction` | `[faction]` | Political or social blocs | `legitimacy`, `territory_claim` |
| `affordance` | `[affordance_instance]` | Capacity and occupancy | `occupied_by`, `cooldown`, `is_open` |
| `zone` | `[zone]` | Multi-zone environments | `zone_danger`, `travel_cost`, `zone_crowding` |
| `institution` | `[institution]` | Rules and enforcement | `sanction_probability`, `rule_legitimacy` |
| `message` | `[agent, message_slot]` | Communication | `recent_message_tokens`, `sender_id`, `message_age` |

These scopes are essential for L5 multi-agent competition and L6 emergent communication.

### 5.3 Social observability and privacy

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
- Shape validation is currently caller responsibility.
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

Runtime VFS evaluation uses `VariableRegistry.set_engine_value()` for evaluator writeback. This method is deliberately narrower than direct storage mutation: it still requires the variable to exist and requires `engine` write permission, but it bypasses declaration-shape checks so derived global VFS variables may store batched per-agent results when their expressions read batched bar state.

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

Phase 1 currently notes that callers are responsible for shape validation. Phase 2+ should move shape checks into the compiler and registry boundary.

Suggested rule:

```text
Manual registry.set() in engine code:
    shape check optional in hot path, strict in debug/test mode

Compiler-generated writes:
    shape checked at compile time and assertable at runtime

External tooling / tests:
    always strict
```

---

## 8. Observation specifications

### 8.1 Building observation specs

```python
from townlet.vfs import VFSObservationSpecBuilder

# Build exposures from config or programmatically
exposures = []
for var in variables:
    if "agent" in var.readable_by:
        entry = {"source_variable": var.id}
        if var.type == "scalar":
            entry["normalization"] = {"kind": "minmax", "min": 0.0, "max": 1.0}
        else:
            entry["normalization"] = None
        exposures.append(entry)

# Build observation spec
builder = VFSObservationSpecBuilder()
obs_spec = builder.build_observation_spec(variables, exposures)

# Calculate total observation dimension
obs_dim = sum(field.shape[0] if field.shape else 1 for field in obs_spec)
print(f"Observation dimension: {obs_dim}")

# Validate against expected dimension (for checkpoint compatibility)
assert obs_dim == EXPECTED_DIM, f"Dimension mismatch! Expected {EXPECTED_DIM}, got {obs_dim}"
```

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
- `curriculum_active` masks,
- dtype information,
- and version metadata.

The checkpoint should store this hash. Resume must refuse to attach a checkpoint to an incompatible observation ABI; changed VFS schemas create a new run fork.

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
clipped_log_scaled
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
    kind: "clipped_log_scaled"
    min: 0.0
    max: 1000.0
    clip: true
```

Normalisation must be part of the observation schema hash.

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

## 11. From Behavioural Action Compiler to VFS Transition Compiler

### 11.1 Naming note

The original Phase 2 roadmap uses **Behavioral Action Compiler (BAC)**. Townlet already uses **Brain as Code (BAC)**. This naming collision will likely become confusing in documentation, telemetry, hashes, and code reviews.

Recommendation:

```text
Use: VFS Transition Compiler (VTC)
Keep as alias: Behavioural Action Compiler / Action Effect Compiler for legacy discussion
```

This document uses **VTC** for the compiler family that executes VFS transition rules.

Current implementation is partial but real:

- `VFSProfileCompiler` compiles profile expressions on the read/derived-variable path: AST parsing, dependency graph construction, topological sorting, cycle detection, and expression type checking.
- `VFSEvaluator` evaluates compiled profile variables in dependency order, with mark-and-sweep evaluation for observed variables plus dependencies and eager mode when all variables are needed.
- `CompiledActionWriteProgram` executes the first write-path slice for `ActionConfig.writes`: parsed expressions, phase ordering, composition modes, clamps, conditions, and active-agent masks.

The unsolved work is not "build any compiler"; it is "finish the VTC as the single write-path and world-transition compiler."

### 11.2 Why the compiler should cover transitions, not only actions

The current action-write compiler handles declared action writes. That is useful but incomplete.

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

Social residue example:

```yaml
rules:
  - id: "seen_stealing_damages_trust"
    phase: "social_residue_effects"
    kind: "visibility_effect"
    reads: ["chosen_action", "observer_mask", "trust"]
    condition: "chosen_action == STEAL & observed_by(observer_mask)"
    writes:
      - variable_id: "trust"
        scope: "pair"
        target: "observer -> actor"
        expression: "trust - 0.15"
        composition: "additive_delta"
        clamp: [0.0, 1.0]
```

Institutional rule example:

```yaml
rules:
  - id: "ambulance_abuse_social_penalty"
    phase: "social_residue_effects"
    kind: "institutional_rule"
    reads: ["chosen_action", "health", "mood", "public_reputation"]
    condition: "chosen_action == CALL_AMBULANCE & health >= 0.7 & mood >= 0.8"
    writes:
      - variable_id: "public_reputation"
        expression: "public_reputation - 0.10"
        composition: "additive_delta"
        clamp: [0.0, 1.0]
```

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

### 16.3 Social residue effect types

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
rules:
  - id: "help_creates_obligation_and_reputation"
    phase: "social_residue_effects"
    kind: "social_residue"
    reads: ["chosen_action", "recipient_id", "observer_mask", "public_reputation", "obligation"]
    condition: "chosen_action == HELP"
    writes:
      - variable_id: "obligation"
        scope: "pair"
        target: "recipient -> actor"
        expression: "obligation + 0.20"
        composition: "additive_delta"
        clamp: [0.0, 1.0]
      - variable_id: "public_reputation"
        target: "actor"
        expression: "public_reputation + 0.05 * any(observer_mask)"
        composition: "additive_delta"
        clamp: [0.0, 1.0]
```

---

## 17. Migration path: hardcoded to VFS-driven environment

### 17.1 Current hardcoded observation generation

The current `VectorizedHamletEnv` pattern uses hardcoded concatenation:

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

### 17.2 Target VFS-driven observation generation

```python
def _initialize_vfs(self):
    """Initialize VFS registry and observation spec once at startup."""
    # Use the compiled universe artifact. The compiler has already loaded
    # vfs_profiles.yaml and the optional variables_reference.yaml metadata.
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

### 17.3 Migration strategy

#### Phase 1.5: Parallel/shadow systems

1. Keep current hardcoded observations in production.
2. Add VFS observation generation as a shadow system.
3. Compare outputs for equivalent configs.
4. Validate dimension compatibility.
5. Run training experiments with both systems.
6. Store observation schema hash in telemetry.

#### Phase 2.0: Initial compiler integration

1. Replace hardcoded observation generation with VFS.
2. Compile simple action writes.
3. Keep old meter update logic for non-action world physics.
4. Run equivalence tests.

#### Phase 2.1–2.3: Transition unification

1. Move passive depletion into VTC.
2. Move cascades and modulations into VTC.
3. Move temporal gates and multi-tick progress into VTC.
4. Move terminal conditions and reward components into VTC.

#### Phase 2.5: Optimisation and cutover

1. Profile registry get/set overhead.
2. Cache static observation fields.
3. JIT compile hot transition paths.
4. Benchmark against hardcoded baseline.
5. Delete old imperative paths after equivalence is proven.

#### Phase 3+: Social/relational expansion

1. Add pair/group/affordance/zone scopes.
2. Add social residue rules.
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
  variables_reference.yaml  # optional static observation metadata overlay
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
    variables_reference.yaml  # optional if present in the source pack
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
uv run pytest tests/test_townlet/integration/test_vfs_integration.py -v

# Full VFS suite
uv run pytest tests/test_townlet/unit/vfs/ tests/test_townlet/integration/test_vfs_integration.py -v
```

### 19.2 Additional tests for VTC

Compiler tests:

```bash
uv run pytest tests/test_townlet/unit/vfs/test_expression_parser.py -v
uv run pytest tests/test_townlet/unit/vfs/test_type_inference.py -v
uv run pytest tests/test_townlet/unit/vfs/test_dependency_graph.py -v
uv run pytest tests/test_townlet/unit/vfs/test_effect_composition.py -v
uv run pytest tests/test_townlet/unit/vfs/test_transition_compiler.py -v
```

Equivalence tests:

```bash
uv run pytest tests/test_townlet/integration/test_vfs_observation_equivalence.py -v
uv run pytest tests/test_townlet/integration/test_vtc_cascade_equivalence.py -v
uv run pytest tests/test_townlet/integration/test_vtc_affordance_equivalence.py -v
uv run pytest tests/test_townlet/integration/test_vtc_terminal_equivalence.py -v
```

Provenance tests:

```bash
uv run pytest tests/test_townlet/unit/vfs/test_schema_hashes.py -v
uv run pytest tests/test_townlet/integration/test_vfs_snapshot_resume.py -v
uv run pytest tests/test_townlet/integration/test_vfs_checkpoint_compatibility.py -v
```

Multi-agent tests:

```bash
uv run pytest tests/test_townlet/unit/vfs/test_pair_scope.py -v
uv run pytest tests/test_townlet/unit/vfs/test_affordance_scope.py -v
uv run pytest tests/test_townlet/integration/test_vfs_occupancy_claims.py -v
uv run pytest tests/test_townlet/integration/test_social_residue_rules.py -v
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

Prefer explicit rules:

```yaml
rules:
  - id: "public_help_increases_reputation"
    phase: "social_residue_effects"
    ...
```

This keeps social meaning inspectable and teachable.

### 20.8 Derived features

Do not store every computed quantity as a variable. Use `FeatureDef` for derived observations where possible.

Store state when it must persist or be authoritative. Derive features when they are observation conveniences.

---

## 21. Known limitations

### 21.1 Phase 1 limitations

1. **Partial VTC coverage.** Profile read expressions compile and evaluate through `VFSProfileCompiler`/`VFSEvaluator`, and simple action writes execute through `CompiledActionWriteProgram`; passive dynamics, cascades, temporal rules, rewards, terminal checks, and telemetry are not yet unified under VTC.
2. **Manual observation generation.** Observation construction still requires explicit registry reads and concatenation.
3. **Partial write validation.** `WriteSpec` expressions are parsed and executed for action writes, but full write-path type/shape validation is still incomplete.
4. **Limited normalisation.** Current normalisation is mostly minmax/zscore.
5. **Limited scopes.** Current scopes are suitable for early levels but not full social simulation.
6. **No dynamic variables.** Variables are fixed at initialisation.
7. **No first-class relationship rules.** Cascades and temporal operations are not yet unified as VFS rules.

### 21.2 Design risks

| Risk | Mitigation |
|---|---|
| Compiler becomes too permissive | Small closed DSL, no arbitrary Python |
| Observation ABI churn breaks checkpoints | Schema hashes and dimension regression tests |
| VFS overhead slows training | JIT, caching, batched reads, compiled transition graph |
| Social variables explode in size | Sparse pair scopes, neighbourhood masks, limited active relationships |
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
  scope: "agent"
  dims: 20
  readable_by: ["agent", "social_model"]
  writable_by: ["vtc"]
```

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

- `docs/architecture/vfs.md`
- `docs/config-schemas/vfs-profiles.md`
- `docs/config-schemas/variables.md` — optional static observation metadata overlay
- `docs/plans/archive/vfs_uplift/2025-11-18-items-and-vfs-profiles.md`
- `docs/plans/archive/vfs_uplift/master_requirements.md`
- `docs/tasks/TASK-002-variables-and-features-system.md`
- `CLAUDE.md` VFS section
- `Townlet v2.5: Universe as Code`
- `Townlet v2.5: Brain as Code`
- `Hamlet Training Levels - Formal Specification`

### Code

- `src/townlet/config/vfs_profiles_config.py`
- `src/townlet/universe/raw_configs_v21.py`
- `src/townlet/universe/compilers/vfs.py`
- `src/townlet/universe/compiled.py`
- `src/townlet/vfs/schema.py`
- `src/townlet/vfs/registry.py`
- `src/townlet/vfs/observation_builder.py`
- `src/townlet/vfs/action_writes.py`
- `src/townlet/vfs/schema_hashes.py`
- `src/townlet/vfs/transition_graph.py`
- `src/townlet/environment/action_config.py`

### Tests

- `tests/test_townlet/unit/vfs/`
- `tests/test_townlet/unit/config/test_vfs_profiles_dto.py`
- `tests/test_townlet/unit/universe/test_vfs_profile_compilation.py`
- `tests/test_townlet/unit/universe/test_vfs_observation_marking.py`
- `tests/test_townlet/unit/vfs/test_observation_dimension_regression.py`
- `tests/test_townlet/integration/test_vfs_runtime_evaluation.py`
- `tests/test_townlet/integration/test_item_vfs_observations.py`

### Reference configs

- `configs/default_curriculum/vfs_profiles.yaml`
- `configs/reference/model_pack/vfs_profiles.yaml`
- `configs/simple/vfs_profiles.yaml`
- `configs/aspatial_test/vfs_profiles.yaml`
- `configs/test/model_config/vfs_profiles.yaml`
- `configs/test/model_config/variables_reference.yaml` — optional observation metadata example
- `configs/test/vfs_bar_access/variables_reference.yaml` — optional observation metadata example

---

## 24. Revised success criteria

### 24.1 Phase 1 success: achieved

- VFS schema definitions implemented.
- Variable registry implemented.
- Observation spec builder implemented.
- ActionConfig dependency tracking implemented.
- 88 tests passing.
- All five current curriculum configs dimension-validated.

### 24.2 Phase 1.5 success

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
