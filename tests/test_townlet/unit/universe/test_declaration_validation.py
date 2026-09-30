"""Validation diagnostics follow declaration identity rather than YAML filenames."""

from __future__ import annotations

import re
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from townlet.config.items_config import ItemAppearanceRuleConfig, ItemsAppearanceConfig, ItemsCatalogConfig, ItemTypeConfig
from townlet.config.vfs_profiles_config import VFSProfilesConfig
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError
from townlet.universe.loaders.v21 import load_v21_configs
from townlet.universe.source_map import SourceMap
from townlet.universe.symbol_table import UniverseSymbolTable
from townlet.universe.validation import limits
from townlet.universe.validation.references import build_symbol_table, resolve_references
from townlet.universe.validation.semantics import validate_v21_semantics

PACK = Path("configs/test/model_config")
LEVEL = "L0_test"


def test_semantics_of_loaded_declarations_do_not_recheck_transport_files(tmp_path: Path) -> None:
    raw = load_v21_configs(PACK)

    validate_v21_semantics(raw, tmp_path, source_map=SourceMap())


@pytest.mark.parametrize(
    ("mismatch", "family", "code"),
    [
        ("meters", "bars", ErrorCode.METER_VOCAB_MISMATCH),
        ("affordances", "affordances", ErrorCode.AFFORDANCE_VOCAB_MISMATCH),
        ("missing_cascade", "bars", ErrorCode.CASCADE_MISSING),
        ("extra_cascade", "bars", ErrorCode.CASCADE_EXTRA),
        ("missing_modulation", "affordances", ErrorCode.MODULATION_MISSING),
        ("extra_modulation", "affordances", ErrorCode.MODULATION_EXTRA),
    ],
)
def test_lockstep_diagnostics_name_both_relocated_declarations(tmp_path: Path, mismatch: str, family: str, code: ErrorCode) -> None:
    raw = load_v21_configs(PACK)
    level = raw.levels[LEVEL]
    if mismatch == "meters":
        level.bars.meters.pop()
    elif mismatch == "affordances":
        level.affordances.affordances.pop()
    elif mismatch == "missing_cascade":
        level.bars.cascades.pop()
    elif mismatch == "extra_cascade":
        level.bars.cascades.append(level.bars.cascades[0].model_copy(update={"source": "energy", "target": "money"}))
    elif mismatch == "missing_modulation":
        level.affordances.modulations.pop()
    else:
        level.affordances.modulations.append(level.affordances.modulations[0].model_copy(update={"bar": "health", "affordances": ["EAT"]}))

    environment_path = tmp_path / "transport" / "vocabulary.yml"
    level_path = tmp_path / "levels" / LEVEL / "rules" / "mechanics.yml"
    source_map = SourceMap()
    source_map.record("environment", environment_path, 4)
    source_map.record(f"levels/{LEVEL}/{family}", level_path, 37)

    with pytest.raises(CompilationError) as caught:
        validate_v21_semantics(raw, PACK, source_map)

    issue = next(issue for issue in caught.value.issues if issue.code == code)
    assert issue.location == f"{level_path}:37"
    assert f"{environment_path}:4" in issue.message
    assert ".yaml" not in issue.message


