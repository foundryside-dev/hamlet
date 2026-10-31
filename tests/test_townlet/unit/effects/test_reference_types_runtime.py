"""Runtime reference traversal for VFS variables.

The batch is independent single-agent worlds (S1): row w of a reference is world w's, so an
agent_ref holds its own world's agent or null (-1), and an item_ref an item row of its own
world or null. A reference outside its world is refused at write and at traversal.
"""

import pytest
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
            default=None,
            lifetime="episode",
            readable_by=["engine"],
            writable_by=["engine"],
        ),
        VariableDef(
            id="held_item",
            scope=VariableScope.AGENT,
            type="item_ref",
            default=None,
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
        items_per_world=max_items,
        item_profiles=item_profiles or {},
    )
    reg._storage["energy"] = torch.tensor([0.2, 0.8, 0.5])
    return reg


def test_agent_ref_traversal_reads_its_own_worlds_agent():
    bars = {"energy": torch.tensor([0.1, 0.6, 0.9])}
    registry = _registry_with_refs()
    registry.set("target", torch.tensor([-1, 1, -1]), writer="engine")
    ctx = ExecutionContext(bars=bars, vfs_registry=registry, self_index=1, target_index=None)

    # World 1's reference names world 1's agent: its own energy (0.8) and bar (0.6).
    assert torch.isclose(ctx.get_path("vfs.target.vfs.energy"), torch.tensor(0.8))
    assert torch.isclose(ctx.get_path("vfs.target.bar.energy"), torch.tensor(0.6))


def test_an_agent_ref_into_another_world_is_refused_at_write_and_at_traversal():
    registry = _registry_with_refs()
    with pytest.raises(RuntimeError, match="Engine defect: agent_ref 'target' in world 0 names agent 1"):
        registry.set("target", torch.tensor([1, 1, -1]), writer="engine")
    assert registry.get("target", reader="engine").tolist() == [-1, -1, -1]

    # Storage planted past the registry's checks still never reads across worlds.
    registry._storage["target"] = torch.tensor([1, 1, 1])
    ctx = ExecutionContext(bars={"energy": torch.ones(3)}, vfs_registry=registry, self_index=0, target_index=None)
    with pytest.raises(ValueError, match="worlds are independent"):
        ctx.get_path("vfs.target.vfs.energy")


def test_item_ref_traversal_reads_item_vfs():
    class _Profile:
        def __init__(self):
            self.variables = [
                type(
                    "Var",
                    (),
                    {"name": "quality", "type": "scalar", "readable_by": ("engine", "agent"), "writable_by": ("engine",), "exposed_to": ()},
                )()
            ]

    registry = _registry_with_refs(max_items=2, item_profiles={"tool": _Profile()})
    registry.register_item_instance(vfs_index=0, profile_name="tool")
    registry.item_vfs[0, 0] = 0.9
    registry.set("held_item", torch.tensor([0, -1, -1]), writer="engine")

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
    # Each world's agent points at itself.
    registry.set("target", torch.tensor([0, 1, 2]), writer="engine")
    ctx = ExecutionContext(
        bars=bars,
        vfs_registry=registry,
        self_index=0,
        target_index=1,
    )

    val = ctx.get_path("target.vfs.target.vfs.energy")
    assert torch.isclose(val, torch.tensor(0.8))

    bar_val = ctx.get_path("target.vfs.target.bar.energy")
    assert torch.isclose(bar_val, torch.tensor(0.6))


def test_target_reference_write_updates_target_slot():
    bars = {"energy": torch.tensor([0.1, 0.6, 0.9])}
    registry = _registry_with_refs()
    ctx = ExecutionContext(
        bars=bars,
        vfs_registry=registry,
        self_index=0,
        target_index=1,
    )

    ctx.set_path("target.vfs.target", torch.tensor(1))
    assert registry.get("target", reader="engine").tolist() == [-1, 1, -1]
    ctx.set_path("target.vfs.target", torch.tensor(-1))
    assert registry.get("target", reader="engine").tolist() == [-1, -1, -1]
    # World 1's agent cannot point at world 2's.
    with pytest.raises(RuntimeError, match="names agent 2"):
        ctx.set_path("target.vfs.target", torch.tensor(2))
