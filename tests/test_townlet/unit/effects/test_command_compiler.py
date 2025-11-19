"""Tests for command compiler with expression validation."""

import pytest

from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.type_checker import TypeCheckError


def test_compiler_modify_validates_path():
    """Compiler validates modify command path exists."""
    node = CommandNode(type=CommandType.MODIFY, path="target.bar.energy", value_expr="5.0")

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.path == "target.bar.energy"


def test_compiler_modify_rejects_invalid_path():
    """Compiler rejects invalid path in modify command."""
    node = CommandNode(type=CommandType.MODIFY, path="target.bar.invalid", value_expr="5.0")

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    with pytest.raises(TypeCheckError, match="invalid"):
        compiler.compile_command(node)


def test_compiler_modify_validates_expression():
    """Compiler type-checks value expression."""
    node = CommandNode(type=CommandType.MODIFY, path="target.bar.energy", value_expr="target.bar.energy + 0.05")

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.value_expr == "target.bar.energy + 0.05"


def test_compiler_modify_rejects_type_mismatch():
    """Compiler rejects type mismatch in modify command."""
    node = CommandNode(
        type=CommandType.MODIFY,
        path="target.bar.energy",  # float
        value_expr="true",  # bool - type mismatch!
    )

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    with pytest.raises(TypeCheckError, match="Type mismatch"):
        compiler.compile_command(node)


def test_compiler_if_validates_bool_condition():
    """Compiler validates if condition is boolean."""
    node = CommandNode(
        type=CommandType.IF,
        condition_expr="target.bar.energy < 0.2",  # Should be bool
        then_commands=[],
        else_commands=[],
    )

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.condition_expr == "target.bar.energy < 0.2"


def test_compiler_if_rejects_non_bool_condition():
    """Compiler rejects non-boolean if condition."""
    node = CommandNode(
        type=CommandType.IF,
        condition_expr="target.bar.energy",  # float, not bool!
        then_commands=[],
        else_commands=[],
    )

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    with pytest.raises(TypeCheckError, match="bool"):
        compiler.compile_command(node)
