"""Tests for expression parser."""
import pytest
from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression import Constant


def test_parse_float_constant():
    """Parser converts float strings to Constant nodes."""
    parser = ExpressionParser()
    result = parser.parse("0.05")

    assert isinstance(result, Constant)
    assert result.value == 0.05
    assert isinstance(result.value, float)


def test_parse_integer_constant():
    """Parser converts integer strings to Constant nodes."""
    parser = ExpressionParser()
    result = parser.parse("42")

    assert isinstance(result, Constant)
    assert result.value == 42
    assert isinstance(result.value, int)


def test_parse_boolean_true():
    """Parser converts 'true' to Constant(True)."""
    parser = ExpressionParser()
    result = parser.parse("true")

    assert isinstance(result, Constant)
    assert result.value is True


def test_parse_boolean_false():
    """Parser converts 'false' to Constant(False)."""
    parser = ExpressionParser()
    result = parser.parse("false")

    assert isinstance(result, Constant)
    assert result.value is False


def test_parse_string_constant():
    """Parser converts quoted strings to Constant nodes."""
    parser = ExpressionParser()
    result = parser.parse('"energy"')

    assert isinstance(result, Constant)
    assert result.value == "energy"
    assert isinstance(result.value, str)


def test_parse_string_with_single_quotes():
    """Parser supports single-quoted strings."""
    parser = ExpressionParser()
    result = parser.parse("'Fridge'")

    assert isinstance(result, Constant)
    assert result.value == "Fridge"


def test_parse_integer_vs_float_distinction():
    """Parser preserves int vs float types (critical for type checking)."""
    parser = ExpressionParser()

    # Integer should parse as int
    int_result = parser.parse("42")
    assert isinstance(int_result, Constant)
    assert isinstance(int_result.value, int)
    assert int_result.value == 42

    # Float should parse as float
    float_result = parser.parse("42.0")
    assert isinstance(float_result, Constant)
    assert isinstance(float_result.value, float)
    assert float_result.value == 42.0

    # Scientific notation should parse as float
    sci_result = parser.parse("1e-3")
    assert isinstance(sci_result, Constant)
    assert isinstance(sci_result.value, float)
    assert sci_result.value == 0.001
