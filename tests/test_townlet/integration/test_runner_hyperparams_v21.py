"""Integration test for v2.1 DemoRunner training loop hyperparameters.

This test builds a minimal v2.1 experiment by copying the default_curriculum
configs, adding a brain.yaml, and then asserting that levels/<level>/training.yaml
training_loop hyperparameters are threaded into VectorizedPopulation.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import mutate_brain_yaml
from townlet.demo.runner import DemoRunner
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.population.vectorized import VectorizedPopulation


@pytest.mark.integration
def test_demorunner_threads_training_loop_hyperparameters(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DemoRunner should honor training_loop hyperparameters from training.yaml."""

    # Prepare v2.1 experiment: copy default_curriculum into a temp directory.
    project_root = Path(__file__).parent.parent.parent.parent
    src_experiment = project_root / "configs" / "default_curriculum"
    experiment_dir = tmp_path / "experiment"
    shutil.copytree(src_experiment, experiment_dir)

    # Ensure brain.yaml uses huber loss with explicit delta (no hidden defaults).
    mutate_brain_yaml(experiment_dir, lambda brain: brain.update({"loss": {"type": "huber", "huber_delta": 1.0}}))

    level_name = "L0_0_minimal"
    training_path = experiment_dir / "levels" / level_name / "training.yaml"

    # Mutate training_loop hyperparameters for this test.
    training_data = yaml.safe_load(training_path.read_text())
    training_data["training"]["training_loop"]["train_frequency"] = 7
    training_data["training"]["training_loop"]["sequence_length"] = 5
    training_data["training"]["training_loop"]["max_grad_norm"] = 3.5
    training_path.write_text(yaml.safe_dump(training_data, sort_keys=False))

    db_path = tmp_path / "test.db"
    checkpoint_dir = tmp_path / "checkpoints"

    # Patch VectorizedHamletEnv.from_universe to avoid full runtime wiring.
    class DummyEnv:
        def __init__(self) -> None:
            class _ObsActivity:
                active_mask = (True,)

            class _Substrate:
                position_dim = 2
                position_dtype = None  # Not used by this test

            self.observation_activity = _ObsActivity()
            self.substrate = _Substrate()
            self.meter_count = 8
            self.num_affordance_types = 1
            self.action_dim = 4

        def attach_runtime_registry(self, registry) -> None:  # pragma: no cover - simple stub
            pass

        def set_exploration_module(self, exploration) -> None:  # pragma: no cover - simple stub
            pass

    monkeypatch.setattr(
        VectorizedHamletEnv,
        "from_universe",
        classmethod(lambda cls, universe, level_name, num_agents, device: DummyEnv()),
    )

    captured: dict[str, float] = {}

    def fake_population_init(
        self,
        env,
        curriculum,
        exploration,
        agent_ids,
        device,
        brain_config,
        obs_dim: int = 70,
        action_dim: int | None = None,
        vision_window_size: int = 5,
        tb_logger=None,
        train_frequency: int = 4,
        batch_size: int | None = None,
        sequence_length: int = 8,
        max_grad_norm: float = 10.0,
        max_episodes: int | None = None,
        max_steps_per_episode: int | None = None,
        observation_spec=None,
    ) -> None:
        captured["train_frequency"] = train_frequency
        captured["sequence_length"] = sequence_length
        captured["max_grad_norm"] = max_grad_norm
        # Stop runner.run() after population construction.
        raise RuntimeError("stop-after-population-init")

    monkeypatch.setattr(VectorizedPopulation, "__init__", fake_population_init)

    runner = DemoRunner(
        config_dir=experiment_dir,
        level_name=level_name,
        db_path=db_path,
        checkpoint_dir=checkpoint_dir,
        max_episodes=1,
    )

    with pytest.raises(RuntimeError, match="stop-after-population-init"):
        runner.run()

    # VectorizedPopulation.__init__ should receive the overridden hyperparameters.
    assert captured["train_frequency"] == 7
    assert captured["sequence_length"] == 5
    assert captured["max_grad_norm"] == pytest.approx(3.5)
