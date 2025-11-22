"""Immutable CompiledUniverse artifact with multi-level support (v2.1)."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any

import msgpack  # type: ignore[import]
import torch

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.agent_config import AgentConfig
from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.environment_config import EnvironmentConfig
from townlet.config.experiment_config import ExperimentConfig
from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.config.stratum_config import StratumConfig
from townlet.config.training_v2_config import TrainingV2Config
from townlet.effects.catalog import EffectCatalog
from townlet.universe.dto import (
    ActionMetadata,
    ActionSpaceMetadata,
    AffordanceInfo,
    AffordanceMetadata,
    MeterInfo,
    MeterMetadata,
    ObservationActivity,
    ObservationField,
    ObservationSpec,
    UniverseMetadata,
)
from townlet.universe.optimization import OptimizationData
from townlet.vfs.profiles import CompiledGlobalProfile
from townlet.vfs.schema import ObservationField as VfsObservationField
from townlet.vfs.schema import VariableDef


@dataclass(frozen=True)
class CompiledVFSProfiles:
    """Compiled VFS profiles (global, agent, item)."""

    global_profile: CompiledGlobalProfile | None = None
    agent_profile: Any | None = None  # TODO: Add CompiledAgentProfile type
    item_profiles: dict[str, Any] | None = None  # TODO: Add CompiledItemProfile type

    def __post_init__(self):
        # Make item_profiles immutable
        if self.item_profiles is None:
            object.__setattr__(self, "item_profiles", {})


@dataclass(frozen=True)
class CompiledUniverse:
    """Compiled universe representation with multi-level support."""

    # Primary (per-primary-level) metadata
    metadata: UniverseMetadata
    observation_spec: ObservationSpec
    observation_activity: ObservationActivity
    vfs_observation_fields: tuple[VfsObservationField, ...]
    vfs_variables: tuple[VariableDef, ...]
    action_space_metadata: ActionSpaceMetadata
    meter_metadata: MeterMetadata
    affordance_metadata: AffordanceMetadata
    optimization_data: OptimizationData

    # Shared experiment-level configs (v2.1)
    experiment: ExperimentConfig
    stratum: StratumConfig
    environment: EnvironmentConfig
    actions: ActionsConfig
    agent: AgentConfig
    items_catalog: ItemsCatalogConfig | None = None

    # Compiled VFS profiles (experiment-level artifact)
    compiled_vfs_profiles: CompiledVFSProfiles | None = None

    # Compiled effects catalog (per-level artifact)
    compiled_effect_catalog: EffectCatalog | None = None

    # Type schema for runtime VFS expression validation
    vfs_expression_schema: dict[str, str] | None = None

    # Marks for which VFS variables are observed (for mark-and-sweep evaluation)
    vfs_observation_marks: dict[str, set[str]] | None = None
    # Format: {"global": {"day_count", "is_night"}, "agent": {"motivation"}, "item": {...}}

    # Provenance
    experiment_dir: Path | None = None
    drive_hash: str | None = None

    # Multi-level support
    all_levels: dict[str, CompiledUniverse.LevelMetadata] | None = None

    @dataclass(frozen=True)
    class LevelMetadata:
        """Per-level metadata for multi-level compilation."""

        level_name: str
        bars: BarsV2Config
        affordances: AffordancesV2Config
        curriculum: CurriculumConfig
        training: TrainingV2Config
        observation_spec: ObservationSpec
        observation_activity: ObservationActivity
        action_metadata: ActionSpaceMetadata
        meter_metadata: MeterMetadata
        affordance_metadata: AffordanceMetadata
        optimization_data: OptimizationData
        vfs_observation_fields: tuple[VfsObservationField, ...]
        vfs_variables: tuple[VariableDef, ...]
        items_appearance: ItemsAppearanceConfig | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "vfs_observation_fields", tuple(self.vfs_observation_fields))
        if self.all_levels is not None and len(self.all_levels) == 0:
            raise ValueError("all_levels must be None or a non-empty dict of LevelMetadata")

    @property
    def available_levels(self) -> list[str]:
        if self.all_levels is None:
            return []
        return sorted(self.all_levels.keys())

    def get_level(self, level_name: str) -> CompiledUniverse.LevelMetadata:
        if self.all_levels is None:
            raise ValueError(
                "This CompiledUniverse was not compiled with multi-level support. "
                "Compile with primary_level and ensure all_levels is populated."
            )
        if level_name not in self.all_levels:
            raise ValueError(f"Level '{level_name}' not found. Available: {list(self.all_levels.keys())}")
        return self.all_levels[level_name]

    def clone(self) -> CompiledUniverse:
        """Clone the compiled universe."""
        return CompiledUniverse(
            metadata=deepcopy(self.metadata),
            observation_spec=deepcopy(self.observation_spec),
            observation_activity=deepcopy(self.observation_activity),
            vfs_observation_fields=tuple(deepcopy(self.vfs_observation_fields)),
            vfs_variables=tuple(deepcopy(self.vfs_variables)),
            action_space_metadata=deepcopy(self.action_space_metadata),
            meter_metadata=deepcopy(self.meter_metadata),
            affordance_metadata=deepcopy(self.affordance_metadata),
            optimization_data=deepcopy(self.optimization_data),
            experiment=deepcopy(self.experiment),
            stratum=deepcopy(self.stratum),
            environment=deepcopy(self.environment),
            actions=deepcopy(self.actions),
            agent=deepcopy(self.agent),
            items_catalog=deepcopy(self.items_catalog) if self.items_catalog is not None else None,
            compiled_vfs_profiles=deepcopy(self.compiled_vfs_profiles) if self.compiled_vfs_profiles is not None else None,
            compiled_effect_catalog=deepcopy(self.compiled_effect_catalog) if self.compiled_effect_catalog is not None else None,
            vfs_expression_schema=deepcopy(self.vfs_expression_schema) if self.vfs_expression_schema is not None else None,
            vfs_observation_marks=deepcopy(self.vfs_observation_marks) if self.vfs_observation_marks is not None else None,
            experiment_dir=self.experiment_dir,
            drive_hash=self.drive_hash,
            all_levels=deepcopy(self.all_levels),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a serialization-friendly dictionary."""
        return {
            "metadata": _dataclass_to_plain(self.metadata),
            "observation_spec": _dataclass_to_plain(self.observation_spec),
            "observation_activity": _dataclass_to_plain(self.observation_activity),
            "vfs_observation_fields": [field.model_dump() for field in self.vfs_observation_fields],
            "vfs_variables": [var.model_dump() for var in getattr(self, "vfs_variables", ())],
            "action_space_metadata": _dataclass_to_plain(self.action_space_metadata),
            "meter_metadata": _dataclass_to_plain(self.meter_metadata),
            "affordance_metadata": _dataclass_to_plain(self.affordance_metadata),
            "optimization_data_raw": {
                "base_depletions": self.optimization_data.base_depletions.cpu().tolist(),
                "cascade_data": self.optimization_data.cascade_data,
                "modulation_data": self.optimization_data.modulation_data,
                "action_mask_table": (
                    self.optimization_data.action_mask_table.cpu().tolist()
                    if self.optimization_data.action_mask_table is not None
                    else None
                ),
                "affordance_position_map": _serialize_affordance_positions(self.optimization_data.affordance_position_map),
            },
            "experiment": self.experiment.model_dump(),
            "stratum": self.stratum.model_dump(),
            "environment": self.environment.model_dump(),
            "actions": self.actions.model_dump(),
            "agent": self.agent.model_dump(),
            "items_catalog": self.items_catalog.model_dump() if self.items_catalog is not None else None,
            "compiled_vfs_profiles": (
                _serialize_vfs_profiles(self.compiled_vfs_profiles) if self.compiled_vfs_profiles is not None else None
            ),
            "compiled_effect_catalog": (
                _serialize_effect_catalog(self.compiled_effect_catalog) if self.compiled_effect_catalog is not None else None
            ),
            "vfs_expression_schema": self.vfs_expression_schema,
            "vfs_observation_marks": (
                {k: list(v) for k, v in self.vfs_observation_marks.items()} if self.vfs_observation_marks is not None else None
            ),  # Convert sets to lists for JSON serialization
            "experiment_dir": None if self.experiment_dir is None else str(self.experiment_dir),
            "drive_hash": self.drive_hash,
            "all_levels": (
                None
                if self.all_levels is None
                else {
                    name: {
                        "level_name": meta.level_name,
                        "bars": meta.bars.model_dump(),
                        "affordances": meta.affordances.model_dump(),
                        "curriculum": meta.curriculum.model_dump(),
                        "training": meta.training.model_dump(),
                        "observation_spec": _dataclass_to_plain(meta.observation_spec),
                        "observation_activity": _dataclass_to_plain(meta.observation_activity),
                        "action_metadata": _dataclass_to_plain(meta.action_metadata),
                        "meter_metadata": _dataclass_to_plain(meta.meter_metadata),
                        "affordance_metadata": _dataclass_to_plain(meta.affordance_metadata),
                        "optimization_data_raw": {
                            "base_depletions": meta.optimization_data.base_depletions.cpu().tolist(),
                            "cascade_data": meta.optimization_data.cascade_data,
                            "modulation_data": meta.optimization_data.modulation_data,
                            "action_mask_table": (
                                meta.optimization_data.action_mask_table.cpu().tolist()
                                if meta.optimization_data.action_mask_table is not None
                                else None
                            ),
                            "affordance_position_map": _serialize_affordance_positions(meta.optimization_data.affordance_position_map),
                        },
                        "vfs_observation_fields": [field.model_dump() for field in meta.vfs_observation_fields],
                        "vfs_variables": [var.model_dump() for var in meta.vfs_variables],
                    }
                    for name, meta in self.all_levels.items()
                }
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CompiledUniverse:
        """Create CompiledUniverse from a dictionary produced by to_dict/save_to_cache."""
        opt_payload = payload.get("optimization_data_raw", {})
        action_mask = opt_payload.get("action_mask_table")
        if action_mask is None:
            action_mask_tensor = torch.zeros((24, 0), dtype=torch.bool)
        else:
            action_mask_tensor = torch.tensor(action_mask, dtype=torch.bool)

        affordance_position_map = _deserialize_affordance_positions(opt_payload.get("affordance_position_map", {}))

        all_levels = None
        raw_levels = payload.get("all_levels")
        if raw_levels is not None:
            all_levels = {}
            for name, meta in raw_levels.items():
                level_opt_payload = meta.get("optimization_data_raw", {})
                level_action_mask = level_opt_payload.get("action_mask_table")
                level_mask_tensor = (
                    torch.tensor(level_action_mask, dtype=torch.bool) if level_action_mask is not None else torch.zeros((24, 0))
                )
                level_affordance_position_map = _deserialize_affordance_positions(level_opt_payload.get("affordance_position_map", {}))
                all_levels[name] = CompiledUniverse.LevelMetadata(
                    level_name=meta["level_name"],
                    bars=BarsV2Config.model_validate(meta["bars"]),
                    affordances=AffordancesV2Config.model_validate(meta["affordances"]),
                    curriculum=CurriculumConfig.model_validate(meta["curriculum"]),
                    training=TrainingV2Config.model_validate(meta["training"]),
                    observation_spec=_observation_spec_from_plain(meta["observation_spec"]),
                    observation_activity=_observation_activity_from_plain(meta.get("observation_activity", {})),
                    action_metadata=_action_space_metadata_from_plain(meta["action_metadata"]),
                    meter_metadata=_meter_metadata_from_plain(meta["meter_metadata"]),
                    affordance_metadata=_affordance_metadata_from_plain(meta["affordance_metadata"]),
                    optimization_data=OptimizationData(
                        base_depletions=torch.tensor(level_opt_payload.get("base_depletions", []), dtype=torch.float32),
                        cascade_data=level_opt_payload.get("cascade_data", {}),
                        modulation_data=level_opt_payload.get("modulation_data", []),
                        action_mask_table=level_mask_tensor,
                        affordance_position_map=level_affordance_position_map,
                    ),
                    vfs_observation_fields=tuple(VfsObservationField(**field) for field in meta.get("vfs_observation_fields", [])),
                    vfs_variables=tuple(VariableDef(**var) for var in meta.get("vfs_variables", [])),
                )

        return CompiledUniverse(
            metadata=UniverseMetadata(**payload["metadata"]),
            observation_spec=_observation_spec_from_plain(payload["observation_spec"]),
            observation_activity=_observation_activity_from_plain(payload.get("observation_activity", {})),
            vfs_observation_fields=tuple(VfsObservationField(**field) for field in payload.get("vfs_observation_fields", [])),
            vfs_variables=tuple(VariableDef(**var) for var in payload.get("vfs_variables", [])),
            action_space_metadata=_action_space_metadata_from_plain(payload["action_space_metadata"]),
            meter_metadata=_meter_metadata_from_plain(payload["meter_metadata"]),
            affordance_metadata=_affordance_metadata_from_plain(payload["affordance_metadata"]),
            optimization_data=OptimizationData(
                base_depletions=torch.tensor(opt_payload.get("base_depletions", []), dtype=torch.float32),
                cascade_data=opt_payload.get("cascade_data"),
                modulation_data=opt_payload.get("modulation_data"),
                action_mask_table=action_mask_tensor,
                affordance_position_map=affordance_position_map,
            ),
            experiment=ExperimentConfig.model_validate(payload["experiment"]),
            stratum=StratumConfig.model_validate(payload["stratum"]),
            environment=EnvironmentConfig.model_validate(payload["environment"]),
            actions=ActionsConfig.model_validate(payload["actions"]),
            agent=AgentConfig.model_validate(payload["agent"]),
            items_catalog=ItemsCatalogConfig.model_validate(payload["items_catalog"]) if payload.get("items_catalog") is not None else None,
            compiled_vfs_profiles=(
                _deserialize_vfs_profiles(payload["compiled_vfs_profiles"]) if payload.get("compiled_vfs_profiles") is not None else None
            ),
            compiled_effect_catalog=(
                _deserialize_effect_catalog(payload["compiled_effect_catalog"])
                if payload.get("compiled_effect_catalog") is not None
                else None
            ),
            vfs_expression_schema=payload.get("vfs_expression_schema"),
            vfs_observation_marks=(
                {k: set(v) for k, v in payload["vfs_observation_marks"].items()}
                if payload.get("vfs_observation_marks") is not None
                else None
            ),  # Convert lists back to sets
            experiment_dir=None if payload.get("experiment_dir") is None else Path(payload["experiment_dir"]),
            drive_hash=payload.get("drive_hash"),
            all_levels=all_levels,
        )

    def save_to_cache(self, path: Path) -> None:
        """Serialize compiled universe to MessagePack file."""
        data = self.to_dict()
        packed = msgpack.packb(data, use_bin_type=True)
        path.write_bytes(packed)

    @classmethod
    def load_from_cache(cls, path: Path) -> CompiledUniverse:
        """Deserialize a compiled universe from MessagePack file."""
        payload = msgpack.unpackb(path.read_bytes(), raw=False)
        return cls.from_dict(payload)

    # Runtime adapters -----------------------------------------------------

    def to_level(self, level_name: str) -> CompiledUniverse.LevelMetadata:
        """Return per-level metadata (raises if missing)."""
        return self.get_level(level_name)

    def as_single_level(self, level_name: str) -> dict[str, Any]:
        """Return a dict of shared + level-specific configs for callers expecting a flat bundle."""
        level = self.get_level(level_name)
        return {
            "experiment": self.experiment,
            "stratum": self.stratum,
            "environment": self.environment,
            "actions": self.actions,
            "agent": self.agent,
            "curriculum": level.curriculum,
            "bars": level.bars,
            "affordances": level.affordances,
            "training": level.training,
        }

    # === Runtime adapters ===

    def create_environment(
        self,
        *,
        num_agents: int,
        level_name: str,
        device: str | torch.device,
    ):
        """Instantiate a VectorizedHamletEnv from this compiled universe.

        Args:
            num_agents: Number of parallel agents to simulate.
            level_name: Curriculum level name to instantiate. Must be provided
                explicitly; no default level selection is performed.
            device: PyTorch device or device string (e.g., \"cpu\", \"cuda\"). Required.

        Returns:
            VectorizedHamletEnv instance
        """

        # Lazy import to avoid circular dependency at module import time.
        from townlet.environment.vectorized_env import VectorizedHamletEnv

        return VectorizedHamletEnv.from_universe(
            self,
            level_name=level_name,
            num_agents=num_agents,
            device=device,
        )


def _dataclass_to_plain(obj: Any) -> Any:
    if is_dataclass(obj):
        return {f.name: _dataclass_to_plain(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, Mapping):
        return {key: _dataclass_to_plain(value) for key, value in obj.items()}
    if isinstance(obj, list | tuple):
        return [_dataclass_to_plain(value) for value in obj]
    if isinstance(obj, slice):
        return [obj.start, obj.stop]
    return obj


def _serialize_affordance_positions(position_map: dict[str, torch.Tensor | None]) -> dict[str, Any]:
    serialized: dict[str, Any] = {}
    for key, value in position_map.items():
        if isinstance(value, torch.Tensor):
            serialized[key] = value.tolist()
        else:
            serialized[key] = value
    return serialized


def _deserialize_affordance_positions(payload: dict[str, Any]) -> dict[str, torch.Tensor | None]:
    restored: dict[str, torch.Tensor | None] = {}
    for key, value in payload.items():
        if value is None:
            restored[key] = None
        else:
            restored[key] = torch.tensor(value)
    return restored


def _observation_spec_from_plain(payload: Mapping[str, Any]) -> ObservationSpec:
    return ObservationSpec(
        total_dims=payload["total_dims"],
        encoding_version=payload["encoding_version"],
        fields=tuple(ObservationField(**field) for field in payload["fields"]),
    )


def _observation_activity_from_plain(payload: Mapping[str, Any]) -> ObservationActivity:
    if not payload:
        return ObservationActivity(active_mask=(), group_slices={}, active_field_uuids=())
    return ObservationActivity(
        active_mask=tuple(payload.get("active_mask", ())),
        group_slices={k: slice(v[0], v[1]) for k, v in payload.get("group_slices", {}).items()},
        active_field_uuids=tuple(payload.get("active_field_uuids", ())),
    )


def _action_space_metadata_from_plain(payload: Mapping[str, Any]) -> ActionSpaceMetadata:
    return ActionSpaceMetadata(
        total_actions=payload["total_actions"],
        actions=tuple(ActionMetadata(**entry) for entry in payload.get("actions", [])),
    )


def _meter_metadata_from_plain(payload: Mapping[str, Any]) -> MeterMetadata:
    return MeterMetadata(meters=tuple(MeterInfo(**entry) for entry in payload.get("meters", [])))


def _affordance_metadata_from_plain(payload: Mapping[str, Any]) -> AffordanceMetadata:
    return AffordanceMetadata(affordances=tuple(AffordanceInfo(**entry) for entry in payload.get("affordances", [])))


def _serialize_vfs_profiles(profiles: CompiledVFSProfiles) -> dict[str, Any]:
    """Serialize CompiledVFSProfiles to dict."""

    result: dict[str, Any] = {}

    if profiles.global_profile is not None:
        result["global_profile"] = {
            "variables": [
                {
                    "name": var.name,
                    "type": var.type,
                    "expression": getattr(var, "expression", None),
                    "ast": None,  # AST not serialized (reconstruct on load)
                    "initial_value": var.initial_value,
                    "result_type": var.result_type,
                }
                for var in profiles.global_profile.variables
            ],
            "dependencies": {name: list(deps) for name, deps in profiles.global_profile.dependencies.items()},
        }
    else:
        result["global_profile"] = None

    result["agent_profile"] = profiles.agent_profile
    result["item_profiles"] = profiles.item_profiles

    return result


def _deserialize_vfs_profiles(payload: dict[str, Any]) -> CompiledVFSProfiles:
    """Deserialize CompiledVFSProfiles from dict."""
    from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable
    from townlet.world.expression import ExpressionParser

    global_profile = None
    if payload.get("global_profile") is not None:
        variables = [
            CompiledVariable(
                name=var["name"],
                type=var["type"],
                expression=var.get("expression"),
                ast=ExpressionParser().parse(var["expression"]) if var.get("expression") else None,
                initial_value=var["initial_value"],
                result_type=var.get("result_type"),
            )
            for var in payload["global_profile"]["variables"]
        ]
        dependencies = payload["global_profile"].get("dependencies", {})
        dependencies = {name: tuple(deps) for name, deps in dependencies.items()}
        global_profile = CompiledGlobalProfile(variables=variables, dependencies=dependencies)

    return CompiledVFSProfiles(
        global_profile=global_profile,
        agent_profile=payload.get("agent_profile"),
        item_profiles=payload.get("item_profiles"),
    )


def _serialize_effect_catalog(catalog: EffectCatalog) -> dict[str, Any]:
    """Serialize EffectCatalog to dict.

    Note: Command nodes are not serialized (AST not preserved).
    Full recompilation from YAML is needed for runtime execution.
    """
    return {
        "effects": {
            effect_id: {
                "id": effect.id,
                "scope": effect.scope,
                "duration": effect.duration,
                "intensity": effect.intensity,
                "reapply_policy": effect.reapply_policy,
                "observable": effect.observable,
                # Note: Command nodes not serialized (will be recompiled on load)
            }
            for effect_id, effect in catalog.effects.items()
        }
    }


def _deserialize_effect_catalog(payload: dict[str, Any]) -> EffectCatalog:
    """Deserialize EffectCatalog from dict.

    Note: Creates stub effects without command nodes (not executable).
    Full recompilation from YAML is needed for runtime execution.
    """
    from townlet.effects.catalog import CompiledEffect

    effects = {
        effect_id: CompiledEffect(
            id=effect_data["id"],
            scope=effect_data["scope"],
            duration=effect_data["duration"],
            intensity=effect_data["intensity"],
            reapply_policy=effect_data["reapply_policy"],
            observable=effect_data["observable"],
            on_spawn=[],  # Stub (not executable)
            on_tick=[],
            on_despawn=[],
            on_interrupt=[],
        )
        for effect_id, effect_data in payload["effects"].items()
    }

    return EffectCatalog(effects=effects)
