"""Performance benchmarks for expression evaluation.

Uses pytest-benchmark to measure expression parsing and evaluation overhead.
"""

import pytest
import torch

from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.parser import ExpressionParser


@pytest.fixture
def parser():
    """Expression parser."""
    return ExpressionParser()


class TestExpressionBenchmarks:
    """Benchmark expression operations."""

    def test_parse_simple_expression(self, benchmark, parser):
        """Benchmark parsing simple expression."""
        expr = "bar.energy + 0.3"

        result = benchmark(parser.parse, expr)

        assert result is not None

    def test_evaluate_simple_expression(self, benchmark, parser):
        """Benchmark evaluating simple expression."""
        expr = "bar.energy + 0.3"
        ast = parser.parse(expr)

        bars = {"energy": torch.tensor([0.5, 0.6])}
        context = ExecutionContext(
            bars=bars,
            vfs={},
            affordances={},
            temporal={},
            device=torch.device("cpu"),
        )

        evaluator = Evaluator(context)
        result = benchmark(evaluator.evaluate, ast)

        # Result is batched tensor [2] - check first element
        assert result[0].item() == pytest.approx(0.8)

    def test_evaluate_complex_expression(self, benchmark, parser):
        """Benchmark evaluating complex expression."""
        expr = "(bar.energy + 0.3) * (1.0 - bar.satiation)"
        ast = parser.parse(expr)

        bars = {
            "energy": torch.tensor([0.5, 0.6]),
            "satiation": torch.tensor([0.2, 0.3]),
        }
        context = ExecutionContext(
            bars=bars,
            vfs={},
            affordances={},
            temporal={},
            device=torch.device("cpu"),
        )

        evaluator = Evaluator(context)
        result = benchmark(evaluator.evaluate, ast)

        # (0.5 + 0.3) * (1.0 - 0.2) = 0.8 * 0.8 = 0.64
        # Result is batched tensor [2] - check first element
        assert result[0].item() == pytest.approx(0.64)

    def test_batch_expression_evaluation(self, benchmark, parser):
        """Benchmark batch expression evaluation (100 agents)."""
        expr = "bar.energy + 0.3"
        ast = parser.parse(expr)

        batch_size = 100
        bars = {"energy": torch.tensor([0.5] * batch_size)}

        def evaluate_batch():
            results = []
            for i in range(batch_size):
                context = ExecutionContext(
                    bars=bars,
                    vfs={},
                    affordances={},
                    temporal={},
                    device=torch.device("cpu"),
                )
                evaluator = Evaluator(context)
                results.append(evaluator.evaluate(ast))
            return results

        results = benchmark(evaluate_batch)

        assert len(results) == batch_size
        # Each result is a batched tensor - check all elements
        assert all(r[0].item() == pytest.approx(0.8) for r in results)
