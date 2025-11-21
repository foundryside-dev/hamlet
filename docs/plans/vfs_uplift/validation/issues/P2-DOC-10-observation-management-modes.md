# [DOC-10] Observation Management Modes Documentation

**Priority:** P2 (Minor)
**Category:** Documentation
**Status:** PARTIAL
**Effort:** 2 hours

## Description

Observation management modes (full_auto, max_compact, full_manual) are documented in implementation plans but not in schema documentation. Developers looking at config files don't have clear reference for how observation slots are allocated and managed. Need schema documentation for observation configuration.

## Current State

**Existing documentation (in plans):**
- Observation modes described in VFS uplift plans
- Implementation notes in `observation_builder.py`
- Modes referenced but not formally documented

**Modes (from implementation):**
1. **full_auto:** Automatic slot allocation, no manual configuration
2. **max_compact:** Minimize observation dimension (efficient packing)
3. **full_manual:** Explicit slot configuration by user

**Missing:**
- Schema documentation in `docs/config-schemas/`
- Configuration examples for each mode
- Trade-offs and use cases for each mode
- Integration with VFS profiles and transfer learning

## Required Implementation

### Add Observation Configuration Documentation (2 hours)

**File:** `docs/config-schemas/observations.md` (new)

**Content:**
```markdown
# Observation Configuration

This document describes HAMLET's observation management system, including slot allocation strategies and configuration options.

---

## Overview

**Observations** are the agent's view of the environment state. HAMLET uses a **fixed-size observation vector** to enable transfer learning across curriculum levels.

**Key Principles:**
1. **Fixed vocabulary:** All levels observe same features (bars, affordances, VFS variables)
2. **Fixed dimensions:** Observation size constant across grid sizes, agent counts
3. **Slot allocation:** Features mapped to fixed slots in observation vector
4. **Transfer learning:** Agent trained on L0 can transfer to L1 (same obs structure)

---

## Observation Components

**Full observation vector includes:**
- **Agent position:** 2D coordinates (relative/scaled/absolute encoding)
- **Bars:** 8 meter values (energy, health, satiation, hygiene, money, mood, social, fitness)
- **Affordances:** 15 affordance features (distance, availability for each affordance type)
- **VFS variables:** Global, agent, and item variables (flattened)
- **Temporal state:** 4 temporal features (hour, day_phase, tick, normalized_time)
- **POMDP window:** 5×5 local observation window (for partial observability)
- **Effects (optional):** Active effects on agent (5 slots × 3 dims)

**Example observation dimensions:**
- L0_0_minimal (full obs): 29 dims
- L2_partial_observability (POMDP): 54 dims (includes 5×5 window)
- With VFS (10 vars): 29 + 10 = 39 dims
- With effects (5 slots): 39 + 15 = 54 dims

---

## Observation Management Modes

### Mode 1: full_auto (Default)

**Automatic slot allocation** - System determines slot layout based on features.

**Behavior:**
- ObservationBuilder automatically allocates slots
- Slot order: position → bars → affordances → VFS → temporal → POMDP → effects
- No manual configuration required
- Slot assignments deterministic (same config = same slots)

**Use case:** ✅ **Recommended for most users** - Minimal configuration, maximum convenience

**Configuration:**
\```yaml
# substrate.yaml (or observation_config.yaml)
observations:
  mode: full_auto  # Default
\```

**Pros:**
- Zero configuration overhead
- Automatic feature detection
- Deterministic slot allocation

**Cons:**
- Less control over slot layout
- Cannot manually optimize for specific hardware

---

### Mode 2: max_compact (Optimization)

**Compact slot allocation** - Minimize observation dimension through efficient packing.

**Behavior:**
- Remove unused feature slots (e.g., affordances not in this level)
- Pack VFS variables densely (no gaps)
- Merge redundant features
- Optimize for minimal observation size

**Use case:** ⚠️ **Advanced users** - Breaks transfer learning, use when obs size is bottleneck

**Configuration:**
\```yaml
observations:
  mode: max_compact
  pack_strategy: "dense"  # Options: dense, sparse
\```

**Pros:**
- Smaller observation dimension
- Reduced memory usage
- Faster network forward pass

**Cons:**
- **Breaks transfer learning** (different levels have different obs dims)
- Manual config required for transfer
- More complex debugging

**Warning:** Only use max_compact when observation dimension is performance bottleneck (>500 dims).

---

### Mode 3: full_manual (Expert)

**Manual slot configuration** - User explicitly defines slot layout.

**Behavior:**
- User specifies exact slot positions for each feature
- Allows custom observation layouts
- Full control over slot allocation
- Requires deep understanding of observation structure

**Use case:** 🔧 **Expert users only** - Custom observation layouts, research experiments

**Configuration:**
\```yaml
observations:
  mode: full_manual
  layout:
    position: {start: 0, size: 2}  # Slots 0-1: position (x, y)
    bars: {start: 2, size: 8}       # Slots 2-9: 8 bars
    affordances: {start: 10, size: 15}  # Slots 10-24: 15 affordances
    vfs_global: {start: 25, size: 5}    # Slots 25-29: 5 global VFS vars
    vfs_agent: {start: 30, size: 10}    # Slots 30-39: 10 agent VFS vars
    temporal: {start: 40, size: 4}      # Slots 40-43: 4 temporal features
    # Total: 44 dims
\```

**Pros:**
- Full control over observation layout
- Can optimize for specific use cases
- Explicit slot assignments (no surprises)

**Cons:**
- High configuration overhead
- Easy to make mistakes (overlapping slots)
- Must update manually when features change
- **Not recommended** unless absolutely necessary

---

## Fixed Vocabulary Pattern

**HAMLET uses fixed vocabulary** for transfer learning:

**Problem:** If L0 observes 3 affordances and L1 observes 14 affordances, observation dimensions differ → cannot transfer checkpoint.

**Solution:** All levels observe same 15 affordance slots, even if not all deployed.

**Example:**
\```
L0_0_minimal (1 affordance):
  Affordance slots: [food_dist, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
  # Only food exists, other slots zero-filled

L1_full_observability (14 affordances):
  Affordance slots: [food_dist, bed_dist, shower_dist, ..., gym_dist, party_dist]
  # All 14 affordances present, last slot zero-filled

# Same observation dimension → checkpoint transfers L0 → L1 ✅
\```

**Applies to:**
- Affordances (15 slots - global vocabulary)
- VFS variables (fixed slots per profile)
- Bars (8 slots - always same bars)
- Actions (global action vocabulary)

---

## VFS Observation Integration

**VFS variables are flattened into observation vector:**

**Slot allocation:**
1. **Global variables:** All global VFS vars in deterministic order (sorted by name)
2. **Agent variables:** Agent's own VFS vars (exclude private variables)
3. **Item variables:** Nearby items' VFS vars (fixed slots, empty if no items)

**Example:**
\```yaml
# vfs_profiles.yaml
global_profile:
  variables:
    is_raining: {type: bool}      # Slot 0: global
    danger_level: {type: int}      # Slot 1: global

agent_profiles:
  player:
    variables:
      experience: {type: int}      # Slot 2: agent
      health_regen: {type: float}  # Slot 3: agent

item_profiles:
  consumable:
    variables:
      quality: {type: float}       # Slot 4: item (if item nearby)

# Observation includes 5 VFS dims: [is_raining, danger_level, experience, health_regen, quality]
# If no items nearby, quality slot = 0
\```

**Normalization:**
- VFS variables normalized according to `normalization` spec in profile
- Normalized values always in [0, 1] or [-1, 1] (z-score)
- Ensures gradients stay stable

---

## POMDP Integration

**Partial observability adds local window to observations:**

**Full observability (L0, L1, L3):**
- Agent sees entire grid (global view)
- Affordance observations: distance to all affordances
- Observation size: 29 dims (no local window)

**Partial observability (L2):**
- Agent sees only 5×5 local window (limited view)
- Local window: 25 cells (5×5) with affordance presence flags
- Observation size: 54 dims (includes 25-dim local window)

**Example:**
\```yaml
# substrate.yaml
pomdp:
  enabled: true
  vision_range: 2  # 5×5 window (2 cells in each direction)
\```

**Observation structure:**
\```
POMDP observations (54 dims):
  [0-24]:   5×5 local window (affordance presence per cell)
  [25-26]:  Agent position (normalized)
  [27-34]:  8 bars
  [35-49]:  15 affordance distances (from agent to nearest)
  [50-53]:  4 temporal features
\```

---

## Configuration Examples

### Example 1: Default (full_auto)

\```yaml
# substrate.yaml - No observation config needed
# System automatically allocates slots
\```

### Example 2: Compact (max_compact)

\```yaml
# observation_config.yaml
observations:
  mode: max_compact
  pack_strategy: dense
  exclude_unused_affordances: true
\```

### Example 3: Manual Layout (full_manual)

\```yaml
# observation_config.yaml
observations:
  mode: full_manual
  layout:
    position: {start: 0, size: 2}
    bars: {start: 2, size: 8}
    affordances: {start: 10, size: 15}
    vfs: {start: 25, size: 20}
    temporal: {start: 45, size: 4}
  total_dims: 49
\```

---

## Transfer Learning Guidelines

**To enable checkpoint transfer across levels:**

1. **Use full_auto mode** (default) - Ensures consistent slot allocation
2. **Use fixed vocabulary** - Same affordances, bars, VFS profiles across levels
3. **Same substrate type** - All levels use Grid2D (or same substrate)
4. **Same encoding mode** - All levels use "relative" encoding

**Example curriculum (transfer-compatible):**
\```
L0_0_minimal → L0_5_dual_resource → L1_full_observability
- All use Grid2D substrate
- All use relative encoding
- All use full_auto observation mode
- All use same 15 affordance vocabulary
- Checkpoint trained on L0 transfers to L1 ✅
\```

**Breaking transfer learning:**
- Changing substrate type (Grid2D → Continuous)
- Changing encoding mode (relative → absolute)
- Using max_compact (variable obs dims)
- Adding/removing bars or affordances from vocabulary

---

## Debugging Observations

**Check observation dimension:**
\```python
env = VectorizedHamletEnv(compiled_universe, num_agents=16)
print(f"Observation dimension: {env.observation_space.shape}")

obs = env.reset()
print(f"Actual observation shape: {obs.shape}")  # Should be [16, obs_dim]
\```

**Inspect observation components:**
\```python
obs_builder = env.obs_builder
print(f"Position dims: {obs_builder.position_start}:{obs_builder.position_end}")
print(f"Bars dims: {obs_builder.bars_start}:{obs_builder.bars_end}")
print(f"VFS dims: {obs_builder.vfs_start}:{obs_builder.vfs_end}")
\```

**Validate observations:**
\```python
assert not torch.isnan(obs).any(), "NaN in observations"
assert not torch.isinf(obs).any(), "Inf in observations"
assert obs.shape[1] == env.observation_space.shape[0], "Dimension mismatch"
\```

---

## FAQ

**Q: Why fixed vocabulary?**
A: Enables transfer learning. Agent trained on simple level can transfer to complex level with same observation structure.

**Q: When should I use max_compact?**
A: Only when observation dimension is performance bottleneck (>500 dims). Otherwise stick with full_auto.

**Q: Can I change observation mode mid-training?**
A: No. Changing mode changes observation dimension, breaking checkpoint compatibility.

**Q: How do I add custom observation features?**
A: Use VFS variables. Custom features can be computed via expressions and included in observations automatically.

**Q: What if I need variable-length observations?**
A: Use fixed-size slots with masking. Example: 5 item slots, mask unused slots with zeros.

---

## References

- Implementation: `src/townlet/vfs/observation_builder.py`
- VFS integration: `docs/config-schemas/variables.md`
- Transfer learning: `docs/guides/transfer-learning.md`
- POMDP: `docs/config-schemas/substrate.md` (POMDP section)
```

