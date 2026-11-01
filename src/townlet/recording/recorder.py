"""Bounded episode capture with a fenced, durable background drain."""

import copy
import fcntl
import hashlib
import logging
import os
import queue
import tempfile
import threading
import uuid
from contextlib import ExitStack, contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path

import lz4.frame  # type: ignore[import-untyped]
import msgpack  # type: ignore[import-untyped]
import torch

from townlet.recording.data_structures import (
    RECORDING_FORMAT_VERSION,
    EpisodeEndMarker,
    EpisodeMetadata,
    RecordedStep,
    validate_recording_episode,
)
from townlet.recording.receipts import (
    LEGACY_RECORDING_RUN,
    RecordingDrainError,
    RecordingPublicationError,
    RecordingReceipt,
    RecordingTicket,
    StorageMode,
)

logger = logging.getLogger(__name__)
_STOP = object()
_root_registry_lock = threading.Lock()


class _RootGuard:
    def __init__(self):
        self.lock = threading.RLock()
        self.depth = 0
        self.descriptor = None


_root_guards: dict[Path, _RootGuard] = {}


@contextmanager
def _legacy_output_root_guard(output_root):
    """One persistent flock inode, with same-thread ownership shared by nesting."""
    root = Path(output_root).resolve()
    with _root_registry_lock:
        if root not in _root_guards:
            _root_guards[root] = _RootGuard()
        state = _root_guards[root]
    with state.lock:
        if state.depth == 0:
            descriptor = os.open(root / ".townlet-legacy-recording.lock", os.O_RDWR | os.O_CREAT, 0o600)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX)
            except Exception as primary:
                try:
                    os.close(descriptor)
                except Exception as cleanup:
                    raise ExceptionGroup("Output-root lock acquisition and cleanup failed", [primary, cleanup]) from primary
                raise
            state.descriptor = descriptor
        state.depth += 1
        primary_error = None
        try:
            yield
        except Exception as error:
            primary_error = error
            raise
        finally:
            state.depth -= 1
            if state.depth == 0:
                failures = []
                try:
                    fcntl.flock(state.descriptor, fcntl.LOCK_UN)
                except Exception as error:
                    failures.append(error)
                try:
                    os.close(state.descriptor)
                except Exception as error:
                    failures.append(error)
                state.descriptor = None
                if failures:
                    if primary_error is not None:
                        failures.insert(0, primary_error)
                    raise ExceptionGroup("Output-root lock release failed", failures)


@dataclass(frozen=True)
class _Capture:
    frame: RecordedStep
    sequence: int
    ticket: RecordingTicket | None


@dataclass(frozen=True)
class _Boundary:
    marker: EpisodeEndMarker
    ticket: RecordingTicket
    dropped_frames: int
    accepted_frames: int


def _sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _sync_directory_ancestry(path):
    """Re-establish namespace durability even after an earlier failed creator.

    Existence does not attest that a previous owner synced a newly created
    ancestor entry. Fresh recorders therefore verify the complete physical
    directory chain rather than trusting an in-memory creation ledger.
    """
    directory = Path(path).resolve()
    while True:
        _sync_directory(directory)
        parent = directory.parent
        if parent == directory:
            break
        directory = parent


