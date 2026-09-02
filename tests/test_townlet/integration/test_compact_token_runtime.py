"""One-tick vertical trace through the sole compact token transport."""

from __future__ import annotations

from pathlib import Path

import torch
import torch.nn as nn

from townlet.agent.network_factory import NetworkFactory
from townlet.config.brain_config import FeedforwardConfig
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.state import RewardTensor
from townlet.universe.compiler import UniverseCompiler


def test_l1_compact_vertical_trace() -> None:
    device = torch.device("cpu")
    universe = UniverseCompiler().compile(
        Path("configs/default_curriculum"),
        primary_level="L1_full_observability",
        use_cache=False,
    )
    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L1_full_observability",
        num_agents=2,
        device=device,
    )

    observations = env.reset()
    next_observations, rewards, dones, _ = env.step(torch.zeros(env.num_agents, dtype=torch.long))
    assert observations.shape == next_observations.shape == (env.num_agents, 118)
    assert env.token_spec.total_dims == env.observation_dim == 118

    replay = ReplayBuffer(capacity=4, device=device)
    replay.push(
        observations,
        torch.zeros(env.num_agents, dtype=torch.long),
        RewardTensor.from_dac(rewards),
        next_observations,
        dones,
    )
    batch = replay.sample(batch_size=2)
    assert batch["observations"].shape == (2, 118)

    flat = NetworkFactory.build_feedforward(
        FeedforwardConfig(hidden_layers=[16], activation="relu", dropout=0.0, layer_norm=False),
        obs_dim=env.token_spec.total_dims,
        action_dim=env.action_dim,
    )
    assert flat(batch["observations"]).shape == (2, env.action_dim)

    from townlet.agent.token_input import TokenInputAssembler

    meter_type = env.token_spec.get_type("meter")
    meter_layout = env.token_spec.compact_layout().get_type("meter")
    assert meter_type is not None and meter_layout is not None
    compact_meter_rows = batch["observations"][:, meter_layout.start : meter_layout.end].view(
        2,
        meter_layout.capacity,
        meter_layout.compact_row_width,
    )
    fixed_meter_rows = TokenInputAssembler(env.token_spec).expand_type("meter", compact_meter_rows)
    projection = nn.Linear(len(meter_type.payload_features), 8)
    projected = projection(fixed_meter_rows[:, :, 1:])
    assert fixed_meter_rows.shape == (2, meter_type.capacity, meter_type.fixed_row_width)
    assert projected.shape == (2, meter_type.capacity, 8)
