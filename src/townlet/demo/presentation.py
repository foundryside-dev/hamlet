"""The observer's presentation surface (PDR-0025).

Two things the live-inference server forwards to a frontend so it can render a universe without
knowing what the game is:

- **Meter metadata** — derived from the compiled artifact: declared bounds, lethality, and the
  declared cascade edges, in compiled index order. This is what the honest default renders from.
  No meter is singled out by name here, and none may be downstream.
- **Presentation** — the pack's optional ``presentation`` declaration (``PresentationConfig``),
  carried on the compiled artifact as ``CompiledUniverse.presentation``. Absent is the honest
  default. The compiler resolves its meter and affordance references at compile time
  (``[UAC-RES-PRESENTATION]``), so nothing here re-reads a file or re-checks a name: there is
  one vocabulary, and the observer reads what the compiler emitted.

Presentation enters no compiled hash and no checkpoint gate.
"""

from __future__ import annotations

from typing import Any

from townlet.config.presentation_config import PresentationConfig
from townlet.universe.compiled import CompiledUniverse

__all__ = [
    "build_meter_metadata",
    "presentation_payload",
]


def build_meter_metadata(universe: CompiledUniverse) -> list[dict[str, Any]]:
    """Per-meter rendering facts, from declarations only, in compiled index order.

    Each row: ``name, index, bounds{min,max}, lethal_min, lethal_max, cascades_to, cascades_from``.
    Cascade lists preserve ``bars.yaml`` declaration order.
    """
    level = universe.get_level(universe.metadata.primary_level)
    bars = level.bars
    by_name = {meter.name: meter for meter in bars.meters}
    cascades_to: dict[str, list[str]] = {name: [] for name in by_name}
    cascades_from: dict[str, list[str]] = {name: [] for name in by_name}
    for cascade in bars.cascades:
        cascades_to[cascade.source].append(cascade.target)
        cascades_from[cascade.target].append(cascade.source)

    rows: list[dict[str, Any]] = []
    for info in level.meter_metadata.meters:
        declared = by_name[info.name]
        rows.append(
            {
                "name": info.name,
                "index": info.index,
                "bounds": {"min": declared.bounds.min, "max": declared.bounds.max},
                "lethal_min": declared.bounds.lethal_min,
                "lethal_max": declared.bounds.lethal_max,
                "cascades_to": list(cascades_to[info.name]),
                "cascades_from": list(cascades_from[info.name]),
            }
        )
    rows.sort(key=lambda row: row["index"])
    return rows


def presentation_payload(config: PresentationConfig | None) -> dict[str, Any] | None:
    """JSON-ready form of the compiled presentation, or ``None`` when the pack declares none."""
    if config is None:
        return None
    return {
        "meters": {name: entry.model_dump(mode="json") for name, entry in config.meters.items()},
        "affordances": {name: entry.model_dump(mode="json") for name, entry in config.affordances.items()},
    }
