"""Instance-owned transition curiosity with bounded, separately serviced learning."""

from __future__ import annotations

import math
from collections import deque
from copy import deepcopy
from typing import Any, cast

import torch
from torch import Tensor, nn
from torch.nn import functional

from townlet.config.exploration_policy import ExplorationServiceReceipt, IntrinsicTransitionContext, ResolvedExplorationPolicy
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration

_COUNTERS = ("admitted_rows", "consumed_rows", "dropped_rows", "optimizer_updates", "mandatory_service_updates")


def _number(value: Any, name: str, integer: bool, minimum: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError(f"ICM {name} requires a finite number >= {minimum}")
    if integer and not isinstance(value, int):
        raise ValueError(f"ICM {name} requires an integer")


def _owned(value: Any) -> Any:
    if isinstance(value, Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {key: _owned(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_owned(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_owned(item) for item in value)
    return deepcopy(value)


class ICMExploration(EpsilonGreedyExploration):
    """Raw transition reward and independently admitted inverse/forward training.

    Pending rows are owned CPU snapshots. Device metadata records checkpoint
    provenance; restore maps tensors onto the receiving instance's device.
    """

    def __init__(
        self,
        policy: ResolvedExplorationPolicy,
        *,
        obs_dim: int,
        action_dim: int,
        feature_dim: int,
        hidden_dim: int,
        learning_rate: float,
        inverse_weight: float,
        forward_weight: float,
        training_batch_size: int,
        max_pending_transitions: int,
        device: torch.device | str,
    ):
        if not isinstance(policy, ResolvedExplorationPolicy) or policy.strategy != "icm":
            raise ValueError("ICM requires a resolved icm policy")
        parameters = {
            "feature_dim": feature_dim,
            "hidden_dim": hidden_dim,
            "learning_rate": learning_rate,
            "inverse_weight": inverse_weight,
            "forward_weight": forward_weight,
            "training_batch_size": training_batch_size,
            "max_pending_transitions": max_pending_transitions,
        }
        for name, value in {"obs_dim": obs_dim, "action_dim": action_dim, **parameters}.items():
            integer = name not in ("learning_rate", "inverse_weight", "forward_weight")
            _number(value, name, integer, 1 if integer else 0)
        if learning_rate <= 0 or max_pending_transitions < training_batch_size:
            raise ValueError("ICM requires positive learning_rate and capacity >= training_batch_size")
        if parameters != dict(policy.provider_parameters):
            raise ValueError("ICM constructor parameters disagree with the selected policy")
        super().__init__(epsilon=policy.epsilon_start, epsilon_decay=policy.epsilon_decay, epsilon_min=policy.epsilon_end)
        self.policy = policy
        self.obs_dim, self.action_dim = obs_dim, action_dim
        self.feature_dim, self.hidden_dim = feature_dim, hidden_dim
        self.learning_rate = float(learning_rate)
        self.inverse_weight, self.forward_weight = float(inverse_weight), float(forward_weight)
        self.training_batch_size, self.max_pending_transitions = training_batch_size, max_pending_transitions
        self.encoder = nn.Sequential(nn.Linear(obs_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, feature_dim))
        self.inverse_model = nn.Sequential(nn.Linear(2 * feature_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, action_dim))
        self.forward_model = nn.Sequential(nn.Linear(feature_dim + action_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, feature_dim))
        for module in (self.encoder, self.inverse_model, self.forward_model):
            module.to(device=device, dtype=torch.float32)
        self.device = next(self.encoder.parameters()).device
        self._source_device = str(self.device)
        self.optimizer = torch.optim.Adam(self._parameters(), lr=self.learning_rate)
        self._pending: deque[dict[str, Any]] = deque()
        self._counters = dict.fromkeys(_COUNTERS, 0)
        self._last_loss = 0.0
        self._service_tick: int | None = None
        self._ordinary_updates_this_tick = 0

    def _parameters(self) -> list[nn.Parameter]:
        return [parameter for module in (self.encoder, self.inverse_model, self.forward_model) for parameter in module.parameters()]

    def _context(self, context: IntrinsicTransitionContext) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        if not isinstance(context, IntrinsicTransitionContext):
            raise ValueError("ICM requires actual predecessor/actions/successor IntrinsicTransitionContext")
        predecessor, actions, successor, active = context.predecessor, context.actions, context.successor, context.active_on_entry
        if predecessor.ndim != 2 or predecessor.shape[1] != self.obs_dim or successor.shape != predecessor.shape:
            raise ValueError("ICM transition observations require [N, obs_dim] geometry")
        if (
            actions.shape != (len(predecessor),)
            or active.shape != actions.shape
            or actions.dtype != torch.long
            or active.dtype != torch.bool
        ):
            raise ValueError("ICM transition actions/eligibility require int64/bool [N] tensors")
        if any(value.device != self.device for value in (predecessor, actions, successor, active)):
            raise ValueError("ICM transition device disagrees with provider device")
        if any(value.dtype != torch.float32 or not torch.isfinite(value).all() for value in (predecessor, successor)):
            raise ValueError("ICM transition observations require finite float32 tensors")
        if ((actions[active] < 0) | (actions[active] >= self.action_dim)).any():
            raise ValueError("ICM eligible transition action is out of bounds")
        return predecessor, actions, successor, active

    def compute_transition_novelty(self, context: IntrinsicTransitionContext, *, update_stats: bool) -> Tensor:
        predecessor, actions, successor, active = self._context(context)
        if not isinstance(update_stats, bool):
            raise ValueError("ICM update_stats requires bool")
        with torch.no_grad():
            rewards = torch.zeros(len(predecessor), device=self.device, dtype=torch.float32)
            if active.any():
                features = self.encoder(predecessor[active])
                target = self.encoder(successor[active]).detach()
                inputs = torch.cat((features, functional.one_hot(actions[active], self.action_dim).to(features)), dim=1)
                rewards[active] = 0.5 * (self.forward_model(inputs) - target).square().mean(dim=1)
            if not torch.isfinite(rewards).all():
                raise ValueError("ICM transition produced nonfinite novelty")
        return rewards.detach()

    def compute_intrinsic_rewards(self, observations: Tensor, *args: Any, **kwargs: Any) -> Tensor:
        raise ValueError("ICM reward requires actual predecessor/actions/successor; use compute_transition_novelty")

    def update(self, batch: dict[str, Tensor]) -> None:
        raise ValueError("ICM learning requires complete transition context; use admit_and_service")

    def _train_batch(self, mandatory: bool) -> None:
        rows = list(self._pending)[: self.training_batch_size]
        predecessor = torch.stack([row["predecessor"] for row in rows]).to(self.device)
        successor = torch.stack([row["successor"] for row in rows]).to(self.device)
        actions = torch.tensor([row["action"] for row in rows], device=self.device, dtype=torch.long)
        features, next_features = self.encoder(predecessor), self.encoder(successor)
        logits = self.inverse_model(torch.cat((features, next_features), dim=1))
        inputs = torch.cat((features, functional.one_hot(actions, self.action_dim).to(features)), dim=1)
        forward_error = (self.forward_model(inputs) - next_features.detach()).square().mean()
        loss = self.inverse_weight * functional.cross_entropy(logits, actions) + self.forward_weight * forward_error
        if not torch.isfinite(loss):
            raise ValueError("ICM transition objective is nonfinite")
        self.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        if any(parameter.grad is not None and not torch.isfinite(parameter.grad).all() for parameter in self._parameters()):
            raise ValueError("ICM transition objective produced nonfinite gradients")
        self.optimizer.step()
        for _ in rows:
            self._pending.popleft()
        self._last_loss = float(loss.detach().item())
        self._counters["consumed_rows"] += len(rows)
        self._counters["optimizer_updates"] += 1
        if mandatory:
            self._counters["mandatory_service_updates"] += 1
        else:
            self._ordinary_updates_this_tick += 1

    def admit_and_service(self, context: IntrinsicTransitionContext) -> ExplorationServiceReceipt:
        predecessor, actions, successor, active = self._context(context)
        if self._service_tick is not None and context.vector_tick < self._service_tick:
            raise ValueError("ICM service vector_tick must be monotonic")
        before = dict(self._counters)
        if context.vector_tick != self._service_tick:
            self._service_tick, self._ordinary_updates_this_tick = context.vector_tick, 0
        for index in active.nonzero(as_tuple=False).flatten().tolist():
            if len(self._pending) == self.max_pending_transitions:
                if self.policy.overflow_policy == "service_before_admit":
                    self._train_batch(True)
                elif self.policy.overflow_policy == "drop_oldest":
                    self._pending.popleft()
                    self._counters["dropped_rows"] += 1
                else:
                    self._counters["admitted_rows"] += 1
                    self._counters["dropped_rows"] += 1
                    continue
            self._pending.append(
                {"predecessor": _owned(predecessor[index]), "action": int(actions[index].item()), "successor": _owned(successor[index])}
            )
            self._counters["admitted_rows"] += 1
        while len(self._pending) >= self.training_batch_size:
            if self.policy.service_mode == "paced_fifo" and self._ordinary_updates_this_tick >= self.policy.max_updates_per_tick:
                break
            self._train_batch(False)
        return ExplorationServiceReceipt(
            provider="icm",
            **{name: self._counters[name] - before[name] for name in _COUNTERS},
            pending_rows=len(self._pending),
            last_loss=self._last_loss,
        )

    def _config(self) -> dict[str, Any]:
        return {
            "obs_dim": self.obs_dim,
            "action_dim": self.action_dim,
            "feature_dim": self.feature_dim,
            "hidden_dim": self.hidden_dim,
            "learning_rate": self.learning_rate,
            "inverse_weight": self.inverse_weight,
            "forward_weight": self.forward_weight,
            "training_batch_size": self.training_batch_size,
            "max_pending_transitions": self.max_pending_transitions,
            "device": self._source_device,
        }

    def checkpoint_state(self) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            _owned(
                {
                    "schema": "icm-state-v1",
                    "policy": self.policy.to_dict(),
                    "policy_identity": self.policy.policy_identity,
                    "config": self._config(),
                    "encoder": self.encoder.state_dict(),
                    "inverse_model": self.inverse_model.state_dict(),
                    "forward_model": self.forward_model.state_dict(),
                    "optimizer": self.optimizer.state_dict(),
                    "epsilon": self.epsilon,
                    "epsilon_decay": self.epsilon_decay,
                    "epsilon_min": self.epsilon_min,
                    "pending": list(self._pending),
                    "counters": self._counters,
                    "last_loss": self._last_loss,
                    "service_tick": self._service_tick,
                    "ordinary_updates_this_tick": self._ordinary_updates_this_tick,
                }
            ),
        )

    def _model_state(self, module: nn.Sequential, payload: Any) -> nn.Sequential:
        expected = module.state_dict()
        if not isinstance(payload, dict) or payload.keys() != expected.keys():
            raise ValueError("ICM model state requires exact tensor keys")
        for name, value in payload.items():
            if (
                not isinstance(value, Tensor)
                or value.shape != expected[name].shape
                or value.dtype != expected[name].dtype
                or not torch.isfinite(value).all()
            ):
                raise ValueError(f"ICM model tensor {name} has invalid geometry/dtype/value")
        candidate = deepcopy(module)
        candidate.load_state_dict(payload, strict=True)
        return candidate

    def _optimizer_state(self, modules: tuple[nn.Module, ...], payload: Any, updates: int) -> torch.optim.Adam:
        parameters = [parameter for module in modules for parameter in module.parameters()]
        expected = self.optimizer.state_dict()["param_groups"]
        if not isinstance(payload, dict) or set(payload) != {"state", "param_groups"} or payload["param_groups"] != expected:
            raise ValueError("ICM optimizer parameter groups disagree with selected configuration")
        states = payload["state"]
        identifiers = expected[0]["params"]
        required: set[int] = set()
        if updates:
            required = set(identifiers)
        if not isinstance(states, dict) or set(states) != required:
            raise ValueError("ICM optimizer state does not match successful update count")
        for identifier, parameter in zip(identifiers, parameters, strict=True):
            if not updates:
                continue
            item = states[identifier]
            if not isinstance(item, dict) or set(item) != {"step", "exp_avg", "exp_avg_sq"}:
                raise ValueError("ICM optimizer moments require complete Adam state")
            step = item["step"]
            if (
                not isinstance(step, Tensor)
                or step.shape != ()
                or not step.is_floating_point()
                or not torch.isfinite(step)
                or step.item() != updates
            ):
                raise ValueError("ICM optimizer step disagrees with successful updates")
            for name in ("exp_avg", "exp_avg_sq"):
                value = item[name]
                if (
                    not isinstance(value, Tensor)
                    or value.shape != parameter.shape
                    or value.dtype != parameter.dtype
                    or not torch.isfinite(value).all()
                ):
                    raise ValueError("ICM optimizer moment has invalid geometry/dtype/value")
                if name == "exp_avg_sq" and (value < 0).any():
                    raise ValueError("ICM optimizer variance must be nonnegative")
        optimizer = torch.optim.Adam(parameters, lr=self.learning_rate)
        optimizer.load_state_dict(_owned(payload))
        return optimizer

    def load_state(self, state: dict[str, Any]) -> None:
        """Validate all transported state off-side before replacing any live state."""
        if not isinstance(state, dict) or state.keys() != self.checkpoint_state().keys() or state["schema"] != "icm-state-v1":
            raise ValueError("ICM requires complete icm-state-v1 checkpoint")
        try:
            policy = ResolvedExplorationPolicy.from_dict(state["policy"])
            if policy.policy_identity != state["policy_identity"] or policy.policy_identity != self.policy.policy_identity:
                raise ValueError("ICM checkpoint selected policy identity disagrees")
            config = state["config"]
            expected = self._config()
            if not isinstance(config, dict) or config.keys() != expected.keys():
                raise ValueError("ICM checkpoint configuration is incomplete")
            for name, value in expected.items():
                if name != "device" and (type(config[name]) is not type(value) or config[name] != value):
                    raise ValueError(f"ICM checkpoint configuration disagrees at {name}")
            if not isinstance(config["device"], str):
                raise ValueError("ICM checkpoint source device requires a device string")
            torch.device(config["device"])
            counters = state["counters"]
            if not isinstance(counters, dict) or set(counters) != set(_COUNTERS):
                raise ValueError("ICM checkpoint counters are incomplete")
            for name, value in counters.items():
                _number(value, name, True, 0)
            pending = state["pending"]
            if not isinstance(pending, list) or len(pending) > self.max_pending_transitions:
                raise ValueError("ICM checkpoint pending transitions exceed capacity")
            for row in pending:
                if not isinstance(row, dict) or set(row) != {"predecessor", "action", "successor"}:
                    raise ValueError("ICM checkpoint requires complete pending transitions")
                _number(row["action"], "pending action", True, 0)
                if row["action"] >= self.action_dim:
                    raise ValueError("ICM checkpoint pending action is out of bounds")
                for name in ("predecessor", "successor"):
                    value = row[name]
                    if (
                        not isinstance(value, Tensor)
                        or value.shape != (self.obs_dim,)
                        or value.dtype != torch.float32
                        or not torch.isfinite(value).all()
                    ):
                        raise ValueError("ICM checkpoint pending observation has invalid geometry/dtype/value")
            updates = counters["optimizer_updates"]
            if counters["consumed_rows"] != updates * self.training_batch_size or counters["mandatory_service_updates"] > updates:
                raise ValueError("ICM checkpoint service counters disagree")
            if counters["admitted_rows"] != counters["consumed_rows"] + counters["dropped_rows"] + len(pending):
                raise ValueError("ICM checkpoint transition conservation failed")
            tick, budget = state["service_tick"], state["ordinary_updates_this_tick"]
            _number(budget, "ordinary service budget", True, 0)
            if tick is None:
                if counters["admitted_rows"] or updates or budget:
                    raise ValueError("ICM unstarted service has nonempty counters")
            else:
                _number(tick, "service_tick", True, 0)
            if budget > updates - counters["mandatory_service_updates"] or (
                policy.service_mode == "paced_fifo" and budget > policy.max_updates_per_tick
            ):
                raise ValueError("ICM checkpoint service tick budget is invalid")
            for name in ("epsilon", "epsilon_decay", "epsilon_min", "last_loss"):
                _number(state[name], name, False, 0)
            if (
                state["epsilon_decay"] != policy.epsilon_decay
                or state["epsilon_min"] != policy.epsilon_end
                or not policy.epsilon_end <= state["epsilon"] <= policy.epsilon_start
            ):
                raise ValueError("ICM checkpoint epsilon schedule disagrees with selected policy")
            if not updates and state["last_loss"] != 0:
                raise ValueError("ICM checkpoint has loss without a successful update")
            encoder = self._model_state(self.encoder, state["encoder"])
            inverse = self._model_state(self.inverse_model, state["inverse_model"])
            forward = self._model_state(self.forward_model, state["forward_model"])
            optimizer = self._optimizer_state((encoder, inverse, forward), state["optimizer"], updates)
            owned_pending = deque(_owned(pending))
        except (KeyError, TypeError, RuntimeError, AttributeError, OverflowError) as error:
            raise ValueError("ICM checkpoint is malformed") from error
        self.encoder, self.inverse_model, self.forward_model, self.optimizer = encoder, inverse, forward, optimizer
        self.policy, self._source_device = policy, config["device"]
        self.epsilon, self.epsilon_decay, self.epsilon_min = state["epsilon"], state["epsilon_decay"], state["epsilon_min"]
        self._pending, self._counters, self._last_loss = owned_pending, dict(counters), float(state["last_loss"])
        self._service_tick, self._ordinary_updates_this_tick = tick, budget
