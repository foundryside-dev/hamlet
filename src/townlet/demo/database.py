"""SQLite database for multi-day demo state management."""

import hashlib
import json
import os
import sqlite3
import stat
import tempfile
import threading
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, fields
from functools import wraps
from pathlib import Path
from typing import Any, Concatenate, get_args

from townlet.recording.data_structures import EpisodeMetadata, build_recording_reward_payload
from townlet.recording.receipts import LEGACY_RECORDING_RUN, RecordingPublicationError
from townlet.training.episode import CompletionReason

DEMO_SCHEMA_VERSION = 1
DEMO_FAMILY_SUFFIXES = ("", "-wal", "-shm", "-journal")
RECORDING_BINDING_PREFIX = "townlet.recording-index:"
RECORDING_BINDING_KEY = "townlet.recording-index:v2"
RECORDING_BINDING_TAG = "townlet-recording-index:v2"
RECORDING_INDEX_VERSION = 2
RECORDING_INDEX_DDL = {
    "recording_index_meta": (
        "CREATE TABLE recording_index_meta (singleton INTEGER PRIMARY KEY CHECK(singleton=1), "
        "schema_version INTEGER NOT NULL CHECK(schema_version=2), family_id TEXT NOT NULL UNIQUE, metric_name TEXT NOT NULL)"
    ),
    "recordings": (
        "CREATE TABLE recordings (index_id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, episode_id INTEGER NOT NULL, "
        "lane INTEGER NOT NULL CHECK(lane>=0), sequence INTEGER NOT NULL, generation INTEGER NOT NULL CHECK(generation>=0), "
        "file_path TEXT NOT NULL, file_sha256 TEXT NOT NULL, "
        "frame_count INTEGER NOT NULL, completion_reason TEXT NOT NULL, total_reward REAL NOT NULL, extrinsic_reward REAL NOT NULL, "
        "intrinsic_reward REAL NOT NULL, shaping_reward REAL NOT NULL, final_done INTEGER NOT NULL CHECK(final_done IN(0,1)), "
        "metadata_json TEXT NOT NULL, CHECK((run_id='townlet:legacy-recording:v1' AND lane=0 AND generation>0) "
        "OR (run_id<>'townlet:legacy-recording:v1' AND generation=0)), UNIQUE(run_id,episode_id,lane,generation))"
    ),
}


def _locked[Result, **Parameters](
    method: Callable[Concatenate["DemoDatabase", Parameters], Result],
) -> Callable[Concatenate["DemoDatabase", Parameters], Result]:
    @wraps(method)
    def call(self: "DemoDatabase", /, *args: Parameters.args, **kwargs: Parameters.kwargs) -> Result:
        with self._lock:
            return method(self, *args, **kwargs)

    return call


def _recording_binding(value):
    try:
        binding = json.loads(value)
    except (ValueError, TypeError) as error:
        raise ValueError("Malformed recording-index association") from error
    if not isinstance(binding, dict) or set(binding) != {"tag", "family_id", "index_name"}:
        raise ValueError("Unsupported recording-index association")
    if binding["tag"] != RECORDING_BINDING_TAG:
        raise ValueError("Unsupported recording-index association tag")
    family_id, name = binding["family_id"], binding["index_name"]
    if not isinstance(family_id, str) or len(family_id) != 32 or any(character not in "0123456789abcdef" for character in family_id):
        raise ValueError("Malformed recording-index family identity")
    if not isinstance(name, str) or not name or Path(name).name != name or "\\" in name or not name.endswith(".recordings.sqlite3"):
        raise ValueError("Recording-index association must use a safe relative basename")
    return binding


