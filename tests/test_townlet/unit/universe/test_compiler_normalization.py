"""Tests for normalization handling in UniverseCompiler."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from townlet.universe.compiler import UniverseCompiler


def _copy_experiment(tmp_path: Path) -> Path:
    source = Path("configs/test/model_config")
    dest = tmp_path / source.name
    shutil.copytree(source, dest)
    return dest


def test_standardize_normalization_maps_to_zscore(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)

    env_path = config_dir / "environment.yaml"
    env_data = yaml.safe_load(env_path.read_text())

    for var in env_data["environment"]["variables"]:
        if var["name"] == "time_since_last_eat":
            var["normalization"]["method"] = "standardize"

    env_path.write_text(yaml.safe_dump(env_data))

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, use_cache=False)

    target_var = next(v for v in compiled.vfs_variables if v.id == "time_since_last_eat")
    target_field = next(f for f in compiled.vfs_observation_fields if f.id == "time_since_last_eat")

    assert target_var.normalization is not None
    assert target_var.normalization.kind == "zscore"
    assert target_field.normalization is not None
    assert target_field.normalization.kind == "zscore"
