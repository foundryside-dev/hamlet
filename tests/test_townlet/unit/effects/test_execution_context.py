"""Tests for effect execution context."""

import torch

from townlet.effects.context import ExecutionContext
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef


class DummyEffectManager:
    def spawn_effect(self, *args, **kwargs):
        raise RuntimeError("spawn_effect not supported in DummyEffectManager")


class DummyItemManager:
    def spawn_item(self, *args, **kwargs):
        raise RuntimeError("spawn_item not supported in DummyItemManager")


def test_execution_context_bar_access():
    """ExecutionContext provides access to bar tensors."""
    bar_storage = {
        "energy": torch.tensor([1.0, 0.5, 0.8]),
        "health": torch.tensor([0.9, 0.7, 1.0]),
    }

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    energy = context.get_path("bar.energy")
    assert torch.equal(energy, torch.tensor([1.0, 0.5, 0.8]))


def test_execution_context_vfs_access():
    """ExecutionContext provides access to VFS variables."""
    variables = [
        VariableDef(
            id="day_count",
            scope="global",
            type="scalar",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            default=0.0,
        ),
        VariableDef(
            id="motivation",
            scope="agent",
            type="scalar",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            default=1.0,
        ),
    ]
    registry = VariableRegistry(variables=variables, num_agents=3, device=torch.device("cpu"))

    # Set initial values
    registry.set("day_count", torch.tensor(42.0), writer="engine")
    registry.set("motivation", torch.tensor([1.0, 0.8, 1.2]), writer="engine")

    context = ExecutionContext(
        bars=None,
        vfs_registry=registry,
        self_index=None,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    day_count = context.get_path("vfs.day_count")
    assert torch.equal(day_count, torch.tensor(42.0))

    motivation = context.get_path("vfs.motivation")
    assert torch.equal(motivation, torch.tensor([1.0, 0.8, 1.2]))


def test_execution_context_target_prefix():
    """ExecutionContext resolves 'target.' prefix."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=1,  # Target is agent index 1
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # target.bar.energy should resolve to energy[1]
    target_energy = context.get_path("target.bar.energy")
    assert target_energy.item() == 0.5


def test_execution_context_set_path():
    """ExecutionContext can mutate bar/VFS values."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # Mutate energy
    context.set_path("bar.energy", torch.tensor([0.9, 0.4, 0.7]))

    assert torch.equal(bar_storage["energy"], torch.tensor([0.9, 0.4, 0.7]))
