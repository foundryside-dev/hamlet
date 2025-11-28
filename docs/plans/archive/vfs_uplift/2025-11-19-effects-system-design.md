# Effects System - Design Document

**Status:** Design Complete - Ready for Implementation
**Date:** 2025-11-19
**Owner:** World Compiler
**Related:** Items & VFS Profiles implementation plans

---

## Executive Summary

The **Effects System** is the foundational command pipeline language for HAMLET's World Compiler. It provides a unified, declarative way to express all simulation behavior: item interactions, affordance effects, VFS updates, cascades, and temporal changes.

**Key Principles:**
- **Reusable effect catalog**: Define effects once, reference by name everywhere
- **Command pipeline execution**: Ordered, explicit commands (no hidden defaults)
- **VFS expression language**: Pure functional expressions for all value computations
- **Strong typing**: Compile-time validation of paths, references, and types
- **Scope-aware**: Effects attach to global/agent/item/affordance with appropriate context

**Architectural Position:** Effects is the **bedrock** of the World Compiler (T0 Pillar 3), compiled before bars, VFS, cascades, items, and affordances. All other World components use Effects for mutation.

---

## 1. Three T0 Pillars Architecture

HAMLET has three Tier-0 compilers that produce the foundational compiled universe:

### **T0 Pillar 1: Strata Compiler**
- **What:** Shape of the world (spatial substrate)
- **Config:** `stratum.yaml`
- **Output:** `CompiledSubstrate` (Grid2D, Continuous, Aspatial, GridND, etc.)

### **T0 Pillar 2: Brain Compiler**
- **What:** How agents think about the world
- **Components:**
  - Q-Learning (DQN, replay buffer, target network, hyperparameters)
  - Drive As Code (reward functions: extrinsic/intrinsic/shaping)
- **Configs:** `brain.yaml`, `drive_as_code.yaml`
- **Output:** `CompiledBrain`
  - `brain_config` (Q-learning parameters)
  - `drive_hash` (reward function provenance)

### **T0 Pillar 3: World Compiler**
- **What:** World objects, rules, and simulation behavior
- **Foundation:** **Effects** (command pipeline language)
- **Components (all built on Effects):**
  - Effects (command pipelines + expressions)
  - Bars (meter dynamics)
  - VFS (variables and features)
  - Cascades (meter interactions)
  - Items (world objects with state)
  - Affordances (interaction points)
- **Configs:** `effects.yaml`, `bars.yaml`, `vfs_profiles.yaml`, `cascades.yaml`, `items.yaml`, `affordances.yaml`
- **Output:** `CompiledWorld`
  - `effect_catalog` (compiled command pipelines)
  - `bar_dynamics`
  - `vfs_profiles`
  - `cascade_rules`
  - `item_catalog`
  - `affordance_catalog`

---

## 2. Effects Catalog Schema

Effects are **precompiled definitions** stored in `effects.yaml` (experiment-scoped). Each effect is a reusable simulation behavior with lifecycle hooks.

### **2.1 Basic Effect Structure**

```yaml
effects:
  version: "1.0"

  effect_definitions:
    - id: "ate_food"
      scope: agent  # Where effect can attach: agent | item | global | affordance

      # Lifecycle parameters
      duration: 10  # Ticks until auto-despawn (REQUIRED)
      intensity: 1.0  # Default strength multiplier (can override at spawn)

      # Stacking policy (REQUIRED - no defaults!)
      reapply_policy: "stack"  # stack | renew | merge | replace

      # Visibility (observation exposure)
      observable: true  # Agent can see this effect in observations

      # Command pipelines (execute at lifecycle stages)
      on_spawn:
        - modify: target.vfs.digesting
          value: true

      on_tick:
        - modify: target.bar.energy
          value: target.bar.energy + (0.05 * intensity)
        - modify: target.bar.hunger
          value: target.bar.hunger - (0.03 * intensity)

      on_despawn:
        - modify: target.vfs.digesting
          value: false

      # Optional: Additional lifecycle hooks
      on_interrupt: []  # When effect forcibly removed
```

### **2.2 Reapply Policies**

When `spawn_effect("ate_food")` is called on an agent that already has `"ate_food"`, the policy determines behavior:

**`stack`** - Create independent instance
```yaml
reapply_policy: "stack"
# Result: Multiple independent timers
# Use case: Each food eaten has its own digestion cycle
# Example: Eat at tick 1 (expires 11), eat at tick 5 (expires 15)
#          → Both effects tick independently
```

