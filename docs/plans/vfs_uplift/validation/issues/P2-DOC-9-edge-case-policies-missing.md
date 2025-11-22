# P2-DOC-9: Edge Case Policies Document Missing

**Priority:** P2 (Minor - Documentation Gap)
**Category:** Documentation
**Estimated Effort:** 2-3 hours
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

The VFS uplift validation plan requires an "Edge Case Policies" document defining how the system handles ambiguous situations, but this document doesn't exist.

**Expected Content:**
- VFS variable circular dependencies (how detected, error message)
- Item VFS overflow behavior (when max items exceeded)
- Effect cascade depth limits (MAX_CASCADE_DEPTH policy)
- Expression evaluation failures (division by zero, invalid references)
- Observation dimension stability (what happens if profiles change)

**Impact:**
- Developers lack authoritative reference for edge case handling
- Users may encounter undefined behavior
- **Low impact:** Code enforces policies, just not documented centrally

**Evidence:**
- Agent 7 (Documentation) report, section DOC-9
- Referenced in validation plan but file doesn't exist

---

## How to Fix

### Step 1: Create Edge Case Policies Document (2 hours)

**File:** `docs/architecture/edge-case-policies.md` (NEW)

```markdown
# Edge Case Policies

This document defines how HAMLET's VFS system handles ambiguous or exceptional situations.

## 1. VFS Expression Evaluation

### 1.1 Circular Dependencies

**Policy:** Compilation FAILS if circular dependencies detected.

**Detection:** Topological sort on dependency graph during VFS profile compilation.

**Example:**
```yaml
vfs_profiles:
  global_profile:
    var_a:
      type: float
      expression: "global.vfs.var_b + 1.0"
    var_b:
      type: float
      expression: "global.vfs.var_a + 1.0"  # ❌ Circular!
```

**Error Message:**
```
CompilationError: Circular dependency detected in VFS expressions:
  global.vfs.var_a → global.vfs.var_b → global.vfs.var_a
```

**Code:** `src/townlet/vfs/profiles.py:VFSProfileCompiler._build_dependency_graph()`

---

### 1.2 Division by Zero

**Policy:** Runtime returns `NaN`, logs warning, does NOT crash.

**Rationale:** Vectorized environments may have valid and invalid divisions in same batch.

**Example:**
```yaml
agent_profile:
  efficiency:
    type: float
    expression: "agent.bar.productivity / agent.bar.time_worked"
    # If time_worked == 0.0 → NaN
```

**Behavior:**
```python
# time_worked = torch.tensor([10.0, 0.0, 5.0])  # Batch of 3 agents
# Result: tensor([0.5, nan, 0.2])
# Warning logged: "Division by zero in expression: agent.bar.productivity / agent.bar.time_worked (env_ids=[1])"
```

**Code:** `src/townlet/world/expression/evaluator.py:ExpressionEvaluator.evaluate()`

---

### 1.3 Invalid Variable References

**Policy:** Compilation FAILS if reference path doesn't exist.

**Example:**
```yaml
agent_profile:
  bonus:
    type: float
    expression: "agent.bar.nonexistent_meter * 2.0"  # ❌ Invalid path
```

**Error Message:**
```
CompilationError: Unknown variable path: agent.bar.nonexistent_meter
  Available agent.bar variables: energy, health, satiation, money
  Did you mean: agent.bar.energy?
```

**Code:** `src/townlet/world/expression/type_checker.py:TypeChecker.check_path()`

---

### 1.4 Type Mismatches

**Policy:** Compilation FAILS if expression types don't match.

**Example:**
```yaml
agent_profile:
  flag:
    type: bool
    expression: "agent.bar.energy + 10.0"  # ❌ float expression for bool variable
```

**Error Message:**
```
CompilationError: Type mismatch for variable 'flag':
  Expected: bool
  Got: float (from expression: agent.bar.energy + 10.0)
```

**Code:** `src/townlet/world/expression/type_checker.py:TypeChecker.check_expression()`

---

## 2. Item VFS Management

### 2.1 Item Pool Overflow

**Policy:** When item pool exceeds `max_items`, spawning NEW items FAILS silently (returns None).

**Rationale:** Prevents GPU memory overflow, item spawning is best-effort.

**Example:**
```yaml
items:
  max_items: 100  # Global limit across all item types
