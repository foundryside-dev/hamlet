"""
Vectorized Hamlet environment for GPU-native training.

Batches multiple independent Hamlet environments into a single vectorized
environment with tensor operations [num_agents, ...].
"""

from __future__ import annotations

from numbers import Number
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import torch

from townlet.environment import env_factory
from townlet.environment.action_builder import ComposedActionSpace
from townlet.environment.action_config import ActionConfig
from townlet.environment.action_executor import ActionExecutor
from townlet.environment.action_labels import ActionLabels
from townlet.environment.action_mask_builder import ActionMaskBuilder
from townlet.environment.affordance_engine import AffordanceEngine
from townlet.environment.dac_engine import DACEngine
from townlet.environment.observation_encoder import ObservationEncoder
from townlet.environment.reward_calculator import RewardCalculator
from townlet.items import InventoryState, ItemActionHandler, ItemManager
from townlet.substrate.continuous import ContinuousSubstrate
from townlet.universe.dto import RuntimeActionSpace
from townlet.vfs.evaluator import EvaluationMode, VFSEvaluator
from townlet.vfs.observation_builder import VFSObservationSpec
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
    from townlet.exploration.base import ExplorationStrategy
    from townlet.population.runtime_registry import AgentRuntimeRegistry
    from townlet.universe.compiled import CompiledUniverse
    from townlet.vfs.schema import VariableDef


# Import consolidated NullItemManager (ENV-009)
from townlet.environment.null_managers import NullItemManager


