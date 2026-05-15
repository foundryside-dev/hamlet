"""Tests for action space composition and legacy action-effect rejection."""

import shutil
import tempfile
from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler

PRIMARY_LEVEL = "L0"


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


class TestLegacyActionEffectRejection:
    """Legacy custom action meter effects must fail at the config boundary."""

    def test_action_with_legacy_costs_fails_compilation(self, temp_config_with_global_actions):
        """Action costs now belong in VTC writes, not actions.yaml custom action fields."""
        config_dir = temp_config_with_global_actions["config_dir"]
        actions_path = temp_config_with_global_actions["actions_path"]

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
        energy: -0.1
  labels:
    preset: gaming
""")

        compiler = UniverseCompiler()

        with pytest.raises(Exception) as exc_info:
            compiler.compile(config_dir, primary_level=PRIMARY_LEVEL, use_cache=False)

        error_msg = str(exc_info.value)
        assert "costs" in error_msg
        assert "extra" in error_msg.lower() or "not permitted" in error_msg.lower()

    def test_action_with_legacy_effects_fails_compilation(self, temp_config_with_global_actions):
        """Action effects now belong in VTC writes, not actions.yaml custom action fields."""
        config_dir = temp_config_with_global_actions["config_dir"]
        actions_path = temp_config_with_global_actions["actions_path"]

        actions_path.write_text("""
actions:
  version: "1.0"
  substrate_actions:
    inherit: true
  custom_actions:
    - name: MEDITATE
      description: "Meditate to improve mood"
      enabled_by_default: true
      effects:
        mood: 0.3
  labels:
    preset: gaming
""")

        compiler = UniverseCompiler()

        with pytest.raises(Exception) as exc_info:
            compiler.compile(config_dir, primary_level=PRIMARY_LEVEL, use_cache=False)

        error_msg = str(exc_info.value)
        assert "effects" in error_msg
        assert "extra" in error_msg.lower() or "not permitted" in error_msg.lower()

    def test_actions_without_legacy_costs_or_effects_compile_successfully(self, temp_config_with_global_actions):
        """Custom actions without legacy meter-effect fields still compile."""
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
  labels:
    preset: gaming
""")

        compiler = UniverseCompiler()
        result = compiler.compile(config_dir, primary_level=PRIMARY_LEVEL, use_cache=False)

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
