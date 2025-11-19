# effects.yaml Configuration

---
## AI-Friendly Frontmatter

**Purpose**: Declarative effect definitions with command pipeline language for HAMLET simulation behavior

**When to Read**: Working with effects system, affordance interactions, item behaviors, temporal mechanics, or any state mutation logic

**AI-Friendly Summary**:
The Effects System is HAMLET's foundational command pipeline language for all simulation behavior. It provides declarative, reusable effect definitions that attach to agents, items, affordances, or global world state. Each effect has lifecycle hooks (on_spawn, on_tick, on_despawn) that execute command pipelines for state mutation. Effects support four reapply policies (stack, renew, merge, replace) and use VFS expression language for all value computations. All commands are compile-time validated for path correctness and type safety. Effects are the bedrock of World Compiler (T0 Pillar 3) - bars, VFS, cascades, items, and affordances all use effects for mutation logic.

**Reading Strategy**:
- **Quick Reference**: Jump to "Field Reference" for specific field documentation
- **Examples**: See "Effect Examples" section for real patterns from effects_smoke config
- **Command Types**: Read "Command Pipeline Language" for available operations
- **First-Time Users**: Read "Overview" → "File Structure" → "Reapply Policies" → "Effect Examples"

**Related Documents**:
- `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md` - Complete design document
- `docs/plans/vfs_uplift/2025-11-19-task-3-1-effects-dtos.md` - Implementation plan
- `docs/config-schemas/variables.md` - VFS variable definitions
- `docs/config-schemas/affordances.md` - Affordance configuration (uses effects)
- Expression language: See `docs/plans/vfs_uplift/2025-11-19-task-1-2-expression-parser.md`

---

**Location**: `<config_pack>/effects.yaml` (experiment-level)

**Status**: Phase 3 Implementation (TASK-003 Complete)

**Pattern**: Effects is the foundational command language for ALL simulation behavior. All behavioral parameters must be explicitly specified (no-defaults principle) to ensure reproducibility.

---

## Overview

The Effects System is HAMLET's declarative command pipeline language that provides a unified way to express all simulation behavior: affordance interactions, item dynamics, temporal changes, meter cascades, and agent state mutations.

### Key Principles

1. **Reusable Effect Catalog**: Define effects once, reference by ID everywhere
2. **Command Pipeline Execution**: Ordered, explicit commands at lifecycle stages
3. **VFS Expression Language**: Pure functional expressions for all value computations
4. **Compile-Time Validation**: Type checking for paths, references, and expressions
5. **Scope-Aware Context**: Effects attach to global/agent/item/affordance with appropriate access

### Architectural Position

Effects is the **bedrock** of the World Compiler (T0 Pillar 3):
- **Compiled First**: Before bars, VFS, cascades, items, affordances
- **Used By All**: All other World components use effects for mutation logic
- **Type-Safe**: Expression ASTs compiled at load time, validated against VFS schema
- **GPU-Native**: Executes on GPU tensors via CommandExecutor

### Benefits

1. **Declarative Configuration**: Change simulation behavior without code changes
2. **Reproducibility**: Effects part of compiled world with provenance tracking
3. **Composability**: Mix and match effects across affordances, items, and agents
4. **Pedagogical Value**: Expose complex behaviors (stacking, merging, timing) as teaching moments
5. **Performance**: Pre-compiled expression ASTs, vectorized execution

---

## File Structure

```yaml
version: "1.0"

effect_definitions:
  - id: string                     # Unique effect identifier
    description: string            # Human-readable description (optional)
    scope: global|agent|item|affordance  # Where effect attaches
    duration: int                  # Ticks until auto-despawn (REQUIRED)
    intensity: float               # Default intensity multiplier
    reapply_policy: stack|renew|merge|replace  # Reapply behavior (REQUIRED)
    observable: bool               # Whether agents can observe this effect

    # Lifecycle command pipelines
    on_spawn: CommandConfig[]      # Execute when effect spawned
    on_tick: CommandConfig[]       # Execute each step while active
    on_despawn: CommandConfig[]    # Execute before removal
```

**Required Fields**:
- `id`: Unique identifier for referencing this effect
- `scope`: Determines attachment point and available context
- `duration`: Lifecycle length (auto-despawn when reaches 0)
- `reapply_policy`: Behavior when same effect spawned on same target
- All command pipeline fields (`on_spawn`, `on_tick`, `on_despawn`) must be present (can be empty lists)

