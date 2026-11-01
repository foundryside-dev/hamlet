"""Selected execution view; authored, execution and cache identities stay distinct."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal

from townlet.config.bac_options import BaCOptions, resolve_bac_options
from townlet.config.brain_config import BrainConfig, apply_training_overrides, compute_brain_hash
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import SCOPE_FIELDS, ResolvedExplorationPolicy, is_legacy_policy_payload, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config


@dataclass(frozen=True)
class FieldRole:
    status: Literal["active", "inactive_preset", "derived", "unqualified"]
    origin: str
    reason: str

    def __post_init__(self) -> None:
        if self.status not in ("active", "inactive_preset", "derived", "unqualified"):
            raise ValueError("invalid effective FieldRole.status")


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _leaves(value: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    result = {}
    for key, item in value.items():
        path = f"{prefix}.{key}"
        if isinstance(item, Mapping) and item:
            result.update(_leaves(item, path))
        else:
            result[path] = item
    return result


def _overlay(base: dict[str, Any], incoming: Mapping[str, Any]) -> None:
    for key, value in incoming.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            _overlay(base[key], value)
        else:
            base[key] = value


@dataclass(frozen=True)
class EffectiveRunConfig:
    base_brain: BrainConfig
    effective_brain: BrainConfig
    training: TrainingV2Config
    authored_options: BaCOptions
    options: BaCOptions
    exploration: ResolvedExplorationPolicy
    primary_level: str
    field_roles: Mapping[str, FieldRole]
    authored_brain_hash: str
    execution_hash: str
    training_hash: str
    derivations: Mapping[str, str]
    origins: Mapping[str, str]

    @property
    def authored_identity(self) -> str:
        """Complete captured brain/training/drive authoring, including presets."""
        return _hash(
            {
                "schema": "effective-run-authored-v1",
                "brain": self.base_brain.model_dump(),
                "exploration": self.exploration.authored_identity,
            }
        )

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if name in ("base_brain", "effective_brain", "training", "authored_options", "options"):
            return value.model_copy(deep=True)
        return value

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_brain": self.base_brain.model_dump(),
            "effective_brain": self.effective_brain.model_dump(),
            "training": self.training.model_dump(),
            "authored_options": self.authored_options.model_dump(),
            "options": self.options.model_dump(),
            "exploration": self.exploration.to_dict(),
            "primary_level": self.primary_level,
            "field_roles": {
                key: {"status": role.status, "origin": role.origin, "reason": role.reason} for key, role in self.field_roles.items()
            },
            "authored_brain_hash": self.authored_brain_hash,
            "authored_identity": self.authored_identity,
            "execution_hash": self.execution_hash,
            "training_hash": self.training_hash,
            "derivations": dict(self.derivations),
            "origins": dict(self.origins),
        }

    def validate_payload(self, payload: Mapping[str, Any]) -> None:
        # Inactive raw presets may contain NaN. Distinct unpacked NaN objects
        # compare unequal; canonical numeric encoding still differs from strings
        # and null. Active numeric validity is checked independently by the DTOs/RP.
        if _hash(self.to_dict()) == _hash(dict(payload)):
            return
        old_fields = set(
            "base_brain effective_brain training authored_options options exploration primary_level field_roles "
            "authored_brain_hash authored_identity execution_hash training_hash derivations origins".split()
        )
        policy = payload.get("exploration")
        options = payload.get("options")
        if (
            set(payload) == old_fields
            and isinstance(policy, Mapping)
            and is_legacy_policy_payload(policy)
            and isinstance(options, Mapping)
            and "curiosity_scope" not in options
            and self.exploration.curiosity_scope == "shared"
            and self.exploration.scope_origin == "bac-options-v1"
        ):
            legacy = self.to_dict()
            legacy["options"].pop("curiosity_scope")
            legacy["exploration"] = self.exploration.legacy_shared_payload()
            for name in SCOPE_FIELDS:
                legacy["field_roles"].pop(f"exploration.{name}", None)
                legacy["derivations"].pop(f"exploration.{name}", None)
            for name in ("scope", "seed_policy"):
                legacy["field_roles"].pop(f"bac_options.curiosity_scope.{name}", None)
                legacy["derivations"].pop(f"curiosity_scope.{name}", None)
            if _hash(legacy) == _hash(dict(payload)):
                return
        raise ValueError("effective_run: serialized fields, roles or execution_hash disagree with resolved authoring")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> EffectiveRunConfig:
        policy = ResolvedExplorationPolicy.from_dict(payload["exploration"])
        result = resolve_effective_run(
            BrainConfig.model_validate(payload["base_brain"]),
            TrainingV2Config.model_validate(payload["training"]),
            primary_level=payload["primary_level"],
            origins=payload["origins"],
            drive_intrinsic=IntrinsicStrategyConfig.model_validate(policy.authored_parameters["drive_intrinsic"]),
        )
        result.validate_payload(payload)
        return result


def resolve_effective_run(
    base: BrainConfig,
    training: TrainingV2Config,
    *,
    primary_level: str,
    origins: Mapping[str, str],
    drive_intrinsic: IntrinsicStrategyConfig,
) -> EffectiveRunConfig:
    """Resolve RP first from authored options, then materialize its selected context.

    OP's omission table is consumed with empty authoring. Its standalone training
    batch capacity check cannot interpret a drive-selected batch. RP owns those
    selected checks; inactive typed presets are retained without reactivating them.
    """
    base = BrainConfig.model_validate(base.model_dump())
    training = TrainingV2Config.model_validate(training.model_dump())
    if not isinstance(primary_level, str) or not primary_level:
        raise ValueError("primary_level must be a nonempty string")
    if any(not isinstance(key, str) or not isinstance(value, str) for key, value in origins.items()):
        raise ValueError("origins must map strings to strings")
    authored = BaCOptions()
    if training.bac_options is not None:
        authored = training.bac_options
    exploration = resolve_exploration_policy(drive_intrinsic, training, authored)
    defaults = resolve_bac_options(BaCOptions(curiosity_scope=authored.curiosity_scope), training=training)
    materialized = defaults.options.model_dump()
    _overlay(materialized, authored.model_dump(exclude_none=True))
    icm = materialized["providers"]["icm"]
    declared_icm = {}
    if authored.providers is not None and authored.providers.icm is not None:
        declared_icm = authored.providers.icm.model_dump(exclude_none=True)
    if "hidden_dim" not in declared_icm:
        icm["hidden_dim"] = 2 * icm["feature_dim"]
    if "max_pending_transitions" not in declared_icm:
        if exploration.curiosity_scope == "per_world":
            cardinality = 1
        else:
            cardinality = training.population.size
        icm["max_pending_transitions"] = max(2 * cardinality, icm["training_batch_size"])
    service = ("service_mode", "max_updates_per_tick", "max_pending_rows", "overflow_policy")
    materialized["rnd"].update({key: getattr(exploration, key) for key in service})
    materialized["provider_parameter_source"] = exploration.provider_parameter_source
    if exploration.strategy in ("icm", "count_based"):
        materialized["providers"][exploration.strategy] = dict(exploration.provider_parameters)
    options = BaCOptions.model_validate(materialized)
    effective = apply_training_overrides(base, training)
    roles: dict[str, FieldRole] = {}
    declared_paths = _leaves(authored.model_dump(exclude_none=True), "bac_options")
    derivations = {item.field: item.reason for item in defaults.provenance if f"bac_options.{item.field}" not in declared_paths}
    derivations["capture_origin"] = "resolved from current authored configuration"
    if "capture_origin" in origins:
        derivations["capture_origin"] = origins["capture_origin"]
    active: dict[str, Any] = {}

    def record(path: str, value: Any, enabled: bool, reason: str, *, origin: str, qualified: bool) -> None:
        status: Literal["active", "inactive_preset", "derived", "unqualified"] = "inactive_preset"
        if not qualified:
            status = "unqualified"
        elif enabled:
            status = "active"
            active[path] = value
        roles[path] = FieldRole(status, origin, reason)

    architecture = effective.architecture.type
    optimizer = effective.optimizer.type
    schedule = effective.optimizer.schedule.type
    optimizer_keys = {
        "adam": {"adam_beta1", "adam_beta2", "adam_eps"},
        "adamw": {"adam_beta1", "adam_beta2", "adam_eps"},
        "sgd": {"sgd_momentum", "sgd_nesterov"},
        "rmsprop": {"rmsprop_alpha", "rmsprop_eps"},
    }
    schedule_keys = {"constant": set(), "step_decay": {"step_size", "gamma"}, "cosine": {"t_max", "eta_min"}, "exponential": {"gamma"}}
    overrides = {
        "q_learning.gamma": "q_learning.gamma",
        "q_learning.target_update_frequency": "q_learning.target_update_frequency",
        "q_learning.use_double_dqn": "q_learning.use_double_dqn",
        "optimizer.learning_rate": "q_learning.learning_rate",
        "replay.capacity": "replay_buffer.capacity",
    }
    for path, value in _leaves(effective.model_dump(), "brain").items():
        relative = path.removeprefix("brain.")
        enabled, qualified = True, relative not in ("description", "version")
        if relative.startswith("architecture.") and relative != "architecture.type":
            enabled = relative.split(".")[1] == architecture
            if relative.endswith("aggregator.num_heads"):
                enabled = enabled and getattr(effective.architecture, architecture).aggregator.type == "attention"
        elif relative.startswith("optimizer.schedule."):
            enabled = relative.split(".")[-1] in schedule_keys[schedule] | {"type"}
        elif relative.startswith("optimizer."):
            enabled = relative.split(".")[-1] in optimizer_keys[optimizer] | {"type", "learning_rate", "weight_decay"}
        elif relative.startswith("replay.priority_"):
            enabled = effective.replay.prioritized
        elif relative == "loss.huber_delta":
            enabled = effective.loss.type == "huber"
        origin = "brain"
        if "brain" in origins:
            origin = origins["brain"]
        record(
            path,
            value,
            enabled,
            "selected executable brain field" if enabled else "retained nonselected preset",
            origin=origin,
            qualified=qualified,
        )
        if relative in overrides:
            roles[path] = FieldRole("inactive_preset", origin, f"base overridden by training.{overrides[relative]}")
            derived_path = f"effective_brain.{relative}"
            active[derived_path] = active.pop(path)
            roles[derived_path] = FieldRole("derived", f"training.{overrides[relative]}", "five-field training override")
    recurrent = architecture == "recurrent"
    for path, value in _leaves(training.model_dump(), "training").items():
        relative = path.removeprefix("training.")
        if relative.startswith(("bac_options", "exploration.", "intrinsic.")):
            continue  # RP owns exploration activity; options get their own selected projection.
        qualified = relative.split(".")[0] not in ("version", "run_metadata", "recording")
        enabled = not (relative.startswith("curriculum.adversarial") and training.curriculum.strategy != "adversarial")
        if relative == "training_loop.sequence_length":
            enabled = recurrent
        if relative == "curriculum.adversarial.adaptation_rate":
            enabled = enabled and options.curriculum is not None and options.curriculum.difficulty_mode == "rate_limited"
        origin = "training"
        if "training" in origins:
            origin = origins["training"]
        record(
            path,
            value,
            enabled,
            "selected training consumer" if enabled else "retained nonselected preset",
            origin=origin,
            qualified=qualified,
        )
    for path, value in _leaves(options.model_dump(), "bac_options").items():
        relative = path.removeprefix("bac_options.")
        if relative.startswith(("providers.", "rnd.")) or relative == "provider_parameter_source":
            continue
        enabled = True
        if relative == "replay.sampling_mode":
            enabled = effective.replay.prioritized
        elif relative == "replay.uniform_sequence_adapter":
            enabled = recurrent and not effective.replay.prioritized
        elif relative == "replay.priority_reduction":
            enabled = recurrent and effective.replay.prioritized
        elif relative.startswith("replay."):
            enabled = recurrent
        provenance = next(item for item in defaults.provenance if item.field == relative)
        if relative.startswith("curriculum."):
            enabled = training.curriculum.strategy == "adversarial"
        explicit = path in declared_paths
        origin = provenance.origin
        if explicit:
            origin = path
        record(path, value, enabled, "selected option" if explicit else provenance.reason, origin=origin, qualified=True)
        if relative.startswith("curiosity_scope.") and exploration.curiosity_scope == "shared":
            active.pop(path, None)  # Published ownership metadata preserves the supported shared hash recipe.
        if enabled and not explicit:
            roles[path] = FieldRole("derived", provenance.origin, provenance.reason)
    for path, role in exploration.field_roles.items():
        key = f"exploration.{path}"
        if path.startswith(("training.", "drive.", "bac_options.")):
            key = path
        # A training value may also supply the Q learner or episode horizon.
        if key in active:
            continue
        roles[key] = FieldRole(role.status, role.origin, role.reason)
        if role.status == "derived":
            derivations[key] = role.reason
    for name in service:
        derivations.pop(f"rnd.{name}", None)
        role = exploration.field_roles[name]
        if role.status == "derived":
            derivations[f"rnd.{name}"] = role.reason
    if exploration.strategy in ("icm", "count_based"):
        for name in exploration.provider_parameters:
            path = f"bac_options.providers.{exploration.strategy}.{name}"
            role = exploration.field_roles[f"provider_parameters.{name}"]
            roles[path] = FieldRole(role.status, role.origin, role.reason)
            derivations.pop(path.removeprefix("bac_options."), None)
            if role.status == "derived":
                derivations[path.removeprefix("bac_options.")] = role.reason
    for path in _leaves(options.model_dump(), "bac_options"):
        if path not in roles:
            roles[path] = FieldRole("inactive_preset", path, "retained nonselected provider preset")
    # Normalize the selected encoder's omission and explicit linear declaration.
    if architecture in ("token_set", "recurrent"):
        encoder = getattr(effective.architecture, architecture).token_encoder
        prefix = f"brain.architecture.{architecture}.token_encoder"
        for path in tuple(active):
            if path == prefix or path.startswith(prefix + "."):
                active.pop(path)
        active[prefix] = {"mode": "linear", "hidden_width": None}
        if encoder is not None:
            active[prefix] = encoder.model_dump()
        roles[prefix] = FieldRole(
            "derived" if encoder is None else "active", "bac-options-v1" if encoder is None else prefix, "selected token encoder"
        )
    return EffectiveRunConfig(
        base,
        effective,
        training,
        authored,
        options,
        exploration,
        primary_level,
        MappingProxyType(roles),
        compute_brain_hash(base),
        _hash({"schema": "effective-run-v1", "fields": active, "exploration": exploration.policy_identity}),
        hashlib.sha256(training.model_dump_json().encode("utf-8")).hexdigest(),
        MappingProxyType(derivations),
        MappingProxyType(dict(origins)),
    )