class EpisodeRecorder:
    """Non-blocking bounded admission; close resolves every accepted item.

    The legacy constructor keeps its original output paths and lane-zero SQL
    visibility. Explicit scopes use disjoint namespaces and qualified lookups.
    A missing database is an explicit file-only mode, never an I/O fallback.
    """

    def __init__(self, config: dict, output_dir: Path, database, curriculum):
        self._initialize(config, output_dir, database, curriculum, LEGACY_RECORDING_RUN, 0, True)

    @classmethod
    def for_scope(cls, config, output_dir, database, curriculum, *, run_id, lane):
        if not isinstance(run_id, str) or not run_id or run_id == LEGACY_RECORDING_RUN:
            raise ValueError("A scoped recorder requires a nonempty, nonreserved exact run ID")
        if type(lane) is not int or lane < 0:
            raise ValueError("Recording lane must be a nonnegative integer")
        instance = cls.__new__(cls)
        instance._initialize(config, output_dir, database, curriculum, run_id, lane, False)
        return instance

    def _initialize(self, config, output_dir, database, curriculum, run_id, lane, legacy):
        self.config, self.database, self.curriculum = config, database, curriculum
        self.run_id, self.lane = run_id, lane
        self._legacy = legacy
        root = Path(output_dir).absolute()
        if legacy:
            self.output_dir = root
        else:
            namespace = hashlib.sha256(run_id.encode("utf-8")).hexdigest()
            self.output_dir = root / f"run-{namespace}" / f"lane-{lane}"
            if not self.output_dir.resolve().is_relative_to(root.resolve()):
                raise ValueError("Scoped output namespace escapes its recording root")
        self._admission = threading.RLock()
        self._shutdown_lock = threading.Lock()
        self._closing = False
        self._shutdown_result = None
        self._shutdown_error = None
        self._sequence = 0
        self._active_episode = None
        self._open_frames = 0
        self._group_dropped = 0
        self._legacy_dropped_frames = 0
        self._legacy_rejected_finishes = 0
        # Existing configuration omissions retain their established meaning.
        max_queue_size = config.get("max_queue_size", 1000)
        if type(max_queue_size) is not int or max_queue_size <= 0:
            raise ValueError("Recording queue capacity must be a positive integer")
        self.queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self.writer = RecordingWriter(self.queue, config, self.output_dir, database, curriculum)
        self.writer.run_id, self.writer.lane, self.writer.legacy = run_id, lane, legacy
        self.writer.path_root = root.parent
        self.writer_thread = threading.Thread(target=self.writer.writer_loop, daemon=True, name="RecordingWriter")
        self.writer_thread.start()

    def _ensure_accepting(self):
        if self._closing:
            raise RuntimeError("Recording admission is closed")
        if self.writer.errors:
            raise RuntimeError("Recording writer has failed") from self.writer.errors[0]

    @property
    def legacy_dropped_frames(self):
        with self._admission:
            return self._legacy_dropped_frames

    @property
    def legacy_rejected_finishes(self):
        with self._admission:
            return self._legacy_rejected_finishes

    def begin_episode(self, episode):
        with self._admission:
            self._ensure_accepting()
            if type(episode) is not int or episode < 0:
                raise ValueError("Recording episode must be a nonnegative integer")
            if self._active_episode is not None or self._open_frames:
                raise ValueError("Recording episode is already bound or has provisional frames")
            self._active_episode = episode

    def record_step(
        self,
        step: int,
        positions: torch.Tensor,
        meters: torch.Tensor,
        action: int,
        reward: float,
        extrinsic_reward: float,
        intrinsic_reward: float,
        shaping_reward: float,
        done: bool,
        q_values: torch.Tensor | None = None,
        epsilon: float | None = None,
        action_masks: torch.Tensor | None = None,
        time_of_day: int | None = None,
        interaction_progress: float | None = None,
    ):
        """Capture a frame, retaining the original None return contract."""
        self._capture(
            step,
            positions,
            meters,
            action,
            reward,
            extrinsic_reward,
            intrinsic_reward,
            shaping_reward,
            done,
            q_values,
            epsilon,
            action_masks,
            time_of_day,
            interaction_progress,
            False,
        )

    def record_bound_step(
        self,
        step,
        positions,
        meters,
        action,
        reward,
        extrinsic_reward,
        intrinsic_reward,
        shaping_reward,
        done,
        q_values,
        epsilon,
        action_masks,
        time_of_day,
        interaction_progress,
    ):
        """Return a frame ticket only for an actual explicitly bound episode."""
        return self._capture(
            step,
            positions,
            meters,
            action,
            reward,
            extrinsic_reward,
            intrinsic_reward,
            shaping_reward,
            done,
            q_values,
            epsilon,
            action_masks,
            time_of_day,
            interaction_progress,
            True,
        )

    def _capture(
        self,
        step,
        positions,
        meters,
        action,
        reward,
        extrinsic_reward,
        intrinsic_reward,
        shaping_reward,
        done,
        q_values,
        epsilon,
        action_masks,
        time_of_day,
        interaction_progress,
        return_ticket,
    ):
        with self._admission:
            self._ensure_accepting()
            if self._active_episode is None and (return_ticket or not self._legacy):
                raise ValueError("Qualified capture requires begin_episode")
            q_tuple = None
            if q_values is not None:
                if hasattr(q_values, "tolist"):
                    q_tuple = tuple(q_values.tolist())
                else:
                    q_tuple = tuple(q_values)
            mask_tuple = None
            if action_masks is not None:
                if hasattr(action_masks, "tolist"):
                    mask_tuple = tuple(action_masks.tolist())
                else:
                    mask_tuple = tuple(action_masks)
            frame = RecordedStep(
                step=step,
                position=tuple(int(positions[i].item()) for i in range(positions.shape[0])),
                meters=tuple(meters.tolist()),
                action=action,
                reward=reward,
                extrinsic_reward=extrinsic_reward,
                intrinsic_reward=intrinsic_reward,
                shaping_reward=shaping_reward,
                done=done,
                q_values=q_tuple,
                epsilon=epsilon,
                action_masks=mask_tuple,
                time_of_day=time_of_day,
                interaction_progress=interaction_progress,
            )
            ticket = None
            if return_ticket:
                ticket = RecordingTicket(self._sequence, self._active_episode, self.lane)
            try:
                self.queue.put_nowait(_Capture(frame, self._sequence, ticket))
            except queue.Full:
                if not self._legacy or return_ticket:
                    raise
                self._legacy_dropped_frames += 1
                self._group_dropped += 1
                logger.warning("Recording queue full (step %s), dropping frame", step)
                return None
            self._sequence += 1
            self._open_frames += 1
            return ticket

    def finish_episode(self, metadata: EpisodeMetadata):
        with self._admission:
            self._ensure_accepting()
            frozen = copy.deepcopy(metadata)
            episode = frozen.episode_id
            if type(episode) is not int or episode < 0:
                raise ValueError("Recording episode must be a nonnegative integer")
            if self._active_episode is not None and episode != self._active_episode:
                raise ValueError("Episode end conflicts with the bound recording episode")
            if not self._legacy and self._active_episode is None:
                raise ValueError("Scoped episode end requires begin_episode")
            ticket = RecordingTicket(self._sequence, episode, self.lane)
            try:
                self.queue.put_nowait(_Boundary(EpisodeEndMarker(metadata=frozen), ticket, self._group_dropped, self._open_frames))
            except queue.Full:
                if not self._legacy:
                    raise
                self._legacy_rejected_finishes += 1
                logger.error("Recording queue full, episode %s metadata lost", episode)
                return None
            self._sequence += 1
            self._active_episode = None
            self._open_frames = 0
            self._group_dropped = 0
            return ticket

    def shutdown(self):
        """Fence admission, enqueue its ordered sentinel, drain and join once."""
        with self._shutdown_lock:
            if self._shutdown_error is not None:
                raise self._shutdown_error
            if self._shutdown_result is not None:
                return self._shutdown_result
            with self._admission:
                self._closing = True
                empty_binding = self._active_episode is not None and self._open_frames == 0
                unended_drops = self._group_dropped
            self.writer.stop()
            self.writer_thread.join()
            receipts = tuple(self.writer.receipts)
            errors = list(self.writer.errors)
            if self.writer.running or self.queue.unfinished_tasks:
                errors.append(RuntimeError("Recording writer exited without resolving all accepted queue work"))
            if empty_binding:
                errors.append(ValueError(f"Bound episode {self._active_episode} has no end marker"))
            if unended_drops:
                errors.append(ValueError(f"Incomplete provisional recording group has {unended_drops} dropped frames"))
            if errors:
                self._shutdown_error = RecordingDrainError(self.run_id, receipts, errors, self.writer.unbound_sequences)
                raise self._shutdown_error from errors[0]
            self._shutdown_result = receipts
            return receipts


