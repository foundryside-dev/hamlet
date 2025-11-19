"""
Type checker tests for expression AST.

Tests type inference and validation for expression trees.
"""

import pytest

from townlet.world.expression.ast_nodes import (
    BinaryOp,
    Constant,
    OperatorType,
    PathAccess,
    UnaryOp,
)
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError


class TestConstantInference:
    """Test type inference for constant nodes."""

    def test_infer_int_constant(self):
        """Integer constants should infer as 'int'."""
        checker = TypeChecker(schema={})
        node = Constant(value=42)
        result_type = checker.check(node)
        assert result_type == "int"

    def test_infer_float_constant(self):
        """Float constants should infer as 'float'."""
        checker = TypeChecker(schema={})
        node = Constant(value=3.14)
        result_type = checker.check(node)
        assert result_type == "float"

    def test_infer_bool_constant(self):
        """Boolean constants should infer as 'bool'."""
        checker = TypeChecker(schema={})
        node = Constant(value=True)
        result_type = checker.check(node)
        assert result_type == "bool"

    def test_infer_string_constant(self):
        """String constants should infer as 'str'."""
        checker = TypeChecker(schema={})
        node = Constant(value="hello")
        result_type = checker.check(node)
        assert result_type == "str"


class TestBinaryOperators:
    """Test type checking for binary operators."""

    def test_type_check_arithmetic_operators(self):
        """Arithmetic operators require scalar operands."""
        checker = TypeChecker(schema={})

        # a + b where a, b are constants
        node = BinaryOp(
            left=Constant(value=5.0),
            op=OperatorType.ADD,
            right=Constant(value=3.0),
        )
        result_type = checker.check(node)

        assert result_type == "float"

    def test_type_check_comparison_operators(self):
        """Comparison operators return bool."""
        checker = TypeChecker(schema={})

        node = BinaryOp(
            left=Constant(value=10),
            op=OperatorType.GT,
            right=Constant(value=5),
        )
        result_type = checker.check(node)

        assert result_type == "bool"

    def test_type_check_logical_operators(self):
        """Logical operators require bool operands."""
        checker = TypeChecker(schema={})

        node = BinaryOp(
            left=Constant(value=True),
            op=OperatorType.AND,
            right=Constant(value=False),
        )
        result_type = checker.check(node)

        assert result_type == "bool"

    def test_type_check_incompatible_operands(self):
        """Type error when operands incompatible."""
        checker = TypeChecker(schema={})

        # true + 5 (bool + scalar)
        node = BinaryOp(
            left=Constant(value=True),
            op=OperatorType.ADD,
            right=Constant(value=5),
        )

        with pytest.raises(TypeCheckError, match="incompatible"):
            checker.check(node)


class TestUnaryOperators:
    """Test type checking for unary operators."""

    def test_type_check_negation(self):
        """Unary negation requires scalar operand."""
        checker = TypeChecker(schema={})

        node = UnaryOp(op=OperatorType.SUB, operand=Constant(value=10))
        result_type = checker.check(node)

        assert result_type == "int"

    def test_type_check_logical_not(self):
        """Logical not requires bool operand."""
        checker = TypeChecker(schema={})

        node = UnaryOp(op=OperatorType.NOT, operand=Constant(value=True))
        result_type = checker.check(node)

        assert result_type == "bool"

    def test_type_check_negation_wrong_type(self):
        """Type error when negating bool."""
        checker = TypeChecker(schema={})

        node = UnaryOp(op=OperatorType.SUB, operand=Constant(value=True))

        with pytest.raises(TypeCheckError, match="requires scalar"):
            checker.check(node)


class TestPathAccess:
    """Test type checking for path access."""

    def test_type_check_path_access_valid(self):
        """Type checker resolves valid paths from schema."""
        schema = {
            "bar.energy": "float",
            "bar.health": "float",
        }
        checker = TypeChecker(schema=schema)

        node = PathAccess(segments=["bar", "energy"])
        result_type = checker.check(node)

        assert result_type == "float"

    def test_type_check_path_access_invalid(self):
        """Type error for unknown path."""
        schema = {
            "bar.energy": "float",
        }
        checker = TypeChecker(schema=schema)

        node = PathAccess(segments=["bar", "invalid"])

        with pytest.raises(TypeCheckError, match="not found in schema"):
            checker.check(node)

    def test_type_check_nested_path(self):
        """Type checker handles deeply nested paths."""
        schema = {
            "global.vfs.is_night": "bool",
        }
        checker = TypeChecker(schema=schema)

        node = PathAccess(segments=["global", "vfs", "is_night"])
        result_type = checker.check(node)

        assert result_type == "bool"
