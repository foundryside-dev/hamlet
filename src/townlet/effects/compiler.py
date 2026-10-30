"""Command compiler with expression validation."""

from __future__ import annotations

from dataclasses import fields, replace
from typing import Any, Literal

from townlet.config.effects_config import EffectScope
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression import ExpressionParser
from townlet.world.expression.ast_nodes import ASTNode, FunctionCall, PathAccess
from townlet.world.expression.type_checker import TypeChecker

__all__ = ["CommandCompiler"]

# for_each collections whose iteration target is an item row, not an agent row
# (executor `_for_each_contexts`: only inventory_items sets target_is_item).
_ITEM_TARGET_COLLECTIONS = frozenset({"inventory_items"})

# Functions that read a TemporalHistory or the evaluation step. Only the VFS profile
# evaluator keeps a history and a step (`vfs/evaluator.py`); a command pipeline (effect,
# affordance interaction, item interaction) runs without one, so these refuse here
# instead of compiling and raising at the first tick (review-2026-10-24 effects F9).
HISTORY_FUNCTIONS = frozenset({"lag", "delta", "moving_average", "ema", "rate_of_change", "rising_edge", "falling_edge", "elapsed_ticks"})


TargetBinding = Literal["agent", "item", "none"]
"""What `target` names while a command runs: an agent row, an item row, or nothing."""


