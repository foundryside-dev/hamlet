"""Tests for item-scoped VFS storage in registry."""

import pytest
import torch

from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope


def test_registry_allocates_item_storage():
    """Registry should allocate tensor for item-scoped variables."""
    variables = [
        VariableDef(
            id="durability",
            scope=VariableScope.ITEM,
            type="scalar",
            default=100.0,
            lifetime="persistent",
            readable_by=["agent", "engine"],
            writable_by=["actions", "engine"],
            description="Item durability",
        ),
        VariableDef(
            id="freshness",
            scope=VariableScope.ITEM,
            type="scalar",
            default=100.0,
            lifetime="persistent",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            description="Item freshness",
        ),
    ]

    registry = VariableRegistry(
        variables=variables,
        num_agents=4,
        max_items=10,  # NEW parameter
        device=torch.device("cpu"),
    )

    # Should have item_vfs tensor: [max_items, num_item_vars]
    assert hasattr(registry, "item_vfs")
    assert registry.item_vfs.shape == (10, 2)  # 10 items, 2 variables

    # Default values should be set
    assert torch.allclose(registry.item_vfs[:, 0], torch.tensor(100.0))  # durability
    assert torch.allclose(registry.item_vfs[:, 1], torch.tensor(100.0))  # freshness


def test_registry_read_item_variable():
    """Registry should support reading item variables via path."""
    variables = [
        VariableDef(
            id="durability",
            scope=VariableScope.ITEM,
            type="scalar",
            default=100.0,
            lifetime="persistent",
            readable_by=["agent", "engine"],
            writable_by=["actions", "engine"],
            description="Item durability",
        ),
    ]

    registry = VariableRegistry(
        variables=variables,
        num_agents=4,
        max_items=10,
        device=torch.device("cpu"),
    )

    # Read durability for item at vfs_index=3
    value = registry.read("durability", context_index=3, scope=VariableScope.ITEM)
    assert value == 100.0


def test_registry_write_item_variable():
    """Registry should support writing item variables via path."""
    variables = [
        VariableDef(
            id="durability",
            scope=VariableScope.ITEM,
            type="scalar",
            default=100.0,
            lifetime="persistent",
            readable_by=["agent", "engine"],
            writable_by=["actions", "engine"],
            description="Item durability",
        ),
    ]

    registry = VariableRegistry(
        variables=variables,
        num_agents=4,
        max_items=10,
        device=torch.device("cpu"),
    )

    # Write durability for item at vfs_index=3
    registry.write("durability", 75.0, context_index=3, scope=VariableScope.ITEM)

    # Verify write
    value = registry.read("durability", context_index=3, scope=VariableScope.ITEM)
    assert value == 75.0

    # Other items unchanged
    value_other = registry.read("durability", context_index=0, scope=VariableScope.ITEM)
    assert value_other == 100.0


def test_registry_rejects_wrong_scope():
    """Reading agent variable as item scope should raise clear error."""
    variables = [
        VariableDef(
            id="energy",
            scope=VariableScope.AGENT,  # Agent scope, not item
            type="scalar",
            default=100.0,
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            description="Agent energy",
        ),
        VariableDef(
            id="durability",
            scope=VariableScope.ITEM,
            type="scalar",
            default=100.0,
            lifetime="persistent",
            readable_by=["agent", "engine"],
            writable_by=["actions", "engine"],
            description="Item durability",
        ),
    ]

    registry = VariableRegistry(
        variables=variables,
        num_agents=4,
        max_items=10,
        device=torch.device("cpu"),
    )

    # Should raise ValueError with clear message about scope mismatch
    with pytest.raises(ValueError, match="has scope.*cannot read as item"):
        registry.read("energy", context_index=0, scope=VariableScope.ITEM)

    # Should also reject write with wrong scope
    with pytest.raises(ValueError, match="has scope.*cannot write as item"):
        registry.write("energy", 50.0, context_index=0, scope=VariableScope.ITEM)

    # Should work for correct scope
    value = registry.read("durability", context_index=0, scope=VariableScope.ITEM)
    assert value == 100.0
