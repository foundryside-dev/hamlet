"""Test spawn_item position resolution with real ItemManager."""

import torch

from townlet.config.items_config import (
    ItemInteractionsConfig,
    ItemsCatalogConfig,
    ItemTypeConfig,
)
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.items.manager import ItemManager
from townlet.vfs.registry import VariableRegistry


def test_spawn_item_resolves_self_position():
    """spawn_item with position='self' should use self agent position."""
    # Create ItemManager with minimal catalog
    catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="health_potion",
                vfs_profile="consumable",
                duration=None,
                cooldown=None,
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            )
        ]
    )

    item_manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=None,
        vfs_registry=None,
    )

    # Create agent positions tensor [batch=3, dims=2]
    agent_positions = torch.tensor(
        [
            [1.0, 2.0],  # Agent 0 at (1, 2)
            [5.0, 7.0],  # Agent 1 at (5, 7)
            [3.0, 4.0],  # Agent 2 at (3, 4)
        ]
    )

    # Create ExecutionContext with self_index=1
    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0, 1.0, 1.0])},
        vfs_registry=None,
        self_index=1,  # Agent 1
        target_index=None,
        item_manager=item_manager,
        agent_positions=agent_positions,
        current_tick=0,
    )

    # Create spawn_item command with position="self"
    command = CommandNode(
        type=CommandType.SPAWN_ITEM,
        item_id="health_potion",
        position="self",
        quantity=1,
        initial_state=None,
    )

    executor = CommandExecutor()
    executor.execute(command, context)

    # Verify item spawned at agent 1's position
    items = item_manager.get_all_items()
    assert len(items) == 1
    assert items[0].position == (5, 7)  # Agent 1's position (rounded)


def test_spawn_item_resolves_target_position():
    """spawn_item with position='target' should use target agent position."""
    catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="loot_drop",
                vfs_profile="loot",
                duration=100,
                cooldown=None,
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            )
        ]
    )

    item_manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=None,
        vfs_registry=None,
    )

    agent_positions = torch.tensor(
        [
            [1.0, 2.0],
            [5.0, 7.0],
            [3.0, 4.0],
        ]
    )

    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0, 1.0, 1.0])},
        vfs_registry=None,
        self_index=0,
        target_index=2,  # Target agent 2
        item_manager=item_manager,
        agent_positions=agent_positions,
        current_tick=0,
    )

    command = CommandNode(
        type=CommandType.SPAWN_ITEM,
        item_id="loot_drop",
        position="target",
        quantity=1,
        initial_state=None,
    )

    executor = CommandExecutor()
    executor.execute(command, context)

    items = item_manager.get_all_items()
    assert len(items) == 1
    assert items[0].position == (3, 4)  # Target agent position


def test_spawn_item_with_explicit_position():
    """spawn_item with explicit coordinates should use those coords."""
    catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="treasure",
                vfs_profile="rare",
                duration=None,
                cooldown=None,
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            )
        ]
    )

    item_manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=None,
        vfs_registry=None,
    )

    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0])},
        vfs_registry=None,
        self_index=0,
        target_index=None,
        item_manager=item_manager,
        agent_positions=torch.tensor([[1.0, 2.0]]),
        current_tick=0,
    )

    # Explicit coordinates
    command = CommandNode(
        type=CommandType.SPAWN_ITEM,
        item_id="treasure",
        position=[10, 15],  # Explicit (x, y)
        quantity=1,
        initial_state=None,
    )

    executor = CommandExecutor()
    executor.execute(command, context)

    items = item_manager.get_all_items()
    assert len(items) == 1
    assert items[0].position == (10, 15)


def test_spawn_item_with_initial_state():
    """spawn_item should pass initial_state to ItemManager."""
    from townlet.vfs.schema import VariableDef, VariableScope

    # Create VFS registry
    variables = [
        VariableDef(
            id="durability",
            type="scalar",
            scope=VariableScope.ITEM,
            lifetime="episode",
            readable_by=["agent"],
            writable_by=["actions"],
            default=100.0,
        ),
    ]

    vfs_registry = VariableRegistry(
        variables=variables,
        num_agents=1,
        max_items=10,
        device="cpu",
    )

    catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="damaged_sword",
                vfs_profile="weapon",
                duration=None,
                cooldown=None,
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            )
        ]
    )

    item_manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=None,
        vfs_registry=vfs_registry,
    )

    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0])},
        vfs_registry=vfs_registry,
        self_index=0,
        target_index=None,
        item_manager=item_manager,
        agent_positions=torch.tensor([[5.0, 5.0]]),
        current_tick=0,
    )

    command = CommandNode(
        type=CommandType.SPAWN_ITEM,
        item_id="damaged_sword",
        position="self",
        quantity=1,
        initial_state={"durability": 25.0},  # Damaged item
    )

    executor = CommandExecutor()
    executor.execute(command, context)

    items = item_manager.get_all_items()
    assert len(items) == 1

    # Verify custom initial_state applied
    durability = vfs_registry.read("durability", context_index=items[0].vfs_index, scope=VariableScope.ITEM)
    assert durability == 25.0
