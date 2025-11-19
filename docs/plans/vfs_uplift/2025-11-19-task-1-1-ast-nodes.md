# Task 1.1: AST Node Types - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the Abstract Syntax Tree (AST) node types that represent parsed expressions in the HAMLET Expression Language.

**Architecture:** Visitor pattern with dataclass nodes. Supports both infix (`a + b`) and functional (`add(a, b)`) syntax. Includes IndexAccess for array/tensor operations (needed for inventory[0] in Phase 4).

**Tech Stack:** Python 3.11+, dataclasses, typing

**References:**
- Gemini's AST analysis: `docs/plans/vfs_uplift/sample_pyparse.md`
- Expression operators: `configs/reference_config/VARIABLE_SUBSYSTEM.md`

---

## Task Breakdown

### Step 1: Create directory structure

**Action:** Set up the expression module directory

```bash
mkdir -p src/townlet/world/expression
mkdir -p src/townlet/world/types
mkdir -p src/townlet/world/compiler
mkdir -p tests/test_townlet/unit/world/expression
```

**Verify:**
```bash
ls -la src/townlet/world/expression/
ls -la tests/test_townlet/unit/world/expression/
```

Expected: Empty directories exist

---

### Step 2: Write failing test for OperatorType enum

**File:** `tests/test_townlet/unit/world/expression/test_ast_nodes.py`

```python
"""Tests for AST node types."""
import pytest
from townlet.world.expression.ast_nodes import OperatorType


def test_operator_type_arithmetic():
    """Arithmetic operators use Python syntax."""
    assert OperatorType.ADD.value == "+"
    assert OperatorType.SUB.value == "-"
    assert OperatorType.MUL.value == "*"
    assert OperatorType.DIV.value == "/"
    assert OperatorType.MOD.value == "%"
    assert OperatorType.POW.value == "**"  # Python syntax, not ^


def test_operator_type_comparison():
    """Comparison operators."""
    assert OperatorType.EQ.value == "=="
    assert OperatorType.NEQ.value == "!="
    assert OperatorType.GT.value == ">"
    assert OperatorType.LT.value == "<"
    assert OperatorType.GTE.value == ">="
    assert OperatorType.LTE.value == "<="


def test_operator_type_logical():
    """Logical operators use Python keywords."""
    assert OperatorType.AND.value == "and"
    assert OperatorType.OR.value == "or"
    assert OperatorType.NOT.value == "not"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_operator_type_arithmetic -v
```

**Expected:** FAIL - Module 'townlet.world.expression.ast_nodes' not found

---

### Step 3: Implement OperatorType enum

**File:** `src/townlet/world/expression/ast_nodes.py`

```python
"""Abstract Syntax Tree node types for HAMLET Expression Language."""
import enum
from dataclasses import dataclass
from typing import Any, List, Union


class OperatorType(enum.Enum):
    """Supported binary and unary operators.

    Notes:
        - POW uses ** (Python syntax) not ^ (mathematical notation)
        - Logical operators use Python keywords (and/or/not)
    """
    # Arithmetic
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    POW = "**"  # Python syntax for power

    # Logical
    AND = "and"
    OR = "or"
    NOT = "not"

    # Comparison
    EQ = "=="
    NEQ = "!="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_operator_type_arithmetic -v
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_operator_type_comparison -v
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_operator_type_logical -v
```

**Expected:** All 3 tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/ast_nodes.py tests/test_townlet/unit/world/expression/test_ast_nodes.py
git commit -m "feat(expression): add OperatorType enum with Python syntax"
```

---

### Step 4: Write failing test for base ASTNode and Visitor pattern

**File:** `tests/test_townlet/unit/world/expression/test_ast_nodes.py` (append)

```python
from townlet.world.expression.ast_nodes import ASTNode, ASTVisitor


