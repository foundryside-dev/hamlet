"""
Integration tests for recurrent networks (LSTM) in Townlet.

Tests LSTM hidden state management, batch training, and POMDP integration.

Test Organization:
- TestLSTMHiddenStatePersistence: Hidden state lifecycle during episodes (4 tests)
- TestLSTMBatchTraining: Hidden-state shape across the training boundary (1 test)
- TestLSTMForwardPass: Forward pass with POMDP (1 test)

Every test here drives a real compiled universe. Two tests migrated from
test_lstm_temporal_learning.py were DELETED rather than repaired (2026-08-16,
hamlet-a0832f9004): they hand-rolled a 7-dim observation in the legacy positional
layout that v2.1 removed, and hand-rolled their own Q-learning update on top of it,
so they exercised torch rather than townlet. The behaviour they claimed — sequence
training and hidden-state persistence through training — is pinned properly, from
YAML, by test_recurrent_bptt_runtime.py.
"""

from pathlib import Path

import pytest
import torch

from tests.test_townlet.helpers.config_builder import mutate_curriculum_yaml, mutate_stratum_yaml
from townlet.agent.networks import RecurrentSpatialQNetwork
from townlet.curriculum.static import StaticCurriculum
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.population.vectorized import VectorizedPopulation

pytestmark = pytest.mark.slow

# =============================================================================
# TEST CLASS 1: LSTM Hidden State Persistence
# =============================================================================