```

**Behavior:**
```python
# If 100 items already exist:
new_item = item_manager.spawn_item("sword")
# new_item == None, no error raised
# Warning logged: "Item pool full (100/100), cannot spawn 'sword'"
```

**Code:** `src/townlet/items/manager.py:ItemManager.spawn_item()`

---

### 2.2 Item Profile Not Found

**Policy:** Compilation FAILS if item references non-existent vfs_profile.

**Example:**
```yaml
# items.yaml
items:
  item_types:
    sword:
      vfs_profile: "weapon"  # ❌ Profile doesn't exist in vfs_profiles.yaml
```

**Error Message:**
```
CompilationError: Item type 'sword' references unknown vfs_profile: 'weapon'
  Available profiles: consumable, armor
  Did you mean: armor?
```

**Code:** `src/townlet/universe/compiler.py:Stage3_CrossValidation`

---

### 2.3 Inventory Overflow

**Policy:** When agent inventory full, GET action MASKED (invalid action).

**Example:**
```yaml
items:
  max_items_per_agent: 3
```

**Behavior:**
```python
# Agent has 3 items, tries to pick up 4th:
# GET action mask = False (action disabled)
# If agent attempts GET anyway (policy bug), no-op occurs
```

**Code:** `src/townlet/items/inventory.py:Inventory.can_pickup()`

---

## 3. Effect System

### 3.1 Cascade Depth Limit

**Policy:** Effect cascades terminate after `MAX_CASCADE_DEPTH=10` levels.

**Rationale:** Prevents infinite recursion from spawn_effect → on_spawn → spawn_effect loops.

**Example:**
```yaml
# Infinite cascade (BAD DESIGN):
effects:
  recursive_spawn:
    on_spawn:
      - command: spawn_effect
        effect: "recursive_spawn"  # Spawns itself!
```

**Behavior:**
```
# Cascade: recursive_spawn (depth 1)
#   → spawn recursive_spawn (depth 2)
#     → spawn recursive_spawn (depth 3)
#       ...
#       → spawn recursive_spawn (depth 10)  ✅ Allowed
#         → spawn recursive_spawn (depth 11)  ❌ BLOCKED

Warning: Effect cascade depth limit reached (10). Blocking further spawn_effect calls.
  Effect: recursive_spawn
  Origin: env_id=0, agent_id=2
```

**Code:** `src/townlet/effects/manager.py:EffectManager._execute_commands()`

---

### 3.2 Invalid Effect References

**Policy:** Compilation FAILS if effect name doesn't exist in catalog.

**Example:**
```yaml
# affordances.yaml
affordances:
  - name: FOOD
    on_interact:
      - effect: "restore_energy"  # ❌ Effect not in effects.yaml
```

**Error Message:**
```
CompilationError: Affordance 'FOOD' references unknown effect: 'restore_energy'
  Available effects: heal, damage, poison
  Did you mean: heal?
```

**Code:** `src/townlet/universe/compiler.py:Stage3_CrossValidation`

---

## 4. Observation Management

### 4.1 Profile Changes After Compilation

**Policy:** Observation dimension FIXED at compile time. Runtime changes FORBIDDEN.

**Rationale:** Q-network expects fixed obs_dim. Changing profiles would break checkpoints.

**Example:**
```yaml
# Original vfs_profiles.yaml
agent_profile:
  gold:
    observation:
      enabled: true  # Contributes 1 dim to obs_dim

# If you change to enabled: false and recompile:
# ❌ Checkpoint transfer will FAIL (obs_dim mismatch)
```

**Error Message:**
```
CheckpointError: Observation dimension mismatch
  Expected: 29 (from checkpoint)
  Got: 28 (from config)

Likely cause: VFS profile changed (variable added/removed from observations)
Fix: Use same vfs_profiles.yaml or train new checkpoint from scratch
```

**Code:** `src/townlet/training/checkpoint_utils.py:load_checkpoint()`

---

### 4.2 Item VFS Masking

**Policy:** Non-existent items have ZERO observations (not NaN or random values).

**Rationale:** Prevents leaking uninitialized memory into observations.

**Example:**
```python
# Environment has 2 items (indices 0, 1), but max_items=5
# Item VFS observations for items 2, 3, 4 are ZEROED
# Shape: [batch_size, max_items, item_vfs_dim]
# Values: [..., [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
```

**Code:** `src/townlet/vfs/observation_builder.py:build_vfs_observation()`

---

## 5. Performance Constraints

### 5.1 VFS Evaluation Overhead

**Policy:** VFS evaluation must add <5% overhead to env.step() time.

**Measurement:** Benchmark with/without VFS evaluation.

**Enforcement:** Performance regression tests in CI.

**Example:**
```bash
# Run performance benchmark
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/performance/test_vfs_overhead.py

