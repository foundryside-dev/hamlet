"""
Type checker tests for expression AST.

Tests type inference and validation for expression trees.
"""

from townlet.world.expression.ast_nodes import (
    Constant,
)
from townlet.world.expression.type_checker import TypeChecker


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
