"""Unit tests for AffordanceEngine.

This file tests the core affordance engine API and mechanics that operate
independently of the environment.

Coverage focus (post-v2.1 refactor):
- Edge cases (affordance not found, invalid inputs)
- Opening hours and affordability checks
- Cost queries (get_affordance_cost, get_duration_ticks)
- Multi-tick vs instant/dual interaction semantics

Note: Full interaction flows and action masking are tested via
VectorizedHamletEnv in test_affordances.py and test_vectorized_env.py.
"""

from dataclasses import dataclass

import pytest
import torch

from townlet.effects.executor import CommandExecutor
from townlet.environment.affordance_engine import (
    AffordanceEngine,
)
from townlet.vfs import vtc


@dataclass
class RuntimeEffect:
    meter: str
    amount: float


@dataclass
class RuntimePipeline:
    on_start: list[RuntimeEffect]
    per_tick: list[RuntimeEffect]
    on_completion: list[RuntimeEffect]


@dataclass
class TimeWindow:
    """Time window for opening hours schedule."""

    start: int
    end: int


@dataclass
class OpeningHours:
    """Opening hours configuration for affordances."""

    enabled: bool
    schedule: list[TimeWindow] | None = None


def make_opening_hours(hours: tuple[int, int]) -> OpeningHours:
    """Helper to convert (open, close) tuple to OpeningHours object.

    Args:
        hours: Tuple of (open_hour, close_hour), e.g., (8, 18) for 8am-6pm.
               Use (0, 24) for 24/7 availability.

    Returns:
        OpeningHours object with appropriate enabled flag and schedule.
    """
    open_hour, close_hour = hours
    # (0, 24) means 24/7 - disable opening hours restriction
    if open_hour == 0 and close_hour == 24:
        return OpeningHours(enabled=False)
    return OpeningHours(enabled=True, schedule=[TimeWindow(start=open_hour, end=close_hour)])


@dataclass
class RuntimeAffordance:
    """Lightweight runtime affordance representation for AffordanceEngine tests."""

    id: str
    name: str
    interaction_type: str  # "instant", "multi_tick", or "dual"
    duration_ticks: int | None
    costs: list[dict[str, float]]
    costs_per_tick: list[dict[str, float]]
    effect_pipeline: RuntimePipeline | None
    opening_hours: OpeningHours


@dataclass
class DictCostAffordance:
    """Affordance shape that mirrors AffordanceParamConfig (dict-based costs)."""

    name: str
    interaction_type: str
    duration_ticks: int | None
    costs: dict[str, float]
    costs_per_tick: dict[str, float]
    interactions: dict
    opening_hours: OpeningHours
    id: str | None = None


