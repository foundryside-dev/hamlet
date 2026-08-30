"""Substrate visibility / egocentric contract (token-obs unit 3, Task 8).

The two-member contract addition (`visible`, `egocentric_delta`) follows the PDR-0041
five-member-contract precedent: the compiler and runtime learn spatial-token visibility by
asking the substrate instance, and each substrate's answer is parity-pinned here per
boundary mode. Spec: token-observation design §3 (visibility filter, egocentric features).

Semantics pinned:

- ``visible(self_pos [N, D], entity_pos [M, D], vision_range) -> [N, M] bool`` under the
  DECLARED distance metric and boundary mode. `vision_range=None` = full observability =
  pass-all. `vision_range` keeps its POMDP meaning: a normalized fraction of the longest
  axis, converted to a radius by the substrate.
- Only `wrap` changes distance semantics (toroidal shortest path). clamp / bounce / sticky
  are in-bounds position regimes: distance is the plain declared metric — pinned by the
  boundary-mode table tests.
- ``egocentric_delta(self_pos [N, D], entity_pos [M, D]) -> [N, M, D] float32`` =
  entity − self, shortest path under wrap, divided by the same axis span as
  ``normalize_positions`` and therefore bounded to [−1, 1].
- GridND thereby gains partial observability (rank ≤ MAX_POSITION_RANK — the §1 trade);
  Aspatial: visible = all, delta = zeros (width 0).
"""

import pytest
import torch

from townlet.substrate.aspatial import AspatialSubstrate
from townlet.substrate.continuous import ContinuousSubstrate
from townlet.substrate.continuousnd import ContinuousNDSubstrate
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.substrate.grid3d import Grid3DSubstrate
from townlet.substrate.gridnd import GridNDSubstrate

BOUNDARIES = ("clamp", "wrap", "bounce", "sticky")


def _grid2d(boundary: str, *, metric: str = "manhattan") -> Grid2DSubstrate:
    return Grid2DSubstrate(width=8, height=8, boundary=boundary, distance_metric=metric)


def _grid3d(boundary: str, *, metric: str = "manhattan") -> Grid3DSubstrate:
    return Grid3DSubstrate(width=8, height=8, depth=3, boundary=boundary, distance_metric=metric)


def _gridnd(boundary: str, *, metric: str = "manhattan") -> GridNDSubstrate:
    return GridNDSubstrate(dimension_sizes=[5, 5, 5, 5], boundary=boundary, distance_metric=metric)


def _continuous(boundary: str, *, metric: str = "euclidean") -> ContinuousSubstrate:
    return ContinuousSubstrate(
        dimensions=2,
        bounds=[(0.0, 10.0), (0.0, 10.0)],
        boundary=boundary,
        movement_delta=0.5,
        interaction_radius=1.0,
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
        distance_metric=metric,
    )


def _continuousnd(boundary: str) -> ContinuousNDSubstrate:
    return ContinuousNDSubstrate(
        bounds=[(0.0, 10.0)] * 4,
        boundary=boundary,
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
    )


class TestVisibleShapesAndFullObservability:
    @pytest.mark.parametrize("boundary", BOUNDARIES)
    def test_none_vision_range_is_pass_all_grid2d(self, boundary):
        substrate = _grid2d(boundary)
        self_pos = torch.tensor([[0, 0], [7, 7]], dtype=torch.long)
        entity_pos = torch.tensor([[3, 3], [0, 7], [7, 0]], dtype=torch.long)
        vis = substrate.visible(self_pos, entity_pos, None)
        assert vis.shape == (2, 3)
        assert vis.dtype == torch.bool
        assert vis.all()

    def test_dimension_mismatch_refuses(self):
        substrate = _grid2d("clamp")
        with pytest.raises(ValueError, match="position_dim"):
            substrate.visible(torch.zeros((1, 3), dtype=torch.long), torch.zeros((1, 2), dtype=torch.long), None)
        with pytest.raises(ValueError, match="position_dim"):
            substrate.egocentric_delta(torch.zeros((1, 2), dtype=torch.long), torch.zeros((1, 3), dtype=torch.long))


