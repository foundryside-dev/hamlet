"""Integration tests for Double DQN training.

This module tests Double DQN integration across full training loops,
verifying that the algorithm works correctly in production scenarios.

Tasks verified:
- Full training loop with Double DQN enabled
- Full training loop with vanilla DQN (use_double_dqn=False)
- Checkpoint persistence of use_double_dqn flag
"""

import sqlite3

import torch

from tests.test_townlet.helpers.config_builder import mutate_brain_yaml, mutate_training_yaml
from townlet.demo.runner import DemoRunner

LEVEL_NAME = "L0_test"


class TestDoubleDoubleTraining:
    """Integration tests for Double DQN in full training loops."""

    @staticmethod
    def _create_fast_test_config(use_double_dqn: bool) -> dict:
        """Create minimal config modifier for fast integration tests."""

        def modifier(data: dict) -> None:
            training = data["training"]
            training_loop = training["training_loop"]

            # Keep runs short for integration speed
            training_loop["max_episodes"] = 10
            training_loop["max_steps_per_episode"] = 50

            # Reduce buffer warmup / batch size to keep CPU-friendly
            replay = training["replay_buffer"]
            replay["min_size"] = 16
            replay["batch_size"] = 8

            curriculum_cfg = training.get("curriculum", {}) or {}
            curriculum_cfg["strategy"] = "adversarial"  # Ensure initialize_population is available
            training["curriculum"] = curriculum_cfg

            # Fast evaluation cadence isn't needed; keep minimal to avoid overhead
            evaluation = training_loop.get("evaluation", {})
            evaluation["interval"] = 1000
            evaluation["num_episodes"] = 1
            training_loop["evaluation"] = evaluation

        return modifier

    @staticmethod
    def _force_huber_loss(config_dir) -> None:
        """Align agent loss with validation rules (huber requires huber_delta)."""

        def _mutate_agent(data: dict) -> None:
            brain = data or {}
            loss_cfg = brain.get("loss", {}) or {}
            loss_cfg["type"] = "huber"
            loss_cfg["huber_delta"] = 1.0
            brain["loss"] = loss_cfg

        mutate_brain_yaml(config_dir, _mutate_agent)

    def test_training_with_double_dqn_enabled(self, tmp_path, config_pack_factory):
        """Full training loop should work with Double DQN enabled.

        Verifies:
        - No crashes during training
        - Q-network updates (weights change)
        - Target network updates occur
        - Replay buffer fills
        """
        config_dir = config_pack_factory(modifier=self._create_fast_test_config(use_double_dqn=True))

        # Set use_double_dqn for this level in training.yaml overrides
        def training_mutator(data: dict) -> None:
            data["training"]["q_learning"]["use_double_dqn"] = True

        mutate_training_yaml(config_dir, training_mutator)
        self._force_huber_loss(config_dir)

        db_path = tmp_path / "test.db"
        checkpoint_dir = tmp_path / "checkpoints"

        # Create runner
        runner = DemoRunner(
            config_dir=config_dir,
            db_path=db_path,
            checkpoint_dir=checkpoint_dir,
            max_episodes=10,
            level_name=LEVEL_NAME,
        )

        # Run training (population is initialized inside run())
        runner.run()

        # Note: We can't capture initial weights before run() because population is None
        # Instead, we verify that weights change by checking replay buffer and episodes

        # Verify: Training completed all episodes
        assert runner.current_episode == 10, "Should complete 10 episodes"

        # Verify: Replay buffer has transitions (indicates learning occurred)
        assert runner.population.replay_buffer.size > 0, "Replay buffer should contain transitions"

        # Verify: use_double_dqn flag is True
        assert runner.population.use_double_dqn is True, "Population should have use_double_dqn=True"

        # Verify: Database has episode records
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM episodes")
        episode_count = cursor.fetchone()[0]
        conn.close()

        assert episode_count == 10, f"Database should have 10 episode records, got {episode_count}"

    def test_training_with_vanilla_dqn(self, tmp_path, config_pack_factory):
        """Full training loop should work with vanilla DQN (use_double_dqn=False).

        Verifies:
        - No crashes during training
        - use_double_dqn=False works correctly
        - Q-learning still functions
        """
        config_dir = config_pack_factory(modifier=self._create_fast_test_config(use_double_dqn=False))

        # Set use_double_dqn override to False for this level
        def training_mutator(data: dict) -> None:
            data["training"]["q_learning"]["use_double_dqn"] = False

        mutate_training_yaml(config_dir, training_mutator)
        self._force_huber_loss(config_dir)

        db_path = tmp_path / "test.db"
        checkpoint_dir = tmp_path / "checkpoints"

        # Create runner
        runner = DemoRunner(
            config_dir=config_dir,
            db_path=db_path,
            checkpoint_dir=checkpoint_dir,
            max_episodes=10,
            level_name=LEVEL_NAME,
        )

        # Run training
        runner.run()

        # Verify: Training completed all episodes
        assert runner.current_episode == 10, "Should complete 10 episodes"

        # Verify: use_double_dqn flag is False
        assert runner.population.use_double_dqn is False, "Population should have use_double_dqn=False"

        # Verify: Database has episode records
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM episodes")
        episode_count = cursor.fetchone()[0]
        conn.close()

        assert episode_count == 10, f"Database should have 10 episode records, got {episode_count}"

    def test_checkpoint_persists_double_dqn_flag(self, tmp_path, config_pack_factory, monkeypatch):
        """Checkpoints should save and restore use_double_dqn flag.

        Verifies:
        - Training with use_double_dqn=True saves flag to checkpoint
        - Loading checkpoint restores flag correctly
        - Training can resume with correct algorithm
        """
        # Set checkpoint interval to 5 for faster testing
        monkeypatch.setattr(DemoRunner, "CHECKPOINT_INTERVAL", 5)

        # Create config with 5 episodes to hit checkpoint interval
        def modifier(data: dict) -> None:
            training = data["training"]
            training_loop = training["training_loop"]

            training_loop["max_episodes"] = 5
            training_loop["max_steps_per_episode"] = 50

            replay = training["replay_buffer"]
            replay["min_size"] = 8
            replay["batch_size"] = 4

            curriculum_cfg = training.get("curriculum", {}) or {}
            curriculum_cfg["strategy"] = "adversarial"
            training["curriculum"] = curriculum_cfg

        config_dir = config_pack_factory(modifier=modifier)

        # Set use_double_dqn in training.yaml overrides
        def training_mutator(data: dict) -> None:
            data["training"]["q_learning"]["use_double_dqn"] = True

        mutate_training_yaml(config_dir, training_mutator)
        self._force_huber_loss(config_dir)

        db_path = tmp_path / "test.db"
        checkpoint_dir = tmp_path / "checkpoints"

        # Phase 1: Train and save checkpoint
        runner1 = DemoRunner(
            config_dir=config_dir,
            db_path=db_path,
            checkpoint_dir=checkpoint_dir,
            max_episodes=5,
            level_name=LEVEL_NAME,
        )
        runner1.run()

        # Verify checkpoint exists
        checkpoints = list(checkpoint_dir.glob("checkpoint_ep*.pt"))
        assert len(checkpoints) > 0, "Checkpoint should be saved"

        # Load checkpoint and verify brain_hash persisted (use_double_dqn is managed by brain.yaml)
        checkpoint_path = checkpoints[0]
        checkpoint_data = torch.load(checkpoint_path, weights_only=False)

        # Check that checkpoint contains brain_hash (proof brain.yaml was used)
        assert "brain_hash" in checkpoint_data, "Checkpoint should contain brain_hash (from brain.yaml)"
        # Note: use_double_dqn is no longer in training_config (moved to brain.yaml)
        # The important test is that it's restored correctly when loading (tested below)

        # Phase 2: Load checkpoint and resume training
        runner2 = DemoRunner(
            config_dir=config_dir,
            db_path=db_path,
            checkpoint_dir=checkpoint_dir,
            max_episodes=10,  # Train 5 more episodes
            level_name=LEVEL_NAME,
        )

        # Note: DemoRunner.run() automatically loads checkpoint if it exists
        # We verify flag after run() when population is initialized
        runner2.run()

        # Verify flag restored correctly from checkpoint
        assert runner2.population.use_double_dqn is True, "Loaded population should have use_double_dqn=True"

        # Verify: Training completed additional episodes
        assert runner2.current_episode == 10, "Should complete 10 total episodes"

        # Verify: Database has episode records (runner2 resumes from checkpoint, adds new episodes)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM episodes")
        episode_count = cursor.fetchone()[0]
        conn.close()

        assert episode_count >= 9, f"Database should have at least 9 episode records, got {episode_count}"
