"""Affordance DTO stages must match the paths ActionExecutor can execute."""

from __future__ import annotations

import pytest

from townlet.config.affordances_v2_config import AffordanceParamConfig, DeploymentConfig, OpeningHoursConfig


def _affordance(
    interaction_type: str,
    *,
    interactions: dict[str, list[dict]] | None = None,
    costs: dict[str, float] | None = None,
    costs_per_tick: dict[str, float] | None = None,
) -> AffordanceParamConfig:
    return AffordanceParamConfig(
        name="TEST",
        interaction_type=interaction_type,
        duration_ticks=None if interaction_type == "instant" else 2,
        costs={} if costs is None else costs,
        costs_per_tick={} if costs_per_tick is None else costs_per_tick,
        interactions={
            "on_start": [],
            "per_tick": [],
            "on_completion": [],
            "on_early_exit": [],
            "on_failure": [],
            **({} if interactions is None else interactions),
        },
        opening_hours=OpeningHoursConfig(enabled=False),
        deployment=DeploymentConfig(type="fixed", positions=[[0, 0]]),
    )


@pytest.mark.parametrize(
    ("interaction_type", "interactions", "costs", "costs_per_tick"),
    (
        pytest.param("instant", {"on_completion": [{"modify": "target.bar.energy", "value": "0.0"}]}, {}, {}, id="instant-completion"),
        pytest.param("instant", {}, {}, {"energy": 0.1}, id="instant-per-tick-cost"),
        pytest.param("multi_tick", {"on_start": [{"modify": "target.bar.energy", "value": "0.0"}]}, {}, {}, id="multi-start"),
        pytest.param("multi_tick", {}, {"energy": 0.1}, {}, id="multi-instant-cost"),
        pytest.param("instant", {"on_early_exit": [{"modify": "target.bar.energy", "value": "0.0"}]}, {}, {}, id="instant-early-exit"),
        pytest.param("multi_tick", {"on_failure": [{"modify": "target.bar.energy", "value": "0.0"}]}, {}, {}, id="multi-failure"),
    ),
)
def test_unreachable_stage_or_cost_declaration_refuses(
    interaction_type: str,
    interactions: dict[str, list[dict]],
    costs: dict[str, float],
    costs_per_tick: dict[str, float],
) -> None:
    with pytest.raises(ValueError, match="unreachable|does not execute"):
        _affordance(
            interaction_type,
            interactions=interactions,
            costs=costs,
            costs_per_tick=costs_per_tick,
        )


@pytest.mark.parametrize("interaction_type", ("instant", "multi_tick"))
def test_reachable_stage_and_cost_matrix_is_admitted(interaction_type: str) -> None:
    interactions: dict[str, list[dict]] = {}
    costs: dict[str, float] = {}
    costs_per_tick: dict[str, float] = {}
    if interaction_type == "instant":
        interactions["on_start"] = [{"modify": "target.bar.energy", "value": "0.0"}]
        costs = {"energy": 0.1}
    if interaction_type == "multi_tick":
        interactions["per_tick"] = [{"modify": "target.bar.energy", "value": "0.0"}]
        interactions["on_completion"] = [{"modify": "target.bar.energy", "value": "0.0"}]
        costs_per_tick = {"energy": 0.1}

    result = _affordance(
        interaction_type,
        interactions=interactions,
        costs=costs,
        costs_per_tick=costs_per_tick,
    )

    assert result.interaction_type == interaction_type


@pytest.mark.parametrize("duration_ticks", (0, -1))
def test_multi_tick_duration_must_be_positive_at_authoring_boundary(duration_ticks: int) -> None:
    with pytest.raises(ValueError, match="duration_ticks|greater than 0"):
        AffordanceParamConfig(
            name="TEST",
            interaction_type="multi_tick",
            duration_ticks=duration_ticks,
            costs={},
            costs_per_tick={},
            interactions={
                "on_start": [],
                "per_tick": [{"modify": "target.bar.energy", "value": "0.0"}],
                "on_completion": [],
                "on_early_exit": [],
                "on_failure": [],
            },
            opening_hours=OpeningHoursConfig(enabled=False),
            deployment=DeploymentConfig(type="fixed", positions=[[0, 0]]),
        )
