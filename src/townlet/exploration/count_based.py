"""Instance-owned finite count novelty; the caller supplies eligible rows.

Quantization floors the exact ratio of represented finite floats, so signed bins
remain arbitrary-precision integers even when division would overflow or round
across a boundary. Provider construction does not supply world-bank routing.
"""

from __future__ import annotations

import math
from collections import OrderedDict
from collections.abc import Mapping
from typing import Any

import torch

from townlet.config.exploration_policy import ExplorationServiceReceipt, IntrinsicTransitionContext, ResolvedExplorationPolicy
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration

_STATE_FIELDS = frozenset(
    (
        "schema_version",
        "policy_identity",
        "policy",
        "quantization_width",
        "max_entries",
        "epsilon",
        "epsilon_decay",
        "epsilon_min",
        "counts",
        "lru",
        "eviction_count",
    )
)


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} requires a finite number")
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} requires a finite number") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} requires a finite number")
    return result


def _integer(value: Any, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} requires an integer >= {minimum}")
    return value


def _key(value: Any) -> tuple[int, ...]:
    if (
        not isinstance(value, tuple)
        or not value
        or any(isinstance(bin_value, bool) or not isinstance(bin_value, int) for bin_value in value)
    ):
        raise ValueError("count keys require nonempty tuples of signed integer bins")
    return value


