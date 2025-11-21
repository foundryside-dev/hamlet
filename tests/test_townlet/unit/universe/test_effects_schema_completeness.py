"""Tests for effects schema completeness."""

from pathlib import Path

from townlet.universe.compiler import UniverseCompiler


def test_effects_schema_includes_item_vfs_paths():
    """Effects schema should include item-scoped VFS paths for self/target."""
    # Setup: Compile config with item profiles
    config_dir = Path(__file__).parent.parent.parent.parent.parent / "configs" / "test" / "items_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_smoke", use_cache=False)

    # Verify: Effect catalog schema includes item VFS paths
    assert compiled.compiled_effect_catalog is not None

    # Check schema includes self.vfs.* paths (for item effects)
    # Example: self.vfs.calories, self.vfs.freshness
    # (Exact paths depend on config, but schema should be built from item profiles)

    # Verify: VFS expression schema includes item paths
    if compiled.compiled_vfs_profiles and compiled.compiled_vfs_profiles.item_profiles:
        for profile_name, profile in compiled.compiled_vfs_profiles.item_profiles.items():
            for var in profile.variables:
                # Item VFS paths should be in expression schema for effects
                # self.vfs.{var_name} and target.vfs.{var_name}
                assert f"self.vfs.{var.name}" in compiled.vfs_expression_schema, (
                    f"Missing self.vfs.{var.name} in schema for profile {profile_name}"
                )
                assert f"target.vfs.{var.name}" in compiled.vfs_expression_schema, (
                    f"Missing target.vfs.{var.name} in schema for profile {profile_name}"
                )


def test_effects_schema_includes_bar_paths():
    """Effects schema should include bar paths for self/target."""
    # Setup: Compile any config with bars
    config_dir = Path(__file__).parent.parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_effects", use_cache=False)

    # Verify: Schema includes bar paths
    assert compiled.vfs_expression_schema is not None
    assert "bar.energy" in compiled.vfs_expression_schema
    # Note: Effects can reference target.bar.energy in commands
