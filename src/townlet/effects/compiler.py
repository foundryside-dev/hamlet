"""Command compiler with expression validation."""

from __future__ import annotations

from typing import Any

from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker

__all__ = ["CommandCompiler"]


class CommandCompiler:
    """Compile commands with expression type checking."""

    def __init__(self, schema: dict[str, str], *, time_enabled: bool = True):
        """Initialize compiler with type schema.

        Args:
            schema: Type schema for paths (e.g., {"target.bar.energy": "float"})
            time_enabled: Whether temporal mechanics are enabled (gates delay)
        """
        self.schema = schema
        self.time_enabled = time_enabled
        self.parser = ExpressionParser()  # type: ignore[no-untyped-call]
        self.type_checker = TypeChecker(schema=schema)

    def compile_command(self, node: CommandNode) -> CommandNode:
        """Compile and validate command.

        Args:
            node: CommandNode AST

        Returns:
            Validated CommandNode (same instance, after validation and AST compilation)

        Raises:
            TypeCheckError: If path invalid or type mismatch
        """
        if node.type == CommandType.MODIFY:
            # Validate required fields are present
            if node.path is None or node.value_expr is None:
                from townlet.world.expression.type_checker import TypeCheckError

                raise TypeCheckError("MODIFY command requires both 'path' and 'value_expr'")

            # Validate path exists
            if node.path not in self.schema:
                from townlet.world.expression.type_checker import TypeCheckError

                raise TypeCheckError(f"Path '{node.path}' not found in schema. Available: {list(self.schema.keys())}")

            # Parse and type-check value expression
            value_ast = self.parser.parse(node.value_expr)
            value_type = self.type_checker.check(value_ast)

            # Verify type matches target path
            target_type = self.schema[node.path]
            if value_type != target_type:
                from townlet.world.expression.type_checker import TypeCheckError

                raise TypeCheckError(f"Type mismatch for path '{node.path}': expected {target_type}, got {value_type}")

            # ✅ PERF FIX: Store compiled AST for runtime use
            node.value_ast = value_ast

        elif node.type == CommandType.SPAWN_EFFECT:
            # Validate and compile target expression only when not a simple literal
            simple_target = node.target in {"self", "target"} or isinstance(node.target, int)
            if not simple_target and node.target_expr:
                target_ast = self.parser.parse(node.target_expr)
                target_type = self.type_checker.check(target_ast)
                if target_type != "int":
                    from townlet.world.expression.type_checker import TypeCheckError

                    raise TypeCheckError(f"spawn_effect target expression must be int, got {target_type} for '{node.target_expr}'")

                # ✅ Store compiled AST
                node.target_ast = target_ast

        elif node.type == CommandType.IF:
            # Validate required fields are present
            if node.condition_expr is None:
                from townlet.world.expression.type_checker import TypeCheckError

                raise TypeCheckError("IF command requires 'condition_expr'")

            # Validate condition is boolean
            cond_ast = self.parser.parse(node.condition_expr)
            cond_type = self.type_checker.check(cond_ast)

            if cond_type != "bool":
                from townlet.world.expression.type_checker import TypeCheckError

                raise TypeCheckError(f"If condition must be bool, got {cond_type}")

            # ✅ Store compiled AST
            node.condition_ast = cond_ast

            # Recursively compile nested commands (with None checks for mypy)
            if node.then_commands is not None:
                for cmd in node.then_commands:
                    self.compile_command(cmd)
            if node.else_commands is not None:
                for cmd in node.else_commands:
                    self.compile_command(cmd)

        elif node.type == CommandType.FOR_EACH:
            # Validate required fields are present
            from townlet.effects.collections import COLLECTION_RESOLVERS
            from townlet.world.expression.type_checker import TypeCheckError

            has_collection = node.collection is not None
            has_collection_expr = node.collection_expr is not None

            if not has_collection and not has_collection_expr:
                raise TypeCheckError("FOR_EACH command requires 'collection'")

            # Validate simple collection names against registered resolvers
            if has_collection:
                if node.collection not in COLLECTION_RESOLVERS:
                    available = sorted(COLLECTION_RESOLVERS.keys())
                    raise TypeCheckError(f"Unknown for_each collection '{node.collection}'. Available: {available}")

            # Only parse/type-check collection_expr when explicitly provided
            if has_collection_expr:
                coll_expr = node.collection_expr
                assert coll_expr is not None
                coll_ast = self.parser.parse(coll_expr)
                self.type_checker.check(coll_ast)
                node.collection_ast = coll_ast

            # Recursively compile nested commands (with None check for mypy)
            nested: list[CommandNode] = []
            seen_ids: set[int] = set()
            for seq in (node.do_commands or [], node.body or []):
                for cmd in seq:
                    if id(cmd) in seen_ids:
                        continue
                    seen_ids.add(id(cmd))
                    nested.append(cmd)
            for cmd in nested:
                self.compile_command(cmd)

            # Explicitly reject nested for_each until vectorized semantics are defined
            def _contains_for_each(commands: list[CommandNode]) -> bool:
                for c in commands:
                    if c.type == CommandType.FOR_EACH:
                        return True
                    nested_cmds: list[CommandNode] = []
                    for seq in (c.then_commands or [], c.else_commands or [], c.do_commands or [], c.body or [], c.default_commands or []):
                        nested_cmds.extend(seq)
                    if nested_cmds and _contains_for_each(nested_cmds):
                        return True
                return False

            if _contains_for_each(nested):
                raise TypeCheckError("Nested for_each is not supported under current vectorized constraints")

        elif node.type == CommandType.SWITCH:
            from townlet.world.expression.type_checker import TypeCheckError

            if node.switch_expr is None:
                raise TypeCheckError("SWITCH command requires 'switch' expression")

            switch_ast = self.parser.parse(node.switch_expr)
            switch_type = self.type_checker.check(switch_ast)
            node.switch_ast = switch_ast

            compiled_cases: list[tuple[Any, list[CommandNode]]] = []
            for when_expr, body in node.cases or []:
                if when_expr is None:
                    raise TypeCheckError("SWITCH case missing 'when' expression")
                when_ast = self.parser.parse(when_expr)
                when_type = self.type_checker.check(when_ast)
                if when_type != switch_type:
                    raise TypeCheckError(f"SWITCH case type mismatch: switch is {switch_type}, case is {when_type}")
                for cmd in body:
                    self.compile_command(cmd)
                compiled_cases.append((when_ast, body))
            node.case_asts = compiled_cases

            for cmd in node.default_commands or []:
                self.compile_command(cmd)

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
            coll_ast = self.parser.parse(node.reduce_expr)
            init_ast = self.parser.parse(node.reduce_init_expr)
            body_ast = self.parser.parse(node.reduce_body_expr)

            # Type check collection -> must be iterable of known-size tensors/lists (policy: reject unknown/ragged)
            coll_type = self.type_checker.check(coll_ast)
            if coll_type not in {"list", "tensor"}:
                raise TypeCheckError("REDUCE collection must be fixed-size list or tensor under vectorized constraints")

            # Type check init and infer accumulator type
            acc_type = self.type_checker.check(init_ast)

            # Extend schema with iterator and accumulator symbols for body checking
            iter_name = node.reduce_iterator
            # Temporarily augment schema
            original_schema = dict(self.type_checker.schema)
            self.type_checker.schema[iter_name] = acc_type  # assume numeric iterator compatible with accumulator
            self.type_checker.schema["acc"] = acc_type
            body_type = self.type_checker.check(body_ast)
            # Restore schema
            self.type_checker.schema = original_schema

            if body_type != acc_type:
                raise TypeCheckError(f"REDUCE body must return accumulator type {acc_type}, got {body_type}")

            # Validate target path exists and matches accumulator type
            if node.reduce_target not in self.schema:
                raise TypeCheckError(f"Path '{node.reduce_target}' not found in schema")
            target_type = self.schema[node.reduce_target]
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

            # Collect target paths written by branches to detect conflicts (modify/reduce targets only for now)
            def collect_writes(cmd: CommandNode) -> set[str]:
                writes: set[str] = set()
                if cmd.type == CommandType.MODIFY and cmd.path:
                    writes.add(cmd.path)
                if cmd.type == CommandType.REDUCE and cmd.reduce_target:
                    writes.add(cmd.reduce_target)
                # Recurse into nested blocks
                for seq in (
                    cmd.then_commands or [],
                    cmd.else_commands or [],
                    cmd.do_commands or [],
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
                self.compile_command(bc)

        elif node.type == CommandType.DELAY:
            from townlet.world.expression.type_checker import TypeCheckError

            if not self.time_enabled:
                raise TypeCheckError("delay command not allowed when time is disabled")
            if node.delay_ticks_expr is None:
                raise TypeCheckError("delay command requires ticks expression")
            if not node.delay_commands:
                raise TypeCheckError("delay command requires a non-empty do block")

            ticks_ast = self.parser.parse(node.delay_ticks_expr)
            ticks_type = self.type_checker.check(ticks_ast)
            if ticks_type != "int":
                raise TypeCheckError("delay ticks expression must be int")

            # Store compiled AST
            node.delay_ticks_ast = ticks_ast

            # Compile nested commands
            for cmd in node.delay_commands:
                self.compile_command(cmd)

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
