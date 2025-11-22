"""Function-call type checking regression tests."""

from __future__ import annotations

import pytest

from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError


def _check(expr: str, schema: dict[str, str]) -> str:
    parser = ExpressionParser()
    ast = parser.parse(expr)
    checker = TypeChecker(schema=schema)
    return checker.check(ast)


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("max(bar, 1)", "float"),
        ("min(bar, 1)", "float"),
        ("abs(bar)", "float"),
        ("clamp(bar, 0.0, 1.0)", "float"),
        ("clamp(health, 0, 1)", "int"),
    ],
)
def test_numeric_functions_type(expr: str, expected: str) -> None:
    schema = {"bar": "float", "health": "int"}
    assert _check(expr, schema) == expected


def test_function_type_errors() -> None:
    schema = {"flag": "bool", "val": "int"}
    with pytest.raises(TypeCheckError):
        _check("max(flag, val)", schema)
    with pytest.raises(TypeCheckError):
        _check("abs(flag)", schema)
    with pytest.raises(TypeCheckError):
        _check("clamp(flag, 0, 1)", schema)
    with pytest.raises(TypeCheckError):
        _check("unknown(val)", schema)
