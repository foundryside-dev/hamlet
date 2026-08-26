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
    RuntimeAction,
    RuntimeActionSpace,
    UniverseMetadata,
)
from townlet.universe.dto.token_spec import SlotBinding, TokenSpec, TokenTypeSchema
from townlet.universe.optimization import OptimizationData
from townlet.vfs.profiles import CompiledGlobalProfile
from townlet.vfs.schema import VariableDef
from townlet.vfs.transition_schedule import (
    VTCTransitionSchedule,
    build_vtc_transition_schedule,
    serialize_vtc_transition_schedule,
    social_rules_from_transition_payload,
)

# 1.15: the bars block became N per-meter observation fields with per-meter normalization
# specs, and VFS source widths split from observed widths (PDR-0054 W3/W4). Every cache built
# before that describes a different observation layout, so the bump converts a silent
# wrong-shape serve into the "recompile the config pack" error this constant already implements.
# 1.16: the `obs_vfs` block became one field per exposed global/agent profile variable plus
# the `obs_item_slots` feature (PDR-0075). A pack whose only profile variables are item-scoped
# does not touch vfs_profiles.yaml for this cut, so its config fingerprint would NOT change and
# a pre-cut cache would serve the old field list silently — the bump is what refuses it.
# 1.17: every compiled `ObservationField` carries a required `feature` (and `feature_ref` for
# meters) from `townlet.universe.dto.observation_feature`; the runtime dispatches on it instead
# of on field names (WS-4 unit 4). No pack changes for this cut, so no config fingerprint moves;
# a pre-cut cache would deserialize into a DTO that now requires `feature` and fail obscurely —
# the bump makes it the "recompile" error instead.
# 1.19: `pack_brain_hash` is required (PDR-0027 lineage legibility) and `brain` is the
# EFFECTIVE base brain for the compiled level (a level's own brain.yaml replaces the pack
# brain). A pre-cut cache lacks the field and would carry the wrong brain semantics — the
# bump makes it a clean "recompile" instead.
# 1.20: UniverseMetadata dropped the never-computed economics fields
# (max_sustainable_income, total_affordance_costs, economic_balance — hardcoded 0.0 since
# introduction). A 1.19 cache's metadata payload carries the extra keys and would fail
# UniverseMetadata(**payload) obscurely; the bump makes it the "recompile" error instead.
# 1.21: the artifact gains the `token_spec` block (unit 3 Task 7) with its two hashes —
# `token_type_schema_hash` (transfer contract) and `layout_hash` (flat-net contract) — and
# `token_advisories`, ALONGSIDE the unchanged observation_spec family (the swap is Task 10).
# The new fields are required in the payload, so a 1.20 cache would fail from_dict on a
# missing-field error naming one key; the bump makes it the "recompile" error instead.
# 1.22: THE CUT (unit 3 Task 10). The `observation_spec`, `observation_activity`,
# `vfs_observation_fields`, `vfs_observation_spec` and `effect_observation_slots` blocks are
# DELETED and the `token_spec` block is the artifact's only observation product;
# `observation_schema_hash` is REDEFINED over the TokenSpec (token-obs spec §5) and therefore
# `vfs_hash` moves on every pack (registered as DIV-008). A 1.21 cache describes an entirely
# different observation ABI whose stored hashes would silently mis-gate a checkpoint; the bump
# makes it the "recompile the config pack" error.
COMPILED_SCHEMA_VERSION = "1.22"

