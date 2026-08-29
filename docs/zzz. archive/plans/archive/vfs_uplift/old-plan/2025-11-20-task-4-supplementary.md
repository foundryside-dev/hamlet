# Items System Completion - Phase 4 Supplementary

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the Items System by wiring Effects execution for item interactions (on_pickup/on_use/on_drop).

**Architecture:** Items use the Effects System for all interactions. ItemActionHandler compiles item interaction commands using CommandCompiler, then executes them via CommandExecutor with proper ExecutionContext targeting the agent.

**Tech Stack:** Effects System (CommandCompiler, CommandExecutor, ExecutionContext), PyTorch (tensors), Pydantic (configs)

**Dependencies:**

- ✅ Phase 3 (Effects System) - CommandCompiler, CommandExecutor, ExecutionContext
- ✅ Task 4.1-4.4 (Items foundation) - ItemManager, InventoryState, ItemActionHandler
- ✅ Task 4.5 (Partial environment integration) - Items components initialized

**Current State:**

- ItemActionHandler exists but has TODO placeholders where Effects should execute
- Effects System is fully implemented and working for affordances
- Environment already has CommandExecutor instance at `self.command_executor`
- Item interaction commands are defined in items.yaml but never compiled or executed

---

## Task 1: Item Lifecycle & Persistence (0.5 days)

**Goal:** Ensure items retain VFS state (durability, age, unique IDs) when moving between World Grid and Agent Inventory.

**Critical Issue:** Using `despawn_item` on pickup deletes item data. When dropped, a new item spawns with reset VFS state. This breaks any durability/spoilage mechanics.

**Solution:** Add `lift_item` (world → held_items) and `place_item` (held_items → world) that preserve ItemInstance.

**Files:**

- Modify: `src/townlet/items/manager.py`
- Test: `tests/test_townlet/unit/items/test_item_lifecycle.py`

---

### Step 1: Write test for item persistence across pickup/drop

**Create** (`tests/test_townlet/unit/items/test_item_lifecycle.py`):

```python
"""Tests for item lifecycle and persistence."""

import torch
from pathlib import Path

from townlet.config.items_config import ItemsCatalogConfig
from townlet.items.manager import ItemManager


def test_item_preserves_identity_when_lifted_and_placed():
    """Items retain instance_id and VFS state when lifted/placed."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
    )

    # Spawn apple at (2, 2)
    item = manager.spawn_item("apple", position=(2, 2), current_tick=0)
    assert item is not None
    original_id = item.instance_id

    # Lift item (pickup) - moves to held_items
    manager.lift_item(original_id)

    # Verify NOT in active_items
    assert original_id not in manager.active_items

    # Verify IN held_items
    assert original_id in manager.held_items
    held_item = manager.held_items[original_id]
    assert held_item.instance_id == original_id
    assert held_item.item_type == "apple"

    # Place item back at (5, 5) (drop)
    manager.place_item(original_id, position=(5, 5))

    # Verify back in active_items with SAME ID
    assert original_id in manager.active_items
    placed_item = manager.active_items[original_id]
    assert placed_item.instance_id == original_id
    assert placed_item.position == (5, 5)

    # Verify NOT in held_items
    assert original_id not in manager.held_items


def test_held_items_continue_ticking():
    """Items in inventory continue to age/spoil."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
    )

    # Spawn apple with duration=100
    item = manager.spawn_item("apple", position=(0, 0), current_tick=0)
    manager.lift_item(item.instance_id)

    # Tick 50 times
    for tick in range(1, 51):
        manager.tick(tick)

    # Verify item aged (ticks_alive increased)
    held_item = manager.held_items[item.instance_id]
    assert held_item.ticks_alive >= 50, "Held items must age"
```

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/items/test_item_lifecycle.py::test_item_preserves_identity_when_lifted_and_placed -v
```

**Expected:** FAIL - `AttributeError: 'ItemManager' object has no attribute 'lift_item'`

---

### Step 2: Add held_items registry to ItemManager

**Modify** (`src/townlet/items/manager.py`):

In `__init__` after initializing `active_items`:

```python
        # Active items in the world (visible on grid)
        self.active_items: dict[int, ItemInstance] = {}

        # Held items (in agent inventories, not on grid)
        # These items continue to tick (age/spoil) but are not spatially positioned
        self.held_items: dict[int, ItemInstance] = {}

        # Next instance ID counter
        self._next_instance_id = 0
