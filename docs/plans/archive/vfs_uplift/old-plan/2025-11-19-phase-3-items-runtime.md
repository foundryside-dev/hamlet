# Items & VFS Profiles - Phase 3: Items Runtime + Inventory

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement runtime item management (ItemManager), agent inventories, and interaction effects (pickup/use/drop).

**Architecture:** Create stateless ItemManager module, extend VectorizedEnv with inventory state, wire action handlers (GET, USE_SLOT_N, DROP_SLOT_N), implement effect application.

**Tech Stack:** Python 3.13, PyTorch, pytest

**Prerequisites:**
- Phase 2 complete (VFS Engine + DynObs passing all tests)
- Observation builder produces VFS observations
- CompiledUniverse contains item catalogs and spawn plans

**Estimated Time:** 32-48 hours implementation + 16-24 hours testing = 8-10 days

---

## Key Tasks Overview

1. **ItemManager Module** (12-16 hours)
   - ItemInstance dataclass (id, type_id, position, holder, VFS state)
   - Spawn/despawn logic with lifecycle management
   - Pickup/drop/use handlers

2. **Inventory Integration** (8-12 hours)
   - Agent inventory state ([batch, max_items_per_agent] slots)
   - Inventory mask for observations
   - max_items_per_agent enforcement

3. **Action Handlers** (8-12 hours)
   - GET action: Transfer item world → inventory
   - USE_SLOT_N action: Apply effects, optionally consume item
   - DROP_SLOT_N action: Transfer item inventory → world

4. **Effect Application** (4-6 hours)
   - Parse ItemInteractionEffectConfig (opaque dicts)
   - Apply bar deltas, VFS updates
   - Durability/consumption mechanics

---

## Task 1: Create ItemManager Module

**Files:**
- Create: `src/townlet/environment/item_manager.py`
- Test: `tests/test_townlet/unit/environment/test_item_manager.py`

### Implementation Steps

**Step 1: Write failing test for ItemInstance**

```python
def test_item_instance_creation():
    """ItemInstance holds state for one item."""
    item = ItemInstance(
        id=0,
        type_id="umbrella",
        position=torch.tensor([2.0, 3.0]),
        holder_agent_id=None,  # Not held
        spawn_step=10,
        expire_step=60,  # Despawns at step 60
        vfs_state_idx=5,  # Index into item VFS storage
    )

    assert item.type_id == "umbrella"
    assert item.holder_agent_id is None
    assert item.is_in_world() is True
    assert item.is_held() is False
```

**Step 2: Implement ItemInstance dataclass**

```python
# src/townlet/environment/item_manager.py

from dataclasses import dataclass
import torch


@dataclass
class ItemInstance:
    """Runtime instance of an item."""
    id: int  # Unique instance ID
    type_id: str  # Item type from catalog
    position: torch.Tensor  # [2] or [3] spatial coords (or None for aspatial)
    holder_agent_id: int | None  # Agent holding this item (None = in world)
    spawn_step: int  # Step when spawned
    expire_step: int  # Step when despawns (-1 = never)
    vfs_state_idx: int  # Index into item VFS storage tensors

    def is_in_world(self) -> bool:
        """Item is placed in world (not held)."""
        return self.holder_agent_id is None

    def is_held(self) -> bool:
        """Item is held by an agent."""
        return self.holder_agent_id is not None
```

**Step 3: Write test for ItemManager initialization**

```python
def test_item_manager_init():
    """ItemManager initializes with catalog and spawn plans."""
    catalog = ItemsCatalogConfig(
        version="1.0",
        item_types=[
            ItemTypeConfig(id="umbrella", name="Umbrella", icon="☂️", tags=[], vfs_profiles=[], interactions={})
        ],
    )

    spawn_plans = {
        "L0_test": ItemsAppearanceConfig(
            version="1.0",
            inventory=InventoryConfig(max_items_per_agent=3),
            spawn_rules=[
                ItemSpawnRuleConfig(
                    type_id="umbrella",
                    placement={"mode": "random", "positions": []},
                    schedule={"kind": "once", "params": {}},
                    limits={"max_simultaneous": 3, "max_total": 10},
                    lifecycle={"duration_steps": 50, "cooldown_steps": 20},
                    priority=10,
                    conditions=[],
                )
            ],
        )
    }

    manager = ItemManager(
        catalog=catalog,
        spawn_plans=spawn_plans,
        level_name="L0_test",
        device=torch.device("cpu"),
    )

    assert manager.max_items_per_agent == 3
    assert len(manager.active_items) == 0  # No items spawned yet
```

