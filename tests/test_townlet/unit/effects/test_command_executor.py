"""Tests for command executor."""

import torch

from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType


def test_executor_modify_bar():
    """Executor modifies bar value via expression."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=None,
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
