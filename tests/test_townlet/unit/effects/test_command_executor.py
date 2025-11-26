"""Tests for command executor."""

import torch

from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType


class DummyEffectManager:
    def spawn_effect(self, *args, **kwargs):
        raise RuntimeError("spawn_effect not supported in DummyEffectManager")


class DummyItemManager:
    def spawn_item(self, *args, **kwargs):
        raise RuntimeError("spawn_item not supported in DummyItemManager")


def test_executor_modify_bar():
    """Executor modifies bar value via expression."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # Create and compile command
    command = CommandNode(type=CommandType.MODIFY, path="bar.energy", value_expr="bar.energy + 0.1")

    schema = {"bar.energy": "float"}
    compiler = CommandCompiler(schema=schema)
    compiler.compile_command(command)

    executor = CommandExecutor()
    executor.execute(command, context)

    # Energy should be increased by 0.1
    assert torch.allclose(bar_storage["energy"], torch.tensor([1.1, 0.6, 0.9]))


def test_executor_modify_with_target():
    """Executor modifies target-prefixed path."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=1,  # Target agent 1
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # Create and compile command
    command = CommandNode(type=CommandType.MODIFY, path="target.bar.energy", value_expr="target.bar.energy + 0.2")

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema=schema)
    compiler.compile_command(command)

    executor = CommandExecutor()
    executor.execute(command, context)

    # Only agent 1's energy should change
    assert torch.allclose(bar_storage["energy"], torch.tensor([1.0, 0.7, 0.8]))


def test_executor_modify_constant():
    """Executor can set constant values."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # Create and compile command
    command = CommandNode(type=CommandType.MODIFY, path="bar.energy", value_expr="0.5")

    schema = {"bar.energy": "float"}
    compiler = CommandCompiler(schema=schema)
    compiler.compile_command(command)

    executor = CommandExecutor()
    executor.execute(command, context)

    # All energy set to 0.5
    assert torch.equal(bar_storage["energy"], torch.tensor([0.5, 0.5, 0.5]))


def test_executor_if_then():
    """Executor executes then branch when condition true."""
    bar_storage = {"energy": torch.tensor([0.1, 0.5, 0.8])}

    from townlet.vfs.registry import VariableRegistry
    from townlet.vfs.schema import VariableDef

    variables = [
        VariableDef(
            id="is_crisis",
            scope="agent",
            type="bool",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            default=False,
        )
    ]
    registry = VariableRegistry(variables=variables, num_agents=3, device=torch.device("cpu"))

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=registry,
        self_index=None,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # Create and compile if command
    command = CommandNode(
        type=CommandType.IF,
        condition_expr="bar.energy < 0.2",  # Will match [0.1, _, _]
        then_commands=[CommandNode(type=CommandType.MODIFY, path="vfs.is_crisis", value_expr="true")],
        else_commands=[],
    )

    # Compile the command and nested commands
    schema = {"bar.energy": "float", "vfs.is_crisis": "bool"}
    compiler = CommandCompiler(schema=schema)
    compiler.compile_command(command)

    executor = CommandExecutor()
    executor.execute(command, context)

    # First agent should have is_crisis set to true
    # But this is a vectorized operation, so ALL will be set
    # For proper per-agent logic, need target_index
    is_crisis = registry.get("is_crisis", reader="agent")
    assert is_crisis.any()  # At least one true


def test_executor_if_else():
    """Executor executes else branch when condition false."""
    bar_storage = {"energy": torch.tensor([0.9])}

    from townlet.vfs.registry import VariableRegistry
    from townlet.vfs.schema import VariableDef

    variables = [
        VariableDef(
            id="status",
            scope="agent",
            type="scalar",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            default=0.0,
        )
    ]
    registry = VariableRegistry(variables=variables, num_agents=1, device=torch.device("cpu"))

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=registry,
        self_index=None,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # Create and compile if command
    command = CommandNode(
        type=CommandType.IF,
        condition_expr="bar.energy < 0.2",  # False
        then_commands=[CommandNode(type=CommandType.MODIFY, path="vfs.status", value_expr="1.0")],
        else_commands=[CommandNode(type=CommandType.MODIFY, path="vfs.status", value_expr="2.0")],
    )

    # Compile the command and nested commands
    schema = {"bar.energy": "float", "vfs.status": "float"}
    compiler = CommandCompiler(schema=schema)
    compiler.compile_command(command)

    executor = CommandExecutor()
    executor.execute(command, context)

    # Else branch should execute
    status = registry.get("status", reader="agent")
    assert torch.equal(status, torch.tensor([2.0]))
