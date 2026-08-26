"""Evaluation marks derive from DECLARATION (having an expression), never from exposure."""

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


def test_evaluation_is_marked_by_declaration_not_by_exposure():
    """An expression variable's value is world STATE, so evaluation cannot key on
    exposure. Marking used to be `exposed_to`-driven, which looked harmless only because
    `exposed_to` failed open to ["agent"]; deleting that fail-open at the unit-3 cut
    would otherwise have silently stopped evaluating every unexposed expression variable
    — a world-evolution change, not an observation one.
    """
    profile = GlobalVFSProfileConfig(
        variables=[GlobalVFSVariableConfig(semantic_type="custom", name="derived", type="float", expression="1.0 + 1.0")]
    )
    profiles_config = VFSProfilesConfig(
        version="1.0", evaluation_mode="mark_and_sweep", debug_logging=False, global_profile=profile
    )
    # Explicitly UNEXPOSED, which is what an authored pack now means by an empty list.
    profiles_config.global_profile.variables[0].exposed_to = []

    assert VFSCompiler().derive_evaluation_marks(profiles_config, overlay_variables=None) == {"global": {"derived"}}
    # The overlay cannot subtract it either, and does not need to add it.
    assert VFSCompiler().derive_evaluation_marks(
        profiles_config, overlay_variables=(_overlay_var("derived", observable=True),)
    ) == {"global": {"derived"}}


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
