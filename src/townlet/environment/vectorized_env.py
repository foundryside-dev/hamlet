"""
Vectorized Hamlet environment for GPU-native training.

Batches multiple independent Hamlet environments into a single vectorized
environment with tensor operations [num_agents, ...].
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from numbers import Number
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import torch

from townlet.environment.action_builder import ComposedActionSpace
from townlet.environment.affordance_engine import AffordanceEngine
from townlet.environment.dac_engine import DACEngine
from townlet.environment.meter_dynamics import MeterDynamics
from townlet.substrate import SpatialSubstrate
from townlet.substrate.continuous import ContinuousSubstrate
from townlet.universe.dto import ActionSpaceMetadata, MeterMetadata
from townlet.vfs.registry import VariableRegistry

if TYPE_CHECKING:
    from townlet.environment.action_config import ActionConfig, ActionSpaceConfig
    from townlet.exploration.base import ExplorationStrategy
    from townlet.population.runtime_registry import AgentRuntimeRegistry
    from townlet.universe.compiled import CompiledUniverse


def _build_bar_index_map(meter_metadata: MeterMetadata) -> dict[str, int]:
    """Build mapping from bar IDs to meter tensor indices.

    Args:
        meter_metadata: Universe meter metadata

    Returns:
        Dictionary mapping bar_id -> tensor_index
    """
    return {meter.name: meter.index for meter in meter_metadata.meters}


def _resolve_deployable_affordances(
    all_affordance_names: list[str],
    enabled_affordances: list[str] | None,
    name_to_id: dict[str, str],
) -> list[str]:
    """Return affordances that should be deployed, respecting IDs and names in config."""

    if enabled_affordances is None:
        raise ValueError("enabled_affordances must be an explicit list (empty to deploy none); null is not allowed.")

    enabled_lookup = {str(entry) for entry in enabled_affordances}
    deployable: list[str] = []
    for name in all_affordance_names:
        if name in enabled_lookup:
            deployable.append(name)
            continue
        aff_id = name_to_id.get(name)
        if aff_id is not None and aff_id in enabled_lookup:
            deployable.append(name)
    return deployable


class VectorizedHamletEnv:
    """
    GPU-native vectorized Hamlet environment.

    Batches multiple independent environments for parallel execution.
    All state is stored as PyTorch tensors on specified device.
    """

    def __init__(
        self,
        *,
        universe: CompiledUniverse,
        level_name: str,
        num_agents: int,
        device: torch.device | str = torch.device("cpu"),
    ):
        """
        Initialize vectorized environment.

        Args:
            universe: CompiledUniverse artifact produced by UniverseCompiler (v2.1 hierarchical configs)
            level_name: Which curriculum level to instantiate (e.g., "L0_0_minimal")
            num_agents: Number of parallel agents to simulate
            device: PyTorch device or device string (defaults to CPU). Infrastructure default - PDR-002 exemption.

        Note (PDR-002 Compliance):
            - device retains an infrastructure default (exempted from no-defaults principle)
            - Behavioral parameters (grid size, observability, energy costs, affordance selection)
              now flow exclusively from the compiled universe
        """
        torch_device = torch.device(device) if isinstance(device, str) else device

        level = universe.get_level(level_name)
        self.level_name = level_name
        self.level = level
        self.universe = universe
        self.config_pack_path = Path(universe.experiment_dir or ".")
        self.num_agents = num_agents
        self.device = torch_device
        self.optimization_data = level.optimization_data

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
                self.day_length = getattr(universe.metadata, "ticks_per_day", 0) or 0
            else:
                self.day_length = inactive_day_length
        self.agent_lifespan = training_cfg.training_loop.max_steps_per_episode
        partial_observability = self.partial_observability
        vision_range = self.vision_range

        from townlet.substrate.factory import SubstrateFactory

        self.substrate = SubstrateFactory.build(self.universe.stratum.stratum.substrate, device=torch_device)

        from townlet.environment.action_labels import get_labels

        action_labels_config = self.universe.actions.actions.labels
        self.action_labels = get_labels(
            preset=action_labels_config.preset,
            substrate_position_dim=self.substrate.position_dim,
        )

        # Metadata and observation activity
        self.metadata = self.universe.metadata
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

        # Get grid_size from substrate (single source of truth)
        # For grid substrates, read directly from substrate dimensions
        # For non-grid substrates (aspatial, continuous), grid_size will be None
        if hasattr(self.substrate, "width") and hasattr(self.substrate, "height"):
            if self.substrate.width != self.substrate.height:
                raise ValueError(f"Non-square grids not yet supported: {self.substrate.width}×{self.substrate.height}")
            self.grid_size = self.substrate.width
        else:
            # For non-grid substrates (aspatial, continuous), use metadata if available
            self.grid_size = self.metadata.grid_size

        # Observation/model metadata
        self.meter_count = self.metadata.meter_count
        meter_count = self.meter_count
        self.base_depletions = self.optimization_data.base_depletions.to(self.device)

        # Derive vision radius/window for partial observability (POMDP) when applicable.
        # Uses the same semantics as the v2.1 compiler:
        #   radius = ceil(vision_range * (grid_size / 2))
        #   window_size = 2 * radius + 1 (clamped to grid_size)
        self.vision_radius: int = 0
        self.local_window_size: int = 0
        if self.partial_observability and self.grid_size is not None:
            grid_size = float(self.grid_size)
            self.vision_radius = max(1, int(math.ceil(self.vision_range * (grid_size / 2.0))))
            self.local_window_size = min((2 * self.vision_radius) + 1, int(grid_size))

        # Validate partial observability support
        if partial_observability and self.substrate.position_dim == 0:
            raise ValueError(
                "Partial observability (POMDP) is not supported for aspatial substrates. "
                "A local vision window requires at least 1 spatial dimension. "
                "Set partial_observability=False when using an aspatial substrate."
            )
        if partial_observability and isinstance(self.substrate, ContinuousSubstrate):
            raise ValueError(
                "Partial observability (POMDP) is not supported for continuous substrates. "
                "Continuous spaces have infinite positions within any local window, making discrete vision grids undefined. "
                "Use partial_observability=False with 'relative' or 'scaled' observation_encoding instead."
            )
        if partial_observability and self.substrate.position_dim >= 4:
            # Exponential blow-up for high-dimensional local windows.
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

        # Validate Grid3D POMDP vision range (prevent memory explosion)
        if partial_observability and self.substrate.position_dim == 3:
            window_size = self.local_window_size or 0
            window_volume = window_size**3 if window_size > 0 else 0
            if window_volume > 125:  # 5×5×5 = 125 is the threshold
                raise ValueError(
                    f"Grid3D POMDP with vision_range={vision_range} requires {window_volume} cells "
                    f"(window size {window_size}×{window_size}×{window_size}), which is excessive. "
                    f"Use vision_range ≤ 2 (5×5×5 = 125 cells) for Grid3D partial observability, "
                    f"or disable partial_observability."
                )

        # Validate observation_encoding compatibility with POMDP
        if partial_observability and hasattr(self.substrate, "observation_encoding"):
            if self.substrate.observation_encoding != "relative":
                raise ValueError(
                    f"Partial observability (POMDP) requires observation_encoding='relative', "
                    f"but substrate is configured with observation_encoding='{self.substrate.observation_encoding}'. "
                    f"POMDP uses normalized positions for recurrent network position encoder. "
                    f"Set observation_encoding='relative' in substrate.yaml or disable partial_observability."
                )

        # Observation dimension is derived from the level-specific spec.
        self.observation_dim = self.observation_spec.total_dims

        # VFS INTEGRATION: Initialize variable registry from compiled VFS variables
        self.vfs_variables = list(level.vfs_variables)
        self.vfs_registry = VariableRegistry(variables=self.vfs_variables, num_agents=num_agents, device=self.device)

        # Initialize reward strategy (TASK-001: variable meters)
        meter_name_to_index = dict(self.metadata.meter_name_to_index)
        self.meter_name_to_index = meter_name_to_index

        # Build bar index map from universe metadata
        bar_index_map = _build_bar_index_map(self.universe.meter_metadata)

        # Instantiate DACEngine using agent drive config (v2.1)
        self.dac_engine = DACEngine(
            dac_config=self.universe.agent.agent.drive,
            vfs_registry=self.vfs_registry,
            device=self.device,
            num_agents=self.num_agents,
            bar_index_map=bar_index_map,
        )
        self.runtime_registry: AgentRuntimeRegistry | None = None  # Injected by population/inference controllers

        # Bars configuration (per-level)
        self.bars_config = level.bars

        # Precompute meter initialization tensor from bars config
        self.initial_meter_values = torch.zeros(meter_count, dtype=torch.float32, device=self.device)
        for bar in self.bars_config.meters:
            idx = meter_name_to_index.get(bar.name)
            if idx is not None:
                self.initial_meter_values[idx] = bar.initial

        # Build terminal conditions from lethal bounds
        terminal_specs: list[dict[str, Any]] = []
        for bar in self.bars_config.meters:
            idx = meter_name_to_index.get(bar.name)
            if idx is None:
                continue
            if bar.bounds.lethal_min:
                terminal_specs.append({"meter_idx": idx, "operator": "<=", "value": bar.bounds.min})
            if bar.bounds.lethal_max:
                terminal_specs.append({"meter_idx": idx, "operator": ">=", "value": bar.bounds.max})

        # Initialize meter dynamics directly from optimization tensors
        self.meter_dynamics = MeterDynamics(
            base_depletions=self.optimization_data.base_depletions,
            cascade_data=self.optimization_data.cascade_data,
            # v2.1: modulation_data encodes bar→affordance modulation (environment.yaml modulation_graph)
            # and is consumed by AffordanceEngine. MeterDynamics currently only supports
            # meter→meter modulations, so we pass an empty sequence here.
            modulation_data=[],
            terminal_conditions=terminal_specs,
            meter_name_to_index=meter_name_to_index,
            device=self.device,
        )

        # Cache action mask table (24 × affordance_count) for temporal mechanics
        self.action_mask_table = self.optimization_data.action_mask_table.to(self.device).clone()
        self.hours_per_day = self.action_mask_table.shape[0] if self.action_mask_table.ndim > 0 else 24

        # Initialize affordance engine with modern affordances (effect_pipeline support).
        # Adapt v2.1 per-level affordances (AffordancesV2Config) into runtime AffordanceConfig.
        from townlet.environment.affordance_config import AffordanceConfig as RuntimeAffordanceConfig

        # Build lookup from environment.yaml affordance vocabulary for categories.
        env_affordance_categories: dict[str, str] = {a.name: a.category for a in self.universe.environment.environment.affordances}

        runtime_affordances: list[RuntimeAffordanceConfig] = []
        for aff in level.affordances.affordances:
            if aff.opening_hours is None:
                raise ValueError(f"affordance '{aff.name}' missing opening_hours (no defaults allowed)")

            # v2.1 affordances are single-tick; enforce explicit interaction type.
            interaction_type = "instant"

            # Derive operating_hours from OpeningHoursConfig:
            # - enabled=false → 24/7 (0–24)
            # - enabled=true → use first schedule window [start, end]
            opening = aff.opening_hours
            if not opening.enabled or not opening.schedule:
                operating_hours = [0, 24]
            else:
                window = opening.schedule[0]
                operating_hours = [window.start, window.end]

            # Map deployment positions to a single canonical position for runtime.
            deployment = aff.deployment
            raw_position = None
            if deployment.type == "fixed" and deployment.positions:
                # Use the first configured position as canonical; optimization data may refine this later.
                raw_position = deployment.positions[0]

            category = env_affordance_categories.get(aff.name, "")

            runtime_affordances.append(
                RuntimeAffordanceConfig(
                    id=aff.name,
                    name=aff.name,
                    category=category,
                    interaction_type=interaction_type,
                    duration_ticks=None,
                    costs=[{"meter": m, "amount": v} for m, v in (aff.costs or {}).items()],
                    effects=[{"meter": m, "amount": v} for m, v in (aff.effects or {}).items()],
                    effects_per_tick=[],
                    costs_per_tick=[],
                    completion_bonus=[],
                    operating_hours=operating_hours,
                    teaching_note=getattr(aff, "teaching_note", None),
                    design_intent=None,
                    position=raw_position,
                )
            )

        # Affordance vocabulary and positions from compiled metadata
        metadata_affordance_lookup = dict(self.metadata.affordance_id_to_index)
        self.affordance_name_to_id = {aff.name: aff.id for aff in runtime_affordances}
        self.affordance_name_to_mask_idx = {
            name: metadata_affordance_lookup.get(aff_id)
            for name, aff_id in self.affordance_name_to_id.items()
            if metadata_affordance_lookup.get(aff_id) is not None
        }
        self.affordance_positions_from_config = {aff.name: getattr(aff, "position", None) for aff in runtime_affordances}
        optimization_position_map = getattr(self.optimization_data, "affordance_position_map", {})
        self.affordance_positions_from_optimization = {
            name: optimization_position_map.get(aff_id) for name, aff_id in self.affordance_name_to_id.items()
        }

        all_affordance_names = [aff.name for aff in runtime_affordances]
        affordance_names_to_deploy = _resolve_deployable_affordances(
            all_affordance_names,
            training_cfg.enabled_affordances,
            self.affordance_name_to_id,
        )

        default_position = torch.zeros(self.substrate.position_dim, dtype=self.substrate.position_dtype, device=self.device)
        self.affordances = {name: default_position.clone() for name in affordance_names_to_deploy}
        self.affordance_names = all_affordance_names
        self.num_affordance_types = len(all_affordance_names)

        # Build modulation rules mapping to affordance names
        modulation_rules = []
        for entry in self.optimization_data.modulation_data:
            aff_idx = entry.get("affordance_idx")
            bar_idx = entry.get("bar_idx")
            if aff_idx is None or bar_idx is None:
                continue
            if aff_idx < 0 or aff_idx >= len(all_affordance_names):
                continue
            aff_name = all_affordance_names[aff_idx]
            modulation_rules.append(
                {
                    "affordance": aff_name,
                    "bar_idx": bar_idx,
                    "threshold": entry.get("threshold", 0.0),
                    "min_multiplier": entry.get("min_multiplier", 1.0),
                }
            )

        self.affordance_engine = AffordanceEngine(
            tuple(runtime_affordances),
            num_agents,
            self.device,
            self.meter_name_to_index,
            modulation_rules=modulation_rules,
        )

        # Build composed action space from compiler metadata and substrate defaults
        self.action_space = self._build_action_space_from_metadata(
            universe.action_space_metadata,
            self.substrate,
        )
        self.action_dim = self.action_space.action_dim
        self.interact_action_idx = self.action_space.get_action_by_name("INTERACT").id
        self.wait_action_idx = self.action_space.get_action_by_name("WAIT").id
        self.up_z_action_idx = self._get_optional_action_idx("UP_Z")
        self.down_z_action_idx = self._get_optional_action_idx("DOWN_Z")
        self._movement_deltas = self._build_movement_deltas()

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
        self.intrinsic_weights = torch.ones(self.num_agents, dtype=torch.float32, device=self.device)  # Default: 1.0 (full exploration)

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

    def _get_optional_action_idx(self, action_name: str) -> int | None:
        """Return action index if available in composed action space."""
        try:
            return self.action_space.get_action_by_name(action_name).id
        except ValueError:
            return None

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

        if not self.enable_temporal_mechanics:
            return True

        if self.action_mask_table.shape[1] == 0:
            return False

        idx = self.affordance_name_to_mask_idx.get(affordance_name)
        if idx is None or idx >= self.action_mask_table.shape[1]:
            # Missing metadata should not block interactions
            return True

        active_hour = self.time_of_day if hour is None else hour
        hour_idx = active_hour % self.hours_per_day
        return bool(self.action_mask_table[hour_idx, idx].item())

    def _compose_action_space(
        self,
        global_actions: ActionSpaceConfig,
        enabled_action_names: list[str] | None,
    ) -> ComposedActionSpace:
        """Legacy builder path is unused in v2.1 runtime."""
        raise NotImplementedError("use _build_action_space_from_metadata in v2.1 runtime")

    def _build_action_space_from_metadata(
        self,
        action_metadata: ActionSpaceMetadata,
        substrate: SpatialSubstrate,
    ) -> ComposedActionSpace:
        """Build ComposedActionSpace using compiler action metadata + substrate default actions."""
        from townlet.environment.action_config import ActionConfig

        actions: list[ActionConfig] = []
        substrate_actions = substrate.get_default_actions()
        substrate_names = [a.name for a in substrate_actions]

        enabled_lookup = {a.name: a.enabled for a in action_metadata.actions}
        id_lookup = {a.name: a.id for a in action_metadata.actions}
        type_lookup = {a.name: a.type for a in action_metadata.actions}
        source_lookup = {a.name: a.source for a in action_metadata.actions}

        for action in substrate_actions:
            if action.name not in id_lookup:
                raise ValueError(f"Action '{action.name}' missing from compiler metadata; no defaults allowed.")
            enabled = enabled_lookup.get(action.name, True)
            action.id = id_lookup[action.name]
            action.enabled = enabled
            action.type = type_lookup.get(action.name, action.type)
            action.source = source_lookup.get(action.name, "substrate")
            actions.append(action)

        for meta_action in action_metadata.actions:
            if meta_action.name in substrate_names:
                continue
            if meta_action.type == "movement":
                raise ValueError(
                    f"Custom movement action '{meta_action.name}' is not supported without explicit delta/teleport; "
                    "define it in the substrate defaults instead."
                )
            action = ActionConfig(
                id=meta_action.id,
                name=meta_action.name,
                type=meta_action.type,
                costs={},
                effects={},
                delta=None,
                teleport_to=None,
                enabled=meta_action.enabled,
                description=meta_action.description or None,
                icon=None,
                source=meta_action.source,
                source_affordance=None,
                reads=[],
                writes=[],
            )
            actions.append(action)

        actions = sorted(actions, key=lambda a: a.id)
        substrate_action_count = len(substrate_actions)
        custom_action_count = len(actions) - substrate_action_count

        return ComposedActionSpace(
            actions=actions,
            substrate_action_count=substrate_action_count,
            custom_action_count=custom_action_count,
            affordance_action_count=0,
            enabled_action_names=None,
        )

    def _build_movement_deltas(self) -> torch.Tensor:
        """Build movement delta tensor from substrate default actions.

        Returns:
            [action_space_size, position_dim] tensor of movement deltas
        """
        action_space_size = self.action_space.action_dim
        position_dim = self.substrate.position_dim

        # Initialize zero deltas for all actions
        deltas = torch.zeros(
            (action_space_size, position_dim),
            device=self.device,
            dtype=self.substrate.position_dtype,
        )

        # Fill in deltas from any action that declares a delta
        for action in self.action_space.actions:
            if action.delta is not None:
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
        self.intrinsic_weights = torch.ones(self.num_agents, dtype=torch.float32, device=self.device)  # Reset to 1.0

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

        return self._get_observations()

    @classmethod
    def from_universe(
        cls,
        universe: CompiledUniverse,
        level_name: str | None = None,
        *,
        num_agents: int,
        device: torch.device | str = "cpu",
    ) -> VectorizedHamletEnv:
        """Instantiate environment using metadata from a compiled universe.

        Args:
            universe: CompiledUniverse with hierarchical configs
            level_name: Which curriculum level to instantiate. If None, defaults to the
                first curriculum level declared in experiment.yaml, falling back to the
                first available compiled level.
            num_agents: Number of parallel agents
            device: PyTorch device

        Returns:
            VectorizedHamletEnv instance
        """

        torch_device = torch.device(device) if isinstance(device, str) else device

        # Backwards compatibility: allow callers to omit level_name and use a sensible default.
        # Prefer the experiment.yaml curriculum_levels ordering when available, otherwise
        # fall back to the first available compiled level.
        if level_name is None:
            default_level: str | None = None

            # Prefer experiment-level ordering if present
            try:
                curriculum_levels = getattr(universe.experiment, "experiment").curriculum_levels
            except Exception:
                curriculum_levels = []

            available_levels = set(universe.available_levels)
            for candidate in curriculum_levels:
                if candidate in available_levels:
                    default_level = candidate
                    break

            # Fallback: first available compiled level
            if default_level is None:
                if not universe.available_levels:
                    raise ValueError(
                        "CompiledUniverse has no curriculum levels. " "Pass level_name explicitly to VectorizedHamletEnv.from_universe()."
                    )
                default_level = universe.available_levels[0]

            level_name = default_level

        return cls(
            universe=universe,
            level_name=level_name,
            num_agents=num_agents,
            device=torch_device,
        )

    def _get_observations(self) -> torch.Tensor:
        """
        Construct observation vector using compiled observation spec.
        """
        import math

        obs_fields = self.observation_spec.fields
        outputs: list[torch.Tensor] = []

        for field in obs_fields:
            name = field.name
            dims = field.dims

            if name == "obs_grid_encoding":
                if self.partial_observability:
                    value = torch.zeros((self.num_agents, dims), device=self.device)
                else:
                    if hasattr(self.substrate, "_encode_full_grid"):
                        grid_encoding = self.substrate._encode_full_grid(self.positions, self.affordances)
                    else:
                        grid_encoding = self.substrate.encode_observation(self.positions, self.affordances)
                    value = grid_encoding
            elif name == "obs_local_window":
                if not self.partial_observability:
                    value = torch.zeros((self.num_agents, dims), device=self.device)
                else:
                    local_window = self.substrate.encode_partial_observation(
                        self.positions,
                        self.affordances,
                        vision_range=self.vision_radius,
                    )
                    value = local_window
            elif name == "obs_position":
                pos = self._encode_position_observation()
                if pos is None:
                    value = torch.zeros((self.num_agents, dims), device=self.device)
                else:
                    # Align encoded dims with spec dims defensively.
                    if pos.dim() == 1:
                        pos = pos.unsqueeze(1)
                    if pos.shape[1] == dims:
                        value = pos
                    elif pos.shape[1] > dims:
                        value = pos[:, :dims]
                    else:
                        value = torch.zeros((self.num_agents, dims), device=self.device)
                        value[:, : pos.shape[1]] = pos
            elif name == "obs_velocity":
                vel = self._encode_velocity_observation()
                if vel is None:
                    value = torch.zeros((self.num_agents, dims), device=self.device)
                else:
                    if vel.dim() == 1:
                        vel = vel.unsqueeze(1)
                    if vel.shape[1] == dims:
                        value = vel
                    elif vel.shape[1] > dims:
                        value = vel[:, :dims]
                    else:
                        value = torch.zeros((self.num_agents, dims), device=self.device)
                        value[:, : vel.shape[1]] = vel
            elif name == "obs_meters":
                value = self.meters
            elif name in {"obs_affordance_at_position", "obs_affordances"}:
                value = self._build_affordance_encoding(dims)
            elif name == "obs_temporal":
                # Temporal observation behavior:
                # - If temporal_support is disabled at experiment level, obs_temporal should not exist.
                # - If support enabled but curriculum marks temporal inactive, emit all zeros (masked).
                # - If support enabled and temporal is active, emit full rich encoding.
                if not self.temporal_support_enabled or not self.enable_temporal_mechanics:
                    value = torch.zeros((self.num_agents, dims), device=self.device)
                else:
                    time_of_day = self.time_of_day
                    day_length = float(self.day_length)
                    time_angle = (time_of_day / day_length) * 2 * math.pi
                    time_sin = torch.tensor(math.sin(time_angle), device=self.device)
                    time_cos = torch.tensor(math.cos(time_angle), device=self.device)
                    day_progress = float(time_of_day) / day_length
                    # Simple day/night split relative to configured day_length:
                    # first quarter and last quarter of the day are treated as night.
                    night_threshold = day_length * 0.25
                    is_night = 1.0 if time_of_day < night_threshold or time_of_day >= (day_length - night_threshold) else 0.0

                    # Populate rich temporal encoding, padding/truncating to dims as needed.
                    value = torch.zeros((self.num_agents, dims), device=self.device)
                    if dims > 0:
                        value[:, 0] = time_sin
                    if dims > 1:
                        value[:, 1] = time_cos
                    if dims > 2:
                        value[:, 2] = day_progress
                    if dims > 3:
                        value[:, 3] = is_night
            else:
                # Environment variables mapping: expect variables named by obs field
                if name not in self.vfs_registry._definitions:
                    raise ValueError(f"Observation field '{name}' not found in VFS variables (no defaults allowed).")
                val = self.vfs_registry.get(name, reader="engine")
                value = val if val.dim() > 1 else val.unsqueeze(1)

            if value.dim() == 1:
                value = value.unsqueeze(1)
            outputs.append(value)

        observations = torch.cat(outputs, dim=1)

        # Apply curriculum activity mask as a final safety net to ensure masked
        # dimensions are zeroed, even if individual field encoders evolve.
        activity = getattr(self, "observation_activity", None)
        if activity is not None and activity.active_mask:
            if len(activity.active_mask) != observations.shape[1]:
                raise ValueError(
                    "ObservationActivity mask length does not match observation_dim.\n"
                    f"  mask_len={len(activity.active_mask)}, obs_dim={observations.shape[1]}"
                )
            mask = torch.tensor(activity.active_mask, device=self.device, dtype=observations.dtype)
            observations = observations * mask.unsqueeze(0)

        return observations

    def _build_affordance_encoding(self, dims: int) -> torch.Tensor:
        """Build one-hot encoding of current affordance under each agent.

        This encodes against the FULL affordance vocabulary (from affordances.yaml),
        not just deployed affordances. This ensures observation dimensions stay
        constant across curriculum levels.

        Returns:
            encoding: [num_agents, num_affordance_types + 1]
                One-hot over affordance types plus explicit \"none\" category.
        """
        # Total affordance classes (excluding the explicit "none" slot)
        num_types = self.num_affordance_types
        total_dims = num_types + 1

        # Initialize all zeros; last column is reserved for "none".
        affordance_encoding = torch.zeros(self.num_agents, total_dims, device=self.device)

        # Iterate over full affordance vocabulary (not just deployed positions).
        for affordance_idx, affordance_name in enumerate(self.affordance_names):
            if affordance_name in self.affordances:
                affordance_pos = self.affordances[affordance_name]
                on_affordance = self.substrate.is_on_position(self.positions, affordance_pos)
                if on_affordance.any():
                    affordance_encoding[on_affordance, affordance_idx] = 1.0

        # Agents not on any affordance get "none" category = 1.0 in last slot.
        row_sums = affordance_encoding.sum(dim=1)
        none_mask = row_sums == 0
        affordance_encoding[none_mask, num_types] = 1.0

        # Align with spec dims defensively (older artifacts may differ).
        if dims == total_dims:
            return affordance_encoding
        if dims < total_dims:
            return affordance_encoding[:, :dims]

        padded = torch.zeros(self.num_agents, dims, device=self.device)
        padded[:, :total_dims] = affordance_encoding
        return padded

    def _encode_position_observation(self) -> torch.Tensor | None:
        """Encode agent position using substrate-native semantics.

        Returns:
            [num_agents, position_dim] tensor or None for aspatial substrates.
        """
        # Aspatial substrates have no positional encoding.
        if getattr(self.substrate, "position_dim", 0) == 0:
            return None

        # Prefer normalized coordinates so obs_position dims match substrate.position_dim
        # independent of observation_encoding (relative/scaled/absolute).
        normalizer = getattr(self.substrate, "normalize_positions", None)
        if callable(normalizer):
            typed_normalizer = cast(Callable[[torch.Tensor], torch.Tensor], normalizer)
            return typed_normalizer(self.positions)

        # Fallbacks: position feature encoders (may include extra metadata).
        encode_fn = Callable[[torch.Tensor, dict[str, torch.Tensor]], torch.Tensor]

        encoder = getattr(self.substrate, "_encode_position_features", None)
        if callable(encoder):
            typed_encoder = cast(encode_fn, encoder)
            return typed_encoder(self.positions, self.affordances)

        public_encoder = getattr(self.substrate, "encode_position_features", None)
        if callable(public_encoder):
            typed_public = cast(encode_fn, public_encoder)
            return typed_public(self.positions, self.affordances)

        encode_observation = getattr(self.substrate, "encode_observation", None)
        if callable(encode_observation):
            typed_encode_obs = cast(encode_fn, encode_observation)
            return typed_encode_obs(self.positions, self.affordances)

        return None

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
        velocity = getattr(self, "_velocity")
        if velocity is None:
            return torch.zeros(
                (self.num_agents, self.substrate.position_dim),
                dtype=torch.float32,
                device=self.device,
            )
        return velocity

    def get_action_masks(self) -> torch.Tensor:
        """
        Get action masks for all agents (invalid actions = False).

        Action masking prevents agents from selecting movements that would
        take them off the grid. This saves exploration budget and speeds learning.

        Returns:
            action_masks: [num_agents, action_dim] bool tensor
                True = valid action, False = invalid
                Grid2D (6 actions): [UP, DOWN, LEFT, RIGHT, INTERACT, WAIT]
                Grid3D (8 actions): [UP, DOWN, LEFT, RIGHT, UP_Z, DOWN_Z, INTERACT, WAIT]
        """
        # Start with base mask (disabled actions = False)
        action_masks = self.action_space.get_base_action_mask(
            num_agents=self.num_agents,
            device=self.device,
        )

        # Check boundary constraints (only for discrete grid substrates)
        # Continuous substrates handle boundaries in apply_movement() via boundary modes
        if self.grid_size is not None and self.substrate.position_dim >= 2:
            # positions[:, 0] = x (column), positions[:, 1] = y (row)
            at_top = self.positions[:, 1] == 0  # y == 0
            at_bottom = self.positions[:, 1] == self.grid_size - 1  # y == max
            at_left = self.positions[:, 0] == 0  # x == 0
            at_right = self.positions[:, 0] == self.grid_size - 1  # x == max

            # Mask invalid movements
            action_masks[at_top, 0] = False  # Can't go UP at top edge
            action_masks[at_bottom, 1] = False  # Can't go DOWN at bottom edge
            action_masks[at_left, 2] = False  # Can't go LEFT at left edge
            action_masks[at_right, 3] = False  # Can't go RIGHT at right edge

        # 3D-specific: mask Z-axis movements at floor/ceiling (discrete grids only)
        if self.grid_size is not None and self.substrate.position_dim == 3:
            at_floor = self.positions[:, 2] == 0  # z == 0
            # Assume depth from substrate
            if hasattr(self.substrate, "depth"):
                at_ceiling = self.positions[:, 2] == self.substrate.depth - 1
            else:
                at_ceiling = torch.zeros(self.num_agents, dtype=torch.bool, device=self.device)

            if self.up_z_action_idx is not None:
                action_masks[at_ceiling, self.up_z_action_idx] = False  # Can't go UP_Z at ceiling
            if self.down_z_action_idx is not None:
                action_masks[at_floor, self.down_z_action_idx] = False  # Can't go DOWN_Z at floor

        # Mask INTERACT - only valid when on an open affordance
        # P1.4: Removed affordability check - agents can attempt INTERACT even when broke
        # Affordability is checked inside interaction handlers; failing to afford just
        # wastes a turn (passive decay) and teaches economic planning

        # Use cached INTERACT index (from ActionSpaceBuilder)
        interact_action_idx = self.interact_action_idx

        on_valid_affordance = torch.zeros(self.num_agents, dtype=torch.bool, device=self.device)

        # Check each affordance using AffordanceEngine
        for affordance_name, affordance_pos in self.affordances.items():
            if self.enable_temporal_mechanics and not self._is_affordance_open(affordance_name):
                continue

            on_this_affordance = self.substrate.is_on_position(self.positions, affordance_pos)
            on_valid_affordance |= on_this_affordance

        base_interact_mask = action_masks[:, interact_action_idx].clone()
        # Respect config-disabled INTERACT entries by preserving the base mask.
        action_masks[:, interact_action_idx] = base_interact_mask & on_valid_affordance

        # P3.1: Mask all actions for dead agents according to terminal conditions.
        # This must be LAST to override all other masking. Terminal conditions are
        # defined in bars.yaml (lethal_min/lethal_max) and enforced by MeterDynamics;
        # we use the env's dones flag as single source of truth instead of hardcoded
        # meter names.
        if hasattr(self, "dones"):
            action_masks[self.dones] = False

        return action_masks

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
        # 1. Execute actions and track successful interactions
        successful_interactions = self._execute_actions(actions)

        # 2. Deplete meters (base passive decay with curriculum difficulty)
        self.meters = self.meter_dynamics.deplete_meters(self.meters, depletion_multiplier)

        # 3. Cascading effects (coupled differential equations!)
        self.meters = self.meter_dynamics.apply_secondary_to_primary_effects(self.meters)
        self.meters = self.meter_dynamics.apply_tertiary_to_secondary_effects(self.meters)
        self.meters = self.meter_dynamics.apply_tertiary_to_primary_effects(self.meters)

        # 4. Check terminal conditions
        self.dones = self.meter_dynamics.check_terminal_conditions(self.meters, self.dones)

        # 5. Increment step counts (before retirement check)
        self.step_counts += 1

        # 5.5. Check for retirement (reached maximum lifespan)
        # Agents that reach their lifespan retire with a bonus reward
        retired = self.step_counts >= self.agent_lifespan

        # 6. Calculate rewards (interoception-aware)
        rewards = self._calculate_shaped_rewards()
        rewards = torch.where(retired, rewards + 1.0, rewards)  # +1 retirement bonus
        self.dones = torch.logical_or(self.dones, retired)

        # 6. Increment time of day only when temporal mechanics are active.
        if self.enable_temporal_mechanics:
            self.time_of_day = (self.time_of_day + 1) % int(self.day_length)
        else:
            self.time_of_day = 0

        observations = self._get_observations()

        info = {
            "step_counts": self.step_counts.clone(),
            "positions": self.positions.clone(),
            "successful_interactions": successful_interactions,  # {agent_idx: affordance_name}
        }

        return observations, rewards, self.dones, info

    def _execute_actions(self, actions: torch.Tensor) -> dict:
        """
        Execute movement, interaction, and wait actions.

        Args:
            actions: [num_agents] tensor
                0=UP, 1=DOWN, 2=LEFT, 3=RIGHT, 4=INTERACT, 5=WAIT

        Returns:
            Dictionary mapping agent indices to affordance names for successful interactions
        """
        # === CUSTOM ACTION DISPATCH (early) ===
        # Custom actions start after substrate actions
        custom_action_start_id = self.action_space.substrate_action_count
        custom_mask = actions >= custom_action_start_id

        if custom_mask.any():
            custom_agent_indices = torch.where(custom_mask)[0]
            for agent_idx in custom_agent_indices:
                action_id = int(actions[agent_idx].item())
                action = self.action_space.get_action_by_id(action_id)

                # Apply custom action costs/effects/teleportation
                self._apply_custom_action(agent_idx, action)

        # Store old positions for temporal mechanics progress tracking AND velocity calculation
        old_positions = self.positions.clone()

        # Apply movement using pre-built delta tensor from ActionConfig
        # Only for substrate actions (custom actions already handled above)
        substrate_mask = actions < custom_action_start_id
        if substrate_mask.any():
            movement_deltas = self._movement_deltas[actions[substrate_mask]]  # [num_substrate_agents, position_dim]
            self.positions[substrate_mask] = self.substrate.apply_movement(self.positions[substrate_mask], movement_deltas)

        # Calculate velocity (movement delta since last step)
        # Cast to float32 (grid substrates use int positions, continuous use float)
        velocity = (self.positions - old_positions).float()  # [num_agents, position_dim]
        self._velocity = velocity

        # Write velocity components to VFS (if velocity variables exist)
        # Scalar variables require shape (num_agents,) not (num_agents, 1)
        if "velocity_x" in self.vfs_registry._definitions:
            self.vfs_registry.set("velocity_x", velocity[:, 0], writer="engine")

        if "velocity_y" in self.vfs_registry._definitions and velocity.shape[1] >= 2:
            self.vfs_registry.set("velocity_y", velocity[:, 1], writer="engine")

        if "velocity_z" in self.vfs_registry._definitions and velocity.shape[1] >= 3:
            self.vfs_registry.set("velocity_z", velocity[:, 2], writer="engine")

        # Calculate and write velocity magnitude (speed)
        if "velocity_magnitude" in self.vfs_registry._definitions:
            magnitude = torch.norm(velocity, dim=1)  # [num_agents]
            self.vfs_registry.set("velocity_magnitude", magnitude, writer="engine")

        # Reset progress for agents that moved away (temporal mechanics)
        if self.enable_temporal_mechanics:
            for agent_idx in range(self.num_agents):
                if not torch.equal(old_positions[agent_idx], self.positions[agent_idx]):
                    self.interaction_progress[agent_idx] = 0
                    self.last_interaction_affordance[agent_idx] = None

        # Apply action costs (configurable)
        # Determine movement actions directly from the movement deltas to support
        # substrates where non-movement actions appear before all movement actions
        # (e.g., 3D where INTERACT/WAIT sit at indices < last movement deltas).
        # Only apply to substrate actions (not custom actions)
        movement_actions = self._movement_deltas.ne(0).any(dim=1)
        # Create a full mask (initialize to False for all agents)
        movement_mask = torch.zeros(self.num_agents, dtype=torch.bool, device=self.device)
        # Only check movement for substrate actions
        if substrate_mask.any():
            movement_mask[substrate_mask] = movement_actions[actions[substrate_mask]]
        if movement_mask.any():
            # Create dynamic cost tensor from bars.yaml (per-level BarsV2Config).
            movement_costs = torch.zeros(self.meter_count, device=self.device)
            for bar in self.bars_config.meters:
                idx = self.meter_name_to_index.get(bar.name)
                if idx is not None:
                    movement_costs[idx] = float(bar.depletion.move)

            self.meters[movement_mask] -= movement_costs.unsqueeze(0)
            self.meters = torch.clamp(self.meters, 0.0, 1.0)

        # WAIT action - NO additional cost
        # WAIT only pays base_depletion (handled by MeterDynamics), no action-specific cost
        # This is architecturally correct: WAIT = existence without action

        # Handle INTERACT actions
        # Use cached INTERACT index (from ActionSpaceBuilder)
        interact_action_idx = self.interact_action_idx

        successful_interactions = {}
        interact_mask = (actions == interact_action_idx) & substrate_mask
        if interact_mask.any():
            # Apply interaction costs from bars.yaml (per-level BarsV2Config).
            interaction_costs = torch.zeros(self.meter_count, device=self.device)
            for bar in self.bars_config.meters:
                idx = self.meter_name_to_index.get(bar.name)
                if idx is not None:
                    interaction_costs[idx] = float(bar.depletion.interact)

            self.meters[interact_mask] -= interaction_costs.unsqueeze(0)
            self.meters = torch.clamp(self.meters, 0.0, 1.0)

            successful_interactions = self._handle_interactions(interact_mask)

        return successful_interactions

    def _handle_interactions(self, interact_mask: torch.Tensor) -> dict:
        """
        Handle INTERACT actions with multi-tick accumulation.

        Args:
            interact_mask: [num_agents] bool mask

        Returns:
            Dictionary mapping agent indices to affordance names
        """
        if not self.enable_temporal_mechanics:
            # No temporal mechanics: always use instant interactions.
            return self._handle_instant_interactions(interact_mask)

        # If temporal mechanics are enabled but there are no multi-tick affordances
        # (interaction_type in {"multi_tick", "dual"}), treat interactions as instant
        # with time-of-day gating only.
        if not any(getattr(aff, "interaction_type", "instant") in {"multi_tick", "dual"} for aff in self.affordance_engine.affordances):
            return self._handle_instant_interactions(interact_mask)

        # Multi-tick interaction logic using AffordanceEngine
        successful_interactions: dict[int, str] = {}

        for affordance_name, affordance_pos in self.affordances.items():
            if not self._is_affordance_open(affordance_name):
                continue

            # Check if still on same affordance (using substrate)
            at_affordance = self.substrate.is_on_position(self.positions, affordance_pos) & interact_mask

            if not at_affordance.any():
                continue

            # Check affordability using AffordanceEngine
            cost_per_tick = self.affordance_engine.get_affordance_cost(affordance_name, cost_mode="per_tick")
            # TASK-001: Use dynamic money index (if money meter exists)
            if self.money_idx is not None:
                can_afford = self.meters[:, self.money_idx] >= cost_per_tick
                at_affordance = at_affordance & can_afford
            # else: no money meter, affordability always passes

            if not at_affordance.any():
                continue

            # Get duration ticks from AffordanceEngine
            duration_ticks = self.affordance_engine.get_duration_ticks(affordance_name)

            # Track successful interactions
            agent_indices = torch.where(at_affordance)[0]

            for agent_idx in agent_indices:
                agent_idx_int = agent_idx.item()
                current_pos = self.positions[agent_idx]

                # Check if continuing same affordance at same position
                if self.last_interaction_affordance[agent_idx_int] == affordance_name and torch.equal(
                    current_pos, self.last_interaction_position[agent_idx_int]
                ):
                    # Continue progress
                    self.interaction_progress[agent_idx] += 1
                else:
                    # New affordance - reset progress
                    self.interaction_progress[agent_idx] = 1
                    self.last_interaction_affordance[agent_idx_int] = affordance_name
                    self.last_interaction_position[agent_idx_int] = current_pos.clone()

                ticks_done = int(self.interaction_progress[agent_idx].item())

                # Create single-agent mask for this agent
                single_agent_mask = torch.zeros(self.num_agents, dtype=torch.bool, device=self.device)
                single_agent_mask[agent_idx] = True

                # Apply multi-tick interaction using AffordanceEngine
                # This applies per-tick effects and costs
                self.meters = self.affordance_engine.apply_multi_tick_interaction(
                    meters=self.meters,
                    affordance_name=affordance_name,
                    current_tick=ticks_done - 1,  # 0-indexed
                    agent_mask=single_agent_mask,
                    check_affordability=False,  # Already checked above
                )

                # Reset progress if completed
                if ticks_done == duration_ticks:
                    self.interaction_progress[agent_idx] = 0
                    self.last_interaction_affordance[agent_idx_int] = None

                successful_interactions[agent_idx_int] = affordance_name

        # Update affordance tracking after all interactions
        self._update_affordance_tracking(successful_interactions)

        return successful_interactions

    def _handle_instant_interactions(self, interact_mask: torch.Tensor) -> dict:
        """
        Handle INTERACT action at affordances (instant mode - no temporal mechanics).

        Uses AffordanceEngine for all logic - no hardcoded costs!

        Args:
            interact_mask: [num_agents] bool mask

        Returns:
            Dictionary mapping agent indices to affordance names for successful interactions
        """
        # Track successful interactions for this step
        successful_interactions = {}  # {agent_idx: affordance_name}

        # Check each affordance
        for affordance_name, affordance_pos in self.affordances.items():
            if self.enable_temporal_mechanics and not self._is_affordance_open(affordance_name):
                continue

            # Check which agents are on this affordance (using substrate)
            at_affordance = self.substrate.is_on_position(self.positions, affordance_pos) & interact_mask

            if not at_affordance.any():
                continue

            # Check affordability using AffordanceEngine
            cost_normalized = self.affordance_engine.get_affordance_cost(affordance_name, cost_mode="instant")
            if cost_normalized > 0:
                # TASK-001: Use dynamic money index (if money meter exists)
                if self.money_idx is not None:
                    can_afford = self.meters[:, self.money_idx] >= cost_normalized
                    at_affordance = at_affordance & can_afford
                # else: no money meter, affordability always passes

                if not at_affordance.any():
                    # No one at this affordance can afford it, skip
                    continue

            # Track successful interactions
            agent_indices = torch.where(at_affordance)[0]
            for agent_idx in agent_indices:
                successful_interactions[agent_idx.item()] = affordance_name

            # Apply affordance effects using AffordanceEngine
            self.meters = self.affordance_engine.apply_interaction(
                meters=self.meters,
                affordance_name=affordance_name,
                agent_mask=at_affordance,
            )

        # Update affordance tracking after all interactions
        self._update_affordance_tracking(successful_interactions)

        return successful_interactions

    def _calculate_shaped_rewards(self) -> torch.Tensor:
        """Calculate total rewards using DACEngine.

        Computes: extrinsic + (intrinsic × modifiers) + shaping bonuses

        Returns:
            rewards: [num_agents] final rewards
        """
        # Gather intrinsic raw values from exploration module (if available)
        if self.exploration_module is not None:
            # Get current observations for intrinsic reward computation
            observations = self._get_observations()
            # BUG-22 FIX: Update stats during training rollouts so normalization tracks distribution
            intrinsic_raw = self.exploration_module.compute_intrinsic_rewards(observations, update_stats=True)
        else:
            # Fallback to zeros if no exploration module is set
            intrinsic_raw = torch.zeros(self.num_agents, device=self.device)

        # Gather additional context for shaping bonuses
        # Use float positions so DACEngine distance computations operate in a
        # consistent continuous space (grid indices or continuous coords).
        agent_positions = self.positions.to(device=self.device, dtype=torch.float32)

        kwargs = {
            "agent_positions": agent_positions,
            "affordance_positions": self._get_affordance_positions(),
            "last_action_affordance": self._get_last_action_affordances(),
            "affordance_streak": self._get_affordance_streaks(),
            "unique_affordances_used": self._get_unique_affordances_used(),
        }

        # Add temporal context if temporal mechanics enabled
        if self.enable_temporal_mechanics:
            kwargs["current_hour"] = self.time_of_day

        # Calculate rewards using DACEngine
        total_rewards, intrinsic_weights, components = self.dac_engine.calculate_rewards(
            step_counts=self.step_counts,
            dones=self.dones,
            meters=self.meters,
            intrinsic_raw=intrinsic_raw,
            **kwargs,
        )

        # Store intrinsic weights for population-level annealing
        self.intrinsic_weights = intrinsic_weights

        # Store components for logging (optional)
        self._last_reward_components = components

        return total_rewards

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

    def _get_meter_index(self, meter_name: str) -> int | None:
        """Get meter index by name.

        Args:
            meter_name: Meter name (e.g., "energy", "mood")

        Returns:
            Meter index, or None if meter doesn't exist
        """
        mapping: dict[str, int] | None = getattr(self, "meter_name_to_index", None)
        if mapping is None:
            return None
        result: int | None = mapping.get(meter_name)
        return result

    def _apply_custom_action(self, agent_idx: int, action: ActionConfig):
        """Apply custom action effects, movement delta, and teleportation.

        Args:
            agent_idx: Agent index
            action: Custom action config
        """
        # Apply costs (negative costs = restoration)
        for meter_name, cost in action.costs.items():
            meter_idx = self._get_meter_index(meter_name)
            if meter_idx is not None:
                self.meters[agent_idx, meter_idx] -= cost  # Subtract cost (negative = add)

        # Apply effects
        for meter_name, effect in action.effects.items():
            meter_idx = self._get_meter_index(meter_name)
            if meter_idx is not None:
                self.meters[agent_idx, meter_idx] += effect  # Add effect

        # Apply movement delta (for movement-type custom actions like SPRINT)
        if action.delta is not None:
            delta_tensor = torch.tensor(action.delta, device=self.device, dtype=self.substrate.position_dtype)
            new_position = self.substrate.apply_movement(self.positions[agent_idx : agent_idx + 1], delta_tensor.unsqueeze(0))
            self.positions[agent_idx] = new_position.squeeze(0)

        # Handle teleportation (overrides movement delta if both present)
        if action.teleport_to is not None:
            target_pos = torch.tensor(
                action.teleport_to,
                device=self.device,
                dtype=self.substrate.position_dtype,
            )
            self.positions[agent_idx] = target_pos

        # Clamp meters to [0, 1]
        self.meters = torch.clamp(self.meters, 0.0, 1.0)

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
                # Fall back to enumeration to guarantee collision-free placement
                all_positions = self.substrate.get_all_positions()
                random.shuffle(all_positions)
                sampled = torch.stack(
                    [
                        torch.tensor(all_positions[idx], dtype=self.substrate.position_dtype, device=self.device)
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
