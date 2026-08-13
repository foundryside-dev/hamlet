"""Harness verdict aggregation and report writing — no subprocesses here (WS-7)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from townlet.oracle.harness import _git, ensure_worktree, exit_code, run_cell, write_report
from townlet.oracle.matrix import Cell
from townlet.oracle.trace_io import CellVerdict, RunParams


def _v(kind: str, cell: str = "c") -> CellVerdict:
    return CellVerdict(kind=kind, cell_id=cell, detail={})


def test_exit_zero_only_for_agree_and_skipped() -> None:
    assert exit_code([_v("AGREE"), _v("SKIPPED")]) == 0
    assert exit_code([_v("AGREE"), _v("DIVERGE")]) == 1
    assert exit_code([_v("HASH_MISMATCH")]) == 1
    assert exit_code([_v("OLD_SIDE_ERROR")]) == 1
    assert exit_code([_v("NEW_SIDE_ERROR")]) == 1
    assert exit_code([]) == 1  # an empty run proves nothing; refuse to look green


def test_report_carries_verdicts_meta_and_register_pointer(tmp_path: Path) -> None:
    verdicts = [_v("AGREE", "cell-a"), _v("DIVERGE", "cell-b")]
    meta = {"oracle_ref": "oracle-2026-08-13", "new_commit": "abc"}
    path = write_report(tmp_path, verdicts, meta)
    report = json.loads(path.read_text())
    assert report["meta"]["oracle_ref"] == "oracle-2026-08-13"
    assert [v["cell_id"] for v in report["verdicts"]] == ["cell-a", "cell-b"]
    assert report["verdicts"][1]["register_refs"] == []
    assert "known-divergences" in report["adjudication_note"]


def test_cuda_cell_without_flag_is_skipped_without_subprocess(tmp_path: Path) -> None:
    """A CUDA cell is always in the declared matrix; without --cuda it must
    report SKIPPED('cuda not requested') and never spawn a driver subprocess.
    repo_root/old_src/new_src point at nonexistent paths — if run_cell tried
    to shell out, it would fail loudly rather than return SKIPPED."""
    cell = Cell(
        RunParams(
            pack="configs/default_curriculum",
            level="L0_0_minimal",
            num_agents=4,
            steps=1,
            seed=42,
            device="cuda",
        )
    )
    bogus = Path("/nonexistent/does-not-exist")
    verdict = run_cell(
        repo_root=bogus,
        old_src=bogus,
        new_src=bogus,
        cell=cell,
        run_dir=tmp_path,
        run_cuda=False,
    )
    assert verdict.kind == "SKIPPED"
    assert verdict.detail["reason"] == "cuda not requested"


# --- ensure_worktree: git plumbing only, no townlet driver spawned ---------
#
# These build a throwaway git repo under tmp_path (init, commit, tag) rather
# than touching the real repo or its real .oracle/ worktree, so they stay
# fast, hermetic unit tests.


def _make_scratch_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "scratch_repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "src" / "townlet").mkdir(parents=True)
    (repo / "src" / "townlet" / "__init__.py").write_text("")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    tag = "oracle-test-tag"
    subprocess.run(["git", "tag", tag], cwd=repo, check=True)
    return repo, tag


def test_ensure_worktree_fresh_create(tmp_path: Path) -> None:
    repo, tag = _make_scratch_repo(tmp_path)
    path = ensure_worktree(repo, tag)
    assert path == repo / ".oracle" / tag
    assert (path / "src" / "townlet").is_dir()


def test_ensure_worktree_clean_reuse_passes(tmp_path: Path) -> None:
    repo, tag = _make_scratch_repo(tmp_path)
    first = ensure_worktree(repo, tag)
    second = ensure_worktree(repo, tag)  # reuse path: verify, don't recreate
    assert first == second == repo / ".oracle" / tag


def test_ensure_worktree_dirty_worktree_aborts(tmp_path: Path) -> None:
    repo, tag = _make_scratch_repo(tmp_path)
    worktree = ensure_worktree(repo, tag)
    (worktree / "src" / "townlet" / "uncommitted.py").write_text("# local edit\n")
    with pytest.raises(SystemExit, match="local changes"):
        ensure_worktree(repo, tag)


def test_ensure_worktree_wrong_head_aborts(tmp_path: Path) -> None:
    repo, tag = _make_scratch_repo(tmp_path)
    # A second commit that the tag does NOT point at.
    (repo / "src" / "townlet" / "extra.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "second"], cwd=repo, check=True)
    second_sha = _git(repo, "rev-parse", "HEAD")

    worktree = ensure_worktree(repo, tag)  # creates the worktree at the tag commit
    subprocess.run(["git", "checkout", "-q", second_sha], cwd=worktree, check=True)

    with pytest.raises(SystemExit, match="is at commit"):
        ensure_worktree(repo, tag)