def test_ast_node_visitor_pattern():
    """ASTNode base class enforces visitor pattern."""

    class TestNode(ASTNode):
        def accept(self, visitor):
            return visitor.visit_test_node(self)

    class TestVisitor(ASTVisitor):
        def visit_test_node(self, node):
            return "visited"

    node = TestNode()
    visitor = TestVisitor()
    result = node.accept(visitor)

    assert result == "visited"


def test_ast_node_requires_accept_implementation():
    """ASTNode subclasses must implement accept()."""

    class BadNode(ASTNode):
        pass  # Forgot to implement accept()

    node = BadNode()
    visitor = ASTVisitor()

    with pytest.raises(NotImplementedError):
        node.accept(visitor)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_ast_node_visitor_pattern -v
```

**Expected:** FAIL - ASTNode, ASTVisitor not defined

---

### Step 5: Implement base ASTNode and ASTVisitor

**File:** `src/townlet/world/expression/ast_nodes.py` (append after OperatorType)

```python
@dataclass
class ASTNode:
    """Base class for all AST nodes.

    Uses Visitor pattern for separating traversal logic (type checking,
    evaluation, pretty printing) from node structure.

    Subclasses MUST implement accept(visitor).
    """
    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for traversal.

        Args:
            visitor: ASTVisitor implementation (TypeChecker, Evaluator, etc.)

        Returns:
            Result of visitor's visit_* method

        Raises:
            NotImplementedError: If subclass doesn't implement accept()
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement accept(visitor)"
        )


class ASTVisitor:
    """Interface for AST traversal (Evaluator, TypeChecker, Printer).

    Implementations must provide visit_* methods for each node type.
    """

    def visit_constant(self, node: "Constant") -> Any:
        """Visit a Constant node."""
        raise NotImplementedError()

    def visit_variable(self, node: "Variable") -> Any:
        """Visit a Variable node."""
        raise NotImplementedError()

    def visit_path_access(self, node: "PathAccess") -> Any:
        """Visit a PathAccess node."""
        raise NotImplementedError()

    def visit_binary_op(self, node: "BinaryOp") -> Any:
        """Visit a BinaryOp node."""
        raise NotImplementedError()

    def visit_unary_op(self, node: "UnaryOp") -> Any:
        """Visit a UnaryOp node."""
        raise NotImplementedError()

    def visit_function_call(self, node: "FunctionCall") -> Any:
        """Visit a FunctionCall node."""
        raise NotImplementedError()

    def visit_if_then_else(self, node: "IfThenElse") -> Any:
        """Visit an IfThenElse node."""
        raise NotImplementedError()

    def visit_index_access(self, node: "IndexAccess") -> Any:
        """Visit an IndexAccess node."""
        raise NotImplementedError()
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_ast_node_visitor_pattern -v
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_ast_node_requires_accept_implementation -v
```

**Expected:** Both tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/ast_nodes.py tests/test_townlet/unit/world/expression/test_ast_nodes.py
git commit -m "feat(expression): add ASTNode base class with Visitor pattern"
```

---

### Step 6: Write failing tests for Constant node

**File:** `tests/test_townlet/unit/world/expression/test_ast_nodes.py` (append)

```python
from townlet.world.expression.ast_nodes import Constant


def test_constant_node_float():
    """Constant node holds float literals."""
    node = Constant(value=0.05)
    assert node.value == 0.05
    assert isinstance(node.value, float)


def test_constant_node_int():
    """Constant node holds integer literals."""
    node = Constant(value=42)
    assert node.value == 42
    assert isinstance(node.value, int)


def test_constant_node_bool():
    """Constant node holds boolean literals."""
    true_node = Constant(value=True)
    false_node = Constant(value=False)

    assert true_node.value is True
    assert false_node.value is False


def test_constant_node_string():
    """Constant node holds string literals."""
    node = Constant(value="energy")
    assert node.value == "energy"
    assert isinstance(node.value, str)


def test_constant_visitor_integration():
    """Constant node works with visitor pattern."""

    class ConstantVisitor(ASTVisitor):
        def visit_constant(self, node):
            return f"const({node.value})"

    node = Constant(value=3.14)
    visitor = ConstantVisitor()
    result = node.accept(visitor)

    assert result == "const(3.14)"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_constant_node_float -v
```

