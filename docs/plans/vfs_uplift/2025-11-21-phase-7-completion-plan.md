# Phase 7: World Compiler Completion Plan

**Status:** Ready for Implementation
**Date:** 2025-11-21
**Branch:** `vfs,effects,items` (continue) or `feature/phase-7-completion` (new)
**Owner:** World Compiler (T0 Pillar 3)
**Components:** Effects Commands + Items Integration

---

## Executive Summary

This plan completes the **critical scope gaps** identified in Phase 6 documentation review. The unified plan (`2025-11-19-unified-world-compiler-plan.md`) promised full implementation of Effects commands and seamless Items integration, but implementation stopped at ~80% completion.

**Gap Analysis:** `docs/plans/vfs_uplift/2025-11-21-scope-gap-analysis.md`

**Critical Gaps to Close:**
1. **Effects Commands** (4-6 days): spawn_effect, spawn_item, for_each not implemented
2. **Items Integration** (2-3 days): Item actions require manual configuration (should be automatic)
3. **Effects Lifecycle** (1 day): on_interrupt hook never executed

**Total Timeline:** 7-10 days (1.5-2 weeks)

**Success Criteria:**
- ✅ Effects can spawn other effects (cascade patterns)
- ✅ Effects can create items (world object generation)
- ✅ Effects can iterate over multiple targets (AoE patterns)
- ✅ Items automatically add GET/USE_SLOT_N/DROP_SLOT_N actions when enabled
- ✅ on_interrupt lifecycle hook executes properly
- ✅ All curriculum levels still compile and train
- ✅ Documentation reflects actual implementation status

---

## Architecture Context

### Current State (Phase 1-6)

```
✅ Expression Language    → Parser, type checker, evaluator working
✅ VFS Profiles           → Dynamic variables, scoped registry working
⚠️ Effects System         → Catalog, manager, SOME commands working
⚠️ Items System           → Manager, inventory working, integration incomplete
✅ Affordance Migration   → All levels migrated to Effects
```

### Target State (Phase 7)

```
✅ Effects System         → ALL commands working (spawn_effect, spawn_item, for_each)
✅ Items System           → Full automatic integration (actions auto-registered)
✅ Effects Lifecycle      → ALL hooks working (including on_interrupt)
```

### Component Dependencies

```
┌─────────────────────────────────────────┐
│       Effects Command Completion        │
│  - spawn_effect (needs EffectManager)   │
│  - spawn_item (needs ItemManager)       │
│  - for_each (needs iteration logic)     │
│  - on_interrupt (needs manager hooks)   │
└──────────────┬──────────────────────────┘
               │
               ├─────────────────────────────────┐
               ▼                                 ▼
    ┌─────────────────────┐        ┌─────────────────────┐
    │  EffectManager      │        │  ItemManager        │
    │  Integration        │        │  Integration        │
    └──────────┬──────────┘        └──────────┬──────────┘
               │                              │
               └──────────────┬───────────────┘
                              ▼
                   ┌──────────────────────┐
                   │  Action Space        │
                   │  Auto-Registration   │
                   └──────────────────────┘
```

---

## Phase 7.1: Effects Command Completion (4-6 days)

**Goal:** Implement the 3 critical Effects commands promised in unified plan but left stubbed.

**Current State:**
- `spawn_effect`: Stub returns dummy ID (`src/townlet/effects/executor.py:90-96`)
- `spawn_item`: Schema exists, not in executor
- `for_each`: Raises `NotImplementedError` (`src/townlet/effects/executor.py:120`)

**Dependencies:**
- ✅ CommandExecutor infrastructure exists
- ✅ EffectManager lifecycle works (spawn, tick, despawn)
- ✅ ItemManager exists with spawn/despawn methods

### Task 7.1.1: spawn_effect Command (2 days)

**Goal:** Effects can spawn other effects (cascade patterns like poisoning → nausea)

**Technical Design:**

```python
# effects.yaml example
poison:
  on_apply:
    - modify: "bar.health"
      value: "bar.health - 0.05"
  on_tick:
    - spawn_effect:
        effect_id: "nausea"
        target: "self"
        duration: 5
        intensity: 0.5
    - if:
        condition: "bar.health < 0.1"
        then:
          - spawn_effect:
              effect_id: "critical_condition"
              target: "self"
              duration: 10
```

**Implementation Steps:**

