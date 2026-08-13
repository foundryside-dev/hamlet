"""The declared comparison matrix.

Cells are DECLARED, not discovered — per the no-defaults principle, every
parameter of every cell is explicit here. The five default_curriculum levels
are three distinct universes (PDR-0018); all five are cells anyway, because
the harness compares runtimes, not curricula.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from townlet.oracle.trace_io import RunParams

_DEFAULT_PACK = "configs/default_curriculum"
_DEFAULT_LEVELS = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)


@dataclass(frozen=True)
class Cell:
    params: RunParams

    @property
    def cell_id(self) -> str:
        p = self.params
        return f"{Path(p.pack).name}:{p.level}:{p.device}:seed{p.seed}"


def default_cells() -> tuple[Cell, ...]:
    """The full declared matrix: all 5 levels on cpu, then all 5 on cuda.

    CUDA cells are always declared, never conditionally omitted — per spec,
    the RUN decision (whether to actually execute them) belongs to the
    harness, which reports them SKIPPED when --cuda is not passed. A matrix
    that drops CUDA cells entirely without the flag would make that skip
    silent instead of reported.
    """
    return tuple(
        Cell(
            RunParams(
                pack=_DEFAULT_PACK,
                level=level,
                num_agents=4,
                steps=100,
                seed=42,
                device=device,
            )
        )
        for device in ("cpu", "cuda")
        for level in _DEFAULT_LEVELS
    )
