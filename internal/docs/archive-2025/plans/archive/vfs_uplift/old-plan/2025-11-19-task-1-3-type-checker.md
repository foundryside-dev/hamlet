# Task 1.3: Type Checker - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a type checking visitor that validates expressions at compile-time, catching type errors before runtime.

**Architecture:** AST Visitor pattern. Infers types bottom-up, validates operator/function compatibility, resolves paths against schema.

**Tech Stack:** Python 3.11+, dataclasses for type system

**Dependencies:** Task 1.1 (AST Nodes), Task 1.2 (Parser) must be complete

**References:**
- Type system spec: Decision D2 in unified plan (scalar, bool, vec2i, vec3i, vecNi, vecNf)
- Path validation: VFS schema from `src/townlet/vfs/schema.py`

---

## Task Breakdown

### Step 1: Write failing tests for primitive type definitions

**File:** `tests/test_townlet/unit/world/types/test_primitive.py`

```python
"""Tests for primitive type system."""
import pytest
from townlet.world.types.primitive import (
    ScalarType,
    BoolType,
    Vec2iType,
    Vec3iType,
    VecNiType,
    VecNfType,
)


def test_scalar_type():
    """ScalarType represents float scalars."""
    t = ScalarType()
    assert str(t) == "scalar"
    assert t == ScalarType()  # Equality


def test_bool_type():
    """BoolType represents booleans."""
    t = BoolType()
    assert str(t) == "bool"
    assert t == BoolType()


def test_vec2i_type():
    """Vec2iType represents 2D integer vectors."""
    t = Vec2iType()
    assert str(t) == "vec2i"
    assert t == Vec2iType()


def test_vec3i_type():
    """Vec3iType represents 3D integer vectors."""
    t = Vec3iType()
    assert str(t) == "vec3i"


def test_vecni_type_with_dims():
    """VecNiType represents N-dimensional integer vectors."""
    t = VecNiType(dims=7)
    assert str(t) == "vec7i"
    assert t.dims == 7


def test_vecnf_type_with_dims():
    """VecNfType represents N-dimensional float vectors."""
    t = VecNfType(dims=10)
    assert str(t) == "vec10f"
    assert t.dims == 10


def test_vecni_equality():
    """VecNi types equal only if same dimensionality."""
    t1 = VecNiType(dims=5)
    t2 = VecNiType(dims=5)
    t3 = VecNiType(dims=7)

    assert t1 == t2
    assert t1 != t3


def test_type_compatibility_scalar_and_bool():
    """Scalars and bools are not compatible."""
    assert ScalarType() != BoolType()
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/types/test_primitive.py::test_scalar_type -v
```

**Expected:** FAIL - Module not found

---

### Step 2: Implement primitive type system

**File:** `src/townlet/world/types/primitive.py`

```python
"""Primitive types for HAMLET Expression Language."""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PrimitiveType:
    """Base class for primitive types.

    All primitive types are immutable (frozen dataclass).
    """

    def __str__(self) -> str:
        raise NotImplementedError()


@dataclass(frozen=True)
class ScalarType(PrimitiveType):
    """Floating-point scalar (single value).

    Examples: 0.05, 3.14, bar.energy
    """

    def __str__(self) -> str:
        return "scalar"


@dataclass(frozen=True)
class BoolType(PrimitiveType):
    """Boolean type.

    Examples: true, false, a > b
    """

    def __str__(self) -> str:
        return "bool"


@dataclass(frozen=True)
class Vec2iType(PrimitiveType):
    """2D integer vector.

    Examples: agent position in Grid2D
    """

    def __str__(self) -> str:
        return "vec2i"


@dataclass(frozen=True)
class Vec3iType(PrimitiveType):
    """3D integer vector.

    Examples: agent position in Grid3D
    """

    def __str__(self) -> str:
        return "vec3i"


@dataclass(frozen=True)
class VecNiType(PrimitiveType):
    """N-dimensional integer vector.

    Examples: agent position in GridND (4D-100D)
    """

    dims: int

    def __str__(self) -> str:
        return f"vec{self.dims}i"


@dataclass(frozen=True)
class VecNfType(PrimitiveType):
    """N-dimensional float vector.

    Examples: continuous state vectors
    """

    dims: int

    def __str__(self) -> str:
        return f"vec{self.dims}f"
```