**`renew`** - Refresh duration
```yaml
reapply_policy: "renew"
# Result: Single instance, timer resets
# Use case: "Well fed" status extends with each meal
# Example: Eat at tick 1 (expires 11), eat at tick 5 (now expires 15)
#          → Only one effect, duration refreshed
```

**`merge`** - Increase intensity
```yaml
reapply_policy: "merge"
# Result: Single instance, intensity stacks
# Use case: Cumulative drug dosage
# Example: Eat at tick 1 (intensity=1.0), eat at tick 5 (intensity=2.0)
#          → Stronger per-tick effect
```

**`replace`** - Clear old, spawn new
```yaml
reapply_policy: "replace"
# Result: Old despawned, new spawned
# Use case: "Currently eating" status (only one at a time)
# Example: Eat at tick 1, eat at tick 5 → despawn old, spawn new
```

### **2.3 Scope Semantics**

**`scope: agent`** - Effect attaches to individual agents
- Access: `target.bar.*`, `target.vfs.*`, `target.position`
- Storage: Per-agent effect list
- Example: `"caffeinated"`, `"hungry"`, `"in_trouble_at_work"`

**`scope: item`** - Effect attaches to item instances
- Access: `target.vfs.*`, `target.position`, `target.holder_agent`
- Storage: Per-item effect list
- Example: `"item_decay"`, `"flaming"`, `"cursed"`

**`scope: global`** - Effect attaches to world state
- Access: `global.vfs.*`, `global.bar.*` (if global bars exist)
- Storage: Single global effect list
- Example: `"nighttime"`, `"heatwave"`, `"rush_hour"`

**`scope: affordance`** - Effect attaches to affordance instances
- Access: `target.vfs.*`, `target.position`, `target.availability`
- Storage: Per-affordance effect list
- Example: `"broken"`, `"locked"`, `"occupied"`

### **2.4 Observable Effects**

```yaml
observable: true   # Agent sees this in observations (e.g., "hungry", "wet")
observable: false  # Hidden from agent (e.g., "in_trouble_at_work", "cursed")
```

Effects with `observable: true` are added to agent observations (future work: obs spec builder integration).

---

## 3. Command Pipeline Specification

Commands are the **imperative operations** that effects execute at lifecycle stages. All commands use **path notation** for targets and **VFS expressions** for values.

### **3.1 State Modification Commands**

```yaml
# modify: Set value using expression
- modify: target.bar.energy
  value: target.bar.energy + 0.1

# set: Direct assignment (alias for modify with simple value)
- set: self.vfs.durability
  value: 0.5

# increment: Shorthand for add
- increment: global.vfs.total_food_eaten
  by: 1

# decrement: Shorthand for subtract
- decrement: self.vfs.uses_remaining
  by: 1
```

### **3.2 Entity Lifecycle Commands**

```yaml
# spawn_item: Create item in world
- spawn_item:
    type_id: "puddle"
    position: self.position  # Expression for position
    assign_to: puddle_ref    # Optional: Capture reference for later use

# spawn_effect: Apply effect to target
- spawn_effect:
    effect_id: "wet"
    target: agent           # or self, global, vfs.some_ref
    duration: 20            # Optional: Override catalog default
    intensity: 1.5          # Optional: Override catalog default

# delete: Remove entity from simulation
- delete: self              # Effect/item removes itself

# despawn: Remove item from world (items only)
- despawn: item_ref         # Remove item by reference
```

### **3.3 Control Flow Commands**

```yaml
# if/then/else: Conditional execution
- if: self.bar.health < 0.3
  then:
    - spawn_effect:
        effect_id: "critical_health"
        target: self
  else:
    - modify: self.bar.mood
      value: self.bar.mood + 0.05

# for_each: Iterate over collections
- for_each: nearby_agents
  range: 3.0              # Within distance 3.0
  do:
    - modify: agent.vfs.social
      value: agent.vfs.social + 0.01
    - spawn_effect:
        effect_id: "social_boost"
        target: agent
```

### **3.4 Messaging/Events Commands**

```yaml
# emit_event: Trigger event observers (future: for logging/analytics)
- emit_event:
    type: "food_eaten"
    data:
      calories: 500
      item_id: self.id

# trigger_cascade: Activate cascade rule manually
- trigger_cascade:
    cascade_id: "energy_to_mood"
    strength_multiplier: 2.0
```

### **3.5 Randomness Commands**