**Expected:** FAIL - Constant not defined

---

### Step 7: Implement Constant node

**File:** `src/townlet/world/expression/ast_nodes.py` (append after ASTVisitor)

```python
@dataclass
class Constant(ASTNode):
    """Literal values (numbers, booleans, strings).

    Examples:
        - 0.05 (float)
        - 42 (int)
        - true (bool)
        - "energy" (string)
    """
    value: Union[float, int, bool, str]

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_constant(self)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py -k "test_constant" -v
```

**Expected:** All 5 constant tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/ast_nodes.py tests/test_townlet/unit/world/expression/test_ast_nodes.py
git commit -m "feat(expression): add Constant AST node for literals"
```

---

### Step 8: Write failing tests for Variable node

**File:** `tests/test_townlet/unit/world/expression/test_ast_nodes.py` (append)

```python
from townlet.world.expression.ast_nodes import Variable


def test_variable_node():
    """Variable node holds simple identifiers."""
    node = Variable(name="intensity")
    assert node.name == "intensity"


def test_variable_visitor_integration():
    """Variable node works with visitor pattern."""

    class VarVisitor(ASTVisitor):
        def visit_variable(self, node):
            return f"var({node.name})"

    node = Variable(name="duration")
    visitor = VarVisitor()
    result = node.accept(visitor)

    assert result == "var(duration)"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_variable_node -v
```

**Expected:** FAIL - Variable not defined

---

### Step 9: Implement Variable node

**File:** `src/townlet/world/expression/ast_nodes.py` (append after Constant)

```python
@dataclass
class Variable(ASTNode):
    """A direct variable reference (simple identifier).

    Examples:
        - intensity
        - duration
        - slot_index

    Note: For dotted paths use PathAccess instead.
    """
    name: str

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_variable(self)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py -k "test_variable" -v
```

**Expected:** Both variable tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/ast_nodes.py tests/test_townlet/unit/world/expression/test_ast_nodes.py
git commit -m "feat(expression): add Variable AST node for identifiers"
```

---

### Step 10: Write failing tests for PathAccess node

**File:** `tests/test_townlet/unit/world/expression/test_ast_nodes.py` (append)

```python
from townlet.world.expression.ast_nodes import PathAccess


def test_path_access_simple():
    """PathAccess node holds dotted paths."""
    node = PathAccess(segments=["target", "bar", "energy"])
    assert node.segments == ["target", "bar", "energy"]


def test_path_access_two_segments():
    """PathAccess works with two segments."""
    node = PathAccess(segments=["self", "position"])
    assert node.segments == ["self", "position"]


def test_path_access_visitor_integration():
    """PathAccess node works with visitor pattern."""

    class PathVisitor(ASTVisitor):
        def visit_path_access(self, node):
            return ".".join(node.segments)

    node = PathAccess(segments=["global", "vfs", "is_night"])
    visitor = PathVisitor()
    result = node.accept(visitor)

    assert result == "global.vfs.is_night"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_path_access_simple -v
```

**Expected:** FAIL - PathAccess not defined

---

### Step 11: Implement PathAccess node

**File:** `src/townlet/world/expression/ast_nodes.py` (append after Variable)

```python
@dataclass
class PathAccess(ASTNode):
    """Dot-notation access to nested state.

    Examples:
        - target.bar.energy → ["target", "bar", "energy"]
        - global.vfs.is_night → ["global", "vfs", "is_night"]
        - self.position → ["self", "position"]

    The segments list represents the path from root to leaf.
    Type checker validates path exists in the schema.
    """
    segments: List[str]

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_path_access(self)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py -k "test_path_access" -v
```

