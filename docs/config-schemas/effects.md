# effects.yaml Configuration

> ⚠️ **Restored to the live tree 2026-08-26 — one required field is missing and one whole vocabulary is absent.**
>
> **⚠️ `max_active_effects` is conditionally REQUIRED whenever effects are declared, and this
> 1700-line document mentions it zero times.** Omit it and the pack is refused.
>
> **⚠️ The `for_each` collection vocabulary is missing, and described as "future" while it
> ships.** Measured occurrence counts in this file: `all_agents` **0**, `switch` **0**,
> `delay` **0**, `sample` **0**. `for_each: all_agents` is the load-bearing surface for
> expressing a declarative step over simultaneous agent submissions, and it is not mentioned
> once — both PRD-0001 Trial O executors reached it only by reading
> `src/townlet/effects/collections.py`. Tracked as `hamlet-7eadeb214c`.
>
> **⚠️ `temporal.*` does NOT work in effects — the single reconciled account** (resolved at
> source 2026-08-26, because this doc and `expressions.md` disagreed):
> - The effects executor passes **`temporal={}`** (`effects/executor.py:43`, `:739`), so
>   `temporal.anything` raises here at runtime.
> - More fundamentally, **no schema builder emits a `temporal.*` key at all** —
>   `build_expression_schema` (`universe/compilers/vfs.py:136-152`) emits only `bar.*`,
>   `vfs.*`, `self.vfs.*`, `target.vfs.*` — so it fails at compile time first.
> - Only the **item spawn-rule** path populates it, with the single key `tick`
>   (`items/manager.py:624`, `:630`).
> - **✅ Correct working form: the bare `tick` variable**, the reserved engine-written step
>   counter (`universe/compilers/vfs.py:130-132`). Not `temporal.tick`.
>
> Tracked as `hamlet-7eadeb214c` (comment 262 carries the `max_active_effects` and `temporal.*`
> findings).
>
> Note `sqrt` / `sin` / `cos` fail at **type-check**, not parse — they are absent from
> `FUNCTION_SPECS`. See `expressions.md`, which carries a banner of its own.


---
## AI-Friendly Frontmatter

**Purpose**: Declarative effect definitions with command pipeline language for HAMLET simulation behavior

**When to Read**: Working with effects system, affordance interactions, item behaviors, temporal mechanics, or any state mutation logic

**AI-Friendly Summary**:
The Effects System is HAMLET's foundational command pipeline language for all simulation behavior. It provides declarative, reusable effect definitions (buffs/debuffs) that attach to agents, items, affordances, or global world state. Each effect has lifecycle hooks (on_spawn, on_tick, on_despawn, on_interrupt) that execute command pipelines for state mutation. Effects support four reapply policies (stack, renew, merge, replace) and use VFS expression language for all value computations. Commands include modify, spawn_effect, spawn_item, if/else conditionals, and for_each loops. All commands are compile-time validated for path correctness and type safety. Effects are the bedrock of World Compiler (T0 Pillar 3) - bars, VFS, cascades, items, and affordances all use effects for mutation logic.

**Reading Strategy**:
- **Quick Reference**: Jump to "Field Reference" for specific field documentation
- **Examples**: See "Effect Examples" section for real patterns
- **Command Types**: Read "Command Pipeline Language" for all available operations
- **First-Time Users**: Read "Overview" → "File Structure" → "Reapply Policies" → "Command Language" → "Examples"

**Related Documents**:
- `docs/zzz. archive/plans/archive/vfs_uplift/2025-11-19-effects-system-design.md` - Complete design document
- `docs/plans/vfs_uplift/2025-11-19-task-3-1-effects-dtos.md` - Implementation plan
- `docs/config-schemas/variables.md` - VFS variable definitions
- `docs/config-schemas/affordances.md` - Affordance configuration (uses effects)
- Expression language: See `docs/plans/vfs_uplift/2025-11-19-task-1-2-expression-parser.md`

