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


def test_unary_op_negation():
    """UnaryOp represents prefix operations like -x."""
    from townlet.world.expression.ast_nodes import UnaryOp, Variable

    operand = Variable(name="x")
    node = UnaryOp(op=OperatorType.SUB, operand=operand)

    assert node.op == OperatorType.SUB
    assert node.operand == operand


def test_unary_op_logical_not():
    """UnaryOp supports logical NOT operator."""
    from townlet.world.expression.ast_nodes import UnaryOp, Variable

    operand = Variable(name="p")
    node = UnaryOp(op=OperatorType.NOT, operand=operand)

    assert node.op == OperatorType.NOT
    assert node.operand == operand


def test_unary_op_visitor_integration():
    """UnaryOp node works with visitor pattern."""
    from townlet.world.expression.ast_nodes import UnaryOp

    class UnaryVisitor(ASTVisitor):
        def visit_unary_op(self, node):
            return f"({node.op.value} {node.operand.value})"

        def visit_constant(self, node):
            return node

    operand = Constant(value=42)
    node = UnaryOp(op=OperatorType.SUB, operand=operand)
    visitor = UnaryVisitor()
    result = node.accept(visitor)

    assert result == "(- 42)"


def test_function_call_no_args():
    """FunctionCall supports zero-argument functions."""
    from townlet.world.expression.ast_nodes import FunctionCall

    node = FunctionCall(function_name="now", arguments=[])
    assert node.function_name == "now"
    assert node.arguments == []


def test_function_call_single_arg():
    """FunctionCall supports single-argument functions."""
    from townlet.world.expression.ast_nodes import FunctionCall, Variable

    arg = Variable(name="x")
    node = FunctionCall(function_name="floor", arguments=[arg])
    assert node.function_name == "floor"
    assert len(node.arguments) == 1
    assert node.arguments[0] == arg


def test_function_call_multiple_args():
    """FunctionCall supports multi-argument functions."""
    from townlet.world.expression.ast_nodes import FunctionCall, Variable

    args = [Variable(name="a"), Variable(name="b"), Constant(value=5)]
    node = FunctionCall(function_name="max", arguments=args)
    assert node.function_name == "max"
    assert len(node.arguments) == 3
    assert node.arguments[0].name == "a"
    assert node.arguments[1].name == "b"
    assert node.arguments[2].value == 5


def test_function_call_visitor_integration():
    """FunctionCall node works with visitor pattern."""
    from townlet.world.expression.ast_nodes import FunctionCall

    class FnVisitor(ASTVisitor):
        def visit_function_call(self, node):
            arg_strs = [str(arg.value) for arg in node.arguments]
            return f"{node.function_name}({', '.join(arg_strs)})"

        def visit_constant(self, node):
            return node

    args = [Constant(value=1), Constant(value=2)]
    node = FunctionCall(function_name="max", arguments=args)
    visitor = FnVisitor()
    result = node.accept(visitor)

    assert result == "max(1, 2)"


def test_function_call_domain_specific():
    """FunctionCall supports HAMLET domain functions."""
    from townlet.world.expression.ast_nodes import FunctionCall

    arg = Constant(value="Fridge")
    node = FunctionCall(function_name="distance_to_affordance", arguments=[arg])

    assert node.function_name == "distance_to_affordance"


def test_if_then_else_basic():
    """IfThenElse represents ternary conditional."""
    from townlet.world.expression.ast_nodes import BinaryOp, IfThenElse, Variable

    condition = BinaryOp(Variable(name="energy"), OperatorType.LT, Constant(value=0.2))
    true_branch = Constant(value=1)
    false_branch = Constant(value=0)
    node = IfThenElse(condition=condition, true_branch=true_branch, false_branch=false_branch)

    assert node.condition == condition
    assert node.true_branch == true_branch
    assert node.false_branch == false_branch


def test_if_then_else_nested():
    """IfThenElse supports nested conditions."""
    from townlet.world.expression.ast_nodes import BinaryOp, IfThenElse, Variable

    # if is_night then (if energy < 0.3 then 2 else 1) else 0
    inner_condition = BinaryOp(Variable(name="energy"), OperatorType.LT, Constant(value=0.3))
    inner_ternary = IfThenElse(condition=inner_condition, true_branch=Constant(value=2), false_branch=Constant(value=1))
    outer_ternary = IfThenElse(condition=Variable(name="is_night"), true_branch=inner_ternary, false_branch=Constant(value=0))

    assert isinstance(outer_ternary.true_branch, IfThenElse)


def test_if_then_else_visitor_integration():
    """IfThenElse node works with visitor pattern."""
    from townlet.world.expression.ast_nodes import IfThenElse, Variable

    class TernaryVisitor(ASTVisitor):
        def visit_if_then_else(self, node):
            return f"(if ? then {node.true_branch.value} else {node.false_branch.value})"

        def visit_constant(self, node):
            return node

    node = IfThenElse(condition=Variable(name="is_night"), true_branch=Constant(value=1), false_branch=Constant(value=0))
    visitor = TernaryVisitor()
    result = node.accept(visitor)

    assert result == "(if ? then 1 else 0)"


def test_index_access_constant():
    """IndexAccess supports constant indices."""
    from townlet.world.expression.ast_nodes import IndexAccess, Variable

    base = Variable(name="items")
    index = Constant(value=0)
    node = IndexAccess(base=base, index=index)

    assert node.base == base
    assert node.index == index


def test_index_access_computed():
    """IndexAccess supports computed indices."""
    from townlet.world.expression.ast_nodes import BinaryOp, IndexAccess, Variable

    # values[i + 1]
    base = Variable(name="values")
    index = BinaryOp(Variable(name="i"), OperatorType.ADD, Constant(value=1))
    node = IndexAccess(base=base, index=index)

    assert isinstance(node.index, BinaryOp)
    assert node.base.name == "values"


def test_index_access_nested():
    """IndexAccess supports nested indexing (chaining)."""
    from townlet.world.expression.ast_nodes import IndexAccess, Variable

    # matrix[row][col] represented as IndexAccess(IndexAccess(matrix, row), col)
    inner = IndexAccess(base=Variable(name="matrix"), index=Variable(name="row"))
    outer = IndexAccess(base=inner, index=Variable(name="col"))

    assert isinstance(outer.base, IndexAccess)
    assert outer.index.name == "col"
    assert outer.base.base.name == "matrix"


def test_index_access_visitor_integration():
    """IndexAccess node works with visitor pattern."""
    from townlet.world.expression.ast_nodes import IndexAccess, Variable

    class IndexVisitor(ASTVisitor):
        def visit_index_access(self, node):
            return f"{node.base.name}[{node.index.value}]"

        def visit_variable(self, node):
            return node

        def visit_constant(self, node):
            return node

    node = IndexAccess(base=Variable(name="items"), index=Constant(value=0))
    visitor = IndexVisitor()
    result = node.accept(visitor)

    assert result == "items[0]"
