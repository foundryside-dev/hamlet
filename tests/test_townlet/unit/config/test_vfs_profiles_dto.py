"""Tests for VFS profiles configuration DTOs."""

import pytest
from pydantic import ValidationError

from townlet.config.vfs_profiles_config import (
    AgentVFSProfileConfig,
    AgentVFSVariableConfig,
    GlobalVFSVariableConfig,
)


def test_global_vfs_variable_with_initial_value():
    """Global VFS variable with static initial value."""
    config = GlobalVFSVariableConfig(
        name="day_count",
        type="int",
        initial_value=0,
        description="Number of days elapsed",
    )

    assert config.name == "day_count"
    assert config.type == "int"
    assert config.initial_value == 0
    assert config.expression is None


def test_global_vfs_variable_with_expression():
    """Global VFS variable with computed expression."""
    config = GlobalVFSVariableConfig(
        name="is_night",
        type="bool",
        expression="temporal.tick % 24 >= 18",
        description="True during night time",
    )

    assert config.name == "is_night"
    assert config.type == "bool"
    assert config.expression == "temporal.tick % 24 >= 18"
    assert config.initial_value is None


def test_global_vfs_variable_requires_value_or_expression():
    """Must have either initial_value or expression."""
    with pytest.raises(ValidationError, match="exactly one"):
        GlobalVFSVariableConfig(
            name="invalid",
            type="int",
            # Missing both initial_value and expression
        )


def test_global_vfs_variable_rejects_both():
    """Cannot have both initial_value and expression."""
    with pytest.raises(ValidationError, match="exactly one"):
        GlobalVFSVariableConfig(
            name="invalid",
            type="int",
            initial_value=5,
            expression="bar.energy + 1",
        )


def test_agent_vfs_variable_with_initial_value():
    """Agent VFS variable with static initial value."""
    config = AgentVFSVariableConfig(
        name="motivation",
        type="float",
        initial_value=1.0,
        description="Agent's intrinsic motivation",
    )

    assert config.name == "motivation"
    assert config.type == "float"
    assert config.initial_value == 1.0


def test_agent_vfs_variable_with_expression():
    """Agent VFS variable with computed expression."""
    config = AgentVFSVariableConfig(
        name="is_crisis",
        type="bool",
        expression="bar.energy < 0.2 or bar.health < 0.2",
        description="True when agent is in resource crisis",
    )

    assert config.name == "is_crisis"
    assert config.expression == "bar.energy < 0.2 or bar.health < 0.2"


def test_agent_vfs_variable_with_reference_type():
    """Agent VFS can reference other entities."""
    config = AgentVFSVariableConfig(
        name="nearest_food",
        type="item_ref",
        expression="nearest(items, self.position, type='food')",
        description="Reference to nearest food item",
    )

    assert config.type == "item_ref"


def test_agent_vfs_profile_unique_names():
    """Agent VFS profile rejects duplicate variable names."""
    with pytest.raises(ValidationError, match="Duplicate"):
        AgentVFSProfileConfig(
            variables=[
                AgentVFSVariableConfig(name="x", type="int", initial_value=0),
                AgentVFSVariableConfig(name="x", type="int", initial_value=1),
            ]
        )
