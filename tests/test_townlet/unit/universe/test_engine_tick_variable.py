"""The engine tick is ambient in expressions and refuses authored collisions."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.config.variables_config import VariableDeclaration, VariablesConfig
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError


def _compile(config_dir: Path):
    return UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME)


def _write_variables(config_dir: Path, declarations: list[dict]) -> None:
    (config_dir / "variables.yaml").write_text(
        yaml.safe_dump(
            {
                "variables": {
                    "version": "1.0",
                    "evaluation_mode": "eager",
                    "debug_logging": False,
                    "extents": {},
                    "item_profiles": ["default_item"],
                    "declarations": declarations,
                }
            }
        )
    )


def _variable(identifier: str, scope: str = "global", **fields) -> dict:
    return {
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "id": identifier,
        "scope": scope,
        "type": "scalar",
        "lifetime": "episode",
        "semantic_type": "custom",
        "exposed_to": [],
        "initial_value": 0.0,
        **fields,
    }


def test_tick_variable_is_injected_into_every_universe(tmp_path):
    universe = _compile(prepare_config_dir(tmp_path))
    tick = next(variable for variable in universe.get_level(universe.metadata.primary_level).vfs_variables if variable.id == "tick")
    assert tick.scope == "global"
    assert tick.writable_by == ["engine"]
    assert "agent" in tick.readable_by


@pytest.mark.parametrize("scope", ["global", "agent"])
def test_authored_variable_named_tick_refuses_at_full_compile(tmp_path, scope):
    config_dir = prepare_config_dir(tmp_path)
    _write_variables(config_dir, [_variable("tick", scope)])
    with pytest.raises(CompilationError, match="tick"):
        _compile(config_dir)


def test_authored_static_variable_named_tick_refuses_in_canonical_inventory():
    """The complete roster cannot silently deduplicate an authored engine tick."""
    authored_tick = VariableDeclaration.model_validate(_variable("tick", initial_value=1.0))
    with pytest.raises(ValueError, match="tick"):
        VariablesConfig(
            version="1.0", evaluation_mode="eager", debug_logging=False, extents={}, item_profiles=[], declarations=[authored_tick]
        )


def test_expression_may_reference_bare_tick(tmp_path):
    config_dir = prepare_config_dir(tmp_path)
    _write_variables(config_dir, [_variable("double_tick", expression="tick * 2.0")])
    universe = _compile(config_dir)
    profile = universe.compiled_vfs_profiles.global_profile
    assert any(variable.name == "double_tick" for variable in profile.variables)
    assert "tick" not in (profile.dependencies or {}).get("double_tick", ())
