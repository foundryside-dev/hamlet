# Items System - Periodic Respawning Implementation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement periodic item respawning based on `spawn_interval` configuration to complete Task 4.5 from the master plan.

**Architecture:** ItemManager tracks next respawn time per item type. Environment calls respawn logic during step(). Items respawn at configured intervals after despawning.

**Tech Stack:** PyTorch (tensors), Pydantic (configs), Python dataclasses

**Dependencies:**
- ✅ Task 4 Phase 1-4 (Items foundation) - COMPLETE
- ✅ Automatic spawning at reset - COMPLETE (2025-11-20)

**Current State:**
- `spawn_interval` field exists in ItemsAppearanceConfig but is not used
- Items spawn once at environment reset
- No periodic respawning mechanism exists

---

## Task 1: Add Respawn Tracking to ItemManager (0.5 days)

**Goal:** Track when each item type should respawn next.

**Files:**
- Modify: `src/townlet/items/manager.py`
- Test: `tests/test_townlet/unit/items/test_periodic_respawn.py`

---

### Step 1: Write test for respawn timer tracking

**Create** (`tests/test_townlet/unit/items/test_periodic_respawn.py`):

```python
"""Tests for periodic item respawning."""

import torch
from pathlib import Path

from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.items.manager import ItemManager


def test_respawn_timer_initialized_on_despawn():
    """When item despawns with cooldown, respawn timer is set."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    # Load appearance config (has spawn_interval)
    appearance_config = ItemsAppearanceConfig(
        version="1.0",
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "spawn_interval": 100,
                "spawn_position": "random",
            }
        ],
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
    )

    # Set appearance config
    manager.set_appearance_config(appearance_config, grid_size=(7, 7))

    # Spawn apple
    item = manager.spawn_item("apple", position=(0, 0), current_tick=0)
    assert item is not None

    # Despawn it (item expires)
    manager.despawn_item(item.instance_id, current_tick=50)

    # Verify respawn timer set
    assert "apple" in manager.respawn_timers
    assert manager.respawn_timers["apple"] == 50 + 100  # current_tick + spawn_interval


def test_respawn_timer_not_set_without_spawn_interval():
    """Items without spawn_interval don't get respawn timers."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    appearance_config = ItemsAppearanceConfig(
        version="1.0",
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "spawn_interval": None,  # No periodic respawn
                "spawn_position": "random",
            }
        ],
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
    )

    manager.set_appearance_config(appearance_config, grid_size=(7, 7))

    # Spawn and despawn
    item = manager.spawn_item("apple", position=(0, 0), current_tick=0)
    manager.despawn_item(item.instance_id, current_tick=50)

    # No respawn timer
    assert "apple" not in manager.respawn_timers
```

---

### Step 2: Run test to verify it fails

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/items/test_periodic_respawn.py::test_respawn_timer_initialized_on_despawn -xvs
```

**Expected:** FAIL - `AttributeError: 'ItemManager' object has no attribute 'set_appearance_config'`

---

### Step 3: Add appearance config storage to ItemManager

**Modify** (`src/townlet/items/manager.py`):

In `__init__`, after initializing `cooldown_until`:

```python
        # Cooldown tracking (item_type -> tick when can spawn again)
        self.cooldown_until: dict[str, int] = {}

        # Appearance config for periodic respawning
        self.appearance_config: ItemsAppearanceConfig | None = None
        self.grid_size: tuple[int, ...] | None = None

        # Respawn timers (item_type -> tick when should respawn)
        self.respawn_timers: dict[str, int] = {}
```

Add method after `spawn_initial_items`:

```python
    def set_appearance_config(
        self,
        appearance_config: ItemsAppearanceConfig,
        grid_size: tuple[int, ...],
    ) -> None:
        """Store appearance config for periodic respawning.

        Args:
            appearance_config: Level-specific item spawn rules
            grid_size: Grid dimensions for random position generation
        """
        self.appearance_config = appearance_config
        self.grid_size = grid_size