```yaml
# Conditional with random chance
- if: random() < 0.1       # 10% chance per tick
  then:
    - spawn_effect:
        effect_id: "food_poisoning"
        target: target

# sample: Choose random value from list
- sample:
    from: ["apple", "burger", "salad"]
    weights: [0.5, 0.3, 0.2]  # Optional: Probability distribution
    assign_to: random_food
- spawn_item:
    type_id: random_food
    position: self.position
```

### **3.6 Path Notation**

Paths use dot notation to traverse entity state:

**Special Variables:**
- `self` - Current entity executing the effect
- `target` - Entity the effect is attached to
- `agent` - Alias for `target` when `scope=agent`
- `global` - Global world state
- `intensity` - Effect's current intensity parameter
- `duration` - Effect's total duration
- `duration_remaining` - Ticks until despawn
- `elapsed_ticks` - How long effect has been active

**Path Examples:**
```yaml
target.bar.energy              # Agent's energy meter
target.vfs.is_starving         # Agent's VFS variable
target.position                # Agent's position (vec2i/vec3i)
self.vfs.durability            # Item's durability (when scope=item)
global.vfs.is_night            # Global VFS variable
vfs.nearest_food.vfs.spoilage  # VFS ref → item → item VFS
```

---

## 4. Type System

The World Compiler validates all paths and expressions using a strong type system.

### **4.1 Primitive Types**

```yaml
scalar   # Single float value
bool     # Boolean (true/false)
vec2i    # 2D integer vector [x, y]
vec3i    # 3D integer vector [x, y, z]
vecNi    # N-dimensional integer vector (requires dims: N)
vecNf    # N-dimensional float vector (requires dims: N)
```

### **4.2 Reference Types**

VFS variables can store **typed references** to entities:

```yaml
# vfs_profiles.yaml
agent_profiles:
  - id: closest_friend
    type: agent_ref
    expression: nearest_agent(vfs.social > 0.5)

  - id: target_food_item
    type: item_ref
    expression: nearest_item(tag="food")

  - id: preferred_bed
    type: affordance_ref
    expression: nearest_affordance(type="Bed")

  - id: active_buff
    type: effect_ref
    expression: first_effect(effect_id="well_fed")
```

### **4.3 Tensor Types (Advanced)**

For power users who need direct GPU tensor manipulation:

```yaml
tensor1d  # 1D tensor [N]
tensor2d  # 2D tensor [M, N]
tensor3d  # 3D tensor [L, M, N]
tensorNd  # N-dimensional tensor (requires shape)

# Example: Distance matrix
global_profiles:
  - id: agent_distance_matrix
    type: tensor2d
    shape: [num_agents, num_agents]  # REQUIRED
    initial_value: zeros             # REQUIRED (zeros | ones | eye | random_normal)
```

### **4.4 Path Traversal Through References**

VFS references enable **entity graph traversal**:

```yaml
# Effect command using VFS reference
on_tick:
  # Access referenced item's VFS
  - modify: vfs.target_food_item.vfs.spoilage
    value: vfs.target_food_item.vfs.spoilage + 0.1

  # Access referenced agent's bars
  - modify: vfs.closest_friend.bar.mood
    value: vfs.closest_friend.bar.mood + 0.05

  # Spawn effect on referenced entity
  - spawn_effect:
      effect_id: "social_boost"
      target: vfs.closest_friend
```

### **4.5 Compile-Time Type Validation**

The World Compiler validates all paths:

```python
# Validation pseudo-code
def validate_path(path: "vfs.target_food_item.vfs.spoilage"):
    # 1. Resolve "vfs.target_food_item"
    var_def = lookup_vfs_variable("target_food_item")
    assert var_def.type == "item_ref", "Expected item reference"

    # 2. Resolve ".vfs.spoilage" on item type
    item_vfs = get_item_vfs_profiles()
    assert "spoilage" in item_vfs, "Item VFS 'spoilage' not found"

    # 3. Return type info
    return TypeInfo(scalar, owner="item")
```

**Compile Errors:**
```yaml
# ERROR: Type mismatch
- modify: vfs.target_food_item.bar.energy
  value: 0.5
# CompileError: Items don't have bars (only agents do)

# ERROR: Reference undefined
- modify: vfs.nonexistent.vfs.health
  value: 0
# CompileError: VFS variable 'nonexistent' not found

# ERROR: Field not found
- modify: vfs.closest_friend.vfs.invalid_field
  value: 1.0
# CompileError: Agent VFS profile 'invalid_field' not defined
```

