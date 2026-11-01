"""Owned replay transport, independent of storage and sampling implementations.

Constructors detach/clone tensors and copy receipt arrays; producer mutations
cannot rewrite history. Frozen fields prevent rebinding, not tensor mutation:
consumers own their transport and must not mutate it while a learner uses it.
No missing-mask inference is performed here. Explicitly unconstrained adapters
must supply their declared all-legal mask; constrained old history is archival.
"""

from dataclasses import dataclass, fields, replace
from typing import Literal

import numpy as np
import numpy.typing as npt
import torch
from torch import Tensor


class HistoricalLegalityUnavailable(ValueError):  # noqa: N818 - approved public interface
    """Unknown historical legality belongs in the approved archive, not replay."""


def _integer(name: str, value: int, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def _text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def validate_successor_masks(masks: Tensor, dones: Tensor, *, action_dim: int) -> None:
    """Validate actual successor sets; only terminal rows may have no action."""
    _integer("action_dim", action_dim, 1)
    if not isinstance(masks, Tensor) or masks.dtype != torch.bool:
        raise ValueError("next_action_masks/legal must be a bool tensor")
    if not isinstance(dones, Tensor) or dones.dtype != torch.bool:
        raise ValueError("dones must be a bool tensor")
    if masks.shape != (*dones.shape, action_dim) or masks.device != dones.device:
        raise ValueError("successor masks shape/device must match dones and action_dim")
    if ((~dones) & ~masks.any(dim=-1)).any():
        raise ValueError("nonterminal successor has no legal action")


@dataclass(frozen=True, slots=True)
class ReplayRequest:
    batch_size: int
    sequence_length: int
    min_transitions: int
    sampling_mode: str
    sequence_mode: str
    sequence_objective: str

    def __post_init__(self) -> None:
        _integer("batch_size", self.batch_size, 1)
        _integer("sequence_length", self.sequence_length, 1)
        _integer("min_transitions", self.min_transitions, 0)
        for name in ("sampling_mode", "sequence_mode", "sequence_objective"):
            _text(name, getattr(self, name))


ReadinessReason = Literal["ready", "warmup", "batch_unavailable", "window_unavailable", "capacity_window_impossible"]


@dataclass(frozen=True, slots=True)
class ReplayReadiness:
    ready: bool
    retained_transitions: int
    sampleable_units: int
    reason: ReadinessReason

    def __post_init__(self) -> None:
        _integer("retained_transitions", self.retained_transitions, 0)
        _integer("sampleable_units", self.sampleable_units, 0)
        if type(self.ready) is not bool or self.reason not in (
            "ready",
            "warmup",
            "batch_unavailable",
            "window_unavailable",
            "capacity_window_impossible",
        ):
            raise ValueError("ready/reason must describe a recognized readiness result")
        if self.ready != (self.reason == "ready") or (self.ready and self.sampleable_units == 0):
            raise ValueError("ready must agree with reason and a nonempty sampleable population")


@dataclass(frozen=True, slots=True)
class SamplingReceipt:
    """Ordered proposal evidence; weights are not renormalized by this DTO.

    Indices identify sampler units, not necessarily contiguous storage slots.
    Sampling laws and objective-specific weight validation belong to samplers.
    """

    indices: npt.NDArray[np.int64]
    weights: npt.NDArray[np.float64]
    population_size: int
    conditional_draw_probabilities: npt.NDArray[np.float64]
    mode: str
    objective_unit: str
    weight_rule: str

    def __post_init__(self) -> None:
        _integer("population_size", self.population_size, 1)
        for name in ("mode", "objective_unit", "weight_rule"):
            _text(name, getattr(self, name))
        size = None
        for name, dtype in (("indices", np.int64), ("weights", np.float64), ("conditional_draw_probabilities", np.float64)):
            value = getattr(self, name)
            if not isinstance(value, np.ndarray) or value.dtype != dtype or value.ndim != 1 or value.size == 0:
                raise ValueError(f"{name} must be a nonempty 1D ndarray[{np.dtype(dtype)}]")
            if size is not None and value.size != size:
                raise ValueError(f"{name} shape must match receipt indices")
            size = value.size
            if not np.isfinite(value).all() or (value < 0).any():
                raise ValueError(f"{name} must be finite and nonnegative")
            if name != "indices" and (value <= 0).any():
                raise ValueError(f"{name} must be positive")
            if name == "conditional_draw_probabilities" and (value > 1).any():
                raise ValueError("conditional_draw_probabilities must be <= 1")
            owned = value.copy()
            owned.setflags(write=False)
            object.__setattr__(self, name, owned)


@dataclass(frozen=True, slots=True)
class ReplayBatch:
    """Real rows are the prefix defined by lengths; loss_mask may select anchors.

    Optional reward components stay independent and never recompose rewards.
    Padded rows carry transport only and are not validated as experience.
    """

    legality_recorded: Tensor
    observations: Tensor
    actions: Tensor
    rewards: Tensor
    rewards_extrinsic: Tensor | None
    rewards_intrinsic: Tensor | None
    rewards_shaping: Tensor | None
    next_observations: Tensor
    dones: Tensor
    next_action_masks: Tensor
    loss_mask: Tensor
    lengths: Tensor
    unit_ids: Tensor
    weights: Tensor
    sampling: SamplingReceipt

    def __post_init__(self) -> None:
        obs = self.observations
        if not isinstance(obs, Tensor) or obs.ndim not in (2, 3) or any(d <= 0 for d in obs.shape):
            raise ValueError("observations shape must be nonempty [B,D] or [B,L,D]")
        shape, device = obs.shape[:-1], obs.device
        b, length = shape[0], shape[1] if obs.ndim == 3 else 1
        for name in ("lengths", "unit_ids", "weights"):
            value = getattr(self, name)
            if not isinstance(value, Tensor) or value.shape != (b,) or value.device != device:
                raise ValueError(f"{name} shape/device must be [B] on observations device")
            if name == "weights":
                if value.dtype != torch.float64 or not torch.isfinite(value).all() or (value <= 0).any():
                    raise ValueError("weights must be finite positive float64 values")
            elif value.dtype != torch.int64 or (value < (1 if name == "lengths" else 0)).any():
                raise ValueError(f"{name} must be int64 with valid nonnegative indices/positive lengths")
        if (self.lengths > length).any():
            raise ValueError("lengths exceed real transport capacity")
        real = torch.arange(length, device=device)[None, :] < self.lengths[:, None]
        if obs.ndim == 2:
            real = real[:, 0]
        for name in (
            "actions",
            "rewards",
            "rewards_extrinsic",
            "rewards_intrinsic",
            "rewards_shaping",
            "dones",
            "legality_recorded",
            "loss_mask",
        ):
            value = getattr(self, name)
            if value is None and name in ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"):
                continue
            if not isinstance(value, Tensor) or value.shape != shape or value.device != device:
                raise ValueError(f"{name} shape/device must match transition rows")
            expected = torch.bool
            if name == "actions":
                expected = torch.int64
            if name.startswith("rewards"):
                if value.dtype != torch.float32 or not torch.isfinite(value[real]).all():
                    raise ValueError(f"{name} must have finite real float32 values")
            elif value.dtype != expected:
                raise ValueError(f"{name} must have dtype {expected}")
        for name in ("observations", "next_observations"):
            value = getattr(self, name)
            if not isinstance(value, Tensor) or value.shape != obs.shape or value.device != device or value.dtype != obs.dtype:
                raise ValueError(f"{name} shape/dtype/device must match observations")
            if value.dtype != torch.float32 or not torch.isfinite(value[real]).all():
                raise ValueError(f"{name} must contain finite real float32 observations")
        masks = self.next_action_masks
        if not isinstance(masks, Tensor) or masks.ndim != len(shape) + 1 or masks.shape[:-1] != shape or masks.shape[-1] < 1:
            raise ValueError("next_action_masks shape must be [*transition_rows,A] with A>0")
        if masks.dtype != torch.bool or masks.device != device:
            raise ValueError("next_action_masks must be bool on observations device")
        if not self.legality_recorded[real].all():
            raise HistoricalLegalityUnavailable("unrecorded real successor legality: preserve in approved historical archive")
        if (self.loss_mask & ~real).any() or not self.loss_mask.reshape(b, -1).any(dim=1).all():
            raise ValueError("loss_mask must select real rows and at least one row per unit")
        if obs.ndim == 3 and (self.dones[:, :-1] & real[:, 1:]).any():
            raise ValueError("real recurrent rows cannot continue after a terminal")
        if ((self.actions[real] < 0) | (self.actions[real] >= masks.shape[-1])).any():
            raise ValueError("actions outside action vocabulary")
        validate_successor_masks(masks[real], self.dones[real], action_dim=masks.shape[-1])
        if not isinstance(self.sampling, SamplingReceipt) or len(self.sampling.indices) != b:
            raise ValueError("sampling receipt shape must match [B]")
        if not np.array_equal(self.weights.detach().cpu().numpy(), self.sampling.weights):
            raise ValueError("weights must agree with sampling receipt")
        object.__setattr__(self, "sampling", replace(self.sampling))
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, Tensor):
                object.__setattr__(self, field.name, value.detach().clone())
