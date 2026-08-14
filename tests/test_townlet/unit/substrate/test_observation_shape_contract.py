"""The substrate observation-shape contract (WS-7 first knockdown, PDR-0035).

The compiler learns a substrate's observation shape by ASKING THE SUBSTRATE
INSTANCE — never by switching on `substrate.type` strings. These tests pin the
contract's load-bearing invariant: every declared component width equals the
width of the tensor the substrate's own encoder actually produces. The three
DIV-003 crashes (docs/oracle/known-divergences.md) are exactly what happens
when the two diverge.

Parity is asserted against the SAME encoder calls the runtime publishes
(observation_encoder.py's sync helpers and their fallback chain), so a
substrate cannot pass by agreeing with itself about the wrong quantity.
"""

from __future__ import annotations

import pytest
import torch

from townlet.substrate.aspatial import AspatialSubstrate
from townlet.substrate.continuous import Continuous2DSubstrate
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.substrate.grid3d import Grid3DSubstrate
from townlet.substrate.gridnd import GridNDSubstrate

_DEVICE = torch.device("cpu")


def _grid2d(encoding: str = "relative", width: int = 8, height: int = 8) -> Grid2DSubstrate:
    return Grid2DSubstrate(
        width=width,
        height=height,
        boundary="clamp",
        distance_metric="manhattan",
        observation_encoding=encoding,
        topology="square",
        enable_diagonals=True,
    )


def _grid3d(encoding: str = "relative", depth: int = 3) -> Grid3DSubstrate:
    return Grid3DSubstrate(
        width=8,
        height=8,
        depth=depth,
        boundary="clamp",
        distance_metric="manhattan",
        observation_encoding=encoding,
        topology="cubic",
        enable_diagonals=True,
    )


def _gridnd(encoding: str = "relative") -> GridNDSubstrate:
    return GridNDSubstrate(
        dimension_sizes=[4, 4, 4, 4],
        boundary="clamp",
        distance_metric="manhattan",
        observation_encoding=encoding,
        topology="hypercube",
    )


def _continuous2d(encoding: str = "relative") -> Continuous2DSubstrate:
    return Continuous2DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=10.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding=encoding,
        action_discretization={"num_directions": 8, "num_speeds": 1},
    )


def _positions_for(substrate) -> torch.Tensor:
    dtype = substrate.position_dtype
    return torch.zeros((3, substrate.position_dim), dtype=dtype, device=_DEVICE)


def _published_position_features(substrate, positions: torch.Tensor) -> torch.Tensor | None:
    """Mirror observation_encoder._encode_position_observation's fallback chain."""
    for name in ("_encode_position_features", "encode_position_features", "encode_observation"):
        encoder = getattr(substrate, name, None)
        if callable(encoder):
            return encoder(positions, {})
    normalizer = getattr(substrate, "normalize_positions", None)
    if callable(normalizer):
        return normalizer(positions)
    return None


# --- grid encoding (obs_grid_encoding) --------------------------------------


@pytest.mark.parametrize("encoding", ["relative", "scaled", "absolute"])
def test_grid2d_grid_encoding_dim_matches_encoder(encoding: str) -> None:
    substrate = _grid2d(encoding)
    produced = substrate._encode_full_grid(_positions_for(substrate), {})
    assert substrate.get_grid_encoding_dim() == produced.shape[1] == 64


def test_grid2d_rect_grid_encoding_dim_matches_encoder() -> None:
    substrate = _grid2d(width=8, height=6)
    produced = substrate._encode_full_grid(_positions_for(substrate), {})
    assert substrate.get_grid_encoding_dim() == produced.shape[1] == 48


@pytest.mark.parametrize("encoding", ["relative", "scaled"])
def test_grid3d_grid_encoding_dim_matches_encoder(encoding: str) -> None:
    substrate = _grid3d(encoding)
    produced = substrate._encode_full_grid(_positions_for(substrate), {})
    assert substrate.get_grid_encoding_dim() == produced.shape[1] == 192


@pytest.mark.parametrize(("encoding", "expected"), [("relative", 4), ("scaled", 8), ("absolute", 4)])
def test_gridnd_grid_encoding_dim_matches_encoder(encoding: str, expected: int) -> None:
    """GridND has no occupancy grid; its published 'grid encoding' IS its
    coordinate encoding (observation_encoder falls back to encode_observation)."""
    substrate = _gridnd(encoding)
    produced = substrate.encode_observation(_positions_for(substrate), {})
    assert substrate.get_grid_encoding_dim() == produced.shape[1] == expected


def test_aspatial_grid_encoding_dim_is_zero() -> None:
    assert AspatialSubstrate().get_grid_encoding_dim() == 0


def test_continuous_grid_encoding_dim_is_zero() -> None:
    assert _continuous2d().get_grid_encoding_dim() == 0


# --- position features (obs_position) ---------------------------------------


