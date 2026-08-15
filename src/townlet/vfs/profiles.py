"""VFS profile compilation with expression evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import networkx as nx  # type: ignore[import-untyped]

from townlet.config.vfs_profiles_config import (
    AgentVFSVariableConfig,
    GlobalVFSProfileConfig,
    GlobalVFSVariableConfig,
    ItemVFSProfileConfig,
    ItemVFSVariableConfig,
)
from townlet.world.expression import ASTNode, ExpressionParser, PathAccess, Variable
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError

__all__ = [
    "VFSProfileCompiler",
    "CircularDependencyError",
    "CompiledVariable",
    "CompiledGlobalProfile",
    "CompiledItemProfile",
]


@dataclass
class CompiledVariable:
    """Compiled VFS variable with parsed expression."""

    name: str
    type: str
    exposed_to: tuple[str, ...]
    semantic_type: str
    expression: str | None = None
    ast: ASTNode | None = None  # None if initial_value
    initial_value: int | float | bool | list | None = None
    result_type: str | None = None  # Inferred type from type checker
    shape: list[int] | None = None
    initial_value_mode: str | None = None
    initial_value_params: dict | None = None
    dims: int | None = None


@dataclass
class CompiledGlobalProfile:
    """Compiled global VFS profile."""

    variables: list[CompiledVariable]
    dependencies: dict[str, tuple[str, ...]]  # In-profile dependencies per variable


@dataclass(frozen=True)
class CompiledItemProfile:
    """Compiled item VFS profile with variables in topological order."""

    profile_name: str  # Profile name (e.g., "food_stats")
    variables: list[CompiledVariable]  # Variables in dependency order

    def __post_init__(self):
        # Make variables tuple for immutability
        if not isinstance(self.variables, tuple):
            object.__setattr__(self, "variables", tuple(self.variables))


class CircularDependencyError(Exception):
    """Raised when circular dependency detected in VFS variables."""

    pass


class VFSProfileCompiler:
    """Compiles VFS profiles with expression dependency resolution."""

    SUPPORTED_VERSIONS = ("1.0",)

    def __init__(self):
        self.parser = ExpressionParser()

    def validate_version(self, version: str) -> None:
        """Ensure the provided config version is supported."""
        if version not in self.SUPPORTED_VERSIONS:
            supported = ", ".join(self.SUPPORTED_VERSIONS)
            raise ValueError(f"Unsupported VFS profiles version '{version}'. Supported versions: {supported}")

    def build_dependency_graph(
        self, variables: Sequence[GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig]
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

    def topological_sort(
        self, variables: Sequence[GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig]
    ) -> list[GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig]:
        """Sort variables in dependency order.

        Returns list of variables sorted topologically.
        Raises CircularDependencyError if dependency cycles exist.
        """
        sorted_vars, _ = self._topological_sort_internal(variables)
        return sorted_vars

    def topological_sort_with_dependencies(
        self, variables: Sequence[GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig]
    ) -> tuple[list[GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig], dict[str, tuple[str, ...]]]:
        """Return both sorted variables and dependency map."""
        return self._topological_sort_internal(variables)

    def _topological_sort_internal(
        self, variables: Sequence[GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig]
    ) -> tuple[list[GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig], dict[str, tuple[str, ...]]]:
        graph = self.build_dependency_graph(variables)

        # Check for cycles
        try:
            # networkx raises NetworkXUnfeasible if cycles exist
            sorted_names = list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            # Find a cycle for error message
            cycles = list(nx.simple_cycles(graph))
            cycle_str = " -> ".join(cycles[0] + [cycles[0][0]])
            raise CircularDependencyError(f"Circular dependency detected in cycle: {cycle_str}")

        # Map names back to variable configs
        name_to_var = {v.name: v for v in variables}
        sorted_vars = [name_to_var[name] for name in sorted_names]

        dependencies: dict[str, tuple[str, ...]] = {}
        for name in sorted_names:
            deps = tuple(sorted(graph.predecessors(name)))
            dependencies[name] = deps

        return sorted_vars, dependencies

    def compile_variable(
        self,
        var: GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig,
        schema: dict[str, str],
    ) -> CompiledVariable:
        """Compile a VFS variable (parse expression, type check).

        Args:
            var: Variable config
            schema: Type schema for available variables

        Returns:
            Compiled variable with parsed AST

        Raises:
            TypeCheckError: If expression has type error
        """
        # Variable with static initial value
        if var.initial_value is not None:
            return CompiledVariable(
                name=var.name,
                exposed_to=tuple(var.exposed_to),
                semantic_type=getattr(var, "semantic_type", "custom"),
                type=var.type,
                expression=None,
                ast=None,
                initial_value=var.initial_value,
                result_type=var.type,
                shape=getattr(var, "shape", None),
                initial_value_mode=getattr(var, "initial_value_mode", None),
                initial_value_params=getattr(var, "initial_value_params", None),
                dims=getattr(var, "dims", None),
            )

        # Variable with expression
        # Parse expression to AST
        ast = self.parser.parse(var.expression)

        # Type check expression
        type_checker = TypeChecker(schema=schema)
        result_type = type_checker.check(ast)

        # Verify result type matches declared type
        if result_type != var.type:
            raise TypeCheckError(f"Variable '{var.name}' declared as {var.type} but expression returns {result_type}")

        return CompiledVariable(
            name=var.name,
            exposed_to=tuple(var.exposed_to),
            semantic_type=getattr(var, "semantic_type", "custom"),
            type=var.type,
            expression=var.expression,
            ast=ast,
            initial_value=None,
            result_type=result_type,
            shape=getattr(var, "shape", None),
            initial_value_mode=getattr(var, "initial_value_mode", None),
            initial_value_params=getattr(var, "initial_value_params", None),
            dims=getattr(var, "dims", None),
        )

    def compile_global_profile(self, profile: GlobalVFSProfileConfig, bar_schema: dict[str, str] | None = None) -> CompiledGlobalProfile:
        """Compile global VFS profile.

        Args:
            profile: Global profile config
            bar_schema: Type schema for bars (e.g., {"energy": "float"})

        Returns:
            Compiled profile with variables in dependency order
        """
        # Sort variables in dependency order
        sorted_vars, dependencies = self.topological_sort_with_dependencies(profile.variables)

        # Build type schema for expression type checking
        schema: dict[str, str] = {}

        # Add bar paths to schema
        if bar_schema:
            for bar_name, bar_type in bar_schema.items():
                schema[f"bar.{bar_name}"] = bar_type

        # Compile each variable
        compiled_vars = []
        for var in sorted_vars:
            compiled = self.compile_variable(var, schema)
            compiled_vars.append(compiled)

            # Add this variable to schema for subsequent variables
            schema[var.name] = var.type

        return CompiledGlobalProfile(variables=compiled_vars, dependencies=dependencies)

    def compile_item_profile(
        self,
        profile: ItemVFSProfileConfig,
        bar_schema: dict[str, str],
    ) -> CompiledItemProfile:
        """Compile item VFS profile.

        Args:
            profile: Item profile config from vfs_profiles.yaml
            bar_schema: Type schema for bars (for expression type checking)

        Returns:
            Compiled item profile with variables in topological order

        Raises:
            ValueError: If circular dependencies detected
        """
        # Sort variables in dependency order
        sorted_vars, _ = self.topological_sort_with_dependencies(profile.variables)

        # Build variable schema (item profiles can reference bars)
        var_schema: dict[str, str] = {}

        # Items can reference bars but not global/agent VFS
        # (items are isolated instances)
        var_schema.update(bar_schema)

        # Compile each variable
        compiled_vars: list[CompiledVariable] = []

        for var in sorted_vars:
            compiled = self.compile_variable(var, var_schema)
            compiled_vars.append(compiled)

            # Add this variable to schema for subsequent variables
            var_schema[var.name] = var.type

        return CompiledItemProfile(
            profile_name=profile.profile_name,
            variables=compiled_vars,
        )
