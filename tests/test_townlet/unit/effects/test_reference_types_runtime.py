"""Runtime reference traversal for VFS variables."""

import torch

from townlet.effects.context import ExecutionContext
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope


def _registry_with_refs(num_agents: int = 3, max_items: int = 0, item_profiles: dict | None = None) -> VariableRegistry:
    variables = [
        VariableDef(
            id="target",
            scope=VariableScope.AGENT,
            type="agent_ref",
            default=1,
            lifetime="episode",
            readable_by=["engine"],
            writable_by=["engine"],
        ),
        VariableDef(
            id="held_item",
            scope=VariableScope.AGENT,
            type="item_ref",
            default=0,
            lifetime="episode",
            readable_by=["engine"],
            writable_by=["engine"],
        ),
        VariableDef(
            id="energy",
            scope=VariableScope.AGENT,
            type="scalar",
            default=0.0,
            lifetime="episode",
            readable_by=["engine"],
            writable_by=["engine"],
        ),
    ]
    reg = VariableRegistry(
        variables=variables,
        num_agents=num_agents,
        device=torch.device("cpu"),
        max_items=max_items,
        item_profiles=item_profiles or {},
    )
    reg._storage["energy"] = torch.tensor([0.2, 0.8, 0.5])
    return reg


def test_agent_ref_traversal_reads_target_bar_and_vfs():
    bars = {"energy": torch.tensor([0.1, 0.6, 0.9])}
    registry = _registry_with_refs()
    ctx = ExecutionContext(
        bars=bars,
        vfs_registry=registry,
        self_index=0,
        target_index=None,
    )

    # vfs.target.vfs.energy should resolve to agent 1's energy (0.8)
    val = ctx.get_path("vfs.target.vfs.energy")
    assert torch.isclose(val, torch.tensor(0.8))

    # vfs.target.bar.energy should resolve to bars for agent 1 (0.6)
    bar_val = ctx.get_path("vfs.target.bar.energy")
    assert torch.isclose(bar_val, torch.tensor(0.6))


def test_item_ref_traversal_reads_item_vfs():
    class _Profile:
        def __init__(self):
            self.variables = [type("Var", (), {"name": "quality", "type": "scalar"})()]

    registry = _registry_with_refs(max_items=2, item_profiles={"tool": _Profile()})
    registry.register_item_instance(vfs_index=0, profile_name="tool")
    registry.item_vfs[0, 0] = 0.9

    ctx = ExecutionContext(
        bars={"energy": torch.tensor([1.0, 1.0, 1.0])},
        vfs_registry=registry,
        self_index=0,
        target_index=None,
    )

    val = ctx.get_path("vfs.held_item.vfs.quality")
    assert torch.isclose(val, torch.tensor(0.9))


def test_invalid_reference_index_raises():
    registry = _registry_with_refs()
    registry._storage["target"] = torch.tensor([999, 999, 999])
    ctx = ExecutionContext(
        bars={"energy": torch.tensor([1.0, 1.0, 1.0])},
        vfs_registry=registry,
        self_index=0,
        target_index=None,
    )

    try:
        ctx.get_path("vfs.target.vfs.energy")
    except ValueError as exc:
        assert "Invalid agent reference index" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid reference")


def test_target_vfs_reads_and_sets_target_agent():
    bars = {"energy": torch.tensor([0.1, 0.6, 0.9])}
    registry = _registry_with_refs()
    registry._storage["energy"] = torch.tensor([0.2, 0.8, 0.5])
    ctx = ExecutionContext(
        bars=bars,
        vfs_registry=registry,
        self_index=0,
        target_index=2,
    )

    # Read uses target_index (agent 2) rather than self_index (agent 0)
    val = ctx.get_path("target.vfs.energy")
    assert torch.isclose(val, torch.tensor(0.5))

    # Write back to target slot
    ctx.set_path("target.vfs.energy", torch.tensor(0.7))
    updated = registry.get("energy", reader="engine")
    assert torch.isclose(updated[2], torch.tensor(0.7))
    assert torch.isclose(updated[0], torch.tensor(0.2))


def test_target_reference_traversal_uses_target_index():
    bars = {"energy": torch.tensor([0.1, 0.6, 0.9])}
    registry = _registry_with_refs()
    registry._storage["energy"] = torch.tensor([0.2, 0.8, 0.5])
    # Agent 1 points to agent 2; agent 0 points to agent 1.
    registry._storage["target"] = torch.tensor([1, 2, 0])
    ctx = ExecutionContext(
        bars=bars,
        vfs_registry=registry,
        self_index=0,
        target_index=1,
    )

    val = ctx.get_path("target.vfs.target.vfs.energy")
    assert torch.isclose(val, torch.tensor(0.5))

    bar_val = ctx.get_path("target.vfs.target.bar.energy")
    assert torch.isclose(bar_val, torch.tensor(0.9))


def test_target_reference_write_updates_target_slot():
    bars = {"energy": torch.tensor([0.1, 0.6, 0.9])}
    registry = _registry_with_refs()
    registry._storage["target"] = torch.tensor([1, 1, 1])
    ctx = ExecutionContext(
        bars=bars,
        vfs_registry=registry,
        self_index=0,
        target_index=1,
    )

    ctx.set_path("target.vfs.target", torch.tensor(2))
    updated = registry.get("target", reader="engine")
    assert updated[1].item() == 2
    assert updated[0].item() == 1
