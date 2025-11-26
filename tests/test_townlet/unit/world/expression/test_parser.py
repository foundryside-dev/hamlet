"""Tests for expression parser."""

import pytest
from pyparsing import ParseException

from townlet.world.expression import (
    BinaryOp,
    Constant,
    FunctionCall,
    IfThenElse,
    IndexAccess,
    OperatorType,
    PathAccess,
    UnaryOp,
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


def test_parse_unary_minus():
    """Parser converts '-x' to UnaryOp(SUB, Variable(x))."""
    parser = ExpressionParser()
    result = parser.parse("-x")

    assert isinstance(result, UnaryOp)
    assert result.op == OperatorType.SUB
    assert isinstance(result.operand, Variable)
    assert result.operand.name == "x"


def test_parse_unary_not():
    """Parser converts 'not active' to UnaryOp(NOT, Variable(active))."""
    parser = ExpressionParser()
    result = parser.parse("not active")

    assert isinstance(result, UnaryOp)
    assert result.op == OperatorType.NOT
    assert isinstance(result.operand, Variable)
    assert result.operand.name == "active"


def test_parse_double_negation():
    """Parser converts '--x' to UnaryOp(SUB, UnaryOp(SUB, Variable(x)))."""
    parser = ExpressionParser()
    result = parser.parse("--x")

    # Outer negation
    assert isinstance(result, UnaryOp)
    assert result.op == OperatorType.SUB

    # Inner negation
    assert isinstance(result.operand, UnaryOp)
    assert result.operand.op == OperatorType.SUB

    # Variable
    assert isinstance(result.operand.operand, Variable)
    assert result.operand.operand.name == "x"


def test_parse_function_call_no_args():
    """Parser converts 'get_time()' to FunctionCall('get_time', [])."""
    parser = ExpressionParser()
    result = parser.parse("get_time()")

    assert isinstance(result, FunctionCall)
    assert result.function_name == "get_time"
    assert result.arguments == []


def test_parse_function_call_single_arg():
    """Parser converts 'abs(x)' to FunctionCall('abs', [Variable(x)])."""
    parser = ExpressionParser()
    result = parser.parse("abs(x)")

    assert isinstance(result, FunctionCall)
    assert result.function_name == "abs"
    assert len(result.arguments) == 1
    assert isinstance(result.arguments[0], Variable)
    assert result.arguments[0].name == "x"


def test_parse_function_call_multiple_args():
    """Parser converts 'clamp(val, 0, 1)' to FunctionCall('clamp', [Variable, Constant, Constant])."""
    parser = ExpressionParser()
    result = parser.parse("clamp(val, 0, 1)")

    assert isinstance(result, FunctionCall)
    assert result.function_name == "clamp"
    assert len(result.arguments) == 3
    assert isinstance(result.arguments[0], Variable)
    assert result.arguments[0].name == "val"
    assert isinstance(result.arguments[1], Constant)
    assert result.arguments[1].value == 0
    assert isinstance(result.arguments[2], Constant)
    assert result.arguments[2].value == 1


def test_parse_function_call_string_arg():
    """Parser converts 'distance_to_affordance("Fridge")' with string argument."""
    parser = ExpressionParser()
    result = parser.parse('distance_to_affordance("Fridge")')

    assert isinstance(result, FunctionCall)
    assert result.function_name == "distance_to_affordance"
    assert len(result.arguments) == 1
    assert isinstance(result.arguments[0], Constant)
    assert result.arguments[0].value == "Fridge"


def test_parse_nested_function_calls():
    """Parser converts 'max(abs(x), abs(y))' with nested function calls."""
    parser = ExpressionParser()
    result = parser.parse("max(abs(x), abs(y))")

    assert isinstance(result, FunctionCall)
    assert result.function_name == "max"
    assert len(result.arguments) == 2

    # First argument: abs(x)
    assert isinstance(result.arguments[0], FunctionCall)
    assert result.arguments[0].function_name == "abs"
    assert len(result.arguments[0].arguments) == 1
    assert isinstance(result.arguments[0].arguments[0], Variable)
    assert result.arguments[0].arguments[0].name == "x"

    # Second argument: abs(y)
    assert isinstance(result.arguments[1], FunctionCall)
    assert result.arguments[1].function_name == "abs"
    assert len(result.arguments[1].arguments) == 1
    assert isinstance(result.arguments[1].arguments[0], Variable)
    assert result.arguments[1].arguments[0].name == "y"


def test_parse_if_then_else():
    """Parser converts 'if x > 0 then 1 else -1' to IfThenElse node."""
    parser = ExpressionParser()
    result = parser.parse("if x > 0 then 1 else -1")

    assert isinstance(result, IfThenElse)

    # Condition: x > 0
    assert isinstance(result.condition, BinaryOp)
    assert result.condition.op == OperatorType.GT
    assert isinstance(result.condition.left, Variable)
    assert result.condition.left.name == "x"
    assert isinstance(result.condition.right, Constant)
    assert result.condition.right.value == 0

    # Then branch: 1
    assert isinstance(result.true_branch, Constant)
    assert result.true_branch.value == 1

    # Else branch: -1
    assert isinstance(result.false_branch, UnaryOp)
    assert result.false_branch.op == OperatorType.SUB
    assert isinstance(result.false_branch.operand, Constant)
    assert result.false_branch.operand.value == 1


def test_parse_nested_if_then_else():
    """Parser converts 'if a then (if b then 1 else 2) else 3' with nested conditionals."""
    parser = ExpressionParser()
    result = parser.parse("if a then (if b then 1 else 2) else 3")

    assert isinstance(result, IfThenElse)

    # Outer condition: a
    assert isinstance(result.condition, Variable)
    assert result.condition.name == "a"

    # Then branch: if b then 1 else 2
    assert isinstance(result.true_branch, IfThenElse)
    assert isinstance(result.true_branch.condition, Variable)
    assert result.true_branch.condition.name == "b"
    assert isinstance(result.true_branch.true_branch, Constant)
    assert result.true_branch.true_branch.value == 1
    assert isinstance(result.true_branch.false_branch, Constant)
    assert result.true_branch.false_branch.value == 2

    # Else branch: 3
    assert isinstance(result.false_branch, Constant)
    assert result.false_branch.value == 3


def test_parse_exponentiation_right_associative():
    """Parser converts '2 ** 3 ** 4' to '2 ** (3 ** 4)' (right associative)."""
    parser = ExpressionParser()
    result = parser.parse("2 ** 3 ** 4")

    # Root should be POW
    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.POW

    # Left side should be Constant(2)
    assert isinstance(result.left, Constant)
    assert result.left.value == 2

    # Right side should be BinaryOp(POW, Constant(3), Constant(4))
    assert isinstance(result.right, BinaryOp)
    assert result.right.op == OperatorType.POW
    assert isinstance(result.right.left, Constant)
    assert result.right.left.value == 3
    assert isinstance(result.right.right, Constant)
    assert result.right.right.value == 4


def test_parse_index_access_constant():
    """Parser handles array indexing with constant index."""
    parser = ExpressionParser()
    result = parser.parse("inventory[0]")

    assert isinstance(result, IndexAccess)
    assert isinstance(result.base, Variable)
    assert result.base.name == "inventory"
    assert isinstance(result.index, Constant)
    assert result.index.value == 0


def test_parse_index_access_variable():
    """Parser handles array indexing with variable index."""
    parser = ExpressionParser()
    result = parser.parse("items[slot_index]")

    assert isinstance(result, IndexAccess)
    assert isinstance(result.base, Variable)
    assert result.base.name == "items"
    assert isinstance(result.index, Variable)
    assert result.index.name == "slot_index"


def test_parse_index_access_expression():
    """Parser handles array indexing with expression index."""
    parser = ExpressionParser()
    result = parser.parse("bars[i + 1]")

    assert isinstance(result, IndexAccess)
    assert isinstance(result.index, BinaryOp)
    assert result.index.op == OperatorType.ADD


def test_parse_nested_index_access():
    """Parser handles multi-dimensional indexing."""
    parser = ExpressionParser()
    result = parser.parse("grid[x][y]")

    # Should parse as: (grid[x])[y]
    assert isinstance(result, IndexAccess)
    assert isinstance(result.base, IndexAccess)
    assert result.base.base.name == "grid"
    assert result.base.index.name == "x"
    assert result.index.name == "y"


def test_parse_float_with_trailing_dot():
    """Parser treats '1.' as float constant."""
    parser = ExpressionParser()
    result = parser.parse("1.")

    assert isinstance(result, Constant)
    assert isinstance(result.value, float)
    assert result.value == 1.0


def test_parse_scientific_notation_positive_exponent():
    """Parser handles scientific notation with positive exponent."""
    parser = ExpressionParser()
    result = parser.parse("1e3")

    assert isinstance(result, Constant)
    assert isinstance(result.value, float)
    assert result.value == 1000.0


def test_parse_nested_index_expression():
    """Parser handles nested index expressions (foo[bar[0]])."""
    parser = ExpressionParser()
    result = parser.parse("foo[bar[0]]")

    assert isinstance(result, IndexAccess)
    assert isinstance(result.base, Variable)
    assert result.base.name == "foo"
    assert isinstance(result.index, IndexAccess)
    assert isinstance(result.index.base, Variable)
    assert result.index.base.name == "bar"
    assert isinstance(result.index.index, Constant)
    assert result.index.index.value == 0


def test_parse_raises_on_trailing_operator():
    """Parser raises ParseException with position for trailing operator."""
    parser = ExpressionParser()

    with pytest.raises(ParseException) as excinfo:
        parser.parse("a +")

    assert excinfo.value.col == 3


def test_parse_raises_on_unclosed_parenthesis():
    """Parser raises on missing closing parenthesis."""
    parser = ExpressionParser()

    with pytest.raises(ParseException):
        parser.parse("(a + b")


def test_parse_raises_on_double_comma_in_arguments():
    """Parser rejects malformed function arguments with double comma."""
    parser = ExpressionParser()

    with pytest.raises(ParseException):
        parser.parse("max(a,,b)")


def test_parse_raises_on_invalid_token():
    """Parser rejects illegal tokens in expressions."""
    parser = ExpressionParser()

    with pytest.raises(ParseException):
        parser.parse("a $ b")


def test_parse_rejects_keyword_as_identifier():
    """Parser rejects reserved keywords used as identifiers."""
    parser = ExpressionParser()

    with pytest.raises(ValueError):
        parser.parse("and + 1")
