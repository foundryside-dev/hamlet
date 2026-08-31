# VFS Profiles Configuration

> ⛔ **Restored to the live tree 2026-08-26 — a pack written from this document WILL NOT PARSE.**
>
> Verified against `src/townlet/config/vfs_profiles_config.py` on 2026-08-26.
>
> **⚠️ Two REQUIRED top-level fields are never mentioned in this document.**
> `VFSProfilesConfig` requires `version`, **`evaluation_mode`** and **`debug_logging`**. This
> file mentions `evaluation_mode` **0 times** and `debug_logging` **0 times**. Omit either and
> the pack is refused at parse.
>
> **⚠️ `readable_by` / `writable_by` are NOT fields of any profile DTO** — this document uses
> them 12 times combined (8 + 4). No class in `vfs_profiles_config.py` declares them:
> variables carry **`exposed_to`** instead. Under `extra="forbid"` they are a parse error. (This
> matches `CLAUDE.md` §VFS: access-control enforcement is real where it runs but currently has
> **no authoring surface** — the compiler hardcodes the role lists.)
>
> **⚠️ The "Optional File" framing is false.** `vfs_profiles.yaml` is **required**, at pack
> root, and level directories must NOT contain one.
>
> **⚠️ `tensorNd` is entirely undocumented here** while `vfs_profiles_config.py:39-52` accepts
> `tensor1d` / `tensor2d` / `tensor3d` / **`tensorNd`**. It genuinely works, and an
> undiscoverable working capability is the worst case for a product whose north-star is
> authorability. Tracked as `hamlet-8b5af63108`.
>
> ✅ **Correct as written — do not "fix" it:** the warning that item-scoped *expressions* are
> refused at compile time is accurate and already present below.
>
> 🔁 **"Observation Integration" was CORRECTED 2026-08-26** (unit-3 token cut, DIV-008 — the
> banner and the section were updated in one commit, so they agree). Three claims that section
> carried are now dead and have been replaced rather than annotated: the fail-open
> `exposed_to` → `["agent"]` injection (**deleted** — empty means unexposed); "values are
> observed raw, no normalization surface" (**normalization is now REQUIRED at exposure**, and
> boundedness is certified there); and the `PDR-0075` per-variable `ObservationField` /
> `obs_item_slots` emission (**gone** — an admitted exposed profile variable compiles to a
> `variable_element` token, and item-profile exposure is refused until the unit-5 pack
> migration). Expression-backed exposure is also refused until milestone 3 static context can
> encode executable initializer identity without erasing it. Everything else in this document is
> still at its 2026-08-26 restoration state.
>
> Tracked as `hamlet-fd0eb2da2c`.
>
> Real field sets, verified: `ItemVFSProfileConfig` = `{profile_name, variables}`;
> item variables = `{id, name, type, initial_value, expression, normalization, exposed_to,
> description}`.


**Status**: Phase 2 Implementation (Expression Support)
**Version**: 1.0
**Last Updated**: 2025-11-21

## Overview

VFS Profiles provide a declarative system for defining **custom variables** beyond the standard bars and affordances. Profiles enable:

- **Global Variables**: Shared state across all agents (day_count, is_night)
- **Agent Variables**: Per-agent custom state (motivation, is_crisis)
- **Item Variables**: Per-item-instance state (durability, nutrition, is_spoiled)

Profiles support **static variables** (initial_value) and **computed variables** (expression DSL), with automatic dependency resolution and type checking.

## Why VFS Profiles?

**Without VFS Profiles** (hardcoded state):
```python
# Hardcoded in environment.py
self.day_count = 0
self.is_night = (self.tick % 24) >= 18
self.motivation = torch.ones(num_agents)
```

**With VFS Profiles** (declarative YAML):
```yaml
global_profile:
  variables:
    - name: day_count
      type: int
      initial_value: 0
    - name: is_night
      type: bool
      expression: "temporal.tick % 24 >= 18"

agent_profile:
  variables:
    - name: motivation
      type: float
      initial_value: 1.0
```

