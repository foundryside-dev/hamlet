# TASK-005Bx: VFS Phase 2 Residual Integration (RC-1 BLOCKER)

**Status**: Ready
**Priority**: **CRITICAL (RC-1 Release Blocker)**
**Estimated Effort**: 20-28 hours (release-quality implementation with batched restructure)
**Dependencies**: TASK-005B (90% complete - expression engine exists), BUG-36 (open - closes this)
**Parent Task**: TASK-005B-VFS2 (original 60-80h estimate - now mostly complete)
**Created**: 2025-11-30
**Updated**: 2025-11-30 (Revised after design review: VFS-only writes, batched execution)
**Completed**: YYYY-MM-DD

**Keywords**: VFS, WriteSpec, ActionConfig.writes, expression integration, variable updates, RC-1, release-blocker
**Subsystems**: `environment/vectorized_env.py`, `environment/action_config.py`, `vfs/registry.py`, `universe/compiler.py`, `universe/dto/`
**Architecture Impact**: Moderate (DTO extensions, new VariableRegistry API, proper serialization)
**Breaking Changes**: No (purely enabling dormant feature, but requires checkpoint compatibility)

---

## AI-Friendly Summary

**What**: Wire `ActionConfig.writes` into action execution so that `WriteSpec.expression` is evaluated and updates VFS variables at runtime. **This is an RC-1 release blocker** - cannot ship with dormant WriteSpec API.

**Why**: The expression engine was built piecemeal during effects/items/compiler work and is production-ready (2,428 lines, 56 commits). VFS2 is 90% complete but shipping incomplete = defect. Must complete properly with release-quality architecture (no hacks).

**Scope**:

- **Included**: Parse WriteSpec expressions, evaluate on action execution, update VariableRegistry via proper API, DTO extensions, checkpoint serialization, permission validation, shape validation, comprehensive testing
- **Excluded**: New expression language features (engine is complete), new VFS capabilities, DAC changes

**RC-1 Quality Requirements**:

- ✅ Proper `VariableRegistry.set_partial()` API (no direct storage hacks)
- ✅ Comprehensive error handling with clear messages
- ✅ Full checkpoint compatibility and serialization
- ✅ Permission and shape validation at compile and runtime
- ✅ Production-grade test coverage (unit + integration + regression)

**What's Already Done (90% of TASK-005B)**:

- ✅ Expression engine (`src/townlet/world/expression/` - parser, AST, evaluator, type checker)
- ✅ VFSEvaluator with mark-and-sweep optimization
- ✅ Function library (28 built-in functions: min/max/clamp/sin/cos/perlin/simplex/etc)
- ✅ Integration with effects, items, universe compiler
- ✅ GPU-native tensor evaluation
- ✅ Temporal history tracking
- ✅ Dependency resolution and topological sorting

**What's Missing (10% - this task)**:

- ❌ ActionConfig.writes → VariableRegistry integration
- ❌ WriteSpec.expression parsing at compile time
- ❌ Expression evaluation on action execution
- ❌ VariableRegistry.set_partial() API for batched updates
- ❌ ActionMetadata DTO extension for compiled writes
- ❌ AST serialization for checkpoint compatibility
- ❌ Permission validation (writable_by enforcement)
- ❌ Shape validation and error context
- ❌ Contract validation for standard variables (optional enhancement)

**Critical Hidden Complexity** (discovered in risk assessment):

- VariableRegistry lacks batched update API (must add set_partial method - 3-4 hours)
- ActionMetadata DTO requires writes field with frozen dataclass compatibility (2-3 hours)
- AST serialization for checkpoints requires expression string storage + re-parsing (2 hours)
- Permission validation missing (writable_by checks - 1 hour)
- Shape validation and device handling missing (2 hours)
- Error context enrichment for debugging (1-2 hours)

**Quick Assessment**:

- **Current Limitation**: `ActionConfig.writes` field exists but is never executed; expressions are stored but ignored (dormant API = cannot ship)
- **After Implementation**: Actions can update VFS variables via expressions (e.g., `REST` increases energy) with proper validation and error handling
- **Unblocks**: RC-1 release, BUG-36 closure, TASK-005B completion, VFS-backed action effects
- **Impact Radius**: VariableRegistry API, ActionMetadata DTO, VectorizedHamletEnv action execution, Universe compiler, checkpoint serialization
- **Release Impact**: RC-1 blocker - cannot ship with incomplete VFS2 or dormant WriteSpec API

---

## Problem Statement

### Current State

**Expression Engine Exists and Works**:

```
src/townlet/world/expression/
├── parser.py         (pyparsing-based, production quality)
├── ast_nodes.py      (Visitor pattern, 10 node types)
├── evaluator.py      (GPU-native torch tensor evaluation)
├── type_checker.py   (full type inference)
├── context.py        (ExecutionContext with bars/vfs/affordances)
├── functions.py      (28 built-in functions)
└── history.py        (temporal tracking)

Total: 2,428 lines, 56 commits, production-ready
```

**Integration Exists**:

- ✅ Effects system: `effects/compiler.py`, `effects/executor.py`
- ✅ Items system: `items/manager.py`
- ✅ Universe compiler: `universe/compiler.py`
- ✅ VFS evaluator: `vfs/evaluator.py` (mark-and-sweep, dependency tracking)

**What's Missing**:

```python
# This field exists but is never used:
class ActionConfig(BaseModel):
    writes: list[WriteSpec] = Field(default_factory=list)  # ← DORMANT

# This class exists but expressions are never parsed:
class WriteSpec(BaseModel):
    variable_id: str
    expression: str  # ← String, never converted to AST

# VectorizedHamletEnv action execution ignores writes:
def _execute_action(self, action_idx):
    # Apply costs/effects to bars
    # ...
    # MISSING: Apply writes to VFS variables
```

