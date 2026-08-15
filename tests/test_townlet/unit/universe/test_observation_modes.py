from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from townlet.config.stratum_config import ObservationModeConfig, StratumConfig
from townlet.universe.compilers.observation import ObservationCompiler
from townlet.universe.dto import ObservationField


def _field(
    name: str,
    dims: int = 2,
    description: str | None = None,
    curriculum_active: bool = True,
) -> ObservationField:
    return ObservationField(
        uuid=None,
        name=name,
        type="vector",
        dims=dims,
        start_index=0,
        end_index=dims,
        scope="agent",
        description=description,
        semantic_type="custom",
        curriculum_active=curriculum_active,
    )


def test_full_auto_keeps_fields():
    fields = [_field("a"), _field("b")]
    mode = ObservationModeConfig(mode="full_auto")
    out = ObservationCompiler._apply_observation_mode(fields, mode)
    assert [f.name for f in out] == ["a", "b"]


def test_max_compact_drops_masked_fields():
    fields = [_field("keep"), _field("drop", description="Inactive field", curriculum_active=False)]
    mode = ObservationModeConfig(mode="max_compact")
    out = ObservationCompiler._apply_observation_mode(fields, mode)
    assert [f.name for f in out] == ["keep"]


def test_full_manual_requires_known_fields():
    fields = [_field("x"), _field("y")]
    mode = ObservationModeConfig(mode="full_manual", include_fields=["x"])
    out = ObservationCompiler._apply_observation_mode(fields, mode)
    assert [f.name for f in out] == ["x"]

    reorder = ObservationModeConfig(mode="full_manual", include_fields=["y", "x"])
    reordered = ObservationCompiler._apply_observation_mode(fields, reorder)
    assert [f.name for f in reordered] == ["y", "x"]

    bad_mode = ObservationModeConfig(mode="full_manual", include_fields=["z"])
    with pytest.raises(ValueError):
        ObservationCompiler._apply_observation_mode(fields, bad_mode)


def test_full_manual_requires_non_empty():
    with pytest.raises(ValueError):
        ObservationModeConfig(mode="full_manual", include_fields=[])


def test_stratum_requires_observation_mode() -> None:
    data = yaml.safe_load(Path("configs/test/model_config/stratum.yaml").read_text())
    del data["stratum"]["observation_mode"]

    with pytest.raises(ValidationError, match="observation_mode"):
        StratumConfig.model_validate(data)
