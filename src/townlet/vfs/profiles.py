"""VFS profile compilation with expression evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import networkx as nx  # type: ignore[import-untyped]
from pyparsing import ParseBaseException

from townlet.config.variables_config import VariableDeclaration
from townlet.vfs.access_policy import validate_static_access
from townlet.vfs.history import expression_history, same_instant_refs, walk
from townlet.vfs.namespace import AGENT_EXPRESSION, ENGINE_TICK, GLOBAL_EXPRESSION, Namespace, ReadContext
from townlet.vfs.schema import NormalizationSpec, VariableScope
from townlet.world.expression import ASTNode, ExpressionParser, PathAccess, Variable
from townlet.world.expression.ast_nodes import BinaryOp, Constant, FunctionCall, IfThenElse, UnaryOp
from townlet.world.expression.functions import TEMPORAL_FUNCTIONS
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError

__all__ = [
    "VFSProfileCompiler",
    "CircularDependencyError",
    "CompiledVariable",
    "CompiledGlobalProfile",
    "CompiledItemProfile",
    "VariableExpressionError",
]


@dataclass
class CompiledVariable:
    """Compiled VFS variable with parsed expression."""

    name: str
    type: str
    exposed_to: tuple[str, ...]
    lifetime: str
    readable_by: tuple[str, ...]
    writable_by: tuple[str, ...]
    expression: str | None = None
    ast: ASTNode | None = None  # None if initial_value
    initial_value: int | float | bool | list | None = None
    result_type: str | None = None  # Inferred type from type checker
    shape: list[int] | None = None
    initial_value_mode: str | None = None
    initial_value_params: dict | None = None
    dims: int | None = None
    # The author's declared observation group, retained for every compiled scope.
    semantic_type: str | None = None
    # The declared normalization — REQUIRED at exposure, absent when unexposed
    # (token-obs spec §2, normalization authority; hamlet-b8ad2ffcd6).
    normalization: NormalizationSpec | None = None

    def __post_init__(self) -> None:
        validate_static_access(self.name, self.readable_by, self.writable_by, self.exposed_to)
        self.readable_by = tuple(self.readable_by)
        self.writable_by = tuple(self.writable_by)
        self.exposed_to = tuple(self.exposed_to)


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
    """Raised when circular dependency detected in VFS variables; ``variable_id`` is one variable on the cycle."""

    def __init__(self, variable_id: str, message: str) -> None:
        super().__init__(message)
        self.variable_id = variable_id


class VariableExpressionError(TypeCheckError):
    """A variable's expression is refused; ``variable_id`` locates the refusal at its declaration."""

    def __init__(self, variable_id: str, message: str) -> None:
        super().__init__(message)
        self.variable_id = variable_id