### Impact

**Current Behavior**:

- Actions with `writes` field pass validation
- Expressions are stored but never evaluated
- Silent no-op (misleading for config authors)

**Desired Behavior**:

- Actions execute writes on invocation
- Expressions update **VFS variables only** (not bars) via VariableRegistry
- Bars can be **read** in expressions (via `bar.X` prefix) but not written
- Example: `REST` action increases a VFS variable `energy_boost` via `"min(1.0, bar.energy * 0.2)"`
- Rationale: Bars have their own modification system (costs/effects); VFS is the extension point for custom state

---

## Solution Overview

### High-Level Approach (RC-1 Quality)

**Compile Time** (Universe Compiler):

1. Parse `WriteSpec.expression` into AST using existing `ExpressionParser`
2. Type-check AST against VFS variable definitions
3. **Validate permissions**: Check `"actions" in var_def.writable_by`
4. Store expression string in ActionMetadata (AST parsed on-demand at runtime)
5. Extend ActionMetadata DTO with `writes: tuple[CompiledWriteSpec, ...]`

**Runtime** (VectorizedHamletEnv):

1. When action fires, parse and evaluate expressions for each WriteSpec
2. Use existing `Evaluator` with `ExecutionContext(bars=..., vfs=...)`
3. **Validate shapes**: Ensure result matches agent count or is broadcastable scalar
4. **Handle devices**: Transfer tensors to VariableRegistry device
5. Call **new API** `VariableRegistry.set_partial(variable_id, values, agent_indices)` for batched updates

**VariableRegistry Extension**:

- Add `set_partial()` method for updating subset of agents
- Proper access control validation
- Shape and type validation
- Device-aware tensor handling

**Checkpoint Compatibility**:

- Store expression strings (not AST objects) in serialized ActionMetadata
- Re-parse expressions on checkpoint load (small overhead, clean architecture)
- Maintain backward compatibility with configs that don't use writes

**Key Architectural Decisions** (for RC-1 quality):

1. **VFS-Only Writes** (DECIDED):
   - `WriteSpec` can only write to VFS variables, NOT bars/meters
   - Bars are readable in expressions via `bar.energy`, `bar.health`, etc.
   - Rationale: "Bars have their own system (costs/effects). If you want a variable you can modify with expressions, create a VFS variable."
   - This maintains clean separation: costs/effects → bars, writes → VFS

2. **Batched Execution** (DECIDED):
   - Restructure custom action execution to batch agents by action ID
   - Current per-agent loop replaced with grouped execution
   - Enables efficient GPU operations and proper `set_partial()` usage
   - Aligns with vectorized codebase philosophy

3. **Batched Updates**: Add proper `set_partial()` API to VariableRegistry (no storage hacks)

4. **AST Storage**: Store expression string in ActionMetadata, parse on-demand at runtime

5. **Permission Validation**: Enforce `writable_by` at compile time with clear errors

6. **Error Context**: Runtime failures include agent index, action name, variable ID for debugging

---

## Detailed Design

### Part 0: VariableRegistry API Extension (3-4 hours)

**File**: `src/townlet/vfs/registry.py`

**Problem**: Current `set()` method requires full tensor replacement. No API for updating subset of agents.

**Current API** (line 270):

```python
def set(self, variable_id: str, value: torch.Tensor, writer: str) -> None:
    """Set variable value with access control."""
    # Expects FULL tensor replacement
    if value.shape != expected_shape:
        raise ValueError(...)
    self._storage[variable_id] = value.to(self.device).clone()
```

**New API** (add method):

```python
def set_partial(
    self,
    variable_id: str,
    values: torch.Tensor,
    agent_indices: torch.Tensor,
    writer: str = "actions"
) -> None:
    """Update variable for subset of agents.

    Args:
        variable_id: Variable to update
        values: New values [num_agents_subset] or scalar
        agent_indices: Which agents to update [num_agents_subset]
        writer: Access control role (default "actions")

    Raises:
        KeyError: Variable not found
        PermissionError: Writer not in writable_by list
        ValueError: Shape mismatch (values must match agent_indices length or be scalar)

    Example:
        # Update energy for 3 agents
        registry.set_partial("energy",
                            torch.tensor([0.5, 0.6, 0.7]),
                            torch.tensor([0, 2, 5]))
    """
    # Validate variable exists
    if variable_id not in self._definitions:
        raise KeyError(f"Variable '{variable_id}' not found in registry")

    var_def = self._definitions[variable_id]

    # Validate write permission
    if writer not in var_def.writable_by:
        raise PermissionError(
            f"Writer '{writer}' cannot write to '{variable_id}'. "
            f"Writable by: {var_def.writable_by}"
        )

    # Validate and broadcast values
    if values.dim() == 0:
        # Scalar: broadcast to all indices
        values = values.expand(len(agent_indices))
    elif values.shape[0] != len(agent_indices):
        raise ValueError(
            f"Values shape {values.shape} doesn't match "
            f"agent_indices length {len(agent_indices)}"
        )

    # Device transfer
    values = values.to(self.device)
    agent_indices = agent_indices.to(self.device)

    # Update storage
    if variable_id not in self._storage:
        # Initialize if needed (shouldn't happen, but defensive)
        self._storage[variable_id] = torch.zeros(
            self.num_agents, device=self.device
        )

    self._storage[variable_id][agent_indices] = values
```

**Tests**:

