"""VFS Transition Compiler support for declarative transition rules."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, fields, replace
from typing import Any, ClassVar, Protocol, cast

import torch

from townlet.config.interaction_type import INTERACTION_TYPES, PROGRESS_INTERACTION_TYPES
from townlet.vfs import vtc_kernels
from townlet.vfs.profiles import CompiledGlobalProfile, VFSProfileCompiler
from townlet.vfs.schema import VariableDef, VariableScope, WriteSpec
from townlet.vfs.storage_dtype import BATCH_ROW_REFERENCE_TYPES, admitted_write_result_types, to_storage_dtype
from townlet.vfs.transition_graph import TransitionPhaseGraph
from townlet.world.expression import ASTNode, ExpressionParser, FunctionCall, IfThenElse, PathAccess, Variable, read_paths
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.functions import FUNCTION_SPECS
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError


class VTCActionWriteSource(Protocol):
    """Minimal action shape needed by the VTC action-write compiler."""

    @property
    def id(self) -> int: ...

    @property
    def name(self) -> str: ...

    @property
    def source_affordance(self) -> str | None: ...

    @property
    def writes(self) -> Sequence[WriteSpec | Mapping[str, Any]]: ...


class VTCThresholdCascadeSource(Protocol):
    """Minimal cascade shape needed by the VTC threshold-cascade compiler."""

    @property
    def source(self) -> str: ...

    @property
    def target(self) -> str: ...

    @property
    def threshold(self) -> float: ...

    @property
    def strength(self) -> float: ...


class VTCPassiveDepletionSource(Protocol):
    """Minimal meter shape needed by the VTC passive-depletion compiler."""

    @property
    def name(self) -> str: ...

    @property
    def depletion(self) -> Any: ...

    @property
    def bounds(self) -> Any: ...


class VTCModulationSource(Protocol):
    """Minimal modulation shape needed by the VTC modulation compiler."""

    @property
    def bar(self) -> str: ...

    @property
    def affordances(self) -> Sequence[str]: ...

    @property
    def type(self) -> str: ...

    @property
    def threshold(self) -> float: ...

    @property
    def min_multiplier(self) -> float: ...


class VTCAffordanceGateSource(Protocol):
    """Minimal affordance shape needed by the VTC operating-hour gate compiler."""

    @property
    def name(self) -> str: ...

    @property
    def opening_hours(self) -> Any: ...


class VTCInteractionProgressSource(Protocol):
    """Minimal affordance shape needed by the VTC interaction-progress compiler."""

    @property
    def name(self) -> str: ...

    @property
    def interaction_type(self) -> str: ...

    @property
    def duration_ticks(self) -> int | None: ...


class VTCTerminalConditionSource(Protocol):
    """Minimal meter shape needed by the VTC terminal-condition compiler."""

    @property
    def name(self) -> str: ...

    @property
    def bounds(self) -> Any: ...


class VTCTransitionRuleSource(Protocol):
    """Minimal rule shape needed by the VTC transition-rule compiler."""

    @property
    def id(self) -> str: ...

    @property
    def phase(self) -> str: ...

    @property
    def condition(self) -> str | None: ...

    @property
    def writes(self) -> Sequence[Mapping[str, Any] | WriteSpec]: ...


@dataclass(frozen=True)
class CompiledVTCActionWrite:
    """A parsed VTC action write with the metadata needed for masked execution."""

    action_id: int
    action_name: str
    source_affordance: str | None
    affordance_index: int | None
    variable_id: str
    target_scope: VariableScope
    expression: str
    expression_ast: ASTNode
    condition: str | None
    condition_ast: ASTNode | None
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str


@dataclass(frozen=True)
class CompiledVTCThresholdCascade:
    """A parsed VTC threshold-delta relationship rule."""

    rule_id: str
    kind: str
    source_variable_id: str
    variable_id: str
    expression: str
    expression_ast: ASTNode
    condition: str
    condition_ast: ASTNode
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str
    cascade_threshold: float
    cascade_strength: float


@dataclass(frozen=True)
class CompiledVTCPassiveDepletion:
    """A parsed VTC passive-depletion rule."""

    rule_id: str
    kind: str
    source_variable_id: str
    variable_id: str
    expression: str
    expression_ast: ASTNode
    condition: str | None
    condition_ast: ASTNode | None
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str
    passive_rate: float


@dataclass(frozen=True)
class CompiledVTCBoundsClamp:
    """A compiled bounds-invariant rule for the `clamp_and_validate` phase.

    One rule per declared meter, sourced from `bars.*.bounds`. This is the
    end-of-transition invariant net, not a per-write clamp: the per-write clamps
    (VTC rule clamps and the environment-level ceilings retained by PDR-0014 B3 /
    PDR-0015) stay where they are because their mid-tick timing is semantic.
    """

    rule_id: str
    kind: str
    source_variable_id: str
    variable_id: str
    expression: str
    condition: str | None
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str


@dataclass(frozen=True)
class CompiledVTCModulation:
    """A parsed VTC affordance modulation rule."""

    rule_id: str
    kind: str
    source_variable_id: str
    target_affordance_id: str
    variable_id: str
    expression: str
    expression_ast: ASTNode
    condition: str | None
    condition_ast: ASTNode | None
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str
    modulation_threshold: float
    min_multiplier: float


@dataclass(frozen=True)
class CompiledVTCAffordanceGate:
    """A parsed VTC operating-hour gate for one affordance."""

    rule_id: str
    kind: str
    source_variable_id: str
    target_affordance_id: str
    variable_id: str
    expression: str
    expression_ast: ASTNode
    condition: str | None
    condition_ast: ASTNode | None
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str


@dataclass(frozen=True)
class CompiledVTCInteractionProgress:
    """A parsed VTC progress-advance rule for one multi-tick affordance."""

    rule_id: str
    kind: str
    source_variable_id: str
    target_affordance_id: str
    variable_id: str
    expression: str
    expression_ast: ASTNode
    condition: str | None
    condition_ast: ASTNode | None
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str
    duration_ticks: int


@dataclass(frozen=True)
class CompiledVTCInteractionCompletionBonus:
    """A parsed VTC completion event rule for one multi-tick affordance."""

    rule_id: str
    kind: str
    source_variable_id: str
    target_affordance_id: str
    variable_id: str
    expression: str
    expression_ast: ASTNode
    condition: str | None
    condition_ast: ASTNode | None
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str
    duration_ticks: int


@dataclass(frozen=True)
class CompiledVTCTerminalCondition:
    """A parsed VTC terminal-condition rule for one lethal meter bound."""

    rule_id: str
    kind: str
    source_variable_id: str
    variable_id: str
    expression: str
    expression_ast: ASTNode
    condition: str | None
    condition_ast: ASTNode | None
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str
    operator: str
    threshold: float


@dataclass(frozen=True)
class CompiledVTCTransitionRule:
    """A parsed VTC transition rule: one condition-gated write to a VFS variable."""

    rule_id: str
    effect: str | None
    variable_id: str
    expression: str
    expression_ast: ASTNode
    condition: str | None
    condition_ast: ASTNode | None
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str
    target_scope: VariableScope
    reads: tuple[str, ...] = field(metadata={"derived": True})
    """The ids of the variables (and meter bars) the expression and condition read, sorted.

    Derived from the two ASTs at compile time, never authored (VFS round-2 S8): every
    spelling the write namespace admits (``x``, ``vfs.x``, ``self.vfs.x``,
    ``target.vfs.x``, ``bar.x``, ``self.bar.x``, ``target.bar.x``) resolves to its
    target id. The ASTs are already identity, so this is not hashed."""
    world_columns: frozenset[str] = field(metadata={"derived": True})
    """Globals a rule targeting affordance state reads as its world's column (S1).

    A global is ``[worlds, ...]`` and affordance state ``[worlds, affordances, ...]``;
    evaluated as stored, the evaluator would align the global's world axis with the
    affordance axis. Each listed global is given a singleton affordance axis first, so
    it spreads along its own world's affordance rows. Derived from the targets' declared
    scopes (already identity in ``vfs_hash``), so it is not rule identity."""


@dataclass(frozen=True)
class _VTCActionWriteEffect:
    """Computed action-write candidate for one atomic VTC phase commit."""

    write: CompiledVTCActionWrite
    expression_value: torch.Tensor
    write_mask: torch.Tensor


@dataclass(frozen=True)
class _VTCTransitionRuleEffect:
    """Computed social-rule candidate for one atomic VTC phase commit."""

    rule: CompiledVTCTransitionRule
    expression_value: torch.Tensor
    write_mask: torch.Tensor


@dataclass(frozen=True)
class VTCInteractionProgressResult:
    """Result of one VTC interaction-progress transition step."""

    interaction_progress: torch.Tensor
    ticks_done: torch.Tensor
    completion_mask: torch.Tensor
    completion_affordances: list[str | None]
    last_affordances: list[str | None]
    last_positions: torch.Tensor


@dataclass(frozen=True)
class VTCWriteResult:
    """A snapshot plus selected write targets, before composition or equality."""

    values: dict[str, torch.Tensor]
    attempted_targets: frozenset[str]


@dataclass(frozen=True)
class VTCWriteRefusal:
    """One authored transition write the compiled schedule cannot apply.

    ``kind`` is ``phase`` (scheduled where it cannot run), ``scope`` (its target has
    no row the write can address) or ``type`` (its expression or condition does not
    type-check against the declared target); the universe compiler maps it to an
    error code.
    """

    origin_key: str
    kind: str
    message: str


@dataclass(frozen=True)
class VTCWriteTarget:
    """Declared identity of one state an authored write may name.

    ``type`` is the declared VFS type (``scalar``, ``bool``, ``agent_ref``, ...); a
    meter bar is agent-scoped ``scalar`` storage with ``meter=True`` so the expression
    schema also admits its ``bar.<name>`` spelling.
    """

    scope: VariableScope
    type: str
    meter: bool
    expression: VTCExpressionSource | None
    """The variable's compiled expression as a write reads it; None for storage (VFS round-2 S4)."""


@dataclass(frozen=True)
class VTCExpressionSource:
    """An expression variable as a transition write or rule reads it (VFS round-2 S4).

    An expression variable is a name for a function of state. A write that reads one
    reads that function evaluated on the state the write sees, not the value the last
    profile evaluation stored: ``ast`` (the expression with every inlinable expression
    variable it reads substituted, recursively) is substituted into the write's
    expression and condition at compile, so the write needs no evaluation order.

    ``stored_because`` is None for such a context-free expression. Otherwise it names
    the function that needs evaluation-time context a transition phase does not carry
    (temporal history, the engine step, positions): re-evaluating a history operator
    mid-tick would read its buffers a second time, so the expression is not inlined
    and a write reads the value its last profile evaluation stored, which is the value
    the observation the action was chosen on showed. A ``tick``-lifetime one has no
    stored value by then (tick state resets before the action phases), so reading it
    from a write refuses at compile.
    """

    ast: ASTNode
    lifetime: str
    stored_because: str | None


def vtc_expression_sources(profiles: Sequence[CompiledGlobalProfile | None]) -> dict[str, VTCExpressionSource]:
    """Every compiled global/agent expression variable as a write reads it, by id.

    ``profiles`` come in evaluation order (global, then agent), each profile's
    variables topologically sorted, so every expression variable an expression reads is
    resolved before the expression itself; cycles were refused by the profile compiler.
    """
    sources: dict[str, VTCExpressionSource] = {}
    for profile in profiles:
        if profile is None:
            continue
        for variable in profile.variables:
            if variable.ast is None:
                continue
            context_call = _context_bound_call(variable.ast)
            if context_call is not None:
                sources[variable.name] = VTCExpressionSource(variable.ast, variable.lifetime, context_call)
                continue
            inlined = {name: source.ast for name, source in sources.items() if source.stored_because is None}
            sources[variable.name] = VTCExpressionSource(_substitute_reads(variable.ast, inlined), variable.lifetime, None)
    return sources


def vtc_write_targets(
    vfs_variables: Iterable[VariableDef],
    meter_names: Iterable[str],
    expression_profiles: Sequence[CompiledGlobalProfile | None],
) -> dict[str, VTCWriteTarget]:
    """Every state a VTC write expression may read or write, by bare name, with its expression if it has one."""
    expressions = vtc_expression_sources(expression_profiles)
    targets = {
        variable.id: VTCWriteTarget(
            VariableScope(variable.scope), variable.type, meter=False, expression=expressions.pop(variable.id, None)
        )
        for variable in vfs_variables
    }
    if expressions:
        raise ValueError(f"Compiled expression variable(s) {sorted(expressions)} have no runtime VFS variable")
    targets.update({name: VTCWriteTarget(VariableScope.AGENT, "scalar", meter=True, expression=None) for name in meter_names})
    return targets


def _context_bound_call(ast: ASTNode) -> str | None:
    """The first function ``ast`` calls that needs evaluation-time context, described; None if it is context-free."""
    found: list[str] = []

    def visit(value: Any) -> None:
        if found:
            return
        if isinstance(value, FunctionCall):
            spec = FUNCTION_SPECS.get(value.function_name)
            if spec is not None and spec.requires:
                found.append(f"'{value.function_name}', which needs {' and '.join(spec.requires)}")
                return
        if isinstance(value, ASTNode):
            for ast_field in fields(value):
                visit(getattr(value, ast_field.name))
        elif isinstance(value, list | tuple):
            for item in value:
                visit(item)

    visit(ast)
    return found[0] if found else None


def _substitute_reads(node: ASTNode, replacements: Mapping[str, ASTNode]) -> ASTNode:
    """``node`` with every read (``Variable`` or ``PathAccess``) named in ``replacements`` replaced by its AST."""
    if isinstance(node, Variable) and node.name in replacements:
        return replacements[node.name]
    if isinstance(node, PathAccess) and ".".join(node.segments) in replacements:
        return replacements[".".join(node.segments)]

    def substitute(value: Any) -> Any:
        if isinstance(value, ASTNode):
            return _substitute_reads(value, replacements)
        if isinstance(value, list):
            return [substitute(item) for item in value]
        if isinstance(value, tuple):
            return tuple(substitute(item) for item in value)
        return value

    changes = {}
    for ast_field in fields(node):
        value = getattr(node, ast_field.name)
        substituted = substitute(value)
        if substituted != value:
            changes[ast_field.name] = substituted
    return replace(node, **changes) if changes else node


