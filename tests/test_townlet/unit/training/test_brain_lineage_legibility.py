"""A brain fork must be legible at load time, not discovered at runtime (PDR-0027)."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pytest
import yaml

from townlet.training.checkpoint_utils import attach_universe_metadata
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/test/model_config")
LEVEL = "L0_test"


def _forked_pack(tmp_path: Path) -> Path:
    target = tmp_path / "forked"
    shutil.copytree(PACK, target)
    brain = yaml.safe_load((target / "brain.yaml").read_text())
    brain["architecture"]["feedforward"]["hidden_layers"] = [64, 64]
    (target / "levels" / LEVEL / "brain.yaml").write_text(yaml.safe_dump(brain, sort_keys=False))
    return target


def test_unforked_universe_has_matching_lineage_hashes(tmp_path: Path) -> None:
    pack_dir = tmp_path / "baseline"
    shutil.copytree(PACK, pack_dir)
    universe = UniverseCompiler().compile(pack_dir, primary_level=LEVEL, use_cache=False)
    assert universe.pack_brain_hash == universe.brain_hash
    assert universe.brain_forked is False


def test_forked_universe_carries_the_fork(tmp_path: Path) -> None:
    universe = UniverseCompiler().compile(_forked_pack(tmp_path), primary_level=LEVEL, use_cache=False)
    assert universe.pack_brain_hash != universe.brain_hash
    assert universe.brain_forked is True


def test_checkpoint_stamps_lineage_and_loader_states_the_fork(tmp_path: Path, caplog) -> None:
    universe = UniverseCompiler().compile(_forked_pack(tmp_path), primary_level=LEVEL, use_cache=False)
    checkpoint: dict = {}
    attach_universe_metadata(checkpoint, universe)
    assert checkpoint["pack_brain_hash"] == universe.pack_brain_hash
    assert checkpoint["brain_hash"] == universe.brain_hash

    from townlet.training.checkpoint_utils import surface_brain_lineage

    with caplog.at_level(logging.WARNING):
        surface_brain_lineage(checkpoint)
    assert any("brain lineage fork" in record.message for record in caplog.records)


def test_checkpoint_without_lineage_stamp_is_refused(tmp_path: Path) -> None:
    """Zero-backcompat: a pre-stamp checkpoint raises, same as every other missing hash."""
    universe = UniverseCompiler().compile(_forked_pack(tmp_path), primary_level=LEVEL, use_cache=False)
    checkpoint: dict = {}
    attach_universe_metadata(checkpoint, universe)
    del checkpoint["pack_brain_hash"]

    from townlet.training.checkpoint_utils import surface_brain_lineage

    with pytest.raises(ValueError, match="pack_brain_hash"):
        surface_brain_lineage(checkpoint)
