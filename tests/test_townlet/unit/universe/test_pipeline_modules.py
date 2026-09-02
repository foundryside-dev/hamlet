"""Direct tests for extracted universe compiler stage modules."""

from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from townlet.universe.errors import CompilationError
from townlet.universe.loaders.preflight import validate_scoping, validate_yaml_syntax
from townlet.universe.loaders.v21 import load_v21_configs
from townlet.universe.validation.feasibility import grid_capacity_for_substrate
from townlet.universe.validation.references import build_symbol_table, resolve_references
from townlet.universe.validation.semantics import select_primary_level, validate_v21_semantics


def _copy_experiment(tmp_path: Path) -> Path:
    source = Path("configs/test/model_config")
    dest = tmp_path / source.name
    shutil.copytree(source, dest)
    return dest


def test_load_v21_configs_returns_raw_configs(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)

    raw = load_v21_configs(config_dir)

    assert "L0_test" in raw.levels


def test_load_v21_configs_loads_root_optional_artifacts(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    (config_dir / "action_labels.yaml").write_text(yaml.safe_dump({"custom": {0: "PORT"}}))

    raw = load_v21_configs(config_dir)

    assert raw.vfs_profiles is not None
    assert raw.effects is not None
    assert raw.action_label_overrides == {0: "PORT"}
    assert raw.variables_reference is not None
    assert {var.id for var in raw.variables_reference} == {"position"}


def test_validate_yaml_syntax_checks_optional_root_yaml(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    (config_dir / "action_labels.yaml").write_text("custom: [broken: yaml")

    with pytest.raises(CompilationError, match="Stage 0: Preflight validation"):
        validate_yaml_syntax(config_dir)


def test_resolve_references_accepts_valid_pack(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    raw = load_v21_configs(config_dir)
    symbol_table = build_symbol_table(raw)

    resolve_references(raw, symbol_table, config_dir)


def test_resolve_references_validates_dac_bar_references(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    drive_path = config_dir / "levels" / "L0_test" / "drive.yaml"
    drive_doc = yaml.safe_load(drive_path.read_text())
    drive_doc["drive"]["modifiers"]["energy_crisis"]["bar"] = "missing_energy"
    drive_path.write_text(yaml.safe_dump(drive_doc))
    raw = load_v21_configs(config_dir)
    symbol_table = build_symbol_table(raw)

    with pytest.raises(CompilationError, match="Modifier 'energy_crisis' references undefined bar: missing_energy"):
        resolve_references(raw, symbol_table, config_dir)


def test_resolve_references_allows_profile_vfs_variables_in_dac(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    (config_dir / "vfs_profiles.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "evaluation_mode": "mark_and_sweep",
                "debug_logging": False,
                "global_profile": {
                    "variables": [
                        {
                            "semantic_type": "custom",
                            "name": "hunger_pressure",
                            "type": "float",
                            "initial_value": 0.0,
                        }
                    ]
                },
                "item_profiles": [],
            },
            sort_keys=False,
        )
    )
    drive_path = config_dir / "levels" / "L0_test" / "drive.yaml"
    drive_doc = yaml.safe_load(drive_path.read_text())
    drive_doc["drive"]["extrinsic"]["variable_bonuses"] = [{"variable": "hunger_pressure", "weight": 0.25}]
    drive_path.write_text(yaml.safe_dump(drive_doc, sort_keys=False))

    raw = load_v21_configs(config_dir)
    symbol_table = build_symbol_table(raw)

    resolve_references(raw, symbol_table, config_dir)


def test_preflight_rejects_level_directory_directly(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)

    with pytest.raises(CompilationError, match="Cannot validate level directory directly"):
        validate_scoping(config_dir / "levels" / "L0_test")


def test_select_primary_level_rejects_unknown_level() -> None:
    levels = {"L0_test": object()}

    with pytest.raises(ValueError, match="Primary level 'missing' not found"):
        select_primary_level(levels, "missing")


def test_select_primary_level_requires_explicit_level() -> None:
    levels = {"L0_test": object()}

    with pytest.raises(ValueError, match="explicit primary_level"):
        select_primary_level(levels, None)


def test_load_v21_configs_rejects_legacy_action_costs(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    actions_path = config_dir / "actions.yaml"
    actions_doc = yaml.safe_load(actions_path.read_text())
    actions_doc["actions"]["custom_actions"][0]["costs"] = {"energy": 1.0}
    actions_path.write_text(yaml.safe_dump(actions_doc, sort_keys=False))

    with pytest.raises(CompilationError) as exc_info:
        load_v21_configs(config_dir)

    error_msg = str(exc_info.value)
    assert "costs" in error_msg
    assert "extra" in error_msg.lower() or "not permitted" in error_msg.lower()


def test_validate_v21_semantics_rejects_cascade_with_unknown_meter(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    environment_path = config_dir / "environment.yaml"
    environment_doc = yaml.safe_load(environment_path.read_text())
    environment_doc["environment"]["cascade_graph"][0]["source"] = "missing_meter"
    environment_path.write_text(yaml.safe_dump(environment_doc, sort_keys=False))

    raw = load_v21_configs(config_dir)

    with pytest.raises(CompilationError, match="CASCADE_INVALID_METER"):
        validate_v21_semantics(raw, config_dir, source_map=None)


def test_validate_v21_semantics_rejects_cascade_cycle(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    environment_path = config_dir / "environment.yaml"
    environment_doc = yaml.safe_load(environment_path.read_text())
    environment_doc["environment"]["cascade_graph"].append(
        {
            "source": "health",
            "target": "satiation",
            "description": "cycle for semantic validation test",
        }
    )
    bars_path = config_dir / "levels" / "L0_test" / "bars.yaml"
    bars_doc = yaml.safe_load(bars_path.read_text())
    bars_doc["bars"]["cascades"].append({"source": "health", "target": "satiation", "threshold": 0.3, "strength": 0.1})
    environment_path.write_text(yaml.safe_dump(environment_doc, sort_keys=False))
    bars_path.write_text(yaml.safe_dump(bars_doc, sort_keys=False))

    raw = load_v21_configs(config_dir)

    with pytest.raises(CompilationError, match="CASCADE_CYCLE"):
        validate_v21_semantics(raw, config_dir, source_map=None)


def test_validate_v21_semantics_rejects_modulation_with_unknown_bar(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    environment_path = config_dir / "environment.yaml"
    environment_doc = yaml.safe_load(environment_path.read_text())
    environment_doc["environment"]["modulation_graph"][0]["bar"] = "missing_bar"
    environment_path.write_text(yaml.safe_dump(environment_doc, sort_keys=False))

    raw = load_v21_configs(config_dir)

    with pytest.raises(CompilationError, match="MODULATION_INVALID_REFERENCE"):
        validate_v21_semantics(raw, config_dir, source_map=None)


def test_validate_v21_semantics_rejects_missing_level_modulation(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    affordances_path = config_dir / "levels" / "L0_test" / "affordances.yaml"
    affordances_doc = yaml.safe_load(affordances_path.read_text())
    affordances_doc["affordances"]["modulations"] = affordances_doc["affordances"]["modulations"][1:]
    affordances_path.write_text(yaml.safe_dump(affordances_doc, sort_keys=False))

    raw = load_v21_configs(config_dir)

    with pytest.raises(CompilationError, match="MODULATION_MISSING"):
        validate_v21_semantics(raw, config_dir, source_map=None)


def test_validate_v21_semantics_rejects_level_meter_vocab_mismatch(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    bars_path = config_dir / "levels" / "L0_test" / "bars.yaml"
    bars_doc = yaml.safe_load(bars_path.read_text())
    bars_doc["bars"]["meters"] = bars_doc["bars"]["meters"][1:]
    bars_path.write_text(yaml.safe_dump(bars_doc, sort_keys=False))

    raw = load_v21_configs(config_dir)

    with pytest.raises(CompilationError, match="METER_VOCAB_MISMATCH"):
        validate_v21_semantics(raw, config_dir, source_map=None)


def test_validate_v21_semantics_rejects_level_affordance_vocab_mismatch(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    affordances_path = config_dir / "levels" / "L0_test" / "affordances.yaml"
    affordances_doc = yaml.safe_load(affordances_path.read_text())
    affordances_doc["affordances"]["affordances"] = [aff for aff in affordances_doc["affordances"]["affordances"] if aff["name"] != "WORK"]
    affordances_path.write_text(yaml.safe_dump(affordances_doc, sort_keys=False))

    raw = load_v21_configs(config_dir)

    with pytest.raises(CompilationError, match="AFFORDANCE_VOCAB_MISMATCH"):
        validate_v21_semantics(raw, config_dir, source_map=None)


def test_validate_v21_semantics_rejects_affordance_cost_with_unknown_meter(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    affordances_path = config_dir / "levels" / "L0_test" / "affordances.yaml"
    affordances_doc = yaml.safe_load(affordances_path.read_text())
    affordances_doc["affordances"]["affordances"][0]["costs"]["bogus_meter"] = 1.0
    affordances_path.write_text(yaml.safe_dump(affordances_doc, sort_keys=False))

    raw = load_v21_configs(config_dir)

    with pytest.raises(CompilationError, match="AFFORDANCE_INVALID_METER"):
        validate_v21_semantics(raw, config_dir, source_map=None)


def test_validate_v21_semantics_rejects_affordance_interaction_with_unknown_meter(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    affordances_path = config_dir / "levels" / "L0_test" / "affordances.yaml"
    affordances_doc = yaml.safe_load(affordances_path.read_text())
    affordances_doc["affordances"]["affordances"][0]["interactions"]["on_start"][0]["modify"] = "target.bar.bogus_meter"
    affordances_path.write_text(yaml.safe_dump(affordances_doc, sort_keys=False))

    raw = load_v21_configs(config_dir)

    with pytest.raises(CompilationError, match="AFFORDANCE_INVALID_METER"):
        validate_v21_semantics(raw, config_dir, source_map=None)


def test_validate_v21_semantics_rejects_unknown_enabled_affordance(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    training_path = config_dir / "levels" / "L0_test" / "training.yaml"
    training_doc = yaml.safe_load(training_path.read_text())
    training_doc["training"]["enabled_affordances"].append("BOGUS_JOB")
    training_path.write_text(yaml.safe_dump(training_doc, sort_keys=False))

    raw = load_v21_configs(config_dir)

    with pytest.raises(CompilationError, match="ENABLED_AFFORDANCES_INVALID"):
        validate_v21_semantics(raw, config_dir, source_map=None)


@pytest.mark.parametrize("missing_field", ("enabled_affordances", "population.size"))
def test_validate_v21_semantics_has_no_fallback_for_required_training_fields(tmp_path: Path, missing_field: str) -> None:
    """Schema-erased required fields must fail instead of acquiring compatibility defaults."""
    config_dir = _copy_experiment(tmp_path)
    raw = load_v21_configs(config_dir)
    training = raw.levels["L0_test"].training
    if missing_field == "population.size":
        del training.population.size
    else:
        del training.enabled_affordances

    with pytest.raises(AttributeError, match=missing_field.rsplit(".", maxsplit=1)[-1]):
        validate_v21_semantics(raw, config_dir, source_map=None)


def test_validate_v21_semantics_rejects_grid_capacity_exceeded(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    stratum_path = config_dir / "stratum.yaml"
    stratum_doc = yaml.safe_load(stratum_path.read_text())
    stratum_doc["stratum"]["substrate"]["grid"]["width"] = 2
    stratum_doc["stratum"]["substrate"]["grid"]["height"] = 2
    stratum_path.write_text(yaml.safe_dump(stratum_doc, sort_keys=False))

    raw = load_v21_configs(config_dir)

    with pytest.raises(CompilationError, match="GRID_CAPACITY_EXCEEDED"):
        validate_v21_semantics(raw, config_dir, source_map=None)


def test_grid_capacity_for_gridnd_substrate() -> None:
    substrate = SimpleNamespace(type="gridnd", gridnd=SimpleNamespace(dimension_sizes=[2, 3, 5]))

    assert grid_capacity_for_substrate(substrate) == 30
