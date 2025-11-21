"""Tests for command parser and AST."""

from townlet.config.effects_config import CommandConfig
from townlet.effects.parser import CommandParser
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


def test_parser_modify_command():
    """Parser converts modify CommandConfig to CommandNode."""
    config = CommandConfig(modify="target.bar.energy", value="target.bar.energy + 0.05")

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.MODIFY
    assert node.path == "target.bar.energy"
    assert node.value_expr == "target.bar.energy + 0.05"


def test_parser_spawn_effect_command():
    """Parser converts spawn_effect CommandConfig to CommandNode."""
    config = CommandConfig(spawn_effect="poisoned", target="self", intensity=2.0)

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.SPAWN_EFFECT
    assert node.effect_id == "poisoned"
    assert node.target == "self"
    assert node.target_expr == "self"
    assert node.intensity == 2.0


def test_parser_if_command():
    """Parser converts if CommandConfig to CommandNode with nesting."""

    config = CommandConfig.model_validate(
        {
            "if": "target.bar.energy < 0.2",
            "then": [{"modify": "target.vfs.is_crisis", "value": "true"}],
            "else": [{"modify": "target.vfs.is_crisis", "value": "false"}],
        }
    )

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.IF
    assert node.condition_expr == "target.bar.energy < 0.2"
    assert len(node.then_commands) == 1
    assert node.then_commands[0].type == CommandType.MODIFY
    assert len(node.else_commands) == 1
