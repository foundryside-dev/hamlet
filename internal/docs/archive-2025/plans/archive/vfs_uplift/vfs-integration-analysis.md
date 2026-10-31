# VFS Integration Analysis: Architecture & Extension Points

**Purpose**: Deep-dive analysis of existing VFS implementation to inform Phase 2 (VFS Engine + DynObs) design
**Created**: 2025-11-19
**Activity**: Activity 8 (Risk Reduction)

---

## Executive Summary

The Variable & Feature System (VFS) is a **3-layer architecture** (Schema → Registry → Observation Builder) integrated into UniverseCompiler Stage 3. It currently supports **3 scopes** (global, agent, agent_private) with access control enforcement.

**Key Finding**: VFS architecture is **highly extensible** for item scope. Extension requires:
1. Add `"item"` to `VariableDef.scope` Literal
2. Extend `VariableRegistry._compute_shape()` for item-scoped tensors
3. Add item-aware access control (items can read/write own state)
4. Integrate item profiles into observation assembly

**Complexity**: **LOW-MEDIUM** - Architecture designed for extensibility, item scope is natural fit.

---

## VFS Architecture Layers

### Layer 1: Schema (Compile-Time Definitions)
**File**: `src/townlet/vfs/schema.py`

#### Core Data Structures

**`VariableDef`** - Variable definition with scope, type, and access control
```python
VariableDef(
    id="energy",
    scope="agent",  # Literal["global", "agent", "agent_private"]
    type="scalar",  # Literal["scalar", "vec2i", "vec3i", "vecNi", "vecNf", "bool"]
    dims=None,      # Required for vecNi/vecNf
    lifetime="episode",  # Literal["tick", "episode"]
    readable_by=["agent", "engine", "acs"],
    writable_by=["engine", "actions"],
    default=1.0,
    normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0),
    description="Energy level [0.0-1.0]"
)
```

**Scope Semantics**:
- `global`: Single value shared by all agents (shape `[]` or `[dims]`)
- `agent`: Per-agent values, observable by all (shape `[num_agents]` or `[num_agents, dims]`)
- `agent_private`: Per-agent values, observable only by owner + engine (shape `[num_agents]` or `[num_agents, dims]`)

**Type System** (Phase 1):
- `scalar`: Single float value (torch.float32)
- `vec2i`, `vec3i`: Fixed 2D/3D integer vectors (torch.long)
- `vecNi`, `vecNf`: N-dimensional vectors (requires `dims` field)
- `bool`: Boolean flag (torch.bool)

**Access Control**:
- `readable_by`: List of authorized readers (`["agent", "engine", "acs", "bac"]`)
- `writable_by`: List of authorized writers (`["engine", "actions", "bac"]`)
- Enforced at runtime by `VariableRegistry`

---

**`ObservationField`** - Maps variable to observation
```python
ObservationField(
    id="obs_energy",
    source_variable="energy",
    exposed_to=["agent"],
    shape=[],  # [] for scalar, [N] for vector
    normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0),
    semantic_type="bars",  # Literal["bars", "spatial", "affordance", "temporal", "custom"]
    curriculum_active=True
)
```

**Semantic Types**: Group observations for structured encoders
- `bars`: Meter values (energy, health, etc.)
- `spatial`: Position, grid encoding
- `affordance`: Affordance state
- `temporal`: Time-of-day, progress
- `custom`: User-defined variables

**Curriculum Masking**: `curriculum_active=False` indicates padding dimensions (masked in training)

---

**`NormalizationSpec`** - Observation normalization
```python
# MinMax normalization
NormalizationSpec(kind="minmax", min=0.0, max=1.0)
NormalizationSpec(kind="minmax", min=[0.0, 0.0], max=[7.0, 7.0])  # Vector

# Z-score normalization
NormalizationSpec(kind="zscore", mean=0.5, std=0.2)
```

**Validator**: Ensures required params present for each kind (min/max for minmax, mean/std for zscore)

---

**`WriteSpec`** - Action write specification (Phase 2+)
```python
WriteSpec(
    variable_id="energy",
    expression="-0.005"  # Phase 1: string, Phase 2: parsed AST
)
```

**Current Status**: Expressions stored as strings (no parsing in Phase 1)

---

### Layer 2: Registry (Runtime Storage)
**File**: `src/townlet/vfs/registry.py`

#### VariableRegistry

**Purpose**: Runtime storage for VFS variables with access control enforcement

**Initialization**:
```python
registry = VariableRegistry(
    variables=[...],  # List[VariableDef]
    num_agents=4,
    device=torch.device("cuda:0")
)
```

