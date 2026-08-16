"""Tests for VFS observation builder integration."""

import pytest
import torch

from townlet.config.vfs_profiles_config import (
    AgentVFSProfileConfig,
    AgentVFSVariableConfig,
    GlobalVFSProfileConfig,
    GlobalVFSVariableConfig,
)
from townlet.vfs.observation_builder import VFSObservationSpec, apply_normalization, build_vfs_observation
from townlet.vfs.registry import ScopedVariableRegistry
from townlet.vfs.schema import NormalizationSpec


def test_vfs_obs_spec_global_variables():
    """Global VFS variables contribute to obs_dim."""
    global_profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="day_count", type="int", initial_value=0),
            GlobalVFSVariableConfig(semantic_type="custom", name="is_night", type="bool", expression="tick % 24 >= 18"),
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
            AgentVFSVariableConfig(semantic_type="custom", name="motivation", type="float", initial_value=1.0),
            AgentVFSVariableConfig(semantic_type="custom", name="is_crisis", type="bool", expression="bar.energy < 0.2"),
            AgentVFSVariableConfig(semantic_type="custom", name="crisis_duration", type="int", initial_value=0),
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


def test_vfs_obs_spec_respects_exposed_to():
    """Only variables exposed to agents contribute to obs_dim."""
    from townlet.config.vfs_profiles_config import ItemVFSProfileConfig, ItemVFSVariableConfig

    global_profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="g_visible", type="int", initial_value=0, exposed_to=["agent"]),
            GlobalVFSVariableConfig(semantic_type="custom", name="g_hidden", type="int", initial_value=1, exposed_to=["engine"]),
        ]
    )
    agent_profile = AgentVFSProfileConfig(
        variables=[
            AgentVFSVariableConfig(semantic_type="custom", name="a_visible", type="bool", initial_value=True, exposed_to=["agent"]),
            AgentVFSVariableConfig(semantic_type="custom", name="a_hidden", type="bool", initial_value=False, exposed_to=["engine"]),
        ]
    )
    item_profile = ItemVFSProfileConfig(
        profile_name="item_stats",
        variables=[
            ItemVFSVariableConfig(name="i_visible", type="float", initial_value=0.5, exposed_to=["agent"]),
            ItemVFSVariableConfig(name="i_hidden", type="float", initial_value=0.1, exposed_to=["engine"]),
        ],
    )

    spec = VFSObservationSpec.from_profiles(
        global_profile=global_profile,
        agent_profile=agent_profile,
        item_profiles=[item_profile],
    )

    assert spec.global_vfs_dim == 1
    assert spec.agent_vfs_dim == 1
    assert spec.item_vfs_dim == spec.max_items_per_agent * 1  # only exposed item var counted
    assert spec.global_vars == ("g_visible",)
    assert spec.agent_vars == ("a_visible",)
    assert spec.item_profile_vars["item_stats"] == ("i_visible",)


def test_vfs_obs_spec_vecn_dimensions():
    """Variable dims are honored for vecNi/vecNf variables."""
    agent_profile = AgentVFSProfileConfig(
        variables=[
            AgentVFSVariableConfig(semantic_type="custom", name="heading", type="vecNi", dims=4, initial_value=[0, 0, 1, 0]),
        ]
    )

    spec = VFSObservationSpec.from_profiles(
        global_profile=None,
        agent_profile=agent_profile,
        item_profiles=[],
    )

    assert spec.agent_vfs_dim == 4


def test_apply_cyclical_sin_cos_normalization():
    """Cyclical normalization expands scalar time into sin/cos features."""
    values = torch.tensor([0.0, 6.0, 12.0])
    normalized = apply_normalization(values, NormalizationSpec(kind="cyclical_sin_cos", period=24.0))

    expected = torch.tensor(
        [
            [0.0, 1.0],
            [1.0, 0.0],
            [0.0, -1.0],
        ]
    )
    assert torch.allclose(normalized, expected, atol=1e-6)


