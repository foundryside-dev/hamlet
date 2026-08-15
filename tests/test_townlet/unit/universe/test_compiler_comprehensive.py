"""Lean compiler helper tests (duplicates removed)."""

from __future__ import annotations

from pathlib import Path

from townlet.universe.compiler import UniverseCompiler


def test_cache_artifact_path_returns_expected_location(tmp_path: Path) -> None:
    """Cache artifacts live under .compiled/universe-<level>.msgpack (one per level)."""
    compiler = UniverseCompiler()
    config_dir = tmp_path / "pack"
    config_dir.mkdir()

    artifact_path = compiler._cache_artifact_path(config_dir, "L0_test")

    assert artifact_path == config_dir / ".compiled" / "universe-L0_test.msgpack"


def test_build_cache_fingerprint_returns_tuple(tmp_path: Path) -> None:
    """Cache fingerprint should be tuple(config_hash, compiler_version)."""
    compiler = UniverseCompiler()
    config_dir = tmp_path / "pack"
    config_dir.mkdir()

    fingerprint = compiler._build_cache_fingerprint(config_dir)

    assert isinstance(fingerprint, tuple)
    assert len(fingerprint) == 2


def test_build_cache_fingerprint_stable_for_same_config(tmp_path: Path) -> None:
    """Fingerprint should be stable for unchanged configs."""
    compiler = UniverseCompiler()
    config_dir = tmp_path / "pack"
    config_dir.mkdir()

    fp1 = compiler._build_cache_fingerprint(config_dir)
    fp2 = compiler._build_cache_fingerprint(config_dir)

    assert fp1 == fp2
