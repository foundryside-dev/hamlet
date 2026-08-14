"""Harness verdict aggregation and report writing — no subprocesses here (WS-7)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from townlet.oracle.harness import (
    SideFailure,
    _collect_run_meta,
    _final_exception_text,
    _git,
    _validate_lone_trace,
    ensure_worktree,
    exit_code,
    run_cell,
    run_cell_safely,
    run_side,
    write_report,
)
from townlet.oracle.matrix import Cell, RegisteredDivergence
from townlet.oracle.trace_io import CellVerdict, HarnessError, RunParams, Trace


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


# --- hamlet-56ec575ae2: exit_code must be able to PASS a registered divergence


def test_exit_code_passes_a_matched_registered_divergence() -> None:
    matched = CellVerdict(kind="DIVERGED_AS_REGISTERED", cell_id="c", detail={}, register_refs=("DIV-003",))
    assert exit_code([matched]) == 0
    assert exit_code([_v("AGREE"), matched, _v("SKIPPED")]) == 0
    # ...but it excuses ONLY its own cell — an unmatched red elsewhere still fails.
    assert exit_code([matched, _v("DIVERGE")]) == 1
    assert exit_code([matched, _v("OLD_SIDE_ERROR")]) == 1


def test_exit_code_fails_the_matched_kind_without_refs() -> None:
    """kind + non-empty refs are BOTH required: a DIVERGED_AS_REGISTERED that
    names no register entry is a harness bug, not a pass."""
    assert exit_code([CellVerdict(kind="DIVERGED_AS_REGISTERED", cell_id="c", detail={})]) == 1


def test_exit_code_fails_clean_kinds_that_carry_refs() -> None:
    """The inverse contract breach: register_refs may appear ONLY on the
    matched kind. An AGREE or SKIPPED carrying refs means something populated
    them outside the matcher — refuse to look green."""
    for kind in ("AGREE", "SKIPPED"):
        odd = CellVerdict(kind=kind, cell_id="c", detail={}, register_refs=("DIV-003",))
        assert exit_code([odd]) == 1


def test_exit_code_fails_registered_divergence_absent() -> None:
    """An expectation that never fires is a stale register entry — a finding,
    never a pass, with or without refs attached."""
    assert exit_code([_v("REGISTERED_DIVERGENCE_ABSENT")]) == 1
    with_refs = CellVerdict(kind="REGISTERED_DIVERGENCE_ABSENT", cell_id="c", detail={}, register_refs=("DIV-003",))
    assert exit_code([with_refs]) == 1


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
    load_trace would otherwise raise deep inside run_cell, uncontained. And it
    must be distinguished from a crash: the synthesized text embeds stdout and
    harness phrasing, which must never satisfy a registered crash signature."""
    fake_driver = tmp_path / "fake_driver.py"
    fake_driver.write_text("import sys\nsys.exit(0)\n")
    out = tmp_path / "missing.npz"
    params = RunParams(pack="p", level="l", num_agents=1, steps=1, seed=1, device="cpu")
    result = run_side(driver=fake_driver, src=tmp_path, params=params, out=out, repo_root=tmp_path)
    assert result is not None
    assert result.kind == "no_trace"
    assert str(out) in result.stderr


def test_run_side_reports_a_nonzero_exit_as_crashed(tmp_path: Path) -> None:
    fake_driver = tmp_path / "fake_driver.py"
    fake_driver.write_text("import sys\nsys.stderr.write('it broke loudly\\n')\nsys.exit(3)\n")
    out = tmp_path / "never.npz"
    params = RunParams(pack="p", level="l", num_agents=1, steps=1, seed=1, device="cpu")
    result = run_side(driver=fake_driver, src=tmp_path, params=params, out=out, repo_root=tmp_path)
    assert result is not None
    assert result.kind == "crashed"
    assert "it broke loudly" in result.stderr


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


# --- hamlet-56ec575ae2: run_cell adjudication of a declared expectation -----
#
# The registered shape (DIV-003, PDR-0036): the ORACLE side fails to produce a
# trace at all, with a declared stderr signature, while the REBUILD produces a
# valid one. Everything below hunts the wrong-pass surface of that contract.

_SIGNATURE = "RuntimeError: oracle cannot reset this substrate"


