# Items & VFS Profiles - Phase 0: Design Resolution

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolve 5 critical design questions blocking Items & VFS Profiles implementation (BLOCKERS identified in deep-dive analysis).

**Architecture:** Collaborative decision-making session with design artifacts, not code implementation. Outputs are decision documents and updated schema examples.

**Tech Stack:** Markdown, YAML schema examples, design documentation

**Prerequisites:**
- Deep-dive analysis completed (`docs/plans/2025-11-18-items-and-vfs-profiles.md` read and understood)
- Project team available for design decisions
- Understanding of VFS Phase 1 constraints (static variables only, expressions rejected)

**Estimated Time:** 12-20 hours across 2-3 days

---

## Task 1: Resolve File Layout (BLOCKER #1)

**Decision:** Where do VFS profiles and items configs live?

**Files:**
- Create: `docs/plans/vfs_uplift/decisions/001-file-layout.md`

**Step 1: Document the options**

Create decision document:

```markdown
# Decision 001: File Layout for VFS Profiles and Items

## Status: PROPOSED

## Context

Items & VFS Profiles require new config files. Two layout strategies:

### Option A: Separate Files
- `configs/<experiment>/vfs_profiles.yaml` (experiment-level)
- `configs/<experiment>/items.yaml` (experiment-level catalog)
- `configs/<experiment>/levels/<level>/items.yaml` (level-level appearance)

Pros:
- Clean separation of concerns
- Easy to diff/review changes
- Future-proof (items will reference profiles extensively)
- Consistent with current multi-file pattern

Cons:
- More files to track
- Slightly more compiler load stages

### Option B: Embedded in environment.yaml
- `configs/<experiment>/environment.yaml` includes `vfs_profiles:` section
- `configs/<experiment>/items.yaml` for catalog
- `configs/<experiment>/levels/<level>/items.yaml` for appearance

Pros:
- One less file to manage
- VFS profiles close to environment config

Cons:
- environment.yaml becomes large (already has substrate, affordances, etc.)
- Harder to review profile changes (buried in large file)
- Circular dependency risk (profiles may reference items in future)

## Decision

**OPTION A: Separate Files**

Rationale:
1. Scales better (item-profile interactions will grow complex)
2. Easier code review (profiles change independently of environment)
3. Consistent with bars.yaml, affordances.yaml pattern
4. Compiler complexity is minor (one extra load stage)

## Consequences

- Update UniverseCompiler to add vfs_profiles.yaml load stage
- Reference config needs vfs_profiles.yaml section
- Schema docs need separate vfs-profiles.md file
```

**Step 2: Review with team**

Action: Present options A and B to team, gather feedback
Expected: Team approval or modification request

**Step 3: Finalize decision**

Update decision document status:
```markdown
## Status: ACCEPTED (2025-11-19)
```

**Step 4: Document file structure**

Add to decision document:

```markdown
## Implementation Impact

### Directory Structure
```
configs/<experiment>/
├── environment.yaml         # Substrate, core settings
├── vfs_profiles.yaml        # NEW: Global/agent/item VFS profiles
├── items.yaml               # NEW: Item catalog (types, interactions)
├── bars.yaml
├── affordances.yaml
└── levels/
    └── <level>/
        ├── items.yaml       # NEW: Item appearance (spawn rules, inventory)
        ├── training.yaml
        └── ...
```

### Compiler Changes Required
- Add `load_vfs_profiles()` method to RawConfigsV21
- Add `load_items_catalog()` method to RawConfigsV21
- Add validation: items.yaml references must exist in vfs_profiles.yaml
```

**Step 5: Commit decision**

```bash
git add docs/plans/vfs_uplift/decisions/001-file-layout.md
git commit -m "docs(vfs): resolve file layout decision (separate files)"
```

---

## Task 2: Resolve Expression Language Scope (BLOCKER #2)

**Decision:** How much expression DSL in Phase 1?

**Files:**
- Create: `docs/plans/vfs_uplift/decisions/002-expression-language-phase1.md`

**Step 1: Document current state**

```markdown
# Decision 002: Expression Language Scope for Phase 1

## Status: PROPOSED

## Context

Current schema examples show `expression` fields:
```yaml
- id: is_night
  expression: "time_of_day >= 20 || time_of_day < 6"
```

But VFS Phase 1 documentation says:
- "Expression language not wired yet (static variables only)"
- `load_variables_reference_config` rejects expressions
- VARIABLE_SUBSYSTEM.md: "Expression-based variables are explicitly rejected"

**Conflict:** Plan shows expression fields but runtime rejects them.

## Options

### Option A: Hard-Coded Defaults Only (Conservative)
Phase 1 schema:
```yaml
- id: is_night
  initial_value: false         # REQUIRED: static default
  # expression: "..."          # REJECTED at load time
  normalization:
    kind: minmax
    min: 0.0
    max: 1.0