class RecordingWriter:
    """Single queue owner; I/O failure resolves work and never abandons drain."""

    def __init__(self, queue: queue.Queue, config: dict, output_dir: Path, database, curriculum):
        self.queue, self.config, self.output_dir = queue, config, Path(output_dir).absolute()
        self.database, self.curriculum = database, curriculum
        self.run_id, self.lane, self.legacy = LEGACY_RECORDING_RUN, 0, True
        self.path_root = self.output_dir.parent
        self.storage_mode: StorageMode
        if database is None:
            self.storage_mode = "file_only"
        else:
            self.storage_mode = "indexed"
        self.episode_buffer: list[RecordedStep] = []
        self._frame_tickets: list[RecordingTicket | None] = []
        self._frame_sequences: list[int] = []
        self._raw_sequence = 0
        self.receipts: list[RecordingReceipt] = []
        self.errors: list[Exception] = []
        self.unbound_sequences: list[int] = []
        self.running = True
        self._stop_lock = threading.Lock()
        self._stopping = False
        self._publication_path: Path | None = None
        self.output_dir.mkdir(parents=True, exist_ok=True)
        _sync_directory_ancestry(self.output_dir)

    def writer_loop(self):
        while True:
            item = self.queue.get()
            try:
                if item is _STOP:
                    if self.episode_buffer:
                        error = ValueError(f"Missing episode-end marker for accepted sequences {tuple(self._frame_sequences)}")
                        self.errors.append(error)
                        self.unbound_sequences.extend(
                            sequence for sequence, ticket in zip(self._frame_sequences, self._frame_tickets) if ticket is None
                        )
                        self._resolve(self._frame_tickets, "failed", None, None, error)
                    break
                if isinstance(item, (RecordedStep, EpisodeEndMarker)):
                    if not self.legacy:
                        self.errors.append(
                            ValueError("Bare recording queue items require the legacy writer; scoped capture requires binding")
                        )
                        continue
                    if isinstance(item, RecordedStep):
                        item = _Capture(item, self._raw_sequence, None)
                    else:
                        metadata = copy.deepcopy(item.metadata)
                        if type(metadata.episode_id) is not int or metadata.episode_id < 0:
                            self.errors.append(ValueError("Raw episode end requires an actual nonnegative episode identity"))
                            continue
                        ticket = RecordingTicket(self._raw_sequence, metadata.episode_id, self.lane)
                        item = _Boundary(EpisodeEndMarker(metadata=metadata), ticket, 0, len(self.episode_buffer))
                    self._raw_sequence += 1
                if isinstance(item, _Capture):
                    self.episode_buffer.append(item.frame)
                    self._frame_tickets.append(item.ticket)
                    self._frame_sequences.append(item.sequence)
                elif isinstance(item, _Boundary):
                    self._process_episode_end(item.marker.metadata, item.ticket, item.dropped_frames, item.accepted_frames)
                else:
                    self.errors.append(TypeError("Unsupported recording queue item"))
            finally:
                self.queue.task_done()
        self.running = False

    def _resolve(self, tickets, status, path, index_id, error):
        self.receipts.extend(
            RecordingReceipt(ticket, status, path, index_id, error, self.storage_mode) for ticket in tickets if ticket is not None
        )

    def _process_episode_end(self, metadata, ticket, dropped_frames, accepted_frames):
        tickets = [*self._frame_tickets, ticket]
        self._publication_path = None
        self._end_sequence = ticket.sequence
        try:
            if dropped_frames or accepted_frames != len(self.episode_buffer):
                raise ValueError(
                    f"Incomplete recording capture: accepted={accepted_frames}, dropped={dropped_frames}, actual={len(self.episode_buffer)}"
                )
            # Validate even unselected work; incomplete accepted capture is an error.
            payload = self._payload(metadata)
            validate_recording_episode(payload, expected_episode_id=metadata.episode_id)
            if self._should_record_episode(metadata):
                path, index_id = self._write_episode(metadata)
                self._resolve(tickets, "persisted", path, index_id, None)
            else:
                logger.debug("Skipped episode %s (no criteria matched)", metadata.episode_id)
                self._resolve(tickets, "not_selected", None, None, None)
        except Exception as error:
            if not isinstance(error, RecordingPublicationError):
                error = RecordingPublicationError(
                    phase="admission",
                    cause=error,
                    path=self._publication_path,
                    legacy_alias_path=None,
                    generation=None,
                    index_id=None,
                    alias_state="not_attempted",
                    canonical_state="not_attempted",
                    index_state="not_attempted",
                )
            self.errors.append(error)
            self._resolve(tickets, "failed", self._publication_path, None, error)
        finally:
            self.episode_buffer.clear()
            self._frame_tickets.clear()
            self._frame_sequences.clear()

    def _should_record_episode(self, metadata: EpisodeMetadata) -> bool:
        """Periodic selects today; other accepted criterion dictionaries remain intact."""
        criteria = self.config.get("criteria", {})
        periodic = criteria.get("periodic", {})
        if periodic.get("enabled", False):
            interval = periodic.get("interval", 100)
            if type(interval) is not int or interval <= 0:
                raise ValueError("Periodic recording interval must be a positive integer")
            return metadata.episode_id % interval == 0
        return False

    def _payload(self, metadata):
        return {
            "version": RECORDING_FORMAT_VERSION,
            "metadata": asdict(metadata),
            "steps": [asdict(step) for step in self.episode_buffer],
            "affordances": metadata.affordance_layout,
        }

    def _write_episode(self, metadata: EpisodeMetadata):
        phase = "admission"
        generation, index_id = None, None
        alias = None
        alias_state = canonical_state = index_state = "not_attempted"
        if self.legacy:
            alias = self.output_dir / f"episode_{metadata.episode_id:06d}.msgpack.lz4"
        try:
            with ExitStack() as guards:
                if self.legacy:
                    guards.enter_context(_legacy_output_root_guard(self.output_dir))
                if self.database is not None:
                    generation = guards.enter_context(
                        self.database.recording_publication(
                            run_id=self.run_id,
                            episode_id=metadata.episode_id,
                            lane=self.lane,
                            legacy=self.legacy,
                        )
                    )
                phase = "artifact"
                payload = self._payload(metadata)
                validate_recording_episode(payload, expected_episode_id=metadata.episode_id)
                serialized = msgpack.packb(payload, use_bin_type=True)
                compression = self.config.get("compression", "lz4")
                if compression == "lz4":
                    compressed = lz4.frame.compress(serialized, compression_level=0)
                else:
                    compressed = serialized
                final_path = self.output_dir / f"episode_{metadata.episode_id:06d}.msgpack.lz4"
                if self.legacy:
                    container = self.output_dir / ".recording-generations"
                    if not container.exists():
                        container.mkdir()
                        _sync_directory(container)
                        _sync_directory(self.output_dir)
                    while True:
                        directory = container / uuid.uuid4().hex
                        try:
                            directory.mkdir()
                        except FileExistsError:
                            continue
                        break
                    _sync_directory(directory)
                    _sync_directory(container)
                    final_path = directory / final_path.name
                self._publish_file(final_path, compressed, False)
                self._verify_artifact(final_path, compressed, compression, metadata.episode_id)
                legacy_file_path = None
                if alias is not None:
                    phase, alias_state = "alias", "unconfirmed"
                    self._publish_file(alias, compressed, True)
                    if alias.read_bytes() != compressed:
                        raise OSError("Canonical recording alias readback differs from its immutable artifact")
                    alias_state = "confirmed"
                    legacy_file_path = str(alias.relative_to(self.path_root))
                if self.database is not None:
                    phase = "index"
                    final_done = False
                    if self.episode_buffer:
                        final_done = self.episode_buffer[-1].done
                    index_id = self.database.insert_scoped_recording(
                        run_id=self.run_id,
                        lane=self.lane,
                        sequence=self._end_sequence,
                        generation=generation,
                        file_path=str(final_path),
                        legacy_file_path=legacy_file_path,
                        file_sha256=hashlib.sha256(compressed).hexdigest(),
                        frame_count=len(self.episode_buffer),
                        final_done=final_done,
                        metadata=metadata,
                        legacy=self.legacy,
                        reason="periodic",
                        file_size=len(serialized),
                        compressed_size=len(compressed),
                    )
                    index_state = "confirmed"
                    if self.legacy:
                        canonical_state = "confirmed"
                phase = "reconciliation"
                self._verify_artifact(final_path, compressed, compression, metadata.episode_id)
                if alias is not None and alias.read_bytes() != compressed:
                    alias_state = "unconfirmed"
                    raise OSError("Canonical recording alias changed before publication completed")
            logger.info("Recorded episode %s, run %r, lane %s", metadata.episode_id, self.run_id, self.lane)
            return final_path, index_id
        except Exception as error:
            cause = error
            pending: list[BaseException] = [error]
            observation = None
            while pending:
                candidate = pending.pop(0)
                if isinstance(candidate, RecordingPublicationError):
                    observation = candidate
                    break
                if isinstance(candidate, BaseExceptionGroup):
                    pending[0:0] = candidate.exceptions
            if observation is not None:
                phase = observation.phase
                if observation is error:
                    cause = observation.cause
                # A cleanup group must remain whole: its primary observations
                # are retained without discarding any publication/release cause.
                canonical_state, index_state = observation.canonical_state, observation.index_state
                if observation.generation is not None:
                    generation = observation.generation
                if observation.index_id is not None:
                    index_id = observation.index_id
            raise RecordingPublicationError(
                phase=phase,
                cause=cause,
                path=self._publication_path,
                legacy_alias_path=alias,
                generation=generation,
                index_id=index_id,
                alias_state=alias_state,
                canonical_state=canonical_state,
                index_state=index_state,
            ) from error

    def _publish_file(self, path, data, replace_alias):
        descriptor, temporary_name = tempfile.mkstemp(prefix=".recording-", dir=path.parent)
        temporary = Path(temporary_name)
        primary_error = None
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if replace_alias:
                os.replace(temporary, path)
            else:
                os.link(temporary, path)
                self._publication_path = path
        except Exception as error:
            primary_error = error
            raise
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except Exception as cleanup:
                if primary_error is not None:
                    raise ExceptionGroup("Recording publication and temporary cleanup failed", [primary_error, cleanup]) from primary_error
                raise
        _sync_directory(path.parent)

    def _verify_artifact(self, path, expected, compression, episode):
        published = path.read_bytes()
        if published != expected:
            raise OSError("Published recording bytes differ from the durable capture")
        if compression == "lz4":
            readback = lz4.frame.decompress(published)
        else:
            readback = published
        validate_recording_episode(msgpack.unpackb(readback, raw=False), expected_episode_id=episode)

    def stop(self):
        with self._stop_lock:
            if not self._stopping:
                self._stopping = True
                self.queue.put(_STOP)
