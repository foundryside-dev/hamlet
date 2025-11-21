"""Command compiler with expression validation."""

from __future__ import annotations

from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker

__all__ = ["CommandCompiler"]


class CommandCompiler:
    """Compile commands with expression type checking."""

    def __init__(self, schema: dict[str, str]):
        """Initialize compiler with type schema.

        Args:
            schema: Type schema for paths (e.g., {"target.bar.energy": "float"})
        """
        self.schema = schema
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
