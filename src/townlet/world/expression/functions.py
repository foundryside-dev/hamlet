"""Shared registry for expression functions: signature, documentation and evaluation.

Every function the expression language can call is one ``FunctionSpec`` registered in
``FUNCTION_SPECS``. The type checker reads ``validate_args`` / ``return_type``; the
evaluator reads ``eval_fn``; ``scripts/gen_expression_functions_doc.py`` renders the
``signature`` / ``summary`` / ``returns`` / ``family`` / ``requires`` columns into
``docs/config-schemas/expressions.md``. Because the three consumers share one record,
the declared return type, the evaluated dtype and the documented table cannot drift
apart independently; ``tests/test_townlet/unit/world/expression/
test_function_registry_agreement.py`` holds the first two to each other.

Shape contract: a scalar-typed result (``int``, ``float``, ``bool``) carries the batch
axis of its per-agent inputs, ``[batch]``; a vector-typed result (``vec2f``, ``vec3f``,
``vecNf``) carries it in front of the vector axis, ``[batch, D]``. No function collapses
or indexes the batch axis: the batch is independent worlds (S1), so ``gather`` and
``scatter`` index a vector's element axis, never another row. A literal has no batch axis, so a result built only from literals is
unbatched: ``one_hot(2, 3)`` is ``[3]``, ``one_hot(bar.slot, 3)`` is ``[batch, 3]``.

Vector widths: ``vec2*`` and ``vec3*`` carry their width in the type, so a pair of
mismatched widths is refused at type check; ``vecN*`` and ``tensor2d`` do not, so their
widths are checked when the function runs and a mismatch raises a ``ValueError`` naming
the function.

Row shape: every spec declares ``shape``, the rule the VFS shape proof
(``townlet.vfs.profiles.VFSProfileCompiler``) derives a call's leading registry axes by,
and ``requires``, the context a call needs (history, positions, a random stream). A
consumer admits a call by ``requires`` alone (``unserved_requirement``), and proves its
axes by ``shape`` alone; there is no hand-kept list of admitted functions anywhere.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import torch

if TYPE_CHECKING:  # pragma: no cover
    from townlet.world.expression.ast_nodes import ASTNode
    from townlet.world.expression.context import ExecutionContext
    from townlet.world.expression.history import TemporalHistory

Numeric = frozenset({"int", "float"})
VectorTypes = frozenset({"vec2i", "vec3i", "vec2f", "vec3f", "vecNi", "vecNf"})

FAMILY_MATH = "Math"
FAMILY_STATISTICS = "Statistics"
FAMILY_LOGIC = "Logic and masks"
FAMILY_SAMPLING = "Sampling"
FAMILY_TEMPORAL = "Temporal"
FAMILY_SPATIAL = "Spatial"
FAMILY_AFFORDANCE = "Affordance"
FAMILY_ORDER: tuple[str, ...] = (
    FAMILY_MATH,
    FAMILY_STATISTICS,
    FAMILY_LOGIC,
    FAMILY_SAMPLING,
    FAMILY_TEMPORAL,
    FAMILY_SPATIAL,
    FAMILY_AFFORDANCE,
)

REQUIRES_HISTORY = "temporal history on the context"
REQUIRES_POSITIONS = "agent and affordance positions on the context"
REQUIRES_RANDOM = "a random stream on the context"

SHAPE_POINTWISE = "pointwise"
"""The result has the join of its arguments' leading axes: a literal joins with anything,
a per-agent argument makes the result per agent, and two distinct axes refuse. Every
function that computes from its arguments alone, history operators included (their
other arguments are literals)."""
SHAPE_AGENT_ROWS = "agent rows"
"""One row per agent whatever the arguments: the functions that read the agent positions
the context carries. In a global expression (no agent axis) such a call refuses."""
SHAPE_DRAW = "draw"
"""One independent draw per row: the join of the arguments' axes with the row axis of the
context the call runs in (per world in a global expression or on a global target, per
agent in an agent expression, an action write or on an agent target), so a literal-only
call still draws once per row, never once for the whole batch."""
SHAPES = frozenset({SHAPE_POINTWISE, SHAPE_AGENT_ROWS, SHAPE_DRAW})


@dataclass(frozen=True)
class FunctionSpec:
    """One expression function: its documented contract and its two implementations."""

    name: str
    signature: str
    summary: str
    returns: str
    family: str
    requires: tuple[str, ...]
    shape: str
    min_args: int
    max_args: int | None
    return_type: Callable[[list[str]], str]
    validate_args: Callable[[list[str]], None]
    eval_fn: Callable[[list[Any], ExecutionContext, list[ASTNode]], torch.Tensor | Any]


# --- Argument validation -----------------------------------------------------------


def _ensure_arg_count(name: str, args: list[str], min_args: int, max_args: int | None) -> None:
    if len(args) < min_args:
        raise ValueError(f"Function '{name}' expects at least {min_args} args, got {len(args)}")
    if max_args is not None and len(args) > max_args:
        raise ValueError(f"Function '{name}' expects at most {max_args} args, got {len(args)}")


def _ensure_all_numeric(name: str, args: list[str]) -> None:
    if not all(arg in Numeric for arg in args):
        raise ValueError(f"Function '{name}' requires numeric args, got {args}")


def _ensure_all_bool(name: str, args: list[str]) -> None:
    if not all(arg == "bool" for arg in args):
        raise ValueError(f"Function '{name}' requires bool args, got {args}")


def _ensure_string_arg(name: str, arg: str, position: int) -> None:
    if arg != "str":
        raise ValueError(f"Function '{name}' argument {position} must be a string literal, got {arg}")


def _ensure_int(name: str, arg: str) -> None:
    if arg != "int":
        raise ValueError(f"Function '{name}' requires integer argument, got {arg}")


def _ensure_bool_arg(name: str, arg: str, position: int) -> None:
    if arg != "bool":
        raise ValueError(f"Function '{name}' argument {position} must be bool, got {arg}")


def _ensure_vector_arg(name: str, arg: str, position: int) -> None:
    if arg in VectorTypes:
        return
    if arg in Numeric:
        raise ValueError(
            f"Function '{name}' argument {position} must be a vector variable (vec2i, vec3i, vec2f, vec3f, vecNi, vecNf), "
            f"got scalar {arg}. The distance between two scalars is abs(a - b)."
        )
    raise ValueError(f"Function '{name}' argument {position} must be a vector variable, got {arg}")


ElementVectorTypes = VectorTypes | {"tensor1d"}
"""Value types with exactly one element axis inside each world's row: what `gather` and
`scatter` index. A scalar type's only axis is the batch, and the batch is independent
worlds (S1), so indexing it would read or write another world's row."""


def _ensure_element_vector_arg(name: str, arg: str, position: int) -> None:
    if arg in ElementVectorTypes:
        return
    raise ValueError(
        f"Function '{name}' argument {position} must be a vector (vec2i, vec3i, vec2f, vec3f, vecNi, vecNf) or tensor1d, "
        f"got {arg}: it indexes the element axis inside one world's value. A {arg} value has no element axis, and its "
        "only row axis is the batch of independent worlds, so an index there would reach another world."
    )


def _element_type(vector_type: str) -> str:
    """The element type of an element-vector type: int for the integer vectors, float otherwise."""
    return "int" if vector_type in {"vec2i", "vec3i", "vecNi"} else "float"


