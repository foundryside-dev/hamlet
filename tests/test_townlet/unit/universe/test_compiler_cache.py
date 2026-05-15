"""Tests for compiler cache helper utilities."""

from __future__ import annotations

import shutil
from pathlib import Path

import msgpack  # type: ignore[import]
import pytest
import yaml

import townlet.universe.compiler as compiler_module
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler


def _copy_experiment(tmp_path: Path, source: Path | None = None) -> Path:
    """Copy a v2.1 experiment directory into tmp_path."""
    experiment_src = source or Path("configs/test/model_config")
    dest = tmp_path / experiment_src.name
    shutil.copytree(experiment_src, dest)
    return dest


def test_cache_directory_resolves_inside_config_dir(tmp_path: Path) -> None:
    compiler = UniverseCompiler()
    config_dir = tmp_path / "pack"
    config_dir.mkdir()

    cache_dir = compiler._cache_directory_for(config_dir)

    assert cache_dir == config_dir / ".compiled"


def test_prepare_cache_directory_creates_directory(tmp_path: Path) -> None:
    compiler = UniverseCompiler()
    cache_dir = tmp_path / ".compiled"

    compiler._prepare_cache_directory(cache_dir)

    assert cache_dir.exists()
    assert cache_dir.is_dir()


def test_prepare_cache_directory_errors_when_path_is_file(tmp_path: Path) -> None:
    compiler = UniverseCompiler()
    cache_dir = tmp_path / ".compiled"
    cache_dir.write_text("not a directory")

    with pytest.raises(RuntimeError):
        compiler._prepare_cache_directory(cache_dir)


def test_cache_artifact_path_points_inside_cache_dir(tmp_path: Path) -> None:
    compiler = UniverseCompiler()
    config_dir = tmp_path / "pack"
    config_dir.mkdir()

    artifact_path = compiler._cache_artifact_path(config_dir)

    assert artifact_path == config_dir / ".compiled" / "universe.msgpack"


def test_compile_uses_cache_when_hash_matches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_dir = _copy_experiment(tmp_path)

    builder = UniverseCompiler()
    builder.compile(config_dir, primary_level="L0_test", use_cache=True)

    flag = {"stage1_called": False}

    def _fail_loader(_config_dir: Path):
        flag["stage1_called"] = True
        raise AssertionError("Stage 1 should not run when loading from cache")

    monkeypatch.setattr(compiler_module, "load_v21_configs", _fail_loader)

    cached_compiler = UniverseCompiler()
    compiled = cached_compiler.compile(config_dir, primary_level="L0_test", use_cache=True)

    assert not flag["stage1_called"]
    assert compiled.metadata.universe_name == "Model Config (Test)"


def test_compile_rebuilds_cache_when_hash_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_dir = _copy_experiment(tmp_path)
    builder = UniverseCompiler()
    builder.compile(config_dir, primary_level="L0_test", use_cache=True)

    training_path = config_dir / "levels" / "L0_test" / "training.yaml"
    training_text = training_path.read_text()
    training_path.write_text(training_text.replace("max_episodes: 500", "max_episodes: 501"))

    original_loader = compiler_module.load_v21_configs
    counter = {"calls": 0}

    def _wrapped_loader(cfg_dir: Path):
        counter["calls"] += 1
        return original_loader(cfg_dir)

    monkeypatch.setattr(compiler_module, "load_v21_configs", _wrapped_loader)

    refreshed_compiler = UniverseCompiler()
    refreshed_compiler.compile(config_dir, primary_level="L0_test", use_cache=True)

    assert counter["calls"] == 1


