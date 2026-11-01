"""Real recording durability across immediate close and writer failures.

Thread barriers control scheduling only: the recorder, writer, filesystem,
compression, validator, and SQLite operations remain real.
"""

import hashlib
import json
import os
import queue
import sqlite3
import stat
import subprocess
import sys
import threading
from contextlib import closing, contextmanager
from dataclasses import replace
from pathlib import Path

import lz4.frame
import msgpack
import pytest
import torch

from townlet.demo.database import DemoDatabase
from townlet.recording.recorder import EpisodeMetadata, EpisodeRecorder, RecordingWriter


def _invoke(call, results, errors):
    try:
        results.append(call())
    except Exception as error:
        errors.append(error)


def _cause(error):
    while hasattr(error, "cause"):
        error = error.cause
    return error


class _Harness:
    def __init__(self, directory, monkeypatch, capacity, interval):
        self.release = threading.Event()
        self.entered = threading.Event()
        self.write_finished = threading.Event()
        self.stop_returned = threading.Event()
        self.loop_errors = []
        original_loop = RecordingWriter.writer_loop
        original_write = RecordingWriter._write_episode
        original_stop = RecordingWriter.stop

        def gated_loop(writer):
            self.entered.set()
            try:
                assert self.release.wait(5), "Test did not release real writer"
                original_loop(writer)
            except Exception as error:
                # An uncaught writer error is evidence, never a successful receipt.
                self.loop_errors.append(error)

        def observed_write(writer, metadata):
            try:
                return original_write(writer, metadata)
            finally:
                self.write_finished.set()

        def observed_stop(writer):
            try:
                return original_stop(writer)
            finally:
                self.stop_returned.set()

        monkeypatch.setattr(RecordingWriter, "writer_loop", gated_loop)
        monkeypatch.setattr(RecordingWriter, "_write_episode", observed_write)
        monkeypatch.setattr(RecordingWriter, "stop", observed_stop)
        self.database = DemoDatabase(directory / "demo.db")
        self.output = directory / "recordings"
        self.config = {
            "max_queue_size": capacity,
            "compression": "lz4",
            "criteria": {"periodic": {"enabled": True, "interval": interval}},
        }
        self.recorder = EpisodeRecorder(self.config, self.output, self.database, None)
        assert self.entered.wait(5), "Real recording writer did not start"

    def close_while_paused(self):
        results, errors = [], []
        closer = threading.Thread(target=_invoke, args=(self.recorder.shutdown, results, errors), daemon=True)
        closer.start()
        try:
            assert self.stop_returned.wait(5), "Shutdown did not reach real writer stop"
        finally:
            self.release.set()
            closer.join(5)
        assert not closer.is_alive(), "Shutdown failed to resolve the closed accepted set"
        assert not self.recorder.writer_thread.is_alive(), "Shutdown left a recording writer alive"
        return results, errors

    def close_running(self):
        self.release.set()
        results, errors = [], []
        _invoke(self.recorder.shutdown, results, errors)
        assert not self.recorder.writer_thread.is_alive()
        return results, errors

    def cleanup(self):
        self.release.set()
        _invoke(self.recorder.shutdown, [], [])
        self.recorder.writer_thread.join(5)
        self.database.close()


@pytest.fixture
def harness_factory(tmp_path, monkeypatch):
    harnesses = []

    def create(capacity, interval):
        harness = _Harness(tmp_path, monkeypatch, capacity, interval)
        harnesses.append(harness)
        return harness

    yield create
    for harness in harnesses:
        harness.cleanup()


def _step(recorder, step, done):
    return recorder.record_step(**_capture_args(step, done))


def _capture_args(step, done):
    return dict(
        step=step,
        positions=torch.tensor([step, 0]),
        meters=torch.tensor([0.5] * 8),
        action=0,
        reward=1.0,
        extrinsic_reward=0.5,
        intrinsic_reward=0.25,
        shaping_reward=0.25,
        done=done,
        q_values=None,
        epsilon=0.1,
        action_masks=torch.ones(6, dtype=torch.bool),
        time_of_day=None,
        interaction_progress=None,
    )


def _metadata(episode):
    return EpisodeMetadata(
        episode_id=episode,
        survival_steps=2,
        completion_reason="cap",
        total_reward=2.0,
        extrinsic_reward=1.0,
        intrinsic_reward=0.5,
        shaping_reward=0.5,
        curriculum_stage=0,
        epsilon=0.1,
        intrinsic_weight=1.0,
        timestamp=1.0,
        affordance_layout={},
        affordance_visits={},
        custom_action_uses={},
    )


def _assert_persisted(harness, episode):
    files = [path for path in harness.output.rglob("*.msgpack.lz4") if path.parent != harness.output]
    assert len(files) == 1, "Shutdown discarded a selected recording instead of publishing it"
    decoded = msgpack.unpackb(lz4.frame.decompress(files[0].read_bytes()), raw=False)
    assert decoded["metadata"]["episode_id"] == episode
    assert len(decoded["steps"]) == 2
    assert [step["step"] for step in decoded["steps"]] == [0, 1]
    assert [step["done"] for step in decoded["steps"]] == [False, False]
    assert decoded["metadata"]["completion_reason"] == "cap"
    assert decoded["metadata"]["survival_steps"] == 2
    assert [step["reward"] for step in decoded["steps"]] == [1.0, 1.0]
    assert decoded["metadata"]["total_reward"] == 2.0
    assert decoded["metadata"]["extrinsic_reward"] == 1.0
    assert decoded["metadata"]["intrinsic_reward"] == 0.5
    assert decoded["metadata"]["shaping_reward"] == 0.5
    row = harness.database.get_recording(episode)
    assert row is not None, "A recording file alone is not an indexed recording"
    assert row["episode_id"] == episode
    alias = harness.output / f"episode_{episode:06d}.msgpack.lz4"
    assert (harness.output.parent / row["file_path"]).resolve() == alias.resolve() and alias.read_bytes() == files[0].read_bytes()
    assert tuple(row[key] for key in ("total_reward", "extrinsic_reward", "intrinsic_reward", "shaping_reward")) == (2.0, 1.0, 0.5, 0.5)
    assert not harness.loop_errors
    return files[0]


def _assert_receipt(harness, ticket, results, errors, status):
    assert not errors, errors
    assert len(results) == 1 and isinstance(results[0], tuple), "Shutdown must return immutable resolved receipts"
    assert len(results[0]) == 1
    receipt = results[0][0]
    assert ticket is not None, "Successful episode admission did not return its ticket"
    assert receipt.ticket == ticket
    assert ticket.episode == 7 and ticket.lane == 0
    assert isinstance(ticket.sequence, int) and ticket.sequence >= 0
    assert receipt.status == status
    assert receipt.storage_mode == "indexed"
    assert harness.recorder.queue.unfinished_tasks == 0, "Accepted queue work remains unresolved"
    return receipt


def test_naturally_timed_recording_control(harness_factory):
    harness = harness_factory(16, 7)
    _step(harness.recorder, 0, False)
    _step(harness.recorder, 1, False)
    harness.recorder.finish_episode(_metadata(7))
    harness.release.set()
    assert harness.write_finished.wait(5), "Real selected recording never reached publication"
    _, errors = harness.close_running()
    assert not errors
    _assert_persisted(harness, 7)
    with closing(sqlite3.connect(harness.database.db_path)) as independent_reader:
        assert independent_reader.execute("SELECT episode_id, survival_steps, total_reward FROM episode_recordings").fetchall() == [
            (7, 2, 2.0)
        ]


def test_immediate_shutdown_drains_selected_episode(harness_factory):
    harness = harness_factory(16, 7)
    _step(harness.recorder, 0, False)
    _step(harness.recorder, 1, False)
    ticket = harness.recorder.finish_episode(_metadata(7))
    results, errors = harness.close_while_paused()
    file_path = _assert_persisted(harness, 7)
    receipt = _assert_receipt(harness, ticket, results, errors, "persisted")
    assert Path(receipt.path).resolve() == file_path.resolve()
    assert receipt.index_id is not None and receipt.error is None
    index = harness.database.db_path.with_name(harness.database.db_path.name + ".recordings.sqlite3")
    with closing(sqlite3.connect(index.as_uri() + "?mode=ro", uri=True)) as independent_reader:
        assert independent_reader.execute("SELECT episode_id, lane, frame_count FROM recordings").fetchall() == [(7, 0, 2)]
    published = file_path.read_bytes()
    assert harness.recorder.shutdown() == results[0]
    assert file_path.read_bytes() == published
    _assert_persisted(harness, 7)


