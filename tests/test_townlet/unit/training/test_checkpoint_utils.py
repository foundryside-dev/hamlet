"""Tests for checkpoint metadata helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.training.checkpoint_utils import (
    assert_checkpoint_dimensions,
    assert_checkpoint_vfs_hash,
    attach_universe_metadata,
    config_hash_warning,
    persist_checkpoint_digest,
    safe_torch_load,
    verify_checkpoint_digest,
)
from townlet.training.state import PopulationCheckpoint
from townlet.universe.compiler import UniverseCompiler


@pytest.fixture(scope="module")
def compiled_universe():
    compiler = UniverseCompiler()
    return compiler.compile(Path("configs/test/model_config"), primary_level="L0_test")


def test_attach_universe_metadata(compiled_universe) -> None:
    checkpoint: dict[str, object] = {}
    attach_universe_metadata(checkpoint, compiled_universe)

    assert checkpoint["config_hash"] == compiled_universe.metadata.config_hash
    assert checkpoint["observation_dim"] == compiled_universe.metadata.observation_dim
    assert checkpoint["action_dim"] == compiled_universe.metadata.action_count
    assert checkpoint["meter_count"] == compiled_universe.metadata.meter_count
    assert checkpoint["observation_field_uuids"] == [field.uuid for field in compiled_universe.observation_spec.fields]
    assert checkpoint["observation_schema_hash"] == compiled_universe.observation_schema_hash
    assert checkpoint["vfs_hash"] == compiled_universe.vfs_hash


def test_config_hash_warning_detects_mismatch(compiled_universe) -> None:
    attach = {}
    attach_universe_metadata(attach, compiled_universe)
    warn = config_hash_warning(attach, compiled_universe)
    assert warn is None

    attach["config_hash"] = "deadbeef"
    warn = config_hash_warning(attach, compiled_universe)
    assert warn is not None
    assert "Checkpoint" in warn


def test_assert_checkpoint_dimensions_raises_on_mismatch(compiled_universe) -> None:
    checkpoint: dict[str, object] = {}
    attach_universe_metadata(checkpoint, compiled_universe)

    assert_checkpoint_dimensions(checkpoint, compiled_universe)

    checkpoint["observation_dim"] = -1
    with pytest.raises(ValueError):
        assert_checkpoint_dimensions(checkpoint, compiled_universe)

    checkpoint = {}
    attach_universe_metadata(checkpoint, compiled_universe)
    checkpoint["observation_field_uuids"][0] = "deadbeefdeadbeef"
    with pytest.raises(ValueError):
        assert_checkpoint_dimensions(checkpoint, compiled_universe)


def test_assert_checkpoint_dimensions_validates_drive_hash(compiled_universe) -> None:
    """CRIT-06: assert_checkpoint_dimensions should validate drive_hash."""
    checkpoint: dict[str, object] = {}
    attach_universe_metadata(checkpoint, compiled_universe)

    # Valid checkpoint should pass
    assert_checkpoint_dimensions(checkpoint, compiled_universe)

    # Missing drive_hash should raise
    checkpoint_no_hash = {}
    attach_universe_metadata(checkpoint_no_hash, compiled_universe)
    del checkpoint_no_hash["drive_hash"]
    with pytest.raises(ValueError, match="missing drive_hash"):
        assert_checkpoint_dimensions(checkpoint_no_hash, compiled_universe)

    # Mismatched drive_hash should raise
    checkpoint_bad_hash = {}
    attach_universe_metadata(checkpoint_bad_hash, compiled_universe)
    checkpoint_bad_hash["drive_hash"] = "deadbeefdeadbeefdeadbeefdeadbeef"
    with pytest.raises(ValueError, match="drive_hash mismatch"):
        assert_checkpoint_dimensions(checkpoint_bad_hash, compiled_universe)


def test_attach_universe_metadata_includes_drive_hash(compiled_universe) -> None:
    """attach_universe_metadata should include drive_hash."""
    checkpoint: dict[str, object] = {}
    attach_universe_metadata(checkpoint, compiled_universe)

    assert "drive_hash" in checkpoint
    assert checkpoint["drive_hash"] == compiled_universe.drive_hash
    assert len(checkpoint["drive_hash"]) == 64  # SHA256 hex string


def test_assert_checkpoint_vfs_hash_rejects_missing_and_mismatch(compiled_universe) -> None:
    """Checkpoint resume should be blocked by VFS ABI mismatch before state load."""
    checkpoint: dict[str, object] = {}
    attach_universe_metadata(checkpoint, compiled_universe)

    assert assert_checkpoint_vfs_hash(checkpoint, compiled_universe, force_new_vfs=False) is True

    missing = dict(checkpoint)
    del missing["vfs_hash"]
    with pytest.raises(ValueError, match="missing vfs_hash"):
        assert_checkpoint_vfs_hash(missing, compiled_universe, force_new_vfs=False)

    mismatched = dict(checkpoint)
    mismatched["vfs_hash"] = "deadbeef" * 8
    with pytest.raises(ValueError, match="--force-new-vfs"):
        assert_checkpoint_vfs_hash(mismatched, compiled_universe, force_new_vfs=False)

    assert assert_checkpoint_vfs_hash(mismatched, compiled_universe, force_new_vfs=True) is False


def test_safe_torch_load_rejects_custom_objects(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "legacy.pt"
    legacy_checkpoint = PopulationCheckpoint(
        generation=0,
        num_agents=1,
        agent_ids=["agent_0"],
        curriculum_states={},
        exploration_states={},
        pareto_frontier=[],
        metrics_summary={},
    )
    torch.save(legacy_checkpoint, checkpoint_path)

    with pytest.raises(Exception) as excinfo:
        safe_torch_load(checkpoint_path)
    assert "weights only load failed" in str(excinfo.value).lower()


def test_safe_torch_load_roundtrip(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "safe.pt"
    payload = {"weights": torch.ones(2), "metadata": {"episode": 5}}
    torch.save(payload, checkpoint_path)

    loaded = safe_torch_load(checkpoint_path)
    assert torch.equal(loaded["weights"], payload["weights"])
    assert loaded["metadata"]["episode"] == 5


def test_checkpoint_digest_roundtrip(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint_ep00010.pt"
    checkpoint_path.write_bytes(b"demo-checkpoint")

    digest = persist_checkpoint_digest(checkpoint_path)
    assert len(digest) == 64  # hex sha256
    assert verify_checkpoint_digest(checkpoint_path, required=True)


def test_checkpoint_digest_detects_tampering(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint_ep00011.pt"
    checkpoint_path.write_bytes(b"demo-checkpoint")
    persist_checkpoint_digest(checkpoint_path)

    checkpoint_path.write_bytes(b"demo-checkpoint-corrupted")
    with pytest.raises(ValueError):
        verify_checkpoint_digest(checkpoint_path, required=True)
