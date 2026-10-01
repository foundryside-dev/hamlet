"""Known write targets refuse read-only policies even in unreachable branches."""

from dataclasses import replace
from pathlib import Path

import pytest

from townlet.config.effects_config import EffectsConfig
from townlet.config.variables_config import VariablesConfig
from townlet.universe.errors import CompilationError
from townlet.universe.raw_configs_v21 import RawConfigsV21


def _raw():
    raw = RawConfigsV21.from_experiment_dir(Path("configs/simple"))
    declarations = [
        dict(
            id="secret",
            scope="agent",
            type="scalar",
            lifetime="episode",
            semantic_type="custom",
            initial_value=3.0,
            exposed_to=[],
            readable_by=["engine"],
            writable_by=[],
        )
    ]
    return replace(
        raw,
        variables=VariablesConfig(
            version="1.0", evaluation_mode="mark_and_sweep", debug_logging=False, extents={}, item_profiles=[], declarations=declarations
        ),
    )


@pytest.mark.parametrize(
    "command",
    [
        {"modify": "vfs.secret", "value": "3"},
        {"if": "false", "then": [{"modify": "target.vfs.secret", "value": "3"}]},
        {"parallel": [{"modify": "self.vfs.secret", "value": "3"}]},
        {"delay": "3", "do": [{"modify": "vfs.secret", "value": "3"}]},
        {"switch": "0", "cases": [{"when": "1", "do": [{"modify": "vfs.secret", "value": "3"}]}]},
        {"for_each": "all_agents", "as": "agent", "do": [{"modify": "target.vfs.secret", "value": "3"}]},
        {"sample": "uniform", "params": {"min": "0", "max": "1"}, "store_in": "vfs.secret"},
        {"reduce": "all_agents", "reduce_as": "agent", "reduce_init": "0", "reduce_body": "acc + 1", "reduce_into": "vfs.secret"},
    ],
)
def test_all_effect_command_write_forms_are_checked(command):
    from townlet.universe.validation.static_access import validate_static_write_targets

    raw = _raw()
    effects = EffectsConfig(
        effect_definitions=[
            dict(
                id="bad",
                scope="agent",
                duration=3,
                reapply_policy="stack",
                observable=False,
                on_spawn=[command],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        ],
        max_active_effects={"global": 0, "agent": 1, "item": 0, "affordance": 0},
    )
    with pytest.raises(CompilationError, match="secret.*engine write"):
        validate_static_write_targets(replace(raw, effects=effects), raw.source_map)


def test_expression_output_requires_engine_writer():
    from townlet.universe.validation.static_access import validate_static_write_targets

    raw = _raw()
    raw.variables.declarations[0].expression = "tick"
    with pytest.raises(CompilationError, match="secret.*engine write"):
        validate_static_write_targets(raw, raw.source_map)


def test_conditional_action_and_social_writes_are_checked():
    from townlet.universe.validation.static_access import validate_static_write_targets
    from townlet.vfs.schema import WriteSpec

    raw = _raw()
    raw.actions.actions.custom_actions[0].writes = [
        WriteSpec(
            variable_id="secret",
            expression="secret",
            condition="false",
            composition="overwrite",
            phase="apply_action_effects",
            priority=0,
            clamp=None,
            telemetry_label="bad",
        )
    ]
    with pytest.raises(CompilationError, match="secret.*engine write"):
        validate_static_write_targets(raw, raw.source_map)
    raw.actions.actions.custom_actions[0].writes = []
    with pytest.raises(CompilationError, match="secret.*engine write"):
        validate_static_write_targets(
            replace(
                raw,
                social_residue_rules=(
                    {
                        "id": "bad",
                        "kind": "social_residue",
                        "phase": "apply_social_residue_effects",
                        "reads": ["secret"],
                        "condition": "false",
                        "writes": [
                            {
                                "variable_id": "secret",
                                "expression": "secret",
                                "composition": "overwrite",
                                "condition": None,
                                "clamp": None,
                                "effect": None,
                                "scope": "agent",
                            }
                        ],
                    },
                ),
            ),
            raw.source_map,
        )


def test_affordance_and_qualified_item_hook_write_targets_refuse():
    from townlet.config.effects_config import CommandConfig
    from townlet.config.items_config import ItemsCatalogConfig
    from townlet.universe.validation.static_access import validate_static_write_targets

    raw = _raw()
    level = next(iter(raw.levels.values()))
    level.affordances.affordances[0].interactions["on_start"] = [
        CommandConfig.model_validate({"if": "false", "then": [{"modify": "vfs.secret", "value": "3"}]})
    ]
    with pytest.raises(CompilationError, match="secret.*engine write"):
        validate_static_write_targets(raw, raw.source_map)
    level.affordances.affordances[0].interactions["on_start"] = []
    raw.variables.item_profiles.append("locked")
    item_variable = raw.variables.declarations[0].model_copy(update={"scope": "item", "profile": "locked"})
    raw.variables.declarations.append(item_variable)
    items = ItemsCatalogConfig(
        version="1.0",
        max_items_per_agent=1,
        max_items_in_world=2,
        item_types=[
            dict(
                id="locked_item",
                name="Locked",
                icon="x",
                tags=["locked"],
                vfs_profile="locked",
                interactions={"on_use": [{"modify": "self.vfs.secret", "value": "3"}]},
            )
        ],
    )
    with pytest.raises(CompilationError, match="locked:secret.*engine write"):
        validate_static_write_targets(replace(raw, items=items), raw.source_map)


def test_compiler_hook_refuses_known_action_with_source_origin(tmp_path):
    import shutil

    import yaml

    from townlet.universe.compiler import UniverseCompiler

    pack = tmp_path / "pack"
    shutil.copytree("configs/simple", pack)
    payload = yaml.safe_load((pack / "variables.yaml").read_text())
    variable = payload["variables"]["declarations"][0]
    variable["writable_by"] = []
    (pack / "variables.yaml").write_text(yaml.safe_dump(payload))
    actions = yaml.safe_load((pack / "actions.yaml").read_text())
    actions["actions"]["custom_actions"][0]["writes"] = [
        dict(
            variable_id=variable["id"],
            expression=variable["id"],
            condition="false",
            composition="overwrite",
            phase="apply_action_effects",
            priority=0,
            clamp=None,
            telemetry_label="denied",
        )
    ]
    (pack / "actions.yaml").write_text(yaml.safe_dump(actions))
    with pytest.raises(CompilationError, match="UAC-STATIC-WRITE") as error:
        UniverseCompiler().compile(pack, primary_level="L0_simple", use_cache=False)
    assert "actions.yaml:" in str(error.value)


def test_unsupported_authored_initial_state_refuses_at_typed_boundary():
    from pydantic import ValidationError

    from townlet.config.effects_config import CommandConfig
    from townlet.config.items_config import ItemAppearanceRuleConfig

    with pytest.raises(ValidationError, match="initial_state") as command_error:
        CommandConfig.model_validate({"spawn_item": "item", "position": "self", "initial_state": {"secret": 3.0}})
    assert command_error.value.errors()[0]["type"] == "extra_forbidden"
    with pytest.raises(ValidationError, match="initial_state") as appearance_error:
        ItemAppearanceRuleConfig.model_validate({"item_type": "item", "spawn_count": 1, "initial_state": {"secret": 3.0}})
    assert appearance_error.value.errors()[0]["type"] == "extra_forbidden"
