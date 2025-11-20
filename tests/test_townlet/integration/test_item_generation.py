"""Integration tests for effect spawning items."""

import torch

from townlet.config.effects_config import EffectScope
from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.schema import CommandNode, CommandType


class MockItemManager:
    """Mock ItemManager for integration testing."""

    def __init__(self):
        self.spawned_items = []
        self.current_step = 0

    def spawn_item(self, item_id, position_hint, initial_state=None):
        """Mock spawn_item that records calls."""
        from townlet.items.instance import ItemInstance

        instance = ItemInstance(
            item_type=item_id,
            instance_id=len(self.spawned_items),
            position=(0, 0),  # Dummy position
            vfs_index=0,
            spawn_tick=self.current_step,
            duration_total=None,
            duration_remaining=None,
        )
        self.spawned_items.append(
            {
                "item_id": item_id,
                "position_hint": position_hint,
                "initial_state": initial_state,
                "instance": instance,
            }
        )
        return instance

    def get_active_items(self):
        """Return spawned items."""
        return [item["instance"] for item in self.spawned_items]


def test_effect_spawns_item_on_completion():
    """Test effect spawning item on completion (loot drop pattern)."""
    executor = CommandExecutor()

    # Create effect catalog with loot_drop effect
    catalog = EffectCatalog(
        effects={
            "loot_drop": CompiledEffect(
                id="loot_drop",
                scope="agent",
                duration=1,
                intensity=1.0,
                reapply_policy="stack",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[
                    CommandNode(
                        type=CommandType.SPAWN_ITEM,
                        item_id="gold_coin",
                        position="self",
                        quantity=1,
                    )
                ],
                on_interrupt=[],
            ),
        }
    )

    item_manager = MockItemManager()
    manager = EffectManager(catalog=catalog, device="cpu", command_executor=executor)

    # Spawn loot_drop effect with duration=1 (despawns next tick)
    bars = {"health": torch.tensor([1.0])}
    manager.spawn_effect(
        effect_id="loot_drop",
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=1,
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=None,
    )

    # Verify no items yet
    assert len(item_manager.get_active_items()) == 0

    # Tick manager (should despawn effect, triggering on_despawn command)
    manager.tick(bars=bars, vfs_registry=None, current_step=1, item_manager=item_manager)

    # Verify gold_coin spawned
    items = item_manager.get_active_items()
    assert len(items) == 1
    assert items[0].item_type == "gold_coin"
