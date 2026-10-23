"""
Tests for video export functionality.

Tests rendering frames and exporting to MP4.
"""

import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pytest


class TestVideoRenderer:
    """Test video frame rendering."""

    def test_renderer_initialization(self):
        """Renderer should initialize with grid size and style."""
        from townlet.recording.video_renderer import EpisodeVideoRenderer

        renderer = EpisodeVideoRenderer(grid_size=8, dpi=100, style="dark")

        assert renderer.grid_size == 8
        assert renderer.dpi == 100
        assert renderer.style == "dark"

    def test_render_simple_frame(self):
        """Renderer should produce numpy array frame."""
        from townlet.recording.video_renderer import EpisodeVideoRenderer

        renderer = EpisodeVideoRenderer(grid_size=8, dpi=100, style="dark")

        # Simple step data
        step_data = {
            "step": 0,
            "position": [3, 4],
            "meters": [0.8, 0.7, 0.6, 0.5, 0.9, 0.8, 0.7, 0.6],
            "action": 2,
            "reward": 1.0,
            "intrinsic_reward": 0.1,
            "done": False,
            "q_values": None,
        }

        metadata = {
            "episode_id": 100,
            "survival_steps": 50,
            "total_reward": 50.0,
            "curriculum_stage": 2,
        }

        affordances = {
            "Bed": [2, 3],
            "Job": [5, 6],
        }

        frame = renderer.render_frame(step_data, metadata, affordances)

        # Should return numpy array (RGB image)
        assert isinstance(frame, np.ndarray)
        assert frame.ndim == 3
        assert frame.shape[2] == 3  # RGB channels
        assert frame.dtype == np.uint8

    def test_render_frame_with_q_values(self):
        """Renderer should display Q-values if provided."""
        from townlet.recording.video_renderer import EpisodeVideoRenderer

        renderer = EpisodeVideoRenderer(grid_size=8, dpi=100, style="dark")

        step_data = {
            "step": 10,
            "position": [4, 4],
            "meters": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
            "action": 0,
            "reward": 1.0,
            "intrinsic_reward": 0.05,
            "done": False,
            "q_values": [0.1, 0.2, 0.3, 0.4, 0.5],
        }

        metadata = {
            "episode_id": 200,
            "survival_steps": 30,
            "total_reward": 30.0,
            "curriculum_stage": 1,
        }

        affordances = {}

        frame = renderer.render_frame(step_data, metadata, affordances)

        assert isinstance(frame, np.ndarray)
        assert frame.shape[2] == 3

    def test_render_frame_with_temporal_mechanics(self):
        """Renderer should display temporal mechanics info."""
        from townlet.recording.video_renderer import EpisodeVideoRenderer

        renderer = EpisodeVideoRenderer(grid_size=8, dpi=100, style="dark")

        step_data = {
            "step": 20,
            "position": [3, 3],
            "meters": [0.7, 0.6, 0.5, 0.4, 0.8, 0.7, 0.6, 0.5],
            "action": 4,
            "reward": 1.0,
            "intrinsic_reward": 0.0,
            "done": False,
            "q_values": None,
            "time_of_day": 12,  # Noon
            "interaction_progress": 0.5,
        }

        metadata = {
            "episode_id": 300,
            "survival_steps": 40,
            "total_reward": 40.0,
            "curriculum_stage": 3,
        }

        affordances = {"CoffeeShop": [1, 1]}

        frame = renderer.render_frame(step_data, metadata, affordances)

        assert isinstance(frame, np.ndarray)

    def test_renderer_consistent_dimensions(self):
        """Renderer should produce consistent frame dimensions."""
        from townlet.recording.video_renderer import EpisodeVideoRenderer

        renderer = EpisodeVideoRenderer(grid_size=8, dpi=100, style="dark")

        # Render multiple frames
        frames = []
        for i in range(5):
            step_data = {
                "step": i,
                "position": [i % 8, i % 8],
                "meters": [0.5] * 8,
                "action": i % 6,
                "reward": 1.0,
                "intrinsic_reward": 0.0,
                "done": False,
                "q_values": None,
            }

            metadata = {
                "episode_id": 400,
                "survival_steps": 10,
                "total_reward": 10.0,
                "curriculum_stage": 1,
            }

            frame = renderer.render_frame(step_data, metadata, {})
            frames.append(frame)

        # All frames should have same dimensions
        first_shape = frames[0].shape
        for frame in frames[1:]:
            assert frame.shape == first_shape


