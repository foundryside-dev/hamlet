"""End-to-end tests for effects compilation pipeline (YAML → catalog with ASTs)."""

from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import prepare_config_dir
from townlet.effects.schema import CommandType
from townlet.universe.compiler import UniverseCompiler


class TestEffectsCompilationPipeline:
    """Verify command expressions are parsed and type-checked at compile time."""

    def _write_effects_yaml(self, config_dir: Path, effects: dict) -> None:
        (config_dir / "effects.yaml").write_text(yaml.dump(effects))

    def test_modify_and_if_commands_have_compiled_asts(self, tmp_path: Path):
        config_dir = prepare_config_dir(tmp_path, name="effects_pipeline")

        effects = {
            "version": "1.0",
            "effect_definitions": [
                {
                    "id": "regen",
                    "scope": "agent",
                    "duration": 1,
                    "reapply_policy": "stack",
                    "observable": True,
                    "intensity": 1.0,
                    "on_spawn": [
                        {
                            "modify": "target.bar.health",
                            "value": "target.bar.health + 0.1 * target.bar.energy",
                        }
                    ],
                    "on_tick": [
                        {
                            "if": "target.bar.health < 0.5",
                            "then": [
                                {
                                    "modify": "target.bar.health",
                                    "value": "target.bar.health + 0.2",
                                }
                            ],
                            "else": [],
                        }
                    ],
                    "on_despawn": [],
                }
            ],
        }
        self._write_effects_yaml(config_dir, effects)

        compiler = UniverseCompiler()
        compiled = compiler.compile(config_dir, use_cache=False)

        catalog = compiled.compiled_effect_catalog
        assert catalog is not None
        effect = catalog.effects["regen"]

        # on_spawn modify should have precompiled value_ast
        spawn_cmd = effect.on_spawn[0]
        assert spawn_cmd.type == CommandType.MODIFY
        assert spawn_cmd.value_expr == "target.bar.health + 0.1 * target.bar.energy"
        assert spawn_cmd.value_ast is not None

        # on_tick if should have condition_ast and nested modify with value_ast
        if_cmd = effect.on_tick[0]
        assert if_cmd.type == CommandType.IF
        assert if_cmd.condition_expr == "target.bar.health < 0.5"
        assert if_cmd.condition_ast is not None
        assert if_cmd.then_commands is not None
        nested_modify = if_cmd.then_commands[0]
        assert nested_modify.type == CommandType.MODIFY
        assert nested_modify.value_ast is not None

    def test_parse_error_propagates_with_effect_name(self, tmp_path: Path):
        config_dir = prepare_config_dir(tmp_path, name="effects_pipeline_error")

        effects = {
            "version": "1.0",
            "effect_definitions": [
                {
                    "id": "broken_effect",
                    "scope": "agent",
                    "duration": 1,
                    "reapply_policy": "stack",
                    "observable": True,
                    "intensity": 1.0,
                    "on_spawn": [
                        {
                            "modify": "target.bar.health",
                            "value": "target.bar.health + 0.1 +",  # Syntax error
                        }
                    ],
                    "on_tick": [],
                    "on_despawn": [],
                }
            ],
        }
        self._write_effects_yaml(config_dir, effects)

        compiler = UniverseCompiler()

        with pytest.raises(Exception) as exc_info:
            compiler.compile(config_dir, use_cache=False)

        assert "broken_effect" in str(exc_info.value)