1. **Add effect_manager to ExecutionContext** (2 hours)
   - Update `ExecutionContext` signature to accept `effect_manager: EffectManager | None`
   - Pass effect_manager through all command execution paths
   - Update all callers (affordance_engine, item action handlers, etc.)

2. **Implement spawn_effect in CommandExecutor** (4 hours)
   - Replace stub at `executor.py:90-96`
   - Call `context.effect_manager.spawn_effect(effect_id, target_agent_idx, duration, params)`
   - Handle target resolution: "self" (self_index), "target" (target_index), explicit index
   - Return actual effect instance ID (not dummy)

3. **Add effect parameters support** (2 hours)
   - Allow passing parameters to spawned effect (intensity, stacks, custom data)
   - Parameters stored in ActiveEffect instance
   - Accessible via `context.effect_params` in spawned effect commands

4. **Write comprehensive tests** (4 hours)
   - Test spawn_effect with "self" target
   - Test spawn_effect with "target" target
   - Test spawn_effect with parameters (intensity, duration)
   - Test cascade patterns (effect A spawns effect B, B spawns C)
   - Test spawn_effect in affordance interactions
   - Test spawn_effect in item interactions

**Deliverables:**
- `src/townlet/effects/context.py` (updated with effect_manager)
- `src/townlet/effects/executor.py` (spawn_effect implemented)
- `tests/test_townlet/unit/effects/test_spawn_effect.py` (15-20 tests)
- `tests/test_townlet/integration/test_effect_cascades.py` (5-10 integration tests)

**Success Criteria:**
- ✅ spawn_effect creates actual effect instances
- ✅ Cascades work (effect spawning effect spawning effect)
- ✅ Target resolution works (self, target, explicit)
- ✅ Parameters passed correctly to spawned effects
- ✅ All tests pass (15-20 unit, 5-10 integration)

---

### Task 7.1.2: spawn_item Command (1.5 days)

**Goal:** Effects can create items in the world (loot drops, crafting results)

**Technical Design:**

```yaml
# effects.yaml example
crafting_complete:
  on_completion:
    - spawn_item:
        item_id: "wooden_axe"
        position: "self"  # or "target" or explicit [x, y]
        quantity: 1
        initial_state:
          durability: 1.0
          quality: 0.8

defeated_enemy:
  on_despawn:
    - spawn_item:
        item_id: "health_potion"
        position: "target"
        quantity: 1
```

**Implementation Steps:**

1. **Add item_manager to ExecutionContext** (1 hour)
   - Update `ExecutionContext` signature to accept `item_manager: ItemManager | None`
   - Pass item_manager through command execution paths

2. **Implement spawn_item in CommandExecutor** (3 hours)
   - Parse spawn_item command YAML (item_id, position, quantity, initial_state)
   - Resolve position: "self", "target", explicit coordinates, "random"
   - Call `context.item_manager.spawn_item(item_id, position, initial_state)`
   - Handle quantity > 1 (spawn multiple items)
   - Return spawned item IDs

3. **Add initial_state support to ItemManager** (2 hours)
   - Extend `ItemManager.spawn_item()` to accept initial VFS state
   - Set item VFS variables on spawn (durability, quality, charges, etc.)
   - Validate initial_state against item's VFS profile

4. **Write comprehensive tests** (3 hours)
   - Test spawn_item with "self" position
   - Test spawn_item with "target" position
   - Test spawn_item with explicit coordinates
   - Test spawn_item with initial_state (durability, quality)
   - Test spawn_item with quantity > 1
   - Test spawn_item in effect lifecycle (on_completion, on_despawn)

**Deliverables:**
- `src/townlet/effects/executor.py` (spawn_item implemented)
- `src/townlet/items/manager.py` (initial_state support)
- `tests/test_townlet/unit/effects/test_spawn_item.py` (15-20 tests)
- `tests/test_townlet/integration/test_item_generation.py` (5-10 integration tests)

**Success Criteria:**
- ✅ spawn_item creates actual item instances in world
- ✅ Position resolution works (self, target, explicit, random)
- ✅ initial_state sets item VFS variables correctly
- ✅ Quantity parameter spawns multiple items
- ✅ All tests pass (15-20 unit, 5-10 integration)

---

### Task 7.1.3: for_each Command (1.5 days)

**Goal:** Effects can iterate over multiple targets (AoE healing, group buffs)

**Technical Design:**

