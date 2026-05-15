"""Optimization-domain compiler boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.bars_v2_config import BarsV2Config
from townlet.universe.dto import ActionSpaceMetadata, AffordanceMetadata, MeterMetadata
from townlet.universe.optimization import OptimizationData


class OptimizationCompiler:
    """Compile tensors and validation data used by optimized runtime paths."""

    def resolve_day_length(self, curriculum: Any, *, temporal_supported: bool, experiment_dir: Path, level_name: str) -> int:
        """Return the optimization day length for a level, failing if required temporal data is missing."""
        day_length = curriculum.curriculum.day_length
        if temporal_supported and curriculum.curriculum.active_temporal:
            if day_length is None or day_length <= 0:
                raise ValueError(
                    "curriculum.day_length is required when temporal mechanics are declared in stratum.temporal_support.\n"
                    f"  Experiment: {experiment_dir}\n"
                    f"  Level: {level_name}\n"
                    "Provide an explicit positive day_length; no defaults are applied."
                )
            return int(day_length)
        return 0

    def build_optimization_data(
        self,
        bars: BarsV2Config,
        affordances: AffordancesV2Config,
        meter_metadata: MeterMetadata,
        affordance_metadata: AffordanceMetadata,
        action_metadata: ActionSpaceMetadata,
        *,
        day_length: int,
    ) -> OptimizationData:
        """Precompute tensors from v2.1 DTOs."""
        _ = action_metadata
        meter_lookup = {m.name: m.index for m in meter_metadata.meters}

        cascade_entries: list[dict[str, Any]] = []
        cascade_by_id: dict[str, list[dict[str, Any]]] = {}
        for cascade in bars.cascades:
            source_idx = meter_lookup.get(cascade.source)
            target_idx = meter_lookup.get(cascade.target)
            if source_idx is None or target_idx is None:
                missing_source = cascade.source not in meter_lookup
                missing_target = cascade.target not in meter_lookup
                parts = ["Invalid cascade entry in bars.yaml."]
                if missing_source:
                    parts.append(f"  Unknown source meter: {cascade.source!r}")
                if missing_target:
                    parts.append(f"  Unknown target meter: {cascade.target!r}")
                parts.append("  Valid meters: " + ", ".join(sorted(meter_lookup.keys())))
                raise ValueError("\n".join(parts))
            entry = {
                "source_idx": source_idx,
                "target_idx": target_idx,
                "threshold": float(cascade.threshold),
                "strength": float(cascade.strength),
            }
            cascade_entries.append(entry)
            pair_id = f"{cascade.source}->{cascade.target}"
            cascade_by_id[pair_id] = cascade_by_id.get(pair_id, []) + [entry]

        modulation_entries: list[dict[str, Any]] = []
        for modulation in affordances.modulations:
            bar_idx = meter_lookup.get(modulation.bar)
            if bar_idx is None:
                raise ValueError(
                    "Invalid modulation entry in affordances.yaml.\n"
                    f"  Unknown bar: {modulation.bar!r}\n"
                    "  Valid meters: " + ", ".join(sorted(meter_lookup.keys()))
                )
            for aff_name in modulation.affordances:
                target_idx = next((i for i, a in enumerate(affordance_metadata.affordances) if a.name == aff_name), None)
                if target_idx is None:
                    valid_affordances = [a.name for a in affordance_metadata.affordances]
                    raise ValueError(
                        "Invalid modulation entry in affordances.yaml.\n"
                        f"  Unknown affordance in modulation.affordances: {aff_name!r}\n"
                        "  Valid affordances: " + ", ".join(sorted(valid_affordances))
                    )
                modulation_entries.append(
                    {
                        "bar_idx": bar_idx,
                        "affordance_idx": target_idx,
                        "threshold": float(modulation.threshold),
                        "min_multiplier": float(modulation.min_multiplier),
                    }
                )

        num_hours = max(day_length, 1)
        num_affordances = len(affordance_metadata.affordances)
        action_mask_table = torch.ones((num_hours, num_affordances), dtype=torch.bool)
        affordance_index: dict[str, int] = {info.name: idx for idx, info in enumerate(affordance_metadata.affordances)}

        for aff_cfg in affordances.affordances:
            aff_idx = affordance_index.get(aff_cfg.name)
            if aff_idx is None:
                continue

            hours_enabled = torch.ones(num_hours, dtype=torch.bool)
            opening = aff_cfg.opening_hours
            if opening.enabled and opening.schedule:
                hours_enabled[:] = False
                for window in opening.schedule:
                    start = int(window.start)
                    end = int(window.end)
                    for hour in range(start, end):
                        hours_enabled[hour % num_hours] = True

            action_mask_table[:, aff_idx] &= hours_enabled

        return OptimizationData(
            cascade_data={"primary_to_pivotal": cascade_entries, **cascade_by_id},
            modulation_data=modulation_entries,
            action_mask_table=action_mask_table,
            affordance_position_map={aff.name: None for aff in affordance_metadata.affordances},
        )