**File:** `src/townlet/world/types/__init__.py`

```python
"""Type system for HAMLET Expression Language."""
from .primitive import (
    PrimitiveType,
    ScalarType,
    BoolType,
    Vec2iType,
    Vec3iType,
    VecNiType,
    VecNfType,
)

__all__ = [
    "PrimitiveType",
    "ScalarType",
    "BoolType",
    "Vec2iType",
    "Vec3iType",
    "VecNiType",
    "VecNfType",
]
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/types/test_primitive.py -v
```

**Expected:** All 8 tests PASS

**Commit:**
```bash
git add src/townlet/world/types/primitive.py src/townlet/world/types/__init__.py tests/test_townlet/unit/world/types/test_primitive.py
git commit -m "feat(types): add primitive type system (scalar, bool, vec types)"
```

---

### Step 3: Write failing tests for type checker with constants

**File:** `tests/test_townlet/unit/world/expression/test_type_checker.py`

```python
"""Tests for expression type checker."""
import pytest
from townlet.world.expression import Constant, Variable, BinaryOp, OperatorType
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError
from townlet.world.types import ScalarType, BoolType


def test_type_check_float_constant():
    """Type checker infers float constants as scalar."""
    checker = TypeChecker(schema={})
    node = Constant(value=3.14)
    result_type = checker.check(node)

    assert result_type == ScalarType()


def test_type_check_int_constant():
    """Type checker infers int constants as scalar."""
    checker = TypeChecker(schema={})
    node = Constant(value=42)
    result_type = checker.check(node)

    assert result_type == ScalarType()


def test_type_check_bool_constant():
    """Type checker infers bool constants as bool."""
    checker = TypeChecker(schema={})
    node = Constant(value=True)
    result_type = checker.check(node)

    assert result_type == BoolType()


def test_type_check_string_constant():
    """String constants have special handling (context-dependent)."""
    checker = TypeChecker(schema={})
    node = Constant(value="energy")

    # For now, strings might be "untyped" or have a StringType
    # We'll define this behavior later
    result_type = checker.check(node)
    assert result_type is not None
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py::test_type_check_float_constant -v
```

**Expected:** FAIL - TypeChecker not defined

---

### Step 4: Implement type checker skeleton with constant inference

**File:** `src/townlet/world/expression/type_checker.py`

```python
"""Type checker for HAMLET Expression Language."""
from typing import Any, Dict
from townlet.world.expression import (
    ASTNode,
    ASTVisitor,
    Constant,
    Variable,
    PathAccess,
    BinaryOp,
    UnaryOp,
    FunctionCall,
    IfThenElse,
    IndexAccess,
)
from townlet.world.types import (
    PrimitiveType,
    ScalarType,
    BoolType,
)


class TypeCheckError(Exception):
    """Raised when type checking fails."""

    pass


class TypeChecker(ASTVisitor):
    """Type checker visitor for expression ASTs.

    Validates type correctness and infers result types.

    Args:
        schema: Type schema mapping variable paths to types
                Example: {"bar.energy": ScalarType(), "agent.position": Vec2iType()}
    """

    def __init__(self, schema: Dict[str, PrimitiveType]):
        self.schema = schema

    def check(self, node: ASTNode) -> PrimitiveType:
        """Type check an AST node.

        Args:
            node: AST node to check

        Returns:
            Inferred type of the expression

        Raises:
            TypeCheckError: If type checking fails
        """
        return node.accept(self)

    def visit_constant(self, node: Constant) -> PrimitiveType:
        """Infer type of constant literals."""
        if isinstance(node.value, bool):
            return BoolType()
        elif isinstance(node.value, (int, float)):
            return ScalarType()
        elif isinstance(node.value, str):
            # Strings are context-dependent (e.g., affordance names)
            # For now, treat as untyped (will validate in context)
            # Return a placeholder "string" type
            return ScalarType()  # TEMPORARY - will refine later
        else:
            raise TypeCheckError(f"Unknown constant type: {type(node.value)}")

    def visit_variable(self, node: Variable) -> PrimitiveType:
        """Look up variable type in schema."""
        raise NotImplementedError("Variable type checking not yet implemented")

    def visit_path_access(self, node: PathAccess) -> PrimitiveType:
        """Resolve path against schema."""
        raise NotImplementedError("Path access type checking not yet implemented")

    def visit_binary_op(self, node: BinaryOp) -> PrimitiveType:
        """Check binary operator type compatibility."""
        raise NotImplementedError("Binary op type checking not yet implemented")

    def visit_unary_op(self, node: UnaryOp) -> PrimitiveType:
        """Check unary operator type."""
        raise NotImplementedError("Unary op type checking not yet implemented")

    def visit_function_call(self, node: FunctionCall) -> PrimitiveType:
        """Check function call signature."""
        raise NotImplementedError("Function call type checking not yet implemented")

    def visit_if_then_else(self, node: IfThenElse) -> PrimitiveType:
        """Check conditional expression."""
        raise NotImplementedError("If/then/else type checking not yet implemented")

    def visit_index_access(self, node: IndexAccess) -> PrimitiveType:
        """Check array indexing."""
        raise NotImplementedError("Index access type checking not yet implemented")
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py -k "constant" -v
```

