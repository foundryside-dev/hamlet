"""Tests for normalization handling in UniverseCompiler."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME
from townlet.universe.compiler import UniverseCompiler


def _copy_experiment(tmp_path: Path) -> Path:
    source = Path("configs/test/model_config")
    dest = tmp_path / source.name
    shutil.copytree(source, dest)
    return dest


def test_standardize_maps_to_zscore_but_refuses_at_exposure(tmp_path: Path) -> None:
    """`standardize` still compiles to a `zscore` NormalizationSpec — and an
    `environment.yaml` variable declaring it now REFUSES.

    Both halves matter. The mapping is the DTO contract and is unchanged. The refusal is
    the unit-3 cut: `environment.yaml` variables are exposed by declaration (spec §2), and
    boundedness is certified at exposure (spec §1), so an unbounded kind cannot reach a
    token value lane. The consequence — recorded, not hidden — is that `standardize` is
    now unreachable from `environment.yaml` entirely; the surface survives for VFS
    variables that are NOT exposed.
    """
    from townlet.config.environment_config import NormalizationConfig
    from townlet.universe.compilers.observation import ObservationCompiler

    mean_value = 50.0
    std_value = 25.0

    spec = ObservationCompiler._convert_normalization(
        "time_since_last_eat",
        NormalizationConfig(method="standardize", range=[0.0, 100.0], mean=mean_value, std=std_value),
    )
    assert spec.kind == "zscore"
    assert spec.mean == mean_value
    assert spec.std == std_value

    config_dir = _copy_experiment(tmp_path)
    env_path = config_dir / "environment.yaml"
    env_data = yaml.safe_load(env_path.read_text())
    for var in env_data["environment"]["variables"]:
        if var["name"] == "time_since_last_eat":
            var["normalization"]["method"] = "standardize"
            # `clip` belongs to `normalize` and is forbidden on `standardize`, which has
            # no range to clamp against (hamlet-fba56feca5).
            var["normalization"].pop("clip", None)
            var["normalization"]["mean"] = mean_value
            var["normalization"]["std"] = std_value
    env_path.write_text(yaml.safe_dump(env_data))

    with pytest.raises(ValueError, match="bounded normalization kind"):
        UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
