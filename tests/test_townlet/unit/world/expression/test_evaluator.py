"""Tests for expression evaluator."""

import torch

from townlet.world.expression import BinaryOp, Constant, OperatorType, PathAccess
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


def test_evaluate_index_access():
    """Evaluator handles tensor indexing."""
    from townlet.world.expression import IndexAccess

    ctx = ExecutionContext(
        bars={},
        vfs={"items": torch.tensor([10, 20, 30])},
        affordances={},
        temporal={},
    )
    evaluator = Evaluator(context=ctx)

    # vfs.items[0]
    node = IndexAccess(
        base=PathAccess(segments=["vfs", "items"]),
        index=Constant(value=0),
    )
    result = evaluator.evaluate(node)

    assert result.item() == 10


def test_evaluate_function_call_max():
    """Evaluator handles max() function."""
    from townlet.world.expression import FunctionCall

    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    # max(3, 7)
    node = FunctionCall(
        function_name="max",
        arguments=[Constant(value=3), Constant(value=7)],
    )
    result = evaluator.evaluate(node)

    assert torch.equal(result, torch.tensor(7))


def test_evaluate_function_call_min():
    """Evaluator handles min() function."""
    from townlet.world.expression import FunctionCall

    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    # min(3, 7)
    node = FunctionCall(
        function_name="min",
        arguments=[Constant(value=3), Constant(value=7)],
    )
    result = evaluator.evaluate(node)

    assert torch.equal(result, torch.tensor(3))


def test_evaluate_function_call_abs():
    """Evaluator handles abs() function."""
    from townlet.world.expression import FunctionCall

    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    # abs(-5)
    node = FunctionCall(
        function_name="abs",
        arguments=[Constant(value=-5)],
    )
    result = evaluator.evaluate(node)

    assert torch.equal(result, torch.tensor(5))


def test_evaluate_function_call_clamp():
    """Evaluator handles clamp() function."""
    from townlet.world.expression import FunctionCall

    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    # clamp(15, 0, 10)
    node = FunctionCall(
        function_name="clamp",
        arguments=[Constant(value=15), Constant(value=0), Constant(value=10)],
    )
    result = evaluator.evaluate(node)

    assert torch.equal(result, torch.tensor(10))


def test_evaluate_function_call_unknown():
    """Evaluator raises NotImplementedError for unknown functions."""
    from townlet.world.expression import FunctionCall

    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=ctx)

    # unknown_func(42)
    node = FunctionCall(
        function_name="unknown_func",
        arguments=[Constant(value=42)],
    )

    try:
        evaluator.evaluate(node)
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError as e:
        assert "unknown_func" in str(e)
        assert "Phase 2" in str(e)


def test_evaluate_if_then_else_vectorized():
    """Evaluator handles vectorized if/then/else using torch.where()."""
    from townlet.world.expression import IfThenElse

    ctx = ExecutionContext(
        bars={"energy": torch.tensor([0.1, 0.5, 0.9])},
        vfs={},
        affordances={},
        temporal={},
    )
    evaluator = Evaluator(context=ctx)

    # if bar.energy < 0.2 then 1 else 0
    node = IfThenElse(
        condition=BinaryOp(
            left=PathAccess(segments=["bar", "energy"]),
            op=OperatorType.LT,
            right=Constant(value=0.2),
        ),
        true_branch=Constant(value=1),
        false_branch=Constant(value=0),
    )
    result = evaluator.evaluate(node)

    # Energy values: [0.1, 0.5, 0.9]
    # Condition: [True, False, False]
    # Result: [1, 0, 0]
    assert torch.equal(result, torch.tensor([1, 0, 0]))


def test_full_integration_if_then_else():
    """Full integration: crisis bonus with if/then/else + path access + binary ops."""
    from townlet.world.expression import IfThenElse

    # Scenario: if energy < 0.2 then 10 * (0.2 - energy) else 0
    # Crisis bonus: 10x penalty for how far below threshold
    ctx = ExecutionContext(
        bars={"energy": torch.tensor([0.1, 0.2, 0.5])},
        vfs={},
        affordances={},
        temporal={},
    )
    evaluator = Evaluator(context=ctx)

    # if bar.energy < 0.2 then 10 * (0.2 - bar.energy) else 0
    node = IfThenElse(
        condition=BinaryOp(
            left=PathAccess(segments=["bar", "energy"]),
            op=OperatorType.LT,
            right=Constant(value=0.2),
        ),
        true_branch=BinaryOp(
            left=Constant(value=10),
            op=OperatorType.MUL,
            right=BinaryOp(
                left=Constant(value=0.2),
                op=OperatorType.SUB,
                right=PathAccess(segments=["bar", "energy"]),
            ),
        ),
        false_branch=Constant(value=0),
    )
    result = evaluator.evaluate(node)

    # Energy values: [0.1, 0.2, 0.5]
    # Condition: [True, False, False]
    # True branch: 10 * (0.2 - energy)
    #   - 0.1: 10 * 0.1 = 1.0
    #   - 0.2: N/A (not executed)
    #   - 0.5: N/A (not executed)
    # Result: [1.0, 0.0, 0.0]
    expected = torch.tensor([1.0, 0.0, 0.0])
    assert torch.allclose(result, expected)