**Step 4: Implement ItemManager class**

```python
class ItemManager:
    """Manages item instances, spawning, and interactions (Phase 1: basic lifecycle)."""

    def __init__(
        self,
        catalog: ItemsCatalogConfig,
        spawn_plans: dict[str, ItemsAppearanceConfig],
        level_name: str,
        device: torch.device,
    ):
        self.catalog = catalog
        self.device = device

        # Load level-specific config
        self.appearance = spawn_plans[level_name]
        self.max_items_per_agent = self.appearance.inventory.max_items_per_agent
        self.spawn_rules = self.appearance.spawn_rules

        # Active item instances
        self.active_items: dict[int, ItemInstance] = {}
        self.next_item_id = 0

        # Catalog lookup
        self.item_types = {item.id: item for item in catalog.item_types}

    def spawn_item(self, type_id: str, position: torch.Tensor, current_step: int) -> ItemInstance:
        """Spawn a new item instance."""
        item_type = self.item_types[type_id]

        # Create instance
        item = ItemInstance(
            id=self.next_item_id,
            type_id=type_id,
            position=position,
            holder_agent_id=None,
            spawn_step=current_step,
            expire_step=current_step + 50,  # TODO: Read from lifecycle config
            vfs_state_idx=self.next_item_id,  # TODO: Allocate from VFS pool
        )

        self.active_items[item.id] = item
        self.next_item_id += 1

        return item

    def despawn_item(self, item_id: int) -> None:
        """Remove item from world."""
        del self.active_items[item_id]

    def step(self, current_step: int) -> None:
        """Update items (despawn expired, spawn scheduled)."""
        # Phase 1: Only despawn expired items
        expired = [
            item_id
            for item_id, item in self.active_items.items()
            if item.expire_step != -1 and current_step >= item.expire_step
        ]
        for item_id in expired:
            self.despawn_item(item_id)

        # Phase 4: Implement scheduled spawning
```

**Step 5-6:** Run tests, commit

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/unit/environment/test_item_manager.py::test_item_instance_creation -v

git add src/townlet/environment/item_manager.py tests/test_townlet/unit/environment/test_item_manager.py
git commit -m "feat(items): add ItemManager with spawn/despawn (Phase 1 lifecycle)"
```

---

## Task 2: Inventory Integration

**Files:**
- Modify: `src/townlet/environment/vectorized_env.py`
- Test: `tests/test_townlet/unit/environment/test_inventory.py`

### Implementation Steps

**Step 1: Write test for inventory state**

```python
def test_inventory_initialization():
    """Environment initializes inventory state for agents."""
    env = VectorizedHamletEnv(
        config=...,  # With items enabled
        num_agents=10,
    )

    # Inventory: [num_agents, max_items_per_agent]
    assert env.inventory.shape == (10, 3)
    assert env.inventory.dtype == torch.int64  # Stores item IDs (-1 = empty)

    # Inventory mask: [num_agents, max_items_per_agent]
    assert env.inventory_mask.shape == (10, 3)
    assert env.inventory_mask.dtype == torch.bool

    # Initially all empty
    assert torch.all(env.inventory == -1)
    assert torch.all(env.inventory_mask == False)
```

**Step 2: Add inventory fields to VectorizedEnv**

```python
# src/townlet/environment/vectorized_env.py

class VectorizedHamletEnv:
    def __init__(self, config, num_agents):
        # ... existing initialization ...

        # NEW: Item inventory state
        if config.items_enabled:
            max_items = config.inventory.max_items_per_agent
            self.inventory = torch.full(
                (num_agents, max_items), -1, dtype=torch.int64, device=self.device
            )  # -1 = empty slot
            self.inventory_mask = torch.zeros(
                (num_agents, max_items), dtype=torch.bool, device=self.device
            )  # True = slot has item
        else:
            self.inventory = None
            self.inventory_mask = None
