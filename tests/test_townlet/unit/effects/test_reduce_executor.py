"""Executor tests for reduce command (fixed-size)."""

import pytest
import torch

from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.type_checker import TypeCheckError


def test_reduce_sum_static_list():
    """Reduce over static list computes sum into target."""
    node = CommandNode(
        type=CommandType.REDUCE,
        reduce_expr="bar.col",
        reduce_iterator="i",
        reduce_init_expr="0",
        reduce_body_expr="acc + i",
        reduce_target="bar.energy",
    )

    schema = {"bar.energy": "int", "bar.col": "tensor"}
    compiler = CommandCompiler(schema)
    compiled = compiler.compile_command(node)

    context = ExecutionContext(bars={"energy": torch.tensor(0), "col": torch.tensor([1, 2, 3])})
    executor = CommandExecutor()

    executor.execute(compiled, context)

    assert torch.equal(context.bars["energy"], torch.tensor(6))


def test_reduce_rejects_collection_type():
    """Reduce rejects non-list/tensor collections."""
    node = CommandNode(
        type=CommandType.REDUCE,
        reduce_expr="true",
        reduce_iterator="i",
        reduce_init_expr="0",
        reduce_body_expr="acc + i",
        reduce_target="bar.energy",
    )

    schema = {"bar.energy": "int"}
    compiler = CommandCompiler(schema)

    with pytest.raises(TypeCheckError, match="collection must be fixed-size"):
        compiler.compile_command(node)


def test_reduce_type_mismatch_body():
    """Reduce body must return accumulator type."""
    node = CommandNode(
        type=CommandType.REDUCE,
        reduce_expr="bar.col",
        reduce_iterator="i",
        reduce_init_expr="0",
        reduce_body_expr="'bad'",
        reduce_target="bar.energy",
    )

    schema = {"bar.energy": "int", "bar.col": "tensor"}
    compiler = CommandCompiler(schema)

    with pytest.raises(TypeCheckError, match="body must return accumulator"):
        compiler.compile_command(node)
