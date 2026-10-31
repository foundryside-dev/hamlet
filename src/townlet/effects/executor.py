"""Command executor for effect pipelines."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import torch

from townlet.config.effects_config import EffectScope
from townlet.effects.context import ExecutionContext
from townlet.effects.schema import CommandNode, CommandType
from townlet.vfs.schema import VariableScope
from townlet.world.expression.context import ExecutionContext as ExprExecutionContext
from townlet.world.expression.evaluator import Evaluator

# NOTE: No ExpressionParser import - ASTs are pre-compiled by CommandCompiler!

MAX_CASCADE_DEPTH = 10

__all__ = ["CommandExecutor", "MAX_CASCADE_DEPTH"]


def _as_condition(value: torch.Tensor, keyword: str) -> torch.Tensor:
    """A command condition is a scalar or one bool per agent; nothing else."""
    if value.dim() > 1:
        raise ValueError(f"'{keyword}' condition must be a scalar or one value per agent, got shape {tuple(value.shape)}")
    return value.to(torch.bool)


def _restrict(parent: torch.Tensor | None, condition: torch.Tensor) -> tuple[bool, torch.Tensor | None]:
    """Narrow the live set `parent` (None: every agent) by `condition`.

    Returns (any agent live, mask). A scalar condition keeps the parent mask: it is
    the degenerate per-agent mask that holds for everyone or for no one.
    """
    if condition.dim() == 0:
        return bool(condition.item()), parent
    mask = condition if parent is None else parent & condition
    return bool(mask.any().item()), mask


def _switch_operand(value: Any, device: torch.device) -> torch.Tensor | str:
    if isinstance(value, torch.Tensor):
        return value
    if isinstance(value, (int, float, bool)):
        return torch.tensor(value, device=device)
    if isinstance(value, str):
        return value
    raise ValueError(f"Unsupported switch value type: {type(value).__name__}")


def _check_bars_materialised(bars: dict[str, torch.Tensor], before: dict[str, torch.Tensor]) -> None:
    """Every bar is still the tensor it was and carries no broadcast stride.

    A command writes into a bar in place; one that rebinds the bar (to an expanded
    view, in review-2026-10-24 effects F1) would make the next per-agent write land on
    every agent. Checked after every command so a view can never survive one.
    """
    for name, tensor in bars.items():
        if name in before and tensor is not before[name]:
            raise RuntimeError(f"Bar '{name}' was rebound by a command; writes must copy into the existing tensor")
        if any(stride == 0 and size > 1 for stride, size in zip(tensor.stride(), tensor.shape, strict=True)):
            raise RuntimeError(f"Bar '{name}' is a broadcast view (stride {tuple(tensor.stride())}); a bar must own its rows")


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
        self._preflight_command(command, context)
        bars_before = dict(context.bars)
        self._dispatch(command, context)
        _check_bars_materialised(context.bars, bars_before)

    def _dispatch(self, command: CommandNode, context: ExecutionContext) -> None:
        if command.type == CommandType.MODIFY:
            self._execute_modify(command, context)
        elif command.type == CommandType.SPAWN_EFFECT:
            if command.target_ast is not None:
                from townlet.effects.admission import permission_denial_rng

                with permission_denial_rng():
                    self._execute_spawn_effect(command, context)
            else:
                self._execute_spawn_effect(command, context)
        elif command.type == CommandType.SPAWN_ITEM:
            self._execute_spawn_item(command, context)
        elif command.type == CommandType.SAMPLE:
            self._execute_sample(command, context)
        elif command.type == CommandType.IF:
            self._execute_if(command, context)
        elif command.type == CommandType.FOR_EACH:
            self._execute_for_each(command, context)
        elif command.type == CommandType.SWITCH:
            self._execute_switch(command, context)
        elif command.type == CommandType.PARALLEL:
            self._execute_parallel(command, context)
        elif command.type == CommandType.DELAY:
            self._execute_delay(command, context)
        else:
            raise NotImplementedError(f"Command type {command.type} not implemented")

    def preflight_commands(self, commands: Sequence[CommandNode], context: ExecutionContext) -> None:
        """Authorize a lifecycle pipeline without evaluating expressions or mutating state."""
        for command in commands:
            self._preflight_command(command, context)

    def _preflight_command(self, command: CommandNode, context: ExecutionContext) -> None:
        """Authorize compound command targets before this command mutates state.

        Constructed conditional branches are conservatively checked just like
        authored branches. Delayed work is checked when it executes, against its
        then-current target. This does not roll back earlier independent commands.
        """
        path = None
        if command.type == CommandType.MODIFY:
            path = command.path
        elif command.type == CommandType.SAMPLE:
            path = command.sample_store_path
        if path is not None:
            context.authorize_write_path(path)
        if command.type == CommandType.SPAWN_ITEM and command.initial_state:
            if command.item_type is None:
                raise ValueError("spawn_item overrides require a declared item type")
            if context.item_manager is None:
                raise ValueError("spawn_item overrides require an item manager")
            context.item_manager._authorize_spawn_state(command.item_type, command.initial_state)
        if command.type == CommandType.FOR_EACH:
            if command.collection == "inventory_items":
                children = self._inventory_item_contexts(context)
            else:
                # Ordinary agent roles are independent of the selected row.
                # Do not evaluate a collection expression or resolver while
                # scanning a compound command's possible write policies.
                children = [context.copy(target_index=None, target_is_item=False)]
            for child in children:
                for nested in command.body or []:
                    self._preflight_command(nested, child)
        elif command.type == CommandType.PARALLEL:
            for nested in command.parallel_commands or []:
                self._preflight_command(nested, context)
        elif command.type == CommandType.IF:
            for nested in [*(command.then_commands or []), *(command.else_commands or [])]:
                self._preflight_command(nested, context)
        elif command.type == CommandType.SWITCH:
            for _, branch in command.case_asts or []:
                for nested in branch:
                    self._preflight_command(nested, context)
            for nested in command.default_commands or []:
                self._preflight_command(nested, context)

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
        if context.spawn_depth >= MAX_CASCADE_DEPTH:
            raise RuntimeError(f"Effect cascade depth limit exceeded ({MAX_CASCADE_DEPTH}). Check for infinite spawn loops.")

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

        # Spawn effect via EffectManager using the catalog definition's authoritative scope.
        if command.effect_id is None:
            raise ValueError("spawn_effect command requires 'effect_id'")

        definition = context.effect_manager.catalog.get(command.effect_id)
        if command.intensity is None:
            raise ValueError("spawn_effect command requires intensity")

        # Every effect lives in one world (S1). An agent- or item-scoped effect lives in
        # its entity's world, which must be the spawning world; a global- or
        # affordance-scoped one lives in the spawning world. Under a per-agent condition
        # the spawn is that world's decision. A context bound to no world spawns one
        # global/affordance instance per live world.
        scope = EffectScope(definition.scope)
        world = context.world_row()
        if scope is EffectScope.AGENT or (scope is EffectScope.ITEM and context.vfs_registry is not None):
            from townlet.effects.manager import EffectManager

            entity_world = EffectManager.effect_world(scope, target_idx, world=None, vfs_registry=context.vfs_registry)
            context.require_same_world(f"spawn_effect '{command.effect_id}' target {scope.value} {target_idx}", entity_world)
            worlds = [w for w in (entity_world,) if context.row_is_live(w)]
        elif world is not None:
            worlds = [w for w in (world,) if context.row_is_live(w)]
        else:
            worlds = context.live_worlds(self._num_worlds(context))

        for world in worlds:
            context.effect_manager.spawn_effect(
                effect_id=command.effect_id,
                target_entity_id=target_idx,
                intensity=command.intensity,
                current_step=context.effect_manager.current_step,
                bars=context.bars,
                vfs_registry=context.vfs_registry,
                spawn_depth=context.spawn_depth,  # manager increments for the spawned effect's on_spawn
                agent_positions=context.agent_positions,
                item_manager=context.item_manager,
                affordance_positions=context.affordance_positions,
                substrate=context.substrate,
                world=world,
            )

    @staticmethod
    def _num_worlds(context: ExecutionContext) -> int:
        """The batch's world count (S1: one world per agent row)."""
        if context.vfs_registry is not None:
            return int(context.vfs_registry.num_worlds)
        if context.write_mask is not None:
            return int(context.write_mask.shape[0])
        if context.bars:
            return int(next(iter(context.bars.values())).shape[0])
        raise ValueError("A pipeline bound to no world needs a registry, write mask or bars to know the batch's worlds")

    def _execute_spawn_item(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute spawn_item command.

        Items are per world (S1). A context bound to one world (an agent, an item, any
        effect) spawns into that world when its row is live under the write mask; a
        context bound to no world spawns into every live world.

        Args:
            command: Spawn item command node
            context: Execution context

        Raises:
            ValueError: If item_manager not available or invalid position
        """
        if context.item_manager is None:
            raise ValueError("item_manager not set in context - cannot spawn items")

        item_type = command.item_type
        if item_type is None:
            raise ValueError("spawn_item command requires 'item_type'")
        if command.quantity is None:
            raise ValueError(f"spawn_item '{item_type}' requires a declared quantity")

        # Resolve position using ItemManager helper (fail-forward on unsupported)
        raw_position = command.position
        origin = None
        explicit_coords = None
        strategy: str

        if raw_position in ("self", "random"):
            if context.self_index is None:
                raise ValueError(f"self_index required for position '{raw_position}'")
            origin = self._entity_position(context, context.self_index, is_item=context.self_is_item)
            strategy = str(raw_position)
        elif raw_position == "target":
            if context.target_index is None:
                raise ValueError("target_index required for position 'target'")
            origin = self._entity_position(context, context.target_index, is_item=context.target_is_item)
            strategy = "target"
        elif isinstance(raw_position, (list, tuple)):
            explicit_coords = tuple(raw_position)
            strategy = "explicit"
        else:
            raise ValueError(f"Invalid position: {command.position}")

        for target_world in context.live_worlds(context.item_manager.num_worlds):
            for _ in range(command.quantity):
                position = context.item_manager.find_spawn_location(
                    target_world,
                    strategy=strategy,
                    origin=origin,
                    explicit=explicit_coords,
                )
                context.item_manager.spawn_item(
                    target_world,
                    item_type=item_type,
                    position=position,
                    current_tick=context.current_tick,
                    initial_state=command.initial_state,
                )

    @staticmethod
    def _entity_position(context: ExecutionContext, index: int, *, is_item: bool) -> tuple[Any, ...]:
        """The position of the context's self/target entity: an agent, or an item row.

        A carried item is where its holder is, as its observation token says.
        """
        if is_item:
            assert context.item_manager is not None
            item = context.item_manager.item_at_row(index)
            if item is None:
                raise ValueError(f"No live item holds arena row {index}; it has no position to spawn at")
            holder = context.item_manager.holder_of(item)
            if holder is None:
                return tuple(item.position)
            index = holder
        if context.agent_positions is None:
            raise ValueError("agent_positions required to spawn at an agent's position")
        return tuple(context.agent_positions[index].tolist())

    def _execute_sample(self, command: CommandNode, context: ExecutionContext) -> None:
        """Sample from a distribution and store the result."""
        if command.sample_store_path is None:
            raise ValueError("sample command missing store path")
        dist = (command.sample_distribution or "").lower()
        if not dist:
            raise ValueError("sample command missing distribution")

        eval_ctx = self._make_eval_context(context, effect=context.effect)
        evaluator = Evaluator(eval_ctx)

        # A world's own stream (S1); a context bound to no world seeds one per tick.
        generator = self._random_stream(context, eval_ctx.device)
        if generator is None:
            generator = torch.Generator(device=eval_ctx.device)
            base_seed = context.seed if context.seed is not None else 0
            tick_seed = context.current_tick if context.current_tick is not None else 0
            generator.manual_seed(int(base_seed + tick_seed))
            context.rng = generator

        def _eval_param(value: Any) -> torch.Tensor:
            if isinstance(value, torch.Tensor):
                return value.to(eval_ctx.device)
            if isinstance(value, (int, float, bool)):
                return torch.tensor(value, device=eval_ctx.device)
            raise ValueError(f"Unsupported param value type: {type(value).__name__}")

        def _eval_ast(ast: Any) -> torch.Tensor:
            val = evaluator.evaluate(ast)
            return _eval_param(val)

        target_tensor = context.get_path(command.sample_store_path)
        shape = tuple(target_tensor.shape)

        param_asts = command.sample_param_asts or {}

        if dist == "uniform":
            min_val = _eval_ast(param_asts["min"])
            max_val = _eval_ast(param_asts["max"])
            rand = torch.rand(shape or (), device=eval_ctx.device, generator=generator)
            result = min_val + rand * (max_val - min_val)
        elif dist == "normal":
            mean = _eval_ast(param_asts["mean"])
            std = _eval_ast(param_asts["std"])
            noise = torch.randn(shape or (), device=eval_ctx.device, generator=generator)
            result = mean + std * noise
        elif dist == "lognormal":
            mean = _eval_ast(param_asts["mean"])
            std = _eval_ast(param_asts["std"])
            noise = torch.randn(shape or (), device=eval_ctx.device, generator=generator)
            result = torch.exp(mean + std * noise)
        elif dist == "exponential":
            rate = _eval_ast(param_asts["rate"])
            # Clamp rate to avoid divide-by-zero
            rate = torch.clamp(rate, min=1e-8)
            rand = torch.rand(shape or (), device=eval_ctx.device, generator=generator)
            result = -torch.log(torch.clamp(rand, min=1e-8)) / rate
        elif dist == "bernoulli":
            p_val = _eval_ast(param_asts["p"])
            rand = torch.rand(shape or (), device=eval_ctx.device, generator=generator)
            result = (rand < p_val).to(dtype=target_tensor.dtype if target_tensor.is_floating_point() else torch.bool)
        elif dist == "categorical":
            ast_list = param_asts.get("probs")
            if ast_list is None:
                raise ValueError("categorical sample requires 'probs'")
            prob_tensors = [_eval_ast(ast) for ast in ast_list]
            probs_tensor = torch.stack(prob_tensors).to(eval_ctx.device)
            probs_sum = probs_tensor.sum()
            if probs_sum <= 0:
                raise ValueError("categorical probs must sum to > 0")
            probs_tensor = probs_tensor / probs_sum
            sample_count = int(torch.tensor(shape).prod().item()) if shape else 1
            sampled = torch.multinomial(probs_tensor, num_samples=sample_count, replacement=True, generator=generator)
            result = sampled.reshape(shape) if shape else sampled[0]
            result = result.to(dtype=target_tensor.dtype, device=eval_ctx.device)
        else:
            raise ValueError(f"Unsupported sample distribution '{dist}'")

        # Broadcast scalar results to target shape if needed
        if not shape and target_tensor.dim() > 0:
            result = result.expand_as(target_tensor)

        context.set_path(command.sample_store_path, result)
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
        condition = _as_condition(evaluator.evaluate(cond_ast), "if")

        # Masked execution: each branch runs for the agents its side of the condition
        # holds for, as a write mask on the branch's context. A scalar condition is the
        # degenerate mask (the whole batch, or nobody).
        self._run_branch(command.then_commands or [], context, *_restrict(context.write_mask, condition))
        self._run_branch(command.else_commands or [], context, *_restrict(context.write_mask, ~condition))

    def _run_branch(self, commands: Sequence[CommandNode], context: ExecutionContext, live: bool, mask: torch.Tensor | None) -> None:
        """Run `commands` under `mask`; a branch no agent is live for is skipped.

        The skip is an optimisation, not semantics: every write under an all-false mask
        is a no-op, and spawns gate on the same mask.
        """
        if not live:
            return
        branch_context = context if mask is context.write_mask else context.copy(write_mask=mask)
        for cmd in commands:
            self.execute(cmd, branch_context)

    def _execute_for_each(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute a preauthorized body for each resolved target."""
        children = self._for_each_contexts(command, context)
        # Resolve only when this loop executes, after earlier sibling writes.
        # Authorize all selected bodies before mutating the first selected row.
        for child_context in children:
            for body_cmd in command.body or []:
                self._preflight_command(body_cmd, child_context)
        for child_context in children:
            for body_cmd in command.body or []:
                self.execute(body_cmd, child_context)

    def _inventory_item_contexts(self, context: ExecutionContext) -> list[ExecutionContext]:
        """Inspect current qualified inventory policies without evaluating expressions."""
        inventory = context.inventory
        if inventory is None:
            raise ValueError("inventory required for 'inventory_items' collection")
        if context.self_index is None:
            raise ValueError("self_index required for 'inventory_items' collection")
        contexts = []
        for slot in inventory.slots[context.self_index]:
            instance_id = int(slot.item())
            if instance_id < 0:
                continue
            item = inventory.items.get(instance_id)
            if item is None:
                raise ValueError(f"Item instance {instance_id} not found in inventory metadata")
            contexts.append(context.copy(target_index=item.vfs_index, target_is_item=True, iterator_value=instance_id))
        return contexts

    def _for_each_contexts(self, command: CommandNode, context: ExecutionContext) -> list[ExecutionContext]:
        """Resolve the complete target set without mutating any target."""
        from townlet.effects.collections import MAX_COLLECTION_SIZE, resolve_collection

        # Resolve collection to list of indices (resolver or expression)
        indices = []
        collection_type = command.collection
        if collection_type:
            indices = resolve_collection(
                collection_type=collection_type,
                context=context,
                max_count=MAX_COLLECTION_SIZE,
            )
        elif command.collection_ast is not None:
            eval_ctx = self._make_eval_context(context, effect=context.effect)
            evaluator = Evaluator(eval_ctx)
            value = evaluator.evaluate(command.collection_ast)
            if isinstance(value, torch.Tensor):
                flat = value.flatten()
                indices = [int(v.item()) for v in flat]
            elif isinstance(value, (list, tuple)):
                indices = [int(v) for v in value]
            else:
                indices = [int(value)]
        else:
            raise ValueError("for_each command missing collection field (resolver or expression required)")

        if len(indices) > MAX_COLLECTION_SIZE:
            raise RuntimeError(f"for_each collection size {len(indices)} exceeds cap {MAX_COLLECTION_SIZE}")

        contexts: list[ExecutionContext] = []
        for idx in indices:
            target_idx = idx
            target_is_item = collection_type == "inventory_items"
            if not target_is_item:
                # An agent element is an agent row; it must live in the pipeline's world.
                context.require_same_world(f"for_each element agent {idx}", idx)
            # For inventory_items, map instance_id -> vfs_index if available
            if target_is_item:
                inventory = context.inventory
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

            contexts.append(child_context)
        return contexts

    def _execute_switch(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute switch/case (equality-based, first-match wins)."""
        if command.switch_ast is None:
            raise ValueError("SWITCH command missing compiled switch_ast")

        eval_ctx = self._make_eval_context(context, effect=context.effect)
        evaluator = Evaluator(eval_ctx)

        switch_eval = _switch_operand(evaluator.evaluate(command.switch_ast), eval_ctx.device)

        # Masked first-match per agent: a case runs for the agents it matches that no
        # earlier case took; the default runs for the agents no case took. A scalar
        # selector is the degenerate mask.
        remaining_live, remaining = True, context.write_mask
        for when_ast, body in command.case_asts or []:
            if not remaining_live:
                break
            when_eval = _switch_operand(evaluator.evaluate(when_ast), eval_ctx.device)
            if isinstance(switch_eval, str) or isinstance(when_eval, str):
                matches = torch.tensor(switch_eval == when_eval, device=eval_ctx.device)
            else:
                matches = _as_condition(switch_eval == when_eval, "switch")
            self._run_branch(body, context, *_restrict(remaining, matches))
            remaining_live, remaining = _restrict(remaining, ~matches)
        self._run_branch(command.default_commands or [], context, remaining_live, remaining)

    def _execute_parallel(self, command: CommandNode, context: ExecutionContext) -> None:
        """Execute branches sequentially (logical parallel) with disjoint writes enforced at compile time."""
        for branch in command.parallel_commands or []:
            self.execute(branch, context)

    def _execute_delay(self, command: CommandNode, context: ExecutionContext) -> None:
        """Enqueue delayed commands via scheduler (if available)."""
        if command.delay_ticks_ast is None:
            raise ValueError("delay command missing compiled ticks AST")

        scheduler = context.scheduler
        if scheduler is None:
            raise RuntimeError("delay command cannot run without scheduler")
        eval_ctx = self._make_eval_context(context, effect=context.effect)
        evaluator = Evaluator(eval_ctx)
        ticks_val = evaluator.evaluate(command.delay_ticks_ast)

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
            "spawn_depth": context.spawn_depth,
            "effect": context.effect,
            # A delayed block runs under the mask that was live when it was scheduled,
            # so an `if` branch that schedules a delay stays per-agent.
            "write_mask": context.write_mask,
        }

        # Delayed work is keyed by the entity that owns it (so an agent's death or an
        # item's despawn cancels it) and, when an effect scheduled it, by that effect
        # instance (so cancelling one effect cancels its own work only).
        scope: str | None = None
        entity_id: Any = context.self_index
        effect_instance: int | None = None
        if context.effect is not None:
            from townlet.effects.manager import EffectManager

            scope, entity_id = EffectManager.schedule_key(context.effect)
            effect_instance = int(context.effect.instance_id)
        elif context.self_index is not None:
            scope = "item" if context.self_is_item else "agent"

        scheduler.schedule(
            commands=command.delay_commands or [],
            delay_ticks=delay_ticks,
            scope=scope,
            entity_id=entity_id,
            context_overrides=context_overrides,
            base_tick=None if context.current_tick is None else context.current_tick,
            effect_instance=effect_instance,
        )

    @staticmethod
    def _random_stream(context: ExecutionContext, device: torch.device) -> torch.Generator | None:
        """The stream this pipeline's randomness draws from: its world's own (S1), if any."""
        if context.rng is not None:
            return context.rng
        from townlet.effects.manager import EffectManager

        world = context.world_row()
        if world is not None and isinstance(context.effect_manager, EffectManager):
            return context.effect_manager.world_rng(world, device)
        return None

    def _make_eval_context(self, context: ExecutionContext, effect: Any | None = None) -> ExprExecutionContext:
        """The expression context of one pipeline step, resolved as ``ExecutionContext.get_path`` resolves.

        Every value is this pipeline's world's (S1): a bare global or affordance variable
        is the world's row, a bare agent variable and ``bar.<m>`` the world's agent's row,
        ``item.<x>`` the bound item's state, and the active effect binds its locals
        (``intensity``, ``elapsed_ticks``, ``duration_remaining``). A context bound to no
        world reads the whole batch.

        Args:
            context: Effect execution context
            effect: Optional ActiveEffect instance (overrides context.effect)
        """
        active_effect = effect if effect is not None else context.effect
        device = next(iter(context.bars.values())).device if context.bars else torch.device("cpu")
        agent_row = context.agent_read_row()
        world_row = context.world_row()

        vfs_dict: dict[str, torch.Tensor] = {}
        bars_dict = {name: ExecutionContext._row(tensor, agent_row) for name, tensor in context.bars.items()}
        if context.vfs_registry:
            for var_id, var_def in context.vfs_registry.variables.items():
                row = agent_row if var_def.scope == VariableScope.AGENT else world_row
                vfs_dict[var_id] = ExecutionContext._row(context.vfs_registry.get(var_id, reader="engine"), row)
        # The locals are reserved names (no variable may take one), bound last.
        if active_effect:
            vfs_dict["intensity"] = torch.tensor(active_effect.intensity, device=device)
            vfs_dict["elapsed_ticks"] = torch.tensor(active_effect.elapsed_ticks, device=device, dtype=torch.float32)
            vfs_dict["duration_remaining"] = torch.tensor(active_effect.duration_remaining, device=device, dtype=torch.float32)

        item_row = context.bound_item()
        item_state = None if item_row is None else context.read_item_state(item_row)

        # Spatial reads evaluate in float32, as the VFS evaluator hands them (grid
        # positions are integer cells; euclidean distance takes a square root).
        # The agent's own position row when the pipeline has a world (S1), so a spatial
        # read is that agent's, like every other read here.
        agent_positions = None
        if context.agent_positions is not None:
            agent_positions = context.agent_positions.to(dtype=torch.float32, device=device)
            if agent_row is not None:
                agent_positions = agent_positions[agent_row : agent_row + 1]
        affordance_positions = (
            None
            if context.affordance_positions is None
            else {name: position.to(dtype=torch.float32, device=device) for name, position in context.affordance_positions.items()}
        )

        return ExprExecutionContext(
            bars=bars_dict,
            vfs=vfs_dict,
            temporal={},
            item_state=item_state,
            device=device,
            agent_positions=agent_positions,
            affordance_positions=affordance_positions,
            rng=self._random_stream(context, device),
        )

    def execute_commands(self, commands: list[CommandNode], context: ExecutionContext) -> None:
        """Execute list of commands in order.

        Args:
            commands: List of command nodes
            context: Execution context
        """
        for command in commands:
            self.execute(command, context)
