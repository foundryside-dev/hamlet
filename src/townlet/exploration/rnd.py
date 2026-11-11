"""Random Network Distillation (RND) for intrinsic motivation."""

from __future__ import annotations

import math
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal, TypedDict, cast

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812

from townlet.config.bac_options import RNDOptions
from townlet.exploration.action_selection import epsilon_greedy_action_selection
from townlet.exploration.base import ExplorationStrategy
from townlet.exploration.world_curiosity_state import ServiceClock, WorldRNGState
from townlet.training.state import BatchedAgentState


class AdamRestoreGroup(TypedDict):
    """Inert ordered native names and owned Adam group configuration."""

    parameter_names: list[str]
    options: dict[str, Any]


class AdamRestoreRecipe(TypedDict):
    """Current native construction instruction, never owner authority."""

    version: Literal[1]
    algorithm: Literal["torch.optim.Adam"]
    groups: list[AdamRestoreGroup]


def _named_adam_parameters(modules: tuple[tuple[str, nn.Module], ...]) -> dict[str, nn.Parameter]:
    named: dict[str, nn.Parameter] = {}
    identities: set[int] = set()
    for prefix, module in modules:
        for suffix, parameter in module.named_parameters(remove_duplicate=False):
            name = f"{prefix}.{suffix}"
            if name in named or id(parameter) in identities:
                raise ValueError("Native Adam requires unique model names without Parameter aliases")
            named[name] = parameter
            identities.add(id(parameter))
    if not named:
        raise ValueError("Native Adam requires named model Parameters")
    return named


def _adam_value_equal(left: Any, right: Any) -> bool:
    """Exact option type/value equality under native concrete-device transport."""
    if type(left) is not type(right):
        return False
    if isinstance(left, torch.Tensor):
        return (
            left.layout == right.layout == torch.strided
            and left.device.type in {"cpu", "cuda"}
            and right.device.type in {"cpu", "cuda"}
            and left.shape == right.shape
            and left.dtype == right.dtype
            and torch.equal(left.detach().cpu(), right.detach().cpu())
        )
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_adam_value_equal(value, right[key]) for key, value in left.items())
    if isinstance(left, (tuple, list)):
        return len(left) == len(right) and all(_adam_value_equal(value, other) for value, other in zip(left, right, strict=True))
    return bool(left == right)


def _validate_adam_options(options: Any) -> None:
    required = {"lr", "betas", "eps", "weight_decay", "amsgrad"}
    if type(options) is not dict or not required.issubset(options) or any(type(key) is not str for key in options):
        raise ValueError("Native Adam requires complete inert group options")
    betas = options["betas"]
    if type(betas) not in {tuple, list} or len(betas) != 2:
        raise ValueError("Native Adam betas require a numeric pair")
    for value in (options["lr"], options["eps"], options["weight_decay"], *betas):
        if isinstance(value, torch.Tensor):
            if (
                isinstance(value, nn.Parameter)
                or value.layout != torch.strided
                or value.device.type not in {"cpu", "cuda"}
                or value.ndim != 0
                or not value.is_floating_point()
                or not torch.isfinite(value).item()
            ):
                raise ValueError("Native Adam settings require finite inert floating scalar tensors")
        elif isinstance(value, bool) or not isinstance(value, (int, float, np.floating)) or not math.isfinite(value):
            raise ValueError("Native Adam settings require finite numeric scalars")
    if options["lr"] < 0 or options["eps"] < 0 or options["weight_decay"] < 0 or any(not 0 <= beta < 1 for beta in betas):
        raise ValueError("Native Adam numeric settings outside accepted ranges")
    for key, value in options.items():
        if key in {"lr", "betas", "eps", "weight_decay"}:
            continue
        if key in {"foreach", "fused"} and value is None:
            continue
        if type(value) is not bool:
            raise ValueError("Native Adam additional group settings must be booleans")


def _validate_adam_recipe(named: dict[str, nn.Parameter], recipe: Any, payload: Any) -> AdamRestoreRecipe:
    if (
        type(recipe) is not dict
        or set(recipe) != {"version", "algorithm", "groups"}
        or type(recipe["version"]) is not int
        or recipe["version"] != 1
        or type(recipe["algorithm"]) is not str
        or recipe["algorithm"] != "torch.optim.Adam"
        or type(recipe["groups"]) is not list
        or not recipe["groups"]
    ):
        raise ValueError("Native restore requires the exact current Adam recipe")
    if type(payload) is not dict or set(payload) != {"state", "param_groups"} or type(payload["param_groups"]) is not list:
        raise ValueError("Native Adam optimizer payload fields mismatch")
    if len(recipe["groups"]) != len(payload["param_groups"]):
        raise ValueError("Native Adam recipe/payload group counts disagree")
    names: list[str] = []
    identifiers: list[int] = []
    for group, saved in zip(recipe["groups"], payload["param_groups"], strict=True):
        if type(group) is not dict or set(group) != {"parameter_names", "options"} or type(group["parameter_names"]) is not list:
            raise ValueError("Native Adam recipe group fields mismatch")
        group_names = group["parameter_names"]
        if any(type(name) is not str or name not in named for name in group_names):
            raise ValueError("Native Adam recipe names must identify actual selected model Parameters")
        if type(saved) is not dict or "params" not in saved or type(saved["params"]) is not list:
            raise ValueError("Native Adam payload groups require ordered integer IDs")
        if any(type(identifier) is not int for identifier in saved["params"]) or len(group_names) != len(saved["params"]):
            raise ValueError("Native Adam names/IDs disagree")
        _validate_adam_options(group["options"])
        if not _adam_value_equal(group["options"], {key: value for key, value in saved.items() if key != "params"}):
            raise ValueError("Native Adam recipe options disagree with optimizer payload")
        names.extend(group_names)
        identifiers.extend(saved["params"])
    if len(names) != len(set(names)) or set(names) != set(named) or len(identifiers) != len(set(identifiers)):
        raise ValueError("Native Adam requires complete unique named Parameter and integer ID coverage")
    history = payload["state"]
    if (
        type(history) is not dict
        or any(type(identifier) is not int for identifier in history)
        or (history and set(history) != set(identifiers))
    ):
        raise ValueError("Native Adam requires empty or complete dense history with covered integer IDs")
    return cast(AdamRestoreRecipe, recipe)


