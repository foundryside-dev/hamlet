"""Tests for VFS profiles configuration DTOs."""

import pytest
from pydantic import ValidationError

from townlet.config.vfs_profiles_config import (
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
