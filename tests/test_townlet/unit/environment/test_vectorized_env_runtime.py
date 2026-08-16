"""Runtime-specific tests for VectorizedHamletEnv."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import townlet.environment.vectorized_env as vectorized_env_module
from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.universe.compiler import UniverseCompiler


@pytest.mark.parametrize("config_name", ["configs/default_curriculum/levels/L0_0_minimal"])
def test_vectorized_env_avoids_runtime_yaml_reads(monkeypatch, config_name: str) -> None:
    """Ensure compiled environments no longer reopen bars/variables/action label YAML files."""

    # v2.1: UniverseCompiler expects an experiment root directory (containing
    # experiment.yaml, stratum.yaml, environment.yaml, etc.). The param here
    # points at a specific level directory; derive experiment_dir + level_name
    # from that path instead of compiling the level folder directly.
    compiler = UniverseCompiler()
    config_path = Path(config_name)

    if "levels" not in config_path.parts:
        experiment_dir = config_path
        level_name: str | None = None
    else:
        # configs/default_curriculum/levels/<level_name> → experiment_dir = configs/default_curriculum
        level_name = config_path.name
        experiment_dir = config_path.parents[1]

    compiled = compiler.compile(experiment_dir, primary_level=level_name)

    blocked = {"bars.yaml", "variables_reference.yaml", "action_labels.yaml"}
    original_open = Path.open

    def guarded_open(self: Path, *args, **kwargs):  # type: ignore[override]
        if self.name in blocked:
            raise AssertionError(f"Unexpected runtime read of {self}")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open, raising=False)

    env = compiled.create_environment(num_agents=1, level_name=level_name, device="cpu")
    assert env.observation_dim == compiled.metadata.observation_dim


def test_vectorized_env_uses_compiled_vfs_variables_without_profile_synthesis(tmp_path: Path) -> None:
    """Runtime VFS registry should consume compiler-emitted variables directly."""
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "global_profile": {"variables": [{"semantic_type": "custom", "name": "day_count", "type": "int", "initial_value": 0}]},
        "agent_profile": {"variables": [{"semantic_type": "custom", "name": "motivation", "type": "float", "initial_value": 0.5}]},
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    compiled_variable_ids = [var.id for var in compiled.vfs_variables]
    assert compiled_variable_ids.count("day_count") == 1
    assert compiled_variable_ids.count("motivation") == 1

    env = compiled.create_environment(num_agents=1, level_name=PRIMARY_LEVEL_NAME, device="cpu")

    runtime_variable_ids = [var.id for var in env.vfs_variables]
    assert runtime_variable_ids == compiled_variable_ids


def test_vectorized_env_uses_compiled_effects_schema(tmp_path: Path) -> None:
    """Runtime effect schema should be consumed from the compiled artifact."""
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "global_profile": {"variables": [{"semantic_type": "custom", "name": "day_count", "type": "int", "initial_value": 0}]},
        "agent_profile": {"variables": [{"semantic_type": "custom", "name": "motivation", "type": "float", "initial_value": 0.5}]},
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    assert compiled.effects_schema is not None
    assert compiled.effects_schema["vfs.day_count"] == "float"
    assert compiled.effects_schema["target.vfs.motivation"] == "float"

    env = compiled.create_environment(num_agents=1, level_name=PRIMARY_LEVEL_NAME, device="cpu")

    assert env.effects_schema == compiled.effects_schema


def test_vectorized_env_passes_compiled_effects_schema_to_item_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    """Item interaction compilation should receive the compiler-emitted effect schema."""
    compiled = UniverseCompiler().compile(Path("configs/test/items_smoke"), primary_level="L0_smoke", use_cache=False)
    assert compiled.effects_schema is not None

    captured: dict[str, dict[str, str] | None] = {}
    original_item_manager = vectorized_env_module.ItemManager

    class CapturingItemManager(original_item_manager):
        def __init__(self, *args, schema=None, **kwargs):
            captured["schema"] = schema
            super().__init__(*args, schema=schema, **kwargs)

    monkeypatch.setattr(vectorized_env_module, "ItemManager", CapturingItemManager)

    compiled.create_environment(num_agents=1, level_name="L0_smoke", device="cpu")

    assert captured["schema"] == compiled.effects_schema


def test_vectorized_env_uses_compiled_runtime_action_space_without_substrate_rebuild(monkeypatch: pytest.MonkeyPatch) -> None:
    """Runtime action-space construction should not re-read substrate defaults."""
    compiled = UniverseCompiler().compile(Path("configs/test/action_space/grid2d"), primary_level="L0", use_cache=False)
    assert compiled.runtime_action_space is not None

    def fail_get_default_actions(self: Grid2DSubstrate):  # type: ignore[override]
        raise AssertionError("Runtime must consume compiled runtime_action_space instead of substrate defaults")

    monkeypatch.setattr(Grid2DSubstrate, "get_default_actions", fail_get_default_actions)

    env = compiled.create_environment(num_agents=1, level_name="L0", device="cpu")

    assert env.action_space.action_dim == compiled.runtime_action_space.action_dim
    assert env.action_ids == compiled.runtime_action_space.action_ids
