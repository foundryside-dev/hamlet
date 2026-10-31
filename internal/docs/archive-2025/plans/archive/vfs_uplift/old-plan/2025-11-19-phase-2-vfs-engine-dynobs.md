# Items & VFS Profiles - Phase 2: VFS Engine + DynObs

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend VFS engine to handle scoped profiles (global/agent/item) and integrate into observation builder with masking.

**Architecture:** Modify VFS registry for profile scopes, extend observation builder to include VFS fields, add dimension regression tests for checkpoint compatibility.

**Tech Stack:** Python 3.13, PyTorch, Pydantic, pytest

**Prerequisites:**
- Phase 1 complete (DTOs + Compiler passing all tests)
- UniverseCompiler returns catalogs in CompiledUniverse
- All Phase 0 design decisions approved

**Estimated Time:** 24-32 hours implementation + 12-16 hours testing = 6-7 days

---

## Key Tasks Overview

1. **Extend VFS Registry for Scoped Profiles** (6-8 hours)
   - Add `scope` parameter to registry initialization
   - Separate storage for global/agent/item profiles
   - Access control enforcement per scope

2. **VFS Observation Spec Builder** (8-10 hours)
   - Generate observation layout from VFS profiles
   - Fixed slot allocation for item profiles (3 slots × 5 profiles = 15 dims)
   - Masking logic for empty slots

3. **DynObs Integration** (6-8 hours)
   - Wire VFS fields into environment observations
   - Implement masking for inactive profiles
   - Validate obs_dim matches compiled metadata

4. **Dimension Regression Tests** (4-6 hours)
   - Test obs_dim stability across all curriculum levels
   - Checkpoint compatibility verification
   - Phase 1 limits enforcement tests

---

## Task 1: Extend VFS Registry for Scoped Profiles

**Files:**
- Modify: `src/townlet/vfs/registry.py`
- Test: `tests/test_townlet/unit/vfs/test_scoped_registry.py`

### Implementation Steps

**Step 1: Write failing test for scoped registry**

```python
def test_scoped_registry_initialization():
    """Registry handles global/agent/item scopes separately."""
    vfs_config = VFSProfilesConfig(
        version="1.0",
        global_profiles=[
            GlobalVFSProfileConfig(
                id="global_flag", scope="global", type="scalar", initial_value=1.0
            )
        ],
        agent_profiles=[
            AgentVFSProfileConfig(
                id="agent_state", scope="agent", type="scalar", initial_value=0.0
            )
        ],
        item_profiles=[],
    )

    registry = VariableRegistry(
        vfs_profiles=vfs_config,
        num_agents=10,
        max_items=50,
        device=torch.device("cpu"),
    )

    # Global: shape [1]
    global_val = registry.get("global_flag", scope="global")
    assert global_val.shape == (1,)

    # Agent: shape [10] (replicated per agent)
    agent_val = registry.get("agent_state", scope="agent")
    assert agent_val.shape == (10,)
```

**Step 2: Modify VariableRegistry to support scopes**

```python
# src/townlet/vfs/registry.py

class VariableRegistry:
    """VFS variable registry with scoped storage (global/agent/item)."""

    def __init__(
        self,
        vfs_profiles: VFSProfilesConfig,
        num_agents: int,
        max_items: int,  # NEW: Phase 1 max_item_instances_total limit
        device: torch.device,
    ):
        self.device = device
        self.num_agents = num_agents
        self.max_items = max_items

        # Separate storage by scope
        self.global_storage: dict[str, torch.Tensor] = {}
        self.agent_storage: dict[str, torch.Tensor] = {}
        self.item_storage: dict[str, torch.Tensor] = {}

        # Initialize global profiles (shape: [1])
        for profile in vfs_profiles.global_profiles:
            self.global_storage[profile.id] = self._init_tensor(
                profile, shape_prefix=(1,)
            )

        # Initialize agent profiles (shape: [num_agents])
        for profile in vfs_profiles.agent_profiles:
            self.agent_storage[profile.id] = self._init_tensor(
                profile, shape_prefix=(num_agents,)
            )

        # Initialize item profiles (shape: [max_items])
        for profile in vfs_profiles.item_profiles:
            self.item_storage[profile.id] = self._init_tensor(
                profile, shape_prefix=(max_items,)
            )

    def _init_tensor(
        self, profile: VFSProfileConfig, shape_prefix: tuple[int, ...]
    ) -> torch.Tensor:
        """Initialize tensor from profile initial_value."""
        # Convert initial_value to tensor
        if isinstance(profile.initial_value, (int, float, bool)):
            value = torch.full(shape_prefix, profile.initial_value, device=self.device)
        elif isinstance(profile.initial_value, list):
            value = torch.tensor(profile.initial_value, device=self.device)
            value = value.unsqueeze(0).expand(*shape_prefix, -1)
        else:
            raise ValueError(f"Unsupported initial_value type: {type(profile.initial_value)}")
        return value

    def get(self, profile_id: str, scope: str, reader: str = "agent") -> torch.Tensor:
        """Get variable value with scope and access control."""
        # Select storage based on scope
        if scope == "global":
            storage = self.global_storage
        elif scope == "agent":
            storage = self.agent_storage
        elif scope == "item":
            storage = self.item_storage
        else:
            raise ValueError(f"Unknown scope: {scope}")

        # TODO: Access control enforcement (reader parameter)

        return storage[profile_id]
```

