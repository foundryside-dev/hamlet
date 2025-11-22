from pathlib import Path

import pytest
import torch

from townlet.config.items_config import ItemAppearanceRuleConfig, ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.items.manager import ItemManager
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError


def _compile_when(rule: ItemAppearanceRuleConfig, schema: dict[str, str]) -> None:
    parser = ExpressionParser()
    checker = TypeChecker(schema=schema)
    ast = parser.parse(rule.when or "")
    assert checker.check(ast) == "bool"
    rule.when_ast = ast


def _appearance(items):
    return ItemsAppearanceConfig(version="1.0", items=items)


def test_spawn_initial_items_gated_by_bar_condition() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))

    appearance = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "placement": {"mode": "random"},
                "when": "bar.energy > 0.5",
            }
        ]
    )

    rule = appearance.items[0]
    _compile_when(rule, {"bar.energy": "float"})

    manager = ItemManager(catalog=catalog, max_items=5, device="cpu")

    low_bars = {"energy": torch.tensor([0.25])}
    manager.spawn_initial_items(appearance, grid_size=(3, 3), current_tick=0, bars=low_bars)
    assert len(manager.active_items) == 0

    high_bars = {"energy": torch.tensor([0.75])}
    manager.spawn_initial_items(appearance, grid_size=(3, 3), current_tick=0, bars=high_bars)
    assert len(manager.active_items) == 1


def test_process_respawns_respects_condition() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))

    appearance = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "schedule": {"type": "periodic", "period": 1},
                "placement": {"mode": "random"},
                "when": "bar.energy > 0.5",
            }
        ]
    )

    rule = appearance.items[0]
    _compile_when(rule, {"bar.energy": "float"})

    manager = ItemManager(catalog=catalog, max_items=5, device="cpu")
    manager.set_appearance_config(appearance, grid_size=(3, 3))

    manager.respawn_timers["apple"] = 0
    low_bars = {"energy": torch.tensor([0.1])}
    manager.process_respawns(current_tick=0, bars=low_bars)
    assert len(manager.active_items) == 0

    manager.respawn_timers["apple"] = 0
    high_bars = {"energy": torch.tensor([1.0])}
    manager.process_respawns(current_tick=0, bars=high_bars)
    assert len(manager.active_items) == 1


def test_vfs_condition_gates_spawn() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))

    appearance = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "placement": {"mode": "random"},
                "when": "vfs.is_raining",
            }
        ]
    )

    rule = appearance.items[0]
    _compile_when(rule, {"vfs.is_raining": "bool", "bar.energy": "float"})

    class _DummyProfile:
        variables: tuple = ()

    registry = VariableRegistry(
        variables=[
            VariableDef(
                id="is_raining",
                scope=VariableScope.GLOBAL,
                type="bool",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=False,
            )
        ],
        num_agents=2,
        device=torch.device("cpu"),
        max_items=5,
        item_profiles={"food": _DummyProfile()},
    )

    manager = ItemManager(catalog=catalog, max_items=5, device="cpu", vfs_registry=registry)
    bars = {"energy": torch.tensor([0.9, 0.9])}

    # False -> no spawn
    registry._storage["is_raining"] = torch.tensor(False)
    manager.spawn_initial_items(appearance, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 0

    # True -> spawn
    registry._storage["is_raining"] = torch.tensor(True)
    manager.spawn_initial_items(appearance, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 1


def test_temporal_condition_and_boolean_logic() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "placement": {"mode": "random"},
                "when": "vfs.is_raining and temporal.tick > 5",
            }
        ]
    )

    rule = appearance.items[0]
    _compile_when(rule, {"vfs.is_raining": "bool", "temporal.tick": "int", "bar.energy": "float"})

    class _DummyProfile:
        variables: tuple = ()

    registry = VariableRegistry(
        variables=[
            VariableDef(
                id="is_raining",
                scope=VariableScope.GLOBAL,
                type="bool",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=False,
            )
        ],
        num_agents=1,
        device=torch.device("cpu"),
        max_items=5,
        item_profiles={"food": _DummyProfile()},
    )

    manager = ItemManager(catalog=catalog, max_items=5, device="cpu", vfs_registry=registry)
    bars = {"energy": torch.tensor([1.0])}

    # tick low -> no spawn
    registry._storage["is_raining"] = torch.tensor(True)
    manager.spawn_initial_items(appearance, grid_size=(3, 3), current_tick=0, bars=bars, temporal={"tick": torch.tensor(3)})
    assert len(manager.active_items) == 0

    # tick high and raining -> spawn
    manager.spawn_initial_items(appearance, grid_size=(3, 3), current_tick=6, bars=bars, temporal={"tick": torch.tensor(6)})
    assert len(manager.active_items) == 1


