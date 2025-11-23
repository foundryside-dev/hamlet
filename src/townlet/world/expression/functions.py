"""Shared registry for expression functions (signatures + evaluation)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import torch

if TYPE_CHECKING:  # pragma: no cover
    from townlet.world.expression.ast_nodes import ASTNode
    from townlet.world.expression.context import ExecutionContext

Numeric = {"int", "float"}


@dataclass(frozen=True)
class FunctionSpec:
    name: str
    min_args: int
    max_args: int | None
    return_type: Callable[[list[str]], str]
    validate_args: Callable[[list[str]], None]
    eval_fn: Callable[[list[Any], ExecutionContext, list[ASTNode]], torch.Tensor | Any]


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


def _ensure_all_string(name: str, args: list[str]) -> None:
    if not all(arg == "str" for arg in args):
        raise ValueError(f"Function '{name}' requires string args, got {args}")


def _ensure_int(name: str, arg: str) -> None:
    if arg != "int":
        raise ValueError(f"Function '{name}' requires integer argument, got {arg}")


def _return_numeric(args: list[str]) -> str:
    return "float" if "float" in args else "int"


def _return_bool(_: list[str]) -> str:
    return "bool"


def _return_float(_: list[str]) -> str:
    return "float"


def _return_int(_: list[str]) -> str:
    return "int"


def _eval_stack_numeric(
    args: list[torch.Tensor],
    reducer: Callable[[torch.Tensor], torch.Tensor],
) -> torch.Tensor:
    stacked = torch.stack(args, dim=0)
    return reducer(stacked)


def _resolve_device(args: list[torch.Tensor], context: ExecutionContext) -> torch.device:
    """Prefer context device, then first argument, else CPU."""
    if context.device is not None:
        return context.device
    if args:
        return args[0].device
    return torch.device("cpu")


def _temporal_key(arg_node: ASTNode) -> str:
    from townlet.world.expression.ast_nodes import PathAccess, Variable

    if isinstance(arg_node, PathAccess):
        return ".".join(arg_node.segments)
    if isinstance(arg_node, Variable):
        return f"vfs.{arg_node.name}"
    raise ValueError("Temporal operators require a variable or path argument as the first parameter")


def _require_history(context: ExecutionContext) -> None:
    if context.history is None:
        raise RuntimeError("Temporal operators require a TemporalHistory on the execution context")


def _require_positions(context: ExecutionContext) -> torch.Tensor:
    if context.agent_positions is None:
        raise RuntimeError("Spatial operators require agent_positions on the execution context")
    return context.agent_positions


def _affordance_position(context: ExecutionContext, name: str) -> torch.Tensor | None:
    positions = context.affordance_positions or {}
    pos = positions.get(name)
    if pos is None:
        return None
    return pos


FUNCTION_SPECS: dict[str, FunctionSpec] = {}


def _register(spec: FunctionSpec) -> None:
    FUNCTION_SPECS[spec.name] = spec


# --- Core math/utility ---
_register(
    FunctionSpec(
        name="max",
        min_args=2,
        max_args=2,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("max", args, 2, 2), _ensure_all_numeric("max", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.max(ts[0], ts[1]),
    )
)

_register(
    FunctionSpec(
        name="min",
        min_args=2,
        max_args=2,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("min", args, 2, 2), _ensure_all_numeric("min", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.min(ts[0], ts[1]),
    )
)

_register(
    FunctionSpec(
        name="abs",
        min_args=1,
        max_args=1,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("abs", args, 1, 1), _ensure_all_numeric("abs", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.abs(ts[0]),
    )
)

_register(
    FunctionSpec(
        name="clamp",
        min_args=3,
        max_args=3,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("clamp", args, 3, 3), _ensure_all_numeric("clamp", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.clamp(ts[0], min=ts[1], max=ts[2]),
    )
)

_register(
    FunctionSpec(
        name="clamp01",
        min_args=1,
        max_args=1,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("clamp01", args, 1, 1), _ensure_all_numeric("clamp01", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.clamp(ts[0], min=0.0, max=1.0),
    )
)

_register(
    FunctionSpec(
        name="sigmoid",
        min_args=1,
        max_args=1,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("sigmoid", args, 1, 1), _ensure_all_numeric("sigmoid", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.sigmoid(ts[0]),
    )
)

_register(
    FunctionSpec(
        name="tanh",
        min_args=1,
        max_args=1,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("tanh", args, 1, 1), _ensure_all_numeric("tanh", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.tanh(ts[0]),
    )
)

_register(
    FunctionSpec(
        name="smoothstep",
        min_args=3,
        max_args=3,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("smoothstep", args, 3, 3), _ensure_all_numeric("smoothstep", args)),
        eval_fn=lambda ts, context, arg_nodes: (
            lambda edge0, edge1, x: (lambda t: t * t * (3 - 2 * t))(torch.clamp((x - edge0) / (edge1 - edge0 + 1e-8), 0.0, 1.0))
        )(ts[0], ts[1], ts[2]),
    )
)

_register(
    FunctionSpec(
        name="mean",
        min_args=1,
        max_args=None,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("mean", args, 1, None), _ensure_all_numeric("mean", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.mean(torch.stack(ts, dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="variance",
        min_args=1,
        max_args=None,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("variance", args, 1, None), _ensure_all_numeric("variance", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.var(torch.stack(ts, dim=0), dim=0, unbiased=False),
    )
)

_register(
    FunctionSpec(
        name="sum",
        min_args=1,
        max_args=None,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("sum", args, 1, None), _ensure_all_numeric("sum", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.sum(torch.stack(ts, dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="product",
        min_args=1,
        max_args=None,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("product", args, 1, None), _ensure_all_numeric("product", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.prod(torch.stack(ts, dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="normalize",
        min_args=1,
        max_args=None,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("normalize", args, 1, None), _ensure_all_numeric("normalize", args)),
        eval_fn=lambda ts, context, arg_nodes: (
            lambda stacked: stacked / torch.clamp(torch.sum(torch.abs(stacked), dim=0, keepdim=True), min=1e-8)
        )(torch.stack(ts, dim=0)),
    )
)

_register(
    FunctionSpec(
        name="min_all",
        min_args=1,
        max_args=None,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("min_all", args, 1, None), _ensure_all_numeric("min_all", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.min(torch.stack(ts, dim=0), dim=0).values,
    )
)

_register(
    FunctionSpec(
        name="max_all",
        min_args=1,
        max_args=None,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("max_all", args, 1, None), _ensure_all_numeric("max_all", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.max(torch.stack(ts, dim=0), dim=0).values,
    )
)

_register(
    FunctionSpec(
        name="count_where",
        min_args=1,
        max_args=None,
        return_type=_return_int,
        validate_args=lambda args: (_ensure_arg_count("count_where", args, 1, None), _ensure_all_bool("count_where", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.sum(torch.stack([t.to(dtype=torch.int64) for t in ts], dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="argmin",
        min_args=1,
        max_args=None,
        return_type=_return_int,
        validate_args=lambda args: (_ensure_arg_count("argmin", args, 1, None), _ensure_all_numeric("argmin", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.argmin(torch.stack(ts, dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="argmax",
        min_args=1,
        max_args=None,
        return_type=_return_int,
        validate_args=lambda args: (_ensure_arg_count("argmax", args, 1, None), _ensure_all_numeric("argmax", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.argmax(torch.stack(ts, dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="threshold",
        min_args=3,
        max_args=3,
        return_type=_return_bool,
        validate_args=lambda args: (_ensure_arg_count("threshold", args, 3, 3), _ensure_all_numeric("threshold", args)),
        eval_fn=lambda ts, context, arg_nodes: torch.where(ts[0] >= ts[2], torch.ones_like(ts[0], dtype=torch.bool), ts[0] > ts[1]),
    )
)


# --- Noise/sampling (vectorized-safe) ---
_register(
    FunctionSpec(
        name="normal_dist",
        min_args=0,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: (
            _ensure_arg_count("normal_dist", args, 0, 2),
            None if not args else _ensure_all_numeric("normal_dist", args),
        ),
        eval_fn=lambda ts, context, arg_nodes: (
            torch.randn((), device=_resolve_device(ts, context))
            if not ts
            else torch.randn_like(ts[0]) * (ts[1] if len(ts) > 1 else 1.0) + ts[0]
        ),
    )
)

_register(
    FunctionSpec(
        name="uniform",
        min_args=0,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: (
            _ensure_arg_count("uniform", args, 0, 2),
            None if not args else _ensure_all_numeric("uniform", args),
        ),
        eval_fn=lambda ts, context, arg_nodes: (
            torch.rand((), device=_resolve_device(ts, context))
            if not ts
            else torch.rand_like(ts[0]) * (ts[1] - ts[0]) + ts[0] if len(ts) == 2 else torch.rand_like(ts[0])
        ),
    )
)


# --- Temporal/history ---
def _ensure_history_key(name: str, arg_nodes: list[ASTNode]) -> str:
    if not arg_nodes:
        raise ValueError(f"Function '{name}' requires at least one argument")
    return _temporal_key(arg_nodes[0])


def _scalar_int(arg: torch.Tensor, name: str) -> int:
    if arg.numel() != 1:
        raise ValueError(f"Function '{name}' expects a scalar integer argument")
    return int(arg.item())


def _scalar_float(arg: torch.Tensor, name: str) -> float:
    if arg.numel() != 1:
        raise ValueError(f"Function '{name}' expects a scalar float argument")
    return float(arg.item())


_register(
    FunctionSpec(
        name="lag",
        min_args=2,
        max_args=2,
        return_type=_return_numeric,
        validate_args=lambda args: (
            _ensure_arg_count("lag", args, 2, 2),
            _ensure_all_numeric("lag", [args[0]]),
            _ensure_int("lag", args[1]),
        ),
        eval_fn=lambda ts, context, arg_nodes: (
            (
                _require_history(context),
                context.history.lag(_ensure_history_key("lag", arg_nodes), _scalar_int(ts[1], "lag"), torch.zeros_like(ts[0])),
            )[1]
        ),
    )
)


_register(
    FunctionSpec(
        name="delta",
        min_args=1,
        max_args=1,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("delta", args, 1, 1), _ensure_all_numeric("delta", args)),
        eval_fn=lambda ts, context, arg_nodes: (
            _require_history(context),
            (
                lambda key: (
                    lambda lagged, valid: (
                        (lambda mask: torch.where(mask, ts[0] - lagged, torch.zeros_like(ts[0])))(
                            (lambda m: ((lambda mm: mm if mm.dim() == ts[0].dim() else mm.unsqueeze(-1).expand_as(ts[0]))(m)))(
                                valid if valid is not None else torch.zeros_like(ts[0]).bool()
                            )
                        )
                    )
                )(
                    context.history.lag(key, 1, torch.zeros_like(ts[0])),
                    context.history.has_history(key, 1),
                )
            )(_ensure_history_key("delta", arg_nodes)),
        )[1],
    )
)


_register(
    FunctionSpec(
        name="moving_average",
        min_args=2,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: (
            _ensure_arg_count("moving_average", args, 2, 2),
            _ensure_all_numeric("moving_average", [args[0]]),
            _ensure_int("moving_average", args[1]),
        ),
        eval_fn=lambda ts, context, arg_nodes: (
            (
                _require_history(context),
                context.history.moving_average(
                    _ensure_history_key("moving_average", arg_nodes), _scalar_int(ts[1], "moving_average"), ts[0]
                ),
            )[1]
        ),
    )
)


_register(
    FunctionSpec(
        name="ema",
        min_args=2,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: (
            _ensure_arg_count("ema", args, 2, 2),
            _ensure_all_numeric("ema", [args[0]]),
            _ensure_all_numeric("ema", [args[1]]),
        ),
        eval_fn=lambda ts, context, arg_nodes: (
            (_require_history(context), context.history.ema(_ensure_history_key("ema", arg_nodes), _scalar_float(ts[1], "ema"), ts[0]))[1]
        ),
    )
)


_register(
    FunctionSpec(
        name="rate_of_change",
        min_args=2,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: (
            _ensure_arg_count("rate_of_change", args, 2, 2),
            _ensure_all_numeric("rate_of_change", [args[0]]),
            _ensure_int("rate_of_change", args[1]),
        ),
        eval_fn=lambda ts, context, arg_nodes: (
            (
                _require_history(context),
                context.history.rate_of_change(
                    _ensure_history_key("rate_of_change", arg_nodes), _scalar_int(ts[1], "rate_of_change"), ts[0]
                ),
            )[1]
        ),
    )
)


_register(
    FunctionSpec(
        name="rising_edge",
        min_args=1,
        max_args=1,
        return_type=_return_bool,
        validate_args=lambda args: (_ensure_arg_count("rising_edge", args, 1, 1), _ensure_all_bool("rising_edge", args)),
        eval_fn=lambda ts, context, arg_nodes: (
            _require_history(context),
            context.history.edge(_ensure_history_key("rising_edge", arg_nodes), ts[0], rising=True),
        )[1],
    )
)


_register(
    FunctionSpec(
        name="falling_edge",
        min_args=1,
        max_args=1,
        return_type=_return_bool,
        validate_args=lambda args: (
            _ensure_arg_count("falling_edge", args, 1, 1),
            _ensure_all_bool("falling_edge", args),
        ),
        eval_fn=lambda ts, context, arg_nodes: (
            _require_history(context),
            context.history.edge(_ensure_history_key("falling_edge", arg_nodes), ts[0], rising=False),
        )[1],
    )
)


# --- Spatial ---


def _scalar_metric(name: str, args: list[Any]) -> str:
    if len(args) < 1:
        return "manhattan"
    metric = args[0]
    if not isinstance(metric, str):
        raise ValueError(f"Function '{name}' metric must be a string literal")
    metric_l = metric.lower()
    if metric_l not in {"manhattan", "euclidean"}:
        raise ValueError(f"Function '{name}' metric must be 'manhattan' or 'euclidean', got '{metric}'")
    return metric_l


def _distance(agent_positions: torch.Tensor, target: torch.Tensor, metric: str) -> torch.Tensor:
    if target.dim() == agent_positions.dim():
        target_exp = target.unsqueeze(0)
    else:
        target_exp = target
    diff = agent_positions - target_exp
    if metric == "manhattan":
        return diff.abs().sum(dim=-1)
    return diff.pow(2).sum(dim=-1).sqrt()


_register(
    FunctionSpec(
        name="distance_to_affordance",
        min_args=1,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: (
            _ensure_arg_count("distance_to_affordance", args, 1, 2),
            _ensure_all_string("distance_to_affordance", [args[0]]),
        ),
        eval_fn=lambda ts, context, arg_nodes: (
            _require_positions(context),
            (
                lambda name, metric: (
                    torch.full((context.agent_positions.shape[0],), float("inf"), device=context.agent_positions.device)
                    if (target := _affordance_position(context, name)) is None
                    else _distance(context.agent_positions, target, metric)
                )
            )(ts[0] if isinstance(ts[0], str) else str(ts[0]), _scalar_metric("distance_to_affordance", ts[1:])),
        )[1],
    )
)


_register(
    FunctionSpec(
        name="in_range",
        min_args=2,
        max_args=3,
        return_type=_return_bool,
        validate_args=lambda args: (
            _ensure_arg_count("in_range", args, 2, 3),
            _ensure_all_string("in_range", [args[0]]),
            _ensure_all_numeric("in_range", [args[1]]),
        ),
        eval_fn=lambda ts, context, arg_nodes: (
            _require_positions(context),
            (
                lambda name, radius, metric: (
                    (_ for _ in ()).throw(ValueError("in_range radius must be >= 0")) if radius < 0 else None,
                    (
                        torch.full((context.agent_positions.shape[0],), float("inf"), device=context.agent_positions.device)
                        if (target := _affordance_position(context, name)) is None
                        else _distance(context.agent_positions, target, metric)
                    )
                    <= radius,
                )[1]
            )(
                ts[0] if isinstance(ts[0], str) else str(ts[0]),
                float(ts[1]) if not isinstance(ts[1], torch.Tensor) else float(ts[1].item()),
                _scalar_metric("in_range", ts[2:]),
            ),
        )[1],
    )
)


_register(
    FunctionSpec(
        name="direction_to_affordance",
        min_args=1,
        max_args=2,
        return_type=_return_float,
        validate_args=lambda args: (
            _ensure_arg_count("direction_to_affordance", args, 1, 2),
            _ensure_all_string("direction_to_affordance", [args[0]]),
        ),
        eval_fn=lambda ts, context, arg_nodes: (
            _require_positions(context),
            (
                lambda name, metric: (
                    torch.zeros_like(context.agent_positions)
                    if (target := _affordance_position(context, name)) is None
                    else (lambda vec, norm: torch.where(norm.unsqueeze(-1) > 0, vec / norm.unsqueeze(-1), torch.zeros_like(vec)))(
                        target.unsqueeze(0) - context.agent_positions,
                        _distance(context.agent_positions, target, metric),
                    )
                )
            )(ts[0] if isinstance(ts[0], str) else str(ts[0]), _scalar_metric("direction_to_affordance", ts[1:])),
        )[1],
    )
)