def test_shutdown_fences_concurrent_acceptance(harness_factory, monkeypatch):
    harness = harness_factory(16, 7)
    recorder = harness.recorder
    _step(recorder, 0, False)
    _step(recorder, 1, False)
    producer_entered, release_producer, close_entered = (threading.Event() for _ in range(3))
    original_put = recorder.queue.put_nowait

    def held_put(item):
        producer_entered.set()
        assert release_producer.wait(5), "Test did not release episode admission"
        return original_put(item)

    monkeypatch.setattr(recorder.queue, "put_nowait", held_put)
    admitted, producer_errors, closed, close_errors = [], [], [], []
    producer = threading.Thread(
        target=_invoke, args=(lambda: recorder.finish_episode(_metadata(7)), admitted, producer_errors), daemon=True
    )
    producer.start()
    assert producer_entered.wait(5)

    def close():
        close_entered.set()
        return recorder.shutdown()

    closer = threading.Thread(target=_invoke, args=(close, closed, close_errors), daemon=True)
    closer.start()
    try:
        assert close_entered.wait(5)
        release_producer.set()
        producer.join(5)
        assert not producer.is_alive() and not producer_errors
        assert harness.stop_returned.wait(5)
        late_results, late_errors = [], []
        late_producer = threading.Thread(target=_invoke, args=(lambda: _step(recorder, 2, False), late_results, late_errors), daemon=True)
        late_producer.start()
        late_producer.join(5)
    finally:
        release_producer.set()
        harness.release.set()
        producer.join(5)
        closer.join(5)
    assert not closer.is_alive() and not recorder.writer_thread.is_alive()
    late_producer.join(5)
    assert not late_producer.is_alive(), "Admission blocked behind shutdown's writer join"
    _assert_persisted(harness, 7)
    _assert_receipt(harness, admitted[0], closed, close_errors, "persisted")
    assert not late_results and late_errors, "Recording admission succeeded after shutdown's acceptance fence"
    assert all(isinstance(error, (RuntimeError, ValueError)) for error in late_errors)


@pytest.mark.parametrize("failure", ("file", "sql", "full", "incomplete"))
def test_writer_failure_propagates(harness_factory, monkeypatch, failure):
    harness = harness_factory(2 if failure == "full" else 16, 7)
    recorder = harness.recorder
    if failure == "file":
        harness.output.rmdir()
        harness.output.write_bytes(b"A regular file cannot contain recordings")
    if failure == "sql":
        original_connect = sqlite3.connect

        def reject_recording(action, table, _column, _database, _trigger):
            return (
                sqlite3.SQLITE_DENY
                if action == sqlite3.SQLITE_INSERT and table in ("recordings", "episode_recordings")
                else sqlite3.SQLITE_OK
            )

        def failing_index_connect(database, *args, **kwargs):
            connection = original_connect(database, *args, **kwargs)
            if str(database).endswith(".recordings.sqlite3"):
                connection.set_authorizer(reject_recording)
            return connection

        harness.database.conn.set_authorizer(reject_recording)
        monkeypatch.setattr(sqlite3, "connect", failing_index_connect)
    _step(recorder, 0, False)
    _step(recorder, 1, False)
    admission_results, admission_errors = [], []
    if failure != "incomplete":
        _invoke(lambda: recorder.finish_episode(_metadata(7)), admission_results, admission_errors)
    if failure in ("file", "sql"):
        harness.release.set()
        assert harness.write_finished.wait(5), "Injected real I/O failure was never exercised"
    if failure == "incomplete":
        buffered = threading.Event()
        original_get = recorder.queue.get

        def observed_get(*args, **kwargs):
            if len(recorder.writer.episode_buffer) == 2:
                buffered.set()
            return original_get(*args, **kwargs)

        monkeypatch.setattr(recorder.queue, "get", observed_get)
        harness.release.set()
        assert buffered.wait(5), "Real writer did not own the incomplete episode"
    results, errors = harness.close_running()
    with closing(sqlite3.connect(harness.database.db_path)) as independent_reader:
        assert independent_reader.execute("SELECT COUNT(*) FROM episode_recordings").fetchone() == (0,)
    if failure == "sql":
        files = [path for path in harness.output.rglob("*.msgpack.lz4") if path.parent != harness.output]
        assert len(files) == 1, "SQL probe must fail after actual publication"
    failures = admission_errors + errors
    if errors and failure == "sql":
        error = errors[0]
        assert type(error).__name__ == "RecordingDrainError" and isinstance(error.receipts, tuple)
        assert error.run_id and len(error.receipts) == 1
        orphan = error.receipts[0]
        assert orphan.storage_mode == "indexed"
        assert orphan.status == "failed" and orphan.ticket == admission_results[0] and orphan.index_id is None
        assert Path(orphan.path).resolve() == files[0].resolve() and isinstance(_cause(orphan.error), sqlite3.Error)
        with pytest.raises(type(error)) as repeated:
            recorder.shutdown()
        assert repeated.value.receipts == error.receipts and repeated.value.run_id == error.run_id
        with pytest.raises((AttributeError, TypeError)):
            error.run_id = "changed"
        with pytest.raises((AttributeError, TypeError)):
            error.receipts = ()
        with pytest.raises((AttributeError, TypeError)):
            orphan.path = "changed"
    if not failures:
        assert results and isinstance(results[0], tuple) and results[0], "Writer failure was silently swallowed"
        failed_receipts = [receipt for receipt in results[0] if receipt.status == "failed"]
        assert failed_receipts, "Failed publication or unresolved work was reported as successful"
        for receipt in failed_receipts:
            assert receipt.ticket is not None and isinstance(receipt.error, Exception)
            assert receipt.index_id is None
            if failure == "sql":
                assert Path(receipt.path).resolve() == files[0].resolve()
                assert receipt.ticket == admission_results[0]
        failures = [receipt.error for receipt in failed_receipts]
    assert all(isinstance(error, (OSError, sqlite3.Error, queue.Full, RuntimeError, ValueError)) for error in failures)
    assert recorder.queue.unfinished_tasks == 0, "Failed accepted work retained queue ownership"


def test_periodic_nonselection_preserves_accepted_criterion_dictionary(harness_factory):
    harness = harness_factory(16, 2)
    # This accepted dictionary is retained; only periodic selection is implemented.
    harness.config["criteria"]["stage_transition"] = {"enabled": True}
    _step(harness.recorder, 0, False)
    _step(harness.recorder, 1, False)
    ticket = harness.recorder.finish_episode(_metadata(7))
    results, errors = harness.close_while_paused()
    receipt = _assert_receipt(harness, ticket, results, errors, "not_selected")
    assert receipt.path is None and receipt.index_id is None and receipt.error is None
    assert list(harness.output.iterdir()) == [] and harness.database.list_recordings() == []
    assert harness.config["criteria"]["stage_transition"] == {"enabled": True}


def test_legacy_metric_reads_preserve_history_without_creating_recording_index(tmp_path):
    path = tmp_path / "history.db"
    index = path.with_name(path.name + ".recordings.sqlite3")
    with DemoDatabase(path) as database:
        database.conn.execute("INSERT INTO system_state VALUES ('unrelated-history', 'keep')")
        database.conn.execute("INSERT INTO episode_recordings VALUES (7,'old/episode_7',1,2,'cap',2,1,.5,.5,0,.1,1,'periodic',17,13)")
        database.conn.commit()
    with DemoDatabase(path) as database:
        assert database.get_system_state("unrelated-history") == "keep"
        assert database.get_recording(7)["file_path"] == "old/episode_7"
        assert len(database.list_recordings()) == 1
        assert database.get_scoped_recording(run_id="absent", episode_id=7, lane=0) is None
        assert database.list_scoped_recordings(run_id="absent", lane=0) == []
        assert database.owned_family_paths == (path,)
        assert database.conn.execute("PRAGMA user_version").fetchone()[0] == 1
    assert not index.exists()


