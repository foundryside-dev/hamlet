"""Optimization-domain compiler boundary."""

from __future__ import annotations

from typing import Protocol

from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.bars_v2_config import BarsV2Config
from townlet.effects.catalog import EffectCatalog
from townlet.universe.dto import ActionSpaceMetadata, AffordanceMetadata, MeterMetadata
from townlet.universe.optimization import OptimizationData


class _OptimizationDelegate(Protocol):
    def _build_optimization_data(
        self,
        bars: BarsV2Config,
        affordances: AffordancesV2Config,
        meter_metadata: MeterMetadata,
        affordance_metadata: AffordanceMetadata,
        action_metadata: ActionSpaceMetadata,
        *,
        day_length: int,
    ) -> OptimizationData: ...

    def _validate_trigger_cascade_ids(
        self,
        compiled_effect_catalog: EffectCatalog,
        optimization_data: OptimizationData,
        *,
        level_name: str,
    ) -> None: ...


class OptimizationCompiler:
    """Compile tensors and validation data used by optimized runtime paths."""

    def __init__(self, delegate: _OptimizationDelegate) -> None:
        self._delegate = delegate

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
        return self._delegate._build_optimization_data(
            bars,
            affordances,
            meter_metadata,
            affordance_metadata,
            action_metadata,
            day_length=day_length,
        )

    def validate_trigger_cascade_ids(
        self,
        compiled_effect_catalog: EffectCatalog,
        optimization_data: OptimizationData,
        *,
        level_name: str,
    ) -> None:
        self._delegate._validate_trigger_cascade_ids(compiled_effect_catalog, optimization_data, level_name=level_name)
