"""End-to-end checks for the L5 config pack.

Under the owner's S1 ruling the batch is N independent single-agent worlds, so L5 is
N agents side by side, each alone. It declares no relational state (the pair scope is
deleted, VFS WP15); its one variable is an agent-scope expression of energy.
"""

from pathlib import Path

import torch

from townlet.universe.compiler import UniverseCompiler


def test_l5_config_compiles_and_steps_as_independent_worlds() -> None:
    config_dir = Path("configs/L5_multi_agent")

    compiled = UniverseCompiler().compile(config_dir, primary_level="L5_multi_agent", use_cache=False)

    variables = {variable.id: variable for variable in compiled.get_level("L5_multi_agent").vfs_variables}
    assert variables["deficit_energy"].scope == "agent"
    assert variables["deficit_energy"].exposed_to == ["agent"]

    env = compiled.create_environment(num_agents=3, level_name="L5_multi_agent", device="cpu")
    env.reset()

    assert env.vfs_registry.get("deficit_energy", reader="agent").shape == torch.Size([3])

    observations, rewards, dones, info = env.step(torch.zeros(3, dtype=torch.long))

    assert observations.shape == torch.Size([3, compiled.metadata_for_level("L5_multi_agent").observation_dim])
    assert rewards.shape == torch.Size([3])
    assert dones.shape == torch.Size([3])
    assert "successful_interactions" in info
