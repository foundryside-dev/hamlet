"""End-to-end integration test for spawn_item with real ItemManager."""

import torch

from townlet.config.effects_config import EffectScope
from townlet.config.items_config import (
    ItemInteractionsConfig,
    ItemsCatalogConfig,
    ItemTypeConfig,
)
from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.schema import CommandNode, CommandType
from townlet.items.manager import ItemManager
from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable
from townlet.vfs.registry import VariableRegistry


class DummyEffectManager:
    def spawn_effect(self, *args, **kwargs):
        raise RuntimeError("spawn_effect not supported in DummyEffectManager")


def test_effect_on_despawn_spawns_item_with_real_itemmanager():
    """Effect on_despawn should spawn item using real ItemManager."""
    # Create VFS registry with compiled item profiles (no legacy item variables)
    item_profiles = {
        "currency": CompiledItemProfile(profile_name="currency", variables=[]),
        "treasure": CompiledItemProfile(
            profile_name="treasure",
            variables=[
                CompiledVariable(
                    name="durability",
                    type="float",
                    expression=None,
                    ast=None,
                    initial_value=100.0,
                    result_type="float",
                ),
                CompiledVariable(
                    name="quality",
                    type="float",
                    expression=None,
                    ast=None,
                    initial_value=1.0,
                    result_type="float",
                ),
            ],
        ),
    }

    vfs_registry = VariableRegistry(
        variables=[],
        num_agents=3,
        max_items=10,
        device=torch.device("cpu"),
        item_profiles=item_profiles,
    )

    # Create ItemManager with loot catalog
    items_catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="gold_coin",
                vfs_profile="currency",
                duration=None,
                cooldown=None,
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            ),
            ItemTypeConfig(
                id="rare_gem",
                vfs_profile="treasure",
                duration=200,
                cooldown=50,
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            ),
        ]
    )

    item_manager = ItemManager(
        catalog=items_catalog,
        max_items=10,
        device="cpu",
        schema=None,
        vfs_registry=vfs_registry,
    )

    # Create effect that spawns loot on despawn (using explicit position to avoid agent_positions requirement)
    compiled_effect = CompiledEffect(
        id="loot_drop_effect",
        scope="agent",
        duration=5,
        intensity=1.0,
        reapply_policy="stack",
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[
            CommandNode(
                type=CommandType.SPAWN_ITEM,
                item_type="gold_coin",
                position=[5, 7],  # Explicit position instead of "self"
                quantity=3,
                initial_state=None,
            ),
            CommandNode(
                type=CommandType.SPAWN_ITEM,
                item_type="rare_gem",
                position=[5, 7],  # Explicit position instead of "self"
                quantity=1,
                initial_state={"durability": 80.0, "quality": 0.9},
            ),
        ],
        on_interrupt=[],
    )

    # Create EffectCatalog and EffectManager
    catalog = EffectCatalog(effects={"loot_drop_effect": compiled_effect})

    executor = CommandExecutor()

    effect_manager = EffectManager(
        catalog=catalog,
        device="cpu",
        command_executor=executor,
    )

    # Spawn effect on agent 1
    bars = {
        "energy": torch.tensor([1.0, 1.0, 1.0]),
        "health": torch.tensor([1.0, 1.0, 1.0]),
    }

    effect_manager.spawn_effect(
        effect_id="loot_drop_effect",
        target_entity_id=1,
        scope=EffectScope.AGENT,
        duration=1,  # Very short duration - will expire after 1 tick
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=vfs_registry,
    )

    # Verify effect is active
    assert len(effect_manager.agent_effects[1]) == 1

    # Tick once to expire effect (should trigger on_despawn and spawn loot)
    effect_manager.tick(
        bars=bars,
        vfs_registry=vfs_registry,
        current_step=1,
        item_manager=item_manager,
    )

    # Effect should be gone now
    assert 1 not in effect_manager.agent_effects or len(effect_manager.agent_effects[1]) == 0

    # Verify loot spawned at agent 1 position
    items = item_manager.get_all_items()
    assert len(items) == 4  # 3 gold coins + 1 rare gem

    # All items at agent 1 position (5, 7)
    for item in items:
        assert item.position == (5, 7)

    # Check item types
    gold_coins = [i for i in items if i.item_type == "gold_coin"]
    rare_gems = [i for i in items if i.item_type == "rare_gem"]

    assert len(gold_coins) == 3
    assert len(rare_gems) == 1

    # Verify rare gem has custom initial_state
    gem = rare_gems[0]
    durability = vfs_registry.read_item(gem.vfs_profile, "durability", gem.vfs_index)
    quality = vfs_registry.read_item(gem.vfs_profile, "quality", gem.vfs_index)

    assert abs(durability - 80.0) < 0.01
    assert abs(quality - 0.9) < 0.01


def test_spawn_item_respects_itemmanager_capacity():
    """spawn_item should respect ItemManager max_items capacity."""
    catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="trash",
                vfs_profile="junk",
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

    # Very small capacity
    item_manager = ItemManager(
        catalog=catalog,
        max_items=2,  # Only 2 items max
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
        effect_manager=DummyEffectManager(),
        agent_positions=torch.tensor([[3.0, 3.0]]),
        current_tick=0,
    )

    from townlet.effects.schema import CommandNode, CommandType

    # Spawn 5 items (should only spawn 2 due to capacity)
    command = CommandNode(
        type=CommandType.SPAWN_ITEM,
        item_type="trash",
        position="self",
        quantity=5,
        initial_state=None,
    )

    executor = CommandExecutor()
    executor.execute(command, context)

    # Only 2 items spawned
    items = item_manager.get_all_items()
    assert len(items) == 2


def test_spawn_item_respects_cooldown():
    """spawn_item should respect ItemManager cooldown."""
    catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="rare_item",
                vfs_profile="rare",
                duration=None,
                cooldown=10,  # 10 tick cooldown
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

    # Spawn first item at tick 0
    item1 = item_manager.spawn_item("rare_item", (3, 3), current_tick=0)
    assert item1 is not None

    # Despawn to trigger cooldown
    item_manager.despawn_item(item1.instance_id, current_tick=0)

    # Try to spawn again at tick 5 (should fail - cooldown not expired)
    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0])},
        vfs_registry=None,
        self_index=0,
        target_index=None,
        item_manager=item_manager,
        effect_manager=DummyEffectManager(),
        agent_positions=torch.tensor([[3.0, 3.0]]),
        current_tick=5,  # Still on cooldown
    )

    from townlet.effects.schema import CommandNode, CommandType

    command = CommandNode(
        type=CommandType.SPAWN_ITEM,
        item_type="rare_item",
        position="self",
        quantity=1,
        initial_state=None,
    )

    executor = CommandExecutor()
    executor.execute(command, context)

    # No new items (cooldown blocked spawn)
    items = item_manager.get_all_items()
    assert len(items) == 0

    # Try again at tick 11 (cooldown expired)
    context.current_tick = 11
    executor.execute(command, context)

    # Now item spawned
    items = item_manager.get_all_items()
    assert len(items) == 1
