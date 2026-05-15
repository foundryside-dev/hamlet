"""v2.1 config-pack loading entry points."""

from __future__ import annotations

from pathlib import Path

from townlet.universe.pipeline import LoadedConfigBundle
from townlet.universe.raw_configs_v21 import RawConfigsV21


def load_v21_configs(experiment_dir: Path) -> LoadedConfigBundle:
    """Load a strict v2.1 hierarchical config pack."""
    return LoadedConfigBundle(raw=RawConfigsV21.from_experiment_dir(experiment_dir))
