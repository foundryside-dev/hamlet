"""Pinning tests for hamlet-88acec4bb5 — dead agents stop transacting (WS-1 sibling 3b).

The INTERACT path builds its mask from the action-id range only
(``interact_mask = (actions == INTERACT) & substrate_mask``); nothing on it
consults ``env.dones``, so a dead agent is charged the interaction debit and
completes interactions on both the instant and multi-tick paths.  These tests
pin the fix: a dead agent is neither charged nor allowed to complete or
progress an interaction, while the tracking side-effects that fire on *intent*
keep their trigger condition (T4).

T3 drives ``_execute_actions`` directly rather than ``env.step`` on purpose:
passive depletion runs with an all-ones active mask, so through a full step a
dead agent's meters move by the passive tick regardless of this fix, and the
"dead delta == 0" assertion is exact only at the executor boundary.  The
debit, the recording, and the progress advance — the whole defect surface —
all live inside ``_execute_actions``.

Every meter assertion is a delta or an exclusion, never an absolute literal.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/default_curriculum")
LEVEL = "L1_full_observability"
L3_LEVEL = "L3_temporal_mechanics"


@pytest.fixture(scope="module")
def universe():
    return UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)


@pytest.fixture(scope="module")
def multi_tick_universe(tmp_path_factory):
    """L3 with SLEEP rewritten to a 3-tick multi-tick interaction (zero per-tick cost)."""
    target = tmp_path_factory.mktemp("dead_agent_multi_tick") / "default_curriculum"
    shutil.copytree(PACK, target)
    compiled = target / ".compiled"
    if compiled.exists():
        shutil.rmtree(compiled)
    affordances = target / "levels" / L3_LEVEL / "affordances.yaml"
    document = yaml.safe_load(affordances.read_text())
    sleep = next(entry for entry in document["affordances"]["affordances"] if entry["name"] == "SLEEP")
    assert sleep["interaction_type"] == "instant", "SLEEP interaction fixture has drifted"
    sleep["interaction_type"] = "multi_tick"
    sleep["duration_ticks"] = 3
    sleep["costs"] = {}
    sleep["costs_per_tick"] = {"energy": 0.0}
    sleep["interactions"]["on_completion"] = sleep["interactions"]["on_start"]
    sleep["interactions"]["on_start"] = []
    affordances.write_text(yaml.safe_dump(document, sort_keys=False))
    return UniverseCompiler().compile(target, primary_level=L3_LEVEL, use_cache=False)


def _env_with_one_dead_agent(universe, level_name=LEVEL):
    env = VectorizedHamletEnv(universe=universe, level_name=level_name, num_agents=2, device="cpu")
    env.reset()
    health = env.meter_name_to_index["health"]
    env.meters[1, health] = 0.0
    env.step(torch.full((2,), env.action_ids["WAIT"], dtype=torch.long))
    assert env.dones.tolist() == [False, True], "vacuity: terminal condition did not kill agent 1"
    return env


def test_a_dead_agent_is_not_charged_the_interaction_cost(universe):
    env = _env_with_one_dead_agent(universe)
    energy = env.meter_name_to_index["energy"]
    occupied = {tuple(v.tolist()) for v in env.affordances.values()}
    free = next((x, y) for x in range(8) for y in range(8) if (x, y) not in occupied)
    env.positions[0] = torch.tensor(free)
    env.positions[1] = torch.tensor(free)
    env.meters[:, energy] = 0.5
    before = env.meters[:, energy].clone()
    env._action_executor._execute_actions(torch.full((2,), env.action_ids["INTERACT"], dtype=torch.long))
    after = env.meters[:, energy]
    assert after[0].item() < before[0].item(), "vacuity: live agent was not charged"
    assert after[1].item() == pytest.approx(before[1].item()), "dead agent was charged the interaction cost"


def test_a_dead_agent_does_not_complete_an_instant_interaction(universe):
    env = _env_with_one_dead_agent(universe)
    energy = env.meter_name_to_index["energy"]
    money = env.meter_name_to_index["money"]
    work = env.affordances["WORK"]
    env.positions[0] = work.clone()
    env.positions[1] = work.clone()
    env.meters[:, energy] = 0.5
    env.meters[:, money] = 0.0
    _, _, _, info = env.step(torch.full((2,), env.action_ids["INTERACT"], dtype=torch.long))
    assert info["successful_interactions"].get(0) == "WORK", "vacuity: live agent did not interact"
    assert 1 not in info["successful_interactions"], "dead agent completed an interaction"
    assert env.meters[1, money].item() == pytest.approx(0.0), "dead agent was paid"
    assert env._last_affordances[1] is None, "dead agent polluted affordance tracking"
    assert env._affordance_streaks["WORK"][1].item() == 0, "dead agent polluted streaks"


def test_a_dead_agent_makes_no_multi_tick_progress_and_pays_nothing(multi_tick_universe):
    env = _env_with_one_dead_agent(multi_tick_universe, level_name=L3_LEVEL)
    energy = env.meter_name_to_index["energy"]
    sleep = env.affordances["SLEEP"]
    env.positions[0] = sleep.clone()
    env.positions[1] = sleep.clone()
    env.meters[:, energy] = 0.5
    before = env.meters[:, energy].clone()
    interact = torch.full((2,), env.action_ids["INTERACT"], dtype=torch.long)
    progress_after_first_tick = None
    for tick in range(3):
        recorded = env._action_executor._execute_actions(interact)
        assert 0 in recorded, f"vacuity: live agent not recorded at tick {tick}"
        assert 1 not in recorded, f"dead agent recorded an interaction at tick {tick}"
        if tick == 0:
            progress_after_first_tick = int(env.interaction_progress[0].item())
    assert progress_after_first_tick is not None and progress_after_first_tick >= 1, "vacuity: live agent made no multi-tick progress"
    delta_dead = env.meters[1, energy].item() - before[1].item()
    assert delta_dead == pytest.approx(0.0), "dead agent paid for a multi-tick interaction"
    assert env.interaction_progress[1].item() == 0, "dead agent made multi-tick progress"


def test_a_live_agent_keeps_its_affordance_tracking_when_only_dead_agents_interact(universe):
    # The trigger-condition lock: gating the whole INTERACT block on the
    # dones-filtered mask would change *which ticks call*
    # _update_affordance_tracking.  The two-name form keeps the trigger on
    # intent, so a tick where only a dead agent intends INTERACT still clears
    # the live agent's stale tracking.  Green on current production code; red
    # under the one-term "simplification".
    env = _env_with_one_dead_agent(universe)
    energy = env.meter_name_to_index["energy"]
    work = env.affordances["WORK"]
    env.positions[0] = work.clone()
    env.positions[1] = work.clone()
    env.meters[:, energy] = 0.5
    _, _, _, info = env.step(torch.tensor([env.action_ids["INTERACT"], env.action_ids["WAIT"]], dtype=torch.long))
    assert info["successful_interactions"].get(0) == "WORK", "vacuity: live agent did not interact"
    assert env._last_affordances[0] == "WORK", "vacuity: tracking did not record the live interaction"
    env.step(torch.tensor([env.action_ids["WAIT"], env.action_ids["INTERACT"]], dtype=torch.long))
    assert env._last_affordances[0] is None, "tracking went stale: a dead-only INTERACT tick must still run _update_affordance_tracking"