---

**Location**: `<config_pack>/effects.yaml` (experiment-level)

**Status**: Phase 3 Complete + Phase 4 Command Extensions Implemented

**Pattern**: Effects is the foundational command language for ALL simulation behavior. All behavioral parameters must be explicitly specified (no-defaults principle) to ensure reproducibility.

---

## Overview

The Effects System is HAMLET's declarative command pipeline language that provides a unified way to express all simulation behavior: affordance interactions, item dynamics, temporal changes, meter cascades, and agent state mutations.

### What Are Effects?

Effects are **reusable, time-limited modifications** to entity state - similar to buffs and debuffs in games like World of Warcraft or status effects in tabletop RPGs. They:

- Attach to agents, items, affordances, or global world state
- Execute commands at lifecycle stages (spawn, tick, despawn)
- Have explicit duration (auto-despawn when timer expires)
- Support stacking policies (stack, renew, merge, replace)
- Are compiled once and reused many times

**Examples**:
- **Agent buffs**: "caffeinated" (energy regen), "inspired" (mood boost), "wet" (hygiene penalty)
- **Agent debuffs**: "poisoned" (health damage), "exhausted" (energy drain), "sick" (all stats reduced)
- **Item states**: "spoiled" (food decay), "rusty" (tool degradation), "enchanted" (bonus effects)
- **World state**: "nighttime" (global visibility modifier), "rush_hour" (affordance availability)

### Key Principles

1. **Reusable Effect Catalog**: Define effects once, reference by ID everywhere
2. **Command Pipeline Execution**: Ordered, explicit commands at lifecycle stages
3. **VFS Expression Language**: Pure functional expressions for all value computations
4. **Compile-Time Validation**: Type checking for paths, references, and expressions
5. **Scope-Aware Context**: Effects attach to global/agent/item/affordance with appropriate access
6. **No Hidden Defaults**: All parameters explicit (duration, intensity, policy)

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
    intensity: float               # Default intensity multiplier (default: 1.0)
    reapply_policy: stack|renew|merge|replace  # Reapply behavior (REQUIRED)
    observable: bool               # Whether agents can observe this effect (default: true)

    # Lifecycle command pipelines
    on_spawn: CommandConfig[]      # Execute when effect spawned
    on_tick: CommandConfig[]       # Execute each step while active
    on_despawn: CommandConfig[]    # Execute before removal
    on_interrupt: CommandConfig[]  # Execute on forced removal
```

**Required Fields**:
- `id`: Unique identifier for referencing this effect
- `scope`: Determines attachment point and available context
- `duration`: Lifecycle length (auto-despawn when reaches 0)
- `reapply_policy`: Behavior when same effect spawned on same target
- All command pipeline fields (`on_spawn`, `on_tick`, `on_despawn`, `on_interrupt`) must be present (can be empty lists)

**Optional Fields**:
- `description`: Documentation string
- `intensity`: Default 1.0 (can be overridden at spawn time)
- `observable`: Default true (visible in agent observations)

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
- Other effects spawn secondary effects
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

##### `stack` - Create Independent Instances

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
**Required**: No (default: `true`)
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

**Future Integration**: Observable effects will be added to observation spec by VFS observation builder.

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
- Trigger secondary effects (`spawn_effect: "visual_glow"`)
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
3. Entity destroyed (cleanup on death/removal)

**Typical Uses**:
- Cleanup flags (`target.vfs.is_buffed = false`)
- Reversal of on_spawn changes (if not handled by duration naturally)
- Final effects (penalty for buff expiring, reward for surviving duration)
- Logging/analytics (record effect completion)

**Performance**: Executes once per despawn (not every tick)

**Empty List**: Valid pattern for effects with no cleanup logic

**Important**: `on_despawn` executes even if effect interrupted (unlike some game engines that only execute on natural expiration)

---

#### `on_interrupt` (list[CommandConfig], REQUIRED)

**Type**: `list[CommandConfig]`
**Required**: Yes (can be empty list)
**Example**:
```yaml
on_interrupt:
  - modify: target.vfs.interrupted
    value: true
