"""Adversarial curriculum that auto-tunes difficulty based on performance.

Tracks per-agent metrics (survival, learning, entropy) and adapts stage
through 5 progressive difficulty levels culminating in sparse rewards.
"""

import math
from collections.abc import Sequence
from copy import deepcopy
from typing import Any, get_args

import torch
import yaml
from pydantic import BaseModel

from townlet.curriculum.base import CurriculumManager
from townlet.training.episode import CompletionReason, LaneOutcome
from townlet.training.state import BatchedAgentState, CurriculumDecision


class StageConfig(BaseModel):
    """Configuration for a single curriculum stage."""

    stage: int
    active_meters: list[str]
    depletion_multiplier: float
    reward_mode: str  # 'shaped' or 'sparse'
    description: str


# Stage progression: 5 stages from easy shaped to full sparse
STAGE_CONFIGS = [
    StageConfig(
        stage=1,
        active_meters=["energy", "hygiene"],
        depletion_multiplier=0.2,
        reward_mode="shaped",
        description="Stage 1: Basic needs (energy, hygiene) at 20% depletion",
    ),
    StageConfig(
        stage=2,
        active_meters=["energy", "hygiene", "satiation"],
        depletion_multiplier=0.5,
        reward_mode="shaped",
        description="Stage 2: Add hunger at 50% depletion",
    ),
    StageConfig(
        stage=3,
        active_meters=["energy", "hygiene", "satiation", "money"],
        depletion_multiplier=0.8,
        reward_mode="shaped",
        description="Stage 3: Add money management at 80% depletion",
    ),
    StageConfig(
        stage=4,
        active_meters=["energy", "hygiene", "satiation", "money", "mood", "social"],
        depletion_multiplier=1.0,
        reward_mode="shaped",
        description="Stage 4: All meters at full depletion",
    ),
    StageConfig(
        stage=5,
        active_meters=["energy", "hygiene", "satiation", "money", "mood", "social"],
        depletion_multiplier=1.0,
        reward_mode="sparse",
        description="Stage 5: SPARSE REWARDS - Graduation!",
    ),
]


class PerformanceTracker:
    """Tracks per-agent performance metrics for curriculum decisions."""

    def __init__(self, num_agents: int, device: torch.device):
        self.num_agents = num_agents
        self.device = device
        self.completion_mode = False

        # Performance metrics (per agent)
        self.episode_rewards = torch.zeros(num_agents, device=device)
        self.episode_steps = torch.zeros(num_agents, device=device)
        self.prev_avg_reward = torch.zeros(num_agents, device=device)
        self.last_survival_rate = torch.zeros(num_agents, device=device)
        self.completed_progress = torch.zeros(num_agents, device=device)

        # Stage tracking
        self.agent_stages = torch.ones(num_agents, dtype=torch.long, device=device)
        self.steps_at_stage = torch.zeros(num_agents, device=device)
        self.episodes_at_stage = torch.zeros(num_agents, dtype=torch.long, device=device)

    def update_step(self, rewards: torch.Tensor, dones: torch.Tensor):
        """Update metrics after environment step.

        Note: rewards here are actually survival_steps, not rewards.
        This is called from Population.update_curriculum_tracker which passes step counts.
        """
        if self.completion_mode:
            return  # Completion owns metrics/dwell; this legacy clock is inactive.
        self.episode_rewards += rewards
        self.episode_steps += 1.0
        self.steps_at_stage += 1.0

        # P1.3: Update baseline BEFORE resetting (capture completed episode reward)
        # This ensures prev_avg_reward reflects the most recent episode performance
        current_avg = self.episode_rewards / torch.clamp(self.episode_steps, min=1.0)
        self.prev_avg_reward = torch.where(dones, current_avg, self.prev_avg_reward)

        # Capture survival rate before reset (rewards are actually step counts)
        self.last_survival_rate = torch.where(dones, rewards / 100.0, self.last_survival_rate)

        # Increment episode counter when episodes complete
        self.episodes_at_stage += dones.long()

        # Reset completed episodes
        self.episode_rewards = torch.where(dones, 0.0, self.episode_rewards)
        self.episode_steps = torch.where(dones, 0.0, self.episode_steps)

    def get_survival_rate(self, max_steps: int) -> torch.Tensor:
        """Completed fractions in completion mode; in-flight fractions in legacy mode."""
        if self.completion_mode:
            return self.last_survival_rate
        return self.episode_steps / max_steps

    def get_learning_progress(self) -> torch.Tensor:
        """Completed fraction delta, or legacy in-flight average reward delta."""
        if self.completion_mode:
            return self.completed_progress
        current_avg = self.episode_rewards / torch.clamp(self.episode_steps, min=1.0)
        progress = current_avg - self.prev_avg_reward
        return progress

    def update_baseline(self):
        """Update reward baseline for learning progress calculation."""
        if self.completion_mode:
            return  # Completion owns the fraction baseline, not this legacy hook.
        current_avg = self.episode_rewards / torch.clamp(self.episode_steps, min=1.0)
        self.prev_avg_reward = current_avg