class VFSProfileCompiler:
    """Compiles VFS profiles with expression dependency resolution."""

    def __init__(self):
        self.parser = ExpressionParser()

    def build_dependency_graph(self, variables: Sequence[VariableDeclaration]) -> nx.DiGraph:
        """Build the same-instant dependency graph of one profile (edges dependency -> dependent).

        An edge is a read of another in-profile variable's value at the current instant.
        A ``lag(x, n)`` read is not one: it reads ``x``'s history ring, committed after
        every variable evaluates (``vfs.history.same_instant_refs``). So a self-reference
        or a cycle closed only through ``lag`` sorts, and any other cycle refuses.
        The engine clock ``tick`` is an input, never an edge.
        """
        graph: nx.DiGraph = nx.DiGraph()
        graph.add_nodes_from(var.id for var in variables)
        variable_names = {v.id for v in variables}
        for var in variables:
            if var.expression is None:
                continue
            for dep in same_instant_refs(self.parser.parse(var.expression)) - {ENGINE_TICK}:
                if dep in variable_names:
                    graph.add_edge(dep, var.id)
        return graph

    def _extract_variable_refs(self, expression: str) -> set[str]:
        """Every variable an expression reads, at any instant (``lag`` reads included): its bare names.

        A dotted path is a meter (``bar.<m>``) or item state (``item.<x>``), never a variable."""
        return {node.name for node in walk(self.parser.parse(expression)) if isinstance(node, Variable)}

    def topological_sort(self, variables: Sequence[VariableDeclaration]) -> list[VariableDeclaration]:
        """Sort variables in dependency order.

        Returns list of variables sorted topologically.
        Raises CircularDependencyError if dependency cycles exist.
        """
        sorted_vars, _ = self._topological_sort_internal(variables)
        return sorted_vars

    def topological_sort_with_dependencies(
        self, variables: Sequence[VariableDeclaration]
    ) -> tuple[list[VariableDeclaration], dict[str, tuple[str, ...]]]:
        """Return both sorted variables and dependency map."""
        return self._topological_sort_internal(variables)

    def _topological_sort_internal(
        self, variables: Sequence[VariableDeclaration]
    ) -> tuple[list[VariableDeclaration], dict[str, tuple[str, ...]]]:
        graph = self.build_dependency_graph(variables)

        # Check for cycles
        try:
            # networkx raises NetworkXUnfeasible if cycles exist
            sorted_names = list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            # Find a cycle for error message
            cycles = list(nx.simple_cycles(graph))
            cycle_str = " -> ".join(cycles[0] + [cycles[0][0]])
            raise CircularDependencyError(
                cycles[0][0],
                f"Circular dependency detected in cycle: {cycle_str}. Each variable in it reads another's value at the "
                "same instant; only a lag(x, n) read (the value n ticks ago) may close a cycle or a self-reference.",
            )

        # Map names back to variable configs
        name_to_var = {v.id: v for v in variables}
        sorted_vars = [name_to_var[name] for name in sorted_names]

        dependencies: dict[str, tuple[str, ...]] = {}
        for name in sorted_names:
            deps = tuple(sorted(graph.predecessors(name)))
            dependencies[name] = deps

        return sorted_vars, dependencies

    def compile_variable(
        self,
        var: VariableDeclaration,
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
        # Variable with a static init source (no expression). The DTO enforces at least one of
        # {initial_value, initial_value_mode, expression}; initial_value_mode is how tensor
        # variables initialize (zeros/ones/eye/random_*). An expression variable may ALSO
        # declare initial_value (PDR-0143) — handled in the expression branch below, which is
        # why this branch is keyed on the absence of an expression, not the presence of a value.
        if var.expression is None:
            return CompiledVariable(
                name=var.id,
                exposed_to=tuple(var.exposed_to),
                lifetime=var.lifetime,
                readable_by=tuple(var.readable_by),
                writable_by=tuple(var.writable_by),
                type="float" if var.type == "scalar" else var.type,
                expression=None,
                ast=None,
                initial_value=var.initial_value,
                result_type="float" if var.type == "scalar" else var.type,
                shape=var.shape,
                initial_value_mode=var.initial_value_mode,
                initial_value_params=var.initial_value_params,
                dims=var.dims,
                semantic_type=var.semantic_type,
                normalization=var.normalization,
            )

        # Variable with expression
        # Parse expression to AST
        ast = self.parser.parse(var.expression)

        # Type check expression
        type_checker = TypeChecker(schema=schema)
        result_type = type_checker.check(ast)

        # Verify result type matches declared type
        if result_type != var.type and not (var.type == "scalar" and result_type in {"int", "float"}):
            raise TypeCheckError(f"Variable '{var.id}' declared as {var.type} but expression returns {result_type}")

        return CompiledVariable(
            name=var.id,
            exposed_to=tuple(var.exposed_to),
            lifetime=var.lifetime,
            readable_by=tuple(var.readable_by),
            writable_by=tuple(var.writable_by),
            type="float" if var.type == "scalar" else var.type,
            expression=var.expression,
            ast=ast,
            initial_value=var.initial_value,
            result_type=result_type,
            shape=var.shape,
            initial_value_mode=var.initial_value_mode,
            initial_value_params=var.initial_value_params,
            dims=var.dims,
            semantic_type=var.semantic_type,
            normalization=var.normalization,
        )

    def compile_profile(
        self,
        variables: Sequence[VariableDeclaration],
        bar_schema: dict[str, str] | None = None,
        *,
        cross_scope: Sequence[VariableDeclaration],
    ) -> CompiledGlobalProfile:
        """Compile one global or agent expression group.

        Args:
            variables: Canonical declarations sharing the compiled storage scope
            bar_schema: Type schema for bars (e.g., {"energy": "float"})
            cross_scope: The declarations of the other registry scope. Globals are
                readable inputs for an agent profile; agent state is refused for a
                global profile (scope widening), with a message naming both sides.

        Returns:
            Compiled profile with variables in dependency order
        """
        scopes = {var.scope for var in variables}
        if len(scopes) != 1:
            raise ValueError(f"A profile compiles one registry scope at a time; got {sorted(str(scope) for scope in scopes)}")
        (scope,) = scopes
        if scope not in {VariableScope.GLOBAL, VariableScope.AGENT}:
            raise ValueError(f"Variable expression execution supports global and agent scopes only; got {scope}")
        other_scope = VariableScope.AGENT if scope == VariableScope.GLOBAL else VariableScope.GLOBAL
        stray_scopes = {var.scope for var in cross_scope} - {other_scope}
        if stray_scopes:
            raise ValueError(
                f"cross_scope for a {scope} profile holds {other_scope} declarations only; got {sorted(str(s) for s in stray_scopes)}"
            )

        # Every expression parses before anything orders or reads it, so a parse error
        # is located at its declaration like every other refusal here.
        for var in variables:
            if var.expression is not None:
                try:
                    self.parser.parse(var.expression)
                except (ParseBaseException, ValueError) as exc:
                    raise VariableExpressionError(
                        var.id, f"Variable '{var.id}' expression '{var.expression}' does not parse: {exc}"
                    ) from exc

        # Sort variables in dependency order
        sorted_vars, dependencies = self.topological_sort_with_dependencies(variables)

        # The one resolver (VFS round-2 S5): the namespace of this profile's scope. An
        # agent expression reads every global by bare name (the runtime evaluates the
        # global profile first and feeds the agent profile the registry state, so these
        # are inputs, not dependency edges: build_dependency_graph only links
        # same-profile ids). Every profile variable enters up front with its declared
        # type and scope shape; a same-instant read is still ordered by the sort above,
        # a lag read may name a variable later in the order, or the variable itself.
        namespace = Namespace(
            variables=[(var.id, var.scope, var.type) for var in (*variables, *cross_scope)],
            meters=bar_schema or {},
            item_state={},
        )
        context = AGENT_EXPRESSION if scope == VariableScope.AGENT else GLOBAL_EXPRESSION
        schema = namespace.schema(context)
        shapes = namespace.shapes(context, payload_for_vectors=True)
        compiled_vars = []

        # The reverse direction is scope widening: a global expression has no agent axis
        # to hold per-agent state, so it refuses here, by name, before the namespace can
        # only say the scope is unreadable.
        widening_ids: set[str] = set()
        if scope == VariableScope.GLOBAL:
            widening_ids = {agent_var.id for agent_var in cross_scope}

        for var in sorted_vars:
            try:
                compiled_vars.append(self._compile_profile_variable(var, schema, shapes, namespace, context, widening_ids))
            except VariableExpressionError:
                raise
            except TypeCheckError as exc:
                raise VariableExpressionError(var.id, str(exc)) from exc

        return CompiledGlobalProfile(variables=compiled_vars, dependencies=dependencies)

    def _compile_profile_variable(
        self,
        var: VariableDeclaration,
        schema: dict[str, str],
        shapes: dict[str, str],
        namespace: Namespace,
        context: ReadContext,
        widening_ids: set[str],
    ) -> CompiledVariable:
        """One profile variable, its expression resolved, type-checked and shape-proved."""
        if var.expression is not None and widening_ids:
            widened = sorted(self._extract_variable_refs(var.expression) & widening_ids)
            if widened:
                raise TypeCheckError(
                    f"Variable '{var.id}' is global-scope but its expression reads agent-scope "
                    f"variable(s) {widened}; a global expression cannot widen to per-agent state. "
                    f"Declare '{var.id}' with scope agent, or read global state only."
                )
        if var.expression is not None:
            refusals = namespace.refusals(self.parser.parse(var.expression), context)
            if refusals:
                raise TypeCheckError(f"Variable '{var.id}' expression '{var.expression}': {' '.join(refusals)}")
        compiled = self.compile_variable(var, schema)
        if compiled.ast is not None:
            if var.type not in {"scalar", "bool"}:
                raise TypeCheckError(f"Variable '{var.id}' expression shape supports scalar and bool outputs only")
            try:
                expression_history(compiled.ast)
            except TypeCheckError as exc:
                raise TypeCheckError(f"Variable '{var.id}' expression '{var.expression}': {exc}") from exc
            output_shape = self._shape(compiled.ast, shapes, temporal=True)
            expected_shape = "agent" if var.scope == VariableScope.AGENT else "scalar"
            if output_shape != expected_shape:
                raise TypeCheckError(
                    f"Variable '{var.id}' expression shape is {output_shape}, expected {expected_shape} for {var.scope} scope"
                )
        return compiled

    @classmethod
    def expression_shape(cls, node: ASTNode, shapes: dict[str, str]) -> str:
        """Prove the output shape of an expression that keeps no history (a write, a rule).

        Temporal operators refuse here: only global and agent variable expressions keep
        the history rings they read (``compile_profile``).
        """
        return cls._shape(node, shapes, temporal=False)

    @classmethod
    def _shape(cls, node: ASTNode, shapes: dict[str, str], *, temporal: bool) -> str:
        """Prove the currently supported scalar/batch output shape without runtime sampling.

        Batch size remains symbolic: a one-agent execution cannot establish global
        versus per-agent compatibility. Unqualified shape-changing functions refuse.

        A shape names the leading registry axes of a value: ``scalar`` (no axis),
        ``agent`` (one row per agent), ``affordance`` (one row per affordance) or
        ``payload`` (a vector/tensor value, refused). ``scalar`` joins with anything;
        two distinct axes refuse, because the evaluator aligns trailing dimensions and
        would combine them by coincidence of extents.
        A temporal operator (admitted when ``temporal``) is pointwise in time: its result
        has its first argument's shape, and its other arguments are literals
        (``vfs.history.expression_history`` proves that before this runs).
        """
        if isinstance(node, Constant):
            return "scalar"
        if isinstance(node, Variable):
            if node.name not in shapes:
                raise TypeCheckError(f"Variable '{node.name}' has no qualified expression shape")
            return shapes[node.name]
        if isinstance(node, PathAccess):
            path = ".".join(node.segments)
            if path not in shapes:
                raise TypeCheckError(f"Expression path '{path}' has no qualified variable output shape")
            return shapes[path]
        if isinstance(node, UnaryOp):
            return cls._shape(node.operand, shapes, temporal=temporal)
        if isinstance(node, FunctionCall) and node.function_name in TEMPORAL_FUNCTIONS:
            if not temporal:
                raise TypeCheckError(
                    f"Expression function '{node.function_name}' reads temporal history, which only global and agent "
                    "variable expressions keep. Declare a variable with that expression and read the variable here."
                )
            shape = cls._shape(node.arguments[0], shapes, temporal=temporal)
            if shape == "payload":
                raise TypeCheckError(f"Expression function '{node.function_name}' reads scalar or bool history only, not a vector/tensor")
            return shape
        if isinstance(node, BinaryOp):
            operands = [node.left, node.right]
        elif isinstance(node, IfThenElse):
            operands = [node.condition, node.true_branch, node.false_branch]
        elif isinstance(node, FunctionCall):
            pointwise = {
                "max",
                "min",
                "abs",
                "clamp",
                "clamp01",
                "sigmoid",
                "tanh",
                "smoothstep",
                "threshold",
                "where",
                "time_in_window",
                "phase_sin",
                "phase_cos",
                "masked_add",
                "masked_set",
                "perlin_noise",
                "simplex_noise",
            }
            stacked = {"mean", "variance", "sum", "product", "min_all", "max_all", "count_where", "argmin", "argmax", "all", "any"}
            if node.function_name not in pointwise | stacked:
                raise TypeCheckError(f"Expression function '{node.function_name}' has no qualified variable output shape")
            operands = list(node.arguments)
            if node.function_name in stacked:
                argument_shapes = {cls._shape(argument, shapes, temporal=temporal) for argument in operands}
                if len(argument_shapes) != 1:
                    raise TypeCheckError(f"Expression function '{node.function_name}' requires equal argument shapes")
        else:
            raise TypeCheckError(f"Expression node '{type(node).__name__}' has no qualified variable output shape")
        operand_shapes = {cls._shape(operand, shapes, temporal=temporal) for operand in operands}
        if "payload" in operand_shapes:
            raise TypeCheckError("Expression shape with vector/tensor payloads is not supported")
        axes = operand_shapes - {"scalar"}
        if not axes:
            return "scalar"
        if len(axes) == 1:
            (axis,) = axes
            return axis
        raise TypeCheckError(
            f"Expression combines values of different shapes {sorted(axes)}; their axes do not align, so the result "
            "would depend on coincidences of extent"
        )

    def compile_item_profile(
        self,
        profile_name: str,
        variables: Sequence[VariableDeclaration],
        bar_schema: dict[str, str],
    ) -> CompiledItemProfile:
        """Compile item VFS profile.

        Args:
            profile_name: Named item schema from the variables declaration
            bar_schema: Type schema for bars (for expression type checking)

        Returns:
            Compiled item profile with variables in topological order

        Raises:
            ValueError: If circular dependencies detected
        """
        for item_var in variables:
            if item_var.expression is not None:
                raise ValueError(
                    f"Item-profile variable '{item_var.id}' declares an expression, but item-profile "
                    "expressions have no evaluator (hamlet-bc0a5deeff) — nothing would ever run it. "
                    "Declare initial_value and drive the variable via effects, or wait for the "
                    "evaluation build. Refusing loudly beats silent inertness."
                )

        # Sort variables in dependency order
        sorted_vars, _ = self.topological_sort_with_dependencies(variables)

        # Build variable schema (item profiles can reference bars)
        var_schema: dict[str, str] = {}

        # Items can reference bars but not global/agent VFS
        # (items are isolated instances)
        var_schema.update(bar_schema)

        # Compile each variable
        compiled_vars: list[CompiledVariable] = []

        for var in sorted_vars:
            compiled = self.compile_variable(var, var_schema)
            if var.type in {"agent_ref", "item_ref", "affordance_ref", "effect_ref"} and var.initial_value is None:
                compiled.initial_value = -1
            compiled_vars.append(compiled)

            # Add this variable to schema for subsequent variables
            var_schema[var.id] = "float" if var.type == "scalar" else var.type

        return CompiledItemProfile(
            profile_name=profile_name,
            variables=compiled_vars,
        )
