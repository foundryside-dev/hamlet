"""Episode accounting requires a stamped schema and refusal without artifact mutation."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from townlet.demo.database import DemoDatabase


def family_bytes(path: Path) -> dict[str, bytes | None]:
    return {
        suffix: member.read_bytes() if member.exists() else None
        for suffix in ("", "-wal", "-shm", "-journal")
        for member in (Path(str(path) + suffix),)
    }


def test_fresh_schema_stamps_accounting_columns_and_roundtrips_truthful_units(tmp_path: Path) -> None:
    path = tmp_path / "fresh.db"
    db = DemoDatabase(path)
    try:
        assert db.conn.execute("PRAGMA user_version").fetchone()[0] == 1
        episode_columns = {row[1]: row for row in db.conn.execute("PRAGMA table_xinfo(episodes)")}
        recording_columns = {row[1]: row for row in db.conn.execute("PRAGMA table_xinfo(episode_recordings)")}
        for name, declared in (
            ("batch_episode_steps", "INTEGER"),
            ("live_agent_transitions", "INTEGER"),
            ("completion_reason", "TEXT"),
            ("shaping_reward", "REAL"),
        ):
            assert episode_columns[name][2:5] == (declared, 1, None)
        assert recording_columns["completion_reason"][2:5] == ("TEXT", 1, None)
        assert recording_columns["shaping_reward"][2:5] == ("REAL", 1, None)
        db.insert_episode(
            episode_id=0,
            timestamp=1.0,
            survival_time=2,
            batch_episode_steps=5,
            live_agent_transitions=7,
            completion_reason="authored_terminal",
            total_reward=1.0,
            extrinsic_reward=0.5,
            intrinsic_reward=0.3,
            shaping_reward=0.2,
            intrinsic_weight=0.1,
            curriculum_stage=1,
            epsilon=0.0,
            observation_schema_hash="schema",
        )
        row = db.get_latest_episodes()[0]
        assert (row["survival_time"], row["batch_episode_steps"], row["live_agent_transitions"]) == (2, 5, 7)
        assert row["completion_reason"] == "authored_terminal"
        assert row["shaping_reward"] == 0.2
    finally:
        db.close()
    assert family_bytes(path)["-wal"] is None
    reopened = DemoDatabase(path)
    try:
        assert reopened.get_latest_episodes()[0]["survival_time"] == 2
    finally:
        reopened.close()


@pytest.mark.parametrize("control", ["old", "malformed_current", "truncated", "orphan_wal", "orphan_shm", "orphan_journal"])
def test_refusal_preserves_original_family_before_any_original_sqlite_open(tmp_path: Path, control: str) -> None:
    path = tmp_path / "retained.db"
    if control == "truncated":
        path.write_bytes(b"SQLite format 3\x00truncated")
    else:
        with sqlite3.connect(path) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                "CREATE TABLE episodes (episode_id INTEGER PRIMARY KEY, timestamp REAL NOT NULL, "
                "survival_time TEXT NOT NULL, total_reward REAL NOT NULL, extrinsic_reward REAL NOT NULL, "
                "intrinsic_reward REAL NOT NULL, intrinsic_weight REAL NOT NULL, curriculum_stage INTEGER NOT NULL, "
                "epsilon REAL NOT NULL, observation_schema_hash TEXT NOT NULL)"
            )
            connection.execute("INSERT INTO episodes VALUES (7, 1.0, 'retained', 1.0, 1.0, 0.0, 0.0, 1, 0.0, 'schema')")
            if control == "malformed_current":
                connection.execute("PRAGMA user_version=1")
        connection.close()
        if control.startswith("orphan_"):
            Path(str(path) + "-" + control.removeprefix("orphan_")).write_bytes(b"")
    before = family_bytes(path)
    original_connect = sqlite3.connect
    original_opens = []

    def observe_connect(database, *args, **kwargs):
        if str(database).split("?", 1)[0].removeprefix("file:") == str(path):
            original_opens.append(str(database))
        return original_connect(database, *args, **kwargs)

    with patch("sqlite3.connect", side_effect=observe_connect):
        with pytest.raises(ValueError):
            DemoDatabase(path)
    assert original_opens == []
    assert family_bytes(path) == before


# This specification is trusted test input, independent of the artifact under inspection.
_SUPPORTED_COLUMNS = {
    "episodes": (
        ("episode_id", "INTEGER PRIMARY KEY"),
        ("timestamp", "REAL NOT NULL"),
        ("survival_time", "INTEGER NOT NULL"),
        ("batch_episode_steps", "INTEGER NOT NULL"),
        ("live_agent_transitions", "INTEGER NOT NULL"),
        ("completion_reason", "TEXT NOT NULL"),
        ("total_reward", "REAL NOT NULL"),
        ("extrinsic_reward", "REAL NOT NULL"),
        ("intrinsic_reward", "REAL NOT NULL"),
        ("shaping_reward", "REAL NOT NULL"),
        ("intrinsic_weight", "REAL NOT NULL"),
        ("curriculum_stage", "INTEGER NOT NULL"),
        ("epsilon", "REAL NOT NULL"),
        ("observation_schema_hash", "TEXT NOT NULL"),
    ),
    "affordance_visits": (
        ("episode_id", "INTEGER NOT NULL"),
        ("from_affordance", "TEXT NOT NULL"),
        ("to_affordance", "TEXT NOT NULL"),
        ("visit_count", "INTEGER NOT NULL"),
    ),
    "position_heatmap": (
        ("episode_id", "INTEGER NOT NULL"),
        ("x", "INTEGER NOT NULL"),
        ("y", "INTEGER NOT NULL"),
        ("visit_count", "INTEGER NOT NULL"),
        ("novelty_value", "REAL"),
    ),
    "system_state": (("key", "TEXT PRIMARY KEY"), ("value", "TEXT NOT NULL")),
    "episode_recordings": (
        ("episode_id", "INTEGER PRIMARY KEY"),
        ("file_path", "TEXT NOT NULL"),
        ("timestamp", "REAL NOT NULL"),
        ("survival_steps", "INTEGER NOT NULL"),
        ("completion_reason", "TEXT NOT NULL"),
        ("total_reward", "REAL NOT NULL"),
        ("extrinsic_reward", "REAL NOT NULL"),
        ("intrinsic_reward", "REAL NOT NULL"),
        ("shaping_reward", "REAL NOT NULL"),
        ("curriculum_stage", "INTEGER NOT NULL"),
        ("epsilon", "REAL NOT NULL"),
        ("intrinsic_weight", "REAL NOT NULL"),
        ("recording_reason", "TEXT NOT NULL"),
        ("file_size_bytes", "INTEGER"),
        ("compressed_size_bytes", "INTEGER"),
    ),
}
_EXPECTED_COLUMNS = {
    table: tuple(
        (cid, name, declaration.split()[0], int("NOT NULL" in declaration), None, int("PRIMARY KEY" in declaration), 0)
        for cid, (name, declaration) in enumerate(columns)
    )
    for table, columns in _SUPPORTED_COLUMNS.items()
}


def _make_closed_supported_database(path: Path, *, changed_table: str | None, defect: str | None) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        for table, columns in _SUPPORTED_COLUMNS.items():
            declarations = [f'"{name}" {declaration}' for name, declaration in columns]
            if table == changed_table:
                if defect == "type":
                    declarations[0] = (
                        declarations[0].replace("INTEGER", "TEXT")
                        if "INTEGER" in declarations[0]
                        else declarations[0].replace("TEXT", "BLOB")
                    )
                elif defect == "nullable":
                    declarations[1] = declarations[1].replace(" NOT NULL", "")
                elif defect == "default":
                    declarations[1] += " DEFAULT 0"
                elif defect == "key":
                    declarations[0] = (
                        declarations[0].replace(" PRIMARY KEY", "")
                        if "PRIMARY KEY" in declarations[0]
                        else declarations[0] + " PRIMARY KEY"
                    )
                elif defect == "hidden":
                    declarations.append('"hidden_value" INTEGER GENERATED ALWAYS AS (1) VIRTUAL')
                elif defect == "missing_column":
                    declarations.pop()
            connection.execute(f'CREATE TABLE "{table}" ({", ".join(declarations)})')
        connection.execute("PRAGMA user_version=1")
        connection.commit()
    finally:
        connection.close()
    assert not any(family_bytes(path)[suffix] is not None for suffix in ("-wal", "-shm", "-journal"))


def _assert_refusal_without_original_open(path: Path) -> None:
    before = family_bytes(path)
    original_connect = sqlite3.connect
    original_opens = []

    def observe_connect(database, *args, **kwargs):
        if str(database).split("?", 1)[0].removeprefix("file:") == str(path):
            original_opens.append(str(database))
        return original_connect(database, *args, **kwargs)

    with patch("sqlite3.connect", side_effect=observe_connect):
        with pytest.raises(ValueError):
            DemoDatabase(path)
    assert original_opens == []
    assert family_bytes(path) == before


@pytest.mark.parametrize("table", list(_SUPPORTED_COLUMNS))
@pytest.mark.parametrize("defect", ["type", "nullable", "default", "key", "hidden", "missing_column"])
def test_current_stamp_requires_complete_column_metadata_before_original_open(tmp_path: Path, table: str, defect: str) -> None:
    path = tmp_path / "malformed.db"
    _make_closed_supported_database(path, changed_table=table, defect=defect)
    _assert_refusal_without_original_open(path)


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
@pytest.mark.parametrize("content", [b"", b"orphan pending state"])
def test_current_stamp_refuses_every_companion_even_empty(tmp_path: Path, suffix: str, content: bytes) -> None:
    path = tmp_path / "current.db"
    _make_closed_supported_database(path, changed_table=None, defect=None)
    Path(str(path) + suffix).write_bytes(content)
    _assert_refusal_without_original_open(path)


def test_current_committed_wal_family_is_refused_and_preserved(tmp_path: Path) -> None:
    path = tmp_path / "current.db"
    _make_closed_supported_database(path, changed_table=None, defect=None)
    owner = sqlite3.connect(path)
    try:
        owner.execute("PRAGMA wal_autocheckpoint=0")
        owner.execute("INSERT INTO system_state VALUES ('pending', 'committed in WAL')")
        owner.commit()
        assert family_bytes(path)["-wal"]
        _assert_refusal_without_original_open(path)
    finally:
        owner.close()


def test_exclusive_custody_is_an_explicit_preflight_requirement(tmp_path: Path) -> None:
    from townlet.demo import database

    path = tmp_path / "current.db"
    _make_closed_supported_database(path, changed_table=None, defect=None)
    inspect = getattr(database, "inspect_existing_demo_schema", None)
    assert callable(inspect), "An explicit OS/private-copy preflight is required"
    before = family_bytes(path)
    with patch("sqlite3.connect", side_effect=AssertionError("No custody permits no SQLite open")):
        with pytest.raises(ValueError, match="custody"):
            inspect(path, _EXPECTED_COLUMNS, exclusive_custody=False)
    assert family_bytes(path) == before


@pytest.mark.parametrize("injection", ["main", "companion"])
def test_detected_external_change_refuses_real_open_and_preserves_injected_state(tmp_path: Path, injection: str) -> None:
    path = tmp_path / "current.db"
    _make_closed_supported_database(path, changed_table=None, defect=None)
    original_connect = sqlite3.connect
    original_opens = []
    injected = []

    def inject_at_private_validation(database, *args, **kwargs):
        opened = str(database).split("?", 1)[0].removeprefix("file:")
        if opened == str(path):
            original_opens.append(opened)
        elif not injected:
            if injection == "main":
                data = bytearray(path.read_bytes())
                data[60:64] = (2).to_bytes(4, "big")
                path.write_bytes(data)
            else:
                Path(str(path) + "-wal").write_bytes(b"external writer")
            injected.append(family_bytes(path))
        return original_connect(database, *args, **kwargs)

    with patch("sqlite3.connect", side_effect=inject_at_private_validation):
        with pytest.raises(ValueError, match="changed"):
            DemoDatabase(path)
    assert injected, "Control must reach private validation and actually inject a source change"
    assert original_opens == []
    assert family_bytes(path) == injected[0]


def test_all_fresh_tables_match_full_trusted_column_specification(tmp_path: Path) -> None:
    with DemoDatabase(tmp_path / "fresh.db") as db:
        for table, expected in _EXPECTED_COLUMNS.items():
            assert tuple(tuple(row) for row in db.conn.execute(f'PRAGMA table_xinfo("{table}")')) == expected


@pytest.mark.parametrize("control", ["corrupt_header", "corrupt_page", "wrong_version", "extra_table", "missing_table"])
def test_nonempty_unsupported_artifacts_never_become_fresh_databases(tmp_path: Path, control: str) -> None:
    path = tmp_path / "retained.db"
    _make_closed_supported_database(path, changed_table=None, defect=None)
    if control == "corrupt_header":
        path.write_bytes(b"not an SQLite artifact" + b"x" * 512)
    elif control == "corrupt_page":
        data = bytearray(path.read_bytes())
        data[100] = 0  # Invalid first B-tree page type; keep its valid header and current stamp.
        path.write_bytes(data)
    elif control == "wrong_version":
        data = bytearray(path.read_bytes())
        data[60:64] = (2).to_bytes(4, "big")
        path.write_bytes(data)
    else:
        connection = sqlite3.connect(path)
        try:
            connection.execute("CREATE TABLE unauthorized (value TEXT)" if control == "extra_table" else "DROP TABLE system_state")
            connection.commit()
        finally:
            connection.close()
    _assert_refusal_without_original_open(path)


def test_closed_companion_free_current_wal_file_reopens(tmp_path: Path) -> None:
    path = tmp_path / "current.db"
    _make_closed_supported_database(path, changed_table=None, defect=None)
    with DemoDatabase(path) as db:
        assert db.conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert db.conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        db.set_system_state("reopened", "current companion-free file")
    assert family_bytes(path)["-wal"] is None
    with DemoDatabase(path) as db:
        assert db.get_system_state("reopened") == "current companion-free file"


def test_zero_byte_companion_free_file_is_fresh(tmp_path: Path) -> None:
    path = tmp_path / "empty.db"
    path.touch()
    with DemoDatabase(path) as db:
        assert db.conn.execute("PRAGMA user_version").fetchone()[0] == 1
