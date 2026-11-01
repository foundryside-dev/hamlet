"""Recorder admission, writer selection, raw queue transport and artifact regressions."""

import hashlib
import queue
import threading
from contextlib import nullcontext
from unittest.mock import Mock, patch

import lz4.frame
import msgpack
import pytest
import torch

from tests.test_townlet.utils.builders import make_test_episode_metadata, make_test_recorded_step
from townlet.recording.data_structures import EpisodeEndMarker, EpisodeMetadata, RecordedStep
from townlet.recording.receipts import RecordingTicket


@patch("townlet.recording.recorder.RecordingWriter")
@patch("townlet.recording.recorder.threading.Thread")
def test_record_step_uses_recording_output_dir_fixture(mock_thread, mock_writer_class, recording_output_dir):
    """EpisodeRecorder should respect the shared recording_output_dir fixture."""

    from townlet.recording.recorder import EpisodeRecorder

    mock_writer_class.return_value = Mock(receipts=[], errors=[], unbound_sequences=[], running=True)
    recorder = EpisodeRecorder(
        config={"max_queue_size": 10},
        output_dir=recording_output_dir,
        database=None,
        curriculum=None,
    )

    positions = torch.tensor([0, 1])
    meters = torch.ones(8)

    recorder.record_step(
        step=0,
        positions=positions,
        meters=meters,
        action=1,
        reward=0.5,
        intrinsic_reward=0.0,
        done=False,
        extrinsic_reward=0.5,
        shaping_reward=0.0,
    )

    assert recording_output_dir.exists()
    assert recorder.queue.qsize() == 1


# =============================================================================
# EPISODE RECORDER TESTS
# =============================================================================


