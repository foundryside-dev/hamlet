# Task 1.4: Expression Evaluator - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an evaluator that executes AST expressions on GPU tensors, producing runtime values.

**Architecture:** AST Visitor pattern. Executes bottom-up, returns PyTorch tensors. Execution context provides bars/vfs/affordance state.

**Tech Stack:** PyTorch (GPU tensors), Python 3.11+

**Dependencies:** Task 1.1 (AST), Task 1.2 (Parser), Task 1.3 (Type Checker) complete

---

## Implementation Note

Due to plan length, this is a condensed version covering essentials. Full function registry and all domain functions will be completed during implementation with additional tests.

---

## Task Breakdown

### Step 1: Create execution context

**File:** `src/townlet/world/expression/context.py`

```python
"""Execution context for expression evaluation."""
import torch
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ExecutionContext:
    """Runtime context for expression evaluation.

    Provides access to simulation state:
    - bars: Meter values (energy, health, etc.)
    - vfs: Variable & Feature System state
    - affordances: Affordance positions/states
    - temporal: Time-based values (tick count, day/night)
    """

    bars: Dict[str, torch.Tensor]  # e.g., {"energy": tensor([batch])}
    vfs: Dict[str, torch.Tensor]
    affordances: Dict[str, Any]  # Affordance state
    temporal: Dict[str, torch.Tensor]  # Time values
    device: torch.device = torch.device("cpu")

    def get(self, path: str) -> torch.Tensor:
        """Resolve dotted path to tensor value.

        Args:
            path: Dotted path like "bar.energy" or "vfs.is_night"

        Returns:
            Tensor value from context

        Raises:
            KeyError: If path not found
        """
        parts = path.split(".")
        if parts[0] == "bar" and len(parts) == 2:
            return self.bars[parts[1]]
        elif parts[0] == "vfs" and len(parts) >= 2:
            return self.vfs[".".join(parts[1:])]
        elif parts[0] == "temporal" and len(parts) == 2:
            return self.temporal[parts[1]]
        else:
            raise KeyError(f"Path '{path}' not found in execution context")
```

**File:** `tests/test_townlet/unit/world/expression/test_context.py`

```python
"""Tests for execution context."""
import torch
import pytest
from townlet.world.expression.context import ExecutionContext


def test_execution_context_get_bar():
    """Context resolves bar paths."""
    ctx = ExecutionContext(
        bars={"energy": torch.tensor([0.5, 0.8])},
        vfs={},
        affordances={},
        temporal={},
    )

    result = ctx.get("bar.energy")
    assert torch.equal(result, torch.tensor([0.5, 0.8]))


def test_execution_context_get_vfs():
    """Context resolves VFS paths."""
    ctx = ExecutionContext(
        bars={},
        vfs={"is_night": torch.tensor([True, False])},
        affordances={},
        temporal={},
    )

    result = ctx.get("vfs.is_night")
    assert torch.equal(result, torch.tensor([True, False]))


def test_execution_context_path_not_found():
    """Context raises KeyError for invalid paths."""
    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})

    with pytest.raises(KeyError, match="not found"):
        ctx.get("invalid.path")
```

**Run, implement, commit** (TDD pattern as before)

---

### Step 2: Implement evaluator skeleton with constants

**File:** `src/townlet/world/expression/evaluator.py`

```python
"""Expression evaluator - executes AST on GPU tensors."""
import torch
from townlet.world.expression import ASTVisitor, Constant, Variable, PathAccess
from townlet.world.expression.context import ExecutionContext


class Evaluator(ASTVisitor):
    """Evaluates expressions to tensor values."""

    def __init__(self, context: ExecutionContext):
        self.context = context

    def evaluate(self, node) -> torch.Tensor:
        """Evaluate AST node to tensor."""
        return node.accept(self)

    def visit_constant(self, node: Constant) -> torch.Tensor:
        """Convert constant to tensor."""
        return torch.tensor(node.value, device=self.context.device)

    # Stubs for other methods...
```

**File:** `tests/test_townlet/unit/world/expression/test_evaluator.py`

```python
import torch
from townlet.world.expression import Constant
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.context import ExecutionContext


def test_evaluate_constant():
    """Evaluator converts constants to tensors."""
    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    node = Constant(value=3.14)
    result = evaluator.evaluate(node)

    assert isinstance(result, torch.Tensor)
    assert result.item() == 3.14
```

**Run, implement, commit**

---

### Step 3: Implement binary operators

**File:** `src/townlet/world/expression/evaluator.py` (add method)

