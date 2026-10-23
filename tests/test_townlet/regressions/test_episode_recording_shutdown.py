"""Ordinary runner shutdown must retain every accepted recording entry."""

from __future__ import annotations

import inspect
import json
import os
import queue
import shutil
import sqlite3
from collections.abc import Callable
from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from typing import Any

import lz4.frame
import msgpack
import pytest

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME
from townlet.demo.runner import DemoRunner
from townlet.recording.data_structures import EpisodeEndMarker, RecordedStep
from townlet.recording.recorder import EpisodeRecorder, RecordingWriter


@pytest.mark.parametrize("attempt", range(10))
def test_ordinary_runner_shutdown_persists_accepted_episode(
    attempt: int,
    tmp_path: Path,
    config_pack_factory: Callable[..., Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check ten fresh real runs immediately after their ordinary cleanup."""
    accepted: list[RecordedStep | EpisodeEndMarker] = []
    dequeued: list[RecordedStep | EpisodeEndMarker] = []
    original_put = queue.Queue._put
    original_get = queue.Queue._get

    def observe_put(real_queue: queue.Queue, entry: Any) -> None:
        original_put(real_queue, entry)
        if isinstance(entry, (RecordedStep, EpisodeEndMarker)):
            accepted.append(entry)

    def observe_get(real_queue: queue.Queue) -> Any:
        entry = original_get(real_queue)
        if isinstance(entry, (RecordedStep, EpisodeEndMarker)):
            dequeued.append(entry)
        return entry

    # Observe the existing queue under its own mutex; production and consumption
    # still use the real recorder, real queue methods, and real writer thread.
    monkeypatch.setattr(queue.Queue, "_put", observe_put)
    monkeypatch.setattr(queue.Queue, "_get", observe_get)

    def configure(data: dict[str, Any]) -> None:
        training = data["training"]
        training["population"]["size"] = 1
        training["training_loop"]["max_episodes"] = 1
        training["training_loop"]["max_steps_per_episode"] = 2
        data["recording"] = {
            "enabled": True,
            "output_dir": "recordings",
            "max_queue_size": 100,
            "compression": "lz4",
            "criteria": {"periodic": {"enabled": True, "interval": 1}},
        }

    config_dir = config_pack_factory(modifier=configure)
    db_path = tmp_path / "demo.db"
    checkpoint_dir = tmp_path / "checkpoints"
    outcome: dict[str, Any] = {
        "attempt": attempt,
        "source_paths": {cls.__name__: str(Path(inspect.getfile(cls)).resolve()) for cls in (DemoRunner, EpisodeRecorder, RecordingWriter)},
        "status": "started",
    }

    try:
        with DemoRunner(
            config_dir=config_dir,
            db_path=db_path,
            checkpoint_dir=checkpoint_dir,
            max_episodes=1,
            level_name=PRIMARY_LEVEL_NAME,
        ) as runner:
            runner.run()

        # Inspect once immediately after the public run/context-manager cleanup.
        # No sleeps, file polls, manual finish calls, or additional writer joins.
        assert runner.recorder is not None
        recorder = runner.recorder
        with recorder.queue.mutex:
            outstanding = list(recorder.queue.queue)
        with closing(sqlite3.connect(db_path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = [dict(row) for row in connection.execute("SELECT * FROM episode_recordings")]
            episodes = [dict(row) for row in connection.execute("SELECT * FROM episodes")]
        frames = [entry for entry in accepted if isinstance(entry, RecordedStep)]
        markers = [entry for entry in accepted if isinstance(entry, EpisodeEndMarker)]
        outcome.update(
            accepted=[{"kind": type(entry).__name__, "data": asdict(entry)} for entry in accepted],
            dequeued=[{"kind": type(entry).__name__, "data": asdict(entry)} for entry in dequeued],
            outstanding=[{"kind": type(entry).__name__, "data": asdict(entry)} for entry in outstanding],
            buffered=[asdict(entry) for entry in recorder.writer.episode_buffer],
            writer_alive=recorder.writer_thread.is_alive(),
            index_rows=rows,
            episode_rows=episodes,
            completed_live_agent_steps=runner.completed_live_agent_steps,
        )
        decoded = None
        if len(rows) == 1:
            recording_path = checkpoint_dir / rows[0]["file_path"]
            outcome["recording_path"] = str(recording_path)
            if recording_path.is_file():
                compressed = recording_path.read_bytes()
                serialized = lz4.frame.decompress(compressed)
                decoded = msgpack.unpackb(serialized, raw=False)
                outcome["decoded"] = decoded
                outcome["compressed_size"] = len(compressed)
                outcome["serialized_size"] = len(serialized)

        assert runner.current_episode == 1
        assert runner.completed_live_agent_steps == 2
        assert len(frames) == 2, outcome
        assert len(markers) == 1, outcome
        assert not outcome["writer_alive"], outcome
        assert len(rows) == 1, f"ordinary shutdown lost recording index: {outcome}"
        assert decoded is not None, f"ordinary shutdown lost recording artifact: {outcome}"
        assert not outstanding, f"ordinary shutdown left accepted entries queued: {outcome}"
        assert not recorder.writer.episode_buffer, outcome
        assert dequeued == accepted, outcome
        expected = msgpack.unpackb(
            msgpack.packb({"metadata": asdict(markers[0].metadata), "steps": [asdict(frame) for frame in frames]}, use_bin_type=True),
            raw=False,
        )
        assert decoded["metadata"] == expected["metadata"]
        assert decoded["steps"] == expected["steps"]
        assert decoded["version"] == 2
        assert [frame["step"] for frame in decoded["steps"]] == [0, 1]
        assert decoded["metadata"]["survival_steps"] == 2
        assert rows[0]["episode_id"] == decoded["metadata"]["episode_id"] == 0
        assert rows[0]["survival_steps"] == 2
        for name in (
            "timestamp",
            "total_reward",
            "extrinsic_reward",
            "intrinsic_reward",
            "shaping_reward",
            "completion_reason",
            "curriculum_stage",
            "epsilon",
            "intrinsic_weight",
        ):
            assert rows[0][name] == decoded["metadata"][name]
        assert rows[0]["recording_reason"] == "periodic"
        assert rows[0]["compressed_size_bytes"] == outcome["compressed_size"]
        assert rows[0]["file_size_bytes"] == outcome["serialized_size"]
        outcome["status"] = "passed"
    except BaseException as error:
        outcome["status"] = "failed"
        outcome["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        (tmp_path / "outcome.json").write_text(json.dumps(outcome, indent=2) + "\n")
        evidence_dir = os.environ.get("EPISODE_RECORDING_SHUTDOWN_EVIDENCE_DIR")
        if evidence_dir is not None:
            shutil.copytree(tmp_path, Path(evidence_dir) / f"attempt-{attempt:02d}")
