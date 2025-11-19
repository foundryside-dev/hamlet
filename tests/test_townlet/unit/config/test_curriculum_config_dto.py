"""Tests for CurriculumConfig DTO (Cycle 4)."""

import pytest
from pydantic import ValidationError

from tests.test_townlet.unit.config.fixtures import (
    PRODUCTION_CONFIG_PACKS,
    VALID_CURRICULUM_PARAMS,
    make_temp_yaml,
    make_valid_params,
)
from townlet.config.curriculum import CurriculumConfig, load_curriculum_config


class TestCurriculumConfigValidation:
    """Test CurriculumConfig schema validation."""

    def test_all_fields_required(self):
        """All fields must be explicitly specified (no-defaults principle)."""
        with pytest.raises(ValidationError) as exc_info:
            CurriculumConfig()

        assert "curriculum" in str(exc_info.value)

    def test_valid_config(self):
        """Valid config with all required fields loads successfully."""
        config = CurriculumConfig(curriculum=VALID_CURRICULUM_PARAMS)
        assert config.curriculum.active_vision == "global"
        assert config.curriculum.vision_range == 0.5
        assert config.curriculum.active_temporal is False
        assert config.curriculum.day_length is None

    def test_vision_range_bounds(self):
        """vision_range must be within [0,1]."""
        with pytest.raises(ValidationError):
            CurriculumConfig(curriculum=make_valid_params(VALID_CURRICULUM_PARAMS, vision_range=-0.1))
        with pytest.raises(ValidationError):
            CurriculumConfig(curriculum=make_valid_params(VALID_CURRICULUM_PARAMS, vision_range=1.1))

    def test_day_length_required_when_temporal_active(self):
        """active_temporal=true requires day_length."""
        with pytest.raises(ValidationError):
            CurriculumConfig(curriculum=make_valid_params(VALID_CURRICULUM_PARAMS, active_temporal=True, day_length=None))

    def test_day_length_must_be_positive_when_provided(self):
        with pytest.raises(ValidationError):
            CurriculumConfig(curriculum=make_valid_params(VALID_CURRICULUM_PARAMS, active_temporal=True, day_length=0))


class TestCurriculumConfigLoading:
    """Test loading from YAML files."""

    def test_load_from_yaml(self, tmp_path):
        """Load curriculum config from YAML file."""
        make_temp_yaml(tmp_path, "curriculum", VALID_CURRICULUM_PARAMS)

        config = load_curriculum_config(tmp_path)
        assert config.curriculum.active_vision == VALID_CURRICULUM_PARAMS["active_vision"]

    def test_load_from_real_config_L0(self):  # noqa: N802
        """Load curriculum config from real L0_0_minimal config pack."""
        config_dir = PRODUCTION_CONFIG_PACKS["L0_0_minimal"]
        if not config_dir.exists():
            pytest.skip(f"Config pack not found: {config_dir}")

        config = load_curriculum_config(config_dir)
        assert config.curriculum.active_vision in {"global", "partial"}
        assert 0.0 <= config.curriculum.vision_range <= 1.0

    def test_load_from_all_production_configs(self):
        """Verify all production config packs have valid curriculum sections."""
        missing_packs = []
        validated_packs = 0
        for pack_name, config_dir in PRODUCTION_CONFIG_PACKS.items():
            if not config_dir.exists():
                missing_packs.append(pack_name)
                continue

            # Should load without errors
            config = load_curriculum_config(config_dir)
            assert config.curriculum.active_vision in {"global", "partial"}, f"{pack_name}: invalid active_vision"
            assert 0.0 <= config.curriculum.vision_range <= 1.0, f"{pack_name}: invalid vision_range"
            validated_packs += 1

        if validated_packs == 0:
            missing = ", ".join(sorted(missing_packs)) if missing_packs else "unknown packs"
            pytest.skip(f"No production config packs available for curriculum validation: {missing}")

    def test_load_missing_field_error(self, tmp_path):
        """Missing required field raises clear error."""
        import yaml

        curriculum_yaml = tmp_path / "curriculum.yaml"

        # Create YAML with missing fields
        with open(curriculum_yaml, "w") as f:
            yaml.dump(
                {
                    "curriculum": {
                        "version": "1.0",
                        "active_vision": "global",
                        # Missing: vision_range, active_temporal, day_length
                    }
                },
                f,
            )

        with pytest.raises(ValueError) as exc_info:
            load_curriculum_config(tmp_path)

        error = str(exc_info.value)
        assert "curriculum" in error.lower() or "validation" in error.lower()