```

**Step 3-5:** Run tests, commit

---

## Task 3: Action Handlers (GET/USE/DROP)

**Files:**
- Modify: `src/townlet/environment/vectorized_env.py`
- Test: `tests/test_townlet/unit/environment/test_item_actions.py`

### Implementation Steps

**Step 1: Write test for GET action**

```python
def test_get_action_pickup_item():
    """GET action transfers item from world to inventory."""
    env = setup_env_with_items()

    # Spawn item at agent 0's position
    item_id = env.item_manager.spawn_item(
        type_id="umbrella", position=env.agent_positions[0], current_step=0
    )

    # Agent 0 executes GET action
    actions = torch.zeros(env.num_agents, dtype=torch.int64)
    actions[0] = ACTION_GET

    env.step(actions)

    # Verify: item removed from world
    assert item_id not in env.item_manager.active_items

    # Verify: item added to inventory slot 0
    assert env.inventory[0, 0] == item_id
    assert env.inventory_mask[0, 0] == True
```

**Step 2: Implement GET action handler**

```python
# src/townlet/environment/vectorized_env.py

def _handle_get_action(self, agent_idx: int) -> None:
    """Handle GET action: pickup item at agent position."""
    # Find items at agent position
    items_here = [
        item
        for item in self.item_manager.active_items.values()
        if item.is_in_world()
        and torch.allclose(item.position, self.agent_positions[agent_idx])
    ]

    if not items_here:
        return  # No item to pickup

    # Check inventory capacity
    empty_slots = (self.inventory[agent_idx] == -1).nonzero(as_tuple=True)[0]
    if len(empty_slots) == 0:
        # Inventory full: DENY pickup (Phase 1 policy)
        return

    # Pickup first item
    item = items_here[0]
    slot_idx = empty_slots[0].item()

    # Transfer item world → inventory
    item.holder_agent_id = agent_idx
    self.inventory[agent_idx, slot_idx] = item.id
    self.inventory_mask[agent_idx, slot_idx] = True

    # Apply pickup effects (Phase 3)
    self._apply_interaction_effects(item, "pickup", agent_idx)
```

**Step 3: Implement USE and DROP similarly**

```python
def _handle_use_slot_n_action(self, agent_idx: int, slot_idx: int) -> None:
    """Handle USE_SLOT_N action: use item in slot."""
    if not self.inventory_mask[agent_idx, slot_idx]:
        return  # Slot empty

    item_id = self.inventory[agent_idx, slot_idx].item()
    item = self.item_manager.active_items[item_id]

    # Apply use effects
    self._apply_interaction_effects(item, "use", agent_idx)

    # TODO: Check if item is consumable (remove from inventory)

def _handle_drop_slot_n_action(self, agent_idx: int, slot_idx: int) -> None:
    """Handle DROP_SLOT_N action: drop item from slot."""
    if not self.inventory_mask[agent_idx, slot_idx]:
        return

    item_id = self.inventory[agent_idx, slot_idx].item()
    item = self.item_manager.active_items[item_id]

    # Transfer item inventory → world
    item.holder_agent_id = None
    item.position = self.agent_positions[agent_idx].clone()
    self.inventory[agent_idx, slot_idx] = -1
    self.inventory_mask[agent_idx, slot_idx] = False

    # Apply drop effects
    self._apply_interaction_effects(item, "drop", agent_idx)
```

**Step 4-5:** Run tests, commit

---

## Task 4: Effect Application

**Files:**
- Create: `src/townlet/environment/item_effects.py`
- Test: `tests/test_townlet/unit/environment/test_item_effects.py`

### Implementation Steps

**Step 1: Write test for bar effects**

```python
def test_apply_bar_effects():
    """Use effect applies bar deltas."""
    env = setup_env()

    # Medkit item with health boost
    item_type = ItemTypeConfig(
        id="medkit",
        interactions=ItemInteractionsConfig(
            use=ItemInteractionEffectConfig(
                bars=[{"name": "health", "delta": 0.3}]
            )
        ),
    )

    agent_idx = 0
    initial_health = env.bars["health"][agent_idx].item()

    apply_item_effects(env, item_type, "use", agent_idx)

    final_health = env.bars["health"][agent_idx].item()
    assert final_health == initial_health + 0.3
```

**Step 2: Implement apply_item_effects**

```python
# src/townlet/environment/item_effects.py

