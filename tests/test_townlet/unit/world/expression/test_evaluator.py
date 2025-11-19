"""Tests for expression evaluator."""

import torch

from townlet.world.expression import Constant
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
