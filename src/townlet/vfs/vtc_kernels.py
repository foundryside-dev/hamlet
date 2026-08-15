"""TorchScript kernels for generated VTC transition rules."""

from __future__ import annotations

import torch


@torch.jit.script
def apply_masked_candidate(phase_value: torch.Tensor, candidate: torch.Tensor, write_mask: torch.Tensor) -> torch.Tensor:
    """Apply an already-computed candidate under a boolean write mask."""
    return torch.where(write_mask, candidate, phase_value)


@torch.jit.script
def apply_passive_depletion(
    phase_value: torch.Tensor,
    active_mask: torch.Tensor,
    passive_rate: float,
    depletion_multiplier: float,
    clamp_low: float,
    clamp_high: float,
) -> torch.Tensor:
    """Apply one generated passive-depletion rule."""
    candidate = torch.clamp(phase_value - (passive_rate * depletion_multiplier), min=clamp_low, max=clamp_high)
    return torch.where(active_mask, candidate, phase_value)


@torch.jit.script
def apply_threshold_cascade(
    source_value: torch.Tensor,
    target_value: torch.Tensor,
    active_mask: torch.Tensor,
    threshold: float,
    strength: float,
    strength_multiplier: float,
    clamp_low: float,
    clamp_high: float,
) -> torch.Tensor:
    """Apply one generated threshold cascade rule."""
    delta = torch.zeros_like(target_value)
    if threshold != 0.0:
        delta = (-strength * strength_multiplier) * ((threshold - source_value) / threshold)
    candidate = torch.clamp(target_value + delta, min=clamp_low, max=clamp_high)
    write_mask = active_mask & (source_value < threshold)
    return torch.where(write_mask, candidate, target_value)


@torch.jit.script
def apply_modulation_multiplier(
    phase_multiplier: torch.Tensor,
    source_value: torch.Tensor,
    active_mask: torch.Tensor,
    threshold: float,
    min_multiplier: float,
    clamp_low: float,
    clamp_high: float,
) -> torch.Tensor:
    """Apply one generated linear affordance-modulation rule."""
    expression = torch.ones_like(phase_multiplier)
    if threshold != 0.0:
        scaled = min_multiplier + (1.0 - min_multiplier) * (source_value / threshold)
        expression = torch.where(source_value < threshold, scaled, torch.ones_like(scaled))
    candidate = torch.clamp(phase_multiplier * expression, min=clamp_low, max=clamp_high)
    return torch.where(active_mask, candidate, phase_multiplier)


@torch.jit.script
def apply_terminal_condition(
    source_value: torch.Tensor,
    dones: torch.Tensor,
    active_mask: torch.Tensor,
    threshold: float,
    is_min_bound: bool,
) -> torch.Tensor:
    """Apply one generated terminal-condition rule."""
    if is_min_bound:
        triggered = source_value <= threshold
    else:
        triggered = source_value >= threshold
    return dones | (triggered & active_mask)
