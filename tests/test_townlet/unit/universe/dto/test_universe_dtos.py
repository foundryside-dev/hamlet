"""Tests for universe DTOs."""

import pytest
import torch

from townlet.universe.dto import (
    ActionMetadata,
    ActionSpaceMetadata,
    AffordanceInfo,
    AffordanceMetadata,
    MeterInfo,
    MeterMetadata,
    UniverseMetadata,
)


class TestActionSpaceMetadata:
    """Action space helpers."""

    def test_action_mask(self):
        actions = (
            ActionMetadata(id=0, name="wait", type="passive", enabled=True, source="substrate", costs={}, description=""),
            ActionMetadata(id=1, name="sleep", type="interaction", enabled=False, source="affordance", costs={}, description=""),
        )
        metadata = ActionSpaceMetadata(total_actions=2, actions=actions)
        mask = metadata.get_action_mask(num_agents=2, device=torch.device("cpu"))

        assert mask.shape == (2, 2)
        assert torch.all(mask[:, 0])
        assert not torch.any(mask[:, 1])


class TestMeterMetadata:
    """Meter metadata helpers."""

    def test_get_meter_by_name(self):
        metadata = MeterMetadata(meters=(MeterInfo(name="energy", index=0, critical=True, initial_value=1.0, observable=True),))
        assert metadata.get_meter_by_name("energy").critical
        with pytest.raises(KeyError):
            metadata.get_meter_by_name("missing")


class TestAffordanceMetadata:
    """Affordance metadata helpers."""

    def test_lookup(self):
        metadata = AffordanceMetadata(
            affordances=(
                AffordanceInfo(
                    id="bed",
                    name="Bed",
                    enabled=True,
                    effects={"energy": 0.5},
                    cost=5.0,
                    category="rest",
                ),
            )
        )
        assert metadata.get_affordance_by_name("Bed").enabled
        with pytest.raises(KeyError):
            metadata.get_affordance_by_name("Shower")


def test_universe_metadata_instantiation():
    """UniverseMetadata stores summary fields."""
    metadata = UniverseMetadata(
        universe_name="L0_0_minimal",
        schema_version="1.0",
        primary_level="L0_0_minimal",
        substrate_type="grid",
        position_dim=2,
        meter_count=2,
        meter_names=("energy", "mood"),
        meter_name_to_index={"energy": 0, "mood": 1},
        affordance_count=1,
        affordance_ids=("Bed",),
        affordance_id_to_index={"Bed": 0},
        action_count=5,
        observation_dim=42,
        grid_size=3,
        grid_cells=9,
        ticks_per_day=24,
        config_version="1.0",
        compiler_version="0.1.0",
        compiled_at="2025-11-07T12:00:00Z",
        config_hash="abc123",
        provenance_id="prov",
        compiler_git_sha="deadbeef",
        python_version="3.11.0",
        torch_version="2.1.0",
        pydantic_version="2.6.0",
    )
    assert metadata.observation_dim == 42