class TestEpisodeRecorderEdgeCases:
    """Test EpisodeRecorder edge cases and error paths."""

    @patch("townlet.recording.recorder.RecordingWriter")
    @patch("townlet.recording.recorder.threading.Thread")
    def test_record_step_with_list_q_values(self, mock_thread, mock_writer_class, recording_output_dir):
        """Should handle q_values as list (line 107 else branch)."""
        from townlet.recording.recorder import EpisodeRecorder

        mock_writer_class.return_value = Mock(receipts=[], errors=[], unbound_sequences=[], running=True)
        config = {"max_queue_size": 100}

        recorder = EpisodeRecorder(
            config=config,
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        positions = torch.tensor([3, 5])
        meters = torch.tensor([1.0, 0.9, 0.8, 0.5, 0.7, 0.6, 0.95, 0.85])

        # Provide q_values as plain list (not tensor)
        q_values_list = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]

        recorder.record_step(
            step=0,
            positions=positions,
            meters=meters,
            action=2,
            reward=1.0,
            intrinsic_reward=0.1,
            done=False,
            q_values=q_values_list,  # List, not tensor
            extrinsic_reward=0.9,
            shaping_reward=0.0,
        )

        # Should convert list to tuple without error
        item = recorder.queue.get_nowait()
        assert isinstance(item.frame, RecordedStep)
        assert item.frame.q_values == tuple(q_values_list)

    @patch("townlet.recording.recorder.RecordingWriter")
    @patch("townlet.recording.recorder.threading.Thread")
    def test_record_step_with_list_action_masks(self, mock_thread, mock_writer_class, recording_output_dir):
        """Should handle action_masks as list (lines 113-116 else branch)."""
        from townlet.recording.recorder import EpisodeRecorder

        mock_writer_class.return_value = Mock(receipts=[], errors=[], unbound_sequences=[], running=True)
        config = {"max_queue_size": 100}

        recorder = EpisodeRecorder(
            config=config,
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        positions = torch.tensor([3, 5])
        meters = torch.tensor([1.0, 0.9, 0.8, 0.5, 0.7, 0.6, 0.95, 0.85])

        # Provide action_masks as plain list (not tensor)
        action_masks_list = [True, True, False, True, True, False]

        recorder.record_step(
            step=0,
            positions=positions,
            meters=meters,
            action=2,
            reward=1.0,
            intrinsic_reward=0.1,
            done=False,
            action_masks=action_masks_list,  # List, not tensor
            extrinsic_reward=0.9,
            shaping_reward=0.0,
        )

        # Should convert list to tuple without error
        item = recorder.queue.get_nowait()
        assert isinstance(item.frame, RecordedStep)
        assert item.frame.action_masks == tuple(action_masks_list)

    @pytest.mark.parametrize(
        ("operation", "counter", "log_method"),
        [
            ("finish", "legacy_rejected_finishes", "error"),
            ("frame", "legacy_dropped_frames", "warning"),
        ],
    )
    @patch("townlet.recording.recorder.RecordingWriter")
    @patch("townlet.recording.recorder.threading.Thread")
    def test_legacy_queue_full_logs_without_accepting(
        self, mock_thread, mock_writer_class, recording_output_dir, operation, counter, log_method
    ):
        """Legacy capacity rejection logs, returns None and preserves the admitted group."""
        from townlet.recording.recorder import EpisodeRecorder

        mock_writer_class.return_value = Mock(receipts=[], errors=[], unbound_sequences=[], running=True)
        recorder = EpisodeRecorder({"max_queue_size": 1}, recording_output_dir, None, None)
        recorder.begin_episode(100)
        frame = dict(
            step=0,
            positions=torch.tensor([3, 5]),
            meters=torch.ones(8),
            action=0,
            reward=1.0,
            intrinsic_reward=0.0,
            done=False,
            extrinsic_reward=1.0,
            shaping_reward=0.0,
        )
        assert recorder.record_step(**frame) is None
        assert recorder.queue.full()
        accepted = recorder.queue.queue[0]
        state = (recorder._sequence, recorder._active_episode, recorder._open_frames, recorder.queue.unfinished_tasks)
        metadata = make_test_episode_metadata(survival_steps=1, total_reward=1.0)
        with patch("townlet.recording.recorder.logger") as mock_logger:
            for count in (1, 2):
                result = recorder.finish_episode(metadata) if operation == "finish" else recorder.record_step(**frame)
                assert result is None
                assert getattr(recorder, counter) == count
                assert getattr(mock_logger, log_method).call_count == count
                assert (recorder._sequence, recorder._active_episode, recorder._open_frames, recorder.queue.unfinished_tasks) == state
                assert list(recorder.queue.queue) == [accepted]
        other_counter = "legacy_dropped_frames" if operation == "finish" else "legacy_rejected_finishes"
        assert getattr(recorder, other_counter) == 0
        with pytest.raises(AttributeError):
            setattr(recorder, counter, 99)

    @pytest.mark.parametrize("route", ["scoped_frame", "scoped_bound_frame", "legacy_bound_frame", "scoped_finish"])
    @patch("townlet.recording.recorder.RecordingWriter")
    @patch("townlet.recording.recorder.threading.Thread")
    def test_qualified_queue_full_remains_strict(self, mock_thread, mock_writer_class, recording_output_dir, route):
        from townlet.recording.recorder import EpisodeRecorder

        mock_writer_class.return_value = Mock(receipts=[], errors=[], unbound_sequences=[], running=True)
        if route == "legacy_bound_frame":
            recorder = EpisodeRecorder({"max_queue_size": 1}, recording_output_dir, None, None)
        else:
            recorder = EpisodeRecorder.for_scope({"max_queue_size": 1}, recording_output_dir, None, None, run_id="capacity", lane=2)
        recorder.begin_episode(100)
        frame = dict(
            step=0,
            positions=torch.tensor([3, 5]),
            meters=torch.ones(8),
            action=0,
            reward=1.0,
            extrinsic_reward=1.0,
            intrinsic_reward=0.0,
            shaping_reward=0.0,
            done=False,
            q_values=None,
            epsilon=None,
            action_masks=None,
            time_of_day=None,
            interaction_progress=None,
        )
        recorder.record_step(**frame)
        accepted = recorder.queue.queue[0]
        state = (recorder._sequence, recorder._active_episode, recorder._open_frames, recorder.queue.unfinished_tasks)
        with pytest.raises(queue.Full):
            if route == "scoped_finish":
                recorder.finish_episode(make_test_episode_metadata(survival_steps=1, total_reward=1.0))
            elif route == "scoped_frame":
                recorder.record_step(**frame)
            else:
                recorder.record_bound_step(**frame)
        assert (recorder._sequence, recorder._active_episode, recorder._open_frames, recorder.queue.unfinished_tasks) == state
        assert list(recorder.queue.queue) == [accepted]
        assert recorder.legacy_dropped_frames == recorder.legacy_rejected_finishes == 0

    @patch("townlet.recording.recorder.RecordingWriter")
    def test_shutdown_method(self, mock_writer_class, recording_output_dir):
        """Shutdown drains the closed accepted set before returning immutable receipts."""
        from townlet.recording.recorder import EpisodeRecorder

        config = {"max_queue_size": 100}

        mock_writer = Mock(receipts=[], errors=[], unbound_sequences=[], running=False)
        mock_writer_class.return_value = mock_writer

        mock_thread = Mock()

        with patch("townlet.recording.recorder.threading.Thread", return_value=mock_thread):
            recorder = EpisodeRecorder(
                config=config,
                output_dir=recording_output_dir,
                database=None,
                curriculum=None,
            )

            assert recorder.shutdown() == ()
            assert recorder.shutdown() == ()
            assert recorder.queue.unfinished_tasks == 0
            with pytest.raises(RuntimeError, match="admission is closed"):
                recorder.begin_episode(1)

            mock_writer.stop.assert_called_once()
            mock_thread.join.assert_called_once_with()


# =============================================================================
# RECORDING WRITER TESTS
# =============================================================================


class TestRecordingWriterProcessing:
    """Test RecordingWriter episode processing logic."""

    def test_writer_loop_processes_bare_step_and_episode_end_marker(self, recording_output_dir):
        """The public raw queue must still publish complete file-only episodes before stop."""
        from townlet.recording.recorder import RecordingWriter

        test_queue = queue.Queue()
        writer = RecordingWriter(
            queue=test_queue,
            config={"compression": "lz4", "criteria": {"periodic": {"enabled": True, "interval": 1}}},
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        step = RecordedStep(
            step=0,
            position=(3, 5),
            meters=(1.0, 0.5),
            action=2,
            reward=1.5,
            extrinsic_reward=0.8,
            intrinsic_reward=0.5,
            shaping_reward=0.2,
            done=True,
            q_values=(1.0, 2.0, 3.0),
            epsilon=0.25,
            action_masks=(True, False, True),
            time_of_day=7,
            interaction_progress=0.75,
        )
        metadata = EpisodeMetadata(
            episode_id=37,
            survival_steps=1,
            completion_reason="authored_terminal",
            total_reward=1.5,
            extrinsic_reward=0.8,
            intrinsic_reward=0.5,
            shaping_reward=0.2,
            curriculum_stage=2,
            epsilon=0.25,
            intrinsic_weight=0.4,
            timestamp=1234567890.0,
            affordance_layout={"Bed": (2, 3)},
            affordance_visits={"Bed": 1},
            custom_action_uses={"WAIT": 1},
        )
        test_queue.put(step)
        test_queue.put(EpisodeEndMarker(metadata=metadata))
        writer.stop()
        worker = threading.Thread(target=writer.writer_loop, daemon=True)
        worker.start()
        worker.join(timeout=5.0)

        assert not worker.is_alive()
        assert writer.running is False
        assert test_queue.unfinished_tasks == 0
        assert not writer.errors
        assert not writer.unbound_sequences
        expected_path = recording_output_dir / "episode_000037.msgpack.lz4"
        assert expected_path.is_file()
        assert len(writer.receipts) == 1
        receipt = writer.receipts[0]
        assert receipt.ticket.episode == metadata.episode_id
        assert receipt.ticket.lane == 0
        assert receipt.status == "persisted"
        assert receipt.storage_mode == "file_only"
        assert receipt.path is not None
        assert receipt.path.is_absolute()
        assert receipt.path.is_file()
        assert receipt.path != expected_path
        assert not receipt.path.samefile(expected_path)
        assert receipt.index_id is None
        assert receipt.error is None
        published = receipt.path.read_bytes()
        assert expected_path.read_bytes() == published
        payload = msgpack.unpackb(lz4.frame.decompress(published), raw=False)
        assert payload == {
            "version": 2,
            "metadata": {
                "episode_id": 37,
                "survival_steps": 1,
                "completion_reason": "authored_terminal",
                "total_reward": 1.5,
                "extrinsic_reward": 0.8,
                "intrinsic_reward": 0.5,
                "shaping_reward": 0.2,
                "curriculum_stage": 2,
                "epsilon": 0.25,
                "intrinsic_weight": 0.4,
                "timestamp": 1234567890.0,
                "affordance_layout": {"Bed": [2, 3]},
                "affordance_visits": {"Bed": 1},
                "custom_action_uses": {"WAIT": 1},
            },
            "steps": [
                {
                    "step": 0,
                    "position": [3, 5],
                    "meters": [1.0, 0.5],
                    "action": 2,
                    "reward": 1.5,
                    "extrinsic_reward": 0.8,
                    "intrinsic_reward": 0.5,
                    "shaping_reward": 0.2,
                    "done": True,
                    "q_values": [1.0, 2.0, 3.0],
                    "epsilon": 0.25,
                    "action_masks": [True, False, True],
                    "time_of_day": 7,
                    "interaction_progress": 0.75,
                }
            ],
            "affordances": {"Bed": [2, 3]},
        }

    def test_writer_loop_rejects_unsupported_queue_item(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        test_queue = queue.Queue()
        writer = RecordingWriter(test_queue, {"criteria": {}}, recording_output_dir, None, None)
        test_queue.put(object())
        writer.stop()
        worker = threading.Thread(target=writer.writer_loop, daemon=True)
        worker.start()
        worker.join(timeout=5.0)

        assert not worker.is_alive()
        assert writer.running is False
        assert test_queue.unfinished_tasks == 0
        assert len(writer.errors) == 1
        assert isinstance(writer.errors[0], TypeError)
        assert not writer.receipts
        assert not list(recording_output_dir.glob("*.msgpack.lz4"))

    def test_writer_loop_refuses_incomplete_bare_episode(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        test_queue = queue.Queue()
        writer = RecordingWriter(test_queue, {"criteria": {}}, recording_output_dir, None, None)
        test_queue.put(make_test_recorded_step())
        writer.stop()
        worker = threading.Thread(target=writer.writer_loop, daemon=True)
        worker.start()
        worker.join(timeout=5.0)

        assert not worker.is_alive()
        assert writer.running is False
        assert test_queue.unfinished_tasks == 0
        assert len(writer.errors) == 1
        assert isinstance(writer.errors[0], ValueError)
        assert "Missing episode-end marker" in str(writer.errors[0])
        assert writer.unbound_sequences == [0]
        assert not writer.receipts
        assert not list(recording_output_dir.glob("*.msgpack.lz4"))

    def test_process_episode_end_clears_buffer(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        writer = RecordingWriter(
            queue=queue.Queue(),
            config={"criteria": {}},
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        writer.episode_buffer.append(make_test_recorded_step(done=True))
        metadata = make_test_episode_metadata(survival_steps=1, total_reward=1.0)
        ticket = RecordingTicket(sequence=1, episode=metadata.episode_id, lane=0)
        writer._process_episode_end(metadata, ticket, dropped_frames=0, accepted_frames=len(writer.episode_buffer))

        assert writer.episode_buffer == []
        assert len(writer.receipts) == 1
        assert writer.receipts[0].ticket == ticket
        assert writer.receipts[0].status == "not_selected"

    def test_process_episode_end_should_record_true(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        writer = RecordingWriter(
            queue=queue.Queue(),
            config={"criteria": {"periodic": {"enabled": True, "interval": 100}}},
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        writer.episode_buffer.append(make_test_recorded_step(done=True))
        metadata = EpisodeMetadata(
            episode_id=100,
            survival_steps=1,
            total_reward=1.0,
            extrinsic_reward=1.0,
            intrinsic_reward=0.0,
            curriculum_stage=1,
            epsilon=0.5,
            intrinsic_weight=0.0,
            timestamp=1234567890.0,
            affordance_layout={"Bed": (2, 3)},
            affordance_visits={"Bed": 1},
            custom_action_uses={},
            completion_reason="authored_terminal",
            shaping_reward=0.0,
        )

        ticket = RecordingTicket(sequence=1, episode=metadata.episode_id, lane=0)
        expected_path = recording_output_dir / "episode_000100.msgpack.lz4"
        with (
            patch.object(writer, "_write_episode", wraps=writer._write_episode) as mock_write,
            patch("townlet.recording.recorder.logger") as mock_logger,
        ):
            writer._process_episode_end(metadata, ticket, dropped_frames=0, accepted_frames=len(writer.episode_buffer))
            mock_write.assert_called_once_with(metadata)
            mock_logger.info.assert_called_once()
        assert writer.receipts[0].status == "persisted"
        assert expected_path.is_file()
        immutable_path = writer.receipts[0].path
        assert immutable_path is not None
        assert immutable_path.is_file()
        assert immutable_path != expected_path
        assert not immutable_path.samefile(expected_path)
        assert immutable_path.read_bytes() == expected_path.read_bytes()

    def test_process_episode_end_should_record_false(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        writer = RecordingWriter(
            queue=queue.Queue(),
            config={"criteria": {"periodic": {"enabled": True, "interval": 100}}},
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        writer.episode_buffer.append(make_test_recorded_step(done=True))
        metadata = EpisodeMetadata(
            episode_id=42,
            survival_steps=1,
            total_reward=1.0,
            extrinsic_reward=1.0,
            intrinsic_reward=0.0,
            curriculum_stage=1,
            epsilon=0.5,
            intrinsic_weight=0.0,
            timestamp=1234567890.0,
            affordance_layout={"Bed": (2, 3)},
            affordance_visits={"Bed": 1},
            custom_action_uses={},
            completion_reason="authored_terminal",
            shaping_reward=0.0,
        )

        ticket = RecordingTicket(sequence=1, episode=metadata.episode_id, lane=0)
        with patch.object(writer, "_write_episode") as mock_write, patch("townlet.recording.recorder.logger") as mock_logger:
            writer._process_episode_end(metadata, ticket, dropped_frames=0, accepted_frames=len(writer.episode_buffer))
            mock_write.assert_not_called()
            mock_logger.debug.assert_called_once()
        assert writer.receipts[0].status == "not_selected"

    def test_should_record_episode_periodic_enabled(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        writer = RecordingWriter(
            queue=queue.Queue(),
            config={"criteria": {"periodic": {"enabled": True, "interval": 50}}},
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        metadata = make_test_episode_metadata(episode_id=100)
        assert writer._should_record_episode(metadata) is True

    def test_should_record_episode_periodic_disabled(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        writer = RecordingWriter(
            queue=queue.Queue(),
            config={"criteria": {"periodic": {"enabled": False, "interval": 50}}},
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        metadata = make_test_episode_metadata()
        assert writer._should_record_episode(metadata) is False

    def test_should_record_episode_no_criteria(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        writer = RecordingWriter(
            queue=queue.Queue(),
            config={"criteria": {}},
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        metadata = make_test_episode_metadata()
        assert writer._should_record_episode(metadata) is False

    def test_write_episode_with_lz4_compression(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        writer = RecordingWriter(
            queue=queue.Queue(),
            config={"compression": "lz4"},
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        writer.episode_buffer.append(make_test_recorded_step(done=True))
        writer._write_episode(make_test_episode_metadata(episode_id=42, survival_steps=1, total_reward=1.0))

        expected_path = recording_output_dir / "episode_000042.msgpack.lz4"
        assert expected_path.exists()
        assert expected_path.stat().st_size > 0

    def test_write_episode_no_compression(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        writer = RecordingWriter(
            queue=queue.Queue(),
            config={"compression": "none"},
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        writer.episode_buffer.append(make_test_recorded_step(done=True))
        writer._write_episode(make_test_episode_metadata(episode_id=99, survival_steps=1, total_reward=1.0))

        expected_path = recording_output_dir / "episode_000099.msgpack.lz4"
        assert expected_path.exists()

    def test_write_episode_with_database_insertion(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        mock_database = Mock()
        mock_database.recording_publication.return_value = nullcontext(1)
        mock_database.insert_scoped_recording.return_value = 7
        extra_dir = recording_output_dir / "nested"
        extra_dir.mkdir(exist_ok=True)

        writer = RecordingWriter(
            queue=queue.Queue(),
            config={"compression": "lz4", "criteria": {"periodic": {"enabled": True, "interval": 1}}},
            output_dir=extra_dir,
            database=mock_database,
            curriculum=None,
        )

        writer.episode_buffer.append(make_test_recorded_step(done=True))
        metadata = make_test_episode_metadata(episode_id=55, survival_steps=1, total_reward=1.0)
        ticket = RecordingTicket(sequence=1, episode=metadata.episode_id, lane=0)
        writer._process_episode_end(metadata, ticket, dropped_frames=0, accepted_frames=len(writer.episode_buffer))

        mock_database.recording_publication.assert_called_once_with(run_id=writer.run_id, episode_id=55, lane=0, legacy=True)
        mock_database.insert_scoped_recording.assert_called_once()
        call_kwargs = mock_database.insert_scoped_recording.call_args.kwargs
        expected_path = extra_dir / "episode_000055.msgpack.lz4"
        assert len(writer.receipts) == 1
        immutable_path = writer.receipts[0].path
        assert immutable_path is not None
        assert immutable_path.is_absolute()
        assert immutable_path.is_file()
        assert immutable_path != expected_path
        assert expected_path.is_file()
        assert not immutable_path.samefile(expected_path)
        published = immutable_path.read_bytes()
        assert expected_path.read_bytes() == published
        serialized = lz4.frame.decompress(published)
        payload = msgpack.unpackb(serialized, raw=False)
        assert call_kwargs["metadata"] == metadata
        assert call_kwargs["metadata"].episode_id == 55
        assert call_kwargs["legacy"] is True
        assert call_kwargs["reason"] == "periodic"
        assert call_kwargs["lane"] == 0
        assert call_kwargs["sequence"] == ticket.sequence
        assert call_kwargs["generation"] == 1
        assert call_kwargs["file_path"] == str(immutable_path)
        assert call_kwargs["legacy_file_path"] == "nested/episode_000055.msgpack.lz4"
        assert call_kwargs["file_sha256"] == hashlib.sha256(published).hexdigest()
        assert call_kwargs["frame_count"] == 1
        assert call_kwargs["final_done"] is True
        assert call_kwargs["file_size"] == len(serialized)
        assert call_kwargs["compressed_size"] == len(published)
        assert payload["metadata"]["episode_id"] == 55
        assert payload["metadata"]["total_reward"] == 1.0
        assert payload["steps"][0]["reward"] == 1.0
        assert payload["steps"][0]["done"] is True
        assert len(writer.receipts) == 1
        assert writer.receipts[0].status == "persisted"
        assert writer.receipts[0].path == immutable_path
        assert writer.receipts[0].index_id == 7
        assert not writer.errors

    def test_stop_method(self, recording_output_dir):
        from townlet.recording.recorder import RecordingWriter

        writer = RecordingWriter(
            queue=queue.Queue(),
            config={},
            output_dir=recording_output_dir,
            database=None,
            curriculum=None,
        )

        assert writer.running is True
        writer.stop()
        writer.writer_loop()
        assert writer.running is False
        assert writer.queue.unfinished_tasks == 0
