"""Uniform replay with owned successor legality and approved historical archives.

The original push/sample pair explicitly serves unconstrained public callers.
Constrained producers use push_recorded with actual successor action sets.
Pre-capture replay is inspectable history and never becomes active experience.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import torch

from townlet.training import historical_checkpoint as history
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


REPLAY_BUFFER_FORMAT_VERSION = 5
REPLAY_BUFFER_KIND = "standard"
_COMPONENTS = ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping")
_PRESENCE_FIELDS = tuple(f"{name}_present" for name in _COMPONENTS)
_ROW_FIELDS = ("observations", "actions", "rewards", *_COMPONENTS, "next_observations", "dones")
_STORAGE_FIELDS = (*_ROW_FIELDS, "next_action_masks", "legality_recorded", *_PRESENCE_FIELDS)
_LEGACY_STATE_KEYS = frozenset({"replay_kind", "format_version", "capacity", "size", "position", *_ROW_FIELDS})
REPLAY_BUFFER_STATE_KEYS = _LEGACY_STATE_KEYS | {
    "action_dim",
    "legality_mode",
    "historical_archives",
    "next_action_masks",
    "legality_recorded",
    *_PRESENCE_FIELDS,
}


@dataclass(frozen=True, slots=True)
class UniformReplayBatch(ReplayBatch):
    """Optional components exist only where their presence tensors are true.

    False positions hold explicit zero placeholders; a wholly absent column
    is None. Presence is telemetry and never changes composed rewards or loss.
    """

    rewards_extrinsic_present: torch.Tensor
    rewards_intrinsic_present: torch.Tensor
    rewards_shaping_present: torch.Tensor

    def __post_init__(self) -> None:
        ReplayBatch.__post_init__(self)
        if self.observations.ndim != 2:
            raise ValueError("uniform batches contain flat transition rows")
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
class _ReplayRows:
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
class _ReplayRestoreCandidate(_ReplayRows):
    size: int
    position: int
    has_wrapped: bool
    action_dim: int | None
    legality_mode: str
    archives: tuple[history.HistoricalReplayArchive, ...]


@dataclass(frozen=True)
class _ValidatedReplayState(_ReplayRows):
    size: int
    position: int
    obs_dim: int | None
    action_dim: int | None
    legality_mode: str
    archives: tuple[history.HistoricalReplayArchive, ...]
    legacy_state: Mapping[str, Any] | None


class ReplayBuffer:
    """FIFO uniform storage; archives have no sampler, warmup or optimizer route."""

    def __init__(self, capacity: int, device: torch.device):
        self.capacity = capacity
        self.device = device
        self.position = self.size = 0
        self.has_wrapped = False
        self.action_dim: int | None = None
        self.legality_mode = "unconstrained"
        self._historical_archives: tuple[history.HistoricalReplayArchive, ...] = ()
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

    @property
    def retained_transitions(self) -> int:
        return self.size

    @property
    def historical_archives(self) -> tuple[history.HistoricalReplayArchive, ...]:
        """Return owned frozen records without exposing the installed records."""
        return tuple(self._own_archive(archive) for archive in self._historical_archives)

    @staticmethod
    def _own_archive(archive: history.HistoricalReplayArchive) -> history.HistoricalReplayArchive:
        if not isinstance(archive, history.HistoricalReplayArchive):
            raise ValueError("historical archive must be a HistoricalReplayArchive")
        owned = history._archive_from_state(history._record(archive))
        if owned.source_formats["replay_kind"] != REPLAY_BUFFER_KIND:
            raise ValueError("historical archive replay kind differs from uniform storage")
        return owned

    def _merge_archives(self, incoming: tuple[history.HistoricalReplayArchive, ...]) -> tuple[history.HistoricalReplayArchive, ...]:
        owned = tuple(self._own_archive(archive) for archive in (*self._historical_archives, *incoming))
        seen: set[str] = set()
        result = []
        for archive in owned:
            if archive.source_digest not in seen:
                seen.add(archive.source_digest)
                result.append(archive)
        return tuple(result)

    def install_historical_archive(self, archive: history.HistoricalReplayArchive) -> None:
        """Validate the complete source domain, digest and rows before mutation."""
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
            raise ValueError("observations must be float32 [batch, obs_dim] with positive observation width")
        batch_size, obs_dim = observations.shape
        if batch_size > self.capacity:
            raise ValueError(f"batch_size ({batch_size}) exceeds buffer capacity ({self.capacity})")
        if next_observations.shape != observations.shape or next_observations.dtype != torch.float32:
            raise ValueError("next_observations must match observations shape and float32 dtype")
        for name, value, dtype in (
            ("actions", actions, torch.int64),
            ("rewards.total", rewards.total, torch.float32),
            ("dones", dones, torch.bool),
        ):
            if value.shape != (batch_size,) or value.dtype != dtype:
                raise ValueError(f"{name} must have shape ({batch_size},) and dtype {dtype}")
        if bool((actions < 0).any()):
            raise ValueError("actions must be nonnegative")
        if self.observations is not None and obs_dim != self.observations.shape[1]:
            raise ValueError(f"observations obs_dim ({obs_dim}) != current buffer obs_dim ({self.observations.shape[1]})")
        for name, tensor_value in (
            ("observations", observations),
            ("next_observations", next_observations),
            ("rewards.total", rewards.total),
            ("rewards.extrinsic", rewards.extrinsic),
            ("rewards.intrinsic", rewards.intrinsic),
            ("rewards.shaping", rewards.shaping),
        ):
            if tensor_value is None:
                continue
            if name.startswith("rewards.") and (tensor_value.shape != (batch_size,) or tensor_value.dtype != torch.float32):
                raise ValueError(f"{name} must have shape ({batch_size},) and dtype torch.float32")
            if not bool(torch.isfinite(tensor_value).all()):
                raise ValueError(f"{name} must contain only finite values")
        return batch_size

    def push(
        self,
        observations: torch.Tensor,
        actions: torch.Tensor,
        rewards: RewardTensor,
        next_observations: torch.Tensor,
        dones: torch.Tensor,
    ) -> None:
        """Preserve the unconstrained public adapter without claiming capture.

        After an action vocabulary has been supplied, this adapter explicitly
        declares every action in it legal. Constrained callers use push_recorded.
        """
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
        """Store actual successor sets and independent optional DAC components."""
        if not isinstance(next_action_masks, torch.Tensor) or next_action_masks.ndim != 2:
            raise ValueError("next_action_masks must be a bool tensor of shape [batch, action_dim]")
        validate_successor_masks(next_action_masks, dones, action_dim=next_action_masks.shape[1])
        self._push(observations, actions, rewards, next_observations, dones, next_action_masks)

    def _push(
        self,
        observations: torch.Tensor,
        actions: torch.Tensor,
        rewards: RewardTensor,
        next_observations: torch.Tensor,
        dones: torch.Tensor,
        masks: torch.Tensor | None,
    ) -> None:
        batch_size = self._validate_push(observations, actions, rewards, next_observations, dones)
        action_dim = self.action_dim
        if masks is not None:
            validate_successor_masks(masks, dones, action_dim=masks.shape[1])
            if action_dim is not None and masks.shape[1] != action_dim:
                raise ValueError("successor action width differs from current buffer action vocabulary")
            action_dim = masks.shape[1]
            if bool((actions >= action_dim).any()):
                raise ValueError("actions outside the declared action vocabulary")
            if self.actions is not None and bool((self.actions[: self.size] >= action_dim).any()):
                raise ValueError("existing unconstrained actions exceed the supplied action vocabulary")
        if batch_size == 0:
            return
        values = {
            "observations": observations,
            "actions": actions,
            "rewards": rewards.total,
            "next_observations": next_observations,
            "dones": dones,
        }
        for name, component in zip(_COMPONENTS, (rewards.extrinsic, rewards.intrinsic, rewards.shaping), strict=True):
            if component is None:
                values[name] = torch.zeros_like(rewards.total)
            else:
                values[name] = component
            values[f"{name}_present"] = torch.full((batch_size,), component is not None, dtype=torch.bool, device=rewards.total.device)
        values["legality_recorded"] = torch.full((batch_size,), masks is not None, dtype=torch.bool, device=dones.device)
        moved = {name: value.detach().to(self.device).clone() for name, value in values.items()}
        if masks is not None:
            moved["next_action_masks"] = masks.detach().to(self.device).clone()
        storage = {name: getattr(self, name) for name in _STORAGE_FIELDS}
        for name, value in moved.items():
            if storage[name] is None:
                storage[name] = torch.zeros((self.capacity, *value.shape[1:]), dtype=value.dtype, device=self.device)
        if action_dim is not None and self.action_dim is None and self.size:
            # Earlier live calls explicitly used the unconstrained adapter.
            storage["next_action_masks"][: self.size].fill_(True)
            storage["legality_recorded"][: self.size].fill_(True)
        indices = (torch.arange(batch_size, device=self.device) + self.position) % self.capacity
        for name, value in moved.items():
            storage[name][indices] = value
        for name, value in storage.items():
            setattr(self, name, value)
        self.action_dim = action_dim
        if action_dim is not None:
            self.legality_mode = "recorded"
        else:
            self.legality_mode = "unconstrained"
        self.position = (self.position + batch_size) % self.capacity
        self.size = min(self.size + batch_size, self.capacity)
        self.has_wrapped = self.size == self.capacity

    def _indices(self, batch_size: int) -> torch.Tensor:
        self._require_int(batch_size, "batch_size", minimum=0, maximum=2**63 - 1)
        if self.size < batch_size:
            raise ValueError(f"Buffer size ({self.size}) < batch_size ({batch_size})")
        if self.observations is None:
            raise ValueError("Cannot sample an unallocated empty replay buffer")
        return torch.randperm(self.size, device=self.device)[:batch_size]

    def sample(self, batch_size: int) -> dict[str, torch.Tensor]:
        """Preserve the public without-replacement transition dictionary adapter."""
        indices = self._indices(batch_size)
        result = {
            name: getattr(self, name)[indices].clone() for name in ("observations", "actions", "rewards", "next_observations", "dones")
        }
        result["mask"] = torch.ones(batch_size, dtype=torch.bool, device=self.device)
        if self.next_action_masks is not None:
            assert self.legality_recorded is not None
            result["next_action_masks"] = self.next_action_masks[indices].clone()
            result["legality_recorded"] = self.legality_recorded[indices].clone()
        return result

    @staticmethod
    def _check_request(request: ReplayRequest) -> None:
        if not isinstance(request, ReplayRequest):
            raise ValueError("uniform replay requires a ReplayRequest")
        if (request.sampling_mode, request.sequence_mode, request.sequence_objective, request.sequence_length) != (
            "uniform_without_replacement",
            "feedforward",
            "transition",
            1,
        ):
            raise ValueError("uniform replay supports flat transitions sampled uniformly without replacement")

    def readiness(self, request: ReplayRequest) -> ReplayReadiness:
        self._check_request(request)
        qualified = self.action_dim is not None and self.legality_recorded is not None and bool(self.legality_recorded[: self.size].all())
        if qualified:
            sampleable = self.size
        else:
            sampleable = 0
        if self.size < request.min_transitions:
            return ReplayReadiness(False, self.size, sampleable, "warmup")
        if sampleable < request.batch_size:
            return ReplayReadiness(False, self.size, sampleable, "batch_unavailable")
        return ReplayReadiness(True, self.size, sampleable, "ready")

    def sample_batch(self, request: ReplayRequest) -> UniformReplayBatch:
        ready = self.readiness(request)
        if not ready.ready:
            raise ValueError(
                f"uniform replay unavailable: {ready.reason}; retained={ready.retained_transitions}, sampleable={ready.sampleable_units}"
            )
        indices = self._indices(request.batch_size)
        weights = np.ones(request.batch_size, dtype=np.float64)
        receipt = SamplingReceipt(
            indices.detach().cpu().numpy().astype(np.int64, copy=True),
            weights,
            self.size,
            1.0 / (self.size - np.arange(request.batch_size, dtype=np.float64)),
            request.sampling_mode,
            "transition",
            "unit_weights",
        )
        components: dict[str, Any] = {}
        for name in _COMPONENTS:
            present = getattr(self, f"{name}_present")[indices]
            if bool(present.any()):
                components[name] = getattr(self, name)[indices]
            else:
                components[name] = None
            components[f"{name}_present"] = present
        assert self.observations is not None and self.actions is not None and self.rewards is not None
        assert self.next_observations is not None and self.dones is not None
        assert self.next_action_masks is not None and self.legality_recorded is not None
        return UniformReplayBatch(
            observations=self.observations[indices],
            actions=self.actions[indices],
            rewards=self.rewards[indices],
            next_observations=self.next_observations[indices],
            dones=self.dones[indices],
            next_action_masks=self.next_action_masks[indices],
            legality_recorded=self.legality_recorded[indices],
            loss_mask=torch.ones(request.batch_size, dtype=torch.bool, device=self.device),
            lengths=torch.ones(request.batch_size, dtype=torch.int64, device=self.device),
            unit_ids=indices,
            weights=torch.from_numpy(weights.copy()).to(self.device),
            sampling=receipt,
            **components,
        )

    def __len__(self) -> int:
        return self.size

    def clear(self) -> None:
        """Deallocate active replay while preserving historical access."""
        self.size = self.position = 0
        self.has_wrapped = False
        self.action_dim = None
        self.legality_mode = "unconstrained"
        for name in _STORAGE_FIELDS:
            setattr(self, name, None)

    def stats(self) -> dict[str, Any]:
        memory_bytes = sum(value.numel() * value.element_size() for name in _STORAGE_FIELDS if (value := getattr(self, name)) is not None)
        occupancy_ratio = self.size / self.capacity if self.capacity > 0 else 0.0
        return {
            "size": self.size,
            "capacity": self.capacity,
            "occupancy_ratio": occupancy_ratio,
            "memory_bytes": memory_bytes,
            "device": str(self.device),
        }

    def serialize(self) -> dict[str, Any]:
        """Own chronological active rows and separate complete archive records."""
        position = 0
        if self.capacity:
            position = self.size % self.capacity
        state: dict[str, Any] = {
            "replay_kind": REPLAY_BUFFER_KIND,
            "format_version": REPLAY_BUFFER_FORMAT_VERSION,
            "capacity": self.capacity,
            "size": self.size,
            "position": position,
            "action_dim": self.action_dim,
            "legality_mode": self.legality_mode,
            "historical_archives": [history._record(archive) for archive in self._historical_archives],
        }
        for name in _STORAGE_FIELDS:
            value = getattr(self, name)
            if value is None or self.size == 0:
                state[name] = None
            elif self.has_wrapped:
                state[name] = torch.cat((value[self.position :], value[: self.position])).detach().cpu().clone()
            else:
                state[name] = value[: self.size].detach().cpu().clone()
        for name in _COMPONENTS:
            present = state[f"{name}_present"]
            if present is not None and not bool(present.any()):
                state[name] = None
        return state

    @staticmethod
    def _require_tensor(state: Mapping[str, Any], field: str, *, dtype: torch.dtype, shape: tuple[int, ...]) -> torch.Tensor:
        value = state[field]
        if not isinstance(value, torch.Tensor) or value.dtype != dtype or tuple(value.shape) != shape:
            raise ValueError(f"Replay checkpoint {field} must be a tensor of shape {shape} and dtype {dtype}")
        if dtype.is_floating_point and not bool(torch.isfinite(value).all()):
            raise ValueError(f"Replay checkpoint {field} must contain only finite values")
        return value.detach().clone()

    @staticmethod
    def _require_int(value: object, field: str, *, minimum: int, maximum: int) -> int:
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValueError(f"Replay checkpoint {field} must be an integer in [{minimum}, {maximum}]; got {value!r}")
        return value

    def _validate_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _ValidatedReplayState:
        if not isinstance(state, Mapping):
            raise ValueError("Replay buffer checkpoint payload must be a mapping")
        version = state.get("format_version")
        if type(version) is not int or version not in (4, REPLAY_BUFFER_FORMAT_VERSION):
            raise ValueError(f"Cannot load replay buffer checkpoint with format_version {version!r}")
        legacy = version == 4
        if legacy:
            expected_keys = _LEGACY_STATE_KEYS
        else:
            expected_keys = REPLAY_BUFFER_STATE_KEYS
        if set(state) != expected_keys:
            raise ValueError(
                f"Replay checkpoint key set mismatch: missing={sorted(expected_keys - set(state))}, "
                f"unknown={sorted(set(state) - expected_keys)}"
            )
        if state["replay_kind"] != REPLAY_BUFFER_KIND:
            raise ValueError("Replay checkpoint replay_kind must be standard")
        capacity = self._require_int(state["capacity"], "capacity", minimum=1, maximum=2**63 - 1)
        if capacity != self.capacity:
            raise ValueError(f"Replay checkpoint capacity is {capacity}; current capacity is {self.capacity}")
        size = self._require_int(state["size"], "size", minimum=0, maximum=capacity)
        position = self._require_int(state["position"], "position", minimum=0, maximum=capacity - 1)
        if position != size % capacity:
            raise ValueError(f"Replay checkpoint position is {position}; expected {size % capacity} for size {size}")
        tensors: dict[str, Any] = dict.fromkeys(_STORAGE_FIELDS)
        legacy_state: Mapping[str, Any] | None = None
        archives: tuple[history.HistoricalReplayArchive, ...] = ()
        action_dim, mode = None, "unconstrained"
        if not legacy:
            mode = state["legality_mode"]
            if type(mode) is not str or mode not in ("recorded", "unconstrained"):
                raise ValueError("Replay checkpoint legality_mode is unsupported")
            action_dim = state["action_dim"]
            if mode == "recorded":
                self._require_int(action_dim, "action_dim", minimum=1, maximum=2**63 - 1)
                if self.action_dim is not None and self.action_dim != action_dim:
                    raise ValueError("Replay checkpoint action_dim differs from current buffer vocabulary")
            elif action_dim is not None:
                raise ValueError("Unconstrained replay without supplied masks cannot claim an action width")
            records = state["historical_archives"]
            if not isinstance(records, list):
                raise ValueError("Replay checkpoint historical_archives must be a list")
            archives = tuple(self._own_archive(history._archive_from_state(record)) for record in records)
        if size == 0:
            names: tuple[str, ...]
            if legacy:
                names = _ROW_FIELDS
            else:
                names = _STORAGE_FIELDS
            if any(state[name] is not None for name in names):
                raise ValueError("Empty replay checkpoint tensor fields must be null")
            if not legacy and (action_dim is not None or mode != "unconstrained"):
                raise ValueError("Unallocated empty replay cannot claim a captured action vocabulary")
            if legacy:
                legacy_state = history._clone(state)
            return _ValidatedReplayState(
                **tensors,
                size=0,
                position=0,
                obs_dim=None,
                action_dim=None,
                legality_mode="unconstrained",
                archives=archives,
                legacy_state=legacy_state,
            )
        observations = state["observations"]
        if not isinstance(observations, torch.Tensor) or observations.ndim != 2 or observations.shape[1] < 1:
            raise ValueError("Replay checkpoint observations must be [rows, obs_dim] with positive width")
        obs_dim = observations.shape[1]
        if expected_obs_dim is not None and obs_dim != expected_obs_dim:
            raise ValueError(f"Replay checkpoint obs_dim is {obs_dim}; expected current obs_dim {expected_obs_dim}")
        if self.observations is not None and self.observations.shape[1] != obs_dim:
            raise ValueError("Replay checkpoint observation width differs from current storage")
        shape: tuple[int, ...]
        for name in _ROW_FIELDS:
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
            if not legacy and name in _COMPONENTS and state[name] is None:
                continue
            tensors[name] = self._require_tensor(state, name, dtype=dtype, shape=shape)
            if tensors[name].device != observations.device:
                raise ValueError("Replay checkpoint row tensor devices must agree")
        if bool((tensors["actions"] < 0).any()):
            raise ValueError("Replay checkpoint actions must be nonnegative")
        if not legacy:
            for name in _COMPONENTS:
                present = self._require_tensor(state, f"{name}_present", dtype=torch.bool, shape=(size,))
                value = tensors[name]
                if present.device != observations.device:
                    raise ValueError("Replay checkpoint component presence devices must agree with rows")
                if value is None:
                    if bool(present.any()):
                        raise ValueError(f"Replay checkpoint {name} omits recorded component values")
                elif not bool(present.any()) or bool((value[~present] != 0).any()):
                    raise ValueError(f"Replay checkpoint {name} has invalid absent-component placeholders")
                tensors[f"{name}_present"] = present
            recorded = self._require_tensor(state, "legality_recorded", dtype=torch.bool, shape=(size,))
            if recorded.device != observations.device:
                raise ValueError("Replay checkpoint legality devices must agree with rows")
            tensors["legality_recorded"] = recorded
            if mode == "recorded":
                assert action_dim is not None
                masks = self._require_tensor(state, "next_action_masks", dtype=torch.bool, shape=(size, action_dim))
                validate_successor_masks(masks, tensors["dones"], action_dim=action_dim)
                if not bool(recorded.all()):
                    raise HistoricalLegalityUnavailable("current replay contains unrecorded successor legality")
                if bool((tensors["actions"] >= action_dim).any()):
                    raise ValueError("Replay checkpoint actions exceed the declared vocabulary")
                tensors["next_action_masks"] = masks
            elif state["next_action_masks"] is not None or bool(recorded.any()):
                raise ValueError("Unconstrained replay cannot claim recorded masks or partial capture")
        if legacy:
            legacy_state = history._clone(state)
        return _ValidatedReplayState(
            **tensors,
            size=size,
            position=position,
            obs_dim=obs_dim,
            action_dim=action_dim,
            legality_mode=mode,
            archives=archives,
            legacy_state=legacy_state,
        )

    def _materialize_serialized(self, state: _ValidatedReplayState) -> _ReplayRestoreCandidate:
        if not isinstance(state, _ValidatedReplayState):
            raise ValueError("uniform materialization requires validated replay state")
        if state.legacy_state is not None:
            archive = history.archive_standalone_replay(state.legacy_state)
            return _ReplayRestoreCandidate(
                **dict.fromkeys(_STORAGE_FIELDS),
                size=0,
                position=0,
                has_wrapped=False,
                action_dim=None,
                legality_mode="unconstrained",
                archives=self._merge_archives((archive,)),
            )
        storage: dict[str, Any] = {}
        for name in _STORAGE_FIELDS:
            value = getattr(state, name)
            if value is None:
                if state.size and name in _COMPONENTS:
                    storage[name] = torch.zeros(self.capacity, dtype=torch.float32, device=self.device)
                else:
                    storage[name] = None
            else:
                allocated = torch.zeros((self.capacity, *value.shape[1:]), dtype=value.dtype, device=self.device)
                allocated[: state.size].copy_(value.to(self.device))
                storage[name] = allocated
        return _ReplayRestoreCandidate(
            **storage,
            size=state.size,
            position=state.position,
            has_wrapped=state.size == self.capacity,
            action_dim=state.action_dim,
            legality_mode=state.legality_mode,
            archives=self._merge_archives(state.archives),
        )

    def _prepare_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _ReplayRestoreCandidate:
        return self._materialize_serialized(self._validate_serialized(state, expected_obs_dim=expected_obs_dim))

    def validate_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int) -> _ValidatedReplayState:
        """Pure exact validation, including supported pre-capture inspection."""
        return self._validate_serialized(state, expected_obs_dim=expected_obs_dim)

    def materialize_validated(self, state: _ValidatedReplayState) -> _ReplayRestoreCandidate:
        """Old validated rows materialize only an archive and empty active replay."""
        return self._materialize_serialized(state)

    def prepare_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _ReplayRestoreCandidate:
        return self._prepare_serialized(state, expected_obs_dim=expected_obs_dim)

    def load_prepared(self, candidate: _ReplayRestoreCandidate) -> None:
        """Transfer one prepared storage candidate after archive checks pass."""
        if not isinstance(candidate, _ReplayRestoreCandidate):
            raise ValueError("uniform installation requires a prepared restore candidate")
        archives = self._merge_archives(candidate.archives)
        for name in _STORAGE_FIELDS:
            setattr(self, name, getattr(candidate, name))
        self.size = candidate.size
        self.position = candidate.position
        self.has_wrapped = candidate.has_wrapped
        self.action_dim = candidate.action_dim
        self.legality_mode = candidate.legality_mode
        self._historical_archives = archives

    def load_for_mode(self, state: Mapping[str, Any], *, requested_mode: history.AccessMode) -> None:
        """Resolve approved historical mode before any restore mutation."""
        if requested_mode not in ("auto", "recorded_full_resume", "archived_history_fresh_episode", "inference"):
            raise ValueError("requested_mode is unsupported")
        validated = self._validate_serialized(state, expected_obs_dim=None)
        if validated.legacy_state is not None and requested_mode == "recorded_full_resume":
            raise HistoricalLegalityUnavailable("missing historical successor masks; use approved archived_history_fresh_episode")
        if validated.legacy_state is None and requested_mode == "archived_history_fresh_episode":
            raise ValueError("current replay cannot discard qualified active rows")
        self.load_prepared(self._materialize_serialized(validated))

    def load_from_serialized(self, state: Mapping[str, Any]) -> None:
        """Ordinary old imports archive/fresh-start; current imports retain capture."""
        self.load_for_mode(state, requested_mode="auto")
