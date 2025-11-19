"""Command executor for effect pipelines."""

from __future__ import annotations

import torch

from townlet.effects.context import ExecutionContext
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.context import ExecutionContext as ExprExecutionContext
from townlet.world.expression.evaluator import Evaluator

# NOTE: No ExpressionParser import - ASTs are pre-compiled by CommandCompiler!

__all__ = ["CommandExecutor"]


class _TargetAwareExecutionContext(ExprExecutionContext):
    """Execution context that supports target. prefix resolution.

    This wrapper extends ExprExecutionContext to handle target.bar.* and target.vfs.*
    paths by delegating to pre-indexed target-scoped dictionaries.
    """

    def __init__(
        self,
        bars: dict[str, torch.Tensor],
        vfs: dict[str, torch.Tensor],
        target_bars: dict[str, torch.Tensor],
        target_vfs: dict[str, torch.Tensor],
    ):
        super().__init__(bars=bars, vfs=vfs, affordances={}, temporal={})
        self.target_bars = target_bars
        self.target_vfs = target_vfs

    def get(self, path: str) -> torch.Tensor:
        """Resolve dotted path with target. prefix support.

        Args:
            path: Dotted path like "bar.energy" or "target.bar.energy"

        Returns:
            Tensor value from context

        Raises:
            KeyError: If path not found
        """
        parts = path.split(".")

        # Handle target. prefix
        if parts[0] == "target":
            if parts[1] == "bar" and len(parts) == 3:
                return self.target_bars[parts[2]]
            elif parts[1] == "vfs" and len(parts) >= 3:
                return self.target_vfs[".".join(parts[2:])]
            else:
                raise KeyError(f"Target path '{path}' not found in execution context")

        # Delegate to parent for non-target paths
        return super().get(path)


class CommandExecutor:
    """Execute effect commands against runtime context.

    IMPORTANT: Commands contain pre-compiled ASTs (from CommandCompiler).
    This executor NEVER parses expressions - it only evaluates pre-compiled ASTs.
    """

    def __init__(self):
        # No parser needed! ASTs are pre-compiled
        pass

    def execute(self, command: CommandNode, context: ExecutionContext):
        """Execute single command.

        Args:
            command: CommandNode with pre-compiled ASTs
            context: Runtime execution context

        Raises:
            NotImplementedError: For unimplemented command types
        """
        if command.type == CommandType.MODIFY:
            self._execute_modify(command, context)
        elif command.type == CommandType.SPAWN_EFFECT:
            self._execute_spawn_effect(command, context)
        elif command.type == CommandType.IF:
            self._execute_if(command, context)
        elif command.type == CommandType.FOR_EACH:
            self._execute_for_each(command, context)
        else:
            raise NotImplementedError(f"Command type {command.type} not implemented")

    def _execute_modify(self, command: CommandNode, context: ExecutionContext):
        """Execute modify command.

        Args:
            command: Modify command node with pre-compiled value_ast
            context: Execution context
        """
        # ✅ PERF FIX: Use pre-compiled AST directly (NO parsing at runtime!)
        value_ast = command.value_ast

        # Create evaluation context from execution context
        eval_ctx = self._make_eval_context(context)

        # Create evaluator with context and evaluate pre-compiled expression
        evaluator = Evaluator(eval_ctx)
        result = evaluator.evaluate(value_ast)

        # Get the original value to check shape
        original = context.get_path(command.path)

        # Broadcast scalar to match original shape if needed
        if result.dim() == 0 and original.dim() > 0:
            result = result.expand_as(original)

        # Set path to result
        context.set_path(command.path, result)

    def _execute_spawn_effect(self, command: CommandNode, context: ExecutionContext):
        """Execute spawn_effect command (stub for now).

        Args:
            command: Spawn effect command node
            context: Execution context
        """
        # Stub for Task 3.4 (EffectManager integration)
        pass

    def _execute_if(self, command: CommandNode, context: ExecutionContext):
        """Execute if command.

        Args:
            command: If command node with pre-compiled condition_ast
            context: Execution context
        """
        # ✅ PERF FIX: Use pre-compiled AST directly (NO parsing at runtime!)
        cond_ast = command.condition_ast
        eval_ctx = self._make_eval_context(context)

        # Create evaluator with context and evaluate pre-compiled condition
        evaluator = Evaluator(eval_ctx)
        condition = evaluator.evaluate(cond_ast)

        # Execute then or else branch
        if condition.item():  # Convert to Python bool
            for cmd in command.then_commands:
                self.execute(cmd, context)
        else:
            for cmd in command.else_commands:
                self.execute(cmd, context)

    def _execute_for_each(self, command: CommandNode, context: ExecutionContext):
        """Execute for_each command (stub for now).

        Args:
            command: For each command node
            context: Execution context
        """
        # Stub for now - requires iterator support in EvaluationContext
        raise NotImplementedError("for_each not implemented yet")

    def _make_eval_context(self, context: ExecutionContext) -> ExprExecutionContext:
        """Convert ExecutionContext to ExprExecutionContext.

        Args:
            context: Effect execution context

        Returns:
            Expression evaluation context
        """
        # Build dictionaries for ExprExecutionContext
        bars_dict = {}
        vfs_dict = {}

        # Add bars
        for bar_name, tensor in context.bars.items():
            bars_dict[bar_name] = tensor

        # Add VFS globals and agent variables
        if context.vfs_registry:
            for var_name in context.vfs_registry.list_global():
                tensor = context.vfs_registry.get_global(var_name)
                vfs_dict[var_name] = tensor

            for var_name in context.vfs_registry.list_agent():
                tensor = context.vfs_registry.get_agent(var_name)
                vfs_dict[var_name] = tensor

        # Handle target. prefix by creating a modified version of bars/vfs for target
        if context.target_index is not None:
            # Create target-scoped bars
            target_bars = {}
            for bar_name, tensor in bars_dict.items():
                if tensor.dim() > 0:
                    target_bars[bar_name] = tensor[context.target_index]
                else:
                    target_bars[bar_name] = tensor

            # Create target-scoped vfs
            target_vfs = {}
            for var_name, tensor in vfs_dict.items():
                if tensor.dim() > 0:
                    target_vfs[var_name] = tensor[context.target_index]
                else:
                    target_vfs[var_name] = tensor

            # Build a custom get() function that handles target. prefix
            # For now, we'll use a wrapper approach
            return _TargetAwareExecutionContext(
                bars=bars_dict,
                vfs=vfs_dict,
                target_bars=target_bars,
                target_vfs=target_vfs,
            )

        # No target, return standard context
        return ExprExecutionContext(
            bars=bars_dict,
            vfs=vfs_dict,
            affordances={},
            temporal={},
        )

    def execute_commands(self, commands: list[CommandNode], context: ExecutionContext):
        """Execute list of commands in order.

        Args:
            commands: List of command nodes
            context: Execution context
        """
        for command in commands:
            self.execute(command, context)
