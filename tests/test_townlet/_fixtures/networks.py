"""Network fixtures for Townlet tests."""

from __future__ import annotations

import pytest
import torch

from townlet.agent.networks import SimpleQNetwork
from townlet.environment.vectorized_env import VectorizedHamletEnv

# `recurrent_qnetwork` was removed here: it had zero users and passed `num_meters=`,
# which has never been a parameter of RecurrentSpatialQNetwork, so any use would
# have raised TypeError at binding. Dead test surface — deleted, not repaired.
__all__ = ["simple_qnetwork"]


@pytest.fixture
def simple_qnetwork(basic_env: VectorizedHamletEnv, device: torch.device) -> SimpleQNetwork:
    """Create a SimpleQNetwork for full-observability tests."""

    obs_dim = basic_env.observation_dim
    return SimpleQNetwork(obs_dim=obs_dim, action_dim=basic_env.action_dim, hidden_dim=128).to(device)
