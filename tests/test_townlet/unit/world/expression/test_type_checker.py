"""
Type checker tests for expression AST.

Tests type inference and validation for expression trees.
"""

import pytest

from townlet.world.expression.ast_nodes import (
    BinaryOp,
    Constant,
    IfThenElse,
    OperatorType,
    PathAccess,
    UnaryOp,
    Variable,
)
from townlet.world.expression.parser import ExpressionParser
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

    def test_type_check_equality_allows_matching_types(self):
        """Equality supports bool, str, and numeric combos."""
        checker = TypeChecker(schema={})

        bool_eq = BinaryOp(left=Constant(value=True), op=OperatorType.EQ, right=Constant(value=False))
        str_eq = BinaryOp(left=Constant(value="a"), op=OperatorType.NEQ, right=Constant(value="b"))
        mixed_numeric = BinaryOp(left=Constant(value=1), op=OperatorType.EQ, right=Constant(value=1.0))

        assert checker.check(bool_eq) == "bool"
        assert checker.check(str_eq) == "bool"
        assert checker.check(mixed_numeric) == "bool"

        bad = BinaryOp(left=Constant(value=True), op=OperatorType.EQ, right=Constant(value="x"))
        with pytest.raises(TypeCheckError):
            checker.check(bad)

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

    def test_type_check_agent_reference_traversal(self):
        """Agent references resolve through target.* schema entries."""
        schema = {
            "vfs.friend": "agent_ref",
            "target.vfs.energy": "float",
            "target.bar.energy": "float",
        }
        checker = TypeChecker(schema=schema)

        vfs_path = PathAccess(segments=["vfs", "friend", "vfs", "energy"])
        bar_path = PathAccess(segments=["vfs", "friend", "bar", "energy"])

        assert checker.check(vfs_path) == "float"
        assert checker.check(bar_path) == "float"

    def test_type_check_item_reference_traversal(self):
        """Item references map into self.vfs schema entries."""
        schema = {
            "vfs.held_item": "item_ref",
            "self.vfs.quality": "float",
        }
        checker = TypeChecker(schema=schema)

        vfs_path = PathAccess(segments=["vfs", "held_item", "vfs", "quality"])

        assert checker.check(vfs_path) == "float"

    def test_type_check_target_reference_traversal(self):
        """Reference traversal under target.* prefix is supported."""
        schema = {
            "target.vfs.friend": "agent_ref",
            "target.vfs.held_item": "item_ref",
            "target.vfs.energy": "float",
            "target.bar.energy": "float",
            "self.vfs.quality": "float",
        }
        checker = TypeChecker(schema=schema)

        agent_ref_path = PathAccess(segments=["target", "vfs", "friend", "vfs", "energy"])
        bar_ref_path = PathAccess(segments=["target", "vfs", "friend", "bar", "energy"])
        item_ref_path = PathAccess(segments=["target", "vfs", "held_item", "vfs", "quality"])

        assert checker.check(agent_ref_path) == "float"
        assert checker.check(bar_ref_path) == "float"
        assert checker.check(item_ref_path) == "float"

    def test_type_check_self_reference_traversal(self):
        """Reference traversal under self.* prefix is supported."""
        schema = {
            "self.vfs.friend": "agent_ref",
            "target.vfs.energy": "float",
            "target.bar.energy": "float",
        }
        checker = TypeChecker(schema=schema)

        agent_ref_path = PathAccess(segments=["self", "vfs", "friend", "vfs", "energy"])
        bar_ref_path = PathAccess(segments=["self", "vfs", "friend", "bar", "energy"])

        assert checker.check(agent_ref_path) == "float"
        assert checker.check(bar_ref_path) == "float"

    def test_type_check_multi_hop_reference_traversal(self):
        """Nested reference chains resolve recursively."""
        schema = {
            "vfs.friend": "agent_ref",
            "target.vfs.friend": "agent_ref",
            "target.vfs.energy": "float",
            "target.bar.energy": "float",
            "target.vfs.held_item": "item_ref",
            "self.vfs.quality": "float",
        }
        checker = TypeChecker(schema=schema)

        double_agent = PathAccess(segments=["vfs", "friend", "vfs", "friend", "vfs", "energy"])
        agent_bar = PathAccess(segments=["vfs", "friend", "vfs", "friend", "bar", "energy"])
        item_chain = PathAccess(segments=["vfs", "friend", "vfs", "held_item", "vfs", "quality"])

        assert checker.check(double_agent) == "float"
        assert checker.check(agent_bar) == "float"
        assert checker.check(item_chain) == "float"

    def test_type_check_nested_reference_traversal(self):
        """Nested references are resolved recursively."""
        schema = {
            "vfs.friend": "agent_ref",
            "target.vfs.friend": "agent_ref",
            "target.vfs.energy": "float",
        }
        checker = TypeChecker(schema=schema)

        nested = PathAccess(segments=["vfs", "friend", "vfs", "friend", "vfs", "energy"])
        assert checker.check(nested) == "float"

    def test_type_check_target_prefixed_multi_hop_reference(self):
        """Reference chains rooted at target.* resolve across multiple hops."""
        schema = {
            "target.vfs.friend": "agent_ref",
            "target.vfs.energy": "float",
        }
        checker = TypeChecker(schema=schema)

        nested = PathAccess(segments=["target", "vfs", "friend", "vfs", "friend", "vfs", "energy"])
        assert checker.check(nested) == "float"


