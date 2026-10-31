# Task 3: Item VFS Integration - Implementation Plan

> **For Claude:** REQUIRED EXECUTION SKILL: Use `superpowers:subagent-driven-development` to execute this plan task-by-task with code review between tasks.

**Goal:** Make item VFS profile-driven end-to-end with proper storage allocation, spawn/init logic, and observations

**Architecture:** Compile item profiles in UniverseCompiler, shape item VFS storage using compiled profiles (not variables_reference.yaml), integrate item VFS into observation builder with masking, and ensure ExecutionContext handles item-scoped variable access.

**Tech Stack:** PyTorch, Pydantic, existing VFS infrastructure, ItemManager

**Estimated Duration:** 2-3 days
**Test Target:** 5-7 new tests

---

## Context

**Current State (after Task 1 & Task 2):**
- ✅ VFS profiles compiled into `CompiledUniverse.compiled_vfs_profiles`
- ✅ Global VFS expressions evaluated at runtime
- ✅ Mark-and-sweep evaluation mode implemented
- ❌ Item profiles NOT compiled (TODO comment in compiler.py:181)
- ❌ Item VFS storage still allocated from `variables_reference.yaml` (not profiles)
- ❌ ItemManager ignores `vfs_profile` field on item types
- ❌ Item VFS observations are zero stubs (observation_builder.py:75)
- ❌ ExecutionContext has `self_is_item` path but no profile-scoped access

**Target State:**
- ✅ Item profiles compiled by UniverseCompiler
- ✅ Item VFS storage shaped by compiled profiles
- ✅ ItemManager assigns `vfs_profile` to instances
- ✅ ItemManager accepts `initial_state` for item VFS initialization
- ✅ ExecutionContext uses profile map for item variable access
- ✅ Observation builder includes item VFS with proper masking

---

## Subtask 3.1: Compile Item Profiles in UniverseCompiler

**Files:**
- Modify: `src/townlet/universe/compiler.py` (add item profile compilation)
- Modify: `src/townlet/vfs/profiles.py` (add CompiledItemProfile if not present)
- Modify: `src/townlet/universe/compiled.py` (update serialization for item_profiles)
- Test: `tests/test_townlet/unit/universe/test_item_profile_compilation.py` (new file)

**Duration:** ~0.5 days

### Step 3.1.1: Write failing test for item profile compilation

**Test:** `tests/test_townlet/unit/universe/test_item_profile_compilation.py`

```python
"""Tests for item profile compilation in UniverseCompiler."""

from pathlib import Path
import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler


def test_compiler_compiles_item_profiles(tmp_path: Path):
    """UniverseCompiler should compile item_profiles from vfs_profiles.yaml."""
    # Setup: Create config with item profiles
    from tests.test_townlet.unit.universe.config_builder import prepare_config_dir

    vfs_profiles = {
        "item_profiles": [
            {
                "profile_name": "food_stats",
                "variables": [
                    {"name": "calories", "type": "int", "initial_value": 100},
                    {"name": "freshness", "type": "float", "expression": "1.0"},
                ],
            },
            {
                "profile_name": "weapon_stats",
                "variables": [
                    {"name": "damage", "type": "int", "initial_value": 50},
                    {"name": "durability", "type": "float", "initial_value": 1.0},
                ],
            },
        ]
    }

    config_dir = prepare_config_dir(tmp_path, vfs_profiles=vfs_profiles)

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="test_level", use_cache=False)

    # Verify: Item profiles are compiled
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.item_profiles is not None
    assert "food_stats" in compiled.compiled_vfs_profiles.item_profiles
    assert "weapon_stats" in compiled.compiled_vfs_profiles.item_profiles

    # Verify: Profiles have correct structure
    food_profile = compiled.compiled_vfs_profiles.item_profiles["food_stats"]
    assert len(food_profile.variables) == 2
    assert food_profile.variables[0].name == "calories"
    assert food_profile.variables[1].name == "freshness"


def test_compiler_handles_missing_item_profiles():
    """UniverseCompiler should handle configs without item_profiles."""
    # Setup: Config without item_profiles
    # ... (minimal fixture)

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="test_level", use_cache=False)

    # Verify: No error, item_profiles is empty dict
    assert compiled.compiled_vfs_profiles is None or compiled.compiled_vfs_profiles.item_profiles == {}
```