def _capture_adam_recipe(named: dict[str, nn.Parameter], optimizer: torch.optim.Optimizer, payload: Any) -> AdamRestoreRecipe:
    if type(optimizer) is not torch.optim.Adam:
        raise ValueError("Native restore supports concrete torch.optim.Adam only")
    names = {id(parameter): name for name, parameter in named.items()}
    groups: list[AdamRestoreGroup] = []
    for group in optimizer.param_groups:
        if any(id(parameter) not in names for parameter in group["params"]):
            raise ValueError("Native Adam contains a foreign Parameter")
        groups.append(
            {
                "parameter_names": [names[id(parameter)] for parameter in group["params"]],
                "options": deepcopy({key: value for key, value in group.items() if key != "params"}),
            }
        )
    recipe: AdamRestoreRecipe = {"version": 1, "algorithm": "torch.optim.Adam", "groups": groups}
    return _validate_adam_recipe(named, recipe, payload)


def _validate_adam_candidate(
    named: dict[str, nn.Parameter], optimizer: torch.optim.Optimizer, recipe: Any, payload: Any, *, exact_options: bool
) -> AdamRestoreRecipe:
    checked = _validate_adam_recipe(named, recipe, payload)
    current_payload = deepcopy(optimizer.state_dict())
    current = _capture_adam_recipe(named, optimizer, current_payload)
    if len(current["groups"]) != len(checked["groups"]):
        raise ValueError("Native Adam candidate group count differs; configure restore explicitly")
    for actual, saved, actual_payload, saved_payload in zip(
        current["groups"], checked["groups"], current_payload["param_groups"], payload["param_groups"], strict=True
    ):
        if actual["parameter_names"] != saved["parameter_names"] or actual_payload["params"] != saved_payload["params"]:
            raise ValueError("Native Adam candidate named association differs; configure restore explicitly")
        if actual["options"].keys() != saved["options"].keys() or (
            exact_options and not _adam_value_equal(actual["options"], saved["options"])
        ):
            raise ValueError("Native Adam candidate group configuration differs; configure restore explicitly")
    return checked


def _adam_from_recipe(named: dict[str, nn.Parameter], recipe: Any, payload: Any) -> torch.optim.Adam:
    checked = _validate_adam_recipe(named, recipe, payload)
    groups = [{**deepcopy(group["options"]), "params": [named[name] for name in group["parameter_names"]]} for group in checked["groups"]]
    # Actual group dictionaries retain accepted inert extra bools. They are not
    # Adam constructor keyword arguments, and defaults are not another authority.
    return torch.optim.Adam(groups)


@dataclass(frozen=True)
class PredictorServiceCounters:
    """Owned primitive snapshot of recorded cumulative work and current occupancy."""

    admitted_rows: int
    consumed_rows: int
    dropped_rows: int
    pending_rows: int
    optimizer_updates: int


@dataclass(frozen=True)
class PredictorServiceReceipt:
    """Per-call row accounting; overflow updates are separate from tick pacing.

    admitted_rows includes explicitly dropped rows, so cumulative admissions equal
    consumed + dropped + pending. No reward normalization is performed by service.
    """

    admitted_rows: int
    consumed_rows: int
    dropped_rows: int
    pending_rows: int
    optimizer_updates: int
    last_loss: float | None
    paced_optimizer_updates: int
    overflow_optimizer_updates: int


@dataclass
class _PreparedRND:
    owner: object
    attributes: dict[str, Any]
    consumed: bool


class RunningMeanStd:
    """Running mean and standard deviation tracker.

    Uses Welford's online algorithm for numerical stability.
    Adapted from OpenAI's RND implementation and CleanRL.
    """

    def __init__(self, epsilon: float = 1e-4):
        """Initialize running statistics.

        Args:
            epsilon: Small constant to avoid division by zero
        """
        self.mean = 0.0
        self.var = 1.0
        self.count = epsilon

    def update(self, x: np.ndarray) -> None:
        """Update running statistics with new batch.

        Args:
            x: Array of shape [batch_size] or [batch_size, ...]
        """
        batch_mean = np.mean(x)
        batch_var = np.var(x)
        batch_count = int(x.size)

        self.update_from_moments(batch_mean, batch_var, batch_count)

    def update_from_moments(self, batch_mean: float, batch_var: float, batch_count: int) -> None:
        """Update from pre-computed batch statistics.

        Args:
            batch_mean: Mean of batch
            batch_var: Variance of batch
            batch_count: Number of samples in batch
        """
        delta = batch_mean - self.mean
        total_count = self.count + batch_count

        new_mean = self.mean + delta * batch_count / total_count
        m_a = self.var * self.count
        m_b = batch_var * batch_count
        m2 = m_a + m_b + delta**2 * self.count * batch_count / total_count
        new_var = m2 / total_count

        self.mean = new_mean
        self.var = new_var
        self.count = total_count