**Benefits**:
- Modular configuration (no code changes)
- Automatic dependency resolution
- Type safety (compile-time validation)
- Observation integration (variables can appear in agent observations)

## File Location

VFS Profiles are defined in `configs/<config_pack>/vfs_profiles.yaml`.

**Optional File**: If no `vfs_profiles.yaml` exists, the system uses default configuration (no custom variables).

## Schema Structure

```yaml
# Top-level structure
version: "1.0"  # Required schema version (strict)

global_profile:
  variables: [...]

agent_profile:
  variables: [...]

item_profiles:
  - profile_name: food_stats
    variables: [...]
  - profile_name: weapon_stats
    variables: [...]
```

### Schema Version

- **1.0** (2025-11-22): Initial VFS profiles schema with explicit `version`, global/agent/item scopes, expressions, and dependency resolution.

## Variable Scopes

VFS Profiles organize variables into three scopes:

| Scope | Storage | Use Case | Example |
|-------|---------|----------|---------|
| **global** | Singleton (shared) | World state, time, global flags | day_count, is_night |
| **agent** | Per-agent batch | Agent-specific state | motivation, is_crisis |
| **item** | Per-item-instance | Item attributes | nutrition, durability |

### Global Scope

**Storage**: Single value shared across all agents
**Shape**: Scalar or vector (no batch dimension)
**When to use**: Time signals, weather, global events

**Example**:
```yaml
global_profile:
  variables:
    - name: day_count
      semantic_type: temporal     # REQUIRED for global/agent variables — see Observation Integration
      type: int
      initial_value: 0
      description: "Number of days elapsed"

    - name: is_night
      semantic_type: temporal
      type: bool
      expression: "temporal.tick % 24 >= 18"
      description: "True during night hours (18:00-6:00)"
```

**Storage Shape**:
- `day_count`: `[]` (scalar)
- `is_night`: `[]` (scalar bool)

### Agent Scope

**Storage**: Per-agent batch tensors
**Shape**: `[num_agents]` for scalar, `[num_agents, dims]` for vector
**When to use**: Agent-specific meters, flags, motivation

**Example**:
```yaml
agent_profile:
  variables:
    - name: motivation
      semantic_type: custom       # REQUIRED for global/agent variables
      type: float
      initial_value: 1.0
      description: "Agent's intrinsic motivation multiplier"

    - name: is_crisis
      semantic_type: custom
      type: bool
      expression: "bar.energy < 0.2 or bar.health < 0.2"
      description: "True when agent is in resource crisis"

    - name: crisis_duration
      semantic_type: custom
      type: int
      initial_value: 0
      description: "Ticks spent in crisis state"
```

**Storage Shape**:
- `motivation`: `[num_agents]`
- `is_crisis`: `[num_agents]`
- `crisis_duration`: `[num_agents]`

### Item Scope

**Storage**: Per-item-instance arrays (profile-based)
**Shape**: `[max_items, num_vars]` per profile
**When to use**: Item attributes (nutrition, durability, age)

> ⚠️ **Item-profile `expression:` refuses at compile.** `VFSProfileCompiler.compile_item_profile`
> has no expression evaluator for item scope and raises `ValueError` (`hamlet-bc0a5deeff`) for
> any item-profile variable that declares `expression`. Every item-profile variable below must
> declare `initial_value` instead; drive changing item state (e.g. spoilage, breakage) via
> effects, not a compiled expression.

**Example**:
```yaml
item_profiles:
  - profile_name: food_stats
    variables:
      - name: nutrition
        type: float
        initial_value: 0.5
        description: "Energy restored when consumed"

      - name: age
        type: int
        initial_value: 0
        description: "Ticks since item creation"

      # Item-profile expressions refuse at compile (hamlet-bc0a5deeff) — static default,
      # flip it via an effect when the item actually spoils.
      - name: is_spoiled
        type: bool
        initial_value: false
        description: "True when food has spoiled"

  - profile_name: weapon_stats
    variables:
      - name: damage
        type: float
        initial_value: 10.0
        description: "Damage dealt per use"

      - name: durability
        type: int
        initial_value: 100
        description: "Remaining uses before breaking"
```

