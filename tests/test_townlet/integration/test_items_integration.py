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


def test_item_actions_defined_in_global_actions():
    """default_curriculum/actions.yaml has GET/USE_SLOT/DROP_SLOT actions."""
    import yaml

    config_path = Path("configs/default_curriculum/actions.yaml")
    with open(config_path) as f:
        data = yaml.safe_load(f)

    action_names = [a["name"] for a in data["actions"]["custom_actions"]]

    # Item actions
    assert "GET" in action_names, "GET action missing"
    assert "USE_SLOT_0" in action_names, "USE_SLOT_0 action missing"
    assert "USE_SLOT_1" in action_names, "USE_SLOT_1 action missing"
    assert "USE_SLOT_2" in action_names, "USE_SLOT_2 action missing"
    assert "DROP_SLOT_0" in action_names, "DROP_SLOT_0 action missing"
    assert "DROP_SLOT_1" in action_names, "DROP_SLOT_1 action missing"
    assert "DROP_SLOT_2" in action_names, "DROP_SLOT_2 action missing"


def test_env_with_items_initializes():
    """Environment with ItemManager and InventoryState initializes correctly."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"))

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