```yaml
# effects.yaml example
group_heal:
  on_apply:
    - for_each:
        collection: "nearby_agents"  # or "all_agents", "party_members"
        radius: 3.0
        iterator: "ally"
        body:
          - modify: "target.bar.health"
            value: "target.bar.health + 0.2"
          - spawn_effect:
              effect_id: "regeneration"
              target: "ally"
              duration: 10

poison_cloud:
  on_tick:
    - for_each:
        collection: "nearby_agents"
        radius: 2.0
        iterator: "victim"
        body:
          - modify: "target.bar.health"
            value: "target.bar.health - 0.05"
```

**Implementation Steps:**

1. **Design for_each schema** (2 hours)
   - Define collection types: "nearby_agents", "all_agents", "inventory_items", "active_effects"
   - Define iterator variable name (accessible in body as "target.<iterator>")
   - Define body as list of commands to execute per iteration
   - Add optional filters (radius, condition expression)

2. **Implement for_each in CommandExecutor** (4 hours)
   - Replace `NotImplementedError` at `executor.py:120`
   - Resolve collection based on type and filters
   - For each element, create child ExecutionContext with iterator binding
   - Execute body commands for each iteration
   - Handle empty collections gracefully

3. **Add collection resolution** (2 hours)
   - "nearby_agents": Get agents within radius of self/target
   - "all_agents": Iterate over all active agents
   - "inventory_items": Iterate over agent's inventory slots
   - "active_effects": Iterate over agent's active effects

4. **Write comprehensive tests** (4 hours)
   - Test for_each with nearby_agents (radius filter)
   - Test for_each with all_agents (no filter)
   - Test for_each with empty collection (no-op)
   - Test nested commands in body (modify, spawn_effect, if)
   - Test iterator variable resolution in expressions
   - Test for_each in different effect lifecycle stages

**Deliverables:**
- `src/townlet/effects/executor.py` (for_each implemented)
- `src/townlet/effects/collections.py` (NEW: collection resolution logic)
- `tests/test_townlet/unit/effects/test_for_each.py` (20-25 tests)
- `tests/test_townlet/integration/test_aoe_effects.py` (5-10 integration tests)

**Success Criteria:**
- ✅ for_each iterates over collections (nearby_agents, all_agents, etc.)
- ✅ Iterator variable accessible in body commands
- ✅ Filters work (radius, condition)
- ✅ Empty collections handled gracefully
- ✅ All tests pass (20-25 unit, 5-10 integration)

---

### Task 7.1.4: on_interrupt Lifecycle Hook (1 day)

**Goal:** Effects can respond to being interrupted by other effects

**Current State:**
- Schema supports on_interrupt
- EffectManager never calls on_interrupt hooks
- `src/townlet/effects/manager.py:137-200` has no execution path

**Technical Design:**

```yaml
# effects.yaml example
concentration_spell:
  reapply_policy: replace  # If replaced, trigger on_interrupt
  on_apply:
    - modify: "bar.energy"
      value: "bar.energy - 0.3"
  on_interrupt:
    - modify: "bar.mood"
      value: "bar.mood - 0.1"  # Penalty for losing concentration
    - spawn_effect:
        effect_id: "stunned"
        target: "self"
        duration: 2

meditation:
  reapply_policy: replace
  on_interrupt:
    - modify: "vfs.agent.is_meditating"
      value: false
```

**Implementation Steps:**

1. **Add interrupt detection to EffectManager** (2 hours)
   - Detect when reapply_policy causes effect removal (replace, merge)
   - Store interrupted effect ID before removal
   - Call `_execute_lifecycle_commands(effect, "on_interrupt")` before despawn

2. **Update reapply policy handlers** (2 hours)
   - `_apply_reapply_policy_replace()`: Trigger on_interrupt for old effect
   - `_apply_reapply_policy_merge()`: Trigger on_interrupt if merge consumes effect
   - Ensure on_interrupt runs BEFORE on_despawn (different semantics)

3. **Add interrupt reason to ExecutionContext** (1 hour)
   - Pass `interrupt_reason` to on_interrupt commands
   - Reasons: "replaced_by_effect", "manually_cancelled", "expired_early"
   - Accessible in expressions: `context.interrupt_reason`