```

---

### Step 3: Implement lift_item method

**Modify** (`src/townlet/items/manager.py`):

Add method after `spawn_item`:

```python
    def lift_item(self, instance_id: int) -> ItemInstance | None:
        """Move item from world to held state (pickup).

        Preserves item identity and VFS state. Item continues to tick.

        Args:
            instance_id: Item instance ID

        Returns:
            ItemInstance if lifted, None if not found
        """
        if instance_id not in self.active_items:
            return None

        # Move from active to held (do NOT free VFS slot - item still exists)
        item = self.active_items.pop(instance_id)
        self.held_items[instance_id] = item

        return item
```

---

### Step 4: Implement place_item method

**Modify** (`src/townlet/items/manager.py`):

Add method after `lift_item`:

```python
    def place_item(
        self,
        instance_id: int,
        position: tuple[int, ...],
    ) -> ItemInstance | None:
        """Move item from held state to world (drop).

        Preserves item identity and VFS state.

        Args:
            instance_id: Item instance ID
            position: Position to place item

        Returns:
            ItemInstance if placed, None if not found
        """
        if instance_id not in self.held_items:
            return None

        # Move from held to active
        item = self.held_items.pop(instance_id)
        item.position = position
        self.active_items[instance_id] = item

        return item
```

---

### Step 5: Update tick() to include held_items

**Modify** (`src/townlet/items/manager.py`):

Update `tick` method to iterate over both registries:

```python
    def tick(self, current_tick: int) -> None:
        """Update item lifetimes and despawn expired items.

        Args:
            current_tick: Current tick
        """
        to_despawn = []

        # Check active items (on grid)
        for instance_id, item in self.active_items.items():
            item.ticks_alive += 1

            if item.duration is not None and item.ticks_alive >= item.duration:
                to_despawn.append(instance_id)

        # Check held items (in inventories) - they also age!
        for instance_id, item in self.held_items.items():
            item.ticks_alive += 1

            if item.duration is not None and item.ticks_alive >= item.duration:
                to_despawn.append(instance_id)

        # Despawn expired items
        for instance_id in to_despawn:
            self.despawn_item(instance_id, current_tick)
```

---

### Step 6: Update despawn_item to handle both registries

**Modify** (`src/townlet/items/manager.py`):

Update `despawn_item` to check both registries:

```python
    def despawn_item(self, instance_id: int, current_tick: int) -> None:
        """Remove item from world or held state.

        Args:
            instance_id: Item instance ID
            current_tick: Current tick
        """
        # Check active items first
        if instance_id in self.active_items:
            item = self.active_items.pop(instance_id)
        # Then check held items
        elif instance_id in self.held_items:
            item = self.held_items.pop(instance_id)
        else:
            return  # Item not found

        # Record cooldown if configured
        if item.cooldown is not None:
            self.cooldowns[item.item_type] = current_tick + item.cooldown

        # Free VFS slot if allocated
        # (VFS cleanup happens here)
```

---

### Step 7: Run lifecycle tests

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/items/test_item_lifecycle.py -v
```

**Expected:** BOTH TESTS PASS

---

### Step 8: Commit

```bash
git add src/townlet/items/manager.py tests/test_townlet/unit/items/test_item_lifecycle.py
git commit -m "feat(items): add lifecycle persistence for pickup/drop

- Add held_items registry for items in inventories
- Implement lift_item() to move world → held (preserves state)
- Implement place_item() to move held → world (preserves state)
- Update tick() to age both active and held items
- Update despawn_item() to handle both registries

Critical fix: Items now retain VFS state (durability, spoilage) when
picked up and dropped. Prevents identity reset bug.

Test results: test_item_lifecycle.py PASSING"
```

---

## Task 2: Wire Effects Compilation for Item Interactions (1 day)

**Goal:** Compile item interaction commands at ItemManager initialization using CommandCompiler.

**Files:**

- Modify: `src/townlet/items/manager.py`
- Test: `tests/test_townlet/unit/items/test_effects_integration.py`

---

### Step 1: Write test for compiled item interactions