**Expected:** All 3 path_access tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/ast_nodes.py tests/test_townlet/unit/world/expression/test_ast_nodes.py
git commit -m "feat(expression): add PathAccess AST node for dotted paths"
```

---

### Step 12: Write failing tests for BinaryOp node

**File:** `tests/test_townlet/unit/world/expression/test_ast_nodes.py` (append)

```python
from townlet.world.expression.ast_nodes import BinaryOp


def test_binary_op_addition():
    """BinaryOp represents infix operations like a + b."""
    left = Constant(value=5.0)
    right = Constant(value=3.0)
    node = BinaryOp(left=left, op=OperatorType.ADD, right=right)

    assert node.left == left
    assert node.op == OperatorType.ADD
    assert node.right == right


def test_binary_op_comparison():
    """BinaryOp supports comparison operators."""
    left = Variable(name="x")
    right = Constant(value=10)
    node = BinaryOp(left=left, op=OperatorType.GT, right=right)

    assert node.op == OperatorType.GT


def test_binary_op_visitor_integration():
    """BinaryOp node works with visitor pattern."""

    class BinOpVisitor(ASTVisitor):
        def visit_binary_op(self, node):
            return f"({node.left.value} {node.op.value} {node.right.value})"

        def visit_constant(self, node):
            return node

    left = Constant(value=10)
    right = Constant(value=20)
    node = BinaryOp(left=left, op=OperatorType.MUL, right=right)
    visitor = BinOpVisitor()
    result = node.accept(visitor)

    assert result == "(10 * 20)"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_binary_op_addition -v
```

**Expected:** FAIL - BinaryOp not defined

---

### Step 13: Implement BinaryOp node

**File:** `src/townlet/world/expression/ast_nodes.py` (append after PathAccess)

```python
@dataclass
class BinaryOp(ASTNode):
    """Binary operations (infix notation).

    Examples:
        - a + b (arithmetic)
        - x > y (comparison)
        - p and q (logical)

    Both left and right operands are AST nodes (can be nested).
    """
    left: ASTNode
    op: OperatorType
    right: ASTNode

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_binary_op(self)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py -k "test_binary_op" -v
```

**Expected:** All 3 binary_op tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/ast_nodes.py tests/test_townlet/unit/world/expression/test_ast_nodes.py
git commit -m "feat(expression): add BinaryOp AST node for infix operators"
```

---

### Step 14: Write failing tests for UnaryOp node

**File:** `tests/test_townlet/unit/world/expression/test_ast_nodes.py` (append)

```python
from townlet.world.expression.ast_nodes import UnaryOp


def test_unary_op_negation():
    """UnaryOp represents prefix operations like -x."""
    operand = Variable(name="x")
    node = UnaryOp(op=OperatorType.SUB, operand=operand)

    assert node.op == OperatorType.SUB
    assert node.operand == operand


def test_unary_op_logical_not():
    """UnaryOp supports logical not."""
    operand = Variable(name="is_active")
    node = UnaryOp(op=OperatorType.NOT, operand=operand)

    assert node.op == OperatorType.NOT


def test_unary_op_visitor_integration():
    """UnaryOp node works with visitor pattern."""

    class UnaryVisitor(ASTVisitor):
        def visit_unary_op(self, node):
            return f"{node.op.value}({node.operand.name})"

        def visit_variable(self, node):
            return node

    operand = Variable(name="y")
    node = UnaryOp(op=OperatorType.SUB, operand=operand)
    visitor = UnaryVisitor()
    result = node.accept(visitor)

    assert result == "-(y)"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_unary_op_negation -v
```

**Expected:** FAIL - UnaryOp not defined

---

### Step 15: Implement UnaryOp node

**File:** `src/townlet/world/expression/ast_nodes.py` (append after BinaryOp)

