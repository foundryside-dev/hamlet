from pathlib import Path

import pytest
import torch

from tests.test_townlet.utils.builders import make_grid2d_substrate
from townlet.config.items_config import (
    ItemAppearanceRuleConfig,
    ItemsAppearanceConfig,
    ItemsCatalogConfig,
    SpawnPlacementConfig,
    SpawnScheduleConfig,
)
from townlet.items.manager import ItemManager


def _bars(val: float, count: int = 1) -> dict[str, torch.Tensor]:
    return {"energy": torch.tensor([val] * count)}


def _appearance(items):
    return ItemsAppearanceConfig(version="1.0", items=items)


def test_fixed_placement_spawns_at_given_positions() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=2,
                placement=SpawnPlacementConfig(mode="fixed", fixed_positions=[(0, 0), (1, 1), (10, 10)]),
            )
        ]
    )
    manager = ItemManager(
        catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(width=5, height=5), items_per_world=5, device="cpu"
    )
    manager.spawn_initial_items(appearance, current_tick=0, bars=_bars(1.0))
    positions = {item.position for item in manager.worlds[0].active.values()}
    assert (0, 0) in positions and (1, 1) in positions
    assert (10, 10) not in positions  # OOB skipped


def test_grid_placement_respects_spacing_and_count() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=3,
                placement=SpawnPlacementConfig(mode="grid", grid_spacing=2),
            )
        ]
    )
    manager = ItemManager(
        catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(width=5, height=5), items_per_world=5, device="cpu"
    )
    manager.spawn_initial_items(appearance, current_tick=0, bars=_bars(1.0))
    positions = [item.position for item in manager.worlds[0].active.values()]
    assert len(positions) == 3
    assert positions[0] == (0, 0)
    assert positions[1] == (0, 2)
    assert positions[2] == (0, 4)


def test_scripted_initial_spawns_only_matching_tick() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    script = [{"tick": 1, "position": (0, 0)}, {"tick": 2, "position": (1, 1)}]
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=2,
                placement=SpawnPlacementConfig(mode="scripted", script=script),
            )
        ]
    )
    manager = ItemManager(
        catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(width=3, height=3), items_per_world=5, device="cpu"
    )
    manager.spawn_initial_items(appearance, current_tick=0, bars=_bars(1.0))
    assert len(manager.worlds[0].active) == 0

    manager.spawn_initial_items(appearance, current_tick=1, bars=_bars(1.0))
    assert len(manager.worlds[0].active) == 1
    assert next(iter(manager.worlds[0].active.values())).position == (0, 0)


def test_time_window_gates_initial_spawn() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=1,
                schedule=SpawnScheduleConfig(type="time_window", start_tick=5, end_tick=10),
            )
        ]
    )
    manager = ItemManager(
        catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(width=3, height=3), items_per_world=5, device="cpu"
    )
    manager.spawn_initial_items(appearance, current_tick=0, bars=_bars(1.0))
    assert len(manager.worlds[0].active) == 0
    manager.spawn_initial_items(appearance, current_tick=6, bars=_bars(1.0))
    assert len(manager.worlds[0].active) == 1


def test_poisson_respawn_probabilistic_gate() -> None:
    torch.manual_seed(0)
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=1,
                schedule=SpawnScheduleConfig(type="poisson", rate=10.0),
            )
        ]
    )
    manager = ItemManager(
        catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(width=3, height=3), items_per_world=5, device="cpu"
    )
    manager.set_appearance_config(appearance)
    manager.worlds[0].respawn_timers["apple"] = 0
    manager.process_respawns(current_tick=0, bars=_bars(1.0))
    assert len(manager.worlds[0].active) == 1


