"""Performance guardrails for scripted VTC kernels."""

from __future__ import annotations

import time
from collections.abc import Callable

import torch

from townlet.vfs import vtc_kernels

SCRIPTED_KERNEL_TOLERANCE = 1.50


def _measure(fn: Callable[[], torch.Tensor], *, iterations: int) -> float:
    for _ in range(10):
        fn()
    start = time.perf_counter()
    for _ in range(iterations):
        fn()
    return (time.perf_counter() - start) / iterations


def test_scripted_vtc_threshold_kernel_within_hardcoded_baseline_tolerance() -> None:
    """Scripted hot path should stay close to the direct tensor equation it replaces."""
    source_value = torch.linspace(0.0, 1.0, steps=32768, dtype=torch.float32)
    target_value = torch.ones_like(source_value)
    active_mask = torch.ones_like(source_value, dtype=torch.bool)

    def hardcoded_baseline() -> torch.Tensor:
        delta = -0.006 * ((0.3 - source_value) / 0.3)
        candidate = torch.clamp(target_value + delta, min=0.0, max=1.0)
        return torch.where(active_mask & (source_value < 0.3), candidate, target_value)

    def scripted_vtc() -> torch.Tensor:
        return vtc_kernels.apply_threshold_cascade(
            source_value,
            target_value,
            active_mask,
            threshold=0.3,
            strength=0.006,
            strength_multiplier=1.0,
            clamp_low=0.0,
            clamp_high=1.0,
        )

    assert torch.allclose(scripted_vtc(), hardcoded_baseline())

    baseline_time = _measure(hardcoded_baseline, iterations=75)
    scripted_time = _measure(scripted_vtc, iterations=75)

    assert scripted_time <= baseline_time * SCRIPTED_KERNEL_TOLERANCE, (
        "Scripted VTC threshold kernel exceeded hardcoded baseline tolerance: "
        f"scripted={scripted_time:.8f}s baseline={baseline_time:.8f}s tolerance={SCRIPTED_KERNEL_TOLERANCE:.2f}x"
    )
