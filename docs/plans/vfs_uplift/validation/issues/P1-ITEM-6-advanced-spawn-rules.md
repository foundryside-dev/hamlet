# [ITEM-6] Advanced Spawn Rules

**Priority:** P1 (Important)
**Category:** Items
**Status:** PARTIAL
**Effort:** 2-3 days

## Description

Items system only implements basic spawn rules (random placement + periodic schedule). Missing advanced spawn rules for controlled placement (fixed positions, grid patterns, scripted spawn sequences) and diverse scheduling strategies (time windows, Poisson processes, normal distribution).

## Current State

**Implemented (working):**
- ✅ Random placement: Items spawn at random positions on substrate
- ✅ Periodic schedule: Items spawn every N ticks (deterministic intervals)
- ✅ Basic spawn parameters: quantity, delay, period
- ✅ Spawn rule schema exists for all modes (declared but not implemented)

**Location:** `src/townlet/items/manager.py:ItemManager.spawn_item()`

**Missing (not implemented):**

### Placement Modes:
- ❌ `fixed`: Spawn at specific coordinates [(x, y), (x, y), ...]
- ❌ `grid`: Spawn in grid pattern (e.g., every 5th cell)
- ❌ `scripted`: Spawn following predefined sequence

### Schedule Types:
- ❌ `time_window`: Spawn only during specific tick ranges [start, end]
- ❌ `poisson`: Spawn following Poisson process (random but controlled rate)
- ❌ `normal`: Spawn with normal distribution around target tick
- ❌ `max_total`: Limit total spawned items (stop spawning after N items)

## Required Implementation

### 1. Fixed Placement Mode (4-5 hours)

**Schema exists:** `placement.mode = "fixed"`, `placement.fixed_positions = [(x, y), ...]`

**Implementation:**
```python
# src/townlet/items/manager.py
def _spawn_fixed_placement(self, spawn_rule, item_type):
    """Spawn items at fixed positions."""
    for position in spawn_rule.placement.fixed_positions:
        if not self._position_occupied(position):
            self.spawn_item(
                item_type=item_type,
                position=position,
                vfs_profile=spawn_rule.vfs_profile,
                initial_state=spawn_rule.initial_state
            )
```

**Tests:**
- Spawn items at specified positions
- Skip occupied positions
- Handle out-of-bounds positions gracefully
- Multiple items at different fixed positions

### 2. Grid Placement Mode (3-4 hours)

**Schema exists:** `placement.mode = "grid"`, `placement.grid_spacing = 5`

**Implementation:**
```python
def _spawn_grid_placement(self, spawn_rule, item_type):
    """Spawn items in grid pattern."""
    spacing = spawn_rule.placement.grid_spacing
    for x in range(0, self.substrate_width, spacing):
        for y in range(0, self.substrate_height, spacing):
            if not self._position_occupied((x, y)):
                self.spawn_item(
                    item_type=item_type,
                    position=(x, y),
                    vfs_profile=spawn_rule.vfs_profile,
                    initial_state=spawn_rule.initial_state
                )
```

**Tests:**
- Grid spawning with various spacing values
- Respect max_total limit
- Handle partially filled grids
- Edge cases: spacing larger than grid, spacing = 1

### 3. Scripted Placement Mode (4-5 hours)

**Schema exists:** `placement.mode = "scripted"`, `placement.script = [{tick: N, position: (x,y)}, ...]`

**Implementation:**
```python
def _spawn_scripted_placement(self, spawn_rule, item_type):
    """Spawn items following script."""
    current_tick = self.current_tick
    for spawn_event in spawn_rule.placement.script:
        if spawn_event.tick == current_tick:
            self.spawn_item(
                item_type=item_type,
                position=spawn_event.position,
                vfs_profile=spawn_rule.vfs_profile,
                initial_state=spawn_rule.initial_state
            )
```

**Tests:**
- Spawn at scripted ticks
- Multiple spawn events in one tick
- Out-of-order scripts handled correctly
- Script exhaustion (no more events)

### 4. Time Window Schedule (2-3 hours)

**Schema exists:** `schedule.type = "time_window"`, `schedule.start_tick`, `schedule.end_tick`

**Implementation:**
```python
def _check_time_window(self, spawn_rule):
    """Check if current tick is within spawn window."""
    if spawn_rule.schedule.type != "time_window":
        return True

    current_tick = self.current_tick
    return (spawn_rule.schedule.start_tick <= current_tick <=
            spawn_rule.schedule.end_tick)
```

**Tests:**
- Spawn only within window
- No spawns before window starts
- No spawns after window ends
- Edge cases: window size = 1, window = entire simulation

### 5. Poisson Schedule (3-4 hours)

**Schema exists:** `schedule.type = "poisson"`, `schedule.rate = lambda`

