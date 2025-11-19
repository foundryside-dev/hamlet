"""Tests for expression parser."""

from townlet.world.expression import (
    BinaryOp,
    Constant,
    OperatorType,
    PathAccess,
    Variable,
)
from townlet.world.expression.parser import ExpressionParser


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


def test_parse_simple_variable():
    """Parser converts identifiers to Variable nodes."""
    parser = ExpressionParser()
    result = parser.parse("intensity")

    assert isinstance(result, Variable)
    assert result.name == "intensity"


def test_parse_variable_with_underscore():
    """Parser supports underscores in variable names."""
    parser = ExpressionParser()
    result = parser.parse("slot_index")

    assert isinstance(result, Variable)
    assert result.name == "slot_index"


def test_parse_variable_with_numbers():
    """Parser supports numbers in variable names (not at start)."""
    parser = ExpressionParser()
    result = parser.parse("var123")

    assert isinstance(result, Variable)
    assert result.name == "var123"


def test_parse_path_access_two_segments():
    """Parser converts dotted paths to PathAccess nodes."""
    parser = ExpressionParser()
    result = parser.parse("self.position")

    assert isinstance(result, PathAccess)
    assert result.segments == ["self", "position"]


def test_parse_path_access_three_segments():
    """Parser handles multi-segment paths."""
    parser = ExpressionParser()
    result = parser.parse("target.bar.energy")

    assert isinstance(result, PathAccess)
    assert result.segments == ["target", "bar", "energy"]


def test_parse_path_access_deep():
    """Parser handles deeply nested paths."""
    parser = ExpressionParser()
    result = parser.parse("global.vfs.agent.is_night")

    assert isinstance(result, PathAccess)
    assert result.segments == ["global", "vfs", "agent", "is_night"]


def test_parse_addition():
    """Parser converts 'a + b' to BinaryOp(ADD, Variable(a), Variable(b))."""
    parser = ExpressionParser()
    result = parser.parse("a + b")

    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.ADD
    assert isinstance(result.left, Variable)
    assert result.left.name == "a"
    assert isinstance(result.right, Variable)
    assert result.right.name == "b"


def test_parse_multiplication():
    """Parser converts 'x * y' to BinaryOp(MUL, Variable(x), Variable(y))."""
    parser = ExpressionParser()
    result = parser.parse("x * y")

    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.MUL
    assert isinstance(result.left, Variable)
    assert result.left.name == "x"
    assert isinstance(result.right, Variable)
    assert result.right.name == "y"


def test_parse_comparison():
    """Parser converts 'x > 10' to BinaryOp(GT, Variable(x), Constant(10))."""
    parser = ExpressionParser()
    result = parser.parse("x > 10")

    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.GT
    assert isinstance(result.left, Variable)
    assert result.left.name == "x"
    assert isinstance(result.right, Constant)
    assert result.right.value == 10


def test_parse_logical_and():
    """Parser converts 'a and b' to BinaryOp(AND, Variable(a), Variable(b))."""
    parser = ExpressionParser()
    result = parser.parse("a and b")

    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.AND
    assert isinstance(result.left, Variable)
    assert result.left.name == "a"
    assert isinstance(result.right, Variable)
    assert result.right.name == "b"


def test_parse_operator_precedence():
    """Parser respects precedence: 'a + b * c' should be 'a + (b * c)'."""
    parser = ExpressionParser()
    result = parser.parse("a + b * c")

    # Root should be ADD
    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.ADD

    # Left side should be Variable(a)
    assert isinstance(result.left, Variable)
    assert result.left.name == "a"

    # Right side should be BinaryOp(MUL, Variable(b), Variable(c))
    assert isinstance(result.right, BinaryOp)
    assert result.right.op == OperatorType.MUL
    assert isinstance(result.right.left, Variable)
    assert result.right.left.name == "b"
    assert isinstance(result.right.right, Variable)
    assert result.right.right.name == "c"


def test_parse_parentheses_override_precedence():
    """Parser respects parentheses: '(a + b) * c' should be '(a + b) * c'."""
    parser = ExpressionParser()
    result = parser.parse("(a + b) * c")

    # Root should be MUL
    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.MUL

    # Left side should be BinaryOp(ADD, Variable(a), Variable(b))
    assert isinstance(result.left, BinaryOp)
    assert result.left.op == OperatorType.ADD
    assert isinstance(result.left.left, Variable)
    assert result.left.left.name == "a"
    assert isinstance(result.left.right, Variable)
    assert result.left.right.name == "b"

    # Right side should be Variable(c)
    assert isinstance(result.right, Variable)
    assert result.right.name == "c"