def _inline_expression_reads(
    targets: Mapping[str, VTCWriteTarget],
    *,
    expression_ast: ASTNode,
    expression: str,
    condition_ast: ASTNode | None,
    condition: str | None,
    prefix: str,
) -> tuple[ASTNode, ASTNode | None] | str:
    """A write's expression and condition with every expression variable they read inlined (VFS round-2 S4).

    Returns the substituted ASTs, or why the write refuses: it calls a function that
    needs context a transition phase does not carry, or it reads (directly or through
    an inlined expression) a context-bound ``tick``-lifetime expression variable,
    which has no stored value while the transition phases run.
    """
    replacements: dict[str, ASTNode] = {}
    stored: dict[str, tuple[str, VTCExpressionSource]] = {}
    for name, target in targets.items():
        if target.expression is None:
            continue
        for spelling in _target_spellings(name, target):
            if target.expression.stored_because is None:
                replacements[spelling] = target.expression.ast
            else:
                stored[spelling] = (name, target.expression)
    checks = [("expression", expression_ast, expression)]
    if condition_ast is not None:
        assert condition is not None
        checks.append(("condition", condition_ast, condition))
    inlined: list[ASTNode] = []
    for kind, ast, text in checks:
        context_call = _context_bound_call(ast)
        if context_call is not None:
            return (
                f"{prefix} {kind} '{text}' calls {context_call}, which a transition write does not carry. "
                "Declare the quantity as an expression variable and read it by name."
            )
        substituted = _substitute_reads(ast, replacements)
        for path in sorted(read_paths(substituted)):
            if path not in stored:
                continue
            name, source = stored[path]
            if source.lifetime == "tick":
                return (
                    f"{prefix} {kind} '{text}' reads tick-lifetime expression variable '{name}', whose expression calls "
                    f"{source.stored_because}, so it is not inlined and a write reads its stored value. Tick-lifetime state "
                    "resets before the action phases, so a write would only ever see its declared literal. "
                    f"Declare '{name}' with lifetime episode."
                )
        inlined.append(substituted)
    return inlined[0], (inlined[1] if condition_ast is not None else None)


_SCOPE_SHAPES: dict[VariableScope, str] = {
    VariableScope.GLOBAL: "scalar",
    VariableScope.AGENT: "agent",
    VariableScope.AFFORDANCE: "affordance",
}
"""The leading registry axes a read of each scope yields (``VFSProfileCompiler.expression_shape`` labels).

A vector/tensor-typed variable carries the same label: its payload width is the type
checker's to prove (``vecNf`` against ``scalar``); the shape proof proves the axes.
Scopes absent here have no registry row, so a write expression cannot read them."""


def _write_expression_namespace(targets: Mapping[str, VTCWriteTarget]) -> tuple[dict[str, str], dict[str, str]]:
    """The type schema and the shape map of a VTC write expression, mirroring the runtime ExecutionContext.

    The context resolves a bare name against the phase snapshot (every registry
    variable, every meter bar, and ``agent_id``), ``bar.<meter>`` against the bars, and
    ``vfs.`` / ``self.vfs.`` / ``target.vfs.`` chains against the snapshot. Every
    spelling reads the whole registry tensor, so every spelling carries its scope's shape.
    """
    schema: dict[str, str] = {"agent_id": "int"}
    shapes: dict[str, str] = {"agent_id": "agent"}
    for name, target in targets.items():
        result_type = "float" if target.type == "scalar" else target.type
        keys = [name, f"vfs.{name}", f"self.vfs.{name}", f"target.vfs.{name}"]
        if target.meter:
            keys += [f"bar.{name}", f"self.bar.{name}", f"target.bar.{name}"]
        for key in keys:
            schema[key] = result_type
            if target.scope in _SCOPE_SHAPES:
                shapes[key] = _SCOPE_SHAPES[target.scope]
    return schema, shapes


def _write_shape_refusal(
    *,
    expression_ast: ASTNode,
    expression: str,
    condition_ast: ASTNode | None,
    condition: str | None,
    shapes: Mapping[str, str],
    admitted_expression: frozenset[str],
    admitted_condition: frozenset[str],
    target_id: str,
    target_scope: VariableScope,
    prefix: str,
) -> str | None:
    """Why a write's expression or condition has a shape its target's scope cannot hold, or None.

    Runs after the type check: the type proves the payload, this proves the axes, so
    an affordance read into an agent row, or an agent value into a global target,
    refuses here instead of failing (or broadcasting by coincidence) at step.
    """
    checks = [("expression", expression_ast, expression, admitted_expression)]
    if condition_ast is not None:
        assert condition is not None
        checks.append(("condition", condition_ast, condition, admitted_condition))
    for kind, ast, text, admitted in checks:
        try:
            shape = VFSProfileCompiler.expression_shape(ast, dict(shapes))
        except TypeCheckError as exc:
            return f"{prefix} {kind} '{text}' has no provable shape: {exc}"
        if shape in admitted:
            continue
        return (
            f"{prefix} {kind} '{text}' is {shape}-shaped, but its target '{target_id}' has declared scope "
            f"'{target_scope.value}', which admits {' or '.join(sorted(admitted))}-shaped values."
        )
    return None


def _write_type_refusal(
    checker: TypeChecker,
    *,
    expression_ast: ASTNode,
    expression: str,
    condition_ast: ASTNode | None,
    condition: str | None,
    target_id: str,
    target_type: str,
    prefix: str,
) -> str | None:
    """Why a write's expression or condition cannot type-check against its target, or None."""
    try:
        result_type = checker.check(expression_ast)
    except TypeCheckError as exc:
        return f"{prefix} expression '{expression}' does not type-check: {exc}"
    admitted = admitted_write_result_types(target_type)
    if result_type not in admitted:
        return (
            f"{prefix} assigns a {result_type} expression '{expression}' to '{target_id}', declared {target_type} "
            f"(admits {', '.join(sorted(admitted))}). Storage writes never coerce dtype; author an expression of the declared type."
        )
    if target_type in BATCH_ROW_REFERENCE_TYPES and not read_paths(expression_ast):
        constant = _constant_value(expression_ast)
        if constant != -1:
            return (
                f"{prefix} assigns the constant {constant} to {target_type} '{target_id}'. A constant is the same "
                "batch row in every world, and the batch is independent worlds (S1), so in every other world it names "
                "another world's entity. Write -1 (null), or a reference this world holds (agent_id for its agent)."
            )
    if target_type in BATCH_ROW_REFERENCE_TYPES and not _world_local_reference(expression_ast, target_type, checker.schema):
        own = ""
        if target_type == "agent_ref":
            own = "agent_id (the acting agent), "
        return (
            f"{prefix} assigns '{expression}' to {target_type} '{target_id}', which is not provably an entity of the "
            "writing world. The batch is independent worlds (S1), so a reference holds a row of its own world or null; "
            f"a reference write is -1 (null), {own}a {target_type} read of this world's state, or where(...) / "
            "if-then-else choosing between those. Arithmetic on a reference is refused: it can name any row."
        )
    if condition_ast is None:
        return None
    try:
        condition_type = checker.check(condition_ast)
    except TypeCheckError as exc:
        return f"{prefix} condition '{condition}' does not type-check: {exc}"
    if condition_type != "bool":
        return f"{prefix} condition '{condition}' is {condition_type}, not bool."
    return None


def _constant_value(ast: ASTNode) -> int:
    """The integer a read-free expression evaluates to."""
    return int(Evaluator(ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})).evaluate(ast))


def _world_local_reference(ast: ASTNode, target_type: str, schema: Mapping[str, str]) -> bool:
    """Whether ``ast`` provably names an entity of the writing world, or null, for a ``target_type`` reference.

    A syntactic rule, since the type system cannot prove row membership: null (a
    read-free expression equal to -1), ``agent_id`` for an ``agent_ref`` (the acting
    agent's own row, its world under S1), a read of a ``target_type`` reference (the
    registry refuses any stored reference outside its row's world), or ``where`` /
    if-then-else whose two value branches are themselves such. Anything else, such as
    ``agent_id * 0``, can name another world's row and is refused.
    """
    if not read_paths(ast):
        return _constant_value(ast) == -1
    if isinstance(ast, Variable | PathAccess):
        if isinstance(ast, Variable):
            path = ast.name
        else:
            path = ".".join(ast.segments)
        return (target_type == "agent_ref" and path == "agent_id") or schema.get(path) == target_type
    if isinstance(ast, IfThenElse):
        branches = [ast.true_branch, ast.false_branch]
    elif isinstance(ast, FunctionCall) and ast.function_name == "where" and len(ast.arguments) == 3:
        branches = list(ast.arguments[1:])
    else:
        return False
    return all(_world_local_reference(branch, target_type, schema) for branch in branches)


class VTCWriteRefusalError(ValueError):
    """Transition writes refused at compile: their phase or their target's scope cannot apply them.

    ``origin_key`` is the source-map key of the authored write, so the universe
    compiler can locate each refusal at ``file:line``.
    """

    def __init__(self, refusals: tuple[VTCWriteRefusal, ...]) -> None:
        self.refusals = refusals
        super().__init__("\n".join(refusal.message for refusal in refusals))


def _unknown_phase_reason(phase: str) -> str:
    return f"phase '{phase}', which is not a transition phase"


def _clamp_in_dtype(value: torch.Tensor, clamp: tuple[float, float] | None) -> torch.Tensor:
    """Clamp a storage-typed candidate without changing its dtype.

    ``torch.clamp`` promotes integer storage to float when the authored bounds are
    floats; a clamp bounds a value, it never retypes it.
    """
    if clamp is None:
        return value
    low, high = clamp
    return torch.clamp(value, min=low, max=high).to(dtype=value.dtype)