**Optional Fields**:
- `description`: Documentation string
- `intensity`: Default 1.0 (can be overridden at spawn time)
- `observable`: Default false (hidden from agent observations)

---

## Field Reference

### Top-Level Fields

#### `version` (string, REQUIRED)

**Type**: `str`
**Required**: Yes
**Example**: `version: "1.0"`

Effects schema version. Always "1.0" for current implementation.

**Validation**: Must be "1.0"

---

#### `effect_definitions` (list, REQUIRED)

**Type**: `list[EffectDefinition]`
**Required**: Yes (can be empty list)
**Example**: See "Effect Examples" section

List of effect definitions. Each effect is a reusable simulation behavior with lifecycle hooks.

---

### Effect Definition Fields

#### `id` (string, REQUIRED)

**Type**: `str`
**Required**: Yes
**Example**: `id: "energy_regen"`

Unique identifier for this effect. Used to spawn effects via `spawn_effect(effect_id=...)` or reference in affordance/item configs.

**Validation**:
- Must be unique across all effects in catalog
- Recommended naming: lowercase with underscores
- Must match regex: `^[a-z_][a-z0-9_]*$`

**Use Cases**:
- Affordances spawn effects when interacted with
- Items apply effects when used
- Cascades trigger conditional effects
- Temporal systems apply periodic effects

---

#### `description` (string, OPTIONAL)

**Type**: `str`
**Required**: No
**Example**: `description: "Regenerates energy over time"`

Human-readable description of effect behavior. Used for documentation and debugging.

**Best Practices**:
- Describe the observable behavior, not implementation details
- Mention key parameters (duration, intensity impact)
- Note any special interactions or side effects

---

#### `scope` (enum, REQUIRED)

**Type**: `"global" | "agent" | "item" | "affordance"`
**Required**: Yes
**Example**: `scope: agent`

Determines where the effect can attach and what context is available to commands.

**Scope Semantics**:

**`agent`** - Effect attaches to individual agents
- **Access**: `target.bar.*`, `target.vfs.*`, `target.position`
- **Storage**: Per-agent effect list `[num_agents]`
- **Examples**: `energy_regen`, `poison`, `caffeinated`, `hungry`
- **Typical Duration**: 1-100 ticks

**`item`** - Effect attaches to item instances
- **Access**: `target.vfs.*`, `target.position`, `target.holder_agent`
- **Storage**: Per-item effect list `[num_items]`
- **Examples**: `item_decay`, `flaming`, `cursed`, `enchanted`
- **Typical Duration**: 10-1000 ticks (long-lived items)

**`global`** - Effect attaches to world state
- **Access**: `global.vfs.*`, `global.bar.*` (if global bars exist)
- **Storage**: Single global effect list
- **Examples**: `day_cycle`, `nighttime`, `heatwave`, `rush_hour`
- **Typical Duration**: 100-10000 ticks (persistent world state)

**`affordance`** - Effect attaches to affordance instances
- **Access**: `target.vfs.*`, `target.position`, `target.availability`
- **Storage**: Per-affordance effect list `[num_affordances]`
- **Examples**: `broken`, `locked`, `occupied`, `on_cooldown`
- **Typical Duration**: 5-50 ticks (temporary state changes)

**Path Resolution**:
- `target.*` resolves to the entity the effect is attached to (scope-dependent)
- `global.*` always resolves to world state
- `self.*` resolves to the effect instance itself (for effect-local state)
- `temporal.*` provides current tick, time-of-day, etc.

---

#### `duration` (int, REQUIRED)

**Type**: `int` (positive)
**Required**: Yes
**Example**: `duration: 20`

Number of ticks before effect auto-despawns. Counts down each time `effect_manager.tick()` is called.

**Lifecycle**:
1. Spawn at tick N: `duration_remaining = duration`, `elapsed_ticks = 0`
2. Each tick: `duration_remaining -= 1`, `elapsed_ticks += 1`
3. Execute `on_tick` commands while `duration_remaining > 0`
4. When `duration_remaining == 0`: Execute `on_despawn`, remove from active effects

**Special Values**:
- `duration: 1` - Instant effect (only on_spawn executes, then immediate despawn)
- `duration: -1` - Future: Permanent effect (never auto-despawns) - NOT IMPLEMENTED

**Validation**: Must be positive integer

**Interaction with Reapply Policies**:
- `renew` policy resets `duration_remaining` to `duration`
- `merge` policy does NOT affect duration (only intensity)
- `stack` creates new instance with own duration
- `replace` despawns old (ending its duration) and spawns new