**Storage Shape**:
- `food_stats.nutrition`: `[max_items]`
- `weapon_stats.durability`: `[max_items]`

## Variable Types

### Scalar Types

| Type | Storage | Python Type | Example |
|------|---------|-------------|---------|
| `int` | `torch.long` | `int` | `0`, `42`, `-5` |
| `float` | `torch.float32` | `float` | `1.0`, `0.5`, `-3.14` |
| `bool` | `torch.bool` | `bool` | `true`, `false` |

### Vector Types

| Type | Dims | Storage | Example |
|------|------|---------|---------|
| `vec2i` | 2 | `torch.long` | `[0, 0]`, `[5, 3]` |
| `vec3i` | 3 | `torch.long` | `[0, 0, 0]`, `[1, 2, 3]` |

### Reference Types (Future)

| Type | Description | Example |
|------|-------------|---------|
| `agent_ref` | Reference to agent index | `0`, `3` |
| `item_ref` | Reference to item index | `5`, `12` |
| `affordance_ref` | Reference to affordance type | `7` |
| `effect_ref` | Reference to effect ID | `2` |

**Note**: Reference types are reserved for future use (Phase 3+).

## Variable Definition Schema

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique variable name — and, when exposed, the name of its observation field, so it must not collide with an `environment.yaml` variable, a meter field, a compiler block, or another exposed profile variable (compile error) |
| `type` | enum | Variable type (int, float, bool, vec2i, vec3i, …) |
| `semantic_type` | enum | **Global and agent variables only. Required.** The observation group the variable's field is laid out in when exposed: one of `spatial`, `affordance`, `effects`, `temporal`, `custom` (`bars` is reserved to meters — compile error). Item variables do **not** take it: they are observed through the single `obs_item_slots` feature, so a per-variable group could reach nothing (`PDR-0075`). |

### Mutually Exclusive Fields (XOR Constraint)

**Exactly one of the following must be specified**:

| Field | Type | Description |
|-------|------|-------------|
| `initial_value` | varies | Static initial value (no computation) |
| `expression` | string | Expression DSL (computed dynamically) |

**Validation**: Pydantic enforces XOR constraint at config load time.

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Human-readable documentation |

## Static vs Dynamic Variables

### Static Variables (initial_value)

**Use when**: Variable has a fixed starting value that may be updated by engine/actions but doesn't require computation.

**Example**:
```yaml
- name: day_count
  type: int
  initial_value: 0
```

**Behavior**:
- Initialized once at environment reset
- Updated by engine or actions during runtime
- No dependencies on other variables

### Dynamic Variables (expression)

**Use when**: Variable is computed from other variables or bars.

**Example**:
```yaml
- name: is_night
  type: bool
  expression: "temporal.tick % 24 >= 18"
```

**Behavior**:
- Recomputed every tick (derived state)
- Dependencies extracted automatically
- Type-checked at compile time

## Expression DSL

### Supported Operators

| Category | Operators | Example |
|----------|-----------|---------|
| Arithmetic | `+`, `-`, `*`, `/`, `%` | `tick % 24` |
| Comparison | `<`, `<=`, `>`, `>=`, `==`, `!=` | `energy < 0.2` |
| Logical | `and`, `or`, `not` | `a and b` |

### Namespace Access

| Namespace | Description | Example |
|-----------|-------------|---------|
| `bar.<name>` | Access bar values | `bar.energy`, `bar.health` |
| `temporal.<field>` | Access time state | `temporal.tick`, `temporal.time_of_day` |
| `self.<field>` | Item-scope self-reference | `self.age`, `self.nutrition` |
| `<var_name>` | Reference other variables | `day_count`, `motivation` |

