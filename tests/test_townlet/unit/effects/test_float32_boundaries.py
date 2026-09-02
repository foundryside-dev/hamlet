"""Float32 authoring boundaries for executable effects and affordances."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from townlet.config.affordances_v2_config import AffordanceParamConfig, DeploymentConfig, OpeningHoursConfig
from townlet.config.effects_config import CommandConfig
from townlet.effects.affordance_identity import AffordanceMeterWrite, SpawnedEffectIdentity
from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.manager import ActiveEffect, EffectManager
from townlet.numeric import require_float32


@pytest.mark.parametrize(
    "value",
    (float("nan"), float("inf"), float("-inf"), 1.0e39, -1.0e39, 1.0e-50, -1.0e-50),
)
def test_require_float32_refuses_nonfinite_overflow_and_underflow(value: float) -> None:
    with pytest.raises(ValueError, match="test value.*float32"):
        require_float32(value, field="test value")


def test_require_float32_returns_the_runtime_value() -> None:
    value = require_float32(0.1, field="test value")

    assert value != 0.1
    assert math.isclose(value, 0.1, rel_tol=1.0e-7)


def _affordance(*, costs: dict[str, float] | None = None, costs_per_tick: dict[str, float] | None = None) -> AffordanceParamConfig:
    interaction_type = "multi_tick" if costs_per_tick is not None else "instant"
    return AffordanceParamConfig(
        name="TEST",
        costs={} if costs is None else costs,
        costs_per_tick={} if costs_per_tick is None else costs_per_tick,
        interactions={
            "on_start": [],
            "per_tick": [],
            "on_completion": [],
            "on_early_exit": [],
            "on_failure": [],
        },
        interaction_type=interaction_type,
        duration_ticks=2 if interaction_type == "multi_tick" else None,
        opening_hours=OpeningHoursConfig(enabled=False),
        deployment=DeploymentConfig(type="fixed", positions=[[0, 0]]),
    )


@pytest.mark.parametrize(
    ("field", "amount"),
    (
        pytest.param("costs", 1.0e39, id="cost-overflow"),
        pytest.param("costs", 1.0e-50, id="cost-underflow"),
        pytest.param("costs_per_tick", -1.0e39, id="per-tick-overflow"),
        pytest.param("costs_per_tick", -1.0e-50, id="per-tick-underflow"),
    ),
)
def test_affordance_costs_refuse_values_without_float32_runtime_meaning(field: str, amount: float) -> None:
    kwargs = {field: {"energy": amount}}

    with pytest.raises(ValidationError, match="float32"):
        _affordance(**kwargs)


@pytest.mark.parametrize("delta", (1.0e39, -1.0e39, 1.0e-50, -1.0e-50))
def test_direct_meter_write_refuses_values_without_float32_runtime_meaning(delta: float) -> None:
    with pytest.raises(ValueError, match="delta.*float32"):
        AffordanceMeterWrite("energy", 1, delta, "on_start", "interaction", "target", None)


@pytest.mark.parametrize("intensity", (1.0e39, -1.0e39, 1.0e-50, -1.0e-50))
def test_spawn_intensity_refuses_values_without_float32_runtime_meaning(intensity: float) -> None:
    with pytest.raises(ValidationError, match="intensity.*float32"):
        CommandConfig(spawn_effect="poison", target="target", intensity=intensity)

    with pytest.raises(ValueError, match="intensity.*float32"):
        SpawnedEffectIdentity("target", intensity, 2, "agent", "merge", True)


def _catalog() -> EffectCatalog:
    return EffectCatalog(
        effects={
            "poison": CompiledEffect(
                id="poison",
                scope="agent",
                duration=10,
                reapply_policy="merge",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        },
        max_active_effects={"global": 1, "agent": 1, "item": 1, "affordance": 1},
    )


def test_active_effect_refuses_invalid_runtime_intensity() -> None:
    with pytest.raises(ValueError, match="intensity.*float32"):
        ActiveEffect(
            effect_id="poison",
            instance_id=0,
            target_entity_id=0,
            scope="agent",
            intensity=1.0e39,
            duration_total=10,
            duration_remaining=10,
            elapsed_ticks=0,
            spawn_step=0,
            observable=True,
        )


def test_effect_manager_stores_canonical_float32_intensity() -> None:
    manager = EffectManager(catalog=_catalog(), device="cpu")

    effect = manager.spawn_effect("poison", 0, intensity=0.1, current_step=0)

    assert effect.intensity == require_float32(0.1, field="expected")


def test_effect_manager_refuses_float32_merge_overflow_transactionally() -> None:
    manager = EffectManager(catalog=_catalog(), device="cpu")
    existing = manager.spawn_effect("poison", 0, intensity=2.0e38, current_step=0)
    before = existing.intensity

    with pytest.raises(ValueError, match="merged effect intensity.*float32"):
        manager.spawn_effect("poison", 0, intensity=2.0e38, current_step=1)

    assert existing.intensity == before
    assert manager.agent_effects[0] == [existing]
    assert manager.next_instance_id == 1