```

---

### Step 4: Update despawn_item to set respawn timers

**Modify** (`src/townlet/items/manager.py`):

Update `despawn_item` method:

```python
    def despawn_item(self, instance_id: int, current_tick: int) -> None:
        """Despawn item from world or held state.

        Args:
            instance_id: Item instance ID to despawn
            current_tick: Current tick (for cooldown tracking)
        """
        # Check active items first
        if instance_id in self.active_items:
            item = self.active_items.pop(instance_id)
        # Then check held items
        elif instance_id in self.held_items:
            item = self.held_items.pop(instance_id)
        else:
            return  # Item not found

        # Free VFS slot
        self.vfs_free_slots.add(item.vfs_index)

        # Set cooldown if configured
        item_def = next(t for t in self.catalog.item_types if t.id == item.item_type)
        if item_def.cooldown is not None:
            self.cooldown_until[item.item_type] = current_tick + item_def.cooldown

        # Set respawn timer if configured in appearance config
        if self.appearance_config is not None:
            # Find appearance rule for this item type
            rule = next(
                (r for r in self.appearance_config.items if r.item_type == item.item_type),
                None,
            )

            if rule is not None and rule.spawn_interval is not None:
                # Schedule respawn
                self.respawn_timers[item.item_type] = current_tick + rule.spawn_interval
```

---

### Step 5: Run test to verify it passes

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/items/test_periodic_respawn.py -xvs
```

**Expected:** BOTH TESTS PASS

---

### Step 6: Commit

```bash
git add src/townlet/items/manager.py tests/test_townlet/unit/items/test_periodic_respawn.py
git commit -m "feat(items): add respawn timer tracking for periodic spawning

- Add appearance_config and grid_size storage to ItemManager
- Add respawn_timers dict to track next respawn time per item type
- Add set_appearance_config() method
- Update despawn_item() to set respawn timer based on spawn_interval
- Only set timer if appearance config exists and spawn_interval is not None

Test results: test_periodic_respawn.py PASSING (2/2)"
```

---

## Task 2: Implement Periodic Respawn Logic (0.5 days)

**Goal:** Respawn items when their timer expires.

**Files:**
- Modify: `src/townlet/items/manager.py`
- Test: `tests/test_townlet/unit/items/test_periodic_respawn.py`

---

### Step 1: Write test for respawn execution

**Modify** (`tests/test_townlet/unit/items/test_periodic_respawn.py`):

Add test:

```python
def test_process_respawns_spawns_item_when_timer_expires():
    """process_respawns spawns item when timer expires."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    appearance_config = ItemsAppearanceConfig(
        version="1.0",
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "spawn_interval": 100,
                "spawn_position": "random",
            }
        ],
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
    )

    manager.set_appearance_config(appearance_config, grid_size=(7, 7))

    # Spawn and despawn apple at tick 0
    item = manager.spawn_item("apple", position=(0, 0), current_tick=0)
    manager.despawn_item(item.instance_id, current_tick=0)

    # Timer should be at tick 100
    assert manager.respawn_timers["apple"] == 100

    # Process respawns at tick 99 (not yet)
    manager.process_respawns(current_tick=99)
    assert len(manager.active_items) == 0

    # Process respawns at tick 100 (timer expires)
    manager.process_respawns(current_tick=100)
    assert len(manager.active_items) == 1

    # Verify apple spawned
    spawned_items = list(manager.active_items.values())
    assert spawned_items[0].item_type == "apple"

    # Timer should be cleared
    assert "apple" not in manager.respawn_timers


def test_process_respawns_respects_max_items_capacity():
    """process_respawns doesn't spawn if at max capacity."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    appearance_config = ItemsAppearanceConfig(
        version="1.0",
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "spawn_interval": 10,
                "spawn_position": "random",
            }
        ],
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=2,  # Small capacity
        device="cpu",
    )

    manager.set_appearance_config(appearance_config, grid_size=(7, 7))

    # Fill manager to capacity with coins
    manager.spawn_item("coin", position=(0, 0), current_tick=0)
    manager.spawn_item("coin", position=(1, 1), current_tick=0)
    assert len(manager.active_items) == 2

    # Set respawn timer for apple
    manager.respawn_timers["apple"] = 10

    # Try to respawn apple
    manager.process_respawns(current_tick=10)

    # Apple should NOT spawn (at capacity)
    assert len(manager.active_items) == 2  # Still just 2 coins

    # Timer should remain (will retry next tick)
    assert "apple" in manager.respawn_timers
```

---