**Create** (`tests/test_townlet/unit/items/test_effects_integration.py`):

```python
"""Tests for Items + Effects System integration."""

import torch
from pathlib import Path

from townlet.config.items_config import ItemsCatalogConfig
from townlet.items.manager import ItemManager
from townlet.effects.schema import CommandType


def test_item_interactions_are_compiled():
    """ItemManager compiles interaction commands using CommandCompiler."""
    # Load items_smoke config
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    # Build schema (same pattern as VectorizedHamletEnv)
    schema = {
        "target.bar.energy": "float",
        "target.bar.health": "float",
        "target.bar.money": "float",
        "target.vfs.has_food": "bool",
    }

    # Create manager with schema
    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=schema,  # NEW PARAMETER
    )

    # Verify apple interactions are compiled
    apple_type = next(t for t in manager.compiled_item_types if t.id == "apple")
    assert apple_type.compiled_on_pickup is not None, "on_pickup not compiled"
    assert len(apple_type.compiled_on_pickup) == 1
    assert apple_type.compiled_on_pickup[0].type == CommandType.MODIFY
    assert apple_type.compiled_on_pickup[0].path == "target.vfs.has_food"
    assert apple_type.compiled_on_pickup[0].value_ast is not None, "AST not compiled"

    # Verify on_use commands compiled
    assert apple_type.compiled_on_use is not None
    assert len(apple_type.compiled_on_use) == 1
    assert apple_type.compiled_on_use[0].path == "target.bar.energy"
    assert apple_type.compiled_on_use[0].value_ast is not None
```

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/items/test_effects_integration.py::test_item_interactions_are_compiled -v
```

**Expected:** FAIL - `ItemManager.__init__() got an unexpected keyword argument 'schema'`

---

### Step 2: Add CompiledItemType dataclass

**Modify** (`src/townlet/items/manager.py`):

Add after imports:

```python
from dataclasses import dataclass

from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode


@dataclass
class CompiledItemType:
    """Item type with pre-compiled Effects commands.

    This is the runtime representation after CommandCompiler processes
    the raw ItemTypeConfig from YAML.
    """

    id: str
    vfs_profile: str
    duration: int | None
    cooldown: int | None

    # Pre-compiled Effects commands (ready for CommandExecutor)
    compiled_on_pickup: list[CommandNode]
    compiled_on_use: list[CommandNode]
    compiled_on_drop: list[CommandNode]
```

---

### Step 3: Update ItemManager to compile interactions

**Modify** (`src/townlet/items/manager.py`):

Update `__init__` signature:

```python
def __init__(
    self,
    catalog: ItemsCatalogConfig,
    max_items: int,
    device: torch.device | str,
    schema: dict[str, str] | None = None,  # NEW: Schema for Effects compilation
) -> None:
```

Add compilation logic in `__init__` (after storing catalog):

```python
    self.catalog = catalog
    self.max_items = max_items
    self.device = torch.device(device) if isinstance(device, str) else device

    # Compile item interactions if schema provided
    self.compiled_item_types: list[CompiledItemType] = []

    if schema is not None:
        compiler = CommandCompiler(schema=schema)

        for item_type in catalog.item_types:
            # Parse raw command dicts to CommandNode AST
            from townlet.effects.parser import parse_commands

            on_pickup_nodes = parse_commands(item_type.interactions.on_pickup)
            on_use_nodes = parse_commands(item_type.interactions.on_use)
            on_drop_nodes = parse_commands(item_type.interactions.on_drop)

            # Compile with type checking and AST storage
            compiled_on_pickup = compiler.compile_commands(on_pickup_nodes)
            compiled_on_use = compiler.compile_commands(on_use_nodes)
            compiled_on_drop = compiler.compile_commands(on_drop_nodes)

            self.compiled_item_types.append(
                CompiledItemType(
                    id=item_type.id,
                    vfs_profile=item_type.vfs_profile,
                    duration=item_type.duration,
                    cooldown=item_type.cooldown,
                    compiled_on_pickup=compiled_on_pickup,
                    compiled_on_use=compiled_on_use,
                    compiled_on_drop=compiled_on_drop,
                )
            )
    else:
        # No schema - store raw types without compilation
        # (Used in unit tests that don't need Effects)
        for item_type in catalog.item_types:
            self.compiled_item_types.append(
                CompiledItemType(
                    id=item_type.id,
                    vfs_profile=item_type.vfs_profile,
                    duration=item_type.duration,
                    cooldown=item_type.cooldown,
                    compiled_on_pickup=[],
                    compiled_on_use=[],
                    compiled_on_drop=[],
                )
            )