```python
    def visit_binary_op(self, node: BinaryOp) -> torch.Tensor:
        """Execute binary operations on tensors."""
        left = node.left.accept(self)
        right = node.right.accept(self)

        if node.op == OperatorType.ADD:
            return left + right
        elif node.op == OperatorType.SUB:
            return left - right
        elif node.op == OperatorType.MUL:
            return left * right
        elif node.op == OperatorType.DIV:
            return left / right
        elif node.op == OperatorType.MOD:
            return left % right
        elif node.op == OperatorType.POW:
            return left ** right
        elif node.op == OperatorType.EQ:
            return left == right
        elif node.op == OperatorType.NEQ:
            return left != right
        elif node.op == OperatorType.LT:
            return left < right
        elif node.op == OperatorType.GT:
            return left > right
        elif node.op == OperatorType.LTE:
            return left <= right
        elif node.op == OperatorType.GTE:
            return left >= right
        elif node.op == OperatorType.AND:
            return left & right
        elif node.op == OperatorType.OR:
            return left | right
        else:
            raise ValueError(f"Unknown operator: {node.op}")
```

**Tests:** Test each operator type (add, sub, mul, div, comparison, logical)

---

### Step 4: Implement unary operators and path access

**Add methods:** `visit_unary_op`, `visit_path_access`, `visit_variable`

**Path access uses context.get():**

```python
    def visit_path_access(self, node: PathAccess) -> torch.Tensor:
        """Resolve path from execution context."""
        path_str = ".".join(node.segments)
        return self.context.get(path_str)
```

**Variable uses context.get() with simple name:**

```python
    def visit_variable(self, node: Variable) -> torch.Tensor:
        """Resolve variable from context."""
        return self.context.get(node.name)
```

---

### Step 5: Implement index access

**File:** `src/townlet/world/expression/evaluator.py` (add method)

```python
    def visit_index_access(self, node: IndexAccess) -> torch.Tensor:
        """Execute tensor indexing.

        Supports:
        - inventory[0] → tensor indexing
        - items[slot_index] → dynamic indexing
        - grid[x][y] → multi-dimensional via nesting
        """
        base = node.base.accept(self)
        index = node.index.accept(self)

        # Convert index to long tensor for indexing
        index_long = index.long()

        # Tensor indexing
        return base[index_long]
```

**Tests:**

```python
def test_evaluate_index_access():
    """Evaluator handles tensor indexing."""
    ctx = ExecutionContext(
        bars={},
        vfs={"items": torch.tensor([10, 20, 30])},
        affordances={},
        temporal={},
    )
    evaluator = Evaluator(context=ctx)

    # items[0]
    node = IndexAccess(
        base=Variable(name="items"),
        index=Constant(value=0),
    )
    result = evaluator.evaluate(node)

    assert result.item() == 10
```

---

### Step 6: Stub function calls (defer full registry)

**File:** `src/townlet/world/expression/evaluator.py`

```python
    def visit_function_call(self, node: FunctionCall) -> torch.Tensor:
        """Execute function calls.

        TODO: Full function registry in Phase 2.
        For now, support basic math functions.
        """
        # Evaluate arguments
        args = [arg.accept(self) for arg in node.arguments]

        # Built-in functions
        if node.function_name == "max":
            return torch.max(*args)
        elif node.function_name == "min":
            return torch.min(*args)
        elif node.function_name == "abs":
            return torch.abs(args[0])
        elif node.function_name == "clamp":
            return torch.clamp(args[0], min=args[1], max=args[2])
        else:
            raise NotImplementedError(
                f"Function '{node.function_name}' not yet implemented. "
                f"Full function registry in Phase 2."
            )
```

---

### Step 7: Implement IfThenElse evaluation

**File:** `src/townlet/world/expression/evaluator.py` (add method after visit_unary_op)

```python
    def visit_if_then_else(self, node: IfThenElse) -> torch.Tensor:
        """Execute vectorized conditional logic using torch.where().

        Critical: Uses torch.where() because condition is a batch tensor.
        Cannot use Python's 'if' statement on Tensor[bool, batch_size].

        Logic: result[i] = true_branch[i] if condition[i] else false_branch[i]

        Example:
            condition = tensor([True, False, True])  # 3 agents
            true_val = tensor([10, 10, 10])
            false_val = tensor([20, 20, 20])
            result = tensor([10, 20, 10])  # Element-wise selection
        """
        condition = node.condition.accept(self)
        true_val = node.true_branch.accept(self)
        false_val = node.false_branch.accept(self)

        # Ensure inputs are tensors (handle scalar constants)
        if not isinstance(condition, torch.Tensor):
            condition = torch.tensor(condition, device=self.context.device)
        if not isinstance(true_val, torch.Tensor):
            true_val = torch.tensor(true_val, device=self.context.device)
        if not isinstance(false_val, torch.Tensor):
            false_val = torch.tensor(false_val, device=self.context.device)

        # Vectorized selection (PyTorch handles broadcasting)
        return torch.where(condition, true_val, false_val)
```

