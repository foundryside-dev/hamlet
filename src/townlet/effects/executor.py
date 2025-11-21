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
        elif command.type == CommandType.SPAWN_ITEM:
            self._execute_spawn_item(command, context)
        elif command.type == CommandType.IF:
            self._execute_if(command, context)
        elif command.type == CommandType.FOR_EACH:
            self._execute_for_each(command, context)
        elif command.type == CommandType.SWITCH:
            self._execute_switch(command, context)
        elif command.type == CommandType.REDUCE:
            self._execute_reduce(command, context)
        elif command.type == CommandType.PARALLEL:
            self._execute_parallel(command, context)
        elif command.type == CommandType.DELAY:
            self._execute_delay(command, context)
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

        # Resolve target index (evaluate expression if needed)
        target_value: str | int | None = command.target
        if target_value is None and command.target_ast is not None:
            eval_ctx = self._make_eval_context(context, effect=context.effect)
            evaluator = Evaluator(eval_ctx)
            evaluated = evaluator.evaluate(command.target_ast)
            if evaluated.numel() != 1:
                raise ValueError("spawn_effect target expression must resolve to a scalar index")
            target_value = int(evaluated.item())

        if target_value == "self":
            if context.self_index is None:
                raise ValueError("self_index not set - cannot use 'self' target")
            target_idx = context.self_index
        elif target_value == "target":
            if context.target_index is None:
                raise ValueError("target_index not set - cannot use 'target' target")
            target_idx = context.target_index
        elif isinstance(target_value, int):
            target_idx = target_value
        else:
            raise ValueError(f"Invalid target: {target_value}")

        # Spawn effect via EffectManager
        # Note: scope hardcoded to AGENT for now (can extend later)
        from townlet.config.effects_config import EffectScope

        if command.effect_id is None:
            raise ValueError("spawn_effect command requires 'effect_id'")

        effect_def = context.effect_manager.catalog.get(command.effect_id)
        resolved_duration = command.duration if command.duration is not None else effect_def.duration

        context.effect_manager.spawn_effect(
            effect_id=command.effect_id,
            target_entity_id=target_idx,
            scope=EffectScope.AGENT,
            duration=resolved_duration,
            intensity=command.intensity or 1.0,
            current_step=context.effect_manager.current_step,
            bars=context.bars,
            vfs_registry=context.vfs_registry,
            spawn_depth=context.spawn_depth,  # manager increments for the spawned effect's on_spawn
            agent_positions=getattr(context, "agent_positions", None),
            item_manager=context.item_manager,
        )

    def _execute_spawn_item(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute spawn_item command.

        Args:
            command: Spawn item command node
            context: Execution context

        Raises:
            ValueError: If item_manager not available or invalid position
        """
        if context.item_manager is None:
            raise ValueError("item_manager not set in context - cannot spawn items")

        # Resolve position using ItemManager helper (fail-forward on unsupported)
        raw_position = command.position
        origin = None
        explicit_coords = None
        strategy: str | tuple | list | None = raw_position

        if raw_position == "self":
            if context.agent_positions is None or context.self_index is None:
                raise ValueError("agent_positions and self_index required for position 'self'")
            origin = tuple(context.agent_positions[context.self_index].tolist())
            strategy = "self"
        elif raw_position == "target":
            if context.agent_positions is None or context.target_index is None:
                raise ValueError("agent_positions and target_index required for position 'target'")
            origin = tuple(context.agent_positions[context.target_index].tolist())
            strategy = "target"
        elif raw_position == "random":
            if context.agent_positions is None or context.self_index is None:
                raise ValueError("agent_positions and self_index required for position 'random'")
            origin = tuple(context.agent_positions[context.self_index].tolist())
            strategy = "random"
        elif isinstance(raw_position, (list, tuple)):
            explicit_coords = tuple(raw_position)
            strategy = "explicit"
        else:
            raise ValueError(f"Invalid position: {command.position}")

        if strategy is None:
            raise ValueError("spawn_item position strategy could not be resolved")

        item_type = command.item_type
        if item_type is None:
            raise ValueError("spawn_item command requires 'item_type'")

        quantity = command.quantity or 1

        for _ in range(quantity):
            position = context.item_manager.find_spawn_location(
                strategy=strategy,
                origin=origin,
                explicit=explicit_coords,
            )
            context.item_manager.spawn_item(
                item_type=item_type,
                position=position,
                current_tick=context.current_tick,
                initial_state=command.initial_state,
            )
        return

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
        """Execute for_each command.

        Args:
            command: For each command node with collection, iterator, body
            context: Execution context
        """
        from townlet.effects.collections import MAX_COLLECTION_SIZE, resolve_collection

        # Resolve collection to list of indices
        collection_type = command.collection
        if not collection_type:
            raise ValueError("for_each command missing collection field")

        indices = resolve_collection(
            collection_type=collection_type,
            context=context,
            radius=command.radius,
            max_count=MAX_COLLECTION_SIZE,
        )

        if len(indices) > MAX_COLLECTION_SIZE:
            raise RuntimeError(f"for_each collection size {len(indices)} exceeds cap {MAX_COLLECTION_SIZE}")

        # Execute body commands for each index
        for idx in indices:
            target_idx = idx
            target_is_item = collection_type == "inventory_items"
            # For inventory_items, map instance_id -> vfs_index if available
            if target_is_item:
                inventory = getattr(context, "inventory", None)
                if inventory is None:
                    raise ValueError("inventory required for 'inventory_items' collection")
                item = inventory.items.get(idx)
                if item is None:
                    raise ValueError(f"Item instance {idx} not found in inventory metadata")
                target_idx = item.vfs_index

            # Create child context with target_index set to current iteration element
            child_context = context.copy(
                target_index=target_idx,  # For items, this is vfs_index
                target_is_item=target_is_item,
                iterator_value=idx,
            )

            # Execute body commands with child context
            body = command.body or []
            for body_cmd in body:
                self.execute(body_cmd, child_context)

    def _execute_switch(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute switch/case (equality-based, first-match wins)."""
        if command.switch_ast is None:
            raise ValueError("SWITCH command missing compiled switch_ast")

        eval_ctx = self._make_eval_context(context, effect=context.effect)
        evaluator = Evaluator(eval_ctx)

        switch_val = evaluator.evaluate(command.switch_ast)

        def _to_scalar_or_tensor(val: Any) -> Any:
            import torch

            if isinstance(val, torch.Tensor):
                return val
            if isinstance(val, (int, float, bool)):
                return torch.tensor(val, device=eval_ctx.device)
            if isinstance(val, str):
                return val
            raise ValueError(f"Unsupported switch value type: {type(val).__name__}")

        switch_eval = _to_scalar_or_tensor(switch_val)

        matched = False
        for when_ast, body in command.case_asts or []:
            when_val = evaluator.evaluate(when_ast)
            when_eval = _to_scalar_or_tensor(when_val)

            if isinstance(switch_eval, str) or isinstance(when_eval, str):
                is_match = switch_eval == when_eval
            else:
                # Assume tensors/scalars; allow broadcasting then any().
                if switch_eval.shape == () and when_eval.shape == ():
                    is_match = bool(switch_eval.item() == when_eval.item())
                else:
                    comp = switch_eval == when_eval
                    is_match = bool(comp.any().item())

            if is_match:
                matched = True
                for cmd in body:
                    self.execute(cmd, context)
                break

        if not matched:
            for cmd in command.default_commands or []:
                self.execute(cmd, context)

    def _execute_reduce(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute reduce over fixed-size collection."""
        if command.collection_ast is None or command.reduce_init_ast is None or command.reduce_body_ast is None:
            raise ValueError("REDUCE command missing compiled ASTs")

        eval_ctx = self._make_eval_context(context, effect=context.effect)
        evaluator = Evaluator(eval_ctx)

        collection_val = evaluator.evaluate(command.collection_ast)
        acc = evaluator.evaluate(command.reduce_init_ast)

        import torch

        # Accept tensor or Python list; enforce fixed-size by cap
        if isinstance(collection_val, list):
            elements = collection_val
        elif isinstance(collection_val, torch.Tensor):
            elements = collection_val
        else:
            raise ValueError("REDUCE collection must evaluate to list or tensor")

        # Cap enforcement
        from townlet.effects.collections import MAX_COLLECTION_SIZE

        length = len(elements) if isinstance(elements, list) else elements.shape[0]
        if length > MAX_COLLECTION_SIZE:
            raise RuntimeError(f"REDUCE collection size {length} exceeds cap {MAX_COLLECTION_SIZE}")

        # Iterate sequentially (fixed-size expectation)
        acc_device = acc.device if hasattr(acc, "device") else None
        for i in range(length):
            iter_val = elements[i] if isinstance(elements, list) else elements[i]

            # Bind iterator and accumulator in a child eval context by shallow copy of dicts
            child_eval_ctx = self._make_eval_context(context, effect=context.effect)
            # Inject iterator and acc into vfs dict for expression resolution
            child_eval_ctx.vfs = dict(child_eval_ctx.vfs)
            if isinstance(iter_val, torch.Tensor):
                child_eval_ctx.vfs[command.reduce_iterator or "iter"] = iter_val
            else:
                # Fall back to tensor on available device, otherwise CPU
                child_eval_ctx.vfs[command.reduce_iterator or "iter"] = (
                    torch.tensor(iter_val, device=acc_device) if acc_device is not None else torch.tensor(iter_val)
                )
            child_eval_ctx.vfs["acc"] = acc
            child_evaluator = Evaluator(child_eval_ctx)
            acc = child_evaluator.evaluate(command.reduce_body_ast)

        # Write back result
        assert command.reduce_target is not None
        context.set_path(command.reduce_target, acc)

    def _execute_parallel(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute branches sequentially (logical parallel) with disjoint writes enforced at compile time."""
        for branch in command.parallel_commands or []:
            self.execute(branch, context)

    def _execute_delay(self, command: CommandNode, context: ExecutionContext) -> None:
        """Enqueue delayed commands via scheduler (if available)."""
        if command.delay_ticks_ast is None:
            raise ValueError("delay command missing compiled ticks AST")

        # Check scheduler availability
        scheduler = getattr(context, "scheduler", None)
        if scheduler is None:
            raise RuntimeError("delay command cannot run without scheduler")

        eval_ctx = self._make_eval_context(context, effect=context.effect)
        evaluator = Evaluator(eval_ctx)
        ticks_val = evaluator.evaluate(command.delay_ticks_ast)

        import torch

        if isinstance(ticks_val, torch.Tensor):
            if ticks_val.numel() != 1:
                raise ValueError("delay ticks expression must resolve to scalar")
            delay_ticks = int(ticks_val.item())
        else:
            delay_ticks = int(ticks_val)

        context_overrides = {
            "self_index": context.self_index,
            "target_index": context.target_index,
            "self_is_item": context.self_is_item,
            "target_is_item": context.target_is_item,
            "spawn_depth": getattr(context, "spawn_depth", 0),
            "effect": context.effect,
        }

        scope = None
        if context.self_index is not None:
            scope = "item" if context.self_is_item else "agent"
        elif context.effect is not None and getattr(context.effect, "scope", None) is not None:
            eff_scope = getattr(context.effect, "scope")
            scope = eff_scope.value if hasattr(eff_scope, "value") else str(eff_scope)

        scheduler.schedule(
            commands=command.delay_commands or [],
            delay_ticks=delay_ticks,
            scope=scope,
            entity_id=context.self_index,
            context_overrides=context_overrides,
            base_tick=None if context.current_tick is None else context.current_tick,
        )

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