```python
# tests/test_townlet/unit/vfs/test_registry_partial_updates.py
def test_set_partial_updates_subset():
    """set_partial updates only specified agents."""

def test_set_partial_broadcasts_scalar():
    """Scalar value broadcasts to all agent_indices."""

def test_set_partial_validates_permission():
    """set_partial raises PermissionError for unauthorized writer."""

def test_set_partial_validates_shape():
    """set_partial raises ValueError on shape mismatch."""

def test_set_partial_handles_device_transfer():
    """set_partial transfers tensors to registry device."""
```

---

### Part 1: Compile-Time WriteSpec Parsing (4-6 hours)

**File**: `src/townlet/universe/compiler.py`

**Changes**:

1. Import `ExpressionParser` and `TypeChecker` (already imported for other uses)
2. When compiling actions, parse `ActionConfig.writes` expressions:

   ```python
   from townlet.world.expression import ExpressionParser, TypeChecker

   parser = ExpressionParser()
   type_checker = TypeChecker(vfs_types)  # VFS variable types from registry

   compiled_writes = []
   for write_spec in action.writes:
       ast = parser.parse(write_spec.expression)
       type_checker.check(ast)  # Validate expression against VFS types
       compiled_writes.append(CompiledWriteSpec(
           variable_id=write_spec.variable_id,
           ast=ast,
           expression_str=write_spec.expression  # Keep for debugging
       ))
   ```

3. Store in action metadata (e.g., extend `ActionMetadata` DTO)

**New DTO** (required for checkpoint serialization):

```python
# src/townlet/universe/dto/action_metadata.py
@dataclass(frozen=True)
class CompiledWriteSpec:
    """Compiled write specification.

    Stores expression string (not AST) for checkpoint serialization.
    AST is parsed on-demand at runtime and cached per action.
    """
    variable_id: str
    expression_str: str  # Source expression for serialization
    # Note: AST parsed lazily at runtime, not stored here

@dataclass(frozen=True)
class ActionMetadata:
    # ... existing fields ...
    writes: tuple[CompiledWriteSpec, ...] = field(default_factory=tuple)  # NEW
```

**Checkpoint Serialization**:

- `expression_str` is JSON-serializable (just a string)
- No custom serialization logic needed
- AST re-parsed on checkpoint load (small overhead, clean architecture)
- Parser is fast (~0.1ms per expression)

**Permission Validation** (NEW - critical for RC-1):

```python
# Validate write permission
var_def = vfs_registry.variables[write_spec.variable_id]
if "actions" not in var_def.writable_by:
    raise CompilationError(
        f"Action '{action.name}' cannot write to '{write_spec.variable_id}'. "
        f"Variable is writable by: {var_def.writable_by}. "
        f"To fix: Add 'actions' to writable_by list in variables_reference.yaml"
    )
```

**Validation** (comprehensive):

- ❌ Error if `variable_id` not in VFS registry
- ❌ Error if `variable_id` refers to a bar/meter (VFS-only writes enforced)
- ❌ Error if `"actions" not in var_def.writable_by` (permission denied)
- ❌ Error if expression has syntax errors
- ❌ Error if expression references unknown variables (bars must use `bar.X` prefix)
- ❌ Error if expression type-checks fail
- ✅ Clear error messages pointing to config file, line number, and variable name

**VFS-Only Enforcement** (NEW):

```python
# Reject writes to bars - they have their own system
if write_spec.variable_id in bars_config.meter_names:
    raise CompilationError(
        f"Action '{action.name}' cannot write to bar '{write_spec.variable_id}' via WriteSpec. "
        f"Bars are modified via 'costs' and 'effects' fields. "
        f"To use expression-based updates, create a VFS variable instead."
    )
```

### Part 2: Runtime Write Execution (6-8 hours)

**File**: `src/townlet/environment/vectorized_env.py`

**Changes**:

#### 2a. Restructure Custom Action Dispatch for Batching

Current code (per-agent, inefficient):

```python
# BEFORE: Per-agent loop
for agent_idx in custom_agent_indices:
    action_id = int(actions[agent_idx].item())
    action = self.action_space.get_action_by_id(action_id)
    self._apply_custom_action(agent_idx, action)
```

New code (batched by action ID):

```python
# AFTER: Batched execution
if custom_mask.any():
    custom_actions = actions[custom_mask]
    custom_indices = torch.where(custom_mask)[0]

    # Group agents by action ID for batched processing
    for action_id in custom_actions.unique():
        action_mask = custom_actions == action_id
        agent_indices = custom_indices[action_mask]
        action = self.action_space.get_action_by_id(int(action_id.item()))

        # Apply costs/effects/teleport in batch
        self._apply_custom_action_batched(agent_indices, action)

        # Execute VFS writes in batch
        action_metadata = self.universe.action_metadata[int(action_id.item())]
        self._execute_writes(action_metadata, agent_indices)
```

#### 2b. Add Batched Custom Action Method

```python
def _apply_custom_action_batched(
    self,
    agent_indices: torch.Tensor,
    action: ActionConfig,
) -> None:
    """Apply custom action to multiple agents (batched).

    Args:
        agent_indices: Agents performing this action [batch_subset]
        action: Custom action config
    """
    # Apply costs (vectorized)
    for meter_name, cost in action.costs.items():
        meter_idx = self._get_meter_index(meter_name, context=f"action '{action.name}' costs")
        self.meters[agent_indices, meter_idx] -= cost

    # Apply effects (vectorized)
    for meter_name, effect in action.effects.items():
        meter_idx = self._get_meter_index(meter_name, context=f"action '{action.name}' effects")
        self.meters[agent_indices, meter_idx] += effect

    # Apply movement delta (if any)
    if action.delta is not None:
        delta_tensor = torch.tensor(action.delta, device=self.device, dtype=self.substrate.position_dtype)
        delta_batch = delta_tensor.unsqueeze(0).expand(len(agent_indices), -1)
        self.positions[agent_indices] = self.substrate.apply_movement(
            self.positions[agent_indices], delta_batch
        )

    # Handle teleportation (if any)
    if action.teleport_to is not None:
        target_pos = torch.tensor(action.teleport_to, device=self.device, dtype=self.substrate.position_dtype)
        self.positions[agent_indices] = target_pos.unsqueeze(0).expand(len(agent_indices), -1)
```