```

Command pipeline executed when effect **forcibly removed** before natural expiration.

**Execution Triggers**:
- Manual despawn via API (future feature)
- Entity death/removal while effect active
- Effect cancelled by game mechanic

**Difference from on_despawn**:
- `on_despawn`: Executes for ALL removals (natural + forced)
- `on_interrupt`: Executes ONLY for forced removals

**Typical Uses**:
- Different cleanup for interrupted vs completed effects
- Penalties for premature termination
- Analytics (track interruption rate)

**Performance**: Executes once per interruption (not every tick)

**Empty List**: Most effects have empty on_interrupt (use on_despawn for all cleanup)

---

## Command Pipeline Language

Effects execute commands at lifecycle stages (on_spawn, on_tick, on_despawn, on_interrupt). Commands are typed, validated at compile-time, and executed on GPU tensors.

### Supported Command Types

**Implemented Commands**:
- ✅ `modify` - Set variable/bar value using expression
- ✅ `spawn_effect` - Spawn another effect
- ✅ `spawn_item` - Create item instance
- ✅ `if` - Conditional execution
- ✅ `for_each` - Iterate over collections

All command types are fully implemented and production-ready.

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
- `self.*`: Effect instance state (for effect-local variables)
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

**Functions**:
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

**Performance**:
- Expressions compiled to AST at world load time (one-time cost)
- AST evaluated on GPU tensors each execution (vectorized)
- Pre-compilation eliminates runtime parsing overhead

---

### `spawn_effect` Command

**Purpose**: Spawn another effect (cascading effects, secondary triggers)

**Schema**:
```yaml
- spawn_effect: <effect_id>
  target: <expression>      # Optional, default: "self"
  intensity: <float>        # Optional, default: 1.0
```

**Fields**:
- `spawn_effect` (string, REQUIRED): Effect ID from catalog
- `target` (expression, OPTIONAL): Target entity for new effect (default: `"self"`)
- `intensity` (float, OPTIONAL): Intensity multiplier for spawned effect (default: 1.0)

**Target Resolution**:
- `"self"`: Apply to entity this effect is on (most common)
- `"target"`: Apply to interaction target (for affordance effects)
- Expression: Dynamic target selection (future: nearby agents, held items)

**Use Cases**:
- **Chained Effects**: Poisoned → spawn "nauseous" after 5 ticks
- **Secondary Effects**: Eating food → spawn "digesting" effect
- **Conditional Triggers**: If health < 0.2 → spawn "critical_condition"
- **Visual Effects**: Buff applied → spawn "visual_glow" effect

**Examples**:

```yaml
# Simple cascade - poison causes nausea
- id: "poison"
  on_spawn:
    - spawn_effect: "nauseous"
      target: "self"
      intensity: 1.0

# Conditional spawn - low energy triggers weakness
- id: "energy_monitor"
  on_tick:
    - if: "target.bar.energy < 0.2"
      then:
        - spawn_effect: "weakness"
          target: "self"
          intensity: 2.0
      else: []

# Intensity scaling - stronger poison spawns stronger nausea
- id: "poison_severe"
  on_spawn:
    - spawn_effect: "nauseous"
      target: "self"
      intensity: "intensity * 1.5"  # Scale by poison intensity
```

**Validation**:
- Effect ID must exist in catalog (compile-time check)
- Target expression must evaluate to valid entity
- Circular dependencies detected (effect A spawns B spawns A)

**Performance**:
- Spawning creates new effect instance (O(1) operation)
- Reapply policy of spawned effect determines behavior

---

### `spawn_item` Command

**Purpose**: Create item instance in world (loot drops, crafting, resource generation)

**Schema**:
```yaml
- spawn_item: <item_type_id>
  position: <expression>    # Optional, location to spawn
