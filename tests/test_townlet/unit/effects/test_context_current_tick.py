"""Test ExecutionContext current_tick parameter."""

import torch

from townlet.effects.context import ExecutionContext


def test_context_has_current_tick():
    """ExecutionContext should store current_tick."""
    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0])},
        vfs_registry=None,
        self_index=0,
        target_index=None,
        current_tick=42,
    )
    assert context.current_tick == 42


def test_context_current_tick_defaults_to_zero():
    """ExecutionContext current_tick should default to 0."""
    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0])},
        vfs_registry=None,
        self_index=0,
        target_index=None,
    )
    assert context.current_tick == 0