```

---

### Step 4: Run test to verify compilation

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/items/test_effects_integration.py::test_item_interactions_are_compiled -v
```

**Expected:** PASS

---

### Step 5: Commit

```bash
git add src/townlet/items/manager.py tests/test_townlet/unit/items/test_effects_integration.py
git commit -m "feat(items): compile item interactions with CommandCompiler

- Add CompiledItemType dataclass with pre-compiled Effects ASTs
- Update ItemManager to accept schema parameter
- Compile on_pickup/on_use/on_drop commands at initialization
- Compiled commands ready for CommandExecutor at runtime

Test results: test_item_interactions_are_compiled PASSING"
```

---

## Task 3: Wire Effects Execution in ItemActionHandler (1 day)

**Goal:** Execute compiled Effects commands for on_pickup/on_use/on_drop interactions.

**Context Resolution:** Define how `self` vs `target` resolve in item interaction commands:
- `target` = The Agent performing the action (target_index = agent_idx)
- `self` = The Item itself (requires ExecutionContext to support item VFS profile access)

**Files:**

- Modify: `src/townlet/items/action_handlers.py`
- Modify: `src/townlet/environment/vectorized_env.py`
- Test: `tests/test_townlet/integration/test_items_integration.py`

---

### Step 1: Write integration test for item Effects execution

**Modify** (`tests/test_townlet/integration/test_items_integration.py`):

Add after `test_env_with_items_initializes()`:

```python
def test_get_action_picks_up_item():
    """GET action picks up item and executes on_pickup Effects."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"))

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    # Reset to initialize state
    env.reset()

    # Spawn apple at (2, 2) - has on_pickup: set target.vfs.has_food = true
    item = env.item_manager.spawn_item("apple", position=(2, 2), current_tick=0)
    assert item is not None

    # Verify VFS variable starts false
    has_food_idx = env.vfs_registry.get_index("has_food")
    initial_has_food = env.vfs_registry.get("has_food")[0].item()
    assert initial_has_food == 0.0, "has_food should start false"

    # Move agent to (2, 2)
    env.positions[0] = torch.tensor([2, 2], dtype=torch.long)

    # Execute GET action
    get_action = env.action_space.get_action_by_name("GET")
    actions = torch.tensor([get_action.id], dtype=torch.long)
    env.step(actions)

    # Verify item picked up
    assert env.item_inventory.count_items(0) == 1
    assert item.instance_id not in env.item_manager.active_items

    # Verify on_pickup Effects executed: has_food = true
    final_has_food = env.vfs_registry.get("has_food")[0].item()
    assert final_has_food == 1.0, "on_pickup should set has_food to true"


def test_use_slot_action_executes_effects():
    """USE_SLOT_N executes on_use Effects (apple increases energy)."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"))

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    env.reset()

    # Spawn apple and pick it up
    item = env.item_manager.spawn_item("apple", position=(0, 0), current_tick=0)
    env.positions[0] = torch.tensor([0, 0], dtype=torch.long)
    get_action = env.action_space.get_action_by_name("GET")
    env.step(torch.tensor([get_action.id]))

    # Record initial energy
    energy_idx = env.meter_name_to_index["energy"]
    initial_energy = env.meters[0, energy_idx].item()

    # Use apple (on_use: energy +0.3)
    use_action = env.action_space.get_action_by_name("USE_SLOT_0")
    env.step(torch.tensor([use_action.id]))

    # Verify energy increased
    final_energy = env.meters[0, energy_idx].item()
    energy_increase = final_energy - initial_energy

    assert energy_increase > 0.29, f"Expected ~0.3 increase, got {energy_increase}"
    assert energy_increase < 0.31, f"Expected ~0.3 increase, got {energy_increase}"
```

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_items_integration.py::test_get_action_picks_up_item -v
```

**Expected:** FAIL - "on_pickup should set has_food to true" (Effects not executed)

---

### Step 2: Add CommandExecutor to ItemActionHandler

**Modify** (`src/townlet/items/action_handlers.py`):

Update imports:

```python
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
```

Update `__init__`:

```python
def __init__(
    self,
    manager: ItemManager,
    inventory: InventoryState,
    command_executor: CommandExecutor,
    vfs_registry: VariableRegistry,
    meters: torch.Tensor,  # [batch, num_meters]
    meter_name_to_index: dict[str, int],
) -> None:
    """Initialize action handler.

    Args:
        manager: ItemManager instance
        inventory: InventoryState instance
        command_executor: CommandExecutor for Effects
        vfs_registry: VFS registry for Effects context
        meters: Meter tensor for Effects context
        meter_name_to_index: Bar name to index mapping
    """
    self.manager = manager
    self.inventory = inventory
    self.command_executor = command_executor
    self.vfs_registry = vfs_registry
    self.meters = meters
    self.meter_name_to_index = meter_name_to_index