```

**Fields**:
- `spawn_item` (string, REQUIRED): Item type ID from item catalog
- `position` (expression, OPTIONAL): Where to spawn item

**Position Resolution**:
- `"target.position"`: At entity's current position
- `"random"`: Random valid position in world (future)
- Expression: Computed position (e.g., `"target.position + [1, 0]"`)

**Use Cases**:
- **Loot Drops**: Enemy death → spawn "gold_coin" at position
- **Resource Generation**: Tree effect → spawn "apple" periodically
- **Crafting Results**: Crafting effect completes → spawn finished item
- **Environmental Spawns**: Rain effect → spawn "puddle" items

**Examples**:

```yaml
# Drop loot on death
- id: "enemy_death"
  on_despawn:
    - spawn_item: "gold_coin"
      position: "target.position"

# Periodic resource generation
- id: "apple_tree"
  on_tick:
    - if: "temporal.tick % 100 == 0"
      then:
        - spawn_item: "apple"
          position: "target.position"
      else: []

# Multiple item spawn
- id: "treasure_chest"
  on_spawn:
    - spawn_item: "gold_coin"
      position: "target.position"
    - spawn_item: "health_potion"
      position: "target.position"
```

**Validation**:
- Item type must exist in item catalog (compile-time check)
- Position must be valid coordinate (runtime check)

**Performance**:
- Creates new item instance (O(1) operation)
- Items have their own lifecycle (duration, decay effects)

---

### `if` Command

**Purpose**: Conditional command execution based on runtime state

**Schema**:
```yaml
- if: <boolean_expression>
  then:
    - <command>
    - <command>
  else:
    - <command>
```

**Fields**:
- `if` (expression, REQUIRED): Boolean expression (condition)
- `then` (list[Command], REQUIRED): Commands to execute if true
- `else` (list[Command], OPTIONAL): Commands to execute if false (default: empty)

**Condition Expressions**:
Must evaluate to boolean type. Use comparison operators and logical combinators.

**Use Cases**:
- **Threshold Effects**: If health < 0.2, apply crisis penalties
- **State-Dependent Behavior**: If night, reduce visibility
- **Resource Checks**: If has currency, unlock premium effects
- **Conditional Spawning**: If poisoned, spawn nauseous effect

**Examples**:

```yaml
# Simple threshold check
- if: "target.bar.energy < 0.2"
  then:
    - modify: target.vfs.in_crisis
      value: true
    - spawn_effect: "energy_crash"
      target: "self"
  else:
    - modify: target.vfs.in_crisis
      value: false

# Multiple conditions
- if: "target.bar.energy < 0.2 and target.bar.health < 0.3"
  then:
    - spawn_effect: "critical_condition"
      target: "self"
      intensity: 3.0
  else: []

# Nested conditionals
- if: "target.bar.health < 0.5"
  then:
    - if: "target.bar.health < 0.2"
      then:
        - spawn_effect: "near_death"
          target: "self"
      else:
        - spawn_effect: "injured"
          target: "self"
  else: []

# Time-based logic
- if: "temporal.tick % 24 >= 18"
  then:
    - modify: global.vfs.is_night
      value: true
  else:
    - modify: global.vfs.is_night
      value: false
```

**Validation**:
- Condition must be boolean type (compile-time check)
- Both then and else branches type-checked
- Nested conditionals supported (arbitrary depth)

**Performance**:
- Condition evaluated once per execution
- Only executed branch runs (no wasted computation)
- Pre-compiled ASTs for condition and branches

---

### `for_each` Command

**Purpose**: Iterate over collections and execute commands for each element

**Schema**:
```yaml
- for_each: <collection_expression>
  as: <iterator_variable>
  do:
    - <command using iterator>
    - <command using iterator>