def test_apply_discrete_and_mask_normalizations():
    """Binary, one-hot, and masked-value normalizations produce stable tensors."""
    binary = apply_normalization(torch.tensor([0.2, 0.7]), NormalizationSpec(kind="binary", threshold=0.5))
    one_hot = apply_normalization(torch.tensor([0, 2, 1]), NormalizationSpec(kind="one_hot", categories=3))
    masked = apply_normalization(torch.tensor([-1.0, 2.5]), NormalizationSpec(kind="masked_value", mask_value=-1.0, fill_value=0.0))

    assert torch.equal(binary, torch.tensor([0.0, 1.0]))
    assert torch.equal(
        one_hot,
        torch.tensor(
            [
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.0, 1.0, 0.0],
            ]
        ),
    )
    assert torch.equal(masked, torch.tensor([0.0, 2.5]))


def test_apply_log_and_rank_normalizations():
    """Log and rank normalization scale numeric tensors without hidden Python loops."""
    values = torch.tensor([0.0, 9.0, 99.0])
    log_scaled = apply_normalization(values, NormalizationSpec(kind="log_scaled", min=0.0, max=99.0, clip=False))
    clipped_log = apply_normalization(torch.tensor([-10.0, 999.0]), NormalizationSpec(kind="log_scaled", min=0.0, max=99.0, clip=True))
    ranked = apply_normalization(torch.tensor([20.0, 10.0, 30.0]), NormalizationSpec(kind="rank_scaled"))

    assert torch.allclose(log_scaled, torch.log1p(values) / torch.log1p(torch.tensor(99.0)))
    assert torch.allclose(clipped_log, torch.tensor([0.0, 1.0]))
    assert torch.equal(ranked, torch.tensor([0.5, 0.0, 1.0]))


