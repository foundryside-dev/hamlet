"""One resolver for every expression consumer (VFS round-2 S5).

A ``Namespace`` is the compiler's symbol table as an expression reads it: every
registry variable with its declared scope and type, every meter, and every item-state
variable. A ``ReadContext`` says what one consumer's runtime serves: which registry
scopes a bare name may read, whether meters and an item are in play, which
engine-provided and pipeline-local names exist, and which function requirements
(history, step, positions) the runtime carries.

``Namespace.entries(context)`` is the one enumeration of what a context can read,
keyed by the canonical spelling (``townlet.world.expression.references``). Every type
checker is fed ``schema(context)`` and every shape proof ``shapes(context)``, both
projections of that enumeration; every runtime context resolves a path through the
same grammar (``parse_reference``). ``refusal(path, context)`` names, for any other
spelling, the one spelling to write instead, so no alias is ever served.

The module also owns expression inlining (VFS round-2 S4 and its follow-up): a
consumer that reads an expression variable reads the function, not a stored value,
unless the expression needs evaluation-time context; and a ``tick``-lifetime one that
cannot be inlined is refused, because tick state is reset before any consumer runs.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, fields, replace
from enum import StrEnum
from typing import Any, Protocol

from townlet.vfs.schema import VariableScope
from townlet.world.expression.ast_nodes import ASTNode, PathAccess, Variable, read_paths
from townlet.world.expression.functions import REQUIRES_HISTORY, REQUIRES_POSITIONS, REQUIRES_STEP, unserved_requirement
from townlet.world.expression.references import ITEM_ROOT, METER_ROOT, Reference, ReferenceKind, parse_reference

__all__ = [
    "AGENT_EXPRESSION",
    "EFFECT_LOCALS",
    "EFFECT_PIPELINE",
    "ENGINE_TICK",
    "GLOBAL_EXPRESSION",
    "INTERACTION_PIPELINE",
    "SPAWN_PREDICATE",
    "SPELLING_RULE",
    "TRANSITION_WRITE",
    "CommandSymbols",
    "ExpressionSource",
    "Namespace",
    "ReadContext",
    "SpellingError",
    "Symbol",
    "SymbolKind",
    "expression_sources",
    "inline_expression_reads",
    "substitute_reads",
]

ENGINE_TICK = "tick"
"""The engine-published step counter: a global registry variable every context reads by bare name."""

EFFECT_LOCALS: Mapping[str, str] = {"intensity": "float", "elapsed_ticks": "float", "duration_remaining": "float"}
"""The names an active effect binds while its pipeline runs (``CommandExecutor._make_eval_context``)."""

SPELLING_RULE = (
    "A variable is its bare id, read in this world by its declared scope; a meter is 'bar.<name>'; "
    "the state of the item a context is bound to is 'item.<name>'."
)


class SpellingError(ValueError):
    """A reference spelling a context does not accept; the message names the one to use."""


class SymbolKind(StrEnum):
    VARIABLE = "variable"
    METER = "meter"
    ITEM_STATE = "item state"
    ENGINE = "engine name"
    LOCAL = "pipeline-local name"


_SCOPE_SHAPES: dict[VariableScope, str] = {
    VariableScope.GLOBAL: "scalar",
    VariableScope.AGENT: "agent",
    VariableScope.AFFORDANCE: "affordance",
}
"""The leading registry axes a read of each scope yields, in this world (S1)."""


@dataclass(frozen=True)
class Symbol:
    """One readable thing: what it is, its expression type, and its registry scope when it is a variable."""

    kind: SymbolKind
    name: str
    type: str
    scope: VariableScope | None

    @property
    def spelling(self) -> str:
        if self.kind == SymbolKind.METER:
            return Reference(ReferenceKind.METER, self.name).spelling
        if self.kind == SymbolKind.ITEM_STATE:
            return Reference(ReferenceKind.ITEM, self.name).spelling
        return self.name

    @property
    def shape(self) -> str:
        """The leading axes a read yields (``VFSProfileCompiler.expression_shape`` labels)."""
        if self.kind == SymbolKind.VARIABLE:
            assert self.scope is not None
            return _SCOPE_SHAPES[self.scope]
        if self.kind == SymbolKind.METER:
            return "agent"
        if self.kind == SymbolKind.ENGINE and self.name == "agent_id":
            return "agent"
        return "scalar"


@dataclass(frozen=True)
class ReadContext:
    """What one consumer's runtime serves."""

    label: str
    variable_scopes: frozenset[VariableScope]
    meters: bool
    item: bool
    engine: Mapping[str, str]
    locals: Mapping[str, str]
    carries: frozenset[str]

    def with_item(self, item: bool) -> ReadContext:
        """This context with (or without) an item bound."""
        return replace(self, item=item)


