"""DACEngine — drive/reward backend.

The DACEngine compiles a level's ``drive.yaml`` (a
:class:`~townlet.config.drive_as_code.DriveAsCodeConfig`) into GPU-native
computation functions for per-step reward calculation. It is invoked by
``VTCRewardProgram`` as the ``reward_backend`` parameter, not directly by the
environment, so "DAC" here is a historical name for what is now simply the
project's drive/reward backend. The runtime entry point is
:meth:`DACEngine.calculate_rewards`.

Design:
- All operations vectorized across agents (batch dimension)
- Modifier evaluation uses torch.where for range lookups
- VFS integration via runtime registry with reader="engine"
- Intrinsic weight modulation for crisis suppression

Formula:
    total_reward = extrinsic + (intrinsic * effective_intrinsic_weight) + shaping

Where:
    effective_intrinsic_weight = base_weight * modifier1 * modifier2 * ...
"""

from collections.abc import Callable

import torch

from townlet.config.drive_as_code import DriveAsCodeConfig
from townlet.vfs.registry import VariableRegistry


class DACEngine:
    """Drive/reward backend compiled from a ``drive.yaml`` specification.

    Historically referred to as the "Drive As Code engine"; in the current
    runtime it is the only reward backend, invoked through
    ``VTCRewardProgram(reward_backend=DACEngine)``. The name is preserved
    to keep checkpoint provenance (``drive_hash``) and call-site greppability
    stable; a rename is deferred (see milestone hamlet-22ffae178f).

    Example:
        >>> engine = DACEngine(
        ...     dac_config=dac_config,
        ...     vfs_registry=vfs_registry,
        ...     device=torch.device("cpu"),
        ...     num_agents=4,
        ... )
        >>> total_rewards, intrinsic_weights, components = engine.calculate_rewards(
        ...     step_counts=step_counts,
        ...     dones=dones,
        ...     meters=meters,
        ...     intrinsic_raw=intrinsic_raw,
        ... )
    """

    def __init__(
        self,
        dac_config: DriveAsCodeConfig,
        vfs_registry: VariableRegistry,
        device: torch.device,
        num_agents: int,
        bar_index_map: dict[str, int],
    ):
        """Initialize DAC engine.

        Args:
            dac_config: Parsed ``drive.yaml`` for the level being compiled.
            vfs_registry: VFS runtime registry for variable access
            device: PyTorch device (cpu or cuda)
            num_agents: Number of agents in population
            bar_index_map: Mapping from bar ID to meters tensor index (from universe metadata)
        """
        self.dac_config = dac_config
        self.vfs_registry = vfs_registry
        self.device = device
        self.num_agents = num_agents
        self.bar_index_map = bar_index_map
        self.vfs_reader = "engine"  # DAC reads as engine, not agent

        # Compile modifiers into lookup tables
        self.modifiers = self._compile_modifiers()

        # Compile extrinsic strategy
        self.extrinsic_fn = self._compile_extrinsic()

        # Compile shaping bonuses
        self.shaping_fns = self._compile_shaping()

        # Logging
        self.log_components = dac_config.composition.log_components
        self.log_modifiers = dac_config.composition.log_modifiers

    def _compile_modifiers(self) -> dict[str, Callable]:
        """Compile modifiers into efficient lookup functions.

        Uses torch.where for GPU-optimized range evaluation.
        Modifiers return multipliers that can be chained together.

        Returns:
            Dictionary mapping modifier name to evaluation function
        """
        compiled: dict[str, Callable] = {}

        for mod_name, mod_config in self.dac_config.modifiers.items():

            def create_modifier_fn(config) -> Callable:
                # Pre-compute range boundaries and multipliers as tensors
                ranges = sorted(config.ranges, key=lambda r: r.min)

                def evaluate_modifier(meters: torch.Tensor) -> torch.Tensor:
                    """Evaluate modifier for all agents."""
                    bar_name = getattr(config, "bar", None)
                    var_name = getattr(config, "variable", None)

                    if bar_name:
                        bar_idx = self._get_bar_index(bar_name)
                        source_value = meters[:, bar_idx]
                    elif var_name:
                        try:
                            source_value = self.vfs_registry.get(var_name, reader=self.vfs_reader)
                        except KeyError:
                            available = list(self.vfs_registry.variables.keys())
                            raise KeyError(
                                f"VFS variable '{var_name}' referenced in modifier '{mod_name}' "
                                f"but not found in registry. Available: {available}"
                            ) from None
                    else:
                        raise ValueError(
                            f"Modifier {mod_name!r} has neither `bar` nor `variable` source. "
                            "drive.yaml modifiers must declare one or the other."
                        )

                    # Evaluate ranges using torch.where for GPU efficiency
                    # Start with the final configured range as the base case.
                    multiplier = torch.full_like(source_value, ranges[-1].multiplier, dtype=torch.float32)

                    # Walk ranges in reverse using nested torch.where.
                    for r in reversed(ranges[:-1]):
                        condition = (source_value >= r.min) & (source_value < r.max)
                        multiplier = torch.where(condition, r.multiplier, multiplier)

                    return multiplier

                return evaluate_modifier

            compiled[mod_name] = create_modifier_fn(mod_config)

        return compiled

    def _compile_extrinsic(self) -> Callable:
        """Compile extrinsic strategy into computation function.

        Returns:
            Function that computes extrinsic rewards [num_agents]
        """
        strategy = self.dac_config.extrinsic

        if strategy.type == "multiplicative":
            # reward = base * bar1 * bar2 * ...
            base = getattr(strategy, "base", None) or 1.0
            bar_ids = getattr(strategy, "bars", [])

            def compute_multiplicative(meters: torch.Tensor, dones: torch.Tensor) -> torch.Tensor:
                """Multiplicative: reward = base * product(bars)"""
                # Start with base
                reward = torch.full((self.num_agents,), base, device=self.device, dtype=torch.float32)

                # Multiply by each bar
                for bar_id in bar_ids:
                    bar_idx = self._get_bar_index(bar_id)
                    reward = reward * meters[:, bar_idx]

                # Apply modifiers
                for modifier_name in getattr(strategy, "apply_modifiers", []):
                    if modifier_name in self.modifiers:
                        modifier_fn = self.modifiers[modifier_name]
                        multiplier = modifier_fn(meters)
                        reward = reward * multiplier

                # Dead agents get 0.0
                reward = torch.where(dones, torch.zeros_like(reward), reward)

                return reward

            return compute_multiplicative

        elif strategy.type == "constant_base_with_shaped_bonus":
            base_reward = getattr(strategy, "base_reward", None) or 1.0
            bar_bonuses = getattr(strategy, "bar_bonuses", [])
            variable_bonuses = getattr(strategy, "variable_bonuses", [])

            def compute_constant_base(meters: torch.Tensor, dones: torch.Tensor) -> torch.Tensor:
                """Constant base + shaped bonuses."""
                reward = torch.full((self.num_agents,), base_reward, device=self.device, dtype=torch.float32)

                # Bar bonuses: bonus = scale * (bar_value - center)
                for bonus_config in bar_bonuses:
                    bar_idx = self._get_bar_index(bonus_config.bar)
                    bar_value = meters[:, bar_idx]
                    bonus = bonus_config.scale * (bar_value - bonus_config.center)
                    reward = reward + bonus

                # VFS variable bonuses: bonus = weight * var_value
                for var_bonus_config in variable_bonuses:
                    var_value = self.vfs_registry.get(var_bonus_config.variable, reader=self.vfs_reader)
                    bonus = var_bonus_config.weight * var_value
                    reward = reward + bonus

                for modifier_name in getattr(strategy, "apply_modifiers", []):
                    if modifier_name in self.modifiers:
                        modifier_fn = self.modifiers[modifier_name]
                        multiplier = modifier_fn(meters)
                        reward = reward * multiplier

                reward = torch.where(dones, torch.zeros_like(reward), reward)
                return reward

            return compute_constant_base

        elif strategy.type == "additive_unweighted":
            # reward = base + sum(bars)
            base = getattr(strategy, "base", None) or 0.0
            bar_ids = getattr(strategy, "bars", [])

            def compute_additive(meters: torch.Tensor, dones: torch.Tensor) -> torch.Tensor:
                """Additive unweighted: reward = base + sum(bars)"""
                reward = torch.full((self.num_agents,), base, device=self.device, dtype=torch.float32)

                # Sum all bars
                for bar_id in bar_ids:
                    bar_idx = self._get_bar_index(bar_id)
                    reward = reward + meters[:, bar_idx]

                # Apply modifiers
                for modifier_name in getattr(strategy, "apply_modifiers", []):
                    if modifier_name in self.modifiers:
                        modifier_fn = self.modifiers[modifier_name]
                        multiplier = modifier_fn(meters)
                        reward = reward * multiplier

                # Dead agents get 0.0
                reward = torch.where(dones, torch.zeros_like(reward), reward)

                return reward

            return compute_additive

        elif strategy.type == "weighted_sum":
            # reward = sum(weight_i * bar_i) using bar_bonuses for weights
            # (center is ignored, scale is the weight)
            base = getattr(strategy, "base", None) or 0.0
            bar_bonuses = getattr(strategy, "bar_bonuses", [])

            def compute_weighted_sum(meters: torch.Tensor, dones: torch.Tensor) -> torch.Tensor:
                """Weighted sum: reward = sum(weight_i * bar_i)"""
                reward = torch.full((self.num_agents,), base, device=self.device, dtype=torch.float32)

                # Add weighted bars (using scale as weight, ignoring center)
                for bonus_config in bar_bonuses:
                    bar_idx = self._get_bar_index(bonus_config.bar)
                    bar_value = meters[:, bar_idx]
                    weighted_value = bonus_config.scale * bar_value
                    reward = reward + weighted_value

                # Apply modifiers
                for modifier_name in getattr(strategy, "apply_modifiers", []):
                    if modifier_name in self.modifiers:
                        modifier_fn = self.modifiers[modifier_name]
                        multiplier = modifier_fn(meters)
                        reward = reward * multiplier

                # Dead agents get 0.0
                reward = torch.where(dones, torch.zeros_like(reward), reward)

                return reward

            return compute_weighted_sum

        elif strategy.type == "polynomial":
            # reward = sum(weight_i * bar_i^exponent_i)
            # Using bar_bonuses: scale=weight, center=exponent
            base = getattr(strategy, "base", None) or 0.0
            bar_bonuses = getattr(strategy, "bar_bonuses", [])

            def compute_polynomial(meters: torch.Tensor, dones: torch.Tensor) -> torch.Tensor:
                """Polynomial: reward = sum(weight_i * bar_i^exponent_i)"""
                reward = torch.full((self.num_agents,), base, device=self.device, dtype=torch.float32)

                # Add polynomial terms (scale=weight, center=exponent)
                for bonus_config in bar_bonuses:
                    bar_idx = self._get_bar_index(bonus_config.bar)
                    bar_value = meters[:, bar_idx]
                    exponent = bonus_config.center
                    weight = bonus_config.scale
                    # CRIT-01: Clamp to non-negative to prevent NaN from negative^fractional
                    bar_value_safe = torch.clamp(bar_value, min=0.0)
                    term = weight * torch.pow(bar_value_safe, exponent)
                    reward = reward + term

                # Apply modifiers
                for modifier_name in getattr(strategy, "apply_modifiers", []):
                    if modifier_name in self.modifiers:
                        modifier_fn = self.modifiers[modifier_name]
                        multiplier = modifier_fn(meters)
                        reward = reward * multiplier

                # Dead agents get 0.0
                reward = torch.where(dones, torch.zeros_like(reward), reward)

                return reward

            return compute_polynomial

        elif strategy.type == "threshold_based":
            # reward = base + sum(bonuses if bar >= threshold)
            base = getattr(strategy, "base", None) or 0.0
            bar_bonuses = getattr(strategy, "bar_bonuses", [])

            def compute_threshold(meters: torch.Tensor, dones: torch.Tensor) -> torch.Tensor:
                """Threshold-based: bonus when bar crosses threshold"""
                reward = torch.full((self.num_agents,), base, device=self.device, dtype=torch.float32)

                # Add threshold bonuses (center=threshold, scale=bonus)
                for bonus_config in bar_bonuses:
                    bar_idx = self._get_bar_index(bonus_config.bar)
                    bar_value = meters[:, bar_idx]
                    threshold = bonus_config.center
                    bonus = bonus_config.scale

                    # Apply bonus where bar >= threshold
                    above_threshold = bar_value >= threshold
                    reward = reward + torch.where(above_threshold, bonus, 0.0)

                # Apply modifiers
                for modifier_name in getattr(strategy, "apply_modifiers", []):
                    if modifier_name in self.modifiers:
                        modifier_fn = self.modifiers[modifier_name]
                        multiplier = modifier_fn(meters)
                        reward = reward * multiplier

                # Dead agents get 0.0
                reward = torch.where(dones, torch.zeros_like(reward), reward)

                return reward

            return compute_threshold

        elif strategy.type == "aggregation":
            # reward = base + min(bars)  (simplified - always uses min)
            # Full implementation would have operation field (min/max/mean/product)
            base = getattr(strategy, "base", None) or 0.0
            bar_ids = getattr(strategy, "bars", [])

            def compute_aggregation(meters: torch.Tensor, dones: torch.Tensor) -> torch.Tensor:
                """Aggregation: reward = base + min(bars)"""
                reward = torch.full((self.num_agents,), base, device=self.device, dtype=torch.float32)

                if bar_ids:
                    # Stack bars for aggregation: [num_agents, num_bars]
                    bar_values = torch.stack([meters[:, self._get_bar_index(bar_id)] for bar_id in bar_ids], dim=1)

                    # Apply min aggregation (could be extended to max/mean/product)
                    aggregated = torch.min(bar_values, dim=1).values
                    reward = reward + aggregated

                # Apply modifiers
                for modifier_name in getattr(strategy, "apply_modifiers", []):
                    if modifier_name in self.modifiers:
                        modifier_fn = self.modifiers[modifier_name]
                        multiplier = modifier_fn(meters)
                        reward = reward * multiplier

                # Dead agents get 0.0
                reward = torch.where(dones, torch.zeros_like(reward), reward)

                return reward

            return compute_aggregation

        elif strategy.type == "vfs_variable":
            # reward = sum(weight_i * vfs[variable_i])
            base = getattr(strategy, "base", None) or 0.0
            variable_bonuses = getattr(strategy, "variable_bonuses", [])

            def compute_vfs_variable(meters: torch.Tensor, dones: torch.Tensor) -> torch.Tensor:
                """VFS variable: reward from VFS-computed values (escape hatch)"""
                reward = torch.full((self.num_agents,), base, device=self.device, dtype=torch.float32)

                # Add weighted VFS variables
                for bonus_config in variable_bonuses:
                    var_value = self.vfs_registry.get(bonus_config.variable, reader=self.vfs_reader)
                    weighted_value = bonus_config.weight * var_value
                    reward = reward + weighted_value

                # Apply modifiers
                for modifier_name in getattr(strategy, "apply_modifiers", []):
                    if modifier_name in self.modifiers:
                        modifier_fn = self.modifiers[modifier_name]
                        multiplier = modifier_fn(meters)
                        reward = reward * multiplier

                # Dead agents get 0.0
                reward = torch.where(dones, torch.zeros_like(reward), reward)

                return reward

            return compute_vfs_variable

        elif strategy.type == "hybrid":
            # Simplified hybrid: base + weighted bars with optional centering
            # Full implementation would compose multiple sub-strategies
            base = getattr(strategy, "base", None) or 0.0
            bar_bonuses = getattr(strategy, "bar_bonuses", [])

            def compute_hybrid(meters: torch.Tensor, dones: torch.Tensor) -> torch.Tensor:
                """Hybrid: combine multiple approaches (simplified version)"""
                reward = torch.full((self.num_agents,), base, device=self.device, dtype=torch.float32)

                # For each bar bonus, apply weighted calculation
                # If center is 0.0, treat as linear weight
                # If center is non-zero, treat as shaped bonus (value - center)
                for bonus_config in bar_bonuses:
                    bar_idx = self._get_bar_index(bonus_config.bar)
                    bar_value = meters[:, bar_idx]

                    if abs(bonus_config.center) < 1e-6:
                        # Linear weight (center ≈ 0)
                        term = bonus_config.scale * bar_value
                    else:
                        # Shaped bonus (value - center)
                        term = bonus_config.scale * (bar_value - bonus_config.center)

                    reward = reward + term

                # Apply modifiers
                for modifier_name in getattr(strategy, "apply_modifiers", []):
                    if modifier_name in self.modifiers:
                        modifier_fn = self.modifiers[modifier_name]
                        multiplier = modifier_fn(meters)
                        reward = reward * multiplier

                # Dead agents get 0.0
                reward = torch.where(dones, torch.zeros_like(reward), reward)

                return reward

            return compute_hybrid

        raise ValueError(f"Unsupported extrinsic strategy: {strategy.type!r}")

    def _compile_shaping(self) -> list[Callable]:
        """Compile shaping bonuses into computation functions.

        Returns:
            List of shaping bonus functions
        """
        shaping_fns = []

        for bonus_config in self.dac_config.shaping:
            if bonus_config.type == "approach_reward":
                # Use closure factory to capture config correctly
                def create_approach_reward_fn(config):
                    target_affordance = config.target_affordance
                    weight = config.weight
                    max_distance = config.max_distance

                    def compute_approach_reward(**kwargs) -> torch.Tensor:
                        """Compute approach reward bonus for all agents."""
                        # Extract kwargs
                        agent_positions = kwargs.get("agent_positions")
                        affordance_positions = kwargs.get("affordance_positions", {})

                        # Initialize bonus to zeros
                        bonus = torch.zeros(self.num_agents, device=self.device)

                        # Check if target affordance exists
                        if target_affordance not in affordance_positions:
                            return bonus

                        # Get target position
                        target_pos = affordance_positions[target_affordance]

                        # Calculate distances using Euclidean norm
                        distances = torch.norm(agent_positions - target_pos, dim=1)

                        # Compute bonus: weight * (1.0 - distance / max_distance), clamped to [0, weight]
                        bonus = weight * (1.0 - distances / max_distance)
                        bonus = torch.clamp(bonus, min=0.0, max=weight)

                        return bonus

                    return compute_approach_reward

                shaping_fns.append(create_approach_reward_fn(bonus_config))

            elif bonus_config.type == "completion_bonus":
                # Use closure factory to capture config correctly
                def create_completion_bonus_fn(config):
                    weight = config.weight
                    target_affordance = config.affordance

                    def compute_completion_bonus(**kwargs) -> torch.Tensor:
                        """Compute completion bonus for all agents."""
                        # Extract kwargs
                        last_action_affordance = kwargs.get("last_action_affordance")

                        # Initialize bonus to zeros
                        bonus = torch.zeros(self.num_agents, device=self.device)

                        # Null check for missing kwarg
                        if last_action_affordance is None:
                            return bonus

                        # Vectorize the comparison using list comprehension + tensor creation
                        # Note: Can't fully vectorize string comparison, but keep it minimal
                        matches: torch.Tensor = torch.tensor(
                            [1.0 if aff == target_affordance else 0.0 for aff in last_action_affordance],
                            device=self.device,
                            dtype=torch.float32,
                        )
                        bonus = weight * matches

                        return torch.as_tensor(bonus)

                    return compute_completion_bonus

                shaping_fns.append(create_completion_bonus_fn(bonus_config))

            elif bonus_config.type == "efficiency_bonus":
                # Use closure factory to capture config correctly
                def create_efficiency_bonus_fn(config):
                    weight = config.weight
                    bar_id = config.bar
                    threshold = config.threshold

                    def compute_efficiency_bonus(**kwargs) -> torch.Tensor:
                        """Compute efficiency bonus for all agents."""
                        # Extract kwargs
                        meters = kwargs.get("meters")

                        # Null check for missing kwarg
                        if meters is None:
                            return torch.zeros(self.num_agents, device=self.device)

                        # Get bar index
                        bar_idx = self._get_bar_index(bar_id)

                        # Get bar values
                        bar_values = meters[:, bar_idx]

                        # Bonus if bar >= threshold
                        above_threshold = bar_values >= threshold
                        bonus = torch.where(above_threshold, weight, 0.0)

                        return bonus

                    return compute_efficiency_bonus

                shaping_fns.append(create_efficiency_bonus_fn(bonus_config))

            elif bonus_config.type == "state_achievement":
                # Use closure factory to capture config correctly
                def create_state_achievement_fn(config):
                    weight = config.weight
                    conditions = config.conditions

                    def compute_state_achievement(**kwargs) -> torch.Tensor:
                        """Compute state achievement bonus for all agents."""
                        # Extract kwargs
                        meters = kwargs.get("meters")

                        # Null check for missing kwarg
                        if meters is None:
                            return torch.zeros(self.num_agents, device=self.device)

                        # Start with all agents meeting all conditions
                        all_conditions_met = torch.ones(self.num_agents, device=self.device, dtype=torch.bool)

                        # Check each condition
                        for condition in conditions:
                            # Get bar index
                            bar_idx = self._get_bar_index(condition.bar)

                            # Get bar values
                            bar_values = meters[:, bar_idx]

                            # Check if condition met
                            condition_met = bar_values >= condition.min_value

                            # Use logical AND to accumulate conditions
                            all_conditions_met = all_conditions_met & condition_met

                        # Convert boolean mask to bonus
                        bonus = torch.where(all_conditions_met, weight, 0.0)

                        return bonus

                    return compute_state_achievement

                shaping_fns.append(create_state_achievement_fn(bonus_config))

            elif bonus_config.type == "streak_bonus":
                # Use closure factory to capture config correctly
                def create_streak_bonus_fn(config):
                    weight = config.weight
                    target_affordance = config.affordance
                    min_streak = config.min_streak

                    def compute_streak_bonus(**kwargs) -> torch.Tensor:
                        """Compute streak bonus for all agents."""
                        # Extract kwargs
                        affordance_streak = kwargs.get("affordance_streak")

                        # Null check for missing kwarg
                        if affordance_streak is None:
                            return torch.zeros(self.num_agents, device=self.device)

                        # Check if target affordance exists in streak dict
                        if target_affordance not in affordance_streak:
                            return torch.zeros(self.num_agents, device=self.device)

                        # Get streak counts for target affordance
                        streak_counts = affordance_streak[target_affordance]

                        # Bonus if streak >= min_streak
                        meets_threshold = streak_counts >= min_streak
                        bonus = torch.where(meets_threshold, weight, 0.0)

                        return bonus

                    return compute_streak_bonus

                shaping_fns.append(create_streak_bonus_fn(bonus_config))

            elif bonus_config.type == "diversity_bonus":
                # Use closure factory to capture config correctly
                def create_diversity_bonus_fn(config):
                    weight = config.weight
                    min_unique = config.min_unique_affordances

                    def compute_diversity_bonus(**kwargs) -> torch.Tensor:
                        """Compute diversity bonus for all agents."""
                        # Extract kwargs
                        unique_affordances_used = kwargs.get("unique_affordances_used")

                        # Null check for missing kwarg
                        if unique_affordances_used is None:
                            return torch.zeros(self.num_agents, device=self.device)

                        # Bonus if unique_affordances_used >= min_unique
                        meets_threshold = unique_affordances_used >= min_unique
                        bonus = torch.where(meets_threshold, weight, 0.0)

                        return bonus

                    return compute_diversity_bonus

                shaping_fns.append(create_diversity_bonus_fn(bonus_config))

            elif bonus_config.type == "timing_bonus":
                # Use closure factory to capture config correctly
                def create_timing_bonus_fn(config):
                    weight = config.weight
                    time_ranges = config.time_ranges

                    def compute_timing_bonus(**kwargs) -> torch.Tensor:
                        """Compute timing bonus for all agents."""
                        # Extract kwargs
                        current_hour = kwargs.get("current_hour")
                        last_action_affordance = kwargs.get("last_action_affordance")

                        # Null checks - require BOTH kwargs
                        if current_hour is None or last_action_affordance is None:
                            return torch.zeros(self.num_agents, device=self.device)

                        # Initialize bonus to zeros
                        bonus = torch.zeros(self.num_agents, device=self.device)

                        # Check each time range
                        for time_range in time_ranges:
                            # Check if current_hour is in range
                            # Handle wrap-around (e.g., 22-6 means 22,23,0,1,2,3,4,5,6)
                            if time_range.start_hour <= time_range.end_hour:
                                # Normal range (e.g., 12-13)
                                in_time_window = (current_hour >= time_range.start_hour) & (current_hour <= time_range.end_hour)
                            else:
                                # Wrap-around range (e.g., 22-6)
                                in_time_window = (current_hour >= time_range.start_hour) | (current_hour <= time_range.end_hour)

                            # Check if last action matches affordance (string comparison, can't fully vectorize)
                            affordance_matches = torch.tensor(
                                [1.0 if aff == time_range.affordance else 0.0 for aff in last_action_affordance],
                                device=self.device,
                                dtype=torch.float32,
                            )

                            # Both conditions must be met
                            matches = in_time_window.float() * affordance_matches

                            # Add bonus for this time range
                            bonus = bonus + (matches * weight * time_range.multiplier)

                        return bonus

                    return compute_timing_bonus

                shaping_fns.append(create_timing_bonus_fn(bonus_config))

            elif bonus_config.type == "economic_efficiency":
                # Use closure factory to capture config correctly
                def create_economic_efficiency_fn(config):
                    weight = config.weight
                    money_bar_id = config.money_bar
                    min_balance = config.min_balance

                    def compute_economic_efficiency(**kwargs) -> torch.Tensor:
                        """Compute economic efficiency bonus for all agents."""
                        # Extract kwargs
                        meters = kwargs.get("meters")

                        # Null check for missing kwarg
                        if meters is None:
                            return torch.zeros(self.num_agents, device=self.device)

                        # Get money bar index
                        bar_idx = self._get_bar_index(money_bar_id)

                        # Get money bar values
                        money_values = meters[:, bar_idx]

                        # Bonus if money >= min_balance
                        above_threshold = money_values >= min_balance
                        bonus = torch.where(above_threshold, weight, 0.0)

                        return bonus

                    return compute_economic_efficiency

                shaping_fns.append(create_economic_efficiency_fn(bonus_config))

            elif bonus_config.type == "balance_bonus":
                # Use closure factory to capture config correctly
                def create_balance_bonus_fn(config):
                    weight = config.weight
                    bar_ids = config.bars
                    max_imbalance = config.max_imbalance

                    def compute_balance_bonus(**kwargs) -> torch.Tensor:
                        """Compute balance bonus for all agents."""
                        # Extract kwargs
                        meters = kwargs.get("meters")

                        # Null check for missing kwarg
                        if meters is None:
                            return torch.zeros(self.num_agents, device=self.device)

                        # Get bar indices
                        bar_indices = [self._get_bar_index(bar_id) for bar_id in bar_ids]

                        # Stack bar values: [num_agents, num_bars]
                        bar_values = torch.stack([meters[:, bar_idx] for bar_idx in bar_indices], dim=1)

                        # Compute imbalance: max - min across bars for each agent
                        imbalance = bar_values.max(dim=1).values - bar_values.min(dim=1).values

                        # Bonus if imbalance <= max_imbalance
                        bonus = torch.where(imbalance <= max_imbalance, weight, 0.0)

                        return bonus

                    return compute_balance_bonus

                shaping_fns.append(create_balance_bonus_fn(bonus_config))

            elif bonus_config.type == "crisis_avoidance":
                # Use closure factory to capture config correctly
                def create_crisis_avoidance_fn(config):
                    weight = config.weight
                    bar_id = config.bar
                    crisis_threshold = config.crisis_threshold

                    def compute_crisis_avoidance(**kwargs) -> torch.Tensor:
                        """Compute crisis avoidance bonus for all agents."""
                        # Extract kwargs
                        meters = kwargs.get("meters")

                        # Null check for missing kwarg
                        if meters is None:
                            return torch.zeros(self.num_agents, device=self.device)

                        # Get bar index
                        bar_idx = self._get_bar_index(bar_id)

                        # Get bar values
                        bar_values = meters[:, bar_idx]

                        # Bonus if bar > crisis_threshold (strictly above, not at)
                        above_crisis = bar_values > crisis_threshold
                        bonus = torch.where(above_crisis, weight, 0.0)

                        return bonus

                    return compute_crisis_avoidance

                shaping_fns.append(create_crisis_avoidance_fn(bonus_config))

            elif bonus_config.type == "vfs_variable":
                # Use closure factory to capture config correctly
                def create_vfs_variable_fn(config):
                    weight = config.weight
                    variable = config.variable

                    def compute_vfs_variable(**kwargs) -> torch.Tensor:
                        """Compute VFS variable bonus for all agents."""
                        # Read variable from VFS registry (no kwargs needed)
                        # NOTE: VFS registry raises KeyError if variable not found
                        # This is intentional - we don't return zeros like other bonuses
                        variable_value = self.vfs_registry.get(variable, reader=self.vfs_reader)

                        # Bonus: weight * variable_value
                        # Supports negative bonuses (weight or variable can be negative)
                        bonus: torch.Tensor = weight * variable_value

                        return bonus

                    return compute_vfs_variable

                shaping_fns.append(create_vfs_variable_fn(bonus_config))

        return shaping_fns

    def _get_bar_index(self, bar_id: str) -> int:
        """Get meter index from universe metadata.

        Args:
            bar_id: Bar identifier (e.g., "energy", "health")

        Returns:
            Index into the meters tensor

        Raises:
            KeyError: If bar_id not found in metadata
        """
        if bar_id not in self.bar_index_map:
            raise KeyError(f"Bar '{bar_id}' not found in universe metadata. " f"Available bars: {list(self.bar_index_map.keys())}")
        return self.bar_index_map[bar_id]

    def calculate_rewards(
        self,
        step_counts: torch.Tensor,
        dones: torch.Tensor,
        meters: torch.Tensor,
        intrinsic_raw: torch.Tensor,
        **kwargs,
    ) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
        """Calculate total rewards with DAC.

        Composes: extrinsic + (intrinsic × modifiers) + shaping

        Args:
            step_counts: [num_agents] current step count
            dones: [num_agents] agent death flags
            meters: [num_agents, meter_count] normalized meter values
            intrinsic_raw: [num_agents] raw intrinsic curiosity values
            **kwargs: Additional context (positions, affordance states, etc.)
                - agent_positions: torch.Tensor (num_agents, ndims)
                - affordance_positions: dict[str, torch.Tensor]
                - last_action_affordance: list[str | None]
                - affordance_streak: dict[str, torch.Tensor]
                - unique_affordances_used: torch.Tensor
                - current_hour: torch.Tensor

        Returns:
            total_rewards: [num_agents] final rewards
            intrinsic_weights: [num_agents] effective intrinsic weights after modifiers
            components: dict of reward components (extrinsic, intrinsic, shaping)

        Raises:
            RuntimeError: If input tensors are on different device than DACEngine
        """

        # Validate device consistency (ENV-007)
        # Compare device types robustly - cuda:0 == cuda (default device)
        def _same_device(a: torch.device, b: torch.device) -> bool:
            """Check if two devices are the same, handling cuda vs cuda:0."""
            if a.type != b.type:
                return False
            if a.type == "cuda":
                # cuda (no index) means device 0, same as cuda:0
                a_idx = a.index if a.index is not None else 0
                b_idx = b.index if b.index is not None else 0
                return a_idx == b_idx
            return True

        if not _same_device(meters.device, self.device):
            raise RuntimeError(
                f"Meters tensor on {meters.device} but DACEngine on {self.device}. " f"Ensure all tensors are on the same device."
            )
        if not _same_device(intrinsic_raw.device, self.device):
            raise RuntimeError(
                f"Intrinsic tensor on {intrinsic_raw.device} but DACEngine on {self.device}. " f"Ensure all tensors are on the same device."
            )
        if not _same_device(dones.device, self.device):
            raise RuntimeError(
                f"Dones tensor on {dones.device} but DACEngine on {self.device}. " f"Ensure all tensors are on the same device."
            )

        # 1. Compute extrinsic reward
        extrinsic = self.extrinsic_fn(meters=meters, dones=dones)

        # 2. Compute intrinsic reward with modifiers
        intrinsic_raw_copy = intrinsic_raw.clone()

        # Apply base_weight first
        base_weight = self.dac_config.intrinsic.base_weight
        intrinsic = intrinsic_raw_copy * base_weight

        # Apply modifiers (only those listed in apply_modifiers)
        intrinsic_weight = torch.ones(self.num_agents, device=self.device)
        for modifier_name in self.dac_config.intrinsic.apply_modifiers:
            if modifier_name in self.modifiers:
                modifier_fn = self.modifiers[modifier_name]
                multiplier = modifier_fn(meters)
                intrinsic_weight = intrinsic_weight * multiplier

        # Apply modifiers to intrinsic rewards
        intrinsic = intrinsic * intrinsic_weight

        # Dead agents get 0.0 intrinsic
        intrinsic = torch.where(dones, torch.zeros_like(intrinsic), intrinsic)

        # 3. Compute shaping bonuses
        shaping_total = torch.zeros(self.num_agents, device=self.device)
        for shaping_fn in self.shaping_fns:
            bonus = shaping_fn(meters=meters, dones=dones, **kwargs)
            shaping_total += bonus

        # Dead agents get 0.0 shaping
        shaping_total = torch.where(dones, torch.zeros_like(shaping_total), shaping_total)

        # 4. Compose total reward
        total_reward = extrinsic + intrinsic + shaping_total

        # 5. Build components dict for logging
        # intrinsic_raw: before modifier application (base_weight applied, not modifiers)
        # intrinsic: after modifier application (base_weight × modifiers × raw)
        intrinsic_raw_weighted = intrinsic_raw_copy * base_weight

        components = {
            "extrinsic": extrinsic,
            "intrinsic": intrinsic,
            "intrinsic_raw": intrinsic_raw_weighted,  # Before modifiers, after base_weight
            "shaping": shaping_total,
        }

        return total_reward, intrinsic_weight, components
