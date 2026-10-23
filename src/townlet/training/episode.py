"""Shared immutable outcomes for completed population episode lanes."""

from dataclasses import dataclass
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
