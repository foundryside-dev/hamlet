"""Harness verdict aggregation and report writing — no subprocesses here (WS-7)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from townlet.oracle.harness import _collect_run_meta, _git, ensure_worktree, exit_code, run_cell, run_cell_safely, run_side, write_report
from townlet.oracle.matrix import Cell
from townlet.oracle.trace_io import CellVerdict, RunParams, Trace


def _v(kind: str, cell: str = "c") -> CellVerdict:
    return CellVerdict(kind=kind, cell_id=cell, detail={})


def test_exit_zero_only_for_agree_and_skipped() -> None:
    assert exit_code([_v("AGREE"), _v("SKIPPED")]) == 0
    assert exit_code([_v("AGREE"), _v("DIVERGE")]) == 1
    assert exit_code([_v("HASH_MISMATCH")]) == 1
    assert exit_code([_v("OLD_SIDE_ERROR")]) == 1
    assert exit_code([_v("NEW_SIDE_ERROR")]) == 1
    assert exit_code([_v("HARNESS_ERROR")]) == 1  # allowlist, not a denylist
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


# --- FIX 4: per-cell containment --------------------------------------------


def test_run_cell_safely_converts_exception_to_harness_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exception escaping run_cell (HarnessError, FileNotFoundError, anything)
    must not abort the whole matrix run — it becomes a HARNESS_ERROR verdict for
    that cell so report.json still gets written for the cells already computed."""
    import townlet.oracle.harness as harness_mod

    def _boom(**kwargs: object) -> CellVerdict:
        raise FileNotFoundError("--out trace file was never written")

    monkeypatch.setattr(harness_mod, "run_cell", _boom)

    cell = Cell(RunParams(pack="p", level="l", num_agents=1, steps=1, seed=1, device="cpu"))
    verdict = run_cell_safely(
        repo_root=Path("/nonexistent"),
        old_src=Path("/nonexistent/old"),
        new_src=Path("/nonexistent/new"),
        cell=cell,
        run_dir=Path("/nonexistent/run"),
        run_cuda=False,
    )
    assert verdict.kind == "HARNESS_ERROR"
    assert verdict.cell_id == cell.cell_id
    assert verdict.detail["exception_type"] == "FileNotFoundError"
    assert "--out trace file" in str(verdict.detail["message"])


def test_run_cell_safely_passes_through_normal_verdicts(monkeypatch: pytest.MonkeyPatch) -> None:
    import townlet.oracle.harness as harness_mod

    monkeypatch.setattr(harness_mod, "run_cell", lambda **kwargs: _v("AGREE", "c"))
    cell = Cell(RunParams(pack="p", level="l", num_agents=1, steps=1, seed=1, device="cpu"))
    verdict = run_cell_safely(
        repo_root=Path("."),
        old_src=Path("."),
        new_src=Path("."),
        cell=cell,
        run_dir=Path("."),
        run_cuda=False,
    )
    assert verdict.kind == "AGREE"


def test_run_side_flags_missing_out_after_zero_exit(tmp_path: Path) -> None:
    """A driver that exits 0 without writing --out (e.g. an argparse SystemExit
    swallowed upstream, or a bug in the driver) must not be treated as success —
    load_trace would otherwise raise deep inside run_cell, uncontained."""
    fake_driver = tmp_path / "fake_driver.py"
    fake_driver.write_text("import sys\nsys.exit(0)\n")
    out = tmp_path / "missing.npz"
    params = RunParams(pack="p", level="l", num_agents=1, steps=1, seed=1, device="cpu")
    result = run_side(driver=fake_driver, src=tmp_path, params=params, out=out, repo_root=tmp_path)
    assert result is not None
    assert str(out) in result


def test_run_side_succeeds_when_out_exists(tmp_path: Path) -> None:
    out = tmp_path / "present.npz"
    fake_driver = tmp_path / "fake_driver.py"
    fake_driver.write_text(f"import sys\nopen({str(out)!r}, 'w').close()\nsys.exit(0)\n")
    params = RunParams(pack="p", level="l", num_agents=1, steps=1, seed=1, device="cpu")
    result = run_side(driver=fake_driver, src=tmp_path, params=params, out=out, repo_root=tmp_path)
    assert result is None


# --- FIX 5: PYTHONPATH injection guard --------------------------------------


def _fake_trace(code_root: str) -> Trace:
    params = RunParams(pack="p", level="l", num_agents=1, steps=1, seed=1, device="cpu")
    return Trace(
        params=params,
        hashes={},
        obs=np.zeros((2, 1, 1), dtype=np.float32),
        rewards=np.zeros((1, 1), dtype=np.float32),
        dones=np.zeros((1, 1), dtype=bool),
        code_root=code_root,
    )


def test_injection_guard_fires_when_sides_report_same_code_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """If PYTHONPATH injection silently failed, both subprocesses would import
    the same working-tree townlet regardless of which src was declared — every
    cell would trivially AGREE and the entire differential run's evidence
    would be a false AGREE. This is the guard against that."""
    import townlet.oracle.harness as harness_mod

    monkeypatch.setattr(harness_mod, "run_side", lambda **kwargs: None)
    monkeypatch.setattr(harness_mod, "load_trace", lambda path: _fake_trace("/same/src"))

    cell = Cell(RunParams(pack="p", level="l", num_agents=1, steps=1, seed=1, device="cpu"))
    verdict = run_cell(
        repo_root=tmp_path,
        old_src=tmp_path / "old",  # old_src != new_src: a genuine differential run
        new_src=tmp_path / "new",
        cell=cell,
        run_dir=tmp_path,
        run_cuda=False,
    )
    assert verdict.kind == "HARNESS_ERROR"
    assert "PYTHONPATH" in str(verdict.detail["reason"])
    assert verdict.detail["code_root"] == "/same/src"


