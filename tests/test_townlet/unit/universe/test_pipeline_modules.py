"""Direct tests for extracted universe compiler stage modules."""

from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from townlet.universe.errors import CompilationError
from townlet.universe.loaders.preflight import validate_scoping
from townlet.universe.loaders.v21 import load_v21_configs
from townlet.universe.pipeline import LoadedConfigBundle, ResolvedConfigBundle
from townlet.universe.validation.feasibility import grid_capacity_for_substrate
from townlet.universe.validation.references import build_symbol_table, resolve_references
from townlet.universe.validation.semantics import select_primary_level


def _copy_experiment(tmp_path: Path) -> Path:
    source = Path("configs/test/model_config")
    dest = tmp_path / source.name
    shutil.copytree(source, dest)
    return dest


def test_load_v21_configs_returns_typed_bundle(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)

    bundle = load_v21_configs(config_dir)

    assert isinstance(bundle, LoadedConfigBundle)
    assert "L0_test" in bundle.raw.levels


def test_resolve_references_returns_typed_bundle(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    raw = load_v21_configs(config_dir).raw
    symbol_table = build_symbol_table(raw)

    bundle = resolve_references(raw, symbol_table, config_dir)

    assert isinstance(bundle, ResolvedConfigBundle)
    assert bundle.raw is raw
    assert bundle.symbol_table is symbol_table


def test_preflight_rejects_level_directory_directly(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)

    with pytest.raises(CompilationError, match="Cannot validate level directory directly"):
        validate_scoping(config_dir / "levels" / "L0_test")


def test_select_primary_level_rejects_unknown_level() -> None:
    levels = {"L0_test": object()}

    with pytest.raises(ValueError, match="Primary level 'missing' not found"):
        select_primary_level(levels, "missing")


def test_grid_capacity_for_gridnd_substrate() -> None:
    substrate = SimpleNamespace(type="gridnd", gridnd=SimpleNamespace(dimension_sizes=[2, 3, 5]))

    assert grid_capacity_for_substrate(substrate) == 30