**Expected:** All 4 constant tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/type_checker.py tests/test_townlet/unit/world/expression/test_type_checker.py
git commit -m "feat(expression): add type checker skeleton with constant inference"
```

---

### Step 5: Write failing tests for binary operator type checking

**File:** `tests/test_townlet/unit/world/expression/test_type_checker.py` (append)

```python
def test_type_check_arithmetic_operators():
    """Arithmetic operators require scalar operands."""
    checker = TypeChecker(schema={})

    # a + b where a, b are constants
    node = BinaryOp(
        left=Constant(value=5.0),
        op=OperatorType.ADD,
        right=Constant(value=3.0),
    )
    result_type = checker.check(node)

    assert result_type == ScalarType()


def test_type_check_comparison_operators():
    """Comparison operators return bool."""
    checker = TypeChecker(schema={})

    node = BinaryOp(
        left=Constant(value=10),
        op=OperatorType.GT,
        right=Constant(value=5),
    )
    result_type = checker.check(node)

    assert result_type == BoolType()


def test_type_check_logical_operators():
    """Logical operators require bool operands."""
    checker = TypeChecker(schema={})

    node = BinaryOp(
        left=Constant(value=True),
        op=OperatorType.AND,
        right=Constant(value=False),
    )
    result_type = checker.check(node)

    assert result_type == BoolType()


def test_type_check_incompatible_operands():
    """Type error when operands incompatible."""
    checker = TypeChecker(schema={})

    # true + 5 (bool + scalar)
    node = BinaryOp(
        left=Constant(value=True),
        op=OperatorType.ADD,
        right=Constant(value=5),
    )

    with pytest.raises(TypeCheckError, match="incompatible"):
        checker.check(node)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py::test_type_check_arithmetic_operators -v
```

**Expected:** FAIL - Binary op not implemented

---

### Step 6: Implement binary operator type checking

**File:** `src/townlet/world/expression/type_checker.py` (modify `visit_binary_op`)

Replace the `visit_binary_op` method:

```python
    def visit_binary_op(self, node: BinaryOp) -> PrimitiveType:
        """Check binary operator type compatibility.

        Rules:
        - Arithmetic (+, -, *, /, %, **): scalar × scalar → scalar
        - Comparison (==, !=, <, >, <=, >=): scalar × scalar → bool
        - Logical (and, or): bool × bool → bool
        """
        left_type = node.left.accept(self)
        right_type = node.right.accept(self)

        # Arithmetic operators
        if node.op in {
            OperatorType.ADD,
            OperatorType.SUB,
            OperatorType.MUL,
            OperatorType.DIV,
            OperatorType.MOD,
            OperatorType.POW,
        }:
            if left_type != ScalarType() or right_type != ScalarType():
                raise TypeCheckError(
                    f"Arithmetic operator {node.op.value} requires scalar operands, "
                    f"got {left_type} and {right_type}"
                )
            return ScalarType()

        # Comparison operators
        elif node.op in {
            OperatorType.EQ,
            OperatorType.NEQ,
            OperatorType.LT,
            OperatorType.GT,
            OperatorType.LTE,
            OperatorType.GTE,
        }:
            if left_type != ScalarType() or right_type != ScalarType():
                raise TypeCheckError(
                    f"Comparison operator {node.op.value} requires scalar operands, "
                    f"got {left_type} and {right_type}"
                )
            return BoolType()

        # Logical operators
        elif node.op in {OperatorType.AND, OperatorType.OR}:
            if left_type != BoolType() or right_type != BoolType():
                raise TypeCheckError(
                    f"Logical operator {node.op.value} requires bool operands, "
                    f"got {left_type} and {right_type}"
                )
            return BoolType()

        else:
            raise TypeCheckError(f"Unknown binary operator: {node.op}")
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py -k "binary or operator or operand" -v
```

**Expected:** All 4 binary operator tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/type_checker.py tests/test_townlet/unit/world/expression/test_type_checker.py
git commit -m "feat(expression): add binary operator type checking"
```

