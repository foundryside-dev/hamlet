"""Shared registry for expression functions (signatures + evaluation)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import torch

Numeric = {"int", "float"}


@dataclass(frozen=True)
class FunctionSpec:
    name: str
    min_args: int
    max_args: int | None
    return_type: Callable[[list[str]], str]
    validate_args: Callable[[list[str]], None]
    eval_fn: Callable[[list[torch.Tensor]], torch.Tensor]


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


def _return_numeric(args: list[str]) -> str:
    return "float" if "float" in args else "int"


def _return_bool(_: list[str]) -> str:
    return "bool"


def _return_float(_: list[str]) -> str:
    return "float"


def _return_int(_: list[str]) -> str:
    return "int"


def _eval_stack_numeric(args: list[torch.Tensor], reducer: Callable[[torch.Tensor], torch.Tensor]) -> torch.Tensor:
    stacked = torch.stack(args, dim=0)
    return reducer(stacked)


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
        eval_fn=lambda ts: torch.max(ts[0], ts[1]),
    )
)

_register(
    FunctionSpec(
        name="min",
        min_args=2,
        max_args=2,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("min", args, 2, 2), _ensure_all_numeric("min", args)),
        eval_fn=lambda ts: torch.min(ts[0], ts[1]),
    )
)

_register(
    FunctionSpec(
        name="abs",
        min_args=1,
        max_args=1,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("abs", args, 1, 1), _ensure_all_numeric("abs", args)),
        eval_fn=lambda ts: torch.abs(ts[0]),
    )
)

_register(
    FunctionSpec(
        name="clamp",
        min_args=3,
        max_args=3,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("clamp", args, 3, 3), _ensure_all_numeric("clamp", args)),
        eval_fn=lambda ts: torch.clamp(ts[0], min=ts[1], max=ts[2]),
    )
)

_register(
    FunctionSpec(
        name="clamp01",
        min_args=1,
        max_args=1,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("clamp01", args, 1, 1), _ensure_all_numeric("clamp01", args)),
        eval_fn=lambda ts: torch.clamp(ts[0], min=0.0, max=1.0),
    )
)

_register(
    FunctionSpec(
        name="sigmoid",
        min_args=1,
        max_args=1,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("sigmoid", args, 1, 1), _ensure_all_numeric("sigmoid", args)),
        eval_fn=lambda ts: torch.sigmoid(ts[0]),
    )
)

_register(
    FunctionSpec(
        name="tanh",
        min_args=1,
        max_args=1,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("tanh", args, 1, 1), _ensure_all_numeric("tanh", args)),
        eval_fn=lambda ts: torch.tanh(ts[0]),
    )
)

_register(
    FunctionSpec(
        name="smoothstep",
        min_args=3,
        max_args=3,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("smoothstep", args, 3, 3), _ensure_all_numeric("smoothstep", args)),
        eval_fn=lambda ts: (
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
        eval_fn=lambda ts: torch.mean(torch.stack(ts, dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="variance",
        min_args=1,
        max_args=None,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("variance", args, 1, None), _ensure_all_numeric("variance", args)),
        eval_fn=lambda ts: torch.var(torch.stack(ts, dim=0), dim=0, unbiased=False),
    )
)

_register(
    FunctionSpec(
        name="sum",
        min_args=1,
        max_args=None,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("sum", args, 1, None), _ensure_all_numeric("sum", args)),
        eval_fn=lambda ts: torch.sum(torch.stack(ts, dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="product",
        min_args=1,
        max_args=None,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("product", args, 1, None), _ensure_all_numeric("product", args)),
        eval_fn=lambda ts: torch.prod(torch.stack(ts, dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="normalize",
        min_args=1,
        max_args=None,
        return_type=_return_float,
        validate_args=lambda args: (_ensure_arg_count("normalize", args, 1, None), _ensure_all_numeric("normalize", args)),
        eval_fn=lambda ts: (lambda stacked: stacked / torch.clamp(torch.sum(torch.abs(stacked), dim=0, keepdim=True), min=1e-8))(
            torch.stack(ts, dim=0)
        ),
    )
)

_register(
    FunctionSpec(
        name="min_all",
        min_args=1,
        max_args=None,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("min_all", args, 1, None), _ensure_all_numeric("min_all", args)),
        eval_fn=lambda ts: torch.min(torch.stack(ts, dim=0), dim=0).values,
    )
)

_register(
    FunctionSpec(
        name="max_all",
        min_args=1,
        max_args=None,
        return_type=_return_numeric,
        validate_args=lambda args: (_ensure_arg_count("max_all", args, 1, None), _ensure_all_numeric("max_all", args)),
        eval_fn=lambda ts: torch.max(torch.stack(ts, dim=0), dim=0).values,
    )
)

_register(
    FunctionSpec(
        name="count_where",
        min_args=1,
        max_args=None,
        return_type=_return_int,
        validate_args=lambda args: (_ensure_arg_count("count_where", args, 1, None), _ensure_all_bool("count_where", args)),
        eval_fn=lambda ts: torch.sum(torch.stack([t.to(dtype=torch.int64) for t in ts], dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="argmin",
        min_args=1,
        max_args=None,
        return_type=_return_int,
        validate_args=lambda args: (_ensure_arg_count("argmin", args, 1, None), _ensure_all_numeric("argmin", args)),
        eval_fn=lambda ts: torch.argmin(torch.stack(ts, dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="argmax",
        min_args=1,
        max_args=None,
        return_type=_return_int,
        validate_args=lambda args: (_ensure_arg_count("argmax", args, 1, None), _ensure_all_numeric("argmax", args)),
        eval_fn=lambda ts: torch.argmax(torch.stack(ts, dim=0), dim=0),
    )
)

_register(
    FunctionSpec(
        name="threshold",
        min_args=3,
        max_args=3,
        return_type=_return_bool,
        validate_args=lambda args: (_ensure_arg_count("threshold", args, 3, 3), _ensure_all_numeric("threshold", args)),
        eval_fn=lambda ts: torch.where(ts[0] >= ts[2], torch.ones_like(ts[0], dtype=torch.bool), ts[0] > ts[1]),
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
        eval_fn=lambda ts: (
            torch.randn((), device=(ts[0].device if ts else torch.device("cpu")))
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
        eval_fn=lambda ts: (
            torch.rand((), device=(ts[0].device if ts else torch.device("cpu")))
            if not ts
            else torch.rand_like(ts[0]) * (ts[1] - ts[0]) + ts[0] if len(ts) == 2 else torch.rand_like(ts[0])
        ),
    )
)