```

**Fields**:
- `for_each` (expression, REQUIRED): Collection to iterate (list, tensor)
- `as` (string, REQUIRED): Variable name for current element
- `do` (list[Command], REQUIRED): Commands to execute for each element

**Collection Sources**:
- `nearby_agents`: Agents within radius (future)
- `held_items`: Items in inventory (future)
- `active_effects`: Effects on entity (future)
- Static lists: `[1, 2, 3]` or VFS array variables

**Iterator Variable**:
Available inside `do` commands as scoped variable. Access via name specified in `as`.

**Use Cases**:
- **Area Effects**: Apply effect to all nearby agents
- **Inventory Processing**: Consume all food items
- **Batch Operations**: Modify multiple VFS variables
- **Relationship Systems**: Update all social connections

**Examples**:

```yaml
# Apply poison to nearby agents (future)
- for_each: "nearby_agents(radius=2)"
  as: "agent"
  do:
    - spawn_effect: "poison"
      target: "agent"
      intensity: 0.5

# Consume all food items (future)
- for_each: "target.inventory.items"
  as: "item"
  do:
    - if: "item.vfs.type == 'food'"
      then:
        - modify: "target.bar.energy"
          value: "target.bar.energy + item.vfs.nutrition"
        - spawn_effect: "item_consumed"
          target: "item"
      else: []

# Batch VFS updates
- for_each: "[1, 2, 3, 4, 5]"
  as: "index"
  do:
    - modify: "target.vfs.multiplier"
      value: "target.vfs.multiplier * index"
```

**Validation**:
- Collection expression must evaluate to iterable type
- Iterator variable scoped to `do` block only
- Commands type-checked with iterator variable in context

**Performance**:
- Loops execute sequentially (not vectorized)
- Keep collections small for performance
- Prefer batch operations over loops when possible

**Current Limitations**:
- Limited collection sources in Phase 3/4
- No nested for_each loops (future enhancement)
- No break/continue statements (execute all iterations)

---

## Effect Examples

Real examples demonstrating common patterns and use cases:

### Example 1: Energy Regeneration (RENEW Policy)

```yaml
- id: "energy_regen"
  description: "Regenerates energy over time, timer refreshes when reapplied"
  scope: agent
  duration: 20
  intensity: 1.0
  reapply_policy: renew
  observable: true

  on_spawn: []

  on_tick:
    - modify: target.bar.energy
      value: "clamp(target.bar.energy + (0.05 * intensity), 0.0, 1.0)"

  on_despawn: []
  on_interrupt: []
```

**Behavior**:
- Regenerates 5% energy per tick for 20 ticks
- If reapplied while active, resets duration to 20 (extends buff)
- Observable by agent (shows as "energy_regen" status)
- No spawn/despawn logic (all behavior in on_tick)

**Use Case**: Food consumption grants sustained energy recovery

**Key Pattern**: RENEW policy for single-instance buffs that extend on reapplication

---

### Example 2: Instant Health Boost (STACK Policy)

```yaml
- id: "health_boost"
  description: "Instant health restoration, multiple uses stack"
  scope: agent
  duration: 1
  intensity: 1.0
  reapply_policy: stack
  observable: true

  on_spawn:
    - modify: target.bar.health
      value: "clamp(target.bar.health + (0.2 * intensity), 0.0, 1.0)"

  on_tick: []
  on_despawn: []
  on_interrupt: []
```

**Behavior**:
- Instant +20% health when spawned
- Duration 1 means immediate despawn after spawn (no ticks)
- Each application stacks (multiple boosts possible)
- All logic in on_spawn (instant effect pattern)

**Use Case**: Consumable healing items (each use gives separate heal)

**Key Pattern**: Duration 1 + on_spawn logic for instant effects

---

### Example 3: Poison (MERGE Policy)

```yaml
- id: "poison"
  description: "Deals damage over time, intensity stacks when reapplied"
  scope: agent
  duration: 20
  intensity: 1.0
  reapply_policy: merge
  observable: true

  on_spawn: []

  on_tick:
    - modify: target.bar.health
      value: "clamp(target.bar.health - (0.02 * intensity), 0.0, 1.0)"

  on_despawn: []
  on_interrupt: []
