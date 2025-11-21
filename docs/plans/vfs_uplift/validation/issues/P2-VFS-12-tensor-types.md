# [VFS-12] Tensor Types (tensor1d/2d/Nd)

**Priority:** P2 (Minor)
**Category:** VFS
**Status:** PARTIAL
**Effort:** 2-3 days

## Description

VFS schema supports vector types (vector3) but not general tensor types (tensor1d, tensor2d, tensorNd). Cannot represent multi-dimensional arrays like 3×3 grid states, image patches, or matrices. Schema declares tensor types but runtime support (shape validation, initial value modes, tensor operations) is not implemented.

## Current State

**Working (vector3):**
```yaml
# VFS variable with vector3 type
variables:
  position:
    type: vector3  # ✅ Works
    default: [0.0, 0.0, 0.0]
    normalization:
      mode: "min_max"
      range: [[0, 10], [0, 10], [0, 10]]  # Per-dimension ranges
```

**Missing (tensors):**
```yaml
# Desired: 1D tensor (vector of arbitrary length)
variables:
  skill_levels:
    type: tensor1d
    shape: [10]  # 10 skills
    default: "zeros"  # Initialize to zeros

# Desired: 2D tensor (matrix)
variables:
  grid_memory:
    type: tensor2d
    shape: [8, 8]  # 8×8 grid
    default: "zeros"

# Desired: 3D tensor (e.g., image patch)
variables:
  visual_memory:
    type: tensor3d
    shape: [5, 5, 3]  # 5×5 RGB patch
    default: "random_normal"  # Initialize with random values
```

**Use cases blocked:**
- Skill systems: Track proficiency in N skills (tensor1d)
- Spatial memory: Agent remembers visited grid cells (tensor2d)
- Visual embeddings: Agent stores visual representations (tensor3d)
- Adjacency matrices: Social network graphs (tensor2d)
- Policy parameters: Store learned policy weights (tensorNd)

## Required Implementation

### 1. Schema Enhancement (2-3 hours)

**File:** `src/townlet/vfs/schema.py`

**Add tensor types to VariableType enum:**
```python
class VariableType(str, Enum):
    # Existing scalar types
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"

    # Existing vector type
    VECTOR3 = "vector3"

    # NEW: Tensor types
    TENSOR1D = "tensor1d"  # 1D array (arbitrary length)
    TENSOR2D = "tensor2d"  # 2D matrix
    TENSOR3D = "tensor3d"  # 3D tensor
    TENSORND = "tensorNd"  # N-dimensional tensor (N ≥ 4)

    # Reference types
    AGENT_REF = "agent_ref"
    ITEM_REF = "item_ref"
```

**Add shape specification to VariableDef:**
```python
@dataclass
class VariableDef:
    type: VariableType
    default: Optional[Any] = None
    expression: Optional[str] = None
    normalization: Optional[NormalizationSpec] = None
    access_control: Optional[AccessControlSpec] = None

    # NEW: Shape specification for tensor types
    shape: Optional[List[int]] = None  # e.g., [10] for tensor1d, [8, 8] for tensor2d

    # NEW: Initial value mode for tensor types
    initial_value_mode: Optional[str] = None  # "zeros", "ones", "eye", "random_normal", "random_uniform"
    initial_value_params: Optional[Dict[str, Any]] = None  # Params for initialization (mean, std, etc.)

    def __post_init__(self):
        # Validate shape required for tensor types
        if self.type in (VariableType.TENSOR1D, VariableType.TENSOR2D,
                         VariableType.TENSOR3D, VariableType.TENSORND):
            if not self.shape:
                raise ValidationError(f"Tensor type {self.type} requires 'shape' field")

        # Validate shape dimensionality matches type
        if self.type == VariableType.TENSOR1D and len(self.shape) != 1:
            raise ValidationError(f"tensor1d requires 1D shape, got {self.shape}")
        if self.type == VariableType.TENSOR2D and len(self.shape) != 2:
            raise ValidationError(f"tensor2d requires 2D shape, got {self.shape}")
        if self.type == VariableType.TENSOR3D and len(self.shape) != 3:
            raise ValidationError(f"tensor3d requires 3D shape, got {self.shape}")
```

