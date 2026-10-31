# [ITEM-8] Spawn Conditions (VFS Predicates)

**Priority:** P1 (Important)
**Category:** Items
**Status:** MISSING
**Effort:** 1 day

## Description

Spawn rules lack conditional gating based on VFS variables or game state. Cannot express "spawn rain items only when vfs:is_raining == true" or "spawn enemies only when vfs:danger_level > 3". All spawn rules execute unconditionally once schedule requirements are met.

## Current State

**Working:** Spawn rules execute based on schedule (periodic, time window, etc.)

**Missing:** No way to gate spawning on runtime conditions:
- Cannot check VFS variables: `when: "vfs:is_raining"`
- Cannot check bar states: `when: "bar:energy < 0.3"`
- Cannot check temporal state: `when: "temporal:is_night"`
- Cannot combine conditions: `when: "vfs:is_raining and temporal:is_night"`

**Use cases blocked:**
- Weather-dependent spawns (rain items only during rain)
- Time-based spawns (nocturnal creatures only at night)
- Resource-dependent spawns (rare items only when scarcity high)
- State-based spawns (enemies only during combat mode)

## Required Implementation

### 1. Add Condition Field to SpawnRule Schema (30 minutes)

**File:** `src/townlet/items/schema.py`

**Changes:**
```python
@dataclass
class SpawnRule:
    item_type: str
    quantity: int
    placement: PlacementSpec
    schedule: ScheduleSpec
    vfs_profile: Optional[str] = None
    initial_state: Optional[Dict[str, Any]] = None

    # NEW: Spawn condition
    when: Optional[str] = None  # VFS expression, e.g., "vfs:is_raining"
```

### 2. Compile Spawn Conditions (2-3 hours)

**File:** `src/townlet/universe/compiler.py`

**Changes:**
```python
def _compile_items_catalog(self):
    """Compile items catalog including spawn condition expressions."""
    for spawn_rule in items_catalog.spawn_rules:
        if spawn_rule.when:
            # Compile condition expression (when AST exists)
            # For now: Store expression string, evaluate at runtime
            spawn_rule.compiled_condition = spawn_rule.when
```

**Note:** Once COMP-7/8/9 (expression AST) implemented, compile conditions to AST here.

### 3. Evaluate Spawn Conditions at Runtime (4-5 hours)

**File:** `src/townlet/items/manager.py`

**Changes:**
```python
def _should_spawn(self, spawn_rule) -> bool:
    """Check if spawn rule conditions are met."""

    # Check schedule (existing)
    if not self._schedule_allows_spawn(spawn_rule):
        return False

    # Check max_total limit (existing)
    if self._max_total_reached(spawn_rule):
        return False

    # NEW: Check spawn condition
    if spawn_rule.when:
        condition_met = self._evaluate_spawn_condition(spawn_rule.when)
        if not condition_met:
            return False

    return True

def _evaluate_spawn_condition(self, condition_expr: str) -> bool:
    """Evaluate spawn condition expression."""
    from townlet.vfs.evaluator import VFSEvaluator

    # Build evaluation context
    context = {
        "vfs": self.vfs_registry,
        "bars": self.bar_manager,
        "temporal": self.temporal_state,
        "tick": self.current_tick
    }

    # Evaluate condition (returns bool)
    result = VFSEvaluator.evaluate_expression(condition_expr, context)
    return bool(result)
```

### 4. Integration with VFS System (2-3 hours)

**Evaluation Context:**
- Global VFS variables: `vfs:is_raining`, `vfs:danger_level`
- Bar states: `bar:energy`, `bar:health` (avg across agents)
- Temporal state: `temporal:is_night`, `temporal:current_tick`
- Custom predicates: `vfs:player_count > 10`

**Path Resolution:**
- Use existing VFSEvaluator path resolution
- Support scoped paths: `vfs:global.is_raining`, `vfs:agent[0].energy`
- Support comparisons: `vfs:danger_level > 3`, `bar:energy < 0.3`
- Support boolean logic: `vfs:is_raining and temporal:is_night`

### 5. Testing (4-5 hours)

**Test file:** `tests/test_townlet/unit/items/test_spawn_conditions.py` (new)