```

Runtime behavior:
- Variables hold static values set at initialization
- No expression evaluation, no dependencies
- `load_variables_reference_config` raises ValidationError if `expression` present

Pros:
- Clear Phase 1 boundary
- Zero BAC complexity in Phase 1
- Forces proper Phase 2 design

Cons:
- Variables are useless (can't derive anything)
- Limits testing of VFS integration

### Option B: Simple Hard-Coded Expressions (Pragmatic)
Phase 1 schema:
```yaml
- id: is_night
  expression_type: "threshold"  # enum: threshold | linear | passthrough
  deps:
    bars: ["time"]
  threshold:
    variable: "time"
    operator: ">="
    value: 20.0
```

Runtime behavior:
- Support 3 expression types: threshold, linear transform, passthrough
- Hard-coded evaluation logic (no DSL parsing)
- Dependency validation at compile time

Pros:
- Enables real VFS testing in Phase 1
- Simpler than full DSL
- Proves out dependency ordering

Cons:
- Technical debt if abandoned for DSL
- Scope creep risk

### Option C: Full Expression DSL (Aggressive)
Implement full expression parser and evaluator in Phase 1.

Pros: Complete feature

Cons: **12-16 week effort, derails entire plan**

## Decision

**OPTION A: Hard-Coded Defaults Only**

Rationale:
1. Phase 1 goal is **schema validation and metadata compilation**, not runtime behavior
2. Expression semantics require BAC integration (Phase 2+)
3. Testing can use mock VFS values (set via `initial_value`)
4. Clear phase boundary prevents scope creep

Constraint: Variables in Phase 1 are **metadata-only**. Runtime behavior deferred to Phase 2.

## Consequences

### Schema Changes
```yaml
# Phase 1: Only static variables allowed
variables:
  - id: "debug_flag"
    scope: "global"
    type: "scalar"
    initial_value: 1.0           # REQUIRED
    normalization:               # OPTIONAL
      kind: minmax
      min: 0.0
      max: 1.0
    # expression: "..."          # FORBIDDEN (raises error)
    # deps: {...}                # FORBIDDEN (raises error)
```

### Validation Rules
`load_variables_reference_config` must reject:
- `expression` field present
- `deps` field present
- Any field not in allowed set: [id, scope, type, initial_value, normalization, description]

### Documentation Updates
All YAML examples in docs/plans/ must add:
```yaml
# FUTURE (Phase 2+): Expression support
# expression: "time_of_day >= 20"
# deps: {bars: ["time"]}
```
```

**Step 2: Review with team**

Action: Present analysis to team
Expected: Approval of Option A (conservative approach)

**Step 3: Update schema examples**

Find all expression examples in plan:

```bash
grep -r "expression:" docs/plans/2025-11-18-items-and-vfs-profiles.md
```

For each occurrence, add `# FUTURE (Phase 2+):` comment prefix.

**Step 4: Define Phase 1 schema**

Document allowed VariableDef fields for Phase 1:

```markdown
## Phase 1 Schema (Static Variables Only)

### Allowed Fields
- `id` (str, required): Unique variable identifier
- `scope` (enum, required): "global" | "agent" | "item"
- `type` (enum, required): "scalar" | "vec2i" | "vec3i" | "vecNi" | "vecNf" | "bool"
- `dims` (int, conditional): Required if type is vecNi/vecNf
- `initial_value` (float | list[float], required): Static default value
- `normalization` (NormalizationSpec, optional): Observation normalization
- `description` (str, optional): Human-readable description

### Forbidden Fields (Phase 2+)
- `expression` - Raises ValidationError with message: "Expression-based variables require Phase 2+ (BAC integration). Use initial_value for Phase 1."
- `deps` - Raises ValidationError
- `update_on` - Raises ValidationError
```

**Step 5: Update validation logic**

Document required change to `load_variables_reference_config`:

```python
# src/townlet/vfs/schema.py

def load_variables_reference_config(config_path: Path) -> list[VariableDef]:
    """Load variables from YAML, enforcing Phase 1 constraints."""
    with open(config_path) as f:
        data = yaml.safe_load(f)

    variables = []
    for var_data in data.get("variables", []):
        # PHASE 1 GUARD: Reject expression-based variables
        forbidden_fields = ["expression", "deps", "update_on"]
        for field in forbidden_fields:
            if field in var_data:
                raise ValidationError(
                    f"Variable '{var_data.get('id', 'unknown')}': "
                    f"Field '{field}' requires Phase 2+ (BAC integration). "
                    f"Use 'initial_value' for static variables in Phase 1."
                )

        # Require initial_value in Phase 1
        if "initial_value" not in var_data:
            raise ValidationError(
                f"Variable '{var_data.get('id', 'unknown')}': "
                f"Field 'initial_value' is required in Phase 1 (static variables only)."
            )

        variables.append(VariableDef(**var_data))

    return variables
```

