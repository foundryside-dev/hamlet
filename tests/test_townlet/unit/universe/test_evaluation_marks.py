"""Evaluation marks derive from exposure: expression vars only, statics never."""

from __future__ import annotations

from pathlib import Path

import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


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
