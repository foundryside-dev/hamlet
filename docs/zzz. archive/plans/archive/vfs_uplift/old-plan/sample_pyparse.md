Here is the impact analysis:

1. **AST Node Requirements (Phase 1):** The `VARIABLE_SUBSYSTEM.md` provides the **definitive standard library** of operators.

      - **Impact:** My AST design for `FunctionCall` must support standard math (`add`, `sub`) *and* domain-specifics (`distance_to_affordance`, `moving_average`, `perlin_noise`).
      - **Syntax Note:** The config examples use functional notation (e.g., `add(a, b)`). A robust expression language usually supports **Infix** (`a + b`) for readability *and* **Functional** (`add(a, b)`) for structure. I will design the AST/Parser to handle **both**.

2. **Item Scope Architecture (Phase 2/4):** The `VFS Integration Analysis` explicitly validates the architectural approach for adding "Item" scope.

      - **Impact:** It confirms that `VFS Profiles` (Plan Phase 2) and `Items` (Plan Phase 4) are the correct places to implement the schema and registry extensions. The analysis gives us the exact implementation blueprint (`_compute_shape` overrides).

3. **No "BAC" Distraction:** The mention of "BAC" (Behavioral Action Compiler) confirms that VFS is a foundational dependency for future systems. We stay the course on World Compiler (T0) to enable BAC later.

-----

### Execution: Phase 1 - Expression Language

**Task 1.1: AST Node Types**

I will now implement the Abstract Syntax Tree (AST) nodes. This defines the data structures that the parser will produce and the evaluator will consume.

**Design Choices:**

- **`@dataclass`**: Used for immutability and clean structure.
- **`Visitor` Pattern**: Prepared for separate `TypeChecker` and `Evaluator` implementations.
- **Operator Flexibility**: Support for both Infix (`+`) and Functional (`add()`) representations.

**File:** `src/townlet/world/expression/ast_nodes.py`

```python
import enum
from dataclasses import dataclass
from typing import Any, List, Optional, Union

class OperatorType(enum.Enum):
    """Supported binary and unary operators."""
    # Arithmetic
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    POW = "^"

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

@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    def accept(self, visitor: Any) -> Any:
        raise NotImplementedError()

@dataclass
class Constant(ASTNode):
    """Literal values (numbers, booleans, strings).

    Example: 0.05, true, "energy"
    """
    value: Union[float, int, bool, str]

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_constant(self)

@dataclass
class Variable(ASTNode):
    """A direct variable reference (simple identifier).

    Example: intensity, duration
    """
    name: str

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_variable(self)

@dataclass
class PathAccess(ASTNode):
    """Dot-notation access to nested state.

    Example: target.bar.energy, global.vfs.is_night
    """
    segments: List[str]

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_path_access(self)

@dataclass
class BinaryOp(ASTNode):
    """Binary operations (infix notation).

    Example: a + b, x > y
    """
    left: ASTNode
    op: OperatorType
    right: ASTNode

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_binary_op(self)

@dataclass
class UnaryOp(ASTNode):
    """Unary operations.

    Example: -x, not y
    """
    op: OperatorType
    operand: ASTNode

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_unary_op(self)

@dataclass
class FunctionCall(ASTNode):
    """Function invocation (standard library or custom).

    Example:
        - max(a, b)
        - distance_to_affordance("Fridge")
        - clamp(val, 0, 1)
    """
    function_name: str
    arguments: List[ASTNode]

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_function_call(self)

@dataclass
class IfThenElse(ASTNode):
    """Ternary conditional logic.

    Example: if condition then true_val else false_val
    Mapped from function: if_then_else(cond, t, f)
    """
    condition: ASTNode
    true_branch: ASTNode
    false_branch: ASTNode

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_if_then_else(self)

class ASTVisitor:
    """Interface for AST traversal (Evaluator, TypeChecker, Printer)."""

    def visit_constant(self, node: Constant) -> Any: ...
    def visit_variable(self, node: Variable) -> Any: ...
    def visit_path_access(self, node: PathAccess) -> Any: ...
    def visit_binary_op(self, node: BinaryOp) -> Any: ...
    def visit_unary_op(self, node: UnaryOp) -> Any: ...
    def visit_function_call(self, node: FunctionCall) -> Any: ...
    def visit_if_then_else(self, node: IfThenElse) -> Any: ...
```

**File:** `src/townlet/world/expression/__init__.py`

```python
from .ast_nodes import (
    ASTNode, Constant, Variable, PathAccess,
    BinaryOp, UnaryOp, FunctionCall, IfThenElse,
    OperatorType, ASTVisitor
)

__all__ = [
    "ASTNode", "Constant", "Variable", "PathAccess",
    "BinaryOp", "UnaryOp", "FunctionCall", "IfThenElse",
    "OperatorType", "ASTVisitor"
]
```

**Immediate Next Step:**
I have defined the AST nodes. The next critical step in Phase 1 is the **Parser**.
