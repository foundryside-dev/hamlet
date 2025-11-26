"""Tests for custom item verbs (local and inventory) masking and dispatch."""

import torch

from townlet.config.items_config import (
    ItemCustomCommand,
    ItemInteractionsConfig,
    ItemsCatalogConfig,
    ItemTypeConfig,
    build_item_command_action_name,
)
from townlet.items.action_handlers import ItemActionHandler
from townlet.items.inventory import InventoryState
from townlet.items.manager import ItemManager


class _Action:
    def __init__(self, name: str, id: int) -> None:
        self.name = name
        self.id = id


class _ActionSpaceStub:
    def __init__(self, names: list[str]) -> None:
        self.actions = [_Action(name, idx) for idx, name in enumerate(names)]
        self.lookup = {a.name: a for a in self.actions}

    def get_action_by_name(self, name: str) -> _Action:
        if name not in self.lookup:
            raise ValueError(f"Action '{name}' not found")
        return self.lookup[name]


class _CommandExecutorStub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def execute(self, command, context) -> None:
        # Record (command, target_index) for assertion
        self.calls.append((command, context.target_index))


class _VFSRegistryStub:
    """Minimal stub; custom verbs here don't touch VFS."""

    item_profile_map = {}


def _catalog_with_custom() -> ItemsCatalogConfig:
    local_cmd = ItemCustomCommand(
        name="OPEN",
        description="Open locally",
        effects=[{"modify": "target.bar.energy", "value": "1.0"}],
    )
    inventory_cmd = ItemCustomCommand(
        name="USE",
        description="Use from inventory",
        effects=[{"modify": "target.bar.energy", "value": "2.0"}],
    )
    return ItemsCatalogConfig(
        version="1.0",
        item_types=[
            ItemTypeConfig(
                id="tool",
                name="Tool",
                icon="🧰",
                tags=["tool"],
                vfs_profile="tool_vfs",
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                    local_commands=[local_cmd],
                    inventory_commands=[inventory_cmd],
                ),
            )
        ],
        max_items_per_agent=2,
        max_items_in_world=4,
    )


def test_custom_item_verbs_masking_and_dispatch():
    catalog = _catalog_with_custom()
    manager = ItemManager(catalog=catalog, max_items=4, device="cpu", schema=None)
    inventory = InventoryState(batch_size=2, max_items_per_agent=2, device="cpu")
    executor = _CommandExecutorStub()
    vfs_registry = _VFSRegistryStub()

    handler = ItemActionHandler(
        manager=manager,
        inventory=inventory,
        command_executor=executor,
        vfs_registry=vfs_registry,
        meter_name_to_index={"energy": 0},
    )

    local_action = build_item_command_action_name("tool", "OPEN", "local")
    inventory_action = build_item_command_action_name("tool", "USE", "inventory")
    action_space = _ActionSpaceStub([local_action, inventory_action])

    # Start with all actions allowed; expect masking to disable without availability
    action_masks = torch.ones((2, 2), dtype=torch.bool)
    handler.compute_custom_action_masks(action_space, action_masks, agent_positions=torch.tensor([[0, 0], [5, 5]]))
    assert not action_masks[0, 0]
    assert not action_masks[0, 1]

    # Add local item at agent 0 position and recompute
    item = manager.spawn_item("tool", position=(0, 0), current_tick=0)
    assert item is not None
    action_masks[:] = True
    handler.compute_custom_action_masks(action_space, action_masks, agent_positions=torch.tensor([[0, 0], [5, 5]]))
    assert action_masks[0, 0]  # agent 0 sees local verb
    assert not action_masks[1, 0]  # agent 1 still masked

    # Dispatch local command executes compiled commands (injected)
    compiled = manager.compiled_item_types[0]
    compiled.compiled_local_commands["OPEN"] = ["LOCAL_CMD"]
    handler.handle_custom_action(
        action_name=local_action,
        agent_idx=0,
        agent_position=torch.tensor([0, 0]),
        current_tick=0,
        meters=torch.zeros((2, 1)),
    )
    assert ("LOCAL_CMD", 0) in executor.calls

    # Inventory verb: put item in agent 1 inventory and mask/unmask
    inventory.add_item(agent_idx=1, item=item)
    action_masks[:] = True
    handler.compute_custom_action_masks(action_space, action_masks, agent_positions=torch.tensor([[1, 1], [2, 2]]))
    assert action_masks[1, 1]

    compiled.compiled_inventory_commands["USE"] = ["INV_CMD"]
    handler.handle_custom_action(
        action_name=inventory_action,
        agent_idx=1,
        agent_position=torch.tensor([2, 2]),
        current_tick=0,
        meters=torch.zeros((2, 1)),
    )
    assert ("INV_CMD", 1) in executor.calls