### Expression Examples

**Simple comparison**:
```yaml
expression: "bar.energy < 0.2"
```

**Boolean logic**:
```yaml
expression: "bar.energy < 0.2 or bar.health < 0.2"
```

**Arithmetic**:
```yaml
expression: "bar.energy + bar.health * 0.5"
```

**Modulo for cyclical time**:
```yaml
expression: "temporal.tick % 24 >= 18"
```

**Self-reference (item scope)** — valid `self.<field>` syntax in item spawn-condition
(`items.yaml` appearance `when:`) and effect expressions; as an item-profile **variable**'s
own `expression:` field it refuses at compile (`hamlet-bc0a5deeff`, see Item Scope above):
```yaml
expression: "self.age > 100"
```

### Type Checking

Expressions are type-checked at compile time using schema inference:

```yaml
# ERROR: Type mismatch
- name: invalid
  type: bool
  expression: "tick + 1"  # Returns int, not bool
```

**Type Checker** validates:
- Expression result type matches declared type
- All referenced variables exist in schema
- Operations are type-safe (no `bool + int`)

## Dependency Resolution

VFS Profiles automatically resolve variable dependencies using topological sort.

### Dependency Graph

The compiler builds a dependency graph by parsing expressions:

**Example**:
```yaml
variables:
  - name: a
    type: int
    initial_value: 1

  - name: b
    type: int
    expression: "a + 1"

  - name: c
    type: int
    expression: "b + 1"
```

**Dependency Graph**:
```
a → b → c
```

**Evaluation Order**: `a`, then `b`, then `c`

### Circular Dependency Detection

The compiler detects and rejects circular dependencies:

**Example (INVALID)**:
```yaml
variables:
  - name: a
    type: int
    expression: "b + 1"

  - name: b
    type: int
    expression: "a + 1"
```

**Error**:
```
CircularDependencyError: Circular dependency detected in cycle: a -> b -> a
```

### Cross-Profile Dependencies

**Rule**: Variables can only reference variables in the same profile.

**Valid** (same profile):
```yaml
agent_profile:
  variables:
    - name: x
      type: int
      initial_value: 1
    - name: y
      type: int
      expression: "x + 1"
```

**Invalid** (cross-profile):
```yaml
global_profile:
  variables:
    - name: day_count
      type: int
      initial_value: 0

agent_profile:
  variables:
    - name: invalid
      type: int
      expression: "day_count + 1"  # ERROR: day_count not in agent scope
```

**Workaround**: Use namespace access (`temporal.tick`) or pass state explicitly.

## Observation Integration

A profile variable appears in the agent's observation when its `exposed_to` list contains
`agent`. **Exposure is explicit.** The three fail-open validators that rewrote an empty
`exposed_to` to `["agent"]` were deleted by the unit-3 token cut: an absent or empty
`exposed_to` now means **unexposed**, full stop. That is the No-Defaults fix the old note
here anticipated, and it is a breaking change for any pack that relied on the injection.

**`normalization` is REQUIRED on an exposed variable, and forbidden on an unexposed one.**
The old claim in this section — "values are observed raw (no normalization surface on profile
variables yet)" — is dead. A value entering a token must come from a bounded normalization
kind, certified at exposure (`token_spec.require_exposure_normalization`):

- `cyclical_sin_cos` and `binary` are bounded by themselves;
- `minmax` and `log_scaled` are bounded only with **`clip: true`**;
- `one_hot` is **refused** on a tokenized variable (it widens 1→C and cannot fit the fixed
  2-lane value block; expose the category as a clipped `minmax` index over `[0, C-1]` and its
  declared range rides in the descriptor block);
- `rank_scaled` is **refused** at exposure (it ranks across the batch, which is causally
  independent worlds — `hamlet-6a6e104523`);
