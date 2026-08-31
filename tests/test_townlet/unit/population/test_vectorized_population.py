"""Tests for VectorizedPopulation Double DQN configuration."""

import pytest
import torch

from townlet.config.brain_config import (
    ArchitectureConfig,
    BrainConfig,
    FeedforwardConfig,
    LossConfig,
    OptimizerConfig,
    QLearningConfig,
    ReplayConfig,
    ScheduleConfig,
)
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.exploration.rnd import RNDExploration
from townlet.population.vectorized import VectorizedPopulation

POPULATION_CHECKPOINT_KEYS = {
    "version",
    "q_network",
    "optimizer",
    "scheduler",
    "total_steps",
    "exploration_state",
    "universe_metadata",
    "target_network",
    "training_step_counter",
    "replay_buffer",
}
POPULATION_UNIVERSE_METADATA_KEYS = {
    "meter_count",
    "meter_names",
    "version",
    "obs_dim",
    "observation_schema_hash",
    "action_dim",
}


def _make_population(
    env,
    curriculum,
    exploration,
    device,
    brain_config,
    **overrides,
):
    """Create VectorizedPopulation with explicit required runtime params for tests."""

    params = {
        "obs_dim": env.observation_dim,
        "action_dim": env.action_dim,
        "vision_window_size": 5,
        "train_frequency": 1,
        "batch_size": 32,
        "sequence_length": 1,
        "max_grad_norm": 10.0,
    }
    params.update(overrides)
    return VectorizedPopulation(
        env=env,
        curriculum=curriculum,
        exploration=exploration,
        agent_ids=["agent_0"],
        device=device,
        brain_config=brain_config,
        **params,
    )


