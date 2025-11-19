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
