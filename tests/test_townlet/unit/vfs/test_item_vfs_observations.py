"""Tests for item VFS observation builder."""

import pytest
import torch

from townlet.vfs.observation_builder import VFSObservationSpec, build_vfs_observation
from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable
from townlet.vfs.registry import VariableRegistry


def test_vfs_observation_includes_item_vfs_with_masking():
    """Observation builder should include item VFS with unused slot masking."""
    # Setup: Registry with 2 items per agent, 1 profile with 2 vars
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
            ),
            CompiledVariable(
                name="freshness",
                type="float",
                ast=None,
                initial_value=1.0,
                result_type="float",
                exposed_to=("agent",),
            ),
        ],
    )

    item_profiles = {"food_stats": food_profile}

    # Create registry
    registry = VariableRegistry(
        variables=[],  # No global/agent vars for this test
        num_agents=3,
        device=torch.device("cpu"),
        max_items=6,  # 3 agents × 2 slots
        item_profiles=item_profiles,
    )

    # Simulate inventory:
    # Agent 0 has 2 items at indices 0, 1
    # Agent 1 has 1 item at index 2
    # Agent 2 has 0 items
    # Initialize item VFS values
    registry.item_vfs[0, 0] = 100.0  # Agent 0, slot 0, calories
    registry.item_vfs[0, 1] = 0.9  # Agent 0, slot 0, freshness
    registry.item_vfs[1, 0] = 150.0  # Agent 0, slot 1, calories
    registry.item_vfs[1, 1] = 0.7  # Agent 0, slot 1, freshness
    registry.item_vfs[2, 0] = 200.0  # Agent 1, slot 0, calories
    registry.item_vfs[2, 1] = 0.5  # Agent 1, slot 0, freshness
    registry.register_item_instance(0, "food_stats")
    registry.register_item_instance(1, "food_stats")
    registry.register_item_instance(2, "food_stats")

    # Create inventory mapping: [batch, max_items_per_agent]
    # -1 means empty slot
    agent_item_inventory = torch.tensor(
        [
            [0, 1],  # Agent 0: items at vfs indices 0, 1
            [2, -1],  # Agent 1: item at vfs index 2, empty slot 1
            [-1, -1],  # Agent 2: both slots empty
        ],
        dtype=torch.long,
        device=torch.device("cpu"),
    )

    spec = VFSObservationSpec(
        global_vfs_dim=0,
        agent_vfs_dim=0,
        item_vfs_dim=4,  # 2 slots × 2 vars
        max_items_per_agent=2,
        max_item_profiles=1,
    )

    # Exercise
    obs = build_vfs_observation(registry, spec, batch_size=3, agent_item_inventory=agent_item_inventory)

    # Verify: Shape includes item VFS
    assert obs.shape == (3, 4)  # [batch, item_vfs_dim]

    # Verify: Agent 0 has both slots filled
    assert obs[0, 0].item() == pytest.approx(100.0)  # slot 0, calories
    assert obs[0, 1].item() == pytest.approx(0.9)  # slot 0, freshness
    assert obs[0, 2].item() == pytest.approx(150.0)  # slot 1, calories
    assert obs[0, 3].item() == pytest.approx(0.7)  # slot 1, freshness

    # Verify: Agent 1 has slot 0 filled, slot 1 masked
    assert obs[1, 0].item() == pytest.approx(200.0)  # slot 0, calories
    assert obs[1, 1].item() == pytest.approx(0.5)  # slot 0, freshness
    assert obs[1, 2].item() == 0.0  # slot 1 masked
    assert obs[1, 3].item() == 0.0  # slot 1 masked

    # Verify: Agent 2 has all slots masked
    assert obs[2, :].sum().item() == 0.0  # All masked


def test_vfs_observation_masks_curriculum_inactive_item_dimensions():
    """Inactive item dimensions should remain stable but emit zeros."""
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
            ),
            CompiledVariable(
                name="freshness",
                type="float",
                ast=None,
                initial_value=1.0,
                result_type="float",
                exposed_to=("agent",),
            ),
        ],
    )
    registry = VariableRegistry(
        variables=[],
        num_agents=2,
        device=torch.device("cpu"),
        max_items=2,
        item_profiles={"food_stats": food_profile},
    )
    registry.item_vfs[0, 0] = 100.0
    registry.item_vfs[0, 1] = 0.9
    registry.item_vfs[1, 0] = 150.0
    registry.item_vfs[1, 1] = 0.7
    registry.register_item_instance(0, "food_stats")
    registry.register_item_instance(1, "food_stats")

    spec = VFSObservationSpec(
        global_vfs_dim=0,
        agent_vfs_dim=0,
        item_vfs_dim=4,
        item_active_mask=(True, False, True, False),
        max_items_per_agent=2,
        max_item_profiles=1,
    )

    obs = build_vfs_observation(
        registry,
        spec,
        batch_size=2,
        agent_item_inventory=torch.tensor([[0, 1], [-1, -1]], dtype=torch.long),
    )

    assert torch.equal(obs, torch.tensor([[100.0, 0.0, 150.0, 0.0], [0.0, 0.0, 0.0, 0.0]]))