#### 2c. Add `_execute_writes()` Method

```python
def _execute_writes(
    self,
    action_metadata: ActionMetadata,
    agent_indices: torch.Tensor,
) -> None:
    """Execute ActionConfig.writes to update VFS variables.

    Args:
        action_metadata: Compiled action with write specs
        agent_indices: Which agents performed this action [batch_subset]

    Note: Writes target VFS variables only. Bars are readable via bar.X prefix
    but not writable (use costs/effects for bar modifications).
    """
    if not action_metadata.writes:
        return

    from townlet.world.expression import Evaluator, ExecutionContext

    # Build execution context
    # - bars: readable via "bar.energy", "bar.health", etc.
    # - vfs: readable via direct name "my_variable"
    context = ExecutionContext(
        bars=self._build_bars_context(agent_indices),  # {name: tensor[batch_subset]}
        vfs=self._build_vfs_context(agent_indices),    # {name: tensor[batch_subset]}
        device=self.device,
    )

    evaluator = Evaluator(context)

    for write_spec, ast in zip(action_metadata.writes, self._get_write_asts(action_metadata.id)):
        # Evaluate expression
        try:
            result = evaluator.evaluate(ast)  # torch.Tensor
        except Exception as e:
            raise RuntimeError(
                f"Failed to evaluate write expression for action '{action_metadata.name}': "
                f"variable='{write_spec.variable_id}', expression='{write_spec.expression_str}'. "
                f"Error: {e}"
            ) from e

        # Shape validation and broadcasting
        if result.dim() == 0:
            values = result.expand(len(agent_indices))
        elif result.shape[0] != len(agent_indices):
            raise RuntimeError(
                f"Expression '{write_spec.expression_str}' for action '{action_metadata.name}' "
                f"returned shape {result.shape} but expected {len(agent_indices)} values"
            )
        else:
            values = result

        # Update VFS variable using batched API
        self.vfs_registry.set_partial(
            write_spec.variable_id,
            values,
            agent_indices=agent_indices,
            writer="actions"
        )

def _build_bars_context(self, agent_indices: torch.Tensor) -> dict[str, torch.Tensor]:
    """Build bars context for expression evaluation (subset of agents)."""
    return {
        f"bar.{name}": self.meters[agent_indices, idx]
        for name, idx in self.meter_name_to_index.items()
    }

def _build_vfs_context(self, agent_indices: torch.Tensor) -> dict[str, torch.Tensor]:
    """Build VFS context for expression evaluation (subset of agents)."""
    result = {}
    for var_id in self.vfs_registry.list_agent():
        full_tensor = self.vfs_registry.get_agent(var_id)
        result[var_id] = full_tensor[agent_indices]
    for var_id in self.vfs_registry.list_global():
        result[var_id] = self.vfs_registry.get_global(var_id)
    return result
```

**Performance Optimization** (caching AST parses):

```python
# Cache parsed ASTs per action to avoid re-parsing on every step
class VectorizedHamletEnv:
    def __init__(self, ...):
        self._action_write_asts: dict[int, list[ASTNode]] = {}  # Cache

    def _get_write_asts(self, action_idx: int) -> list[ASTNode]:
        """Get cached AST for action writes (lazy parse + cache)."""
        if action_idx not in self._action_write_asts:
            action = self.universe.action_metadata[action_idx]
            parser = ExpressionParser()
            self._action_write_asts[action_idx] = [
                parser.parse(ws.expression_str) for ws in action.writes
            ]
        return self._action_write_asts[action_idx]
```

**Device Handling** (critical for GPU training):

- Always transfer values to VariableRegistry device before update
- ExecutionContext uses env device for evaluation
- `set_partial()` handles device transfer internally

### Part 3: Contract Validation (Optional Enhancement - 2-3 hours)

**File**: `src/townlet/universe/compiler.py`

**Enhancement**: Validate standard variable contracts at compile time

```python
def _validate_standard_variable_contracts(
    self,
    substrate_type: str,
    vfs_variables: dict[str, VariableDef],
) -> None:
    """Validate required VFS variables exist with correct types/scopes.

    Standard variables required by VectorizedHamletEnv:
    - position (agent, vec2f/vec3f depending on substrate)
    - grid_encoding (agent, varies by substrate)
    - affordance_at_position (agent, bool or categorical)
    - time_sin, time_cos (global, float) - if temporal enabled
    - interaction_progress (agent, float) - if interactions exist
    - lifetime_progress (agent, float)
    """
    required_vars = self._get_required_variables(substrate_type)

    for var_name, expected_spec in required_vars.items():
        if var_name not in vfs_variables:
            raise CompilationError(
                f"Required VFS variable '{var_name}' missing from variables_reference.yaml. "
                f"Add: id={var_name}, type={expected_spec.type}, scope={expected_spec.scope}"
            )

        actual = vfs_variables[var_name]
        if actual.type != expected_spec.type:
            raise CompilationError(
                f"VFS variable '{var_name}' has wrong type: "
                f"expected {expected_spec.type}, got {actual.type}"
            )

        if actual.scope != expected_spec.scope:
            raise CompilationError(
                f"VFS variable '{var_name}' has wrong scope: "
                f"expected {expected_spec.scope}, got {actual.scope}"
            )
```

