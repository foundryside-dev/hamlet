"""Integration coverage for custom item verbs (local/inventory) in action space and runtime."""

import shutil
from pathlib import Path

import torch
import yaml

from tests.test_townlet.utils.builders import make_vectorized_env_from_pack
from townlet.config.items_config import build_item_command_action_name
from townlet.universe.compiler import UniverseCompiler


def test_custom_item_verbs_flow_from_config_to_runtime(tmp_path):
    """Custom item verbs should surface in action metadata, mask correctly, and execute effects."""
    source_pack = Path("configs/test/items_smoke")
    config_pack = tmp_path / "pack"
    shutil.copytree(source_pack, config_pack)

    items_path = config_pack / "items.yaml"
    data = yaml.safe_load(items_path.read_text())
    apple = next(it for it in data["items"]["item_types"] if it["id"] == "apple")
    apple["interactions"]["local_commands"] = [
        {
            "name": "EAT_LOCAL",
            "description": "Eat an apple on the ground",
            "effects": [{"modify": "target.bar.energy", "value": "target.bar.energy - 0.05"}],
        }
    ]
    apple["interactions"]["inventory_commands"] = [
        {
            "name": "EAT_HELD",
            "description": "Eat an apple while holding it",
            "effects": [{"modify": "target.bar.energy", "value": "target.bar.energy - 0.10"}],
        }
    ]
    items_path.write_text(yaml.safe_dump(data, sort_keys=False))

    compiler = UniverseCompiler()
    universe = compiler.compile(config_pack, primary_level="L0_smoke", use_cache=False)

    local_action = build_item_command_action_name("apple", "EAT_LOCAL", "local")
    inventory_action = build_item_command_action_name("apple", "EAT_HELD", "inventory")
    action_names = {a.name for a in universe.action_space_metadata.actions}
    assert local_action in action_names
    assert inventory_action in action_names

    env = make_vectorized_env_from_pack(config_pack, level_name="L0_smoke", num_agents=1, device="cpu")
    env.reset()
    energy_idx = env.meter_name_to_index["energy"]
    occupied_positions = {
        tuple(int(coord) for coord in item.position) for item in env.item_manager.active_items.values() if item.position is not None
    }
    assert env.grid_size is not None
    spawn_position = next((x, y) for x in range(env.grid_size) for y in range(env.grid_size) if (x, y) not in occupied_positions)
    env.positions[0] = torch.tensor(spawn_position, device=env.device)

    item = env.item_manager.spawn_item("apple", position=spawn_position, current_tick=0)
    assert item is not None

    masks = env.get_action_masks()
    local_id = env.action_space.get_action_by_name(local_action).id
    assert bool(masks[0, local_id].item()) is True

    before = env.meters[0, energy_idx].item()
    env.step(torch.tensor([local_id], device=env.device))
    after = env.meters[0, energy_idx].item()
    assert after < before

    pickup = env.item_handler.handle_get_action(
        agent_idx=0,
        agent_position=torch.tensor(spawn_position, device=env.device),
        current_tick=1,
        meters=env.meters,
    )
    assert pickup is True
    masks = env.get_action_masks()
    inventory_id = env.action_space.get_action_by_name(inventory_action).id
    assert bool(masks[0, inventory_id].item()) is True

    before = env.meters[0, energy_idx].item()
    env.step(torch.tensor([inventory_id], device=env.device))
    after = env.meters[0, energy_idx].item()
    assert after < before