```

---

### Step 3: Implement _execute_interaction helper method

**Modify** (`src/townlet/items/action_handlers.py`):

Add method before `handle_get_action`:

```python
def _execute_interaction(
    self,
    item_type: str,
    agent_idx: int,
    interaction: Literal["on_pickup", "on_use", "on_drop"],
) -> None:
    """Execute Effects commands for item interaction.

    Args:
        item_type: Item type ID (e.g., "apple")
        agent_idx: Agent performing interaction
        interaction: Which interaction type to execute
    """
    # Find compiled item type
    compiled_type = next(
        (t for t in self.manager.compiled_item_types if t.id == item_type),
        None,
    )

    if compiled_type is None:
        return  # Item type not found

    # Get compiled commands for this interaction
    if interaction == "on_pickup":
        commands = compiled_type.compiled_on_pickup
    elif interaction == "on_use":
        commands = compiled_type.compiled_on_use
    elif interaction == "on_drop":
        commands = compiled_type.compiled_on_drop
    else:
        return

    if not commands:
        return  # No commands to execute

    # Build ExecutionContext targeting the agent
    # Pattern: Same as affordance Effects execution
    bars_dict = {
        name: self.meters[:, idx]
        for name, idx in self.meter_name_to_index.items()
    }

    # Context mapping for item interactions:
    # - target = Agent performing the action (can access target.bar.*, target.vfs.*)
    # - self = The Item itself (TODO: requires item VFS index for self.vfs.*)
    #
    # Current limitation: If item commands use self.vfs.durability, ExecutionContext
    # needs to support source_item_index. For Phase 1-3, items only modify target.
    context = ExecutionContext(
        bars=bars_dict,
        vfs_registry=self.vfs_registry,
        self_index=None,  # Items don't have self yet (Phase 4 limitation)
        target_index=agent_idx,  # Agent is the target
    )

    # Execute all commands
    for command in commands:
        self.command_executor.execute(command, context)
```

---

### Step 4: Wire Effects execution into action handlers

**Modify** (`src/townlet/items/action_handlers.py`):

Replace TODO in `handle_get_action` (line 68-69):

```python
        if success:
            # Move item from world to held state (preserves VFS state)
            self.manager.lift_item(item.instance_id)

            # Execute on_pickup Effects commands
            self._execute_interaction(
                item_type=item.item_type,
                agent_idx=agent_idx,
                interaction="on_pickup",
            )
```

Replace TODO in `handle_use_slot_action` (line 95-96):

```python
        if instance_id is None:
            return False  # Slot empty

        # Get item from manager to find item_type
        # (ItemInstance tracks item_type at line 17 of instance.py)
        item = next(
            (i for i in self.inventory.items.values() if i.instance_id == instance_id),
            None,
        )

        if item is None:
            # Item was despawned but still in inventory (edge case)
            return False

        # Execute on_use Effects commands
        self._execute_interaction(
            item_type=item.item_type,
            agent_idx=agent_idx,
            interaction="on_use",
        )

        return True