@dataclass(frozen=True)
class VTCActionWriteProgram:
    """Executable collection of compiled VTC action writes."""

    writes: tuple[CompiledVTCActionWrite, ...]

    def apply(
        self,
        *,
        actions: torch.Tensor,
        vfs_state: Mapping[str, torch.Tensor],
        bars_state: Mapping[str, torch.Tensor],
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> VTCWriteResult:
        """Apply compiled VTC writes to a VFS state snapshot using action and active-agent masks."""
        if actions.shape != active_mask.shape:
            raise ValueError(f"actions shape {tuple(actions.shape)} must match active_mask shape {tuple(active_mask.shape)}")

        # Bar names and variable ids are disjoint: the universe compiler's symbol
        # table refuses the collision (SYMBOL_METER_COLLISION).
        updated = {name: value.to(device=device).clone() for name, value in vfs_state.items()}
        updated.update({bar_name: value.to(device=device).clone() for bar_name, value in bars_state.items()})
        bar_names = set(bars_state)
        actions_on_device = actions.to(device=device)
        active_mask_on_device = active_mask.to(device=device)

        attempted_targets: set[str] = set()
        for phase_writes in self._iter_phase_groups():
            phase_snapshot = dict(updated)
            phase_effects = self._compute_phase_effects(
                phase_writes=phase_writes,
                phase_snapshot=phase_snapshot,
                bar_names=bar_names,
                actions=actions_on_device,
                active_mask=active_mask_on_device,
                device=device,
            )
            attempted_targets.update(effect.write.variable_id for effect in phase_effects if bool(effect.write_mask.any()))
            updated = self._commit_phase_effects(phase_snapshot, phase_effects)

        return VTCWriteResult(updated, frozenset(attempted_targets))

    def _iter_phase_groups(self) -> list[tuple[CompiledVTCActionWrite, ...]]:
        phase_groups: list[tuple[CompiledVTCActionWrite, ...]] = []
        current_phase: str | None = None
        current_group: list[CompiledVTCActionWrite] = []

        for write in self.writes:
            if current_phase is None:
                current_phase = write.phase
            if write.phase != current_phase:
                phase_groups.append(tuple(current_group))
                current_group = []
                current_phase = write.phase
            current_group.append(write)

        if current_group:
            phase_groups.append(tuple(current_group))
        return phase_groups

    def _compute_phase_effects(
        self,
        *,
        phase_writes: Sequence[CompiledVTCActionWrite],
        phase_snapshot: Mapping[str, torch.Tensor],
        bar_names: set[str],
        actions: torch.Tensor,
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> tuple[_VTCActionWriteEffect, ...]:
        phase_effects: list[_VTCActionWriteEffect] = []
        context_vfs = dict(phase_snapshot)
        context_vfs.setdefault("agent_id", torch.arange(actions.shape[0], device=device))
        context = ExecutionContext(
            bars={name: phase_snapshot[name] for name in bar_names},
            vfs=context_vfs,
            affordances={},
            temporal={},
            device=device,
            num_agents=actions.shape[0],
        )
        evaluator = Evaluator(context)

        for write in phase_writes:
            if write.variable_id not in phase_snapshot:
                raise KeyError(f"VTC action write targets unknown VFS variable '{write.variable_id}'")

            target_snapshot = phase_snapshot[write.variable_id]
            write_mask = self._build_write_mask(write, actions, active_mask, evaluator)
            expression_value = self._evaluate_tensor(evaluator, write.expression_ast, "expression", write)
            phase_effects.append(
                _VTCActionWriteEffect(
                    write=write,
                    expression_value=self._coerce_expression_tensor(expression_value, target_snapshot, actions, write),
                    write_mask=write_mask,
                )
            )

        return tuple(phase_effects)

    def _commit_phase_effects(
        self,
        phase_snapshot: Mapping[str, torch.Tensor],
        phase_effects: Sequence[_VTCActionWriteEffect],
    ) -> dict[str, torch.Tensor]:
        phase_values = dict(phase_snapshot)
        priority_state: dict[str, torch.Tensor] = {}

        for effect in phase_effects:
            phase_value = phase_values[effect.write.variable_id]
            phase_values[effect.write.variable_id] = self._apply_composed_write(
                write=effect.write,
                phase_value=phase_value,
                expression_value=effect.expression_value,
                write_mask=effect.write_mask,
                priority_state=priority_state,
            )

        return phase_values

    def _apply_composed_write(
        self,
        *,
        write: CompiledVTCActionWrite,
        phase_value: torch.Tensor,
        expression_value: torch.Tensor,
        write_mask: torch.Tensor,
        priority_state: dict[str, torch.Tensor],
    ) -> torch.Tensor:
        # The compiler admits a claim composition only as an affordance occupancy claim.
        if write.composition == "claim_if_free":
            return self._apply_affordance_claim_if_free(write, phase_value, expression_value, write_mask)
        if write.composition == "capacity_claim":
            return self._apply_affordance_capacity_claim(write, phase_value, expression_value, write_mask)

        candidate = self._compose_candidate(write, phase_value, expression_value)
        candidate = self._apply_optional_clamp(write, candidate)

        if write.composition == "priority_write":
            return self._apply_priority_write(write, phase_value, candidate, write_mask, priority_state)

        broadcast_mask = self._broadcast_agent_mask(write_mask, phase_value, write)
        return cast(torch.Tensor, vtc_kernels.apply_masked_candidate(phase_value, candidate, broadcast_mask))

    def _compose_candidate(self, write: CompiledVTCActionWrite, phase_value: torch.Tensor, expression_value: torch.Tensor) -> torch.Tensor:
        # expression_value is already storage-typed (_coerce_expression_tensor).
        expression = expression_value
        if write.composition in {"overwrite", "last_write_wins", "priority_write", "clamp"}:
            return expression
        if write.composition == "additive_delta":
            return phase_value + expression
        if write.composition == "multiplicative_modifier":
            return phase_value * expression
        if write.composition == "min":
            return torch.minimum(phase_value, expression)
        if write.composition == "max":
            return torch.maximum(phase_value, expression)
        raise NotImplementedError(f"VTC action write composition '{write.composition}' is not implemented yet")

    @staticmethod
    def _capacity_from_clamp(write: CompiledVTCActionWrite) -> int:
        assert write.clamp is not None
        capacity_value = write.clamp[1]
        capacity = int(capacity_value)
        if capacity < 0 or float(capacity) != float(capacity_value):
            raise ValueError(f"VTC capacity_claim write '{write.telemetry_label}' requires non-negative integer clamp high")
        return capacity

    def _apply_affordance_claim_if_free(
        self,
        write: CompiledVTCActionWrite,
        phase_value: torch.Tensor,
        expression_value: torch.Tensor,
        write_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Each world's claimant takes its own world's source-affordance row when that row is free.

        Affordance state is per world (S1: storage ``[worlds, affordances, ...]``), and a
        world has one agent, so a claim never contends with another world's: there is
        no cross-world "lower index wins".
        """
        affordance_index = self._require_affordance_index(write, phase_value)
        rows = phase_value[:, affordance_index]  # [worlds, ...]
        claim = write_mask.bool() & self._row_free_for_claim(rows)
        candidate = phase_value.clone()
        candidate[:, affordance_index] = torch.where(self._broadcast_rows(claim, rows), expression_value, rows)
        return candidate

    def _apply_affordance_capacity_claim(
        self,
        write: CompiledVTCActionWrite,
        phase_value: torch.Tensor,
        expression_value: torch.Tensor,
        write_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Each world's claimant takes the first free slot of its own world's source affordance."""
        if write.clamp is None:
            raise ValueError(f"VTC capacity_claim write '{write.telemetry_label}' requires clamp high to declare capacity")
        if phase_value.dim() < 3:
            raise ValueError(
                f"VTC affordance capacity_claim write '{write.telemetry_label}' requires target shape [worlds, affordances, slots, ...]"
            )

        affordance_index = self._require_affordance_index(write, phase_value)
        capacity = self._capacity_from_clamp(write)
        if capacity > phase_value.shape[2]:
            raise ValueError(
                f"VTC affordance capacity_claim write '{write.telemetry_label}' declares capacity {capacity} "
                f"but target only has {phase_value.shape[2]} slots"
            )
        if capacity == 0:
            return phase_value

        slots = phase_value[:, affordance_index, :capacity]  # [worlds, capacity, ...]
        free = self._slot_free_per_world(slots)  # [worlds, capacity]
        has_free = free.any(dim=1)
        first_free = torch.argmax(free.to(torch.int8), dim=1)  # first True per world
        claim = write_mask.bool() & has_free
        chosen = torch.zeros_like(free)
        chosen[torch.arange(free.shape[0], device=free.device), first_free] = True
        chosen &= claim.unsqueeze(1)
        payload = expression_value.unsqueeze(1).expand_as(slots)
        candidate = phase_value.clone()
        candidate[:, affordance_index, :capacity] = torch.where(self._broadcast_rows(chosen, slots), payload, slots)
        return candidate

    @staticmethod
    def _broadcast_rows(mask: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """`mask` with trailing singleton axes added until it broadcasts over `target`."""
        while mask.dim() < target.dim():
            mask = mask.unsqueeze(-1)
        return mask

    @staticmethod
    def _slot_free_per_world(slots: torch.Tensor) -> torch.Tensor:
        """Free slots ``[worlds, capacity]`` of a ``[worlds, capacity, ...]`` slot block."""
        if slots.dim() == 2:
            return ~slots if slots.dtype == torch.bool else slots < 0
        if slots.dtype == torch.bool:
            return ~slots.flatten(start_dim=2).any(dim=2)
        return (slots < 0).flatten(start_dim=2).all(dim=2)

    @staticmethod
    def _targets_affordance_occupancy(write: CompiledVTCActionWrite) -> bool:
        # The compiler admits an affordance-scoped target only as an occupancy claim.
        return write.target_scope == VariableScope.AFFORDANCE

    @staticmethod
    def _require_affordance_index(write: CompiledVTCActionWrite, target: torch.Tensor) -> int:
        if write.affordance_index is None:
            raise ValueError(f"VTC affordance occupancy write '{write.telemetry_label}' has no source affordance index")
        if target.dim() < 2:
            raise ValueError(
                f"VTC affordance occupancy write '{write.telemetry_label}' needs [worlds, affordances, ...] storage, "
                f"got shape {tuple(target.shape)}"
            )
        if write.affordance_index < 0 or write.affordance_index >= target.shape[1]:
            raise ValueError(
                f"VTC affordance occupancy write '{write.telemetry_label}' source affordance index {write.affordance_index} "
                f"is outside target extent {target.shape[1]}"
            )
        return write.affordance_index

    @staticmethod
    def _row_free_for_claim(value: torch.Tensor) -> torch.Tensor:
        if value.dtype == torch.bool:
            return ~VTCActionWriteProgram._row_any(value)
        return VTCActionWriteProgram._row_all(value < 0)

    @staticmethod
    def _row_all(mask: torch.Tensor) -> torch.Tensor:
        if mask.dim() <= 1:
            return mask.bool()
        return mask.bool().flatten(start_dim=1).all(dim=1)

    @staticmethod
    def _row_any(mask: torch.Tensor) -> torch.Tensor:
        if mask.dim() <= 1:
            return mask.bool()
        return mask.bool().flatten(start_dim=1).any(dim=1)

    @staticmethod
    def _apply_optional_clamp(write: CompiledVTCActionWrite, value: torch.Tensor) -> torch.Tensor:
        return _clamp_in_dtype(value, write.clamp)

    def _apply_priority_write(
        self,
        write: CompiledVTCActionWrite,
        phase_value: torch.Tensor,
        candidate: torch.Tensor,
        write_mask: torch.Tensor,
        priority_state: dict[str, torch.Tensor],
    ) -> torch.Tensor:
        current_priority = priority_state.get(write.variable_id)
        if current_priority is None:
            current_priority = torch.full(write_mask.shape, -1, device=write_mask.device, dtype=torch.long)

        write_priority = torch.full(write_mask.shape, write.priority, device=write_mask.device, dtype=torch.long)
        winning_mask = write_mask & (write_priority >= current_priority)
        priority_state[write.variable_id] = torch.where(winning_mask, write_priority, current_priority)
        broadcast_mask = self._broadcast_agent_mask(winning_mask, phase_value, write)
        return cast(torch.Tensor, vtc_kernels.apply_masked_candidate(phase_value, candidate, broadcast_mask))

    def _build_write_mask(
        self,
        write: CompiledVTCActionWrite,
        actions: torch.Tensor,
        active_mask: torch.Tensor,
        evaluator: Evaluator,
    ) -> torch.Tensor:
        action_mask = actions == write.action_id
        write_mask = action_mask & active_mask.bool()
        if write.condition_ast is None:
            return write_mask

        condition = self._evaluate_tensor(evaluator, write.condition_ast, "condition", write)
        condition_mask = self._coerce_condition_mask(condition, actions, write)
        return write_mask & condition_mask

    @staticmethod
    def _evaluate_tensor(evaluator: Evaluator, ast: ASTNode, kind: str, write: CompiledVTCActionWrite) -> torch.Tensor:
        value: Any = evaluator.evaluate(ast)
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"VTC action write {write.telemetry_label} {kind} resolved to non-tensor value")
        return value

    @staticmethod
    def _coerce_condition_mask(condition: torch.Tensor, actions: torch.Tensor, write: CompiledVTCActionWrite) -> torch.Tensor:
        condition = to_storage_dtype(condition, torch.bool, f"Condition for VTC action write '{write.telemetry_label}'")
        if condition.dim() == 0:
            return torch.full(actions.shape, bool(condition.item()), dtype=torch.bool, device=actions.device)
        if condition.shape != actions.shape:
            raise ValueError(
                f"Condition for VTC action write '{write.telemetry_label}' produced shape {tuple(condition.shape)}, "
                f"expected {tuple(actions.shape)}"
            )
        return condition.to(device=actions.device)

    @staticmethod
    def _coerce_expression_tensor(
        value: torch.Tensor,
        target: torch.Tensor,
        actions: torch.Tensor,
        write: CompiledVTCActionWrite,
    ) -> torch.Tensor:
        value = to_storage_dtype(value, target.dtype, f"Expression for VTC action write '{write.telemetry_label}'").to(device=target.device)
        if VTCActionWriteProgram._targets_affordance_occupancy(write):
            return VTCActionWriteProgram._coerce_affordance_payload_tensor(value, target, actions, write)
        if value.dim() == 0:
            return value.expand_as(target)
        if value.shape != target.shape:
            raise ValueError(
                f"Expression for VTC action write '{write.telemetry_label}' produced shape {tuple(value.shape)}, "
                f"expected {tuple(target.shape)}"
            )
        return value

    @staticmethod
    def _coerce_affordance_payload_tensor(
        value: torch.Tensor,
        target: torch.Tensor,
        actions: torch.Tensor,
        write: CompiledVTCActionWrite,
    ) -> torch.Tensor:
        """The claimant payload, one per world: ``[worlds, *row]`` (claim) or ``[worlds, *slot]`` (capacity)."""
        if target.dim() < 2:
            raise ValueError(f"VTC affordance occupancy write '{write.telemetry_label}' needs [worlds, affordances, ...] storage")
        if write.composition == "capacity_claim":
            if target.dim() < 3:
                raise ValueError(
                    f"VTC affordance capacity_claim write '{write.telemetry_label}' requires target shape [worlds, affordances, slots, ...]"
                )
            payload_shape = torch.Size((actions.shape[0], *tuple(target.shape[3:])))
        else:
            payload_shape = torch.Size((actions.shape[0], *tuple(target.shape[2:])))

        if value.dim() == 0:
            return value.expand(payload_shape)
        if value.shape == payload_shape:
            return value

        per_claimant_shape = torch.Size(payload_shape[1:])
        if per_claimant_shape and value.shape == per_claimant_shape:
            return value.expand(payload_shape)

        raise ValueError(
            f"Expression for VTC affordance occupancy write '{write.telemetry_label}' produced shape {tuple(value.shape)}, "
            f"expected claimant payload shape {tuple(payload_shape)}"
        )

    @staticmethod
    def _broadcast_agent_mask(mask: torch.Tensor, target: torch.Tensor, write: CompiledVTCActionWrite) -> torch.Tensor:
        # The compiler admits only agent-axis targets here (ACTION_WRITE_AGENT_AXIS_SCOPES),
        # whose storage leads with the agent axis by construction.
        assert write.target_scope in ACTION_WRITE_AGENT_AXIS_SCOPES, write
        assert target.dim() >= 1 and target.shape[0] == mask.shape[0], (write.telemetry_label, tuple(target.shape))
        broadcast_mask = mask
        while broadcast_mask.dim() < target.dim():
            broadcast_mask = broadcast_mask.unsqueeze(-1)
        return broadcast_mask


@dataclass(frozen=True)
class VTCThresholdCascadeProgram:
    """Executable collection of compiled VTC threshold-delta cascade rules."""

    rules: tuple[CompiledVTCThresholdCascade, ...]

    def apply(
        self,
        *,
        bars_state: Mapping[str, torch.Tensor],
        active_mask: torch.Tensor,
        device: torch.device,
        strength_multiplier: float = 1.0,
    ) -> dict[str, torch.Tensor]:
        """Apply compiled threshold cascades to a bar state snapshot."""
        if strength_multiplier <= 0:
            raise ValueError("threshold cascade strength_multiplier must be positive")
        if active_mask.dim() != 1:
            raise ValueError(f"active_mask must be rank-1, got shape {tuple(active_mask.shape)}")

        updated = {name: value.to(device=device).clone() for name, value in bars_state.items()}
        active_mask_on_device = active_mask.to(device=device, dtype=torch.bool)

        for phase_rules in self._iter_phase_groups(self.rules):
            phase_snapshot = dict(updated)
            phase_values = dict(updated)

            for rule in phase_rules:
                if rule.variable_id not in phase_values:
                    raise KeyError(f"VTC threshold cascade targets unknown bar '{rule.variable_id}'")
                if rule.source_variable_id not in phase_snapshot:
                    raise KeyError(f"VTC threshold cascade reads unknown bar '{rule.source_variable_id}'")
                if rule.composition != "additive_delta":
                    raise NotImplementedError(f"VTC threshold cascade composition '{rule.composition}' is not scriptable")
                clamp_low, clamp_high = _required_clamp(rule.clamp, rule.telemetry_label)

                target_value = phase_values[rule.variable_id]
                source_value = phase_snapshot[rule.source_variable_id].to(device=device, dtype=target_value.dtype)
                phase_values[rule.variable_id] = vtc_kernels.apply_threshold_cascade(
                    source_value,
                    target_value,
                    active_mask_on_device,
                    rule.cascade_threshold,
                    rule.cascade_strength,
                    strength_multiplier,
                    clamp_low,
                    clamp_high,
                )

            updated = phase_values

        return updated

    @staticmethod
    def _iter_phase_groups(rules: Sequence[CompiledVTCThresholdCascade]) -> list[tuple[CompiledVTCThresholdCascade, ...]]:
        phase_groups: list[tuple[CompiledVTCThresholdCascade, ...]] = []
        current_phase: str | None = None
        current_group: list[CompiledVTCThresholdCascade] = []

        for rule in rules:
            if current_phase is None:
                current_phase = rule.phase
            if rule.phase != current_phase:
                phase_groups.append(tuple(current_group))
                current_group = []
                current_phase = rule.phase
            current_group.append(rule)

        if current_group:
            phase_groups.append(tuple(current_group))
        return phase_groups


@dataclass(frozen=True)
class VTCPassiveDepletionProgram:
    """Executable collection of compiled VTC passive-depletion rules."""

    rules: tuple[CompiledVTCPassiveDepletion, ...]

    def apply(
        self,
        *,
        bars_state: Mapping[str, torch.Tensor],
        active_mask: torch.Tensor,
        device: torch.device,
        depletion_multiplier: float = 1.0,
    ) -> dict[str, torch.Tensor]:
        """Apply passive depletion to meter bars using a VTC phase snapshot."""
        if depletion_multiplier < 0:
            raise ValueError("passive depletion multiplier must be non-negative")
        if active_mask.dim() != 1:
            raise ValueError(f"active_mask must be rank-1, got shape {tuple(active_mask.shape)}")

        updated = {name: value.to(device=device).clone() for name, value in bars_state.items()}
        active_mask_on_device = active_mask.to(device=device, dtype=torch.bool)

        for phase_rules in self._iter_phase_groups(self.rules):
            phase_values = dict(updated)

            for rule in phase_rules:
                if rule.variable_id not in phase_values:
                    raise KeyError(f"VTC passive depletion targets unknown bar '{rule.variable_id}'")
                if rule.condition_ast is not None:
                    raise NotImplementedError(f"VTC passive depletion condition '{rule.telemetry_label}' is not scriptable")
                if rule.composition != "overwrite":
                    raise NotImplementedError(f"VTC passive depletion composition '{rule.composition}' is not scriptable")
                clamp_low, clamp_high = _required_clamp(rule.clamp, rule.telemetry_label)

                phase_value = phase_values[rule.variable_id]
                phase_values[rule.variable_id] = vtc_kernels.apply_passive_depletion(
                    phase_value,
                    active_mask_on_device,
                    rule.passive_rate,
                    float(depletion_multiplier),
                    clamp_low,
                    clamp_high,
                )

            updated = phase_values

        return updated

    @staticmethod
    def _iter_phase_groups(rules: Sequence[CompiledVTCPassiveDepletion]) -> list[tuple[CompiledVTCPassiveDepletion, ...]]:
        phase_groups: list[tuple[CompiledVTCPassiveDepletion, ...]] = []
        current_phase: str | None = None
        current_group: list[CompiledVTCPassiveDepletion] = []

        for rule in rules:
            if current_phase is None:
                current_phase = rule.phase
            if rule.phase != current_phase:
                phase_groups.append(tuple(current_group))
                current_group = []
                current_phase = rule.phase
            current_group.append(rule)

        if current_group:
            phase_groups.append(tuple(current_group))
        return phase_groups


@dataclass(frozen=True)
class VTCBoundsClampProgram:
    """Executable collection of compiled bounds-invariant rules.

    Bounds are declarations about the state, not about a write, so `apply` takes no
    active mask: a dead agent's meter is still required to sit inside its declared
    bounds, and clamping an already-in-bounds value is the identity.
    """

    rules: tuple[CompiledVTCBoundsClamp, ...]

    def apply(
        self,
        *,
        bars_state: Mapping[str, torch.Tensor],
        device: torch.device,
    ) -> dict[str, torch.Tensor]:
        """Clamp every ruled meter into its declared bounds; touch nothing else."""
        updated = {name: value.to(device=device).clone() for name, value in bars_state.items()}
        for rule in self.rules:
            if rule.variable_id not in updated:
                raise KeyError(f"VTC bounds clamp targets unknown bar '{rule.variable_id}'")
            clamp_low, clamp_high = _required_clamp(rule.clamp, rule.telemetry_label)
            updated[rule.variable_id] = torch.clamp(updated[rule.variable_id], min=clamp_low, max=clamp_high)
        return updated


@dataclass(frozen=True)
class VTCModulationProgram:
    """Executable collection of compiled VTC affordance modulation rules."""

    rules: tuple[CompiledVTCModulation, ...]

    def compute_affordance_multiplier(
        self,
        affordance_name: str,
        bars_state: Mapping[str, torch.Tensor],
        *,
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> torch.Tensor:
        """Compute the composed multiplier for an affordance from compiled modulation rules."""
        if active_mask.dim() != 1:
            raise ValueError(f"active_mask must be rank-1, got shape {tuple(active_mask.shape)}")

        bars_on_device = {name: value.to(device=device) for name, value in bars_state.items()}
        dtype = self._infer_dtype(bars_on_device)
        active_mask_on_device = active_mask.to(device=device, dtype=torch.bool)
        multiplier = torch.ones(active_mask_on_device.shape, device=device, dtype=dtype)
        matching_rules = tuple(rule for rule in self.rules if rule.target_affordance_id == affordance_name)

        for phase_rules in self._iter_phase_groups(matching_rules):
            phase_value = multiplier
            phase_snapshot = dict(bars_on_device)

            for rule in phase_rules:
                if rule.source_variable_id not in phase_snapshot:
                    raise KeyError(f"VTC modulation reads unknown bar '{rule.source_variable_id}'")
                if rule.condition_ast is not None:
                    raise NotImplementedError(f"VTC modulation condition '{rule.telemetry_label}' is not scriptable")
                if rule.composition != "multiplicative_modifier":
                    raise NotImplementedError(f"VTC modulation composition '{rule.composition}' is not scriptable")
                clamp_low, clamp_high = _required_clamp(rule.clamp, rule.telemetry_label)

                source_value = phase_snapshot[rule.source_variable_id].to(device=device, dtype=phase_value.dtype)
                phase_value = vtc_kernels.apply_modulation_multiplier(
                    phase_value,
                    source_value,
                    active_mask_on_device,
                    rule.modulation_threshold,
                    rule.min_multiplier,
                    clamp_low,
                    clamp_high,
                )

            multiplier = phase_value

        return torch.where(active_mask_on_device, multiplier, torch.zeros_like(multiplier))

    @staticmethod
    def _infer_dtype(bars_state: Mapping[str, torch.Tensor]) -> torch.dtype:
        if not bars_state:
            return torch.float32
        first_bar = next(iter(bars_state.values()))
        return first_bar.dtype if first_bar.is_floating_point() else torch.float32

    @staticmethod
    def _iter_phase_groups(rules: Sequence[CompiledVTCModulation]) -> list[tuple[CompiledVTCModulation, ...]]:
        phase_groups: list[tuple[CompiledVTCModulation, ...]] = []
        current_phase: str | None = None
        current_group: list[CompiledVTCModulation] = []

        for rule in rules:
            if current_phase is None:
                current_phase = rule.phase
            if rule.phase != current_phase:
                phase_groups.append(tuple(current_group))
                current_group = []
                current_phase = rule.phase
            current_group.append(rule)

        if current_group:
            phase_groups.append(tuple(current_group))
        return phase_groups


@dataclass(frozen=True)
class VTCAffordanceGateProgram:
    """Executable collection of compiled VTC operating-hour gates."""

    rules: tuple[CompiledVTCAffordanceGate, ...]

    def is_affordance_open(self, affordance_name: str, *, time_of_day: int | float | torch.Tensor, device: torch.device) -> bool:
        """Return whether one affordance is open for the current temporal state."""
        values = self.compute(time_of_day=time_of_day, device=device)
        try:
            value = values[affordance_name]
        except KeyError as exc:
            raise KeyError(f"VTC affordance gates have no rule for affordance '{affordance_name}'") from exc
        if value.numel() != 1:
            raise ValueError(f"VTC affordance gate for '{affordance_name}' produced non-scalar shape {tuple(value.shape)}")
        return bool(value.item())

    def compute(self, *, time_of_day: int | float | torch.Tensor, device: torch.device) -> dict[str, torch.Tensor]:
        """Evaluate all operating-hour gates from the VTC temporal snapshot."""
        time_tensor = self._time_tensor(time_of_day, device=device)
        context = ExecutionContext(
            bars={},
            vfs={},
            affordances={},
            temporal={"time_of_day": time_tensor},
            device=device,
        )
        evaluator = Evaluator(context)
        values: dict[str, torch.Tensor] = {}
        for rule in self.rules:
            value = self._evaluate_tensor(evaluator, rule.expression_ast, "expression", rule).to(device=device, dtype=torch.bool)
            if value.numel() != 1:
                raise ValueError(f"VTC affordance gate '{rule.telemetry_label}' produced non-scalar shape {tuple(value.shape)}")
            values[rule.target_affordance_id] = value.reshape(())
        return values

    @staticmethod
    def _time_tensor(time_of_day: int | float | torch.Tensor, *, device: torch.device) -> torch.Tensor:
        if isinstance(time_of_day, torch.Tensor):
            if time_of_day.numel() != 1:
                raise ValueError(f"time_of_day must be scalar, got shape {tuple(time_of_day.shape)}")
            return time_of_day.to(device=device, dtype=torch.float32).reshape(())
        return torch.tensor(float(time_of_day), device=device, dtype=torch.float32)

    @staticmethod
    def _evaluate_tensor(
        evaluator: Evaluator,
        ast: ASTNode,
        kind: str,
        rule: CompiledVTCAffordanceGate,
    ) -> torch.Tensor:
        value: Any = evaluator.evaluate(ast)
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"VTC affordance gate {rule.telemetry_label} {kind} resolved to non-tensor value")
        return value


@dataclass(frozen=True)
class VTCInteractionProgressProgram:
    """Executable collection of compiled VTC multi-tick progress and completion rules."""

    progress_rules: tuple[CompiledVTCInteractionProgress, ...]
    completion_bonus_rules: tuple[CompiledVTCInteractionCompletionBonus, ...]

    def apply(
        self,
        *,
        interaction_affordances: Mapping[int, str],
        positions: torch.Tensor,
        interaction_progress: torch.Tensor,
        last_affordances: Sequence[str | None],
        last_positions: torch.Tensor,
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> VTCInteractionProgressResult:
        """Advance multi-tick interaction progress using compiled VTC duration rules."""
        self._validate_apply_inputs(
            positions=positions,
            interaction_progress=interaction_progress,
            last_affordances=last_affordances,
            last_positions=last_positions,
            active_mask=active_mask,
        )

        positions_on_device = positions.to(device=device)
        last_positions_on_device = last_positions.to(device=device)
        previous_progress = interaction_progress.to(device=device, dtype=torch.long)
        active = active_mask.to(device=device, dtype=torch.bool)

        next_progress = torch.zeros_like(previous_progress)
        ticks_done = torch.zeros_like(previous_progress)
        completion_mask = torch.zeros(previous_progress.shape, device=device, dtype=torch.bool)
        completion_affordances: list[str | None] = [None] * previous_progress.shape[0]
        next_last_affordances: list[str | None] = [None] * previous_progress.shape[0]
        next_last_positions = last_positions_on_device.clone()

        normalized_interactions = self._normalize_interaction_affordances(interaction_affordances, previous_progress.shape[0])
        for agent_idx in range(previous_progress.shape[0]):
            if not bool(active[agent_idx].item()):
                next_progress[agent_idx] = previous_progress[agent_idx]
                next_last_affordances[agent_idx] = last_affordances[agent_idx]
                next_last_positions[agent_idx] = last_positions_on_device[agent_idx]
                continue

            affordance_name = normalized_interactions.get(agent_idx)
            if affordance_name is None:
                next_last_positions[agent_idx] = positions_on_device[agent_idx]
                continue

            rule = self._rule_for_affordance(affordance_name)
            same_affordance = last_affordances[agent_idx] == affordance_name
            same_position = torch.equal(last_positions_on_device[agent_idx], positions_on_device[agent_idx])
            candidate_ticks = (
                previous_progress[agent_idx] + 1
                if same_affordance and same_position
                else torch.tensor(
                    1,
                    device=device,
                    dtype=torch.long,
                )
            )
            ticks_done[agent_idx] = candidate_ticks

            if int(candidate_ticks.item()) >= rule.duration_ticks:
                completion_mask[agent_idx] = True
                completion_affordances[agent_idx] = affordance_name
                next_last_affordances[agent_idx] = None
            else:
                next_progress[agent_idx] = candidate_ticks
                next_last_affordances[agent_idx] = affordance_name

            next_last_positions[agent_idx] = positions_on_device[agent_idx]

        return VTCInteractionProgressResult(
            interaction_progress=next_progress,
            ticks_done=ticks_done,
            completion_mask=completion_mask,
            completion_affordances=completion_affordances,
            last_affordances=next_last_affordances,
            last_positions=next_last_positions,
        )

    def has_multi_tick_affordances(self) -> bool:
        """Return whether this program contains any multi-tick affordance rules."""
        return bool(self.progress_rules)

    def contains_affordance(self, affordance_name: str) -> bool:
        """Return whether an affordance has VTC multi-tick progress semantics."""
        return any(rule.target_affordance_id == affordance_name for rule in self.progress_rules)

    @staticmethod
    def _validate_apply_inputs(
        *,
        positions: torch.Tensor,
        interaction_progress: torch.Tensor,
        last_affordances: Sequence[str | None],
        last_positions: torch.Tensor,
        active_mask: torch.Tensor,
    ) -> None:
        if interaction_progress.dim() != 1:
            raise ValueError(f"interaction_progress must be rank-1, got shape {tuple(interaction_progress.shape)}")
        if active_mask.shape != interaction_progress.shape:
            raise ValueError(
                f"active_mask shape {tuple(active_mask.shape)} must match interaction_progress shape "
                f"{tuple(interaction_progress.shape)}"
            )
        if positions.shape[0] != interaction_progress.shape[0]:
            raise ValueError(
                f"positions leading dimension {positions.shape[0]} must match interaction batch {interaction_progress.shape[0]}"
            )
        if last_positions.shape != positions.shape:
            raise ValueError(f"last_positions shape {tuple(last_positions.shape)} must match positions shape {tuple(positions.shape)}")
        if len(last_affordances) != interaction_progress.shape[0]:
            raise ValueError(
                f"last_affordances length {len(last_affordances)} must match interaction batch {interaction_progress.shape[0]}"
            )

    @staticmethod
    def _normalize_interaction_affordances(interaction_affordances: Mapping[int, str], batch_size: int) -> dict[int, str]:
        normalized: dict[int, str] = {}
        for raw_idx, affordance_name in interaction_affordances.items():
            agent_idx = int(raw_idx)
            if agent_idx < 0 or agent_idx >= batch_size:
                raise ValueError(f"Interaction agent index {agent_idx} is outside batch size {batch_size}")
            normalized[agent_idx] = affordance_name
        return normalized

    def _rule_for_affordance(self, affordance_name: str) -> CompiledVTCInteractionProgress:
        for rule in self.progress_rules:
            if rule.target_affordance_id == affordance_name:
                return rule
        raise KeyError(f"VTC interaction progress has no rule for affordance '{affordance_name}'")


@dataclass(frozen=True)
class VTCTerminalConditionProgram:
    """Executable collection of compiled VTC terminal-condition rules."""

    rules: tuple[CompiledVTCTerminalCondition, ...]

    def apply(
        self,
        *,
        bars_state: Mapping[str, torch.Tensor],
        dones: torch.Tensor,
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> torch.Tensor:
        """Evaluate terminal conditions and OR triggered terminals into existing done flags."""
        self._validate_apply_inputs(bars_state=bars_state, dones=dones, active_mask=active_mask)

        updated_dones = dones.to(device=device, dtype=torch.bool).clone()
        active = active_mask.to(device=device, dtype=torch.bool)
        bars_on_device = {name: value.to(device=device) for name, value in bars_state.items()}
        if len(self.rules) == 0:
            return updated_dones

        missing_bars = sorted({rule.source_variable_id for rule in self.rules if rule.source_variable_id not in bars_on_device})
        if missing_bars:
            raise KeyError(f"VTC terminal conditions reference unknown bars: {missing_bars}")

        for rule in self.rules:
            if rule.condition_ast is not None:
                raise NotImplementedError(f"VTC terminal condition '{rule.telemetry_label}' condition is not scriptable")
            if rule.composition != "event":
                raise NotImplementedError(f"VTC terminal condition composition '{rule.composition}' is not scriptable")
            source_value = bars_on_device[rule.source_variable_id]
            if source_value.shape != updated_dones.shape:
                raise ValueError(
                    f"VTC terminal condition {rule.telemetry_label} reads shape {tuple(source_value.shape)}; "
                    f"expected {tuple(updated_dones.shape)}"
                )
            updated_dones = vtc_kernels.apply_terminal_condition(
                source_value,
                updated_dones,
                active,
                rule.threshold,
                rule.operator == "<=",
            )

        return updated_dones

    @staticmethod
    def _validate_apply_inputs(
        *,
        bars_state: Mapping[str, torch.Tensor],
        dones: torch.Tensor,
        active_mask: torch.Tensor,
    ) -> None:
        if dones.dim() != 1:
            raise ValueError(f"dones must be rank-1, got shape {tuple(dones.shape)}")
        if active_mask.shape != dones.shape:
            raise ValueError(f"active_mask shape {tuple(active_mask.shape)} must match dones shape {tuple(dones.shape)}")
        for bar_name, value in bars_state.items():
            if value.shape != dones.shape:
                raise ValueError(f"bar '{bar_name}' shape {tuple(value.shape)} must match dones shape {tuple(dones.shape)}")


@dataclass(frozen=True)
class VTCTransitionRuleProgram:
    """Executable collection of compiled VTC transition rules."""

    rules: tuple[CompiledVTCTransitionRule, ...]

    def apply(
        self,
        *,
        vfs_state: Mapping[str, torch.Tensor],
        active_mask: torch.Tensor,
        device: torch.device,
        bars_state: Mapping[str, torch.Tensor] | None = None,
    ) -> VTCWriteResult:
        """Apply compiled social-state writes using phase snapshots and masked commits."""
        if active_mask.dim() != 1:
            raise ValueError(f"active_mask must be rank-1, got shape {tuple(active_mask.shape)}")

        bars = {} if bars_state is None else dict(bars_state)
        updated = {name: value.to(device=device).clone() for name, value in vfs_state.items()}
        bars_on_device = {name: value.to(device=device) for name, value in bars.items()}

        active = active_mask.to(device=device, dtype=torch.bool)
        attempted_targets: set[str] = set()
        for phase_rules in self._iter_phase_groups(self.rules):
            phase_snapshot = dict(updated)
            phase_effects = self._compute_phase_effects(
                phase_rules=phase_rules,
                phase_snapshot=phase_snapshot,
                bars_state=bars_on_device,
                active_mask=active,
                device=device,
            )
            attempted_targets.update(effect.rule.variable_id for effect in phase_effects if bool(effect.write_mask.any()))
            updated = self._commit_phase_effects(phase_snapshot, phase_effects)

        return VTCWriteResult(updated, frozenset(attempted_targets))

    @staticmethod
    def _iter_phase_groups(rules: Sequence[CompiledVTCTransitionRule]) -> list[tuple[CompiledVTCTransitionRule, ...]]:
        phase_groups: list[tuple[CompiledVTCTransitionRule, ...]] = []
        current_phase: str | None = None
        current_group: list[CompiledVTCTransitionRule] = []

        for rule in rules:
            if current_phase is None:
                current_phase = rule.phase
            if rule.phase != current_phase:
                phase_groups.append(tuple(current_group))
                current_group = []
                current_phase = rule.phase
            current_group.append(rule)

        if current_group:
            phase_groups.append(tuple(current_group))
        return phase_groups

    def _compute_phase_effects(
        self,
        *,
        phase_rules: Sequence[CompiledVTCTransitionRule],
        phase_snapshot: Mapping[str, torch.Tensor],
        bars_state: Mapping[str, torch.Tensor],
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> tuple[_VTCTransitionRuleEffect, ...]:
        phase_effects: list[_VTCTransitionRuleEffect] = []
        context_vfs = dict(phase_snapshot)
        context_vfs.setdefault("agent_id", torch.arange(active_mask.shape[0], device=device))
        context = ExecutionContext(
            bars=dict(bars_state),
            vfs=context_vfs,
            affordances={},
            temporal={},
            device=device,
            num_agents=active_mask.shape[0],
        )
        evaluator = Evaluator(context)

        for rule in phase_rules:
            if rule.variable_id not in phase_snapshot:
                raise KeyError(f"VTC transition rule targets unknown VFS variable '{rule.variable_id}'")

            target_snapshot = phase_snapshot[rule.variable_id]
            rule_evaluator = evaluator
            if rule.world_columns:
                rule_evaluator = Evaluator(replace(context, vfs=self._world_column_view(context_vfs, rule, target_snapshot)))
            condition_mask = self._build_write_mask(rule, target_snapshot, active_mask, rule_evaluator)
            expression_value = self._evaluate_tensor(rule_evaluator, rule.expression_ast, "expression", rule)
            phase_effects.append(
                _VTCTransitionRuleEffect(
                    rule=rule,
                    expression_value=self._coerce_expression_tensor(expression_value, target_snapshot, rule, active_mask),
                    write_mask=condition_mask,
                )
            )

        return tuple(phase_effects)

    @staticmethod
    def _world_column_view(
        context_vfs: Mapping[str, torch.Tensor], rule: CompiledVTCTransitionRule, target: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        """The snapshot with each of `rule.world_columns` given a singleton affordance axis.

        A global ``[worlds, *payload]`` becomes ``[worlds, 1, *payload]``; a scalar global
        also gets the target's trailing axes as singletons, so it broadcasts over its own
        world's affordance rows (and their element axes), never over another world's.
        """
        view = dict(context_vfs)
        for name in rule.world_columns:
            value = view[name]
            if value.dim() == 1:
                value = value.view(value.shape[0], *([1] * (target.dim() - 1)))
            else:
                value = value.unsqueeze(1)
            view[name] = value
        return view

    def _commit_phase_effects(
        self,
        phase_snapshot: Mapping[str, torch.Tensor],
        phase_effects: Sequence[_VTCTransitionRuleEffect],
    ) -> dict[str, torch.Tensor]:
        phase_values = dict(phase_snapshot)
        priority_state: dict[str, torch.Tensor] = {}

        for effect in phase_effects:
            phase_value = phase_values[effect.rule.variable_id]
            phase_values[effect.rule.variable_id] = self._apply_composed_write(
                rule=effect.rule,
                phase_value=phase_value,
                expression_value=effect.expression_value,
                write_mask=effect.write_mask,
                priority_state=priority_state,
            )

        return phase_values

    def _apply_composed_write(
        self,
        *,
        rule: CompiledVTCTransitionRule,
        phase_value: torch.Tensor,
        expression_value: torch.Tensor,
        write_mask: torch.Tensor,
        priority_state: dict[str, torch.Tensor],
    ) -> torch.Tensor:
        candidate = self._compose_candidate(rule, phase_value, expression_value)
        candidate = self._apply_optional_clamp(rule, candidate)

        if rule.composition == "priority_write":
            return self._apply_priority_write(rule, phase_value, candidate, write_mask, priority_state)
        return cast(torch.Tensor, vtc_kernels.apply_masked_candidate(phase_value, candidate, write_mask))

    @staticmethod
    def _compose_candidate(
        rule: CompiledVTCTransitionRule,
        phase_value: torch.Tensor,
        expression_value: torch.Tensor,
    ) -> torch.Tensor:
        # expression_value is already storage-typed (_coerce_expression_tensor).
        expression = expression_value
        if rule.composition in {"overwrite", "last_write_wins", "priority_write", "clamp"}:
            return expression
        if rule.composition == "additive_delta":
            return phase_value + expression
        if rule.composition == "multiplicative_modifier":
            return phase_value * expression
        if rule.composition == "min":
            return torch.minimum(phase_value, expression)
        if rule.composition == "max":
            return torch.maximum(phase_value, expression)
        raise AssertionError(f"VTC transition rule composition '{rule.composition}' is outside RULE_WRITE_COMPOSITIONS")

    @staticmethod
    def _apply_optional_clamp(rule: CompiledVTCTransitionRule, value: torch.Tensor) -> torch.Tensor:
        return _clamp_in_dtype(value, rule.clamp)

    def _apply_priority_write(
        self,
        rule: CompiledVTCTransitionRule,
        phase_value: torch.Tensor,
        candidate: torch.Tensor,
        write_mask: torch.Tensor,
        priority_state: dict[str, torch.Tensor],
    ) -> torch.Tensor:
        current_priority = priority_state.get(rule.variable_id)
        if current_priority is None:
            current_priority = torch.full(write_mask.shape, -1, device=write_mask.device, dtype=torch.long)

        write_priority = torch.full(write_mask.shape, rule.priority, device=write_mask.device, dtype=torch.long)
        winning_mask = write_mask & (write_priority >= current_priority)
        priority_state[rule.variable_id] = torch.where(winning_mask, write_priority, current_priority)
        return cast(torch.Tensor, vtc_kernels.apply_masked_candidate(phase_value, candidate, winning_mask))

    def _build_write_mask(
        self,
        rule: CompiledVTCTransitionRule,
        target: torch.Tensor,
        active_mask: torch.Tensor,
        evaluator: Evaluator,
    ) -> torch.Tensor:
        active_target_mask = self._active_mask_for_target(rule, target, active_mask)
        if rule.condition_ast is None:
            return active_target_mask

        condition = self._evaluate_tensor(evaluator, rule.condition_ast, "condition", rule)
        condition_mask = self._coerce_mask_to_target(condition, target, rule, active_mask)
        return condition_mask & active_target_mask

    @staticmethod
    def _evaluate_tensor(
        evaluator: Evaluator,
        ast: ASTNode,
        kind: str,
        rule: CompiledVTCTransitionRule,
    ) -> torch.Tensor:
        value: Any = evaluator.evaluate(ast)
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"VTC transition rule {rule.telemetry_label} {kind} resolved to non-tensor value")
        return value

    @staticmethod
    def _coerce_expression_tensor(
        value: torch.Tensor,
        target: torch.Tensor,
        rule: CompiledVTCTransitionRule,
        active_mask: torch.Tensor,
    ) -> torch.Tensor:
        return VTCTransitionRuleProgram._coerce_tensor_to_target(
            value,
            target,
            rule,
            active_mask,
            label="Expression",
            dtype=target.dtype,
        )

    @staticmethod
    def _coerce_mask_to_target(
        value: torch.Tensor,
        target: torch.Tensor,
        rule: CompiledVTCTransitionRule,
        active_mask: torch.Tensor,
    ) -> torch.Tensor:
        return VTCTransitionRuleProgram._coerce_tensor_to_target(
            value,
            target,
            rule,
            active_mask,
            label="Condition",
            dtype=torch.bool,
        )

    @staticmethod
    def _coerce_tensor_to_target(
        value: torch.Tensor,
        target: torch.Tensor,
        rule: CompiledVTCTransitionRule,
        active_mask: torch.Tensor,
        *,
        label: str,
        dtype: torch.dtype,
    ) -> torch.Tensor:
        value_on_device = to_storage_dtype(value, dtype, f"{label} for VTC transition rule '{rule.telemetry_label}'").to(
            device=target.device
        )
        if value_on_device.dim() == 0:
            return value_on_device.expand_as(target)
        if value_on_device.shape == target.shape:
            return value_on_device

        # The compile-time shape proof admits one more case: a per-row value (an agent
        # row, a global's per-world value, or a world column of one) on a target with
        # further axes (affordance rows, or a vector or tensor row), spread along them.
        num_agents = active_mask.shape[0]
        if rule.target_scope in BATCH_AXIS_SCOPES and 1 <= value_on_device.dim() <= target.dim() and value_on_device.shape[0] == num_agents:
            VTCTransitionRuleProgram._assert_target_shape(rule, target, num_agents)
            padded = value_on_device.reshape(*value_on_device.shape, *([1] * (target.dim() - value_on_device.dim())))
            try:
                return padded.expand_as(target)
            except RuntimeError:
                pass

        raise ValueError(
            f"{label} for VTC transition rule '{rule.telemetry_label}' produced shape {tuple(value.shape)} for "
            f"{rule.target_scope.value}-scope target shape {tuple(target.shape)}; the compiled shape proof admits none such"
        )

    @staticmethod
    def _active_mask_for_target(
        rule: CompiledVTCTransitionRule,
        target: torch.Tensor,
        active_mask: torch.Tensor,
    ) -> torch.Tensor:
        active = active_mask.to(device=target.device, dtype=torch.bool)
        num_agents = active.shape[0]
        # Every rule target scope leads with the batch axis (the compiler admits no other):
        # an agent row, or a world's global or affordance rows (S1), each advancing while
        # its own agent is active.
        assert rule.target_scope in BATCH_AXIS_SCOPES, rule
        VTCTransitionRuleProgram._assert_target_shape(rule, target, num_agents)
        agent_mask = active
        while agent_mask.dim() < target.dim():
            agent_mask = agent_mask.unsqueeze(-1)
        return agent_mask.expand_as(target)

    @staticmethod
    def _assert_target_shape(rule: CompiledVTCTransitionRule, target: torch.Tensor, num_agents: int) -> None:
        """The declared scope fixes the leading axis; storage that disagrees is a registry defect."""
        assert target.dim() >= 1 and int(target.shape[0]) == num_agents, (
            f"VTC transition rule '{rule.telemetry_label}' targets {rule.target_scope.value}-scope "
            f"'{rule.variable_id}' with storage shape {tuple(target.shape)}; expected a leading batch axis of {num_agents}"
        )


@dataclass(frozen=True)
class VTCRewardProgram:
    """Shape contract over the DAC reward backend's outputs.

    Rewards are DAC's: this is not a transition-phase program and carries no compiled
    rules. It calls the backend and refuses outputs whose tensors or component set
    disagree with the per-agent batch.
    """

    expected_components: ClassVar[tuple[str, ...]] = ("extrinsic", "intrinsic", "intrinsic_raw", "shaping")

    def apply(
        self,
        *,
        reward_backend: Any,
        step_counts: torch.Tensor,
        dones: torch.Tensor,
        meters: torch.Tensor,
        intrinsic_raw: torch.Tensor,
        reward_context: Mapping[str, Any],
    ) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
        """Run the reward phase through the DAC backend and validate declared component outputs."""
        total_rewards, intrinsic_weights, components = reward_backend.calculate_rewards(
            step_counts=step_counts,
            dones=dones,
            meters=meters,
            intrinsic_raw=intrinsic_raw,
            **dict(reward_context),
        )
        self._validate_tensor("total_rewards", total_rewards, dones)
        self._validate_tensor("intrinsic_weights", intrinsic_weights, dones)
        self._validate_components(components, dones)
        return total_rewards, intrinsic_weights, components

    @staticmethod
    def _validate_tensor(name: str, value: Any, dones: torch.Tensor) -> None:
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"VTC reward program expected {name} to be a tensor")
        if value.shape != dones.shape:
            raise ValueError(f"VTC reward program expected {name} shape {tuple(dones.shape)}, got {tuple(value.shape)}")

    def _validate_components(self, components: Any, dones: torch.Tensor) -> None:
        if not isinstance(components, dict):
            raise TypeError("VTC reward program expected components to be a dict")

        missing = sorted(component for component in self.expected_components if component not in components)
        if missing:
            raise KeyError(f"VTC reward program missing declared reward components: {missing}")

        for name, value in components.items():
            if not isinstance(value, torch.Tensor):
                raise TypeError(f"VTC reward component '{name}' resolved to non-tensor value")
            if value.shape != dones.shape:
                raise ValueError(
                    f"VTC reward component '{name}' shape {tuple(value.shape)} does not match dones shape {tuple(dones.shape)}"
                )


#: Transition-rule write compositions. The occupancy claims (``claim_if_free``,
#: ``capacity_claim``) are action-write only: a rule has no claimant and no source affordance.
RULE_WRITE_COMPOSITIONS: tuple[str, ...] = (
    "overwrite",
    "additive_delta",
    "multiplicative_modifier",
    "min",
    "max",
    "clamp",
    "priority_write",
    "last_write_wins",
)


def compile_vtc_transition_rules(
    rules: Sequence[VTCTransitionRuleSource | Mapping[str, Any]],
    targets: Mapping[str, VTCWriteTarget],
) -> VTCTransitionRuleProgram:
    """Compile declarative transition rules into VTC writes."""
    return compile_vtc_transition_rules_with_phase_graph(rules, targets, TransitionPhaseGraph.default())


def compile_vtc_transition_rules_with_phase_graph(
    rules: Sequence[VTCTransitionRuleSource | Mapping[str, Any]],
    targets: Mapping[str, VTCWriteTarget],
    phase_graph: TransitionPhaseGraph,
) -> VTCTransitionRuleProgram:
    """Compile relationship/social-state rules using an explicit transition phase graph.

    ``targets`` names every state a rule may read or write with its declared scope and
    type: the scope, never the storage shape, decides how a write is masked and
    broadcast; the type is what the write expression must type-check to.
    """
    parser = ExpressionParser()
    schema, shapes = _write_expression_namespace(targets)
    global_ids = frozenset(name for name, target in targets.items() if target.scope == VariableScope.GLOBAL)
    checker = TypeChecker(schema=schema)
    compiled_rules: list[CompiledVTCTransitionRule] = []
    refusals: list[VTCWriteRefusal] = []

    for rule_index, raw_rule in enumerate(rules):
        rule = _coerce_transition_rule(raw_rule, rule_index)
        for write_index, raw_write in enumerate(rule["writes"]):
            write = _coerce_transition_rule_write(raw_write, rule, write_index)
            if write["phase"] not in phase_graph.ordered_phases:
                refusals.append(
                    VTCWriteRefusal(
                        origin_key=f"transition_rules:{rule['rule_id']}",
                        kind="phase",
                        message=(
                            f"Transition rule '{rule['rule_id']}' write '{write['telemetry_label']}' is scheduled at "
                            f"{_unknown_phase_reason(write['phase'])}. "
                            f"Transition phases: {', '.join(phase_graph.ordered_phases)}"
                        ),
                    )
                )
                continue
            target = targets.get(write["variable_id"])
            if target is None or target.scope not in _RULE_ADMITTED_SHAPES:
                refusals.append(
                    VTCWriteRefusal(
                        origin_key=f"transition_rules:{rule['rule_id']}",
                        kind="scope",
                        message=(
                            f"Transition rule '{rule['rule_id']}' write '{write['telemetry_label']}' targets "
                            + (
                                f"unknown VFS variable '{write['variable_id']}'"
                                if target is None
                                else f"{target.scope.value}-scope variable '{write['variable_id']}', which has no registry row"
                            )
                        ),
                    )
                )
                continue
            condition = _combined_condition(rule["condition"], write["condition"])
            expression_ast = parser.parse(write["expression"])
            condition_ast = parser.parse(condition) if condition is not None else None
            type_refusal = _write_type_refusal(
                checker,
                expression_ast=expression_ast,
                expression=write["expression"],
                condition_ast=condition_ast,
                condition=condition,
                target_id=write["variable_id"],
                target_type=target.type,
                prefix=f"Transition rule '{rule['rule_id']}' write '{write['telemetry_label']}'",
            )
            if type_refusal is not None:
                refusals.append(VTCWriteRefusal(origin_key=f"transition_rules:{rule['rule_id']}", kind="type", message=type_refusal))
                continue
            # From here on the ASTs are the inlined ones: what the rule evaluates (S4).
            inlined = _inline_expression_reads(
                targets,
                expression_ast=expression_ast,
                expression=write["expression"],
                condition_ast=condition_ast,
                condition=condition,
                prefix=f"Transition rule '{rule['rule_id']}' write '{write['telemetry_label']}'",
            )
            if isinstance(inlined, str):
                refusals.append(VTCWriteRefusal(origin_key=f"transition_rules:{rule['rule_id']}", kind="type", message=inlined))
                continue
            expression_ast, condition_ast = inlined
            admitted_shapes = _RULE_ADMITTED_SHAPES[target.scope]
            shape_refusal = _write_shape_refusal(
                expression_ast=expression_ast,
                expression=write["expression"],
                condition_ast=condition_ast,
                condition=condition,
                shapes=shapes,
                admitted_expression=admitted_shapes,
                admitted_condition=admitted_shapes,
                target_id=write["variable_id"],
                target_scope=target.scope,
                prefix=f"Transition rule '{rule['rule_id']}' write '{write['telemetry_label']}'",
            )
            if shape_refusal is not None:
                refusals.append(VTCWriteRefusal(origin_key=f"transition_rules:{rule['rule_id']}", kind="type", message=shape_refusal))
                continue
            compiled_rules.append(
                CompiledVTCTransitionRule(
                    rule_id=rule["rule_id"],
                    effect=write["effect"],
                    variable_id=write["variable_id"],
                    expression=write["expression"],
                    expression_ast=expression_ast,
                    condition=condition,
                    condition_ast=condition_ast,
                    composition=write["composition"],
                    phase=write["phase"],
                    priority=write["priority"],
                    clamp=write["clamp"],
                    telemetry_label=write["telemetry_label"],
                    target_scope=target.scope,
                    reads=_rule_reads(targets, expression_ast, condition_ast),
                    world_columns=_world_columns(target.scope, global_ids, expression_ast, condition_ast),
                )
            )

    if refusals:
        raise VTCWriteRefusalError(tuple(refusals))
    return VTCTransitionRuleProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id, item.telemetry_label),
            )
        )
    )


#: Rule fields the compiler used to accept and now refuses: ``reads`` is derived from
#: the ASTs and ``kind`` was a label with no behaviour (VFS round-2 S8). The authored
#: DTO refuses them as unknown keys; this catches a mapping source that bypasses it.
_DELETED_RULE_FIELDS = ("reads", "kind")


def _coerce_transition_rule(rule: VTCTransitionRuleSource | Mapping[str, Any], rule_index: int) -> dict[str, Any]:
    rule_id = str(_config_field(rule, "id", "")).strip()
    if not rule_id:
        raise ValueError("VTC transition rule requires non-empty id")

    for deleted in _DELETED_RULE_FIELDS:
        if _config_field(rule, deleted, None) is not None:
            raise ValueError(
                f"VTC transition rule '{rule_id}' declares '{deleted}', which no longer exists: "
                "a rule's reads are derived from its expression and condition, and a rule has no kind"
            )

    phase = _config_field(rule, "phase", None)
    if phase is None or not str(phase).strip():
        raise ValueError(f"VTC transition rule '{rule_id}' requires explicit phase")

    raw_condition = _config_field(rule, "condition", None)
    condition = None if raw_condition is None else str(raw_condition).strip()
    if condition == "":
        raise ValueError(f"VTC transition rule '{rule_id}' condition must be non-empty when provided")

    raw_writes = _config_field(rule, "writes", None)
    writes = _iter_config_items(raw_writes)
    if not writes:
        raise ValueError(f"VTC transition rule '{rule_id}' requires at least one write")

    raw_priority = _config_field(rule, "priority", None)
    priority = rule_index if raw_priority is None else int(raw_priority)
    if priority < 0:
        raise ValueError(f"VTC transition rule '{rule_id}' priority must be non-negative")

    return {
        "rule_id": rule_id,
        "phase": str(phase),
        "condition": condition,
        "writes": writes,
        "priority": priority,
    }


def _coerce_transition_rule_write(raw_write: Mapping[str, Any] | WriteSpec, rule: Mapping[str, Any], write_index: int) -> dict[str, Any]:
    rule_id = str(rule["rule_id"])
    condition: str | None
    composition: str
    effect: str | None

    if isinstance(raw_write, WriteSpec):
        variable_id = raw_write.variable_id
        expression = raw_write.expression
        condition = raw_write.condition
        composition = raw_write.composition
        phase = raw_write.phase
        priority = raw_write.priority
        clamp = raw_write.clamp
        telemetry_label = raw_write.telemetry_label
        effect = None
    elif isinstance(raw_write, Mapping):
        variable_id = str(raw_write.get("variable_id", "")).strip()
        expression = str(raw_write.get("expression", "")).strip()
        condition_raw = raw_write.get("condition")
        condition = None if condition_raw is None else str(condition_raw).strip()
        composition = str(raw_write.get("composition", "")).strip()
        phase = str(raw_write.get("phase", rule["phase"])).strip()
        raw_priority = raw_write.get("priority")
        priority = int(rule["priority"]) + write_index if raw_priority is None else int(raw_priority)
        clamp = _coerce_optional_clamp(raw_write.get("clamp"))
        telemetry_label = str(raw_write.get("telemetry_label") or _transition_rule_telemetry_label(rule_id, raw_write)).strip()
        effect_raw = raw_write.get("effect")
        effect = None if effect_raw is None else str(effect_raw).strip()
    else:
        raise TypeError(f"VTC transition rule '{rule_id}' write entry must be a WriteSpec or mapping")

    if not variable_id:
        raise ValueError(f"VTC transition rule '{rule_id}' write requires variable_id")
    if not expression:
        raise ValueError(f"VTC transition rule '{rule_id}' write to '{variable_id}' requires expression")
    if condition == "":
        raise ValueError(f"VTC transition rule '{rule_id}' write to '{variable_id}' condition must be non-empty when provided")
    if composition not in RULE_WRITE_COMPOSITIONS:
        raise ValueError(
            f"VTC transition rule '{rule_id}' write to '{variable_id}' composition '{composition}' is not one of "
            f"{', '.join(RULE_WRITE_COMPOSITIONS)}"
        )
    if not phase:
        raise ValueError(f"VTC transition rule '{rule_id}' write to '{variable_id}' requires phase")
    if priority < 0:
        raise ValueError(f"VTC transition rule '{rule_id}' write to '{variable_id}' priority must be non-negative")
    if not telemetry_label:
        raise ValueError(f"VTC transition rule '{rule_id}' write to '{variable_id}' requires telemetry_label")
    if effect == "":
        raise ValueError(f"VTC transition rule '{rule_id}' write to '{variable_id}' effect must be non-empty when provided")

    return {
        "variable_id": variable_id,
        "expression": expression,
        "condition": condition,
        "composition": composition,
        "phase": phase,
        "priority": priority,
        "clamp": clamp,
        "telemetry_label": telemetry_label,
        "effect": effect,
    }


def _coerce_optional_clamp(raw_clamp: Any) -> tuple[float, float] | None:
    if raw_clamp is None:
        return None
    clamp_values = list(raw_clamp)
    if len(clamp_values) != 2:
        raise ValueError("VTC transition rule clamp must contain exactly two values")
    low = float(clamp_values[0])
    high = float(clamp_values[1])
    if low > high:
        raise ValueError("VTC transition rule clamp lower bound must be <= upper bound")
    return (low, high)


def _transition_rule_telemetry_label(rule_id: str, write: Mapping[str, Any]) -> str:
    """``rule_id:effect``, or ``rule_id:variable_id`` for an unlabelled write. The id names the rule."""
    effect = write.get("effect")
    variable_id = write.get("variable_id", "unknown")
    suffix = effect if effect is not None else variable_id
    return f"{rule_id}:{suffix}"


def _combined_condition(rule_condition: str | None, write_condition: str | None) -> str | None:
    if rule_condition is None:
        return write_condition
    if write_condition is None:
        return rule_condition
    return f"({rule_condition}) and ({write_condition})"


def compile_vtc_action_writes(
    actions: Sequence[VTCActionWriteSource],
    targets: Mapping[str, VTCWriteTarget],
) -> VTCActionWriteProgram:
    """Compile ActionConfig writes into VTC records sorted by phase, priority, and action id."""
    return compile_vtc_action_writes_with_phase_graph(actions, targets, TransitionPhaseGraph.default())


def compile_vtc_action_writes_with_phase_graph(
    actions: Sequence[VTCActionWriteSource],
    targets: Mapping[str, VTCWriteTarget],
    phase_graph: TransitionPhaseGraph,
) -> VTCActionWriteProgram:
    """Compile ActionConfig writes using an explicit VTC transition phase graph."""
    return _compile_vtc_action_writes_with_phase_graph(actions, targets, phase_graph, affordance_index_by_name=None)


def compile_vtc_affordance_occupancy(
    actions: Sequence[VTCActionWriteSource],
    targets: Mapping[str, VTCWriteTarget],
    affordance_ids: Sequence[str],
) -> VTCActionWriteProgram:
    """Compile affordance occupancy action writes with source-affordance row targeting."""
    return compile_vtc_affordance_occupancy_with_phase_graph(actions, targets, affordance_ids, TransitionPhaseGraph.default())


def compile_vtc_affordance_occupancy_with_phase_graph(
    actions: Sequence[VTCActionWriteSource],
    targets: Mapping[str, VTCWriteTarget],
    affordance_ids: Sequence[str],
    phase_graph: TransitionPhaseGraph,
) -> VTCActionWriteProgram:
    """Compile affordance occupancy writes using an explicit VTC transition phase graph."""
    affordance_index_by_name = _affordance_index_by_name(affordance_ids)
    return _compile_vtc_action_writes_with_phase_graph(actions, targets, phase_graph, affordance_index_by_name=affordance_index_by_name)


ACTION_WRITE_AGENT_AXIS_SCOPES: frozenset[VariableScope] = frozenset({VariableScope.AGENT})
"""Scopes an action write may target: an action write lands on the acting agent's row.

A global also has one row per world, and under S1 the acting agent's world is its row,
but admitting action writes to world state is an authoring decision of its own; a
global is written by a transition rule or an interaction effect."""

BATCH_AXIS_SCOPES: frozenset[VariableScope] = frozenset({VariableScope.GLOBAL, VariableScope.AGENT, VariableScope.AFFORDANCE})
"""Scopes whose registry storage leads with the batch axis: one row per agent, or per world.

Under S1 (2026-10-25) the batch is independent single-agent worlds, so the world axis
of a global or an affordance variable and the agent axis coincide at runtime; a
transition rule's target row in any of them is masked by its own agent's (world's)
activity. The authoring contract still tells them apart: a global reads as a scalar in
its world, an affordance variable as one row per affordance (`_SCOPE_SHAPES`)."""

AFFORDANCE_OCCUPANCY_PHASE = "resolve_affordance_access_and_occupancy"
AFFORDANCE_OCCUPANCY_COMPOSITIONS = frozenset({"claim_if_free", "capacity_claim"})


_AGENT_ROW_SHAPES = frozenset({"scalar", "agent"})
"""Value shapes an action write's expression and condition may produce.

An action write lands per acting agent, so its value is one per agent (or a
scalar): an agent row or an occupancy claimant's payload."""


def _target_spellings(name: str, target: VTCWriteTarget) -> tuple[str, ...]:
    """Every spelling of ``name`` the write namespace admits (``_write_expression_namespace`` enumerates the same set)."""
    keys = [name, f"vfs.{name}", f"self.vfs.{name}", f"target.vfs.{name}"]
    if target.meter:
        keys += [f"bar.{name}", f"self.bar.{name}", f"target.bar.{name}"]
    return tuple(keys)


def _rule_reads(targets: Mapping[str, VTCWriteTarget], *asts: ASTNode | None) -> tuple[str, ...]:
    """The ids of every target the ASTs read, sorted: a rule's reads are derived, never authored (S8).

    Runs after the type check, so every path the ASTs read is either a target
    spelling or the context's own ``agent_id``, which is no variable.
    """
    spellings = {spelling: name for name, target in targets.items() for spelling in _target_spellings(name, target)}
    paths = frozenset().union(*(read_paths(ast) for ast in asts if ast is not None))
    return tuple(sorted({spellings[path] for path in paths if path in spellings}))


def _world_columns(target_scope: VariableScope, global_ids: frozenset[str], *asts: ASTNode | None) -> frozenset[str]:
    """The globals a rule on affordance state reads (any spelling the context resolves); none for other targets."""
    if target_scope != VariableScope.AFFORDANCE:
        return frozenset()
    paths = frozenset().union(*(read_paths(ast) for ast in asts if ast is not None))
    return frozenset(
        name for name in global_ids if paths & {name, f"vfs.{name}", f"self.vfs.{name}", f"target.vfs.{name}", f"global.vfs.{name}"}
    )


_RULE_ADMITTED_SHAPES: dict[VariableScope, frozenset[str]] = {
    VariableScope.GLOBAL: frozenset({"scalar"}),
    VariableScope.AGENT: _AGENT_ROW_SHAPES,
    VariableScope.AFFORDANCE: frozenset({"scalar", "affordance"}),
}
"""Value shapes a transition-rule write (expression and condition) may produce, by target scope."""


def _action_write_scope_refusal(
    write: WriteSpec,
    action_name: str,
    target_scope: VariableScope | None,
    affordance_index: int | None,
) -> str | None:
    """Why an action write cannot apply to its target's declared scope, or None when it can.

    An action write applies per acting agent. Its target must therefore have one row
    per agent (an agent-axis scope or a meter bar), except for an affordance occupancy
    claim, which writes the acting action's source-affordance row of an
    affordance-scoped variable.
    """
    prefix = f"Action '{action_name}' write '{write.telemetry_label}' targets"
    if target_scope is None:
        return f"{prefix} unknown state variable '{write.variable_id}'. Declare it as a VFS variable or meter bar."
    if target_scope == VariableScope.AFFORDANCE:
        is_claim = (
            write.composition in AFFORDANCE_OCCUPANCY_COMPOSITIONS
            and write.phase == AFFORDANCE_OCCUPANCY_PHASE
            and affordance_index is not None
        )
        if is_claim:
            return None
        return (
            f"{prefix} variable '{write.variable_id}', declared scope 'affordance'. An action writes affordance-scoped "
            f"state only as an occupancy claim: composition {' or '.join(sorted(AFFORDANCE_OCCUPANCY_COMPOSITIONS))} "
            f"at phase '{AFFORDANCE_OCCUPANCY_PHASE}', from an action that declares source_affordance."
        )
    if write.composition in AFFORDANCE_OCCUPANCY_COMPOSITIONS:
        return (
            f"{prefix} variable '{write.variable_id}', declared scope '{target_scope.value}', with composition "
            f"'{write.composition}'. An occupancy claim writes its action's source-affordance row of an "
            "affordance-scoped variable; declare the claimed state with scope affordance."
        )
    if target_scope in ACTION_WRITE_AGENT_AXIS_SCOPES:
        return None
    admitted = ", ".join(sorted(scope.value for scope in ACTION_WRITE_AGENT_AXIS_SCOPES))
    return (
        f"{prefix} variable '{write.variable_id}', declared scope '{target_scope.value}'. An action write applies to "
        f"the acting agent's row, so its target must be a meter bar or a variable of scope {admitted}. "
        f"A '{target_scope.value}' variable is written by a transition rule or an interaction effect."
    )


def _compile_vtc_action_writes_with_phase_graph(
    actions: Sequence[VTCActionWriteSource],
    targets: Mapping[str, VTCWriteTarget],
    phase_graph: TransitionPhaseGraph,
    *,
    affordance_index_by_name: Mapping[str, int] | None,
) -> VTCActionWriteProgram:
    parser = ExpressionParser()
    schema, shapes = _write_expression_namespace(targets)
    checker = TypeChecker(schema=schema)
    compiled_writes: list[CompiledVTCActionWrite] = []
    refusals: list[VTCWriteRefusal] = []
    admitted = phase_graph.action_phases

    for action in actions:
        source_affordance = _action_source_affordance(action)
        affordance_index = _action_affordance_index(source_affordance, affordance_index_by_name, action.name)
        for write_index, raw_write in enumerate(action.writes):
            write = _coerce_write_spec(raw_write, action.name)
            origin_key = f"actions:{action.name}:writes[{write_index}]"
            if write.phase not in admitted:
                if write.phase in phase_graph.ordered_phases:
                    reason = f"phase '{write.phase}', which runs without the tick's actions, so the write could never apply"
                else:
                    reason = _unknown_phase_reason(write.phase)
                refusals.append(
                    VTCWriteRefusal(
                        origin_key=origin_key,
                        kind="phase",
                        message=(
                            f"Action '{action.name}' write '{write.telemetry_label}' is scheduled at {reason}. "
                            f"Action writes are admitted at: {', '.join(admitted)}"
                        ),
                    )
                )
                continue
            target = targets.get(write.variable_id)
            scope_refusal = _action_write_scope_refusal(write, action.name, None if target is None else target.scope, affordance_index)
            if scope_refusal is not None:
                refusals.append(VTCWriteRefusal(origin_key=origin_key, kind="scope", message=scope_refusal))
                continue
            assert target is not None
            expression_ast = parser.parse(write.expression)
            condition_ast = parser.parse(write.condition) if write.condition is not None else None
            type_refusal = _write_type_refusal(
                checker,
                expression_ast=expression_ast,
                expression=write.expression,
                condition_ast=condition_ast,
                condition=write.condition,
                target_id=write.variable_id,
                target_type=target.type,
                prefix=f"Action '{action.name}' write '{write.telemetry_label}'",
            )
            if type_refusal is not None:
                refusals.append(VTCWriteRefusal(origin_key=origin_key, kind="type", message=type_refusal))
                continue
            # From here on the ASTs are the inlined ones: what the write evaluates (S4).
            inlined = _inline_expression_reads(
                targets,
                expression_ast=expression_ast,
                expression=write.expression,
                condition_ast=condition_ast,
                condition=write.condition,
                prefix=f"Action '{action.name}' write '{write.telemetry_label}'",
            )
            if isinstance(inlined, str):
                refusals.append(VTCWriteRefusal(origin_key=origin_key, kind="type", message=inlined))
                continue
            expression_ast, condition_ast = inlined
            # A shape refusal is the second half of the type proof (payload, then axes),
            # so it reports under the same kind.
            shape_refusal = _write_shape_refusal(
                expression_ast=expression_ast,
                expression=write.expression,
                condition_ast=condition_ast,
                condition=write.condition,
                shapes=shapes,
                admitted_expression=_AGENT_ROW_SHAPES,
                admitted_condition=_AGENT_ROW_SHAPES,
                target_id=write.variable_id,
                target_scope=target.scope,
                prefix=f"Action '{action.name}' write '{write.telemetry_label}'",
            )
            if shape_refusal is not None:
                refusals.append(VTCWriteRefusal(origin_key=origin_key, kind="type", message=shape_refusal))
                continue
            compiled_writes.append(
                CompiledVTCActionWrite(
                    action_id=action.id,
                    action_name=action.name,
                    source_affordance=source_affordance,
                    affordance_index=affordance_index,
                    variable_id=write.variable_id,
                    target_scope=target.scope,
                    expression=write.expression,
                    expression_ast=expression_ast,
                    condition=write.condition,
                    condition_ast=condition_ast,
                    composition=write.composition,
                    phase=write.phase,
                    priority=write.priority,
                    clamp=write.clamp,
                    telemetry_label=write.telemetry_label,
                )
            )

    if refusals:
        raise VTCWriteRefusalError(tuple(refusals))
    return VTCActionWriteProgram(
        writes=tuple(
            sorted(
                compiled_writes,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.action_id, item.telemetry_label),
            )
        )
    )