def _ensure_element_update(name: str, base: str, update: str) -> None:
    """A scatter update is one element of `base`: an int into an integer vector, any number into a float one."""
    if update not in Numeric or (_element_type(base) == "int" and update != "int"):
        raise ValueError(f"Function '{name}' writes one {_element_type(base)} element of {base}, got {update}")


def _ensure_candidates_arg(name: str, arg: str, position: int) -> None:
    """Candidates are a tensor2d of rows, held per world.

    A vector variable's only row axis is the batch, and the batch is independent worlds
    (S1): its rows as candidates would let one world pick another world's row. So a
    vector variable is refused; a tensor2d's candidate rows sit inside each world's row.
    """
    if arg == "tensor2d":
        return
    raise ValueError(
        f"Function '{name}' argument {position} must be a tensor2d of candidate rows, got {arg}: a vector variable's rows "
        "are the batch's independent worlds, never one world's candidates"
    )


def _static_vector_width(arg: str) -> int | None:
    """The vector width the type name carries: 2 or 3, or None for vecN* and tensor2d."""
    if arg in {"vec2i", "vec2f"}:
        return 2
    if arg in {"vec3i", "vec3f"}:
        return 3
    return None


def _ensure_same_vector_width(name: str, left: str, right: str) -> None:
    """Refuse two vector arguments whose statically known widths differ."""
    left_width = _static_vector_width(left)
    right_width = _static_vector_width(right)
    if left_width is not None and right_width is not None and left_width != right_width:
        raise ValueError(
            f"Function '{name}' requires vectors of one width, got {left} (width {left_width}) and {right} (width {right_width})"
        )


REFERENCE_TYPES = frozenset({"agent_ref", "item_ref"})
"""Batch-row reference types: a row of this world, or the null row -1 (an int)."""


def branch_type(left: str, right: str) -> str | None:
    """The type two selected branches unify to, or None when they do not.

    Equal types unify to themselves, numerics promote, and a reference unifies with an
    int (its null, ``-1``) to the reference: ``where(c, ref, -1)``. Whether the int is
    the null is the write's world-locality proof to make, not the type checker's.
    """
    if left == right:
        return left
    if left in Numeric and right in Numeric:
        return "float" if "float" in {left, right} else "int"
    if left in REFERENCE_TYPES and right == "int":
        return left
    if right in REFERENCE_TYPES and left == "int":
        return right
    return None


def _ensure_branches(name: str, left: str, right: str) -> None:
    if branch_type(left, right) is None:
        raise ValueError(
            f"Function '{name}' requires matching branch types, numeric promotion, or a reference and its int null; got {left} and {right}"
        )


def _ensure_matching_or_numeric(name: str, left: str, right: str) -> None:
    if left == right:
        return
    if left in Numeric and right in Numeric:
        return
    raise ValueError(f"Function '{name}' requires matching value types or numeric promotion, got {left} and {right}")


def _ensure_optional_string_arg(name: str, args: list[str], index: int) -> None:
    if len(args) > index and args[index] != "str":
        raise ValueError(f"Function '{name}' argument {index + 1} must be a string metric literal, got {args[index]}")


def _run_validators(*validators: Callable[[], None]) -> None:
    """Execute multiple validator functions in sequence and return None."""
    for validator in validators:
        validator()


# --- Return types --------------------------------------------------------------------


def _return_numeric(args: list[str]) -> str:
    return "float" if "float" in args else "int"


def _return_bool(_: list[str]) -> str:
    return "bool"


def _return_float(_: list[str]) -> str:
    return "float"


def _return_int(_: list[str]) -> str:
    return "int"


def _return_first(args: list[str]) -> str:
    return args[0]


def _return_element(args: list[str]) -> str:
    return _element_type(args[0])


def _return_vecnf(_: list[str]) -> str:
    return "vecNf"


def _return_where(args: list[str]) -> str:
    unified = branch_type(args[1], args[2])
    if unified is None:
        return args[1]
    return unified


def _return_masked_numeric(args: list[str]) -> str:
    left, right = args[0], args[1]
    if left in Numeric and right in Numeric:
        return "float" if "float" in {left, right} else "int"
    return left


def _return_float_vector(args: list[str]) -> str:
    """The float vector type of the same width as the (vector) first argument."""
    arg = args[0]
    if arg in {"vec2i", "vec2f"}:
        return "vec2f"
    if arg in {"vec3i", "vec3f"}:
        return "vec3f"
    return "vecNf"


# --- Shared evaluation helpers -------------------------------------------------------


def _stack_args(args: list[torch.Tensor]) -> torch.Tensor:
    """Stack the arguments on a new leading axis, broadcasting scalars against per-agent inputs."""
    return torch.stack(torch.broadcast_tensors(*args), dim=0)


def _stack_float(args: list[torch.Tensor]) -> torch.Tensor:
    return _stack_args(args).to(dtype=torch.float32)


