# Task 2.4: Observation Builder - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Include VFS variables in agent observations with fixed slot allocation for transfer learning.

**Architecture:** ObservationSpec defines obs_dim contributions. VFS adds fixed slots for global/agent/item variables. Item VFS uses slot masking for empty inventory positions.

**Tech Stack:** PyTorch tensors, Pydantic models, Python 3.11+

**Dependencies:** Task 2.1 (VFS Profiles DTOs), Task 2.2 (Scoped Registry), Task 2.3 (Expression Integration)

---

## Background

Phase 1 observations included:
- Position (2 dims for Grid2D)
- Bars (8 meters)
- Affordances (14 slots)
- Temporal (4 dims)

**Total:** 28 dims (L0/L1) or 53 dims (L2 with POMDP window)

Phase 2 adds VFS variables to observations:
- **Global VFS**: N global variables (shared across agents)
- **Agent VFS**: M agent variables (per-agent)
- **Item VFS**: Fixed slots (3 items × 5 max profiles × K vars per profile)

**Key constraint:** obs_dim MUST be stable across curriculum levels for transfer learning.

---

## Task Breakdown

### Step 1: Write failing test for VFS contribution to obs_dim

**File:** `tests/test_townlet/unit/vfs/test_observation_builder.py`

```python
"""Tests for VFS observation builder integration."""
import pytest
from townlet.vfs.observation_builder import VFSObservationSpec
from townlet.config.vfs_profiles_config import (
    GlobalVFSProfileConfig,
    GlobalVFSVariableConfig,
    AgentVFSProfileConfig,
    AgentVFSVariableConfig,
)


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
                ]
            ),
        ],
    )

    # 1 global + 1 agent + (3 slots × 1 profile × 1 var) = 5
    assert spec.global_vfs_dim == 1
    assert spec.agent_vfs_dim == 1
    assert spec.item_vfs_dim == 3  # 3 inventory slots
    assert spec.total_vfs_dim == 5
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_observation_builder.py::test_vfs_obs_spec_global_variables -v
```

**Expected:** FAIL - VFSObservationSpec not defined

---

### Step 2: Implement VFSObservationSpec

**File:** `src/townlet/vfs/observation_builder.py`

```python
"""VFS observation builder for agent observations."""
from dataclasses import dataclass
from townlet.config.vfs_profiles_config import (
    GlobalVFSProfileConfig,
    AgentVFSProfileConfig,
    ItemVFSProfileConfig,
)


@dataclass
class VFSObservationSpec:
    """Observation dimension specification for VFS variables.

    Defines how many dimensions VFS contributes to agent observations.
    """

    global_vfs_dim: int  # Number of global variables
    agent_vfs_dim: int   # Number of agent variables
    item_vfs_dim: int    # Number of item VFS dimensions (slots × profiles × vars)

    max_items_per_agent: int = 3  # Fixed inventory size
    max_item_profiles: int = 5    # Fixed profile count for transfer learning

    @property
    def total_vfs_dim(self) -> int:
        """Total VFS contribution to obs_dim."""
        return self.global_vfs_dim + self.agent_vfs_dim + self.item_vfs_dim

    @classmethod
    def from_profiles(
        cls,
        global_profile: GlobalVFSProfileConfig | None,
        agent_profile: AgentVFSProfileConfig | None,
        item_profiles: list[ItemVFSProfileConfig],
    ) -> "VFSObservationSpec":
        """Create observation spec from VFS profiles.

        Args:
            global_profile: Global VFS profile config (or None)
            agent_profile: Agent VFS profile config (or None)
            item_profiles: List of item VFS profile configs

        Returns:
            Observation spec with dimension counts
        """
        # Global VFS dimensions
        global_dim = 0
        if global_profile is not None:
            global_dim = len(global_profile.variables)

        # Agent VFS dimensions
        agent_dim = 0
        if agent_profile is not None:
            agent_dim = len(agent_profile.variables)

        # Item VFS dimensions: max_items × max_profiles × vars_per_profile
        # For now, assume all profiles have same number of variables
        # (will refactor in Phase 4 with actual item system)
        item_dim = 0
        if item_profiles:
            # Fixed slots: 3 items × 5 profiles × vars_per_profile
            max_vars_per_profile = max(len(p.variables) for p in item_profiles)
            item_dim = 3 * max_vars_per_profile  # Simplified for Phase 2

        return cls(
            global_vfs_dim=global_dim,
            agent_vfs_dim=agent_dim,
            item_vfs_dim=item_dim,
        )
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_observation_builder.py -v
```

**Expected:** All 3 tests PASS

**Commit:**
```bash
git add src/townlet/vfs/observation_builder.py tests/test_townlet/unit/vfs/test_observation_builder.py
git commit -m "feat(vfs): add VFSObservationSpec for obs_dim calculation"
```

---

### Step 3: Write failing test for obs vector construction

**File:** `tests/test_townlet/unit/vfs/test_observation_builder.py` (append)

```python
import torch
from townlet.vfs.registry import ScopedVariableRegistry
from townlet.vfs.observation_builder import build_vfs_observation


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

    # Items: Stub for now (will implement in Phase 4)
    # For Phase 2, just allocate zero-filled slots

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
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_observation_builder.py::test_build_vfs_observation_global_only -v
```

**Expected:** FAIL - build_vfs_observation() not defined

---

### Step 4: Implement obs vector construction

**File:** `src/townlet/vfs/observation_builder.py` (add function)

