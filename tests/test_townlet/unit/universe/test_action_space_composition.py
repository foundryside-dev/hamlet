"""
Test suite for action space composition, specifically meter reference validation.

Tests for JANK-02: Action costs/effects with unknown meters should produce compile errors.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler


@pytest.fixture
def temp_config_with_global_actions():
    """Create a temporary config directory and manage actions.yaml safely."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir)

        # Copy static v2.1 action-space test pack as the base (known to compile successfully)
        repo_root = Path(__file__).parent.parent.parent.parent.parent
        source_config = repo_root / "configs" / "test" / "action_space" / "grid2d"

        # Copy entire experiment pack structure (experiment.yaml, stratum.yaml, levels/, etc.)
        shutil.copytree(source_config, config_path, dirs_exist_ok=True)

        actions_path = config_path / "actions.yaml"
        backup_content = actions_path.read_text() if actions_path.exists() else None

        try:
            yield {
                "config_dir": config_path,
                "actions_path": actions_path,
            }
        finally:
            # Restore original content if we had a backup
            if backup_content is not None:
                actions_path.write_text(backup_content)
            # No cleanup/deletion - CI environment is transitory


class TestActionMeterValidation:
    """
    Test that actions with unknown meter references produce UAC-ACT-002 errors.

    Phase 3-4: TDD implementation and verification for JANK-02 fix.
    """

    def test_action_with_unknown_meter_in_costs_fails_compilation(self, temp_config_with_global_actions):
        """
        JANK-02: Action with unknown meter in costs should produce UAC-ACT-002 error.

        Verifies strict validation:
        - Compilation fails with UAC-ACT-002 error code
        - Error message includes action name and meter name
        - Error location references global_actions.yaml
        """
        config_dir = temp_config_with_global_actions["config_dir"]
        actions_path = temp_config_with_global_actions["actions_path"]

        # Create actions.yaml with typo'd meter name in costs
        actions_path.write_text("""
actions:
  version: "1.0"
  substrate_actions:
    inherit: true
  custom_actions:
    - name: REST
      description: "Rest to recover energy"
      enabled_by_default: true
      costs:
        hygeine: -0.1  # TYPO: should be 'hygiene' (which exists in bars.yaml)
      effects:
        energy: 0.2
  labels:
    preset: gaming
""")

        # Attempt compilation
        compiler = UniverseCompiler()

        # Compilation should raise CompilationError with UAC-ACT-002
        with pytest.raises(Exception) as exc_info:
            compiler.compile(config_dir, use_cache=False)

        error_msg = str(exc_info.value)

        # Verify UAC-ACT-002 error was raised
        assert "UAC-ACT-002" in error_msg, f"Expected UAC-ACT-002 error code, got: {error_msg}"
        assert "REST" in error_msg, f"Error should mention action name 'REST', got: {error_msg}"
        assert "hygeine" in error_msg, f"Error should mention unknown meter 'hygeine', got: {error_msg}"
        assert "costs" in error_msg, f"Error should specify 'costs' field, got: {error_msg}"

    def test_action_with_unknown_meter_in_effects_fails_compilation(self, temp_config_with_global_actions):
        """
        JANK-02: Action with unknown meter in effects should produce UAC-ACT-002 error.
        """
        config_dir = temp_config_with_global_actions["config_dir"]
        actions_path = temp_config_with_global_actions["actions_path"]

        # Create actions.yaml with unknown meter in effects
        actions_path.write_text("""
actions:
  version: "1.0"
  substrate_actions:
    inherit: true
  custom_actions:
    - name: MEDITATE
      description: "Meditate to improve mood"
      enabled_by_default: true
      costs:
        energy: 0.01
      effects:
        moood: 0.3  # TYPO: should be 'mood'
  labels:
    preset: gaming
""")

        compiler = UniverseCompiler()

        with pytest.raises(Exception) as exc_info:
            compiler.compile(config_dir, use_cache=False)

        error_msg = str(exc_info.value)

        assert "UAC-ACT-002" in error_msg, "Expected UAC-ACT-002 error code"
        assert "MEDITATE" in error_msg, "Error should mention action name 'MEDITATE'"
        assert "moood" in error_msg, "Error should mention unknown meter 'moood'"
        assert "effects" in error_msg, "Error should specify 'effects' field"

    def test_action_with_multiple_unknown_meters_reports_all_errors(self, temp_config_with_global_actions):
        """
        JANK-02: Action with multiple unknown meters should produce error for each.
        """
        config_dir = temp_config_with_global_actions["config_dir"]
        actions_path = temp_config_with_global_actions["actions_path"]

        # Multiple unknown meters in same action
        actions_path.write_text("""
actions:
  version: "1.0"
  substrate_actions:
    inherit: true
  custom_actions:
    - name: WORKOUT
      description: "Exercise"
      enabled_by_default: true
      costs:
        stamina: 0.2    # Unknown meter
        hydration: 0.1  # Unknown meter
      effects:
        fitness_level: 0.3  # Unknown meter (correct name is 'fitness')
  labels:
    preset: gaming
""")

        compiler = UniverseCompiler()

        with pytest.raises(Exception) as exc_info:
            compiler.compile(config_dir, use_cache=False)

        error_msg = str(exc_info.value)

        # Should mention all unknown meters
        assert "stamina" in error_msg, "Should mention 'stamina'"
        assert "hydration" in error_msg, "Should mention 'hydration'"
        assert "fitness_level" in error_msg, "Should mention 'fitness_level'"
        assert "WORKOUT" in error_msg, "Should mention action name"

    def test_action_with_valid_meters_compiles_successfully(self, temp_config_with_global_actions):
        """
        JANK-02: Action with only valid meter references should compile without errors.

        Ensures strict validation doesn't break valid configs.
        """
        config_dir = temp_config_with_global_actions["config_dir"]
        actions_path = temp_config_with_global_actions["actions_path"]

        # Valid meter references (energy, health, money exist in test pack bars.yaml)
        actions_path.write_text("""
actions:
  version: "1.0"
  substrate_actions:
    inherit: true
  custom_actions:
    - name: REST
      description: "Rest to recover energy"
      enabled_by_default: true
      costs:
        health: 0.05  # Valid meter from bars.yaml
      effects:
        energy: 0.2   # Valid meter from bars.yaml

    - name: MEDITATE
      description: "Meditate"
      enabled_by_default: true
      costs:
        energy: 0.01
      effects:
        health: 0.01
  labels:
    preset: gaming
""")

        compiler = UniverseCompiler()

        # Should compile successfully
        result = compiler.compile(config_dir, use_cache=False)

        assert result is not None, "Compilation should succeed with valid meters"

    def test_empty_costs_and_effects_compiles_successfully(self, temp_config_with_global_actions):
        """Actions with no costs/effects should compile fine."""
        config_dir = temp_config_with_global_actions["config_dir"]
        actions_path = temp_config_with_global_actions["actions_path"]

        actions_path.write_text("""
actions:
  version: "1.0"
  substrate_actions:
    inherit: true
  custom_actions:
    - name: REST
      description: "Do nothing"
      enabled_by_default: true
      costs: {}
      effects: {}
  labels:
    preset: gaming
""")

        compiler = UniverseCompiler()
        result = compiler.compile(config_dir, use_cache=False)

        assert result is not None, "Empty costs/effects should compile successfully"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
