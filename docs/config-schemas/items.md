# Items Configuration

---
## AI-Friendly Frontmatter

**Purpose**: Items catalog schema for world objects that agents can pick up, use, and drop

**When to Read**: Working with Items system, inventory mechanics, consumables, collectibles, durables, or item-based interactions

**AI-Friendly Summary**:
Items are world objects that agents can interact with through GET, USE_SLOT_N, and DROP_SLOT_N actions. Each item type is defined in an experiment-level catalog (`items.yaml`) with VFS-backed state (durability, quality, etc.), Effects-based interactions (on_pickup/on_use/on_drop), and lifecycle properties (duration, cooldown). Level-specific appearance configs control spawn rules (count, interval, position). Items use fixed-size inventories per agent and support periodic respawning. The separation of catalog (experiment-level types) from appearance (level-specific spawning) enables curriculum progression without duplicating item definitions.

**Reading Strategy**:
- **Quick Reference**: Jump to "Field Reference" sections for specific field documentation
- **Examples**: See "Complete Examples" section for real item types (consumables, durables, collectibles)
- **First-Time Users**: Read "Overview" → "File Structure" → "Catalog vs Appearance" → "Complete Examples"
- **Integration**: Read "VFS State" and "Interactions" sections for Effects integration

**Related Documents**:
- `docs/config-schemas/effects.md` - Effects command language for item interactions
- `docs/config-schemas/variables.md` - VFS variable definitions (item scope)
- `src/townlet/items/manager.py` - ItemManager implementation
- `src/townlet/items/instance.py` - ItemInstance runtime state
- `src/townlet/items/inventory.py` - Inventory management
- `src/townlet/items/action_handlers.py` - Action execution (GET, USE_SLOT_N, DROP_SLOT_N)

---

**Status**: Phase 1-3 Implementation (Items Integration)
**Version**: 1.0

---

## Overview

The Items system enables world objects that agents can pick up, use, and drop. Items have persistent state (via VFS), lifecycle management (duration, cooldown, respawning), and Effects-based interactions (on_pickup, on_use, on_drop).

### Key Principles

1. **Catalog-Appearance Separation**: Item types defined once (experiment-level), spawn rules per level
2. **VFS-Backed State**: Items use VFS profiles for persistent state (durability, quality, charges)
3. **Effects-Based Interactions**: All item behaviors use Effects command language
4. **Fixed-Size Inventories**: Each agent has max_items_per_agent inventory slots
5. **Lifecycle Management**: Items can expire (duration), respawn (spawn_interval), and have cooldowns

### Architectural Position

Items integrate with:
- **VFS**: Item-scoped variables for durability, quality, charges, etc.
- **Effects**: on_pickup/on_use/on_drop use Effects command pipelines
- **Actions**: GET, USE_SLOT_N, DROP_SLOT_N expand action space
- **Inventory**: Fixed-size per-agent storage with DENY_PICKUP policy

### Benefits

1. **Curriculum Progression**: Same item types, different spawn rules per level
2. **VFS Integration**: Items have persistent state (durability degrades, charges consumed)
3. **Declarative Configuration**: Change item behaviors without code changes
4. **Pedagogical Value**: Teaches resource management, inventory planning, item lifecycles
5. **Reproducibility**: Items part of compiled world with provenance tracking

---

## File Structure

Items configuration consists of two separate files:

### 1. Items Catalog (Experiment-Level)

**Location**: `<config_pack>/items.yaml`

Defines item types once for entire experiment.

```yaml
items:
  version: "1.0"

  item_types:
    - id: string                    # Unique item type identifier
      vfs_profile: string           # VFS profile ID (item scope)
      description: string           # Human-readable description (optional)
      duration: int | null          # Lifetime in ticks (null = permanent)
      cooldown: int | null          # Ticks before can respawn (null = no cooldown)
      interactions:
        on_pickup: CommandConfig[]  # Effects when picked up
        on_use: CommandConfig[]     # Effects when used (USE_SLOT_N)
        on_drop: CommandConfig[]    # Effects when dropped

  max_items_per_agent: int          # Inventory capacity (1-10)
  max_items_in_world: int           # Max concurrent items (1-1000)
```

