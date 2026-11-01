"""Portable ownership and exact-WorldId seed contracts, without a runtime bank.

Private seed inputs deliberately exclude lane order, population, model parameters
and all clocks. Actual mutable state/RNG installation belongs to the bank owner.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal

from townlet.config.exploration_policy import STRATEGIES, ResolvedExplorationPolicy, Strategy

WORLD_SEED_COMPONENTS = ("model_init", "target", "predictor", "service")


def _hash(record: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(dict(record), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _integer(value: Any, name: str, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name}: expected integer >= {minimum}")


def _nonempty(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name}: expected exact nonempty string")


def derive_world_seed(*, training_seed: int, world_id: str, provider_kind: str, component: str) -> int:
    """Versioned canonical KDF over only the four declared ownership inputs."""
    _integer(training_seed, "training_seed", 0)
    _nonempty(world_id, "world_id")
    _nonempty(component, "component")
    if provider_kind not in STRATEGIES:
        raise ValueError("provider_kind: unsupported curiosity provider")
    digest = _hash(
        {
            "schema": "world-curiosity-seed-v1",
            "training_seed": training_seed,
            "world_id": world_id,
            "provider_kind": provider_kind,
            "component": component,
        }
    )
    return int(digest[:16], 16) & (2**63 - 1)


@dataclass(frozen=True)
class WorldCuriosityDescriptor:
    """Immutable declared geometry, ID binding and canonical ID-keyed streams.

    Equal descriptors never own shared mutable storage. Shared mode records its
    legacy stream ownership; it does not pretend to derive private world seeds.
    """

    schema_version: Literal[1]
    scope: Literal["shared", "per_world"]
    provider_kind: Strategy
    provider_parameter_hash: str
    observation_dim: int
    action_dim: int
    world_ids: tuple[str, ...]
    seed_policy: Literal["legacy_shared_v1", "world_id_derived_v1"]
    service_clock_unit: Literal["vector_tick", "world_eligible_admission"]
    origin: Literal["authored", "bac-options-v1"]
    guarantee: Literal["shared_population_state", "world_id_owned_state"]
    training_seed: int
    seeds: Mapping[str, Mapping[str, int]]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported world curiosity descriptor schema")
        if self.scope not in ("shared", "per_world") or self.provider_kind not in STRATEGIES:
            raise ValueError("invalid world curiosity scope/provider")
        expected = ("legacy_shared_v1", "vector_tick", "shared_population_state")
        if self.scope == "per_world":
            expected = ("world_id_derived_v1", "world_eligible_admission", "world_id_owned_state")
        if (self.seed_policy, self.service_clock_unit, self.guarantee) != expected:
            raise ValueError("world curiosity descriptor ownership/seed/clock guarantee disagrees")
        if self.origin not in ("authored", "bac-options-v1"):
            raise ValueError("invalid world curiosity origin")
        if self.scope == "per_world" and self.origin != "authored":
            raise ValueError("private curiosity requires an explicit declaration")
        if (
            not isinstance(self.provider_parameter_hash, str)
            or len(self.provider_parameter_hash) != 64
            or any(char not in "0123456789abcdef" for char in self.provider_parameter_hash)
        ):
            raise ValueError("provider_parameter_hash must be a canonical SHA256")
        _integer(self.observation_dim, "observation_dim", 0)
        _integer(self.action_dim, "action_dim", 1)
        _integer(self.training_seed, "training_seed", 0)
        if not isinstance(self.world_ids, (tuple, list)) or any(not isinstance(item, str) for item in self.world_ids):
            raise ValueError("world_ids must contain exact strings")
        world_ids = tuple(self.world_ids)
        if self.scope == "per_world":
            if not world_ids or any(not item for item in world_ids):
                raise ValueError("strict world IDs must be nonempty")
            if len(set(world_ids)) != len(world_ids):
                raise ValueError("duplicate strict world IDs")
        object.__setattr__(self, "world_ids", world_ids)
        if not isinstance(self.seeds, Mapping):
            raise ValueError("seeds must be an ID-keyed mapping")
        if self.scope == "per_world":
            required = set(world_ids)
        else:
            required = set()
        if set(self.seeds) != required:
            raise ValueError("seeds must match the exact private world IDs")
        owned: dict[str, Mapping[str, int]] = {}
        for world_id in sorted(required):
            streams = self.seeds[world_id]
            if not isinstance(streams, Mapping) or set(streams) != set(WORLD_SEED_COMPONENTS):
                raise ValueError("seeds must persist every named private stream")
            for component, seed in streams.items():
                _integer(seed, f"seeds.{world_id}.{component}", 0)
                if seed != derive_world_seed(
                    training_seed=self.training_seed, world_id=world_id, provider_kind=self.provider_kind, component=component
                ):
                    raise ValueError("persisted world seed disagrees with versioned derivation")
            owned[world_id] = MappingProxyType(dict(streams))
        object.__setattr__(self, "seeds", MappingProxyType(owned))

    @property
    def canonical_world_ids(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.world_ids)))

    @property
    def world_binding_hash(self) -> str:
        """Runtime row binding, kept separate from compiled policy identity."""
        return _hash({"schema": "world-curiosity-binding-v1", "world_ids": list(self.world_ids)})

    def seed_for(self, world_id: str, component: str) -> int:
        if self.scope != "per_world":
            raise ValueError("shared curiosity retains its legacy shared RNG ownership")
        if world_id not in self.seeds or component not in self.seeds[world_id]:
            raise ValueError("unknown exact world ID or private seed component")
        return self.seeds[world_id][component]

    @classmethod
    def from_policy(
        cls,
        policy: ResolvedExplorationPolicy,
        *,
        world_ids: tuple[str, ...],
        observation_dim: int,
        action_dim: int,
        training_seed: int,
    ) -> WorldCuriosityDescriptor:
        seeds = {}
        if policy.curiosity_scope == "per_world":
            # Validate before constructing a map so duplicate IDs cannot vanish.
            if not isinstance(world_ids, (tuple, list)):
                raise ValueError("strict world IDs require an ordered sequence")
            for world_id in world_ids:
                _nonempty(world_id, "world_id")
            if len(set(world_ids)) != len(world_ids):
                raise ValueError("duplicate strict world IDs")
            seeds = {
                world_id: {
                    component: derive_world_seed(
                        training_seed=training_seed, world_id=world_id, provider_kind=policy.strategy, component=component
                    )
                    for component in WORLD_SEED_COMPONENTS
                }
                for world_id in world_ids
            }
        return cls(
            schema_version=1,
            scope=policy.curiosity_scope,
            provider_kind=policy.strategy,
            provider_parameter_hash=_hash(dict(policy.provider_parameters)),
            observation_dim=observation_dim,
            action_dim=action_dim,
            world_ids=world_ids,
            seed_policy=policy.seed_policy,
            service_clock_unit=policy.service_clock_unit,
            origin=policy.scope_origin,
            guarantee=policy.scope_guarantee,
            training_seed=training_seed,
            seeds=seeds,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scope": self.scope,
            "provider_kind": self.provider_kind,
            "provider_parameter_hash": self.provider_parameter_hash,
            "observation_dim": self.observation_dim,
            "action_dim": self.action_dim,
            "world_ids": list(self.world_ids),
            "canonical_world_ids": list(self.canonical_world_ids),
            "world_binding_hash": self.world_binding_hash,
            "seed_policy": self.seed_policy,
            "service_clock_unit": self.service_clock_unit,
            "origin": self.origin,
            "guarantee": self.guarantee,
            "training_seed": self.training_seed,
            "seeds": {world_id: dict(streams) for world_id, streams in self.seeds.items()},
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> WorldCuriosityDescriptor:
        required = set(
            "schema_version scope provider_kind provider_parameter_hash observation_dim action_dim world_ids canonical_world_ids "
            "world_binding_hash seed_policy service_clock_unit origin guarantee training_seed seeds".split()
        )
        if set(payload) != required:
            raise ValueError("world curiosity descriptor requires a complete versioned field set")
        values = dict(payload)
        binding = values.pop("world_binding_hash")
        canonical = values.pop("canonical_world_ids")
        result = cls(**values)
        if canonical != list(result.canonical_world_ids) or binding != result.world_binding_hash:
            raise ValueError("world curiosity descriptor ID binding disagrees")
        return result