@pytest.mark.parametrize(("encoding", "expected"), [("relative", 2), ("scaled", 4), ("absolute", 2)])
def test_grid2d_position_feature_dim_matches_encoder(encoding: str, expected: int) -> None:
    """The DIV-003 'scaled' crash: the encoder emits 4 features, the compiler
    hardcoded 2. Declared width must equal the published width, per encoding."""
    substrate = _grid2d(encoding)
    produced = _published_position_features(substrate, _positions_for(substrate))
    assert produced is not None
    assert substrate.get_position_feature_dim() == produced.shape[1] == expected


@pytest.mark.parametrize(("encoding", "expected"), [("relative", 3), ("scaled", 6), ("absolute", 3)])
def test_grid3d_position_feature_dim_matches_encoder(encoding: str, expected: int) -> None:
    substrate = _grid3d(encoding)
    produced = _published_position_features(substrate, _positions_for(substrate))
    assert produced is not None
    assert substrate.get_position_feature_dim() == produced.shape[1] == expected


@pytest.mark.parametrize(("encoding", "expected"), [("relative", 4), ("scaled", 8), ("absolute", 4)])
def test_gridnd_position_feature_dim_matches_encoder(encoding: str, expected: int) -> None:
    substrate = _gridnd(encoding)
    produced = _published_position_features(substrate, _positions_for(substrate))
    assert produced is not None
    assert substrate.get_position_feature_dim() == produced.shape[1] == expected


@pytest.mark.parametrize("encoding", ["relative", "scaled", "absolute"])
def test_continuous_position_feature_dim_matches_encoder(encoding: str) -> None:
    substrate = _continuous2d(encoding)
    produced = _published_position_features(substrate, _positions_for(substrate))
    assert produced is not None
    assert substrate.get_position_feature_dim() == produced.shape[1] == substrate.get_observation_dim()


def test_aspatial_position_feature_dim_is_zero() -> None:
    assert AspatialSubstrate().get_position_feature_dim() == 0


# --- partial vision window (obs_local_window) --------------------------------


@pytest.mark.parametrize("radius", [1, 2, 3])
def test_grid2d_partial_window_dim_matches_encoder(radius: int) -> None:
    substrate = _grid2d()
    produced = substrate.encode_partial_observation(_positions_for(substrate), {}, vision_range=radius)
    assert substrate.supports_partial_vision
    assert substrate.get_partial_window_dim(radius) == produced.shape[1] == (2 * radius + 1) ** 2


@pytest.mark.parametrize("radius", [1, 2])
def test_grid3d_partial_window_dim_matches_encoder(radius: int) -> None:
    """The DIV-003 'cubic + partial' crash: the encoder emits a (2r+1)^3 cube,
    the compiler computed a 2-D window."""
    substrate = _grid3d()
    produced = substrate.encode_partial_observation(_positions_for(substrate), {}, vision_range=radius)
    assert substrate.supports_partial_vision
    assert substrate.get_partial_window_dim(radius) == produced.shape[1] == (2 * radius + 1) ** 3


def test_gridnd_does_not_support_partial_vision() -> None:
    assert not _gridnd().supports_partial_vision


def test_continuous_does_not_support_partial_vision() -> None:
    assert not _continuous2d().supports_partial_vision


def test_aspatial_does_not_support_partial_vision() -> None:
    assert not AspatialSubstrate().supports_partial_vision


# --- vision radius derivation ------------------------------------------------


def test_grid2d_vision_radius_matches_documented_l2_window() -> None:
    """vision_range=0.5 on 8x8 -> radius 2 -> the documented 5x5 window."""
    assert _grid2d().get_vision_radius(0.5) == 2


def test_grid2d_vision_radius_has_floor_of_one() -> None:
    """vision_range=0.0 must still yield radius 1, not 0 — ceil alone returns
    0 there (for any POSITIVE range ceil already gives >=1, so probing 0.0 is
    the only input that can catch a dropped floor; the first mutation battery
    proved a 0.01 probe cannot)."""
    assert _grid2d().get_vision_radius(0.0) == 1


def test_grid2d_rect_vision_radius_derives_from_longest_axis() -> None:
    """Non-square grids derive the radius from the longest axis, reducing to
    the historical grid_size/2 formula on squares."""
    assert _grid2d(width=8, height=6).get_vision_radius(0.5) == 2
    assert _grid2d(width=6, height=8).get_vision_radius(0.5) == 2


def test_grid3d_vision_radius_matches_pomdp_validation_pins() -> None:
    """0.5 -> radius 2 (window 5, accepted); 0.75 -> radius 3 (window 7,
    rejected by the env's 125-cell cap) — the exact pins in
    test_pomdp_validation.py."""
    substrate = _grid3d(depth=8)
    assert substrate.get_vision_radius(0.5) == 2
    assert substrate.get_vision_radius(0.75) == 3
