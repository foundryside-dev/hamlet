"""Type checker for HAMLET Expression Language.

Performs bottom-up type inference and validation on expression ASTs.
Ensures type safety before evaluation (e.g., no string + int).

Type System:
    - Primitive types: int, float, bool, str
    - Container types: list[T], dict[str, T]
    - Special: any (for dynamic contexts)

Type Inference Rules:
    - Constants: Inferred from Python type
    - Variables: Looked up in schema
    - BinaryOp: Type-specific rules (e.g., int + int → int, int + float → float)
    - Functions: Signature lookup (e.g., max(int, int) → int)
    - Conditionals: Branches must unify to common type

Design:
    - Uses Visitor pattern for traversal
    - Bottom-up inference (visit children, infer parent)
    - Raises TypeCheckError on violations
"""

from typing import Any

from townlet.world.expression.ast_nodes import (
    ASTNode,
    ASTVisitor,
    BinaryOp,
    Constant,
    FunctionCall,
    IfThenElse,
    IndexAccess,
    PathAccess,
    UnaryOp,
    Variable,
)


class TypeCheckError(Exception):
    """Raised when type checking fails.

    Examples:
        - Type mismatch: "hello" + 5
        - Unknown variable: undefined_var
        - Invalid operation: true / false
        - Function signature mismatch: max("a", "b") when max expects numbers
    """

    pass


class TypeChecker(ASTVisitor):
    """Type checker for expression ASTs.

    Performs bottom-up type inference:
        1. Visit leaf nodes (constants, variables) - infer types
        2. Visit intermediate nodes (operators, functions) - check operand types
        3. Visit root node - return final type

    Attributes:
        schema: Type schema for variables/paths (e.g., {"energy": "float", "is_night": "bool"})
    """

    def __init__(self, schema: dict[str, Any]):
        """Initialize type checker with schema.

        Args:
            schema: Type information for variables and paths
                   Example: {"energy": "float", "target.bar.health": "float"}
        """
        self.schema = schema

    def check(self, node: ASTNode) -> str:
        """Type check an AST and return inferred type.

        Args:
            node: Root of expression AST

        Returns:
            Inferred type as string ("int", "float", "bool", "str", etc.)

        Raises:
            TypeCheckError: If type checking fails
        """
        return node.accept(self)

    def visit_constant(self, node: Constant) -> str:
        """Infer type from constant value.

        Args:
            node: Constant AST node

        Returns:
            Type name: "int", "float", "bool", or "str"
        """
        value = node.value
        if isinstance(value, bool):
            # Check bool BEFORE int (bool is subclass of int in Python)
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "str"
        else:
            raise TypeCheckError(f"Unknown constant type: {type(value).__name__}")

    def visit_variable(self, node: Variable) -> str:
        """Look up variable type in schema.

        Args:
            node: Variable AST node

        Returns:
            Type from schema

        Raises:
            TypeCheckError: If variable not in schema
        """
        raise NotImplementedError("visit_variable not yet implemented")

    def visit_path_access(self, node: PathAccess) -> str:
        """Look up path type in schema.

        Args:
            node: PathAccess AST node

        Returns:
            Type from schema

        Raises:
            TypeCheckError: If path not in schema
        """
        raise NotImplementedError("visit_path_access not yet implemented")

    def visit_binary_op(self, node: BinaryOp) -> str:
        """Type check binary operation.

        Args:
            node: BinaryOp AST node

        Returns:
            Result type based on operand types and operator

        Raises:
            TypeCheckError: If operand types incompatible with operator

        Rules:
            - Arithmetic (+, -, *, /, %, **): numeric × numeric → numeric
            - Comparison (==, !=, <, >, <=, >=): numeric × numeric → bool
            - Logical (and, or): bool × bool → bool
        """
        from townlet.world.expression.ast_nodes import OperatorType

        left_type = node.left.accept(self)
        right_type = node.right.accept(self)

        # Helper to check if type is numeric (int or float)
        def is_numeric(t: str) -> bool:
            return t in ("int", "float")

        # Arithmetic operators
        if node.op in {
            OperatorType.ADD,
            OperatorType.SUB,
            OperatorType.MUL,
            OperatorType.DIV,
            OperatorType.MOD,
            OperatorType.POW,
        }:
            if not is_numeric(left_type) or not is_numeric(right_type):
                raise TypeCheckError(
                    f"Arithmetic operator {node.op.value} requires numeric operands, got incompatible types {left_type} and {right_type}"
                )
            # Type promotion: if either is float, result is float
            if left_type == "float" or right_type == "float":
                return "float"
            return "int"

        # Comparison operators
        elif node.op in {
            OperatorType.EQ,
            OperatorType.NEQ,
            OperatorType.LT,
            OperatorType.GT,
            OperatorType.LTE,
            OperatorType.GTE,
        }:
            if not is_numeric(left_type) or not is_numeric(right_type):
                raise TypeCheckError(
                    f"Comparison operator {node.op.value} requires numeric operands, got incompatible types {left_type} and {right_type}"
                )
            return "bool"

        # Logical operators
        elif node.op in {OperatorType.AND, OperatorType.OR}:
            if left_type != "bool" or right_type != "bool":
                raise TypeCheckError(
                    f"Logical operator {node.op.value} requires bool operands, got incompatible types {left_type} and {right_type}"
                )
            return "bool"

        else:
            raise TypeCheckError(f"Unknown binary operator: {node.op}")

    def visit_unary_op(self, node: UnaryOp) -> str:
        """Type check unary operation.

        Args:
            node: UnaryOp AST node

        Returns:
            Result type based on operand type and operator

        Raises:
            TypeCheckError: If operand type incompatible with operator

        Rules:
            - Negation (-): numeric → numeric
            - Logical not (not): bool → bool
        """
        from townlet.world.expression.ast_nodes import OperatorType

        operand_type = node.operand.accept(self)

        # Helper to check if type is numeric (int or float)
        def is_numeric(t: str) -> bool:
            return t in ("int", "float")

        if node.op == OperatorType.SUB:  # Negation
            if not is_numeric(operand_type):
                raise TypeCheckError(f"Unary negation requires scalar operand, got {operand_type}")
            return operand_type

        elif node.op == OperatorType.NOT:
            if operand_type != "bool":
                raise TypeCheckError(f"Logical not requires bool operand, got {operand_type}")
            return "bool"

        else:
            raise TypeCheckError(f"Unknown unary operator: {node.op}")

    def visit_function_call(self, node: FunctionCall) -> str:
        """Type check function call.

        Args:
            node: FunctionCall AST node

        Returns:
            Return type from function signature

        Raises:
            TypeCheckError: If function unknown or argument types don't match signature
        """
        raise NotImplementedError("visit_function_call not yet implemented")

    def visit_if_then_else(self, node: IfThenElse) -> str:
        """Type check conditional expression.

        Args:
            node: IfThenElse AST node

        Returns:
            Unified type of true and false branches

        Raises:
            TypeCheckError: If condition not bool or branches have incompatible types
        """
        raise NotImplementedError("visit_if_then_else not yet implemented")

    def visit_index_access(self, node: IndexAccess) -> str:
        """Type check index access.

        Args:
            node: IndexAccess AST node

        Returns:
            Element type from container type

        Raises:
            TypeCheckError: If base not indexable or index not int
        """
        raise NotImplementedError("visit_index_access not yet implemented")