### 2. Registry Support (1-2 days)

**File:** `src/townlet/vfs/registry.py`

**Add tensor storage and initialization:**
```python
class VFSRegistry:
    def _initialize_tensor(self, var_def: VariableDef, num_entities: int) -> torch.Tensor:
        """Initialize tensor variable storage."""

        shape = var_def.shape
        mode = var_def.initial_value_mode or "zeros"

        # Full shape: [num_entities, *tensor_shape]
        full_shape = [num_entities] + shape

        if mode == "zeros":
            return torch.zeros(full_shape, dtype=torch.float32, device=self.device)

        elif mode == "ones":
            return torch.ones(full_shape, dtype=torch.float32, device=self.device)

        elif mode == "eye":
            # Identity matrix (only for 2D tensors)
            if len(shape) != 2 or shape[0] != shape[1]:
                raise ValidationError("'eye' mode requires square 2D tensor")
            identity = torch.eye(shape[0], dtype=torch.float32, device=self.device)
            return identity.unsqueeze(0).expand(num_entities, -1, -1).clone()

        elif mode == "random_normal":
            # Normal distribution
            params = var_def.initial_value_params or {}
            mean = params.get("mean", 0.0)
            std = params.get("std", 1.0)
            return torch.normal(mean, std, size=full_shape, device=self.device)

        elif mode == "random_uniform":
            # Uniform distribution
            params = var_def.initial_value_params or {}
            low = params.get("low", 0.0)
            high = params.get("high", 1.0)
            return torch.rand(full_shape, device=self.device) * (high - low) + low

        else:
            raise ValidationError(f"Unknown initial_value_mode: {mode}")

    def get_tensor_slice(self, scope: str, idx: int, var_name: str, slice_spec: Any) -> torch.Tensor:
        """Get slice of tensor variable (e.g., [0:3, 2:5] for 2D tensor)."""
        tensor = self.get(scope, idx, var_name)
        return tensor[slice_spec]

    def set_tensor_slice(self, scope: str, idx: int, var_name: str, slice_spec: Any, value: torch.Tensor):
        """Set slice of tensor variable."""
        tensor = self.get(scope, idx, var_name)
        tensor[slice_spec] = value
```

### 3. Observation Integration (1 day)

**File:** `src/townlet/vfs/observation_builder.py`

**Add tensor flattening for observations:**
```python
def _build_tensor_observation(self, var_name: str, var_def: VariableDef, tensor: torch.Tensor) -> torch.Tensor:
    """Flatten tensor into observation vector."""

    # Tensor shape: [num_agents, *tensor_dims]
    # Flatten tensor dimensions: [num_agents, *tensor_dims] → [num_agents, flat_size]
    flat_size = torch.prod(torch.tensor(var_def.shape)).item()
    flat_tensor = tensor.reshape(tensor.shape[0], flat_size)

    # Apply normalization if specified
    if var_def.normalization:
        flat_tensor = self._apply_normalization(flat_tensor, var_def.normalization)

    return flat_tensor
```

**Update observation dimension calculation:**
```python
def calculate_observation_dim(vfs_profiles: CompiledVFSProfiles) -> int:
    """Calculate total VFS observation dimension including tensors."""
    total_dim = 0

    for profile in [vfs_profiles.global_profile, *vfs_profiles.agent_profiles.values()]:
        for var_def in profile.variables.values():
            if var_def.type in (VariableType.TENSOR1D, VariableType.TENSOR2D,
                                VariableType.TENSOR3D, VariableType.TENSORND):
                # Tensor contributes flattened size
                tensor_size = torch.prod(torch.tensor(var_def.shape)).item()
                total_dim += tensor_size
            else:
                # Scalar/vector contributes small fixed size
                total_dim += 1  # Or size based on type

    return total_dim
```

### 4. Expression Support (1 day - depends on COMP-7/8/9)

**File:** `src/townlet/world/expression/evaluator.py`

