"""Integration tests for expression system.

Tests the complete pipeline: Parse → Type Check → Evaluate
"""

import pytest
import torch

from townlet.world.expression import ExpressionParser
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError


def test_full_pipeline():
    """Test Parse → Type Check → Evaluate pipeline."""
    parser = ExpressionParser()

    # Parse
    ast = parser.parse("bar.health + 10")
    assert ast is not None

    # Type Check (schema uses paths)
    schema = {"bar.health": "float"}
    type_checker = TypeChecker(schema=schema)
    type_checker.check(ast)

    # Evaluate
    context = ExecutionContext(bars={"health": torch.tensor(50.0)}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=context)
    result = evaluator.evaluate(ast)
    assert torch.allclose(result, torch.tensor(60.0))


def test_pipeline_with_complex_expression():
    """Test pipeline with nested operations."""
    parser = ExpressionParser()

    ast = parser.parse("(bar.energy * 2) + (bar.health / 5)")
    schema = {"bar.energy": "float", "bar.health": "float"}
    type_checker = TypeChecker(schema=schema)
    type_checker.check(ast)

    context = ExecutionContext(bars={"energy": torch.tensor(25.0), "health": torch.tensor(100.0)}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=context)
    result = evaluator.evaluate(ast)

    assert torch.allclose(result, torch.tensor(70.0))  # (25*2) + (100/5) = 50 + 20


def test_pipeline_with_comparison():
    """Test pipeline with comparison operator."""
    parser = ExpressionParser()

    ast = parser.parse("bar.health > 50")
    schema = {"bar.health": "float"}
    type_checker = TypeChecker(schema=schema)
    type_checker.check(ast)

    context = ExecutionContext(bars={"health": torch.tensor(75.0)}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=context)
    result = evaluator.evaluate(ast)

    assert result.item() is True


def test_pipeline_with_logical_operators():
    """Test pipeline with logical operations."""
    parser = ExpressionParser()

    ast = parser.parse("bar.energy > 20 and bar.health < 100")
    schema = {"bar.energy": "float", "bar.health": "float"}
    type_checker = TypeChecker(schema=schema)
    type_checker.check(ast)

    context = ExecutionContext(bars={"energy": torch.tensor(30.0), "health": torch.tensor(50.0)}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=context)
    result = evaluator.evaluate(ast)

    assert result.item() is True


def test_pipeline_with_function_call():
    """Test pipeline with function call (skipped - Phase 2)."""
    # Function call type checking not implemented in Phase 1
    pytest.skip("Function call type checking deferred to Phase 2")


def test_pipeline_type_error_detection():
    """Test that type checker catches errors before evaluation."""
    parser = ExpressionParser()

    ast = parser.parse("bar.unknown_var + 10")
    schema = {"bar.health": "float"}  # bar.unknown_var not in schema
    type_checker = TypeChecker(schema=schema)

    with pytest.raises(TypeCheckError, match="Path 'bar.unknown_var' not found in schema"):
        type_checker.check(ast)


def test_pipeline_with_unary_negation():
    """Test pipeline with unary negation."""
    parser = ExpressionParser()

    ast = parser.parse("-bar.energy")
    schema = {"bar.energy": "float"}
    type_checker = TypeChecker(schema=schema)
    type_checker.check(ast)

    context = ExecutionContext(bars={"energy": torch.tensor(25.0)}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=context)
    result = evaluator.evaluate(ast)

    assert torch.allclose(result, torch.tensor(-25.0))


def test_pipeline_with_logical_not():
    """Test pipeline with logical NOT."""
    parser = ExpressionParser()

    ast = parser.parse("not (bar.health > 50)")
    schema = {"bar.health": "float"}
    type_checker = TypeChecker(schema=schema)
    type_checker.check(ast)

    context = ExecutionContext(bars={"health": torch.tensor(30.0)}, vfs={}, affordances={}, temporal={})
    evaluator = Evaluator(context=context)
    result = evaluator.evaluate(ast)

    assert result.item() is True


def test_pipeline_with_index_access():
    """Test pipeline with array indexing (skipped - Phase 4)."""
    # Index access type checking not implemented in Phase 1
    pytest.skip("Index access type checking deferred to Phase 4")


def test_pipeline_multiple_expressions():
    """Test pipeline with multiple different expression types."""
    parser = ExpressionParser()

    expressions = [
        ("5.0 + 3.0", {}, {}, 8.0, False),
        ("bar.x * 2.0", {"x": 10.0}, {"bar.x": "float"}, 20.0, False),
        ("bar.a > bar.b", {"a": 5.0, "b": 3.0}, {"bar.a": "float", "bar.b": "float"}, True, True),
        ("(bar.a + bar.b) / 2.0", {"a": 10.0, "b": 20.0}, {"bar.a": "float", "bar.b": "float"}, 15.0, False),
    ]

    for expr_str, bars, schema, expected, is_bool in expressions:
        ast = parser.parse(expr_str)
        type_checker = TypeChecker(schema=schema)
        type_checker.check(ast)

        context = ExecutionContext(bars={k: torch.tensor(v) for k, v in bars.items()}, vfs={}, affordances={}, temporal={})
        evaluator = Evaluator(context=context)
        result = evaluator.evaluate(ast)

        if is_bool:
            assert result.item() is expected, f"Failed for expression: {expr_str}"
        else:
            assert torch.allclose(result, torch.tensor(expected)), f"Failed for expression: {expr_str}"
