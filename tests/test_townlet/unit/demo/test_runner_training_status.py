"""DemoRunner records how training actually ended, never a blanket ``completed``."""

import sqlite3
from pathlib import Path

import pytest

import townlet.demo.runner as runner_module
from townlet.demo.runner import DemoRunner, resolve_training_status


def _training_status(db_path: Path) -> str:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT value FROM system_state WHERE key = 'training_status'").fetchone()[0]
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"failed": False, "should_shutdown": False, "budget_reached": True, "episodes_reached": False}, "completed"),
        ({"failed": False, "should_shutdown": False, "budget_reached": False, "episodes_reached": True}, "completed"),
        ({"failed": False, "should_shutdown": True, "budget_reached": True, "episodes_reached": False}, "completed"),
        ({"failed": False, "should_shutdown": True, "budget_reached": False, "episodes_reached": False}, "interrupted"),
        ({"failed": False, "should_shutdown": True, "budget_reached": False, "episodes_reached": True}, "interrupted"),
        ({"failed": True, "should_shutdown": True, "budget_reached": True, "episodes_reached": True}, "failed"),
    ],
)
def test_status_follows_the_terminal_cause(kwargs: dict[str, bool], expected: str) -> None:
    assert resolve_training_status(**kwargs) == expected


def test_loop_exit_without_terminal_cause_refuses() -> None:
    with pytest.raises(ValueError):
        resolve_training_status(failed=False, should_shutdown=False, budget_reached=False, episodes_reached=False)


def test_budget_completion_records_completed(tmp_path: Path) -> None:
    runner = DemoRunner(
        config_dir=Path("configs/test/model_config"),
        db_path=tmp_path / "demo.db",
        checkpoint_dir=tmp_path / "checkpoints",
        max_episodes=1,
        level_name="L0_test",
        max_environment_steps=8,
    )
    runner.run()
    assert _training_status(tmp_path / "demo.db") == "completed"


def test_graceful_stop_before_budget_records_interrupted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = DemoRunner(
        config_dir=Path("configs/test/model_config"),
        db_path=tmp_path / "demo.db",
        checkpoint_dir=tmp_path / "checkpoints",
        max_episodes=1,
        level_name="L0_test",
        max_environment_steps=10_000,
    )

    def stop_after_first_vector_step(*, completed: int, live_agents: int, budget: int) -> tuple[bool, int]:
        runner.should_shutdown = True
        return True, 0

    monkeypatch.setattr(runner_module, "decide_live_agent_budget", stop_after_first_vector_step)
    runner.run()

    assert runner.environment_step_budget_reached is False
    assert 0 < runner.completed_live_agent_steps < 10_000
    assert _training_status(tmp_path / "demo.db") == "interrupted"


def test_training_error_records_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = DemoRunner(
        config_dir=Path("configs/test/model_config"),
        db_path=tmp_path / "demo.db",
        checkpoint_dir=tmp_path / "checkpoints",
        max_episodes=1,
        level_name="L0_test",
        max_environment_steps=8,
    )

    def explode(*, completed: int, live_agents: int, budget: int) -> tuple[bool, int]:
        raise RuntimeError("boom")

    monkeypatch.setattr(runner_module, "decide_live_agent_budget", explode)
    with pytest.raises(RuntimeError, match="boom"):
        runner.run()
    assert _training_status(tmp_path / "demo.db") == "failed"