**Note**: This closes the "implicit contracts" issue from TASK-005B Phase 1. Optional because runtime errors are already clear, but compile-time errors are better UX.

---

## Testing Strategy

### Unit Tests (5-7 hours)

**Test Files**:

- `tests/test_townlet/unit/vfs/test_registry_partial_updates.py` (NEW - VariableRegistry.set_partial)
- `tests/test_townlet/unit/environment/test_action_writes.py` (NEW - action write integration)
- `tests/test_townlet/unit/universe/test_write_spec_compilation.py` (NEW - compile-time validation)

**Test Cases**:

1. **VariableRegistry.set_partial tests** (NEW):

   ```python
   def test_set_partial_updates_subset():
       """set_partial updates only specified agents."""
       registry = VariableRegistry(...)
       registry.set_partial("energy", torch.tensor([0.8, 0.9]), torch.tensor([0, 2]))
       # Assert: Only agents 0 and 2 updated

   def test_set_partial_broadcasts_scalar():
       """Scalar broadcasts to all indices."""
       registry.set_partial("energy", torch.tensor(0.5), torch.tensor([1, 3, 5]))
       # Assert: All three agents get 0.5

   def test_set_partial_validates_permission():
       """Unauthorized writer raises PermissionError."""
       # Variable writable by ["engine"] only
       with pytest.raises(PermissionError):
           registry.set_partial("position", values, indices, writer="actions")

   def test_set_partial_validates_shape():
       """Shape mismatch raises ValueError with clear message."""
       # 3 values but 5 indices
       with pytest.raises(ValueError, match="doesn't match"):
           registry.set_partial("energy", torch.tensor([1,2,3]), torch.tensor([0,1,2,3,4]))
   ```

2. **Compile-time tests**:

   ```python
   def test_write_spec_parses_simple_expression():
       """ActionConfig.writes with simple constant expression."""
       # VFS variable: rest_counter (writable_by=["actions"])
       action = ActionConfig(
           name="TEST",
           type="passive",
           writes=[WriteSpec(variable_id="rest_counter", expression="0.5")]
       )
       # Compile action
       # Assert: AST is Constant(0.5)

   def test_write_spec_parses_complex_expression():
       """ActionConfig.writes with variable reference and bar read."""
       # VFS variable: energy_snapshot (writable_by=["actions"])
       action = ActionConfig(
           name="REST",
           type="passive",
           writes=[WriteSpec(variable_id="energy_snapshot", expression="min(1.0, bar.energy + 0.1)")]
       )
       # Compile action
       # Assert: AST is FunctionCall("min", [Constant(1.0), BinaryOp(...)])

   def test_write_spec_rejects_bar_target():
       """Writing to a bar (not VFS variable) fails with clear error."""
       action = ActionConfig(
           name="BAD",
           type="passive",
           writes=[WriteSpec(variable_id="energy", expression="0.5")]  # energy is a bar!
       )
       # Assert: CompilationError("Cannot write to bar 'energy' via WriteSpec. Use costs/effects instead.")

   def test_write_spec_rejects_invalid_expression():
       """Malformed expression raises clear error."""
       action = ActionConfig(
           name="BAD",
           type="passive",
           writes=[WriteSpec(variable_id="rest_counter", expression="rest_counter ++ 0.1")]  # Invalid
       )
       # Assert: CompilationError with syntax error details

   def test_write_spec_rejects_unknown_variable():
       """Write to non-existent VFS variable fails."""
       action = ActionConfig(
           name="BAD",
           type="passive",
           writes=[WriteSpec(variable_id="nonexistent", expression="1.0")]
       )
       # Assert: CompilationError("VFS variable 'nonexistent' not found")

   def test_write_spec_enforces_permission():
       """Write to variable without 'actions' permission fails."""
       # VFS variable: position (writable_by=["engine"] only)
       action = ActionConfig(
           name="TELEPORT",
           type="passive",
           writes=[WriteSpec(variable_id="position", expression="[3, 3]")]
       )
       # Assert: CompilationError("cannot write to 'position'. Writable by: ['engine']")
   ```

3. **Runtime tests**:

   ```python
   def test_write_spec_updates_vfs_variable():
       """Action execution evaluates write and updates VFS registry."""
       # Setup env with VFS variable "rest_counter" (writable_by=["actions"])
       # Execute action with writes=[WriteSpec("rest_counter", "0.8")]
       # Assert: vfs_registry.get_agent("rest_counter") == 0.8

   def test_write_spec_batched_update():
       """Writes update only agents that performed action."""
       # Setup env with 10 agents, VFS variable "rest_counter"
       # 3 agents perform REST action
       # Assert: Only those 3 agents' rest_counter updated

   def test_write_spec_expression_reads_bar_state():
       """Expression can read bar state via bar.X prefix."""
       # Setup env with bar energy=0.5, VFS variable "energy_snapshot"
       # Execute action with writes=[WriteSpec("energy_snapshot", "bar.energy * 2")]
       # Assert: energy_snapshot updated to 1.0

   def test_write_spec_expression_reads_vfs_state():
       """Expression can read and update VFS state."""
       # Setup env with VFS variable "counter" = 5.0
       # Execute action with writes=[WriteSpec("counter", "counter + 1.0")]
       # Assert: counter updated to 6.0

   def test_write_spec_shape_mismatch_raises():
       """Expression returning wrong shape raises with clear error."""
       # Expression returns shape [10] but only 3 agents performed action
       # Assert: RuntimeError with action name, variable, and shape details

   def test_write_spec_evaluation_error_context():
       """Expression evaluation errors include debugging context."""
       # Expression: "counter / 0" (divide by zero)
       # Assert: RuntimeError mentions action name, variable, expression string
   ```

