"""Evaluation marks derive from exposure: expression vars only, statics never."""

from __future__ import annotations

import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.config.vfs_profiles_config import (
    GlobalVFSProfileConfig,
    GlobalVFSVariableConfig,
    VFSProfilesConfig,
)
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compilers.vfs import VFSCompiler
from townlet.vfs.schema import VariableDef


def _compile_with_profiles(tmp_path, profile_payload):
    config_dir = prepare_config_dir(tmp_path)
    (config_dir / "vfs_profiles.yaml").write_text(yaml.safe_dump(profile_payload))
    return UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME)


def test_expression_variables_are_marked_without_any_overlay(tmp_path):
    u = _compile_with_profiles(tmp_path, {
        "version": "1.0", "evaluation_mode": "mark_and_sweep", "debug_logging": False,
        "global_profile": {"variables": [
            {"semantic_type": "custom", "name": "base", "type": "float", "initial_value": 1.0},
            {"semantic_type": "custom", "name": "derived", "type": "float", "expression": "base + 1.0"},
        ]},
        "agent_profile": {"variables": [
            {"semantic_type": "custom", "name": "flag", "type": "bool", "expression": "bar.energy < 0.2"},
        ]},
        "item_profiles": [{"profile_name": "default_item", "variables": []}],
    })
    assert u.vfs_evaluation_marks == {"global": {"derived"}, "agent": {"flag"}}


def test_statics_are_never_marked(tmp_path):
    u = _compile_with_profiles(tmp_path, {
        "version": "1.0", "evaluation_mode": "mark_and_sweep", "debug_logging": False,
        "global_profile": {"variables": [
            {"semantic_type": "custom", "name": "counter", "type": "int", "initial_value": 0},
        ]},
        "agent_profile": None,
        "item_profiles": [{"profile_name": "default_item", "variables": []}],
    })
    assert not (u.vfs_evaluation_marks or {}).get("global")


def test_old_field_name_is_gone(tmp_path):
    u = _compile_with_profiles(tmp_path, {
        "version": "1.0", "evaluation_mode": "eager", "debug_logging": False,
        "global_profile": None, "agent_profile": None,
        "item_profiles": [{"profile_name": "default_item", "variables": []}],
    })
    assert not hasattr(u, "vfs_observation_marks")


def _overlay_var(name: str, *, observable: bool) -> VariableDef:
    return VariableDef(
        id=name,
        scope="global",
        type="scalar",
        lifetime="episode",
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        default=0.0,
        observable=observable,
    )


def test_overlay_observable_marks_an_expression_variable_with_no_exposure():
    """The overlay-additive union is the compiler's own path (not the pydantic default):
    GlobalVFSProfileConfig.default_metadata forces exposed_to=["agent"] whenever it is
    empty at construction, so exposed_to is truthy for every profile variable declared
    through YAML. To exercise the overlay branch specifically — not exposed_to's default —
    force a genuinely empty exposed_to on the variable object AFTER construction (pydantic
    does not re-validate on plain attribute assignment)."""
    profile = GlobalVFSProfileConfig(
        variables=[GlobalVFSVariableConfig(semantic_type="custom", name="derived", type="float", expression="1.0 + 1.0")]
    )
    profiles_config = VFSProfilesConfig(
        version="1.0", evaluation_mode="mark_and_sweep", debug_logging=False, global_profile=profile
    )
    # Nesting `profile` inside VFSProfilesConfig() re-validates it (pydantic re-runs
    # nested-model validators on construction), which would re-fill exposed_to via
    # default_metadata — so the override must happen AFTER this point, on the config
    # object we actually pass to derive_evaluation_marks.
    profiles_config.global_profile.variables[0].exposed_to = []  # bypass the exposed_to default for this test only

    marks_without_overlay = VFSCompiler().derive_evaluation_marks(profiles_config, overlay_variables=None)
    assert not (marks_without_overlay or {}).get("global")

    marks_with_overlay = VFSCompiler().derive_evaluation_marks(
        profiles_config, overlay_variables=(_overlay_var("derived", observable=True),)
    )
    assert marks_with_overlay == {"global": {"derived"}}


def test_overlay_observable_on_a_static_never_marks_it():
    profile = GlobalVFSProfileConfig(
        variables=[GlobalVFSVariableConfig(semantic_type="custom", name="counter", type="int", initial_value=0)]
    )
    profiles_config = VFSProfilesConfig(
        version="1.0", evaluation_mode="mark_and_sweep", debug_logging=False, global_profile=profile
    )

    marks = VFSCompiler().derive_evaluation_marks(
        profiles_config, overlay_variables=(_overlay_var("counter", observable=True),)
    )
    assert not (marks or {}).get("global")
