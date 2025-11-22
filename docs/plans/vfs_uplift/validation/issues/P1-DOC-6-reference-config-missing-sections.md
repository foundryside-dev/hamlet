# P1-DOC-6: Reference Config Missing VFS Profiles and Items Sections

**Priority:** P1 (Important - Should Fix)
**Category:** Documentation
**Estimated Effort:** 4 hours
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

The reference configuration documentation (`docs/config-schemas/reference-config.md` or similar) does not include comprehensive examples for `vfs_profiles.yaml` and `items.yaml`, making it difficult for users to understand the complete schema.

**Impact:**
- Users don't have a complete reference for all config files
- Missing examples for VFS profiles (global/agent/item)
- Missing examples for items catalog with VFS integration
- Gap in documentation completeness

**Evidence:**
- Agent 7 (Documentation) report, section DOC-6
- Existing reference configs in `configs/` lack vfs_profiles sections
- No centralized reference documentation showing all schemas together

---

## What's Missing

### 1. VFS Profiles Section

Reference config should document:
- `vfs_profiles.yaml` structure
- `global_profile` with expression-based variables
- `agent_profile` with per-agent state
- `item_profiles` with per-item-type VFS state
- Observation control (`observation: true/false`)
- Access control (readers/writers)

### 2. Items Catalog Section

Reference config should document:
- `items.yaml` structure
- Item types with `vfs_profile` references
- Inventory configuration
- Spawn rules (placement, schedule, conditions)
- Interaction effects (on_pickup, on_use, on_drop)
- Lifecycle parameters (duration, cooldown)

---

## How to Fix

### Step 1: Create Comprehensive Reference Config (2 hours)

**File:** `docs/config-schemas/reference-config-complete.md` (NEW)

```markdown
# Complete HAMLET Configuration Reference

This document shows all configuration files for a complete HAMLET experiment.

## Directory Structure

```
configs/my_experiment/
├── vfs_profiles.yaml         # VFS variable definitions (experiment-level)
├── effects.yaml               # Effect catalog (experiment-level)
├── items.yaml                 # Item catalog (experiment-level)
└── levels/
    └── L1_example/
        ├── substrate.yaml     # Spatial substrate
        ├── bars.yaml          # Meters
        ├── affordances.yaml   # Interactions
        ├── training.yaml      # Hyperparameters
        └── enabled_actions.yaml
```

## VFS Profiles (`vfs_profiles.yaml`)

```yaml
version: "2.1"

# Global variables (shared across all agents)
global_profile:
  time_of_day:
    expression: "(step % 24) / 24.0"
    observation: true
    semantic_type: temporal

  day_of_week:
    expression: "((step // 24) % 7) / 7.0"
    observation: true
    semantic_type: temporal

# Per-agent variables
agent_profile:
  energy_efficiency:
    expression: "self.bar.energy / self.bar.max_energy"
    observation: true
    semantic_type: derived

  health_status:
    expression: "if self.bar.health > 0.8 then 1.0 else 0.0"
    observation: true
    semantic_type: categorical

# Per-item-type VFS profiles
item_profiles:
  sword:
    durability:
      initial_value: 1.0
      observation: true
      semantic_type: resource
    sharpness:
      initial_value: 2.0
      observation: true
      semantic_type: attribute

  potion:
    remaining_doses:
      initial_value: 3.0
      observation: true
      semantic_type: count
```

## Items Catalog (`items.yaml`)

```yaml
version: "2.1"

# Inventory configuration
inventory:
  max_items_per_agent: 5

# Item type definitions
item_types:
  sword:
    vfs_profile: "sword"  # References item_profiles.sword above
    lifecycle:
      duration: null        # Persistent (doesn't decay)
      cooldown: 0

    spawn_rules:
      placement:
        strategy: random
        max_count: 10
      schedule:
        type: poisson
        rate: 0.1

    interaction_effects:
      on_pickup:
        - effect: equip_weapon
          target: self
      on_use:
        - effect: attack
          target: nearest_enemy
      on_drop:
        - effect: unequip_weapon
          target: self

  potion:
    vfs_profile: "potion"
    lifecycle:
      duration: 100       # Decays after 100 steps
      cooldown: 10

    spawn_rules:
      placement:
        strategy: grid
        positions: [[2, 2], [7, 7]]
        max_count: 5
      schedule:
        type: fixed_interval
        interval: 50
        offset: 0

    interaction_effects:
      on_use:
        - effect: heal
          target: self
        - effect: decrement_doses  # Modifies item.vfs.remaining_doses
          target: item
```

## Effects (`effects.yaml`)

[... existing effects reference ...]

## Substrate (`substrate.yaml`)

[... existing substrate reference ...]

## Bars (`bars.yaml`)

[... existing bars reference ...]

## Affordances (`affordances.yaml`)

[... existing affordances reference ...]

## Training (`training.yaml`)

[... existing training reference ...]
```

### Step 2: Add Examples to Existing Schema Docs (1 hour)

**File:** `docs/config-schemas/vfs-profiles.md`

Add "Complete Example" section at end:

```markdown
## Complete Example

See [reference-config-complete.md](./reference-config-complete.md) for a full example showing `vfs_profiles.yaml` in context with items, effects, and other config files.
```

**File:** `docs/config-schemas/items.md`

Add similar cross-reference.

### Step 3: Update README or Getting Started Guide (1 hour)

**File:** `docs/guides/getting-started.md` or `README.md`

Add section:

```markdown
## Configuration Files Overview

HAMLET experiments are configured via YAML files:

- **Experiment-level** (shared across curriculum):
  - `vfs_profiles.yaml` - Variable definitions
  - `effects.yaml` - Effect catalog
  - `items.yaml` - Item catalog

- **Level-specific** (per curriculum level):
  - `substrate.yaml` - Spatial environment
  - `bars.yaml` - Agent meters
  - `affordances.yaml` - Interactions
  - `training.yaml` - Hyperparameters

See [Complete Configuration Reference](./docs/config-schemas/reference-config-complete.md) for full example.
```

---

## Acceptance Criteria

- [ ] `docs/config-schemas/reference-config-complete.md` created
- [ ] Shows all 8+ config files with realistic examples
- [ ] VFS profiles section complete (global/agent/item profiles)
- [ ] Items section complete (with vfs_profile references)
- [ ] Cross-references added to schema docs
- [ ] Getting started guide updated with config file overview

---

## Files to Create/Modify

1. `docs/config-schemas/reference-config-complete.md` (NEW) - Complete reference
2. `docs/config-schemas/vfs-profiles.md` - Add cross-reference
3. `docs/config-schemas/items.md` - Add cross-reference
4. `docs/guides/getting-started.md` - Add config overview section
5. `README.md` (optional) - Link to reference config

---

## Related Issues

- Related: P1-DOC-8 (VFS integration guide outdated)
- Related: P1-DOC-10 (observation modes not documented)

---

## Notes

- Use realistic examples from actual curriculum levels (L1, L2, L3)
- Ensure consistency with existing schema docs
- Include comments explaining WHY certain fields are set
- Cross-reference between experiment-level and level-specific configs