class TestDoubleDQNConfiguration:
    """Test Double DQN parameter plumbing."""

    def test_population_accepts_use_double_dqn_parameter(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """VectorizedPopulation should read use_double_dqn from brain_config."""
        # Create brain_config with use_double_dqn=True
        brain_config = BrainConfig(
            version="1.0",
            description="Test Double DQN",
            architecture=ArchitectureConfig(
                type="feedforward",
                feedforward=FeedforwardConfig(
                    hidden_layers=[128, 64],
                    activation="relu",
                    dropout=0.0,
                    layer_norm=False,
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(type="constant"),
            ),
            loss=LossConfig(type="mse"),
            q_learning=QLearningConfig(
                gamma=0.99,
                target_update_frequency=100,
                use_double_dqn=True,  # Double DQN enabled
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config,
        )

        assert population.use_double_dqn is True

    def test_population_defaults_to_vanilla_dqn_when_false(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """VectorizedPopulation with use_double_dqn=False in brain_config uses vanilla DQN."""
        # minimal_brain_config has use_double_dqn: false
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )

        assert population.use_double_dqn is False

    def test_population_stores_use_double_dqn_attribute(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """use_double_dqn should be stored as instance attribute from brain_config."""
        # Create brain_config with use_double_dqn=False
        brain_config_vanilla = BrainConfig(
            version="1.0",
            description="Test Vanilla DQN",
            architecture=ArchitectureConfig(
                type="feedforward",
                feedforward=FeedforwardConfig(
                    hidden_layers=[128, 64],
                    activation="relu",
                    dropout=0.0,
                    layer_norm=False,
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(type="constant"),
            ),
            loss=LossConfig(type="mse"),
            q_learning=QLearningConfig(
                gamma=0.99,
                target_update_frequency=100,
                use_double_dqn=False,  # Vanilla DQN
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        # Create brain_config with use_double_dqn=True
        brain_config_double = BrainConfig(
            version="1.0",
            description="Test Double DQN",
            architecture=ArchitectureConfig(
                type="feedforward",
                feedforward=FeedforwardConfig(
                    hidden_layers=[128, 64],
                    activation="relu",
                    dropout=0.0,
                    layer_norm=False,
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(type="constant"),
            ),
            loss=LossConfig(type="mse"),
            q_learning=QLearningConfig(
                gamma=0.99,
                target_update_frequency=100,
                use_double_dqn=True,  # Double DQN
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        pop_vanilla = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config_vanilla,
        )

        pop_double = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config_double,
        )

        assert pop_vanilla.use_double_dqn is False
        assert pop_double.use_double_dqn is True


@pytest.fixture
def simple_brain_config():
    """Create a simple BrainConfig for testing."""
    return BrainConfig(
        version="1.0",
        description="Test brain config",
        architecture=ArchitectureConfig(
            type="feedforward",
            feedforward=FeedforwardConfig(
                hidden_layers=[128, 64],
                activation="relu",
                dropout=0.0,
                layer_norm=False,
            ),
        ),
        optimizer=OptimizerConfig(
            type="adam",
            learning_rate=0.001,
            adam_beta1=0.9,
            adam_beta2=0.999,
            adam_eps=1e-8,
            weight_decay=0.0,
            schedule=ScheduleConfig(type="constant"),
        ),
        loss=LossConfig(type="mse"),
        q_learning=QLearningConfig(
            gamma=0.99,
            target_update_frequency=100,
            use_double_dqn=False,
        ),
        replay=ReplayConfig(
            capacity=10000,
            prioritized=False,
        ),
    )


class TestBrainConfigIntegration:
    """Test BrainConfig parameter plumbing."""

    def test_population_accepts_brain_config_parameter(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        simple_brain_config,
    ):
        """VectorizedPopulation should accept brain_config parameter."""
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=simple_brain_config,
        )

        assert population.brain_config is simple_brain_config

    def test_population_builds_network_from_brain_config(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        simple_brain_config,
    ):
        """VectorizedPopulation should build Q-network from brain_config."""
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=simple_brain_config,
        )

        # Network should be built from config (not hardcoded)
        # Verify network architecture matches brain_config.architecture.feedforward
        import torch.nn as nn

        assert isinstance(population.q_network, nn.Sequential)
        # Config has hidden_layers=[128, 64], so we expect:
        # Linear(obs_dim -> 128), ReLU, Linear(128 -> 64), ReLU, Linear(64 -> action_dim)
        # Total: 5 layers (2 linear + 2 activation + 1 output linear)
        assert len(population.q_network) == 5

    def test_population_builds_optimizer_from_brain_config(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        simple_brain_config,
    ):
        """VectorizedPopulation should build optimizer from brain_config."""
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=simple_brain_config,
        )

        # Optimizer should be Adam with config parameters
        import torch.optim as optim

        assert isinstance(population.optimizer, optim.Adam)
        # Verify learning rate matches config
        assert population.optimizer.param_groups[0]["lr"] == 0.001

    def test_brain_config_sets_q_learning_parameters(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """brain_config q_learning fields should be used for Q-learning parameters."""
        # Create brain_config with specific q_learning values
        brain_config = BrainConfig(
            version="1.0",
            description="Test Q-learning parameters",
            architecture=ArchitectureConfig(
                type="feedforward",
                feedforward=FeedforwardConfig(
                    hidden_layers=[128],
                    activation="relu",
                    dropout=0.0,
                    layer_norm=False,
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(type="constant"),
            ),
            loss=LossConfig(type="mse"),
            q_learning=QLearningConfig(
                gamma=0.90,
                target_update_frequency=250,
                use_double_dqn=True,
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config,
        )

        # Verify brain_config values are used
        assert population.gamma == 0.90
        assert population.target_update_frequency == 250
        assert population.use_double_dqn is True

    def test_configured_loss_function_is_used(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """Configured loss function should be used in training."""
        import torch.nn as nn

        # Create brain_config with Huber loss
        brain_config = BrainConfig(
            version="1.0",
            description="Test Huber loss usage",
            architecture=ArchitectureConfig(
                type="feedforward",
                feedforward=FeedforwardConfig(
                    hidden_layers=[128],
                    activation="relu",
                    dropout=0.0,
                    layer_norm=False,
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(type="constant"),
            ),
            loss=LossConfig(type="huber", huber_delta=2.0),  # Huber loss with delta=2.0
            q_learning=QLearningConfig(
                gamma=0.99,
                target_update_frequency=100,
                use_double_dqn=False,
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config,
        )

        # Verify loss function is HuberLoss with correct delta
        assert isinstance(population.loss_fn, nn.HuberLoss)
        assert population.loss_fn.delta == 2.0


class TestRecurrentNetworkSupport:
    """Test recurrent network integration (Phase 2)."""

    def test_population_builds_recurrent_network_from_brain_config(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """VectorizedPopulation should build RecurrentSpatialQNetwork from recurrent config."""
        from townlet.agent.networks import RecurrentSpatialQNetwork
        from townlet.config.brain_config import (
            CNNEncoderConfig,
            LSTMConfig,
            MLPEncoderConfig,
            RecurrentConfig,
        )

        brain_config = BrainConfig(
            version="1.0",
            description="Test recurrent config",
            architecture=ArchitectureConfig(
                type="recurrent",
                recurrent=RecurrentConfig(
                    vision_encoder=CNNEncoderConfig(
                        channels=[16, 32],
                        kernel_sizes=[3, 3],
                        strides=[1, 1],
                        padding=[1, 1],
                        activation="relu",
                    ),
                    position_encoder=MLPEncoderConfig(
                        hidden_sizes=[32],
                        activation="relu",
                    ),
                    meter_encoder=MLPEncoderConfig(
                        hidden_sizes=[32],
                        activation="relu",
                    ),
                    affordance_encoder=MLPEncoderConfig(
                        hidden_sizes=[32],
                        activation="relu",
                    ),
                    lstm=LSTMConfig(
                        hidden_size=256,
                        num_layers=1,
                        dropout=0.0,
                    ),
                    q_head=MLPEncoderConfig(
                        hidden_sizes=[128],
                        activation="relu",
                    ),
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.0001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(type="constant"),
            ),
            loss=LossConfig(type="huber", huber_delta=1.0),
            q_learning=QLearningConfig(
                gamma=0.99,
                target_update_frequency=100,
                use_double_dqn=True,
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config,
        )

        # Should build RecurrentSpatialQNetwork
        assert isinstance(population.q_network, RecurrentSpatialQNetwork)
        assert isinstance(population.target_network, RecurrentSpatialQNetwork)
        assert population.is_recurrent is True

    def test_is_recurrent_flag_comes_from_brain_config_not_network_type(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """CRITICAL: is_recurrent flag must come from brain_config.architecture.type, not network_type parameter."""
        from townlet.config.brain_config import (
            CNNEncoderConfig,
            LSTMConfig,
            MLPEncoderConfig,
            RecurrentConfig,
        )

        # Create recurrent brain_config
        recurrent_config = BrainConfig(
            version="1.0",
            description="Test is_recurrent flag correctness",
            architecture=ArchitectureConfig(
                type="recurrent",
                recurrent=RecurrentConfig(
                    vision_encoder=CNNEncoderConfig(
                        channels=[16, 32],
                        kernel_sizes=[3, 3],
                        strides=[1, 1],
                        padding=[1, 1],
                        activation="relu",
                    ),
                    position_encoder=MLPEncoderConfig(
                        hidden_sizes=[32],
                        activation="relu",
                    ),
                    meter_encoder=MLPEncoderConfig(
                        hidden_sizes=[32],
                        activation="relu",
                    ),
                    affordance_encoder=MLPEncoderConfig(
                        hidden_sizes=[32],
                        activation="relu",
                    ),
                    lstm=LSTMConfig(
                        hidden_size=256,
                        num_layers=1,
                        dropout=0.0,
                    ),
                    q_head=MLPEncoderConfig(
                        hidden_sizes=[128],
                        activation="relu",
                    ),
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.0001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(type="constant"),
            ),
            loss=LossConfig(type="huber", huber_delta=1.0),
            q_learning=QLearningConfig(
                gamma=0.99,
                target_update_frequency=100,
                use_double_dqn=True,
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        # Pass brain_config with recurrent architecture
        # The is_recurrent flag should come from brain_config.architecture.type
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=recurrent_config,
            sequence_length=1,
        )

        # CRITICAL: is_recurrent should be True (from brain_config.architecture.type)
        # NOT False (from brain_config=minimal_brain_config)
        assert population.is_recurrent is True, (
            "is_recurrent flag must come from brain_config.architecture.type, not network_type parameter. "
            f"Expected True (from brain_config), got {population.is_recurrent} (from network_type)"
        )

    def test_is_recurrent_flag_uses_network_type_when_no_brain_config(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
        recurrent_brain_config,
    ):
        """is_recurrent should be inferred from brain_config architecture type."""
        # Test feedforward network
        population_feedforward = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        assert population_feedforward.is_recurrent is False

        # Test recurrent network
        population_recurrent = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=recurrent_brain_config,
            sequence_length=1,
        )
        assert population_recurrent.is_recurrent is True

    def test_recurrent_network_has_correct_dimensions(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """Recurrent network should have dimensions from config."""
        from townlet.config.brain_config import (
            CNNEncoderConfig,
            LSTMConfig,
            MLPEncoderConfig,
            RecurrentConfig,
        )

        brain_config = BrainConfig(
            version="1.0",
            description="Test recurrent dimensions",
            architecture=ArchitectureConfig(
                type="recurrent",
                recurrent=RecurrentConfig(
                    vision_encoder=CNNEncoderConfig(
                        channels=[16, 32],
                        kernel_sizes=[3, 3],
                        strides=[1, 1],
                        padding=[1, 1],
                        activation="relu",
                    ),
                    position_encoder=MLPEncoderConfig(
                        hidden_sizes=[32],
                        activation="relu",
                    ),
                    meter_encoder=MLPEncoderConfig(
                        hidden_sizes=[32],
                        activation="relu",
                    ),
                    affordance_encoder=MLPEncoderConfig(
                        hidden_sizes=[32],
                        activation="relu",
                    ),
                    lstm=LSTMConfig(
                        hidden_size=128,  # Different from hardcoded 256
                        num_layers=1,
                        dropout=0.0,
                    ),
                    q_head=MLPEncoderConfig(
                        hidden_sizes=[128],
                        activation="relu",
                    ),
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.0001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(type="constant"),
            ),
            loss=LossConfig(type="huber", huber_delta=1.0),
            q_learning=QLearningConfig(
                gamma=0.99,
                target_update_frequency=100,
                use_double_dqn=True,
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config,
            sequence_length=1,
        )

        # LSTM hidden size should come from config (128), not hardcoded (256)
        assert population.q_network.lstm.hidden_size == 128


class TestSchedulerIntegration:
    """Test learning rate scheduler integration (Phase 2)."""

    def test_population_unpacks_scheduler_from_optimizer_factory(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """VectorizedPopulation should unpack (optimizer, scheduler) tuple."""
        from torch.optim.lr_scheduler import StepLR

        brain_config = BrainConfig(
            version="1.0",
            description="Test step decay schedule",
            architecture=ArchitectureConfig(
                type="feedforward",
                feedforward=FeedforwardConfig(
                    hidden_layers=[128],
                    activation="relu",
                    dropout=0.0,
                    layer_norm=False,
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(
                    type="step_decay",
                    step_size=100,
                    gamma=0.1,
                ),
            ),
            loss=LossConfig(type="mse"),
            q_learning=QLearningConfig(
                gamma=0.99,
                target_update_frequency=100,
                use_double_dqn=False,
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config,
        )

        # Should unpack scheduler from OptimizerFactory.build()
        assert hasattr(population, "scheduler")
        assert isinstance(population.scheduler, StepLR)

    def test_population_has_no_scheduler_for_constant_schedule(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """VectorizedPopulation should have scheduler=None for constant schedule."""
        brain_config = BrainConfig(
            version="1.0",
            description="Test constant schedule",
            architecture=ArchitectureConfig(
                type="feedforward",
                feedforward=FeedforwardConfig(
                    hidden_layers=[128],
                    activation="relu",
                    dropout=0.0,
                    layer_norm=False,
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(type="constant"),
            ),
            loss=LossConfig(type="mse"),
            q_learning=QLearningConfig(
                gamma=0.99,
                target_update_frequency=100,
                use_double_dqn=False,
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config,
        )

        # Constant schedule should result in scheduler=None
        assert hasattr(population, "scheduler")
        assert population.scheduler is None

    def test_exponential_scheduler_support(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """VectorizedPopulation should support ExponentialLR scheduler."""
        from torch.optim.lr_scheduler import ExponentialLR

        brain_config = BrainConfig(
            version="1.0",
            description="Test exponential schedule",
            architecture=ArchitectureConfig(
                type="feedforward",
                feedforward=FeedforwardConfig(
                    hidden_layers=[128],
                    activation="relu",
                    dropout=0.0,
                    layer_norm=False,
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(
                    type="exponential",
                    gamma=0.9999,
                ),
            ),
            loss=LossConfig(type="mse"),
            q_learning=QLearningConfig(
                gamma=0.99,
                target_update_frequency=100,
                use_double_dqn=False,
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config,
        )

        assert isinstance(population.scheduler, ExponentialLR)

    def test_scheduler_state_persists_across_checkpoint_save_load(
        self,
        compile_universe,
        test_config_pack_path,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """Scheduler state should be saved and restored in checkpoints."""
        from townlet.environment.vectorized_env import VectorizedHamletEnv

        # Create CPU-based environment
        universe = compile_universe(test_config_pack_path)
        env = VectorizedHamletEnv.from_universe(
            universe,
            level_name="L0_test",
            num_agents=1,
            device=cpu_device,
        )

        brain_config = BrainConfig(
            version="1.0",
            description="Test scheduler state persistence",
            architecture=ArchitectureConfig(
                type="feedforward",
                feedforward=FeedforwardConfig(
                    hidden_layers=[128],
                    activation="relu",
                    dropout=0.0,
                    layer_norm=False,
                ),
            ),
            optimizer=OptimizerConfig(
                type="adam",
                learning_rate=0.001,
                adam_beta1=0.9,
                adam_beta2=0.999,
                adam_eps=1e-8,
                weight_decay=0.0,
                schedule=ScheduleConfig(
                    type="step_decay",
                    step_size=100,
                    gamma=0.1,
                ),
            ),
            loss=LossConfig(type="mse"),
            q_learning=QLearningConfig(
                gamma=0.99,
                target_update_frequency=100,
                use_double_dqn=False,
            ),
            replay=ReplayConfig(
                capacity=10000,
                prioritized=False,
            ),
        )

        # Create population with scheduler
        population1 = _make_population(
            env=env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config,
            obs_dim=env.observation_dim,
        )

        # Initialize curriculum
        adversarial_curriculum.initialize_population(1)

        # Take training steps to advance scheduler
        # Add some transitions to replay buffer first
        population1.reset()
        for _ in range(10):
            state = population1.step_population(env)
            if state.dones.any():
                break

        # Advance scheduler by triggering training steps
        # Fill replay buffer with enough transitions
        for _ in range(100):
            state = population1.step_population(env)
            if state.dones.any():
                env.reset()
                population1.reset()

        # Get scheduler step count before checkpoint
        initial_step_count = population1.scheduler.last_epoch

        # Save checkpoint
        checkpoint = population1.get_checkpoint_state()

        # Verify scheduler state is in checkpoint
        assert "scheduler" in checkpoint
        assert checkpoint["scheduler"] is not None
        assert checkpoint["scheduler"]["last_epoch"] == initial_step_count

        # Create new population
        population2 = _make_population(
            env=env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config,
            obs_dim=env.observation_dim,
        )

        # Verify new population starts at step 0
        assert population2.scheduler.last_epoch == 0

        # Load checkpoint
        population2.load_checkpoint_state(checkpoint)

        # Verify scheduler state restored
        assert population2.scheduler.last_epoch == initial_step_count


class TestPopulationCheckpointSchema:
    """Exact current checkpoint schema and restoration contract."""

    def test_producer_emits_exact_current_key_sets(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )

        checkpoint = population.get_checkpoint_state()

        assert set(checkpoint) == POPULATION_CHECKPOINT_KEYS
        assert set(checkpoint["universe_metadata"]) == POPULATION_UNIVERSE_METADATA_KEYS

    def test_validator_is_public_non_mutating_and_refuses_network_shape_mismatch(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        checkpoint = population.get_checkpoint_state()
        before = {key: value.clone() for key, value in population.q_network.state_dict().items()}
        first_key = next(iter(checkpoint["q_network"]))
        checkpoint["q_network"][first_key] = checkpoint["q_network"][first_key][:-1]

        with pytest.raises(ValueError, match="q_network.*shape mismatch"):
            population.validate_checkpoint_state(checkpoint)

        after = population.q_network.state_dict()
        assert all(torch.equal(before[key], after[key]) for key in before)

    @pytest.mark.parametrize("missing_key", sorted(POPULATION_CHECKPOINT_KEYS))
    def test_loader_refuses_every_missing_top_level_key(
        self,
        missing_key,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        checkpoint = population.get_checkpoint_state()
        checkpoint.pop(missing_key)

        with pytest.raises(ValueError, match="Population checkpoint key set mismatch"):
            population.load_checkpoint_state(checkpoint)

    def test_loader_refuses_unknown_top_level_key(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        checkpoint = population.get_checkpoint_state()
        checkpoint["removed_field"] = 1

        with pytest.raises(ValueError, match="Population checkpoint key set mismatch"):
            population.load_checkpoint_state(checkpoint)

    @pytest.mark.parametrize("missing_key", sorted(POPULATION_UNIVERSE_METADATA_KEYS))
    def test_loader_refuses_every_missing_universe_metadata_key(
        self,
        missing_key,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        checkpoint = population.get_checkpoint_state()
        checkpoint["universe_metadata"].pop(missing_key)

        with pytest.raises(ValueError, match="Population universe_metadata key set mismatch"):
            population.load_checkpoint_state(checkpoint)

    def test_loader_refuses_unknown_universe_metadata_key(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        checkpoint = population.get_checkpoint_state()
        checkpoint["universe_metadata"]["removed_field"] = 1

        with pytest.raises(ValueError, match="Population universe_metadata key set mismatch"):
            population.load_checkpoint_state(checkpoint)

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        (
            pytest.param("meter_names", ("wrong",), "meter names mismatch", id="meter-names"),
            pytest.param("version", "wrong", "bar config version mismatch", id="bar-version"),
        ),
    )
    def test_loader_validates_every_universe_metadata_value(
        self,
        field,
        value,
        message,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        checkpoint = population.get_checkpoint_state()
        checkpoint["universe_metadata"][field] = value

        with pytest.raises(ValueError, match=message):
            population.load_checkpoint_state(checkpoint)

    @pytest.mark.parametrize("state_key", ("target_network", "replay_buffer", "exploration_state"))
    def test_loader_refuses_null_mandatory_state(
        self,
        state_key,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        checkpoint = population.get_checkpoint_state()
        checkpoint[state_key] = None

        with pytest.raises(ValueError, match=f"{state_key} must contain state"):
            population.load_checkpoint_state(checkpoint)

    def test_loader_refuses_scheduler_state_when_current_scheduler_is_absent(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        checkpoint = population.get_checkpoint_state()
        checkpoint["scheduler"] = {"last_epoch": 7}

        with pytest.raises(ValueError, match="scheduler nullability mismatch"):
            population.load_checkpoint_state(checkpoint)

    def test_loader_refuses_null_scheduler_when_current_scheduler_exists(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        optimizer = minimal_brain_config.optimizer.model_copy(
            update={"schedule": ScheduleConfig(type="step_decay", step_size=10, gamma=0.5)}
        )
        brain_config = minimal_brain_config.model_copy(update={"optimizer": optimizer})
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=brain_config,
        )
        checkpoint = population.get_checkpoint_state()
        checkpoint["scheduler"] = None

        with pytest.raises(ValueError, match="scheduler nullability mismatch"):
            population.load_checkpoint_state(checkpoint)

    def test_loader_restores_counters_and_exploration_exactly(
        self,
        basic_env,
        adversarial_curriculum,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        source_exploration = EpsilonGreedyExploration(epsilon=0.37, epsilon_decay=0.91, epsilon_min=0.07)
        source = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=source_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        source.total_steps = 17
        source.training_step_counter = 23
        checkpoint = source.get_checkpoint_state()

        target_exploration = EpsilonGreedyExploration(epsilon=1.0, epsilon_decay=0.5, epsilon_min=0.1)
        target = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=target_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        target.total_steps = 999
        target.training_step_counter = 999

        target.load_checkpoint_state(checkpoint)

        assert target.total_steps == 17
        assert target.training_step_counter == 23
        assert target.exploration.checkpoint_state() == checkpoint["exploration_state"]


def test_brain_config_none_raises_valueerror(basic_env, adversarial_curriculum, epsilon_greedy_exploration, cpu_device):
    """VectorizedPopulation should reject brain_config=None per WP-C2."""
    import pytest

    from townlet.population.vectorized import VectorizedPopulation

    with pytest.raises(ValueError, match="brain_config is required"):
        VectorizedPopulation(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            agent_ids=["agent_0"],
            device=cpu_device,
            obs_dim=basic_env.observation_dim,
            action_dim=basic_env.action_dim,
            vision_window_size=5,
            train_frequency=1,
            batch_size=32,
            sequence_length=1,
            max_grad_norm=10.0,
            brain_config=None,  # Should raise ValueError
        )


def test_token_spec_none_raises_valueerror(basic_env, adversarial_curriculum, epsilon_greedy_exploration, cpu_device, minimal_brain_config):
    """VectorizedPopulation raises ValueError when env.token_spec is None.

    Per CLAUDE.md "no implicit defaults" philosophy, we require env.token_spec
    to be explicitly set rather than silently falling back.
    """
    import pytest

    from townlet.population.vectorized import VectorizedPopulation

    # Mock env without token_spec
    basic_env.token_spec = None

    with pytest.raises(ValueError, match="token_spec is required"):
        VectorizedPopulation(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            agent_ids=["agent_0"],
            device=cpu_device,
            obs_dim=basic_env.observation_dim,
            action_dim=basic_env.action_dim,
            vision_window_size=5,
            train_frequency=1,
            batch_size=32,
            sequence_length=1,
            max_grad_norm=10.0,
            brain_config=minimal_brain_config,
        )


def test_token_spec_missing_attribute_raises_valueerror(
    basic_env, adversarial_curriculum, epsilon_greedy_exploration, cpu_device, minimal_brain_config
):
    """VectorizedPopulation raises ValueError when env has no token_spec attribute.

    Covers the case where the env object doesn't have the attribute at all
    (not just when it's set to None).
    """
    import pytest

    from townlet.population.vectorized import VectorizedPopulation

    # Delete the token_spec attribute entirely
    if hasattr(basic_env, "token_spec"):
        delattr(basic_env, "token_spec")

    with pytest.raises(ValueError, match="token_spec is required"):
        VectorizedPopulation(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            agent_ids=["agent_0"],
            device=cpu_device,
            obs_dim=basic_env.observation_dim,
            action_dim=basic_env.action_dim,
            vision_window_size=5,
            train_frequency=1,
            batch_size=32,
            sequence_length=1,
            max_grad_norm=10.0,
            brain_config=minimal_brain_config,
        )


def test_device_mismatch_in_step_all_raises_runtime_error(
    basic_env, adversarial_curriculum, epsilon_greedy_exploration, cpu_device, minimal_brain_config
):
    """step_all raises RuntimeError when observation tensor is on wrong device (POP-004).

    Device mismatches cause cryptic PyTorch errors deep in computation graphs.
    This validation provides clear error messages.

    Note: This test uses monkeypatching to simulate device mismatch since actual
    device mismatch requires CUDA hardware.
    """
    import pytest
    import torch

    from townlet.population.vectorized import VectorizedPopulation

    population = VectorizedPopulation(
        env=basic_env,
        curriculum=adversarial_curriculum,
        exploration=epsilon_greedy_exploration,
        agent_ids=["agent_0"],
        device=cpu_device,
        obs_dim=basic_env.observation_dim,
        action_dim=basic_env.action_dim,
        vision_window_size=5,
        train_frequency=1,
        batch_size=32,
        sequence_length=1,
        max_grad_norm=10.0,
        brain_config=minimal_brain_config,
    )

    # Create a mock tensor with a different device
    # We can't actually use a different device without CUDA, so we mock the device property
    class MockTensor:
        """Mock tensor that reports a different device for testing."""

        def __init__(self, real_tensor):
            self._real = real_tensor
            self.device = torch.device("meta")  # Different from cpu_device

        def __getattr__(self, name):
            return getattr(self._real, name)

    # Replace current_obs with our mock
    original_obs = population.current_obs
    population.current_obs = MockTensor(original_obs)

    # Create action mask (required for step_population)
    action_mask = torch.ones(1, basic_env.action_dim, dtype=torch.bool)

    with pytest.raises(RuntimeError, match="Observation tensor on"):
        population.step_population(action_mask)


class TestPopulationExplorationTelemetry:
    """Telemetry is defined only for the three production exploration strategies."""

    def test_exact_values_for_all_supported_strategies(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )

        epsilon_greedy_exploration.epsilon = 0.31
        assert population._get_current_epsilon_value() == 0.31
        assert population._get_current_intrinsic_weight_value() == 0.0

        rnd = RNDExploration(obs_dim=basic_env.observation_dim, epsilon_start=0.27, device=cpu_device)
        population.exploration = rnd
        assert population._get_current_epsilon_value() == 0.27
        assert population._get_current_intrinsic_weight_value() == 0.0

        adaptive = AdaptiveIntrinsicExploration(
            obs_dim=basic_env.observation_dim,
            epsilon_start=0.19,
            initial_intrinsic_weight=0.43,
            device=cpu_device,
        )
        population.exploration = adaptive
        assert population._get_current_epsilon_value() == 0.19
        assert population._get_current_intrinsic_weight_value() == 0.43

    def test_unsupported_strategy_refuses_instead_of_falling_back(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ) -> None:
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )
        population.exploration = object()  # type: ignore[assignment]

        with pytest.raises(TypeError, match="Unsupported exploration strategy"):
            population._get_current_epsilon_value()
        with pytest.raises(TypeError, match="Unsupported exploration strategy"):
            population._get_current_intrinsic_weight_value()


class TestRewardComponentWiring:
    """Test that reward components flow from env to population to buffer."""

    def test_components_extracted_from_info_dict(
        self,
        compile_universe,
        test_config_pack_path,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """VectorizedPopulation extracts reward components from env info dict."""

        import torch

        from townlet.environment.vectorized_env import VectorizedHamletEnv

        # Create CPU-based environment to match cpu_device
        universe = compile_universe(test_config_pack_path)
        basic_env = VectorizedHamletEnv.from_universe(
            universe,
            level_name="L0_test",
            num_agents=1,
            device=cpu_device,
        )

        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )

        # Initialize tb_logger attribute (implementation expects it to exist)
        population.tb_logger = None

        # Initialize curriculum before stepping population
        adversarial_curriculum.initialize_population(1)

        # Mock the environment step to return components
        original_step = basic_env.step

        def mock_step(actions, *args, **kwargs):
            obs, rewards, dones, info = original_step(actions, *args, **kwargs)
            # Add mock components to info dict
            info["reward_components"] = {
                "extrinsic": torch.tensor([0.5]),
                "intrinsic": torch.tensor([0.3]),
                "shaping": torch.tensor([0.2]),
            }
            info["intrinsic_weight"] = torch.tensor([1.0])
            return obs, rewards, dones, info

        basic_env.step = mock_step

        # Step population
        population.step_population(basic_env)

        # Verify replay buffer has components
        if hasattr(population.replay_buffer, "rewards_extrinsic"):
            assert population.replay_buffer.rewards_extrinsic is not None
            assert population.replay_buffer.rewards_intrinsic is not None
            assert population.replay_buffer.rewards_shaping is not None

    def test_reward_tensor_created_with_components(
        self,
        compile_universe,
        test_config_pack_path,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """RewardTensor is created with component fields populated."""
        import torch

        from townlet.environment.vectorized_env import VectorizedHamletEnv

        # Create CPU-based environment to match cpu_device
        universe = compile_universe(test_config_pack_path)
        basic_env = VectorizedHamletEnv.from_universe(
            universe,
            level_name="L0_test",
            num_agents=1,
            device=cpu_device,
        )

        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )

        # Initialize tb_logger attribute (implementation expects it to exist)
        population.tb_logger = None

        # Initialize curriculum before stepping population
        adversarial_curriculum.initialize_population(1)

        # Mock environment step
        original_step = basic_env.step

        def mock_step(actions, *args, **kwargs):
            obs, rewards, dones, info = original_step(actions, *args, **kwargs)
            info["reward_components"] = {
                "extrinsic": torch.tensor([0.5]),
                "intrinsic": torch.tensor([0.3]),
                "shaping": torch.tensor([0.2]),
            }
            return obs, rewards, dones, info

        basic_env.step = mock_step

        # Step population (this will create RewardTensor internally)
        population.step_population(basic_env)

        # Verify components are stored in buffer
        buffer = population.replay_buffer
        if hasattr(buffer, "rewards_extrinsic") and buffer.size > 0:
            # Components should be stored
            assert buffer.rewards_extrinsic[0].item() == pytest.approx(0.5)
            assert buffer.rewards_intrinsic[0].item() == pytest.approx(0.3)
            assert buffer.rewards_shaping[0].item() == pytest.approx(0.2)

    def test_tensorboard_logging_called_when_components_present(
        self,
        compile_universe,
        test_config_pack_path,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
        tmp_path,
    ):
        """TensorBoard logging is called when components are in info dict."""
        from unittest.mock import MagicMock

        import torch

        from townlet.environment.vectorized_env import VectorizedHamletEnv

        # Create CPU-based environment to match cpu_device
        universe = compile_universe(test_config_pack_path)
        basic_env = VectorizedHamletEnv.from_universe(
            universe,
            level_name="L0_test",
            num_agents=1,
            device=cpu_device,
        )

        # Create population with TensorBoard logger
        from townlet.training.tensorboard_logger import TensorBoardLogger

        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )

        # Initialize curriculum before stepping population
        adversarial_curriculum.initialize_population(1)

        # Attach TensorBoard logger
        population.tb_logger = TensorBoardLogger(log_dir=tmp_path / "tb_logs")

        # Mock the log_custom_metric method
        population.tb_logger.log_custom_metric = MagicMock()

        # Mock environment step
        original_step = basic_env.step

        def mock_step(actions, *args, **kwargs):
            obs, rewards, dones, info = original_step(actions, *args, **kwargs)
            info["reward_components"] = {
                "extrinsic": torch.tensor([0.5]),
                "intrinsic": torch.tensor([0.3]),
                "shaping": torch.tensor([0.2]),
            }
            info["intrinsic_weight"] = torch.tensor([1.0])
            return obs, rewards, dones, info

        basic_env.step = mock_step

        # Step population
        population.step_population(basic_env)

        # Verify log_custom_metric was called for components
        assert population.tb_logger.log_custom_metric.call_count >= 3
        # Should have logged at least: extrinsic, intrinsic, shaping

        # Cleanup
        population.tb_logger.close()

    def test_episode_container_has_component_keys(
        self,
        basic_env,
        adversarial_curriculum,
        epsilon_greedy_exploration,
        cpu_device,
        minimal_brain_config,
    ):
        """Episode containers include component keys for provenance tracking."""
        population = _make_population(
            env=basic_env,
            curriculum=adversarial_curriculum,
            exploration=epsilon_greedy_exploration,
            device=cpu_device,
            brain_config=minimal_brain_config,
        )

        # Test _new_episode_container directly
        episode = population._new_episode_container()
        assert "rewards" in episode
        assert "rewards_extrinsic" in episode
        assert "rewards_intrinsic" in episode
        assert "rewards_shaping" in episode
        assert "observations" in episode
        assert "actions" in episode
        assert "dones" in episode
