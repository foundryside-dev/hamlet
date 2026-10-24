"""Tests for checkpoint metadata helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.training.checkpoint_utils import (
    CHECKPOINT_FORMAT_VERSION,
    DEMO_CHECKPOINT_KEYS,
    PACK_HASH_KEYS,
    assert_checkpoint_dimensions,
    assert_checkpoint_identity,
    assert_checkpoint_pack_hashes,
    assert_checkpoint_vfs_hash,
    attach_universe_metadata,
    persist_checkpoint_digest,
    safe_torch_load,
    validate_demo_checkpoint_payload,
    validate_demo_checkpoint_runtime_fields,
    verify_checkpoint_digest,
)
from townlet.training.state import PopulationCheckpoint
from townlet.universe.compiler import UniverseCompiler


@pytest.fixture(scope="module")
def compiled_universe():
    compiler = UniverseCompiler()
    return compiler.compile(Path("configs/test/model_config"), primary_level="L0_test")


def test_demo_checkpoint_payload_requires_exact_current_key_set() -> None:
    payload = {key: None for key in DEMO_CHECKPOINT_KEYS}
    payload["version"] = CHECKPOINT_FORMAT_VERSION
    validate_demo_checkpoint_payload(payload)

    missing = dict(payload)
    missing.pop("population_state")
    with pytest.raises(ValueError, match=r"missing=\['population_state'\], unknown=\[\]"):
        validate_demo_checkpoint_payload(missing)

    unknown = dict(payload)
    unknown["legacy_epsilon"] = 0.5
    with pytest.raises(ValueError, match=r"missing=\[\], unknown=\['legacy_epsilon'\]"):
        validate_demo_checkpoint_payload(unknown)


def test_demo_checkpoint_runtime_fields_require_exact_bound_values() -> None:
    payload = {key: None for key in DEMO_CHECKPOINT_KEYS}
    payload["substrate_metadata"] = {"position_dim": 2, "substrate_type": "Grid2DSubstrate"}
    payload["agent_ids"] = ["agent_0"]
    payload["epsilon"] = 0.25
    payload["completed_live_agent_steps"] = 123

    validate_demo_checkpoint_runtime_fields(
        payload,
        position_dim=2,
        substrate_type="Grid2DSubstrate",
        num_agents=1,
    )

    nonfinite = dict(payload)
    nonfinite["epsilon"] = float("nan")
    with pytest.raises(ValueError, match="epsilon must be a finite number"):
        validate_demo_checkpoint_runtime_fields(
            nonfinite,
            position_dim=2,
            substrate_type="Grid2DSubstrate",
            num_agents=1,
        )

    wrong_substrate = dict(payload)
    wrong_substrate["substrate_metadata"] = {"position_dim": 3, "substrate_type": "Grid2DSubstrate"}
    with pytest.raises(ValueError, match="position_dim mismatch"):
        validate_demo_checkpoint_runtime_fields(
            wrong_substrate,
            position_dim=2,
            substrate_type="Grid2DSubstrate",
            num_agents=1,
        )

    wrong_agents = dict(payload)
    wrong_agents["agent_ids"] = ["agent_0", "agent_1"]
    with pytest.raises(ValueError, match="agent_ids length mismatch"):
        validate_demo_checkpoint_runtime_fields(
            wrong_agents,
            position_dim=2,
            substrate_type="Grid2DSubstrate",
            num_agents=1,
        )

    invalid_steps = dict(payload)
    invalid_steps["completed_live_agent_steps"] = -1
    with pytest.raises(ValueError, match="completed_live_agent_steps must be a non-negative integer"):
        validate_demo_checkpoint_runtime_fields(
            invalid_steps,
            position_dim=2,
            substrate_type="Grid2DSubstrate",
            num_agents=1,
        )


def test_attach_universe_metadata(compiled_universe) -> None:
    checkpoint: dict[str, object] = {}
    attach_universe_metadata(checkpoint, compiled_universe)
    level = compiled_universe.get_level(compiled_universe.metadata.primary_level)

    # The cache fingerprint is not identity: a comment edit or file rename moves it while
    # every semantic hash stays put, so it is not stamped at all (hamlet-2dde1015fe).
    assert "config_hash" not in checkpoint
    assert checkpoint["action_dim"] == level.action_metadata.total_actions
    assert checkpoint["meter_count"] == len(level.meter_metadata.meters)
    assert checkpoint["observation_schema_hash"] == level.observation_schema_hash
    assert checkpoint["vfs_hash"] == level.vfs_hash
    # The observation identity is the two TokenSpec hashes since the unit-3 cut;
    # `observation_dim` and `observation_field_uuids` died with the ObservationSpec.
    assert checkpoint["token_type_schema_hash"] == level.token_type_schema_hash
    assert checkpoint["layout_hash"] == level.layout_hash
    assert "observation_dim" not in checkpoint
    assert "observation_field_uuids" not in checkpoint
    # The five pack-scope content hashes (hamlet-2dde1015fe). `items_hash` is a stamped
    # None on a pack with no item arena — a value, not an absence.
    for key in PACK_HASH_KEYS:
        assert key in checkpoint
        assert checkpoint[key] == getattr(compiled_universe, key)
    assert compiled_universe.items_hash is None, "model_config grew an item arena; re-derive this pin"
    assert checkpoint["items_hash"] is None


def test_assert_checkpoint_identity_composes_all_legs(compiled_universe) -> None:
    """WS-1 task 5: the single identity gate both checkpoint consumers route through.

    `config_hash_warning` is deliberately gone (PDR-0022): a warning is the silent
    acceptance the Provenance-integrity guardrail forbids. The composed chain is
    format version → vfs_hash → dimensions/content hashes → pack hashes → primary_level.
    """
    checkpoint: dict[str, object] = {"version": CHECKPOINT_FORMAT_VERSION}
    attach_universe_metadata(checkpoint, compiled_universe)

    # Honest A/A resumes.
    assert assert_checkpoint_identity(checkpoint, compiled_universe, force_new_vfs=False) is True

    # Leg 1 — format version, checked FIRST: a wrong-format checkpoint may lack
    # vfs_hash entirely, so nothing downstream can be trusted to even be present.
    with pytest.raises(ValueError, match="Unsupported checkpoint version"):
        assert_checkpoint_identity({"version": 2}, compiled_universe, force_new_vfs=False)

    # Leg 2 — VFS ABI. force_new_vfs=True is the ONLY False-returning branch.
    mismatched_vfs = dict(checkpoint)
    mismatched_vfs["vfs_hash"] = "deadbeef" * 8
    with pytest.raises(ValueError, match="vfs_hash mismatch"):
        assert_checkpoint_identity(mismatched_vfs, compiled_universe, force_new_vfs=False)
    assert assert_checkpoint_identity(mismatched_vfs, compiled_universe, force_new_vfs=True) is False

    # Leg 3 — dimensions + content hashes are enforced through the composed gate.
    mismatched_drive = dict(checkpoint)
    mismatched_drive["drive_hash"] = "deadbeef" * 8
    with pytest.raises(ValueError, match="drive_hash mismatch"):
        assert_checkpoint_identity(mismatched_drive, compiled_universe, force_new_vfs=False)

    # Leg 4 — the five pack-scope hashes, each a hard refusal through the composed gate.
    for key in PACK_HASH_KEYS:
        mismatched_pack = dict(checkpoint)
        mismatched_pack[key] = "deadbeef" * 8
        with pytest.raises(ValueError, match=f"{key} mismatch"):
            assert_checkpoint_identity(mismatched_pack, compiled_universe, force_new_vfs=False)
        missing_pack = dict(checkpoint)
        del missing_pack[key]
        with pytest.raises(ValueError, match=f"missing {key}"):
            assert_checkpoint_identity(missing_pack, compiled_universe, force_new_vfs=False)

    # Leg 5 — D5: primary_level. Missing raises (no-hidden-defaults); mismatch raises.
    missing_level = dict(checkpoint)
    del missing_level["primary_level"]
    with pytest.raises(ValueError, match="missing primary_level"):
        assert_checkpoint_identity(missing_level, compiled_universe, force_new_vfs=False)

    wrong_level = dict(checkpoint)
    wrong_level["primary_level"] = "L9_not_this_level"
    with pytest.raises(ValueError, match="primary_level mismatch"):
        assert_checkpoint_identity(wrong_level, compiled_universe, force_new_vfs=False)


def test_items_hash_none_versus_value_is_a_change(compiled_universe) -> None:
    """`items_hash` is nullable: `None` is the stamped value of a pack with no item arena.

    A catalog appearing (checkpoint None, universe digest) or vanishing (checkpoint digest,
    universe None) is a changed world and refuses like any other mismatch; `None == None`
    resumes. The checkpoint-digest-versus-universe-None direction uses the real
    `items_smoke` pack so the universe side is a compiled artifact, not a stub.
    """
    assert compiled_universe.items_hash is None, "model_config grew an item arena; re-derive this pin"
    checkpoint: dict[str, object] = {"version": CHECKPOINT_FORMAT_VERSION}
    attach_universe_metadata(checkpoint, compiled_universe)
    assert assert_checkpoint_identity(checkpoint, compiled_universe, force_new_vfs=False) is True

    catalog_vanished = dict(checkpoint)
    catalog_vanished["items_hash"] = "deadbeef" * 8
    with pytest.raises(ValueError, match="items_hash mismatch: checkpoint=deadbeefdeadbeef..., current=None"):
        assert_checkpoint_identity(catalog_vanished, compiled_universe, force_new_vfs=False)

    with_items = UniverseCompiler().compile(Path("configs/test/items_smoke"), primary_level="L0_smoke", use_cache=False)
    assert with_items.items_hash is not None
    stamped_with_items: dict[str, object] = {"version": CHECKPOINT_FORMAT_VERSION}
    attach_universe_metadata(stamped_with_items, with_items)
    assert stamped_with_items["items_hash"] == with_items.items_hash
    catalog_appeared = dict(stamped_with_items)
    catalog_appeared["items_hash"] = None
    with pytest.raises(ValueError, match="items_hash mismatch: checkpoint=None, current="):
        assert_checkpoint_pack_hashes(catalog_appeared, with_items)


def test_assert_checkpoint_dimensions_raises_on_mismatch(compiled_universe) -> None:
    checkpoint: dict[str, object] = {}
    attach_universe_metadata(checkpoint, compiled_universe)

    assert_checkpoint_dimensions(checkpoint, compiled_universe)

    checkpoint["action_dim"] = -1
    with pytest.raises(ValueError, match="action_dim mismatch"):
        assert_checkpoint_dimensions(checkpoint, compiled_universe)

    # The observation leg for a flat reader is the LAYOUT hash.
    checkpoint = {}
    attach_universe_metadata(checkpoint, compiled_universe)
    checkpoint["layout_hash"] = "deadbeef" * 8
    with pytest.raises(ValueError, match="layout_hash mismatch"):
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
    level = compiled_universe.get_level(compiled_universe.metadata.primary_level)

    assert "drive_hash" in checkpoint
    assert checkpoint["drive_hash"] == level.drive_hash
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


def test_safe_torch_load_rejects_custom_objects_by_default(tmp_path: Path) -> None:
    """The default safe path must refuse to unpickle a checkpoint that carries
    custom Python objects. Demo / inference paths only get past this gate by
    passing allow_unsafe_pickle=True explicitly."""
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

    with pytest.raises(RuntimeError) as excinfo:
        safe_torch_load(checkpoint_path)
    assert "weights-only load failed" in str(excinfo.value).lower()
    assert "allow_unsafe_pickle=True" in str(excinfo.value)


def test_safe_torch_load_unsafe_opt_in_loads_custom_objects(tmp_path: Path, caplog) -> None:
    """When the caller explicitly opts in, the unsafe pickle path loads and
    emits a loud WARN."""
    checkpoint_path = tmp_path / "legacy.pt"
    legacy_checkpoint = PopulationCheckpoint(
        generation=1,
        num_agents=1,
        agent_ids=["agent_0"],
        curriculum_states={},
        exploration_states={},
        pareto_frontier=[],
        metrics_summary={},
    )
    torch.save(legacy_checkpoint, checkpoint_path)

    with caplog.at_level("WARNING", logger="townlet.training.checkpoint_utils"):
        loaded = safe_torch_load(checkpoint_path, allow_unsafe_pickle=True)
    assert isinstance(loaded, PopulationCheckpoint)
    assert loaded.generation == 1
    assert any("allow_unsafe_pickle=True" in record.message for record in caplog.records)


def test_safe_torch_load_roundtrip(tmp_path: Path) -> None:
    """The safe default path round-trips a plain weights payload."""
    checkpoint_path = tmp_path / "safe.pt"
    payload = {"weights": torch.ones(2), "metadata": {"episode": 5}}
    torch.save(payload, checkpoint_path)

    loaded = safe_torch_load(checkpoint_path)
    assert torch.equal(loaded["weights"], payload["weights"])
    assert loaded["metadata"]["episode"] == 5


def test_verify_checkpoint_digest_required_by_default(tmp_path: Path) -> None:
    """Default behavior must reject a checkpoint that has no sidecar digest."""
    checkpoint_path = tmp_path / "no_digest.pt"
    checkpoint_path.write_bytes(b"demo-checkpoint")
    with pytest.raises(FileNotFoundError):
        verify_checkpoint_digest(checkpoint_path)


def test_verify_checkpoint_digest_explicit_optional(tmp_path: Path) -> None:
    """required=False is the explicit local-dev escape and must return False
    when the digest is missing rather than raising."""
    checkpoint_path = tmp_path / "no_digest.pt"
    checkpoint_path.write_bytes(b"demo-checkpoint")
    assert verify_checkpoint_digest(checkpoint_path, required=False) is False


def test_checkpoint_digest_roundtrip(tmp_path: Path) -> None:
    """A persisted digest is accepted on default verification."""
    checkpoint_path = tmp_path / "checkpoint_ep00010.pt"
    checkpoint_path.write_bytes(b"demo-checkpoint")

    digest = persist_checkpoint_digest(checkpoint_path)
    assert len(digest) == 64  # hex sha256
    assert verify_checkpoint_digest(checkpoint_path)


def test_checkpoint_digest_detects_tampering(tmp_path: Path) -> None:
    """A digest mismatch raises whether or not the digest is 'required' (the
    digest file exists; what's wrong is its contents)."""
    checkpoint_path = tmp_path / "checkpoint_ep00011.pt"
    checkpoint_path.write_bytes(b"demo-checkpoint")
    persist_checkpoint_digest(checkpoint_path)

    checkpoint_path.write_bytes(b"demo-checkpoint-corrupted")
    with pytest.raises(ValueError):
        verify_checkpoint_digest(checkpoint_path)
