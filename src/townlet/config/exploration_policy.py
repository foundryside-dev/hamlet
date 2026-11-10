"""Authored exploration policy and the current delegated runtime boundary.

Execution identity hashes resolved active behavior only. Authored identity retains
presets and provenance separately. Runtime producers are imported at construction.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass, fields, replace
from functools import wraps
from threading import RLock
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast

import torch
from torch import Tensor

from townlet.config.bac_options import BaCOptions, CuriosityScopeOptions, resolve_bac_options, resolve_curiosity_scope
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.training_v2_config import TrainingV2Config

if TYPE_CHECKING:
    from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration

Strategy = Literal["none", "rnd", "adaptive_rnd", "count_based", "icm"]
STRATEGIES = ("none", "rnd", "adaptive_rnd", "count_based", "icm")
SCOPE_FIELDS = frozenset(("curiosity_scope", "seed_policy", "service_clock_unit", "scope_origin", "scope_guarantee"))
SCOPE_UNITS = {
    "curiosity_scope": "ownership_scope",
    "seed_policy": "seed_derivation_version",
    "service_clock_unit": "service_opportunity_unit",
    "scope_origin": "declaration_origin",
    "scope_guarantee": "ownership_guarantee",
}


def _scope_values(options: CuriosityScopeOptions | None) -> dict[str, str]:
    selected, origin = resolve_curiosity_scope(options)
    return {
        "curiosity_scope": selected.scope,
        "seed_policy": str(selected.seed_policy),
        "service_clock_unit": "world_eligible_admission" if selected.scope == "per_world" else "vector_tick",
        "scope_origin": origin,
        "scope_guarantee": "world_id_owned_state" if selected.scope == "per_world" else "shared_population_state",
    }


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("exploration authoring mappings require string keys")
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if value is None or isinstance(value, (str, bool, int, float, FieldRole)):
        return value
    raise ValueError(f"exploration authoring requires portable values, got {type(value).__name__}")


def _portable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _portable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_portable(item) for item in value]
    if isinstance(value, FieldRole):
        return {"status": value.status, "origin": value.origin, "reason": value.reason}
    return value


def _identity(value: Any) -> str:
    return hashlib.sha256(json.dumps(_portable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _provider_schema(strategy: Strategy) -> dict[str, str | None]:
    """Required selected keys and their duplicate scalar names, if any."""
    schema: dict[str, str | None] = {}
    if strategy in ("rnd", "adaptive_rnd"):
        schema = {"feature_dim": "rnd_feature_dim", "learning_rate": "rnd_learning_rate", "predictor_batch_size": "predictor_batch_size"}
        if strategy == "adaptive_rnd":
            for name in (
                "min_intrinsic_weight",
                "variance_threshold",
                "min_survival_fraction",
                "max_episode_length",
                "survival_window",
                "decay_rate",
            ):
                schema[name] = name
    elif strategy == "count_based":
        schema = {"quantization_width": None, "max_entries": None}
    elif strategy == "icm":
        schema = {
            "feature_dim": None,
            "hidden_dim": None,
            "learning_rate": None,
            "inverse_weight": None,
            "forward_weight": None,
            "training_batch_size": "predictor_batch_size",
            "max_pending_transitions": "max_pending_rows",
        }
    return schema


def _active_policy_fields(strategy: Strategy) -> set[str]:
    """Schema owns execution activity; transported annotations cannot redefine it."""
    active = {
        "strategy",
        "epsilon_start",
        "epsilon_end",
        "epsilon_decay",
        "provider_parameters",
        "reward_observation_phase",
        "predictor_observation_phase",
        "predictor_input_kind",
    }
    active.update(SCOPE_FIELDS)
    if strategy != "none":
        active.update(("initial_intrinsic_weight", "drive_base_weight", "modifier_names"))
    if strategy in ("rnd", "adaptive_rnd"):
        active.add("provider_parameter_source")
    if strategy in ("rnd", "adaptive_rnd", "icm"):
        active.update(("service_mode", "max_updates_per_tick", "max_pending_rows", "overflow_policy"))
    active.update(scalar for scalar in _provider_schema(strategy).values() if scalar is not None)
    return active


@dataclass(frozen=True)
class FieldRole:
    status: Literal["active", "inactive_preset", "derived", "unqualified"]
    origin: str
    reason: str

    def __post_init__(self) -> None:
        if self.status not in ("active", "inactive_preset", "derived", "unqualified"):
            raise ValueError("invalid exploration FieldRole.status")


@dataclass(frozen=True)
class ResolvedExplorationPolicy:
    strategy: Strategy
    epsilon_start: float
    epsilon_end: float
    epsilon_decay: float
    rnd_feature_dim: int
    rnd_learning_rate: float
    predictor_batch_size: int
    initial_intrinsic_weight: float
    min_intrinsic_weight: float
    variance_threshold: float
    min_survival_fraction: float
    max_episode_length: int
    survival_window: int
    decay_rate: float
    drive_base_weight: float
    modifier_names: tuple[str, ...]
    provider_parameters: Mapping[str, Any]
    reward_observation_phase: Literal["successor_postphysics"]
    predictor_observation_phase: Literal["eligible_predecessor"]
    predictor_input_kind: Literal["observation", "transition"]
    field_roles: Mapping[str, FieldRole]
    service_mode: Literal["occupancy_fifo", "paced_fifo"]
    max_updates_per_tick: int
    max_pending_rows: int
    overflow_policy: Literal["service_before_admit", "drop_oldest", "drop_newest"]
    provider_parameter_source: Literal["training", "drive"]
    raw_provider_parameters: Mapping[str, Any]
    authored_parameters: Mapping[str, Any]
    parameter_units: Mapping[str, str]
    curiosity_scope: Literal["shared", "per_world"]
    seed_policy: Literal["legacy_shared_v1", "world_id_derived_v1"]
    service_clock_unit: Literal["vector_tick", "world_eligible_admission"]
    scope_origin: Literal["authored", "bac-options-v1"]
    scope_guarantee: Literal["shared_population_state", "world_id_owned_state"]

    def __post_init__(self) -> None:
        if self.strategy not in STRATEGIES:
            raise ValueError("invalid exploration strategy")
        for name in ("provider_parameters", "raw_provider_parameters", "authored_parameters", "field_roles", "parameter_units"):
            object.__setattr__(self, name, _freeze(getattr(self, name)))
        authored_options = self.authored_parameters.get("bac_options")
        if not isinstance(authored_options, Mapping):
            raise ValueError("authored_parameters.bac_options requires captured authoring")
        declaration = None
        if "curiosity_scope" in authored_options:
            if not isinstance(authored_options["curiosity_scope"], Mapping):
                raise ValueError("authored curiosity_scope must be a complete declaration")
            declaration = CuriosityScopeOptions.model_validate(dict(authored_options["curiosity_scope"]))
        expected_scope = _scope_values(declaration)
        for name, expected in expected_scope.items():
            if getattr(self, name) != expected:
                raise ValueError(f"{name}: disagrees with authored curiosity ownership")
            if self.parameter_units.get(name) != SCOPE_UNITS[name]:
                raise ValueError(f"parameter_units.{name}: invalid ownership unit")
        expected_update_unit = "predictor_minibatches/vector_tick"
        if self.curiosity_scope == "per_world":
            expected_update_unit = "predictor_minibatches/world_eligible_admission"
        if self.parameter_units.get("max_updates_per_tick") != expected_update_unit:
            raise ValueError("parameter_units.max_updates_per_tick: disagrees with service clock")
        object.__setattr__(self, "modifier_names", tuple(self.modifier_names))
        for name in ("epsilon_start", "epsilon_end", "epsilon_decay", "initial_intrinsic_weight", "drive_base_weight"):
            _number(getattr(self, name), name, False, 0.0)
        if self.epsilon_end > self.epsilon_start or self.epsilon_start > 1 or not 0 < self.epsilon_decay < 1:
            raise ValueError("invalid exploration epsilon schedule")
        if self.drive_base_weight > 1:
            raise ValueError("drive_base_weight must be <= 1")
        if self.service_mode not in ("occupancy_fifo", "paced_fifo"):
            raise ValueError("invalid exploration service_mode")
        if self.overflow_policy not in ("service_before_admit", "drop_oldest", "drop_newest"):
            raise ValueError("invalid exploration overflow_policy")
        if self.provider_parameter_source not in ("training", "drive"):
            raise ValueError("invalid exploration provider_parameter_source")
        if self.reward_observation_phase != "successor_postphysics":
            raise ValueError("invalid reward_observation_phase")
        if self.predictor_observation_phase != "eligible_predecessor":
            raise ValueError("invalid predictor_observation_phase")
        expected_kind = "observation"
        if self.strategy == "icm":
            expected_kind = "transition"
        if self.predictor_input_kind != expected_kind:
            raise ValueError("invalid predictor_input_kind")
        for name in ("max_updates_per_tick", "max_pending_rows"):
            _number(getattr(self, name), name, True, 1)
        active = _active_policy_fields(self.strategy)
        schema = _provider_schema(self.strategy)
        # Validate numeric contracts independently of serialized field_roles.
        for name in (
            "rnd_feature_dim",
            "rnd_learning_rate",
            "predictor_batch_size",
            "min_intrinsic_weight",
            "variance_threshold",
            "min_survival_fraction",
            "max_episode_length",
            "survival_window",
            "decay_rate",
        ):
            if name in active:
                key = name
                if name == "rnd_feature_dim":
                    key = "feature_dim"
                _parameter(getattr(self, name), key, name)
        missing = set(schema) - self.provider_parameters.keys()
        extra = self.provider_parameters.keys() - set(schema)
        if missing or extra:
            raise ValueError(f"provider_parameters: {self.strategy} schema missing={sorted(missing)}, unexpected={sorted(extra)}")
        for key, scalar in schema.items():
            value = self.provider_parameters[key]
            _parameter(value, key, f"provider_parameters.{key}")
            if scalar is not None and value != getattr(self, scalar):
                raise ValueError(f"provider_parameters.{key}: conflicts with {scalar}")
        if self.strategy in ("rnd", "adaptive_rnd", "icm") and self.max_pending_rows < self.predictor_batch_size:
            raise ValueError("max_pending_rows must accommodate predictor_batch_size")
        # Annotation provenance remains portable, but activity must match the
        # selected executable schema. Inactive presets retain their own values.
        metadata = {"field_roles", "raw_provider_parameters", "authored_parameters", "parameter_units"}
        required_roles = {item.name for item in fields(self)} - metadata
        required_roles.update(f"provider_parameters.{key}" for key in schema)
        for name in required_roles:
            if name not in self.field_roles or not isinstance(self.field_roles[name], FieldRole):
                raise ValueError(f"field_roles.{name}: required resolved activity annotation")
            expected_active = name in active
            if name.startswith("provider_parameters."):
                expected_active = True
            status = self.field_roles[name].status
            if expected_active and status not in ("active", "derived"):
                raise ValueError(f"field_roles.{name}: selected strategy requires active or derived status")
            if not expected_active and status != "inactive_preset":
                raise ValueError(f"field_roles.{name}: selected strategy requires inactive_preset status")

    @property
    def policy_identity(self) -> str:
        """Canonical SHA256 of active values; provenance/presets are excluded."""
        payload = {"schema": "exploration-policy-v1"}
        for name in _active_policy_fields(self.strategy):
            if self.curiosity_scope == "shared" and name in SCOPE_FIELDS:
                continue  # Supported shared execution retains the exact old recipe.
            payload[name] = _portable(getattr(self, name))
        return _identity(payload)

    @property
    def authored_identity(self) -> str:
        return _identity(self.authored_parameters)

    def execution_identity(self) -> str:
        return self.policy_identity

    def to_dict(self) -> dict[str, Any]:
        """Own a fresh portable tree, never expose internal mutable aliases."""
        return {item.name: _portable(getattr(self, item.name)) for item in fields(self)}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ResolvedExplorationPolicy:
        if not isinstance(payload, Mapping) or set(payload) != {field.name for field in fields(cls)}:
            raise ValueError("exploration policy requires the complete current field set")
        values = dict(payload)
        values["field_roles"] = {key: FieldRole(**value) for key, value in values["field_roles"].items()}
        return cls(**values)


@dataclass(frozen=True, init=False)
class IntrinsicTransitionContext:
    """Owned detached transition snapshot. Tensor access returns independent copies."""

    _predecessor: Tensor
    _actions: Tensor
    _successor: Tensor
    _active_on_entry: Tensor
    vector_tick: int

    def __init__(self, *, predecessor: Tensor, actions: Tensor, successor: Tensor, active_on_entry: Tensor, vector_tick: int):
        if predecessor.ndim != 2 or successor.shape != predecessor.shape:
            raise ValueError("transition predecessor/successor shape must be [N,D]")
        rows = predecessor.shape[0]
        if actions.shape != (rows,) or active_on_entry.shape != (rows,):
            raise ValueError("transition actions/active_on_entry shape must be [N]")
        if actions.dtype != torch.long or active_on_entry.dtype != torch.bool:
            raise ValueError("transition actions must be int64 and active_on_entry bool")
        if not predecessor.is_floating_point() or successor.dtype != predecessor.dtype:
            raise ValueError("transition observations require matching floating dtypes")
        if any(item.device != predecessor.device for item in (actions, successor, active_on_entry)):
            raise ValueError("transition tensors must share a device")
        if not torch.isfinite(predecessor).all() or not torch.isfinite(successor).all():
            raise ValueError("transition observations must be finite")
        _number(vector_tick, "vector_tick", True, 0)
        for name, value in (
            ("predecessor", predecessor),
            ("actions", actions),
            ("successor", successor),
            ("active_on_entry", active_on_entry),
        ):
            object.__setattr__(self, f"_{name}", value.detach().clone())
        object.__setattr__(self, "vector_tick", vector_tick)

    @property
    def predecessor(self) -> Tensor:
        return self._predecessor.clone()

    @property
    def actions(self) -> Tensor:
        return self._actions.clone()

    @property
    def successor(self) -> Tensor:
        return self._successor.clone()

    @property
    def active_on_entry(self) -> Tensor:
        return self._active_on_entry.clone()


@dataclass(frozen=True)
class ExplorationServiceReceipt:
    provider: str
    admitted_rows: int
    consumed_rows: int
    dropped_rows: int
    pending_rows: int
    optimizer_updates: int
    mandatory_service_updates: int
    last_loss: float

    def __post_init__(self) -> None:
        if self.provider not in STRATEGIES:
            raise ValueError("invalid exploration receipt provider")
        for name in ("admitted_rows", "consumed_rows", "dropped_rows", "pending_rows", "optimizer_updates", "mandatory_service_updates"):
            _number(getattr(self, name), name, True, 0)
        _number(self.last_loss, "last_loss", False, 0)
        if self.mandatory_service_updates > self.optimizer_updates:
            raise ValueError("mandatory_service_updates exceeds optimizer_updates")


def _number(value: Any, location: str, integer: bool, minimum: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{location}: expected finite numeric value")
    if integer and not isinstance(value, int):
        raise ValueError(f"{location}: expected integer")
    if value < minimum:
        raise ValueError(f"{location}: must be >= {minimum}")


def _parameter(value: Any, key: str, location: str) -> None:
    integers = {
        "feature_dim",
        "hidden_dim",
        "predictor_batch_size",
        "training_batch_size",
        "max_pending_transitions",
        "max_entries",
        "survival_window",
        "max_episode_length",
    }
    zero_allowed = {"initial_intrinsic_weight", "min_intrinsic_weight", "inverse_weight", "forward_weight"}
    minimum = 0.0
    if key in integers:
        minimum = 1
    _number(value, location, key in integers, minimum)
    if key not in integers and key not in zero_allowed and value <= 0:
        raise ValueError(f"{location}: must be positive")
    if key in ("min_survival_fraction", "decay_rate") and value >= 1:
        raise ValueError(f"{location}: must be < 1")
    if key == "min_intrinsic_weight" and value > 1:
        raise ValueError(f"{location}: must be <= 1")


def resolve_exploration_policy(
    drive_intrinsic: IntrinsicStrategyConfig, training: TrainingV2Config, options: BaCOptions
) -> ResolvedExplorationPolicy:
    """Drive selects kind; typed selected overrides > raw selected > derivation.

    RND/adaptive use training ownership unless the authored source is drive.
    Equal-rank aliases conflict only when consumed; presets retain their bytes.
    """
    drive = drive_intrinsic
    strategy = drive.strategy
    # OP validates its standalone training-owned interpretation. Here selected
    # raw/typed provider batches must participate before relational checks.
    # Consume OP's versioned omission table, then apply authored values below.
    resolved = resolve_bac_options(BaCOptions(curiosity_scope=options.curiosity_scope), training=training)
    selected_options = resolved.options
    source = selected_options.provider_parameter_source
    if options.provider_parameter_source is not None:
        source = options.provider_parameter_source
    assert source is not None and selected_options.rnd is not None
    roles: dict[str, FieldRole] = {}
    raw = {key: getattr(drive, key) for key in ("rnd_config", "adaptive_config", "count_config", "icm_config")}
    authored_options = options.model_dump(exclude_none=True)
    authored = {"drive_intrinsic": drive.model_dump(), "training": training.model_dump(), "bac_options": authored_options}

    def role(path: str, active: bool, origin: str, reason: str) -> None:
        status: Literal["active", "inactive_preset", "derived", "unqualified"] = "inactive_preset"
        if active:
            status = "active"
        roles[path] = FieldRole(status, origin, reason)

    def preset_leaves(value: Any, path: str) -> None:
        role(path, False, path, "retained authored preset; no selected consumer")
        if isinstance(value, Mapping):
            for key, item in value.items():
                preset_leaves(item, f"{path}.{key}")

    for key, value in raw.items():
        preset_leaves(value, f"drive.intrinsic.{key}")
    preset_leaves(authored_options, "bac_options")
    values: dict[str, Any] = {
        "strategy": strategy,
        **_scope_values(options.curiosity_scope),
        **training.exploration.model_dump(),
        "rnd_feature_dim": training.intrinsic.rnd.feature_dim,
        "rnd_learning_rate": training.intrinsic.rnd.learning_rate,
        "predictor_batch_size": training.replay_buffer.batch_size,
        "initial_intrinsic_weight": training.intrinsic.initial_weight,
        "min_intrinsic_weight": training.intrinsic.annealing.min_weight,
        "variance_threshold": training.intrinsic.annealing.threshold,
        "min_survival_fraction": training.intrinsic.min_survival_fraction,
        "max_episode_length": training.training_loop.max_steps_per_episode,
        "survival_window": training.intrinsic.survival_window,
        "decay_rate": training.intrinsic.annealing.decay_rate,
        "drive_base_weight": drive.base_weight,
        "modifier_names": tuple(drive.apply_modifiers),
    }
    if values["curiosity_scope"] == "per_world":
        cardinality = 1
    else:
        cardinality = training.population.size
    origins = {
        "strategy": "drive.intrinsic.strategy",
        "drive_base_weight": "drive.intrinsic.base_weight",
        "modifier_names": "drive.intrinsic.apply_modifiers",
        "rnd_feature_dim": "training.intrinsic.rnd.feature_dim",
        "rnd_learning_rate": "training.intrinsic.rnd.learning_rate",
        "predictor_batch_size": "training.replay_buffer.batch_size",
        "initial_intrinsic_weight": "training.intrinsic.initial_weight",
        "min_intrinsic_weight": "training.intrinsic.annealing.min_weight",
        "variance_threshold": "training.intrinsic.annealing.threshold",
        "min_survival_fraction": "training.intrinsic.min_survival_fraction",
        "survival_window": "training.intrinsic.survival_window",
        "max_episode_length": "training.training_loop.max_steps_per_episode",
        "decay_rate": "training.intrinsic.annealing.decay_rate",
        **{key: f"training.exploration.{key}" for key in training.exploration.model_dump()},
    }
    rnd_keys = {
        "feature_dim": "rnd_feature_dim",
        "rnd_feature_dim": "rnd_feature_dim",
        "learning_rate": "rnd_learning_rate",
        "rnd_learning_rate": "rnd_learning_rate",
        "batch_size": "predictor_batch_size",
        "predictor_batch_size": "predictor_batch_size",
    }
    adaptive_keys = {
        **rnd_keys,
        "min_weight": "min_intrinsic_weight",
        "min_intrinsic_weight": "min_intrinsic_weight",
        "threshold": "variance_threshold",
        "variance_threshold": "variance_threshold",
        "decay_rate": "decay_rate",
        "min_survival_fraction": "min_survival_fraction",
        "max_episode_length": "max_episode_length",
        "survival_window": "survival_window",
    }

    def raw_candidates(blocks: tuple[str, ...], aliases: Mapping[str, str]) -> dict[str, list[tuple[str, Any]]]:
        candidates: dict[str, list[tuple[str, Any]]] = {}
        for block in blocks:
            if raw[block] is not None:
                for key, value in raw[block].items():
                    if key in aliases:
                        if aliases[key] not in candidates:
                            candidates[aliases[key]] = []
                        candidates[aliases[key]].append((f"drive.intrinsic.{block}.{key}", value))
        return candidates

    def choose_raw(key: str, candidates: list[tuple[str, Any]]) -> tuple[Any, str]:
        first_path, first_value = candidates[0]
        for path, value in candidates:
            _parameter(value, key, path)
            if value != first_value:
                raise ValueError(f"conflicting equal-precedence values: {first_path} and {path}")
            role(path, True, path, "selected drive provider parameter")
        return first_value, first_path

    training_origins = dict(origins)
    is_rnd = strategy in ("rnd", "adaptive_rnd")
    if is_rnd and source == "drive":
        blocks: tuple[str, ...] = ("rnd_config",)
        aliases = rnd_keys
        if strategy == "adaptive_rnd":
            blocks = ("rnd_config", "adaptive_config")
            aliases = adaptive_keys
        for key, entries in raw_candidates(blocks, aliases).items():
            values[key], origins[key] = choose_raw(key, entries)
    adaptive_fields = {
        "min_intrinsic_weight",
        "variance_threshold",
        "decay_rate",
        "min_survival_fraction",
        "survival_window",
        "max_episode_length",
    }
    rnd_fields = {"rnd_feature_dim", "rnd_learning_rate", "predictor_batch_size"}
    for key, origin in origins.items():
        active = True
        if key in adaptive_fields:
            active = strategy == "adaptive_rnd"
        elif key in rnd_fields:
            active = is_rnd
        elif key in ("drive_base_weight", "modifier_names", "initial_intrinsic_weight"):
            active = strategy != "none"
        role(key, active, origin, "resolved exploration ownership")
        if origin not in roles or roles[origin].status != "active":
            role(origin, active, origin, "selected authored value")
        if active and key not in ("strategy", "modifier_names"):
            if key.startswith("epsilon_") or key == "drive_base_weight":
                _number(values[key], origin, False, 0)
            else:
                check_key = key
                if key == "rnd_feature_dim":
                    check_key = "feature_dim"
                _parameter(values[key], check_key, origin)
    for key, training_origin in training_origins.items():
        if origins[key] != training_origin:
            role(training_origin, False, training_origin, "overridden by selected drive parameter source")
    parameters: dict[str, Any] = {}
    if is_rnd:
        parameters = {
            "feature_dim": values["rnd_feature_dim"],
            "learning_rate": values["rnd_learning_rate"],
            "predictor_batch_size": values["predictor_batch_size"],
        }
        if strategy == "adaptive_rnd":
            parameters.update({key: values[key] for key in adaptive_fields})
        for key in parameters:
            scalar = key
            if key == "feature_dim":
                scalar = "rnd_feature_dim"
            elif key == "learning_rate":
                scalar = "rnd_learning_rate"
            roles[f"provider_parameters.{key}"] = roles[scalar]
    elif strategy in ("count_based", "icm"):
        block, option_name = "count_config", "count_based"
        parameters = {"quantization_width": 1 / 16, "max_entries": training.replay_buffer.capacity}
        if strategy == "icm":
            block, option_name = "icm_config", "icm"
            parameters = {
                "feature_dim": training.intrinsic.rnd.feature_dim,
                "hidden_dim": 2 * training.intrinsic.rnd.feature_dim,
                "learning_rate": training.intrinsic.rnd.learning_rate,
                "inverse_weight": 0.8,
                "forward_weight": 0.2,
                "training_batch_size": training.replay_buffer.batch_size,
                "max_pending_transitions": max(2 * cardinality, training.replay_buffer.batch_size),
            }
        typed: dict[str, Any] = {}
        if options.providers is not None:
            provider = getattr(options.providers, option_name)
            if provider is not None:
                typed = provider.model_dump(exclude_none=True)
        candidates = raw_candidates((block,), {key: key for key in parameters})
        derivation_origins = {
            "max_entries": "training.replay_buffer.capacity",
            "feature_dim": "training.intrinsic.rnd.feature_dim",
            "learning_rate": "training.intrinsic.rnd.learning_rate",
            "training_batch_size": "training.replay_buffer.batch_size",
        }
        for key in parameters:
            path = f"provider_parameters.{key}"
            origin = "bac-options-v1"
            reason = "versioned provider derivation"
            if key in derivation_origins:
                origin = derivation_origins[key]
                reason = origin
            status: Literal["active", "inactive_preset", "derived", "unqualified"] = "derived"
            if key == "hidden_dim":
                parameters[key] = 2 * parameters["feature_dim"]
                reason = "2 * resolved provider_parameters.feature_dim"
            if key == "max_pending_transitions":
                parameters[key] = max(2 * cardinality, parameters["training_batch_size"])
                reason = "max(2 * training.population.size, resolved provider_parameters.training_batch_size)"
                if values["curiosity_scope"] == "per_world":
                    reason = "max(2 * local world cardinality1, resolved provider_parameters.training_batch_size)"
            if key in typed:
                parameters[key] = typed[key]
                origin = f"bac_options.providers.{option_name}.{key}"
                reason, status = "explicit typed override", "active"
                role(origin, True, origin, reason)
            elif key in candidates:
                parameters[key], origin = choose_raw(key, candidates[key])
                reason, status = "selected drive provider parameter", "active"
            _parameter(parameters[key], key, origin)
            roles[path] = FieldRole(status, origin, reason)
            if status == "derived" and origin.startswith("training."):
                roles[origin] = FieldRole("derived", origin, f"supplies {path}")
        if strategy == "icm":
            if parameters["max_pending_transitions"] < parameters["training_batch_size"]:
                raise ValueError("provider_parameters.max_pending_transitions must accommodate training_batch_size")
            values["predictor_batch_size"] = parameters["training_batch_size"]
            role("predictor_batch_size", True, "provider_parameters.training_batch_size", "ICM complete-transition batch")
    service = selected_options.rnd.model_dump()
    authored_service: dict[str, Any] = {}
    if options.rnd is not None:
        authored_service = options.rnd.model_dump(exclude_none=True)
        service.update(authored_service)
    if "rnd" not in authored_options or "max_pending_rows" not in authored_options["rnd"]:
        service["max_pending_rows"] = max(2 * cardinality, values["predictor_batch_size"])
    if strategy == "icm":
        service["max_pending_rows"] = parameters["max_pending_transitions"]
    for key, value in service.items():
        active = strategy in ("rnd", "adaptive_rnd", "icm")
        provenance = next(item for item in resolved.provenance if item.field == f"rnd.{key}")
        origin, reason = provenance.origin, provenance.reason
        explicit = key in authored_service
        if explicit:
            origin, reason = f"bac_options.rnd.{key}", "explicit option"
        if key == "max_pending_rows" and not explicit:
            reason = "max(2 * training.population.size, resolved predictor_batch_size); bounded-service upgrade"
            if values["curiosity_scope"] == "per_world":
                reason = "max(2 * local world cardinality1, resolved predictor_batch_size)"
        if key == "max_pending_rows" and strategy == "icm":
            origin, reason = "provider_parameters.max_pending_transitions", "ICM transition queue capacity"
        role(key, active, origin, reason)
        if active and not explicit:
            roles[key] = FieldRole("derived", origin, reason)
        role(f"bac_options.rnd.{key}", active and not (strategy == "icm" and key == "max_pending_rows"), origin, reason)
        values[key] = value
    for key in ("provider_parameters", "reward_observation_phase", "predictor_observation_phase", "predictor_input_kind"):
        role(key, True, "exploration-policy-v1", "selected provider schema/observation phase")
    role("provider_parameter_source", is_rnd, "bac_options.provider_parameter_source", "training unless explicitly drive")
    role("bac_options.provider_parameter_source", is_rnd, "bac-options-v1", "explicit or versioned source ownership")
    for name in SCOPE_FIELDS:
        role(name, True, values["scope_origin"], "resolved curiosity ownership contract")
    for name in ("scope", "seed_policy"):
        role(f"bac_options.curiosity_scope.{name}", True, values["scope_origin"], "selected curiosity ownership contract")
    units = {
        "epsilon_start": "probability",
        "epsilon_end": "probability",
        "epsilon_decay": "factor/committed_batch_episode",
        "rnd_feature_dim": "features",
        "rnd_learning_rate": "optimizer_learning_rate",
        "predictor_batch_size": "eligible_rows",
        "initial_intrinsic_weight": "runtime_intrinsic_scale",
        "min_intrinsic_weight": "runtime_intrinsic_scale",
        "variance_threshold": "survival_variance",
        "min_survival_fraction": "fraction/planned_horizon",
        "max_episode_length": "lane_steps",
        "survival_window": "committed_lane_outcomes",
        "decay_rate": "factor/qualified_outcome",
        "drive_base_weight": "DAC_multiplier",
        "modifier_names": "DAC_named_modifiers",
        "max_pending_rows": "eligible_rows",
        "max_updates_per_tick": "predictor_minibatches/vector_tick",
        "provider_parameters": "selected_provider_units",
        "quantization_width": "observation_units/bin",
        "max_entries": "LRU_keys",
        "feature_dim": "features",
        "hidden_dim": "units",
        "learning_rate": "optimizer_learning_rate",
        "inverse_weight": "loss_multiplier",
        "forward_weight": "loss_multiplier",
        "training_batch_size": "eligible_transitions",
        "max_pending_transitions": "eligible_transitions",
        **SCOPE_UNITS,
    }
    if values["curiosity_scope"] == "per_world":
        units["max_updates_per_tick"] = "predictor_minibatches/world_eligible_admission"
    input_kind: Literal["observation", "transition"] = "observation"
    if strategy == "icm":
        input_kind = "transition"
    return ResolvedExplorationPolicy(
        **values,
        provider_parameters=parameters,
        reward_observation_phase="successor_postphysics",
        predictor_observation_phase="eligible_predecessor",
        predictor_input_kind=input_kind,
        field_roles=roles,
        provider_parameter_source=source,
        raw_provider_parameters=raw,
        authored_parameters=authored,
        parameter_units=units,
    )


def _runtime_require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _runtime_keys(value: Any, names: tuple[str, ...], location: str) -> None:
    _runtime_require(isinstance(value, Mapping) and set(value) == set(names), f"{location}: exact current fields required")


def _runtime_operation(method: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(method)
    def invoke(self: ExplorationRuntime, *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            if self._operation_active:
                raise RuntimeError("reentrant runtime operation")
            self._operation_active = True
            try:
                return method(self, *args, **kwargs)
            finally:
                self._operation_active = False

    return invoke


class _ParentCommit(TypedDict):
    batch_episode: int
    completion_content: tuple[tuple[str, str], ...]
    epsilon_before: float
    epsilon_after: float


class _ParentCadence(TypedDict):
    schema: Literal["parent-global-epsilon-cadence-v1"]
    last_committed: _ParentCommit | None


class PreparedExplorationRestore:
    """Identity-only receiver capability; all publication data stays in its owner."""

    __slots__ = ()


@dataclass(frozen=True)
class _ExplorationPublication:
    revision: int
    bank_revision: int
    bank_handle: Any
    state: tuple[EpsilonGreedyExploration, _ParentCadence]
    mode: str
    accepted: Any
    parent_restore: Any
    next_revision: int
    empty_handles: dict[PreparedExplorationRestore, Any]


class ExplorationRuntime:
    """One BANK and one global selector, with separate authenticated parent cadence.

    Parent callbacks are required integration contracts, not implementations of
    POP/runner authority. Issuer callbacks retain the real BANK owner; those
    external references and unrelated action RNG users require parent quiescence.
    Historical available payloads are not executable current runtime transports.
    """

    def __init__(
        self,
        *,
        policy: ResolvedExplorationPolicy,
        descriptor: Any,
        device: torch.device | str,
        validate_accepted_episode: Callable[..., None],
        issuer_factory: Callable[..., Any],
        report_allocation: Callable[..., None],
        validate_committed_batch: Callable[..., None],
        validate_parent_cadence: Callable[..., None],
    ):
        # BANK/PF import policy types from this module: defer their imports.
        from townlet.exploration import curiosity_checkpoint as checkpoint
        from townlet.exploration.provider_factory import make_policy_selector
        from townlet.exploration.scoped_curiosity import CuriosityBank, allocation_estimate

        _runtime_require(isinstance(policy, ResolvedExplorationPolicy), "actual resolved exploration policy required")
        _runtime_require(callable(validate_committed_batch) and callable(validate_parent_cadence), "parent cadence callbacks required")
        self._lock = RLock()
        self._operation_active = True
        self._revision = 0
        self._restores: dict[PreparedExplorationRestore, _ExplorationPublication] = {}
        self._codec = checkpoint
        self._policy = ResolvedExplorationPolicy.from_dict(policy.to_dict())
        self._validate_committed_batch = validate_committed_batch
        self._validate_parent_cadence = validate_parent_cadence
        self._report = report_allocation
        try:
            self._bank = CuriosityBank(
                policy=self._policy,
                descriptor=descriptor,
                device=device,
                validate_accepted_episode=validate_accepted_episode,
                issuer_factory=issuer_factory,
                report_allocation=report_allocation,
            )
            self._estimate = allocation_estimate(policy=self._policy, descriptor=self._bank.descriptor, device=self._bank.device)
            self._state: tuple[EpsilonGreedyExploration, _ParentCadence] = (
                make_policy_selector(self._policy),
                {"schema": "parent-global-epsilon-cadence-v1", "last_committed": None},
            )
        finally:
            self._operation_active = False

    def _invalidate(self) -> None:
        self._revision += 1
        self._restores.clear()

    def _bank_call(self, method: str, **kwargs: Any) -> Any:
        revision = self._bank.mutation_revision
        try:
            return getattr(self._bank, method)(**kwargs)
        finally:
            if self._bank.mutation_revision != revision:
                self._invalidate()

    @property
    def epsilon(self) -> float:
        """The sole harmless reentrant observation; never reads a provider."""
        with self._lock:
            return self._state[0].epsilon

    def _epsilon_tensor(self, batch_size: int, device: torch.device | str) -> Tensor:
        _runtime_require(type(batch_size) is int and batch_size >= 0, "epsilon batch_size must be a nonnegative integer")
        selected = torch.device(device)
        _runtime_require(selected == self._bank.device, "epsilon tensor device differs from selected runtime")
        return torch.full((batch_size,), self._state[0].epsilon, dtype=torch.float32, device=selected)

    @_runtime_operation
    def epsilon_tensor(self, *, batch_size: int, device: torch.device | str) -> Tensor:
        return self._epsilon_tensor(batch_size, device)

    @_runtime_operation
    def select_actions(self, q_values: Tensor, agent_states: Any, action_masks: Tensor | None) -> Tensor:
        from townlet.training.state import BatchedAgentState

        _runtime_require(isinstance(agent_states, BatchedAgentState), "actual BatchedAgentState required")
        _runtime_require(
            isinstance(q_values, Tensor)
            and q_values.layout == torch.strided
            and q_values.ndim == 2
            and q_values.is_floating_point()
            and q_values.shape[1] == self._bank.descriptor.action_dim
            and q_values.device == self._bank.device
            and bool(torch.isfinite(q_values).all()),
            "Q values must be finite selected-device [N,A] floating tensors",
        )
        count = q_values.shape[0]
        observations = agent_states.observations
        _runtime_require(
            isinstance(observations, Tensor)
            and observations.layout == torch.strided
            and observations.shape == (count, self._bank.descriptor.observation_dim)
            and observations.device == q_values.device,
            "selection observation geometry mismatch",
        )
        for name in ("actions", "rewards", "dones", "epsilons", "intrinsic_rewards", "survival_times"):
            value = getattr(agent_states, name)
            _runtime_require(
                isinstance(value, Tensor) and value.layout == torch.strided and value.shape == (count,) and value.device == q_values.device,
                f"selection {name} geometry mismatch",
            )
        _runtime_require(torch.device(agent_states.device) == q_values.device, "selection state device mismatch")
        if action_masks is not None:
            _runtime_require(
                isinstance(action_masks, Tensor)
                and action_masks.layout == torch.strided
                and action_masks.dtype == torch.bool
                and action_masks.shape == q_values.shape
                and action_masks.device == q_values.device
                and bool(action_masks.any(dim=1).all()),
                "selection masks must be bool [N,A] with a legal action per presented row",
            )
        if count == 0:
            return torch.empty(0, dtype=torch.int64, device=q_values.device)
        view = BatchedAgentState(
            observations=observations,
            actions=agent_states.actions,
            rewards=agent_states.rewards,
            dones=agent_states.dones,
            epsilons=self._epsilon_tensor(count, q_values.device),
            intrinsic_rewards=agent_states.intrinsic_rewards,
            survival_times=agent_states.survival_times,
            device=q_values.device,
            info=agent_states.info,
        )
        # A selection can consume ambient action RNG even when its result fails.
        try:
            actions = self._state[0].select_actions(q_values, view, action_masks)
            _runtime_require(
                isinstance(actions, Tensor)
                and actions.dtype == torch.int64
                and actions.shape == (count,)
                and actions.device == q_values.device
                and bool(((actions >= 0) & (actions < q_values.shape[1])).all()),
                "selector returned invalid actions",
            )
            return actions
        finally:
            self._invalidate()

    @_runtime_operation
    def begin_episode(self, *, accepted: Any) -> Any:
        return self._bank_call("begin_episode", accepted=accepted)

    @_runtime_operation
    def prepare_step_stamp(self, *, accepted: Any, world_ids: tuple[str, ...], active_on_entry: Tensor, vector_tick: int) -> Any:
        return self._bank_call(
            "prepare_step_stamp", accepted=accepted, world_ids=world_ids, active_on_entry=active_on_entry, vector_tick=vector_tick
        )

    @_runtime_operation
    def reward(self, *, context: IntrinsicTransitionContext, stamp: Any, accepted: Any, update_stats: bool) -> Any:
        return self._bank_call("reward", context=context, stamp=stamp, accepted=accepted, update_stats=update_stats)

    @_runtime_operation
    def admit_and_service(self, *, context: IntrinsicTransitionContext, stamp: Any, accepted: Any) -> Any:
        return self._bank_call("admit_and_service", context=context, stamp=stamp, accepted=accepted)

    @_runtime_operation
    def prepare_completion(
        self,
        *,
        accepted: Any,
        boundary_key: int,
        completion_content: Any,
        outcomes: tuple[Any, ...],
        participated_world_ids: tuple[str, ...],
    ) -> Any:
        return self._bank_call(
            "prepare_completion",
            accepted=accepted,
            boundary_key=boundary_key,
            completion_content=completion_content,
            outcomes=outcomes,
            participated_world_ids=participated_world_ids,
        )

    @_runtime_operation
    def commit_completion(self, *, prepared: Any) -> Any:
        return self._bank_call("commit_completion", prepared=prepared)

    @_runtime_operation
    def prepare_empty_episode_evidence(self, *, accepted: Any) -> Any:
        return self._bank_call("prepare_empty_episode_evidence", accepted=accepted)

    @_runtime_operation
    def quarantine_episode(self, *, accepted: Any, reason: str) -> None:
        self._bank_call("quarantine_episode", accepted=accepted, reason=reason)

    @_runtime_operation
    def snapshot_world(self, *, world_id: str) -> dict[str, Any]:
        result = self._bank_call("snapshot_world", world_id=world_id)
        if not isinstance(result, dict) or any(not isinstance(key, str) for key in result):
            raise TypeError("BANK snapshot must be a dictionary with string keys")
        return cast(dict[str, Any], result)

    def _report_extra(self, operation: str, canonical_bytes: int, tensor_bytes: int) -> None:
        self._report(
            replace(
                self._estimate,
                operation=operation,
                known_tensor_bytes=tensor_bytes,
                components=(("runtime_owned_input_and_callback_views", tensor_bytes),),
                assumptions=(f"canonical outcome payload bytes={canonical_bytes}; immutable scalar/string metadata",),
                unknown_components=("runtime Python objects and callback-retained copies", "caller input and prior prepared states"),
            )
        )

    def _fresh(self, revision: int, bank_revision: int) -> None:
        _runtime_require(
            self._revision == revision and self._bank.mutation_revision == bank_revision,
            "runtime or BANK changed during callback/preparation",
        )

    @_runtime_operation
    def commit_batch_episode(self, *, batch_episode: int, outcomes: tuple[Any, ...]) -> None:
        from townlet.training.episode import LaneOutcome, freeze_lane_outcome

        _runtime_require(type(batch_episode) is int and batch_episode >= 0, "parent batch key must be a nonnegative integer")
        _runtime_require(
            type(outcomes) is tuple and all(isinstance(event, LaneOutcome) for event in outcomes), "actual parent outcomes required"
        )
        _runtime_require(
            all(type(event.batch_episode) is int and event.batch_episode == batch_episode for event in outcomes),
            "parent outcome batch mismatch",
        )
        indexes = tuple(event.outcome.agent_idx for event in outcomes)
        _runtime_require(all(type(index) is int and index >= 0 for index in indexes), "invalid parent outcome lane")
        _runtime_require(len(set(indexes)) == len(indexes), "duplicate parent outcome lane")
        revision, bank_revision = self._revision, self._bank.mutation_revision
        # Report before owning tensors; BANK's separate completion has no role here.
        outcome_bytes = sum(
            tensor.numel() * tensor.element_size()
            for event in outcomes
            for tensor in (event.outcome.final_observation, event.outcome.final_meters)
        )
        self._report_extra("runtime_parent_commit", outcome_bytes, 2 * outcome_bytes)
        owned = deepcopy(outcomes)
        canonical = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, owned))
        view = deepcopy(owned)
        result = self._validate_committed_batch(batch_episode=batch_episode, outcomes=view)
        _runtime_require(result is None, "parent committed-batch validator must return None")
        observed = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, view))
        _runtime_require(self._codec.same(observed, canonical), "parent callback changed outcome view")
        self._fresh(revision, bank_revision)
        selector, cadence = self._state
        last = cadence["last_committed"]
        if last is not None:
            _runtime_require(batch_episode >= last["batch_episode"], "stale parent batch key")
            if batch_episode == last["batch_episode"]:
                _runtime_require(self._codec.same(last["completion_content"], canonical), "changed committed parent outcome content")
                return
        before = selector.epsilon
        after = max(self._policy.epsilon_end, before * self._policy.epsilon_decay)
        next_cadence: _ParentCadence = {
            "schema": "parent-global-epsilon-cadence-v1",
            "last_committed": {
                "batch_episode": batch_episode,
                "completion_content": canonical,
                "epsilon_before": before,
                "epsilon_after": after,
            },
        }
        next_state = (selector, next_cadence)
        selector.epsilon = after
        self._state = next_state
        self._invalidate()

    def _validate_selector_cadence(self, policy: ResolvedExplorationPolicy, selector: Any, cadence: Any) -> None:
        _runtime_keys(selector, ("epsilon", "epsilon_decay", "epsilon_min"), "selector")
        for key, value in selector.items():
            _number(value, f"selector.{key}", False, 0)
        _runtime_require(policy.epsilon_end <= selector["epsilon"] <= policy.epsilon_start, "selector epsilon outside selected schedule")
        _runtime_require(
            selector["epsilon_decay"] == policy.epsilon_decay and selector["epsilon_min"] == policy.epsilon_end,
            "selector schedule differs from policy",
        )
        _runtime_keys(cadence, ("schema", "last_committed"), "cadence")
        _runtime_require(cadence["schema"] == "parent-global-epsilon-cadence-v1", "unsupported parent cadence schema")
        record = cadence["last_committed"]
        if record is None:
            _runtime_require(selector["epsilon"] == policy.epsilon_start, "uncommitted parent cadence requires initial epsilon")
            return
        _runtime_keys(record, ("batch_episode", "completion_content", "epsilon_before", "epsilon_after"), "last parent commit")
        _runtime_require(type(record["batch_episode"]) is int and record["batch_episode"] >= 0, "invalid retained parent batch key")
        for key in ("epsilon_before", "epsilon_after"):
            _number(record[key], f"cadence.{key}", False, 0)
            _runtime_require(policy.epsilon_end <= record[key] <= policy.epsilon_start, "retained epsilon outside policy bounds")
        _runtime_require(
            record["epsilon_after"] == max(policy.epsilon_end, record["epsilon_before"] * policy.epsilon_decay)
            and selector["epsilon"] == record["epsilon_after"],
            "selector and parent cadence recurrence disagree",
        )
        content = record["completion_content"]
        _runtime_require(type(content) is tuple, "canonical parent completion content must be a tuple")
        for item in content:
            _runtime_require(
                type(item) is tuple and len(item) == 2 and all(type(value) is str and bool(value) for value in item),
                "parent content requires complete canonical payload and fingerprint pairs",
            )
            try:
                payload = bytes.fromhex(item[0])
            except ValueError as error:
                raise ValueError("parent outcome payload must be canonical hex") from error
            _runtime_require(payload.hex() == item[0], "parent outcome payload must be canonical hex")

    def _parse(self, state: Any, *, initialization: bool) -> tuple[Any, dict[str, Any], _ParentCadence]:
        _runtime_keys(state, ("schema", "policy", "bank", "selector", "cadence"), "exploration runtime")
        _runtime_require(state["schema"] == "exploration-runtime-state-v1", "unsupported exploration runtime schema")
        policy = ResolvedExplorationPolicy.from_dict(state["policy"])
        _runtime_require(self._codec.same(policy.to_dict(), state["policy"]), "runtime policy must roundtrip completely")
        if not initialization:
            _runtime_require(self._codec.same(policy.to_dict(), self._policy.to_dict()), "complete receiving runtime policy mismatch")
        _runtime_require(isinstance(state["bank"], Mapping), "current BANK transport required")
        _runtime_require(self._codec.same(state["bank"].get("policy"), policy.to_dict()), "runtime and BANK policy disagree")
        self._validate_selector_cadence(policy, state["selector"], state["cadence"])
        if initialization:
            _runtime_require(
                (policy.epsilon_start, policy.epsilon_end, policy.epsilon_decay)
                == (self._policy.epsilon_start, self._policy.epsilon_end, self._policy.epsilon_decay),
                "private initialization must preserve the global epsilon schedule",
            )
        record = state["cadence"]["last_committed"]
        if record is None:
            size = 0
        else:
            size = sum(len(item[0]) // 2 for item in record["completion_content"])
        self._report_extra("runtime_prepare", size, self._codec.tensor_bytes(state))
        owned = self._codec.owned(state)
        # The report callback precedes allocation. Check the owned metadata too,
        # so a callback cannot change authoring after preflight unnoticed. BANK
        # still exclusively validates the complete owned native subtree.
        _runtime_keys(owned, ("schema", "policy", "bank", "selector", "cadence"), "exploration runtime")
        _runtime_require(owned["schema"] == "exploration-runtime-state-v1", "runtime schema changed during allocation reporting")
        _runtime_require(self._codec.same(owned["policy"], policy.to_dict()), "runtime policy changed during allocation reporting")
        _runtime_require(
            isinstance(owned["bank"], Mapping) and self._codec.same(owned["bank"].get("policy"), policy.to_dict()),
            "runtime and owned BANK policy disagree",
        )
        self._validate_selector_cadence(policy, owned["selector"], owned["cadence"])
        return owned["bank"], owned["selector"], cast(_ParentCadence, owned["cadence"])

    def _correlate_cadence(self, cadence: _ParentCadence, *, mode: str, accepted: Any, parent_restore: Any) -> None:
        revision, bank_revision = self._revision, self._bank.mutation_revision
        view = self._codec.owned(cadence)
        result = self._validate_parent_cadence(cadence=view, mode=mode, accepted=accepted, parent_restore=parent_restore)
        _runtime_require(result is None, "parent cadence validator must return None")
        _runtime_require(self._codec.same(view, cadence), "parent callback changed cadence view")
        self._fresh(revision, bank_revision)

    @_runtime_operation
    def checkpoint_state(self) -> dict[str, Any]:
        selector, cadence = self._state
        owned_cadence = self._codec.owned(cadence)
        selector_state = selector.checkpoint_state()
        self._validate_selector_cadence(self._policy, selector_state, owned_cadence)
        bank_state = self._bank_call("checkpoint_state")
        return dict(
            schema="exploration-runtime-state-v1",
            policy=self._policy.to_dict(),
            bank=bank_state,
            selector=selector_state,
            cadence=owned_cadence,
        )

    def _retain(
        self,
        *,
        bank_handle: Any,
        selector_state: dict[str, Any],
        cadence: _ParentCadence,
        mode: str,
        accepted: Any,
        parent_restore: Any,
        revision: int,
        bank_revision: int,
    ) -> PreparedExplorationRestore:
        from townlet.exploration.provider_factory import make_policy_selector

        selector = make_policy_selector(self._policy)
        # Strict separate-global validation happened off-side; native BANK data
        # never passes through this selector's permissive loader.
        selector.load_state(selector_state)
        state = (selector, cadence)
        token = PreparedExplorationRestore()
        publication = _ExplorationPublication(revision, bank_revision, bank_handle, state, mode, accepted, parent_restore, revision + 1, {})
        self._correlate_cadence(cadence, mode=mode, accepted=accepted, parent_restore=parent_restore)
        self._fresh(revision, bank_revision)
        self._restores[token] = publication
        return token

    @_runtime_operation
    def prepare_restore(
        self, *, state: Any, mode: str, accepted: Any, parent_restore: Any, validate_parent_restore: Any
    ) -> PreparedExplorationRestore:
        revision, bank_revision = self._revision, self._bank.mutation_revision
        bank_state, selector, cadence = self._parse(state, initialization=False)
        self._correlate_cadence(cadence, mode=mode, accepted=accepted, parent_restore=parent_restore)
        self._fresh(revision, bank_revision)
        handle = self._bank_call(
            "prepare_restore",
            state=bank_state,
            mode=mode,
            accepted=accepted,
            parent_restore=parent_restore,
            validate_parent_restore=validate_parent_restore,
        )
        return self._retain(
            bank_handle=handle,
            selector_state=selector,
            cadence=cadence,
            mode=mode,
            accepted=accepted,
            parent_restore=parent_restore,
            revision=revision,
            bank_revision=bank_revision,
        )

    @_runtime_operation
    def prepare_private_initialization(
        self, *, state: Any, initialization: str, parent_restore: Any, validate_parent_restore: Any
    ) -> PreparedExplorationRestore:
        revision, bank_revision = self._revision, self._bank.mutation_revision
        bank_state, selector, cadence = self._parse(state, initialization=True)
        if bank_state.get("bank_phase") == "initial":
            mode = "initial"
        else:
            mode = "private_initialized"
        self._correlate_cadence(cadence, mode=mode, accepted=None, parent_restore=parent_restore)
        self._fresh(revision, bank_revision)
        handle = self._bank_call(
            "prepare_private_initialization",
            state=bank_state,
            initialization=initialization,
            parent_restore=parent_restore,
            validate_parent_restore=validate_parent_restore,
        )
        return self._retain(
            bank_handle=handle,
            selector_state=selector,
            cadence=cadence,
            mode=mode,
            accepted=None,
            parent_restore=parent_restore,
            revision=revision,
            bank_revision=bank_revision,
        )

    @_runtime_operation
    def install_restore(self, *, prepared: PreparedExplorationRestore) -> None:
        _runtime_require(type(prepared) is PreparedExplorationRestore and prepared in self._restores, "foreign or consumed runtime restore")
        publication = self._restores[prepared]
        self._fresh(publication.revision, publication.bank_revision)
        self._correlate_cadence(
            publication.state[1], mode=publication.mode, accepted=publication.accepted, parent_restore=publication.parent_restore
        )
        self._fresh(publication.revision, publication.bank_revision)
        # Guard stays active inside BANK's final accepted-token authentication.
        # Its own handle/freshness checks remain authoritative. No fallible work,
        # callback, loader, allocation or corrective check follows its publish.
        self._bank.install_restore(prepared=publication.bank_handle)
        self._state = publication.state
        self._revision = publication.next_revision
        self._restores = publication.empty_handles


def build_exploration(
    *,
    policy: ResolvedExplorationPolicy,
    descriptor: Any,
    device: torch.device | str,
    validate_accepted_episode: Callable[..., None],
    issuer_factory: Callable[..., Any],
    report_allocation: Callable[..., None],
    validate_committed_batch: Callable[..., None],
    validate_parent_cadence: Callable[..., None],
) -> ExplorationRuntime:
    """Construct the current selected runtime; all owner dependencies are explicit."""
    return ExplorationRuntime(
        policy=policy,
        descriptor=descriptor,
        device=device,
        validate_accepted_episode=validate_accepted_episode,
        issuer_factory=issuer_factory,
        report_allocation=report_allocation,
        validate_committed_batch=validate_committed_batch,
        validate_parent_cadence=validate_parent_cadence,
    )
