"""Tests for TrainingV2Config DTO (v2.1 training.yaml)."""

from pathlib import Path

import numpy as np
import pytest
import torch
from pydantic import ValidationError

from townlet.config.training_v2_config import (
    ReplayBufferConfig,
    TrainingV2Config,
    load_training_v2_config,
)
from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
from townlet.training.replay_contract import ReplayRequest
from townlet.training.state import RewardTensor


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

    @pytest.mark.parametrize("capacity,batch_size,min_size", [(100, 64, 32), (2, 3, 1)])
    def test_batch_size_can_exceed_warmup_threshold(self, capacity: int, batch_size: int, min_size: int):
        """Warmup counts retained transitions; the sampling law decides availability."""
        config = ReplayBufferConfig(capacity=capacity, batch_size=batch_size, min_size=min_size)

        assert config.model_dump() == {"capacity": capacity, "batch_size": batch_size, "min_size": min_size}

    @pytest.mark.parametrize("capacity,batch_size,min_size", [(100, 32, 64), (1, 1, 1), (100, 100, 100)])
    def test_existing_valid_replay_geometry_is_preserved(self, capacity: int, batch_size: int, min_size: int):
        config = ReplayBufferConfig(capacity=capacity, batch_size=batch_size, min_size=min_size)

        assert (config.capacity, config.batch_size, config.min_size) == (capacity, batch_size, min_size)

    @pytest.mark.parametrize("field", ["capacity", "batch_size", "min_size"])
    @pytest.mark.parametrize("value", [0, -1])
    def test_replay_counts_must_remain_positive(self, field: str, value: int):
        payload = {"capacity": 4, "batch_size": 1, "min_size": 1}
        payload[field] = value

        with pytest.raises(ValidationError, match=field):
            ReplayBufferConfig(**payload)

    @pytest.mark.parametrize("field", ["capacity", "batch_size", "min_size"])
    def test_replay_counts_remain_required(self, field: str):
        payload = {"capacity": 4, "batch_size": 1, "min_size": 1}
        payload.pop(field)

        with pytest.raises(ValidationError, match=field):
            ReplayBufferConfig(**payload)

    def test_unknown_replay_setting_is_rejected(self):
        with pytest.raises(ValidationError, match="extra_forbidden"):
            ReplayBufferConfig.model_validate({"capacity": 4, "batch_size": 1, "min_size": 1, "replacement": True})

    @pytest.mark.parametrize("sampling_mode", ["independent_with_replacement", "successive_without_replacement"])
    def test_backend_readiness_distinguishes_warmup_from_batch_availability(self, sampling_mode: str):
        config = ReplayBufferConfig(capacity=2, batch_size=3, min_size=1)
        buffer = PrioritizedReplayBuffer(capacity=config.capacity, alpha=0.6, beta=0.4, beta_annealing=False, device=torch.device("cpu"))
        buffer.configure_sampling(sampling_mode=sampling_mode, rng=np.random.default_rng(412), origin="authored")
        request = ReplayRequest(
            batch_size=config.batch_size,
            sequence_length=1,
            min_transitions=config.min_size,
            sampling_mode=sampling_mode,
            sequence_mode="feedforward",
            sequence_objective="transition",
        )
        before = buffer.serialize()["sampling_rng"]

        assert buffer.readiness(request).reason == "warmup"
        with pytest.raises(ValueError, match="warmup"):
            buffer.sample_batch(request)
        assert buffer.serialize()["sampling_rng"] == before

        buffer.push_recorded(
            observations=torch.tensor([[2.0]]),
            actions=torch.tensor([0], dtype=torch.int64),
            rewards=RewardTensor(torch.tensor([1.0]), extrinsic=None, intrinsic=None, shaping=None, is_composed=True),
            next_observations=torch.tensor([[3.0]]),
            dones=torch.tensor([False]),
            next_action_masks=torch.tensor([[True]]),
        )
        ready = buffer.readiness(request)
        assert ready.retained_transitions == ready.sampleable_units == config.min_size
        assert buffer.serialize()["sampling_rng"] == before

        if sampling_mode == "independent_with_replacement":
            assert ready.ready and ready.reason == "ready"
            batch = buffer.sample_batch(request)
            assert batch.observations.shape == (config.batch_size, 1)
            assert batch.unit_ids.tolist() == [0, 0, 0]
            assert batch.sampling.population_size == 1
        else:
            assert not ready.ready and ready.reason == "batch_unavailable"
            with pytest.raises(ValueError, match="batch_unavailable"):
                buffer.sample_batch(request)
            assert buffer.serialize()["sampling_rng"] == before