def _expect_cell(device: str = "cpu", ref: str = "DIV-003") -> Cell:
    return Cell(
        RunParams(pack="p", level="l", num_agents=2, steps=3, seed=7, device=device),
        expected=RegisteredDivergence(register_ref=ref, old_stderr_substring=_SIGNATURE),
    )


def _crashed(final_exception: str = _SIGNATURE, *, pre: str = "") -> SideFailure:
    """A crashed-side failure whose stderr is a well-formed traceback with
    final_exception as the exception line, optionally preceded by noise."""
    return SideFailure(
        kind="crashed",
        stderr=(f'{pre}Traceback (most recent call last):\n  File "/x/y.py", line 1, in <module>\n    boom()\n{final_exception}\n'),
    )


def _trace_for(params: RunParams, code_root: str, obs_fill: float = 0.0) -> Trace:
    return Trace(
        params=params,
        hashes={},
        obs=np.full((params.steps + 1, params.num_agents, 3), obs_fill, dtype=np.float32),
        rewards=np.zeros((params.steps, params.num_agents), dtype=np.float32),
        dones=np.zeros((params.steps, params.num_agents), dtype=bool),
        code_root=code_root,
    )


def _fake_sides(monkeypatch: pytest.MonkeyPatch, *, old: SideFailure | None, new: SideFailure | None) -> list[str]:
    """Monkeypatch run_side with per-side results; returns the call log."""
    import townlet.oracle.harness as harness_mod

    calls: list[str] = []

    def fake_run_side(*, driver: Path, src: Path, params: RunParams, out: Path, repo_root: Path) -> SideFailure | None:
        side = "old" if str(src).endswith("old") else "new"
        calls.append(side)
        return old if side == "old" else new

    monkeypatch.setattr(harness_mod, "run_side", fake_run_side)
    return calls


def _run_expect_cell(cell: Cell, tmp_path: Path) -> CellVerdict:
    return run_cell(
        repo_root=tmp_path,
        old_src=tmp_path / "old",
        new_src=tmp_path / "new",
        cell=cell,
        run_dir=tmp_path,
        run_cuda=False,
    )


def test_registered_old_crash_with_running_new_side_passes_as_registered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import townlet.oracle.harness as harness_mod

    cell = _expect_cell()
    new_root = str((tmp_path / "new").resolve())
    calls = _fake_sides(monkeypatch, old=_crashed(), new=None)
    monkeypatch.setattr(harness_mod, "load_trace", lambda path: _trace_for(cell.params, new_root))

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "DIVERGED_AS_REGISTERED"
    assert verdict.register_refs == ("DIV-003",)
    assert verdict.detail["register_ref"] == "DIV-003"
    assert verdict.detail["new_code_root"] == new_root
    assert _SIGNATURE in str(verdict.detail["old_final_exception"])
    # The new side MUST actually have run: an old-side crash alone proves
    # nothing about the rebuild — pre-knockdown BOTH sides crash, and passing
    # on the old crash alone would certify a knockdown that never happened.
    assert calls == ["old", "new"]