class CommandCompiler:
    """Compile commands with expression type checking."""

    def __init__(self, schema: dict[str, str], *, agent_target: bool, time_enabled: bool = True):
        """Initialize compiler with type schema.

        Args:
            schema: Type schema for paths (e.g., {"target.bar.energy": "float"})
            time_enabled: Whether temporal mechanics are enabled (gates delay)
            agent_target: Whether the compiled pipeline runs with `target` bound to one
                agent row — true for affordance interactions, item interactions and
                agent-scoped effects; false for global and affordance-scoped effects.
                An item-scoped effect's `target` is the item itself: build its
                compiler with `for_effect_scope`. A bare `vfs.X` naming an agent-scoped variable means that
                agent's row, never the batch: with an agent target it is resolved to
                `target.vfs.X` (reads and writes alike); without one a write to it is
                refused here.
        """
        self.schema = schema
        self.time_enabled = time_enabled
        self.root_binding: TargetBinding = "agent" if agent_target else "none"
        self.parser = ExpressionParser()  # type: ignore[no-untyped-call]
        self.type_checker = TypeChecker(schema=schema)
        # Under an item binding `target` is the item row (ExecutionContext
        # `target_is_item`): `target.vfs.X` names item-profile state, typed like the
        # schema's `self.vfs.X`, and an item has no bars or agent registry row.
        self.item_schema = {key: value for key, value in schema.items() if not key.startswith("target.")}
        self.item_schema.update({f"target.{key[len('self.'):]}": value for key, value in schema.items() if key.startswith("self.vfs.")})
        self.item_type_checker = TypeChecker(schema=self.item_schema)

    @classmethod
    def for_effect_scope(cls, schema: dict[str, str], *, scope: EffectScope, time_enabled: bool) -> CommandCompiler:
        """The compiler for an effect of `scope`, with `target` bound as EffectManager binds it.

        An agent-scoped effect's target is its agent row; an item-scoped effect's target
        is the item itself (`_lifecycle_context` sets `target_is_item`); global and
        affordance effects have no target agent.
        """
        compiler = cls(schema, agent_target=scope == EffectScope.AGENT, time_enabled=time_enabled)
        if scope == EffectScope.ITEM:
            compiler.root_binding = "item"
        return compiler

    def _schema(self, binding: TargetBinding) -> dict[str, str]:
        return self.item_schema if binding == "item" else self.schema

    def _checker(self, binding: TargetBinding) -> TypeChecker:
        return self.item_type_checker if binding == "item" else self.type_checker

    # -- bare `vfs.X` resolution -------------------------------------------------

    def _bare_agent_path(self, path: str) -> bool:
        """True when `path` is a bare `vfs.X` naming an agent-scoped variable.

        `EffectsCompiler.build_schema` registers agent variables under
        both `vfs.X` and `target.vfs.X`, globals under `vfs.X` and `global.vfs.X`, and
        item-profile variables under `self.vfs.X` only — so the `target.` twin is the
        schema's statement that `X` has an agent axis.
        """
        return path.startswith("vfs.") and f"target.{path}" in self.schema

    def _canonical_write_path(self, path: str) -> str:
        """The path a write lands on once bare agent paths are resolved (no refusal)."""
        return f"target.{path}" if self._bare_agent_path(path) else path

    def _resolve_write_path(self, path: str, binding: TargetBinding, what: str) -> str:
        if not self._bare_agent_path(path):
            return path
        if binding != "agent":
            from townlet.world.expression.type_checker import TypeCheckError

            name = path[len("vfs.") :]
            raise TypeCheckError(
                f"{what} '{path}' writes agent-scoped variable '{name}' but this pipeline runs with no interacting "
                f"agent: a bare agent-scoped write is one agent's row, never the batch. Write it as "
                f"'target.{path}' from an agent-scoped effect, an affordance or item interaction, or a for_each "
                "over agents."
            )
        return f"target.{path}"

    def _resolve_expression(self, ast: ASTNode, binding: TargetBinding) -> ASTNode:
        """Rewrite bare agent-scoped `vfs.X` references to `target.vfs.X` under an agent target."""
        if binding != "agent":
            return ast
        return _rewrite_ast(ast, self._bare_agent_path)

    def _parse(self, expression: str, binding: TargetBinding) -> ASTNode:
        ast = self.parser.parse(expression)
        _refuse_history_functions(ast, expression)
        return self._resolve_expression(ast, binding)

    def compile_command(self, node: CommandNode) -> CommandNode:
        """Compile and validate command.

        Args:
            node: CommandNode AST

        Returns:
            Validated CommandNode (same instance, after validation and AST compilation)

        Raises:
            TypeCheckError: If path invalid or type mismatch
        """
        return self._compile_command(node, self.root_binding)

    def _compile_command(self, node: CommandNode, binding: TargetBinding) -> CommandNode:
        schema = self._schema(binding)
        type_checker = self._checker(binding)
        if node.type == CommandType.MODIFY:
            # Validate required fields are present
            if node.path is None or node.value_expr is None:
                from townlet.world.expression.type_checker import TypeCheckError

                raise TypeCheckError("MODIFY command requires both 'path' and 'value_expr'")

            node.path = self._resolve_write_path(node.path, binding, "MODIFY target")

            # Validate path exists
            if node.path not in schema:
                from townlet.world.expression.type_checker import TypeCheckError

                raise TypeCheckError(f"Path '{node.path}' not found in schema. Available: {list(schema.keys())}")

            # Parse and type-check value expression
            value_ast = self._parse(node.value_expr, binding)
            value_type = type_checker.check(value_ast)

            # Verify type matches target path
            target_type = schema[node.path]
            if value_type != target_type:
                from townlet.world.expression.type_checker import TypeCheckError

                raise TypeCheckError(f"Type mismatch for path '{node.path}': expected {target_type}, got {value_type}")

            # ✅ PERF FIX: Store compiled AST for runtime use
            node.value_ast = value_ast

        elif node.type == CommandType.SPAWN_EFFECT:
            from townlet.world.expression.type_checker import TypeCheckError

            if node.effect_id is None:
                raise TypeCheckError("SPAWN_EFFECT command requires 'effect_id'")
            if node.target is None and node.target_expr is None:
                raise TypeCheckError("SPAWN_EFFECT command requires 'target'")
            if node.intensity is None:
                raise TypeCheckError("SPAWN_EFFECT command requires 'intensity'")

            # Validate and compile target expression only when not a simple literal
            simple_target = node.target in {"self", "target"} or isinstance(node.target, int)
            if not simple_target and node.target_expr:
                target_ast = self._parse(node.target_expr, binding)
                target_type = type_checker.check(target_ast)
                if target_type != "int":
                    raise TypeCheckError(f"spawn_effect target expression must be int, got {target_type} for '{node.target_expr}'")

                # ✅ Store compiled AST
                node.target_ast = target_ast

        elif node.type == CommandType.SAMPLE:
            from townlet.world.expression.type_checker import TypeCheckError

            dist = (node.sample_distribution or "").lower()
            if not dist:
                raise TypeCheckError("SAMPLE command requires 'sample_distribution'")
            if node.sample_store_path is None:
                raise TypeCheckError("SAMPLE command requires 'sample_store_path'")
            node.sample_store_path = self._resolve_write_path(node.sample_store_path, binding, "SAMPLE store_in")
            if node.sample_store_path not in schema:
                raise TypeCheckError(f"Path '{node.sample_store_path}' not found in schema. Available: {list(schema.keys())}")

            required_params: dict[str, tuple[str, ...]] = {
                "uniform": ("min", "max"),
                "normal": ("mean", "std"),
                "lognormal": ("mean", "std"),
                "exponential": ("rate",),
                "bernoulli": ("p",),
                "categorical": ("probs",),
            }
            if dist not in required_params:
                raise TypeCheckError(f"Unsupported sample distribution '{dist}'")

            params = node.sample_params or {}
            missing = [p for p in required_params[dist] if p not in params]
            if missing:
                raise TypeCheckError(f"SAMPLE '{dist}' missing params: {missing}")

            target_type = schema[node.sample_store_path]
            expected_type = {
                "uniform": "float",
                "normal": "float",
                "lognormal": "float",
                "exponential": "float",
                "bernoulli": "bool",
                "categorical": "int",
            }[dist]

            allowed_target_types = {expected_type}
            if dist == "bernoulli":
                allowed_target_types.add("float")
            if dist == "categorical":
                allowed_target_types.add("float")

            if target_type not in allowed_target_types:
                raise TypeCheckError(f"SAMPLE target '{node.sample_store_path}' expects type {target_type}, got {expected_type}")

            param_asts: dict[str, Any] = {}
            for name, raw_val in params.items():
                if dist == "categorical" and name == "probs":
                    if not isinstance(raw_val, (list, tuple)):
                        raise TypeCheckError("categorical probs must be a list")
                    ast_list = []
                    for idx, prob in enumerate(raw_val):
                        expr = prob if isinstance(prob, str) else str(prob)
                        ast = self._parse(expr, binding)
                        prob_type = type_checker.check(ast)
                        if prob_type not in {"int", "float"}:
                            raise TypeCheckError(f"categorical probs[{idx}] must be numeric, got {prob_type}")
                        ast_list.append(ast)
                    param_asts[name] = ast_list
                    continue

                expr = raw_val if isinstance(raw_val, str) else str(raw_val)
                ast = self._parse(expr, binding)
                arg_type = type_checker.check(ast)
                if arg_type not in {"int", "float"}:
                    raise TypeCheckError(f"SAMPLE param '{name}' must be numeric, got {arg_type}")
                param_asts[name] = ast

            node.sample_param_asts = param_asts

        elif node.type == CommandType.IF:
            # Validate required fields are present
            if node.condition_expr is None:
                from townlet.world.expression.type_checker import TypeCheckError

                raise TypeCheckError("IF command requires 'condition_expr'")

            # Validate condition is boolean
            cond_ast = self._parse(node.condition_expr, binding)
            cond_type = type_checker.check(cond_ast)

            if cond_type != "bool":
                from townlet.world.expression.type_checker import TypeCheckError

                raise TypeCheckError(f"If condition must be bool, got {cond_type}")

            # ✅ Store compiled AST
            node.condition_ast = cond_ast

            # Recursively compile nested commands (with None checks for mypy)
            if node.then_commands is not None:
                for cmd in node.then_commands:
                    self._compile_command(cmd, binding)
            if node.else_commands is not None:
                for cmd in node.else_commands:
                    self._compile_command(cmd, binding)

        elif node.type == CommandType.FOR_EACH:
            # Validate required fields are present
            from townlet.effects.collections import COLLECTION_RESOLVERS
            from townlet.world.expression.type_checker import TypeCheckError

            has_collection = node.collection is not None
            has_collection_expr = node.collection_expr is not None

            if not has_collection and not has_collection_expr:
                raise TypeCheckError("FOR_EACH command requires 'collection'")

            # If an explicit collection expression is provided, parse/type-check it and
            # skip resolver validation. Otherwise, validate resolver name.
            if has_collection_expr:
                coll_expr = node.collection_expr
                assert coll_expr is not None
                coll_ast = self._parse(str(coll_expr), binding)
                type_checker.check(coll_ast)
                node.collection_ast = coll_ast
            elif has_collection:
                if node.collection not in COLLECTION_RESOLVERS:
                    available = sorted(COLLECTION_RESOLVERS.keys())
                    raise TypeCheckError(f"Unknown for_each collection '{node.collection}'. Available: {available}")

            # The body runs once per element with `target` rebound to it: an agent row
            # for every collection except the item-row ones.
            body_binding: TargetBinding = "item" if node.collection in _ITEM_TARGET_COLLECTIONS else "agent"

            # Recursively compile nested commands (with None check for mypy)
            nested: list[CommandNode] = []
            seen_ids: set[int] = set()
            for cmd in node.body or []:
                if id(cmd) in seen_ids:
                    continue
                seen_ids.add(id(cmd))
                nested.append(cmd)
            for cmd in nested:
                self._compile_command(cmd, body_binding)

            # Explicitly reject nested for_each until vectorized semantics are defined
            def _child_commands(cmd: CommandNode) -> list[CommandNode]:
                children: list[CommandNode] = []
                children.extend(cmd.then_commands or [])
                children.extend(cmd.else_commands or [])
                children.extend(cmd.body or [])
                children.extend(cmd.default_commands or [])
                children.extend(cmd.parallel_commands or [])
                children.extend(cmd.delay_commands or [])
                for _, case_body in cmd.cases or []:
                    children.extend(case_body)
                return children

            def _contains_for_each(commands: list[CommandNode]) -> bool:
                for c in commands:
                    if c.type == CommandType.FOR_EACH:
                        return True
                    nested_cmds = _child_commands(c)
                    if nested_cmds and _contains_for_each(nested_cmds):
                        return True
                return False

            if _contains_for_each(nested):
                raise TypeCheckError("Nested for_each is not supported under current vectorized constraints")

        elif node.type == CommandType.SWITCH:
            from townlet.world.expression.type_checker import TypeCheckError

            if node.switch_expr is None:
                raise TypeCheckError("SWITCH command requires 'switch' expression")

            switch_ast = self._parse(node.switch_expr, binding)
            switch_type = type_checker.check(switch_ast)
            node.switch_ast = switch_ast

            compiled_cases: list[tuple[Any, list[CommandNode]]] = []
            for when_expr, body in node.cases or []:
                if when_expr is None:
                    raise TypeCheckError("SWITCH case missing 'when' expression")
                when_ast = self._parse(when_expr, binding)
                when_type = type_checker.check(when_ast)
                if when_type != switch_type:
                    raise TypeCheckError(f"SWITCH case type mismatch: switch is {switch_type}, case is {when_type}")
                for cmd in body:
                    self._compile_command(cmd, binding)
                compiled_cases.append((when_ast, body))
            node.case_asts = compiled_cases

            for cmd in node.default_commands or []:
                self._compile_command(cmd, binding)

        elif node.type == CommandType.REDUCE:
            from townlet.world.expression.type_checker import TypeCheckError

            if (
                node.reduce_expr is None
                or node.reduce_iterator is None
                or node.reduce_init_expr is None
                or node.reduce_body_expr is None
                or node.reduce_target is None
            ):
                raise TypeCheckError("REDUCE command requires collection, iterator, init, body, and target")

            # Parse expressions
            coll_ast = self._parse(node.reduce_expr, binding)
            init_ast = self._parse(node.reduce_init_expr, binding)
            body_ast = self._parse(node.reduce_body_expr, binding)

            # Type check collection -> must be iterable of known-size tensors/lists (policy: reject unknown/ragged)
            coll_type = type_checker.check(coll_ast)
            if coll_type not in {"list", "tensor"}:
                raise TypeCheckError("REDUCE collection must be fixed-size list or tensor under vectorized constraints")

            # Type check init and infer accumulator type
            acc_type = type_checker.check(init_ast)

            # Extend schema with iterator and accumulator symbols for body checking
            iter_name = node.reduce_iterator
            # Temporarily augment schema
            original_schema = dict(type_checker.schema)
            type_checker.schema[iter_name] = acc_type  # assume numeric iterator compatible with accumulator
            type_checker.schema["acc"] = acc_type
            body_type = type_checker.check(body_ast)
            # Restore schema
            type_checker.schema = original_schema

            if body_type != acc_type:
                raise TypeCheckError(f"REDUCE body must return accumulator type {acc_type}, got {body_type}")

            # Validate target path exists and matches accumulator type
            node.reduce_target = self._resolve_write_path(node.reduce_target, binding, "REDUCE into")
            if node.reduce_target not in schema:
                raise TypeCheckError(f"Path '{node.reduce_target}' not found in schema")
            target_type = schema[node.reduce_target]
            if target_type != acc_type:
                raise TypeCheckError(f"REDUCE target type mismatch: expected {target_type}, got {acc_type}")

            # Store compiled ASTs
            node.collection_ast = coll_ast
            node.reduce_init_ast = init_ast
            node.reduce_body_ast = body_ast

        elif node.type == CommandType.PARALLEL:
            from townlet.world.expression.type_checker import TypeCheckError

            branches = node.parallel_commands or []
            if not branches:
                raise TypeCheckError("PARALLEL command requires at least one branch")

            # Collect target paths written by branches to detect conflicts (modify/reduce targets only for now).
            # Bare agent paths are compared in their resolved form so `vfs.x` and `target.vfs.x` collide.
            def collect_writes(cmd: CommandNode) -> set[str]:
                writes: set[str] = set()
                if cmd.type == CommandType.MODIFY and cmd.path:
                    writes.add(self._canonical_write_path(cmd.path))
                if cmd.type == CommandType.REDUCE and cmd.reduce_target:
                    writes.add(self._canonical_write_path(cmd.reduce_target))
                # Recurse into nested blocks
                for seq in (
                    cmd.then_commands or [],
                    cmd.else_commands or [],
                    cmd.body or [],
                    cmd.default_commands or [],
                    cmd.parallel_commands or [],
                ):
                    for sub in seq:
                        writes.update(collect_writes(sub))
                return writes

            branch_writes = [collect_writes(bc) for bc in branches]
            # Detect conflicts
            seen: set[str] = set()
            for writes in branch_writes:
                overlap = seen.intersection(writes)
                if overlap:
                    raise TypeCheckError(f"PARALLEL branches write the same targets: {sorted(overlap)}")
                seen.update(writes)

            # Compile branches
            for bc in branches:
                self._compile_command(bc, binding)

        elif node.type == CommandType.DELAY:
            from townlet.world.expression.type_checker import TypeCheckError

            if not self.time_enabled:
                raise TypeCheckError("delay command not allowed when time is disabled")
            if node.delay_ticks_expr is None:
                raise TypeCheckError("delay command requires ticks expression")
            if not node.delay_commands:
                raise TypeCheckError("delay command requires a non-empty do block")

            ticks_ast = self._parse(node.delay_ticks_expr, binding)
            ticks_type = type_checker.check(ticks_ast)
            if ticks_type != "int":
                raise TypeCheckError("delay ticks expression must be int")

            # Store compiled AST
            node.delay_ticks_ast = ticks_ast

            # Compile nested commands (the scheduler replays them with the same target)
            for cmd in node.delay_commands:
                self._compile_command(cmd, binding)

        elif node.type == CommandType.SPAWN_ITEM:
            from townlet.world.expression.type_checker import TypeCheckError

            if not node.item_type:
                raise TypeCheckError("SPAWN_ITEM command requires 'item_type'")
            if node.quantity is None or node.quantity < 1:
                raise TypeCheckError(f"SPAWN_ITEM '{node.item_type}' requires a declared quantity >= 1, got {node.quantity}")

            # Validate position expression if provided (not simple "random"/"self"/"target")
            simple_position = node.position in {"random", "self", "target"} or node.position is None
            if not simple_position and node.position_expr:
                position_ast = self._parse(node.position_expr, binding)
                # Position expressions should produce coordinates - type check for sanity
                type_checker.check(position_ast)
                node.position_ast = position_ast

        return node

    def compile_commands(self, nodes: list[CommandNode]) -> list[CommandNode]:
        """Compile list of commands.

        Args:
            nodes: List of CommandNode AST nodes

        Returns:
            Validated list of CommandNode (same instances, after validation)
        """
        for node in nodes:
            self.compile_command(node)
        return nodes


