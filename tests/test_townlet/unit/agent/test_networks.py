"""Non-token Q-network unit contracts.

Token-set and recurrent networks have dedicated contract suites.
"""

import torch
import torch.nn as nn

from townlet.agent.networks import DuelingQNetwork, SimpleQNetwork


def test_simple_q_network_shape_and_gradient() -> None:
    network = SimpleQNetwork(obs_dim=29, action_dim=8, hidden_dim=128)
    observations = torch.randn(4, 29, requires_grad=True)
    q_values = network(observations)
    assert q_values.shape == (4, 8)
    q_values.mean().backward()
    assert all(parameter.grad is not None for parameter in network.parameters())


def test_dueling_q_network_shape_and_identifiability() -> None:
    network = DuelingQNetwork(
        obs_dim=29,
        action_dim=8,
        shared_dims=[64],
        value_dims=[32],
        advantage_dims=[32],
        activation="relu",
        dropout=0.0,
        layer_norm=True,
    )
    observations = torch.randn(4, 29)
    q_values = network(observations)
    assert q_values.shape == (4, 8)
    assert not any(isinstance(module, nn.LSTM) for module in network.modules())