@pytest.fixture
def affordance_engine_components(cpu_device):
    """Provide a synthetic meter map and affordance set for AffordanceEngine tests.

    This fixture is intentionally decoupled from on-disk config packs so the
    engine can be tested in isolation.
    """

    # Stable meter ordering used in tests (matches mock_config.yaml semantics)
    meter_name_to_index = {
        "energy": 0,
        "hygiene": 1,
        "satiation": 2,
        "money": 3,
        "mood": 4,
        "social": 5,
        "health": 6,
        "fitness": 7,
    }

    class BarsConfigCompat:
        def __init__(self, mapping: dict[str, int]):
            self.meter_name_to_index = mapping

    bars_config = BarsConfigCompat(meter_name_to_index)

    # Runtime affordances used across tests.
    affordances: tuple[RuntimeAffordance, ...] = (
        # Bed: multi-tick/dual-style rest affordance
        RuntimeAffordance(
            id="0",
            name="Bed",
            interaction_type="dual",
            duration_ticks=5,
            costs=[{"meter": "money", "amount": 0.0}],
            costs_per_tick=[{"meter": "money", "amount": 0.01}],
            effect_pipeline=RuntimePipeline(
                on_start=[],
                per_tick=[RuntimeEffect(meter="energy", amount=0.05)],
                on_completion=[RuntimeEffect(meter="energy", amount=0.25)],
            ),
            opening_hours=make_opening_hours((0, 24)),  # Always available
        ),
        # Shower: instant/dual hygiene affordance ($0.03, +0.4 hygiene)
        RuntimeAffordance(
            id="1",
            name="Shower",
            interaction_type="dual",
            duration_ticks=3,
            costs=[{"meter": "money", "amount": 0.03}],
            costs_per_tick=[],
            effect_pipeline=RuntimePipeline(
                on_start=[RuntimeEffect(meter="hygiene", amount=0.4)],
                per_tick=[],
                on_completion=[],
            ),
            opening_hours=make_opening_hours((0, 24)),
        ),
        # FastFood: dual-mode convenience food ($0.05, 2 ticks)
        RuntimeAffordance(
            id="2",
            name="FastFood",
            interaction_type="dual",
            duration_ticks=2,
            costs=[{"meter": "money", "amount": 0.05}],
            costs_per_tick=[],
            effect_pipeline=RuntimePipeline(
                on_start=[],
                per_tick=[RuntimeEffect(meter="satiation", amount=0.225)],
                on_completion=[RuntimeEffect(meter="satiation", amount=0.225)],
            ),
            opening_hours=make_opening_hours((0, 24)),
        ),
        # Job: dual-mode income source (4 ticks)
        RuntimeAffordance(
            id="3",
            name="Job",
            interaction_type="dual",
            duration_ticks=4,
            costs=[],
            costs_per_tick=[],
            effect_pipeline=RuntimePipeline(
                on_start=[],
                per_tick=[
                    RuntimeEffect(meter="money", amount=0.05625),
                    RuntimeEffect(meter="energy", amount=-0.0375),
                ],
                on_completion=[RuntimeEffect(meter="money", amount=0.05625)],
            ),
            opening_hours=make_opening_hours((8, 18)),  # 8am-6pm
        ),
        # Hospital: instant health restore ($0.15)
        RuntimeAffordance(
            id="4",
            name="Hospital",
            interaction_type="instant",
            duration_ticks=None,
            costs=[{"meter": "money", "amount": 0.15}],
            costs_per_tick=[],
            effect_pipeline=RuntimePipeline(
                on_start=[RuntimeEffect(meter="health", amount=0.4)],
                per_tick=[],
                on_completion=[],
            ),
            opening_hours=make_opening_hours((0, 24)),
        ),
        # Bar: social/mood/health trade-off ($0.15, wraparound hours)
        RuntimeAffordance(
            id="5",
            name="Bar",
            interaction_type="instant",
            duration_ticks=None,
            costs=[{"meter": "money", "amount": 0.15}],
            costs_per_tick=[],
            effect_pipeline=RuntimePipeline(
                on_start=[
                    RuntimeEffect(meter="social", amount=0.5),
                    RuntimeEffect(meter="mood", amount=0.25),
                    RuntimeEffect(meter="health", amount=-0.05),
                ],
                per_tick=[],
                on_completion=[],
            ),
            opening_hours=make_opening_hours((18, 28)),  # 6pm-4am
        ),
        # Park: free recreation (no costs)
        RuntimeAffordance(
            id="6",
            name="Park",
            interaction_type="instant",
            duration_ticks=None,
            costs=[],
            costs_per_tick=[],
            effect_pipeline=RuntimePipeline(
                on_start=[
                    RuntimeEffect(meter="social", amount=0.1),
                    RuntimeEffect(meter="fitness", amount=0.05),
                    RuntimeEffect(meter="mood", amount=0.05),
                ],
                per_tick=[],
                on_completion=[],
            ),
            opening_hours=make_opening_hours((0, 24)),
        ),
    )

    return bars_config, affordances


