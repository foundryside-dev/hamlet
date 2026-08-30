"""N-dimensional continuous substrate (N≥4 dimensions)."""

import warnings
from typing import Literal

import torch

from townlet.environment.action_config import ActionConfig
from townlet.substrate.base import (
    SpatialSubstrate,
    combine_metric,
    pairwise_axis_deltas,
    require_position_batch,
)


class ContinuousNDSubstrate(SpatialSubstrate):
    """N-dimensional continuous space for abstract state spaces.

    ContinuousND supports 4D to 100D continuous substrates with float coordinates.
    For 1D/2D/3D continuous spaces, use Continuous1D/2D/3DSubstrate for better ergonomics.

    Coordinate system:
    - positions: [d0, d1, d2, ..., dN] where d0 is dimension 0, etc.
    - Each dimension has configurable bounds: (min, max)
    - Coordinates are continuous floats, not discrete integers

    Movement:
    - Discrete actions move agent by fixed movement_delta
    - MOVE_D0_NEGATIVE = delta = (-movement_delta, 0, 0, ...)
    - MOVE_D0_POSITIVE = delta = (+movement_delta, 0, 0, ...)

    Interaction:
    - Agent must be within interaction_radius of affordance
    - Uses distance metric (euclidean, manhattan, chebyshev)
    - Proximity-based, not exact position match

    Positions are observed in the canonical normalized [0, 1] coordinate range.

    Use cases:
    - High-dimensional continuous control
    - Abstract state space experiments
    - Robotics simulation in high dimensions
    """

    def __init__(
        self,
        bounds: list[tuple[float, float]],
        boundary: Literal["clamp", "wrap", "bounce", "sticky"],
        movement_delta: float,
        interaction_radius: float,
        distance_metric: Literal["euclidean", "manhattan", "chebyshev"] = "euclidean",
    ):
        """Initialize N-dimensional continuous substrate.

        Args:
            bounds: List of (min, max) tuples for each dimension
            boundary: Boundary mode ("clamp", "wrap", "bounce", "sticky")
            movement_delta: Distance discrete actions move agent
            interaction_radius: Distance threshold for affordance interaction
            distance_metric: Distance metric ("euclidean", "manhattan", "chebyshev")

        Raises:
            ValueError: If dimensions < 4 or bounds invalid

        Warnings:
            UserWarning: If dimensions >= 10 (action space size warning)
        """
        # Validate dimension count
        num_dims = len(bounds)
        if num_dims < 4:
            raise ValueError(
                f"ContinuousND requires at least 4 dimensions, got {num_dims}. "
                f"Use Continuous1DSubstrate (1D), Continuous2DSubstrate (2D), or "
                f"Continuous3DSubstrate (3D) instead."
            )

        if num_dims > 100:
            raise ValueError(f"ContinuousND dimension count ({num_dims}) exceeds limit (100)")

        # Warn at N≥10 (action space grows large)
        if num_dims >= 10:
            warnings.warn(
                f"ContinuousND with {num_dims} dimensions has {2 * num_dims + 2} actions. "
                f"Large action spaces may be challenging to train. "
                f"Verify this is intentional for your research.",
                UserWarning,
            )

        # Validate bounds
        for i, (min_val, max_val) in enumerate(bounds):
            if min_val >= max_val:
                raise ValueError(f"Bound {i} invalid: min ({min_val}) must be < max ({max_val})")

            # Check space is large enough for interaction
            range_size = max_val - min_val
            if range_size < interaction_radius:
                raise ValueError(
                    f"Dimension {i} range ({range_size}) < interaction_radius ({interaction_radius}). "
                    f"Space too small for affordance interaction."
                )

        # Validate parameters
        if boundary not in ("clamp", "wrap", "bounce", "sticky"):
            raise ValueError(f"Unknown boundary mode: {boundary}")

        if distance_metric not in ("euclidean", "manhattan", "chebyshev"):
            raise ValueError(f"Unknown distance metric: {distance_metric}")

        if movement_delta <= 0:
            raise ValueError(f"movement_delta must be positive, got {movement_delta}")

        if interaction_radius <= 0:
            raise ValueError(f"interaction_radius must be positive, got {interaction_radius}")

        # Warn if interaction_radius < movement_delta
        if interaction_radius < movement_delta:
            warnings.warn(
                f"interaction_radius ({interaction_radius}) < movement_delta ({movement_delta}). "
                f"Agent may step over affordances without interaction. "
                f"This may be intentional for challenge, but verify configuration.",
                UserWarning,
            )

        # Store configuration
        self.bounds = bounds
        self.boundary = boundary
        self.movement_delta = movement_delta
        self.interaction_radius = interaction_radius
        self.distance_metric = distance_metric

    @property
    def position_dim(self) -> int:
        """Return number of dimensions."""
        return len(self.bounds)

    @property
    def position_dtype(self) -> torch.dtype:
        """Continuous positions are float32."""
        return torch.float32

    @property
    def action_space_size(self) -> int:
        """Return number of discrete actions: 2N + 2.

        ContinuousND uses the standard spatial substrate action space:
        - 2N movement actions (±movement_delta per dimension)
        - 1 INTERACT action
        - 1 WAIT action (lower energy cost than movement)

        This matches Continuous1D/2D/3D for consistency and environment compatibility.

        Returns:
            2*N + 2 where N = position_dim
        """
        return 2 * self.position_dim + 2

    # Implementation methods
    def initialize_positions(self, num_agents: int, device: torch.device) -> torch.Tensor:
        """Initialize random positions uniformly in continuous bounds.

        Returns:
            [num_agents, N] tensor of float positions
        """
        positions = []
        for min_val, max_val in self.bounds:
            dim_positions = torch.rand(num_agents, device=device, dtype=torch.float32) * (max_val - min_val) + min_val
            positions.append(dim_positions)

        return torch.stack(positions, dim=1)

    def apply_movement(self, positions: torch.Tensor, deltas: torch.Tensor) -> torch.Tensor:
        """Apply movement deltas with boundary handling.

        Args:
            positions: [num_agents, N] current positions (float32)
            deltas: [num_agents, N] movement deltas (float32)

        Returns:
            [num_agents, N] new positions after boundary handling
        """
        # Scale deltas by movement_delta
        scaled_deltas = deltas.float() * self.movement_delta
        new_positions = positions + scaled_deltas

        # Apply boundary handling per dimension
        for dim_idx, (min_val, max_val) in enumerate(self.bounds):
            if self.boundary == "clamp":
                new_positions[:, dim_idx] = torch.clamp(new_positions[:, dim_idx], min_val, max_val)

            elif self.boundary == "wrap":
                # Toroidal wraparound
                range_size = max_val - min_val
                # Shift to [0, range_size), wrap, shift back
                new_positions[:, dim_idx] = ((new_positions[:, dim_idx] - min_val) % range_size) + min_val

            elif self.boundary == "bounce":
                # Elastic reflection
                range_size = max_val - min_val

                # Normalize to [0, range_size)
                normalized = new_positions[:, dim_idx] - min_val

                # Reflect about boundaries (multiple bounces)
                # Fold into [0, 2*range_size)
                normalized = normalized % (2 * range_size)

                # If in second half, reflect back
                exceed_half = normalized >= range_size
                normalized[exceed_half] = 2 * range_size - normalized[exceed_half]

                # Denormalize back
                new_positions[:, dim_idx] = normalized + min_val

            elif self.boundary == "sticky":
                # Stay in place if out of bounds
                out_of_bounds = (new_positions[:, dim_idx] < min_val) | (new_positions[:, dim_idx] > max_val)
                new_positions[out_of_bounds, dim_idx] = positions[out_of_bounds, dim_idx]

        return new_positions

    def compute_distance(self, pos1: torch.Tensor, pos2: torch.Tensor) -> torch.Tensor:
        """Compute distance between positions using configured metric.

        Handles broadcasting: pos2 can be [N] or [batch, N].

        Args:
            pos1: [batch, N] positions
            pos2: [N] or [batch, N] positions

        Returns:
            [batch] distances
        """
        # Handle broadcasting: pos2 might be single position [N] or batch [batch, N]
        if pos2.dim() == 1:
            pos2 = pos2.unsqueeze(0)  # [N] → [1, N]

        if self.distance_metric == "euclidean":
            # L2 distance: sqrt(sum of squared differences)
            return torch.sqrt(((pos1 - pos2) ** 2).sum(dim=-1))

        elif self.distance_metric == "manhattan":
            # L1 distance: sum of absolute differences
            return torch.abs(pos1 - pos2).sum(dim=-1)

        elif self.distance_metric == "chebyshev":
            # L∞ distance: max of absolute differences
            return torch.abs(pos1 - pos2).max(dim=-1)[0]

    def _encode_relative(self, positions: torch.Tensor, affordances: dict[str, torch.Tensor]) -> torch.Tensor:
        """Encode positions as normalized coordinates [0, 1] per dimension."""
        num_agents = positions.shape[0]
        device = positions.device

        normalized = torch.zeros((num_agents, len(self.bounds)), dtype=torch.float32, device=device)

        for dim_idx, (min_val, max_val) in enumerate(self.bounds):
            range_size = max_val - min_val
            normalized[:, dim_idx] = (positions[:, dim_idx] - min_val) / range_size

        return normalized

    def _encode_scaled(self, positions: torch.Tensor, affordances: dict[str, torch.Tensor]) -> torch.Tensor:
        """Encode positions as normalized coordinates + range metadata."""
        num_agents = positions.shape[0]
        device = positions.device

        # Get normalized positions
        relative = self._encode_relative(positions, affordances)

        # Add range metadata
        ranges = []
        for min_val, max_val in self.bounds:
            ranges.append(max_val - min_val)

        ranges_tensor = torch.tensor(ranges, dtype=torch.float32, device=device).unsqueeze(0).expand(num_agents, -1)

        return torch.cat([relative, ranges_tensor], dim=1)

    def _encode_absolute(self, positions: torch.Tensor, affordances: dict[str, torch.Tensor]) -> torch.Tensor:
        """Encode positions as raw unnormalized coordinates."""
        return positions

    @property
    def supports_partial_vision(self) -> bool:
        return False

    def get_vision_radius(self, vision_range: float) -> int:
        raise ValueError("Continuous substrates do not support partial vision; no vision radius exists.")

    def normalize_positions(self, positions: torch.Tensor) -> torch.Tensor:
        """Normalize positions to the canonical [0, 1] coordinate range.

        Args:
            positions: [num_agents, position_dim] positions

        Returns:
            [num_agents, position_dim] normalized to [0, 1]
        """
        return self._encode_relative(positions, {})

    # --- Token visibility / egocentric contract (token-obs unit 3, Task 8) -----

    def _token_axis_extents(self, device: torch.device) -> torch.Tensor:
        return torch.tensor([float(max_val - min_val) for min_val, max_val in self.bounds], dtype=torch.float32, device=device)

    def _token_vision_radius(self, vision_range: float) -> float:
        """Radius in world units from the declared fraction of the longest axis extent."""
        longest = max(max_val - min_val for min_val, max_val in self.bounds)
        return vision_range * (longest / 2.0)

    def visible(self, self_pos: torch.Tensor, entity_pos: torch.Tensor, vision_range: float | None) -> torch.Tensor:
        """Declared-metric visibility; wrap-aware (toroidal shortest path under `wrap`)."""
        require_position_batch(self_pos, self.position_dim, argument="self_pos")
        require_position_batch(entity_pos, self.position_dim, argument="entity_pos")
        if vision_range is None:
            return torch.ones((self_pos.shape[0], entity_pos.shape[0]), dtype=torch.bool, device=self_pos.device)
        radius = self._token_vision_radius(vision_range)
        wrap = self._token_axis_extents(self_pos.device) if self.boundary == "wrap" else None
        deltas = pairwise_axis_deltas(self_pos, entity_pos, wrap)
        return combine_metric(deltas.abs(), self.distance_metric) <= radius

    def egocentric_delta(self, self_pos: torch.Tensor, entity_pos: torch.Tensor) -> torch.Tensor:
        """Bounded entity − self per axis, using the shortest path under wrap."""
        require_position_batch(self_pos, self.position_dim, argument="self_pos")
        require_position_batch(entity_pos, self.position_dim, argument="entity_pos")
        wrap = self._token_axis_extents(self_pos.device) if self.boundary == "wrap" else None
        deltas = pairwise_axis_deltas(self_pos, entity_pos, wrap)
        return deltas / self._token_axis_extents(deltas.device)

    def get_valid_neighbors(self, position: torch.Tensor) -> list[torch.Tensor]:
        """Raise error - continuous space has no discrete neighbors.

        Args:
            position: Position tensor (not used)

        Raises:
            NotImplementedError: Continuous substrates don't have discrete neighbors
        """
        raise NotImplementedError(
            "ContinuousND has continuous positions. "
            "No discrete neighbors exist. "
            "Use compute_distance() and interaction_radius for proximity detection."
        )

    def is_on_position(self, agent_positions: torch.Tensor, target_position: torch.Tensor) -> torch.Tensor:
        """Check if agents are within interaction radius of target (proximity-based).

        Args:
            agent_positions: [num_agents, N] agent positions
            target_position: [N] target position

        Returns:
            [num_agents] boolean tensor (True if agent within interaction_radius)
        """
        distance = self.compute_distance(agent_positions, target_position)
        return distance <= self.interaction_radius

    def get_all_positions(self) -> list[list[float]]:
        """Raise error - continuous space has infinite positions."""
        raise NotImplementedError(
            "ContinuousND has infinite positions (continuous space). "
            "Use random sampling for affordance placement instead. "
            "See vectorized_env.py randomize_affordance_positions()."
        )

    def get_capacity(self) -> None:
        """Return None for infinite capacity (continuous space)."""
        return None

    def supports_enumerable_positions(self) -> bool:
        """Continuous substrates have infinite positions."""
        return False

    def get_default_actions(self) -> list[ActionConfig]:
        """Return ContinuousND's 2N+2 default actions (same pattern as GridND).

        Note: Deltas are integers that get scaled by movement_delta in apply_movement().
        """
        actions = []
        action_id = 0
        n_dims = len(self.bounds)

        # Generate movement actions for each dimension
        for dim_idx in range(n_dims):
            # Negative direction
            delta: list[int | float] = [0] * n_dims
            delta[dim_idx] = -1  # Scaled by movement_delta in apply_movement()
            actions.append(
                ActionConfig(
                    id=action_id,
                    name=f"DIM{dim_idx}_NEG",
                    type="movement",
                    delta=delta,
                    teleport_to=None,
                    costs={},
                    effects={},
                    description=f"Move -{self.movement_delta} along dimension {dim_idx}",
                    icon=None,
                    source="substrate",
                    source_affordance=None,
                    enabled=True,
                )
            )
            action_id += 1

            # Positive direction
            delta = [0] * n_dims
            delta[dim_idx] = 1  # Scaled by movement_delta in apply_movement()
            actions.append(
                ActionConfig(
                    id=action_id,
                    name=f"DIM{dim_idx}_POS",
                    type="movement",
                    delta=delta,
                    teleport_to=None,
                    costs={},
                    effects={},
                    description=f"Move +{self.movement_delta} along dimension {dim_idx}",
                    icon=None,
                    source="substrate",
                    source_affordance=None,
                    enabled=True,
                )
            )
            action_id += 1

        # Core interactions
        actions.append(
            ActionConfig(
                id=action_id,
                name="INTERACT",
                type="interaction",
                delta=None,
                teleport_to=None,
                costs={},
                effects={},
                description="Interact with affordance at current position",
                icon=None,
                source="substrate",
                source_affordance=None,
                enabled=True,
            )
        )
        action_id += 1

        actions.append(
            ActionConfig(
                id=action_id,
                name="WAIT",
                type="passive",
                delta=None,
                teleport_to=None,
                costs={},
                effects={},
                description="Wait in place (idle metabolic cost)",
                icon=None,
                source="substrate",
                source_affordance=None,
                enabled=True,
            )
        )

        return actions
