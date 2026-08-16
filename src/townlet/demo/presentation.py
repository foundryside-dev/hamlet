"""The observer's presentation surface (PDR-0025).

Two things the live-inference server forwards to a frontend so it can render a universe without
knowing what the game is:

- **Meter metadata** — derived from the compiled artifact: declared bounds, lethality, and the
  declared cascade edges, in compiled index order. This is what the honest default renders from.
  No meter is singled out by name here, and none may be downstream.
- **Presentation** — an optional pack-level ``presentation.yaml`` (``PresentationConfig``). Absent
  is the honest default. Present, it is validated against the compiled universe's meter and
  affordance names so a declaration for something that does not exist is a loud error, not a
  silently ignored key.

The universe compiler never reads ``presentation.yaml``; nothing here enters a compiled hash.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from townlet.config.presentation_config import PresentationConfig
from townlet.universe.compiled import CompiledUniverse

__all__ = [
    "PRESENTATION_FILENAME",
    "PresentationError",
    "build_meter_metadata",
    "load_presentation",
    "presentation_payload",
]

PRESENTATION_FILENAME = "presentation.yaml"


class PresentationError(ValueError):
    """A ``presentation.yaml`` that cannot be honoured — malformed, or naming things the universe lacks."""


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


def load_presentation(config_dir: Path, universe: CompiledUniverse) -> PresentationConfig | None:
    """Read ``<config_dir>/presentation.yaml`` if present; ``None`` is the honest default.

    Raises ``PresentationError`` if the file is malformed or names a meter/affordance the compiled
    universe does not declare.
    """
    path = Path(config_dir) / PRESENTATION_FILENAME
    if not path.exists():
        return None

    try:
        raw = yaml.safe_load(path.read_text())
        config = PresentationConfig.model_validate(raw)
    except (yaml.YAMLError, ValidationError) as exc:
        raise PresentationError(f"{path}: {exc}") from exc

    level = universe.get_level(universe.metadata.primary_level)
    meter_names = {info.name for info in level.meter_metadata.meters}
    affordance_names = {info.name for info in level.affordance_metadata.affordances}
    unknown_meters = sorted(set(config.meters) - meter_names)
    unknown_affordances = sorted(set(config.affordances) - affordance_names)
    if unknown_meters or unknown_affordances:
        parts = []
        if unknown_meters:
            parts.append(f"meters {unknown_meters} (declared meters: {sorted(meter_names)})")
        if unknown_affordances:
            parts.append(f"affordances {unknown_affordances} (declared affordances: {sorted(affordance_names)})")
        raise PresentationError(f"{path} declares presentation for undeclared " + " and ".join(parts))
    return config


def presentation_payload(config: PresentationConfig | None) -> dict[str, Any] | None:
    """JSON-ready form of a loaded presentation, or ``None`` when the pack declares none."""
    if config is None:
        return None
    return {
        "meters": {name: entry.model_dump(mode="json") for name, entry in config.meters.items()},
        "affordances": {name: entry.model_dump(mode="json") for name, entry in config.affordances.items()},
    }