**Storage Model**:
- `_storage: dict[str, torch.Tensor]` - Variable ID → tensor
- `_definitions: dict[str, VariableDef]` - Variable ID → definition
- `_expected_shapes: dict[str, torch.Size]` - Variable ID → expected shape
- `_expected_dtypes: dict[str, torch.dtype]` - Variable ID → expected dtype

**Shape Computation** (`_compute_shape()`):
```python
# Scalar variables
global scope:          ()              # Shape []
agent scope:           (num_agents,)   # Shape [num_agents]
agent_private scope:   (num_agents,)   # Shape [num_agents]

# Vector variables (dims=2)
global scope:          (2,)              # Shape [2]
agent scope:           (num_agents, 2)   # Shape [num_agents, 2]
agent_private scope:   (num_agents, 2)   # Shape [num_agents, 2]
```

**Access Control Enforcement**:
```python
# Read with permission check
energy = registry.get("energy", reader="agent")
# Raises PermissionError if "agent" not in readable_by

# Write with permission check
registry.set("energy", new_values, writer="engine")
# Raises PermissionError if "engine" not in writable_by
```

**agent_private Special Handling**:
- `reader="agent"` raises PermissionError for agent_private variables
- Only privileged readers (engine, acs, bac) can access raw values

**Validation**:
- Shape mismatch raises ValueError
- dtype mismatch raises ValueError
- Defensive copy on write (avoid aliasing)

---

### Layer 3: Observation Builder (Compile-Time Spec Generation)
**File**: `src/townlet/vfs/observation_builder.py`

#### VFSObservationSpecBuilder

**Purpose**: Generate observation specifications (schemas) from variable definitions + exposure config

**Key Method**:
```python
spec_builder = VFSObservationSpecBuilder()
obs_fields = spec_builder.build_observation_spec(
    variables=[...],  # List[VariableDef]
    exposures=[       # List[dict] from config
        {
            "id": "obs_energy",
            "source_variable": "energy",
            "exposed_to": ["agent"],
            "shape": [],
            "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            "semantic_type": "bars",
            "curriculum_active": True
        }
    ]
)
```

**Validation**:
- `source_variable` must exist in `variables` list
- `id`, `exposed_to`, `shape` required (no defaults)
- `semantic_type` must be one of: bars, spatial, affordance, temporal, custom
- `curriculum_active` required boolean
- Normalization shape must match observation shape

**No-Defaults Policy**: All fields explicitly required (enforced by ValueError)

---

## UniverseCompiler Integration

### Compilation Pipeline (7 Stages)

VFS integrated into **Stage 3: Observations**

```
Stage 0: YAML Syntax Validation
Stage 1: Load v2.1 Configs
Stage 1b: v2.1 Semantic Validation
Stage 2: Symbol Table (affordances, meters, actions)
Stage 3: Observations + VFS ← VFS INTEGRATION HERE
Stage 4: Cross-Validation (DAC references, etc.)
Stage 5: Metadata Assembly
Stage 6: Optimization
Stage 7: Cache Emission
```

### VFS Build Methods

**`_build_vfs_observation_fields()`** (`compiler.py:1240`)
- Mirrors `ObservationSpec` fields into `VFSObservationField` tuples
- Converts environment.yaml normalization → VFS `NormalizationSpec`
- Sets `curriculum_active=False` if description contains "MASKED"
- Returns `tuple[VFSObservationField, ...]`

**`_build_vfs_variables()`** (`compiler.py:1308`)
- Builds `VariableDef` tuples from:
  1. System observation primitives (obs_position, obs_meters, etc.) from `obs_spec`
  2. User-defined variables from `environment.environment.variables`
- Ensures every `VFSObservationField.source_variable` has backing `VariableDef`
- Returns `tuple[VariableDef, ...]`

### CompiledUniverse Storage

```python
CompiledUniverse(
    metadata=...,
    observation_spec=...,
    vfs_observation_fields=tuple[VFSObservationField, ...],  # VFS fields
    vfs_variables=tuple[VariableDef, ...],                   # VFS variables
    ...
)
```

**Per-Level Storage**:
```python
CompiledUniverse.LevelMetadata(
    level_name="L0_smoke",
    vfs_observation_fields=(...),  # Level-specific VFS fields
    vfs_variables=(...),           # Level-specific VFS variables
    ...
)
```

---

## Extension Points for Item Scope

### 1. **Schema Extension** (vfs/schema.py)

#### Current Scope Literal
```python
scope: Literal["global", "agent", "agent_private"]
```

#### Extended for Items
```python
scope: Literal["global", "agent", "agent_private", "item"]
```

