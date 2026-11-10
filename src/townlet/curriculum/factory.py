"""Construct current curricula from explicit resolved policy declarations."""

from __future__ import annotations

import torch

from townlet.config.bac_options import CurriculumOptions, StaticBaselinePolicy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.curriculum.adversarial import AdversarialCurriculum
from townlet.curriculum.base import CurriculumManager
from townlet.curriculum.static import StaticCurriculum


def build_curriculum(
    training: TrainingV2Config,
    *,
    curriculum_options: CurriculumOptions,
    static_policy: StaticBaselinePolicy,
    device: torch.device,
) -> CurriculumManager:
    """Build an uninitialized manager; the caller initializes its actual population.

    Resolve options and the roster-bound static baseline at the configuration
    boundary. This consumer never selects omitted values or probes old APIs.
    Static reward and meter metadata are transported without claiming their
    application mechanics are qualified. Programmatic StaticCurriculum callers
    may continue supplying their own supported fixed parameters directly.
    """
    if curriculum_options.commit_mode != "completion":
        raise ValueError("curriculum_options.commit_mode must be resolved to completion")
    if curriculum_options.difficulty_mode not in ("stage_band", "rate_limited"):
        raise ValueError("curriculum_options.difficulty_mode must be resolved")
    strategy_cfg = training.curriculum
    if strategy_cfg.strategy == "static":
        return StaticCurriculum(
            commit_mode=curriculum_options.commit_mode,
            difficulty_level=static_policy.difficulty_level,
            reward_mode=static_policy.reward_mode,
            active_meters=list(static_policy.active_meters),
            depletion_multiplier=static_policy.depletion_multiplier,
        )
    if strategy_cfg.strategy == "adversarial":
        adversarial_cfg = strategy_cfg.adversarial
        if adversarial_cfg is None:
            raise ValueError("training.curriculum.adversarial is required when curriculum.strategy='adversarial'")
        return AdversarialCurriculum(
            commit_mode=curriculum_options.commit_mode,
            difficulty_mode=curriculum_options.difficulty_mode,
            adaptation_rate=adversarial_cfg.adaptation_rate,
            min_difficulty=adversarial_cfg.min_difficulty,
            max_difficulty=adversarial_cfg.max_difficulty,
            survival_advance_threshold=adversarial_cfg.survival_advance_threshold,
            survival_retreat_threshold=adversarial_cfg.survival_retreat_threshold,
            entropy_gate=adversarial_cfg.entropy_gate,
            min_steps_at_stage=adversarial_cfg.min_steps_at_stage,
            device=device,
        )
    raise ValueError(f"Unsupported curriculum.strategy: {strategy_cfg.strategy!r}")
