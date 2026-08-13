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


def test_default_matrix_declares_all_ten_cells() -> None:
    """CUDA duplicates of each cell are always declared — never absent from
    the matrix — so the harness can report them SKIPPED instead of silently
    omitting them when --cuda is not passed (spec: 'never silent')."""
    cells: tuple[Cell, ...] = default_cells()
    assert len(cells) == 10
    assert all(c.params.pack == "configs/default_curriculum" for c in cells)
    assert all(c.params.num_agents == 4 for c in cells)
    assert all(c.params.steps == 100 for c in cells)
    assert all(c.params.seed == 42 for c in cells)


def test_cpu_block_precedes_cuda_block() -> None:
    cells = default_cells()
    assert tuple(c.params.device for c in cells[:5]) == ("cpu",) * 5
    assert tuple(c.params.device for c in cells[5:]) == ("cuda",) * 5
    assert tuple(c.params.level for c in cells[:5]) == LEVELS
    assert tuple(c.params.level for c in cells[5:]) == LEVELS


def test_cell_id_is_unique_and_readable() -> None:
    cells = default_cells()
    ids = [c.cell_id for c in cells]
    assert len(set(ids)) == len(ids)
    assert "default_curriculum:L0_0_minimal:cpu:seed42" in ids