def test_run_lane_collisions_preserve_distinct_files_indexes_and_legacy_history(harness_factory):
    harness = harness_factory(16, 7)
    harness.database.conn.execute("INSERT INTO episode_recordings VALUES (7,'old/episode_7',1,2,'cap',2,1,.5,.5,0,.1,1,'periodic',17,13)")
    harness.database.conn.commit()
    harness.release.set()
    paths = set()
    for run_id, lane in (("run/a", 0), ("run/a", 1), ("run?a", 0), ("run?a", 1)):
        recorder = EpisodeRecorder.for_scope(harness.config, harness.output, harness.database, None, run_id=run_id, lane=lane)
        recorder.begin_episode(7)
        _step(recorder, 0, False)
        _step(recorder, 1, False)
        ticket = recorder.finish_episode(_metadata(7))
        receipts = recorder.shutdown()
        assert isinstance(receipts, tuple) and len(receipts) == 1
        receipt = receipts[0]
        assert receipt.status == "persisted" and receipt.ticket == ticket and ticket.episode == 7 and ticket.lane == lane
        path = Path(receipt.path).resolve()
        assert path.is_relative_to(harness.output.resolve()) and path not in paths
        assert len(msgpack.unpackb(lz4.frame.decompress(path.read_bytes()), raw=False)["steps"]) == 2
        row = harness.database.get_scoped_recording(run_id=run_id, episode_id=7, lane=lane)
        assert row["run_id"] == run_id and row["lane"] == lane and row["episode_id"] == 7
        assert row["file_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert harness.database.list_scoped_recordings(run_id=run_id, lane=lane) == [row]
        assert recorder.shutdown() == receipts
        paths.add(path)
    assert len(paths) == 4 and harness.database.get_recording(7)["file_path"] == "old/episode_7"
    with closing(sqlite3.connect(harness.database.owned_family_paths[1])) as independent_reader:
        assert independent_reader.execute("SELECT COUNT(*) FROM recordings").fetchone() == (4,)


@pytest.mark.parametrize("invalid", ("malformed", "active", "version", "schema"))
def test_closed_associated_index_export_and_fail_closed_admission(harness_factory, invalid):
    harness = harness_factory(16, 7)
    _step(harness.recorder, 0, False)
    _step(harness.recorder, 1, False)
    harness.recorder.finish_episode(_metadata(7))
    _, errors = harness.close_while_paused()
    assert not errors
    harness.database.close()
    metric = harness.database.db_path
    index = metric.with_name(metric.name + ".recordings.sqlite3")
    assert harness.database.owned_family_paths == (metric, index)
    assert harness.database.checkpoint_owned_families() == (metric, index)
    assert all(not Path(str(path) + suffix).exists() for path in (metric, index) for suffix in ("-wal", "-shm", "-journal"))
    if invalid == "malformed":
        index.write_bytes(b"malformed recording index")
    elif invalid == "active":
        Path(str(index) + "-wal").write_bytes(b"")
    else:
        with closing(sqlite3.connect(index)) as connection:
            connection.execute("PRAGMA user_version=999" if invalid == "version" else "ALTER TABLE recordings ADD COLUMN unreviewed TEXT")
            connection.commit()
    members = [Path(str(path) + suffix) for path in (metric, index) for suffix in ("", "-wal", "-shm", "-journal")]
    before = {path: path.read_bytes() for path in members if path.exists()}
    with pytest.raises((ValueError, RuntimeError)):
        DemoDatabase(metric)
    assert {path: path.read_bytes() for path in members if path.exists()} == before
    with pytest.raises((ValueError, RuntimeError)):
        harness.database.checkpoint_owned_families()
    assert {path: path.read_bytes() for path in members if path.exists()} == before


def test_explicit_no_database_preserves_durable_file_only_mode(harness_factory):
    harness = harness_factory(16, 7)
    recorder = EpisodeRecorder(harness.config, harness.output / "file-only", None, None)
    try:
        assert _step(recorder, 0, False) is None
        assert _step(recorder, 1, False) is None
        ticket = recorder.finish_episode(_metadata(7))
    finally:
        harness.release.set()
        receipts = recorder.shutdown()
    assert isinstance(receipts, tuple) and len(receipts) == 1
    receipt = receipts[0]
    assert receipt.ticket == ticket and receipt.status == "persisted" and receipt.storage_mode == "file_only"
    assert receipt.index_id is None and receipt.error is None
    assert len(msgpack.unpackb(lz4.frame.decompress(Path(receipt.path).read_bytes()), raw=False)["steps"]) == 2
    assert recorder.shutdown() == receipts and not harness.database.db_path.with_name("demo.db.recordings.sqlite3").exists()


def test_bound_frame_ticket_requires_real_binding_and_resolves_with_end(harness_factory):
    harness = harness_factory(16, 7)
    recorder = harness.recorder
    with pytest.raises(ValueError):
        recorder.record_bound_step(**_capture_args(0, False))
    recorder.begin_episode(7)
    frame_ticket = recorder.record_bound_step(**_capture_args(0, False))
    assert _step(recorder, 1, False) is None
    with pytest.raises(ValueError):
        recorder.finish_episode(_metadata(8))
    end_ticket = recorder.finish_episode(_metadata(7))
    results, errors = harness.close_while_paused()
    assert not errors and tuple(receipt.ticket for receipt in results[0]) == (frame_ticket, end_ticket)
    assert frame_ticket.episode == 7 and frame_ticket.lane == 0 and frame_ticket.sequence < end_ticket.sequence
    assert all(receipt.status == "persisted" and receipt.storage_mode == "indexed" for receipt in results[0])
    assert recorder.queue.unfinished_tasks == 0
    _assert_persisted(harness, 7)


@pytest.mark.parametrize(
    "trigger,altered_path",
    (
        (
            "CREATE TRIGGER canonical_ignore BEFORE INSERT ON episode_recordings BEGIN SELECT RAISE(IGNORE); END;",
            None,
        ),
        (
            "CREATE TRIGGER canonical_alter AFTER INSERT ON episode_recordings BEGIN "
            "UPDATE episode_recordings SET file_path='wrong/path' WHERE episode_id=NEW.episode_id; END;",
            "wrong/path",
        ),
    ),
)
def test_legacy_publication_requires_matching_committed_canonical_readback(tmp_path, harness_factory, trigger, altered_path):
    # This is admitted canonical-v1 SQL DATA, not a change to its classifier.
    with DemoDatabase(tmp_path / "demo.db") as seed:
        seed.conn.executescript(trigger)
    harness = harness_factory(16, 7)
    assert harness.database.conn.execute("SELECT COUNT(*) FROM sqlite_schema WHERE type='trigger'").fetchone()[0] == 1
    _step(harness.recorder, 0, False)
    _step(harness.recorder, 1, False)
    ticket = harness.recorder.finish_episode(_metadata(7))
    results, errors = harness.close_while_paused()
    files = [path for path in harness.output.rglob("*.msgpack.lz4") if path.parent != harness.output]
    assert len(files) == 1 and len(msgpack.unpackb(lz4.frame.decompress(files[0].read_bytes()), raw=False)["steps"]) == 2
    canonical = harness.database.get_recording(7)
    assert canonical is None or canonical["file_path"] == altered_path
    assert errors and not results, "A suppressed/altered canonical row was reported as persisted"
    error = errors[0]
    assert type(error).__name__ == "RecordingDrainError" and isinstance(error.receipts, tuple) and len(error.receipts) == 1
    receipt = error.receipts[0]
    assert receipt.ticket == ticket and receipt.status == "failed" and receipt.storage_mode == "indexed"
    assert Path(receipt.path).resolve() == files[0].resolve() and isinstance(receipt.error, RuntimeError)
    scoped = harness.database.get_scoped_recording(run_id=error.run_id, episode_id=7, lane=0)
    if scoped is not None:
        assert scoped["file_sha256"] == hashlib.sha256(files[0].read_bytes()).hexdigest()
    with pytest.raises(type(error)) as repeated:
        harness.recorder.shutdown()
    assert repeated.value is error and repeated.value.receipts == error.receipts
    assert harness.recorder.queue.unfinished_tasks == 0


@pytest.mark.parametrize("persistent", (False, True))
def test_failed_index_directory_sync_is_retried_or_remains_explicit(harness_factory, tmp_path, request, monkeypatch, persistent):
    harness = harness_factory(16, 7)
    database = DemoDatabase(tmp_path / "metric-sync" / "demo.db")
    request.addfinalizer(database.close)
    output = tmp_path / "artifact-sync" / "recordings"
    first = EpisodeRecorder(harness.config, output, database, None)
    target = database.db_path.parent.stat()
    attempts, successful = [], []
    original_fsync = os.fsync

    def failing_directory_sync(descriptor):
        actual = os.fstat(descriptor)
        is_index_directory = stat.S_ISDIR(actual.st_mode) and (actual.st_dev, actual.st_ino) == (target.st_dev, target.st_ino)
        if is_index_directory:
            attempts.append(descriptor)
            if persistent or len(attempts) == 1:
                raise OSError("injected recording-index directory sync failure")
        original_fsync(descriptor)
        if is_index_directory:
            successful.append(descriptor)

    monkeypatch.setattr(os, "fsync", failing_directory_sync)
    harness.release.set()
    _step(first, 0, False)
    _step(first, 1, False)
    first_ticket = first.finish_episode(_metadata(7))
    first_results, first_errors = [], []
    _invoke(first.shutdown, first_results, first_errors)
    assert not first_results and first_errors and len(attempts) == 1 and not successful
    first_receipt = first_errors[0].receipts[0]
    assert first_receipt.ticket == first_ticket and first_receipt.status == "failed" and isinstance(_cause(first_receipt.error), OSError)
    assert first_receipt.path is None and database.get_recording(7) is None
    second = EpisodeRecorder(harness.config, output, database, None)
    try:
        _step(second, 0, False)
        _step(second, 1, False)
        second_ticket = second.finish_episode(_metadata(14))
    finally:
        second_results, second_errors = [], []
        _invoke(second.shutdown, second_results, second_errors)
    if second_errors:
        second_receipt = second_errors[0].receipts[0]
        assert second_receipt.ticket == second_ticket and second_receipt.status == "failed"
        assert second_receipt.path is None and database.get_recording(14) is None
    else:
        assert successful, "Later publication forgot the failed required index-directory sync"
        second_receipt = second_results[0][0]
        assert second_receipt.ticket == second_ticket and second_receipt.status == "persisted"
        assert second_receipt.storage_mode == "indexed" and database.get_recording(14) is not None
    assert second.queue.unfinished_tasks == 0
    database.close()
    if successful:
        assert len(database.checkpoint_owned_families()) == 2
    else:
        with pytest.raises(RuntimeError):
            database.checkpoint_owned_families()


@pytest.mark.parametrize(
    "trigger,binding_witness",
    (
        (
            "CREATE TRIGGER binding_ignore BEFORE INSERT ON system_state "
            "WHEN NEW.key='townlet.recording-index:v2' BEGIN SELECT RAISE(IGNORE); END;",
            None,
        ),
        (
            "CREATE TRIGGER binding_alter AFTER INSERT ON system_state WHEN NEW.key='townlet.recording-index:v2' "
            "BEGIN UPDATE system_state SET value='{}' WHERE key=NEW.key; END;",
            "{}",
        ),
    ),
)
def test_publication_requires_committed_binding_and_retains_failed_association(tmp_path, harness_factory, trigger, binding_witness):
    with DemoDatabase(tmp_path / "demo.db") as seed:
        seed.conn.executescript(trigger)
    harness = harness_factory(16, 7)
    assert harness.database.conn.execute("SELECT COUNT(*) FROM sqlite_schema WHERE type='trigger'").fetchone()[0] == 1
    _step(harness.recorder, 0, False)
    _step(harness.recorder, 1, False)
    ticket = harness.recorder.finish_episode(_metadata(7))
    results, errors = harness.close_while_paused()
    assert not list(harness.output.rglob("*.msgpack.lz4"))
    assert harness.database.get_system_state("townlet.recording-index:v2") == binding_witness
    assert errors and not results, "Recording was reported persisted without its committed family binding"
    error = errors[0]
    assert type(error).__name__ == "RecordingDrainError" and isinstance(error.receipts, tuple) and len(error.receipts) == 1
    receipt = error.receipts[0]
    assert receipt.ticket == ticket and receipt.status == "failed" and receipt.storage_mode == "indexed"
    assert receipt.path is None and isinstance(_cause(receipt.error), (RuntimeError, ValueError))
    with pytest.raises(type(error)) as repeated:
        harness.recorder.shutdown()
    assert repeated.value is error and repeated.value.run_id == error.run_id and repeated.value.receipts == error.receipts
    second = EpisodeRecorder(harness.config, harness.output, harness.database, None)
    try:
        _step(second, 0, False)
        _step(second, 1, False)
        second_ticket = second.finish_episode(_metadata(14))
    finally:
        second_results, second_errors = [], []
        _invoke(second.shutdown, second_results, second_errors)
    assert second_errors and not second_results, "Later publication bypassed failed association reconciliation"
    second_receipt = second_errors[0].receipts[0]
    assert second_receipt.status == "failed" and second_receipt.ticket == second_ticket and second_receipt.path is None
    assert second_errors[0].run_id == error.run_id
    assert harness.database.get_recording(14) is None and second.queue.unfinished_tasks == 0
    harness.database.close()
    with pytest.raises((ValueError, RuntimeError)):
        harness.database.checkpoint_owned_families()
    before = {path: path.read_bytes() for path in harness.database.owned_family_paths}
    with pytest.raises((ValueError, RuntimeError)):
        DemoDatabase(harness.database.db_path)
    assert {path: path.read_bytes() for path in harness.database.owned_family_paths} == before


def _queue_repeat(recorder, total, bound):
    frames = []
    if bound:
        recorder.begin_episode(7)
    for step in (0, 1):
        capture = _capture_args(step, False)
        capture.update(reward=total / 2, extrinsic_reward=total / 4, intrinsic_reward=total / 8, shaping_reward=total / 8)
        if bound:
            frames.append(recorder.record_bound_step(**capture))
        else:
            assert recorder.record_step(**capture) is None
    metadata = replace(_metadata(7), total_reward=total, extrinsic_reward=total / 2, intrinsic_reward=total / 4, shaping_reward=total / 4)
    return tuple(frames), recorder.finish_episode(metadata)


def _assert_immutable(receipt, total):
    assert receipt.status == "persisted" and receipt.error is None
    path = Path(receipt.path)
    assert path.is_absolute() and path.is_file()
    raw = path.read_bytes()
    payload = msgpack.unpackb(lz4.frame.decompress(raw), raw=False)
    assert set(payload) == {"version", "metadata", "steps", "affordances"} and payload["version"] == 2
    assert payload["metadata"]["episode_id"] == 7 and payload["metadata"]["total_reward"] == total
    assert len(payload["steps"]) == 2 and sum(frame["reward"] for frame in payload["steps"]) == total
    return raw


def _assert_legacy_latest(database, output, total, raw):
    alias = output / "episode_000007.msgpack.lz4"
    assert alias.read_bytes() == raw and not alias.is_symlink()
    expected = {
        "episode_id": 7,
        "file_path": str(alias.relative_to(output.parent)),
        "timestamp": 1.0,
        "survival_steps": 2,
        "completion_reason": "cap",
        "total_reward": total,
        "extrinsic_reward": total / 2,
        "intrinsic_reward": total / 4,
        "shaping_reward": total / 4,
        "curriculum_stage": 0,
        "epsilon": 0.1,
        "intrinsic_weight": 1.0,
        "recording_reason": "periodic",
        "file_size_bytes": len(lz4.frame.decompress(raw)),
        "compressed_size_bytes": len(raw),
    }
    assert database.get_recording(7) == expected
    with closing(sqlite3.connect(database.db_path)) as independent_reader:
        independent_reader.row_factory = sqlite3.Row
        assert dict(independent_reader.execute("SELECT * FROM episode_recordings WHERE episode_id=7").fetchone()) == expected
        assert independent_reader.execute("PRAGMA user_version").fetchone()[0] == 1


@pytest.mark.parametrize("bound", (False, True))
def test_legacy_repeat_before_shutdown_preserves_each_publication(harness_factory, bound):
    harness = harness_factory(16, 7)
    first_frames, first = _queue_repeat(harness.recorder, 2.0, bound)
    second_frames, second = _queue_repeat(harness.recorder, 4.0, bound)
    assert first != second
    results, errors = harness.close_while_paused()
    assert not errors, "The existing legacy constructor refused a genuine second same-episode publication"
    by_ticket = {receipt.ticket: receipt for receipt in results[0]}
    earlier, latest = by_ticket[first], by_ticket[second]
    earlier_raw, latest_raw = _assert_immutable(earlier, 2.0), _assert_immutable(latest, 4.0)
    assert earlier.path != latest.path and earlier.index_id != latest.index_id and earlier_raw != latest_raw
    for generation, receipt, frames in ((1, earlier, first_frames), (2, latest, second_frames)):
        row = harness.database.get_scoped_recording_by_index(index_id=receipt.index_id)
        assert row["generation"] == generation and row["file_path"] == str(receipt.path)
        assert row["file_sha256"] == hashlib.sha256(Path(receipt.path).read_bytes()).hexdigest()
        assert all(by_ticket[ticket].path == receipt.path and by_ticket[ticket].index_id == receipt.index_id for ticket in frames)
    _assert_legacy_latest(harness.database, harness.output, 4.0, latest_raw)
    alias = harness.output / "episode_000007.msgpack.lz4"
    assert all(alias.stat().st_ino != Path(receipt.path).stat().st_ino for receipt in (earlier, latest))
    alias.write_bytes(b"ordinary caller overwrite of the mutable alias")
    assert Path(earlier.path).read_bytes() == earlier_raw and Path(latest.path).read_bytes() == latest_raw
    alias.write_bytes(latest_raw)
    assert harness.recorder.shutdown() == results[0]
    assert len(harness.database.list_scoped_recordings(run_id="townlet:legacy-recording:v1", lane=0)) == 2


def test_file_only_repeats_keep_immutable_receipts_across_instances(harness_factory):
    harness = harness_factory(16, 7)
    output = harness.output / "file-only-repeat"
    recorder = EpisodeRecorder(harness.config, output, None, None)
    _queue_repeat(recorder, 2.0, False)
    _queue_repeat(recorder, 4.0, False)
    harness.release.set()
    results, errors = [], []
    _invoke(recorder.shutdown, results, errors)
    assert not errors, "File-only legacy capture refused its second genuine same-episode publication"
    receipts = results[0]
    raw = [_assert_immutable(receipt, total) for receipt, total in zip(receipts, (2.0, 4.0), strict=True)]
    later = EpisodeRecorder(harness.config, output, None, None)
    _queue_repeat(later, 6.0, False)
    latest = later.shutdown()[0]
    raw.append(_assert_immutable(latest, 6.0))
    all_receipts = (*receipts, latest)
    assert len({receipt.path for receipt in all_receipts}) == 3
    assert all(receipt.index_id is None and receipt.storage_mode == "file_only" for receipt in all_receipts)
    assert all(Path(receipt.path).read_bytes() == data for receipt, data in zip(all_receipts, raw, strict=True))
    assert (output / "episode_000007.msgpack.lz4").read_bytes() == raw[-1]


@pytest.mark.parametrize("rejection", ("frame", "finish"))
def test_legacy_capacity_rejection_keeps_no_throw_calls_and_truthful_drain(harness_factory, caplog, rejection):
    harness = harness_factory(2, 7)
    recorder = harness.recorder
    _step(recorder, 0, False)
    _step(recorder, 1, False)
    before = recorder._sequence, recorder._open_frames, recorder.queue.qsize(), recorder.queue.unfinished_tasks
    if rejection == "frame":
        assert _step(recorder, 2, False) is None
        assert recorder.legacy_dropped_frames == 1 and recorder.legacy_rejected_finishes == 0
        assert "dropping frame" in caplog.text
        assert recorder.finish_episode(_metadata(7)) is None
        assert recorder.legacy_rejected_finishes == 1
    else:
        assert recorder.finish_episode(_metadata(7)) is None
        assert recorder.legacy_dropped_frames == 0 and recorder.legacy_rejected_finishes == 1
        assert "metadata lost" in caplog.text
    assert (recorder._sequence, recorder._open_frames, recorder.queue.qsize(), recorder.queue.unfinished_tasks) == before
    harness.release.set()
    recorder.queue.join()
    if rejection == "frame":
        ticket = recorder.finish_episode(_metadata(7))
        assert ticket.sequence == 2
    results, errors = harness.close_running()
    assert errors and not results and not list(harness.output.rglob("*.msgpack.lz4"))
    if rejection == "frame":
        assert errors[0].receipts[0].ticket == ticket and errors[0].receipts[0].status == "failed"
        assert recorder.legacy_dropped_frames == 1
    else:
        assert errors[0].receipts == () and errors[0].unbound_sequences == (0, 1)
        assert recorder.legacy_rejected_finishes == 1


def test_legacy_rejected_boundary_can_retry_without_resetting_counters(harness_factory):
    harness = harness_factory(2, 7)
    recorder = harness.recorder
    _step(recorder, 0, False)
    _step(recorder, 1, False)
    assert recorder.finish_episode(_metadata(7)) is None
    harness.release.set()
    recorder.queue.join()
    ticket = recorder.finish_episode(_metadata(7))
    assert ticket.sequence == 2
    results, errors = harness.close_running()
    assert not errors and len(results[0]) == 1 and results[0][0].ticket == ticket
    _assert_immutable(results[0][0], 2.0)
    assert recorder.legacy_dropped_frames == 0 and recorder.legacy_rejected_finishes == 1
    with pytest.raises((AttributeError, TypeError)):
        recorder.legacy_rejected_finishes = 0


@pytest.mark.parametrize("route", ("legacy_bound", "scoped_bound", "scoped_step", "scoped_finish"))
def test_qualified_capacity_stays_strict_without_legacy_counter_changes(harness_factory, route):
    harness = harness_factory(1, 7)
    recorder = harness.recorder
    if route != "legacy_bound":
        recorder = EpisodeRecorder.for_scope(harness.config, harness.output, harness.database, None, run_id="strict-capacity", lane=3)
    recorder.begin_episode(7)
    if route.endswith("bound"):
        recorder.record_bound_step(**_capture_args(0, False))
    else:
        _step(recorder, 0, False)
    before = recorder._sequence, recorder._open_frames, recorder.queue.unfinished_tasks
    with pytest.raises(queue.Full):
        if route.endswith("bound"):
            recorder.record_bound_step(**_capture_args(1, False))
        elif route == "scoped_step":
            _step(recorder, 1, False)
        else:
            recorder.finish_episode(_metadata(7))
    assert (recorder._sequence, recorder._open_frames, recorder.queue.unfinished_tasks) == before
    assert recorder.legacy_dropped_frames == 0 and recorder.legacy_rejected_finishes == 0
    harness.release.set()
    recorder.queue.join()
    results, errors = [], []
    _invoke(recorder.shutdown, results, errors)
    assert errors and not results and recorder.queue.unfinished_tasks == 0


def _publish_once(config, output, database, total):
    recorder = EpisodeRecorder(config, output, database, None)
    try:
        _queue_repeat(recorder, total, False)
    finally:
        receipts = recorder.shutdown()
    assert recorder.shutdown() == receipts
    return receipts[0]


def test_repeat_generations_continue_after_instances_reopen_and_remote_db_root(harness_factory, tmp_path):
    harness = harness_factory(16, 7)
    harness.release.set()
    output, metric = tmp_path / "artifact-root" / "recordings", tmp_path / "metric-root" / "metrics.db"
    with DemoDatabase(metric) as database:
        first = _publish_once(harness.config, output, database, 2.0)
        second = _publish_once(harness.config, output, database, 4.0)
        original = _assert_immutable(first, 2.0), _assert_immutable(second, 4.0)
        _assert_legacy_latest(database, output, 4.0, original[1])
    with DemoDatabase(metric) as database:
        third = _publish_once(harness.config, output, database, 6.0)
        latest = _assert_immutable(third, 6.0)
        for generation, receipt in enumerate((first, second, third), 1):
            row = database.get_scoped_recording_by_index(index_id=receipt.index_id)
            assert row["generation"] == generation and row["file_path"] == str(receipt.path)
        assert Path(first.path).read_bytes() == original[0] and Path(second.path).read_bytes() == original[1]
        assert database.get_scoped_recording(run_id="townlet:legacy-recording:v1", episode_id=7, lane=0)["index_id"] == third.index_id
        _assert_legacy_latest(database, output, 6.0, latest)
    assert database.checkpoint_owned_families() == (metric, metric.with_name(metric.name + ".recordings.sqlite3"))


def test_scoped_generation_zero_refuses_repeat_and_preserves_legacy_alias(harness_factory):
    harness = harness_factory(16, 7)
    _queue_repeat(harness.recorder, 2.0, False)
    results, errors = harness.close_while_paused()
    assert not errors
    legacy = results[0][0]
    alias_bytes = (harness.output / "episode_000007.msgpack.lz4").read_bytes()
    reserved = "townlet:legacy-recording:v1"
    with pytest.raises(ValueError):
        EpisodeRecorder.for_scope(harness.config, harness.output, harness.database, None, run_id=reserved, lane=0)
    scoped = EpisodeRecorder.for_scope(harness.config, harness.output, harness.database, None, run_id=reserved + "-user", lane=0)
    _queue_repeat(scoped, 4.0, True)
    receipt = scoped.shutdown()[-1]
    original = _assert_immutable(receipt, 4.0)
    assert harness.database.get_scoped_recording_by_index(index_id=receipt.index_id)["generation"] == 0
    duplicate = EpisodeRecorder.for_scope(harness.config, harness.output, harness.database, None, run_id=reserved + "-user", lane=0)
    _queue_repeat(duplicate, 6.0, True)
    with pytest.raises(RuntimeError) as failed:
        duplicate.shutdown()
    assert all(item.path is None and item.status == "failed" for item in failed.value.receipts)
    assert Path(receipt.path).read_bytes() == original
    assert (harness.output / "episode_000007.msgpack.lz4").read_bytes() == alias_bytes
    assert harness.database.get_recording(7)["total_reward"] == 2.0 and legacy.storage_mode == "indexed"


@pytest.mark.parametrize("evidence", ("v1_binding", "v1_index", "foreign_binding"))
def test_v2_admission_preserves_earlier_or_foreign_index_evidence(tmp_path, evidence):
    metric = tmp_path / "metric.db"
    with DemoDatabase(metric) as database:
        if evidence != "v1_index":
            key = "townlet.recording-index:v1"
            if evidence == "foreign_binding":
                key = "townlet.recording-index:future"
            database.conn.execute("INSERT INTO system_state VALUES (?,?)", (key, "{}"))
            database.conn.commit()
    members = [metric]
    if evidence == "v1_index":
        index = metric.with_name(metric.name + ".recordings.sqlite3")
        connection = sqlite3.connect(index)
        connection.execute("PRAGMA user_version=1")
        connection.close()
        members.append(index)
    before = {path: path.read_bytes() for path in members}
    with pytest.raises(ValueError):
        DemoDatabase(metric)
    assert {path: path.read_bytes() for path in members} == before


@pytest.mark.parametrize(
    "fault",
    (
        "guard",
        "artifact",
        "cleanup",
        "unlock",
        "alias_replace",
        "alias_sync",
        "alias_readback",
        "canonical_ignore",
        "canonical_alter",
        "index_commit",
        "index_readback",
    ),
)
def test_later_publication_failure_keeps_prior_immutable_success(harness_factory, monkeypatch, fault):
    import fcntl
    import tempfile

    harness = harness_factory(16, 7)
    _queue_repeat(harness.recorder, 2.0, False)
    results, errors = harness.close_while_paused()
    assert not errors
    prior = results[0][0]
    prior_raw = _assert_immutable(prior, 2.0)
    prior_row = harness.database.get_scoped_recording_by_index(index_id=prior.index_id)
    alias = harness.output / "episode_000007.msgpack.lz4"
    if fault in ("guard", "unlock"):
        original_flock = fcntl.flock

        def broken_lock(descriptor, operation):
            if (operation == fcntl.LOCK_EX and fault == "guard") or (operation == fcntl.LOCK_UN and fault == "unlock"):
                raise OSError("injected output-root lock failure")
            return original_flock(descriptor, operation)

        monkeypatch.setattr(fcntl, "flock", broken_lock)
    elif fault == "artifact":

        def broken_stage(*args, **kwargs):
            raise OSError("injected artifact staging failure")

        monkeypatch.setattr(tempfile, "mkstemp", broken_stage)
    elif fault == "cleanup":
        original_unlink = Path.unlink

        def unlinking(path, *args, **kwargs):
            if path.name.startswith(".recording-"):
                raise OSError("injected temporary cleanup failure")
            return original_unlink(path, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", unlinking)
    elif fault == "alias_readback":
        original_read = Path.read_bytes

        def reading(path):
            if path == alias:
                return b"injected alias readback mismatch"
            return original_read(path)

        monkeypatch.setattr(Path, "read_bytes", reading)
    elif fault in ("alias_replace", "alias_sync"):
        original_replace, original_fsync = os.replace, os.fsync
        replaced = threading.Event()

        def replacing(source, target):
            if Path(target) == alias and fault == "alias_replace":
                raise OSError("injected alias replace failure")
            result = original_replace(source, target)
            if Path(target) == alias:
                replaced.set()
            return result

        def syncing(descriptor):
            actual = os.fstat(descriptor)
            if replaced.is_set() and stat.S_ISDIR(actual.st_mode) and actual.st_ino == harness.output.stat().st_ino:
                raise OSError("injected alias directory sync failure")
            return original_fsync(descriptor)

        monkeypatch.setattr(os, "replace", replacing)
        if fault == "alias_sync":
            monkeypatch.setattr(os, "fsync", syncing)
    elif fault.startswith("canonical"):
        statement = "SELECT RAISE(IGNORE);"
        timing = "BEFORE"
        if fault == "canonical_alter":
            timing, statement = "AFTER", "UPDATE episode_recordings SET file_path='wrong/path' WHERE episode_id=NEW.episode_id;"
        harness.database.conn.executescript(f"CREATE TRIGGER later_fault {timing} INSERT ON episode_recordings BEGIN {statement} END;")
    else:
        committed = threading.Event()

        def index_authorizer(action, first, _second, _db, _trigger):
            if action == sqlite3.SQLITE_TRANSACTION and first == "COMMIT":
                if fault == "index_commit":
                    return sqlite3.SQLITE_DENY
                committed.set()
            if fault == "index_readback" and committed.is_set() and action == sqlite3.SQLITE_READ and first == "recordings":
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        harness.database._index_conn.set_authorizer(index_authorizer)
    actor = EpisodeRecorder(harness.config, harness.output, harness.database, None)
    _queue_repeat(actor, 4.0, False)
    with pytest.raises(RuntimeError) as failed:
        actor.shutdown()
    harness.database._index_conn.set_authorizer(None)
    receipt = failed.value.receipts[0]
    error = receipt.error
    assert type(error).__name__ == "RecordingPublicationError" and receipt.status == "failed" and receipt.storage_mode == "indexed"
    assert error.path == receipt.path and error.cause is not None
    if fault in ("guard", "artifact"):
        assert receipt.path is None and error.alias_state == error.canonical_state == error.index_state == "not_attempted"
    else:
        assert Path(receipt.path).is_file() and receipt.path != prior.path and error.generation == 2
        assert error.legacy_alias_path == alias
    if fault == "index_commit":
        assert error.canonical_state == "confirmed" and error.index_state == "unconfirmed"
        with closing(sqlite3.connect(harness.database.owned_family_paths[1])) as reader:
            assert reader.execute("SELECT COUNT(*) FROM recordings").fetchone() == (1,)
        assert harness.database.get_recording(7)["total_reward"] == 4.0
    if fault == "index_readback":
        assert (
            error.index_state == "unconfirmed"
            and len(harness.database.list_scoped_recordings(run_id="townlet:legacy-recording:v1", lane=0)) == 2
        )
    assert Path(prior.path).read_bytes() == prior_raw
    assert harness.database.get_scoped_recording_by_index(index_id=prior.index_id) == prior_row
    with pytest.raises((AttributeError, TypeError)):
        error.phase = "confirmed"
    with pytest.raises(type(failed.value)) as repeated:
        actor.shutdown()
    assert repeated.value is failed.value
    if fault in ("unlock", "alias_replace"):
        if fault == "unlock":
            monkeypatch.setattr(fcntl, "flock", original_flock)
        else:
            monkeypatch.setattr(os, "replace", original_replace)
        retried = _publish_once(harness.config, harness.output, harness.database, 6.0)
        assert retried.path != receipt.path and _assert_immutable(retried, 6.0)
        assert Path(prior.path).read_bytes() == prior_raw


def test_same_root_threads_publish_serially_through_complete_db_readback(harness_factory, monkeypatch):
    import townlet.recording.recorder as module

    harness = harness_factory(16, 7)
    first = harness.recorder
    first.writer_thread.name = "FirstPublisher"
    entered, second_entered, release = (threading.Event() for _ in range(3))
    original_guard, original_replace = module._legacy_output_root_guard, os.replace

    @contextmanager
    def observing_guard(root):
        if threading.current_thread().name == "SecondPublisher":
            second_entered.set()
        with original_guard(root):
            yield

    def replacing(source, target):
        if threading.current_thread().name == "FirstPublisher":
            entered.set()
            assert release.wait(10)
        return original_replace(source, target)

    monkeypatch.setattr(module, "_legacy_output_root_guard", observing_guard)
    monkeypatch.setattr(os, "replace", replacing)
    _queue_repeat(first, 2.0, False)
    first_results, first_errors, second_results, second_errors = [], [], [], []
    closer = threading.Thread(target=_invoke, args=(first.shutdown, first_results, first_errors), daemon=True)
    closer.start()
    harness.release.set()
    try:
        assert entered.wait(5)
        second = EpisodeRecorder(harness.config, harness.output, harness.database, None)
        second.writer_thread.name = "SecondPublisher"
        _queue_repeat(second, 4.0, False)
        other = threading.Thread(target=_invoke, args=(second.shutdown, second_results, second_errors), daemon=True)
        other.start()
        assert second_entered.wait(5)
    finally:
        release.set()
        closer.join(10)
    other.join(10)
    assert not closer.is_alive() and not other.is_alive() and not first_errors and not second_errors
    earlier, latest = first_results[0][0], second_results[0][0]
    _assert_immutable(earlier, 2.0)
    latest_raw = _assert_immutable(latest, 4.0)
    _assert_legacy_latest(harness.database, harness.output, 4.0, latest_raw)
    assert earlier.path != latest.path and earlier.index_id != latest.index_id


_PROCESS_PUBLISHER = """
import fcntl, hashlib, json, sys
from pathlib import Path
expected, output = json.loads(sys.argv[1]), Path(sys.argv[2])
def identity():
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest for path, digest in expected.items())
identity()
with (output / '.townlet-legacy-recording.lock').open('a+b') as stream:
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('contended', flush=True)
    else:
        raise AssertionError('real parent publication did not own its persistent flock')
import torch
import townlet.recording.recorder as module
assert str(Path(module.__file__).resolve()) in expected
torch.set_num_threads(1)
assert torch.get_num_threads() == 1
config = {'max_queue_size': 16, 'compression': 'lz4', 'criteria': {'periodic': {'enabled': True, 'interval': 7}}}
recorder = module.EpisodeRecorder(config, output, None, None)
for step in (0, 1):
    assert recorder.record_step(step=step, positions=torch.tensor([step, 0]), meters=torch.tensor([.5]*8),
        action=0, reward=2., extrinsic_reward=1., intrinsic_reward=.5, shaping_reward=.5, done=False,
        q_values=None, epsilon=.1, action_masks=torch.ones(6, dtype=torch.bool),
        time_of_day=None, interaction_progress=None) is None
metadata = module.EpisodeMetadata(episode_id=7, survival_steps=2, completion_reason='cap', total_reward=4.,
    extrinsic_reward=2., intrinsic_reward=1., shaping_reward=1., curriculum_stage=0, epsilon=.1,
    intrinsic_weight=1., timestamp=1., affordance_layout={}, affordance_visits={}, custom_action_uses={})
recorder.finish_episode(metadata)
receipt = recorder.shutdown()[0]
assert receipt.status == 'persisted' and receipt.storage_mode == 'file_only' and receipt.index_id is None
identity()
assert torch.get_num_threads() == 1
print(json.dumps({'path': str(receipt.path)}), flush=True)
"""


def test_real_process_contention_nested_flock_and_file_only_indexed_overlap(harness_factory, monkeypatch):
    import fcntl

    import townlet.recording.recorder as module

    harness = harness_factory(16, 7)
    root = Path(__file__).resolve().parents[4]
    owned = (
        Path(module.__file__).resolve(),
        root / "src/townlet/demo/database.py",
        root / "src/townlet/recording/receipts.py",
        Path(__file__).resolve(),
    )
    expected = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in owned}
    entered, release = threading.Event(), threading.Event()
    original_replace, original_flock = os.replace, fcntl.flock
    acquisitions = []
    harness.recorder.writer_thread.name = "IndexedParent"

    def flocking(descriptor, operation):
        if operation == fcntl.LOCK_EX and threading.current_thread().name == "IndexedParent":
            acquisitions.append(descriptor)
        return original_flock(descriptor, operation)

    def replacing(source, target):
        with module._legacy_output_root_guard(harness.output):
            entered.set()
            assert release.wait(10), "Parent process publication was not released"
        return original_replace(source, target)

    monkeypatch.setattr(fcntl, "flock", flocking)
    monkeypatch.setattr(os, "replace", replacing)
    _queue_repeat(harness.recorder, 2.0, False)
    results, errors = [], []
    closer = threading.Thread(target=_invoke, args=(harness.recorder.shutdown, results, errors), daemon=True)
    closer.start()
    harness.release.set()
    process = None
    try:
        assert entered.wait(5)
        lock_inode = (harness.output / ".townlet-legacy-recording.lock").stat().st_ino
        assert len(acquisitions) == 1, "Same-thread nesting reacquired flock on another descriptor"
        environment = dict(os.environ)
        environment.update(
            PYTHONPATH=str(root / "src"), CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", _PROCESS_PUBLISHER, json.dumps(expected), str(harness.output)],
            cwd=root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert process.stdout.readline().strip() == "contended"
    finally:
        release.set()
        closer.join(10)
        if process is not None:
            try:
                output, error_output = process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                pytest.fail("Independent publisher failed to release/finish")
    assert not closer.is_alive() and not errors and process.returncode == 0, error_output
    parent = results[0][0]
    _assert_immutable(parent, 2.0)
    child_path = Path(json.loads(output.strip().splitlines()[-1])["path"])
    child_raw = child_path.read_bytes()
    assert msgpack.unpackb(lz4.frame.decompress(child_raw), raw=False)["metadata"]["total_reward"] == 4.0
    assert child_path != parent.path and (harness.output / "episode_000007.msgpack.lz4").read_bytes() == child_raw
    assert harness.database.get_recording(7)["total_reward"] == 2.0
    assert (harness.output / ".townlet-legacy-recording.lock").stat().st_ino == lock_inode
    assert {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in owned} == expected


def test_legacy_boundary_rejection_counter_is_cumulative_across_publications(harness_factory, monkeypatch):
    harness = harness_factory(2, 7)
    recorder = harness.recorder
    paused, release = threading.Event(), threading.Event()
    original = recorder.writer._process_episode_end

    def processing(*args):
        original(*args)
        if not paused.is_set():
            paused.set()
            assert release.wait(10)

    monkeypatch.setattr(recorder.writer, "_process_episode_end", processing)
    _step(recorder, 0, False)
    _step(recorder, 1, False)
    assert recorder.finish_episode(_metadata(7)) is None
    harness.release.set()
    recorder.queue.join()
    first = recorder.finish_episode(_metadata(7))
    try:
        assert paused.wait(5)
        _step(recorder, 0, False)
        _step(recorder, 1, False)
        assert recorder.finish_episode(_metadata(7)) is None
        assert recorder.legacy_rejected_finishes == 2
    finally:
        release.set()
    recorder.queue.join()
    second = recorder.finish_episode(_metadata(7))
    results, errors = harness.close_running()
    assert not errors and tuple(item.ticket for item in results[0]) == (first, second)
    assert recorder.legacy_dropped_frames == 0 and recorder.legacy_rejected_finishes == 2
    with pytest.raises(RuntimeError):
        _step(recorder, 2, False)


def test_uncompressed_legacy_repeat_preserves_native_payload_and_alias(harness_factory):
    harness = harness_factory(16, 7)
    harness.config["compression"] = "none"
    _queue_repeat(harness.recorder, 2.0, False)
    _queue_repeat(harness.recorder, 4.0, False)
    results, errors = harness.close_while_paused()
    assert not errors and len(results[0]) == 2
    first, second = results[0]
    assert first.path != second.path
    for receipt, total in ((first, 2.0), (second, 4.0)):
        payload = msgpack.unpackb(Path(receipt.path).read_bytes(), raw=False)
        assert payload["version"] == 2 and payload["metadata"]["total_reward"] == total
    assert (harness.output / "episode_000007.msgpack.lz4").read_bytes() == Path(second.path).read_bytes()


@pytest.mark.parametrize("ancestor", ("top", "nested"))
def test_fresh_recorder_retries_failed_nested_root_ancestor_durability(harness_factory, tmp_path, monkeypatch, ancestor):
    harness = harness_factory(16, 7)
    harness.release.set()
    output = tmp_path / "new-parent" / "new-child" / "recordings"
    target = tmp_path
    if ancestor == "nested":
        target = tmp_path / "new-parent"
    recovered = threading.Event()
    attempts, successful = [], []
    original_fsync = os.fsync

    def syncing(descriptor):
        actual = os.fstat(descriptor)
        if stat.S_ISDIR(actual.st_mode) and target.exists():
            expected = target.stat()
            if (actual.st_dev, actual.st_ino) == (expected.st_dev, expected.st_ino):
                attempts.append(descriptor)
                if not recovered.is_set():
                    raise OSError("persistent nested-root ancestor sync failure")
                original_fsync(descriptor)
                successful.append(descriptor)
                return
        original_fsync(descriptor)

    monkeypatch.setattr(os, "fsync", syncing)
    with pytest.raises(OSError, match="nested-root ancestor"):
        EpisodeRecorder(harness.config, output, None, None)
    assert output.is_dir() and len(attempts) == 1
    results, errors = [], []
    _invoke(lambda: _publish_once(harness.config, output, None, 2.0), results, errors)
    assert errors and not results, "Fresh recorder forgot an explicitly failed ancestor durability operation"
    assert all(isinstance(error, (OSError, RuntimeError)) for error in errors)
    assert not successful
    recovered.set()
    receipt = _publish_once(harness.config, output, None, 4.0)
    assert successful, "Recovery reported persisted without syncing the original failed ancestor"
    _assert_immutable(receipt, 4.0)


def test_new_database_owner_retries_failed_index_parent_sync(harness_factory, tmp_path, monkeypatch):
    harness = harness_factory(16, 7)
    harness.release.set()
    metric, output = tmp_path / "metric-owner" / "metrics.db", tmp_path / "artifact-owner" / "recordings"
    database = DemoDatabase(metric)
    target = metric.parent.stat()
    original_fsync = os.fsync
    recovered = threading.Event()
    attempts, successful = [], []

    def syncing(descriptor):
        actual = os.fstat(descriptor)
        if stat.S_ISDIR(actual.st_mode) and (actual.st_dev, actual.st_ino) == (target.st_dev, target.st_ino):
            attempts.append(descriptor)
            if not recovered.is_set():
                raise OSError("persistent index-parent sync failure")
            original_fsync(descriptor)
            successful.append(descriptor)
            return
        original_fsync(descriptor)

    monkeypatch.setattr(os, "fsync", syncing)
    results, errors = [], []
    try:
        _invoke(lambda: _publish_once(harness.config, output, database, 2.0), results, errors)
        assert errors and not results and attempts and not successful
    finally:
        database.close()

    def fresh_publication(total):
        with DemoDatabase(metric) as reopened:
            return _publish_once(harness.config, output, reopened, total)

    results, errors = [], []
    _invoke(lambda: fresh_publication(4.0), results, errors)
    assert errors and not results, "Fresh DB owner forgot the failed explicit index-parent sync"
    assert all(isinstance(error, (OSError, RuntimeError)) for error in errors)
    recovered.set()
    receipt = fresh_publication(6.0)
    assert successful
    _assert_immutable(receipt, 6.0)


def test_committed_index_then_release_failure_preserves_structured_primary_custody(harness_factory, monkeypatch):
    import fcntl

    fail_commit = threading.Event()
    original_connect, original_flock = sqlite3.connect, fcntl.flock

    class CommitAfterFailure(sqlite3.Connection):
        def commit(self):
            super().commit()
            if fail_commit.is_set():
                raise OSError("companion commit completed before injected failure")

    def connecting(database, *args, **kwargs):
        if str(database).endswith(".recordings.sqlite3"):
            kwargs["factory"] = CommitAfterFailure
        return original_connect(database, *args, **kwargs)

    def unlocking(descriptor, operation):
        result = original_flock(descriptor, operation)
        if operation == fcntl.LOCK_UN and fail_commit.is_set():
            raise OSError("root unlock completed before injected failure")
        return result

    monkeypatch.setattr(sqlite3, "connect", connecting)
    monkeypatch.setattr(fcntl, "flock", unlocking)
    harness = harness_factory(16, 7)
    _queue_repeat(harness.recorder, 2.0, False)
    results, errors = harness.close_while_paused()
    assert not errors
    prior = results[0][0]
    prior_bytes = _assert_immutable(prior, 2.0)
    prior_row = harness.database.get_scoped_recording_by_index(index_id=prior.index_id)
    fail_commit.set()
    actor = EpisodeRecorder(harness.config, harness.output, harness.database, None)
    _queue_repeat(actor, 4.0, False)
    with pytest.raises(RuntimeError) as failed:
        actor.shutdown()
    receipt = failed.value.receipts[0]
    error = receipt.error
    assert error.phase == "index" and error.canonical_state == "confirmed" and error.index_state == "unconfirmed"
    assert error.index_id == 2 and error.generation == 2 and error.alias_state == "confirmed"
    assert error.path == receipt.path and Path(receipt.path).is_file()

    def messages(cause):
        parts = [str(cause)]
        if isinstance(cause, BaseExceptionGroup):
            for child in cause.exceptions:
                parts.extend(messages(child))
        elif hasattr(cause, "cause"):
            parts.extend(messages(cause.cause))
        return parts

    joined = " ".join(messages(error.cause))
    assert "companion commit completed" in joined and "root unlock completed" in joined
    assert len(harness.database.list_scoped_recordings(run_id="townlet:legacy-recording:v1", lane=0)) == 2
    assert (
        Path(prior.path).read_bytes() == prior_bytes
        and harness.database.get_scoped_recording_by_index(index_id=prior.index_id) == prior_row
    )
    assert harness.database.get_recording(7)["total_reward"] == 4.0
