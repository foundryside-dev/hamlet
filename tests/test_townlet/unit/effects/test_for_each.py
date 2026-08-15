"""Tests for for_each command."""

import pytest
import torch

from townlet.effects.collections import MAX_COLLECTION_SIZE
from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression import ExpressionParser


class DummyEffectManager:
    def spawn_effect(self, *args, **kwargs):
        raise RuntimeError("spawn_effect not supported in DummyEffectManager")


class DummyItemManager:
    def spawn_item(self, *args, **kwargs):
        raise RuntimeError("spawn_item not supported in DummyItemManager")


class DummyInventory:
    """Minimal inventory stub with slots tensor."""

    def __init__(self, slots: torch.Tensor):
        self.slots = slots
        self.items = {}


def test_for_each_nearby_agents_with_modify():
    """Test for_each iterates over nearby agents and modifies bars."""
    executor = CommandExecutor()

    # Create for_each command: heal all agents within radius 3.0
    command = CommandNode(
        type=CommandType.FOR_EACH,
        collection="nearby_agents",
        radius=3.0,
        iterator="ally",
        body=[
            CommandNode(
                type=CommandType.MODIFY,
                path="target.bar.health",
                value_expr="target.bar.health + 0.2",
            )
        ],
    )

    # Compile nested modify command
    schema = {"target.bar.health": "float"}
    compiler = CommandCompiler(schema=schema)
    for body_cmd in command.body:
        compiler.compile_command(body_cmd)

    # Create context with 3 agents (self at index 0, others at 1, 2)
    bars = {
        "health": torch.tensor([0.5, 0.6, 0.7]),  # All agents need healing
    }

    # Mock agent positions (needed for radius check)
    # Agent 0 at (0, 0), Agent 1 at (2, 0), Agent 2 at (10, 0)
    # Only Agent 1 is within radius 3.0
    agent_positions = torch.tensor([[0.0, 0.0], [2.0, 0.0], [10.0, 0.0]])

    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
        agent_positions=agent_positions,  # NEW field needed
    )

    # Execute for_each
    executor.execute(command, context)

    # Verify only agent 1 was healed (within radius)
    assert bars["health"][0].item() == pytest.approx(0.5)  # Self unchanged
    assert bars["health"][1].item() == pytest.approx(0.8)  # Agent 1 healed (+0.2)
    assert bars["health"][2].item() == pytest.approx(0.7)  # Agent 2 unchanged (too far)


def test_for_each_all_agents():
    """Test for_each with all_agents collection."""
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.FOR_EACH,
        collection="all_agents",
        iterator="agent",
        body=[
            CommandNode(
                type=CommandType.MODIFY,
                path="target.bar.energy",
                value_expr="target.bar.energy + 0.1",
            )
        ],
    )

    # Compile nested modify command
    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema=schema)
    for body_cmd in command.body:
        compiler.compile_command(body_cmd)

    bars = {"energy": torch.tensor([0.2, 0.3, 0.4])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    executor.execute(command, context)

    # All agents should be boosted (+0.1 energy)
    assert bars["energy"][0].item() == pytest.approx(0.3)
    assert bars["energy"][1].item() == pytest.approx(0.4)
    assert bars["energy"][2].item() == pytest.approx(0.5)


def test_for_each_unknown_collection_raises():
    """Unknown collection should raise immediately."""
    executor = CommandExecutor()
    command = CommandNode(
        type=CommandType.FOR_EACH,
        collection="not_a_collection",
        iterator="x",
        body=[],
    )
    bars = {"energy": torch.tensor([0.2])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )
    with pytest.raises(ValueError):
        executor.execute(command, context)


def test_for_each_collection_expression_executes():
    """Expression-based collection should be evaluated at runtime."""
    executor = CommandExecutor()
    parser = ExpressionParser()
    coll_ast = parser.parse("0")
    command = CommandNode(
        type=CommandType.FOR_EACH,
        collection=None,
        collection_expr="0",
        collection_ast=coll_ast,
        iterator="idx",
        body=[
            CommandNode(
                type=CommandType.MODIFY,
                path="target.bar.energy",
                value_expr="target.bar.energy + 1",
            )
        ],
    )

    # Compile nested modify command
    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema=schema)
    for body_cmd in command.body:
        compiler.compile_command(body_cmd)

    bars = {"energy": torch.tensor([0.0, 5.0])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    executor.execute(command, context)

    assert torch.allclose(bars["energy"], torch.tensor([1.0, 5.0]))


def test_for_each_empty_collection_noop():
    """Test for_each with empty collection is no-op."""
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.FOR_EACH,
        collection="nearby_agents",
        radius=1.0,  # Very small radius - no one nearby
        iterator="ally",
        body=[
            CommandNode(
                type=CommandType.MODIFY,
                path="target.bar.health",
                value_expr="0.0",  # Would zero health
            )
        ],
    )

    # Compile nested modify command (with literal value this time)
    schema = {"target.bar.health": "float"}
    compiler = CommandCompiler(schema=schema)
    for body_cmd in command.body:
        compiler.compile_command(body_cmd)

    bars = {"health": torch.tensor([0.5, 0.6])}
    agent_positions = torch.tensor([[0.0, 0.0], [10.0, 10.0]])  # Far apart

    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
        agent_positions=agent_positions,
    )

    executor.execute(command, context)

    # Health unchanged (no nearby agents)
    assert bars["health"][0].item() == pytest.approx(0.5)
    assert bars["health"][1].item() == pytest.approx(0.6)