class TestAffordanceQueries:
    """Test affordance lookup and query methods."""

    def test_get_affordance_by_id(self, cpu_device, affordance_engine_components):
        """Get affordance by ID should return correct config."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Get Bed by ID (Bed is the first affordance in action_masking pack)
        bed = engine.get_affordance("0")
        assert bed is not None
        assert bed.name == "Bed"

    def test_get_affordance_invalid_id_returns_none(self, cpu_device, affordance_engine_components):
        """Get affordance with invalid ID should return None."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Invalid ID
        result = engine.get_affordance("invalid_id_12345")
        assert result is None

    def test_get_num_affordances(self, cpu_device, affordance_engine_components):
        """Get number of affordances should return correct count."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Synthetic fixture defines 7 affordances
        assert engine.get_num_affordances() == 7

    def test_get_affordance_action_map(self, cpu_device, affordance_engine_components):
        """Get affordance action map should return name-to-index mapping."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        action_map = engine.get_affordance_action_map()

        # Should be a dict
        assert isinstance(action_map, dict)

        # Synthetic fixture defines 7 affordances
        assert len(action_map) == 7

        # Should contain expected affordances from synthetic fixture
        assert "Bed" in action_map
        assert "Hospital" in action_map
        assert "Job" in action_map

        # Indices should be integers
        assert all(isinstance(idx, int) for idx in action_map.values())


