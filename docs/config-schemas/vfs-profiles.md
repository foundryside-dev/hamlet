# VFS Profiles Configuration

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
      type: int
      initial_value: 0
      description: "Number of days elapsed"

    - name: is_night
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
      type: float
      initial_value: 1.0
      description: "Agent's intrinsic motivation multiplier"

    - name: is_crisis
      type: bool
      expression: "bar.energy < 0.2 or bar.health < 0.2"
      description: "True when agent is in resource crisis"

    - name: crisis_duration
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

      - name: is_spoiled
        type: bool
        expression: "self.age > 100"
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
| `name` | string | Unique variable name (within profile) |
| `type` | enum | Variable type (int, float, bool, vec2i, vec3i) |

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

**Self-reference (item scope)**:
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

Variables can appear in agent observations by configuring access control in `variables_reference.yaml`.

### Making Variables Observable

**Step 1**: Define variable in `vfs_profiles.yaml`:
```yaml
agent_profile:
  variables:
    - name: motivation
      type: float
      initial_value: 1.0
```

**Step 2**: Configure access control in `variables_reference.yaml`:
```yaml
variables:
  - id: motivation
    scope: agent
    type: scalar
    lifetime: episode
    readable_by: ["agent", "engine"]  # Agent can observe
    writable_by: ["engine"]
    default: 1.0
```

**Step 3**: Variable automatically appears in observations.

### Observation Dimensions

Each observable variable contributes to `obs_dim`:

| Type | Contribution |
|------|--------------|
| `int`, `float`, `bool` | +1 dim |
| `vec2i` | +2 dims |
| `vec3i` | +3 dims |

**Example**:
```yaml
agent_profile:
  variables:
    - name: motivation        # +1 dim
    - name: is_crisis         # +1 dim (bool converted to float)
    - name: crisis_duration   # +1 dim
```

**Total Agent VFS**: 3 dims

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
        expression: "self.durability <= 0"
        description: "True when weapon is broken"

      - name: damage
        type: float
        initial_value: 10.0
        description: "Base damage dealt per use"
```

**Usage**:
- `durability` decremented by engine on item use
- `is_broken` recomputed automatically
- `damage` used in combat calculations

### Example 6: Food Spoilage

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
        expression: "self.age > 100"
        description: "True when food has spoiled"

      - name: effective_nutrition
        type: float
        expression: "0.0 if self.age > 100 else nutrition"
        description: "Nutrition value (0 if spoiled)"
```

**Dependency Order**: `age` → `is_spoiled` → `effective_nutrition`

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