class TestVariable:
    """Test type checking for variables."""

    def test_type_check_variable_in_schema(self):
        """Variables resolve from schema (simple names)."""
        schema = {
            "intensity": "float",
            "duration": "float",
        }
        checker = TypeChecker(schema=schema)

        node = Variable(name="intensity")
        result_type = checker.check(node)

        assert result_type == "float"

    def test_type_check_variable_not_in_schema(self):
        """Type error for unknown variable."""
        schema = {}
        checker = TypeChecker(schema=schema)

        node = Variable(name="unknown")

        with pytest.raises(TypeCheckError, match="not found"):
            checker.check(node)


class TestIntegration:
    """Integration tests: Parse then type check."""

    def test_integration_parse_and_typecheck(self):
        """Integration: parse expression string, then type check."""
        schema = {
            "bar.energy": "float",
            "bar.health": "float",
        }

        parser = ExpressionParser()
        checker = TypeChecker(schema=schema)

        # Parse "bar.energy + 0.05"
        ast = parser.parse("bar.energy + 0.05")

        # Type check
        result_type = checker.check(ast)

        assert result_type == "float"

    def test_integration_type_error_from_parsed_expr(self):
        """Integration: type error from parsed expression."""
        schema = {"x": "int"}

        parser = ExpressionParser()
        checker = TypeChecker(schema=schema)

        # Parse "x and true" (type error: int and bool)
        ast = parser.parse("x and true")

        with pytest.raises(TypeCheckError, match="requires bool"):
            checker.check(ast)

    def test_type_check_if_then_else(self):
        """Type checker validates if/then/else conditionals."""
        schema = {}
        checker = TypeChecker(schema=schema)

        # if true then 1 else 2
        node = IfThenElse(
            condition=Constant(value=True),
            true_branch=Constant(value=1),
            false_branch=Constant(value=2),
        )
        result_type = checker.check(node)

        assert result_type == "int"

    def test_type_check_if_non_bool_condition(self):
        """Type error when condition is not bool."""
        schema = {}
        checker = TypeChecker(schema=schema)

        # if 5 then 1 else 2  (condition is int, not bool)
        node = IfThenElse(
            condition=Constant(value=5),
            true_branch=Constant(value=1),
            false_branch=Constant(value=2),
        )

        with pytest.raises(TypeCheckError, match="must be bool"):
            checker.check(node)

    def test_type_check_if_mismatched_branches(self):
        """Type error when branches have different types."""
        schema = {}
        checker = TypeChecker(schema=schema)

        # if true then 1 else true  (int vs bool)
        node = IfThenElse(
            condition=Constant(value=True),
            true_branch=Constant(value=1),
            false_branch=Constant(value=True),
        )

        with pytest.raises(TypeCheckError, match="must have same type"):
            checker.check(node)
