"""Real authored transitions must enter replay and close population lanes once."""

from __future__ import annotations

import copy
from pathlib import Path
from unittest.mock import patch

import pytest
import torch
import yaml

from tests.test_townlet.regressions.fixtures.episode_lanes import (
    compile_authored_environment,
    controlled_action_schedule,
    copy_authored_config,
)
from townlet.curriculum.adversarial import AdversarialCurriculum
from townlet.curriculum.static import StaticCurriculum
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer


def make_lane_population(
    directory: Path,
    *,
    mode: str,
    num_agents: int,
    lifespan: int,
    batch_size: int,
    sequence_length: int,
    rnd_batch_size: int,
    double_dqn: bool,
) -> VectorizedPopulation:
    """Compile the authored pack and selected architecture through supported YAML."""
    config = copy_authored_config(directory, lifespan=lifespan, num_agents=num_agents)
    brain_path = config / "brain.yaml"
    brain = yaml.safe_load(brain_path.read_text())
    if mode == "recurrent":
        brain["architecture"] = {
            "type": "recurrent",
            "recurrent": {
                "token_embed_dim": 16,
                "aggregator": {"type": "mean"},
                "lstm": {"hidden_size": 16, "num_layers": 1, "dropout": 0.0},
                "q_head_hidden_dim": 16,
            },
        }
    else:
        brain["architecture"]["feedforward"]["hidden_layers"] = [16, 16]
    brain["q_learning"]["use_double_dqn"] = double_dqn
    brain["q_learning"]["target_update_frequency"] = 1000
    brain["replay"]["capacity"] = 1000
    if mode == "per":
        brain["replay"].update(prioritized=True, priority_alpha=0.6, priority_beta=0.4, priority_beta_annealing=False)
    brain_path.write_text(yaml.safe_dump(brain, sort_keys=False))
    env = compile_authored_environment(config, num_agents=num_agents)
    exploration = AdaptiveIntrinsicExploration(
        obs_dim=env.observation_dim, rnd_training_batch_size=rnd_batch_size, device=torch.device("cpu")
    )
    population = VectorizedPopulation(
        env=env,
        curriculum=StaticCurriculum(1.0),
        exploration=exploration,
        agent_ids=[f"lane-{index}" for index in range(num_agents)],
        device=torch.device("cpu"),
        brain_config=env.universe.brain,
        obs_dim=env.observation_dim,
        action_dim=env.action_dim,
        train_frequency=1,
        batch_size=batch_size,
        sequence_length=sequence_length,
        max_grad_norm=1.0,
        tb_logger=None,
        max_episodes=100,
        max_steps_per_episode=lifespan,
    )
    population.reset()
    return population


def schedule_for(end_ticks: tuple[int, ...]) -> list[tuple[str, ...]]:
    return [tuple("END_LANE" if ending == tick else "WAIT" for ending in end_ticks) for tick in range(1, max(end_ticks) + 1)]


def assert_nested_equal(before, after) -> None:
    if isinstance(before, torch.Tensor):
        assert torch.equal(before, after)
    elif isinstance(before, dict):
        assert before.keys() == after.keys()
        for key in before:
            assert_nested_equal(before[key], after[key])
    elif isinstance(before, list | tuple):
        assert len(before) == len(after)
        for left, right in zip(before, after, strict=True):
            assert_nested_equal(left, right)
    else:
        assert before == after


@pytest.mark.parametrize("mode", ["standard", "per", "recurrent"])
def test_two_five_replay_contains_seven_transitions_and_two_terminal_rows(tmp_path: Path, mode: str) -> None:
    population = make_lane_population(
        tmp_path / "pack",
        mode=mode,
        num_agents=2,
        lifespan=20,
        batch_size=128,
        sequence_length=1,
        rnd_batch_size=128,
        double_dqn=False,
    )
    with controlled_action_schedule(population.exploration, population.env, schedule_for((2, 5))):
        for _ in range(5):
            population.step_population(population.env)
    replay = population.replay_buffer
    if isinstance(replay, SequentialReplayBuffer):
        assert replay.num_transitions == 7
        assert [len(episode["actions"]) for episode in replay.episodes] == [2, 5]
        assert sum(int(episode["dones"].sum()) for episode in replay.episodes) == 2
    else:
        assert len(replay) == 7
        assert replay.dones[:7].sum() == 2


