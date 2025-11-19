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
        raise NotImplementedError("visit_variable not yet implemented")

    def visit_path_access(self, node: PathAccess) -> torch.Tensor:
        """Resolve path from execution context."""
        raise NotImplementedError("visit_path_access not yet implemented")

    def visit_binary_op(self, node: BinaryOp) -> torch.Tensor:
        """Execute binary operations on tensors."""
        raise NotImplementedError("visit_binary_op not yet implemented")

    def visit_unary_op(self, node: UnaryOp) -> torch.Tensor:
        """Execute unary operations on tensors."""
        raise NotImplementedError("visit_unary_op not yet implemented")

    def visit_function_call(self, node: FunctionCall) -> torch.Tensor:
        """Execute function calls."""
        raise NotImplementedError("visit_function_call not yet implemented")

    def visit_if_then_else(self, node: IfThenElse) -> torch.Tensor:
        """Execute vectorized conditional logic using torch.where()."""
        raise NotImplementedError("visit_if_then_else not yet implemented")

    def visit_index_access(self, node: IndexAccess) -> torch.Tensor:
        """Execute tensor indexing."""
        raise NotImplementedError("visit_index_access not yet implemented")
