"""Tests for command parser and AST."""

from townlet.effects.schema import CommandNode, CommandType


def test_command_node_modify():
    """CommandNode for modify command."""
    node = CommandNode(type=CommandType.MODIFY, path="target.bar.energy", value_expr="target.bar.energy + 0.05")

    assert node.type == CommandType.MODIFY
    assert node.path == "target.bar.energy"
    assert node.value_expr == "target.bar.energy + 0.05"


def test_command_node_spawn_effect():
    """CommandNode for spawn_effect command."""
    node = CommandNode(type=CommandType.SPAWN_EFFECT, effect_id="poisoned", target_expr="self", intensity=2.0)

    assert node.type == CommandType.SPAWN_EFFECT
    assert node.effect_id == "poisoned"
    assert node.target_expr == "self"
    assert node.intensity == 2.0


def test_command_node_if():
    """CommandNode for if command with nested then/else."""
    node = CommandNode(
        type=CommandType.IF,
        condition_expr="target.bar.energy < 0.2",
        then_commands=[CommandNode(type=CommandType.MODIFY, path="target.vfs.is_crisis", value_expr="true")],
        else_commands=[CommandNode(type=CommandType.MODIFY, path="target.vfs.is_crisis", value_expr="false")],
    )

    assert node.type == CommandType.IF
    assert node.condition_expr == "target.bar.energy < 0.2"
    assert len(node.then_commands) == 1
    assert len(node.else_commands) == 1