class CountExploration(EpsilonGreedyExploration):
    """Bounded LRU counts with pure no-stat queries and no neural training."""

    def __init__(self, policy: ResolvedExplorationPolicy, *, quantization_width: float, max_entries: int, device: torch.device | str):
        if not isinstance(policy, ResolvedExplorationPolicy) or policy.strategy != "count_based":
            raise ValueError("CountExploration requires a resolved count_based policy")
        width = _finite_number(quantization_width, "quantization_width")
        capacity = _integer(max_entries, "max_entries", 1)
        if width <= 0 or width != policy.provider_parameters["quantization_width"] or capacity != policy.provider_parameters["max_entries"]:
            raise ValueError("count configuration must match the selected resolved policy")
        self.policy = ResolvedExplorationPolicy.from_dict(policy.to_dict())
        self.device = torch.device(device)
        self._quantization_width = width
        self._max_entries = capacity
        self._width_numerator, self._width_denominator = width.as_integer_ratio()
        self._counts: OrderedDict[tuple[int, ...], int] = OrderedDict()
        self._eviction_count = 0
        super().__init__(epsilon=policy.epsilon_start, epsilon_decay=policy.epsilon_decay, epsilon_min=policy.epsilon_end)

    @property
    def eviction_count(self) -> int:
        return self._eviction_count

    def compute_intrinsic_rewards(self, observations: torch.Tensor, *args: Any, **kwargs: Any) -> torch.Tensor:
        """Return 1/sqrt(next count); only explicit admissions change counts/LRU."""
        if len(args) > 1 or set(kwargs) - {"update_stats"}:
            raise TypeError("count rewards accept observations and one update_stats flag")
        if args and "update_stats" in kwargs:
            raise TypeError("update_stats was supplied more than once")
        if args:
            update_stats = args[0]
        elif "update_stats" in kwargs:
            update_stats = kwargs["update_stats"]
        else:
            update_stats = False  # Inherited observation protocol: omitted flag is a pure query.
        if not isinstance(update_stats, bool):
            raise ValueError("update_stats requires a bool")
        if not isinstance(observations, torch.Tensor) or observations.ndim != 2 or observations.shape[1] == 0:
            raise ValueError("count observations require shape [N,D] with D > 0")
        if not observations.is_floating_point() or not bool(torch.isfinite(observations).all()):
            raise ValueError("count observations require finite floating values")
        if observations.device.type != self.device.type or (
            self.device.index is not None and observations.device.index != self.device.index
        ):
            raise ValueError("count observations must use the configured device")
        # Prepare every key before the first mutation, including later bad rows.
        keys: list[tuple[int, ...]] = []
        for row in observations.detach().cpu().tolist():
            bins = []
            for value in row:
                numerator, denominator = value.as_integer_ratio()
                bins.append((numerator * self._width_denominator) // (denominator * self._width_numerator))
            keys.append(tuple(bins))
        rewards = []
        for key in keys:
            if key in self._counts:
                count = self._counts[key] + 1
            else:
                count = 1
            # log accepts arbitrary-precision positive counts without float overflow.
            rewards.append(math.exp(-0.5 * math.log(count)))
            if update_stats:
                if key not in self._counts and len(self._counts) == self._max_entries:
                    self._counts.popitem(last=False)
                    self._eviction_count += 1
                self._counts[key] = count
                self._counts.move_to_end(key)
        return torch.tensor(rewards, dtype=observations.dtype, device=observations.device)

    def admit_and_service(self, context: IntrinsicTransitionContext) -> ExplorationServiceReceipt:
        """COUNT has no predictor queue, optimizer, or second count admission."""
        if not isinstance(context, IntrinsicTransitionContext):
            raise ValueError("count service requires an IntrinsicTransitionContext")
        return ExplorationServiceReceipt(
            provider="count_based",
            admitted_rows=0,
            consumed_rows=0,
            dropped_rows=0,
            pending_rows=0,
            optimizer_updates=0,
            mandatory_service_updates=0,
            last_loss=0.0,
        )

    def checkpoint_state(self) -> dict[str, Any]:
        """Return independent native checkpoint data, including full provenance."""
        return {
            "schema_version": "count-state-v1",
            "policy_identity": self.policy.policy_identity,
            "policy": self.policy.to_dict(),
            "quantization_width": self._quantization_width,
            "max_entries": self._max_entries,
            **super().checkpoint_state(),
            "counts": dict(self._counts),
            "lru": list(self._counts),
            "eviction_count": self._eviction_count,
        }

    def load_state(self, state: dict[str, Any]) -> None:
        """Validate the complete candidate before changing any owned state."""
        if not isinstance(state, Mapping) or set(state) != _STATE_FIELDS or state["schema_version"] != "count-state-v1":
            raise ValueError("count checkpoint requires the complete count-state-v1 schema")
        try:
            restored_policy = ResolvedExplorationPolicy.from_dict(state["policy"])
        except (TypeError, ValueError, KeyError, AttributeError, OverflowError) as error:
            raise ValueError("invalid count checkpoint policy") from error
        identity = restored_policy.policy_identity
        if restored_policy.strategy != "count_based" or state["policy_identity"] != identity or identity != self.policy.policy_identity:
            raise ValueError("count checkpoint active policy identity disagrees with the provider")
        width = _finite_number(state["quantization_width"], "quantization_width")
        capacity = _integer(state["max_entries"], "max_entries", 1)
        if width != self._quantization_width or capacity != self._max_entries:
            raise ValueError("count checkpoint configuration disagrees with the provider")
        if (
            width != restored_policy.provider_parameters["quantization_width"]
            or capacity != restored_policy.provider_parameters["max_entries"]
        ):
            raise ValueError("count checkpoint configuration disagrees with its policy")
        epsilon = _finite_number(state["epsilon"], "epsilon")
        decay = _finite_number(state["epsilon_decay"], "epsilon_decay")
        minimum = _finite_number(state["epsilon_min"], "epsilon_min")
        if (
            decay != restored_policy.epsilon_decay
            or minimum != restored_policy.epsilon_end
            or not minimum <= epsilon <= restored_policy.epsilon_start
        ):
            raise ValueError("count checkpoint epsilon state disagrees with its policy")
        evictions = _integer(state["eviction_count"], "eviction_count", 0)
        counts, lru = state["counts"], state["lru"]
        if not isinstance(counts, dict) or not isinstance(lru, list) or len(counts) > capacity:
            raise ValueError("count checkpoint requires bounded counts and an ordered LRU list")
        for key, count in counts.items():
            _key(key)
            _integer(count, "count", 1)
        for key in lru:
            _key(key)
        if len(lru) != len(counts) or len(set(lru)) != len(lru) or set(lru) != set(counts):
            raise ValueError("count checkpoint LRU must contain every admitted key exactly once")
        prepared_counts = OrderedDict((key, counts[key]) for key in lru)
        self.policy = restored_policy
        self.epsilon, self.epsilon_decay, self.epsilon_min = epsilon, decay, minimum
        self._counts, self._eviction_count = prepared_counts, evictions