4. **Write comprehensive tests** (3 hours)
   - Test on_interrupt when effect replaced (reapply_policy: replace)
   - Test on_interrupt vs on_despawn ordering (interrupt first, then despawn)
   - Test on_interrupt with interrupt_reason parameter
   - Test on_interrupt with spawn_effect (interrupt spawns new effect)
   - Test manual effect cancellation triggers on_interrupt

**Deliverables:**
- `src/townlet/effects/manager.py` (on_interrupt execution added)
- `src/townlet/effects/context.py` (interrupt_reason field)
- `tests/test_townlet/unit/effects/test_lifecycle_interrupt.py` (15-20 tests)

**Success Criteria:**
- ✅ on_interrupt executes when effect replaced
- ✅ on_interrupt executes BEFORE on_despawn
- ✅ interrupt_reason accessible in commands
- ✅ Reapply policies trigger on_interrupt correctly
- ✅ All tests pass (15-20 tests)

---

### Phase 7.1 Summary

**Deliverables:**
- 4 commands implemented (spawn_effect, spawn_item, for_each, on_interrupt)
- ~70-85 new tests (50-60 unit, 15-25 integration)
- Effects system feature-complete per unified plan

**Timeline:** 4-6 days (6 days if integration issues arise)

**Success Criteria:**
- ✅ All 4 commands work in isolation (unit tests)
- ✅ All 4 commands work in affordance interactions (integration tests)
- ✅ All 4 commands work in item interactions (integration tests)
- ✅ Cascade patterns work (effect → effect → effect)
- ✅ AoE patterns work (effect → multiple agents)
- ✅ Item generation patterns work (effect → item spawns)

---

## Phase 7.2: Items Integration Completion (2-3 days)

**Goal:** Items automatically add interaction actions when enabled (no manual configuration)

**Current State:**
- Item actions (GET, USE_SLOT_N, DROP_SLOT_N) exist as handlers
- Actions must be manually configured in `actions.yaml` (usability failure)
- Documentation incorrectly states actions are automatic

**Target State:**
- Enabling Items in config automatically adds GET/USE_SLOT_N/DROP_SLOT_N to action space
- Action indices predictable and stable
- Manual configuration still possible (overrides)

### Task 7.2.1: Action Space Auto-Registration (1.5 days)

**Goal:** Items system automatically registers actions when enabled

**Technical Design:**

```yaml
# training.yaml
items:
  enabled: true
  num_inventory_slots: 3
  # Actions automatically added:
  # - GET (global pickup action)
  # - USE_SLOT_0 (use item in slot 0)
  # - USE_SLOT_1
  # - USE_SLOT_2
  # - DROP_SLOT_0 (drop item from slot 0)
  # - DROP_SLOT_1
  # - DROP_SLOT_2
  # Total: 1 + 3 + 3 = 7 actions
```

**Implementation Steps:**

1. **Add auto-registration logic to action space builder** (3 hours)
   - Detect `items.enabled: true` in config
   - Generate GET action definition automatically
   - Generate USE_SLOT_N actions (N = num_inventory_slots)
   - Generate DROP_SLOT_N actions (N = num_inventory_slots)
   - Insert at predictable indices (after custom actions, before substrate actions)

2. **Define action index allocation policy** (2 hours)
   - Order: Custom actions → Item actions → Substrate actions
   - Item action order: GET → USE_SLOT_0..N-1 → DROP_SLOT_0..N-1
   - Document index stability guarantees (for checkpoint compatibility)
   - Add assertion: num_inventory_slots must match checkpoint value

3. **Add override mechanism** (2 hours)
   - Allow manual `actions.yaml` to override auto-generated actions
   - Use case: Custom GET action with different behavior
   - Merge auto-generated + manual (manual takes precedence)

4. **Update action masking** (1 hour)
   - GET masked when inventory full
   - USE_SLOT_N masked when slot empty
   - DROP_SLOT_N masked when slot empty
   - Ensure masking works with auto-registered actions

5. **Write comprehensive tests** (4 hours)
   - Test auto-registration with items.enabled: true
   - Test correct action indices (GET → USE → DROP order)
   - Test num_inventory_slots = 1, 3, 5 (different slot counts)
   - Test manual override of auto-generated actions
   - Test action masking (inventory full, slots empty)
   - Test items.enabled: false (no auto-registration)

**Deliverables:**
- `src/townlet/environment/action_config.py` (auto-registration logic)
- `src/townlet/universe/compiler.py` (wire auto-registration into compilation)
- `tests/test_townlet/unit/environment/test_item_action_registration.py` (20-25 tests)
- `tests/test_townlet/integration/test_items_auto_config.py` (5-10 integration tests)