**Implementation:**
```python
def _check_poisson_spawn(self, spawn_rule):
    """Check if spawn occurs via Poisson process."""
    import numpy as np
    rate = spawn_rule.schedule.rate
    # Poisson process: P(event in dt) = 1 - e^(-lambda * dt)
    spawn_probability = 1 - np.exp(-rate)
    return np.random.random() < spawn_probability
```

**Tests:**
- Spawn rate matches expected lambda
- Randomness but controlled rate
- Edge cases: rate = 0, rate = very high

### 6. Normal Distribution Schedule (3-4 hours)

**Schema exists:** `schedule.type = "normal"`, `schedule.mean`, `schedule.std_dev`

**Implementation:**
```python
def _sample_normal_spawn_tick(self, spawn_rule):
    """Sample next spawn tick from normal distribution."""
    import numpy as np
    mean = spawn_rule.schedule.mean
    std_dev = spawn_rule.schedule.std_dev
    next_tick = int(np.random.normal(mean, std_dev))
    return max(0, next_tick)  # Clamp to non-negative
```

**Tests:**
- Spawn ticks follow normal distribution
- Mean and std dev honored
- Handle negative samples (clamp to 0)
- Multiple spawns centered around mean

### 7. Max Total Limit (2 hours)

**Schema exists:** `spawn_rule.max_total = N`

**Implementation:**
```python
# Track spawned item counts
self.spawn_counts: Dict[str, int] = {}

def spawn_item(self, item_type, ...):
    spawn_rule = self.spawn_rules[item_type]
    if spawn_rule.max_total:
        if self.spawn_counts.get(item_type, 0) >= spawn_rule.max_total:
            return  # Max limit reached

    # Existing spawn logic...
    self.spawn_counts[item_type] = self.spawn_counts.get(item_type, 0) + 1
```

**Tests:**
- Spawning stops at max_total
- Count persists across ticks
- Count resets on environment reset
- Different limits for different item types

## Acceptance Criteria

**Placement Modes:**
- [ ] Fixed placement spawns items at specified positions
- [ ] Grid placement spawns items in grid pattern with spacing
- [ ] Scripted placement follows spawn event timeline
- [ ] All placement modes respect position validity (bounds, occupation)

**Schedule Types:**
- [ ] Time window schedule spawns only within tick range
- [ ] Poisson schedule spawns with controlled random rate
- [ ] Normal schedule spawns with normal distribution around mean
- [ ] Periodic schedule continues to work (no regression)

**Limits:**
- [ ] max_total limit enforced for all spawn rules
- [ ] Spawn counts tracked per item type
- [ ] Spawn counts reset on environment reset

**Testing:**
- [ ] 30+ tests covering all spawn modes and schedules
- [ ] Integration tests with real environments
- [ ] Edge cases handled gracefully (out of bounds, max limits, empty scripts)
- [ ] Performance: No significant overhead from advanced spawn logic

**Documentation:**
- [ ] Update `docs/config-schemas/items.md` with spawn rule examples
- [ ] Add spawn rule cookbook with common patterns

## Evidence

**Source Report:** gap-report-final.md (lines 55-68), gap-report-items.md
**Schema:** `src/townlet/items/schema.py` (SpawnRule, PlacementSpec, ScheduleSpec)
**Current Implementation:** `src/townlet/items/manager.py:spawn_item()` (basic random + periodic only)

## Implementation Notes

**Why P1 (not P0):** Current spawn rules (random + periodic) sufficient for Phase 1-3 curriculum levels. Advanced spawn rules needed for Phase 4+ scenarios (e.g., shops that restock on schedule, enemies that spawn in waves, resources that appear in specific locations).

**Phase Requirements:**
- Phase 1-3: Random + periodic sufficient ✅
- Phase 4+: Fixed, grid, time windows needed
- Phase 5+: Scripted, Poisson, normal distributions for complex scenarios

**Implementation Order (by priority):**
1. Fixed placement (explicit control for landmarks, shops)
2. Time window schedule (day/night spawning, event-based)
3. Max total limit (resource scarcity)
4. Grid placement (resource distribution patterns)
5. Poisson schedule (organic randomness)
6. Normal schedule (bell curve spawning)
7. Scripted placement (narrative sequences)

**Testing Strategy:**
- Unit tests for each spawn mode in isolation
- Integration tests with vectorized environments
- Stress tests: 1000+ items, rapid spawning
- Randomness tests: Verify distributions (chi-square goodness of fit)

## References

- Schema: `src/townlet/items/schema.py` (SpawnRule, PlacementSpec, ScheduleSpec)
- Implementation: `src/townlet/items/manager.py:spawn_item()`
- Tests: `tests/test_townlet/unit/items/test_spawn_rules.py` (extend)
- Documentation: `docs/config-schemas/items.md` (update with examples)
- Related: ITEM-8 (spawn conditions), items system design in VFS uplift plans
