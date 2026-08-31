"""DemoRunner contracts for the summed-live-agent transition budget."""

from pathlib import Path

import pytest

from townlet.demo.runner import DemoRunner, decide_live_agent_budget


def test_budget_advances_only_when_whole_vector_step_fits() -> None:
    assert decide_live_agent_budget(completed=0, live_agents=8, budget=16) == (True, 0)
    assert decide_live_agent_budget(completed=8, live_agents=8, budget=16) == (True, 0)
    assert decide_live_agent_budget(completed=16, live_agents=8, budget=16) == (False, 0)


def test_unreachable_remainder_stops_before_overshoot() -> None:
    assert decide_live_agent_budget(completed=15, live_agents=2, budget=16) == (False, 1)


@pytest.mark.parametrize(
    ("completed", "live_agents", "budget"),
    [(-1, 1, 1), (0, 0, 1), (0, 1, 0), (2, 1, 1), (False, 1, 1), (0, True, 1), (0, 1, True)],
)
def test_invalid_budget_state_refuses(completed: int | bool, live_agents: int | bool, budget: int | bool) -> None:
    with pytest.raises(ValueError):
        decide_live_agent_budget(completed=completed, live_agents=live_agents, budget=budget)


def test_runner_stops_before_partial_vector_step(tmp_path: Path) -> None:
    """An eight-agent environment must not take a partial step for budget one."""
    runner = DemoRunner(
        config_dir=Path("configs/test/model_config"),
        db_path=tmp_path / "demo.db",
        checkpoint_dir=tmp_path / "checkpoints",
        max_episodes=1,
        level_name="L0_test",
        max_environment_steps=1,
    )

    runner.run()

    assert runner.completed_live_agent_steps == 0
    assert runner.environment_step_budget_shortfall == 1
    assert runner.environment_step_budget_reached is True
    assert runner.current_episode == 0


def test_budget_counter_round_trips_and_prevents_resume_overshoot(tmp_path: Path) -> None:
    checkpoint_dir = tmp_path / "checkpoints"
    first = DemoRunner(
        config_dir=Path("configs/test/model_config"),
        db_path=tmp_path / "first.db",
        checkpoint_dir=checkpoint_dir,
        max_episodes=1,
        level_name="L0_test",
        max_environment_steps=8,
    )
    first.run()
    assert first.completed_live_agent_steps == 8

    resumed = DemoRunner(
        config_dir=Path("configs/test/model_config"),
        db_path=tmp_path / "resumed.db",
        checkpoint_dir=checkpoint_dir,
        max_episodes=2,
        level_name="L0_test",
        max_environment_steps=8,
    )
    resumed.run()

    assert resumed.completed_live_agent_steps == 8
    assert resumed.environment_step_budget_shortfall == 0
    assert resumed.environment_step_budget_reached is True
