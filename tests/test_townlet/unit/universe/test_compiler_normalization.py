"""Canonical variable normalization refuses incompatible authoring and exposure."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError


def _copy_experiment(tmp_path: Path) -> Path:
    source = Path("configs/test/model_config")
    dest = tmp_path / source.name
    shutil.copytree(source, dest)
    return dest


def test_unbounded_zscore_refuses_at_exposure(tmp_path: Path) -> None:
    """Normalization is authored directly; exposed values require bounded encoding."""
    config_dir = _copy_experiment(tmp_path)
    path = config_dir / "variables.yaml"
    data = yaml.safe_load(path.read_text())
    variable = next(var for var in data["variables"]["declarations"] if var["id"] == "time_since_last_eat")
    variable["normalization"] = {"kind": "zscore", "mean": 50.0, "std": 25.0}
    path.write_text(yaml.safe_dump(data))
    with pytest.raises((ValueError, CompilationError), match="bounded normalization kind"):
        UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)


def test_old_normalization_method_shape_refuses_with_source(tmp_path: Path) -> None:
    """The removed method/range authoring DTO has no compatibility conversion."""
    config_dir = _copy_experiment(tmp_path)
    path = config_dir / "variables.yaml"
    data = yaml.safe_load(path.read_text())
    variable = next(var for var in data["variables"]["declarations"] if var["id"] == "time_since_last_eat")
    variable["normalization"] = {"method": "standardize", "range": [0.0, 100.0], "mean": 50.0, "std": 25.0}
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    assert str(path) in str(caught.value)