### Step 2: Run test to verify it fails

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/items/test_periodic_respawn.py::test_process_respawns_spawns_item_when_timer_expires -xvs
```

**Expected:** FAIL - `AttributeError: 'ItemManager' object has no attribute 'process_respawns'`

---

### Step 3: Implement process_respawns method

**Modify** (`src/townlet/items/manager.py`):

Add method after `set_appearance_config`:

```python
    def process_respawns(self, current_tick: int) -> None:
        """Process periodic item respawning based on timers.

        Args:
            current_tick: Current environment tick
        """
        if self.appearance_config is None or self.grid_size is None:
            return  # No appearance config, no respawning

        # Check which timers have expired
        expired_types = [
            item_type
            for item_type, respawn_tick in self.respawn_timers.items()
            if current_tick >= respawn_tick
        ]

        # Attempt to spawn each expired type
        for item_type in expired_types:
            # Find appearance rule for this item type
            rule = next(
                (r for r in self.appearance_config.items if r.item_type == item_type),
                None,
            )

            if rule is None:
                # Rule removed from config, clear timer
                del self.respawn_timers[item_type]
                continue

            # Generate random position
            if rule.spawn_position == "random":
                position = tuple(random.randint(0, size - 1) for size in self.grid_size)
            else:
                # TODO: Support fixed positions when needed
                position = tuple(random.randint(0, size - 1) for size in self.grid_size)

            # Attempt spawn (may fail if at capacity or on cooldown)
            spawned = self.spawn_item(item_type, position, current_tick)

            if spawned is not None:
                # Successfully spawned, clear timer
                del self.respawn_timers[item_type]

                # If spawn_interval exists, schedule next respawn when this item despawns
                # (Timer will be set by despawn_item when this item expires)
            else:
                # Failed to spawn (at capacity or cooldown), keep timer for retry next tick
                # Don't delete timer - will retry on next process_respawns call
                pass
```

---

### Step 4: Run tests to verify they pass

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/items/test_periodic_respawn.py -xvs
```

**Expected:** ALL 4 TESTS PASS

---

### Step 5: Commit

```bash
git add src/townlet/items/manager.py tests/test_townlet/unit/items/test_periodic_respawn.py
git commit -m "feat(items): implement periodic respawning logic

- Add process_respawns() method to ItemManager
- Spawn items when respawn timer expires
- Respect max_items capacity (retry on next tick if full)
- Clear timer on successful spawn
- Support random position generation

Test results: test_periodic_respawn.py PASSING (4/4)"
```

---

## Task 3: Wire Periodic Respawning into Environment (0.5 days)

**Goal:** Call process_respawns during environment step.

**Files:**
- Modify: `src/townlet/environment/vectorized_env.py`
- Modify: `src/townlet/items/manager.py` (update spawn_initial_items)
- Test: `tests/test_townlet/integration/test_items_integration.py`

---

### Step 1: Write integration test for periodic respawning

**Modify** (`tests/test_townlet/integration/test_items_integration.py`):

Add test:

```python
def test_periodic_respawning_during_training():
    """Items respawn periodically during environment steps."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), use_cache=False)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    # Reset spawns initial items
    env.reset()

    # Count initial items
    initial_count = len(env.item_manager.active_items)
    assert initial_count > 0, "Should have spawned items at reset"

    # Pick up all apples (they have spawn_interval=100)
    apples = [i for i in env.item_manager.active_items.values() if i.item_type == "apple"]
    for apple in apples:
        env.positions[0] = torch.tensor(apple.position, dtype=torch.long)
        get_action = env.action_space.get_action_by_name("GET")
        env.step(torch.tensor([get_action.id]))

    # Verify apples picked up
    remaining_apples = [i for i in env.item_manager.active_items.values() if i.item_type == "apple"]
    assert len(remaining_apples) == 0, "All apples should be picked up"

    # Step 100 times (spawn_interval for apple)
    wait_action = env.action_space.get_action_by_name("WAIT")
    for _ in range(100):
        env.step(torch.tensor([wait_action.id]))

    # Verify at least one apple respawned
    respawned_apples = [i for i in env.item_manager.active_items.values() if i.item_type == "apple"]
    assert len(respawned_apples) > 0, "Apples should have respawned after 100 ticks"
```

---

### Step 2: Run test to verify it fails

**Run:**

```bash
rm -rf configs/test/items_smoke/.compiled
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src timeout 30 uv run pytest tests/test_townlet/integration/test_items_integration.py::test_periodic_respawning_during_training -xvs
```

**Expected:** FAIL - "Apples should have respawned after 100 ticks"

---

### Step 3: Update spawn_initial_items to call set_appearance_config

**Modify** (`src/townlet/items/manager.py`):

