"""One authored exploration boundary; provider construction belongs to T18d.

Execution identity hashes resolved active behavior only. Authored identity retains
presets and provenance separately. No compiler, environment or provider is imported.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any, Literal

import torch
from torch import Tensor

from townlet.config.bac_options import BaCOptions, resolve_bac_options
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.training_v2_config import TrainingV2Config

Strategy = Literal["none", "rnd", "adaptive_rnd", "count_based", "icm"]
STRATEGIES = ("none", "rnd", "adaptive_rnd", "count_based", "icm")


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

    def __post_init__(self) -> None:
        if self.strategy not in STRATEGIES:
            raise ValueError("invalid exploration strategy")
        for name in ("provider_parameters", "raw_provider_parameters", "authored_parameters", "field_roles", "parameter_units"):
            object.__setattr__(self, name, _freeze(getattr(self, name)))
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
        values = dict(payload)
        values["field_roles"] = {key: FieldRole(**value) for key, value in payload["field_roles"].items()}
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
    resolved = resolve_bac_options(BaCOptions(), training=training)
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
                "max_pending_transitions": max(2 * training.population.size, training.replay_buffer.batch_size),
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
                parameters[key] = max(2 * training.population.size, parameters["training_batch_size"])
                reason = "max(2 * training.population.size, resolved provider_parameters.training_batch_size)"
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
        service["max_pending_rows"] = max(2 * training.population.size, values["predictor_batch_size"])
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
    }
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