**Step 3-5:** Run tests, commit

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/unit/vfs/test_scoped_registry.py -v

git add src/townlet/vfs/registry.py tests/test_townlet/unit/vfs/test_scoped_registry.py
git commit -m "feat(vfs): add scoped registry (global/agent/item storage)"
```

---

## Task 2: VFS Observation Spec Builder

**Files:**
- Modify: `src/townlet/vfs/observation_builder.py`
- Test: `tests/test_townlet/unit/vfs/test_vfs_obs_spec_builder.py`

### Implementation Steps

**Step 1: Write test for VFS obs layout**

```python
def test_vfs_obs_layout_with_items():
    """Observation layout includes global/agent/item VFS fields."""
    vfs_config = VFSProfilesConfig(
        version="1.0",
        global_profiles=[
            GlobalVFSProfileConfig(id="g1", scope="global", type="scalar", initial_value=0.0),
        ],
        agent_profiles=[
            AgentVFSProfileConfig(id="a1", scope="agent", type="scalar", initial_value=0.0),
        ],
        item_profiles=[
            ItemVFSProfileConfig(id="i1", scope="item", type="scalar", initial_value=1.0),
            ItemVFSProfileConfig(id="i2", scope="item", type="scalar", initial_value=1.0),
        ],
    )

    builder = VFSObservationSpecBuilder(
        vfs_profiles=vfs_config,
        max_items_per_agent=3,  # Phase 1 limit
    )

    spec = builder.build_spec()

    # Verify layout
    assert spec.global_vfs_dims == 1  # 1 global profile
    assert spec.agent_vfs_dims == 1   # 1 agent profile
    assert spec.item_vfs_dims == 2 * 3  # 2 profiles × 3 slots = 6 dims
    assert spec.total_vfs_dims == 1 + 1 + 6  # 8 total
```

**Step 2: Implement VFSObservationSpecBuilder**

```python
# src/townlet/vfs/observation_builder.py

from dataclasses import dataclass

@dataclass
class VFSObservationSpec:
    """VFS contribution to observation vector."""
    global_vfs_dims: int
    agent_vfs_dims: int
    item_vfs_dims: int  # num_item_profiles × max_items_per_agent
    total_vfs_dims: int

    # Index ranges for each section
    global_vfs_slice: slice
    agent_vfs_slice: slice
    item_vfs_slice: slice


class VFSObservationSpecBuilder:
    """Build observation spec from VFS profiles (Phase 1: static layout)."""

    def __init__(
        self,
        vfs_profiles: VFSProfilesConfig | None,
        max_items_per_agent: int,
    ):
        self.vfs_profiles = vfs_profiles
        self.max_items_per_agent = max_items_per_agent

    def build_spec(self) -> VFSObservationSpec | None:
        """Build VFS observation spec with fixed layout."""
        if self.vfs_profiles is None:
            return None

        # Count dims per scope (Phase 1: all profiles are scalar = 1 dim)
        global_dims = len(self.vfs_profiles.global_profiles)
        agent_dims = len(self.vfs_profiles.agent_profiles)
        item_profile_count = len(self.vfs_profiles.item_profiles)

        # Phase 1: Reserve max_items_per_agent slots
        # Each slot gets ALL item profiles
        item_dims = item_profile_count * self.max_items_per_agent

        total_dims = global_dims + agent_dims + item_dims

        # Define index slices
        offset = 0
        global_slice = slice(offset, offset + global_dims)
        offset += global_dims

        agent_slice = slice(offset, offset + agent_dims)
        offset += agent_dims

        item_slice = slice(offset, offset + item_dims)

        return VFSObservationSpec(
            global_vfs_dims=global_dims,
            agent_vfs_dims=agent_dims,
            item_vfs_dims=item_dims,
            total_vfs_dims=total_dims,
            global_vfs_slice=global_slice,
            agent_vfs_slice=agent_slice,
            item_vfs_slice=item_slice,
        )