@pytest.mark.parametrize("mode", ["standard", "per", "recurrent"])
@pytest.mark.parametrize("end_ticks", [(2, 5), (5, 2), (2, 2), (2,)])
def test_replay_matches_independent_eligible_ledger_and_completes_once(tmp_path: Path, mode: str, end_ticks: tuple[int, ...]) -> None:
    population = make_lane_population(
        tmp_path / "pack",
        mode=mode,
        num_agents=len(end_ticks),
        lifespan=20,
        batch_size=128,
        sequence_length=1,
        rnd_batch_size=128,
        double_dqn=False,
    )
    env = population.env
    ledger_counts = torch.zeros(len(end_ticks), dtype=torch.long)
    ledger_terminals = torch.zeros_like(ledger_counts)
    expected = {
        key: []
        for key in (
            "observations",
            "actions",
            "rewards",
            "rewards_extrinsic",
            "rewards_intrinsic",
            "rewards_shaping",
            "next_observations",
            "dones",
        )
    }
    lane_rows = {}
    stored_lanes = []
    completed = []
    original_store = population._store_episode_and_reset

    def store(agent_idx):
        result = original_store(agent_idx)
        if result:
            stored_lanes.append((episode, agent_idx))
        return result

    original_finalize = population._finalize_episode

    def finalize(*args, **kwargs):
        result = original_finalize(*args, **kwargs)
        completed.append(result)
        return result

    for episode in range(2):
        if episode:
            population.reset()
            assert population.episode_step_counts.tolist() == [0] * len(end_ticks)
            assert population.runtime_registry.get_survival_time_tensor().tolist() == [0] * len(end_ticks)
        episode_counts = torch.zeros_like(ledger_counts)
        for agent in range(len(end_ticks)):
            lane_rows[episode, agent] = {name: [] for name in expected}
        with (
            patch.object(population, "_finalize_episode", side_effect=finalize),
            patch.object(population, "_store_episode_and_reset", side_effect=store),
        ):
            with controlled_action_schedule(population.exploration, env, schedule_for(end_ticks)):
                for _ in range(max(end_ticks)):
                    before_done = env.dones.clone()
                    predecessor = population.current_obs.clone()
                    state = population.step_population(env)
                    active = ~before_done
                    new_end = active & state.dones
                    episode_counts += active.long()
                    ledger_counts += active.long()
                    ledger_terminals += new_end.long()
                    fields = {
                        "observations": predecessor,
                        "actions": state.actions,
                        "rewards": state.rewards,
                        "next_observations": state.observations,
                        "dones": state.dones,
                        **{
                            f"rewards_{key}": value
                            for key, value in state.info["reward_components"].items()
                            if key in {"extrinsic", "intrinsic", "shaping"}
                        },
                    }
                    for name, value in fields.items():
                        expected[name].append(value[active].detach().clone())
                        for agent in torch.nonzero(active, as_tuple=False).flatten().tolist():
                            lane_rows[episode, agent][name].append(value[agent].detach().clone())
        assert episode_counts.tolist() == list(end_ticks)
        assert population.episode_step_counts.tolist() == list(end_ticks)
        assert population.runtime_registry.get_survival_time_tensor().tolist() == list(end_ticks)
        assert [item.survival_time for item in population.episode_completions] == list(end_ticks)
        assert [item.reason for item in population.episode_completions] == ["authored_terminal"] * len(end_ticks)
        assert len(completed) == (episode + 1) * len(end_ticks)
        assert all(item is not None for item in completed)
        assert len(population.exploration.survival_history) == (episode + 1) * len(end_ticks)
        assert sorted(population.exploration.survival_history) == sorted(list(end_ticks) * (episode + 1))
        with pytest.raises(RuntimeError, match="complete"):
            population.step_population(env)
    assert ledger_counts.tolist() == [2 * value for value in end_ticks]
    assert ledger_terminals.tolist() == [2] * len(end_ticks)
    if isinstance(population.replay_buffer, SequentialReplayBuffer):
        replay = population.replay_buffer
        assert sorted(len(item["actions"]) for item in replay.episodes) == sorted(list(end_ticks) * 2)
        assert replay.num_transitions == 2 * sum(end_ticks)
        assert sum(int(item["dones"].sum()) for item in replay.episodes) == 2 * len(end_ticks)
        # Store-call coordinates bind each complete sequence to its episode/lane.
        assert len(stored_lanes) == len(replay.episodes)
        assert len(set(stored_lanes)) == 2 * len(end_ticks)
        for coordinate, stored in zip(stored_lanes, replay.episodes, strict=True):
            for name in expected:
                assert torch.equal(stored[name], torch.stack(lane_rows[coordinate][name])), (coordinate, name)
    else:
        assert len(population.replay_buffer) == 2 * sum(end_ticks)
        for name, rows in expected.items():
            actual = getattr(population.replay_buffer, name)[: 2 * sum(end_ticks)]
            assert torch.equal(actual, torch.cat(rows)), name