**Success Criteria:**
- ✅ items.enabled: true auto-adds 1 + 2*N actions (N = num_inventory_slots)
- ✅ Action indices stable and predictable
- ✅ Manual actions.yaml can override auto-generated actions
- ✅ Action masking works correctly
- ✅ All tests pass (25-35 tests)

---

### Task 7.2.2: Documentation Updates (0.5 days)

**Goal:** Document automatic action registration clearly

**Implementation Steps:**

1. **Update items.md** (1 hour)
   - Add "Automatic Action Registration" section
   - Explain 1 + 2*N action formula
   - Show action index allocation table
   - Remove incorrect "NOT automatic" warning from review findings

2. **Update world-compiler-guide.md** (1 hour)
   - Add Items quick start with auto-registration
   - Show minimal config (just items.enabled: true)
   - Explain when to use manual configuration (rare)

3. **Add migration guide** (1 hour)
   - For users with manual actions.yaml
   - Explain how to remove manual config and use auto-registration
   - Document override patterns for custom behavior

4. **Update config schema examples** (1 hour)
   - Show auto-registration in `configs/templates/items_template/`
   - Add comments explaining automatic actions
   - Update all curriculum levels to use auto-registration

**Deliverables:**
- `docs/config-schemas/items.md` (updated with auto-registration)
- `docs/guides/world-compiler-guide.md` (Items quick start)
- `docs/guides/items-migration.md` (NEW: migration from manual config)
- `configs/templates/items_template/` (updated examples)

**Success Criteria:**
- ✅ Documentation clearly states items.enabled: true adds actions automatically
- ✅ Action index allocation documented with table
- ✅ Migration guide exists for manual config users
- ✅ Examples show minimal config (no manual actions.yaml)

---

### Phase 7.2 Summary

**Deliverables:**
- Auto-registration logic implemented
- ~30-45 new tests (25-35 unit, 5-10 integration)
- Documentation updated and accurate

**Timeline:** 2-3 days

**Success Criteria:**
- ✅ items.enabled: true works out-of-box (no manual config)
- ✅ Action space stable and predictable
- ✅ All curriculum levels compile with auto-registration
- ✅ Documentation accurate and clear

---

## Phase 7.3: Integration Testing & Validation (1 day)

**Goal:** Verify all Phase 7 changes work together and don't break existing functionality

### Task 7.3.1: End-to-End Integration Tests (0.5 days)

**Test Scenarios:**

1. **Effect Cascade Patterns** (2 hours)
   - Create config with poison → nausea → weakness cascade
   - Verify all effects spawn correctly
   - Verify cascade terminates (no infinite loops)
   - Verify effect parameters propagate

2. **Effect Item Generation** (1 hour)
   - Create config where defeating affordance spawns loot item
   - Verify item appears in world with correct initial_state
   - Verify agent can pickup spawned item

3. **AoE Effect Patterns** (1 hour)
   - Create config with for_each healing nearby agents
   - Verify all agents in radius affected
   - Verify agents outside radius unaffected
   - Verify empty collection handled

4. **Items Auto-Registration E2E** (1 hour)
   - Create new config with items.enabled: true, NO manual actions.yaml
   - Verify GET/USE_SLOT_N/DROP_SLOT_N actions exist
   - Verify agent can pickup, use, drop items
   - Verify action masking works

**Deliverables:**
- `tests/test_townlet/integration/test_phase7_complete.py` (10-15 tests)

---

### Task 7.3.2: Curriculum Regression Testing (0.5 days)

**Goal:** Ensure all existing curriculum levels still work

**Test Steps:**

1. **Compilation Tests** (1 hour)
   - Compile all 5 curriculum levels
   - Verify no compilation errors
   - Verify obs_dim unchanged (checkpoint compatibility)

2. **Smoke Training Tests** (2 hours)
   - Run 100 episodes of L0_0_minimal
   - Run 100 episodes of L0_5_dual_resource
   - Verify agents survive, no crashes
   - Verify rewards within expected range

3. **Items Smoke Test** (1 hour)
   - Enable items in L1_full_observability
   - Verify auto-registration adds 7 actions (3 slots)
   - Run 100 episodes
   - Verify agents can interact with items