def test_config_hash_includes_relative_yaml_paths(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    compiler = UniverseCompiler()
    original_hash = compiler._compute_config_hash(config_dir)

    (config_dir / "levels" / "L0_test").rename(config_dir / "levels" / "L1_test")

    assert compiler._compute_config_hash(config_dir) != original_hash


def test_compile_rebuilds_cache_when_compiler_provenance_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_dir = _copy_experiment(tmp_path)
    builder = UniverseCompiler()
    builder.compile(config_dir, primary_level="L0_test", use_cache=True)

    original_loader = compiler_module.load_v21_configs
    counter = {"calls": 0}

    def _wrapped_loader(cfg_dir: Path):
        counter["calls"] += 1
        return original_loader(cfg_dir)

    monkeypatch.setattr(compiler_module, "COMPILER_VERSION", "99.0-test")
    monkeypatch.setattr(compiler_module, "load_v21_configs", _wrapped_loader)

    UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=True)

    assert counter["calls"] == 1


def test_compile_recovers_from_corrupted_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_dir = _copy_experiment(tmp_path)
    compiler = UniverseCompiler()
    compiler.compile(config_dir, primary_level="L0_test", use_cache=True)

    cache_path = compiler._cache_artifact_path(config_dir)
    cache_path.write_bytes(b"corrupted")

    original_loader = compiler_module.load_v21_configs
    counter = {"calls": 0}

    def _wrapped_loader(cfg_dir: Path):
        counter["calls"] += 1
        return original_loader(cfg_dir)

    monkeypatch.setattr(compiler_module, "load_v21_configs", _wrapped_loader)

    UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=True)

    assert counter["calls"] == 1


@pytest.mark.parametrize(
    "missing_field",
    [
        "observation_activity",
        "vfs_observation_fields",
        "vfs_variables",
        "action_space_metadata",
        "runtime_action_space",
        "optimization_data_raw",
        "vfs_observation_spec",
    ],
)
def test_direct_cache_load_rejects_missing_required_top_level_fields(tmp_path: Path, missing_field: str) -> None:
    config_dir = _copy_experiment(tmp_path)
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_test", use_cache=True)

    payload = compiled.to_dict()
    payload.pop(missing_field)
    stale_path = tmp_path / f"missing-{missing_field}.msgpack"
    stale_path.write_bytes(msgpack.packb(payload, use_bin_type=True))

    with pytest.raises(ValueError, match=f"missing required field '{missing_field}'"):
        CompiledUniverse.load_from_cache(stale_path)


@pytest.mark.parametrize(
    "missing_field",
    [
        "compiled_vfs_profiles",
        "compiled_effect_catalog",
        "effects_schema",
        "effect_observation_slots",
        "vfs_expression_schema",
        "vfs_history_spec",
        "vfs_observation_marks",
        "all_levels",
    ],
)
def test_direct_cache_load_rejects_missing_current_schema_optional_value_fields(tmp_path: Path, missing_field: str) -> None:
    config_dir = _copy_experiment(tmp_path)
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_test", use_cache=True)

    payload = compiled.to_dict()
    payload.pop(missing_field)
    stale_path = tmp_path / f"missing-current-schema-{missing_field}.msgpack"
    stale_path.write_bytes(msgpack.packb(payload, use_bin_type=True))

    with pytest.raises(ValueError, match=f"missing required field '{missing_field}'"):
        CompiledUniverse.load_from_cache(stale_path)


@pytest.mark.parametrize(
    "missing_field",
    [
        "global_vars",
        "agent_vars",
        "item_profile_vars",
        "item_vars_per_slot",
        "max_item_profiles",
        "max_tensor_elements",
    ],
)
def test_direct_cache_load_rejects_missing_vfs_observation_spec_fields(tmp_path: Path, missing_field: str) -> None:
    config_dir = _copy_experiment(tmp_path)
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_test", use_cache=True)

    payload = compiled.to_dict()
    payload["vfs_observation_spec"].pop(missing_field)
    stale_path = tmp_path / f"missing-vfs-observation-spec-{missing_field}.msgpack"
    stale_path.write_bytes(msgpack.packb(payload, use_bin_type=True))

    with pytest.raises(ValueError, match=f"missing required field 'vfs_observation_spec.{missing_field}'"):
        CompiledUniverse.load_from_cache(stale_path)


