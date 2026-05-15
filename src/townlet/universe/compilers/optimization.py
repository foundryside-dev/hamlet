"""Optimization-domain compiler boundary."""

from __future__ import annotations

from typing import Any

import torch

from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.bars_v2_config import BarsV2Config
from townlet.effects.catalog import EffectCatalog
from townlet.effects.schema import CommandType
from townlet.universe.dto import ActionSpaceMetadata, AffordanceMetadata, MeterMetadata
from townlet.universe.optimization import OptimizationData


class OptimizationCompiler:
    """Compile tensors and validation data used by optimized runtime paths."""

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
        base_depletions = torch.zeros(len(meter_metadata.meters), dtype=torch.float32)
        for bar in bars.meters:
            idx = meter_lookup.get(bar.name)
            if idx is not None:
                base_depletions[idx] = float(bar.depletion.passive)

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
            base_depletions=base_depletions,
            cascade_data={"primary_to_pivotal": cascade_entries, **cascade_by_id},
            modulation_data=modulation_entries,
            action_mask_table=action_mask_table,
            affordance_position_map={aff.name: None for aff in affordance_metadata.affordances},
        )

    def validate_trigger_cascade_ids(
        self,
        compiled_effect_catalog: EffectCatalog,
        optimization_data: OptimizationData,
        *,
        level_name: str,
    ) -> None:
        """Ensure trigger_cascade commands reference cascades compiled for this level."""
        valid_ids = set(optimization_data.cascade_data.keys())
        if not valid_ids:
            for effect in compiled_effect_catalog.effects.values():
                for cmd in self._walk_commands(effect):
                    if cmd.type == CommandType.TRIGGER_CASCADE:
                        raise ValueError(
                            "trigger_cascade referenced but no cascades are defined in bars.yaml.\n"
                            f"  Level: {level_name}\n"
                            f"  Effect: {effect.id}\n"
                            "  Define cascades in bars.cascades before using trigger_cascade."
                        )
            return

        for effect in compiled_effect_catalog.effects.values():
            for cmd in self._walk_commands(effect):
                if cmd.type == CommandType.TRIGGER_CASCADE:
                    cascade_id = cmd.cascade_id
                    if not cascade_id or cascade_id not in valid_ids:
                        raise ValueError(
                            "trigger_cascade references unknown cascade_id.\n"
                            f"  Level: {level_name}\n"
                            f"  Effect: {effect.id}\n"
                            f"  cascade_id: {cascade_id!r}\n"
                            f"  Valid cascade ids: {sorted(valid_ids)}"
                        )

    @staticmethod
    def _walk_commands(effect: Any):
        """Yield all CommandNodes from a compiled effect recursively."""

        def walk(cmd):
            yield cmd
            if cmd.type == CommandType.IF:
                for child in cmd.then_commands or []:
                    yield from walk(child)
                for child in cmd.else_commands or []:
                    yield from walk(child)
            elif cmd.type == CommandType.FOR_EACH:
                for child in cmd.body or cmd.do_commands or []:
                    yield from walk(child)
            elif cmd.type == CommandType.SWITCH:
                for _, body in cmd.cases or []:
                    for child in body:
                        yield from walk(child)
                for child in cmd.default_commands or []:
                    yield from walk(child)
            elif cmd.type == CommandType.REDUCE:
                pass
            elif cmd.type == CommandType.PARALLEL:
                for child in cmd.parallel_commands or []:
                    yield from walk(child)
            elif cmd.type == CommandType.DELAY:
                for child in cmd.delay_commands or []:
                    yield from walk(child)

        pipelines = list(effect.on_spawn) + list(effect.on_tick) + list(effect.on_despawn) + list(getattr(effect, "on_interrupt", []) or [])
        for command in pipelines:
            yield from walk(command)