class TestOperatingHours:
    """Test operating hours and availability checks."""

    def test_is_affordance_open_invalid_name_returns_false(self, cpu_device, affordance_engine_components):
        """Check if invalid affordance name returns False."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Invalid affordance name
        assert not engine.is_affordance_open("InvalidAffordance", time_of_day=12)

    def test_is_affordance_open_wraparound_hours(self, cpu_device, affordance_engine_components):
        """Check midnight wraparound hours (Bar: 18-28 = 6pm-4am)."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Bar: [18, 28] (6pm to 4am, wraps midnight)
        assert engine.is_affordance_open("Bar", time_of_day=18)  # 6pm - OPEN
        assert engine.is_affordance_open("Bar", time_of_day=23)  # 11pm - OPEN
        assert engine.is_affordance_open("Bar", time_of_day=0)  # Midnight - OPEN
        assert engine.is_affordance_open("Bar", time_of_day=3)  # 3am - OPEN
        assert not engine.is_affordance_open("Bar", time_of_day=4)  # 4am - CLOSED
        assert not engine.is_affordance_open("Bar", time_of_day=12)  # Noon - CLOSED

    def test_is_affordance_open_normal_hours(self, cpu_device, affordance_engine_components):
        """Check normal operating hours (Job: 8-18 = 8am-6pm)."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Job: [8, 18] (8am to 6pm, no wraparound)
        assert not engine.is_affordance_open("Job", time_of_day=6)  # 6am - CLOSED
        assert engine.is_affordance_open("Job", time_of_day=8)  # 8am - OPEN
        assert engine.is_affordance_open("Job", time_of_day=12)  # Noon - OPEN
        assert engine.is_affordance_open("Job", time_of_day=17)  # 5pm - OPEN
        assert not engine.is_affordance_open("Job", time_of_day=18)  # 6pm - CLOSED
        assert not engine.is_affordance_open("Job", time_of_day=20)  # 8pm - CLOSED


class TestAffordabilityChecking:
    """Test affordability validation logic."""

    def test_check_affordability_single_cost(self, cpu_device, affordance_engine_components):
        """Check affordability with single cost (money)."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=4, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Create meter tensors (4 agents)
        meters = torch.zeros((4, 8), dtype=torch.float32, device=cpu_device)
        meters[:, 3] = torch.tensor([0.10, 0.05, 0.00, 0.15], device=cpu_device)  # Money

        # Hospital costs $0.15 (money)
        hospital = engine.affordance_map["Hospital"]
        can_afford = engine._check_affordability(meters, hospital.costs)

        # Agents with >= $0.15 can afford (only agent 3)
        expected = torch.tensor([False, False, False, True], device=cpu_device)
        assert torch.equal(can_afford, expected)

    def test_check_affordability_multiple_costs(self, cpu_device, affordance_engine_components):
        """Check affordability with no costs (always affordable)."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=4, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Create meter tensors
        meters = torch.zeros((4, 8), dtype=torch.float32, device=cpu_device)
        meters[:, 0] = torch.tensor([0.80, 0.10, 0.50, 0.80], device=cpu_device)  # Energy
        meters[:, 3] = torch.tensor([0.10, 0.10, 0.00, 0.10], device=cpu_device)  # Money

        # Park has no costs, so all agents can afford
        park = engine.affordance_map["Park"]
        can_afford = engine._check_affordability(meters, park.costs)

        # All agents should be able to afford (no costs)
        expected = torch.tensor([True, True, True, True], device=cpu_device)
        assert torch.equal(can_afford, expected)

    def test_check_affordability_all_agents_can_afford(self, cpu_device, affordance_engine_components):
        """All agents can afford should return all True."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=4, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # All agents have plenty of money
        meters = torch.ones((4, 8), dtype=torch.float32, device=cpu_device)

        # Shower costs $0.03
        shower = engine.affordance_map["Shower"]
        can_afford = engine._check_affordability(meters, shower.costs)

        # All should be able to afford
        assert torch.all(can_afford)

    def test_check_affordability_mixed_affordability(self, cpu_device, affordance_engine_components):
        """Mixed affordability should return correct mask."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=4, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Varied money levels
        meters = torch.zeros((4, 8), dtype=torch.float32, device=cpu_device)
        meters[:, 3] = torch.tensor([0.20, 0.02, 0.10, 0.00], device=cpu_device)

        # FastFood costs $0.05
        fastfood = engine.affordance_map["FastFood"]
        can_afford = engine._check_affordability(meters, fastfood.costs)

        # Agent 0: $0.20 ✅, Agent 1: $0.02 ❌, Agent 2: $0.10 ✅, Agent 3: $0.00 ❌
        expected = torch.tensor([True, False, True, False], device=cpu_device)
        assert torch.equal(can_afford, expected)


class TestCostQueries:
    """Test cost and tick requirement queries."""

    def test_get_affordance_cost_instant_mode(self, cpu_device, affordance_engine_components):
        """Get instant mode cost should return correct value."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Shower instant cost: $0.03
        cost = engine.get_affordance_cost("Shower", cost_mode="instant")
        assert abs(cost - 0.03) < 1e-6

        # Hospital instant cost: $0.15
        cost = engine.get_affordance_cost("Hospital", cost_mode="instant")
        assert abs(cost - 0.15) < 1e-6

    def test_get_affordance_cost_per_tick_mode(self, cpu_device, affordance_engine_components):
        """Get per-tick mode cost should return correct value."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Bed per-tick cost: $0.01 per tick
        cost = engine.get_affordance_cost("Bed", cost_mode="per_tick")
        assert abs(cost - 0.01) < 1e-6

    def test_get_affordance_cost_invalid_affordance(self, cpu_device, affordance_engine_components):
        """Get cost for invalid affordance should return 0.0."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        cost = engine.get_affordance_cost("InvalidAffordance", cost_mode="instant")
        assert cost == 0.0

    def test_get_duration_ticks_instant(self, cpu_device, affordance_engine_components):
        """Get required ticks for dual-mode affordances returns actual tick count."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Shower is dual-mode, requires 3 ticks
        ticks = engine.get_duration_ticks("Shower")
        assert ticks == 3

        # FastFood is dual-mode, requires 2 ticks
        ticks = engine.get_duration_ticks("FastFood")
        assert ticks == 2

    def test_get_duration_ticks_multi_tick(self, cpu_device, affordance_engine_components):
        """Get required ticks for multi-tick affordance should return correct value."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        # Bed requires 5 ticks
        ticks = engine.get_duration_ticks("Bed")
        assert ticks == 5

        # Job requires 4 ticks
        ticks = engine.get_duration_ticks("Job")
        assert ticks == 4

    def test_get_duration_ticks_invalid_affordance(self, cpu_device, affordance_engine_components):
        """Get required ticks for invalid affordance should return 1."""
        bars_config, affordance_config = affordance_engine_components
        engine = AffordanceEngine(affordance_config, num_agents=1, device=cpu_device, meter_name_to_idx=bars_config.meter_name_to_index)

        ticks = engine.get_duration_ticks("InvalidAffordance")
        assert ticks == 1