def test_matched_ref_is_the_declared_one_not_a_constant(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Mutation kill: a hardcoded register_refs=("DIV-003",) must not survive —
    the verdict must carry whatever ref the CELL declared."""
    import townlet.oracle.harness as harness_mod

    cell = _expect_cell(ref="DIV-042")
    _fake_sides(monkeypatch, old=_crashed(), new=None)
    monkeypatch.setattr(harness_mod, "load_trace", lambda path: _trace_for(cell.params, str((tmp_path / "new").resolve())))

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "DIVERGED_AS_REGISTERED"
    assert verdict.register_refs == ("DIV-042",)
    assert verdict.detail["register_ref"] == "DIV-042"


def test_old_crash_without_the_registered_signature_still_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A registered entry must not wave through an UNRELATED old-side failure
    on the same cell — the match is the signature, not the crash."""
    cell = _expect_cell()
    calls = _fake_sides(monkeypatch, old=_crashed("KeyError: 'entirely_unrelated'"), new=None)

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "OLD_SIDE_ERROR"
    assert verdict.register_refs == ()
    assert verdict.detail["side"] == "old"
    expectation = verdict.detail["expectation"]
    assert isinstance(expectation, dict)
    assert expectation["register_ref"] == "DIV-003"
    assert expectation["expected_substring"] == _SIGNATURE
    assert calls == ["old"]  # unexplained old-side failure: nothing more to adjudicate


def test_signature_in_noise_before_an_unrelated_crash_does_not_match(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Co-occurrence is not causation: the signature appearing in a warning
    line, with the process then dying of something else, must NOT pass — the
    match is anchored to the final exception text, not the whole stream."""
    cell = _expect_cell()
    _fake_sides(
        monkeypatch,
        old=_crashed("ValueError: something else entirely", pre=f"WARNING: {_SIGNATURE}\n"),
        new=None,
    )

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "OLD_SIDE_ERROR"
    assert verdict.register_refs == ()
    assert "final exception" in str(verdict.detail["expectation"]["status"])


def test_signature_in_a_frame_path_does_not_match(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Frame lines are indented and excluded from the match target: a
    signature that happens to appear in a file path certifies nothing."""
    cell = _expect_cell()
    stderr = f'Traceback (most recent call last):\n  File "{_SIGNATURE}", line 1, in <module>\nValueError: unrelated\n'
    _fake_sides(monkeypatch, old=SideFailure(kind="crashed", stderr=stderr), new=None)

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "OLD_SIDE_ERROR"
    assert verdict.register_refs == ()


def test_crash_without_a_traceback_does_not_match(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A crash with no Python traceback on stderr (hard abort, C++ layer)
    cannot be anchored — fail closed, never guess."""
    cell = _expect_cell()
    _fake_sides(monkeypatch, old=SideFailure(kind="crashed", stderr=f"{_SIGNATURE}\n"), new=None)

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "OLD_SIDE_ERROR"
    assert verdict.register_refs == ()
    assert "traceback" in str(verdict.detail["expectation"]["status"]).lower()


def test_a_non_crash_failure_does_not_match_even_with_the_signature_embedded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The exit-0-without---out failure returns HARNESS-SYNTHESIZED text that
    embeds driver stdout AND stderr; the signature appearing there is not the
    registered crash (adversarial finding, reproduced pre-fix: this passed).
    The embedded stderr here carries a complete, well-formed traceback ending
    in the signature — the realistic FIX-4 shape (exception printed, then
    swallowed upstream, exit 0) — so the kind=="crashed" conjunct is doing the
    work on its own, not hiding behind the traceback anchor."""
    cell = _expect_cell()
    embedded_tb = f'Traceback (most recent call last):\n  File "/x/y.py", line 1, in <module>\n{_SIGNATURE}\n'
    synthetic = f"driver exited 0 but did not write --out file /x/old.npz\nstdout:\n\nstderr:\n{embedded_tb}"
    _fake_sides(monkeypatch, old=SideFailure(kind="no_trace", stderr=synthetic), new=None)

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "OLD_SIDE_ERROR"
    assert verdict.register_refs == ()
    assert verdict.detail["failure_kind"] == "no_trace"
    assert "without crashing" in str(verdict.detail["expectation"]["status"])


def test_a_crash_that_still_wrote_a_trace_does_not_match(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The registered shape is 'fails to produce a trace'. A side that wrote a
    complete trace and THEN died is not that shape — and suppressing it would
    discard a comparable trace."""
    cell = _expect_cell()
    _fake_sides(monkeypatch, old=_crashed(), new=None)
    old_out = tmp_path / (cell.cell_id.replace(":", "_") + ".old.npz")
    old_out.write_bytes(b"placeholder written before the crash")

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "OLD_SIDE_ERROR"
    assert verdict.register_refs == ()
    assert "wrote a trace" in str(verdict.detail["expectation"]["status"])


def test_matched_path_rejects_a_new_trace_from_the_wrong_code_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """FIX 5 analog for the lone-trace path: with no old trace to compare
    code_root against, the new trace must prove it ran the declared src."""
    import townlet.oracle.harness as harness_mod

    cell = _expect_cell()
    _fake_sides(monkeypatch, old=_crashed(), new=None)
    monkeypatch.setattr(harness_mod, "load_trace", lambda path: _trace_for(cell.params, "/somewhere/else/src"))

    with pytest.raises(HarnessError, match="code_root"):
        _run_expect_cell(cell, tmp_path)


def test_registered_old_crash_with_crashing_new_side_fails_as_not_yet_built(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Pre-knockdown state: both sides crash. The old side matching the
    signature is NOT a pass — the divergence exists only once the rebuild
    actually runs. This is the test for the short-circuit hole."""
    cell = _expect_cell()
    calls = _fake_sides(
        monkeypatch,
        old=_crashed(),
        new=_crashed("RuntimeError: rebuild also dies"),
    )

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "NEW_SIDE_ERROR"
    assert verdict.register_refs == ()
    assert verdict.detail["side"] == "new"
    expectation = verdict.detail["expectation"]
    assert isinstance(expectation, dict)
    assert expectation["register_ref"] == "DIV-003"
    assert "not" in str(expectation["status"]).lower() and "built" in str(expectation["status"]).lower()
    assert calls == ["old", "new"]


def test_expectation_with_agreeing_sides_fails_as_absent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The old side RAN on a cell registered to crash: the register entry is
    stale (or the surface regressed to agreement). Especially when the traces
    AGREE, this must fail — an expectation that never fires is exactly the
    unexercised suppression machinery PDR-0037's reversal trigger names."""
    import townlet.oracle.harness as harness_mod

    cell = _expect_cell()
    _fake_sides(monkeypatch, old=None, new=None)
    traces = {"old": _trace_for(cell.params, "/old/src"), "new": _trace_for(cell.params, "/new/src")}
    order = iter(["old", "new"])
    monkeypatch.setattr(harness_mod, "load_trace", lambda path: traces[next(order)])

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "REGISTERED_DIVERGENCE_ABSENT"
    assert verdict.register_refs == ()
    assert verdict.detail["register_ref"] == "DIV-003"
    assert verdict.detail["underlying_kind"] == "AGREE"


def test_expectation_with_diverging_sides_fails_as_absent_with_evidence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Old ran AND the traces differ: two findings at once. The verdict stays
    REGISTERED_DIVERGENCE_ABSENT (the registered shape did not manifest) and
    carries the underlying DIVERGE as evidence — it must never pass as if the
    trace divergence were the registered one."""
    import townlet.oracle.harness as harness_mod

    cell = _expect_cell()
    _fake_sides(monkeypatch, old=None, new=None)
    traces = {"old": _trace_for(cell.params, "/old/src", obs_fill=0.0), "new": _trace_for(cell.params, "/new/src", obs_fill=1.0)}
    order = iter(["old", "new"])
    monkeypatch.setattr(harness_mod, "load_trace", lambda path: traces[next(order)])

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "REGISTERED_DIVERGENCE_ABSENT"
    assert verdict.register_refs == ()
    assert verdict.detail["underlying_kind"] == "DIVERGE"
    assert verdict.detail["underlying_detail"]  # the localization evidence survives


def test_expectation_with_old_running_and_new_crashing_fails_as_new_side_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cell = _expect_cell()
    _fake_sides(monkeypatch, old=None, new=_crashed("RuntimeError: rebuild dies"))

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "NEW_SIDE_ERROR"
    assert verdict.register_refs == ()
    expectation = verdict.detail["expectation"]
    assert isinstance(expectation, dict)
    assert expectation["register_ref"] == "DIV-003"


def test_matched_path_rejects_a_new_trace_with_wrong_params(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """With no old trace to compare against, the lone new trace must at least
    prove it is THIS cell's run — a driver that ignored its argv would
    otherwise certify the wrong experiment."""
    import townlet.oracle.harness as harness_mod

    cell = _expect_cell()
    _fake_sides(monkeypatch, old=_crashed(), new=None)
    wrong = RunParams(pack="p", level="l", num_agents=2, steps=3, seed=8, device="cpu")  # seed differs
    monkeypatch.setattr(harness_mod, "load_trace", lambda path: _trace_for(wrong, str((tmp_path / "new").resolve())))

    with pytest.raises(HarnessError, match="params"):
        _run_expect_cell(cell, tmp_path)


def test_matched_path_rejects_a_new_trace_with_inconsistent_shapes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import townlet.oracle.harness as harness_mod

    cell = _expect_cell()
    _fake_sides(monkeypatch, old=_crashed(), new=None)
    good = _trace_for(cell.params, str((tmp_path / "new").resolve()))
    truncated = Trace(
        params=good.params,
        hashes=good.hashes,
        obs=good.obs[:-1],  # one frame short of steps+1
        rewards=good.rewards,
        dones=good.dones,
        code_root=good.code_root,
    )
    monkeypatch.setattr(harness_mod, "load_trace", lambda path: truncated)

    with pytest.raises(HarnessError, match="shape"):
        _run_expect_cell(cell, tmp_path)


def test_plain_cell_old_error_still_short_circuits_the_new_side(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Regression pin: cells WITHOUT an expectation keep today's behaviour
    exactly — old-side failure returns immediately, new side never runs, no
    expectation key in the detail."""
    cell = Cell(RunParams(pack="p", level="l", num_agents=2, steps=3, seed=7, device="cpu"))
    calls = _fake_sides(monkeypatch, old=_crashed("RuntimeError: boom happened here"), new=None)

    verdict = _run_expect_cell(cell, tmp_path)
    assert verdict.kind == "OLD_SIDE_ERROR"
    assert verdict.register_refs == ()
    assert "expectation" not in verdict.detail
    assert calls == ["old"]


def test_expectation_cell_cuda_skip_carries_no_refs(tmp_path: Path) -> None:
    verdict = run_cell(
        repo_root=Path("/nonexistent"),
        old_src=Path("/nonexistent/old"),
        new_src=Path("/nonexistent/new"),
        cell=_expect_cell("cuda"),
        run_dir=tmp_path,
        run_cuda=False,
    )
    assert verdict.kind == "SKIPPED"
    assert verdict.register_refs == ()


def test_exit_code_fails_an_all_skipped_run() -> None:
    """'Doing nothing cannot look green' has to cover more than the empty
    list: a run in which every declared cell was SKIPPED executed nothing and
    proves nothing. Unreachable through today's cpu+cuda matrix — this pins
    the rule against future matrix shapes."""
    assert exit_code([_v("SKIPPED")]) == 1
    assert exit_code([_v("SKIPPED"), _v("SKIPPED")]) == 1
    assert exit_code([_v("SKIPPED"), _v("AGREE")]) == 0  # one executed cell suffices


def test_validate_lone_trace_rejects_each_array_shape_independently() -> None:
    """Mutation kills: a validator that checks obs alone (or drops the ndim
    check) must not survive — every array is validated against the cell's own
    declared params."""
    import dataclasses

    cell = _expect_cell()
    p = cell.params
    good = _trace_for(p, "/s")
    bad_arrays = {
        "rewards": np.zeros((p.num_agents, p.steps), dtype=np.float32),  # transposed
        "dones": np.zeros((p.steps + 1, p.num_agents), dtype=bool),  # off by one
        "obs": np.zeros((p.steps + 1, p.num_agents), dtype=np.float32),  # ndim 2, matching prefix
    }
    for field, bad in bad_arrays.items():
        mutated = dataclasses.replace(good, **{field: bad})
        with pytest.raises(HarnessError, match="shape"):
            _validate_lone_trace(mutated, cell)
    _validate_lone_trace(good, cell)  # and the unmutated trace passes


def test_final_exception_text_extraction() -> None:
    """The match target is the unindented exception line(s) of the LAST
    traceback block — not frames, not noise before it, not chained blocks."""
    tb = 'Traceback (most recent call last):\n  File "/a/b.py", line 1, in <module>\n    x()\nValueError: first\n'
    chained = (
        tb
        + "\nDuring handling of the above exception, another exception occurred:\n\n"
        + ('Traceback (most recent call last):\n  File "/c/d.py", line 2, in <module>\nRuntimeError: second\n')
    )
    assert _final_exception_text(tb) == "ValueError: first"
    assert _final_exception_text(chained) == "RuntimeError: second"
    assert _final_exception_text("WARNING: noise\n" + tb) == "ValueError: first"
    assert _final_exception_text("no traceback here at all") is None
    assert _final_exception_text("Traceback (most recent call last):\n") is None
    multiline = (
        'Traceback (most recent call last):\n  File "/a.py", line 1, in <module>\npydantic.ValidationError: 2 errors\nfield_a missing\n'
    )
    assert _final_exception_text(multiline) == "pydantic.ValidationError: 2 errors\nfield_a missing"


def test_report_serializes_register_refs(tmp_path: Path) -> None:
    matched = CellVerdict(
        kind="DIVERGED_AS_REGISTERED",
        cell_id="c",
        detail={"register_ref": "DIV-003"},
        register_refs=("DIV-003",),
    )
    path = write_report(tmp_path, [matched], {})
    report = json.loads(path.read_text())
    assert report["verdicts"][0]["register_refs"] == ["DIV-003"]


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
