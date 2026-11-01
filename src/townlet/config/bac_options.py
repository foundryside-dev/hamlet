"""Portable BAC declarations and versioned semantic resolution, not runtime wiring.

None is an absence marker, never a constructor-selected behavioral value. Call
resolve_bac_options at the effective-run boundary before consuming these options.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, SerializerFunctionWrapHandler, model_serializer, model_validator

if TYPE_CHECKING:
    from townlet.config.training_v2_config import TrainingV2Config


class OptionModel(BaseModel):
    """Strict, immutable, finite-only portable policy schema."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, strict=True)


class TokenEncoderOptions(OptionModel):
    """Additive encoder declaration; omission retains recorded linear semantics."""

    mode: Literal["linear", "interaction_mlp"]
    hidden_width: Annotated[int, Field(gt=0)] | None = None

    @model_validator(mode="after")
    def validate_hidden_width(self) -> TokenEncoderOptions:
        if self.mode == "linear" and self.hidden_width is not None:
            raise ValueError("linear token_encoder takes no hidden_width")
        if self.mode == "interaction_mlp" and self.hidden_width is None:
            raise ValueError("interaction_mlp token_encoder requires positive hidden_width")
        return self


def resolve_token_encoder(options: TokenEncoderOptions | None) -> tuple[TokenEncoderOptions, str]:
    """Return portable selected encoder and versioned omission provenance."""
    if options is None:
        return TokenEncoderOptions(mode="linear"), "bac-options-v1: omitted token_encoder retains linear"
    return options, "authored"


class ReplayOptions(OptionModel):
    sampling_mode: Literal["successive_without_replacement", "independent_with_replacement"] | None = None
    uniform_sequence_adapter: Literal["legacy_episode_length_with_replacement", "uniform_windows_with_replacement"] | None = None
    sequence_mode: Literal["fixed_full", "adaptive_prefix"] | None = None
    retention_mode: Literal["whole_episode", "transition_tail"] | None = None
    sequence_objective: Literal["window_mean", "anchor_transition"] | None = None
    priority_reduction: Literal["max_abs", "mean_abs"] | None = None


class RNDOptions(OptionModel):
    service_mode: Literal["occupancy_fifo", "paced_fifo"] | None = None
    max_updates_per_tick: Annotated[int, Field(gt=0)] | None = None
    max_pending_rows: Annotated[int, Field(gt=0)] | None = None
    overflow_policy: Literal["service_before_admit", "drop_oldest", "drop_newest"] | None = None


class CurriculumOptions(OptionModel):
    commit_mode: Literal["completion", "legacy_step"] | None = None
    difficulty_mode: Literal["stage_band", "rate_limited"] | None = None


class ServingOptions(OptionModel):
    policy_mode: Literal["greedy_eval", "mc_dropout"] | None = None


class CheckpointOptions(OptionModel):
    save_initial: bool | None = None
    save_final: bool | None = None


class CountBasedOptions(OptionModel):
    quantization_width: Annotated[float, Field(gt=0)] | None = None
    max_entries: Annotated[int, Field(gt=0)] | None = None


class ICMOptions(OptionModel):
    feature_dim: Annotated[int, Field(gt=0)] | None = None
    hidden_dim: Annotated[int, Field(gt=0)] | None = None
    learning_rate: Annotated[float, Field(gt=0)] | None = None
    inverse_weight: Annotated[float, Field(ge=0)] | None = None
    forward_weight: Annotated[float, Field(ge=0)] | None = None
    training_batch_size: Annotated[int, Field(gt=0)] | None = None
    max_pending_transitions: Annotated[int, Field(gt=0)] | None = None


class ProviderOptions(OptionModel):
    """Overrides for count/ICM; drive retains ownership of the five-way selector.

    RND/adaptive settings are training-owned unless provider_parameter_source is
    drive. Their raw drive dictionaries remain owned by the drive DTO (T18a).
    """

    count_based: CountBasedOptions | None = None
    icm: ICMOptions | None = None