# Expected output:
# Baseline step: 1.23ms
# With VFS: 1.27ms
# Overhead: 3.2% ✅ (< 5% threshold)
```

**Code:** `tests/test_townlet/performance/test_component_benchmarks.py`

---

## 6. Checkpoint Serialization

### 6.1 Item VFS State Persistence

**Policy:** Item VFS state SHOULD be in checkpoints (currently NOT implemented - see P1-RUN-9).

**Expected Behavior:**
```python
# Save checkpoint with item state
checkpoint = {
    'registry': {
        'global_vfs': global_vfs_tensor,
        'agent_vfs': agent_vfs_tensor,
        'item_vfs': item_vfs_tensor,  # ✅ Should exist
    }
}
```

**Current Behavior:**
```python
# item_vfs NOT in checkpoints ❌
# Items respawn with default VFS values on resume
```

**Status:** OPEN (see issue P1-RUN-9)

---

## 7. Error Message Quality

### 7.1 Typo Suggestions

**Policy:** Compiler errors SHOULD suggest corrections using difflib.

**Current:**
```
CompilationError: Unknown variable: agent.bar.helth
Did you mean: agent.bar.health?
```

**Future Enhancement (P2-SUCCESS-1):** Use Levenshtein distance for better suggestions.

---

## Summary Table

| Edge Case | Detection | Failure Mode | Policy |
|-----------|-----------|--------------|--------|
| Circular VFS deps | Compile-time | Compilation error | FAIL LOUDLY |
| Division by zero | Runtime | NaN result | LOG WARNING, continue |
| Invalid reference | Compile-time | Compilation error | FAIL LOUDLY |
| Type mismatch | Compile-time | Compilation error | FAIL LOUDLY |
| Item pool overflow | Runtime | Spawn returns None | LOG WARNING, continue |
| Item profile missing | Compile-time | Compilation error | FAIL LOUDLY |
| Inventory overflow | Runtime | Mask GET action | PREVENT GRACEFULLY |
| Cascade depth limit | Runtime | Block spawn_effect | LOG WARNING, continue |
| Invalid effect ref | Compile-time | Compilation error | FAIL LOUDLY |
| Profile change | Load checkpoint | Checkpoint error | FAIL LOUDLY |
| Item VFS masking | Runtime | Zero non-existent items | AUTOMATIC |

---

## Design Principles

1. **Fail Fast at Compile Time:** Invalid configs should never reach runtime
2. **Graceful Degradation at Runtime:** Batch processing shouldn't crash on edge cases
3. **Clear Error Messages:** Users should know exactly what's wrong and how to fix it
4. **Type Safety:** Use Pydantic and type checker to prevent invalid states
5. **No Silent Failures:** All edge cases log warnings or errors
```

### Step 2: Link from Architecture Docs (15 minutes)

Add reference to edge-case-policies.md in relevant architecture docs:
- `docs/architecture/COMPILER_ARCHITECTURE.md`
- `docs/config-schemas/vfs-profiles.md`
- `docs/config-schemas/effects.md`

---

## Acceptance Criteria

- [ ] `docs/architecture/edge-case-policies.md` created
- [ ] All 7 edge case categories documented
- [ ] Each policy includes: description, example, error message, code reference
- [ ] Summary table provided
- [ ] Design principles documented
- [ ] Linked from relevant docs

---

## Files to Create/Modify

1. `docs/architecture/edge-case-policies.md` (NEW) - Complete policy document
2. `docs/architecture/COMPILER_ARCHITECTURE.md` - Add link to edge case policies
3. `docs/config-schemas/vfs-profiles.md` - Add link for VFS edge cases
4. `docs/config-schemas/effects.md` - Add link for effect edge cases

---

## Related Issues

- Related: P2-SUCCESS-1 (typo suggestions)
- Related: P1-RUN-9 (checkpoint serialization)
- Blocks: None (documentation gap)

---

## Notes

- **Low priority:** Policies already enforced in code, just not documented centrally
- **Pedagogical value:** Helps developers understand "why" design decisions were made
- Content should be extracted from existing code comments and error handling
- Can use grep to find existing edge case handling: `grep -r "MAX_CASCADE_DEPTH\|circular\|overflow" src/townlet/`
