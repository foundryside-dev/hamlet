"""Integration tests for Items system in VectorizedHamletEnv."""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler


def test_items_smoke_config_pack_exists():
    """items_smoke config pack has all required files."""
    config_dir = Path("configs/test/items_smoke")

    # Core config files
    assert (config_dir / "items.yaml").exists(), "items.yaml missing"
    assert (config_dir / "substrate.yaml").exists(), "substrate.yaml missing"
    assert (config_dir / "bars.yaml").exists(), "bars.yaml missing"
    assert (config_dir / "affordances.yaml").exists(), "affordances.yaml missing"
    assert (config_dir / "training.yaml").exists(), "training.yaml missing"


def test_items_catalog_has_three_item_types():
    """items.yaml defines apple, medkit, coin."""
    import yaml

    config_path = Path("configs/test/items_smoke/items.yaml")
    with open(config_path) as f:
        data = yaml.safe_load(f)

    item_types = data["items"]["item_types"]
    item_ids = [item["id"] for item in item_types]

    assert len(item_ids) == 3, f"Expected 3 item types, got {len(item_ids)}"
    assert "apple" in item_ids, "apple item type missing"
    assert "medkit" in item_ids, "medkit item type missing"
    assert "coin" in item_ids, "coin item type missing"


def test_items_catalog_validates_with_schema():
    """items.yaml validates against ItemsCatalogConfig schema."""
    import yaml

    from townlet.config.items_config import ItemsCatalogConfig

    config_path = Path("configs/test/items_smoke/items.yaml")
    with open(config_path) as f:
        data = yaml.safe_load(f)

    # Should not raise ValidationError
    catalog = ItemsCatalogConfig(**data["items"])

    assert catalog.max_items_per_agent == 3
    assert catalog.max_items_in_world == 10
    assert len(catalog.item_types) == 3


def test_item_actions_are_auto_registered():
    """Item actions are auto-added to the action space when items are enabled."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), use_cache=False)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    action_names = {a.name for a in env.action_space.actions}

    assert "GET" in action_names, "GET action missing from auto-registered actions"
    for slot_idx in range(universe.items_catalog.max_items_per_agent):
        assert f"USE_SLOT_{slot_idx}" in action_names, f"USE_SLOT_{slot_idx} action missing"
        assert f"DROP_SLOT_{slot_idx}" in action_names, f"DROP_SLOT_{slot_idx} action missing"


def test_env_with_items_initializes():
    """Environment with ItemManager and InventoryState initializes correctly."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), use_cache=False)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=4,
        device="cpu",
    )

    # Verify Items components exist
    assert env.item_manager is not None, "ItemManager not initialized"
    assert env.item_inventory is not None, "InventoryState not initialized"
    assert env.item_handler is not None, "ItemActionHandler not initialized"

    # Verify inventory shape
    assert env.item_inventory.slots.shape == (4, 3), f"Expected (4, 3), got {env.item_inventory.slots.shape}"
    assert torch.all(env.item_inventory.slots == -1), "Inventory should start empty"


def test_get_action_picks_up_item():
    """GET action picks up item and executes on_pickup Effects."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), use_cache=False)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    # Reset to initialize state
    env.reset()

    # Spawn coin at (2, 2) - has on_pickup: money +0.1 (10 out of max 100)
    item = env.item_manager.spawn_item("coin", position=(2, 2), current_tick=0)
    assert item is not None

    # Record initial money
    money_idx = env.meter_name_to_index["money"]
    initial_money = env.meters[0, money_idx].item()

    # Move agent to (2, 2)
    env.positions[0] = torch.tensor([2, 2], dtype=torch.long)

    # Execute GET action
    get_action = env.action_space.get_action_by_name("GET")
    actions = torch.tensor([get_action.id], dtype=torch.long)
    env.step(actions)

    # Verify item picked up
    assert env.item_inventory.count_items(0) == 1
    assert item.instance_id not in env.item_manager.active_items

    # Verify on_pickup Effects executed: money increased by 0.1
    final_money = env.meters[0, money_idx].item()
    money_increase = final_money - initial_money
    assert money_increase > 0.09, f"Expected ~0.1 increase, got {money_increase}"
    assert money_increase < 0.11, f"Expected ~0.1 increase, got {money_increase}"


def test_use_slot_action_executes_effects():
    """USE_SLOT_N executes on_use Effects (apple increases energy)."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), use_cache=False)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    env.reset()

    # Spawn apple and pick it up
    env.item_manager.spawn_item("apple", position=(0, 0), current_tick=0)
    env.positions[0] = torch.tensor([0, 0], dtype=torch.long)
    get_action = env.action_space.get_action_by_name("GET")
    env.step(torch.tensor([get_action.id]))

    # Record initial energy
    energy_idx = env.meter_name_to_index["energy"]
    initial_energy = env.meters[0, energy_idx].item()

    # Use apple (on_use: energy +0.3)
    use_action = env.action_space.get_action_by_name("USE_SLOT_0")
    env.step(torch.tensor([use_action.id]))

    # Verify energy increased (accounting for meter decay during step)
    # Apple adds +0.3, but energy also decays during the step
    # Net result should be positive (item effect > decay)
    final_energy = env.meters[0, energy_idx].item()
    energy_increase = final_energy - initial_energy

    assert energy_increase > 0.0, f"Expected positive energy increase from apple, got {energy_increase}"


