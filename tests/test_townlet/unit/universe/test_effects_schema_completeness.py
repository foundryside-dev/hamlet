"""The command-pipeline namespace is complete: every compiled symbol has its one spelling (VFS round-2 S5)."""

import shutil
from pathlib import Path

import pytest
import yaml

from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode, CommandType
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compilers.effects import EffectsCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.namespace import ANY_ITEM, EFFECT_PIPELINE, ItemBinding
from townlet.vfs.schema import VariableDef
from townlet.world.expression.type_checker import TypeCheckError

CONFIGS = Path(__file__).resolve().parents[4] / "configs"


def _env(pack: str, level: str):
    universe = UniverseCompiler().compile(CONFIGS / pack, primary_level=level, use_cache=False)
    return universe, universe.create_environment(num_agents=1, level_name=level, device="cpu")


def test_item_state_is_item_dot_name_of_the_bound_profile():
    universe, env = _env("test/items_smoke", "L0_smoke")
    namespace = env.command_symbols.namespace
    assert universe.compiled_vfs_profiles is not None and universe.compiled_vfs_profiles.item_profiles
    for name, profile in universe.compiled_vfs_profiles.item_profiles.items():
        schema = namespace.schema(EFFECT_PIPELINE.with_item(ItemBinding.of_profile(name)))
        for var in profile.variables:
            assert f"item.{var.name}" in schema
            assert f"item.{var.name}" not in namespace.schema(EFFECT_PIPELINE)
    # An item chosen at run time reads only what every profile declares.
    assert {key for key in namespace.schema(EFFECT_PIPELINE.with_item(ANY_ITEM)) if key.startswith("item.")} == {"item.condition"}


def test_meters_locals_and_tick_are_served():
    _, env = _env("test/effects_smoke", "L0_effects")
    schema = env.command_symbols.namespace.schema(EFFECT_PIPELINE)
    for name in ("intensity", "elapsed_ticks", "duration_remaining", "tick", "bar.energy"):
        assert name in schema
    assert "target.bar.energy" not in schema and "energy" not in schema


def _var(var_id: str, scope: str, var_type: str = "scalar") -> VariableDef:
    default = [0.0, 0.0] if var_type == "vec2f" else 0.0
    return VariableDef(
        id=var_id, scope=scope, type=var_type, lifetime="episode", default=default, readable_by=["engine"], writable_by=["engine"]
    )


def test_global_and_agent_variables_have_one_bare_spelling():
    symbols = EffectsCompiler().build_symbols(
        variables=[_var("world_heat", "global"), _var("deficit", "agent")],
        meter_names=(),
        compiled_vfs_profiles=None,
        expressions={},
        time_enabled=True,
    )
    schema = symbols.namespace.schema(EFFECT_PIPELINE)
    assert {"world_heat", "deficit"} <= schema.keys()
    assert not any(key.startswith(("vfs.", "global.", "target.", "self.")) for key in schema)


def test_canonical_vector_type_is_preserved_before_command_compilation(tmp_path):
    symbols = EffectsCompiler().build_symbols(
        variables=[_var("vector", "global", "vec2f"), _var("scalar", "global")],
        meter_names=(),
        compiled_vfs_profiles=None,
        expressions={},
        time_enabled=True,
    )
    compiler = CommandCompiler(symbols.namespace, context=EFFECT_PIPELINE, time_enabled=True, expressions={})
    with pytest.raises(TypeCheckError, match="expected float, got vec2f"):
        compiler.compile_command(CommandNode(type=CommandType.MODIFY, path="scalar", value_expr="vector"))

    pack = tmp_path / "pack"
    shutil.copytree(CONFIGS / "test" / "effects_smoke", pack, ignore=shutil.ignore_patterns(".compiled"))
    variables = yaml.safe_load((pack / "variables.yaml").read_text())
    for var_id, var_type, initial in (("vector", "vec2f", [0.1, 0.2]), ("scalar", "scalar", 0.0)):
        variables["variables"]["declarations"].append(
            dict(
                readable_by=["engine", "agent"],
                writable_by=["engine"],
                id=var_id,
                scope="global",
                type=var_type,
                lifetime="episode",
                semantic_type="custom",
                exposed_to=[],
                initial_value=initial,
            )
        )
    (pack / "variables.yaml").write_text(yaml.safe_dump(variables))
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
            on_tick=[dict(modify="scalar", value="vector")],
            on_despawn=[],
            on_interrupt=[],
        )
    ]
    effects["max_active_effects"] = {"global": 1, "agent": 0, "item": 0, "affordance": 0}
    effects_path.write_text(yaml.safe_dump(effects))
    with pytest.raises(CompilationError, match="expected float, got vec2f"):
        UniverseCompiler().compile(pack, primary_level="L0_effects", use_cache=False)
