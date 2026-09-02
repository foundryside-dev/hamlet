"""DemoRunner seeds the run from training config (hamlet-834108b55a).

The seed is declared in training.yaml (required field), the runner pushes it
through the single seeding door at construction — before anything random is
built — and the checkpoint carries it via the persisted training config, so a
run is reproducible from its own artifact.
"""

import random
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from townlet.curriculum.static import StaticCurriculum
from townlet.demo.runner import DemoRunner
from townlet.determinism import seed_all
from townlet.training.checkpoint_utils import DEMO_CHECKPOINT_KEYS, persist_checkpoint_digest

CONFIG_DIR = Path("configs/test/model_config")
LEVEL = "L0_test"
PACK_SEED = 42  # declared in configs/test/model_config/levels/L0_test/training.yaml


def _make_runner(tmp_path: Path) -> DemoRunner:
    return DemoRunner(
        config_dir=CONFIG_DIR,
        db_path=tmp_path / "test.db",
        checkpoint_dir=tmp_path / "checkpoints",
        max_episodes=1,
        level_name=LEVEL,
    )


class _CheckpointSubstrate:
    position_dim = 2


class _CheckpointEnv:
    substrate = _CheckpointSubstrate()

    @staticmethod
    def get_affordance_positions() -> dict[str, tuple[int, int]]:
        return {}

    @staticmethod
    def validate_affordance_positions(_positions: dict[str, tuple[int, int]]) -> None:
        return None

    @staticmethod
    def set_affordance_positions(_positions: dict[str, tuple[int, int]]) -> None:
        raise AssertionError("outer schema validation must run before environment mutation")


class _CheckpointPopulation:
    num_agents = 1
    agent_ids = ["agent_0"]

    def __init__(self) -> None:
        self.load_calls = 0

    @staticmethod
    def get_checkpoint_state() -> dict[str, Any]:
        return {"synthetic": "population"}

    @staticmethod
    def _get_current_epsilon_value() -> float:
        return 0.25

    @staticmethod
    def validate_checkpoint_state(_state: dict[str, Any]) -> None:
        return None

    def load_checkpoint_state(self, _state: dict[str, Any]) -> None:
        self.load_calls += 1

    @staticmethod
    def flush_episode(_agent_idx: int) -> None:
        return None


class _CheckpointCurriculum:
    @staticmethod
    def checkpoint_state() -> dict[str, Any]:
        return {"synthetic": "curriculum"}

    @staticmethod
    def validate_checkpoint_state(_state: dict[str, Any]) -> None:
        return None

    @staticmethod
    def load_state(_state: dict[str, Any]) -> None:
        raise AssertionError("outer schema validation must run before curriculum mutation")


def _initialize_checkpoint_components(runner: DemoRunner) -> _CheckpointPopulation:
    population = _CheckpointPopulation()
    runner.env = _CheckpointEnv()  # type: ignore[assignment]
    runner.population = population  # type: ignore[assignment]
    runner.curriculum = _CheckpointCurriculum()  # type: ignore[assignment]
    return population


def test_runner_init_seeds_every_stream_from_training_config(tmp_path: Path) -> None:
    """After construction, all three RNG streams sit in the seed_all(seed) state."""
    # Deliberately scramble every stream so a runner that fails to seed cannot pass.
    random.seed(999)
    np.random.seed(999)
    torch.manual_seed(999)

    runner = _make_runner(tmp_path)
    try:
        observed = (random.random(), float(np.random.rand()), torch.rand(4).tolist())
    finally:
        runner._cleanup()

    seed_all(PACK_SEED)
    expected = (random.random(), float(np.random.rand()), torch.rand(4).tolist())
    assert observed == expected


def test_checkpoint_carries_the_seed(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    try:
        _initialize_checkpoint_components(runner)
        runner.save_checkpoint()
        checkpoint_path = next((tmp_path / "checkpoints").glob("checkpoint_ep*.pt"))
        checkpoint = torch.load(checkpoint_path, weights_only=True)
    finally:
        runner._cleanup()

    assert checkpoint["training_config"]["seed"] == PACK_SEED
    assert set(checkpoint) == DEMO_CHECKPOINT_KEYS


def test_checkpoint_save_requires_initialized_components_before_flushing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _make_runner(tmp_path)
    flushed = False

    def _record_flush() -> None:
        nonlocal flushed
        flushed = True

    monkeypatch.setattr(runner, "flush_all_agents", _record_flush)
    try:
        with pytest.raises(RuntimeError, match="env, population, and curriculum"):
            runner.save_checkpoint()
    finally:
        runner._cleanup()

    assert flushed is False
    assert list((tmp_path / "checkpoints").glob("checkpoint_ep*.pt")) == []


def test_checkpoint_load_requires_initialized_components_even_without_files(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    try:
        with pytest.raises(RuntimeError, match="env, population, and curriculum"):
            runner.load_checkpoint()
    finally:
        runner._cleanup()


@pytest.mark.parametrize("schema_change", ("missing", "unknown"))
def test_runner_load_refuses_outer_schema_change_before_mutation(tmp_path: Path, schema_change: str) -> None:
    runner = _make_runner(tmp_path)
    try:
        _initialize_checkpoint_components(runner)
        runner.current_episode = 7
        runner.save_checkpoint()
        checkpoint_path = next((tmp_path / "checkpoints").glob("checkpoint_ep*.pt"))
        checkpoint = torch.load(checkpoint_path, weights_only=False)
        if schema_change == "missing":
            checkpoint.pop("epsilon")
        else:
            checkpoint["legacy_epsilon"] = 0.5
        torch.save(checkpoint, checkpoint_path)
        persist_checkpoint_digest(checkpoint_path)
        runner.current_episode = 99

        with pytest.raises(ValueError, match="Demo checkpoint key set mismatch"):
            runner.load_checkpoint()

        assert runner.current_episode == 99
    finally:
        runner._cleanup()


def test_runner_refuses_malformed_curriculum_before_population_mutation(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    try:
        population = _initialize_checkpoint_components(runner)
        curriculum = StaticCurriculum()
        curriculum.initialize_population(1)
        runner.curriculum = curriculum
        runner.current_episode = 7
        runner.save_checkpoint()
        checkpoint_path = next((tmp_path / "checkpoints").glob("checkpoint_ep*.pt"))
        checkpoint = torch.load(checkpoint_path, weights_only=False)
        checkpoint["curriculum_state"].pop("reward_mode")
        torch.save(checkpoint, checkpoint_path)
        persist_checkpoint_digest(checkpoint_path)

        with pytest.raises(ValueError, match="Static curriculum checkpoint key set mismatch"):
            runner.load_checkpoint()

        assert population.load_calls == 0
    finally:
        runner._cleanup()