def test_for_each_iteration_cap_raises():
    """for_each enforces collection size cap to prevent runaway iteration."""
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.FOR_EACH,
        collection="all_agents",
        iterator="agent",
        body=[],
    )

    bars = {"energy": torch.zeros(MAX_COLLECTION_SIZE + 1)}  # exceed collection cap
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    with pytest.raises(RuntimeError):
        executor.execute(command, context)


def test_for_each_inventory_items_skips_empty_and_uses_ints():
    """inventory_items should skip empty slots and provide int instance ids."""
    executor = CommandExecutor()
    command = CommandNode(
        type=CommandType.FOR_EACH,
        collection="inventory_items",
        iterator="item",
        body=[
            CommandNode(
                type=CommandType.MODIFY,
                path="target.vfs.durability",
                value_expr="target.vfs.durability + 1.0",
            )
        ],
    )

    schema = {"target.vfs.durability": "float"}
    compiler = CommandCompiler(schema=schema)
    for body_cmd in command.body:
        compiler.compile_command(body_cmd)

    bars = {"health": torch.tensor([0.5, 0.5, 0.5])}
    # Inventory slots: agent 0 has items 2 and -1 (empty)
    inventory = DummyInventory(slots=torch.tensor([[2, -1], [-1, -1]], dtype=torch.long))

    # Minimal item metadata mapping instance_id -> ItemInstance-like with vfs_index
    class DummyItem:
        def __init__(self, vfs_index):
            self.vfs_index = vfs_index

    inventory.items[2] = DummyItem(vfs_index=2)

    # Mock VFS registry for item durability values indexed by item_id
    class DummyVFS:
        def __init__(self):
            self.values = {"durability": torch.tensor([5.0, 6.0, 7.0])}
            self.variables = {"durability": object()}

        def read_item(self, profile_name, name, vfs_index):
            return self.values[name][vfs_index]

        def write_item(self, profile_name, name, value, vfs_index):
            self.values[name][vfs_index] = value

        def get(self, name, reader=None):
            return self.values[name]

        def get_item_profile_for_index(self, vfs_index):
            return "default"

        def get_item_variable_type(self, profile_name, name):
            return "float"

    vfs = DummyVFS()

    context = ExecutionContext(
        bars=bars,
        vfs_registry=vfs,
        self_index=0,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )
    context.inventory = inventory

    executor.execute(command, context)

    # Only item id 2 should be touched (durability +1)
    assert vfs.values["durability"][2].item() == pytest.approx(8.0)
    assert vfs.values["durability"][0].item() == pytest.approx(5.0)
    assert vfs.values["durability"][1].item() == pytest.approx(6.0)
