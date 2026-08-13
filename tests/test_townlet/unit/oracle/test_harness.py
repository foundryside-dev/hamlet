"""Harness verdict aggregation and report writing — no subprocesses here (WS-7)."""

from __future__ import annotations

import json
from pathlib import Path

from townlet.oracle.harness import exit_code, write_report
from townlet.oracle.trace_io import CellVerdict


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