**Step 6: Commit decision**

```bash
git add docs/plans/vfs_uplift/decisions/002-expression-language-phase1.md
git commit -m "docs(vfs): resolve expression language scope (Phase 1 = static only)"
```

---

## Task 3: Resolve Observation Budget (BLOCKER #3)

**Decision:** How many item slots in observation vector?

**Files:**
- Create: `docs/plans/vfs_uplift/decisions/003-observation-budget.md`

**Step 1: Calculate observation size impact**

```markdown
# Decision 003: Observation Budget for Item VFS

## Status: PROPOSED

## Context

Item VFS profiles must appear in agent observations. Need to determine:
1. How many item slots to reserve in obs vector
2. What happens when agent holds more items than slots
3. obs_dim stability across curriculum levels

## Sizing Analysis

### Current Observation Dimensions (Grid2D, relative encoding)
- L0_0_minimal: 38 dims
- L0_5_dual_resource: 78 dims
- L1_full_observability: 93 dims
- L2_partial_observability (POMDP): 54 dims
- L3_temporal_mechanics: 93 dims

### Item VFS Addition (example)
Assume:
- max_items_per_agent: 3
- VFS profiles per item: 2 (e.g., durability, wetness_resistance)
- Dims per profile: 1 (scalar)

Additional dims: 3 slots × 2 profiles × 1 dim = **6 dims**

With masking: Empty slots contribute masked values (0.0), not missing dims.

### Scalability
At 10 items/agent with 5 profiles each:
- Additional dims: 10 × 5 × 1 = **50 dims**
- L1 total: 93 + 50 = 143 dims (still reasonable for MLP)

At 20 items/agent with 10 profiles each:
- Additional dims: 20 × 10 × 1 = **200 dims**
- L1 total: 93 + 200 = 293 dims (starts to impact network size)

## Options

### Option A: Fixed Small Slots (Conservative)
- max_items_per_agent: 3 (hard limit in Phase 1)
- max_vfs_profiles_per_item: 5 (validation limit)
- Max additional dims: 3 × 5 = 15 dims

Pros:
- Predictable obs_dim
- Minimal network impact
- Easy to reason about

Cons:
- Limited item complexity
- May need to increase in Phase 3+

### Option B: Configurable Slots (Flexible)
- max_items_per_agent: configurable (Level-scoped)
- max_item_obs_slots: configurable (Experiment-scoped, ≤ max_items_per_agent)
- obs shows first N items by priority/order

Pros:
- Scales with use case
- Advanced users can tune

Cons:
- obs_dim varies by experiment (breaks checkpoint transfer)
- Requires experiment-level obs layout decisions

### Option C: Dynamic Pooling (Advanced)
- Aggregate item VFS via pooling (mean/max/sum across held items)
- Fixed obs_dim regardless of item count

Pros:
- Scalable to arbitrary items
- Stable obs_dim

Cons:
- Loses per-item information
- Complex to implement
- Deferred to Phase 4+

## Decision

**OPTION A: Fixed Small Slots (Phase 1)**

Phase 1 Constraints:
- `max_items_per_agent: 3` (hard-coded limit)
- `max_vfs_profiles_per_item: 5` (compiler validation)
- Total item contribution: ≤ 15 dims

Rationale:
1. Proves out item VFS integration without explosion
2. Checkpoint compatibility preserved (fixed layout)
3. Can increase in Phase 3 if needed (breaking change acceptable in pre-release)

## Consequences

### Validation Rules
Compiler must enforce:
```python
if config.inventory.max_items_per_agent > 3:
    raise ValidationError(
        "Phase 1 limit: max_items_per_agent must be ≤ 3. "
        "Increase requires Phase 3+ (obs layout redesign)."
    )

profile_count = sum(len(item_type.vfs_profiles) for item_type in catalog)
if profile_count > 5:
    raise ValidationError(
        f"Phase 1 limit: max 5 VFS profiles per item type. "
        f"Found {profile_count} profiles in item '{item_type.id}'."
    )
```

### Observation Layout
```
Agent Observation:
  [0:N]       Standard fields (position, bars, affordances, temporal)
  [N:N+5]     Item slot 0 VFS profiles (5 profiles, padded if <5)
  [N+5:N+10]  Item slot 1 VFS profiles
  [N+10:N+15] Item slot 2 VFS profiles