@pytest.mark.parametrize("mode", ["standard", "per", "recurrent"])
@pytest.mark.parametrize("reason", ["cap", "budget", "shutdown", "checkpoint"])
def test_pending_reset_refuses_before_mutation_and_explicit_cut_closes_once(tmp_path: Path, mode: str, reason: str) -> None:
    population = make_lane_population(
        tmp_path / "pack",
        mode=mode,
        num_agents=2,
        lifespan=20,
        batch_size=128,
        sequence_length=1,
        rnd_batch_size=128,
        double_dqn=False,
    )
    with controlled_action_schedule(population.exploration, population.env, [("WAIT", "WAIT")]):
        population.step_population(population.env)
    snapshot = {
        "obs": population.current_obs.clone(),
        "meters": population.env.meters.clone(),
        "dones": population.env.dones.clone(),
        "counts": population.env.step_counts.clone(),
        "population_counts": population.episode_step_counts.clone(),
        "tick": population.env.global_tick,
        "episodes": copy.deepcopy(population.current_episodes),
        "hidden": copy.deepcopy(population.rollout_hidden),
        "registry": population.runtime_registry.get_survival_time_tensor().clone(),
        "history": list(population.exploration.survival_history),
        "environment_tensors": {name: value.clone() for name, value in vars(population.env).items() if isinstance(value, torch.Tensor)},
        "registry_tensors": {
            name: value.clone() for name, value in vars(population.runtime_registry).items() if isinstance(value, torch.Tensor)
        },
    }
    with pytest.raises(RuntimeError, match="explicit stop reason"):
        population.reset()
    current = {
        "obs": population.current_obs,
        "meters": population.env.meters,
        "dones": population.env.dones,
        "counts": population.env.step_counts,
        "population_counts": population.episode_step_counts,
        "tick": population.env.global_tick,
        "episodes": population.current_episodes,
        "hidden": population.rollout_hidden,
        "registry": population.runtime_registry.get_survival_time_tensor(),
        "history": population.exploration.survival_history,
        "environment_tensors": {name: value for name, value in vars(population.env).items() if isinstance(value, torch.Tensor)},
        "registry_tensors": {name: value for name, value in vars(population.runtime_registry).items() if isinstance(value, torch.Tensor)},
    }
    assert_nested_equal(snapshot, current)
    for index in range(2):
        completion = population.flush_episode(index, reason=reason)
        assert completion.reason == reason
        assert completion.survival_time == 1
        observation = completion.final_observation.clone()
        meters = completion.final_meters.clone()
        assert population.flush_episode(index, reason="checkpoint") is None
        population.current_obs[index].zero_()
        population.env.meters[index].zero_()
        assert torch.equal(completion.final_observation, observation)
        assert torch.equal(completion.final_meters, meters)
    assert population.exploration.survival_history == [1, 1]
    if isinstance(population.replay_buffer, SequentialReplayBuffer):
        assert all(not item["dones"].any() for item in population.replay_buffer.episodes)
    else:
        assert not population.replay_buffer.dones[:2].any()
    population.reset()
    population.reset()
    assert population.episode_step_counts.tolist() == [0, 0]
    assert population.episode_completions == [None, None]
    assert population.exploration.survival_history == [1, 1]
    assert population.flush_episode(0, reason="checkpoint") is None


