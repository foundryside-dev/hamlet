"""End-to-end checks for the L5 multi-agent VFS config pack."""

from pathlib import Path

import torch

from townlet.universe.compiler import UniverseCompiler


def test_l5_multi_agent_config_exercises_pair_and_affordance_scopes_end_to_end() -> None:
    config_dir = Path("configs/L5_multi_agent")

    compiled = UniverseCompiler().compile(config_dir, primary_level="L5_multi_agent", use_cache=False)

    variables = {variable.id: variable for variable in compiled.vfs_variables}
    assert variables["trust"].scope == "pair"
    assert variables["trust"].type == "scalar"
    assert variables["occupied_by"].scope == "affordance"
    assert variables["occupied_by"].type == "agent_ref"

    env = compiled.create_environment(num_agents=3, level_name="L5_multi_agent", device="cpu")

    trust = env.vfs_registry.get("trust", reader="agent")
    occupied_by = env.vfs_registry.get("occupied_by", reader="engine")

    assert trust.shape == torch.Size([3, 3])
    assert torch.allclose(trust, torch.full((3, 3), 0.5))
    assert occupied_by.shape == torch.Size([compiled.metadata_for_level("L5_multi_agent").affordance_count])
    assert torch.all(occupied_by == -1)

    observations, rewards, dones, info = env.step(torch.zeros(3, dtype=torch.long))

    assert observations.shape == torch.Size([3, compiled.metadata_for_level("L5_multi_agent").observation_dim])
    assert rewards.shape == torch.Size([3])
    assert dones.shape == torch.Size([3])
    assert "successful_interactions" in info
