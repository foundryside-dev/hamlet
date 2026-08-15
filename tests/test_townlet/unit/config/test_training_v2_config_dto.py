"""Tests for TrainingV2Config DTO (v2.1 training.yaml)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from townlet.config.training_v2_config import (
    ReplayBufferConfig,
    TrainingV2Config,
    load_training_v2_config,
)


class TestTrainingV2ConfigLoading:
    """Test loading TrainingV2Config from real v2.1 YAML."""

    def test_load_from_model_config_training_yaml(self):
        """Load training.yaml from the canonical model_config level."""
        level_dir = Path("configs/test/model_config/levels/L0_test")
        assert level_dir.exists(), f"Level directory not found: {level_dir}"

        config = load_training_v2_config(level_dir)

        assert config.version == "1.0"
        assert config.population.size == 8
        assert config.randomize_affordances is True
        assert "REST" in (config.enabled_actions.custom if config.enabled_actions is not None else [])

        # Spot-check nested sections against training.yaml
        assert config.q_learning.gamma == pytest.approx(0.99)
        assert config.replay_buffer.capacity == 100_000
        assert config.training_loop.max_episodes == 10_000
        assert config.training_loop.max_steps_per_episode == 1_000

    def test_seed_is_required(self):
        """A training config without `seed` must fail loudly (no-defaults principle).

        The seed is THE reproducibility parameter: a hidden or optional seed is a
        non-reproducible run by construction (hamlet-834108b55a). It also rides
        `training_hash` into checkpoint identity, so it must live in config.
        """
        level_dir = Path("configs/test/model_config/levels/L0_test")
        config = load_training_v2_config(level_dir)
        data = config.model_dump()

        data.pop("seed")

        with pytest.raises(ValidationError, match="seed"):
            TrainingV2Config(**data)

    def test_seed_loads_from_yaml(self):
        """The shipped test pack declares an explicit seed and it round-trips."""
        level_dir = Path("configs/test/model_config/levels/L0_test")
        config = load_training_v2_config(level_dir)
        assert isinstance(config.seed, int)

    def test_enabled_affordances_must_not_be_null(self):
        """enabled_affordances must be provided as a list, not null."""
        level_dir = Path("configs/test/model_config/levels/L0_test")
        config = load_training_v2_config(level_dir)
        data = config.model_dump()

        data["enabled_affordances"] = None

        with pytest.raises(ValidationError):
            TrainingV2Config(**data)

    def test_load_training_v2_missing_required_fields_errors(self, tmp_path: Path):
        """Missing required sections (e.g., population) should raise clear errors."""
        config_dir = tmp_path / "level"
        config_dir.mkdir()

        training_yaml = config_dir / "training.yaml"
        training_yaml.write_text("""
run_metadata:
  output_subdir: test-level
training:
  version: "1.0"
  # population, replay_buffer, exploration, etc. deliberately omitted
""")

        with pytest.raises(ValueError) as exc_info:
            load_training_v2_config(config_dir)

        error = str(exc_info.value)
        # Pydantic error details should reference at least one missing field
        assert "population" in error or "field required" in error.lower()


class TestReplayBufferConfigValidation:
    """Direct tests for ReplayBufferConfig invariants."""

    def test_min_size_must_not_exceed_capacity(self):
        with pytest.raises(ValueError, match="must be <= capacity"):
            ReplayBufferConfig(capacity=100, batch_size=32, min_size=200)

    def test_batch_size_must_not_exceed_min_size(self):
        with pytest.raises(ValueError, match="must be <= min_size"):
            ReplayBufferConfig(capacity=100, batch_size=64, min_size=32)