class RNDNetwork(nn.Module):
    """3-layer MLP for RND embeddings.

    Architecture: [obs_dim → 256 → 128 → embed_dim]
    Matches SimpleQNetwork architecture for consistency.
    """

    def __init__(self, obs_dim: int = 70, embed_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, embed_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Transform observations to embeddings.

        Args:
            x: [batch, obs_dim] observations

        Returns:
            [batch, embed_dim] embeddings
        """
        # No activity mask: RND consumes the token serialization whole. The mask (and
        # its buffer, and this multiply) died with the fixed-width superset ABI at the
        # unit-3 cut — every token dim is real, and padding is a token's own presence
        # feature, not a dead column to zero.
        return cast(torch.Tensor, self.net(x))


class RNDExploration(ExplorationStrategy):
    """Random Network Distillation for novelty-based intrinsic rewards.

    Uses prediction error as intrinsic reward signal:
    - High error = novel state = high intrinsic reward
    - Low error = familiar state = low intrinsic reward
    """

    def __init__(
        self,
        obs_dim: int = 70,
        embed_dim: int = 128,
        learning_rate: float = 1e-4,
        training_batch_size: int = 128,
        epsilon_start: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        device: torch.device = torch.device("cpu"),
        *,
        rng: WorldRNGState | None,
        service_clock_unit: Literal["vector_tick", "world_eligible_admission"],
    ):
        """Initialize RND with fixed and predictor networks.

        Args:
            obs_dim: Observation dimension
            embed_dim: Embedding dimension
            learning_rate: Learning rate for predictor network
            training_batch_size: Batch size for predictor training
            epsilon_start: Initial epsilon for epsilon-greedy
            epsilon_min: Minimum epsilon
            epsilon_decay: Epsilon decay rate
            device: Device for tensors
        """
        ServiceClock(service_clock_unit, 0)
        if rng is not None and not isinstance(rng, WorldRNGState):
            raise ValueError("RND rng must be an actual world RNG owner or explicit None")
        for name, value in (("obs_dim", obs_dim), ("embed_dim", embed_dim), ("training_batch_size", training_batch_size)):
            if type(value) is not int or value <= 0:
                raise ValueError(f"RND {name} must be a positive integer")
        for scalar_name, scalar_value in (
            ("learning_rate", learning_rate),
            ("epsilon_start", epsilon_start),
            ("epsilon_min", epsilon_min),
            ("epsilon_decay", epsilon_decay),
        ):
            if isinstance(scalar_value, bool) or not isinstance(scalar_value, (int, float)) or not math.isfinite(scalar_value):
                raise ValueError(f"RND {scalar_name} must be finite numeric configuration")
        if learning_rate < 0 or not 0 <= epsilon_min <= epsilon_start <= 1 or not 0 <= epsilon_decay <= 1:
            raise ValueError("RND learning rate/epsilon configuration is invalid")
        device = torch.device(device)
        if device.type not in {"cpu", "cuda"}:
            raise ValueError("RND requires a concrete CPU or CUDA destination")
        self._service_clock_unit = service_clock_unit
        self.obs_dim = obs_dim
        self.embed_dim = embed_dim
        self.training_batch_size = training_batch_size
        self.device = device

        # Epsilon parameters
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

        # Fixed network (random, frozen)
        with rng.activate("target") if rng is not None else nullcontext():
            self.fixed_network = RNDNetwork(obs_dim, embed_dim).to(device)
        for param in self.fixed_network.parameters():
            param.requires_grad = False

        # Predictor network (trained to match fixed)
        with rng.activate("predictor") if rng is not None else nullcontext():
            self.predictor_network = RNDNetwork(obs_dim, embed_dim).to(device)

        # Optimizer for predictor
        self.optimizer = torch.optim.Adam(self.predictor_network.parameters(), lr=learning_rate)

        # Observation buffer for mini-batch training
        self.obs_buffer: list[torch.Tensor] = []
        self.step_counter = 0
        self.service_options: RNDOptions | None = None
        self._admitted_rows = 0
        self._consumed_rows = 0
        self._dropped_rows = 0
        self._optimizer_updates = 0
        self._optimizer_epoch_origin = 0
        self._service_position: int | None
        if service_clock_unit == "world_eligible_admission":
            self._service_position = 0
        else:
            self._service_position = None
        self._ordinary_updates_at_position = 0

        # Running statistics for intrinsic reward normalization
        self.reward_rms = RunningMeanStd()

    @property
    def service_clock_unit(self) -> Literal["vector_tick", "world_eligible_admission"]:
        return self._service_clock_unit

    def _require_shared(self) -> None:
        if self.service_clock_unit != "vector_tick":
            raise ValueError("Private RND learning requires explicit eligible-admission clock")

    def select_actions(
        self,
        q_values: torch.Tensor,
        agent_states: BatchedAgentState,
        action_masks: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Select actions using epsilon-greedy with action masking.

        Args:
            q_values: Q-values for each action [batch, num_actions]
            agent_states: Current state (contains per-agent epsilons)
            action_masks: Optional action validity masks [batch, num_actions] bool

        Returns:
            actions: [batch] selected actions
        """
        return epsilon_greedy_action_selection(
            q_values=q_values,
            epsilons=agent_states.epsilons,
            action_masks=action_masks,
        )

    def compute_intrinsic_rewards(
        self,
        observations: torch.Tensor,  # [batch, obs_dim]
        update_stats: bool = False,
    ) -> torch.Tensor:
        """Compute normalized RND novelty signal (prediction error).

        Args:
            observations: [batch, obs_dim] state observations
            update_stats: If True, update running mean/std statistics (use during training rollouts)

        Returns:
            [batch] normalized intrinsic rewards
        """
        self._validate_observations(observations)
        if type(update_stats) is not bool:
            raise ValueError("RND update_stats requires bool")
        if observations.device != next(self.predictor_network.parameters()).device:
            raise ValueError("RND reward observations must match the provider device")
        if len(observations) == 0:
            return torch.empty(0, device=observations.device, dtype=observations.dtype)
        with torch.no_grad():
            target_features: torch.Tensor = self.fixed_network(observations)
            predicted_features: torch.Tensor = self.predictor_network(observations)
            # MSE per sample (high error = novel = high reward)
            mse_per_sample = ((target_features - predicted_features) ** 2).mean(dim=1)

            if not torch.isfinite(mse_per_sample).all().item():
                raise ValueError("RND produced nonfinite novelty")
            # Optionally update running statistics (only during training rollouts)
            if update_stats:
                mse_numpy = mse_per_sample.cpu().numpy()
                self.reward_rms.update(mse_numpy)

            # Normalize by running standard deviation
            # This brings intrinsic rewards to comparable magnitude with extrinsic rewards
            normalized = mse_per_sample / (np.sqrt(self.reward_rms.var) + 1e-8)

        return cast(torch.Tensor, normalized)

    def update(self, batch: dict[str, torch.Tensor]) -> None:
        """Update predictor network from experience batch.

        Args:
            batch: Experience batch with 'observations' key
        """
        self._require_shared()
        if "observations" not in batch:
            return
        observations = batch["observations"]
        self._validate_observations(observations)
        self._validate_buffer()
        if self.service_options is not None:
            prospective = self.step_counter
            if self._service_position is not None:
                prospective = max(prospective, self._service_position + 1)
            self.admit_and_service(observations, vector_tick=prospective)
            self.step_counter = prospective + 1
            return
        self.obs_buffer.extend(row.detach().clone() for row in observations)
        self._admitted_rows += len(observations)
        self.update_predictor()

    def _validate_buffer(self) -> None:
        for row in self.obs_buffer:
            if not isinstance(row, torch.Tensor) or row.ndim != 1:
                raise ValueError("RND pending observations require owned observation rows")
            self._validate_observations(row.unsqueeze(0))

    def _validate_observations(self, observations: torch.Tensor) -> None:
        if (
            not isinstance(observations, torch.Tensor)
            or observations.layout != torch.strided
            or observations.device.type not in {"cpu", "cuda"}
            or observations.ndim != 2
            or observations.shape[1] != self.obs_dim
            or observations.dtype != next(self.predictor_network.parameters()).dtype
        ):
            raise ValueError("RND observations must be finite floating rows with matching width and dtype")
        for chunk in observations.split(self.training_batch_size):
            if not torch.isfinite(chunk).all().item():
                raise ValueError("RND observations must be finite floating rows with matching width and dtype")

    def _validated_options(self, options: RNDOptions) -> RNDOptions:
        if not isinstance(options, RNDOptions):
            raise ValueError("RND service requires resolved RNDOptions")
        checked = RNDOptions.model_validate(options.model_dump())
        if any(value is None for value in checked.model_dump().values()):
            raise ValueError("RND service requires centrally resolved, explicit options")
        assert checked.max_pending_rows is not None
        if checked.max_pending_rows < self.training_batch_size:
            raise ValueError("RND max_pending_rows must accommodate one training minibatch")
        return checked

    def configure_service(self, options: RNDOptions) -> None:
        """Bind fully resolved policy before service; never choose consumer defaults."""
        checked = self._validated_options(options)
        if self.service_options == checked:
            return
        if self.obs_buffer or self._admitted_rows:
            raise ValueError("configure RND service before admission; live policy changes require explicit transfer")
        self.service_options = checked

    def predictor_service_counters(self) -> PredictorServiceCounters:
        """Observe native recorded counters and occupancy without servicing work.

        External obs_buffer appends affect occupancy immediately; their admissions
        are recorded by the next update_predictor call, even for a partial batch.
        Callers measuring legacy work must start their interval before appending
        and end it after that update. Reading this view never reconciles counters
        or copies pending observations, networks, or optimizer state.
        """
        return PredictorServiceCounters(
            admitted_rows=self._admitted_rows,
            consumed_rows=self._consumed_rows,
            dropped_rows=self._dropped_rows,
            pending_rows=len(self.obs_buffer),
            optimizer_updates=self._optimizer_updates,
        )

    def admit_and_service(self, observations: torch.Tensor, *, vector_tick: int) -> PredictorServiceReceipt:
        """Current shared grouped admission; equal ticks share ordinary budget."""
        self._require_shared()
        return self.admit_and_service_at(observations, clock=ServiceClock("vector_tick", vector_tick))

    def admit_and_service_at(self, observations: torch.Tensor, *, clock: ServiceClock) -> PredictorServiceReceipt:
        """Validate the entire call before servicing explicit shared/private clocks."""
        self._validate_observations(observations)
        self._validate_buffer()
        if self.service_options is None:
            raise ValueError("Configure resolved RND service options before admission")
        options = self._validated_options(self.service_options)
        assert options.max_pending_rows is not None
        if len(self.obs_buffer) > options.max_pending_rows:
            raise ValueError("RND existing buffer exceeds bounded service capacity")
        if type(clock) is not ServiceClock:
            raise ValueError("RND service requires ServiceClock")
        ServiceClock(clock.unit, clock.position)
        if clock.unit != self.service_clock_unit:
            raise ValueError("RND service clock unit differs from selected unit")
        previous = self._service_position
        if clock.unit == "vector_tick":
            if previous is not None and clock.position < previous:
                raise ValueError("RND vector clock must not regress")
            return self._admit_service_rows(observations, clock.position)
        assert previous is not None
        if clock.position != previous + len(observations):
            raise ValueError("RND private clock delta must equal actual eligible admissions")
        receipts = [self._admit_service_rows(row.unsqueeze(0), previous + index + 1) for index, row in enumerate(observations)]
        losses = [receipt.last_loss for receipt in receipts if receipt.last_loss is not None]
        return PredictorServiceReceipt(
            admitted_rows=len(observations),
            consumed_rows=sum(item.consumed_rows for item in receipts),
            dropped_rows=sum(item.dropped_rows for item in receipts),
            pending_rows=len(self.obs_buffer),
            optimizer_updates=sum(item.optimizer_updates for item in receipts),
            last_loss=losses[-1] if losses else None,
            paced_optimizer_updates=sum(item.paced_optimizer_updates for item in receipts),
            overflow_optimizer_updates=sum(item.overflow_optimizer_updates for item in receipts),
        )

    def _admit_service_rows(self, observations: torch.Tensor, position: int) -> PredictorServiceReceipt:
        options = self.service_options
        assert options is not None
        if position != self._service_position:
            self._service_position = position
            self._ordinary_updates_at_position = 0
        capacity = options.max_pending_rows
        budget = options.max_updates_per_tick
        assert capacity is not None and budget is not None
        start_consumed, start_dropped = self._consumed_rows, self._dropped_rows
        paced, overflow = 0, 0
        last_loss: float | None = None
        offset = 0
        while True:
            while len(self.obs_buffer) >= self.training_batch_size:
                if options.service_mode == "paced_fifo" and self._ordinary_updates_at_position >= budget:
                    break
                last_loss = self._update_predictor()
                paced += 1
                self._ordinary_updates_at_position += 1
            if offset == len(observations):
                break
            room = capacity - len(self.obs_buffer)
            if room == 0:
                if options.overflow_policy == "service_before_admit":
                    last_loss = self._update_predictor()
                    overflow += 1
                    continue
                count = min(len(observations) - offset, capacity)
                if options.overflow_policy == "drop_newest":
                    self._admitted_rows += count
                    self._dropped_rows += count
                    offset += count
                    continue
                del self.obs_buffer[:count]
                self._dropped_rows += count
                room = count
            count = min(room, len(observations) - offset)
            self.obs_buffer.extend(row.detach().to(self.device).clone() for row in observations[offset : offset + count])
            self._admitted_rows += count
            offset += count
        return PredictorServiceReceipt(
            admitted_rows=len(observations),
            consumed_rows=self._consumed_rows - start_consumed,
            dropped_rows=self._dropped_rows - start_dropped,
            pending_rows=len(self.obs_buffer),
            optimizer_updates=paced + overflow,
            last_loss=last_loss,
            paced_optimizer_updates=paced,
            overflow_optimizer_updates=overflow,
        )

    def update_predictor(self) -> float:
        """Train predictor network on accumulated observations.

        Called every training_batch_size steps.

        Returns:
            Prediction loss (for logging)
        """
        self._require_shared()
        self._validate_buffer()
        return self._update_predictor()

    def _update_predictor(self) -> float:
        # Direct callers own the public buffer and may admit rows without a tick.
        self._admitted_rows = max(self._admitted_rows, self._consumed_rows + self._dropped_rows + len(self.obs_buffer))
        if len(self.obs_buffer) < self.training_batch_size:
            return 0.0

        # Stack observations into batch
        obs_batch = torch.stack(self.obs_buffer[: self.training_batch_size]).to(self.device)

        # Compute loss
        target = self.fixed_network(obs_batch).detach()
        predicted = self.predictor_network(obs_batch)
        loss = F.mse_loss(predicted, target)

        if not torch.isfinite(loss).item():
            raise ValueError("RND objective is nonfinite")
        # Gradient step
        self.optimizer.zero_grad()
        loss.backward()
        if any(
            parameter.grad is not None and not torch.isfinite(parameter.grad).all().item()
            for parameter in self.predictor_network.parameters()
        ):
            raise ValueError("RND objective produced nonfinite gradients")
        self.optimizer.step()
        del self.obs_buffer[: self.training_batch_size]
        self._consumed_rows += self.training_batch_size
        self._optimizer_updates += 1
        return loss.item()

    def decay_epsilon(self) -> None:
        """Decay epsilon (call once per episode)."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def available_state(self) -> dict[str, Any]:
        """Return serializable state for checkpoint saving.

        Returns:
            Dict with network weights, optimizer state, epsilon, and normalization stats
        """
        return deepcopy(
            {
                "fixed_network": self.fixed_network.state_dict(),
                "predictor_network": self.predictor_network.state_dict(),
                "optimizer": self.optimizer.state_dict(),
                "epsilon": self.epsilon,
                "epsilon_min": self.epsilon_min,
                "epsilon_decay": self.epsilon_decay,
                "obs_dim": self.obs_dim,
                "embed_dim": self.embed_dim,
                # Normalization statistics
                "reward_rms_mean": self.reward_rms.mean,
                "reward_rms_var": self.reward_rms.var,
                "reward_rms_count": self.reward_rms.count,
            }
        )

    def checkpoint_state(self) -> dict[str, Any]:
        """Owned snapshot, including FIFO order and clocks for learned-state resume."""
        if any(parameter.requires_grad or parameter.grad is not None for parameter in self.fixed_network.parameters()):
            raise ValueError("RND target must remain frozen and gradient-free")
        state = self.available_state()
        state["schema"] = "rnd-state-v4"
        state["adam_restore_recipe"] = _capture_adam_recipe(self._named_predictor_parameters(), self.optimizer, state["optimizer"])
        pending = torch.empty((0, self.obs_dim), device=self.device)
        if self.obs_buffer:
            pending = torch.stack(self.obs_buffer).detach().clone()
        admitted = self._admitted_rows
        if self.service_options is None:
            admitted = self._consumed_rows + self._dropped_rows + len(self.obs_buffer)
        options = None
        if self.service_options is not None:
            options = self.service_options.model_dump()
        state["predictor_service"] = {
            "version": 3,
            "training_batch_size": self.training_batch_size,
            "options": options,
            "pending_observations": pending,
            "admitted_rows": admitted,
            "consumed_rows": self._consumed_rows,
            "dropped_rows": self._dropped_rows,
            "optimizer_updates": self._optimizer_updates,
            "optimizer_epoch_origin": self._optimizer_epoch_origin,
            # Capture the trusted live clock, including public manual optimizer
            # steps outside recorded service updates. Restore validates this saved offset.
            "optimizer_step_offset": self._optimizer_step(self.optimizer) - (self._optimizer_updates - self._optimizer_epoch_origin),
            "service_clock_unit": self.service_clock_unit,
            "service_position": self._service_position,
            "ordinary_updates_at_position": self._ordinary_updates_at_position,
            "step_counter": self.step_counter,
        }
        return state

    @staticmethod
    def _finite_tree(value: Any) -> None:
        if isinstance(value, torch.Tensor):
            if not torch.isfinite(value).all().item():
                raise ValueError("RND checkpoint contains nonfinite tensors")
        elif isinstance(value, dict):
            for item in value.values():
                RNDExploration._finite_tree(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                RNDExploration._finite_tree(item)
        elif isinstance(value, (float, np.floating)) and not math.isfinite(value):
            raise ValueError("RND checkpoint contains nonfinite numbers")

    @staticmethod
    def _optimizer_step(optimizer: torch.optim.Optimizer) -> int:
        if not optimizer.state:
            return 0
        return int(next(iter(optimizer.state.values()))["step"].item())

    def _validate_optimizer_groups(self, groups: Any) -> None:
        expected = self.optimizer.state_dict()["param_groups"]
        if not isinstance(groups, list) or len(groups) != len(expected):
            raise ValueError("RND checkpoint optimizer groups mismatch")
        for group, reference in zip(groups, expected, strict=True):
            if not isinstance(group, dict) or set(group) != set(reference):
                raise ValueError("RND checkpoint optimizer group fields mismatch")
            if (
                not isinstance(group["params"], list)
                or any(type(index) is not int for index in group["params"])
                or group["params"] != reference["params"]
            ):
                raise ValueError("RND checkpoint optimizer parameter IDs invalid")
            betas = group["betas"]
            if not isinstance(betas, (tuple, list)) or len(betas) != 2:
                raise ValueError("RND checkpoint optimizer betas invalid")
            for value in (group["lr"], group["eps"], group["weight_decay"], *betas):
                scalar_tensor = isinstance(value, torch.Tensor) and value.ndim == 0 and value.is_floating_point()
                if not scalar_tensor and (isinstance(value, bool) or not isinstance(value, (int, float, np.floating))):
                    raise ValueError("RND checkpoint optimizer settings must be numeric scalars")
            for key, value in group.items():
                if key in {"params", "betas", "lr", "eps", "weight_decay"}:
                    continue
                if key in {"foreach", "fused"} and value is None:
                    continue
                if type(value) is not bool:
                    raise ValueError("RND checkpoint optimizer execution flags must be booleans")

    def _prepare_available_state(self, state: dict[str, Any], recipe: AdamRestoreRecipe) -> tuple[Any, Any, Any]:
        expected_keys = set(self.available_state())
        missing = expected_keys - set(state)
        if missing:
            raise KeyError(f"RND available-state missing fields: {sorted(missing)}")
        if set(state) != expected_keys:
            raise ValueError("RND available-state fields mismatch")
        self._finite_tree(state)
        if (
            type(state["obs_dim"]) is not int
            or type(state["embed_dim"]) is not int
            or state["obs_dim"] != self.obs_dim
            or state["embed_dim"] != self.embed_dim
        ):
            raise ValueError("RND checkpoint network geometry mismatch")
        for key in ("epsilon", "epsilon_min", "epsilon_decay", "reward_rms_mean", "reward_rms_var", "reward_rms_count"):
            if isinstance(state[key], bool) or not isinstance(state[key], (int, float, np.floating)):
                raise ValueError(f"RND checkpoint {key} must be a finite scalar")
        if any(not 0 <= state[key] <= 1 for key in ("epsilon", "epsilon_min", "epsilon_decay")):
            raise ValueError("RND checkpoint epsilon settings outside [0,1]")
        if state["epsilon"] < state["epsilon_min"]:
            raise ValueError("RND checkpoint epsilon is below its floor")
        if state["reward_rms_var"] < 0 or state["reward_rms_count"] <= 0:
            raise ValueError("RND checkpoint normalization variance/count invalid")
        fixed, predictor, optimizer = deepcopy((self.fixed_network, self.predictor_network, self.optimizer))
        _validate_adam_candidate(
            _named_adam_parameters((("predictor_network", predictor),)), optimizer, recipe, state["optimizer"], exact_options=False
        )
        for module, key in ((fixed, "fixed_network"), (predictor, "predictor_network")):
            expected = module.state_dict()
            if set(state[key]) != set(expected):
                raise ValueError("RND checkpoint network fields mismatch")
            for name, tensor in state[key].items():
                if not isinstance(tensor, torch.Tensor) or tensor.shape != expected[name].shape or tensor.dtype != expected[name].dtype:
                    raise ValueError("RND checkpoint network tensor mismatch")
            module.load_state_dict(state[key])
        optimizer_state = state["optimizer"]
        if not isinstance(optimizer_state, dict) or set(optimizer_state) != {"state", "param_groups"}:
            raise ValueError("RND checkpoint optimizer fields mismatch")
        self._validate_optimizer_groups(optimizer_state["param_groups"])
        states = optimizer_state["state"]
        if not isinstance(states, dict) or any(type(identifier) is not int for identifier in states):
            raise ValueError("RND checkpoint optimizer moments require exact integer parameter IDs")
        parameter_ids = [index for group in optimizer_state["param_groups"] for index in group["params"]]
        if len(set(parameter_ids)) != len(parameter_ids) or not set(states).issubset(parameter_ids):
            raise ValueError("RND checkpoint optimizer parameter identity mismatch")
        if states and set(states) != set(parameter_ids):
            raise ValueError("RND dense predictor requires complete Adam history for every parameter")
        # Inspect original transported tensors before Adam can cast moments to
        # parameter dtype, losing invalid dtype/negative-underflow information.
        steps: set[int] = set()
        for group, destination in zip(optimizer_state["param_groups"], optimizer.param_groups, strict=True):
            if group["lr"] < 0 or group["eps"] < 0 or group["weight_decay"] < 0 or any(not 0 <= beta < 1 for beta in group["betas"]):
                raise ValueError("RND checkpoint optimizer settings invalid")
            for identifier, parameter in zip(group["params"], destination["params"], strict=True):
                if identifier not in states:
                    continue
                moments = states[identifier]
                required = {"step", "exp_avg", "exp_avg_sq"}
                if group["amsgrad"]:
                    required.add("max_exp_avg_sq")
                if not isinstance(moments, dict) or set(moments) != required:
                    raise ValueError("RND checkpoint optimizer moment fields mismatch")
                for name, tensor in moments.items():
                    if not isinstance(tensor, torch.Tensor) or tensor.layout != torch.strided or tensor.device.type not in {"cpu", "cuda"}:
                        raise ValueError("RND checkpoint optimizer moments require concrete dense tensors")
                    if not torch.isfinite(tensor).all().item():
                        raise ValueError("RND checkpoint optimizer moments must be finite")
                    if name == "step":
                        if tensor.shape != () or not tensor.is_floating_point() or tensor.item() < 0 or tensor.item() != int(tensor.item()):
                            raise ValueError("RND checkpoint optimizer step invalid")
                        steps.add(int(tensor.item()))
                    elif tensor.shape != parameter.shape or tensor.dtype != parameter.dtype:
                        raise ValueError("RND raw optimizer moment geometry/dtype mismatch")
                    elif name in {"exp_avg_sq", "max_exp_avg_sq"} and (tensor < 0).any().item():
                        raise ValueError("RND raw optimizer squared moments must be nonnegative")
        if len(steps) > 1:
            raise ValueError("RND dense predictor Adam parameter steps must agree")
        optimizer.load_state_dict(deepcopy(optimizer_state))
        self._finite_tree(optimizer.state_dict())
        # Exercise destination execution on disposable copies, including flags
        # whose device/version compatibility is enforced only during Adam.step.
        probe = deepcopy(optimizer)
        for group in probe.param_groups:
            for parameter in group["params"]:
                parameter.grad = torch.zeros_like(parameter)
        try:
            probe.step()
            self._finite_tree(probe.state_dict())
            for group in probe.param_groups:
                for parameter in group["params"]:
                    if not torch.isfinite(parameter).all().item():
                        raise ValueError("RND checkpoint optimizer produces nonfinite destination parameters")
        except (AssertionError, RuntimeError, TypeError, ValueError) as exc:
            raise ValueError("RND checkpoint optimizer cannot execute on this destination") from exc
        return fixed, predictor, optimizer

    def _install_available_state(self, state: dict[str, Any], prepared: tuple[Any, Any, Any]) -> None:
        self.fixed_network, self.predictor_network, self.optimizer = prepared
        self.epsilon, self.epsilon_min, self.epsilon_decay = state["epsilon"], state["epsilon_min"], state["epsilon_decay"]
        self.reward_rms.mean, self.reward_rms.var, self.reward_rms.count = (
            state["reward_rms_mean"],
            state["reward_rms_var"],
            state["reward_rms_count"],
        )

    def validate_state(self, state: dict[str, Any]) -> None:
        """Pure complete current-native validation, with no live installation."""
        self.prepare_state(state)

    def _named_predictor_parameters(self) -> dict[str, nn.Parameter]:
        named = _named_adam_parameters((("predictor_network", self.predictor_network),))
        fixed = {id(parameter) for parameter in self.fixed_network.parameters()}
        if any(id(parameter) in fixed for parameter in named.values()):
            raise ValueError("RND predictor Adam must exclude every fixed-target Parameter")
        return named

    def with_restore_configuration(self, state: dict[str, Any]) -> RNDExploration:
        """Return an independent configured graph before learned-state installation.

        The caller supplies selected factory provenance and source custody. Model
        copying and real Adam construction consume no RNG and never mutate self.
        """
        try:
            owned = deepcopy(state)
            if type(owned) is not dict or owned.keys() != self.checkpoint_state().keys() or owned["schema"] != "rnd-state-v4":
                raise ValueError("RND restore configuration requires complete rnd-state-v4")
            candidate = deepcopy(self)
            candidate.optimizer = _adam_from_recipe(
                candidate._named_predictor_parameters(), owned["adam_restore_recipe"], owned["optimizer"]
            )
            for module in (candidate.fixed_network, candidate.predictor_network):
                for parameter in module.parameters():
                    parameter.grad = None
            candidate.validate_state(owned)
            return candidate
        except (KeyError, TypeError, RuntimeError, AttributeError, OverflowError) as error:
            raise ValueError("RND restore configuration is malformed") from error

    def _prepare_state(self, state: dict[str, Any]) -> tuple[tuple[Any, Any, Any], list[torch.Tensor], dict[str, Any]]:
        if not isinstance(state, dict) or state.keys() != self.checkpoint_state().keys() or state["schema"] != "rnd-state-v4":
            raise ValueError("RND requires complete current rnd-state-v4 checkpoint")
        recipe = _validate_adam_candidate(
            self._named_predictor_parameters(), self.optimizer, state["adam_restore_recipe"], state["optimizer"], exact_options=False
        )
        available = {key: value for key, value in state.items() if key not in {"schema", "predictor_service", "adam_restore_recipe"}}
        prepared = self._prepare_available_state(available, recipe)
        service = state["predictor_service"]
        if not isinstance(service, dict) or set(service) != set(self.checkpoint_state()["predictor_service"]):
            raise ValueError("RND predictor service checkpoint fields mismatch")
        if (
            type(service["version"]) is not int
            or service["version"] != 3
            or type(service["training_batch_size"]) is not int
            or service["training_batch_size"] != self.training_batch_size
        ):
            raise ValueError("RND predictor service version/minibatch mismatch")
        options = None
        if service["options"] is not None:
            if self.service_options is None:
                raise ValueError("RND checkpoint service options differ from unconfigured destination")
            expected_options = self.service_options.model_dump()
            raw_options = service["options"]
            if (
                not isinstance(raw_options, dict)
                or raw_options.keys() != expected_options.keys()
                or any(
                    type(value) is not type(expected_options[key]) or value != expected_options[key] for key, value in raw_options.items()
                )
            ):
                raise ValueError("RND checkpoint requires exact selected service options")
            options = self._validated_options(RNDOptions.model_validate(raw_options))
        if options != self.service_options:
            raise ValueError("RND checkpoint service policy differs from configured destination")
        pending = service["pending_observations"]
        self._validate_observations(pending)
        for key in ("admitted_rows", "consumed_rows", "dropped_rows", "optimizer_updates", "ordinary_updates_at_position", "step_counter"):
            if type(service[key]) is not int or service[key] < 0:
                raise ValueError(f"RND service {key} must be a nonnegative integer")
        offset = service["optimizer_step_offset"]
        origin = service["optimizer_epoch_origin"]
        if type(origin) is not int or not 0 <= origin <= service["optimizer_updates"]:
            raise ValueError("RND optimizer epoch origin must be an exact retained lifetime update count")
        epoch_updates = service["optimizer_updates"] - origin
        if type(offset) is not int or epoch_updates + offset < 0:
            raise ValueError("RND optimizer step offset must describe a nonnegative Adam clock")
        if self._optimizer_step(prepared[2]) != epoch_updates + offset:
            raise ValueError("RND Adam history does not match versioned service optimizer updates")
        if type(service["service_clock_unit"]) is not str or service["service_clock_unit"] != self.service_clock_unit:
            raise ValueError("RND checkpoint service unit differs from destination")
        tick = service["service_position"]
        if tick is not None and (type(tick) is not int or tick < 0):
            raise ValueError("RND service position invalid")
        if service["admitted_rows"] != service["consumed_rows"] + service["dropped_rows"] + len(pending):
            raise ValueError("RND service row accounting mismatch")
        if service["consumed_rows"] != service["optimizer_updates"] * self.training_batch_size:
            raise ValueError("RND service optimizer accounting mismatch")
        if self.service_clock_unit == "world_eligible_admission":
            if options is None or tick != service["admitted_rows"] or service["step_counter"] != 0:
                raise ValueError("RND private native clock/configuration disagrees with admissions")
            if tick == 0 and (service["optimizer_updates"] or service["ordinary_updates_at_position"]):
                raise ValueError("RND unstarted private service has work")
        if tick is None and service["ordinary_updates_at_position"] != 0:
            raise ValueError("RND service pacing requires a tick")
        if service["ordinary_updates_at_position"] > service["optimizer_updates"]:
            raise ValueError("RND service paced updates exceed total optimizer updates")
        if options is not None:
            assert options.max_pending_rows is not None and options.max_updates_per_tick is not None
            if len(pending) > options.max_pending_rows:
                raise ValueError("RND pending observations exceed capacity")
            if options.service_mode == "paced_fifo" and service["ordinary_updates_at_position"] > options.max_updates_per_tick:
                raise ValueError("RND service paced budget exceeded")
            # The explicit direct one-minibatch API may leave complete batches;
            # occupancy admit_and_service drains these on its next invocation.
        pending_rows = [row.detach().to(self.device).clone() for row in pending]
        return prepared, pending_rows, service

    def prepare_state(self, state: dict[str, Any]) -> _PreparedRND:
        """Own and prepare every field off-side before a destination-bound commit."""
        try:
            owned = deepcopy(state)
            prepared, pending_rows, service = self._prepare_state(owned)
            candidate = deepcopy(self)
            candidate._install_available_state(owned, prepared)
            candidate.obs_buffer = pending_rows
            candidate._admitted_rows = service["admitted_rows"]
            candidate._consumed_rows = service["consumed_rows"]
            candidate._dropped_rows = service["dropped_rows"]
            candidate._optimizer_updates = service["optimizer_updates"]
            candidate._optimizer_epoch_origin = service["optimizer_epoch_origin"]
            candidate._service_position = service["service_position"]
            candidate._ordinary_updates_at_position = service["ordinary_updates_at_position"]
            candidate.step_counter = service["step_counter"]
            return _PreparedRND(self, candidate.__dict__, False)
        except (KeyError, TypeError, RuntimeError, AttributeError, OverflowError) as error:
            raise ValueError("RND checkpoint is malformed") from error

    def prepare_learning_reset(self, *, fresh: RNDExploration) -> _PreparedRND:
        """Prepare fresh factory learning with unchanged owned service obligations.

        Construction and its RNG continuation belong to the enclosing owner. This
        method only validates/copies existing objects; it never constructs a model
        or activates a random stream. The enclosing BANK authenticates freshness
        and boundary revisions before installing its native prepared candidate.
        """
        if type(fresh) is not RNDExploration or fresh is self:
            raise ValueError("RND reset requires a distinct actual RND factory candidate")
        current = self.checkpoint_state()
        self.validate_state(current)
        fresh_state = fresh.checkpoint_state()
        fresh.validate_state(fresh_state)
        for backend in (self, fresh):
            actual = [parameter for group in backend.optimizer.param_groups for parameter in group["params"]]
            expected = list(backend.predictor_network.parameters())
            if (
                type(backend.optimizer) is not torch.optim.Adam
                or len(actual) != len(expected)
                or any(parameter is not reference for parameter, reference in zip(actual, expected, strict=True))
            ):
                raise ValueError("RND reset requires actual predictor/Adam Parameter pairing")
            if any(parameter.requires_grad or parameter.grad is not None for parameter in backend.fixed_network.parameters()):
                raise ValueError("RND reset requires a frozen gradient-free target")
        if (
            self.obs_dim != fresh.obs_dim
            or self.embed_dim != fresh.embed_dim
            or self.training_batch_size != fresh.training_batch_size
            or self.device != fresh.device
            or self.service_clock_unit != fresh.service_clock_unit
            or self.service_options != fresh.service_options
            or self.epsilon_min != fresh.epsilon_min
            or self.epsilon_decay != fresh.epsilon_decay
            or current["optimizer"]["param_groups"] != fresh_state["optimizer"]["param_groups"]
        ):
            raise ValueError("RND fresh candidate differs from the retained selected configuration")
        service = fresh_state["predictor_service"]
        if (
            any(
                service[key] != 0
                for key in (
                    "admitted_rows",
                    "consumed_rows",
                    "dropped_rows",
                    "optimizer_updates",
                    "optimizer_epoch_origin",
                    "optimizer_step_offset",
                    "ordinary_updates_at_position",
                    "step_counter",
                )
            )
            or len(service["pending_observations"])
            or service["service_position"] != (0 if self.service_clock_unit == "world_eligible_admission" else None)
            or fresh.optimizer.state
            or any(parameter.grad is not None for parameter in fresh.predictor_network.parameters())
            or (fresh.reward_rms.mean, fresh.reward_rms.var, fresh.reward_rms.count) != (0.0, 1.0, 1e-4)
        ):
            raise ValueError("RND reset candidate must have genuine fresh learning and no service work")
        for key in (
            "fixed_network",
            "predictor_network",
            "optimizer",
            "adam_restore_recipe",
            "reward_rms_mean",
            "reward_rms_var",
            "reward_rms_count",
        ):
            current[key] = fresh_state[key]
        current["predictor_service"]["optimizer_epoch_origin"] = self._optimizer_updates
        current["predictor_service"]["optimizer_step_offset"] = 0
        prepared = self.prepare_state(current)
        for module_name in ("fixed_network", "predictor_network"):
            for parameter in prepared.attributes[module_name].parameters():
                parameter.grad = None
        return prepared

    def install_state(self, prepared: _PreparedRND) -> None:
        if type(prepared) is not _PreparedRND or prepared.owner is not self or prepared.consumed:
            raise ValueError("RND prepared state belongs to another destination or was consumed")
        prepared.consumed = True
        self.__dict__ = prepared.attributes

    def load_state(self, state: dict[str, Any]) -> None:
        self.install_state(self.prepare_state(state))
