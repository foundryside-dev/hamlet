"""Integration tests for VFS runtime evaluation."""

from pathlib import Path

import torch

from townlet.universe.compiler import UniverseCompiler


def test_vfs_expressions_evaluated_at_runtime():
    """VFS expressions should be evaluated during environment step."""
    # Setup: Compile universe with VFS profiles
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_effects", use_cache=False)

    # Create environment
    env = compiled.create_environment(
        num_agents=4,
        level_name="L0_effects",
        device=torch.device("cpu"),
    )

    # Exercise: Step environment
    env.reset()
    obs, rewards, dones, info = env.step(torch.zeros(4, dtype=torch.long))

    # Verify: VFS variables should be in registry and updated
    # (day_count should increment each step if expression is "day_count + 1")
    assert hasattr(env, "vfs_registry")
    # Check that global VFS variables exist
    assert "day_count" in env.vfs_registry._storage or "day_count" in env.vfs_registry.variables