**Deliverables:**
- Updated regression test suite
- Performance benchmark comparison (Phase 6 vs Phase 7)

---

### Phase 7.3 Summary

**Deliverables:**
- 10-15 integration tests
- Curriculum regression verified
- Performance benchmarks updated

**Timeline:** 1 day

**Success Criteria:**
- ✅ All Phase 7 features work together (no integration bugs)
- ✅ All curriculum levels compile and train
- ✅ No performance regressions (<5% overhead)
- ✅ Checkpoint compatibility maintained

---

## Phase 7.4: Documentation Polish (0.5 days)

**Goal:** Update all documentation to reflect Phase 7 completion

### Task 7.4.1: Fix Critical Documentation Errors (1 hour)

From review findings:

1. **expressions.md**
   - Fix operator precedence table (unary ops level 1)
   - Clarify division type inference
   - Add note about batched tensors

2. **vfs-profiles.md**
   - Add vector types (vec2f, vec3f, vecNi, vecNf) if implemented
   - Add reference types (agent_ref, item_ref) if implemented
   - Add "When Expressions Evaluate" section

3. **effects.md**
   - Remove "Not Yet Implemented" markers for spawn_effect, spawn_item, for_each
   - Add on_interrupt documentation with examples
   - Add implementation status table (all features implemented)

4. **items.md**
   - Update to reflect automatic action registration
   - Remove CRITICAL manual config warning
   - Add action index allocation table

5. **world-compiler-guide.md**
   - Update implementation status table (all features complete)
   - Add Phase 7 completion examples

---

### Task 7.4.2: Create Phase 7 Completion Summary (1 hour)

**File:** `docs/plans/vfs_uplift/PHASE-7-COMPLETE.md`

**Contents:**
- Summary of gaps closed
- Implementation highlights
- Test coverage statistics
- Performance impact analysis
- Breaking changes (if any)
- Migration notes

---

### Phase 7.4 Summary

**Deliverables:**
- 5 documentation files updated
- Phase 7 completion summary

**Timeline:** 0.5 days (4 hours)

**Success Criteria:**
- ✅ All documentation accurate and complete
- ✅ No "Not Yet Implemented" markers for implemented features
- ✅ Examples work as shown
- ✅ Phase 7 completion documented

---

## Milestone Summary

| Phase | Duration | Tests | Components |
|-------|----------|-------|------------|
| **Phase 7.1: Effects Commands** | 4-6 days | 70-85 | spawn_effect, spawn_item, for_each, on_interrupt |
| **Phase 7.2: Items Integration** | 2-3 days | 30-45 | Auto-registration, masking, docs |
| **Phase 7.3: Integration Testing** | 1 day | 10-15 | E2E tests, regression |
| **Phase 7.4: Documentation** | 0.5 days | 0 | Docs polish, completion summary |
| **TOTAL** | **7.5-10.5 days** | **110-145** | **Complete World Compiler** |

---

## Critical Path

```
Week 1 (Days 1-5):
  ├─ Phase 7.1.1: spawn_effect (2 days)
  ├─ Phase 7.1.2: spawn_item (1.5 days)
  └─ Phase 7.1.3: for_each (1.5 days)

Week 2 (Days 6-10):
  ├─ Phase 7.1.4: on_interrupt (1 day)
  ├─ Phase 7.2.1: Auto-registration (1.5 days)
  ├─ Phase 7.2.2: Docs update (0.5 days)
  ├─ Phase 7.3: Integration tests (1 day)
  └─ Phase 7.4: Documentation polish (0.5 days)
```

**Parallelization Opportunity:** Phase 7.2 (Items) can start after Phase 7.1.1 (spawn_effect) completes, reducing total time by 1-2 days with two developers.

---

## Risk Assessment

### High Risk Areas

**1. ExecutionContext Parameter Explosion (Phase 7.1)**
- **Risk:** Adding effect_manager, item_manager to ExecutionContext breaks all callers
- **Mitigation:**
  - Make parameters optional (default None)
  - Update callers incrementally (affordances first, then items)
  - Write adapter if needed to minimize changes

**2. Action Index Stability (Phase 7.2)**
- **Risk:** Auto-registration changes action indices, breaks checkpoints
- **Mitigation:**
  - Document index allocation policy clearly
  - Add assertion in checkpoint loading (verify num_inventory_slots matches)
  - Provide migration script if needed

