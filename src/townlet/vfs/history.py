"""History requirements of VFS profile expressions: which keys keep a ring, and how deep.

The temporal operators (``lag``, ``delta``, ``moving_average``, ``ema``,
``rate_of_change``, ``rising_edge``, ``falling_edge``) read the past of a named value.
Their runtime contract lives in ``townlet.world.expression.history``; this module is the
compile side: it refuses a temporal call the runtime could not serve, with a
``TypeCheckError`` that stage 6 locates at the variables declaration, and derives the
ring depth every history key needs, from the global and the agent profile alike.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from townlet.world.expression.ast_nodes import (
    ASTNode,
    BinaryOp,
    Constant,
    FunctionCall,
    IfThenElse,
    IndexAccess,
    PathAccess,
    UnaryOp,
    Variable,
)
from townlet.world.expression.history import MAX_WINDOW_SIZE, TEMPORAL_FUNCTIONS, history_key
from townlet.world.expression.type_checker import TypeCheckError

if TYPE_CHECKING:
    from townlet.vfs.profiles import CompiledGlobalProfile

__all__ = ["TEMPORAL_FUNCTIONS", "collect_history_requirements", "expression_history", "same_instant_refs", "walk"]


def _children(node: ASTNode) -> tuple[ASTNode, ...]:
    if isinstance(node, BinaryOp):
        return (node.left, node.right)
    if isinstance(node, UnaryOp):
        return (node.operand,)
    if isinstance(node, FunctionCall):
        return tuple(node.arguments)
    if isinstance(node, IfThenElse):
        return (node.condition, node.true_branch, node.false_branch)
    if isinstance(node, IndexAccess):
        return (node.base, node.index)
    return ()


def walk(node: ASTNode) -> Iterator[ASTNode]:
    """Every node of a profile expression, the root first."""
    yield node
    for child in _children(node):
        yield from walk(child)


def same_instant_refs(node: ASTNode) -> set[str]:
    """The bare names an expression reads at the current instant: its dependency edges.

    A ``lag(x, n)`` read is the one exception: it reads ``x``'s ring, which the engine
    commits after every variable has evaluated, never ``x``'s in-evaluation value. So
    it is not an edge, and ``t: where(e, 0.0, lag(t, 1) + 1.0)`` is no cycle. Every other
    temporal operator also reads its argument's current value, so its read is an edge.
    """
    if isinstance(node, Variable):
        return {node.name}
    if isinstance(node, PathAccess):
        return {node.segments[0]}  # a reference variable a path dereferences (``target.bar.x``)
    if isinstance(node, FunctionCall) and node.function_name == "lag":
        return set().union(*(same_instant_refs(argument) for argument in node.arguments[1:]))
    return set().union(*(same_instant_refs(child) for child in _children(node)))


def _literal_int(call: FunctionCall, what: str, *, low: int) -> int:
    argument = call.arguments[1]
    if not isinstance(argument, Constant) or isinstance(argument.value, bool) or not isinstance(argument.value, int):
        raise TypeCheckError(f"Function '{call.function_name}' takes its {what} as an integer literal; got a computed value")
    value = int(argument.value)
    if not low <= value <= MAX_WINDOW_SIZE:
        raise TypeCheckError(f"Function '{call.function_name}' {what} must be in {low}..{MAX_WINDOW_SIZE}; got {value}")
    return value


def _ring_depth(call: FunctionCall) -> int:
    """How many committed instants back one temporal call reads (at least 1)."""
    name = call.function_name
    if name == "lag":
        return _literal_int(call, "depth n", low=1)
    if name == "rate_of_change":
        return _literal_int(call, "window", low=1)
    if name == "moving_average":
        return max(_literal_int(call, "window", low=1) - 1, 1)
    if name == "ema":
        argument = call.arguments[1]
        if not isinstance(argument, Constant) or isinstance(argument.value, bool) or not isinstance(argument.value, (int, float)):
            raise TypeCheckError("Function 'ema' takes its smoothing alpha as a numeric literal; got a computed value")
        if not 0.0 < float(argument.value) <= 1.0:
            raise TypeCheckError(f"Function 'ema' alpha must be in (0, 1]; got {argument.value}")
        return 1
    return 1  # delta, rising_edge, falling_edge read one instant back


def expression_history(node: ASTNode) -> dict[str, int]:
    """The ring depth each history key read by one expression needs; refuses what cannot be served.

    A temporal operator reads the past of a NAMED value: a variable (``vfs.<id>``, the
    clock ``vfs.tick``) or a meter (``bar.<meter>``). A computed argument has no ring to
    read, so it refuses with the fix: declare the computation as its own variable.
    """
    requirements: dict[str, int] = {}
    for found in walk(node):
        if not isinstance(found, FunctionCall) or found.function_name not in TEMPORAL_FUNCTIONS:
            continue
        if not found.arguments:
            raise TypeCheckError(f"Function '{found.function_name}' needs the named value whose history it reads")
        key = history_key(found.arguments[0])
        if key is None:
            raise TypeCheckError(
                f"Function '{found.function_name}' reads the history of a named value, but its first argument is a "
                "computed expression. Declare that expression as its own variable (a bool variable for an edge) "
                f"and apply '{found.function_name}' to the variable."
            )
        requirements[key] = max(requirements.get(key, 0), _ring_depth(found))
    return requirements


def collect_history_requirements(
    global_profile: CompiledGlobalProfile | None,
    agent_profile: CompiledGlobalProfile | None,
) -> dict[str, int]:
    """Every history key either profile reads, with the deepest ring any read needs.

    Keys are one namespace across both profiles (a variable id is unique in the
    registry; a meter or the clock read by both profiles shares one ring), and every
    key's rows are worlds, ``[N]``: a global is per world (S1) and a world holds one agent.
    """
    requirements: dict[str, int] = {}
    for profile in (global_profile, agent_profile):
        if profile is None:
            continue
        for variable in profile.variables:
            if variable.ast is None:
                continue
            for key, depth in expression_history(variable.ast).items():
                requirements[key] = max(requirements.get(key, 0), depth)
    return dict(sorted(requirements.items()))
