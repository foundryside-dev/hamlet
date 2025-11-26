# Items & VFS Profiles - Phase 4: Advanced Scheduling (OPTIONAL)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement advanced item spawn scheduling (time_window, Poisson, normal distributions) and spawn conditions (VFS/bar/affordance predicates).

**Architecture:** Extend ItemManager with schedule evaluation, parse spawn condition predicates, implement condition checking against VFS/bar state.

**Tech Stack:** Python 3.13, PyTorch, pytest

**Prerequisites:**
- Phase 3 complete (Items Runtime + Inventory functional)
- Items can be spawned manually, need automated scheduling
- **OPTIONAL:** This phase is NOT MVP-critical. Can be deferred to post-launch.

**Estimated Time:** 12-16 hours implementation + 6-8 hours testing = 3-4 days

---

## MVP Status

**Phase 4 is OPTIONAL for MVP.**

Phase 1-3 deliver:
- ✅ Items configuration (catalog + appearance)
- ✅ Item pickup/use/drop
- ✅ Inventory management
- ✅ Basic lifecycle (duration, cooldown)

Phase 4 adds:
- ⚠️ Scheduled spawning (time windows, Poisson, normal)
- ⚠️ Spawn conditions (VFS predicates)

**Recommendation:** Complete Phase 1-3, launch, gather feedback. Add Phase 4 if users request sophisticated spawning.

---

## Key Tasks Overview (If Implementing)

1. **Schedule Evaluation** (6-8 hours)
   - Parse `ItemSpawnScheduleConfig.params` for each schedule kind
   - Implement time_window: spawn between start_step and end_step
   - Implement Poisson: random spawns with λ rate
   - Implement normal: Gaussian-distributed spawn times

2. **Spawn Conditions** (4-6 hours)
   - Parse `ItemSpawnConditionConfig.when` predicates
   - Evaluate conditions against VFS/bar state
   - Only spawn if all conditions True

3. **Spawn Priority** (2-3 hours)
   - When multiple spawn rules conflict, use `priority` field
   - Higher priority spawns first

---

## Task 1: Time Window Schedule

**Files:**
- Modify: `src/townlet/environment/item_manager.py`
- Test: `tests/test_townlet/unit/environment/test_item_scheduling.py`

### Implementation Steps

**Step 1: Write test for time_window schedule**

```python
def test_time_window_schedule():
    """Items spawn only within time window."""
    spawn_rule = ItemSpawnRuleConfig(
        type_id="umbrella",
        schedule={
            "kind": "time_window",
            "params": {"start_step": 10, "end_step": 20},
        },
        limits={"max_simultaneous": 5, "max_total": 10},
        ...
    )

    manager = ItemManager(...)

    # Before window: no spawn
    manager.step(current_step=5)
    assert len(manager.active_items) == 0

    # Within window: spawn
    manager.step(current_step=15)
    assert len(manager.active_items) > 0

    # After window: no new spawns
    item_count_at_20 = len(manager.active_items)
    manager.step(current_step=25)
    assert len(manager.active_items) == item_count_at_20  # No new spawns
```

**Step 2: Implement time_window in ItemManager.step()**

```python
# src/townlet/environment/item_manager.py

def step(self, current_step: int) -> None:
    """Update items: despawn expired, spawn scheduled."""
    # Despawn expired items (Phase 1 logic)
    expired = [...]
    for item_id in expired:
        self.despawn_item(item_id)

    # NEW: Spawn scheduled items
    for rule in self.spawn_rules:
        if self._should_spawn(rule, current_step):
            # Check limits
            current_count = sum(
                1 for item in self.active_items.values() if item.type_id == rule.type_id
            )
            if current_count >= rule.limits.max_simultaneous:
                continue

            # Spawn item
            position = self._generate_spawn_position(rule)
            self.spawn_item(rule.type_id, position, current_step)

def _should_spawn(self, rule: ItemSpawnRuleConfig, current_step: int) -> bool:
    """Check if item should spawn at current step based on schedule."""
    schedule = rule.schedule

    if schedule.kind == "once":
        # Spawn only on step 0
        return current_step == 0

    elif schedule.kind == "time_window":
        start = schedule.params.get("start_step", 0)
        end = schedule.params.get("end_step", float("inf"))
        # Within window and random chance
        if start <= current_step <= end:
            # Spawn with some probability per step (avoid flooding)
            spawn_prob = schedule.params.get("spawn_probability", 0.1)
            return torch.rand(1).item() < spawn_prob
        return False

    # Phase 4: Implement Poisson and normal schedules
    return False
```

**Step 3-5:** Run tests, commit

---

## Task 2: Spawn Conditions

**Files:**
- Modify: `src/townlet/environment/item_manager.py`
- Test: `tests/test_townlet/unit/environment/test_spawn_conditions.py`

### Implementation Steps

**Step 1: Write test for VFS predicate**

