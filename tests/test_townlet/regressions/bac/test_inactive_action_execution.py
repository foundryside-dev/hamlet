"""Completed action slots are transport, not permission to change a world."""

from pathlib import Path

import pytest
import torch
import yaml
from test_successor_producer import _environment as _producer_environment
from test_successor_producer import _write

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler


def _step(env: VectorizedHamletEnv, names: list[str]) -> tuple:
    actions = torch.tensor([env.action_space.get_action_by_name(name).id for name in names])
    active = ~env.dones
    selected_legal = env.get_action_masks().gather(1, actions.unsqueeze(1)).squeeze(1)
    assert selected_legal[active].all()  # Only completed transport slots bypass legality.
    result = env.step(actions)
    observations, _, dones, info = result
    assert torch.equal(observations, env._get_observations())
    assert torch.equal(info["successor_action_masks"], env.get_action_masks())
    assert not info["successor_action_masks"][dones].any()
    assert info["successor_action_masks"][~dones].any(dim=1).all()
    return result


def test_authored_terminal_drop_preserves_inventory(tmp_path: Path) -> None:
    env = _producer_environment(tmp_path, only_get=False, terminal=True, lifespan=5)
    _step(env, ["GET", "GET"])
    _, _, dones, terminal = _step(env, ["WAIT", "WAIT"])
    assert dones.tolist() == [True, False]
    assert terminal["newly_terminal"].tolist() == [True, False]
    assert env.item_inventory is not None
    inventory = env.item_inventory.slots.clone()
    assert (inventory != -1).all()
    _, rewards, _, info = _step(env, ["DROP_SLOT_0", "WAIT"])
    assert info["active_on_entry"].tolist() == [False, True]
    assert info["step_counts"].tolist() == [2, 3]
    assert rewards[0] == 0
    assert not info["newly_terminal"].any()
    assert torch.equal(env.item_inventory.slots, inventory)


def _environment(tmp_path: Path, *, spatial: bool, exclusive: bool, terminal: bool) -> VectorizedHamletEnv:
    _producer_environment(tmp_path, only_get=False, terminal=False, lifespan=6)
    pack = tmp_path / "successor_pack"
    items = yaml.safe_load((pack / "items.yaml").read_text())
    token = items["items"]["item_types"][0]
    token["exclusive"] = exclusive
    effect = [{"modify": "bar.money", "value": "bar.money + 1.0"}]
    token["interactions"]["on_use"] = effect
    token["interactions"]["inventory_commands"] = [{"name": "POLISH", "effects": effect}]
    token["interactions"]["local_commands"] = [{"name": "TOUCH", "effects": effect}]
    _write(pack / "items.yaml", items)
    training_path = pack / "levels" / "L0" / "training.yaml"
    training = yaml.safe_load(training_path.read_text())
    training["training"]["population"]["size"] = 4
    training["training"]["randomize_affordances"] = spatial
    _write(training_path, training)
    if spatial:
        stratum = yaml.safe_load((pack / "stratum.yaml").read_text())
        stratum["stratum"]["substrate"] = {
            "type": "grid",
            "grid": {
                "topology": "square",
                "width": 8,
                "height": 8,
                "boundary": "clamp",
                "distance_metric": "manhattan",
                "diagonals": False,
            },
        }
        _write(pack / "stratum.yaml", stratum)
        bars_path = pack / "levels" / "L0" / "bars.yaml"
        bars = yaml.safe_load(bars_path.read_text())
        bars["bars"]["meters"][1]["depletion"]["move"] = 0.1
        _write(bars_path, bars)
    if terminal:
        _write(
            pack / "transition_rules.yaml",
            {
                "version": "1.0",
                "transition_rules": [
                    {
                        "id": "authored_early_death",
                        "phase": "apply_transition_rules",
                        "condition": "(agent_id < 2) and (tick >= 1)",
                        "writes": [
                            {
                                "variable_id": "bar.energy",
                                "expression": "0.0",
                                "composition": "overwrite",
                                "condition": None,
                                "clamp": None,
                                "effect": None,
                            }
                        ],
                    }
                ],
            },
        )
    universe = UniverseCompiler().compile(pack, primary_level="L0", use_cache=False)
    env = VectorizedHamletEnv(universe=universe, level_name="L0", num_agents=4, device="cpu")
    env.reset()
    return env


def _snapshot(env: VectorizedHamletEnv, rows: slice) -> tuple:
    assert env.item_inventory is not None
    assert env.item_manager is not None
    indices = range(*rows.indices(env.num_agents))
    items = tuple(
        (world, item.instance_id, tuple(item.position), env.item_manager.holder_of(item))
        for world in indices
        for item in env.item_manager.items_in_world(world)
    )
    tensors = (env._get_observations(), env.meters, env.positions, env._velocity, env.item_inventory.slots)
    return tuple(value[rows].clone() for value in tensors), items


def _assert_snapshot(env: VectorizedHamletEnv, rows: slice, expected: tuple) -> None:
    tensors, items = _snapshot(env, rows)
    for actual, before in zip(tensors, expected[0], strict=True):
        assert torch.equal(actual, before)
    assert items == expected[1]


def _item_action(env: VectorizedHamletEnv, name: str) -> str:
    if name not in {"POLISH", "TOUCH"}:
        return name
    assert env.item_handler is not None
    matches = [action for action in env.item_handler.custom_action_specs if name in action]
    assert len(matches) == 1
    return matches[0]


