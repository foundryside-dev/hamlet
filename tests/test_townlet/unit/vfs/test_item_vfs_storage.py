"""Tests for profile-driven item VFS storage."""

import torch

from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable
from townlet.vfs.registry import VariableRegistry


def test_registry_initializes_item_storage_from_profiles():
    """VariableRegistry should allocate item VFS storage from compiled profiles."""
    # Setup: Create compiled item profiles
    food_profile = CompiledItemProfile(
        profile_name="food_stats",
        variables=[
            CompiledVariable(
                name="calories",
                type="int",
                ast=None,
                initial_value=100,
                result_type="int",
                exposed_to=("agent",),
                semantic_type="custom",
            ),
            CompiledVariable(
                name="freshness",
                type="float",
                ast=None,
                initial_value=1.0,
                result_type="float",
                exposed_to=("agent",),
                semantic_type="custom",
            ),
        ],
    )

    weapon_profile = CompiledItemProfile(
        profile_name="weapon_stats",
        variables=[
            CompiledVariable(
                name="damage",
                type="int",
                ast=None,
                initial_value=50,
                result_type="int",
                exposed_to=("agent",),
                semantic_type="custom",
            ),
            CompiledVariable(
                name="durability",
                type="float",
                ast=None,
                initial_value=1.0,
                result_type="float",
                exposed_to=("agent",),
                semantic_type="custom",
            ),
        ],
    )

    item_profiles = {"food_stats": food_profile, "weapon_stats": weapon_profile}

    # Exercise: Initialize registry with profiles
    registry = VariableRegistry(
        variables=[],  # No global/agent vars for this test
        num_agents=4,
        device=torch.device("cpu"),
        max_items=10,
        item_profiles=item_profiles,  # NEW parameter
    )

    # Verify: Profile map exists
    assert hasattr(registry, "item_profile_map")
    assert "food_stats" in registry.item_profile_map
    assert "weapon_stats" in registry.item_profile_map

    # Verify: Map contains variable indices
    assert "calories" in registry.item_profile_map["food_stats"]
    assert "freshness" in registry.item_profile_map["food_stats"]
    assert registry.item_profile_map["food_stats"]["calories"] == 0
    assert registry.item_profile_map["food_stats"]["freshness"] == 1


def test_registry_item_storage_has_correct_shape():
    """Item VFS storage should have shape [max_items, max_profile_vars]."""
    # Setup: Profiles with different variable counts
    profile1 = CompiledItemProfile(
        profile_name="profile1",
        variables=[
            CompiledVariable(
                name="var1",
                type="int",
                ast=None,
                initial_value=0,
                result_type="int",
                exposed_to=("agent",),
                semantic_type="custom",
            ),
            CompiledVariable(
                name="var2",
                type="int",
                ast=None,
                initial_value=0,
                result_type="int",
                exposed_to=("agent",),
                semantic_type="custom",
            ),
        ],
    )

    profile2 = CompiledItemProfile(
        profile_name="profile2",
        variables=[
            CompiledVariable(
                name="var1",
                type="int",
                ast=None,
                initial_value=0,
                result_type="int",
                exposed_to=("agent",),
                semantic_type="custom",
            ),
        ],
    )

    # Exercise
    registry = VariableRegistry(
        variables=[],
        num_agents=4,
        device=torch.device("cpu"),
        max_items=10,
        item_profiles={"profile1": profile1, "profile2": profile2},
    )

    # Verify: Storage tensor shape
    # Shape should be [max_items, max_vars_across_all_profiles]
    assert registry.item_vfs is not None
    assert registry.item_vfs.shape == (10, 2)  # 10 items, 2 vars (max across profiles)