**Expected:** Tests FAIL (item profiles not compiled yet)

### Step 3.1.2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_item_profile_compilation.py::test_compiler_compiles_item_profiles -xvs
```

**Expected Output:**
```
FAILED - AssertionError: item_profiles is empty
```

### Step 3.1.3: Add CompiledItemProfile to vfs/profiles.py (if needed)

**File:** `src/townlet/vfs/profiles.py`

Check if CompiledItemProfile already exists. If not, add it:

```python
# After CompiledGlobalProfile definition

@dataclass(frozen=True)
class CompiledItemProfile:
    """Compiled item VFS profile with variables in topological order."""

    profile_name: str  # Profile name (e.g., "food_stats")
    variables: list[CompiledVariable]  # Variables in dependency order

    def __post_init__(self):
        # Make variables tuple for immutability
        if not isinstance(self.variables, tuple):
            object.__setattr__(self, "variables", tuple(self.variables))
```

**Location:** After CompiledGlobalProfile definition (around line 80)

### Step 3.1.4: Update VFSProfileCompiler to compile item profiles

**File:** `src/townlet/vfs/profiles.py`

Add method to compile item profiles:

```python
# In VFSProfileCompiler class, after compile_global_profile method

def compile_item_profile(
    self,
    profile: ItemVFSProfileConfig,
    bar_schema: dict[str, str],
) -> CompiledItemProfile:
    """Compile item VFS profile.

    Args:
        profile: Item profile config from vfs_profiles.yaml
        bar_schema: Type schema for bars (for expression type checking)

    Returns:
        Compiled item profile with variables in topological order

    Raises:
        ValueError: If circular dependencies detected
    """
    # Build variable schema (item profiles can't reference global/agent vars)
    var_schema: dict[str, str] = {}

    # Items can reference bars but not global/agent VFS
    # (items are isolated instances)
    var_schema.update(bar_schema)

    # Parse and validate variable expressions
    compiled_vars: list[CompiledVariable] = []

    for var_config in profile.variables:
        ast_node = None
        if var_config.expression is not None:
            # Parse expression
            ast_node = self._parser.parse(var_config.expression)

            # Type check
            inferred_type = self._type_checker.check(ast_node, var_schema)

            # Validate type matches declaration
            if var_config.type != inferred_type:
                raise TypeError(
                    f"Item variable '{var_config.name}' type mismatch: "
                    f"declared '{var_config.type}' but expression returns '{inferred_type}'"
                )

        # Add to schema for later variables
        var_schema[var_config.name] = var_config.type

        compiled_vars.append(
            CompiledVariable(
                name=var_config.name,
                type=var_config.type,
                ast=ast_node,
                initial_value=var_config.initial_value,
                result_type=var_config.type,
            )
        )

    # Sort variables in topological order
    sorted_vars = self._sort_variables_topo(compiled_vars)

    return CompiledItemProfile(
        profile_name=profile.profile_name,
        variables=sorted_vars,
    )
```

**Location:** After `compile_global_profile` method

### Step 3.1.5: Update UniverseCompiler to compile item profiles

**File:** `src/townlet/universe/compiler.py`

Update `_compile_vfs_profiles` method to compile item profiles:

```python
# In _compile_vfs_profiles method, replace the TODO comment (line 181-186)

# Compile item profiles
compiled_item_profiles: dict[str, CompiledItemProfile] = {}
if profiles_config.item_profiles:
    for item_profile_config in profiles_config.item_profiles:
        compiled_profile = compiler.compile_item_profile(
            item_profile_config,
            bar_schema=bar_schema,
        )
        compiled_item_profiles[compiled_profile.profile_name] = compiled_profile

return CompiledVFSProfiles(
    global_profile=compiled_global,
    agent_profile=None,  # TODO: Task 4 or later
    item_profiles=compiled_item_profiles,
)
```

**Location:** Replace lines 181-187 in compiler.py

### Step 3.1.6: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_item_profile_compilation.py -xvs
```

**Expected:** PASS (2/2 tests)