Empty slots: Masked with 0.0 values
Profile ordering: Deterministic (sorted by profile_id)
```

### Overflow Policy (when agent tries to pickup 4th item)
Phase 1: **Deny pickup**
- INTERACT action on item succeeds but item not added to inventory
- Agent receives feedback (optional: negative shaping reward)
- No silent overflows

Future: Configurable policy (drop_oldest | priority_replace)
```

**Step 2: Update limits in plan**

Document Phase 1 limits:

```markdown
## Phase 1 Hard Limits

| Limit | Value | Enforcement |
|-------|-------|-------------|
| max_items_per_agent | 3 | Compiler validation |
| max_vfs_profiles_per_item | 5 | Compiler validation |
| max_item_types_per_experiment | 10 | Compiler validation |
| max_item_instances_total | 50 | Runtime warning (not error) |

### Rationale
- Keeps obs_dim growth bounded (≤15 dims for items)
- Proves out architecture without complexity
- Limits are relaxed in Phase 3+ after validation
```

**Step 3: Define overflow policy**

```markdown
## Inventory Overflow Behavior

### Phase 1: Deny Pickup
When agent at max_items_per_agent attempts pickup:

1. INTERACT action executes (no action mask blocking)
2. Pickup logic checks inventory count
3. If count == max_items_per_agent:
   - Pickup denied
   - Item remains in world
   - Agent receives no item
   - Optional: Negative shaping reward (-0.1)

### Future (Phase 3+): Configurable Policy
```yaml
inventory:
  max_items_per_agent: 5
  overflow_policy: "drop_oldest"  # deny | drop_oldest | priority_replace
```
```

**Step 4: Commit decision**

```bash
git add docs/plans/vfs_uplift/decisions/003-observation-budget.md
git commit -m "docs(vfs): resolve observation budget (3 slots, 5 profiles, deny overflow)"
```

---

## Task 4: Resolve Interaction Granularity (BLOCKER #4)

**Decision:** How are item interactions represented in action vocabulary?

**Files:**
- Create: `docs/plans/vfs_uplift/decisions/004-interaction-granularity.md`

**Step 1: Analyze action space implications**

```markdown
# Decision 004: Item Interaction Action Granularity

## Status: PROPOSED

## Context

Items introduce new agent actions:
- Pickup item
- Drop item
- Use item (consume, activate, etc.)

Question: How are these represented in the fixed action vocabulary?

## Current Action Space Architecture

HAMLET uses **global fixed action vocabulary** for checkpoint transfer:
- Grid2D: 8 actions (6 directional + INTERACT + WAIT)
- All levels share same action_dim
- Action masking used for per-level differences

Example: L0 has 1 affordance, L1 has 14, but both have action_dim=8.
L0 masks INTERACT when no affordance nearby.

## Options

### Option A: Fixed Core Actions + Slot-Specific Use
Action vocabulary:
```
0: MOVE_NORTH
1: MOVE_SOUTH
2: MOVE_EAST
3: MOVE_WEST
...
6: INTERACT      # For affordances
7: WAIT
8: GET           # NEW: Pickup item at position
9: DROP_SLOT_0   # NEW: Drop item from slot 0
10: DROP_SLOT_1
11: DROP_SLOT_2
12: USE_SLOT_0   # NEW: Use item in slot 0
13: USE_SLOT_1
14: USE_SLOT_2
```

Total action_dim: 15 (Grid2D with items)

Masking:
- GET masked when no item at position
- DROP_SLOT_N masked when slot N empty
- USE_SLOT_N masked when slot N empty or item has no use effect

Pros:
- Fixed vocabulary (checkpoint compatible)
- Explicit per-slot control
- Aligns with current masking philosophy

Cons:
- action_dim grows with max_items_per_agent
- Slot semantics exposed to policy

### Option B: Parameterized Actions
Action vocabulary:
```
8: GET
9: DROP <slot_id>
10: USE <slot_id>
```

Requires: Argument passing mechanism (not currently supported)

Pros:
- Compact action space
- Scales to any slot count

Cons:
- **Breaking change to action_config architecture**
- **Not compatible with current discrete action space**
- 8-12 week implementation for argument support

### Option C: Single USE Action + Heuristic
Action vocabulary:
```
8: GET
9: DROP
10: USE
```

Runtime behavior:
- USE: Uses "first usable item" in inventory (priority order)
- DROP: Drops "first droppable item"

Pros:
- Minimal action space growth

Cons:
- Removes agent control over which item
- Confusing for debugging
- Not suitable for strategic item use

## Decision

**OPTION A: Fixed Core Actions + Slot-Specific Actions**

Rationale:
1. Aligns with current action_config philosophy (fixed vocab + masking)
2. No breaking changes to action space architecture
3. Explicit control matches other actions (directional movement)
4. action_dim growth acceptable (Grid2D: 8→15, still tiny)

Phase 1 Constraint: max_items_per_agent=3, so action_dim growth is 7 actions.

## Consequences

### Action Vocabulary (Grid2D with Items)
```yaml
# Experiment-level: global_actions.yaml includes item actions
substrate_actions:
  - MOVE_NORTH
  - MOVE_SOUTH
  - MOVE_EAST
  - MOVE_WEST
  - MOVE_NORTHEAST
  - MOVE_NORTHWEST
  - MOVE_SOUTHEAST
  - MOVE_SOUTHWEST

