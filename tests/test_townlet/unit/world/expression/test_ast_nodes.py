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


def test_variable_node():
    """Variable node holds simple identifiers."""
    from townlet.world.expression.ast_nodes import Variable

    node = Variable(name="intensity")
    assert node.name == "intensity"


def test_variable_visitor_integration():
    """Variable node works with visitor pattern."""
    from townlet.world.expression.ast_nodes import Variable

    class VarVisitor(ASTVisitor):
        def visit_variable(self, node):
            return f"var({node.name})"

    node = Variable(name="duration")
    visitor = VarVisitor()
    result = node.accept(visitor)

    assert result == "var(duration)"


def test_path_access_simple():
    """PathAccess node holds dotted paths."""
    from townlet.world.expression.ast_nodes import PathAccess

    node = PathAccess(segments=["target", "bar", "energy"])
    assert node.segments == ["target", "bar", "energy"]


def test_path_access_two_segments():
    """PathAccess works with two segments."""
    from townlet.world.expression.ast_nodes import PathAccess

    node = PathAccess(segments=["self", "position"])
    assert node.segments == ["self", "position"]


def test_path_access_visitor_integration():
    """PathAccess node works with visitor pattern."""
    from townlet.world.expression.ast_nodes import PathAccess

    class PathVisitor(ASTVisitor):
        def visit_path_access(self, node):
            return ".".join(node.segments)

    node = PathAccess(segments=["global", "vfs", "is_night"])
    visitor = PathVisitor()
    result = node.accept(visitor)

    assert result == "global.vfs.is_night"


def test_binary_op_addition():
    """BinaryOp represents infix operations like a + b."""
    from townlet.world.expression.ast_nodes import BinaryOp

    left = Constant(value=5.0)
    right = Constant(value=3.0)
    node = BinaryOp(left=left, op=OperatorType.ADD, right=right)

    assert node.left == left
    assert node.op == OperatorType.ADD
    assert node.right == right


def test_binary_op_comparison():
    """BinaryOp supports comparison operators."""
    from townlet.world.expression.ast_nodes import BinaryOp, Variable

    left = Variable(name="x")
    right = Constant(value=10)
    node = BinaryOp(left=left, op=OperatorType.GT, right=right)

    assert node.op == OperatorType.GT


def test_binary_op_visitor_integration():
    """BinaryOp node works with visitor pattern."""
    from townlet.world.expression.ast_nodes import BinaryOp

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
