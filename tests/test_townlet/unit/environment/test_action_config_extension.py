"""Test ActionConfig's VFS ``writes`` field.

``ActionConfig.reads`` was deleted (VFS round-2 S8): nothing consumed it, the compiler
always emitted an empty tuple, and a declared dependency list that no code checked was a
second authority over the write expressions. What an action reads is the expressions'
business.
"""

import pytest
from pydantic import ValidationError

from townlet.environment.action_config import ActionConfig
from townlet.vfs.schema import WriteSpec


def make_write_spec(variable_id: str, expression: str, *, telemetry_label: str) -> WriteSpec:
    return WriteSpec(
        variable_id=variable_id,
        expression=expression,
        condition=None,
        composition="additive_delta",
        phase="action_effects",
        priority=0,
        clamp=None,
        telemetry_label=telemetry_label,
    )


def _action(**overrides) -> ActionConfig:
    payload = dict(
        id=0,
        name="REST",
        type="passive",
        costs={},
        effects={},
        delta=None,
        teleport_to=None,
        enabled=True,
        description=None,
        icon=None,
        source="custom",
        source_affordance=None,
    )
    payload.update(overrides)
    return ActionConfig(**payload)


class TestActionConfigWritesField:
    """Test ActionConfig with writes field (VFS WriteSpec)."""

    def test_action_config_with_writes(self):
        write_spec = make_write_spec(variable_id="position", expression="home_pos", telemetry_label="teleport_home_position")
        action = _action(name="TELEPORT_HOME", type="movement", costs={"energy": 0.05}, teleport_to=[0, 0], writes=[write_spec])

        assert len(action.writes) == 1
        assert action.writes[0].variable_id == "position"
        assert action.writes[0].expression == "home_pos"

    def test_action_config_with_multiple_writes(self):
        write_specs = [
            make_write_spec(variable_id="energy", expression="energy - 0.1", telemetry_label="rest_energy_cost"),
            make_write_spec(variable_id="mood", expression="mood + 0.05", telemetry_label="rest_mood_gain"),
        ]
        action = _action(writes=write_specs)

        assert len(action.writes) == 2
        assert action.writes[0].variable_id == "energy"
        assert action.writes[1].variable_id == "mood"

    def test_action_config_with_empty_writes(self):
        action = _action(name="WAIT", source="substrate", costs={"energy": 0.001}, writes=[])
        assert action.writes == []


class TestActionConfigSerialization:
    def test_action_config_serialization_with_writes(self):
        write_spec = make_write_spec(variable_id="energy", expression="energy - 0.1", telemetry_label="rest_energy_cost")
        action = _action(effects={"energy": 0.02}, writes=[write_spec])

        data = action.model_dump()
        assert "writes" in data
        assert "reads" not in data
        assert len(data["writes"]) == 1

        action2 = ActionConfig.model_validate(data)
        assert len(action2.writes) == 1
        assert action2.writes[0].variable_id == "energy"

    def test_action_config_serialization_omitted_writes(self):
        action = _action(name="UP", type="movement", source="substrate", costs={"energy": 0.005}, delta=[0, -1])
        assert action.model_dump()["writes"] == []


class TestActionConfigValidation:
    def test_action_config_writes_must_be_list(self):
        with pytest.raises(ValidationError):
            _action(writes="not_a_list")

    def test_deleted_reads_field_is_refused_at_parse(self):
        """The old dependency list is an unknown key, not a silently dropped one."""
        with pytest.raises(ValidationError, match="reads"):
            _action(reads=["energy"])