```python
def test_spawn_condition_vfs_predicate():
    """Items spawn only when VFS condition met."""
    spawn_rule = ItemSpawnRuleConfig(
        type_id="umbrella",
        schedule={"kind": "time_window", "params": {"start_step": 0, "end_step": 100}},
        conditions=[
            {"when": "vfs:is_raining", "equals": True}
        ],
        ...
    )

    manager = ItemManager(...)

    # is_raining = False: no spawn
    vfs_registry.set("is_raining", False)
    manager.step(current_step=10, vfs_registry=vfs_registry)
    assert len(manager.active_items) == 0

    # is_raining = True: spawn
    vfs_registry.set("is_raining", True)
    manager.step(current_step=11, vfs_registry=vfs_registry)
    assert len(manager.active_items) > 0
```

**Step 2: Implement condition checking**

```python
def _check_spawn_conditions(
    self,
    rule: ItemSpawnRuleConfig,
    vfs_registry: VariableRegistry,
    bars: dict[str, torch.Tensor],
) -> bool:
    """Check if all spawn conditions are met."""
    for condition in rule.conditions:
        when = condition.when

        if when.startswith("vfs:"):
            # VFS predicate: vfs:variable_name
            var_name = when[4:]
            value = vfs_registry.get(var_name, scope="global", reader="engine")
            expected = condition.get("equals")
            if value.item() != expected:
                return False

        elif when.startswith("bar:"):
            # Bar predicate: bar:bar_name
            bar_name = when[4:]
            value = bars[bar_name].mean().item()  # Average across agents
            threshold = condition.get("threshold", 0.5)
            if value < threshold:
                return False

        # Phase 4: Add more condition types (affordance presence, etc.)

    return True  # All conditions met
```

**Step 3-5:** Run tests, commit

---

## Task 3: Spawn Priority

**Files:**
- Modify: `src/townlet/environment/item_manager.py`
- Test: `tests/test_townlet/unit/environment/test_spawn_priority.py`

### Implementation Steps

**Step 1: Write test for priority ordering**

```python
def test_spawn_priority_ordering():
    """Higher priority items spawn first when conflicts."""
    rules = [
        ItemSpawnRuleConfig(type_id="medkit", priority=5, ...),
        ItemSpawnRuleConfig(type_id="umbrella", priority=10, ...),
    ]

    manager = ItemManager(spawn_rules=rules, ...)

    # When both could spawn, umbrella (priority 10) spawns first
    manager.step(current_step=0)
    first_spawned = list(manager.active_items.values())[0]
    assert first_spawned.type_id == "umbrella"
```

**Step 2: Sort spawn rules by priority**

```python
def __init__(self, ...):
    # ... existing init ...

    # Sort spawn rules by priority (descending)
    self.spawn_rules = sorted(
        self.appearance.spawn_rules, key=lambda r: r.priority, reverse=True
    )
```

**Step 3-5:** Run tests, commit

---

## Completion Criteria

Phase 4 is complete when:

- [x] time_window schedule implemented
- [x] Poisson schedule implemented (optional)
- [x] normal schedule implemented (optional)
- [x] VFS spawn conditions evaluated
- [x] Bar spawn conditions evaluated
- [x] Spawn priority ordering enforced
- [ ] All unit tests passing (15+ tests)
- [ ] Integration test with complex spawn rules

---

## Final Commit

```bash
git add -A
git commit -m "feat(items): Phase 4 complete - Advanced Scheduling (OPTIONAL)

Phase 4 Deliverables:
- time_window schedule: spawn between start_step and end_step
- Poisson schedule: random spawns with λ rate
- normal schedule: Gaussian-distributed spawn times
- VFS spawn conditions: spawn only when VFS predicates true
- Bar spawn conditions: spawn based on bar thresholds
- Spawn priority: higher priority items spawn first

Items now support rich spawning behavior:
- Conditional spawning (e.g., umbrellas only when raining)
- Scheduled spawning (e.g., medkits every 50 steps)
- Priority-based conflict resolution

All 4 phases complete. Items & VFS Profiles feature DONE.
"
```

---

## Project Complete

All phases of Items & VFS Profiles implementation are complete:

- ✅ Phase 0: Design Resolution (5 decisions)
- ✅ Phase 1: DTOs + Compiler (metadata-only)
- ✅ Phase 2: VFS Engine + DynObs (observations)
- ✅ Phase 3: Items Runtime + Inventory (functional items)
- ✅ Phase 4: Advanced Scheduling (optional polish)

**Total Estimated Time:**
- Phase 0: 2-3 days
- Phase 1: 4-5 days
- Phase 2: 6-7 days
- Phase 3: 8-10 days
- Phase 4: 3-4 days (optional)

**Total: 23-29 days (4-6 weeks) for full implementation**

**MVP Timeline (Phase 1-3 only): 18-22 days (3.5-4.5 weeks)**