def test_normal_respawn_samples_future_tick() -> None:
    torch.manual_seed(0)
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=1,
                schedule=SpawnScheduleConfig(type="normal", mean=1.0, std_dev=0.01),
            )
        ]
    )
    manager = ItemManager(
        catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(width=3, height=3), items_per_world=5, device="cpu"
    )
    manager.set_appearance_config(appearance)
    manager.worlds[0].respawn_timers["apple"] = 0
    manager.process_respawns(current_tick=0, bars=_bars(1.0))
    # normal mean=1 should schedule around tick 1, so not yet
    assert len(manager.worlds[0].active) == 0
    spawned = False
    for tick in (1, 2, 3):
        manager.process_respawns(current_tick=tick, bars=_bars(1.0))
        if len(manager.worlds[0].active) > 0:
            spawned = True
            break
    assert spawned


def test_max_total_caps_spawns() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=3,
                max_total=1,
                placement=SpawnPlacementConfig(mode="fixed", fixed_positions=[(0, 0), (1, 1), (2, 2)]),
            )
        ]
    )
    manager = ItemManager(
        catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(width=3, height=3), items_per_world=5, device="cpu"
    )
    manager.spawn_initial_items(appearance, current_tick=0, bars=_bars(1.0))
    assert len(manager.worlds[0].active) == 1


def test_time_window_respawn_stops_after_end() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=1,
                schedule=SpawnScheduleConfig(type="time_window", start_tick=1, end_tick=2),
            )
        ]
    )
    manager = ItemManager(
        catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(width=3, height=3), items_per_world=5, device="cpu"
    )
    manager.set_appearance_config(appearance)
    manager.worlds[0].respawn_timers["apple"] = 0
    manager.process_respawns(current_tick=0, bars=_bars(1.0))
    # before window
    assert len(manager.worlds[0].active) == 0
    manager.process_respawns(current_tick=1, bars=_bars(1.0))
    assert len(manager.worlds[0].active) == 1
    # after window should clear timer and not spawn more
    manager.process_respawns(current_tick=3, bars=_bars(1.0))
    assert len(manager.worlds[0].active) == 1


def test_scripted_respawn_consumes_events_by_tick() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    script = [{"tick": 1, "position": (0, 0)}, {"tick": 2, "position": (1, 1)}]
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=1,
                placement=SpawnPlacementConfig(mode="scripted", script=script),
                schedule=SpawnScheduleConfig(type="time_window", start_tick=0, end_tick=5),
            )
        ]
    )
    manager = ItemManager(
        catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(width=3, height=3), items_per_world=5, device="cpu"
    )
    manager.set_appearance_config(appearance)
    manager.worlds[0].respawn_timers["apple"] = 1
    manager.process_respawns(current_tick=1, bars=_bars(1.0))
    assert len(manager.worlds[0].active) == 1
    assert next(iter(manager.worlds[0].active.values())).position == (0, 0)
    manager.process_respawns(current_tick=2, bars=_bars(1.0))
    positions = {item.position for item in manager.worlds[0].active.values()}
    assert (1, 1) in positions


def test_fixed_placement_skips_occupied_cells() -> None:
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=2,
                placement=SpawnPlacementConfig(mode="fixed", fixed_positions=[(0, 0), (0, 0), (1, 1)]),
            )
        ]
    )
    manager = ItemManager(
        catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(width=3, height=3), items_per_world=5, device="cpu"
    )
    # Occupy (0,0)
    manager.spawn_item(0, "apple", position=(0, 0), current_tick=0)
    manager.spawn_initial_items(appearance, current_tick=0, bars=_bars(1.0))
    positions = {item.position for item in manager.worlds[0].active.values()}
    assert positions == {(0, 0), (1, 1)}


def test_fixed_placement_off_the_grid_is_an_invariant_violation() -> None:
    """The compiler refuses an off-grid authored cell; reaching the runtime with one raises."""
    catalog = ItemsCatalogConfig.from_yaml(path=Path("configs/test/items_smoke/items.yaml"))
    appearance = _appearance(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=1,
                placement=SpawnPlacementConfig(mode="fixed", fixed_positions=[(10, 10)]),
            )
        ]
    )
    manager = ItemManager(
        catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(width=3, height=3), items_per_world=5, device="cpu"
    )
    with pytest.raises(ValueError, match="not a cell of the substrate"):
        manager.spawn_initial_items(appearance, current_tick=0, bars=_bars(1.0))
