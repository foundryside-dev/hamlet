"""Tests for vision radius bounds (ENV-002) in VectorizedHamletEnv."""


def _set_partial_with_vision(vision_range: float):
    """Create curriculum mutator for partial observability with specific vision range."""

    def mutate(curriculum):
        curriculum["curriculum"]["active_vision"] = "partial"
        curriculum["curriculum"]["vision_range"] = vision_range

    return mutate

    # Note: test_vision_radius_exceeds_max_raises_error was removed because:
    # - vision_range is validated to be <= 1.0 by CurriculumConfig
    # - grid size is validated to be <= 10000 cells (100x100)
    # - With these constraints, max radius = ceil(1.0 * 50) = 50, which is exactly
    #   at MAX_VISION_RADIUS, so we can never exceed it through valid configs.
    # The validation in vectorized_env.py exists as a safety net for future changes
    # to upstream validation, but cannot be tested through normal config paths.