@pytest.mark.parametrize("exclusive", [True, False], ids=["exclusive", "shared"])
@pytest.mark.parametrize("name", ["WAIT", "GET", "DROP_SLOT_0", "USE_SLOT_0", "POLISH", "TOUCH"])
def test_inactive_item_intent_freezes_world_and_live_actions_work(tmp_path: Path, exclusive: bool, name: str) -> None:
    env = _environment(tmp_path, spatial=False, exclusive=exclusive, terminal=True)
    action = _item_action(env, name)
    initial = "WAIT" if name in {"GET", "TOUCH"} else "GET"
    _step(env, [initial] * 4)
    _, _, dones, terminal = _step(env, ["WAIT"] * 4)
    assert dones.tolist() == [True, True, False, False]
    assert terminal["active_on_entry"].all()
    assert terminal["newly_terminal"].tolist() == [True, True, False, False]
    frozen = _snapshot(env, slice(0, 2))
    historical = terminal["successor_action_masks"].clone()
    assert env.item_inventory is not None
    _, rewards, _, info = _step(env, [action] * 4)
    assert info["active_on_entry"].tolist() == [False, False, True, True]
    assert info["step_counts"].tolist() == [2, 2, 3, 3]
    assert not info["newly_terminal"].any()
    assert not rewards[:2].any()
    _assert_snapshot(env, slice(0, 2), frozen)
    if name in {"USE_SLOT_0", "POLISH", "TOUCH"}:
        assert env.meters[2:, env.meter_name_to_index["money"]].tolist() == [1.0, 1.0]
    if name == "GET":
        assert (env.item_inventory.slots[2:] != -1).all()
    if name == "DROP_SLOT_0":
        assert (env.item_inventory.slots[2:] == -1).all()
    for _ in range(3):
        _, _, _, info = _step(env, [action, action, "WAIT", "WAIT"])
        _assert_snapshot(env, slice(0, 2), frozen)
    assert info["newly_retired"].tolist() == [False, False, True, True]
    assert info["newly_terminal"].tolist() == [False, False, True, True]
    assert info["step_counts"].tolist() == [2, 2, 6, 6]
    all_frozen = _snapshot(env, slice(None))
    _, rewards, dones, extra = _step(env, [action] * 4)
    _assert_snapshot(env, slice(None), all_frozen)
    assert dones.all()
    assert not rewards.any()
    assert not extra["active_on_entry"].any()
    assert not extra["newly_terminal"].any()
    assert not extra["newly_retired"].any()
    assert torch.equal(terminal["successor_action_masks"], historical)


def _movement_names(env: VectorizedHamletEnv) -> list[str]:
    names = []
    for row in range(env.num_agents):
        for action in env.action_space.actions:
            if action.id >= env.action_space.substrate_action_count:
                continue
            delta = env._movement_deltas[action.id]
            position = env.positions[row] + delta
            if delta.ne(0).any() and ((position >= 0) & (position < 8)).all():
                names.append(action.name)
                break
    assert len(names) == env.num_agents
    return names


@pytest.mark.parametrize("terminal", [True, False], ids=["authored", "retirement"])
@pytest.mark.parametrize("inactive_move", [True, False], ids=["move", "wait"])
def test_movement_and_velocity_freeze_after_eligible_final_action(tmp_path: Path, terminal: bool, inactive_move: bool) -> None:
    env = _environment(tmp_path, spatial=True, exclusive=True, terminal=terminal)
    _step(env, ["WAIT"] * 4)
    before = env.positions.clone()
    final_tick = 2 if terminal else 6
    for _ in range(final_tick - 1):
        before = env.positions.clone()
        _, _, _, info = _step(env, _movement_names(env))
        assert env.positions.ne(before).any(dim=1).all()
    assert info["active_on_entry"].all()
    assert info["newly_terminal"][:2].all()
    assert env._velocity[:2].ne(0).any(dim=1).all()
    frozen = _snapshot(env, slice(0, 2))
    live_before = env.positions[2:].clone()
    health_before = env.meters[:, env.meter_name_to_index["health"]].clone()
    following = _movement_names(env)
    if not inactive_move:
        following[:2] = ["WAIT", "WAIT"]
    _, _, _, info = _step(env, following)
    _assert_snapshot(env, slice(0, 2), frozen)
    assert not info["newly_terminal"].any()
    if terminal:
        assert env.positions[2:].ne(live_before).any(dim=1).all()
        torch.testing.assert_close(env.meters[2:, env.meter_name_to_index["health"]], health_before[2:] - 0.1)
    else:
        assert not info["active_on_entry"].any()


@pytest.mark.parametrize("name", ["GET", "DROP_SLOT_0", "USE_SLOT_0", "POLISH", "TOUCH"])
def test_terminal_causing_item_action_executes_once(tmp_path: Path, name: str) -> None:
    env = _environment(tmp_path, spatial=False, exclusive=True, terminal=True)
    action = _item_action(env, name)
    _step(env, ["WAIT" if name in {"GET", "TOUCH"} else "GET"] * 4)
    _, _, _, info = _step(env, [action] * 4)
    assert info["active_on_entry"].all()
    assert info["newly_terminal"].tolist() == [True, True, False, False]
    assert env.item_inventory is not None
    if name == "GET":
        assert (env.item_inventory.slots != -1).all()
    elif name == "DROP_SLOT_0":
        assert (env.item_inventory.slots == -1).all()
    else:
        assert env.meters[:, env.meter_name_to_index["money"]].tolist() == [1.0] * 4
    frozen = _snapshot(env, slice(0, 2))
    _step(env, [action, action, "WAIT", "WAIT"])
    _assert_snapshot(env, slice(0, 2), frozen)