**Add tensor operations to expression language:**
```python
# Tensor indexing: vfs:skill_levels[3] (get 4th skill)
# Tensor slicing: vfs:grid_memory[0:3, 2:5] (get subgrid)
# Tensor aggregation: sum(vfs:skill_levels), mean(vfs:grid_memory)
# Tensor element-wise ops: vfs:grid_memory * 0.5 (scale all elements)
```

### 5. Testing (1 day)

**File:** `tests/test_townlet/unit/vfs/test_tensor_types.py` (new)

**Test cases:**
```python
def test_tensor1d_initialization():
    """Test 1D tensor variable initialization."""
    var_def = VariableDef(
        type=VariableType.TENSOR1D,
        shape=[10],
        initial_value_mode="zeros"
    )
    registry = VFSRegistry(device="cpu")
    tensor = registry._initialize_tensor(var_def, num_entities=32)

    assert tensor.shape == (32, 10)
    assert torch.all(tensor == 0.0)

def test_tensor2d_eye_initialization():
    """Test 2D tensor initialized as identity matrix."""
    var_def = VariableDef(
        type=VariableType.TENSOR2D,
        shape=[5, 5],
        initial_value_mode="eye"
    )
    registry = VFSRegistry(device="cpu")
    tensor = registry._initialize_tensor(var_def, num_entities=16)

    assert tensor.shape == (16, 5, 5)
    for i in range(16):
        assert torch.allclose(tensor[i], torch.eye(5))

def test_tensor_random_normal_initialization():
    """Test tensor initialized with random normal distribution."""
    var_def = VariableDef(
        type=VariableType.TENSOR2D,
        shape=[8, 8],
        initial_value_mode="random_normal",
        initial_value_params={"mean": 0.5, "std": 0.1}
    )
    registry = VFSRegistry(device="cpu")
    tensor = registry._initialize_tensor(var_def, num_entities=32)

    assert tensor.shape == (32, 8, 8)
    assert 0.3 < tensor.mean().item() < 0.7  # Roughly centered around 0.5
    assert 0.05 < tensor.std().item() < 0.15  # Roughly std = 0.1

def test_tensor_observation_flattening():
    """Test tensor flattened into observation vector."""
    var_def = VariableDef(
        type=VariableType.TENSOR2D,
        shape=[4, 4]
    )
    tensor = torch.rand(32, 4, 4)  # 32 agents, 4×4 tensors

    flat = observation_builder._build_tensor_observation("grid_memory", var_def, tensor)
    assert flat.shape == (32, 16)  # 4×4 = 16 flattened

def test_tensor_slice_operations():
    """Test getting and setting tensor slices."""
    registry = VFSRegistry(device="cpu")
    registry.set("agent", 0, "grid_memory", torch.zeros(8, 8))

    # Get slice
    subgrid = registry.get_tensor_slice("agent", 0, "grid_memory", (slice(0, 3), slice(2, 5)))
    assert subgrid.shape == (3, 3)

    # Set slice
    registry.set_tensor_slice("agent", 0, "grid_memory", (slice(0, 3), slice(2, 5)), torch.ones(3, 3))
    full_grid = registry.get("agent", 0, "grid_memory")
    assert torch.all(full_grid[0:3, 2:5] == 1.0)

def test_tensor_shape_validation():
    """Test shape validation for tensor types."""
    with pytest.raises(ValidationError):
        # tensor2d requires 2D shape
        VariableDef(type=VariableType.TENSOR2D, shape=[10])

    with pytest.raises(ValidationError):
        # tensor types require shape field
        VariableDef(type=VariableType.TENSOR1D)
```

## Acceptance Criteria

- [ ] Tensor types (tensor1d/2d/3d/Nd) in VariableType enum
- [ ] VariableDef has `shape` and `initial_value_mode` fields
- [ ] Shape validation: Tensor types require shape, dimensionality must match type
- [ ] Registry initializes tensors with zeros/ones/eye/random_normal/random_uniform
- [ ] Tensor storage in GPU tensors with shape [num_entities, *tensor_dims]
- [ ] Tensor flattening for observations (flatten → normalize → include in obs)
- [ ] Tensor slice operations (get/set slices)
- [ ] Observation dimension calculation includes tensor sizes
- [ ] 20+ tests covering tensor initialization, storage, observation, and validation
- [ ] Documentation updated with tensor type examples