---

#### `intensity` (float, OPTIONAL)

**Type**: `float`
**Required**: No (default: 1.0)
**Example**: `intensity: 1.0`

Default intensity multiplier for effect strength. Can be overridden when spawning via `spawn_effect(..., intensity=2.5)`.

**Usage in Commands**:
```yaml
on_tick:
  - modify: target.bar.energy
    value: "target.bar.energy + (0.05 * intensity)"  # intensity is available as variable
```

**Typical Patterns**:
- **Scaling Effects**: Multiply all value changes by intensity
- **Threshold Effects**: Use intensity in conditionals (`if intensity > 2.0 then ...`)
- **Diminishing Returns**: `sqrt(intensity)` or `log(1 + intensity)`

**Interaction with Reapply Policies**:
- `stack`: Each instance has own intensity (can differ)
- `renew`: Keeps existing intensity (or uses new if higher)
- `merge`: `intensity += new_intensity` (cumulative stacking)
- `replace`: Old intensity discarded, new intensity used

**Validation**: Must be non-negative float

---

#### `reapply_policy` (enum, REQUIRED)

**Type**: `"stack" | "renew" | "merge" | "replace"`
**Required**: Yes
**Example**: `reapply_policy: renew`

Determines behavior when `spawn_effect(effect_id)` is called on entity that already has this effect active.

**Policy Details**:

##### `stack` - Create Independent Instance

**Behavior**: Each application creates a new, independent effect instance

```yaml
reapply_policy: stack

# Timeline:
# Tick 1: spawn_effect("health_boost", duration=5) → Instance A (expires tick 6)
# Tick 3: spawn_effect("health_boost", duration=5) → Instance B (expires tick 8)
# Result: Both instances tick independently, both execute commands
```

**Use Cases**:
- Food digestion cycles (each meal has own timer)
- Damage-over-time stacking (multiple poison sources)
- Buff stacking (multiple temporary stat boosts)

**Performance**: O(num_instances) - can create many instances if spammed

**Command Execution**: All instances execute their commands (effects compound!)

---

##### `renew` - Refresh Duration

**Behavior**: Reset `duration_remaining` to `duration`, keep single instance

```yaml
reapply_policy: renew

# Timeline:
# Tick 1: spawn_effect("energy_regen", duration=20) → Instance A (expires tick 21)
# Tick 15: spawn_effect("energy_regen", duration=20) → Instance A refreshed (now expires tick 35)
# Result: Single instance, timer extended
```

**Use Cases**:
- "Well fed" status (eating extends the buff)
- Regeneration effects (activity refreshes the healing)
- Temporary buffs that extend with repeated application

**Performance**: O(1) - always single instance

**Command Execution**: Single execution per tick (no compounding)

**Implementation Detail**: Intensity can optionally be updated to max(old, new)

---

##### `merge` - Increase Intensity

**Behavior**: Accumulate intensity, keep single instance

```yaml
reapply_policy: merge

# Timeline:
# Tick 1: spawn_effect("poison", intensity=1.0, duration=20) → Instance A (intensity=1.0)
# Tick 5: spawn_effect("poison", intensity=0.5, duration=20) → Instance A (intensity=1.5)
# Result: Single instance, stronger effect
```

**Use Cases**:
- Cumulative drug dosage (multiple applications stack strength)
- Poison stacking (multiple sources increase damage rate)
- Debuff accumulation (repeated failures worsen penalty)

**Performance**: O(1) - always single instance

**Command Execution**: Single execution per tick, but with higher intensity (commands scale by intensity)

**Best Practice**: Use `intensity` in expressions for proper scaling:
```yaml
on_tick:
  - modify: target.bar.health
    value: "target.bar.health - (0.02 * intensity)"  # Scales with merges
```

---

##### `replace` - Clear Old, Spawn New

**Behavior**: Despawn existing instance (execute `on_despawn`), spawn new instance (execute `on_spawn`)

```yaml
reapply_policy: replace

# Timeline:
# Tick 1: spawn_effect("currently_eating", duration=10) → Instance A
# Tick 5: spawn_effect("currently_eating", duration=10) → Instance A despawned, Instance B spawned
# Result: Only newest instance exists
```

**Use Cases**:
- "Currently doing X" status (only one action at a time)
- Replacing buffs (new overwrites old completely)
- State transitions (entering new state exits previous)

**Performance**: O(1) - always single instance

**Command Execution**: Old effect's `on_despawn` executes, new effect's `on_spawn` executes

