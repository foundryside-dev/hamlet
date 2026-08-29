"""Compile-path validation tests for UniverseCompiler."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError


def _copy_experiment(tmp_path: Path) -> Path:
    source = Path("configs/test/model_config")
    dest = tmp_path / source.name
    shutil.copytree(source, dest)
    return dest


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def test_compile_rejects_nonexistent_config_path(tmp_path: Path) -> None:
    with pytest.raises(CompilationError, match="does not exist"):
        UniverseCompiler().compile(tmp_path / "missing", primary_level="L0_test", use_cache=False)


def test_compile_rejects_file_path(tmp_path: Path) -> None:
    file_path = tmp_path / "not-a-config-pack.yaml"
    file_path.write_text("version: 2.1\n")

    with pytest.raises(CompilationError, match="not a directory"):
        UniverseCompiler().compile(file_path, primary_level="L0_test", use_cache=False)


def test_compile_rejects_invalid_yaml_in_level_file(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    (config_dir / "levels" / "L0_test" / "curriculum.yaml").write_text("invalid: [yaml: syntax")

    with pytest.raises(CompilationError, match="Stage 0: Preflight validation"):
        UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=False)


def test_compile_rejects_grid_capacity_exceeded(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    stratum_path = config_dir / "stratum.yaml"
    stratum = _load_yaml(stratum_path)
    stratum["stratum"]["substrate"]["grid"]["width"] = 2
    stratum["stratum"]["substrate"]["grid"]["height"] = 2
    _write_yaml(stratum_path, stratum)

    with pytest.raises((CompilationError, ValueError), match="Grid capacity exceeded"):
        UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=False)


def test_compile_rejects_unknown_enabled_affordance(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    training_path = config_dir / "levels" / "L0_test" / "training.yaml"
    training = _load_yaml(training_path)
    training["training"]["enabled_affordances"].append("BOGUS_JOB")
    _write_yaml(training_path, training)

    with pytest.raises((CompilationError, ValueError), match="Invalid enabled_affordances"):
        UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=False)


def test_compile_rejects_affordance_missing_opening_hours(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    affordances_path = config_dir / "levels" / "L0_test" / "affordances.yaml"
    affordances = _load_yaml(affordances_path)
    affordances["affordances"]["affordances"][0].pop("opening_hours")
    _write_yaml(affordances_path, affordances)

    with pytest.raises(CompilationError, match="opening_hours"):
        UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=False)


def test_compile_accepts_valid_v21_config_pack(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)

    compiled = UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=False)

    assert compiled.metadata.universe_name == "Model Config (Test)"
    assert compiled.available_levels == ["L0_test"]