def test_authored_death_and_healthy_retirement_have_distinct_owned_reasons(tmp_path: Path) -> None:
    population = make_lane_population(
        tmp_path / "pack",
        mode="standard",
        num_agents=2,
        lifespan=5,
        batch_size=128,
        sequence_length=1,
        rnd_batch_size=128,
        double_dqn=False,
    )
    schedule = schedule_for((2, 5))
    schedule[-1] = ("WAIT", "WAIT")
    events = []
    with controlled_action_schedule(population.exploration, population.env, schedule):
        for _ in range(5):
            state = population.step_population(population.env)
            events.extend(state.info["episode_completions"])
    assert [(event.agent_idx, event.reason, event.survival_time) for event in events] == [(0, "authored_terminal", 2), (1, "retirement", 5)]
    assert state.rewards[0] == 0.0
    assert state.rewards[1] > 1.0
    assert population.exploration.survival_history == [2, 5]
    assert population.replay_buffer.dones[:7].sum() == 2


def test_recurrent_dead_hidden_stays_zero_with_full_adversarial_q_rows(tmp_path: Path) -> None:
    torch.manual_seed(71)
    population = make_lane_population(
        tmp_path / "pack",
        mode="recurrent",
        num_agents=2,
        lifespan=20,
        batch_size=128,
        sequence_length=1,
        rnd_batch_size=128,
        double_dqn=False,
    )
    curriculum = AdversarialCurriculum(max_steps_per_episode=20, min_steps_at_stage=1000, device=population.device)
    curriculum.initialize_population(2)
    population.curriculum = curriculum
    hidden_rows = []
    reference_hidden = population.q_network.initial_hidden(2, population.device)
    original_entropy = curriculum._calculate_action_entropy
    original_decisions = curriculum.get_batch_decisions_with_qvalues
    observed_entropies = []
    observed_q_inputs = []

    def entropy(q_values):
        result = original_entropy(q_values)
        observed_entropies.append(result.detach().clone())
        return result

    def decisions(agent_states, agent_ids, q_values):
        observed_q_inputs.append(q_values.detach().clone())
        assert agent_ids == population.agent_ids
        return original_decisions(agent_states, agent_ids, q_values)

    with (
        patch.object(curriculum, "_calculate_action_entropy", side_effect=entropy),
        patch.object(curriculum, "get_batch_decisions_with_qvalues", side_effect=decisions),
        controlled_action_schedule(population.exploration, population.env, schedule_for((2, 5))) as selection,
    ):
        for tick in range(1, 6):
            with torch.no_grad():
                reference_q, next_reference_hidden = population.q_network(population.current_obs.unsqueeze(1), reference_hidden)
                active = ~population.env.dones.clone()
                for next_tensor, previous_tensor in zip(next_reference_hidden, reference_hidden, strict=True):
                    next_tensor[:, ~active] = previous_tensor[:, ~active]
                reference_hidden = next_reference_hidden
            state = population.step_population(population.env)
            assert torch.equal(selection.q_values[-1], reference_q[:, 0])
            assert torch.equal(observed_q_inputs[-1], reference_q[:, 0])
            for reference_tensor in reference_hidden:
                reference_tensor[:, state.dones] = 0.0
            for expected_tensor, actual_tensor in zip(reference_hidden, population.rollout_hidden, strict=True):
                assert torch.equal(expected_tensor, actual_tensor)
            assert len(population.current_curriculum_decisions) == 2
            assert population.current_curriculum_decisions[0].depletion_multiplier == 0.2
            assert curriculum.tracker.agent_stages.tolist() == [1, 1]
            probabilities = torch.softmax(selection.q_values[-1], dim=1)
            entropy = -(probabilities * torch.log(probabilities + 1e-10)).sum(dim=1)
            assert entropy.shape == (2,) and torch.isfinite(entropy).all()
            assert torch.allclose(observed_entropies[-1], entropy / torch.log(torch.tensor(float(population.env.action_dim))))
            assert state.actions[1] == population.env.action_ids["END_LANE" if tick == 5 else "WAIT"]
            h, c = population.rollout_hidden
            if tick >= 2:
                assert not h[:, 0].any() and not c[:, 0].any()
            if tick < 5:
                assert h[:, 1].any() and c[:, 1].any()
                hidden_rows.append(h[:, 1].clone())
    assert any(not torch.equal(left, right) for left, right in zip(hidden_rows, hidden_rows[1:]))
    assert selection.q_values[2][0].abs().sum() > 0  # Dead Q rows still come from the real full forward.