---

## 5. Expression Language Integration

All command `value` fields use the **VFS expression language** from `VARIABLE_SUBSYSTEM.md`. This provides a unified syntax across effects, VFS variables, conditions, and DAC rewards.

### **5.1 Execution Context**

Every expression has access to contextual variables based on effect scope:

```yaml
# Effect on agent
on_tick:
  - modify: target.bar.energy
    value: target.bar.energy + (0.05 * intensity)

# Available in expressions:
# - target.bar.*       → Agent's meters
# - target.vfs.*       → Agent's VFS variables
# - target.position    → Agent's position
# - self.*             → Effect's own state
# - intensity          → Effect parameter
# - duration           → Effect total duration
# - duration_remaining → Ticks until despawn
# - elapsed_ticks      → How long active
# - global.vfs.*       → Global VFS variables
# - time_of_day        → Temporal state [0, 23]
# - step_count         → Episode step
```

### **5.2 Operator Library**

Effects can use **all operators** from VARIABLE_SUBSYSTEM.md:

**Mathematical:**
```yaml
value: sqrt(pow(target.bar.energy, 2) + pow(target.bar.health, 2))
value: clamp(target.bar.mood + 0.1, 0.0, 1.0)
```

**Trigonometric:**
```yaml
value: sin(2 * pi * time_of_day / 24)
value: cos(elapsed_ticks / 10)
```

**Temporal:**
```yaml
value: moving_average(target.bar.energy, 10)
value: delta(target.bar.health)  # Change since last tick
value: lag(target.bar.mood, 5)   # Value 5 ticks ago
```

**Spatial:**
```yaml
value: distance_to_affordance("Fridge")
value: if_then_else(in_range("Bed", 2.0), 1.0, 0.0)
```

**Statistical:**
```yaml
value: min(target.bar.energy, target.bar.health, target.bar.satiation)
value: mean(vfs.observation_history[0:10])
```

**Stochastic:**
```yaml
value: clamp(gaussian_noise(0, 0.1), -0.5, 0.5)
value: bernoulli(0.05)  # 5% chance
```

**Conditional:**
```yaml
value: if_then_else(target.bar.energy < 0.3, -0.1, 0.05)
value: switch(floor(time_of_day / 6), [0.5, 1.0, 1.2, 0.8])
```

### **5.3 Expression Compilation**

The World Compiler parses expressions into ASTs:

```yaml
# Config
value: target.bar.energy + (0.05 * intensity)

# Compiled AST
BinaryOp(
  op=ADD,
  left=PathAccess(["target", "bar", "energy"]),
  right=BinaryOp(
    op=MUL,
    left=Constant(0.05),
    right=Variable("intensity")
  )
)
```

Runtime execution evaluates ASTs using GPU tensors.

### **5.4 Type Safety**

Compiler validates expression types match target types:

```yaml
# ✓ VALID: scalar → scalar
- modify: target.bar.energy
  value: 0.5

# ✓ VALID: vec2i → vec2i
- modify: target.position
  value: [3, 5]

# ✗ INVALID: vec2i → scalar
- modify: target.bar.energy
  value: [1, 2]
# CompileError: Cannot assign vec2i to scalar field
```

---

## 6. World Compiler Pipeline

The World Compiler orchestrates compilation of all simulation components, with **Effects compiled first** (other components reference effects).

### **6.1 Compilation Stages**

```python
class WorldCompiler:
    def compile(self, config_dir: Path) -> CompiledWorld:
        # Stage 1: Load all configs
        raw = self.load_configs(config_dir)

        # Stage 2: Compile Effects FIRST (foundation)
        effects = self.compile_effects(raw.effects)

        # Stage 3: Compile other components (can reference effects)
        bars = self.compile_bars(raw.bars, effects)
        vfs = self.compile_vfs(raw.vfs_profiles, effects)
        cascades = self.compile_cascades(raw.cascades, effects)
        items = self.compile_items(raw.items, effects, vfs)
        affordances = self.compile_affordances(raw.affordances, effects)

        # Stage 4: Cross-validate references
        self.cross_validate(effects, bars, vfs, cascades, items, affordances)

        # Stage 5: Emit compiled world
        return CompiledWorld(
            effect_catalog=effects,
            bar_dynamics=bars,
            vfs_profiles=vfs,
            cascade_rules=cascades,
            item_catalog=items,
            affordance_catalog=affordances,
            world_hash=self.compute_hash(...)
        )
```