def _read_recording_binding(path):
    if not path.exists() or path.stat().st_size == 0:
        return None
    with read_existing_demo_snapshot(path, exclusive_custody=True) as connection:
        rows = connection.execute(
            "SELECT key,value FROM system_state WHERE substr(key,1,?)=?", (len(RECORDING_BINDING_PREFIX), RECORDING_BINDING_PREFIX)
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1 or rows[0][0] != RECORDING_BINDING_KEY:
            raise ValueError("Earlier or conflicting recording-index association must be preserved unchanged")
        return _recording_binding(rows[0][1])


def inspect_recording_index(path, binding):
    """Validate the complete stopped index privately before any owner opens it.

    All schema entries are pinned, including SQLite's two implicit UNIQUE
    indexes. Additional triggers, views, tables, columns or internal tables are
    unsupported. Neither recovery nor opportunistic adoption is performed.
    """
    before = demo_family_snapshot(path)
    try:
        if before[0] is None or before[0][2] == 0 or any(member is not None for member in before[1:]):
            raise ValueError("A nonempty stopped companion-free recording index is required")
        data, signature = _read_regular(path)
        if signature != before[0] or len(data) < 100 or data[:16] != b"SQLite format 3\x00":
            raise ValueError("Malformed or changing recording-index family")
        if int.from_bytes(data[60:64], "big") != RECORDING_INDEX_VERSION:
            raise ValueError("Unsupported recording-index schema version")
        with tempfile.TemporaryDirectory(prefix="recording-index-preflight-") as directory:
            private = Path(directory) / "index.db"
            private.write_bytes(data)
            connection = sqlite3.connect(private.as_uri() + "?mode=ro", uri=True)
            try:
                if connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                    raise ValueError("Corrupt recording index")
                expected = sorted(
                    [("table", table, table, ddl) for table, ddl in RECORDING_INDEX_DDL.items()]
                    + [("index", "sqlite_autoindex_" + table + "_1", table, None) for table in RECORDING_INDEX_DDL]
                )
                actual = sorted(connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema").fetchall())
                if actual != expected or connection.execute("PRAGMA user_version").fetchone() != (RECORDING_INDEX_VERSION,):
                    raise ValueError("Unsupported recording-index closed schema")
                rows = connection.execute("SELECT singleton,schema_version,family_id,metric_name FROM recording_index_meta").fetchall()
                if len(rows) != 1 or rows[0][:3] != (1, RECORDING_INDEX_VERSION, binding["family_id"]) or not rows[0][3]:
                    raise ValueError("Recording-index ownership does not match its metric association")
                connection.row_factory = sqlite3.Row
                for row in connection.execute("SELECT * FROM recordings"):
                    _validate_recording_row(dict(row))
            except sqlite3.DatabaseError as error:
                raise ValueError("Malformed recording-index database") from error
            finally:
                connection.close()
    finally:
        if demo_family_snapshot(path) != before:
            raise ValueError("Recording-index family changed during preflight")


def _validate_recording_row(row):
    if not isinstance(row["run_id"], str) or not row["run_id"]:
        raise ValueError("Recording index has an invalid run identity")
    if any(
        type(row[key]) is not int or row[key] < 0 for key in ("index_id", "episode_id", "lane", "sequence", "generation", "frame_count")
    ):
        raise ValueError("Recording index has an invalid integer identity/count")
    if row["run_id"] == LEGACY_RECORDING_RUN:
        if row["lane"] != 0 or row["generation"] <= 0:
            raise ValueError("Legacy recording history requires lane zero and a positive generation")
    elif row["generation"] != 0:
        raise ValueError("Scoped recording history requires generation zero")
    path, digest = row["file_path"], row["file_sha256"]
    if not isinstance(path, str) or not path or ".." in Path(path).parts:
        raise ValueError("Recording index has an unsafe artifact locator")
    if not Path(path).is_absolute():
        raise ValueError("Immutable recording history requires an absolute artifact locator")
    if not isinstance(digest, str) or len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("Recording index has an invalid published artifact digest")
    try:
        metadata = json.loads(row["metadata_json"])
        if not isinstance(metadata, dict) or set(metadata) != {field.name for field in fields(EpisodeMetadata)}:
            raise ValueError("Recording metadata must retain the exact episode schema")
        if metadata["episode_id"] != row["episode_id"] or metadata["survival_steps"] != row["frame_count"]:
            raise ValueError("Recording metadata identity/count differs from its index")
        if metadata["completion_reason"] != row["completion_reason"] or row["completion_reason"] not in get_args(CompletionReason):
            raise ValueError("Recording index has an invalid ending")
        terminal = row["completion_reason"] in ("authored_terminal", "retirement")
        if row["final_done"] != int(terminal):
            raise ValueError("Recording index has an inconsistent final done flag")
        for key in ("total_reward", "extrinsic_reward", "intrinsic_reward", "shaping_reward"):
            if metadata[key] != row[key]:
                raise ValueError("Recording metadata reward differs from its index")
        build_recording_reward_payload(
            total=row["total_reward"], extrinsic=row["extrinsic_reward"], intrinsic=row["intrinsic_reward"], shaping=row["shaping_reward"]
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Malformed immutable recording metadata") from error


Column = tuple[int, str, str, int, str | None, int, int]
Signature = tuple[int, int, int, int, int, str]
DEMO_TABLE_COLUMNS = {
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
DEMO_EXPECTED_COLUMNS: dict[str, tuple[Column, ...]] = {
    table: tuple(
        (cid, name, declaration.split()[0], int("NOT NULL" in declaration), None, int("PRIMARY KEY" in declaration), 0)
        for cid, (name, declaration) in enumerate(columns)
    )
    for table, columns in DEMO_TABLE_COLUMNS.items()
}
DEMO_SCHEMA_DDL = """
            CREATE TABLE episodes (
                episode_id INTEGER PRIMARY KEY,
                timestamp REAL NOT NULL,
                survival_time INTEGER NOT NULL,
                batch_episode_steps INTEGER NOT NULL,
                live_agent_transitions INTEGER NOT NULL,
                completion_reason TEXT NOT NULL,
                total_reward REAL NOT NULL,
                extrinsic_reward REAL NOT NULL,
                intrinsic_reward REAL NOT NULL,
                shaping_reward REAL NOT NULL,
                intrinsic_weight REAL NOT NULL,
                curriculum_stage INTEGER NOT NULL,
                epsilon REAL NOT NULL,
                observation_schema_hash TEXT NOT NULL
            );
            CREATE INDEX idx_episodes_timestamp ON episodes(timestamp);

            CREATE TABLE affordance_visits (
                episode_id INTEGER NOT NULL,
                from_affordance TEXT NOT NULL,
                to_affordance TEXT NOT NULL,
                visit_count INTEGER NOT NULL,
                FOREIGN KEY (episode_id) REFERENCES episodes(episode_id)
            );
            CREATE INDEX idx_visits_episode ON affordance_visits(episode_id);

            CREATE TABLE position_heatmap (
                episode_id INTEGER NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                visit_count INTEGER NOT NULL,
                novelty_value REAL,
                FOREIGN KEY (episode_id) REFERENCES episodes(episode_id)
            );
            CREATE INDEX idx_heatmap_episode ON position_heatmap(episode_id);

            CREATE TABLE system_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE episode_recordings (
                episode_id INTEGER PRIMARY KEY,
                file_path TEXT NOT NULL,
                timestamp REAL NOT NULL,
                survival_steps INTEGER NOT NULL,
                completion_reason TEXT NOT NULL,
                total_reward REAL NOT NULL,
                extrinsic_reward REAL NOT NULL,
                intrinsic_reward REAL NOT NULL,
                shaping_reward REAL NOT NULL,
                curriculum_stage INTEGER NOT NULL,
                epsilon REAL NOT NULL,
                intrinsic_weight REAL NOT NULL,
                recording_reason TEXT NOT NULL,
                file_size_bytes INTEGER,
                compressed_size_bytes INTEGER
            );
            CREATE INDEX idx_recordings_stage ON episode_recordings(curriculum_stage);
            CREATE INDEX idx_recordings_reason ON episode_recordings(recording_reason);
            CREATE INDEX idx_recordings_reward ON episode_recordings(total_reward);
        """


def _read_regular(path: Path) -> tuple[bytes, Signature]:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"Unsupported nonregular artifact: {path.name}")
        data = stream.read()
        after = os.fstat(stream.fileno())

    def fields(value: os.stat_result) -> tuple[int, int, int, int, int]:
        return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns

    if fields(before) != fields(after) or len(data) != after.st_size:
        raise ValueError("Demo artifact changed during read")
    return data, (*fields(after), hashlib.sha256(data).hexdigest())


def demo_family_snapshot(path: Path) -> tuple[Signature | None, ...]:
    """Raw OS reads only; include companion existence and bytes."""
    readings: list[Signature | None] = []
    for suffix in DEMO_FAMILY_SUFFIXES:
        member = Path(str(path) + suffix)
        try:
            _, signature = _read_regular(member)
        except FileNotFoundError:
            readings.append(None)
        else:
            readings.append(signature)
    return tuple(readings)


def inspect_existing_demo_schema(
    path: Path,
    expected_columns: Mapping[str, tuple[Column, ...]],
    *,
    exclusive_custody: bool,
) -> None:
    """Require stopped owners and custody through the following real open.

    Only absent/zero-byte companion-free new files and closed companion-free
    current files are supported. Any WAL/SHM/journal presence is refused, even
    an empty companion. No checkpoint, recovery, migration or original-file
    SQLite open occurs here. Fingerprints detect changes, not atomic snapshots.
    """
    if not exclusive_custody:
        raise ValueError("Exclusive demo artifact custody is required")
    path = path.absolute()
    if any(not table.isidentifier() for table in expected_columns):
        raise ValueError("Invalid internal schema table name")
    before = demo_family_snapshot(path)
    try:
        if any(reading is not None for reading in before[1:]):
            raise ValueError("Existing WAL/SHM/journal family is unsupported; preserve it unchanged")
        if before[0] is None or before[0][2] == 0:
            return
        data, signature = _read_regular(path)
        if signature != before[0]:
            raise ValueError("Demo artifact changed before private validation")
        if len(data) < 100 or data[:16] != b"SQLite format 3\x00":
            raise ValueError("Malformed nonempty demo database header")
        version = int.from_bytes(data[60:64], "big")
        if version != DEMO_SCHEMA_VERSION:
            raise ValueError(f"Unsupported demo schema version: {version}")
        # WAL may exist only in this private directory. No immutable assumption.
        with tempfile.TemporaryDirectory(prefix="demo-schema-preflight-") as directory:
            private_path = Path(directory) / "probe.db"
            private_path.write_bytes(data)
            connection = sqlite3.connect(private_path.as_uri() + "?mode=ro", uri=True)
            try:
                if connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                    raise ValueError("Corrupt demo database")
                if connection.execute("PRAGMA user_version").fetchone() != (DEMO_SCHEMA_VERSION,):
                    raise ValueError("Unsupported demo schema stamp")
                actual_tables = {
                    row[0]
                    for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' AND substr(name, 1, 7) != 'sqlite_'")
                }
                if actual_tables != set(expected_columns):
                    raise ValueError("Unsupported demo table layout")
                for table, columns in expected_columns.items():
                    actual = tuple(connection.execute(f'PRAGMA table_xinfo("{table}")'))
                    if actual != columns:
                        raise ValueError(f"Unsupported demo columns: {table}")
            except sqlite3.DatabaseError as error:
                raise ValueError("Malformed demo database") from error
            finally:
                connection.close()
    finally:
        if demo_family_snapshot(path) != before:
            raise ValueError("Demo artifact family changed during preflight")


@contextmanager
def read_existing_demo_snapshot(path: Path, *, exclusive_custody: bool) -> Iterator[sqlite3.Connection]:
    """Read a validated private copy while retaining the stopped original family.

    The caller must hold exclusive custody throughout the context. Existing,
    nonempty, companion-free current databases are required. SQLite never opens
    the original; final fingerprints detect external changes without repairing
    them. The private connection stays open through downstream reconciliation.
    """
    if not exclusive_custody:
        raise ValueError("Exclusive demo artifact custody is required")
    path = path.absolute()
    before = demo_family_snapshot(path)
    try:
        if before[0] is None:
            raise FileNotFoundError(f"Existing demo database required: {path}")
        if before[0][2] == 0:
            raise ValueError("Existing nonempty demo database required")
        inspect_existing_demo_schema(path, DEMO_EXPECTED_COLUMNS, exclusive_custody=True)
        data, signature = _read_regular(path)
        if signature != before[0] or demo_family_snapshot(path) != before:
            raise ValueError("Demo artifact family changed before private read")
        with tempfile.TemporaryDirectory(prefix="demo-accounting-read-") as directory:
            private_path = Path(directory) / "snapshot.db"
            private_path.write_bytes(data)
            connection = sqlite3.connect(private_path.as_uri() + "?mode=ro", uri=True)
            try:
                yield connection
            finally:
                connection.close()
    finally:
        if demo_family_snapshot(path) != before:
            raise ValueError("Demo artifact family changed during private read")


class DemoDatabase:
    """Manages SQLite database for demo metrics and state.

    Opening requires exclusive caller custody of a stopped, companion-free family.
    Current files reopen after normal owner closure; pending or incompatible files
    are refused unchanged. The admitted connection may serve its recording writer
    thread, but multiple DemoDatabase owners for the same family are unsupported.
    """

    def __init__(self, db_path: Path | str):
        """Initialize database, creating schema if needed.

        Args:
            db_path: Path to SQLite database file
        """
        self._lock = threading.RLock()
        self._closed = True
        self._close_errors = ()
        self._index_conn = None
        self._association = None
        self._index_pending = False
        self._index_sync_pending = False
        self._publication_stack: list[tuple[str, int, int, int]] = []
        self.db_path = Path(db_path)
        self._index_path = self.db_path.with_name(self.db_path.name + ".recordings.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Caller owns a stopped family exclusively through inspection and actual reopen.
        inspect_existing_demo_schema(self.db_path, DEMO_EXPECTED_COLUMNS, exclusive_custody=True)
        self._association = _read_recording_binding(self.db_path)
        if self._association is not None:
            self._index_path = self.db_path.parent / self._association["index_name"]
            inspect_recording_index(self._index_path, self._association)
        elif any(member is not None for member in demo_family_snapshot(self._index_path)):
            raise ValueError("Unexpected unassociated recording-index family; preserve it unchanged")

        # Enable WAL mode for this admitted current database
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._closed = False  # Track closed state for idempotency
        try:
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=FULL")
            self.conn.row_factory = sqlite3.Row
            if self.conn.execute("PRAGMA user_version").fetchone()[0] != DEMO_SCHEMA_VERSION:
                self._create_schema()
            if self._association is not None:
                self._index_conn = sqlite3.connect(self._index_path, check_same_thread=False)
                self._index_conn.execute("PRAGMA journal_mode=WAL")
                self._index_conn.execute("PRAGMA synchronous=FULL")
                self._index_conn.row_factory = sqlite3.Row
                # A stopped valid file does not attest that a previous owner's
                # explicit directory sync succeeded before its failed close.
                self._index_sync_pending = True
                self._sync_recording_index_directory()
        except BaseException:
            self.close()
            raise

    def _ensure_open(self):
        """Ensure database connection is open.

        Raises:
            RuntimeError: If database connection is closed
        """
        if self._closed:
            raise RuntimeError(
                "Database connection is closed. Cannot perform database operations "
                "after close() has been called. Create a new DemoDatabase instance."
            )

    def _create_schema(self):
        """Create and stamp the fresh schema in one transaction."""
        self.conn.executescript("BEGIN IMMEDIATE;" + DEMO_SCHEMA_DDL + f"PRAGMA user_version={DEMO_SCHEMA_VERSION}; COMMIT;")

    @_locked
    def insert_episode(
        self,
        episode_id: int,
        timestamp: float,
        survival_time: int,
        batch_episode_steps: int,
        live_agent_transitions: int,
        completion_reason: CompletionReason,
        total_reward: float,
        extrinsic_reward: float,
        intrinsic_reward: float,
        shaping_reward: float,
        intrinsic_weight: float,
        curriculum_stage: int,
        epsilon: float,
        observation_schema_hash: str,
    ):
        """Insert episode metrics into database.

        Args:
            episode_id: Episode number
            timestamp: Unix timestamp
            survival_time: Eligible slot-zero transitions
            batch_episode_steps: Vector ticks in this batch
            live_agent_transitions: Eligible transitions across all lanes
            completion_reason: Frozen slot-zero completion reason
            total_reward: Combined reward
            extrinsic_reward: Environment reward
            intrinsic_reward: Effective canonical DAC contributor
            shaping_reward: Canonical DAC shaping contributor
            intrinsic_weight: Current intrinsic weight
            curriculum_stage: Current curriculum stage (1-5)
            epsilon: Current exploration epsilon
            observation_schema_hash: Compiled observation ABI hash for this run

        Raises:
            RuntimeError: If database connection is closed
        """
        self._ensure_open()
        if completion_reason not in get_args(CompletionReason):
            raise ValueError("Unsupported episode completion reason")
        build_recording_reward_payload(total=total_reward, extrinsic=extrinsic_reward, intrinsic=intrinsic_reward, shaping=shaping_reward)
        self.conn.execute(
            """INSERT OR REPLACE INTO episodes
               (episode_id, timestamp, survival_time, batch_episode_steps, live_agent_transitions, completion_reason,
                total_reward, extrinsic_reward,
                intrinsic_reward, shaping_reward, intrinsic_weight, curriculum_stage, epsilon, observation_schema_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                episode_id,
                timestamp,
                survival_time,
                batch_episode_steps,
                live_agent_transitions,
                completion_reason,
                total_reward,
                extrinsic_reward,
                intrinsic_reward,
                shaping_reward,
                intrinsic_weight,
                curriculum_stage,
                epsilon,
                observation_schema_hash,
            ),
        )
        self.conn.commit()

    @_locked
    def get_latest_episodes(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get most recent episodes.

        Args:
            limit: Maximum number of episodes to return

        Returns:
            List of episode dictionaries

        Raises:
            RuntimeError: If database connection is closed
        """
        self._ensure_open()
        cursor = self.conn.execute("SELECT * FROM episodes ORDER BY episode_id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    @_locked
    def set_system_state(self, key: str, value: str):
        """Set system state key-value pair.

        Args:
            key: State key
            value: State value (will be converted to string)

        Raises:
            RuntimeError: If database connection is closed
        """
        self._ensure_open()
        if key.startswith(RECORDING_BINDING_PREFIX):
            raise ValueError("Recording-index ownership metadata is reserved")
        self.conn.execute("INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

    @_locked
    def get_system_state(self, key: str) -> str | None:
        """Get system state value.

        Args:
            key: State key

        Returns:
            State value or None if not found

        Raises:
            RuntimeError: If database connection is closed
        """
        self._ensure_open()
        cursor = self.conn.execute("SELECT value FROM system_state WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else None

    @_locked
    def insert_affordance_visits(self, episode_id: int, transitions: dict[str, dict[str, int]]):
        """Insert affordance transition counts for an episode.

        Args:
            episode_id: Episode number
            transitions: Dict mapping from_affordance -> {to_affordance: count}

        Example:
            transitions = {
                "Bed": {"Hospital": 3, "Job": 1},
                "Hospital": {"Bed": 2}
            }
            # Inserts 3 rows:
            #   (episode_id, "Bed", "Hospital", 3)
            #   (episode_id, "Bed", "Job", 1)
            #   (episode_id, "Hospital", "Bed", 2)

        Raises:
            RuntimeError: If database connection is closed
        """
        self._ensure_open()
        if not transitions:
            return  # No transitions to insert (empty episode)

        rows = []
        for from_aff, to_affs in transitions.items():
            for to_aff, count in to_affs.items():
                rows.append((episode_id, from_aff, to_aff, count))

        self.conn.executemany(
            "INSERT INTO affordance_visits (episode_id, from_affordance, to_affordance, visit_count) VALUES (?, ?, ?, ?)", rows
        )
        self.conn.commit()

    def insert_position_heatmap(
        self,
        episode_id: int,
        positions: dict[tuple[int, int], int],
        novelty: dict[tuple[int, int], float] | None = None,
    ):
        """Insert position visit counts and novelty values for an episode.

        Args:
            episode_id: Episode number
            positions: Dict mapping (x, y) -> visit_count
            novelty: Optional dict mapping (x, y) -> novelty_value

        TODO: Implement in Task 5 for visualization
        """
        pass

    def get_position_heatmap(self, episode_id: int) -> list[dict[str, Any]]:
        """Get position heatmap data for an episode.

        Args:
            episode_id: Episode number

        Returns:
            List of position heatmap rows

        TODO: Implement in Task 5 for visualization
        """
        raise NotImplementedError("Position heatmap retrieval will be implemented in Task 5.")

    @_locked
    def insert_recording(
        self,
        episode_id: int,
        file_path: str,
        metadata,  # EpisodeMetadata type hint would require import
        reason: str,
        file_size: int,
        compressed_size: int,
    ):
        """Insert recording metadata into database.

        Args:
            episode_id: Episode number
            file_path: Path to recording file
            metadata: EpisodeMetadata instance
            reason: Recording reason (e.g., 'periodic', 'stage_transition')
            file_size: Uncompressed file size in bytes
            compressed_size: Compressed file size in bytes

        Raises:
            RuntimeError: If database connection is closed
        """
        self._ensure_open()
        self.conn.execute(
            """INSERT OR REPLACE INTO episode_recordings
               (episode_id, file_path, timestamp, survival_steps, completion_reason, total_reward,
                extrinsic_reward, intrinsic_reward, shaping_reward, curriculum_stage, epsilon,
                intrinsic_weight, recording_reason, file_size_bytes, compressed_size_bytes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                episode_id,
                file_path,
                metadata.timestamp,
                metadata.survival_steps,
                metadata.completion_reason,
                metadata.total_reward,
                metadata.extrinsic_reward,
                metadata.intrinsic_reward,
                metadata.shaping_reward,
                metadata.curriculum_stage,
                metadata.epsilon,
                metadata.intrinsic_weight,
                reason,
                file_size,
                compressed_size,
            ),
        )
        self.conn.commit()

    @_locked
    def get_recording(self, episode_id: int) -> dict[str, Any] | None:
        """Get recording metadata by episode_id.

        Args:
            episode_id: Episode number

        Returns:
            Recording metadata dict or None if not found

        Raises:
            RuntimeError: If database connection is closed
        """
        self._ensure_open()
        cursor = self.conn.execute(
            "SELECT * FROM episode_recordings WHERE episode_id = ?",
            (episode_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    @_locked
    def list_recordings(
        self,
        stage: int | None = None,
        reason: str | None = None,
        min_reward: float | None = None,
        max_reward: float | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List recordings with optional filters.

        Args:
            stage: Filter by curriculum stage
            reason: Filter by recording reason
            min_reward: Filter by minimum total reward
            max_reward: Filter by maximum total reward
            limit: Maximum number of recordings to return

        Returns:
            List of recording metadata dicts, ordered by episode_id DESC

        Raises:
            RuntimeError: If database connection is closed
        """
        self._ensure_open()
        query = "SELECT * FROM episode_recordings WHERE 1=1"
        params: list[int | str | float] = []

        if stage is not None:
            query += " AND curriculum_stage = ?"
            params.append(stage)

        if reason is not None:
            query += " AND recording_reason = ?"
            params.append(reason)

        if min_reward is not None:
            query += " AND total_reward >= ?"
            params.append(min_reward)

        if max_reward is not None:
            query += " AND total_reward <= ?"
            params.append(max_reward)

        query += " ORDER BY episode_id DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    @property
    def owned_family_paths(self):
        with self._lock:
            return (self.db_path, self._index_path) if self._association is not None or self._index_pending else (self.db_path,)

    @_locked
    def checkpoint_owned_families(self):
        """Expose only a complete, closed and independently validated family set."""
        if not self._closed or self._close_errors or self._index_pending or self._index_sync_pending:
            raise RuntimeError("A complete recording-family checkpoint requires successful drain/close and coherent ownership")
        inspect_existing_demo_schema(self.db_path, DEMO_EXPECTED_COLUMNS, exclusive_custody=True)
        binding = _read_recording_binding(self.db_path)
        if binding != self._association:
            raise ValueError("Recording-index association changed after owner closure")
        if binding is not None:
            inspect_recording_index(self._index_path, binding)
        elif any(member is not None for member in demo_family_snapshot(self._index_path)):
            raise ValueError("Unexpected recording-index family prevents a complete checkpoint")
        return self.owned_family_paths

    def _ensure_recording_index(self):
        self._ensure_open()
        if self._index_pending:
            raise RuntimeError("An incomplete recording-index association requires explicit reconciliation")
        if self._index_conn is not None:
            self._assert_recording_binding(self._association)
            self._sync_recording_index_directory()
            return self._index_conn
        if self.conn.in_transaction:
            raise RuntimeError("Cannot associate recording storage during a pending metric transaction")
        if (
            self.conn.execute(
                "SELECT key FROM system_state WHERE substr(key,1,?)=?", (len(RECORDING_BINDING_PREFIX), RECORDING_BINDING_PREFIX)
            ).fetchone()
            is not None
        ):
            raise ValueError("Unexpected reserved recording-index association; refusing replacement")
        if any(member is not None for member in demo_family_snapshot(self._index_path)):
            raise ValueError("Refusing to adopt or overwrite an unassociated recording-index family")
        binding = {"tag": RECORDING_BINDING_TAG, "family_id": uuid.uuid4().hex, "index_name": self._index_path.name}
        _recording_binding(json.dumps(binding))
        descriptor = os.open(self._index_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
        self._index_pending = True
        self._index_sync_pending = True
        connection = sqlite3.connect(self._index_path, check_same_thread=False)
        self._index_conn = connection
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.row_factory = sqlite3.Row
            connection.executescript("BEGIN IMMEDIATE;" + ";".join(RECORDING_INDEX_DDL.values()) + ";")
            connection.execute(
                "INSERT INTO recording_index_meta VALUES (1,?,?,?)", (RECORDING_INDEX_VERSION, binding["family_id"], self.db_path.name)
            )
            connection.execute(f"PRAGMA user_version={RECORDING_INDEX_VERSION}")
            connection.commit()
            self.conn.execute(
                "INSERT INTO system_state (key,value) VALUES (?,?)",
                (RECORDING_BINDING_KEY, json.dumps(binding, sort_keys=True, separators=(",", ":"))),
            )
            self.conn.commit()
            committed_binding = self.conn.execute("SELECT value FROM system_state WHERE key=?", (RECORDING_BINDING_KEY,)).fetchone()
            if committed_binding is None or _recording_binding(committed_binding[0]) != binding:
                raise RuntimeError("Committed recording-index association differs from its owned family binding")
        except BaseException:
            connection.rollback()
            self.conn.rollback()
            raise
        self._association = binding
        self._index_pending = False
        self._sync_recording_index_directory()
        return connection

    def _sync_recording_index_directory(self):
        if not self._index_sync_pending:
            return
        # Persist both newly created directory entries as well as SQLite commits.
        # Re-establish the whole physical namespace on fresh owner admission;
        # neither directory existence nor reset memory flags prove durability.
        directory = self._index_path.parent.resolve()
        while True:
            descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            parent = directory.parent
            if parent == directory:
                break
            directory = parent
        self._index_sync_pending = False

    def _assert_recording_binding(self, expected):
        rows = self.conn.execute(
            "SELECT key,value FROM system_state WHERE substr(key,1,?)=?", (len(RECORDING_BINDING_PREFIX), RECORDING_BINDING_PREFIX)
        ).fetchall()
        try:
            if len(rows) != 1 or rows[0][0] != RECORDING_BINDING_KEY or _recording_binding(rows[0][1]) != expected:
                raise ValueError("Committed recording-index ownership differs from its admitted association")
        except Exception:
            self._index_pending = True
            raise

    @contextmanager
    def recording_publication(self, *, run_id: str, episode_id: int, lane: int, legacy: bool) -> Iterator[int]:
        with self._lock:
            try:
                if not isinstance(run_id, str) or not run_id or type(episode_id) is not int or episode_id < 0:
                    raise ValueError("Recording publication requires exact run and episode identity")
                if type(lane) is not int or lane < 0 or type(legacy) is not bool or legacy != (run_id == LEGACY_RECORDING_RUN):
                    raise ValueError("Recording publication requires a valid lane and visibility role")
                if legacy and lane != 0:
                    raise ValueError("Legacy publication requires lane zero")
                connection = self._ensure_recording_index()
                if legacy:
                    maximum = connection.execute(
                        "SELECT MAX(generation) FROM recordings WHERE run_id=? AND episode_id=? AND lane=?", (run_id, episode_id, lane)
                    ).fetchone()[0]
                    generation = 1
                    if maximum is not None:
                        generation = maximum + 1
                else:
                    generation = 0
                    if (
                        connection.execute(
                            "SELECT index_id FROM recordings WHERE run_id=? AND episode_id=? AND lane=?", (run_id, episode_id, lane)
                        ).fetchone()
                        is not None
                    ):
                        raise ValueError("Scoped recording identity already has an immutable publication")
            except Exception as error:
                phase = "admission"
                if self._index_sync_pending and not self._index_pending:
                    phase = "durability"
                raise RecordingPublicationError(
                    phase=phase,
                    cause=error,
                    path=None,
                    legacy_alias_path=None,
                    generation=None,
                    index_id=None,
                    alias_state="not_attempted",
                    canonical_state="not_attempted",
                    index_state="not_attempted",
                ) from error
            self._publication_stack.append((run_id, episode_id, lane, generation))
            try:
                yield generation
                self._assert_recording_binding(self._association)
            finally:
                self._publication_stack.pop()

    @_locked
    def insert_scoped_recording(
        self,
        *,
        run_id,
        lane,
        sequence,
        generation,
        file_path,
        legacy_file_path,
        file_sha256,
        frame_count,
        final_done,
        metadata,
        legacy,
        reason,
        file_size,
        compressed_size,
    ):
        """Commit a qualified immutable row; legacy capture also retains its old index.

        Two SQLite families cannot promise cross-file WAL atomicity. Success is
        returned only after both required commits and readback. Any partial
        commit is an explicit recorder failure whose run/ticket/path remain
        available for reconciliation; it is never downgraded to file-only.
        """
        self._ensure_open()
        if type(legacy) is not bool or legacy != (run_id == LEGACY_RECORDING_RUN) or (legacy and lane != 0):
            raise ValueError("Recording scope does not match its legacy visibility role")
        row = {
            "index_id": 0,
            "run_id": run_id,
            "episode_id": metadata.episode_id,
            "lane": lane,
            "sequence": sequence,
            "generation": generation,
            "file_path": file_path,
            "file_sha256": file_sha256,
            "frame_count": frame_count,
            "completion_reason": metadata.completion_reason,
            "total_reward": metadata.total_reward,
            "extrinsic_reward": metadata.extrinsic_reward,
            "intrinsic_reward": metadata.intrinsic_reward,
            "shaping_reward": metadata.shaping_reward,
            "final_done": int(final_done),
            "metadata_json": json.dumps(asdict(metadata), sort_keys=True, separators=(",", ":"), allow_nan=False),
        }
        _validate_recording_row(row)
        if legacy:
            if (
                not isinstance(legacy_file_path, str)
                or not legacy_file_path
                or Path(legacy_file_path).is_absolute()
                or ".." in Path(legacy_file_path).parts
            ):
                raise ValueError("Legacy publication requires its explicit original relative alias locator")
        elif legacy_file_path is not None:
            raise ValueError("Scoped publication cannot supply a legacy alias locator")
        if self.conn.in_transaction:
            raise RuntimeError("Recording commit cannot take ownership of a pending metric transaction")
        connection = self._ensure_recording_index()
        identity = (run_id, metadata.episode_id, lane, generation)
        if self._publication_stack and self._publication_stack[-1] != identity:
            raise ValueError("Recording insertion differs from its enclosing publication context")
        if legacy:
            maximum = connection.execute(
                "SELECT MAX(generation) FROM recordings WHERE run_id=? AND episode_id=? AND lane=?", (run_id, metadata.episode_id, lane)
            ).fetchone()[0]
            expected_generation = 1
            if maximum is not None:
                expected_generation = maximum + 1
            if generation != expected_generation:
                raise ValueError("Legacy generation differs from the next committed history generation")
        columns = tuple(key for key in row if key != "index_id")
        legacy_row = None
        phase = "canonical"
        canonical_state = index_state = "not_attempted"
        index_id = None
        try:
            if legacy:
                canonical_state = "unconfirmed"
                legacy_row = {
                    "episode_id": metadata.episode_id,
                    "file_path": legacy_file_path,
                    "timestamp": metadata.timestamp,
                    "survival_steps": metadata.survival_steps,
                    "completion_reason": metadata.completion_reason,
                    "total_reward": metadata.total_reward,
                    "extrinsic_reward": metadata.extrinsic_reward,
                    "intrinsic_reward": metadata.intrinsic_reward,
                    "shaping_reward": metadata.shaping_reward,
                    "curriculum_stage": metadata.curriculum_stage,
                    "epsilon": metadata.epsilon,
                    "intrinsic_weight": metadata.intrinsic_weight,
                    "recording_reason": reason,
                    "file_size_bytes": file_size,
                    "compressed_size_bytes": compressed_size,
                }
                self.conn.execute(
                    f"INSERT OR REPLACE INTO episode_recordings ({','.join(legacy_row)}) VALUES ({','.join('?' for _ in legacy_row)})",
                    tuple(legacy_row.values()),
                )
                self.conn.commit()
                canonical = self.conn.execute("SELECT * FROM episode_recordings WHERE episode_id=?", (metadata.episode_id,)).fetchone()
                if canonical is None or dict(canonical) != legacy_row:
                    raise RuntimeError("Committed canonical recording readback differs from publication metadata")
                canonical_state = "confirmed"
            phase, index_state = "index", "unconfirmed"
            cursor = connection.execute(
                f"INSERT INTO recordings ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                tuple(row[key] for key in columns),
            )
            index_id = cursor.lastrowid
            connection.commit()
            actual = connection.execute("SELECT * FROM recordings WHERE index_id=?", (index_id,)).fetchone()
            row["index_id"] = index_id
            if actual is None or dict(actual) != row:
                raise RuntimeError("Committed recording-index readback differs from publication metadata")
            index_state = "confirmed"
            phase = "reconciliation"
            self._assert_recording_binding(self._association)
        except Exception as error:
            causes = [error]
            for owner in (connection, self.conn):
                try:
                    owner.rollback()
                except Exception as cleanup:
                    causes.append(cleanup)
            cause = error
            if len(causes) > 1:
                cause = ExceptionGroup("Recording transaction and cleanup failed", causes)
            raise RecordingPublicationError(
                phase=phase,
                cause=cause,
                path=Path(file_path),
                legacy_alias_path=None,
                generation=generation,
                index_id=index_id,
                alias_state="not_attempted",
                canonical_state=canonical_state,
                index_state=index_state,
            ) from error
        return index_id

    @_locked
    def get_scoped_recording(self, *, run_id, episode_id, lane):
        self._ensure_open()
        if self._index_conn is None:
            return None
        row = self._index_conn.execute(
            "SELECT * FROM recordings WHERE run_id=? AND episode_id=? AND lane=? ORDER BY generation DESC,index_id DESC LIMIT 1",
            (run_id, episode_id, lane),
        ).fetchone()
        return None if row is None else dict(row)

    @_locked
    def list_scoped_recordings(self, *, run_id, lane):
        self._ensure_open()
        if self._index_conn is None:
            return []
        return [
            dict(row)
            for row in self._index_conn.execute(
                "SELECT * FROM recordings WHERE run_id=? AND lane=? ORDER BY episode_id,generation,index_id", (run_id, lane)
            )
        ]

    @_locked
    def get_scoped_recording_by_index(self, *, index_id: int) -> dict[str, Any] | None:
        self._ensure_open()
        if type(index_id) is not int or index_id <= 0:
            raise ValueError("Recording history lookup requires an integer index ID")
        if self._index_conn is None:
            return None
        row = self._index_conn.execute("SELECT * FROM recordings WHERE index_id=?", (index_id,)).fetchone()
        if row is None:
            return None
        return dict(row)

    @_locked
    def close(self):
        """Attempt both owned closes; a failed close never permits a checkpoint."""
        if self._closed:
            if self._close_errors:
                raise self._close_errors[0]
            return
        errors = []
        for connection in (self._index_conn, self.conn):
            if connection is None:
                continue
            try:
                if connection.in_transaction:
                    connection.rollback()
                if connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] != 0:
                    raise RuntimeError("Owned SQLite family remained busy during close")
            except Exception as error:
                errors.append(error)
            finally:
                try:
                    connection.close()
                except Exception as error:
                    errors.append(error)
        self._closed = True
        self._close_errors = tuple(errors)
        if errors:
            raise errors[0]

    def __enter__(self):
        """Context manager entry - returns self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures database is closed."""
        self.close()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Destructor - ensures database is closed during garbage collection."""
        try:
            self.close()
        except Exception:
            # Explicit close/checkpoint retains and reports failures to its owner.
            pass
