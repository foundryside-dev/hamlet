"""Real authored runner artifacts agree through persistence, playback and exports."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import inspect
import json
import math
import os
import queue
import shutil
import sqlite3
import subprocess
from collections import Counter
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import lz4.frame
import msgpack
import pytest
import torch

from scripts.l2_baseline import cmd_curves
from scripts.l2_token_regression import write_training_curves
from tests.test_townlet.regressions.fixtures.episode_lanes import LEVEL_NAME
from tests.test_townlet.regressions.test_episode_lane_sinks import events_for, run_lane_runner
from townlet.demo.database import DemoDatabase
from townlet.demo.live_inference import LiveInferenceServer
from townlet.demo.runner import DemoRunner
from townlet.recording.data_structures import EpisodeEndMarker, RecordedStep
from townlet.recording.recorder import RecordingWriter
from townlet.recording.replay import ReplayManager

REWARD_FIELDS = {
    "reward": "total_reward",
    "extrinsic_reward": "extrinsic_reward",
    "intrinsic_reward": "intrinsic_reward",
    "shaping_reward": "shaping_reward",
}
CURVE_HEADER = (
    "episode,survival_steps_agent0,batch_episode_steps,live_agent_transitions,"
    "total_live_agent_transitions_cumulative,epsilon,intrinsic_weight"
)


def _json_value(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return value.tolist()
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _unpack(path: Path) -> dict:
    return msgpack.unpackb(lz4.frame.decompress(path.read_bytes()), raw=False)


@dataclass
class PersistedRun:
    root: Path
    runner: DemoRunner
    ticks: list[dict]
    episodes: list[dict]
    recordings: list[dict]
    payloads: list[dict]
    accepted: list[RecordedStep | EpisodeEndMarker]
    outcome: dict


@pytest.fixture(scope="module")
def persisted_run(tmp_path_factory: pytest.TempPathFactory):
    """Use ordinary public cleanup, then inspect once before any replay/export opens."""
    root = tmp_path_factory.mktemp("episode-lane-artifacts")
    run_dir = root / "run"
    accepted: list[RecordedStep | EpisodeEndMarker] = []
    dequeued: list[RecordedStep | EpisodeEndMarker] = []
    original_put, original_get = queue.Queue._put, queue.Queue._get
    source_root = Path(__file__).resolve().parents[3]
    source_paths = {
        model.__name__: Path(inspect.getfile(model)).resolve()
        for model in (DemoRunner, DemoDatabase, RecordedStep, RecordingWriter, ReplayManager, LiveInferenceServer)
    }
    outcome: dict = {
        "status": "started",
        "revision": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=source_root, check=True, capture_output=True, text=True
        ).stdout.strip(),
        "source_identity": {
            name: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for name, path in source_paths.items()
        },
    }

    def put(real_queue: queue.Queue, item: Any) -> None:
        original_put(real_queue, item)
        if isinstance(item, (RecordedStep, EpisodeEndMarker)):
            accepted.append(item)

    def get(real_queue: queue.Queue) -> Any:
        item = original_get(real_queue)
        if isinstance(item, (RecordedStep, EpisodeEndMarker)):
            dequeued.append(item)
        return item

    try:
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.chdir(root)
            monkeypatch.setattr(queue.Queue, "_put", put)
            monkeypatch.setattr(queue.Queue, "_get", get)
            runner, ticks, _ = run_lane_runner(run_dir, episodes=2, budget=None, cap=None, end_ticks=(2, 5), real_dac=True, recording=True)
        assert runner.recorder is not None
        recorder = runner.recorder
        with recorder.queue.mutex:
            outstanding = list(recorder.queue.queue)
        with closing(sqlite3.connect(runner.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            episodes = [dict(row) for row in connection.execute("SELECT * FROM episodes ORDER BY episode_id")]
            recordings = [dict(row) for row in connection.execute("SELECT * FROM episode_recordings ORDER BY episode_id")]
        payloads = []
        files = []
        for recording in recordings:
            path = runner.checkpoint_dir / recording["file_path"]
            files.append({"path": str(path), "exists": path.is_file()})
            if path.is_file():
                compressed = path.read_bytes()
                serialized = lz4.frame.decompress(compressed)
                payloads.append(msgpack.unpackb(serialized, raw=False))
                files[-1].update(
                    sha256=hashlib.sha256(compressed).hexdigest(), compressed_size=len(compressed), serialized_size=len(serialized)
                )
        outcome.update(
            accepted=[{"kind": type(item).__name__, "data": asdict(item)} for item in accepted],
            dequeued=[{"kind": type(item).__name__, "data": asdict(item)} for item in dequeued],
            outstanding=[{"kind": type(item).__name__, "data": asdict(item)} for item in outstanding],
            buffered=[asdict(item) for item in recorder.writer.episode_buffer],
            writer_alive=recorder.writer_thread.is_alive(),
            files=files,
            episodes=episodes,
            recordings=recordings,
            ticks=_json_value(ticks),
            realized_live_agent_steps=runner.completed_live_agent_steps,
            config_sha256={
                str(path.relative_to(run_dir / "pack")): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted((run_dir / "pack").rglob("*.yaml"))
            },
        )
        (root / "ordinary-cleanup.json").write_text(json.dumps(outcome, indent=2) + "\n")
        assert not outcome["writer_alive"], f"ORDINARY_RECORDING_LOSS: {outcome}"
        assert not outstanding and not recorder.writer.episode_buffer, f"ORDINARY_RECORDING_LOSS: {outcome}"
        assert [id(item) for item in dequeued] == [id(item) for item in accepted], f"ORDINARY_RECORDING_LOSS: {outcome}"
        assert len(recordings) == len(payloads) == 2, f"ORDINARY_RECORDING_LOSS: {outcome}"
        assert len([item for item in accepted if isinstance(item, RecordedStep)]) == 4
        assert len([item for item in accepted if isinstance(item, EpisodeEndMarker)]) == 2
        assert len(episodes) == runner.current_episode == 2
        assert runner.completed_live_agent_steps == sum(int(item["active"].sum()) for item in ticks) == 14
        # Realized metadata is measured from this actual runner, never synthesized from batch size.
        (run_dir / "meta.json").write_text(json.dumps({"realized_live_agent_steps": runner.completed_live_agent_steps}) + "\n")
        outcome["status"] = "ordinary_cleanup_passed"
        yield PersistedRun(root, runner, ticks, episodes, recordings, payloads, accepted, outcome)
    except BaseException as error:
        outcome.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        (root / "ordinary-cleanup.json").write_text(json.dumps(outcome, indent=2) + "\n")
        evidence_dir = os.environ.get("EPISODE_LANE_ARTIFACT_EVIDENCE_DIR")
        if evidence_dir is not None:
            shutil.copytree(root, Path(evidence_dir) / root.name)


def _assert_payload_ledger(data: dict, ticks: list[dict], action_ids: dict[str, int]) -> None:
    """Independent semantic proof; structural validation cannot infer true eligibility."""
    metadata = data["metadata"]
    observed = [item for item in ticks if item["episode"] == metadata["episode_id"] and bool(item["active"][0])]
    assert data["version"] == 2
    assert metadata["completion_reason"] == "authored_terminal"
    assert len(data["steps"]) == metadata["survival_steps"] == len(observed) == 2
    usage = Counter(int(item["actions"][0]) for item in observed)
    assert metadata["custom_action_uses"] == {name: usage[number] for name, number in action_ids.items() if usage[number]}
    for index, (frame, tick) in enumerate(zip(data["steps"], observed, strict=True)):
        assert frame["step"] == index
        assert frame["action"] == int(tick["actions"][0])
        assert frame["done"] == bool(tick["dones"][0])
        assert frame["meters"] == pytest.approx(tick["meters"][0].tolist())
        assert frame["reward"] == pytest.approx(float(tick["rewards"][0]), rel=1e-5, abs=1e-6)
        for name in ("extrinsic", "intrinsic", "shaping"):
            assert frame[f"{name}_reward"] == pytest.approx(float(tick["components"][name][0]), rel=1e-5, abs=1e-6)
    for frame_key, metadata_key in REWARD_FIELDS.items():
        assert metadata[metadata_key] == pytest.approx(math.fsum(frame[frame_key] for frame in data["steps"]), rel=1e-5, abs=1e-6)
    assert data["steps"][0]["reward"] > 0.0
    assert data["steps"][0]["shaping_reward"] > 0.0
    assert data["steps"][1]["reward"] == 0.0


def test_ordinary_two_episode_files_index_sql_and_tb_match_actual_eligible_ledger(persisted_run: PersistedRun) -> None:
    run = persisted_run
    assert run.runner.env is not None
    accumulator = events_for(run.runner)
    accepted = iter(run.accepted)
    for episode, (payload, recording, row) in enumerate(zip(run.payloads, run.recordings, run.episodes, strict=True)):
        queued_frames = []
        for item in accepted:
            if isinstance(item, EpisodeEndMarker):
                marker = item
                break
            queued_frames.append(asdict(item))
        queued = msgpack.unpackb(msgpack.packb({"metadata": asdict(marker.metadata), "steps": queued_frames}), raw=False)
        assert payload["metadata"] == queued["metadata"]
        assert payload["steps"] == queued["steps"]
        _assert_payload_ledger(payload, run.ticks, run.runner.env.action_ids)
        observed = [item for item in run.ticks if item["episode"] == episode]
        assert torch.stack([item["active"] for item in observed]).sum(dim=0).tolist() == [2, 5]
        assert row["survival_time"] == recording["survival_steps"] == 2
        assert row["batch_episode_steps"] == 5
        assert row["live_agent_transitions"] == 7
        assert row["completion_reason"] == recording["completion_reason"] == "authored_terminal"
        path = run.runner.checkpoint_dir / recording["file_path"]
        assert recording["compressed_size_bytes"] == len(path.read_bytes())
        assert recording["file_size_bytes"] == len(lz4.frame.decompress(path.read_bytes()))
        for metadata_key in (*REWARD_FIELDS.values(), "timestamp", "curriculum_stage", "epsilon", "intrinsic_weight"):
            assert recording[metadata_key] == pytest.approx(payload["metadata"][metadata_key], rel=1e-5, abs=1e-6)
        for agent in range(2):
            assert accumulator.Scalars(f"agent_{agent}/Episode/Survival_Time")[episode].value == (2, 5)[agent]
            for frame_key, metadata_key in REWARD_FIELDS.items():
                values = [
                    float(item["rewards"][agent] if frame_key == "reward" else item["components"][frame_key.removesuffix("_reward")][agent])
                    for item in observed
                    if bool(item["active"][agent])
                ]
                total = math.fsum(values)
                tag = "Total" if frame_key == "reward" else frame_key.removesuffix("_reward").title()
                assert accumulator.Scalars(f"agent_{agent}/Episode/{tag}_Reward")[episode].value == pytest.approx(total, rel=1e-5, abs=1e-6)
                if agent == 0:
                    assert row[metadata_key] == pytest.approx(total, rel=1e-5, abs=1e-6)


@pytest.mark.asyncio
async def test_actual_replay_manager_and_observer_seek_back_reset_and_episode_reload(
    persisted_run: PersistedRun, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = persisted_run
    with DemoDatabase(run.runner.db_path) as database:
        replay = ReplayManager(database, run.runner.checkpoint_dir)
        for episode, payload in enumerate(run.payloads):
            assert replay.load_episode(episode)
            assert replay.steps == payload["steps"]
            for index in (0, 1, 0, 1):
                assert replay.seek(index)
                assert replay.get_current_cumulative_reward() == pytest.approx(
                    sum(frame["reward"] for frame in payload["steps"][: index + 1])
                )
            replay.reset()
            assert replay.get_current_cumulative_reward() == pytest.approx(payload["steps"][0]["reward"])
    monkeypatch.chdir(run.root)

    class Transport:
        def __init__(self) -> None:
            self.messages: list[dict] = []

        async def send_json(self, message: dict) -> None:
            self.messages.append(copy.deepcopy(message))

    server = LiveInferenceServer(
        checkpoint_dir=run.runner.checkpoint_dir,
        level_name=LEVEL_NAME,
        port=8766,
        step_delay=0.01,
        total_episodes=2,
        config_dir=run.runner.config_dir,
        db_path=run.runner.db_path,
        recordings_dir=run.runner.checkpoint_dir,
    )
    client = Transport()
    server.clients.add(client)
    try:
        await server.startup()
        for episode in (0, 1, 0):
            payload = run.payloads[episode]
            await server._handle_load_replay(client, {"episode_id": episode})
            loaded = client.messages[-2]
            assert loaded["type"] == "replay_loaded" and loaded["total_steps"] == 2
            assert loaded["metadata"]["completion_reason"] == "authored_terminal"
            for index in (0, 1, 0, 1):
                await server._handle_replay_control(client, {"action": "seek", "seek_step": index})
                update = client.messages[-1]
                frame = payload["steps"][index]
                assert update["type"] == "state_update" and update["mode"] == "replay"
                assert update["episode_id"] == episode and update["step"] == frame["step"]
                for name in REWARD_FIELDS:
                    assert update[name] == frame[name]
                assert update["cumulative_reward"] == pytest.approx(sum(item["reward"] for item in payload["steps"][: index + 1]))
                agent = update["grid"]["agents"][0]
                assert (agent["x"], agent["y"]) == tuple(frame["position"])
                assert agent["last_action"] == frame["action"]
                assert list(update["agent_meters"]["agent_0"]["meters"].values()) == frame["meters"]
                assert update["replay_metadata"]["current_step"] == index
                assert update["replay_metadata"]["completion_reason"] == payload["metadata"]["completion_reason"]
                for name in REWARD_FIELDS.values():
                    assert update["replay_metadata"][name] == payload["metadata"][name]
                if frame["q_values"]:
                    assert update["q_values"] == frame["q_values"]
                for name in ("time_of_day", "interaction_progress"):
                    if frame[name] is not None:
                        assert update[name] == frame[name]
            await server._handle_command(client, {"command": "reset"})
            assert client.messages[-1]["replay_metadata"]["current_step"] == 0
            assert client.messages[-1]["cumulative_reward"] == pytest.approx(payload["steps"][0]["reward"])
        (run.root / "observer-messages.json").write_text(json.dumps(client.messages, indent=2) + "\n")
    finally:
        await server.shutdown()
        assert server.replay_manager is not None
        server.replay_manager.database.close()
        assert server._qvalue_log_file is None


def test_both_real_exporters_use_same_run_and_actual_fourteen_transition_metadata(persisted_run: PersistedRun) -> None:
    run = persisted_run
    run_dir = run.runner.db_path.parent
    cmd_curves(argparse.Namespace(run_dir=str(run_dir)))
    baseline = (run_dir / "curves.csv").read_text()
    (run.root / "baseline-curves.csv").write_text(baseline)
    write_training_curves(run_dir)
    token = (run_dir / "curves.csv").read_text()
    assert token == baseline
    assert token.splitlines()[0] == CURVE_HEADER
    rows = list(csv.DictReader(token.splitlines()))
    assert [(int(row["survival_steps_agent0"]), int(row["batch_episode_steps"]), int(row["live_agent_transitions"])) for row in rows] == [
        (2, 5, 7),
        (2, 5, 7),
    ]
    assert [int(row["total_live_agent_transitions_cumulative"]) for row in rows] == [7, 14]
    transitions = list(csv.DictReader((run_dir / "transitions.csv").read_text().splitlines()))
    assert int(transitions[-1]["completed_live_agent_steps"]) == 14
    assert json.loads((run_dir / "meta.json").read_text())["realized_live_agent_steps"] == 14


@pytest.mark.parametrize(
    "corruption", ["schema", "reason", "missing_component", "nan", "sum", "phantom", "consistent_phantom", "raw_intrinsic"]
)
def test_copied_real_artifact_corruption_is_refused_or_detected_against_ledger(persisted_run: PersistedRun, corruption: str) -> None:
    run = persisted_run
    assert run.runner.env is not None
    original = run.runner.checkpoint_dir / run.recordings[0]["file_path"]
    original_digest = hashlib.sha256(original.read_bytes()).hexdigest()
    _assert_payload_ledger(_unpack(original), run.ticks, run.runner.env.action_ids)
    root = run.root / f"corruption-{corruption}"
    target = root / "checkpoints" / run.recordings[0]["file_path"]
    target.parent.mkdir(parents=True)
    shutil.copy2(run.runner.db_path, root / "demo.db")
    data = copy.deepcopy(_unpack(original))
    semantic = corruption in {"consistent_phantom", "raw_intrinsic"}
    if corruption == "schema":
        data["version"] = 1
    elif corruption == "reason":
        data["metadata"]["completion_reason"] = "unsupported"
    elif corruption == "missing_component":
        del data["steps"][0]["shaping_reward"]
    elif corruption == "nan":
        data["steps"][0]["reward"] = float("nan")
    elif corruption == "sum":
        data["steps"][0]["reward"] += 1.0
    elif corruption in {"phantom", "consistent_phantom"}:
        frame = copy.deepcopy(data["steps"][-1])
        if semantic:
            data["steps"][-1]["done"] = False
            frame["step"] = 2
            data["metadata"]["survival_steps"] = 3
        data["steps"].append(frame)
    elif corruption == "raw_intrinsic":
        frame = data["steps"][0]
        raw = float(run.ticks[0]["components"]["intrinsic_raw"][0])
        assert raw != frame["intrinsic_reward"]
        delta = raw - frame["intrinsic_reward"]
        frame["intrinsic_reward"] = raw
        frame["reward"] += delta
        data["metadata"]["intrinsic_reward"] += delta
        data["metadata"]["total_reward"] += delta
    target.write_bytes(lz4.frame.compress(msgpack.packb(data, use_bin_type=True)))
    with DemoDatabase(root / "demo.db") as database:
        replay = ReplayManager(database, root / "checkpoints")
        loaded = replay.load_episode(0)
        if semantic:
            assert loaded
            with pytest.raises(AssertionError):
                _assert_payload_ledger(_unpack(target), run.ticks, run.runner.env.action_ids)
        else:
            assert not loaded
            assert replay.episode_id is None and not replay.steps and replay.metadata is None
    assert hashlib.sha256(original.read_bytes()).hexdigest() == original_digest
    (root / "outcome.json").write_text(json.dumps({"reader_loaded": loaded, "independent_ledger_detected": semantic}) + "\n")
