# Phase 0 Decision Matrix: Items & VFS Profiles

**Purpose**: Pre-populate concrete options for each design question to accelerate Phase 0 execution
**Created**: 2025-11-19
**Target**: Resolve all 5 design blockers before Phase 1 start

---

## Decision Summary Table

| Question | Options | Recommended | Confidence | Impact |
|----------|---------|-------------|------------|--------|
| **Q1: File Layout** | 2-tier, 3-tier, 2-tier-ref | 2-tier | HIGH | Phase 1-3 |
| **Q2: Expression Scope** | Phase 1 static, Phase 2+ | Phase 2+ | MEDIUM | Phase 1-2 |
| **Q3: Observation Budget** | Fixed, proportional, dynamic | Proportional | MEDIUM | Phase 2 |
| **Q4: Interaction Granularity** | Pickup+command, GET-only | GET-only | HIGH | Phase 3 |
| **Q5: Performance Limits** | Conservative, moderate, aggressive | Moderate | LOW | Phase 3 |

---

## Q1: File Layout (2-tier vs 3-tier for Items Configuration)

### Context
Items need both **catalog** (item types, VFS profiles, interactions) and **appearance** (spawn rules, positions). Current codebase uses 2-tier pattern for affordances, bars, environment. Should items follow same pattern or introduce 3-tier?

### Options

#### Option A: **2-Tier Pattern** (experiment + level)
```
configs/experiment/
├── items.yaml          # Item catalog + VFS profiles
└── levels/L0/
    └── items.yaml      # Spawn rules (references catalog via type_id)
```

**Pros**:
- ✅ Consistent with affordances.yaml, bars.yaml pattern
- ✅ Familiar to existing config authors
- ✅ Simple mental model (catalog vs deployment)
- ✅ Minimal file count

**Cons**:
- ❌ Level-scoped items.yaml duplicates spawn rules if shared
- ❌ Type catalog mixed with spawn rules (some cognitive load)

**Precedent**: `affordances.yaml` (experiment-level definitions) + `affordances.yaml` (level-level deployment)

**Example** (current items_smoke):
```yaml
# configs/test/items_smoke/items.yaml (experiment-level)
item_types:
  - id: test_item
    name: "Test Item"
    vfs_profiles: [item_durability, item_uses_remaining]
    interactions:
      use:
        bars: [{name: energy, delta: 0.2}]

# configs/test/items_smoke/levels/L0_smoke/items.yaml (level-level)
inventory:
  max_items_per_agent: 3
spawn_rules:
  - type_id: test_item
    placement: {mode: fixed, positions: [[2.0, 2.0]]}
    schedule: {kind: once}
```

---

#### Option B: **3-Tier Pattern** (catalog + spawns + level)
```
configs/experiment/
├── items_catalog.yaml  # Item types only
├── items_spawns.yaml   # Shared spawn rules (optional)
└── levels/L0/
    └── items.yaml      # Level-specific overrides
```

**Pros**:
- ✅ Clear separation of concerns (types vs spawns)
- ✅ Shared spawn rules across levels (DRY)
- ✅ Scales better for complex experiments (100+ item types)

**Cons**:
- ❌ No precedent in current codebase (cognitive burden)
- ❌ More files to maintain (3 vs 2)
- ❌ Indirection (type → spawn rule → level override)

**Precedent**: **None** - would be first 3-tier pattern in HAMLET

---

#### Option C: **2-Tier with References** (experiment catalog + level refs)
```
configs/experiment/
├── items.yaml          # Item types + default spawn rules
└── levels/L0/
    └── items.yaml      # Inventory + spawn rule references
```

**Pros**:
- ✅ DRY for shared spawn rules (reference by ID)
- ✅ Still 2-tier (consistent with existing patterns)
- ✅ Flexible (levels can override spawn params)

**Cons**:
- ❌ Requires spawn rule ID system (added complexity)
- ❌ Two ways to define spawns (inline vs reference)

**Precedent**: Partial - VFS `vfs_profiles.yaml` uses ID references

---

### Recommendation: **Option A (2-Tier Pattern)**

