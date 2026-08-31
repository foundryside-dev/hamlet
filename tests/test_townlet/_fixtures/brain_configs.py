"""BrainConfig test fixtures for WP-C2 migration.

Provides standardized brain.yaml fixtures for all test scenarios:
- minimal_brain_config: SimpleQNetwork for unit tests
- recurrent_brain_config: RecurrentTokenQNetwork for POMDP tests

Usage:
    def test_something(minimal_brain_config):
        population = VectorizedPopulation(..., brain_config=minimal_brain_config)
"""

import pytest

from townlet.config.brain_config import load_brain_config


@pytest.fixture
def minimal_brain_config(tmp_path):
    """Minimal brain.yaml for SimpleQNetwork testing.

    Use for: Unit tests requiring minimal network configuration.
    Architecture: SimpleQNetwork (MLP: obs_dim → 128 → 64 → action_dim)
    """
    brain_yaml = tmp_path / "brain.yaml"
    brain_yaml.write_text("""
version: "1.0"
description: "Minimal brain config for testing"

architecture:
  type: feedforward
  feedforward:
    hidden_layers: [128, 64]
    activation: relu
    dropout: 0.0
    layer_norm: false

optimizer:
  type: adam
  learning_rate: 0.001
  adam_beta1: 0.9
  adam_beta2: 0.999
  adam_eps: 1.0e-8
  weight_decay: 0.0
  schedule:
    type: constant

loss:
  type: smooth_l1

q_learning:
  gamma: 0.99
  use_double_dqn: false
  target_update_frequency: 100

replay:
  capacity: 10000
  prioritized: false
""")
    return load_brain_config(tmp_path)


@pytest.fixture
def recurrent_brain_config(tmp_path):
    """Recurrent brain.yaml for LSTM testing.

    Use for: POMDP tests requiring RecurrentTokenQNetwork.
    Architecture: token-set encoder + LSTM
    """
    brain_yaml = tmp_path / "brain.yaml"
    brain_yaml.write_text("""
version: "1.0"
description: "Recurrent brain config for POMDP tests"

architecture:
  type: recurrent
  recurrent:
    token_embed_dim: 64
    aggregator:
      type: mean
    lstm:
      hidden_size: 256
      num_layers: 1
      dropout: 0.0
    q_head_hidden_dim: 128

optimizer:
  type: adam
  learning_rate: 0.0003
  adam_beta1: 0.9
  adam_beta2: 0.999
  adam_eps: 1.0e-8
  weight_decay: 0.00001
  schedule:
    type: constant

loss:
  type: huber
  huber_delta: 1.0

q_learning:
  gamma: 0.99
  use_double_dqn: true
  target_update_frequency: 200

replay:
  capacity: 5000
  prioritized: false
""")
    return load_brain_config(tmp_path)
