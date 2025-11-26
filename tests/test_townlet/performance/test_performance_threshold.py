"""Performance guardrail: ensure VFS/effects/items overhead stays within threshold."""

from __future__ import annotations

import time
from pathlib import Path

import torch

from townlet.universe.compiler import UniverseCompiler

# Target: VFS/effects/items should add <5% overhead vs baseline
OVERHEAD_LIMIT = 0.05


def _compile_env(config_dir: Path, level_name: str):
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level=level_name, use_cache=False)
    env = compiled.create_environment(level_name=level_name, num_agents=4, device=torch.device("cpu"))
    return env


def _per_step_time(env, steps: int = 50) -> float:
    """Measure average step time (seconds/step) using WAIT actions."""
    wait_action = env.action_ids["WAIT"]
    actions = torch.full((env.num_agents,), wait_action, device=env.device, dtype=torch.long)
    env.reset()
    start = time.perf_counter()
    for _ in range(steps):
        env.step(actions)
    elapsed = time.perf_counter() - start
    return elapsed / steps


def test_vfs_overhead_under_limit(tmp_path):
    """Assert VFS/items/effects overhead stays within configured threshold."""
    baseline_config = Path("configs/default_curriculum")
    vfs_config = Path("configs/test/effects_smoke")

    baseline_env = _compile_env(baseline_config, level_name="L0_0_minimal")
    vfs_env = _compile_env(vfs_config, level_name="L0_effects")

    baseline_time = _per_step_time(baseline_env)
    vfs_time = _per_step_time(vfs_env)

    # Avoid division by zero; if baseline is zero, treat any overhead as failure
    if baseline_time <= 0.0:
        raise AssertionError("Baseline step time reported as zero; cannot compute overhead.")

    overhead_ratio = (vfs_time - baseline_time) / baseline_time

    # Allow tiny absolute jitter to avoid flakiness on fast CI machines
    jitter = 1e-4
    assert overhead_ratio <= OVERHEAD_LIMIT + jitter, (
        f"VFS overhead too high: {overhead_ratio:.4f} (> {OVERHEAD_LIMIT}) " f"(baseline={baseline_time:.6f}s, vfs={vfs_time:.6f}s)"
    )