@pytest.mark.parametrize(
    ("limit_name", "family", "code"),
    [
        ("MAX_METERS", "environment", ErrorCode.CONFIG_LIMIT_EXCEEDED),
        ("MAX_AFFORDANCES", "environment", ErrorCode.CONFIG_LIMIT_EXCEEDED),
        ("MAX_CASCADES", "environment", ErrorCode.CONFIG_LIMIT_EXCEEDED),
        ("MAX_VARIABLES", "environment", ErrorCode.CONFIG_LIMIT_EXCEEDED),
        ("MAX_ACTIONS", "actions", ErrorCode.CONFIG_LIMIT_EXCEEDED),
        ("MAX_GRID_CELLS", "stratum", ErrorCode.GRID_SIZE_LIMIT_EXCEEDED),
        ("MAX_ITEM_TYPES", "items", ErrorCode.ITEM_TYPES_LIMIT_EXCEEDED),
        ("MAX_SPAWN_RULES_PER_ITEM", f"levels/{LEVEL}/items_appearance", ErrorCode.SPAWN_RULE_LIMIT_EXCEEDED),
    ],
)
def test_limit_diagnostics_use_relocated_family_origin(tmp_path: Path, monkeypatch, limit_name: str, family: str, code: ErrorCode) -> None:
    raw = load_v21_configs(PACK)
    if limit_name == "MAX_ITEM_TYPES":
        item_type = ItemTypeConfig.model_validate(
            {
                "id": "tool",
                "name": "Tool",
                "icon": "t",
                "tags": ["tool"],
                "vfs_profile": "tool",
                "duration": None,
                "cooldown": None,
                "interactions": {"on_pickup": [], "on_use": [], "on_drop": [], "local_commands": [], "inventory_commands": []},
            }
        )
        raw = replace(raw, items=ItemsCatalogConfig(version="1.0", item_types=[item_type], max_items_per_agent=1, max_items_in_world=1))
    if limit_name == "MAX_SPAWN_RULES_PER_ITEM":
        raw.levels[LEVEL] = replace(
            raw.levels[LEVEL],
            items_appearance=ItemsAppearanceConfig(version="1.0", items=[ItemAppearanceRuleConfig(item_type="tool", spawn_count=1)]),
        )
    monkeypatch.setattr(limits, limit_name, 0)
    origin = tmp_path / "transport" / "declarations.yml"
    source_map = SourceMap()
    source_map.record(family, origin, 19)

    with pytest.raises(CompilationError) as caught:
        limits.validate_v21_limits(raw, PACK, source_map=source_map)

    issue = next(issue for issue in caught.value.issues if issue.code == code)
    assert issue.location == f"{origin}:19"
    assert ".yaml" not in issue.message


def test_nested_dac_reference_uses_relocated_entry_origin(tmp_path: Path) -> None:
    raw = load_v21_configs(PACK)
    raw.levels[LEVEL].drive.extrinsic.bar_bonuses[0].bar = "unknown_bar"
    origin = tmp_path / "levels" / LEVEL / "rewards" / "objective.yml"
    source_map = SourceMap()
    source_map.record(f"levels/{LEVEL}/drive:extrinsic.bar_bonuses[0]", origin, 29)

    with pytest.raises(CompilationError) as caught:
        resolve_references(raw, build_symbol_table(raw), PACK, source_map)

    issue = next(issue for issue in caught.value.issues if issue.code == ErrorCode.DAC_REF_UNDEFINED_BAR_BONUS_BAR)
    assert issue.location == f"{origin}:29"


def test_affordance_reference_uses_relocated_named_origin(tmp_path: Path) -> None:
    raw = load_v21_configs(PACK)
    affordance = raw.levels[LEVEL].affordances.affordances[0]
    affordance.interactions["on_start"][0].modify = "target.vfs.missing_value"
    origin = tmp_path / "levels" / LEVEL / "mechanics" / "interactions.yml"
    source_map = SourceMap()
    source_map.record(f"levels/{LEVEL}/affordances:{affordance.name}", origin, 11)

    with pytest.raises(CompilationError) as caught:
        resolve_references(raw, build_symbol_table(raw), PACK, source_map)

    issue = next(issue for issue in caught.value.issues if issue.code == ErrorCode.UAC_RES_VFS)
    assert issue.location == f"{origin}:11"


def test_item_appearance_reference_uses_relocated_family_origin(tmp_path: Path) -> None:
    raw = load_v21_configs(PACK)
    raw.levels[LEVEL] = replace(
        raw.levels[LEVEL],
        items_appearance=ItemsAppearanceConfig(version="1.0", items=[ItemAppearanceRuleConfig(item_type="missing_tool", spawn_count=1)]),
    )
    origin = tmp_path / "levels" / LEVEL / "objects" / "spawns.yml"
    source_map = SourceMap()
    source_map.record(f"levels/{LEVEL}/items_appearance", origin, 7)

    with pytest.raises(CompilationError) as caught:
        resolve_references(raw, build_symbol_table(raw), PACK, source_map)

    issue = next(issue for issue in caught.value.issues if issue.code == ErrorCode.UAC_RES_ITEM)
    assert issue.location == f"{origin}:7"


