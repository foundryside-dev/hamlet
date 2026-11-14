"""
Vectorized Hamlet environment for GPU-native training.

Batches multiple independent Hamlet environments into a single vectorized
environment with tensor operations [num_agents, ...].
"""

from __future__ import annotations

import math
import os
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from numbers import Number, Real
from pathlib import Path
from threading import Thread, current_thread
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast
from weakref import ReferenceType, WeakKeyDictionary, WeakSet, WeakValueDictionary, ref

import torch

from townlet.config.exploration_policy import ExplorationRuntime, IntrinsicStepHandoff, IntrinsicTransitionContext
from townlet.config.world_roster import (
    WorldAcceptedEpisode,
    WorldEpisodeReservation,
    WorldOwnerReceipt,
    WorldRecord,
    WorldRosterDeclaration,
    canonical_hash,
    exact_integer,
    exact_world_ids,
    frozen_value,
    owned_value,
    same_value,
    validate_world_snapshot,
    world_binding,
)
from townlet.environment import env_factory
from townlet.environment.action_builder import ComposedActionSpace
from townlet.environment.action_config import ActionConfig
from townlet.environment.action_executor import ActionExecutor
from townlet.environment.action_labels import ActionLabels
from townlet.environment.action_mask_builder import ActionMaskBuilder
from townlet.environment.affordance_engine import AffordanceEngine
from townlet.environment.dac_engine import DACEngine
from townlet.environment.manual_physical import ManualPhysicalSession, ManualPhysicalStepResult
from townlet.environment.observation_encoder import build_token_observation_encoder
from townlet.environment.parent_custody import EnvCustody, EnvParentCustody, env_guard
from townlet.environment.reward_calculator import RewardCalculator
from townlet.environment.token_publishers import (
    EffectSlotBatch,
    ItemSlotBatch,
    TokenCapacityError,
    TokenPublishContext,
)
from townlet.items import InventoryState, ItemActionHandler, ItemManager
from townlet.universe.dto import RuntimeActionSpace
from townlet.universe.dto.token_spec import item_capacity
from townlet.vfs.evaluator import VFSEvaluator
from townlet.vfs.namespace import CommandSymbols, Namespace, expression_sources
from townlet.vfs.profiles import CompiledGlobalProfile
from townlet.vfs.random_draws import DrawInstant, VFSRandomness, VFSWorldContext
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.transition_schedule import VTCTransitionContext, VTCTransitionRunner, VTCTransitionState
from townlet.vfs.vtc import (
    VTCActionWriteProgram,
    VTCAffordanceGateProgram,
    VTCInteractionProgressProgram,
    VTCModulationProgram,
    VTCPassiveDepletionProgram,
    VTCRewardProgram,
    VTCTerminalConditionProgram,
    VTCThresholdCascadeProgram,
)

if TYPE_CHECKING:
    from townlet.exploration.world_curiosity_state import CuriosityStepStamp
    from townlet.population.runtime_registry import AgentRuntimeRegistry
    from townlet.training.clock_ledger import PreparedVectorStep
    from townlet.universe.compiled import CompiledUniverse
    from townlet.vfs.schema import VariableDef


# Import consolidated NullItemManager (ENV-009)
from townlet.environment.null_managers import NullItemManager