class EvaluationOptions(OptionModel):
    """Viewer overrides; world/policy identity is compiled, never authored here."""

    seed: Annotated[int, Field(ge=0)] | None = None
    episode_cap: Annotated[int, Field(gt=0)] | None = None
    epsilon: Annotated[float, Field(ge=0, le=1)] | None = None
    curriculum_state_policy: Literal["fresh", "retain_compatible"] | None = None
    reward_metric: Literal["extrinsic", "intrinsic", "shaping", "total"] | None = None


class CuriosityScopeOptions(OptionModel):
    """Ownership declaration; seed omission is resolved by the versioned table."""

    scope: Literal["shared", "per_world"]
    seed_policy: Literal["legacy_shared_v1", "world_id_derived_v1"] | None = None

    @model_validator(mode="after")
    def validate_seed_policy(self) -> CuriosityScopeOptions:
        if self.scope == "shared":
            expected = "legacy_shared_v1"
        else:
            expected = "world_id_derived_v1"
        if self.seed_policy is not None and self.seed_policy != expected:
            raise ValueError("curiosity_scope.seed_policy disagrees with scope")
        return self


def resolve_curiosity_scope(options: CuriosityScopeOptions | None) -> tuple[CuriosityScopeOptions, str]:
    """Missing scope is explicitly shared, including known old cache payloads."""
    if options is None:
        return CuriosityScopeOptions(scope="shared", seed_policy="legacy_shared_v1"), "bac-options-v1"
    seed_policy: Literal["legacy_shared_v1", "world_id_derived_v1"] = "legacy_shared_v1"
    if options.scope == "per_world":
        seed_policy = "world_id_derived_v1"
    return CuriosityScopeOptions(scope=options.scope, seed_policy=seed_policy), "authored"


