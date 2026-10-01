"""Access denial preflights the complete spawn operation before allocation."""

from __future__ import annotations

import pytest
import torch

from townlet.config.items_config import ItemInteractionsConfig, ItemsCatalogConfig, ItemTypeConfig
from townlet.effects.context import ExecutionContext
from townlet.items.manager import ItemManager
from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable
from townlet.vfs.registry import VariableRegistry


def _manager() -> ItemManager:
    variables = [
        CompiledVariable(
            name=name, type="float", lifetime="episode", readable_by=("engine",), writable_by=writers, exposed_to=(), initial_value=2.0
        )
        for name, writers in [("allowed", ("engine",)), ("constant", ())]
    ]
    registry = VariableRegistry(
        [], 2, torch.device("cpu"), max_items=3, item_profiles={"object": CompiledItemProfile(profile_name="object", variables=variables)}
    )
    catalog = ItemsCatalogConfig(
        version="1.0",
        max_items_per_agent=1,
        max_items_in_world=3,
        item_types=[
            ItemTypeConfig(
                id="object",
                name="Object",
                icon="o",
                tags=["object"],
                vfs_profile="object",
                duration=None,
                cooldown=None,
                interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
            )
        ],
    )
    return ItemManager(catalog=catalog, max_items=3, device="cpu", schema=None, vfs_registry=registry)


@pytest.mark.parametrize("overrides", [{"constant": 2.0}, {"allowed": 9.0, "constant": 2.0}, {"allowed": 9.0, "missing": 2.0}])
def test_denied_spawn_overrides_leave_complete_operation_unchanged(overrides: dict[str, float]) -> None:
    manager = _manager()
    registry = manager.vfs_registry
    assert registry is not None and registry.item_vfs is not None
    before = registry.item_vfs.clone()
    slots = manager.vfs_free_slots.copy()
    with pytest.raises((PermissionError, KeyError)):
        manager.spawn_item("object", (1, 1), 0, initial_state=overrides)
    assert torch.equal(before, registry.item_vfs)
    assert manager.vfs_free_slots == slots
    assert manager.next_instance_id == 0
    assert manager.active_items == manager.held_items == {}
    assert registry.item_vfs_index_to_profile == {}
    assert manager._position_index == {}


def test_immutable_defaults_initialize_without_becoming_authored_writes() -> None:
    manager = _manager()
    item = manager.spawn_item("object", (1, 1), 0)
    assert item is not None
    registry = manager.vfs_registry
    assert registry is not None
    assert registry.read_item("object", "constant", item.vfs_index, reader="engine") == 2.0
    manager.reset_state()
    item = manager.spawn_item("object", (1, 1), 0, initial_state={"allowed": 7.0})
    assert item is not None
    assert registry.read_item("object", "constant", item.vfs_index, reader="engine") == 2.0
    assert registry.read_item("object", "allowed", item.vfs_index, reader="engine") == 7.0


def test_dynamic_path_authorization_denies_no_op_item_write() -> None:
    manager = _manager()
    item = manager.spawn_item("object", (1, 1), 0)
    assert item is not None
    ctx = ExecutionContext(vfs_registry=manager.vfs_registry, self_is_item=True, self_index=item.vfs_index)
    with pytest.raises(PermissionError, match="constant"):
        ctx.authorize_write_path("self.vfs.constant")


def test_compound_spawn_denial_precedes_sibling_mutation() -> None:
    from townlet.effects.compiler import CommandCompiler
    from townlet.effects.executor import CommandExecutor
    from townlet.effects.schema import CommandNode, CommandType

    manager = _manager()
    command = CommandCompiler({"bar.energy": "float"}).compile_command(
        CommandNode(
            type=CommandType.PARALLEL,
            parallel_commands=[
                CommandNode(type=CommandType.MODIFY, path="bar.energy", value_expr="9.0"),
                CommandNode(
                    type=CommandType.SPAWN_ITEM,
                    item_type="object",
                    position="self",
                    quantity=1,
                    initial_state={"allowed": 8.0, "constant": 2.0},
                ),
            ],
        )
    )
    ctx = ExecutionContext(
        bars={"energy": torch.full((2,), 3.0)},
        item_manager=manager,
        vfs_registry=manager.vfs_registry,
        self_index=0,
        agent_positions=torch.zeros((2, 2), dtype=torch.long),
    )
    before = ctx.bars["energy"].clone()
    with pytest.raises(PermissionError, match="constant"):
        CommandExecutor().execute(command, ctx)
    assert torch.equal(ctx.bars["energy"], before)
    assert manager.active_items == {}
