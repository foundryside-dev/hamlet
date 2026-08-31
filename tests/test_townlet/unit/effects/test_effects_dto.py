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


def test_command_config_spawn_effect_requires_target_and_intensity():
    """spawn_effect commands must spell out behavior-affecting fields."""
    with pytest.raises(ValidationError, match="target"):
        CommandConfig(spawn_effect="poisoned", intensity=1.0)

    with pytest.raises(ValidationError, match="intensity"):
        CommandConfig(spawn_effect="poisoned", target="self")


@pytest.mark.parametrize("intensity", (float("nan"), float("inf"), float("-inf")))
def test_command_config_spawn_effect_refuses_nonfinite_intensity(intensity: float):
    with pytest.raises(ValidationError, match="finite number"):
        CommandConfig(spawn_effect="poisoned", target="self", intensity=intensity)


def test_command_config_sample_rejects_distribution_alias():
    """sample is the only accepted stochastic command key."""
    with pytest.raises(ValidationError, match="Extra inputs"):
        CommandConfig(distribution="uniform", params={"min": 0.0, "max": 1.0}, store_in="target.vfs.roll")


def test_command_config_rejects_trigger_cascade_command():
    """Passive cascades are VTC rules, not effects commands."""
    with pytest.raises(ValidationError, match="Extra inputs"):
        CommandConfig(trigger_cascade="hunger_cascade", cascade_strength=1.0)


def test_command_config_rejects_removed_trigger_cascade_even_with_valid_command():
    """Deleted command keys must fail loudly instead of being ignored."""
    with pytest.raises(ValidationError, match="Extra inputs"):
        CommandConfig(
            modify="target.bar.energy",
            value="target.bar.energy + 0.05",
            trigger_cascade="hunger_cascade",
            cascade_strength=1.0,
        )


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
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )

    assert effect.id == "ate_food"
    assert effect.scope == EffectScope.AGENT
    assert effect.duration == 10
    assert effect.reapply_policy == ReapplyPolicy.STACK
    assert effect.observable is True
    assert effect.on_spawn == []
    assert effect.on_tick == []
    assert effect.on_despawn == []


def test_effect_definition_with_commands():
    """EffectDefinitionConfig with lifecycle commands."""
    effect = EffectDefinitionConfig(
        id="poisoned",
        scope="agent",
        duration=20,
        reapply_policy="merge",
        observable=True,
        on_spawn=[{"modify": "target.vfs.is_poisoned", "value": "true"}],
        on_tick=[{"modify": "target.bar.health", "value": "target.bar.health - (0.1 * intensity)"}],
        on_despawn=[{"modify": "target.vfs.is_poisoned", "value": "false"}],
        on_interrupt=[],
    )

    assert effect.id == "poisoned"
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
            observable=True,
            # Missing duration
        )


def test_effect_definition_requires_observable():
    with pytest.raises(ValidationError, match="observable"):
        EffectDefinitionConfig(id="invalid", scope="agent", duration=1, reapply_policy="stack")


@pytest.mark.parametrize("field", ("on_spawn", "on_tick", "on_despawn", "on_interrupt"))
@pytest.mark.parametrize("mode", ("missing", "null"))
def test_effect_definition_requires_explicit_nonnull_lifecycle_lists(field: str, mode: str):
    payload = {
        "id": "explicit",
        "scope": "agent",
        "duration": 1,
        "reapply_policy": "stack",
        "observable": True,
        "on_spawn": [],
        "on_tick": [],
        "on_despawn": [],
        "on_interrupt": [],
    }
    if mode == "missing":
        del payload[field]
    else:
        payload[field] = None

    with pytest.raises(ValidationError, match=field):
        EffectDefinitionConfig.model_validate(payload)


def test_effect_definition_requires_reapply_policy():
    """EffectDefinitionConfig requires reapply_policy (no default)."""
    with pytest.raises(ValidationError, match="reapply_policy"):
        EffectDefinitionConfig(
            id="invalid",
            scope="agent",
            duration=10,
            observable=True,
            # Missing reapply_policy
        )


def test_effects_config_minimal():
    """EffectsConfig loads from YAML structure."""
    from townlet.config.effects_config import EffectsConfig

    config = EffectsConfig(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        version="1.0",
        effect_definitions=[
            {
                "id": "ate_food",
                "scope": "agent",
                "duration": 10,
                "reapply_policy": "stack",
                "observable": True,
                "on_spawn": [],
                "on_tick": [],
                "on_despawn": [],
                "on_interrupt": [],
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
                {
                    "id": "poisoned",
                    "scope": "agent",
                    "duration": 10,
                    "reapply_policy": "stack",
                    "observable": True,
                    "on_spawn": [],
                    "on_tick": [],
                    "on_despawn": [],
                    "on_interrupt": [],
                },
                {
                    "id": "poisoned",
                    "scope": "agent",
                    "duration": 20,
                    "reapply_policy": "merge",
                    "observable": True,
                    "on_spawn": [],
                    "on_tick": [],
                    "on_despawn": [],
                    "on_interrupt": [],
                },
            ],
        )


def test_effects_config_from_yaml():
    """EffectsConfig can load from YAML file."""
    import yaml

    from townlet.config.effects_config import EffectsConfig

    yaml_content = """
version: "1.0"

max_active_effects: {global: 8, agent: 8, item: 8, affordance: 8}
effect_definitions:
  - id: "ate_food"
    scope: agent
    duration: 10
    reapply_policy: stack
    observable: true
    on_spawn: []
    on_tick:
      - modify: target.bar.energy
        value: target.bar.energy + 0.05
    on_despawn: []
    on_interrupt: []

  - id: "poisoned"
    scope: agent
    duration: 20
    reapply_policy: merge
    observable: true
    on_spawn: []
    on_tick:
      - modify: target.bar.health
        value: target.bar.health - (0.1 * intensity)
    on_despawn: []
    on_interrupt: []
"""

    data = yaml.safe_load(yaml_content)
    config = EffectsConfig(**data)

    assert len(config.effect_definitions) == 2
    assert config.effect_definitions[0].id == "ate_food"
    assert config.effect_definitions[1].id == "poisoned"
