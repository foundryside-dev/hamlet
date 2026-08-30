"""Central fixtures for substrate tests (explicit params, diagonal control)."""

from __future__ import annotations

import pytest

from townlet.substrate.continuous import Continuous1DSubstrate, Continuous2DSubstrate, Continuous3DSubstrate
from townlet.substrate.continuousnd import ContinuousNDSubstrate
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.substrate.grid3d import Grid3DSubstrate
from townlet.substrate.gridnd import GridNDSubstrate


@pytest.fixture
def action_disc():
    return {"num_directions": 8, "num_magnitudes": 3}


@pytest.fixture
def grid2d_diagonals():
    return Grid2DSubstrate(
        width=8,
        height=8,
        boundary="clamp",
        distance_metric="manhattan",
        enable_diagonals=True,
    )


@pytest.fixture
def grid3d_diagonals():
    return Grid3DSubstrate(
        width=8,
        height=8,
        depth=3,
        boundary="clamp",
        distance_metric="manhattan",
        enable_diagonals=True,
    )


@pytest.fixture
def gridnd_no_diagonals():
    return GridNDSubstrate(
        dimension_sizes=[8, 8, 8, 8],
        boundary="clamp",
        distance_metric="manhattan",
        topology="hypercube",
        enable_diagonals=False,
    )


@pytest.fixture
def cont1d(action_disc):
    return Continuous1DSubstrate(
        min_x=0.0,
        max_x=10.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        action_discretization=action_disc,
    )


@pytest.fixture
def cont2d(action_disc):
    return Continuous2DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=10.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        action_discretization=action_disc,
    )


@pytest.fixture
def cont3d(action_disc):
    return Continuous3DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=10.0,
        min_z=0.0,
        max_z=5.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        action_discretization=action_disc,
    )


@pytest.fixture
def contnd():
    return ContinuousNDSubstrate(
        bounds=[(0.0, 1.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0)],
        boundary="clamp",
        movement_delta=0.1,
        interaction_radius=0.2,
        distance_metric="euclidean",
    )
