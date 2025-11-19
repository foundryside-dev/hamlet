"""Tests for ExplorationConfig DTO (Cycle 5)."""

import pytest
from pydantic import ValidationError

from tests.test_townlet.unit.config.fixtures import (
    PRODUCTION_CONFIG_PACKS,
    VALID_EXPLORATION_PARAMS,
    make_temp_yaml,
    make_valid_params,
)
from townlet.config.exploration import ExplorationConfig, load_exploration_config


class TestExplorationConfigValidation:
    """Test ExplorationConfig schema validation (no-defaults principle)."""

    def test_all_fields_required(self):
        """All fields must be explicitly specified (no defaults)."""
        with pytest.raises(ValidationError) as exc_info:
            ExplorationConfig()

        assert "epsilon_start" in str(exc_info.value)

    def test_valid_config(self):
        """Valid config with all required fields loads successfully."""
        config = ExplorationConfig(**VALID_EXPLORATION_PARAMS)
        assert config.epsilon_start == 1.0
        assert config.epsilon_end == 0.01
        assert config.epsilon_decay == 0.995

    def test_epsilon_bounds(self):
        """epsilon values must be within [0,1] and start >= end."""
        with pytest.raises(ValidationError):
            ExplorationConfig(**make_valid_params(VALID_EXPLORATION_PARAMS, epsilon_start=-0.1))
        with pytest.raises(ValidationError):
            ExplorationConfig(**make_valid_params(VALID_EXPLORATION_PARAMS, epsilon_end=1.5))
        with pytest.raises(ValidationError):
            ExplorationConfig(**make_valid_params(VALID_EXPLORATION_PARAMS, epsilon_decay=1.5))
        # start >= end requirement
        with pytest.raises(ValidationError):
            ExplorationConfig(**make_valid_params(VALID_EXPLORATION_PARAMS, epsilon_start=0.1, epsilon_end=0.5))


class TestExplorationConfigLoading:
    """Test loading ExplorationConfig from YAML."""

    def test_load_from_yaml(self, tmp_path):
        """Load exploration config from YAML file."""
        # Create exploration section in training.yaml
        yaml_path = make_temp_yaml(tmp_path, "training", {"exploration": VALID_EXPLORATION_PARAMS})
        training_yaml = tmp_path / "training.yaml"
        yaml_path.rename(training_yaml)

        config = load_exploration_config(tmp_path)
        assert config.epsilon_start == VALID_EXPLORATION_PARAMS["epsilon_start"]

    def test_load_from_real_config_L0(self):  # noqa: N802
        """Load exploration config from real L0_0_minimal config pack."""
        config_dir = PRODUCTION_CONFIG_PACKS["L0_0_minimal"]
        if not config_dir.exists():
            pytest.skip(f"Config pack not found: {config_dir}")

        config = load_exploration_config(config_dir)
        # Validate it's a valid ExplorationConfig (fields are required, so if it loads it's valid)
        assert 0.0 <= config.epsilon_end <= config.epsilon_start <= 1.0
        assert 0.0 < config.epsilon_decay < 1.0

    def test_load_from_all_production_configs(self):
        """Verify all production config packs have valid exploration sections."""
        missing_packs = []
        validated_packs = 0
        for pack_name, config_dir in PRODUCTION_CONFIG_PACKS.items():
            if not config_dir.exists():
                missing_packs.append(pack_name)
                continue

            # Should load without errors
            config = load_exploration_config(config_dir)
            assert 0.0 <= config.epsilon_end <= config.epsilon_start <= 1.0, f"{pack_name}: epsilon bounds invalid"
            assert 0.0 < config.epsilon_decay < 1.0, f"{pack_name}: epsilon_decay must be in (0,1)"
            validated_packs += 1

        if validated_packs == 0:
            missing = ", ".join(sorted(missing_packs)) if missing_packs else "unknown packs"
            pytest.skip(f"No production config packs available for exploration validation: {missing}")

    def test_load_missing_field_error(self, tmp_path):
        """Missing required field raises clear error."""
        import yaml

        config_dir = tmp_path
        training_yaml = config_dir / "training.yaml"

        # Create YAML with missing fields
        with open(training_yaml, "w") as f:
            yaml.dump(
                {
                    "training": {
                        "exploration": {
                            "epsilon_start": 1.0,
                            # Missing epsilon_end / epsilon_decay
                        }
                    }
                },
                f,
            )

        with pytest.raises(ValueError) as exc_info:
            load_exploration_config(config_dir)

        error = str(exc_info.value)
        assert "exploration" in error.lower() or "validation" in error.lower()
