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
        return node.accept(self)  # type: ignore[no-any-return]

    def visit_constant(self, node: Constant) -> torch.Tensor:
        """Convert constant to tensor."""
        if isinstance(node.value, str):
            return node.value  # type: ignore[return-value]
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
            return left + right  # type: ignore[no-any-return]
        elif node.op == OperatorType.SUB:
            return left - right  # type: ignore[no-any-return]
        elif node.op == OperatorType.MUL:
            return left * right  # type: ignore[no-any-return]
        elif node.op == OperatorType.DIV:
            return left / right  # type: ignore[no-any-return]
        elif node.op == OperatorType.MOD:
            return left % right  # type: ignore[no-any-return]
        elif node.op == OperatorType.POW:
            return left**right  # type: ignore[no-any-return]
        elif node.op == OperatorType.EQ:
            return left == right  # type: ignore[no-any-return]
        elif node.op == OperatorType.NEQ:
            return left != right  # type: ignore[no-any-return]
        elif node.op == OperatorType.LT:
            return left < right  # type: ignore[no-any-return]
        elif node.op == OperatorType.GT:
            return left > right  # type: ignore[no-any-return]
        elif node.op == OperatorType.LTE:
            return left <= right  # type: ignore[no-any-return]
        elif node.op == OperatorType.GTE:
            return left >= right  # type: ignore[no-any-return]
        elif node.op == OperatorType.AND:
            return left & right  # type: ignore[no-any-return]
        elif node.op == OperatorType.OR:
            return left | right  # type: ignore[no-any-return]
        else:
            raise ValueError(f"Unknown operator: {node.op}")

    def visit_unary_op(self, node: UnaryOp) -> torch.Tensor:
        """Execute unary operations on tensors."""
        from townlet.world.expression.ast_nodes import OperatorType

        operand = node.operand.accept(self)

        if node.op == OperatorType.SUB:
            return -operand  # type: ignore[no-any-return]
        elif node.op == OperatorType.NOT:
            return ~operand  # type: ignore[no-any-return]
        else:
            raise ValueError(f"Unknown unary operator: {node.op}")

    def visit_function_call(self, node: FunctionCall) -> torch.Tensor:
        """Execute function calls.

        Uses shared registry to keep signatures and implementations aligned with the type checker.
        """
        from townlet.world.expression.functions import FUNCTION_SPECS

        args = [arg.accept(self) for arg in node.arguments]
        spec = FUNCTION_SPECS.get(node.function_name)
        if spec is None:
            raise NotImplementedError(f"Function '{node.function_name}' not implemented.")

        return spec.eval_fn(args, self.context, node.arguments)

    def visit_if_then_else(self, node: IfThenElse) -> torch.Tensor:
        """Execute vectorized conditional logic using torch.where().

        Evaluates condition, true_branch, and false_branch as tensors,
        then uses torch.where() to select elements from true/false branches
        based on the condition tensor.

        This enables GPU-native conditional logic without Python branching.

        Example:
            if bar.energy < 0.2 then 1 else 0
            - energy = [0.1, 0.5, 0.9]
            - condition = [True, False, False]
            - result = [1, 0, 0]
        """
        condition = node.condition.accept(self)
        true_branch = node.true_branch.accept(self)
        false_branch = node.false_branch.accept(self)

        return torch.where(condition, true_branch, false_branch)  # type: ignore[no-any-return]

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
        return base[index_long]  # type: ignore[no-any-return]