**Important**: Despawn is explicit (not silent) - useful for cleanup logic

---

#### `observable` (bool, OPTIONAL)

**Type**: `bool`
**Required**: No (default: `false`)
**Example**: `observable: true`

Whether agents can observe this effect in their observations.

**True** - Effect visible to agent:
```yaml
observable: true
# Examples: "hungry", "wet", "caffeinated", "injured"
# Agent should know about these for decision-making
```

**False** - Effect hidden from agent:
```yaml
observable: false
# Examples: "in_trouble_at_work", "cursed", "monitored", "marked_for_promotion"
# Agent cannot directly observe, but may infer from consequences
```

**Future Integration**: Observable effects will be added to observation spec by VFS observation builder. Current implementation marks for future use but does not yet modify observations.

**Pedagogical Value**: Hidden effects teach agents to infer latent state from consequences (e.g., "Why is my boss mad? Oh, I must be in trouble")

---

#### `on_spawn` (list[CommandConfig], REQUIRED)

**Type**: `list[CommandConfig]`
**Required**: Yes (can be empty list)
**Example**:
```yaml
on_spawn:
  - modify: target.bar.health
    value: "target.bar.health + 0.2"
```

Command pipeline executed **immediately** when effect spawned. Executes before first tick.

**Execution Order**:
1. Effect instance created
2. `on_spawn` commands execute
3. Effect added to active effects
4. (Later) `on_tick` commands execute each step

**Typical Uses**:
- Instant stat changes (health boost, energy penalty)
- Set initial flags (`target.vfs.is_buffed = true`)
- Trigger secondary effects (`spawn_effect("visual_glow")`)
- Initialization logic for complex effects

**Performance**: Executes once per spawn (not every tick)

**Empty List**: Valid pattern for effects with no spawn logic (all behavior in on_tick)

---

#### `on_tick` (list[CommandConfig], REQUIRED)

**Type**: `list[CommandConfig]`
**Required**: Yes (can be empty list)
**Example**:
```yaml
on_tick:
  - modify: target.bar.energy
    value: "target.bar.energy + (0.05 * intensity)"
```

Command pipeline executed **every tick** while effect active. Core effect behavior.

**Execution Order**:
1. `effect_manager.tick()` called (in `env.step()` after action execution)
2. For each active effect: execute `on_tick` commands
3. Decrement `duration_remaining`
4. If `duration_remaining == 0`, execute `on_despawn` and remove

**Typical Uses**:
- Regeneration/degeneration (bars change over time)
- Periodic checks (if conditions then trigger)
- State updates (modify VFS variables based on current state)
- Temporal logic (day/night cycles, time-based state changes)

**Performance**: Executes every tick for every active effect - keep command lists short!

**Empty List**: Valid for instant-only effects (all logic in `on_spawn`)

**Important**: Effects tick AFTER action execution and AFTER cascades, so they can react to current state.

---

#### `on_despawn` (list[CommandConfig], REQUIRED)

**Type**: `list[CommandConfig]`
**Required**: Yes (can be empty list)
**Example**:
```yaml
on_despawn:
  - modify: target.vfs.is_buffed
    value: false
```

Command pipeline executed **immediately** before effect removed from active effects.

**Execution Triggers**:
1. `duration_remaining` reaches 0 (natural expiration)
2. `reapply_policy: replace` triggered (old effect replaced)
3. Manual despawn via `despawn_effect()` (future API)
4. Entity destroyed (cleanup on death/removal)

**Typical Uses**:
- Cleanup flags (`target.vfs.is_buffed = false`)
- Reversal of on_spawn changes (if not handled by duration naturally)
- Final effects (penalty for buff expiring, reward for surviving duration)
- Logging/analytics (record effect completion)

**Performance**: Executes once per despawn (not every tick)

**Empty List**: Valid pattern for effects with no cleanup logic

**Important**: `on_despawn` executes even if effect interrupted (unlike some game engines that only execute on natural expiration)

---

## Command Pipeline Language

Effects execute commands at lifecycle stages (on_spawn, on_tick, on_despawn). Commands are typed, validated at compile-time, and executed on GPU tensors.

### Supported Command Types

**Current Implementation** (Phase 3):
- ✅ `modify` - Set variable/bar value using expression

**Future Extensions** (Phase 4+):
- ⏳ `spawn_effect` - Spawn another effect
- ⏳ `spawn_item` - Create item instance
- ⏳ `if` - Conditional execution
- ⏳ `for_each` - Iterate over collections

