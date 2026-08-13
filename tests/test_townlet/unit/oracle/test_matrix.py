"""The declared comparison matrix — explicit cells, no discovery magic (WS-7)."""

from __future__ import annotations

from townlet.oracle.matrix import Cell, default_cells

LEVELS = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)


def test_default_matrix_is_the_five_levels_on_cpu() -> None:
    cells: tuple[Cell, ...] = default_cells()
    assert tuple(c.params.level for c in cells) == LEVELS
    assert all(c.params.device == "cpu" for c in cells)
    assert all(c.params.pack == "configs/default_curriculum" for c in cells)
    assert all(c.params.num_agents == 4 for c in cells)
    assert all(c.params.steps == 100 for c in cells)
    assert all(c.params.seed == 42 for c in cells)


def test_cuda_flag_appends_cuda_variants() -> None:
    cells = default_cells(include_cuda=True)
    assert len(cells) == 10
    cuda = [c for c in cells if c.params.device == "cuda"]
    assert tuple(c.params.level for c in cuda) == LEVELS


def test_cell_id_is_unique_and_readable() -> None:
    cells = default_cells(include_cuda=True)
    ids = [c.cell_id for c in cells]
    assert len(set(ids)) == len(ids)
    assert "default_curriculum:L0_0_minimal:cpu:seed42" in ids
