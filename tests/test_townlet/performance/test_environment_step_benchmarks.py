"""Benchmarks for environment step overhead (baseline vs VFS/items/effects).

These benchmarks parameterise across population scale so the
hot-path report (docs/performance/runtime-hot-paths.md) can compare
vectorisation candidates across realistic agent counts.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.universe.compiler import UniverseCompiler

# Scale axes recorded in pytest-benchmark metadata so each run captures
# enough dimensions to compare optimisation work against a baseline.
_AGENT_SCALE = (1, 4, 16, 64)


@pytest.fixture(scope="session")
def _compile_universe() -> callable:
    compiler = UniverseCompiler()

    def _compile(config_dir: Path | str, *, primary_level: str):
        return compiler.compile(Path(config_dir), primary_level=primary_level, use_cache=False)

    return _compile


def _build_env(_compile_universe, config_dir: str, primary_level: str, num_agents: int):
    universe = _compile_universe(Path(config_dir), primary_level=primary_level)
    env = universe.create_environment(level_name=primary_level, num_agents=num_agents, device=torch.device("cpu"))
    env.reset()
    return env


@pytest.fixture(scope="session")
def baseline_env(_compile_universe):
    return _build_env(_compile_universe, "configs/default_curriculum", "L0_0_minimal", num_agents=4)


@pytest.fixture(scope="session")
def vfs_env(_compile_universe):
    return _build_env(_compile_universe, "configs/test/effects_smoke", "L0_effects", num_agents=4)


def _record_scale_axes(benchmark, env, *, label: str) -> None:
    """Pin scale dimensions on the benchmark record so future runs compare.

    Captures num_agents, action_dim, observation_dim, position_dim,
    affordance_count, grid_size — every axis named in the
    hamlet-2b92152ac9 done_definition.
    """
    benchmark.extra_info["scenario"] = label
    benchmark.extra_info["num_agents"] = env.num_agents
    benchmark.extra_info["action_dim"] = env.action_dim
    benchmark.extra_info["observation_dim"] = env.observation_dim
    benchmark.extra_info["position_dim"] = env.substrate.position_dim
    benchmark.extra_info["affordance_count"] = len(env.affordances) if hasattr(env, "affordances") else 0
    benchmark.extra_info["grid_size"] = env.grid_size if env.grid_size is not None else 0


class TestEnvironmentStepBenchmarks:
    """Benchmark env.step across scale and feature surface."""

    @pytest.mark.benchmark(group="env-step")
    def test_baseline_step(self, benchmark, baseline_env):
        wait_action = baseline_env.action_ids["WAIT"]
        actions = torch.full((baseline_env.num_agents,), wait_action, device=baseline_env.device, dtype=torch.long)
        _record_scale_axes(benchmark, baseline_env, label="baseline")

        def _step():
            baseline_env.step(actions)

        benchmark(_step)

    @pytest.mark.benchmark(group="env-step")
    def test_vfs_enabled_step(self, benchmark, vfs_env):
        wait_action = vfs_env.action_ids["WAIT"]
        actions = torch.full((vfs_env.num_agents,), wait_action, device=vfs_env.device, dtype=torch.long)
        _record_scale_axes(benchmark, vfs_env, label="vfs+effects+items")

        def _step():
            vfs_env.step(actions)

        benchmark(_step)

    @pytest.mark.benchmark(group="env-step-scale")
    @pytest.mark.parametrize("num_agents", _AGENT_SCALE)
    def test_baseline_step_scales(self, benchmark, _compile_universe, num_agents):
        """Track env.step cost vs num_agents to bound the per-agent overhead.

        A per-agent Python loop in the hot path would show super-linear
        growth here; a fully-vectorised path would stay close to flat.
        """
        env = _build_env(_compile_universe, "configs/default_curriculum", "L0_0_minimal", num_agents=num_agents)
        wait_action = env.action_ids["WAIT"]
        actions = torch.full((num_agents,), wait_action, device=env.device, dtype=torch.long)
        _record_scale_axes(benchmark, env, label=f"baseline_n{num_agents}")

        def _step():
            env.step(actions)

        benchmark(_step)


class TestActionMaskBenchmarks:
    """Benchmark the extracted ActionMaskBuilder (hamlet-278239308d)."""

    @pytest.mark.benchmark(group="action-mask")
    @pytest.mark.parametrize("num_agents", _AGENT_SCALE)
    def test_action_mask_build(self, benchmark, _compile_universe, num_agents):
        env = _build_env(_compile_universe, "configs/default_curriculum", "L0_0_minimal", num_agents=num_agents)
        _record_scale_axes(benchmark, env, label=f"action_mask_n{num_agents}")

        def _build_mask():
            env.get_action_masks()

        benchmark(_build_mask)


class TestVTCTransitionRunnerBenchmarks:
    """Benchmark the VTC transition schedule runner across scale.

    The runner is the choreographer behind env.step; isolating its cost
    lets the hot-path report distinguish env wrapper overhead from VTC
    program work.
    """

    @pytest.mark.benchmark(group="vtc-runner")
    @pytest.mark.parametrize("num_agents", _AGENT_SCALE)
    def test_vtc_passive_depletion(self, benchmark, _compile_universe, num_agents):
        """The passive-depletion phase is per-tick on every agent; it is one
        of the candidates the architecture report flags for vectorisation."""
        env = _build_env(_compile_universe, "configs/default_curriculum", "L0_0_minimal", num_agents=num_agents)
        _record_scale_axes(benchmark, env, label=f"vtc_passive_depletion_n{num_agents}")

        def _depletion():
            env._apply_vtc_passive_depletion(1.0)

        benchmark(_depletion)

    @pytest.mark.benchmark(group="vtc-runner")
    @pytest.mark.parametrize("num_agents", _AGENT_SCALE)
    def test_vtc_threshold_cascades(self, benchmark, _compile_universe, num_agents):
        """Threshold cascades run on every tick and are a per-agent hot path."""
        env = _build_env(_compile_universe, "configs/default_curriculum", "L0_0_minimal", num_agents=num_agents)
        _record_scale_axes(benchmark, env, label=f"vtc_threshold_cascades_n{num_agents}")

        def _cascades():
            env._apply_vtc_threshold_cascades()

        benchmark(_cascades)


class TestRewardCalculatorBenchmarks:
    """Benchmark reward calculation in isolation across scale."""

    @pytest.mark.benchmark(group="reward")
    @pytest.mark.parametrize("num_agents", _AGENT_SCALE)
    def test_calculate_shaped_rewards(self, benchmark, _compile_universe, num_agents):
        env = _build_env(_compile_universe, "configs/default_curriculum", "L0_0_minimal", num_agents=num_agents)
        _record_scale_axes(benchmark, env, label=f"reward_n{num_agents}")

        def _rewards():
            env._reward_calculator._calculate_shaped_rewards()

        benchmark(_rewards)
