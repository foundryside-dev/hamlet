"""Offline reads preserve the complete retained SQLite artifact family."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

import pytest

from tests.test_townlet.unit.demo.test_episode_database_schema import _make_closed_supported_database
from tests.test_townlet.unit.scripts.test_l2_baseline import _write_accounting_run
from townlet.training.episode_accounting import read_episode_accounting


def _family(path: Path) -> dict[str, tuple[bytes, int, int, int, int, int] | None]:
    result = {}
    for suffix in ("", "-wal", "-shm", "-journal"):
        member = Path(str(path) + suffix)
        if not member.exists():
            result[suffix] = None
            continue
        metadata = member.stat()
        result[suffix] = (
            member.read_bytes(),
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        )
    return result


@pytest.fixture(params=["reader", "baseline", "token_regression"])
def consume(request):
    if request.param == "reader":
        return read_episode_accounting
    script = Path(__file__).parents[4] / "scripts" / f"l2_{request.param}.py"
    spec = importlib.util.spec_from_file_location(f"custody_{request.param}", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return lambda run_dir: module.cmd_curves(Namespace(run_dir=str(run_dir)))


def _prepare(run_dir: Path, control: str) -> None:
    if control in {"absent", "empty"}:
        run_dir.mkdir()
        if control == "empty":
            (run_dir / "demo.db").touch()
    elif control == "malformed_current":
        run_dir.mkdir()
        _make_closed_supported_database(run_dir / "demo.db", changed_table="episodes", defect="nullable")
    else:
        _write_accounting_run(
            run_dir,
            duplicate=False,
            wrong_survival=control == "late_tb_failure",
            old_columns=control == "legacy",
        )
    if control.startswith("zero_"):
        Path(str(run_dir / "demo.db") + "-" + control.removeprefix("zero_")).touch()
    if control == "accepted":
        from townlet.training.checkpoint_utils import persist_checkpoint_digest

        torch = pytest.importorskip("torch")
        checkpoint_dir = run_dir / "checkpoints"
        checkpoint_dir.mkdir()
        checkpoint = checkpoint_dir / "checkpoint_ep00001.pt"
        torch.save({"episode": 1, "completed_live_agent_steps": 14}, checkpoint)
        persist_checkpoint_digest(checkpoint)
        (run_dir / "meta.json").write_text(json.dumps({"realized_live_agent_steps": 14}))


@pytest.mark.parametrize(
    "control", ["legacy", "malformed_current", "late_tb_failure", "zero_wal", "zero_shm", "zero_journal", "absent", "empty"]
)
def test_refusal_preserves_family_and_never_opens_original_with_sqlite(consume, tmp_path: Path, control: str) -> None:
    run_dir = tmp_path / "run"
    _prepare(run_dir, control)
    database = run_dir / "demo.db"
    before = _family(database)
    real_connect = sqlite3.connect
    original_opens = []
    connections = []

    def observe_connect(target, *args, **kwargs):
        target_path = unquote(urlsplit(str(target)).path) if str(target).startswith("file:") else str(target)
        if Path(target_path).absolute() == database.absolute():
            original_opens.append(str(target))
        connection = real_connect(target, *args, **kwargs)
        connections.append(connection)
        return connection

    with patch("sqlite3.connect", side_effect=observe_connect):
        with pytest.raises((ValueError, FileNotFoundError, sqlite3.DatabaseError)):
            consume(run_dir)
    assert _family(database) == before
    assert original_opens == []
    assert not (run_dir / "curves.csv").exists()
    assert not (run_dir / "transitions.csv").exists()
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")


def test_accepted_closed_current_wal_read_preserves_family_and_uses_private_connections(consume, tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    _prepare(run_dir, "accepted")
    database = run_dir / "demo.db"
    before = _family(database)
    assert before[""] is not None
    assert before[""][0][18:20] == b"\x02\x02"  # Closed file still carries WAL journal mode.
    assert all(before[suffix] is None for suffix in ("-wal", "-shm", "-journal"))
    real_connect = sqlite3.connect
    opened_paths = []
    connections = []

    def observe_connect(target, *args, **kwargs):
        target_path = unquote(urlsplit(str(target)).path) if str(target).startswith("file:") else str(target)
        opened_paths.append(Path(target_path).absolute())
        connection = real_connect(target, *args, **kwargs)
        connections.append(connection)
        return connection

    with patch("sqlite3.connect", side_effect=observe_connect):
        rows = consume(run_dir)
    assert _family(database) == before
    assert opened_paths and database.absolute() not in opened_paths
    if rows is not None:
        assert [(row.survival_steps_agent0, row.batch_episode_steps, row.live_agent_transitions) for row in rows] == [(2, 5, 7)] * 2
    else:
        assert (run_dir / "curves.csv").is_file()
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")


def test_snapshot_requires_explicit_exclusive_custody_before_sqlite(tmp_path: Path) -> None:
    from townlet.demo.database import read_existing_demo_snapshot

    database = tmp_path / "absent.db"
    with patch("sqlite3.connect") as connect:
        with pytest.raises(ValueError, match="Exclusive"):
            with read_existing_demo_snapshot(database, exclusive_custody=False):
                pytest.fail("Snapshot admitted without custody")
    connect.assert_not_called()
    assert not database.exists()


def test_external_family_change_during_real_event_reload_refuses_before_export(consume, tmp_path: Path) -> None:
    from townlet.training.episode_accounting import EventAccumulator

    run_dir = tmp_path / "run"
    _prepare(run_dir, "accepted")
    database = run_dir / "demo.db"
    before = _family(database)
    original_reload = EventAccumulator.Reload
    journal = Path(str(database) + "-journal")

    def reload_then_external_change(accumulator):
        result = original_reload(accumulator)
        journal.write_bytes(b"external owner changed custody")
        return result

    with patch.object(EventAccumulator, "Reload", reload_then_external_change):
        with pytest.raises(ValueError, match="family changed"):
            consume(run_dir)
    after = _family(database)
    assert after[""] == before[""]
    assert after["-wal"] == before["-wal"]
    assert after["-shm"] == before["-shm"]
    assert journal.read_bytes() == b"external owner changed custody"
    assert not (run_dir / "curves.csv").exists()
    assert not (run_dir / "transitions.csv").exists()
