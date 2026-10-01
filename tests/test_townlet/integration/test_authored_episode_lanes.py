"""Authored lifecycle assertions execute the actual compiler, brain and population."""

import torch

from tests.test_townlet.regressions.fixtures.episode_lanes import (
    EPISODE_LANE_CONFIG,
    UNEQUAL_ENDINGS,
    build_authored_population,
    controlled_action_schedule,
    observe_environment_steps,
)
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration


def _population():
    return build_authored_population(
        EPISODE_LANE_CONFIG,
        num_agents=2,
        exploration=EpsilonGreedyExploration(epsilon=0.0, epsilon_decay=1.0, epsilon_min=0.0),
    )


def test_authored_pack_compiles() -> None:
    population = _population()
    env = population.env
    assert env.universe.brain.architecture.type == "feedforward"
    assert population.brain_config.architecture.feedforward.hidden_layers == [256, 128]
    assert env.meters[:, env.meter_name_to_index["energy"]].tolist() == [1.0, 1.0]
    forwards = []
    hook = population.q_network.register_forward_hook(lambda _module, _args, output: forwards.append(output.detach().clone()))
    try:
        with controlled_action_schedule(population.exploration, env, UNEQUAL_ENDINGS) as selection, observe_environment_steps(env) as ticks:
            for _ in UNEQUAL_ENDINGS:
                population.step_population(env)
    finally:
        hook.remove()
    assert len(forwards) == len(selection.q_values) == 5
    assert all(torch.equal(output, q_values) for output, q_values in zip(forwards, selection.q_values, strict=True))
    assert torch.stack([item.active_before for item in ticks]).sum(dim=0).tolist() == [2, 5]
    assert torch.stack([item.new_done for item in ticks]).sum(dim=0).tolist() == [1, 1]
    assert ticks[1].new_done.tolist() == [True, False]
    assert ticks[4].new_done.tolist() == [False, True]
    assert env.global_tick == 5


def test_authored_population_survival_reports_the_seven_actual_transitions() -> None:
    population = _population()
    env = population.env
    with controlled_action_schedule(population.exploration, env, UNEQUAL_ENDINGS), observe_environment_steps(env) as ticks:
        for _ in UNEQUAL_ENDINGS:
            state = population.step_population(env)
    actual = torch.stack([item.active_before for item in ticks]).sum(dim=0).tolist()
    print(f"authored independent survival={actual}; published survival={state.survival_times.tolist()}")
    assert actual == [2, 5]
    assert state.survival_times.tolist() == actual
    assert sum(actual) == 7
    assert env.global_tick == 5