def test_vfs_observation_handles_no_item_inventory():
    """Observation builder should use zero stub when agent_item_inventory is None."""
    # Setup: Registry with item profiles
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
            ),
        ],
    )

    item_profiles = {"food_stats": food_profile}

    registry = VariableRegistry(
        variables=[],
        num_agents=3,
        device=torch.device("cpu"),
        max_items=6,
        item_profiles=item_profiles,
    )

    spec = VFSObservationSpec(
        global_vfs_dim=0,
        agent_vfs_dim=0,
        item_vfs_dim=2,  # 2 slots × 1 var
        max_items_per_agent=2,
        max_item_profiles=1,
    )

    # Exercise: Build observations without item_inventory (zero stub fallback)
    obs = build_vfs_observation(registry, spec, batch_size=3, agent_item_inventory=None)

    # Verify: Shape is correct
    assert obs.shape == (3, 2)

    # Verify: All values are zeros (stub behavior)
    assert obs.sum().item() == 0.0


def test_vfs_observation_handles_mixed_global_agent_item():
    """Observation builder should combine global, agent, and item VFS correctly."""
    # Setup: Use ScopedVariableRegistry for simpler interface
    from townlet.vfs.registry import ScopedVariableRegistry

    # Create scoped registry
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    # Set global variable
    registry.set_global("day_count", torch.tensor(5.0))

    # Set agent variables (2 agents)
    registry.set_agent("energy", torch.tensor([0.8, 0.6], dtype=torch.float32))

    # Set item VFS storage manually (simulating item profiles)
    registry.item_vfs = torch.zeros((4, 1), dtype=torch.float32, device=torch.device("cpu"))
    registry.item_vfs[0, 0] = 150.0  # Agent 0, slot 0
    registry.item_vfs[1, 0] = 200.0  # Agent 0, slot 1
    registry.item_profile_map = {"food_stats": {"nutrition": 0}}
    registry.item_vfs_index_to_profile = {0: "food_stats", 1: "food_stats"}

    # Create inventory
    agent_item_inventory = torch.tensor(
        [
            [0, 1],  # Agent 0: both slots filled
            [-1, -1],  # Agent 1: both slots empty
        ],
        dtype=torch.long,
        device=torch.device("cpu"),
    )

    spec = VFSObservationSpec(
        global_vfs_dim=1,
        agent_vfs_dim=1,
        item_vfs_dim=2,  # 2 slots × 1 var
        max_items_per_agent=2,
        max_item_profiles=1,
        item_profile_vars={"food_stats": ("nutrition",)},
    )

    # Exercise
    obs = build_vfs_observation(registry, spec, batch_size=2, agent_item_inventory=agent_item_inventory)

    # Verify: Shape is global + agent + item = 1 + 1 + 2 = 4
    assert obs.shape == (2, 4)

    # Verify: Agent 0 components
    assert obs[0, 0].item() == 5.0  # global: day_count
    assert obs[0, 1].item() == pytest.approx(0.8)  # agent: energy
    assert obs[0, 2].item() == pytest.approx(150.0)  # item slot 0
    assert obs[0, 3].item() == pytest.approx(200.0)  # item slot 1

    # Verify: Agent 1 components
    assert obs[1, 0].item() == 5.0  # global: day_count
    assert obs[1, 1].item() == pytest.approx(0.6)  # agent: energy
    assert obs[1, 2].item() == 0.0  # item slot 0 masked
    assert obs[1, 3].item() == 0.0  # item slot 1 masked


def test_item_vfs_observation_rejects_unregistered_row_profile():
    """An inventory row with no registered profile must fail loudly.

    HONEST NOTE: this passes on current production code — it is a *regression
    lock*, not a red-before pin. It exists because the guard it exercises had
    zero test coverage, and the tempting way to "fix" the broken benchmark
    fixture in ``tests/test_townlet/performance/test_component_benchmarks.py``
    was to soften this raise into a silent zero-fill.

    Verified: softening the raise makes the builder emit an all-zero item block
    for a slot that genuinely holds an item, so an agent carrying a full
    inventory observes an empty one and nothing anywhere reports it.
    """
    from townlet.vfs.registry import ScopedVariableRegistry

    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_global("day_count", torch.tensor(1.0))
    registry.set_agent("energy", torch.tensor([0.5], dtype=torch.float32))

    registry.item_vfs = torch.ones((2, 1), dtype=torch.float32)
    # Deliberately left unpopulated: row 0 is referenced by the inventory below
    # but maps to no profile.
    registry.item_profile_map = {"food_stats": {"nutrition": 0}}
    registry.item_vfs_index_to_profile = {}

    agent_item_inventory = torch.tensor([[0]], dtype=torch.long)

    spec = VFSObservationSpec(
        global_vfs_dim=1,
        agent_vfs_dim=1,
        item_vfs_dim=1,
        max_items_per_agent=1,
        max_item_profiles=1,
        item_profile_vars={"food_stats": ("nutrition",)},
    )

    with pytest.raises(RuntimeError, match="cannot resolve exposed variables"):
        build_vfs_observation(registry, spec, batch_size=1, agent_item_inventory=agent_item_inventory)