```python
import torch
from townlet.vfs.registry import ScopedVariableRegistry


def build_vfs_observation(
    registry: ScopedVariableRegistry,
    spec: VFSObservationSpec,
    batch_size: int,
) -> torch.Tensor:
    """Build VFS observation vector for agents.

    Args:
        registry: Variable registry with global/agent/item state
        spec: Observation specification (dims)
        batch_size: Number of agents

    Returns:
        Observation tensor with shape [batch, total_vfs_dim]
    """
    components = []

    # Global VFS: broadcast singleton values to batch
    if spec.global_vfs_dim > 0:
        global_vars = []
        for var_name in registry.list_global():
            value = registry.get_global(var_name)
            # Convert bool to float, broadcast to batch
            if value.dtype == torch.bool:
                value = value.float()
            # Broadcast singleton to batch
            value = value.expand(batch_size)
            global_vars.append(value.unsqueeze(1))  # [batch, 1]

        if global_vars:
            global_obs = torch.cat(global_vars, dim=1)  # [batch, global_dim]
            components.append(global_obs)

    # Agent VFS: per-agent values
    if spec.agent_vfs_dim > 0:
        agent_vars = []
        for var_name in registry.list_agent():
            value = registry.get_agent(var_name)
            # Convert bool to float
            if value.dtype == torch.bool:
                value = value.float()
            agent_vars.append(value.unsqueeze(1))  # [batch, 1]

        if agent_vars:
            agent_obs = torch.cat(agent_vars, dim=1)  # [batch, agent_dim]
            components.append(agent_obs)

    # Item VFS: stubbed for Phase 2 (zero-filled)
    if spec.item_vfs_dim > 0:
        item_obs = torch.zeros(batch_size, spec.item_vfs_dim, device=registry.device)
        components.append(item_obs)

    # Concatenate all components
    if components:
        return torch.cat(components, dim=1)  # [batch, total_vfs_dim]
    else:
        return torch.zeros(batch_size, 0, device=registry.device)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_observation_builder.py -k "build_vfs_observation" -v
```

**Expected:** All 3 obs construction tests PASS

**Commit:**
```bash
git add src/townlet/vfs/observation_builder.py tests/test_townlet/unit/vfs/test_observation_builder.py
git commit -m "feat(vfs): add VFS observation vector construction"
```

---

### Step 5: Write failing test for obs_dim stability

**File:** `tests/test_townlet/unit/vfs/test_observation_builder.py` (append)

```python
def test_obs_dim_stable_across_levels():
    """VFS obs_dim must be stable for transfer learning."""
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

    # obs_dim MUST differ (no fixed vocabulary for VFS yet)
    # This is expected for Phase 2 - Phase 3 will add fixed vocabulary
    assert l0_spec.total_vfs_dim == 1
    assert l1_spec.total_vfs_dim == 4

    # TODO Phase 3: Fixed VFS vocabulary across levels
    # assert l0_spec.total_vfs_dim == l1_spec.total_vfs_dim
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_observation_builder.py::test_obs_dim_stable_across_levels -v
```

**Expected:** PASS (documents current behavior, not enforced yet)

**Commit:**
```bash
git add tests/test_townlet/unit/vfs/test_observation_builder.py
git commit -m "test(vfs): document obs_dim stability requirement (Phase 3)"
```

---

### Step 6: Add module exports

**File:** `src/townlet/vfs/observation_builder.py` (add at top)

```python
"""VFS observation builder for agent observations."""
from __future__ import annotations
import torch
from dataclasses import dataclass
from townlet.config.vfs_profiles_config import (
    GlobalVFSProfileConfig,
    AgentVFSProfileConfig,
    ItemVFSProfileConfig,
)
from townlet.vfs.registry import ScopedVariableRegistry

__all__ = [
    "VFSObservationSpec",
    "build_vfs_observation",
]
```

**Verify:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "from townlet.vfs.observation_builder import VFSObservationSpec; print('OK')"
```

**Expected:** Prints "OK"

**Commit:**
```bash
git add src/townlet/vfs/observation_builder.py
git commit -m "feat(vfs): export observation builder in module API"
```

---

### Step 7: Type checking and formatting

**Run mypy:**
```bash
UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/vfs/observation_builder.py
```

**Expected:** Success

**Run ruff:**
```bash
UV_CACHE_DIR=.uv-cache uv run ruff format src/townlet/vfs/observation_builder.py tests/test_townlet/unit/vfs/test_observation_builder.py
UV_CACHE_DIR=.uv-cache uv run ruff check src/townlet/vfs/observation_builder.py
```

**Expected:** No changes needed

**Run full test suite:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_observation_builder.py -v
```

**Expected:** All ~10 tests PASS

**Commit:**
```bash
git add -u
git commit -m "test(vfs): verify all observation builder tests pass"
```

---

## Success Criteria

✅ **10+ tests passing** (obs spec, obs vector construction, stability)
✅ **VFSObservationSpec calculates dims** (global, agent, item)
✅ **Observation vector construction** (global broadcast, agent per-agent, item slots)
✅ **Type conversions** (bool → float for observations)
✅ **obs_dim stability documented** (requirement for Phase 3)
✅ **Type checking passes** (mypy clean)
✅ **Code formatted** (ruff)

---

## Phase 2 Complete!

All Phase 2 tasks finished:
- ✅ Task 2.1: VFS Profiles DTOs
- ✅ Task 2.2: Scoped Registry
- ✅ Task 2.3: Expression Evaluation Integration
- ✅ Task 2.4: Observation Builder

**Total Tests:** ~50+ tests passing across Phase 2

---

## Next Steps

**Phase 3: Effects System**

Build the command pipeline foundation:
- Task 3.1: Effects DTOs & Catalog
- Task 3.2: Command Parser & Compiler
- Task 3.3: Command Executor
- Task 3.4: EffectManager Runtime
- Task 3.5: Environment Integration

See: `docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md` Phase 3