```python
@dataclass
class UnaryOp(ASTNode):
    """Unary operations (prefix notation).

    Examples:
        - -x (negation)
        - not y (logical negation)

    Operand is an AST node (can be nested).
    """
    op: OperatorType
    operand: ASTNode

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_unary_op(self)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py -k "test_unary_op" -v
```

**Expected:** All 3 unary_op tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/ast_nodes.py tests/test_townlet/unit/world/expression/test_ast_nodes.py
git commit -m "feat(expression): add UnaryOp AST node for prefix operators"
```

---

### Step 16: Write failing tests for FunctionCall node

**File:** `tests/test_townlet/unit/world/expression/test_ast_nodes.py` (append)

```python
from townlet.world.expression.ast_nodes import FunctionCall


def test_function_call_no_args():
    """FunctionCall supports zero-argument functions."""
    node = FunctionCall(function_name="get_time", arguments=[])

    assert node.function_name == "get_time"
    assert node.arguments == []


def test_function_call_single_arg():
    """FunctionCall supports single argument."""
    arg = Constant(value=5)
    node = FunctionCall(function_name="abs", arguments=[arg])

    assert node.function_name == "abs"
    assert len(node.arguments) == 1
    assert node.arguments[0] == arg


def test_function_call_multiple_args():
    """FunctionCall supports multiple arguments."""
    arg1 = Variable(name="a")
    arg2 = Variable(name="b")
    arg3 = Constant(value=10)
    node = FunctionCall(function_name="clamp", arguments=[arg1, arg2, arg3])

    assert node.function_name == "clamp"
    assert len(node.arguments) == 3


def test_function_call_domain_specific():
    """FunctionCall supports HAMLET domain functions."""
    arg = Constant(value="Fridge")
    node = FunctionCall(function_name="distance_to_affordance", arguments=[arg])

    assert node.function_name == "distance_to_affordance"


def test_function_call_visitor_integration():
    """FunctionCall node works with visitor pattern."""

    class FuncVisitor(ASTVisitor):
        def visit_function_call(self, node):
            return f"{node.function_name}(...)"

    node = FunctionCall(function_name="max", arguments=[])
    visitor = FuncVisitor()
    result = node.accept(visitor)

    assert result == "max(...)"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_function_call_no_args -v
```

**Expected:** FAIL - FunctionCall not defined

---

### Step 17: Implement FunctionCall node

**File:** `src/townlet/world/expression/ast_nodes.py` (append after UnaryOp)

```python
@dataclass
class FunctionCall(ASTNode):
    """Function invocation (standard library or domain-specific).

    Examples:
        - max(a, b) - Standard math
        - distance_to_affordance("Fridge") - HAMLET domain
        - clamp(val, 0, 1) - Range limiting
        - perlin_noise(x, y, seed) - Procedural generation

    All functions resolved from single namespace (no prefixes needed).
    Function registry handles both standard and domain-specific functions.
    """
    function_name: str
    arguments: List[ASTNode]

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_function_call(self)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py -k "test_function_call" -v
```

**Expected:** All 5 function_call tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/ast_nodes.py tests/test_townlet/unit/world/expression/test_ast_nodes.py
git commit -m "feat(expression): add FunctionCall AST node for function invocation"
```

---

### Step 18: Write failing tests for IfThenElse node

**File:** `tests/test_townlet/unit/world/expression/test_ast_nodes.py` (append)

```python
from townlet.world.expression.ast_nodes import IfThenElse


def test_if_then_else_structure():
    """IfThenElse represents ternary conditional logic."""
    condition = BinaryOp(
        left=Variable(name="x"),
        op=OperatorType.GT,
        right=Constant(value=0)
    )
    true_branch = Constant(value=1)
    false_branch = Constant(value=0)

    node = IfThenElse(
        condition=condition,
        true_branch=true_branch,
        false_branch=false_branch
    )

    assert node.condition == condition
    assert node.true_branch == true_branch
    assert node.false_branch == false_branch


def test_if_then_else_visitor_integration():
    """IfThenElse node works with visitor pattern."""

    class IfElseVisitor(ASTVisitor):
        def visit_if_then_else(self, node):
            return "if ? then : else"

    node = IfThenElse(
        condition=Variable(name="cond"),
        true_branch=Constant(value="yes"),
        false_branch=Constant(value="no")
    )
    visitor = IfElseVisitor()
    result = node.accept(visitor)

    assert result == "if ? then : else"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_if_then_else_structure -v
```

