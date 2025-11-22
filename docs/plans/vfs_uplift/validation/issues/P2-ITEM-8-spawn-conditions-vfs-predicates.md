# P2-ITEM-8: Item Spawn Conditions VFS Predicate Support

**Priority:** P2 (Minor - Can Defer)
**Category:** Items System
**Estimated Effort:** 2 days
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

Item spawn conditions exist but lack documentation/testing for VFS-based predicates (e.g., "only spawn sword if agent.vfs.combat_level > 5").

**Current State:**
- Basic spawn conditions mechanism exists
- Can specify `conditions:` field in spawn rules
- Missing: Documentation of VFS predicate syntax
- Missing: Tests for VFS-based spawn conditions

**Impact:**
- Users cannot create VFS-conditional item spawning
- Limits gameplay complexity (no level-gated items)
- **Low impact:** Most use cases don't require conditional spawning

**Evidence:**
- Agent 4 (Items) report, section ITEM-8
- Code exists but undocumented/untested

---

## How to Fix

### Step 1: Document VFS Predicate Syntax (1 hour)

**File:** `docs/config-schemas/items.md`

Add section:

```markdown
### Spawn Conditions

Control when items spawn based on VFS state:

```yaml
item_types:
  legendary_sword:
    spawn_rules:
      placement:
        strategy: random
      conditions:
        - "global.vfs.day_of_week > 0.85"  # Only spawn on weekends
        - "count(agents where agent.vfs.combat_level > 5) >= 2"  # At least 2 high-level agents
```

#### Condition Syntax

Conditions use the VFS expression language with boolean result.

**Examples:**
- `"global.vfs.time_of_day > 0.5"` - Only afternoon/evening
- `"mean(agents.vfs.gold) > 100"` - Average wealth threshold
- `"exists(agent where agent.bar.health < 0.2)"` - Any low-health agent
```

### Step 2: Implement VFS Predicate Evaluation (4 hours)

**File:** `src/townlet/items/manager.py`

```python
def should_spawn_item(self, item_type: str) -> torch.Tensor:
    """Evaluate spawn conditions for item type.

    Returns:
        bool tensor [n_envs] indicating which envs should spawn item
    """
    spawn_rules = self.catalog.item_types[item_type].spawn_rules

    if not spawn_rules.conditions:
        return torch.ones(self.n_envs, dtype=torch.bool)  # Always spawn

    # Evaluate all conditions
    spawn_mask = torch.ones(self.n_envs, dtype=torch.bool)
    for condition_expr in spawn_rules.conditions:
        # Use VFS evaluator to compute condition
        result = self.vfs_evaluator.evaluate(condition_expr, self.context)

        # Result should be boolean tensor
        if result.dtype != torch.bool:
            result = result > 0.5  # Threshold for float → bool

        spawn_mask &= result  # AND all conditions

    return spawn_mask
```

### Step 3: Add Tests (2 hours)

**File:** `tests/test_townlet/unit/items/test_spawn_conditions.py` (NEW)

```python
def test_spawn_condition_vfs_predicate():
    """Verify items only spawn when VFS condition met."""
    # Setup: Item requires high energy
    config = {
        "items": {
            "energy_potion": {
                "vfs_profile": "potion",
                "spawn_rules": {
                    "placement": {"strategy": "random"},
                    "conditions": ["global.vfs.time_of_day > 0.5"]  # Only PM
                }
            }
        }
    }

    # Set time to morning (0.25)
    env.registry.global_vfs[0, time_idx] = 0.25
    can_spawn = env.item_manager.should_spawn_item("energy_potion")
    assert not can_spawn.any()  # Should not spawn in morning

    # Set time to evening (0.75)
    env.registry.global_vfs[0, time_idx] = 0.75
    can_spawn = env.item_manager.should_spawn_item("energy_potion")
    assert can_spawn.all()  # Should spawn in evening
```

### Step 4: Add Advanced Condition Tests (2 hours)

Test complex conditions:
- Multiple AND conditions
- Agent aggregations (`mean()`, `count()`, `exists()`)
- Item VFS state conditions

---

## Acceptance Criteria

- [ ] VFS predicate syntax documented in `items.md`
- [ ] `should_spawn_item()` evaluates VFS conditions
- [ ] Tests verify conditions work (simple and complex)
- [ ] Examples in docs show realistic use cases

---

## Files to Modify

1. `docs/config-schemas/items.md` - Document VFS predicate syntax
2. `src/townlet/items/manager.py` - Implement condition evaluation
3. `tests/test_townlet/unit/items/test_spawn_conditions.py` (NEW) - Tests

---

## Related Issues

- Related: P1-VFS-1 (expression operators - may need aggregations)
- Blocking: None (optional feature)

---

## Notes

- **Low priority:** Basic spawning works fine without conditions
- **Nice-to-have:** Enables more sophisticated gameplay
- **Deferred:** Can add when needed for advanced curriculum levels
- Consider if this should integrate with existing VFS evaluator or have custom logic
