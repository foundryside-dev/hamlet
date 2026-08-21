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
    assert compiled.effects_schema is not None

    # Check schema includes self.vfs.* paths (for item effects)
    # Example: self.vfs.calories, self.vfs.freshness
    # (Exact paths depend on config, but schema should be built from item profiles)

    # Verify: VFS expression schema includes item paths
    if compiled.compiled_vfs_profiles and compiled.compiled_vfs_profiles.item_profiles:
        for profile_name, profile in compiled.compiled_vfs_profiles.item_profiles.items():
            for var in profile.variables:
                assert (
                    f"self.vfs.{var.name}" in compiled.effects_schema
                ), f"Missing self.vfs.{var.name} in compiled effects schema for profile {profile_name}"
                # Item VFS paths should be in expression schema for effects
                # self.vfs.{var_name} and target.vfs.{var_name}
                assert (
                    f"self.vfs.{var.name}" in compiled.vfs_expression_schema
                ), f"Missing self.vfs.{var.name} in schema for profile {profile_name}"
                assert (
                    f"target.vfs.{var.name}" in compiled.vfs_expression_schema
                ), f"Missing target.vfs.{var.name} in schema for profile {profile_name}"


def test_effects_schema_includes_bar_paths():
    """Effects schema should include bar paths for self/target."""
    # Setup: Compile any config with bars
    config_dir = Path(__file__).parent.parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_effects", use_cache=False)

    # Verify: Schema includes bar paths
    assert compiled.effects_schema is not None
    assert "intensity" in compiled.effects_schema
    assert "elapsed_ticks" in compiled.effects_schema
    assert "duration_remaining" in compiled.effects_schema
    assert "bar.energy" in compiled.effects_schema
    assert "target.bar.energy" in compiled.effects_schema
    assert compiled.vfs_expression_schema is not None
    assert "bar.energy" in compiled.vfs_expression_schema
    # Note: Effects can reference target.bar.energy in commands


def test_effects_schema_global_profile_vars_register_global_root_not_target():
    """Global-profile variables register vfs.X and global.vfs.X — never target.vfs.X.

    A global variable has no per-agent axis, so target.vfs.X has no runtime
    semantics; registering it type-checks a path whose execution indexes the
    container's first spatial axis by agent index (hamlet-cf16cdb6c4).
    """
    from townlet.universe.compiled import CompiledVFSProfiles
    from townlet.universe.compilers.effects import EffectsCompiler
    from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable

    profiles = CompiledVFSProfiles(
        evaluation_mode="eager",
        debug_logging=False,
        global_profile=CompiledGlobalProfile(
            variables=[CompiledVariable(name="grid", type="tensor2d", exposed_to=("agent",), shape=[3, 3])],
            dependencies={},
        ),
    )

    schema = EffectsCompiler().build_schema(
        bar_names=("energy",),
        environment_variables=(),
        compiled_vfs_profiles=profiles,
    )

    assert "vfs.grid" in schema
    assert "global.vfs.grid" in schema
    assert "target.vfs.grid" not in schema


def test_effects_schema_env_vars_are_scope_aware():
    """environment.yaml variables register per their declared scope."""
    from townlet.config.environment_config import NormalizationConfig, VariableConfig
    from townlet.universe.compilers.effects import EffectsCompiler

    norm = NormalizationConfig(method="normalize", clip=False, range=[0.0, 1.0])
    env_global = VariableConfig(
        name="world_heat",
        type="scalar",
        dims=1,
        scope="global",
        description="test",
        normalization=norm,
        semantic_type="custom",
    )
    env_agent = VariableConfig(
        name="deficit",
        type="scalar",
        dims=1,
        scope="agent",
        description="test",
        normalization=norm,
        semantic_type="custom",
    )

    schema = EffectsCompiler().build_schema(
        bar_names=(),
        environment_variables=(env_global, env_agent),
        compiled_vfs_profiles=None,
    )

    # Global-scoped: readable plainly and via the explicit root; no target path.
    assert "vfs.world_heat" in schema
    assert "global.vfs.world_heat" in schema
    assert "target.vfs.world_heat" not in schema

    # Agent-scoped: unchanged registration.
    assert "vfs.deficit" in schema
    assert "target.vfs.deficit" in schema
    assert "global.vfs.deficit" not in schema
