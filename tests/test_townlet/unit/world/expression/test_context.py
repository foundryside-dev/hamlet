"""Tests for execution context."""

import pytest
import torch

from townlet.world.expression.context import ExecutionContext


def test_execution_context_get_bar():
    """Context resolves bar paths."""
    ctx = ExecutionContext(
        bars={"energy": torch.tensor([0.5, 0.8])},
        vfs={},
        affordances={},
        temporal={},
    )

    result = ctx.get("bar.energy")
    assert torch.equal(result, torch.tensor([0.5, 0.8]))


def test_execution_context_get_vfs():
    """Context resolves VFS paths."""
    ctx = ExecutionContext(
        bars={},
        vfs={"is_night": torch.tensor([True, False])},
        affordances={},
        temporal={},
    )

    result = ctx.get("vfs.is_night")
    assert torch.equal(result, torch.tensor([True, False]))


def test_execution_context_path_not_found():
    """Context raises KeyError for invalid paths."""
    ctx = ExecutionContext(bars={}, vfs={}, affordances={}, temporal={})

    with pytest.raises(KeyError, match="not found"):
        ctx.get("invalid.path")
