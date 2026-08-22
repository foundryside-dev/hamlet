"""The engine tick variable: injected always, ambient in expressions, collision-refused."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def _compile(config_dir: Path):
    return UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME)


def _write_profiles(config_dir: Path, payload: dict) -> None:
    (config_dir / "vfs_profiles.yaml").write_text(yaml.safe_dump(payload))


_BASE_PROFILES = {
    "version": "1.0",
    "evaluation_mode": "eager",
    "debug_logging": False,
    "global_profile": {"variables": []},
    "agent_profile": None,
    "item_profiles": [{"profile_name": "default_item", "variables": []}],
}


def test_tick_variable_is_injected_into_every_universe(tmp_path):
    u = _compile(prepare_config_dir(tmp_path))
    tick = next(v for v in u.vfs_variables if v.id == "tick")
    assert str(tick.scope) in ("global", "VariableScope.GLOBAL") or tick.scope.value == "global"
    assert tick.writable_by == ["engine"]
    assert "agent" in tick.readable_by


def test_authored_variable_named_tick_refuses(tmp_path):
    config_dir = prepare_config_dir(tmp_path)
    payload = {**_BASE_PROFILES, "global_profile": {"variables": [
        {"semantic_type": "custom", "name": "tick", "type": "float", "initial_value": 0.0}
    ]}}
    _write_profiles(config_dir, payload)
    with pytest.raises(ValueError, match="tick"):
        _compile(config_dir)


def test_profile_expression_may_reference_bare_tick(tmp_path):
    config_dir = prepare_config_dir(tmp_path)
    payload = {**_BASE_PROFILES, "global_profile": {"variables": [
        {"semantic_type": "custom", "name": "double_tick", "type": "float", "expression": "tick * 2.0"}
    ]}}
    _write_profiles(config_dir, payload)
    u = _compile(config_dir)
    gp = u.compiled_vfs_profiles.global_profile
    assert any(v.name == "double_tick" for v in gp.variables)
    # tick is ambient, never an in-profile dependency edge:
    assert "tick" not in (gp.dependencies or {}).get("double_tick", ())
