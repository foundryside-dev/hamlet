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

    def __init__(self, schema: dict[str, str]):
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
        result = node.accept(self)
        return str(result)

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
        if node.name not in self.schema:
            raise TypeCheckError(f"Variable '{node.name}' not found in schema. Available variables: {list(self.schema.keys())}")

        return self.schema[node.name]

    def visit_path_access(self, node: PathAccess) -> str:
        """Look up path type in schema.

        Args:
            node: PathAccess AST node

        Returns:
            Type from schema

        Raises:
            TypeCheckError: If path not in schema
        """
        path_str = ".".join(node.segments)

        # Direct lookup first
        if path_str in self.schema:
            return self.schema[path_str]

        # Handle reference traversal for vfs.*, self.vfs.*, and target.vfs.* roots.
        resolved = self._resolve_reference_path(node.segments)
        if resolved is not None:
            return resolved

        raise TypeCheckError(f"Path '{path_str}' not found in schema. Available paths: {list(self.schema.keys())}")

    def _resolve_reference_path(self, segments: list[str]) -> str | None:
        """Resolve reference traversals recursively from vfs./target.vfs./self.vfs. roots."""
        if len(segments) < 2:
            return None

        # Normalize starting prefix and strip root tokens
        prefix: str | None = None
        remaining = segments
        if remaining[0] in {"target", "self"}:
            if len(remaining) < 3 or remaining[1] != "vfs":
                return None
            prefix = remaining[0]
            remaining = remaining[1:]
        elif remaining[0] != "vfs":
            return None

        def resolve(current_prefix: str | None, segs: list[str]) -> str:
            if len(segs) < 2 or segs[0] != "vfs":
                raise TypeCheckError(f"Invalid reference traversal starting at '{'.'.join(segs)}'")

            ref_name = segs[1]
            key_prefix = f"{current_prefix}." if current_prefix else ""
            key = f"{key_prefix}vfs.{ref_name}"
            ref_type = self.schema.get(key)
            if ref_type is None:
                raise TypeCheckError(f"Reference traversal requires schema entry for '{key}'")

            tail = segs[2:]

            # Reference hop
            if ref_type in {"agent_ref", "item_ref"}:
                if not tail:
                    raise TypeCheckError(f"Reference '{ref_name}' must be followed by '.vfs.<name>' or '.bar.<name>'")
                hop_kind, *rest = tail
                next_prefix = "target" if ref_type == "agent_ref" else "self"

                if hop_kind == "bar":
                    if not rest:
                        raise TypeCheckError("Reference traversal missing bar name")
                    bar_key = f"{next_prefix}.bar.{'.'.join(rest)}"
                    inferred = self.schema.get(bar_key)
                    if inferred is None:
                        raise TypeCheckError(
                            f"Path '{'.'.join(segments)}' not found in schema after reference resolution. Checked '{bar_key}'."
                        )
                    return inferred

                if hop_kind != "vfs":
                    raise TypeCheckError(f"Invalid reference traversal segment '{hop_kind}'. Expected 'vfs' or 'bar' after reference.")

                # Recurse into next reference chain
                return resolve(next_prefix, ["vfs", *rest])

            # Non-reference leaf
            if tail:
                raise TypeCheckError(f"Cannot traverse beyond non-reference variable '{ref_name}' (path '{'.'.join(segments)}').")
            return ref_type

        return resolve(prefix, remaining)

    def _lookup_ref_type(self, prefix: str | None, ref_name: str) -> str | None:
        """Look up ref type from available schema keys."""
        candidate_keys = []
        if prefix:
            candidate_keys.append(f"{prefix}.vfs.{ref_name}")
        for key in (f"vfs.{ref_name}", f"target.vfs.{ref_name}", f"self.vfs.{ref_name}"):
            if key not in candidate_keys:
                candidate_keys.append(key)
        return next((self.schema[key] for key in candidate_keys if key in self.schema), None)

    def _fallback_target_lookup(self, tail: list[str], path_str: str) -> str:
        """Fallback: look up tail as target.vfs.<...> after recursion."""
        target_path = f"target.vfs.{'.'.join(tail[1:])}"
        inferred = self.schema.get(target_path)
        if inferred is None:
            raise TypeCheckError(f"Path '{path_str}' not found in schema after reference resolution. Checked '{target_path}'.")
        return inferred

    def _fallback_item_lookup(self, tail: list[str], path_str: str) -> str:
        """Fallback: look up tail as self.vfs.<...> after recursion for item refs."""
        target_path = f"self.vfs.{'.'.join(tail[1:])}"
        inferred = self.schema.get(target_path)
        if inferred is None:
            raise TypeCheckError(f"Path '{path_str}' not found in schema after reference resolution. Checked '{target_path}'.")
        return inferred

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
            # Type cast for mypy - operand_type is str from visitor
            return str(operand_type)

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
        raise NotImplementedError("Function call type checking deferred to Phase 2 (requires function registry with signatures)")

    def visit_if_then_else(self, node: IfThenElse) -> str:
        """Type check conditional expression.

        Args:
            node: IfThenElse AST node

        Returns:
            Unified type of true and false branches

        Raises:
            TypeCheckError: If condition not bool or branches have incompatible types

        Rules:
            - Condition must be bool
            - True and false branches must have same type
            - Result type is branch type
        """
        # Check condition is bool
        cond_type = node.condition.accept(self)
        if cond_type != "bool":
            raise TypeCheckError(f"If condition must be bool, got {cond_type}")

        # Check both branches
        true_type = node.true_branch.accept(self)
        false_type = node.false_branch.accept(self)

        # Branches must match
        if true_type != false_type:
            raise TypeCheckError(f"If branches must have same type. Got {true_type} (true) and {false_type} (false)")

        # Result type is branch type (type cast for mypy)
        return str(true_type)

    def visit_index_access(self, node: IndexAccess) -> str:
        """Type check index access.

        Args:
            node: IndexAccess AST node

        Returns:
            Element type from container type

        Raises:
            TypeCheckError: If base not indexable or index not int
        """
        raise NotImplementedError("Index access type checking deferred to Phase 4 (requires tensor/array types)")