class VectorizedHamletEnv:
    """
    GPU-native vectorized Hamlet environment.

    Batches multiple independent environments for parallel execution.
    All state is stored as PyTorch tensors on specified device.
    """

    EFFECT_OBS_SLOTS = 8  # Fixed number of observable effect slots per agent

    runtime_registry: AgentRuntimeRegistry | None

    def __init__(
        self,
        *,
        universe: CompiledUniverse,
        level_name: str,
        num_agents: int,
        device: torch.device | str,
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
        self._observation_encoder = ObservationEncoder(self)
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
        self.observation_activity = level.observation_activity
        # Use level-specific observation spec so non-primary levels
        # (e.g., POMDP vs full observability) get correct shapes.
        self.observation_spec = level.observation_spec

        # grid_size is the SQUARE display size legacy consumers expect; the
        # metadata compiler derives it from the substrate instance (None for
        # non-square and non-grid substrates). Nothing shape-bearing reads it
        # any more — boundary masking asks the substrate per axis and the
        # vision window asks the substrate directly (WS-7 first knockdown;
        # the non-square guard that used to live here was DIV-003's third
        # registered crash).
        self.grid_size = self.metadata.grid_size

        # Observation/model metadata
        self.meter_count = self.metadata.meter_count
        meter_count = self.meter_count

        # POMDP support and vision-window sizing live in a single helper so
        # the env body reads as orchestration, not validation. The helper
        # writes to vision_radius and local_window_size on self.
        self.vision_radius: int = 0
        self.local_window_size: int = 0
        self._configure_partial_observability()

        # Observation dimension is derived from the level-specific spec.
        self.observation_dim = self.observation_spec.total_dims

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
        self.affordance_overrides: dict[str, bool] = {}
        self.effect_manager = (
            EffectManager(
                catalog=effect_catalog,
                command_executor=self.command_executor,
                device=str(self.device),
                time_enabled=self.temporal_support_enabled,
                affordance_overrides=self.affordance_overrides,
            )
            if effect_catalog is not None
            else None
        )
        self.effect_observation_slots = getattr(universe, "effect_observation_slots", self.EFFECT_OBS_SLOTS)

        if universe.effects_schema is None:
            raise ValueError("Compiled universe is missing effects_schema. Recompile the config pack before creating an environment.")
        self.effects_schema = dict(universe.effects_schema)

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
        self.vtc_reward_program: VTCRewardProgram = self.vtc_transition_schedule.reward_component_program

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

        # Exploration module (optional, set by population or external code)
        self.exploration_module: ExplorationStrategy | None = None

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
        if self.randomize_affordances:
            self.randomize_affordance_positions()
        else:
            self._apply_configured_affordance_positions()

    def attach_runtime_registry(self, registry: AgentRuntimeRegistry) -> None:
        """Attach runtime registry for telemetry tracking."""
        self.runtime_registry = registry

    def set_exploration_module(self, exploration: ExplorationStrategy) -> None:
        """Set exploration module for intrinsic reward computation.

        Args:
            exploration: Exploration strategy (RND, ICM, epsilon-greedy, etc.)

        Note:
            This is typically called by VectorizedPopulation during initialization,
            but can also be set manually for testing or custom training loops.
        """
        self.exploration_module = exploration

    def _apply_configured_affordance_positions(self) -> None:
        """Load static affordance positions from config/optimization data."""

        if self.substrate.position_dim == 0:
            empty = torch.zeros(0, dtype=self.substrate.position_dtype, device=self.device)
            for name in self.affordances.keys():
                self.affordances[name] = empty.clone()
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

    def _is_affordance_open(self, affordance_name: str, hour: int | None = None) -> bool:
        """Return True if an affordance is open for the specified (or current) hour."""

        if affordance_name in self.affordance_overrides:
            return bool(self.affordance_overrides[affordance_name])

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

    def _build_vfs_affordance_context(self) -> dict[str, dict[str, torch.Tensor]]:
        """Build affordance state exposed to VFS expressions."""
        return {
            affordance_name: {"available": torch.tensor(self._is_affordance_open(affordance_name), device=self.device)}
            for affordance_name in self.affordances
        }

    def _build_vfs_temporal_context(self) -> dict[str, torch.Tensor]:
        """Build temporal state exposed to VFS expressions."""
        if not self.enable_temporal_mechanics:
            return {}

        day_length = float(self.day_length)
        time_of_day = float(self.time_of_day)
        day_progress = time_of_day / day_length
        night_threshold = day_length * 0.25
        is_night = time_of_day < night_threshold or time_of_day >= (day_length - night_threshold)

        return {
            "tick": torch.tensor(self.global_tick, device=self.device),
            "time_of_day": torch.tensor(time_of_day, device=self.device),
            "day_progress": torch.tensor(day_progress, device=self.device),
            "is_night": torch.tensor(is_night, device=self.device),
        }

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
                reads=list(action.reads),
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

    def _configure_partial_observability(self) -> None:
        """Derive POMDP vision window and validate substrate compatibility.

        Writes ``self.vision_radius`` and ``self.local_window_size`` when
        partial observability is enabled. Raises ``ValueError`` for any
        substrate / encoding combination that is unsupported under POMDP —
        these are configuration errors that should fail at compile time,
        not silently produce broken observations.
        """
        max_vision_radius = 50
        if self.partial_observability and self.substrate.supports_partial_vision:
            # The substrate owns the radius derivation and the window width
            # (WS-7 first knockdown): the same numbers the compiler asked for
            # at build_spec time, so declared and produced dims cannot drift.
            raw_radius = self.substrate.get_vision_radius(self.vision_range)
            if raw_radius > max_vision_radius:
                raise ValueError(
                    f"Vision radius {raw_radius} exceeds maximum {max_vision_radius}. "
                    f"This would create a {2 * raw_radius + 1}x{2 * raw_radius + 1} observation window, "
                    f"causing OOM. Reduce vision_range ({self.vision_range}) or the grid extent. "
                    f"Max supported configuration: derived vision radius <= {max_vision_radius}"
                )
            self.vision_radius = raw_radius
            self.local_window_size = (2 * self.vision_radius) + 1

        if not self.partial_observability:
            return

        if self.substrate.position_dim == 0:
            raise ValueError(
                "Partial observability (POMDP) is not supported for aspatial substrates. "
                "A local vision window requires at least 1 spatial dimension. "
                "Set partial_observability=False when using an aspatial substrate."
            )
        if isinstance(self.substrate, ContinuousSubstrate):
            raise ValueError(
                "Partial observability (POMDP) is not supported for continuous substrates. "
                "Continuous spaces have infinite positions within any local window, making discrete vision grids undefined. "
                "Use partial_observability=False with 'relative' or 'scaled' observation_encoding instead."
            )
        if self.substrate.position_dim >= 4:
            window_size = self.local_window_size or 0
            cell_count = window_size**self.substrate.position_dim if window_size > 0 else 0
            raise ValueError(
                f"Partial observability (POMDP) is not supported for {self.substrate.position_dim}D substrates. "
                f"\n\nProblem: Local window size grows EXPONENTIALLY with dimensionality:"
                f"\n  - 2D: {window_size}×{window_size} = {window_size**2} cells (practical)"
                f"\n  - 3D: {window_size}×{window_size}×{window_size} = {window_size**3} cells (supported up to vision_range=2)"
                f"\n  - {self.substrate.position_dim}D: {window_size}^{self.substrate.position_dim} = {cell_count:,} cells (IMPRACTICAL)"
                f"\n\nThis creates:"
                f"\n  - Network input explosion ({cell_count:,} vision features + position + meters)"
                f"\n  - Memory explosion (each agent's observation is massive)"
                f"\n  - Training slowdown (gradient computation over huge inputs)"
                f"\n\nSolution: Use full observability (partial_observability=False) with normalized position encoding:"
                f"\n  - observation_encoding='relative': Just {self.substrate.position_dim} dims (normalized coordinates)"
                f"\n  - observation_encoding='scaled': {self.substrate.position_dim * 2} dims (coordinates + grid sizes)"
                f"\n  - Enables dimension-independent learning WITHOUT exponential curse"
                f"\n\nSee docs/manual/pomdp_compatibility_matrix.md for details."
            )
        if self.substrate.position_dim == 3:
            window_size = self.local_window_size or 0
            window_volume = window_size**3 if window_size > 0 else 0
            if window_volume > 125:
                raise ValueError(
                    f"Grid3D POMDP with vision_range={self.vision_range} requires {window_volume} cells "
                    f"(window size {window_size}×{window_size}×{window_size}), which is excessive. "
                    f"Use vision_range ≤ 2 (5×5×5 = 125 cells) for Grid3D partial observability, "
                    f"or disable partial_observability."
                )
        if hasattr(self.substrate, "observation_encoding") and self.substrate.observation_encoding != "relative":
            raise ValueError(
                f"Partial observability (POMDP) requires observation_encoding='relative', "
                f"but substrate is configured with observation_encoding='{self.substrate.observation_encoding}'. "
                f"POMDP uses normalized positions for recurrent network position encoder. "
                f"Set observation_encoding='relative' in substrate.yaml or disable partial_observability."
            )

    def _initialize_vfs_subsystem(self) -> None:
        """Build the VFS variable registry, observation spec, and evaluator.

        Phase method of __init__ (hamlet-2559b98232). Writes:
        ``vfs_variables``, ``vfs_registry``, ``vfs_observation_spec``,
        ``vfs_evaluator``, ``vfs_evaluation_marks``, ``meter_name_to_index``,
        Depends on ``self.metadata``, ``self.num_agents``,
        ``self.device``, ``self.universe``.
        """
        universe = self.universe
        self.vfs_variables: list[VariableDef] = list(universe.vfs_variables)

        max_items_in_world = universe.items_catalog.max_items_in_world if universe.items_catalog else 0
        item_profiles = None
        if universe.compiled_vfs_profiles is not None:
            item_profiles = universe.compiled_vfs_profiles.item_profiles

        self.vfs_registry = VariableRegistry(
            variables=self.vfs_variables,
            num_agents=self.num_agents,
            device=self.device,
            max_items=max_items_in_world,
            num_affordances=self.metadata.affordance_count,
            item_profiles=item_profiles,
            num_zones=self.metadata.num_zones,
            num_groups=self.metadata.num_groups,
            num_message_slots=self.metadata.num_message_slots,
        )

        self.vfs_observation_spec: VFSObservationSpec | None = None
        if universe.compiled_vfs_profiles is not None:
            if universe.vfs_observation_spec is None:
                raise ValueError("Compiled universe is missing vfs_observation_spec; recompile the config pack.")
            self.vfs_observation_spec = universe.vfs_observation_spec

        self.vfs_evaluator: VFSEvaluator | None = None
        if universe.compiled_vfs_profiles is not None:
            mode = EvaluationMode(universe.compiled_vfs_profiles.evaluation_mode)
            self.vfs_evaluator = VFSEvaluator(
                mode=mode,
                history_spec=universe.vfs_history_spec,
                debug_logging=universe.compiled_vfs_profiles.debug_logging,
            )
            self.vfs_evaluation_marks = universe.vfs_evaluation_marks
        else:
            self.vfs_evaluation_marks = None

        meter_name_to_index = dict(self.metadata.meter_name_to_index)
        self.meter_name_to_index = meter_name_to_index

    def _initialize_dac_engine(self) -> None:
        """Construct the DAC reward backend and prepare the runtime-registry slot.

        Phase method of __init__ (hamlet-2559b98232). Writes ``dac_engine``
        and ``runtime_registry``. Depends on ``vfs_registry`` from the VFS
        phase.
        """
        bar_index_map = env_factory._build_bar_index_map(self.universe.meter_metadata)
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
                "Define item VFS profiles in vfs_profiles.yaml for all item types."
            )

        self.item_manager = ItemManager(
            catalog=universe.items_catalog,
            max_items=universe.items_catalog.max_items_in_world,
            device=self.device,
            schema=self.effects_schema,
            vfs_registry=self.vfs_registry,
            effect_manager=self.effect_manager,
        )
        self.item_inventory = InventoryState(
            batch_size=num_agents,
            max_items_per_agent=universe.items_catalog.max_items_per_agent,
            device=str(self.device),
        )
        self.item_handler = ItemActionHandler(
            manager=self.item_manager,
            inventory=self.item_inventory,
            command_executor=self.command_executor,
            vfs_registry=self.vfs_registry,
            meter_name_to_index=self.meter_name_to_index,
            effect_manager=self.effect_manager,
            affordance_overrides=self.affordance_overrides,
        )

    def _initialize_affordance_engine(self, num_agents: int) -> None:
        """Build the affordance engine.

        Phase method of __init__ (hamlet-2559b98232). Must run after the
        item subsystem; depends on the VTC modulation program, VFS registry,
        effects schema, command executor, and effect manager.
        """
        self.affordance_engine = AffordanceEngine(
            tuple(self.level.affordances.affordances),
            num_agents,
            self.device,
            self.meter_name_to_index,
            modulation_program=self.vtc_modulation_program,
            vfs_registry=self.vfs_registry,
            effects_schema=self.effects_schema,
            command_executor=self.command_executor,
            effect_manager=self.effect_manager,
            meter_bounds_min=self.meter_bounds_min,
            meter_bounds_max=self.meter_bounds_max,
            item_manager=self.item_manager or NullItemManager(),
            affordance_overrides=self.affordance_overrides,
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
        return self.action_labels.get_all_labels()

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

    def reset(self) -> torch.Tensor:
        """
        Reset all environments.

        Returns:
            observations: [num_agents, observation_dim]
        """
        # Refresh affordance layout each episode so randomization/configured layouts stay in sync
        # BUG-15 fix: randomize_affordance_positions() now returns agent positions to prevent collisions
        if self.randomize_affordances:
            agent_positions = self.randomize_affordance_positions()
            # Use returned positions (guaranteed collision-free with affordances)
            self.positions = (
                agent_positions if agent_positions is not None else self.substrate.initialize_positions(self.num_agents, self.device)
            )
        else:
            self._apply_configured_affordance_positions()
            # When using configured positions, agents still spawn randomly (could still collide)
            # TODO: Consider also handling configured affordance case for complete collision-free guarantee
            self.positions = self.substrate.initialize_positions(self.num_agents, self.device)

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
        self.global_tick = 0  # HIGH-01: Reset global time counter
        self.intrinsic_weights = torch.ones(self.num_agents, dtype=torch.float32, device=self.device)  # Reset to 1.0
        self.vfs_registry.reset_episode_scoped()
        # Pinned tick write point (token-obs unit 2): same registry cell as step()'s.
        # Ordered AFTER reset_episode_scoped: the tick variable is episode-lifetime, so
        # a write before the reset would be clobbered back to its declared initial —
        # value-identically today (both are 0.0), but the pinned write must be the
        # authoritative one, not a coincidence (comment-242 item 3, reorder chosen).
        self.vfs_registry.set_engine_value("tick", torch.tensor(float(self.global_tick), device=self.device))

        # Reset temporal mechanics state
        if self.enable_temporal_mechanics:
            self.time_of_day = 0
            self.interaction_progress.fill_(0)
            self.last_interaction_affordance = [None] * self.num_agents
            self.last_interaction_position.fill_(0)

        # Reset affordance history tracking
        self._last_affordances = [None] * self.num_agents
        self._affordance_streaks = {}
        self._unique_affordances_count.zero_()
        self._affordances_seen = [set() for _ in range(self.num_agents)]
        # Clear any runtime overrides so each episode starts from configured availability
        self.affordance_overrides.clear()

        # Reset scheduler/delayed work and cancel agent-scoped pending items between episodes
        if self.effect_manager is not None:
            # Clear scheduler state
            self.effect_manager.reset_scheduler(current_tick=0)
            # Cancel any lingering agent-scoped items (paranoia if reset called mid-episode)
            for agent_idx in range(self.num_agents):
                self.effect_manager.cancel_scheduled_for_entity(scope="agent", entity_id=agent_idx)

        # Reset temporal history so temporal VFS ops don't leak across episodes
        if self.vfs_evaluator is not None:
            self.vfs_evaluator.reset()

        # Clear item/inventory state between episodes
        if self.item_manager is not None:
            self.item_manager.reset_state()
        if self.item_inventory is not None:
            self.item_inventory.reset()

        # Spawn initial items if configured
        if self.item_manager is not None and self.level.items_appearance is not None:
            # Get grid size from substrate (only works for Grid2D/Grid3D/GridND)
            # For continuous substrates, this would need different handling
            grid_size: tuple[int, ...] | None = None
            if hasattr(self.substrate, "width") and hasattr(self.substrate, "height"):
                if hasattr(self.substrate, "depth"):
                    # Grid3D
                    grid_size = (self.substrate.width, self.substrate.height, self.substrate.depth)
                else:
                    # Grid2D
                    grid_size = (self.substrate.width, self.substrate.height)

            if grid_size is not None:
                bars_dict_spawn = {name: self.meters[:, idx] for name, idx in self.meter_name_to_index.items()}
                temporal_context = {"tick": torch.tensor(0, device=self.device)} if self.enable_temporal_mechanics else None
                self.item_manager.spawn_initial_items(
                    appearance_config=self.level.items_appearance,
                    grid_size=grid_size,
                    current_tick=0,
                    bars=bars_dict_spawn,
                    temporal=temporal_context,
                )

        return self._observation_encoder._get_observations()

    @classmethod
    def from_universe(
        cls,
        universe: CompiledUniverse,
        *,
        level_name: str,
        num_agents: int,
        device: torch.device | str,
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
        return env_factory.from_universe(
            cls,
            universe=universe,
            level_name=level_name,
            num_agents=num_agents,
            device=device,
        )

    def _get_observations(self) -> torch.Tensor:
        """Construct observation vector using compiled observation spec."""
        return self._observation_encoder._get_observations()

    def _build_affordance_encoding(self, dims: int) -> torch.Tensor:
        """Build one-hot encoding of current affordance under each agent."""
        return self._observation_encoder._build_affordance_encoding(dims)

    def _build_effects_observation(self, dims: int) -> torch.Tensor:
        """Encode observable effects into a fixed-size tensor."""
        if dims <= 0:
            return torch.zeros(self.num_agents, 0, device=self.device)

        if self.effect_manager is None or self.effect_observation_slots <= 0:
            return torch.zeros(self.num_agents, dims, device=self.device)

        expected_dims = self.effect_observation_slots * 3
        if dims != expected_dims:
            raise ValueError(
                f"Observation field 'obs_effects' expected {dims} dims, but effect observation metadata requires {expected_dims}."
            )

        slots = self.effect_observation_slots
        effect_obs = torch.zeros(self.num_agents, slots, 3, device=self.device)

        for agent_idx in range(self.num_agents):
            for slot_idx, effect in enumerate(self.effect_manager.get_observable_agent_effects(agent_idx)[:slots]):
                effect_obs[agent_idx, slot_idx, 0] = float(getattr(effect, "effect_index", -1))
                total = max(1, int(getattr(effect, "duration_total", 1)))
                remaining = max(0, int(getattr(effect, "duration_remaining", 0)))
                effect_obs[agent_idx, slot_idx, 1] = float(remaining) / float(total)
                effect_obs[agent_idx, slot_idx, 2] = 1.0

        return effect_obs.reshape(self.num_agents, slots * 3)

    def _encode_position_observation(self) -> torch.Tensor | None:
        """Encode agent position using substrate-native semantics."""
        return self._observation_encoder._encode_position_observation()

    def _encode_velocity_observation(self) -> torch.Tensor | None:
        """Encode agent velocity as delta position per step.

        Returns:
            [num_agents, position_dim] tensor or None for aspatial substrates.
        """
        if getattr(self.substrate, "position_dim", 0) == 0:
            return None

        # Velocity is tracked per-step in _execute_actions; default to zeros if unset.
        if not hasattr(self, "_velocity"):
            return torch.zeros(
                (self.num_agents, self.substrate.position_dim),
                dtype=torch.float32,
                device=self.device,
            )
        velocity: torch.Tensor | None = getattr(self, "_velocity")
        if velocity is None:
            return torch.zeros(
                (self.num_agents, self.substrate.position_dim),
                dtype=torch.float32,
                device=self.device,
            )
        return velocity

    def get_action_masks(self) -> torch.Tensor:
        """Compute valid-action masks for the current tick.

        Delegates to :class:`ActionMaskBuilder`. Returns a
        ``[num_agents, action_dim]`` bool tensor where ``True`` is a valid
        action; semantics are documented on the builder.
        """
        return self.action_mask_builder.build(
            num_agents=self.num_agents,
            positions=self.positions,
            dones=self.dones if hasattr(self, "dones") else None,
            item_inventory=self.item_inventory,
            item_manager=self.item_manager,
            item_handler=self.item_handler,
            affordances=self.affordances,
            is_affordance_open=self._is_affordance_open,
        )

    def step(
        self,
        actions: torch.Tensor,  # [num_agents]
        depletion_multiplier: float = 1.0,  # Curriculum difficulty
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]:
        """
        Execute one step for all agents.

        Args:
            actions: [num_agents] tensor of actions (0-4)
            depletion_multiplier: Curriculum difficulty multiplier (0.2 = 20% difficulty)

        Returns:
            observations: [num_agents, observation_dim]
            rewards: [num_agents]
            dones: [num_agents] bool
            info: dict with metadata
        """
        # Pinned tick write point (token-obs unit 2): every consumer of THIS step —
        # action executor, effects (current_step), evaluator — sees this one value,
        # and any read of the registry's tick returns the same.
        self.vfs_registry.set_engine_value("tick", torch.tensor(float(self.global_tick), device=self.device))
        prev_dones = self.dones.clone()
        self.vfs_registry.reset_tick_scoped()
        # 1. Execute actions and track successful interactions
        successful_interactions = self._action_executor._execute_actions(actions)
        self._run_vtc_transition_phases(
            self.vtc_transition_runner.phases_through("apply_completion_bonuses"),
            actions=actions,
            active_mask=torch.logical_not(prev_dones),
        )

        # 2. Deplete meters (base passive decay with curriculum difficulty)
        self._apply_vtc_passive_depletion(depletion_multiplier)

        # 3. Passive threshold cascades via VTC relationship rules.
        self._apply_vtc_threshold_cascades()

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
            )

        # Sync meters back from bars dict (effects may have modified them)
        for bar_name, idx in self.meter_name_to_index.items():
            self.meters[:, idx] = bars_dict[bar_name]

        # 3.6. Evaluate VFS expressions if evaluator present
        if self.vfs_evaluator is not None and self.universe.compiled_vfs_profiles is not None:
            # Build execution context from current state
            bars_dict_vfs = {name: self.meters[:, idx] for name, idx in self.meter_name_to_index.items()}

            # Get current VFS state from registry
            # HIGH-02: Use proper VFS API instead of direct _storage access
            current_vfs_state = self._current_vfs_state()

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
                    step=self.global_tick,  # HIGH-01: Use global tick instead of agent 0
                    affordances=self._build_vfs_affordance_context(),
                    temporal=self._build_vfs_temporal_context(),
                    agent_positions=self.positions.to(dtype=torch.float32, device=self.device),
                    affordance_positions={k: v.to(dtype=torch.float32, device=self.device) for k, v in self.affordances.items()},
                    vfs_types={name: var.type for name, var in self.vfs_registry.variables.items()},
                    num_agents=self.num_agents,
                    item_vfs=self.vfs_registry.item_vfs,
                    item_profile_map=self.vfs_registry.item_profile_map,
                    item_index_to_profile=self.vfs_registry.item_vfs_index_to_profile,
                )

                self._write_back_profile_expressions(
                    "Global-profile", "global_profile", global_profile, updated_vfs, require_agent_shape=False
                )

            # Evaluate agent profile (hamlet-5d74335111). Compiled agent profiles are
            # CompiledGlobalProfile — the same machinery, the same MARK_AND_SWEEP
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
                    step=self.global_tick,
                    affordances=self._build_vfs_affordance_context(),
                    temporal=self._build_vfs_temporal_context(),
                    agent_positions=self.positions.to(dtype=torch.float32, device=self.device),
                    affordance_positions={k: v.to(dtype=torch.float32, device=self.device) for k, v in self.affordances.items()},
                    vfs_types={name: var.type for name, var in self.vfs_registry.variables.items()},
                    num_agents=self.num_agents,
                    item_vfs=self.vfs_registry.item_vfs,
                    item_profile_map=self.vfs_registry.item_profile_map,
                    item_index_to_profile=self.vfs_registry.item_vfs_index_to_profile,
                )
                self._write_back_profile_expressions(
                    "Agent-profile", "agent_profile", agent_profile, updated_agent_vfs, require_agent_shape=True
                )

        self._run_vtc_transition_phases(
            self.vtc_transition_runner.phases_between("apply_threshold_cascades", "evaluate_terminal_conditions"),
            active_mask=torch.logical_not(prev_dones),
        )

        # 4. Evaluate VTC terminal conditions
        self._apply_vtc_terminal_conditions()

        # 5. Increment step counts (before retirement check)
        self.step_counts += 1
        self.global_tick += 1  # HIGH-01: Increment global time counter

        # 5.1. Age items and process periodic respawning (after step count increment)
        # Items age/despawn/respawn based on the NEW tick count after incrementing
        if self.item_manager is not None:
            # HIGH-01: Use global tick instead of agent 0
            # Age all items (expire items that reach duration limit)
            self.item_manager.tick(self.global_tick)
            # Respawn items whose spawn_interval timer has expired
            bars_dict_spawn = {name: self.meters[:, idx] for name, idx in self.meter_name_to_index.items()}
            temporal_context = {"tick": torch.tensor(self.global_tick, device=self.device)} if self.enable_temporal_mechanics else None
            self.item_manager.process_respawns(self.global_tick, bars=bars_dict_spawn, temporal=temporal_context)

        # 5.5. Check for retirement (reached maximum lifespan)
        # Agents that reach their lifespan retire with a bonus reward
        retired = self.step_counts >= self.agent_lifespan

        # 6. Calculate rewards (interoception-aware)
        rewards = self._reward_calculator._calculate_shaped_rewards()
        rewards = torch.where(retired, rewards + 1.0, rewards)  # +1 retirement bonus
        self.dones = torch.logical_or(self.dones, retired)

        # Cancel any pending agent-scoped delayed work for agents that just became done
        if self.effect_manager is not None and self.effect_manager.scheduler is not None:
            newly_done = torch.logical_and(self.dones, ~prev_dones)
            if newly_done.any():
                for idx in torch.nonzero(newly_done, as_tuple=False).flatten():
                    self.effect_manager.cancel_scheduled_for_entity(scope="agent", entity_id=int(idx))

        # 6. time_of_day is DERIVED from global_tick at this same point in the step —
        # one temporal pipeline (token-obs unit 2c). The update point is load-bearing:
        # the reward calculator reads time_of_day between the global_tick increment and
        # here, and moving this line changes reward timing against the pinned oracle.
        self.time_of_day = (self.global_tick % int(self.day_length)) if self.enable_temporal_mechanics else 0

        observations = self._observation_encoder._get_observations()

        info = {
            "step_counts": self.step_counts.clone(),
            "positions": self.positions.clone(),
            "successful_interactions": successful_interactions,  # {agent_idx: affordance_name}
            "reward_components": self._last_reward_components,  # DAC breakdown
            "intrinsic_weight": self.intrinsic_weights,  # Effective modifier weight
        }

        return observations, rewards, self.dones, info

    def _execute_actions(self, actions: torch.Tensor) -> dict:
        """Execute movement, interaction, and wait actions."""
        return self._action_executor._execute_actions(actions)

    def _apply_vtc_action_writes(self, actions: torch.Tensor, active_mask: torch.Tensor) -> None:
        """Apply compiled VFS transition writes for selected actions."""
        self._run_vtc_transition_phases(
            self.vtc_transition_runner.phases_through("apply_completion_bonuses"),
            actions=actions,
            active_mask=active_mask,
        )

    def _apply_vtc_passive_depletion(self, depletion_multiplier: float) -> None:
        """Apply compiled VFS passive-depletion rules to meter bars."""
        self._run_vtc_transition_phases(
            ("apply_passive_depletion",),
            active_mask=torch.ones_like(self.dones, dtype=torch.bool, device=self.device),
            depletion_multiplier=depletion_multiplier,
        )

    def _apply_vtc_threshold_cascades(self) -> None:
        """Apply compiled VFS threshold-cascade rules to meter bars."""
        self._run_vtc_transition_phases(
            ("apply_threshold_cascades",),
            active_mask=torch.ones_like(self.dones, dtype=torch.bool, device=self.device),
        )

    def _apply_vtc_terminal_conditions(self) -> None:
        """Evaluate compiled VFS terminal-condition rules over meter bars."""
        self._run_vtc_transition_phases(
            ("evaluate_terminal_conditions",),
            dones=self.dones,
            active_mask=torch.logical_not(self.dones),
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
        result = self.vtc_transition_runner.run_phases(
            phases,
            VTCTransitionContext(
                actions=actions,
                vfs_state=self._current_vfs_state(),
                bars_state=self._current_bar_state(),
                active_mask=active_mask,
                device=self.device,
                dones=dones,
                depletion_multiplier=depletion_multiplier,
            ),
        )
        self._commit_vtc_transition_state(result)

    def _commit_vtc_transition_state(self, state: VTCTransitionState) -> None:
        for bar_name, value in state.bars_state.items():
            self._set_vtc_bar_value(bar_name, value)
        for variable_id, value in state.vfs_state.items():
            if variable_id not in self.vfs_registry.variables:
                raise KeyError(
                    f"VTC transition write-back produced unknown variable id '{variable_id}'.\n"
                    "  Write source: VTC transition state commit (_commit_vtc_transition_state) "
                    "(hamlet-0ddc83e377)."
                )
            self.vfs_registry.set_engine_value(variable_id, value)
        if state.dones is not None:
            self.dones = state.dones

    def _write_back_profile_expressions(
        self,
        profile_label: str,
        write_source: str,
        profile: Any,
        updated_vfs: dict[str, torch.Tensor],
        *,
        require_agent_shape: bool,
    ) -> None:
        """Commit profile expression outputs to the registry — the static-merge/refusal
        block, hoisted out of step()'s `compiled_vfs_profiles is not None` gate
        (comment-242 item 2) so the global and agent branches share one implementation.

        The evaluator chases in-profile dependencies of marked variables, so
        `updated_vfs` can contain a STATIC dependency re-emitted at its initial value
        (evaluator.py's add_with_deps; statics also enter vars_to_eval via
        history_spec). Statics are storage, not evaluation output: write back only
        expression variables, or a dependency chase silently clobbers an engine-written
        static every step (hamlet-df3a96bbac). An unknown variable id is a refusal
        (hamlet-0ddc83e377); agent-profile expressions must land [num_agents]-shaped.
        """
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
            self.vfs_registry.set_engine_value(var_name, value)

    def _current_vfs_state(self) -> dict[str, torch.Tensor]:
        """Return the engine-readable VFS registry snapshot."""
        return {var_name: self.vfs_registry.get(var_name, reader="engine") for var_name in self.vfs_registry.variables.keys()}

    def _current_bar_state(self) -> dict[str, torch.Tensor]:
        """Return meter bars in the VTC expression namespace."""
        return {bar_name: self.meters[:, idx] for bar_name, idx in self.meter_name_to_index.items()}

    def _set_vtc_bar_value(self, bar_name: str, value: torch.Tensor) -> None:
        """Write a VTC-updated bar tensor back to the environment meters."""
        meter_idx = self.meter_name_to_index[bar_name]
        expected = self.meters[:, meter_idx]
        if value.shape != expected.shape:
            raise ValueError(f"VTC action write for bar '{bar_name}' produced shape {tuple(value.shape)}, expected {tuple(expected.shape)}")
        self.meters[:, meter_idx] = value.to(device=self.device, dtype=expected.dtype)

    def _handle_interactions(self, interact_mask: torch.Tensor) -> dict:
        """Handle INTERACT actions with multi-tick accumulation."""
        return self._action_executor._handle_interactions(interact_mask)

    def _handle_instant_interactions(self, interact_mask: torch.Tensor) -> dict:
        """Handle INTERACT action at affordances in instant mode."""
        return self._action_executor._handle_instant_interactions(interact_mask)

    def _calculate_shaped_rewards(self) -> torch.Tensor:
        """Calculate total rewards using DACEngine."""
        return self._reward_calculator._calculate_shaped_rewards()

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

    def get_affordance_positions(self) -> dict:
        """Get current affordance positions (substrate-agnostic checkpointing).

        Returns:
            Dictionary with 'positions', 'ordering', and 'position_dim' keys:
            - 'positions': Dict mapping affordance names to position lists
            - 'ordering': List of affordance names in consistent order
            - 'position_dim': Dimensionality for validation (0=aspatial, 2=2D, 3=3D)
        """
        positions = {}
        for name, pos_tensor in self.affordances.items():
            # Convert tensor to list (handles any dimensionality)
            pos = pos_tensor.cpu().tolist()

            # Ensure pos is a list (even for 0-dimensional positions)
            if isinstance(pos, int | float):
                pos = [pos]
            elif self.substrate.position_dim == 0:
                pos = []

            positions[name] = [int(x) for x in pos] if pos else []

        return {
            "positions": positions,
            "ordering": self.affordance_names,
            "position_dim": self.substrate.position_dim,  # For validation
        }

    def set_affordance_positions(self, checkpoint_data: dict) -> None:
        """Set affordance positions from checkpoint.

        Args:
            checkpoint_data: Dictionary with 'positions', 'ordering', and 'position_dim'

        Raises:
            ValueError: If checkpoint missing position_dim or incompatible with substrate
        """
        # Validate position_dim exists
        if "position_dim" not in checkpoint_data:
            raise ValueError(
                "Checkpoint missing 'position_dim' field.\n"
                "This checkpoint format is no longer supported.\n"
                "\n"
                "Action required:\n"
                "  1. Delete old checkpoint directories\n"
                "  2. Retrain models from scratch\n"
            )

        # Validate compatibility
        checkpoint_position_dim = checkpoint_data["position_dim"]
        if checkpoint_position_dim != self.substrate.position_dim:
            raise ValueError(
                f"Checkpoint position_dim mismatch: checkpoint has {checkpoint_position_dim}D, "
                f"but current substrate requires {self.substrate.position_dim}D."
            )

        # Load checkpoint data
        positions = checkpoint_data["positions"]
        ordering = checkpoint_data["ordering"]

        self.affordance_names = ordering
        self.num_affordance_types = len(self.affordance_names)

        for name, pos in positions.items():
            if name in self.affordances:
                self.affordances[name] = torch.tensor(pos, device=self.device, dtype=self.substrate.position_dtype)

    def randomize_affordance_positions(self) -> torch.Tensor | None:
        """Randomize affordance positions and return agent spawn positions.

        Returns:
            Agent spawn positions [num_agents, position_dim] or None if not randomizing.
            Positions are guaranteed collision-free with affordances.

        Note:
            BUG-15 fix: Samples (affordances + agents) positions together to prevent
            agents spawning on top of affordances.
        """

        if not self.randomize_affordances:
            return None

        if not self.affordances:
            return None

        # Aspatial universes have no coordinates; store empty tensors for consistency
        if self.substrate.position_dim == 0:
            empty = torch.zeros(0, dtype=self.substrate.position_dtype, device=self.device)
            for name in self.affordances.keys():
                self.affordances[name] = empty.clone()
            # Return empty agent positions for aspatial
            return torch.zeros(self.num_agents, 0, dtype=self.substrate.position_dtype, device=self.device)

        # Check capacity analytically without enumerating positions (JANK-10 fix)
        capacity = self.substrate.get_capacity()

        # If capacity is finite, validate there's enough space
        if capacity is not None:
            required_slots = len(self.affordances) + self.num_agents
            if required_slots > capacity:
                # Align with v2.1 compiler behavior: treat this as an operator warning
                # rather than a hard error (RawConfigsV21 already emits a warning).
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    "Grid capacity warning at runtime: %s positions may not fit %s agents + %s affordances "
                    "(%s entities total). Disabling affordance randomization for this run.",
                    capacity,
                    self.num_agents,
                    len(self.affordances),
                    required_slots,
                )
                # Disable randomization for this environment instance and fall back
                # to configured positions (env will call _apply_configured_affordance_positions()).
                self.randomize_affordances = False
                return None

        # Sample (affordances + agents) positions together (BUG-15 fix)
        # For discrete grids: retry on collision to guarantee unique positions
        # For continuous: collisions are acceptable (infinite positions)
        total_positions_needed = len(self.affordances) + self.num_agents
        sampled = None

        if capacity is not None:
            # Discrete grid: try random sampling with collision detection
            max_attempts = 10
            for attempt in range(max_attempts):
                sampled = self.substrate.initialize_positions(total_positions_needed, self.device)

                # Convert positions to tuples for uniqueness check
                positions_as_tuples = [tuple(sampled[i].tolist()) for i in range(total_positions_needed)]
                if len(positions_as_tuples) == len(set(positions_as_tuples)):
                    break  # No collisions, we're done
            else:
                # Retries exhausted (very rare for large grids, possible for small grids)
                # Fall back to enumeration to guarantee collision-free placement.
                # Permutation is drawn from torch's CPU RNG, not Python's global
                # `random` — placement must be reproducible from seed_all alone.
                all_positions = self.substrate.get_all_positions()
                perm = torch.randperm(len(all_positions))
                sampled = torch.stack(
                    [
                        torch.tensor(all_positions[int(perm[idx])], dtype=self.substrate.position_dtype, device=self.device)
                        for idx in range(total_positions_needed)
                    ]
                )
        else:
            # Continuous/aspatial: sample directly (infinite positions, collisions OK)
            sampled = self.substrate.initialize_positions(total_positions_needed, self.device)

        # Split: first N for affordances, remaining M for agents
        affordance_positions = sampled[: len(self.affordances)]
        agent_positions = sampled[len(self.affordances) :]

        for idx, name in enumerate(self.affordances.keys()):
            self.affordances[name] = affordance_positions[idx].clone()

        return agent_positions