- `none`, `zscore`, bare `masked_value` and unclipped range kinds are unbounded and refused.

### What the compiler emits

An exposed global or agent profile variable with a literal initializer compiles to a
**`variable_element` token** in the compiled `TokenSpec`, one token per element (a tensor-shaped
variable tokenizes per element; a scalar is the rank-0 case). Deterministic `zeros`, `ones`, and
`eye` initializers are lowered losslessly to that literal default before token binding. Random
initializers and expression-backed exposure are refused because their executable initializer
identity cannot yet survive into static context; milestone 3 owns that representation. Each
admitted token's payload is a padded position block, the two-lane value block, and the
**descriptor block** — the variable's declared parameters, name-free:
scope one-hot, `semantic_type` one-hot, normalization kind one-hot plus its canonical
parameter vector, dtype flag, lifetime one-hot, normalized declared initial, log element
count, and owner-slot coordinate. Identity is the declared payload (spec §1); two variables
identical in every declared parameter are **refused at compile time** as
indistinguishable.

The current default curriculum therefore emits zero `variable_element` tokens. Its expression-
driven time variable remains live in VFS but is deliberately unexposed until that initializer
identity can be represented.

> **Item-profile exposure does not compile yet.** The `obs_item_slots` feature this section
> used to describe died with the `ObservationSpec` family. An exposed item-profile variable
> is refused at compile with the unit-5 pack migration named in the message. `PDR-0075`'s
> per-variable-field emission and `hamlet-1ad6383186`'s layout question are both superseded
> by the token layout.

```yaml
global_profile:
  variables:
    - name: time_of_day_phase   # live expression state; unexposed, so emits no token
      id: time_of_day_phase
      type: float
      semantic_type: temporal
      expression: tick
agent_profile:
  variables:
    - name: motivation          # → one `variable_element` token
      type: float
      initial_value: 1.0
      semantic_type: custom
      exposed_to: [agent]
      normalization:
        kind: minmax
        min: 0.0
        max: 1.0
        clip: true              # required: minmax is bounded only when clipped
```

### Observation width

An exposed variable contributes **tokens**, not a hand-summable dim count: one token per
element, each of fixed per-type width. `cyclical_sin_cos` is the one kind that uses both
value lanes of a single token rather than widening anything.

Ask the compiled artifact for the truth — `token_spec.census` for counts,
`token_spec.total_dims` for the serialization width, `token_spec.row_layout()` for offsets.
Do not sum by hand, and do not quote a literal: `observation_spec` no longer exists.

### Access Control

Variables support fine-grained access control:

| Role | Description | Example Use |
|------|-------------|-------------|
| `agent` | Agent networks observe | Decision-making state |
| `engine` | Environment engine reads/writes | Dynamics, rendering |
| `acs` | Adversarial Curriculum System reads | Difficulty adjustment |
| `bac` | Behavioral Action Compiler reads/writes | Action execution |

**Pattern: Observable State**:
```yaml
readable_by: ["agent", "engine"]
writable_by: ["engine"]
```

**Pattern: Hidden State**:
```yaml
readable_by: ["engine"]  # Agent cannot observe
writable_by: ["engine"]
```

## Complete Examples

### Example 1: Static Day Counter

```yaml
global_profile:
  variables:
    - name: day_count
      type: int
      initial_value: 0
      description: "Number of days elapsed (updated by engine)"
```

**Usage**:
- Engine increments `day_count` when `tick % 24 == 0`
- Observable by agents for time-aware behavior

### Example 2: Computed Night Flag

```yaml
global_profile:
  variables:
    - name: is_night
      type: bool
      expression: "temporal.tick % 24 >= 18"
      description: "True during night hours (18:00-23:59)"
```

**Usage**:
- Recomputed every tick
- Agents can observe for circadian behavior patterns

### Example 3: Agent Crisis Detection