def test_profile_registration_error_uses_qualified_profile_origin(tmp_path: Path, monkeypatch) -> None:
    """Same-named variables in different profiles never share diagnostic identity."""
    raw = load_v21_configs(PACK)
    variable = {"name": "shared", "type": "float", "initial_value": 0.0}
    raw = replace(
        raw,
        vfs_profiles=VFSProfilesConfig.model_validate(
            {
                "version": "1.0",
                "evaluation_mode": "mark_and_sweep",
                "debug_logging": False,
                "global_profile": {"variables": [{**variable, "semantic_type": "custom"}]},
                "agent_profile": {"variables": [{**variable, "semantic_type": "custom"}]},
                "item_profiles": [
                    {"profile_name": "tool", "variables": [variable]},
                    {"profile_name": "food", "variables": [variable]},
                ],
            }
        ),
    )
    source_map = SourceMap()
    origins = []
    for index, qualifier in enumerate(("global_profile", "agent_profile", "item_profiles:tool", "item_profiles:food"), start=1):
        path = tmp_path / "profiles" / f"{index}.yml"
        source_map.record(f"vfs_profiles:{qualifier}:shared", path, 8)
        origins.append(f"{path}:8")

    # Inject a domain registration failure to exercise provenance on its error boundary.
    def fail_registration(self, config):
        raise CompilationError("Symbols", ["Injected profile registration failure"])

    monkeypatch.setattr(UniverseSymbolTable, "register_profile_vfs_variable", fail_registration)
    with pytest.raises(CompilationError) as caught:
        build_symbol_table(raw, source_map)

    assert [issue.location for issue in caught.value.issues] == origins


@pytest.mark.parametrize("failure", ["limit", "vocabulary", "affordance_meter", "dac_reference"])
def test_compiler_validation_keeps_origins_after_transport_relocation(tmp_path: Path, monkeypatch, failure: str) -> None:
    config_dir = tmp_path / "relocated_pack"
    shutil.copytree(PACK, config_dir)
    environment_path = config_dir / "environment.yaml"
    level_dir = config_dir / "levels" / LEVEL
    if failure == "limit":
        family = "environment"
        code = ErrorCode.CONFIG_LIMIT_EXCEEDED
        monkeypatch.setattr(limits, "MAX_METERS", 0)
    elif failure == "vocabulary":
        family = "bars"
        code = ErrorCode.METER_VOCAB_MISMATCH
        path = level_dir / "bars.yaml"
        document = yaml.safe_load(path.read_text())
        document["bars"]["meters"].pop()
        path.write_text(yaml.safe_dump(document, sort_keys=False))
    elif failure == "affordance_meter":
        family = "affordances"
        code = ErrorCode.AFFORDANCE_INVALID_METER
        path = level_dir / "affordances.yaml"
        document = yaml.safe_load(path.read_text())
        document["affordances"]["affordances"][0]["costs"]["unknown_meter"] = 0.1
        path.write_text(yaml.safe_dump(document, sort_keys=False))
    else:
        family = "drive"
        code = ErrorCode.DAC_REF_UNDEFINED_BAR_BONUS_BAR
        path = level_dir / "drive.yaml"
        document = yaml.safe_load(path.read_text())
        document["drive"]["extrinsic"]["bar_bonuses"][0]["bar"] = "unknown_meter"
        path.write_text(yaml.safe_dump(document, sort_keys=False))

    relocated_environment = config_dir / "vocabulary" / "world.yml"
    relocated_environment.parent.mkdir()
    environment_path.rename(relocated_environment)
    if family == "environment":
        relocated = relocated_environment
    else:
        relocated = level_dir / "mechanics" / "declarations.yml"
        relocated.parent.mkdir()
        (level_dir / f"{family}.yaml").rename(relocated)

    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(config_dir, primary_level=LEVEL, use_cache=False)

    assert code in {issue.code for issue in caught.value.issues}, str(caught.value)
    issue = next(issue for issue in caught.value.issues if issue.code == code)
    assert re.fullmatch(rf"{re.escape(str(relocated))}:\d+", issue.location or ""), str(caught.value)
    if failure == "vocabulary":
        assert re.search(rf"{re.escape(str(relocated_environment))}:\d+", issue.message), issue.message