4. **Checkpoint compatibility tests** (NEW):

   ```python
   def test_action_metadata_serializes_writes():
       """ActionMetadata with writes roundtrips through serialization."""
       metadata = ActionMetadata(
           ...,
           writes=(CompiledWriteSpec("energy", "0.5"),)
       )
       data = metadata.to_dict()
       restored = ActionMetadata.from_dict(data)
       assert restored.writes[0].expression_str == "0.5"

   def test_checkpoint_with_writes_loads():
       """Checkpoint containing actions with writes loads correctly."""
       # Save checkpoint with write-enabled actions
       # Load checkpoint
       # Assert: expression strings preserved, ASTs re-parsed
   ```

### Integration Tests (2-3 hours)

**Test File**: `tests/test_townlet/integration/test_vfs_action_writes.py`

**Test Case**:

```python
def test_rest_action_updates_vfs_via_writes():
    """End-to-end test: REST action uses WriteSpec to update VFS variable."""
    # Create minimal config with:
    # - Bar: energy (standard meter, modified via effects)
    # - VFS variable: rest_accumulator (agent, float, writable_by=["actions"])
    # - Custom action: REST with:
    #     effects: {energy: 0.1}  # Bar modification the normal way
    #     writes: [{variable_id: "rest_accumulator", expression: "rest_accumulator + 1.0"}]

    env = VectorizedHamletEnv(...)
    obs = env.reset()

    # Initial state
    initial_rest = env.vfs_registry.get_agent("rest_accumulator")
    assert torch.allclose(initial_rest, torch.tensor([0.0, 0.0]))

    # Execute REST action
    rest_action_idx = env.action_space.get_action_by_name("REST").id
    obs, reward, done, info = env.step(torch.tensor([rest_action_idx, rest_action_idx]))

    # Verify VFS variable updated
    rest_acc = env.vfs_registry.get_agent("rest_accumulator")
    assert torch.allclose(rest_acc, torch.tensor([1.0, 1.0]))

    # Verify bar also updated (via effects, not writes)
    # This confirms both systems work together
```

**Additional Integration Tests**:

```python
def test_expression_reads_bar_state():
    """WriteSpec expression can read bar values via bar.X prefix."""
    # VFS variable: energy_when_rested (writable_by=["actions"])
    # Action writes: [{variable_id: "energy_when_rested", expression: "bar.energy"}]
    # Verify: VFS variable captures bar value at action time

def test_multiple_actions_with_writes():
    """Multiple actions can write to different VFS variables."""
    # Action A writes to rest_counter
    # Action B writes to work_counter
    # Verify: Both VFS updates work correctly, bars unaffected

def test_write_permission_denied_at_runtime():
    """Write to unauthorized variable fails gracefully."""
    # This shouldn't happen (compile-time check), but defensive
    # Verify: Clear error message, env doesn't crash
```

**Regression Tests** (critical for RC-1):

- ✅ Verify L0-L3 configs still work (no actions use writes yet)
- ✅ Verify old checkpoints still load (backward compatibility)
- ✅ Verify new checkpoints with writes load correctly
- ✅ Verify training runs complete without crashes
- ✅ Verify no performance regression (<1% overhead acceptable)

---

## Migration Guide

### For Existing Configs

**No changes required**:

- Existing configs don't use `writes` field
- Empty `writes: []` is default and no-op
- This is purely enabling a dormant feature

### Design Philosophy: Bars vs VFS

**Bars are the 98% solution** - standard RL meters (energy, health, mood, etc.) that cover most use cases. Modify them with `costs` and `effects` fields.

**VFS is the 2% escape hatch** - when you need custom state that bars don't cover, don't hack the bar system. Build what you actually want using VFS variables and `writes`.

### For New Configs Using Writes

**Example**: Track cumulative rest time (custom metric not suitable for bars)

```yaml
# variables_reference.yaml - define the VFS variable
variables:
  - id: "rest_accumulator"
    scope: "agent"
    type: "scalar"
    lifetime: "episode"
    readable_by: ["agent", "engine"]
    writable_by: ["engine", "actions"]  # Note: "actions" required for writes
    default: 0.0
    description: "Cumulative rest time this episode"

# actions.yaml - use writes to update it
custom_actions:
  - name: "REST"
    type: "passive"
    costs: {}
    effects: {energy: 0.1}  # Bar modification via effects (the 98% way)
    reads: ["rest_accumulator"]
    writes:
      - variable_id: "rest_accumulator"
        expression: "rest_accumulator + 1.0"  # VFS modification via writes (the 2% way)
```

**Example**: Expression reading bar state

```yaml
writes:
  - variable_id: "energy_efficiency"
    expression: "bar.energy * bar.health"  # Read bars via bar.X prefix
```

**What WON'T work** (and the correct alternative):

```yaml
# ❌ WRONG: Trying to write to a bar via WriteSpec
writes:
  - variable_id: "energy"  # This is a bar, not a VFS variable!
    expression: "min(1.0, bar.energy + 0.1)"
# Error: "Cannot write to bar 'energy' via WriteSpec. Use costs/effects instead."

# ✅ CORRECT: Use effects for bar modifications
effects: {energy: 0.1}
```

**Validation**: Compiler will error if:

- `variable_id` doesn't exist in `variables_reference.yaml`
- `variable_id` refers to a bar/meter (use costs/effects instead)
- `"actions"` not in variable's `writable_by` list
- Expression has syntax errors
- Expression references unknown variables