class BaCOptions(OptionModel):
    """Authored partial options or fully resolved values; omission is preserved."""

    replay: ReplayOptions | None = None
    rnd: RNDOptions | None = None
    curriculum: CurriculumOptions | None = None
    serving: ServingOptions | None = None
    checkpoint: CheckpointOptions | None = None
    providers: ProviderOptions | None = None
    provider_parameter_source: Literal["training", "drive"] | None = None
    evaluation: EvaluationOptions | None = None
    curiosity_scope: CuriosityScopeOptions | None = None

    @model_serializer(mode="wrap")
    def portable_options(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        """Preserve the exact pre-scope nested authoring/hash for omitted scope."""
        result: dict[str, Any] = handler(self)
        if self.curiosity_scope is None:
            result.pop("curiosity_scope", None)
        return result


class OptionProvenance(OptionModel):
    field: str
    origin: str
    reason: str


class ResolvedBaCOptions(OptionModel):
    schema_version: Literal["bac-options-v1"]
    options: BaCOptions
    provenance: tuple[OptionProvenance, ...]


def resolve_bac_options(options: BaCOptions | None, *, training: TrainingV2Config) -> ResolvedBaCOptions:
    """Resolve only option omissions; drive precedence/field roles belong to T18a.

    Shared capacity uses parallel N; private capacity uses local cardinality1.
    All values and origins are serializable; shared numerics stay unchanged.
    """
    batch = training.replay_buffer.batch_size
    if options is None:
        declaration = None
    else:
        declaration = options.curiosity_scope
    scope, _ = resolve_curiosity_scope(declaration)
    if scope.scope == "per_world":
        cardinality = 1
    else:
        cardinality = training.population.size
    pending = max(2 * cardinality, batch)
    # This is the single versioned resolution table, not defaults in consumers.
    table: dict[str, Any] = {
        "replay": {
            "sampling_mode": "successive_without_replacement",
            "uniform_sequence_adapter": "legacy_episode_length_with_replacement",
            "sequence_mode": "fixed_full",
            "retention_mode": "whole_episode",
            "sequence_objective": "window_mean",
            "priority_reduction": "max_abs",
        },
        "rnd": {
            "service_mode": "paced_fifo",
            "max_updates_per_tick": 1,
            "max_pending_rows": pending,
            "overflow_policy": "service_before_admit",
        },
        "curriculum": {"commit_mode": "completion", "difficulty_mode": "stage_band"},
        "serving": {"policy_mode": "greedy_eval"},
        "checkpoint": {"save_initial": False, "save_final": True},
        "provider_parameter_source": "training",
        "curiosity_scope": scope.model_dump(),
        "providers": {
            "count_based": {"quantization_width": 1 / 16, "max_entries": training.replay_buffer.capacity},
            "icm": {
                "feature_dim": training.intrinsic.rnd.feature_dim,
                "hidden_dim": 2 * training.intrinsic.rnd.feature_dim,
                "learning_rate": training.intrinsic.rnd.learning_rate,
                "inverse_weight": 0.8,
                "forward_weight": 0.2,
                "training_batch_size": batch,
                "max_pending_transitions": pending,
            },
        },
        "evaluation": {
            "seed": training.seed,
            "episode_cap": training.training_loop.max_steps_per_episode,
            "epsilon": training.exploration.epsilon_end,
            "curriculum_state_policy": "fresh",
            "reward_metric": "extrinsic",
        },
    }
    authored: dict[str, Any] = {}
    if options is not None:
        authored = options.model_dump(exclude_none=True)
    icm_overrides: dict[str, Any] = {}
    if "providers" in authored and "icm" in authored["providers"]:
        icm_overrides = authored["providers"]["icm"]
    icm = table["providers"]["icm"]
    if "feature_dim" in icm_overrides:
        icm["hidden_dim"] = 2 * icm_overrides["feature_dim"]
    if "training_batch_size" in icm_overrides:
        icm["max_pending_transitions"] = max(2 * cardinality, icm_overrides["training_batch_size"])
    reasons = {
        "rnd.max_pending_rows": "max(2 * training.population.size, training.replay_buffer.batch_size); bounded-service upgrade",
        "providers.count_based.max_entries": "training.replay_buffer.capacity",
        "providers.icm.feature_dim": "training.intrinsic.rnd.feature_dim",
        "providers.icm.hidden_dim": "2 * resolved providers.icm.feature_dim",
        "providers.icm.learning_rate": "training.intrinsic.rnd.learning_rate",
        "providers.icm.training_batch_size": "training.replay_buffer.batch_size",
        "providers.icm.max_pending_transitions": "max(2 * training.population.size, resolved providers.icm.training_batch_size)",
        "evaluation.seed": "training.seed",
        "evaluation.episode_cap": "training.training_loop.max_steps_per_episode",
        "evaluation.epsilon": "training.exploration.epsilon_end",
        "curiosity_scope.scope": "omitted scope retains shared population ownership",
        "curiosity_scope.seed_policy": "versioned seed semantics for the selected ownership scope",
    }
    if scope.scope == "per_world":
        reasons["rnd.max_pending_rows"] = "max(2 * local world cardinality1, training.replay_buffer.batch_size)"
        reasons["providers.icm.max_pending_transitions"] = "max(2 * local world cardinality1, resolved providers.icm.training_batch_size)"
    provenance: list[OptionProvenance] = []

    def merge(base: dict[str, Any], overrides: dict[str, Any], prefix: str) -> None:
        for key, value in base.items():
            path = key
            if prefix:
                path = f"{prefix}.{key}"
            if isinstance(value, dict):
                nested: dict[str, Any] = {}
                if key in overrides:
                    nested = overrides[key]
                merge(value, nested, path)
            else:
                explicit = key in overrides
                if explicit:
                    base[key] = overrides[key]
                origin = "bac-options-v1"
                reason = "versioned old-document semantic resolution"
                if path in reasons:
                    reason = reasons[path]
                if explicit:
                    origin = "authored"
                    reason = "explicit option"
                provenance.append(
                    OptionProvenance(
                        field=path,
                        origin=origin,
                        reason=reason,
                    )
                )

    merge(table, authored, "")
    if table["rnd"]["max_pending_rows"] < batch:
        raise ValueError("bac_options.rnd.max_pending_rows must accommodate training.replay_buffer.batch_size")
    if icm["max_pending_transitions"] < icm["training_batch_size"]:
        raise ValueError("bac_options.providers.icm.max_pending_transitions must accommodate training_batch_size")
    return ResolvedBaCOptions(schema_version="bac-options-v1", options=BaCOptions.model_validate(table), provenance=tuple(provenance))