---

### Step 7: Write failing tests for unary operator type checking

**File:** `tests/test_townlet/unit/world/expression/test_type_checker.py` (append)

```python
from townlet.world.expression import UnaryOp


def test_type_check_negation():
    """Unary negation requires scalar operand."""
    checker = TypeChecker(schema={})

    node = UnaryOp(op=OperatorType.SUB, operand=Constant(value=10))
    result_type = checker.check(node)

    assert result_type == ScalarType()


def test_type_check_logical_not():
    """Logical not requires bool operand."""
    checker = TypeChecker(schema={})

    node = UnaryOp(op=OperatorType.NOT, operand=Constant(value=True))
    result_type = checker.check(node)

    assert result_type == BoolType()


def test_type_check_negation_wrong_type():
    """Type error when negating bool."""
    checker = TypeChecker(schema={})

    node = UnaryOp(op=OperatorType.SUB, operand=Constant(value=True))

    with pytest.raises(TypeCheckError, match="requires scalar"):
        checker.check(node)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py::test_type_check_negation -v
```

**Expected:** FAIL - Unary op not implemented

---

### Step 8: Implement unary operator type checking

**File:** `src/townlet/world/expression/type_checker.py` (modify `visit_unary_op`)

Replace the method:

```python
    def visit_unary_op(self, node: UnaryOp) -> PrimitiveType:
        """Check unary operator type.

        Rules:
        - Negation (-): scalar → scalar
        - Logical not (not): bool → bool
        """
        operand_type = node.operand.accept(self)

        if node.op == OperatorType.SUB:  # Negation
            if operand_type != ScalarType():
                raise TypeCheckError(
                    f"Unary negation requires scalar operand, got {operand_type}"
                )
            return ScalarType()

        elif node.op == OperatorType.NOT:
            if operand_type != BoolType():
                raise TypeCheckError(
                    f"Logical not requires bool operand, got {operand_type}"
                )
            return BoolType()

        else:
            raise TypeCheckError(f"Unknown unary operator: {node.op}")
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py -k "unary or negation or not" -v
```

**Expected:** All 3 unary tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/type_checker.py tests/test_townlet/unit/world/expression/test_type_checker.py
git commit -m "feat(expression): add unary operator type checking"
```

---

### Step 9: Write failing tests for path access validation

**File:** `tests/test_townlet/unit/world/expression/test_type_checker.py` (append)

```python
def test_type_check_path_access_valid():
    """Type checker resolves valid paths from schema."""
    schema = {
        "bar.energy": ScalarType(),
        "bar.health": ScalarType(),
    }
    checker = TypeChecker(schema=schema)

    node = PathAccess(segments=["bar", "energy"])
    result_type = checker.check(node)

    assert result_type == ScalarType()


def test_type_check_path_access_invalid():
    """Type error for unknown path."""
    schema = {
        "bar.energy": ScalarType(),
    }
    checker = TypeChecker(schema=schema)

    node = PathAccess(segments=["bar", "invalid"])

    with pytest.raises(TypeCheckError, match="not found in schema"):
        checker.check(node)