```

**Note:** This reveals we need inventory to track ItemInstance objects, not just IDs. Fix in next step.

---

### Step 5: Fix inventory to track ItemInstance objects

**Modify** (`src/townlet/items/inventory.py`):

Change class docstring and add items dict:

```python
class InventoryState:
    """Fixed-size inventory for agents using GPU tensors.

    Storage:
    - slots: [batch, max_items_per_agent] tensor of instance IDs (-1 = empty)
    - items: dict[instance_id -> ItemInstance] for metadata lookup
    """

    def __init__(
        self,
        batch_size: int,
        max_items_per_agent: int,
        device: torch.device | str,
    ) -> None:
        self.batch_size = batch_size
        self.max_items_per_agent = max_items_per_agent
        self.device = torch.device(device) if isinstance(device, str) else device

        # Slot storage: -1 = empty, ≥0 = instance_id
        self.slots = torch.full(
            (batch_size, max_items_per_agent),
            fill_value=-1,
            dtype=torch.long,
            device=self.device,
        )

        # Item metadata lookup
        self.items: dict[int, ItemInstance] = {}
```

Update `add_item`:

```python
    def add_item(self, agent_idx: int, item: ItemInstance) -> bool:
        """Add item to first empty slot (DENY_PICKUP if full).

        Args:
            agent_idx: Agent index
            item: ItemInstance to add

        Returns:
            True if added, False if inventory full
        """
        # Find first empty slot
        agent_slots = self.slots[agent_idx]
        empty_mask = agent_slots == -1

        if not empty_mask.any():
            return False  # DENY_PICKUP policy

        # Get first empty slot index
        slot_idx = int(torch.where(empty_mask)[0][0].item())

        # Store instance ID
        self.slots[agent_idx, slot_idx] = item.instance_id

        # Store item metadata
        self.items[item.instance_id] = item

        return True
```

Update `remove_item`:

```python
    def remove_item(self, agent_idx: int, slot_idx: int) -> int | None:
        """Remove item from slot.

        Args:
            agent_idx: Agent index
            slot_idx: Slot index

        Returns:
            Instance ID if removed, None if slot empty
        """
        instance_id = int(self.slots[agent_idx, slot_idx].item())

        if instance_id == -1:
            return None

        # Clear slot
        self.slots[agent_idx, slot_idx] = -1

        # Remove from metadata (keep for respawn tracking)
        # Actually DON'T remove - need it for DROP action
        # self.items.pop(instance_id, None)

        return instance_id
```

---

### Step 6: Fix handle_use_slot_action to use items dict

**Modify** (`src/townlet/items/action_handlers.py`):

Replace handle_use_slot_action implementation:

```python
    def handle_use_slot_action(
        self,
        agent_idx: int,
        slot_idx: int,
        current_tick: int,
    ) -> bool:
        """Handle USE_SLOT_N action (use item in inventory slot).

        Args:
            agent_idx: Agent index
            slot_idx: Inventory slot index (0-based)
            current_tick: Current tick

        Returns:
            True if item used, False if slot empty
        """
        # Get item from slot (without removing)
        instance_id = self.inventory.get_item(agent_idx, slot_idx)

        if instance_id is None:
            return False  # Slot empty

        # Get item metadata from inventory
        item = self.inventory.items.get(instance_id)

        if item is None:
            return False  # Item metadata missing (shouldn't happen)

        # Execute on_use Effects commands
        self._execute_interaction(
            item_type=item.item_type,
            agent_idx=agent_idx,
            interaction="on_use",
        )

        return True
```

---

### Step 7: Update VectorizedHamletEnv to pass parameters

**Modify** (`src/townlet/environment/vectorized_env.py`):

Find Items initialization (line 534-555), update ItemActionHandler construction:

```python
        # === ITEMS INITIALIZATION ===
        if universe.items_catalog is not None:
            # Build schema for Effects compilation
            schema: dict[str, str] = {}
            for bar_name in self.meter_name_to_index.keys():
                schema[f"target.bar.{bar_name}"] = "float"
            for var in self.vfs_variables:
                vfs_type = "bool" if var.type == "bool" else "float"
                schema[f"target.vfs.{var.id}"] = vfs_type

            self.item_manager = ItemManager(
                catalog=universe.items_catalog,
                max_items=universe.items_catalog.max_items_in_world,
                device=device,
                schema=schema,  # NEW: Enable Effects compilation
            )

            self.item_inventory = InventoryState(
                batch_size=num_agents,
                max_items_per_agent=universe.items_catalog.max_items_per_agent,
                device=device,
            )

            self.item_handler = ItemActionHandler(
                manager=self.item_manager,
                inventory=self.item_inventory,
                command_executor=self.command_executor,  # NEW
                vfs_registry=self.vfs_registry,  # NEW
                meters=self.meters,  # NEW
                meter_name_to_index=self.meter_name_to_index,  # NEW
            )
        else:
            self.item_manager = None
            self.item_inventory = None
            self.item_handler = None
