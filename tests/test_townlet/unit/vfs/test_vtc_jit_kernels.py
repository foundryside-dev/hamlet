"""Tests for scripted VTC transition kernels."""

from __future__ import annotations

import torch

from townlet.config.affordances_v2_config import ModulationParamConfig
from townlet.vfs import vtc, vtc_kernels


def test_vtc_hot_transition_kernels_are_torchscript() -> None:
    """Hot generated transition kernels should be TorchScript functions."""
    assert hasattr(vtc_kernels.apply_passive_depletion, "graph")
    assert hasattr(vtc_kernels.apply_threshold_cascade, "graph")
    assert hasattr(vtc_kernels.apply_modulation_multiplier, "graph")
    assert hasattr(vtc_kernels.apply_terminal_condition, "graph")


def test_vtc_generated_hot_paths_do_not_call_expression_interpreter(monkeypatch) -> None:
    """Generated fixed-shape rules should execute through scripted tensor kernels."""

    def _raise_if_interpreted(*args: object, **kwargs: object) -> torch.Tensor:
        raise AssertionError("generated VTC hot path called the expression interpreter")

    monkeypatch.setattr(vtc.Evaluator, "evaluate", _raise_if_interpreted)
    device = torch.device("cpu")
    active_mask = torch.tensor([True, True, False], device=device)

    passive_program = vtc.compile_vtc_passive_depletions(
        [{"name": "energy", "depletion": {"passive": 0.1}, "bounds": {"min": 0.0, "max": 1.0}}]
    )
    passive = passive_program.apply(
        bars_state={"energy": torch.tensor([0.5, 0.05, 0.9], device=device)},
        active_mask=active_mask,
        device=device,
        depletion_multiplier=2.0,
    )
    assert torch.allclose(passive["energy"], torch.tensor([0.3, 0.0, 0.9], device=device))

    cascade_program = vtc.compile_vtc_threshold_cascades(
        [{"source": "satiation", "target": "energy", "threshold": 0.3, "strength": 0.006}],
        [{"name": "energy", "depletion": {"passive": 0.0}, "bounds": {"min": 0.0, "max": 1.0}}],
    )
    cascade = cascade_program.apply(
        bars_state={
            "energy": torch.tensor([1.0, 1.0, 1.0], device=device),
            "satiation": torch.tensor([0.15, 0.5, 0.15], device=device),
        },
        active_mask=active_mask,
        device=device,
    )
    assert torch.allclose(cascade["energy"], torch.tensor([0.997, 1.0, 1.0], device=device), atol=1e-7)

    modulation_program = vtc.compile_vtc_modulations(
        [
            ModulationParamConfig(
                bar="energy",
                affordances=["WORK"],
                type="linear_multiplier",
                threshold=0.3,
                min_multiplier=0.5,
            )
        ]
    )
    multiplier = modulation_program.compute_affordance_multiplier(
        "WORK",
        {"energy": torch.tensor([0.15, 0.6, 0.15], device=device)},
        active_mask=active_mask,
        device=device,
    )
    assert torch.allclose(multiplier, torch.tensor([0.75, 1.0, 0.0], device=device))

    terminal_program = vtc.compile_vtc_terminal_conditions(
        [{"name": "energy", "bounds": {"min": 0.0, "max": 1.0, "lethal_min": True, "lethal_max": False}}]
    )
    dones = terminal_program.apply(
        bars_state={"energy": torch.tensor([0.0, 0.5, 0.0], device=device)},
        dones=torch.tensor([False, True, False], device=device),
        active_mask=active_mask,
        device=device,
    )
    assert torch.equal(dones, torch.tensor([True, True, False], device=device))


def test_generated_vtc_programs_do_not_keep_interpreter_fallback_helpers() -> None:
    """Generated transition programs should not retain unused interpreter fallback paths."""
    forbidden_helpers = {
        vtc.VTCThresholdCascadeProgram: {
            "_apply_composed_rule",
            "_broadcast_agent_mask",
            "_build_rule_mask",
            "_coerce_condition_mask",
            "_evaluate_tensor",
        },
        vtc.VTCPassiveDepletionProgram: {
            "_apply_composed_rule",
            "_build_rule_mask",
            "_coerce_rule_tensor",
            "_evaluate_tensor",
        },
        vtc.VTCModulationProgram: {
            "_apply_composed_rule",
            "_build_rule_mask",
            "_coerce_rule_tensor",
            "_evaluate_tensor",
        },
        vtc.VTCTerminalConditionProgram: {"_evaluate_bool_tensor"},
    }

    for program_cls, helper_names in forbidden_helpers.items():
        leaked_helpers = sorted(helper_name for helper_name in helper_names if helper_name in program_cls.__dict__)
        assert leaked_helpers == [], f"{program_cls.__name__} still exposes interpreter fallback helpers: {leaked_helpers}"


def test_scripted_vtc_kernels_match_hardcoded_tensor_baselines() -> None:
    """Scripted kernels should preserve the direct hardcoded tensor equations."""
    device = torch.device("cpu")
    active_mask = torch.tensor([True, True, False, True], device=device)
    energy = torch.tensor([0.5, 0.05, 0.9, 1.0], device=device)

    hardcoded_passive = torch.where(active_mask, torch.clamp(energy - (0.1 * 2.0), min=0.0, max=1.0), energy)
    scripted_passive = vtc_kernels.apply_passive_depletion(
        energy,
        active_mask,
        passive_rate=0.1,
        depletion_multiplier=2.0,
        clamp_low=0.0,
        clamp_high=1.0,
    )
    assert torch.allclose(scripted_passive, hardcoded_passive)

    satiation = torch.tensor([0.15, 0.5, 0.15, 0.0], device=device)
    hardcoded_delta = -0.006 * ((0.3 - satiation) / 0.3)
    hardcoded_candidate = torch.clamp(energy + hardcoded_delta, min=0.0, max=1.0)
    hardcoded_cascade = torch.where(active_mask & (satiation < 0.3), hardcoded_candidate, energy)
    scripted_cascade = vtc_kernels.apply_threshold_cascade(
        satiation,
        energy,
        active_mask,
        threshold=0.3,
        strength=0.006,
        strength_multiplier=1.0,
        clamp_low=0.0,
        clamp_high=1.0,
    )
    assert torch.allclose(scripted_cascade, hardcoded_cascade)
