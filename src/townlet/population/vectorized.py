"""
Vectorized population manager.

Coordinates multiple agents with shared curriculum and exploration strategies.
Manages Q-networks, replay buffers, and training loops.
"""

from __future__ import annotations

import copy
import hashlib
import logging
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from numbers import Real
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812

from townlet.agent.loss_factory import LossFactory
from townlet.agent.network_factory import NetworkFactory
from townlet.agent.networks import RecurrentTokenQNetwork
from townlet.agent.optimizer_factory import OptimizerFactory
from townlet.config.bac_options import ReplayOptions, resolve_bac_options
from townlet.config.brain_config import BrainConfig
from townlet.config.exploration_policy import ExplorationRuntime, IntrinsicStepHandoff
from townlet.curriculum.base import CurriculumManager
from townlet.exploration.action_selection import epsilon_greedy_action_selection_eligible
from townlet.population.base import PopulationManager
from townlet.population.runtime_registry import AgentRuntimeRegistry
from townlet.training.checkpoint_utils import TokenRosterReport
from townlet.training.clock_ledger import ClockLedger, PreparedPopulationRestore, PreparedVectorStep
from townlet.training.episode import CompletionReason, EpisodeCompletion, LaneOutcome, RunnerCompletionReason, freeze_lane_outcome
from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
from townlet.training.q_targets import legal_td_target
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.replay_contract import HistoricalLegalityUnavailable, ReplayBatch, ReplayRequest
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer
from townlet.training.state import BatchedAgentState, CurriculumDecision, PopulationCheckpoint, RewardTensor

if TYPE_CHECKING:
    from townlet.environment.vectorized_env import VectorizedHamletEnv

_logger = logging.getLogger(__name__)

POPULATION_CHECKPOINT_FORMAT_VERSION = 7
POPULATION_CHECKPOINT_KEYS = frozenset(
    {
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
        "clock_ledger",
        "vector_step_progress",
    }
)
POPULATION_UNIVERSE_METADATA_KEYS = frozenset(
    {
        "meter_count",
        "meter_names",
        "version",
        "obs_dim",
        "observation_schema_hash",
        "action_dim",
    }
)

EpisodeContainer = dict[str, list[torch.Tensor]]
ReplayStorage = ReplayBuffer | SequentialReplayBuffer | PrioritizedReplayBuffer


@dataclass(frozen=True)
class _VectorStep:
    vector_tick: int
    accepted: Any
    world_ids: tuple[str, ...]
    predecessor: torch.Tensor
    actions: torch.Tensor
    active_on_entry: torch.Tensor


@dataclass(frozen=True, slots=True)
class _PopulationReading:
    accepted: Any
    vector_tick: int
    observation: torch.Tensor
    env_dones: torch.Tensor
    env_counts: torch.Tensor
    completed: torch.Tensor
    counts: torch.Tensor
    action_masks: torch.Tensor | None


@dataclass(slots=True)
class _InitialDecision:
    accepted: Any
    reset: Any
    retired_world_ids: tuple[str, ...]
    retired: torch.Tensor
    participation: Any


@dataclass(slots=True)
class _InitialReset:
    record: Any
    retired_world_ids: tuple[str, ...]
    revision: int
    before: _PopulationReading
    intent: Any
    prepared: Any
    ready: Any
    decision: _InitialDecision | None
    candidate: _PopulationReading | None
    observation: torch.Tensor
    completed: torch.Tensor
    next_revision: int


@dataclass(frozen=True, slots=True)
class _SelectionFrame:
    accepted: Any
    reset: Any
    decision: _InitialDecision | None
    prior: _PopulationReading | None
    revision: int
    observation: torch.Tensor
    completed: torch.Tensor
    counts: torch.Tensor
    env_phase: str