class TestGrid2DBoundaryModeTable:
    """The per-substrate boundary-mode table: wrap is toroidal, the rest are plain metric."""

    # vision_range 0.5 on an 8-wide grid -> radius ceil(0.5 * 8/2) = 2 cells.
    RANGE = 0.5

    @pytest.mark.parametrize("boundary", ("clamp", "bounce", "sticky"))
    def test_non_wrap_corner_to_corner_invisible(self, boundary):
        substrate = _grid2d(boundary)
        vis = substrate.visible(torch.tensor([[0, 0]]), torch.tensor([[7, 0], [2, 0], [3, 0]]), self.RANGE)
        assert vis.tolist() == [[False, True, False]]

    def test_wrap_corner_to_corner_visible(self):
        substrate = _grid2d("wrap")
        # |0-7| = 7 plain, but 1 around the torus: inside radius 2.
        vis = substrate.visible(torch.tensor([[0, 0]]), torch.tensor([[7, 0], [4, 0]]), self.RANGE)
        assert vis.tolist() == [[True, False]]

    def test_metric_is_declared_not_assumed(self):
        # Diagonal at (2, 2): manhattan distance 4 > 2, chebyshev distance 2 <= 2.
        manhattan = _grid2d("clamp", metric="manhattan")
        chebyshev = _grid2d("clamp", metric="chebyshev")
        self_pos = torch.tensor([[0, 0]])
        entity = torch.tensor([[2, 2]])
        assert manhattan.visible(self_pos, entity, self.RANGE).tolist() == [[False]]
        assert chebyshev.visible(self_pos, entity, self.RANGE).tolist() == [[True]]

    def test_euclidean_metric(self):
        euclid = _grid2d("clamp", metric="euclidean")
        # (2, 2) -> sqrt(8) ~ 2.83 > 2; (1, 1) -> sqrt(2) ~ 1.41 <= 2.
        vis = euclid.visible(torch.tensor([[0, 0]]), torch.tensor([[2, 2], [1, 1]]), self.RANGE)
        assert vis.tolist() == [[False, True]]

    @pytest.mark.parametrize("boundary", ("clamp", "bounce", "sticky"))
    def test_non_wrap_egocentric_is_bounded(self, boundary):
        substrate = _grid2d(boundary)
        delta = substrate.egocentric_delta(torch.tensor([[0, 0]]), torch.tensor([[7, 3]]))
        assert delta.shape == (1, 1, 2)
        assert delta.dtype == torch.float32
        assert delta[0, 0].tolist() == pytest.approx([1.0, 3.0 / 7.0])

    def test_wrap_egocentric_is_shortest_path(self):
        substrate = _grid2d("wrap")
        # entity at x=7 seen from x=0 on width 8: shortest signed path is -1, not +7.
        delta = substrate.egocentric_delta(torch.tensor([[0, 0]]), torch.tensor([[7, 3]]))
        assert delta[0, 0].tolist() == pytest.approx([-1.0 / 7.0, 3.0 / 7.0])


class TestGrid3DBoundaryModeTable:
    @pytest.mark.parametrize("boundary", ("clamp", "bounce", "sticky"))
    def test_non_wrap_far_z_invisible(self, boundary):
        substrate = _grid3d(boundary)
        # radius = ceil(0.5 * max(8,8,3)/2) = 2
        vis = substrate.visible(torch.tensor([[0, 0, 0]]), torch.tensor([[0, 7, 0], [0, 2, 0]]), 0.5)
        assert vis.tolist() == [[False, True]]

    def test_wrap_shortest_path_visible(self):
        substrate = _grid3d("wrap")
        vis = substrate.visible(torch.tensor([[0, 0, 0]]), torch.tensor([[0, 7, 0]]), 0.5)
        assert vis.tolist() == [[True]]

    def test_wrap_egocentric_wraps_every_axis(self):
        substrate = _grid3d("wrap")
        delta = substrate.egocentric_delta(torch.tensor([[0, 0, 0]]), torch.tensor([[7, 7, 2]]))
        # relative encoding: -1 cell / span 7, -1 / 7, -1 cell on depth / span 2.
        assert delta[0, 0].tolist() == pytest.approx([-1.0 / 7.0, -1.0 / 7.0, -1.0 / 2.0])


class TestGridNDGainsPartialObservability:
    """The §1 trade: GridND (rank <= MAX_POSITION_RANK) becomes visibility-filterable even
    though its raster local-window path never existed (`supports_partial_vision` stays
    False — that is the OLD window contract, untouched)."""

    def test_supports_partial_vision_unchanged(self):
        assert _gridnd("clamp").supports_partial_vision is False

    @pytest.mark.parametrize("boundary", ("clamp", "bounce", "sticky"))
    def test_non_wrap_table(self, boundary):
        substrate = _gridnd(boundary)
        # radius = ceil(0.5 * 5/2) = 2 (longest-axis formula, identical to grid2d/3d).
        self_pos = torch.tensor([[0, 0, 0, 0]])
        entities = torch.tensor([[4, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 0]])
        assert substrate.visible(self_pos, entities, 0.5).tolist() == [[False, True, False]]

    def test_wrap_table(self):
        substrate = _gridnd("wrap")
        self_pos = torch.tensor([[0, 0, 0, 0]])
        entities = torch.tensor([[4, 0, 0, 0], [4, 4, 0, 0]])
        # |0-4| = 4 plain but 1 on the 5-torus -> manhattan 1 and 2.
        assert substrate.visible(self_pos, entities, 0.5).tolist() == [[True, True]]

    def test_wrap_egocentric(self):
        substrate = _gridnd("wrap")
        delta = substrate.egocentric_delta(torch.tensor([[0, 0, 0, 0]]), torch.tensor([[4, 3, 0, 0]]))
        # relative: -1/4 (wrap), 3 -> shortest is -2 on a 5-torus -> -2/4.
        assert delta[0, 0].tolist() == pytest.approx([-0.25, -0.5, 0.0, 0.0])


