"""Random Network Distillation (RND) for intrinsic motivation."""

from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812

from townlet.config.bac_options import RNDOptions
from townlet.exploration.action_selection import epsilon_greedy_action_selection
from townlet.exploration.base import ExplorationStrategy
from townlet.training.state import BatchedAgentState


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
        batch_count = x.size if isinstance(x.size, int) else np.prod(x.shape)

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
        if type(training_batch_size) is not int or training_batch_size <= 0:
            raise ValueError("RND training_batch_size must be a positive integer")
        self.obs_dim = obs_dim
        self.embed_dim = embed_dim
        self.training_batch_size = training_batch_size
        self.device = device

        # Epsilon parameters
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

        # Fixed network (random, frozen)
        self.fixed_network = RNDNetwork(obs_dim, embed_dim).to(device)
        for param in self.fixed_network.parameters():
            param.requires_grad = False

        # Predictor network (trained to match fixed)
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
        self._vector_tick: int | None = None
        self._paced_updates_this_tick = 0

        # Running statistics for intrinsic reward normalization
        self.reward_rms = RunningMeanStd()

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
        with torch.no_grad():
            target_features: torch.Tensor = self.fixed_network(observations)
            predicted_features: torch.Tensor = self.predictor_network(observations)
            # MSE per sample (high error = novel = high reward)
            mse_per_sample = ((target_features - predicted_features) ** 2).mean(dim=1)

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
        if "observations" not in batch:
            return

        observations = batch["observations"]

        if self.service_options is not None:
            # The unclocked compatibility API denotes the next local service tick.
            if self._vector_tick is not None:
                self.step_counter = max(self.step_counter, self._vector_tick + 1)
            self.admit_and_service(observations, vector_tick=self.step_counter)
            self.step_counter += 1
            return
        # Explicit legacy adapter: one minibatch per call, retaining its old API.
        self._validate_observations(observations)
        self.obs_buffer.extend(row.detach().clone() for row in observations)
        self._admitted_rows += len(observations)
        self.update_predictor()

    def _validate_observations(self, observations: torch.Tensor) -> None:
        if (
            not isinstance(observations, torch.Tensor)
            or observations.ndim != 2
            or observations.shape[1] != self.obs_dim
            or observations.dtype != next(self.predictor_network.parameters()).dtype
        ):
            raise ValueError("RND observations must be finite floating rows with matching width and dtype")
        for chunk in observations.split(self.training_batch_size):
            if not torch.isfinite(chunk).all().item():
                raise ValueError("RND observations must be finite floating rows with matching width and dtype")

    def _validated_options(self, options: RNDOptions) -> RNDOptions:
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

    def admit_and_service(self, observations: torch.Tensor, *, vector_tick: int) -> PredictorServiceReceipt:
        """Admit only caller-selected eligible predecessor rows in bounded chunks.

        The caller owns eligibility and local clocks. Repeated calls at the same
        tick share the ordinary paced budget. Lossless mandatory overflow service
        may exceed that budget and is reported separately. Each loop either admits,
        consumes, or explicitly drops rows, including oversized input tensors.
        """
        self._validate_observations(observations)
        options = self.service_options
        if options is None:
            raise ValueError("configure_service with resolved options before bounded RND admission")
        if type(vector_tick) is not int or vector_tick < 0 or (self._vector_tick is not None and vector_tick < self._vector_tick):
            raise ValueError("RND vector_tick must be a nonnegative monotone integer")
        if vector_tick != self._vector_tick:
            self._vector_tick = vector_tick
            self._paced_updates_this_tick = 0
        capacity = options.max_pending_rows
        budget = options.max_updates_per_tick
        assert capacity is not None and budget is not None
        start_consumed, start_dropped = self._consumed_rows, self._dropped_rows
        paced, overflow = 0, 0
        last_loss: float | None = None
        offset = 0
        while True:
            while len(self.obs_buffer) >= self.training_batch_size:
                if options.service_mode == "paced_fifo" and self._paced_updates_this_tick >= budget:
                    break
                last_loss = self.update_predictor()
                paced += 1
                self._paced_updates_this_tick += 1
            if offset == len(observations):
                break
            room = capacity - len(self.obs_buffer)
            if room == 0:
                if options.overflow_policy == "service_before_admit":
                    last_loss = self.update_predictor()
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

        # Gradient step
        self.optimizer.zero_grad()
        loss.backward()
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
        state = self.available_state()
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
            "version": 1,
            "training_batch_size": self.training_batch_size,
            "options": options,
            "pending_observations": pending,
            "admitted_rows": admitted,
            "consumed_rows": self._consumed_rows,
            "dropped_rows": self._dropped_rows,
            "optimizer_updates": self._optimizer_updates,
            # Capture the trusted live clock, including public manual optimizer
            # steps and historical imports. Restore validates this saved offset.
            "optimizer_step_offset": self._optimizer_step(self.optimizer) - self._optimizer_updates,
            "vector_tick": self._vector_tick,
            "paced_updates_this_tick": self._paced_updates_this_tick,
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
            if not isinstance(group["params"], list) or any(type(index) is not int for index in group["params"]):
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

    def _prepare_available_state(self, state: dict[str, Any]) -> tuple[Any, Any, Any]:
        expected_keys = set(self.available_state())
        missing = expected_keys - set(state)
        if missing:
            raise KeyError(f"RND available-state missing fields: {sorted(missing)}")
        if set(state) != expected_keys:
            raise ValueError("RND available-state fields mismatch")
        self._finite_tree(state)
        if state["obs_dim"] != self.obs_dim or state["embed_dim"] != self.embed_dim:
            raise ValueError("RND checkpoint network geometry mismatch")
        for key in ("epsilon", "epsilon_min", "epsilon_decay", "reward_rms_mean", "reward_rms_var", "reward_rms_count"):
            if isinstance(state[key], bool) or not isinstance(state[key], (int, float, np.floating)):
                raise ValueError(f"RND checkpoint {key} must be a finite scalar")
        if any(not 0 <= state[key] <= 1 for key in ("epsilon", "epsilon_min", "epsilon_decay")):
            raise ValueError("RND checkpoint epsilon settings outside [0,1]")
        if state["reward_rms_var"] < 0 or state["reward_rms_count"] <= 0:
            raise ValueError("RND checkpoint normalization variance/count invalid")
        fixed, predictor, optimizer = deepcopy((self.fixed_network, self.predictor_network, self.optimizer))
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
        if not isinstance(optimizer_state["state"], dict):
            raise ValueError("RND checkpoint optimizer moments must be a mapping")
        parameter_ids = [index for group in optimizer_state["param_groups"] for index in group["params"]]
        if len(set(parameter_ids)) != len(parameter_ids) or not set(optimizer_state["state"]).issubset(parameter_ids):
            raise ValueError("RND checkpoint optimizer parameter identity mismatch")
        if optimizer_state["state"] and set(optimizer_state["state"]) != set(parameter_ids):
            raise ValueError("RND dense predictor requires complete Adam history for every parameter")
        optimizer.load_state_dict(deepcopy(optimizer_state))
        steps: set[int] = set()
        for group in optimizer.param_groups:
            if group["lr"] < 0 or group["eps"] < 0 or group["weight_decay"] < 0 or any(not 0 <= beta < 1 for beta in group["betas"]):
                raise ValueError("RND checkpoint optimizer settings invalid")
            for parameter in group["params"]:
                if parameter not in optimizer.state:
                    continue
                moments = optimizer.state[parameter]
                required = {"step", "exp_avg", "exp_avg_sq"}
                if group["amsgrad"]:
                    required.add("max_exp_avg_sq")
                if set(moments) != required:
                    raise ValueError("RND checkpoint optimizer moment fields mismatch")
                for name, tensor in moments.items():
                    if not isinstance(tensor, torch.Tensor):
                        raise ValueError("RND checkpoint optimizer moments must be tensors")
                    if name == "step":
                        if tensor.numel() != 1 or tensor.item() < 0 or tensor.item() != int(tensor.item()):
                            raise ValueError("RND checkpoint optimizer step invalid")
                        steps.add(int(tensor.item()))
                    elif tensor.shape != parameter.shape or tensor.dtype != parameter.dtype:
                        raise ValueError("RND checkpoint optimizer moment geometry mismatch")
                    elif name in {"exp_avg_sq", "max_exp_avg_sq"} and (tensor < 0).any().item():
                        raise ValueError("RND checkpoint optimizer squared moments must be nonnegative")
        if len(steps) > 1:
            raise ValueError("RND dense predictor Adam parameter steps must agree")
        # Exercise destination execution on disposable copies, including flags
        # whose device/version compatibility is enforced only during Adam.step.
        probe = deepcopy(optimizer)
        for group in probe.param_groups:
            for parameter in group["params"]:
                parameter.grad = torch.zeros_like(parameter)
        try:
            probe.step()
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

    def load_available_state(self, state: dict[str, Any]) -> None:
        """Explicit historical import of available state only; never invent old tails/RNG.

        Preserves destination pending work/clocks, matching the historical API.
        Source pending work and RNG are unavailable; this is not tail continuation.
        """
        prepared = self._prepare_available_state(state)
        self._install_available_state(state, prepared)

    def validate_state(self, state: dict[str, Any]) -> None:
        """Validate a full continuation payload without modifying live state."""
        if "predictor_service" not in state:
            self._prepare_available_state(state)
        else:
            self._prepare_state(state)

    def _prepare_state(self, state: dict[str, Any]) -> tuple[tuple[Any, Any, Any], list[torch.Tensor], dict[str, Any]]:
        if "predictor_service" not in state:
            raise ValueError("RND continuation requires predictor_service; use load_available_state for historical imports")
        available = {key: value for key, value in state.items() if key != "predictor_service"}
        prepared = self._prepare_available_state(available)
        service = state["predictor_service"]
        if not isinstance(service, dict) or set(service) != set(self.checkpoint_state()["predictor_service"]):
            raise ValueError("RND predictor service checkpoint fields mismatch")
        if (
            type(service["version"]) is not int
            or service["version"] != 1
            or type(service["training_batch_size"]) is not int
            or service["training_batch_size"] != self.training_batch_size
        ):
            raise ValueError("RND predictor service version/minibatch mismatch")
        options = None
        if service["options"] is not None:
            options = self._validated_options(RNDOptions.model_validate(service["options"]))
        if options != self.service_options:
            raise ValueError("RND checkpoint service policy differs from configured destination")
        pending = service["pending_observations"]
        self._validate_observations(pending)
        for key in ("admitted_rows", "consumed_rows", "dropped_rows", "optimizer_updates", "paced_updates_this_tick", "step_counter"):
            if type(service[key]) is not int or service[key] < 0:
                raise ValueError(f"RND service {key} must be a nonnegative integer")
        offset = service["optimizer_step_offset"]
        if type(offset) is not int or service["optimizer_updates"] + offset < 0:
            raise ValueError("RND optimizer step offset must describe a nonnegative Adam clock")
        if self._optimizer_step(prepared[2]) != service["optimizer_updates"] + offset:
            raise ValueError("RND Adam history does not match versioned service optimizer updates")
        tick = service["vector_tick"]
        if tick is not None and (type(tick) is not int or tick < 0):
            raise ValueError("RND service vector_tick invalid")
        if service["admitted_rows"] != service["consumed_rows"] + service["dropped_rows"] + len(pending):
            raise ValueError("RND service row accounting mismatch")
        if service["consumed_rows"] != service["optimizer_updates"] * self.training_batch_size:
            raise ValueError("RND service optimizer accounting mismatch")
        if tick is None and service["paced_updates_this_tick"] != 0:
            raise ValueError("RND service pacing requires a tick")
        if service["paced_updates_this_tick"] > service["optimizer_updates"]:
            raise ValueError("RND service paced updates exceed total optimizer updates")
        if options is not None:
            assert options.max_pending_rows is not None and options.max_updates_per_tick is not None
            if len(pending) > options.max_pending_rows:
                raise ValueError("RND pending observations exceed capacity")
            if options.service_mode == "paced_fifo" and service["paced_updates_this_tick"] > options.max_updates_per_tick:
                raise ValueError("RND service paced budget exceeded")
            # The explicit direct one-minibatch API may leave complete batches;
            # occupancy admit_and_service drains these on its next invocation.
        pending_rows = [row.detach().to(self.device).clone() for row in pending]
        return prepared, pending_rows, service

    def load_state(self, state: dict[str, Any]) -> None:
        """Validate all owned checkpoint payloads before atomic installation."""
        if "predictor_service" not in state:
            # Exact old schema dispatch, not recovery from malformed current state.
            self.load_available_state(state)
            return
        prepared, pending_rows, service = self._prepare_state(state)
        self._install_available_state(state, prepared)
        self.obs_buffer = pending_rows
        self._admitted_rows, self._consumed_rows, self._dropped_rows = (
            service["admitted_rows"],
            service["consumed_rows"],
            service["dropped_rows"],
        )
        self._optimizer_updates = service["optimizer_updates"]
        self._vector_tick, self._paced_updates_this_tick = service["vector_tick"], service["paced_updates_this_tick"]
        self.step_counter = service["step_counter"]
