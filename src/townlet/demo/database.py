"""SQLite database for multi-day demo state management."""

import hashlib
import os
import sqlite3
import stat
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, get_args

from townlet.recording.data_structures import build_recording_reward_payload
from townlet.training.episode import CompletionReason

DEMO_SCHEMA_VERSION = 1
DEMO_FAMILY_SUFFIXES = ("", "-wal", "-shm", "-journal")
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
        self._closed = True
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Caller owns a stopped family exclusively through inspection and actual reopen.
        inspect_existing_demo_schema(self.db_path, DEMO_EXPECTED_COLUMNS, exclusive_custody=True)

        # Enable WAL mode for this admitted current database
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.row_factory = sqlite3.Row

        self._closed = False  # Track closed state for idempotency

        if self.conn.execute("PRAGMA user_version").fetchone()[0] != DEMO_SCHEMA_VERSION:
            try:
                self._create_schema()
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

    def set_system_state(self, key: str, value: str):
        """Set system state key-value pair.

        Args:
            key: State key
            value: State value (will be converted to string)

        Raises:
            RuntimeError: If database connection is closed
        """
        self._ensure_open()
        self.conn.execute("INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

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

    def close(self):
        """Close database connection.

        Safe to call multiple times (idempotent).
        """
        if self._closed:
            return  # Already closed, safe to call again

        self.conn.close()
        self._closed = True

    def __enter__(self):
        """Context manager entry - returns self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures database is closed."""
        self.close()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Destructor - ensures database is closed during garbage collection."""
        self.close()