core_actions:
  - INTERACT        # Generated when affordances > 0
  - WAIT            # Always present

item_actions:     # Generated when max_items_per_agent > 0
  - GET             # Pickup item at current position
  - DROP_SLOT_0     # Drop item from inventory slot 0
  - DROP_SLOT_1
  - DROP_SLOT_2
  - USE_SLOT_0      # Use/consume item in slot 0
  - USE_SLOT_1
  - USE_SLOT_2
```

### Masking Logic
```python
# Pseudocode for action masking
def compute_action_mask(agent_state, world_state):
    mask = torch.ones(action_dim, dtype=torch.bool)

    # GET: masked if no item at agent position
    item_at_pos = world_state.items_at_position(agent_state.position)
    mask[ACTION_GET] = len(item_at_pos) > 0

    # DROP_SLOT_N: masked if slot N empty
    for slot_idx in range(max_items_per_agent):
        mask[ACTION_DROP_SLOT_0 + slot_idx] = (
            agent_state.inventory[slot_idx] is not None
        )

    # USE_SLOT_N: masked if slot N empty or item not usable
    for slot_idx in range(max_items_per_agent):
        item = agent_state.inventory[slot_idx]
        mask[ACTION_USE_SLOT_0 + slot_idx] = (
            item is not None and item.has_use_effect
        )

    return mask
```

### Compiler Changes
- ActionConfig must generate item actions when `max_items_per_agent > 0`
- Action indices must be deterministic (sorted order)
- Action labels derived from slot index (DROP_SLOT_0, not DROP_ITEM_umbrella)

### Documentation
Update action space docs to show:
- Core actions (always present): WAIT
- Substrate actions (substrate-dependent): MOVE_*, INTERACT
- Item actions (items-dependent): GET, DROP_SLOT_*, USE_SLOT_*
```

**Step 2: Document action_dim impact**

```markdown
## Action Dimension Growth

### Grid2D
- Without items: 8 actions (6 move + INTERACT + WAIT)
- With items (max_items_per_agent=3): 15 actions
- Growth: +7 actions (+87%)

### Grid3D
- Without items: 10 actions
- With items: 17 actions
- Growth: +7 actions (+70%)

### Aspatial
- Without items: 4 actions (custom actions + WAIT)
- With items: 11 actions
- Growth: +7 actions (+175%)

Note: Growth is constant (+1 GET + 3 DROP + 3 USE) regardless of substrate.
```

**Step 3: Update schema for item interactions**

```markdown
## Item Interaction Schema (Revised)

Items define effects, not custom actions:

```yaml
# configs/<experiment>/items.yaml
item_types:
  - id: umbrella
    name: "Umbrella"
    icon: "☂️"
    vfs_profiles: ["item_wetness_resistance"]

    interactions:
      # Pickup effect (triggered by GET action)
      pickup:
        effects:
          bars: []
          vfs: []

      # Use effect (triggered by USE_SLOT_N action)
      use:
        effects:
          bars:
            - name: "mood"
              delta: 0.1
          agent_vfs:
            - name: "is_protected_from_rain"
              set_value: true
        consumes_item: true    # Item removed from inventory after use

      # Drop effect (triggered by DROP_SLOT_N action)
      drop:
        effects:
          agent_vfs:
            - name: "is_protected_from_rain"
              set_value: false
```

No item-scoped custom actions. Interactions are effect specifications.
```

**Step 4: Commit decision**

```bash
git add docs/plans/vfs_uplift/decisions/004-interaction-granularity.md
git commit -m "docs(vfs): resolve interaction granularity (fixed vocab + slot actions)"
```

---

## Task 5: Resolve Performance Limits (BLOCKER #5)

**Decision:** What are the hard limits on items and profiles?

