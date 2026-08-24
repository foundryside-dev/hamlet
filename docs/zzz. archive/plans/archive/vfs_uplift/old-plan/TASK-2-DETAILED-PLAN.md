# Task 2: Runtime VFS Evaluation (Mark-and-Sweep) - Implementation Plan

> **For Claude:** REQUIRED EXECUTION SKILL: Use `superpowers:subagent-driven-development` to execute this plan task-by-task with code review between tasks.

**Goal:** Execute VFS expressions at runtime using compiled profiles with mark-and-sweep evaluation

**Architecture:** Create VFSEvaluator to evaluate compiled expressions in topological order, add compile-time marking to identify which VFS variables are observed, integrate with VariableRegistry, and update observation builder to use compiled profiles.

**Tech Stack:** PyTorch, networkx (topo sort), Pydantic, existing expression evaluator

**Estimated Duration:** 3-4 days
**Test Target:** 8-10 new tests

---

## Context

**Current State (after Task 1):**
- ✅ VFS profiles compiled into `CompiledUniverse.compiled_vfs_profiles`
- ✅ Expression evaluator exists (`townlet.world.expression.evaluator.Evaluator`)
- ✅ ExecutionContext exists for expression evaluation
- ✅ VariableRegistry exists for VFS storage (`townlet.vfs.registry`)
- ❌ VFS expressions NOT evaluated at runtime (profiles ignored)
- ❌ No marking system (all variables would be evaluated, inefficient)
- ❌ `variables_reference.yaml` still loaded at runtime (needs replacement)

**Target State:**
- ✅ VFS expressions evaluated at runtime using compiled profiles
- ✅ Mark-and-sweep mode: only evaluate variables needed for observations
- ✅ Compile-time marking identifies observed variables
- ✅ Registry initialized from compiled profiles (not `variables_reference.yaml`)
- ✅ Observation builder uses compiled item profiles with masking

---

## Subtask 2.1: Add VFS Observation Marking to Compiler

**Files:**
- Modify: `src/townlet/universe/compiler.py` (add marking logic)
- Modify: `src/townlet/universe/compiled.py` (add vfs_observation_marks field)
- Test: `tests/test_townlet/unit/universe/test_vfs_observation_marking.py` (new file)

**Duration:** ~1 day

### Step 2.1.1: Write failing test for VFS observation marking

**Test:** `tests/test_townlet/unit/universe/test_vfs_observation_marking.py`

```python
"""Tests for VFS observation marking in UniverseCompiler."""

from pathlib import Path
import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler


def test_compiler_marks_vfs_variables_used_in_observations(tmp_path: Path):
    """Compiler should mark which VFS variables appear in observation fields."""
    # Setup: Create config with VFS profiles and observations
    from tests.test_townlet.unit.universe.config_builder import prepare_config_dir

    vfs_profiles = {
        "global_profile": {
            "variables": [
                {"name": "day_count", "type": "int", "initial_value": 0},
                {"name": "unused_var", "type": "int", "initial_value": 0},
            ]
        }
    }

    # Create observation that uses day_count but NOT unused_var
    variables_ref = {
        "variables": [
            {
                "id": "day_count",
                "scope": "global",
                "type": "scalar",
                "default_value": 0,
                "readers": ["agent"],
                "writers": ["engine"],
                "observable": True,  # This marks it for observation
            },
            {
                "id": "unused_var",
                "scope": "global",
                "type": "scalar",
                "default_value": 0,
                "readers": ["agent"],
                "writers": ["engine"],
                "observable": False,  # NOT in observations
            },
        ]
    }

    config_dir = prepare_config_dir(
        tmp_path,
        vfs_profiles=vfs_profiles,
        variables_reference=variables_ref,
    )

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="test_level", use_cache=False)

    # Verify: day_count is marked, unused_var is not
    assert compiled.vfs_observation_marks is not None
    assert "day_count" in compiled.vfs_observation_marks["global"]
    assert "unused_var" not in compiled.vfs_observation_marks["global"]


def test_compiler_marks_empty_when_no_vfs_observations():
    """Compiler should handle configs without VFS observations."""
    # Setup: Config with NO VFS variables in observations
    # ... (minimal fixture)

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="test_level", use_cache=False)

    # Verify: marks are empty or None
    assert compiled.vfs_observation_marks is None or len(compiled.vfs_observation_marks.get("global", set())) == 0
```

