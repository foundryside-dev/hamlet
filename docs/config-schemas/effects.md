# effects.yaml Configuration

> ⚠️ **Restored to the live tree 2026-08-26 — one required field is missing and one whole vocabulary is absent.**
>
> **⚠️ `max_active_effects` is conditionally REQUIRED whenever effects are declared, and this
> 1700-line document mentions it zero times.** Omit it and the pack is refused.
>
> **⚠️ The `for_each` collection vocabulary is missing, and described as "future" while it
> ships.** Measured occurrence counts in this file: `all_agents` **0**, `switch` **1** (the semantics section below),
> `delay` **0**, `sample` **0**. `for_each: all_agents` is the load-bearing surface for
> expressing a declarative step over simultaneous agent submissions, and it is not mentioned
> once — both PRD-0001 Trial O executors reached it only by reading
> `src/townlet/effects/collections.py`. Tracked as `hamlet-7eadeb214c`.
>
> **Time and position in effects** (2026-10-24, effects remediation WP3; `hamlet-a737e444c0`).
> One account for every command pipeline (effects, affordance interactions, item interactions):
> - **✅ Time: the bare `tick` variable**, the engine-written step counter. The effects
>   schema admits the engine's ambient names by bare name, exactly as VFS profile
>   expressions do. A declared clock (a global variable whose `expression` derives from
>   `tick`, e.g. `day_phase: "tick % 24"`) is read as `vfs.<id>` like any global.
> - **❌ `temporal.*`** has no schema entry in a command pipeline and refuses at compile.
> - **❌ Temporal-history functions** — `lag`, `delta`, `moving_average`, `ema`,
>   `rate_of_change`, `rising_edge`, `falling_edge`, and `elapsed_ticks()` — **refuse at
>   compile**: only the VFS profile evaluator keeps a history and a step. Declare a variable
>   with `expression: "lag(bar.energy, 1)"` in the pack-scope variables declaration and read
>   that variable from the command.
> - **✅ Position: `distance_to_affordance`, `in_range`, `direction_to_affordance`** evaluate
>   per agent. The environment hands every effect tick the agent positions, the deployed
>   affordance positions and the substrate. An undeployed affordance is at distance `inf`.
>   These functions take their own `"manhattan"`/`"euclidean"` argument (default manhattan);
>   they do not read the stratum's `distance_metric`. `nearby_agents` does (see `for_each`).
> - Inside an interaction pipeline (`affordances.yaml`, `items.yaml`) position reads still
>   raise at runtime: the affordance engine and item handler do not yet pass positions.

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

**Scope**: Optional pack-scope effects declaration, conventionally `<config_pack>/effects.yaml`.
The bare `effect_definitions` shape is recognized by content; fragments may live in nested
`.yaml`/`.yml` documents. Effect identifiers must be unique across the scope, with both origins
reported on collision. See [declaration discovery](declarations.md).

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

**Episode boundary**: effects are episode-scoped. `env.reset()` calls `EffectManager.reset()`
before anything in the new episode can spawn: every global, agent, item and affordance effect is
discarded, all delayed (`delay`) work is cancelled, the scheduler clock returns to tick 0 and
instance ids restart at 0. This is a hard clear: no `on_despawn` or `on_interrupt` runs, because
meters and episode-scoped VFS state have already been re-initialised and a hook would write into
the new episode. An instance never carries over. A legitimately re-spawned effect is one that a
spawn path re-creates after the reset (an interaction, a cascade, or a `delay` block scheduled in
the new episode); it starts fresh, with full `duration` and `elapsed_ticks = 0`. There is no
`on_reset` hook, so an effect cannot be declared live at tick 0.

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
- `vfs.*` (bare): a global variable is its one shared value. A bare `vfs.X` naming an
  **agent-scoped** variable is the interacting agent's row, never the batch: wherever the
  pipeline runs with an agent target (affordance and item interactions, agent-scoped effects,
  `for_each` bodies over agents) the compiler resolves it to `target.vfs.X`, for reads and
  writes alike; a write to it from a pipeline with no agent target (a global, item or
  affordance-scoped effect, a `for_each: inventory_items` body) is refused at compile.
- `tick` (bare): the engine step counter. `temporal.*` has no entry in a command pipeline and
  refuses at compile; a declared clock is a global variable read as `vfs.<id>`.

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

**Write semantics** (2026-10-24, review F1):
- A bare `bar.X` is the whole batch: one value per agent. A scalar `value` (`"0.3"`)
  broadcasts to every agent. `target.bar.X` / `self.bar.X` write one agent's row.
- Every write lands **in place** in the existing tensor. The bar is never rebound to a
  new tensor or a broadcast view, so a scalar `modify: bar.X` followed by a
  `target.bar.X` write to the same bar in the same tick changes only the target's row
  (`[0.3, 0.3, 0.3]` then `[0.3, 0.4, 0.3]`, never `[0.4, 0.4, 0.4]`). The executor
  checks after every command that no bar was rebound or left with a broadcast stride.