def test_type_check_nested_path():
    """Type checker handles deeply nested paths."""
    schema = {
        "global.vfs.is_night": BoolType(),
    }
    checker = TypeChecker(schema=schema)

    node = PathAccess(segments=["global", "vfs", "is_night"])
    result_type = checker.check(node)

    assert result_type == BoolType()
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py::test_type_check_path_access_valid -v
```

**Expected:** FAIL - Path access not implemented

---

### Step 10: Implement path access type resolution

**File:** `src/townlet/world/expression/type_checker.py` (modify `visit_path_access`)

Replace the method:

```python
    def visit_path_access(self, node: PathAccess) -> PrimitiveType:
        """Resolve path against schema.

        Joins path segments with '.' and looks up in schema.
        """
        path_str = ".".join(node.segments)

        if path_str not in self.schema:
            raise TypeCheckError(
                f"Path '{path_str}' not found in schema. "
                f"Available paths: {list(self.schema.keys())}"
            )

        return self.schema[path_str]
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py -k "path_access" -v
```

**Expected:** All 3 path tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/type_checker.py tests/test_townlet/unit/world/expression/test_type_checker.py
git commit -m "feat(expression): add path access type resolution"
```

---

### Step 11: Write failing tests for variable type checking

**File:** `tests/test_townlet/unit/world/expression/test_type_checker.py` (append)

```python
def test_type_check_variable_in_schema():
    """Variables resolve from schema (simple names)."""
    schema = {
        "intensity": ScalarType(),
        "duration": ScalarType(),
    }
    checker = TypeChecker(schema=schema)

    node = Variable(name="intensity")
    result_type = checker.check(node)

    assert result_type == ScalarType()


def test_type_check_variable_not_in_schema():
    """Type error for unknown variable."""
    schema = {}
    checker = TypeChecker(schema=schema)

    node = Variable(name="unknown")

    with pytest.raises(TypeCheckError, match="not found"):
        checker.check(node)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py::test_type_check_variable_in_schema -v
```

**Expected:** FAIL - Variable not implemented

---

### Step 12: Implement variable type checking

**File:** `src/townlet/world/expression/type_checker.py` (modify `visit_variable`)

Replace the method:

```python
    def visit_variable(self, node: Variable) -> PrimitiveType:
        """Look up variable type in schema.

        Simple variables (single identifier) look up directly in schema.
        """
        if node.name not in self.schema:
            raise TypeCheckError(
                f"Variable '{node.name}' not found in schema. "
                f"Available variables: {list(self.schema.keys())}"
            )

        return self.schema[node.name]
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py -k "variable" -v
```

**Expected:** Both variable tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/type_checker.py tests/test_townlet/unit/world/expression/test_type_checker.py
git commit -m "feat(expression): add variable type checking"
```

---

### Step 13: Integration test - Parse then type check

**File:** `tests/test_townlet/unit/world/expression/test_type_checker.py` (append)

```python
from townlet.world.expression import ExpressionParser


def test_integration_parse_and_typecheck():
    """Integration: parse expression string, then type check."""
    schema = {
        "bar.energy": ScalarType(),
        "bar.health": ScalarType(),
    }

    parser = ExpressionParser()
    checker = TypeChecker(schema=schema)

    # Parse "bar.energy + 0.05"
    ast = parser.parse("bar.energy + 0.05")

    # Type check
    result_type = checker.check(ast)

    assert result_type == ScalarType()


def test_integration_type_error_from_parsed_expr():
    """Integration: type error from parsed expression."""
    schema = {"x": ScalarType()}

    parser = ExpressionParser()
    checker = TypeChecker(schema=schema)

    # Parse "x and true" (type error: scalar and bool)
    ast = parser.parse("x and true")

    with pytest.raises(TypeCheckError, match="requires bool"):
        checker.check(ast)


def test_type_check_if_then_else():
    """Type checker validates if/then/else conditionals."""
    schema = {}
    checker = TypeChecker(schema=schema)

    # if true then 1 else 2
    node = IfThenElse(
        condition=Constant(value=True),
        true_branch=Constant(value=1),
        false_branch=Constant(value=2),
    )
    result_type = checker.check(node)

    assert result_type == ScalarType()


def test_type_check_if_non_bool_condition():
    """Type error when condition is not bool."""
    schema = {}
    checker = TypeChecker(schema=schema)

    # if 5 then 1 else 2  (condition is scalar, not bool)
    node = IfThenElse(
        condition=Constant(value=5),
        true_branch=Constant(value=1),
        false_branch=Constant(value=2),
    )

    with pytest.raises(TypeCheckError, match="must be bool"):
        checker.check(node)


