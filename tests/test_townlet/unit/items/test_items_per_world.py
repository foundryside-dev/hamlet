"""Items are per world (owner ruling S1, 2026-10-25: the batch is N independent worlds).

One `ItemManager` used to serve every world: a pickup in world 0 hid an exclusive item
from every world, and spawn positions, capacity, respawn timers and item-scope state were
all shared. Each world now owns its own item lifecycle (`WorldItemState`) and its own block
of the flat item arena (row = world * items_per_world + slot). Also covered here, absorbed
by the same change: items spawn on continuous substrates, a carried item publishes a
token and a state row at its holder's position, and grid-cell placements are checked
against the substrate at compile time.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
import yaml

from tests.test_townlet.helpers.config_builder import copy_config_pack
from tests.test_townlet.utils.builders import make_grid2d_substrate, make_vectorized_env_from_pack
from townlet.config.items_config import (
    ItemAppearanceRuleConfig,
    ItemInteractionsConfig,
    ItemsAppearanceConfig,
    ItemsCatalogConfig,
    ItemTypeConfig,
    SpawnPlacementConfig,
    SpawnScheduleConfig,
)
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.items.action_handlers import ItemActionHandler
from townlet.items.inventory import InventoryState
from townlet.items.manager import ItemManager
from townlet.substrate.continuous import ContinuousSubstrate
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError, CompilationErrorCollector
from townlet.universe.validation.semantics import _validate_item_placements
from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable
from townlet.vfs.registry import VariableRegistry
from townlet.world.expression import ExpressionParser

DEVICE = torch.device("cpu")
ITEMS_SMOKE = Path("configs/test/items_smoke")
LEVEL = "L0_smoke"


# --------------------------------------------------------------------------- fixtures


def _catalog(*, exclusive: bool = True, max_items_in_world: int = 3, max_items_per_agent: int = 1) -> ItemsCatalogConfig:
    return ItemsCatalogConfig(
        version="1.0",
        item_types=[
            ItemTypeConfig(
                id="gem",
                name="Gem",
                icon="g",
                tags=["gem"],
                exclusive=exclusive,
                vfs_profile="gem",
                interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
            )
        ],
        max_items_per_agent=max_items_per_agent,
        max_items_in_world=max_items_in_world,
    )


def _registry(num_worlds: int, items_per_world: int) -> VariableRegistry:
    profile = CompiledItemProfile(
        profile_name="gem",
        variables=[
            CompiledVariable(
                readable_by=("engine", "agent"),
                writable_by=("engine",),
                name="shine",
                lifetime="episode",
                type="float",
                ast=None,
                initial_value=1.0,
                result_type="float",
                exposed_to=("agent",),
            )
        ],
    )
    return VariableRegistry([], num_worlds, DEVICE, items_per_world=items_per_world, item_profiles={"gem": profile})


def _manager(*, num_worlds: int = 2, items_per_world: int = 4, registry: VariableRegistry | None = None, substrate=None, **catalog):
    return ItemManager(
        catalog=_catalog(**catalog),
        items_per_world=items_per_world,
        num_worlds=num_worlds,
        substrate=substrate if substrate is not None else make_grid2d_substrate(width=5, height=5),
        device=DEVICE,
        vfs_registry=registry,
    )


def _handler(manager: ItemManager) -> tuple[ItemActionHandler, InventoryState]:
    inventory = InventoryState(batch_size=manager.num_worlds, max_items_per_agent=1, device="cpu")
    manager.inventory = inventory
    handler = ItemActionHandler(
        manager=manager,
        inventory=inventory,
        command_executor=CommandExecutor(),
        vfs_registry=manager.vfs_registry,
        meter_name_to_index={},
    )
    return handler, inventory


def _appearance(**rule) -> ItemsAppearanceConfig:
    return ItemsAppearanceConfig(version="1.0", items=[ItemAppearanceRuleConfig(item_type="gem", **rule)])


def _row_of(env, obs: torch.Tensor, type_name: str, slot_index: int, world: int) -> list[float]:
    for name, slot, start, end in env.token_spec.row_layout():
        if name == type_name and slot == slot_index:
            return obs[world, start:end].tolist()
    raise KeyError((type_name, slot_index))


def _element_row(env, obs: torch.Tensor, filler_ref: str, world: int) -> list[float]:
    element_type = env.token_spec.get_type("variable_element")
    for name, slot, start, end in env.token_spec.row_layout():
        if name == "variable_element" and element_type.slot_bindings[slot].filler_ref == filler_ref:
            return obs[world, start:end].tolist()
    raise KeyError(filler_ref)


def _lane(env, type_name: str, feature: str) -> int:
    layout = next(t for t in env.token_spec.compact_layout().types if t.type_name == type_name)
    return layout.dynamic_features.index(feature)


# --------------------------------------------------------------------------- pickup


def test_world_0_picking_up_an_exclusive_item_leaves_world_1s_item_on_the_ground() -> None:
    manager = _manager()
    handler, inventory = _handler(manager)
    gem0 = manager.spawn_item(0, "gem", (2, 2), current_tick=0)
    gem1 = manager.spawn_item(1, "gem", (2, 2), current_tick=0)
    assert gem0 is not None and gem1 is not None
    here = torch.tensor([2, 2])

    assert handler.handle_get_action(agent_idx=0, agent_position=here, current_tick=0, meters=torch.zeros((2, 0))) is True
    assert inventory.has_item(0, gem0.instance_id)
    assert manager.worlds[0].active == {} and manager.worlds[0].held == {gem0.instance_id: gem0}
    # World 1's own gem is untouched and still on its ground, so world 1's agent can take it.
    assert manager.worlds[1].active == {gem1.instance_id: gem1}
    assert manager.items_at(1, here) == [gem1]
    assert handler.handle_get_action(agent_idx=1, agent_position=here, current_tick=0, meters=torch.zeros((2, 0))) is True
    assert inventory.has_item(1, gem1.instance_id) and not inventory.has_item(1, gem0.instance_id)


def test_every_world_spawns_its_own_level_start_items() -> None:
    env = make_vectorized_env_from_pack(ITEMS_SMOKE, level_name=LEVEL, num_agents=3, device=DEVICE)
    env.reset()
    per_world = [sorted(item.item_type for item in env.item_manager.items_in_world(world)) for world in range(3)]
    assert per_world[0] == ["apple", "apple", "apple", "medkit"]
    assert per_world[1] == per_world[0] and per_world[2] == per_world[0]
    for world in range(3):
        rows = [item.vfs_index for item in env.item_manager.items_in_world(world)]
        assert all(env.vfs_registry.item_world(row) == world for row in rows)


# --------------------------------------------------------------------------- lifecycle


def test_spawning_capacity_and_arena_rows_are_per_world() -> None:
    manager = _manager(items_per_world=2)
    assert manager.spawn_item(0, "gem", (0, 0), 0) is not None
    assert manager.spawn_item(0, "gem", (1, 0), 0) is not None
    assert manager.spawn_item(0, "gem", (2, 0), 0) is None  # world 0 is at capacity
    second = manager.spawn_item(1, "gem", (0, 0), 0)  # world 1 is not
    assert second is not None
    assert sorted(item.vfs_index for item in manager.items_in_world(0)) == [0, 1]
    assert second.vfs_index == 2  # world 1's block starts at items_per_world


def test_respawn_timers_are_per_world() -> None:
    manager = _manager(items_per_world=2)
    appearance = _appearance(
        spawn_count=1, placement=SpawnPlacementConfig(mode="random"), schedule=SpawnScheduleConfig(type="periodic", period=5)
    )
    manager.spawn_initial_items(appearance, current_tick=0)
    assert [len(manager.items_in_world(world)) for world in range(2)] == [1, 1]

    (gem0,) = manager.items_in_world(0)
    manager.despawn_item(gem0.instance_id, current_tick=1)
    assert manager.worlds[0].respawn_timers == {"gem": 6}
    assert manager.worlds[1].respawn_timers == {}

    manager.process_respawns(6)
    assert [len(manager.items_in_world(world)) for world in range(2)] == [1, 1]
    assert manager.worlds[0].rule_spawn_counts == {"rule_0_gem": 2}
    assert manager.worlds[1].rule_spawn_counts == {"rule_0_gem": 1}


def test_cooldowns_are_per_world() -> None:
    catalog = _catalog()
    catalog.item_types[0].cooldown = 10
    manager = ItemManager(catalog=catalog, items_per_world=4, num_worlds=2, substrate=make_grid2d_substrate(), device=DEVICE)
    gem = manager.spawn_item(0, "gem", (0, 0), 0)
    assert gem is not None
    manager.despawn_item(gem.instance_id, current_tick=1)
    assert manager.spawn_item(0, "gem", (0, 0), 2) is None  # world 0 cools down
    assert manager.spawn_item(1, "gem", (0, 0), 2) is not None  # world 1 never despawned one


def test_a_rejected_spawn_predicate_arms_the_timer_only_in_the_rejecting_world() -> None:
    manager = _manager(items_per_world=2)
    appearance = _appearance(
        spawn_count=1,
        placement=SpawnPlacementConfig(mode="random"),
        schedule=SpawnScheduleConfig(type="periodic", period=3),
        when="bar.energy > 0.5",
    )
    appearance.items[0].when_ast = ExpressionParser().parse("bar.energy > 0.5")
    manager.spawn_initial_items(appearance, current_tick=0, bars={"energy": torch.tensor([0.9, 0.1])})
    assert [len(manager.items_in_world(world)) for world in range(2)] == [1, 0]
    assert manager.worlds[0].respawn_timers == {}
    assert manager.worlds[1].respawn_timers == {"gem": 3}

    manager.process_respawns(3, bars={"energy": torch.tensor([0.1, 0.9])})
    assert [len(manager.items_in_world(world)) for world in range(2)] == [1, 1]


# --------------------------------------------------------------------------- item-scope state and effects


def test_item_scope_state_is_per_world() -> None:
    registry = _registry(num_worlds=2, items_per_world=4)
    manager = _manager(items_per_world=4, registry=registry)
    gem0 = manager.spawn_item(0, "gem", (0, 0), 0, initial_state={"shine": 0.25})
    gem1 = manager.spawn_item(1, "gem", (0, 0), 0)
    assert gem0 is not None and gem1 is not None
    assert registry.item_vfs is not None and tuple(registry.item_vfs.shape) == (8, 1)
    assert (registry.item_world(gem0.vfs_index), registry.item_world(gem1.vfs_index)) == (0, 1)
    assert registry.read_item("gem", "shine", gem0.vfs_index, reader="engine") == pytest.approx(0.25)
    assert registry.read_item("gem", "shine", gem1.vfs_index, reader="engine") == pytest.approx(1.0)

    manager.despawn_item(gem0.instance_id, current_tick=1)
    assert registry.get_item_profile_for_index(gem0.vfs_index) is None
    assert registry.get_item_profile_for_index(gem1.vfs_index) == "gem"


def test_an_item_write_in_world_0_never_touches_world_1() -> None:
    registry = _registry(num_worlds=2, items_per_world=4)
    manager = _manager(items_per_world=4, registry=registry)
    gem0 = manager.spawn_item(0, "gem", (0, 0), 0)
    gem1 = manager.spawn_item(1, "gem", (0, 0), 0)
    assert gem0 is not None and gem1 is not None
    context = ExecutionContext(vfs_registry=registry, self_index=gem0.vfs_index, self_is_item=True, item_manager=manager)
    assert context.world_row() == 0
    context.set_path("self.vfs.shine", torch.tensor(0.5))
    assert registry.read_item("gem", "shine", gem0.vfs_index, reader="engine") == pytest.approx(0.5)
    assert registry.read_item("gem", "shine", gem1.vfs_index, reader="engine") == pytest.approx(1.0)

    # A per-agent condition gates an item's write by the item's own world, not the batch:
    # world 0 masked out skips world 0's item; world 1 live writes world 1's item.
    mask = torch.tensor([False, True])
    context.copy(write_mask=mask).set_path("self.vfs.shine", torch.tensor(0.0))
    assert registry.read_item("gem", "shine", gem0.vfs_index, reader="engine") == pytest.approx(0.5)
    context.copy(self_index=gem1.vfs_index, write_mask=mask).set_path("self.vfs.shine", torch.tensor(0.0))
    assert registry.read_item("gem", "shine", gem1.vfs_index, reader="engine") == pytest.approx(0.0)


def test_spawn_item_from_an_item_context_lands_in_that_items_world() -> None:
    registry = _registry(num_worlds=2, items_per_world=4)
    manager = _manager(items_per_world=4, registry=registry)
    gem1 = manager.spawn_item(1, "gem", (3, 1), 0)
    assert gem1 is not None
    context = ExecutionContext(vfs_registry=registry, self_index=gem1.vfs_index, self_is_item=True, item_manager=manager)
    CommandExecutor().execute(CommandNode(type=CommandType.SPAWN_ITEM, item_type="gem", position="self", quantity=1), context)
    assert manager.items_in_world(0) == []
    assert [item.position for item in manager.items_in_world(1)] == [(3, 1), (3, 1)]


def test_an_item_effect_in_world_0_never_touches_world_1(tmp_path: Path) -> None:
    env = make_vectorized_env_from_pack(ITEMS_SMOKE, level_name=LEVEL, num_agents=2, device=DEVICE)
    env.reset()
    medkits = [env.item_manager.spawn_item(world, "medkit", (4, 4), current_tick=0) for world in range(2)]
    assert all(medkit is not None for medkit in medkits)
    rows = [medkit.vfs_index for medkit in medkits]
    durability = [env.vfs_registry.read_item("medical", "durability", row, reader="engine") for row in rows]
    env.effect_manager.spawn_effect(
        "wear_and_tear",
        rows[0],
        1.0,
        env.global_tick,
        bars=env.bars,
        vfs_registry=env.vfs_registry,
        item_manager=env.item_manager,
    )
    wait = next(i for i, action in enumerate(env.action_space.actions) if action.name == "WAIT")
    obs, *_ = env.step(torch.tensor([wait, wait]))
    after = [env.vfs_registry.read_item("medical", "durability", row, reader="engine") for row in rows]
    assert after[0] < durability[0]
    assert after[1] == pytest.approx(durability[1])

    # The effect is observable in the item's own world only.
    present = [0.0, 0.0]
    for name, _slot, start, _end in env.token_spec.row_layout():
        if name == "effect":
            for world in range(2):
                present[world] += float(obs[world, start])
    assert present[0] >= 1.0
    assert present[1] == 0.0


# --------------------------------------------------------------------------- carried items in the observation


def _carry(env, item_type: str, world: int, position: tuple[int, int]):
    item = env.item_manager.spawn_item(world, item_type, position, current_tick=0)
    assert item is not None
    env.positions[world] = torch.tensor(position, dtype=env.positions.dtype)
    assert env.item_handler.handle_get_action(agent_idx=world, agent_position=env.positions[world], current_tick=0, meters=env.meters)
    return item


def test_a_carried_exclusive_item_has_a_token_and_a_state_row_at_its_holder() -> None:
    env = make_vectorized_env_from_pack(ITEMS_SMOKE, level_name=LEVEL, num_agents=2, device=DEVICE)
    env.reset()
    medkit = _carry(env, "medkit", world=0, position=(1, 1))
    assert medkit.instance_id in env.item_manager.worlds[0].held
    env.positions[0] = torch.tensor([3, 2], dtype=env.positions.dtype)  # the holder walks off
    obs = env._get_observations()

    slot = medkit.vfs_index  # world 0: slot = row
    row = _row_of(env, obs, "item", slot, world=0)
    assert row[0] == 1.0
    assert row[_lane(env, "item", "carried")] == 1.0
    assert row[_lane(env, "item", "owner_slot_applicable")] == 1.0
    pos0 = _lane(env, "item", "position_0")
    assert row[pos0 : pos0 + 2] == pytest.approx([3 / 4, 2 / 4])  # the holder's cell on the 5x5 grid
    state = _element_row(env, obs, f"medical.durability[{slot}]", world=0)
    assert state[0] == 1.0
    # World 1 owns no item at that slot unless it spawned one there itself.
    world1_rows = {item.vfs_index - env.items_per_world for item in env.item_manager.items_in_world(1)}
    if slot not in world1_rows:
        assert _row_of(env, obs, "item", slot, world=1)[0] == 0.0


def test_a_shared_carried_item_reports_its_holders_position() -> None:
    env = make_vectorized_env_from_pack(ITEMS_SMOKE, level_name=LEVEL, num_agents=2, device=DEVICE)
    env.reset()
    for item_type in env.item_manager.catalog.item_types:
        item_type.exclusive = False
    coin = _carry(env, "coin", world=1, position=(0, 4))
    assert coin.instance_id in env.item_manager.worlds[1].active  # shared: stays on the ground
    env.positions[1] = torch.tensor([4, 0], dtype=env.positions.dtype)
    obs = env._get_observations()

    slot = coin.vfs_index - env.items_per_world
    row = _row_of(env, obs, "item", slot, world=1)
    assert row[0] == 1.0 and row[_lane(env, "item", "carried")] == 1.0
    pos0 = _lane(env, "item", "position_0")
    assert row[pos0 : pos0 + 2] == pytest.approx([1.0, 0.0])  # the holder's (4, 0), not the ground (0, 4)


# --------------------------------------------------------------------------- substrates


def _continuous() -> ContinuousSubstrate:
    return ContinuousSubstrate(
        dimensions=2,
        bounds=[(0.0, 10.0), (0.0, 10.0)],
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=0.75,
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
        distance_metric="euclidean",
    )


def test_items_spawn_and_are_picked_up_on_a_continuous_substrate() -> None:
    manager = _manager(substrate=_continuous(), items_per_world=4)
    handler, inventory = _handler(manager)
    manager.spawn_initial_items(_appearance(spawn_count=3, placement=SpawnPlacementConfig(mode="random")), current_tick=0)
    for world in range(2):
        items = manager.items_in_world(world)
        assert len(items) == 3
        for item in items:
            assert all(isinstance(c, float) and 0.0 <= c <= 10.0 for c in item.position)

    target = manager.items_in_world(0)[0]
    near = torch.tensor(target.position) + torch.tensor([0.3, 0.3])  # inside the interaction radius
    assert target in manager.items_at(0, near)
    assert handler.handle_get_action(agent_idx=0, agent_position=near, current_tick=0, meters=torch.zeros((2, 0))) is True
    assert inventory.count_items(0) == 1


def _pack_with_apple_placement(tmp_path: Path, placement: dict) -> Path:
    pack = copy_config_pack(ITEMS_SMOKE, tmp_path, name="items_placement")
    items_path = pack / "levels" / LEVEL / "items.yaml"
    data = yaml.safe_load(items_path.read_text())
    for rule in data["items"]:
        if rule["item_type"] == "apple":
            rule["placement"] = placement
            rule["spawn_count"] = 1
    items_path.write_text(yaml.safe_dump(data, sort_keys=False))
    return pack


@pytest.mark.parametrize(
    "placement",
    [
        {"mode": "fixed", "fixed_positions": [[1, 1, 1]]},  # rank 3 on a 2-D grid
        {"mode": "fixed", "fixed_positions": [[5, 0]]},  # off the 5x5 grid
        {"mode": "scripted", "script": [{"tick": 0, "position": [0, 9]}]},
    ],
)
def test_a_placement_cell_that_is_not_a_grid_cell_refuses_at_compile(tmp_path: Path, placement: dict) -> None:
    with pytest.raises(CompilationError, match="ITEM-PLACEMENT-SUBSTRATE"):
        UniverseCompiler().compile(_pack_with_apple_placement(tmp_path, placement), primary_level=LEVEL)


def test_a_fixed_cell_inside_the_grid_compiles_and_spawns_there_in_every_world(tmp_path: Path) -> None:
    pack = _pack_with_apple_placement(tmp_path, {"mode": "fixed", "fixed_positions": [[4, 3]]})
    env = make_vectorized_env_from_pack(pack, level_name=LEVEL, num_agents=2, device=DEVICE)
    env.reset()
    for world in range(2):
        apples = [item.position for item in env.item_manager.items_in_world(world) if item.item_type == "apple"]
        assert apples == [(4, 3)]


@pytest.mark.parametrize("substrate_type", ["continuous", "continuousnd", "aspatial"])
@pytest.mark.parametrize("mode", ["fixed", "grid", "scripted"])
def test_a_grid_cell_placement_on_a_non_grid_substrate_refuses(substrate_type: str, mode: str) -> None:
    """fixed / grid / scripted name grid cells; only `random` (the substrate's own
    position initialization) places items on continuous and aspatial substrates."""
    placement = SpawnPlacementConfig(mode=mode, fixed_positions=[(0, 0)] if mode == "fixed" else None, grid_spacing=1)
    appearance = _appearance(spawn_count=1, placement=placement)
    substrate = SimpleNamespace(type=substrate_type, grid=None, gridnd=None)
    raw = SimpleNamespace(
        stratum=SimpleNamespace(stratum=SimpleNamespace(substrate=substrate)),
        levels={LEVEL: SimpleNamespace(items_appearance=appearance)},
    )
    errors = CompilationErrorCollector(stage="test")
    _validate_item_placements(raw, Path("pack"), None, errors)
    with pytest.raises(CompilationError, match="ITEM-PLACEMENT-SUBSTRATE"):
        errors.check_and_raise()

    random_only = _appearance(spawn_count=1, placement=SpawnPlacementConfig(mode="random"))
    raw.levels[LEVEL].items_appearance = random_only
    errors = CompilationErrorCollector(stage="test")
    _validate_item_placements(raw, Path("pack"), None, errors)
    errors.check_and_raise()
