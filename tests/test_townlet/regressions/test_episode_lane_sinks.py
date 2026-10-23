"""Ordinary runner sinks must describe the independently observed eligible lanes."""

from __future__ import annotations

import math
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest
import torch
import yaml
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

from tests.test_townlet.regressions.fixtures.episode_lanes import LEVEL_NAME, action_ids, copy_authored_config
from townlet.demo.runner import DemoRunner
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.population.vectorized import VectorizedPopulation


def run_lane_runner(
    run_dir: Path, *, episodes: int, budget: int | None, cap: int | None, end_ticks: tuple[int, int], real_dac: bool, recording: bool
) -> tuple[DemoRunner, list[dict], list[tuple[torch.Tensor, torch.Tensor]]]:
    """Control selection only; compiler, forward, runner and all sinks execute normally."""
    run_dir.mkdir(parents=True)
    config = copy_authored_config(run_dir / "pack", lifespan=10, num_agents=2)
    training_path = config / "levels" / LEVEL_NAME / "training.yaml"
    training = yaml.safe_load(training_path.read_text())
    training["training"]["training_loop"]["max_episodes"] = episodes
    training["training"]["replay_buffer"]["batch_size"] = 128
    training["recording"] = {
        "enabled": recording,
        "output_dir": "recordings",
        "max_queue_size": 100,
        "compression": "lz4",
        "criteria": {"periodic": {"enabled": True, "interval": 1}},
    }
    training_path.write_text(yaml.safe_dump(training, sort_keys=False))
    if real_dac:
        drive_path = config / "levels" / LEVEL_NAME / "drive.yaml"
        drive = yaml.safe_load(drive_path.read_text())
        drive["drive"]["modifiers"]["energy_crisis"]["ranges"][1]["multiplier"] = 0.5
        drive["drive"]["shaping"][0]["max_distance"] = 100.0
        drive_path.write_text(yaml.safe_dump(drive, sort_keys=False))
    ticks: list[dict] = []
    curricula: list[tuple[torch.Tensor, torch.Tensor]] = []
    original_reset = VectorizedPopulation.reset
    original_step = VectorizedHamletEnv.step
    original_curriculum = VectorizedPopulation.update_curriculum_tracker
    episode = -1

    def reset(population: VectorizedPopulation) -> None:
        nonlocal episode
        original_reset(population)
        episode += 1
        env = population.env
        if cap is not None:
            # Explicit caller truncation fixture: the authored environment retains
            # its lifespan of ten while the caller cuts the batch loop earlier.
            assert env.agent_lifespan == 10
            runner.training_config.training_loop.max_steps_per_episode = cap
        assert env.meters[:, env.meter_name_to_index["energy"]].tolist() == [1.0, 1.0]

        def select(q_values, agent_states, action_masks):
            assert q_values.shape == (2, env.action_dim) and torch.isfinite(q_values).all()
            assert agent_states.observations.shape[0] == 2
            tick = env.global_tick + 1
            names = tuple("END_LANE" if tick >= ending else "WAIT" for ending in end_ticks)
            actions = action_ids(env, names)
            assert action_masks[torch.arange(2), actions][~env.dones].all()
            return actions

        population.exploration.select_actions = select

    def step(env: VectorizedHamletEnv, actions: torch.Tensor, depletion_multiplier: float = 1.0):
        active = (~env.dones).clone()
        result = original_step(env, actions, depletion_multiplier)
        observations, rewards, dones, info = result
        ticks.append(
            {
                "episode": episode,
                "tick": env.global_tick,
                "active": active,
                "terminal": active & dones,
                "dones": dones.clone(),
                "actions": actions.clone(),
                "observations": observations.detach().cpu().clone(),
                "meters": env.meters.detach().cpu().clone(),
                "rewards": rewards.detach().cpu().clone(),
                "components": {key: value.detach().cpu().clone() for key, value in info["reward_components"].items()},
                "weights": info["intrinsic_weight"].detach().cpu().clone(),
            }
        )
        return result

    def curriculum(population, survival_times, dones):
        curricula.append((survival_times.detach().cpu().clone(), dones.detach().cpu().clone()))
        return original_curriculum(population, survival_times, dones)

    exploration_patch = (
        patch("townlet.demo.runner.AdaptiveIntrinsicExploration", side_effect=lambda **kwargs: EpsilonGreedyExploration(0.0, 1.0, 0.0))
        if not real_dac
        else patch(
            "townlet.demo.runner.AdaptiveIntrinsicExploration",
            wraps=__import__(
                "townlet.exploration.adaptive_intrinsic", fromlist=["AdaptiveIntrinsicExploration"]
            ).AdaptiveIntrinsicExploration,
        )
    )
    with (
        exploration_patch,
        patch.object(VectorizedPopulation, "reset", reset),
        patch.object(VectorizedHamletEnv, "step", step),
        patch.object(VectorizedPopulation, "update_curriculum_tracker", curriculum),
        DemoRunner(
            config_dir=config,
            db_path=run_dir / "demo.db",
            checkpoint_dir=run_dir / "checkpoints",
            max_episodes=episodes,
            level_name=LEVEL_NAME,
            max_environment_steps=budget,
        ) as runner,
    ):
        runner.run()
    return runner, ticks, curricula


