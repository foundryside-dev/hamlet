"""Runtime-specific tests for VectorizedHamletEnv."""

from __future__ import annotations

from pathlib import Path

import pytest

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