### 2. Items Appearance (Level-Specific)

**Location**: `<config_pack>/levels/<level_name>/items.yaml`

Defines spawn rules for specific level.

```yaml
version: "1.0"

items:
  - item_type: string               # Item type ID from catalog
    spawn_count: int                # Number to spawn at level start
    spawn_interval: int | null      # Ticks between respawns (null = no respawn)
    spawn_position: random | fixed  # Position strategy
```

---

## Catalog Configuration

### Items Catalog Schema

```yaml
items:
  version: "1.0"

  item_types:
    - id: "apple"
      vfs_profile: "food"
      description: "Restores energy when consumed"
      duration: null        # Permanent (doesn't expire)
      cooldown: null        # No cooldown
      interactions:
        on_pickup: []
        on_use:
          - modify: "target.bar.energy"
            value: "target.bar.energy + 0.3"
        on_drop: []

    - id: "medkit"
      vfs_profile: "medical"
      description: "Restores health, degrades with use"
      duration: 100         # Despawns after 100 ticks
      cooldown: 50          # Can't respawn for 50 ticks
      interactions:
        on_pickup: []
        on_use:
          - modify: "target.bar.health"
            value: "target.bar.health + 0.5"
          - modify: "self.vfs.durability"
            value: "self.vfs.durability - 10"
        on_drop: []

  max_items_per_agent: 3
  max_items_in_world: 10
```

### Field Reference: Item Type

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique item type identifier (lowercase, alphanumeric + underscores) |
| `vfs_profile` | string | VFS profile ID from vfs_profiles.yaml (item scope) |
| `interactions` | object | Item interaction commands (on_pickup, on_use, on_drop) |

#### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | string | null | Human-readable description (metadata only) |
| `duration` | int \| null | null | Item lifetime in ticks (null = permanent) |
| `cooldown` | int \| null | null | Ticks before can respawn after despawn (null = no cooldown) |

### Field Reference: Catalog Global

| Field | Type | Default | Constraints | Description |
|-------|------|---------|-------------|-------------|
| `max_items_per_agent` | int | 3 | 1-10 | Inventory capacity per agent |
| `max_items_in_world` | int | 10 | 1-1000 | Max items that can exist simultaneously |

### Validation Rules

1. **Unique IDs**: Item type IDs must be unique within catalog
2. **Lowercase IDs**: Item IDs must be lowercase alphanumeric + underscores
3. **VFS Profile Exists**: `vfs_profile` must reference existing item-scoped profile
4. **Duration Positive**: `duration` must be >= 1 if specified
5. **Cooldown Non-Negative**: `cooldown` must be >= 0 if specified

---

## Appearance Configuration

### Items Appearance Schema

```yaml
version: "1.0"

items:
  - item_type: "apple"
    spawn_count: 3          # Spawn 3 apples at level start
    spawn_interval: 100     # Respawn every 100 ticks
    spawn_position: random

  - item_type: "medkit"
    spawn_count: 1
    spawn_interval: 200
    spawn_position: random

  - item_type: "coin"
    spawn_count: 5
    spawn_interval: null    # Only spawn at level start, no respawn
    spawn_position: random
```

