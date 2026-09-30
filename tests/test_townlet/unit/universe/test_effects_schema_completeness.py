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


def test_effects_schema_canonical_global_variables_never_acquire_target_paths():
    from townlet.config.variables_config import VariablesConfig
    from townlet.universe.compilers.effects import EffectsCompiler

    variables = VariablesConfig(
        version="1.0",
        evaluation_mode="eager",
        debug_logging=False,
        extents={},
        item_profiles=[],
        declarations=[
            {
                "id": "world_heat",
                "scope": "global",
                "type": "scalar",
                "lifetime": "episode",
                "initial_value": 0.0,
                "semantic_type": "custom",
                "exposed_to": [],
            },
            {
                "id": "deficit",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "initial_value": 0.0,
                "semantic_type": "custom",
                "exposed_to": [],
            },
        ],
    )
    schema = EffectsCompiler().build_schema(bar_names=(), variables=variables, compiled_vfs_profiles=None)
    assert "vfs.world_heat" in schema
    assert "global.vfs.world_heat" in schema
    assert "target.vfs.world_heat" not in schema
    assert "vfs.deficit" in schema
    assert "target.vfs.deficit" in schema
    assert "global.vfs.deficit" not in schema


def test_effects_schema_preserves_canonical_vector_type_before_command_compilation(tmp_path):
    import shutil

    import pytest
    import yaml

    from townlet.config.variables_config import VariablesConfig
    from townlet.effects.compiler import CommandCompiler
    from townlet.effects.schema import CommandNode, CommandType
    from townlet.universe.compilers.effects import EffectsCompiler
    from townlet.universe.errors import CompilationError
    from townlet.world.expression.type_checker import TypeCheckError

    variables = VariablesConfig(
        version="1.0",
        evaluation_mode="mark_and_sweep",
        debug_logging=False,
        extents={},
        item_profiles=[],
        declarations=[
            dict(
                id="vector",
                scope="global",
                type="vec2f",
                lifetime="episode",
                semantic_type="custom",
                exposed_to=[],
                initial_value=[0.1, 0.2],
            ),
            dict(id="scalar", scope="global", type="scalar", lifetime="episode", semantic_type="custom", exposed_to=[], initial_value=0.0),
        ],
    )
    schema = EffectsCompiler().build_schema(bar_names=(), variables=variables, compiled_vfs_profiles=None)
    command = CommandNode(type=CommandType.MODIFY, path="vfs.scalar", value_expr="vfs.vector")
    with pytest.raises(TypeCheckError, match="expected float, got vec2f"):
        CommandCompiler(schema).compile_command(command)

    pack = tmp_path / "pack"
    shutil.copytree("configs/test/effects_smoke", pack)
    (pack / "variables.yaml").write_text(yaml.safe_dump({"variables": variables.model_dump(mode="json", exclude_unset=True)}))
    effects_path = pack / "effects.yaml"
    effects = yaml.safe_load(effects_path.read_text())
    effects["effect_definitions"] = [
        dict(
            id="type_probe",
            scope="global",
            duration=1,
            reapply_policy="renew",
            observable=False,
            on_spawn=[],
            on_tick=[dict(modify="vfs.scalar", value="vfs.vector")],
            on_despawn=[],
            on_interrupt=[],
        )
    ]
    effects["max_active_effects"] = {"global": 1, "agent": 0, "item": 0, "affordance": 0}
    effects_path.write_text(yaml.safe_dump(effects))
    with pytest.raises(CompilationError, match="expected float, got vec2f"):
        UniverseCompiler().compile(pack, primary_level="L0_effects", use_cache=False)
