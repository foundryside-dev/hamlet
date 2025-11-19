"""Tests for AST node types."""

import pytest

from townlet.world.expression.ast_nodes import ASTNode, ASTVisitor, Constant, OperatorType


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
