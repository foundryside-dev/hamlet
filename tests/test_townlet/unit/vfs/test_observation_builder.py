"""Tests for VFS observation builder integration."""

from townlet.config.vfs_profiles_config import (
    AgentVFSProfileConfig,
    AgentVFSVariableConfig,
    GlobalVFSProfileConfig,
    GlobalVFSVariableConfig,
)
from townlet.vfs.observation_builder import VFSObservationSpec


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
