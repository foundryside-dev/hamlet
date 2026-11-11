"""Instance-owned transition curiosity with bounded, separately serviced learning."""

from __future__ import annotations

import math
from collections import deque
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal, cast

import torch
from torch import Tensor, nn
from torch.nn import functional

from townlet.config.exploration_policy import ExplorationServiceReceipt, IntrinsicTransitionContext, ResolvedExplorationPolicy
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.exploration.rnd import (
    AdamRestoreRecipe,
    _adam_from_recipe,
    _adam_value_equal,
    _capture_adam_recipe,
    _named_adam_parameters,
    _validate_adam_candidate,
    _validate_adam_recipe,
)
from townlet.exploration.world_curiosity_state import ServiceClock, WorldRNGState

_COUNTERS = ("admitted_rows", "consumed_rows", "dropped_rows", "optimizer_updates", "mandatory_service_updates")


@dataclass
class _PreparedICM:
    owner: object
    attributes: dict[str, Any]
    consumed: bool


def _number(value: Any, name: str, integer: bool, minimum: float) -> None:
    if integer:
        if type(value) is not int or value < minimum:
            raise ValueError(f"ICM {name} requires an exact integer >= {minimum}")
    elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError(f"ICM {name} requires a finite number >= {minimum}")


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
        rng: WorldRNGState | None,
        service_clock_unit: Literal["vector_tick", "world_eligible_admission"],
    ):
        ServiceClock(service_clock_unit, 0)
        if rng is not None and not isinstance(rng, WorldRNGState):
            raise ValueError("ICM rng must be an actual world RNG owner or explicit None")
        self._service_clock_unit = service_clock_unit
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
        device = torch.device(device)
        if device.type not in {"cpu", "cuda"}:
            raise ValueError("ICM requires a concrete CPU or CUDA destination")
        super().__init__(epsilon=policy.epsilon_start, epsilon_decay=policy.epsilon_decay, epsilon_min=policy.epsilon_end)
        self.policy = policy
        self.obs_dim, self.action_dim = obs_dim, action_dim
        self.feature_dim, self.hidden_dim = feature_dim, hidden_dim
        self.learning_rate = float(learning_rate)
        self.inverse_weight, self.forward_weight = float(inverse_weight), float(forward_weight)
        self.training_batch_size, self.max_pending_transitions = training_batch_size, max_pending_transitions
        with rng.activate("model_init") if rng is not None else nullcontext():
            self.encoder = nn.Sequential(nn.Linear(obs_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, feature_dim))
            self.inverse_model = nn.Sequential(nn.Linear(2 * feature_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, action_dim))
        with rng.activate("predictor") if rng is not None else nullcontext():
            self.forward_model = nn.Sequential(
                nn.Linear(feature_dim + action_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, feature_dim)
            )
        for module in (self.encoder, self.inverse_model, self.forward_model):
            module.to(device=device, dtype=torch.float32)
        self.device = next(self.encoder.parameters()).device
        self._source_device = str(self.device)
        self.optimizer = torch.optim.Adam(self._parameters(), lr=self.learning_rate)
        self._pending: deque[dict[str, Any]] = deque()
        self._counters = dict.fromkeys(_COUNTERS, 0)
        self._optimizer_epoch_origin = 0
        self._last_loss = 0.0
        self._service_position: int | None
        if service_clock_unit == "world_eligible_admission":
            self._service_position = 0
        else:
            self._service_position = None
        self._ordinary_updates_at_position = 0

    def __deepcopy__(self, memo: dict[int, Any]) -> ICMExploration:
        """Copy real learned state without pickling frozen policy mappings."""
        candidate = object.__new__(type(self))
        memo[id(self)] = candidate
        if id(self.policy) not in memo:
            memo[id(self.policy)] = type(self.policy).from_dict(self.policy.to_dict())
        candidate.__dict__ = deepcopy(self.__dict__, memo)
        return candidate

    @property
    def service_clock_unit(self) -> Literal["vector_tick", "world_eligible_admission"]:
        return self._service_clock_unit

    def _parameters(self) -> list[nn.Parameter]:
        return [parameter for module in (self.encoder, self.inverse_model, self.forward_model) for parameter in module.parameters()]

    def _named_model_parameters(self) -> dict[str, nn.Parameter]:
        return _named_adam_parameters(
            (("encoder", self.encoder), ("inverse_model", self.inverse_model), ("forward_model", self.forward_model))
        )

    def _context(self, context: IntrinsicTransitionContext) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        if not isinstance(context, IntrinsicTransitionContext):
            raise ValueError("ICM requires actual predecessor/actions/successor IntrinsicTransitionContext")
        predecessor, actions, successor, active = context.predecessor, context.actions, context.successor, context.active_on_entry
        if any(
            value.layout != torch.strided or value.device.type not in {"cpu", "cuda"} for value in (predecessor, actions, successor, active)
        ):
            raise ValueError("ICM context requires concrete dense CPU/CUDA tensors")
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
            self._ordinary_updates_at_position += 1

    def admit_and_service(self, context: IntrinsicTransitionContext) -> ExplorationServiceReceipt:
        """Current shared grouped service with explicit context vector cadence."""
        if self.service_clock_unit != "vector_tick":
            raise ValueError("Private ICM requires explicit eligible-admission service")
        if not isinstance(context, IntrinsicTransitionContext):
            raise ValueError("ICM requires an actual transition context")
        return self.admit_and_service_at(context, clock=ServiceClock("vector_tick", context.vector_tick))

    def admit_and_service_at(self, context: IntrinsicTransitionContext, *, clock: ServiceClock) -> ExplorationServiceReceipt:
        predecessor, actions, successor, active = self._context(context)
        if type(clock) is not ServiceClock:
            raise ValueError("ICM service requires ServiceClock")
        ServiceClock(clock.unit, clock.position)
        ServiceClock("vector_tick", context.vector_tick)
        if clock.unit != self.service_clock_unit:
            raise ValueError("ICM service clock differs from selected unit")
        indices = active.nonzero(as_tuple=False).flatten().tolist()
        previous = self._service_position
        if clock.unit == "vector_tick":
            if clock.position != context.vector_tick or (previous is not None and clock.position < previous):
                raise ValueError("ICM shared clock must match context and not regress")
        elif previous is None or clock.position != previous + len(indices):
            raise ValueError("ICM private clock delta must equal actual eligible admissions")
        before = dict(self._counters)
        if clock.unit == "vector_tick":
            self._admit_rows(predecessor, actions, successor, indices, clock.position)
        else:
            assert previous is not None
            for offset, index in enumerate(indices):
                self._admit_rows(predecessor, actions, successor, [index], previous + offset + 1)
        return ExplorationServiceReceipt(
            provider="icm",
            **{name: self._counters[name] - before[name] for name in _COUNTERS},
            pending_rows=len(self._pending),
            last_loss=self._last_loss,
        )

    def _admit_rows(self, predecessor: Tensor, actions: Tensor, successor: Tensor, indices: list[int], position: int) -> None:
        if position != self._service_position:
            self._service_position, self._ordinary_updates_at_position = position, 0
        for index in indices:
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
            if self.policy.service_mode == "paced_fifo" and self._ordinary_updates_at_position >= self.policy.max_updates_per_tick:
                break
            self._train_batch(False)

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
        if len(self.optimizer.param_groups) != 1:
            raise ValueError("ICM restore requires one actual Adam group")
        state = cast(
            dict[str, Any],
            _owned(
                {
                    "schema": "icm-state-v4",
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
                    "optimizer_epoch_origin": self._optimizer_epoch_origin,
                    "last_loss": self._last_loss,
                    "service_clock_unit": self.service_clock_unit,
                    "service_position": self._service_position,
                    "ordinary_updates_at_position": self._ordinary_updates_at_position,
                }
            ),
        )
        state["adam_restore_recipe"] = _owned(_capture_adam_recipe(self._named_model_parameters(), self.optimizer, state["optimizer"]))
        return state

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

    def _optimizer_state(self, modules: tuple[nn.Module, ...], payload: Any, updates: int, recipe: AdamRestoreRecipe) -> torch.optim.Adam:
        named = _named_adam_parameters((("encoder", modules[0]), ("inverse_model", modules[1]), ("forward_model", modules[2])))
        _validate_adam_recipe(named, recipe, payload)
        expected = self.optimizer.state_dict()["param_groups"]
        if len(expected) != 1 or not _adam_value_equal(payload["param_groups"], expected):
            raise ValueError("ICM optimizer parameter groups disagree with selected configuration")
        parameters = [named[name] for name in recipe["groups"][0]["parameter_names"]]
        for group, reference in zip(payload["param_groups"], expected, strict=True):
            if any(type(group[key]) is not type(value) for key, value in reference.items()):
                raise ValueError("ICM optimizer group field types disagree with selected configuration")
            if any(type(value) is not int for value in group["params"]) or any(type(value) is not float for value in group["betas"]):
                raise ValueError("ICM optimizer parameter IDs/betas require exact native types")
        states = payload["state"]
        identifiers = payload["param_groups"][0]["params"]
        required: set[int] = set()
        if updates:
            required = set(identifiers)
        if not isinstance(states, dict) or set(states) != required or any(type(key) is not int for key in states):
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
        optimizer = _adam_from_recipe(named, recipe, payload)
        optimizer.load_state_dict(_owned(payload))
        return optimizer

    def validate_state(self, state: dict[str, Any]) -> None:
        self.prepare_state(state)

    def with_restore_configuration(self, state: dict[str, Any]) -> ICMExploration:
        """Return an owned selected model graph with checked single-group Adam."""
        try:
            _validate_adam_recipe(self._named_model_parameters(), state["adam_restore_recipe"], state["optimizer"])
            owned = _owned(state)
            if type(owned) is not dict or owned.keys() != self.checkpoint_state().keys() or owned["schema"] != "icm-state-v4":
                raise ValueError("ICM restore configuration requires complete icm-state-v4")
            candidate = deepcopy(self)
            candidate.optimizer = _adam_from_recipe(candidate._named_model_parameters(), owned["adam_restore_recipe"], owned["optimizer"])
            for module in (candidate.encoder, candidate.inverse_model, candidate.forward_model):
                for parameter in module.parameters():
                    parameter.grad = None
            candidate.validate_state(owned)
            return candidate
        except (KeyError, TypeError, RuntimeError, AttributeError, OverflowError) as error:
            raise ValueError("ICM restore configuration is malformed") from error

    def prepare_state(self, state: dict[str, Any]) -> _PreparedICM:
        """Validate and own every transported field before any live installation."""
        try:
            _validate_adam_recipe(self._named_model_parameters(), state["adam_restore_recipe"], state["optimizer"])
            state = _owned(state)
            if not isinstance(state, dict) or state.keys() != self.checkpoint_state().keys() or state["schema"] != "icm-state-v4":
                raise ValueError("ICM requires complete icm-state-v4 checkpoint")
            recipe = _validate_adam_candidate(
                self._named_model_parameters(), self.optimizer, state["adam_restore_recipe"], state["optimizer"], exact_options=True
            )
            if not isinstance(state["policy"], dict) or state["policy"].keys() != self.policy.to_dict().keys():
                raise ValueError("ICM checkpoint requires current complete policy fields")
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
            if torch.device(config["device"]).type not in {"cpu", "cuda"}:
                raise ValueError("ICM checkpoint source device must be CPU or CUDA")
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
            origin = state["optimizer_epoch_origin"]
            _number(origin, "optimizer epoch origin", True, 0)
            if origin > updates:
                raise ValueError("ICM optimizer epoch origin exceeds retained lifetime updates")
            epoch_updates = updates - origin
            if counters["consumed_rows"] != updates * self.training_batch_size or counters["mandatory_service_updates"] > updates:
                raise ValueError("ICM checkpoint service counters disagree")
            if counters["admitted_rows"] != counters["consumed_rows"] + counters["dropped_rows"] + len(pending):
                raise ValueError("ICM checkpoint transition conservation failed")
            if type(state["service_clock_unit"]) is not str or state["service_clock_unit"] != self.service_clock_unit:
                raise ValueError("ICM checkpoint service unit differs from destination")
            tick, budget = state["service_position"], state["ordinary_updates_at_position"]
            _number(budget, "ordinary service budget", True, 0)
            if tick is None:
                if counters["admitted_rows"] or updates or budget:
                    raise ValueError("ICM unstarted service has nonempty counters")
            else:
                _number(tick, "service_position", True, 0)
            if self.service_clock_unit == "world_eligible_admission":
                if tick != counters["admitted_rows"] or (tick == 0 and (updates or budget)):
                    raise ValueError("ICM private service position disagrees with admissions")
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
            if not epoch_updates and state["last_loss"] != 0:
                raise ValueError("ICM checkpoint has loss without a successful update")
            encoder = self._model_state(self.encoder, state["encoder"])
            inverse = self._model_state(self.inverse_model, state["inverse_model"])
            forward = self._model_state(self.forward_model, state["forward_model"])
            optimizer = self._optimizer_state((encoder, inverse, forward), state["optimizer"], epoch_updates, recipe)
            owned_pending = deque(_owned(pending))
        except (KeyError, TypeError, RuntimeError, AttributeError, OverflowError) as error:
            raise ValueError("ICM checkpoint is malformed") from error
        candidate = deepcopy(self, {id(self.policy): policy})
        candidate.encoder, candidate.inverse_model, candidate.forward_model, candidate.optimizer = encoder, inverse, forward, optimizer
        candidate.policy, candidate._source_device = policy, config["device"]
        candidate.epsilon, candidate.epsilon_decay, candidate.epsilon_min = state["epsilon"], state["epsilon_decay"], state["epsilon_min"]
        candidate._pending, candidate._counters, candidate._last_loss = owned_pending, dict(counters), float(state["last_loss"])
        candidate._optimizer_epoch_origin = origin
        candidate._service_position, candidate._ordinary_updates_at_position = tick, budget
        return _PreparedICM(self, candidate.__dict__, False)

    def prepare_learning_reset(self, *, fresh: ICMExploration) -> _PreparedICM:
        """Copy real fresh learning without altering service work or consuming RNG.

        The enclosing owner supplies an already-constructed factory candidate and
        owns RNG continuation, boundary authority and final publication freshness.
        """
        if type(fresh) is not ICMExploration or fresh is self:
            raise ValueError("ICM reset requires a distinct actual ICM factory candidate")
        current = self.checkpoint_state()
        self.validate_state(current)
        fresh_state = fresh.checkpoint_state()
        fresh.validate_state(fresh_state)
        if (
            self.policy.to_dict() != fresh.policy.to_dict()
            or {key: value for key, value in self._config().items() if key != "device"}
            != {key: value for key, value in fresh._config().items() if key != "device"}
            or self.device != fresh.device
            or self.service_clock_unit != fresh.service_clock_unit
            or self.epsilon_min != fresh.epsilon_min
            or self.epsilon_decay != fresh.epsilon_decay
        ):
            raise ValueError("ICM reset candidate differs from retained selected policy or geometry")
        for backend in (self, fresh):
            actual = [parameter for group in backend.optimizer.param_groups for parameter in group["params"]]
            expected = backend._parameters()
            if (
                type(backend.optimizer) is not torch.optim.Adam
                or len(actual) != len(expected)
                or any(parameter is not reference for parameter, reference in zip(actual, expected, strict=True))
            ):
                raise ValueError("ICM reset requires actual model/Adam Parameter pairing")
        if (
            any(fresh._counters.values())
            or fresh._optimizer_epoch_origin != 0
            or fresh._pending
            or fresh._last_loss != 0
            or fresh._ordinary_updates_at_position != 0
            or fresh._service_position != (0 if self.service_clock_unit == "world_eligible_admission" else None)
            or fresh.optimizer.state
            or any(parameter.grad is not None for parameter in fresh._parameters())
        ):
            raise ValueError("ICM reset candidate must have genuine fresh learning and no service work")
        for key in ("encoder", "inverse_model", "forward_model", "optimizer", "adam_restore_recipe"):
            current[key] = fresh_state[key]
        current["optimizer_epoch_origin"] = self._counters["optimizer_updates"]
        current["last_loss"] = 0.0
        prepared = self.prepare_state(current)
        for module_name in ("encoder", "inverse_model", "forward_model"):
            for parameter in prepared.attributes[module_name].parameters():
                parameter.grad = None
        return prepared

    def install_state(self, prepared: _PreparedICM) -> None:
        if type(prepared) is not _PreparedICM or prepared.owner is not self or prepared.consumed:
            raise ValueError("ICM prepared state belongs to another destination or was consumed")
        prepared.consumed = True
        self.__dict__ = prepared.attributes

    def load_state(self, state: dict[str, Any]) -> None:
        self.install_state(self.prepare_state(state))
