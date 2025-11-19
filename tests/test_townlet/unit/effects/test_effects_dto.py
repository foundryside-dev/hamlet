"""Tests for Effects configuration DTOs."""

import pytest
from pydantic import ValidationError

from townlet.config.effects_config import CommandConfig, EffectScope, ReapplyPolicy


def test_reapply_policy_enum():
    """ReapplyPolicy has exactly 4 values."""
    assert ReapplyPolicy.STACK.value == "stack"
    assert ReapplyPolicy.RENEW.value == "renew"
    assert ReapplyPolicy.MERGE.value == "merge"
    assert ReapplyPolicy.REPLACE.value == "replace"


def test_reapply_policy_case_insensitive():
    """ReapplyPolicy accepts mixed case strings."""
    assert ReapplyPolicy("stack") == ReapplyPolicy.STACK
    assert ReapplyPolicy("Stack") == ReapplyPolicy.STACK
    assert ReapplyPolicy("STACK") == ReapplyPolicy.STACK


def test_effect_scope_enum():
    """EffectScope has exactly 4 values."""
    assert EffectScope.GLOBAL.value == "global"
    assert EffectScope.AGENT.value == "agent"
    assert EffectScope.ITEM.value == "item"
    assert EffectScope.AFFORDANCE.value == "affordance"


def test_effect_scope_case_insensitive():
    """EffectScope accepts mixed case strings."""
    assert EffectScope("global") == EffectScope.GLOBAL
    assert EffectScope("Global") == EffectScope.GLOBAL
    assert EffectScope("GLOBAL") == EffectScope.GLOBAL


def test_command_config_modify():
    """CommandConfig validates modify commands."""
    cmd = CommandConfig(modify="target.bar.energy", value="target.bar.energy + 0.05")

    assert cmd.modify == "target.bar.energy"
    assert cmd.value == "target.bar.energy + 0.05"
    assert cmd.spawn_effect is None
    assert cmd.if_condition is None


def test_command_config_spawn_effect():
    """CommandConfig validates spawn_effect commands."""
    cmd = CommandConfig(spawn_effect="poisoned", target="self", intensity=2.0)

    assert cmd.spawn_effect == "poisoned"
    assert cmd.target == "self"
    assert cmd.intensity == 2.0


def test_command_config_requires_one_command_type():
    """CommandConfig requires exactly one command type."""
    with pytest.raises(ValidationError, match="Exactly one command"):
        CommandConfig()  # No command specified

    with pytest.raises(ValidationError, match="Exactly one command"):
        CommandConfig(
            modify="target.bar.energy",
            value="5.0",
            spawn_effect="poisoned",  # Can't have both
        )


def test_command_config_modify_requires_value():
    """modify command must have value field."""
    with pytest.raises(ValidationError, match="modify command requires 'value' field"):
        CommandConfig(modify="target.bar.energy")  # Missing value
