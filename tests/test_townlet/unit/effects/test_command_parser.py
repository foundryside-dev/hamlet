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


def test_parser_spawn_item_command():
    """Parser converts spawn_item CommandConfig to CommandNode."""
    config = CommandConfig(spawn_item="health_potion", position="random")

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.SPAWN_ITEM
    assert node.item_type == "health_potion"
    assert node.position == "random"
    assert node.position_expr == "random"


def test_parser_sample_command():
    """Parser converts sample CommandConfig to CommandNode."""
    config = CommandConfig(sample="uniform", params={"min": 0.0, "max": 1.0}, store_in="temp.roll")

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.SAMPLE
    assert node.sample_distribution == "uniform"
    assert node.sample_params == {"min": 0.0, "max": 1.0}
    assert node.sample_store_path == "temp.roll"


def test_parser_for_each_command():
    """Parser converts for_each CommandConfig to CommandNode."""
    config = CommandConfig.model_validate(
        {
            "for_each": "nearby_items",  # Expression-based, not registered resolver
            "as": "item",
            "do": [{"modify": "item.durability", "value": "item.durability - 1"}],
        }
    )

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.FOR_EACH
    assert node.collection_expr == "nearby_items"
    assert node.iterator == "item"
    assert len(node.body) == 1
    assert node.body[0].type == CommandType.MODIFY


def test_parser_switch_command():
    """Parser converts switch CommandConfig to CommandNode."""
    # Note: cases[i]["do"] contains CommandConfig objects, not raw dicts
    config = CommandConfig(
        switch="target.bar.energy",
        cases=[
            {"when": "energy < 0.2", "do": [CommandConfig(modify="target.vfs.state", value="'critical'")]},
            {"when": "energy < 0.5", "do": [CommandConfig(modify="target.vfs.state", value="'low'")]},
        ],
        default=[CommandConfig(modify="target.vfs.state", value="'normal'")],
    )

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.SWITCH
    assert node.switch_expr == "target.bar.energy"
    assert len(node.cases) == 2
    assert node.cases[0][0] == "energy < 0.2"  # when expression
    assert len(node.cases[0][1]) == 1  # do commands
    assert len(node.default_commands) == 1


def test_parser_reduce_command():
    """Parser converts reduce CommandConfig to CommandNode."""
    config = CommandConfig(
        reduce="nearby_agents",
        reduce_as="agent",
        reduce_init="0",
        reduce_body="acc + agent.bar.energy",
        reduce_into="temp.total_energy",
    )

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.REDUCE
    assert node.reduce_expr == "nearby_agents"
    assert node.reduce_iterator == "agent"
    assert node.reduce_init_expr == "0"
    assert node.reduce_body_expr == "acc + agent.bar.energy"
    assert node.reduce_target == "temp.total_energy"


def test_parser_parallel_command():
    """Parser converts parallel CommandConfig to CommandNode."""
    config = CommandConfig.model_validate(
        {
            "parallel": [
                {"modify": "target.bar.energy", "value": "target.bar.energy + 0.1"},
                {"modify": "target.bar.mood", "value": "target.bar.mood + 0.05"},
            ]
        }
    )

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.PARALLEL
    assert len(node.parallel_commands) == 2
    assert node.parallel_commands[0].type == CommandType.MODIFY
    assert node.parallel_commands[1].type == CommandType.MODIFY


def test_parser_delay_command():
    """Parser converts delay CommandConfig to CommandNode."""
    config = CommandConfig.model_validate({"delay": "10", "do": [{"modify": "target.bar.energy", "value": "target.bar.energy + 0.5"}]})

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.DELAY
    assert node.delay_ticks_expr == "10"
    assert len(node.delay_commands) == 1
    assert node.delay_commands[0].type == CommandType.MODIFY


def test_parser_invalid_command_raises():
    """CommandConfig validation rejects empty command."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Exactly one command type required"):
        CommandConfig()


def test_parser_spawn_effect_numeric_target():
    """Parser handles numeric string targets for spawn_effect."""
    config = CommandConfig(spawn_effect="buff", target="5", intensity=1.0)

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.SPAWN_EFFECT
    assert node.target == 5  # Should be resolved to int
    assert node.target_expr == "5"


def test_parser_spawn_effect_expression_target():
    """Parser handles expression targets for spawn_effect."""
    config = CommandConfig(spawn_effect="buff", target="agents[0]", intensity=1.0)

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.SPAWN_EFFECT
    assert node.target is None  # Expression - resolved at runtime
    assert node.target_expr == "agents[0]"


def test_parser_parse_commands_list():
    """Parser handles list of commands."""
    configs = [
        CommandConfig(modify="target.bar.energy", value="target.bar.energy + 0.1"),
        CommandConfig(modify="target.bar.mood", value="target.bar.mood + 0.05"),
    ]

    parser = CommandParser()
    nodes = parser.parse_commands(configs)

    assert len(nodes) == 2
    assert all(n.type == CommandType.MODIFY for n in nodes)


def test_parser_switch_missing_when_raises():
    """Parser raises ValueError when switch case is missing 'when'."""
    import pytest

    config = CommandConfig(
        switch="energy",
        cases=[{"do": [CommandConfig(modify="x", value="1")]}],  # Missing 'when'
        default=[],
    )

    parser = CommandParser()
    with pytest.raises(ValueError, match="'when' expression is required"):
        parser.parse_command(config)
