"""Prioritized replay with matching estimators, stable handles and owned history.

Legacy sample/update addresses immediate physical slots on the external NumPy
stream. Qualified batches use persisted sampler configuration and monotonic
IDs scoped to this buffer/checkpoint history. Exact captured5 adapts to6 without
losing active legality; maskless4 remains isolated archival history.
"""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import torch

from townlet.training import historical_checkpoint as history
from townlet.training import per_sampling
from townlet.training.replay_contract import (
    HistoricalLegalityUnavailable,
    ReplayBatch,
    ReplayReadiness,
    ReplayRequest,
    SamplingReceipt,
    validate_successor_masks,
)

if TYPE_CHECKING:
    from townlet.training.state import RewardTensor

PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION = 6
PRIORITIZED_REPLAY_BUFFER_KIND = "prioritized"
_COMPONENTS = ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping")
_PRESENCE_FIELDS = tuple(f"{name}_present" for name in _COMPONENTS)
_PER_TENSOR_FIELDS = ("observations", "actions", "rewards", *_COMPONENTS, "next_observations", "dones")
_STORAGE_FIELDS = (*_PER_TENSOR_FIELDS, "next_action_masks", "legality_recorded", *_PRESENCE_FIELDS)
_LEGACY_STATE_KEYS = frozenset(
    {
        "replay_kind",
        "format_version",
        "capacity",
        "alpha",
        "beta",
        "beta_initial",
        "beta_annealing",
        "priorities",
        "max_priority",
        "position",
        "size_current",
        *_PER_TENSOR_FIELDS,
    }
)
_CAPTURED_STATE_KEYS = _LEGACY_STATE_KEYS | {
    "action_dim",
    "legality_mode",
    "historical_archives",
    "next_action_masks",
    "legality_recorded",
    *_PRESENCE_FIELDS,
}
PRIORITIZED_REPLAY_BUFFER_STATE_KEYS = _CAPTURED_STATE_KEYS | {
    "unit_ids",
    "next_unit_id",
    "sampling_mode",
    "sampling_origin",
    "sampling_objective_unit",
    "sampling_weight_rule",
    "sampling_rng",
}
_MAX_UNIT_COUNTER = 2**63 - 1
_BIT_GENERATORS: dict[str, type[np.random.BitGenerator]] = {
    "PCG64": np.random.PCG64,
    "PCG64DXSM": np.random.PCG64DXSM,
    "MT19937": np.random.MT19937,
    "Philox": np.random.Philox,
    "SFC64": np.random.SFC64,
}


@dataclass(frozen=True)
class _SamplerConfiguration:
    mode: str
    origin: str
    objective_unit: str
    weight_rule: str
    rng: np.random.Generator | None


@dataclass(frozen=True, slots=True)
class PrioritizedReplayBatch(ReplayBatch):
    """Optional reward values are recorded exactly where presence is true."""

    rewards_extrinsic_present: torch.Tensor
    rewards_intrinsic_present: torch.Tensor
    rewards_shaping_present: torch.Tensor

    def __post_init__(self) -> None:
        ReplayBatch.__post_init__(self)
        if self.observations.ndim != 2:
            raise ValueError("prioritized batches contain flat transition rows")
        for name in _COMPONENTS:
            present, value = getattr(self, f"{name}_present"), getattr(self, name)
            if not isinstance(present, torch.Tensor) or present.dtype != torch.bool:
                raise ValueError(f"{name}_present must be a bool tensor")
            if present.shape != self.rewards.shape or present.device != self.rewards.device:
                raise ValueError(f"{name}_present must match reward rows and device")
            if value is None:
                if bool(present.any()):
                    raise ValueError(f"{name} cannot omit recorded component values")
            elif not bool(present.any()) or bool((value[~present] != 0).any()):
                raise ValueError(f"{name} must use None when absent and zero placeholders where unrecorded")
            object.__setattr__(self, f"{name}_present", present.detach().clone())


@dataclass(frozen=True)
class _PrioritizedRows:
    observations: torch.Tensor | None
    actions: torch.Tensor | None
    rewards: torch.Tensor | None
    rewards_extrinsic: torch.Tensor | None
    rewards_intrinsic: torch.Tensor | None
    rewards_shaping: torch.Tensor | None
    next_observations: torch.Tensor | None
    dones: torch.Tensor | None
    next_action_masks: torch.Tensor | None
    legality_recorded: torch.Tensor | None
    rewards_extrinsic_present: torch.Tensor | None
    rewards_intrinsic_present: torch.Tensor | None
    rewards_shaping_present: torch.Tensor | None


@dataclass(frozen=True)
class _ValidatedPrioritizedState(_PrioritizedRows):
    beta: float
    priorities: np.ndarray
    max_priority: float
    position: int
    size_current: int
    obs_dim: int | None
    action_dim: int | None
    legality_mode: str
    archives: tuple[history.HistoricalReplayArchive, ...]
    legacy_state: Mapping[str, Any] | None
    unit_ids: np.ndarray
    next_unit_id: int
    sampler: _SamplerConfiguration


@dataclass(frozen=True)
class _PrioritizedRestoreCandidate(_PrioritizedRows):
    beta: float
    priorities: np.ndarray
    max_priority: float
    position: int
    size_current: int
    action_dim: int | None
    legality_mode: str
    archives: tuple[history.HistoricalReplayArchive, ...]
    unit_ids: np.ndarray
    next_unit_id: int
    sampler: _SamplerConfiguration