### Update Schema Documentation Cross-References (30 minutes)

**Files to update:**
- `docs/config-schemas/variables.md` - Add reference to observations.md
- `docs/config-schemas/substrate.md` - Add reference to observations.md (POMDP section)
- `docs/guides/vfs-integration-guide.md` - Reference observation modes

**Add to each file:**
```markdown
**See also:** [Observation Configuration](./observations.md) for observation slot allocation and management modes.
```

## Acceptance Criteria

- [ ] `docs/config-schemas/observations.md` created
- [ ] Observation management modes documented (full_auto, max_compact, full_manual)
- [ ] Configuration examples for each mode
- [ ] Trade-offs and use cases explained
- [ ] Fixed vocabulary pattern documented
- [ ] VFS observation integration explained
- [ ] POMDP integration documented
- [ ] Transfer learning guidelines included
- [ ] Debugging section with code examples
- [ ] FAQ section answers common questions
- [ ] Cross-references added to related schema docs
- [ ] Linked from documentation index

## Evidence

**Source Report:** gap-report-final.md (lines 71-94), gap-report-testing-docs.md
**Current state:** Observation modes documented in plans, not in schema docs

## Implementation Notes

**Why P2 (not P1/P0):** Observation system works correctly. This is about documentation discoverability. Users can figure out observation structure from code/plans, but dedicated schema doc would improve usability.