**Debugging**: Set `HAMLET_DEBUG_VFS=1` to log VFS evaluations

---

## Acceptance Criteria (RC-1 Release Quality)

### Must Have (RC-1 Blockers)

- [ ] **VFS-only writes enforced**: Compile-time error if `variable_id` refers to a bar/meter
- [ ] **Batched custom action execution**: Restructure per-agent loop to batch by action ID
- [ ] **VariableRegistry.set_partial() API implemented** with proper validation
- [ ] **Permission validation**: `"actions" in writable_by` checked at compile time
- [ ] **Shape validation**: Expression results validated against agent count at runtime
- [ ] **Device handling**: Proper tensor device transfers in all paths
- [ ] **Checkpoint compatibility**: Expression strings serialize/deserialize correctly
- [ ] `WriteSpec.expression` is parsed at runtime (on-demand with caching)
- [ ] Type checking validates expression against VFS variable types at compile time
- [ ] Unknown variable references raise clear errors (bars require `bar.X` prefix)
- [ ] Action execution evaluates writes and updates VariableRegistry
- [ ] Batched updates work correctly (only agents performing action updated)
- [ ] **Comprehensive unit tests**: Registry API, permissions, shapes, checkpoints, bar rejection
- [ ] **Integration tests**: End-to-end write flow, bar+VFS coexistence, regression tests for L0-L3
- [ ] **Error messages**: Clear context (action, variable, expression, agent index) on failures
- [ ] **BUG-36 closed** with verification that writes actually work
- [ ] **TASK-005B marked complete** (VFS Phase 2 fully implemented)

### Should Have (Quality Improvements)

- [ ] Standard variable contract validation at compile time (Part 3 - optional)
- [ ] Debug logging for write execution (via HAMLET_DEBUG_VFS env var)
- [ ] Example config demonstrating writes (REST action in test fixtures)
- [ ] Performance benchmark showing <1% overhead
- [ ] AST caching optimization (avoid re-parsing per step)

### Documentation (Required for RC-1)

- [ ] Config example in `docs/config-schemas/` showing writes syntax
- [ ] Permission requirements documented (writable_by must include "actions")
- [ ] Migration notes for enabling writes in existing configs
- [ ] CLAUDE.md updated: remove "WriteSpec is dormant", add "VFS2 complete"
- [ ] TASK-005B.md updated to mark as complete with reference to this task

---

## Risk Assessment (From Comprehensive Agent Review)

### 🔴 HIGH RISK

#### RISK-H1: VariableRegistry API Design (RESOLVED)

**Severity**: CRITICAL (was blocker)
**Resolution**: Add `set_partial()` method (proper API for RC-1)

**Decision**: Use Option A (proper API) not Option B (storage hacks)

- Clean API for batched updates
- Proper access control validation
- Release-quality architecture
- +3-4 hours but required for RC-1

#### RISK-H2: Expression Shape Mismatches

**Severity**: HIGH
**Likelihood**: Medium (40%)
**Mitigation**: Comprehensive shape validation with clear error messages

```python
if result.dim() == 0:
    values = result.expand(len(agent_indices))
elif result.shape[0] != len(agent_indices):
    raise RuntimeError(
        f"Expression '{expr_str}' returned shape {result.shape} "
        f"but expected {len(agent_indices)} for action '{action_name}'"
    )
```

#### RISK-H3: Checkpoint Serialization

**Severity**: HIGH
**Likelihood**: High (80%)
**Resolution**: Store expression string, re-parse on load

- Small overhead (parser is fast, ~0.1ms per expression)
- Clean architecture (no custom AST serialization)
- Checkpoint compatibility maintained

### 🟡 MEDIUM RISK

#### RISK-M1: Permission Enforcement

**Severity**: MEDIUM
**Mitigation**: Validate `"actions" in var_def.writable_by` at compile time

```python
if "actions" not in var_def.writable_by:
    raise CompilationError(
        f"Action {action.name} cannot write to {variable_id}. "
        f"Writable by: {var_def.writable_by}"
    )
```

#### RISK-M2: Device Placement

**Severity**: MEDIUM
**Mitigation**: `set_partial()` handles device transfer internally

- Always transfer to VariableRegistry device
- Handled in API, not caller's responsibility

### 🟢 LOW RISK

#### RISK-L1: Performance Overhead

**Severity**: LOW
**Impact**: Expression evaluation in action hot path
**Benchmark**: Effects system (similar) adds <1% overhead
**Mitigation**: AST caching, early exit for empty writes

### Process Risks

**Risk**: Scope creep into new expression features

- **Likelihood**: Low (engine is complete, task explicitly excludes new features)
- **Impact**: Medium (would delay RC-1)
- **Mitigation**: Stick to integration only; defer new features to future tasks

---

## Out of Scope

### Explicitly NOT Included

- ❌ New expression language features (engine is complete)
- ❌ New VFS variable types (scalar/vector/bool sufficient)
- ❌ DAC integration with VFS writes (separate task)
- ❌ Effects system changes (already integrated)
- ❌ Items system changes (already integrated)
- ❌ Frontend visualization of VFS variables

### Future Work

- **TASK-005C**: DAC + VFS integration (vfs_variable reward strategies)
- **TASK-005D**: VFS observation builder enhancements
- **TASK-006**: Frontend VFS inspector tool

---

## Dependencies

### Completed Prerequisites

- ✅ TASK-002C (VFS Phase 1) - schema, registry, observation specs
- ✅ Expression engine - 2,428 lines, production-ready
- ✅ VFSEvaluator - mark-and-sweep, dependency tracking
- ✅ Effects/Items integration - expression engine in use

### Blockers

- None (all dependencies satisfied)

