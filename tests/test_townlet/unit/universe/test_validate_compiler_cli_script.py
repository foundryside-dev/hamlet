"""Fleet validation discovers pack boundaries and reads declared experiment content."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.validate_compiler_cli import iter_config_dirs, resolve_primary_level, run_cli_validate


def relocated_pack(tmp_path: Path, fixture: str) -> Path:
    pack = tmp_path / "research" / fixture
    shutil.copytree(Path("configs/test") / fixture, pack, ignore=shutil.ignore_patterns(".compiled"))
    concepts = pack / "concepts" / "metadata"
    concepts.mkdir(parents=True)
    (pack / "experiment.yaml").rename(concepts / "scenario.yml")
    level = next((pack / "levels").iterdir())
    mechanics = level / "rules"
    mechanics.mkdir()
    (level / "drive.yaml").rename(mechanics / "reward-declaration.yml")
    return pack


def test_fleet_discovery_and_validation_use_relocated_declarations(tmp_path: Path) -> None:
    pack = relocated_pack(tmp_path, "model_config")

    assert iter_config_dirs(tmp_path) == [pack]
    assert iter_config_dirs(pack) == [pack]
    assert resolve_primary_level(pack) == "L0_test"
    run_cli_validate(pack)
    assert not (pack / ".compiled").exists()


def test_relocated_negative_fixture_still_fails_compiler_validation(tmp_path: Path) -> None:
    pack = relocated_pack(tmp_path, "vfs_type_mismatch")

    assert iter_config_dirs(tmp_path) == [pack]
    assert resolve_primary_level(pack) == "L0_type_mismatch"
    with pytest.raises(subprocess.CalledProcessError) as caught:
        run_cli_validate(pack)
    assert caught.value.returncode != 0
    run_cli_validate(pack, expect_failure=True)
