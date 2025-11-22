"""Benchmarks for environment step overhead (baseline vs VFS/items/effects)."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.universe.compiler import UniverseCompiler


@pytest.fixture(scope="session")
def _compile_universe() -> callable:
    compiler = UniverseCompiler()

    def _compile(config_dir: Path | str):
        return compiler.compile(Path(config_dir), use_cache=False)

    return _compile


@pytest.fixture(scope="session")
def baseline_env(_compile_universe):
    """Minimal env without VFS/items/effects (default curriculum)."""
    config_dir = Path("configs/default_curriculum")
    universe = _compile_universe(config_dir)
    env = universe.create_environment(level_name="L0_0_minimal", num_agents=4, device=torch.device("cpu"))
    env.reset()
    return env


@pytest.fixture(scope="session")
def vfs_env(_compile_universe):
    """Env with VFS/items/effects enabled (effects smoke config)."""
    config_dir = Path("configs/test/effects_smoke")
    universe = _compile_universe(config_dir)
    env = universe.create_environment(level_name="L0_effects", num_agents=4, device=torch.device("cpu"))
    env.reset()
    return env


class TestEnvironmentStepBenchmarks:
    """Benchmark env.step to track overhead."""

    @pytest.mark.benchmark(group="env-step")
    def test_baseline_step(self, benchmark, baseline_env):
        wait_action = baseline_env.action_ids["WAIT"]
        actions = torch.full((baseline_env.num_agents,), wait_action, device=baseline_env.device, dtype=torch.long)

        def _step():
            baseline_env.step(actions)

        benchmark(_step)

    @pytest.mark.benchmark(group="env-step")
    def test_vfs_enabled_step(self, benchmark, vfs_env):
        wait_action = vfs_env.action_ids["WAIT"]
        actions = torch.full((vfs_env.num_agents,), wait_action, device=vfs_env.device, dtype=torch.long)

        def _step():
            vfs_env.step(actions)

        benchmark(_step)