### Step 3.1.7: Commit item profile compilation

```bash
git add src/townlet/vfs/profiles.py src/townlet/universe/compiler.py tests/test_townlet/unit/universe/test_item_profile_compilation.py
git commit -m "feat(compiler): add item profile compilation to UniverseCompiler

- Add CompiledItemProfile dataclass to vfs/profiles.py
- Add compile_item_profile() method to VFSProfileCompiler
- Compile all item_profiles from vfs_profiles.yaml
- Store compiled profiles in CompiledVFSProfiles.item_profiles dict
- Tests verify profile compilation and empty handling

Task 3.1 complete (Item profile compilation)"
```

---

## Subtask 3.2: Profile-Driven Item VFS Storage

**Files:**
- Modify: `src/townlet/vfs/registry.py` (add profile-driven initialization)
- Modify: `src/townlet/environment/vectorized_env.py` (use compiled profiles for item storage)
- Test: `tests/test_townlet/unit/vfs/test_item_vfs_storage.py` (new file)

**Duration:** ~1 day

### Step 3.2.1: Write failing test for profile-driven storage

**Test:** `tests/test_townlet/unit/vfs/test_item_vfs_storage.py`

```python
"""Tests for profile-driven item VFS storage."""

import torch
import pytest

from townlet.vfs.registry import VariableRegistry
from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable


def test_registry_initializes_item_storage_from_profiles():
    """VariableRegistry should allocate item VFS storage from compiled profiles."""
    # Setup: Create compiled item profiles
    food_profile = CompiledItemProfile(
        profile_name="food_stats",
        variables=[
            CompiledVariable(name="calories", type="int", ast=None, initial_value=100, result_type="int"),
            CompiledVariable(name="freshness", type="float", ast=None, initial_value=1.0, result_type="float"),
        ],
    )

    weapon_profile = CompiledItemProfile(
        profile_name="weapon_stats",
        variables=[
            CompiledVariable(name="damage", type="int", ast=None, initial_value=50, result_type="int"),
            CompiledVariable(name="durability", type="float", ast=None, initial_value=1.0, result_type="float"),
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
            CompiledVariable(name="var1", type="int", ast=None, initial_value=0, result_type="int"),
            CompiledVariable(name="var2", type="int", ast=None, initial_value=0, result_type="int"),
        ],
    )

    profile2 = CompiledItemProfile(
        profile_name="profile2",
        variables=[
            CompiledVariable(name="var1", type="int", ast=None, initial_value=0, result_type="int"),
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
```

