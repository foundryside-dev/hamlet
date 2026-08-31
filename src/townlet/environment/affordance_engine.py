"""
AffordanceEngine: Config-driven affordance interaction system.

This module processes affordance interactions using YAML configuration instead
of hardcoded logic.

Architecture:
- Load affordance configs at initialization
- Pre-build lookup maps and tensors for GPU performance
- Apply instant interactions (single-step effects)
- Apply multi-tick interactions (progressive effects)
- Handle operating hours and affordability checks

Teaching Value:
- Students can modify affordances by editing YAML, not Python
- Different affordance sets create different strategic environments
- Demonstrates data-driven game design

Status: Ready for integration with vectorized_env.py
"""

from dataclasses import dataclass
from typing import Any, cast

import torch

from townlet.config.affordances_v2_config import AffordanceParamConfig
from townlet.effects.compiler import CommandCompiler
from townlet.effects.executor import CommandExecutor, ExecutionContext
from townlet.effects.parser import CommandParser
from townlet.effects.schema import CommandNode
from townlet.environment.null_managers import NullItemManager


@dataclass
class CompiledAffordance:
    """Pre-compiled Effects commands for affordance lifecycle stages."""

    on_start: list[CommandNode]
    per_tick: list[CommandNode]
    on_completion: list[CommandNode]
    on_early_exit: list[CommandNode]
    on_failure: list[CommandNode]