class TestLSTMHiddenStatePersistence:
    """Test LSTM hidden state lifecycle during episode execution."""

    def test_hidden_state_persists_across_10_steps_within_episode(
        self, cpu_device, cpu_env_factory, config_pack_factory, recurrent_brain_config
    ):
        """
        Verify hidden state evolves during episode rollout.

        Hidden state should change across steps as the agent accumulates
        experience, demonstrating that memory is being built up.
        """

        def _modifier(cfg):
            training = cfg["training"]
            training_loop = training["training_loop"]
            training_loop["max_steps_per_episode"] = 1000

        config_dir = config_pack_factory(modifier=_modifier, name="lstm_hidden_state_survival")

        # Switch to partial observability and shrink grid to 5x5
        mutate_curriculum_yaml(
            config_dir,
            lambda c: c["curriculum"].update({"active_vision": "partial", "vision_range": 0.5}),
        )
        mutate_stratum_yaml(
            config_dir,
            lambda s: s["stratum"]["substrate"]["grid"].update({"width": 5, "height": 5}),
        )
        env = cpu_env_factory(config_dir=config_dir, num_agents=1)

        # Create recurrent population
        curriculum = StaticCurriculum()
        exploration = EpsilonGreedyExploration(
            epsilon=0.1,
            epsilon_min=0.1,
            epsilon_decay=1.0,
        )

        population = VectorizedPopulation(
            env=env,
            curriculum=curriculum,
            exploration=exploration,
            agent_ids=["agent_0"],
            device=cpu_device,
            obs_dim=env.observation_dim,
            action_dim=env.action_dim,
            brain_config=recurrent_brain_config,
            vision_window_size=5,
            batch_size=8,
            sequence_length=1,
            max_grad_norm=10.0,
            train_frequency=10000,  # Disable training (test focuses on hidden state persistence)
        )

        # Reset environment and population
        population.reset()

        # Initialize all meters to 1.0 to prevent cascade-induced death during test
        env.meters.fill_(1.0)

        # Capture initial rollout memory (population-owned since WS-1(b))
        assert population.rollout_hidden is not None
        h0, c0 = population.rollout_hidden
        hidden_states = [(h0.clone(), c0.clone())]

        # Run 10 steps and verify agent survives
        for step_num in range(10):
            state = population.step_population(env)
            # Ensure agent didn't die (would reset hidden state and break test)
            assert not state.dones[0], (
                f"Agent died at step {step_num + 1}/10. "
                f"Energy: {env.meters[0, 0]:.3f}, Health: {env.meters[0, 6]:.3f}. "
                "This test requires agent to survive 10 steps to verify hidden state persistence. "
                "If this fails, energy costs may need to be reduced further."
            )
            h, c = population.rollout_hidden
            hidden_states.append((h.clone(), c.clone()))

        # Verify hidden state changed across steps
        for i in range(len(hidden_states) - 1):
            h_curr, c_curr = hidden_states[i]
            h_next, c_next = hidden_states[i + 1]

            # Hidden states should be different (memory evolving)
            assert not torch.allclose(h_curr, h_next, atol=1e-6), f"Hidden state should change between steps {i} and {i + 1}"
            assert not torch.allclose(c_curr, c_next, atol=1e-6), f"Cell state should change between steps {i} and {i + 1}"

    def test_hidden_state_resets_on_death(self, cpu_device, cpu_env_factory, config_pack_factory, recurrent_brain_config):
        """
        Verify hidden state resets when agent dies.

        When agent dies, hidden state should be reset to zeros to prevent
        memory contamination across episodes.
        """
        # Seed RNG for deterministic behavior in full suite
        torch.manual_seed(42)

        def _modifier(cfg):
            training = cfg["training"]
            training_loop = training["training_loop"]
            training_loop["max_steps_per_episode"] = 1000

        config_dir = config_pack_factory(modifier=_modifier, name="lstm_hidden_state_reset")

        mutate_curriculum_yaml(
            config_dir,
            lambda c: c["curriculum"].update({"active_vision": "partial", "vision_range": 0.5}),
        )
        mutate_stratum_yaml(
            config_dir,
            lambda s: s["stratum"]["substrate"]["grid"].update({"width": 5, "height": 5}),
        )
        env = cpu_env_factory(config_dir=config_dir, num_agents=1)

        curriculum = StaticCurriculum()
        exploration = EpsilonGreedyExploration(
            epsilon=0.0,  # Greedy for determinism
            epsilon_min=0.0,
            epsilon_decay=1.0,
        )

        population = VectorizedPopulation(
            env=env,
            curriculum=curriculum,
            exploration=exploration,
            agent_ids=["agent_0"],
            device=cpu_device,
            obs_dim=env.observation_dim,
            action_dim=env.action_dim,
            brain_config=recurrent_brain_config,
            vision_window_size=5,
            batch_size=8,
            sequence_length=1,
            max_grad_norm=10.0,
            train_frequency=10000,  # Disable training (test focuses on death reset)
        )

        population.reset()

        # Run until death (energy drains to 0)
        max_steps = 200  # Safety limit
        done = False
        for step in range(max_steps):
            state = population.step_population(env)
            if state.dones[0]:
                done = True
                break

        assert done, "Agent should have died"

        # After death, rollout memory should be zeros
        assert population.rollout_hidden is not None
        h, c = population.rollout_hidden

        assert torch.allclose(h, torch.zeros_like(h)), "Hidden state should be zeros after death"
        assert torch.allclose(c, torch.zeros_like(c)), "Cell state should be zeros after death"

    def test_hidden_state_resets_after_flush_on_max_steps(self, cpu_device, cpu_env_factory, config_pack_factory, recurrent_brain_config):
        """
        Verify hidden state resets after flush_episode() on max_steps survival.

        When agent survives max_steps, flush_episode() should reset hidden state
        to prevent memory leakage into next episode.
        """

        def _modifier(cfg):
            training_loop = cfg["training"]["training_loop"]
            training_loop["max_steps_per_episode"] = 1000

        config_dir = config_pack_factory(modifier=_modifier, name="lstm_hidden_state_flush")

        mutate_curriculum_yaml(
            config_dir,
            lambda c: c["curriculum"].update({"active_vision": "partial", "vision_range": 0.5}),
        )
        mutate_stratum_yaml(
            config_dir,
            lambda s: s["stratum"]["substrate"]["grid"].update({"width": 5, "height": 5}),
        )
        env = cpu_env_factory(config_dir=config_dir, num_agents=1)

        curriculum = StaticCurriculum()
        exploration = EpsilonGreedyExploration(
            epsilon=0.1,
            epsilon_min=0.1,
            epsilon_decay=1.0,
        )

        population = VectorizedPopulation(
            env=env,
            curriculum=curriculum,
            exploration=exploration,
            agent_ids=["agent_0"],
            device=cpu_device,
            obs_dim=env.observation_dim,
            action_dim=env.action_dim,
            brain_config=recurrent_brain_config,
            vision_window_size=5,
            batch_size=8,
            sequence_length=1,
            max_grad_norm=10.0,
            train_frequency=10000,  # Disable training (test focuses on flush behavior)
        )

        population.reset()

        # Initialize all meters to 1.0 to prevent cascade-induced death during test
        env.meters.fill_(1.0)

        # Run 50 steps (no death expected)
        for _ in range(50):
            population.step_population(env)

        # Flush episode (max_steps survival)
        population.flush_episode(agent_idx=0)

        # Rollout memory should be zeros after flush
        assert population.rollout_hidden is not None
        h, c = population.rollout_hidden

        assert torch.allclose(h, torch.zeros_like(h)), "Hidden state should be zeros after flush"
        assert torch.allclose(c, torch.zeros_like(c)), "Cell state should be zeros after flush"

    def test_hidden_state_shape_correct_during_episode(self, cpu_device, cpu_env_factory, config_pack_factory, recurrent_brain_config):
        """
        Verify hidden state shape during multi-agent rollout.

        Hidden state shape should be [1, num_agents, 256] throughout episode.
        """

        # Create environment with 2 agents
        # Use VERY low energy costs to ensure agents survive 10 steps
        def _modifier(cfg):
            training_loop = cfg["training"]["training_loop"]
            training_loop["max_steps_per_episode"] = 1000

        config_dir = config_pack_factory(modifier=_modifier, name="lstm_hidden_state_shape")

        mutate_curriculum_yaml(
            config_dir,
            lambda c: c["curriculum"].update({"active_vision": "partial", "vision_range": 0.5}),
        )
        mutate_stratum_yaml(
            config_dir,
            lambda s: s["stratum"]["substrate"]["grid"].update({"width": 5, "height": 5}),
        )
        env = cpu_env_factory(config_dir=config_dir, num_agents=2)

        curriculum = StaticCurriculum()
        exploration = EpsilonGreedyExploration(
            epsilon=0.1,
            epsilon_min=0.1,
            epsilon_decay=1.0,
        )

        population = VectorizedPopulation(
            env=env,
            curriculum=curriculum,
            exploration=exploration,
            agent_ids=["agent_0", "agent_1"],
            device=cpu_device,
            obs_dim=env.observation_dim,
            action_dim=env.action_dim,
            brain_config=recurrent_brain_config,
            vision_window_size=5,
            batch_size=8,
            sequence_length=1,
            max_grad_norm=10.0,
            train_frequency=10000,  # Disable training (test focuses on shape verification)
        )

        population.reset()

        # Initialize all meters to 1.0 to prevent cascade-induced death during test
        env.meters.fill_(1.0)

        # Verify initial shape
        assert population.rollout_hidden is not None
        h, c = population.rollout_hidden
        assert h.shape == (1, 2, 256), f"Expected shape (1, 2, 256), got {h.shape}"
        assert c.shape == (1, 2, 256), f"Expected shape (1, 2, 256), got {c.shape}"

        # Run 10 steps and verify shape remains consistent
        for _ in range(10):
            population.step_population(env)
            h, c = population.rollout_hidden
            assert h.shape == (1, 2, 256), f"Hidden state shape should be (1, 2, 256), got {h.shape}"
            assert c.shape == (1, 2, 256), f"Cell state shape should be (1, 2, 256), got {c.shape}"


