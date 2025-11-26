"""Tests for collection resolution in effects system."""

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import pytest
import torch

from townlet.effects.collections import (
    COLLECTION_RESOLVERS,
    register_collection_resolver,
    resolve_collection,
)


@dataclass
class MockContext:
    """Minimal context for testing collection resolvers."""

    bars: dict[str, torch.Tensor] = field(default_factory=dict)
    self_index: int | None = None
    agent_positions: torch.Tensor | None = None
    inventory: Any = None
    effect_manager: Any = None


# --- all_agents resolver tests ---


def test_all_agents_returns_range_of_batch_size():
    """all_agents returns [0..batch_size-1]."""
    ctx = MockContext(bars={"energy": torch.zeros(5)})

    result = resolve_collection("all_agents", ctx)

    assert result == [0, 1, 2, 3, 4]


# --- nearby_agents resolver tests ---


def test_nearby_agents_requires_radius():
    """nearby_agents raises if radius not provided."""
    ctx = MockContext(
        bars={"energy": torch.zeros(4)},
        self_index=0,
        agent_positions=torch.tensor([[0.0, 0.0], [1.0, 0.0], [5.0, 0.0], [10.0, 0.0]]),
    )

    with pytest.raises(ValueError, match="radius required"):
        resolve_collection("nearby_agents", ctx)


def test_nearby_agents_requires_self_index():
    """nearby_agents raises if self_index is None."""
    ctx = MockContext(
        bars={"energy": torch.zeros(4)},
        self_index=None,  # Missing!
        agent_positions=torch.tensor([[0.0, 0.0], [1.0, 0.0], [5.0, 0.0], [10.0, 0.0]]),
    )

    with pytest.raises(ValueError, match="self_index required"):
        resolve_collection("nearby_agents", ctx, radius=2.0)


def test_nearby_agents_requires_agent_positions():
    """nearby_agents raises if agent_positions is None."""
    ctx = MockContext(
        bars={"energy": torch.zeros(4)},
        self_index=0,
        agent_positions=None,  # Missing!
    )

    with pytest.raises(ValueError, match="agent_positions required"):
        resolve_collection("nearby_agents", ctx, radius=2.0)


def test_nearby_agents_returns_agents_within_radius():
    """nearby_agents returns indices of agents within radius (excluding self)."""
    ctx = MockContext(
        bars={"energy": torch.zeros(4)},
        self_index=0,
        agent_positions=torch.tensor([[0.0, 0.0], [1.0, 0.0], [5.0, 0.0], [10.0, 0.0]]),
    )

    result = resolve_collection("nearby_agents", ctx, radius=2.0)

    # Agent 1 is at distance 1.0, within radius 2.0
    # Agent 2 is at distance 5.0, outside radius 2.0
    # Agent 3 is at distance 10.0, outside radius 2.0
    assert result == [1]


# --- inventory_items resolver tests ---


def test_inventory_items_requires_inventory():
    """inventory_items raises if inventory is None."""
    ctx = MockContext(self_index=0, inventory=None)

    with pytest.raises(ValueError, match="inventory required"):
        resolve_collection("inventory_items", ctx)


def test_inventory_items_returns_non_negative_slots():
    """inventory_items returns indices of items in inventory slots."""
    mock_inventory = MagicMock()
    mock_inventory.slots = torch.tensor([[1, -1, 3], [2, 4, -1]])  # batch_size=2, max_items=3

    ctx = MockContext(self_index=0, inventory=mock_inventory)

    result = resolve_collection("inventory_items", ctx)

    # Agent 0 has items at indices 1 and 3 (slot values >= 0)
    assert result == [1, 3]


# --- active_effects resolver tests ---


def test_active_effects_requires_effect_manager():
    """active_effects raises if effect_manager is None."""
    ctx = MockContext(self_index=0, effect_manager=None)

    with pytest.raises(ValueError, match="effect_manager required"):
        resolve_collection("active_effects", ctx)


def test_active_effects_requires_self_index():
    """active_effects raises if self_index is None."""
    mock_manager = MagicMock()
    mock_manager.agent_effects = {}

    ctx = MockContext(self_index=None, effect_manager=mock_manager)

    with pytest.raises(ValueError, match="self_index required"):
        resolve_collection("active_effects", ctx)


def test_active_effects_returns_effect_target_ids():
    """active_effects returns target_entity_id for each active effect."""
    effect1 = MagicMock()
    effect1.target_entity_id = 100
    effect2 = MagicMock()
    effect2.target_entity_id = 200

    mock_manager = MagicMock()
    mock_manager.agent_effects = {0: [effect1, effect2]}

    ctx = MockContext(self_index=0, effect_manager=mock_manager)

    result = resolve_collection("active_effects", ctx)

    assert result == [100, 200]


def test_active_effects_returns_empty_for_no_effects():
    """active_effects returns empty list when agent has no effects."""
    mock_manager = MagicMock()
    mock_manager.agent_effects = {}  # No effects for any agent

    ctx = MockContext(self_index=0, effect_manager=mock_manager)

    result = resolve_collection("active_effects", ctx)

    assert result == []


# --- register_collection_resolver tests ---


def test_register_collection_resolver_adds_new_resolver():
    """register_collection_resolver adds a new resolver."""

    def custom_resolver(context: Any, **kwargs: Any) -> list[int]:
        return [42]

    register_collection_resolver("custom_test", custom_resolver)

    assert "custom_test" in COLLECTION_RESOLVERS
    assert COLLECTION_RESOLVERS["custom_test"] is custom_resolver

    # Cleanup
    del COLLECTION_RESOLVERS["custom_test"]


def test_register_collection_resolver_overwrites_existing():
    """register_collection_resolver overwrites existing resolver."""

    def new_all_agents(context: Any, **kwargs: Any) -> list[int]:
        return [999]

    original = COLLECTION_RESOLVERS["all_agents"]
    register_collection_resolver("all_agents", new_all_agents)

    assert COLLECTION_RESOLVERS["all_agents"] is new_all_agents

    # Restore original
    COLLECTION_RESOLVERS["all_agents"] = original


# --- resolve_collection edge cases ---


def test_resolve_collection_rejects_non_positive_max_count():
    """resolve_collection raises for max_count <= 0."""
    ctx = MockContext(bars={"energy": torch.zeros(4)})

    with pytest.raises(ValueError, match="max_count must be positive"):
        resolve_collection("all_agents", ctx, max_count=0)


def test_resolve_collection_rejects_negative_max_count():
    """resolve_collection raises for negative max_count."""
    ctx = MockContext(bars={"energy": torch.zeros(4)})

    with pytest.raises(ValueError, match="max_count must be positive"):
        resolve_collection("all_agents", ctx, max_count=-1)


def test_resolve_collection_raises_for_unknown_type():
    """resolve_collection raises for unknown collection type."""
    ctx = MockContext(bars={"energy": torch.zeros(4)})

    with pytest.raises(ValueError, match="Unknown collection type"):
        resolve_collection("nonexistent_collection", ctx)


def test_resolve_collection_raises_for_exceeding_max_count():
    """resolve_collection raises when collection exceeds max_count."""
    ctx = MockContext(bars={"energy": torch.zeros(100)})

    with pytest.raises(RuntimeError, match="exceeds cap"):
        resolve_collection("all_agents", ctx, max_count=10)