class PrioritizedReplayBuffer:
    """Physical ring storage; archival priorities cannot address active rows."""

    def __init__(self, capacity: int, alpha: float, beta: float, beta_annealing: bool, device: torch.device):
        self.capacity, self.alpha, self.beta = capacity, alpha, beta
        self.beta_initial, self.beta_annealing, self.device = beta, beta_annealing, device
        self.observations: torch.Tensor | None = None
        self.actions: torch.Tensor | None = None
        self.rewards: torch.Tensor | None = None
        self.rewards_extrinsic: torch.Tensor | None = None
        self.rewards_intrinsic: torch.Tensor | None = None
        self.rewards_shaping: torch.Tensor | None = None
        self.next_observations: torch.Tensor | None = None
        self.dones: torch.Tensor | None = None
        self.next_action_masks: torch.Tensor | None = None
        self.legality_recorded: torch.Tensor | None = None
        self.rewards_extrinsic_present: torch.Tensor | None = None
        self.rewards_intrinsic_present: torch.Tensor | None = None
        self.rewards_shaping_present: torch.Tensor | None = None
        self.action_dim: int | None = None
        self.legality_mode = "unconstrained"
        self._historical_archives: tuple[history.HistoricalReplayArchive, ...] = ()
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.max_priority = 1.0
        self.position = self.size_current = 0
        self.unit_ids = np.full(capacity, -1, dtype=np.int64)
        self.next_unit_id = 0
        self._id_to_slot: dict[int, int] = {}
        self._sampler = self._external_sampler("legacy-constructor")

    @staticmethod
    def _external_sampler(origin: str) -> _SamplerConfiguration:
        mode = per_sampling.SUCCESSIVE
        return _SamplerConfiguration(mode, origin, "transition", per_sampling.WEIGHT_RULES[mode], None)

    def configure_sampling(self, *, sampling_mode: str, rng: np.random.Generator, origin: str) -> None:
        """Own an explicit configured Generator without advancing the caller's RNG."""
        if not isinstance(rng, np.random.Generator):
            raise ValueError("PER configure_sampling requires an explicit numpy.random.Generator")
        state = {
            "sampling_mode": sampling_mode,
            "sampling_origin": origin,
            "sampling_objective_unit": "transition",
            "sampling_weight_rule": per_sampling.WEIGHT_RULES.get(sampling_mode) if isinstance(sampling_mode, str) else None,
            "sampling_rng": {
                "ownership": "owned_numpy_generator",
                "bit_generator": type(rng.bit_generator).__name__,
                "state": copy.deepcopy(rng.bit_generator.state),
            },
        }
        sampler = self._validate_sampler(state)
        self._sampler = sampler

    @staticmethod
    def _closed_mapping(value: object, keys: tuple[str, ...], field: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping) or set(value) != set(keys):
            raise ValueError(f"PER {field} has an invalid closed key set")
        return value

    @classmethod
    def _restore_generator(cls, kind: str, raw: object) -> np.random.Generator:
        """Validate known engine state, then install it on an off-side engine."""
        if type(kind) is not str or kind not in _BIT_GENERATORS:
            raise ValueError("PER sampling_rng bit_generator kind is unsupported")
        keys: tuple[str, ...]
        if kind == "MT19937":
            keys = ("bit_generator", "state")
        elif kind == "Philox":
            keys = ("bit_generator", "state", "buffer", "buffer_pos", "has_uint32", "uinteger")
        else:
            keys = ("bit_generator", "state", "has_uint32", "uinteger")
        state = cls._closed_mapping(raw, keys, "sampling_rng.state")
        if type(state["bit_generator"]) is not str or state["bit_generator"] != kind:
            raise ValueError("PER sampling_rng engine kind disagrees with its state")

        def array(value: object, dtype: np.dtype, shape: tuple[int, ...], field: str) -> None:
            if not isinstance(value, np.ndarray) or value.dtype != dtype or value.shape != shape:
                raise ValueError(f"PER sampling_rng {field} dtype/shape is invalid")

        if kind in ("PCG64", "PCG64DXSM"):
            nested = cls._closed_mapping(state["state"], ("state", "inc"), "sampling_rng.state.state")
            cls._require_int(nested["state"], "sampling_rng.state.state.state", minimum=0, maximum=2**128 - 1)
            increment = cls._require_int(nested["inc"], "sampling_rng.state.state.inc", minimum=1, maximum=2**128 - 1)
            if increment % 2 != 1:
                raise ValueError("PER sampling_rng PCG increment must be odd")
        elif kind == "MT19937":
            nested = cls._closed_mapping(state["state"], ("key", "pos"), "sampling_rng.state.state")
            array(nested["key"], np.dtype(np.uint32), (624,), "MT19937 key")
            if not np.any(nested["key"]):
                raise ValueError("PER sampling_rng MT19937 key cannot be all zero")
            cls._require_int(nested["pos"], "sampling_rng.state.state.pos", minimum=0, maximum=624)
        elif kind == "Philox":
            nested = cls._closed_mapping(state["state"], ("counter", "key"), "sampling_rng.state.state")
            array(nested["counter"], np.dtype(np.uint64), (4,), "Philox counter")
            array(nested["key"], np.dtype(np.uint64), (2,), "Philox key")
            array(state["buffer"], np.dtype(np.uint64), (4,), "Philox buffer")
            cls._require_int(state["buffer_pos"], "sampling_rng.state.buffer_pos", minimum=0, maximum=4)
        else:
            nested = cls._closed_mapping(state["state"], ("state",), "sampling_rng.state.state")
            array(nested["state"], np.dtype(np.uint64), (4,), "SFC64 state")
        if kind != "MT19937":
            cls._require_int(state["has_uint32"], "sampling_rng.state.has_uint32", minimum=0, maximum=1)
            cls._require_int(state["uinteger"], "sampling_rng.state.uinteger", minimum=0, maximum=2**32 - 1)
        # Zero is an explicit restore-only placeholder, immediately replaced by
        # the complete validated saved state. No draw uses this placeholder.
        engine = _BIT_GENERATORS[kind](0)
        try:
            engine.state = copy.deepcopy(dict(state))
        except (ValueError, TypeError, OverflowError) as error:
            raise ValueError(f"PER sampling_rng {kind} state is invalid") from error
        return np.random.Generator(engine)

    @classmethod
    def _validate_sampler(cls, state: Mapping[str, Any]) -> _SamplerConfiguration:
        mode, origin = state["sampling_mode"], state["sampling_origin"]
        if type(mode) is not str or mode not in per_sampling.WEIGHT_RULES:
            raise ValueError("PER sampling_mode is unsupported")
        if type(origin) is not str or origin not in ("authored", "bac-options-v1", "legacy-constructor", "captured5-physical-slot-adapter"):
            raise ValueError("PER sampling_origin is unsupported")
        if type(state["sampling_objective_unit"]) is not str or state["sampling_objective_unit"] != "transition":
            raise ValueError("PER sampling_objective_unit must be transition")
        if type(state["sampling_weight_rule"]) is not str or state["sampling_weight_rule"] != per_sampling.WEIGHT_RULES[mode]:
            raise ValueError("PER sampling_weight_rule contradicts sampling_mode")
        descriptor = cls._closed_mapping(state["sampling_rng"], ("ownership", "bit_generator", "state"), "sampling_rng")
        ownership = descriptor["ownership"]
        if type(ownership) is not str:
            raise ValueError("PER sampling_rng ownership must be a string")
        if ownership == "numpy_global_legacy":
            if (
                mode != per_sampling.SUCCESSIVE
                or origin not in ("legacy-constructor", "captured5-physical-slot-adapter")
                or descriptor["bit_generator"] is not None
                or descriptor["state"] is not None
            ):
                raise ValueError("PER external-global sampler ownership/configuration contradicts its metadata")
            rng = None
        elif ownership == "owned_numpy_generator":
            if origin not in ("authored", "bac-options-v1"):
                raise ValueError("PER owned Generator requires authored or bac-options-v1 origin")
            rng = cls._restore_generator(descriptor["bit_generator"], descriptor["state"])
        else:
            raise ValueError("PER sampling_rng ownership is unsupported")
        return _SamplerConfiguration(mode, origin, "transition", per_sampling.WEIGHT_RULES[mode], rng)

    @staticmethod
    def _sampler_metadata(sampler: _SamplerConfiguration) -> dict[str, Any]:
        descriptor: dict[str, Any] = {"ownership": "numpy_global_legacy", "bit_generator": None, "state": None}
        if sampler.rng is not None:
            descriptor = {
                "ownership": "owned_numpy_generator",
                "bit_generator": type(sampler.rng.bit_generator).__name__,
                "state": copy.deepcopy(sampler.rng.bit_generator.state),
            }
        return {
            "sampling_mode": sampler.mode,
            "sampling_origin": sampler.origin,
            "sampling_objective_unit": sampler.objective_unit,
            "sampling_weight_rule": sampler.weight_rule,
            "sampling_rng": descriptor,
        }

    @classmethod
    def _clone_sampler(cls, sampler: _SamplerConfiguration) -> _SamplerConfiguration:
        return cls._validate_sampler(cls._sampler_metadata(sampler))

    @property
    def retained_transitions(self) -> int:
        return self.size_current

    @property
    def historical_archives(self) -> tuple[history.HistoricalReplayArchive, ...]:
        return tuple(self._own_archive(archive) for archive in self._historical_archives)

    @staticmethod
    def _own_archive(archive: history.HistoricalReplayArchive) -> history.HistoricalReplayArchive:
        if not isinstance(archive, history.HistoricalReplayArchive):
            raise ValueError("historical archive must be a HistoricalReplayArchive")
        owned = history._archive_from_state(history._record(archive))
        if owned.source_formats["replay_kind"] != PRIORITIZED_REPLAY_BUFFER_KIND:
            raise ValueError("historical archive replay kind differs from prioritized storage")
        # Preserve stricter PER4 cross-field validation as well as archive digest validation.
        state = owned.original_state
        capacity = PrioritizedReplayBuffer._require_int(state["capacity"], "capacity", minimum=1, maximum=2**63 - 1)
        alpha = PrioritizedReplayBuffer._require_float(state["alpha"], "alpha", minimum=0.0, maximum=1.0)
        beta_initial = PrioritizedReplayBuffer._require_float(state["beta_initial"], "beta_initial", minimum=0.0, maximum=1.0)
        annealing = state["beta_annealing"]
        assert isinstance(annealing, bool)  # The owned archive validated this exact type.
        validator = PrioritizedReplayBuffer(capacity, alpha, beta_initial, annealing, torch.device("cpu"))
        validator.validate_serialized(state, expected_obs_dim=None)
        return owned

    def _merge_archives(self, incoming: tuple[history.HistoricalReplayArchive, ...]) -> tuple[history.HistoricalReplayArchive, ...]:
        result = []
        seen = set()
        for archive in (*self._historical_archives, *incoming):
            owned = self._own_archive(archive)
            if owned.source_digest not in seen:
                seen.add(owned.source_digest)
                result.append(owned)
        return tuple(result)

    def install_historical_archive(self, archive: history.HistoricalReplayArchive) -> None:
        archives = self._merge_archives((archive,))
        self._historical_archives = archives

    def _validate_push(
        self,
        observations: torch.Tensor,
        actions: torch.Tensor,
        rewards: RewardTensor,
        next_observations: torch.Tensor,
        dones: torch.Tensor,
    ) -> int:
        if observations.ndim != 2 or observations.dtype != torch.float32 or observations.shape[1] < 1:
            raise ValueError("observations must be 2D with dtype torch.float32 and positive observation width")
        if next_observations.ndim != 2 or next_observations.dtype != torch.float32:
            raise ValueError("next_observations must be 2D with dtype torch.float32")
        if actions.ndim != 1 or actions.dtype != torch.int64:
            raise ValueError("actions must be 1D with dtype torch.int64")
        if rewards.total.ndim != 1 or rewards.total.dtype != torch.float32:
            raise ValueError("rewards.total must be 1D with dtype torch.float32")
        if dones.ndim != 1 or dones.dtype != torch.bool:
            raise ValueError("dones must be 1D with dtype torch.bool")
        batch_size, obs_dim = observations.shape
        if batch_size > self.capacity:
            raise ValueError(f"batch_size ({batch_size}) exceeds buffer capacity ({self.capacity})")
        if actions.shape[0] != batch_size or rewards.total.shape[0] != batch_size or dones.shape[0] != batch_size:
            raise ValueError("PER transition batch tensors must have the same leading dimension.")
        if next_observations.shape != observations.shape:
            raise ValueError(
                f"next_observations shape {tuple(next_observations.shape)} must equal observations shape {tuple(observations.shape)}"
            )
        if self.observations is not None and obs_dim != self.observations.shape[1]:
            raise ValueError(f"observations obs_dim ({obs_dim}) != current buffer obs_dim ({self.observations.shape[1]})")
        if bool((actions < 0).any()):
            raise ValueError("actions must be nonnegative")
        for name, value in (
            ("observations", observations),
            ("next_observations", next_observations),
            ("rewards.total", rewards.total),
            ("rewards.extrinsic", rewards.extrinsic),
            ("rewards.intrinsic", rewards.intrinsic),
            ("rewards.shaping", rewards.shaping),
        ):
            if value is None:
                continue
            if name.startswith("rewards.") and (value.shape != (batch_size,) or value.dtype != torch.float32):
                raise ValueError(f"{name} must have shape ({batch_size},) and dtype torch.float32")
            if not bool(torch.isfinite(value).all()):
                raise ValueError(f"{name} must contain only finite values")
        return batch_size

    def push(
        self, observations: torch.Tensor, actions: torch.Tensor, rewards: RewardTensor, next_observations: torch.Tensor, dones: torch.Tensor
    ) -> None:
        """Retain the explicitly unconstrained public adapter and legacy sample."""
        masks = None
        if self.action_dim is not None:
            masks = torch.ones((*dones.shape, self.action_dim), dtype=torch.bool, device=dones.device)
        self._push(observations, actions, rewards, next_observations, dones, masks)

    def push_recorded(
        self,
        observations: torch.Tensor,
        actions: torch.Tensor,
        rewards: RewardTensor,
        next_observations: torch.Tensor,
        dones: torch.Tensor,
        next_action_masks: torch.Tensor,
    ) -> None:
        if not isinstance(next_action_masks, torch.Tensor) or next_action_masks.ndim != 2:
            raise ValueError("next_action_masks must be a bool tensor of shape [batch, action_dim]")
        validate_successor_masks(next_action_masks, dones, action_dim=next_action_masks.shape[1])
        self._push(observations, actions, rewards, next_observations, dones, next_action_masks)

    def declare_unconstrained_action_dim(self, *, action_dim: int) -> None:
        """Explicitly declare all actions legal for existing unconstrained live rows."""
        self._require_int(action_dim, "action_dim", minimum=1, maximum=2**63 - 1)
        if self.action_dim is not None:
            if self.action_dim != action_dim:
                raise ValueError("action_dim differs from current buffer vocabulary")
            return
        if self.actions is not None and bool((self.actions[: self.size_current] >= action_dim).any()):
            raise ValueError("existing unconstrained actions exceed the supplied action vocabulary")
        masks = torch.ones((self.capacity, action_dim), dtype=torch.bool, device=self.device)
        recorded = torch.zeros(self.capacity, dtype=torch.bool, device=self.device)
        recorded[: self.size_current].fill_(True)
        self.next_action_masks, self.legality_recorded = masks, recorded
        self.action_dim, self.legality_mode = action_dim, "recorded"

    @staticmethod
    def _insertion_priority(maximum: float) -> np.float32:
        """Validate the actual storage conversion, without changing saved metadata."""
        if not math.isfinite(maximum) or maximum <= 0:
            raise ValueError("PER max_priority must be finite and positive for insertion")
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            priority = np.float32(maximum)
        if not np.isfinite(priority) or priority <= 0:
            raise ValueError("PER max_priority must convert to a positive finite float32 insertion priority")
        return priority

    def _push(self, observations, actions, rewards, next_observations, dones, masks) -> None:
        batch_size = self._validate_push(observations, actions, rewards, next_observations, dones)
        action_dim = self.action_dim
        if masks is not None:
            validate_successor_masks(masks, dones, action_dim=masks.shape[1])
            if action_dim is not None and masks.shape[1] != action_dim:
                raise ValueError("successor action width differs from current buffer action vocabulary")
            action_dim = masks.shape[1]
            if bool((actions >= action_dim).any()):
                raise ValueError("actions outside the declared action vocabulary")
            if self.actions is not None and bool((self.actions[: self.size_current] >= action_dim).any()):
                raise ValueError("existing unconstrained actions exceed the supplied action vocabulary")
        if not batch_size:
            return
        if self.next_unit_id > _MAX_UNIT_COUNTER - batch_size:
            raise OverflowError("PER unit ID counter exhausted before insertion")
        insertion_priority = self._insertion_priority(self.max_priority)
        values = {
            "observations": observations,
            "actions": actions,
            "rewards": rewards.total,
            "next_observations": next_observations,
            "dones": dones,
        }
        for name, value in zip(_COMPONENTS, (rewards.extrinsic, rewards.intrinsic, rewards.shaping), strict=True):
            if value is None:
                values[name] = torch.zeros_like(rewards.total)
            else:
                values[name] = value
            values[f"{name}_present"] = torch.full((batch_size,), value is not None, dtype=torch.bool, device=rewards.total.device)
        values["legality_recorded"] = torch.full((batch_size,), masks is not None, dtype=torch.bool, device=dones.device)
        if masks is not None:
            values["next_action_masks"] = masks
        moved = {name: value.detach().to(self.device).clone() for name, value in values.items()}
        storage = {name: getattr(self, name) for name in _STORAGE_FIELDS}
        for name, value in moved.items():
            if storage[name] is None:
                storage[name] = torch.zeros((self.capacity, *value.shape[1:]), dtype=value.dtype, device=self.device)
        physical = (np.arange(batch_size, dtype=np.int64) + self.position) % self.capacity
        indices = torch.from_numpy(physical.copy()).to(self.device)
        priorities, unit_ids = self.priorities.copy(), self.unit_ids.copy()
        priorities[physical] = insertion_priority
        unit_ids[physical] = np.arange(self.next_unit_id, self.next_unit_id + batch_size, dtype=np.int64)
        size = min(self.size_current + batch_size, self.capacity)
        # A valid Python maximum may round upward when stored. Preserve it at
        # restore, then cover all actual committed priorities after insertion.
        maximum = max(self.max_priority, float(priorities[:size].max()))
        reverse = self._id_to_slot.copy()
        for slot in physical:
            previous = int(self.unit_ids[slot])
            if previous >= 0:
                reverse.pop(previous)
            reverse[int(unit_ids[slot])] = int(slot)
        if action_dim is not None and self.action_dim is None and self.size_current:
            storage["next_action_masks"][: self.size_current].fill_(True)
            storage["legality_recorded"][: self.size_current].fill_(True)
        for name, value in moved.items():
            storage[name][indices] = value
        for name, value in storage.items():
            setattr(self, name, value)
        self.priorities, self.unit_ids, self._id_to_slot = priorities, unit_ids, reverse
        self.max_priority = maximum
        self.next_unit_id += batch_size
        self.position = (self.position + batch_size) % self.capacity
        self.size_current = size
        self.action_dim = action_dim
        if action_dim is None:
            self.legality_mode = "unconstrained"
        else:
            self.legality_mode = "recorded"

    def _draw(self, batch_size: int) -> SamplingReceipt:
        return per_sampling.sample_legacy_units(
            self.priorities[: self.size_current].astype(np.float64), alpha=self.alpha, beta=self.beta, batch_size=batch_size
        )

    def sample(self, batch_size: int) -> dict:
        """Global NumPy successive sampling with physical indices and float32 weights."""
        if (
            not isinstance(batch_size, (bool, np.bool_))
            and isinstance(batch_size, (int, np.integer))
            and batch_size > 0
            and self.size_current < batch_size
        ):
            raise ValueError(f"Buffer size ({self.size_current}) < batch_size ({batch_size})")
        receipt = per_sampling.sample_legacy_float32_units(
            self.priorities[: self.size_current].astype(np.float64), alpha=self.alpha, beta=self.beta, batch_size=batch_size
        )
        indices = receipt.indices.copy()
        # Retain the existing dictionary dtype without silently overflowing a
        # mathematically valid float64 correction at this narrower boundary.
        with np.errstate(over="ignore", under="ignore"):
            weights = receipt.weights.astype(np.float32)
        if not np.isfinite(weights).all() or np.any(weights <= 0):
            position = int(np.flatnonzero(~np.isfinite(weights) | (weights <= 0))[0])
            raise ValueError(f"PER legacy sample weight at physical index {indices[position]} is not positive finite representable float32")
        selected = torch.tensor(indices, dtype=torch.long, device=self.device)
        result = {name: getattr(self, name)[selected] for name in ("observations", "actions", "rewards", "next_observations", "dones")}
        result.update(weights=torch.tensor(weights, dtype=torch.float32, device=self.device), indices=indices)
        if self.next_action_masks is not None:
            assert self.legality_recorded is not None
            result["next_action_masks"] = self.next_action_masks[selected]
            result["legality_recorded"] = self.legality_recorded[selected]
        return result

    def _check_request(self, request: ReplayRequest) -> None:
        if not isinstance(request, ReplayRequest) or (
            request.sequence_mode,
            request.sequence_objective,
            request.sequence_length,
        ) != ("feedforward", "transition", 1):
            raise ValueError("prioritized replay supports flat transition requests")
        if request.sampling_mode != self._sampler.mode:
            raise ValueError("PER request sampling_mode differs from configured mode; use configure_sampling explicitly")

    def readiness(self, request: ReplayRequest) -> ReplayReadiness:
        self._check_request(request)
        qualified = (
            self.action_dim is not None and self.legality_recorded is not None and bool(self.legality_recorded[: self.size_current].all())
        )
        if qualified:
            sampleable = self.size_current
        else:
            sampleable = 0
        if self.size_current < request.min_transitions:
            return ReplayReadiness(False, self.size_current, sampleable, "warmup")
        if not sampleable or (request.sampling_mode == per_sampling.SUCCESSIVE and sampleable < request.batch_size):
            return ReplayReadiness(False, self.size_current, sampleable, "batch_unavailable")
        return ReplayReadiness(True, self.size_current, sampleable, "ready")

    def sample_batch(self, request: ReplayRequest) -> PrioritizedReplayBatch:
        ready = self.readiness(request)
        if not ready.ready:
            raise ValueError(
                f"prioritized replay unavailable: {ready.reason}; "
                f"retained={ready.retained_transitions}, sampleable={ready.sampleable_units}"
            )
        if self._sampler.rng is None:
            receipt = self._draw(request.batch_size)
        else:
            receipt = per_sampling.sample_units(
                self.priorities[: self.size_current].astype(np.float64),
                alpha=self.alpha,
                beta=self.beta,
                batch_size=request.batch_size,
                mode=self._sampler.mode,
                rng=self._sampler.rng,
            )
        indices, weights = receipt.indices, receipt.weights
        selected = torch.tensor(indices, dtype=torch.int64, device=self.device)
        components: dict[str, Any] = {}
        for name in _COMPONENTS:
            present = getattr(self, f"{name}_present")[selected]
            if bool(present.any()):
                components[name] = getattr(self, name)[selected]
            else:
                components[name] = None
            components[f"{name}_present"] = present
        return PrioritizedReplayBatch(
            **{
                name: getattr(self, name)[selected]
                for name in ("observations", "actions", "rewards", "next_observations", "dones", "next_action_masks", "legality_recorded")
            },
            loss_mask=torch.ones(request.batch_size, dtype=torch.bool, device=self.device),
            lengths=torch.ones(request.batch_size, dtype=torch.int64, device=self.device),
            unit_ids=torch.from_numpy(self.unit_ids[indices].copy()).to(self.device),
            weights=torch.from_numpy(weights.copy()).to(self.device),
            sampling=receipt,
            **components,
        )

    def update_priorities(self, indices: np.ndarray, td_errors: torch.Tensor) -> None:
        """Update immediate physical slots; durable callers use stable unit IDs."""
        priorities, maximum = self._prepare_priority_update(indices, td_errors, stable=False)
        self.priorities, self.max_priority = priorities, maximum

    def update_unit_priorities(self, unit_ids: np.ndarray, td_errors: torch.Tensor) -> None:
        """Reject retired IDs rather than updating a new occupant of their slot."""
        priorities, maximum = self._prepare_priority_update(unit_ids, td_errors, stable=True)
        self.priorities, self.max_priority = priorities, maximum

    def _prepare_priority_update(self, indices: np.ndarray, td_errors: torch.Tensor, *, stable: bool) -> tuple[np.ndarray, float]:
        if stable:
            field = "unit_ids"
        else:
            field = "indices"
        if not isinstance(indices, np.ndarray) or indices.ndim != 1 or indices.dtype.kind not in "iu":
            raise ValueError(f"PER {field} must be a one-dimensional integer array")
        if stable and indices.dtype != np.int64:
            raise ValueError("PER unit_ids must have dtype int64")
        if not isinstance(td_errors, torch.Tensor) or td_errors.ndim != 1 or td_errors.shape != indices.shape or td_errors.is_complex():
            raise ValueError(f"PER td_errors shape/length must match {field} and contain real values")
        values = td_errors.detach().to(device="cpu", dtype=torch.float64).numpy()
        if not np.isfinite(values).all():
            position = int(np.flatnonzero(~np.isfinite(values))[0])
            raise ValueError(f"PER td_errors at {field}[{position}]={indices[position]} is not finite")
        slots = []
        for position, raw in enumerate(indices):
            index = int(raw)
            if stable:
                if index not in self._id_to_slot:
                    raise ValueError(f"PER stale or unknown unit ID {index} at unit_ids[{position}]")
                slots.append(self._id_to_slot[index])
            else:
                if not 0 <= index < self.size_current:
                    raise ValueError(f"PER indices[{position}]={index} is outside the active physical slots")
                slots.append(index)
        with np.errstate(over="ignore", invalid="ignore"):
            candidates = (np.abs(values) + 1e-6).astype(np.float32)
        invalid = np.flatnonzero(~np.isfinite(candidates) | (candidates <= 0))
        if invalid.size:
            position = int(invalid[0])
            raise ValueError(f"PER priority at {field}[{position}]={indices[position]} is not positive finite representable float32")
        reduced: dict[int, float] = {}
        for slot, priority in zip(slots, candidates, strict=True):
            if slot in reduced:
                reduced[slot] = max(reduced[slot], float(priority))
            else:
                reduced[slot] = float(priority)
        priorities = self.priorities.copy()
        for slot, priority in reduced.items():
            priorities[slot] = priority
        maximum = self.max_priority
        if reduced:
            maximum = max(maximum, max(reduced.values()))
        return priorities, maximum

    def anneal_beta(self, total_steps: int, current_step: int) -> None:
        if self.beta_annealing:
            if total_steps <= 0:
                return
            progress = min(current_step / total_steps, 1.0)
            self.beta = self.beta_initial + (1.0 - self.beta_initial) * progress

    def size(self) -> int:
        return self.size_current

    def __len__(self) -> int:
        return self.size_current

    def clear(self) -> None:
        """Clear active storage, keeping archives and the current annealed beta."""
        priorities = np.zeros(self.capacity, dtype=np.float32)
        unit_ids = np.full(self.capacity, -1, dtype=np.int64)
        reverse: dict[int, int] = {}
        self.size_current = self.position = 0
        for name in _STORAGE_FIELDS:
            setattr(self, name, None)
        self.action_dim, self.legality_mode = None, "unconstrained"
        self.priorities, self.unit_ids, self._id_to_slot = priorities, unit_ids, reverse
        self.max_priority = 1.0

    def stats(self) -> dict[str, Any]:
        memory_bytes = sum(value.numel() * value.element_size() for name in _STORAGE_FIELDS if (value := getattr(self, name)) is not None)
        # Retain the old empty/unallocated memory report; allocated arrays include priorities.
        if self.observations is not None:
            memory_bytes += self.priorities.nbytes
        return {
            "size": self.size_current,
            "capacity": self.capacity,
            "occupancy_ratio": self.size_current / self.capacity if self.capacity > 0 else 0.0,
            "memory_bytes": memory_bytes,
            "device": str(self.device),
        }

    def serialize(self) -> dict:
        """Keep physical ring rows aligned with capacity-length priorities and position."""
        empty = self.size_current == 0
        state = {
            "replay_kind": PRIORITIZED_REPLAY_BUFFER_KIND,
            "format_version": PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION,
            "capacity": self.capacity,
            "alpha": self.alpha,
            "beta": self.beta,
            "beta_initial": self.beta_initial,
            "beta_annealing": self.beta_annealing,
            "priorities": self.priorities.copy(),
            "max_priority": self.max_priority,
            "position": self.position,
            "size_current": self.size_current,
            "action_dim": None if empty else self.action_dim,
            "legality_mode": "unconstrained" if empty else self.legality_mode,
            "historical_archives": [history._record(archive) for archive in self._historical_archives],
            "unit_ids": self.unit_ids.copy(),
            "next_unit_id": self.next_unit_id,
            **self._sampler_metadata(self._sampler),
        }
        for name in _STORAGE_FIELDS:
            value = getattr(self, name)
            if empty or value is None:
                state[name] = None
            else:
                state[name] = value[: self.size_current].detach().cpu().clone()
        for name in _COMPONENTS:
            present = state[f"{name}_present"]
            if present is not None:
                assert isinstance(present, torch.Tensor)
                if not bool(present.any()):
                    state[name] = None
        return state

    @staticmethod
    def _require_int(value: object, field: str, *, minimum: int, maximum: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"PER checkpoint {field} must be an integer; got {value!r}. Regenerate the checkpoint.")
        if not minimum <= value <= maximum:
            raise ValueError(f"PER checkpoint {field}={value} is outside [{minimum}, {maximum}]. Regenerate the checkpoint.")
        return value

    @staticmethod
    def _require_float(value: object, field: str, *, minimum: float, maximum: float) -> float:
        if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(float(value)):
            raise ValueError(f"PER checkpoint {field} must be a finite number; got {value!r}. Regenerate the checkpoint.")
        result = float(value)
        if not minimum <= result <= maximum:
            raise ValueError(f"PER checkpoint {field}={result} is outside [{minimum}, {maximum}]. Regenerate the checkpoint.")
        return result

    @staticmethod
    def _require_tensor(state: Mapping[str, Any], field: str, *, dtype: torch.dtype, shape: tuple[int, ...]) -> torch.Tensor:
        value = state[field]
        if not isinstance(value, torch.Tensor):
            raise ValueError(f"PER checkpoint {field} must be a tensor; got {type(value).__name__}. Regenerate the checkpoint.")
        if value.dtype is not dtype:
            raise ValueError(f"PER checkpoint {field} dtype is {value.dtype}; expected {dtype}. Regenerate the checkpoint.")
        if tuple(value.shape) != shape:
            raise ValueError(f"PER checkpoint {field} shape is {tuple(value.shape)}; expected {shape}. Regenerate the checkpoint.")
        if dtype.is_floating_point and not bool(torch.isfinite(value).all()):
            raise ValueError(f"PER checkpoint {field} must contain only finite values. Regenerate the checkpoint.")
        return value.detach().clone()

    @classmethod
    def _validate_identity(cls, state: Mapping[str, Any], capacity: int, size: int) -> tuple[np.ndarray, int]:
        unit_ids = state["unit_ids"]
        if not isinstance(unit_ids, np.ndarray) or unit_ids.dtype != np.int64 or unit_ids.shape != (capacity,):
            raise ValueError("PER unit_ids must be a capacity-length int64 array")
        counter = cls._require_int(state["next_unit_id"], "next_unit_id", minimum=0, maximum=_MAX_UNIT_COUNTER)
        live = unit_ids[:size]
        if np.any(live < 0) or np.any(live >= counter) or len(np.unique(live)) != size:
            raise ValueError("PER live unit_ids must be unique nonnegative IDs strictly below next_unit_id")
        if np.any(unit_ids[size:] != -1):
            raise ValueError("PER inactive unit_ids must use -1")
        return unit_ids.copy(), counter

    def _validate_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _ValidatedPrioritizedState:
        if not isinstance(state, Mapping):
            raise ValueError(f"Prioritized replay checkpoint payload must be a mapping; got {type(state).__name__}.")
        version = state.get("format_version")
        if type(version) is not int or version not in (4, 5, PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION):
            raise ValueError(f"Cannot load PER checkpoint with format_version {version!r}; supported format_version values are 4, 5 and 6.")
        legacy = version == 4
        if legacy:
            expected_keys = _LEGACY_STATE_KEYS
        elif version == 5:
            expected_keys = _CAPTURED_STATE_KEYS
        else:
            expected_keys = PRIORITIZED_REPLAY_BUFFER_STATE_KEYS
        if state.get("replay_kind") != PRIORITIZED_REPLAY_BUFFER_KIND:
            raise ValueError(
                f"PER checkpoint replay_kind is {state.get('replay_kind')!r}; expected 'prioritized'. Regenerate the checkpoint."
            )
        if set(state) != expected_keys:
            raise ValueError(
                f"PER checkpoint key set mismatch: missing={sorted(expected_keys - set(state))}, "
                f"unknown={sorted(set(state) - expected_keys)}. Regenerate the checkpoint."
            )
        capacity = self._require_int(state["capacity"], "capacity", minimum=1, maximum=2**63 - 1)
        if capacity != self.capacity:
            raise ValueError(
                f"PER checkpoint capacity is {capacity}; current capacity is {self.capacity}. "
                "Regenerate the checkpoint for this configuration."
            )
        alpha = self._require_float(state["alpha"], "alpha", minimum=0.0, maximum=1.0)
        if alpha != self.alpha:
            raise ValueError(f"PER checkpoint alpha is {alpha}; current alpha is {self.alpha}. Regenerate the checkpoint.")
        initial = self._require_float(state["beta_initial"], "beta_initial", minimum=0.0, maximum=1.0)
        if initial != self.beta_initial:
            raise ValueError(
                f"PER checkpoint beta_initial is {initial}; current beta_initial is {self.beta_initial}. Regenerate the checkpoint."
            )
        annealing = state["beta_annealing"]
        if type(annealing) is not bool:
            raise ValueError("PER checkpoint beta_annealing must be a boolean. Regenerate the checkpoint.")
        if annealing != self.beta_annealing:
            raise ValueError(
                f"PER checkpoint beta_annealing is {annealing}; current beta_annealing is {self.beta_annealing}. Regenerate the checkpoint."
            )
        beta = self._require_float(state["beta"], "beta", minimum=initial, maximum=1.0)
        if not annealing and beta != initial:
            raise ValueError("PER checkpoint beta must equal beta_initial when beta annealing is disabled. Regenerate the checkpoint.")
        size = self._require_int(state["size_current"], "size_current", minimum=0, maximum=capacity)
        position = self._require_int(state["position"], "position", minimum=0, maximum=capacity - 1)
        if size < capacity and position != size:
            raise ValueError(f"PER checkpoint position is {position}; expected {size} before wrap. Regenerate the checkpoint.")
        priorities = state["priorities"]
        if not isinstance(priorities, np.ndarray):
            raise ValueError(
                f"PER checkpoint priorities must be a numpy array; got {type(priorities).__name__}. Regenerate the checkpoint."
            )
        if priorities.dtype != np.dtype(np.float32):
            raise ValueError(f"PER checkpoint priorities dtype is {priorities.dtype}; expected float32. Regenerate the checkpoint.")
        if priorities.shape != (capacity,):
            raise ValueError(f"PER checkpoint priorities shape is {priorities.shape}; expected {(capacity,)}. Regenerate the checkpoint.")
        if not bool(np.isfinite(priorities).all()):
            raise ValueError("PER checkpoint priorities must contain only finite values. Regenerate the checkpoint.")
        if np.any(priorities[:size] <= 0) or np.any(priorities[size:] < 0):
            raise ValueError("PER checkpoint priorities are outside the valid positive/zero ranges. Regenerate the checkpoint.")
        maximum = self._require_float(state["max_priority"], "max_priority", minimum=0.0, maximum=float("inf"))
        if maximum <= 0:
            raise ValueError("PER checkpoint max_priority must be positive. Regenerate the checkpoint.")
        if not legacy:
            self._insertion_priority(maximum)
        if size and maximum < float(priorities[:size].max()):
            raise ValueError("PER checkpoint max_priority is below an active priority. Regenerate the checkpoint.")
        geometry: int | None = None
        mode = "unconstrained"
        archives: tuple[history.HistoricalReplayArchive, ...] = ()
        if not legacy:
            mode = state["legality_mode"]
            if type(mode) is not str or mode not in ("unconstrained", "recorded"):
                raise ValueError("PER checkpoint legality_mode is unsupported")
            geometry = state["action_dim"]
            if mode == "recorded":
                self._require_int(geometry, "action_dim", minimum=1, maximum=2**63 - 1)
                if self.action_dim is not None and geometry != self.action_dim:
                    raise ValueError("PER checkpoint action_dim differs from current buffer vocabulary")
            elif geometry is not None:
                raise ValueError("Unconstrained PER cannot claim an action width")
            if not isinstance(state["historical_archives"], list):
                raise ValueError("PER checkpoint historical_archives must be a list")
            archives = tuple(self._own_archive(history._archive_from_state(item)) for item in state["historical_archives"])
        tensors: dict[str, Any] = dict.fromkeys(_STORAGE_FIELDS)
        obs_dim = None
        if not size:
            names: tuple[str, ...]
            if legacy:
                names = _PER_TENSOR_FIELDS
            else:
                names = _STORAGE_FIELDS
            if any(state[name] is not None for name in names):
                raise ValueError("Empty PER checkpoint tensor fields must be null. Regenerate the checkpoint.")
            if not legacy and (geometry is not None or mode != "unconstrained"):
                raise ValueError("Unallocated empty PER cannot claim captured action metadata")
        else:
            observations = state["observations"]
            if not isinstance(observations, torch.Tensor) or observations.ndim != 2:
                raise ValueError("PER checkpoint observations must be a 2D tensor. Regenerate the checkpoint.")
            obs_dim = observations.shape[1]
            if obs_dim <= 0:
                raise ValueError("PER checkpoint observations obs_dim must be positive. Regenerate the checkpoint.")
            if expected_obs_dim is not None and obs_dim != expected_obs_dim:
                raise ValueError(
                    f"PER checkpoint obs_dim is {obs_dim}; expected current obs_dim {expected_obs_dim}. Regenerate the checkpoint."
                )
            if self.observations is not None and obs_dim != self.observations.shape[1]:
                raise ValueError(
                    f"PER checkpoint obs_dim is {obs_dim}; current buffer obs_dim is {self.observations.shape[1]}. "
                    "Regenerate the checkpoint."
                )
            for name in _PER_TENSOR_FIELDS:
                if not legacy and name in _COMPONENTS and state[name] is None:
                    continue
                shape: tuple[int, ...]
                if name in ("observations", "next_observations"):
                    shape = (size, obs_dim)
                else:
                    shape = (size,)
                if name == "actions":
                    dtype = torch.int64
                elif name == "dones":
                    dtype = torch.bool
                else:
                    dtype = torch.float32
                tensors[name] = self._require_tensor(state, name, dtype=dtype, shape=shape)
                if not legacy and tensors[name].device != observations.device:
                    raise ValueError("PER checkpoint row tensor devices must agree")
            if not legacy:
                if bool((tensors["actions"] < 0).any()):
                    raise ValueError("PER checkpoint actions must be nonnegative")
                for name in _COMPONENTS:
                    present = self._require_tensor(state, f"{name}_present", dtype=torch.bool, shape=(size,))
                    if present.device != observations.device:
                        raise ValueError("PER checkpoint presence devices must agree with rows")
                    value = tensors[name]
                    if value is None:
                        if bool(present.any()):
                            raise ValueError(f"PER checkpoint {name} omits recorded component values")
                    elif not bool(present.any()) or bool((value[~present] != 0).any()):
                        raise ValueError(f"PER checkpoint {name} has invalid absent-component placeholders")
                    tensors[f"{name}_present"] = present
                recorded = self._require_tensor(state, "legality_recorded", dtype=torch.bool, shape=(size,))
                if recorded.device != observations.device:
                    raise ValueError("PER checkpoint legality devices must agree with rows")
                tensors["legality_recorded"] = recorded
                if mode == "recorded":
                    assert geometry is not None
                    masks = self._require_tensor(state, "next_action_masks", dtype=torch.bool, shape=(size, geometry))
                    validate_successor_masks(masks, tensors["dones"], action_dim=geometry)
                    if not bool(recorded.all()):
                        raise HistoricalLegalityUnavailable("current PER contains unrecorded successor legality")
                    if bool((tensors["actions"] >= geometry).any()):
                        raise ValueError("PER checkpoint actions exceed the declared vocabulary")
                    tensors["next_action_masks"] = masks
                elif state["next_action_masks"] is not None or bool(recorded.any()):
                    raise ValueError("Unconstrained PER cannot claim recorded masks or partial capture")
        if version == 6:
            unit_ids, counter = self._validate_identity(state, capacity, size)
            sampler = self._validate_sampler(state)
        else:
            unit_ids = np.full(capacity, -1, dtype=np.int64)
            if legacy:
                # This import starts fresh active replay under the current
                # configured owner, without reissuing the target's retired IDs.
                counter, sampler = self.next_unit_id, self._clone_sampler(self._sampler)
            else:
                # Captured5 has legality but predates handles/private RNG. Its
                # explicit history boundary deterministically names live slots.
                unit_ids[:size] = np.arange(size, dtype=np.int64)
                counter, sampler = size, self._external_sampler("captured5-physical-slot-adapter")
        return _ValidatedPrioritizedState(
            **tensors,
            beta=beta,
            priorities=priorities.copy(),
            max_priority=maximum,
            position=position,
            size_current=size,
            obs_dim=obs_dim,
            action_dim=geometry,
            legality_mode=mode,
            archives=archives,
            legacy_state=history._clone(state) if legacy else None,
            unit_ids=unit_ids,
            next_unit_id=counter,
            sampler=sampler,
        )

    def _materialize_serialized(self, state: _ValidatedPrioritizedState) -> _PrioritizedRestoreCandidate:
        if not isinstance(state, _ValidatedPrioritizedState):
            raise ValueError("PER materialization requires validated replay state")
        if state.legacy_state is not None:
            archive = history.archive_standalone_replay(state.legacy_state)
            return _PrioritizedRestoreCandidate(
                **dict.fromkeys(_STORAGE_FIELDS),
                beta=state.beta,
                priorities=np.zeros(self.capacity, dtype=np.float32),
                max_priority=1.0,
                position=0,
                size_current=0,
                action_dim=None,
                legality_mode="unconstrained",
                archives=self._merge_archives((archive,)),
                unit_ids=state.unit_ids.copy(),
                next_unit_id=state.next_unit_id,
                sampler=self._clone_sampler(state.sampler),
            )
        storage: dict[str, torch.Tensor | None] = {}
        for name in _STORAGE_FIELDS:
            value = getattr(state, name)
            if value is None:
                if state.size_current and name in _COMPONENTS:
                    storage[name] = torch.zeros(self.capacity, dtype=torch.float32, device=self.device)
                else:
                    storage[name] = None
            else:
                allocated = torch.zeros((self.capacity, *value.shape[1:]), dtype=value.dtype, device=self.device)
                allocated[: state.size_current].copy_(value.to(self.device))
                storage[name] = allocated
        return _PrioritizedRestoreCandidate(
            **storage,
            beta=state.beta,
            priorities=state.priorities.copy(),
            max_priority=state.max_priority,
            position=state.position,
            size_current=state.size_current,
            action_dim=state.action_dim,
            legality_mode=state.legality_mode,
            archives=self._merge_archives(state.archives),
            unit_ids=state.unit_ids.copy(),
            next_unit_id=state.next_unit_id,
            sampler=self._clone_sampler(state.sampler),
        )

    def _prepare_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _PrioritizedRestoreCandidate:
        return self._materialize_serialized(self._validate_serialized(state, expected_obs_dim=expected_obs_dim))

    def validate_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _ValidatedPrioritizedState:
        """Pure strict current/old validation; never archives, materializes or installs."""
        return self._validate_serialized(state, expected_obs_dim=expected_obs_dim)

    def materialize_validated(self, state: _ValidatedPrioritizedState) -> _PrioritizedRestoreCandidate:
        return self._materialize_serialized(state)

    def prepare_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _PrioritizedRestoreCandidate:
        return self._prepare_serialized(state, expected_obs_dim=expected_obs_dim)

    def load_prepared(self, candidate: _PrioritizedRestoreCandidate) -> None:
        if not isinstance(candidate, _PrioritizedRestoreCandidate):
            raise ValueError("PER installation requires a prepared restore candidate")
        archives = self._merge_archives(candidate.archives)
        # Clone every fallible owned resource before assigning any live field.
        storage = {name: None if (value := getattr(candidate, name)) is None else value.detach().clone() for name in _STORAGE_FIELDS}
        priorities, unit_ids = candidate.priorities.copy(), candidate.unit_ids.copy()
        reverse = {int(unit): slot for slot, unit in enumerate(unit_ids[: candidate.size_current])}
        sampler = self._clone_sampler(candidate.sampler)
        for name, value in storage.items():
            setattr(self, name, value)
        self.beta, self.priorities, self.max_priority = candidate.beta, priorities, candidate.max_priority
        self.position, self.size_current = candidate.position, candidate.size_current
        self.action_dim, self.legality_mode = candidate.action_dim, candidate.legality_mode
        self.unit_ids, self.next_unit_id, self._id_to_slot = unit_ids, candidate.next_unit_id, reverse
        self._sampler = sampler
        self._historical_archives = archives

    def load_for_mode(self, state: Mapping[str, Any], *, requested_mode: history.AccessMode) -> None:
        if requested_mode not in ("auto", "recorded_full_resume", "archived_history_fresh_episode", "inference"):
            raise ValueError("requested_mode is unsupported")
        validated = self._validate_serialized(state, expected_obs_dim=None)
        if validated.legacy_state is not None and requested_mode == "recorded_full_resume":
            raise HistoricalLegalityUnavailable("missing historical successor masks; use approved archived_history_fresh_episode")
        if validated.legacy_state is None and requested_mode == "archived_history_fresh_episode":
            raise ValueError("current PER cannot discard qualified active rows")
        self.load_prepared(self._materialize_serialized(validated))

    def load_from_serialized(self, state: Mapping[str, Any]) -> None:
        self.load_for_mode(state, requested_mode="auto")
