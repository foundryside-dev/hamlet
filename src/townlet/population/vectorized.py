"""
Vectorized population manager.

Coordinates multiple agents with shared curriculum and exploration strategies.
Manages Q-networks, replay buffers, and training loops.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812

from townlet.agent.loss_factory import LossFactory
from townlet.agent.network_factory import NetworkFactory
from townlet.agent.networks import RecurrentSpatialQNetwork
from townlet.agent.optimizer_factory import OptimizerFactory
from townlet.config.brain_config import BrainConfig
from townlet.curriculum.base import CurriculumManager
from townlet.exploration.action_selection import epsilon_greedy_action_selection
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.base import ExplorationStrategy
from townlet.exploration.rnd import RNDExploration
from townlet.population.base import PopulationManager
from townlet.population.runtime_registry import AgentRuntimeRegistry
from townlet.training.checkpoint_utils import TokenRosterReport, load_token_network_state_by_type
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer
from townlet.training.state import BatchedAgentState, CurriculumDecision, PopulationCheckpoint, RewardTensor
from townlet.universe.token_hashes import compute_token_layout_hash

if TYPE_CHECKING:
    from townlet.environment.vectorized_env import VectorizedHamletEnv

_logger = logging.getLogger(__name__)

EpisodeContainer = dict[str, list[torch.Tensor]]



class VectorizedPopulation(PopulationManager):
    """
    Vectorized population manager.

    Coordinates training for num_agents parallel agents with shared
    curriculum and exploration strategies.
    """

    def __init__(
        self,
        env: VectorizedHamletEnv,
        curriculum: CurriculumManager,
        exploration: ExplorationStrategy,
        agent_ids: list[str],
        device: torch.device,
        brain_config: BrainConfig,
        obs_dim: int,
        train_frequency: int,
        batch_size: int,
        sequence_length: int,
        max_grad_norm: float,
        action_dim: int,
        vision_window_size: int,
        tb_logger=None,
        max_episodes: int | None = None,
        max_steps_per_episode: int | None = None,
    ):
        """
        Initialize vectorized population.

        Args:
            env: Vectorized environment (must have a compiled `token_spec`)
            curriculum: Curriculum manager
            exploration: Exploration strategy
            agent_ids: List of agent identifiers
            device: PyTorch device
            obs_dim: Observation dimension
            action_dim: Action dimension (defaults to env.action_dim if not specified)
            brain_config: Brain configuration (REQUIRED). Specifies network architecture,
                optimizer, loss function, Q-learning parameters, and replay buffer settings.
                See docs/config-schemas/brain.md for schema.
            vision_window_size: Size of local vision window for recurrent networks (5 for 5×5)
            tb_logger: Optional TensorBoard logger
            train_frequency: Train Q-network every N steps (required; typically from training.yaml)
            batch_size: Batch size for experience replay (required; typically from training.yaml replay_buffer.batch_size)
            sequence_length: Length of sequences for LSTM training (required for recurrent agents)
            max_grad_norm: Gradient clipping threshold (required; typically from training.yaml)
            max_episodes: Maximum training episodes (for PER beta annealing)
            max_steps_per_episode: Maximum steps per episode (for PER beta annealing)
        """
        # ✅ WP-C2: Validate brain_config required (no legacy fallback)
        if brain_config is None:
            raise ValueError(
                "brain_config is required. Legacy initialization path removed in WP-C2. "
                "Provide brain.yaml configuration for all training runs. "
                "See docs/config-schemas/brain.md for examples."
            )

        # The compiled token artifact is the observation ABI (unit-3 cut). It is required
        # and set by VectorizedHamletEnv from the compiled universe; no silent fallback.
        if getattr(env, "token_spec", None) is None:
            raise ValueError(
                "env.token_spec is required. The environment must carry the compiled TokenSpec "
                "from the compiled universe. This is set automatically by VectorizedHamletEnv."
            )
        self.token_spec = env.token_spec

        self.env = env
        self.curriculum = curriculum
        self.exploration = exploration
        self.agent_ids = agent_ids
        self.num_agents = len(agent_ids)
        self.device = device
        self.tb_logger = tb_logger
        self.brain_config = brain_config
        self.max_episodes = max_episodes
        self.max_steps_per_episode = max_steps_per_episode

        # Brain_config always provided (no else branch needed)
        self.gamma = brain_config.q_learning.gamma
        self.use_double_dqn = brain_config.q_learning.use_double_dqn
        target_update_frequency = brain_config.q_learning.target_update_frequency

        self.action_dim = action_dim

        # Agent runtime metrics (telemetry + reward baseline source of truth)
        self.runtime_registry = AgentRuntimeRegistry(agent_ids=agent_ids, device=device)
        self.env.attach_runtime_registry(self.runtime_registry)

        # Wire exploration module to environment for intrinsic reward computation
        self.env.set_exploration_module(exploration)

        # Training metrics (for TensorBoard logging)
        self.last_td_error = 0.0
        self.last_loss = 0.0
        self.last_q_values_mean = 0.0
        self.last_training_step = 0
        self.last_rnd_loss = 0.0  # RND predictor loss (for monitoring intrinsic exploration)
        self._per_beta_warning_logged = False  # POP-006: Track if we've warned about missing annealing params

        # Q-network (shared across all agents for now)
        # Store params needed for network building helper
        self._vision_window_size = vision_window_size
        self._obs_dim = obs_dim

        # Build network using DRY helper (POP-001)
        self.q_network: nn.Module = self._build_network(brain_config, obs_dim, action_dim, env, vision_window_size).to(device)

        # Set is_recurrent flag from brain_config
        self.is_recurrent = brain_config.architecture.type == "recurrent"

        # Set is_dueling flag from brain_config
        self.is_dueling = brain_config.architecture.type == "dueling"

        # Set is_set_encoder flag from brain_config
        self.is_set_encoder = brain_config.architecture.type == "set_encoder"

        # Set is_token_set flag from brain_config (token-obs unit 3 Task 9)
        self.is_token_set = brain_config.architecture.type == "token_set"

        # Target network (stabilises training for both feed-forward and recurrent agents)
        # Build using DRY helper (POP-001)
        self.target_network: nn.Module = self._build_network(brain_config, obs_dim, action_dim, env, vision_window_size).to(device)

        # Initialize common target network state
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()  # Target network always in eval mode
        self.target_update_frequency = target_update_frequency
        self.training_step_counter = 0

        # Propagate temporal mechanics flag from environment to recurrent networks.
        if self.is_recurrent and hasattr(env, "enable_temporal_mechanics"):
            temporal_enabled = bool(getattr(env, "enable_temporal_mechanics"))
            if hasattr(self.q_network, "enable_temporal_features"):
                self.q_network.enable_temporal_features = temporal_enabled  # type: ignore[assignment]
            if hasattr(self.target_network, "enable_temporal_features"):
                self.target_network.enable_temporal_features = temporal_enabled  # type: ignore[assignment]

        # Optimizer and scheduler from brain_config
        self.optimizer, self.scheduler = OptimizerFactory.build(
            config=brain_config.optimizer,
            parameters=self.q_network.parameters(),
        )

        # Loss function from brain_config
        self.loss_fn = LossFactory.build(config=brain_config.loss)
        # Store loss config for PER path (needs functional API with reduction='none')
        self.loss_type = brain_config.loss.type
        # Set delta for huber loss (Pydantic validates not None when type="huber")
        if brain_config.loss.type == "huber":
            assert brain_config.loss.huber_delta is not None
            self.loss_delta: float = brain_config.loss.huber_delta
        else:
            self.loss_delta = 1.0

        # Replay buffer (dual system: sequential for recurrent, standard/PER for feedforward)
        # TASK-005 Phase 3: Support PrioritizedReplayBuffer
        from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer

        self.replay_buffer: ReplayBuffer | SequentialReplayBuffer | PrioritizedReplayBuffer
        self.current_episodes: list[EpisodeContainer] = []

        # Determine if PER is enabled from brain_config
        self.use_per = brain_config.replay.prioritized

        # Replay buffer capacity from brain_config
        replay_capacity = brain_config.replay.capacity

        if self.is_recurrent:
            # Recurrent networks use sequential buffer (PER not yet supported for sequences)
            self.replay_buffer = SequentialReplayBuffer(capacity=replay_capacity, device=device)
            # Episode tracking for sequential buffer
            self.current_episodes = [self._new_episode_container() for _ in range(self.num_agents)]

            # TASK-005 Phase 3: Raise NotImplementedError for PER + recurrent
            if self.use_per:
                raise NotImplementedError(
                    "Prioritized replay not yet supported for recurrent networks. "
                    "Use prioritized=false in brain.yaml for recurrent architectures."
                )
        else:
            # Feedforward networks support both standard and prioritized replay
            if self.use_per:
                # TASK-005 Phase 3: Instantiate PrioritizedReplayBuffer
                # Pydantic validator ensures PER params not None when prioritized=True
                assert brain_config.replay.priority_alpha is not None
                assert brain_config.replay.priority_beta is not None
                assert brain_config.replay.priority_beta_annealing is not None
                self.replay_buffer = PrioritizedReplayBuffer(
                    capacity=replay_capacity,
                    alpha=brain_config.replay.priority_alpha,
                    beta=brain_config.replay.priority_beta,
                    beta_annealing=brain_config.replay.priority_beta_annealing,
                    device=device,
                )
            else:
                self.replay_buffer = ReplayBuffer(capacity=replay_capacity, device=device)

        # Training hyperparameters (configurable)
        self.total_steps = 0
        self.train_frequency = train_frequency
        self.sequence_length = sequence_length
        self.max_grad_norm = max_grad_norm
        self.batch_size = batch_size

        # Episode step counters (reset on done)
        self.episode_step_counts = torch.zeros(self.num_agents, dtype=torch.long, device=device)

        # Current state
        self.current_obs = torch.zeros((self.num_agents, obs_dim), dtype=torch.float32, device=device)
        self.current_epsilons = torch.zeros(self.num_agents, dtype=torch.float32, device=device)
        self.current_curriculum_decisions: list[CurriculumDecision] = []  # Store curriculum decisions
        self.current_depletion_multiplier: float = 1.0  # Track curriculum difficulty

        # WS-1(b): rollout memory is population-owned; the network holds no state.
        self.rollout_hidden: tuple[torch.Tensor, torch.Tensor] | None = None
        if self.is_recurrent:
            recurrent_network = cast(RecurrentSpatialQNetwork, self.q_network)
            self.rollout_hidden = recurrent_network.initial_hidden(self.num_agents, self.device)
        # Q-values recorded by the action selectors (read by the live-inference display).
        self.last_selected_q_values: torch.Tensor | None = None

    def reset(self) -> None:
        """Reset all environments and state."""
        self.current_obs = self.env.reset()

        # Re-seed population-owned rollout memory (if applicable)
        if self.is_recurrent:
            recurrent_network = cast(RecurrentSpatialQNetwork, self.q_network)
            self.rollout_hidden = recurrent_network.initial_hidden(self.num_agents, self.device)

        # Get epsilon from exploration strategy (handle both direct and composed)
        # Sync telemetry + exploration metrics (initial epsilon / stage)
        self.sync_exploration_metrics()
        self._sync_curriculum_metrics()

    # ------------------------------------------------------------------ #
    # Episode lifecycle helpers
    # ------------------------------------------------------------------ #
    def _new_episode_container(self) -> EpisodeContainer:
        """Create a fresh container for accumulating episode data.

        CRIT-07: Now uses single 'rewards' key for DAC-composed totals,
        plus component keys for provenance tracking.
        """
        return {
            "observations": [],
            "actions": [],
            "rewards": [],  # CRIT-07: Single rewards field for DAC-composed totals
            "rewards_extrinsic": [],  # DAC extrinsic component
            "rewards_intrinsic": [],  # DAC intrinsic component (after modifiers)
            "rewards_shaping": [],  # DAC shaping component
            "dones": [],
            "next_observations": [],  # WS-1(c): successor for the window-boundary bootstrap
        }

    # ------------------------------------------------------------------ #
    # TensorBoard logging helper (POP-002 DRY)
    # ------------------------------------------------------------------ #
    def _log_network_histograms(self) -> None:
        """Log network weight/gradient histograms to TensorBoard.

        Called during training to monitor parameter distributions.
        Only logs every 100 steps to avoid performance overhead.
        """
        if self.tb_logger is None or self.total_steps % 100 != 0:
            return
        for name, param in self.q_network.named_parameters():
            self.tb_logger.writer.add_histogram(f"Network/Weights/{name}", param.data, self.total_steps)
            if param.grad is not None:
                self.tb_logger.writer.add_histogram(f"Network/Gradients/{name}", param.grad, self.total_steps)

    def _log_reward_components(
        self,
        components: dict[str, torch.Tensor],
        intrinsic_weight: torch.Tensor | None,
    ) -> None:
        """Log reward component means to TensorBoard.

        Args:
            components: DAC reward components dict with keys:
                - "extrinsic": Extrinsic (environment) rewards
                - "intrinsic": Intrinsic (exploration) rewards after modifiers
                - "shaping": Shaping bonus rewards
                - "intrinsic_raw": (optional) Intrinsic before modifiers
            intrinsic_weight: Effective intrinsic weight after modifiers
        """
        if self.tb_logger is None:
            return

        step = self.total_steps

        # Log mean values across all agents
        self.tb_logger.log_custom_metric("Rewards/Extrinsic_Mean", components["extrinsic"].mean().item(), step)
        self.tb_logger.log_custom_metric("Rewards/Intrinsic_Mean", components["intrinsic"].mean().item(), step)
        self.tb_logger.log_custom_metric("Rewards/Shaping_Mean", components["shaping"].mean().item(), step)

        # Log intrinsic_raw if available (before modifiers)
        if "intrinsic_raw" in components:
            self.tb_logger.log_custom_metric("Rewards/Intrinsic_Raw_Mean", components["intrinsic_raw"].mean().item(), step)

        # Log effective intrinsic weight
        if intrinsic_weight is not None:
            self.tb_logger.log_custom_metric("Rewards/Intrinsic_Weight_Mean", intrinsic_weight.mean().item(), step)

    # ------------------------------------------------------------------ #
    # Network building helper (POP-001 DRY)
    # ------------------------------------------------------------------ #
    def _build_network(
        self,
        brain_config: BrainConfig,
        obs_dim: int,
        action_dim: int,
        env: VectorizedHamletEnv,
        vision_window_size: int,
    ) -> nn.Module:
        """Build network from brain_config (DRY helper for q_network and target_network).

        Args:
            brain_config: Brain configuration specifying architecture
            obs_dim: Observation dimension
            action_dim: Action dimension
            env: Environment for substrate/meter info (recurrent networks)
            vision_window_size: Vision window size (recurrent networks)

        Returns:
            Constructed network module (not yet moved to device)

        """
        arch = brain_config.architecture
        if arch.type == "feedforward":
            assert arch.feedforward is not None, "feedforward config must be present"
            return NetworkFactory.build_feedforward(
                config=arch.feedforward,
                obs_dim=obs_dim,
                action_dim=action_dim,
            )
        elif arch.type == "recurrent":
            assert arch.recurrent is not None, "recurrent config must be present"
            # Post-cut this is a token-BLOCK reader: its input slices come from the
            # compiled TokenSpec's contiguous per-type serialization, not from a raster
            # observation spec. A token-NATIVE recurrent/attention brain is unit 4.
            return NetworkFactory.build_recurrent(
                config=arch.recurrent,
                action_dim=action_dim,
                substrate_position_dim=env.substrate.position_dim,
                token_spec=env.token_spec,
            )
        elif arch.type == "dueling":
            assert arch.dueling is not None, "dueling config must be present"
            return NetworkFactory.build_dueling(
                config=arch.dueling,
                obs_dim=obs_dim,
                action_dim=action_dim,
            )
        elif arch.type == "set_encoder":
            raise ValueError(
                "architecture.type='set_encoder' has no buildable network after the unit-3 token cut.\n"
                "  Reason: it sliced a single flattened token FIELD out of the compiled "
                "ObservationSpec, and that spec no longer exists — the whole observation is now a "
                "token set.\n"
                "  Landing: declare `token_set`, which consumes the compiled TokenSpec directly."
            )
        elif arch.type == "token_set":
            assert arch.token_set is not None, "token_set config must be present"
            token_spec = env.universe.token_spec
            # IDENTITY, not width (task-9 review M3, discharged at the cut): the network
            # reads the serialization positionally, so equal width with a different slot
            # binding is a silently wrong net. `layout_hash` IS that identity.
            env_layout_hash = compute_token_layout_hash(env.token_spec)
            if env_layout_hash != compute_token_layout_hash(token_spec):
                raise ValueError(
                    "architecture.type='token_set' is bound to a different token layout than the "
                    "environment serializes.\n"
                    f"  environment layout_hash: {env_layout_hash}\n"
                    f"  brain layout_hash:       {compute_token_layout_hash(token_spec)}\n"
                    "  Rule: a flat reader's dims are positional — equal width with a re-bound slot "
                    "changes what every dim MEANS. Recompile the pack so both come from one artifact."
                )
            return NetworkFactory.build_token_set(
                config=arch.token_set,
                action_dim=action_dim,
                token_spec=token_spec,
            )
        else:
            raise ValueError(
                f"Unsupported architecture type: {arch.type}. Supported: feedforward, recurrent, dueling, set_encoder, token_set"
            )

    def _store_episode_and_reset(self, agent_idx: int) -> bool:
        """Store accumulated episode for agent and reset buffers."""
        if not self.is_recurrent or not self.current_episodes:
            return False

        episode = self.current_episodes[agent_idx]
        if len(episode["observations"]) == 0:
            return False

        sequential_buffer = cast(SequentialReplayBuffer, self.replay_buffer)

        # CRIT-07: Store episode with components for provenance tracking
        episode_data = {
            "observations": torch.stack(episode["observations"]),
            "actions": torch.stack(episode["actions"]),
            "rewards": torch.stack(episode["rewards"]),
            "dones": torch.stack(episode["dones"]),
            "next_observations": torch.stack(episode["next_observations"]),
        }

        # Add components if present
        if len(episode["rewards_extrinsic"]) > 0:
            episode_data["rewards_extrinsic"] = torch.stack(episode["rewards_extrinsic"])
            episode_data["rewards_intrinsic"] = torch.stack(episode["rewards_intrinsic"])
            episode_data["rewards_shaping"] = torch.stack(episode["rewards_shaping"])

        sequential_buffer.store_episode(episode_data)

        self.current_episodes[agent_idx] = self._new_episode_container()
        return True

    def _reset_hidden_state(self, agent_idx: int) -> None:
        """Zero the population-owned rollout memory for a single agent (episode boundary)."""
        if not self.is_recurrent:
            return

        assert self.rollout_hidden is not None, "rollout_hidden is seeded in __init__ for recurrent populations"
        h, c = self.rollout_hidden
        # In-place zeroing is deliberate and safe: every producer of rollout_hidden
        # runs under torch.no_grad(), so there is no autograd graph to corrupt.
        # Do not "fix" this into a clone.
        h[:, agent_idx, :] = 0.0
        c[:, agent_idx, :] = 0.0

    def _unroll_recurrent(
        self, network: RecurrentSpatialQNetwork, observations: torch.Tensor
    ) -> tuple[list[torch.Tensor], tuple[torch.Tensor, torch.Tensor]]:
        """Unroll `network` over a sampled batch, threading hidden state t -> t+1.

        Hidden state is LOCAL to this unroll: it starts at zeros for every sampled
        sequence (DRQN zero-start, retained deliberately - the WS-1(b) defect was
        the missing carry between timesteps, not the zero start). The rollout
        memory in self.rollout_hidden is never touched.

        Args:
            observations: [batch, seq_len, obs_dim]

        Returns:
            (q_values_per_step, final_hidden): per-timestep Q-values, each
            [batch, action_dim], and the hidden state after the last timestep -
            the state the WS-1(c) boundary bootstrap must evaluate under.
        """
        batch_size, seq_len = observations.shape[0], observations.shape[1]
        hidden = network.initial_hidden(batch_size, observations.device)
        q_values_per_step: list[torch.Tensor] = []
        for t in range(seq_len):
            q_values, hidden = network(observations[:, t, :], hidden)
            q_values_per_step.append(q_values)
        return q_values_per_step, hidden

    # ------------------------------------------------------------------ #
    # Telemetry synchronisation helpers
    # ------------------------------------------------------------------ #
    def _get_current_epsilon_value(self) -> float:
        """Return current exploration epsilon (global for now)."""
        if isinstance(self.exploration, AdaptiveIntrinsicExploration):
            return float(self.exploration.rnd.epsilon)
        if hasattr(self.exploration, "epsilon"):
            return float(self.exploration.epsilon)
        return 0.0

    def _get_current_intrinsic_weight_value(self) -> float:
        """Return current intrinsic reward weight."""
        if hasattr(self.exploration, "get_intrinsic_weight"):
            return float(self.exploration.get_intrinsic_weight())
        return 0.0

    def _sync_curriculum_metrics(self) -> None:
        """
        Write curriculum metadata (stage) into the runtime registry.

        Prefers the most recent curriculum decisions; falls back to tracker state
        when decisions are unavailable (e.g. before the first population step).
        """
        if self.current_curriculum_decisions:
            for idx, decision in enumerate(self.current_curriculum_decisions):
                stage_value = self._difficulty_to_stage(float(decision.difficulty_level))
                self.runtime_registry.set_curriculum_stage(agent_idx=idx, stage=stage_value)
            return

        tracker = getattr(self.curriculum, "tracker", None)
        if tracker is None or not hasattr(tracker, "agent_stages"):
            return

        for idx in range(self.num_agents):
            stage_value = int(tracker.agent_stages[idx].item())
            self.runtime_registry.set_curriculum_stage(agent_idx=idx, stage=stage_value)

    @staticmethod
    def _difficulty_to_stage(difficulty_level: float) -> int:
        """Convert curriculum difficulty (0.0-1.0) to discrete stage (1-5)."""
        stage = int(round(difficulty_level * 4.0)) + 1
        return max(1, min(5, stage))

    def sync_exploration_metrics(self) -> None:
        """
        Synchronise exploration parameters (epsilon, intrinsic weight) to registry.

        Also refreshes current_epsilons to keep action selection in sync with telemetry.
        """
        epsilon_tensor = torch.full(
            (self.num_agents,),
            self._get_current_epsilon_value(),
            dtype=torch.float32,
            device=self.device,
        )
        self.current_epsilons = epsilon_tensor

        intrinsic_weight = self._get_current_intrinsic_weight_value()

        for idx in range(self.num_agents):
            self.runtime_registry.set_epsilon(agent_idx=idx, epsilon=epsilon_tensor[idx])
            self.runtime_registry.set_intrinsic_weight(agent_idx=idx, weight=intrinsic_weight)

    def _finalize_episode(self, agent_idx: int, survival_time: int) -> None:
        """Finalize episode metadata and bookkeeping after store."""
        self.runtime_registry.record_survival_time(agent_idx=agent_idx, steps=survival_time)

        if isinstance(self.exploration, AdaptiveIntrinsicExploration):
            self.exploration.update_on_episode_end(survival_time=survival_time)

        # Sync exploration telemetry after any annealing/decay changes
        self.sync_exploration_metrics()

        self.episode_step_counts[agent_idx] = 0
        self._reset_hidden_state(agent_idx)

    def flush_episode(self, agent_idx: int) -> None:
        """
        Flush current episode for an agent to replay buffer.

        Used when agent dies or episode hits max_steps.
        This prevents memory leaks and ensures successful episodes reach the replay buffer.

        Args:
            agent_idx: Index of agent to flush
        """
        if not self.is_recurrent:
            # Feedforward mode: transitions already in buffer, nothing to flush
            return

        episode = self.current_episodes[agent_idx]
        if len(episode["observations"]) == 0:
            # Nothing to flush
            return

        survival_time = len(episode["observations"])
        self._store_episode_and_reset(agent_idx)
        self._finalize_episode(agent_idx, survival_time)

    def select_greedy_actions(self, env: VectorizedHamletEnv) -> torch.Tensor:
        """
        Select greedy actions with action masking for inference.

        This is the canonical way to select actions during inference.
        Uses the same action masking logic as training to prevent boundary violations.

        Args:
            env: Environment to get action masks from

        Returns:
            actions: [num_agents] tensor of selected actions
        """
        with torch.no_grad():
            # Get Q-values from network (recurrent: advance the rollout memory)
            if self.is_recurrent:
                recurrent_network = cast(RecurrentSpatialQNetwork, self.q_network)
                assert self.rollout_hidden is not None
                q_values, self.rollout_hidden = recurrent_network(self.current_obs, self.rollout_hidden)
            else:
                q_values = self.q_network(self.current_obs)
            # Record BEFORE any early exit so the live Q-value display never reads stale values (plan §3 H8).
            self.last_selected_q_values = q_values

            # Get action masks from environment
            action_masks = env.get_action_masks()

            # Mask invalid actions with -inf before argmax
            masked_q_values = q_values.clone()
            masked_q_values[~action_masks] = float("-inf")

            # Select best valid action
            actions: torch.Tensor = masked_q_values.argmax(dim=1)

        return actions

    def select_epsilon_greedy_actions(self, env: VectorizedHamletEnv, epsilon: float) -> torch.Tensor:
        """
        Select epsilon-greedy actions with action masking.

        With probability epsilon, select random valid action.
        With probability (1-epsilon), select greedy action.

        Args:
            env: Environment to get action masks from
            epsilon: Exploration rate [0, 1]

        Returns:
            actions: [num_agents] tensor of selected actions
        """
        with torch.no_grad():
            # Get Q-values from network (recurrent: advance the rollout memory)
            if self.is_recurrent:
                recurrent_network = cast(RecurrentSpatialQNetwork, self.q_network)
                assert self.rollout_hidden is not None
                q_values, self.rollout_hidden = recurrent_network(self.current_obs, self.rollout_hidden)
            else:
                q_values = self.q_network(self.current_obs)
            # The return below sits inside this no_grad block: record the Q-values
            # HERE, before the action-mask fetch, or the live display is permanently
            # None (plan §3 H8 - a silent regression no test upstream catches).
            self.last_selected_q_values = q_values

            # Get action masks from environment
            action_masks = env.get_action_masks()

            # Use shared epsilon-greedy action selection
            epsilons = torch.full((self.num_agents,), epsilon, device=self.device, dtype=torch.float32)
            return epsilon_greedy_action_selection(
                q_values=q_values,
                epsilons=epsilons,
                action_masks=action_masks,
            )

    def step_population(
        self,
        envs: VectorizedHamletEnv,
    ) -> BatchedAgentState:
        """
        Execute one training step for entire population.

        Args:
            envs: Vectorized environment (same as self.env)

        Returns:
            BatchedAgentState with all agent data after step
        """

        # POP-004: Validate device consistency to prevent cryptic PyTorch errors
        # Compare device types robustly - cuda:0 == cuda (default device)
        def _same_device(a: torch.device, b: torch.device) -> bool:
            """Check if two devices are the same, handling cuda vs cuda:0."""
            if a.type != b.type:
                return False
            if a.type == "cuda":
                # cuda (no index) means device 0, same as cuda:0
                a_idx = a.index if a.index is not None else 0
                b_idx = b.index if b.index is not None else 0
                return a_idx == b_idx
            return True

        if not _same_device(self.current_obs.device, self.device):
            raise RuntimeError(
                f"Observation tensor on {self.current_obs.device} but population on {self.device}. "
                f"Ensure environment and population use the same device."
            )

        # 1. Get Q-values from network
        with torch.no_grad():
            if self.is_recurrent:
                recurrent_network = cast(RecurrentSpatialQNetwork, self.q_network)
                assert self.rollout_hidden is not None
                # Thread and advance the population-owned rollout memory.
                q_values, self.rollout_hidden = recurrent_network(self.current_obs, self.rollout_hidden)
            else:
                q_values = self.q_network(self.current_obs)

        # 2. Create temporary agent state for curriculum decision
        temp_state = BatchedAgentState(
            observations=self.current_obs,
            actions=torch.zeros(self.num_agents, dtype=torch.long, device=self.device),
            rewards=torch.zeros(self.num_agents, device=self.device),
            dones=torch.zeros(self.num_agents, dtype=torch.bool, device=self.device),
            epsilons=self.current_epsilons,
            intrinsic_rewards=torch.zeros(self.num_agents, device=self.device),
            survival_times=envs.step_counts.clone(),
            device=self.device,
        )

        # 3. Get curriculum decisions (pass Q-values if curriculum supports it)
        if hasattr(self.curriculum, "get_batch_decisions_with_qvalues"):
            # AdversarialCurriculum - pass Q-values for entropy calculation
            self.current_curriculum_decisions = self.curriculum.get_batch_decisions_with_qvalues(
                temp_state,
                self.agent_ids,
                q_values,
            )
        else:
            # StaticCurriculum or other curricula - no Q-values needed
            self.current_curriculum_decisions = self.curriculum.get_batch_decisions(
                temp_state,
                self.agent_ids,
            )

        # 3.5 Sync curriculum metrics to registry
        self._sync_curriculum_metrics()

        # 4. Get action masks from environment
        action_masks = envs.get_action_masks()

        # 5. Select actions via exploration strategy (with action masking)
        actions = self.exploration.select_actions(q_values, temp_state, action_masks)

        # 6. Extract curriculum difficulty multiplier
        depletion_multiplier = 1.0
        if self.current_curriculum_decisions:
            depletion_multiplier = self.current_curriculum_decisions[0].depletion_multiplier

        # 7. Step environment with curriculum difficulty
        # Note: rewards from environment already contain full DAC composition:
        #   rewards = extrinsic + (intrinsic * base_weight * modifiers) + shaping
        next_obs, rewards, dones, info = envs.step(actions, depletion_multiplier)

        # 7. Compute intrinsic rewards for logging/tracking only (not added to rewards)
        # DAC engine already includes intrinsic in the rewards tensor above
        # BUG-22 FIX: Don't update stats here - they're updated in the environment during reward calculation
        intrinsic_rewards = torch.zeros_like(rewards)
        if isinstance(self.exploration, RNDExploration | AdaptiveIntrinsicExploration):
            intrinsic_rewards = self.exploration.compute_intrinsic_rewards(self.current_obs, update_stats=False)

        # 7. Store transition in replay buffer
        # Extract DAC components from info dict for provenance tracking
        components = info.get("reward_components", {})
        intrinsic_weight = info.get("intrinsic_weight")

        reward_tensor = RewardTensor.from_dac(
            total=rewards,
            extrinsic=components.get("extrinsic"),
            intrinsic=components.get("intrinsic"),
            shaping=components.get("shaping"),
        )

        # Log components to TensorBoard (step-level aggregation)
        if self.tb_logger is not None and components:
            self._log_reward_components(
                components=components,
                intrinsic_weight=intrinsic_weight,
            )

        if self.is_recurrent:
            # For recurrent networks: accumulate episodes with components
            for i in range(self.num_agents):
                self.current_episodes[i]["observations"].append(self.current_obs[i].cpu())
                self.current_episodes[i]["actions"].append(actions[i].cpu())
                self.current_episodes[i]["rewards"].append(rewards[i].cpu())
                self.current_episodes[i]["rewards_extrinsic"].append(components["extrinsic"][i].cpu())
                self.current_episodes[i]["rewards_intrinsic"].append(components["intrinsic"][i].cpu())
                self.current_episodes[i]["rewards_shaping"].append(components["shaping"][i].cpu())
                self.current_episodes[i]["dones"].append(dones[i].cpu())
                # WS-1(c): at a done step next_obs[i] is the post-reset observation -
                # harmless and correct, the (~dones) factor zeros its bootstrap, and it
                # is exactly what the feedforward path stores. Do not special-case it.
                self.current_episodes[i]["next_observations"].append(next_obs[i].cpu())
        else:
            # For feedforward networks: store individual transitions
            # Both ReplayBuffer and PrioritizedReplayBuffer accept RewardTensor
            # SequentialReplayBuffer is only used for recurrent (not in this branch)
            self.replay_buffer.push(  # type: ignore[union-attr]
                observations=self.current_obs,
                actions=actions,
                rewards=reward_tensor,  # CRIT-07: RewardTensor with DAC-composed total
                next_observations=next_obs,
                dones=dones,
            )

        # 8. Train RND predictor (if applicable)
        if isinstance(self.exploration, RNDExploration | AdaptiveIntrinsicExploration):
            rnd = self.exploration.rnd if isinstance(self.exploration, AdaptiveIntrinsicExploration) else self.exploration
            # Accumulate observations in RND buffer
            for i in range(self.num_agents):
                rnd.obs_buffer.append(self.current_obs[i].cpu())
            # Train predictor if buffer is full
            rnd_loss = rnd.update_predictor()
            # Track RND loss for monitoring (similar to Q-network loss)
            self.last_rnd_loss = rnd_loss

        # 9. Train Q-network from replay buffer (every train_frequency steps)
        self.total_steps += 1
        # For recurrent: need enough episodes (16+) for sequence sampling
        # For feedforward: need enough transitions (>= batch_size) for batch sampling
        min_buffer_size = 16 if self.is_recurrent else self.batch_size
        # All buffer types implement __len__, but mypy doesn't infer it for unions
        if self.total_steps % self.train_frequency == 0 and len(self.replay_buffer) >= min_buffer_size:  # type: ignore[arg-type]
            # MED-13: Removed intrinsic_weight parameter - DAC already composes rewards before storage

            if self.is_recurrent:
                # Sequential LSTM training with target network for temporal dependencies
                sequential_buffer = cast(SequentialReplayBuffer, self.replay_buffer)
                batch = sequential_buffer.sample_sequences(
                    batch_size=self.batch_size,
                    seq_len=self.sequence_length,
                )

                seq_len = batch["observations"].shape[1]

                # PASS 1: Q-predictions from the online network, hidden state threaded
                # t -> t+1 through the sampled window (gradient flows through the unroll).
                recurrent_network = cast(RecurrentSpatialQNetwork, self.q_network)
                q_values_online_list, online_final_hidden = self._unroll_recurrent(recurrent_network, batch["observations"])
                q_pred_list = []
                for t in range(seq_len):
                    q_pred = q_values_online_list[t].gather(1, batch["actions"][:, t].unsqueeze(1)).squeeze()
                    q_pred_list.append(q_pred)

                # PASS 2: Q-targets. The last index of a sampled window is a WINDOW
                # boundary, not a terminal (WS-1(c)): it bootstraps from the stored
                # successor next_observations[:, -1], evaluated under the hidden
                # state accumulated over the window. A real terminal at the boundary
                # is still zeroed by the (~dones) factor in the shared formula.
                with torch.no_grad():
                    boundary_next_obs = batch["next_observations"][:, -1, :]

                    if self.use_double_dqn:
                        # Boundary forward for the ONLINE network, immediately after
                        # its unroll and under ITS final hidden state. Order is
                        # load-bearing: moving this after the target unroll, or
                        # crossing the two hidden states, silently evaluates the
                        # successor under the wrong network's trajectory (plan H6;
                        # the networks have different weights).
                        q_online_boundary, _ = recurrent_network(boundary_next_obs, online_final_hidden)

                    target_recurrent = cast(RecurrentSpatialQNetwork, self.target_network)
                    q_values_target_list, target_final_hidden = self._unroll_recurrent(target_recurrent, batch["observations"])
                    # Boundary forward for the TARGET network, under its own final hidden state.
                    q_target_boundary, _ = target_recurrent(boundary_next_obs, target_final_hidden)

                    if self.use_double_dqn:
                        # Double DQN: online network selects, target network evaluates.
                        # Action selection reuses PASS 1's online unroll - a third
                        # unroll would recompute the same trajectory.
                        next_action_list = [q_values_online.argmax(1) for q_values_online in q_values_online_list]

                        q_target_list = []
                        for t in range(seq_len):
                            if t < seq_len - 1:
                                # Use Q-values from t+1, evaluated at actions selected by online network
                                next_actions = next_action_list[t + 1]
                                q_next = q_values_target_list[t + 1].gather(1, next_actions.unsqueeze(1)).squeeze(1)
                            else:
                                # Window boundary: successor evaluated at the online network's argmax
                                boundary_actions = q_online_boundary.argmax(1)
                                q_next = q_target_boundary.gather(1, boundary_actions.unsqueeze(1)).squeeze(1)
                            q_target = batch["rewards"][:, t] + self.gamma * q_next * (~batch["dones"][:, t]).float()
                            q_target_list.append(q_target)
                    else:
                        # Vanilla DQN: target network both selects and evaluates
                        q_target_list = []
                        for t in range(seq_len):
                            if t < seq_len - 1:
                                # Use Q-values from t+1 (computed with hidden state from t)
                                q_next = q_values_target_list[t + 1].max(1)[0]
                            else:
                                # Window boundary: successor evaluated by the target network
                                q_next = q_target_boundary.max(1)[0]
                            q_target = batch["rewards"][:, t] + self.gamma * q_next * (~batch["dones"][:, t]).float()
                            q_target_list.append(q_target)

                # Compute loss across all timesteps with post-terminal masking (P2.2)
                q_pred_all = torch.stack(q_pred_list, dim=1)  # [batch, seq_len]
                q_target_all = torch.stack(q_target_list, dim=1)  # [batch, seq_len]

                # P2.2: Apply mask to prevent gradients from post-terminal garbage
                # TASK-005 Phase 1: Use configured loss type (element-wise for masking)
                # POP-003: Removed redundant None checks - brain_config is required in __init__
                if self.brain_config.loss.type == "huber":
                    losses = F.huber_loss(
                        q_pred_all,
                        q_target_all,
                        reduction="none",
                        delta=self.loss_delta,  # Already set in __init__ with proper type
                    )
                elif self.brain_config.loss.type == "smooth_l1":
                    losses = F.smooth_l1_loss(q_pred_all, q_target_all, reduction="none")
                elif self.brain_config.loss.type == "mse":
                    losses = F.mse_loss(q_pred_all, q_target_all, reduction="none")
                else:
                    raise ValueError(f"Unsupported loss type: {self.brain_config.loss.type}. Must be one of {{'huber','smooth_l1','mse'}}.")
                mask = batch["mask"].float()  # [batch, seq_len] - True for valid timesteps
                masked_loss = (losses * mask).sum() / mask.sum().clamp_min(1)
                loss: torch.Tensor = masked_loss

                # Store training metrics
                with torch.no_grad():
                    # Compute metrics only on valid (masked) timesteps
                    valid_errors = ((q_target_all - q_pred_all).abs() * mask).sum() / mask.sum().clamp_min(1)
                    self.last_td_error = valid_errors.item()
                    self.last_loss = loss.item()
                    # Q-values mean across valid timesteps only
                    valid_q_mean = (q_pred_all * mask).sum() / mask.sum().clamp_min(1)
                    self.last_q_values_mean = valid_q_mean.item()
                    self.last_training_step = self.total_steps

                # Backprop and optimize
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=self.max_grad_norm)
                self.optimizer.step()

                # Step scheduler if present (TASK-005 Phase 2)
                if self.scheduler is not None:
                    self.scheduler.step()

                # Log network statistics to TensorBoard (POP-002 DRY helper)
                self._log_network_histograms()

                # Update target network periodically
                self.training_step_counter += 1
                if self.training_step_counter % self.target_update_frequency == 0:
                    self.target_network.load_state_dict(self.q_network.state_dict())

                # NOTE (WS-1(b)): no rollout-memory reset here. Training uses hidden
                # state local to _unroll_recurrent; the old post-training reset was
                # the clobber that zeroed mid-episode rollout memory (measured:
                # 207/936 mid-episode forwards received an exactly-zero hidden state).
            else:
                # Standard feedforward DQN training (with optional PER)
                # TASK-005 Phase 3: Support both standard and prioritized replay
                if self.use_per:
                    from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer

                    per_buffer = cast(PrioritizedReplayBuffer, self.replay_buffer)
                    batch = per_buffer.sample(batch_size=self.batch_size)
                    weights = batch["weights"]  # Importance sampling weights
                    indices = cast(np.ndarray, batch["indices"])  # For priority updates
                else:
                    standard_buffer = cast(ReplayBuffer, self.replay_buffer)
                    batch = standard_buffer.sample(batch_size=self.batch_size)  # MED-13: Removed intrinsic_weight
                    weights = torch.ones(self.batch_size, device=self.device)  # Uniform weights

                # Compute Q-predictions from online network
                q_pred = self.q_network(batch["observations"]).gather(1, batch["actions"].unsqueeze(1)).squeeze()

                # Compute Q-targets (vanilla DQN vs Double DQN)
                with torch.no_grad():
                    if self.use_double_dqn:
                        # Double DQN: Use online network for action selection, target network for evaluation
                        next_actions = self.q_network(batch["next_observations"]).argmax(1)
                        q_next = self.target_network(batch["next_observations"]).gather(1, next_actions.unsqueeze(1)).squeeze()
                    else:
                        # Vanilla DQN: Use target network for both selection and evaluation
                        q_next = self.target_network(batch["next_observations"]).max(1)[0]

                    q_target = batch["rewards"] + self.gamma * q_next * (~batch["dones"]).float()

                # TASK-005 Phase 3: Compute TD errors for PER priority updates
                td_errors = (q_pred - q_target).abs()

                # TASK-005 Phase 3: Weighted loss for importance sampling correction
                if self.use_per:
                    # PER: Apply importance sampling weights to loss
                    # Use functional API with reduction='none' to get per-sample losses
                    if self.loss_type == "mse":
                        per_sample_loss = F.mse_loss(q_pred, q_target, reduction="none")
                    elif self.loss_type == "huber":
                        per_sample_loss = F.huber_loss(q_pred, q_target, reduction="none", delta=self.loss_delta)
                    elif self.loss_type == "smooth_l1":
                        per_sample_loss = F.smooth_l1_loss(q_pred, q_target, reduction="none")
                    else:
                        raise ValueError(f"Unsupported loss type for PER: {self.loss_type}")
                    loss = (weights * per_sample_loss).mean()
                else:
                    # Standard: Use configured loss function
                    loss = self.loss_fn(q_pred, q_target)

                # Store training metrics
                with torch.no_grad():
                    self.last_td_error = (q_target - q_pred).abs().mean().item()
                    self.last_loss = loss.item()
                    self.last_q_values_mean = q_pred.mean().item()
                    self.last_training_step = self.total_steps

                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=self.max_grad_norm)
                self.optimizer.step()

                # Step scheduler if present (TASK-005 Phase 2)
                if self.scheduler is not None:
                    self.scheduler.step()

                # TASK-005 Phase 3: Update priorities in PER buffer
                if self.use_per:
                    per_buffer.update_priorities(indices, td_errors)

                    # Anneal beta toward 1.0 over training
                    if per_buffer.beta_annealing:
                        # Estimate total steps from constructor params (if available)
                        if self.max_episodes is not None and self.max_steps_per_episode is not None:
                            total_steps = self.max_episodes * self.max_steps_per_episode
                            per_buffer.anneal_beta(total_steps, self.total_steps)
                        elif not self._per_beta_warning_logged:
                            # POP-006: Warn once if beta annealing is enabled but params are missing
                            _logger.warning(
                                "PER beta_annealing enabled but max_episodes/max_steps_per_episode not set. "
                                "Beta will remain at initial value, which may reduce training efficiency. "
                                "Set max_episodes and max_steps_per_episode in training.yaml to enable annealing."
                            )
                            self._per_beta_warning_logged = True

                # Periodically sync target network for stability
                self.training_step_counter += 1
                if self.training_step_counter % self.target_update_frequency == 0:
                    self.target_network.load_state_dict(self.q_network.state_dict())

                # Log network statistics to TensorBoard (POP-002 DRY helper)
                self._log_network_histograms()

        # 10. Update current state
        self.current_obs = next_obs

        # Track episode steps
        self.episode_step_counts += 1

        # 11. Handle episode resets (for adaptive intrinsic annealing)
        if dones.any():
            reset_indices = torch.where(dones)[0]
            for idx in reset_indices:
                survival_time = int(self.episode_step_counts[idx].item())
                if self.is_recurrent:
                    self._store_episode_and_reset(idx)
                self._finalize_episode(idx, survival_time)

        # 12. Construct BatchedAgentState
        # Note: rewards from environment already contain full DAC composition including intrinsic.
        # We do NOT add intrinsic_rewards again to avoid double-counting.
        # intrinsic_rewards is kept for logging/tracking purposes only.
        total_rewards = rewards  # Already contains: extrinsic + intrinsic + shaping from DAC

        # 10. Construct and return batched agent state
        # Add Q-values to info for recording (clone to CPU to avoid GPU memory issues)
        info["q_values"] = [q_values[i].cpu().tolist() for i in range(self.num_agents)]

        state = BatchedAgentState(
            observations=next_obs,
            actions=actions,
            rewards=total_rewards,
            dones=dones,
            epsilons=self.current_epsilons,
            intrinsic_rewards=intrinsic_rewards,
            survival_times=info["step_counts"],
            device=self.device,
            info=info,  # Pass environment info (includes successful_interactions, q_values)
        )

        return state

    def build_telemetry_snapshot(self, episode_index: int | None = None) -> dict:
        """
        Construct JSON-safe telemetry snapshot for all agents.

        Args:
            episode_index: Optional episode index to include in payload.

        Returns:
            Dict with schema version, episode index, and per-agent telemetry.
        """
        agents = [self.runtime_registry.get_snapshot_for_agent(i).to_dict() for i in range(self.num_agents)]
        payload = {
            "schema_version": "1.0.0",
            "episode_index": int(episode_index) if episode_index is not None else None,
            "agents": agents,
        }
        return payload

    def update_curriculum_tracker(self, rewards: torch.Tensor, dones: torch.Tensor) -> None:
        """Update curriculum tracker with episode rewards/dones."""
        if hasattr(self.curriculum, "tracker") and self.curriculum.tracker is not None:
            self.curriculum.tracker.update_step(rewards, dones)

    def get_training_metrics(self) -> dict:
        """Get recent training metrics for logging.

        Returns:
            Dictionary with TD error, loss, Q-values mean, and training step.
            Returns None values if no training has occurred yet.
        """
        return {
            "td_error": self.last_td_error,
            "loss": self.last_loss,
            "q_values_mean": self.last_q_values_mean,
            "training_step": self.last_training_step,
        }

    def get_checkpoint(self) -> PopulationCheckpoint:
        """
        Return Pydantic checkpoint.

        Returns:
            PopulationCheckpoint DTO
        """
        return PopulationCheckpoint(
            generation=0,
            num_agents=self.num_agents,
            agent_ids=self.agent_ids,
            curriculum_states={"global": self.curriculum.checkpoint_state()},
            exploration_states={"global": self.exploration.checkpoint_state()},
            pareto_frontier=[],
            metrics_summary={},
        )

    def get_checkpoint_state(self) -> dict:
        """
        Get complete checkpoint state for saving (P1.1 complete checkpointing).

        Returns comprehensive state dict including:
        - Version number
        - Q-network weights
        - Target network weights (if recurrent)
        - Optimizer state
        - Training counters
        - Replay buffer contents
        - Exploration strategy state
        - Curriculum state
        - Universe metadata (meter count, names) for validation (TASK-001)

        Returns:
            Complete checkpoint state dictionary
        """
        checkpoint = {
            "version": 2,  # Checkpoint format version
            "q_network": self.q_network.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "scheduler": self.scheduler.state_dict() if self.scheduler is not None else None,
            "total_steps": self.total_steps,
            "exploration_state": self.exploration.checkpoint_state(),
        }

        # Universe metadata for compatibility validation (TASK-001)
        # This allows detecting meter count mismatches when loading checkpoints
        bars_config = self.env.bars_config
        checkpoint["universe_metadata"] = {
            "meter_count": bars_config.meter_count,
            "meter_names": bars_config.meter_names,
            "version": bars_config.version,
            "obs_dim": self.env.observation_dim,
            "action_dim": self.action_dim,  # From environment action space (TASK-002B Phase 4.1)
        }

        # Target network (always initialized - POP-008 simplified)
        checkpoint["target_network"] = self.target_network.state_dict()
        checkpoint["training_step_counter"] = self.training_step_counter

        # Replay buffer
        # All buffer types implement serialize(), but mypy doesn't infer it for unions
        checkpoint["replay_buffer"] = self.replay_buffer.serialize()  # type: ignore[union-attr]

        return checkpoint

    def load_checkpoint_state(self, checkpoint: dict) -> None:
        """
        Restore population state from checkpoint (P1.1 complete checkpointing).

        Args:
            checkpoint: State dictionary from get_checkpoint_state()

        Raises:
            ValueError: If checkpoint universe metadata doesn't match current environment
        """
        # Validate universe compatibility
        if "universe_metadata" not in checkpoint:
            raise ValueError(
                "Checkpoint missing 'universe_metadata' field.\n"
                "This checkpoint format is no longer supported.\n"
                "Please retrain from scratch."
            )

        metadata = checkpoint["universe_metadata"]
        bars_config = self.env.bars_config
        current_meter_count = bars_config.meter_count

        # Validate meter count matches
        checkpoint_meter_count = metadata.get("meter_count")
        if checkpoint_meter_count != current_meter_count:
            raise ValueError(
                f"Checkpoint meter count mismatch: checkpoint has {checkpoint_meter_count} meters, "
                f"but current environment has {current_meter_count} meters. "
                f"Cannot load checkpoint trained on different universe configuration."
            )

        # Validate obs_dim matches.
        #
        # This was a WARNING that then proceeded to load_state_dict anyway. That was already
        # wrong — a differing obs_dim means the first Linear layer has a different in_features
        # and the load either raises with a shape message that names neither cause, or (for a
        # recurrent net, whose encoders are sized per BLOCK) succeeds against a layout the
        # weights were never trained on.
        #
        # PDR-0054 makes it sharper: meter count is no longer sufficient to characterise the
        # observation, because a meter's declared range_type changes its observed width. So
        # the count check above can pass while the layout differs entirely, and this is the
        # check that actually catches it.
        checkpoint_obs_dim = metadata.get("obs_dim")
        current_obs_dim = self.env.observation_dim
        if checkpoint_obs_dim != current_obs_dim:
            raise ValueError(
                f"Checkpoint obs_dim mismatch: checkpoint has {checkpoint_obs_dim}, "
                f"current env has {current_obs_dim}.\n"
                "  Cause: grid size, observability mode, or a meter's declared range_type "
                "differs from the universe this checkpoint was trained on.\n"
                "  Rule: the observation layout is part of a checkpoint's identity. Retrain, "
                "or load against the universe the checkpoint names."
            )

        # Restore Q-network
        self.q_network.load_state_dict(checkpoint["q_network"])

        # Restore optimizer
        self.optimizer.load_state_dict(checkpoint["optimizer"])

        # Restore scheduler state (if exists)
        if "scheduler" in checkpoint and checkpoint["scheduler"] is not None:
            if self.scheduler is not None:
                self.scheduler.load_state_dict(checkpoint["scheduler"])

        # Restore training counters
        self.total_steps = checkpoint.get("total_steps", 0)

        # Restore target network (if exists in checkpoint)
        # POP-008: Removed redundant self.target_network is not None check - always initialized
        if "target_network" in checkpoint and checkpoint["target_network"] is not None:
            self.target_network.load_state_dict(checkpoint["target_network"])
            self.training_step_counter = checkpoint.get("training_step_counter", 0)

        # Restore replay buffer
        if "replay_buffer" in checkpoint:
            # All buffer types implement load_from_serialized(), but mypy doesn't infer it for unions
            self.replay_buffer.load_from_serialized(checkpoint["replay_buffer"])  # type: ignore[union-attr]

        # Restore exploration state
        if "exploration_state" in checkpoint:
            self.exploration.load_state(checkpoint["exploration_state"])

    # ------------------------------------------------------------------ #
    # Cross-universe token-net load (token-obs unit 3 Task 9)
    # ------------------------------------------------------------------ #
    def load_token_network_cross_universe(self, source_q_network_state: dict[str, torch.Tensor]) -> TokenRosterReport:
        """Load a token net trained on ANOTHER universe into this population (spec §4).

        Per-type encoders and the aggregator transfer as feature extractors by
        ModuleDict type key (intersection load, both directions reported loudly;
        payload-schema mismatch refuses — `load_token_network_state_by_type`).
        Because the source universe's rewards, optimizer moments and novelty
        statistics do not describe THIS universe, a cross-universe load then:

        - re-copies the target network from the freshly-loaded online network;
        - resets the optimizer and LR schedule (fresh moments — stale Adam state
          against re-initialized or re-purposed weights is silent corruption);
        - resets RND state through its existing construction surface (a fresh
          fixed/predictor pair and reward statistics; the epsilon schedule carries
          over — it is exploration pacing, not novelty state).

        This is the seam the Task-10 cut wires into the checkpoint-consumer paths;
        nothing calls it in the live step path this task.
        """
        if not self.is_token_set:
            raise ValueError(
                "load_token_network_cross_universe requires architecture.type='token_set'; "
                f"this population runs {self.brain_config.architecture.type!r}."
            )
        report = load_token_network_state_by_type(self.q_network, source_q_network_state)

        # Re-copy target from the loaded online net (never load the source's target).
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()
        self.training_step_counter = 0

        # Fresh optimizer + schedule over the loaded parameters.
        self.optimizer, self.scheduler = OptimizerFactory.build(
            config=self.brain_config.optimizer,
            parameters=self.q_network.parameters(),
        )

        self._reset_rnd_state()
        return report

    def _reset_rnd_state(self) -> None:
        """Reset RND novelty state via its existing construction surface.

        `RNDExploration` exposes no in-place reset; a fresh instance built from the
        live instance's own constructor parameters IS the reset surface.
        """

        def _fresh(rnd: RNDExploration) -> RNDExploration:
            return RNDExploration(
                obs_dim=rnd.obs_dim,
                embed_dim=rnd.embed_dim,
                learning_rate=float(rnd.optimizer.param_groups[0]["lr"]),
                training_batch_size=rnd.training_batch_size,
                epsilon_start=rnd.epsilon,
                epsilon_min=rnd.epsilon_min,
                epsilon_decay=rnd.epsilon_decay,
                device=rnd.device,
            )

        exploration = self.exploration
        if isinstance(exploration, RNDExploration):
            fresh = _fresh(exploration)
            self.exploration = fresh
            self.env.set_exploration_module(fresh)
        elif isinstance(exploration, AdaptiveIntrinsicExploration):
            exploration.rnd = _fresh(exploration.rnd)
            # Cross-universe load: the wrapper's annealing/survival statistics are
            # source-universe data and must not steer the target universe (task-9
            # review I1) — reset them alongside the inner RND.
            exploration.current_intrinsic_weight = exploration.initial_intrinsic_weight
            exploration.survival_history.clear()
