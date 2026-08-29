"""Tests for SourceMap wiring: compile diagnostics carry file:line provenance."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.universe.source_map import build_pack_source_map


def _copy_experiment(tmp_path: Path) -> Path:
    source = Path("configs/test/model_config")
    dest = tmp_path / source.name
    shutil.copytree(source, dest)
    return dest


def test_build_pack_source_map_records_affordance_lines() -> None:
    source_map = build_pack_source_map(Path("configs/test/model_config"))

    located = source_map.lookup("levels/L0_test/affordances.yaml:EAT")
    assert located is not None
    path, _, line = located.rpartition(":")
    assert path.endswith("affordances.yaml")
    assert line.isdigit() and int(line) > 0


def test_build_pack_source_map_records_drive_modifier_lines() -> None:
    source_map = build_pack_source_map(Path("configs/test/model_config"))

    located = source_map.lookup("levels/L0_test/drive.yaml:modifiers.energy_crisis")
    assert located is not None
    assert re.search(r"drive\.yaml:\d+$", located)


def test_build_pack_source_map_records_cascade_lines() -> None:
    source_map = build_pack_source_map(Path("configs/test/model_config"))
    bars_doc = yaml.safe_load(Path("configs/test/model_config/levels/L0_test/bars.yaml").read_text())
    cascades = bars_doc["bars"]["cascades"]
    assert cascades, "test pack must declare at least one cascade"
    key = f"levels/L0_test/bars.yaml:{cascades[0]['source']}->{cascades[0]['target']}"

    located = source_map.lookup(key)
    assert located is not None
    assert re.search(r"bars\.yaml:\d+$", located)


def test_dac_reference_error_carries_drive_line(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    drive_path = config_dir / "levels" / "L0_test" / "drive.yaml"
    drive_doc = yaml.safe_load(drive_path.read_text())
    drive_doc["drive"]["modifiers"]["energy_crisis"]["bar"] = "missing_energy"
    drive_path.write_text(yaml.safe_dump(drive_doc))

    with pytest.raises(CompilationError) as excinfo:
        UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=False)

    message = str(excinfo.value)
    assert "DAC-REF-001" in message
    assert re.search(r"drive\.yaml:\d+", message), message


def test_affordance_semantic_error_carries_affordances_line(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    aff_path = config_dir / "levels" / "L0_test" / "affordances.yaml"
    aff_doc = yaml.safe_load(aff_path.read_text())
    aff_doc["affordances"]["affordances"][0]["costs"]["ghost_meter"] = 1.0
    aff_path.write_text(yaml.safe_dump(aff_doc))

    with pytest.raises(CompilationError) as excinfo:
        UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=False)

    message = str(excinfo.value)
    assert "AFFORDANCE_INVALID_METER" in message
    assert re.search(r"affordances\.yaml:\d+", message), message
