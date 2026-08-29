"""Test configurable observation encoding for Grid3D substrate."""

import pytest
import torch

from townlet.substrate.grid3d import Grid3DSubstrate


@pytest.fixture
def device():
    return torch.device("cpu")


@pytest.fixture
def grid3d_relative(device):
    """Grid3D with relative encoding (normalized coordinates)."""
    return Grid3DSubstrate(
        width=8,
        height=8,
        depth=3,
        boundary="clamp",
        distance_metric="manhattan",
        observation_encoding="relative",
    )


@pytest.fixture
def grid3d_scaled(device):
    """Grid3D with scaled encoding (normalized + ranges)."""
    return Grid3DSubstrate(
        width=8,
        height=8,
        depth=3,
        boundary="clamp",
        distance_metric="manhattan",
        observation_encoding="scaled",
    )


@pytest.fixture
def grid3d_absolute(device):
    """Grid3D with absolute encoding (raw coordinates)."""
    return Grid3DSubstrate(
        width=8,
        height=8,
        depth=3,
        boundary="clamp",
        distance_metric="manhattan",
        observation_encoding="absolute",
    )


def test_grid3d_default_encoding_is_relative():
    """Grid3D should default to relative encoding for backward compatibility."""
    substrate = Grid3DSubstrate(
        width=8,
        height=8,
        depth=3,
        boundary="clamp",
        distance_metric="manhattan",
        # observation_encoding NOT provided
    )
    assert substrate.observation_encoding == "relative"
