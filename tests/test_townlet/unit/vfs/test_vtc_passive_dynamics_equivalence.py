"""Behavioural equivalence coverage for passive dynamics migrated into VTC."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.config.affordances_v2_config import AffordancesV2Config, load_affordances_v2_config
from townlet.config.bars_v2_config import BarsV2Config, load_bars_v2_config
from townlet.vfs.vtc import compile_vtc_modulations, compile_vtc_passive_depletions, compile_vtc_threshold_cascades

LEVEL_NAMES = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)
LEVELS_ROOT = Path("configs/default_curriculum/levels")
SAMPLE_BAR_VALUES = torch.tensor([0.0, 0.05, 0.15, 0.25, 0.35, 0.55, 1.0], dtype=torch.float32)


def _level_dir(level_name: str) -> Path:
    return LEVELS_ROOT / level_name


def _sample_bar_state(bars: BarsV2Config) -> dict[str, torch.Tensor]:
    return {meter.name: torch.roll(SAMPLE_BAR_VALUES, shifts=index).clone() for index, meter in enumerate(bars.meters)}


def _legacy_decay_and_cascades(
    bars: BarsV2Config,
    bars_state: dict[str, torch.Tensor],
    *,
    depletion_multiplier: float,
) -> dict[str, torch.Tensor]:
    updated = {name: value.clone() for name, value in bars_state.items()}

    for meter in bars.meters:
        updated[meter.name] = torch.clamp(
            updated[meter.name] - (float(meter.depletion.passive) * depletion_multiplier),
            min=0.0,
            max=1.0,
        )

    phase_snapshot = {name: value.clone() for name, value in updated.items()}
    for cascade in bars.cascades:
        source = phase_snapshot[cascade.source]
        if cascade.threshold == 0.0:
            delta = torch.zeros_like(source)
        else:
            threshold = float(cascade.threshold)
            strength = float(cascade.strength)
            delta = torch.where(
                source < threshold,
                -strength * ((threshold - source) / threshold),
                torch.zeros_like(source),
            )
        updated[cascade.target] = torch.clamp(updated[cascade.target] + delta, min=0.0, max=1.0)

    return updated


def _legacy_affordance_multiplier(
    affordances: AffordancesV2Config,
    affordance_name: str,
    bars_state: dict[str, torch.Tensor],
    active_mask: torch.Tensor,
) -> torch.Tensor:
    multiplier = torch.ones(active_mask.shape, dtype=torch.float32)

    for modulation in affordances.modulations:
        if affordance_name not in modulation.affordances:
            continue

        source = bars_state[modulation.bar]
        if modulation.threshold == 0.0:
            factor = torch.ones_like(source)
        else:
            threshold = float(modulation.threshold)
            min_multiplier = float(modulation.min_multiplier)
            factor = torch.where(
                source < threshold,
                min_multiplier + ((1.0 - min_multiplier) * (source / threshold)),
                torch.ones_like(source),
            )
        multiplier = torch.clamp(multiplier * factor, min=0.0, max=1.0)

    return torch.where(active_mask, multiplier, torch.zeros_like(multiplier))


@pytest.mark.parametrize("level_name", LEVEL_NAMES)
@pytest.mark.parametrize("depletion_multiplier", (1.0, 1.75))
def test_vtc_decay_and_cascades_match_legacy_formulas(level_name: str, depletion_multiplier: float) -> None:
    """VTC passive depletion plus cascades should match the old per-level formulas."""
    bars = load_bars_v2_config(_level_dir(level_name))
    initial = _sample_bar_state(bars)
    active_mask = torch.ones(SAMPLE_BAR_VALUES.shape, dtype=torch.bool)

    depleted = compile_vtc_passive_depletions(bars.meters).apply(
        bars_state=initial,
        active_mask=active_mask,
        device=torch.device("cpu"),
        depletion_multiplier=depletion_multiplier,
    )
    actual = compile_vtc_threshold_cascades(bars.cascades, bars.meters).apply(
        bars_state=depleted,
        active_mask=active_mask,
        device=torch.device("cpu"),
    )
    expected = _legacy_decay_and_cascades(bars, initial, depletion_multiplier=depletion_multiplier)

    for meter in bars.meters:
        assert torch.allclose(actual[meter.name], expected[meter.name], atol=1e-6), f"{level_name} {meter.name}"


@pytest.mark.parametrize("level_name", LEVEL_NAMES)
def test_vtc_modulations_match_legacy_linear_multiplier_formula(level_name: str) -> None:
    """VTC affordance modulations should match the legacy linear multiplier formula."""
    bars = load_bars_v2_config(_level_dir(level_name))
    affordances = load_affordances_v2_config(_level_dir(level_name))
    bars_state = _sample_bar_state(bars)
    active_mask = torch.tensor([True, True, False, True, False, True, True])
    program = compile_vtc_modulations(affordances.modulations)

    for affordance in affordances.affordances:
        actual = program.compute_affordance_multiplier(
            affordance.name,
            bars_state,
            active_mask=active_mask,
            device=torch.device("cpu"),
        )
        expected = _legacy_affordance_multiplier(affordances, affordance.name, bars_state, active_mask)

        assert torch.allclose(actual, expected, atol=1e-6), f"{level_name} {affordance.name}"