```yaml
agent_profile:
  variables:
    - name: is_crisis
      type: bool
      expression: "bar.energy < 0.2 or bar.health < 0.2"
      description: "Agent in resource crisis"

    - name: crisis_duration
      type: int
      initial_value: 0
      description: "Ticks spent in crisis (updated by engine)"
```

**Usage**:
- `is_crisis` recomputed every tick from bars
- `crisis_duration` incremented by engine when `is_crisis == true`
- Observable for crisis-aware reward shaping

### Example 4: Motivation with Dependencies

```yaml
agent_profile:
  variables:
    - name: base_motivation
      type: float
      initial_value: 1.0
      description: "Base motivation level"

    - name: crisis_penalty
      type: float
      expression: "0.5 if bar.energy < 0.2 else 1.0"
      description: "Penalty during crisis (0.5x motivation)"

    - name: effective_motivation
      type: float
      expression: "base_motivation * crisis_penalty"
      description: "Final motivation after crisis penalty"
```

**Dependency Order**: `base_motivation` → `crisis_penalty` → `effective_motivation`

### Example 5: Item Durability

> Item-profile `expression:` refuses at compile (`hamlet-bc0a5deeff`) — `is_broken` is a static
> default, flipped by an effect when `durability` reaches zero, not a compiled expression.

```yaml
item_profiles:
  - profile_name: weapon_stats
    variables:
      - name: durability
        type: int
        initial_value: 100
        description: "Remaining uses before breaking"

      - name: is_broken
        type: bool
        initial_value: false
        description: "True when weapon is broken"

      - name: damage
        type: float
        initial_value: 10.0
        description: "Base damage dealt per use"
```

**Usage**:
- `durability` decremented by engine on item use
- `is_broken` set by an effect that watches `durability` (no item-scope expression evaluator)
- `damage` used in combat calculations

### Example 6: Food Spoilage

> Item-profile `expression:` refuses at compile (`hamlet-bc0a5deeff`) — `is_spoiled` and
> `effective_nutrition` are static defaults here; drive them via effects instead of a
> compiled dependency chain.

```yaml
item_profiles:
  - profile_name: food_stats
    variables:
      - name: nutrition
        type: float
        initial_value: 0.5
        description: "Energy restored when consumed"

      - name: age
        type: int
        initial_value: 0
        description: "Ticks since creation"

      - name: is_spoiled
        type: bool
        initial_value: false
        description: "True when food has spoiled"

      - name: effective_nutrition
        type: float
        initial_value: 0.5
        description: "Nutrition value (0 if spoiled; set by an effect, not a compiled expression)"
```

**Usage**: `age` accumulates via the engine; an effect flips `is_spoiled` and
`effective_nutrition` when `age` crosses the spoilage threshold — item scope has no compiled
dependency resolution to do this automatically.

### Example 7: Multi-Profile Items System

```yaml
item_profiles:
  # Food profile
  - profile_name: food_stats
    variables:
      - name: nutrition
        type: float
        initial_value: 0.5

  # Weapon profile
  - profile_name: weapon_stats
    variables:
      - name: damage
        type: float
        initial_value: 10.0

  # Tool profile
  - profile_name: tool_stats
    variables:
      - name: efficiency
        type: float
        initial_value: 1.0

  # Clothing profile
  - profile_name: clothing_stats
    variables:
      - name: warmth
        type: float
        initial_value: 0.3
```

**Usage**:
- Each item instance has a `profile_name` (e.g., "food_stats")
- Item VFS storage allocates space for all profiles
- Agent observations include item VFS (padded to fixed size)

## Configuration Patterns

### Pattern 1: Read-Only Computed Variable

```yaml
- name: avg_health
  type: float
  expression: "bar.health"
  description: "Current health (read-only computed)"
```

**Access Control**:
```yaml
readable_by: ["agent", "engine"]
writable_by: []  # No writers (purely computed)
```

### Pattern 2: State Machine Flag