class TestDictCostAffordances:
    """Regression coverage for dict-style costs from AffordanceParamConfig."""

    def _build_engine(self, affordances: tuple, cpu_device):
        meter_map = {"energy": 0, "money": 1}
        return AffordanceEngine(affordances, num_agents=1, device=cpu_device, meter_name_to_idx=meter_map)

    def test_apply_instant_interaction_handles_dict_costs(self, cpu_device):
        affordance = DictCostAffordance(
            name="Eat",
            interaction_type="instant",
            duration_ticks=None,
            costs={"energy": 0.2, "money": 0.1},
            costs_per_tick={},
            interactions={},
            opening_hours=make_opening_hours((0, 24)),
        )
        engine = self._build_engine((affordance,), cpu_device)
        meters = torch.tensor([[1.0, 0.5]], device=cpu_device)
        mask = torch.tensor([True], device=cpu_device)

        updated = engine.apply_instant_interaction(meters, "Eat", mask, check_affordability=True)

        assert torch.isclose(updated[0, 0], torch.tensor(0.8, device=cpu_device))  # energy
        assert torch.isclose(updated[0, 1], torch.tensor(0.4, device=cpu_device))  # money

    def test_check_affordability_with_dict_costs(self, cpu_device):
        affordance = DictCostAffordance(
            name="Expensive",
            interaction_type="instant",
            duration_ticks=None,
            costs={"energy": 0.6},
            costs_per_tick={},
            interactions={},
            opening_hours=make_opening_hours((0, 24)),
        )
        engine = self._build_engine((affordance,), cpu_device)
        meters = torch.tensor([[0.5, 1.0]], device=cpu_device)

        result = engine._check_affordability(meters, affordance.costs)

        assert torch.equal(result, torch.tensor([False], device=cpu_device))

    def test_apply_multi_tick_with_dict_costs_per_tick(self, cpu_device):
        affordance = DictCostAffordance(
            name="Train",
            interaction_type="multi_tick",
            duration_ticks=2,
            costs={},
            costs_per_tick={"money": 0.1},
            interactions={},
            opening_hours=make_opening_hours((0, 24)),
        )
        engine = self._build_engine((affordance,), cpu_device)
        meters = torch.tensor([[1.0, 1.0]], device=cpu_device)
        mask = torch.tensor([True], device=cpu_device)

        updated = engine.apply_multi_tick_interaction(meters, "Train", current_tick=0, agent_mask=mask, check_affordability=True)

        assert torch.isclose(updated[0, 1], torch.tensor(0.9, device=cpu_device))

    def test_get_affordance_cost_reads_money_from_dict(self, cpu_device):
        affordance = DictCostAffordance(
            name="Taxi",
            interaction_type="instant",
            duration_ticks=None,
            costs={"money": 0.25},
            costs_per_tick={},
            interactions={},
            opening_hours=make_opening_hours((0, 24)),
        )
        engine = self._build_engine((affordance,), cpu_device)

        assert engine.get_affordance_cost("Taxi", cost_mode="instant") == 0.25


