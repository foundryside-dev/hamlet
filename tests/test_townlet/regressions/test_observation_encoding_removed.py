"""Regression contract for the retired observation-encoding selector."""

from __future__ import annotations

import inspect
from typing import Any

import pytest
import torch
from pydantic import BaseModel, ValidationError

from townlet.config.stratum_config import ContinuousConfig, GridConfig, GridNDConfig
from townlet.substrate.continuous import (
    Continuous1DSubstrate,
    Continuous2DSubstrate,
    Continuous3DSubstrate,
    ContinuousSubstrate,
)
from townlet.substrate.continuousnd import ContinuousNDSubstrate
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.substrate.grid3d import Grid3DSubstrate
from townlet.substrate.gridnd import GridNDSubstrate


@pytest.mark.parametrize(
    ("config_type", "fields"),
    [
        (
            GridConfig,
            {
                "topology": "square",
                "width": 8,
                "height": 8,
                "boundary": "clamp",
                "distance_metric": "manhattan",
                "diagonals": False,
            },
        ),
        (
            GridNDConfig,
            {
                "dimension_sizes": [4, 4, 4, 4],
                "boundary": "clamp",
                "distance_metric": "manhattan",
                "topology": "hypercube",
            },
        ),
        (
            ContinuousConfig,
            {
                "dimensions": 2,
                "bounds": [(0.0, 10.0), (0.0, 20.0)],
                "boundary": "clamp",
                "movement_delta": 0.5,
                "interaction_radius": 1.0,
                "distance_metric": "euclidean",
                "action_discretization": {"num_directions": 8, "num_magnitudes": 3},
            },
        ),
    ],
)
def test_observation_encoding_is_rejected_by_stratum_dtos(config_type: type[BaseModel], fields: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        config_type.model_validate({**fields, "observation_encoding": "absolute"})


@pytest.mark.parametrize(
    "substrate_type",
    [
        Grid2DSubstrate,
        Grid3DSubstrate,
        GridNDSubstrate,
        ContinuousSubstrate,
        Continuous1DSubstrate,
        Continuous2DSubstrate,
        Continuous3DSubstrate,
        ContinuousNDSubstrate,
    ],
)
def test_observation_encoding_is_not_a_substrate_constructor_parameter(substrate_type: type[Any]) -> None:
    assert "observation_encoding" not in inspect.signature(substrate_type).parameters


def test_spatial_egocentric_deltas_use_one_bounded_encoding() -> None:
    cases = [
        (
            Grid2DSubstrate(width=8, height=4, boundary="clamp", distance_metric="manhattan"),
            torch.tensor([[0, 0]]),
            torch.tensor([[7, 3]]),
        ),
        (
            Grid3DSubstrate(width=8, height=4, depth=3, boundary="clamp", distance_metric="manhattan"),
            torch.tensor([[0, 0, 0]]),
            torch.tensor([[7, 3, 2]]),
        ),
        (
            GridNDSubstrate(dimension_sizes=[5, 4, 3, 2], boundary="clamp", distance_metric="manhattan"),
            torch.tensor([[0, 0, 0, 0]]),
            torch.tensor([[4, 3, 2, 1]]),
        ),
        (
            ContinuousSubstrate(
                dimensions=2,
                bounds=[(-5.0, 5.0), (10.0, 30.0)],
                boundary="clamp",
                movement_delta=0.5,
                interaction_radius=1.0,
                distance_metric="euclidean",
                action_discretization={"num_directions": 8, "num_magnitudes": 3},
            ),
            torch.tensor([[-5.0, 10.0]]),
            torch.tensor([[5.0, 30.0]]),
        ),
        (
            ContinuousNDSubstrate(
                bounds=[(-5.0, 5.0), (10.0, 30.0), (0.0, 4.0), (-2.0, 6.0)],
                boundary="clamp",
                movement_delta=0.5,
                interaction_radius=1.0,
                distance_metric="euclidean",
            ),
            torch.tensor([[-5.0, 10.0, 0.0, -2.0]]),
            torch.tensor([[5.0, 30.0, 4.0, 6.0]]),
        ),
    ]

    for substrate, observer, entity in cases:
        delta = substrate.egocentric_delta(observer, entity)
        assert delta[0, 0].tolist() == pytest.approx([1.0] * substrate.position_dim)
        assert torch.all(delta >= -1.0)
        assert torch.all(delta <= 1.0)
