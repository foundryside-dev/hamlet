"""Curriculum factory helpers for v2.1 training packs.

Selects the appropriate curriculum implementation (static vs adversarial)
based on TrainingV2Config.curriculum.strategy, so that behavior is driven
by configuration rather than hard-coded defaults.
"""

from __future__ import annotations

from typing import Final

import torch

from townlet.config.training_v2_config import TrainingV2Config
from townlet.curriculum.adversarial import AdversarialCurriculum
from townlet.curriculum.base import CurriculumManager
from townlet.curriculum.static import StaticCurriculum

DEFAULT_STATIC_DIFFICULTY: Final[float] = 0.5


def build_curriculum(
    training: TrainingV2Config,
    *,
    max_steps_per_episode: int,
    device: torch.device,
) -> CurriculumManager:
    """Build a CurriculumManager from TrainingV2Config.

    Args:
        training: Parsed v2.1 training configuration for the current level.
        max_steps_per_episode: Episode length from training.training_loop.
        device: Torch device for any curriculum-internal tensors.

    Returns:
        A CurriculumManager instance (StaticCurriculum or AdversarialCurriculum).

    Notes:
        - For strategy="static", this returns a StaticCurriculum with fixed
          difficulty and meter set. Future work may expose these knobs in
          TrainingV2Config.
        - For strategy="adversarial", this returns AdversarialCurriculum
          configured with max_steps_per_episode and device. The per-stage
          advancement/retreat thresholds remain defined in AdversarialCurriculum;
          additional wiring from training.curriculum.adversarial can be added
          without changing call sites.
    """
    strategy_cfg = training.curriculum
    strategy = strategy_cfg.strategy

    if strategy == "static":
        # Static curriculum: no adaptation, fixed difficulty.
        # Use StaticCurriculum defaults for now; they already cover the full
        # meter set used by the environment. This keeps behavior explicit and
        # makes the strategy flag meaningful without introducing new schema.
        return StaticCurriculum(difficulty_level=DEFAULT_STATIC_DIFFICULTY)

    if strategy == "adversarial":
        adversarial_cfg = strategy_cfg.adversarial
        if adversarial_cfg is None:
            raise ValueError("training.curriculum.adversarial is required when " "curriculum.strategy='adversarial'.")

        curriculum = AdversarialCurriculum(
            max_steps_per_episode=max_steps_per_episode,
            device=device,
        )
        curriculum.configure_from_training(adversarial_cfg)
        return curriculum

    raise ValueError(f"Unsupported curriculum.strategy: {strategy!r}")