**Rationale**:
1. **Consistency** with existing codebase (affordances, bars, environment all use 2-tier)
2. **Simplicity** for MVP (can refactor to 3-tier later if needed)
3. **Low migration cost** from items_smoke (already uses 2-tier)
4. **Proven pattern** - less risk than inventing 3-tier

**Implementation Note**: If spawn rule duplication becomes painful post-MVP, migrate to Option C (2-tier with references) rather than 3-tier (maintains consistency).

---

## Q2: Expression Language Scope (Phase 1 vs Phase 2+)

### Context
VFS profiles can have static values (`initial_value: 1.0`) or expression-based values (`expression: "energy * 0.5"`). Should Phase 1 support expressions, or defer to Phase 2+?

### Options

#### Option A: **Phase 1 Static-Only** (Recommended by plan)
```yaml
# Phase 1: Only initial_value allowed
item_profiles:
  - id: item_durability
    scope: item
    type: scalar
    initial_value: 1.0  # ✅ Static value
```

**Pros**:
- ✅ Simpler Phase 1 implementation (no expression evaluator)
- ✅ Clear phase boundary (static → expressions)
- ✅ Lower risk (expressions are complex, many edge cases)
- ✅ Enables smoke testing without expression engine

**Cons**:
- ❌ Limited expressiveness in Phase 1
- ❌ Config migration required for Phase 2 (static → expression)
- ❌ Cannot express derived variables early (e.g., `item_quality = item_durability * item_rarity`)

**Timeline**: Phase 1 (4-5 days), Phase 2 adds expressions (+3-4 days)

---

#### Option B: **Phase 1 with Minimal Expressions**
```yaml
# Phase 1: Support simple expressions (no conditionals, no loops)
item_profiles:
  - id: item_quality
    scope: item
    type: scalar
    expression: "item_durability * 0.5"  # ✅ Simple arithmetic
```

**Pros**:
- ✅ More expressive Phase 1 configs
- ✅ No config migration for Phase 2
- ✅ Early validation of expression system

**Cons**:
- ❌ Extends Phase 1 timeline (+2-3 days for expression evaluator)
- ❌ Complex edge cases (circular deps, undefined vars)
- ❌ Phase 1 becomes "Phase 1.5" (blurs boundaries)

**Timeline**: Phase 1 (6-8 days with expressions)

---

#### Option C: **Phase 1 with Literal Expressions**
```yaml
# Phase 1: Support literal-only expressions (no variable refs)
item_profiles:
  - id: item_durability
    scope: item
    type: scalar
    expression: "1.0 * 0.5"  # ✅ Compile-time constant
```

**Pros**:
- ✅ Expression syntax in Phase 1 (forwards-compatible)
- ✅ Simpler than full expressions (compile-time eval)
- ✅ No runtime evaluator required

**Cons**:
- ❌ Pointless (equivalent to `initial_value: 0.5`)
- ❌ Confusing to users ("why can't I reference variables?")

**Timeline**: Phase 1 (4-5 days, no real benefit)

---

### Recommendation: **Option A (Phase 1 Static-Only)**

**Rationale**:
1. **Risk mitigation**: Expressions are complex (parser, evaluator, circular dep detection, type checking)
2. **Phase boundary clarity**: Phase 1 = DTOs + Compiler, Phase 2 = VFS Engine + Expressions
3. **Incremental value**: items_smoke works fine with static values
4. **Precedent**: DAC modifiers use expressions, but they're Phase 4 complexity (not MVP)

**Migration Path**: Phase 2 adds `expression` field, static configs remain valid (backwards compatible).

---

## Q3: Observation Budget (Allocating 55 Dims Across Scopes)

### Context
Phase 1 worst-case: +55 dims (20 global + 20 agent + 15 item). How should these be allocated across scopes to balance flexibility vs safety?

### Current Limits (from validate_vfs_obs_dimensions.py)
- Max global profiles: 20
- Max agent profiles: 20
- Max item profiles (per type): 5
- Max items per agent: 3
- Total worst-case: 55 dims

### Options