def _affordance_index_by_name(affordance_ids: Sequence[str]) -> dict[str, int]:
    index_by_name: dict[str, int] = {}
    for index, raw_name in enumerate(affordance_ids):
        name = str(raw_name)
        if not name:
            raise ValueError("VTC affordance occupancy compiler received an empty affordance id")
        if name in index_by_name:
            raise ValueError(f"Duplicate affordance id '{name}' in VTC affordance occupancy compiler")
        index_by_name[name] = index
    return index_by_name


def _action_source_affordance(action: VTCActionWriteSource) -> str | None:
    source_affordance = action.source_affordance
    if source_affordance is None:
        return None
    return str(source_affordance)


def _action_affordance_index(
    source_affordance: str | None,
    affordance_index_by_name: Mapping[str, int] | None,
    action_name: str,
) -> int | None:
    if affordance_index_by_name is None or source_affordance is None:
        return None
    try:
        return affordance_index_by_name[source_affordance]
    except KeyError as exc:
        raise ValueError(f"Action '{action_name}' references unknown source_affordance '{source_affordance}'") from exc


def _coerce_write_spec(write: WriteSpec | Mapping[str, Any], action_name: str) -> WriteSpec:
    if isinstance(write, WriteSpec):
        return write
    if isinstance(write, Mapping):
        return WriteSpec.model_validate(dict(write))
    raise TypeError(f"Action '{action_name}' write entry must be a WriteSpec or mapping")


