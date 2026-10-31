"""Command compiler with expression validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from townlet.config.effects_config import EffectScope
from townlet.effects.schema import CommandNode, CommandType
from townlet.vfs.namespace import (
    EFFECT_PIPELINE,
    ExpressionSource,
    Namespace,
    ReadContext,
    SpellingError,
    SymbolKind,
    inline_expression_reads,
)
from townlet.world.expression import ExpressionParser, read_paths
from townlet.world.expression.ast_nodes import ASTNode
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError

__all__ = ["CommandCompiler"]

# for_each collections whose iteration target is an item row, not an agent row
# (executor `_for_each_contexts`: only inventory_items sets target_is_item).
_ITEM_TARGET_COLLECTIONS = frozenset({"inventory_items"})

_WRITABLE_KINDS = frozenset({SymbolKind.VARIABLE, SymbolKind.METER, SymbolKind.ITEM_STATE})


class CommandCompiler:
    """Compile command pipelines: every path and expression resolves through the one resolver (VFS round-2 S5)."""

    def __init__(
        self,
        namespace: Namespace,
        *,
        context: ReadContext,
        time_enabled: bool,
        expressions: Mapping[str, ExpressionSource],
    ):
        """Initialize the compiler for one pipeline.

        Args:
            namespace: The symbol table (``Namespace.of_registry`` over the compiled roster)
            context: What the pipeline's runtime serves: ``INTERACTION_PIPELINE`` for an
                affordance interaction, ``.with_item(True)`` for an item interaction,
                ``EFFECT_PIPELINE`` (``.with_item(True)`` when item-scoped) for an effect.
                A bare variable is read and written in the pipeline's world by its declared
                scope (S1: a world has one agent, so an agent variable is that agent's row
                wherever the pipeline runs); ``item.<x>`` names the bound item's state.
            time_enabled: Whether temporal mechanics are enabled (gates delay)
            expressions: Every compiled expression variable as a consumer reads it; a
                pure one is inlined into every expression that reads it (S4 follow-up)
        """
        self.namespace = namespace
        self.context = context
        self.time_enabled = time_enabled
        self.expressions = expressions
        self.parser = ExpressionParser()  # type: ignore[no-untyped-call]

    @classmethod
    def for_effect_scope(
        cls,
        namespace: Namespace,
        *,
        scope: EffectScope,
        time_enabled: bool,
        expressions: Mapping[str, ExpressionSource],
    ) -> CommandCompiler:
        """The compiler for an effect of ``scope``: an item-scoped effect is bound to its item."""
        return cls(
            namespace,
            context=EFFECT_PIPELINE.with_item(scope == EffectScope.ITEM),
            time_enabled=time_enabled,
            expressions=expressions,
        )

    def _schema(self, context: ReadContext) -> dict[str, str]:
        return self.namespace.schema(context)

    def _checker(self, context: ReadContext) -> TypeChecker:
        return TypeChecker(schema=self.namespace.schema(context))

    def _resolve_write_path(self, path: str, context: ReadContext, what: str) -> str:
        """The canonical path a write lands on, or a TypeCheckError naming the spelling to use."""
        try:
            symbol = self.namespace.resolve(path, context)
        except SpellingError as exc:
            raise TypeCheckError(f"{what} {exc}") from exc
        if symbol.kind not in _WRITABLE_KINDS:
            raise TypeCheckError(f"{what} '{path}' is the {symbol.kind}, which is no state a command can change")
        return path

    def _parse(self, expression: str, context: ReadContext) -> ASTNode:
        ast = self.parser.parse(expression)
        refusals = self.namespace.refusals(ast, context)
        if refusals:
            raise TypeCheckError(f"Expression '{expression}': {' '.join(refusals)}")
        try:
            return inline_expression_reads(ast, self.expressions, consumer="a command pipeline")
        except SpellingError as exc:
            raise TypeCheckError(f"Expression '{expression}' {exc}") from exc

    def compile_command(self, node: CommandNode) -> CommandNode:
        """Compile and validate command.

        Args:
            node: CommandNode AST

        Returns:
            Validated CommandNode (same instance, after validation and AST compilation)

        Raises:
            TypeCheckError: If path invalid or type mismatch
        """
        return self._compile_command(node, self.context)

    def _compile_command(self, node: CommandNode, binding: ReadContext) -> CommandNode:
        schema = self._schema(binding)
        type_checker = self._checker(binding)
        if node.type == CommandType.MODIFY:
            # Validate required fields are present
            if node.path is None or node.value_expr is None:
                raise TypeCheckError("MODIFY command requires both 'path' and 'value_expr'")

            node.path = self._resolve_write_path(node.path, binding, "MODIFY target")

            # Validate path exists
            if node.path not in schema:
                raise TypeCheckError(f"Path '{node.path}' not found in schema. Available: {list(schema.keys())}")

            # Parse and type-check value expression
            value_ast = self._parse(node.value_expr, binding)
            value_type = type_checker.check(value_ast)

            # Verify type matches target path
            target_type = schema[node.path]
            if value_type != target_type:
                raise TypeCheckError(f"Type mismatch for path '{node.path}': expected {target_type}, got {value_type}")

            # ✅ PERF FIX: Store compiled AST for runtime use
            node.value_ast = value_ast

        elif node.type == CommandType.SPAWN_EFFECT:
            if node.effect_id is None:
                raise TypeCheckError("SPAWN_EFFECT command requires 'effect_id'")
            if node.target is None and node.target_expr is None:
                raise TypeCheckError("SPAWN_EFFECT command requires 'target'")
            if node.intensity is None:
                raise TypeCheckError("SPAWN_EFFECT command requires 'intensity'")

            if isinstance(node.target, int):
                raise TypeCheckError(spawn_target_literal_refusal(str(node.target)))
            if node.target is None and node.target_expr and spawn_target_reads_nothing(node.target_expr):
                raise TypeCheckError(spawn_target_literal_refusal(node.target_expr))
            if node.target not in {"self", "target"} and node.target_expr:
                target_ast = self._parse(node.target_expr, binding)
                target_type = type_checker.check(target_ast)
                if target_type not in {"int", "agent_ref", "item_ref"}:
                    raise TypeCheckError(
                        f"spawn_effect target expression must be an int or a reference, got {target_type} for '{node.target_expr}'"
                    )

                # ✅ Store compiled AST
                node.target_ast = target_ast

        elif node.type == CommandType.SAMPLE:
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
                raise TypeCheckError("IF command requires 'condition_expr'")

            # Validate condition is boolean
            cond_ast = self._parse(node.condition_expr, binding)
            cond_type = type_checker.check(cond_ast)

            if cond_type != "bool":
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
            body_binding = binding.with_item(binding.item or node.collection in _ITEM_TARGET_COLLECTIONS)

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

        elif node.type == CommandType.PARALLEL:
            branches = node.parallel_commands or []
            if not branches:
                raise TypeCheckError("PARALLEL command requires at least one branch")

            # Collect target paths written by branches to detect conflicts (modify targets only for now).
            # One spelling per reference, so two branches writing one target spell it alike.
            def collect_writes(cmd: CommandNode) -> set[str]:
                writes: set[str] = set()
                if cmd.type == CommandType.MODIFY and cmd.path:
                    writes.add(cmd.path)
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


def spawn_target_reads_nothing(target: str) -> bool:
    """Whether an authored spawn_effect target is a constant: it reads no state.

    `self` and `target` name the spawning context's entity. Any other target is an int
    expression; one that reads nothing (``3``, ``-1``, ``1 + 1``) is the same row in
    every world.
    """
    if target in {"self", "target"}:
        return False
    return not read_paths(ExpressionParser().parse(target))


def spawn_target_literal_refusal(target: str) -> str:
    """Why a constant spawn_effect target is refused (shared by the compile-time walker)."""
    return (
        f"spawn_effect target '{target}' is a constant row index. A row is one world's entity (an agent row is its "
        "world; an item row belongs to one world), and the batch is independent worlds (S1), so in every other world "
        "it names another world's entity. Spawn on 'self' or 'target', or an int expression over this world's state."
    )