def events_for(runner: DemoRunner) -> EventAccumulator:
    assert runner.tb_logger is not None
    accumulator = EventAccumulator(str(runner.tb_logger.log_dir), size_guidance={"scalars": 0, "tensors": 0})
    accumulator.Reload()
    return accumulator


@pytest.mark.parametrize("end_ticks", [(2, 5), (5, 2)])
def test_ordinary_runner_db_tb_curriculum_and_snapshots_match_two_episode_ledger(tmp_path: Path, end_ticks: tuple[int, int]) -> None:
    runner, ticks, curricula = run_lane_runner(
        tmp_path / "run", episodes=2, budget=None, cap=None, end_ticks=end_ticks, real_dac=False, recording=False
    )
    with closing(sqlite3.connect(runner.db_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = [dict(row) for row in connection.execute("SELECT * FROM episodes ORDER BY episode_id")]
    assert len(rows) == len(curricula) == 2
    acc = events_for(runner)
    for episode, row in enumerate(rows):
        observed = [item for item in ticks if item["episode"] == episode]
        counts = torch.stack([item["active"] for item in observed]).sum(dim=0).tolist()
        assert counts == list(end_ticks)
        assert len(observed) == row["batch_episode_steps"] == 5
        assert row["survival_time"] == end_ticks[0]
        assert row["live_agent_transitions"] == sum(counts) == 7
        assert row["completion_reason"] == "authored_terminal"
        assert acc.Scalars("Batch/Vector_Ticks")[episode].value == 5
        assert acc.Scalars("Batch/Live_Agent_Transitions")[episode].value == 7
        assert curricula[episode][0].tolist() == counts
        assert curricula[episode][1].tolist() == [True, True]
        for agent in range(2):
            assert acc.Scalars(f"agent_{agent}/Episode/Survival_Time")[episode].value == counts[agent]
            reason = acc.Tensors(f"agent_{agent}/Episode/Completion_Reason/text_summary")[episode]
            assert reason.tensor_proto.string_val == [b"authored_terminal"]
    assert runner.population is not None
    final_episode = [item for item in ticks if item["episode"] == 1]
    for agent, ending in enumerate(end_ticks):
        completion = runner.population.episode_completions[agent]
        assert torch.equal(completion.final_meters, final_episode[ending - 1]["meters"][agent])
        assert torch.equal(completion.final_observation, final_episode[ending - 1]["observations"][agent])
        usage = Counter(int(item["actions"][agent]) for item in final_episode if bool(item["active"][agent]))
        assert usage[runner.env.action_ids["END_LANE"]] == 1
        assert acc.Scalars(f"agent_{agent}/CustomActions/END_LANE")[1].value == 1


def test_real_dac_db_and_tb_publish_effective_components_and_zero_terminal_frame(tmp_path: Path) -> None:
    runner, ticks, _ = run_lane_runner(
        tmp_path / "run", episodes=1, budget=None, cap=None, end_ticks=(2, 5), real_dac=True, recording=False
    )
    acc = events_for(runner)
    assert ticks[0]["rewards"][0] > 0
    assert ticks[1]["rewards"][0] == 0
    assert any(item["components"]["shaping"].abs().sum() > 0 for item in ticks)
    assert any(
        bool(item["active"][agent])
        and item["components"]["intrinsic"][agent] > 0
        and not torch.isclose(item["components"]["intrinsic"][agent], item["components"]["intrinsic_raw"][agent] * 0.1)
        for item in ticks
        for agent in range(2)
    )
    with closing(sqlite3.connect(runner.db_path)) as connection:
        connection.row_factory = sqlite3.Row
        row = dict(connection.execute("SELECT * FROM episodes").fetchone())
    for agent in range(2):
        totals = {
            key: sum(float(item["components"][key][agent]) for item in ticks if bool(item["active"][agent]))
            for key in ("extrinsic", "intrinsic", "shaping")
        }
        total = sum(float(item["rewards"][agent]) for item in ticks if bool(item["active"][agent]))
        assert math.isclose(total, sum(totals.values()), rel_tol=1e-5, abs_tol=1e-6)
        for name, value in (("Total", total), *((name.title(), value) for name, value in totals.items())):
            assert acc.Scalars(f"agent_{agent}/Episode/{name}_Reward")[0].value == pytest.approx(value, rel=1e-5, abs=1e-6)
        if agent == 0:
            assert row["total_reward"] == pytest.approx(total, rel=1e-5, abs=1e-6)
            for name, value in totals.items():
                assert row[f"{name}_reward"] == pytest.approx(value, rel=1e-5, abs=1e-6)


def test_budget_six_retains_terminal_and_once_only_survivor_truncation(tmp_path: Path) -> None:
    runner, ticks, curricula = run_lane_runner(
        tmp_path / "run", episodes=1, budget=6, cap=None, end_ticks=(2, 5), real_dac=False, recording=False
    )
    assert len(ticks) == 4
    assert torch.stack([item["active"] for item in ticks]).sum(dim=0).tolist() == [2, 4]
    assert runner.completed_live_agent_steps == 6
    assert len(curricula) == 1
    assert runner.population is not None
    outcomes = runner.population.episode_completions
    assert [(item.survival_time, item.reason) for item in outcomes] == [(2, "authored_terminal"), (4, "budget")]
    replay = runner.population.replay_buffer
    assert len(replay) == 6
    assert replay.dones[:6].sum() == 1
    assert not replay.dones[5]
    assert runner.population.flush_episode(1, reason="checkpoint") is None


@pytest.mark.parametrize("end_ticks", [(2, 5), (5, 2)])
def test_caller_cap_keeps_authored_terminal_and_live_bootstrap(tmp_path: Path, end_ticks: tuple[int, int]) -> None:
    runner, ticks, curricula = run_lane_runner(
        tmp_path / "run", episodes=1, budget=None, cap=3, end_ticks=end_ticks, real_dac=False, recording=False
    )
    assert len(ticks) == 3
    expected = [min(ending, 3) for ending in end_ticks]
    assert torch.stack([item["active"] for item in ticks]).sum(dim=0).tolist() == expected
    assert runner.completed_live_agent_steps == 5
    assert len(curricula) == 1 and curricula[0][0].tolist() == expected
    assert runner.population is not None
    assert [(item.survival_time, item.reason) for item in runner.population.episode_completions] == [
        (count, "authored_terminal" if ending == 2 else "cap") for count, ending in zip(expected, end_ticks, strict=True)
    ]
    replay = runner.population.replay_buffer
    assert len(replay) == 5 and replay.dones[:5].sum() == 1 and not replay.dones[4]
    with closing(sqlite3.connect(runner.db_path)) as connection:
        row = connection.execute(
            "SELECT survival_time,batch_episode_steps,live_agent_transitions,completion_reason FROM episodes"
        ).fetchone()
    assert row == (expected[0], 3, 5, "authored_terminal" if end_ticks[0] == 2 else "cap")


def test_indivisible_zero_work_budget_publishes_no_episode(tmp_path: Path) -> None:
    runner, ticks, curricula = run_lane_runner(
        tmp_path / "run", episodes=1, budget=1, cap=None, end_ticks=(2, 5), real_dac=False, recording=True
    )
    assert not ticks and not curricula
    assert runner.current_episode == runner.completed_live_agent_steps == 0
    assert runner.environment_step_budget_shortfall == 1
    with closing(sqlite3.connect(runner.db_path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM episode_recordings").fetchone()[0] == 0
    acc = events_for(runner)
    assert not any("/Episode/" in tag for tag in acc.Tags()["scalars"])
    assert runner.population is not None
    assert all(item is None for item in runner.population.episode_completions)


def test_runner_publishes_owned_completion_meters_after_live_storage_changes(tmp_path: Path) -> None:
    original = VectorizedPopulation.update_curriculum_tracker

    def mutate_storage(population, survival_times, dones):
        result = original(population, survival_times, dones)
        population.env.meters.add_(0.25)
        return result

    # Explicit aliasing control after completion, rather than authored state.
    with patch.object(VectorizedPopulation, "update_curriculum_tracker", mutate_storage):
        runner, ticks, _ = run_lane_runner(
            tmp_path / "run", episodes=1, budget=None, cap=None, end_ticks=(2, 5), real_dac=False, recording=False
        )
    acc = events_for(runner)
    for agent, ending in enumerate((2, 5)):
        expected = ticks[ending - 1]["meters"][agent]
        assert not torch.equal(expected, runner.env.meters[agent])
        for meter_index, name in enumerate(runner.env.bars_config.meter_names):
            event = acc.Scalars(f"agent_{agent}/Meters/{name.capitalize()}")[0]
            assert event.step == ending
            assert event.value == pytest.approx(float(expected[meter_index]))


def test_caller_cap_completes_lanes_before_curriculum_publication(tmp_path: Path) -> None:
    original = VectorizedPopulation.update_curriculum_tracker

    def require_completions(population, survival_times, dones):
        assert all(item is not None for item in population.episode_completions)
        assert [item.reason for item in population.episode_completions] == ["authored_terminal", "cap"]
        return original(population, survival_times, dones)

    with patch.object(VectorizedPopulation, "update_curriculum_tracker", require_completions):
        run_lane_runner(tmp_path / "run", episodes=1, budget=None, cap=3, end_ticks=(2, 5), real_dac=False, recording=False)