See `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md` for complete command language specification.

---

### `modify` Command

**Purpose**: Set target variable/bar to new value computed from expression

**Schema**:
```yaml
- modify: <path>
  value: <expression>
```

**Fields**:
- `modify` (string, REQUIRED): Path to target variable (e.g., `target.bar.energy`, `global.vfs.is_night`)
- `value` (string, REQUIRED): Expression string evaluating to new value

**Path Resolution**:
- `target.*`: Entity effect is attached to (scope-dependent)
  - `target.bar.energy`: Agent's energy bar (agent scope)
  - `target.vfs.durability`: Item's durability variable (item scope)
- `global.*`: World state
  - `global.vfs.is_night`: Global boolean flag
  - `global.bar.economy`: Global economy meter (if exists)
- `self.*`: Effect instance state (future: effect-local variables)
- `temporal.*`: Time context
  - `temporal.tick`: Current environment step count
  - `temporal.time_of_day`: Hour in 24-hour cycle

**Expression Language**:
Effects use HAMLET's VFS expression language (pure functional, type-safe):

**Operators**:
- Arithmetic: `+`, `-`, `*`, `/`, `%`, `**` (power)
- Comparison: `<`, `<=`, `>`, `>=`, `==`, `!=`
- Logical: `and`, `or`, `not`
- Ternary: `<cond> if <test> else <alt>`

**Functions** (Current):
- `clamp(value, min, max)`: Clamp value to range
- `min(a, b)`: Minimum of two values
- `max(a, b)`: Maximum of two values
- `abs(x)`: Absolute value
- `sqrt(x)`: Square root
- `sin(x)`, `cos(x)`: Trigonometric functions

**Variables Available in Expressions**:
- `intensity`: Effect instance intensity
- All paths: `target.bar.*`, `target.vfs.*`, `global.vfs.*`, `temporal.*`

**Type Safety**:
- Expressions type-checked at compile-time
- Path must exist in VFS schema (validated by CommandCompiler)
- Expression return type must match target path type
- Type mismatches cause compilation errors (fail-fast)

**Examples**:

```yaml
# Simple increment (WRONG - doesn't clamp)
- modify: target.bar.energy
  value: "target.bar.energy + 0.05"

# Clamped increment (CORRECT - bars bounded [0,1])
- modify: target.bar.energy
  value: "clamp(target.bar.energy + (0.05 * intensity), 0.0, 1.0)"

# Conditional modification
- modify: target.bar.health
  value: "target.bar.health - 0.1 if target.vfs.is_poisoned else target.bar.health"

# Temporal logic
- modify: global.vfs.is_night
  value: "temporal.tick % 24 >= 18"

# Complex computation
- modify: target.bar.mood
  value: "clamp(target.bar.mood + (sqrt(intensity) * 0.02), 0.0, 1.0)"
```

**Limitations** (Phase 3):
- ❌ No user-defined functions (only built-in functions)
- ❌ No side effects (pure functional)
- ❌ No loops in expressions (use `for_each` command in Phase 4)
- ❌ No mutation (each modify creates new value, does not modify in place within expression)

**Performance**:
- Expressions compiled to AST at world load time (one-time cost)
- AST evaluated on GPU tensors each execution (vectorized)
- Pre-compilation eliminates runtime parsing overhead

---

## Effect Examples

Real examples from `configs/test/effects_smoke/effects.yaml`:

### Example 1: Energy Regeneration (RENEW Policy)

```yaml
- id: "energy_regen"
  scope: agent
  duration: 20
  intensity: 1.0
  reapply_policy: renew
  observable: true

  on_spawn: []

  on_tick:
    - modify: target.bar.energy
      value: "target.bar.energy + (0.05 * intensity)"

  on_despawn: []
```

**Behavior**:
- Regenerates 5% energy per tick for 20 ticks
- If reapplied while active, resets duration to 20 (extends buff)
- Observable by agent (shows as "energy_regen" status)
- No spawn/despawn logic (all behavior in on_tick)

**Use Case**: Food consumption grants sustained energy recovery

---

### Example 2: Instant Health Boost (STACK Policy)

```yaml
- id: "health_boost"
  scope: agent
  duration: 1
  intensity: 1.0
  reapply_policy: stack
  observable: true

  on_spawn:
    - modify: target.bar.health
      value: "target.bar.health + (0.2 * intensity)"

  on_tick: []

  on_despawn: []
```

