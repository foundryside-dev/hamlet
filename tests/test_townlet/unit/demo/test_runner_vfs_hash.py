"""Tests for VFS hash handling in demo checkpoint resume."""

from pathlib import Path

import pytest
import torch

from townlet.demo.runner import DemoRunner
from townlet.training.checkpoint_utils import (
    CHECKPOINT_FORMAT_VERSION,
    DEMO_CHECKPOINT_KEYS,
    attach_universe_metadata,
    persist_checkpoint_digest,
)
from townlet.universe.compiled import CompiledUniverse


def _write_mismatched_checkpoint(
    checkpoint_dir: Path,
    universe: CompiledUniverse,
    *,
    write_digest: bool = True,
) -> Path:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / "checkpoint_ep00012.pt"
    checkpoint = {key: None for key in DEMO_CHECKPOINT_KEYS}
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
            "config_dir": "configs/test/model_config",
        }
    )
    attach_universe_metadata(checkpoint, universe)
    checkpoint["vfs_hash"] = "deadbeef" * 8
    torch.save(checkpoint, checkpoint_path)
    if write_digest:
        persist_checkpoint_digest(checkpoint_path)
    return checkpoint_path


def _initialize_checkpoint_components(runner: DemoRunner) -> None:
    # These tests stop at the VFS/digest gate, before any component API is used.
    runner.env = object()  # type: ignore[assignment]
    runner.population = object()  # type: ignore[assignment]
    runner.curriculum = object()  # type: ignore[assignment]


def test_runner_rejects_checkpoint_vfs_hash_mismatch(tmp_path: Path) -> None:
    """Resuming across a VFS ABI change should fail loudly."""
    checkpoint_dir = tmp_path / "checkpoints"
    runner = DemoRunner(
        config_dir=Path("configs/test/model_config"),
        db_path=tmp_path / "test.db",
        checkpoint_dir=checkpoint_dir,
        max_episodes=1,
        level_name="L0_test",
    )
    _initialize_checkpoint_components(runner)
    _write_mismatched_checkpoint(checkpoint_dir, runner.compiled)

    try:
        try:
            runner.load_checkpoint()
        except ValueError as exc:
            assert "vfs_hash mismatch" in str(exc)
            assert "--force-new-vfs" in str(exc)
        else:
            raise AssertionError("Expected VFS hash mismatch to reject checkpoint resume")
    finally:
        runner._cleanup()


def test_runner_force_new_vfs_branches_without_loading_checkpoint(tmp_path: Path) -> None:
    """The explicit override should start fresh instead of loading incompatible state."""
    checkpoint_dir = tmp_path / "checkpoints"
    runner = DemoRunner(
        config_dir=Path("configs/test/model_config"),
        db_path=tmp_path / "test.db",
        checkpoint_dir=checkpoint_dir,
        max_episodes=1,
        level_name="L0_test",
        force_new_vfs=True,
    )
    _initialize_checkpoint_components(runner)
    _write_mismatched_checkpoint(checkpoint_dir, runner.compiled)

    try:
        assert runner.load_checkpoint() is None
        assert runner.current_episode == 0
    finally:
        runner._cleanup()


def test_both_checkpoint_consumers_call_the_shared_identity_guard() -> None:
    """WS-1 task 5: `assert_checkpoint_identity` is the single insertion point.

    The claim "a check added there is enforced on both paths" is only true while
    both consumers actually route through it and neither keeps a hand-rolled copy
    of the chain. Source-level pin so a drive-by 'optimization' on either path
    fails here by name.
    """
    import inspect

    from townlet.demo import live_inference

    runner_src = inspect.getsource(DemoRunner.load_checkpoint)
    serving_src = inspect.getsource(live_inference.LiveInferenceServer._check_and_load_checkpoint)

    assert "assert_checkpoint_identity(" in runner_src, "DemoRunner.load_checkpoint no longer routes through the shared identity guard"
    assert "assert_checkpoint_identity(" in serving_src, "the serving path no longer routes through the shared identity guard"

    # No second hand-rolled copy of the chain on either path — the piecemeal
    # checks must be called only inside assert_checkpoint_identity itself.
    for name, source in (("DemoRunner.load_checkpoint", runner_src), ("LiveInferenceServer._check_and_load_checkpoint", serving_src)):
        for piecemeal in ("assert_checkpoint_vfs_hash(", "assert_checkpoint_dimensions(", "config_hash_warning("):
            assert piecemeal not in source, f"{name} hand-rolls {piecemeal}...) instead of the shared guard"

    # H8: the named regression shape. `if self.compiled_universe is not None:` around the
    # guard is the silent skip this unit exists to delete — None must RAISE, not skip.
    assert "if self.compiled_universe is not None" not in serving_src, "the serving path reintroduced the silent skip (plan §3 H8)"


def test_runner_requires_checkpoint_digest_before_pickle_load(tmp_path: Path) -> None:
    """Demo checkpoint resume must verify a sidecar digest before unsafe pickle loading."""
    checkpoint_dir = tmp_path / "checkpoints"
    runner = DemoRunner(
        config_dir=Path("configs/test/model_config"),
        db_path=tmp_path / "test.db",
        checkpoint_dir=checkpoint_dir,
        max_episodes=1,
        level_name="L0_test",
    )
    _initialize_checkpoint_components(runner)
    _write_mismatched_checkpoint(checkpoint_dir, runner.compiled, write_digest=False)

    try:
        with pytest.raises(FileNotFoundError, match="Missing checksum file"):
            runner.load_checkpoint()
    finally:
        runner._cleanup()