def compile_vtc_threshold_cascades(
    cascades: Sequence[VTCThresholdCascadeSource | Mapping[str, Any]],
    meters: Sequence[VTCPassiveDepletionSource | Mapping[str, Any]],
) -> VTCThresholdCascadeProgram:
    """Compile bars.yaml cascades into VTC threshold-delta transition rules."""
    return compile_vtc_threshold_cascades_with_phase_graph(cascades, meters, TransitionPhaseGraph.default())


def compile_vtc_threshold_cascades_with_phase_graph(
    cascades: Sequence[VTCThresholdCascadeSource | Mapping[str, Any]],
    meters: Sequence[VTCPassiveDepletionSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCThresholdCascadeProgram:
    """Compile bars.yaml cascades using an explicit VTC transition phase graph.

    ``meters`` supplies the declared bounds of each cascade's *target*: a cascade
    writes the target meter, so the target's ceiling is the one that applies.
    """
    parser = ExpressionParser()
    compiled_rules: list[CompiledVTCThresholdCascade] = []
    bounds_by_meter: dict[str, tuple[float, float]] = {}
    for raw_meter in meters:
        if isinstance(raw_meter, Mapping):
            meter_name = str(raw_meter["name"])
            meter_bounds = raw_meter["bounds"]
        else:
            meter_name = raw_meter.name
            meter_bounds = raw_meter.bounds
        bounds_by_meter[meter_name] = _coerce_meter_bounds(meter_bounds)

    for priority, raw_cascade in enumerate(cascades):
        cascade = _coerce_threshold_cascade(raw_cascade)
        threshold_literal = _format_rule_float(cascade["threshold"])
        strength_literal = _format_rule_float(-cascade["strength"])
        condition = f"bar.{cascade['source']} < {threshold_literal}"
        expression = (
            "0.0"
            if cascade["threshold"] == 0.0
            else f"{strength_literal} * (({threshold_literal} - bar.{cascade['source']}) / {threshold_literal})"
        )
        rule_id = cascade["rule_id"]
        target_bounds = bounds_by_meter.get(cascade["target"])
        if target_bounds is None:
            raise ValueError(
                "Threshold cascade targets a meter with no declared bounds.\n"
                f"  Cascade: {rule_id}\n"
                f"  Target meter: {cascade['target']}\n"
                f"  Meters supplied: {sorted(bounds_by_meter)}\n"
                "  Rule: a cascade writes its target, so the target must declare bounds.min/bounds.max."
            )
        compiled_rules.append(
            CompiledVTCThresholdCascade(
                rule_id=rule_id,
                kind="threshold_delta",
                source_variable_id=cascade["source"],
                variable_id=cascade["target"],
                expression=expression,
                expression_ast=parser.parse(expression),
                condition=condition,
                condition_ast=parser.parse(condition),
                composition="additive_delta",
                phase="apply_threshold_cascades",
                priority=priority,
                clamp=target_bounds,
                telemetry_label=f"threshold_delta:{rule_id}",
                cascade_threshold=cascade["threshold"],
                cascade_strength=cascade["strength"],
            )
        )

    return VTCThresholdCascadeProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


def _coerce_threshold_cascade(cascade: VTCThresholdCascadeSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(cascade, Mapping):
        source = str(cascade["source"])
        target = str(cascade["target"])
        threshold = float(cascade["threshold"])
        strength = float(cascade["strength"])
        rule_id = str(cascade.get("id") or cascade.get("rule_id") or f"{source}->{target}")
    else:
        source = cascade.source
        target = cascade.target
        threshold = float(cascade.threshold)
        strength = float(cascade.strength)
        rule_id = str(getattr(cascade, "id", None) or f"{source}->{target}")

    return {
        "rule_id": rule_id,
        "source": source,
        "target": target,
        "threshold": threshold,
        "strength": strength,
    }


def compile_vtc_bounds_clamps_with_phase_graph(
    meters: Sequence[VTCPassiveDepletionSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCBoundsClampProgram:
    """Compile declared meter bounds using an explicit VTC transition phase graph."""
    compiled_rules: list[CompiledVTCBoundsClamp] = []

    for priority, raw_meter in enumerate(meters):
        meter = _coerce_bounds_clamp(raw_meter)
        low_literal = _format_rule_float(meter["bounds_min"])
        high_literal = _format_rule_float(meter["bounds_max"])
        compiled_rules.append(
            CompiledVTCBoundsClamp(
                rule_id=f"bounds:{meter['name']}",
                kind="bounds_clamp",
                source_variable_id=meter["name"],
                variable_id=meter["name"],
                expression=f"clamp(bar.{meter['name']}, {low_literal}, {high_literal})",
                condition=None,
                composition="overwrite",
                phase="clamp_and_validate",
                priority=priority,
                clamp=(meter["bounds_min"], meter["bounds_max"]),
                telemetry_label=f"bounds_clamp:{meter['name']}",
            )
        )

    return VTCBoundsClampProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


def _coerce_bounds_clamp(meter: VTCPassiveDepletionSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(meter, Mapping):
        name = str(meter["name"])
        bounds = meter["bounds"]
    else:
        name = meter.name
        bounds = meter.bounds

    bounds_min, bounds_max = _coerce_meter_bounds(bounds)
    return {
        "name": name,
        "bounds_min": bounds_min,
        "bounds_max": bounds_max,
    }


def compile_vtc_passive_depletions(meters: Sequence[VTCPassiveDepletionSource | Mapping[str, Any]]) -> VTCPassiveDepletionProgram:
    """Compile meter passive depletion rates into VTC overwrite rules."""
    return compile_vtc_passive_depletions_with_phase_graph(meters, TransitionPhaseGraph.default())


def compile_vtc_passive_depletions_with_phase_graph(
    meters: Sequence[VTCPassiveDepletionSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCPassiveDepletionProgram:
    """Compile meter passive depletion rates using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    compiled_rules: list[CompiledVTCPassiveDepletion] = []

    for priority, raw_meter in enumerate(meters):
        meter = _coerce_passive_depletion(raw_meter)
        depletion_literal = _format_rule_float(meter["passive"])
        expression = f"bar.{meter['name']} - ({depletion_literal} * temporal.depletion_multiplier)"
        compiled_rules.append(
            CompiledVTCPassiveDepletion(
                rule_id=f"passive:{meter['name']}",
                kind="passive_depletion",
                source_variable_id=meter["name"],
                variable_id=meter["name"],
                expression=expression,
                expression_ast=parser.parse(expression),
                condition=None,
                condition_ast=None,
                composition="overwrite",
                phase="apply_passive_depletion",
                priority=priority,
                clamp=(meter["bounds_min"], meter["bounds_max"]),
                telemetry_label=f"passive_depletion:{meter['name']}",
                passive_rate=meter["passive"],
            )
        )

    return VTCPassiveDepletionProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


def _coerce_meter_bounds(bounds: Any) -> tuple[float, float]:
    """Read the declared [min, max] off a bar's bounds, mapping or attribute form.

    Shared by the passive-depletion and threshold-cascade coercions so the declared
    ceiling is read one way in both. `_coerce_terminal_condition_meter` deliberately
    does NOT use it: it needs `lethal_min`/`lethal_max` as well, which a 2-tuple
    cannot carry.
    """
    if isinstance(bounds, Mapping):
        return float(bounds["min"]), float(bounds["max"])
    return float(bounds.min), float(bounds.max)


def _coerce_passive_depletion(meter: VTCPassiveDepletionSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(meter, Mapping):
        name = str(meter["name"])
        depletion = meter["depletion"]
        passive = float(depletion["passive"] if isinstance(depletion, Mapping) else getattr(depletion, "passive"))
        bounds = meter["bounds"]
    else:
        name = meter.name
        passive = float(meter.depletion.passive)
        bounds = meter.bounds

    bounds_min, bounds_max = _coerce_meter_bounds(bounds)
    return {
        "name": name,
        "passive": passive,
        "bounds_min": bounds_min,
        "bounds_max": bounds_max,
    }


def compile_vtc_modulations(modulations: Sequence[VTCModulationSource | Mapping[str, Any]]) -> VTCModulationProgram:
    """Compile affordance modulation parameters into VTC multiplier rules."""
    return compile_vtc_modulations_with_phase_graph(modulations, TransitionPhaseGraph.default())


def compile_vtc_modulations_with_phase_graph(
    modulations: Sequence[VTCModulationSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCModulationProgram:
    """Compile affordance modulation parameters using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    compiled_rules: list[CompiledVTCModulation] = []

    for raw_modulation in modulations:
        modulation = _coerce_modulation(raw_modulation)
        for affordance in modulation["affordances"]:
            threshold_literal = _format_rule_float(modulation["threshold"])
            min_multiplier_literal = _format_rule_float(modulation["min_multiplier"])
            if modulation["threshold"] == 0.0:
                expression = "1.0"
            else:
                expression = (
                    f"where(bar.{modulation['bar']} < {threshold_literal}, "
                    f"{min_multiplier_literal} + (1.0 - {min_multiplier_literal}) * "
                    f"(bar.{modulation['bar']} / {threshold_literal}), 1.0)"
                )
            rule_id = f"{modulation['bar']}->{affordance}"
            compiled_rules.append(
                CompiledVTCModulation(
                    rule_id=rule_id,
                    kind="modulation",
                    source_variable_id=modulation["bar"],
                    target_affordance_id=affordance,
                    variable_id=f"affordance.{affordance}.multiplier",
                    expression=expression,
                    expression_ast=parser.parse(expression),
                    condition=None,
                    condition_ast=None,
                    composition="multiplicative_modifier",
                    # Not runner-dispatched: the affordance engine reads these multipliers
                    # while it applies affordance effects, so they belong to that phase.
                    phase="apply_action_effects",
                    priority=len(compiled_rules),
                    # B3: this clamp bounds an affordance EFFECTIVENESS MULTIPLIER, not a
                    # meter. [0, 1] is the multiplier's own domain and has nothing to do
                    # with bars.*.bounds — do not "harmonise" it onto the declared meter
                    # bounds the way WS-1(e) did for the passive/cascade/runtime clamps.
                    clamp=(0.0, 1.0),
                    telemetry_label=f"modulation:{rule_id}",
                    modulation_threshold=modulation["threshold"],
                    min_multiplier=modulation["min_multiplier"],
                )
            )

    return VTCModulationProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


def _coerce_modulation(modulation: VTCModulationSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(modulation, Mapping):
        bar = str(modulation["bar"])
        affordances = [str(affordance) for affordance in modulation["affordances"]]
        modulation_type = str(modulation["type"])
        threshold = float(modulation["threshold"])
        min_multiplier = float(modulation["min_multiplier"])
    else:
        bar = modulation.bar
        affordances = [str(affordance) for affordance in modulation.affordances]
        modulation_type = str(modulation.type)
        threshold = float(modulation.threshold)
        min_multiplier = float(modulation.min_multiplier)

    if modulation_type != "linear_multiplier":
        raise ValueError(f"Unsupported VTC modulation type '{modulation_type}' for bar '{bar}'")

    return {
        "bar": bar,
        "affordances": affordances,
        "threshold": threshold,
        "min_multiplier": min_multiplier,
    }


def compile_vtc_interaction_progress(
    affordances: Sequence[VTCInteractionProgressSource | Mapping[str, Any]],
) -> VTCInteractionProgressProgram:
    """Compile multi-tick affordance durations into VTC progress and completion rules."""
    return compile_vtc_interaction_progress_with_phase_graph(affordances, TransitionPhaseGraph.default())


def compile_vtc_interaction_progress_with_phase_graph(
    affordances: Sequence[VTCInteractionProgressSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCInteractionProgressProgram:
    """Compile multi-tick affordance durations using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    progress_rules: list[CompiledVTCInteractionProgress] = []
    completion_bonus_rules: list[CompiledVTCInteractionCompletionBonus] = []
    progress_expression = "where(same_affordance and affordance_is_open and chosen_interact, interaction_progress + 1, 0)"

    for raw_affordance in affordances:
        affordance = _coerce_interaction_progress_affordance(raw_affordance)
        if affordance["interaction_type"] not in PROGRESS_INTERACTION_TYPES:
            continue

        name = affordance["name"]
        duration_ticks = affordance["duration_ticks"]
        priority = len(progress_rules)
        slug = _rule_slug(name)
        progress_rules.append(
            CompiledVTCInteractionProgress(
                rule_id=f"{slug}_advance_interaction_progress",
                kind="interaction_progress",
                source_variable_id="interaction_progress",
                target_affordance_id=name,
                variable_id="interaction_progress",
                expression=progress_expression,
                expression_ast=parser.parse(progress_expression),
                condition=None,
                condition_ast=None,
                composition="overwrite",
                phase="advance_interaction_progress",
                priority=priority,
                clamp=None,
                telemetry_label=f"interaction_progress:{name}",
                duration_ticks=duration_ticks,
            )
        )

        completion_expression = f"interaction_progress >= {duration_ticks}"
        completion_bonus_rules.append(
            CompiledVTCInteractionCompletionBonus(
                rule_id=f"{slug}_completion_bonus",
                kind="interaction_completion_bonus",
                source_variable_id="interaction_progress",
                target_affordance_id=name,
                variable_id=f"affordance.{name}.completed",
                expression=completion_expression,
                expression_ast=parser.parse(completion_expression),
                condition=None,
                condition_ast=None,
                composition="event",
                phase="apply_completion_bonuses",
                priority=priority,
                clamp=None,
                telemetry_label=f"interaction_completion_bonus:{name}",
                duration_ticks=duration_ticks,
            )
        )

    return VTCInteractionProgressProgram(
        progress_rules=tuple(
            sorted(
                progress_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        ),
        completion_bonus_rules=tuple(
            sorted(
                completion_bonus_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        ),
    )


def _coerce_interaction_progress_affordance(
    affordance: VTCInteractionProgressSource | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(affordance, Mapping):
        name = str(affordance["name"])
        interaction_type = str(affordance["interaction_type"])
        duration_ticks = affordance.get("duration_ticks")
    else:
        name = affordance.name
        interaction_type = str(affordance.interaction_type)
        duration_ticks = affordance.duration_ticks

    if interaction_type not in INTERACTION_TYPES:
        raise ValueError(
            f"Unsupported VTC interaction_type '{interaction_type}' for affordance '{name}' — "
            f"the closed vocabulary is {sorted(INTERACTION_TYPES)} (townlet.config.interaction_type)"
        )
    if interaction_type in PROGRESS_INTERACTION_TYPES:
        if duration_ticks is None:
            raise ValueError(f"Affordance '{name}' interaction_type='{interaction_type}' requires duration_ticks")
        duration = int(duration_ticks)
        if duration <= 0:
            raise ValueError(f"Affordance '{name}' duration_ticks must be positive, got {duration}")
    else:
        duration = None

    return {
        "name": name,
        "interaction_type": interaction_type,
        "duration_ticks": duration,
    }


def compile_vtc_terminal_conditions(
    meters: Sequence[VTCTerminalConditionSource | Mapping[str, Any]],
) -> VTCTerminalConditionProgram:
    """Compile lethal meter bounds into VTC terminal-condition rules."""
    return compile_vtc_terminal_conditions_with_phase_graph(meters, TransitionPhaseGraph.default())


def compile_vtc_terminal_conditions_with_phase_graph(
    meters: Sequence[VTCTerminalConditionSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCTerminalConditionProgram:
    """Compile lethal meter bounds using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    compiled_rules: list[CompiledVTCTerminalCondition] = []

    for raw_meter in meters:
        meter = _coerce_terminal_condition_meter(raw_meter)
        if meter["lethal_min"]:
            threshold = meter["min"]
            operator = "<="
            name = meter["name"]
            expression = f"bar.{name} {operator} {_format_rule_float(threshold)}"
            compiled_rules.append(
                CompiledVTCTerminalCondition(
                    rule_id=f"terminal:{name}:min",
                    kind="terminal_condition",
                    source_variable_id=name,
                    variable_id="done",
                    expression=expression,
                    expression_ast=parser.parse(expression),
                    condition=None,
                    condition_ast=None,
                    composition="event",
                    phase="evaluate_terminal_conditions",
                    priority=len(compiled_rules),
                    clamp=None,
                    telemetry_label=f"terminal_condition:{name}:min",
                    operator=operator,
                    threshold=threshold,
                )
            )
        if meter["lethal_max"]:
            threshold = meter["max"]
            operator = ">="
            name = meter["name"]
            expression = f"bar.{name} {operator} {_format_rule_float(threshold)}"
            compiled_rules.append(
                CompiledVTCTerminalCondition(
                    rule_id=f"terminal:{name}:max",
                    kind="terminal_condition",
                    source_variable_id=name,
                    variable_id="done",
                    expression=expression,
                    expression_ast=parser.parse(expression),
                    condition=None,
                    condition_ast=None,
                    composition="event",
                    phase="evaluate_terminal_conditions",
                    priority=len(compiled_rules),
                    clamp=None,
                    telemetry_label=f"terminal_condition:{name}:max",
                    operator=operator,
                    threshold=threshold,
                )
            )

    return VTCTerminalConditionProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


def _coerce_terminal_condition_meter(meter: VTCTerminalConditionSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(meter, Mapping):
        name = str(meter["name"])
        bounds = meter["bounds"]
    else:
        name = meter.name
        bounds = meter.bounds

    if isinstance(bounds, Mapping):
        min_value = float(bounds["min"])
        max_value = float(bounds["max"])
        lethal_min = bool(bounds["lethal_min"])
        lethal_max = bool(bounds["lethal_max"])
    else:
        min_value = float(bounds.min)
        max_value = float(bounds.max)
        lethal_min = bool(bounds.lethal_min)
        lethal_max = bool(bounds.lethal_max)

    return {
        "name": name,
        "min": min_value,
        "max": max_value,
        "lethal_min": lethal_min,
        "lethal_max": lethal_max,
    }


def compile_vtc_affordance_gates(affordances: Sequence[VTCAffordanceGateSource | Mapping[str, Any]]) -> VTCAffordanceGateProgram:
    """Compile affordance opening hours into VTC action-legality gate rules."""
    return compile_vtc_affordance_gates_with_phase_graph(affordances, TransitionPhaseGraph.default())


def compile_vtc_affordance_gates_with_phase_graph(
    affordances: Sequence[VTCAffordanceGateSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCAffordanceGateProgram:
    """Compile affordance opening hours using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    compiled_rules: list[CompiledVTCAffordanceGate] = []

    for priority, raw_affordance in enumerate(affordances):
        affordance = _coerce_affordance_gate(raw_affordance)
        expression = _opening_hours_expression(affordance["windows"])
        name = affordance["name"]
        compiled_rules.append(
            CompiledVTCAffordanceGate(
                rule_id=f"{_rule_slug(name)}_open_window",
                kind="affordance_gate",
                source_variable_id="time_of_day",
                target_affordance_id=name,
                variable_id=f"affordance.{name}.available",
                expression=expression,
                expression_ast=parser.parse(expression),
                condition=None,
                condition_ast=None,
                composition="overwrite",
                phase="compute_action_legality_masks",
                priority=priority,
                clamp=None,
                telemetry_label=f"affordance_gate:{name}",
            )
        )

    return VTCAffordanceGateProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


def _coerce_affordance_gate(affordance: VTCAffordanceGateSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(affordance, Mapping):
        name = str(affordance["name"])
        opening_hours = affordance["opening_hours"]
    else:
        name = affordance.name
        opening_hours = affordance.opening_hours

    enabled = _opening_hours_enabled(opening_hours)
    if not enabled:
        return {"name": name, "windows": [(0.0, 24.0)]}

    windows = _opening_hours_windows(opening_hours)
    if not windows:
        raise ValueError(f"Affordance '{name}' opening_hours.enabled=true requires at least one VTC gate window")
    return {"name": name, "windows": windows}


def _opening_hours_enabled(opening_hours: Any) -> bool:
    if isinstance(opening_hours, Mapping):
        return bool(opening_hours["enabled"])
    return bool(opening_hours.enabled)


def _opening_hours_windows(opening_hours: Any) -> list[tuple[float, float]]:
    schedule = opening_hours["schedule"] if isinstance(opening_hours, Mapping) else opening_hours.schedule
    windows: list[tuple[float, float]] = []
    for window in schedule:
        if isinstance(window, Mapping):
            start = window["start"]
            end = window["end"]
        else:
            start = window.start
            end = window.end
        windows.append((float(start), float(end)))
    return windows


def _opening_hours_expression(windows: Sequence[tuple[float, float]]) -> str:
    expressions = [
        f"time_in_window(temporal.time_of_day, {_format_rule_float(start)}, {_format_rule_float(end)})" for start, end in windows
    ]
    return " || ".join(expressions)


def _config_field(config: Any, field: str, default: Any = None) -> Any:
    if isinstance(config, Mapping):
        return config.get(field, default)
    return getattr(config, field, default)


def _iter_config_items(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value)


def _rule_slug(name: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in name).strip("_") or "affordance"


def _required_clamp(clamp: tuple[float, float] | None, telemetry_label: str) -> tuple[float, float]:
    if clamp is None:
        raise ValueError(f"Generated VTC rule '{telemetry_label}' requires explicit clamp bounds for scripted execution")
    return clamp


def _format_rule_float(value: float) -> str:
    return repr(float(value))