**File:** `tests/test_townlet/unit/world/expression/test_evaluator.py` (append)

```python
def test_evaluate_if_then_else_vectorized():
    """Evaluator handles vectorized conditional (batch processing)."""
    from townlet.world.expression import PathAccess, IfThenElse, BinaryOp, OperatorType

    ctx = ExecutionContext(
        bars={"energy": torch.tensor([0.2, 0.8, 0.1])},  # 3 agents
        vfs={},
        affordances={},
        temporal={},
    )
    evaluator = Evaluator(context=ctx)

    # if bar.energy < 0.3 then 1.0 else 0.0
    node = IfThenElse(
        condition=BinaryOp(
            left=PathAccess(segments=["bar", "energy"]),
            op=OperatorType.LT,
            right=Constant(value=0.3)
        ),
        true_branch=Constant(value=1.0),
        false_branch=Constant(value=0.0)
    )

    result = evaluator.evaluate(node)

    # [0.2 < 0.3 (T), 0.8 < 0.3 (F), 0.1 < 0.3 (T)]
    expected = torch.tensor([1.0, 0.0, 1.0])
    assert torch.allclose(result, expected)


def test_full_integration_if_then_else():
    """Parse + evaluate if/then/else on batched data."""
    from townlet.world.expression import ExpressionParser

    parser = ExpressionParser()
    ctx = ExecutionContext(
        bars={"health": torch.tensor([0.5, 1.0])},
        vfs={},
        affordances={},
        temporal={},
    )
    evaluator = Evaluator(context=ctx)

    ast = parser.parse("if bar.health > 0.8 then 10 else 20")
    result = evaluator.evaluate(ast)

    # [0.5 > 0.8 (F) -> 20, 1.0 > 0.8 (T) -> 10]
    expected = torch.tensor([20.0, 10.0])
    assert torch.allclose(result, expected)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_evaluator.py::test_evaluate_if_then_else_vectorized -v
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_evaluator.py::test_full_integration_if_then_else -v
```

**Expected:** Both tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/evaluator.py tests/test_townlet/unit/world/expression/test_evaluator.py
git commit -m "feat(expression): implement vectorized if/then/else evaluation with torch.where"
```

---

### Step 8: Integration test - Parse → Type Check → Evaluate

**File:** `tests/test_townlet/unit/world/expression/test_integration.py`

```python
"""End-to-end integration tests."""
import torch
from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.context import ExecutionContext
from townlet.world.types import ScalarType


def test_full_pipeline():
    """Parse → Type Check → Evaluate pipeline."""
    # Parse
    parser = ExpressionParser()
    ast = parser.parse("bar.energy + 0.05")

    # Type Check
    schema = {"bar.energy": ScalarType()}
    type_checker = TypeChecker(schema=schema)
    result_type = type_checker.check(ast)
    assert result_type == ScalarType()

    # Evaluate
    ctx = ExecutionContext(
        bars={"energy": torch.tensor([0.5, 0.8])},
        vfs={},
        affordances={},
        temporal={},
    )
    evaluator = Evaluator(context=ctx)
    result = evaluator.evaluate(ast)

    expected = torch.tensor([0.55, 0.85])
    assert torch.allclose(result, expected)
```

---

### Step 9: Add to module API and finalize

**File:** `src/townlet/world/expression/__init__.py`

```python
from .evaluator import Evaluator
from .context import ExecutionContext

__all__ = [
    # ... existing ...
    "Evaluator",
    "ExecutionContext",
]
```

**Run full test suite:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/ -v
```

**Expected:** ~120 tests passing across all Phase 1 modules (includes IfThenElse tests)

**Type check and format:**
```bash
UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/world/
UV_CACHE_DIR=.uv-cache uv run ruff format src/townlet/world/ tests/test_townlet/unit/world/
```

**Final commit:**
```bash
git add -u
git commit -m "feat(expression): Phase 1 complete - AST, Parser, TypeChecker, Evaluator"
```

---

## Success Criteria

✅ **~120 tests passing** (across all Phase 1 tasks, includes IfThenElse evaluation)
✅ **Parse → Type Check → Evaluate pipeline working**
✅ **GPU tensor execution** (PyTorch operations)
✅ **Execution context** (bars, vfs access)
✅ **All operators implemented** (arithmetic, comparison, logical, unary, index)
✅ **Basic functions** (max, min, abs, clamp)
✅ **Type checking passes** (mypy clean)
✅ **Code formatted** (ruff)

---

## Next Steps

**Phase 2: VFS Profiles (Dynamic)**

Extend VFS from static variables to expression-based, dynamic variables. Use the expression language we just built!

See: `docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md` Phase 2
