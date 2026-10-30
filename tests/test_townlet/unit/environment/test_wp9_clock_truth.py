"""VFS WP9, findings F1 and F2: the observation describes the state the next action is taken in.

In the observation returned by reset() and by every step(), the registry `tick`, every
expression derived from it (L3's `day_phase`), and the `time_of_day` that gates the next
action's opening hours are the same instant; and reset() evaluates expressions before
building the observation, so none shows its declared literal or a previous episode's value.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
import torch
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler

REPO = Path(__file__).resolve().parents[4]
L3 = "L3_temporal_mechanics"


def _variable_rows(env, obs: torch.Tensor, agent: int = 0) -> dict[str, list[float]]:
    """variable_element filler_ref -> that agent's observation row (presence first)."""
    spec = env.token_spec
    bindings = spec.get_type("variable_element").slot_bindings
    return {
        bindings[slot].filler_ref: obs[agent, start:end].tolist()
        for token_type, slot, start, end in spec.row_layout()
        if token_type == "variable_element"
    }


def _registry(env, name: str) -> torch.Tensor:
    return env.vfs_registry.get(name, reader="engine")


def _wait(env) -> torch.Tensor:
    index = next(i for i, action in enumerate(env.action_space.actions) if action.name == "WAIT")
    return torch.full((env.num_agents,), index, dtype=torch.long, device=env.device)


@pytest.fixture(scope="module")
def l3_env():
    universe = UniverseCompiler().compile(REPO / "configs" / "default_curriculum", primary_level=L3)
    return universe.create_environment(num_agents=1, level_name=L3, device="cpu")


def _observed_hour(env, obs: torch.Tensor) -> float:
    _presence, sin, cos = _variable_rows(env, obs)["day_phase"][:3]
    period = 24.0
    return round((math.atan2(sin, cos) / (2 * math.pi) * period) % period, 3) % period


def _assert_one_instant(env, obs: torch.Tensor) -> None:
    tick = env.global_tick
    assert float(_registry(env, "tick")) == float(tick)
    assert float(_registry(env, "day_phase")) == float(tick)
    assert env.time_of_day == tick % int(env.day_length)
    assert _observed_hour(env, obs) == pytest.approx(env.time_of_day, abs=1e-3)


def test_shipped_l3_clock_agrees_at_reset_and_every_step(l3_env):
    env = l3_env
    assert int(env.day_length) == 24
    obs = env.reset()
    _assert_one_instant(env, obs)
    assert env.time_of_day == 0
    for _ in range(30):  # crosses the day boundary
        obs, *_ = env.step(_wait(env))
        _assert_one_instant(env, obs)


def test_shipped_l3_second_episode_starts_at_hour_zero(l3_env):
    """r2: the reset observation used to carry the previous episode's final hour."""
    env = l3_env
    env.reset()
    for _ in range(29):
        env.step(_wait(env))
    obs = env.reset()
    _assert_one_instant(env, obs)
    assert _observed_hour(env, obs) == 0.0


def _interact_at(env, affordance: str) -> tuple[dict, float]:
    """INTERACT standing on `affordance` with full energy/mood; return (successes, money delta)."""
    interact = next(i for i, action in enumerate(env.action_space.actions) if action.name == "INTERACT")
    env.positions[0] = env.affordances[affordance].to(env.positions.dtype)
    for meter in ("energy", "mood"):
        env.meters[0, env.meter_name_to_index[meter]] = 1.0
    money = env.meter_name_to_index["money"]
    before = float(env.meters[0, money])
    _obs, _reward, _done, info = env.step(torch.full((env.num_agents,), interact, dtype=torch.long, device=env.device))
    return dict(info["successful_interactions"]), float(env.meters[0, money]) - before


def test_opening_hours_gate_the_hour_the_observation_shows(l3_env):
    """WORK opens at hour 9. INTERACT taken when the observation reads hour 8 does nothing;
    taken when it reads hour 9 it succeeds and pays: the gate is the observed hour."""
    env = l3_env
    obs = env.reset()
    for _ in range(8):
        obs, *_ = env.step(_wait(env))
    assert _observed_hour(env, obs) == pytest.approx(8.0, abs=1e-3)
    successes, paid = _interact_at(env, "WORK")
    assert successes == {}
    assert paid <= 0.0

    obs = env.reset()
    for _ in range(9):
        obs, *_ = env.step(_wait(env))
    assert _observed_hour(env, obs) == pytest.approx(9.0, abs=1e-3)
    successes, paid = _interact_at(env, "WORK")
    assert successes == {0: "WORK"}
    assert paid > 0.0


_MM2 = {"kind": "minmax", "min": 0.0, "max": 2.0, "clip": True}
_MM100 = {"kind": "minmax", "min": 0.0, "max": 100.0, "clip": True}


def _declaration(identifier, *, scope, lifetime, expression, normalization, initial=0.0):
    return {
        "id": identifier,
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "scope": scope,
        "type": "scalar",
        "lifetime": lifetime,
        "semantic_type": "custom",
        "initial_value": initial,
        "exposed_to": ["agent"],
        "normalization": normalization,
        "expression": expression,
    }


@pytest.fixture
def expression_env(tmp_path):
    config_dir = prepare_config_dir(tmp_path)
    variables = {
        "variables": {
            "version": "1.0",
            "extents": {},
            "item_profiles": ["default_item"],
            "declarations": [
                _declaration("e_energy", scope="agent", lifetime="episode", expression="bar.energy * 2.0", normalization=_MM2),
                _declaration("g_persist_tick", scope="global", lifetime="persistent", expression="tick", normalization=_MM100),
                _declaration("tick_mirror", scope="global", lifetime="tick", expression="tick + 1.0", normalization=_MM100),
            ],
        }
    }
    (config_dir / "variables.yaml").write_text(yaml.safe_dump(variables))
    universe = UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME)
    return universe.create_environment(num_agents=2, level_name=PRIMARY_LEVEL_NAME, device="cpu")


def test_episode_expression_publishes_its_evaluated_value_at_reset(expression_env):
    env = expression_env
    obs = env.reset()
    energy = env.meters[:, env.meter_name_to_index["energy"]]
    assert torch.equal(_registry(env, "e_energy"), energy * 2.0)
    assert float(energy[0]) != 0.0  # the declared literal (0.0) would be distinguishable
    presence, lane = _variable_rows(env, obs, agent=0)["e_energy"][:2]
    assert presence == 1.0
    assert lane == pytest.approx(float(energy[0]) * 2.0 / 2.0)


def test_persistent_expression_does_not_leak_previous_episode(expression_env):
    env = expression_env
    env.reset()
    for _ in range(5):
        env.step(_wait(env))
    assert float(_registry(env, "g_persist_tick")) == 5.0
    obs = env.reset()
    assert float(_registry(env, "g_persist_tick")) == 0.0
    assert _variable_rows(env, obs)["g_persist_tick"][1] == 0.0


def test_tick_lifetime_expression_tracks_the_clock(expression_env):
    """r1's `tick_mirror: tick + 1` read global_tick, one ahead of the registry tick."""
    env = expression_env
    env.reset()
    assert float(_registry(env, "tick_mirror")) == 1.0
    for _ in range(3):
        env.step(_wait(env))
        assert float(_registry(env, "tick")) == float(env.global_tick)
        assert float(_registry(env, "tick_mirror")) == float(env.global_tick) + 1.0
