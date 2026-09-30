"""Guardrail tests for v2.1 config size limits."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.universe.loaders.v21 import load_v21_configs
from townlet.universe.validation import limits
from townlet.universe.validation.limits import MAX_ITEM_TYPES, MAX_SPAWN_RULES_PER_ITEM, MAX_VFS_PROFILES


def _make_item_types(count: int, *, profile: str = "default") -> list[dict]:
    """Generate minimal item_type entries."""
    return [
        {
            "id": f"item_{idx}",
            "name": f"Item {idx}",
            "icon": "i",
            "tags": ["tag"],
            "vfs_profile": profile,
            "duration": None,
            "cooldown": None,
            "interactions": {
                "on_pickup": [],
                "on_use": [],
                "on_drop": [],
                "local_commands": [],
                "inventory_commands": [],
            },
        }
        for idx in range(count)
    ]


def _write_items_catalog(config_dir: Path, *, item_types: list[dict]) -> None:
    """Override items.yaml with provided catalog."""
    catalog = {
        "items": {
            "version": "1.0",
            "max_items_per_agent": 3,
            "max_items_in_world": 50,
            "item_types": item_types,
        }
    }
    (config_dir / "items.yaml").write_text(yaml.safe_dump(catalog))


def _write_variables(config_dir: Path, *, profile_count: int) -> None:
    """Declare explicit item-profile groups and one scalar variable in each."""
    profiles = [f"profile_{idx}" for idx in range(profile_count)]
    variables = {
        "variables": {
            "version": "1.0",
            "evaluation_mode": "mark_and_sweep",
            "debug_logging": False,
            "extents": {},
            "item_profiles": profiles,
            "declarations": [
                {
                    "id": "value",
                    "profile": profile,
                    "scope": "item",
                    "type": "scalar",
                    "lifetime": "episode",
                    "semantic_type": "custom",
                    "initial_value": idx,
                    "exposed_to": [],
                }
                for idx, profile in enumerate(profiles)
            ],
        }
    }
    (config_dir / "variables.yaml").write_text(yaml.safe_dump(variables))


def test_item_catalog_rejects_more_than_max_item_types(tmp_path: Path) -> None:
    """items.yaml should fail fast when item_types exceeds MAX_ITEM_TYPES."""
    config_dir = prepare_config_dir(tmp_path, name="too_many_items")
    _write_variables(config_dir, profile_count=1)
    _write_items_catalog(config_dir, item_types=_make_item_types(MAX_ITEM_TYPES + 1))

    compiler = UniverseCompiler()
    with pytest.raises(CompilationError, match="item_types exceeds safety limit"):
        compiler.compile(config_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)


def test_item_catalog_limit_is_enforced_by_limits_validation_after_dto_load(tmp_path: Path) -> None:
    """Stage 1 should load DTOs; the limits validator should own safety limit policy."""
    config_dir = prepare_config_dir(tmp_path, name="too_many_items_limits_module")
    _write_variables(config_dir, profile_count=1)
    _write_items_catalog(config_dir, item_types=_make_item_types(MAX_ITEM_TYPES + 1))

    raw = load_v21_configs(config_dir)

    with pytest.raises(CompilationError, match="item_types exceeds safety limit"):
        limits.validate_v21_limits(raw, config_dir, source_map=None)


def test_spawn_rules_per_item_are_capped(tmp_path: Path) -> None:
    """Level item appearances should enforce a per-item spawn rule cap."""
    config_dir = prepare_config_dir(tmp_path, name="too_many_spawn_rules")
    _write_variables(config_dir, profile_count=1)
    _write_items_catalog(config_dir, item_types=_make_item_types(1))

    level_items_path = config_dir / "levels" / PRIMARY_LEVEL_NAME / "items.yaml"
    level_items = [{"item_type": "item_0", "spawn_count": 1, "placement": {"mode": "random"}} for _ in range(MAX_SPAWN_RULES_PER_ITEM + 1)]
    level_items_path.parent.mkdir(parents=True, exist_ok=True)
    level_items_path.write_text(yaml.safe_dump({"version": "1.0", "items": level_items}))

    compiler = UniverseCompiler()
    with pytest.raises(CompilationError, match="spawn rules exceed safety limit"):
        compiler.compile(config_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)


def test_item_profile_group_count_is_capped(tmp_path: Path) -> None:
    """Named item groups are bounded independently of their variable counts."""
    config_dir = prepare_config_dir(tmp_path, name="too_many_profiles")
    _write_variables(config_dir, profile_count=MAX_VFS_PROFILES + 1)
    path = config_dir / "variables.yaml"
    data = yaml.safe_load(path.read_text())
    data["variables"]["declarations"] = []
    path.write_text(yaml.safe_dump(data))
    _write_items_catalog(config_dir, item_types=_make_item_types(1, profile="profile_0"))

    compiler = UniverseCompiler()
    with pytest.raises(CompilationError, match="Variables item profile count exceeds safety limit") as caught:
        compiler.compile(config_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    assert f"{MAX_VFS_PROFILES + 1} (max {MAX_VFS_PROFILES})" in str(caught.value)
    assert caught.value.issues[0].code == "CONFIG_LIMIT_EXCEEDED"
    assert caught.value.issues[0].location == f"{config_dir / 'variables.yaml'}:1"
