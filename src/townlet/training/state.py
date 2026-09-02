"""
State representations for Townlet training.

Contains DTOs for cold path (config, checkpoints, telemetry) using Pydantic
for validation, and hot path (training loop) using PyTorch tensors.
"""

from __future__ import annotations

from typing import Any, TypedDict

import torch
from pydantic import BaseModel, ConfigDict, Field


# LOW-10: TypedDict for environment info dict structure
class EnvInfoDict(TypedDict, total=False):
    """
    Structure for environment info dict returned by step().

    TypedDict with total=False means all fields are optional.
    This documents expected fields without enforcing strict validation
    (since different environments may return different fields).

    Common fields:
        - terminal_reason: str - Why episode ended ("death", "timeout", "success")
        - affordance_visited: str - Last affordance interacted with
        - meter_levels: dict[str, float] - Final meter values at episode end
        - custom_metrics: dict[str, Any] - Environment-specific data
    """

    terminal_reason: str
    affordance_visited: str
    meter_levels: dict[str, float]
    custom_metrics: dict[str, Any]


class RewardTensor:
    """
    Hot path: Encapsulates reward tensors with explicit composition semantics.

    CRIT-07: Replaces the misleading pattern of storing DAC-composed totals as
    'rewards_extrinsic' with zeros for 'rewards_intrinsic'. This DTO makes the
    composition state explicit.

    For DAC-composed rewards: is_composed=True, total contains the composed value,
    components are optional (for debugging/analysis).

    Split component fixtures construct the total explicitly with is_composed=False.

    Attributes:
        total: Combined reward tensor [batch_size] - always present
        extrinsic: Extrinsic (environment) reward component [batch_size] - optional
        intrinsic: Intrinsic (exploration) reward component [batch_size] - optional
        shaping: Shaping bonus component [batch_size] - optional
        is_composed: True if total was pre-composed by DAC, False if needs computation
    """

    __slots__ = ["total", "extrinsic", "intrinsic", "shaping", "is_composed"]

    def __init__(
        self,
        total: torch.Tensor,
        *,
        extrinsic: torch.Tensor | None = None,
        intrinsic: torch.Tensor | None = None,
        shaping: torch.Tensor | None = None,
        is_composed: bool = True,
    ):
        """
        Construct RewardTensor.

        Args:
            total: Combined reward tensor [batch_size]
            extrinsic: Extrinsic reward component (optional)
            intrinsic: Intrinsic reward component (optional)
            shaping: Shaping bonus component (optional)
            is_composed: True if total was pre-composed by DAC
        """
        self.total = total
        self.extrinsic = extrinsic
        self.intrinsic = intrinsic
        self.shaping = shaping
        self.is_composed = is_composed

    @classmethod
    def from_dac(
        cls,
        total: torch.Tensor,
        *,
        extrinsic: torch.Tensor | None = None,
        intrinsic: torch.Tensor | None = None,
        shaping: torch.Tensor | None = None,
    ) -> RewardTensor:
        """
        Create RewardTensor from DAC-composed rewards.

        Args:
            total: Pre-composed total reward from DAC
            extrinsic: Optional extrinsic component (for debugging)
            intrinsic: Optional intrinsic component (for debugging)
            shaping: Optional shaping component (for debugging)
        """
        return cls(
            total=total,
            extrinsic=extrinsic,
            intrinsic=intrinsic,
            shaping=shaping,
            is_composed=True,
        )

    def to(self, device: torch.device) -> RewardTensor:
        """Move all tensors to specified device."""
        return RewardTensor(
            total=self.total.to(device),
            extrinsic=self.extrinsic.to(device) if self.extrinsic is not None else None,
            intrinsic=self.intrinsic.to(device) if self.intrinsic is not None else None,
            shaping=self.shaping.to(device) if self.shaping is not None else None,
            is_composed=self.is_composed,
        )

    def cpu(self) -> RewardTensor:
        """Move all tensors to CPU."""
        return self.to(torch.device("cpu"))

    @property
    def batch_size(self) -> int:
        """Get batch size from total tensor shape."""
        return self.total.shape[0]

    def __repr__(self) -> str:
        components = []
        if self.extrinsic is not None:
            components.append("extrinsic")
        if self.intrinsic is not None:
            components.append("intrinsic")
        if self.shaping is not None:
            components.append("shaping")
        comp_str = ", ".join(components) if components else "none"
        return f"RewardTensor(batch_size={self.batch_size}, is_composed={self.is_composed}, components=[{comp_str}])"


