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
        self.parser = ExpressionParser()
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
            # Validate and compile target expression
            if node.target_expr:
                target_ast = self.parser.parse(node.target_expr)
                self.type_checker.check(target_ast)
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
            if node.collection_expr is None:
                from townlet.world.expression.type_checker import TypeCheckError

                raise TypeCheckError("FOR_EACH command requires 'collection_expr'")

            # Validate collection expression
            coll_ast = self.parser.parse(node.collection_expr)
            self.type_checker.check(coll_ast)

            # ✅ Store compiled AST
            node.collection_ast = coll_ast

            # Recursively compile nested commands (with None check for mypy)
            if node.do_commands is not None:
                for cmd in node.do_commands:
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
