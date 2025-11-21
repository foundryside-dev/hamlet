"""Tests for Effects configuration DTOs."""

import pytest
from pydantic import ValidationError

from townlet.config.effects_config import (
    CommandConfig,
    EffectDefinitionConfig,
    EffectScope,
    ReapplyPolicy,
)


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


def test_command_config_parallel_not_set():
    """parallel defaults to None to avoid tripping validation."""
    cmd = CommandConfig(modify="target.bar.energy", value="5.0")
    assert cmd.parallel is None


def test_command_config_parallel_requires_branch():
    """parallel command must declare at least one branch."""
    with pytest.raises(ValidationError, match="parallel command requires at least one branch"):
        CommandConfig(parallel=[])


def test_effect_definition_minimal():
    """EffectDefinitionConfig with minimal required fields."""
    effect = EffectDefinitionConfig(
        id="ate_food",
        scope="agent",
        duration=10,
        reapply_policy="stack",
    )

    assert effect.id == "ate_food"
    assert effect.scope == EffectScope.AGENT
    assert effect.duration == 10
    assert effect.reapply_policy == ReapplyPolicy.STACK
    assert effect.intensity == 1.0  # Default
    assert effect.observable is True  # Default
    assert effect.on_spawn == []
    assert effect.on_tick == []
    assert effect.on_despawn == []


def test_effect_definition_with_commands():
    """EffectDefinitionConfig with lifecycle commands."""
    effect = EffectDefinitionConfig(
        id="poisoned",
        scope="agent",
        duration=20,
        intensity=0.5,
        reapply_policy="merge",
        observable=True,
        on_spawn=[{"modify": "target.vfs.is_poisoned", "value": "true"}],
        on_tick=[{"modify": "target.bar.health", "value": "target.bar.health - (0.1 * intensity)"}],
        on_despawn=[{"modify": "target.vfs.is_poisoned", "value": "false"}],
    )

    assert effect.id == "poisoned"
    assert effect.intensity == 0.5
    assert effect.reapply_policy == ReapplyPolicy.MERGE
    assert len(effect.on_spawn) == 1
    assert len(effect.on_tick) == 1
    assert len(effect.on_despawn) == 1


def test_effect_definition_requires_duration():
    """EffectDefinitionConfig requires duration field."""
    with pytest.raises(ValidationError, match="duration"):
        EffectDefinitionConfig(
            id="invalid",
            scope="agent",
            reapply_policy="stack",
            # Missing duration
        )


def test_effect_definition_requires_reapply_policy():
    """EffectDefinitionConfig requires reapply_policy (no default)."""
    with pytest.raises(ValidationError, match="reapply_policy"):
        EffectDefinitionConfig(
            id="invalid",
            scope="agent",
            duration=10,
            # Missing reapply_policy
        )


def test_effects_config_minimal():
    """EffectsConfig loads from YAML structure."""
    from townlet.config.effects_config import EffectsConfig

    config = EffectsConfig(
        version="1.0",
        effect_definitions=[
            {
                "id": "ate_food",
                "scope": "agent",
                "duration": 10,
                "reapply_policy": "stack",
            }
        ],
    )

    assert config.version == "1.0"
    assert len(config.effect_definitions) == 1
    assert config.effect_definitions[0].id == "ate_food"


def test_effects_config_rejects_duplicate_ids():
    """EffectsConfig validates unique effect IDs."""
    from townlet.config.effects_config import EffectsConfig

    with pytest.raises(ValidationError, match="Duplicate effect"):
        EffectsConfig(
            version="1.0",
            effect_definitions=[
                {"id": "poisoned", "scope": "agent", "duration": 10, "reapply_policy": "stack"},
                {"id": "poisoned", "scope": "agent", "duration": 20, "reapply_policy": "merge"},
            ],
        )


def test_effects_config_from_yaml():
    """EffectsConfig can load from YAML file."""
    import yaml

    from townlet.config.effects_config import EffectsConfig

    yaml_content = """
version: "1.0"

effect_definitions:
  - id: "ate_food"
    scope: agent
    duration: 10
    reapply_policy: stack
    on_tick:
      - modify: target.bar.energy
        value: target.bar.energy + 0.05

  - id: "poisoned"
    scope: agent
    duration: 20
    intensity: 0.5
    reapply_policy: merge
    on_tick:
      - modify: target.bar.health
        value: target.bar.health - (0.1 * intensity)
"""

    data = yaml.safe_load(yaml_content)
    config = EffectsConfig(**data)

    assert len(config.effect_definitions) == 2
    assert config.effect_definitions[0].id == "ate_food"
    assert config.effect_definitions[1].id == "poisoned"
