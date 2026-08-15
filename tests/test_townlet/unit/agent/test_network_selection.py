"""Test network instantiation patterns for different architectures."""

from pathlib import Path

from townlet.agent.networks import RecurrentSpatialQNetwork, SimpleQNetwork, StructuredQNetwork
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler


class TestStructuredNetworkInstantiation:
    def test_structured_network_instantiated_with_observation_activity(self):
        """VectorizedPopulation should instantiate StructuredQNetwork when network_type='structured'."""
        config_dir = Path("configs/default_curriculum")

        compiler = UniverseCompiler()
        compiled = compiler.compile(config_dir, primary_level="L0_5_dual_resource", use_cache=False)

        # Create environment to get observation_activity
        env = VectorizedHamletEnv.from_universe(compiled, level_name="L0_5_dual_resource", num_agents=4, device="cpu")

        # Manually create StructuredQNetwork as population would
        network = StructuredQNetwork(
            obs_dim=env.observation_dim,
            action_dim=env.action_dim,
            observation_activity=env.observation_activity,
        )

        assert isinstance(network, StructuredQNetwork)
        assert hasattr(network, "observation_activity")
        assert hasattr(network, "group_encoders")

    def test_simple_network_still_works(self):
        """VectorizedPopulation should still instantiate SimpleQNetwork when network_type='simple'."""
        config_dir = Path("configs/default_curriculum")

        compiler = UniverseCompiler()
        compiled = compiler.compile(config_dir, primary_level="L0_5_dual_resource", use_cache=False)
        env = VectorizedHamletEnv.from_universe(compiled, level_name="L0_5_dual_resource", num_agents=4, device="cpu")

        # Manually create SimpleQNetwork as population would
        network = SimpleQNetwork(
            obs_dim=env.observation_dim,
            action_dim=env.action_dim,
            hidden_dim=128,
        )

        assert isinstance(network, SimpleQNetwork)

    def test_recurrent_network_still_works(self):
        """VectorizedPopulation should still instantiate RecurrentSpatialQNetwork when network_type='recurrent'."""
        config_dir = Path("configs/default_curriculum")

        compiler = UniverseCompiler()
        compiled = compiler.compile(config_dir, primary_level="L2_partial_observability", use_cache=False)
        env = VectorizedHamletEnv.from_universe(compiled, level_name="L2_partial_observability", num_agents=4, device="cpu")

        # Manually create RecurrentSpatialQNetwork as population would. Both the bars
        # width and the block's location come from the compiled artifact — the network
        # no longer accepts a meter COUNT, and no longer finds the block by field name.
        bars = env.observation_activity.group_slices["bars"]
        network = RecurrentSpatialQNetwork(
            action_dim=env.action_dim,
            window_size=5,
            position_dim=2,
            bars_dim=bars.stop - bars.start,
            num_affordance_types=14,
            enable_temporal_features=True,
            hidden_dim=256,
            observation_spec=env.observation_spec,
            observation_activity=env.observation_activity,
        )

        assert isinstance(network, RecurrentSpatialQNetwork)
        assert network.bars_dim == 8, "eight meters, each observing one dim, is still eight"
