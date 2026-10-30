"""VFS WP10 (round-2 F5): `variables_hash` is the sixth pack hash, stamped and hard-compared.

The plumbing is generic — `attach_universe_metadata` stamps and `assert_checkpoint_pack_hashes`
compares every key in `PACK_HASH_KEYS` — so these tests pin the membership and walk the two real
consumers' paths: the shared identity gate and `DemoRunner.load_checkpoint`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.demo.runner import DemoRunner
from townlet.training.checkpoint_utils import (
    CHECKPOINT_FORMAT_VERSION,
    DEMO_CHECKPOINT_KEYS,
    PACK_HASH_KEYS,
    assert_checkpoint_identity,
    attach_universe_metadata,
    persist_checkpoint_digest,
)
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

MODEL_CONFIG = Path("configs/test/model_config")


@pytest.fixture(scope="module")
def compiled_universe() -> CompiledUniverse:
    return UniverseCompiler().compile(MODEL_CONFIG, primary_level="L0_test", use_cache=False)


def test_variables_hash_is_a_pack_hash_and_a_checkpoint_key() -> None:
    assert "variables_hash" in PACK_HASH_KEYS
    assert "variables_hash" in DEMO_CHECKPOINT_KEYS
    assert len(PACK_HASH_KEYS) == 6


def test_variables_hash_is_stamped_and_hard_compared(compiled_universe: CompiledUniverse) -> None:
    checkpoint: dict[str, object] = {"version": CHECKPOINT_FORMAT_VERSION}
    attach_universe_metadata(checkpoint, compiled_universe)
    assert checkpoint["variables_hash"] == compiled_universe.variables_hash
    assert isinstance(compiled_universe.variables_hash, str) and len(compiled_universe.variables_hash) == 64
    assert assert_checkpoint_identity(checkpoint, compiled_universe, force_new_vfs=False) is True

    mismatched = dict(checkpoint)
    mismatched["variables_hash"] = "deadbeef" * 8
    with pytest.raises(ValueError, match="variables_hash mismatch"):
        assert_checkpoint_identity(mismatched, compiled_universe, force_new_vfs=False)
    # No --force-new-vfs escape: a pack hash is a hard refusal, like the other five.
    with pytest.raises(ValueError, match="variables_hash mismatch"):
        assert_checkpoint_identity(mismatched, compiled_universe, force_new_vfs=True)

    missing = dict(checkpoint)
    del missing["variables_hash"]
    with pytest.raises(ValueError, match="missing variables_hash"):
        assert_checkpoint_identity(missing, compiled_universe, force_new_vfs=False)


def test_variables_hash_survives_the_artifact_round_trip(compiled_universe: CompiledUniverse) -> None:
    restored = CompiledUniverse.from_dict(compiled_universe.to_dict())
    assert restored.variables_hash == compiled_universe.variables_hash

    payload = compiled_universe.to_dict()
    del payload["variables_hash"]
    with pytest.raises(ValueError, match="variables_hash"):
        CompiledUniverse.from_dict(payload)


def test_runner_refuses_resume_on_variables_hash_mismatch(tmp_path: Path) -> None:
    checkpoint_dir = tmp_path / "checkpoints"
    runner = DemoRunner(
        config_dir=MODEL_CONFIG,
        db_path=tmp_path / "test.db",
        checkpoint_dir=checkpoint_dir,
        max_episodes=1,
        level_name="L0_test",
    )
    # The gate runs before any component API is used.
    runner.env = object()  # type: ignore[assignment]
    runner.population = object()  # type: ignore[assignment]
    runner.curriculum = object()  # type: ignore[assignment]

    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / "checkpoint_ep00012.pt"
    checkpoint: dict[str, object] = {key: None for key in DEMO_CHECKPOINT_KEYS}
    checkpoint.update(
        {
            "version": CHECKPOINT_FORMAT_VERSION,
            "episode": 12,
            "timestamp": 1.0,
            "substrate_metadata": {"position_dim": 2, "substrate_type": "Grid2DSubstrate"},
            "population_state": {},
            "curriculum_state": {},
            "affordance_layout": {},
            "agent_ids": ["agent_0"],
            "epsilon": 0.25,
            "training_config": {},
            "config_dir": str(MODEL_CONFIG),
        }
    )
    attach_universe_metadata(checkpoint, runner.compiled)
    checkpoint["variables_hash"] = "deadbeef" * 8
    torch.save(checkpoint, checkpoint_path)
    persist_checkpoint_digest(checkpoint_path)

    try:
        with pytest.raises(ValueError, match="variables_hash mismatch"):
            runner.load_checkpoint()
    finally:
        runner._cleanup()
