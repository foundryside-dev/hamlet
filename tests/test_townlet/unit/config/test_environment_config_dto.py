"""Tests for EnvironmentConfig DTO (v2.1 environment.yaml)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from townlet.config.environment_config import EnvironmentConfig


class TestEnvironmentConfigLoading:
    """Test loading EnvironmentConfig from real v2.1 YAML."""

    def test_load_from_model_config_environment_yaml(self):
        """Load environment.yaml from the canonical model_config pack."""
        env_path = Path("configs/test/model_config/environment.yaml")
        assert env_path.exists(), f"environment.yaml not found at {env_path}"

        config = EnvironmentConfig.from_yaml(env_path)
        root = config.environment

        # Basic shape checks
        assert root.version == "1.0"
        assert len(root.meters) == 8
        assert len(root.cascade_graph) > 0
        assert len(root.modulation_graph) > 0
        assert len(root.affordances) >= 1
        assert len(root.variables) >= 1
        assert len(root.cues) >= 1

        # Meters and affordances match expected vocabulary
        meter_names = {m.name for m in root.meters}
        assert {"energy", "health", "satiation", "hygiene", "money", "fitness", "mood", "social"} <= meter_names

        affordance_names = {a.name for a in root.affordances}
        assert {"EAT", "SLEEP", "WORK"}.issubset(affordance_names)

        # At least one cascade and modulation edge references valid meters/affordances
        cascade = next(c for c in root.cascade_graph if c.source == "satiation" and c.target == "health")
        assert "hunger" in cascade.description.lower()

        modulation = next(m for m in root.modulation_graph if m.bar == "energy")
        assert "WORK" in {a.upper() for a in modulation.affordances}

    def test_environment_config_bars_and_variables_are_consistent(self):
        """Meters in environment.yaml should align with VFS variables."""
        env_path = Path("configs/default_curriculum/environment.yaml")
        assert env_path.exists(), f"environment.yaml not found at {env_path}"

        config = EnvironmentConfig.from_yaml(env_path)
        root = config.environment

        meter_names = {m.name for m in root.meters}
        variable_names = {v.name for v in root.variables}

        # All meter-backed variables should have corresponding meters
        assert "deficit_energy" in variable_names
        assert "deficit_satiation" in variable_names
        assert "time_since_last_eat" in variable_names
        assert "time_since_last_sleep" in variable_names

        # Simple consistency check: variables must reference valid meter concepts
        assert "energy" in meter_names
        assert "satiation" in meter_names

    def test_environment_config_rejects_extra_meter_fields(self, tmp_path: Path):
        """Extra fields in meter definitions should be rejected (extra=forbid)."""
        env_yaml = tmp_path / "environment.yaml"
        env_yaml.write_text(
            """
environment:
  version: "1.0"
  meters:
    - name: energy
      description: "Energy"
      range_type: normalized
      extra_field: "not allowed"
  cascade_graph: []
  modulation_graph: []
  affordances: []
  variables: []
  cues: []
"""
        )

        with pytest.raises(ValidationError):
            EnvironmentConfig.from_yaml(env_yaml)

    def test_variable_normalization_range_requires_two_values(self, tmp_path: Path):
        """Normalization.range must contain exactly two values [min, max]."""
        env_yaml = tmp_path / "environment.yaml"
        env_yaml.write_text(
            """
environment:
  version: "1.0"
  meters:
    - name: energy
      description: "Energy"
      range_type: normalized
  cascade_graph: []
  modulation_graph: []
  affordances: []
  variables:
    - name: deficit_energy
      type: scalar
      dims: 1
      scope: agent
      description: "How far below target energy"
      normalization:
        method: clip
        range: [0.0]
  cues: []
"""
        )

        with pytest.raises(ValidationError):
            EnvironmentConfig.from_yaml(env_yaml)
