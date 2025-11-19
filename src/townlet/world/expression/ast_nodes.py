"""Abstract Syntax Tree node types for HAMLET Expression Language."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass  # Forward references handled by quotes


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
        raise NotImplementedError(f"{self.__class__.__name__} must implement accept(visitor)")


class ASTVisitor:
    """Interface for AST traversal (Evaluator, TypeChecker, Printer).

    Implementations must provide visit_* methods for each node type.
    """

    def visit_constant(self, node: Any) -> Any:  # noqa: ARG002
        """Visit a Constant node."""
        raise NotImplementedError()

    def visit_variable(self, node: Any) -> Any:  # noqa: ARG002
        """Visit a Variable node."""
        raise NotImplementedError()

    def visit_path_access(self, node: Any) -> Any:  # noqa: ARG002
        """Visit a PathAccess node."""
        raise NotImplementedError()

    def visit_binary_op(self, node: Any) -> Any:  # noqa: ARG002
        """Visit a BinaryOp node."""
        raise NotImplementedError()

    def visit_unary_op(self, node: Any) -> Any:  # noqa: ARG002
        """Visit a UnaryOp node."""
        raise NotImplementedError()

    def visit_function_call(self, node: Any) -> Any:  # noqa: ARG002
        """Visit a FunctionCall node."""
        raise NotImplementedError()

    def visit_if_then_else(self, node: Any) -> Any:  # noqa: ARG002
        """Visit an IfThenElse node."""
        raise NotImplementedError()

    def visit_index_access(self, node: Any) -> Any:  # noqa: ARG002
        """Visit an IndexAccess node."""
        raise NotImplementedError()


@dataclass
class Constant(ASTNode):
    """Literal values (numbers, booleans, strings).

    Examples:
        - 0.05 (float)
        - 42 (int)
        - true (bool)
        - "energy" (string)
    """

    value: float | int | bool | str

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_constant(self)


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

    segments: list[str]

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_path_access(self)


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


@dataclass
class UnaryOp(ASTNode):
    """Unary operations (prefix notation).

    Examples:
        - -x (arithmetic negation)
        - not p (logical negation)

    The operand is an AST node (can be nested).
    """

    op: OperatorType
    operand: ASTNode

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_unary_op(self)


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
    arguments: list[ASTNode]

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_function_call(self)


@dataclass
class IfThenElse(ASTNode):
    """Conditional expression (ternary operator).

    Examples:
        - if energy < 0.2 then 1 else 0 (crisis bonus)
        - if is_night then 0.5 else 1.0 (time multiplier)
        - if has_job then income else 0 (conditional reward)

    Evaluates condition, returns true_branch if true, false_branch if false.
    All branches are AST nodes (can be arbitrarily complex).
    """

    condition: ASTNode
    true_branch: ASTNode
    false_branch: ASTNode

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_if_then_else(self)


@dataclass
class IndexAccess(ASTNode):
    """Array/list element access by index.

    Examples:
        - items[0] (constant index)
        - values[i] (variable index)
        - prices[slot_idx + 1] (computed index)
        - matrix[row][col] (nested access - chained IndexAccess nodes)

    Both target and index are AST nodes (can be nested expressions).
    Target must evaluate to array/list, index to integer.
    """

    target: ASTNode
    index: ASTNode

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_index_access(self)
