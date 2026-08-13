"""Subprocess self-comparison: working tree vs working tree must AGREE (WS-7).

Exercises the real driver-subprocess plumbing (PYTHONPATH injection, -P flag,
trace round-trip through files, compare) WITHOUT needing the oracle worktree —
both sides are the working tree, so CI never depends on a tag being present.
A full old-vs-new run is a CLI operation, not a suite test (by design)."""

from __future__ import annotations

from pathlib import Path

import pytest

from townlet.oracle.harness import run_cell
from townlet.oracle.matrix import Cell
from townlet.oracle.trace_io import RunParams

pytestmark = pytest.mark.slow

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_self_comparison_agrees(tmp_path: Path) -> None:
    cell = Cell(
        RunParams(
            pack="configs/default_curriculum",
            level="L0_0_minimal",
            num_agents=4,
            steps=10,
            seed=42,
            device="cpu",
        )
    )
    verdict = run_cell(
        repo_root=REPO_ROOT,
        old_src=REPO_ROOT / "src",
        new_src=REPO_ROOT / "src",
        cell=cell,
        run_dir=tmp_path,
        run_cuda=False,
    )
    assert verdict.kind == "AGREE", verdict.detail


def test_driver_failure_is_a_loud_side_error(tmp_path: Path) -> None:
    cell = Cell(
        RunParams(
            pack="configs/default_curriculum",
            level="NO_SUCH_LEVEL",
            num_agents=4,
            steps=2,
            seed=42,
            device="cpu",
        )
    )
    verdict = run_cell(
        repo_root=REPO_ROOT,
        old_src=REPO_ROOT / "src",
        new_src=REPO_ROOT / "src",
        cell=cell,
        run_dir=tmp_path,
        run_cuda=False,
    )
    assert verdict.kind == "OLD_SIDE_ERROR"  # old side runs first, fails first
    assert verdict.detail["side"] == "old"
    assert "NO_SUCH_LEVEL" in str(verdict.detail["stderr"])
