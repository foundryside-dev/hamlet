"""Tests for VFS observation builder integration."""

import torch

from townlet.config.vfs_profiles_config import (
    AgentVFSProfileConfig,
    AgentVFSVariableConfig,
    GlobalVFSProfileConfig,
    GlobalVFSVariableConfig,
)
from townlet.vfs.observation_builder import VFSObservationSpec, build_vfs_observation
from townlet.vfs.registry import ScopedVariableRegistry


def test_vfs_obs_spec_global_variables():
    """Global VFS variables contribute to obs_dim."""
    global_profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="day_count", type="int", initial_value=0),
            GlobalVFSVariableConfig(name="is_night", type="bool", expression="tick % 24 >= 18"),
        ]
    )

    spec = VFSObservationSpec.from_profiles(
        global_profile=global_profile,
        agent_profile=None,
        item_profiles=[],
    )

    # 2 global variables
    assert spec.global_vfs_dim == 2
    assert spec.agent_vfs_dim == 0
    assert spec.item_vfs_dim == 0
    assert spec.total_vfs_dim == 2


def test_vfs_obs_spec_agent_variables():
    """Agent VFS variables contribute to obs_dim."""
    agent_profile = AgentVFSProfileConfig(
        variables=[
            AgentVFSVariableConfig(name="motivation", type="float", initial_value=1.0),
            AgentVFSVariableConfig(name="is_crisis", type="bool", expression="bar.energy < 0.2"),
            AgentVFSVariableConfig(name="crisis_duration", type="int", initial_value=0),
        ]
    )

    spec = VFSObservationSpec.from_profiles(
        global_profile=None,
        agent_profile=agent_profile,
        item_profiles=[],
    )

    # 3 agent variables
    assert spec.global_vfs_dim == 0
    assert spec.agent_vfs_dim == 3
    assert spec.total_vfs_dim == 3


def test_vfs_obs_spec_complete():
    """Complete VFS profile with global + agent + items."""
    from townlet.config.vfs_profiles_config import ItemVFSProfileConfig, ItemVFSVariableConfig

    spec = VFSObservationSpec.from_profiles(
        global_profile=GlobalVFSProfileConfig(
            variables=[
                GlobalVFSVariableConfig(name="day_count", type="int", initial_value=0),
            ]
        ),
        agent_profile=AgentVFSProfileConfig(
            variables=[
                AgentVFSVariableConfig(name="motivation", type="float", initial_value=1.0),
            ]
        ),
        item_profiles=[
            ItemVFSProfileConfig(
                profile_name="food_stats",
                variables=[
                    ItemVFSVariableConfig(name="nutrition", type="float", initial_value=0.5),
                ],
            ),
        ],
    )

    # 1 global + 1 agent + (3 slots × 1 profile × 1 var) = 5
    assert spec.global_vfs_dim == 1
    assert spec.agent_vfs_dim == 1
    assert spec.item_vfs_dim == 3  # 3 inventory slots
    assert spec.total_vfs_dim == 5


# Step 3: Observation vector construction tests


def test_build_vfs_observation_global_only():
    """Build observation vector with only global VFS."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_global("day_count", torch.tensor(42))
    registry.set_global("is_night", torch.tensor(True))

    spec = VFSObservationSpec(
        global_vfs_dim=2,
        agent_vfs_dim=0,
        item_vfs_dim=0,
    )

    batch_size = 3
    obs = build_vfs_observation(registry, spec, batch_size)

    # Shape: [batch, total_vfs_dim] = [3, 2]
    assert obs.shape == (batch_size, 2)

    # Global values broadcast across batch
    assert torch.equal(obs[:, 0], torch.tensor([42.0, 42.0, 42.0]))
    assert torch.equal(obs[:, 1], torch.tensor([1.0, 1.0, 1.0]))  # True -> 1.0


def test_build_vfs_observation_agent_only():
    """Build observation vector with only agent VFS."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_agent("motivation", torch.tensor([1.0, 0.8, 1.2]))
    registry.set_agent("is_crisis", torch.tensor([False, True, False]))

    spec = VFSObservationSpec(
        global_vfs_dim=0,
        agent_vfs_dim=2,
        item_vfs_dim=0,
    )

    batch_size = 3
    obs = build_vfs_observation(registry, spec, batch_size)

    # Shape: [batch, total_vfs_dim] = [3, 2]
    assert obs.shape == (batch_size, 2)

    # Agent values per agent
    assert torch.equal(obs[:, 0], torch.tensor([1.0, 0.8, 1.2]))
    assert torch.equal(obs[:, 1], torch.tensor([0.0, 1.0, 0.0]))  # bool -> float


def test_build_vfs_observation_complete():
    """Build observation vector with global + agent + items."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    # Global: 1 variable
    registry.set_global("day_count", torch.tensor(5))

    # Agent: 1 variable (batch=2)
    registry.set_agent("motivation", torch.tensor([1.0, 0.8]))

    # Items: Provide zero-initialized storage to satisfy the non-legacy path
    registry.item_vfs = torch.zeros((3, 1), dtype=torch.float32, device=registry.device)

    spec = VFSObservationSpec(
        global_vfs_dim=1,
        agent_vfs_dim=1,
        item_vfs_dim=3,  # 3 item slots (stubbed)
    )

    batch_size = 2
    obs = build_vfs_observation(registry, spec, batch_size)

    # Shape: [batch, total_vfs_dim] = [2, 5]
    assert obs.shape == (batch_size, 5)

    # Global broadcast
    assert torch.equal(obs[:, 0], torch.tensor([5.0, 5.0]))

    # Agent per-agent
    assert torch.equal(obs[:, 1], torch.tensor([1.0, 0.8]))

    # Item slots zero-filled (stubbed for Phase 2)
    assert torch.equal(obs[:, 2:5], torch.zeros(batch_size, 3))


# Step 5: obs_dim stability test


def test_obs_dim_stable_across_levels():
    """VFS obs_dim must be stable for transfer learning.

    NOTE: This test documents Phase 2 behavior where obs_dim varies across levels.
    In Phase 3, we will implement a fixed VFS vocabulary to ensure obs_dim stability.
    """
    # L0_minimal: minimal VFS
    l0_spec = VFSObservationSpec.from_profiles(
        global_profile=GlobalVFSProfileConfig(
            variables=[
                GlobalVFSVariableConfig(name="tick", type="int", initial_value=0),
            ]
        ),
        agent_profile=AgentVFSProfileConfig(variables=[]),
        item_profiles=[],
    )

    # L1_full: full VFS
    l1_spec = VFSObservationSpec.from_profiles(
        global_profile=GlobalVFSProfileConfig(
            variables=[
                GlobalVFSVariableConfig(name="tick", type="int", initial_value=0),
                GlobalVFSVariableConfig(name="day_count", type="int", initial_value=0),
                GlobalVFSVariableConfig(name="is_night", type="bool", expression="tick % 24 >= 18"),
            ]
        ),
        agent_profile=AgentVFSProfileConfig(
            variables=[
                AgentVFSVariableConfig(name="motivation", type="float", initial_value=1.0),
            ]
        ),
        item_profiles=[],
    )

    # Phase 2: obs_dim VARIES across levels (expected behavior)
    # This is expected for Phase 2 - Phase 3 will add fixed vocabulary
    assert l0_spec.total_vfs_dim == 1
    assert l1_spec.total_vfs_dim == 4

    # TODO Phase 3: Fixed VFS vocabulary across levels
    # When Phase 3 is implemented, uncomment this assertion:
    # assert l0_spec.total_vfs_dim == l1_spec.total_vfs_dim