**Behavior**:
- Instant +20% health when spawned
- Duration 1 means immediate despawn after spawn (no ticks)
- Each application stacks (multiple boosts possible)
- All logic in on_spawn (instant effect pattern)

**Use Case**: Consumable healing items (each use gives separate heal)

---

### Example 3: Poison (MERGE Policy)

```yaml
- id: "poison"
  scope: agent
  duration: 20
  intensity: 1.0
  reapply_policy: merge
  observable: true

  on_spawn: []

  on_tick:
    - modify: target.bar.health
      value: "target.bar.health - (0.02 * intensity)"

  on_despawn: []
```

**Behavior**:
- Deals 2% health damage per tick
- If reapplied, intensity accumulates (1.0 → 1.5 → 2.0)
- Single instance with escalating damage
- Duration not affected by reapplication (keeps counting down)

**Use Case**: Multiple poison sources stack severity (not duration)

**Important**: Note how `intensity` scales the damage - crucial for MERGE policy!

---

### Example 4: Global Day/Night Cycle

```yaml
- id: "global_day_cycle"
  scope: global
  duration: 1000
  intensity: 1.0
  reapply_policy: stack
  observable: false  # World state, not agent-specific

  on_spawn: []

  on_tick:
    - modify: global.vfs.is_night
      value: "temporal.tick % 24 >= 18"

  on_despawn: []
```

**Behavior**:
- Sets global `is_night` flag based on time-of-day
- Updates every tick using temporal context
- Duration 1000 for long-lived world state effect
- Not observable (global state, not agent-specific status)

**Use Case**: Environment spawns this on startup for day/night cycles

**Note**: Uses `temporal.tick` for time-based logic, `global.vfs.*` for world state

---

## Compilation and Validation

Effects are compiled by the World Compiler as part of universe compilation:

### Compilation Pipeline

```
effects.yaml → EffectsConfig (Pydantic) → EffectCatalog (runtime) → EffectManager (execution)
     ↓                ↓                          ↓                           ↓
  Parse YAML    Validate schema          Compile commands             Execute commands
                Type-check paths        Pre-compile ASTs             Update GPU tensors
```

### Compile-Time Checks

**Schema Validation** (Pydantic):
- All required fields present
- Field types correct (int, float, string, enum)
- Enum values valid (scope, reapply_policy)
- List structures correct (on_spawn, on_tick, on_despawn)