_EVERY_REQUIREMENT = frozenset({REQUIRES_HISTORY, REQUIRES_STEP, REQUIRES_POSITIONS})

GLOBAL_EXPRESSION = ReadContext(
    label="a global variable expression",
    variable_scopes=frozenset({VariableScope.GLOBAL}),
    meters=True,
    item=False,
    engine={},
    locals={},
    carries=_EVERY_REQUIREMENT,
)
AGENT_EXPRESSION = ReadContext(
    label="an agent variable expression",
    variable_scopes=frozenset({VariableScope.GLOBAL, VariableScope.AGENT}),
    meters=True,
    item=False,
    engine={},
    locals={},
    carries=_EVERY_REQUIREMENT,
)
TRANSITION_WRITE = ReadContext(
    label="a transition write or rule",
    variable_scopes=frozenset({VariableScope.GLOBAL, VariableScope.AGENT, VariableScope.AFFORDANCE}),
    meters=True,
    item=False,
    engine={"agent_id": "int"},
    locals={},
    carries=frozenset(),
)
SPAWN_PREDICATE = ReadContext(
    label="an item spawn predicate",
    variable_scopes=frozenset({VariableScope.GLOBAL, VariableScope.AGENT}),
    meters=True,
    item=False,
    engine={},
    locals={},
    carries=frozenset(),
)
INTERACTION_PIPELINE = ReadContext(
    label="an interaction pipeline",
    variable_scopes=frozenset({VariableScope.GLOBAL, VariableScope.AGENT}),
    meters=True,
    item=False,
    engine={},
    locals={},
    carries=frozenset({REQUIRES_POSITIONS}),
)
"""An affordance interaction (no item) or an item interaction (``with_item(True)``)."""
EFFECT_PIPELINE = ReadContext(
    label="an effect pipeline",
    variable_scopes=frozenset({VariableScope.GLOBAL, VariableScope.AGENT}),
    meters=True,
    item=False,
    engine={},
    locals=EFFECT_LOCALS,
    carries=frozenset({REQUIRES_POSITIONS}),
)
"""An effect of any scope; an item-scoped effect is ``with_item(True)``."""

_LEGACY_ENTITY_QUALIFIERS = frozenset({"self", "target", "global", "agent"})
_LEGACY_STORAGE_ROOT = "vfs"