**Documentation Purpose:**
1. **Configuration reference:** How to configure observation modes
2. **Design explanation:** Why fixed vocabulary, how slot allocation works
3. **Transfer learning guide:** Enable checkpoint transfer across levels
4. **Debugging reference:** How to inspect and validate observations

**Key Concepts to Document:**
- **Fixed vocabulary:** Same features across all levels (transfer learning)
- **Slot allocation:** Deterministic mapping of features to observation slots
- **Management modes:** full_auto (default), max_compact (optimization), full_manual (expert)
- **VFS integration:** How VFS variables appear in observations
- **POMDP integration:** How local window adds to observation dimension

**Audience:**
- **Beginners:** Use full_auto (default), understand observation components
- **Intermediate:** Understand slot allocation, transfer learning
- **Advanced:** Use max_compact for optimization, understand trade-offs
- **Experts:** Use full_manual for custom layouts (rare)

**Documentation Structure:**
1. Overview (what are observations?)
2. Components (what's in the observation vector?)
3. Management modes (how to configure?)
4. Fixed vocabulary (transfer learning pattern)
5. VFS integration (how VFS variables appear)
6. POMDP integration (partial observability)
7. Examples (configuration for each mode)
8. Transfer learning guidelines
9. Debugging (how to inspect observations)
10. FAQ (common questions)

**Related Documentation:**
- `docs/config-schemas/variables.md` - VFS variables in observations
- `docs/config-schemas/substrate.md` - POMDP configuration
- `docs/guides/transfer-learning.md` - Checkpoint transfer patterns (if exists)

## References

- Documentation file: `docs/config-schemas/observations.md` (to be created)
- Implementation: `src/townlet/vfs/observation_builder.py`
- Related: VFS uplift plans (observation mode descriptions), transfer learning patterns