def _promote_pair(left: torch.Tensor, right: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Cast both tensors to their common promoted dtype on ``left``'s device."""
    dtype = torch.promote_types(left.dtype, right.dtype)
    return left.to(dtype=dtype), right.to(device=left.device, dtype=dtype)


def _check_vector_widths(name: str, left: torch.Tensor, right: torch.Tensor) -> None:
    if left.shape[-1] != right.shape[-1]:
        raise ValueError(f"Function '{name}' requires vectors of one width, got widths {left.shape[-1]} and {right.shape[-1]}")


def _broadcast_bool_mask(mask: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    broadcast = mask.to(device=target.device, dtype=torch.bool)
    while broadcast.dim() < target.dim():
        broadcast = broadcast.unsqueeze(-1)
    return broadcast


def _scalar_int(arg: torch.Tensor, name: str) -> int:
    if arg.numel() != 1:
        raise ValueError(f"Function '{name}' expects a scalar integer argument")
    return int(arg.item())


def _scalar_float(arg: torch.Tensor, name: str) -> float:
    if arg.numel() != 1:
        raise ValueError(f"Function '{name}' expects a scalar float argument")
    return float(arg.item())


def _history_key(name: str, arg_nodes: list[ASTNode]) -> str:
    from townlet.world.expression.history import history_key

    if not arg_nodes:
        raise ValueError(f"Function '{name}' needs the named value whose history it reads")
    key = history_key(arg_nodes[0])
    if key is None:
        raise ValueError(f"Function '{name}' reads the history of a named value: its first argument must be a variable or path")
    return key


def _get_history(context: ExecutionContext) -> TemporalHistory:
    if context.history is None:
        raise RuntimeError("Temporal operators require a TemporalHistory on the execution context")
    return context.history


def _require_positions(context: ExecutionContext) -> torch.Tensor:
    if context.agent_positions is None:
        raise RuntimeError("Spatial operators require agent_positions on the execution context")
    return context.agent_positions


def _affordance_position(context: ExecutionContext, name: str) -> torch.Tensor | None:
    positions = context.affordance_positions or {}
    return positions.get(name)


def _string_arg(value: Any) -> str:
    return value if isinstance(value, str) else str(value)


def _metric_from_args(name: str, args: list[Any], fallback: str) -> str:
    if len(args) < 1:
        return fallback
    metric = args[0]
    if not isinstance(metric, str):
        raise ValueError(f"Function '{name}' metric must be a string literal")
    metric_l = metric.lower()
    if metric_l not in {"manhattan", "euclidean"}:
        raise ValueError(f"Function '{name}' metric must be 'manhattan' or 'euclidean', got '{metric}'")
    return metric_l


def _reduce_vector(diff: torch.Tensor, metric: str) -> torch.Tensor:
    """Collapse the trailing vector axis of a float difference under ``metric``."""
    if metric == "manhattan":
        return diff.abs().sum(dim=-1)
    return diff.pow(2).sum(dim=-1).sqrt()


def _as_float_vector(value: torch.Tensor, device: torch.device) -> torch.Tensor:
    return value.to(device=device, dtype=torch.float32)


def _distance_between(name: str, left: torch.Tensor, right: torch.Tensor, metric: str) -> torch.Tensor:
    """Distance between two vectors, reduced over the vector axis only: ``[batch, D] -> [batch]``.

    Both operands are measured in float32 so an int vector against a float vector is the
    true distance, the same in either argument order.
    """
    _check_vector_widths(name, left, right)
    diff = _as_float_vector(left, left.device) - _as_float_vector(right, left.device)
    return _reduce_vector(diff, metric)


def _distance_to_target(agent_positions: torch.Tensor, target: torch.Tensor, metric: str) -> torch.Tensor:
    diff = _as_float_vector(agent_positions, agent_positions.device) - _as_float_vector(target, agent_positions.device)
    return _reduce_vector(diff, metric)


# --- Perlin noise ---------------------------------------------------------------------


def _fade(t: torch.Tensor) -> torch.Tensor:
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a: torch.Tensor, b: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
    return a + t * (b - a)


def _gradient(hash_tensor: torch.Tensor, xf: torch.Tensor, yf: torch.Tensor) -> torch.Tensor:
    gradients = torch.tensor([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]], device=hash_tensor.device)
    g = gradients[hash_tensor % 4]
    return g[..., 0] * xf + g[..., 1] * yf


def _perlin_2d(x: torch.Tensor, y: torch.Tensor, seed: int) -> torch.Tensor:
    x = x.to(dtype=torch.float32)
    y = y.to(dtype=torch.float32)
    x, y = torch.broadcast_tensors(x, y)

    xi = torch.floor(x).to(dtype=torch.int64)
    yi = torch.floor(y).to(dtype=torch.int64)
    xf = x - xi.to(dtype=torch.float32)
    yf = y - yi.to(dtype=torch.float32)

    def _hash(ix: torch.Tensor, iy: torch.Tensor) -> torch.Tensor:
        return (ix * 374761393 + iy * 668265263 + seed * 1446648777) & 0xFFFFFFFF

    aa = _hash(xi, yi)
    ab = _hash(xi, yi + 1)
    ba = _hash(xi + 1, yi)
    bb = _hash(xi + 1, yi + 1)

    x1 = _gradient(aa, xf, yf)
    x2 = _gradient(ba, xf - 1, yf)
    y1 = _lerp(x1, x2, _fade(xf))

    x3 = _gradient(ab, xf, yf - 1)
    x4 = _gradient(bb, xf - 1, yf - 1)
    y2 = _lerp(x3, x4, _fade(xf))

    return _lerp(y1, y2, _fade(yf))


def _eval_perlin(name: str, args: list[Any]) -> torch.Tensor:
    x = cast(torch.Tensor, args[0])
    y = cast(torch.Tensor, args[1]) if len(args) > 1 else torch.zeros_like(x)
    seed = _scalar_int(args[2], name) if len(args) > 2 else 0
    return _perlin_2d(x, y, seed)


# --- Evaluation functions -------------------------------------------------------------


def _eval_max(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.max(cast(torch.Tensor, args[0]), cast(torch.Tensor, args[1]))


def _eval_min(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.min(cast(torch.Tensor, args[0]), cast(torch.Tensor, args[1]))


def _eval_abs(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.abs(args[0])


def _eval_clamp(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.clamp(args[0], min=args[1], max=args[2])


def _eval_clamp01(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.clamp(cast(torch.Tensor, args[0]).to(dtype=torch.float32), min=0.0, max=1.0)


def _eval_sigmoid(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.sigmoid(cast(torch.Tensor, args[0]).to(dtype=torch.float32))


def _eval_tanh(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.tanh(cast(torch.Tensor, args[0]).to(dtype=torch.float32))


def _eval_smoothstep(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    edge0, edge1, x = (cast(torch.Tensor, arg).to(dtype=torch.float32) for arg in args)
    t = torch.clamp((x - edge0) / (edge1 - edge0 + 1e-8), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _eval_mean(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.mean(_stack_float(args), dim=0)


def _eval_variance(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.var(_stack_float(args), dim=0, unbiased=False)


def _eval_sum(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.sum(_stack_float(args), dim=0)


def _eval_product(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.prod(_stack_float(args), dim=0)


def _eval_min_all(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.min(_stack_args(args), dim=0).values


def _eval_max_all(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.max(_stack_args(args), dim=0).values


def _eval_count_where(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.sum(_stack_args(args).to(dtype=torch.int64), dim=0)


def _eval_argmin(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.argmin(_stack_args(args), dim=0)


def _eval_argmax(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.argmax(_stack_args(args), dim=0)


def _eval_threshold(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    value, low, high = args
    return torch.where(value >= high, torch.ones_like(value, dtype=torch.bool), value > low)


def _eval_all(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.all(_stack_args(args).bool(), dim=0)


def _eval_any(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.any(_stack_args(args).bool(), dim=0)


def _eval_where(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    condition, if_true, if_false = args
    return torch.where(_broadcast_bool_mask(condition, if_true), if_true, if_false)


def _eval_masked_add(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    value, delta, mask = _promote_pair(args[0], args[1]) + (args[2],)
    return torch.where(_broadcast_bool_mask(mask, value), value + delta, value)


def _eval_masked_set(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    value, replacement, mask = _promote_pair(args[0], args[1]) + (args[2],)
    return torch.where(_broadcast_bool_mask(mask, value), replacement, value)


def _element_broadcast(values: torch.Tensor, indices: torch.Tensor, name: str) -> tuple[torch.Tensor, torch.Tensor]:
    """`values` ``[..., D]`` and integer `indices` ``[...]`` broadcast to one leading shape.

    The index addresses the element axis (the last) inside each row; it never addresses
    the batch axis, so every row reads and writes its own world's value (S1).
    """
    width = int(values.shape[-1])
    indices = indices.to(device=values.device, dtype=torch.long)
    if bool(((indices < 0) | (indices >= width)).any()):
        raise ValueError(f"Function '{name}' index is outside the element axis [0, {width})")
    leading = torch.broadcast_shapes(values.shape[:-1], indices.shape)
    return values.expand(*leading, width), indices.expand(leading)


def _eval_gather(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    values, indices = _element_broadcast(cast(torch.Tensor, args[0]), cast(torch.Tensor, args[1]), "gather")
    return torch.gather(values, -1, indices.unsqueeze(-1)).squeeze(-1)


def _eval_scatter(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    base = cast(torch.Tensor, args[0])
    update = cast(torch.Tensor, args[2]).to(device=base.device, dtype=base.dtype)
    leading = torch.broadcast_shapes(base.shape[:-1], cast(torch.Tensor, args[1]).shape, update.shape)
    values, indices = _element_broadcast(base.expand(*leading, base.shape[-1]), cast(torch.Tensor, args[1]), "scatter")
    mask = torch.nn.functional.one_hot(indices, num_classes=int(values.shape[-1])).bool()
    return torch.where(mask, update.expand(leading).unsqueeze(-1), values)


def _eval_one_hot(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    indices, class_count = args
    classes = _scalar_int(class_count, "one_hot")
    if classes < 2:
        raise ValueError("Function 'one_hot' requires at least 2 classes")
    return torch.nn.functional.one_hot(indices.to(dtype=torch.long), num_classes=classes).to(device=indices.device, dtype=torch.float32)


def _eval_normalize(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    vector = cast(torch.Tensor, args[0]).to(dtype=torch.float32)
    norm = torch.clamp(vector.pow(2).sum(dim=-1, keepdim=True).sqrt(), min=1e-8)
    return vector / norm


def _draw(name: str, sampler: Callable[..., torch.Tensor], like: torch.Tensor, context: ExecutionContext) -> torch.Tensor:
    """One independent draw per row, shaped like ``like`` (``SHAPE_DRAW``).

    A VFS context (a profile expression, an action write, a transition rule) carries one
    generator per world, ``context.world_rngs``: world ``w``'s draws come from its own
    stream only, so they depend neither on the batch size nor on any other world (S1),
    and a literal argument still draws once per row. A command pipeline is bound to one
    world and carries that world's generator as ``context.rng``; a context bound to no
    world carries neither and draws from torch's global stream, which only direct engine
    or test callers build.
    """
    if context.world_rngs is not None:
        rows = len(context.world_rngs)
        if like.dim() == 0:
            tail: tuple[int, ...] = ()
        elif int(like.shape[0]) == rows:
            tail = tuple(like.shape[1:])
        else:
            raise RuntimeError(
                f"Engine defect: function '{name}' draws one value per world ({rows} worlds) but its argument has "
                f"shape {tuple(like.shape)}; the compiled shape proof admits no such argument"
            )
        return torch.stack([sampler(tail, device=like.device, generator=generator) for generator in context.world_rngs])
    return sampler(like.shape, device=like.device, generator=context.rng)


def _eval_normal_dist(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    if not args:
        return _draw("normal_dist", torch.randn, torch.zeros((), device=context.device), context)
    mean = cast(torch.Tensor, args[0]).to(dtype=torch.float32)
    std = cast(torch.Tensor, args[1]).to(device=mean.device, dtype=torch.float32) if len(args) > 1 else 1.0
    return _draw("normal_dist", torch.randn, mean, context) * std + mean


def _eval_uniform(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    if not args:
        return _draw("uniform", torch.rand, torch.zeros((), device=context.device), context)
    low = cast(torch.Tensor, args[0]).to(dtype=torch.float32)
    if len(args) == 1:
        return _draw("uniform", torch.rand, low, context)
    high = cast(torch.Tensor, args[1]).to(device=low.device, dtype=torch.float32)
    return _draw("uniform", torch.rand, low, context) * (high - low) + low


def _eval_perlin_noise(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return _eval_perlin("perlin_noise", args)


def _eval_simplex_noise(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return _eval_perlin("simplex_noise", args)


def _eval_time_in_window(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    time_value = args[0]
    period = torch.tensor(24.0, device=time_value.device, dtype=time_value.dtype)
    hour = torch.remainder(time_value, period)
    start_raw = args[1].to(device=time_value.device, dtype=time_value.dtype)
    end_raw = args[2].to(device=time_value.device, dtype=time_value.dtype)
    start = torch.remainder(start_raw, period)
    end = torch.remainder(end_raw, period)

    always_open = torch.remainder(end_raw - start_raw, period) == 0
    non_wrapping = start < end
    inside_non_wrapping = (hour >= start) & (hour < end)
    inside_wrapping = (hour >= start) | (hour < end)
    return torch.where(
        always_open, torch.ones_like(inside_non_wrapping, dtype=torch.bool), torch.where(non_wrapping, inside_non_wrapping, inside_wrapping)
    )


def _phase_radians(value: torch.Tensor, period: torch.Tensor, name: str) -> torch.Tensor:
    period = period.to(device=value.device, dtype=torch.float32)
    if (period <= 0).any():
        raise ValueError(f"Function '{name}' period must be > 0")
    return value.to(dtype=torch.float32) * (2.0 * math.pi) / period


def _eval_phase_sin(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.sin(_phase_radians(args[0], args[1], "phase_sin"))


def _eval_phase_cos(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return torch.cos(_phase_radians(args[0], args[1], "phase_cos"))


def _eval_lag(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return _get_history(context).lag(_history_key("lag", arg_nodes), _scalar_int(args[1], "lag"))


def _eval_delta(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    current = cast(torch.Tensor, args[0])
    return current - _get_history(context).lag(_history_key("delta", arg_nodes), 1).to(current.dtype)


def _eval_moving_average(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    current = cast(torch.Tensor, args[0]).to(dtype=torch.float32)
    key = _history_key("moving_average", arg_nodes)
    window = _scalar_int(args[1], "moving_average")
    history = _get_history(context)
    total = current
    for offset in range(1, window):
        total = total + history.lag(key, offset).to(torch.float32)
    return total / float(window)


def _eval_ema(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return _get_history(context).ema(_history_key("ema", arg_nodes), _scalar_float(args[1], "ema"), cast(torch.Tensor, args[0]))


def _eval_rate_of_change(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    window = _scalar_int(args[1], "rate_of_change")
    lagged = _get_history(context).lag(_history_key("rate_of_change", arg_nodes), window)
    return (cast(torch.Tensor, args[0]).to(torch.float32) - lagged.to(torch.float32)) / float(window)


def _eval_rising_edge(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    previous = _get_history(context).lag(_history_key("rising_edge", arg_nodes), 1).to(torch.bool)
    return torch.logical_and(cast(torch.Tensor, args[0]), torch.logical_not(previous))


def _eval_falling_edge(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    previous = _get_history(context).lag(_history_key("falling_edge", arg_nodes), 1).to(torch.bool)
    return torch.logical_and(torch.logical_not(cast(torch.Tensor, args[0])), previous)


def _eval_distance(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return _distance_between("distance", args[0], args[1], _metric_from_args("distance", args[2:], "euclidean"))


def _eval_manhattan_distance(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    return _distance_between("manhattan_distance", args[0], args[1], "manhattan")


def _eval_within_radius(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    distance = _distance_between("within_radius", args[0], args[1], _metric_from_args("within_radius", args[3:], "euclidean"))
    radius = cast(torch.Tensor, args[2]).to(device=distance.device, dtype=distance.dtype)
    return distance <= radius


def _eval_nearest(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    points = cast(torch.Tensor, args[0])
    candidates = _as_float_vector(cast(torch.Tensor, args[1]), points.device)
    # Candidates are [..., K, D] with the point's leading (per-world) axes: each point
    # chooses among its own world's rows only.
    if candidates.dim() != points.dim() + 1 or candidates.shape[: points.dim() - 1] != points.shape[:-1]:
        raise ValueError(
            f"Function 'nearest' needs candidates shaped [..., K, D] with the point's leading axes "
            f"{tuple(points.shape[:-1])}, got {tuple(candidates.shape)}: candidates are per world, never the batch's rows"
        )
    _check_vector_widths("nearest", points, candidates)
    diff = _as_float_vector(points, points.device).unsqueeze(-2) - candidates
    distances = _reduce_vector(diff, _metric_from_args("nearest", args[2:], "euclidean"))
    return torch.argmin(distances, dim=-1)


def _eval_distance_to_affordance(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    agent_positions = _require_positions(context)
    target = _affordance_position(context, _string_arg(args[0]))
    metric = _metric_from_args("distance_to_affordance", args[1:], "manhattan")
    if target is None:
        return torch.full((agent_positions.shape[0],), float("inf"), device=agent_positions.device)
    return _distance_to_target(agent_positions, target, metric)


def _eval_in_range(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    agent_positions = _require_positions(context)
    target = _affordance_position(context, _string_arg(args[0]))
    radius = _scalar_float(args[1], "in_range")
    if radius < 0:
        raise ValueError("in_range radius must be >= 0")
    metric = _metric_from_args("in_range", args[2:], "manhattan")
    if target is None:
        distance = torch.full((agent_positions.shape[0],), float("inf"), device=agent_positions.device)
    else:
        distance = _distance_to_target(agent_positions, target, metric)
    return distance <= radius


def _eval_direction_to_affordance(args: list[Any], context: ExecutionContext, arg_nodes: list[ASTNode]) -> torch.Tensor:
    agent_positions = _require_positions(context)
    target = _affordance_position(context, _string_arg(args[0]))
    metric = _metric_from_args("direction_to_affordance", args[1:], "manhattan")
    if target is None:
        return torch.zeros_like(agent_positions, dtype=torch.float32)
    vector = _as_float_vector(target, agent_positions.device).unsqueeze(0) - _as_float_vector(agent_positions, agent_positions.device)
    norm = _distance_to_target(agent_positions, target, metric).unsqueeze(-1)
    return torch.where(norm > 0, vector / norm, torch.zeros_like(vector))


# --- Registry -----------------------------------------------------------------------------

FUNCTION_SPECS: dict[str, FunctionSpec] = {}


def _register(spec: FunctionSpec) -> None:
    if spec.name in FUNCTION_SPECS:
        raise ValueError(f"Expression function '{spec.name}' registered twice")
    if spec.family not in FAMILY_ORDER:
        raise ValueError(f"Expression function '{spec.name}' names unknown family {spec.family!r}")
    if spec.shape not in SHAPES:
        raise ValueError(f"Expression function '{spec.name}' names unknown shape rule {spec.shape!r}")
    FUNCTION_SPECS[spec.name] = spec


def _numeric_spec(
    name: str,
    *,
    signature: str,
    summary: str,
    returns: str,
    family: str,
    arity: int,
    return_type: Callable[[list[str]], str],
    eval_fn: Callable[[list[Any], ExecutionContext, list[ASTNode]], torch.Tensor | Any],
) -> FunctionSpec:
    """A fixed-arity function over numeric scalars."""
    return FunctionSpec(
        name=name,
        signature=signature,
        summary=summary,
        returns=returns,
        family=family,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=arity,
        max_args=arity,
        return_type=return_type,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count(name, args, arity, arity), lambda: _ensure_all_numeric(name, args)
        ),
        eval_fn=eval_fn,
    )


def _variadic_spec(
    name: str,
    *,
    signature: str,
    summary: str,
    returns: str,
    family: str,
    return_type: Callable[[list[str]], str],
    element_check: Callable[[str, list[str]], None],
    eval_fn: Callable[[list[Any], ExecutionContext, list[ASTNode]], torch.Tensor | Any],
) -> FunctionSpec:
    """A function over one or more arguments of one type family, reduced across the arguments."""
    return FunctionSpec(
        name=name,
        signature=signature,
        summary=summary,
        returns=returns,
        family=family,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=1,
        max_args=None,
        return_type=return_type,
        validate_args=lambda args: _run_validators(lambda: _ensure_arg_count(name, args, 1, None), lambda: element_check(name, args)),
        eval_fn=eval_fn,
    )


NUMERIC_RETURNS = "int when every argument is int, else float"

# --- Math ---
_register(
    _numeric_spec(
        "max",
        signature="max(a, b)",
        summary="Element-wise maximum of two numbers.",
        returns=NUMERIC_RETURNS,
        family=FAMILY_MATH,
        arity=2,
        return_type=_return_numeric,
        eval_fn=_eval_max,
    )
)
_register(
    _numeric_spec(
        "min",
        signature="min(a, b)",
        summary="Element-wise minimum of two numbers.",
        returns=NUMERIC_RETURNS,
        family=FAMILY_MATH,
        arity=2,
        return_type=_return_numeric,
        eval_fn=_eval_min,
    )
)
_register(
    _numeric_spec(
        "abs",
        signature="abs(x)",
        summary="Absolute value.",
        returns=NUMERIC_RETURNS,
        family=FAMILY_MATH,
        arity=1,
        return_type=_return_numeric,
        eval_fn=_eval_abs,
    )
)
_register(
    _numeric_spec(
        "clamp",
        signature="clamp(x, low, high)",
        summary="Clamp `x` into `[low, high]`.",
        returns=NUMERIC_RETURNS,
        family=FAMILY_MATH,
        arity=3,
        return_type=_return_numeric,
        eval_fn=_eval_clamp,
    )
)
_register(
    _numeric_spec(
        "clamp01",
        signature="clamp01(x)",
        summary="Clamp `x` into `[0.0, 1.0]`.",
        returns="float",
        family=FAMILY_MATH,
        arity=1,
        return_type=_return_float,
        eval_fn=_eval_clamp01,
    )
)
_register(
    _numeric_spec(
        "sigmoid",
        signature="sigmoid(x)",
        summary="Logistic sigmoid `1 / (1 + exp(-x))`.",
        returns="float",
        family=FAMILY_MATH,
        arity=1,
        return_type=_return_float,
        eval_fn=_eval_sigmoid,
    )
)
_register(
    _numeric_spec(
        "tanh",
        signature="tanh(x)",
        summary="Hyperbolic tangent.",
        returns="float",
        family=FAMILY_MATH,
        arity=1,
        return_type=_return_float,
        eval_fn=_eval_tanh,
    )
)
_register(
    _numeric_spec(
        "smoothstep",
        signature="smoothstep(edge0, edge1, x)",
        summary="Hermite interpolation of `x` from 0 at `edge0` to 1 at `edge1`.",
        returns="float",
        family=FAMILY_MATH,
        arity=3,
        return_type=_return_float,
        eval_fn=_eval_smoothstep,
    )
)
_register(
    _numeric_spec(
        "threshold",
        signature="threshold(x, low, high)",
        summary="`x > low`, forced true once `x >= high` (a two-level trigger).",
        returns="bool",
        family=FAMILY_MATH,
        arity=3,
        return_type=_return_bool,
        eval_fn=_eval_threshold,
    )
)

# --- Statistics (reduced across the arguments, never across agents) ---
_register(
    _variadic_spec(
        "mean",
        signature="mean(a, b, ...)",
        summary="Arithmetic mean of the arguments.",
        returns="float",
        family=FAMILY_STATISTICS,
        return_type=_return_float,
        element_check=_ensure_all_numeric,
        eval_fn=_eval_mean,
    )
)
_register(
    _variadic_spec(
        "variance",
        signature="variance(a, b, ...)",
        summary="Population variance of the arguments.",
        returns="float",
        family=FAMILY_STATISTICS,
        return_type=_return_float,
        element_check=_ensure_all_numeric,
        eval_fn=_eval_variance,
    )
)
_register(
    _variadic_spec(
        "sum",
        signature="sum(a, b, ...)",
        summary="Sum of the arguments.",
        returns="float",
        family=FAMILY_STATISTICS,
        return_type=_return_float,
        element_check=_ensure_all_numeric,
        eval_fn=_eval_sum,
    )
)
_register(
    _variadic_spec(
        "product",
        signature="product(a, b, ...)",
        summary="Product of the arguments.",
        returns="float",
        family=FAMILY_STATISTICS,
        return_type=_return_float,
        element_check=_ensure_all_numeric,
        eval_fn=_eval_product,
    )
)
_register(
    _variadic_spec(
        "min_all",
        signature="min_all(a, b, ...)",
        summary="Smallest of the arguments.",
        returns=NUMERIC_RETURNS,
        family=FAMILY_STATISTICS,
        return_type=_return_numeric,
        element_check=_ensure_all_numeric,
        eval_fn=_eval_min_all,
    )
)
_register(
    _variadic_spec(
        "max_all",
        signature="max_all(a, b, ...)",
        summary="Largest of the arguments.",
        returns=NUMERIC_RETURNS,
        family=FAMILY_STATISTICS,
        return_type=_return_numeric,
        element_check=_ensure_all_numeric,
        eval_fn=_eval_max_all,
    )
)
_register(
    _variadic_spec(
        "argmin",
        signature="argmin(a, b, ...)",
        summary="Zero-based position of the smallest argument.",
        returns="int",
        family=FAMILY_STATISTICS,
        return_type=_return_int,
        element_check=_ensure_all_numeric,
        eval_fn=_eval_argmin,
    )
)
_register(
    _variadic_spec(
        "argmax",
        signature="argmax(a, b, ...)",
        summary="Zero-based position of the largest argument.",
        returns="int",
        family=FAMILY_STATISTICS,
        return_type=_return_int,
        element_check=_ensure_all_numeric,
        eval_fn=_eval_argmax,
    )
)
_register(
    _variadic_spec(
        "count_where",
        signature="count_where(c1, c2, ...)",
        summary="How many of the bool arguments are true.",
        returns="int",
        family=FAMILY_STATISTICS,
        return_type=_return_int,
        element_check=_ensure_all_bool,
        eval_fn=_eval_count_where,
    )
)

# --- Logic and masks ---
_register(
    _variadic_spec(
        "all",
        signature="all(c1, c2, ...)",
        summary="True when every bool argument is true.",
        returns="bool",
        family=FAMILY_LOGIC,
        return_type=_return_bool,
        element_check=_ensure_all_bool,
        eval_fn=_eval_all,
    )
)
_register(
    _variadic_spec(
        "any",
        signature="any(c1, c2, ...)",
        summary="True when at least one bool argument is true.",
        returns="bool",
        family=FAMILY_LOGIC,
        return_type=_return_bool,
        element_check=_ensure_all_bool,
        eval_fn=_eval_any,
    )
)
_register(
    FunctionSpec(
        name="where",
        signature="where(condition, if_true, if_false)",
        summary="Select `if_true` where `condition` holds, else `if_false`; the branches must share a type.",
        returns="the branch type (numeric branches promote; a reference and an int give the reference)",
        family=FAMILY_LOGIC,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=3,
        max_args=3,
        return_type=_return_where,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("where", args, 3, 3),
            lambda: _ensure_bool_arg("where", args[0], 1),
            lambda: _ensure_branches("where", args[1], args[2]),
        ),
        eval_fn=_eval_where,
    )
)
_register(
    FunctionSpec(
        name="masked_add",
        signature="masked_add(value, delta, mask)",
        summary="`value + delta` where `mask` holds, `value` elsewhere.",
        returns="the numeric type of `value` and `delta` (promoted)",
        family=FAMILY_LOGIC,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=3,
        max_args=3,
        return_type=_return_masked_numeric,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("masked_add", args, 3, 3),
            lambda: _ensure_all_numeric("masked_add", args[:2]),
            lambda: _ensure_bool_arg("masked_add", args[2], 3),
        ),
        eval_fn=_eval_masked_add,
    )
)
_register(
    FunctionSpec(
        name="masked_set",
        signature="masked_set(value, replacement, mask)",
        summary="`replacement` where `mask` holds, `value` elsewhere.",
        returns="the type of `value` (numeric pairs promote)",
        family=FAMILY_LOGIC,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=3,
        max_args=3,
        return_type=_return_masked_numeric,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("masked_set", args, 3, 3),
            lambda: _ensure_matching_or_numeric("masked_set", args[0], args[1]),
            lambda: _ensure_bool_arg("masked_set", args[2], 3),
        ),
        eval_fn=_eval_masked_set,
    )
)
_register(
    FunctionSpec(
        name="gather",
        signature="gather(values, index)",
        summary="`values[index]`: one element of a vector (or tensor1d) inside the reading world's value.",
        returns="the element type of `values` (int for vec2i/vec3i/vecNi, else float)",
        family=FAMILY_LOGIC,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=2,
        max_args=2,
        return_type=_return_element,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("gather", args, 2, 2),
            lambda: _ensure_element_vector_arg("gather", args[0], 1),
            lambda: _ensure_int("gather", args[1]),
        ),
        eval_fn=_eval_gather,
    )
)
_register(
    FunctionSpec(
        name="scatter",
        signature="scatter(base, index, update)",
        summary="A copy of the vector (or tensor1d) `base` with element `index` set to `update`, inside each world's value.",
        returns="the type of `base`",
        family=FAMILY_LOGIC,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=3,
        max_args=3,
        return_type=_return_first,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("scatter", args, 3, 3),
            lambda: _ensure_element_vector_arg("scatter", args[0], 1),
            lambda: _ensure_int("scatter", args[1]),
            lambda: _ensure_element_update("scatter", args[0], args[2]),
        ),
        eval_fn=_eval_scatter,
    )
)
_register(
    FunctionSpec(
        name="one_hot",
        signature="one_hot(index, classes)",
        summary="One-hot vector of width `classes` (a literal >= 2) with a 1.0 at `index`.",
        returns="vecNf of width `classes`",
        family=FAMILY_LOGIC,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=2,
        max_args=2,
        return_type=_return_vecnf,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("one_hot", args, 2, 2),
            lambda: _ensure_int("one_hot", args[0]),
            lambda: _ensure_int("one_hot", args[1]),
        ),
        eval_fn=_eval_one_hot,
    )
)

# --- Sampling ---
_register(
    FunctionSpec(
        name="normal_dist",
        signature="normal_dist([mean[, std]])",
        summary="Gaussian draw, one per row of the context, from the world's own stream.",
        returns="float",
        family=FAMILY_SAMPLING,
        requires=(REQUIRES_RANDOM,),
        shape=SHAPE_DRAW,
        min_args=0,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("normal_dist", args, 0, 2), lambda: _ensure_all_numeric("normal_dist", args)
        ),
        eval_fn=_eval_normal_dist,
    )
)
_register(
    FunctionSpec(
        name="uniform",
        signature="uniform([low[, high]])",
        summary=(
            "Uniform draw in `[low, high)` (`[0, 1)` with one or no arguments), one per row of the context, from the " "world's own stream."
        ),
        returns="float",
        family=FAMILY_SAMPLING,
        requires=(REQUIRES_RANDOM,),
        shape=SHAPE_DRAW,
        min_args=0,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("uniform", args, 0, 2), lambda: _ensure_all_numeric("uniform", args)
        ),
        eval_fn=_eval_uniform,
    )
)
_register(
    FunctionSpec(
        name="perlin_noise",
        signature="perlin_noise(x[, y[, seed]])",
        summary="Deterministic 2-D Perlin gradient noise at `(x, y)`.",
        returns="float",
        family=FAMILY_SAMPLING,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=1,
        max_args=3,
        return_type=_return_float,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("perlin_noise", args, 1, 3), lambda: _ensure_all_numeric("perlin_noise", args)
        ),
        eval_fn=_eval_perlin_noise,
    )
)
_register(
    FunctionSpec(
        name="simplex_noise",
        signature="simplex_noise(x[, y[, seed]])",
        summary="Alias of `perlin_noise`: the same gradient-noise field, not a simplex lattice.",
        returns="float",
        family=FAMILY_SAMPLING,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=1,
        max_args=3,
        return_type=_return_float,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("simplex_noise", args, 1, 3), lambda: _ensure_all_numeric("simplex_noise", args)
        ),
        eval_fn=_eval_simplex_noise,
    )
)

# --- Temporal ---
_register(
    _numeric_spec(
        "time_in_window",
        signature="time_in_window(time, start, end)",
        summary="True when `time` modulo a 24-tick day lies in `[start, end)`, wrapping past midnight.",
        returns="bool",
        family=FAMILY_TEMPORAL,
        arity=3,
        return_type=_return_bool,
        eval_fn=_eval_time_in_window,
    )
)
_register(
    _numeric_spec(
        "phase_sin",
        signature="phase_sin(time, period)",
        summary="`sin(2π · time / period)`.",
        returns="float",
        family=FAMILY_TEMPORAL,
        arity=2,
        return_type=_return_float,
        eval_fn=_eval_phase_sin,
    )
)
_register(
    _numeric_spec(
        "phase_cos",
        signature="phase_cos(time, period)",
        summary="`cos(2π · time / period)`.",
        returns="float",
        family=FAMILY_TEMPORAL,
        arity=2,
        return_type=_return_float,
        eval_fn=_eval_phase_cos,
    )
)
_register(
    FunctionSpec(
        name="lag",
        signature="lag(x, n)",
        summary=(
            "The value `x` held `n` ticks ago (`n` a literal, 1 to 256); before `n` ticks of the episode exist, "
            "the value `x` held when the episode began."
        ),
        returns=NUMERIC_RETURNS,
        family=FAMILY_TEMPORAL,
        requires=(REQUIRES_HISTORY,),
        shape=SHAPE_POINTWISE,
        min_args=2,
        max_args=2,
        return_type=_return_numeric,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("lag", args, 2, 2), lambda: _ensure_all_numeric("lag", [args[0]]), lambda: _ensure_int("lag", args[1])
        ),
        eval_fn=_eval_lag,
    )
)
_register(
    FunctionSpec(
        name="delta",
        signature="delta(x)",
        summary="`x - lag(x, 1)`.",
        returns=NUMERIC_RETURNS,
        family=FAMILY_TEMPORAL,
        requires=(REQUIRES_HISTORY,),
        shape=SHAPE_POINTWISE,
        min_args=1,
        max_args=1,
        return_type=_return_numeric,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("delta", args, 1, 1), lambda: _ensure_all_numeric("delta", args)
        ),
        eval_fn=_eval_delta,
    )
)
_register(
    FunctionSpec(
        name="moving_average",
        signature="moving_average(x, window)",
        summary="Mean of `x, lag(x, 1), …, lag(x, window - 1)` (`window` a literal, 1 to 256).",
        returns="float",
        family=FAMILY_TEMPORAL,
        requires=(REQUIRES_HISTORY,),
        shape=SHAPE_POINTWISE,
        min_args=2,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("moving_average", args, 2, 2),
            lambda: _ensure_all_numeric("moving_average", [args[0]]),
            lambda: _ensure_int("moving_average", args[1]),
        ),
        eval_fn=_eval_moving_average,
    )
)
_register(
    FunctionSpec(
        name="ema",
        signature="ema(x, alpha)",
        summary="`alpha · x + (1 − alpha) · ema` of the previous tick, `alpha` a literal in `(0, 1]`; the episode-start value seeds it.",
        returns="float",
        family=FAMILY_TEMPORAL,
        requires=(REQUIRES_HISTORY,),
        shape=SHAPE_POINTWISE,
        min_args=2,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("ema", args, 2, 2),
            lambda: _ensure_all_numeric("ema", [args[0]]),
            lambda: _ensure_all_numeric("ema", [args[1]]),
        ),
        eval_fn=_eval_ema,
    )
)
_register(
    FunctionSpec(
        name="rate_of_change",
        signature="rate_of_change(x, window)",
        summary="`(x - lag(x, window)) / window` (`window` a literal, 1 to 256).",
        returns="float",
        family=FAMILY_TEMPORAL,
        requires=(REQUIRES_HISTORY,),
        shape=SHAPE_POINTWISE,
        min_args=2,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("rate_of_change", args, 2, 2),
            lambda: _ensure_all_numeric("rate_of_change", [args[0]]),
            lambda: _ensure_int("rate_of_change", args[1]),
        ),
        eval_fn=_eval_rate_of_change,
    )
)
_register(
    FunctionSpec(
        name="rising_edge",
        signature="rising_edge(flag)",
        summary="`flag and not lag(flag, 1)`: true on the tick `flag` turns from false to true.",
        returns="bool",
        family=FAMILY_TEMPORAL,
        requires=(REQUIRES_HISTORY,),
        shape=SHAPE_POINTWISE,
        min_args=1,
        max_args=1,
        return_type=_return_bool,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("rising_edge", args, 1, 1), lambda: _ensure_all_bool("rising_edge", args)
        ),
        eval_fn=_eval_rising_edge,
    )
)
_register(
    FunctionSpec(
        name="falling_edge",
        signature="falling_edge(flag)",
        summary="`not flag and lag(flag, 1)`: true on the tick `flag` turns from true to false.",
        returns="bool",
        family=FAMILY_TEMPORAL,
        requires=(REQUIRES_HISTORY,),
        shape=SHAPE_POINTWISE,
        min_args=1,
        max_args=1,
        return_type=_return_bool,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("falling_edge", args, 1, 1), lambda: _ensure_all_bool("falling_edge", args)
        ),
        eval_fn=_eval_falling_edge,
    )
)

# --- Spatial (vector variables; reduced over the vector axis, never over agents) ---
_register(
    FunctionSpec(
        name="distance",
        signature='distance(a, b[, "manhattan" | "euclidean"])',
        summary="Distance between two vector variables of one width, measured in float (default euclidean).",
        returns="float",
        family=FAMILY_SPATIAL,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=2,
        max_args=3,
        return_type=_return_float,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("distance", args, 2, 3),
            lambda: _ensure_vector_arg("distance", args[0], 1),
            lambda: _ensure_vector_arg("distance", args[1], 2),
            lambda: _ensure_same_vector_width("distance", args[0], args[1]),
            lambda: _ensure_optional_string_arg("distance", args, 2),
        ),
        eval_fn=_eval_distance,
    )
)
_register(
    FunctionSpec(
        name="manhattan_distance",
        signature="manhattan_distance(a, b)",
        summary="L1 distance between two vector variables of one width, measured in float.",
        returns="float",
        family=FAMILY_SPATIAL,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=2,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("manhattan_distance", args, 2, 2),
            lambda: _ensure_vector_arg("manhattan_distance", args[0], 1),
            lambda: _ensure_vector_arg("manhattan_distance", args[1], 2),
            lambda: _ensure_same_vector_width("manhattan_distance", args[0], args[1]),
        ),
        eval_fn=_eval_manhattan_distance,
    )
)
_register(
    FunctionSpec(
        name="within_radius",
        signature='within_radius(a, b, radius[, "manhattan" | "euclidean"])',
        summary="True when `distance(a, b)` is at most `radius`.",
        returns="bool",
        family=FAMILY_SPATIAL,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=3,
        max_args=4,
        return_type=_return_bool,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("within_radius", args, 3, 4),
            lambda: _ensure_vector_arg("within_radius", args[0], 1),
            lambda: _ensure_vector_arg("within_radius", args[1], 2),
            lambda: _ensure_same_vector_width("within_radius", args[0], args[1]),
            lambda: _ensure_all_numeric("within_radius", [args[2]]),
            lambda: _ensure_optional_string_arg("within_radius", args, 3),
        ),
        eval_fn=_eval_within_radius,
    )
)
_register(
    FunctionSpec(
        name="nearest",
        signature='nearest(point, candidates[, "manhattan" | "euclidean"])',
        summary="Row index of the candidate nearest to `point`; `candidates` is a tensor2d of rows in the point's world.",
        returns="int",
        family=FAMILY_SPATIAL,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=2,
        max_args=3,
        return_type=_return_int,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("nearest", args, 2, 3),
            lambda: _ensure_vector_arg("nearest", args[0], 1),
            lambda: _ensure_candidates_arg("nearest", args[1], 2),
            lambda: _ensure_same_vector_width("nearest", args[0], args[1]),
            lambda: _ensure_optional_string_arg("nearest", args, 2),
        ),
        eval_fn=_eval_nearest,
    )
)
_register(
    FunctionSpec(
        name="normalize",
        signature="normalize(v)",
        summary="`v` scaled to unit euclidean length (the zero vector stays zero).",
        returns="the float vector type of `v`'s width (vec2f, vec3f or vecNf)",
        family=FAMILY_SPATIAL,
        requires=(),
        shape=SHAPE_POINTWISE,
        min_args=1,
        max_args=1,
        return_type=_return_float_vector,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("normalize", args, 1, 1),
            lambda: _ensure_vector_arg("normalize", args[0], 1),
        ),
        eval_fn=_eval_normalize,
    )
)

# --- Affordance (read the agent and affordance positions the engine threads into the context) ---
_register(
    FunctionSpec(
        name="distance_to_affordance",
        signature='distance_to_affordance("NAME"[, "manhattan" | "euclidean"])',
        summary="Each agent's distance to the named affordance (default manhattan); infinity when it is not deployed.",
        returns="float",
        family=FAMILY_AFFORDANCE,
        requires=(REQUIRES_POSITIONS,),
        shape=SHAPE_AGENT_ROWS,
        min_args=1,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("distance_to_affordance", args, 1, 2),
            lambda: _ensure_string_arg("distance_to_affordance", args[0], 1),
            lambda: _ensure_optional_string_arg("distance_to_affordance", args, 1),
        ),
        eval_fn=_eval_distance_to_affordance,
    )
)
_register(
    FunctionSpec(
        name="in_range",
        signature='in_range("NAME", radius[, "manhattan" | "euclidean"])',
        summary="True for each agent within `radius` of the named affordance.",
        returns="bool",
        family=FAMILY_AFFORDANCE,
        requires=(REQUIRES_POSITIONS,),
        shape=SHAPE_AGENT_ROWS,
        min_args=2,
        max_args=3,
        return_type=_return_bool,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("in_range", args, 2, 3),
            lambda: _ensure_string_arg("in_range", args[0], 1),
            lambda: _ensure_all_numeric("in_range", [args[1]]),
            lambda: _ensure_optional_string_arg("in_range", args, 2),
        ),
        eval_fn=_eval_in_range,
    )
)
_register(
    FunctionSpec(
        name="direction_to_affordance",
        signature='direction_to_affordance("NAME"[, "manhattan" | "euclidean"])',
        summary="Unit vector from each agent towards the named affordance (zero at the affordance or when it is not deployed).",
        returns="vecNf of the substrate's position width",
        family=FAMILY_AFFORDANCE,
        requires=(REQUIRES_POSITIONS,),
        shape=SHAPE_AGENT_ROWS,
        min_args=1,
        max_args=2,
        return_type=_return_vecnf,
        validate_args=lambda args: _run_validators(
            lambda: _ensure_arg_count("direction_to_affordance", args, 1, 2),
            lambda: _ensure_string_arg("direction_to_affordance", args[0], 1),
            lambda: _ensure_optional_string_arg("direction_to_affordance", args, 1),
        ),
        eval_fn=_eval_direction_to_affordance,
    )
)


TEMPORAL_FUNCTIONS: frozenset[str] = frozenset(name for name, spec in FUNCTION_SPECS.items() if REQUIRES_HISTORY in spec.requires)
"""The operators that read a history ring: every function that requires temporal history.

Derived from ``FUNCTION_SPECS``, never listed by hand, so a new history operator joins
it by declaring ``REQUIRES_HISTORY``. ``lag`` alone never reads its argument's current
value, so it alone may close a self-reference."""


def unserved_requirement(node: ASTNode, carried: frozenset[str]) -> str | None:
    """The first function ``node`` calls whose context requirement ``carried`` lacks, described; None if all are served.

    The one predicate every consumer refuses context-bound functions by: a profile
    expression carries history, positions and a random stream; a transition write or
    rule carries a random stream; an effect or interaction pipeline carries positions and
    a random stream; a spawn predicate carries none (``townlet.vfs.namespace``).
    """
    from dataclasses import fields

    from townlet.world.expression.ast_nodes import ASTNode as _ASTNode
    from townlet.world.expression.ast_nodes import FunctionCall

    found: list[str] = []

    def visit(value: Any) -> None:
        if found:
            return
        if isinstance(value, FunctionCall):
            spec = FUNCTION_SPECS.get(value.function_name)
            missing = [requirement for requirement in (spec.requires if spec is not None else ()) if requirement not in carried]
            if missing:
                found.append(f"'{value.function_name}', which needs {' and '.join(missing)}")
                return
        if isinstance(value, _ASTNode):
            for ast_field in fields(value):
                visit(getattr(value, ast_field.name))
        elif isinstance(value, list | tuple):
            for item in value:
                visit(item)

    visit(node)
    return found[0] if found else None
