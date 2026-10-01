"""
Tests for ReplayManager.

Tests loading and controlling episode replay.
"""

import tempfile
import time
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import lz4.frame
import msgpack
import pytest

from tests.test_townlet.utils.builders import make_test_recording_payload


class TestReplayManager:
    """Test ReplayManager functionality."""

    def test_replay_manager_initialization(self):
        """ReplayManager should initialize with database and directory."""
        from townlet.demo.database import DemoDatabase
        from townlet.recording.replay import ReplayManager

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            recordings_dir = tmpdir_path / "recordings"
            recordings_dir.mkdir()

            db = DemoDatabase(db_path)
            replay = ReplayManager(db, recordings_dir)

            assert replay.database is db
            assert replay.recordings_base_dir == recordings_dir
            assert replay.is_loaded() is False
            # Close database to prevent resource warnings
            db.close()

    def test_load_episode_from_file(self):
        """ReplayManager should load and decompress episode."""
        from townlet.demo.database import DemoDatabase
        from townlet.recording.data_structures import EpisodeMetadata, RecordedStep
        from townlet.recording.replay import ReplayManager

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            recordings_dir = tmpdir_path / "recordings"
            recordings_dir.mkdir()

            # Create database and recording
            db = DemoDatabase(db_path)

            # Create sample episode
            metadata = EpisodeMetadata(
                episode_id=100,
                survival_steps=10,
                total_reward=10.0,
                extrinsic_reward=9.5,
                intrinsic_reward=0.5,
                curriculum_stage=1,
                epsilon=0.1,
                intrinsic_weight=0.5,
                timestamp=time.time(),
                affordance_layout={"Bed": (2, 3)},
                affordance_visits={"Bed": 1},
                custom_action_uses={},
                completion_reason="authored_terminal",
                shaping_reward=0.0,
            )

            steps = [
                RecordedStep(
                    step=i,
                    position=(3, 4),
                    meters=(0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1),
                    action=i % 6,
                    reward=1.0,
                    intrinsic_reward=0.05,
                    done=(i == 9),
                    q_values=(0.1, 0.2, 0.3, 0.4, 0.5),
                    extrinsic_reward=0.95,
                    shaping_reward=0.0,
                )
                for i in range(10)
            ]

            # Serialize and write
            metadata = replace(
                metadata,
                survival_steps=len(steps),
                total_reward=sum(step.reward for step in steps),
                extrinsic_reward=sum(step.extrinsic_reward for step in steps),
                intrinsic_reward=sum(step.intrinsic_reward for step in steps),
                shaping_reward=sum(step.shaping_reward for step in steps),
            )
            episode_data = {
                "version": 2,
                "metadata": asdict(metadata),
                "steps": [asdict(step) for step in steps],
                "affordances": metadata.affordance_layout,
            }
            serialized = msgpack.packb(episode_data, use_bin_type=True)
            compressed = lz4.frame.compress(serialized, compression_level=0)

            file_path = recordings_dir / "episode_000100.msgpack.lz4"
            file_path.write_bytes(compressed)

            # Insert into database
            db.insert_recording(
                episode_id=100,
                file_path=str(file_path.relative_to(tmpdir_path)),
                metadata=metadata,
                reason="periodic_100",
                file_size=len(serialized),
                compressed_size=len(compressed),
            )

            # Load with ReplayManager
            replay = ReplayManager(db, tmpdir_path)
            success = replay.load_episode(100)

            assert success is True
            assert replay.is_loaded() is True
            assert replay.episode_id == 100
            assert replay.get_total_steps() == 10
            assert replay.get_metadata()["episode_id"] == 100
            assert replay.get_affordances() == {"Bed": [2, 3]}  # msgpack converts tuples to lists
            # Close database to prevent resource warnings
            db.close()

    def test_load_nonexistent_episode(self):
        """ReplayManager should return False for nonexistent episode."""
        from townlet.demo.database import DemoDatabase
        from townlet.recording.replay import ReplayManager

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            recordings_dir = tmpdir_path / "recordings"
            recordings_dir.mkdir()

            db = DemoDatabase(db_path)
            replay = ReplayManager(db, recordings_dir)

            success = replay.load_episode(999)
            assert success is False
            assert replay.is_loaded() is False
            # Close database to prevent resource warnings
            db.close()

    def test_replay_step_progression(self):
        """ReplayManager should advance through steps."""
        from townlet.demo.database import DemoDatabase
        from townlet.recording.data_structures import EpisodeMetadata, RecordedStep
        from townlet.recording.replay import ReplayManager

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            recordings_dir = tmpdir_path / "recordings"
            recordings_dir.mkdir()

            db = DemoDatabase(db_path)

            # Create minimal episode
            metadata = EpisodeMetadata(
                episode_id=200,
                survival_steps=5,
                total_reward=5.0,
                extrinsic_reward=5.0,
                intrinsic_reward=0.0,
                curriculum_stage=1,
                epsilon=0.1,
                intrinsic_weight=0.5,
                timestamp=time.time(),
                affordance_layout={},
                affordance_visits={},
                custom_action_uses={},
                completion_reason="authored_terminal",
                shaping_reward=0.0,
            )

            steps = [
                RecordedStep(
                    step=i,
                    position=(i, i),
                    meters=(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
                    action=0,
                    reward=1.0,
                    intrinsic_reward=0.0,
                    done=(i == 4),
                    q_values=None,
                    extrinsic_reward=1.0,
                    shaping_reward=0.0,
                )
                for i in range(5)
            ]

            metadata = replace(
                metadata,
                survival_steps=len(steps),
                total_reward=sum(step.reward for step in steps),
                extrinsic_reward=sum(step.extrinsic_reward for step in steps),
                intrinsic_reward=sum(step.intrinsic_reward for step in steps),
                shaping_reward=sum(step.shaping_reward for step in steps),
            )
            episode_data = {
                "version": 2,
                "metadata": asdict(metadata),
                "steps": [asdict(step) for step in steps],
                "affordances": {},
            }
            serialized = msgpack.packb(episode_data, use_bin_type=True)
            compressed = lz4.frame.compress(serialized)

            file_path = recordings_dir / "episode_000200.msgpack.lz4"
            file_path.write_bytes(compressed)

            db.insert_recording(
                episode_id=200,
                file_path=str(file_path.relative_to(tmpdir_path)),
                metadata=metadata,
                reason="test",
                file_size=len(serialized),
                compressed_size=len(compressed),
            )

            # Load and step through
            replay = ReplayManager(db, tmpdir_path)
            replay.load_episode(200)

            # Initially at step 0
            assert replay.get_current_step_index() == 0
            step = replay.get_current_step()
            assert step["step"] == 0
            assert step["position"] == [0, 0]  # msgpack converts tuples to lists

            # Advance to step 1
            next_step = replay.next_step()
            assert replay.get_current_step_index() == 1
            assert next_step["step"] == 1
            assert next_step["position"] == [1, 1]

            # Advance to step 2
            next_step = replay.next_step()
            assert replay.get_current_step_index() == 2
            # Close database to prevent resource warnings
            db.close()

    def test_replay_at_end(self):
        """ReplayManager should detect end of episode."""
        from townlet.demo.database import DemoDatabase
        from townlet.recording.data_structures import EpisodeMetadata, RecordedStep
        from townlet.recording.replay import ReplayManager

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            recordings_dir = tmpdir_path / "recordings"
            recordings_dir.mkdir()

            db = DemoDatabase(db_path)

            # Create 3-step episode
            metadata = EpisodeMetadata(
                episode_id=300,
                survival_steps=3,
                total_reward=3.0,
                extrinsic_reward=3.0,
                intrinsic_reward=0.0,
                curriculum_stage=1,
                epsilon=0.1,
                intrinsic_weight=0.5,
                timestamp=time.time(),
                affordance_layout={},
                affordance_visits={},
                custom_action_uses={},
                completion_reason="authored_terminal",
                shaping_reward=0.0,
            )

            steps = [
                RecordedStep(
                    step=i,
                    position=(0, 0),
                    meters=(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
                    action=0,
                    reward=1.0,
                    intrinsic_reward=0.0,
                    done=(i == 2),
                    q_values=None,
                    extrinsic_reward=1.0,
                    shaping_reward=0.0,
                )
                for i in range(3)
            ]

            metadata = replace(
                metadata,
                survival_steps=len(steps),
                total_reward=sum(step.reward for step in steps),
                extrinsic_reward=sum(step.extrinsic_reward for step in steps),
                intrinsic_reward=sum(step.intrinsic_reward for step in steps),
                shaping_reward=sum(step.shaping_reward for step in steps),
            )
            episode_data = {
                "version": 2,
                "metadata": asdict(metadata),
                "steps": [asdict(step) for step in steps],
                "affordances": {},
            }
            serialized = msgpack.packb(episode_data, use_bin_type=True)
            compressed = lz4.frame.compress(serialized)

            file_path = recordings_dir / "episode_000300.msgpack.lz4"
            file_path.write_bytes(compressed)

            db.insert_recording(
                episode_id=300,
                file_path=str(file_path.relative_to(tmpdir_path)),
                metadata=metadata,
                reason="test",
                file_size=len(serialized),
                compressed_size=len(compressed),
            )

            # Load and advance to end
            replay = ReplayManager(db, tmpdir_path)
            replay.load_episode(300)

            assert replay.is_at_end() is False

            replay.next_step()  # step 1
            replay.next_step()  # step 2
            replay.next_step()  # past end

            assert replay.is_at_end() is True
            assert replay.get_current_step() is None
            # Close database to prevent resource warnings
            db.close()

    def test_replay_seek(self):
        """ReplayManager should support seeking."""
        from townlet.demo.database import DemoDatabase
        from townlet.recording.data_structures import EpisodeMetadata, RecordedStep
        from townlet.recording.replay import ReplayManager

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            recordings_dir = tmpdir_path / "recordings"
            recordings_dir.mkdir()

            db = DemoDatabase(db_path)

            # Create 10-step episode
            metadata = EpisodeMetadata(
                episode_id=400,
                survival_steps=10,
                total_reward=10.0,
                extrinsic_reward=10.0,
                intrinsic_reward=0.0,
                curriculum_stage=1,
                epsilon=0.1,
                intrinsic_weight=0.5,
                timestamp=time.time(),
                affordance_layout={},
                affordance_visits={},
                custom_action_uses={},
                completion_reason="authored_terminal",
                shaping_reward=0.0,
            )

            steps = [
                RecordedStep(
                    step=i,
                    position=(0, 0),
                    meters=(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
                    action=0,
                    reward=1.0,
                    intrinsic_reward=0.0,
                    done=(i == 9),
                    q_values=None,
                    extrinsic_reward=1.0,
                    shaping_reward=0.0,
                )
                for i in range(10)
            ]

            metadata = replace(
                metadata,
                survival_steps=len(steps),
                total_reward=sum(step.reward for step in steps),
                extrinsic_reward=sum(step.extrinsic_reward for step in steps),
                intrinsic_reward=sum(step.intrinsic_reward for step in steps),
                shaping_reward=sum(step.shaping_reward for step in steps),
            )
            episode_data = {
                "version": 2,
                "metadata": asdict(metadata),
                "steps": [asdict(step) for step in steps],
                "affordances": {},
            }
            serialized = msgpack.packb(episode_data, use_bin_type=True)
            compressed = lz4.frame.compress(serialized)

            file_path = recordings_dir / "episode_000400.msgpack.lz4"
            file_path.write_bytes(compressed)

            db.insert_recording(
                episode_id=400,
                file_path=str(file_path.relative_to(tmpdir_path)),
                metadata=metadata,
                reason="test",
                file_size=len(serialized),
                compressed_size=len(compressed),
            )

            # Load and seek
            replay = ReplayManager(db, tmpdir_path)
            replay.load_episode(400)

            # Seek to step 5
            success = replay.seek(5)
            assert success is True
            assert replay.get_current_step_index() == 5
            assert replay.get_current_step()["step"] == 5

            # Seek to beginning
            success = replay.seek(0)
            assert success is True
            assert replay.get_current_step_index() == 0

            # Seek out of bounds
            success = replay.seek(100)
            assert success is False
            assert replay.get_current_step_index() == 0  # Unchanged
            # Close database to prevent resource warnings
            db.close()

    def test_replay_reset(self):
        """ReplayManager should reset to beginning."""
        from townlet.demo.database import DemoDatabase
        from townlet.recording.data_structures import EpisodeMetadata, RecordedStep
        from townlet.recording.replay import ReplayManager

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            recordings_dir = tmpdir_path / "recordings"
            recordings_dir.mkdir()

            db = DemoDatabase(db_path)

            # Create episode
            metadata = EpisodeMetadata(
                episode_id=500,
                survival_steps=5,
                total_reward=5.0,
                extrinsic_reward=5.0,
                intrinsic_reward=0.0,
                curriculum_stage=1,
                epsilon=0.1,
                intrinsic_weight=0.5,
                timestamp=time.time(),
                affordance_layout={},
                affordance_visits={},
                custom_action_uses={},
                completion_reason="authored_terminal",
                shaping_reward=0.0,
            )

            steps = [
                RecordedStep(
                    step=i,
                    position=(0, 0),
                    meters=(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
                    action=0,
                    reward=1.0,
                    intrinsic_reward=0.0,
                    done=(i == 4),
                    q_values=None,
                    extrinsic_reward=1.0,
                    shaping_reward=0.0,
                )
                for i in range(5)
            ]

            metadata = replace(
                metadata,
                survival_steps=len(steps),
                total_reward=sum(step.reward for step in steps),
                extrinsic_reward=sum(step.extrinsic_reward for step in steps),
                intrinsic_reward=sum(step.intrinsic_reward for step in steps),
                shaping_reward=sum(step.shaping_reward for step in steps),
            )
            episode_data = {
                "version": 2,
                "metadata": asdict(metadata),
                "steps": [asdict(step) for step in steps],
                "affordances": {},
            }
            serialized = msgpack.packb(episode_data, use_bin_type=True)
            compressed = lz4.frame.compress(serialized)

            file_path = recordings_dir / "episode_000500.msgpack.lz4"
            file_path.write_bytes(compressed)

            db.insert_recording(
                episode_id=500,
                file_path=str(file_path.relative_to(tmpdir_path)),
                metadata=metadata,
                reason="test",
                file_size=len(serialized),
                compressed_size=len(compressed),
            )

            # Load, advance, then reset
            replay = ReplayManager(db, tmpdir_path)
            replay.load_episode(500)

            replay.next_step()
            replay.next_step()
            assert replay.get_current_step_index() == 2

            replay.reset()
            assert replay.get_current_step_index() == 0
            assert replay.playing is False
            # Close database to prevent resource warnings
            db.close()

    def test_replay_unload(self):
        """ReplayManager should unload episode."""
        from townlet.demo.database import DemoDatabase
        from townlet.recording.data_structures import EpisodeMetadata, RecordedStep
        from townlet.recording.replay import ReplayManager

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            recordings_dir = tmpdir_path / "recordings"
            recordings_dir.mkdir()

            db = DemoDatabase(db_path)

            # Create episode
            metadata = EpisodeMetadata(
                episode_id=600,
                survival_steps=1,
                total_reward=1.0,
                extrinsic_reward=1.0,
                intrinsic_reward=0.0,
                curriculum_stage=1,
                epsilon=0.1,
                intrinsic_weight=0.5,
                timestamp=time.time(),
                affordance_layout={},
                affordance_visits={},
                custom_action_uses={},
                completion_reason="authored_terminal",
                shaping_reward=0.0,
            )

            steps = [
                RecordedStep(
                    step=0,
                    position=(0, 0),
                    meters=(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
                    action=0,
                    reward=1.0,
                    intrinsic_reward=0.0,
                    done=True,
                    q_values=None,
                    extrinsic_reward=1.0,
                    shaping_reward=0.0,
                )
            ]

            metadata = replace(
                metadata,
                survival_steps=len(steps),
                total_reward=sum(step.reward for step in steps),
                extrinsic_reward=sum(step.extrinsic_reward for step in steps),
                intrinsic_reward=sum(step.intrinsic_reward for step in steps),
                shaping_reward=sum(step.shaping_reward for step in steps),
            )
            episode_data = {
                "version": 2,
                "metadata": asdict(metadata),
                "steps": [asdict(step) for step in steps],
                "affordances": {},
            }
            serialized = msgpack.packb(episode_data, use_bin_type=True)
            compressed = lz4.frame.compress(serialized)

            file_path = recordings_dir / "episode_000600.msgpack.lz4"
            file_path.write_bytes(compressed)

            db.insert_recording(
                episode_id=600,
                file_path=str(file_path.relative_to(tmpdir_path)),
                metadata=metadata,
                reason="test",
                file_size=len(serialized),
                compressed_size=len(compressed),
            )

            # Load and unload
            replay = ReplayManager(db, tmpdir_path)
            replay.load_episode(600)
            assert replay.is_loaded() is True

            replay.unload()
            assert replay.is_loaded() is False
            assert replay.episode_id is None
            assert replay.get_total_steps() == 0
            # Close database to prevent resource warnings
            db.close()


def _index_raw_recording(db, directory: Path, payload: dict) -> Path:
    """Use the real file codec and database without constructing the DTO under test."""
    episode_id = payload["metadata"]["episode_id"]
    path = directory / f"episode_{episode_id:06d}.msgpack.lz4"
    serialized = msgpack.packb(payload, use_bin_type=True)
    compressed = lz4.frame.compress(serialized)
    path.write_bytes(compressed)
    db.insert_recording(
        episode_id=episode_id,
        file_path=path.name,
        metadata=SimpleNamespace(**payload["metadata"]),
        reason="periodic",
        file_size=len(serialized),
        compressed_size=len(compressed),
    )
    return path


@pytest.mark.parametrize("reason", ["authored_terminal", "retirement", "cap", "budget", "shutdown", "checkpoint"])
def test_current_recording_preserves_components_completion_and_selected_prefix(tmp_path: Path, reason: str) -> None:
    from townlet.demo.database import DemoDatabase
    from townlet.recording.replay import ReplayManager

    with DemoDatabase(tmp_path / "demo.db") as db:
        payload = make_test_recording_payload(episode_id=7, completion_reason=reason)
        _index_raw_recording(db, tmp_path, payload)
        replay = ReplayManager(db, tmp_path)
        assert replay.load_episode(7)
        assert replay.get_metadata()["completion_reason"] == reason
        assert replay.get_metadata()["shaping_reward"] == 0.2
        row = db.get_recording(7)
        assert row["recording_reason"] == "periodic"
        assert row["completion_reason"] == reason
        assert row["shaping_reward"] == 0.2
        prefix = getattr(replay, "get_current_cumulative_reward", None)
        assert callable(prefix), "ReplayManager must project the canonical selected-index prefix"
        assert prefix() == 1.0
        assert replay.next_step()["reward"] == 0.0
        assert prefix() == 1.0
        assert prefix() == 1.0
        assert replay.seek(0)
        assert prefix() == 1.0
        replay.reset()
        assert prefix() == 1.0
        replay.next_step()
        assert replay.next_step() is None
        with pytest.raises(ValueError, match="selected"):
            prefix()
        next_payload = make_test_recording_payload(episode_id=8, completion_reason="budget")
        for key in ("reward", "extrinsic_reward", "intrinsic_reward", "shaping_reward"):
            next_payload["steps"][0][key] *= 2
        for key in ("total_reward", "extrinsic_reward", "intrinsic_reward", "shaping_reward"):
            next_payload["metadata"][key] *= 2
        _index_raw_recording(db, tmp_path, next_payload)
        assert replay.load_episode(8)
        assert prefix() == 2.0
        replay.unload()
        with pytest.raises(ValueError, match="selected"):
            prefix()


_INVALID_RECORDINGS = [
    "version_1",
    "version_future",
    "version_bool",
    "unknown_top",
    "missing_affordances",
    "unknown_metadata",
    "unknown_step",
    "empty_frames",
    "frame_count",
    "episode_identity",
    "invalid_reason",
    "reason_type",
    "early_terminal",
    "missing_terminal",
    "truncation_terminal",
    "nonbool_done",
    "bad_step_number",
    "step_order",
    "enveloped_affordances",
    "layout_disagreement",
    "mixed_position_rank",
    "coordinate_type",
    "coordinate_bool",
    "reward_bool",
    "raw_novelty",
]
_INVALID_RECORDINGS += [
    f"missing_metadata_{key}" for key in make_test_recording_payload(episode_id=1, completion_reason="budget")["metadata"]
]
_INVALID_RECORDINGS += [f"missing_step_{key}" for key in make_test_recording_payload(episode_id=1, completion_reason="budget")["steps"][0]]
_INVALID_RECORDINGS += [f"frame_mismatch_{key}" for key in ("reward", "extrinsic_reward", "intrinsic_reward", "shaping_reward")]
_INVALID_RECORDINGS += [f"metadata_mismatch_{key}" for key in ("total_reward", "extrinsic_reward", "intrinsic_reward", "shaping_reward")]
_INVALID_RECORDINGS += [
    f"{scope}_nonfinite_{key}_{value}"
    for scope, keys in (
        ("frame", ("reward", "extrinsic_reward", "intrinsic_reward", "shaping_reward")),
        ("metadata", ("total_reward", "extrinsic_reward", "intrinsic_reward", "shaping_reward")),
    )
    for key in keys
    for value in ("nan", "inf", "negative_inf")
]


def _invalidate_recording(payload: dict, control: str) -> None:
    metadata, steps = payload["metadata"], payload["steps"]
    if control.startswith("missing_metadata_"):
        del metadata[control.removeprefix("missing_metadata_")]
    elif control.startswith("missing_step_"):
        del steps[0][control.removeprefix("missing_step_")]
    elif control.startswith("frame_mismatch_"):
        steps[0][control.removeprefix("frame_mismatch_")] += 0.01
    elif control.startswith("metadata_mismatch_"):
        metadata[control.removeprefix("metadata_mismatch_")] += 0.01
    elif "_nonfinite_" in control:
        scope, remainder = control.split("_nonfinite_", 1)
        for label, number in (("negative_inf", -float("inf")), ("nan", float("nan")), ("inf", float("inf"))):
            if remainder.endswith("_" + label):
                key = remainder.removesuffix("_" + label)
                (steps[0] if scope == "frame" else metadata)[key] = number
                break
    elif control.startswith("version_"):
        payload["version"] = {"version_1": 1, "version_future": 3, "version_bool": True}[control]
    elif control == "unknown_top":
        payload["historical_layout"] = {}
    elif control == "missing_affordances":
        del payload["affordances"]
    elif control == "unknown_metadata":
        metadata["recording_reason"] = "periodic"
    elif control == "unknown_step":
        steps[0]["active_on_entry"] = True
    elif control == "empty_frames":
        payload["steps"] = []
    elif control == "frame_count":
        metadata["survival_steps"] += 1
    elif control == "episode_identity":
        metadata["episode_id"] = 999
    elif control == "invalid_reason":
        metadata["completion_reason"] = "periodic"
    elif control == "reason_type":
        metadata["completion_reason"] = 1
    elif control == "early_terminal":
        steps[0]["done"] = True
    elif control == "missing_terminal":
        steps[-1]["done"] = False
    elif control == "truncation_terminal":
        metadata["completion_reason"] = "budget"
    elif control == "nonbool_done":
        steps[-1]["done"] = 1
    elif control == "bad_step_number":
        steps[0]["step"] = True
    elif control == "step_order":
        steps[1]["step"] = 0
    elif control == "enveloped_affordances":
        envelope = {"positions": {"Bed": [2, 3]}, "ordering": ["Bed"], "position_dim": 2}
        payload["affordances"] = metadata["affordance_layout"] = envelope
    elif control == "layout_disagreement":
        payload["affordances"] = {"Bed": [3, 4]}
    elif control == "mixed_position_rank":
        steps[0]["position"] = [3]
    elif control == "coordinate_type":
        metadata["affordance_layout"]["Bed"][0] = 1.5
    elif control == "coordinate_bool":
        steps[0]["position"][0] = True
    elif control == "reward_bool":
        steps[0]["reward"] = True
    elif control == "raw_novelty":
        steps[0]["intrinsic_reward"] = 3.0
    else:
        raise AssertionError(f"Unknown control: {control}")


@pytest.mark.parametrize("control", _INVALID_RECORDINGS)
def test_invalid_recording_refuses_before_installing_replay_state(tmp_path: Path, control: str) -> None:
    from townlet.demo.database import DemoDatabase
    from townlet.recording.replay import ReplayManager

    with DemoDatabase(tmp_path / "demo.db") as db:
        payload = make_test_recording_payload(episode_id=7, completion_reason="authored_terminal")
        path = _index_raw_recording(db, tmp_path, payload)
        replay = ReplayManager(db, tmp_path)
        assert replay.load_episode(7)
        replay.seek(1)
        replay.playing = True
        installed = (replay.episode_id, replay.metadata, replay.steps, replay.affordances, replay.current_step_index, replay.playing)
        _invalidate_recording(payload, control)
        path.write_bytes(lz4.frame.compress(msgpack.packb(payload, use_bin_type=True)))
        assert replay.load_episode(7) is False, f"Unsupported recording accepted: {control}"
        assert (
            replay.episode_id,
            replay.metadata,
            replay.steps,
            replay.affordances,
            replay.current_step_index,
            replay.playing,
        ) == installed