def _ffmpeg_available() -> bool:
    """Check if ffmpeg is available."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class TestVideoExport:
    """Test video export to MP4."""

    @pytest.mark.skipif(not _ffmpeg_available(), reason="ffmpeg not installed")
    def test_export_episode_to_mp4(self):
        """Should export episode to MP4 file."""
        import time
        from dataclasses import asdict, replace

        import lz4.frame
        import msgpack

        from townlet.demo.database import DemoDatabase
        from townlet.recording.data_structures import EpisodeMetadata, RecordedStep
        from townlet.recording.video_export import export_episode_video

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            recordings_dir = tmpdir_path / "recordings"
            recordings_dir.mkdir()

            # Create database and recording
            db = DemoDatabase(db_path)

            metadata = EpisodeMetadata(
                episode_id=500,
                survival_steps=10,
                total_reward=10.0,
                extrinsic_reward=10.0,
                intrinsic_reward=0.0,
                curriculum_stage=1,
                epsilon=0.1,
                intrinsic_weight=0.5,
                timestamp=time.time(),
                affordance_layout={"Bed": (2, 3)},
                affordance_visits={"Bed": 2},
                custom_action_uses={},
                completion_reason="authored_terminal",
                shaping_reward=0.0,
            )

            steps = [
                RecordedStep(
                    step=i,
                    position=(3 + i % 2, 4),
                    meters=(0.8, 0.7, 0.6, 0.5, 0.9, 0.8, 0.7, 0.6),
                    action=i % 6,
                    reward=1.0,
                    intrinsic_reward=0.0,
                    done=(i == 9),
                    q_values=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6),  # 6 actions: UP, DOWN, LEFT, RIGHT, INTERACT, WAIT
                    extrinsic_reward=1.0,
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

            # Close database to prevent resource warnings
            db.close()

            # Export video
            output_path = tmpdir_path / "episode_500.mp4"
            export_episode_video(
                episode_id=500,
                database_path=db_path,
                recordings_base_dir=tmpdir_path,
                output_path=output_path,
                fps=10,
                dpi=80,
            )

            # Verify file exists
            assert output_path.exists()
            assert output_path.stat().st_size > 0


class TestBatchExport:
    """Test batch video export."""

    def test_batch_export_filters(self):
        """Should export multiple episodes with filters."""
        # This is more of an integration test
        # Just verify the API exists
        from townlet.recording import video_export

        assert hasattr(video_export, "batch_export_videos")


def _make_export_database(tmp_path: Path):
    from types import SimpleNamespace

    import lz4.frame
    import msgpack

    from tests.test_townlet.utils.builders import make_test_recording_payload
    from townlet.demo.database import DemoDatabase

    path = tmp_path / "demo.db"
    with DemoDatabase(path) as db:
        for episode_id in (1, 2):
            payload = make_test_recording_payload(episode_id=episode_id, completion_reason="authored_terminal")
            serialized = msgpack.packb(payload, use_bin_type=True)
            compressed = lz4.frame.compress(serialized)
            recording_path = tmp_path / f"episode_{episode_id:06d}.msgpack.lz4"
            recording_path.write_bytes(compressed)
            db.insert_recording(
                episode_id=episode_id,
                file_path=recording_path.name,
                metadata=SimpleNamespace(**payload["metadata"]),
                reason="periodic",
                file_size=len(serialized),
                compressed_size=len(compressed),
            )
    return path


def test_real_two_recording_batch_closes_query_and_each_loaded_reader_before_next_open(tmp_path: Path, monkeypatch) -> None:
    from townlet.demo.database import DemoDatabase
    from townlet.recording import video_export
    from townlet.recording.replay import ReplayManager

    database_path = _make_export_database(tmp_path)
    owners = []
    loaded = []
    rendered = []
    original_load = ReplayManager.load_episode

    def observe_database(path):
        assert all(db._closed for db in owners), "Query and prior export owners must close before another original open"
        assert not any(Path(str(path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal"))
        db = DemoDatabase(path)
        owners.append(db)
        return db

    def observe_load(self, episode_id):
        result = original_load(self, episode_id)
        assert result, "The real current-format reader must load both recordings"
        loaded.append(episode_id)
        return result

    class FastRenderer:
        def __init__(self, **kwargs):
            assert all(db._closed for db in owners), "Loaded in-memory frames must release DB custody before rendering"

        def render_frame(self, step, metadata, affordances):
            rendered.append((step, metadata, affordances))
            return np.zeros((2, 2, 3), dtype=np.uint8)

    def fast_encode(frames_dir, output_path, **kwargs):
        output_path.write_bytes(b"test encoded video")
        return True

    monkeypatch.setattr(video_export, "DemoDatabase", observe_database)
    monkeypatch.setattr(ReplayManager, "load_episode", observe_load)
    monkeypatch.setattr(video_export, "EpisodeVideoRenderer", FastRenderer)
    monkeypatch.setattr(video_export, "_encode_video_ffmpeg", fast_encode)
    try:
        assert video_export.batch_export_videos(database_path, tmp_path, tmp_path / "videos", reason="periodic") == 2
        assert loaded == [2, 1]
        assert len(owners) == 3
        assert all(db._closed for db in owners)
        assert len(rendered) == 4
        for step, metadata, affordances in rendered:
            assert metadata["completion_reason"] == "authored_terminal"
            assert metadata["total_reward"] == 1.0
            assert metadata["shaping_reward"] == 0.2
            assert affordances == {"Bed": [2, 3]}
            assert step["reward"] == (1.0 if step["step"] == 0 else 0.0)
            assert step["extrinsic_reward"] == (0.5 if step["step"] == 0 else 0.0)
            assert step["intrinsic_reward"] == (0.3 if step["step"] == 0 else 0.0)
            assert step["shaping_reward"] == (0.2 if step["step"] == 0 else 0.0)
        assert not any(Path(str(database_path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal"))
    finally:
        for db in owners:
            db.close()


@pytest.mark.parametrize("failure", ["missing_file", "invalid_payload", "load_exception"])
def test_real_export_releases_reader_custody_on_load_failure(tmp_path: Path, monkeypatch, failure: str) -> None:
    from townlet.demo.database import DemoDatabase
    from townlet.recording import video_export
    from townlet.recording.replay import ReplayManager

    database_path = _make_export_database(tmp_path)
    owners = []
    recording_path = tmp_path / "episode_000001.msgpack.lz4"
    if failure == "missing_file":
        recording_path.unlink()
    elif failure == "invalid_payload":
        recording_path.write_bytes(b"invalid LZ4")
    else:

        def raise_from_load(self, episode_id):
            assert self.database.get_recording(episode_id) is not None
            raise RuntimeError("injected reader exception")

        monkeypatch.setattr(ReplayManager, "load_episode", raise_from_load)

    def observe_database(path):
        db = DemoDatabase(path)
        owners.append(db)
        return db

    monkeypatch.setattr(video_export, "DemoDatabase", observe_database)
    try:
        if failure == "load_exception":
            with pytest.raises(RuntimeError, match="injected reader"):
                video_export.export_episode_video(1, database_path, tmp_path, tmp_path / "video.mp4")
        else:
            assert video_export.export_episode_video(1, database_path, tmp_path, tmp_path / "video.mp4") is False
        assert owners and all(db._closed for db in owners), "Every unsuccessful reader must close its real DB in finally"
        assert not any(Path(str(database_path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal"))
        with DemoDatabase(database_path) as reopened:
            assert reopened.get_recording(2) is not None
    finally:
        for db in owners:
            db.close()


def test_real_batch_query_exception_closes_query_owner(tmp_path: Path, monkeypatch) -> None:
    from townlet.demo.database import DemoDatabase
    from townlet.recording import video_export

    database_path = _make_export_database(tmp_path)
    owners = []

    def observe_database(path):
        db = DemoDatabase(path)
        owners.append(db)
        return db

    def raise_from_query(self, **kwargs):
        assert self.get_recording(1) is not None
        raise RuntimeError("injected query exception")

    monkeypatch.setattr(video_export, "DemoDatabase", observe_database)
    monkeypatch.setattr(DemoDatabase, "list_recordings", raise_from_query)
    try:
        with pytest.raises(RuntimeError, match="injected query"):
            video_export.batch_export_videos(database_path, tmp_path, tmp_path / "videos")
        assert owners and all(db._closed for db in owners)
        assert not any(Path(str(database_path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal"))
    finally:
        for db in owners:
            db.close()


def test_actual_renderer_labels_canonical_frame_total_and_episode_total() -> None:
    from matplotlib.figure import Figure

    from tests.test_townlet.utils.builders import make_test_recording_payload
    from townlet.recording.video_renderer import EpisodeVideoRenderer

    payload = make_test_recording_payload(episode_id=7, completion_reason="authored_terminal")
    renderer = EpisodeVideoRenderer(grid_size=8, dpi=20, style="dark")
    for row in payload["steps"]:
        figure = Figure()
        axis = figure.add_subplot(111)
        renderer._render_info(axis, row, payload["metadata"])
        labels = {text.get_text() for text in axis.texts}
        assert f"Reward: {row['reward']:.2f}" in labels
        assert "Total: 1.0" in labels
        if row["step"] == 0:
            assert "Reward: 1.00" in labels
            assert "Reward: 0.50" not in labels  # Extrinsic is only one contributor.