---

## References

**Related Tasks**:

- TASK-005B-VFS2.md (parent task - now ~90% complete)
- TASK-002C-VARIABLE-FEATURE-SYSTEM.md (VFS Phase 1)

**Related Bugs**:

- BUG-36 (WriteSpec unused) - **this task closes it**
- BUG-38 (metadata threading) - closed 2025-11-30
- BUG-28 (semantic_type) - verified complete

**Key Files**:

- `src/townlet/world/expression/` - expression engine (2,428 lines)
- `src/townlet/vfs/evaluator.py` - VFSEvaluator with mark-and-sweep
- `src/townlet/environment/vectorized_env.py` - action execution path
- `src/townlet/universe/compiler.py` - action compilation

**External Dependencies**:

- pyparsing (already in use for expression parsing)
- torch (already in use everywhere)

---

## Effort Breakdown (Revised After Design Review)

| Task | Estimated Hours | Notes |
|------|----------------|-------|
| Part 0: VariableRegistry.set_partial() API | 3-4 | Batched updates, permission validation, device handling |
| Part 1: Compile-time parsing + DTO changes | 4-6 | ActionMetadata extension, VFS-only validation, permission checks |
| Part 2a: Batched custom action restructure | 2-3 | Replace per-agent loop with grouped execution |
| Part 2b: Runtime write execution + caching | 4-5 | AST caching, shape validation, bar.X context building |
| Part 3: Contract validation (optional) | 2-3 | Standard variable validation at compile time |
| Unit tests (comprehensive) | 5-7 | Registry API, permissions, shapes, bar rejection, checkpoints |
| Integration tests + regression | 2-3 | End-to-end flow, bar+VFS coexistence, L0-L3 verification |
| Documentation updates | 1-2 | Config examples, 98%/2% philosophy, migration guide |
| **Total** | **20-28 hours** | Includes batched restructure and VFS-only enforcement |

**Why the Increase**:

- Original estimate: 10-14 hours (assumed simple plumbing)
- Risk assessment revealed: 3 hidden architectural requirements not in original task
  1. VariableRegistry lacks batched API (+3-4 hours)
  2. ActionMetadata DTO needs extension (+2-3 hours)
  3. AST serialization for checkpoints (+2 hours)
- Design decisions added scope:
  1. VFS-only writes enforcement (+1 hour compile-time validation)
  2. Batched custom action restructure (+2-3 hours)
  3. Expression namespace with `bar.X` prefix (+1 hour context building)
- Additional RC-1 quality requirements: permission validation, shape validation, error context (+3-4 hours)
- Comprehensive testing for release quality (+2-3 hours)

**Confidence Level**: High (75%) - Expression engine is stable, integration patterns exist in effects system

**Note**: Original TASK-005B estimated 60-80 hours assuming expression engine would be built from scratch. Since engine exists (90% complete), 20-28 hours of **release-quality** integration work remains (including architectural decisions for VFS-only writes and batched execution).

---

## Success Metrics

**Completion Criteria**:

1. BUG-36 closed
2. TASK-005B marked complete
3. All tests passing (unit + integration)
4. Example config demonstrating writes working
5. No regression in L0-L3 curriculum training

**Quality Gates**:

- Zero test failures
- Type checker coverage >80%
- Clear error messages for all validation failures
- Performance overhead <1% (benchmark REST action)

---

## Notes for Implementation

**Critical Path (RC-1 Focus)**:

1. **Part 0**: Add `VariableRegistry.set_partial()` method (3-4h) - FOUNDATION
2. **Part 1**: Extend ActionMetadata DTO + compile-time parsing (4-6h)
3. **Part 2**: Runtime execution + AST caching (6-8h)
4. **Unit Tests**: Comprehensive coverage (5-7h)
5. **Integration**: End-to-end + regression (2-3h)
6. **Documentation**: Config examples + migration (1-2h)

**Start Here**:

1. **Read existing patterns**:
   - Line 1686 of vectorized_env.py (VFS storage pattern)
   - Line 1823 of vectorized_env.py (batched meter updates)
   - `effects/compiler.py:55` (expression parsing pattern)
   - `vfs/evaluator.py` (VFSEvaluator pattern for reference)
2. **Implement VariableRegistry.set_partial() FIRST** (enables all other work)
3. **Add unit test for simplest case**: constant write (`expression: "0.5"`)
4. **Implement compile-time parsing with permission checks**
5. **Implement runtime execution with shape validation**
6. **Add integration test (REST action example)**
7. **Regression test L0-L3** to ensure no breakage
8. **Close BUG-36** with evidence that writes work

**Common Pitfalls (From Risk Assessment)**:

- ❌ Don't allow writes to bars (reject at compile time with clear error pointing to costs/effects)
- ❌ Don't use direct `_storage` access (add proper API for RC-1)
- ❌ Don't rebuild expression features that exist (reuse everything)
- ❌ Don't keep the per-agent custom action loop (restructure for batching)
- ⚠️ Expressions read bars via `bar.X` prefix, VFS via direct name
- ⚠️ Watch tensor shapes in batched updates (validate at runtime)
- ⚠️ Test both scalar and batched expression results
- ⚠️ Handle empty `writes: []` gracefully (early exit, no overhead)
- ⚠️ Device placement: always `.to(registry.device)` before updates
- ⚠️ Permission validation: check `writable_by` at compile time
- ⚠️ Error context: include action name, variable, expression in all errors

**Quick Wins**:

- Effects system has working integration pattern (copy it)
- Evaluator and ExecutionContext APIs are stable and tested
- Type checker will catch most errors at compile time
- Parser is fast (~0.1ms) so re-parsing on load is acceptable