## Evidence

**Source Report:** gap-report-final.md (lines 71-94), gap-report-vfs.md
**Schema:** `src/townlet/vfs/schema.py:VariableType` (vector3 works, tensors missing)

## Implementation Notes

**Why P2 (not P1/P0):** Tensor types are advanced feature for complex state representations. Phase 1-3 curriculum levels use scalar and vector3 variables (sufficient for basic RL tasks). Tensors needed for Phase 4+ (visual memory, skill trees, spatial reasoning).

**Design Decisions:**

1. **Storage Format:**
   - GPU tensors: [num_entities, *tensor_dims]
   - Example: 32 agents with 8×8 grid memory → [32, 8, 8] tensor
   - Efficient for vectorized operations across batch

2. **Observation Integration:**
   - Flatten tensors into observation vector
   - Example: [32, 8, 8] → [32, 64] (8×8 = 64 dims)
   - Apply normalization after flattening
   - **Warning:** Large tensors explode observation dimension (use cautiously)

3. **Initial Value Modes:**
   - `zeros`: All elements = 0 (default)
   - `ones`: All elements = 1
   - `eye`: Identity matrix (2D only, square shape required)
   - `random_normal`: Sample from N(μ, σ²) with configurable mean/std
   - `random_uniform`: Sample from U(low, high) with configurable bounds

4. **Expression Language Integration (future):**
   - Tensor indexing: `vfs:skill_levels[3]` (3rd element)
   - Tensor slicing: `vfs:grid_memory[0:3, 2:5]` (subgrid)
   - Tensor aggregation: `sum(vfs:skill_levels)`, `mean(vfs:grid_memory)`
   - Requires expression parser (COMP-7) and AST support

**Use Case Examples:**

**Skill System:**
```yaml
# Agent tracks proficiency in 10 skills
variables:
  skill_levels:
    type: tensor1d
    shape: [10]
    default: zeros
    normalization:
      mode: "min_max"
      range: [0, 100]  # Skills range 0-100
```

**Spatial Memory:**
```yaml
# Agent remembers which grid cells visited
variables:
  visited_cells:
    type: tensor2d
    shape: [8, 8]  # Match grid size
    default: zeros  # 0 = unvisited, 1 = visited
```

**Visual Embedding:**
```yaml
# Agent stores visual representation of environment
variables:
  visual_memory:
    type: tensor3d
    shape: [5, 5, 32]  # 5×5 spatial, 32 feature channels
    default: random_normal
    initial_value_params:
      mean: 0.0
      std: 0.1
```

**Adjacency Matrix (Social Network):**
```yaml
# Agent tracks relationships with other agents
variables:
  social_graph:
    type: tensor2d
    shape: [512, 512]  # 512 agents × 512 agents
    default: zeros  # No connections initially
```

**Performance Considerations:**
- Large tensors increase memory usage: [32 agents, 512, 512] = 8MB per variable
- Observation dimension explosion: 8×8 tensor = 64 dims, 512×512 tensor = 262K dims (!!)
- Recommendation: Use tensors for state storage, not direct observation (use aggregations)
- Alternative: Tensor variables not in observations (internal state only)

**Observation Dimension Management:**
- Option 1: Flatten all tensors (simple but large obs)
- Option 2: Aggregate tensors (sum, mean, max) → single scalar
- Option 3: Mark tensors as "non-observable" (storage only, not in obs)
- Recommendation: Use access_control to exclude tensors from agent observations

## References

- Schema: `src/townlet/vfs/schema.py:VariableType` (add tensor types)
- Registry: `src/townlet/vfs/registry.py` (add tensor initialization and storage)
- ObservationBuilder: `src/townlet/vfs/observation_builder.py` (add tensor flattening)
- Test file: `tests/test_townlet/unit/vfs/test_tensor_types.py` (to be created)
- Documentation: `docs/config-schemas/variables.md` (add tensor type examples)
- Related: Vector3 implementation (similar patterns), observation dimension calculation
