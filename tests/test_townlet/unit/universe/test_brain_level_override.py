"""Per-level brain.yaml override (PDR-0027, hamlet-0d0115383e).

A level directory MAY contain a complete brain.yaml; if present it replaces the
pack-root brain as the effective base for that level. A level that says nothing
inherits the pack brain unchanged.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/test/model_config")
LEVEL = "L0_test"


def _clone_pack(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(PACK, target)
    return target


def _write_level_brain(pack_dir: Path, hidden_layers: list[int]) -> None:
    brain = yaml.safe_load((pack_dir / "brain.yaml").read_text())
    brain["architecture"]["feedforward"]["hidden_layers"] = hidden_layers
    (pack_dir / "levels" / LEVEL / "brain.yaml").write_text(yaml.safe_dump(brain, sort_keys=False))


def test_level_without_brain_yaml_inherits_pack_brain(tmp_path: Path) -> None:
    pack_dir = _clone_pack(tmp_path, "baseline")
    universe = UniverseCompiler().compile(pack_dir, primary_level=LEVEL, use_cache=False)
    assert universe.brain.architecture.feedforward.hidden_layers == [256, 128]


def test_level_brain_yaml_replaces_pack_brain_and_moves_the_hash(tmp_path: Path) -> None:
    baseline_dir = _clone_pack(tmp_path, "baseline")
    forked_dir = _clone_pack(tmp_path, "forked")
    _write_level_brain(forked_dir, hidden_layers=[64, 64])

    compiler = UniverseCompiler()
    baseline = compiler.compile(baseline_dir, primary_level=LEVEL, use_cache=False)
    forked = compiler.compile(forked_dir, primary_level=LEVEL, use_cache=False)

    assert forked.brain.architecture.feedforward.hidden_layers == [64, 64]
    assert baseline.brain.architecture.feedforward.hidden_layers == [256, 128]
    assert forked.brain_hash != baseline.brain_hash


def test_adding_level_brain_yaml_changes_config_hash(tmp_path: Path) -> None:
    baseline_dir = _clone_pack(tmp_path, "baseline")
    forked_dir = _clone_pack(tmp_path, "forked")
    _write_level_brain(forked_dir, hidden_layers=[64, 64])

    compiler = UniverseCompiler()
    baseline = compiler.compile(baseline_dir, primary_level=LEVEL, use_cache=False)
    forked = compiler.compile(forked_dir, primary_level=LEVEL, use_cache=False)
    assert baseline.metadata.config_hash != forked.metadata.config_hash


def test_identical_level_brain_yaml_is_not_a_hash_fork(tmp_path: Path) -> None:
    baseline_dir = _clone_pack(tmp_path, "baseline")
    copied_dir = _clone_pack(tmp_path, "copied")
    shutil.copy(copied_dir / "brain.yaml", copied_dir / "levels" / LEVEL / "brain.yaml")

    compiler = UniverseCompiler()
    baseline = compiler.compile(baseline_dir, primary_level=LEVEL, use_cache=False)
    copied = compiler.compile(copied_dir, primary_level=LEVEL, use_cache=False)
    assert copied.brain_hash == baseline.brain_hash
