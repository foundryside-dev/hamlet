"""Compile-time validation for trigger_cascade cascade_id references."""

from __future__ import annotations

import pytest
import torch

from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.schema import CommandNode, CommandType
from townlet.universe.compilers.optimization import OptimizationCompiler
from townlet.universe.optimization import OptimizationData


def _make_catalog(cascade_id: str) -> EffectCatalog:
    cmd = CommandNode(type=CommandType.TRIGGER_CASCADE, cascade_id=cascade_id)
    effect = CompiledEffect(
        id="effect_with_cascade",
        scope="agent",
        duration=1,
        intensity=1.0,
        reapply_policy="stack",
        observable=True,
        on_spawn=[cmd],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )
    return EffectCatalog(effects={effect.id: effect})


def _make_optimization(cascades: dict[str, list[dict]]) -> OptimizationData:
    return OptimizationData(
        base_depletions=torch.zeros(1),
        cascade_data=cascades,
        modulation_data=[],
        action_mask_table=torch.zeros((1, 0), dtype=torch.bool),
        affordance_position_map={},
    )


def test_trigger_cascade_validates_known_id():
    catalog = _make_catalog("primary_to_pivotal")
    opt = _make_optimization({"primary_to_pivotal": []})
    compiler = OptimizationCompiler()
    compiler.validate_trigger_cascade_ids(catalog, opt, level_name="L1")


def test_trigger_cascade_rejects_unknown_id():
    catalog = _make_catalog("missing")
    opt = _make_optimization({"primary_to_pivotal": []})
    compiler = OptimizationCompiler()
    with pytest.raises(ValueError, match="unknown cascade_id"):
        compiler.validate_trigger_cascade_ids(catalog, opt, level_name="L1")


def test_trigger_cascade_rejects_when_no_cascades_defined():
    catalog = _make_catalog("anything")
    opt = _make_optimization({})
    compiler = OptimizationCompiler()
    with pytest.raises(ValueError, match="no cascades are defined"):
        compiler.validate_trigger_cascade_ids(catalog, opt, level_name="L1")
