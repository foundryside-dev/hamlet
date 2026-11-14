"""Demo runner for multi-day training."""

from __future__ import annotations

import copy
import json
import logging
import signal
import time
from collections import defaultdict
from pathlib import Path
from types import MappingProxyType
from typing import Any

import numpy as np
import torch

from townlet.config.exploration_policy import ExplorationRuntime, build_exploration
from townlet.config.resolved_launch import resolve_launch
from townlet.config.world_roster import WorldRosterDeclaration, canonical_bytes
from townlet.curriculum.base import CurriculumManager
from townlet.curriculum.factory import build_curriculum
from townlet.demo.database import DemoDatabase
from townlet.determinism import seed_all
from townlet.environment.vectorized_env import VectorizedHamletEnv, WorldReceiptIssuer
from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.checkpoint_utils import (
    CHECKPOINT_FORMAT_VERSION,
    assert_checkpoint_identity,
    attach_universe_metadata,
    persist_checkpoint_digest,
    safe_torch_load,
    validate_demo_checkpoint_payload,
    validate_demo_checkpoint_runtime_fields,
    validate_demo_native_boundary,
    verify_checkpoint_digest,
)
from townlet.training.episode import RunnerCompletionReason, freeze_lane_outcome
from townlet.training.native_rng import NativeRNGState
from townlet.training.state import BatchedAgentState
from townlet.training.tensorboard_logger import TensorBoardLogger
from townlet.universe.compiled import CompiledUniverse

logger = logging.getLogger(__name__)


def resolve_training_status(*, failed: bool, should_shutdown: bool, budget_reached: bool, episodes_reached: bool) -> str:
    """Name how a training loop ended; a graceful stop short of its budget is not ``completed``.

    A shutdown request truncates the episode it lands in, so it outranks the episode
    limit: only a reached transition budget makes a shut-down run ``completed``.
    """
    if failed:
        return "failed"
    if budget_reached:
        return "completed"
    if should_shutdown:
        return "interrupted"
    if episodes_reached:
        return "completed"
    raise ValueError("training loop exited without a terminal cause")


def decide_live_agent_budget(*, completed: int, live_agents: int, budget: int) -> tuple[bool, int]:
    """Decide whether one indivisible vector step fits a live-agent transition budget.

    Returns ``(may_step, shortfall)``. The shortfall is non-zero only when the
    remaining budget cannot fit all currently live lanes, so callers stop before
    the vector step rather than overshooting or injecting a partial batch.
    """
    values = {"completed": completed, "live_agents": live_agents, "budget": budget}
    for name, value in values.items():
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{name} must be an integer")
    if completed < 0:
        raise ValueError("completed must be non-negative")
    if live_agents <= 0:
        raise ValueError("live_agents must be positive")
    if budget <= 0:
        raise ValueError("budget must be positive")
    if completed > budget:
        raise ValueError("completed cannot exceed budget")
    remaining = budget - completed
    return (True, 0) if live_agents <= remaining else (False, remaining)


