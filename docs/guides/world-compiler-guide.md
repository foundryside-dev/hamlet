# World Compiler User Guide

**Status**: Phase 6 Complete (World Compiler T0 Pillar 3)
**Version**: 1.0
**Last Updated**: 2025-11-21

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Directory Structure](#directory-structure)
4. [Common Patterns](#common-patterns)
5. [Compilation](#compilation)
6. [Integration](#integration)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Introduction

The **World Compiler** is HAMLET's unified system for defining and compiling simulation behavior. It integrates four powerful layers into a single coherent pipeline:

### The Four Integrated Layers

```
┌─────────────────────────────────────┐
│ 1. Expression Language              │  ← Foundation: Pure functional expressions
│    - Parse expressions to AST       │
│    - Type checking & validation     │
│    - Runtime evaluation on GPU      │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ 2. VFS       │  │ 3. Effects   │      ← State & Behavior: Variables and commands
│    Profiles  │  │    System    │
│ - Dynamic    │  │ - Catalogs   │
│ - Static     │  │ - Commands   │
│ - Computed   │  │ - Lifecycle  │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ▼
        ┌──────────────┐
        │ 4. Items     │               ← World Objects: Inventory and interactions
        │    System    │
        │ - Catalog    │
        │ - Inventory  │
        │ - Lifecycle  │
        └──────────────┘
```

### What Each Layer Does

**Expression Language** - Pure functional expressions for all value computations:
- Arithmetic: `bar.energy + 0.05 * intensity`
- Logic: `bar.energy < 0.3 if is_night else bar.energy < 0.5`
- Built-in functions: `clamp(value, 0.0, 1.0)`, `min()`, `max()`, `sqrt()`

**VFS (Variable & Feature System)** - Declarative state space configuration:
- Agent variables: `energy`, `is_wet`, `distance_to_food`
- Global variables: `is_night`, `day_count`, `rush_hour`
- Item variables: `durability`, `quality`, `owner_id`
- Computed variables: Expressions evaluated on-demand

**Effects System** - Command pipeline language for behavior:
- Lifecycle hooks: `on_spawn`, `on_tick`, `on_despawn`
- Command types: `modify` (set values), `spawn_effect`, `spawn_item`, `if`, `for_each`
- Reapply policies: `stack`, `renew`, `merge`, `replace`
- Scoped execution: Effects attach to agents, items, affordances, or global state

**Items System** - World objects with inventory and interactions:
- Item catalog (experiment-level): Types, properties, interactions
- Item appearance (level-level): Spawn rules, distributions, respawning
- Inventory management: Pickup, use, drop actions
- VFS integration: Item state visible in observations

### Why Use World Compiler?

1. **Declarative Configuration**: Change simulation behavior without code changes
2. **Type Safety**: Compile-time validation catches errors before runtime
3. **GPU-Native**: Pre-compiled expressions execute on GPU tensors (vectorized)
4. **Reproducibility**: All configs compiled with provenance tracking (hashes)
5. **Composability**: Mix and match effects, items, and expressions freely
6. **Pedagogical**: Expose complex behaviors as teaching moments for students

---

## Getting Started

### Minimal Example Config Pack

This is the smallest valid config pack that demonstrates all four layers:

```
my_experiment/
├── experiment.yaml           # Experiment metadata
├── stratum.yaml             # Spatial substrate (grid size, topology)
├── environment.yaml         # Vocabulary (meters, affordances)
├── actions.yaml             # Available actions
├── agent.yaml               # Network architecture
└── levels/
    └── L0_test/
        ├── curriculum.yaml   # Level metadata
        ├── bars.yaml         # Meter behaviors
        ├── affordances.yaml  # Interactions (uses Effects)
        └── training.yaml     # Training hyperparameters
```

**Step 1: Create experiment-level configs**

`experiment.yaml`:
```yaml
experiment:
  version: "1.0"
  experiment_name: "My First Experiment"
  metadata:
    name: "Getting Started Example"
    description: "Minimal config demonstrating World Compiler"
    author: "Your Name"
    created: "2025-11-21"
  curriculum_levels:
    - L0_test
```

`stratum.yaml`:
```yaml
stratum:
  version: "1.0"
  substrate:
    type: grid
    grid_size: [5, 5]
    boundary_mode: clamp
    distance_metric: manhattan
```

`environment.yaml`:
```yaml
environment:
  version: "2.1"
  environment:
    affordances:
      - id: EAT
        name: EAT
        category: consumption
    meters:
      - name: energy
        initial: 1.0
    cascades: []
```

`actions.yaml`:
```yaml
actions:
  version: "1.0"
  vocabulary: global
  enabled_actions:
    - MOVE_N
    - MOVE_S
    - MOVE_E
    - MOVE_W
    - INTERACT
    - WAIT
```

`agent.yaml`:
```yaml
agent:
  version: "1.0"
  network_type: simple_q
  hidden_layers: [128, 64]
```

**Step 2: Create level configs**

`levels/L0_test/curriculum.yaml`:
```yaml
curriculum:
  version: "1.0"
  level_name: L0_test
  unlocks_at_episode: 0
  difficulty: 1
```

`levels/L0_test/bars.yaml`:
```yaml
bars:
  version: "1.0"
  meters:
    - name: energy
      initial: 1.0
      depletion:
        passive: 0.01
        move: 0.02
        interact: 0.05
      recovery:
        natural: 0.0
      bounds:
        min: 0.0
        max: 1.0
        lethal_min: true
        lethal_max: false
  cascades: []
```

`levels/L0_test/affordances.yaml`:
```yaml
affordances:
  version: "1.0"
  affordances:
    - name: EAT
      interaction_type: instant
      costs:
        energy: 0.05
      opening_hours:
        enabled: false
      deployment:
        type: fixed
        positions:
          - [2, 2]
      interactions:
        on_start:
          - modify: target.bar.energy
            value: "clamp(target.bar.energy + 0.3, 0.0, 1.0)"
        per_tick: []
        on_completion: []
        on_early_exit: []
        on_failure: []
  modulations: []
```

`levels/L0_test/training.yaml`:
```yaml
training:
  version: "1.0"
  num_agents: 2
  num_episodes: 100
  max_steps_per_episode: 100
  learning_rate: 0.001
  gamma: 0.99
  epsilon_start: 1.0
  epsilon_end: 0.1
  epsilon_decay_episodes: 50
  target_update_freq: 10
  use_double_dqn: true
```

**Step 3: Compile and validate**

```bash
# Validate configs (no cache)
python -m townlet.compiler validate my_experiment/

# Compile configs (generates cache)
python -m townlet.compiler compile my_experiment/

# Inspect compiled artifact
python -m townlet.compiler inspect my_experiment/.compiled/universe.msgpack
```

---

## Directory Structure

### Experiment-Level vs Level-Level

The World Compiler uses a **two-tier structure** to separate vocabulary (breaks checkpoints) from parameters (doesn't break checkpoints):

```
<experiment_dir>/
├── experiment.yaml          # EXPERIMENT-LEVEL: What levels exist
├── stratum.yaml             # EXPERIMENT-LEVEL: Spatial substrate type/size
├── environment.yaml         # EXPERIMENT-LEVEL: VOCABULARY (meters, affordances)
├── actions.yaml             # EXPERIMENT-LEVEL: Action vocabulary
├── agent.yaml               # EXPERIMENT-LEVEL: Network architecture
│
└── levels/                  # LEVEL-LEVEL: HOW behaviors work (parameters)
    ├── L0_minimal/
    │   ├── curriculum.yaml   # Level metadata
    │   ├── bars.yaml         # HOW meters behave (decay rates, bounds)
    │   ├── affordances.yaml  # HOW affordances work (interactions, costs)
    │   └── training.yaml     # Training hyperparameters
    │
    └── L1_full/
        ├── curriculum.yaml
        ├── bars.yaml         # Different parameters, same vocabulary
        ├── affordances.yaml  # Different parameters, same vocabulary
        └── training.yaml
```

### Why This Split?

**Experiment-Level (WHAT exists)**:
- Defines vocabulary that affects observation shape
- Changes break checkpoint compatibility
- Shared across all curriculum levels
- Examples: Number of meters, affordance IDs, action count

**Level-Level (HOW things behave)**:
- Defines parameters that don't affect observation shape
- Changes DON'T break checkpoint compatibility
- Differs across curriculum levels
- Examples: Decay rates, interaction effects, learning rate

**Key Insight**: Checkpoints can transfer across levels (L0 → L1) because they share vocabulary but differ only in parameters.

### Required Files Per Directory

**Experiment-Level (6 files)**:
1. `experiment.yaml` - Experiment metadata and level list
2. `stratum.yaml` - Substrate configuration
3. `environment.yaml` - Vocabulary (meters, affordances, cascades)
4. `actions.yaml` - Action vocabulary
5. `agent.yaml` - Network architecture

**Level-Level (4 files per level)**:
1. `curriculum.yaml` - Level metadata (unlock conditions)
2. `bars.yaml` - Meter behaviors (decay, recovery, bounds)
3. `affordances.yaml` - Affordance interactions (effects, costs)
4. `training.yaml` - Training hyperparameters

---

## Common Patterns

### Pattern 1: Computed VFS Variable

**Problem**: Want to expose a derived feature (e.g., energy urgency) to the agent without hardcoding it in Python.

**Solution**: Use VFS computed variables with expression language.

**Not Yet Implemented** - VFS computed variables are planned for Phase 2+. Current implementation supports static variables only.

**Future Pattern**:
```yaml
# vfs_profiles.yaml (FUTURE - Phase 2+)
agent_profile:
  energy_urgency:
    type: scalar
    scope: agent
    expression: "1.0 - bar.energy"  # Computed each step
    description: "How urgently agent needs energy [0-1]"
```

**Current Workaround**:
Use effects to compute and store values:
```yaml
# affordances.yaml (CURRENT - Phase 1)
affordances:
  - name: COMPUTE_URGENCY
    interaction_type: instant
    interactions:
      on_start:
        - modify: vfs.energy_urgency
          value: "1.0 - target.bar.energy"
```

---

### Pattern 2: Stacking Effect

**Problem**: Want multiple poison sources to stack (each adds damage independently).

**Solution**: Use `reapply_policy: stack` with intensity scaling.

`effects.yaml`:
```yaml
effect_definitions:
  - id: poison
    scope: agent
    duration: 20
    intensity: 1.0
    reapply_policy: stack  # Each application creates new instance
    observable: true

    on_spawn: []

    on_tick:
      - modify: target.bar.health
        value: "clamp(target.bar.health - (0.02 * intensity), 0.0, 1.0)"

    on_despawn: []
```

**Result**: If agent is poisoned 3 times, they have 3 independent poison effects ticking simultaneously (3× damage rate).

**Use Cases**:
- Multiple damage sources (poison, fire, bleeding)
- Food digestion (each meal digests independently)
- Buff stacking (multiple temporary stat boosts)

---

### Pattern 3: Item with Durability

**Problem**: Want items to degrade over time and break when durability reaches zero.

**Solution**: Use item VFS variable + effect that decreases durability each tick.

**Not Yet Fully Integrated** - Items system is complete but VFS-Items integration is partial.

**Planned Pattern** (Phase 4.5 complete):
```yaml
# items.yaml
items:
  - id: sword
    vfs_profile:
      durability:
        type: scalar
        initial: 100.0
        description: "Durability [0-100], breaks at 0"

    on_use:
      - modify: target.vfs.durability
        value: "target.vfs.durability - 1.0"
      - spawn_effect: weapon_attack
        target: nearby_enemy
```

**Current Workaround**:
Use hardcoded item properties until VFS-Items integration complete.

---

### Pattern 4: Expression-Based Affordance

**Problem**: Want affordance effects to depend on time of day (e.g., WORK gives more money during rush hour).

**Solution**: Use temporal context in effect expressions.

`affordances.yaml`:
```yaml
affordances:
  - name: WORK
    interaction_type: instant
    costs:
      energy: 0.3
    interactions:
      on_start:
        # Base pay: $20, bonus: $10 during rush hour (7-9am, 5-7pm)
        - modify: target.bar.money
          value: "target.bar.money + (20.0 + (10.0 if (temporal.hour >= 7 and temporal.hour < 9) or (temporal.hour >= 17 and temporal.hour < 19) else 0.0))"
```

**Temporal Variables Available**:
- `temporal.tick` - Current environment step count
- `temporal.hour` - Hour in 24-hour cycle (requires temporal mechanics enabled)
- `temporal.time_of_day` - Continuous time [0-24]

---

### Pattern 5: Cascade Triggered by Effect

**Problem**: Want low energy to trigger health damage (cascade), but only if agent is also wet (from effect).

**Solution**: Use conditional expression in cascade with VFS flag set by effect.

**Step 1: Effect sets VFS flag**

`effects.yaml`:
```yaml
effect_definitions:
  - id: wet
    scope: agent
    duration: 30
    reapply_policy: renew
    observable: true

    on_spawn:
      - modify: vfs.is_wet
        value: "true"

    on_tick: []

    on_despawn:
      - modify: vfs.is_wet
        value: "false"
```

**Step 2: Cascade checks flag** (Future - Phase 4+)

```yaml
# cascades.yaml (FUTURE)
cascades:
  - source: energy
    target: health
    condition: "source < 0.3 and vfs.is_wet"  # Only cascade if wet
    strength: 0.01
```

**Current Workaround**:
Use effect `on_tick` to manually check condition and modify target:
```yaml
# effects.yaml (CURRENT)
effect_definitions:
  - id: hypothermia
    scope: agent
    duration: 1000  # Long-lived check effect
    reapply_policy: renew

    on_tick:
      # If energy low AND wet, damage health
      - modify: target.bar.health
        value: "clamp(target.bar.health - 0.01, 0.0, 1.0) if (target.bar.energy < 0.3 and vfs.is_wet) else target.bar.health"
```

---

## Compilation

### CLI Commands

The World Compiler provides three CLI commands:

#### 1. Validate (Lint-Style Check)

**Purpose**: Check configs for errors without touching cache.

```bash
python -m townlet.compiler validate <config_dir>
```

**What it checks**:
- YAML syntax errors
- Schema validation (required fields, types)
- Path validation (bars, affordances, VFS variables exist)
- Expression syntax (parseable, type-safe)
- Cross-level vocabulary consistency

**Exit codes**:
- `0` - Validation passed
- `1` - Validation failed (prints error messages)

**Example**:
```bash
# Validate default curriculum
python -m townlet.compiler validate configs/default_curriculum/

# Expected output:
# ✓ Loaded experiment config
# ✓ Loaded 5 curriculum levels
# ✓ Vocabulary consistent across levels
# ✓ All expressions valid
# Validation passed.
```

#### 2. Compile (Build + Cache)

**Purpose**: Compile configs and generate cached artifact.

```bash
python -m townlet.compiler compile <config_dir> [--no-cache]
```

**What it does**:
1. Parse YAML configs to DTOs
2. Build symbol table (resolve references)
3. Validate paths and types
4. Cross-validate vocabulary consistency
5. Generate metadata and optimization data
6. Compile expressions to ASTs
7. Cache artifact to `<config_dir>/.compiled/universe.msgpack`

**Options**:
- `--no-cache` - Skip cache reads/writes (always rebuild)

**Cache invalidation**:
- Cache automatically invalidated if any config file changes
- Uses SHA256 hash of config contents for cache key
- Cache format: MessagePack (compact binary)

**Example**:
```bash
# Compile and cache
python -m townlet.compiler compile configs/default_curriculum/

# Expected output:
# Compiling experiment: default_curriculum
# ✓ Parsed 5 levels
# ✓ Vocabulary validation passed
# ✓ Expression compilation complete
# ✓ Cache written to configs/default_curriculum/.compiled/universe.msgpack
# Compilation complete in 1.23s
```

#### 3. Inspect (View Artifact)

**Purpose**: Inspect compiled universe artifact contents.

```bash
python -m townlet.compiler inspect <config_dir_or_artifact> [--format table|json]
```

**What it shows**:
- Metadata: Meter names, affordance IDs, action count
- Observation spec: Dimensions, fields, shapes
- Action space: Available actions, vocabulary
- Optimization data: Modulation tables, mask tables
- Level info: Training hyperparams, affordances per level

**Formats**:
- `table` (default) - Human-readable ASCII tables
- `json` - Machine-readable JSON output

**Example**:
```bash
# Inspect compiled artifact (table format)
python -m townlet.compiler inspect configs/default_curriculum/

# Expected output:
# ======= UNIVERSE METADATA =======
# Schema Version: 1.0
# Compiler Version: 0.1.0
# Compiled: 2025-11-21T10:30:00Z
#
# Meters: energy, health, satiation, hygiene, money, fitness, mood, social
# Affordances: EAT, SLEEP, WORK, SHOWER, EXERCISE, SOCIALIZE, ...
# Actions: 8 (MOVE_N, MOVE_S, MOVE_E, MOVE_W, INTERACT, WAIT)
#
# ======= OBSERVATION SPEC =======
# Dimensions: 29
# Fields:
#   - position: [2] (spatial)
#   - meters: [8] (bars)
#   - affordances: [14] (affordances)
#   - temporal: [4] (temporal)
# ...
```

---

### Compilation Errors

#### Schema Validation Errors

**Missing required field**:
```
ValidationError: bars.yaml
  Field 'bounds' is required for meter 'energy'
  Line 10: - name: energy
```

**Fix**: Add missing field to config.

**Invalid type**:
```
ValidationError: affordances.yaml
  Field 'duration' must be int, got str
  Line 25: duration: "20"  # Should be: duration: 20
```

**Fix**: Correct type in config (remove quotes for numbers).

**Invalid enum value**:
```
ValidationError: effects.yaml
  Field 'reapply_policy' must be one of: stack, renew, merge, replace
  Got: 'accumulate'
  Line 15: reapply_policy: accumulate
```

**Fix**: Use valid enum value.

#### Path Validation Errors

**Path not found**:
```
PathError: affordances.yaml
  Path 'target.bar.mana' not found in schema
  Available bars: energy, health, satiation, hygiene, money, fitness, mood, social
  Line 30: modify: target.bar.mana
```

**Fix**: Use existing meter name or add meter to `bars.yaml`.

**Scope violation**:
```
ScopeError: effects.yaml (FUTURE - not yet enforced)
  agent-scoped effect cannot modify global.bar.economy
  Cross-scope mutation not allowed
  Line 40: modify: global.bar.economy
```

**Fix**: Change target path to match effect scope.

#### Expression Errors

**Syntax error**:
```
ParseError: affordances.yaml
  Invalid expression syntax at position 20
  'target.bar.energy +' (expected operand)
  Line 35: value: "target.bar.energy +"
```

**Fix**: Complete expression with operand.

**Type mismatch**:
```
TypeCheckError: affordances.yaml
  Type mismatch for path 'target.bar.energy'
  Expected: float
  Got: bool
  Expression: 'target.bar.energy > 0.5'
  Line 40: value: "target.bar.energy > 0.5"
```

**Fix**: Use ternary operator for conditional assignment:
```yaml
value: "target.bar.energy + 0.1 if target.bar.energy > 0.5 else target.bar.energy"
```

#### Vocabulary Consistency Errors

**Meter vocabulary mismatch**:
```
VocabularyError: levels/L1_full/bars.yaml
  Meter vocabulary mismatch:
  Missing meters: ['fitness']
  Extra meters: []

  All curriculum levels must have same meter vocabulary as environment.yaml
  This ensures checkpoint portability across curriculum.
```

**Fix**: Add missing meter to level's `bars.yaml` (copy from environment.yaml, adjust parameters only).

---

## Integration

### How Expression → VFS → Effects → Items Flow Together

The four layers work together in a specific execution order:

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 0: COMPILE TIME                                        │
│                                                              │
│ 1. Parse YAML configs                                       │
│ 2. Build symbol table (resolve references)                  │
│ 3. Validate paths (bars, vfs, affordances exist)            │
│ 4. Compile expressions to ASTs                              │
│ 5. Cache compiled universe                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STEP 1: ENVIRONMENT INITIALIZATION                          │
│                                                              │
│ 1. Load compiled universe from cache                        │
│ 2. Initialize VFS registry (allocate tensors)               │
│ 3. Initialize bars (set initial values)                     │
│ 4. Initialize affordances (place on grid)                   │
│ 5. Initialize items (spawn initial items)                   │
│ 6. Initialize effects (spawn global effects)                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STEP 2: ENVIRONMENT STEP (each tick)                        │
│                                                              │
│ 1. Execute actions                                          │
│    → Action costs applied to bars                           │
│    → Affordance interactions execute (spawn effects)        │
│    → Item interactions execute (spawn effects)              │
│                                                              │
│ 2. Update bars                                              │
│    → Passive decay applied                                  │
│    → Natural recovery applied                               │
│                                                              │
│ 3. Execute cascades                                         │
│    → Cross-bar effects (low energy → health damage)         │
│                                                              │
│ 4. Tick effects                                             │
│    → All active effects execute on_tick commands            │
│    → Commands modify bars, VFS, spawn new effects           │
│    → Effects with duration=0 despawn (execute on_despawn)   │
│                                                              │
│ 5. Update items                                             │
│    → Item lifecycle (spawn/despawn)                         │
│    → Item VFS updated                                       │
│                                                              │
│ 6. Build observations                                       │
│    → Evaluate VFS expressions (if dynamic)                  │
│    → Collect bars, VFS, affordances, items                  │
│    → Assemble into observation tensor                       │
│                                                              │
│ 7. Compute rewards                                          │
│    → Drive As Code evaluation                               │
│    → Intrinsic rewards (RND, ICM)                           │
└─────────────────────────────────────────────────────────────┘
```

### Example: Food Poisoning Chain

This example shows all four layers working together:

**Scenario**: Agent eats bad food → gets food poisoning effect → health decreases → cascade triggers low health effect → VFS urgency variable computed → agent observes urgency.

**Step 1: Expression Language** - Define computations

```yaml
# No config yet - expressions appear in other configs
```

**Step 2: VFS** - Define urgency variable

```yaml
# vfs_profiles.yaml (FUTURE - Phase 2+)
agent_profile:
  health_urgency:
    type: scalar
    scope: agent
    expression: "1.0 - bar.health"  # Computed from health
    description: "How urgently agent needs medical attention"
```

**Step 3: Effects** - Define food poisoning effect

```yaml
# effects.yaml
effect_definitions:
  - id: food_poisoning
    scope: agent
    duration: 50
    intensity: 1.0
    reapply_policy: merge  # Multiple bad foods stack severity
    observable: true

    on_spawn:
      - modify: vfs.is_sick
        value: "true"

    on_tick:
      - modify: target.bar.health
        value: "clamp(target.bar.health - (0.02 * intensity), 0.0, 1.0)"

    on_despawn:
      - modify: vfs.is_sick
        value: "false"
```

**Step 4: Items** - Define bad food item

```yaml
# items.yaml (FUTURE - Phase 4)
items:
  - id: spoiled_food
    name: "Spoiled Food"
    on_use:
      - spawn_effect: food_poisoning
        target: user
        intensity: 1.5  # Worse than normal poison
```

**Step 5: Affordance** - Allow eating item

```yaml
# affordances.yaml
affordances:
  - name: EAT
    interaction_type: instant
    costs:
      energy: 0.05
    interactions:
      on_start:
        # If eating spoiled food, spawn poison effect
        # (This logic would be in item on_use in Phase 4)
        - spawn_effect: food_poisoning
          intensity: 1.5
```

**Step 6: Cascade** - Low health triggers emergency

```yaml
# bars.yaml
cascades:
  - source: health
    target: energy
    threshold: 0.3
    strength: 0.01  # Being sick drains energy
```

**Execution Flow**:
1. Agent executes INTERACT at EAT affordance
2. Affordance `on_start` spawns `food_poisoning` effect
3. Effect `on_spawn` sets `vfs.is_sick = true`
4. Each tick:
   - Effect `on_tick` decreases health by 2% (scaled by intensity)
   - Cascade checks: if `health < 0.3`, drain energy by 1%
   - VFS evaluates: `health_urgency = 1.0 - bar.health`
5. Observation builder includes:
   - `bar.health` (current health value)
   - `vfs.is_sick` (boolean flag)
   - `vfs.health_urgency` (computed urgency)
6. After 50 ticks:
   - Effect despawns
   - `on_despawn` sets `vfs.is_sick = false`

**Result**: Agent learns to avoid spoiled food (negative reward from health loss + cascade effects).

---

## Troubleshooting

### Common Issues

#### Q: Configs validate but training crashes

**Symptoms**: Compiler validation passes, but `demo_runner.py` crashes with runtime error.

**Possible Causes**:
1. **Observation dimension mismatch** - VFS added fields but obs_dim not updated
2. **Action space mismatch** - Enabled actions don't match network output size
3. **Device mismatch** - Trying to mix CPU and CUDA tensors

**Debugging**:
```bash
# Check observation dimensions
python -m townlet.compiler inspect configs/my_experiment/ | grep "Dimensions:"

# Check action count
python -m townlet.compiler inspect configs/my_experiment/ | grep "Actions:"

# Check for device errors in logs
grep "device" training_output.log
```

**Fix**: Ensure obs_dim and action_count consistent across all levels.

---

#### Q: Expression syntax error but looks correct

**Symptoms**: Parser reports syntax error, but expression looks valid.

**Possible Causes**:
1. **Missing quotes** - Expression must be quoted string in YAML
2. **YAML special characters** - Colon `:` inside unquoted string breaks YAML
3. **Unbalanced parentheses** - Hard to spot in long expressions

**Example**:
```yaml
# WRONG - Not quoted
value: target.bar.energy + 0.1

# WRONG - Colon breaks YAML
value: "if condition: then_value else else_value"

# CORRECT - Quoted and valid syntax
value: "target.bar.energy + 0.1"

# CORRECT - Use if-then-else (not colon)
value: "then_value if condition else else_value"
```

**Debugging**:
1. Copy expression to Python REPL
2. Try parsing with `ExpressionParser()`
3. Check for unbalanced parentheses with text editor

---

#### Q: Effect spawned but not ticking

**Symptoms**: Effect appears in active effects list but `on_tick` commands don't execute.

**Possible Causes**:
1. **Duration already expired** - Effect spawned with `duration=1`, despawned immediately
2. **Scope mismatch** - Spawned agent effect on item (wrong target)
3. **EffectManager not ticked** - `effect_manager.tick()` not called in env.step()

**Debugging**:
```python
# Check active effects
active_effects = env.effect_manager.get_all_active_effects()
print(f"Active effects: {len(active_effects)}")

# Check duration remaining
for effect in active_effects:
    print(f"Effect {effect.effect_id}: duration={effect.duration_remaining}")

# Check if tick called
# Add logging to effect_manager.tick()
```

**Fix**: Verify effect duration > 1, correct scope, and tick() called each step.

---

#### Q: VFS variable not appearing in observations

**Symptoms**: Defined VFS variable but not visible in agent observations.

**Possible Causes**:
1. **Not exposed** - Variable defined but not in `exposed_observations` (Phase 1)
2. **Wrong scope** - `agent_private` scope not readable by agent
3. **Expression not evaluated** - Computed variable but mark-and-sweep didn't mark it

**Debugging**:
```python
# Check VFS registry contents
vfs_values = env.vfs_registry.get_all("agent")
print(f"VFS variables: {vfs_values.keys()}")

# Check observation spec
obs_spec = env.observation_spec
print(f"Observation fields: {obs_spec.fields}")
```

**Fix**: Add variable to observation spec or change scope to `agent`.

---

#### Q: Item pickup/drop not working

**Symptoms**: Agent executes GET action but item not added to inventory.

**Possible Causes**:
1. **Inventory full** - `max_items_per_agent` reached
2. **Item too far** - Agent not at item position
3. **Action masked** - GET action masked when no items nearby

**Debugging**:
```python
# Check inventory state
inventory = env.item_manager.get_inventory(agent_idx)
print(f"Inventory: {inventory}")

# Check item positions
items = env.item_manager.get_all_items()
for item in items:
    print(f"Item {item.id} at {item.position}")

# Check action mask
action_mask = env.get_action_mask()
print(f"GET action masked: {action_mask[agent_idx, GET_ACTION_IDX]}")
```

**Fix**: Ensure inventory space, agent at item position, and action not masked.

---

### Debugging Tools

#### 1. Verbose Logging

Enable debug logging to see compilation details:

```bash
export LOG_LEVEL=DEBUG
python -m townlet.compiler compile configs/my_experiment/
```

**Output includes**:
- Config file load times
- Symbol table resolution steps
- Expression AST trees
- Type checking results
- Cache hit/miss status

---

#### 2. Expression Testing

Test expressions in isolation:

```python
from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.context import ExecutionContext
import torch

# Parse expression
parser = ExpressionParser()
ast = parser.parse("bar.energy + 0.3")

# Create context
bars = {"energy": torch.tensor([0.5, 0.6])}
context = ExecutionContext(bars=bars, vfs={}, affordances={}, temporal={}, device=torch.device("cpu"))

# Evaluate
evaluator = Evaluator(context)
result = evaluator.evaluate(ast)
print(f"Result: {result}")  # [0.8, 0.9]
```

---

#### 3. Effect Execution Tracing

Trace effect command execution:

```python
# Enable effect logging
import logging
logging.getLogger("townlet.effects").setLevel(logging.DEBUG)

# Run step
obs, reward, done, info = env.step(actions)

# Check logs for:
# - Effect spawned: <effect_id>
# - Executing on_tick for effect: <effect_id>
# - Command modify: target.bar.energy = 0.75
# - Effect despawned: <effect_id>
```

---

#### 4. Cache Inspection

Inspect cache without loading full environment:

```bash
# Inspect MessagePack cache directly
python -c "
import msgpack
with open('configs/my_experiment/.compiled/universe.msgpack', 'rb') as f:
    data = msgpack.unpack(f, raw=False)
    print('Keys:', data.keys())
    print('Metadata:', data['metadata'])
"
```

---

## Best Practices

### Config Organization

#### 1. One Experiment Per Directory

**Good**:
```
experiments/
├── energy_only/          # Experiment 1: Simple energy management
│   ├── experiment.yaml
│   └── levels/...
├── full_needs/           # Experiment 2: All 8 needs
│   ├── experiment.yaml
│   └── levels/...
└── temporal/             # Experiment 3: Day/night cycles
    ├── experiment.yaml
    └── levels/...
```

**Bad**:
```
configs/
├── experiment1_experiment.yaml    # Naming conflicts
├── experiment2_experiment.yaml
└── shared_levels/                 # Levels can't be shared safely
```

**Why**: Each experiment should be self-contained for reproducibility.

---

#### 2. Progressive Curriculum Levels

**Good**: Levels build complexity incrementally
```
levels/
├── L0_0_minimal/        # 1 meter, 1 affordance
├── L0_5_dual_resource/  # 2 meters, 4 affordances
├── L1_full_observability/ # All meters, all affordances, full visibility
├── L2_partial_observability/ # All meters, POMDP
└── L3_temporal_mechanics/ # All meters + time
```

**Bad**: Levels jump complexity
```
levels/
├── L0_minimal/          # 1 meter
└── L1_everything/       # All meters + POMDP + temporal + items (too big a jump!)
```

**Why**: Gradual complexity increase enables curriculum learning.

---

#### 3. Descriptive Effect Names

**Good**:
```yaml
effect_definitions:
  - id: energy_regen        # Clear: regenerates energy
  - id: poison              # Clear: damages health
  - id: caffeinated         # Clear: agent has caffeine boost
```

**Bad**:
```yaml
effect_definitions:
  - id: effect_1            # Unclear: what does this do?
  - id: buff                # Vague: buff what?
  - id: ate_food            # Wrong: describes action, not state
```

**Why**: Effect IDs appear in logs, observations, and debugging output.

---

#### 4. Always Use Clamp for Bar Modifications

**Good**:
```yaml
on_tick:
  - modify: target.bar.energy
    value: "clamp(target.bar.energy + 0.05, 0.0, 1.0)"
```

**Bad**:
```yaml
on_tick:
  - modify: target.bar.energy
    value: "target.bar.energy + 0.05"  # Can exceed [0, 1]!
```

**Why**: Prevents out-of-bounds bar values that break reward functions.

---

#### 5. Document Complex Expressions

**Good**:
```yaml
affordances:
  - name: WORK
    interactions:
      on_start:
        # Base pay: $20, bonus: $10 during rush hour (7-9am, 5-7pm)
        - modify: target.bar.money
          value: "target.bar.money + (20.0 + (10.0 if (temporal.hour >= 7 and temporal.hour < 9) or (temporal.hour >= 17 and temporal.hour < 19) else 0.0))"
```

**Bad**:
```yaml
affordances:
  - name: WORK
    interactions:
      on_start:
        - modify: target.bar.money
          value: "target.bar.money + (20.0 + (10.0 if (temporal.hour >= 7 and temporal.hour < 9) or (temporal.hour >= 17 and temporal.hour < 19) else 0.0))"
          # No comment - hard to understand!
```

**Why**: Long expressions are hard to read without context.

---

### Testing Strategies

#### 1. Test Each Layer Independently

Before integrating all layers, test each in isolation:

**Expression Language**:
```bash
pytest tests/test_townlet/unit/world/expression/ -v
```

**VFS**:
```bash
pytest tests/test_townlet/unit/vfs/ -v
```

**Effects**:
```bash
pytest tests/test_townlet/unit/effects/ -v
```

**Items**:
```bash
pytest tests/test_townlet/unit/items/ -v
```

---

#### 2. Use Smoke Tests for New Configs

Before full training, run short smoke test:

```bash
# 10 episodes, 50 steps each
python scripts/run_demo.py --config configs/my_experiment/ \
    --num-episodes 10 \
    --max-steps 50 \
    --no-checkpoint
```

**What to check**:
- No crashes
- Observations have correct shape
- Rewards are non-zero
- Effects spawn and despawn correctly

---

#### 3. Compare Against Baseline

When changing configs, compare metrics against baseline:

```bash
# Run baseline
python scripts/run_demo.py --config configs/baseline/ --output baseline_results.json

# Run new config
python scripts/run_demo.py --config configs/new/ --output new_results.json

# Compare
python scripts/compare_results.py baseline_results.json new_results.json
```

**Metrics to compare**:
- Mean episode reward
- Mean episode length
- Learning speed (episodes to convergence)
- Exploration diversity (RND loss)

---

#### 4. Validate Vocabulary Consistency

Before training across levels:

```bash
# Validate all levels use same vocabulary
python -m townlet.compiler validate configs/my_experiment/

# Expected: ✓ Vocabulary consistent across levels
```

---

#### 5. Test Checkpoint Transfer

Verify checkpoints transfer across levels:

```python
# Train on L0
python scripts/run_demo.py --config configs/my_experiment/ --level L0_minimal

# Load checkpoint and continue on L1
python scripts/run_demo.py --config configs/my_experiment/ --level L1_full \
    --checkpoint checkpoints/L0_minimal/episode_100.pt
```

**Expected**: No crashes, training continues smoothly.

---

### Performance Optimization

#### 1. Minimize on_tick Commands

Effects tick every step - keep command lists short:

**Good** (1-2 commands):
```yaml
on_tick:
  - modify: target.bar.energy
    value: "clamp(target.bar.energy + 0.05, 0.0, 1.0)"
```

**Bad** (many commands):
```yaml
on_tick:
  - modify: target.bar.energy
    value: "target.bar.energy + 0.01"
  - modify: target.bar.energy
    value: "target.bar.energy + 0.01"
  - modify: target.bar.energy
    value: "target.bar.energy + 0.01"
  # ... 10 more commands (slow!)
```

**Why**: Each command has overhead. Combine into single expression.

---

#### 2. Use Stack Policy Sparingly

Stack policy creates many instances:

**Good** (bounded stacking):
```yaml
- id: food_digesting
  reapply_policy: stack
  duration: 10  # Short duration = bounded instances
```

**Bad** (unbounded stacking):
```yaml
- id: permanent_buff
  reapply_policy: stack
  duration: 10000  # Very long duration = many instances accumulate
```

**Why**: 100 stacked instances = 100× command execution overhead.

---

#### 3. Cache Compiled Artifacts

Always use cache in production:

```bash
# First run: compile and cache
python scripts/run_demo.py --config configs/my_experiment/

# Subsequent runs: load from cache (faster)
python scripts/run_demo.py --config configs/my_experiment/
```

**Cache speedup**: 10-50× faster startup (no re-compilation).

---

#### 4. Profile Expression Evaluation

If expressions are slow:

```python
import cProfile
import pstats

# Profile expression evaluation
cProfile.run('evaluator.evaluate(ast)', 'profile_stats')

# Print top 20 slowest functions
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative').print_stats(20)
```

**Common bottlenecks**:
- Complex nested conditionals
- Many function calls in expressions
- Large vector operations

---

## See Also

**Config Schemas** (detailed reference docs):
- `docs/config-schemas/effects.md` - Effects system complete reference
- `docs/config-schemas/variables.md` - VFS variables configuration
- `docs/config-schemas/affordances.md` - Affordance interactions
- `docs/config-schemas/drive_as_code.md` - Reward function configuration

**Design Documents** (architectural context):
- `docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md` - Master implementation plan
- `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md` - Effects system architecture
- `docs/plans/2025-11-18-items-and-vfs-profiles.md` - Items system design

**Implementation Plans** (task breakdowns):
- `docs/plans/vfs_uplift/2025-11-19-task-1-2-expression-parser.md` - Expression language parser
- `docs/plans/vfs_uplift/2025-11-19-task-3-1-effects-dtos-catalog.md` - Effects DTOs and catalog
- `docs/plans/vfs_uplift/2025-11-20-task-4-items-system.md` - Items system implementation

**Integration Tests** (working examples):
- `tests/test_townlet/integration/test_world_compiler_full.py` - Complete pipeline tests
- `tests/test_townlet/integration/test_expression_vfs_effects.py` - Expression → VFS → Effects flow
- `tests/test_townlet/integration/test_curriculum_compatibility.py` - Level vocabulary consistency

**Example Configs** (copy-paste templates):
- `configs/default_curriculum/` - Complete reference curriculum
- `configs/test/effects_smoke/` - Minimal effects examples
- `configs/test/items_smoke/` - Minimal items examples (when complete)

---

**Status**: World Compiler (T0 Pillar 3) Complete
**Version**: 1.0
**Last Updated**: 2025-11-21
