"""Exact required-field checks for nested compiled-artifact structures."""

from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path
from typing import Any

import pytest

from townlet.universe.compiled import COMPILED_SCHEMA_VERSION, CompiledUniverse

PRIMARY_LEVEL_ALIAS_FIELDS = (
    "token_spec",
    "token_type_schema_hash",
    "layout_hash",
    "observation_schema_hash",
    "vfs_variables",
    "variable_schema_hash",
    "action_space_metadata",
    "runtime_action_space",
    "action_schema_hash",
    "transition_graph_hash",
    "transition_schedule",
    "vfs_hash",
    "meter_metadata",
    "affordance_metadata",
    "optimization_data",
    "token_advisories",
    "drive_hash",
    "curriculum_hash",
    "bars_hash",
    "affordances_hash",
    "training_hash",
)

PRIMARY_LEVEL_ALIAS_PAYLOAD_FIELDS = tuple(
    "optimization_data_raw" if field_name == "optimization_data" else field_name for field_name in PRIMARY_LEVEL_ALIAS_FIELDS
)

PRIMARY_LEVEL_PAYLOAD_FIELDS = tuple(
    (
        "optimization_data_raw"
        if field_name == "optimization_data"
        else "action_metadata" if field_name == "action_space_metadata" else field_name
    )
    for field_name in PRIMARY_LEVEL_ALIAS_FIELDS
)

COMMAND_NODE_FIELDS = (
    "type",
    "path",
    "value_expr",
    "effect_id",
    "target",
    "target_expr",
    "intensity",
    "item_type",
    "position",
    "position_expr",
    "quantity",
    "initial_state",
    "sample_distribution",
    "sample_params",
    "sample_store_path",
    "condition_expr",
    "then_commands",
    "else_commands",
    "collection",
    "collection_expr",
    "iterator",
    "body",
    "radius",
    "switch_expr",
    "cases",
    "default_commands",
    "reduce_expr",
    "reduce_iterator",
    "reduce_init_expr",
    "reduce_body_expr",
    "reduce_target",
    "parallel_commands",
    "delay_ticks_expr",
    "delay_commands",
)

COMPILED_VFS_PROFILE_FIELDS = (
    "evaluation_mode",
    "debug_logging",
    "global_profile",
    "agent_profile",
    "item_profiles",
)

COMPILED_VARIABLE_FIELDS = (
    "name",
    "type",
    "expression",
    "initial_value",
    "result_type",
    "exposed_to",
    "shape",
    "initial_value_mode",
    "initial_value_params",
    "dims",
    "semantic_type",
    "normalization",
)

LEVEL_FIELDS = (
    "level_name",
    "bars",
    "affordances",
    "drive",
    "drive_hash",
    "curriculum_hash",
    "bars_hash",
    "affordances_hash",
    "training_hash",
    "curriculum",
    "training",
    "token_spec",
    "token_type_schema_hash",
    "layout_hash",
    "action_metadata",
    "runtime_action_space",
    "action_schema_hash",
    "transition_graph_hash",
    "transition_schedule",
    "vfs_hash",
    "meter_metadata",
    "meter_declarations",
    "affordance_metadata",
    "optimization_data_raw",
    "observation_schema_hash",
    "vfs_variables",
    "variable_schema_hash",
    "token_advisories",
)


@pytest.fixture(scope="module")
def artifact_payload(compile_universe) -> dict[str, Any]:
    compiled = compile_universe(Path("configs/reference/model_pack"), primary_level="L0_demo")
    return compiled.to_dict()


def test_primary_level_products_exist_only_on_level_metadata(artifact_payload: dict[str, Any]) -> None:
    compiled_fields = {field.name for field in fields(CompiledUniverse)}

    assert compiled_fields.isdisjoint(PRIMARY_LEVEL_ALIAS_FIELDS)
    assert set(artifact_payload).isdisjoint(PRIMARY_LEVEL_ALIAS_PAYLOAD_FIELDS)
    assert set(PRIMARY_LEVEL_PAYLOAD_FIELDS) <= set(artifact_payload["all_levels"]["L0_demo"])


def test_primary_level_authority_cut_bumps_exact_artifact_schema() -> None:
    assert COMPILED_SCHEMA_VERSION == "1.26"


def _assert_missing_field(payload: dict[str, Any], field_path: str) -> None:
    with pytest.raises(ValueError, match=re.escape(f"missing required field '{field_path}'")):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("field_name", COMMAND_NODE_FIELDS)
def test_compiled_artifact_requires_every_serialized_command_field(artifact_payload: dict[str, Any], field_name: str) -> None:
    payload = artifact_payload.copy()
    payload["compiled_effect_catalog"] = artifact_payload["compiled_effect_catalog"].copy()
    payload["compiled_effect_catalog"]["effects"] = artifact_payload["compiled_effect_catalog"]["effects"].copy()
    payload["compiled_effect_catalog"]["effects"]["ate_food"] = artifact_payload["compiled_effect_catalog"]["effects"]["ate_food"].copy()
    payload["compiled_effect_catalog"]["effects"]["ate_food"]["on_spawn"] = [
        artifact_payload["compiled_effect_catalog"]["effects"]["ate_food"]["on_spawn"][0].copy()
    ]
    command = payload["compiled_effect_catalog"]["effects"]["ate_food"]["on_spawn"][0]
    command.pop(field_name)

    _assert_missing_field(payload, f"compiled_effect_catalog.effects.ate_food.on_spawn[0].{field_name}")