@dataclass(frozen=True)
class _ReplaySetup:
    options: ReplayOptions
    min_transitions: int
    rng: np.random.Generator
    origin: str
    horizon: int
    horizon_origin: str
    tick: int
    preserve_global: bool

    @classmethod
    def create(
        cls,
        options: ReplayOptions,
        minimum: int,
        rng: np.random.Generator,
        origin: str,
        horizon: int,
        horizon_origin: str,
        tick: int,
        preserve_global: bool,
    ) -> _ReplaySetup:
        if not isinstance(options, ReplayOptions):
            raise ValueError("replay_options must be fully resolved ReplayOptions")
        owned = ReplayOptions.model_validate(options.model_dump())
        if any(value is None for value in owned.model_dump().values()):
            raise ValueError("All six replay options must be explicitly resolved")
        for label, value, lower in (
            ("min_transitions", minimum, 0),
            ("beta_vector_tick_horizon", horizon, 1),
            ("current_vector_tick", tick, 0),
        ):
            if type(value) is not int or value < lower:
                raise ValueError(f"{label} must be an exact integer >= {lower}")
        if not isinstance(rng, np.random.Generator) or origin not in {"authored", "bac-options-v1"}:
            raise ValueError("Replay requires an explicit NumPy Generator and authored/bac-options-v1 origin")
        if not isinstance(horizon_origin, str) or not horizon_origin.strip():
            raise ValueError("beta_horizon_origin must name the explicit horizon derivation")
        return cls(owned, minimum, copy.deepcopy(rng), origin, horizon, horizon_origin, tick, preserve_global)


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
        exploration: ExplorationRuntime,
        agent_ids: list[str],
        device: torch.device,
        brain_config: BrainConfig,
        obs_dim: int,
        train_frequency: int,
        batch_size: int,
        sequence_length: int,
        max_grad_norm: float,
        action_dim: int,
        tb_logger=None,
        max_episodes: int | None = None,
        max_steps_per_episode: int | None = None,
    ):
        self._initialize(
            env,
            curriculum,
            exploration,
            agent_ids,
            device,
            brain_config,
            obs_dim,
            train_frequency,
            batch_size,
            sequence_length,
            max_grad_norm,
            action_dim,
            tb_logger,
            max_episodes,
            max_steps_per_episode,
            None,
        )

    @classmethod
    def for_training(
        cls,
        *,
        env: VectorizedHamletEnv,
        curriculum: CurriculumManager,
        exploration: ExplorationRuntime,
        agent_ids: list[str],
        device: torch.device,
        brain_config: BrainConfig,
        obs_dim: int,
        train_frequency: int,
        batch_size: int,
        sequence_length: int,
        max_grad_norm: float,
        action_dim: int,
        tb_logger: Any,
        max_episodes: int | None,
        max_steps_per_episode: int | None,
        replay_options: ReplayOptions,
        min_transitions: int,
        replay_rng: np.random.Generator,
        replay_origin: str,
        beta_vector_tick_horizon: int,
        beta_horizon_origin: str,
        current_vector_tick: int,
    ) -> VectorizedPopulation:
        """Construct the selected learner with explicit owned replay policy and clock."""
        setup = _ReplaySetup.create(
            replay_options,
            min_transitions,
            replay_rng,
            replay_origin,
            beta_vector_tick_horizon,
            beta_horizon_origin,
            current_vector_tick,
            False,
        )
        population = cls.__new__(cls)
        population._initialize(
            env,
            curriculum,
            exploration,
            agent_ids,
            device,
            brain_config,
            obs_dim,
            train_frequency,
            batch_size,
            sequence_length,
            max_grad_norm,
            action_dim,
            tb_logger,
            max_episodes,
            max_steps_per_episode,
            setup,
        )
        return population

    def _initialize(
        self,
        env: VectorizedHamletEnv,
        curriculum: CurriculumManager,
        exploration: ExplorationRuntime,
        agent_ids: list[str],
        device: torch.device,
        brain_config: BrainConfig,
        obs_dim: int,
        train_frequency: int,
        batch_size: int,
        sequence_length: int,
        max_grad_norm: float,
        action_dim: int,
        tb_logger: Any,
        max_episodes: int | None,
        max_steps_per_episode: int | None,
        replay_setup: _ReplaySetup | None,
    ) -> None:
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
            tb_logger: Optional TensorBoard logger
            train_frequency: Train Q-network every N steps (required; typically from training.yaml)
            batch_size: Batch size for experience replay (required; typically from training.yaml replay_buffer.batch_size)
            sequence_length: Length of sequences for LSTM training (required for recurrent agents)
            max_grad_norm: Gradient clipping threshold (required; typically from training.yaml)
            max_episodes: Maximum training episodes (for PER beta annealing)
            max_steps_per_episode: Maximum steps per episode (for PER beta annealing)
        """
        # The compiled brain configuration is mandatory runtime input.
        if brain_config is None:
            raise ValueError(
                "brain_config is required. Provide brain.yaml configuration for all training runs. "
                "See docs/config-schemas/brain.md for examples."
            )
        if not isinstance(exploration, ExplorationRuntime):
            raise TypeError("Population requires the selected current ExplorationRuntime")

        # The compiled token artifact is the observation ABI (unit-3 cut). It is required
        # and set by VectorizedHamletEnv from the compiled universe; no alternate source exists.
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
        self.env.set_exploration_runtime(exploration=exploration, claim_vector_step=self.claim_vector_step)

        # Training metrics (for TensorBoard logging)
        self.last_td_error = 0.0
        self.last_loss = 0.0
        self.last_q_values_mean = 0.0
        self.last_training_step = 0
        self.last_rnd_loss = 0.0  # RND predictor loss (for monitoring intrinsic exploration)
        self._per_beta_warning_logged = False  # POP-006: Track if we've warned about missing annealing params

        # Q-network (shared across all agents for now)
        # Store params needed for network building helper
        self._obs_dim = obs_dim

        # Build network using DRY helper (POP-001)
        self.q_network: nn.Module = self._build_network(brain_config, obs_dim, action_dim, env).to(device)

        # Set is_recurrent flag from brain_config
        self.is_recurrent = brain_config.architecture.type == "recurrent"

        # Set is_dueling flag from brain_config
        self.is_dueling = brain_config.architecture.type == "dueling"

        self.is_token_native = brain_config.architecture.type in {"token_set", "recurrent"}

        # Target network (stabilises training for both feed-forward and recurrent agents)
        # Build using DRY helper (POP-001)
        self.target_network: nn.Module = self._build_network(brain_config, obs_dim, action_dim, env).to(device)

        # Initialize common target network state
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()  # Target network always in eval mode
        self.target_update_frequency = target_update_frequency
        self.training_step_counter = 0

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
        self.replay_buffer: ReplayBuffer | SequentialReplayBuffer | PrioritizedReplayBuffer
        self.current_episodes: list[EpisodeContainer] = []

        # Determine if PER is enabled from brain_config
        self.use_per = brain_config.replay.prioritized

        # Replay buffer capacity from brain_config
        replay_capacity = brain_config.replay.capacity

        if self.is_recurrent:
            self.current_episodes = [self._new_episode_container() for _ in range(self.num_agents)]
        if replay_setup is not None:
            self.replay_buffer = self._new_replay(replay_setup)
        elif self.is_recurrent:
            # Construction/inspection has no learner-only seed/horizon requirement.
            self.replay_buffer = SequentialReplayBuffer(capacity=replay_capacity, device=device)
        else:
            # Feedforward networks select the configured standard or prioritized replay.
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
        if replay_setup is None:
            self.total_steps = 0
        else:
            self.total_steps = replay_setup.tick
        self.train_frequency = train_frequency
        self.sequence_length = sequence_length
        self.max_grad_norm = max_grad_norm
        self.batch_size = batch_size

        # Lane survival and completion state are cleared only by an explicit batch reset.
        self.episode_step_counts = torch.zeros(self.num_agents, dtype=torch.long, device=device)
        self.episode_completed = torch.zeros(self.num_agents, dtype=torch.bool, device=self.device)
        self.episode_completions: list[EpisodeCompletion | None] = [None for _ in range(self.num_agents)]
        self._clock_ledger = ClockLedger(vector_ticks=self.total_steps)
        self._clock_ledger_restore_unavailable = self.total_steps != 0
        self._accepted: Any = None
        self._activation: Any = None
        self._reset_stage: str | None = None
        self._reset_record: Any = None
        self._initial_reset: _InitialReset | None = None
        self._initial_decision: _InitialDecision | None = None
        self._prior_reading: _PopulationReading | None = None
        self._selection_frame: _SelectionFrame | None = None
        self._step_inspection: object | None = None
        self._population_issuer: Any = None
        self._empty_evidence: Any = None
        self._vector_steps: dict[PreparedVectorStep, _VectorStep] = {}
        self._vector_stage: str | None = None
        self._vector_step_progress: dict[str, Any] | None = None
        self._step_active = False
        self._failed_step = False
        self._returned_step: dict[str, Any] | None = None
        self._service_receipts: tuple[Any, ...] = ()
        self._checkpoint_revision = 0
        self._population_restores: dict[PreparedPopulationRestore, Any] = {}
        self._preparing_checkpoint: Any = None
        self._pending_batch_commit: Any = None
        self._batch_commit_active = False
        self._batch_commit_progress: dict[str, Any] | None = None
        self._episode_participants: set[int] = set()
        self._batch_participants: dict[int, tuple[int, ...]] = {}
        self._parent_cadence: dict[str, Any] = {"schema": "parent-global-epsilon-cadence-v1", "last_committed": None}
        self._next_world_binding: tuple[tuple[str, ...], tuple[int, ...]] | None = None
        self._owned_episode: tuple[int, int, tuple[str, ...], tuple[int, ...]] | None = None
        self._owned_reset_pending = False
        self._begun_batch_ids: set[int] = set()
        self._completed_outcomes: tuple[LaneOutcome, ...] = ()
        self._published_outcome_fingerprints: dict[tuple[int, int], str] = {}
        self._published_events: dict[tuple[int, int], LaneOutcome] = {}
        self._committed_outcomes: dict[tuple[int, int], str] = {}
        self._committed_batches: set[int] = set()
        self._episode_reward_totals = torch.zeros((self.num_agents, 4), dtype=torch.float64)
        self._episode_entropies = torch.zeros(self.num_agents, dtype=torch.float64)
        self._episode_entropy_present = torch.zeros(self.num_agents, dtype=torch.bool)

        # Current state
        self.current_obs = torch.zeros((self.num_agents, obs_dim), dtype=torch.float32, device=device)
        self.current_epsilons = torch.zeros(self.num_agents, dtype=torch.float32, device=device)
        self.current_curriculum_decisions: list[CurriculumDecision] = []  # Store curriculum decisions
        self.current_depletion_multiplier: float = 1.0  # Track curriculum difficulty

        # WS-1(b): rollout memory is population-owned; the network holds no state.
        self.rollout_hidden: tuple[torch.Tensor, torch.Tensor] | None = None
        if self.is_recurrent:
            recurrent_network = cast(RecurrentTokenQNetwork, self.q_network)
            self.rollout_hidden = recurrent_network.initial_hidden(self.num_agents, self.device)
        # Q-values recorded by the action selectors (read by the live-inference display).
        self.last_selected_q_values: torch.Tensor | None = None
        self._replay_setup = replay_setup
        self.replay_option_provenance: tuple[Any, ...] | None = None
        self._last_readiness: tuple[str, int, int] | None = None
        self._replay_was_loaded = False
        self._constructor_replay: ReplayStorage | None
        self._constructor_replay_state: dict[str, Any] | None
        self._bound_replay: ReplayStorage | None
        if replay_setup is None:
            self._constructor_replay = self.replay_buffer
            self._constructor_replay_state = copy.deepcopy(self.replay_buffer.serialize())
            self._bound_replay = None
        else:
            self._constructor_replay = None
            self._constructor_replay_state = None
            self._bound_replay = self.replay_buffer
        self._last_beta_tick = self.total_steps

    def _new_replay(self, setup: _ReplaySetup) -> ReplayStorage:
        """Build offside; callers install only after all required validation succeeds."""
        replay = self.brain_config.replay
        if self.use_per:
            assert replay.priority_alpha is not None
            assert replay.priority_beta is not None
            assert replay.priority_beta_annealing is not None
        if self.is_recurrent:
            if self.use_per:
                return SequentialReplayBuffer.for_prioritized_replay(
                    replay.capacity,
                    self.device,
                    options=setup.options,
                    action_dim=self.action_dim,
                    legality_mode="captured",
                    alpha=cast(float, replay.priority_alpha),
                    beta=cast(float, replay.priority_beta),
                    beta_annealing=cast(bool, replay.priority_beta_annealing),
                    beta_vector_tick_horizon=setup.horizon,
                    current_vector_tick=setup.tick,
                    rng=setup.rng,
                    origin=setup.origin,
                )
            return SequentialReplayBuffer.for_replay(
                replay.capacity, self.device, options=setup.options, action_dim=self.action_dim, legality_mode="captured"
            )
        if self.use_per:
            buffer = PrioritizedReplayBuffer(
                replay.capacity,
                cast(float, replay.priority_alpha),
                cast(float, replay.priority_beta),
                cast(bool, replay.priority_beta_annealing),
                self.device,
            )
            if not setup.preserve_global:
                buffer.configure_sampling(sampling_mode=cast(str, setup.options.sampling_mode), rng=setup.rng, origin=setup.origin)
            return buffer
        return ReplayBuffer(replay.capacity, self.device)

    def _compiled_replay_setup(self, tick: int) -> _ReplaySetup:
        training = self.env.level.training
        resolved = resolve_bac_options(training.bac_options, training=training)
        options = resolved.options.replay
        assert options is not None
        if self.max_episodes is not None:
            episodes = self.max_episodes
            episode_origin = "population.max_episodes"
        else:
            episodes = training.training_loop.max_episodes
            episode_origin = "training.training_loop.max_episodes"
        if self.max_steps_per_episode is not None:
            steps = self.max_steps_per_episode
            step_origin = "population.max_steps_per_episode"
        else:
            steps = training.training_loop.max_steps_per_episode
            step_origin = "training.training_loop.max_steps_per_episode"
        return _ReplaySetup.create(
            options,
            training.replay_buffer.min_size,
            np.random.Generator(np.random.PCG64(training.seed)),
            "authored",
            episodes * steps,
            f"{episode_origin}({episodes})*{step_origin}({steps}); upper-bound vector ticks",
            tick,
            not self.is_recurrent and options.sampling_mode == "successive_without_replacement",
        )

    @classmethod
    def _same_replay_state(cls, left: object, right: object) -> bool:
        if isinstance(left, torch.Tensor):
            return isinstance(right, torch.Tensor) and left.dtype == right.dtype and left.shape == right.shape and torch.equal(left, right)
        if isinstance(left, np.ndarray):
            return isinstance(right, np.ndarray) and np.array_equal(left, right)
        if isinstance(left, Mapping):
            return (
                isinstance(right, Mapping)
                and left.keys() == right.keys()
                and all(cls._same_replay_state(v, right[k]) for k, v in left.items())
            )
        if isinstance(left, (tuple, list)):
            return (
                isinstance(right, (tuple, list))
                and type(left) is type(right)
                and len(left) == len(right)
                and all(cls._same_replay_state(a, b) for a, b in zip(left, right, strict=True))
            )
        return bool(left == right)

    def _validate_replay_binding(self, buffer: ReplayStorage, setup: _ReplaySetup, state: Mapping[str, Any]) -> None:
        if state["capacity"] != self.brain_config.replay.capacity:
            raise ValueError("Installed replay capacity disagrees with the passed brain")
        if self.is_recurrent:
            if not isinstance(buffer, SequentialReplayBuffer) or state.get("format_version") not in (6, 7):
                raise ValueError("Learning requires qualified captured sequential replay")
            if (
                state["replay_options"] != setup.options.model_dump()
                or state["action_dim"] != self.action_dim
                or state["legality_mode"] != "captured"
            ):
                raise ValueError("Installed sequential replay policy/action geometry disagrees with the learner")
            priority = state.get("priority_state")
            if self.use_per != (priority is not None):
                raise ValueError("Installed sequential replay prioritization disagrees with the passed brain")
            if priority is not None:
                if priority["current_vector_tick"] != self.total_steps or priority["beta_vector_tick_horizon"] != setup.horizon:
                    raise ValueError("Installed sequential replay clock/horizon disagrees with the restored population")
                self._validate_per_configuration(priority)
        else:
            if self.use_per != isinstance(buffer, PrioritizedReplayBuffer) or isinstance(buffer, SequentialReplayBuffer):
                raise ValueError("Installed flat replay kind disagrees with the passed brain")
            if buffer.retained_transitions and state.get("action_dim") is None:
                raise HistoricalLegalityUnavailable("Unknown successor legality cannot enter compiled-world learning")
            if self.use_per:
                if state["sampling_mode"] != setup.options.sampling_mode:
                    raise ValueError("Installed flat replay sampler mode disagrees with the learner")
                self._validate_per_configuration(state)

    def _validate_per_configuration(self, state: Mapping[str, Any]) -> None:
        replay = self.brain_config.replay
        if (state["alpha"], state["beta_initial"], state["beta_annealing"]) != (
            replay.priority_alpha,
            replay.priority_beta,
            replay.priority_beta_annealing,
        ):
            raise ValueError("Installed replay PER configuration disagrees with the passed brain")

    def _bind_training(self) -> None:
        """Adopt installed state; only a genuinely pristine constructor buffer is fresh."""
        if self.total_steps < self._last_beta_tick:
            raise ValueError("Population vector tick cannot rewind during ordinary learning")
        if self._bound_replay is self.replay_buffer:
            return
        compiled = self._replay_setup is None
        if self._replay_setup is not None:
            setup = replace(self._replay_setup, tick=self.total_steps)
        else:
            setup = self._compiled_replay_setup(self.total_steps)
        buffer = self.replay_buffer
        state = buffer.serialize()
        pristine = (
            buffer is self._constructor_replay
            and not self._replay_was_loaded
            and self.total_steps == 0
            and self.training_step_counter == 0
            and self._same_replay_state(state, self._constructor_replay_state)
        )
        adapt = self.is_recurrent and (state.get("format_version") not in (6, 7) or (self.use_per and state.get("format_version") == 6))
        if (pristine and self.is_recurrent) or adapt:
            candidate = self._new_replay(setup)
            sequential = cast(SequentialReplayBuffer, candidate)
            if not pristine:
                if "inspection_kind" in state:
                    transport = state["legacy_transport"]
                    if transport["num_transitions"]:
                        sequential.load_prepared(sequential.prepare_serialized(transport, expected_obs_dim=self._obs_dim))
                    sequential.load_prepared(sequential.prepare_archived_import(buffer.historical_archives, expected_obs_dim=self._obs_dim))
                else:
                    prepared = sequential.prepare_serialized(state, expected_obs_dim=self._obs_dim)
                    sequential.load_prepared(prepared)
            buffer, state = candidate, candidate.serialize()
        elif pristine and self.use_per and not setup.preserve_global:
            candidate = self._new_replay(setup)
            buffer, state = candidate, candidate.serialize()
        self._validate_replay_binding(buffer, setup, state)
        self.replay_buffer = buffer
        self._replay_setup = setup
        self._bound_replay = buffer
        self._last_beta_tick = self.total_steps
        self._constructor_replay = None
        self._constructor_replay_state = None
        if compiled:
            resolved = resolve_bac_options(self.env.level.training.bac_options, training=self.env.level.training)
            self.replay_option_provenance = tuple(p.model_copy(deep=True) for p in resolved.provenance if p.field.startswith("replay."))

    def _pace_replay(self) -> None:
        if self.total_steps < self._last_beta_tick:
            raise ValueError("Population vector tick cannot rewind")
        assert self._replay_setup is not None
        if self.use_per:
            if self.is_recurrent:
                cast(SequentialReplayBuffer, self.replay_buffer).set_vector_tick(self.total_steps)
            else:
                cast(PrioritizedReplayBuffer, self.replay_buffer).anneal_beta(self._replay_setup.horizon, self.total_steps)
        self._last_beta_tick = self.total_steps

    def _replay_request(self) -> ReplayRequest:
        assert self._replay_setup is not None
        setup = self._replay_setup
        return ReplayRequest(
            self.batch_size,
            self.sequence_length if self.is_recurrent else 1,
            setup.min_transitions,
            cast(str, setup.options.sampling_mode) if self.is_recurrent or self.use_per else "uniform_without_replacement",
            cast(str, setup.options.sequence_mode) if self.is_recurrent else "feedforward",
            cast(str, setup.options.sequence_objective) if self.is_recurrent else "transition",
        )

    def _loss_values(self, predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        if self.loss_type == "huber":
            return F.huber_loss(predictions, targets, reduction="none", delta=self.loss_delta)
        if self.loss_type == "smooth_l1":
            return F.smooth_l1_loss(predictions, targets, reduction="none")
        if self.loss_type == "mse":
            return F.mse_loss(predictions, targets, reduction="none")
        raise ValueError(f"Unsupported loss type: {self.loss_type}")

    def _recurrent_predictions(self, batch: ReplayBatch) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Evaluate only real prefixes; each bootstrap branches to its exact stored successor."""
        online = cast(RecurrentTokenQNetwork, self.q_network)
        target = cast(RecurrentTokenQNetwork, self.target_network)
        predictions = torch.zeros_like(batch.rewards)
        targets = torch.zeros_like(batch.rewards)
        real = torch.arange(batch.observations.shape[1], device=self.device)[None, :] < batch.lengths[:, None]
        for length in batch.lengths.unique().tolist():
            rows = torch.nonzero(batch.lengths == length, as_tuple=False).flatten()
            online_hidden = online.initial_hidden(len(rows), self.device)
            target_hidden = target.initial_hidden(len(rows), self.device)
            current_predictions, current_targets = [], []
            for t in range(length):
                observation = batch.observations[rows, t : t + 1]
                values, online_hidden = online(observation, online_hidden)
                current_predictions.append(values[:, 0].gather(1, batch.actions[rows, t, None]).squeeze(-1))
                with torch.no_grad():
                    _, target_hidden = target(observation, target_hidden)
                    successor = batch.next_observations[rows, t : t + 1]
                    target_next, _ = target(successor, target_hidden)
                    online_next: torch.Tensor | None = None
                    if self.use_double_dqn:
                        branch_hidden = online_hidden[0].detach(), online_hidden[1].detach()
                        online_branch, _ = online(successor, branch_hidden)
                        online_next = online_branch[:, 0]
                    current_targets.append(
                        legal_td_target(
                            batch.rewards[rows, t],
                            batch.dones[rows, t],
                            online_next,
                            target_next[:, 0],
                            batch.next_action_masks[rows, t],
                            gamma=self.gamma,
                            double_dqn=self.use_double_dqn,
                        )
                    )
            predictions[rows, :length] = torch.stack(current_predictions, dim=1)
            targets[rows, :length] = torch.stack(current_targets, dim=1)
        return predictions, targets, real

    def _learn(self) -> None:
        request = self._replay_request()
        readiness = self.replay_buffer.readiness(request)
        signature = readiness.reason, readiness.retained_transitions, readiness.sampleable_units
        if not readiness.ready:
            if signature != self._last_readiness:
                _logger.info("Replay not ready: %s (retained=%d, sampleable=%d)", *signature)
            self._last_readiness = signature
            return
        self._last_readiness = signature
        batch = self.replay_buffer.sample_batch(request, lineage=None)
        self.q_network.train()
        self.target_network.eval()
        if self.is_recurrent:
            predictions, targets, real = self._recurrent_predictions(batch)
            selected = batch.loss_mask
            losses = self._loss_values(predictions[selected], targets[selected])
            unit_losses = torch.zeros(len(batch.lengths), dtype=torch.float64, device=self.device)
            unit_losses.scatter_add_(0, torch.nonzero(selected, as_tuple=True)[0], losses.double())
            unit_losses = unit_losses / selected.sum(dim=1)
        else:
            predictions = self.q_network(batch.observations).gather(1, batch.actions[:, None]).squeeze(-1)
            with torch.no_grad():
                if self.use_double_dqn:
                    online_next = self.q_network(batch.next_observations)
                else:
                    online_next = None
                target_next = self.target_network(batch.next_observations)
                targets = legal_td_target(
                    batch.rewards,
                    batch.dones,
                    online_next,
                    target_next,
                    batch.next_action_masks,
                    gamma=self.gamma,
                    double_dqn=self.use_double_dqn,
                )
            real = torch.ones_like(batch.dones, dtype=torch.bool)
            unit_losses = self._loss_values(predictions, targets)
        loss = (unit_losses * batch.weights.detach()).mean()
        # Promote each operand before subtraction, then select/reduce unweighted real rows.
        errors = torch.zeros_like(batch.rewards, dtype=torch.float64)
        errors[real] = predictions[real].detach().double() - targets[real].double()
        td_mean = errors[real].abs().mean().item()
        q_mean = predictions[real].detach().double().mean().item()
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=self.max_grad_norm)
        self.optimizer.step()
        self.training_step_counter += 1
        self._clock_ledger = self._clock_ledger.advance(optimizer_updates=1)
        if self.scheduler is not None:
            self.scheduler.step()
        if self.training_step_counter % self.target_update_frequency == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
        self.last_td_error, self.last_loss, self.last_q_values_mean = td_mean, loss.item(), q_mean
        self.last_training_step = self.total_steps
        if self.use_per:
            if self.is_recurrent:
                cast(SequentialReplayBuffer, self.replay_buffer).update_priorities(batch.unit_ids, errors, loss_mask=batch.loss_mask)
            else:
                handles = batch.unit_ids.detach().cpu().numpy().astype(np.int64, copy=True)
                cast(PrioritizedReplayBuffer, self.replay_buffer).update_unit_priorities(handles, errors)
        self._log_network_histograms()

    def _require_operation_idle(self) -> None:
        if (
            self._step_active
            or self._selection_frame is not None
            or self._initial_reset is not None
            or self._step_inspection is not None
            or self._preparing_checkpoint is not None
            or self._batch_commit_active
        ):
            raise RuntimeError("Reentrant population operation")

    def _quarantine_participation(self, error: Exception) -> None:
        self._failed_step, self._activation = True, None
        if self._accepted is not None:
            try:
                self.env.abandon_episode(accepted=self._accepted, reason="runtime_failure")
            except Exception as cleanup:
                error.add_note(f"Population integrity quarantine: {cleanup!r}")

    @staticmethod
    def _same_reading(value: Any, owned: torch.Tensor) -> bool:
        return (
            isinstance(value, torch.Tensor)
            and value.layout == torch.strided
            and value.dtype == owned.dtype
            and value.device == owned.device
            and value.shape == owned.shape
            and torch.equal(value, owned)
        )

    def _copy_reading(self, *, accepted: Any, observation: torch.Tensor, action_masks: torch.Tensor | None) -> _PopulationReading:
        return _PopulationReading(
            accepted,
            self.total_steps,
            observation.detach().clone(),
            self.env.dones.detach().clone(),
            self.env.step_counts.detach().clone(),
            self.episode_completed.detach().clone(),
            self.episode_step_counts.detach().clone(),
            None if action_masks is None else action_masks.detach().clone(),
        )

    def _parent_reading_matches(self, reading: _PopulationReading) -> bool:
        return all(
            self._same_reading(value, owned)
            for value, owned in (
                (self.current_obs, reading.observation),
                (self.episode_completed, reading.completed),
                (self.episode_step_counts, reading.counts),
            )
        )

    def _check_owned_state(self) -> _PopulationReading:
        decision, prior = self._initial_decision, self._prior_reading
        if (
            decision is None
            or prior is None
            or self._accepted is not decision.accepted
            or self._reset_record is not decision.reset
            or prior.accepted is not decision.accepted
            or prior.vector_tick != self.total_steps
            or prior.action_masks is None
        ):
            missing = RuntimeError("Owned episode lacks its genuine sealed population reading")
            self._quarantine_participation(missing)
            raise missing
        retired_rows = torch.nonzero(decision.retired, as_tuple=False).flatten().tolist()
        healthy = (
            self._parent_reading_matches(prior)
            and self._same_reading(self.env.dones, prior.env_dones)
            and self._same_reading(self.env.step_counts, prior.env_counts)
            and all(
                bool(self.episode_completed[row])
                and int(self.episode_step_counts[row]) == 0
                and self.episode_completions[row] is None
                and row not in self._episode_participants
                and not bool(self._episode_entropy_present[row])
                and not bool(self._episode_reward_totals[row].any())
                and (not self.is_recurrent or not self.current_episodes[row]["observations"])
                for row in retired_rows
            )
        )
        if not healthy:
            error = ValueError("Population state changed outside its owned transition boundary")
            self._quarantine_participation(error)
            raise error
        return prior

    def _validate_owned_training(self) -> _PopulationReading:
        prior = self._check_owned_state()
        assert self._initial_decision is not None
        try:
            self.env.validate_initial_participation(
                accepted=prior.accepted, participation=self._initial_decision.participation, predecessor=prior.observation
            )
        except Exception:
            if self.env.world_phase == "quarantined":
                self._failed_step, self._activation = True, None
            raise
        self._check_owned_state()
        return prior

    def _validate_owned_reading(self) -> _PopulationReading:
        prior = self._check_owned_state()
        assert self._initial_decision is not None
        try:
            self.env.validate_initial_participation_reading(
                accepted=prior.accepted, participation=self._initial_decision.participation, predecessor=prior.observation
            )
        except Exception:
            if self.env.world_phase == "quarantined":
                self._failed_step, self._activation = True, None
            raise
        self._check_owned_state()
        return prior

    def _begin_selection(self) -> _SelectionFrame:
        self._require_operation_idle()
        if self._failed_step or self._pending_batch_commit is not None or self._vector_steps or self._owned_reset_pending:
            raise RuntimeError("Pending or failed population work cannot select actions")
        if self._accepted is not None or self._initial_decision is not None or self._reset_record is not None:
            self._check_owned_state()
        frame = _SelectionFrame(
            self._accepted,
            self._reset_record,
            self._initial_decision,
            self._prior_reading,
            self._checkpoint_revision,
            self.current_obs.detach().clone(),
            self.episode_completed.detach().clone(),
            self.episode_step_counts.detach().clone(),
            self.env.world_phase,
        )
        self._selection_frame = frame
        try:
            self._revalidate_selection(frame)
            frame = replace(frame, revision=frame.revision + 1)
            self._checkpoint_revision = frame.revision
            self._selection_frame = frame
            return frame
        except Exception:
            if self._selection_frame is frame:
                self._selection_frame = None
            raise

    def _selection_changed(self, frame: _SelectionFrame) -> bool:
        return (
            self._selection_frame is not frame
            or self._checkpoint_revision != frame.revision
            or self._accepted is not frame.accepted
            or self._reset_record is not frame.reset
            or self._initial_decision is not frame.decision
            or self._prior_reading is not frame.prior
            or self._owned_reset_pending
            or self._failed_step
            or self.env.world_phase != frame.env_phase
            or not self._same_reading(self.current_obs, frame.observation)
            or not self._same_reading(self.episode_completed, frame.completed)
            or not self._same_reading(self.episode_step_counts, frame.counts)
        )

    def _revalidate_selection(self, frame: _SelectionFrame) -> None:
        if not self._selection_changed(frame) and frame.decision is not None:
            self._validate_owned_reading()
        if self._selection_changed(frame):
            error = ValueError("Selection callback changed retained population custody")
            self._quarantine_participation(error)
            raise error

    def _check_selection_exception(self, frame: _SelectionFrame, error: Exception) -> None:
        try:
            self._revalidate_selection(frame)
        except Exception as invalid:
            error.add_note(f"Selection failure could not certify retained owner state: {invalid!r}")
            if not self._failed_step:
                self._quarantine_participation(error)

    def _prepare_initial_participation(self, work: _InitialReset) -> None:
        if self._initial_reset is not work or self._checkpoint_revision != work.revision:
            raise RuntimeError("Stale private reset preparation")
        work.intent = self._population_issuer.issue(
            kind="initial_participation_intent",
            payload=dict(
                accepted=work.record.accepted,
                world_ids=work.record.accepted.world_ids,
                retired_world_ids=work.retired_world_ids,
                population_revision=work.revision,
            ),
        )
        work.prepared = self.env.prepare_initial_participation(accepted=work.record.accepted, intent=work.intent)
        observation, masks = work.prepared.observation, work.prepared.action_masks
        if (
            not self._same_reading(observation, work.before.observation)
            or not self._parent_reading_matches(work.before)
            or masks.layout != torch.strided
            or masks.shape != (self.num_agents, self.action_dim)
            or masks.dtype != torch.bool
            or masks.device != self.device
            or work.prepared.retired_world_ids != work.retired_world_ids
        ):
            raise ValueError("Prepared initial participation changed reset readings or selected geometry")
        retired = torch.tensor(
            [world in work.retired_world_ids for world in work.record.accepted.world_ids], dtype=torch.bool, device=self.device
        )
        if bool(masks[retired].any()) or bool((~retired & ~masks.any(dim=1)).any()):
            raise ValueError("Prepared masks disagree with the initial participation decision")
        work.observation, work.completed = observation, retired.clone()
        work.decision = _InitialDecision(work.record.accepted, work.record, work.retired_world_ids, retired.clone(), None)
        work.candidate = _PopulationReading(
            work.record.accepted,
            self.total_steps,
            observation.detach().clone(),
            retired.clone(),
            work.before.env_counts.clone(),
            retired.clone(),
            work.before.counts.clone(),
            masks.detach().clone(),
        )
        work.ready = self._population_issuer.issue(
            kind="initial_participation_ready",
            payload=dict(accepted=work.record.accepted, intent=work.intent, prepared=work.prepared, population_revision=work.revision),
        )

    def _publish_initial_participation(self, work: _InitialReset) -> None:
        decision, candidate = work.decision, work.candidate
        if (
            self._initial_reset is not work
            or decision is None
            or candidate is None
            or self._checkpoint_revision != work.revision
            or not self._parent_reading_matches(work.before)
            or not self._same_reading(self.env.dones, work.before.env_dones)
            or not self._same_reading(self.env.step_counts, work.before.env_counts)
            or self._vector_steps
            or self._completed_outcomes
            or self._episode_participants
            or any(value is not None for value in self.episode_completions)
            or bool(self._episode_reward_totals.any())
            or bool(self._episode_entropy_present.any())
            or any(episode["observations"] for episode in self.current_episodes)
        ):
            raise ValueError("Population reset changed before initial participation publication")
        result = self.env.commit_initial_participation(prepared=work.prepared, population_ready=work.ready)
        # Assignment-only paired suffix: no clone, callback, receipt, validation or allocation.
        decision.participation = result
        self.current_obs = work.observation
        self.episode_completed = work.completed
        self._initial_decision = decision
        self._prior_reading = candidate
        self._checkpoint_revision = work.next_revision
        self._initial_reset = None
        self._reset_stage = "finalizing"

    def reset(self, *, reservation: Any, retired_world_ids: tuple[str, ...]) -> tuple[Any, Any]:
        """Reset all environments and state."""
        from townlet.environment.vectorized_env import WorldReceiptIssuer

        self._require_operation_idle()
        if self._step_active or self._failed_step or self._preparing_checkpoint is not None or self._pending_batch_commit is not None:
            raise RuntimeError("A running or failed population attempt requires healthy boundary recovery")
        if self._vector_steps:
            raise RuntimeError("Resolve the pending vector step before reset")
        pending = (self.episode_step_counts > 0) & ~self.episode_completed
        if bool(pending.any()):
            raise RuntimeError("Complete pending lanes with an explicit stop reason before reset")
        binding = self._owned_episode
        if binding is None or (reservation.batch_episode, reservation.world_ids, reservation.world_episode_seqs) != (
            binding[0],
            binding[2],
            binding[3],
        ):
            raise ValueError("Reset reservation must match the explicitly begun population episode")
        if (
            type(retired_world_ids) is not tuple
            or any(type(world) is not str or not world for world in retired_world_ids)
            or len(set(retired_world_ids)) != len(retired_world_ids)
            or tuple(world for world in binding[2] if world in retired_world_ids) != retired_world_ids
        ):
            raise ValueError("Retired world IDs must be an exact ordered unique subset of the bound roster")
        if (
            self._reset_record is not None
            and self._reset_record.accepted is self._accepted
            and (self._accepted.batch_episode, self._accepted.world_ids, self._accepted.world_episode_seqs)
            == (binding[0], binding[2], binding[3])
        ):
            self._validate_owned_reading()
            if self._initial_decision is None or retired_world_ids != self._initial_decision.retired_world_ids:
                raise ValueError("An accepted reset cannot change its sealed initial decision")
        previous_stage = self._reset_stage
        self._reset_stage, self._step_active = "preparing", True
        record = None
        try:
            record = self.env.reset(reservation=reservation)
            self._reset_record = record
            if record.accepted is self._accepted:
                if previous_stage != "completed" or self._activation is None:
                    raise RuntimeError("Accepted reset has no completed population preparation")
                self._reset_stage = "completed"
                return record, self._activation
            observation = record.observation
            if (
                observation.layout != torch.strided
                or observation.shape != self.current_obs.shape
                or observation.dtype != torch.float32
                or observation.device != self.device
                or not bool(torch.isfinite(observation).all())
            ):
                raise ValueError("Reset observation disagrees with the selected population geometry")
            if self._population_issuer is None:
                self._population_issuer = WorldReceiptIssuer(owner=self)
            self.current_obs = observation.detach().clone()
            self._empty_evidence, self._vector_steps, self._vector_stage = None, {}, None
            self._episode_participants = set()
            self._checkpoint_revision += 1
            self.episode_step_counts.zero_()
            self.episode_completed.zero_()
            self.episode_completions = [None for _ in range(self.num_agents)]
            self._owned_reset_pending = False
            self._completed_outcomes = ()
            self._episode_reward_totals.zero_()
            self._episode_entropies.zero_()
            self._episode_entropy_present.zero_()
            if self.is_recurrent:
                recurrent_network = cast(RecurrentTokenQNetwork, self.q_network)
                self.rollout_hidden = recurrent_network.initial_hidden(self.num_agents, self.device)
                self.current_episodes = [self._new_episode_container() for _ in range(self.num_agents)]
            for agent_idx in range(self.num_agents):
                self.runtime_registry.record_survival_time(agent_idx=agent_idx, steps=0)
            self._publish_exploration_metrics()
            self._sync_curriculum_metrics()
            before = self._copy_reading(accepted=record.accepted, observation=self.current_obs, action_masks=None)
            work = _InitialReset(
                record,
                retired_world_ids,
                self._checkpoint_revision,
                before,
                None,
                None,
                None,
                None,
                None,
                self.current_obs,
                self.episode_completed,
                self._checkpoint_revision + 1,
            )
            self._initial_reset = work
            self._prepare_initial_participation(work)
            self._publish_initial_participation(work)
            activation = self._population_issuer.issue(kind="activation", payload={"accepted": record.accepted})
            if (
                work.candidate is None
                or self._prior_reading is not work.candidate
                or self._initial_decision is not work.decision
                or self._reset_record is not record
                or self._checkpoint_revision != work.next_revision
                or self._failed_step
                or self._initial_reset is not None
                or self._reset_stage != "finalizing"
                or not self._step_active
                or not self._parent_reading_matches(work.candidate)
            ):
                raise ValueError("Activation finalization changed the paired population publication")
            assert work.decision is not None
            self.env.validate_initial_participation_reading(
                accepted=record.accepted, participation=work.decision.participation, predecessor=work.candidate.observation
            )
            if (
                work.candidate is None
                or work.decision is None
                or self._prior_reading is not work.candidate
                or self._initial_decision is not work.decision
                or self._reset_record is not record
                or self._checkpoint_revision != work.next_revision
                or self._failed_step
                or self._initial_reset is not None
                or self._reset_stage != "finalizing"
                or not self._step_active
                or not self._parent_reading_matches(work.candidate)
            ):
                raise ValueError("Final activation reading changed retained population publication")
            self._accepted, self._activation = record.accepted, activation
            self._reset_stage = "completed"
            return record, activation
        except Exception as error:
            self._reset_stage, self._failed_step, self._activation = "failed", True, None
            if record is not None:
                try:
                    self.env.abandon_episode(accepted=record.accepted, reason="runtime_failure")
                except Exception as quarantine_error:
                    error.add_note(f"Reset quarantine failed: {quarantine_error!r}")
            raise
        finally:
            self._initial_reset = None
            self._step_active = False

    def prepare_empty_episode_evidence(self, *, accepted: Any) -> Any:
        """Attest actual zero participation without completing or clearing any work."""
        self._require_operation_idle()
        self._check_owned_state()
        self.env.validate_accepted_episode(accepted=accepted)
        if self._pending_batch_commit is not None:
            raise RuntimeError("Resolve the pending batch commitment before another transition")
        if accepted is None or accepted is not self._accepted or self._population_issuer is None:
            raise ValueError("Empty evidence requires this population's actual activated acceptance")
        if self._step_active or self._failed_step or self._preparing_checkpoint is not None or self._vector_steps:
            raise RuntimeError("Running, failed or pending population work cannot attest an empty episode")
        if self._owned_reset_pending or bool((self.episode_step_counts != 0).any()) or bool((self.env.step_counts != 0).any()):
            raise RuntimeError("A participating or unprepared episode is not empty")
        if self._completed_outcomes or any(episode["observations"] for episode in self.current_episodes):
            raise RuntimeError("Owned outcomes or collected transitions prevent empty evidence")
        if self._vector_step_progress is not None and self._vector_step_progress["accepted_identity"] == self._accepted_identity(accepted):
            raise RuntimeError("An actual vector attempt is distinct from a zero-step empty episode")
        if self._empty_evidence is None:
            self._empty_evidence = self._population_issuer.issue(
                kind="empty_episode", payload={"accepted": accepted, "participated_world_ids": (), "events": ()}
            )
        return self._empty_evidence

    @property
    def vector_step_progress(self) -> dict[str, Any] | None:
        """Owned portable evidence; this reading never authenticates an execution."""
        return copy.deepcopy(self._vector_step_progress)

    @staticmethod
    def _accepted_identity(accepted: Any) -> dict[str, Any]:
        return dict(
            batch_episode=accepted.batch_episode, world_ids=list(accepted.world_ids), world_episode_seqs=list(accepted.world_episode_seqs)
        )

    def _step_record(
        self, *, accepted: Any, world_ids: tuple[str, ...], predecessor: torch.Tensor, actions: torch.Tensor, active_on_entry: torch.Tensor
    ) -> _VectorStep:
        if (
            self._preparing_checkpoint is not None
            or self._selection_frame is not None
            or self._initial_reset is not None
            or self._failed_step
            or self._owned_reset_pending
            or accepted is not self._accepted
            or accepted is None
        ):
            raise RuntimeError("Step requires this population's healthy accepted reset")
        self.env.validate_accepted_episode(accepted=accepted)
        self._validate_owned_training()
        if self._pending_batch_commit is not None:
            raise RuntimeError("Resolve the pending batch commitment before another transition")
        if (
            type(self.total_steps) is not int
            or self._clock_ledger_restore_unavailable
            or self._clock_ledger.vector_ticks != self.total_steps
        ):
            raise ValueError("Next step requires the authoritative complete parent vector position")
        if type(world_ids) is not tuple or world_ids != accepted.world_ids:
            raise ValueError("Step world order must equal the actual accepted binding")
        for value, shape, dtype in (
            (predecessor, (self.num_agents, self._obs_dim), torch.float32),
            (actions, (self.num_agents,), torch.int64),
            (active_on_entry, (self.num_agents,), torch.bool),
        ):
            if (
                not isinstance(value, torch.Tensor)
                or value.layout != torch.strided
                or value.shape != shape
                or value.dtype != dtype
                or value.device != self.device
            ):
                raise ValueError("Step tensors require exact selected geometry, dtype and device")
        if not bool(torch.isfinite(predecessor).all()) or not torch.equal(predecessor, self.current_obs):
            raise ValueError("Step predecessor must equal the population's previous returned observation")
        if not bool(((actions >= 0) & (actions < self.action_dim)).all()):
            raise ValueError("Step actions are outside the selected action vocabulary")
        if not torch.equal(active_on_entry, ~self.env.dones) or bool((active_on_entry & self.episode_completed).any()):
            raise ValueError("Step activity disagrees with actual ENV/population entry state")
        return _VectorStep(
            self.total_steps + 1,
            accepted,
            world_ids,
            predecessor.detach().clone(),
            actions.detach().clone(),
            active_on_entry.detach().clone(),
        )

    @staticmethod
    def _same_step(left: _VectorStep, right: _VectorStep) -> bool:
        return (
            left.vector_tick == right.vector_tick
            and left.accepted is right.accepted
            and left.world_ids == right.world_ids
            and all(
                torch.equal(a, b)
                for a, b in (
                    (left.predecessor, right.predecessor),
                    (left.actions, right.actions),
                    (left.active_on_entry, right.active_on_entry),
                )
            )
        )

    def prepare_vector_step(
        self, *, accepted: Any, world_ids: tuple[str, ...], predecessor: torch.Tensor, actions: torch.Tensor, active_on_entry: torch.Tensor
    ) -> PreparedVectorStep:
        """Own a pure candidate; equal pending preparation retains its issued identity."""
        self._require_operation_idle()
        inspection = object()
        self._step_inspection = inspection
        try:
            return self._prepare_vector_step(
                accepted=accepted, world_ids=world_ids, predecessor=predecessor, actions=actions, active_on_entry=active_on_entry
            )
        finally:
            if self._step_inspection is inspection:
                self._step_inspection = None

    def _prepare_vector_step(
        self, *, accepted: Any, world_ids: tuple[str, ...], predecessor: torch.Tensor, actions: torch.Tensor, active_on_entry: torch.Tensor
    ) -> PreparedVectorStep:
        record = self._step_record(
            accepted=accepted, world_ids=world_ids, predecessor=predecessor, actions=actions, active_on_entry=active_on_entry
        )
        if self._vector_steps:
            handle, pending = next(iter(self._vector_steps.items()))
            if self._vector_stage != "prepared" or not self._same_step(pending, record):
                raise ValueError("Pending step cannot be replaced or executed twice")
            return handle
        handle = PreparedVectorStep()
        self._vector_steps = {handle: record}
        self._vector_stage = "prepared"
        return handle

    def claim_vector_step(
        self,
        *,
        prepared: PreparedVectorStep,
        accepted: Any,
        world_ids: tuple[str, ...],
        predecessor: torch.Tensor,
        actions: torch.Tensor,
        active_on_entry: torch.Tensor,
    ) -> int:
        """Authenticate exactly one prephysics execution of an issued candidate."""
        if self._step_inspection is not None:
            raise RuntimeError("Reentrant population step inspection")
        inspection = object()
        self._step_inspection = inspection
        try:
            return self._claim_vector_step(
                prepared=prepared,
                accepted=accepted,
                world_ids=world_ids,
                predecessor=predecessor,
                actions=actions,
                active_on_entry=active_on_entry,
            )
        finally:
            if self._step_inspection is inspection:
                self._step_inspection = None

    def _claim_vector_step(
        self,
        *,
        prepared: PreparedVectorStep,
        accepted: Any,
        world_ids: tuple[str, ...],
        predecessor: torch.Tensor,
        actions: torch.Tensor,
        active_on_entry: torch.Tensor,
    ) -> int:
        if type(prepared) is not PreparedVectorStep or prepared not in self._vector_steps or self._vector_stage != "prepared":
            raise ValueError("Foreign, consumed or already executing vector step")
        candidate = self._step_record(
            accepted=accepted, world_ids=world_ids, predecessor=predecessor, actions=actions, active_on_entry=active_on_entry
        )
        record = self._vector_steps[prepared]
        if not self._same_step(record, candidate):
            raise ValueError("Claim changed the owned vector step")
        participants = self._episode_participants | set(torch.nonzero(record.active_on_entry, as_tuple=False).flatten().tolist())
        self._episode_participants = participants
        self._vector_stage = "executing"
        return record.vector_tick

    # ------------------------------------------------------------------ #
    # Episode lifecycle helpers
    # ------------------------------------------------------------------ #
    @property
    def clock_ledger(self) -> ClockLedger:
        """Owned runtime clocks; historical checkpoints do not invent missing units."""
        if self._clock_ledger_restore_unavailable:
            raise RuntimeError("The loaded historical checkpoint has no complete clock ledger; native ledger restore is not available")
        return self._clock_ledger

    @property
    def completed_outcomes(self) -> tuple[LaneOutcome, ...]:
        """Independent owned readings of this explicitly begun episode's events."""
        # LaneOutcome construction clones its embedded DTO tensors. Each sink
        # receives its own readings and cannot mutate POP's canonical authority.
        return tuple(replace(event) for event in self._completed_outcomes)

    def bind_episode_worlds(self, *, world_ids: Sequence[str], world_episode_seqs: Sequence[int]) -> None:
        """Own actual caller identities, never infer them from row, batch or tick."""
        self._require_operation_idle()
        if self._failed_step or self._vector_steps:
            raise RuntimeError("Failed or pending population work cannot change world binding")
        if self._preparing_checkpoint is not None or self._step_active or self._pending_batch_commit is not None:
            raise RuntimeError("Reentrant population binding")
        ids, sequences = tuple(world_ids), tuple(world_episode_seqs)
        if len(ids) != self.num_agents or len(sequences) != self.num_agents:
            raise ValueError("World identity binding must contain exactly one entry per lane")
        if any(not isinstance(world, str) or not world.strip() for world in ids) or len(set(ids)) != len(ids):
            raise ValueError("World IDs must be unique concrete nonempty strings")
        if any(type(sequence) is not int or sequence < 0 for sequence in sequences):
            raise ValueError("World episode sequences must be explicit nonnegative integers")
        if self._owned_reset_pending or bool(((self.episode_step_counts > 0) & ~self.episode_completed).any()):
            raise RuntimeError("Complete the current episode before binding another episode")
        self._next_world_binding = ids, sequences
        self._checkpoint_revision += 1

    def begin_batch_episode(self, index: int, planned_horizon: int) -> None:
        """Pin fresh caller binding before the next population reset and rollout."""
        self._require_operation_idle()
        if self._failed_step or self._vector_steps:
            raise RuntimeError("Failed or pending population work cannot begin an episode")
        if self._preparing_checkpoint is not None or self._step_active or self._pending_batch_commit is not None:
            raise RuntimeError("Reentrant population episode entry")
        if type(index) is not int or index < 0 or type(planned_horizon) is not int or planned_horizon < 1:
            raise ValueError("Batch index/horizon must be nonnegative/positive integers")
        if self._next_world_binding is None:
            raise RuntimeError("Bind concrete world IDs and episode sequences before beginning each owned episode")
        if self._owned_reset_pending or bool(((self.episode_step_counts > 0) & ~self.episode_completed).any()):
            raise RuntimeError("Complete the current episode before beginning another episode")
        if index in self._begun_batch_ids:
            raise ValueError("A batch episode identity cannot be reused")
        ids, sequences = self._next_world_binding
        self._owned_episode = index, planned_horizon, ids, sequences
        self._next_world_binding = None
        self._owned_reset_pending = True
        self._begun_batch_ids.add(index)
        self._checkpoint_revision += 1

    @staticmethod
    def _outcome_fingerprint(event: LaneOutcome) -> str:
        completion = event.outcome
        scalars = (
            event.batch_episode,
            event.planned_horizon,
            event.world_id,
            event.world_episode_seq,
            event.reward_total,
            event.reward_extrinsic,
            event.reward_intrinsic,
            event.reward_shaping,
            event.policy_entropy,
            completion.agent_idx,
            completion.reason,
            completion.survival_time,
        )
        digest = hashlib.sha256(repr(scalars).encode("utf-8"))
        for reading in (completion.final_observation, completion.final_meters):
            digest.update(str((reading.dtype, tuple(reading.shape))).encode("utf-8"))
            digest.update(reading.detach().cpu().contiguous().numpy().tobytes())
        return digest.hexdigest()

    @property
    def batch_commit_progress(self) -> dict[str, Any] | None:
        """Owned completion custody, including an unresolved possibly mutating child call."""
        return copy.deepcopy(self._batch_commit_progress)

    def _retain_participant_roster(self) -> None:
        if self._owned_episode is None or self._accepted is None or self._owned_episode[0] != self._accepted.batch_episode:
            return
        participants = tuple(torch.nonzero(self.episode_step_counts > 0, as_tuple=False).flatten().tolist())
        if (
            participants
            and set(participants) == self._episode_participants
            and all(bool(self.episode_completed[lane]) for lane in participants)
            and all(bool(self.env.dones[lane]) for lane in range(self.num_agents) if lane not in participants)
        ):
            self._batch_participants[self._owned_episode[0]] = participants

    def commit_episode_outcomes(self, outcomes: Sequence[LaneOutcome]) -> None:
        """Retain exact child retry custody; publish parent completion only after its return."""
        self._require_operation_idle()
        if (
            self._step_active
            or self._failed_step
            or self._preparing_checkpoint is not None
            or self._batch_commit_active
            or self._vector_steps
        ):
            raise RuntimeError("Cannot commit outcomes during running, pending or failed population work")
        incoming = tuple(outcomes)
        prepared: dict[tuple[int, int], str] = {}
        request_values: dict[tuple[int, int], bytes] = {}
        for event in incoming:
            if not isinstance(event, LaneOutcome):
                raise ValueError("Only owned LaneOutcome events may be committed")
            identity = event.batch_episode, event.outcome.agent_idx
            fingerprint = self._outcome_fingerprint(event)
            expected = self._published_outcome_fingerprints.get(identity)
            if expected is None or fingerprint != expected or (identity in prepared and prepared[identity] != fingerprint):
                raise ValueError("Outcome was not published or its owned content changed")
            canonical = freeze_lane_outcome(event).payload
            if canonical != freeze_lane_outcome(self._published_events[identity]).payload:
                raise ValueError("Outcome canonical content differs from its actual publication")
            request_values[identity] = canonical
            prepared[identity] = fingerprint
        batches = {identity[0] for identity in prepared}
        request = tuple(sorted(request_values.items()))
        if self._pending_batch_commit is not None and request != self._pending_batch_commit["request"]:
            raise RuntimeError("Resolve the retained batch commitment before unrelated parent work")
        self._committed_outcomes.update(prepared)
        self._retain_participant_roster()
        ordered_batches = sorted(batches)
        if self._pending_batch_commit is not None:
            pending_batch = self._pending_batch_commit["batch"]
            ordered_batches.sort(key=lambda batch: batch != pending_batch)
        for batch in ordered_batches:
            participants = self._batch_participants.get(batch)
            if (
                batch in self._committed_batches
                or not participants
                or not all((batch, lane) in self._committed_outcomes for lane in participants)
            ):
                continue
            if self._pending_batch_commit is None:
                events = tuple(self._published_events[(batch, lane)] for lane in participants)
                content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, events))
                self._pending_batch_commit = dict(
                    batch=batch,
                    events=events,
                    content=content,
                    request=request,
                    before=self.exploration.epsilon,
                    ledger=self._clock_ledger.advance(completed_batch_episodes=1),
                    batches=self._committed_batches | {batch},
                    revision=self._checkpoint_revision + 1,
                )
            pending = self._pending_batch_commit
            self._batch_commit_progress = dict(batch_episode=batch, status="pending", last_reached_stage="runtime_in_progress")
            self._batch_commit_active = True
            try:
                self.exploration.commit_batch_episode(batch_episode=batch, outcomes=pending["events"])
                cadence = dict(
                    schema="parent-global-epsilon-cadence-v1",
                    last_committed=dict(
                        batch_episode=batch,
                        completion_content=pending["content"],
                        epsilon_before=pending["before"],
                        epsilon_after=self.exploration.epsilon,
                    ),
                )
                completed = dict(batch_episode=batch, status="completed", last_reached_stage="completed")
                self._clock_ledger, self._committed_batches = pending["ledger"], pending["batches"]
                self._parent_cadence, self._batch_commit_progress = cadence, completed
                self._checkpoint_revision = pending["revision"]
                self._pending_batch_commit = None
            finally:
                self._batch_commit_active = False

    def validate_committed_batch(self, *, batch_episode: int, outcomes: tuple[Any, ...]) -> None:
        content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, outcomes))
        pending = self._pending_batch_commit
        if not self._batch_commit_active or pending is None or (pending["batch"], pending["content"]) != (batch_episode, content):
            raise ValueError("Global epsilon requires this population's retained complete batch")

    def validate_parent_cadence(self, *, cadence: Any, mode: str, accepted: Any, parent_restore: Any) -> None:
        if self._preparing_checkpoint is not None:
            expected, expected_mode, expected_parent = self._preparing_checkpoint
            if mode != expected_mode or parent_restore is not expected_parent or not self._same_replay_state(cadence, expected):
                raise ValueError("Prepared parent and runtime cadence disagree")
        elif not self._same_replay_state(cadence, self._parent_cadence):
            raise ValueError("Runtime cadence does not match actual parent commitment")
        if accepted is not None:
            self.env.validate_accepted_episode(accepted=accepted)
            if accepted is not self._accepted:
                raise ValueError("Cadence accepted identity differs from this parent")

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
            "next_action_masks": [],
            "legality_recorded": [],
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
    ) -> nn.Module:
        """Build network from brain_config (DRY helper for q_network and target_network).

        Args:
            brain_config: Brain configuration specifying architecture
            obs_dim: Observation dimension
            action_dim: Action dimension
            env: Environment carrying the compiled token schema

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
            return NetworkFactory.build_recurrent(
                config=arch.recurrent,
                action_dim=action_dim,
                token_spec=env.token_spec,
            )
        elif arch.type == "dueling":
            assert arch.dueling is not None, "dueling config must be present"
            return NetworkFactory.build_dueling(
                config=arch.dueling,
                obs_dim=obs_dim,
                action_dim=action_dim,
            )
        elif arch.type == "token_set":
            assert arch.token_set is not None, "token_set config must be present"
            return NetworkFactory.build_token_set(
                config=arch.token_set,
                action_dim=action_dim,
                token_spec=env.token_spec,
            )
        else:
            raise ValueError(f"Unsupported architecture type: {arch.type}. Supported: feedforward, recurrent, dueling, token_set")

    def _store_episode_and_reset(self, agent_idx: int) -> bool:
        """Store accumulated episode for agent and reset buffers."""
        if not self.is_recurrent or not self.current_episodes:
            return False

        episode = self.current_episodes[agent_idx]
        if len(episode["observations"]) == 0:
            return False

        self._bind_training()
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

        sequential_buffer.store_captured_episode(
            episode_data,
            next_action_masks=torch.stack(episode["next_action_masks"]),
            legality_recorded=torch.stack(episode["legality_recorded"]),
        )

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
        self, network: RecurrentTokenQNetwork, observations: torch.Tensor
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
        """Evaluate a sampled sequence in one recurrent network call.

        Hidden state is LOCAL to this unroll: it starts at zeros for every sampled
        sequence (DRQN zero-start, retained deliberately - the WS-1(b) defect was
        the missing carry between timesteps, not the zero start). The rollout
        memory in self.rollout_hidden is never touched.

        Args:
            observations: [batch, seq_len, obs_dim]

        Returns:
            (q_values, final_hidden), where q_values is [batch, sequence, action]
            and final_hidden is used for the boundary bootstrap.
        """
        batch_size = observations.shape[0]
        hidden = network.initial_hidden(batch_size, observations.device)
        return cast(tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]], network(observations, hidden))

    @torch.no_grad()
    def _rollout_q(self, eligible: torch.Tensor) -> torch.Tensor:
        if self.is_recurrent:
            recurrent = cast(RecurrentTokenQNetwork, self.q_network)
            assert self.rollout_hidden is not None
            h, c = self.rollout_hidden
            inactive_h, inactive_c = h[:, ~eligible].clone(), c[:, ~eligible].clone()
            sequence, (next_h, next_c) = recurrent(self.current_obs.unsqueeze(1), (h, c))
            next_h[:, ~eligible], next_c[:, ~eligible] = inactive_h, inactive_c
            self.rollout_hidden = next_h, next_c
            values = sequence[:, 0]
        else:
            values = self.q_network(self.current_obs)
        self.last_selected_q_values = values
        return cast(torch.Tensor, values)

    @staticmethod
    def _validate_selection(values: torch.Tensor, masks: torch.Tensor, eligible: torch.Tensor) -> None:
        if eligible.dtype != torch.bool or eligible.shape != values.shape[:1] or eligible.device != values.device:
            raise ValueError("Action eligibility must be bool[N] on the Q device")
        if masks.dtype != torch.bool or masks.shape != values.shape or masks.device != values.device:
            raise ValueError("Action masks must be bool[N,A] on the Q device")
        if bool((eligible & ~masks.any(dim=1)).any()):
            raise ValueError("eligible rows have no legal actions")

    def _select_eligible(
        self,
        values: torch.Tensor,
        state: BatchedAgentState,
        masks: torch.Tensor,
        eligible: torch.Tensor,
    ) -> torch.Tensor:
        self._validate_selection(values, masks, eligible)
        actions = values.argmax(dim=1)
        if bool(eligible.any()):
            view = BatchedAgentState(
                observations=state.observations[eligible],
                actions=state.actions[eligible],
                rewards=state.rewards[eligible],
                dones=~eligible[eligible],
                epsilons=state.epsilons[eligible],
                intrinsic_rewards=state.intrinsic_rewards[eligible],
                survival_times=state.survival_times[eligible],
                device=state.device,
            )
            selected = self.exploration.select_actions(values[eligible], view, masks[eligible])
            if selected.shape != actions[eligible].shape or selected.dtype != torch.int64 or selected.device != actions.device:
                raise ValueError("Provider actions must be int64[eligible rows] on the Q device")
            actions[eligible] = selected
        return actions

    # ------------------------------------------------------------------ #
    # Telemetry synchronisation helpers
    # ------------------------------------------------------------------ #
    def _get_current_epsilon_value(self) -> float:
        """Read the current runtime's independent global selector."""
        return self.exploration.epsilon

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
        self._require_operation_idle()
        if self._failed_step or self._pending_batch_commit is not None or self._vector_steps or self._owned_reset_pending:
            raise RuntimeError("Reentrant population telemetry publication")
        self._publish_exploration_metrics()

    def _publish_exploration_metrics(self) -> None:
        epsilon_tensor = torch.full(
            (self.num_agents,),
            self._get_current_epsilon_value(),
            dtype=torch.float32,
            device=self.device,
        )
        self.current_epsilons = epsilon_tensor

        for idx in range(self.num_agents):
            self.runtime_registry.set_epsilon(agent_idx=idx, epsilon=epsilon_tensor[idx])

    def _finalize_episode(self, agent_idx: int, reason: CompletionReason) -> EpisodeCompletion | None:
        """Close one nonempty lane once and retain its final owned readings."""
        if bool(self.episode_completed[agent_idx]):
            return None
        survival_time = int(self.episode_step_counts[agent_idx].item())
        if survival_time == 0:
            return None
        if self.is_recurrent and not self._store_episode_and_reset(agent_idx):
            raise RuntimeError("A nonempty episode lost its recurrent transitions.")
        completion = EpisodeCompletion(
            agent_idx=agent_idx,
            reason=reason,
            survival_time=survival_time,
            final_observation=self.current_obs[agent_idx].detach().cpu().clone(),
            final_meters=self.env.meters[agent_idx].detach().cpu().clone(),
        )
        envelope = None
        if self._owned_episode is not None:
            if not bool(self._episode_entropy_present[agent_idx]):
                raise RuntimeError("A nonempty owned episode has no eligible policy entropy snapshot")
            batch, horizon, worlds, sequences = self._owned_episode
            totals = self._episode_reward_totals[agent_idx].tolist()
            envelope = LaneOutcome(
                outcome=completion,
                batch_episode=batch,
                planned_horizon=horizon,
                reward_total=totals[0],
                reward_extrinsic=totals[1],
                reward_intrinsic=totals[2],
                reward_shaping=totals[3],
                policy_entropy=float(self._episode_entropies[agent_idx].item()),
                world_id=worlds[agent_idx],
                world_episode_seq=sequences[agent_idx],
            )
        self.episode_completed[agent_idx] = True
        self.episode_completions[agent_idx] = completion
        if envelope is not None:
            # Pin authoritative content at publication, before any public read.
            # Fingerprints survive accepted resets so delayed/partial commits
            # retain authority without retaining every episode's tensor payloads.
            identity = envelope.batch_episode, envelope.outcome.agent_idx
            self._published_outcome_fingerprints[identity] = self._outcome_fingerprint(envelope)
            self._published_events[identity] = replace(envelope)
            self._completed_outcomes = (*self._completed_outcomes, envelope)
        self.runtime_registry.record_survival_time(agent_idx=agent_idx, steps=survival_time)
        self._publish_exploration_metrics()
        self._reset_hidden_state(agent_idx)
        self._retain_participant_roster()
        return completion

    def flush_episode(self, agent_idx: int, reason: RunnerCompletionReason) -> EpisodeCompletion | None:
        """Complete a surviving lane for an explicit external stop without changing replay done."""
        self._require_operation_idle()
        if self._preparing_checkpoint is not None or self._step_active or self._failed_step or self._pending_batch_commit is not None:
            raise RuntimeError("Cannot flush during running, restoring or failed population work")
        if self._vector_steps or self._owned_reset_pending:
            raise RuntimeError("Complete pending population work before flushing")
        self._step_active = True
        try:
            prior = self._validate_owned_training()
            completed = prior.completed.clone()
            if int(prior.counts[agent_idx]) > 0:
                completed[agent_idx] = True
            candidate = replace(prior, completed=completed)
            self._checkpoint_revision += 1
            try:
                result = self._finalize_episode(agent_idx, reason)
                assert self._initial_decision is not None
                self.env.validate_initial_participation(
                    accepted=prior.accepted, participation=self._initial_decision.participation, predecessor=prior.observation
                )
                if not self._parent_reading_matches(candidate):
                    raise ValueError("Flush callback changed the owned population reading")
                self._prior_reading = candidate
                self._check_owned_state()
                return result
            except Exception as error:
                self._quarantine_participation(error)
                raise
        finally:
            self._step_active = False

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
        frame = self._begin_selection()
        try:
            with torch.no_grad():
                eligible = ~env.dones & ~self.episode_completed
                q_values = self._rollout_q(eligible)
                action_masks = env.get_action_masks()
                self._revalidate_selection(frame)
                self._validate_selection(q_values, action_masks, eligible)
                actions = q_values.argmax(dim=1)
                actions[eligible] = q_values[eligible].masked_fill(~action_masks[eligible], -torch.inf).argmax(dim=1)
                return actions
        except Exception as error:
            self._check_selection_exception(frame, error)
            raise
        finally:
            if self._selection_frame is frame:
                self._selection_frame = None

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
        frame = self._begin_selection()
        try:
            with torch.no_grad():
                eligible = ~env.dones & ~self.episode_completed
                q_values = self._rollout_q(eligible)
                action_masks = env.get_action_masks()
                self._revalidate_selection(frame)
                epsilons = torch.full((self.num_agents,), epsilon, device=self.device, dtype=torch.float32)
                return epsilon_greedy_action_selection_eligible(
                    q_values=q_values,
                    epsilons=epsilons,
                    action_masks=action_masks,
                    eligible=eligible,
                )
        except Exception as error:
            self._check_selection_exception(frame, error)
            raise
        finally:
            if self._selection_frame is frame:
                self._selection_frame = None

    def step_population(self, envs: VectorizedHamletEnv) -> BatchedAgentState:
        """Execute once; retain truthful progress and quarantine irreversible failures."""
        self._require_operation_idle()
        if self._step_active or self._failed_step or self._preparing_checkpoint is not None or self._pending_batch_commit is not None:
            raise RuntimeError("Reentrant or quarantined population step")
        if envs is not self.env or self._accepted is None or self._clock_ledger_restore_unavailable:
            raise ValueError("Step requires this population's bound current ENV and complete clocks")
        if self._vector_steps:
            raise RuntimeError("Resolve the pending vector step before another population step")
        self._step_active = True
        try:
            self._validate_owned_training()
            self._checkpoint_revision += 1
            state = self._execute_population_step(envs)
            record = next(iter(self._vector_steps.values()))
            self._vector_step_progress = dict(
                vector_tick=record.vector_tick,
                status="completed",
                last_reached_stage="completed",
                accepted_identity=self._accepted_identity(record.accepted),
            )
            self._vector_stage = "completed"
            self._vector_steps = {}
            return state
        except Exception as error:
            if self._vector_steps:
                record = next(iter(self._vector_steps.values()))
                self._vector_step_progress = dict(
                    vector_tick=record.vector_tick,
                    status="failed",
                    last_reached_stage=self._vector_stage,
                    accepted_identity=self._accepted_identity(record.accepted),
                )
                self._failed_step = True
                if self._vector_stage != "prepared":
                    for quarantine in (
                        lambda: self.exploration.quarantine_episode(accepted=record.accepted, reason="runtime_failure"),
                        lambda: self.env.abandon_episode(accepted=record.accepted, reason="runtime_failure"),
                    ):
                        try:
                            quarantine()
                        except Exception as quarantine_error:
                            error.add_note(f"Quarantine failure retained with original step error: {quarantine_error!r}")
            raise
        finally:
            self._step_active = False

    def _execute_population_step(
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

        if bool(self.episode_completed.all()):
            raise RuntimeError("Population episode is complete; call reset before stepping.")
        if self._owned_reset_pending:
            raise RuntimeError("Reset the explicitly begun batch before stepping")
        prior = self._validate_owned_training()
        active_on_entry = ~envs.dones.clone()
        if bool((active_on_entry & self.episode_completed).any()):
            raise RuntimeError("A completed population lane cannot enter another transition.")
        self._bind_training()
        self._validate_owned_training()
        q_values = self._rollout_q(active_on_entry)
        self._validate_owned_training()
        if self._owned_episode is not None:
            if not bool(torch.isfinite(q_values[active_on_entry]).all()):
                raise ValueError("Owned policy Q-values must be finite at the eligible predecessor")
            if q_values.shape[-1] == 1:
                # A finite deterministic vocabulary has zero entropy. Validate
                # Q first: this is not a fallback for NaN or infinite inputs.
                entropy = torch.zeros_like(q_values[:, 0])
            else:
                probabilities = torch.softmax(q_values, dim=-1)
                entropy = -(probabilities * torch.log(probabilities + 1e-10)).sum(dim=-1) / torch.log(
                    torch.tensor(q_values.shape[-1], dtype=torch.float32, device=q_values.device)
                )
            if not bool(torch.isfinite(entropy[active_on_entry]).all()):
                raise ValueError("Owned policy entropy must be finite at the eligible predecessor")
            active_cpu = active_on_entry.detach().cpu()
            self._episode_entropies[active_cpu] = entropy[active_on_entry].detach().cpu().double()
            self._episode_entropy_present[active_cpu] = True

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
        self._validate_owned_training()
        self._sync_curriculum_metrics()
        self._validate_owned_training()

        # 4. Get action masks from environment
        action_masks = envs.get_action_masks()
        self._validate_owned_training()

        # 5. Select actions via exploration strategy (with action masking)
        actions = self._select_eligible(q_values, temp_state, action_masks, active_on_entry)

        # 6. Extract curriculum difficulty multiplier
        depletion_multiplier = 1.0
        if self.current_curriculum_decisions:
            depletion_multiplier = self.current_curriculum_decisions[0].depletion_multiplier

        # 7. Step environment with curriculum difficulty
        # Note: rewards from environment already contain full DAC composition:
        #   rewards = extrinsic + (intrinsic * base_weight * modifiers) + shaping
        prepared = self._prepare_vector_step(
            accepted=self._accepted,
            world_ids=self._accepted.world_ids,
            predecessor=self.current_obs,
            actions=actions,
            active_on_entry=active_on_entry,
        )
        next_obs, rewards, dones, info = envs.step(actions, depletion_multiplier, vector_step=prepared)

        active_on_entry = info["active_on_entry"]
        newly_terminal = info["newly_terminal"]
        newly_retired = info["newly_retired"]
        components = info["reward_components"]
        intrinsic_weight = info["intrinsic_weight"]
        if self._owned_episode is not None:
            active_cpu = active_on_entry.detach().cpu()
            readings = torch.stack((rewards, components["extrinsic"], components["intrinsic"], components["shaping"]), dim=1)
            self._episode_reward_totals[active_cpu] += readings[active_on_entry].detach().cpu().double()

        handoff = info["intrinsic_transition"]
        if not isinstance(handoff, IntrinsicStepHandoff) or handoff.accepted is not self._accepted:
            raise ValueError("ENV returned a foreign intrinsic handoff")
        record = self._vector_steps[prepared]
        context = handoff.context
        if next_obs.shape != record.predecessor.shape or next_obs.dtype != torch.float32 or next_obs.device != self.device:
            raise ValueError("ENV successor disagrees with the selected parent observation geometry")
        if self._vector_stage != "executing" or context.vector_tick != record.vector_tick or handoff.stamp.world_ids != record.world_ids:
            raise ValueError("ENV did not claim this exact vector step")
        if any(
            not torch.equal(a, b)
            for a, b in (
                (context.predecessor, record.predecessor),
                (context.actions, record.actions),
                (context.active_on_entry, record.active_on_entry),
                (context.successor, next_obs),
                (active_on_entry, record.active_on_entry),
                (handoff.stamp.eligible, record.active_on_entry),
            )
        ):
            raise ValueError("ENV handoff changed the owned canonical transition")
        self._vector_stage = "env_returned"
        next_counts = prior.counts + active_on_entry.long()
        if (
            not self._same_reading(info["step_counts"], next_counts)
            or not self._same_reading(envs.step_counts, next_counts)
            or not bool(torch.isfinite(next_obs).all())
            or info["successor_action_masks"].shape != (self.num_agents, self.action_dim)
            or info["successor_action_masks"].dtype != torch.bool
            or info["successor_action_masks"].device != self.device
        ):
            raise ValueError("ENV return disagrees with the owned next population cut")
        successor = _PopulationReading(
            self._accepted,
            record.vector_tick,
            next_obs.detach().clone(),
            dones.detach().clone(),
            next_counts.detach().clone(),
            prior.completed | newly_terminal,
            next_counts.detach().clone(),
            info["successor_action_masks"].detach().clone(),
        )
        self._returned_step = copy.deepcopy(
            dict(
                observations=next_obs,
                rewards=rewards,
                dones=dones,
                components=components,
                successor_action_masks=info["successor_action_masks"],
            )
        )
        intrinsic_rewards = components["provider_intrinsic_raw"].detach().clone()
        for row, scale in enumerate(components["runtime_intrinsic_scale"]):
            self.runtime_registry.set_intrinsic_weight(agent_idx=row, weight=scale)

        if self.tb_logger is not None:
            self._log_reward_components(components=components, intrinsic_weight=intrinsic_weight)

        if self.is_recurrent:
            for agent_idx in torch.nonzero(active_on_entry, as_tuple=False).flatten().tolist():
                episode = self.current_episodes[agent_idx]
                episode["observations"].append(self.current_obs[agent_idx].detach().cpu().clone())
                episode["actions"].append(actions[agent_idx].detach().cpu().clone())
                episode["rewards"].append(rewards[agent_idx].detach().cpu().clone())
                episode["rewards_extrinsic"].append(components["extrinsic"][agent_idx].detach().cpu().clone())
                episode["rewards_intrinsic"].append(components["intrinsic"][agent_idx].detach().cpu().clone())
                episode["rewards_shaping"].append(components["shaping"][agent_idx].detach().cpu().clone())
                episode["dones"].append(dones[agent_idx].detach().cpu().clone())
                episode["next_observations"].append(next_obs[agent_idx].detach().cpu().clone())
                episode["next_action_masks"].append(info["successor_action_masks"][agent_idx].detach().cpu().clone())
                episode["legality_recorded"].append(torch.tensor(True, dtype=torch.bool))
        else:
            rows = torch.nonzero(active_on_entry, as_tuple=False).flatten()
            flat_buffer = cast(ReplayBuffer | PrioritizedReplayBuffer, self.replay_buffer)
            for chunk in rows.split(self.brain_config.replay.capacity):
                eligible_rewards = RewardTensor.from_dac(
                    total=rewards[chunk],
                    extrinsic=components["extrinsic"][chunk],
                    intrinsic=components["intrinsic"][chunk],
                    shaping=components["shaping"][chunk],
                )
                flat_buffer.push_recorded(
                    observations=self.current_obs[chunk],
                    actions=actions[chunk],
                    rewards=eligible_rewards,
                    next_observations=next_obs[chunk],
                    dones=dones[chunk],
                    next_action_masks=info["successor_action_masks"][chunk],
                )

        self._vector_stage = "replay_admitted"
        receipts = self.exploration.admit_and_service(context=context, stamp=handoff.stamp, accepted=handoff.accepted)
        replacement = self._clock_ledger.advance(
            predictor_admitted_rows=sum(receipt.admitted_rows for receipt in receipts),
            predictor_consumed_minibatches=sum(receipt.optimizer_updates for receipt in receipts),
            predictor_dropped_rows=sum(receipt.dropped_rows for receipt in receipts),
        )
        self._service_receipts = receipts
        self._clock_ledger = replacement
        self.last_rnd_loss = receipts[-1].last_loss if receipts else 0.0
        self._vector_stage = "serviced"
        # Preserve the existing advancement cut; allocate/validate before either publication.
        replacement = self._clock_ledger.advance(vector_ticks=1, eligible_transitions=int(active_on_entry.sum().item()))
        self.total_steps = record.vector_tick
        self._clock_ledger = replacement
        self._vector_stage = "advanced"
        self._pace_replay()
        if self.total_steps % self.train_frequency == 0:
            self._learn()

        # 10. Update current state
        if not self._parent_reading_matches(prior) or self._prior_reading is not prior:
            raise ValueError("A child callback changed the population predecessor")
        assert self._initial_decision is not None
        envs.validate_initial_participation(
            accepted=self._accepted, participation=self._initial_decision.participation, predecessor=successor.observation
        )
        self.current_obs = next_obs

        self.episode_step_counts += active_on_entry.long()
        new_completions = []
        for agent_idx in torch.nonzero(newly_terminal, as_tuple=False).flatten().tolist():
            reason: CompletionReason = "retirement" if bool(newly_retired[agent_idx]) else "authored_terminal"
            completion = self._finalize_episode(agent_idx, reason)
            if completion is not None:
                new_completions.append(completion)
        info["episode_completions"] = tuple(new_completions)
        envs.validate_initial_participation(
            accepted=self._accepted, participation=self._initial_decision.participation, predecessor=successor.observation
        )
        if not self._parent_reading_matches(successor):
            raise ValueError("Population finalization changed the actual successor reading")
        self._prior_reading = successor

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
        self._require_operation_idle()
        if self._failed_step or self._owned_reset_pending or self._vector_steps or self._pending_batch_commit is not None:
            raise RuntimeError("Pending population work cannot update curriculum telemetry")
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
        self._require_operation_idle()
        if self._failed_step or self._vector_steps or self._owned_reset_pending or self._pending_batch_commit is not None:
            raise RuntimeError("Pending population work cannot export a checkpoint")
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
        - Target network weights
        - Optimizer state
        - Scheduler state or explicit null when no scheduler is configured
        - Training counters
        - Replay buffer contents
        - Exploration strategy state
        - Exact universe metadata for identity validation

        Returns:
            Complete checkpoint state dictionary
        """
        self._require_operation_idle()
        if self._owned_reset_pending:
            raise RuntimeError("An outstanding owned reset cannot export a checkpoint")
        failed_diagnostic = self._failed_step and self._has_failed_step_diagnostic()
        if self._failed_step and not failed_diagnostic:
            raise RuntimeError("Failed reset or unclassified work cannot export a healthy checkpoint")
        if self._step_active or self._pending_batch_commit is not None or (self._vector_steps and not self._failed_step):
            raise RuntimeError("In-progress vector work cannot masquerade as a healthy checkpoint")
        bars_config = self.env.bars_config
        return {
            "version": POPULATION_CHECKPOINT_FORMAT_VERSION,
            "clock_ledger": asdict(self.clock_ledger),
            "vector_step_progress": self.vector_step_progress,
            "q_network": self.q_network.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "scheduler": self.scheduler.state_dict() if self.scheduler is not None else None,
            "total_steps": self.total_steps,
            "exploration_state": self._checkpoint_exploration_state(failed_diagnostic=failed_diagnostic),
            "universe_metadata": {
                "meter_count": bars_config.meter_count,
                "meter_names": bars_config.meter_names,
                "version": bars_config.version,
                "obs_dim": self.env.observation_dim,
                "observation_schema_hash": self.env.level.observation_schema_hash,
                "action_dim": self.action_dim,
            },
            "target_network": self.target_network.state_dict(),
            "training_step_counter": self.training_step_counter,
            # All buffer types implement serialize(), but mypy doesn't infer it for unions.
            "replay_buffer": self.replay_buffer.serialize(),  # type: ignore[union-attr]
        }

    def _checkpoint_exploration_state(self, *, failed_diagnostic: bool) -> dict[str, Any]:
        if failed_diagnostic:
            return cast(dict[str, Any], self.exploration.diagnostic_state())
        return cast(dict[str, Any], self.exploration.checkpoint_state())

    def _has_failed_step_diagnostic(self) -> bool:
        progress = self._vector_step_progress
        if not self._failed_step or not self._vector_steps or progress is None:
            return False
        record = next(iter(self._vector_steps.values()))
        if (
            progress["status"] == "failed"
            and progress["last_reached_stage"] == self._vector_stage
            and progress["vector_tick"] == record.vector_tick
            and progress["accepted_identity"] == self._accepted_identity(record.accepted)
        ):
            return True
        return False

    @staticmethod
    def _require_exact_mapping(label: str, incoming_state: object, expected_keys: frozenset[str]) -> Mapping[str, object]:
        if not isinstance(incoming_state, Mapping):
            raise ValueError(f"Population checkpoint {label} must be a mapping; got {type(incoming_state).__name__}.")
        incoming_keys = set(incoming_state)
        if incoming_keys != expected_keys:
            missing = sorted(expected_keys - incoming_keys)
            unknown = sorted(incoming_keys - expected_keys)
            raise ValueError(f"Population checkpoint {label} key mismatch: missing={missing}, unknown={unknown}.")
        return incoming_state

    @staticmethod
    def _require_nonnegative_int(label: str, value: object) -> int:
        if type(value) is not int or value < 0:
            raise ValueError(f"Population checkpoint {label} mismatch: expected a non-negative integer, got {value!r}.")
        return value

    @staticmethod
    def _require_finite_real(label: str, value: object) -> float:
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
            raise ValueError(f"Population checkpoint {label} must be a finite real number; got {value!r}.")
        return float(value)

    @staticmethod
    def _validate_network_checkpoint_state(
        state_key: str,
        incoming_state: object,
        current_state: Mapping[str, torch.Tensor],
    ) -> None:
        if not isinstance(incoming_state, Mapping):
            raise ValueError(f"Population checkpoint {state_key} must be a parameter mapping.")

        incoming_keys = set(incoming_state)
        current_keys = set(current_state)
        if incoming_keys != current_keys:
            missing = sorted(current_keys - incoming_keys)
            unknown = sorted(incoming_keys - current_keys)
            raise ValueError(f"Population checkpoint {state_key} key mismatch: missing={missing}, unknown={unknown}.")

        for parameter_name, current_tensor in current_state.items():
            incoming_tensor = incoming_state[parameter_name]
            if not isinstance(incoming_tensor, torch.Tensor):
                raise ValueError(
                    f"Population checkpoint {state_key}.{parameter_name} must be a tensor; " f"got {type(incoming_tensor).__name__}."
                )
            if incoming_tensor.shape != current_tensor.shape:
                raise ValueError(
                    f"Population checkpoint {state_key} shape mismatch for {parameter_name}: "
                    f"checkpoint={tuple(incoming_tensor.shape)}, current={tuple(current_tensor.shape)}."
                )
            if incoming_tensor.dtype != current_tensor.dtype:
                raise ValueError(
                    f"Population checkpoint {state_key} dtype mismatch for {parameter_name}: "
                    f"checkpoint={incoming_tensor.dtype}, current={current_tensor.dtype}."
                )
            if (incoming_tensor.is_floating_point() or incoming_tensor.is_complex()) and not torch.isfinite(incoming_tensor).all():
                raise ValueError(f"Population checkpoint {state_key}.{parameter_name} contains non-finite values.")

    @classmethod
    def _validate_optimizer_checkpoint_state(
        cls,
        label: str,
        incoming_state: object,
        optimizer: torch.optim.Optimizer,
        *,
        allow_learning_rate_change: bool = False,
    ) -> tuple[float, ...]:
        state = cls._require_exact_mapping(label, incoming_state, frozenset({"state", "param_groups"}))
        saved_state = state["state"]
        saved_groups = state["param_groups"]
        if not isinstance(saved_state, Mapping):
            raise ValueError(f"Population checkpoint {label}.state must be a mapping.")
        if not isinstance(saved_groups, list):
            raise ValueError(f"Population checkpoint {label}.param_groups must be a list.")
        if len(saved_groups) != len(optimizer.param_groups):
            raise ValueError(
                f"Population checkpoint {label} parameter-group count mismatch: "
                f"checkpoint={len(saved_groups)}, current={len(optimizer.param_groups)}."
            )

        current_serialized_groups = optimizer.state_dict()["param_groups"]
        parameter_by_saved_id: dict[int, torch.Tensor] = {}
        expected_state_keys_by_saved_id: dict[int, frozenset[str]] = {}
        saved_learning_rates: list[float] = []
        for group_index, (saved_group, current_group, current_serialized_group) in enumerate(
            zip(saved_groups, optimizer.param_groups, current_serialized_groups, strict=True)
        ):
            if not isinstance(saved_group, Mapping):
                raise ValueError(f"Population checkpoint {label}.param_groups[{group_index}] must be a mapping.")
            expected_group_keys = set(current_serialized_group)
            saved_group_keys = set(saved_group)
            if saved_group_keys != expected_group_keys:
                missing = sorted(expected_group_keys - saved_group_keys)
                unknown = sorted(saved_group_keys - expected_group_keys)
                raise ValueError(
                    f"Population checkpoint {label}.param_groups[{group_index}] key mismatch: " f"missing={missing}, unknown={unknown}."
                )
            group_label = f"{label}.param_groups[{group_index}]"
            for group_key, current_value in current_serialized_group.items():
                if group_key == "params":
                    continue
                saved_value = saved_group[group_key]
                value_label = f"{group_label}.{group_key}"
                if group_key == "lr":
                    if type(saved_value) is not type(current_value):
                        raise ValueError(
                            f"Population checkpoint {value_label} type mismatch: "
                            f"checkpoint={type(saved_value).__name__}, current={type(current_value).__name__}."
                        )
                    learning_rate = cls._require_finite_real(value_label, saved_value)
                    if learning_rate < 0.0:
                        raise ValueError(f"Population checkpoint {value_label} must be non-negative; got {learning_rate}.")
                    if not allow_learning_rate_change and learning_rate != float(current_value):
                        raise ValueError(
                            f"Population checkpoint {value_label} mismatch: checkpoint={learning_rate}, current={current_value}."
                        )
                    saved_learning_rates.append(learning_rate)
                    continue
                cls._validate_exact_checkpoint_value(value_label, saved_value, current_value)

            saved_parameter_ids = saved_group["params"]
            current_parameters = current_group["params"]
            if not isinstance(saved_parameter_ids, list):
                raise ValueError(f"Population checkpoint {label}.param_groups[{group_index}].params must be a list.")
            if len(saved_parameter_ids) != len(current_parameters):
                raise ValueError(
                    f"Population checkpoint {label} parameter count mismatch in group {group_index}: "
                    f"checkpoint={len(saved_parameter_ids)}, current={len(current_parameters)}."
                )
            for parameter_index, (saved_id, parameter) in enumerate(zip(saved_parameter_ids, current_parameters, strict=True)):
                if isinstance(saved_id, bool) or not isinstance(saved_id, int):
                    raise ValueError(
                        f"Population checkpoint {label}.param_groups[{group_index}].params[{parameter_index}] "
                        "must be an integer parameter id."
                    )
                if saved_id in parameter_by_saved_id:
                    raise ValueError(f"Population checkpoint {label} repeats parameter id {saved_id}.")
                if not isinstance(parameter, torch.Tensor):
                    raise ValueError(f"Current {label} parameter {parameter_index} in group {group_index} is not a tensor.")
                parameter_by_saved_id[saved_id] = parameter
                expected_state_keys_by_saved_id[saved_id] = cls._optimizer_parameter_state_keys(optimizer, current_group)

        if any(isinstance(saved_id, bool) or not isinstance(saved_id, int) for saved_id in saved_state):
            raise ValueError(f"Population checkpoint {label}.state entries must map integer ids to mappings.")
        unknown_state_ids = set(saved_state) - set(parameter_by_saved_id)
        if unknown_state_ids:
            raise ValueError(f"Population checkpoint {label}.state has unknown parameter ids: {sorted(unknown_state_ids)}.")
        for saved_id, parameter_state in saved_state.items():
            if not isinstance(parameter_state, Mapping):
                raise ValueError(f"Population checkpoint {label}.state entries must map integer ids to mappings.")
            parameter = parameter_by_saved_id[saved_id]
            expected_state_keys = expected_state_keys_by_saved_id[saved_id]
            if set(parameter_state) != expected_state_keys:
                missing = sorted(expected_state_keys - set(parameter_state))
                unknown = sorted(set(parameter_state) - expected_state_keys)
                raise ValueError(f"Population checkpoint {label}.state[{saved_id!r}] key mismatch: missing={missing}, unknown={unknown}.")
            for value_key, value in parameter_state.items():
                value_label = f"{label}.state[{saved_id!r}].{value_key}"
                if not isinstance(value, torch.Tensor):
                    raise ValueError(f"Population checkpoint {value_label} must be a tensor; got {type(value).__name__}.")
                if value_key == "step":
                    if value.shape != torch.Size([]) or value.dtype is not torch.float32:
                        raise ValueError(f"Population checkpoint {value_label} must be a scalar torch.float32 tensor.")
                    step = float(value.item())
                    if not math.isfinite(step) or step < 0.0 or not step.is_integer():
                        raise ValueError(f"Population checkpoint {value_label} must be a finite non-negative integer-valued scalar.")
                    continue
                if value.shape != parameter.shape:
                    raise ValueError(
                        f"Population checkpoint {value_label} shape mismatch: "
                        f"checkpoint={tuple(value.shape)}, parameter={tuple(parameter.shape)}."
                    )
                if value.dtype != parameter.dtype:
                    raise ValueError(
                        f"Population checkpoint {value_label} dtype mismatch: " f"checkpoint={value.dtype}, parameter={parameter.dtype}."
                    )
                if (value.is_floating_point() or value.is_complex()) and not torch.isfinite(value).all():
                    raise ValueError(f"Population checkpoint {value_label} contains non-finite values.")
        return tuple(saved_learning_rates)

    @classmethod
    def _validate_exact_checkpoint_value(cls, label: str, incoming: object, current: object) -> None:
        if isinstance(current, Mapping):
            if not isinstance(incoming, Mapping):
                raise ValueError(f"Population checkpoint {label} must be a mapping.")
            if set(incoming) != set(current):
                missing = sorted(set(current) - set(incoming))
                unknown = sorted(set(incoming) - set(current))
                raise ValueError(f"Population checkpoint {label} key mismatch: missing={missing}, unknown={unknown}.")
            for key, current_value in current.items():
                cls._validate_exact_checkpoint_value(f"{label}.{key}", incoming[key], current_value)
            return
        if isinstance(current, (list, tuple)):
            if type(incoming) is not type(current) or len(incoming) != len(current):
                raise ValueError(f"Population checkpoint {label} sequence shape/type mismatch.")
            for index, (incoming_value, current_value) in enumerate(zip(incoming, current, strict=True)):
                cls._validate_exact_checkpoint_value(f"{label}[{index}]", incoming_value, current_value)
            return
        if isinstance(current, torch.Tensor):
            if not isinstance(incoming, torch.Tensor) or incoming.shape != current.shape or incoming.dtype != current.dtype:
                raise ValueError(f"Population checkpoint {label} tensor shape/dtype mismatch.")
            if (incoming.is_floating_point() or incoming.is_complex()) and not torch.isfinite(incoming).all():
                raise ValueError(f"Population checkpoint {label} contains non-finite values.")
            if not torch.equal(incoming, current):
                raise ValueError(f"Population checkpoint {label} mismatch against the current configuration.")
            return
        if current is None:
            if incoming is not None:
                raise ValueError(f"Population checkpoint {label} must be null.")
            return
        if type(incoming) is not type(current):
            raise ValueError(
                f"Population checkpoint {label} type mismatch: checkpoint={type(incoming).__name__}, current={type(current).__name__}."
            )
        if isinstance(incoming, bool):
            if incoming != current:
                raise ValueError(f"Population checkpoint {label} mismatch: checkpoint={incoming!r}, current={current!r}.")
            return
        if isinstance(incoming, Real):
            cls._require_finite_real(label, incoming)
        if incoming != current:
            raise ValueError(f"Population checkpoint {label} mismatch: checkpoint={incoming!r}, current={current!r}.")

    @staticmethod
    def _optimizer_parameter_state_keys(
        optimizer: torch.optim.Optimizer,
        parameter_group: Mapping[str, Any],
    ) -> frozenset[str]:
        if isinstance(optimizer, (torch.optim.Adam, torch.optim.AdamW)):
            keys = {"step", "exp_avg", "exp_avg_sq"}
            if parameter_group["amsgrad"] is True:
                keys.add("max_exp_avg_sq")
            return frozenset(keys)
        if isinstance(optimizer, torch.optim.SGD):
            return frozenset({"momentum_buffer"}) if float(parameter_group["momentum"]) > 0.0 else frozenset()
        if isinstance(optimizer, torch.optim.RMSprop):
            keys = {"step", "square_avg"}
            if float(parameter_group["momentum"]) > 0.0:
                keys.add("momentum_buffer")
            if parameter_group["centered"] is True:
                keys.add("grad_avg")
            return frozenset(keys)
        raise ValueError(f"Population checkpoint optimizer type {type(optimizer).__name__} is unsupported.")

    @classmethod
    def _validate_scheduler_checkpoint_state(
        cls,
        label: str,
        incoming_state: object,
        scheduler: torch.optim.lr_scheduler.LRScheduler,
        optimizer_learning_rates: tuple[float, ...],
    ) -> None:
        current_state = scheduler.state_dict()
        state = cls._require_exact_mapping(label, incoming_state, frozenset(current_state))
        mutable_keys = frozenset({"last_epoch", "_step_count", "_is_initial", "_get_lr_called_within_step", "_last_lr"})
        for key, current_value in current_state.items():
            if key not in mutable_keys:
                cls._validate_exact_checkpoint_value(f"{label}.{key}", state[key], current_value)

        last_epoch = cls._require_nonnegative_int(f"{label}.last_epoch", state["last_epoch"])
        step_count = cls._require_nonnegative_int(f"{label}._step_count", state["_step_count"])
        if step_count != last_epoch + 1:
            raise ValueError(
                f"Population checkpoint {label}._step_count must equal last_epoch + 1; "
                f"checkpoint={step_count}, expected={last_epoch + 1}."
            )
        for key in ("_is_initial", "_get_lr_called_within_step"):
            value = state[key]
            if type(value) is not bool or value is not False:
                raise ValueError(f"Population checkpoint {label}.{key} must be false outside a scheduler step.")

        last_learning_rates = state["_last_lr"]
        if not isinstance(last_learning_rates, list) or len(last_learning_rates) != len(optimizer_learning_rates):
            raise ValueError(
                f"Population checkpoint {label}._last_lr must be a list with " f"{len(optimizer_learning_rates)} optimizer-group entries."
            )
        for index, (value, optimizer_value) in enumerate(zip(last_learning_rates, optimizer_learning_rates, strict=True)):
            value_label = f"{label}._last_lr[{index}]"
            if type(value) is not float:
                raise ValueError(f"Population checkpoint {value_label} must be a float; got {type(value).__name__}.")
            learning_rate = cls._require_finite_real(value_label, value)
            if learning_rate < 0.0:
                raise ValueError(f"Population checkpoint {value_label} must be non-negative; got {learning_rate}.")
            if learning_rate != optimizer_value:
                raise ValueError(
                    f"Population checkpoint {value_label} must match optimizer group {index} lr; "
                    f"scheduler={learning_rate}, optimizer={optimizer_value}."
                )

    def _validate_checkpoint_state(self, checkpoint: Mapping[str, object]) -> Any:
        """
        Validate a complete population checkpoint without mutating runtime state.

        Args:
            checkpoint: State dictionary from get_checkpoint_state()

        Raises:
            ValueError: If the payload or universe identity is not exactly current
        """
        if not isinstance(checkpoint, Mapping):
            raise ValueError(f"Population checkpoint payload must be a mapping; got {type(checkpoint).__name__}.")

        # The version is the first artifact gate. A previous-format payload is not
        # inspected for keys or nested state because its entire shape is invalid.
        checkpoint_version = checkpoint.get("version")
        if type(checkpoint_version) is not int or checkpoint_version != POPULATION_CHECKPOINT_FORMAT_VERSION:
            raise ValueError(
                "Unsupported population checkpoint version: "
                f"checkpoint={checkpoint_version!r}, expected={POPULATION_CHECKPOINT_FORMAT_VERSION}. "
                "Regenerate the checkpoint with the current compact observation ABI."
            )

        checkpoint_keys = set(checkpoint)
        if checkpoint_keys != POPULATION_CHECKPOINT_KEYS:
            missing = sorted(POPULATION_CHECKPOINT_KEYS - checkpoint_keys)
            unknown = sorted(checkpoint_keys - POPULATION_CHECKPOINT_KEYS)
            raise ValueError(
                "Population checkpoint key set mismatch: "
                f"missing={missing}, unknown={unknown}. "
                "This checkpoint payload is no longer supported; retrain from scratch."
            )

        current_obs_dim = self.env.observation_dim
        token_obs_dim = self.token_spec.total_dims
        if current_obs_dim != token_obs_dim:
            raise ValueError(
                "Current environment observation_dim must equal token_spec.total_dims before checkpoint state can be applied: "
                f"observation_dim={current_obs_dim}, token_spec.total_dims={token_obs_dim}."
            )
        if self._obs_dim != current_obs_dim:
            raise ValueError(
                "Current population obs_dim must equal the environment compact observation width before checkpoint state can be applied: "
                f"population={self._obs_dim}, environment={current_obs_dim}."
            )

        metadata = checkpoint["universe_metadata"]
        if not isinstance(metadata, Mapping):
            raise ValueError(
                "Population universe_metadata must be a mapping with the exact current key set; " f"got {type(metadata).__name__}."
            )

        metadata_keys = set(metadata)
        if metadata_keys != POPULATION_UNIVERSE_METADATA_KEYS:
            missing = sorted(POPULATION_UNIVERSE_METADATA_KEYS - metadata_keys)
            unknown = sorted(metadata_keys - POPULATION_UNIVERSE_METADATA_KEYS)
            raise ValueError(
                "Population universe_metadata key set mismatch: "
                f"missing={missing}, unknown={unknown}. "
                "This checkpoint payload is no longer supported; retrain from scratch."
            )

        # Validate universe identity before mutating any population state.
        checkpoint_observation_hash = metadata["observation_schema_hash"]
        if not isinstance(checkpoint_observation_hash, str):
            raise ValueError("Population universe_metadata.observation_schema_hash must be a string.")
        current_observation_hash = self.env.level.observation_schema_hash
        if checkpoint_observation_hash != current_observation_hash:
            raise ValueError(
                "Checkpoint observation_schema_hash mismatch: "
                f"checkpoint={str(checkpoint_observation_hash)[:16]}..., "
                f"current={current_observation_hash[:16]}.... "
                "The selected level's observation semantics changed; retrain or load the exact compiled level."
            )
        checkpoint_action_dim = self._require_nonnegative_int("universe_metadata.action_dim", metadata["action_dim"])
        if checkpoint_action_dim != self.action_dim:
            raise ValueError(
                "Checkpoint action_dim mismatch: "
                f"checkpoint={checkpoint_action_dim!r}, current={self.action_dim}. "
                "The action ABI changed; retrain or load the exact compiled level."
            )
        bars_config = self.env.bars_config
        checkpoint_meter_count = self._require_nonnegative_int("universe_metadata.meter_count", metadata["meter_count"])
        current_meter_count = bars_config.meter_count
        if checkpoint_meter_count != current_meter_count:
            raise ValueError(
                f"Checkpoint meter count mismatch: checkpoint has {checkpoint_meter_count} meters, "
                f"but current environment has {current_meter_count} meters. "
                f"Cannot load checkpoint trained on different universe configuration."
            )

        checkpoint_meter_names = metadata["meter_names"]
        if type(checkpoint_meter_names) is not type(bars_config.meter_names) or not isinstance(checkpoint_meter_names, (list, tuple)):
            raise ValueError(
                "Population universe_metadata.meter_names type mismatch: "
                f"checkpoint={type(checkpoint_meter_names).__name__}, current={type(bars_config.meter_names).__name__}."
            )
        if any(not isinstance(name, str) for name in checkpoint_meter_names):
            raise ValueError("Population universe_metadata.meter_names entries must be strings.")
        if checkpoint_meter_names != bars_config.meter_names:
            raise ValueError(
                "Checkpoint meter names mismatch: "
                f"checkpoint={checkpoint_meter_names!r}, current={bars_config.meter_names!r}. "
                "Cannot load checkpoint trained on a different meter layout."
            )

        checkpoint_bars_version = metadata["version"]
        if not isinstance(checkpoint_bars_version, str):
            raise ValueError("Population universe_metadata.version must be a string.")
        if checkpoint_bars_version != bars_config.version:
            raise ValueError(
                "Checkpoint bar config version mismatch: " f"checkpoint={checkpoint_bars_version!r}, current={bars_config.version!r}."
            )

        # Validate obs_dim matches.
        #
        # This was a WARNING that then proceeded to load_state_dict anyway. That was already
        # wrong — a differing obs_dim means the first Linear layer has a different in_features
        # and the load either raises with a shape message that names neither cause, or (for a
        # recurrent net, whose encoders are sized per BLOCK) succeeds against a layout the
        # weights were never trained on.
        #
        # This is deliberately a narrow dimensional guard. The outer checkpoint-identity gate
        # compares semantic hashes, including the compiled static identity changed by a meter's
        # range_type. Every admitted meter normalization occupies the same fixed two-lane block,
        # so changing range_type alone does not change obs_dim. The count check above can still
        # pass while another token capacity or payload-width change alters the serialized tensor;
        # this inner check catches only that shape mismatch.
        checkpoint_obs_dim = self._require_nonnegative_int("universe_metadata.obs_dim", metadata["obs_dim"])
        if checkpoint_obs_dim != current_obs_dim:
            raise ValueError(
                f"Checkpoint obs_dim mismatch: checkpoint has {checkpoint_obs_dim}, "
                f"current env has {current_obs_dim}.\n"
                "  Cause: compiled token capacity or payload width differs from the universe "
                "this checkpoint was trained on.\n"
                "  Rule: this inner guard checks serialized tensor dimensions only; the outer "
                "checkpoint-identity gate handles semantic changes. Retrain, or load against "
                "the universe the checkpoint names."
            )

        scheduler_state = checkpoint["scheduler"]
        if (self.scheduler is None) != (scheduler_state is None):
            raise ValueError(
                "Population checkpoint scheduler nullability mismatch: "
                f"checkpoint_has_scheduler={scheduler_state is not None}, "
                f"current_has_scheduler={self.scheduler is not None}."
            )

        for state_key in ("q_network", "optimizer", "target_network", "replay_buffer", "exploration_state"):
            if checkpoint[state_key] is None:
                raise ValueError(f"Population checkpoint {state_key} must contain state, got null.")

        self._require_nonnegative_int("total_steps", checkpoint["total_steps"])
        self._require_nonnegative_int("training_step_counter", checkpoint["training_step_counter"])
        self._validate_network_checkpoint_state("q_network", checkpoint["q_network"], self.q_network.state_dict())
        self._validate_network_checkpoint_state("target_network", checkpoint["target_network"], self.target_network.state_dict())
        optimizer_learning_rates = self._validate_optimizer_checkpoint_state(
            "optimizer",
            checkpoint["optimizer"],
            self.optimizer,
            allow_learning_rate_change=self.scheduler is not None,
        )
        if self.scheduler is not None:
            self._validate_scheduler_checkpoint_state("scheduler", scheduler_state, self.scheduler, optimizer_learning_rates)
        replay_state = cast(Mapping[str, Any], checkpoint["replay_buffer"])
        replay_target = self.replay_buffer
        # Captured6 has no PER clock/state. Prepare its actual selected target at
        # the restored tick offside; never move a live target merely to validate.
        if self.is_recurrent and self.use_per and replay_state.get("format_version") in (5, 6):
            restored_tick = cast(int, checkpoint["total_steps"])
            if self._replay_setup is not None:
                setup = replace(self._replay_setup, tick=restored_tick)
            else:
                setup = self._compiled_replay_setup(restored_tick)
            replay_target = self._new_replay(setup)
        validated_replay: Any = replay_target.validate_serialized(replay_state, expected_obs_dim=current_obs_dim)
        if self.is_recurrent and replay_state.get("format_version") == 7:
            if replay_state["priority_state"]["current_vector_tick"] != checkpoint["total_steps"]:
                raise ValueError("Sequential replay vector tick must equal the restored population total_steps")
        return replay_target, validated_replay

    def _checkpoint_clocks(self, checkpoint: Mapping[str, Any]) -> tuple[ClockLedger, Any]:
        raw = self._require_exact_mapping("clock_ledger", checkpoint["clock_ledger"], frozenset(asdict(ClockLedger())))
        ledger = ClockLedger(**{key: self._require_nonnegative_int(f"clock_ledger.{key}", value) for key, value in raw.items()})
        if ledger.vector_ticks != checkpoint["total_steps"] or ledger.optimizer_updates != checkpoint["training_step_counter"]:
            raise ValueError("Population counters disagree with the complete clock ledger")
        progress = copy.deepcopy(checkpoint["vector_step_progress"])
        if progress is None:
            if any(asdict(ledger).values()):
                raise ValueError("Only genuine fresh INITIAL has no vector progress")
            return ledger, progress
        record = self._require_exact_mapping(
            "vector_step_progress", progress, frozenset({"vector_tick", "status", "last_reached_stage", "accepted_identity"})
        )
        if record["status"] != "completed" or record["last_reached_stage"] != "completed":
            raise ValueError("Failed or in-progress work cannot enter a healthy native restore")
        if type(record["vector_tick"]) is not int or record["vector_tick"] != ledger.vector_ticks or ledger.vector_ticks < 1:
            raise ValueError("Completed progress must name the reached parent vector tick")
        accepted = self._require_exact_mapping(
            "accepted_identity", record["accepted_identity"], frozenset({"batch_episode", "world_ids", "world_episode_seqs"})
        )
        self._require_nonnegative_int("accepted batch", accepted["batch_episode"])
        ids, seqs = cast(list[Any], accepted["world_ids"]), cast(list[Any], accepted["world_episode_seqs"])
        if (
            type(ids) is not list
            or len(ids) != self.num_agents
            or any(type(item) is not str for item in ids)
            or len(set(ids)) != len(ids)
            or set(ids) != set(self.env.world_ids)
        ):
            raise ValueError("Progress requires actual portable world membership")
        if type(seqs) is not list or len(seqs) != self.num_agents or any(type(item) is not int or item < 1 for item in seqs):
            raise ValueError("Progress requires actual positive accepted world sequences")
        return ledger, progress

    def prepare_checkpoint_state(
        self, checkpoint: Mapping[str, Any], *, mode: str, parent_restore: Any, validate_parent_restore: Any, initialization: str | None
    ) -> PreparedPopulationRestore:
        """Prepare every owned child offside; external boundary authentication stays genuine."""
        self._require_operation_idle()
        if self._failed_step or self._owned_reset_pending or self._vector_steps:
            raise RuntimeError("A failed population cannot install boundary state")
        if self._step_active or self._preparing_checkpoint is not None or self._pending_batch_commit is not None:
            raise RuntimeError("Reentrant population restore")
        if self._accepted is not None:
            raise ValueError("Boundary restore requires a fresh receiving population")
        if self.env.world_phase != "fresh-unbound":
            raise ValueError("Bound component replacement requires the genuine outer stable-owner installation protocol")
        revision = self._checkpoint_revision
        owned = copy.deepcopy(checkpoint)
        replay_target, validated_replay = self._validate_checkpoint_state(owned)
        ledger, progress = self._checkpoint_clocks(owned)
        if mode not in {"initial", "completed_boundary", "private_initialized"} or (mode == "initial") != (progress is None):
            raise ValueError("Healthy parent progress disagrees with requested boundary mode")
        if mode != "initial" and (parent_restore is None or not callable(validate_parent_restore)):
            raise ValueError("Completed/initialized restore requires genuine external parent preparation")
        q, target, optimizer, scheduler = copy.deepcopy((self.q_network, self.target_network, self.optimizer, self.scheduler))
        q.load_state_dict(owned["q_network"])
        target.load_state_dict(owned["target_network"])
        optimizer.load_state_dict(owned["optimizer"])
        if scheduler is not None:
            scheduler.load_state_dict(owned["scheduler"])
        if replay_target is self.replay_buffer:
            # Replay custody is owner-bound and contains locks and opaque RNG
            # authority. Reconstruct offside through its real transport instead
            # of copying that authority or moving a prepared handle to a copy.
            if self._replay_setup is not None:
                setup = replace(self._replay_setup, tick=ledger.vector_ticks)
            else:
                setup = self._compiled_replay_setup(ledger.vector_ticks)
            replay_target = self._new_replay(setup)
            retained = replay_target.prepare_serialized(self.replay_buffer.serialize(), expected_obs_dim=self._obs_dim, lineage=None)
            replay_target.load_prepared(retained, lineage=None)
        prepared_replay = replay_target.materialize_validated(validated_replay, lineage=None)
        replay_target.load_prepared(prepared_replay, lineage=None)
        cadence = copy.deepcopy(owned["exploration_state"]["cadence"])
        correlation = cadence, mode, parent_restore
        self._preparing_checkpoint = correlation
        try:
            if initialization is None:
                runtime = self.exploration.prepare_restore(
                    state=owned["exploration_state"],
                    mode=mode,
                    accepted=None,
                    parent_restore=parent_restore,
                    validate_parent_restore=validate_parent_restore,
                )
            else:
                runtime = self.exploration.prepare_private_initialization(
                    state=owned["exploration_state"],
                    initialization=initialization,
                    parent_restore=parent_restore,
                    validate_parent_restore=validate_parent_restore,
                )
        finally:
            self._preparing_checkpoint = None
        if revision != self._checkpoint_revision:
            raise ValueError("Population changed during restore preparation")
        handle = PreparedPopulationRestore()
        self._population_restores[handle] = (
            revision,
            runtime,
            q,
            target,
            optimizer,
            scheduler,
            replay_target,
            ledger,
            progress,
            correlation,
            cadence,
        )
        return handle

    def install_checkpoint_state(self, *, prepared: PreparedPopulationRestore) -> None:
        self._require_operation_idle()
        if self._failed_step or self._owned_reset_pending or self._vector_steps:
            raise RuntimeError("A failed population cannot install boundary state")
        if type(prepared) is not PreparedPopulationRestore or prepared not in self._population_restores or self._step_active:
            raise ValueError("Foreign, consumed or reentrant population restore")
        if self.env.world_phase != "fresh-unbound":
            raise ValueError("Bound component replacement requires the genuine outer stable-owner installation protocol")
        revision, runtime, q, target, optimizer, scheduler, replay, ledger, progress, correlation, cadence = self._population_restores[
            prepared
        ]
        if revision != self._checkpoint_revision:
            raise ValueError("Stale population restore")
        # Preallocate all post-child publication state before the final runtime/BANK check.
        empty_steps: dict[PreparedVectorStep, _VectorStep] = {}
        empty_restores: dict[PreparedPopulationRestore, Any] = {}
        next_revision = revision + 1
        self._preparing_checkpoint, self._step_active = correlation, True
        try:
            self.exploration.install_restore(prepared=runtime)
            self.q_network, self.target_network, self.optimizer, self.scheduler = q, target, optimizer, scheduler
            self.replay_buffer = replay
            self.total_steps, self._clock_ledger = ledger.vector_ticks, ledger
            self.training_step_counter = ledger.optimizer_updates
            self._vector_step_progress, self._parent_cadence = progress, cadence
            self._vector_steps, self._population_restores = empty_steps, empty_restores
            self._failed_step, self._clock_ledger_restore_unavailable = False, False
            self._vector_stage, self._returned_step, self._service_receipts = None, None, ()
            self._initial_decision, self._prior_reading, self._initial_reset, self._selection_frame = None, None, None, None
            self._checkpoint_revision, self._last_beta_tick = next_revision, ledger.vector_ticks
            self._bound_replay, self._replay_was_loaded = replay, True
            self._constructor_replay, self._constructor_replay_state, self._last_readiness = None, None, None
        finally:
            self._preparing_checkpoint, self._step_active = None, False

    def validate_checkpoint_state(self, checkpoint: Mapping[str, object]) -> None:
        """Structure/native-child INITIAL validation without publishing any child."""
        self.prepare_checkpoint_state(checkpoint, mode="initial", parent_restore=None, validate_parent_restore=None, initialization=None)

    def load_checkpoint_state(self, checkpoint: Mapping[str, object]) -> None:
        """Install genuine current INITIAL; other boundaries use explicit prepared custody."""
        prepared = self.prepare_checkpoint_state(
            checkpoint, mode="initial", parent_restore=None, validate_parent_restore=None, initialization=None
        )
        self.install_checkpoint_state(prepared=prepared)

    # ------------------------------------------------------------------ #
    # Cross-universe token-net load (token-obs unit 3 Task 9)
    # ------------------------------------------------------------------ #
    def load_token_network_cross_universe(self, source_q_network_state: dict[str, torch.Tensor]) -> TokenRosterReport:
        """Current transfer awaits genuine same-BANK/native boundary reset coordination."""
        if not self.is_token_native:
            raise ValueError("Cross-universe transfer requires a token-native architecture")
        raise RuntimeError("Cross-universe transfer requires the current same-BANK novelty-reset owner protocol")