def test_comparison_variants_and_vector_reduction() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "placement": {"mode": "random"},
                "when": "bar.energy >= 0.5",
            }
        ]
    )

    rule = appearance.items[0]
    _compile_when(rule, {"bar.energy": "float"})

    manager = ItemManager(catalog=catalog, max_items=5, device="cpu")

    # Mixed batch (one below threshold) -> all() reduction rejects
    bars = {"energy": torch.tensor([0.4, 0.7])}
    manager.spawn_initial_items(appearance, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 0

    # All above threshold -> allow
    bars_high = {"energy": torch.tensor([0.5, 0.8])}
    manager.spawn_initial_items(appearance, grid_size=(3, 3), current_tick=0, bars=bars_high)
    assert len(manager.active_items) == 1


def test_unknown_symbol_rejected_at_compile_time() -> None:
    rule = ItemAppearanceRuleConfig(
        item_type="apple",
        spawn_count=1,
        spawn_position="random",
        when="vfs.unknown_flag",
    )

    with pytest.raises(TypeCheckError):
        _compile_when(rule, {"bar.energy": "float"})


def test_missing_ast_raises_runtime_error() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=1,
                spawn_position="random",
                when="bar.energy > 0.5",
            )
        ]
    )

    manager = ItemManager(catalog=catalog, max_items=5, device="cpu")
    bars = {"energy": torch.tensor([0.9])}

    with pytest.raises(RuntimeError, match="compiled AST"):
        manager.spawn_initial_items(appearance, grid_size=(3, 3), current_tick=0, bars=bars)