### **6.2 Effect Compilation Details**

```python
def compile_effects(self, yaml: EffectsConfig) -> CompiledEffectCatalog:
    catalog = {}

    for effect_def in yaml.effect_definitions:
        # 1. Validate schema
        validate_effect_schema(effect_def)

        # 2. Parse command pipelines to ASTs
        on_spawn_ast = parse_commands(effect_def.on_spawn)
        on_tick_ast = parse_commands(effect_def.on_tick)
        on_despawn_ast = parse_commands(effect_def.on_despawn)

        # 3. Parse expressions in command values
        for cmd in on_tick_ast:
            if cmd.type == "modify":
                cmd.value_expr = parse_expression(cmd.value)

        # 4. Store compiled effect
        catalog[effect_def.id] = CompiledEffect(
            id=effect_def.id,
            scope=effect_def.scope,
            duration=effect_def.duration,
            intensity=effect_def.intensity,
            reapply_policy=effect_def.reapply_policy,
            on_spawn_commands=on_spawn_ast,
            on_tick_commands=on_tick_ast,
            on_despawn_commands=on_despawn_ast
        )

    return CompiledEffectCatalog(effects=catalog)
```

### **6.3 Cross-Validation**

```python
def cross_validate(self, effects, bars, vfs, ...):
    for effect in effects.effects.values():
        for cmd in effect.on_tick_commands:
            # Validate path resolution
            if cmd.type == "modify":
                self.validate_path(cmd.target_path, effect.scope, bars, vfs)

            # Validate effect references
            if cmd.type == "spawn_effect":
                if cmd.effect_id not in effects.effects:
                    raise CompileError(
                        f"Effect '{effect.id}' references unknown effect '{cmd.effect_id}'"
                    )

            # Validate item references
            if cmd.type == "spawn_item":
                if cmd.type_id not in items.item_types:
                    raise CompileError(
                        f"Effect '{effect.id}' spawns unknown item '{cmd.type_id}'"
                    )
```

### **6.4 Error Reporting**

```yaml
# effects.yaml
- id: ate_food
  on_tick:
    - modify: target.bar.nonexistent
      value: 0.5
```

```
CompilationError: Effect 'ate_food' command 'modify'
  Path: target.bar.nonexistent
  Error: Bar 'nonexistent' not found in bars.yaml
  Available bars: energy, health, satiation, hunger, mood, social, fitness, hygiene

  File: configs/experiment/effects.yaml
  Line: 12

  Did you mean: 'energy'?
```

---

## 7. Runtime Execution Model

The **EffectManager** tracks all active effects and executes their command pipelines each environment step.

### **7.1 ActiveEffect Runtime Structure**

```python
@dataclass
class ActiveEffect:
    """Runtime instance of an effect attached to an entity."""

    effect_id: str              # Reference to catalog definition
    instance_id: int            # Unique instance ID
    target_entity: EntityRef    # What it's attached to
    scope: EffectScope          # Where it lives (agent/item/global/affordance)

    # Lifecycle state
    intensity: float            # Current intensity multiplier
    duration_total: int         # Total ticks when spawned
    duration_remaining: int     # Ticks until despawn
    elapsed_ticks: int          # How long active
    spawn_step: int             # When it was created

    # Compiled commands (from catalog)
    on_tick_commands: List[CompiledCommand]
    on_despawn_commands: List[CompiledCommand]
```

### **7.2 EffectManager Lifecycle**

