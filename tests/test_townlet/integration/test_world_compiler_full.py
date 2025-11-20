"""Integration tests for complete World Compiler pipeline.

Tests the full compilation flow:
  Config YAML → Parse → Validate → Compile → Execute
"""

from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler


@pytest.fixture
def compiler():
    """UniverseCompiler instance."""
    return UniverseCompiler()


@pytest.fixture
def integration_config_dir():
    """Use L0_0_minimal as test config (already minimal and valid)."""
    # Use existing minimal config from default curriculum
    return Path("/home/john/hamlet/configs/default_curriculum")


class TestWorldCompilerPipeline:
    """Test complete compilation pipeline."""

    def test_compile_minimal_config(self, compiler, integration_config_dir):
        """Compiler can parse and validate minimal config pack."""
        # Compile the config
        universe = compiler.compile(integration_config_dir)

        # Verify compilation succeeded
        assert universe is not None
        assert universe.metadata is not None
        assert universe.optimization_data is not None

        # Verify levels loaded (default_curriculum has 5 levels)
        assert universe.all_levels is not None
        assert len(universe.all_levels) == 5
        assert "L0_0_minimal" in universe.available_levels

    def test_compiled_universe_structure(self, compiler, integration_config_dir):
        """CompiledUniverse has correct structure."""
        universe = compiler.compile(integration_config_dir)

        # Check metadata structure
        assert hasattr(universe.metadata, "meter_names")
        assert hasattr(universe.metadata, "affordance_ids")
        assert hasattr(universe.metadata, "action_count")

        # Check optimization data
        assert hasattr(universe.optimization_data, "action_mask_table")
        assert hasattr(universe.optimization_data, "modulation_data")

        # Check level structure
        level = universe.get_level("L0_0_minimal")
        assert hasattr(level, "affordances")
        assert hasattr(level, "bars")
        assert hasattr(level, "training")

    def test_affordance_effects_compilation(self, compiler, integration_config_dir):
        """Affordance interactions compile to Effects commands."""
        universe = compiler.compile(integration_config_dir)

        level = universe.get_level("L0_0_minimal")
        eat_affordance = next(a for a in level.affordances.affordances if a.name == "EAT")

        # Verify interactions field exists
        assert hasattr(eat_affordance, "interactions")
        assert "on_start" in eat_affordance.interactions

        # Verify on_start has effect commands
        on_start_commands = eat_affordance.interactions["on_start"]
        assert len(on_start_commands) > 0

        # Verify command structure (first command modifies satiation)
        cmd = on_start_commands[0]
        assert hasattr(cmd, "modify")
        assert hasattr(cmd, "value")
        assert cmd.modify == "target.bar.satiation"
        assert "target.bar.satiation + 0.4" in cmd.value