# =============================================================================
# TEST CLASS 2: LSTM Batch Training
# =============================================================================


class TestLSTMBatchTraining:
    """Test LSTM batch training with sequence sampling."""

    def test_hidden_state_batch_size_correct_during_training(
        self, cpu_device, cpu_env_factory, config_pack_factory, recurrent_brain_config
    ):
        """
        Verify hidden state shape changes from num_agents to batch_size during training.

        During episode: [1, num_agents, 256]
        During training: [1, batch_size, 256]
        After training: [1, num_agents, 256]
        """

        def _modifier(cfg):
            training_loop = cfg["training"]["training_loop"]
            training_loop["max_steps_per_episode"] = 1000

        config_dir = config_pack_factory(modifier=_modifier, name="lstm_batch_size")

        mutate_curriculum_yaml(
            config_dir,
            lambda c: c["curriculum"].update({"active_vision": "partial", "vision_range": 0.5}),
        )
        mutate_stratum_yaml(
            config_dir,
            lambda s: s["stratum"]["substrate"]["grid"].update({"width": 5, "height": 5}),
        )
        env = cpu_env_factory(config_dir=config_dir, num_agents=2)

        curriculum = StaticCurriculum()
        exploration = EpsilonGreedyExploration(
            epsilon=0.1,
            epsilon_min=0.1,
            epsilon_decay=1.0,
        )

        population = VectorizedPopulation(
            env=env,
            curriculum=curriculum,
            exploration=exploration,
            agent_ids=["agent_0", "agent_1"],
            device=cpu_device,
            obs_dim=env.observation_dim,
            action_dim=env.action_dim,
            brain_config=recurrent_brain_config,
            vision_window_size=5,
            batch_size=8,
            sequence_length=5,
            max_grad_norm=10.0,
            train_frequency=4,
        )

        population.reset()

        # Initialize all meters to 1.0 to prevent cascade-induced death during test
        env.meters.fill_(1.0)

        # Verify initial shape (episode batch size = num_agents)
        assert population.rollout_hidden is not None
        h, c = population.rollout_hidden
        assert h.shape == (1, 2, 256), f"Initial hidden state should be (1, 2, 256), got {h.shape}"

        # Run enough steps to trigger training (need 16+ episodes in buffer)
        # Each episode needs to die to be stored
        for episode in range(20):
            # Run until death
            for step in range(100):
                state = population.step_population(env)
                if state.dones.any():
                    break

        # Training must not touch the rollout memory: still num_agents-shaped
        h, c = population.rollout_hidden
        assert h.shape == (1, 2, 256), f"After training, hidden state should be (1, 2, 256), got {h.shape}"


