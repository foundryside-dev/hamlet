"""Unit tests for AST node dataclasses."""

from dataclasses import FrozenInstanceError

import pytest

from townlet.world.expression.ast_nodes import (
    ASTNode,
    BinaryOp,
    Constant,
    FunctionCall,
    IfThenElse,
    IndexAccess,
    OperatorType,
    PathAccess,
    Reduce,
    Switch,
    UnaryOp,
    Variable,
)


def test_astnode_defaults_are_none():
    """Base ASTNode metadata defaults to None when not provided."""
    node = Constant(value=1)

    assert node.line is None
    assert node.column is None
    assert node.type_annotation is None


def test_astnode_metadata_can_be_set():
    """Line/column/type_annotation can be provided."""
    node = Variable(name="foo", line=2, column=4, type_annotation="float")

    assert node.line == 2
    assert node.column == 4
    assert node.type_annotation == "float"


def test_nodes_are_frozen():
    """Nodes are immutable dataclasses (frozen)."""
    node = Constant(value=1)

    with pytest.raises(FrozenInstanceError):
        node.value = 2  # type: ignore[misc]


def test_path_access_segments_preserved():
    """PathAccess stores segments in order."""
    node = PathAccess(segments=["target", "bar", "energy"])

    assert node.segments == ["target", "bar", "energy"]


def test_binary_op_fields_set():
    """BinaryOp captures left/right/op fields."""
    left = Variable(name="a")
    right = Variable(name="b")
    node = BinaryOp(left=left, op=OperatorType.ADD, right=right, line=1, column=2)

    assert node.left is left
    assert node.right is right
    assert node.op is OperatorType.ADD
    assert node.line == 1
    assert node.column == 2


def test_unary_op_fields_set():
    """UnaryOp captures operand and operator."""
    operand = Constant(value=10)
    node = UnaryOp(op=OperatorType.SUB, operand=operand)

    assert node.operand is operand
    assert node.op is OperatorType.SUB


def test_function_call_arguments_immutable_binding():
    """FunctionCall stores function name and argument list."""
    arg = Constant(value=3)
    call = FunctionCall(function_name="inc", arguments=[arg])

    assert call.function_name == "inc"
    assert call.arguments == [arg]


def test_if_then_else_fields_set():
    """IfThenElse stores condition and branch nodes."""
    node = IfThenElse(condition=Constant(True), true_branch=Constant(1), false_branch=Constant(0))

    assert isinstance(node.condition, Constant)
    assert node.true_branch.value == 1
    assert node.false_branch.value == 0


def test_index_access_fields_set():
    """IndexAccess stores base and index expressions."""
    base = Variable(name="arr")
    index = Constant(value=2)
    node = IndexAccess(base=base, index=index, type_annotation="int")

    assert node.base is base
    assert node.index is index
    assert node.type_annotation == "int"


def test_dataclass_equality_and_hash():
    """Frozen dataclasses support equality and hashing for identical content."""
    a1 = Constant(value=5, line=1, column=1)
    a2 = Constant(value=5, line=1, column=1)

    assert a1 == a2
    assert hash(a1) == hash(a2)


def test_astnode_is_base_class():
    """All nodes derive from ASTNode for visitor dispatch."""
    node = PathAccess(segments=["a", "b"])

    assert isinstance(node, ASTNode)


def test_switch_fields_set_and_default_none():
    """Switch node stores switch expr, cases, and optional default."""
    switch_expr = Variable(name="mode")
    case1 = (Constant(value="a"), [])
    case2 = (Constant(value="b"), [])
    node = Switch(switch_expr=switch_expr, cases=[case1, case2])

    assert node.switch_expr is switch_expr
    assert node.cases == [case1, case2]
    assert node.default is None


def test_reduce_fields_set():
    """Reduce node stores collection, iterator, init, body, and optional target."""
    collection = Variable(name="arr")
    init = Constant(value=0)
    body = BinaryOp(left=Variable(name="acc"), op=OperatorType.ADD, right=Variable(name="item"))
    node = Reduce(collection=collection, iterator="item", init=init, body=body, target="out.var")

    assert node.collection is collection
    assert node.iterator == "item"
    assert node.init is init
    assert node.body is body
    assert node.target == "out.var"
