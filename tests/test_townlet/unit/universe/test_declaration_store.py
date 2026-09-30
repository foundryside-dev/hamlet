"""Authoring transport never selects a declaration's meaning."""

from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path

import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

CONFIGS = Path(__file__).parents[4] / "configs"
LEVEL = "L3_temporal_mechanics"


@pytest.fixture
def pack(tmp_path: Path) -> Path:
    destination = tmp_path / "pack"
    shutil.copytree(CONFIGS / "default_curriculum", destination, ignore=shutil.ignore_patterns(".compiled"))
    return destination


def semantic_hashes(universe) -> dict[str, str | None]:
    result = {
        field.name: getattr(universe, field.name)
        for field in dataclasses.fields(universe)
        if field.name.endswith("_hash")
    }
    for level, metadata in universe.all_levels.items():
        result.update(
            {
                f"{level}.{field.name}": getattr(metadata, field.name)
                for field in dataclasses.fields(metadata)
                if field.name.endswith("_hash")
            }
        )
    return result


def test_drive_can_move_to_nested_arbitrary_filename(pack: Path) -> None:
    compiler = UniverseCompiler()
    before = compiler.compile(pack, primary_level=LEVEL, use_cache=False)
    origin = pack / "levels" / LEVEL / "drive.yaml"
    destination = origin.parent / "weather" / "mission.yml"
    destination.parent.mkdir()
    origin.rename(destination)
    after = compiler.compile(pack, primary_level=LEVEL, use_cache=False)
    assert semantic_hashes(before) == semantic_hashes(after)
    assert before.metadata.config_hash != after.metadata.config_hash


def test_multiple_yaml_documents_can_share_one_file(pack: Path) -> None:
    compiler = UniverseCompiler()
    before = compiler.compile(pack, primary_level=LEVEL, use_cache=False)
    directory = pack / "levels" / LEVEL
    sections = [yaml.safe_load((directory / name).read_text()) for name in ("drive.yaml", "curriculum.yaml")]
    (directory / "mission.yaml").write_text(yaml.safe_dump_all(sections, sort_keys=False))
    (directory / "drive.yaml").unlink()
    (directory / "curriculum.yaml").unlink()
    after = compiler.compile(pack, primary_level=LEVEL, use_cache=False)
    assert semantic_hashes(before) == semantic_hashes(after)


def test_unknown_document_is_refused_with_origin(pack: Path) -> None:
    origin = pack / "unused.yaml"
    origin.write_text("unrecognised_mechanic: true\n")
    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    assert f"{origin}:1" in str(caught.value)
    assert "declaration" in str(caught.value).lower()


def test_duplicate_drive_names_both_origins(pack: Path) -> None:
    origin = pack / "levels" / LEVEL / "drive.yaml"
    duplicate = origin.with_name("duplicate.yaml")
    shutil.copyfile(origin, duplicate)
    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    assert f"{origin}:1" in str(caught.value)
    assert f"{duplicate}:1" in str(caught.value)


def test_missing_drive_names_declaration_instead_of_filename(pack: Path) -> None:
    (pack / "levels" / LEVEL / "drive.yaml").unlink()
    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    assert "drive declaration" in str(caught.value).lower()
    assert "drive.yaml" not in str(caught.value)


def test_original_items_smoke_refuses_every_ignored_file(tmp_path: Path) -> None:
    pack = tmp_path / "original_items_smoke"
    shutil.copytree(CONFIGS / "test" / "items_smoke", pack, ignore=shutil.ignore_patterns(".compiled"))
    strays = Path(__file__).parents[2] / "fixtures" / "declaration_store" / "items_smoke_strays"
    for stray in strays.iterdir():
        shutil.copyfile(stray, pack / stray.name)
    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(pack, primary_level="L0_smoke", use_cache=False)
    message = str(caught.value)
    for filename in ("substrate.yaml", "drive_as_code.yaml", "bars.yaml", "affordances.yaml", "training.yaml"):
        assert str(pack / filename) in message
    assert "experiment.yaml" not in message


def test_clock_period_reference_preserves_compiled_semantics(pack: Path) -> None:
    compiler = UniverseCompiler()
    before = compiler.compile(pack, primary_level=LEVEL, use_cache=False)
    origin = pack / "levels" / LEVEL / "curriculum.yaml"
    data = yaml.safe_load(origin.read_text())
    data["curriculum"]["day_length"] = {"period_of": "day_phase"}
    origin.write_text(yaml.safe_dump(data, sort_keys=False))
    after = compiler.compile(pack, primary_level=LEVEL, use_cache=False)
    assert after.get_level(LEVEL).curriculum.curriculum.day_length == 24
    assert semantic_hashes(before) == semantic_hashes(after)