def test_injection_guard_silent_when_code_roots_differ(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import townlet.oracle.harness as harness_mod

    traces = {"old": _fake_trace("/old/src"), "new": _fake_trace("/new/src")}
    calls = iter(["old", "new"])
    monkeypatch.setattr(harness_mod, "run_side", lambda **kwargs: None)
    monkeypatch.setattr(harness_mod, "load_trace", lambda path: traces[next(calls)])

    cell = Cell(RunParams(pack="p", level="l", num_agents=1, steps=1, seed=1, device="cpu"))
    verdict = run_cell(
        repo_root=tmp_path,
        old_src=tmp_path / "old",
        new_src=tmp_path / "new",
        cell=cell,
        run_dir=tmp_path,
        run_cuda=False,
    )
    assert verdict.kind == "AGREE"  # both fake traces are identical apart from code_root


def test_injection_guard_not_applied_to_self_comparison(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """test_self_comparison_agrees deliberately passes old_src == new_src; the
    guard must not fire for that case even though both sides report the same
    code_root, since that IS the same code by design there."""
    import townlet.oracle.harness as harness_mod

    monkeypatch.setattr(harness_mod, "run_side", lambda **kwargs: None)
    monkeypatch.setattr(harness_mod, "load_trace", lambda path: _fake_trace("/same/src"))

    cell = Cell(RunParams(pack="p", level="l", num_agents=1, steps=1, seed=1, device="cpu"))
    same_src = tmp_path / "src"
    verdict = run_cell(
        repo_root=tmp_path,
        old_src=same_src,
        new_src=same_src,
        cell=cell,
        run_dir=tmp_path,
        run_cuda=False,
    )
    assert verdict.kind == "AGREE"


# --- FIX 4 (follow-up): commit-level meta gathered before the cell loop ----


def test_collect_run_meta_gathers_commit_provenance(tmp_path: Path) -> None:
    repo, tag = _make_scratch_repo(tmp_path)
    meta = _collect_run_meta(repo, tag, "20260101-000000")
    assert meta["oracle_ref"] == tag
    assert meta["oracle_commit"] == _git(repo, "rev-parse", "HEAD")
    assert meta["new_commit"] == meta["oracle_commit"]
    assert meta["new_dirty"] is False
    assert meta["generated"] == "20260101-000000"


def test_collect_run_meta_raises_loudly_on_git_failure(tmp_path: Path) -> None:
    """A git failure gathering commit provenance must raise (check=True), not
    be swallowed into a falsely-clean meta record."""
    not_a_repo = tmp_path / "not-a-repo"
    not_a_repo.mkdir()
    with pytest.raises(subprocess.CalledProcessError):
        _collect_run_meta(not_a_repo, "some-tag", "run-id")


def test_main_collects_meta_before_running_any_cell(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Regression pin for FIX 4: _collect_run_meta's git calls (check=True)
    must complete before any cell subprocess runs. Gathered after the loop
    instead, a git failure there would destroy every verdict run_cell_safely
    already computed — the exact all-or-nothing failure mode containment was
    built to eliminate, just moved one block down."""
    import townlet.oracle.harness as harness_mod

    # A fake module __file__ so main()'s repo_root/run_dir resolve under
    # tmp_path instead of touching the real repo's runs/differential/.
    fake_file = tmp_path / "fakepkg" / "src" / "townlet" / "oracle" / "harness.py"
    monkeypatch.setattr(harness_mod, "__file__", str(fake_file))

    order: list[str] = []
    cell = Cell(RunParams(pack="p", level="l", num_agents=1, steps=1, seed=1, device="cpu"))

    def fake_collect_run_meta(repo_root: Path, oracle_ref: str, run_id: str) -> dict[str, object]:
        order.append("meta")
        return {"oracle_ref": oracle_ref, "generated": run_id}

    def fake_run_cell_safely(**kwargs: object) -> CellVerdict:
        order.append("cell")
        got_cell = kwargs["cell"]
        assert isinstance(got_cell, Cell)
        return CellVerdict(kind="AGREE", cell_id=got_cell.cell_id, detail={})

    monkeypatch.setattr(harness_mod, "ensure_worktree", lambda repo_root, tag: tmp_path / "worktree")
    monkeypatch.setattr(harness_mod, "default_cells", lambda: (cell,))
    monkeypatch.setattr(harness_mod, "run_cell_safely", fake_run_cell_safely)
    monkeypatch.setattr(harness_mod, "_collect_run_meta", fake_collect_run_meta)
    monkeypatch.setattr(harness_mod, "write_report", lambda run_dir, verdicts, meta: run_dir / "report.json")

    exit_status = harness_mod.main([])

    assert order == ["meta", "cell"]
    assert exit_status == 0