**Item Scope Semantics**:
- **Storage**: Per-item values, observable by agents/engine
- **Shape**: `[num_items]` (scalar) or `[num_items, dims]` (vector)
- **Use Case**: item_durability, item_uses_remaining, item_rarity
- **Access Control**: Items can read/write own state, agents can read

**Example**:
```python
VariableDef(
    id="item_durability",
    scope="item",  # NEW SCOPE
    type="scalar",
    lifetime="episode",
    readable_by=["agent", "engine", "item"],  # Items can read own state
    writable_by=["engine", "item"],           # Items can write own state
    default=1.0
)
```

---

### 2. **Registry Extension** (vfs/registry.py)

#### Current `_compute_shape()` Logic
```python
if var_def.scope == "global":
    return ()  # or (dims,) for vectors
elif var_def.scope in ("agent", "agent_private"):
    return (num_agents,)  # or (num_agents, dims) for vectors
```

#### Extended for Item Scope
```python
if var_def.scope == "global":
    return ()  # or (dims,) for vectors
elif var_def.scope in ("agent", "agent_private"):
    return (num_agents,)  # or (num_agents, dims) for vectors
elif var_def.scope == "item":
    return (num_items,)  # or (num_items, dims) for vectors
```

**Required**: Add `num_items: int` parameter to `VariableRegistry.__init__()`

---

#### Current `_initialize_storage()` Logic
```python
if var_def.scope == "global":
    tensor = torch.tensor(var_def.default, ...)
else:  # agent or agent_private
    tensor = torch.full((num_agents,), var_def.default, ...)
```

#### Extended for Item Scope
```python
if var_def.scope == "global":
    tensor = torch.tensor(var_def.default, ...)
elif var_def.scope in ("agent", "agent_private"):
    tensor = torch.full((num_agents,), var_def.default, ...)
elif var_def.scope == "item":
    tensor = torch.full((num_items,), var_def.default, ...)
```

**Complexity**: **LOW** - Straightforward extension of existing pattern

---

### 3. **Access Control Extension**

#### Item-Aware Access Control

**New reader**: `"item"` - items can read own state
```python
VariableDef(
    id="item_durability",
    scope="item",
    readable_by=["agent", "engine", "item"],  # Items can read
    writable_by=["engine", "item"],           # Items can write
    ...
)
```

**Access Check** (in `VariableRegistry.get()`):
```python
if reader == "item":
    # Item can only read its own slot (requires item_id parameter)
    if var_def.scope == "item":
        # Return value[item_id] (single item's state)
        return self._storage[variable_id][item_id].clone()
```

**Challenge**: Item-scoped reads require item ID context (which item is reading?)

**Solution**: Extend `get()` signature:
```python
def get(self, variable_id: str, reader: str, context: dict | None = None) -> torch.Tensor:
    """Get variable with access control.

    Args:
        context: Optional reader context (e.g., {"item_id": 3} for item-scoped reads)
    """
```

---

### 4. **Observation Assembly Extension**

#### Current Observation Building (Conceptual)
```python
obs = torch.cat([
    global_vars,      # Shape [global_dims]
    agent_vars,       # Shape [num_agents, agent_dims]
], dim=-1)
```

#### Extended for Item Scope
```python
# Per-agent observation includes:
# - Global vars (broadcasted to all agents)
# - Agent-specific vars (agent's own state)
# - Item vars (items in agent's inventory)

for agent_idx in range(num_agents):
    agent_items = inventory[agent_idx]  # List of item IDs in agent's inventory

    item_obs = []
    for slot_idx in range(max_items_per_agent):
        if slot_idx < len(agent_items):
            item_id = agent_items[slot_idx]
            # Get item's VFS state
            item_obs.append(item_vfs_state[item_id])
        else:
            # Empty slot - pad with zeros
            item_obs.append(torch.zeros(item_vfs_dims))

    obs[agent_idx] = torch.cat([
        global_vars,
        agent_vars[agent_idx],
        torch.cat(item_obs)  # Flattened item observations
    ])
```

**Complexity**: **MEDIUM** - Requires inventory-aware observation assembly

**Edge Case** (from edge-case-policies.md):
- **Policy #5**: Empty slots masked with 0.0 (not removed)
- **Implication**: Fixed obs_dim (3 slots × item_vfs_dims, even if inventory < 3)

---

## Current VFS Usage Patterns

### environment.yaml Variables (Current)
```yaml
environment:
  variables:
    - name: deficit_energy
      type: scalar
      dims: 1
      scope: agent
      description: "How far below target energy"
      normalization:
        method: clip
        range: [0.0, 1.0]

    - name: time_since_last_eat
      type: scalar
      dims: 1
      scope: agent
      description: "Timesteps since last EAT action"
      normalization:
        method: normalize
        range: [0.0, 100.0]
```