```

**Step 3-5:** Run tests, commit

---

## Task 3: DynObs Integration (Stub)

**Note:** Full DynObs integration requires environment changes (Phase 3). For Phase 2, we create the INTERFACE only.

**Files:**
- Create: `src/townlet/vfs/observation_assembly.py`
- Test: `tests/test_townlet/unit/vfs/test_observation_assembly.py`

### Implementation Steps

**Step 1: Write test for obs assembly**

```python
def test_assemble_vfs_observations():
    """Assemble VFS observations with masking for empty item slots."""
    # Create registry with values
    registry = VariableRegistry(...)

    # Agent inventory state: [has item in slot 0, empty slot 1, empty slot 2]
    inventory_mask = torch.tensor([[True, False, False]], dtype=torch.bool)

    obs = assemble_vfs_observations(
        registry=registry,
        agent_ids=[0],
        inventory_mask=inventory_mask,
        vfs_spec=spec,
    )

    # Verify shape
    assert obs.shape == (1, spec.total_vfs_dims)

    # Verify masking: slot 1 and 2 should be masked (0.0)
    # (exact indices depend on spec layout)
```

**Step 2: Implement assemble_vfs_observations**

```python
# src/townlet/vfs/observation_assembly.py

import torch

def assemble_vfs_observations(
    registry: VariableRegistry,
    agent_ids: list[int],
    inventory_mask: torch.Tensor,  # [batch, max_items_per_agent]
    vfs_spec: VFSObservationSpec,
) -> torch.Tensor:
    """Assemble VFS observations for agents with item slot masking.

    Args:
        registry: VFS variable registry
        agent_ids: Agent indices
        inventory_mask: Bool mask (True = slot has item, False = empty)
        vfs_spec: VFS observation spec

    Returns:
        obs: [batch, total_vfs_dims] observation tensor
    """
    batch_size = len(agent_ids)
    obs = torch.zeros(batch_size, vfs_spec.total_vfs_dims, device=registry.device)

    # Global VFS (broadcast to all agents)
    if vfs_spec.global_vfs_dims > 0:
        global_vals = ...  # Extract from registry
        obs[:, vfs_spec.global_vfs_slice] = global_vals

    # Agent VFS (per-agent values)
    if vfs_spec.agent_vfs_dims > 0:
        agent_vals = ...  # Extract from registry for agent_ids
        obs[:, vfs_spec.agent_vfs_slice] = agent_vals

    # Item VFS (masked by inventory)
    if vfs_spec.item_vfs_dims > 0:
        # For each slot, copy item VFS if inventory_mask[slot] == True
        # Otherwise leave as 0.0 (masked)
        ...  # Implementation details

    return obs
```

**Step 3-5:** Run tests, commit

---

## Task 4: Dimension Regression Tests

**Files:**
- Test: `tests/test_townlet/integration/test_vfs_obs_dimensions.py`

### Implementation Steps

**Step 1: Write dimension regression test**

```python
def test_obs_dim_stable_with_vfs_profiles():
    """Adding VFS profiles increases obs_dim predictably."""
    # Baseline: No VFS profiles
    obs_dim_baseline = compute_obs_dim(vfs_profiles=None, max_items_per_agent=0)

    # With VFS: 2 global + 2 agent + 0 items
    vfs_config_no_items = VFSProfilesConfig(
        version="1.0",
        global_profiles=[...],  # 2 profiles
        agent_profiles=[...],   # 2 profiles
        item_profiles=[],
    )
    obs_dim_vfs = compute_obs_dim(vfs_config_no_items, max_items_per_agent=0)

    # Should increase by 4 dims (2 global + 2 agent)
    assert obs_dim_vfs == obs_dim_baseline + 4

    # With items: 2 item profiles × 3 slots = 6 dims
    vfs_config_with_items = VFSProfilesConfig(
        version="1.0",
        global_profiles=[...],
        agent_profiles=[...],
        item_profiles=[...],  # 2 profiles
    )
    obs_dim_items = compute_obs_dim(vfs_config_with_items, max_items_per_agent=3)

    # Should increase by 4 + 6 = 10 dims total
    assert obs_dim_items == obs_dim_baseline + 10
```

**Step 2-5:** Implement helper, run tests, commit

---

## Completion Criteria

Phase 2 is complete when:

- [x] VFS registry supports scoped profiles (global/agent/item)
- [x] Observation spec builder generates fixed layout with item slots
- [x] Observation assembly function handles masking
- [x] Dimension regression tests pass for all curriculum levels
- [x] obs_dim computation matches compiled metadata
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Code review complete

---

## Final Commit

```bash
git add -A
git commit -m "feat(vfs): Phase 2 complete - VFS Engine + DynObs

Phase 2 Deliverables:
- Scoped VFS registry (global/agent/item storage)
- VFSObservationSpecBuilder with fixed item slot layout
- Observation assembly with inventory masking
- Dimension regression tests (obs_dim stability)

VFS Observation Layout (Phase 1):
- Global VFS: N global profiles
- Agent VFS: M agent profiles
- Item VFS: P item profiles × 3 slots (masked if empty)
- Total: N + M + (P × 3) additional dims

Ready for Phase 3 (Items Runtime + Inventory).
"
```

---

## Next Phase

**Phase 3: Items Runtime + Inventory**

See: `docs/plans/vfs_uplift/2025-11-19-phase-3-items-runtime.md`
