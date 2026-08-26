"""StructuredQNetwork over caller-given semantic group slices.

The compiled `ObservationActivity` this network used to read its groups from was
deleted at the unit-3 token cut, and no `architecture.type` names this network, so it
is unreachable from any config pack — it dies with the unit-6 sweep. What is pinned
here is the seam that survived the cut: the network takes explicit `group_slices` and
builds one encoder per non-empty group.
"""

import pytest
import torch

from townlet.agent.networks import StructuredQNetwork

OBS_DIM = 24
ACTION_DIM = 6
GROUP_SLICES = {
    "spatial": slice(0, 8),
    "bars": slice(8, 16),
    "custom": slice(16, 24),
}


def _network(**overrides) -> StructuredQNetwork:
    kwargs = {"obs_dim": OBS_DIM, "action_dim": ACTION_DIM, "group_slices": GROUP_SLICES}
    kwargs.update(overrides)
    return StructuredQNetwork(**kwargs)


class TestStructuredQNetwork:
    def test_builds_one_encoder_per_declared_group(self) -> None:
        network = _network()
        assert set(network.group_encoders.keys()) == set(GROUP_SLICES)

    def test_empty_group_gets_no_encoder(self) -> None:
        # A zero-width group is not a defect; it simply contributes no encoder.
        network = _network(group_slices={**GROUP_SLICES, "effects": slice(24, 24)})
        assert "effects" not in network.group_encoders

    def test_forward_produces_q_values_per_action(self) -> None:
        network = _network()
        q_values = network(torch.randn(4, OBS_DIM))
        assert q_values.shape == (4, ACTION_DIM)

    def test_group_embed_dim_is_explicit(self) -> None:
        network = _network(group_embed_dim=8)
        assert network.group_embed_dim == 8
        assert network(torch.randn(2, OBS_DIM)).shape == (2, ACTION_DIM)

    def test_a_slice_past_the_observation_is_loud(self) -> None:
        network = _network(group_slices={"spatial": slice(0, OBS_DIM + 4)})
        with pytest.raises(RuntimeError):
            network(torch.randn(2, OBS_DIM))