```

**Behavior**:
- Deals 2% health damage per tick
- If reapplied, intensity accumulates (1.0 → 1.5 → 2.0)
- Single instance with escalating damage
- Duration not affected by reapplication (keeps counting down)

**Use Case**: Multiple poison sources stack severity (not duration)

**Key Pattern**: MERGE policy + intensity scaling for accumulating debuffs

**Important**: Note how `intensity` scales the damage - crucial for MERGE policy!

---

### Example 4: Caffeinated Buff (Complex State Management)

```yaml
- id: "caffeinated"
  description: "Energy boost with crash effect on expiration"
  scope: agent
  duration: 30
  intensity: 1.0
  reapply_policy: renew
  observable: true

  on_spawn:
    - modify: target.vfs.is_caffeinated
      value: true
    - modify: target.bar.energy
      value: "clamp(target.bar.energy + 0.3, 0.0, 1.0)"

  on_tick:
    - modify: target.bar.mood
      value: "clamp(target.bar.mood + (0.01 * intensity), 0.0, 1.0)"

  on_despawn:
    - modify: target.vfs.is_caffeinated
      value: false
    - spawn_effect: "caffeine_crash"
      target: "self"
      intensity: 1.0

  on_interrupt:
    - modify: target.vfs.is_caffeinated
      value: false
```

**Behavior**:
- Instant energy boost on application
- Gradual mood improvement while active
- Sets VFS flag for other systems to check
- Spawns crash effect on natural expiration
- Cleans up flag even if interrupted

**Use Case**: Coffee consumption with realistic crash mechanics

**Key Pattern**: on_spawn (instant), on_tick (sustained), on_despawn (consequence)

---

### Example 5: Wet Effect (State + Conditional Logic)

```yaml
- id: "wet"
  description: "Reduces hygiene when wet, spawns cold if too long"
  scope: agent
  duration: 50
  intensity: 1.0
  reapply_policy: renew
  observable: true

  on_spawn:
    - modify: target.vfs.is_wet
      value: true

  on_tick:
    - modify: target.bar.hygiene
      value: "clamp(target.bar.hygiene - (0.01 * intensity), 0.0, 1.0)"
    - if: "effect.elapsed_ticks > 30"
      then:
        - spawn_effect: "cold"
          target: "self"
          intensity: 1.0
      else: []

  on_despawn:
    - modify: target.vfs.is_wet
      value: false

  on_interrupt:
    - modify: target.vfs.is_wet
      value: false
```

**Behavior**:
- Sets wet flag, reduces hygiene over time
- If wet for >30 ticks, spawns cold effect
- Renew policy extends duration (stay wet longer if re-exposed)
- Cleanup handled in both on_despawn and on_interrupt

**Use Case**: Environmental effects with conditional escalation

**Key Pattern**: Conditional spawning based on effect lifetime

**Note**: Uses `effect.elapsed_ticks` to track how long effect has been active

---

### Example 6: Global Day/Night Cycle

```yaml
- id: "global_day_cycle"
  description: "Updates global day/night state based on time"
  scope: global
  duration: 10000
  intensity: 1.0
  reapply_policy: stack
  observable: false

  on_spawn: []

  on_tick:
    - modify: global.vfs.is_night
      value: "temporal.tick % 24 >= 18 and temporal.tick % 24 < 6"
    - modify: global.vfs.time_of_day
      value: "temporal.tick % 24"

  on_despawn: []
  on_interrupt: []
