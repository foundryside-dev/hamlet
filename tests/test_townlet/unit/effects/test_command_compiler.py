"""Tests for command compiler with expression validation."""

import pytest

from tests.test_townlet._fixtures.command_namespace import command_compiler
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.type_checker import TypeCheckError


def test_compiler_modify_validates_path():
    """Compiler validates modify command path exists."""
    node = CommandNode(type=CommandType.MODIFY, path="bar.energy", value_expr="5.0")

    schema = {"bar.energy": "float"}
    compiler = command_compiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.path == "bar.energy"


def test_compiler_modify_rejects_invalid_path():
    """Compiler rejects invalid path in modify command."""
    node = CommandNode(type=CommandType.MODIFY, path="bar.invalid", value_expr="5.0")

    schema = {"bar.energy": "float"}
    compiler = command_compiler(schema)

    with pytest.raises(TypeCheckError, match="invalid"):
        compiler.compile_command(node)


def test_compiler_modify_validates_expression():
    """Compiler type-checks value expression."""
    node = CommandNode(type=CommandType.MODIFY, path="bar.energy", value_expr="bar.energy + 0.05")

    schema = {"bar.energy": "float"}
    compiler = command_compiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.value_expr == "bar.energy + 0.05"


def test_compiler_modify_rejects_type_mismatch():
    """Compiler rejects type mismatch in modify command."""
    node = CommandNode(
        type=CommandType.MODIFY,
        path="bar.energy",  # float
        value_expr="true",  # bool - type mismatch!
    )

    schema = {"bar.energy": "float"}
    compiler = command_compiler(schema)

    with pytest.raises(TypeCheckError, match="Type mismatch"):
        compiler.compile_command(node)


def test_compiler_if_validates_bool_condition():
    """Compiler validates if condition is boolean."""
    node = CommandNode(
        type=CommandType.IF,
        condition_expr="bar.energy < 0.2",  # Should be bool
        then_commands=[],
        else_commands=[],
    )

    schema = {"bar.energy": "float"}
    compiler = command_compiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.condition_expr == "bar.energy < 0.2"


def test_compiler_if_rejects_non_bool_condition():
    """Compiler rejects non-boolean if condition."""
    node = CommandNode(
        type=CommandType.IF,
        condition_expr="bar.energy",  # float, not bool!
        then_commands=[],
        else_commands=[],
    )

    schema = {"bar.energy": "float"}
    compiler = command_compiler(schema)

    with pytest.raises(TypeCheckError, match="bool"):
        compiler.compile_command(node)


def test_compiler_for_each_accepts_registered_collection_without_expr():
    """Compiler should accept enum-style for_each collection without collection_expr."""
    node = CommandNode(
        type=CommandType.FOR_EACH,
        collection="all_agents",
        body=[],
    )

    compiler = command_compiler({})
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

    compiler = command_compiler({})

    with pytest.raises(TypeCheckError, match="Unknown for_each collection"):
        compiler.compile_command(node)


def test_compiler_for_each_accepts_collection_expression():
    """Compiler should accept expression-based for_each collections (no resolver lookup)."""
    node = CommandNode(
        type=CommandType.FOR_EACH,
        collection=None,
        collection_expr="held",
        body=[],
    )

    compiler = command_compiler({"held": "list"})
    compiled = compiler.compile_command(node)

    assert compiled.collection is None
    assert compiled.collection_ast is not None


def test_compiler_switch_happy_path():
    """Compiler type-checks switch equality cases."""
    node = CommandNode(
        type=CommandType.SWITCH,
        switch_expr="mode",
        cases=[("1", []), ("2", [])],
    )

    schema = {"mode": "int"}
    compiler = command_compiler(schema)

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
    compiler = command_compiler(schema)

    with pytest.raises(TypeCheckError, match="type mismatch"):
        compiler.compile_command(node)


def test_compiler_for_each_rejects_nested_for_each():
    """Compiler rejects nested for_each commands."""
    inner = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", body=[])
    outer = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", body=[inner])

    compiler = command_compiler({})

    with pytest.raises(TypeCheckError, match="Nested for_each"):
        compiler.compile_command(outer)


def test_compiler_for_each_rejects_nested_for_each_in_switch_case():
    """Nested for_each hidden inside switch is rejected."""
    inner = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", body=[])
    switch = CommandNode(
        type=CommandType.SWITCH,
        switch_expr="mode",
        cases=[("1", [inner])],
    )
    outer = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", body=[switch])

    compiler = command_compiler({"mode": "int"})

    with pytest.raises(TypeCheckError, match="Nested for_each"):
        compiler.compile_command(outer)


def test_compiler_for_each_rejects_nested_for_each_in_parallel():
    """Nested for_each hidden inside parallel is rejected."""
    inner = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", body=[])
    parallel = CommandNode(type=CommandType.PARALLEL, parallel_commands=[inner])
    outer = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", body=[parallel])

    compiler = command_compiler({})

    with pytest.raises(TypeCheckError, match="Nested for_each"):
        compiler.compile_command(outer)


def test_compiler_for_each_rejects_nested_for_each_in_delay():
    """Nested for_each hidden inside delay is rejected."""
    inner = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", body=[])
    delay = CommandNode(type=CommandType.DELAY, delay_ticks_expr="1", delay_commands=[inner])
    outer = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", body=[delay])

    compiler = command_compiler({})

    with pytest.raises(TypeCheckError, match="Nested for_each"):
        compiler.compile_command(outer)


def test_compiler_delay_rejects_when_time_disabled():
    """delay commands are gated by time_enabled flag."""
    node = CommandNode(
        type=CommandType.DELAY,
        delay_ticks_expr="1",
        delay_commands=[CommandNode(type=CommandType.MODIFY, path="foo", value_expr="1")],
    )

    compiler = command_compiler({"foo": "float"}, time_enabled=False)

    with pytest.raises(TypeCheckError, match="time is disabled"):
        compiler.compile_command(node)


# --- SPAWN_ITEM validation tests ---


def test_compiler_spawn_item_validates_item_type_required():
    """Compiler requires item_type for SPAWN_ITEM."""
    node = CommandNode(
        type=CommandType.SPAWN_ITEM,
        item_type=None,  # Missing!
        position="random",
    )

    compiler = command_compiler({})

    with pytest.raises(TypeCheckError, match="item_type"):
        compiler.compile_command(node)


def test_compiler_spawn_item_accepts_simple_position():
    """Compiler accepts simple position values without validation."""
    node = CommandNode(
        type=CommandType.SPAWN_ITEM,
        item_type="health_potion",
        position="random",
        quantity=1,
    )

    compiler = command_compiler({})
    compiled = compiler.compile_command(node)

    assert compiled.item_type == "health_potion"
    assert compiled.position == "random"


def test_compiler_spawn_item_validates_position_expression():
    """Compiler parses and validates complex position expressions."""
    node = CommandNode(
        type=CommandType.SPAWN_ITEM,
        item_type="health_potion",
        position="coords",  # Not a simple value
        position_expr="cell + 1",
        quantity=1,
    )

    compiler = command_compiler({"cell": "int"})
    compiled = compiler.compile_command(node)

    assert compiled.item_type == "health_potion"
    assert compiled.position_ast is not None
