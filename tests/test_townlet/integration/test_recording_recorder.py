"""
Tests for episode recorder.

Tests the core recording infrastructure: EpisodeRecorder and RecordingWriter.
"""

import hashlib
import queue
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
import torch


def _stop_writer_for_queue_inspection(recorder):
    """Give the test sole ownership of queue entries before capture begins."""
    recorder.writer.stop()
    recorder.writer_thread.join(timeout=1.0)
    assert not recorder.writer_thread.is_alive()
    assert recorder.writer.running is False
    assert recorder.queue.unfinished_tasks == 0


def _take_queue_item(recorder):
    """Acknowledge an entry that the test takes from the stopped writer."""
    item = recorder.queue.get_nowait()
    recorder.queue.task_done()
    return item


class TestEpisodeRecorder:
    """Test EpisodeRecorder queue and threading."""

    def test_recorder_creates_queue(self):
        """Recorder should create a bounded queue on initialization."""
        from townlet.recording.recorder import EpisodeRecorder

        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock minimal dependencies
            config = {"max_queue_size": 100}

            recorder = EpisodeRecorder(
                config=config,
                output_dir=Path(tmpdir),
                database=None,  # Mock
                curriculum=None,  # Mock
            )

            # Verify queue exists and has correct size
            assert recorder.queue is not None
            assert recorder.queue.maxsize == 100
            assert recorder.shutdown() == ()
            assert not recorder.writer_thread.is_alive()
            assert recorder.writer.running is False
            assert recorder.queue.unfinished_tasks == 0

    def test_record_step_adds_to_queue(self):
        """record_step should queue a capture containing the exact RecordedStep."""
        from townlet.recording.data_structures import RecordedStep
        from townlet.recording.recorder import EpisodeRecorder

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"max_queue_size": 100}

            recorder = EpisodeRecorder(
                config=config,
                output_dir=Path(tmpdir),
                database=None,
                curriculum=None,
            )
            _stop_writer_for_queue_inspection(recorder)

            # Record a step
            positions = torch.tensor([3, 5])
            meters = torch.tensor([1.0, 0.9, 0.8, 0.5, 0.7, 0.6, 0.95, 0.85])

            recorder.record_step(
                step=0,
                positions=positions,
                meters=meters,
                action=4,
                reward=1.0,
                intrinsic_reward=0.15,
                done=False,
                q_values=None,
                extrinsic_reward=0.85,
                shaping_reward=0.0,
            )

            # Verify item added to queue
            assert recorder.queue.qsize() == 1

            # Inspect the frame carried by the recorder's private queue entry.
            capture = _take_queue_item(recorder)
            assert capture.sequence == 0
            assert capture.ticket is None
            item = capture.frame
            assert isinstance(item, RecordedStep)
            assert item.step == 0
            assert item.position == (3, 5)
            assert item.action == 4
            assert item.meters == tuple(meters.tolist())
            assert item.reward == 1.0
            assert item.extrinsic_reward == 0.85
            assert item.intrinsic_reward == 0.15
            assert item.shaping_reward == 0.0
            assert item.done is False
            assert recorder.shutdown() == ()
            assert recorder.queue.unfinished_tasks == 0

    def test_record_step_clones_tensors(self, cpu_device):
        """record_step should clone tensors to prevent training loop blocking."""
        from townlet.recording.recorder import EpisodeRecorder

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"max_queue_size": 100}

            recorder = EpisodeRecorder(
                config=config,
                output_dir=Path(tmpdir),
                database=None,
                curriculum=None,
            )
            _stop_writer_for_queue_inspection(recorder)

            # Create tensors on CPU device for determinism
            positions = torch.tensor([3, 5], device=cpu_device)
            meters = torch.tensor([1.0, 0.9, 0.8, 0.5, 0.7, 0.6, 0.95, 0.85], device=cpu_device)

            recorder.record_step(
                step=0,
                positions=positions,
                meters=meters,
                action=4,
                reward=1.0,
                intrinsic_reward=0.15,
                done=False,
                extrinsic_reward=0.85,
                shaping_reward=0.0,
            )

            # Get recorded step
            item = _take_queue_item(recorder).frame

            # Verify position is a tuple (converted from tensor)
            assert isinstance(item.position, tuple)
            assert item.position == (3, 5)
            assert item.meters == tuple(meters.tolist())
            positions.fill_(0)
            meters.fill_(0)
            assert item.position == (3, 5)
            assert item.meters != tuple(meters.tolist())
            assert recorder.shutdown() == ()
            assert recorder.queue.unfinished_tasks == 0

    def test_record_step_with_q_values(self):
        """record_step should handle optional Q-values."""
        import numpy as np

        from townlet.recording.recorder import EpisodeRecorder

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"max_queue_size": 100}

            recorder = EpisodeRecorder(
                config=config,
                output_dir=Path(tmpdir),
                database=None,
                curriculum=None,
            )
            _stop_writer_for_queue_inspection(recorder)

            positions = torch.tensor([0, 0])
            meters = torch.tensor([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
            q_values = torch.tensor([0.8, 0.7, 0.9, 0.6, 1.2, 0.5])
            action_masks = torch.tensor([True, False, True, True, False, True])

            recorder.record_step(
                step=10,
                positions=positions,
                meters=meters,
                action=2,
                reward=0.8,
                intrinsic_reward=0.05,
                done=False,
                q_values=q_values,
                action_masks=action_masks,
                extrinsic_reward=0.75,
                shaping_reward=0.0,
            )

            item = _take_queue_item(recorder).frame
            # Use approximate equality due to float32 precision
            assert np.allclose(item.q_values, (0.8, 0.7, 0.9, 0.6, 1.2, 0.5), rtol=1e-5)
            assert item.action_masks == (True, False, True, True, False, True)
            q_values.fill_(0)
            action_masks.fill_(False)
            assert np.allclose(item.q_values, (0.8, 0.7, 0.9, 0.6, 1.2, 0.5), rtol=1e-5)
            assert item.action_masks == (True, False, True, True, False, True)
            assert recorder.shutdown() == ()
            assert recorder.queue.unfinished_tasks == 0

    def test_record_step_with_temporal_mechanics(self):
        """record_step should handle temporal mechanics fields."""
        from townlet.recording.recorder import EpisodeRecorder

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"max_queue_size": 100}

            recorder = EpisodeRecorder(
                config=config,
                output_dir=Path(tmpdir),
                database=None,
                curriculum=None,
            )
            _stop_writer_for_queue_inspection(recorder)

            positions = torch.tensor([4, 4])
            meters = torch.tensor([0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3])

            recorder.record_step(
                step=100,
                positions=positions,
                meters=meters,
                action=4,
                reward=0.5,
                intrinsic_reward=0.1,
                done=False,
                time_of_day=12,
                interaction_progress=0.33,
                extrinsic_reward=0.4,
                shaping_reward=0.0,
            )

            item = _take_queue_item(recorder).frame
            assert item.time_of_day == 12
            assert item.interaction_progress == 0.33
            assert recorder.shutdown() == ()
            assert recorder.queue.unfinished_tasks == 0

    def test_record_temporal_mechanics_from_environment(self, cpu_device, cpu_env_factory):
        """record_step should capture temporal state from VectorizedHamletEnv.

        Integration test: Verify that temporal mechanics state (time_of_day,
        interaction_progress) from a live environment gets correctly recorded.
        """
        from townlet.recording.recorder import EpisodeRecorder

        # Create environment with temporal mechanics enabled
        env = cpu_env_factory(
            config_dir=Path("configs/default_curriculum"),
            level_name="L3_temporal_mechanics",
            num_agents=1,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"max_queue_size": 100}

            recorder = EpisodeRecorder(
                config=config,
                output_dir=Path(tmpdir),
                database=None,
                curriculum=None,
            )

            _stop_writer_for_queue_inspection(recorder)

            # Reset environment and place agent on a known affordance
            env.reset()
            assert env.affordances, "No affordances deployed in temporal mechanics level"
            affordance_name, affordance_pos = next(iter(env.affordances.items()))
            env.positions[0] = affordance_pos.clone()
            env.meters[0, 0] = 0.3  # Low energy

            # Record 3 interaction steps
            for i in range(3):
                # Take INTERACT action
                interact_action = env.action_ids["INTERACT"]
                obs, reward, done, info = env.step(torch.tensor([interact_action], device=cpu_device))

                # Record step with temporal state
                recorder.record_step(
                    step=i,
                    positions=env.positions[0],
                    meters=env.meters[0],
                    action=interact_action,
                    reward=reward[0].item(),
                    intrinsic_reward=float(info["reward_components"]["intrinsic"][0].item()),
                    done=done[0].item(),
                    time_of_day=env.time_of_day,
                    interaction_progress=env.interaction_progress[0].item() / 10.0,  # Normalized
                    extrinsic_reward=float(info["reward_components"]["extrinsic"][0].item()),
                    shaping_reward=float(info["reward_components"]["shaping"][0].item()),
                )

            # Verify 3 steps recorded with temporal state
            assert recorder.queue.qsize() == 3

            # Check each recorded step
            for i in range(3):
                item = _take_queue_item(recorder).frame

                # Time advances with each step (24-tick cycle)
                assert item.time_of_day is not None
                assert 0 <= item.time_of_day < 24

                # Interaction progress should be recorded (non-decreasing per step)
                assert item.interaction_progress is not None
                assert item.interaction_progress >= 0.0
                if i > 0:
                    assert item.interaction_progress >= 0.0
            assert recorder.shutdown() == ()
            assert recorder.queue.unfinished_tasks == 0

    def test_finish_episode_adds_marker(self):
        """finish_episode should queue a boundary with the exact episode metadata."""
        from townlet.recording.data_structures import EpisodeEndMarker, EpisodeMetadata
        from townlet.recording.receipts import RecordingTicket
        from townlet.recording.recorder import EpisodeRecorder

        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"max_queue_size": 100}

            recorder = EpisodeRecorder(
                config=config,
                output_dir=Path(tmpdir),
                database=None,
                curriculum=None,
            )
            _stop_writer_for_queue_inspection(recorder)

            # Create metadata
            metadata = EpisodeMetadata(
                episode_id=100,
                survival_steps=200,
                total_reward=150.0,
                extrinsic_reward=145.0,
                intrinsic_reward=5.0,
                curriculum_stage=2,
                epsilon=0.5,
                intrinsic_weight=0.5,
                timestamp=1699123456.78,
                affordance_layout={"Bed": (2, 3)},
                affordance_visits={"Bed": 5},
                custom_action_uses={},
                completion_reason="authored_terminal",
                shaping_reward=0.0,
            )

            ticket = recorder.finish_episode(metadata)

            # Verify marker added
            assert recorder.queue.qsize() == 1
            boundary = _take_queue_item(recorder)
            assert ticket == RecordingTicket(sequence=0, episode=100, lane=0)
            assert boundary.ticket == ticket
            item = boundary.marker
            assert isinstance(item, EpisodeEndMarker)
            assert item.metadata.episode_id == 100
            assert item.metadata == metadata
            assert item.metadata is not metadata
            assert recorder.shutdown() == ()
            assert recorder.queue.unfinished_tasks == 0

    def test_queue_overflow_graceful_degradation(self, caplog):
        """Legacy overflow should log dropped frames and retain admitted transport entries."""
        from townlet.recording.receipts import RecordingDrainError
        from townlet.recording.recorder import EpisodeRecorder

        with tempfile.TemporaryDirectory() as tmpdir:
            # Very small queue
            config = {"max_queue_size": 2}

            recorder = EpisodeRecorder(
                config=config,
                output_dir=Path(tmpdir),
                database=None,
                curriculum=None,
            )

            _stop_writer_for_queue_inspection(recorder)

            positions = torch.tensor([0, 0])
            meters = torch.tensor([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

            # Fill queue
            recorder.record_step(
                step=0,
                positions=positions,
                meters=meters,
                action=0,
                reward=1.0,
                intrinsic_reward=0.0,
                done=False,
                extrinsic_reward=1.0,
                shaping_reward=0.0,
            )
            recorder.record_step(
                step=1,
                positions=positions,
                meters=meters,
                action=0,
                reward=1.0,
                intrinsic_reward=0.0,
                done=False,
                extrinsic_reward=1.0,
                shaping_reward=0.0,
            )

            # Queue is full (size=2)
            assert recorder.queue.full()

            # Legacy callers retain their no-throw, None-returning overflow path.
            with caplog.at_level("WARNING", logger="townlet.recording.recorder"):
                for dropped_frames in range(1, 3):
                    assert (
                        recorder.record_step(
                            step=2,
                            positions=positions,
                            meters=meters,
                            action=0,
                            reward=1.0,
                            intrinsic_reward=0.0,
                            done=False,
                            extrinsic_reward=1.0,
                            shaping_reward=0.0,
                        )
                        is None
                    )
                    assert recorder.legacy_dropped_frames == dropped_frames
                    assert recorder.queue.qsize() == 2

            messages = [record.getMessage().lower() for record in caplog.records if record.name == "townlet.recording.recorder"]
            assert len(messages) == 2
            assert all("queue" in message and "full" in message and "dropp" in message for message in messages)
            with pytest.raises(AttributeError):
                recorder.legacy_dropped_frames = 0
            assert recorder.legacy_dropped_frames == 2

            # This stopped-consumer fixture proves only transport preservation.
            # Both admitted frames remain; neither dropped attempt consumes a sequence.
            assert recorder.queue.qsize() == 2
            for sequence in range(2):
                capture = _take_queue_item(recorder)
                assert capture.sequence == sequence
                assert capture.ticket is None
                assert capture.frame.step == sequence
                assert capture.frame.position == (0, 0)
                assert capture.frame.meters == tuple(meters.tolist())
                assert capture.frame.reward == 1.0
                assert capture.frame.extrinsic_reward == 1.0
                assert capture.frame.intrinsic_reward == 0.0
                assert capture.frame.shaping_reward == 0.0
                assert capture.frame.done is False

            # A later admitted frame receives the next accepted sequence.
            assert (
                recorder.record_step(
                    step=2,
                    positions=positions,
                    meters=meters,
                    action=0,
                    reward=1.0,
                    intrinsic_reward=0.0,
                    done=False,
                    extrinsic_reward=1.0,
                    shaping_reward=0.0,
                )
                is None
            )
            capture = _take_queue_item(recorder)
            assert capture.sequence == 2
            assert capture.ticket is None
            assert capture.frame.step == 2
            assert capture.frame.position == (0, 0)
            assert capture.frame.meters == tuple(meters.tolist())
            assert capture.frame.reward == 1.0
            assert capture.frame.extrinsic_reward == 1.0
            assert capture.frame.intrinsic_reward == 0.0
            assert capture.frame.shaping_reward == 0.0
            assert capture.frame.done is False
            assert recorder.legacy_dropped_frames == 2

            # Taking transport entries cannot resolve a producer's incomplete group.
            with pytest.raises(RecordingDrainError) as failure:
                recorder.shutdown()
            assert failure.value.errors
            assert not any(receipt.status == "persisted" for receipt in failure.value.resolved_receipts)
            with pytest.raises(RuntimeError, match="admission is closed"):
                recorder.record_step(
                    step=3,
                    positions=positions,
                    meters=meters,
                    action=0,
                    reward=1.0,
                    intrinsic_reward=0.0,
                    done=False,
                    extrinsic_reward=1.0,
                    shaping_reward=0.0,
                )
            assert not recorder.writer_thread.is_alive()
            assert recorder.writer.running is False
            assert recorder.queue.unfinished_tasks == 0

    def test_shutdown_reports_incomplete_accepted_work(self):
        """Closing with an accepted frame and no end marker must report its loss."""
        from townlet.recording.receipts import RecordingDrainError
        from townlet.recording.recorder import EpisodeRecorder

        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = EpisodeRecorder({"max_queue_size": 100}, Path(tmpdir), None, None)
            recorder.record_step(
                step=0,
                positions=torch.tensor([0, 0]),
                meters=torch.ones(8),
                action=0,
                reward=1.0,
                extrinsic_reward=1.0,
                intrinsic_reward=0.0,
                shaping_reward=0.0,
                done=False,
            )

            with pytest.raises(RecordingDrainError) as failure:
                recorder.shutdown()

            assert failure.value.unbound_sequences == (0,)
            assert failure.value.receipts == ()
            assert failure.value.resolved_receipts == ()
            assert len(failure.value.errors) == 1
            assert "Missing episode-end marker" in str(failure.value.errors[0])
            assert not recorder.writer_thread.is_alive()
            assert recorder.writer.running is False
            assert recorder.queue.unfinished_tasks == 0


class TestRecordingWriter:
    """Test RecordingWriter background thread."""

    def test_writer_starts_thread(self):
        """Writer should start background thread on initialization."""
        from townlet.recording.recorder import RecordingWriter

        with tempfile.TemporaryDirectory() as tmpdir:
            test_queue = queue.Queue(maxsize=100)
            config = {"compression": "lz4"}

            writer = RecordingWriter(
                queue=test_queue,
                config=config,
                output_dir=Path(tmpdir),
                database=None,
                curriculum=None,
            )

            # Verify writer is ready
            assert writer.running is True
            assert writer.episode_buffer == []

    def test_writer_buffers_steps(self):
        """Writer should buffer RecordedStep items."""
        from townlet.recording.data_structures import RecordedStep
        from townlet.recording.recorder import RecordingWriter

        with tempfile.TemporaryDirectory() as tmpdir:
            test_queue = queue.Queue(maxsize=100)
            config = {"compression": "lz4"}

            writer = RecordingWriter(
                queue=test_queue,
                config=config,
                output_dir=Path(tmpdir),
                database=None,
                curriculum=None,
            )

            # Start writer thread
            writer_thread = threading.Thread(target=writer.writer_loop, daemon=True)
            writer_thread.start()

            # Add step to queue
            step = RecordedStep(
                step=0,
                position=(0, 0),
                meters=(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
                action=0,
                reward=1.0,
                intrinsic_reward=0.0,
                done=False,
                q_values=None,
                extrinsic_reward=1.0,
                shaping_reward=0.0,
            )
            test_queue.put(step)

            # Synchronize with the real consumer before inspecting its buffer.
            test_queue.join()

            # Verify step was buffered
            assert len(writer.episode_buffer) == 1
            assert writer.episode_buffer[0] == step

            # Stop writer
            writer.stop()
            writer_thread.join(timeout=1.0)
            assert not writer_thread.is_alive()
            assert writer.running is False
            assert test_queue.unfinished_tasks == 0
            assert len(writer.errors) == 1
            assert "Missing episode-end marker" in str(writer.errors[0])
            assert writer.unbound_sequences == [0]
            assert writer.receipts == []

    def test_writer_clears_buffer_on_episode_end(self):
        """Writer should clear buffer after processing episode end."""
        from townlet.recording.data_structures import EpisodeEndMarker, EpisodeMetadata, RecordedStep
        from townlet.recording.receipts import RecordingTicket
        from townlet.recording.recorder import RecordingWriter

        with tempfile.TemporaryDirectory() as tmpdir:
            test_queue = queue.Queue(maxsize=100)
            config = {"compression": "lz4", "criteria": {"periodic": {"enabled": True, "interval": 1}}}  # Record everything

            # Mock database
            class MockDatabase:
                def __init__(self):
                    self.recordings = []

                @contextmanager
                def recording_publication(self, run_id, episode_id, lane, legacy):
                    yield 1

                def insert_scoped_recording(self, **kwargs):
                    self.recordings.append(kwargs)
                    return 1

            database = MockDatabase()

            writer = RecordingWriter(
                queue=test_queue,
                config=config,
                output_dir=Path(tmpdir),
                database=database,
                curriculum=None,
            )

            # Add step
            step = RecordedStep(
                step=0,
                position=(0, 0),
                meters=(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
                action=0,
                reward=1.0,
                intrinsic_reward=0.0,
                done=False,
                q_values=None,
                extrinsic_reward=1.0,
                shaping_reward=0.0,
            )
            test_queue.put(step)

            # Add episode end marker
            metadata = EpisodeMetadata(
                episode_id=1,
                survival_steps=1,
                total_reward=1.0,
                extrinsic_reward=1.0,
                intrinsic_reward=0.0,
                curriculum_stage=1,
                epsilon=1.0,
                intrinsic_weight=1.0,
                timestamp=time.time(),
                affordance_layout={},
                affordance_visits={},
                custom_action_uses={},
                completion_reason="cap",
                shaping_reward=0.0,
            )
            marker = EpisodeEndMarker(metadata=metadata)
            test_queue.put(marker)

            # Both raw public queue items must pass through the actual consumer.
            writer_thread = threading.Thread(target=writer.writer_loop, daemon=True)
            writer_thread.start()
            test_queue.join()
            writer.stop()
            writer_thread.join(timeout=1.0)

            # Buffer should be cleared
            assert len(writer.episode_buffer) == 0
            assert not writer_thread.is_alive()
            assert writer.running is False
            assert test_queue.unfinished_tasks == 0
            assert writer.errors == []
            assert len(database.recordings) == 1
            indexed = database.recordings[0]
            assert indexed["metadata"] == metadata
            assert indexed["sequence"] == 1
            assert indexed["frame_count"] == 1
            assert indexed["final_done"] is False
            assert indexed["legacy"] is True
            assert len(writer.receipts) == 1
            receipt = writer.receipts[0]
            assert receipt.ticket == RecordingTicket(sequence=1, episode=1, lane=0)
            assert receipt.status == "persisted"
            canonical_path = Path(tmpdir) / "episode_000001.msgpack.lz4"
            assert canonical_path.is_file()
            assert receipt.path is not None
            assert receipt.path.is_absolute()
            assert receipt.path.is_relative_to(Path(tmpdir))
            assert receipt.path.parent != Path(tmpdir)
            assert receipt.path.is_file()
            assert receipt.path.read_bytes() == canonical_path.read_bytes()
            assert receipt.path.stat().st_ino != canonical_path.stat().st_ino
            assert indexed["generation"] == 1
            assert indexed["file_path"] == str(receipt.path)
            assert indexed["legacy_file_path"] == str(canonical_path.relative_to(Path(tmpdir).parent))
            assert indexed["file_sha256"] == hashlib.sha256(receipt.path.read_bytes()).hexdigest()
            assert receipt.index_id == 1
            assert receipt.error is None
            assert receipt.storage_mode == "indexed"

    def test_writer_stops_gracefully(self):
        """Writer should stop when stop() is called."""
        from townlet.recording.recorder import RecordingWriter

        with tempfile.TemporaryDirectory() as tmpdir:
            test_queue = queue.Queue(maxsize=100)
            config = {"compression": "lz4"}

            writer = RecordingWriter(
                queue=test_queue,
                config=config,
                output_dir=Path(tmpdir),
                database=None,
                curriculum=None,
            )

            assert writer.running is True

            # Stop writer
            writer.stop()

            # stop() only enqueues the sentinel; the loop must still consume it.
            assert writer.running is True
            assert test_queue.unfinished_tasks == 1
            writer_thread = threading.Thread(target=writer.writer_loop, daemon=True)
            writer_thread.start()
            writer_thread.join(timeout=1.0)
            assert not writer_thread.is_alive()
            assert writer.running is False
            assert test_queue.unfinished_tasks == 0
            assert writer.errors == []