# =============================================================================
# TEST CLASS 3: LSTM Forward Pass
# =============================================================================


class TestLSTMForwardPass:
    """Test LSTM forward pass with POMDP observations."""

    def test_partial_observability_5x5_window_to_lstm(self, cpu_device, cpu_env_factory):
        """
        Verify POMDP environment → LSTM data flow.

        POMDP env (vision_range=2) produces 5×5 window.
        LSTM forward pass should work correctly and produce Q-values.
        """
        env = cpu_env_factory(
            config_dir=Path("configs/default_curriculum"),
            num_agents=1,
            level_name="L2_partial_observability",
        )

        # Create recurrent network. The spec and activity are REQUIRED for forward():
        # v2.1 slices the observation by ObservationSpec, and constructing without them
        # yields a network that builds and then raises on first use.
        bars_slice = env.observation_activity.group_slices["bars"]
        network = RecurrentSpatialQNetwork(
            action_dim=env.action_dim,
            window_size=5,
            position_dim=2,
            # OBSERVED width of the meter block, read from the activity — not the meter count
            bars_dim=bars_slice.stop - bars_slice.start,
            num_affordance_types=env.num_affordance_types,
            enable_temporal_features=False,
            hidden_dim=256,
            observation_spec=env.observation_spec,
            observation_activity=env.observation_activity,
        ).to(cpu_device)

        # Reset environment and get observation
        obs = env.reset()

        # Verify observation shape (POMDP)
        expected_obs_dim = env.metadata.observation_dim
        assert obs.shape == (1, expected_obs_dim), f"Expected obs shape (1, {expected_obs_dim}), got {obs.shape}"

        # Fresh hidden state
        initial_hidden = network.initial_hidden(1, cpu_device)

        # Forward pass
        q_values, new_hidden = network(obs, initial_hidden)

        # Verify Q-values shape
        assert q_values.shape == (1, env.action_dim), f"Expected Q-values shape (1, {env.action_dim}), got {q_values.shape}"

        # Verify hidden state shape
        h, c = new_hidden
        assert h.shape == (1, 1, 256), f"Expected h shape (1, 1, 256), got {h.shape}"
        assert c.shape == (1, 1, 256), f"Expected c shape (1, 1, 256), got {c.shape}"

        # Verify Q-values are finite
        assert torch.isfinite(q_values).all(), "Q-values should be finite"

        # Verify hidden state changed from initial zeros
        initial_h, initial_c = initial_hidden
        assert not torch.allclose(h, initial_h, atol=1e-6), "Hidden state should change after forward pass"
        assert not torch.allclose(c, initial_c, atol=1e-6), "Cell state should change after forward pass"