def test_type_check_if_mismatched_branches():
    """Type error when branches have different types."""
    schema = {}
    checker = TypeChecker(schema=schema)

    # if true then 1 else true  (scalar vs bool)
    node = IfThenElse(
        condition=Constant(value=True),
        true_branch=Constant(value=1),
        false_branch=Constant(value=True),
    )

    with pytest.raises(TypeCheckError, match="must have same type"):
        checker.check(node)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py::test_integration_parse_and_typecheck -v
```

**Expected:** Both integration tests PASS (no new code needed)

**Commit:**
```bash
git add tests/test_townlet/unit/world/expression/test_type_checker.py
git commit -m "test(expression): add integration tests for parse + type check"
```

---

### Step 14: Stub remaining visitor methods (deferred to Phase 2/3/4)

**File:** `src/townlet/world/expression/type_checker.py` (modify stubs)

Update the NotImplementedError stubs with clearer messages:

```python
    def visit_function_call(self, node: FunctionCall) -> PrimitiveType:
        """Check function call signature.

        TODO: Implement in Phase 2 (need function registry).
        """
        raise NotImplementedError(
            "Function call type checking deferred to Phase 2 "
            "(requires function registry with signatures)"
        )

    def visit_if_then_else(self, node: IfThenElse) -> PrimitiveType:
        """Check conditional expression.

        Rules:
        - Condition must be bool
        - True and false branches must have same type
        - Result type is branch type
        """
        # Check condition is bool
        cond_type = node.condition.accept(self)
        if cond_type != BoolType():
            raise TypeCheckError(
                f"If condition must be bool, got {cond_type}"
            )

        # Check both branches
        true_type = node.true_branch.accept(self)
        false_type = node.false_branch.accept(self)

        # Branches must match
        if true_type != false_type:
            raise TypeCheckError(
                f"If branches must have same type. "
                f"Got {true_type} (true) and {false_type} (false)"
            )

        # Result type is branch type
        return true_type

    def visit_index_access(self, node: IndexAccess) -> PrimitiveType:
        """Check array indexing.

        TODO: Implement in Phase 4 (need tensor types).
        """
        raise NotImplementedError(
            "Index access type checking deferred to Phase 4 "
            "(requires tensor/array types)"
        )
```

**Commit:**
```bash
git add src/townlet/world/expression/type_checker.py
git commit -m "feat(expression): implement if/then/else type checking"
```

---

### Step 15: Add type checker to module API

**File:** `src/townlet/world/expression/__init__.py` (modify)

```python
from .type_checker import TypeChecker, TypeCheckError

__all__ = [
    # ... existing ...
    "TypeChecker",
    "TypeCheckError",
]
```

**Verify:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "from townlet.world.expression import TypeChecker, TypeCheckError; print('OK')"
```

**Expected:** Prints "OK"

**Commit:**
```bash
git add src/townlet/world/expression/__init__.py
git commit -m "feat(expression): export TypeChecker in module API"
```

---

### Step 16: Run full test suite

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py -v
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/types/test_primitive.py -v
```

**Expected:** All tests PASS

**Count:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_type_checker.py tests/test_townlet/unit/world/types/test_primitive.py --co -q
```

**Expected:** ~28-33 tests total (includes 3 IfThenElse type checking tests)

---

### Step 17: Type checking and formatting

**Run mypy:**
```bash
UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/world/expression/type_checker.py
UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/world/types/primitive.py
```

**Expected:** Success

**Run ruff:**
```bash
UV_CACHE_DIR=.uv-cache uv run ruff format src/townlet/world/
UV_CACHE_DIR=.uv-cache uv run ruff format tests/test_townlet/unit/world/
```

**Commit:**
```bash
git add -u
git commit -m "style(expression): format type checker code"
```

---

## Success Criteria

✅ **28-33 tests passing** (includes IfThenElse type checking)
✅ **Type system defined** (scalar, bool, vec types)
✅ **Type inference working** (constants, variables, operators)
✅ **Path resolution** (validates against schema)
✅ **Operator type checking** (catches incompatible types)
✅ **Type checking passes** (mypy clean)
✅ **Code formatted** (ruff)

---

## Next Steps

**Phase 1 - Task 1.4: Expression Evaluator**

Implement evaluation visitor that:
- Executes AST on GPU tensors (PyTorch)
- Handles all operators and functions
- Supports execution context (bars, vfs, affordances)
- Includes IndexAccess evaluation

See: `docs/plans/2025-11-19-task-1-4-expression-evaluator.md` (to be created)