def test_affordance_engine_executes_effects_commands():
    """Affordances with interactions field execute Effects commands."""
    # This test verifies that AffordanceEngine can compile and execute Effects commands
    # from the interactions field. It tests the basic integration without needing
    # a full VectorizedHamletEnv setup.

    from unittest.mock import Mock

    from townlet.config.affordances_v2_config import AffordanceParamConfig, DeploymentConfig, OpeningHoursConfig

    # Create affordance with interactions (Effects commands)
    affordance = AffordanceParamConfig(
        name="TEST_AFFORDANCE",
        interaction_type="instant",
        costs={},
        interactions={
            "on_start": [{"modify": "target.bar.energy", "value": "target.bar.energy + 0.5"}],
            "per_tick": [],
            "on_completion": [],
            "on_early_exit": [],
            "on_failure": [],
        },
        opening_hours=OpeningHoursConfig(enabled=False),
        deployment=DeploymentConfig(type="random"),
    )

    # Create mock VFS registry and effects schema
    mock_registry = Mock()
    mock_registry.storage = {"energy": torch.tensor([0.2, 0.3])}

    # Effects schema is dict[str, str] mapping paths to types
    effects_schema = {
        "target.bar.energy": "float",
        "target.bar.health": "float",
    }

    # Create mock command executor
    mock_executor = Mock(spec=CommandExecutor)

    # Create affordance engine - should compile Effects at init
    meter_name_to_idx = {"energy": 0, "health": 1}
    engine = AffordanceEngine(
        affordance_config=(affordance,),
        num_agents=2,
        device=torch.device("cpu"),
        meter_name_to_idx=meter_name_to_idx,
        modulation_program=None,
        vfs_registry=mock_registry,
        effects_schema=effects_schema,
        command_executor=mock_executor,
    )

    # Verify compilation happened
    assert "TEST_AFFORDANCE" in engine.compiled_affordances
    compiled = engine.compiled_affordances["TEST_AFFORDANCE"]

    # Verify on_start commands were compiled
    assert len(compiled.on_start) > 0

    # Verify other stages are empty
    assert len(compiled.per_tick) == 0
    assert len(compiled.on_completion) == 0
    assert len(compiled.on_early_exit) == 0
    assert len(compiled.on_failure) == 0


def test_affordance_effects_apply_modulation_multiplier():
    """Effect deltas inherit the modulation multiplier (not just costs)."""
    from townlet.config.affordances_v2_config import AffordanceParamConfig, DeploymentConfig, OpeningHoursConfig

    affordance = AffordanceParamConfig(
        name="TEST_AFFORDANCE",
        interaction_type="instant",
        costs={},
        interactions={
            "on_start": [{"modify": "target.bar.energy", "value": "target.bar.energy + 0.4"}],
            "per_tick": [],
            "on_completion": [],
            "on_early_exit": [],
            "on_failure": [],
        },
        opening_hours=OpeningHoursConfig(enabled=False),
        deployment=DeploymentConfig(type="random"),
    )

    effects_schema = {
        "target.bar.energy": "float",
    }

    from townlet.config.affordances_v2_config import ModulationParamConfig

    modulation_program = vtc.compile_vtc_modulations(
        [
            ModulationParamConfig(
                bar="energy",
                affordances=["TEST_AFFORDANCE"],
                type="linear_multiplier",
                threshold=1.0,
                min_multiplier=0.5,
            )
        ]
    )

    engine = AffordanceEngine(
        affordance_config=(affordance,),
        num_agents=1,
        device=torch.device("cpu"),
        meter_name_to_idx={"energy": 0},
        modulation_program=modulation_program,
        vfs_registry=None,
        effects_schema=effects_schema,
        command_executor=CommandExecutor(),
    )

    meters = torch.tensor([[0.0]], dtype=torch.float32)
    updated = engine.apply_instant_interaction(meters, "TEST_AFFORDANCE", torch.tensor([True]))

    # Interaction delta is 0.4 but should be scaled by multiplier (0.5 at energy=0.0)
    assert updated[0, 0].item() == pytest.approx(0.2)


