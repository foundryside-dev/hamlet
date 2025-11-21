"""Executor tests for switch command."""

import torch

from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType


def _make_modify(path: str, value_expr: str) -> CommandNode:
    return CommandNode(type=CommandType.MODIFY, path=path, value_expr=value_expr)


def test_switch_executes_matching_case():
    """Switch executes first matching equality case."""
    # switch 1 -> case 1 triggers, sets bar.energy to 5
    switch_node = CommandNode(
        type=CommandType.SWITCH,
        switch_expr="1",
        cases=[("1", [_make_modify("bar.energy", "5.0")])],
        default_commands=[_make_modify("bar.energy", "9.0")],
    )

    schema = {"bar.energy": "float"}
    compiler = CommandCompiler(schema)
    compiled = compiler.compile_command(switch_node)

    context = ExecutionContext(bars={"energy": torch.tensor(0.0)})
    executor = CommandExecutor()

    executor.execute(compiled, context)

    assert torch.allclose(context.bars["energy"], torch.tensor(5.0))


def test_switch_executes_default_when_no_match():
    """Switch executes default when no case matches."""
    switch_node = CommandNode(
        type=CommandType.SWITCH,
        switch_expr="3",
        cases=[("1", [_make_modify("bar.energy", "1.0")]), ("2", [_make_modify("bar.energy", "2.0")])],
        default_commands=[_make_modify("bar.energy", "7.0")],
    )

    schema = {"bar.energy": "float"}
    compiler = CommandCompiler(schema)
    compiled = compiler.compile_command(switch_node)

    context = ExecutionContext(bars={"energy": torch.tensor(0.0)})
    executor = CommandExecutor()

    executor.execute(compiled, context)

    assert torch.allclose(context.bars["energy"], torch.tensor(7.0))