**3. for_each Performance (Phase 7.1.3)**
- **Risk:** Iterating over many agents per effect tick causes slowdown
- **Mitigation:**
  - Profile early with 100 agents, 10 active effects
  - Add max_iterations parameter to prevent abuse
  - Consider batching if vectorization possible

**4. Cascade Infinite Loops (Phase 7.1.1)**
- **Risk:** Effect A spawns B, B spawns A → infinite recursion
- **Mitigation:**
  - Add spawn depth limit (max_cascade_depth = 10)
  - Track spawn chain in ExecutionContext
  - Raise error if depth exceeded

### Medium Risk Areas

**5. Item Spawn Position Resolution (Phase 7.1.2)**
- **Risk:** "random" position collides with existing items or walls
- **Mitigation:**
  - Add collision detection
  - Retry up to 3 times for random positions
  - Fall back to nearest empty cell

**6. on_interrupt Semantics (Phase 7.1.4)**
- **Risk:** Unclear when on_interrupt should fire vs on_despawn
- **Mitigation:**
  - Document clear semantics: on_interrupt = involuntary removal, on_despawn = natural expiry
  - Write tests covering all reapply policies
  - Add examples to docs

---

## Success Criteria (Overall)

### Technical
- ✅ 110-145 new tests passing
- ✅ All Effects commands work (spawn_effect, spawn_item, for_each, on_interrupt)
- ✅ Items automatically register actions (no manual config)
- ✅ All curriculum levels compile and train
- ✅ <5% performance regression vs Phase 6
- ✅ Checkpoint compatibility maintained

### Architectural
- ✅ Effects can cascade (spawn other effects)
- ✅ Effects can generate items (spawn_item)
- ✅ Effects can affect multiple targets (for_each)
- ✅ Items usable out-of-box (auto-registration)
- ✅ No manual configuration required for common use cases

### Documentation
- ✅ All 5 schema docs accurate (no "Not Yet Implemented" for implemented features)
- ✅ World Compiler guide reflects Phase 7 completion
- ✅ Examples work as shown
- ✅ Migration guide exists for manual config users

---

## Execution Strategy

### Recommended: Subagent-Driven Development (Per Phase)

**Approach:**

1. Execute Phase 7.1 (Effects Commands) as 4 separate tasks
   - Each task (spawn_effect, spawn_item, for_each, on_interrupt) assigned to subagent
   - Code review between tasks
   - Run tests after each task

2. Execute Phase 7.2 (Items Integration) as 2 tasks
   - Task 7.2.1 (auto-registration) and Task 7.2.2 (docs) can run sequentially
   - Code review before integration tests

3. Execute Phase 7.3 (Integration) as final validation
   - Manual verification of key scenarios
   - Performance benchmarking

4. Execute Phase 7.4 (Documentation) to close out

**Commands:**

```bash
# Phase 7.1.1
"Use subagent-driven development to execute Task 7.1.1: spawn_effect Command from docs/plans/vfs_uplift/2025-11-21-phase-7-completion-plan.md"

# Phase 7.1.2
"Use subagent-driven development to execute Task 7.1.2: spawn_item Command from docs/plans/vfs_uplift/2025-11-21-phase-7-completion-plan.md"

# ... etc
```

**Advantages:**
- Clear task boundaries (each command is self-contained)
- Can catch integration issues early
- Easier to debug (smaller changes per task)

---

## Technical Decisions

### D1: ExecutionContext Extension Strategy

**Decision:** Make effect_manager and item_manager optional parameters

**Rationale:**
- Backward compatibility with existing callers
- Gradual rollout (affordances first, then items)
- Easier testing (can test commands in isolation)

**Implementation:**
```python
@dataclass
class ExecutionContext:
    bars: dict[str, torch.Tensor]
    vfs_registry: Any | None
    self_index: int | None
    target_index: int | None
    effect_manager: Any | None = None  # NEW (optional)
    item_manager: Any | None = None    # NEW (optional)
    interrupt_reason: str | None = None  # NEW (optional)
```

---

### D2: Action Index Allocation Policy

**Decision:** Custom → Item → Substrate (fixed order)

**Rationale:**
- Custom actions first (user-defined, highest priority)
- Item actions next (auto-generated, stable positions)
- Substrate actions last (grid movement, always present)

