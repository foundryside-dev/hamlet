"""Derived state evaluates by declaration; static state never reinitializes on evaluation."""

import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.config.variables_config import VariablesConfig
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compilers.vfs import VFSCompiler


def _variable(identifier, *, scope="global", expression=None, initial_value=0.0, type="scalar"):
    return {
        "id": identifier,
        "scope": scope,
        "type": type,
        "lifetime": "episode",
        "semantic_type": "custom",
        "exposed_to": [],
        "initial_value": initial_value,
        **({"expression": expression} if expression is not None else {}),
    }


def _config(declarations, evaluation_mode="mark_and_sweep"):
    return VariablesConfig(
        version="1.0",
        evaluation_mode=evaluation_mode,
        debug_logging=False,
        extents={},
        item_profiles=["default_item"],
        declarations=declarations,
    )


def _compile(tmp_path, declarations, evaluation_mode="mark_and_sweep"):
    directory = prepare_config_dir(tmp_path)
    (directory / "variables.yaml").write_text(yaml.safe_dump({"variables": _config(declarations, evaluation_mode).model_dump(mode="json")}))
    return UniverseCompiler().compile(directory, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)


def test_expression_variables_are_marked_without_auxiliary_inputs(tmp_path):
    universe = _compile(
        tmp_path,
        [
            _variable("base", initial_value=1.0),
            _variable("derived", expression="base + 1.0"),
            _variable("flag", scope="agent", type="bool", expression="bar.energy < 0.2", initial_value=False),
        ],
    )
    assert universe.vfs_evaluation_marks == {"global": {"derived"}, "agent": {"flag"}}


def test_statics_are_never_marked(tmp_path):
    universe = _compile(tmp_path, [_variable("counter")])
    assert not universe.vfs_evaluation_marks


def test_removed_observation_mark_field_is_absent(tmp_path):
    universe = _compile(tmp_path, [], "eager")
    assert not hasattr(universe, "vfs_observation_marks")


def test_evaluation_is_marked_by_declaration_not_by_exposure():
    config = _config([_variable("derived", expression="1.0 + 1.0")])
    assert VFSCompiler().derive_evaluation_marks(config) == {"global": {"derived"}}


def test_static_declaration_does_not_acquire_expression_marks():
    assert VFSCompiler().derive_evaluation_marks(_config([_variable("counter")])) == {}