**Path Validation** (CommandCompiler):
- `modify` paths exist in VFS schema
- Paths accessible from effect scope (e.g., agent-scoped effects can't modify global bars)
- Path types match expression return types

**Expression Validation** (ExpressionParser + TypeChecker):
- Expressions parse correctly (valid syntax)
- Types inferred correctly (type checker validates operations)
- Return type matches target path type
- Variables referenced exist in context (target, global, temporal, intensity)

**Reference Validation** (Future Phase 4):
- `spawn_effect` effect_id exists in catalog
- `spawn_item` item_type exists in item catalog
- Circular dependencies detected (effect A spawns B spawns A)

### Compilation Errors

**Invalid Path**:
```
TypeCheckError: Path 'target.bar.invalid' not found in schema.
Available: ['target.bar.energy', 'target.bar.health', ...]
```

**Type Mismatch**:
```
TypeCheckError: Type mismatch for path 'target.bar.energy':
expected float, got bool
```

**Expression Syntax Error**:
```
ParseError: Invalid expression syntax at position 15:
'target.bar.energy +' (expected operand)
```

**Scope Violation** (Future):
```
ScopeError: agent-scoped effect cannot modify global.bar.economy
(cross-scope mutation not allowed)
```

### Performance Optimization

**Pre-Compilation**:
- Expression strings → AST at world load time (one-time cost)
- ASTs stored in CommandNode.value_ast (reused every execution)
- Eliminates runtime parsing overhead

**Vectorized Execution**:
- CommandExecutor evaluates ASTs on GPU tensors
- Entire batch of agents processed in parallel
- Single CUDA kernel for expression evaluation

**Scoped Collections**:
- Effects stored in scope-specific collections (agent_effects, global_effects, etc.)
- Prevents O(all_effects) searches for scoped operations
- Typical overhead: <1% of step time for 10-50 active effects

---

## Integration with Other Systems

### Affordances

Affordances spawn effects when interacted with:

```yaml
# affordances.yaml
affordances:
  - id: "bed"
    on_interact:
      spawn_effect: "energy_regen"  # References effect from effects.yaml
      duration_override: 30          # Optional: override default duration
      intensity_override: 1.5        # Optional: override default intensity
```

**Integration**: Affordance compiler validates `spawn_effect` references exist in EffectCatalog

### Items (Future Phase 4)

Items apply effects when used/equipped:

```yaml
# items.yaml (future)
items:
  - id: "healing_potion"
    on_use:
      - spawn_effect: "health_boost"
        target: "user"
        intensity: 2.0  # Stronger than default
```

### Cascades (Future Phase 4)

Cascades can conditionally spawn effects:

```yaml
# cascades.yaml (future)
cascades:
  - source: energy
    targets:
      - target: health
        condition: "source < 0.2"  # Low energy damages health
        on_trigger:
          spawn_effect: "energy_crash"  # Spawns debuff effect
```

### VFS Profiles (Future Phase 4)

VFS profiles define variables that effects modify:

```yaml
# vfs_profiles.yaml
variables:
  - id: "is_buffed"
    scope: agent
    type: bool
    default: false
    readable_by: ["agent", "engine"]
    writable_by: ["engine"]  # Effects can modify via CommandExecutor
```

**Integration**: Effect commands validated against VFS schema (paths must exist)

---

## Best Practices

### Naming Conventions

**Effect IDs**:
- Lowercase with underscores: `energy_regen`, `health_boost`
- Descriptive of behavior, not source: `caffeinated` (not `drank_coffee`)
- Verb forms for actions: `regenerating`, `bleeding`
- Noun forms for states: `poisoned`, `buffed`, `cursed`

**Descriptions**:
- Active voice: "Regenerates energy over time" (not "Energy is regenerated")
- Mention key parameters: "Deals 2% health damage per tick"
- Note interactions: "Stacks with other poison sources"

### Duration Guidelines

**Instant Effects**: `duration: 1`
- All logic in `on_spawn`
- Empty `on_tick` and `on_despawn`
- Use for consumables, instant stat changes

**Short-Term Effects**: `duration: 5-20`
- Typical agent buffs/debuffs
- Food digestion, temporary stat boosts
- Balance: Long enough to matter, short enough to require reapplication

**Medium-Term Effects**: `duration: 50-200`
- Item decay, slow transformations
- Multi-tick processes (crafting, building)

**Long-Term Effects**: `duration: 500-5000`
- Global world state (day/night cycles)
- Persistent item enchantments
- Slow environmental changes

**Avoid**: Very short durations (<5) for on_tick effects (high overhead, little benefit)

### Intensity Patterns

**Linear Scaling** (simple, predictable):
```yaml
value: "target.bar.energy + (0.05 * intensity)"
```

**Diminishing Returns** (prevents overpowering stacks):
```yaml
value: "target.bar.energy + (0.05 * sqrt(intensity))"
```

**Threshold Effects** (discrete breakpoints):
```yaml
value: "target.bar.energy + (0.1 if intensity > 2.0 else 0.05)"
```

**Avoid**: Hardcoded values that don't scale with intensity (breaks MERGE policy!)

### Reapply Policy Selection

**Use `stack` when**:
- Each application is independent (food digestion)
- Want cumulative effects (multiple damage sources)
- Duration should NOT reset

**Use `renew` when**:
- Want single instance with extended duration (buffs)
- Don't want intensity stacking (power cap)
- Encourage frequent reapplication (stay fed)

**Use `merge` when**:
- Want intensity stacking but single instance (poison)
- Severity should accumulate (cumulative dosage)
- Duration should NOT reset

**Use `replace` when**:
- Only one instance should exist (current action)
- Old effect should be interrupted (state transition)
- Want explicit on_despawn for old effect

### Performance Optimization

**Minimize on_tick Commands**:
- Executes every tick for every active effect
- Keep command lists short (1-3 commands ideal)
- Complex logic should be in expressions, not multiple commands

**Use Clamping**:
- Always clamp bar modifications: `clamp(value, 0.0, 1.0)`
- Prevents out-of-range values, reduces downstream checks

**Batch Related Modifications**:
- Modify multiple bars in single effect rather than spawning multiple effects
- Reduces active effect count, improves cache locality

**Avoid Redundant Effects**:
- Don't spawn `energy_regen` if already active (unless using stack policy intentionally)
- Check for existing effects before spawning (future API: `has_effect()`)

### Pedagogical Patterns

**"Interesting Failures"**:
- Low energy causing health damage (teaches resource management)
- Buff stacking leading to overpowered agents (teaches balance)
- Poison merging causing rapid death (teaches threat prioritization)

**Observable vs Hidden Effects**:
- Make causal effects observable (agent should know they're poisoned)
- Make latent states hidden (agent infers "boss is mad" from consequences)
- Teaches agents to model unobservable state from observations

**Reapply Policy Lessons**:
- Compare `stack` vs `renew` in curriculum (L1 vs L2)
- Show emergent behavior from different policies
- Let students experiment with policy changes without code changes

---

## Troubleshooting

### Common Issues

**Q: Effect not executing commands**
- Verify effect spawned correctly (`effect_manager.get_all_active_effects()`)
- Check `duration_remaining > 0` (may have already expired)
- Ensure `effect_manager.tick()` called in env.step()
- Verify commands are in correct lifecycle hook (on_spawn vs on_tick)

**Q: Type check error for valid path**
- Check VFS schema includes the path (`variables_reference.yaml`)
- Verify path accessible from effect scope (agent can't modify global bars directly)
- Ensure expression return type matches path type (bool vs float)

**Q: Effect spawned but not ticking**
- Check scope matches target entity (can't spawn agent-scoped effect on item)
- Verify `current_step` passed to `tick()` (required parameter)
- Ensure `env_state` passed for context building

**Q: Intensity not scaling properly**
- Verify expressions multiply by `intensity` variable
- Check merge policy used if expecting intensity stacking
- Ensure intensity passed at spawn time (defaults to 1.0)

**Q: Effects despawning too early/late**
- Check `duration` field matches intended tick count
- Verify `duration: 1` used for instant effects (common mistake: `duration: 0`)
- Remember tick occurs AFTER commands execute (duration=1 means spawn → tick → despawn)

### Validation Errors

**Missing Required Field**:
```yaml
# ERROR: Missing reapply_policy
- id: "energy_regen"
  scope: agent
  duration: 20
  # reapply_policy: renew  # REQUIRED!
```
**Fix**: Add `reapply_policy: <policy>` to every effect definition

**Invalid Scope**:
```yaml
# ERROR: Invalid scope value
- id: "buff"
  scope: "player"  # Should be: agent, item, global, or affordance
```
**Fix**: Use one of the four valid scope values

**Type Mismatch in Expression**:
```yaml
# ERROR: Boolean assigned to float path
- modify: target.bar.energy  # Type: float
  value: "target.bar.energy > 0.5"  # Returns: bool
```
**Fix**: Ensure expression returns correct type (use ternary for conditionals)

**Path Not Found**:
```yaml
# ERROR: Path doesn't exist in VFS schema
- modify: target.bar.mana  # If mana not defined in bars.yaml
  value: "0.5"
```
**Fix**: Add variable to VFS schema or correct path typo

---

## Future Enhancements

**Phase 4 Command Extensions**:
- `spawn_effect` - Spawn secondary effects from effects
- `spawn_item` - Create items dynamically
- `if`/`else` - Conditional command execution
- `for_each` - Iterate over collections (nearby agents, inventory items)

**Phase 5 Advanced Features**:
- Effect-local state (`self.vfs.*` variables specific to effect instance)
- Cross-scope effects (agent effect modifying nearby agents)
- Effect queries (`nearby_agents`, `held_items` in expressions)
- Dynamic duration modification (extend/reduce during execution)
- Effect interruption signals (`on_interrupt` hook for forced removal)

**Integration Improvements**:
- Observable effects in observation spec (auto-add to agent observations)
- Effect visualization in frontend (status icons, particle effects)
- Effect analytics (frequency, duration histograms, impact analysis)
- A/B testing framework (compare effect variants without code changes)

**Debugging Tools**:
- Effect execution logs (which commands executed, values before/after)
- Effect timelines (visualize spawns, ticks, despawns over time)
- Command trace mode (step through command execution)
- Expression debugger (inspect AST, intermediate values)

---

## See Also

- **Design Document**: `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md` - Complete architecture
- **Implementation Plan**: `docs/plans/vfs_uplift/2025-11-19-task-3-1-effects-dtos.md` - DTOs and catalog
- **VFS Variables**: `docs/config-schemas/variables.md` - Variable system that effects modify
- **Affordances**: `docs/config-schemas/affordances.md` - How affordances spawn effects
- **Expression Language**: `docs/plans/vfs_uplift/2025-11-19-task-1-2-expression-parser.md` - Expression syntax and semantics
- **Training Config**: `docs/config-schemas/training.md` - How to run experiments with effects

---

**Status**: Phase 3 Complete (TASK-003)
**Version**: 1.0
**Last Updated**: 2025-11-20
