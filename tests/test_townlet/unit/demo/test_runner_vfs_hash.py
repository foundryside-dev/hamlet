"""Tests for VFS hash handling in demo checkpoint resume."""

from pathlib import Path

import torch

from townlet.demo.runner import DemoRunner


def _write_mismatched_checkpoint(checkpoint_dir: Path) -> None:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "version": 3,
            "episode": 12,
            "timestamp": 1.0,
            "substrate_metadata": {"position_dim": 2, "substrate_type": "Grid2DSubstrate"},
            "vfs_hash": "deadbeef" * 8,
        },
        checkpoint_dir / "checkpoint_ep00012.pt",
    )


def test_runner_rejects_checkpoint_vfs_hash_mismatch(tmp_path: Path) -> None:
    """Resuming across a VFS ABI change should fail loudly."""
    checkpoint_dir = tmp_path / "checkpoints"
    _write_mismatched_checkpoint(checkpoint_dir)

    runner = DemoRunner(
        config_dir=Path("configs/test/model_config"),
        db_path=tmp_path / "test.db",
        checkpoint_dir=checkpoint_dir,
        max_episodes=1,
        level_name="L0_test",
    )

    try:
        try:
            runner.load_checkpoint(runner.compiled)
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
    _write_mismatched_checkpoint(checkpoint_dir)

    runner = DemoRunner(
        config_dir=Path("configs/test/model_config"),
        db_path=tmp_path / "test.db",
        checkpoint_dir=checkpoint_dir,
        max_episodes=1,
        level_name="L0_test",
        force_new_vfs=True,
    )

    try:
        assert runner.load_checkpoint(runner.compiled) is None
        assert runner.current_episode == 0
    finally:
        runner._cleanup()