def _refuse_history_functions(node: ASTNode, expression: str) -> None:
    """Refuse a temporal-history function anywhere in a command expression."""
    for found in _walk(node):
        if isinstance(found, FunctionCall) and found.function_name in HISTORY_FUNCTIONS:
            from townlet.world.expression.type_checker import TypeCheckError

            raise TypeCheckError(
                f"Function '{found.function_name}' in '{expression}' reads temporal history, which only VFS "
                "profile expressions keep. Declare a variable with `expression: "
                f'"{found.function_name}(...)"` in the pack-scope variables declaration and read that '
                "variable from the command instead."
            )


def _walk(node: ASTNode) -> list[ASTNode]:
    found = [node]
    for field in fields(node):
        found.extend(_walk_value(getattr(node, field.name)))
    return found


def _walk_value(value: Any) -> list[ASTNode]:
    if isinstance(value, ASTNode):
        return _walk(value)
    if isinstance(value, list | tuple):
        return [nested for item in value for nested in _walk_value(item)]
    return []


def _rewrite_ast(node: ASTNode, is_bare_agent_path: Any) -> ASTNode:
    """Return `node` with every bare agent-scoped `vfs.X` PathAccess rebased to `target.vfs.X`.

    AST nodes are frozen dataclasses; untouched subtrees are returned by identity.
    """
    if isinstance(node, PathAccess):
        if is_bare_agent_path(".".join(node.segments)):
            return replace(node, segments=["target", *node.segments])
        return node
    changes: dict[str, Any] = {}
    for field in fields(node):
        value = getattr(node, field.name)
        rewritten = _rewrite_value(value, is_bare_agent_path)
        if rewritten is not value:
            changes[field.name] = rewritten
    return replace(node, **changes) if changes else node


def _rewrite_value(value: Any, is_bare_agent_path: Any) -> Any:
    if isinstance(value, ASTNode):
        return _rewrite_ast(value, is_bare_agent_path)
    if isinstance(value, list):
        items = [_rewrite_value(item, is_bare_agent_path) for item in value]
        return items if any(new is not old for new, old in zip(items, value, strict=True)) else value
    if isinstance(value, tuple):
        members = tuple(_rewrite_value(item, is_bare_agent_path) for item in value)
        return members if any(new is not old for new, old in zip(members, value, strict=True)) else value
    return value