REQUIRED_COMPILED_UNIVERSE_FIELDS = (
    "compiled_schema_version",
    "metadata",
    "observation_schema_hash",
    "vfs_variables",
    "variable_schema_hash",
    "action_space_metadata",
    "runtime_action_space",
    "action_schema_hash",
    "transition_graph_hash",
    "transition_schedule",
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
    "vfs_expression_schema",
    "vfs_history_spec",
    "vfs_evaluation_marks",
    "token_spec",
    "token_type_schema_hash",
    "layout_hash",
    "token_advisories",
    "experiment_dir",
    "drive_hash",
    "curriculum_hash",
    "bars_hash",
    "affordances_hash",
    "training_hash",
    "brain_hash",
    "pack_brain_hash",
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
    # A compiled agent profile is a CompiledGlobalProfile: both compile through
    # VFSProfileCompiler.compile_global_profile (townlet/universe/compilers/vfs.py).
    agent_profile: CompiledGlobalProfile | None = None
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
    # The token observation artifact IS the compiler's observation product (unit-3
    # Task-10 cut). The ObservationSpec / ObservationActivity / VFS-mirror family it
    # replaced is deleted, not carried.
    token_spec: TokenSpec
    # Transfer contract: hash of the TokenSpec type schemas (per-type payload feature
    # names + filler kinds + encoding version); equal hashes mean per-type encoder
    # weights are exchangeable.
    token_type_schema_hash: str
    # Flat-net contract: hash of the serialization layout (type order, capacities, slot
    # bindings, total_dims); equal hashes mean a flat reader sees identical dim meanings.
    layout_hash: str
    # Type schema + slot-binding CONTENT over the TokenSpec (token-obs spec §5). Slot 2
    # of the unchanged four-term `compute_vfs_hash` composition — which is why `vfs_hash`
    # moved on every pack at the cut (DIV-008).
    observation_schema_hash: str
    vfs_variables: tuple[VariableDef, ...]
    variable_schema_hash: str
    action_space_metadata: ActionSpaceMetadata
    runtime_action_space: RuntimeActionSpace
    action_schema_hash: str
    transition_graph_hash: str
    transition_schedule: VTCTransitionSchedule
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

    # Type schema for runtime VFS expression validation
    vfs_expression_schema: dict[str, str] | None = None

    # Temporal history requirements for VFS expressions
    vfs_history_spec: dict[str, int] | None = None

    # Marks for which VFS expression variables are evaluated (for mark-and-sweep evaluation).
    # Derived from exposure (profile exposed_to, plus overlay observable), not observation
    # directly — the field is named for what it does (hamlet-df3a96bbac).
    vfs_evaluation_marks: dict[str, set[str]] | None = None
    # Format: {"global": {"day_count", "is_night"}, "agent": {"motivation"}}

    # Compile-time token advisories. Exposure-rule and effect-budget failures are
    # compile REFUSALS since the unit-3 cut; what remains here is the mean-aggregator
    # census advisory (an instrument, not a gate).
    token_advisories: tuple[str, ...] = ()

    # Provenance
    experiment_dir: Path | None = None
    drive_hash: str | None = None
    curriculum_hash: str | None = None
    bars_hash: str | None = None
    affordances_hash: str | None = None
    training_hash: str | None = None
    # brain_hash is the SHA256 of the PRIMARY LEVEL's EFFECTIVE brain config —
    # brain.yaml merged with that level's training.yaml overrides via
    # apply_training_overrides — not of brain.yaml. It is level-scoped, like drive_hash.
    brain_hash: str | None = None
    # Hash of the PACK-ROOT brain under the primary level's training overrides (PDR-0027).
    # pack_brain_hash != brain_hash means: this level declared its own brain.yaml.
    pack_brain_hash: str | None = None
    experiment_hash: str | None = None
    stratum_hash: str | None = None
    environment_hash: str | None = None
    actions_hash: str | None = None
    items_hash: str | None = None

    # Multi-level support
    all_levels: dict[str, CompiledUniverse.LevelMetadata] | None = None

    @property
    def brain_forked(self) -> bool:
        """True when the compiled level's effective brain diverges from the pack baseline."""
        return self.pack_brain_hash is not None and self.pack_brain_hash != self.brain_hash

    @dataclass(frozen=True)
    class LevelMetadata:
        """Per-level metadata for multi-level compilation."""

        level_name: str
        bars: BarsV2Config
        affordances: AffordancesV2Config
        drive: DriveAsCodeConfig
        curriculum: CurriculumConfig
        training: TrainingV2Config
        # The token observation artifact — see the CompiledUniverse fields of the same
        # names for the contracts.
        token_spec: TokenSpec
        token_type_schema_hash: str
        layout_hash: str
        action_metadata: ActionSpaceMetadata
        runtime_action_space: RuntimeActionSpace
        action_schema_hash: str
        transition_graph_hash: str
        transition_schedule: VTCTransitionSchedule
        vfs_hash: str
        meter_metadata: MeterMetadata
        affordance_metadata: AffordanceMetadata
        optimization_data: OptimizationData
        observation_schema_hash: str
        vfs_variables: tuple[VariableDef, ...]
        variable_schema_hash: str
        drive_hash: str | None = None
        curriculum_hash: str | None = None
        bars_hash: str | None = None
        affordances_hash: str | None = None
        training_hash: str | None = None
        items_appearance: ItemsAppearanceConfig | None = None
        token_advisories: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "token_advisories", tuple(self.token_advisories))
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
            # primary_level MUST be re-projected with the rest. This method realigns
            # eight fields onto the requested level; leaving the ninth pointing at
            # the level the universe was COMPILED at makes the returned object
            # internally inconsistent, and primary_level is the one field that is
            # not recoverable from any other — L0_5_dual_resource and
            # L1_full_observability are identical on every hash a checkpoint stamps.
            primary_level=level_name,
            meter_count=len(meter_names),
            meter_names=meter_names,
            meter_name_to_index=meter_name_to_index,
            affordance_count=len(affordance_ids),
            affordance_ids=affordance_ids,
            affordance_id_to_index=affordance_id_to_index,
            action_count=level.action_metadata.total_actions,
            observation_dim=level.token_spec.total_dims,
            ticks_per_day=ticks_per_day,
        )

    def clone(self) -> CompiledUniverse:
        """Clone the compiled universe."""
        return CompiledUniverse(
            metadata=deepcopy(self.metadata),
            # Frozen, tuple-carrying dataclass: safe to share.
            token_spec=self.token_spec,
            token_type_schema_hash=self.token_type_schema_hash,
            layout_hash=self.layout_hash,
            observation_schema_hash=self.observation_schema_hash,
            vfs_variables=tuple(deepcopy(self.vfs_variables)),
            variable_schema_hash=self.variable_schema_hash,
            action_space_metadata=deepcopy(self.action_space_metadata),
            runtime_action_space=deepcopy(self.runtime_action_space),
            action_schema_hash=self.action_schema_hash,
            transition_graph_hash=self.transition_graph_hash,
            transition_schedule=deepcopy(self.transition_schedule),
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
            vfs_expression_schema=deepcopy(self.vfs_expression_schema) if self.vfs_expression_schema is not None else None,
            vfs_history_spec=deepcopy(self.vfs_history_spec) if self.vfs_history_spec is not None else None,
            vfs_evaluation_marks=deepcopy(self.vfs_evaluation_marks) if self.vfs_evaluation_marks is not None else None,
            token_advisories=self.token_advisories,
            experiment_dir=self.experiment_dir,
            drive_hash=self.drive_hash,
            curriculum_hash=self.curriculum_hash,
            bars_hash=self.bars_hash,
            affordances_hash=self.affordances_hash,
            training_hash=self.training_hash,
            brain_hash=self.brain_hash,
            pack_brain_hash=self.pack_brain_hash,
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
            "token_spec": _serialize_token_spec(self.token_spec),
            "token_type_schema_hash": self.token_type_schema_hash,
            "layout_hash": self.layout_hash,
            "observation_schema_hash": self.observation_schema_hash,
            "vfs_variables": [var.model_dump() for var in getattr(self, "vfs_variables", ())],
            "variable_schema_hash": self.variable_schema_hash,
            "action_space_metadata": _dataclass_to_plain(self.action_space_metadata),
            "runtime_action_space": _dataclass_to_plain(self.runtime_action_space),
            "action_schema_hash": self.action_schema_hash,
            "transition_graph_hash": self.transition_graph_hash,
            "transition_schedule": serialize_vtc_transition_schedule(self.transition_schedule),
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
            "vfs_expression_schema": self.vfs_expression_schema,
            "vfs_history_spec": self.vfs_history_spec,
            "vfs_evaluation_marks": (
                {k: list(v) for k, v in self.vfs_evaluation_marks.items()} if self.vfs_evaluation_marks is not None else None
            ),  # Convert sets to lists for JSON serialization
            "token_advisories": list(self.token_advisories),
            "experiment_dir": None if self.experiment_dir is None else str(self.experiment_dir),
            "drive_hash": self.drive_hash,
            "curriculum_hash": self.curriculum_hash,
            "bars_hash": self.bars_hash,
            "affordances_hash": self.affordances_hash,
            "training_hash": self.training_hash,
            "brain_hash": self.brain_hash,
            "pack_brain_hash": self.pack_brain_hash,
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
                        "token_spec": _serialize_token_spec(meta.token_spec),
                        "token_type_schema_hash": meta.token_type_schema_hash,
                        "layout_hash": meta.layout_hash,
                        "action_metadata": _dataclass_to_plain(meta.action_metadata),
                        "runtime_action_space": _dataclass_to_plain(meta.runtime_action_space),
                        "action_schema_hash": meta.action_schema_hash,
                        "transition_graph_hash": meta.transition_graph_hash,
                        "transition_schedule": serialize_vtc_transition_schedule(meta.transition_schedule),
                        "vfs_hash": meta.vfs_hash,
                        "meter_metadata": _dataclass_to_plain(meta.meter_metadata),
                        "affordance_metadata": _dataclass_to_plain(meta.affordance_metadata),
                        "optimization_data_raw": {
                            "cascade_data": meta.optimization_data.cascade_data,
                            "modulation_data": meta.optimization_data.modulation_data,
                            "affordance_position_map": _serialize_affordance_positions(meta.optimization_data.affordance_position_map),
                        },
                        "observation_schema_hash": meta.observation_schema_hash,
                        "vfs_variables": [var.model_dump() for var in meta.vfs_variables],
                        "variable_schema_hash": meta.variable_schema_hash,
                        "token_advisories": list(meta.token_advisories),
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
                level_bars = BarsV2Config.model_validate(meta["bars"])
                level_affordances = AffordancesV2Config.model_validate(meta["affordances"])
                level_drive = DriveAsCodeConfig.model_validate(meta["drive"])
                level_curriculum = CurriculumConfig.model_validate(meta["curriculum"])
                level_training = TrainingV2Config.model_validate(meta["training"])
                level_runtime_action_space = _runtime_action_space_from_plain(
                    _required_mapping(meta, f"all_levels.{name}.runtime_action_space"),
                    f"all_levels.{name}.runtime_action_space",
                )
                level_vfs_variables = tuple(VariableDef(**var) for var in _required_field(meta, f"all_levels.{name}.vfs_variables"))
                level_transition_payload = _required_mapping(meta, f"all_levels.{name}.transition_schedule")
                level_schedule = build_vtc_transition_schedule(
                    runtime_action_space=level_runtime_action_space,
                    level=_SerializedLevel(
                        bars=level_bars,
                        affordances=level_affordances,
                        drive=level_drive,
                    ),
                    social_residue_rules=social_rules_from_transition_payload(
                        level_transition_payload,
                        field_name=f"all_levels.{name}.transition_schedule",
                    ),
                    vfs_variables=level_vfs_variables,
                )
                all_levels[name] = CompiledUniverse.LevelMetadata(
                    level_name=meta["level_name"],
                    bars=level_bars,
                    affordances=level_affordances,
                    drive=level_drive,
                    drive_hash=_required_field(meta, f"all_levels.{name}.drive_hash"),
                    curriculum_hash=_required_field(meta, f"all_levels.{name}.curriculum_hash"),
                    bars_hash=_required_field(meta, f"all_levels.{name}.bars_hash"),
                    affordances_hash=_required_field(meta, f"all_levels.{name}.affordances_hash"),
                    training_hash=_required_field(meta, f"all_levels.{name}.training_hash"),
                    curriculum=level_curriculum,
                    training=level_training,
                    token_spec=_token_spec_from_plain(_required_field(meta, f"all_levels.{name}.token_spec")),
                    token_type_schema_hash=_required_field(meta, f"all_levels.{name}.token_type_schema_hash"),
                    layout_hash=_required_field(meta, f"all_levels.{name}.layout_hash"),
                    action_metadata=_action_space_metadata_from_plain(meta["action_metadata"], f"all_levels.{name}.action_metadata"),
                    runtime_action_space=level_runtime_action_space,
                    action_schema_hash=_required_field(meta, f"all_levels.{name}.action_schema_hash"),
                    transition_graph_hash=_required_field(meta, f"all_levels.{name}.transition_graph_hash"),
                    transition_schedule=level_schedule,
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
                    observation_schema_hash=_required_field(meta, f"all_levels.{name}.observation_schema_hash"),
                    vfs_variables=level_vfs_variables,
                    variable_schema_hash=_required_field(meta, f"all_levels.{name}.variable_schema_hash"),
                    token_advisories=tuple(_required_field(meta, f"all_levels.{name}.token_advisories")),
                )

        top_runtime_action_space = _runtime_action_space_from_plain(_required_mapping(payload, "runtime_action_space"))
        top_vfs_variables = tuple(VariableDef(**var) for var in _required_field(payload, "vfs_variables"))
        top_bars = None
        top_affordances = None
        top_drive = None
        if all_levels is not None:
            # Look the primary level up BY NAME. The previous implementation scanned
            # for the first level matching (transition_graph_hash, vfs_hash,
            # action_schema_hash), which is sound only if that triple is unique —
            # and it is not: L0_5_dual_resource and L1_full_observability collide on
            # all three in the shipped pack, so popping L1 out silently rebuilt the
            # projection from L0_5's bars with no raise.
            declared_primary = _required_field(_required_mapping(payload, "metadata"), "primary_level")
            level_meta = all_levels.get(declared_primary)
            if level_meta is None:
                raise ValueError(
                    f"Compiled universe declares primary_level '{declared_primary}' but all_levels "
                    f"contains {sorted(all_levels)}; recompile the config pack."
                )
            top_bars = level_meta.bars
            top_affordances = level_meta.affordances
            top_drive = level_meta.drive
        if top_bars is None or top_affordances is None or top_drive is None:
            raise ValueError("Compiled universe cache cannot resolve primary transition level; recompile the config pack.")
        top_transition_payload = _required_mapping(payload, "transition_schedule")
        top_transition_schedule = build_vtc_transition_schedule(
            runtime_action_space=top_runtime_action_space,
            level=_SerializedLevel(bars=top_bars, affordances=top_affordances, drive=top_drive),
            social_residue_rules=social_rules_from_transition_payload(
                top_transition_payload,
                field_name="transition_schedule",
            ),
            vfs_variables=top_vfs_variables,
        )

        return CompiledUniverse(
            metadata=UniverseMetadata(**payload["metadata"]),
            token_spec=_token_spec_from_plain(_required_field(payload, "token_spec")),
            token_type_schema_hash=_required_field(payload, "token_type_schema_hash"),
            layout_hash=_required_field(payload, "layout_hash"),
            observation_schema_hash=_required_field(payload, "observation_schema_hash"),
            vfs_variables=top_vfs_variables,
            variable_schema_hash=_required_field(payload, "variable_schema_hash"),
            action_space_metadata=_action_space_metadata_from_plain(payload["action_space_metadata"]),
            runtime_action_space=top_runtime_action_space,
            action_schema_hash=_required_field(payload, "action_schema_hash"),
            transition_graph_hash=_required_field(payload, "transition_graph_hash"),
            transition_schedule=top_transition_schedule,
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
            vfs_expression_schema=_required_field(payload, "vfs_expression_schema"),
            vfs_history_spec=_required_field(payload, "vfs_history_spec"),
            vfs_evaluation_marks=(
                {k: set(v) for k, v in _required_field(payload, "vfs_evaluation_marks").items()}
                if _required_field(payload, "vfs_evaluation_marks") is not None
                else None
            ),  # Convert lists back to sets
            token_advisories=tuple(_required_field(payload, "token_advisories")),
            experiment_dir=None if _required_field(payload, "experiment_dir") is None else Path(payload["experiment_dir"]),
            drive_hash=_required_field(payload, "drive_hash"),
            curriculum_hash=_required_field(payload, "curriculum_hash"),
            bars_hash=_required_field(payload, "bars_hash"),
            affordances_hash=_required_field(payload, "affordances_hash"),
            training_hash=_required_field(payload, "training_hash"),
            brain_hash=_required_field(payload, "brain_hash"),
            pack_brain_hash=_required_field(payload, "pack_brain_hash"),
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


@dataclass(frozen=True)
class _SerializedLevel:
    bars: BarsV2Config
    affordances: AffordancesV2Config
    drive: DriveAsCodeConfig


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


def _serialize_token_spec(spec: TokenSpec) -> dict[str, Any]:
    """Serialize a TokenSpec to a msgpack-safe dict.

    `payload_features` are serialized even though they are engine constants: the artifact
    is self-describing (token-obs spec §2), and `TokenTypeSchema.__post_init__` compares
    them against the running engine's schema on load — a cache whose payload schema
    disagrees with the engine refuses loudly instead of deserializing a lie.
    """
    return {
        "encoding_version": spec.encoding_version,
        "types": [
            {
                "type_name": t.type_name,
                "payload_features": list(t.payload_features),
                "capacity": t.capacity,
                "slot_bindings": [
                    {
                        "slot_index": binding.slot_index,
                        "filler_kind": binding.filler_kind,
                        "filler_ref": binding.filler_ref,
                        "static_signature": None if binding.static_signature is None else list(binding.static_signature),
                    }
                    for binding in t.slot_bindings
                ],
            }
            for t in spec.types
        ],
    }


def _token_spec_from_plain(payload: Mapping[str, Any] | None) -> TokenSpec:
    if payload is None:
        raise ValueError(
            "Compiled universe cache carries a null `token_spec`. The TokenSpec IS the artifact's "
            "observation product since COMPILED_SCHEMA_VERSION 1.22; recompile the config pack."
        )
    types = tuple(
        TokenTypeSchema(
            type_name=entry["type_name"],
            payload_features=tuple(entry["payload_features"]),
            capacity=entry["capacity"],
            slot_bindings=tuple(
                SlotBinding(
                    slot_index=binding["slot_index"],
                    filler_kind=binding["filler_kind"],
                    filler_ref=binding["filler_ref"],
                    static_signature=None if binding["static_signature"] is None else tuple(binding["static_signature"]),
                )
                for binding in entry["slot_bindings"]
            ),
        )
        for entry in payload["types"]
    )
    return TokenSpec(types=types, encoding_version=payload["encoding_version"])


def _serialize_compiled_variable(var: Any) -> dict[str, Any]:
    """Serialize one CompiledVariable to a msgpack-safe dict (AST reconstructed on load)."""
    return {
        "name": var.name,
        "type": var.type,
        "expression": var.expression,
        "initial_value": var.initial_value,
        "result_type": var.result_type,
        "exposed_to": list(var.exposed_to),
        "shape": var.shape,
        "initial_value_mode": var.initial_value_mode,
        "initial_value_params": var.initial_value_params,
        "dims": var.dims,
        "semantic_type": var.semantic_type,
        "normalization": None if var.normalization is None else var.normalization.model_dump(mode="json", exclude_none=True),
    }


def _serialize_profile(profile: Any) -> dict[str, Any] | None:
    """Serialize a CompiledGlobalProfile (used for both global and agent profiles)."""
    if profile is None:
        return None
    return {
        "variables": [_serialize_compiled_variable(var) for var in profile.variables],
        "dependencies": {name: list(deps) for name, deps in profile.dependencies.items()},
    }


def _serialize_vfs_profiles(profiles: CompiledVFSProfiles) -> dict[str, Any]:
    """Serialize CompiledVFSProfiles to dict."""

    result: dict[str, Any] = {
        "evaluation_mode": profiles.evaluation_mode,
        "debug_logging": profiles.debug_logging,
        "global_profile": _serialize_profile(profiles.global_profile),
        "agent_profile": _serialize_profile(profiles.agent_profile),
    }

    if profiles.item_profiles:
        item_profiles_serialized: dict[str, Any] = {}
        for name, profile in profiles.item_profiles.items():
            item_profiles_serialized[name] = {
                "profile_name": profile.profile_name,
                "variables": [_serialize_compiled_variable(var) for var in profile.variables],
            }
        result["item_profiles"] = item_profiles_serialized
    else:
        result["item_profiles"] = None

    return result


def _deserialize_compiled_variable(var: dict[str, Any]) -> Any:
    """Rebuild one CompiledVariable, reconstructing its expression AST."""
    from townlet.vfs.profiles import CompiledVariable
    from townlet.vfs.schema import NormalizationSpec
    from townlet.world.expression import ExpressionParser

    raw_normalization = var.get("normalization")
    return CompiledVariable(
        name=var["name"],
        type=var["type"],
        expression=var.get("expression"),
        ast=ExpressionParser().parse(var["expression"]) if var.get("expression") else None,
        initial_value=var.get("initial_value"),
        result_type=var.get("result_type"),
        # No fail-open default: an absent exposed_to in a cached artifact means UNEXPOSED
        # (explicit exposure at the unit-3 cut, hamlet-d97b4d6b4a).
        exposed_to=tuple(var.get("exposed_to") or ()),
        shape=var.get("shape"),
        initial_value_mode=var.get("initial_value_mode"),
        initial_value_params=var.get("initial_value_params"),
        dims=var.get("dims"),
        semantic_type=var.get("semantic_type"),
        normalization=None if raw_normalization is None else NormalizationSpec(**raw_normalization),
    )


def _deserialize_profile(payload: dict[str, Any] | None) -> Any | None:
    """Rebuild a CompiledGlobalProfile (used for both global and agent profiles)."""
    from townlet.vfs.profiles import CompiledGlobalProfile

    if payload is None:
        return None
    variables = [_deserialize_compiled_variable(var) for var in payload["variables"]]
    dependencies = {name: tuple(deps) for name, deps in payload.get("dependencies", {}).items()}
    return CompiledGlobalProfile(variables=variables, dependencies=dependencies)


def _deserialize_vfs_profiles(payload: dict[str, Any]) -> CompiledVFSProfiles:
    """Deserialize CompiledVFSProfiles from dict."""
    from townlet.vfs.profiles import CompiledItemProfile

    item_profiles = None
    raw_items = payload.get("item_profiles")
    if raw_items:
        item_profiles = {}
        for name, profile in raw_items.items():
            variables = [_deserialize_compiled_variable(var) for var in profile.get("variables", [])]
            item_profiles[name] = CompiledItemProfile(profile_name=profile["profile_name"], variables=variables)

    return CompiledVFSProfiles(
        evaluation_mode=payload["evaluation_mode"],
        debug_logging=payload["debug_logging"],
        global_profile=_deserialize_profile(payload.get("global_profile")),
        agent_profile=_deserialize_profile(payload.get("agent_profile")),
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