def test_equality_and_inequality_operators() -> None:
    """Test == and != comparison operators."""
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))

    # Test == operator
    appearance_eq = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "placement": {"mode": "random"},
                "when": "vfs.mode == 1",
            }
        ]
    )
    rule_eq = appearance_eq.items[0]
    _compile_when(rule_eq, {"vfs.mode": "float", "bar.energy": "float"})

    class _DummyProfile:
        variables: tuple = ()

    registry = VariableRegistry(
        variables=[
            VariableDef(
                id="mode",
                scope=VariableScope.GLOBAL,
                type="scalar",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=0,
            )
        ],
        num_agents=1,
        device=torch.device("cpu"),
        max_items=5,
        item_profiles={"food": _DummyProfile()},
    )

    manager = ItemManager(catalog=catalog, max_items=5, device="cpu", vfs_registry=registry)
    bars = {"energy": torch.tensor([1.0])}

    # mode=0 -> no spawn
    registry._storage["mode"] = torch.tensor(0)
    manager.spawn_initial_items(appearance_eq, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 0

    # mode=1 -> spawn
    registry._storage["mode"] = torch.tensor(1)
    manager.spawn_initial_items(appearance_eq, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 1

    # Test != operator
    manager.active_items.clear()
    appearance_neq = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "placement": {"mode": "random"},
                "when": "vfs.mode != 0",
            }
        ]
    )
    rule_neq = appearance_neq.items[0]
    _compile_when(rule_neq, {"vfs.mode": "float", "bar.energy": "float"})

    # mode=0 -> no spawn
    registry._storage["mode"] = torch.tensor(0)
    manager.spawn_initial_items(appearance_neq, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 0

    # mode=2 -> spawn
    registry._storage["mode"] = torch.tensor(2)
    manager.spawn_initial_items(appearance_neq, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 1


def test_or_and_not_boolean_operators() -> None:
    """Test OR and NOT boolean logic."""
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))

    # Test OR operator
    appearance_or = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "placement": {"mode": "random"},
                "when": "vfs.is_day or vfs.is_special",
            }
        ]
    )
    rule_or = appearance_or.items[0]
    _compile_when(rule_or, {"vfs.is_day": "bool", "vfs.is_special": "bool", "bar.energy": "float"})

    class _DummyProfile:
        variables: tuple = ()

    registry = VariableRegistry(
        variables=[
            VariableDef(
                id="is_day",
                scope=VariableScope.GLOBAL,
                type="bool",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=False,
            ),
            VariableDef(
                id="is_special",
                scope=VariableScope.GLOBAL,
                type="bool",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=False,
            ),
        ],
        num_agents=1,
        device=torch.device("cpu"),
        max_items=5,
        item_profiles={"food": _DummyProfile()},
    )

    manager = ItemManager(catalog=catalog, max_items=5, device="cpu", vfs_registry=registry)
    bars = {"energy": torch.tensor([1.0])}

    # Both false -> no spawn
    registry._storage["is_day"] = torch.tensor(False)
    registry._storage["is_special"] = torch.tensor(False)
    manager.spawn_initial_items(appearance_or, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 0

    # One true -> spawn
    registry._storage["is_day"] = torch.tensor(True)
    manager.spawn_initial_items(appearance_or, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 1

    # Test NOT operator
    manager.active_items.clear()
    appearance_not = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "placement": {"mode": "random"},
                "when": "not vfs.is_day",
            }
        ]
    )
    rule_not = appearance_not.items[0]
    _compile_when(rule_not, {"vfs.is_day": "bool", "bar.energy": "float"})

    # is_day=True -> no spawn (because NOT)
    registry._storage["is_day"] = torch.tensor(True)
    manager.spawn_initial_items(appearance_not, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 0

    # is_day=False -> spawn
    registry._storage["is_day"] = torch.tensor(False)
    manager.spawn_initial_items(appearance_not, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 1


def test_less_than_operators() -> None:
    """Test < and <= comparison operators."""
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))

    # Test < operator
    appearance_lt = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "placement": {"mode": "random"},
                "when": "bar.energy < 0.3",
            }
        ]
    )
    rule_lt = appearance_lt.items[0]
    _compile_when(rule_lt, {"bar.energy": "float"})

    manager = ItemManager(catalog=catalog, max_items=5, device="cpu")

    # Above threshold -> no spawn
    bars_high = {"energy": torch.tensor([0.5])}
    manager.spawn_initial_items(appearance_lt, grid_size=(3, 3), current_tick=0, bars=bars_high)
    assert len(manager.active_items) == 0

    # Below threshold -> spawn
    bars_low = {"energy": torch.tensor([0.2])}
    manager.spawn_initial_items(appearance_lt, grid_size=(3, 3), current_tick=0, bars=bars_low)
    assert len(manager.active_items) == 1

    # Test <= operator
    manager.active_items.clear()
    appearance_lte = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "placement": {"mode": "random"},
                "when": "bar.energy <= 0.3",
            }
        ]
    )
    rule_lte = appearance_lte.items[0]
    _compile_when(rule_lte, {"bar.energy": "float"})

    # Equal to threshold -> spawn
    bars_equal = {"energy": torch.tensor([0.3])}
    manager.spawn_initial_items(appearance_lte, grid_size=(3, 3), current_tick=0, bars=bars_equal)
    assert len(manager.active_items) == 1


def test_unconditional_spawn_has_no_overhead() -> None:
    """Verify that spawns without conditions don't evaluate expressions."""
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))

    # Unconditional spawn rule (no when field)
    appearance = _appearance(
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "placement": {"mode": "random"},
                # No 'when' field
            }
        ]
    )

    manager = ItemManager(catalog=catalog, max_items=5, device="cpu")
    bars = {"energy": torch.tensor([0.5])}

    # Should spawn without evaluating any conditions
    manager.spawn_initial_items(appearance, grid_size=(3, 3), current_tick=0, bars=bars)
    assert len(manager.active_items) == 1

    # Verify when and when_ast are None
    assert appearance.items[0].when is None
    assert appearance.items[0].when_ast is None
