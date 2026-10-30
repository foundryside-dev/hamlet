"""WP11 (VFS round-2 F3): item-state rows share the item token's visibility mask.

Under `active_vision: partial` the `item` token zeroes presence and payload for an
item outside the observer's range, but the item-state `variable_element` companion
rows used to publish presence 1 with the live value regardless — a POMDP leak: the
policy could see that an item exists in a slot, and its state, while the item itself
was hidden. Both publishers now consume ONE per-slot mask
(`token_publishers.item_slot_visibility`), so a state row is present exactly when its
owner item token is present, per observer world. Converted from
`review-2026-10-24/vfs_round2/r3_item_state_vision_leak.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch
import yaml

from tests.test_townlet.helpers.config_builder import copy_config_pack, mutate_stratum_yaml
from tests.test_townlet.unit.environment.test_token_publishers import (
    _BOUNDED,
    _dynamic_type,
    _item_batch,
    _item_profile_registry,
    _lane,
    _layout,
    _rows,
    _variable_type,
)
from tests.test_townlet.utils.builders import make_vectorized_env_from_pack
from townlet.environment.token_publishers import (
    ItemArenaVariableElementPublisher,
    ItemStateSlotDeclaration,
    ItemTokenPublisher,
    TokenPublishContext,
    item_slot_visibility,
)
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.universe.dto.token_spec import SlotBinding
from townlet.vfs.schema import VariableScope

DEVICE = torch.device("cpu")
ITEMS_SMOKE = Path("configs/test/items_smoke")
LEVEL = "L0_smoke"
# 8x8 grid: radius = max(1, ceil(0.2 * 8 / 2)) = 1 cell (manhattan).
VISION_RANGE = 0.2


# --------------------------------------------------------------------------- unit level


def _substrate() -> Grid2DSubstrate:
    return Grid2DSubstrate(width=8, height=8, boundary="clamp", distance_metric="manhattan")


def _publishers(capacity: int = 2):
    """An `item` publisher and an item-state publisher over the same owner slots:
    state slot i exposes `food.nutrition` of the item in owner slot i."""
    registry = _item_profile_registry()
    item_schema = _dynamic_type("item", capacity)
    item_publisher = ItemTokenPublisher(item_schema, _layout(item_schema), _substrate(), owner_slot_capacity=2)
    bindings = [
        SlotBinding(slot_index=i, filler_kind="static", filler_ref=f"food.nutrition[{i}]", scope=VariableScope.ITEM)
        for i in range(capacity)
    ]
    declarations = [ItemStateSlotDeclaration(slot_index=i, owner_slot=i, normalization=_BOUNDED) for i in range(capacity)]
    state_schema = _variable_type(bindings)
    state_publisher = ItemArenaVariableElementPublisher(
        state_schema,
        _layout(state_schema),
        registry,
        declarations,
        owner_capacity=capacity,
        substrate=_substrate(),
        device=DEVICE,
    )
    return registry, item_publisher, item_schema, state_publisher, state_schema


def _publish_both(ctx: TokenPublishContext, capacity: int = 2):
    registry, item_publisher, item_schema, state_publisher, state_schema = _publishers(capacity)
    registry.register_item_instance(0, "food")
    registry.write_item("food", "nutrition", 0.75, vfs_index=0, writer="engine")
    item_rows = _rows(item_schema.capacity, "item")
    state_rows = _rows(state_schema.capacity, "variable_element")
    item_publisher.publish(item_rows, ctx)
    state_publisher.publish(state_rows, ctx)
    return item_rows, state_rows


def test_hidden_item_hides_its_state_row_per_observer_world():
    # Item in owner slot 0 at (5, 5); world 0 adjacent (in range), world 1 far (out).
    batch = _item_batch([0], [[5, 5]], [0], [[False], [False]], [-1])
    ctx = TokenPublishContext(positions=torch.tensor([[5, 4], [0, 0]]), item_slots=batch, vision_range=VISION_RANGE)
    item_rows, state_rows = _publish_both(ctx)

    assert item_rows[:, 0, 0].tolist() == [1.0, 0.0]
    assert state_rows[:, 0, 0].tolist() == [1.0, 0.0]
    v0 = _lane("variable_element", "value_0")
    assert state_rows[0, 0, v0].item() == pytest.approx(0.75)  # seen: live value
    assert state_rows[1, 0].abs().sum().item() == 0.0  # hidden: presence 0 AND payload 0
    # Slot 1 has no item: absent for every world in both publishers.
    assert item_rows[:, 1].abs().sum().item() == 0.0
    assert state_rows[:, 1].abs().sum().item() == 0.0


def test_carried_item_is_visible_to_its_carrier_world_only():
    # Stored position far from both observers; world 0's agent carries it.
    batch = _item_batch([0], [[7, 7]], [0], [[True], [False]], [1])
    ctx = TokenPublishContext(positions=torch.tensor([[0, 0], [0, 0]]), item_slots=batch, vision_range=VISION_RANGE)
    item_rows, state_rows = _publish_both(ctx)

    assert item_rows[:, 0, 0].tolist() == [1.0, 0.0]
    assert state_rows[:, 0, 0].tolist() == [1.0, 0.0]
    assert state_rows[1, 0].abs().sum().item() == 0.0


def test_full_observability_is_unchanged():
    # No vision filter: every live slot is present in every world and the state
    # publisher needs no observer positions at all.
    batch = _item_batch([0], [[7, 7]], [0], [[False], [False]], [-1])
    ctx = TokenPublishContext(positions=torch.tensor([[0, 0], [0, 0]]), item_slots=batch, vision_range=None)
    item_rows, state_rows = _publish_both(ctx)
    assert item_rows[:, 0, 0].tolist() == [1.0, 1.0]
    assert state_rows[:, 0, 0].tolist() == [1.0, 1.0]
    v0 = _lane("variable_element", "value_0")
    assert state_rows[:, 0, v0].tolist() == pytest.approx([0.75, 0.75])

    registry, _, _, state_publisher, state_schema = _publishers()
    registry.register_item_instance(0, "food")
    rows = _rows(state_schema.capacity, "variable_element")
    state_publisher.publish(rows, TokenPublishContext(item_slots=batch))  # positions None is legal here
    assert rows[:, 0, 0].tolist() == [1.0, 1.0]


def test_partial_vision_requires_observer_positions():
    batch = _item_batch([0], [[7, 7]], [0], [[False], [False]], [-1])
    with pytest.raises(ValueError, match="item_slot_visibility requires TokenPublishContext.positions"):
        item_slot_visibility(_substrate(), TokenPublishContext(item_slots=batch, vision_range=VISION_RANGE), batch)


def test_state_presence_equals_item_presence_for_every_slot_and_world():
    """The invariant the fix buys, swept over random placements: the two publishers
    cannot drift because they read one mask."""
    generator = torch.Generator().manual_seed(0)
    for _ in range(25):
        item_positions = torch.randint(0, 8, (2, 2), generator=generator)
        observer_positions = torch.randint(0, 8, (3, 2), generator=generator)
        carried = torch.rand((3, 2), generator=generator) < 0.3
        batch = _item_batch([0, 1], item_positions.tolist(), [0, 1], carried.tolist(), [-1, -1])
        ctx = TokenPublishContext(positions=observer_positions, item_slots=batch, vision_range=VISION_RANGE)
        registry, item_publisher, item_schema, state_publisher, state_schema = _publishers()
        for vfs_index in (0, 1):
            registry.register_item_instance(vfs_index, "food")
            registry.write_item("food", "nutrition", 0.5, vfs_index=vfs_index, writer="engine")
        item_rows = _rows(item_schema.capacity, "item", batch=3)
        state_rows = _rows(state_schema.capacity, "variable_element", batch=3)
        item_publisher.publish(item_rows, ctx)
        state_publisher.publish(state_rows, ctx)
        expected = item_slot_visibility(_substrate(), ctx, batch).to(dtype=torch.float32)
        assert torch.equal(item_rows[:, :, 0], expected)
        assert torch.equal(state_rows[:, :, 0], expected)
        hidden = state_rows[:, :, 0] == 0.0
        assert state_rows[hidden].abs().sum().item() == 0.0


# --------------------------------------------------------------------------- env level (r3)


def _element_row(env, obs: torch.Tensor, filler_ref: str, world: int) -> list[float]:
    spec = env.token_spec
    element_type = spec.get_type("variable_element")
    for type_name, slot, start, end in spec.row_layout():
        if type_name == "variable_element" and element_type.slot_bindings[slot].filler_ref == filler_ref:
            return obs[world, start:end].tolist()
    raise KeyError(filler_ref)


def _item_row(env, obs: torch.Tensor, slot_index: int, world: int) -> list[float]:
    for type_name, slot, start, end in env.token_spec.row_layout():
        if type_name == "item" and slot == slot_index:
            return obs[world, start:end].tolist()
    raise KeyError(slot_index)


def _partial_items_pack(tmp_path: Path) -> Path:
    pack = copy_config_pack(ITEMS_SMOKE, tmp_path, name="items_partial")
    mutate_stratum_yaml(pack, lambda data: data["stratum"].update({"vision_support": "both"}))
    curriculum_yaml = pack / "levels" / LEVEL / "curriculum.yaml"
    data = yaml.safe_load(curriculum_yaml.read_text())
    data["curriculum"].update({"active_vision": "partial", "vision_range": VISION_RANGE})
    curriculum_yaml.write_text(yaml.safe_dump(data, sort_keys=False))
    return pack


def _spawn_medkit(env, position: tuple[int, int]):
    item = env.item_manager.spawn_item(item_type="medkit", position=position, current_tick=0)
    assert item is not None
    return item


def test_r3_item_state_row_follows_item_token_under_partial_vision(tmp_path: Path) -> None:
    # 5x5 grid, vision_range 0.2 => radius max(1, ceil(0.2 * 5 / 2)) = 1 cell.
    env = make_vectorized_env_from_pack(_partial_items_pack(tmp_path), level_name=LEVEL, num_agents=2, device=DEVICE)
    assert env.partial_observability is True
    env.reset()
    medkit = _spawn_medkit(env, (4, 4))
    env.positions[0] = torch.tensor([4, 3], dtype=env.positions.dtype)  # manhattan 1: in range
    env.positions[1] = torch.tensor([0, 0], dtype=env.positions.dtype)  # manhattan 8: hidden
    obs = env._get_observations()

    state_ref = f"medical.durability[{medkit.vfs_index}]"
    seen_item = _item_row(env, obs, medkit.vfs_index, world=0)
    hidden_item = _item_row(env, obs, medkit.vfs_index, world=1)
    seen_state = _element_row(env, obs, state_ref, world=0)
    hidden_state = _element_row(env, obs, state_ref, world=1)
    assert seen_item[0] == 1.0
    assert hidden_item[0] == 0.0
    assert seen_state[0] == 1.0
    assert seen_state[1] == pytest.approx(1.0)  # durability 100 / 100, minmax
    assert hidden_state == [0.0] * len(hidden_state)

    # The invariant over EVERY item slot and world: state presence never exceeds
    # item presence (the initial random spawns are included).
    element_type = env.token_spec.get_type("variable_element")
    for type_name, slot, start, end in env.token_spec.row_layout():
        if type_name != "variable_element" or element_type.slot_bindings[slot].scope != VariableScope.ITEM:
            continue
        owner_slot = int(element_type.slot_bindings[slot].filler_ref.rsplit("[", 1)[1].rstrip("]"))
        for world in range(env.num_agents):
            assert obs[world, start] <= _item_row(env, obs, owner_slot, world)[0]


def test_r3_full_observability_publishes_state_regardless_of_distance(tmp_path: Path) -> None:
    pack = copy_config_pack(ITEMS_SMOKE, tmp_path, name="items_global")
    env = make_vectorized_env_from_pack(pack, level_name=LEVEL, num_agents=2, device=DEVICE)
    assert env.partial_observability is False
    env.reset()
    medkit = _spawn_medkit(env, (4, 4))
    env.positions[0] = torch.tensor([4, 3], dtype=env.positions.dtype)
    env.positions[1] = torch.tensor([0, 0], dtype=env.positions.dtype)
    obs = env._get_observations()
    state_ref = f"medical.durability[{medkit.vfs_index}]"
    for world in range(2):
        assert _item_row(env, obs, medkit.vfs_index, world)[0] == 1.0
        row = _element_row(env, obs, state_ref, world)
        assert row[0] == 1.0
        assert row[1] == pytest.approx(1.0)
