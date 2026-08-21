"""Cache serialization of agent profiles, and loudness of cache-write failures.

Pins hamlet-a141ab5db3 / hamlet-cbb747a51e: a pack declaring `agent_profile`
compiled fine but its artifact could not be serialized (`agent_profile` was
passed to msgpack as a raw CompiledGlobalProfile), and the failed write was
downgraded to a logger warning while the CLI printed success and exited 0.
"""

from __future__ import annotations

from pathlib import Path

import msgpack  # type: ignore[import]
import pytest
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.profiles import CompiledGlobalProfile


def _write_profiles_with_agent(experiment_dir: Path) -> None:
    profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "global_profile": {
            "variables": [
                {"semantic_type": "custom", "name": "day_count", "type": "int", "initial_value": 0},
            ]
        },
        "agent_profile": {
            "variables": [
                {"semantic_type": "custom", "name": "inventory_weight", "type": "float", "initial_value": 0.0},
                {
                    "semantic_type": "custom",
                    "name": "is_encumbered",
                    "type": "bool",
                    "expression": "inventory_weight > 1.0",
                },
            ]
        },
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))


@pytest.fixture
def compiled_with_agent_profile(tmp_path: Path) -> CompiledUniverse:
    experiment_dir = prepare_config_dir(tmp_path, name="agent_profile_pack")
    _write_profiles_with_agent(experiment_dir)
    return UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)


def test_to_dict_with_agent_profile_is_msgpack_serializable(compiled_with_agent_profile) -> None:
    """The exact failure mode: msgpack could not pack the raw compiled agent profile."""
    packed = msgpack.packb(compiled_with_agent_profile.to_dict(), use_bin_type=True)
    assert packed


def test_agent_profile_round_trips_through_dict(compiled_with_agent_profile) -> None:
    restored = CompiledUniverse.from_dict(
        msgpack.unpackb(
            msgpack.packb(compiled_with_agent_profile.to_dict(), use_bin_type=True),
            raw=False,
            strict_map_key=False,
        )
    )

    profile = restored.compiled_vfs_profiles.agent_profile
    assert isinstance(profile, CompiledGlobalProfile)

    by_name = {var.name: var for var in profile.variables}
    assert set(by_name) == {"inventory_weight", "is_encumbered"}

    weight = by_name["inventory_weight"]
    assert weight.type == "float"
    assert weight.initial_value == 0.0
    assert weight.semantic_type == "custom"

    encumbered = by_name["is_encumbered"]
    assert encumbered.expression == "inventory_weight > 1.0"
    assert encumbered.ast is not None, "expression ASTs must be reconstructed on load"
    assert encumbered.result_type == "bool"

    assert profile.dependencies["is_encumbered"] == ("inventory_weight",)


def test_global_profile_round_trip_preserves_semantic_type(compiled_with_agent_profile) -> None:
    """The global-profile serializer dropped semantic_type/shape/dims; pin the full field set."""
    restored = CompiledUniverse.from_dict(compiled_with_agent_profile.to_dict())
    var = restored.compiled_vfs_profiles.global_profile.variables[0]
    assert var.name == "day_count"
    assert var.semantic_type == "custom"


def test_compile_writes_artifact_for_pack_with_agent_profile(tmp_path: Path) -> None:
    """End-to-end: compile with cache enabled must actually write the .msgpack."""
    experiment_dir = prepare_config_dir(tmp_path, name="agent_profile_pack")
    _write_profiles_with_agent(experiment_dir)

    UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=True)

    artifact = experiment_dir / ".compiled" / f"universe-{PRIMARY_LEVEL_NAME}.msgpack"
    assert artifact.exists(), "compile reported success but wrote no cache artifact"

    loaded = CompiledUniverse.load_from_cache(artifact)
    assert isinstance(loaded.compiled_vfs_profiles.agent_profile, CompiledGlobalProfile)


def test_failed_cache_write_raises_instead_of_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A cache write failure must fail compile() loudly, not degrade to a log line."""
    experiment_dir = prepare_config_dir(tmp_path, name="agent_profile_pack")
    _write_profiles_with_agent(experiment_dir)

    def _boom(self, path: Path) -> None:
        raise TypeError("can not serialize 'Whatever' object")

    monkeypatch.setattr(CompiledUniverse, "save_to_cache", _boom)

    with pytest.raises(CompilationError) as excinfo:
        UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=True)

    assert "cache artifact" in str(excinfo.value).lower()


def test_cli_compile_exits_nonzero_when_cache_write_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """The CLI must not print success or exit 0 over a missing artifact."""
    from townlet.universe.__main__ import main

    experiment_dir = prepare_config_dir(tmp_path, name="agent_profile_pack")
    _write_profiles_with_agent(experiment_dir)

    def _boom(self, path: Path) -> None:
        raise TypeError("can not serialize 'Whatever' object")

    monkeypatch.setattr(CompiledUniverse, "save_to_cache", _boom)

    exit_code = main(["compile", str(experiment_dir), "--primary-level", PRIMARY_LEVEL_NAME])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "Compilation succeeded" not in captured.out