def test_affordance_effects_apply_vtc_modulation_multiplier():
    """AffordanceEngine should get modulation multipliers from the compiled VTC program."""
    from townlet.config.affordances_v2_config import (
        AffordanceParamConfig,
        DeploymentConfig,
        ModulationParamConfig,
        OpeningHoursConfig,
    )

    assert hasattr(vtc, "compile_vtc_modulations"), "VTC modulation compiler is required"

    affordance = AffordanceParamConfig(
        name="TEST_AFFORDANCE",
        interaction_type="instant",
        costs={},
        interactions={
            "on_start": [{"modify": "target.bar.energy", "value": "target.bar.energy + 0.4"}],
            "per_tick": [],
            "on_completion": [],
            "on_early_exit": [],
            "on_failure": [],
        },
        opening_hours=OpeningHoursConfig(enabled=False),
        deployment=DeploymentConfig(type="random"),
    )
    modulation_program = vtc.compile_vtc_modulations(
        [
            ModulationParamConfig(
                bar="energy",
                affordances=["TEST_AFFORDANCE"],
                type="linear_multiplier",
                threshold=1.0,
                min_multiplier=0.5,
            )
        ]
    )

    engine = AffordanceEngine(
        affordance_config=(affordance,),
        num_agents=1,
        device=torch.device("cpu"),
        meter_name_to_idx={"energy": 0},
        modulation_program=modulation_program,
        vfs_registry=None,
        effects_schema={"target.bar.energy": "float"},
        command_executor=CommandExecutor(),
    )

    meters = torch.tensor([[0.0]], dtype=torch.float32)
    updated = engine.apply_instant_interaction(meters, "TEST_AFFORDANCE", torch.tensor([True]))

    assert updated[0, 0].item() == pytest.approx(0.2)


def test_get_meter_idx_validation_raises_on_unknown_meter():
    """_get_meter_idx should raise KeyError with helpful message for unknown meters (ENV-005).

    The error message should include:
    1. The unknown meter name
    2. The context (if provided)
    3. List of available meters
    """
    from townlet.effects.executor import CommandExecutor

    @dataclass
    class SimpleAffordance:
        id: str
        name: str
        interaction_type: str
        duration_ticks: int | None
        costs: list[dict]
        costs_per_tick: list[dict]
        effect_pipeline: None
        opening_hours: OpeningHours

    # Create an affordance with an unknown meter in costs
    affordance_with_bad_meter = SimpleAffordance(
        id="test",
        name="BadMeterAffordance",
        interaction_type="instant",
        duration_ticks=None,
        costs=[{"meter": "nonexistent_bar", "amount": 0.1}],  # This meter doesn't exist
        costs_per_tick=[],
        effect_pipeline=None,
        opening_hours=make_opening_hours((0, 24)),
    )

    # Only define "energy" as valid meter, not "nonexistent_bar"
    engine = AffordanceEngine(
        affordance_config=(affordance_with_bad_meter,),
        num_agents=1,
        device=torch.device("cpu"),
        meter_name_to_idx={"energy": 0, "health": 1},
        modulation_program=None,
        vfs_registry=None,
        effects_schema={},
        command_executor=CommandExecutor(),
    )

    meters = torch.tensor([[1.0, 1.0]], dtype=torch.float32)

    # Trying to apply this affordance should raise KeyError with context
    with pytest.raises(KeyError) as excinfo:
        engine.apply_instant_interaction(meters, "BadMeterAffordance", torch.tensor([True]))

    error_msg = str(excinfo.value)
    # Should mention the unknown meter
    assert "nonexistent_bar" in error_msg
    # Should mention the affordance context
    assert "BadMeterAffordance" in error_msg or "affordance" in error_msg.lower()
    # Should list available meters
    assert "energy" in error_msg or "Available" in error_msg
