"""Tests for expression evaluator."""

import torch

from townlet.world.expression import BinaryOp, Constant, OperatorType
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator


def test_evaluate_constant():
    """Evaluator converts constants to tensors."""
    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    node = Constant(value=3.14)
    result = evaluator.evaluate(node)

    assert isinstance(result, torch.Tensor)
    assert torch.allclose(result, torch.tensor(3.14))


def test_evaluate_binary_op_arithmetic_add():
    """Evaluator handles arithmetic addition."""
    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    # 5 + 3
    node = BinaryOp(left=Constant(value=5), op=OperatorType.ADD, right=Constant(value=3))
    result = evaluator.evaluate(node)

    assert torch.allclose(result, torch.tensor(8))


def test_evaluate_binary_op_arithmetic_mul():
    """Evaluator handles arithmetic multiplication."""
    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    # 4 * 2.5
    node = BinaryOp(left=Constant(value=4), op=OperatorType.MUL, right=Constant(value=2.5))
    result = evaluator.evaluate(node)

    assert torch.allclose(result, torch.tensor(10.0))


def test_evaluate_binary_op_comparison_lt():
    """Evaluator handles comparison (less than)."""
    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    # 3 < 5
    node = BinaryOp(left=Constant(value=3), op=OperatorType.LT, right=Constant(value=5))
    result = evaluator.evaluate(node)

    assert torch.equal(result, torch.tensor(True))


def test_evaluate_binary_op_logical_and():
    """Evaluator handles logical AND."""
    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    # True and False
    node = BinaryOp(left=Constant(value=True), op=OperatorType.AND, right=Constant(value=False))
    result = evaluator.evaluate(node)

    assert torch.equal(result, torch.tensor(False))


def test_evaluate_unary_op_negation():
    """Evaluator handles unary negation (SUB)."""
    from townlet.world.expression import UnaryOp

    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    # -5
    node = UnaryOp(op=OperatorType.SUB, operand=Constant(value=5))
    result = evaluator.evaluate(node)

    assert torch.equal(result, torch.tensor(-5))


def test_evaluate_unary_op_not():
    """Evaluator handles logical NOT."""
    from townlet.world.expression import UnaryOp

    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    # not True
    node = UnaryOp(op=OperatorType.NOT, operand=Constant(value=True))
    result = evaluator.evaluate(node)

    assert torch.equal(result, torch.tensor(False))


def test_evaluate_path_access_bar():
    """Evaluator resolves bar paths."""
    from townlet.world.expression import PathAccess

    ctx = ExecutionContext(
        bars={"energy": torch.tensor([0.5, 0.8])},
        vfs={},
        affordances={},
        temporal={},
    )
    evaluator = Evaluator(context=ctx)

    # bar.energy
    node = PathAccess(segments=["bar", "energy"])
    result = evaluator.evaluate(node)

    assert torch.equal(result, torch.tensor([0.5, 0.8]))


def test_evaluate_path_access_vfs():
    """Evaluator resolves VFS paths."""
    from townlet.world.expression import PathAccess

    ctx = ExecutionContext(
        bars={},
        vfs={"is_night": torch.tensor([True, False])},
        affordances={},
        temporal={},
    )
    evaluator = Evaluator(context=ctx)

    # vfs.is_night
    node = PathAccess(segments=["vfs", "is_night"])
    result = evaluator.evaluate(node)

    assert torch.equal(result, torch.tensor([True, False]))


def test_evaluate_variable():
    """Evaluator resolves simple variables via context."""
    from townlet.world.expression import Variable

    ctx = ExecutionContext(
        bars={"health": torch.tensor([0.9, 1.0])},
        vfs={},
        affordances={},
        temporal={},
    )
    evaluator = Evaluator(context=ctx)

    # Variable name should resolve via context.get()
    # In this case, "bar.health" stored in bars
    node = Variable(name="bar.health")
    result = evaluator.evaluate(node)

    assert torch.equal(result, torch.tensor([0.9, 1.0]))
