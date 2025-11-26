"""Unit tests for UniverseSymbolTable registration semantics."""

from dataclasses import dataclass

import pytest

from townlet.environment.action_config import ActionConfig
from townlet.universe.errors import CompilationError
from townlet.universe.symbol_table import UniverseSymbolTable
from townlet.vfs.schema import VariableDef


@dataclass
class _StubBar:
    name: str
    index: int


@dataclass
class _StubCascade:
    name: str
    description: str
    source: str
    target: str
    threshold: float
    strength: float


@dataclass
class _StubAffordance:
    id: str
    name: str
    category: str
    interaction_type: str
    costs: list
    effect_pipeline: dict
    operating_hours: list[int]


def test_duplicate_meter_registration_raises():
    table = UniverseSymbolTable()
    bar = _StubBar(name="energy", index=0)

    table.register_meter(bar)
    with pytest.raises(CompilationError):
        table.register_meter(bar)


def test_duplicate_variable_registration_raises():
    table = UniverseSymbolTable()
    var = VariableDef(
        id="energy",
        scope="agent",
        type="scalar",
        dims=None,
        lifetime="episode",
        readable_by=["agent"],
        writable_by=["engine"],
        default=1.0,
        description=None,
    )

    table.register_variable(var)
    with pytest.raises(CompilationError):
        table.register_variable(var)


def test_duplicate_action_registration_raises():
    table = UniverseSymbolTable()
    action = ActionConfig(
        id=0,
        name="REST",
        type="passive",
        costs={},
        effects={},
        delta=None,
        teleport_to=None,
        enabled=True,
        description=None,
        icon=None,
        source="custom",
        source_affordance=None,
        reads=[],
        writes=[],
    )

    table.register_action(action)
    with pytest.raises(CompilationError):
        table.register_action(action)


def test_duplicate_cascade_registration_raises():
    table = UniverseSymbolTable()
    cascade = _StubCascade(
        name="energy_to_health",
        description="starvation",
        source="energy",
        target="health",
        threshold=0.5,
        strength=0.1,
    )

    table.register_cascade(cascade)
    with pytest.raises(CompilationError):
        table.register_cascade(cascade)


def test_duplicate_affordance_registration_raises():
    table = UniverseSymbolTable()
    affordance = _StubAffordance(
        id="Bed",
        name="Bed",
        category="rest",
        interaction_type="instant",
        costs=[],
        effect_pipeline={"instant": [{"meter": "energy", "amount": 0.5}]},
        operating_hours=[0, 24],  # Required by BUG-30 fix
    )

    table.register_affordance(affordance)
    with pytest.raises(CompilationError):
        table.register_affordance(affordance)


def test_duplicate_item_registration_raises():
    table = UniverseSymbolTable()

    @dataclass
    class _Item:
        id: str

    item = _Item(id="apple")
    table.register_item(item)
    with pytest.raises(CompilationError):
        table.register_item(item)
