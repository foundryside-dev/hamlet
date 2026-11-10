"""Current authored world declarations and immutable lifecycle value records.

This module owns data only. ENV owns issuance, acceptance and all live cursors.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

import torch


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def exact_integer(value: Any, minimum: int, name: str) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} requires an integer >= {minimum}")
    return value


def exact_world_ids(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)) or not value:
        raise ValueError("world IDs require a nonempty ordered sequence")
    if any(not isinstance(item, str) or not item for item in value):
        raise ValueError("world IDs require exact nonempty strings")
    if len(set(value)) != len(value):
        raise ValueError("world IDs must be unique")
    return tuple(value)


def world_binding(world_ids: tuple[str, ...]) -> dict[str, Any]:
    values = {"schema": "world-binding-v1", "world_ids": list(exact_world_ids(world_ids))}
    return {**values, "hash": canonical_hash(values)}


@dataclass(frozen=True)
class WorldRosterDeclaration:
    world_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "world_ids", exact_world_ids(self.world_ids))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> WorldRosterDeclaration:
        if not isinstance(payload, Mapping) or set(payload) != {"schema", "world_ids"}:
            raise ValueError("world roster requires exact current fields")
        if payload["schema"] != "world-roster-v1" or not isinstance(payload["world_ids"], list):
            raise ValueError("world roster requires current schema and serialized ID list")
        return cls(exact_world_ids(payload["world_ids"]))

    def to_dict(self) -> dict[str, Any]:
        return {"schema": "world-roster-v1", "world_ids": list(self.world_ids)}

    @property
    def semantic_identity(self) -> str:
        return canonical_hash({"schema": "world-membership-v1", "world_ids": sorted(self.world_ids)})

    @property
    def manifest_digest(self) -> str:
        return hashlib.sha256(canonical_bytes(self.to_dict()) + b"\n").hexdigest()


@dataclass(frozen=True, eq=False)
class WorldEpisodeReservation:
    world_ids: tuple[str, ...]
    world_episode_seqs: tuple[int, ...]
    batch_episode: int
    _owner: object
    _generation: int
    _release: WorldRecord


@dataclass(frozen=True, eq=False)
class WorldAcceptedEpisode:
    world_ids: tuple[str, ...]
    world_episode_seqs: tuple[int, ...]
    batch_episode: int
    _owner: object
    _generation: int


@dataclass(frozen=True, eq=False)
class WorldRecord:
    """Owned data with in-process capability identity; never serialize the owner."""

    kind: str
    _owner: object
    _generation: int
    _payload: Mapping[str, Any]

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        payload = object.__getattribute__(self, "_payload")
        if name not in payload:
            raise AttributeError(name)
        return owned_value(payload[name])

    @property
    def payload(self) -> dict[str, Any]:
        return {key: owned_value(value) for key, value in self._payload.items()}


@dataclass(frozen=True, eq=False)
class WorldOwnerReceipt(WorldRecord):
    _issuer: object

    @property
    def owner(self) -> object:
        return self._owner


class _FrozenList(tuple):
    """Preserve portable list shape while owning immutable internal storage."""


def owned_value(value: Any) -> Any:
    """Copy mutable values while preserving already-issued opaque capabilities."""
    if isinstance(value, (WorldRecord, WorldEpisodeReservation, WorldAcceptedEpisode)):
        return value
    if isinstance(value, torch.Tensor):
        return value.detach().clone()
    if isinstance(value, Mapping):
        return {key: owned_value(item) for key, item in value.items()}
    if isinstance(value, _FrozenList):
        return [owned_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(owned_value(item) for item in value)
    if isinstance(value, list):
        return [owned_value(item) for item in value]
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise ValueError(f"unsupported world receipt value: {type(value).__name__}")


def frozen_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("receipt mappings require string keys")
        return MappingProxyType({key: frozen_value(item) for key, item in value.items()})
    if isinstance(value, list):
        return _FrozenList(frozen_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(frozen_value(item) for item in value)
    return owned_value(value)


def same_value(left: Any, right: Any) -> bool:
    if isinstance(left, torch.Tensor):
        return (
            isinstance(right, torch.Tensor)
            and left.dtype == right.dtype
            and left.device == right.device
            and left.shape == right.shape
            and torch.equal(left, right)
        )
    if isinstance(left, Mapping):
        return isinstance(right, Mapping) and left.keys() == right.keys() and all(same_value(left[key], right[key]) for key in left)
    if isinstance(left, (tuple, list)):
        return (
            isinstance(right, (tuple, list)) and len(left) == len(right) and all(same_value(a, b) for a, b in zip(left, right, strict=True))
        )
    if isinstance(left, WorldOwnerReceipt):
        return (
            isinstance(right, WorldOwnerReceipt)
            and left.owner is right.owner
            and left.kind == right.kind
            and same_value(left.payload, right.payload)
        )
    if isinstance(left, (WorldRecord, WorldEpisodeReservation, WorldAcceptedEpisode)):
        return left is right
    return type(left) is type(right) and left == right


def validate_world_snapshot(
    state: Mapping[str, Any], kind: str, roster: WorldRosterDeclaration, seed: int, semantic_identity: str
) -> dict[str, Any]:
    """Pure current-native structure and available accepted-history validation."""
    keys = {
        "schema",
        "kind",
        "next_batch_episode",
        "world_roster",
        "manifest_digest",
        "roster_semantic_identity",
        "training_seed",
        "execution_identity",
        "saved_lane_binding",
        "destination_lane_binding",
        "accepted_episode_seqs",
        "last_closed_episode",
        "completed_boundary_key",
        "accepted_bindings",
    }
    if not isinstance(state, Mapping) or set(state) != keys or state["schema"] != "world-lifecycle-v3":
        raise ValueError("world snapshot requires exact current schema")
    if kind not in ("INITIAL", "COMPLETED") or state["kind"] != kind:
        raise ValueError("world snapshot requires matching explicit kind")
    if (
        state["world_roster"] != roster.to_dict()
        or state["manifest_digest"] != roster.manifest_digest
        or state["roster_semantic_identity"] != roster.semantic_identity
        or state["execution_identity"] != semantic_identity
    ):
        raise ValueError("world snapshot declaration or semantic identity disagrees")
    if exact_integer(state["training_seed"], 0, "training seed") != seed:
        raise ValueError("world snapshot training seed disagrees")
    next_batch = exact_integer(state["next_batch_episode"], 0, "next batch")
    membership = set(roster.world_ids)

    def binding(value: Any) -> tuple[str, ...]:
        if not isinstance(value, Mapping) or set(value) != {"schema", "world_ids", "hash"}:
            raise ValueError("world binding requires exact fields")
        ids = exact_world_ids(value["world_ids"])
        if set(ids) != membership or value != world_binding(ids):
            raise ValueError("world binding integrity disagrees")
        return ids

    binding(state["destination_lane_binding"])
    cursors = state["accepted_episode_seqs"]
    if not isinstance(cursors, Mapping) or set(cursors) != membership:
        raise ValueError("accepted cursors must cover declared membership")
    for sequence in cursors.values():
        exact_integer(sequence, 0, "accepted sequence")
    if len(set(cursors.values())) != 1:
        raise ValueError("current full-roster histories cannot create unequal accepted cursors")
    history = state["accepted_bindings"]
    if not isinstance(history, list):
        raise ValueError("accepted binding history requires a list")
    if kind == "INITIAL":
        if (
            any(cursors.values())
            or history
            or state["last_closed_episode"] is not None
            or state["completed_boundary_key"] is not None
            or state["saved_lane_binding"] is not None
        ):
            raise ValueError("INITIAL cannot contain accepted or completed history")
        return {key: owned_value(value) for key, value in state.items()}
    batch = exact_integer(state["completed_boundary_key"], 0, "completed boundary")
    if next_batch != batch + 1 or not all(cursors.values()):
        raise ValueError("completed next batch or accepted cursors disagree")
    saved_ids = binding(state["saved_lane_binding"])
    previous_batch, previous_sequence = None, None
    for item in history:
        if not isinstance(item, Mapping) or set(item) != {"batch_episode", "world_ids", "world_episode_seqs"}:
            raise ValueError("accepted binding requires exact fields")
        item_batch = exact_integer(item["batch_episode"], 0, "historical batch")
        ids = exact_world_ids(item["world_ids"])
        sequences = item["world_episode_seqs"]
        if set(ids) != membership or not isinstance(sequences, list) or len(sequences) != len(ids):
            raise ValueError("historical binding membership or sequence shape disagrees")
        for sequence in sequences:
            exact_integer(sequence, 1, "historical sequence")
        if len(set(sequences)) != 1 or item_batch > batch or sequences[0] > item_batch + 1:
            raise ValueError("unsupported historical cursor provenance")
        if previous_batch is not None:
            assert previous_sequence is not None
            if item_batch <= previous_batch or sequences[0] - previous_sequence != item_batch - previous_batch:
                raise ValueError("historical accepted sequence progression disagrees")
        previous_batch, previous_sequence = item_batch, sequences[0]
    last = state["last_closed_episode"]
    if not isinstance(last, Mapping) or set(last) != {
        "batch_episode",
        "world_ids",
        "world_episode_seqs",
        "completion_content",
        "participated_world_ids",
    }:
        raise ValueError("completed snapshot requires exact last closure")
    exact_integer(last["batch_episode"], 0, "last closure batch")
    if not isinstance(last["world_ids"], list) or not isinstance(last["world_episode_seqs"], list):
        raise ValueError("last closure identities require serialized lists")
    exact_world_ids(last["world_ids"])
    if len(last["world_episode_seqs"]) != len(last["world_ids"]):
        raise ValueError("last closure sequence shape disagrees")
    for sequence in last["world_episode_seqs"]:
        exact_integer(sequence, 1, "last closure sequence")
    if not history or history[-1]["batch_episode"] != batch or last["batch_episode"] != batch:
        raise ValueError("missing last accepted binding provenance")
    for name in ("world_ids", "world_episode_seqs"):
        if last[name] != history[-1][name]:
            raise ValueError("last closure contradicts accepted provenance")
    if tuple(last["world_ids"]) != saved_ids or dict(zip(saved_ids, last["world_episode_seqs"], strict=True)) != cursors:
        raise ValueError("last saved binding contradicts current cursors")
    if not set(exact_world_ids(last["participated_world_ids"])).issubset(membership):
        raise ValueError("last closure participants are not declared worlds")
    return {key: owned_value(value) for key, value in state.items()}
