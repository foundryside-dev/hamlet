"""Closed authoring shapes must refuse before coercion or helper traversal."""

import shutil
from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.universe.raw_configs_v21 import RawConfigsV21


@pytest.fixture
def pack(tmp_path: Path) -> Path:
    target = tmp_path / "pack"
    source = Path(__file__).parents[4] / "configs" / "test" / "model_config"
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(".compiled"))
    return target


@pytest.mark.parametrize(
    "payload",
    [
        "variables: {}\nthis_is_a_typo: 10\n",
        "variables: [oops]\n",
        "variables: {bad: 1}\n",
        "variables: {version: '1.0', evaluation_mode: eager, debug_logging: false, extents: 7, item_profiles: [], declarations: []}\n",
    ],
)
def test_canonical_variable_bad_shapes_are_structured(pack: Path, payload: str) -> None:
    origin = pack / "variables.yaml"
    origin.write_text(payload)
    with pytest.raises(CompilationError) as caught:
        RawConfigsV21.from_experiment_dir(pack)
    assert str(origin) in str(caught.value)
    expected_code = "DECLARATION_UNKNOWN" if "this_is_a_typo" in payload else "LOAD_ERROR"
    assert expected_code in str(caught.value)


def test_numeric_label_collision_is_refused_before_coercion(pack: Path) -> None:
    origin = pack / "labels.yml"
    origin.write_text('custom:\n  "1": first\n  1: second\n')
    with pytest.raises(CompilationError) as caught:
        RawConfigsV21.from_experiment_dir(pack)
    assert f"{origin}:2" in str(caught.value)
    assert f"{origin}:3" in str(caught.value)


def test_labels_have_one_explicit_integer_identifier_shape(pack: Path) -> None:
    origin = pack / "labels.yml"
    origin.write_text('custom:\n  "1": first\n')
    with pytest.raises(CompilationError):
        RawConfigsV21.from_experiment_dir(pack)


def test_integer_labels_are_consumed(pack: Path) -> None:
    (pack / "labels.yml").write_text("custom:\n  1: first\n")
    assert RawConfigsV21.from_experiment_dir(pack).action_label_overrides == {1: "first"}


@pytest.mark.parametrize("exists", [False, True])
def test_preflight_path_refusals_have_source_and_code(tmp_path: Path, exists: bool) -> None:
    origin = tmp_path / "invalid_pack"
    if exists:
        origin.write_text("file, not a pack directory")
    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(origin, primary_level="L0_test", use_cache=False)
    assert all(issue.code == "CONFIG_PATH_INVALID" and issue.location == f"{origin}:1" for issue in caught.value.issues)