class _RegistryVariable(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def scope(self) -> VariableScope | str: ...

    @property
    def type(self) -> str: ...


class _ItemVariable(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def type(self) -> str: ...


class _ItemProfile(Protocol):
    @property
    def variables(self) -> Sequence[_ItemVariable]: ...


class Namespace:
    """The symbol table as expressions read it, projected per ``ReadContext``."""

    def __init__(
        self,
        *,
        variables: Iterable[tuple[str, VariableScope | str, str]],
        meters: Iterable[str],
        item_state: Mapping[str, str],
    ) -> None:
        """``variables`` are ``(id, scope, declared type)`` registry variables (the engine's ``tick`` included)."""
        self._variables: dict[str, Symbol] = {}
        for name, scope, declared_type in variables:
            self._variables[name] = Symbol(SymbolKind.VARIABLE, name, _expression_type(declared_type), VariableScope(scope))
        if ENGINE_TICK not in self._variables:
            self._variables[ENGINE_TICK] = Symbol(SymbolKind.VARIABLE, ENGINE_TICK, "float", VariableScope.GLOBAL)
        self._meters = {name: Symbol(SymbolKind.METER, name, "float", None) for name in meters}
        self._items = {
            name: Symbol(SymbolKind.ITEM_STATE, name, _expression_type(item_type), None) for name, item_type in item_state.items()
        }

    @classmethod
    def of_registry(
        cls, variables: Iterable[_RegistryVariable], *, meters: Iterable[str], item_profiles: Mapping[str, _ItemProfile]
    ) -> Namespace:
        """The namespace of a compiled roster: the registry's variables (``VFSCompiler.build_runtime_variables``,
        ``tick`` included), the level's meters, and every item profile's state.

        The compiler and the environment both build a command pipeline's namespace
        through this one constructor, from the same compiled products.
        """
        return cls(
            variables=[(variable.id, variable.scope, variable.type) for variable in variables],
            meters=meters,
            item_state={variable.name: variable.type for profile in item_profiles.values() for variable in profile.variables},
        )

    # -- enumeration ------------------------------------------------------------------

    def entries(self, context: ReadContext) -> dict[str, Symbol]:
        """Every spelling ``context`` reads, canonical, with what it resolves to."""
        found: dict[str, Symbol] = {}
        for name, symbol in self._variables.items():
            if symbol.scope in context.variable_scopes:
                found[name] = symbol
        for name, engine_type in context.engine.items():
            found[name] = Symbol(SymbolKind.ENGINE, name, engine_type, None)
        for name, local_type in context.locals.items():
            found[name] = Symbol(SymbolKind.LOCAL, name, local_type, None)
        if context.meters:
            found.update({symbol.spelling: symbol for symbol in self._meters.values()})
        if context.item:
            found.update({symbol.spelling: symbol for symbol in self._items.values()})
        return found

    def schema(self, context: ReadContext) -> dict[str, str]:
        """The type checker's schema: spelling -> expression type."""
        return {spelling: symbol.type for spelling, symbol in self.entries(context).items()}

    def shapes(self, context: ReadContext, *, payload_for_vectors: bool) -> dict[str, str]:
        """The shape proof's map: spelling -> leading axes.

        ``payload_for_vectors`` labels a vector/tensor-typed read ``payload`` (refused by
        the shape proof) instead of its scope's axes: a variable expression yields
        scalars and bools only, while a write's type checker proves a vector's width.
        """
        shapes: dict[str, str] = {}
        for spelling, symbol in self.entries(context).items():
            shapes[spelling] = symbol.shape
            if payload_for_vectors and symbol.type not in {"int", "float", "bool"}:
                shapes[spelling] = "payload"
        return shapes

    def variable(self, name: str) -> Symbol | None:
        """The registry variable ``name``, whatever context reads it."""
        return self._variables.get(name)

    # -- resolution and refusal -------------------------------------------------------

    def resolve(self, path: str, context: ReadContext) -> Symbol:
        """What ``path`` names in ``context``; raises ``SpellingError`` naming the spelling to use."""
        entry = self.entries(context).get(path)
        if entry is not None:
            return entry
        raise SpellingError(self._refusal(path, context))

    def refusal(self, path: str, context: ReadContext) -> str | None:
        """Why ``context`` refuses ``path``, naming the one spelling to use; None when it reads it."""
        if path in self.entries(context):
            return None
        return self._refusal(path, context)

    def refusals(self, ast: ASTNode, context: ReadContext) -> list[str]:
        """Every refused read in ``ast``, plus a call to a function whose context ``context`` does not carry."""
        found = [message for path in sorted(read_paths(ast)) if (message := self.refusal(path, context)) is not None]
        call = unserved_requirement(ast, context.carries)
        if call is not None:
            found.append(
                f"it calls {call}, which {context.label} does not carry. "
                "Declare the quantity as a global or agent expression variable and read it by name."
            )
        return found

    def _refusal(self, path: str, context: ReadContext) -> str:
        entries = self.entries(context)
        intended = self._intended(path, context)
        if intended is not None and intended.spelling != path:
            if intended.spelling in entries:
                return f"'{path}' is not a spelling {context.label} accepts: write '{intended.spelling}'. {SPELLING_RULE}"
            return f"'{path}' is not a spelling: the {intended.kind} is '{intended.spelling}', {self._unread(intended, context)}"
        if intended is not None:
            return f"'{intended.spelling}' names the {intended.kind} '{intended.name}', {self._unread(intended, context)}"
        reference = parse_reference(path)
        if reference is None or reference.kind != ReferenceKind.NAME:
            return f"'{path}' is not a reference {context.label} can read. {SPELLING_RULE}"
        return f"'{path}' names no variable, meter or item state {context.label} can read. {SPELLING_RULE}"

    def _unread(self, symbol: Symbol, context: ReadContext) -> str:
        if symbol.kind == SymbolKind.ITEM_STATE:
            return (
                f"but {context.label} is bound to no item ('item.' names the item of an item interaction, an "
                "item-scoped effect or an inventory loop)."
            )
        if symbol.kind == SymbolKind.METER:
            return f"which {context.label} cannot read."
        assert symbol.scope is not None
        readable = ", ".join(sorted(scope.value for scope in context.variable_scopes))
        return f"declared scope '{symbol.scope.value}', which {context.label} cannot read (it reads {readable} variables)."

    def _intended(self, path: str, context: ReadContext) -> Symbol | None:
        """The symbol an old (or out-of-context) spelling means, when it names exactly one."""
        segments = path.split(".")
        qualifier = None
        if len(segments) > 1 and segments[0] in _LEGACY_ENTITY_QUALIFIERS:
            qualifier = segments.pop(0)
        if len(segments) > 1 and segments[0] == _LEGACY_STORAGE_ROOT:
            segments.pop(0)
        if len(segments) == 2 and segments[0] == METER_ROOT:
            meter = self._meters.get(segments[1])
            return meter if meter is not None else self._bare(segments[1], context, qualifier)
        if len(segments) == 2 and segments[0] == ITEM_ROOT:
            item = self._items.get(segments[1])
            return item if item is not None else self._bare(segments[1], context, qualifier)
        if len(segments) != 1:
            return None
        return self._bare(segments[0], context, qualifier)

    def _bare(self, name: str, context: ReadContext, qualifier: str | None) -> Symbol | None:
        served = self.entries(context)
        item = self._items.get(name)
        if item is not None and context.item and qualifier in {"self", "target"}:
            return item
        if name in served and served[name].kind != SymbolKind.ITEM_STATE:
            return served[name]
        candidates = [symbol for symbol in (self._variables.get(name), self._meters.get(name), item) if symbol is not None]
        in_context = [symbol for symbol in candidates if symbol.spelling in served]
        if in_context:
            return in_context[0]
        return candidates[0] if candidates else None


def _expression_type(declared_type: str) -> str:
    return "float" if declared_type == "scalar" else declared_type


@dataclass(frozen=True)
class CommandSymbols:
    """What a command-pipeline compiler resolves against: the namespace and the inlinable expressions."""

    namespace: Namespace
    expressions: Mapping[str, ExpressionSource]


# -- expression inlining (VFS round-2 S4 and the S5 follow-up) ---------------------------


@dataclass(frozen=True)
class ExpressionSource:
    """An expression variable as a consumer reads it.

    An expression variable is a name for a function of state. A consumer that reads one
    reads that function evaluated on the state the consumer sees, not the value the last
    profile evaluation stored: ``ast`` (the expression with every inlinable expression
    variable it reads substituted, recursively) is substituted into the consumer's
    expression at compile, so it needs no evaluation order.

    ``stored_because`` is None for such a context-free expression. Otherwise it names
    the function that needs evaluation-time context a consumer outside the profile
    evaluator does not carry (temporal history, the engine step, positions):
    re-evaluating a history operator would read its buffers a second time, so the
    expression is not inlined and a consumer reads the value its last profile evaluation
    stored. A ``tick``-lifetime one has no stored value by then (tick state resets
    before any consumer runs), so reading it refuses at compile.
    """

    ast: ASTNode
    lifetime: str
    stored_because: str | None


class _CompiledVariable(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def ast(self) -> ASTNode | None: ...

    @property
    def lifetime(self) -> str: ...


class _CompiledProfile(Protocol):
    @property
    def variables(self) -> Sequence[_CompiledVariable]: ...


def expression_sources(profiles: Sequence[_CompiledProfile | None]) -> dict[str, ExpressionSource]:
    """Every compiled global/agent expression variable as a consumer reads it, by id.

    ``profiles`` come in evaluation order (global, then agent), each profile's
    variables topologically sorted, so every expression variable an expression reads is
    resolved before the expression itself; cycles were refused by the profile compiler.
    """
    sources: dict[str, ExpressionSource] = {}
    for profile in profiles:
        if profile is None:
            continue
        for variable in profile.variables:
            if variable.ast is None:
                continue
            context_call = unserved_requirement(variable.ast, frozenset())
            if context_call is not None:
                sources[variable.name] = ExpressionSource(variable.ast, variable.lifetime, context_call)
                continue
            inlined = {name: source.ast for name, source in sources.items() if source.stored_because is None}
            sources[variable.name] = ExpressionSource(substitute_reads(variable.ast, inlined), variable.lifetime, None)
    return sources


def substitute_reads(node: ASTNode, replacements: Mapping[str, ASTNode]) -> ASTNode:
    """``node`` with every read (``Variable`` or ``PathAccess``) named in ``replacements`` replaced by its AST."""
    if isinstance(node, Variable) and node.name in replacements:
        return replacements[node.name]
    if isinstance(node, PathAccess) and ".".join(node.segments) in replacements:
        return replacements[".".join(node.segments)]

    def substitute(value: Any) -> Any:
        if isinstance(value, ASTNode):
            return substitute_reads(value, replacements)
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


def inline_expression_reads(ast: ASTNode, sources: Mapping[str, ExpressionSource], *, consumer: str) -> ASTNode:
    """``ast`` with every inlinable expression variable it reads substituted by its function.

    Raises ``SpellingError`` when ``ast`` reads (directly or through an inlined
    expression) a ``tick``-lifetime expression variable that cannot be inlined: tick
    state resets before ``consumer`` runs, so it would only ever read the declared literal.
    """
    replacements = {name: source.ast for name, source in sources.items() if source.stored_because is None}
    substituted = substitute_reads(ast, replacements)
    for path in sorted(read_paths(substituted)):
        source = sources.get(path)
        if source is None or source.stored_because is None or source.lifetime != "tick":
            continue
        raise SpellingError(
            f"it reads tick-lifetime expression variable '{path}', whose expression calls {source.stored_because}, so "
            f"it is not inlined and {consumer} reads its stored value. Tick-lifetime state resets before {consumer} "
            f"runs, so it would only ever see its declared literal. Declare '{path}' with lifetime episode."
        )
    return substituted