def test_vfs_obs_spec_complete():
    """Complete VFS profile with global + agent + items."""
    from townlet.config.vfs_profiles_config import ItemVFSProfileConfig, ItemVFSVariableConfig

    spec = VFSObservationSpec.from_profiles(
        global_profile=GlobalVFSProfileConfig(
            variables=[
                GlobalVFSVariableConfig(semantic_type="custom", name="day_count", type="int", initial_value=0),
            ]
        ),
        agent_profile=AgentVFSProfileConfig(
            variables=[
                AgentVFSVariableConfig(semantic_type="custom", name="motivation", type="float", initial_value=1.0),
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
    registry.set_agent("target_ref", torch.tensor([1, 0, 2], dtype=torch.long))
    registry.set_agent("tensor_feat", torch.ones((3, 2, 2)))

    spec = VFSObservationSpec(
        global_vfs_dim=0,
        agent_vfs_dim=7,
        item_vfs_dim=0,
    )

    batch_size = 3
    obs = build_vfs_observation(registry, spec, batch_size)

    # Shape: [batch, total_vfs_dim] = [3, 7]
    assert obs.shape == (batch_size, 7)

    # Agent values per agent
    assert torch.equal(obs[:, 0], torch.tensor([1.0, 0.8, 1.2]))
    assert torch.equal(obs[:, 1], torch.tensor([0.0, 1.0, 0.0]))  # bool -> float
    assert torch.equal(obs[:, 2], torch.tensor([1.0, 0.0, 2.0]))  # long -> float
    assert torch.equal(obs[:, 3:], torch.ones(batch_size, 4))  # flattened tensor_feat


def test_build_vfs_observation_masks_curriculum_inactive_dimensions():
    """Inactive curriculum dimensions should stay in the ABI but emit zeros."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_global("visible_global", torch.tensor(5.0))
    registry.set_global("inactive_global", torch.tensor(7.0))
    registry.set_agent("visible_agent", torch.tensor([1.0, 2.0]))
    registry.set_agent("inactive_agent", torch.tensor([3.0, 4.0]))

    spec = VFSObservationSpec(
        global_vfs_dim=2,
        agent_vfs_dim=2,
        item_vfs_dim=0,
        global_vars=("visible_global", "inactive_global"),
        agent_vars=("visible_agent", "inactive_agent"),
        global_active_mask=(True, False),
        agent_active_mask=(True, False),
    )

    obs = build_vfs_observation(registry, spec, batch_size=2)

    assert obs.shape == (2, 4)
    assert torch.equal(obs, torch.tensor([[5.0, 0.0, 1.0, 0.0], [5.0, 0.0, 2.0, 0.0]]))


def test_build_vfs_observation_rejects_misaligned_active_mask():
    """A curriculum mask that no longer matches the ABI should fail loudly."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_global("visible_global", torch.tensor(5.0))
    registry.set_global("inactive_global", torch.tensor(7.0))

    spec = VFSObservationSpec(
        global_vfs_dim=2,
        agent_vfs_dim=0,
        item_vfs_dim=0,
        global_vars=("visible_global", "inactive_global"),
        global_active_mask=(True,),
    )

    with pytest.raises(ValueError, match="global_active_mask length 1 does not match global_vfs_dim 2"):
        build_vfs_observation(registry, spec, batch_size=2)


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


def test_build_vfs_observation_flattens_tensors():
    """Tensor-shaped values are flattened per agent."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    # Global 2x2 tensor -> 4 dims
    registry.set_global("matrix", torch.tensor([[1.0, 2.0], [3.0, 4.0]]))
    # Agent 2x2 tensor -> 4 dims
    registry.set_agent("embedding", torch.ones((3, 2, 2)))

    spec = VFSObservationSpec(
        global_vfs_dim=4,
        agent_vfs_dim=4,
        item_vfs_dim=0,
    )

    batch_size = 3
    obs = build_vfs_observation(registry, spec, batch_size)

    assert obs.shape == (batch_size, 8)
    # First four dims: broadcasted global tensor flattened
    expected_global = torch.tensor([[1.0, 2.0, 3.0, 4.0]]).expand(batch_size, -1)
    assert torch.equal(obs[:, :4], expected_global)
    # Next four dims: agent tensor flattened per agent
    assert torch.equal(obs[:, 4:], torch.ones(batch_size, 4))


def test_build_vfs_observation_raises_for_missing_item_profile_map():
    """A registered item profile must have a registry index map; typos are fatal."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.item_vfs = torch.tensor([[3.0]], dtype=torch.float32)
    registry.item_profile_map = {}
    registry.item_vfs_index_to_profile = {0: "missing_profile"}

    spec = VFSObservationSpec(
        global_vfs_dim=0,
        agent_vfs_dim=0,
        item_vfs_dim=1,
        item_profile_vars={"missing_profile": ("durability",)},
        max_items_per_agent=1,
    )

    with pytest.raises(RuntimeError, match="missing_profile"):
        build_vfs_observation(
            registry,
            spec,
            batch_size=1,
            agent_item_inventory=torch.tensor([[0]], dtype=torch.long),
        )


def test_vfs_observation_spec_tensor_dims_with_guardrail():
    """Spec computation respects tensor shape and guardrails."""
    global_profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="g_tensor", type="tensor1d", shape=[4], initial_value_mode="ones"),
        ]
    )

    spec = VFSObservationSpec.from_profiles(
        global_profile=global_profile,
        agent_profile=None,
        item_profiles=[],
    )

    assert spec.global_vfs_dim == 4
    assert spec.agent_vfs_dim == 0

    # Guardrail: too-large tensor should raise
    big_global_profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="big", type="tensor2d", shape=[2000, 2000], initial_value=0),
        ]
    )
    with pytest.raises(ValueError):
        VFSObservationSpec.from_profiles(
            global_profile=big_global_profile,
            agent_profile=None,
            item_profiles=[],
        )


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
                GlobalVFSVariableConfig(semantic_type="custom", name="tick", type="int", initial_value=0),
            ]
        ),
        agent_profile=AgentVFSProfileConfig(variables=[]),
        item_profiles=[],
    )

    # L1_full: full VFS
    l1_spec = VFSObservationSpec.from_profiles(
        global_profile=GlobalVFSProfileConfig(
            variables=[
                GlobalVFSVariableConfig(semantic_type="custom", name="tick", type="int", initial_value=0),
                GlobalVFSVariableConfig(semantic_type="custom", name="day_count", type="int", initial_value=0),
                GlobalVFSVariableConfig(semantic_type="custom", name="is_night", type="bool", expression="tick % 24 >= 18"),
            ]
        ),
        agent_profile=AgentVFSProfileConfig(
            variables=[
                AgentVFSVariableConfig(semantic_type="custom", name="motivation", type="float", initial_value=1.0),
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
