"""Tests for parallel command validation."""

import pytest

from tests.test_townlet._fixtures.command_namespace import command_compiler
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.type_checker import TypeCheckError


def _modify(path: str, value_expr: str) -> CommandNode:
    return CommandNode(type=CommandType.MODIFY, path=path, value_expr=value_expr)


def test_parallel_allows_disjoint_writes():
    """Parallel compiles when branches write different targets."""
    branch1 = _modify("bar.a", "1.0")
    branch2 = _modify("bar.b", "2.0")
    node = CommandNode(type=CommandType.PARALLEL, parallel_commands=[branch1, branch2])

    schema = {"bar.a": "float", "bar.b": "float"}
    compiler = command_compiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.parallel_commands is not None


def test_parallel_rejects_conflicting_writes():
    """Parallel rejects branches writing the same target."""
    branch1 = _modify("bar.a", "1.0")
    branch2 = _modify("bar.a", "2.0")
    node = CommandNode(type=CommandType.PARALLEL, parallel_commands=[branch1, branch2])

    schema = {"bar.a": "float"}
    compiler = command_compiler(schema)

    with pytest.raises(TypeCheckError, match="same targets"):
        compiler.compile_command(node)
