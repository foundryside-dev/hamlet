"""An immediate descendant refusal cannot commit its parent's earlier work."""

import pytest
import torch

from townlet.config.items_config import ItemInteractionsConfig, ItemsCatalogConfig, ItemTypeConfig
from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.compiler import CommandCompiler
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.schema import CommandNode, CommandType
from townlet.items.instance import ItemInstance
from townlet.items.manager import ItemManager
from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef


def _services() -> tuple[EffectManager, VariableRegistry, ItemManager, ItemInstance, dict[str, torch.Tensor], CommandCompiler]:
    profiles = {
        name: CompiledItemProfile(
            profile_name=name,
            variables=[
                CompiledVariable(
                    name="charge",
                    type="float",
                    exposed_to=(),
                    lifetime="episode",
                    readable_by=("engine",),
                    writable_by=writers,
                    initial_value=2.0,
                )
            ],
        )
        for name, writers in [("writable", ("engine",)), ("sealed", ())]
    }
    registry = VariableRegistry(
        [
            VariableDef(
                id=name,
                scope=scope,
                type="scalar",
                lifetime="episode",
                default=2.0,
                readable_by=["engine"],
                writable_by=["engine"],
            )
            for name, scope in [("global_state", "global"), ("agent_state", "agent"), ("private_state", "agent_private")]
        ],
        num_agents=2,
        device=torch.device("cpu"),
        max_items=3,
        item_profiles=profiles,
    )
    compiler = CommandCompiler(
        {
            "bar.energy": "float",
            "self.vfs.charge": "float",
            "vfs.global_state": "float",
            "self.vfs.agent_state": "float",
            "vfs.private_state": "float",
            "affordance.bank.available": "bool",
        }
    )
    effects = {
        "parent": CompiledEffect(
            id="parent",
            scope="agent",
            duration=5,
            reapply_policy="stack",
            observable=True,
            on_spawn=[],
            on_tick=compiler.compile_commands([CommandNode(type=CommandType.MODIFY, path="bar.energy", value_expr="bar.energy + 1.0")]),
            on_despawn=[],
            on_interrupt=[],
        ),
        "child": CompiledEffect(
            id="child",
            scope="item",
            duration=5,
            reapply_policy="stack",
            observable=True,
            on_spawn=compiler.compile_commands([CommandNode(type=CommandType.MODIFY, path="self.vfs.charge", value_expr="4.0")]),
            on_tick=[],
            on_despawn=[],
            on_interrupt=[],
        ),
    }
    manager = EffectManager(
        catalog=EffectCatalog(effects=effects, max_active_effects={"global": 0, "agent": 2, "item": 2, "affordance": 0}),
        command_executor=CommandExecutor(),
        affordance_overrides={"bank": True},
    )
    catalog = ItemsCatalogConfig(
        version="1.0",
        item_types=[
            ItemTypeConfig(
                id=name,
                name=name,
                icon="x",
                tags=["tool"],
                vfs_profile=name,
                duration=None,
                cooldown=None,
                interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
            )
            for name in profiles
        ],
        max_items_per_agent=3,
        max_items_in_world=3,
    )
    items = ItemManager(catalog=catalog, max_items=3, device="cpu", schema=None, vfs_registry=registry, effect_manager=manager)
    sealed = items.spawn_item("sealed", (0, 0), 0)
    assert sealed is not None
    return manager, registry, items, sealed, {"energy": torch.full((2,), 3.0)}, compiler


def test_fresh_parent_denial_releases_items_positions_and_profile_rows() -> None:
    manager, registry, items, sealed, bars, compiler = _services()
    manager.catalog.effects["parent"].on_spawn = compiler.compile_commands(
        [
            CommandNode(type=CommandType.SPAWN_ITEM, item_type="writable", position="self", quantity=1, initial_state={"charge": 7.0}),
            CommandNode(type=CommandType.SPAWN_EFFECT, effect_id="child", target=sealed.vfs_index, intensity=1.0),
        ]
    )
    assert registry.item_vfs is not None
    arena = registry.item_vfs
    before_arena = arena.clone()
    before_profiles = registry.item_vfs_index_to_profile.copy()
    with pytest.raises(PermissionError, match="sealed"):
        manager.spawn_effect(
            "parent",
            0,
            1.0,
            0,
            bars=bars,
            vfs_registry=registry,
            item_manager=items,
            agent_positions=torch.tensor([[4, 5], [6, 7]]),
        )
    assert items.get_all_items() == [sealed]
    assert items.get_all_items()[0] is sealed
    assert not items._position_occupied((4, 5))
    assert registry.item_vfs is arena
    assert torch.equal(arena, before_arena)
    assert registry.item_vfs_index_to_profile == before_profiles
    assert manager.get_all_active_effects() == []
    manager.tick(bars, registry, current_step=1, item_manager=items)
    assert torch.equal(bars["energy"], torch.full((2,), 3.0))
    # A failed cascade must leave both free rows and the next public item ID
    # available. No hidden item can consume capacity or retain its profile.
    first = items.spawn_item("writable", (4, 5), 1, initial_state={"charge": 6.0})
    second = items.spawn_item("writable", (6, 7), 1)
    assert first is not None and second is not None
    assert (first.instance_id, second.instance_id) == (1, 2)
    assert first.vfs_index != second.vfs_index
    assert registry.read_item("writable", "charge", first.vfs_index, reader="engine") == 6.0
    assert registry.read_item("sealed", "charge", sealed.vfs_index, reader="engine") == 2.0


def test_descendant_denial_restores_published_arenas_private_aliases_and_affordance() -> None:
    manager, registry, items, sealed, bars, compiler = _services()
    # Hold the views used by runtime publishers, and the original private tensor
    # which ordinary registry writes replace. The rollback must repair both.
    original = {name: tensor for name, tensor in registry._storage.items()}
    published_global = registry._scope_arenas["global"].tensor
    published_agents = registry._scope_arenas["agent"].tensor
    global_values = published_global.clone()
    agent_values = published_agents.clone()
    availability = manager.affordance_overrides
    assert availability is not None
    manager.catalog.effects["parent"].on_spawn = compiler.compile_commands(
        [
            CommandNode(type=CommandType.MODIFY, path="vfs.global_state", value_expr="9.0"),
            CommandNode(type=CommandType.MODIFY, path="self.vfs.agent_state", value_expr="8.0"),
            CommandNode(type=CommandType.MODIFY, path="vfs.private_state", value_expr="7.0"),
            CommandNode(type=CommandType.MODIFY, path="affordance.bank.available", value_expr="false"),
            CommandNode(type=CommandType.SPAWN_EFFECT, effect_id="child", target=sealed.vfs_index, intensity=1.0),
        ]
    )
    with pytest.raises(PermissionError, match="sealed"):
        manager.spawn_effect("parent", 0, 1.0, 0, bars=bars, vfs_registry=registry, item_manager=items)
    for name, tensor in original.items():
        assert registry._storage[name] is tensor
        assert torch.equal(tensor, torch.full_like(tensor, 2.0))
        assert torch.equal(registry.get(name, reader="engine"), tensor)
    assert registry._scope_arenas["global"].tensor is published_global
    assert registry._scope_arenas["agent"].tensor is published_agents
    assert torch.equal(published_global, global_values)
    assert torch.equal(published_agents, agent_values)
    assert manager.affordance_overrides is availability
    assert availability == {"bank": True}
    assert manager.get_all_active_effects() == []
