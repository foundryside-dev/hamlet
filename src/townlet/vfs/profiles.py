"""VFS profile compilation with expression evaluation."""

from __future__ import annotations

import networkx as nx

from townlet.config.vfs_profiles_config import (
    AgentVFSVariableConfig,
    GlobalVFSVariableConfig,
    ItemVFSVariableConfig,
)
from townlet.world.expression import ASTNode, ExpressionParser, PathAccess, Variable

__all__ = [
    "VFSProfileCompiler",
]


class VFSProfileCompiler:
    """Compiles VFS profiles with expression dependency resolution."""

    def __init__(self):
        self.parser = ExpressionParser()

    def build_dependency_graph(
        self, variables: list[GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig]
    ) -> nx.DiGraph:
        """Build dependency graph for variables.

        Args:
            variables: List of variable configs

        Returns:
            Directed graph with edges from dependency -> dependent
        """
        graph: nx.DiGraph = nx.DiGraph()

        # Add all variables as nodes
        for var in variables:
            graph.add_node(var.name)

        # Add edges for expression dependencies
        # Pre-compute variable names as a set for O(1) lookup instead of O(n)
        variable_names = {v.name for v in variables}

        for var in variables:
            if var.expression is not None:
                # Extract variable references from expression
                deps = self._extract_variable_refs(var.expression)
                for dep in deps:
                    # Only add edge if dependency is in same profile
                    if dep in variable_names:
                        graph.add_edge(dep, var.name)

        return graph

    def _extract_variable_refs(self, expression: str) -> set[str]:
        """Extract variable references by parsing AST (robust, not regex).

        Uses Phase 1 parser to build AST, then traverses to find Variable nodes.
        This is 100% accurate - no false matches from string literals or partial matches.

        Args:
            expression: Expression string (e.g., "a + b * c")

        Returns:
            Set of variable names referenced
        """
        # Parse expression to AST (reuse Phase 1 parser!)
        ast = self.parser.parse(expression)

        # Traverse AST to collect Variable nodes
        refs = set()

        def visit(node: ASTNode) -> None:
            """Recursively visit AST nodes to find Variables and PathAccess."""
            if isinstance(node, Variable):
                refs.add(node.name)
            elif isinstance(node, PathAccess):
                # Extract root namespace (e.g., "bar" from "bar.energy")
                refs.add(node.segments[0])

            # Visit children (handles BinaryOp, UnaryOp, FunctionCall, etc.)
            if hasattr(node, "left"):
                visit(node.left)
            if hasattr(node, "right"):
                visit(node.right)
            if hasattr(node, "operand"):
                visit(node.operand)
            if hasattr(node, "arguments"):
                for arg in node.arguments:
                    visit(arg)
            if hasattr(node, "condition"):
                visit(node.condition)
            if hasattr(node, "true_branch"):
                visit(node.true_branch)
            if hasattr(node, "false_branch"):
                visit(node.false_branch)
            if hasattr(node, "base"):
                visit(node.base)
            if hasattr(node, "index"):
                visit(node.index)

        visit(ast)
        return refs