**Files:**
- Create: `docs/plans/vfs_uplift/decisions/005-performance-limits.md`

**Step 1: Define Phase 1 conservative limits**

```markdown
# Decision 005: Performance Limits for Items & VFS Profiles

## Status: PROPOSED

## Context

Need hard limits to:
1. Prevent pathological configs (1000 items, 100 profiles each)
2. Bound GPU memory usage
3. Ensure reasonable compilation times
4. Guide users toward sensible designs

## Phase 1 Limits (Conservative)

### Inventory Limits
| Limit | Value | Rationale |
|-------|-------|-----------|
| max_items_per_agent | 3 | Observation budget (15 dims) |
| max_item_types | 10 | Catalog complexity |
| max_item_instances_total | 50 | GPU memory (50 items × vectorized ops) |

### VFS Limits
| Limit | Value | Rationale |
|-------|-------|-----------|
| max_vfs_profiles_per_item | 5 | Observation slots |
| max_vfs_profiles_global | 20 | Shared state complexity |
| max_vfs_profiles_agent | 20 | Per-agent state |

### Spawn Limits (per level)
| Limit | Value | Rationale |
|-------|-------|-----------|
| max_spawn_rules | 10 | Scheduling complexity |
| max_simultaneous_items (per type) | 10 | World clutter |

### Total Budget
- Max obs_dim growth: 15 (items) + 20 (global VFS) + 20 (agent VFS) = **55 dims**
- Max action_dim growth: 7 (item actions)

## Enforcement Strategy

### Compiler-Time (Strict)
Raise ValidationError if exceeded:
- max_item_types
- max_vfs_profiles_per_item
- max_vfs_profiles_global
- max_vfs_profiles_agent
- max_spawn_rules

### Runtime (Warning)
Log warning if exceeded:
- max_item_instances_total (warn at 40, error at 50)

### No Enforcement
Soft limits (documented but not enforced):
- Suggested: Keep spawn rules < 5 for readability
- Suggested: Keep VFS profiles < 10 per scope for simplicity

## Consequences

### Validation Code
```python
# src/townlet/universe/compiler.py

def validate_items_catalog(catalog: ItemsCatalogConfig) -> None:
    if len(catalog.item_types) > MAX_ITEM_TYPES:
        raise ValidationError(
            f"Too many item types: {len(catalog.item_types)} > {MAX_ITEM_TYPES}. "
            f"Phase 1 limit. Reduce item catalog size."
        )

    for item_type in catalog.item_types:
        if len(item_type.vfs_profiles) > MAX_VFS_PROFILES_PER_ITEM:
            raise ValidationError(
                f"Item '{item_type.id}': Too many VFS profiles: "
                f"{len(item_type.vfs_profiles)} > {MAX_VFS_PROFILES_PER_ITEM}. "
                f"Reduce profile count or increase limit in Phase 3."
            )

def validate_vfs_profiles(profiles: VFSProfilesConfig) -> None:
    if len(profiles.global_profiles) > MAX_VFS_PROFILES_GLOBAL:
        raise ValidationError(
            f"Too many global VFS profiles: {len(profiles.global_profiles)} > "
            f"{MAX_VFS_PROFILES_GLOBAL}."
        )

    if len(profiles.agent_profiles) > MAX_VFS_PROFILES_AGENT:
        raise ValidationError(
            f"Too many agent VFS profiles: {len(profiles.agent_profiles)} > "
            f"{MAX_VFS_PROFILES_AGENT}."
        )
```

### Constants
```python
# src/townlet/universe/compiler.py (add to top of file)

# Phase 1 Limits (Items & VFS Profiles)
MAX_ITEM_TYPES = 10
MAX_ITEM_INSTANCES_TOTAL = 50
MAX_VFS_PROFILES_PER_ITEM = 5
MAX_VFS_PROFILES_GLOBAL = 20
MAX_VFS_PROFILES_AGENT = 20
MAX_SPAWN_RULES_PER_LEVEL = 10
```

### Documentation
Add to reference config:
```yaml
# configs/reference_config/reference-config-v2.1-complete.yaml

# PHASE 1 LIMITS (enforced by compiler)
# - max_item_types: 10
# - max_items_per_agent: 3
# - max_vfs_profiles_per_item: 5
# - max_vfs_profiles_global: 20
# - max_vfs_profiles_agent: 20
#
# These limits prevent pathological configs and bound GPU memory.
# Limits may be increased in Phase 3+ after performance profiling.
```
```

**Step 2: Define profiling requirements for Phase 3**