@pytest.mark.parametrize("field_name", ("when", "commands"))
def test_compiled_artifact_requires_every_serialized_switch_case_field(artifact_payload: dict[str, Any], field_name: str) -> None:
    payload = artifact_payload.copy()
    payload["compiled_effect_catalog"] = artifact_payload["compiled_effect_catalog"].copy()
    payload["compiled_effect_catalog"]["effects"] = artifact_payload["compiled_effect_catalog"]["effects"].copy()
    payload["compiled_effect_catalog"]["effects"]["ate_food"] = artifact_payload["compiled_effect_catalog"]["effects"]["ate_food"].copy()
    payload["compiled_effect_catalog"]["effects"]["ate_food"]["on_spawn"] = [
        artifact_payload["compiled_effect_catalog"]["effects"]["ate_food"]["on_spawn"][0].copy()
    ]
    command = payload["compiled_effect_catalog"]["effects"]["ate_food"]["on_spawn"][0]
    command["type"] = "switch"
    command["switch_expr"] = "1"
    command["cases"] = [{"when": "1", "commands": []}]
    command["cases"][0].pop(field_name)

    _assert_missing_field(payload, f"compiled_effect_catalog.effects.ate_food.on_spawn[0].cases[0].{field_name}")


@pytest.mark.parametrize("field_name", COMPILED_VFS_PROFILE_FIELDS)
def test_compiled_artifact_requires_every_vfs_profile_field(artifact_payload: dict[str, Any], field_name: str) -> None:
    payload = artifact_payload.copy()
    payload["compiled_vfs_profiles"] = artifact_payload["compiled_vfs_profiles"].copy()
    payload["compiled_vfs_profiles"].pop(field_name)

    _assert_missing_field(payload, f"compiled_vfs_profiles.{field_name}")


@pytest.mark.parametrize("profile_name", ("global_profile", "agent_profile"))
@pytest.mark.parametrize("field_name", ("variables", "dependencies"))
def test_compiled_artifact_requires_every_global_style_profile_field(
    artifact_payload: dict[str, Any], profile_name: str, field_name: str
) -> None:
    payload = artifact_payload.copy()
    payload["compiled_vfs_profiles"] = artifact_payload["compiled_vfs_profiles"].copy()
    payload["compiled_vfs_profiles"][profile_name] = artifact_payload["compiled_vfs_profiles"][profile_name].copy()
    payload["compiled_vfs_profiles"][profile_name].pop(field_name)

    _assert_missing_field(payload, f"compiled_vfs_profiles.{profile_name}.{field_name}")


@pytest.mark.parametrize("field_name", ("profile_name", "variables"))
def test_compiled_artifact_requires_every_item_profile_field(artifact_payload: dict[str, Any], field_name: str) -> None:
    payload = artifact_payload.copy()
    payload["compiled_vfs_profiles"] = artifact_payload["compiled_vfs_profiles"].copy()
    payload["compiled_vfs_profiles"]["item_profiles"] = artifact_payload["compiled_vfs_profiles"]["item_profiles"].copy()
    payload["compiled_vfs_profiles"]["item_profiles"]["default_item"] = artifact_payload["compiled_vfs_profiles"]["item_profiles"][
        "default_item"
    ].copy()
    payload["compiled_vfs_profiles"]["item_profiles"]["default_item"].pop(field_name)

    _assert_missing_field(payload, f"compiled_vfs_profiles.item_profiles.default_item.{field_name}")


@pytest.mark.parametrize("field_name", COMPILED_VARIABLE_FIELDS)
def test_compiled_artifact_requires_every_serialized_vfs_variable_field(artifact_payload: dict[str, Any], field_name: str) -> None:
    payload = artifact_payload.copy()
    payload["compiled_vfs_profiles"] = artifact_payload["compiled_vfs_profiles"].copy()
    payload["compiled_vfs_profiles"]["global_profile"] = artifact_payload["compiled_vfs_profiles"]["global_profile"].copy()
    payload["compiled_vfs_profiles"]["global_profile"]["variables"] = [
        artifact_payload["compiled_vfs_profiles"]["global_profile"]["variables"][0].copy()
    ]
    variable = payload["compiled_vfs_profiles"]["global_profile"]["variables"][0]
    variable.pop(field_name)

    _assert_missing_field(payload, f"compiled_vfs_profiles.global_profile.variables[0].{field_name}")


@pytest.mark.parametrize("field_name", LEVEL_FIELDS)
def test_compiled_artifact_requires_every_serialized_level_field(artifact_payload: dict[str, Any], field_name: str) -> None:
    payload = artifact_payload.copy()
    payload["all_levels"] = artifact_payload["all_levels"].copy()
    payload["all_levels"]["L0_demo"] = artifact_payload["all_levels"]["L0_demo"].copy()
    payload["all_levels"]["L0_demo"].pop(field_name)

    _assert_missing_field(payload, f"all_levels.L0_demo.{field_name}")


@pytest.mark.parametrize("field_name", ("cascade_data", "modulation_data", "affordance_position_map"))
def test_compiled_artifact_requires_every_level_optimization_field(artifact_payload: dict[str, Any], field_name: str) -> None:
    payload = artifact_payload.copy()
    payload["all_levels"] = artifact_payload["all_levels"].copy()
    payload["all_levels"]["L0_demo"] = artifact_payload["all_levels"]["L0_demo"].copy()
    payload["all_levels"]["L0_demo"]["optimization_data_raw"] = artifact_payload["all_levels"]["L0_demo"]["optimization_data_raw"].copy()
    payload["all_levels"]["L0_demo"]["optimization_data_raw"].pop(field_name)

    _assert_missing_field(payload, f"all_levels.L0_demo.optimization_data_raw.{field_name}")