class CurriculumDecision(BaseModel):
    """
    Cold path: Curriculum decision for environment configuration.

    Returned by CurriculumManager to specify environment settings.
    Validated at construction, immutable, serializable.
    """

    model_config = ConfigDict(frozen=True)

    difficulty_level: float = Field(..., ge=0.0, le=1.0, description="Difficulty level from 0.0 (easiest) to 1.0 (hardest)")
    active_meters: list[str] = Field(
        ...,
        min_length=1,
        max_length=6,
        description="Which meters are active (e.g., ['energy', 'hygiene']). "
        "MED-12: max_length=6 corresponds to hardcoded meter count in HAMLET "
        "(energy, hygiene, satiation, money, mood, social). Increase if adding more meters.",
    )
    depletion_multiplier: float = Field(..., gt=0.0, le=10.0, description="Depletion rate multiplier (0.1 = 10x slower, 1.0 = normal)")
    reward_mode: str = Field(..., pattern=r"^(shaped|sparse)$", description="Reward mode: 'shaped' (dense) or 'sparse'")
    reason: str = Field(..., min_length=1, description="Human-readable explanation for this decision")


class PopulationCheckpoint(BaseModel):
    """
    Cold path: Serializable population state for checkpointing.

    Contains all state needed to restore a population training run:
    per-agent curriculum state, exploration state, Pareto frontier, etc.
    """

    model_config = ConfigDict(frozen=True)

    generation: int = Field(..., ge=0, description="Generation number (for genetic algorithms)")
    num_agents: int = Field(..., ge=1, le=1000, description="Number of agents in population (1-1000)")
    agent_ids: list[str] = Field(..., description="List of agent identifiers")
    curriculum_states: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Per-agent curriculum manager state")
    exploration_states: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Per-agent exploration strategy state")
    pareto_frontier: list[str] = Field(default_factory=list, description="Agent IDs on Pareto frontier (non-dominated solutions)")
    metrics_summary: dict[str, float] = Field(default_factory=dict, description="Summary metrics (avg_survival, avg_reward, etc.)")


class BatchedAgentState:
    """
    Hot path: Vectorized agent state for GPU training loops.

    All data is batched tensors (batch_size = num_agents).
    Optimized for GPU operations, minimal validation overhead.
    Use slots for memory efficiency.
    """

    __slots__ = [
        "observations",
        "actions",
        "rewards",
        "dones",
        "epsilons",
        "intrinsic_rewards",
        "survival_times",
        "device",
        "info",
    ]

    def __init__(
        self,
        observations: torch.Tensor,  # [batch, obs_dim]
        actions: torch.Tensor,  # [batch]
        rewards: torch.Tensor,  # [batch]
        dones: torch.Tensor,  # [batch] bool
        epsilons: torch.Tensor,  # [batch]
        intrinsic_rewards: torch.Tensor,  # [batch]
        survival_times: torch.Tensor,  # [batch]
        device: torch.device,
        info: dict | None = None,  # Environment info dict (see EnvInfoDict for structure)
    ):
        """
        Construct batched agent state.

        All tensors must be on the same device.
        No validation in __init__ for performance (hot path).

        LOW-10: info dict structure documented in EnvInfoDict TypedDict.
        HIGH-09: Removed curriculum_difficulties field (dead code - never populated).
        """
        self.observations = observations
        self.actions = actions
        self.rewards = rewards
        self.dones = dones
        self.epsilons = epsilons
        self.intrinsic_rewards = intrinsic_rewards
        self.survival_times = survival_times
        self.device = device
        self.info = info if info is not None else {}

    @property
    def batch_size(self) -> int:
        """Get batch size from observations shape."""
        return self.observations.shape[0]

    def to(self, device: torch.device) -> BatchedAgentState:
        """
        Move all tensors to specified device.

        Returns new BatchedAgentState (tensors are immutable after .to()).
        """
        return BatchedAgentState(
            observations=self.observations.to(device),
            actions=self.actions.to(device),
            rewards=self.rewards.to(device),
            dones=self.dones.to(device),
            epsilons=self.epsilons.to(device),
            intrinsic_rewards=self.intrinsic_rewards.to(device),
            survival_times=self.survival_times.to(device),
            device=device,
            info=self.info,  # CRIT-05: Preserve info dict on device transfer
        )

    # LOW-09: Deleted detach_cpu_summary() - dead code, never called in production