class AffordanceEngine:
    """
    Config-driven affordance interaction processor.

    Handles instant and multi-tick affordance interactions based on YAML configuration.
    All operations are vectorized for GPU performance.
    """

    def __init__(
        self,
        affordance_config: tuple[AffordanceParamConfig, ...],
        num_agents: int,
        device: torch.device,
        meter_name_to_idx: dict[str, int],
        modulation_program: Any | None = None,
        vfs_registry: Any | None = None,  # NEW: VFS registry for Effects
        effects_schema: Any | None = None,  # NEW: Effects schema for compilation
        command_executor: CommandExecutor | None = None,  # NEW: Effects executor
        effect_manager: Any | None = None,  # NEW: EffectManager required for Effects commands
        item_manager: Any | None = None,  # NEW: ItemManager required for spawn_item
        affordance_overrides: dict[str, bool] | None = None,  # NEW: dynamic availability toggles
        *,
        meter_bounds_min: torch.Tensor,
        meter_bounds_max: torch.Tensor,
    ):
        """
        Initialize AffordanceEngine.

        Args:
            affordance_config: Tuple of affordances from compiled universe (v2.1 runtime form)
            num_agents: Number of agents in parallel
            device: torch.device for GPU/CPU
            meter_name_to_idx: Mapping of meter names to indices (from bars_config)
            modulation_program: Compiled VTC modulation program for affordance effectiveness
            vfs_registry: VFS registry for Effects system (optional)
            effects_schema: Effects schema for command compilation (optional)
            command_executor: Effects command executor (optional)
            meter_bounds_min: Declared per-meter floors, shape [meter_count]. Required.
            meter_bounds_max: Declared per-meter ceilings, shape [meter_count]. Required.
        """
        self.num_agents = num_agents
        self.device = device
        self.meter_bounds_min = meter_bounds_min
        self.meter_bounds_max = meter_bounds_max

        invalid_affordance_types = sorted(
            {type(affordance).__name__ for affordance in affordance_config if not isinstance(affordance, AffordanceParamConfig)}
        )
        if invalid_affordance_types:
            raise TypeError("AffordanceEngine requires canonical AffordanceParamConfig entries; " f"received {invalid_affordance_types}.")
        self.affordances = affordance_config

        self.meter_name_to_idx = meter_name_to_idx
        self.modulation_program = modulation_program
        self.vfs_registry = vfs_registry  # NEW
        self.command_executor = command_executor  # NEW
        self.effect_manager = effect_manager or NullEffectManager()
        self.item_manager = item_manager or NullItemManager()
        self.affordance_overrides = affordance_overrides

        # Build lookup maps
        self._build_lookup_maps()

        # Compile affordance Effects commands at startup (CRITICAL: Performance)
        self.compiled_affordances: dict[str, CompiledAffordance] = {}

        if command_executor is not None and effects_schema is not None:
            parser = CommandParser()
            compiler = CommandCompiler(schema=effects_schema)

            for affordance in affordance_config:
                compiled = CompiledAffordance(
                    on_start=[],
                    per_tick=[],
                    on_completion=[],
                    on_early_exit=[],
                    on_failure=[],
                )

                for stage in ["on_start", "per_tick", "on_completion", "on_early_exit", "on_failure"]:
                    commands = affordance.interactions.get(stage, [])
                    if commands:
                        command_nodes = parser.parse_commands(commands)
                        compiled_commands = compiler.compile_commands(command_nodes)
                        setattr(compiled, stage, compiled_commands)

                self.compiled_affordances[affordance.name] = compiled

        # Pre-compute tensors for common operations (future optimization)
        # For now, we compute on-the-fly for clarity

    def _build_lookup_maps(self) -> None:
        """
        Build efficient lookup maps for affordances.

        The affordance order is determined BY THE CONFIG FILE, not hardcoded.
        This makes the config the single source of truth.
        """
        # Map affordance name to index (order from config file)
        self.affordance_name_to_idx: dict[str, int] = {}
        self.affordance_map: dict[str, AffordanceParamConfig] = {}

        for idx, aff in enumerate(self.affordances):
            name = aff.name
            self.affordance_name_to_idx[name] = idx
            self.affordance_map[name] = aff

    def apply_instant_interaction(
        self,
        meters: torch.Tensor,
        affordance_name: str,
        agent_mask: torch.Tensor,
        *,
        current_tick: int,
    ) -> torch.Tensor:
        """
        Apply instant affordance interaction.

        Affordability is a PRECONDITION, not an option. The caller gates on
        :meth:`can_afford` and this method asserts it, so the gate and the
        application cannot drift apart. The old ``check_affordability: bool = False``
        made the safe behaviour opt-in and every production caller left it off.

        Args:
            meters: [num_agents, meter_count] current meter values
            affordance_name: Name of affordance (e.g., "Shower")
            agent_mask: [num_agents] bool mask of agents to apply to
            current_tick: Current global tick. REQUIRED and deliberately without a
                default — it seeds the effect command RNG and anchors the scheduler,
                so a missing value silently degrades to tick 0 with no error.

        Returns:
            updated_meters: [num_agents, meter_count] after effects applied

        Raises:
            ValueError: Unknown affordance, wrong interaction type, or any masked
                agent that cannot pay the declared costs.
        """
        affordance = self.affordance_map.get(affordance_name)
        if affordance is None:
            raise ValueError(f"Unknown affordance '{affordance_name}'. Known affordances: {sorted(self.affordance_map)}")

        if affordance.interaction_type != "instant":
            raise ValueError(
                f"Affordance '{affordance_name}' is {affordance.interaction_type}, "
                "not instant. Use apply_vtc_multi_tick_effects instead."
            )

        # Clone meters to avoid modifying input
        updated_meters = meters.clone()

        # Affordability is asserted, never silently narrowed. Narrowing the mask here
        # would let the caller record a completed interaction the engine declined.
        if len(affordance.costs) > 0:
            affordable = self.can_afford(affordance_name, meters, cost_mode="instant")
            offenders = torch.nonzero(agent_mask & ~affordable, as_tuple=False).flatten()
            if offenders.numel() > 0:
                declared = affordance.costs
                raise ValueError(
                    f"Agents {offenders.tolist()} cannot pay for affordance '{affordance_name}'; "
                    f"declared costs {declared}. Gate on can_afford() before applying."
                )

        # Apply costs (modern dict format)
        multipliers = self._compute_affordance_multiplier(affordance.name, meters, agent_mask)
        for meter_name, amount in affordance.costs.items():
            meter_idx = self._get_meter_idx(meter_name, f"affordance '{affordance_name}' cost")
            updated_meters[agent_mask, meter_idx] -= amount * multipliers[agent_mask]

        # Execute compiled Effects commands (on_start stage for instant affordances)
        updated_meters = self._execute_affordance_effects(
            affordance_name,
            "on_start",
            agent_mask,
            updated_meters,
            multipliers=multipliers,
            current_tick=current_tick,
        )

        # Clamp meters to their DECLARED per-meter bounds (WS-1(e)).
        # RETAINED deliberately (PDR-0014 B3 / PDR-0015): this is a real ceiling, not a
        # duplicate of the VTC clamp — do not delete it and do not add a second.
        updated_meters = torch.clamp(updated_meters, self.meter_bounds_min, self.meter_bounds_max)

        return updated_meters

    def _compute_affordance_multiplier(self, affordance_name: str, meters: torch.Tensor, agent_mask: torch.Tensor) -> torch.Tensor:
        """Compute modulation multiplier for a given affordance based on bar values."""
        if self.modulation_program is None:
            active = agent_mask.to(device=meters.device, dtype=torch.bool)
            return torch.where(
                active,
                torch.ones(meters.shape[0], device=meters.device, dtype=meters.dtype),
                torch.zeros(meters.shape[0], device=meters.device, dtype=meters.dtype),
            )

        bars_state = {name: meters[:, idx] for name, idx in self.meter_name_to_idx.items() if 0 <= idx < meters.shape[1]}
        return cast(
            torch.Tensor,
            self.modulation_program.compute_affordance_multiplier(
                affordance_name,
                bars_state,
                active_mask=agent_mask,
                device=meters.device,
            ),
        )

    def apply_vtc_multi_tick_effects(
        self,
        *,
        meters: torch.Tensor,
        affordance_name: str,
        current_tick: int,
        agent_mask: torch.Tensor,
        completion_mask: torch.Tensor,
    ) -> torch.Tensor:
        """
        Apply VTC-selected multi-tick affordance effects for a single tick.

        Args:
            meters: [num_agents, 8] current meter values
            affordance_name: Name of affordance (e.g., "Bed", "Job")
            current_tick: Current tick number selected by VTC [0, duration_ticks-1]
            agent_mask: [num_agents] bool mask of agents to apply to
            completion_mask: [num_agents] bool mask of agents completed by the VTC rule

        Returns:
            updated_meters: [num_agents, 8] after VTC-selected effects are applied
        """
        affordance = self.affordance_map.get(affordance_name)
        if affordance is None:
            return meters

        if affordance.interaction_type != "multi_tick":
            raise ValueError(
                f"Affordance '{affordance_name}' is {affordance.interaction_type}, "
                "not multi_tick. Use apply_instant_interaction instead."
            )

        if completion_mask.shape != agent_mask.shape:
            raise ValueError(f"completion_mask shape {tuple(completion_mask.shape)} must match agent_mask shape {tuple(agent_mask.shape)}")

        # Clone meters
        updated_meters = meters.clone()
        agent_mask = agent_mask.to(device=meters.device, dtype=torch.bool)
        completion_mask = completion_mask.to(device=meters.device, dtype=torch.bool)

        # NO affordability raise on this path, deliberately. Effects are applied a
        # tick at a time after the interaction has already begun, so the
        # gate-and-apply invariant that apply_instant_interaction asserts does not
        # hold here: an agent can become unable to pay mid-interaction through no
        # fault of the caller. The executor gates at the START of a multi-tick
        # interaction instead.

        # Apply per-tick costs (modern dict format)
        multipliers = self._compute_affordance_multiplier(affordance.name, meters, agent_mask)
        for meter_name, amount in affordance.costs_per_tick.items():
            meter_idx = self._get_meter_idx(meter_name, f"affordance '{affordance_name}' per-tick cost")
            updated_meters[agent_mask, meter_idx] -= amount * multipliers[agent_mask]

        # Execute compiled Effects commands (per_tick stage)
        updated_meters = self._execute_affordance_effects(
            affordance_name,
            "per_tick",
            agent_mask,
            updated_meters,
            multipliers=multipliers,
            current_tick=current_tick,
        )

        if completion_mask.any():
            updated_meters = self._execute_affordance_effects(
                affordance_name,
                "on_completion",
                completion_mask,
                updated_meters,
                multipliers=multipliers,
                current_tick=current_tick,
            )

        # Clamp meters to their DECLARED per-meter bounds (WS-1(e)).
        updated_meters = torch.clamp(updated_meters, self.meter_bounds_min, self.meter_bounds_max)

        return updated_meters

    def can_afford(self, affordance_name: str, meters: torch.Tensor, *, cost_mode: str = "instant") -> torch.Tensor:
        """Which agents can pay EVERY declared cost of this affordance.

        Public because the action mask and the application path must agree: the
        executor gates on this, and ``apply_instant_interaction`` asserts it. A
        private helper invited the two to drift, which is how the gate came to
        consider only ``money`` while every other declared cost was ignored.

        Args:
            affordance_name: Name of the affordance.
            meters: ``[batch_size, meter_count]`` current meter values.
            cost_mode: ``"instant"`` (``costs``) or ``"per_tick"`` (``costs_per_tick``).

        Returns:
            ``[batch_size]`` bool tensor.

        Raises:
            ValueError: Unknown affordance, or an unrecognised ``cost_mode``.
        """
        affordance = self.affordance_map.get(affordance_name)
        if affordance is None:
            raise ValueError(f"Unknown affordance '{affordance_name}'. Known affordances: {sorted(self.affordance_map)}")
        if cost_mode not in ("instant", "per_tick"):
            raise ValueError(f"Unknown cost_mode '{cost_mode}' for affordance '{affordance_name}'; expected 'instant' or 'per_tick'.")

        costs = affordance.costs if cost_mode == "instant" else affordance.costs_per_tick

        # Accumulator on the METERS' device, not self.device: callers pass tensors
        # that may live elsewhere, and a device mismatch here is a silent crash in
        # the hottest path.
        affordable = torch.ones(meters.shape[0], dtype=torch.bool, device=meters.device)

        for meter, amount in costs.items():
            # The context string is load-bearing: an existing test asserts the
            # resulting error message contains "affordance".
            meter_idx = self._get_meter_idx(meter, f"affordance '{affordance_name}' {cost_mode} cost")
            affordable = affordable & (meters[:, meter_idx] >= amount)

        return affordable

    # HIGH-09: Deleted get_action_masks() - dead code with hardcoded dimensions (num_affordances=15).
    # Action masking is handled by vectorized_env.py using ActionBuilder.get_base_action_mask().

    def get_affordance_action_map(self) -> dict[str, int]:
        """
        Get the mapping of affordance names to action indices.

        The environment should use this to build its action space,
        ensuring it's always in sync with the config file.

        Returns:
            Dict mapping affordance name to action index
            Example: {"Bed": 0, "Shower": 1, ...}
        """
        return self.affordance_name_to_idx.copy()

    def get_num_affordances(self) -> int:
        """Get the number of affordances defined in config."""
        return len(self.affordances)

    def get_duration_ticks(self, affordance_name: str) -> int:
        """
        Get the duration in ticks for a multi-tick affordance.

        Args:
            affordance_name: Name of affordance

        Returns:
            Number of duration ticks (1 for instant affordances)
        """
        affordance = self.affordance_map.get(affordance_name)
        if affordance is None:
            raise ValueError(f"Unknown affordance '{affordance_name}'. Known affordances: {sorted(self.affordance_map)}")
        if affordance.duration_ticks is None:
            return 1
        return int(affordance.duration_ticks)

    def _get_meter_idx(self, meter_name: str, context: str = "") -> int:
        """Get meter index with validation and helpful error messages.

        Args:
            meter_name: Name of the meter to look up
            context: Context for error message (e.g., "affordance 'sleep' cost")

        Returns:
            Index of the meter in the meters tensor

        Raises:
            KeyError: If meter name not found in meter_name_to_idx
        """
        if meter_name not in self.meter_name_to_idx:
            ctx_msg = f" in {context}" if context else ""
            raise KeyError(f"Unknown meter '{meter_name}'{ctx_msg}. " f"Available meters: {sorted(self.meter_name_to_idx.keys())}")
        return self.meter_name_to_idx[meter_name]

    def _execute_affordance_effects(
        self,
        affordance_name: str,
        stage: str,
        agent_mask: torch.Tensor,
        meters: torch.Tensor,
        multipliers: torch.Tensor | None = None,
        current_tick: int | None = None,
    ) -> torch.Tensor:
        """Execute pre-compiled Effects commands for affordance lifecycle stage.

        Args:
            affordance_name: Affordance name
            stage: Lifecycle stage (on_start, per_tick, on_completion, etc.)
            agent_mask: Boolean mask of agents interacting [batch]
            meters: Current meter values [batch, num_meters]
            multipliers: Modulation multipliers to scale effect deltas [batch]

        Returns:
            Updated meters tensor [batch, num_meters]
        """
        if self.command_executor is None:
            return meters  # No Effects support, return unchanged

        if affordance_name not in self.compiled_affordances:
            return meters  # No compiled Effects, return unchanged

        compiled = self.compiled_affordances[affordance_name]
        commands = getattr(compiled, stage)

        if not commands:
            return meters  # No commands for this stage

        # Execute commands for each agent in mask
        updated_meters = meters.clone()
        pre_effect_meters = updated_meters.clone()
        if multipliers is None:
            multipliers = torch.ones(
                meters.shape[0],
                device=meters.device,
                dtype=meters.dtype,
            )
            # Zero out non-participating agents to guard against stray writes
            inactive = ~agent_mask
            if inactive.any():
                multipliers[inactive] = 0.0

        for agent_idx in torch.where(agent_mask)[0]:
            # Build bars dict (same pattern as ItemActionHandler)
            bars_dict = {name: updated_meters[:, idx] for name, idx in self.meter_name_to_idx.items()}

            context = ExecutionContext(
                bars=bars_dict,
                vfs_registry=self.vfs_registry,
                self_index=None,  # Affordances don't have self yet
                target_index=agent_idx.item(),
                effect_manager=self.effect_manager,
                item_manager=self.item_manager,
                scheduler=getattr(self.effect_manager, "scheduler", None),
                current_tick=current_tick or 0,
                affordance_overrides=self.affordance_overrides,
            )

            for command in commands:
                self.command_executor.execute(command, context)

            # Sync meters back from bars dict
            for meter_name, meter_idx in self.meter_name_to_idx.items():
                updated_meters[:, meter_idx] = bars_dict[meter_name]

        # Scale effect deltas by modulation multipliers
        deltas = updated_meters - pre_effect_meters
        updated_meters = pre_effect_meters + deltas * multipliers.unsqueeze(1)

        return updated_meters


class NullEffectManager:
    """Fallback EffectManager that raises on spawn when Effects are not configured."""

    def spawn_effect(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - defensive only
        raise RuntimeError("EffectManager not configured; spawn_effect unavailable")
