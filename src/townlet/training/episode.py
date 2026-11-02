"""Shared immutable outcomes for completed population episode lanes."""

import math
from dataclasses import dataclass, replace
from numbers import Real
from typing import Literal

import torch

CompletionReason = Literal["authored_terminal", "retirement", "cap", "budget", "shutdown", "checkpoint"]
RunnerCompletionReason = Literal["cap", "budget", "shutdown", "checkpoint"]


@dataclass(frozen=True)
class EpisodeCompletion:
    """An owned CPU snapshot of one nonempty lane at its completion boundary."""

    agent_idx: int
    reason: CompletionReason
    survival_time: int
    final_observation: torch.Tensor
    final_meters: torch.Tensor


@dataclass(frozen=True)
class LaneOutcome:
    """An owned completion envelope with explicit caller-supplied world identity.

    Tensor readings are detached CPU copies. Frozen fields prevent rebinding;
    consumers must treat the owned tensor readings as immutable event data.
    """

    outcome: EpisodeCompletion
    batch_episode: int
    planned_horizon: int
    reward_total: float
    reward_extrinsic: float
    reward_intrinsic: float
    reward_shaping: float
    policy_entropy: float
    world_id: str
    world_episode_seq: int

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, EpisodeCompletion):
            raise ValueError("outcome must be an EpisodeCompletion")
        for name, minimum in (("batch_episode", 0), ("planned_horizon", 1), ("world_episode_seq", 0)):
            value = getattr(self, name)
            if type(value) is not int or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")
        if not isinstance(self.world_id, str) or not self.world_id.strip():
            raise ValueError("world_id must be a concrete nonempty string")
        for name in ("reward_total", "reward_extrinsic", "reward_intrinsic", "reward_shaping", "policy_entropy"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
                raise ValueError(f"{name} must be a finite real value")
            object.__setattr__(self, name, float(value))
        object.__setattr__(
            self,
            "outcome",
            replace(
                self.outcome,
                final_observation=self.outcome.final_observation.detach().cpu().clone(),
                final_meters=self.outcome.final_meters.detach().cpu().clone(),
            ),
        )