Update `spawn_initial_items` method:

```python
    def spawn_initial_items(
        self,
        appearance_config: ItemsAppearanceConfig,
        grid_size: tuple[int, ...],
        current_tick: int,
    ) -> None:
        """Spawn items at level start based on ItemsAppearanceConfig.

        Args:
            appearance_config: Level-specific item spawn rules
            grid_size: Grid dimensions (e.g., (7, 7) for 7x7 grid)
            current_tick: Current environment tick
        """
        # Store config for periodic respawning
        self.set_appearance_config(appearance_config, grid_size)

        for rule in appearance_config.items:
            # Validate item type exists in catalog
            if not any(t.id == rule.item_type for t in self.catalog.item_types):
                # Skip unknown item types (e.g., energy_drink in test config)
                continue

            # Spawn count items
            for _ in range(rule.spawn_count):
                # Generate random position within grid bounds
                if rule.spawn_position == "random":
                    position = tuple(random.randint(0, size - 1) for size in grid_size)
                else:
                    # TODO: Support fixed positions when needed
                    position = tuple(random.randint(0, size - 1) for size in grid_size)

                # Attempt spawn (may fail if at capacity)
                self.spawn_item(rule.item_type, position, current_tick)
```

---

### Step 4: Wire process_respawns into environment step

**Modify** (`src/townlet/environment/vectorized_env.py`):

Find the `step()` method and add respawn processing after meter dynamics. Look for where `self.meter_dynamics.tick()` is called (around line 1130-1140), and add after it:

```python
        # Apply meter dynamics (decay/regeneration)
        self.meter_dynamics.tick(
            meters=self.meters,
            dones=self.dones,
            time_of_day=self.time_of_day if self.enable_temporal_mechanics else None,
        )

        # Process periodic item respawning
        if self.item_manager is not None:
            self.item_manager.process_respawns(current_tick=int(self.current_tick))
```

---

### Step 5: Run integration test to verify it passes

**Run:**

```bash
rm -rf configs/test/items_smoke/.compiled
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src timeout 30 uv run pytest tests/test_townlet/integration/test_items_integration.py::test_periodic_respawning_during_training -xvs
```

**Expected:** PASS

---

### Step 6: Run all items integration tests

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src timeout 60 uv run pytest tests/test_townlet/integration/test_items_integration.py -v
```

**Expected:** ALL TESTS PASS (10/10 including new test)

---

### Step 7: Commit

```bash
git add src/townlet/environment/vectorized_env.py src/townlet/items/manager.py tests/test_townlet/integration/test_items_integration.py
git commit -m "feat(items): wire periodic respawning into environment step

- Call process_respawns() during environment step
- Update spawn_initial_items() to call set_appearance_config()
- Add integration test for periodic respawning during training
- Items now respawn at configured intervals after despawning

Test results: All 10 items integration tests PASSING

Completes Task 4.5 from master plan: Item spawn scheduler

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `test_periodic_respawn.py` - 4 tests PASSING
- [ ] `test_items_integration.py` - 10 tests PASSING (including periodic respawn test)
- [ ] Items respawn at configured `spawn_interval` after despawning
- [ ] Respawn logic respects `max_items` capacity
- [ ] Items without `spawn_interval` don't respawn
- [ ] Respawn timers cleared on successful spawn
- [ ] No respawn attempts if appearance config is None
- [ ] Environment calls `process_respawns()` each step

---

## Final Assessment

**Before This Plan:**
- Items spawn once at environment reset ✅
- `spawn_interval` field parsed but unused ❌
- No periodic respawning mechanism ❌

**After This Plan:**
- Items spawn at environment reset ✅
- Items respawn periodically based on `spawn_interval` ✅
- Respawn logic integrated into environment step loop ✅
- Respects capacity and cooldown constraints ✅

**Task Breakdown:**
- Task 1: Respawn timer tracking (0.5 days)
- Task 2: Respawn logic implementation (0.5 days)
- Task 3: Environment integration (0.5 days)

**Estimated Time:** 1.5 days

**Outcome:** Task 4.5 from master plan **COMPLETE** - Item spawn scheduler fully functional

---

## Related Documentation

- **Master Plan:** `docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md` (Phase 4, Task 4.5)
- **Items Foundation:** `docs/plans/vfs_uplift/2025-11-20-task-4-supplementary.md`
- **Config Schema:** `docs/config-schemas/items.md`