```yaml
- name: is_sleeping
  type: bool
  initial_value: false
  description: "Agent is currently sleeping"
```

**Usage**:
- Engine sets to `true` on BED interaction
- Engine sets to `false` after sleep duration expires
- Observable for state-dependent behavior

### Pattern 3: Accumulator

```yaml
- name: total_food_consumed
  type: int
  initial_value: 0
  description: "Total food items consumed (lifetime)"
```

**Usage**:
- Engine increments on FOOD consumption
- Observable for long-term strategy tracking

### Pattern 4: Threshold Detection

```yaml
- name: is_healthy
  type: bool
  expression: "bar.health > 0.7"
```

**Usage**:
- Recomputed every tick
- Used in reward shaping or action preconditions

### Pattern 5: Vector State

```yaml
- name: home_position
  type: vec2i
  initial_value: [0, 0]
  description: "Agent's home position (set once at spawn)"
```

**Usage**:
- Engine sets once at spawn
- Observable for homing behavior

## Troubleshooting

### Issue: Variable Not Appearing in Observations

**Symptom**: Variable defined in `vfs_profiles.yaml` but not observable by agent.

**Cause**: Missing access control configuration in `variables_reference.yaml`.

**Solution**:
1. Add variable to `variables_reference.yaml`
2. Set `readable_by: ["agent", ...]`
3. Verify observation dimension increased

### Issue: Circular Dependency Error

**Symptom**: `CircularDependencyError` at config load time.

**Cause**: Variables reference each other in a cycle.

