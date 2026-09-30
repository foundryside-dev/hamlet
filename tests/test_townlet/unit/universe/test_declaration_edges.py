"""Author mistakes and fragmented catalogs retain precise declaration origins."""

import shutil
from pathlib import Path

import pytest
import yaml

from townlet.config.bars_v2_config import BarsV2Config
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.declarations import DeclarationStore
from townlet.universe.errors import CompilationError
from townlet.universe.raw_configs_v21 import RawConfigsV21


@pytest.fixture
def pack(tmp_path: Path) -> Path:
    root = tmp_path / "pack"
    shutil.copytree("configs/default_curriculum", root, ignore=shutil.ignore_patterns(".compiled"))
    return root


@pytest.mark.parametrize("field", ["profile", "variable", "expression", "normalization"])
def test_malformed_clock_shapes_are_structured(pack: Path, field: str) -> None:
    path = pack / "vfs_profiles.yaml"
    data = yaml.safe_load(path.read_text())
    if field == "profile":
        data["global_profile"] = ["oops"]
    elif field == "variable":
        data["global_profile"]["variables"] = ["oops"]
    else:
        data["global_profile"]["variables"][0][field] = 1 if field == "expression" else ["oops"]
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    with pytest.raises(CompilationError) as caught:
        RawConfigsV21.from_experiment_dir(pack)
    assert str(path) in str(caught.value)


def test_optional_catalog_can_be_absent(pack: Path) -> None:
    (pack / "items.yaml").unlink()
    assert RawConfigsV21.from_experiment_dir(pack).items is None


@pytest.mark.parametrize("invalid_fragment", [0, 1])
def test_merged_array_validation_points_to_original_field(pack: Path, invalid_fragment: int) -> None:
    directory = pack / "levels" / "L0_0_minimal"
    source = directory / "bars.yaml"
    data = yaml.safe_load(source.read_text())["bars"]
    paths = [source, directory / "z_bars.yml"]
    fragments = [{**data, "meters": data["meters"][:1]}, {"version": data["version"], "meters": data["meters"][1:]}]
    fragments[invalid_fragment]["meters"][0]["initial"] = "oops"
    for path, fragment in zip(paths, fragments, strict=True):
        path.write_text(yaml.safe_dump({"bars": fragment}, sort_keys=False))
    invalid = paths[invalid_fragment]
    line = next(index for index, value in enumerate(invalid.read_text().splitlines(), 1) if "oops" in value)
    store = DeclarationStore.discover(pack)
    store.parse("bars", "L0_0_minimal", BarsV2Config, False)
    assert store.errors.issues[0].location == f"{invalid}:{line}"


def test_profile_collision_names_its_own_namespace(pack: Path) -> None:
    source = pack / "vfs_profiles.yaml"
    data = yaml.safe_load(source.read_text())
    variable = {"name": "foo", "id": "foo", "type": "float", "semantic_type": "custom", "initial_value": 0.0, "exposed_to": []}
    data["global_profile"]["variables"].append(variable)
    source.write_text(yaml.safe_dump(data, sort_keys=False))
    headers = {key: data[key] for key in ("version", "evaluation_mode", "debug_logging")}
    agent = pack / "w_agent.yml"
    agent.write_text(yaml.safe_dump({**headers, "agent_profile": {"variables": [variable]}}, sort_keys=False))
    duplicate = pack / "z_global.yml"
    duplicate.write_text(yaml.safe_dump({**headers, "global_profile": {"variables": [variable]}}, sort_keys=False))
    with pytest.raises(CompilationError) as caught:
        DeclarationStore.discover(pack)
    message = str(caught.value)
    assert str(source) in message and str(duplicate) in message
    assert str(agent) not in message


def test_effect_fragments_accept_equal_budget_headers(tmp_path: Path) -> None:
    root = tmp_path / "effects"
    shutil.copytree("configs/test/effects_smoke", root, ignore=shutil.ignore_patterns(".compiled"))
    path = root / "effects.yaml"
    data = yaml.safe_load(path.read_text())
    path.write_text(yaml.safe_dump({**data, "effect_definitions": data["effect_definitions"][:1]}, sort_keys=False))
    (root / "z_effects.yml").write_text(yaml.safe_dump({**data, "effect_definitions": data["effect_definitions"][1:]}, sort_keys=False))
    assert len(RawConfigsV21.from_experiment_dir(root).effects.effect_definitions) == len(data["effect_definitions"])


def test_duplicate_entity_in_one_document_names_both_lines(pack: Path) -> None:
    path = pack / "levels" / "L0_0_minimal" / "bars.yaml"
    data = yaml.safe_load(path.read_text())
    # A distinct mapping avoids representing this as a YAML alias.
    data["bars"]["meters"].append(dict(data["bars"]["meters"][0]))
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    with pytest.raises(CompilationError) as caught:
        DeclarationStore.discover(pack)
    assert "first declared at" in str(caught.value)
    assert str(path) in str(caught.value)


def test_outside_pack_symlink_directory_is_refused(pack: Path, tmp_path: Path) -> None:
    outside = tmp_path / "external"
    outside.mkdir()
    (outside / "ignored.yml").write_text("unknown: true\n")
    linked = pack / "linked"
    linked.symlink_to(outside, target_is_directory=True)
    with pytest.raises(CompilationError) as caught:
        DeclarationStore.discover(pack)
    assert f"{linked}:1" in str(caught.value)