@pytest.mark.parametrize(
    ("section", "missing_field"),
    [
        ("action_space_metadata", "actions"),
        ("action_space_metadata", "labels"),
        ("action_space_metadata", "label_description"),
        ("action_space_metadata", "label_domain"),
        ("runtime_action_space", "actions"),
        ("runtime_action_space", "substrate_action_count"),
        ("runtime_action_space", "custom_action_count"),
        ("runtime_action_space", "affordance_action_count"),
        ("runtime_action_space", "enabled_action_names"),
        ("meter_metadata", "meters"),
        ("affordance_metadata", "affordances"),
    ],
)
def test_direct_cache_load_rejects_missing_metadata_collection_fields(tmp_path: Path, section: str, missing_field: str) -> None:
    config_dir = _copy_experiment(tmp_path)
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_test", use_cache=True)

    payload = compiled.to_dict()
    payload[section].pop(missing_field)
    stale_path = tmp_path / f"missing-{section}-{missing_field}.msgpack"
    stale_path.write_bytes(msgpack.packb(payload, use_bin_type=True))

    with pytest.raises(ValueError, match=f"missing required field '{section}.{missing_field}'"):
        CompiledUniverse.load_from_cache(stale_path)


@pytest.mark.parametrize(
    "missing_field",
    ["drive_hash", "curriculum_hash", "bars_hash", "affordances_hash", "training_hash"],
)
def test_direct_cache_load_rejects_missing_level_provenance_fields(tmp_path: Path, missing_field: str) -> None:
    config_dir = _copy_experiment(tmp_path)
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_test", use_cache=True)

    payload = compiled.to_dict()
    payload["all_levels"]["L0_test"].pop(missing_field)
    stale_path = tmp_path / f"missing-level-provenance-{missing_field}.msgpack"
    stale_path.write_bytes(msgpack.packb(payload, use_bin_type=True))

    with pytest.raises(ValueError, match=f"missing required field 'all_levels.L0_test.{missing_field}'"):
        CompiledUniverse.load_from_cache(stale_path)


@pytest.mark.parametrize("missing_field", ["observation_activity", "vfs_observation_fields", "vfs_variables", "optimization_data_raw"])
def test_direct_cache_load_rejects_missing_required_level_fields(tmp_path: Path, missing_field: str) -> None:
    config_dir = _copy_experiment(tmp_path)
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_test", use_cache=True)

    payload = compiled.to_dict()
    payload["all_levels"]["L0_test"].pop(missing_field)
    stale_path = tmp_path / f"missing-level-{missing_field}.msgpack"
    stale_path.write_bytes(msgpack.packb(payload, use_bin_type=True))

    with pytest.raises(ValueError, match=f"missing required field 'all_levels.L0_test.{missing_field}'"):
        CompiledUniverse.load_from_cache(stale_path)


@pytest.mark.parametrize("missing_field", ["observation_activity", "vfs_observation_fields", "vfs_variables", "optimization_data_raw"])
def test_compile_cache_fast_path_recovers_from_missing_required_fields(tmp_path: Path, missing_field: str) -> None:
    config_dir = _copy_experiment(tmp_path)
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_test", use_cache=True)

    payload = compiled.to_dict()
    payload.pop(missing_field)
    compiler._cache_artifact_path(config_dir).write_bytes(msgpack.packb(payload, use_bin_type=True))

    recompiled = UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=True)

    assert recompiled.metadata.universe_name == "Model Config (Test)"
    assert recompiled.observation_activity.active_dim_count > 0


def test_cache_handles_zero_affordances(tmp_path: Path) -> None:
    """Ensure cache logic tolerates enabled_affordances=None in training config."""
    config_dir = _copy_experiment(tmp_path)

    training_path = config_dir / "levels" / "L0_test" / "training.yaml"
    training = yaml.safe_load(training_path.read_text())
    training.setdefault("environment", {})["enabled_affordances"] = None
    training_path.write_text(yaml.safe_dump(training))

    compiler = UniverseCompiler()
    compiler.compile(config_dir, primary_level="L0_test", use_cache=True)
    compiler.compile(config_dir, primary_level="L0_test", use_cache=True)  # ensure cache load works