**Test cases:**
- Simple conditions: `vfs:is_raining` (boolean check)
- Comparisons: `vfs:danger_level > 3` (numeric comparison)
- Boolean logic: `vfs:is_raining and temporal:is_night` (compound conditions)
- Condition prevents spawn when false
- Condition allows spawn when true
- Missing VFS variable handled gracefully (error or default false)
- Condition evaluation efficient (no overhead for unconditional spawns)

## Acceptance Criteria

- [ ] SpawnRule schema has `when` field for condition expressions
- [ ] UniverseCompiler compiles spawn conditions (stores expression string)
- [ ] ItemManager evaluates spawn conditions before spawning
- [ ] Conditions can reference VFS variables (vfs:*)
- [ ] Conditions can reference bar states (bar:*)
- [ ] Conditions can reference temporal state (temporal:*)
- [ ] Conditions support comparisons (>, <, ==, !=, >=, <=)
- [ ] Conditions support boolean logic (and, or, not)
- [ ] Spawn blocked when condition evaluates to false
- [ ] Spawn allowed when condition evaluates to true
- [ ] 15+ tests covering condition evaluation and spawn gating
- [ ] Documentation updated with spawn condition examples

## Evidence

**Source Report:** gap-report-final.md (lines 55-68), gap-report-items.md
**Related Requirements:** ITEM-6 (advanced spawn rules), VFS expression system
**Schema:** `src/townlet/items/schema.py:SpawnRule`

## Implementation Notes

**Why P1 (not P0):** Spawn conditions are advanced feature for Phase 4+ scenarios. Phase 1-3 curriculum levels use unconditional spawning (periodic schedules sufficient).

**Design Decisions:**

1. **Expression Language Integration:**
   - Reuse VFSEvaluator for condition evaluation (consistent with VFS system)
   - Once COMP-7/8/9 implemented, compile conditions to AST at compile time
   - For now: String-based evaluation (consistent with current VFS expressions)

2. **Evaluation Context:**
   - Spawn conditions evaluate in global context (not per-agent)
   - Access to VFS registry, bar manager, temporal state
   - No access to individual agent states (spawn is world-level event)

3. **Performance:**
   - Condition evaluation only for spawn rules with `when` field
   - Cache compiled conditions for repeated evaluation
   - Efficient early-exit: schedule check → max_total check → condition check

**Example Usage:**

```yaml
# items_catalog.yaml
spawn_rules:
  - item_type: "rain_boots"
    quantity: 5
    placement:
      mode: "random"
    schedule:
      type: "periodic"
      period: 100
    when: "vfs:is_raining"  # Only spawn rain boots when raining

  - item_type: "enemy_goblin"
    quantity: 3
    placement:
      mode: "grid"
      spacing: 10
    schedule:
      type: "time_window"
      start_tick: 1000
      end_tick: 2000
    when: "vfs:danger_level > 3 and temporal:is_night"  # Tough enemies at night when dangerous

  - item_type: "health_potion"
    quantity: 10
    placement:
      mode: "random"
    schedule:
      type: "periodic"
      period: 50
    when: "bar:health < 0.5"  # More potions when agents are low health
```

**Integration with ITEM-6 (Advanced Spawn Rules):**
- Conditions work with all placement modes (random, fixed, grid, scripted)
- Conditions work with all schedule types (periodic, time_window, poisson, normal)
- Conditions checked after schedule but before placement
- Order: Schedule → Max Total → Condition → Placement

**Error Handling:**
- Undefined VFS variables: Default to false (don't spawn)
- Malformed expressions: Raise compile-time error
- Type errors (comparing string to number): Raise runtime error with clear message

## References

- Schema: `src/townlet/items/schema.py:SpawnRule` (add `when` field)
- Manager: `src/townlet/items/manager.py:_should_spawn()` (add condition check)
- Evaluator: `src/townlet/vfs/evaluator.py` (reuse expression evaluation)
- Test file: `tests/test_townlet/unit/items/test_spawn_conditions.py` (to be created)
- Documentation: `docs/config-schemas/items.md` (add spawn condition examples)
- Related: ITEM-6 (advanced spawn rules), VFS expression language
