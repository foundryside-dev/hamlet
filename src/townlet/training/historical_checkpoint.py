"""Approved, non-sampling access to exact pre-capture checkpoint history.

``state-sha256:v1`` hashes framed typed values, never pickle bytes. Every frame
is one ASCII tag, an unsigned big-endian eight-byte payload length, then payload.
Mappings preserve their container type and iteration order; tensors encode dtype,
shape, byte order, and contiguous logical value bits independently of device.
File-byte provenance belongs to native loaders, outside the six archive fields.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import struct
import sys
import tempfile
from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal

import numpy as np
import torch
from pydantic import BaseModel
from torch import Tensor

from townlet.config.brain_config import BrainConfig, apply_training_overrides
from townlet.config.training_v2_config import TrainingV2Config
from townlet.training.replay_contract import HistoricalLegalityUnavailable, validate_successor_masks

APPROVAL_REFERENCE = "BAC-HISTORY-A-2026-11-01"
REWARD_SEMANTICS = "historical_recorded_pre_fix"
AccessMode = Literal["auto", "recorded_full_resume", "archived_history_fresh_episode", "inference"]
_MODES = ("auto", "recorded_full_resume", "archived_history_fresh_episode", "inference")
_ROWS = ("observations", "actions", "rewards", "next_observations", "dones")
_COMPONENTS = ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping")
_KINDS = {"standard": 4, "prioritized": 4, "sequential": 5}
_CURRENT_REPLAY_VERSIONS = {"standard": (5,), "prioritized": (5, 6), "sequential": (6, 7)}
_STATE_PREFIX = "state-sha256:v1:"


def _supported_formats(demo: int, population: int, replay: int, kind: str) -> bool:
    return (demo, population, replay) == (9, 6, _KINDS[kind]) or (
        (demo, population) == (10, 7) and replay in _CURRENT_REPLAY_VERSIONS[kind]
    )


def _clone(value):
    if isinstance(value, Tensor):
        return value.detach().clone()
    if isinstance(value, OrderedDict):
        return OrderedDict((_clone(key), _clone(item)) for key, item in value.items())
    if isinstance(value, Mapping):
        return {_clone(key): _clone(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clone(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_clone(item) for item in value)
    return copy.deepcopy(value)


def _frame(tag: bytes, payload: bytes) -> bytes:
    return tag + len(payload).to_bytes(8, "big") + payload


def _canonical(value) -> bytes:
    """Closed v1 encoding: unsupported objects refuse instead of being coerced."""
    if value is None:
        return _frame(b"n", b"")
    if type(value) is bool:
        return _frame(b"b", bytes([value]))
    if type(value) is int:
        return _frame(b"i", value.to_bytes(max(1, (value.bit_length() + 8) // 8), "big", signed=True))
    if type(value) is float:
        return _frame(b"f", struct.pack(">d", value))
    if type(value) is str:
        return _frame(b"s", value.encode("utf-8", errors="surrogatepass"))
    if type(value) in (bytes, bytearray):
        return _frame(b"y" if type(value) is bytes else b"z", bytes(value))
    if isinstance(value, Tensor):
        if value.layout != torch.strided or value.is_quantized:
            raise ValueError("archive digest requires dense, non-quantized tensors")
        owned = value.detach().resolve_conj().resolve_neg().cpu().contiguous()
        bits = owned.reshape(-1).view(torch.uint8).numpy().tobytes()
        return _frame(b"t", _canonical((str(owned.dtype), tuple(owned.shape), sys.byteorder)) + _frame(b"r", bits))
    if isinstance(value, (np.ndarray, np.generic)):
        if value.dtype.hasobject or value.dtype.fields is not None:
            raise ValueError("archive digest refuses object/structured numpy values")
        body = _canonical((value.dtype.str, tuple(value.shape))) + _frame(b"r", value.tobytes(order="C"))
        if isinstance(value, np.ndarray):
            return _frame(b"a", body)
        return _frame(b"g", body)
    if type(value) in (list, tuple):
        return _frame(b"l" if type(value) is list else b"q", b"".join(_canonical(item) for item in value))
    if type(value) in (dict, OrderedDict):
        body = b"".join(_canonical(key) + _canonical(item) for key, item in value.items())
        return _frame(b"d" if type(value) is dict else b"o", body)
    raise ValueError(f"unsupported archive digest value type: {type(value).__name__}")


def _state_digest(state: Mapping[str, object], source_formats: Mapping[str, object]) -> str:
    return _STATE_PREFIX + hashlib.sha256(b"BAC-HC-state-v1\0" + _canonical((source_formats, state))).hexdigest()


def _mapping(value, location: str) -> Mapping:
    if not isinstance(value, Mapping):
        raise ValueError(f"{location} must be a mapping")
    return value


def _mapping_sequence(value: object, location: str) -> tuple[Mapping, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{location} must be a sequence of mappings")
    return tuple(_mapping(item, f"{location}[{index}]") for index, item in enumerate(value))


def _tensor(value: object, location: str) -> Tensor:
    if not isinstance(value, Tensor):
        raise ValueError(f"{location} must be a tensor")
    return value


def _integer(value, location: str, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{location} must be an integer >= {minimum}")
    return value


def _keys(value: Mapping, expected, location: str) -> None:
    expected = set(expected)
    if set(value) != expected:
        raise ValueError(f"{location} schema key mismatch: missing={expected - set(value)}, unknown={set(value) - expected}")


def _formats(payload: Mapping[str, object]) -> tuple[dict, Mapping, Mapping]:
    payload = _mapping(payload, "checkpoint")
    population = _mapping(payload.get("population_state"), "population_state")
    replay = _mapping(population.get("replay_buffer"), "population_state.replay_buffer")
    kind = replay.get("replay_kind")
    version, population_version, replay_version = payload.get("version"), population.get("version"), replay.get("format_version")
    if (
        type(kind) is not str
        or kind not in _KINDS
        or type(version) is not int
        or type(population_version) is not int
        or type(replay_version) is not int
    ):
        raise ValueError("unsupported checkpoint/population/replay format or replay_kind")
    if not _supported_formats(version, population_version, replay_version, kind):
        raise ValueError(f"unsupported checkpoint/population/replay versions: {version}/{population_version}/{replay_version}")
    return {"demo": version, "population": population_version, "replay": replay_version, "replay_kind": kind}, population, replay


def _count(replay: Mapping) -> int:
    kind = replay.get("replay_kind")
    count_keys = {"standard": "size", "prioritized": "size_current", "sequential": "num_transitions"}
    if type(kind) is not str or kind not in count_keys:
        raise ValueError("replay.replay_kind is unsupported")
    key = count_keys[kind]
    count = _integer(replay.get(key), f"replay.{key}", 0)
    if count > _integer(replay.get("capacity"), "replay.capacity", 1):
        raise ValueError("replay retained row count exceeds capacity")
    return count


def _validate_rows(rows: Mapping, location: str) -> int:
    _keys(rows, (*_ROWS, *_COMPONENTS), location)
    observations = rows["observations"]
    if not isinstance(observations, Tensor) or observations.ndim != 2 or observations.shape[1] < 1:
        raise ValueError(f"{location}.observations shape must be [rows, obs_dim]")
    count = observations.shape[0]
    for key in (*_ROWS, *_COMPONENTS):
        tensor = rows[key]
        if key in _COMPONENTS and tensor is None:
            continue
        shape: torch.Size | tuple[int, ...]
        if key in ("observations", "next_observations"):
            shape = observations.shape
        else:
            shape = (count,)
        if key == "actions":
            dtype = torch.int64
        elif key == "dones":
            dtype = torch.bool
        else:
            dtype = torch.float32
        if not isinstance(tensor, Tensor) or tensor.shape != shape or tensor.dtype != dtype:
            raise ValueError(f"{location}.{key} row shape/dtype mismatch")
        if tensor.device != observations.device or not torch.isfinite(tensor).all():
            raise ValueError(f"{location}.{key} row device/finite-value mismatch")
    if (rows["actions"] < 0).any():
        raise ValueError(f"{location}.actions contains a negative action")
    return count


def _validate_archive_state(state: Mapping, formats: Mapping) -> int:
    standalone = set(formats) == {"scope", "replay", "replay_kind"}
    version_keys: tuple[str, ...]
    if standalone:
        if type(formats["scope"]) is not str or formats["scope"] != "standalone_replay":
            raise ValueError("archive standalone source scope is unsupported")
    else:
        _keys(formats, ("demo", "population", "replay", "replay_kind"), "archive.source_formats")
    kind = formats.get("replay_kind")
    if standalone:
        version_keys = ("replay",)
    else:
        version_keys = ("demo", "population", "replay")
    if type(kind) is not str or kind not in _KINDS or any(type(formats[key]) is not int for key in version_keys):
        raise ValueError("archive source format domain is invalid")
    if formats["replay"] != _KINDS[kind] or (not standalone and (formats["demo"], formats["population"]) != (9, 6)):
        raise ValueError("archive source formats must be exact pre-capture 9/6/4,4,5")
    if state.get("replay_kind") != kind or type(state.get("format_version")) is not int or state["format_version"] != _KINDS[kind]:
        raise ValueError("archive state replay format differs from declared source format")
    count = _count(state)
    base = ("replay_kind", "format_version", "capacity")
    if kind == "sequential":
        _keys(state, (*base, "num_transitions", "episodes"), "archive.replay")
        if not isinstance(state["episodes"], list):
            raise ValueError("archive.replay.episodes must be a list")
        total, width = 0, None
        for index, episode in enumerate(state["episodes"]):
            episode = _mapping(episode, f"archive.episodes[{index}]")
            length = _validate_rows(episode, f"archive.episodes[{index}]")
            if length < 1:
                raise ValueError("archive episode boundaries contain empty episodes")
            if width is not None and width != episode["observations"].shape[1]:
                raise ValueError("archive episode observation widths differ")
            width, total = episode["observations"].shape[1], total + length
        if total != count:
            raise ValueError("archive episode row lengths differ from num_transitions")
    else:
        extra: tuple[str, ...]
        if kind == "standard":
            extra = ("position", "size")
        else:
            extra = ("alpha", "beta", "beta_initial", "beta_annealing", "priorities", "max_priority", "position", "size_current")
        _keys(state, (*base, *_ROWS, *_COMPONENTS, *extra), "archive.replay")
        empty_unallocated = count == 0 and all(state[key] is None for key in (*_ROWS, *_COMPONENTS))
        if not empty_unallocated and _validate_rows({key: state[key] for key in (*_ROWS, *_COMPONENTS)}, "archive.replay") != count:
            raise ValueError("archive replay row shape differs from retained count")
        position = _integer(state["position"], "archive.replay.position", 0)
        if position >= state["capacity"]:
            raise ValueError("archive replay position exceeds capacity")
        if kind == "standard" and position != count % state["capacity"]:
            raise ValueError("archive standard replay position differs from chronological retained rows")
        if kind == "prioritized":
            priorities = state["priorities"]
            if not isinstance(priorities, np.ndarray) or priorities.dtype != np.float32 or priorities.shape != (state["capacity"],):
                raise ValueError("archive priorities dtype/shape mismatch")
            if not np.isfinite(priorities).all() or (priorities < 0).any() or (priorities[:count] <= 0).any():
                raise ValueError("archive priorities must be finite, with positive retained values")
            for key in ("alpha", "beta", "beta_initial", "max_priority"):
                value = state[key]
                if type(value) not in (float, int) or not np.isfinite(value) or value < 0 or (key != "max_priority" and value > 1):
                    raise ValueError(f"archive replay.{key} is invalid")
            if state["max_priority"] <= 0 or type(state["beta_annealing"]) is not bool:
                raise ValueError("archive max_priority/beta_annealing is invalid")
    return count


class _Owned:
    __slots__ = ()

    def __getattribute__(self, name):
        value = object.__getattribute__(self, name)
        return _clone(value) if name in ("original_state", "source_formats", "restored_clocks", "available_learned_state") else value


def _own(instance, names) -> None:
    for name in names:
        object.__setattr__(instance, name, _clone(getattr(instance, name)))


@dataclass(frozen=True, slots=True)
class ArchiveExportReceipt:
    destination: Path
    source_digest: str
    row_count: int
    output_digest: str


@dataclass(frozen=True, slots=True)
class HistoricalReplayArchive(_Owned):
    source_formats: Mapping[str, object]
    original_state: Mapping[str, object]
    source_digest: str
    archived_row_count: int
    reward_semantics: str
    approval_reference: str

    def __post_init__(self) -> None:
        _own(self, ("source_formats", "original_state"))
        state, formats = self.original_state, self.source_formats
        if self.reward_semantics != REWARD_SEMANTICS or self.approval_reference != APPROVAL_REFERENCE:
            raise ValueError("archive reward semantics/approval differs from approved historical policy")
        count = _validate_archive_state(_mapping(state, "archive.original_state"), _mapping(formats, "archive.source_formats"))
        if count != _integer(self.archived_row_count, "archive.archived_row_count", 0):
            raise ValueError("archive row count differs from original state")
        if self.source_digest != _state_digest(state, formats):
            raise ValueError("archive source digest mismatch after owned cloning")

    def query_rows(self, *, offset: int, limit: int) -> Mapping[str, Tensor]:
        """Component values are recorded only where their ``*_present`` mask is true.

        Missing component positions carry zero placeholders under false masks;
        wholly missing selections omit the value tensor. These are inspection
        results, never qualified learner rows or reconstructed recorded rewards.
        """
        _integer(offset, "offset", 0)
        _integer(limit, "limit", 0)
        state = _mapping(self.original_state, "archive.original_state")
        selection = slice(offset, offset + limit)
        result: dict[str, Tensor]
        if state["replay_kind"] == "sequential":
            episodes = _mapping_sequence(state["episodes"], "archive.episodes")
            if not episodes:
                return {}
            result = {key: torch.cat([_tensor(episode[key], key) for episode in episodes])[selection].clone() for key in _ROWS}
            for key in _COMPONENTS:
                components, coverage = [], []
                for episode in episodes:
                    rewards = _tensor(episode["rewards"], "rewards")
                    if episode[key] is None:
                        components.append(torch.zeros_like(rewards))
                        coverage.append(torch.zeros_like(rewards, dtype=torch.bool))
                    else:
                        components.append(_tensor(episode[key], key))
                        coverage.append(torch.ones_like(rewards, dtype=torch.bool))
                present = torch.cat(coverage)[selection].clone()
                result[f"{key}_present"] = present
                if present.any():
                    result[key] = torch.cat(components)[selection].clone()
            ids = [
                torch.full((len(_tensor(episode["actions"], "actions")),), index, dtype=torch.int64)
                for index, episode in enumerate(episodes)
            ]
            result["episode_ids"] = torch.cat(ids)[selection].clone()
            return result
        if state["observations"] is None:
            return {}
        result = {key: _tensor(state[key], key)[selection].clone() for key in _ROWS}
        for key in _COMPONENTS:
            if state[key] is None:
                result[f"{key}_present"] = torch.zeros_like(result["rewards"], dtype=torch.bool)
            else:
                component = _tensor(state[key], key)[selection].clone()
                result[key] = component
                result[f"{key}_present"] = torch.ones_like(component, dtype=torch.bool)
        if "priorities" in state:
            result["priorities"] = torch.from_numpy(state["priorities"][: self.archived_row_count][selection].copy())
        return result

    def export(self, destination: Path) -> ArchiveExportReceipt:
        """Verify a durable temporary native artifact, then publish without clobber."""
        destination = Path(destination)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"archive export destination already exists: {destination}")
        descriptor, name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
        temporary = Path(name)
        published = False
        try:
            with os.fdopen(descriptor, "wb") as handle:
                torch.save(self.original_state, handle)
                handle.flush()
                os.fsync(handle.fileno())
            restored = torch.load(temporary, map_location="cpu", weights_only=False)
            if _state_digest(restored, self.source_formats) != self.source_digest:
                raise ValueError("archive exported state digest mismatch on readback")
            output_digest = "artifact-sha256:" + hashlib.sha256(temporary.read_bytes()).hexdigest()
            os.link(temporary, destination)
            published = True
            directory = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            return ArchiveExportReceipt(destination, self.source_digest, self.archived_row_count, output_digest)
        except BaseException:
            if published:
                destination.unlink()
            raise
        finally:
            temporary.unlink(missing_ok=True)


def archive_standalone_replay(state: Mapping[str, object]) -> HistoricalReplayArchive:
    """Archive a known pre-capture replay without claiming container provenance."""
    owned = _clone(_mapping(state, "standalone replay"))
    formats = {"scope": "standalone_replay", "replay": owned.get("format_version"), "replay_kind": owned.get("replay_kind")}
    count = _validate_archive_state(owned, formats)
    return HistoricalReplayArchive(formats, owned, _state_digest(owned, formats), count, REWARD_SEMANTICS, APPROVAL_REFERENCE)


@dataclass(frozen=True, slots=True)
class HistoricalAccessPolicy(_Owned):
    source_formats: Mapping[str, object]
    requested_mode: AccessMode
    effective_mode: AccessMode
    approval_reference: str | None
    archived_row_count: int
    active_retained_transitions: int
    restored_clocks: Mapping[str, object]
    guarantees: tuple[str, ...]
    legacy_identity_recipe: str

    def __post_init__(self) -> None:
        _own(self, ("source_formats", "restored_clocks"))
        formats = _mapping(self.source_formats, "policy.source_formats")
        _keys(formats, ("demo", "population", "replay", "replay_kind"), "policy.source_formats")
        kind = formats["replay_kind"]
        if type(kind) is not str or kind not in _KINDS or any(type(formats[key]) is not int for key in ("demo", "population", "replay")):
            raise ValueError("policy source formats are invalid")
        legacy = formats["demo"] == 9
        if not _supported_formats(formats["demo"], formats["population"], formats["replay"], kind):
            raise ValueError("policy source format versions are unsupported")
        if self.requested_mode not in _MODES or self.effective_mode not in _MODES[1:]:
            raise ValueError("historical policy requested/effective mode is invalid")
        _integer(self.archived_row_count, "policy.archived_row_count", 0)
        _integer(self.active_retained_transitions, "policy.active_retained_transitions", 0)
        if self.approval_reference not in (None, APPROVAL_REFERENCE):
            raise ValueError("historical policy approval reference is invalid")
        if self.requested_mode == "inference":
            expected_mode = "inference"
        elif legacy:
            expected_mode = "archived_history_fresh_episode"
        else:
            expected_mode = "recorded_full_resume"
        if self.effective_mode != expected_mode or (legacy and self.requested_mode == "recorded_full_resume"):
            raise ValueError("historical policy mode disagrees with source formats")
        if not legacy and self.requested_mode == "archived_history_fresh_episode":
            raise ValueError("current policy cannot discard qualified active replay")
        if (legacy or self.archived_row_count) and self.approval_reference != APPROVAL_REFERENCE:
            raise ValueError("historical policy lacks its approved archive reference")
        if legacy and self.active_retained_transitions != 0:
            raise ValueError("historical policy cannot retain unrecorded active replay")
        if not isinstance(self.guarantees, tuple) or any(not isinstance(item, str) for item in self.guarantees):
            raise ValueError("historical policy guarantees must be a tuple of strings")
        if not isinstance(self.legacy_identity_recipe, str) or not self.legacy_identity_recipe:
            raise ValueError("historical policy identity recipe is missing")
        for key, value in _mapping(self.restored_clocks, "policy.restored_clocks").items():
            _integer(value, f"policy.restored_clocks.{key}", 0)


@dataclass(frozen=True, slots=True)
class HistoricalPreparedEnvelope(_Owned):
    policy: HistoricalAccessPolicy
    archives: tuple[HistoricalReplayArchive, ...]
    available_learned_state: Mapping[str, object]

    def __post_init__(self) -> None:
        _own(self, ("available_learned_state",))
        _mapping(self.available_learned_state, "envelope.available_learned_state")
        if not isinstance(self.policy, HistoricalAccessPolicy) or not isinstance(self.archives, tuple):
            raise ValueError("historical envelope policy/archives types are invalid")
        if any(not isinstance(archive, HistoricalReplayArchive) for archive in self.archives):
            raise ValueError("historical envelope contains an invalid archive")
        if sum(archive.archived_row_count for archive in self.archives) != self.policy.archived_row_count:
            raise ValueError("historical envelope archive row counts differ from policy")
        if self.policy.source_formats.get("demo") == 9:
            if len(self.archives) != 1 or self.archives[0].source_formats != self.policy.source_formats:
                raise ValueError("historical envelope archive source formats differ from policy")
            population = _mapping(self.available_learned_state.get("population_state"), "envelope.population_state")
            if self.policy.active_retained_transitions != 0 or "replay_buffer" in population:
                raise ValueError("historical envelope cannot retain pre-capture rows in active replay")


def _archive_from_state(state: Mapping) -> HistoricalReplayArchive:
    state = _mapping(state, "embedded archive")
    _keys(state, (field.name for field in fields(HistoricalReplayArchive)), "embedded archive")
    return HistoricalReplayArchive(**state)


def _embedded_archives(payload: Mapping) -> tuple[HistoricalReplayArchive, ...]:
    if "historical_archives" not in payload:
        return ()
    records = _mapping_sequence(payload["historical_archives"], "historical_archives")
    return tuple(_archive_from_state(record) for record in records)


def _validate_empty_current_uniform(replay: Mapping) -> None:
    """Admit only the unallocated empty representation emitted by uniform5."""
    tensor_fields = (*_ROWS, *_COMPONENTS, "next_action_masks", "legality_recorded", *(f"{name}_present" for name in _COMPONENTS))
    _keys(
        replay,
        (
            "replay_kind",
            "format_version",
            "capacity",
            "size",
            "position",
            "action_dim",
            "legality_mode",
            "historical_archives",
            *tensor_fields,
        ),
        "empty current uniform replay",
    )
    if _integer(replay["position"], "replay.position", 0) != 0:
        raise ValueError("empty current uniform replay position must be zero")
    if replay["action_dim"] is not None or type(replay["legality_mode"]) is not str or replay["legality_mode"] != "unconstrained":
        raise ValueError("empty current uniform replay cannot claim captured action metadata")
    if any(replay[name] is not None for name in tensor_fields):
        raise ValueError("empty current uniform replay tensor fields must be null")
    if not isinstance(replay["historical_archives"], list):
        raise ValueError("empty current uniform replay historical_archives must be a list")
    for archive in _embedded_archives(replay):
        if archive.source_formats["replay_kind"] != "standard":
            raise ValueError("uniform replay contains an incompatible historical archive kind")


def resolve_historical_access(payload: Mapping[str, object], *, requested_mode: AccessMode) -> HistoricalAccessPolicy:
    if requested_mode not in _MODES:
        raise ValueError("requested_mode is unsupported")
    formats, population, replay = _formats(payload)
    count = _count(replay)
    legacy = formats["demo"] == 9
    effective: AccessMode
    if legacy:
        _validate_archive_state(replay, formats)
        if requested_mode == "recorded_full_resume":
            raise HistoricalLegalityUnavailable(
                f"missing historical successor masks; use archived_history_fresh_episode under {APPROVAL_REFERENCE}"
            )
        if requested_mode == "inference":
            effective = "inference"
        else:
            effective = "archived_history_fresh_episode"
        archived, active = count, 0
    else:
        if requested_mode == "archived_history_fresh_episode":
            raise ValueError("current captured replay requires recorded_full_resume or inference")
        episodes: tuple[Mapping, ...]
        if formats["replay_kind"] == "standard" and count == 0:
            _validate_empty_current_uniform(replay)
            episodes = ()
        elif formats["replay_kind"] == "sequential":
            episodes = _mapping_sequence(replay.get("episodes"), "replay.episodes")
        else:
            episodes = (replay,)
        for index, rows in enumerate(episodes):
            rows = _mapping(rows, f"replay.rows[{index}]")
            dones, masks, recorded = rows.get("dones"), rows.get("next_action_masks"), rows.get("legality_recorded")
            if not isinstance(recorded, Tensor) or recorded.dtype != torch.bool or not recorded.all():
                raise HistoricalLegalityUnavailable(f"replay.rows[{index}] contains unrecorded successor legality")
            if not isinstance(masks, Tensor) or masks.ndim != 2 or not isinstance(dones, Tensor) or recorded.shape != dones.shape:
                raise ValueError(f"replay.rows[{index}] successor mask/recorded shapes are invalid")
            if formats["replay_kind"] == "standard":
                if dones.shape != (count,):
                    raise ValueError("current uniform replay row count differs from its retained count")
                if _integer(rows.get("position"), "replay.position", 0) != count % replay["capacity"]:
                    raise ValueError("current uniform replay position differs from chronological retained rows")
            validate_successor_masks(masks, dones, action_dim=_integer(payload.get("action_dim"), "action_dim", 1))
        archived = sum(archive.archived_row_count for archive in _embedded_archives(payload))
        active = count
        if requested_mode == "inference":
            effective = "inference"
        else:
            effective = "recorded_full_resume"
    clocks = {key: payload[key] for key in ("episode", "completed_live_agent_steps") if key in payload}
    clocks.update({key: population[key] for key in ("total_steps", "training_step_counter") if key in population})
    guarantees: tuple[str, ...] = (
        "archive rows have no sampler or optimizer route",
        "source clocks do not establish active replay readiness",
    )
    approval: str | None
    if legacy or archived:
        approval = APPROVAL_REFERENCE
    else:
        approval = None
    if legacy:
        guarantees += ("source provider was AdaptiveIntrinsicExploration", "unrecorded successor masks and RND tails/RNG are unavailable")
        recipe = "format9:brain-sorted-json;training-pydantic-json;five-training-overrides"
    else:
        recipe = "current-captured"
    return HistoricalAccessPolicy(
        formats,
        requested_mode,
        effective,
        approval,
        archived,
        active,
        clocks,
        guarantees,
        recipe,
    )


def prepare_historical_envelope(
    payload: Mapping[str, object], *, requested_mode: AccessMode, validate_legacy: Callable[[Mapping[str, object]], None]
) -> HistoricalPreparedEnvelope:
    owned = _clone(_mapping(payload, "checkpoint"))
    policy = resolve_historical_access(owned, requested_mode=requested_mode)
    archives: tuple[HistoricalReplayArchive, ...]
    if policy.source_formats["demo"] == 9:
        validate_legacy(owned)
        replay = owned["population_state"].pop("replay_buffer")
        archive = HistoricalReplayArchive(
            policy.source_formats,
            replay,
            _state_digest(replay, policy.source_formats),
            policy.archived_row_count,
            REWARD_SEMANTICS,
            APPROVAL_REFERENCE,
        )
        archives = (archive,)
    else:
        archives = _embedded_archives(owned)
    return HistoricalPreparedEnvelope(policy, archives, owned)


def _record(value) -> dict:
    return {field.name: _clone(getattr(value, field.name)) for field in fields(value)}


def encode_historical_envelope(envelope: HistoricalPreparedEnvelope) -> Mapping[str, object]:
    """Embed complete owned state; mapping input supplies no file-byte provenance."""
    return {
        "schema_version": 1,
        "policy": _record(envelope.policy),
        "archives": [_record(archive) for archive in envelope.archives],
        "available_learned_state": envelope.available_learned_state,
    }


def decode_historical_envelope(state: Mapping[str, object]) -> HistoricalPreparedEnvelope:
    state = _mapping(state, "historical envelope")
    _keys(state, ("schema_version", "policy", "archives", "available_learned_state"), "historical envelope")
    if type(state["schema_version"]) is not int or state["schema_version"] != 1:
        raise ValueError("unsupported historical envelope schema_version")
    policy = _mapping(state["policy"], "historical policy")
    _keys(policy, (field.name for field in fields(HistoricalAccessPolicy)), "historical policy")
    archives = _mapping_sequence(state["archives"], "historical envelope archives")
    learned = _mapping(state["available_learned_state"], "historical envelope available_learned_state")
    return HistoricalPreparedEnvelope(HistoricalAccessPolicy(**policy), tuple(_archive_from_state(item) for item in archives), learned)


def _training9(training) -> TrainingV2Config:
    if isinstance(training, BaseModel):
        raw = training.model_dump()
    else:
        raw = dict(_mapping(training, "format9.training"))
    if raw.get("bac_options") is not None:
        raise ValueError("format9 identity cannot attest explicitly selected bac_options")
    return TrainingV2Config.model_validate(raw)


def format9_training_hash(training) -> str:
    """The old compiler's Pydantic JSON recipe, excluding only absent new options."""
    canonical = _training9(training).model_dump_json(exclude={"bac_options"})
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def format9_brain_hash(brain, *, training) -> str:
    """Exact old sorted JSON brain recipe, including the five old overrides."""
    if isinstance(brain, BaseModel):
        raw = brain.model_dump()
    else:
        raw = _clone(_mapping(brain, "format9.brain"))
    architecture = _mapping(raw.get("architecture"), "format9.brain.architecture")
    for key in ("token_set", "recurrent"):
        section = architecture.get(key)
        if isinstance(section, Mapping) and section.get("token_encoder") is not None:
            raise ValueError(f"format9 identity cannot attest explicit architecture.{key}.token_encoder")
    model = BrainConfig.model_validate(raw)
    if training is not None:
        model = apply_training_overrides(model, _training9(training))
    canonical = model.model_dump()
    for key in ("token_set", "recurrent"):
        if canonical["architecture"][key] is not None:
            canonical["architecture"][key].pop("token_encoder", None)
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, indent=None).encode("utf-8")).hexdigest()
