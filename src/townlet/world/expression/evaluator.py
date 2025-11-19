"""Expression evaluator - executes AST on GPU tensors."""

import torch

from townlet.world.expression.ast_nodes import (
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
from townlet.world.expression.context import ExecutionContext


class Evaluator(ASTVisitor):
    """Evaluates expressions to tensor values."""

    def __init__(self, context: ExecutionContext):
        self.context = context

    def evaluate(self, node) -> torch.Tensor:
        """Evaluate AST node to tensor."""
        return node.accept(self)

    def visit_constant(self, node: Constant) -> torch.Tensor:
        """Convert constant to tensor."""
        return torch.tensor(node.value, device=self.context.device)

    def visit_variable(self, node: Variable) -> torch.Tensor:
        """Resolve variable from context."""
        return self.context.get(node.name)

    def visit_path_access(self, node: PathAccess) -> torch.Tensor:
        """Resolve path from execution context."""
        path_str = ".".join(node.segments)
        return self.context.get(path_str)

    def visit_binary_op(self, node: BinaryOp) -> torch.Tensor:
        """Execute binary operations on tensors."""
        from townlet.world.expression.ast_nodes import OperatorType

        left = node.left.accept(self)
        right = node.right.accept(self)

        if node.op == OperatorType.ADD:
            return left + right
        elif node.op == OperatorType.SUB:
            return left - right
        elif node.op == OperatorType.MUL:
            return left * right
        elif node.op == OperatorType.DIV:
            return left / right
        elif node.op == OperatorType.MOD:
            return left % right
        elif node.op == OperatorType.POW:
            return left**right
        elif node.op == OperatorType.EQ:
            return left == right
        elif node.op == OperatorType.NEQ:
            return left != right
        elif node.op == OperatorType.LT:
            return left < right
        elif node.op == OperatorType.GT:
            return left > right
        elif node.op == OperatorType.LTE:
            return left <= right
        elif node.op == OperatorType.GTE:
            return left >= right
        elif node.op == OperatorType.AND:
            return left & right
        elif node.op == OperatorType.OR:
            return left | right
        else:
            raise ValueError(f"Unknown operator: {node.op}")

    def visit_unary_op(self, node: UnaryOp) -> torch.Tensor:
        """Execute unary operations on tensors."""
        from townlet.world.expression.ast_nodes import OperatorType

        operand = node.operand.accept(self)

        if node.op == OperatorType.SUB:
            return -operand
        elif node.op == OperatorType.NOT:
            return ~operand
        else:
            raise ValueError(f"Unknown unary operator: {node.op}")

    def visit_function_call(self, node: FunctionCall) -> torch.Tensor:
        """Execute function calls.

        Supports basic math functions:
        - max(a, b): element-wise maximum
        - min(a, b): element-wise minimum
        - abs(x): absolute value
        - clamp(x, min, max): clamp to range

        Phase 2 will add domain-specific functions (distance_to_affordance, etc.)
        """
        # Recursively evaluate all arguments
        args = [arg.accept(self) for arg in node.arguments]

        # Built-in math functions
        if node.function_name == "max":
            if len(args) != 2:
                raise ValueError(f"max() requires 2 arguments, got {len(args)}")
            return torch.max(args[0], args[1])
        elif node.function_name == "min":
            if len(args) != 2:
                raise ValueError(f"min() requires 2 arguments, got {len(args)}")
            return torch.min(args[0], args[1])
        elif node.function_name == "abs":
            if len(args) != 1:
                raise ValueError(f"abs() requires 1 argument, got {len(args)}")
            return torch.abs(args[0])
        elif node.function_name == "clamp":
            if len(args) != 3:
                raise ValueError(f"clamp() requires 3 arguments, got {len(args)}")
            return torch.clamp(args[0], min=args[1], max=args[2])
        else:
            raise NotImplementedError(
                f"Function '{node.function_name}' not implemented. "
                "Domain-specific functions (distance_to_affordance, etc.) "
                "will be added in Phase 2."
            )

    def visit_if_then_else(self, node: IfThenElse) -> torch.Tensor:
        """Execute vectorized conditional logic using torch.where()."""
        raise NotImplementedError("visit_if_then_else not yet implemented")

    def visit_index_access(self, node: IndexAccess) -> torch.Tensor:
        """Execute tensor indexing.

        Supports:
        - inventory[0] -> tensor indexing
        - items[slot_index] -> dynamic indexing
        - grid[x][y] -> multi-dimensional via nesting
        """
        base = node.base.accept(self)
        index = node.index.accept(self)

        # Convert index to long tensor for indexing
        index_long = index.long()

        # Tensor indexing
        return base[index_long]