_WORLD_ROLES = {"population", "curiosity", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection"}
_EFFECT_ROLES = {
    "curriculum_receipt": "curriculum",
    "exploration_receipt": "exploration",
    "population_commit_receipt": "population",
    "epsilon_install_receipt": "exploration",
    "selection_sync_receipt": "selection",
}


class PreparedNativeLayout:
    """Opaque ENV-issued data preparation; publication needs the real finalizer."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("native layouts are issued by their receiving ENV")

    def __copy__(self):
        raise TypeError("native layout handles cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("native layout handles cannot be copied")

    def __reduce__(self):
        raise TypeError("native layout handles cannot be serialized")


@dataclass(frozen=True, slots=True)
class _NativeLayoutData:
    parent: ReferenceType[Any]
    pid: int
    thread: Thread
    revision: int
    next_revision: int
    positions: dict[str, torch.Tensor]
    assignments: tuple[tuple[str, torch.Tensor], ...]


class WorldReceiptIssuer:
    """Cooperative owner custody; copied or duck-typed evidence is never issued."""

    def __init__(self, *, owner: object):
        self._owner = owner
        self._issued: WeakValueDictionary[int, WorldOwnerReceipt] = WeakValueDictionary()

    @property
    def owner(self) -> object:
        return self._owner

    def issue(self, *, kind: str, payload: Mapping[str, Any]) -> WorldOwnerReceipt:
        if not isinstance(kind, str) or not kind or not isinstance(payload, Mapping):
            raise ValueError("owner receipts require a kind and owned field mapping")
        receipt = WorldOwnerReceipt(kind, self.owner, 0, frozen_value(payload), self)
        self._issued[id(receipt)] = receipt
        return receipt

    @staticmethod
    def validate(receipt: Any, kind: str, owner: object) -> WorldOwnerReceipt:
        if not isinstance(receipt, WorldOwnerReceipt) or not isinstance(receipt._issuer, WorldReceiptIssuer):
            raise ValueError("committed evidence requires an issued owner receipt")
        issuer = receipt._issuer
        if issuer._issued.get(id(receipt)) is not receipt or receipt.kind != kind or receipt.owner is not owner:
            raise ValueError("wrong receipt kind, issuer or copied evidence")
        return receipt


class WorldBoundaryAuthority:
    """T26's bound release capability; saving is never a release side effect."""

    def __init__(self, env: VectorizedHamletEnv, owner: object):
        self._env, self._owner = env, owner

    def _bound_env(self) -> VectorizedHamletEnv:
        if self._env._world_authority is not self:
            raise ValueError("boundary capability was not bound by this ENV")
        self._env._participation_ingress()
        self._env._check_committed_participation()
        return self._env

    @env_guard
    def bootstrap(self, *, first_batch_episode: int) -> WorldRecord:
        env = self._bound_env()
        exact_integer(first_batch_episode, 0, "first batch")
        env._require_phase("fresh-bound", "bootstrap-ready")
        if env._world_bootstrap is not None:
            if env._world_bootstrap.next_batch_episode != first_batch_episode:
                raise ValueError("bootstrap batch cannot change")
            return env._world_bootstrap
        env._world_bootstrap = env._record("release", {"release_kind": "bootstrap", "next_batch_episode": first_batch_episode})
        return env._world_bootstrap

    @env_guard
    def completed(self, *, closure: WorldRecord, effects: WorldOwnerReceipt) -> WorldRecord:
        env = self._bound_env()
        env._require_phase("closed-awaiting-release", "released-completed")
        env._valid_record(closure, "closure")
        if closure is not env._world_closure:
            raise ValueError("release must name the current closure")
        proof = WorldReceiptIssuer.validate(effects, "boundary_effects", self._owner)
        fields = proof.payload
        required = {
            "batch_episode",
            "accepted_identity",
            "completion_content",
            "retirement_receipt",
            "curriculum_receipt",
            "exploration_receipt",
            "population_commit_receipt",
            "epsilon_install_receipt",
            "selection_sync_receipt",
        }
        if set(fields) != required or fields["accepted_identity"] is not env._world_accepted:
            raise ValueError("effects require the exact accepted boundary")
        exact_integer(fields["batch_episode"], 0, "effects batch")
        if fields["batch_episode"] != closure.boundary_key or not same_value(fields["completion_content"], closure.completion_content):
            raise ValueError("effects disagree with closure content")
        if fields["retirement_receipt"] is not closure.dispositions:
            raise ValueError("retirement evidence disagrees")
        for name in required - {"batch_episode", "accepted_identity", "completion_content", "retirement_receipt"}:
            child = fields[name]
            WorldReceiptIssuer.validate(child, name, env._world_role_owners[_EFFECT_ROLES[name]])
            if set(child.payload) != {"accepted", "boundary_key", "completion_content"}:
                raise ValueError("effect receipt requires exact correlation fields")
            exact_integer(child.boundary_key, 0, "effect boundary")
            if (
                child.accepted is not env._world_accepted
                or child.boundary_key != closure.boundary_key
                or not same_value(child.completion_content, closure.completion_content)
            ):
                raise ValueError("effect receipt belongs to another boundary")
        return env._equal_record(
            "completed_release",
            "release",
            {
                "release_kind": "completed",
                "next_batch_episode": closure.boundary_key + 1,
                "closure": closure,
                "effects": effects,
            },
        )

    @env_guard
    def prepare_initial_snapshot(self, *, release: WorldRecord, owners: WorldOwnerReceipt) -> WorldRecord:
        env = self._bound_env()
        env._require_phase("bootstrap-ready")
        env._require_release(release)
        proof = WorldReceiptIssuer.validate(owners, "initial_owners", self._owner)
        exact_integer(proof.bootstrap_first_batch, 0, "initial bootstrap batch")
        fields = proof.payload
        names = {"population", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection"}
        if set(fields) != names | {"semantic_execution_identity", "bootstrap_first_batch", "world_binding"}:
            raise ValueError("initial preparation requires every current owner")
        if (
            proof.semantic_execution_identity != env.semantic_execution_identity
            or proof.bootstrap_first_batch != release.next_batch_episode
            or tuple(proof.world_binding) != env.world_ids
        ):
            raise ValueError("initial owner identity disagrees")
        for name in names:
            child = fields[name]
            WorldReceiptIssuer.validate(child, "initial_owner", env._world_role_owners[name])
            if set(child.payload) != {"role", "state", "semantic_execution_identity", "bootstrap_first_batch", "world_binding"}:
                raise ValueError("initial owner must provide its prepared current state")
            if (
                child.role != name
                or child.semantic_execution_identity != env.semantic_execution_identity
                or type(child.bootstrap_first_batch) is not int
                or child.bootstrap_first_batch != release.next_batch_episode
                or tuple(child.world_binding) != env.world_ids
            ):
                raise ValueError("initial owner role or correlation disagrees")
        return env._record("initial_snapshot", {"release": release, "owners": owners})

    @env_guard
    def restored(self, *, restore: WorldRecord, boundary: WorldOwnerReceipt) -> WorldRecord:
        from townlet.environment.restore_attempt import consume_restore_route

        env = self._bound_env()
        consume_restore_route(env=env, prepared=restore, route="release")
        env._require_phase("fresh-bound")
        env._valid_record(restore, "prepared_restore")
        proof = WorldReceiptIssuer.validate(boundary, "restored_boundary", self._owner)
        if set(proof.payload) != {"kind", "state", "prepared"} or proof.prepared is not restore:
            raise ValueError("restore requires matching joint prepared evidence")
        if proof.payload["kind"] != restore.state["kind"] or not same_value(proof.state, restore.state):
            raise ValueError("joint restore evidence disagrees")
        return env._record(
            "release", {"release_kind": "restored", "next_batch_episode": restore.state["next_batch_episode"], "restore": restore}
        )

    def restore_bank_attempt(
        self, *, prepared: WorldRecord, bank: Any, validate_parent_restore: Callable[..., Any], finalize_component: Callable[..., Any]
    ) -> AbstractContextManager[Any]:
        from townlet.environment.restore_attempt import restore_attempt

        if self._env._world_restore_terminal:
            raise ValueError("receiver is terminal after failed restore composition")
        return restore_attempt(
            authority=self,
            prepared=prepared,
            child=bank,
            profile="bank",
            validate_parent_restore=validate_parent_restore,
            finalize_component=finalize_component,
        )

    def restore_runtime_attempt(
        self, *, prepared: WorldRecord, runtime: Any, validate_parent_restore: Callable[..., Any], finalize_component: Callable[..., Any]
    ) -> AbstractContextManager[Any]:
        from townlet.environment.restore_attempt import restore_attempt

        if self._env._world_restore_terminal:
            raise ValueError("receiver is terminal after failed restore composition")
        return restore_attempt(
            authority=self,
            prepared=prepared,
            child=runtime,
            profile="runtime",
            validate_parent_restore=validate_parent_restore,
            finalize_component=finalize_component,
        )


class VectorizedHamletEnv:
    """
    GPU-native vectorized Hamlet environment.

    Batches multiple independent environments for parallel execution.
    All state is stored as PyTorch tensors on specified device.
    """

    EFFECT_OBS_SLOTS = 8  # Fixed number of observable effect slots per agent

    runtime_registry: AgentRuntimeRegistry | None
    positions: torch.Tensor
    _velocity: torch.Tensor
    meters: torch.Tensor
    dones: torch.Tensor
    step_counts: torch.Tensor
    intrinsic_weights: torch.Tensor
    _movement_deltas: torch.Tensor
    meter_bounds_min: torch.Tensor
    meter_bounds_max: torch.Tensor
    interaction_progress: torch.Tensor
    last_interaction_position: torch.Tensor
    time_of_day: int
    vtc_reward_program: VTCRewardProgram
    action_space: ComposedActionSpace
    action_ids: dict[str, int]
    affordances: dict[str, torch.Tensor]
    affordance_engine: AffordanceEngine

    def __init__(
        self,
        *,
        universe: CompiledUniverse,
        level_name: str,
        num_agents: int,
        device: torch.device | str,
        world_roster: WorldRosterDeclaration,
        training_seed: int,
        lane_world_ids: tuple[str, ...],
    ):
        """
        Initialize vectorized environment.

        Args:
            universe: CompiledUniverse artifact produced by UniverseCompiler (v2.1 hierarchical configs)
            level_name: Which curriculum level to instantiate (e.g., "L0_0_minimal")
            num_agents: Number of parallel agents to simulate
            device: PyTorch device or device string (must be provided explicitly)

        Note (PDR-002 Compliance):
            - device retains an infrastructure default (exempted from no-defaults principle)
            - Behavioral parameters (grid size, observability, energy costs, affordance selection)
              now flow exclusively from the compiled universe
        """
        self._env_custody = EnvCustody(self)
        self._initialize_world_identity(world_roster, training_seed, lane_world_ids, num_agents, universe.execution_hash)
        if device is None:
            raise ValueError("VectorizedHamletEnv requires an explicit device; cannot default to CPU/GPU.")
        torch_device = torch.device(device) if isinstance(device, str) else device

        level = universe.get_level(level_name)
        self.level_name = level_name
        self.level = level
        self.universe = universe
        self.config_pack_path = Path(universe.experiment_dir or ".")
        self.num_agents = num_agents
        self.device = torch_device
        self._action_executor = ActionExecutor(self)
        self._reward_calculator = RewardCalculator(self)
        self.optimization_data = level.optimization_data
        self.metadata = self.universe.metadata_for_level(level_name)

        # Training/runtime controls: derive from level.training
        training_cfg = level.training
        # population_cfg is currently unused but retained for future runtime wiring
        population_cfg = training_cfg.population  # noqa: F841
        # v2.1: runtime environment knobs live on TrainingV2Config
        self.randomize_affordances = training_cfg.randomize_affordances
        self.partial_observability = level.curriculum.curriculum.active_vision != "global"
        # Curriculum vision_range is normalized [0, 1]; radius/window derive from grid size.
        self.vision_range = level.curriculum.curriculum.vision_range
        if training_cfg.enabled_affordances is None:
            raise ValueError("training.enabled_affordances must be an explicit list (empty to deploy none); null is not allowed.")
        self.enabled_affordances = list(training_cfg.enabled_affordances)
        self.temporal_support_enabled = self.universe.stratum.stratum.temporal_support == "enabled"
        self.temporal_active = level.curriculum.curriculum.active_temporal
        # Temporal mechanics (day/night cycle) are only active when support is enabled
        # and the curriculum marks temporal as active.
        self.enable_temporal_mechanics = self.temporal_support_enabled and self.temporal_active
        # Curriculum day_length controls temporal encoding when mechanics are enabled.
        # When temporal mechanics are active, day_length must be explicitly specified.
        if self.enable_temporal_mechanics:
            if level.curriculum.curriculum.day_length is None:
                raise ValueError(
                    "curriculum.day_length is required when active_temporal=true and "
                    "stratum.temporal_support='enabled'. No defaults allowed."
                )
            self.day_length = level.curriculum.curriculum.day_length
        else:
            # Temporal inactive: allow day_length to be null; use metadata ticks_per_day (may be 0) when absent.
            inactive_day_length = level.curriculum.curriculum.day_length
            if inactive_day_length is None:
                self.day_length = getattr(self.metadata, "ticks_per_day", 0) or 0
            else:
                self.day_length = inactive_day_length
        self.agent_lifespan = training_cfg.training_loop.max_steps_per_episode

        from townlet.substrate.factory import SubstrateFactory

        self.substrate = SubstrateFactory.build(self.universe.stratum.stratum.substrate, device=torch_device)

        # Action labels are provided by the compiler via ActionSpaceMetadata.
        level_action_metadata = level.action_metadata
        compiled_labels = getattr(level_action_metadata, "labels", {}) or {}
        if not compiled_labels:
            raise ValueError("Compiled action labels missing; recompile configs to generate ActionSpaceMetadata.labels.")

        # Rehydrate into ActionLabels for downstream helpers
        self.action_labels = ActionLabels(
            labels=dict(compiled_labels),
            description=getattr(level_action_metadata, "label_description", ""),
            domain=getattr(level_action_metadata, "label_domain", ""),
        )

        # Metadata and observation activity
        # Experiment-level label for batching/logging, derived from experiment.yaml.
        # experiment_name is mandatory in v2.1; treat missing or empty values as a configuration error.
        experiment_root = self.universe.experiment.experiment
        experiment_label = getattr(experiment_root, "experiment_name", None)
        if not experiment_label:
            raise ValueError(
                "Missing mandatory experiment_name in experiment.yaml. "
                "Set experiment.experiment_name in your v2.1 experiment config and recompile."
            )
        self.experiment_batch_label = experiment_label
        # The compiled token artifact IS the observation ABI (unit-3 Task-10 cut).
        # Layout is stable across curriculum levels, while level-authored meter and
        # affordance parameters can change compiled static identity. The encoder must
        # therefore consume this selected level's spec, never the primary-level alias.
        self.token_spec = level.token_spec

        # Observation/model metadata
        self.meter_count = self.metadata.meter_count
        meter_count = self.meter_count

        # Serialization width of the compiled token observation.
        self.observation_dim = self.token_spec.total_dims

        # Phases below are private helpers that mutate self in a fixed order
        # (hamlet-2559b98232). __init__ reads as orchestration; each phase is
        # individually grokable.
        self._initialize_vfs_subsystem()
        self._initialize_dac_engine()

        # EFFECTS INTEGRATION: Use compiled effect catalog from UniverseCompiler
        from townlet.effects.executor import CommandExecutor
        from townlet.effects.manager import EffectManager

        # Use compiled catalog from CompiledUniverse (Task 4.1)
        effect_catalog = universe.compiled_effect_catalog
        # Note: Minimal configs without affordances have None catalog (expected behavior)
        # If affordances exist but catalog missing, compilation would have failed

        self.command_executor = CommandExecutor()
        self.effect_manager = (
            EffectManager(
                catalog=effect_catalog,
                command_executor=self.command_executor,
                device=str(self.device),
                time_enabled=self.temporal_support_enabled,
            )
            if effect_catalog is not None
            else None
        )

        # Bars configuration (per-level)
        self.bars_config = level.bars

        # Precompute meter initialization tensor from bars config
        self.initial_meter_values = torch.zeros(meter_count, dtype=torch.float32, device=self.device)
        for bar in self.bars_config.meters:
            idx = self.meter_name_to_index.get(bar.name)
            if idx is not None:
                self.initial_meter_values[idx] = bar.initial

        # Declared meter bounds drive every runtime ceiling and floor (WS-1(e)).
        # Two vectorized [meter_count] tensors, never a branch on a bar name: the
        # runtime stays domain-agnostic and `money` is not special-cased anywhere.
        self.meter_bounds_min = torch.zeros(meter_count, dtype=torch.float32, device=self.device)
        self.meter_bounds_max = torch.zeros(meter_count, dtype=torch.float32, device=self.device)
        covered_indices: set[int] = set()
        for bar in self.bars_config.meters:
            idx = self.meter_name_to_index.get(bar.name)
            if idx is None:
                continue
            self.meter_bounds_min[idx] = bar.bounds.min
            self.meter_bounds_max[idx] = bar.bounds.max
            covered_indices.add(idx)
        uncovered = sorted(set(range(meter_count)) - covered_indices)
        if uncovered:
            index_to_name = {idx: name for name, idx in self.meter_name_to_index.items()}
            uncovered_names = [index_to_name.get(idx, f"<index {idx}>") for idx in uncovered]
            raise ValueError(
                "Meter indices in the compiled metadata have no declared bar to supply bounds.\n"
                f"  Uncovered meters: {uncovered_names}\n"
                "  Rule: every meter must declare bounds.min/bounds.max in bars.yaml; there is no default."
            )

        # Initialize affordance engine with AffordanceParamConfig directly
        # No RuntimeAffordanceConfig conversion needed - AffordanceEngine uses interactions field

        affordances_list = level.affordances.affordances

        # Extract positions directly from AffordanceParamConfig
        def _extract_position(aff):
            """Extract first fixed position from deployment config."""
            if aff.deployment.type == "fixed" and aff.deployment.positions:
                return aff.deployment.positions[0]
            return None

        # Affordance vocabulary and positions from compiled metadata
        self.affordance_name_to_id = {aff.name: aff.name for aff in affordances_list}
        self.affordance_positions_from_config = {aff.name: _extract_position(aff) for aff in affordances_list}
        optimization_position_map = getattr(self.optimization_data, "affordance_position_map", {})
        self.affordance_positions_from_optimization = {
            name: optimization_position_map.get(aff_id) for name, aff_id in self.affordance_name_to_id.items()
        }

        all_affordance_names = [aff.name for aff in affordances_list]
        affordance_names_to_deploy = env_factory._resolve_deployable_affordances(
            all_affordance_names,
            training_cfg.enabled_affordances,
            self.affordance_name_to_id,
        )

        default_position = torch.zeros(self.substrate.position_dim, dtype=self.substrate.position_dtype, device=self.device)
        self.affordances = {name: default_position.clone() for name in affordance_names_to_deploy}
        self.affordance_names = all_affordance_names
        self.num_affordance_types = len(all_affordance_names)

        # Build composed action space from compiler-emitted runtime artifact
        self.action_space = self._build_action_space_from_runtime_artifact(level.runtime_action_space)
        self.action_dim = self.action_space.action_dim
        self.action_ids = level.runtime_action_space.action_ids
        self._movement_deltas = self._build_movement_deltas()
        self.vtc_transition_schedule = level.transition_schedule
        self.vtc_transition_runner = VTCTransitionRunner(self.vtc_transition_schedule)
        self.vtc_action_write_program: VTCActionWriteProgram = self.vtc_transition_schedule.action_write_program
        self.vtc_affordance_gate_program: VTCAffordanceGateProgram = self.vtc_transition_schedule.affordance_gate_program
        self.vtc_interaction_progress_program: VTCInteractionProgressProgram = self.vtc_transition_schedule.interaction_progress_program
        self.vtc_terminal_condition_program: VTCTerminalConditionProgram = self.vtc_transition_schedule.terminal_condition_program
        self.vtc_passive_depletion_program: VTCPassiveDepletionProgram = self.vtc_transition_schedule.passive_depletion_program
        self.vtc_modulation_program: VTCModulationProgram = self.vtc_transition_schedule.modulation_program
        self.vtc_threshold_cascade_program: VTCThresholdCascadeProgram = self.vtc_transition_schedule.threshold_cascade_program
        self.vtc_reward_program = VTCRewardProgram()

        # Per-tick action-mask computation extracted from this class. The
        # builder is stateless; per-tick state is passed at call time.
        self.action_mask_builder = ActionMaskBuilder(
            action_space=self.action_space,
            device=self.device,
            substrate=self.substrate,
            movement_deltas=self._movement_deltas,
            action_ids=self.action_ids,
            enable_temporal_mechanics=self.enable_temporal_mechanics,
        )

        # State tensors (initialized in reset)
        self.positions = torch.zeros(
            (self.num_agents, self.substrate.position_dim),
            dtype=self.substrate.position_dtype,
            device=self.device,
        )
        # Velocity (delta position per step) in float coordinates
        self._velocity = torch.zeros(
            (self.num_agents, self.substrate.position_dim),
            dtype=torch.float32,
            device=self.device,
        )
        self.meters = torch.zeros((self.num_agents, meter_count), dtype=torch.float32, device=self.device)
        self.dones = torch.zeros(self.num_agents, dtype=torch.bool, device=self.device)
        self.step_counts = torch.zeros(self.num_agents, dtype=torch.long, device=self.device)
        self.global_tick: int = 0  # HIGH-01: Track global time independently of agent 0
        self.intrinsic_weights = torch.ones(self.num_agents, dtype=torch.float32, device=self.device)  # Default: 1.0 (full exploration)
        self._last_reward_components: dict[str, torch.Tensor] = {}

        # Items + affordance engine wiring (depends on meters, vfs_registry,
        # effect_manager, command_executor — all set above).
        self._initialize_item_subsystem(num_agents)
        self._initialize_affordance_engine(num_agents)

        # Required current runtime and parent claim are bound before stepping.
        self._exploration_bound = False
        self._manual_session: ManualPhysicalSession | None = None
        self._manual_close_prepared: WorldRecord | None = None
        self._exploration_runtime: ExplorationRuntime
        self._claim_vector_step: Callable[..., int]

        # Temporal mechanics state
        self.interaction_progress = torch.zeros(self.num_agents, dtype=torch.long, device=self.device)
        self.last_interaction_affordance: list[str | None] = [None] * self.num_agents
        self.last_interaction_position = torch.zeros(
            (self.num_agents, self.substrate.position_dim),
            dtype=self.substrate.position_dtype,
            device=self.device,
        )
        self.time_of_day = 0

        if not self.enable_temporal_mechanics:
            # When temporal mechanics are disabled, interaction progress is unused but kept for typing consistency.
            self.interaction_progress.zero_()

        # Affordance history tracking (for DAC shaping bonuses)
        # Track last affordance interacted with per agent
        self._last_affordances: list[str | None] = [None] * self.num_agents
        # Track consecutive interactions with each affordance (per-affordance, per-agent)
        self._affordance_streaks: dict[str, torch.Tensor] = {}
        # Track count of unique affordances used per agent
        self._unique_affordances_count = torch.zeros(self.num_agents, dtype=torch.long, device=self.device)
        # Track set of unique affordances seen per agent
        self._affordances_seen: list[set[str]] = [set() for _ in range(self.num_agents)]

        # Initialize affordance positions
        # v2.1: all affordances from affordances.yaml are deployable; no curriculum-level
        # enabled_affordances gating via training.yaml.
        self._affordance_layout_cache: tuple[torch.Tensor, torch.Tensor] | None = None
        self._native_layout_revision = 0
        self._native_layout_preparations: WeakKeyDictionary[PreparedNativeLayout, _NativeLayoutData] = WeakKeyDictionary()
        if self.randomize_affordances:
            self._randomize_affordance_positions()
        else:
            self._apply_configured_affordance_positions()

        # Built last: the token encoder reads the substrate, the meter columns, the
        # compiled affordance/effect declarations and the VFS registry, so every phase
        # above must have run.
        self._observation_encoder = build_token_observation_encoder(self)

    def _affordance_layout(self) -> tuple[torch.Tensor, torch.Tensor]:
        """`([C, D] positions, [C] deployed)` in COMPILED SLOT ORDER, cached.

        Affordance layouts are static between resets; rebuilding this per tick was the
        per-tick Python loop + `torch.stack` measured by `hamlet-c7084169f7`. The cache
        is invalidated wherever `self.affordances` is written.
        """
        if self._affordance_layout_cache is not None:
            return self._affordance_layout_cache
        dim = self.substrate.position_dim
        affordance_type = self.token_spec.get_type("affordance")
        slot_refs = [] if affordance_type is None else [binding.filler_ref for binding in affordance_type.slot_bindings]
        deployed = torch.tensor([ref in self.affordances for ref in slot_refs], dtype=torch.bool, device=self.device)
        zero = torch.zeros(dim, dtype=self.substrate.position_dtype, device=self.device)
        positions = torch.stack([self.affordances.get(ref, zero) for ref in slot_refs]) if slot_refs else zero.new_zeros((0, dim))
        self._affordance_layout_cache = (positions.to(device=self.device), deployed)
        return self._affordance_layout_cache

    def _build_token_publish_context(self) -> TokenPublishContext:
        """One tick's publisher inputs (token-obs spec §3).

        `vision_range` is the substrate's visibility radius argument: `None` under full
        observability (pass-all), the declared normalized fraction under POMDP. That is
        the ONLY thing partial observability changes about the observation — the TokenSpec
        is identical (spec §3; POMDP does not shrink or reshape the tensor).
        """
        affordance_positions, affordance_deployed = self._affordance_layout()
        return TokenPublishContext(
            positions=self.positions,
            velocities=self._encode_velocity_observation(),
            meters=self.meters,
            affordance_positions=affordance_positions,
            affordance_deployed=affordance_deployed,
            vision_range=self.vision_range if self.partial_observability else None,
            agent_slots=None,
            item_slots=self._item_slot_batch(),
            effect_slots=self._effect_slot_batch(),
        )

    @env_guard
    def attach_runtime_registry(self, registry: AgentRuntimeRegistry) -> None:
        """Attach runtime registry for telemetry tracking."""
        self._participation_ingress()
        self.runtime_registry = registry

    def retain_parent_custody(self) -> AbstractContextManager[EnvParentCustody]:
        """Retain ENV exclusion through explicit parent execution and its consumer."""
        return self._env_custody.retain()

    @env_guard
    def set_exploration_runtime(self, *, exploration: ExplorationRuntime, claim_vector_step: Callable[..., int]) -> None:
        """Bind once before world role custody freezes; equal rebinding also refuses."""
        self._participation_ingress()
        if self._exploration_bound or self._manual_session is not None or self._world_phase != "fresh-unbound":
            raise ValueError("exploration runtime must bind once before world authority registration")
        if not isinstance(exploration, ExplorationRuntime) or not callable(claim_vector_step):
            raise TypeError("ENV requires a current exploration runtime and parent claim callback")
        self._exploration_runtime = exploration
        self._claim_vector_step = claim_vector_step
        self._exploration_bound = True

    @env_guard
    def bind_manual_execution(self, *, population_owner: object) -> ManualPhysicalSession:
        """Issue the sole manual driver after role binding, before bootstrap/reset."""
        self._require_phase("fresh-bound")
        if (
            self._manual_session is not None
            or self._exploration_bound
            or self._world_role_owners.get("population") is not population_owner
            or self._world_authority is None
            or self._world_bootstrap is not None
            or self._env_custody.scope is not None
        ):
            raise ValueError("manual execution requires the exact fresh bound population and no execution binding")
        session = ManualPhysicalSession._issue(self, population_owner)
        self._manual_session = session
        return session

    @env_guard
    def _step_manual(
        self, *, session: ManualPhysicalSession, accepted: WorldAcceptedEpisode, actions: torch.Tensor, depletion_multiplier: float
    ) -> ManualPhysicalStepResult:
        if type(session) is not ManualPhysicalSession or session is not self._manual_session:
            raise ValueError("manual physical entry requires this ENV's issued session")
        return session._step(accepted, actions, depletion_multiplier)

    @env_guard
    def _retire_manual(
        self, *, session: ManualPhysicalSession, accepted: WorldAcceptedEpisode, world_ids: tuple[str, ...], reason: str
    ) -> WorldRecord:
        if type(session) is not ManualPhysicalSession or session is not self._manual_session:
            raise ValueError("manual retirement requires this ENV's issued session")
        return session._retire(accepted, world_ids, reason)

    def _apply_configured_affordance_positions(self) -> None:
        """Load static affordance positions from config/optimization data."""
        self._participation_ingress()
        self._native_layout_revision += 1

        if self.substrate.position_dim == 0:
            empty = torch.zeros(0, dtype=self.substrate.position_dtype, device=self.device)
            for name in self.affordances.keys():
                self.affordances[name] = empty.clone()
            self._affordance_layout_cache = None
            return

        for name in self.affordances.keys():
            source = self.affordance_positions_from_config.get(name)
            if source is None:
                optimization_tensor = self.affordance_positions_from_optimization.get(name)
                if isinstance(optimization_tensor, torch.Tensor):
                    source = optimization_tensor.tolist()
                else:
                    source = optimization_tensor

            tensor = self._position_to_tensor(source, name)
            self.affordances[name] = tensor
        self._affordance_layout_cache = None

    def _position_to_tensor(self, raw_position: Any, affordance_name: str) -> torch.Tensor:
        """Convert raw config/optimization positions into substrate tensors."""

        if self.substrate.position_dim == 0:
            return torch.zeros(0, dtype=self.substrate.position_dtype, device=self.device)

        if raw_position is None:
            raise ValueError(f"Affordance '{affordance_name}' requires explicit position when randomize_affordances is disabled.")

        if isinstance(raw_position, torch.Tensor):
            tensor = raw_position.to(device=self.device, dtype=self.substrate.position_dtype)
        elif isinstance(raw_position, dict):
            if set(raw_position.keys()) == {"q", "r"}:
                coords = [raw_position["q"], raw_position["r"]]
            else:
                raise ValueError(
                    f"Affordance '{affordance_name}' provided unsupported position mapping keys: {sorted(raw_position.keys())}."
                )
            tensor = torch.tensor(coords, dtype=self.substrate.position_dtype, device=self.device)
        elif isinstance(raw_position, list | tuple):
            tensor = torch.tensor(list(raw_position), dtype=self.substrate.position_dtype, device=self.device)
        elif isinstance(raw_position, Number):
            tensor = torch.tensor([raw_position], dtype=self.substrate.position_dtype, device=self.device)
        else:
            raise ValueError(f"Affordance '{affordance_name}' provided unsupported position type: {type(raw_position)!r}.")

        if tensor.numel() != self.substrate.position_dim:
            raise ValueError(
                f"Affordance '{affordance_name}' position has {tensor.numel()} dims but substrate requires {self.substrate.position_dim}."
            )

        return tensor

    def _affordance_open_mask(self, affordance_name: str) -> torch.Tensor:
        """`[num_worlds]` bool: whether each world's affordance is open now (its declared opening hours)."""
        scheduled = self._is_affordance_open(affordance_name)
        return torch.full((self.num_agents,), scheduled, dtype=torch.bool, device=self.device)

    def _is_affordance_open(self, affordance_name: str, hour: int | None = None) -> bool:
        """Return True if an affordance's declared opening hours admit the specified (or current) hour."""

        if not self.enable_temporal_mechanics:
            return True

        active_hour = self.time_of_day if hour is None else hour
        try:
            return self.vtc_affordance_gate_program.is_affordance_open(
                affordance_name,
                time_of_day=active_hour,
                device=self.device,
            )
        except KeyError as exc:
            raise ValueError(f"Missing VTC operating-hour gate for affordance '{affordance_name}'") from exc

    def _clock_hour(self) -> int:
        """The hour `global_tick` falls in: the one derivation of every hour the engine uses."""
        return (self.global_tick % int(self.day_length)) if self.enable_temporal_mechanics else 0

    def _publish_engine_tick(self) -> None:
        """Write `global_tick` into the registry's engine `tick` (the one temporal primitive).

        `tick` is a global like any other: one row per world. Every world steps in
        lockstep, so the engine writes the same instant into every row.
        """
        self._participation_ingress()
        self.vfs_registry.set_engine_value("tick", torch.full((self.vfs_registry.num_worlds,), float(self.global_tick), device=self.device))

    def _build_action_space_from_runtime_artifact(self, runtime_action_space: RuntimeActionSpace) -> ComposedActionSpace:
        """Build ComposedActionSpace from compiler-emitted runtime actions."""
        actions = [
            ActionConfig(
                id=action.id,
                name=action.name,
                type=action.type,
                costs=dict(action.costs),
                effects=dict(action.effects),
                delta=list(action.delta) if action.delta is not None else None,
                teleport_to=list(action.teleport_to) if action.teleport_to is not None else None,
                enabled=action.enabled,
                description=action.description,
                icon=action.icon,
                source=action.source,
                source_affordance=action.source_affordance,
                writes=cast(Any, [dict(write) for write in action.writes]),
            )
            for action in runtime_action_space.actions
        ]
        return ComposedActionSpace(
            actions=actions,
            substrate_action_count=runtime_action_space.substrate_action_count,
            custom_action_count=runtime_action_space.custom_action_count,
            affordance_action_count=runtime_action_space.affordance_action_count,
            enabled_action_names=(
                set(runtime_action_space.enabled_action_names) if runtime_action_space.enabled_action_names is not None else None
            ),
        )

    def _initialize_vfs_subsystem(self) -> None:
        """Build the VFS variable registry and evaluator.

        Phase method of __init__ (hamlet-2559b98232). Writes:
        ``vfs_variables``, ``vfs_registry``,
        ``vfs_evaluator``, ``vfs_evaluation_marks``, ``meter_name_to_index``,
        Depends on ``self.metadata``, ``self.num_agents``,
        ``self.device``, ``self.universe``.
        """
        universe = self.universe
        self.vfs_variables: list[VariableDef] = list(self.level.vfs_variables)

        # Items are per world (S1). One world's arena is its ground slots plus its agents'
        # carried slots (`item_capacity`, the same count that sizes the `item` token); the
        # registry holds one such block per world, flat: row = world * C + slot.
        self.items_per_world = (
            item_capacity(
                max_items_in_world=universe.items_catalog.max_items_in_world,
                max_items_per_agent=universe.items_catalog.max_items_per_agent,
                declared_agents_per_world=None,
            )
            if universe.items_catalog
            else 0
        )
        item_profiles = None
        if universe.compiled_vfs_profiles is not None:
            item_profiles = universe.compiled_vfs_profiles.item_profiles

        self.vfs_registry = VariableRegistry(
            variables=self.vfs_variables,
            num_agents=self.num_agents,
            device=self.device,
            items_per_world=self.items_per_world,
            num_affordances=self.metadata.affordance_count,
            item_profiles=item_profiles,
        )

        # VFS has no lifecycle counter: this is the fresh sequence-zero ENV projection.
        # Its domain is independent of ambient RNG, unlike simulator spawn/layout work.
        self.vfs_randomness = VFSRandomness(context=self._current_vfs_context())
        self.vfs_evaluator: VFSEvaluator | None = None
        if universe.compiled_vfs_profiles is not None:
            self.vfs_evaluator = VFSEvaluator(history_spec=universe.vfs_history_spec)
            self.vfs_evaluation_marks = universe.vfs_evaluation_marks
        else:
            self.vfs_evaluation_marks = None

        meter_name_to_index = dict(self.metadata.meter_name_to_index)
        self.meter_name_to_index = meter_name_to_index

        # The one resolver every interaction pipeline compiles against (VFS round-2 S5),
        # built from the same compiled products, by the same constructor, as the compiler's.
        expression_profiles = (
            ()
            if universe.compiled_vfs_profiles is None
            else (universe.compiled_vfs_profiles.global_profile, universe.compiled_vfs_profiles.agent_profile)
        )
        self.command_symbols = CommandSymbols(
            namespace=Namespace.of_registry(
                self.vfs_variables, meters=tuple(meter.name for meter in self.level.bars.meters), item_profiles=item_profiles or {}
            ),
            expressions=expression_sources(expression_profiles),
            time_enabled=self.temporal_support_enabled,
        )

    def _initialize_dac_engine(self) -> None:
        """Construct the DAC reward backend and prepare the runtime-registry slot.

        Phase method of __init__ (hamlet-2559b98232). Writes ``dac_engine``
        and ``runtime_registry``. Depends on ``vfs_registry`` from the VFS
        phase.
        """
        bar_index_map = env_factory._build_bar_index_map(self.level.meter_metadata)
        self.dac_engine = DACEngine(
            dac_config=self.level.drive,
            vfs_registry=self.vfs_registry,
            device=self.device,
            num_agents=self.num_agents,
            bar_index_map=bar_index_map,
        )
        self.runtime_registry = None

    def _initialize_item_subsystem(self, num_agents: int) -> None:
        """Build the item manager, inventory, and action handler — or leave
        every slot None when the universe has no items catalog.

        Phase method of __init__ (hamlet-2559b98232). Must run after meters
        are allocated (the action handler captures the meter index map) and
        after the effect manager + command executor exist.
        """
        universe = self.universe
        self.item_manager: ItemManager | None = None
        self.item_inventory: InventoryState | None = None
        self.item_handler: ItemActionHandler | None = None

        if universe.items_catalog is None:
            return

        if universe.compiled_vfs_profiles is None or not universe.compiled_vfs_profiles.item_profiles:
            raise ValueError(
                "items_catalog provided but compiled_vfs_profiles.item_profiles is missing. "
                "Declare item profile names and state in the canonical variables declaration for all item types."
            )

        item_token = self.token_spec.get_type("item")
        token_capacity = 0 if item_token is None else item_token.capacity
        if token_capacity != self.items_per_world:
            # One compiled `item` slot per per-world arena row (slot = row - world * C);
            # anything else would drop or alias items in the observation.
            raise ValueError(
                f"Compiled item token capacity {token_capacity} disagrees with the per-world item arena "
                f"({self.items_per_world} rows); recompile the config pack"
            )
        self.item_manager = ItemManager(
            catalog=universe.items_catalog,
            items_per_world=self.items_per_world,
            num_worlds=num_agents,
            substrate=self.substrate,
            device=self.device,
            symbols=self.command_symbols,
            vfs_registry=self.vfs_registry,
            effect_manager=self.effect_manager,
        )
        self.item_inventory = self.item_manager.inventory
        self.item_handler = ItemActionHandler(
            manager=self.item_manager,
            command_executor=self.command_executor,
            vfs_registry=self.vfs_registry,
            meter_name_to_index=self.meter_name_to_index,
            effect_manager=self.effect_manager,
            agent_positions=lambda: self.positions,
        )

    def _initialize_affordance_engine(self, num_agents: int) -> None:
        """Build the affordance engine.

        Phase method of __init__ (hamlet-2559b98232). Must run after the
        item subsystem; depends on the VTC modulation program, VFS registry,
        command symbols, command executor, and effect manager.
        """
        self.affordance_engine = AffordanceEngine(
            tuple(self.level.affordances.affordances),
            num_agents,
            self.device,
            self.meter_name_to_index,
            modulation_program=self.vtc_modulation_program,
            vfs_registry=self.vfs_registry,
            command_symbols=self.command_symbols,
            command_executor=self.command_executor,
            effect_manager=self.effect_manager,
            meter_bounds_min=self.meter_bounds_min,
            meter_bounds_max=self.meter_bounds_max,
            item_manager=self.item_manager or NullItemManager(),
        )

    def _build_movement_deltas(self) -> torch.Tensor:
        """Build movement delta tensor from action space (metadata-driven).

        Returns:
            [action_dim, position_dim] tensor of movement deltas
        """
        position_dim = self.substrate.position_dim

        # Initialize zero deltas for all actions
        deltas = torch.zeros(
            (self.action_dim, position_dim),
            device=self.device,
            dtype=self.substrate.position_dtype,
        )

        # Fill in deltas from any action that declares a delta
        for action in self.action_space.actions:
            if action.type == "movement" and action.delta is not None:
                deltas[action.id] = torch.tensor(
                    action.delta,
                    device=self.device,
                    dtype=self.substrate.position_dtype,
                )

        return deltas

    @env_guard
    def get_action_label_names(self) -> dict[int, str]:
        """Get action label names for current substrate.

        Returns:
            Dictionary mapping action indices to user-facing labels.

        Example:
            >>> env = VectorizedHamletEnv(...)
            >>> labels = env.get_action_label_names()
            >>> print(labels)
            {0: 'UP', 1: 'DOWN', 2: 'LEFT', 3: 'RIGHT', 4: 'INTERACT', 5: 'WAIT'}
        """
        return dict(self.action_labels.get_all_labels())

    @property
    def bars(self) -> dict[str, torch.Tensor]:
        """Convert meters tensor to dict for effects system.

        Returns:
            Dictionary mapping bar names to meter tensors [num_agents]
        """
        bars_dict = {}
        for bar_name, idx in self.meter_name_to_index.items():
            bars_dict[bar_name] = self.meters[:, idx]
        return bars_dict

    def _reset_world_state(self) -> torch.Tensor:
        """Reset all environments and return the first observation of the episode.

        The observation describes the state the first action is taken in, exactly as
        `step()`'s observation describes the state the next action is taken in. Reset runs
        the tail of `step()`'s phase order from an empty world, at instant 0:

        1. world state: affordance layout, positions, velocity, meters, dones, step counts;
        2. clock: `global_tick = 0`, registry `tick` written after `reset_episode_scoped`
           (tick is episode-lifetime, so an earlier write would be clobbered), hour 0;
        3. episode-scoped engine state: affordance tracking and overrides, effects,
           expression history, items and inventories;
        4. expressions: `_evaluate_vfs_profiles()` over that state (step: after the clock
           advance), so no expression shows its declared literal or, for a persistent
           one, the previous episode's value;
        5. item spawn, whose predicates read the evaluated expressions (step: respawn
           after evaluation);
        6. observation.
        """
        self._participation_ingress()
        # Refresh affordance layout each episode so randomization/configured layouts stay in sync.
        # randomize_affordance_positions() returns agent positions clear of every affordance.
        if self.randomize_affordances:
            agent_positions = self._randomize_affordance_positions()
            self.positions = (
                agent_positions
                if agent_positions is not None
                else self.substrate.initialize_positions(self.num_agents, self.device, generator=None)
            )
        else:
            self._apply_configured_affordance_positions()
            # When using configured positions, agents still spawn randomly (could still collide)
            # TODO: Consider also handling configured affordance case for complete collision-free guarantee
            self.positions = self.substrate.initialize_positions(self.num_agents, self.device, generator=None)

        # At episode start, velocity is zero.
        self._velocity = torch.zeros(
            (self.num_agents, self.substrate.position_dim),
            dtype=torch.float32,
            device=self.device,
        )

        # Initial meter values (normalized to [0, 1]) from compiled bars config
        self.meters = self.initial_meter_values.unsqueeze(0).expand(self.num_agents, -1).clone()

        self.dones = torch.zeros(self.num_agents, dtype=torch.bool, device=self.device)
        self.step_counts = torch.zeros(self.num_agents, dtype=torch.long, device=self.device)
        self.intrinsic_weights = torch.ones(self.num_agents, dtype=torch.float32, device=self.device)  # Reset to 1.0

        # 2. Clock at instant 0.
        self.global_tick = 0
        self.vfs_registry.reset_episode_scoped()
        self._publish_engine_tick()
        self.time_of_day = self._clock_hour()
        if self.enable_temporal_mechanics:
            self.interaction_progress.fill_(0)
            self.last_interaction_affordance = [None] * self.num_agents
            self.last_interaction_position.fill_(0)

        # 3. Episode-scoped engine state.
        self._last_affordances = [None] * self.num_agents
        self._affordance_streaks = {}
        self._unique_affordances_count.zero_()
        self._affordances_seen = [set() for _ in range(self.num_agents)]
        # Effects are episode-scoped: discard every active effect and all delayed work
        # (no hooks run) before anything in this episode can spawn one.
        if self.effect_manager is not None:
            self.effect_manager.reset()

        # Reset temporal history so temporal VFS ops don't leak across episodes
        if self.vfs_evaluator is not None:
            self.vfs_evaluator.reset()
        # Public reset has already installed the validated reservation's VFS projection.

        if self.item_manager is not None:
            self.item_manager.reset_state()  # and its inventory

        # 4. Expressions over the instant-0 state.
        self._evaluate_vfs_profiles()

        # 5. Initial item spawn into every world (predicates read the evaluated
        # expressions; placement asks the substrate, so every substrate spawns).
        if self.item_manager is not None and self.level.items_appearance is not None:
            self.item_manager.spawn_initial_items(
                appearance_config=self.level.items_appearance,
                current_tick=self.global_tick,
                bars=self.bars,
            )

        return self._get_observations()

    @classmethod
    def from_universe(
        cls,
        universe: CompiledUniverse,
        *,
        level_name: str,
        num_agents: int,
        device: torch.device | str,
        world_roster: WorldRosterDeclaration,
        training_seed: int,
        lane_world_ids: tuple[str, ...],
    ) -> VectorizedHamletEnv:
        """Instantiate environment using metadata from a compiled universe.

        Args:
            universe: CompiledUniverse with hierarchical configs
            level_name: Curriculum level to instantiate (e.g., \"L0_0_minimal\").
                Must be provided explicitly; no default level selection is performed.
            num_agents: Number of parallel agents
            device: PyTorch device (explicit)

        Returns:
            VectorizedHamletEnv instance
        """
        if level_name is None:
            raise ValueError("level_name must be explicit")
        return env_factory.from_universe(
            cls,
            universe,
            level_name=level_name,
            num_agents=num_agents,
            device=device,
            world_roster=world_roster,
            training_seed=training_seed,
            lane_world_ids=lane_world_ids,
        )

    def _get_observations(self) -> torch.Tensor:
        """Serialize this tick's compiled token observation, `[num_agents, total_dims]`."""
        self._participation_ingress()
        return self._encode_observations()

    def _encode_observations(self) -> torch.Tensor:
        """Internal fixed-state read, also used inside the participation guard."""
        return self._observation_encoder.encode(self.num_agents, self._build_token_publish_context())

    def _item_slot_batch(self) -> ItemSlotBatch | None:
        """Every world's live items keyed by compiled `item` token slot.

        Items are per world (S1): world `w`'s item at arena row `r` occupies compiled slot
        `r - w * C` (`C` = the per-world arena = the `item` token capacity, checked at
        init). Ground and carried items both publish: a carried item (an exclusive one is
        lifted into `held`; a shared one stays on the ground) takes its holder's position
        and inventory slot, in the holder's world.
        """
        manager = self.item_manager
        if manager is None or self.items_per_world == 0:
            return None
        inventory = self.item_inventory
        dim = self.substrate.position_dim
        per_world = self.items_per_world
        # Host-side assembly in plain Python lists, then one tensor per field: no per-item
        # tensor ops. Holder inventories and agent positions cross to the host once.
        inventory_rows: list[list[int]] | None = None
        if inventory is not None:
            inventory_rows = inventory.slots.tolist()
        agent_positions: list[list[Any]] | None = None
        if dim > 0:
            agent_positions = self.positions.tolist()
        entry_worlds: list[int] = []
        entry_slots: list[int] = []
        entry_positions: list[list[Any]] = []
        entry_carried: list[bool] = []
        entry_owner: list[int] = []
        for world in range(self.num_agents):
            for item in manager.items_in_world(world):
                position: list[Any] = list(item.position)
                carried = False
                inventory_slot = -1
                holder = manager.holder_of(item)
                if holder is not None and inventory_rows is not None and item.instance_id in inventory_rows[holder]:
                    carried = True
                    inventory_slot = inventory_rows[holder].index(item.instance_id)
                    if agent_positions is not None:
                        position = agent_positions[holder]
                entry_worlds.append(world)
                entry_slots.append(item.vfs_index - world * per_world)
                entry_positions.append(position)
                entry_carried.append(carried)
                entry_owner.append(inventory_slot)

        if not entry_slots:
            return None
        used = sorted(set(entry_slots))
        column_of = {slot: column for column, slot in enumerate(used)}
        k = len(used)
        n = self.num_agents
        slot_tensor = torch.tensor(used, dtype=torch.long, device=self.device)
        world_index = torch.tensor(entry_worlds, dtype=torch.long, device=self.device)
        column_index = torch.tensor([column_of[slot] for slot in entry_slots], dtype=torch.long, device=self.device)
        active = torch.zeros((n, k), dtype=torch.bool, device=self.device)
        active[world_index, column_index] = True
        positions = torch.zeros((n, k, dim), dtype=self.substrate.position_dtype, device=self.device)
        if dim > 0:
            positions[world_index, column_index] = torch.tensor(entry_positions, dtype=self.substrate.position_dtype, device=self.device)
        # Every world's row for a column is its own block's row for that slot.
        vfs_rows = torch.arange(n, device=self.device).unsqueeze(1) * per_world + slot_tensor.unsqueeze(0)
        carried_mask = torch.zeros((n, k), dtype=torch.bool, device=self.device)
        carried_mask[world_index, column_index] = torch.tensor(entry_carried, dtype=torch.bool, device=self.device)
        owner_slot = torch.full((n, k), -1, dtype=torch.long, device=self.device)
        owner_slot[world_index, column_index] = torch.tensor(entry_owner, dtype=torch.long, device=self.device)
        return ItemSlotBatch(
            slot_indices=slot_tensor,
            active=active,
            positions=positions,
            vfs_rows=vfs_rows,
            carried=carried_mask,
            owner_slot=owner_slot,
            source="item_manager",
        )

    def _effect_slot_batch(self) -> EffectSlotBatch | None:
        """Active observable effects keyed by compiled `effect` token slot.

        The compiled effect layout is scope-blocked in `EffectScope` vocabulary order,
        each block sized `budget x denominator` (`effect_slot_refs`). Within a block a
        live effect takes the next free index, per world — effect content is per world
        because the agent-scope store is keyed by world (`num_agents` is a batch of
        independent worlds). Overflowing a scope's declared budget raises at publish
        time; it is never silently truncated.
        """
        manager = self.effect_manager
        effect_type = self.token_spec.get_type("effect")
        if manager is None or effect_type is None or effect_type.capacity == 0:
            return None
        catalog_order: dict[str, int] = {}
        for index, context in enumerate(effect_type.effect_catalog_contexts):
            prefix = "effect:"
            if not context.context_ref.startswith(prefix) or len(context.context_ref) == len(prefix):
                raise ValueError(f"Compiled effect catalog context {context.context_ref!r} must use the non-empty 'effect:<id>' authority")
            effect_id = context.context_ref[len(prefix) :]
            if effect_id in catalog_order:
                raise ValueError(f"Compiled effect catalog contains duplicate context authority for {effect_id!r}")
            catalog_order[effect_id] = index
        block_slots: dict[str, list[int]] = {}
        for binding in effect_type.slot_bindings:
            scope = binding.filler_ref.split(":")[1]
            block_slots.setdefault(scope, []).append(binding.slot_index)

        # per world: scope -> list of (slot, catalog index, remaining fraction, intensity)
        occupied: dict[int, list[tuple[int, int, float, float]]] = {}
        for world in range(self.num_agents):
            cursor = dict.fromkeys(block_slots, 0)
            rows: list[tuple[int, int, float, float]] = []
            for effect in self._observable_effects_for_world(world):
                scope = effect.scope.value if hasattr(effect.scope, "value") else str(effect.scope)
                slots = block_slots.get(scope)
                if not slots:
                    continue
                index = cursor[scope]
                if index >= len(slots):
                    raise TokenCapacityError("effect", len(slots), index + 1, f"effect_manager scope {scope!r}")
                cursor[scope] = index + 1
                catalog_index = catalog_order.get(effect.effect_id)
                if catalog_index is None:
                    raise ValueError(f"Active effect {effect.effect_id!r} is not in the compiled effect catalog")
                total = max(1, int(effect.duration_total))
                remaining = max(0, int(effect.duration_remaining))
                rows.append((slots[index], catalog_index, remaining / total, float(effect.intensity)))
            occupied[world] = rows

        used = sorted({slot for rows in occupied.values() for slot, _, _, _ in rows})
        if not used:
            return None
        column_of = {slot: column for column, slot in enumerate(used)}
        k = len(used)
        effect_indices = torch.zeros((self.num_agents, k), dtype=torch.long, device=self.device)
        remaining_fraction = torch.zeros((self.num_agents, k), dtype=torch.float32, device=self.device)
        intensity = torch.zeros((self.num_agents, k), dtype=torch.float32, device=self.device)
        active = torch.zeros((self.num_agents, k), dtype=torch.bool, device=self.device)
        for world, rows in occupied.items():
            for slot, catalog_index, fraction, live_intensity in rows:
                column = column_of[slot]
                effect_indices[world, column] = catalog_index
                remaining_fraction[world, column] = fraction
                intensity[world, column] = live_intensity
                active[world, column] = True
        return EffectSlotBatch(
            slot_indices=torch.tensor(used, dtype=torch.long, device=self.device),
            effect_indices=effect_indices,
            remaining_fraction=remaining_fraction,
            intensity=intensity,
            active=active,
            owner_slot=torch.full((k,), -1, dtype=torch.long, device=self.device),
            source="effect_manager",
        )

    def _observable_effects_for_world(self, world: int) -> list[Any]:
        """Every observable active effect living in `world`, any scope (each effect has one world)."""
        manager = self.effect_manager
        assert manager is not None
        return [effect for effect in manager.effects_in_world(world) if effect.observable]

    def _encode_velocity_observation(self) -> torch.Tensor | None:
        """Agent velocity (delta position per step), `[num_agents, position_dim]`; None when aspatial."""
        if self.substrate.position_dim == 0:
            return None
        return self._velocity

    @env_guard
    def get_action_masks(self) -> torch.Tensor:
        """Compute valid-action masks for the current tick.

        Delegates to :class:`ActionMaskBuilder`. Returns a
        ``[num_agents, action_dim]`` bool tensor where ``True`` is a valid
        action; semantics are documented on the builder.
        """
        self._participation_ingress()
        return self._build_action_masks()

    def _build_action_masks(self) -> torch.Tensor:
        return self.action_mask_builder.build(
            num_agents=self.num_agents,
            positions=self.positions,
            dones=self.dones if hasattr(self, "dones") else None,
            item_inventory=self.item_inventory,
            item_manager=self.item_manager,
            item_handler=self.item_handler,
            affordances=self.affordances,
            affordance_open=self._affordance_open_mask,
        )

    @env_guard
    def step(
        self,
        actions: torch.Tensor,  # [num_agents]
        depletion_multiplier: float = 1.0,  # Curriculum difficulty
        *,
        vector_step: PreparedVectorStep,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]:
        """
        Execute one step for all agents.

        Clock contract: the step's action is taken at instant `global_tick` (k) — the
        registry `tick`, `time_of_day` (which gates opening hours), effects'
        `current_step` and the action executor all read k. Once the transition phases have
        committed, the clock advances to k+1 at ONE point (`global_tick`, then the registry
        `tick`); expressions, terminal conditions, item aging/respawn and the observation
        all describe that instant, because the observation describes the state the next
        action is taken in. `time_of_day` flips to k+1's hour last, after the reward
        calculator has read the hour the action was taken at.

        Args:
            actions: [num_agents] tensor of actions (0-4)
            depletion_multiplier: Curriculum difficulty multiplier (0.2 = 20% difficulty)

        Returns:
            observations: [num_agents, observation_dim]
            rewards: [num_agents]
            dones: [num_agents] bool
            info: dict with metadata and owned bool [num_agents, action_dim]
                successor_action_masks for this same committed observation/status
        """
        self._participation_ingress()
        if not self._exploration_bound or self._manual_session is not None:
            raise ValueError("ordinary ENV.step requires its real POP/runtime binding")
        if self._world_phase != "active":
            raise ValueError("world episode must be accepted and activated before stepping")
        accepted = self._world_accepted
        if accepted is None:
            raise ValueError("active world episode requires its current accepted token")
        self._accepted(accepted)
        self._check_committed_participation()
        predecessor = self._get_observations().detach().clone()
        actions = actions.detach().clone()
        active_on_entry = ~self.dones.detach().clone()
        vector_tick = self._env_custody.outcall(
            "claim",
            self._claim_vector_step,
            owner=self._world_role_owners["population"],
            prepared=vector_step,
            accepted=accepted,
            world_ids=self.world_ids,
            predecessor=predecessor,
            actions=actions,
            active_on_entry=active_on_entry,
        )
        # Claim is a genuine owner callback and may perform fail-closed cleanup.
        # No-decision episodes require this check too, before the first write.
        self._require_phase("active")
        self._accepted(accepted)
        self._check_committed_participation()
        return self._step_physical(
            accepted=accepted,
            predecessor=predecessor,
            actions=actions,
            active_on_entry=active_on_entry,
            vector_tick=vector_tick,
            depletion_multiplier=depletion_multiplier,
            manual_decision=None,
        )

    def _step_physical(
        self,
        *,
        accepted: WorldAcceptedEpisode,
        predecessor: torch.Tensor,
        actions: torch.Tensor,
        active_on_entry: torch.Tensor,
        vector_tick: int,
        depletion_multiplier: float,
        manual_decision: WorldRecord | None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]:
        """The shared physical kernel; a manual entry consumes its genuine decision."""
        if manual_decision is not None:
            if self._manual_session is None:
                raise ValueError("manual physical decision has no bound issuer")
            self._manual_session._claim(manual_decision, accepted, predecessor, actions, active_on_entry, vector_tick)
        elif self._manual_session is not None:
            raise ValueError("manual physical work requires its issued decision")
        self._world_revision += 1
        self.vfs_registry.reset_tick_scoped()
        refusals_before = 0
        if self.effect_manager is not None:
            refusals_before = len(self.effect_manager.spawn_refusals)
        # 1. Execute actions and track successful interactions
        successful_interactions = self._action_executor._execute_actions(actions)
        self._run_vtc_transition_phases(
            self.vtc_transition_schedule.phase_graph.action_phases,
            actions=actions,
            active_mask=active_on_entry,
        )

        # 2. Deplete meters (base passive decay with curriculum difficulty)
        self._apply_vtc_passive_depletion(depletion_multiplier, active_on_entry)

        # 3. Passive threshold cascades via VTC relationship rules.
        self._apply_vtc_threshold_cascades(active_on_entry)

        # 3.5. Execute active effects (after cascades, before terminal checks)
        # Effects can modify bars based on current state after all natural dynamics applied
        bars_dict = {}
        for bar_name, idx in self.meter_name_to_index.items():
            bars_dict[bar_name] = self.meters[:, idx]

        if self.effect_manager is not None:
            self.effect_manager.tick(
                bars=bars_dict,
                vfs_registry=self.vfs_registry,
                current_step=self.global_tick,  # HIGH-01: Use global tick instead of agent 0
                item_manager=self.item_manager,
                agent_positions=self.positions,
                affordance_positions=self.affordances,
                substrate=self.substrate,
                # A world whose agent is done is frozen: its effects write nothing,
                # exactly as VTC rules are masked by activity.
                live=active_on_entry,
            )

        # Sync meters back from bars dict (effects may have modified them)
        for bar_name, idx in self.meter_name_to_index.items():
            self.meters[:, idx] = bars_dict[bar_name]

        self._run_vtc_transition_phases(
            self.vtc_transition_runner.phases_between("apply_threshold_cascades", "evaluate_terminal_conditions"),
            active_mask=active_on_entry,
        )

        # 3.6. Advance the clock to k+1: the transitions of instant k have committed.
        self.global_tick += 1  # HIGH-01: Track global time independently of agent 0
        self._publish_engine_tick()

        # 3.7. Evaluate VFS expressions over the committed state at the new instant: after
        # every transition phase that writes VFS variables (action writes, transition rules)
        # and after clamp_and_validate, so expressions never lag a transition write or
        # the clock.
        self._evaluate_vfs_profiles()

        # 4. Evaluate VTC terminal conditions
        self._apply_vtc_terminal_conditions(active_on_entry)
        authored_terminal = active_on_entry & self.dones

        # 5. Count eligible transitions, including the transition that ends a lane.
        self.step_counts += active_on_entry.to(dtype=self.step_counts.dtype)

        # 5.1. Age items and process periodic respawning at the new instant; respawn
        # predicates read the expressions evaluated at 3.7.
        if self.item_manager is not None:
            # Age all items (expire items that reach duration limit)
            self.item_manager.tick(self.global_tick, live=active_on_entry)
            # Respawn items whose periodic schedule timer has expired.
            self.item_manager.process_respawns(self.global_tick, bars=self.bars, live=active_on_entry)

        # 5.5. Check for retirement (reached maximum lifespan)
        # Authored termination wins coincidence with the configured lifespan.
        newly_retired = active_on_entry & ~authored_terminal & (self.step_counts >= self.agent_lifespan)

        # 6. Calculate rewards (interoception-aware)
        intrinsic_transition = None
        if manual_decision is None:
            intrinsic_context = IntrinsicTransitionContext(
                predecessor=predecessor,
                actions=actions,
                successor=self._get_observations(),
                active_on_entry=active_on_entry,
                vector_tick=vector_tick,
            )
            intrinsic_stamp = self._exploration_runtime.prepare_step_stamp(
                accepted=accepted,
                world_ids=self.world_ids,
                active_on_entry=active_on_entry,
                vector_tick=vector_tick,
            )
            intrinsic_transition = IntrinsicStepHandoff(intrinsic_context, intrinsic_stamp, accepted)
            rewards = self._reward_calculator._calculate_shaped_rewards(
                active_on_entry=active_on_entry,
                intrinsic_context=intrinsic_context,
                intrinsic_stamp=intrinsic_stamp,
                accepted=accepted,
            )
        else:
            rewards = self._reward_calculator._calculate_manual_rewards()
        bonus = newly_retired.to(dtype=rewards.dtype)
        components = self._last_reward_components
        components["extrinsic"] = components["extrinsic"] + bonus
        rewards = rewards + bonus
        rewards = torch.where(active_on_entry, rewards, torch.zeros_like(rewards))
        for name, component in components.items():
            components[name] = torch.where(active_on_entry, component, torch.zeros_like(component))
        self.intrinsic_weights = torch.where(active_on_entry, self.intrinsic_weights, torch.zeros_like(self.intrinsic_weights))
        self.dones = torch.logical_or(self.dones, newly_retired)
        newly_terminal = authored_terminal | newly_retired

        # Cancel any pending agent-scoped delayed work for agents that just became done
        self._cancel_terminal_effects(newly_terminal)

        # 7. time_of_day is DERIVED from global_tick — one temporal pipeline (token-obs
        # unit 2c). It flips to the new instant's hour only here: the reward calculator
        # (6) reads the hour the action was taken at, and from here on it gates the next
        # action, matching the registry tick and every expression in the observation.
        self.time_of_day = self._clock_hour()

        observations = self._get_observations()
        # Build only after all successor state, retirement and the next action's hour
        # have committed. Completed rows may be empty; a live row must be selectable.
        successor_action_masks = self._build_action_masks().clone()
        live_empty = ~self.dones & ~successor_action_masks.any(dim=1)
        if live_empty.any():
            agent_ids = torch.nonzero(live_empty, as_tuple=False).flatten().tolist()
            raise ValueError(
                "nonterminal successor has no legal action: "
                f"pack={self.config_pack_path}, level={self.level_name}, tick={self.global_tick}, agents={agent_ids}"
            )

        info = {
            "successor_action_masks": successor_action_masks,
            "active_on_entry": active_on_entry.clone(),
            "newly_terminal": newly_terminal.clone(),
            "newly_retired": newly_retired.clone(),
            "step_counts": self.step_counts.clone(),
            "positions": self.positions.clone(),
            "successful_interactions": successful_interactions,  # {agent_idx: affordance_name}
            "reward_components": self._last_reward_components,  # DAC breakdown
            "intrinsic_weight": self.intrinsic_weights,  # Effective modifier weight
            # Effect spawns this step refused at `max_active_effects`, each naming its world.
            "effect_spawn_refusals": () if self.effect_manager is None else tuple(self.effect_manager.spawn_refusals[refusals_before:]),
        }
        if intrinsic_transition is not None:
            info["intrinsic_transition"] = intrinsic_transition

        self._advance_participation_witness(observations)
        return observations, rewards, self.dones, info

    def _cancel_terminal_effects(self, newly_terminal: torch.Tensor) -> None:
        if self.effect_manager is not None and self.effect_manager.scheduler is not None:
            if newly_terminal.any():
                for idx in torch.nonzero(newly_terminal, as_tuple=False).flatten():
                    self.effect_manager.cancel_scheduled_for_entity(scope="agent", entity_id=int(idx))

    def _evaluate_vfs_profiles(self) -> None:
        """Evaluate global then agent profile expressions and commit them to the registry."""
        self._participation_ingress()
        if self.vfs_evaluator is not None and self.universe.compiled_vfs_profiles is not None:
            # Build execution context from current state
            bars_dict_vfs = {name: self.meters[:, idx] for name, idx in self.meter_name_to_index.items()}

            # Get current VFS state from registry
            # HIGH-02: Use proper VFS API instead of direct _storage access
            current_vfs_state = self._current_vfs_state()
            # One instant of history: seeded at the episode's first instant from this
            # pre-evaluation state, committed after both profiles (WP14).
            self.vfs_evaluator.begin_instant(bars_dict_vfs, current_vfs_state, self.device)

            # Evaluate global profile
            global_profile = self.universe.compiled_vfs_profiles.global_profile
            if global_profile is not None:
                marks = self.vfs_evaluation_marks.get("global", set()) if self.vfs_evaluation_marks else set()

                updated_vfs = self.vfs_evaluator.evaluate_global_profile(
                    profile=global_profile,
                    bars=bars_dict_vfs,
                    vfs_state=current_vfs_state,
                    marks=marks,
                    device=self.device,
                    agent_positions=self.positions.to(dtype=torch.float32, device=self.device),
                    affordance_positions={k: v.to(dtype=torch.float32, device=self.device) for k, v in self.affordances.items()},
                    draws=self._vfs_draws(),
                )

                self._write_back_profile_expressions(
                    "Global-profile", "global_profile", global_profile, updated_vfs, require_agent_shape=False
                )
                # Agent expressions may read globals: re-snapshot so they see this tick's
                # global expression values, not the pre-write-back snapshot.
                current_vfs_state = self._current_vfs_state()

            # Evaluate agent profile (hamlet-5d74335111). Compiled agent profiles are
            # CompiledGlobalProfile — the same machinery, the same mark-and-sweep
            # static-skip in evaluate_global_profile, and the same expression-only
            # write-back filter (statics are storage, never re-written from a
            # dependency-chased initial — hamlet-df3a96bbac applies here too), but
            # expressions here already produce [num_agents]-shaped tensors from
            # `bar.*` references, so write-back is checked against that exact shape.
            agent_profile = self.universe.compiled_vfs_profiles.agent_profile
            if agent_profile is not None:
                agent_marks = self.vfs_evaluation_marks.get("agent", set()) if self.vfs_evaluation_marks else set()
                updated_agent_vfs = self.vfs_evaluator.evaluate_global_profile(
                    profile=agent_profile,
                    bars=bars_dict_vfs,
                    vfs_state=current_vfs_state,
                    marks=agent_marks,
                    device=self.device,
                    agent_positions=self.positions.to(dtype=torch.float32, device=self.device),
                    affordance_positions={k: v.to(dtype=torch.float32, device=self.device) for k, v in self.affordances.items()},
                    draws=self._vfs_draws(),
                )
                self._write_back_profile_expressions(
                    "Agent-profile", "agent_profile", agent_profile, updated_agent_vfs, require_agent_shape=True
                )

            # A world whose agent is done is frozen: its history does not advance. At the
            # step's evaluation `dones` is still the entry mask (terminals run after it).
            self.vfs_evaluator.commit_instant(bars_dict_vfs, self._current_vfs_state(), live=~self.dones)

    def _vfs_draws(self) -> DrawInstant:
        """Draw from the in-reset candidate or accepted per-world identity, never rows."""
        if self._world_phase == "resetting":
            expected = self._world_vfs_pending
            if expected is None:
                raise ValueError("reset-time VFS draws require a validated reservation projection")
        else:
            self._require_phase("active-awaiting-activation", "active", "boundary-pending", "closed-awaiting-release", "released-completed")
            expected = self._current_vfs_context()
        if self.vfs_randomness.context != expected:
            raise ValueError("VFS draw context contradicts ENV world identity")
        return self.vfs_randomness.instant(tick=self.global_tick, device=self.device)

    def _current_vfs_context(self) -> VFSWorldContext:
        """Pure projection of ENV's actual lane binding and accepted cursors."""
        return VFSWorldContext(
            training_seed=self._world_seed,
            world_ids=self.world_ids,
            world_episode_seqs=tuple(self._world_cursors[world_id] for world_id in self.world_ids),
        )

    @env_guard
    def vfs_random_state(self) -> dict[str, Any]:
        return self._vfs_random_state()

    def _vfs_random_state(self) -> dict[str, Any]:
        """Export owned current identity data, excluding provisional or failed attempts."""
        self._participation_ingress()
        if self._world_phase in ("resetting", "restoring", "quarantined"):
            raise ValueError("VFS native export requires a stable authoritative context")
        if self.vfs_randomness.context != self._current_vfs_context():
            raise ValueError("VFS native context contradicts ENV world identity")
        return self.vfs_randomness.state()

    @env_guard
    def restore_vfs_random_state(self, state: Mapping[str, Any]) -> None:
        """Validate/reinstall only the current projection; joint restore owns cursor changes."""
        self._require_phase("fresh-unbound", "fresh-bound", "bootstrap-ready", "released-completed")
        context = VFSRandomness.validate_state(state, expected=self._current_vfs_context())
        self.vfs_randomness = VFSRandomness(context=context)

    def _execute_actions(self, actions: torch.Tensor) -> dict:
        """Execute movement, interaction, and wait actions."""
        self._participation_ingress()
        return self._action_executor._execute_actions(actions)

    def _apply_vtc_passive_depletion(self, depletion_multiplier: float, active_mask: torch.Tensor) -> None:
        """Apply compiled VFS passive-depletion rules (and any transition rule at that phase)
        to the agents active on entry to this step (``step()`` captures the mask once)."""
        self._run_vtc_transition_phases(
            ("apply_passive_depletion",),
            active_mask=active_mask,
            depletion_multiplier=depletion_multiplier,
        )

    def _apply_vtc_threshold_cascades(self, active_mask: torch.Tensor) -> None:
        """Apply compiled VFS threshold-cascade rules (and any transition rule at that phase)
        to the agents active on entry to this step."""
        self._run_vtc_transition_phases(
            ("apply_threshold_cascades",),
            active_mask=active_mask,
        )

    def _apply_vtc_terminal_conditions(self, active_mask: torch.Tensor) -> None:
        """Evaluate compiled VFS terminal-condition rules over meter bars for the agents
        active on entry to this step."""
        self._run_vtc_transition_phases(
            ("evaluate_terminal_conditions",),
            dones=self.dones,
            active_mask=active_mask,
        )

    def _run_vtc_transition_phases(
        self,
        phases: tuple[str, ...],
        *,
        active_mask: torch.Tensor,
        actions: torch.Tensor | None = None,
        dones: torch.Tensor | None = None,
        depletion_multiplier: float = 1.0,
    ) -> None:
        """Execute generic compiled VTC transition phases and commit their writes."""
        self._participation_ingress()
        result = self.vtc_transition_runner.run_phases(
            phases,
            VTCTransitionContext(
                actions=actions,
                vfs_state=self._current_vfs_state(),
                bars_state=self._current_bar_state(),
                active_mask=active_mask,
                device=self.device,
                draws=self._vfs_draws(),
                dones=dones,
                depletion_multiplier=depletion_multiplier,
            ),
        )
        self._commit_vtc_transition_state(result)

    def _commit_vtc_transition_state(self, state: VTCTransitionState) -> None:
        self._participation_ingress()
        # Authorize the complete selected operation before publishing any result.
        # The remaining snapshot values are reads, including immutable literals.
        for variable_id in sorted(state.attempted_vfs_targets):
            if variable_id not in state.vfs_state:
                raise KeyError(f"VTC write intent has no value for '{variable_id}'")
            self.vfs_registry.authorize_write(variable_id, writer="engine")
        for bar_name, value in state.bars_state.items():
            self._set_vtc_bar_value(bar_name, value)
        for variable_id in sorted(state.attempted_vfs_targets):
            self.vfs_registry.set_engine_value(variable_id, state.vfs_state[variable_id])
        if state.dones is not None:
            self.dones = state.dones

    def _write_back_profile_expressions(
        self,
        profile_label: str,
        write_source: str,
        profile: CompiledGlobalProfile,
        updated_vfs: dict[str, torch.Tensor],
        *,
        require_agent_shape: bool,
    ) -> None:
        """Commit profile expression outputs to the registry — the static-merge/refusal
        block, hoisted out of step()'s `compiled_vfs_profiles is not None` gate
        (comment-242 item 2) so the global and agent branches share one implementation.

        The evaluator chases in-profile dependencies of marked variables, so
        `updated_vfs` can contain a STATIC dependency, reported at its current runtime
        value (evaluator.py's add_with_deps; statics also enter vars_to_eval via
        history_spec). Statics are storage, not evaluation output: write back only
        expression variables, or a dependency chase silently clobbers an engine-written
        static every step (hamlet-df3a96bbac). An unknown variable id is a refusal
        (hamlet-0ddc83e377); agent-profile expressions must land [num_agents]-shaped.

        A global expression evaluates per world: one that reads a global or `tick`
        yields one value per world; one that reads only literals is world-invariant and
        yields a 0-d value, which is that same value in every world's row.
        """
        self._participation_ingress()
        expression_var_names = {var.name for var in profile.variables if var.ast is not None}
        for var_name, value in updated_vfs.items():
            if var_name not in expression_var_names:
                continue  # static: storage, never written back (hamlet-df3a96bbac)
            if var_name not in self.vfs_registry.variables:
                raise KeyError(
                    f"{profile_label} VFS write-back produced unknown variable id '{var_name}'.\n"
                    f"  Write source: {write_source} expression evaluation "
                    "(vfs_evaluator.evaluate_global_profile) (hamlet-0ddc83e377)."
                )
            if require_agent_shape and value.shape != (self.num_agents,):
                raise ValueError(
                    f"Agent-profile variable '{var_name}' evaluated to shape {tuple(value.shape)}, "
                    f"expected ({self.num_agents},). A constant belongs in initial_value, not an expression."
                )
            if not require_agent_shape and value.dim() == 0:
                value = value.expand(self.vfs_registry.num_worlds).clone()
            self.vfs_registry.set_engine_value(var_name, value)

    def _current_vfs_state(self) -> dict[str, torch.Tensor]:
        """Return the engine-readable VFS registry snapshot."""
        return {var_name: self.vfs_registry.get(var_name, reader="engine") for var_name in self.vfs_registry.variables.keys()}

    def _current_bar_state(self) -> dict[str, torch.Tensor]:
        """Return meter bars in the VTC expression namespace."""
        return {bar_name: self.meters[:, idx] for bar_name, idx in self.meter_name_to_index.items()}

    def _set_vtc_bar_value(self, bar_name: str, value: torch.Tensor) -> None:
        """Write a VTC-updated bar tensor back to the environment meters."""
        self._participation_ingress()
        meter_idx = self.meter_name_to_index[bar_name]
        expected = self.meters[:, meter_idx]
        if value.shape != expected.shape:
            raise ValueError(f"VTC action write for bar '{bar_name}' produced shape {tuple(value.shape)}, expected {tuple(expected.shape)}")
        self.meters[:, meter_idx] = value.to(device=self.device, dtype=expected.dtype)

    def _handle_interactions(self, interact_mask: torch.Tensor) -> dict:
        """Handle INTERACT actions with multi-tick accumulation."""
        self._participation_ingress()
        return self._action_executor._handle_interactions(interact_mask)

    def _handle_instant_interactions(self, interact_mask: torch.Tensor) -> dict:
        """Handle INTERACT action at affordances in instant mode."""
        self._participation_ingress()
        return self._action_executor._handle_instant_interactions(interact_mask)

    def _calculate_shaped_rewards(
        self,
        *,
        active_on_entry: torch.Tensor,
        intrinsic_context: IntrinsicTransitionContext,
        intrinsic_stamp: CuriosityStepStamp,
        accepted: WorldAcceptedEpisode,
    ) -> torch.Tensor:
        """Calculate canonical rewards for the exact accepted transition."""
        return self._reward_calculator._calculate_shaped_rewards(
            active_on_entry=active_on_entry,
            intrinsic_context=intrinsic_context,
            intrinsic_stamp=intrinsic_stamp,
            accepted=accepted,
        )

    def _get_affordance_positions(self) -> dict[str, torch.Tensor]:
        """Get current affordance positions as dict.

        Returns:
            Dictionary mapping affordance_id -> position tensor

        Note:
            Returns empty dict for Aspatial substrate.
            For spatial substrates, returns positions from substrate.
        """
        # For spatial substrates, return affordance positions
        if hasattr(self, "affordances") and self.affordances:
            return self.affordances
        return {}

    def _update_affordance_tracking(self, successful_interactions: dict[int, str]) -> None:
        """Update affordance tracking based on successful interactions.

        Args:
            successful_interactions: Dictionary mapping agent_idx -> affordance_name

        Updates:
            - _last_affordances: Last affordance per agent
            - _affordance_streaks: Consecutive interactions per affordance
            - _unique_affordances_count: Count of unique affordances per agent
            - _affordances_seen: Set of unique affordances per agent
        """
        self._participation_ingress()
        # Initialize streak tensors for all affordances if not present
        for affordance_name in self.affordances.keys():
            if affordance_name not in self._affordance_streaks:
                self._affordance_streaks[affordance_name] = torch.zeros(self.num_agents, dtype=torch.long, device=self.device)

        # Update tracking for each agent
        for agent_idx in range(self.num_agents):
            if agent_idx in successful_interactions:
                # Agent interacted with an affordance
                affordance_name = successful_interactions[agent_idx]

                # Update last affordance
                last_affordance = self._last_affordances[agent_idx]
                self._last_affordances[agent_idx] = affordance_name

                # Update streaks
                if last_affordance == affordance_name:
                    # Consecutive interaction with same affordance - increment streak
                    self._affordance_streaks[affordance_name][agent_idx] += 1
                else:
                    # Different affordance or first interaction - reset all streaks and start new one
                    for aff_name in self._affordance_streaks:
                        self._affordance_streaks[aff_name][agent_idx] = 0
                    self._affordance_streaks[affordance_name][agent_idx] = 1

                # Update unique affordance count
                if affordance_name not in self._affordances_seen[agent_idx]:
                    self._affordances_seen[agent_idx].add(affordance_name)
                    self._unique_affordances_count[agent_idx] += 1
            else:
                # Agent did not interact - reset last affordance but keep streaks and unique counts
                self._last_affordances[agent_idx] = None

    def _get_last_action_affordances(self) -> list[str | None]:
        """Get last affordance used by each agent.

        Returns:
            List of affordance IDs or None for each agent
        """
        if hasattr(self, "_last_affordances"):
            return self._last_affordances
        return [None] * self.num_agents

    def _get_affordance_streaks(self) -> dict[str, torch.Tensor]:
        """Get affordance streak counts per agent.

        Returns:
            Dictionary mapping affordance_id -> streak count tensor[num_agents]
        """
        if hasattr(self, "_affordance_streaks"):
            return self._affordance_streaks
        return {}

    def _get_unique_affordances_used(self) -> torch.Tensor:
        """Get count of unique affordances used by each agent.

        Returns:
            Tensor[num_agents] of unique affordance counts
        """
        if hasattr(self, "_unique_affordances_count"):
            return self._unique_affordances_count
        return torch.zeros(self.num_agents, device=self.device)

    @env_guard
    def get_affordance_positions(self) -> dict:
        """Get current affordance positions (substrate-agnostic checkpointing).

        Returns:
            Dictionary with 'positions', 'ordering', and 'position_dim' keys:
            - 'positions': Dict mapping affordance names to position lists
            - 'ordering': List of affordance names in consistent order
            - 'position_dim': Dimensionality for validation (0=aspatial, 2=2D, 3=3D)
        """
        self._participation_ingress()
        positions = {}
        for name, pos_tensor in self.affordances.items():
            # Convert tensor to list (handles any dimensionality)
            pos = pos_tensor.cpu().tolist()

            # Ensure pos is a list (even for 0-dimensional positions)
            if isinstance(pos, int | float):
                pos = [pos]
            elif self.substrate.position_dim == 0:
                pos = []

            positions[name] = list(pos) if pos else []

        return {
            "positions": positions,
            "ordering": list(self.affordances),
            "position_dim": self.substrate.position_dim,  # For validation
        }

    @env_guard
    def set_affordance_positions(self, checkpoint_data: dict) -> None:
        """Set affordance positions from checkpoint.

        Args:
            checkpoint_data: Dictionary with 'positions', 'ordering', and 'position_dim'

        Raises:
            ValueError: If the checkpoint layout or any position is invalid.
        """
        self._participation_ingress()
        validated_positions = self._validate_affordance_positions(checkpoint_data)
        self._native_layout_revision += 1
        for name in self.affordances:
            self.affordances[name] = validated_positions[name]
        self._affordance_layout_cache = None

    @env_guard
    def prepare_native_layout(self, state: dict, *, parent_plan: object) -> PreparedNativeLayout:
        """Materialize owned layout tensors before the native restore starts."""
        from townlet.population.vectorized import validate_native_population_data

        self._participation_ingress()
        validate_native_population_data(plan=parent_plan, owner=self)
        positions = self._validate_affordance_positions(state)
        prepared = object.__new__(PreparedNativeLayout)
        self._native_layout_preparations[prepared] = _NativeLayoutData(
            ref(parent_plan),
            os.getpid(),
            current_thread(),
            self._native_layout_revision,
            self._native_layout_revision + 1,
            self.affordances,
            tuple(positions.items()),
        )
        return prepared

    @env_guard
    def install_native_layout(self, *, prepared: object, parent_plan: object, attempt: object, restored: object) -> None:
        """Publish preallocated layout only inside this ENV's genuine finalizer."""
        from townlet.environment.restore_attempt import validate_restore_finalizer
        from townlet.population.vectorized import validate_native_population_data

        self._participation_ingress()
        validate_restore_finalizer(attempt=attempt, owner=self, restored=restored)
        validate_native_population_data(plan=parent_plan, owner=self)
        if type(prepared) is not PreparedNativeLayout:
            raise ValueError("native layout handle is foreign or unissued")
        data = self._native_layout_preparations.get(prepared)
        if (
            data is None
            or data.parent() is not parent_plan
            or data.pid != os.getpid()
            or data.thread is not current_thread()
            or data.revision != self._native_layout_revision
            or data.positions is not self.affordances
        ):
            raise ValueError("native layout preparation is stale, consumed or foreign")
        del self._native_layout_preparations[prepared]
        self._native_layout_revision = data.next_revision
        for name, tensor in data.assignments:
            self.affordances[name] = tensor
        self._affordance_layout_cache = None

    @env_guard
    def validate_affordance_positions(self, checkpoint_data: dict) -> dict[str, torch.Tensor]:
        return self._validate_affordance_positions(checkpoint_data)

    def _validate_affordance_positions(self, checkpoint_data: dict) -> dict[str, torch.Tensor]:
        """Validate checkpoint affordance positions without mutating environment state."""
        self._participation_ingress()
        expected_keys = {"positions", "ordering", "position_dim"}
        if type(checkpoint_data) is not dict or set(checkpoint_data) != expected_keys:
            raise ValueError(f"Affordance checkpoint keys must be exactly {sorted(expected_keys)}")

        checkpoint_position_dim = checkpoint_data["position_dim"]
        if type(checkpoint_position_dim) is not int:
            raise ValueError("Affordance checkpoint position_dim must be an integer")
        if checkpoint_position_dim != self.substrate.position_dim:
            raise ValueError(
                f"Checkpoint position_dim mismatch: checkpoint has {checkpoint_position_dim}D, "
                f"but current substrate requires {self.substrate.position_dim}D."
            )

        ordering = checkpoint_data["ordering"]
        if type(ordering) is not list or not all(type(name) is str for name in ordering):
            raise ValueError("Affordance checkpoint ordering must be a list of names")
        if len(ordering) != len(set(ordering)):
            raise ValueError("Affordance checkpoint ordering contains duplicates")
        deployed_names = list(self.affordances)
        if ordering != deployed_names:
            raise ValueError("Affordance checkpoint ordering must exactly match the current affordance ordering")

        positions = checkpoint_data["positions"]
        if type(positions) is not dict:
            raise ValueError("Affordance checkpoint positions must be a dictionary")
        if set(positions) != set(deployed_names):
            raise ValueError("Affordance checkpoint position names must exactly match the current affordance names")

        validated_positions: dict[str, torch.Tensor] = {}
        for name in ordering:
            position = positions[name]
            if type(position) is not list or len(position) != checkpoint_position_dim:
                raise ValueError(f"Affordance {name!r} coordinate sequence must contain exactly {checkpoint_position_dim} values")
            if any(isinstance(coordinate, bool) or not isinstance(coordinate, Real) for coordinate in position):
                raise ValueError(f"Affordance {name!r} coordinates must be numeric")
            if any(not math.isfinite(float(coordinate)) for coordinate in position):
                raise ValueError(f"Affordance {name!r} coordinates must be finite")
            if not self.substrate.position_dtype.is_floating_point and any(not float(coordinate).is_integer() for coordinate in position):
                raise ValueError(f"Affordance {name!r} coordinates must be integer-compatible")

            try:
                position_tensor = torch.tensor(position, device=self.device, dtype=self.substrate.position_dtype)
                normalized = self.substrate.normalize_positions(position_tensor.unsqueeze(0))
            except (OverflowError, RuntimeError, TypeError, ValueError) as exc:
                raise ValueError(f"Affordance {name!r} coordinates are invalid for the current substrate") from exc

            expected_shape = (1, checkpoint_position_dim)
            if tuple(normalized.shape) != expected_shape:
                raise ValueError(
                    f"Affordance {name!r} substrate position shape mismatch: expected {expected_shape}, got {tuple(normalized.shape)}"
                )
            if not bool(torch.isfinite(normalized).all()):
                raise ValueError(f"Affordance {name!r} coordinates are not finite in the current substrate dtype")
            if not bool(((normalized >= 0) & (normalized <= 1)).all()):
                raise ValueError(f"Affordance {name!r} coordinates are outside the current substrate bounds")

            validated_positions[name] = position_tensor

        return validated_positions

    @env_guard
    def randomize_affordance_positions(self) -> torch.Tensor | None:
        return self._randomize_affordance_positions()

    def _randomize_affordance_positions(self) -> torch.Tensor | None:
        """Randomize affordance positions and return agent spawn positions.

        Returns:
            Agent spawn positions [num_agents, position_dim], or None when the level does
            not randomize (or deploys no affordance).

        Placement follows owner ruling S1: the batch is N independent single-agent worlds
        sharing one affordance layout. Affordances take distinct cells; each world's one
        agent takes a cell no affordance holds. Agents of different worlds never meet, so
        they may share a cell. The compiler refuses a level whose substrate cannot hold
        its deployed affordances plus one agent (`GRID_CAPACITY_EXCEEDED`), so this never
        reads a declared position: under `randomize_affordances: true` none is consulted.
        """

        self._participation_ingress()
        if not self.randomize_affordances:
            return None

        if not self.affordances:
            return None

        self._native_layout_revision += 1
        # Aspatial universes have no coordinates; store empty tensors for consistency
        if self.substrate.position_dim == 0:
            empty = torch.zeros(0, dtype=self.substrate.position_dtype, device=self.device)
            for name in self.affordances.keys():
                self.affordances[name] = empty.clone()
            self._affordance_layout_cache = None
            # Return empty agent positions for aspatial
            return torch.zeros(self.num_agents, 0, dtype=self.substrate.position_dtype, device=self.device)

        affordance_count = len(self.affordances)
        capacity = self.substrate.get_capacity()

        if capacity is None:
            # Continuous: sample directly (infinite positions, collisions are measure-zero).
            sampled = self.substrate.initialize_positions(affordance_count + self.num_agents, self.device, generator=None)
            affordance_positions = sampled[:affordance_count]
            agent_positions = sampled[affordance_count:]
        else:
            if affordance_count + 1 > capacity:
                # The compiler refuses this per world (GRID_CAPACITY_EXCEEDED); reaching it means
                # the universe bypassed the compile.
                raise ValueError(f"Substrate capacity {capacity} cannot hold {affordance_count} affordance(s) plus one agent per world.")
            affordance_positions = self._sample_distinct_cells(affordance_count)
            agent_positions = self._sample_free_cells(self.num_agents, affordance_positions)

        for idx, name in enumerate(self.affordances.keys()):
            self.affordances[name] = affordance_positions[idx].clone()
        self._affordance_layout_cache = None

        return agent_positions

    def _sample_distinct_cells(self, count: int) -> torch.Tensor:
        """`count` pairwise-distinct cells of a finite substrate, drawn from torch's RNG only.

        Rejection sampling first; when retries are exhausted (a crowded substrate) the cells
        are drawn by a permutation of the enumerated positions. Never Python's `random`:
        placement must be reproducible from `seed_all` alone.
        """
        for _ in range(10):
            sampled = self.substrate.initialize_positions(count, self.device, generator=None)
            if len({tuple(row) for row in sampled.tolist()}) == count:
                return sampled
        all_positions = self.substrate.get_all_positions()
        perm = torch.randperm(len(all_positions))
        return torch.tensor(
            [all_positions[int(perm[idx])] for idx in range(count)], dtype=self.substrate.position_dtype, device=self.device
        )

    def _sample_free_cells(self, count: int, occupied: torch.Tensor) -> torch.Tensor:
        """One cell per world that no affordance holds; worlds are independent, so rows may repeat."""
        taken = {tuple(row) for row in occupied.tolist()}
        sampled = self.substrate.initialize_positions(count, self.device, generator=None)
        for _ in range(10):
            clashes = [index for index, row in enumerate(sampled.tolist()) if tuple(row) in taken]
            if not clashes:
                return sampled
            sampled[clashes] = self.substrate.initialize_positions(len(clashes), self.device, generator=None)
        clashes = [index for index, row in enumerate(sampled.tolist()) if tuple(row) in taken]
        if clashes:
            free = [position for position in self.substrate.get_all_positions() if tuple(position) not in taken]
            picks = torch.randint(0, len(free), (len(clashes),))
            sampled[clashes] = torch.tensor([free[int(pick)] for pick in picks], dtype=self.substrate.position_dtype, device=self.device)
        return sampled

    def _initialize_world_identity(
        self, roster: WorldRosterDeclaration, seed: int, lane_ids: tuple[str, ...], count: int, execution_identity: str
    ) -> None:
        if not isinstance(roster, WorldRosterDeclaration):
            raise ValueError("ENV requires an authored WorldRosterDeclaration")
        ids = exact_world_ids(lane_ids)
        exact_integer(count, 1, "world count")
        exact_integer(seed, 0, "training seed")
        if len(ids) != count or set(ids) != set(roster.world_ids):
            raise ValueError("lane binding must contain the exact declared roster")
        self._world_roster, self._world_seed, self._world_ids = roster, seed, ids
        self._world_identity = canonical_hash({"execution": execution_identity, "membership": roster.semantic_identity, "seed": seed})
        self._world_phase, self._world_generation = "fresh-unbound", 0
        self._world_revision = 0
        self._world_role_owners: Mapping[str, object] = {}
        self._world_frozen: WorldRecord | None = None
        self._world_cursors = dict.fromkeys(ids, 0)
        self._world_records: WeakValueDictionary[int, WorldRecord] = WeakValueDictionary()
        # Composition owns revocation/terminal transitions; the pure preparation
        # predicate must never grant currentness after either has been recorded.
        self._world_restore_revoked: WeakSet[WorldRecord] = WeakSet()
        self._world_restore_terminal = False
        self._world_restore_escrows: WeakKeyDictionary[WorldRecord, Any] = WeakKeyDictionary()
        self._world_restore_attempt: Any = None
        self._world_equal: dict[str, WorldRecord] = {}
        self._world_bindings: dict[int, dict[str, Any]] = {}
        self._world_authority: WorldBoundaryAuthority | None = None
        self._world_bootstrap: WorldRecord | None = None
        self._world_release: WorldRecord | None = None
        self._world_accepted: WorldAcceptedEpisode | None = None
        self._world_reset: WorldRecord | None = None
        self._world_reservation: WorldEpisodeReservation | None = None
        self._world_closure: WorldRecord | None = None
        self._world_last_closed: dict[str, Any] | None = None
        self._world_consumers: tuple[object, object] | None = None
        self._world_saved_binding: dict[str, Any] | None = None
        self._world_restored: tuple[WorldRecord, WorldRecord] | None = None
        self._world_vfs_pending: VFSWorldContext | None = None
        self._participation_busy = False
        self._participation_failed = False
        self._participation_pending: dict[str, Any] | None = None
        self._participation_committed: dict[str, Any] | None = None
        self._participation_reset_state: dict[str, Any] | None = None

    @property
    def world_ids(self) -> tuple[str, ...]:
        return self._world_ids

    @property
    @env_guard
    def accepted_episode_seqs(self) -> Mapping[str, int]:
        return MappingProxyType(dict(self._world_cursors))

    @env_guard
    def accepted_binding_batches(self) -> tuple[int, ...]:
        """Return actual retained history references at an installed boundary."""
        self._require_phase("bootstrap-ready", "released-completed")
        if self._world_release is None:
            raise ValueError("accepted history export requires its installed boundary release")
        self._require_release(self._world_release)
        return tuple(sorted(self._world_bindings))

    @property
    @env_guard
    def world_phase(self) -> str:
        return self._world_phase

    @property
    def semantic_execution_identity(self) -> str:
        return self._world_identity

    def _require_phase(self, *phases: str) -> None:
        self._participation_ingress()
        if self._world_phase not in phases:
            raise ValueError(f"operation is unavailable in world phase {self._world_phase}")

    def _record(self, kind: str, payload: Mapping[str, Any]) -> WorldRecord:
        result = WorldRecord(kind, self, self._world_generation, frozen_value(payload))
        self._world_records[id(result)] = result
        return result

    def _valid_record(self, record: Any, kind: str) -> None:
        if (
            not isinstance(record, WorldRecord)
            or record.kind != kind
            or record._owner is not self
            or record._generation != self._world_generation
            or self._world_records.get(id(record)) is not record
        ):
            raise ValueError("foreign, stale, changed or unissued world capability")

    def _equal_record(self, key: str, kind: str, payload: Mapping[str, Any]) -> WorldRecord:
        previous = self._world_equal.get(key)
        if previous is not None:
            if not same_value(previous.payload, payload):
                raise ValueError("changed content on a world operation retry")
            return previous
        result = self._record(kind, payload)
        self._world_equal[key] = result
        return result

    def _require_release(self, release: WorldRecord) -> None:
        self._valid_record(release, "release")
        if release is not self._world_release:
            raise ValueError("world operation requires the installed release")

    @env_guard
    def bind_boundary_authority(self, *, owner: object, role_owners: Mapping[str, object]) -> WorldBoundaryAuthority:
        self._participation_ingress()
        if not isinstance(role_owners, Mapping) or set(role_owners) != _WORLD_ROLES or any(value is None for value in role_owners.values()):
            raise ValueError("boundary authority requires every actual role owner")
        if self._world_authority is not None:
            if self._world_authority._owner is not owner or any(
                role_owners[key] is not self._world_role_owners[key] for key in _WORLD_ROLES
            ):
                raise ValueError("world boundary authority is already bound")
            return self._world_authority
        self._require_phase("fresh-unbound")
        self._world_authority = WorldBoundaryAuthority(self, owner)
        self._world_role_owners = MappingProxyType(dict(role_owners))
        self._world_phase = "fresh-bound"
        return self._world_authority

    @env_guard
    def install_boundary_release(self, release: WorldRecord) -> WorldRecord:
        self._participation_ingress()
        self._check_committed_participation()
        self._valid_record(release, "release")
        if release is self._world_release:
            self._require_phase("bootstrap-ready", "released-completed")
            return release
        if release.release_kind == "bootstrap":
            self._require_phase("fresh-bound")
            if release is not self._world_bootstrap:
                raise ValueError("unissued bootstrap")
            phase = "bootstrap-ready"
        elif release.release_kind == "completed":
            self._require_phase("closed-awaiting-release")
            if release.closure is not self._world_closure:
                raise ValueError("release does not match current closure")
            phase = "released-completed"
        else:
            raise ValueError("restored releases install only with their prepared restore")
        self._world_release, self._world_phase = release, phase
        return release

    @env_guard
    def prepare_episode(self, *, batch_episode: int, release: WorldRecord) -> WorldEpisodeReservation:
        return self._prepare_episode(batch_episode=batch_episode, release=release)

    def _prepare_episode(self, *, batch_episode: int, release: WorldRecord) -> WorldEpisodeReservation:
        self._require_phase("bootstrap-ready", "released-completed")
        self._check_committed_participation()
        self._require_release(release)
        exact_integer(batch_episode, 0, "batch episode")
        if batch_episode != release.next_batch_episode:
            raise ValueError("batch identity must be the released next batch")
        return WorldEpisodeReservation(
            self.world_ids,
            tuple(self._world_cursors[key] + 1 for key in self.world_ids),
            batch_episode,
            self,
            self._world_generation,
            release,
        )

    @env_guard
    def validate_episode_reservation(self, reservation: WorldEpisodeReservation) -> None:
        self._validate_episode_reservation(reservation)

    def _validate_episode_reservation(self, reservation: WorldEpisodeReservation) -> None:
        self._require_phase("bootstrap-ready", "released-completed")
        if not isinstance(reservation, WorldEpisodeReservation) or reservation._owner is not self:
            raise ValueError("reservation belongs to another world authority")
        if not isinstance(reservation.world_episode_seqs, tuple):
            raise ValueError("reservation sequences must be immutable")
        for sequence in reservation.world_episode_seqs:
            exact_integer(sequence, 1, "reserved sequence")
        self._require_release(reservation._release)
        expected = self._prepare_episode(batch_episode=reservation.batch_episode, release=reservation._release)
        if (
            reservation._generation != expected._generation
            or reservation.world_ids != expected.world_ids
            or reservation.world_episode_seqs != expected.world_episode_seqs
        ):
            raise ValueError("reservation identity or cursor disagrees")

    @env_guard
    def reset(self, *, reservation: WorldEpisodeReservation) -> WorldRecord:
        self._participation_ingress()
        self._check_committed_participation()
        previous = self._world_reservation
        duplicate = (
            isinstance(reservation, WorldEpisodeReservation)
            and previous is not None
            and type(reservation.batch_episode) is int
            and isinstance(reservation.world_episode_seqs, tuple)
            and all(type(sequence) is int for sequence in reservation.world_episode_seqs)
            and reservation._owner is previous._owner
            and reservation._generation == previous._generation
            and reservation._release is previous._release
            and reservation.batch_episode == previous.batch_episode
            and reservation.world_ids == previous.world_ids
            and reservation.world_episode_seqs == previous.world_episode_seqs
        )
        if self._world_reset is not None and duplicate:
            self._require_phase("active-awaiting-activation", "active", "closed-awaiting-release", "released-completed")
            return self._world_reset
        self._validate_episode_reservation(reservation)
        self._participation_pending = self._participation_committed = self._participation_reset_state = None
        self._participation_failed = False
        self._manual_close_prepared = None
        candidate = VFSWorldContext(
            training_seed=self._world_seed,
            world_ids=reservation.world_ids,
            world_episode_seqs=reservation.world_episode_seqs,
        )
        draws = VFSRandomness(context=candidate)
        self._world_phase = "resetting"
        try:
            # Project the exact candidate before any reset-time expression is evaluated.
            # Acceptance remains below; this provisional context grants no checkpoint right.
            self._world_vfs_pending = candidate
            self.vfs_randomness = draws
            observation = self._reset_world_state()
            generation = self._world_generation + 1
            accepted = WorldAcceptedEpisode(
                reservation.world_ids, reservation.world_episode_seqs, reservation.batch_episode, self, generation
            )
            binding = {
                "batch_episode": accepted.batch_episode,
                "world_ids": list(accepted.world_ids),
                "world_episode_seqs": list(accepted.world_episode_seqs),
            }
            self._world_generation = generation
            receipt = self._record("reset", {"accepted": accepted, "observation": observation})
            self._world_cursors = dict(zip(accepted.world_ids, accepted.world_episode_seqs, strict=True))
            self._world_bindings[accepted.batch_episode] = binding
            self._world_accepted, self._world_reset, self._world_reservation = accepted, receipt, reservation
            self._world_restored = None
            self._world_frozen = None
            self._world_equal = {}
            self._world_closure, self._world_release = None, None
            self._world_phase = "active-awaiting-activation"
            self._participation_reset_state = self._participation_state()
            return receipt
        except BaseException:
            self._world_phase = "quarantined"
            raise
        finally:
            self._world_vfs_pending = None

    def _accepted(self, accepted: WorldAcceptedEpisode) -> None:
        if accepted is not self._world_accepted or accepted is None:
            raise ValueError("accepted episode must be this ENV's current token")

    def validate_accepted_episode(self, *, accepted: WorldAcceptedEpisode) -> None:
        """Authenticate current token identity; callers retain their phase checks."""
        if self._world_restore_terminal:
            raise ValueError("receiver is terminal after failed restore composition")
        self._accepted(accepted)

    def _participation_ingress(self) -> None:
        """Synchronous cooperative fence, not an inter-thread lock."""
        if self._world_restore_terminal:
            raise ValueError("receiver is terminal after failed restore composition")
        if self._participation_busy or self._participation_pending is not None:
            raise ValueError("initial participation owns the current operation window")

    def _finish_restore_attempt_failure(self, attempt: Any) -> None:
        from townlet.environment.restore_attempt import finish_restore_failure

        finish_restore_failure(env=self, attempt=attempt)

    def _participation_state(self) -> dict[str, Any]:
        """Own finite ENV state; builtin read purity covers unencoded manager state.

        No simulator export/evaluation or guessed item/effect/history schema is used.
        The supported mask/encoder graph reads those managers without mutation under
        fixed builtin configuration and single-owner quiescence.
        """
        names = (
            "positions",
            "_velocity",
            "meters",
            "dones",
            "step_counts",
            "intrinsic_weights",
            "interaction_progress",
            "last_interaction_position",
            "_unique_affordances_count",
        )
        state: dict[str, Any] = {
            "tensors": {name: getattr(self, name) for name in names},
            "tick": self.global_tick,
            "hour": self.time_of_day,
            "affordances": self.affordances,
            "layout": self._affordance_layout_cache,
            "last_interaction": self.last_interaction_affordance,
            "last_affordances": self._last_affordances,
            "streaks": self._affordance_streaks,
            "seen": tuple(tuple(sorted(values)) for values in self._affordances_seen),
            "vfs": self._current_vfs_state(),
        }
        return {key: owned_value(value) for key, value in state.items()}

    def _quarantine_participation(self) -> None:
        self._participation_pending = None
        self._participation_failed = True
        self._world_phase = "quarantined"

    def _check_participation_state(self, expected: Mapping[str, Any]) -> None:
        if not same_value(expected, self._participation_state()):
            self._quarantine_participation()
            raise ValueError("initial participation physical/status evidence changed")

    def _invalidate_participation(self, expected: Mapping[str, Any] | None) -> None:
        self._participation_pending = None
        if expected is not None:
            try:
                self._check_participation_state(expected)
            except BaseException:
                # A failed read cannot certify a healthy replacement preparation.
                self._quarantine_participation()

    def _participation_reading(self, value: Any, *, width: int, dtype: torch.dtype) -> None:
        shape = (self.num_agents, width)
        if (
            not isinstance(value, torch.Tensor)
            or value.layout != torch.strided
            or value.shape != shape
            or value.dtype != dtype
            or value.device != self.device
            or (dtype == torch.float32 and not bool(torch.isfinite(value).all()))
        ):
            raise ValueError("initial participation reading has invalid geometry, dtype or device")

    def _initial_participation_window(self, accepted: WorldAcceptedEpisode) -> None:
        self._accepted(accepted)
        if (
            self._world_phase != "active-awaiting-activation"
            or self._participation_failed
            or self._world_reset is None
            or self._world_reservation is None
            or self._participation_reset_state is None
            or self._world_frozen is not None
            or self._participation_committed is not None
            or "activation" in self._world_equal
        ):
            raise ValueError("initial participation requires an unactivated genuine reset")

    @env_guard
    def prepare_initial_participation(self, *, accepted: WorldAcceptedEpisode, intent: WorldOwnerReceipt) -> WorldRecord:
        """Stage an owner-issued pre-first-transition retirement without publishing it."""
        try:
            return self._prepare_initial_participation(accepted=accepted, intent=intent)
        except ValueError:
            raise  # Pure input refusals precede the guarded staging work below.
        except BaseException:
            self._invalidate_participation(self._participation_reset_state)
            raise

    def _prepare_initial_participation(self, *, accepted: WorldAcceptedEpisode, intent: WorldOwnerReceipt) -> WorldRecord:
        if self._participation_busy:
            raise ValueError("initial participation cannot reenter")
        self._initial_participation_window(accepted)
        proof = WorldReceiptIssuer.validate(intent, "initial_participation_intent", self._world_role_owners["population"])
        fields = proof.payload
        if set(fields) != {"accepted", "world_ids", "retired_world_ids", "population_revision"}:
            raise ValueError("initial participation intent requires exact fields")
        retired = fields["retired_world_ids"]
        if (
            fields["accepted"] is not accepted
            or type(fields["world_ids"]) is not tuple
            or fields["world_ids"] != self.world_ids
            or type(retired) is not tuple
            or any(type(key) is not str or not key for key in retired)
            or len(set(retired)) != len(retired)
            or tuple(key for key in self.world_ids if key in retired) != retired
        ):
            raise ValueError("initial participation intent identity or ordered subset disagrees")
        revision = exact_integer(fields["population_revision"], 0, "population revision")
        previous = self._participation_pending
        if previous is not None and previous["intent"] is not intent:
            raise ValueError("another initial participation intent is retained")
        reset_state, reset_record = self._participation_reset_state, self._world_reset
        assert reset_state is not None and reset_record is not None
        self._participation_busy = True
        try:
            if previous is not None:
                self._check_initial_preparation(previous)
                retained = previous["prepared"]
                if not isinstance(retained, WorldRecord):
                    raise ValueError("retained initial participation preparation is invalid")
                self._valid_record(retained, "prepared_initial_participation")
                return retained
            self._check_participation_state(reset_state)
            if self.global_tick != 0 or bool(self.step_counts.any()) or bool(self.dones.any()):
                self._quarantine_participation()
                raise ValueError("initial participation requires pristine reset activity and counts")
            observation = self._encode_observations().detach().clone()
            self._check_participation_state(reset_state)
            self._participation_reading(observation, width=self.observation_dim, dtype=torch.float32)
            if not same_value(observation, reset_record.observation):
                self._quarantine_participation()
                raise ValueError("initial participation reset observation changed")
            before = self._participation_state()
            # One genuine fixed-reset legal mask. Dones is read only at the builtin
            # builder's final clearing step, so derive retirement without a callback.
            legal = self._build_action_masks()
            self._check_participation_state(before)
            self._participation_reading(legal, width=self.action_dim, dtype=torch.bool)
            candidate_mask = legal.detach().clone()
            candidate_dones = torch.tensor([key in retired for key in self.world_ids], dtype=torch.bool, device=self.device)
            candidate_mask[candidate_dones] = False
            if bool((~candidate_dones & ~candidate_mask.any(dim=1)).any()):
                raise ValueError("initial participation leaves a live world without a legal action")
            self._check_participation_state(before)
            self._initial_participation_window(accepted)
            candidate_state = owned_value(before)
            candidate_state["tensors"]["dones"] = candidate_dones.detach().clone()
            prepared = self._record(
                "prepared_initial_participation",
                {
                    "accepted": accepted,
                    "intent": intent,
                    "retired_world_ids": retired,
                    "observation": observation,
                    "action_masks": candidate_mask,
                },
            )
            self._participation_pending = {
                "prepared": prepared,
                "accepted": accepted,
                "intent": intent,
                "reset": self._world_reset,
                "reservation": self._world_reservation,
                "generation": self._world_generation,
                "revision": self._world_revision,
                "population_revision": revision,
                "retired": retired,
                "before": before,
                "candidate_state": candidate_state,
                "observation": observation,
                "mask": candidate_mask,
                "dones": candidate_dones,
            }
            return prepared
        except BaseException:
            self._invalidate_participation(self._participation_reset_state)
            raise
        finally:
            self._participation_busy = False

    def _check_initial_preparation(self, pending: Mapping[str, Any]) -> None:
        self._initial_participation_window(pending["accepted"])
        if (
            pending["reset"] is not self._world_reset
            or pending["reservation"] is not self._world_reservation
            or pending["generation"] != self._world_generation
            or pending["revision"] != self._world_revision
        ):
            raise ValueError("initial participation preparation is stale")
        self._check_participation_state(pending["before"])

    @env_guard
    def commit_initial_participation(self, *, prepared: WorldRecord, population_ready: WorldOwnerReceipt) -> WorldRecord:
        """Publish a single staged decision; every fallible operation precedes dones."""
        try:
            return self._commit_initial_participation(prepared=prepared, population_ready=population_ready)
        except ValueError:
            raise  # Exact input refusals leave existing healthy pending custody.
        except BaseException:
            pending = self._participation_pending
            if pending is not None:
                self._invalidate_participation(pending["before"])
            raise

    def _commit_initial_participation(self, *, prepared: WorldRecord, population_ready: WorldOwnerReceipt) -> WorldRecord:
        if self._participation_busy:
            raise ValueError("initial participation cannot reenter")
        self._valid_record(prepared, "prepared_initial_participation")
        pending = self._participation_pending
        if pending is None or pending["prepared"] is not prepared:
            raise ValueError("initial participation preparation is not pending")
        self._initial_participation_window(pending["accepted"])
        proof = WorldReceiptIssuer.validate(population_ready, "initial_participation_ready", self._world_role_owners["population"])
        fields = proof.payload
        if set(fields) != {"accepted", "intent", "prepared", "population_revision"}:
            raise ValueError("initial participation ready requires exact fields")
        exact_integer(fields["population_revision"], 0, "population revision")
        if (
            fields["accepted"] is not pending["accepted"]
            or fields["intent"] is not pending["intent"]
            or fields["prepared"] is not prepared
            or fields["population_revision"] != pending["population_revision"]
        ):
            raise ValueError("initial participation ready disagrees with retained preparation")
        self._participation_busy = True
        publishing = False
        try:
            self._check_initial_preparation(pending)
            observation = self._encode_observations()
            self._participation_reading(observation, width=self.observation_dim, dtype=torch.float32)
            if not same_value(observation, pending["observation"]):
                self._quarantine_participation()
                raise ValueError("initial participation physical observation changed")
            self._check_participation_state(pending["before"])
            self._check_initial_preparation(pending)
            self._participation_reading(pending["mask"], width=self.action_dim, dtype=torch.bool)
            if (
                bool(pending["mask"][pending["dones"]].any())
                or bool((~pending["dones"] & ~pending["mask"].any(dim=1)).any())
                or not same_value(pending["candidate_state"]["tensors"]["dones"], pending["dones"])
            ):
                raise ValueError("initial participation candidate changed")
            revision = self._world_revision + 1
            result = self._record(
                "initial_participation",
                {
                    "accepted": pending["accepted"],
                    "retired_world_ids": pending["retired"],
                    "observation": pending["observation"],
                    "action_masks": pending["mask"],
                },
            )
            committed = {
                "result": result,
                "accepted": pending["accepted"],
                "reset": pending["reset"],
                "generation": self._world_generation,
                "revision": revision,
                "retired": pending["dones"].detach().clone(),
                "state": pending["candidate_state"],
                "observation": pending["observation"],
            }
            candidate_dones = pending["dones"]
            self._check_initial_preparation(pending)
            # No property read, clone, issuer, callback or allocation after this cut.
            publishing = True
            self.dones = candidate_dones
            self._participation_committed = committed
            self._participation_pending = None
            self._world_revision = revision
            return result
        except BaseException:
            if publishing:
                self._quarantine_participation()
            else:
                self._invalidate_participation(pending["before"])
            raise
        finally:
            self._participation_busy = False

    def _check_participation_custody(self, committed: Mapping[str, Any], *, phase: str) -> None:
        if (
            phase not in ("active-awaiting-activation", "active", "boundary-pending", "closed-awaiting-release", "released-completed")
            or self._world_phase != phase
            or self._participation_failed
            or self._participation_pending is not None
            or self._participation_committed is not committed
            or committed["accepted"] is not self._world_accepted
            or committed["reset"] is not self._world_reset
            or committed["generation"] != self._world_generation
            or committed["revision"] != self._world_revision
        ):
            self._quarantine_participation()
            raise ValueError("initial participation lifecycle custody is stale or failed")
        self._valid_record(committed["result"], "initial_participation")

    def _check_committed_participation(self) -> None:
        committed = self._participation_committed
        if committed is None:
            return
        phase = self._world_phase
        previous_busy = self._participation_busy
        self._participation_busy = True
        try:
            self._check_participation_custody(committed, phase=phase)
            self._check_participation_state(committed["state"])
            retired = committed["retired"]
            if bool((~self.dones[retired]).any()) or bool(self.step_counts[retired].any()):
                self._quarantine_participation()
                raise ValueError("a sealed retired world cannot participate")
            observation = self._encode_observations()
            self._participation_reading(observation, width=self.observation_dim, dtype=torch.float32)
            self._check_participation_state(committed["state"])
            if not same_value(observation, committed["observation"]):
                self._quarantine_participation()
                raise ValueError("sealed current physical observation changed")
            # Encoding/state reads may return unchanged bytes after legitimate
            # abandonment. Physical equality never reinstates lifecycle authority.
            self._check_participation_custody(committed, phase=phase)
        finally:
            self._participation_busy = previous_busy

    def _advance_participation_witness(self, observation: torch.Tensor) -> None:
        committed = self._participation_committed
        if committed is not None:
            retired = committed["retired"]
            if bool((~self.dones[retired]).any()) or bool(self.step_counts[retired].any()):
                self._quarantine_participation()
                raise ValueError("a genuine step contradicted sealed retirement")
            state = self._participation_state()
            reading = observation.detach().clone()
            committed["state"], committed["observation"], committed["revision"] = state, reading, self._world_revision

    @env_guard
    def validate_initial_participation(
        self, *, accepted: WorldAcceptedEpisode, participation: WorldRecord, predecessor: torch.Tensor
    ) -> None:
        """Authenticate current sealed activity/physical reading before parent effects."""
        self._require_phase("active")
        self._validate_participation_reading(accepted=accepted, participation=participation, predecessor=predecessor)

    @env_guard
    def validate_initial_participation_reading(
        self, *, accepted: WorldAcceptedEpisode, participation: WorldRecord, predecessor: torch.Tensor
    ) -> None:
        """Validate retained observation custody for a query, without opening physics."""
        self._require_phase("active-awaiting-activation", "active", "closed-awaiting-release", "released-completed")
        self._validate_participation_reading(accepted=accepted, participation=participation, predecessor=predecessor)

    def _validate_participation_reading(
        self, *, accepted: WorldAcceptedEpisode, participation: WorldRecord, predecessor: torch.Tensor
    ) -> None:
        """Shared non-issuing read; public wrappers retain their fixed phase policies."""
        self._accepted(accepted)
        self._valid_record(participation, "initial_participation")
        committed = self._participation_committed
        if committed is None or committed["result"] is not participation or committed["accepted"] is not accepted:
            raise ValueError("initial participation requires the exact committed decision")
        self._participation_reading(predecessor, width=self.observation_dim, dtype=torch.float32)
        self._participation_busy = True
        try:
            self._check_committed_participation()
            if not same_value(committed["observation"], predecessor):
                raise ValueError("initial participation predecessor disagrees with current physical reading")
        finally:
            self._participation_busy = False

    @env_guard
    def activate_episode(
        self, *, accepted: WorldAcceptedEpisode, population_receipt: WorldOwnerReceipt, curiosity_receipt: WorldOwnerReceipt
    ) -> WorldRecord:
        self._require_phase("active-awaiting-activation", "active")
        self._accepted(accepted)
        self._check_committed_participation()
        for role, receipt in (("population", population_receipt), ("curiosity", curiosity_receipt)):
            WorldReceiptIssuer.validate(receipt, "activation", self._world_role_owners[role])
            if set(receipt.payload) != {"accepted"} or receipt.accepted is not accepted:
                raise ValueError("activation receipt identity disagrees")
        owners = (population_receipt.owner, curiosity_receipt.owner)
        if self._world_consumers is not None and any(a is not b for a, b in zip(owners, self._world_consumers, strict=True)):
            raise ValueError("episode consumers cannot change inside an ENV")
        result = self._equal_record(
            "activation", "activation", {"accepted": accepted, "population": population_receipt, "curiosity": curiosity_receipt}
        )
        self._world_consumers, self._world_phase = owners, "active"
        return result

    @env_guard
    def prepare_episode_close(
        self,
        *,
        accepted: WorldAcceptedEpisode,
        boundary_key: int,
        completion_content: Any,
        participated_world_ids: tuple[str, ...],
        dispositions: WorldOwnerReceipt,
    ) -> WorldRecord:
        self._require_phase("active", "closed-awaiting-release", "released-completed")
        self._accepted(accepted)
        self._check_committed_participation()
        if self._manual_session is not None and self._world_phase == "active":
            self._manual_session._check()
            self._manual_session._current(accepted)
        exact_integer(boundary_key, 0, "boundary key")
        participants = exact_world_ids(participated_world_ids)
        actual = {key for index, key in enumerate(self.world_ids) if int(self.step_counts[index]) > 0}
        if boundary_key != accepted.batch_episode or set(participants) != actual:
            raise ValueError("closure requires exactly the genuinely participated worlds")
        if self._world_consumers is None:
            raise ValueError("closure requires activated consumers")
        proof = WorldReceiptIssuer.validate(dispositions, "prepared_dispositions", self._world_consumers[1])
        if set(proof.payload) != {"accepted", "boundary_key", "completion_content", "participated_world_ids", "dispositions"}:
            raise ValueError("disposition receipt requires complete fields")
        exact_integer(proof.boundary_key, 0, "disposition boundary")
        expected = tuple((key, "completed" if key in actual else "retired_nonparticipating") for key in self.world_ids)
        if (
            proof.accepted is not accepted
            or proof.boundary_key != boundary_key
            or tuple(proof.participated_world_ids) != participants
            or not same_value(proof.completion_content, completion_content)
            or proof.dispositions != expected
        ):
            raise ValueError("committed dispositions disagree with the accepted episode")
        payload = {
            "accepted": accepted,
            "boundary_key": boundary_key,
            "completion_content": completion_content,
            "participated_world_ids": participants,
            "dispositions": dispositions,
            "revision": self._world_revision,
        }
        result = self._record("prepared_close", payload)
        if self._manual_session is not None:
            self._manual_close_prepared = result
        return result

    @env_guard
    def freeze_episode_close(self, prepared: WorldRecord) -> WorldRecord:
        self._require_phase("active", "boundary-pending", "closed-awaiting-release", "released-completed")
        self._check_committed_participation()
        self._valid_record(prepared, "prepared_close")
        self._accepted(prepared.accepted)
        if prepared.revision != self._world_revision or (self._world_frozen is not None and self._world_frozen is not prepared):
            raise ValueError("closure preparation is stale or another boundary is frozen")
        if self._world_frozen is prepared:
            return prepared
        self._world_frozen, self._world_phase = prepared, "boundary-pending"
        return prepared

    @env_guard
    def close_episode(self, prepared: WorldRecord, *, dispositions: WorldOwnerReceipt) -> WorldRecord:
        self._require_phase("boundary-pending", "closed-awaiting-release", "released-completed")
        self._check_committed_participation()
        self._valid_record(prepared, "prepared_close")
        if prepared is not self._world_frozen or prepared.revision != self._world_revision:
            raise ValueError("closure requires the frozen current preparation")
        WorldReceiptIssuer.validate(dispositions, "dispositions", self._world_role_owners["curiosity"])
        if not same_value(dispositions.payload, prepared.dispositions.payload):
            raise ValueError("committed bank disposition disagrees with prepared content")
        closure = self._equal_record("closure", "closure", {**prepared.payload, "dispositions": dispositions})
        if self._world_closure is not None:
            return closure
        accepted = prepared.accepted
        last = {
            "batch_episode": accepted.batch_episode,
            "world_ids": list(accepted.world_ids),
            "world_episode_seqs": list(accepted.world_episode_seqs),
            "completion_content": owned_value(prepared.completion_content),
            "participated_world_ids": list(prepared.participated_world_ids),
        }
        self._world_last_closed, self._world_saved_binding = last, world_binding(accepted.world_ids)
        self._world_closure, self._world_phase = closure, "closed-awaiting-release"
        return closure

    @env_guard
    def abandon_episode(self, *, accepted: WorldAcceptedEpisode, reason: str) -> WorldRecord:
        return self._abandon_episode(accepted=accepted, reason=reason)

    def _abandon_episode(self, *, accepted: WorldAcceptedEpisode, reason: str) -> WorldRecord:
        """ENV-owned cleanup also used beneath the original manual operation guard."""
        self._accepted(accepted)
        if reason == "runtime_failure" and accepted is self._world_accepted:
            # Fail-closed owner cleanup must work even while public entry is fenced.
            if self._participation_busy or self._participation_pending is not None or self._participation_failed:
                self._quarantine_participation()
                return self._equal_record("abandonment", "abandonment", {"accepted": accepted, "reason": reason})
        else:
            self._participation_ingress()
        if reason not in ("empty_participation", "runtime_failure"):
            raise ValueError("unknown episode abandonment reason")
        if self._world_phase == "quarantined":
            previous = self._world_equal.get("abandonment")
            if previous is None or previous.reason != reason:
                raise ValueError("different failed attempt cannot be retried")
            return previous
        self._require_phase("active", "active-awaiting-activation")
        if reason == "empty_participation":
            self._check_committed_participation()
            if bool((self.step_counts > 0).any()) or self._world_consumers is None:
                raise ValueError("empty abandonment requires activated empty owners")
            for owner in self._world_consumers:
                method = getattr(owner, "prepare_empty_episode_evidence", None)
                if not callable(method):
                    raise ValueError("owner lacks the required empty-episode proof")
                proof = self._env_custody.outcall("empty", method, owner=owner, accepted=accepted)
                evidence = WorldReceiptIssuer.validate(proof, "empty_episode", owner)
                if set(evidence.payload) != {"accepted", "participated_world_ids", "events"} or evidence.accepted is not accepted:
                    raise ValueError("empty-episode proof identity disagrees")
                if evidence.participated_world_ids or evidence.events:
                    raise ValueError("episode has participating owner state")
        result = self._equal_record("abandonment", "abandonment", {"accepted": accepted, "reason": reason})
        self._world_phase = "quarantined"
        return result

    @env_guard
    def checkpoint_world_state(
        self, *, kind: str, release: WorldRecord, retained_binding_batches: tuple[int, ...], initial: WorldRecord | None
    ) -> dict[str, Any]:
        self._require_release(release)
        self._participation_ingress()
        self._check_committed_participation()
        if not isinstance(retained_binding_batches, tuple):
            raise ValueError("retained history references require a tuple")
        for batch in retained_binding_batches:
            exact_integer(batch, 0, "retained batch")
        if tuple(sorted(set(retained_binding_batches))) != retained_binding_batches:
            raise ValueError("retained batch references must be sorted and unique")
        if kind == "INITIAL":
            self._require_phase("bootstrap-ready")
            self._valid_record(initial, "initial_snapshot")
            assert isinstance(initial, WorldRecord)
            if initial.release is not release or retained_binding_batches or any(self._world_cursors.values()) or self._world_bindings:
                raise ValueError("INITIAL requires pristine bootstrap and no accepted history")
        elif kind == "COMPLETED":
            self._require_phase("released-completed")
            if (
                initial is not None
                or self._world_last_closed is None
                or self._world_last_closed["batch_episode"] not in retained_binding_batches
            ):
                raise ValueError("completed snapshots require current closure provenance")
        else:
            raise ValueError("snapshot kind must be explicit INITIAL or COMPLETED")
        if any(batch not in self._world_bindings for batch in retained_binding_batches):
            raise ValueError("missing retained accepted-binding provenance")
        return {
            "schema": "world-lifecycle-v4",
            "kind": kind,
            "next_batch_episode": release.next_batch_episode,
            "world_roster": self._world_roster.to_dict(),
            "manifest_digest": self._world_roster.manifest_digest,
            "roster_semantic_identity": self._world_roster.semantic_identity,
            "training_seed": self._world_seed,
            "execution_identity": self.semantic_execution_identity,
            "saved_lane_binding": owned_value(self._world_saved_binding),
            "destination_lane_binding": world_binding(self.world_ids),
            "accepted_episode_seqs": dict(self._world_cursors),
            "last_closed_episode": owned_value(self._world_last_closed),
            "completed_boundary_key": None if self._world_last_closed is None else self._world_last_closed["batch_episode"],
            "accepted_bindings": [owned_value(self._world_bindings[batch]) for batch in retained_binding_batches],
            "vfs_random_context": self._vfs_random_state(),
        }

    @env_guard
    def prepare_world_restore(
        self,
        *,
        kind: str,
        state: Mapping[str, Any],
        world_roster: WorldRosterDeclaration,
        destination_world_ids: tuple[str, ...],
        semantic_execution_identity: str,
    ) -> WorldRecord:
        self._require_phase("fresh-bound")
        if not isinstance(world_roster, WorldRosterDeclaration) or world_roster.to_dict() != self._world_roster.to_dict():
            raise ValueError("restore must preserve the original authored roster manifest")
        destination = exact_world_ids(destination_world_ids)
        if set(destination) != set(self.world_ids) or destination != self.world_ids:
            raise ValueError("restore destination must be the fresh ENV's actual binding")
        if semantic_execution_identity != self.semantic_execution_identity:
            raise ValueError("restore destination semantic identity disagrees")
        prepared = validate_world_snapshot(state, kind, world_roster, self._world_seed, semantic_execution_identity)
        # Validate saved producer order first, then explicitly project to this destination.
        context = VFSWorldContext(
            training_seed=self._world_seed,
            world_ids=destination,
            world_episode_seqs=tuple(prepared["accepted_episode_seqs"][world_id] for world_id in destination),
        )
        record = self._record(
            "prepared_restore",
            {
                "state": prepared,
                "destination_world_ids": destination,
                "destination_vfs_context": VFSRandomness(context=context).state(),
            },
        )
        self._env_custody._seal_prepared_restore(record)
        return record

    @env_guard
    def install_world_restore(self, *, prepared: WorldRecord, release: WorldRecord) -> WorldRecord:
        from townlet.environment.restore_attempt import consume_restore_route

        consume_restore_route(env=self, prepared=prepared, route="world")
        if self._world_restored is not None and self._world_restored == (prepared, release):
            self._require_phase("bootstrap-ready", "released-completed")
            assert self._world_release is not None
            return self._world_release
        self._require_phase("fresh-bound")
        self._valid_record(prepared, "prepared_restore")
        self._valid_record(release, "release")
        if release.release_kind != "restored" or release.restore is not prepared:
            raise ValueError("restore release does not name this preparation")
        state = prepared.state
        expected = VFSWorldContext(
            training_seed=self._world_seed,
            world_ids=self.world_ids,
            world_episode_seqs=tuple(state["accepted_episode_seqs"][world_id] for world_id in self.world_ids),
        )
        context = VFSRandomness.validate_state(prepared.destination_vfs_context, expected=expected)
        draws = VFSRandomness(context=context)
        self._world_phase = "restoring"
        try:
            self._world_generation += 1
            self._participation_pending = self._participation_committed = self._participation_reset_state = None
            self._participation_failed = False
            self._manual_close_prepared = None
            self._world_cursors = dict(state["accepted_episode_seqs"])
            self._world_bindings = {item["batch_episode"]: owned_value(item) for item in state["accepted_bindings"]}
            self._world_last_closed = owned_value(state["last_closed_episode"])
            self._world_saved_binding = owned_value(state["saved_lane_binding"])
            self.vfs_randomness = draws
            if state["kind"] == "INITIAL":
                installed = self._record("release", {"release_kind": "bootstrap", "next_batch_episode": state["next_batch_episode"]})
                self._world_bootstrap = installed
                phase = "bootstrap-ready"
            else:
                last = self._world_last_closed
                assert last is not None
                self._world_accepted = WorldAcceptedEpisode(
                    tuple(last["world_ids"]),
                    tuple(last["world_episode_seqs"]),
                    last["batch_episode"],
                    self,
                    self._world_generation,
                )
                self._world_closure = self._record("restored_closure", {"semantic_state": last})
                installed = self._record("release", {"release_kind": "completed", "next_batch_episode": state["next_batch_episode"]})
                phase = "released-completed"
            self._world_release = installed
            self._world_restored = (prepared, release)
            self._world_phase = phase
            return installed
        except BaseException:
            self._world_phase = "quarantined"
            raise
