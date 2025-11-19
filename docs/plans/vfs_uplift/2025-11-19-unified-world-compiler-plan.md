# Unified World Compiler Implementation Plan

**Status:** Ready for Implementation
**Date:** 2025-11-19
**Owner:** World Compiler (T0 Pillar 3)
**Components:** Expression Language + VFS Profiles + Effects + Items

---

## Executive Summary

This plan implements the complete **World Compiler** (T0 Pillar 3) as a unified package of work, building from foundational expression language through VFS profiles, Effects system, and Items integration.

**Key Insight:** These components are **not independent features** - they are layers of a single coherent system. The expression language powers VFS variables, which feed into Effects, which drive Items interactions. Building them together ensures clean integration and avoids retrofit pain.

**Total Timeline:** 28-36 days (5.5-7 weeks)
**Components Delivered:**
- HAMLET Expression Language (compiler + runtime)
- VFS Profiles (dynamic, expression-based)
- Effects System (command pipelines)
- Items System (built on Effects)
- Complete World Compiler integration

---

## Architecture Overview

### Three T0 Pillars

```
T0 PILLAR 1: Strata Compiler
├─→ Spatial substrate (Grid2D, Continuous, Aspatial)
└─→ Output: CompiledSubstrate

T0 PILLAR 2: Brain Compiler
├─→ Q-Learning + Drive As Code
└─→ Output: CompiledBrain

T0 PILLAR 3: World Compiler (THIS PLAN)
├─→ Foundation: Expression Language + Type System
├─→ Layer 1: VFS Profiles (dynamic variables)
├─→ Layer 2: Effects (command pipelines)
├─→ Layer 3: Items (world objects)
└─→ Output: CompiledWorld
```

### Component Dependencies

```
┌─────────────────────────────────────┐
│ Expression Language + Type System   │ ← Foundation (Week 1-2)
│ - Parse expressions to AST          │
│ - Type checking & validation        │
│ - Runtime evaluation context        │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ VFS Profiles │  │   Effects    │     ← Layer 1 & 2 (Week 2-4)
│ - Dynamic    │  │ - Catalogs   │
│ - References │  │ - Commands   │
│ - Computed   │  │ - Runtime    │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ▼
        ┌──────────────┐
        │    Items     │               ← Layer 3 (Week 5-6)
        │ - Catalog    │
        │ - Effects    │
        │ - Inventory  │
        └──────────────┘
```

---

## Phase 1: Expression Language Foundation (6-8 days)

**Goal:** Build the HAMLET Expression Language that powers all dynamic computation (VFS, Effects, DAC).

**Why First:** Both VFS and Effects need expression evaluation. Building this foundation avoids duplicate work.

### Deliverables

```
src/townlet/world/
├── expression/
│   ├── __init__.py
│   ├── ast_nodes.py         # AST node types (BinaryOp, PathAccess, etc.)
│   ├── parser.py            # Parse string → AST
│   ├── type_checker.py      # Validate types, resolve paths
│   ├── evaluator.py         # Execute AST → tensor value
│   └── context.py           # Execution context (bars, vfs, self, target)
├── types/
│   ├── __init__.py
│   ├── primitive.py         # scalar, bool, vec2i, vec3i, vecNi, vecNf
│   ├── reference.py         # agent_ref, item_ref, affordance_ref, effect_ref
│   └── tensor.py            # tensor1d, tensor2d, tensor3d, tensorNd
└── compiler/
    ├── __init__.py
    └── world_compiler.py    # Main compilation orchestrator

configs/test/expression_smoke/
└── expressions.yaml         # Test expressions for validation

tests/test_townlet/unit/world/expression/
├── test_parser.py           # Parse expressions to AST
├── test_type_checker.py     # Type validation
├── test_evaluator.py        # Execution tests
└── test_operators.py        # All operators from VARIABLE_SUBSYSTEM.md
```

### Tasks

**Task 1.1: AST Node Types (2 days)**
- Define AST nodes: `Constant`, `Variable`, `PathAccess`, `BinaryOp`, `UnaryOp`, `FunctionCall`, `IfThenElse`
- Implement visitor pattern for AST traversal
- Write 10-15 unit tests

