"""Metadata-domain compiler boundary."""

from __future__ import annotations

import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pydantic
import torch

from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.environment_config import EnvironmentConfig as EnvConfigV21
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.dto import AffordanceInfo, AffordanceMetadata, MeterInfo, MeterMetadata, UniverseMetadata
from townlet.universe.raw_configs_v21 import RawConfigsV21


class MetadataCompiler:
    """Compile public metadata DTOs for the compiled universe."""

    def __init__(
        self,
        *,
        schema_version: str,
        compiler_version: str,
        compute_config_mtime: Callable[[Path], float],
        build_cache_fingerprint: Callable[[Path], tuple[str, str]],
        get_git_sha: Callable[[], str],
    ) -> None:
        self._schema_version = schema_version
        self._compiler_version = compiler_version
        self._compute_config_mtime = compute_config_mtime
        self._build_cache_fingerprint = build_cache_fingerprint
        self._get_git_sha = get_git_sha

    def build_meter_metadata(self, environment: EnvConfigV21, bars: BarsV2Config) -> MeterMetadata:
        """Meters: use environment vocabulary, initial from bars."""
        meter_lookup = {meter.name: meter for meter in bars.meters}
        meter_infos: list[MeterInfo] = []
        for idx, meter in enumerate(environment.environment.meters):
            bar_cfg = meter_lookup.get(meter.name)
            initial = bar_cfg.initial if bar_cfg else 0.0
            meter_infos.append(
                MeterInfo(
                    name=meter.name,
                    index=idx,
                    critical=False,
                    initial_value=initial,
                    observable=True,
                    description=meter.description,
                )
            )
        return MeterMetadata(meters=tuple(meter_infos))

    def build_affordance_metadata(self, affordances: AffordancesV2Config) -> AffordanceMetadata:
        """Affordance metadata derived from per-level affordances.yaml."""
        infos: list[AffordanceInfo] = []
        for aff in affordances.affordances:
            effects_dict = {}
            if aff.interactions and "on_start" in aff.interactions:
                for cmd in aff.interactions["on_start"]:
                    modify = getattr(cmd, "modify", None)
                    if isinstance(modify, str) and modify.startswith("target.bar."):
                        meter_name = modify.split(".")[-1]
                        value_field = getattr(cmd, "value", None)
                        if isinstance(value_field, str) and "+" in value_field:
                            try:
                                value_part = value_field.split("+")[-1].strip()
                                effects_dict[meter_name] = float(value_part)
                            except (ValueError, IndexError):
                                pass

            infos.append(
                AffordanceInfo(
                    id=aff.name,
                    name=aff.name,
                    enabled=True,
                    effects=effects_dict,
                    cost=float(aff.costs.get("money", 0.0)) if hasattr(aff, "costs") else 0.0,
                    category=None,
                    description="",
                    position=None,
                )
            )
        return AffordanceMetadata(affordances=tuple(infos))

    def build_universe_metadata(
        self,
        raw: RawConfigsV21,
        primary_meta: CompiledUniverse.LevelMetadata,
        *,
        experiment_dir: Path,
        config_hash: str | None,
        config_mtime: float | None,
    ) -> UniverseMetadata:
        """Construct UniverseMetadata summary."""
        meter_names = tuple(m.name for m in primary_meta.meter_metadata.meters)
        meter_name_to_index = {m.name: m.index for m in primary_meta.meter_metadata.meters}
        affordance_ids = tuple(a.id for a in primary_meta.affordance_metadata.affordances)
        affordance_id_to_index = {a.id: idx for idx, a in enumerate(primary_meta.affordance_metadata.affordances)}

        grid_size = None
        grid_cells = None
        position_dim = 0
        substrate_cfg = raw.stratum.stratum.substrate
        substrate_type = substrate_cfg.type
        if substrate_type in {"grid", "grid3d"} and substrate_cfg.grid is not None:
            width = substrate_cfg.grid.width
            height = substrate_cfg.grid.height
            grid_size = width
            depth = getattr(substrate_cfg.grid, "depth", None)
            if depth is not None:
                grid_cells = width * height * depth
                position_dim = 3
            else:
                grid_cells = width * height
                position_dim = 2
        elif substrate_type == "gridnd" and substrate_cfg.gridnd is not None:
            grid_cells = 1
            for size in substrate_cfg.gridnd.dimension_sizes:
                grid_cells *= size
            position_dim = len(substrate_cfg.gridnd.dimension_sizes)

        curriculum_day_length = primary_meta.curriculum.curriculum.day_length
        temporal_supported = raw.stratum.stratum.temporal_support == "enabled"
        temporal_active = primary_meta.curriculum.curriculum.active_temporal
        if temporal_supported and temporal_active:
            if curriculum_day_length is None or curriculum_day_length <= 0:
                raise ValueError(
                    "Missing curriculum.day_length for temporal-enabled stratum.\n"
                    f"  Experiment: {experiment_dir}\n"
                    f"  Level: {primary_meta.level_name}\n"
                    "Provide an explicit positive day_length; no defaults are applied."
                )
            ticks_per_day = curriculum_day_length
        else:
            ticks_per_day = 0

        if config_hash is None:
            config_hash, provenance_id = self._build_cache_fingerprint(experiment_dir)
        else:
            _, provenance_id = self._build_cache_fingerprint(experiment_dir)
        if config_mtime is None:
            config_mtime = self._compute_config_mtime(experiment_dir)

        try:
            config_version = raw.experiment.experiment.version
        except AttributeError as exc:
            raise ValueError(
                "experiment.version is required in experiment.yaml (no defaults allowed). Provide an explicit semantic version string."
            ) from exc
        if not config_version:
            raise ValueError("experiment.version is required in experiment.yaml and cannot be empty.")

        return UniverseMetadata(
            universe_name=raw.experiment.experiment.metadata.name,
            schema_version=self._schema_version,
            substrate_type=substrate_type,
            position_dim=position_dim,
            meter_count=len(meter_names),
            meter_names=meter_names,
            meter_name_to_index=meter_name_to_index,
            affordance_count=len(affordance_ids),
            affordance_ids=affordance_ids,
            affordance_id_to_index=affordance_id_to_index,
            action_count=primary_meta.action_metadata.total_actions,
            observation_dim=primary_meta.observation_spec.total_dims,
            grid_size=grid_size,
            grid_cells=grid_cells,
            max_sustainable_income=0.0,
            total_affordance_costs=0.0,
            economic_balance=0.0,
            ticks_per_day=ticks_per_day,
            config_version=config_version,
            compiler_version=self._compiler_version,
            compiled_at=datetime.now(UTC).isoformat(),
            config_hash=config_hash,
            config_mtime=config_mtime,
            provenance_id=provenance_id,
            compiler_git_sha=self._get_git_sha(),
            python_version=sys.version.split()[0],
            torch_version=torch.__version__,
            pydantic_version=pydantic.__version__,
        )
