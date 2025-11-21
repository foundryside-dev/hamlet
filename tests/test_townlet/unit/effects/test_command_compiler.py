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


def test_compiler_for_each_accepts_registered_collection_without_expr():
    """Compiler should accept enum-style for_each collection without collection_expr."""
    node = CommandNode(
        type=CommandType.FOR_EACH,
        collection="all_agents",
        body=[],
    )

    compiler = CommandCompiler(schema={})
    compiled = compiler.compile_command(node)

    assert compiled.collection == "all_agents"
    assert compiled.collection_ast is None


def test_compiler_for_each_rejects_unknown_collection():
    """Compiler should reject unknown for_each collections early."""
    node = CommandNode(
        type=CommandType.FOR_EACH,
        collection="not_real",
        body=[],
    )

    compiler = CommandCompiler(schema={})

    with pytest.raises(TypeCheckError, match="Unknown for_each collection"):
        compiler.compile_command(node)


def test_compiler_switch_happy_path():
    """Compiler type-checks switch equality cases."""
    node = CommandNode(
        type=CommandType.SWITCH,
        switch_expr="mode",
        cases=[("1", []), ("2", [])],
    )

    schema = {"mode": "int"}
    compiler = CommandCompiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.switch_ast is not None
    assert compiled.case_asts and len(compiled.case_asts) == 2


def test_compiler_switch_rejects_type_mismatch_case():
    """Compiler rejects switch case with mismatched type."""
    node = CommandNode(
        type=CommandType.SWITCH,
        switch_expr="mode",
        cases=[("true", [])],
    )

    schema = {"mode": "int"}
    compiler = CommandCompiler(schema)

    with pytest.raises(TypeCheckError, match="type mismatch"):
        compiler.compile_command(node)


def test_compiler_reduce_rejected_for_now():
    """Reduce command compiles when collection is fixed-size tensor path."""
    node = CommandNode(
        type=CommandType.REDUCE,
        reduce_expr="bar.col",
        reduce_iterator="i",
        reduce_init_expr="0",
        reduce_body_expr="acc + i",
        reduce_target="target.bar.energy",
    )

    schema = {"target.bar.energy": "int", "bar.col": "tensor"}
    compiler = CommandCompiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.collection_ast is not None


def test_compiler_for_each_rejects_nested_for_each():
    """Compiler rejects nested for_each commands."""
    inner = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", body=[])
    outer = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", body=[inner])

    compiler = CommandCompiler(schema={})

    with pytest.raises(TypeCheckError, match="Nested for_each"):
        compiler.compile_command(outer)


def test_compiler_delay_rejects_when_time_disabled():
    """delay commands are gated by time_enabled flag."""
    node = CommandNode(
        type=CommandType.DELAY,
        delay_ticks_expr="1",
        delay_commands=[CommandNode(type=CommandType.MODIFY, path="vfs.foo", value_expr="1")],
    )

    compiler = CommandCompiler(schema={"vfs.foo": "float"}, time_enabled=False)

    with pytest.raises(TypeCheckError, match="time is disabled"):
        compiler.compile_command(node)