```

**Behavior**:
- Sets global `is_night` flag based on time-of-day
- Updates every tick using temporal context
- Duration 10000 for long-lived world state effect
- Not observable (global state, not agent-specific status)

**Use Case**: Environment spawns this on startup for day/night cycles

**Key Pattern**: Global scope + temporal expressions for world state

**Note**: Uses `temporal.tick` for time-based logic, `global.vfs.*` for world state

---

### Example 7: Item Decay (ITEM Scope)

```yaml
- id: "item_decay"
  description: "Food items spoil over time, become inedible"
  scope: item
  duration: 200
  intensity: 1.0
  reapply_policy: stack
  observable: false

  on_spawn: []

  on_tick:
    - modify: target.vfs.freshness
      value: "clamp(target.vfs.freshness - (0.005 * intensity), 0.0, 1.0)"
    - if: "target.vfs.freshness < 0.1"
      then:
        - modify: target.vfs.is_spoiled
          value: true
        - spawn_effect: "spoiled"
          target: "self"
          intensity: 1.0
      else: []

  on_despawn: []
  on_interrupt: []
```

**Behavior**:
- Reduces item freshness over time
- When freshness drops below 10%, marks as spoiled
- Spawns "spoiled" effect for additional consequences
- Stack policy allows multiple decay effects (compounding decay)

**Use Case**: Perishable food items in simulation

**Key Pattern**: Item scope + conditional state transitions

**Note**: Items have their own VFS variables (target.vfs.*)

---

### Example 8: Affordance Cooldown (AFFORDANCE Scope)

```yaml
- id: "on_cooldown"
  description: "Prevents affordance reuse for duration"
  scope: affordance
  duration: 10
  intensity: 1.0
  reapply_policy: renew
  observable: true

  on_spawn:
    - modify: target.vfs.available
      value: false

  on_tick: []

  on_despawn:
    - modify: target.vfs.available
      value: true

  on_interrupt:
    - modify: target.vfs.available
      value: true
```

**Behavior**:
- Marks affordance as unavailable on spawn
- Lasts 10 ticks (cooldown period)
- Renew policy extends cooldown if triggered again
- Restores availability on despawn/interrupt

**Use Case**: Prevent spam-clicking affordances, enforce cooldown periods

**Key Pattern**: Affordance scope + availability flag manipulation

**Note**: AffordanceEngine can check target.vfs.available before allowing interaction

---

### Example 9: Inspired Buff (Secondary Effect Spawn)

```yaml
- id: "inspired"
  description: "Boosts mood and spawns creativity effect"
  scope: agent
  duration: 40
  intensity: 1.0
  reapply_policy: replace
  observable: true

  on_spawn:
    - modify: target.bar.mood
      value: "clamp(target.bar.mood + 0.2, 0.0, 1.0)"
    - spawn_effect: "creative"
      target: "self"
      intensity: 1.5

  on_tick:
    - modify: target.bar.mood
      value: "clamp(target.bar.mood + (0.005 * intensity), 0.0, 1.0)"

  on_despawn:
    - modify: target.vfs.was_recently_inspired
      value: true

  on_interrupt: []
```

**Behavior**:
- Instant mood boost on spawn
- Spawns secondary "creative" effect with higher intensity
- Sustained mood gain while active
- Leaves flag when expires (for analytics or future effects)
- Replace policy: Only one inspiration at a time

**Use Case**: Art/music affordances grant inspiration with cascading benefits

**Key Pattern**: Effect spawning effects for complex behaviors

---

### Example 10: Area Effect (FOR_EACH Loop)

```yaml
# Future example - requires nearby_agents() implementation
- id: "healing_aura"
  description: "Heals nearby agents in radius"
  scope: agent
  duration: 20
  intensity: 1.0
  reapply_policy: stack
  observable: true

  on_spawn: []

  on_tick:
    - for_each: "nearby_agents(radius=2)"
      as: "nearby"
      do:
        - modify: "nearby.bar.health"
          value: "clamp(nearby.bar.health + (0.02 * intensity), 0.0, 1.0)"

  on_despawn: []
  on_interrupt: []