```python
class EffectManager:
    """Manages all active effects across all entities."""

    def __init__(self, compiled_catalog: CompiledEffectCatalog, device: torch.device):
        self.catalog = compiled_catalog
        self.device = device

        # Scoped storage
        self.global_effects: List[ActiveEffect] = []
        self.agent_effects: Dict[int, List[ActiveEffect]] = {}
        self.item_effects: Dict[int, List[ActiveEffect]] = {}
        self.affordance_effects: Dict[str, List[ActiveEffect]] = {}

        self.next_instance_id = 0

    def spawn_effect(
        self,
        effect_id: str,
        target: EntityRef,
        duration: int | None = None,
        intensity: float = 1.0
    ) -> ActiveEffect:
        """Spawn new effect instance."""

        effect_def = self.catalog.effects[effect_id]

        # Handle reapply policy
        existing = self._find_existing(effect_id, target)
        if existing:
            if effect_def.reapply_policy == "renew":
                existing.duration_remaining = duration or effect_def.duration
                return existing
            elif effect_def.reapply_policy == "merge":
                existing.intensity += intensity
                return existing
            elif effect_def.reapply_policy == "replace":
                self._despawn_effect(existing)

        # Create new instance
        active = ActiveEffect(
            effect_id=effect_id,
            instance_id=self.next_instance_id,
            target_entity=target,
            scope=effect_def.scope,
            intensity=intensity,
            duration_total=duration or effect_def.duration,
            duration_remaining=duration or effect_def.duration,
            elapsed_ticks=0,
            spawn_step=self.current_step,
            on_tick_commands=effect_def.on_tick_commands,
            on_despawn_commands=effect_def.on_despawn_commands
        )
        self.next_instance_id += 1

        # Store in scoped collection
        self._add_to_scope(active)

        # Execute on_spawn commands
        self._execute_commands(active, effect_def.on_spawn_commands)

        return active

    def tick(self, env_state: EnvironmentState) -> None:
        """Execute all active effects for one timestep."""

        for scope_effects in [
            self.global_effects,
            *self.agent_effects.values(),
            *self.item_effects.values(),
            *self.affordance_effects.values()
        ]:
            for effect in scope_effects:
                # Build execution context
                context = self._build_context(effect, env_state)

                # Execute on_tick commands
                self._execute_commands(effect, effect.on_tick_commands, context)

                # Update lifecycle
                effect.elapsed_ticks += 1
                effect.duration_remaining -= 1

                # Check for expiry
                if effect.duration_remaining <= 0:
                    self._despawn_effect(effect, context)
```

### **7.3 Command Execution**

```python
def _execute_commands(
    self,
    effect: ActiveEffect,
    commands: List[CompiledCommand],
    context: ExecutionContext
) -> None:
    """Execute command pipeline."""

    for cmd in commands:
        match cmd.type:
            case "modify":
                # Evaluate expression
                new_value = self._eval_expr(cmd.value_expr, context)

                # Resolve target path to GPU tensor
                target_tensor = context.resolve_path(cmd.target_path)

                # Apply mutation
                target_tensor.copy_(new_value)

            case "spawn_effect":
                self.spawn_effect(
                    effect_id=cmd.effect_id,
                    target=context.resolve_target(cmd.target),
                    duration=cmd.duration,
                    intensity=cmd.intensity
                )

            case "spawn_item":
                context.item_manager.spawn_item(
                    type_id=cmd.type_id,
                    position=context.resolve_expr(cmd.position)
                )

            case "if":
                condition = self._eval_expr(cmd.condition_expr, context)
                if condition:
                    self._execute_commands(effect, cmd.then_commands, context)
                elif cmd.else_commands:
                    self._execute_commands(effect, cmd.else_commands, context)

            case "delete":
                effect.marked_for_deletion = True
```

### **7.4 Execution Context**

```python
@dataclass
class ExecutionContext:
    """Runtime context for expression/command evaluation."""

    # Entity references
    effect: ActiveEffect
    target_entity: EntityRef

    # State tensors (GPU)
    bars: torch.Tensor                      # [batch, num_bars]
    vfs_global: Dict[str, torch.Tensor]
    vfs_agent: Dict[str, torch.Tensor]
    vfs_item: Dict[str, torch.Tensor]

    # Managers
    item_manager: ItemManager
    effect_manager: EffectManager

    # Temporal state
    step_count: int
    time_of_day: float

    def resolve_path(self, path: List[str]) -> torch.Tensor:
        """Resolve path like 'target.bar.energy' to GPU tensor."""
        match path[0]:
            case "target":
                match path[1]:
                    case "bar":
                        bar_idx = self.bar_name_to_idx[path[2]]
                        return self.bars[self.target_entity.id, bar_idx]
                    case "vfs":
                        return self.vfs_agent[path[2]][self.target_entity.id]
            case "global":
                match path[1]:
                    case "vfs":
                        return self.vfs_global[path[2]]
```

### **7.5 Environment Integration**

```python
class VectorizedHamletEnv:
    def __init__(self, compiled_universe: CompiledUniverse):
        # ... existing init ...

        # NEW: Initialize EffectManager
        self.effect_manager = EffectManager(
            compiled_catalog=compiled_universe.world.effect_catalog,
            device=self.device
        )

    def step(self, actions):
        # ... existing step logic ...

        # NEW: Execute all active effects
        self.effect_manager.tick(self.state)

        # ... continue with observations, rewards, etc ...
```