class TestContinuousBoundaryModeTable:
    @pytest.mark.parametrize("boundary", ("clamp", "bounce", "sticky"))
    def test_non_wrap_table(self, boundary):
        substrate = _continuous(boundary)
        # radius = 0.5 * 10/2 = 2.5 world units.
        self_pos = torch.tensor([[0.0, 0.0]])
        entities = torch.tensor([[9.0, 0.0], [2.0, 1.0]])
        assert substrate.visible(self_pos, entities, 0.5).tolist() == [[False, True]]

    def test_wrap_table(self):
        substrate = _continuous("wrap")
        self_pos = torch.tensor([[0.0, 0.0]])
        entities = torch.tensor([[9.0, 0.0], [5.0, 0.0]])
        # 9.0 is 1.0 around the 10-torus; 5.0 is 5.0 either way.
        assert substrate.visible(self_pos, entities, 0.5).tolist() == [[True, False]]

    def test_wrap_egocentric_shortest_path(self):
        substrate = _continuous("wrap")
        delta = substrate.egocentric_delta(torch.tensor([[0.0, 0.0]]), torch.tensor([[9.0, 3.0]]))
        assert delta[0, 0].tolist() == pytest.approx([-0.1, 0.3])

    def test_egocentric_delta_normalizes_by_extent(self):
        substrate = _continuous("clamp")
        delta = substrate.egocentric_delta(torch.tensor([[0.0, 0.0]]), torch.tensor([[9.0, 3.0]]))
        assert delta[0, 0].tolist() == pytest.approx([0.9, 0.3])

    @pytest.mark.parametrize("boundary", BOUNDARIES)
    def test_continuousnd_table(self, boundary):
        # ContinuousND's visible/egocentric bodies are DUPLICATED from Continuous, not
        # inherited, so all four boundary modes get their own rows here (review
        # Important-1): only wrap changes semantics; clamp/bounce/sticky are plain
        # metric distance.
        substrate = _continuousnd(boundary)
        self_pos = torch.zeros((1, 4))
        entity = torch.tensor([[9.0, 0.0, 0.0, 0.0]])
        vis = substrate.visible(self_pos, entity, 0.5)
        assert vis.tolist() == [[boundary == "wrap"]]

    @pytest.mark.parametrize("boundary", ("clamp", "bounce", "sticky"))
    def test_continuousnd_non_wrap_egocentric_is_plain_difference(self, boundary):
        substrate = _continuousnd(boundary)
        delta = substrate.egocentric_delta(torch.zeros((1, 4)), torch.tensor([[9.0, 3.0, 0.0, 0.0]]))
        # relative encoding normalizes by extent (10.0) with no wrap folding.
        assert delta[0, 0].tolist() == pytest.approx([0.9, 0.3, 0.0, 0.0])

    def test_continuousnd_wrap_egocentric_shortest_path(self):
        substrate = _continuousnd("wrap")
        delta = substrate.egocentric_delta(torch.zeros((1, 4)), torch.tensor([[9.0, 3.0, 0.0, 0.0]]))
        assert delta[0, 0].tolist() == pytest.approx([-0.1, 0.3, 0.0, 0.0])


class TestAspatial:
    def test_visible_is_all(self):
        substrate = AspatialSubstrate()
        self_pos = torch.zeros((3, 0))
        entity_pos = torch.zeros((2, 0))
        vis = substrate.visible(self_pos, entity_pos, 0.1)
        assert vis.shape == (3, 2)
        assert vis.dtype == torch.bool
        assert vis.all()

    def test_egocentric_delta_is_zero_width(self):
        substrate = AspatialSubstrate()
        delta = substrate.egocentric_delta(torch.zeros((3, 0)), torch.zeros((2, 0)))
        assert delta.shape == (3, 2, 0)
        assert delta.dtype == torch.float32


class TestWrapTieBreak:
    def test_even_extent_half_span_is_deterministic(self):
        # On an 8-torus, |0-4| is 4 both ways; the shortest-path convention maps the tie
        # to the NEGATIVE half-span deterministically (remainder arithmetic).
        substrate = _grid2d("wrap")
        delta = substrate.egocentric_delta(torch.tensor([[0, 0]]), torch.tensor([[4, 0]]))
        assert delta[0, 0, 0].item() == pytest.approx(-4.0 / 7.0)


class TestVisibleZeroEntities:
    def test_empty_entity_set(self):
        substrate = _grid2d("clamp")
        vis = substrate.visible(torch.tensor([[0, 0]]), torch.zeros((0, 2), dtype=torch.long), 0.5)
        assert vis.shape == (1, 0)
        delta = substrate.egocentric_delta(torch.tensor([[0, 0]]), torch.zeros((0, 2), dtype=torch.long))
        assert delta.shape == (1, 0, 2)
