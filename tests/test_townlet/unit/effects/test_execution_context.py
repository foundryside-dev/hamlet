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


# --- Self prefix tests ---


def test_execution_context_self_prefix_bar():
    """ExecutionContext resolves 'self.' prefix for bars."""
    import pytest

    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=2,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # self.bar.energy should resolve to energy[2]
    self_energy = context.get_path("self.bar.energy")
    assert self_energy.item() == pytest.approx(0.8)


def test_execution_context_self_prefix_vfs():
    """ExecutionContext resolves 'self.vfs.' for agent VFS variables."""
    import pytest

    variables = [
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
    registry.set("motivation", torch.tensor([1.0, 0.8, 1.2]), writer="engine")

    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0, 1.0, 1.0])},
        vfs_registry=registry,
        self_index=1,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # self.vfs.motivation should resolve to motivation[1]
    self_motivation = context.get_path("self.vfs.motivation")
    assert self_motivation.item() == pytest.approx(0.8)


# --- Affordance availability tests ---


def test_execution_context_affordance_available():
    """ExecutionContext resolves affordance availability paths."""
    bar_storage = {"energy": torch.tensor([1.0])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
        affordance_overrides={"food": True, "water": False},
    )

    food_available = context.get_path("affordance.food.available")
    assert food_available.item() is True

    water_available = context.get_path("affordance.water.available")
    assert water_available.item() is False


def test_execution_context_set_affordance_available():
    """ExecutionContext can set affordance availability."""
    bar_storage = {"energy": torch.tensor([1.0])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
        affordance_overrides={},
    )

    # Set affordance availability
    context.set_path("affordance.gym.available", torch.tensor(False))
    assert context.affordance_overrides["gym"] is False


# --- Target VFS tests ---


def test_execution_context_target_vfs():
    """ExecutionContext resolves 'target.vfs.' for agent VFS variables."""
    import pytest

    variables = [
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
    registry.set("motivation", torch.tensor([1.0, 0.8, 1.2]), writer="engine")

    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0, 1.0, 1.0])},
        vfs_registry=registry,
        self_index=0,
        target_index=2,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # target.vfs.motivation should resolve to motivation[2]
    target_motivation = context.get_path("target.vfs.motivation")
    assert target_motivation.item() == pytest.approx(1.2)


def test_execution_context_set_target_vfs():
    """ExecutionContext can set 'target.vfs.' for agent VFS variables."""
    variables = [
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
    registry.set("motivation", torch.tensor([1.0, 0.8, 1.2]), writer="engine")

    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0, 1.0, 1.0])},
        vfs_registry=registry,
        self_index=0,
        target_index=1,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # Set target.vfs.motivation
    context.set_path("target.vfs.motivation", torch.tensor(0.5))

    # Verify it was set
    all_motivation = registry.get("motivation", reader="engine")
    assert all_motivation[1].item() == 0.5


# --- Error path tests ---


def test_execution_context_target_index_not_set_raises():
    """ExecutionContext raises when target_index not set for target. paths."""
    import pytest

    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=0,
        target_index=None,  # Not set!
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    with pytest.raises(ValueError, match="target_index not set"):
        context.get_path("target.bar.energy")


def test_execution_context_self_index_not_set_raises():
    """ExecutionContext raises when self_index not set for self. paths."""
    import pytest

    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,  # Not set!
        target_index=0,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    with pytest.raises(ValueError, match="self_index not set"):
        context.get_path("self.bar.energy")


def test_execution_context_bar_not_found_raises():
    """ExecutionContext raises KeyError for unknown bar."""
    import pytest

    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=0,
        target_index=1,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    with pytest.raises(KeyError, match="unknown_bar"):
        context.get_path("bar.unknown_bar")


def test_execution_context_vfs_registry_not_set_raises():
    """ExecutionContext raises when VFS registry not set for vfs. paths."""
    import pytest

    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0])},
        vfs_registry=None,  # Not set!
        self_index=0,
        target_index=0,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    with pytest.raises(ValueError, match="VFS registry not set"):
        context.get_path("vfs.some_var")


def test_execution_context_invalid_path_raises():
    """ExecutionContext raises for invalid paths."""
    import pytest

    context = ExecutionContext(
        bars={"energy": torch.tensor([1.0])},
        vfs_registry=None,
        self_index=0,
        target_index=0,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    with pytest.raises(ValueError, match="Invalid path"):
        context.get_path("invalid.path.here")


# --- Copy/override tests ---


def test_execution_context_copy():
    """ExecutionContext.copy() creates shallow copy with overrides."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=0,
        target_index=1,
        effect_manager=DummyEffectManager(),
        item_manager=DummyItemManager(),
    )

    # Copy with override
    copied = context.copy(self_index=2, target_index=0)

    assert copied.self_index == 2
    assert copied.target_index == 0
    # Original unchanged
    assert context.self_index == 0
    assert context.target_index == 1
    # Shared reference to bars
    assert copied.bars is bar_storage
