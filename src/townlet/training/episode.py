"""Shared immutable outcomes for completed population episode lanes."""

import hashlib
import json
import math
from dataclasses import dataclass, fields, replace
from numbers import Real
from typing import Any, Literal, get_args

import torch

CompletionReason = Literal["authored_terminal", "retirement", "cap", "budget", "shutdown", "checkpoint"]
RunnerCompletionReason = Literal["cap", "budget", "shutdown", "checkpoint"]


@dataclass(frozen=True)
class EpisodeCompletion:
    """An owned CPU snapshot of one nonempty lane at its completion boundary."""

    agent_idx: int
    reason: CompletionReason
    survival_time: int
    final_observation: torch.Tensor
    final_meters: torch.Tensor


@dataclass(frozen=True)
class LaneOutcome:
    """An owned completion envelope with explicit caller-supplied world identity.

    Tensor readings are detached CPU copies. Frozen fields prevent rebinding;
    consumers must treat the owned tensor readings as immutable event data.
    """

    outcome: EpisodeCompletion
    batch_episode: int
    planned_horizon: int
    reward_total: float
    reward_extrinsic: float
    reward_intrinsic: float
    reward_shaping: float
    policy_entropy: float
    world_id: str
    world_episode_seq: int

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, EpisodeCompletion):
            raise ValueError("outcome must be an EpisodeCompletion")
        for name, minimum in (("batch_episode", 0), ("planned_horizon", 1), ("world_episode_seq", 0)):
            value = getattr(self, name)
            if type(value) is not int or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")
        if not isinstance(self.world_id, str) or not self.world_id:
            raise ValueError("world_id must be a concrete nonempty string")
        for name in ("reward_total", "reward_extrinsic", "reward_intrinsic", "reward_shaping", "policy_entropy"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
                raise ValueError(f"{name} must be a finite real value")
            object.__setattr__(self, name, float(value))
        object.__setattr__(
            self,
            "outcome",
            replace(
                self.outcome,
                final_observation=self.outcome.final_observation.detach().cpu().clone(),
                final_meters=self.outcome.final_meters.detach().cpu().clone(),
            ),
        )


def lane_outcome_from_state(state: dict[str, Any]) -> LaneOutcome:
    """Read the exact current envelope mapping, with no historical decoding."""
    if not isinstance(state, dict) or set(state) != {field.name for field in fields(LaneOutcome)}:
        raise ValueError("Invalid LaneOutcome fields")
    completion = state["outcome"]
    if not isinstance(completion, dict) or set(completion) != {field.name for field in fields(EpisodeCompletion)}:
        raise ValueError("Invalid EpisodeCompletion fields")
    for name in ("agent_idx", "survival_time"):
        if type(completion[name]) is not int or completion[name] < (1 if name == "survival_time" else 0):
            raise ValueError(f"Invalid completion {name}")
    if completion["reason"] not in get_args(CompletionReason):
        raise ValueError("Unknown completion reason")
    for name in ("final_observation", "final_meters"):
        reading = completion[name]
        if not isinstance(reading, torch.Tensor) or reading.layout != torch.strided or not torch.isfinite(reading).all().item():
            raise ValueError("Completion readings must be finite dense tensors")
    scalars = {key: value for key, value in state.items() if key != "outcome"}
    event = LaneOutcome(outcome=EpisodeCompletion(**completion), **scalars)
    if event.outcome.survival_time > event.planned_horizon:
        raise ValueError("Completion exceeds planned horizon")
    return event


def lane_outcome_state(event: LaneOutcome) -> dict[str, Any]:
    """Return an independently owned, exact current envelope mapping."""
    if not isinstance(event, LaneOutcome):
        raise ValueError("Expected LaneOutcome")
    state = {field.name: getattr(event, field.name) for field in fields(LaneOutcome)}
    state["outcome"] = {field.name: getattr(event.outcome, field.name) for field in fields(EpisodeCompletion)}
    owned = lane_outcome_from_state(state)
    state = {field.name: getattr(owned, field.name) for field in fields(LaneOutcome)}
    state["outcome"] = {field.name: getattr(owned.outcome, field.name) for field in fields(EpisodeCompletion)}
    return state


_READING_DTYPES = {
    str(dtype): dtype
    for dtype in (
        torch.bool,
        torch.uint8,
        torch.int8,
        torch.int16,
        torch.int32,
        torch.int64,
        torch.float16,
        torch.bfloat16,
        torch.float32,
        torch.float64,
        torch.complex64,
        torch.complex128,
    )
}


@dataclass(frozen=True)
class FrozenLaneOutcome:
    """An immutable full-envelope reading suitable for prepared sink handoffs."""

    payload: bytes
    fingerprint: str

    def to_outcome(self) -> LaneOutcome:
        """Verify and decode this current canonical payload into owned tensors."""
        if not isinstance(self.payload, bytes) or hashlib.sha256(self.payload).hexdigest() != self.fingerprint:
            raise ValueError("Invalid frozen outcome fingerprint")
        try:
            state = json.loads(self.payload)
            for name in ("final_observation", "final_meters"):
                reading = state["outcome"][name]
                if not isinstance(reading, dict) or set(reading) != {"dtype", "shape", "data"}:
                    raise ValueError("Invalid encoded tensor")
                dtype, shape = _READING_DTYPES[reading["dtype"]], reading["shape"]
                if not isinstance(shape, list) or any(type(size) is not int or size < 0 for size in shape):
                    raise ValueError("Invalid tensor shape")
                raw = bytes.fromhex(reading["data"])
                if len(raw) != math.prod(shape) * torch.empty((), dtype=dtype).element_size():
                    raise ValueError("Invalid tensor byte length")
                if raw:
                    tensor = torch.frombuffer(bytearray(raw), dtype=dtype).clone()
                else:
                    tensor = torch.empty(0, dtype=dtype)
                state["outcome"][name] = tensor.reshape(shape)
            return lane_outcome_from_state(state)
        except (KeyError, TypeError, RuntimeError, json.JSONDecodeError) as error:
            raise ValueError("Invalid frozen outcome content") from error


def freeze_lane_outcome(event: LaneOutcome) -> FrozenLaneOutcome:
    """Pin identity, every scalar, and dtype/shape/raw bytes of both readings."""
    state = lane_outcome_state(event)
    for name in ("final_observation", "final_meters"):
        reading = state["outcome"][name].contiguous()
        if str(reading.dtype) not in _READING_DTYPES:
            raise ValueError("Unsupported completion reading dtype")
        state["outcome"][name] = {
            "dtype": str(reading.dtype),
            "shape": list(reading.shape),
            "data": reading.reshape(-1).view(torch.uint8).numpy().tobytes().hex(),
        }
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return FrozenLaneOutcome(payload=payload, fingerprint=hashlib.sha256(payload).hexdigest())


def lane_outcome_fingerprint(event: LaneOutcome) -> str:
    """Shared fingerprint definition for completion producers and sinks."""
    return freeze_lane_outcome(event).fingerprint
