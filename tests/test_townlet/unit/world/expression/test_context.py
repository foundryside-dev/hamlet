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


def test_execution_context_agent_ref_traversal():
    """Agent references traverse into bar and VFS tensors."""
    bars = {"energy": torch.tensor([0.1, 0.5, 0.9])}
    vfs = {
        "friend": torch.tensor([1, 2, 0], dtype=torch.long),
        "energy": torch.tensor([0.2, 0.8, 0.4]),
    }
    ctx = ExecutionContext(
        bars=bars,
        vfs=vfs,
        affordances={},
        temporal={},
        vfs_types={"friend": "agent_ref", "energy": "float"},
        num_agents=3,
    )

    vfs_result = ctx.get("vfs.friend.vfs.energy")
    bar_result = ctx.get("vfs.friend.bar.energy")
    assert torch.allclose(vfs_result, torch.tensor([0.8, 0.4, 0.2]))
    assert torch.allclose(bar_result, torch.tensor([0.5, 0.9, 0.1]))


def test_execution_context_agent_ref_invalid_index():
    """Out-of-range references raise to avoid silent leaks."""
    bars = {"energy": torch.tensor([0.1, 0.5, 0.9])}
    vfs = {
        "friend": torch.tensor([99, 1, 2], dtype=torch.long),
        "energy": torch.tensor([0.2, 0.8, 0.4]),
    }
    ctx = ExecutionContext(
        bars=bars,
        vfs=vfs,
        affordances={},
        temporal={},
        vfs_types={"friend": "agent_ref", "energy": "float"},
        num_agents=3,
    )

    with pytest.raises(ValueError, match="agent reference"):
        ctx.get("vfs.friend.vfs.energy")


def test_execution_context_agent_ref_masks_sentinel_reference():
    """-1 sentinel indices are masked instead of raising."""
    bars = {"energy": torch.tensor([0.1, 0.5])}
    vfs = {
        "friend": torch.tensor([-1, 0], dtype=torch.long),
        "energy": torch.tensor([0.2, 0.8]),
    }
    ctx = ExecutionContext(
        bars=bars,
        vfs=vfs,
        affordances={},
        temporal={},
        vfs_types={"friend": "agent_ref", "energy": "float"},
        num_agents=2,
    )

    vfs_result = ctx.get("vfs.friend.vfs.energy")
    bar_result = ctx.get("vfs.friend.bar.energy")
    assert torch.allclose(vfs_result, torch.tensor([0.0, 0.2]))
    assert torch.allclose(bar_result, torch.tensor([0.0, 0.1]))


def test_execution_context_item_ref_masks_sentinel_reference():
    """Item references ignore the -1 sentinel and zero out missing entries."""
    item_vfs = torch.zeros((3, 1))
    item_vfs[1, 0] = 0.5
    item_vfs[2, 0] = 0.9
    ctx = ExecutionContext(
        bars={"energy": torch.tensor([1.0, 1.0])},
        vfs={"held_item": torch.tensor([-1, 2], dtype=torch.long)},
        affordances={},
        temporal={},
        vfs_types={"held_item": "item_ref"},
        num_agents=2,
        item_vfs=item_vfs,
        item_profile_map={"tool": {"quality": 0}},
        item_index_to_profile={1: "tool", 2: "tool"},
    )

    quality = ctx.get("vfs.held_item.vfs.quality")
    assert torch.allclose(quality, torch.tensor([0.0, 0.9]))


def test_execution_context_strips_ref_segments():
    """ref segments are ignored during traversal."""
    bars = {"energy": torch.tensor([0.1, 0.5, 0.9])}
    vfs = {
        "friend": torch.tensor([1, 2, 0], dtype=torch.long),
        "energy": torch.tensor([0.2, 0.8, 0.4]),
    }
    ctx = ExecutionContext(
        bars=bars,
        vfs=vfs,
        affordances={},
        temporal={},
        vfs_types={"friend": "agent_ref", "energy": "float"},
        num_agents=3,
    )

    vfs_result = ctx.get("vfs.ref.friend.vfs.energy")
    assert torch.allclose(vfs_result, torch.tensor([0.8, 0.4, 0.2]))