**Expected:** FAIL - IfThenElse not defined

---

### Step 19: Implement IfThenElse node

**File:** `src/townlet/world/expression/ast_nodes.py` (append after FunctionCall)

```python
@dataclass
class IfThenElse(ASTNode):
    """Ternary conditional logic.

    Examples (syntax TBD by parser):
        - if condition then true_val else false_val
        - condition ? true_val : false_val
        - if_then_else(cond, t, f)  # Functional form

    All three branches are AST nodes (can be nested).
    Condition must evaluate to boolean.
    """
    condition: ASTNode
    true_branch: ASTNode
    false_branch: ASTNode

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_if_then_else(self)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py -k "test_if_then_else" -v
```

**Expected:** Both if_then_else tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/ast_nodes.py tests/test_townlet/unit/world/expression/test_ast_nodes.py
git commit -m "feat(expression): add IfThenElse AST node for conditional logic"
```

---

### Step 20: Write failing tests for IndexAccess node

**File:** `tests/test_townlet/unit/world/expression/test_ast_nodes.py` (append)

```python
from townlet.world.expression.ast_nodes import IndexAccess


def test_index_access_simple():
    """IndexAccess represents array/tensor indexing."""
    base = Variable(name="inventory")
    index = Constant(value=0)
    node = IndexAccess(base=base, index=index)

    assert node.base == base
    assert node.index == index


def test_index_access_variable_index():
    """IndexAccess supports variable indices."""
    base = Variable(name="items")
    index = Variable(name="slot_index")
    node = IndexAccess(base=base, index=index)

    assert node.index == index


def test_index_access_nested():
    """IndexAccess can be nested (multi-dimensional)."""
    # items[i][j]
    inner = IndexAccess(
        base=Variable(name="items"),
        index=Variable(name="i")
    )
    outer = IndexAccess(
        base=inner,
        index=Variable(name="j")
    )

    assert isinstance(outer.base, IndexAccess)
    assert outer.base == inner


def test_index_access_visitor_integration():
    """IndexAccess node works with visitor pattern."""

    class IndexVisitor(ASTVisitor):
        def visit_index_access(self, node):
            return f"{node.base.name}[...]"

        def visit_variable(self, node):
            return node

    base = Variable(name="bars")
    index = Constant(value=3)
    node = IndexAccess(base=base, index=index)
    visitor = IndexVisitor()
    result = node.accept(visitor)

    assert result == "bars[...]"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py::test_index_access_simple -v
```

**Expected:** FAIL - IndexAccess not defined

---

### Step 21: Implement IndexAccess node

**File:** `src/townlet/world/expression/ast_nodes.py` (append after IfThenElse)

```python
@dataclass
class IndexAccess(ASTNode):
    """Array/tensor indexing.

    Examples:
        - inventory[0] - First inventory slot
        - items[slot_index] - Dynamic index
        - bars[3] - Specific bar by index

    Critical for Phase 4 (Items) inventory operations.

    Both base and index are AST nodes:
        - base: What we're indexing (must evaluate to array/tensor)
        - index: The index (must evaluate to integer)

    Supports multi-dimensional indexing via nesting:
        - items[i][j] → IndexAccess(IndexAccess(items, i), j)
    """
    base: ASTNode
    index: ASTNode

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_index_access(self)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py -k "test_index_access" -v
```

**Expected:** All 4 index_access tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/ast_nodes.py tests/test_townlet/unit/world/expression/test_ast_nodes.py
git commit -m "feat(expression): add IndexAccess AST node for array indexing"
```