**Solution**:
1. Review expression dependencies
2. Break cycle by using initial_value for one variable
3. Reorder variable definitions (order doesn't matter, dependencies do)

### Issue: Type Mismatch Error

**Symptom**: `TypeCheckError: Variable 'x' declared as bool but expression returns int`.

**Cause**: Expression result type doesn't match declared type.

**Solution**:
1. Fix expression to return correct type
2. Use comparison operator to convert to bool: `x > 0`
3. Change declared type to match expression result

### Issue: Undefined Variable Error

**Symptom**: `KeyError: Variable 'x' not found in schema`.

**Cause**: Expression references variable that doesn't exist.

**Solution**:
1. Check spelling of variable name
2. Ensure referenced variable is in same profile
3. Use namespace access for cross-scope references (`bar.energy`)

### Issue: Observation Dimension Mismatch

**Symptom**: `AssertionError: Expected obs_dim=X, got Y`.

**Cause**: VFS variables changed, breaking checkpoint compatibility.

**Solution**:
1. Run dimension regression tests
2. Update expected dimensions in tests
3. Retrain checkpoints with new observation space

## Best Practices

### 1. Prefer Static Over Computed When Possible

**Why**: Static variables are faster (no recomputation) and easier to debug.

**Example**:
```yaml
# GOOD: Static (if updated by engine)
- name: day_count
  type: int
  initial_value: 0

# BAD: Computed (if never changes)
- name: day_count
  type: int
  expression: "temporal.tick / 24"  # Wasteful if never used
```

### 2. Use Descriptive Variable Names

**Why**: Variable names appear in logs, debugging output, and observations.

**Example**:
```yaml
# GOOD
- name: is_crisis
  type: bool
  expression: "bar.energy < 0.2 or bar.health < 0.2"

# BAD
- name: x
  type: bool
  expression: "bar.energy < 0.2 or bar.health < 0.2"
```

### 3. Document Variable Semantics

**Why**: Variables are referenced across multiple systems (observations, actions, rewards).

**Example**:
```yaml
- name: motivation
  type: float
  initial_value: 1.0
  description: "Intrinsic motivation multiplier [0.5-2.0] (affects exploration)"
```

### 4. Minimize Observable Variables

**Why**: Each observable variable increases `obs_dim`, slowing training.

**Pattern**: Only expose variables agents need for decision-making.

```yaml
# Agent-observable (decision-relevant)
- name: is_crisis
  readable_by: ["agent", "engine"]

# Hidden (internal state)
- name: debug_flag
  readable_by: ["engine"]
```

### 5. Use Profiles for Item Families

**Why**: Profiles enable transfer learning across item types.

**Example**:
```yaml
item_profiles:
  # All consumables share nutrition
  - profile_name: consumable_stats
    variables:
      - name: nutrition
        type: float
        initial_value: 0.5

  # All durables share durability
  - profile_name: durable_stats
    variables:
      - name: durability
        type: int
        initial_value: 100
```

### 6. Test Profiles in Isolation

**Why**: Complex profiles can cause subtle bugs.

**Pattern**: Create test configs with minimal profiles:

```yaml
# configs/test/vfs_profiles_smoke/vfs_profiles.yaml
global_profile:
  variables:
    - name: test_flag
      type: bool
      initial_value: true
```

## Validation

### Compile-Time Validation (Pydantic)

- Schema validation on YAML load
- XOR constraint (initial_value XOR expression)
- Type checking (int/float/bool/vec2i/vec3i)
- Unique variable names within profile

### Runtime Validation (Compiler)

- Expression parsing (syntax validation)
- Type checking (result type matches declared type)
- Dependency resolution (topological sort)
- Circular dependency detection

### Integration Tests

- Observation dimension regression tests
- Profile compilation tests
- Expression evaluation tests
- Access control tests

## Integration with Other Systems

### Universe Compiler Integration

VFS Profiles are compiled by the Universe Compiler (UAC) during config validation:

**Pipeline**:
1. Load `vfs_profiles.yaml` → Pydantic validation
2. Parse expressions → AST generation
3. Build dependency graph → Topological sort
4. Type check expressions → Schema validation
5. Emit compiled profile → Runtime execution

### Observation Builder Integration

Observable variables are integrated into agent observations:

**Pipeline**:
1. Load `variables_reference.yaml` → Access control
2. Extract `readable_by: ["agent"]` variables
3. Compute VFS observation dimensions
4. Build observation tensor at runtime

### Effect System Integration (Future)

VFS variables will be readable/writable by Effects:

**Example Effect**:
```yaml
effects:
  - id: increment_crisis_duration
    writes:
      - variable_id: crisis_duration
        expression: "crisis_duration + 1"
```

## Migration Guide

### Adding VFS Profiles to Existing Config

**Step 1**: Create `vfs_profiles.yaml`:
```yaml
agent_profile:
  variables:
    - name: motivation
      type: float
      initial_value: 1.0
```

**Step 2**: Add to `variables_reference.yaml`:
```yaml
variables:
  - id: motivation
    scope: agent
    type: scalar
    lifetime: episode
    readable_by: ["agent", "engine"]
    writable_by: ["engine"]
    default: 1.0
```

**Step 3**: Verify observation dimension:
```bash
uv run pytest tests/test_townlet/unit/vfs/test_observation_dimension_regression.py
```

**Step 4**: Retrain checkpoints (observation space changed).

## Reference Files

**Test Configurations**:
- `configs/test/vfs_profiles_smoke/vfs_profiles.yaml` - Minimal test profile
- `configs/test/items_smoke/vfs_profiles.yaml` - Item profiles test

**Source Files**:
- `src/townlet/vfs/profiles.py` - Profile compiler
- `src/townlet/config/vfs_profiles_config.py` - Pydantic schemas
- `src/townlet/vfs/registry.py` - Runtime storage
- `src/townlet/vfs/observation_builder.py` - Observation integration

**Tests**:
- `tests/test_townlet/unit/vfs/test_expression_integration.py` - Profile compilation tests

## See Also

- `docs/config-schemas/variables.md` - VFS Variables reference
- `docs/plans/2025-11-06-variables-and-features-system.md` - VFS design document
- `docs/plans/vfs_uplift/` - VFS implementation plans
- `src/townlet/universe/compiler.py` - Universe Compiler (UAC)
