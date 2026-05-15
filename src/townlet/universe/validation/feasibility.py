"""Reusable feasibility checks for universe validation passes."""

from __future__ import annotations

from typing import Any


def grid_capacity_for_substrate(substrate: Any) -> int | None:
    """Return finite grid capacity for grid-like substrates, otherwise None."""
    grid_config = getattr(substrate, "grid", None)
    if getattr(substrate, "type", None) == "grid" and grid_config is not None:
        width = int(grid_config.width)
        height = int(grid_config.height)
        depth = getattr(grid_config, "depth", None)
        return width * height if depth is None else width * height * int(depth)

    gridnd_config = getattr(substrate, "gridnd", None)
    if getattr(substrate, "type", None) == "gridnd" and gridnd_config is not None:
        capacity = 1
        for size in gridnd_config.dimension_sizes:
            capacity *= int(size)
        return capacity

    return None