**Task 1.2: Expression Parser (2 days)**
- Implement recursive descent parser (or use pyparsing)
- Parse: `target.bar.energy + (0.05 * intensity)` → AST
- Handle operator precedence, parentheses
- Write 15-20 parsing tests

**Task 1.3: Type Checker (2 days)**
- Implement type inference for expressions
- Validate path resolution (`target.bar.energy` exists)
- Check type compatibility (can't assign vec2i to scalar)
- Write 20-25 type validation tests

**Task 1.4: Expression Evaluator (2 days)**
- Implement AST execution (visitor pattern)
- GPU tensor operations (via PyTorch)
- Execution context (bars, vfs, temporal state)
- Write 15-20 evaluation tests

**Success Criteria:**
- ✅ 60+ tests passing
- ✅ Can parse all operator types from VARIABLE_SUBSYSTEM.md
- ✅ Type checking catches invalid paths at compile-time
- ✅ Evaluator executes expressions on GPU tensors

---

## Phase 2: VFS Profiles (Dynamic) (5-6 days)

**Goal:** Extend VFS from Phase 1 (static variables) to Phase 2 (expression-based, dynamic variables).

**Dependencies:** Phase 1 (Expression Language)

### Deliverables

```
src/townlet/vfs/
├── schema.py               # EXTEND: Add expression field, reference types
├── registry.py             # EXTEND: Scoped storage (global/agent/item)
├── observation_builder.py  # EXTEND: Include VFS in obs
└── profiles.py             # NEW: VFS profile compilation

src/townlet/config/
└── vfs_profiles_config.py  # NEW: DTOs for vfs_profiles.yaml

configs/test/vfs_smoke/
└── vfs_profiles.yaml       # Test profiles with expressions

tests/test_townlet/unit/vfs/
├── test_profiles_dto.py            # Config loading
├── test_expression_variables.py    # Expression-based variables
├── test_reference_types.py         # agent_ref, item_ref, etc.
└── test_scoped_registry.py         # Global/agent/item storage
```

### Tasks

**Task 2.1: VFS Profiles DTOs (1 day)**
- Create `vfs_profiles_config.py` (GlobalVFSProfileConfig, AgentVFSProfileConfig, ItemVFSProfileConfig)
- Schema validation (expression XOR initial_value)
- Reference type support
- Write 10-15 DTO tests

**Task 2.2: Scoped Registry (2 days)**
- Extend `VariableRegistry` for global/agent/item scopes
- Separate storage: `global_storage`, `agent_storage`, `item_storage`
- Access control per scope
- Write 15-20 registry tests

**Task 2.3: Expression Evaluation Integration (2 days)**
- Wire expression evaluator into VFS
- Topological sort for dependency ordering
- Handle circular dependency detection
- Write 15-20 evaluation tests

**Task 2.4: Observation Builder (1 day)**
- Include VFS fields in observations
- Fixed slot allocation for item VFS (3 slots × 5 profiles)
- Masking for empty slots
- Write 10-15 obs builder tests

**Success Criteria:**
- ✅ 50+ tests passing
- ✅ VFS variables can use expressions (`bar["energy"] + 0.05`)
- ✅ Reference types work (`agent_ref`, `item_ref`)
- ✅ obs_dim stable across levels (regression tests pass)

---

## Phase 3: Effects System (7-9 days)

**Goal:** Implement Effects as the command pipeline foundation for all simulation behavior.

**Dependencies:** Phase 1 (Expression Language), Phase 2 (VFS Profiles)

### Deliverables

```
src/townlet/effects/
├── __init__.py
├── schema.py               # EffectDef, ActiveEffect, CommandNode
├── catalog.py              # Effect catalog loading/compilation
├── executor.py             # Command pipeline interpreter
├── manager.py              # ActiveEffect lifecycle (tick, spawn, despawn)
└── context.py              # Runtime execution context

src/townlet/config/
└── effects_config.py       # NEW: DTOs for effects.yaml

configs/test/effects_smoke/
└── effects.yaml            # Test effects (ate_food, wet, etc.)

tests/test_townlet/unit/effects/
├── test_effects_dto.py            # Config loading
├── test_catalog_compilation.py    # Effect compilation
├── test_command_pipeline.py       # Command execution
├── test_effect_lifecycle.py       # Spawn/tick/despawn
├── test_reapply_policies.py       # Stack/renew/merge/replace
└── test_integration.py            # Full effect system
```

### Tasks

**Task 3.1: Effects DTOs & Catalog (2 days)**
- Create `effects_config.py` (EffectDefinitionConfig, EffectsConfig)
- Schema validation (reapply_policy required, etc.)
- Catalog compilation (effects.yaml → CompiledEffectCatalog)
- Write 15-20 DTO/catalog tests

**Task 3.2: Command Parser & Compiler (2 days)**
- Parse command YAML to CommandNode AST
- Compile expressions within commands (`value:` fields)
- Type checking for command targets
- Write 20-25 command compilation tests

**Task 3.3: Command Executor (2 days)**
- Implement command execution (modify, spawn_effect, spawn_item, if, for_each, etc.)
- Path resolution through execution context
- GPU tensor mutations
- Write 20-25 execution tests

**Task 3.4: EffectManager Runtime (2 days)**
- ActiveEffect lifecycle tracking
- Spawn/tick/despawn logic
- Reapply policy implementation (stack/renew/merge/replace)
- Scoped storage (global/agent/item/affordance effects)
- Write 15-20 manager tests

**Task 3.5: Environment Integration (1 day)**
- Wire EffectManager into VectorizedHamletEnv
- Call `effect_manager.tick()` each step
- Integration test with effects_smoke
- Write 5-10 integration tests

**Success Criteria:**
- ✅ 75+ tests passing
- ✅ Can load effects_smoke/effects.yaml
- ✅ All command types execute correctly
- ✅ Reapply policies work (stack/renew/merge/replace)
- ✅ Effects integrated into environment step loop

---

## Phase 4: Items System (8-10 days)

**Goal:** Implement Items using Effects for all interactions (clean from day 1, no opaque dicts).

**Dependencies:** Phase 2 (VFS Profiles), Phase 3 (Effects)

### Deliverables

```
src/townlet/items/
├── __init__.py
├── manager.py              # ItemManager (spawn/despawn, lifecycle)
├── inventory.py            # Agent inventory state
└── instance.py             # ItemInstance dataclass

src/townlet/config/
└── items_config.py         # NEW: DTOs for items.yaml

configs/test/items_smoke/
├── items.yaml              # Item catalog (experiment-level)
├── vfs_profiles.yaml       # Item VFS profiles
├── effects.yaml            # Item-related effects
└── levels/L0_smoke/
    └── items.yaml          # Item appearance (spawn rules)

tests/test_townlet/unit/items/
├── test_items_dto.py              # Config loading
├── test_item_manager.py           # ItemManager lifecycle
├── test_inventory.py              # Agent inventory state
├── test_item_interactions.py      # Pickup/use/drop with Effects
└── test_integration.py            # Full items system

tests/test_townlet/integration/
└── test_items_smoke_full.py       # End-to-end training with items
```

### Tasks

**Task 4.1: Items DTOs (2 days)**
- Create `items_config.py` (ItemTypeConfig, ItemsCatalogConfig, ItemsAppearanceConfig)
- Experiment-level vs level-level split
- Interaction commands (using Effects)
- Write 15-20 DTO tests

**Task 4.2: ItemManager (3 days)**
- ItemInstance dataclass
- Spawn/despawn logic
- Lifecycle management (duration, cooldown)
- Position tracking (spatial/aspatial)
- Item VFS state allocation
- Write 20-25 manager tests

**Task 4.3: Inventory Integration (2 days)**
- Agent inventory state ([batch, max_items_per_agent] slots)
- Pickup/drop mechanics
- Inventory overflow policy (DENY_PICKUP from edge-case-policies.md)
- Write 15-20 inventory tests

**Task 4.4: Action Handlers (2 days)**
- GET action (world → inventory)
- USE_SLOT_N actions (trigger Effects)
- DROP_SLOT_N actions (inventory → world)
- Action masking (GET masked when inventory full, etc.)
- Write 15-20 action handler tests

**Task 4.5: Environment Integration (1 day)**
- Wire ItemManager into VectorizedHamletEnv
- Item spawn scheduler
- Items in observations (via VFS)
- Integration test with items_smoke
- Write 5-10 integration tests

**Success Criteria:**
- ✅ 70+ tests passing
- ✅ items_smoke config loads and compiles
- ✅ Agents can pickup/use/drop items
- ✅ Items spawn/despawn with lifecycle rules
- ✅ Item interactions use Effects (no opaque dicts)
- ✅ Full training loop works with items

---

## Phase 5: Affordance Migration (3-4 days)

**Goal:** Migrate existing affordances from EffectPipeline to Effects system.

**Dependencies:** Phase 3 (Effects)

### Deliverables

```
src/townlet/config/
└── effect_pipeline.py      # DELETE (deprecated)

configs/default_curriculum/
└── levels/*/affordances.yaml  # MIGRATE to Effects syntax

tests/test_townlet/unit/affordances/
└── test_affordance_effects.py  # Updated for Effects
```

### Tasks

**Task 5.1: Schema Migration (1 day)**
- Update affordance DTOs to use Effects commands
- Remove old EffectPipeline references
- Write migration script for existing configs

**Task 5.2: Config Updates (2 days)**
- Migrate all curriculum level affordances.yaml files
- Convert EffectPipeline to Effects commands
- Update test fixtures

**Task 5.3: Code Cleanup (1 day)**
- Delete `effect_pipeline.py`
- Remove EffectPipeline from imports
- Verify all tests pass with new system

**Success Criteria:**
- ✅ All curriculum levels migrated
- ✅ EffectPipeline code deleted
- ✅ Zero regressions in existing tests
- ✅ Affordances use unified Effects system

---

## Phase 6: Integration & Testing (4-5 days)

**Goal:** End-to-end testing, performance validation, documentation.

**Dependencies:** All previous phases

### Deliverables

```
tests/test_townlet/integration/
├── test_world_compiler_full.py     # Complete World Compiler pipeline
├── test_expression_vfs_effects.py  # Expression → VFS → Effects flow
├── test_items_effects_cascade.py   # Items → Effects → Cascades
└── test_curriculum_compatibility.py # All levels still work

docs/config-schemas/
├── expressions.md          # Expression language reference
├── vfs-profiles.md         # VFS profiles schema
├── effects.md              # Effects catalog schema
└── items.md                # Items schema

docs/guides/
└── world-compiler-guide.md # User guide for World Compiler
```

### Tasks

**Task 6.1: Integration Tests (2 days)**
- Test complete compilation pipeline
- Test expression evaluation across VFS/Effects/Items
- Test complex interactions (food poisoning chain example)
- Write 10-15 integration tests

**Task 6.2: Performance Validation (1 day)**
- Benchmark expression evaluation overhead
- Profile effect execution in tight loop
- Ensure <5% performance regression vs baseline
- Document performance characteristics

**Task 6.3: Documentation (2 days)**
- Expression language reference (all operators)
- VFS profiles schema documentation
- Effects catalog schema documentation
- Items schema documentation
- World Compiler user guide

**Success Criteria:**
- ✅ 15+ integration tests passing
- ✅ <5% performance regression
- ✅ Complete documentation suite
- ✅ All curriculum levels pass full training

---

## Milestone Summary

| Phase | Duration | Tests | Components |
|-------|----------|-------|------------|
| **Phase 1: Expression Language** | 6-8 days | 60+ | Parser, Type Checker, Evaluator |
| **Phase 2: VFS Profiles** | 5-6 days | 50+ | Dynamic variables, References |
| **Phase 3: Effects System** | 7-9 days | 75+ | Commands, Catalog, Runtime |
| **Phase 4: Items System** | 8-10 days | 70+ | Manager, Inventory, Actions |
| **Phase 5: Affordance Migration** | 3-4 days | 0 (existing) | Config migration |
| **Phase 6: Integration** | 4-5 days | 15+ | E2E tests, Docs |
| **TOTAL** | **28-36 days** | **270+** | **Complete World Compiler** |

---

## Critical Path

```
Week 1-2:  Phase 1 (Expression Language)
              ↓
Week 2-3:  Phase 2 (VFS Profiles)
              ↓
Week 3-5:  Phase 3 (Effects System)
              ↓
Week 5-7:  Phase 4 (Items System)
              ↓
Week 7:    Phase 5 (Affordance Migration) + Phase 6 (Integration)
```

**Parallelization Opportunity:** Phase 2 (VFS) and Phase 3 (Effects) have minimal dependencies after Phase 1. Could run in parallel with two developers (reduce 2-3 days).

---

## Risk Assessment

### High Risk Areas

**1. Expression Language Performance (Phase 1)**
- **Risk:** AST evaluation too slow for tight loop
- **Mitigation:**
  - Profile early (Task 1.4)
  - Consider JIT compilation if needed
  - Cache compiled expressions

**2. VFS Circular Dependencies (Phase 2)**
- **Risk:** Infinite loops in variable dependencies
- **Mitigation:**
  - Topological sort at compile-time
  - Compiler error on cycles
  - Explicit dependency declaration

**3. Effects State Synchronization (Phase 3)**
- **Risk:** Effect state diverges from entity state
- **Mitigation:**
  - Assertions on state invariants
  - Checkpoint roundtrip tests
  - Clear ownership model (EffectManager owns effect state)

**4. obs_dim Stability (Phase 2 + Phase 4)**
- **Risk:** Adding VFS/Items breaks checkpoint compatibility
- **Mitigation:**
  - Fixed slot allocation (3 items × 5 profiles = 15 dims)
  - Dimension regression tests (already written)
  - Compile-time obs_dim validation

### Medium Risk Areas

**5. Type System Complexity (Phase 1)**
- **Risk:** Type inference gets too complex
- **Mitigation:**
  - Start simple (primitives only)
  - Add reference types incrementally
  - Comprehensive type checker tests

**6. Migration Effort (Phase 5)**
- **Risk:** Manual config migration error-prone
- **Mitigation:**
  - Write automated migration script
  - Validate before/after configs produce same behavior
  - Test migrated configs thoroughly

---

## Success Criteria (Overall)

### Technical
- ✅ 270+ tests passing across all phases
- ✅ <5% performance regression vs baseline
- ✅ All curriculum levels compile and train
- ✅ Checkpoint compatibility maintained (obs_dim stable)
- ✅ Zero backwards compatibility code (pre-release freedom)

### Architectural
- ✅ Expression language powers VFS, Effects, and DAC
- ✅ Effects replace all old mutation systems (EffectPipeline, opaque dicts)
- ✅ Items built cleanly on Effects (no retrofit)
- ✅ Type system prevents invalid paths at compile-time

### Documentation
- ✅ Complete schema docs for all config files
- ✅ Expression language reference (all operators)
- ✅ World Compiler user guide
- ✅ Migration guide for affordances

---

## Architectural Decisions (RESOLVED 2025-11-19)

### ✅ D1: Expression Language Implementation

**Decision:** Use pyparsing library

**Rationale:**

- **Faster to working code**: Phase 1 is already 6-8 days. Hand-written parser adds 2-3 days of parser debugging
- **Well-defined syntax**: Standard expressions (`target.bar.energy + 0.05`), not novel syntax
- **Mature library**: pyparsing used by Markdown parsers, SQL parsers. Well-tested.
- **Low dependency cost**: Pure Python, no native code. Simple `pip install pyparsing`
- **Pre-release freedom**: Can rewrite later if needed (no users to support)

**Implementation:** Task 1.2 will use pyparsing's `ParserElement` classes

---

### ✅ D2: VFS Expression Evaluation Timing

**Decision:** Hybrid (mark-and-sweep) with eager fallback option

**Rationale:**

- **Future vision alignment**: Enables user-controlled `expose_to_obs` per-variable in Phase 5+
- **Performance**: Only evaluate VFS variables that go into observations (marked at compile-time)
- **Implementation cost**: ~200 lines vs ~100 for eager (acceptable for long-term benefits)
- **Escape hatch**: Trivial fallback to eager if mark-and-sweep proves buggy

**Implementation:**

1. **Compile-time**: ObservationBuilder marks VFS variables that appear in obs spec
2. **Runtime**: VariableRegistry evaluates only marked variables (topological sort for dependencies)
3. **Fallback**: `eval_mode="eager"` flag to evaluate all variables if needed

**Acceptance Criteria for Hybrid:**

- ✅ Topological sort works (dependency tests pass)
- ✅ Performance ≥ Eager (profiling shows no regression)
- ✅ obs_dim stable (marked vars produce correct obs shape)

**Trigger for Eager Fallback:**

- ❌ Topological sort bugs persist after 2 days debugging
- ❌ Profiling shows >5% overhead vs Eager
- ❌ Need to log/inspect non-obs VFS variables

**Future Benefit:**

```yaml
# Phase 5+: User explicitly controls observability
agent_profile:
  distance_to_food:
    expression: "..."
    expose_to_obs: true   # ← Evaluated (marked)

  debug_helper:
    expression: "..."
    expose_to_obs: false  # ← Not evaluated (not marked)
```

---

### ✅ D3: Item VFS State Allocation

**Decision:** Pre-allocate max_items pool (fixed-size tensors)

**Rationale:**

- **GPU-native**: Fixed-size tensors required for efficient GPU computation
- **Tiny memory cost**: Even 1000 items × 10 profiles × 4 bytes = 40KB per batch
- **Architectural consistency**: Already pre-allocate affordance slots (14 affordances even if only 3 deployed)
- **Checkpoint serialization**: Fixed-size tensor dumps trivially to checkpoint

**Implementation:**

```python
# ItemManager allocates fixed pool
item_vfs = torch.zeros(max_items, num_profiles)  # [max_items, num_profiles]
active_items_mask = torch.zeros(max_items, dtype=torch.bool)  # [max_items]
```

**Reconsider only if:**

- Need 10,000+ items per world (unlikely for pedagogical environment)
- Profiling shows memory pressure (also unlikely)

---

### ✅ D4: Observable Effects in Observations

**Decision:** Effects write to VFS variables, VFS handles obs inclusion

**Rationale:**

- **Pedagogical clarity**: Students see semantic meaning (`is_wet: true`) not abstraction (`effect #7 active`)
- **Reuses existing mechanism**: VFS already handles obs inclusion with access control
- **Zero implementation cost**: Effects already need to mutate something (bars or VFS)
- **Teaching moment**: Distinction between implementation detail (effect active) vs observable state (effect's consequences)

**Implementation:**

```yaml
# effects.yaml
wet:
  on_apply:
    - modify: "vfs.agent.is_wet"
      value: true
  on_despawn:
    - modify: "vfs.agent.is_wet"
      value: false

# vfs_profiles.yaml
agent_profile:
  is_wet:
    type: bool
    scope: agent
    writers: [effects]
    readable_by: [agent]  # ← Goes into observations automatically
```

**Pedagogical Win:**

- ❌ Option A (Fixed slots): Students see "effect #7 active" - meaningless abstraction
- ❌ Option B (Summary): Students see "num_active_effects: 3" - also meaningless
- ✅ Option C (VFS): Students see "is_wet: true" - **semantic meaning**

---

## Execution Strategy

### Recommended: Subagent-Driven Development

**Approach:**

1. Use `superpowers:subagent-driven-development` skill
2. Execute one phase at a time
3. Review code after each task (fail-fast on issues)
4. Run tests between tasks (continuous validation)

**Commands:**

```bash
# Phase 1
"Use subagent-driven development to execute Phase 1: Expression Language Foundation from docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md"

# Phase 2
"Use subagent-driven development to execute Phase 2: VFS Profiles from docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md"

# ... etc
```

**Advantages:**

- Tight feedback loop (catch issues early)
- Can course-correct between tasks
- Easier to debug (smaller changes)

---

## Related Documentation

- **Effects System Design:** `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md`
- **Original Items Plan:** `docs/plans/2025-11-18-items-and-vfs-profiles.md`
- **VFS Expression Language:** `configs/reference_config/VARIABLE_SUBSYSTEM.md`
- **Edge Case Policies:** `docs/plans/vfs_uplift/edge-case-policies.md`

---

## Next Steps

**Before Implementation:**

1. ✅ Review this plan with team
2. ✅ Resolve architectural decisions (D1-D4) - **COMPLETE 2025-11-19**
3. ⬜ Create feature branch: `feature/world-compiler`
4. ⬜ Set up worktree (optional): `git worktree add`

**To Start Implementation:**

1. Read Phase 1 task list
2. Use subagent-driven development skill
3. Execute tasks sequentially with review checkpoints
4. Mark phases complete as tests pass

**Questions?**

- Stuck on implementation? Use `superpowers:systematic-debugging`
- Tests failing? Use `superpowers:test-driven-development`
- Need code review? Use `superpowers:requesting-code-review`