#### Option A: **Fixed Allocation** (Current limits)
```
Global:  20 dims (fixed)
Agent:   20 dims (fixed)
Item:    15 dims (5 profiles × 3 slots, fixed)
Total:   55 dims worst-case
```

**Pros**:
- ✅ Already validated (Activity 1: worst-case = 148 dims, SAFE)
- ✅ Simple enforcement (hard limits in validation)
- ✅ Predictable obs_dim growth

**Cons**:
- ❌ Inflexible (can't trade global dims for item dims)
- ❌ May over-allocate to scopes that don't need it

**Risk**: LOW (mathematically proven safe)

---

#### Option B: **Proportional Allocation** (Scope-weighted)
```
Total budget: 55 dims
Allocation:
  - Global: 15 dims (27%)  # Reduced from 20
  - Agent:  20 dims (36%)  # Unchanged
  - Item:   20 dims (37%)  # Increased from 15
```

**Pros**:
- ✅ Balances scopes more evenly
- ✅ Higher item capacity (20 dims = 6-7 item profiles × 3 slots)
- ✅ Still safe (15+20+20 = 55 dims total)

**Cons**:
- ❌ Requires changing validated limits
- ❌ Global scope may be under-allocated for complex experiments

**Risk**: LOW (total unchanged, just redistributed)

---

#### Option C: **Dynamic Allocation** (Config-specified)
```yaml
# vfs_profiles.yaml
budget:
  total_max_dims: 55
  global_max: 25    # Config-specified
  agent_max: 15
  item_max: 15
```

**Pros**:
- ✅ Maximum flexibility (operators choose trade-offs)
- ✅ Can optimize per-experiment

**Cons**:
- ❌ Complex validation (must check total ≤ 55)
- ❌ Foot-gun (operators can misconfigure)
- ❌ Harder to reason about obs_dim stability

**Risk**: MEDIUM (validation complexity, user error)

---

### Recommendation: **Option B (Proportional Allocation)**

**Rationale**:
1. **Balanced**: Items likely need more dims than global state (item_durability, item_uses, item_rarity, item_quality, etc.)
2. **Safe**: Total still 55 dims, just redistributed
3. **Simple**: No dynamic config, just update Phase 1 limits

**Proposed Limits**:
```python
MAX_GLOBAL_PROFILES = 15  # Down from 20
MAX_AGENT_PROFILES = 20   # Unchanged
MAX_ITEM_PROFILES_PER_TYPE = 6  # Up from 5
MAX_ITEMS_PER_AGENT = 3   # Unchanged

# Total: 15 + 20 + (6×3) = 53 dims (2 dims safety margin)
```

**Re-validation Required**: Update `validate_vfs_obs_dimensions.py` with new limits.

---

## Q4: Interaction Granularity (Pickup vs GET Command)

### Context
Items need pickup/drop/use interactions. Should these be:
- **Generic commands** (GET, DROP_SLOT_N, USE_SLOT_N) that work for all items?
- **Item-specific actions** (PICKUP_SWORD, USE_SWORD) generated per item type?

### Options

#### Option A: **Generic GET/DROP/USE Commands** (Recommended)
```
Actions: [GET, DROP_SLOT_0, DROP_SLOT_1, DROP_SLOT_2, USE_SLOT_0, USE_SLOT_1, USE_SLOT_2]
Total:   7 new actions (3 slots)
```

**Pros**:
- ✅ Fixed action space size (7 actions regardless of item count)
- ✅ Simpler action masking (mask slots without items)
- ✅ Generalizes well (agents learn "use item" concept)
- ✅ Precedent: INTERACT is generic, not affordance-specific

**Cons**:
- ❌ Cannot have item-specific pickup logic (e.g., "sword requires strength")
- ❌ Agent must learn slot management (which slot has which item)

**Action Space Growth**: +7 actions (fixed)

---

#### Option B: **Item-Specific Actions**
```
Actions: [PICKUP_POTION, USE_POTION, DROP_POTION, PICKUP_SWORD, USE_SWORD, DROP_SWORD, ...]
Total:   3N actions (N = item types in universe)
```

**Pros**:
- ✅ Item-specific pickup logic (conditions, costs per item type)
- ✅ Explicit action names (easier to interpret policies)

**Cons**:
- ❌ Action space explosion (10 item types = 30 new actions)
- ❌ Breaks curriculum transfer (L0 with 1 item != L1 with 10 items)
- ❌ Harder action masking (mask per item type + inventory state)

**Action Space Growth**: +3N actions (unbounded)

---

#### Option C: **Hybrid** (Generic GET + Item-Specific USE)
```
Actions: [GET, DROP_SLOT_0, DROP_SLOT_1, DROP_SLOT_2, USE_POTION, USE_SWORD, ...]
Total:   4 + N actions (N = item types)
```

**Pros**:
- ✅ Generic pickup/drop (saves action space)
- ✅ Item-specific use (enables custom logic per item)

**Cons**:
- ❌ Asymmetric (pickup generic, use specific - confusing)
- ❌ Still action space growth (4+N actions)

**Action Space Growth**: +4+N actions

---

### Recommendation: **Option A (Generic GET/DROP/USE)**

**Rationale**:
1. **Fixed action space**: Critical for curriculum transfer (L0 → L1 checkpoint compatibility)
2. **Precedent**: INTERACT is generic, works with all affordances
3. **Simplicity**: 7 actions vs 30+ for 10 item types
4. **Pedagogical**: Forces agents to learn inventory management (slot tracking)

**Implementation**:
- `GET`: Pickup item at current position → first empty inventory slot
- `DROP_SLOT_N`: Drop item from slot N at current position
- `USE_SLOT_N`: Execute item's `interactions.use` effects, decrement uses_remaining

**Edge Case** (from edge-case-policies.md):
- GET when inventory full → DENY_PICKUP (masked in action space)
- USE_SLOT_N when slot empty → NO-OP (masked)

---

## Q5: Performance Limits (Spawn Frequency, Item Count)

### Context
Items add runtime overhead (spawn evaluation, item state updates, observation assembly). What performance limits should Phase 1 enforce?

### Existing Limits (from compiler.py)
```python
MAX_METERS = 100
MAX_AFFORDANCES = 100
MAX_CASCADES = 500
MAX_ACTIONS = 300
```

### Options

#### Option A: **Conservative Limits** (Safety-first)
```python
MAX_ITEM_TYPES = 10           # Per experiment
MAX_ITEMS_PER_AGENT = 3       # Inventory capacity
MAX_SIMULTANEOUS_ITEMS = 20   # Per level (across all agents)
MAX_SPAWNS_PER_EPISODE = 50   # Lifetime spawn budget
```

**Pros**:
- ✅ Low performance risk
- ✅ Forces operators to think about spawn budget
- ✅ Easy to profile and validate

**Cons**:
- ❌ May be too restrictive for complex scenarios
- ❌ Hard limit may frustrate operators

**Expected Overhead**: <5% frame time

---

#### Option B: **Moderate Limits** (Balanced)
```python
MAX_ITEM_TYPES = 20           # Per experiment
MAX_ITEMS_PER_AGENT = 5       # Inventory capacity
MAX_SIMULTANEOUS_ITEMS = 50   # Per level
MAX_SPAWNS_PER_EPISODE = 200  # Lifetime spawn budget
```

**Pros**:
- ✅ Room for complex experiments
- ✅ Still bounded (prevents runaway spawns)
- ✅ Aligns with MAX_AFFORDANCES = 100 precedent

**Cons**:
- ❌ Higher performance risk (needs profiling)
- ❌ More complex item state management

**Expected Overhead**: 5-10% frame time

---

#### Option C: **Aggressive Limits** (Performance-tested)
```python
MAX_ITEM_TYPES = 50           # Per experiment
MAX_ITEMS_PER_AGENT = 10      # Large inventory
MAX_SIMULTANEOUS_ITEMS = 100  # Per level
MAX_SPAWNS_PER_EPISODE = 500  # High spawn budget
```

**Pros**:
- ✅ Maximum flexibility
- ✅ Future-proof (won't need to raise limits)

**Cons**:
- ❌ High performance risk (may degrade frame rate)
- ❌ Complex state management (100 items × 10 profiles = 1000 obs dims)
- ❌ Requires extensive profiling

**Expected Overhead**: 10-20% frame time (RISKY)

---

### Recommendation: **Option B (Moderate Limits)**

**Rationale**:
1. **Precedent**: MAX_AFFORDANCES = 100, so 50 simultaneous items is reasonable
2. **Flexibility**: 20 item types × 5 inventory slots = enough for complex scenarios
3. **Safety margin**: 200 spawns/episode unlikely to be hit in Phase 1 testing
4. **Profiling target**: items_smoke provides baseline, can adjust in Phase 3

**Proposed Limits**:
```python
# Phase 1 Item Limits (src/townlet/universe/compiler.py)
MAX_ITEM_TYPES = 20
MAX_ITEMS_PER_AGENT = 5
MAX_SIMULTANEOUS_ITEMS_PER_LEVEL = 50
MAX_TOTAL_SPAWNS_PER_EPISODE = 200
```

**Validation**: Add assertions to UniverseCompiler Stage 1b (semantic validation).

---

## Implementation Checklist

Once Phase 0 decisions are finalized, update:

- [ ] `docs/plans/vfs_uplift/2025-11-19-phase-1-dtos-compiler.md` (Task 1: VFS Profiles DTOs)
  - Specify 2-tier file layout
  - Clarify static-only VFS profiles (no expressions)
  - Document proportional limits (15 global, 20 agent, 18 item)

- [ ] `docs/plans/vfs_uplift/2025-11-19-phase-3-items-runtime.md` (Task 3: Action Handlers)
  - Implement GET/DROP_SLOT_N/USE_SLOT_N actions
  - Document slot management logic
  - Reference edge-case-policies.md for overflow/empty slot handling

- [ ] `src/townlet/universe/compiler.py` (Add Phase 1 limits)
  - MAX_ITEM_TYPES = 20
  - MAX_ITEMS_PER_AGENT = 5
  - MAX_SIMULTANEOUS_ITEMS_PER_LEVEL = 50
  - MAX_TOTAL_SPAWNS_PER_EPISODE = 200

- [ ] `scripts/validate_vfs_obs_dimensions.py` (Update limits)
  - MAX_GLOBAL_PROFILES = 15 (down from 20)
  - MAX_ITEM_PROFILES_PER_TYPE = 6 (up from 5)
  - Re-run validation, update expected worst-case dims

- [ ] `tests/test_townlet/unit/vfs/test_observation_dimension_regression.py` (Update tests)
  - Update worst-case dims: 93 + (15+20+18) = 146 dims
  - Update realistic dims: 93 + (5+5+12) = 115 dims

- [ ] `docs/plans/vfs_uplift/edge-case-policies.md` (Validate alignment)
  - Ensure policies align with Q4 decision (generic GET/DROP/USE)
  - Update Policy #2 if needed (item commands vs item-specific actions)

---

## Confidence Assessment

| Decision | Confidence | Reason |
|----------|------------|--------|
| **Q1: 2-tier layout** | ⭐⭐⭐⭐⭐ HIGH | Strong precedent, minimal risk |
| **Q2: Phase 1 static** | ⭐⭐⭐⭐ MEDIUM-HIGH | Clear phase boundary, some flexibility trade-off |
| **Q3: Proportional limits** | ⭐⭐⭐ MEDIUM | Reasonable balance, needs re-validation |
| **Q4: Generic GET/USE** | ⭐⭐⭐⭐⭐ HIGH | Fixed action space critical for transfer learning |
| **Q5: Moderate limits** | ⭐⭐⭐ MEDIUM | Needs profiling, may adjust in Phase 3 |

---

## Next Steps

1. **Review** this decision matrix with team/stakeholders
2. **Finalize** decisions (accept recommendations or choose alternatives)
3. **Update** Phase 1-3 plans with finalized decisions
4. **Execute** Phase 0 (2-3 days → 1.5-2 days with this prep work)
5. **Begin** Phase 1 implementation with high confidence

**Time Saved**: This decision matrix reduces Phase 0 execution time by **0.5-1 day** (options pre-researched, precedents documented, trade-offs analyzed).
