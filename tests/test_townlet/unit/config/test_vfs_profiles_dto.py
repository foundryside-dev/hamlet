"""Tests for VFS profiles configuration DTOs."""

import pytest
from pydantic import ValidationError

from townlet.config.vfs_profiles_config import (
    AgentVFSProfileConfig,
    AgentVFSVariableConfig,
    GlobalVFSProfileConfig,
    GlobalVFSVariableConfig,
    ItemVFSProfileConfig,
    ItemVFSVariableConfig,
    VFSProfilesConfig,
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


def test_item_vfs_variable_with_initial_value():
    """Item VFS variable with static initial value."""
    config = ItemVFSVariableConfig(
        name="nutrition",
        type="float",
        initial_value=0.5,
        description="Nutritional value of food item",
    )

    assert config.name == "nutrition"
    assert config.type == "float"
    assert config.initial_value == 0.5


def test_item_vfs_variable_with_expression():
    """Item VFS variable with computed expression."""
    config = ItemVFSVariableConfig(
        name="is_spoiled",
        type="bool",
        expression="self.age > 100",
        description="True when item has spoiled",
    )

    assert config.name == "is_spoiled"
    assert config.expression == "self.age > 100"


def test_item_vfs_variable_with_owner_reference():
    """Item VFS can reference owning agent."""
    config = ItemVFSVariableConfig(
        name="owner",
        type="agent_ref",
        expression="self.held_by",
        description="Agent currently holding this item",
    )

    assert config.type == "agent_ref"


def test_item_vfs_profile_multiple_variables():
    """Item VFS profile supports multiple variables."""
    profile = ItemVFSProfileConfig(
        profile_name="food_stats",
        variables=[
            ItemVFSVariableConfig(name="nutrition", type="float", initial_value=0.5),
            ItemVFSVariableConfig(name="is_spoiled", type="bool", expression="self.age > 100"),
        ],
    )

    assert profile.profile_name == "food_stats"
    assert len(profile.variables) == 2


def test_vfs_profiles_config_complete():
    """VFSProfilesConfig loads global + agent + item profiles."""
    config = VFSProfilesConfig(
        version="1.0",
        evaluation_mode="mark_and_sweep",
        debug_logging=False,
        global_profile=GlobalVFSProfileConfig(
            variables=[
                GlobalVFSVariableConfig(name="day_count", type="int", initial_value=0),
            ]
        ),
        agent_profile=AgentVFSProfileConfig(
            variables=[
                AgentVFSVariableConfig(name="motivation", type="float", initial_value=1.0),
            ]
        ),
        item_profiles=[
            ItemVFSProfileConfig(
                profile_name="food_stats",
                variables=[
                    ItemVFSVariableConfig(name="nutrition", type="float", initial_value=0.5),
                ],
            ),
        ],
    )

    assert config.global_profile is not None
    assert config.agent_profile is not None
    assert len(config.item_profiles) == 1


def test_vfs_profiles_config_optional_sections():
    """VFSProfilesConfig allows missing sections."""
    config = VFSProfilesConfig(
        version="1.0",
        evaluation_mode="mark_and_sweep",
        debug_logging=False,
        global_profile=None,
        agent_profile=AgentVFSProfileConfig(variables=[]),
        item_profiles=[],
    )

    assert config.global_profile is None
    assert config.agent_profile is not None
    assert len(config.item_profiles) == 0


def test_vfs_profiles_config_owns_evaluator_runtime_flags():
    """VFS evaluator mode and logging are explicit config fields."""
    config = VFSProfilesConfig(
        version="1.0",
        evaluation_mode="eager",
        debug_logging=True,
        global_profile=None,
        agent_profile=None,
        item_profiles=[],
    )

    assert config.evaluation_mode == "eager"
    assert config.debug_logging is True


def test_vfs_profiles_config_requires_supported_version():
    """Version must be explicitly supported."""
    with pytest.raises(ValidationError):
        VFSProfilesConfig(
            version="0.9",
            evaluation_mode="mark_and_sweep",
            debug_logging=False,
            global_profile=None,
            agent_profile=None,
            item_profiles=[],
        )