class AdversarialCurriculum(CurriculumManager):
    """Auto-tuning curriculum based on survival, learning, and entropy.

    Advances agents through 5 stages when they demonstrate:
    - High survival rate (>70%)
    - Positive learning progress
    - Low entropy (<0.5) - policy convergence

    Retreats agents when they struggle:
    - Low survival rate (<30%)
    - Negative learning progress
    """

    def __init__(
        self,
        max_steps_per_episode: int = 500,
        survival_advance_threshold: float = 0.7,
        survival_retreat_threshold: float = 0.3,
        entropy_gate: float = 0.5,
        min_steps_at_stage: int = 1000,
        device: torch.device = torch.device("cpu"),
    ):
        self.max_steps_per_episode = max_steps_per_episode
        self.survival_advance_threshold = survival_advance_threshold
        self.survival_retreat_threshold = survival_retreat_threshold
        self.entropy_gate = entropy_gate
        self.min_steps_at_stage = min_steps_at_stage
        self.device = device

        self.tracker: PerformanceTracker | None = None  # Set when population initialized
        self.transition_events: list[dict[str, Any]] = []

        # Optional difficulty configuration (v2.1 training.yaml – curriculum.adversarial)
        # These parameters control how the internal 1–5 stage index is mapped to an
        # external difficulty_level ∈ [min_difficulty, max_difficulty]. They do NOT
        # change stage advancement/retreat thresholds, which remain governed by
        # survival/learning/entropy metrics.
        self.difficulty_metric: str | None = None
        self.difficulty_adaptation_rate: float | None = None
        self.difficulty_min: float | None = None
        self.difficulty_max: float | None = None
        self.commit_mode = "legacy_step"
        self.difficulty_mode = "stage_band"
        self._seen_completions: set[tuple[int, int]] = set()
        self._completed: list[dict[str, Any]] = []
        self._difficulty: list[float] = []

    def configure_from_training(self, config: Any) -> None:
        """Configure curriculum thresholds and difficulty mapping from TrainingV2Config.

        Args:
            config: AdversarialCurriculumConfig-like object with attributes:
                - difficulty_metric
                - adaptation_rate
                - min_difficulty
                - max_difficulty
                - survival_advance_threshold
                - survival_retreat_threshold
                - entropy_gate
                - min_steps_at_stage
                - commit_mode: legacy_step (default) or completion
                - difficulty_mode: stage_band (default) or rate_limited
                  (adaptation_rate is difficulty change per eligible transition)
        """
        commitment = getattr(config, "commit_mode", self.commit_mode)
        difficulty = getattr(config, "difficulty_mode", self.difficulty_mode)
        low, high = getattr(config, "min_difficulty", 0.0), getattr(config, "max_difficulty", 1.0)
        rate = getattr(config, "adaptation_rate", None)
        if commitment not in ("legacy_step", "completion") or difficulty not in ("stage_band", "rate_limited"):
            raise ValueError("Unknown curriculum commitment/difficulty mode")
        if difficulty == "rate_limited" and commitment != "completion":
            raise ValueError("rate_limited requires the completion transition clock")
        if (
            any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (low, high))
            or not 0 <= low <= high <= 1
        ):
            raise ValueError("Difficulty bounds must be finite and ordered within [0, 1]")
        if rate is not None and (isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate < 0):
            raise ValueError("adaptation_rate must be finite and nonnegative")
        if difficulty == "rate_limited" and rate is None:
            raise ValueError("rate_limited requires adaptation_rate")
        if self.tracker is not None and (
            self.commit_mode == "completion" or commitment != self.commit_mode or difficulty != self.difficulty_mode
        ):
            raise RuntimeError("Select curriculum modes before initialize_population")
        self.commit_mode, self.difficulty_mode = commitment, difficulty
        # Difficulty mapping configuration (v2.1)
        self.difficulty_metric = getattr(config, "difficulty_metric", None)
        self.difficulty_adaptation_rate = getattr(config, "adaptation_rate", None)
        self.difficulty_min = low
        self.difficulty_max = high

        # Thresholds: override constructor defaults with config values when provided.
        self.survival_advance_threshold = getattr(config, "survival_advance_threshold", self.survival_advance_threshold)
        self.survival_retreat_threshold = getattr(config, "survival_retreat_threshold", self.survival_retreat_threshold)
        self.entropy_gate = getattr(config, "entropy_gate", self.entropy_gate)
        self.min_steps_at_stage = getattr(config, "min_steps_at_stage", self.min_steps_at_stage)

    @classmethod
    def from_yaml(cls, config_path: str) -> "AdversarialCurriculum":
        """Load curriculum from YAML config file.

        Args:
            config_path: Path to YAML config file

        Returns:
            Configured AdversarialCurriculum instance
        """
        with open(config_path) as f:
            config = yaml.safe_load(f)

        curriculum_config = config.get("curriculum", {})

        # Extract device config
        device_str = curriculum_config.get("device", "cpu")
        device = torch.device(device_str)

        return cls(
            max_steps_per_episode=curriculum_config.get("max_steps_per_episode", 500),
            survival_advance_threshold=curriculum_config.get("survival_advance_threshold", 0.7),
            survival_retreat_threshold=curriculum_config.get("survival_retreat_threshold", 0.3),
            entropy_gate=curriculum_config.get("entropy_gate", 0.5),
            min_steps_at_stage=curriculum_config.get("min_steps_at_stage", 1000),
            device=device,
        )

    def initialize_population(self, num_agents: int):
        """Initialize performance tracking for population."""
        self.tracker = PerformanceTracker(num_agents, self.device)
        self.tracker.completion_mode = self.commit_mode == "completion"
        self._seen_completions.clear()
        self._completed = [{} for _ in range(num_agents)]
        self._difficulty = [self.difficulty_min if self.difficulty_min is not None else 0.0] * num_agents
        self.transition_events.clear()

    def commit_episode_outcomes(self, outcomes: Sequence[LaneOutcome]) -> None:
        """Commit once per (batch episode, lane), using eligible lane transitions.

        Legacy step mode keeps its original metrics and does not accept a second
        clock. Configure completion before population initialization to opt in.
        """
        tracker = self.tracker
        if tracker is None or self.commit_mode != "completion":
            raise RuntimeError("Initialize a completion-mode population before committing")
        for event in outcomes:
            if not isinstance(event, LaneOutcome):
                raise ValueError("Expected LaneOutcome")
            lane, steps = event.outcome.agent_idx, event.outcome.survival_time
            if (
                type(lane) is not int
                or not 0 <= lane < tracker.num_agents
                or type(steps) is not int
                or not 0 < steps <= event.planned_horizon
            ):
                raise ValueError("Completion lane/transitions outside declared population/horizon")
            if event.outcome.reason not in get_args(CompletionReason):
                raise ValueError("Unknown completion reason")
        for event in outcomes:
            lane, steps = event.outcome.agent_idx, event.outcome.survival_time
            identity = (event.batch_episode, lane)
            if identity in self._seen_completions:
                continue
            fraction = steps / event.planned_horizon
            progress = fraction - self._completed[lane].get("survival_baseline", 0.0)
            tracker.last_survival_rate[lane] = fraction
            tracker.completed_progress[lane] = progress
            tracker.steps_at_stage[lane] += steps
            tracker.episodes_at_stage[lane] += 1
            self._completed[lane] = {
                "learning_progress": progress,
                "completion_reason": event.outcome.reason,
                "policy_entropy": event.policy_entropy,
                "survival_baseline": fraction,
                **{
                    key: getattr(event, key)
                    for key in ("reward_total", "reward_extrinsic", "reward_intrinsic", "reward_shaping", "world_id", "world_episode_seq")
                },
            }
            stage, dwell = int(tracker.agent_stages[lane].item()), int(tracker.steps_at_stage[lane].item())
            reason = None
            if dwell >= self.min_steps_at_stage:
                if stage > 1 and (fraction < self.survival_retreat_threshold or progress < 0):
                    reason = "retreat"
                elif stage < 5 and fraction > self.survival_advance_threshold and progress > 0 and event.policy_entropy < self.entropy_gate:
                    reason = "advance"
            if reason is not None:
                tracker.agent_stages[lane] += 1 if reason == "advance" else -1
                tracker.steps_at_stage[lane] = 0
                tracker.episodes_at_stage[lane] = 0
                self._record_transition_event(
                    agent_id=None,
                    from_stage=stage,
                    to_stage=int(tracker.agent_stages[lane].item()),
                    reason=reason,
                    survival_rate=fraction,
                    learning_progress=progress,
                    entropy=event.policy_entropy,
                    steps_at_stage=dwell,
                )
                self.transition_events[-1].update(
                    agent_idx=lane, world_id=event.world_id, world_episode_seq=event.world_episode_seq, batch_episode=event.batch_episode
                )
            tracker.prev_avg_reward[lane] = fraction
            if self.difficulty_mode == "rate_limited":
                low, high = self.difficulty_min, self.difficulty_max
                target = low + (int(tracker.agent_stages[lane].item()) - 1) / 4 * (high - low)
                budget = self.difficulty_adaptation_rate * steps
                self._difficulty[lane] = min(
                    high, max(low, self._difficulty[lane] + max(-budget, min(budget, target - self._difficulty[lane])))
                )
            self._seen_completions.add(identity)

    def _get_active_meters(self, stage: int) -> list[str]:
        """Get active meters for stage."""
        return STAGE_CONFIGS[stage - 1].active_meters

    def _get_depletion_multiplier(self, stage: int) -> float:
        """Get depletion multiplier for stage."""
        return STAGE_CONFIGS[stage - 1].depletion_multiplier

    def _get_reward_mode(self, stage: int) -> str:
        """Get reward mode for stage."""
        return STAGE_CONFIGS[stage - 1].reward_mode

    def _should_advance(self, agent_idx: int, entropy: float) -> bool:
        """Check if agent should advance to next stage."""
        tracker = self.tracker
        if tracker is None:
            raise RuntimeError("Performance tracker not initialized. Call initialize_population first.")

        # Bounds checking
        if not (0 <= agent_idx < tracker.num_agents):
            raise ValueError(f"Invalid agent_idx: {agent_idx}, must be in range [0, {tracker.num_agents})")

        if tracker.agent_stages[agent_idx] >= 5:
            return False  # Already at max stage

        # Check minimum steps at stage
        if tracker.steps_at_stage[agent_idx] < self.min_steps_at_stage:
            return False

        # Calculate metrics
        survival_rate = float(tracker.get_survival_rate(self.max_steps_per_episode)[agent_idx].item())
        learning_progress = float(tracker.get_learning_progress()[agent_idx].item())

        # Multi-signal decision
        high_survival = survival_rate > self.survival_advance_threshold
        positive_learning = learning_progress > 0
        converged = entropy < self.entropy_gate

        return high_survival and positive_learning and converged

    def _should_retreat(self, agent_idx: int) -> bool:
        """Check if agent should retreat to previous stage."""
        tracker = self.tracker
        if tracker is None:
            raise RuntimeError("Performance tracker not initialized. Call initialize_population first.")

        # Bounds checking
        if not (0 <= agent_idx < tracker.num_agents):
            raise ValueError(f"Invalid agent_idx: {agent_idx}, must be in range [0, {tracker.num_agents})")

        if tracker.agent_stages[agent_idx] <= 1:
            return False  # Already at minimum stage

        # Check minimum steps at stage
        if tracker.steps_at_stage[agent_idx] < self.min_steps_at_stage:
            return False

        # Calculate metrics
        survival_rate = float(tracker.get_survival_rate(self.max_steps_per_episode)[agent_idx].item())
        learning_progress = float(tracker.get_learning_progress()[agent_idx].item())

        # Retreat conditions
        low_survival = survival_rate < self.survival_retreat_threshold
        negative_learning = learning_progress < 0

        return low_survival or negative_learning

    def get_batch_decisions_with_qvalues(
        self,
        agent_states: BatchedAgentState,
        agent_ids: list[str],
        q_values: torch.Tensor,
    ) -> list[CurriculumDecision]:
        """Generate curriculum decisions with Q-values for entropy calculation.

        This is the main entry point when called from VectorizedPopulation.
        """
        tracker = self.tracker
        if tracker is None:
            raise RuntimeError("Must call initialize_population before get_batch_decisions")

        # Calculate entropy from Q-values
        entropies = self._calculate_action_entropy(q_values)

        survival_rates = tracker.get_survival_rate(self.max_steps_per_episode)
        learning_progress = tracker.get_learning_progress()

        decisions = []
        for i, agent_id in enumerate(agent_ids):
            from_stage = int(tracker.agent_stages[i].item())
            steps_before = int(tracker.steps_at_stage[i].item())
            entropy_value = entropies[i].item()
            transition_reason: str | None = None

            # Check for retreat first (takes priority)
            if self.commit_mode == "legacy_step" and self._should_retreat(i):
                tracker.agent_stages[i] -= 1
                tracker.steps_at_stage[i] = 0
                tracker.episodes_at_stage[i] = 0
                # Update baseline for retreating agent only
                current_avg_i = tracker.episode_rewards[i] / torch.clamp(tracker.episode_steps[i], min=1.0)
                tracker.prev_avg_reward[i] = current_avg_i
                transition_reason = "retreat"
            # Then check for advancement
            elif self.commit_mode == "legacy_step" and self._should_advance(i, entropies[i].item()):
                tracker.agent_stages[i] += 1
                tracker.steps_at_stage[i] = 0
                tracker.episodes_at_stage[i] = 0
                # Update baseline for advancing agent only (not all agents)
                current_avg_i = tracker.episode_rewards[i] / torch.clamp(tracker.episode_steps[i], min=1.0)
                tracker.prev_avg_reward[i] = current_avg_i
                transition_reason = "advance"

            # Get current stage
            stage = int(tracker.agent_stages[i].item())
            config = STAGE_CONFIGS[stage - 1]

            if transition_reason is not None:
                self._record_transition_event(
                    agent_id=agent_id,
                    from_stage=from_stage,
                    to_stage=stage,
                    reason=transition_reason,
                    survival_rate=survival_rates[i].item(),
                    learning_progress=learning_progress[i].item(),
                    entropy=entropy_value,
                    steps_at_stage=steps_before,
                )

            # Normalize stage (1-5) to difficulty_level (0.0-1.0)
            # Base mapping: Stage 1 -> 0.0 (easiest), Stage 5 -> 1.0 (hardest sparse rewards).
            base_difficulty = (stage - 1) / 4.0

            # If v2.1 adversarial config provided, map base_difficulty into the
            # configured [min_difficulty, max_difficulty] range. This keeps the
            # underlying stage logic unchanged while allowing operators to
            # express difficulty bands declaratively.
            low = self.difficulty_min if self.difficulty_min is not None else 0.0
            high = self.difficulty_max if self.difficulty_max is not None else 1.0
            if high >= low:
                difficulty_level = low + base_difficulty * (high - low)
            else:
                difficulty_level = base_difficulty
            if self.difficulty_mode == "rate_limited":
                difficulty_level = self._difficulty[i]

            decision = CurriculumDecision(
                difficulty_level=difficulty_level,
                active_meters=config.active_meters,
                depletion_multiplier=config.depletion_multiplier,
                reward_mode=config.reward_mode,
                reason=f"{config.description} (agent {agent_id})",
            )
            decisions.append(decision)

        # NOTE: Per-agent step counting should be handled by PerformanceTracker.update_step()
        # which is called after each environment step. Removed global increment that was
        # incorrectly updating all agents simultaneously.

        return decisions

    def _record_transition_event(
        self,
        *,
        agent_id: str | None,
        from_stage: int,
        to_stage: int,
        reason: str,
        survival_rate: float,
        learning_progress: float,
        entropy: float,
        steps_at_stage: int,
    ) -> None:
        """Append structured telemetry for stage transitions."""
        self.transition_events.append(
            {
                "agent_id": agent_id,
                "from_stage": from_stage,
                "to_stage": to_stage,
                "reason": reason,
                "survival_rate": survival_rate,
                "learning_progress": learning_progress,
                "entropy": entropy,
                "steps_at_stage": steps_at_stage,
            }
        )

    def get_batch_decisions(
        self,
        agent_states: BatchedAgentState,
        agent_ids: list[str],
    ) -> list[CurriculumDecision]:
        """Generate curriculum decisions without Q-values (for testing).

        Uses zero entropy (assumes converged policy).
        """
        # Create dummy Q-values with peaked distribution (low entropy)
        num_agents = len(agent_ids)
        q_values = torch.zeros(num_agents, 5, device=self.device)
        q_values[:, 0] = 10.0  # Make action 0 dominant

        return self.get_batch_decisions_with_qvalues(agent_states, agent_ids, q_values)

    def _calculate_action_entropy(self, q_values: torch.Tensor) -> torch.Tensor:
        """Calculate action distribution entropy from Q-values.

        Higher entropy = more uniform distribution (exploring)
        Lower entropy = peaked distribution (converged policy)

        Args:
            q_values: [batch_size, num_actions] Q-values

        Returns:
            [batch_size] entropy values (0 = deterministic, ~1.79 = uniform for 6 actions)
        """
        # Convert Q-values to probabilities (softmax with temperature=1)
        probs = torch.softmax(q_values, dim=-1)

        # Calculate entropy: -sum(p * log(p))
        log_probs = torch.log(probs + 1e-10)  # Add epsilon for numerical stability
        entropy = -torch.sum(probs * log_probs, dim=-1)

        # Normalize to [0, 1] range (max entropy for 6 actions = log(6) ≈ 1.792)
        num_actions = torch.tensor(q_values.shape[-1], dtype=torch.float32, device=q_values.device)
        normalized_entropy = entropy / torch.log(num_actions)

        return normalized_entropy

    # All tensor fields PerformanceTracker carries; the checkpoint schema is
    # the union of these keys and load_state will not tolerate any missing.
    _TRACKER_FIELDS: tuple[str, ...] = (
        "agent_stages",
        "steps_at_stage",
        "episodes_at_stage",
        "episode_rewards",
        "episode_steps",
        "prev_avg_reward",
        "last_survival_rate",
    )

    def checkpoint_state(self) -> dict[str, Any]:
        """Return serializable state for checkpoint saving.

        Every tensor in :class:`PerformanceTracker` must round-trip: telemetry
        and stage-progression counters (``episodes_at_stage``,
        ``last_survival_rate``) used to silently reset on resume, hiding
        progress and confusing the recorder. Returns an empty dict only when
        the population has not been initialised yet.
        """
        if self.tracker is None:
            return {}

        state = {field: getattr(self.tracker, field).cpu().clone() for field in self._TRACKER_FIELDS}
        if self.commit_mode == "completion":
            state["completion"] = {
                "version": 1,
                "config": self._completion_config(),
                "seen": sorted(self._seen_completions),
                "metrics": deepcopy(self._completed),
                "difficulty": self._difficulty.copy(),
            }
        return state

    def _completion_config(self) -> dict[str, Any]:
        """Meaning-bearing configuration must match on completion-mode resume."""
        return {
            key: getattr(self, key)
            for key in (
                "commit_mode",
                "difficulty_mode",
                "difficulty_adaptation_rate",
                "difficulty_min",
                "difficulty_max",
                "survival_advance_threshold",
                "survival_retreat_threshold",
                "entropy_gate",
                "min_steps_at_stage",
            )
        }

    def load_state(self, state: dict[str, Any]) -> None:
        """Restore curriculum manager from checkpoint.

        The exact schema and live-population shape are validated before mutation.
        """
        self.validate_checkpoint_state(state)
        assert self.tracker is not None
        for field in self._TRACKER_FIELDS:
            tensor = state[field]
            setattr(self.tracker, field, tensor.to(self.device).clone())
        if self.commit_mode == "completion":
            completed = state["completion"]
            self._seen_completions = set(completed["seen"])
            self._completed = deepcopy(completed["metrics"])
            self._difficulty = completed["difficulty"].copy()
            self.tracker.completed_progress = torch.tensor(
                [row.get("learning_progress", 0.0) for row in self._completed], device=self.device
            )

    def validate_checkpoint_state(self, state: dict[str, Any]) -> None:
        """Validate exact tracker state without mutating the live curriculum."""
        if self.tracker is None:
            raise RuntimeError("Must initialize_population before validating state")
        if not isinstance(state, dict):
            raise ValueError(f"Adversarial curriculum checkpoint must be a dictionary; got {type(state).__name__}.")

        expected_keys = set(self._TRACKER_FIELDS)
        if self.commit_mode == "completion":
            expected_keys.add("completion")
        state_keys = set(state)
        if state_keys != expected_keys:
            missing = sorted(expected_keys - state_keys)
            unknown = sorted(state_keys - expected_keys)
            raise ValueError(f"Adversarial curriculum checkpoint key set mismatch: missing={missing}, unknown={unknown}.")

        num_agents = self.tracker.num_agents
        for field in self._TRACKER_FIELDS:
            tensor = state[field]
            if not isinstance(tensor, torch.Tensor):
                raise ValueError(f"Adversarial curriculum checkpoint {field} must be a tensor; got {type(tensor).__name__}.")
            current = getattr(self.tracker, field)
            if tensor.shape != (num_agents,):
                raise ValueError(
                    f"Checkpoint curriculum tracker field {field!r} has shape "
                    f"{tuple(tensor.shape)} but current tracker num_agents={num_agents}. "
                    "Resuming into a differently-sized population is not supported."
                )
            if tensor.dtype != current.dtype:
                raise ValueError(
                    f"Adversarial curriculum checkpoint {field} dtype mismatch: checkpoint={tensor.dtype}, current={current.dtype}."
                )
            if tensor.is_floating_point() and not torch.isfinite(tensor).all().item():
                raise ValueError(f"Adversarial curriculum checkpoint {field} must contain only finite values.")
        if self.commit_mode == "completion":
            self._validate_completed_state(state["completion"])

    def _validate_completed_state(self, completed: Any) -> None:
        if not isinstance(completed, dict) or set(completed) != {"version", "config", "seen", "metrics", "difficulty"}:
            raise ValueError("Invalid completion checkpoint envelope")
        if type(completed["version"]) is not int or completed["version"] != 1 or completed["config"] != self._completion_config():
            raise ValueError("Completion checkpoint version/configuration mismatch")
        seen, metrics, difficulty = (completed[k] for k in ("seen", "metrics", "difficulty"))
        count = self.tracker.num_agents
        if not isinstance(seen, list) or any(
            not isinstance(pair, tuple)
            or len(pair) != 2
            or type(pair[0]) is not int
            or pair[0] < 0
            or type(pair[1]) is not int
            or not 0 <= pair[1] < count
            for pair in seen
        ):
            raise ValueError("Invalid completion event identities")
        if len(set(seen)) != len(seen):
            raise ValueError("Duplicate completion identities in checkpoint")
        if not isinstance(metrics, list) or len(metrics) != count or not isinstance(difficulty, list) or len(difficulty) != count:
            raise ValueError("Completion checkpoint population mismatch")
        keys = {
            "learning_progress",
            "completion_reason",
            "policy_entropy",
            "survival_baseline",
            "reward_total",
            "reward_extrinsic",
            "reward_intrinsic",
            "reward_shaping",
            "world_id",
            "world_episode_seq",
        }
        for lane, (row, value) in enumerate(zip(metrics, difficulty, strict=True)):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not (self.difficulty_min if self.difficulty_min is not None else 0.0)
                <= value
                <= (self.difficulty_max if self.difficulty_max is not None else 1.0)
            ):
                raise ValueError("Invalid checkpoint difficulty")
            if not isinstance(row, dict) or bool(row) != any(pair[1] == lane for pair in seen) or (row and set(row) != keys):
                raise ValueError("Missing or invalid completed metrics")
            if not row:
                continue
            if (
                row["completion_reason"] not in get_args(CompletionReason)
                or not isinstance(row["world_id"], str)
                or not row["world_id"].strip()
                or type(row["world_episode_seq"]) is not int
                or row["world_episode_seq"] < 0
            ):
                raise ValueError("Invalid completed world identity/reason")
            if (
                any(
                    isinstance(row[k], bool) or not isinstance(row[k], (int, float)) or not math.isfinite(row[k])
                    for k in keys - {"completion_reason", "world_id", "world_episode_seq"}
                )
                or not 0 <= row["survival_baseline"] <= 1
            ):
                raise ValueError("Invalid completed numeric metrics")

    def get_stage_info(self, agent_idx: int = 0) -> dict:
        """Get detailed stage information for an agent.

        Useful for recording criteria that need to predict stage transitions.

        Args:
            agent_idx: Agent index to query

        Returns:
            {
                "current_stage": int,
                "episodes_at_stage": int,
                "survival_rate": float (0-1),
                "likely_transition_soon": bool,
            }
        """
        if self.tracker is None:
            raise RuntimeError("Performance tracker not initialized. Call initialize_population first.")

        if not (0 <= agent_idx < self.tracker.num_agents):
            raise ValueError(f"Invalid agent_idx: {agent_idx}, must be in range [0, {self.tracker.num_agents})")

        current_stage = int(self.tracker.agent_stages[agent_idx].item())
        episodes_at_stage = int(self.tracker.episodes_at_stage[agent_idx].item())

        # Get survival rate from last completed episode
        survival_rate = float(self.tracker.last_survival_rate[agent_idx].item())

        # Predict if transition is likely soon
        # Heuristic: high survival + enough steps at stage + not at max stage
        steps_at_stage = float(self.tracker.steps_at_stage[agent_idx].item())
        likely_transition = (
            current_stage < 5  # Not at max stage
            and steps_at_stage >= self.min_steps_at_stage  # Enough steps at this stage
            and survival_rate >= self.survival_advance_threshold  # High survival
        )

        return {
            "current_stage": current_stage,
            "episodes_at_stage": episodes_at_stage,
            "survival_rate": survival_rate,
            "likely_transition_soon": likely_transition,
            "commit_mode": self.commit_mode,
            "difficulty_mode": self.difficulty_mode,
            "adaptation_rate": self.difficulty_adaptation_rate,
            "adaptation_rate_active": self.difficulty_mode == "rate_limited",
            "adaptation_rate_units": "difficulty_per_eligible_transition" if self.difficulty_mode == "rate_limited" else "inactive",
            "active_meters_status": "unqualified",
            "reward_mode_status": "unqualified",
            "difficulty_calibrated": False,
            **(self._completed[agent_idx] if self.commit_mode == "completion" else {}),
        }