@pytest.mark.parametrize("kind", ["inside_directory", "broken_yaml"])
def test_unreadable_symlink_transports_are_refused(pack: Path, kind: str) -> None:
    linked = pack / "linked.yml"
    if kind == "inside_directory":
        linked.symlink_to(pack / "levels", target_is_directory=True)
    else:
        linked.symlink_to(pack / "missing.yml")
    with pytest.raises(CompilationError) as caught:
        DeclarationStore.discover(pack)
    assert f"{linked}:1" in str(caught.value)


def test_recursive_yaml_alias_is_a_structured_refusal(pack: Path) -> None:
    path = pack / "recursive.yml"
    path.write_text("variables: &recursive\n  - *recursive\n")
    with pytest.raises(CompilationError) as caught:
        DeclarationStore.discover(pack)
    assert str(path) in str(caught.value)


@pytest.mark.parametrize("failure", ["unknown", "noncyclical", "fractional", "boolean", "equal_literal", "unequal_literal", "inactive"])
def test_clock_reference_refusals_have_the_authored_origin(pack: Path, failure: str) -> None:
    profile_path = pack / "vfs_profiles.yaml"
    profiles = yaml.safe_load(profile_path.read_text())
    variable = profiles["global_profile"]["variables"][0]
    curriculum_path = pack / "levels" / "L3_temporal_mechanics" / "curriculum.yaml"
    curriculum = yaml.safe_load(curriculum_path.read_text())
    if failure == "unknown":
        curriculum["curriculum"]["day_length"] = {"period_of": "missing_clock"}
    elif failure == "noncyclical":
        variable["normalization"] = {"kind": "minmax", "min": 0.0, "max": 24.0, "clip": False}
    elif failure == "fractional":
        variable["normalization"]["period"] = 24.5
    elif failure == "boolean":
        variable["type"] = "bool"
    elif failure in {"equal_literal", "unequal_literal"}:
        curriculum["curriculum"]["day_length"] = 24 if failure == "equal_literal" else 25
    else:
        curriculum["curriculum"]["active_temporal"] = False
    profile_path.write_text(yaml.safe_dump(profiles, sort_keys=False))
    curriculum_path.write_text(yaml.safe_dump(curriculum, sort_keys=False))
    with pytest.raises(CompilationError) as caught:
        RawConfigsV21.from_experiment_dir(pack)
    message = str(caught.value)
    assert str(curriculum_path) in message
    if failure in {"noncyclical", "fractional", "boolean", "equal_literal", "unequal_literal"}:
        assert str(profile_path) in message


def test_clock_reference_selects_global_identity_among_profiles_and_clocks(pack: Path) -> None:
    path = pack / "vfs_profiles.yaml"
    profiles = yaml.safe_load(path.read_text())
    second = dict(profiles["global_profile"]["variables"][0])
    second.update(name="other_clock", id="other_clock", normalization={"kind": "cyclical_sin_cos", "period": 30})
    profiles["global_profile"]["variables"].append(second)
    profiles["agent_profile"] = {
        "variables": [
            {"name": "other_clock", "id": "other_clock", "type": "float", "semantic_type": "custom", "initial_value": 0.0, "exposed_to": []}
        ]
    }
    path.write_text(yaml.safe_dump(profiles, sort_keys=False))
    curriculum_path = pack / "levels" / "L3_temporal_mechanics" / "curriculum.yaml"
    curriculum = yaml.safe_load(curriculum_path.read_text())
    curriculum["curriculum"]["day_length"] = {"period_of": "other_clock"}
    curriculum_path.write_text(yaml.safe_dump(curriculum, sort_keys=False))
    raw = RawConfigsV21.from_experiment_dir(pack)
    assert raw.levels["L3_temporal_mechanics"].curriculum.curriculum.day_length == 30


def test_shared_document_preserves_each_wrapper_line(pack: Path) -> None:
    directory = pack / "levels" / "L0_0_minimal"
    source = directory / "mission.yml"
    source.write_text(
        "# introduction\n\n" + (directory / "bars.yaml").read_text() + "\n# boundary\n" + (directory / "drive.yaml").read_text()
    )
    (directory / "bars.yaml").unlink()
    (directory / "drive.yaml").unlink()
    lines = source.read_text().splitlines()
    store = DeclarationStore.discover(pack)
    for family in ("bars", "drive"):
        line = next(index for index, value in enumerate(lines, 1) if value == f"{family}:")
        assert store.source_map.lookup(f"levels/L0_0_minimal/{family}") == f"{source}:{line}"


def test_clock_authority_mutation_changes_both_resolved_consumers(pack: Path) -> None:
    compiler = UniverseCompiler()
    before = compiler.compile(pack, primary_level="L3_temporal_mechanics", use_cache=False)
    path = pack / "vfs_profiles.yaml"
    profiles = yaml.safe_load(path.read_text())
    profiles["global_profile"]["variables"][0]["normalization"]["period"] = 30
    path.write_text(yaml.safe_dump(profiles, sort_keys=False))
    after = compiler.compile(pack, primary_level="L3_temporal_mechanics", use_cache=False)
    level = after.get_level("L3_temporal_mechanics")
    clock = next(variable for variable in level.vfs_variables if variable.id == "day_phase")
    assert level.curriculum.curriculum.day_length == 30
    assert clock.normalization.period == 30
    assert level.observation_schema_hash != before.get_level("L3_temporal_mechanics").observation_schema_hash
    assert after.get_level("L0_0_minimal").curriculum.curriculum.day_length is None
