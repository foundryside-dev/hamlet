"""Command executor for effect pipelines."""

from __future__ import annotations

from typing import Any

import torch

from townlet.effects.context import ExecutionContext
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.context import ExecutionContext as ExprExecutionContext
from townlet.world.expression.evaluator import Evaluator

# NOTE: No ExpressionParser import - ASTs are pre-compiled by CommandCompiler!

__all__ = ["CommandExecutor"]


class _TargetAwareExecutionContext(ExprExecutionContext):
    """Execution context that supports target. and self. prefix resolution.

    This wrapper extends ExprExecutionContext to handle target.bar.*, target.vfs.*,
    self.bar.*, and self.vfs.* paths by delegating to pre-indexed dictionaries.
    """

    def __init__(
        self,
        bars: dict[str, torch.Tensor],
        vfs: dict[str, torch.Tensor],
        target_bars: dict[str, torch.Tensor],
        target_vfs: dict[str, torch.Tensor],
        self_bars: dict[str, torch.Tensor] | None = None,  # NEW
        self_vfs: dict[str, torch.Tensor] | None = None,  # NEW
        vfs_registry: Any | None = None,  # NEW: For item-scoped VFS lookups
        self_index: int | None = None,  # NEW
        self_is_item: bool = False,  # NEW
    ):
        super().__init__(bars=bars, vfs=vfs, affordances={}, temporal={})
        self.target_bars = target_bars
        self.target_vfs = target_vfs
        self.self_bars = self_bars or {}  # NEW
        self.self_vfs = self_vfs or {}  # NEW
        self.vfs_registry = vfs_registry  # NEW
        self.self_index = self_index  # NEW
        self.self_is_item = self_is_item  # NEW

    def get(self, path: str) -> torch.Tensor:
        """Resolve dotted path with target. and self. prefix support.

        Args:
            path: Dotted path like "bar.energy", "target.bar.energy", or "self.vfs.durability"

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

        # NEW: Handle self. prefix
        if parts[0] == "self":
            # Special handling for self.vfs.* when self is an item
            if parts[1] == "vfs" and len(parts) >= 3 and self.self_is_item:
                import torch

                from townlet.vfs.schema import VariableScope

                var_name = ".".join(parts[2:])
                if self.vfs_registry is None or self.self_index is None:
                    raise ValueError("VFS registry or self_index not set for item-scoped VFS lookup")
                value = self.vfs_registry.read(
                    var_name,
                    context_index=self.self_index,
                    scope=VariableScope.ITEM,
                )
                # Convert to tensor if needed
                if not isinstance(value, torch.Tensor):
                    value = torch.tensor(value, dtype=torch.float32)
                return value
            elif parts[1] == "bar" and len(parts) == 3:
                return self.self_bars[parts[2]]
            elif parts[1] == "vfs" and len(parts) >= 3:
                return self.self_vfs[".".join(parts[2:])]
            else:
                raise KeyError(f"Self path '{path}' not found in execution context")

        # Delegate to parent for non-target/non-self paths
        return super().get(path)


class CommandExecutor:
    """Execute effect commands against runtime context.

    IMPORTANT: Commands contain pre-compiled ASTs (from CommandCompiler).
    This executor NEVER parses expressions - it only evaluates pre-compiled ASTs.
    """

    def __init__(self) -> None:
        # No parser needed! ASTs are pre-compiled
        pass

    def execute(self, command: CommandNode, context: ExecutionContext) -> None:
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

    def _execute_modify(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute modify command.

        Args:
            command: Modify command node with pre-compiled value_ast
            context: Execution context
        """
        # ✅ PERF FIX: Use pre-compiled AST directly (NO parsing at runtime!)
        value_ast = command.value_ast
        assert command.path is not None, "MODIFY command must have path"

        # Create evaluation context from execution context
        eval_ctx = self._make_eval_context(context, effect=context.effect)

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

    def _execute_spawn_effect(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute spawn_effect command.

        Args:
            command: Spawn effect command node
            context: Execution context

        Raises:
            ValueError: If effect_manager not available or cascade depth exceeded
        """
        if context.effect_manager is None:
            raise ValueError("effect_manager not set in context - cannot spawn effects")

        # Check cascade depth limit
        max_cascade_depth = 10
        if context.spawn_depth >= max_cascade_depth:
            raise RuntimeError(f"Effect cascade depth limit exceeded ({max_cascade_depth}). Check for infinite spawn loops.")

        # Resolve target index
        if command.target == "self":
            if context.self_index is None:
                raise ValueError("self_index not set - cannot use 'self' target")
            target_idx = context.self_index
        elif command.target == "target":
            if context.target_index is None:
                raise ValueError("target_index not set - cannot use 'target' target")
            target_idx = context.target_index
        elif isinstance(command.target, int):
            target_idx = command.target
        else:
            raise ValueError(f"Invalid target: {command.target}")

        # Spawn effect via EffectManager
        # Note: scope hardcoded to AGENT for now (can extend later)
        from townlet.config.effects_config import EffectScope

        spawned = context.effect_manager.spawn_effect(
            effect_id=command.effect_id,
            target_entity_id=target_idx,
            scope=EffectScope.AGENT,
            duration=command.duration or 10,
            intensity=command.intensity or 1.0,
            current_step=context.effect_manager.current_step,
        )

        # Return spawned effect instance ID for potential future use
        return spawned.instance_id

    def _execute_if(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute if command.

        Args:
            command: If command node with pre-compiled condition_ast
            context: Execution context
        """
        # ✅ PERF FIX: Use pre-compiled AST directly (NO parsing at runtime!)
        cond_ast = command.condition_ast
        eval_ctx = self._make_eval_context(context, effect=context.effect)

        # Create evaluator with context and evaluate pre-compiled condition
        evaluator = Evaluator(eval_ctx)
        condition = evaluator.evaluate(cond_ast)

        # Execute then or else branch
        # For vectorized conditions, check if any element is true
        if condition.dim() == 0:
            # Scalar condition
            is_true = condition.item()
        else:
            # Vector condition - check if any element is true
            is_true = condition.any().item()

        if is_true:
            then_commands = command.then_commands or []
            for cmd in then_commands:
                self.execute(cmd, context)
        else:
            else_commands = command.else_commands or []
            for cmd in else_commands:
                self.execute(cmd, context)

    def _execute_for_each(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute for_each command (stub for now).

        Args:
            command: For each command node
            context: Execution context
        """
        # Stub for now - requires iterator support in EvaluationContext
        raise NotImplementedError("for_each not implemented yet")

    def _make_eval_context(self, context: ExecutionContext, effect: Any | None = None) -> ExprExecutionContext:
        """Convert ExecutionContext to ExprExecutionContext.

        Args:
            context: Effect execution context
            effect: Optional ActiveEffect instance (overrides context.effect)

        Returns:
            Expression evaluation context
        """
        # Use effect from parameter or context
        active_effect = effect or context.effect

        # Build dictionaries for ExprExecutionContext
        bars_dict = {}
        vfs_dict = {}

        # Add effect-specific variables (if available)
        if active_effect:
            # Make effect variables available as scalars
            import torch

            device = self.device if hasattr(self, "device") else "cpu"
            vfs_dict["intensity"] = torch.tensor(active_effect.intensity, device=device)
            vfs_dict["elapsed_ticks"] = torch.tensor(active_effect.elapsed_ticks, device=device)
            vfs_dict["duration_remaining"] = torch.tensor(active_effect.duration_remaining, device=device)

        # Add bars
        for bar_name, tensor in context.bars.items():
            bars_dict[bar_name] = tensor

        # Add VFS variables (VariableRegistry API compatibility)
        if context.vfs_registry:
            # VariableRegistry has .variables property with variable definitions
            for var_id, var_def in context.vfs_registry.variables.items():
                try:
                    tensor = context.vfs_registry.get(var_id, reader="engine")
                    vfs_dict[var_id] = tensor
                except KeyError:
                    # Variable not initialized yet, skip
                    pass

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

            # NEW: Create self-scoped bars/vfs if self_index is set
            # BUT: Only do this if self is NOT an item (items don't have bars)
            self_bars = {}
            self_vfs = {}
            if context.self_index is not None and not context.self_is_item:
                # Self is an agent - index into agent-scoped tensors
                for bar_name, tensor in bars_dict.items():
                    if tensor.dim() > 0:
                        self_bars[bar_name] = tensor[context.self_index]
                    else:
                        self_bars[bar_name] = tensor

                for var_name, tensor in vfs_dict.items():
                    if tensor.dim() > 0:
                        self_vfs[var_name] = tensor[context.self_index]
                    else:
                        self_vfs[var_name] = tensor
            # If self is an item, self_bars/self_vfs stay empty
            # Item-scoped VFS lookups are handled directly in _TargetAwareExecutionContext.get()

            # Build a custom get() function that handles target. and self. prefix
            return _TargetAwareExecutionContext(
                bars=bars_dict,
                vfs=vfs_dict,
                target_bars=target_bars,
                target_vfs=target_vfs,
                self_bars=self_bars,  # NEW
                self_vfs=self_vfs,  # NEW
                vfs_registry=context.vfs_registry,  # NEW: For item-scoped lookups
                self_index=context.self_index,  # NEW
                self_is_item=context.self_is_item,  # NEW
            )

        # No target, return standard context
        return ExprExecutionContext(
            bars=bars_dict,
            vfs=vfs_dict,
            affordances={},
            temporal={},
        )

    def execute_commands(self, commands: list[CommandNode], context: ExecutionContext) -> None:
        """Execute list of commands in order.

        Args:
            commands: List of command nodes
            context: Execution context
        """
        for command in commands:
            self.execute(command, context)