class DemoRunner:
    """Orchestrates multi-day demo training with checkpointing."""

    HEARTBEAT_INTERVAL = 10
    SUMMARY_INTERVAL = 50

    def __init__(
        self,
        config_dir: Path | str,
        db_path: Path | str,
        checkpoint_dir: Path | str,
        max_episodes: int | None = None,
        *,
        world_roster: WorldRosterDeclaration,
        level_name: str | None = None,
        force_new_vfs: bool = False,
        max_environment_steps: int | None = None,
    ):
        """Initialize demo runner.

        Args:
            config_dir: Authored experiment root or direct levels/<name> directory.
            level_name: Explicit curriculum selection; may be inferred only when unambiguous.
            db_path: Path to SQLite database
            checkpoint_dir: Directory for checkpoint files
            world_roster: Explicit immutable declaration of the run's logical worlds.
            max_episodes: Explicit runtime limit; omission uses selected effective training.
            force_new_vfs: Start a fresh run branch instead of resuming an incompatible VFS checkpoint.
            max_environment_steps: Optional summed-live-agent transition budget.
                A vector step is taken only when every currently live lane fits.
        """
        # Resolve and validate before allocating runtime files/logger resources.
        if not isinstance(world_roster, WorldRosterDeclaration):
            raise ValueError("world_roster requires a WorldRosterDeclaration")
        self.resolved_launch = resolve_launch(Path(config_dir), level_name=level_name)
        self.config_dir = self.resolved_launch.root
        self.level_name = self.resolved_launch.level_name
        self.compiled: CompiledUniverse = self.resolved_launch.compiled
        self.effective_run = self.resolved_launch.effective
        self.training_config_origin = self.resolved_launch.declaration_origins[f"levels/{self.level_name}/training"]
        source_path, separator, source_line = self.training_config_origin.rpartition(":")
        if not separator or not source_line.isdecimal() or int(source_line) < 1 or not Path(source_path).is_absolute():
            raise ValueError("Resolved training origin must contain an absolute declaration path and authored line")
        self.training_config_path = Path(source_path)
        overrides = {}
        if max_episodes is not None:
            overrides["max_episodes"] = max_episodes
        self.launch_overrides = MappingProxyType(overrides)
        self.db_path = Path(db_path)
        self.checkpoint_dir = Path(checkpoint_dir)
        if len(world_roster.world_ids) != self.effective_run.training.population.size:
            raise ValueError("world roster cardinality must match the selected population")
        self.world_roster = world_roster
        self.world_roster_path = self.checkpoint_dir.parent / "run-world-roster.json"
        self.force_new_vfs = force_new_vfs
        if max_environment_steps is not None and (
            not isinstance(max_environment_steps, int) or isinstance(max_environment_steps, bool) or max_environment_steps <= 0
        ):
            raise ValueError("max_environment_steps must be a positive integer or None")
        self.max_environment_steps = max_environment_steps
        self.completed_live_agent_steps = 0
        self.environment_step_budget_shortfall = 0
        self.environment_step_budget_reached = False

        # The run declaration is immutable and precedes database/logger/RNG setup.
        roster_bytes = canonical_bytes(world_roster.to_dict()) + b"\n"
        if self.world_roster_path.exists():
            self._validate_world_roster_manifest(roster_bytes)
        elif self.db_path.exists() or (self.checkpoint_dir.exists() and any(self.checkpoint_dir.iterdir())):
            raise ValueError("existing run is missing its world roster manifest")
        else:
            self.checkpoint_dir.parent.mkdir(parents=True, exist_ok=True)
            try:
                with self.world_roster_path.open("xb") as stream:
                    stream.write(roster_bytes)
            except FileExistsError:
                self._validate_world_roster_manifest(roster_bytes)

        # Create directories
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self.db = DemoDatabase(self.db_path)

        # Initialize TensorBoard logger
        # If checkpoint_dir is in a structured run (e.g., runs/L1_full_observability/2025-11-02_143022/checkpoints)
        # then tensorboard should be at sibling level, not inside checkpoints
        parent_dir = self.checkpoint_dir.parent
        if parent_dir.parent.parent.name == "runs" and self.checkpoint_dir.name == "checkpoints":
            # New structure: runs/LX_name/timestamp/checkpoints -> use runs/LX_name/timestamp/tensorboard
            tb_log_dir = parent_dir / "tensorboard"
        else:
            # Old structure or direct invocation: put tensorboard inside checkpoint_dir
            tb_log_dir = self.checkpoint_dir / "tensorboard"

        self.tb_logger = TensorBoardLogger(
            log_dir=tb_log_dir,
            flush_every=10,
        )

        # Reuse the selected compilation; do not reread a transport-specific file.
        level_config = self.compiled.get_level(self.level_name)
        self.experiment_config = self.compiled.experiment
        self.stratum_config = self.compiled.stratum
        self.environment_config = self.compiled.environment
        self.actions_config = self.compiled.actions
        self.brain_config = self.compiled.brain
        self.curriculum_config = level_config.curriculum
        self.bars_config = level_config.bars
        self.affordances_config = level_config.affordances
        self.training_config = level_config.training
        # Seed every RNG stream before anything random is constructed; the seed is
        # config-declared so the run is reproducible from its own checkpoint.
        seed_all(self.training_config.seed)
        # Set max_episodes: use provided value, otherwise read from curriculum training config
        if max_episodes is not None:
            self.max_episodes = max_episodes
        else:
            self.max_episodes = self.effective_run.training.training_loop.max_episodes

        self.current_episode = 0

        # Initialize components (will be created in run())
        self.env: VectorizedHamletEnv | None = None
        self.population: VectorizedPopulation | None = None
        self.curriculum: CurriculumManager | None = None
        self._last_native_checkpoint: dict[str, Any] | None = None
        self.exploration: ExplorationRuntime | None = None
        self.recorder = None  # Episode recorder (initialized if recording enabled)

        # Shutdown flag
        self.should_shutdown = False
        # Signal handlers only work in main thread
        try:
            signal.signal(signal.SIGTERM, self._handle_shutdown)
            signal.signal(signal.SIGINT, self._handle_shutdown)
        except ValueError:
            # Running in a worker thread (e.g., unified server)
            # Signal handling will be done by the orchestrator
            pass

    def _validate_world_roster_manifest(self, expected: bytes) -> None:
        """Refuse missing, malformed or changed persisted run identity without mutation."""
        try:
            actual = self.world_roster_path.read_bytes()
            declared = WorldRosterDeclaration.from_dict(json.loads(actual))
        except (OSError, ValueError, TypeError) as error:
            raise ValueError("invalid world roster manifest") from error
        if declared != self.world_roster or actual != expected:
            raise ValueError("world roster manifest differs from the supplied declaration")

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signal gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_shutdown = True

    def _cleanup(self):
        """Internal cleanup method for resources.

        Safe to call multiple times (idempotent).
        Handles partial initialization gracefully.
        """
        # Shutdown recorder if enabled
        if hasattr(self, "recorder") and self.recorder is not None:
            logger.info("Shutting down episode recorder...")
            try:
                self.recorder.shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down recorder: {e}")

        # Close database connection
        if hasattr(self, "db"):
            try:
                self.db.close()
            except Exception as e:
                logger.warning(f"Error closing database: {e}")

        # Close TensorBoard logger
        if hasattr(self, "tb_logger"):
            try:
                self.tb_logger.close()
            except Exception as e:
                logger.warning(f"Error closing TensorBoard logger: {e}")

    def __enter__(self):
        """Enter context manager - return self for 'with' statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - cleanup resources.

        Args:
            exc_type: Exception type if exception occurred
            exc_val: Exception value if exception occurred
            exc_tb: Exception traceback if exception occurred

        Returns:
            False to propagate exceptions (don't suppress)
        """
        self._cleanup()
        return False  # Don't suppress exceptions

    def flush_all_agents(self):
        """Flush unfinished, participating lanes without repeating completed effects."""
        if not self.population:
            return

        for agent_idx in range(self.population.num_agents):
            if int(self.population.episode_step_counts[agent_idx]) > 0 and not bool(self.population.episode_completed[agent_idx]):
                self.population.flush_episode(agent_idx, reason="checkpoint")

    def _complete_training_episode(self) -> None:
        """Commit actual learner effects before granting the next ENV boundary."""
        population, runtime, curriculum, env = self.population, self.exploration, self.curriculum, self.env
        if population is None or runtime is None or curriculum is None or env is None:
            raise RuntimeError("Episode completion requires initialized training components")
        accepted = self.accepted_episode
        events = tuple(sorted(population.completed_outcomes, key=lambda event: event.outcome.agent_idx))
        if not events:
            raise RuntimeError("Nonempty completion requires actual population outcomes")
        frozen = tuple(map(freeze_lane_outcome, events))
        content = tuple((item.payload.hex(), item.fingerprint) for item in frozen)
        participants = tuple(event.world_id for event in events)
        batch = accepted.batch_episode
        before_count = population.clock_ledger.completed_batch_episodes
        before_epsilon = runtime.epsilon
        work = {"batch_episode": batch, "completion_content": content, "stage": "preparing"}
        self.boundary_work = work
        curriculum_prepared = curriculum.prepare_episode_outcomes(events)
        bank_prepared = runtime.prepare_completion(
            accepted=accepted,
            boundary_key=batch,
            completion_content=content,
            outcomes=events,
            participated_world_ids=participants,
        )
        close = env.prepare_episode_close(
            accepted=accepted,
            boundary_key=batch,
            completion_content=content,
            participated_world_ids=participants,
            dispositions=bank_prepared.prepared_receipt,
        )
        work.update(curriculum_prepared=curriculum_prepared, bank_prepared=bank_prepared, close=close)
        env.freeze_episode_close(close)
        work["stage"] = "curriculum_in_progress"
        curriculum.commit_prepared_episode_outcomes(curriculum_prepared)
        curriculum_state = curriculum.checkpoint_state()
        curriculum.validate_checkpoint_state(curriculum_state)
        committed = {tuple(entry["identity"]): entry["fingerprint"] for entry in curriculum_state["completion"]["events"]}
        if any(
            committed.get((event.batch_episode, event.outcome.agent_idx)) != reading.fingerprint for event, reading in zip(events, frozen)
        ):
            raise RuntimeError("Curriculum did not retain the actual population completions")
        work["stage"] = "curiosity_in_progress"
        retirement = runtime.commit_completion(prepared=bank_prepared)
        work.update(retirement=retirement, stage="population_in_progress")
        population.commit_episode_outcomes(events)
        if population.clock_ledger.completed_batch_episodes != before_count + 1:
            raise RuntimeError("Population did not commit exactly one completed batch")
        progress = population.batch_commit_progress
        if progress is None or progress["batch_episode"] != batch or progress["status"] != "completed":
            raise RuntimeError("Population completion remains unresolved")
        expected_epsilon = max(self.effective_run.exploration.epsilon_end, before_epsilon * self.effective_run.exploration.epsilon_decay)
        cadence = runtime.checkpoint_state()["cadence"]["last_committed"]
        if (
            cadence
            != {
                "batch_episode": batch,
                "completion_content": content,
                "epsilon_before": before_epsilon,
                "epsilon_after": expected_epsilon,
            }
            or runtime.epsilon != expected_epsilon
        ):
            raise RuntimeError("Runtime cadence does not attest this completed batch")
        work["stage"] = "selection_in_progress"
        population.sync_exploration_metrics()
        if not torch.equal(population.current_epsilons, torch.full_like(population.current_epsilons, expected_epsilon)):
            raise RuntimeError("Population selection inputs do not reflect committed epsilon")
        work["stage"] = "effects_verified"
        payload = {"accepted": accepted, "boundary_key": batch, "completion_content": content}
        children = {
            name: WorldReceiptIssuer(owner=owner).issue(kind=name, payload=payload)
            for name, owner in (
                ("curriculum_receipt", curriculum),
                ("exploration_receipt", runtime),
                ("population_commit_receipt", population),
                ("epsilon_install_receipt", runtime),
                ("selection_sync_receipt", runtime),
            )
        }
        closure = env.close_episode(close, dispositions=retirement)
        work.update(closure=closure, stage="release_in_progress")
        effects = WorldReceiptIssuer(owner=self).issue(
            kind="boundary_effects",
            payload={
                "batch_episode": batch,
                "accepted_identity": accepted,
                "completion_content": content,
                "retirement_receipt": closure.dispositions,
                **children,
            },
        )
        release = self.boundary_authority.completed(closure=closure, effects=effects)
        env.install_boundary_release(release)
        self.boundary_release = release
        work.update(stage="completed", release=release)
        self._capture_native_boundary()

    def _capture_native_component_data(self, *, kind: str) -> dict[str, Any]:
        """Own boundary data before attestation; this alone grants no ENV authority.

        The native controller must add its authentic world snapshot and coherent
        outer RNG state before retaining or persisting a resumable artifact.
        """
        env, population, curriculum = self.env, self.population, self.curriculum
        if env is None or population is None or curriculum is None:
            raise RuntimeError("Native snapshot requires initialized training owners")
        phases = {"INITIAL": "bootstrap-ready", "COMPLETED": "released-completed"}
        if kind not in phases or env.world_phase != phases[kind]:
            raise ValueError("Native snapshot requires an actual INITIAL or COMPLETED boundary")
        release = self.boundary_release
        if release is None:
            raise ValueError("Native snapshot requires its installed boundary release")
        if kind == "INITIAL":
            mode = "initial"
        else:
            mode = "completed_boundary"
        population_state = population.capture_native_checkpoint_data(mode=mode)
        curriculum_state = copy.deepcopy(curriculum.checkpoint_state())
        curriculum.validate_checkpoint_state(curriculum_state)
        layout = copy.deepcopy(env.get_affordance_positions())
        env.validate_affordance_positions(layout)
        persistent = copy.deepcopy(env.vfs_registry.persistent_state())
        env.vfs_registry.validate_persistent_state(persistent)
        completed = population_state["clock_ledger"]["completed_batch_episodes"]
        if release.next_batch_episode != completed:
            raise ValueError("Runner release and completed native population count disagree")
        return {
            "population_state": population_state,
            "curriculum_state": curriculum_state,
            "affordance_layout": layout,
            "vfs_persistent_state": persistent,
            "agent_ids": copy.deepcopy(population.agent_ids),
            "episode": completed,
            "epsilon": population._get_current_epsilon_value(),
            "completed_live_agent_steps": self.completed_live_agent_steps,
        }

    def _capture_native_boundary(self) -> None:
        """Retain one fully owned lawful boundary, including its ambient RNG state."""
        if self.env is None or self.population is None or self.curriculum is None:
            raise RuntimeError("Native capture requires actual initialized owners")
        env, population = self.env, self.population
        if env.world_phase == "bootstrap-ready":
            kind = "INITIAL"
        else:
            kind = "COMPLETED"
        components = self._capture_native_component_data(kind=kind)
        initial = None
        if kind == "INITIAL":
            state = components["population_state"]
            common = dict(
                semantic_execution_identity=env.semantic_execution_identity,
                bootstrap_first_batch=self.boundary_release.next_batch_episode,
                world_binding=env.world_ids,
            )
            readings = {
                "population": (population, state),
                "curriculum": (self.curriculum, components["curriculum_state"]),
                "exploration": (self.exploration, state["exploration_state"]),
                "network": (population.q_network, state["q_network"]),
                "optimizer": (population.optimizer, state["optimizer"]),
                "scheduler": (population if population.scheduler is None else population.scheduler, state["scheduler"]),
                "replay": (population.replay_buffer, state["replay_buffer"]),
                "selection": (self.exploration, state["exploration_state"]["selector"]),
            }
            children = {
                role: WorldReceiptIssuer(owner=owner).issue(kind="initial_owner", payload=dict(role=role, state=reading, **common))
                for role, (owner, reading) in readings.items()
            }
            proof = WorldReceiptIssuer(owner=self).issue(kind="initial_owners", payload=dict(children, **common))
            initial = self.boundary_authority.prepare_initial_snapshot(release=self.boundary_release, owners=proof)
        world = env.checkpoint_world_state(
            kind=kind, release=self.boundary_release, retained_binding_batches=env.accepted_binding_batches(), initial=initial
        )
        checkpoint: dict[str, Any] = {
            "version": CHECKPOINT_FORMAT_VERSION,
            "timestamp": time.time(),
            "substrate_metadata": {
                "position_dim": env.substrate.position_dim,
                "substrate_type": type(env.substrate).__name__,
            },
            **components,
            "vfs_random_state": copy.deepcopy(world["vfs_random_context"]),
            "native_boundary": {"kind": kind, "world_state": world, "rng_state": self.native_rng.capture()},
            "training_config": self.training_config.model_dump(),
            "config_dir": str(self.config_dir),
        }

        # WS-1 task 5: unconditional. The old `if universe is not None:` skip meant a
        # checkpoint could be written with ZERO provenance keys, making every guard vacuous.
        attach_universe_metadata(checkpoint, self.compiled)
        validate_demo_checkpoint_payload(checkpoint)
        validate_demo_checkpoint_runtime_fields(
            checkpoint,
            position_dim=env.substrate.position_dim,
            substrate_type=type(env.substrate).__name__,
            num_agents=population.num_agents,
        )

        validate_demo_native_boundary(checkpoint, cuda_devices=self.native_cuda_devices)
        self._last_native_checkpoint = checkpoint

    def save_checkpoint(self) -> None:
        """Persist the last lawful boundary, including after zero-step quarantine."""
        checkpoint = self._last_native_checkpoint
        if checkpoint is None:
            raise RuntimeError("No genuine native boundary has been captured")
        checkpoint_path = self.checkpoint_dir / f"checkpoint_ep{checkpoint['episode']:05d}.pt"
        torch.save(checkpoint, checkpoint_path)
        persist_checkpoint_digest(checkpoint_path)
        logger.info(f"Checkpoint saved: {checkpoint_path}")

        # Update system state
        self.db.set_system_state("last_checkpoint", str(checkpoint_path))

    def load_checkpoint(self) -> int | None:
        """Load latest checkpoint if exists.

        Returns:
            Episode number of loaded checkpoint, or None if no checkpoint
            (or when force-new-VFS explicitly branches instead of resuming)
        """
        if self.env is None or self.population is None or self.curriculum is None or self.exploration is None:
            raise RuntimeError("Checkpoint load requires initialized env, population, and curriculum components.")

        env = self.env
        population = self.population
        curriculum = self.curriculum

        # Find latest checkpoint
        checkpoints = sorted(self.checkpoint_dir.glob("checkpoint_ep*.pt"))
        if not checkpoints:
            logger.info("No checkpoints found, starting from scratch")
            return None

        latest_checkpoint = checkpoints[-1]
        logger.info(f"Loading checkpoint: {latest_checkpoint}")

        verify_checkpoint_digest(latest_checkpoint, required=True)
        # The verified digest pins the trusted Python payload we unpickle below.
        checkpoint = safe_torch_load(latest_checkpoint, allow_unsafe_pickle=True)
        validate_demo_checkpoint_payload(checkpoint)

        # WS-1 task 5: the shared identity gate (format version, VFS ABI, dimensions,
        # content hashes, primary_level). The serving path runs the identical chain.
        if not assert_checkpoint_identity(checkpoint, self.compiled, force_new_vfs=self.force_new_vfs):
            return None

        # Validate every outer and nested runtime-bound value before mutation.
        validate_demo_checkpoint_runtime_fields(
            checkpoint,
            position_dim=env.substrate.position_dim,
            substrate_type=type(env.substrate).__name__,
            num_agents=population.num_agents,
        )
        completed_live_agent_steps = checkpoint["completed_live_agent_steps"]
        if self.max_environment_steps is not None and completed_live_agent_steps > self.max_environment_steps:
            raise ValueError(
                "Checkpoint completed_live_agent_steps exceeds this run's environment-step budget: "
                f"checkpoint={completed_live_agent_steps}, budget={self.max_environment_steps}."
            )
        validate_demo_native_boundary(checkpoint, cuda_devices=self.native_cuda_devices)
        native = checkpoint["native_boundary"]
        ledger = checkpoint["population_state"]["clock_ledger"]
        if (
            checkpoint["episode"] != ledger["completed_batch_episodes"]
            or completed_live_agent_steps != ledger["eligible_transitions"]
            or checkpoint["epsilon"] != checkpoint["population_state"]["exploration_state"]["selector"]["epsilon"]
        ):
            raise ValueError("Runner continuation fields disagree with the actual native population state")
        if native["kind"] == "INITIAL":
            mode = "initial"
        else:
            mode = "completed_boundary"
        self.exploration.validate_restore_data(state=checkpoint["population_state"]["exploration_state"], mode=mode)
        plan = population.prepare_native_checkpoint_data(checkpoint["population_state"], mode=mode)
        replay_data = population.replay_buffer.stage_native_restore(
            population.native_replay_restore_state(plan=plan), expected_obs_dim=env.observation_dim, parent_plan=plan, lineage=None
        )
        curriculum_data = curriculum.prepare_native_state(checkpoint["curriculum_state"], parent_plan=plan)
        layout_data = env.prepare_native_layout(checkpoint["affordance_layout"], parent_plan=plan)
        persistent_data = env.vfs_registry.prepare_native_persistent_state(checkpoint["vfs_persistent_state"], env=env, parent_plan=plan)
        rng_data = self.native_rng.prepare(native["rng_state"], parent=population, parent_plan=plan)
        world_prepared = env.prepare_world_restore(
            kind=native["kind"],
            state=native["world_state"],
            world_roster=self.world_roster,
            destination_world_ids=env.world_ids,
            semantic_execution_identity=env.semantic_execution_identity,
        )

        def validate_parent_restore(*, prepared: Any, curiosity_state: Any) -> None:
            if prepared is not world_prepared:
                raise ValueError("Native parent comparator received another world preparation")
            population.validate_native_parent_restore(plan=plan, prepared=prepared, curiosity_state=curiosity_state)

        def finalize_component(*, restored: Any) -> None:
            population.install_native_model_data(plan=plan, attempt=attempt, restored=restored)
            population.replay_buffer.install_native_restore(replay_data, parent_plan=plan, attempt=attempt, restored=restored, lineage=None)
            curriculum.install_native_state(prepared=curriculum_data, parent_plan=plan, attempt=attempt, restored=restored)
            env.install_native_layout(prepared=layout_data, parent_plan=plan, attempt=attempt, restored=restored)
            env.vfs_registry.install_native_persistent_state(
                prepared=persistent_data, env=env, parent_plan=plan, attempt=attempt, restored=restored
            )
            self.native_rng.install(prepared=rng_data, parent_plan=plan, attempt=attempt, restored=restored)
            population.finish_native_checkpoint_data(plan=plan, attempt=attempt, restored=restored)

        with self.boundary_authority.restore_runtime_attempt(
            prepared=world_prepared,
            runtime=self.exploration,
            validate_parent_restore=validate_parent_restore,
            finalize_component=finalize_component,
        ) as attempt:
            with population.native_restore_cadence(plan=plan, prepared=world_prepared):
                attempt.prepare_child(state=checkpoint["population_state"]["exploration_state"], mode=mode)
            boundary = WorldReceiptIssuer(owner=self).issue(
                kind="restored_boundary", payload={"kind": native["kind"], "state": native["world_state"], "prepared": world_prepared}
            )
            attempt.issue_release(boundary=boundary)
            with population.native_restore_cadence(plan=plan, prepared=world_prepared):
                attempt.install_child()
            attempt.install_world()
            release = attempt.finish()
        self.boundary_release = release
        self._last_native_checkpoint = checkpoint
        population.agent_ids = checkpoint["agent_ids"]
        self.current_episode = checkpoint["episode"]
        self.completed_live_agent_steps = completed_live_agent_steps
        if self.max_environment_steps is not None:
            self.environment_step_budget_shortfall = self.max_environment_steps - completed_live_agent_steps
            self.environment_step_budget_reached = completed_live_agent_steps == self.max_environment_steps

        logger.info(f"Resumed from episode {self.current_episode}")
        return self.current_episode

    def run(self):
        """Run demo training loop."""
        self._validate_world_roster_manifest(canonical_bytes(self.world_roster.to_dict()) + b"\n")
        logger.info(f"Starting demo runner: {self.max_episodes} episodes")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Checkpoints: {self.checkpoint_dir}")

        # PDR-002: No-defaults validation done automatically by config DTOs
        # All required parameters validated at load time

        # Initialize training components
        # v2.1: device is an infrastructure concern (no-defaults exemption).
        if torch.cuda.is_available():
            device = torch.device("cuda", torch.cuda.current_device())
        else:
            device = torch.device("cpu")

        # Per-level metadata
        level_meta = self.compiled.get_level(self.level_name)
        # Extract config parameters from DTOs (all required, validated at load time)
        effective_training = self.effective_run.training
        loop_cfg = effective_training.training_loop
        num_agents = effective_training.population.size
        grid_cells = self.compiled.metadata.grid_cells
        partial_observability = level_meta.curriculum.curriculum.active_vision != "global"
        vision_range = level_meta.curriculum.curriculum.vision_range
        enable_temporal_mechanics = level_meta.curriculum.curriculum.active_temporal

        # Create environment from compiled universe
        self.env = VectorizedHamletEnv.from_universe(
            self.compiled,
            level_name=self.level_name,
            num_agents=num_agents,
            device=device,
            world_roster=self.world_roster,
            training_seed=effective_training.seed,
            lane_world_ids=self.world_roster.world_ids,
        )

        # Dimensions sourced from compiled metadata
        obs_dim = level_meta.token_spec.total_dims
        action_dim = level_meta.action_metadata.total_actions

        # Create curriculum (all params required per PDR-002)
        self.curriculum = build_curriculum(
            effective_training,
            curriculum_options=self.effective_run.options.curriculum,
            static_policy=self.effective_run.static_policy,
            device=device,
        )

        # Resolved authoring selects the provider family and curiosity scope.
        # Retain the actual BANK owner, distinct from its runtime facade.
        def curiosity_issuer(bank: Any) -> WorldReceiptIssuer:
            self.curiosity_bank = bank
            return WorldReceiptIssuer(owner=bank)

        def validate_committed_batch(*, batch_episode: int, outcomes: tuple[Any, ...]) -> None:
            if self.population is None:
                raise RuntimeError("Exploration requires its constructed population owner")
            self.population.validate_committed_batch(batch_episode=batch_episode, outcomes=outcomes)

        def validate_parent_cadence(*, cadence: Any, mode: str, accepted: Any, parent_restore: Any) -> None:
            if self.population is None:
                raise RuntimeError("Exploration requires its constructed population owner")
            self.population.validate_parent_cadence(cadence=cadence, mode=mode, accepted=accepted, parent_restore=parent_restore)

        descriptor = WorldCuriosityDescriptor.from_policy(
            self.effective_run.exploration,
            world_ids=self.world_roster.world_ids,
            observation_dim=obs_dim,
            action_dim=action_dim,
            training_seed=effective_training.seed,
        )
        self.exploration = build_exploration(
            policy=self.effective_run.exploration,
            descriptor=descriptor,
            device=device,
            validate_accepted_episode=self.env.validate_accepted_episode,
            issuer_factory=curiosity_issuer,
            report_allocation=lambda estimate: logger.info("Curiosity allocation estimate: %r", estimate),
            validate_committed_batch=validate_committed_batch,
            validate_parent_cadence=validate_parent_cadence,
        )

        # Get training hyperparameters from config (all required per PDR-002)
        train_frequency = loop_cfg.train_frequency
        batch_size = effective_training.replay_buffer.batch_size
        sequence_length = loop_cfg.sequence_length
        max_grad_norm = loop_cfg.max_grad_norm

        # Create agent IDs
        agent_ids = [f"agent_{i}" for i in range(num_agents)]

        base_brain_config = self.brain_config
        logger.info(f"Brain config from brain.yaml: {base_brain_config.description}")

        # Consume the canonical resolved policy, including all five brain overrides.
        effective_brain_config = self.effective_run.effective_brain
        replay_options = self.effective_run.options.replay
        assert replay_options is not None
        if "max_episodes" in self.launch_overrides:
            episode_limit_origin = f"launch_overrides.max_episodes({self.max_episodes})"
        else:
            episode_limit_origin = f"training.training_loop.max_episodes({self.max_episodes}) at {self.training_config_origin}"
        beta_horizon_origin = (
            f"{episode_limit_origin} * training.training_loop.max_steps_per_episode({loop_cfg.max_steps_per_episode}) "
            f"at {self.training_config_origin}; upper-bound vector ticks"
        )

        # Create population (effective_brain_config provides network/optimizer/Q-learning parameters)
        self.population = VectorizedPopulation.for_training(
            env=self.env,
            curriculum=self.curriculum,
            exploration=self.exploration,
            agent_ids=agent_ids,
            device=device,
            obs_dim=obs_dim,
            action_dim=action_dim,
            tb_logger=self.tb_logger,
            train_frequency=train_frequency,
            batch_size=batch_size,
            sequence_length=sequence_length,
            max_grad_norm=max_grad_norm,
            brain_config=effective_brain_config,
            max_episodes=self.max_episodes,
            max_steps_per_episode=loop_cfg.max_steps_per_episode,
            replay_options=replay_options,
            min_transitions=effective_training.replay_buffer.min_size,
            replay_rng=np.random.Generator(np.random.PCG64(effective_training.seed)),
            replay_origin="authored",
            beta_vector_tick_horizon=self.max_episodes * loop_cfg.max_steps_per_episode,
            beta_horizon_origin=beta_horizon_origin,
            current_vector_tick=0,
        )

        self.curriculum.initialize_population(num_agents)

        # Bind authentic live owners after POP has installed its ENV runtime hook.
        # BANK owns curiosity; the facade owns selection and global exploration.
        self.boundary_authority = self.env.bind_boundary_authority(
            owner=self,
            role_owners={
                "population": self.population,
                "curiosity": self.curiosity_bank,
                "curriculum": self.curriculum,
                "exploration": self.exploration,
                "network": self.population.q_network,
                "optimizer": self.population.optimizer,
                "scheduler": self.population if self.population.scheduler is None else self.population.scheduler,
                "replay": self.population.replay_buffer,
                "selection": self.exploration,
            },
        )
        self.boundary_release = None
        cuda_index = device.index
        if device.type == "cuda" and cuda_index is None:
            raise ValueError("Native runner continuation requires an indexed CUDA device")
        self.native_cuda_devices: tuple[int, ...]
        if cuda_index is None:
            self.native_cuda_devices = ()
        else:
            self.native_cuda_devices = (cuda_index,)
        self.native_rng = NativeRNGState(cuda_devices=self.native_cuda_devices)
        self._last_native_checkpoint = None

        # Initialize episode recorder if enabled
        recording_cfg = self.training_config.recording
        if recording_cfg and recording_cfg.enabled:
            from townlet.recording.recorder import EpisodeRecorder

            recording_payload = recording_cfg.model_dump(exclude_none=True)
            # Create recording output directory
            recording_output_dir = self.checkpoint_dir / (recording_cfg.output_dir or "recordings")
            recording_output_dir.mkdir(parents=True, exist_ok=True)

            self.recorder = EpisodeRecorder(
                config=recording_payload,
                output_dir=recording_output_dir,
                database=self.db,
                curriculum=self.curriculum,
            )
            logger.info(f"Episode recording enabled: {recording_output_dir}")
        else:
            logger.info("Episode recording disabled")

        # Try to resume from checkpoint
        loaded_episode = self.load_checkpoint()
        if loaded_episode is not None:
            self.current_episode = loaded_episode
        else:
            # Receiving checkpoint controllers must remain fresh-bound during
            # restore. Bootstrap only after establishing this is a fresh run.
            self.boundary_release = self.boundary_authority.bootstrap(first_batch_episode=self.current_episode)
            self.env.install_boundary_release(self.boundary_release)
            self.population.sync_exploration_metrics()
            self._capture_native_boundary()

        # Phase 4 - Log hyperparameters to TensorBoard
        self.hparams = {
            "learning_rate": effective_brain_config.optimizer.learning_rate,
            "gamma": effective_brain_config.q_learning.gamma,
            "network_architecture": base_brain_config.architecture.type,  # 'feedforward' or 'recurrent'
            "replay_buffer_capacity": effective_brain_config.replay.capacity,
            "grid_cells": grid_cells,
            "partial_observability": partial_observability,
            "vision_range": vision_range,
            "enable_temporal": enable_temporal_mechanics,
            "initial_intrinsic_weight": 1.0,
            "variance_threshold": self.training_config.intrinsic.annealing.threshold,
            "max_steps_per_episode": loop_cfg.max_steps_per_episode,
            "observation_schema_hash": level_meta.observation_schema_hash,
        }
        # Note: final metrics will be logged at end of training
        self.tb_logger.log_hyperparameters(hparams=self.hparams, metrics={})

        # Check for shutdown before starting training loop
        if self.should_shutdown:
            logger.info("[Training] Shutdown requested during initialization, exiting before training starts")
            return

        # Mark training started
        self.db.set_system_state("training_status", "running")
        self.db.set_system_state("start_time", str(time.time()))
        if self.max_environment_steps is not None:
            self.db.set_system_state("environment_step_budget_requested", str(self.max_environment_steps))
            self.db.set_system_state("environment_step_budget_stop_rule", "stop_before_vector_step")

        # Training loop
        failed = False
        training_error: BaseException | None = None
        try:
            while self.current_episode < self.max_episodes and not self.should_shutdown and not self.environment_step_budget_reached:
                if self.max_environment_steps is not None:
                    may_step, shortfall = decide_live_agent_budget(
                        completed=self.completed_live_agent_steps,
                        live_agents=self.population.num_agents,
                        budget=self.max_environment_steps,
                    )
                    if not may_step:
                        self.environment_step_budget_shortfall = shortfall
                        self.environment_step_budget_reached = True
                        break
                episode_start = time.time()

                # Generalization test at episode 5000
                if self.current_episode == 5000:
                    logger.info("=" * 60)
                    logger.info("GENERALIZATION TEST: Randomizing affordance positions")
                    logger.info("=" * 60)

                    # Store old positions
                    old_positions = self.env.get_affordance_positions()
                    logger.info(f"Old positions: {old_positions}")

                    # Randomize
                    self.env.randomize_affordance_positions()

                    # Store new positions
                    new_positions = self.env.get_affordance_positions()
                    logger.info(f"New positions: {new_positions}")

                    # Mark in database
                    import json

                    self.db.set_system_state("affordance_randomization_episode", "5000")
                    self.db.set_system_state("old_affordance_positions", json.dumps(old_positions))
                    self.db.set_system_state("new_affordance_positions", json.dumps(new_positions))

                # ENV allocates identity; POP seals genuine initial participation
                # before either consumer becomes active.
                if self.boundary_release is None or self.boundary_release.next_batch_episode != self.current_episode:
                    raise RuntimeError("Episode entry requires its installed controller boundary release")
                reservation = self.env.prepare_episode(batch_episode=self.current_episode, release=self.boundary_release)
                self.population.bind_episode_worlds(world_ids=reservation.world_ids, world_episode_seqs=reservation.world_episode_seqs)
                self.population.begin_batch_episode(self.current_episode, planned_horizon=loop_cfg.max_steps_per_episode)
                # This runner starts every declared lane; POP still publishes
                # the authenticated all-participating decision for that roster.
                reset_record, population_activation = self.population.reset(reservation=reservation, retired_world_ids=())
                curiosity_activation = self.exploration.begin_episode(accepted=reset_record.accepted)
                self.env.activate_episode(
                    accepted=reset_record.accepted,
                    population_receipt=population_activation,
                    curiosity_receipt=curiosity_activation,
                )
                self.accepted_episode = reset_record.accepted

                # Run episode
                num_agents = self.population.num_agents
                max_steps = loop_cfg.max_steps_per_episode
                episode_reward = torch.zeros(num_agents, device=self.env.device)
                episode_extrinsic_reward = torch.zeros(num_agents, device=self.env.device)
                episode_intrinsic_reward = torch.zeros(num_agents, device=self.env.device)
                episode_shaping_reward = torch.zeros(num_agents, device=self.env.device)
                episode_intrinsic_scales = torch.zeros(num_agents, device=self.env.device)
                batch_episode_steps = 0
                episode_live_agent_transitions = 0
                affordance_visits = [defaultdict(int) for _ in range(num_agents)]
                custom_action_uses = [defaultdict(int) for _ in range(num_agents)]  # Track REST, MEDITATE, etc.
                # NEW: Transition tracking
                affordance_transitions = [defaultdict(lambda: defaultdict(int)) for _ in range(num_agents)]
                last_affordance = [None for _ in range(num_agents)]
                last_agent_state: BatchedAgentState | None = None
                alive_agents = torch.ones(num_agents, dtype=torch.bool, device=self.env.device)

                for step in range(max_steps):
                    # Check for shutdown request every step for immediate response
                    if self.should_shutdown:
                        logger.info(f"[Training] Shutdown requested during episode {self.current_episode + 1}, step {step}/{max_steps}")
                        break

                    live_agent_count = int(alive_agents.sum().item())
                    if self.max_environment_steps is not None:
                        may_step, shortfall = decide_live_agent_budget(
                            completed=self.completed_live_agent_steps,
                            live_agents=live_agent_count,
                            budget=self.max_environment_steps,
                        )
                        if not may_step:
                            self.environment_step_budget_shortfall = shortfall
                            self.environment_step_budget_reached = True
                            logger.info(
                                "[Training] Environment-step budget reached at %s/%s live-agent transitions " "(conservative shortfall %s)",
                                self.completed_live_agent_steps,
                                self.max_environment_steps,
                                shortfall,
                            )
                            break

                    agent_state = self.population.step_population(self.env)
                    last_agent_state = agent_state
                    self.completed_live_agent_steps += live_agent_count
                    if self.max_environment_steps is not None and self.completed_live_agent_steps == self.max_environment_steps:
                        self.environment_step_budget_shortfall = 0
                        self.environment_step_budget_reached = True

                    if self.curriculum.transition_events:
                        self.tb_logger.log_curriculum_transitions(
                            episode=self.current_episode,
                            events=list(self.curriculum.transition_events),
                        )
                        # Log curriculum transitions to console
                        for event in self.curriculum.transition_events:
                            logger.info(
                                f"🎓 Curriculum {event['type'].upper()}: Stage {event['from_stage']} → {event['to_stage']} "
                                f"(Survival: {event['survival_rate']:.1%}, Entropy: {event['entropy']:.3f})"
                            )
                        self.curriculum.transition_events.clear()

                    # The same entry-eligible canonical row feeds summaries and recordings.
                    active_on_entry = agent_state.info["active_on_entry"]
                    components = agent_state.info["reward_components"]
                    episode_intrinsic_scales = torch.where(active_on_entry, components["runtime_intrinsic_scale"], episode_intrinsic_scales)
                    zero_reward = torch.zeros_like(agent_state.rewards)
                    episode_reward += torch.where(active_on_entry, agent_state.rewards, zero_reward)
                    episode_extrinsic_reward += torch.where(active_on_entry, components["extrinsic"], zero_reward)
                    episode_intrinsic_reward += torch.where(active_on_entry, components["intrinsic"], zero_reward)
                    episode_shaping_reward += torch.where(active_on_entry, components["shaping"], zero_reward)
                    batch_episode_steps += 1
                    episode_live_agent_transitions += int(active_on_entry.sum().item())

                    if "successful_interactions" in agent_state.info:
                        for agent_idx, affordance_name in agent_state.info["successful_interactions"].items():
                            if 0 <= agent_idx < num_agents and bool(active_on_entry[agent_idx].item()):
                                # Existing: count tracking
                                affordance_visits[agent_idx][affordance_name] += 1

                                # NEW: transition tracking
                                prev = last_affordance[agent_idx]
                                if prev is not None:
                                    # Record transition: prev → current
                                    affordance_transitions[agent_idx][prev][affordance_name] += 1

                                # Update last affordance for next transition
                                last_affordance[agent_idx] = affordance_name

                    # Track custom action uses (REST, MEDITATE, etc.)
                    for idx in range(num_agents):
                        if not bool(active_on_entry[idx].item()):
                            continue
                        action_id = int(agent_state.actions[idx].item())
                        # Custom actions start after substrate actions
                        if action_id >= self.env.action_space.substrate_action_count:
                            action = self.env.action_space.get_action_by_id(action_id)
                            custom_action_uses[idx][action.name] += 1

                    # Record step if recording enabled (only agent 0 for now)
                    if self.recorder is not None and bool(active_on_entry[0].item()):
                        # Get temporal mechanics fields if available
                        time_of_day = agent_state.info.get("time_of_day", [None] * num_agents)[0]
                        interaction_progress = agent_state.info.get("interaction_progress", [None] * num_agents)[0]

                        # Get action masks for debugging (which actions were valid)
                        action_masks = self.env.get_action_masks()[0]  # Agent 0 action masks

                        self.recorder.record_step(
                            step=step,
                            positions=self.env.positions[0],  # Agent 0 position
                            meters=self.env.meters[0],  # Agent 0 meters
                            action=(
                                agent_state.actions[0].item() if hasattr(agent_state.actions[0], "item") else int(agent_state.actions[0])
                            ),
                            reward=float(agent_state.rewards[0].item()),
                            extrinsic_reward=float(components["extrinsic"][0].item()),
                            intrinsic_reward=float(components["intrinsic"][0].item()),
                            shaping_reward=float(components["shaping"][0].item()),
                            done=bool(agent_state.dones[0].item()),
                            q_values=agent_state.info.get("q_values", [None] * num_agents)[0],
                            epsilon=float(agent_state.epsilons[0].item()),
                            action_masks=action_masks,
                            time_of_day=time_of_day,
                            interaction_progress=interaction_progress,
                        )

                    alive_agents &= ~agent_state.dones
                    if torch.all(agent_state.dones).item() or self.environment_step_budget_reached:
                        break

                if last_agent_state is None:
                    self.env.abandon_episode(accepted=self.accepted_episode, reason="empty_participation")
                    # This is quarantine, not a completed/native boundary. The
                    # native controller must preserve the last lawful snapshot.
                    break

                # Close surviving lanes before publishing for the actual external stop.
                completion_reason: RunnerCompletionReason
                if self.environment_step_budget_reached:
                    completion_reason = "budget"
                elif self.should_shutdown:
                    completion_reason = "shutdown"
                else:
                    completion_reason = "cap"
                for agent_idx in range(self.population.num_agents):
                    if not last_agent_state.dones[agent_idx]:
                        self.population.flush_episode(agent_idx=agent_idx, reason=completion_reason)

                completions = self.population.episode_completions
                if any(outcome is None for outcome in completions):
                    raise RuntimeError("Cannot publish a participated lane without its completion")
                completed_outcomes = [outcome for outcome in completions if outcome is not None]
                step_counts = torch.tensor(
                    [outcome.survival_time for outcome in completed_outcomes], dtype=torch.long, device=self.env.device
                )
                final_meters = [outcome.final_meters.detach().cpu().clone() for outcome in completed_outcomes]
                self._complete_training_episode()

                epsilon_value = self.population._get_current_epsilon_value()
                intrinsic_scales = episode_intrinsic_scales.detach().cpu()
                intrinsic_weight_value = float(intrinsic_scales[0].item())

                episode_reward_cpu = episode_reward.detach().cpu()
                episode_extrinsic_cpu = episode_extrinsic_reward.detach().cpu()
                episode_intrinsic_cpu = episode_intrinsic_reward.detach().cpu()
                episode_shaping_cpu = episode_shaping_reward.detach().cpu()
                completion = self.population.episode_completions[0]
                if completion is None:
                    raise RuntimeError("Cannot publish an episode without a slot-zero completion")
                step_counts_cpu = step_counts.detach().cpu().long()
                stages_cpu = torch.tensor([self.curriculum.get_stage_info(idx)["current_stage"] for idx in range(num_agents)])

                # Log metrics to database
                episode_timestamp = time.time()
                self.db.insert_episode(
                    episode_id=self.current_episode,
                    timestamp=episode_timestamp,
                    survival_time=completion.survival_time,
                    batch_episode_steps=batch_episode_steps,
                    live_agent_transitions=episode_live_agent_transitions,
                    completion_reason=completion.reason,
                    total_reward=float(episode_reward_cpu[0].item()),
                    extrinsic_reward=float(episode_extrinsic_cpu[0].item()),
                    intrinsic_reward=float(episode_intrinsic_cpu[0].item()),
                    shaping_reward=float(episode_shaping_cpu[0].item()),
                    intrinsic_weight=intrinsic_weight_value,
                    curriculum_stage=int(stages_cpu[0].item()),
                    epsilon=epsilon_value,
                    observation_schema_hash=level_meta.observation_schema_hash,
                )

                # NEW: Insert affordance transitions for agent 0
                if affordance_transitions[0]:
                    # Convert nested defaultdict to regular dict for database insertion
                    transitions_dict = {from_aff: dict(to_affs) for from_aff, to_affs in affordance_transitions[0].items()}
                    self.db.insert_affordance_visits(episode_id=self.current_episode, transitions=transitions_dict)

                # Finish episode recording if enabled
                if self.recorder is not None:
                    from townlet.recording.data_structures import EpisodeMetadata

                    metadata = EpisodeMetadata(
                        episode_id=self.current_episode,
                        survival_steps=completion.survival_time,
                        completion_reason=completion.reason,
                        total_reward=float(episode_reward_cpu[0].item()),
                        extrinsic_reward=float(episode_extrinsic_cpu[0].item()),
                        intrinsic_reward=float(episode_intrinsic_cpu[0].item()),
                        shaping_reward=float(episode_shaping_cpu[0].item()),
                        curriculum_stage=int(stages_cpu[0].item()),
                        epsilon=epsilon_value,
                        intrinsic_weight=intrinsic_weight_value,
                        timestamp=episode_timestamp,
                        affordance_layout={
                            name: tuple(position) for name, position in self.env.get_affordance_positions()["positions"].items()
                        },
                        affordance_visits={k: v for k, v in affordance_visits[0].items()},  # Agent 0 visits
                        custom_action_uses={k: v for k, v in custom_action_uses[0].items()},  # Agent 0 custom actions
                    )
                    self.recorder.finish_episode(metadata)

                agent_metrics = []
                for idx, agent_id in enumerate(self.population.agent_ids):
                    agent_completion = self.population.episode_completions[idx]
                    if agent_completion is None:
                        raise RuntimeError("Cannot publish a participated lane without its completion")
                    agent_metrics.append(
                        {
                            "agent_id": agent_id,
                            "survival_time": agent_completion.survival_time,
                            "completion_reason": agent_completion.reason,
                            "total_reward": float(episode_reward_cpu[idx].item()),
                            "extrinsic_reward": float(episode_extrinsic_cpu[idx].item()),
                            "intrinsic_reward": float(episode_intrinsic_cpu[idx].item()),
                            "shaping_reward": float(episode_shaping_cpu[idx].item()),
                            "curriculum_stage": int(stages_cpu[idx].item()),
                            "epsilon": epsilon_value,
                            "intrinsic_weight": float(intrinsic_scales[idx].item()),
                        }
                    )

                # Log to TensorBoard (Phase 1 - Episode metrics)
                self.tb_logger.log_multi_agent_episode(
                    episode=self.current_episode,
                    agents=agent_metrics,
                )
                self.tb_logger.writer.add_scalar("Batch/Vector_Ticks", batch_episode_steps, self.current_episode)
                self.tb_logger.writer.add_scalar("Batch/Live_Agent_Transitions", episode_live_agent_transitions, self.current_episode)

                # Phase 2 - Training metrics (if training occurred this episode)
                training_metrics = self.population.get_training_metrics()
                if training_metrics["training_step"] > 0:
                    self.tb_logger.log_training_step(
                        step=training_metrics["training_step"],
                        td_error=training_metrics["td_error"],
                        loss=training_metrics["loss"],
                    )

                # Phase 3 - Meter dynamics and affordance usage
                # Get actual meter names from config (supports variable meter counts)
                meter_names = self.env.bars_config.meter_names
                for idx, agent_id in enumerate(self.population.agent_ids):
                    meters_tensor = final_meters[idx]
                    if meters_tensor is not None:
                        meter_dict = {name: meters_tensor[i].item() for i, name in enumerate(meter_names)}
                        self.tb_logger.log_meters(
                            episode=self.current_episode,
                            step=int(step_counts_cpu[idx].item()),
                            meters=meter_dict,
                            agent_id=agent_id,
                        )

                for idx, visits in enumerate(affordance_visits):
                    if visits:
                        self.tb_logger.log_affordance_usage(
                            episode=self.current_episode,
                            affordance_counts=dict(visits),
                            agent_id=self.population.agent_ids[idx],
                        )

                for idx, uses in enumerate(custom_action_uses):
                    if uses:
                        self.tb_logger.log_custom_action_usage(
                            episode=self.current_episode,
                            action_counts=dict(uses),
                            agent_id=self.population.agent_ids[idx],
                        )

                # Heartbeat log every HEARTBEAT_INTERVAL episodes
                if self.current_episode % self.HEARTBEAT_INTERVAL == 0:
                    elapsed = time.time() - episode_start
                    stage_overview = "/".join(str(int(s.item())) for s in stages_cpu)

                    # Calculate reward breakdown
                    total_reward = episode_reward_cpu[0].item()
                    extrinsic_reward = episode_extrinsic_cpu[0].item()
                    intrinsic_reward = episode_intrinsic_cpu[0].item()
                    shaping_reward = episode_shaping_cpu[0].item()

                    logger.info(
                        f"Episode {self.current_episode}/{self.max_episodes} | "
                        f"Survival: {int(step_counts_cpu[0].item())} steps | "
                        f"Reward: {total_reward:.2f} (Extrinsic: {extrinsic_reward:.2f}, "
                        f"Intrinsic: {intrinsic_reward:.2f}, Shaping: {shaping_reward:.2f}) | "
                        f"ε: {epsilon_value:.3f} | "
                        f"Stage: {stage_overview} | "
                        f"Time: {elapsed:.2f}s"
                    )

                # Detailed summary every SUMMARY_INTERVAL episodes
                if self.current_episode % self.SUMMARY_INTERVAL == 0:
                    # Get training metrics
                    training_metrics = self.population.get_training_metrics()

                    # Get final meters for agent 0
                    final_meter_values = {}
                    if final_meters[0] is not None:
                        # Get actual meter names from config (supports variable meter counts)
                        meter_names = self.env.bars_config.meter_names
                        final_meter_values = {name: final_meters[0][i].item() for i, name in enumerate(meter_names)}

                    # Get affordance usage for agent 0 with tick counts and completed interactions
                    if affordance_visits[0]:
                        summary_parts = []
                        for name, tick_count in affordance_visits[0].items():
                            # Get duration_ticks to calculate completed interactions
                            duration = self.env.affordance_engine.get_duration_ticks(name)
                            completed = tick_count // duration
                            summary_parts.append(f"{name}: {tick_count} ({completed})")
                        affordance_summary = ", ".join(summary_parts)
                    else:
                        affordance_summary = "None"

                    logger.info("=" * 80)
                    logger.info(f"📊 SUMMARY - Episode {self.current_episode}/{self.max_episodes}")
                    logger.info("-" * 80)
                    logger.info(f"Performance:    Survival: {int(step_counts_cpu[0].item())} steps | Stage: {stage_overview}")
                    logger.info(
                        f"Rewards:        Total: {total_reward:.2f} | "
                        f"Extrinsic: {extrinsic_reward:.2f} | Intrinsic: {intrinsic_reward:.2f} | Shaping: {shaping_reward:.2f}"
                    )
                    # Check if annealing would trigger (for status display)
                    annealing_active = self.exploration.should_anneal() if hasattr(self.exploration, "should_anneal") else False
                    annealing_status = "🔻 ANNEALING" if annealing_active else "✓ exploring"
                    logger.info(
                        f"Exploration:    ε: {epsilon_value:.3f} | Intrinsic Weight: {intrinsic_weight_value:.3f} | {annealing_status}"
                    )
                    if training_metrics["training_step"] > 0:
                        logger.info(
                            f"Training:       Steps: {training_metrics['training_step']} | "
                            f"Loss: {training_metrics['loss']:.4f} | TD Error: {training_metrics['td_error']:.4f}"
                        )
                    if final_meter_values:
                        # Build dynamic meter summary (supports variable meter counts)
                        meter_parts = [f"{name.capitalize()}: {value:.2f}" for name, value in final_meter_values.items()]
                        meter_summary = " | ".join(meter_parts)
                        logger.info(f"Final Meters:   {meter_summary}")
                    logger.info(f"Affordances:    {affordance_summary}")

                    # Log custom action usage (REST, MEDITATE, etc.)
                    if custom_action_uses[0]:
                        custom_summary_parts = [f"{name}: {count}" for name, count in custom_action_uses[0].items()]
                        custom_summary = ", ".join(custom_summary_parts)
                        logger.info(f"Custom Actions: {custom_summary}")

                    # Log total interaction ticks for debugging
                    total_interaction_ticks = sum(affordance_visits[0].values()) if affordance_visits[0] else 0
                    total_custom_actions = sum(custom_action_uses[0].values()) if custom_action_uses[0] else 0
                    total_interactions = total_interaction_ticks + total_custom_actions
                    logger.info(
                        f"Interactions:   {total_interaction_ticks} affordance ticks + {total_custom_actions} custom actions = "
                        f"{total_interactions}/{int(step_counts_cpu[0].item())} steps "
                        f"({100 * total_interactions / max(1, int(step_counts_cpu[0].item())):.1f}%)"
                    )
                    logger.info("=" * 80)

                # Honor the resolved, authored checkpoint cadence.
                if self.population.clock_ledger.completed_batch_episodes % loop_cfg.checkpointing.interval == 0:
                    self.save_checkpoint()

                self.current_episode += 1

        except BaseException as error:
            failed = True
            training_error = error
            raise
        finally:
            if self.max_environment_steps is not None:
                shortfall = self.max_environment_steps - self.completed_live_agent_steps
                if shortfall < 0:
                    raise RuntimeError(
                        f"environment-step budget overshot: {self.completed_live_agent_steps} > {self.max_environment_steps}"
                    )
                self.environment_step_budget_shortfall = shortfall
                self.db.set_system_state("environment_step_budget_realized", str(self.completed_live_agent_steps))
                self.db.set_system_state("environment_step_budget_shortfall", str(shortfall))

            # Save final checkpoint
            logger.info("Training complete, saving final checkpoint...")
            try:
                self.save_checkpoint()
            except Exception as checkpoint_error:
                if training_error is None:
                    raise
                training_error.add_note(f"Final checkpoint also failed: {checkpoint_error!r}")
                logger.exception("Final checkpoint failed while preserving the original training error")

            # Phase 4 - Log final metrics with hyperparameters
            if self.population is not None:
                final_metrics = {
                    "final_episode": self.current_episode,
                    "total_training_steps": self.population.total_steps,
                }
                # Re-log hyperparameters with final metrics for comparison
                if hasattr(self, "hparams"):
                    self.tb_logger.log_hyperparameters(hparams=self.hparams, metrics=final_metrics)

            self.db.set_system_state(
                "training_status",
                resolve_training_status(
                    failed=failed,
                    should_shutdown=self.should_shutdown,
                    budget_reached=self.environment_step_budget_reached,
                    episodes_reached=self.current_episode >= self.max_episodes,
                ),
            )

            # Use extracted cleanup method
            self._cleanup()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit("townlet.demo.runner is no longer a direct CLI entry point.\nUse scripts/run_demo.py for the unified demo server.")
