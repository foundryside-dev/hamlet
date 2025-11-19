"""Tests for AST node types."""

import pytest

from townlet.world.expression.ast_nodes import ASTNode, ASTVisitor, OperatorType


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