def test_drop_slot_action_spawns_item_in_world():
    """DROP_SLOT_N spawns item back into world at agent position."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), use_cache=False)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    env.reset()

    pickup_pos = (0, 0)
    # Ensure no other items occupy the pickup position
    for instance_id, item in list(env.item_manager.active_items.items()):
        if item.position == pickup_pos:
            env.item_manager.active_items.pop(instance_id)

    # Give agent apple in slot 0
    apple = env.item_manager.spawn_item("apple", position=(0, 0), current_tick=0)
    apple_instance_id = apple.instance_id  # Track the specific apple we spawned
    env.positions[0] = torch.tensor(pickup_pos, dtype=torch.long)
    get_action = env.action_space.get_action_by_name("GET")
    env.step(torch.tensor([get_action.id]))

    # Verify in inventory
    assert env.item_inventory.count_items(0) == 1

    # Move to (4, 4) and drop
    env.positions[0] = torch.tensor([4, 4], dtype=torch.long)
    drop_action = env.action_space.get_action_by_name("DROP_SLOT_0")
    env.step(torch.tensor([drop_action.id]))

    # Verify removed from inventory
    assert env.item_inventory.count_items(0) == 0

    # Verify OUR apple is in active_items at (4, 4)
    # (There may be other items at (4, 4) from random initial spawn)
    assert apple_instance_id in env.item_manager.active_items, "Dropped item not in active_items"
    dropped_apple = env.item_manager.active_items[apple_instance_id]
    assert dropped_apple.position == (4, 4), f"Dropped item at {dropped_apple.position}, expected (4, 4)"
    assert dropped_apple.item_type == "apple"


def test_automatic_item_spawning_at_reset():
    """Items spawn automatically at reset based on ItemsAppearanceConfig."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), use_cache=False)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    # Reset should spawn items according to levels/L0_smoke/items.yaml
    # - 3 apples
    # - 1 medkit
    # - 2 energy_drink (but energy_drink not in catalog, should skip)
    env.reset()

    # Count items by type
    active_items = list(env.item_manager.active_items.values())
    apple_count = sum(1 for item in active_items if item.item_type == "apple")
    medkit_count = sum(1 for item in active_items if item.item_type == "medkit")

    # Verify correct spawn counts
    assert apple_count == 3, f"Expected 3 apples, got {apple_count}"
    assert medkit_count == 1, f"Expected 1 medkit, got {medkit_count}"

    # Verify total item count
    assert len(active_items) == 4, f"Expected 4 items total (3 apples + 1 medkit), got {len(active_items)}"

    # Verify positions are within grid bounds (7x7 grid for items_smoke)
    for item in active_items:
        x, y = item.position
        assert 0 <= x < 7, f"Item x position {x} out of bounds"
        assert 0 <= y < 7, f"Item y position {y} out of bounds"


def test_periodic_item_respawning():
    """Items respawn at configured intervals after despawning."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), use_cache=False)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    # Reset spawns initial items (1 medkit with duration=100, spawn_interval=200)
    env.reset()

    # Verify initial spawn (should have 1 medkit from appearance config)
    initial_medkits = [i for i in env.item_manager.active_items.values() if i.item_type == "medkit"]
    assert len(initial_medkits) == 1, f"Expected 1 medkit at spawn, got {len(initial_medkits)}"

    # Wait for medkit to expire in the world (duration=100 ticks)
    # Item spawned at tick 0, ticks down each step, expires at tick 101
    # Then respawn_timer = despawn_tick + spawn_interval = 101 + 200 = 301
    wait_action = env.action_space.get_action_by_name("WAIT")
    for _ in range(101):  # Wait for item to expire
        env.step(torch.tensor([wait_action.id]))

    # Verify medkit despawned after duration expired
    remaining_medkits = [i for i in env.item_manager.active_items.values() if i.item_type == "medkit"]
    assert len(remaining_medkits) == 0, "Medkit should have despawned after duration expired"

    # Verify respawn timer is set correctly (should be at tick 101 + 200 = 301)
    assert "medkit" in env.item_manager.respawn_timers, "Respawn timer should be set for medkit"

    # Step until respawn_timer expires (200 more ticks to reach tick 301)
    for _ in range(200):
        env.step(torch.tensor([wait_action.id]))

    # Verify medkit respawned after spawn_interval elapsed
    respawned_medkits = [i for i in env.item_manager.active_items.values() if i.item_type == "medkit"]
    assert len(respawned_medkits) == 1, f"Expected 1 medkit to respawn after spawn_interval, got {len(respawned_medkits)}"