```

**Behavior**:
- Each tick, finds agents within radius 2
- Heals each nearby agent by 2% health
- Stack policy allows multiple auras (compounding heals)
- Works on others, not self

**Use Case**: Support abilities, area buffs, social effects

**Key Pattern**: for_each loop for multi-target effects

**Note**: Requires spatial query functions (future feature)

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
- List structures correct (on_spawn, on_tick, on_despawn, on_interrupt)

**Path Validation** (CommandCompiler):
- `modify` paths exist in VFS schema
- Paths accessible from effect scope
- Path types match expression return types

**Expression Validation** (ExpressionParser + TypeChecker):
- Expressions parse correctly (valid syntax)
- Types inferred correctly (type checker validates operations)
- Return type matches target path type
- Variables referenced exist in context (target, global, temporal, intensity)

**Reference Validation**:
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

**Missing Effect Reference**:
```
ReferenceError: Effect 'nonexistent_effect' not found in catalog
(referenced in spawn_effect command)
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
  - name: "BED"
    interactions:
      on_start:
        - spawn_effect: "energy_regen"
          target: "self"
          intensity: 1.5
```

**Integration**: AffordanceEngine validates `spawn_effect` references exist in EffectCatalog

### Items

Items apply effects when used/equipped/consumed:

```yaml
# items.yaml
items:
  item_types:
    - id: "healing_potion"
      interactions:
        on_use:
          - spawn_effect: "health_boost"
            target: "user"
            intensity: 2.0
```

**Integration**: Items use same command language as effects

### Cascades (Future)

Cascades can conditionally spawn effects:

```yaml
# cascades.yaml (future)
cascades:
  - source: energy
    targets:
      - target: health
        condition: "source < 0.2"
        on_trigger:
          - spawn_effect: "energy_crash"
```

### VFS Profiles

VFS profiles define variables that effects modify:

```yaml
# variables_reference.yaml
variables:
  - id: "is_caffeinated"
    scope: agent
    type: bool
    default: false
    readers: [agent, engine]
    writers: [engine]  # Effects can modify via CommandExecutor
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
- Don't spawn effects unnecessarily
- Use renew/merge policies to prevent duplicate instances

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
- Compare `stack` vs `renew` in curriculum
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
- Verify path accessible from effect scope
- Ensure expression return type matches path type (bool vs float)

**Q: Effect spawned but not ticking**
- Check scope matches target entity
- Verify `current_step` passed to `tick()`
- Ensure `env_state` passed for context building

**Q: Intensity not scaling properly**
- Verify expressions multiply by `intensity` variable
- Check merge policy used if expecting intensity stacking
- Ensure intensity passed at spawn time (defaults to 1.0)

**Q: Effects despawning too early/late**
- Check `duration` field matches intended tick count
- Verify `duration: 1` used for instant effects (common mistake: `duration: 0`)
- Remember tick occurs AFTER commands execute

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

## See Also

- **Design Document**: `docs/zzz. archive/plans/archive/vfs_uplift/2025-11-19-effects-system-design.md` - Complete architecture
- **Implementation Plan**: `docs/plans/vfs_uplift/2025-11-19-task-3-1-effects-dtos.md` - DTOs and catalog
- **VFS Variables**: `docs/config-schemas/variables.md` - Variable system that effects modify
- **Affordances**: `docs/config-schemas/affordances.md` - How affordances spawn effects
- **Expression Language**: `docs/plans/vfs_uplift/2025-11-19-task-1-2-expression-parser.md` - Expression syntax and semantics
- **Training Config**: `docs/config-schemas/training.md` - How to run experiments with effects

---

**Status**: Phase 3 Complete + Phase 4 Command Extensions Implemented
**Version**: 1.0
**Last Updated**: 2025-11-21
