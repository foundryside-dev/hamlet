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




# --- grid encoding (obs_grid_encoding) --------------------------------------














# --- position features (obs_position) ---------------------------------------












# --- partial vision window (obs_local_window) --------------------------------






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