```markdown
## Phase 3 Profiling Requirements

Before increasing limits, must profile:

### GPU Memory Test
Config: Max allowed items and profiles
- 10 item types
- 3 items per agent
- 5 profiles per item
- 100 agents

Measure:
- Peak GPU memory (CUDA profiler)
- Obs tensor size (bytes)
- Inventory tensor size (bytes)

Pass criteria: < 2GB GPU memory for 100-agent vectorized env

### Compilation Time Test
Config: Max allowed complexity
- 10 item types
- 10 spawn rules
- 20 global + 20 agent VFS profiles

Measure:
- Compiler wall-clock time

Pass criteria: < 5 seconds to compile universe

### Runtime Performance Test
Config: Max item instances
- 50 items spawned simultaneously
- 100 agents

Measure:
- FPS (frames per second) during training
- Inventory update time per step

Pass criteria: > 500 FPS on RTX 3090

## Limit Increase Protocol

To increase Phase 1 limits:
1. Run all profiling tests at new limit
2. Document memory/performance impact
3. Update constants in compiler.py
4. Update validation error messages
5. Update reference config documentation
```

**Step 3: Commit decision**

```bash
git add docs/plans/vfs_uplift/decisions/005-performance-limits.md
git commit -m "docs(vfs): resolve performance limits (conservative Phase 1 bounds)"
```

---

## Task 6: Create Decision Summary Document

**Files:**
- Create: `docs/plans/vfs_uplift/decisions/README.md`

**Step 1: Write summary**

```markdown
# Items & VFS Profiles - Design Decisions

This directory contains the 5 critical design decisions that unblocked the implementation plan.

## Decision Index

| ID | Decision | Status | Date |
|----|----------|--------|------|
| 001 | [File Layout](001-file-layout.md) | ACCEPTED | 2025-11-19 |
| 002 | [Expression Language Phase 1 Scope](002-expression-language-phase1.md) | ACCEPTED | 2025-11-19 |
| 003 | [Observation Budget](003-observation-budget.md) | ACCEPTED | 2025-11-19 |
| 004 | [Interaction Granularity](004-interaction-granularity.md) | ACCEPTED | 2025-11-19 |
| 005 | [Performance Limits](005-performance-limits.md) | ACCEPTED | 2025-11-19 |

## Summary

### File Layout (001)
**Decision:** Separate `vfs_profiles.yaml` and `items.yaml` files (not embedded in environment.yaml)

**Impact:**
- +2 experiment-level files
- +1 level-level file (items.yaml for appearance)
- Cleaner separation, easier code review

### Expression Language (002)
**Decision:** Phase 1 supports only static variables (`initial_value` field). Expression DSL deferred to Phase 2+ (BAC integration).

**Impact:**
- Phase 1 variables are metadata-only
- Validation rejects `expression`, `deps`, `update_on` fields
- All plan examples updated with `# FUTURE:` comments

### Observation Budget (003)
**Decision:** Phase 1 limits: `max_items_per_agent=3`, `max_vfs_profiles_per_item=5`

**Impact:**
- Max item contribution to obs: 15 dims
- Overflow policy: Deny pickup (no silent failures)
- obs_dim remains stable across levels

### Interaction Granularity (004)
**Decision:** Fixed action vocabulary with slot-specific actions (GET, DROP_SLOT_0-2, USE_SLOT_0-2)

**Impact:**
- action_dim growth: +7 actions (Grid2D: 8→15)
- No parameterized actions (avoids architecture redesign)
- Masking controls availability per slot

### Performance Limits (005)
**Decision:** Conservative Phase 1 limits with compiler validation

**Impact:**
- max_item_types: 10
- max_item_instances_total: 50
- max_vfs_profiles_global: 20
- max_vfs_profiles_agent: 20
- Profiling required before increasing in Phase 3

## Next Steps

With all 5 decisions resolved, proceed to:
- **Phase 1:** DTOs + Compiler (schema implementation)
- **Phase 2:** VFS Engine + DynObs (runtime evaluation)
- **Phase 3:** Items Runtime + Inventory (state management)
- **Phase 4:** Advanced Scheduling (optional)

See `docs/plans/vfs_uplift/` for implementation plans.
```

**Step 2: Commit summary**

```bash
git add docs/plans/vfs_uplift/decisions/README.md
git commit -m "docs(vfs): add design decisions summary (Phase 0 complete)"
```

---

## Task 7: Update Main Plan with Decisions

**Files:**
- Modify: `docs/plans/2025-11-18-items-and-vfs-profiles.md`

**Step 1: Add link to decisions**

At the top of Section 9 (Open Design Questions), add:

```markdown
## 9. Open Design Questions

**STATUS: RESOLVED (2025-11-19)**

All design questions have been resolved. See detailed decision documents:
- [Decision Index](vfs_uplift/decisions/README.md)