**Allocation:**
```
Action indices:
[0 .. N_custom-1]:        Custom actions from actions.yaml
[N_custom]:               GET (if items enabled)
[N_custom+1 .. N_custom+N_slots]:     USE_SLOT_0 .. USE_SLOT_{N_slots-1}
[N_custom+N_slots+1 .. N_custom+2*N_slots]: DROP_SLOT_0 .. DROP_SLOT_{N_slots-1}
[N_custom+2*N_slots+1 .. end]:       Substrate actions (UP, DOWN, LEFT, RIGHT, etc.)
```

---

### D3: Cascade Depth Limit

**Decision:** max_cascade_depth = 10 (configurable)

**Rationale:**
- Prevents infinite loops (effect A spawns B, B spawns A)
- 10 levels sufficient for legitimate cascades (poison → nausea → weakness → stunned)
- Configurable for advanced users who need deeper chains

**Implementation:**
```python
# In ExecutionContext
spawn_depth: int = 0  # Incremented on each spawn_effect

# In CommandExecutor.execute_spawn_effect()
if context.spawn_depth >= MAX_CASCADE_DEPTH:
    raise RuntimeError(f"Effect cascade depth limit exceeded ({MAX_CASCADE_DEPTH})")

child_context = context.with_spawn_depth(context.spawn_depth + 1)
```

---

### D4: for_each Collection Types (Initial Set)

**Decision:** Support 4 collection types in Phase 7.1.3

1. **nearby_agents**: Agents within radius of self/target
2. **all_agents**: All active agents in environment
3. **inventory_items**: Items in agent's inventory slots
4. **active_effects**: Effects currently active on agent

**Rationale:**
- Covers 90% of AoE use cases
- Simple to implement (all data available in context)
- Can add more types later (party_members, affordances_in_range, etc.)

**Future Types:**
- party_members (requires party system)
- affordances_in_range (requires spatial queries)
- agents_with_effect (requires effect queries)

---

## Related Documentation

- **Gap Analysis:** `docs/plans/vfs_uplift/2025-11-21-scope-gap-analysis.md`
- **Review Findings:** `docs/plans/vfs_uplift/2025-11-21-phase-6-documentation-review-findings.md`
- **Unified Plan:** `docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md`
- **Phase 6 Summary:** `docs/plans/vfs_uplift/PHASE-6-COMPLETE.md`

---

## Appendix A: Test Coverage Breakdown

| Component | Unit Tests | Integration Tests | Total |
|-----------|-----------|-------------------|-------|
| spawn_effect | 15-20 | 5-10 | 20-30 |
| spawn_item | 15-20 | 5-10 | 20-30 |
| for_each | 20-25 | 5-10 | 25-35 |
| on_interrupt | 15-20 | 0 | 15-20 |
| Item auto-registration | 20-25 | 5-10 | 25-35 |
| Phase 7 E2E | 0 | 10-15 | 10-15 |
| **TOTAL** | **85-110** | **30-55** | **115-165** |

---

## Appendix B: Performance Targets

| Operation | Target | Rationale |
|-----------|--------|-----------|
| spawn_effect per call | <50 μs | Effect spawning is common (cascades) |
| spawn_item per call | <100 μs | Item spawning is rare (loot drops) |
| for_each iteration | <10 μs per agent | AoE effects run every tick |
| on_interrupt execution | <30 μs | Interrupts are edge cases |
| Overall Phase 7 overhead | <5% | Maintain Phase 6 performance |

---

## Appendix C: Breaking Changes

### Potential Breaking Changes (To Monitor)

1. **ExecutionContext signature change**
   - Impact: All command executors, affordance engine, item handlers
   - Mitigation: Optional parameters (default None)

2. **Action space indices shift**
   - Impact: Checkpoints with Items enabled
   - Mitigation: Assert num_inventory_slots matches at load time

3. **EffectManager spawn_effect API**
   - Impact: Any external code calling spawn_effect directly (unlikely)
   - Mitigation: Update callers, add deprecation warning if needed

### Non-Breaking Changes

- All new features (spawn_item, for_each, on_interrupt) are additive
- Documentation updates don't affect runtime behavior
- Test additions don't break existing tests

---

**Phase 7: World Compiler Completion - Ready for Implementation**

Part of T0 Pillar 3: World Compiler

Total Duration: 7.5-10.5 days (1.5-2 weeks)
Total New Tests: 110-145
Total New Features: 7 (4 commands + auto-registration + lifecycle hook + docs)
