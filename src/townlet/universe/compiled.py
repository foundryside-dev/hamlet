"""Immutable CompiledUniverse artifact with multi-level support (v2.1)."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, fields, is_dataclass, replace
from pathlib import Path
from typing import Any

import msgpack  # type: ignore[import]
import torch

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.brain_config import BrainConfig
from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.drive_as_code import DriveAsCodeConfig
from townlet.config.environment_config import EnvironmentConfig
from townlet.config.experiment_config import ExperimentConfig
from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.config.stratum_config import StratumConfig
from townlet.config.training_v2_config import TrainingV2Config
from townlet.effects.catalog import EffectCatalog
from townlet.effects.schema import CommandNode, CommandType
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
    RuntimeAction,
    RuntimeActionSpace,
    UniverseMetadata,
)
from townlet.universe.optimization import OptimizationData
from townlet.vfs.observation_builder import VFSObservationSpec
from townlet.vfs.profiles import CompiledGlobalProfile
from townlet.vfs.schema import ObservationField as VfsObservationField
from townlet.vfs.schema import VariableDef

COMPILED_SCHEMA_VERSION = "1.12"

REQUIRED_COMPILED_UNIVERSE_FIELDS = (
    "compiled_schema_version",
    "metadata",
    "observation_spec",
    "observation_activity",
    "vfs_observation_fields",
    "observation_schema_hash",
    "vfs_variables",
    "variable_schema_hash",
    "action_space_metadata",
    "runtime_action_space",
    "action_schema_hash",
    "transition_graph_hash",
    "vfs_hash",
    "meter_metadata",
    "affordance_metadata",
    "optimization_data_raw",
    "experiment",
    "stratum",
    "environment",
    "actions",
    "brain",
    "items_catalog",
    "compiled_vfs_profiles",
    "compiled_effect_catalog",
    "effects_schema",
    "effect_observation_slots",
    "vfs_expression_schema",
    "vfs_history_spec",
    "vfs_observation_marks",
    "vfs_observation_spec",
    "experiment_dir",
    "drive_hash",
    "brain_hash",
    "experiment_hash",
    "stratum_hash",
    "environment_hash",
    "actions_hash",
    "items_hash",
    "all_levels",
)


@dataclass(frozen=True)
class CompiledVFSProfiles:
    """Compiled VFS profiles (global, agent, item)."""

    evaluation_mode: str
    debug_logging: bool
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
    observation_schema_hash: str
    vfs_variables: tuple[VariableDef, ...]
    variable_schema_hash: str
    action_space_metadata: ActionSpaceMetadata
    runtime_action_space: RuntimeActionSpace
    action_schema_hash: str
    transition_graph_hash: str
    vfs_hash: str
    meter_metadata: MeterMetadata
    affordance_metadata: AffordanceMetadata
    optimization_data: OptimizationData

    # Shared experiment-level configs (v2.1)
    experiment: ExperimentConfig
    stratum: StratumConfig
    environment: EnvironmentConfig
    actions: ActionsConfig
    brain: BrainConfig
    items_catalog: ItemsCatalogConfig | None = None

    # Compiled VFS profiles (experiment-level artifact)
    compiled_vfs_profiles: CompiledVFSProfiles | None = None

    # Compiled effects catalog (per-level artifact)
    compiled_effect_catalog: EffectCatalog | None = None
    effects_schema: dict[str, str] | None = None
    effect_observation_slots: int = 0

    # Type schema for runtime VFS expression validation
    vfs_expression_schema: dict[str, str] | None = None

    # Temporal history requirements for VFS expressions
    vfs_history_spec: dict[str, int] | None = None

    # Marks for which VFS variables are observed (for mark-and-sweep evaluation)
    vfs_observation_marks: dict[str, set[str]] | None = None
    # Format: {"global": {"day_count", "is_night"}, "agent": {"motivation"}, "item": {...}}

    # Runtime-ready VFS observation dimensions and variable order.
    vfs_observation_spec: VFSObservationSpec | None = None

    # Provenance
    experiment_dir: Path | None = None
    drive_hash: str | None = None
    brain_hash: str | None = None
    experiment_hash: str | None = None
    stratum_hash: str | None = None
    environment_hash: str | None = None
    actions_hash: str | None = None
    items_hash: str | None = None

    # Multi-level support
    all_levels: dict[str, CompiledUniverse.LevelMetadata] | None = None

    @dataclass(frozen=True)
    class LevelMetadata:
        """Per-level metadata for multi-level compilation."""

        level_name: str
        bars: BarsV2Config
        affordances: AffordancesV2Config
        drive: DriveAsCodeConfig
        curriculum: CurriculumConfig
        training: TrainingV2Config
        observation_spec: ObservationSpec
        observation_activity: ObservationActivity
        action_metadata: ActionSpaceMetadata
        runtime_action_space: RuntimeActionSpace
        action_schema_hash: str
        transition_graph_hash: str
        vfs_hash: str
        meter_metadata: MeterMetadata
        affordance_metadata: AffordanceMetadata
        optimization_data: OptimizationData
        vfs_observation_fields: tuple[VfsObservationField, ...]
        observation_schema_hash: str
        vfs_variables: tuple[VariableDef, ...]
        variable_schema_hash: str
        drive_hash: str | None = None
        curriculum_hash: str | None = None
        bars_hash: str | None = None
        affordances_hash: str | None = None
        training_hash: str | None = None
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

    def metadata_for_level(self, level_name: str) -> UniverseMetadata:
        """Return public metadata aligned to the requested level."""
        level = self.get_level(level_name)
        meter_names = tuple(meter.name for meter in level.meter_metadata.meters)
        meter_name_to_index = {meter.name: meter.index for meter in level.meter_metadata.meters}
        affordance_ids = tuple(affordance.id for affordance in level.affordance_metadata.affordances)
        affordance_id_to_index = {affordance.id: idx for idx, affordance in enumerate(level.affordance_metadata.affordances)}

        ticks_per_day = 0
        if self.stratum.stratum.temporal_support == "enabled" and level.curriculum.curriculum.active_temporal:
            day_length = level.curriculum.curriculum.day_length
            if day_length is None or day_length <= 0:
                raise ValueError(
                    "curriculum.day_length is required when temporal support is enabled and active_temporal=true. " f"Level: {level_name}"
                )
            ticks_per_day = day_length

        return replace(
            self.metadata,
            meter_count=len(meter_names),
            meter_names=meter_names,
            meter_name_to_index=meter_name_to_index,
            affordance_count=len(affordance_ids),
            affordance_ids=affordance_ids,
            affordance_id_to_index=affordance_id_to_index,
            action_count=level.action_metadata.total_actions,
            observation_dim=level.observation_spec.total_dims,
            ticks_per_day=ticks_per_day,
        )

    def clone(self) -> CompiledUniverse:
        """Clone the compiled universe."""
        return CompiledUniverse(
            metadata=deepcopy(self.metadata),
            observation_spec=deepcopy(self.observation_spec),
            observation_activity=deepcopy(self.observation_activity),
            vfs_observation_fields=tuple(deepcopy(self.vfs_observation_fields)),
            observation_schema_hash=self.observation_schema_hash,
            vfs_variables=tuple(deepcopy(self.vfs_variables)),
            variable_schema_hash=self.variable_schema_hash,
            action_space_metadata=deepcopy(self.action_space_metadata),
            runtime_action_space=deepcopy(self.runtime_action_space),
            action_schema_hash=self.action_schema_hash,
            transition_graph_hash=self.transition_graph_hash,
            vfs_hash=self.vfs_hash,
            meter_metadata=deepcopy(self.meter_metadata),
            affordance_metadata=deepcopy(self.affordance_metadata),
            optimization_data=deepcopy(self.optimization_data),
            experiment=deepcopy(self.experiment),
            stratum=deepcopy(self.stratum),
            environment=deepcopy(self.environment),
            actions=deepcopy(self.actions),
            brain=deepcopy(self.brain),
            items_catalog=deepcopy(self.items_catalog) if self.items_catalog is not None else None,
            compiled_vfs_profiles=deepcopy(self.compiled_vfs_profiles) if self.compiled_vfs_profiles is not None else None,
            compiled_effect_catalog=deepcopy(self.compiled_effect_catalog) if self.compiled_effect_catalog is not None else None,
            effects_schema=deepcopy(self.effects_schema) if self.effects_schema is not None else None,
            effect_observation_slots=self.effect_observation_slots,
            vfs_expression_schema=deepcopy(self.vfs_expression_schema) if self.vfs_expression_schema is not None else None,
            vfs_history_spec=deepcopy(self.vfs_history_spec) if self.vfs_history_spec is not None else None,
            vfs_observation_marks=deepcopy(self.vfs_observation_marks) if self.vfs_observation_marks is not None else None,
            vfs_observation_spec=deepcopy(self.vfs_observation_spec) if self.vfs_observation_spec is not None else None,
            experiment_dir=self.experiment_dir,
            drive_hash=self.drive_hash,
            brain_hash=self.brain_hash,
            experiment_hash=self.experiment_hash,
            stratum_hash=self.stratum_hash,
            environment_hash=self.environment_hash,
            actions_hash=self.actions_hash,
            items_hash=self.items_hash,
            all_levels=deepcopy(self.all_levels),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a serialization-friendly dictionary."""
        return {
            "compiled_schema_version": COMPILED_SCHEMA_VERSION,
            "metadata": _dataclass_to_plain(self.metadata),
            "observation_spec": _dataclass_to_plain(self.observation_spec),
            "observation_activity": _dataclass_to_plain(self.observation_activity),
            "vfs_observation_fields": [field.model_dump() for field in self.vfs_observation_fields],
            "observation_schema_hash": self.observation_schema_hash,
            "vfs_variables": [var.model_dump() for var in getattr(self, "vfs_variables", ())],
            "variable_schema_hash": self.variable_schema_hash,
            "action_space_metadata": _dataclass_to_plain(self.action_space_metadata),
            "runtime_action_space": _dataclass_to_plain(self.runtime_action_space),
            "action_schema_hash": self.action_schema_hash,
            "transition_graph_hash": self.transition_graph_hash,
            "vfs_hash": self.vfs_hash,
            "meter_metadata": _dataclass_to_plain(self.meter_metadata),
            "affordance_metadata": _dataclass_to_plain(self.affordance_metadata),
            "optimization_data_raw": {
                "cascade_data": self.optimization_data.cascade_data,
                "modulation_data": self.optimization_data.modulation_data,
                "affordance_position_map": _serialize_affordance_positions(self.optimization_data.affordance_position_map),
            },
            "experiment": self.experiment.model_dump(),
            "stratum": self.stratum.model_dump(),
            "environment": self.environment.model_dump(),
            "actions": self.actions.model_dump(),
            "brain": self.brain.model_dump(),
            "items_catalog": self.items_catalog.model_dump() if self.items_catalog is not None else None,
            "compiled_vfs_profiles": (
                _serialize_vfs_profiles(self.compiled_vfs_profiles) if self.compiled_vfs_profiles is not None else None
            ),
            "compiled_effect_catalog": (
                _serialize_effect_catalog(self.compiled_effect_catalog) if self.compiled_effect_catalog is not None else None
            ),
            "effects_schema": self.effects_schema,
            "effect_observation_slots": self.effect_observation_slots,
            "vfs_expression_schema": self.vfs_expression_schema,
            "vfs_history_spec": self.vfs_history_spec,
            "vfs_observation_marks": (
                {k: list(v) for k, v in self.vfs_observation_marks.items()} if self.vfs_observation_marks is not None else None
            ),  # Convert sets to lists for JSON serialization
            "vfs_observation_spec": (_dataclass_to_plain(self.vfs_observation_spec) if self.vfs_observation_spec is not None else None),
            "experiment_dir": None if self.experiment_dir is None else str(self.experiment_dir),
            "drive_hash": self.drive_hash,
            "brain_hash": self.brain_hash,
            "experiment_hash": self.experiment_hash,
            "stratum_hash": self.stratum_hash,
            "environment_hash": self.environment_hash,
            "actions_hash": self.actions_hash,
            "items_hash": self.items_hash,
            "all_levels": (
                None
                if self.all_levels is None
                else {
                    name: {
                        "level_name": meta.level_name,
                        "bars": meta.bars.model_dump(),
                        "affordances": meta.affordances.model_dump(by_alias=True),
                        "drive": meta.drive.model_dump(),
                        "drive_hash": meta.drive_hash,
                        "curriculum_hash": meta.curriculum_hash,
                        "bars_hash": meta.bars_hash,
                        "affordances_hash": meta.affordances_hash,
                        "training_hash": meta.training_hash,
                        "curriculum": meta.curriculum.model_dump(),
                        "training": meta.training.model_dump(),
                        "observation_spec": _dataclass_to_plain(meta.observation_spec),
                        "observation_activity": _dataclass_to_plain(meta.observation_activity),
                        "action_metadata": _dataclass_to_plain(meta.action_metadata),
                        "runtime_action_space": _dataclass_to_plain(meta.runtime_action_space),
                        "action_schema_hash": meta.action_schema_hash,
                        "transition_graph_hash": meta.transition_graph_hash,
                        "vfs_hash": meta.vfs_hash,
                        "meter_metadata": _dataclass_to_plain(meta.meter_metadata),
                        "affordance_metadata": _dataclass_to_plain(meta.affordance_metadata),
                        "optimization_data_raw": {
                            "cascade_data": meta.optimization_data.cascade_data,
                            "modulation_data": meta.optimization_data.modulation_data,
                            "affordance_position_map": _serialize_affordance_positions(meta.optimization_data.affordance_position_map),
                        },
                        "vfs_observation_fields": [field.model_dump() for field in meta.vfs_observation_fields],
                        "observation_schema_hash": meta.observation_schema_hash,
                        "vfs_variables": [var.model_dump() for var in meta.vfs_variables],
                        "variable_schema_hash": meta.variable_schema_hash,
                    }
                    for name, meta in self.all_levels.items()
                }
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CompiledUniverse:
        """Create CompiledUniverse from a dictionary produced by to_dict/save_to_cache."""
        for field_name in REQUIRED_COMPILED_UNIVERSE_FIELDS:
            _required_field(payload, field_name)

        opt_payload = _required_mapping(payload, "optimization_data_raw")
        affordance_position_map = _deserialize_affordance_positions(
            _required_field(opt_payload, "optimization_data_raw.affordance_position_map")
        )

        all_levels = None
        raw_levels = _required_field(payload, "all_levels")
        if raw_levels is not None:
            all_levels = {}
            for name, meta in raw_levels.items():
                level_opt_payload = _required_mapping(meta, f"all_levels.{name}.optimization_data_raw")
                level_affordance_position_map = _deserialize_affordance_positions(
                    _required_field(level_opt_payload, f"all_levels.{name}.optimization_data_raw.affordance_position_map")
                )
                all_levels[name] = CompiledUniverse.LevelMetadata(
                    level_name=meta["level_name"],
                    bars=BarsV2Config.model_validate(meta["bars"]),
                    affordances=AffordancesV2Config.model_validate(meta["affordances"]),
                    drive=DriveAsCodeConfig.model_validate(meta["drive"]),
                    drive_hash=_required_field(meta, f"all_levels.{name}.drive_hash"),
                    curriculum_hash=_required_field(meta, f"all_levels.{name}.curriculum_hash"),
                    bars_hash=_required_field(meta, f"all_levels.{name}.bars_hash"),
                    affordances_hash=_required_field(meta, f"all_levels.{name}.affordances_hash"),
                    training_hash=_required_field(meta, f"all_levels.{name}.training_hash"),
                    curriculum=CurriculumConfig.model_validate(meta["curriculum"]),
                    training=TrainingV2Config.model_validate(meta["training"]),
                    observation_spec=_observation_spec_from_plain(meta["observation_spec"]),
                    observation_activity=_observation_activity_from_plain(
                        _required_mapping(meta, f"all_levels.{name}.observation_activity")
                    ),
                    action_metadata=_action_space_metadata_from_plain(meta["action_metadata"], f"all_levels.{name}.action_metadata"),
                    runtime_action_space=_runtime_action_space_from_plain(
                        _required_mapping(meta, f"all_levels.{name}.runtime_action_space"),
                        f"all_levels.{name}.runtime_action_space",
                    ),
                    action_schema_hash=_required_field(meta, f"all_levels.{name}.action_schema_hash"),
                    transition_graph_hash=_required_field(meta, f"all_levels.{name}.transition_graph_hash"),
                    vfs_hash=_required_field(meta, f"all_levels.{name}.vfs_hash"),
                    meter_metadata=_meter_metadata_from_plain(meta["meter_metadata"], f"all_levels.{name}.meter_metadata"),
                    affordance_metadata=_affordance_metadata_from_plain(
                        meta["affordance_metadata"], f"all_levels.{name}.affordance_metadata"
                    ),
                    optimization_data=OptimizationData(
                        cascade_data=_required_field(level_opt_payload, f"all_levels.{name}.optimization_data_raw.cascade_data"),
                        modulation_data=_required_field(level_opt_payload, f"all_levels.{name}.optimization_data_raw.modulation_data"),
                        affordance_position_map=level_affordance_position_map,
                    ),
                    vfs_observation_fields=tuple(
                        VfsObservationField(**field) for field in _required_field(meta, f"all_levels.{name}.vfs_observation_fields")
                    ),
                    observation_schema_hash=_required_field(meta, f"all_levels.{name}.observation_schema_hash"),
                    vfs_variables=tuple(VariableDef(**var) for var in _required_field(meta, f"all_levels.{name}.vfs_variables")),
                    variable_schema_hash=_required_field(meta, f"all_levels.{name}.variable_schema_hash"),
                )

        return CompiledUniverse(
            metadata=UniverseMetadata(**payload["metadata"]),
            observation_spec=_observation_spec_from_plain(payload["observation_spec"]),
            observation_activity=_observation_activity_from_plain(_required_mapping(payload, "observation_activity")),
            vfs_observation_fields=tuple(VfsObservationField(**field) for field in _required_field(payload, "vfs_observation_fields")),
            observation_schema_hash=_required_field(payload, "observation_schema_hash"),
            vfs_variables=tuple(VariableDef(**var) for var in _required_field(payload, "vfs_variables")),
            variable_schema_hash=_required_field(payload, "variable_schema_hash"),
            action_space_metadata=_action_space_metadata_from_plain(payload["action_space_metadata"]),
            runtime_action_space=_runtime_action_space_from_plain(_required_mapping(payload, "runtime_action_space")),
            action_schema_hash=_required_field(payload, "action_schema_hash"),
            transition_graph_hash=_required_field(payload, "transition_graph_hash"),
            vfs_hash=_required_field(payload, "vfs_hash"),
            meter_metadata=_meter_metadata_from_plain(payload["meter_metadata"]),
            affordance_metadata=_affordance_metadata_from_plain(payload["affordance_metadata"]),
            optimization_data=OptimizationData(
                cascade_data=_required_field(opt_payload, "optimization_data_raw.cascade_data"),
                modulation_data=_required_field(opt_payload, "optimization_data_raw.modulation_data"),
                affordance_position_map=affordance_position_map,
            ),
            experiment=ExperimentConfig.model_validate(payload["experiment"]),
            stratum=StratumConfig.model_validate(payload["stratum"]),
            environment=EnvironmentConfig.model_validate(payload["environment"]),
            actions=ActionsConfig.model_validate(payload["actions"]),
            brain=BrainConfig.model_validate(payload["brain"]),
            items_catalog=(
                ItemsCatalogConfig.model_validate(_required_field(payload, "items_catalog"))
                if _required_field(payload, "items_catalog") is not None
                else None
            ),
            compiled_vfs_profiles=(
                _deserialize_vfs_profiles(_required_field(payload, "compiled_vfs_profiles"))
                if _required_field(payload, "compiled_vfs_profiles") is not None
                else None
            ),
            compiled_effect_catalog=(
                _deserialize_effect_catalog(_required_field(payload, "compiled_effect_catalog"))
                if _required_field(payload, "compiled_effect_catalog") is not None
                else None
            ),
            effects_schema=_required_field(payload, "effects_schema"),
            effect_observation_slots=_required_field(payload, "effect_observation_slots"),
            vfs_expression_schema=_required_field(payload, "vfs_expression_schema"),
            vfs_history_spec=_required_field(payload, "vfs_history_spec"),
            vfs_observation_marks=(
                {k: set(v) for k, v in _required_field(payload, "vfs_observation_marks").items()}
                if _required_field(payload, "vfs_observation_marks") is not None
                else None
            ),  # Convert lists back to sets
            vfs_observation_spec=_vfs_observation_spec_from_plain(_required_field(payload, "vfs_observation_spec")),
            experiment_dir=None if _required_field(payload, "experiment_dir") is None else Path(payload["experiment_dir"]),
            drive_hash=_required_field(payload, "drive_hash"),
            brain_hash=_required_field(payload, "brain_hash"),
            experiment_hash=_required_field(payload, "experiment_hash"),
            stratum_hash=_required_field(payload, "stratum_hash"),
            environment_hash=_required_field(payload, "environment_hash"),
            actions_hash=_required_field(payload, "actions_hash"),
            items_hash=_required_field(payload, "items_hash"),
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
        payload = msgpack.unpackb(path.read_bytes(), raw=False, strict_map_key=False)
        schema_version = _required_field(payload, "compiled_schema_version")
        if schema_version != COMPILED_SCHEMA_VERSION:
            raise ValueError(
                f"Compiled universe schema mismatch for {path}: "
                f"found '{schema_version}', expected '{COMPILED_SCHEMA_VERSION}'. "
                "Recompile the config pack with `python -m townlet.universe compile <config_dir>`."
            )
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
            "brain": self.brain,
            "curriculum": level.curriculum,
            "bars": level.bars,
            "affordances": level.affordances,
            "drive": level.drive,
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


def _missing_required_field(field_name: str) -> ValueError:
    return ValueError(f"Compiled universe cache is missing required field '{field_name}'; recompile the config pack.")


def _required_field(payload: Mapping[str, Any], field_name: str) -> Any:
    key = field_name.rsplit(".", 1)[-1]
    if key not in payload:
        raise _missing_required_field(field_name)
    return payload[key]


def _required_mapping(payload: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
    value = _required_field(payload, field_name)
    if not isinstance(value, Mapping):
        raise ValueError(f"Compiled universe cache field '{field_name}' must be a mapping; recompile the config pack.")
    return value


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
    return ObservationActivity(
        active_mask=tuple(_required_field(payload, "observation_activity.active_mask")),
        group_slices={k: slice(v[0], v[1]) for k, v in _required_field(payload, "observation_activity.group_slices").items()},
        active_field_uuids=tuple(_required_field(payload, "observation_activity.active_field_uuids")),
    )


def _action_space_metadata_from_plain(payload: Mapping[str, Any], field_name: str = "action_space_metadata") -> ActionSpaceMetadata:
    return ActionSpaceMetadata(
        total_actions=_required_field(payload, f"{field_name}.total_actions"),
        actions=tuple(ActionMetadata(**entry) for entry in _required_field(payload, f"{field_name}.actions")),
        labels=_required_field(payload, f"{field_name}.labels"),
        label_description=_required_field(payload, f"{field_name}.label_description"),
        label_domain=_required_field(payload, f"{field_name}.label_domain"),
    )


def _runtime_action_space_from_plain(payload: Mapping[str, Any], field_name: str = "runtime_action_space") -> RuntimeActionSpace:
    return RuntimeActionSpace(
        actions=tuple(RuntimeAction(**entry) for entry in _required_field(payload, f"{field_name}.actions")),
        substrate_action_count=_required_field(payload, f"{field_name}.substrate_action_count"),
        custom_action_count=_required_field(payload, f"{field_name}.custom_action_count"),
        affordance_action_count=_required_field(payload, f"{field_name}.affordance_action_count"),
        enabled_action_names=_required_field(payload, f"{field_name}.enabled_action_names"),
    )


def _meter_metadata_from_plain(payload: Mapping[str, Any], field_name: str = "meter_metadata") -> MeterMetadata:
    return MeterMetadata(meters=tuple(MeterInfo(**entry) for entry in _required_field(payload, f"{field_name}.meters")))


def _affordance_metadata_from_plain(payload: Mapping[str, Any], field_name: str = "affordance_metadata") -> AffordanceMetadata:
    return AffordanceMetadata(affordances=tuple(AffordanceInfo(**entry) for entry in _required_field(payload, f"{field_name}.affordances")))


def _vfs_observation_spec_from_plain(payload: Mapping[str, Any] | None) -> VFSObservationSpec | None:
    if payload is None:
        return None
    return VFSObservationSpec(
        global_vfs_dim=_required_field(payload, "vfs_observation_spec.global_vfs_dim"),
        agent_vfs_dim=_required_field(payload, "vfs_observation_spec.agent_vfs_dim"),
        item_vfs_dim=_required_field(payload, "vfs_observation_spec.item_vfs_dim"),
        global_vars=tuple(_required_field(payload, "vfs_observation_spec.global_vars")),
        agent_vars=tuple(_required_field(payload, "vfs_observation_spec.agent_vars")),
        item_profile_vars={
            name: tuple(values) for name, values in _required_field(payload, "vfs_observation_spec.item_profile_vars").items()
        },
        item_vars_per_slot=_required_field(payload, "vfs_observation_spec.item_vars_per_slot"),
        global_active_mask=tuple(_required_field(payload, "vfs_observation_spec.global_active_mask")),
        agent_active_mask=tuple(_required_field(payload, "vfs_observation_spec.agent_active_mask")),
        item_active_mask=tuple(_required_field(payload, "vfs_observation_spec.item_active_mask")),
        max_items_per_agent=_required_field(payload, "vfs_observation_spec.max_items_per_agent"),
        max_item_profiles=_required_field(payload, "vfs_observation_spec.max_item_profiles"),
        max_tensor_elements=_required_field(payload, "vfs_observation_spec.max_tensor_elements"),
    )


def _serialize_vfs_profiles(profiles: CompiledVFSProfiles) -> dict[str, Any]:
    """Serialize CompiledVFSProfiles to dict."""

    result: dict[str, Any] = {
        "evaluation_mode": profiles.evaluation_mode,
        "debug_logging": profiles.debug_logging,
    }

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
                    "exposed_to": list(var.exposed_to),
                    "semantic_type": getattr(var, "semantic_type", "custom"),
                }
                for var in profiles.global_profile.variables
            ],
            "dependencies": {name: list(deps) for name, deps in profiles.global_profile.dependencies.items()},
        }
    else:
        result["global_profile"] = None

    result["agent_profile"] = profiles.agent_profile

    if profiles.item_profiles:
        item_profiles_serialized: dict[str, Any] = {}
        for name, profile in profiles.item_profiles.items():
            item_profiles_serialized[name] = {
                "profile_name": profile.profile_name,
                "variables": [
                    {
                        "name": var.name,
                        "type": var.type,
                        "expression": getattr(var, "expression", None),
                        "initial_value": var.initial_value,
                        "result_type": var.result_type,
                        "shape": var.shape,
                        "initial_value_mode": var.initial_value_mode,
                        "initial_value_params": var.initial_value_params,
                        "dims": var.dims,
                        "exposed_to": list(var.exposed_to),
                        "semantic_type": getattr(var, "semantic_type", "custom"),
                    }
                    for var in profile.variables
                ],
            }
        result["item_profiles"] = item_profiles_serialized
    else:
        result["item_profiles"] = None

    return result


def _deserialize_vfs_profiles(payload: dict[str, Any]) -> CompiledVFSProfiles:
    """Deserialize CompiledVFSProfiles from dict."""
    from townlet.vfs.profiles import CompiledGlobalProfile, CompiledItemProfile, CompiledVariable
    from townlet.world.expression import ExpressionParser

    global_profile = None
    if payload.get("global_profile") is not None:
        variables = []
        for var in payload["global_profile"]["variables"]:
            variables.append(
                CompiledVariable(
                    name=var["name"],
                    type=var["type"],
                    expression=var.get("expression"),
                    ast=ExpressionParser().parse(var["expression"]) if var.get("expression") else None,
                    initial_value=var["initial_value"],
                    result_type=var.get("result_type"),
                    exposed_to=tuple(var.get("exposed_to", ["agent"])),
                    semantic_type=var.get("semantic_type", "custom"),
                )
            )
        dependencies = payload["global_profile"].get("dependencies", {})
        dependencies = {name: tuple(deps) for name, deps in dependencies.items()}
        global_profile = CompiledGlobalProfile(variables=variables, dependencies=dependencies)

    item_profiles = None
    raw_items = payload.get("item_profiles")
    if raw_items:
        item_profiles = {}
        for name, profile in raw_items.items():
            variables = [
                CompiledVariable(
                    name=var["name"],
                    type=var["type"],
                    expression=var.get("expression"),
                    ast=ExpressionParser().parse(var["expression"]) if var.get("expression") else None,
                    initial_value=var.get("initial_value"),
                    result_type=var.get("result_type"),
                    shape=var.get("shape"),
                    initial_value_mode=var.get("initial_value_mode"),
                    initial_value_params=var.get("initial_value_params"),
                    dims=var.get("dims"),
                    exposed_to=tuple(var.get("exposed_to", ["agent"])),
                    semantic_type=var.get("semantic_type", "custom"),
                )
                for var in profile.get("variables", [])
            ]
            item_profiles[name] = CompiledItemProfile(profile_name=profile["profile_name"], variables=variables)

    return CompiledVFSProfiles(
        evaluation_mode=payload["evaluation_mode"],
        debug_logging=payload["debug_logging"],
        global_profile=global_profile,
        agent_profile=payload.get("agent_profile"),
        item_profiles=item_profiles,
    )


def _serialize_effect_catalog(catalog: EffectCatalog) -> dict[str, Any]:
    """Serialize EffectCatalog to dict."""
    return {
        "effects": {
            effect_id: {
                "id": effect.id,
                "scope": effect.scope,
                "duration": effect.duration,
                "intensity": effect.intensity,
                "reapply_policy": effect.reapply_policy,
                "observable": effect.observable,
                "on_spawn": _serialize_command_pipeline(effect.on_spawn),
                "on_tick": _serialize_command_pipeline(effect.on_tick),
                "on_despawn": _serialize_command_pipeline(effect.on_despawn),
                "on_interrupt": _serialize_command_pipeline(effect.on_interrupt),
            }
            for effect_id, effect in catalog.effects.items()
        }
    }


def _deserialize_effect_catalog(payload: dict[str, Any]) -> EffectCatalog:
    """Deserialize EffectCatalog from dict."""
    from townlet.effects.catalog import CompiledEffect

    effects = {
        effect_id: CompiledEffect(
            id=effect_data["id"],
            scope=effect_data["scope"],
            duration=effect_data["duration"],
            intensity=effect_data["intensity"],
            reapply_policy=effect_data["reapply_policy"],
            observable=effect_data["observable"],
            on_spawn=_deserialize_command_pipeline(effect_data["on_spawn"]),
            on_tick=_deserialize_command_pipeline(effect_data["on_tick"]),
            on_despawn=_deserialize_command_pipeline(effect_data["on_despawn"]),
            on_interrupt=_deserialize_command_pipeline(effect_data["on_interrupt"]),
        )
        for effect_id, effect_data in payload["effects"].items()
    }

    return EffectCatalog(effects=effects)


def _serialize_command_pipeline(commands: list[CommandNode]) -> list[dict[str, Any]]:
    return [_serialize_command_node(command) for command in commands]


def _serialize_command_node(command: CommandNode) -> dict[str, Any]:
    return {
        "type": command.type.value,
        "path": command.path,
        "value_expr": command.value_expr,
        "effect_id": command.effect_id,
        "target": command.target,
        "target_expr": command.target_expr,
        "duration": command.duration,
        "intensity": command.intensity,
        "item_type": command.item_type,
        "position": command.position,
        "position_expr": command.position_expr,
        "quantity": command.quantity,
        "initial_state": command.initial_state,
        "sample_distribution": command.sample_distribution,
        "sample_params": command.sample_params,
        "sample_store_path": command.sample_store_path,
        "condition_expr": command.condition_expr,
        "then_commands": _serialize_command_pipeline(command.then_commands or []),
        "else_commands": _serialize_command_pipeline(command.else_commands or []),
        "collection": command.collection,
        "collection_expr": command.collection_expr,
        "iterator": command.iterator,
        "body": _serialize_command_pipeline(command.body or []),
        "radius": command.radius,
        "switch_expr": command.switch_expr,
        "cases": [
            {"when": when_expr, "commands": _serialize_command_pipeline(case_commands)} for when_expr, case_commands in command.cases or []
        ],
        "default_commands": _serialize_command_pipeline(command.default_commands or []),
        "reduce_expr": command.reduce_expr,
        "reduce_iterator": command.reduce_iterator,
        "reduce_init_expr": command.reduce_init_expr,
        "reduce_body_expr": command.reduce_body_expr,
        "reduce_target": command.reduce_target,
        "parallel_commands": _serialize_command_pipeline(command.parallel_commands or []),
        "delay_ticks_expr": command.delay_ticks_expr,
        "delay_commands": _serialize_command_pipeline(command.delay_commands or []),
    }


def _deserialize_command_pipeline(payload: list[dict[str, Any]]) -> list[CommandNode]:
    from townlet.world.expression import ExpressionParser

    commands = [_deserialize_command_node(command_data) for command_data in payload]
    parser = ExpressionParser()
    for command in commands:
        _hydrate_command_asts(command, parser)
    return commands


def _deserialize_command_node(payload: dict[str, Any]) -> CommandNode:
    return CommandNode(
        type=CommandType(payload["type"]),
        path=payload.get("path"),
        value_expr=payload.get("value_expr"),
        effect_id=payload.get("effect_id"),
        target=payload.get("target"),
        target_expr=payload.get("target_expr"),
        duration=payload.get("duration"),
        intensity=payload.get("intensity"),
        item_type=payload.get("item_type"),
        position=payload.get("position"),
        position_expr=payload.get("position_expr"),
        quantity=payload.get("quantity"),
        initial_state=payload.get("initial_state"),
        sample_distribution=payload.get("sample_distribution"),
        sample_params=payload.get("sample_params"),
        sample_store_path=payload.get("sample_store_path"),
        condition_expr=payload.get("condition_expr"),
        then_commands=[_deserialize_command_node(command) for command in payload["then_commands"]],
        else_commands=[_deserialize_command_node(command) for command in payload["else_commands"]],
        collection=payload.get("collection"),
        collection_expr=payload.get("collection_expr"),
        iterator=payload.get("iterator"),
        body=[_deserialize_command_node(command) for command in payload["body"]],
        radius=payload.get("radius"),
        switch_expr=payload.get("switch_expr"),
        cases=[(case["when"], [_deserialize_command_node(command) for command in case["commands"]]) for case in payload["cases"]],
        default_commands=[_deserialize_command_node(command) for command in payload["default_commands"]],
        reduce_expr=payload.get("reduce_expr"),
        reduce_iterator=payload.get("reduce_iterator"),
        reduce_init_expr=payload.get("reduce_init_expr"),
        reduce_body_expr=payload.get("reduce_body_expr"),
        reduce_target=payload.get("reduce_target"),
        parallel_commands=[_deserialize_command_node(command) for command in payload["parallel_commands"]],
        delay_ticks_expr=payload.get("delay_ticks_expr"),
        delay_commands=[_deserialize_command_node(command) for command in payload["delay_commands"]],
    )


def _hydrate_command_asts(command: CommandNode, parser: Any) -> None:
    if command.value_expr is not None:
        command.value_ast = parser.parse(command.value_expr)

    simple_target = command.target in {"self", "target"} or isinstance(command.target, int)
    if command.target_expr is not None and not simple_target:
        command.target_ast = parser.parse(command.target_expr)

    simple_position = command.position in {"random", "self", "target"} or command.position is None
    if command.position_expr is not None and not simple_position:
        command.position_ast = parser.parse(command.position_expr)

    if command.sample_params:
        command.sample_param_asts = {}
        for name, raw_value in command.sample_params.items():
            if (command.sample_distribution or "").lower() == "categorical" and name == "probs":
                command.sample_param_asts[name] = [parser.parse(str(probability)) for probability in raw_value]
            else:
                command.sample_param_asts[name] = parser.parse(str(raw_value))

    if command.condition_expr is not None:
        command.condition_ast = parser.parse(command.condition_expr)

    if command.collection_expr is not None:
        command.collection_ast = parser.parse(command.collection_expr)

    if command.switch_expr is not None:
        command.switch_ast = parser.parse(command.switch_expr)
        command.case_asts = [(parser.parse(when_expr), case_commands) for when_expr, case_commands in command.cases or []]

    if command.reduce_expr is not None:
        command.collection_ast = parser.parse(command.reduce_expr)
    if command.reduce_init_expr is not None:
        command.reduce_init_ast = parser.parse(command.reduce_init_expr)
    if command.reduce_body_expr is not None:
        command.reduce_body_ast = parser.parse(command.reduce_body_expr)

    if command.delay_ticks_expr is not None:
        command.delay_ticks_ast = parser.parse(command.delay_ticks_expr)

    for child in _iter_nested_commands(command):
        _hydrate_command_asts(child, parser)


def _iter_nested_commands(command: CommandNode) -> list[CommandNode]:
    children: list[CommandNode] = []
    children.extend(command.then_commands or [])
    children.extend(command.else_commands or [])
    children.extend(command.body or [])
    children.extend(command.default_commands or [])
    children.extend(command.parallel_commands or [])
    children.extend(command.delay_commands or [])
    for _, case_commands in command.cases or []:
        children.extend(case_commands)
    return children