---

### Step 22: Create __init__.py for expression module

**File:** `src/townlet/world/expression/__init__.py`

```python
"""HAMLET Expression Language - AST and evaluation engine.

This module provides the foundation for declarative expressions used in:
    - VFS variables (Phase 2)
    - Effects commands (Phase 3)
    - Items interactions (Phase 4)
    - Drive As Code rewards (future integration)

Architecture:
    - AST nodes (this module) - Data structures for parsed expressions
    - Parser (parser.py) - String → AST using pyparsing
    - Type Checker (type_checker.py) - Validate types and paths
    - Evaluator (evaluator.py) - Execute AST on GPU tensors
"""
from .ast_nodes import (
    # Base classes
    ASTNode,
    ASTVisitor,
    OperatorType,

    # Leaf nodes
    Constant,
    Variable,

    # Compound nodes
    PathAccess,
    BinaryOp,
    UnaryOp,
    FunctionCall,
    IfThenElse,
    IndexAccess,
)

__all__ = [
    # Base classes
    "ASTNode",
    "ASTVisitor",
    "OperatorType",

    # Leaf nodes
    "Constant",
    "Variable",

    # Compound nodes
    "PathAccess",
    "BinaryOp",
    "UnaryOp",
    "FunctionCall",
    "IfThenElse",
    "IndexAccess",
]
```

**Verify:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "from townlet.world.expression import *; print(ASTNode, Constant, IndexAccess)"
```

**Expected:** Prints class objects, no import errors

**Commit:**
```bash
git add src/townlet/world/expression/__init__.py
git commit -m "feat(expression): add module __init__ with public API"
```

---

### Step 23: Run full test suite

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_ast_nodes.py -v
```

**Expected:** All tests PASS

**Summary:**
```
tests/test_townlet/unit/world/expression/test_ast_nodes.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓ 25 passed
```

**Count:**
- OperatorType: 3 tests
- Base classes: 2 tests
- Constant: 5 tests
- Variable: 2 tests
- PathAccess: 3 tests
- BinaryOp: 3 tests
- UnaryOp: 3 tests
- FunctionCall: 5 tests
- IfThenElse: 2 tests
- IndexAccess: 4 tests
**Total: 32 tests** (exceeds plan's 10-15 target ✅)

---

### Step 24: Type checking with mypy

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/world/expression/ast_nodes.py
```

**Expected:** Success, no type errors

**If errors:** Fix type hints and re-run

---

### Step 25: Code formatting

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run ruff format src/townlet/world/expression/
UV_CACHE_DIR=.uv-cache uv run ruff format tests/test_townlet/unit/world/expression/
```

**Expected:** Files formatted

**Commit:**
```bash
git add -u
git commit -m "style(expression): format code with ruff"
```

---

## Success Criteria

✅ **32+ tests passing** (exceeds 10-15 requirement)
✅ **8 AST node types implemented** (Constant, Variable, PathAccess, BinaryOp, UnaryOp, FunctionCall, IfThenElse, IndexAccess)
✅ **Visitor pattern working** (ASTVisitor interface + accept() methods)
✅ **OperatorType enum with Python syntax** (** not ^, and/or/not)
✅ **IndexAccess included** (ready for inventory[0] in Phase 4)
✅ **Type checking passes** (mypy clean)
✅ **Code formatted** (ruff)

---

## Next Steps

**Phase 1 - Task 1.2: Expression Parser**

Use pyparsing to build parser that converts strings → AST:
- `"a + b"` → `BinaryOp(Variable("a"), ADD, Variable("b"))`
- `"target.bar.energy"` → `PathAccess(["target", "bar", "energy"])`
- `"inventory[0]"` → `IndexAccess(Variable("inventory"), Constant(0))`

See: `docs/plans/2025-11-19-task-1-2-expression-parser.md` (to be created)