- Inside a masked `if`/`switch` branch (below) a batch write lands only on the agents
  the condition holds for, and a row write lands only if that agent's row is live.

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

# Temporal logic (bare `tick`; `temporal.*` refuses in an effect)
- modify: global.vfs.is_night
  value: "tick % 24 >= 18"

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

**Purpose**: Create item instances in the world (loot drops, crafting, resource generation)

**Schema** (every field required):
```yaml
- spawn_item: <item_type_id>
  position: self | target | random
  quantity: <int >= 1>
```

**Fields**:
- `spawn_item` (string, REQUIRED): Item type ID from the item catalog
- `position` (string, REQUIRED): `self` or `target` (the agent's cell), or `random` (a free
  cell found from the `self` agent's position)
- `quantity` (int ≥ 1, REQUIRED): number of items placed by one execution of the command;
  each finds its own spawn location. An item arena at capacity places fewer, silently.
- No `initial_state`: an authored override map is refused as an extra field, because
  compile-time write authorization cannot see one. A spawned item starts from its VFS
  profile's declared initial values; change them afterwards with `modify` on the item.

**Examples**:

```yaml
# Drop loot on death
- id: "enemy_death"
  on_despawn:
    - spawn_item: "gold_coin"
      position: target
      quantity: 3

# Periodic resource generation
- id: "apple_tree"
  on_tick:
    - if: "tick % 100 == 0"
      then:
        - spawn_item: "apple"
          position: random
          quantity: 1
      else: []
```

**Validation**:
- `quantity` is required; a missing or null one refuses at parse
- Item type must exist in the item catalog
- `spawn_item` has no per-agent row: inside an `if`/`switch` branch that holds for only
  some agents it is refused at runtime (see `if`)

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
- `else` (list[Command], REQUIRED): Commands to execute if false; write `else: []` for none

**Condition Expressions**:
Must evaluate to boolean type. Use comparison operators and logical combinators.

**Semantics — masked execution** (2026-10-24, review F2): the condition is evaluated
**per agent**, and each branch runs with its side of the condition as a **write mask**.
One keyword, one meaning: the command form of `if` agrees with the expression form
(`if c then a else b`, which is element-wise).

- A per-agent condition (`bar.health < 0.5`, one bool per agent) runs `then` for the
  agents it holds for and `else` for the agents it does not — both branches may run in
  the same tick, each on its own agents. Nothing is reduced with `any()`/`all()`.
- Inside a masked branch, a batch write (`modify: bar.energy`) lands only on the live
  agents; a row write (`target.bar.energy`, `target.vfs.X`, bare agent-scoped `vfs.X`)
  lands only if that agent's row is live; an agent-scoped `spawn_effect` spawns only if
  its target agent's row is live. A nested `if` intersects its mask with the enclosing one.
- A scalar condition (`target.bar.health < 0.5`, `intensity > 1.0`) is the degenerate
  mask: it holds for every agent or for none, so exactly one branch runs, unmasked.
- `then` runs to completion before `else`. Each agent's row is written by exactly one
  branch, so row-local expressions are unaffected, but an aggregate read in `else`
  (`mean(bar.energy)`, a `for_each` over `all_agents`) sees `then`'s writes.
- A target with **no per-agent row** — a global variable, a scalar bar, an item variable,
  `affordance.X.available`, `spawn_item`, a non-agent `spawn_effect`, a `delay` block —
  can only be written when the mask is whole (every agent live). Writing it from a
  branch that holds for only some agents is refused at runtime with a message naming
  the target: condition on a scalar value instead, or write a per-agent target.

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
- if: "tick % 24 >= 18"
  then:
    - modify: global.vfs.is_night
      value: true
  else:
    - modify: global.vfs.is_night
      value: false
```

**Validation**:
- Condition must be boolean type (compile-time check); at runtime it must be a scalar
  or one value per agent
- Both then and else branches type-checked and write-authorized, whichever runs
- Nested conditionals supported (arbitrary depth); masks intersect

**Performance**:
- Condition evaluated once per execution, over the whole batch
- A branch no agent is live for is skipped (every write under an empty mask is a no-op)
- Pre-compiled ASTs for condition and branches

---

### `switch` Command

**Purpose**: Select one of several command lists by equality against a selector

**Schema**:
```yaml
- switch: <expression>
  cases:
    - when: <expression>
      do:
        - <command>
    - when: <expression>
      do:
        - <command>
  default:
    - <command>
```

**Fields**:
- `switch` (expression, REQUIRED): Selector value
- `cases` (list, REQUIRED): Ordered `when`/`do` pairs; `when` is compared to the selector
  with `==`
- `default` (list[Command], REQUIRED): Commands for a selector no case matched; `default: []`
  for none (at least one of `cases` and `default` must be non-empty)

**Semantics — masked first-match, per agent**: the same rule as `if`. The selector and
every `when` are evaluated over the batch; a case runs for the agents it matches that no
earlier case took, with that set as its write mask; `default` runs for the agents no case
took. A scalar selector is the degenerate mask (one case or the default runs, unmasked).
A string selector compares as a scalar. Cases run in authored order, then `default`; a
later case's aggregate reads see earlier cases' writes.

```yaml
# bar.level per agent [1, 2, 3] → energy per agent [0.1, 0.2, 0.9]
- switch: "bar.level"
  cases:
    - when: "1"
      do: [{modify: bar.energy, value: "0.1"}]
    - when: "2"
      do: [{modify: bar.energy, value: "0.2"}]
  default:
    - modify: bar.energy
      value: "0.9"
```

The no-per-agent-row rule from `if` applies: a global, item, affordance, `spawn_item` or
`delay` target inside a case that holds for only some agents is refused at runtime.

---

### `for_each` Command

**Purpose**: Run a command list once per element of a collection, with `target` bound to it

**Schema**:
```yaml
- for_each: all_agents | nearby_agents | inventory_items | active_effects | <expression>
  radius: <number >= 0>   # REQUIRED for nearby_agents, refused for every other collection
  as: <name>              # accepted, not yet bound to anything (see below)
  do:
    - <command>           # `target.*` is the current element
```

**Fields**:
- `for_each` (string, REQUIRED): a collection name, or an expression evaluating to indices
- `do` (list[Command], REQUIRED): commands run once per element; inside them `target.*`
  addresses the element (an agent row, or an item row for `inventory_items`)
- `radius` (number ≥ 0, REQUIRED for `nearby_agents` only): distance in world units (grid
  cells on a grid)
- `as` (string, OPTIONAL): accepted but **not bound** — the body cannot read it yet
  (review-2026-10-24 effects F4; remediation WP7 decides bind or delete). Address the
  element as `target.*`.

**Collections**:
- `all_agents`: every agent row.
- `nearby_agents`: every other agent whose distance from the attached agent (`self`) is at
  most `radius`, measured by the substrate under the stratum's declared `distance_metric`
  (`manhattan`, `euclidean` or `chebyshev`). On an aspatial substrate every distance is 0,
  so every other agent is nearby. Needs an agent-scoped effect (it measures from `self`).
- `inventory_items`: the attached agent's held items (item rows).
- `active_effects`: see review-2026-10-24 effects F6 before relying on it.

**Examples**:

```yaml
# Heal every agent within 2 cells of the attached agent (stratum: distance_metric manhattan)
- for_each: nearby_agents
  radius: 2
  do:
    - modify: target.bar.health
      value: "clamp(target.bar.health + 0.02 * intensity, 0.0, 1.0)"

# Penalise every agent
- for_each: all_agents
  do:
    - modify: target.bar.comfort
      value: "target.bar.comfort - 0.1"
```

**Validation**:
- `radius` present exactly when the collection selects by distance (parse-time refusal)
- Body commands type-checked with `target` bound to the element's row kind
- No nested `for_each`; collections over 256 elements raise

**Performance**:
- Loops execute sequentially (not vectorized); keep collections small

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
      value: "tick % 24 >= 18 or tick % 24 < 6"
    - modify: global.vfs.time_of_day
      value: "tick % 24"

  on_despawn: []
  on_interrupt: []
```

**Behavior**:
- Sets global `is_night` flag based on time-of-day
- Updates every tick from the engine `tick`
- Duration 10000 for long-lived world state effect
- Not observable (global state, not agent-specific status)

**Use Case**: Environment spawns this on startup for day/night cycles

**Key Pattern**: Global scope + temporal expressions for world state

**Note**: Uses the bare `tick` for time-based logic, `global.vfs.*` for world state. A pack
with a declared clock variable (`expression: "tick % 24"`) can read that instead.

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
- id: "healing_aura"
  description: "Heals nearby agents in radius"
  scope: agent
  duration: 20
  reapply_policy: stack
  observable: true

  on_spawn: []

  on_tick:
    - for_each: nearby_agents
      radius: 2
      do:
        - modify: target.bar.health
          value: "clamp(target.bar.health + (0.02 * intensity), 0.0, 1.0)"

  on_despawn: []
  on_interrupt: []
```

**Behavior**:
- Each tick, finds the other agents within 2 cells of the attached agent under the
  stratum's declared `distance_metric`
- Heals each by 2% health; the attached agent itself is not in `nearby_agents`
- Stack policy allows multiple auras (compounding heals)

**Use Case**: Support abilities, area buffs, social effects

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

### Declared variables

Effects read/write supported variables from the canonical pack-scope roster.
The compiler supplies engine roles; authors do not declare readers or writers.

```yaml
variables:
  version: '1.0'
  item_profiles: []
  declarations:
  - id: is_caffeinated
    scope: agent
    type: bool
    lifetime: episode
    semantic_type: custom
    initial_value: false
    exposed_to: []
```

See [variables](variables.md) for scope and consumer restrictions. A registered symbol
is not a promise that every effect execution context supports every scope.

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
- Check VFS schema includes the path (the canonical variables declaration)
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
