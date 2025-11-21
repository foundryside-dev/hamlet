"""
AffordanceEngine: Config-driven affordance interaction system.

This module processes affordance interactions using YAML configuration instead
of hardcoded logic. Follows the same pattern as MeterDynamics (ACTION #1).

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
from typing import Any

import torch

from townlet.config.effects_config import CommandConfig
from townlet.effects.compiler import CommandCompiler
from townlet.effects.executor import CommandExecutor, ExecutionContext
from townlet.effects.parser import CommandParser
from townlet.effects.schema import CommandNode
from townlet.environment.temporal_utils import is_affordance_open as canonical_is_affordance_open


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
        affordance_config: tuple[Any, ...],
        num_agents: int,
        device: torch.device,
        meter_name_to_idx: dict[str, int],
        modulation_rules: list[dict[str, Any]] | None = None,
        vfs_registry: Any | None = None,  # NEW: VFS registry for Effects
        effects_schema: Any | None = None,  # NEW: Effects schema for compilation
        command_executor: CommandExecutor | None = None,  # NEW: Effects executor
        effect_manager: Any | None = None,  # NEW: EffectManager required for Effects commands
        item_manager: Any | None = None,  # NEW: ItemManager required for spawn_item
    ):
        """
        Initialize AffordanceEngine.

        Args:
            affordance_config: Tuple of affordances from compiled universe (v2.1 runtime form)
            num_agents: Number of agents in parallel
            device: torch.device for GPU/CPU
            meter_name_to_idx: Mapping of meter names to indices (from bars_config)
            modulation_rules: Modulation rules for affordance effectiveness
            vfs_registry: VFS registry for Effects system (optional)
            effects_schema: Effects schema for command compilation (optional)
            command_executor: Effects command executor (optional)
        """
        self.num_agents = num_agents
        self.device = device

        self.affordances = affordance_config

        self.meter_name_to_idx = meter_name_to_idx
        self.modulation_rules = modulation_rules or []
        self.vfs_registry = vfs_registry  # NEW
        self.command_executor = command_executor  # NEW
        self.effect_manager = effect_manager or NullEffectManager()
        self.item_manager = item_manager or NullItemManager()

        # Build lookup maps
        self._build_lookup_maps()

        # Compile affordance Effects commands at startup (CRITICAL: Performance)
        self.compiled_affordances: dict[str, CompiledAffordance] = {}

        if command_executor is not None and effects_schema is not None:
            parser = CommandParser()
            compiler = CommandCompiler(schema=effects_schema)

            for affordance in affordance_config:
                # Check if affordance has interactions attribute
                if hasattr(affordance, "interactions") and affordance.interactions is not None:
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
                            command_configs = [CommandConfig(**cmd) if isinstance(cmd, dict) else cmd for cmd in commands]
                            command_nodes = parser.parse_commands(command_configs)
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
        self.affordance_map_by_id: dict[str, Any] = {}
        self.affordance_map: dict[str, Any] = {}

        for idx, aff in enumerate(self.affordances):
            name = getattr(aff, "name", None)
            if not name:
                continue
            self.affordance_name_to_idx[name] = idx
            # Prefer explicit id when available; otherwise fall back to name.
            aff_id = getattr(aff, "id", name)
            self.affordance_map_by_id[aff_id] = aff
            self.affordance_map[name] = aff

    def get_affordance(self, affordance_id: str):
        """Get affordance config by ID."""
        return self.affordance_map_by_id.get(affordance_id)

    def is_affordance_open(self, affordance_name: str, time_of_day: int) -> bool:
        """Check if affordance is open at given time.

        Args:
            affordance_name: Name of affordance (e.g., "Job", "Bar")
            time_of_day: Current hour [0-23]

        Returns:
            True if open, False if closed

        Note:
            Delegates to canonical temporal_utils.is_affordance_open() to avoid
            logic drift (see JANK-09). Do not re-implement this logic.
        """
        affordance = self.affordance_map.get(affordance_name)
        if affordance is None:
            return False

        # Prefer opening_hours from config (supports schedules); fall back to legacy operating_hours tuple if present.
        if hasattr(affordance, "opening_hours"):
            opening_hours = getattr(affordance, "opening_hours")
            if not getattr(opening_hours, "enabled", False):
                return True  # 24/7 availability
            schedule = getattr(opening_hours, "schedule", []) or []
            if not schedule:
                raise ValueError(
                    f"Affordance '{affordance_name}' has opening_hours.enabled=true but an empty schedule; "
                    "provide at least one time window."
                )
            for window in schedule:
                start = getattr(window, "start", None)
                end = getattr(window, "end", None)
                if start is None or end is None:
                    raise ValueError(
                        f"Affordance '{affordance_name}' has malformed opening_hours window: {window!r}. "
                        "Expected 'start' and 'end' integers."
                    )
                if canonical_is_affordance_open(time_of_day, (start, end)):
                    return True
            return False

        if hasattr(affordance, "operating_hours"):
            operating_hours = getattr(affordance, "operating_hours")
            try:
                open_hour, close_hour = operating_hours
            except Exception as exc:  # pragma: no cover - defensive
                raise ValueError(
                    f"Affordance '{affordance_name}' has invalid operating_hours; "
                    f"expected [open_hour, close_hour], got: {operating_hours!r}."
                ) from exc
            return canonical_is_affordance_open(time_of_day, (open_hour, close_hour))

        raise ValueError(
            f"Affordance '{affordance_name}' missing opening_hours/operating_hours; "
            "runtime affordances must provide explicit availability windows."
        )

    def apply_instant_interaction(
        self,
        meters: torch.Tensor,
        affordance_name: str,
        agent_mask: torch.Tensor,
        check_affordability: bool = False,
    ) -> torch.Tensor:
        """
        Apply instant affordance interaction.

        Args:
            meters: [num_agents, 8] current meter values
            affordance_name: Name of affordance (e.g., "Shower")
            agent_mask: [num_agents] bool mask of agents to apply to
            check_affordability: If True, check if agents can afford costs

        Returns:
            updated_meters: [num_agents, 8] after effects applied
        """
        affordance = self.affordance_map.get(affordance_name)
        if affordance is None:
            return meters

        if affordance.interaction_type not in ["instant", "dual"]:
            raise ValueError(
                f"Affordance '{affordance_name}' is {affordance.interaction_type}, "
                f"not instant or dual. Use apply_multi_tick_interaction instead."
            )

        # Clone meters to avoid modifying input
        updated_meters = meters.clone()

        # Check affordability if requested
        if check_affordability and len(affordance.costs) > 0:
            can_afford = self._check_affordability(meters, affordance.costs)
            agent_mask = agent_mask & can_afford

        # Apply costs (modern dict format)
        multipliers = self._compute_affordance_multiplier(affordance.name, meters, agent_mask)
        for cost in self._iter_costs(affordance.costs):
            meter_name, amount = self._cost_fields(cost)
            meter_idx = self.meter_name_to_idx[meter_name]
            updated_meters[agent_mask, meter_idx] -= amount * multipliers[agent_mask]

        # Execute compiled Effects commands (on_start stage for instant affordances)
        updated_meters = self._execute_affordance_effects(
            affordance_name,
            "on_start",
            agent_mask,
            updated_meters,
            multipliers=multipliers,
        )

        # Clamp meters to [0, 1]
        updated_meters = torch.clamp(updated_meters, 0.0, 1.0)

        return updated_meters

    def _compute_affordance_multiplier(self, affordance_name: str, meters: torch.Tensor, agent_mask: torch.Tensor) -> torch.Tensor:
        """Compute modulation multiplier for a given affordance based on bar values."""
        multiplier = torch.ones(meters.shape[0], device=meters.device, dtype=meters.dtype)
        for rule in self.modulation_rules:
            if rule.get("affordance") != affordance_name:
                continue
            bar_idx = rule.get("bar_idx")
            threshold = rule.get("threshold")
            min_multiplier = rule.get("min_multiplier")
            if bar_idx is None or threshold is None or min_multiplier is None:
                continue
            val = meters[:, bar_idx]
            factor = torch.ones_like(val)
            below = val < threshold
            if below.any():
                factor = torch.where(
                    below,
                    min_multiplier + (1.0 - min_multiplier) * (val / threshold),
                    torch.ones_like(val),
                )
            multiplier = multiplier * factor
        # Zero out masked agents to avoid applying to inactive ones
        masked = ~agent_mask
        if masked.any():
            multiplier[masked] = 0.0
        return multiplier

    def apply_multi_tick_interaction(
        self,
        meters: torch.Tensor,
        affordance_name: str,
        current_tick: int,
        agent_mask: torch.Tensor,
        check_affordability: bool = False,
    ) -> torch.Tensor:
        """
        Apply multi-tick affordance interaction for a single tick.

        Args:
            meters: [num_agents, 8] current meter values
            affordance_name: Name of affordance (e.g., "Bed", "Job")
            current_tick: Current tick number [0, duration_ticks-1]
            agent_mask: [num_agents] bool mask of agents to apply to
            check_affordability: If True, check if agents can afford costs

        Returns:
            updated_meters: [num_agents, 8] after per-tick effects applied
        """
        affordance = self.affordance_map.get(affordance_name)
        if affordance is None:
            return meters

        if affordance.interaction_type not in ["multi_tick", "dual"]:
            raise ValueError(
                f"Affordance '{affordance_name}' is {affordance.interaction_type}, "
                f"not multi_tick or dual. Use apply_instant_interaction instead."
            )

        # Clone meters
        updated_meters = meters.clone()

        # Check affordability if requested
        if check_affordability and len(affordance.costs_per_tick) > 0:
            can_afford = self._check_affordability(meters, affordance.costs_per_tick)
            agent_mask = agent_mask & can_afford

        # Apply per-tick costs (modern dict format)
        multipliers = self._compute_affordance_multiplier(affordance.name, meters, agent_mask)
        for cost in self._iter_costs(affordance.costs_per_tick):
            meter_name, amount = self._cost_fields(cost)
            meter_idx = self.meter_name_to_idx[meter_name]
            updated_meters[agent_mask, meter_idx] -= amount * multipliers[agent_mask]

        # Execute compiled Effects commands (per_tick stage)
        updated_meters = self._execute_affordance_effects(
            affordance_name,
            "per_tick",
            agent_mask,
            updated_meters,
            multipliers=multipliers,
        )

        duration_ticks = affordance.duration_ticks or 1

        # Check if this is the final tick - if so, apply completion bonus
        is_final_tick = current_tick == (duration_ticks - 1)
        if is_final_tick:
            # Execute compiled Effects commands (on_completion stage)
            updated_meters = self._execute_affordance_effects(
                affordance_name,
                "on_completion",
                agent_mask,
                updated_meters,
                multipliers=multipliers,
            )

        # Clamp meters to [0, 1]
        updated_meters = torch.clamp(updated_meters, 0.0, 1.0)

        return updated_meters

    def _check_affordability(self, meters: torch.Tensor, costs: list) -> torch.Tensor:
        """
        Check if agents can afford the costs.

        Args:
            meters: [batch_size, 8] current meter values
            costs: List of cost dicts with 'meter' and 'amount' keys

        Returns:
            can_afford: [batch_size] bool tensor
        """
        batch_size = meters.shape[0]
        can_afford = torch.ones(batch_size, dtype=torch.bool, device=self.device)

        for cost in self._iter_costs(costs):
            meter, amount = self._cost_fields(cost)
            meter_idx = self.meter_name_to_idx[meter]
            can_afford = can_afford & (meters[:, meter_idx] >= amount)

        return can_afford

    def get_action_masks(
        self,
        meters: torch.Tensor,
        time_of_day: int,
        check_affordability: bool = True,
        check_hours: bool = True,
    ) -> torch.Tensor:
        """
        Get action masks for all agents considering affordability and operating hours.

        Args:
            meters: [batch_size, 8] current meter values
            time_of_day: Current hour [0-23]
            check_affordability: If True, mask unaffordable actions
            check_hours: If True, mask closed affordances

        Returns:
            action_masks: [batch_size, num_actions] bool tensor
                         Actions include: 4 movement + 15 affordances = 19 total
        """
        batch_size = meters.shape[0]
        num_movement_actions = 4  # UP, DOWN, LEFT, RIGHT
        num_affordances = 15
        num_actions = num_movement_actions + num_affordances

        # Start with all actions available
        action_masks = torch.ones((batch_size, num_actions), dtype=torch.bool, device=self.device)

        # Movement actions always available
        # (boundary checks happen separately in environment)

        # Check each affordance
        for affordance_name, affordance_idx in self.affordance_name_to_idx.items():
            affordance = self.affordance_map.get(affordance_name)
            if affordance is None:
                continue

            action_idx = num_movement_actions + affordance_idx

            # Check operating hours
            if check_hours:
                is_open = self.is_affordance_open(affordance_name, time_of_day)
                if not is_open:
                    action_masks[:, action_idx] = False
                    continue

            # Check affordability
            if check_affordability:
                # Check instant costs
                if len(affordance.costs) > 0:
                    can_afford = self._check_affordability(meters, affordance.costs)
                    action_masks[:, action_idx] = action_masks[:, action_idx] & can_afford

                # Check per-tick costs (for multi-tick affordances)
                elif len(affordance.costs_per_tick) > 0:
                    can_afford = self._check_affordability(meters, affordance.costs_per_tick)
                    action_masks[:, action_idx] = action_masks[:, action_idx] & can_afford

        return action_masks

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

    def get_affordance_cost(self, affordance_name: str, cost_mode: str = "instant") -> float:
        """
        Get the monetary cost for an affordance interaction.

        Args:
            affordance_name: Name of affordance
            cost_mode: "instant" or "per_tick"

        Returns:
            Normalized cost [0, 1] where 1.0 = $100
        """
        affordance = self.affordance_map.get(affordance_name)
        if affordance is None:
            return 0.0

        # Get costs list based on mode (modern dict format)
        costs = affordance.costs if cost_mode == "instant" else affordance.costs_per_tick

        # Find money cost (most affordances only have money cost)
        for cost in self._iter_costs(costs):
            meter, amount = self._cost_fields(cost)
            if meter == "money":
                return float(amount)

        return 0.0

    def get_duration_ticks(self, affordance_name: str) -> int:
        """
        Get the duration in ticks for a multi-tick affordance.

        Args:
            affordance_name: Name of affordance

        Returns:
            Number of duration ticks (1 for instant affordances)
        """
        affordance = self.affordance_map.get(affordance_name)
        if affordance is None or affordance.duration_ticks is None:
            return 1
        return int(affordance.duration_ticks)

    def apply_interaction(
        self,
        meters: torch.Tensor,
        affordance_name: str,
        agent_mask: torch.Tensor,
    ) -> torch.Tensor:
        """
        Apply affordance effects to agent meters.

        This method applies the effects and costs defined in the config
        for a given affordance to the specified agents.

        Args:
            meters: [num_agents, 8] meter values
            affordance_name: Name of the affordance being interacted with
            agent_mask: [num_agents] bool mask indicating which agents interact

        Returns:
            Updated meters tensor [num_agents, 8]

        Raises:
            ValueError: If affordance_name is not recognized
        """
        # Validate affordance exists
        if affordance_name not in self.affordance_name_to_idx:
            raise ValueError(f"Unknown affordance: {affordance_name}")

        # Get affordance config
        affordance = self.affordances[self.affordance_name_to_idx[affordance_name]]

        # Clone meters to avoid in-place modification
        result_meters = meters.clone()

        multipliers = self._compute_affordance_multiplier(affordance.name, meters, agent_mask)

        # Apply costs first
        for cost in self._iter_costs(affordance.costs):
            meter_name, amount = self._cost_fields(cost)
            meter_idx = self.meter_name_to_idx[meter_name]
            result_meters[agent_mask, meter_idx] -= amount * multipliers[agent_mask]

        # Execute compiled Effects commands (on_start stage)
        result_meters = self._execute_affordance_effects(
            affordance_name,
            "on_start",
            agent_mask,
            result_meters,
            multipliers=multipliers,
        )

        return result_meters

    @staticmethod
    def _iter_costs(costs) -> Any:
        """Yield cost entries from either dict- or list-style configs."""
        if isinstance(costs, dict):
            return costs.items()
        return costs

    @staticmethod
    def _cost_fields(cost) -> tuple[str, float]:
        """Extract (meter, amount) from dict-style or DTO-style cost entries."""
        if hasattr(cost, "meter"):
            return cost.meter, float(cost.amount)
        if isinstance(cost, tuple) and len(cost) == 2:
            meter, amount = cost
            return str(meter), float(amount)
        if isinstance(cost, dict):
            if "meter" in cost:
                return cost["meter"], float(cost["amount"])
            if cost:
                meter, amount = next(iter(cost.items()))
                return meter, float(amount)
        raise ValueError(f"Unsupported cost format: {cost!r}")

    def _execute_affordance_effects(
        self,
        affordance_name: str,
        stage: str,
        agent_mask: torch.Tensor,
        meters: torch.Tensor,
        multipliers: torch.Tensor | None = None,
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


class NullItemManager:
    """Fallback ItemManager that raises on spawn when Items are not configured."""

    def spawn_item(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - defensive only
        raise RuntimeError("ItemManager not configured; spawn_item unavailable")
