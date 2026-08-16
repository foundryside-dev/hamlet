"""Tests for normalization handling in UniverseCompiler."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME
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

    mean_value = 50.0
    std_value = 25.0

    for var in env_data["environment"]["variables"]:
        if var["name"] == "time_since_last_eat":
            var["normalization"]["method"] = "standardize"
            # `clip` belongs to `normalize` and is forbidden on `standardize`,
            # which has no range to clamp against (hamlet-fba56feca5). Leaving
            # it behind is rejected rather than ignored — that rejection is the
            # point, so drop it here as a real author would.
            var["normalization"].pop("clip", None)
            var["normalization"]["mean"] = mean_value
            var["normalization"]["std"] = std_value

    env_path.write_text(yaml.safe_dump(env_data))

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    target_var = next(v for v in compiled.vfs_variables if v.id == "time_since_last_eat")
    target_field = next(f for f in compiled.vfs_observation_fields if f.id == "time_since_last_eat")

    assert target_var.normalization is not None
    assert target_var.normalization.kind == "zscore"
    assert target_var.normalization.mean == mean_value
    assert target_var.normalization.std == std_value
    assert target_field.normalization is not None
    assert target_field.normalization.kind == "zscore"
    assert target_field.normalization.mean == mean_value
    assert target_field.normalization.std == std_value
