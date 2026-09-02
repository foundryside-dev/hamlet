"""Tests for ComposedActionSpace."""

import torch

from townlet.environment.action_builder import ComposedActionSpace
from townlet.environment.action_config import ActionConfig


def make_action(id: int, name: str, type: str, **overrides) -> ActionConfig:
    """Factory for creating ActionConfig in tests with explicit defaults.

    Centralizes ActionConfig creation so when fields change, we only update here.
    """
    defaults = {
        "id": id,
        "name": name,
        "type": type,
        "delta": None,
        "teleport_to": None,
        "costs": {},
        "effects": {},
        "enabled": True,
        "description": None,
        "icon": None,
        "source": "substrate",
        "source_affordance": None,
    }
    defaults.update(overrides)
    return ActionConfig(**defaults)


def test_composed_action_space_basic():
    """ComposedActionSpace should track actions and metadata."""
    actions = [
        make_action(0, "UP", "movement", delta=[0, -1]),
        make_action(1, "DOWN", "movement", delta=[0, 1]),
        make_action(2, "REST", "passive", source="custom"),
    ]

    space = ComposedActionSpace(
        actions=actions,
        substrate_action_count=2,
        custom_action_count=1,
        affordance_action_count=0,
        enabled_action_names=None,
    )

    assert space.action_dim == 3
    assert space.substrate_action_count == 2
    assert space.custom_action_count == 1


def test_composed_action_space_get_by_id():
    """Should retrieve action by ID."""
    actions = [
        make_action(0, "UP", "movement", delta=[0, -1]),
        make_action(1, "REST", "passive", source="custom"),
    ]

    space = ComposedActionSpace(
        actions=actions,
        substrate_action_count=1,
        custom_action_count=1,
        affordance_action_count=0,
        enabled_action_names=None,
    )

    assert space.get_action_by_id(0).name == "UP"
    assert space.get_action_by_id(1).name == "REST"


def test_composed_action_space_get_by_name():
    """Should retrieve action by name."""
    actions = [
        make_action(0, "UP", "movement", delta=[0, -1]),
        make_action(1, "REST", "passive", source="custom"),
    ]

    space = ComposedActionSpace(
        actions=actions,
        substrate_action_count=1,
        custom_action_count=1,
        affordance_action_count=0,
        enabled_action_names=None,
    )

    assert space.get_action_by_name("UP").id == 0
    assert space.get_action_by_name("REST").id == 1


def test_composed_action_space_enabled_count():
    """Should count enabled vs disabled actions."""
    actions = [
        make_action(0, "UP", "movement", delta=[0, -1]),
        make_action(1, "DOWN", "movement", delta=[0, 1]),
        make_action(2, "REST", "passive", source="custom"),
        make_action(3, "MEDITATE", "passive", enabled=False, source="custom"),  # Disabled
    ]

    space = ComposedActionSpace(
        actions=actions,
        substrate_action_count=2,
        custom_action_count=2,
        affordance_action_count=0,
        enabled_action_names={"UP", "DOWN", "REST"},  # MEDITATE not enabled
    )

    assert space.action_dim == 4  # Total actions (including disabled)
    assert space.enabled_action_count == 3  # Only enabled ones


def test_composed_action_space_get_base_mask():
    """Should generate action mask with disabled actions masked out."""
    actions = [
        make_action(0, "UP", "movement", delta=[0, -1]),
        make_action(1, "DOWN", "movement", delta=[0, 1]),
        make_action(2, "REST", "passive", source="custom"),
        make_action(3, "MEDITATE", "passive", enabled=False, source="custom"),  # Disabled
    ]

    space = ComposedActionSpace(
        actions=actions,
        substrate_action_count=2,
        custom_action_count=2,
        affordance_action_count=0,
        enabled_action_names=None,
    )

    mask = space.get_base_action_mask(num_agents=2, device=torch.device("cpu"))

    # Shape: [2 agents, 4 actions]
    assert mask.shape == (2, 4)

    # Actions 0, 1, 2 enabled (True)
    assert mask[0, 0]
    assert mask[0, 1]
    assert mask[0, 2]

    # Action 3 disabled (False)
    assert not mask[0, 3]
    assert not mask[1, 3]  # Disabled for all agents