Original questions and resolutions:
```

**Step 2: Update each question with resolution**

For each question in Section 9, add resolution:

```markdown
1. **File layout** → RESOLVED
   - Decision: Separate `vfs_profiles.yaml` file (not embedded)
   - See: [001-file-layout.md](vfs_uplift/decisions/001-file-layout.md)

2. **Expression language for VFS profiles** → RESOLVED
   - Decision: Phase 1 = static variables only (`initial_value`), no expressions
   - See: [002-expression-language-phase1.md](vfs_uplift/decisions/002-expression-language-phase1.md)

3. **Observation budget** → RESOLVED
   - Decision: max_items_per_agent=3, max_vfs_profiles_per_item=5, deny overflow
   - See: [003-observation-budget.md](vfs_uplift/decisions/003-observation-budget.md)

4. **Interaction granularity** → RESOLVED
   - Decision: Fixed vocab + slot-specific actions (GET, DROP_SLOT_N, USE_SLOT_N)
   - See: [004-interaction-granularity.md](vfs_uplift/decisions/004-interaction-granularity.md)

5. **Performance considerations** → RESOLVED
   - Decision: Conservative Phase 1 limits (10 types, 50 instances, 20 profiles/scope)
   - See: [005-performance-limits.md](vfs_uplift/decisions/005-performance-limits.md)
```

**Step 3: Commit update**

```bash
git add docs/plans/2025-11-18-items-and-vfs-profiles.md
git commit -m "docs(vfs): mark design questions resolved, link to decisions"
```

---

## Task 8: Create Phase 1 Readiness Checklist

**Files:**
- Create: `docs/plans/vfs_uplift/PHASE1-READINESS.md`

**Step 1: Write checklist**

```markdown
# Phase 1 Readiness Checklist

Before starting Phase 1 implementation (DTOs + Compiler), verify:

## Design Decisions Complete

- [x] BLOCKER #1: File layout (separate vfs_profiles.yaml) - RESOLVED
- [x] BLOCKER #2: Expression language scope (static only) - RESOLVED
- [x] BLOCKER #3: Observation budget (3 slots, 5 profiles) - RESOLVED
- [x] BLOCKER #4: Interaction granularity (slot actions) - RESOLVED
- [x] BLOCKER #5: Performance limits (conservative) - RESOLVED

## Preconditions Met

- [x] All tests passing (verified: action_space 7/7 passed)
- [x] HamletConfig removed (verified: 0 grep matches)
- [x] VFS Phase 1 complete (verified: 88 tests, 90% coverage)
- [x] Config v2.1 operational (verified: 5 curriculum levels)

## Documentation Ready

- [x] Decision documents written (5 decisions in vfs_uplift/decisions/)
- [x] Decision summary created (README.md with index)
- [x] Main plan updated (design questions marked resolved)
- [ ] Phase 1 implementation plan written (PENDING)

## Team Alignment

- [ ] Design decisions reviewed by team
- [ ] Performance limits approved
- [ ] 4-6 week timeline acknowledged
- [ ] Phase 4 marked as optional (not MVP blocker)

## GO/NO-GO Decision

**Status:** NO-GO (pending team review)

**Blocking:** Team review of design decisions

**Next Action:** Present decision documents to team for approval

---

Once all checkboxes marked [x], Phase 1 implementation may begin.
```

**Step 2: Commit checklist**

```bash
git add docs/plans/vfs_uplift/PHASE1-READINESS.md
git commit -m "docs(vfs): create Phase 1 readiness checklist"
```

---

## Completion Criteria

Phase 0 is complete when:

- [x] All 5 design decisions documented
- [x] Decision summary created
- [x] Main plan updated with resolution links
- [x] Phase 1 readiness checklist created
- [ ] **Team review and approval of all decisions** (BLOCKING)

---

## Final Commit

```bash
git add -A
git commit -m "docs(vfs): Phase 0 design resolution complete

Resolved 5 critical design blockers:
1. File layout: Separate vfs_profiles.yaml (not embedded)
2. Expression language: Phase 1 static only, defer DSL to Phase 2+
3. Observation budget: 3 slots × 5 profiles, deny overflow
4. Interaction granularity: Fixed vocab + slot actions
5. Performance limits: Conservative bounds (10 types, 50 instances)

All design artifacts in docs/plans/vfs_uplift/decisions/

Ready for team review. Phase 1 blocked on approval.
"
```

---

## Next Phase

Once team approves all decisions → **Phase 1: DTOs + Compiler Implementation**

See: `docs/plans/vfs_uplift/2025-11-19-phase-1-dtos-compiler.md` (to be created)