def apply_item_effects(
    env: VectorizedHamletEnv,
    item_type: ItemTypeConfig,
    interaction: str,  # "pickup" | "use" | "drop"
    agent_idx: int,
) -> None:
    """Apply item interaction effects (Phase 1: bar deltas only, VFS deferred)."""
    effects = getattr(item_type.interactions, interaction, None)
    if effects is None:
        return

    # Apply bar effects
    if effects.bars:
        for bar_effect in effects.bars:
            bar_name = bar_effect["name"]
            delta = bar_effect["delta"]
            env.bars[bar_name][agent_idx] += delta
            # Clamp to [0, 1]
            env.bars[bar_name][agent_idx] = torch.clamp(
                env.bars[bar_name][agent_idx], 0.0, 1.0
            )

    # TODO: Apply agent_vfs effects (Phase 2+)
    # TODO: Apply item_vfs effects (Phase 2+)
```

**Step 3-5:** Run tests, commit

---

## Task 5: Checkpoint Serialization

**Files:**
- Modify: `src/townlet/training/state.py`
- Test: `tests/test_townlet/unit/training/test_item_checkpoints.py`

### Implementation Steps

**Step 1: Write test for item state in checkpoints**

```python
def test_save_and_load_item_state():
    """Checkpoint includes item manager and inventory state."""
    env = setup_env_with_items()

    # Spawn items and populate inventories
    env.item_manager.spawn_item("umbrella", torch.tensor([1.0, 1.0]), current_step=0)
    env.inventory[0, 0] = 0  # Agent 0 holds item 0

    # Save checkpoint
    state = env.get_checkpoint_state()

    # Modify environment
    env.item_manager.despawn_item(0)
    env.inventory[:] = -1

    # Load checkpoint
    env.load_checkpoint_state(state)

    # Verify restored
    assert 0 in env.item_manager.active_items
    assert env.inventory[0, 0] == 0
```

**Step 2: Extend checkpoint state with item fields**

```python
# src/townlet/training/state.py

def get_checkpoint_state(env: VectorizedHamletEnv) -> dict:
    """Serialize environment state including items."""
    state = {
        # ... existing fields (bars, positions, etc.) ...
    }

    # NEW: Item state
    if env.item_manager is not None:
        state["items"] = {
            "active_items": [
                {
                    "id": item.id,
                    "type_id": item.type_id,
                    "position": item.position.cpu(),
                    "holder_agent_id": item.holder_agent_id,
                    "spawn_step": item.spawn_step,
                    "expire_step": item.expire_step,
                    "vfs_state_idx": item.vfs_state_idx,
                }
                for item in env.item_manager.active_items.values()
            ],
            "next_item_id": env.item_manager.next_item_id,
        }
        state["inventory"] = env.inventory.cpu()
        state["inventory_mask"] = env.inventory_mask.cpu()

    return state
```

**Step 3-5:** Run tests, commit

---

## Completion Criteria

Phase 3 is complete when:

- [x] ItemManager spawns/despawns items with lifecycle
- [x] Agent inventory state integrated into environment
- [x] GET/USE_SLOT_N/DROP_SLOT_N actions implemented
- [x] Item effects apply bar deltas
- [x] Checkpoint serialization includes items and inventory
- [x] Inventory limit enforcement (deny pickup when full)
- [ ] All unit tests passing (50+ tests)
- [ ] Integration tests passing
- [ ] Smoke test with items_smoke config pack

---

## Final Commit

```bash
git add -A
git commit -m "feat(items): Phase 3 complete - Items Runtime + Inventory

Phase 3 Deliverables:
- ItemManager with spawn/despawn lifecycle
- Agent inventory state ([num_agents, max_items_per_agent])
- Action handlers: GET, USE_SLOT_N, DROP_SLOT_N
- Item effects: bar deltas, VFS updates (partial)
- Checkpoint serialization for items and inventory
- Inventory overflow policy: deny pickup (Phase 1)

Items are now functional in runtime. Agents can pickup, use, and drop items.
Effects modify agent state (bars, VFS).

Ready for Phase 4 (Advanced Scheduling - Optional).
"
```

---

## Next Phase

**Phase 4: Advanced Scheduling (Optional)**

See: `docs/plans/vfs_uplift/2025-11-19-phase-4-advanced-scheduling.md`

**Note:** Phase 4 is NOT MVP-critical. Can be deferred to post-launch if schedule pressure.