### Field Reference: Appearance Rule

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `item_type` | string | (required) | Item type ID from catalog |
| `spawn_count` | int | 1 | Number to spawn at level start (0 = don't spawn) |
| `spawn_interval` | int \| null | null | Ticks between respawns (null = no periodic respawn) |
| `spawn_position` | enum | random | Position strategy: `random` or `fixed` |
| `when` | string \| null | null | Boolean expression gating spawn (e.g., `bar.energy > 0.5`) |

### Validation Rules

1. **Item Type Exists**: `item_type` must reference existing catalog item
2. **Spawn Count Non-Negative**: `spawn_count` must be >= 0
3. **Spawn Interval Positive**: `spawn_interval` must be >= 1 if specified
4. **Condition is Boolean**: `when` must type-check to bool against bars/VFS/temporal schema (temporal symbols only when temporal mechanics enabled)

### Spawn Condition Examples

```yaml
# Weather-dependent spawn
items:
  - item_type: "rain_boots"
    spawn_count: 2
    spawn_position: random
    spawn_interval: 50
    when: "vfs.is_raining"

# Time-gated spawn (requires temporal mechanics enabled)
  - item_type: "night_flower"
    spawn_count: 1
    spawn_position: random
    when: "temporal.tick % 1000 > 500"  # Only after halfway through the day

# State-based gate with boolean logic
  - item_type: "health_potion"
    spawn_count: 3
    spawn_interval: 25
    spawn_position: random
    when: "(bar.energy < 0.4) and vfs.danger_level >= 3"
```

Supported symbols: `bar.<meter>`, `vfs.<variable>`, `temporal.tick` (only when temporal mechanics are enabled). All standard comparison operators and boolean logic (`and`, `or`, `not`) are available via the expression language.

---

## Catalog vs Appearance Separation

### Why Separate?

**Catalog** (Experiment-Level):
- Defines item types ONCE for entire experiment
- Contains VFS profiles, interactions, lifecycle properties
- Shared across all curriculum levels
- Enables consistent item behavior

**Appearance** (Level-Specific):
- Defines spawn rules PER LEVEL
- Contains spawn counts, intervals, positions
- Enables curriculum progression (L0: 1 apple, L1: 10 apples)
- Avoids duplicating item definitions

### Example: Curriculum Progression

**Catalog** (`configs/my_experiment/items.yaml`):
```yaml
items:
  version: "1.0"
  item_types:
    - id: "apple"
      vfs_profile: "food"
      interactions:
        on_use:
          - modify: "target.bar.energy"
            value: "target.bar.energy + 0.3"
  # ... other settings
```

**L0 Appearance** (`configs/my_experiment/levels/L0_minimal/items.yaml`):
```yaml
version: "1.0"
items:
  - item_type: "apple"
    spawn_count: 1          # Sparse resources (hard)
    spawn_interval: null
```

**L1 Appearance** (`configs/my_experiment/levels/L1_abundant/items.yaml`):
```yaml
version: "1.0"
items:
  - item_type: "apple"
    spawn_count: 10         # Abundant resources (easy)
    spawn_interval: 50      # Frequent respawns
```

Same item type, different difficulty tuning per level.

---

## Interactions

All item interactions use Effects command language. Commands are compiled at Universe Compiler stage and executed by CommandExecutor.

### Interaction Types

#### on_pickup
**Trigger**: When item picked up via GET action (added to inventory)
**Context**: `target` = agent performing pickup, `self` = item instance
**Use Cases**: Auto-consume on pickup (coins), record pickup (quests)

#### on_use
**Trigger**: When USE_SLOT_N action executed on inventory slot
**Context**: `target` = agent using item, `self` = item instance
**Use Cases**: Consume item (food), degrade durability (tools), activate effects

#### on_drop
**Trigger**: When DROP_SLOT_N action executed on inventory slot
**Context**: `target` = agent dropping item, `self` = item instance
**Use Cases**: Apply penalty (fragile items), trigger trap, leave marker

### Context Mapping

When Effects execute during item interactions:

- **`target`**: Agent performing the action
  - Can access `target.bar.*` (agent meters)
  - Can access `target.vfs.*` (agent VFS variables)

- **`self`**: Item instance
  - Can access `self.vfs.*` (item VFS variables like durability)
  - Cannot access `self.bar.*` (items don't have meters)

### Effects Command Reference

Items support all Effects commands:

**modify**: Mutate bar or VFS variable
```yaml
- modify: "target.bar.energy"
  value: "target.bar.energy + 0.3"

- modify: "self.vfs.durability"
  value: "self.vfs.durability - 10"
```

**spawn_effect**: Spawn persistent effect on agent
```yaml
- spawn_effect:
    effect_id: "food_poisoning"
    target: "self"        # Spawn on agent
    duration: 100
    intensity: 1.0
```

**spawn_item**: Spawn new item instance (e.g., broken tool drops scrap)
```yaml
- spawn_item:
    item_type: "scrap_metal"
    position: "target.position"
    duration: null
```

**if**: Conditional execution
```yaml
- if:
    condition: "self.vfs.durability > 0"
    then:
      - modify: "target.bar.health"
        value: "target.bar.health + 0.5"
    else:
      - spawn_effect:
          effect_id: "broken_item"
          target: "self"
```

See `docs/config-schemas/effects.md` for complete Effects command reference.

---

## VFS State

Items use VFS profiles to store persistent state. Each item instance has a unique VFS index into the item-scoped tensor `[max_items, num_item_profiles]`.

### VFS Profile Configuration

**Location**: `<config_pack>/vfs_profiles.yaml`

```yaml
item_profiles:
  - id: "durability"
    scope: item
    type: scalar
    initial_value: 100.0
    description: "Item durability (100.0 = pristine, 0.0 = broken)"
    normalization:
      kind: minmax
      min: 0.0
      max: 100.0

  - id: "quality"
    scope: item
    type: scalar
    initial_value: 1.0
    description: "Item quality multiplier (affects effectiveness)"
    normalization:
      kind: minmax
      min: 0.0
      max: 1.0

  - id: "charges"
    scope: item
    type: scalar
    initial_value: 3.0
    description: "Number of uses remaining"
    normalization:
      kind: minmax
      min: 0.0
      max: 10.0
```

### Accessing Item State

**In item interactions** (on_pickup, on_use, on_drop):
```yaml
# Read item state
- if:
    condition: "self.vfs.durability > 0"
    then:
      - modify: "target.bar.health"
        value: "target.bar.health + 0.5"

# Modify item state
- modify: "self.vfs.durability"
  value: "self.vfs.durability - 10"

- modify: "self.vfs.charges"
  value: "self.vfs.charges - 1"
```

**Item state persists** across:
- Pickup → Use → Use → Drop → Pickup (same instance)
- Duration ticks (item ages while held)
- Inventory transitions (active ↔ held)

**Item state resets** when:
- Item despawns (duration expires)
- Item respawns (new instance)

### VFS Profile Mapping

Each item type specifies a `vfs_profile` field:

```yaml
item_types:
  - id: "torch"
    vfs_profile: "durable"    # References item_profiles in vfs_profiles.yaml
```

**Multiple items can share profiles**:
```yaml
item_types:
  - id: "torch"
    vfs_profile: "durable"    # Uses durability profile
  - id: "hammer"
    vfs_profile: "durable"    # Uses same profile (different instances)
  - id: "apple"
    vfs_profile: "consumable" # Uses different profile
```

---

## Lifecycle

### Spawning

**Initial Spawn** (level start):
- ItemManager.spawn_initial_items() reads appearance config
- Spawns `spawn_count` items per type at random positions
- Allocates VFS slot, initializes VFS variables to defaults
- Item added to `active_items` registry

**Periodic Respawn** (during episode):
- When item despawns, timer set to `spawn_interval` ticks
- ItemManager.process_respawns() checks timers each tick
- Attempts spawn when timer expires
- Respawn may fail if at capacity or on cooldown

### Duration

Items can be **permanent** (duration = null) or **temporary** (duration = int).

**Permanent Items**:
```yaml
- id: "gold_coin"
  duration: null    # Never expires
```
- Item persists until picked up and consumed
- Useful for collectibles, permanent resources

**Temporary Items**:
```yaml
- id: "fresh_bread"
  duration: 100     # Despawns after 100 ticks
```
- Item despawns after `duration` ticks (age tracked even when held)
- Useful for spoilable food, timed powerups
- Duration counts down each tick (active AND held)

### Cooldown

After despawn, item type may have cooldown before respawning:

```yaml
- id: "rare_gem"
  cooldown: 200     # Can't spawn for 200 ticks after despawn
```

**Cooldown prevents**:
- Immediate respawn after pickup (prevents farming)
- Spawn flooding (multiple items despawn → all try to respawn)

**Cooldown tracking**:
- Per item TYPE (not per instance)
- If 3 "rare_gem" instances despawn, only most recent sets cooldown

### Despawning

Items despawn when:
1. **Duration expires** (ItemManager.tick() checks duration_remaining)
2. **Consumed by interaction** (e.g., on_use reduces charges to 0, then effects can spawn_item to remove)
3. **Manually despawned** (ItemManager.despawn_item())

**Despawn process**:
1. Remove from `active_items` or `held_items` registry
2. Free VFS slot (added back to `vfs_free_slots`)
3. Set cooldown timer if configured
4. Set respawn timer if `spawn_interval` configured

---

## Inventory Management

### Fixed-Size Inventories

Each agent has fixed inventory capacity:

```yaml
max_items_per_agent: 3    # Each agent can hold 3 items
```

**Storage**: GPU tensor `[batch_size, max_items_per_agent]` with instance IDs
- Value -1 = empty slot
- Value >= 0 = instance_id of held item

### Actions

**GET**: Pick up item at agent's position
- Finds item at `agent.position`
- Adds to first empty inventory slot
- Fails if inventory full (DENY_PICKUP policy)
- Executes `on_pickup` Effects
- Item moved from world (`active_items`) to held state (`held_items`)

**USE_SLOT_N**: Use item in slot N
- N = 0, 1, 2, ... (zero-indexed)
- Executes `on_use` Effects
- Item remains in inventory (unless Effects despawn it)
- Fails if slot empty

**DROP_SLOT_N**: Drop item from slot N
- Removes from inventory slot
- Executes `on_drop` Effects
- Places item at agent's position
- Fails if slot empty

### DENY_PICKUP Policy

When inventory full, GET action fails:
- No pickup
- No `on_pickup` Effects execute
- Item remains on ground

**Pedagogical Value**: Teaches inventory management, opportunity cost

---

## Complete Examples

### 1. Consumable (Food)

**Catalog**:
```yaml
- id: "apple"
  vfs_profile: "food"
  description: "Fresh apple, restores energy"
  duration: null        # Permanent until consumed
  cooldown: null
  interactions:
    on_pickup: []       # No effect on pickup
    on_use:
      - modify: "target.bar.energy"
        value: "target.bar.energy + 0.3"
      # Note: To actually remove from inventory, need custom consume logic
      # Phase 1-3: Items remain in inventory after use
    on_drop: []
```

**Appearance**:
```yaml
- item_type: "apple"
  spawn_count: 5
  spawn_interval: 100   # Respawn every 100 ticks
  spawn_position: random
```

**VFS Profile** (vfs_profiles.yaml):
```yaml
item_profiles:
  - id: "food"
    scope: item
    type: scalar
    initial_value: 1.0
    description: "Food freshness (1.0 = fresh, 0.0 = spoiled)"
```

---

### 2. Durable (Tool)

**Catalog**:
```yaml
- id: "torch"
  vfs_profile: "durable"
  description: "Light source, degrades with use"
  duration: 200         # Burns out after 200 ticks
  cooldown: 50
  interactions:
    on_pickup: []
    on_use:
      - modify: "self.vfs.durability"
        value: "self.vfs.durability - 5"
      - modify: "target.bar.mood"
        value: "target.bar.mood + 0.1"  # Light improves mood
      - if:
          condition: "self.vfs.durability <= 0"
          then:
            - spawn_effect:
                effect_id: "darkness"
                target: "self"
                duration: 50
                intensity: 1.0
    on_drop: []
```

**Appearance**:
```yaml
- item_type: "torch"
  spawn_count: 2
  spawn_interval: null  # Don't respawn (limited resource)
  spawn_position: random
```

**VFS Profile**:
```yaml
item_profiles:
  - id: "durable"
    scope: item
    type: scalar
    initial_value: 100.0
    description: "Item durability"
    normalization:
      kind: minmax
      min: 0.0
      max: 100.0
```

---

### 3. Collectible (Currency)

**Catalog**:
```yaml
- id: "coin"
  vfs_profile: "currency"
  description: "Gold coin, adds money on pickup"
  duration: null        # Permanent
  cooldown: null
  interactions:
    on_pickup:
      - modify: "target.bar.money"
        value: "target.bar.money + 0.1"  # Add 10 currency units
    on_use: []          # No use action (consumed on pickup)
    on_drop: []
```

**Appearance**:
```yaml
- item_type: "coin"
  spawn_count: 10
  spawn_interval: 50    # Respawn every 50 ticks
  spawn_position: random
```

**VFS Profile**:
```yaml
item_profiles:
  - id: "currency"
    scope: item
    type: scalar
    initial_value: 1.0
    description: "Coin value multiplier (for different denominations)"
```

---

### 4. Medical (Healing)

**Catalog**:
```yaml
- id: "medkit"
  vfs_profile: "medical"
  description: "Medical kit with limited charges"
  duration: 100         # Expires after 100 ticks
  cooldown: 50
  interactions:
    on_pickup: []
    on_use:
      - if:
          condition: "self.vfs.charges > 0"
          then:
            - modify: "target.bar.health"
              value: "target.bar.health + 0.5"
            - modify: "self.vfs.charges"
              value: "self.vfs.charges - 1"
          else:
            - spawn_effect:
                effect_id: "empty_medkit"
                target: "self"
                duration: 10
                intensity: 1.0
    on_drop: []
```

**Appearance**:
```yaml
- item_type: "medkit"
  spawn_count: 1
  spawn_interval: 200
  spawn_position: random
```

**VFS Profile**:
```yaml
item_profiles:
  - id: "medical"
    scope: item
    type: scalar
    initial_value: 3.0
    description: "Number of charges (uses) remaining"
    normalization:
      kind: minmax
      min: 0.0
      max: 5.0
```

---

### 5. Spoilable (Perishable Food)

**Catalog**:
```yaml
- id: "fresh_bread"
  vfs_profile: "perishable"
  description: "Fresh bread, spoils over time"
  duration: 50          # Spoils after 50 ticks
  cooldown: null
  interactions:
    on_pickup: []
    on_use:
      - if:
          condition: "self.vfs.freshness > 0.5"
          then:
            - modify: "target.bar.satiation"
              value: "target.bar.satiation + 0.4"
            - modify: "target.bar.mood"
              value: "target.bar.mood + 0.1"  # Fresh bread tastes good
          else:
            - modify: "target.bar.satiation"
              value: "target.bar.satiation + 0.2"  # Less filling when stale
            - modify: "target.bar.health"
              value: "target.bar.health - 0.1"  # Spoiled food hurts health
      - modify: "self.vfs.freshness"
        value: "self.vfs.freshness - 0.2"  # Degrades with each use
    on_drop: []
```

**Appearance**:
```yaml
- item_type: "fresh_bread"
  spawn_count: 3
  spawn_interval: 75
  spawn_position: random
```

**VFS Profile**:
```yaml
item_profiles:
  - id: "perishable"
    scope: item
    type: scalar
    initial_value: 1.0
    description: "Freshness level (1.0 = fresh, 0.0 = spoiled)"
    normalization:
      kind: minmax
      min: 0.0
      max: 1.0
```

---

## Integration with Other Systems

### VFS Integration

**Item-scoped variables** stored in VFS registry:
- Tensor shape: `[max_items, num_item_profiles]`
- Each item instance has unique `vfs_index`
- VFS slot allocated on spawn, freed on despawn
- State persists across inventory transitions

**Access control**:
- Items can read/write their own VFS variables via `self.vfs.*`
- Agents can read item VFS variables when interacting (future: for observation)

### Effects Integration

**Items use Effects for ALL interactions**:
- `on_pickup`: Effects executed when GET succeeds
- `on_use`: Effects executed when USE_SLOT_N succeeds
- `on_drop`: Effects executed when DROP_SLOT_N succeeds

**Compilation**: ItemManager compiles Effects at initialization using CommandCompiler
**Execution**: ItemActionHandler executes via CommandExecutor with ExecutionContext

### Action Space Integration

**Items add 3 action types**:
- `GET`: Pickup item at position (global action)
- `USE_SLOT_N`: Use item in slot N (per-slot action)
- `DROP_SLOT_N`: Drop item from slot N (per-slot action)

**Example**: With `max_items_per_agent: 3`:
- Action space adds: `GET`, `USE_SLOT_0`, `USE_SLOT_1`, `USE_SLOT_2`, `DROP_SLOT_0`, `DROP_SLOT_1`, `DROP_SLOT_2`
- Total: 7 item-related actions

---

## Common Patterns

### Pattern: Auto-Consume on Pickup

**Use Case**: Coins, quest items that auto-consume
```yaml
- id: "coin"
  interactions:
    on_pickup:
      - modify: "target.bar.money"
        value: "target.bar.money + 0.1"
    on_use: []    # No use action needed
```

### Pattern: Durability Degradation

**Use Case**: Tools, weapons, armor
```yaml
- id: "pickaxe"
  interactions:
    on_use:
      - modify: "self.vfs.durability"
        value: "self.vfs.durability - 5"
      - if:
          condition: "self.vfs.durability > 0"
          then:
            - modify: "target.bar.resources"
              value: "target.bar.resources + 0.1"
```

### Pattern: Charge Consumption

**Use Case**: Batteries, medical kits, scrolls
```yaml
- id: "battery"
  interactions:
    on_use:
      - if:
          condition: "self.vfs.charges > 0"
          then:
            - spawn_effect:
                effect_id: "powered"
                target: "self"
                duration: 100
            - modify: "self.vfs.charges"
              value: "self.vfs.charges - 1"
```

### Pattern: Quality-Based Effects

**Use Case**: High-quality items more effective
```yaml
- id: "potion"
  interactions:
    on_use:
      - modify: "target.bar.health"
        value: "target.bar.health + (0.3 * self.vfs.quality)"
      # Quality 1.0 = +0.3, Quality 0.5 = +0.15
```

### Pattern: Temporary Spawn with No Respawn

**Use Case**: One-time pickups, quest items
```yaml
# Appearance config
- item_type: "quest_key"
  spawn_count: 1
  spawn_interval: null    # Never respawns
  spawn_position: random
```

---

## Validation

### Compile-Time Validation

**Universe Compiler validates**:
1. Item type IDs unique
2. VFS profiles exist (item scope)
3. Effects commands well-formed
4. Appearance references existing item types

**Validation failures**:
- Duplicate item IDs → Error
- Missing VFS profile → Error
- Invalid Effects command → Error
- Appearance references unknown item type → Warning (skipped at runtime)

### Runtime Validation

**ItemManager enforces**:
1. Max items in world (capacity limit)
2. Max items per agent (inventory limit)
3. Cooldown periods (prevent spam spawning)
4. VFS slot allocation (finite pool)

**Validation failures**:
- Spawn at capacity → Returns None (silent failure)
- Pickup with full inventory → Returns False (DENY_PICKUP)
- Use empty slot → Returns False (no-op)

---

## Performance Considerations

### VFS Slot Pool

**Fixed-size allocation**:
- Pre-allocate `max_items_in_world` VFS slots
- Slot recycling on despawn
- O(1) allocation/deallocation using free set

**Recommendation**: Set `max_items_in_world` >= (num_item_types × spawn_count)

### Held Items Tick

**Both active AND held items tick**:
- Active items: On grid, visible
- Held items: In inventories, not visible
- Both age (duration_remaining decreases)

**Pedagogical Value**: Food spoils even when carried

### Respawn Timers

**Per-type timers**:
- Only one respawn timer per item type
- Multiple despawns → most recent sets timer
- O(num_item_types) timer checks per tick

---

## Migration from Legacy

**Phase 1-3 Limitations**:
- No custom item commands (only Effects: modify, spawn_effect, spawn_item, if)
- No fixed spawn positions (only random)
- Items don't auto-consume on use (require explicit Effects to remove)
- No item-to-item interactions
- No item observations (agents can't see what's in inventory via obs)

**Future Phases**:
- Item observations (inventory composition visible)
- Crafting system (combine items)
- Item-to-item effects (poison apple damages nearby food)
- Fixed spawn positions
- Item wear/repair system
- Item rarity/quality on spawn

---

## See Also

- **Effects Language**: `docs/config-schemas/effects.md` - Effects command reference
- **VFS Variables**: `docs/config-schemas/variables.md` - VFS profile configuration
- **Action Space**: `docs/config-schemas/enabled_actions.md` - Action space configuration
- **Implementation**: `src/townlet/items/` - Items system source code
- **Tests**: `tests/test_townlet/unit/items/` - Items unit tests