**Expected:** Tests FAIL (field doesn't exist yet)

### Step 2.1.2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_vfs_observation_marking.py::test_compiler_marks_vfs_variables_used_in_observations -xvs
```

**Expected Output:**
```
FAILED - AttributeError: 'CompiledUniverse' object has no attribute 'vfs_observation_marks'
```

### Step 2.1.3: Add vfs_observation_marks field to CompiledUniverse

**File:** `src/townlet/universe/compiled.py`

Add field after `vfs_expression_schema`:

```python
@dataclass(frozen=True)
class CompiledUniverse:
    """Compiled universe representation with multi-level support."""

    # ... existing fields ...

    # NEW: Marks for which VFS variables are observed (for mark-and-sweep)
    vfs_observation_marks: dict[str, set[str]] | None = None
    # Format: {"global": {"day_count", "is_night"}, "agent": {"motivation"}, "item": {...}}

    # ... rest of code ...
```

**Location:** After line 87 (after `vfs_expression_schema`)

### Step 2.1.4: Add VFS observation marking to UniverseCompiler

**File:** `src/townlet/universe/compiler.py`

Add method to extract marks from variables_reference.yaml:

```python
# Add after _build_vfs_expression_schema method (around line 244)

def _extract_vfs_observation_marks(
    self,
    variables: tuple[VariableDef, ...]
) -> dict[str, set[str]]:
    """Extract which VFS variables are marked for observation.

    Args:
        variables: VFS variables from variables_reference.yaml

    Returns:
        Dict mapping scope to set of observed variable names
        Example: {"global": {"day_count"}, "agent": {"motivation"}}
    """
    marks: dict[str, set[str]] = {
        "global": set(),
        "agent": set(),
        "item": set(),
    }

    for var in variables:
        # Variables with observable=True are included in observations
        if var.observable:
            scope_key = var.scope.value if hasattr(var.scope, "value") else str(var.scope)

            # Map VariableScope to mark keys
            if scope_key == "global":
                marks["global"].add(var.id)
            elif scope_key in ("agent", "agent_private"):
                marks["agent"].add(var.id)
            # TODO: Handle item-scoped variables (Task 3)

    # Remove empty scopes
    return {k: v for k, v in marks.items() if v}
```

Update compile() method to extract marks:

```python
# In compile() method, after building vfs_expression_schema (around line 495)

# Extract VFS observation marks for mark-and-sweep evaluation
vfs_observation_marks = self._extract_vfs_observation_marks(vfs_variables)

# ... when constructing CompiledUniverse (around line 515) ...

return CompiledUniverse(
    # ... existing fields ...
    vfs_observation_marks=vfs_observation_marks,
    # ... rest of fields ...
)
```

### Step 2.1.5: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_vfs_observation_marking.py -xvs
```

**Expected:** PASS (2/2 tests)

### Step 2.1.6: Commit VFS observation marking

```bash
git add src/townlet/universe/compiled.py src/townlet/universe/compiler.py tests/test_townlet/unit/universe/test_vfs_observation_marking.py
git commit -m "feat(compiler): add VFS observation marking for mark-and-sweep

- Add vfs_observation_marks field to CompiledUniverse
- Extract marks from variables_reference.yaml (observable=True)
- Mark variables included in agent observations
- Tests verify marking logic

Task 2.1 complete (VFS observation marking)"
```

---

## Subtask 2.2: Create VFSEvaluator with Mark-and-Sweep

**Files:**
- Create: `src/townlet/vfs/evaluator.py` (new file)
- Test: `tests/test_townlet/unit/vfs/test_vfs_evaluator.py` (new file)

**Duration:** ~1 day

### Step 2.2.1: Write failing test for VFS evaluator

**Test:** `tests/test_townlet/unit/vfs/test_vfs_evaluator.py`

```python
"""Tests for VFS expression evaluator."""

import torch
import pytest

from townlet.vfs.evaluator import VFSEvaluator, EvaluationMode
from townlet.vfs.profiles import CompiledVariable, CompiledGlobalProfile
from townlet.world.expression import ExpressionParser


def test_vfs_evaluator_evaluates_expressions_in_topo_order():
    """VFS evaluator should evaluate variables in dependency order."""
    # Setup: Create profile with dependencies (b depends on a)
    parser = ExpressionParser()

    variables = [
        CompiledVariable(
            name="a",
            type="int",
            ast=None,
            initial_value=5,
            result_type="int",
        ),
        CompiledVariable(
            name="b",
            type="int",
            ast=parser.parse("a + 10"),  # Depends on "a"
            initial_value=None,
            result_type="int",
        ),
    ]

    profile = CompiledGlobalProfile(variables=variables)

    # Create context with initial values
    bars = {"energy": torch.tensor([1.0])}
    vfs_state = {"a": torch.tensor([5])}  # Initial value for "a"

    # Exercise: Evaluate profile
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars=bars,
        vfs_state=vfs_state,
        device=torch.device("cpu"),
    )

    # Verify: "b" should be evaluated to a + 10 = 15
    assert result["a"].item() == 5
    assert result["b"].item() == 15


def test_vfs_evaluator_mark_and_sweep_only_evaluates_marked_vars():
    """Mark-and-sweep mode should only evaluate observed variables."""
    # Setup: 3 variables, only 1 marked for observation
    parser = ExpressionParser()

    variables = [
        CompiledVariable(name="observed", type="int", ast=parser.parse("1 + 1"), initial_value=None, result_type="int"),
        CompiledVariable(name="unobserved", type="int", ast=parser.parse("2 + 2"), initial_value=None, result_type="int"),
    ]

    profile = CompiledGlobalProfile(variables=variables)

    # Exercise: Evaluate with mark-and-sweep (only "observed")
    evaluator = VFSEvaluator(mode=EvaluationMode.MARK_AND_SWEEP)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars={},
        vfs_state={},
        marks={"observed"},  # Only this variable marked
        device=torch.device("cpu"),
    )

    # Verify: Only "observed" is evaluated
    assert "observed" in result
    assert "unobserved" not in result


def test_vfs_evaluator_eager_mode_evaluates_all_vars():
    """Eager mode should evaluate all variables regardless of marks."""
    # Setup: Same as mark-and-sweep test
    parser = ExpressionParser()

    variables = [
        CompiledVariable(name="var1", type="int", ast=parser.parse("1"), initial_value=None, result_type="int"),
        CompiledVariable(name="var2", type="int", ast=parser.parse("2"), initial_value=None, result_type="int"),
    ]

    profile = CompiledGlobalProfile(variables=variables)

    # Exercise: Evaluate with eager mode
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars={},
        vfs_state={},
        marks=set(),  # Empty marks, but eager should evaluate all
        device=torch.device("cpu"),
    )

    # Verify: Both variables evaluated
    assert "var1" in result
    assert "var2" in result
```

**Expected:** Tests FAIL (module doesn't exist)

### Step 2.2.2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_vfs_evaluator.py::test_vfs_evaluator_evaluates_expressions_in_topo_order -xvs
```

**Expected Output:**
```
ModuleNotFoundError: No module named 'townlet.vfs.evaluator'
```

### Step 2.2.3: Implement VFSEvaluator

**File:** `src/townlet/vfs/evaluator.py` (new file)

```python
"""VFS expression evaluator with mark-and-sweep support."""

from __future__ import annotations

from enum import Enum

import torch

from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator

__all__ = ["VFSEvaluator", "EvaluationMode"]


class EvaluationMode(str, Enum):
    """VFS evaluation mode."""

    MARK_AND_SWEEP = "mark_and_sweep"  # Only evaluate observed variables
    EAGER = "eager"  # Evaluate all variables (debug mode)


class VFSEvaluator:
    """Evaluates VFS expressions using compiled profiles."""

    def __init__(self, mode: EvaluationMode = EvaluationMode.MARK_AND_SWEEP):
        """Initialize VFS evaluator.

        Args:
            mode: Evaluation mode (mark_and_sweep or eager)
        """
        self.mode = mode

    def evaluate_global_profile(
        self,
        profile: CompiledGlobalProfile,
        bars: dict[str, torch.Tensor],
        vfs_state: dict[str, torch.Tensor],
        marks: set[str] | None = None,
        device: torch.device = torch.device("cpu"),
    ) -> dict[str, torch.Tensor]:
        """Evaluate global VFS profile expressions.

        Args:
            profile: Compiled global profile with variables in topo order
            bars: Bar state (e.g., {"energy": tensor([batch])})
            vfs_state: Current VFS state (inputs for expressions)
            marks: Set of variable names to evaluate (for mark-and-sweep)
            device: PyTorch device

        Returns:
            Dict mapping variable names to evaluated tensors
        """
        # Determine which variables to evaluate
        if self.mode == EvaluationMode.MARK_AND_SWEEP:
            if marks is None:
                marks = set()
            vars_to_eval = marks
        else:  # EAGER mode
            vars_to_eval = {var.name for var in profile.variables}

        # Build execution context
        context = ExecutionContext(
            bars=bars,
            vfs=vfs_state.copy(),  # Copy so we can update during evaluation
            affordances={},  # TODO: Add affordance support (Task 3)
            temporal={},    # TODO: Add temporal support (Task 3)
            device=device,
        )

        evaluator = Evaluator(context)
        result = {}

        # Evaluate variables in topological order (profile.variables already sorted)
        for var in profile.variables:
            # Skip if not in evaluation set (mark-and-sweep)
            if var.name not in vars_to_eval:
                continue

            # Static initial value (no expression)
            if var.ast is None:
                value = torch.tensor(var.initial_value, device=device)
            else:
                # Evaluate expression using current context
                value = evaluator.evaluate(var.ast)

            # Store result
            result[var.name] = value
            # Update context so later variables can reference this one
            context.vfs[var.name] = value

        return result
```

**Location:** New file at `src/townlet/vfs/evaluator.py`

### Step 2.2.4: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_vfs_evaluator.py -xvs
```

**Expected:** PASS (3/3 tests)

### Step 2.2.5: Commit VFS evaluator

```bash
git add src/townlet/vfs/evaluator.py tests/test_townlet/unit/vfs/test_vfs_evaluator.py
git commit -m "feat(vfs): add VFSEvaluator with mark-and-sweep support

- Create VFSEvaluator for runtime expression evaluation
- Support MARK_AND_SWEEP mode (only evaluate observed vars)
- Support EAGER mode (evaluate all vars, debug)
- Evaluate expressions in topological order
- Update execution context as variables are evaluated
- Tests verify topo order and mark-and-sweep logic

Task 2.2 complete (VFS evaluator)"
```

---

## Subtask 2.3: Integrate VFSEvaluator into VectorizedEnv

**Files:**
- Modify: `src/townlet/environment/vectorized_env.py` (integrate evaluator)
- Test: `tests/test_townlet/integration/test_vfs_runtime_evaluation.py` (new file)

**Duration:** ~1 day

### Step 2.3.1: Write failing integration test

**Test:** `tests/test_townlet/integration/test_vfs_runtime_evaluation.py`

```python
"""Integration tests for VFS runtime evaluation."""

from pathlib import Path
import torch

from townlet.universe.compiler import UniverseCompiler


def test_vfs_expressions_evaluated_at_runtime():
    """VFS expressions should be evaluated during environment step."""
    # Setup: Compile universe with VFS profiles
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="effects_smoke", use_cache=False)

    # Create environment
    env = compiled.create_environment(
        num_agents=4,
        level_name="effects_smoke",
        device=torch.device("cpu"),
    )

    # Exercise: Step environment
    env.reset()
    obs, rewards, dones, info = env.step(torch.zeros(4, dtype=torch.long))

    # Verify: VFS variables should be in registry and updated
    # (day_count should increment each step if expression is "day_count + 1")
    assert hasattr(env, "vfs_registry")
    # Check that global VFS variables exist
    assert "day_count" in env.vfs_registry._storage or "day_count" in env.vfs_registry.variables
```

**Expected:** Test FAILS (VFS evaluation not wired in)

### Step 2.3.2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_vfs_runtime_evaluation.py::test_vfs_expressions_evaluated_at_runtime -xvs
```

**Expected:** FAIL (VFS expressions not evaluated)

### Step 2.3.3: Integrate VFSEvaluator into vectorized_env

**File:** `src/townlet/environment/vectorized_env.py`

Add imports at top of file:

```python
# After existing VFS imports (around line 50)
from townlet.vfs.evaluator import VFSEvaluator, EvaluationMode
```

Add VFS evaluator initialization in `__init__`:

```python
# In __init__, after VFS registry initialization (around line 300)

# Initialize VFS evaluator (if profiles present)
self.vfs_evaluator: VFSEvaluator | None = None
if compiled_universe.compiled_vfs_profiles is not None:
    # Default to mark-and-sweep for efficiency
    # Can override with EAGER mode via env var for debugging
    import os
    mode = EvaluationMode.EAGER if os.getenv("VFS_EVAL_MODE") == "eager" else EvaluationMode.MARK_AND_SWEEP

    self.vfs_evaluator = VFSEvaluator(mode=mode)
    self.vfs_observation_marks = compiled_universe.vfs_observation_marks
```

Add VFS evaluation to step loop:

```python
# In step() method, after meter updates (around line 600)

# Evaluate VFS expressions if evaluator present
if self.vfs_evaluator is not None and self.compiled_universe.compiled_vfs_profiles is not None:
    # Build execution context from current state
    bars_dict = {
        name: self.bars[:, idx]
        for name, idx in self.meter_name_to_index.items()
    }

    # Get current VFS state from registry
    current_vfs_state = {}
    for var_name in self.vfs_registry.variables.keys():
        if var_name in self.vfs_registry._storage:
            current_vfs_state[var_name] = self.vfs_registry._storage[var_name]

    # Evaluate global profile
    global_profile = self.compiled_universe.compiled_vfs_profiles.global_profile
    if global_profile is not None:
        marks = self.vfs_observation_marks.get("global", set()) if self.vfs_observation_marks else None

        updated_vfs = self.vfs_evaluator.evaluate_global_profile(
            profile=global_profile,
            bars=bars_dict,
            vfs_state=current_vfs_state,
            marks=marks,
            device=self.device,
        )

        # Write updated values back to registry
        for var_name, value in updated_vfs.items():
            if var_name in self.vfs_registry.variables:
                self.vfs_registry._storage[var_name] = value
```

**Location:** After meter updates in step() method

### Step 2.3.4: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_vfs_runtime_evaluation.py::test_vfs_expressions_evaluated_at_runtime -xvs
```

**Expected:** PASS

### Step 2.3.5: Commit VFS runtime integration

```bash
git add src/townlet/environment/vectorized_env.py tests/test_townlet/integration/test_vfs_runtime_evaluation.py
git commit -m "feat(env): integrate VFS evaluator into step loop

- Initialize VFSEvaluator in VectorizedHamletEnv.__init__
- Evaluate VFS expressions each step after meter updates
- Use mark-and-sweep by default (EAGER mode via VFS_EVAL_MODE env var)
- Write evaluated values back to registry
- Integration test verifies VFS evaluation at runtime

Task 2.3 complete (VFS runtime integration)"
```

---

## Subtask 2.4: Update CompiledUniverse Serialization for Marks

**Files:**
- Modify: `src/townlet/universe/compiled.py` (add marks serialization)
- Test: `tests/test_townlet/unit/universe/test_compiled_universe_serialization.py` (update existing tests)

**Duration:** ~0.5 days

### Step 2.4.1: Write failing serialization test

**Test:** Add to `tests/test_townlet/unit/universe/test_compiled_universe_serialization.py`

```python
def test_compiled_universe_serializes_vfs_observation_marks(minimal_compiled_universe_with_profiles):
    """CompiledUniverse.to_dict() should serialize VFS observation marks."""
    # Exercise
    data = minimal_compiled_universe_with_profiles.to_dict()

    # Verify
    assert "vfs_observation_marks" in data


def test_compiled_universe_deserializes_vfs_observation_marks(minimal_compiled_universe_with_profiles):
    """CompiledUniverse.from_dict() should deserialize VFS observation marks."""
    # Setup
    data = minimal_compiled_universe_with_profiles.to_dict()

    # Exercise
    restored = CompiledUniverse.from_dict(data)

    # Verify
    assert restored.vfs_observation_marks is not None
```

**Expected:** Tests FAIL (marks not serialized)

### Step 2.4.2: Update serialization methods

**File:** `src/townlet/universe/compiled.py`

Update `to_dict()`:

```python
# In to_dict(), after vfs_expression_schema (around line 197)

"vfs_expression_schema": self.vfs_expression_schema,
"vfs_observation_marks": (
    {k: list(v) for k, v in self.vfs_observation_marks.items()}
    if self.vfs_observation_marks is not None
    else None
),  # Convert sets to lists for JSON serialization
```

Update `from_dict()`:

```python
# In from_dict(), after vfs_expression_schema (around line 303)

vfs_expression_schema=payload.get("vfs_expression_schema"),
vfs_observation_marks=(
    {k: set(v) for k, v in payload["vfs_observation_marks"].items()}
    if payload.get("vfs_observation_marks") is not None
    else None
),  # Convert lists back to sets
```

Update `clone()`:

```python
# In clone(), after vfs_expression_schema (around line 160)

vfs_expression_schema=deepcopy(self.vfs_expression_schema) if self.vfs_expression_schema is not None else None,
vfs_observation_marks=deepcopy(self.vfs_observation_marks) if self.vfs_observation_marks is not None else None,
```

### Step 2.4.3: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_compiled_universe_serialization.py -xvs
```

**Expected:** All tests PASS (including 2 new tests)

### Step 2.4.4: Commit serialization updates

```bash
git add src/townlet/universe/compiled.py tests/test_townlet/unit/universe/test_compiled_universe_serialization.py
git commit -m "feat(compiler): add serialization for vfs_observation_marks

- Serialize vfs_observation_marks in to_dict() (sets → lists)
- Deserialize vfs_observation_marks in from_dict() (lists → sets)
- Update clone() to include marks
- Tests verify round-trip serialization

Task 2.4 complete (Marks serialization)"
```

---

## Subtask 2.5: Integration Tests and Documentation

**Files:**
- Test: `tests/test_townlet/integration/test_vfs_runtime_evaluation.py` (expand tests)
- Modify: `docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md` (update status)

**Duration:** ~0.5 days

### Step 2.5.1: Expand integration tests

**Test:** Add to `tests/test_townlet/integration/test_vfs_runtime_evaluation.py`

```python
def test_mark_and_sweep_only_evaluates_observed_vars():
    """Mark-and-sweep should only evaluate variables in observations."""
    # Setup: Config with 2 VFS vars, only 1 observed
    # ... (create test config)

    # Exercise: Run environment
    env = compiled.create_environment(...)
    env.reset()
    env.step(actions)

    # Verify: Only observed variable was evaluated
    # (can check via logging or registry state)


def test_eager_mode_evaluates_all_vars():
    """Eager mode should evaluate all VFS variables."""
    import os
    os.environ["VFS_EVAL_MODE"] = "eager"

    # Exercise: Same as mark-and-sweep test
    # ...

    # Verify: All variables evaluated

    del os.environ["VFS_EVAL_MODE"]
```

### Step 2.5.2: Run all Task 2 tests

```bash
UV_CACHE_DIR=.uv-cache uv run pytest \
  tests/test_townlet/unit/universe/test_vfs_observation_marking.py \
  tests/test_townlet/unit/vfs/test_vfs_evaluator.py \
  tests/test_townlet/integration/test_vfs_runtime_evaluation.py \
  -xvs
```

**Expected:** All tests PASS (~8-10 tests total)

### Step 2.5.3: Update documentation

**File:** `docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md`

Add Task 2 status section:

```markdown
### Task 2: Runtime VFS Evaluation ✅ COMPLETE

**Status:** 100% complete
**Timeline:** Planned 3-4 days | Actual: X days
**Test Coverage:** 10 tests (100% passing)

**Deliverables:**
- ✅ VFS observation marking at compile time
- ✅ VFSEvaluator with mark-and-sweep support
- ✅ Runtime integration in VectorizedHamletEnv
- ✅ Serialization support for observation marks
- ✅ Integration tests

**Commits:** [list commit SHAs]
```

### Step 2.5.4: Commit documentation

```bash
git add docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md tests/test_townlet/integration/test_vfs_runtime_evaluation.py
git commit -m "docs: mark Task 2 (Runtime VFS evaluation) as COMPLETE

Task 2 delivered:
- VFS expressions evaluated at runtime ✅
- Mark-and-sweep evaluation mode ✅
- Compile-time observation marking ✅
- Runtime integration complete ✅
- 10 new tests passing

Next: Task 3 (Item VFS integration)"
```

---

## Task 2 Success Criteria

**Functional:**
- ✅ VFS expressions evaluated at runtime using compiled profiles
- ✅ Mark-and-sweep mode: only evaluate observed variables
- ✅ Eager mode available for debugging
- ✅ Compile-time marking identifies observed variables
- ✅ Execution context includes bars + VFS state
- ✅ VFS state updated in registry after evaluation

**Tests:**
- ✅ 8-10 new tests passing
- ✅ All existing tests still pass

**Code Quality:**
- ✅ VFSEvaluator reuses existing Evaluator infrastructure
- ✅ No breaking changes to existing API
- ✅ Serialization supports new fields

---

## Notes for Engineer

**Key Design Decisions:**

1. **Mark-and-sweep is default, eager is debug:**
   - Mark-and-sweep: Only evaluate VFS variables that appear in observations (efficient)
   - Eager: Evaluate all variables (useful for debugging, controlled by `VFS_EVAL_MODE` env var)

2. **Evaluation happens in step loop:**
   - After meter updates, before observation building
   - Uses current bar state and previous VFS state as inputs
   - Writes updated values back to registry

3. **Topological order preserved:**
   - VFSProfileCompiler already sorts variables in dependency order
   - VFSEvaluator evaluates in that order, updating context as it goes

4. **Marks extracted from variables_reference.yaml:**
   - Variables with `observable: true` are marked for evaluation
   - Marks stored in CompiledUniverse for runtime use

**Common Pitfalls:**

- Don't evaluate expressions before reading current state from registry
- Don't forget to update context.vfs as variables are evaluated (dependencies!)
- Don't serialize sets directly (convert to lists first for JSON compatibility)
- Don't break when `compiled_vfs_profiles` is None (some configs don't use VFS)

**Testing Strategy:**

- Unit tests: Test VFSEvaluator in isolation with mock profiles
- Integration tests: Test full environment with real config packs
- Test both mark-and-sweep and eager modes
- Verify topo order by creating dependencies (b depends on a)

---

## Execution Handoff

**Plan complete and saved to `docs/plans/vfs_uplift/TASK-2-DETAILED-PLAN.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - Dispatch fresh subagent per subtask, review between subtasks, fast iteration with quality gates

**2. Parallel Session (separate)** - Open new session with `/superpowers:execute-plan`, batch execution with checkpoints

**Which approach?**
