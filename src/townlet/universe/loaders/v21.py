"""v2.1 config-pack loading entry points."""

from __future__ import annotations

from pathlib import Path

from townlet.universe.raw_configs_v21 import RawConfigsV21


def load_v21_configs(experiment_dir: Path) -> RawConfigsV21:
    """Load a strict v2.1 hierarchical config pack."""
    return RawConfigsV21.from_experiment_dir(experiment_dir)
