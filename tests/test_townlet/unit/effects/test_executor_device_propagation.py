"""Ensure effect expression evaluation honors tensor devices."""

from __future__ import annotations

import torch

from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker


def test_executor_propagates_device_for_literals():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    bars = {"energy": torch.tensor([0.5], device=device)}
    schema = {"bar.energy": "float"}

    # Build command with precompiled AST
    parser = ExpressionParser()
    ast = parser.parse("bar.energy + 0.1")
    TypeChecker(schema=schema).check(ast)

    cmd = CommandNode(
        type=CommandType.MODIFY,
        path="bar.energy",
        value_expr=None,
        value_ast=ast,
    )

    ctx = ExecutionContext(bars=bars)
    executor = CommandExecutor()
    executor.execute(cmd, ctx)

    assert torch.allclose(ctx.bars["energy"], torch.tensor([0.6], device=device))