---

## 8. Integration Examples

### **8.1 Items Use Effects (Clean from Day 1)**

```yaml
# items.yaml - No opaque dicts, pure Effects
item_types:
  - id: apple
    name: "Apple"
    icon: "🍎"
    vfs_profiles: [item_freshness, item_calories]

    interactions:
      pickup:
        commands:
          - modify: target.vfs.inventory_weight
            value: target.vfs.inventory_weight + 0.1

      use:
        commands:
          # Spawn reusable effect
          - spawn_effect:
              effect_id: "ate_food"
              target: agent
              duration: 10
              intensity: vfs.item_calories / 100  # Scale by item

          # Consume item
          - decrement: self.vfs.item_uses
            by: 1
          - if: self.vfs.item_uses <= 0
            then:
              - delete: self

      drop:
        commands:
          - modify: target.vfs.inventory_weight
            value: target.vfs.inventory_weight - 0.1
          - spawn_effect:
              effect_id: "item_decay"
              target: self
              duration: 100
```

### **8.2 Affordances Migrate to Effects**

```yaml
# OLD: affordances.yaml (EffectPipeline - deprecated)
affordances:
  - id: fridge
    on_completion:
      - meter: energy
        amount: 0.3

# NEW: affordances.yaml (Effects)
affordances:
  - id: fridge
    on_completion:
      commands:
        - spawn_effect:
            effect_id: "ate_food"
            target: agent
            intensity: 1.5  # Fridge food more substantial
        - spawn_effect:
            effect_id: "satisfied"
            target: agent
            duration: 20
```

### **8.3 VFS Variables Drive Effects**

```yaml
# vfs_profiles.yaml
agent_profiles:
  - id: is_starving
    type: bool
    expression: bar["hunger"] < 0.15

  - id: nearest_food_item
    type: item_ref
    expression: nearest_item(tag="food")

# effects.yaml
effects:
  - id: starvation_damage
    scope: agent
    on_tick:
      - modify: target.bar.health
        value: target.bar.health - 0.05
      - modify: target.bar.mood
        value: target.bar.mood - 0.03

# Environment step (pseudo-code)
if agent.vfs.is_starving and not has_effect(agent, "starvation_damage"):
    spawn_effect("starvation_damage", target=agent)
```

### **8.4 Cascades as Effect Triggers**

```yaml
# cascades.yaml
cascades:
  - category: health_crisis
    rules:
      - source: health
        target: mood
        threshold: 0.2
        on_trigger:
          commands:
            - spawn_effect:
                effect_id: "panic"
                target: agent
                duration: 30

# effects.yaml
effects:
  - id: panic
    scope: agent
    reapply_policy: renew  # Extends panic duration
    on_tick:
      - modify: target.bar.mood
        value: target.bar.mood - 0.05
      - modify: target.vfs.decision_clarity
        value: 0.3
```

### **8.5 Complete Example: Food Poisoning Chain**

```yaml
# 1. Item with spoilage
item_types:
  - id: leftovers
    vfs_profiles: [item_spoilage]
    interactions:
      use:
        commands:
          - if: self.vfs.item_spoilage > 0.8
            then:
              - spawn_effect:
                  effect_id: "food_poisoning"
                  target: agent
                  intensity: self.vfs.item_spoilage
            else:
              - spawn_effect:
                  effect_id: "ate_food"
                  target: agent

# 2. Item decay effect (passive spoilage)
effects:
  - id: item_decay
    scope: item
    on_tick:
      - increment: target.vfs.item_spoilage
        by: 0.02

# 3. Food poisoning effect
effects:
  - id: food_poisoning
    scope: agent
    duration: 50
    reapply_policy: merge  # Multiple bad foods compound
    on_tick:
      - modify: target.bar.health
        value: target.bar.health - (0.05 * intensity)
      - if: random() < 0.1
        then:
          - spawn_effect:
              effect_id: "nausea"
              target: target

# 4. Nausea effect (nested)
effects:
  - id: nausea
    scope: agent
    duration: 10
    on_tick:
      - modify: target.bar.mood
        value: target.bar.mood - 0.1
      - modify: target.vfs.can_eat
        value: false
    on_despawn:
      - modify: target.vfs.can_eat
        value: true
```

---

## 9. Implementation Phases

### **Phase 0: Effects Foundation (6-8 days)**

Build Effects system in isolation:

```
src/townlet/effects/
├── schema.py           # EffectDef, ActiveEffect, CommandNode DTOs
├── executor.py         # Command pipeline interpreter
├── manager.py          # ActiveEffect lifecycle (tick, spawn, despawn)
├── context.py          # Runtime execution context
└── catalog.py          # Effect catalog loading/validation

configs/test/effects_smoke/
└── effects.yaml        # Test effects

tests/test_townlet/unit/effects/  # 40-50 tests
├── test_command_pipeline.py
├── test_effect_lifecycle.py
└── test_expression_context.py
```

**Success Criteria:**
- Can load effects.yaml catalog
- Can spawn/tick/despawn effects on mock entities
- All command types (A-E) working in isolation
- No integration with environment yet

### **Phase 1: Affordance Migration (3-4 days)**

Replace `EffectPipeline` with unified Effects:

```python
# Delete: src/townlet/config/effect_pipeline.py
# Migrate: All affordances.yaml files to new schema
```

**Success Criteria:**
- All curriculum levels migrated
- Old EffectPipeline deleted
- Existing tests pass

### **Phase 2: Items Implementation (8-10 days)**

Implement items using Effects from day 1 (no opaque dicts):

**Success Criteria:**
- items_smoke working with Effects
- Items can spawn/modify effects
- No opaque dict code written

### **Phase 3: VFS Dynamic Variables (4-6 days - Optional)**

VFS variables can update via Effects:

```yaml
agent_profiles:
  - id: energy_urgency
    type: scalar
    update_mode: effect_driven  # NEW
```

---

## 10. Open Questions

### **10.1 Observable Effects in Observations**

How should `observable: true` effects appear in agent observations?

**Option A:** Fixed slots (similar to items)
- Reserve N effect slots in obs vector
- Mask unused slots
- Pro: Stable obs_dim
- Con: Limited to N effects

**Option B:** Effect summary features
- Add `num_active_effects` (scalar)
- Add `effect_intensity_sum` (scalar)
- Pro: Bounded obs contribution
- Con: Loses effect identity

**Option C:** One-hot encoding
- One-hot vector over effect catalog
- Pro: Agent knows which effects
- Con: Large obs_dim for big catalogs

**Recommendation:** Defer to VFS Profiles integration (Phase 3). Effects can write to VFS variables which are already in observations.

### **10.2 Effect Observation Masking**

Should effects automatically mask affordance availability?

```yaml
effects:
  - id: roadblock_active
    scope: global
    affordance_masks:
      - affordance_id: road_tile_5_3
        available: false
```

**Decision:** YES - effects can modify `affordance.available` via commands:

```yaml
on_spawn:
  - modify: affordance.road_tile_5_3.available
    value: false
on_despawn:
  - modify: affordance.road_tile_5_3.available
    value: true
```

No special `affordance_masks` field needed (commands are sufficient).

### **10.3 Effect Nesting Depth Limits**

Should we limit effect spawning depth to prevent infinite recursion?

```yaml
# Effect A spawns Effect B, which spawns Effect C, ...
```

**Recommendation:** Add compiler warning for recursive references, runtime limit (max_depth=10).

---

## 11. Success Metrics

### **Phase 0 (Effects Foundation)**
- ✅ 40-50 unit tests passing
- ✅ Can load effects_smoke/effects.yaml
- ✅ All command types execute correctly
- ✅ Expression evaluation works

### **Phase 1 (Affordance Migration)**
- ✅ All curriculum levels migrated
- ✅ EffectPipeline code deleted
- ✅ Zero regression in existing tests

### **Phase 2 (Items with Effects)**
- ✅ items_smoke full integration
- ✅ Items spawn/modify effects
- ✅ No opaque dict code exists

### **Phase 3 (VFS Integration)**
- ✅ VFS variables can trigger effects
- ✅ Effects update VFS variables
- ✅ Observable effects in observations

---

## 12. Related Documentation

- **VFS Expression Language:** `configs/reference_config/VARIABLE_SUBSYSTEM.md`
- **Items & VFS Profiles Plan:** `docs/plans/2025-11-18-items-and-vfs-profiles.md`
- **VFS Uplift Phases:** `docs/plans/vfs_uplift/`
- **Drive As Code:** `docs/config-schemas/drive_as_code.md`

---

**Next Steps:**
1. Review this design with team
2. Create Phase 0 implementation plan (task-by-task)
3. Begin Effects foundation implementation
4. Update Items/VFS plans to reference Effects