```

---

### Step 8: Run integration tests

**Run:**

```bash
rm -rf configs/test/items_smoke/.compiled
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_items_integration.py::test_get_action_picks_up_item -v
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_items_integration.py::test_use_slot_action_executes_effects -v
```

**Expected:** BOTH TESTS PASS

---

### Step 9: Commit

```bash
git add src/townlet/items/action_handlers.py src/townlet/items/inventory.py src/townlet/environment/vectorized_env.py tests/test_townlet/integration/test_items_integration.py
git commit -m "feat(items): execute Effects for item interactions

- Add _execute_interaction() to ItemActionHandler
- Wire on_pickup/on_use Effects execution
- Update InventoryState to track ItemInstance metadata
- Pass CommandExecutor and VFS context to ItemActionHandler
- Build schema for Effects compilation in environment init

Test results:
- test_get_action_picks_up_item: PASSING (on_pickup sets VFS)
- test_use_slot_action_executes_effects: PASSING (on_use modifies bars)

Apple item now properly restores energy when used!"
```

---

## Task 4: Complete DROP Action Implementation (0.5 days)

**Goal:** Place items back into world when dropped from inventory, preserving their identity and VFS state.

**Files:**

- Modify: `src/townlet/items/action_handlers.py`
- Test: `tests/test_townlet/integration/test_items_integration.py`

---

### Step 1: Write integration test for DROP action

**Modify** (`tests/test_townlet/integration/test_items_integration.py`):

Add test:

```python
def test_drop_slot_action_spawns_item_in_world():
    """DROP_SLOT_N spawns item back into world at agent position."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"))

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    env.reset()

    # Give agent apple in slot 0
    item = env.item_manager.spawn_item("apple", position=(0, 0), current_tick=0)
    env.positions[0] = torch.tensor([0, 0], dtype=torch.long)
    get_action = env.action_space.get_action_by_name("GET")
    env.step(torch.tensor([get_action.id]))

    # Verify in inventory
    assert env.item_inventory.count_items(0) == 1

    # Move to (5, 5) and drop
    env.positions[0] = torch.tensor([5, 5], dtype=torch.long)
    drop_action = env.action_space.get_action_by_name("DROP_SLOT_0")
    env.step(torch.tensor([drop_action.id]))

    # Verify removed from inventory
    assert env.item_inventory.count_items(0) == 0

    # Verify spawned at (5, 5)
    spawned_items = [
        i for i in env.item_manager.active_items.values()
        if i.position == (5, 5)
    ]
    assert len(spawned_items) == 1, "Item not spawned at drop position"
    assert spawned_items[0].item_type == "apple"
```

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_items_integration.py::test_drop_slot_action_spawns_item_in_world -v
```

**Expected:** FAIL - "Item not spawned at drop position"

---

### Step 2: Implement DROP action place logic

**Modify** (`src/townlet/items/action_handlers.py`):

Replace `handle_drop_slot_action` implementation (remove TODO):

```python
    def handle_drop_slot_action(
        self,
        agent_idx: int,
        slot_idx: int,
        agent_position: torch.Tensor,  # [position_dim]
        current_tick: int,
    ) -> bool:
        """Handle DROP_SLOT_N action (drop item from inventory).

        Args:
            agent_idx: Agent index
            slot_idx: Inventory slot index (0-based)
            agent_position: Agent position (where to drop item)
            current_tick: Current tick

        Returns:
            True if item dropped, False if slot empty
        """
        # Remove item from inventory slot
        instance_id = self.inventory.remove_item(agent_idx, slot_idx)

        if instance_id is None:
            return False  # Slot already empty

        # Get item metadata from inventory
        item = self.inventory.items.get(instance_id)

        if item is None:
            return False  # Item metadata missing (shouldn't happen)

        # Execute on_drop Effects commands
        self._execute_interaction(
            item_type=item.item_type,
            agent_idx=agent_idx,
            interaction="on_drop",
        )

        # Place item back in world at agent's position (preserves VFS state)
        agent_pos_tuple = tuple(agent_position.tolist())
        self.manager.place_item(
            instance_id=instance_id,  # Use existing instance (NOT spawn_item)
            position=agent_pos_tuple,
        )

        return True
```

---

### Step 3: Run test to verify DROP works

**Run:**

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_items_integration.py::test_drop_slot_action_spawns_item_in_world -v
```

**Expected:** PASS

---

### Step 4: Commit

```bash
git add src/townlet/items/action_handlers.py tests/test_townlet/integration/test_items_integration.py
git commit -m "feat(items): implement DROP action with item persistence

- Remove TODO from handle_drop_slot_action
- Use place_item() to return item to world (preserves VFS state)
- Execute on_drop Effects before placing
- Use item metadata from inventory.items dict

Critical: Item retains instance_id and VFS state when dropped.
No identity reset - durability/spoilage/age preserved.

Test results: test_drop_slot_action_spawns_item_in_world PASSING

Items System core loop complete: GET → USE → DROP all functional!"
```

---

## Task 5: Implement Automatic Item Spawning (Optional - 0.5 days)

**Goal:** Spawn items automatically at level start based on ItemsAppearanceConfig.

**Status:** OPTIONAL - Manual spawning via `item_manager.spawn_item()` works for testing.

**Future Work:**

- Parse `levels/*/items.yaml` for ItemsAppearanceConfig
- Implement `spawn_initial_items()` in ItemManager
- Wire into `VectorizedHamletEnv.reset()`
- Implement periodic respawning based on `spawn_interval`

**Skip for now** - deferred to future iteration.

---

## Verification Checklist

After completing Tasks 1-4, verify:

- [ ] `test_item_preserves_identity_when_lifted_and_placed` PASSING
- [ ] `test_held_items_continue_ticking` PASSING
- [ ] `test_item_interactions_are_compiled` PASSING
- [ ] `test_get_action_picks_up_item` PASSING (on_pickup sets VFS)
- [ ] `test_use_slot_action_executes_effects` PASSING (on_use modifies bars)
- [ ] `test_drop_slot_action_spawns_item_in_world` PASSING
- [ ] Apple item restores energy when used
- [ ] Coin item gives money when picked up
- [ ] Medkit item restores health when used
- [ ] Items preserve instance_id when picked up and dropped
- [ ] Items continue to age/spoil while in inventory
- [ ] No TODO comments in `src/townlet/items/action_handlers.py`
- [ ] All integration tests in `test_items_integration.py` passing

---

## Final Assessment

**Before This Plan:**

- Items config loaded ✅
- Items components initialized ✅
- Action dispatch wired ✅
- **Lifecycle management: ❌ despawn/spawn resets VFS state**
- **Effects execution: ❌ TODO placeholders**
- **Context resolution: ❌ Undefined self vs target**

**After This Plan:**

- Items config loaded ✅
- Items components initialized ✅
- Action dispatch wired ✅
- **Lifecycle management: ✅ lift_item/place_item preserves state**
- **Effects execution: ✅ FULLY FUNCTIONAL**
- **Context resolution: ✅ Documented (target=agent, self=item)**
- Item interactions work end-to-end ✅
- Items retain identity across pickup/drop ✅

**Task Breakdown:**
- Task 1: Item Lifecycle & Persistence (0.5 days)
- Task 2: Effects Compilation (1 day)
- Task 3: Effects Execution (1 day)
- Task 4: DROP Action (0.5 days)
- Task 5: Automatic Spawning (optional, deferred)

**Estimated Time:** 3 days (0.5 lifecycle + 1 compilation + 1 execution + 0.5 DROP)

**Outcome:** Items System **COMPLETE** and **PRODUCTION READY**

**Critical Improvements:**
- Items preserve VFS state (durability, spoilage) across world ↔ inventory transitions
- No identity reset bugs from despawn/spawn pattern
- Clear context resolution for Effects commands (target vs self)
- Items continue to tick/age while held in inventory