**Current Limitations**:
- Only `global` and `agent` scopes used (no `agent_private` or `item` yet)
- Static values only (no expressions - Phase 2+)
- No item-scoped variables (not implemented)

---

### DAC VFS References (Future)
```yaml
# drive_as_code.yaml can reference VFS variables
modifiers:
  energy_crisis:
    type: range_multiplier
    variable: deficit_energy  # References VFS variable
    ranges:
      - min: 0.0
        max: 0.2
        multiplier: 0.0

extrinsic:
  type: vfs_variable
  variable: custom_reward  # VFS variable as reward source
```

**Validation**: UniverseCompiler Stage 4 validates DAC references exist in VFS

---

## Phase 2 Integration Plan

### Required Changes

**1. Schema Extension** (`vfs/schema.py`):
```python
# Line 234: Extend scope Literal
scope: Literal["global", "agent", "agent_private", "item"]
```

**2. Registry Extension** (`vfs/registry.py`):
```python
# Add num_items parameter
def __init__(self, variables, num_agents, num_items, device):
    self.num_items = num_items
    ...

# Extend _compute_shape()
elif var_def.scope == "item":
    return (num_items,) if is_scalar else (num_items, dims)

# Extend _initialize_storage()
elif var_def.scope == "item":
    tensor = torch.full((num_items,), var_def.default, ...)
```

**3. Access Control Extension** (optional Phase 2, required Phase 3):
```python
# Extend get() for item-scoped reads
def get(self, variable_id, reader, context=None):
    if reader == "item" and context and "item_id" in context:
        item_id = context["item_id"]
        return self._storage[variable_id][item_id].clone()
    ...
```

**4. Observation Builder** (Phase 2):
- Add item profile assembly logic
- Implement inventory-aware observation generation
- Handle empty slot masking (Policy #5)

---

## Constraints & Assumptions

### Hard Constraints
1. **No-Defaults Policy**: All config fields must be explicit (no implicit values)
2. **Fixed obs_dim**: Observation dimension must remain constant (enables curriculum transfer)
3. **Access Control**: Read/write permissions enforced at runtime
4. **Shape Validation**: Tensor shapes must match variable definitions

### Soft Constraints
1. **Expression Language**: Deferred to Phase 2+ (static values only in Phase 1)
2. **Item Scope**: Not yet implemented (needs Phase 2 extension)
3. **agent_private Scope**: Defined but rarely used in current configs

### Assumptions
1. **GPU Tensors**: All VFS storage assumed to be GPU tensors (device parameter)
2. **Batch Processing**: VFS designed for vectorized operations (num_agents dimension)
3. **Static Vocabulary**: VFS profiles defined at compile-time (not runtime-dynamic)

---

## Risk Assessment

| Extension Point | Complexity | Risk | Notes |
|-----------------|------------|------|-------|
| **Schema scope Literal** | LOW | LOW | Simple enum extension |
| **Registry shape computation** | LOW | LOW | Pattern already exists for agent scope |
| **Registry storage init** | LOW | LOW | Straightforward tensor allocation |
| **Access control (item reads)** | MEDIUM | MEDIUM | Requires context parameter, item ID tracking |
| **Observation assembly** | MEDIUM-HIGH | MEDIUM | Inventory-aware logic, empty slot masking |

**Overall Phase 2 Risk**: **MEDIUM** - Architecture supports extension, but observation assembly adds complexity.

---

## Recommendations

### Phase 1: DTOs + Compiler (No VFS Changes)
- **DO NOT** extend VFS in Phase 1
- Focus on `items.yaml` + `vfs_profiles.yaml` DTOs
- Validate configs compile (no runtime integration)
- **Rationale**: VFS extension couples with observation assembly (Phase 2)

### Phase 2: VFS Engine + DynObs
- **Extend** VariableDef.scope to include `"item"`
- **Extend** VariableRegistry for item-scoped tensors
- **Implement** inventory-aware observation assembly
- **Defer** item-scoped access control to Phase 3 (not needed for observations)

### Phase 3: Items Runtime + Inventory
- **Implement** item-aware access control (item reads/writes own state)
- **Integrate** VFS with ItemManager (items update own durability, uses_remaining)
- **Test** VFS performance with 50 simultaneous items (profiling target)

---

## Conclusion

**VFS architecture is well-designed for extensibility**. Item scope is a natural extension of existing agent/agent_private pattern. **Primary complexity is observation assembly** (inventory-aware logic), not VFS registry extension.

**Confidence**: **HIGH** - VFS extension is straightforward, low risk.

**Next Steps**: Use this analysis to inform Phase 2 plan revisions (observation budget, VFS integration points).