**Expected:** Tests FAIL (item_profiles parameter doesn't exist yet)

### Step 3.2.2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_item_vfs_storage.py::test_registry_initializes_item_storage_from_profiles -xvs
```

**Expected Output:**
```
FAILED - TypeError: __init__() got an unexpected keyword argument 'item_profiles'
```

### Step 3.2.3: Update VariableRegistry to accept item_profiles

**File:** `src/townlet/vfs/registry.py`

Update `__init__` signature and add profile-driven initialization:

```python
# In VariableRegistry.__init__, update signature (around line 50)

def __init__(
    self,
    variables: list[VariableDef],
    num_agents: int,
    device: torch.device,
    max_items: int = 0,
    item_profiles: dict[str, Any] | None = None,  # NEW: Compiled item profiles
):
    """Initialize variable registry.

    Args:
        variables: List of variable definitions (global, agent)
        num_agents: Number of agents in the environment
        device: PyTorch device (cpu or cuda)
        max_items: Maximum items (for item-scoped variables)
        item_profiles: Compiled item profiles (profile_name → CompiledItemProfile)
    """
    self.num_agents = num_agents
    self.max_items = max_items
    self.device = device
    self.item_profiles = item_profiles or {}  # Store compiled profiles

    # ... existing code ...

    # Initialize item-scoped storage with profiles
    self.item_vfs: torch.Tensor | None = None
    self.item_profile_map: dict[str, dict[str, int]] = {}  # {profile_name → {var_name → index}}
    self._initialize_item_storage_from_profiles()
```

**Location:** Update __init__ signature and body (lines 50-86)

### Step 3.2.4: Implement profile-driven item storage initialization

**File:** `src/townlet/vfs/registry.py`

Replace `_initialize_item_storage` method with `_initialize_item_storage_from_profiles`:

```python
# Replace _initialize_item_storage method (was at line 250+)

def _initialize_item_storage_from_profiles(self) -> None:
    """Initialize item VFS storage from compiled profiles.

    Creates:
    - item_vfs: [max_items, max_profile_vars] tensor
    - item_profile_map: {profile_name → {var_name → tensor_index}}

    Item storage is profile-agnostic: all profiles share the same tensor layout
    using max_profile_vars across all profiles. Unused slots are masked.
    """
    if self.max_items == 0 or not self.item_profiles:
        # No items or no profiles
        self.item_vfs = None
        self.item_profile_map = {}
        return

    # Calculate max variables across all profiles
    max_vars = 0
    for profile in self.item_profiles.values():
        max_vars = max(max_vars, len(profile.variables))

    # Allocate storage: [max_items, max_vars]
    self.item_vfs = torch.zeros(
        (self.max_items, max_vars),
        dtype=torch.float32,
        device=self.device,
    )

    # Build profile map: {profile_name → {var_name → index}}
    for profile_name, profile in self.item_profiles.items():
        var_map = {}
        for idx, var in enumerate(profile.variables):
            var_map[var.name] = idx
        self.item_profile_map[profile_name] = var_map
```

**Location:** Replace old `_initialize_item_storage` method

### Step 3.2.5: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_item_vfs_storage.py -xvs
```

**Expected:** PASS (2/2 tests)

### Step 3.2.6: Update vectorized_env to pass item_profiles to registry

**File:** `src/townlet/environment/vectorized_env.py`

Update VariableRegistry initialization to use compiled item profiles:

```python
# In __init__, when creating VariableRegistry (around line 280)

# Extract item profiles from compiled universe
item_profiles = None
if compiled_universe.compiled_vfs_profiles is not None:
    item_profiles = compiled_universe.compiled_vfs_profiles.item_profiles

# Initialize VFS registry with profile-driven item storage
self.vfs_registry = VariableRegistry(
    variables=vfs_variables,
    num_agents=num_agents,
    device=self.device,
    max_items=max_items_per_agent * num_agents,  # Total items in world
    item_profiles=item_profiles,  # NEW: Pass compiled profiles
)
```

**Location:** Update VariableRegistry initialization (around line 280)

### Step 3.2.7: Commit profile-driven storage

```bash
git add src/townlet/vfs/registry.py src/townlet/environment/vectorized_env.py tests/test_townlet/unit/vfs/test_item_vfs_storage.py
git commit -m "feat(vfs): add profile-driven item VFS storage

- Add item_profiles parameter to VariableRegistry.__init__
- Implement _initialize_item_storage_from_profiles()
- Allocate storage as [max_items, max_vars] tensor
- Build item_profile_map: {profile_name → {var_name → index}}
- Update vectorized_env to pass compiled item profiles
- Tests verify storage allocation and profile map

Task 3.2 complete (Profile-driven storage)"
```

---

## Subtask 3.3: ItemManager VFS Profile Integration

**Files:**
- Modify: `src/townlet/items/manager.py` (assign vfs_profile, accept initial_state)
- Test: `tests/test_townlet/unit/items/test_item_vfs_profile_assignment.py` (new file)

**Duration:** ~0.5 days

### Step 3.3.1: Write failing test for profile assignment

**Test:** `tests/test_townlet/unit/items/test_item_vfs_profile_assignment.py`

```python
"""Tests for ItemManager VFS profile assignment."""

import torch
import pytest

from townlet.items.manager import ItemManager
from townlet.config.items_config import ItemsCatalogConfig
from townlet.vfs.registry import VariableRegistry


def test_item_manager_assigns_vfs_profile_on_spawn():
    """ItemManager should assign vfs_profile from item type on spawn."""
    # Setup: Catalog with item types that have vfs_profile
    catalog = ItemsCatalogConfig(
        item_types=[
            {
                "id": "apple",
                "vfs_profile": "food_stats",
                "interactions": {"on_pickup": [], "on_use": [], "on_drop": []},
            }
        ],
        appearance={"spawn_rate": 0.1, "max_items_per_agent": 3},
    )

    # Create registry with food_stats profile
    # ... (setup registry with compiled profile)

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device=torch.device("cpu"),
        vfs_registry=registry,
    )

    # Exercise: Spawn an apple
    instance = manager.spawn_item(
        item_type="apple",
        position=(0, 0),
        spawn_tick=0,
    )

    # Verify: Instance has vfs_profile assigned
    assert instance.vfs_profile == "food_stats"


def test_item_manager_accepts_initial_state():
    """ItemManager should accept initial_state for item VFS initialization."""
    # Setup: Same as above
    # ...

    # Exercise: Spawn with initial_state
    instance = manager.spawn_item(
        item_type="apple",
        position=(0, 0),
        spawn_tick=0,
        initial_state={"calories": 150, "freshness": 0.8},  # Override defaults
    )

    # Verify: VFS state initialized with custom values
    # (Check registry storage at instance.vfs_index)
    vfs_values = registry.get_item_vfs(instance.vfs_index, profile_name="food_stats")
    assert vfs_values["calories"].item() == 150
    assert vfs_values["freshness"].item() == pytest.approx(0.8)
```

**Expected:** Tests FAIL (spawn_item doesn't support initial_state)

### Step 3.3.2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/items/test_item_vfs_profile_assignment.py::test_item_manager_assigns_vfs_profile_on_spawn -xvs
```

**Expected Output:**
```
FAILED - AttributeError: 'ItemInstance' has no attribute 'vfs_profile'
```

### Step 3.3.3: Update ItemInstance to include vfs_profile

**File:** `src/townlet/items/instance.py`

Add vfs_profile field:

```python
@dataclass
class ItemInstance:
    """Runtime instance of an item in the world."""

    item_type: str  # Reference to ItemTypeConfig.id
    instance_id: int  # Unique instance ID
    position: tuple[int, ...] | tuple[float, ...]  # Spatial position
    vfs_index: int  # Index into item_vfs tensor

    vfs_profile: str  # NEW: VFS profile name (e.g., "food_stats")

    spawn_tick: int  # When item was spawned
    duration_total: int | None  # Total lifetime
    duration_remaining: int | None  # Ticks until despawn

    # ... existing methods ...
```

**Location:** Add field after `vfs_index` (line 19)

### Step 3.3.4: Update ItemManager.spawn_item to assign profile and initial_state

**File:** `src/townlet/items/manager.py`

Update `spawn_item` method signature and implementation:

```python
# In ItemManager class, update spawn_item method (around line 120)

def spawn_item(
    self,
    item_type: str,
    position: tuple[int, ...] | tuple[float, ...],
    spawn_tick: int,
    initial_state: dict[str, float | int] | None = None,  # NEW: VFS initial values
) -> ItemInstance:
    """Spawn a new item instance.

    Args:
        item_type: Item type ID (must exist in catalog)
        position: Spatial position
        spawn_tick: Current tick
        initial_state: Optional VFS initial values {var_name → value}

    Returns:
        Newly spawned ItemInstance

    Raises:
        ValueError: If item_type not in catalog
        RuntimeError: If max_items exceeded
    """
    # Find item type in catalog
    item_config = None
    for item_type_config in self.catalog.item_types:
        if item_type_config.id == item_type:
            item_config = item_type_config
            break

    if item_config is None:
        raise ValueError(f"Item type '{item_type}' not found in catalog")

    # Allocate VFS index
    vfs_index = self._allocate_vfs_index()

    # Initialize VFS state from profile defaults + initial_state overrides
    if self.vfs_registry is not None and item_config.vfs_profile:
        profile_name = item_config.vfs_profile

        # Get profile from registry
        if profile_name not in self.vfs_registry.item_profile_map:
            raise ValueError(f"VFS profile '{profile_name}' not found in registry")

        profile_map = self.vfs_registry.item_profile_map[profile_name]

        # Initialize with defaults from compiled profile
        # (defaults are already set in tensor initialization)

        # Apply initial_state overrides if provided
        if initial_state is not None:
            for var_name, value in initial_state.items():
                if var_name not in profile_map:
                    raise ValueError(
                        f"Variable '{var_name}' not in profile '{profile_name}'"
                    )
                var_idx = profile_map[var_name]
                self.vfs_registry.item_vfs[vfs_index, var_idx] = float(value)

    # Create instance
    instance = ItemInstance(
        item_type=item_type,
        instance_id=self._next_instance_id,
        position=position,
        vfs_index=vfs_index,
        vfs_profile=item_config.vfs_profile,  # NEW: Assign profile
        spawn_tick=spawn_tick,
        duration_total=item_config.duration,
        duration_remaining=item_config.duration,
    )

    self._next_instance_id += 1
    self.instances[instance.instance_id] = instance

    return instance
```

**Location:** Update spawn_item method (around line 120)

### Step 3.3.5: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/items/test_item_vfs_profile_assignment.py -xvs
```

**Expected:** PASS (2/2 tests)

### Step 3.3.6: Commit ItemManager profile integration

```bash
git add src/townlet/items/instance.py src/townlet/items/manager.py tests/test_townlet/unit/items/test_item_vfs_profile_assignment.py
git commit -m "feat(items): integrate VFS profiles into ItemManager

- Add vfs_profile field to ItemInstance
- Add initial_state parameter to spawn_item()
- Assign vfs_profile from item type on spawn
- Initialize item VFS state with profile defaults
- Apply initial_state overrides if provided
- Tests verify profile assignment and initial_state

Task 3.3 complete (ItemManager integration)"
```

---

## Subtask 3.4: Update Observation Builder for Item VFS

**Files:**
- Modify: `src/townlet/vfs/observation_builder.py` (add item VFS with masking)
- Test: `tests/test_townlet/unit/vfs/test_item_vfs_observations.py` (new file)

**Duration:** ~0.5 days

### Step 3.4.1: Write failing test for item VFS observations

**Test:** `tests/test_townlet/unit/vfs/test_item_vfs_observations.py`

```python
"""Tests for item VFS observation builder."""

import torch
import pytest

from townlet.vfs.observation_builder import VFSObservationSpec, build_vfs_observation
from townlet.vfs.registry import VariableRegistry


def test_vfs_observation_includes_item_vfs_with_masking():
    """Observation builder should include item VFS with unused slot masking."""
    # Setup: Registry with 2 items per agent, 1 profile with 2 vars
    # ... (create registry with item profiles)

    # Agent 0 has 2 items, Agent 1 has 1 item, Agent 2 has 0 items
    # ... (populate item_vfs tensor)

    spec = VFSObservationSpec(
        global_vfs_dim=0,
        agent_vfs_dim=0,
        item_vfs_dim=4,  # 2 slots × 2 vars
        max_items_per_agent=2,
        max_item_profiles=1,
    )

    # Exercise
    obs = build_vfs_observation(registry, spec, batch_size=3)

    # Verify: Shape includes item VFS
    assert obs.shape == (3, 4)  # [batch, item_vfs_dim]

    # Verify: Unused slots are masked (zeros)
    # Agent 0: slots 0,1 filled
    # Agent 1: slot 0 filled, slot 1 masked
    # Agent 2: slots 0,1 masked
    assert obs[1, 2:4].sum() == 0  # Agent 1 slot 1 masked
    assert obs[2, :].sum() == 0  # Agent 2 all masked
```

**Expected:** Test FAILS (item VFS not included in observations)

### Step 3.4.2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_item_vfs_observations.py::test_vfs_observation_includes_item_vfs_with_masking -xvs
```

**Expected Output:**
```
FAILED - AssertionError: Item VFS not in observations (zero stub)
```

### Step 3.4.3: Update build_vfs_observation to include item VFS

**File:** `src/townlet/vfs/observation_builder.py`

Update `build_vfs_observation` function to include item VFS:

```python
# In build_vfs_observation function (around line 98)

def build_vfs_observation(
    registry: ScopedVariableRegistry,
    spec: VFSObservationSpec,
    batch_size: int,
    agent_item_inventory: torch.Tensor | None = None,  # NEW: [batch, max_items_per_agent] item indices
) -> torch.Tensor:
    """Build VFS observation vector for agents.

    Args:
        registry: Variable registry with global/agent/item state
        spec: Observation specification (dims)
        batch_size: Number of agents
        agent_item_inventory: Item indices for each agent slot (or None for zero stubs)

    Returns:
        Observation tensor with shape [batch, total_vfs_dim]
    """
    components = []

    # Global VFS (unchanged)
    if spec.global_vfs_dim > 0:
        # ... existing code ...
        components.append(global_obs)

    # Agent VFS (unchanged)
    if spec.agent_vfs_dim > 0:
        # ... existing code ...
        components.append(agent_obs)

    # Item VFS (NEW: Include item state with masking)
    if spec.item_vfs_dim > 0:
        if agent_item_inventory is None:
            # No item system yet, use zero stub
            item_obs = torch.zeros(
                (batch_size, spec.item_vfs_dim),
                dtype=torch.float32,
                device=registry.device,
            )
        else:
            # Build item observations with masking
            # Shape: [batch, max_items_per_agent, max_vars_per_profile]
            item_vfs_slices = []

            for agent_idx in range(batch_size):
                agent_slots = []
                for slot_idx in range(spec.max_items_per_agent):
                    item_idx = agent_item_inventory[agent_idx, slot_idx].item()

                    if item_idx == -1:  # Empty slot
                        # Masked slot: all zeros
                        agent_slots.append(
                            torch.zeros(
                                spec.item_vfs_dim // spec.max_items_per_agent,
                                dtype=torch.float32,
                                device=registry.device,
                            )
                        )
                    else:
                        # Extract item VFS state
                        item_vfs = registry.item_vfs[item_idx, :]
                        agent_slots.append(item_vfs)

                # Flatten slots: [max_items × vars]
                item_vfs_slices.append(torch.cat(agent_slots))

            item_obs = torch.stack(item_vfs_slices)  # [batch, item_vfs_dim]

        components.append(item_obs)

    # Concatenate all components
    if not components:
        # No VFS observations
        return torch.zeros((batch_size, 0), dtype=torch.float32, device=registry.device)

    return torch.cat(components, dim=-1)
```

**Location:** Update build_vfs_observation function (around line 83)

### Step 3.4.4: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_item_vfs_observations.py -xvs
```

**Expected:** PASS

### Step 3.4.5: Commit observation builder updates

```bash
git add src/townlet/vfs/observation_builder.py tests/test_townlet/unit/vfs/test_item_vfs_observations.py
git commit -m "feat(vfs): add item VFS to observations with masking

- Update build_vfs_observation to include item VFS
- Add agent_item_inventory parameter for item slot mapping
- Implement masking for empty item slots (zeros)
- Remove zero-stub behavior for item_vfs_dim
- Tests verify item VFS observations with masking

Task 3.4 complete (Item VFS observations)"
```

---

## Subtask 3.5: Integration Tests and Documentation

**Files:**
- Test: `tests/test_townlet/integration/test_item_vfs_integration.py` (new file)
- Modify: `docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md`

**Duration:** ~0.5 days

### Step 3.5.1: Write integration test

**Test:** `tests/test_townlet/integration/test_item_vfs_integration.py`

```python
"""Integration tests for item VFS end-to-end."""

from pathlib import Path
import torch

from townlet.universe.compiler import UniverseCompiler


def test_item_vfs_profile_driven_end_to_end():
    """Item VFS should be profile-driven from compilation to observations."""
    # Setup: Compile items_smoke config (has item profiles)
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "items_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="items_smoke", use_cache=False)

    # Verify: Item profiles compiled
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.item_profiles is not None
    assert len(compiled.compiled_vfs_profiles.item_profiles) > 0

    # Create environment
    env = compiled.create_environment(
        num_agents=4,
        level_name="items_smoke",
        device=torch.device("cpu"),
    )

    # Verify: Item VFS storage allocated
    assert env.vfs_registry.item_vfs is not None
    assert env.vfs_registry.item_profile_map is not None

    # Exercise: Spawn item and observe VFS
    # ... (use ItemManager to spawn item with initial_state)

    # Verify: Item VFS appears in observations
    obs = env.reset()
    # ... (check obs includes non-zero item VFS)


def test_item_spawn_with_initial_state():
    """Items spawned with initial_state should have custom VFS values."""
    # Setup: Compile config with items
    # ...

    # Exercise: Spawn item with custom initial_state
    # ...

    # Verify: VFS state reflects initial_state
    # ...
```

**Location:** New file at `tests/test_townlet/integration/test_item_vfs_integration.py`

### Step 3.5.2: Run integration tests

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_item_vfs_integration.py -xvs
```

**Expected:** PASS

### Step 3.5.3: Update documentation

**File:** `docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md`

Add Task 3 status section:

```markdown
### Task 3: Item VFS Integration ✅ COMPLETE

**Status:** 100% complete
**Timeline:** Planned 2-3 days | Actual: X days
**Test Coverage:** 7 tests (100% passing)

**Deliverables:**
- ✅ Item profiles compiled by UniverseCompiler
- ✅ Item VFS storage shaped by compiled profiles
- ✅ ItemManager assigns vfs_profile to instances
- ✅ ItemManager accepts initial_state for VFS initialization
- ✅ Observation builder includes item VFS with masking
- ✅ Integration tests

**Commits:** [list commit SHAs]
```

### Step 3.5.4: Commit documentation

```bash
git add docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md tests/test_townlet/integration/test_item_vfs_integration.py
git commit -m "docs: mark Task 3 (Item VFS integration) as COMPLETE

Task 3 delivered:
- Item profiles compiled ✅
- Profile-driven item VFS storage ✅
- ItemManager VFS profile assignment ✅
- Item VFS observations with masking ✅
- 7 new tests passing

Next: Task 4 (Effects runtime usage)"
```

---

## Task 3 Success Criteria

**Functional:**
- ✅ Item profiles compiled from `vfs_profiles.yaml`
- ✅ Item VFS storage allocated using compiled profiles
- ✅ ItemManager assigns `vfs_profile` to item instances
- ✅ ItemManager accepts `initial_state` for VFS initialization
- ✅ ExecutionContext handles item-scoped variable access
- ✅ Observation builder includes item VFS with proper masking

**Tests:**
- ✅ 5-7 new tests passing
- ✅ All existing tests still pass

**Code Quality:**
- ✅ No runtime reads of `variables_reference.yaml` for item vars
- ✅ Item storage is profile-driven (not YAML-driven)
- ✅ Proper masking for empty item slots in observations

---

## Notes for Engineer

**Key Design Decisions:**

1. **Profile-agnostic storage layout:**
   - Item VFS tensor: `[max_items, max_vars_across_all_profiles]`
   - All profiles share same tensor, unused slots masked
   - Rationale: Simpler indexing, easier transfer learning

2. **Profile map for variable lookups:**
   - `item_profile_map: {profile_name → {var_name → tensor_index}}`
   - Allows fast VFS reads/writes by profile + variable name

3. **Initial_state overrides profile defaults:**
   - Profile defines defaults via `initial_value`
   - Spawn can override with `initial_state` dict
   - Useful for randomized loot, partial consumption, etc.

4. **Observation masking:**
   - Empty item slots filled with zeros
   - Agents see fixed inventory size (transfer learning)
   - Masking prevents agents from reading garbage values

**Common Pitfalls:**

- Don't forget to pass `item_profiles` to VariableRegistry in vectorized_env
- Don't forget to update ItemInstance dataclass with `vfs_profile` field
- Don't forget masking in observation builder (empty slots = zeros)
- Don't break existing tests that don't use item VFS (allow None/empty profiles)

**Testing Strategy:**

- Unit tests: Test each component in isolation (registry, manager, obs builder)
- Integration tests: Test full pipeline with real config packs
- Use `items_smoke` config for integration tests
- Verify masking with agents holding different item counts

---

## Execution Handoff

**Plan complete and saved to `docs/plans/vfs_uplift/TASK-3-DETAILED-PLAN.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - Dispatch fresh subagent per subtask, review between subtasks, fast iteration with quality gates

**2. Parallel Session (separate)** - Open new session with `/superpowers:execute-plan`, batch execution with checkpoints

**Which approach?**
