"""3D cubic grid substrate with integer coordinates (x, y, z)."""

import math
from typing import Literal

import torch

from townlet.environment.action_config import ActionConfig

from .base import SpatialSubstrate, combine_metric, pairwise_axis_deltas, require_position_batch


class Grid3DSubstrate(SpatialSubstrate):
    """3D cubic grid substrate.

    Position representation: [x, y, z] where:
    - x ∈ [0, width)
    - y ∈ [0, height)
    - z ∈ [0, depth)

    Movement actions: 6 directions (±x, ±y, ±z)

    Observation encoding: Normalized coordinates [0, 1] (not one-hot)
    - Prevents dimension explosion (3 dims instead of width*height*depth)
    - Matches Continuous substrate encoding strategy
    - Network learns spatial relationships

    Boundary modes:
    - clamp: Hard walls (position clamped to bounds)
    - wrap: Toroidal wraparound (Pac-Man in 3D)
    - bounce: Elastic reflection
    - sticky: Stay in place when hitting boundary

    Distance metrics:
    - manhattan: L1 norm, |x1-x2| + |y1-y2| + |z1-z2| (matches 6-directional movement)
    - euclidean: L2 norm, sqrt((x1-x2)² + (y1-y2)² + (z1-z2)²) (straight-line distance)
    - chebyshev: L∞ norm, max(|x1-x2|, |y1-y2|, |z1-z2|) (king's move in 3D)
    """

    position_dim = 3
    position_dtype = torch.long

    def __init__(
        self,
        width: int,
        height: int,
        depth: int,
        boundary: Literal["clamp", "wrap", "bounce", "sticky"],
        distance_metric: Literal["manhattan", "euclidean", "chebyshev"] = "manhattan",
        topology: Literal["cubic"] = "cubic",  # NEW: Grid3D is always cubic topology
        enable_diagonals: bool = True,
    ):
        """Initialize 3D cubic grid.

        Args:
            width: Number of cells in X dimension
            height: Number of cells in Y dimension
            depth: Number of cells in Z dimension (floors/layers)
            boundary: Boundary mode
            distance_metric: Distance calculation method
            topology: Grid topology ("cubic" for 3D Cartesian grid)
        """
        if width <= 0 or height <= 0 or depth <= 0:
            raise ValueError(f"Grid dimensions must be positive: {width}×{height}×{depth}\nExample: width: 8, height: 8, depth: 3")
        if boundary not in ("clamp", "wrap", "bounce", "sticky"):
            raise ValueError(f"Unknown boundary mode: {boundary}")
        if distance_metric not in ("manhattan", "euclidean", "chebyshev"):
            raise ValueError(f"Unknown distance metric: {distance_metric}")

        self.width = width
        self.height = height
        self.depth = depth
        self.boundary = boundary
        self.distance_metric = distance_metric
        self.topology = topology  # NEW: Store topology
        self.enable_diagonals = enable_diagonals

    @property
    def coordinate_semantics(self) -> dict:
        """Describe what each dimension represents."""
        return {
            "X": "horizontal",  # Left/right
            "Y": "vertical",  # Up/down (screen coordinates)
            "Z": "depth",  # Floor/layer
        }

    def initialize_positions(self, num_agents: int, device: torch.device) -> torch.Tensor:
        """Randomly initialize positions in 3D grid."""
        return torch.stack(
            [
                torch.randint(0, self.width, (num_agents,), device=device),
                torch.randint(0, self.height, (num_agents,), device=device),
                torch.randint(0, self.depth, (num_agents,), device=device),
            ],
            dim=1,
        )

    def apply_movement(self, positions: torch.Tensor, deltas: torch.Tensor) -> torch.Tensor:
        """Apply movement deltas with boundary handling in 3D."""
        new_positions = positions + deltas.long()

        if self.boundary == "clamp":
            new_positions[:, 0] = torch.clamp(new_positions[:, 0], 0, self.width - 1)
            new_positions[:, 1] = torch.clamp(new_positions[:, 1], 0, self.height - 1)
            new_positions[:, 2] = torch.clamp(new_positions[:, 2], 0, self.depth - 1)

        elif self.boundary == "wrap":
            new_positions[:, 0] = new_positions[:, 0] % self.width
            new_positions[:, 1] = new_positions[:, 1] % self.height
            new_positions[:, 2] = new_positions[:, 2] % self.depth

        elif self.boundary == "bounce":
            for dim, max_val in enumerate([self.width, self.height, self.depth]):
                negative_mask = new_positions[:, dim] < 0
                new_positions[negative_mask, dim] = -new_positions[negative_mask, dim]

                exceed_mask = new_positions[:, dim] >= max_val
                new_positions[exceed_mask, dim] = 2 * (max_val - 1) - new_positions[exceed_mask, dim]

                new_positions[:, dim] = torch.clamp(new_positions[:, dim], 0, max_val - 1)

        elif self.boundary == "sticky":
            for dim, max_val in enumerate([self.width, self.height, self.depth]):
                out_of_bounds = (new_positions[:, dim] < 0) | (new_positions[:, dim] >= max_val)
                new_positions[out_of_bounds, dim] = positions[out_of_bounds, dim]

        return new_positions

    def compute_distance(self, pos1: torch.Tensor, pos2: torch.Tensor) -> torch.Tensor:
        """Compute distance between positions in 3D."""
        if self.distance_metric == "manhattan":
            return torch.abs(pos1 - pos2).sum(dim=-1)
        elif self.distance_metric == "euclidean":
            return torch.sqrt(((pos1 - pos2) ** 2).sum(dim=-1))
        elif self.distance_metric == "chebyshev":
            return torch.abs(pos1 - pos2).max(dim=-1)[0]

    def get_default_actions(self) -> list[ActionConfig]:
        """Return Grid3D's default actions, optionally including XY-plane diagonals."""
        actions: list[ActionConfig] = [
            # XY plane movement (cardinal)
            ActionConfig(
                id=0,
                name="UP",
                type="movement",
                delta=[0, -1, 0],
                teleport_to=None,
                costs={},
                effects={},
                description="Move one cell upward (north)",
                icon=None,
                source="substrate",
                source_affordance=None,
                enabled=True,
            ),
            ActionConfig(
                id=1,
                name="DOWN",
                type="movement",
                delta=[0, 1, 0],
                teleport_to=None,
                costs={},
                effects={},
                description="Move one cell downward (south)",
                icon=None,
                source="substrate",
                source_affordance=None,
                enabled=True,
            ),
            ActionConfig(
                id=2,
                name="LEFT",
                type="movement",
                delta=[-1, 0, 0],
                teleport_to=None,
                costs={},
                effects={},
                description="Move one cell left (west)",
                icon=None,
                source="substrate",
                source_affordance=None,
                enabled=True,
            ),
            ActionConfig(
                id=3,
                name="RIGHT",
                type="movement",
                delta=[1, 0, 0],
                teleport_to=None,
                costs={},
                effects={},
                description="Move one cell right (east)",
                icon=None,
                source="substrate",
                source_affordance=None,
                enabled=True,
            ),
        ]

        if self.enable_diagonals:
            actions.extend(
                [
                    ActionConfig(
                        id=4,
                        name="UP_LEFT",
                        type="movement",
                        delta=[-1, -1, 0],
                        teleport_to=None,
                        costs={},
                        effects={},
                        description="Move one cell diagonally up-left (northwest)",
                        icon=None,
                        source="substrate",
                        source_affordance=None,
                        enabled=True,
                    ),
                    ActionConfig(
                        id=5,
                        name="UP_RIGHT",
                        type="movement",
                        delta=[1, -1, 0],
                        teleport_to=None,
                        costs={},
                        effects={},
                        description="Move one cell diagonally up-right (northeast)",
                        icon=None,
                        source="substrate",
                        source_affordance=None,
                        enabled=True,
                    ),
                    ActionConfig(
                        id=6,
                        name="DOWN_LEFT",
                        type="movement",
                        delta=[-1, 1, 0],
                        teleport_to=None,
                        costs={},
                        effects={},
                        description="Move one cell diagonally down-left (southwest)",
                        icon=None,
                        source="substrate",
                        source_affordance=None,
                        enabled=True,
                    ),
                    ActionConfig(
                        id=7,
                        name="DOWN_RIGHT",
                        type="movement",
                        delta=[1, 1, 0],
                        teleport_to=None,
                        costs={},
                        effects={},
                        description="Move one cell diagonally down-right (southeast)",
                        icon=None,
                        source="substrate",
                        source_affordance=None,
                        enabled=True,
                    ),
                ]
            )

        # Z-axis movement (vertical)
        actions.extend(
            [
                ActionConfig(
                    id=len(actions),
                    name="UP_Z",
                    type="movement",
                    delta=[0, 0, -1],
                    teleport_to=None,
                    costs={},
                    effects={},
                    description="Move one floor up (climb stairs)",
                    icon=None,
                    source="substrate",
                    source_affordance=None,
                    enabled=True,
                ),
                ActionConfig(
                    id=len(actions) + 1,
                    name="DOWN_Z",
                    type="movement",
                    delta=[0, 0, 1],
                    teleport_to=None,
                    costs={},
                    effects={},
                    description="Move one floor down (descend stairs)",
                    icon=None,
                    source="substrate",
                    source_affordance=None,
                    enabled=True,
                ),
            ]
        )

        # Core interactions (same as Grid2D; WAIT is custom-only)
        actions.extend(
            [
                ActionConfig(
                    id=len(actions),
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
                ),
            ]
        )

        return actions

    def is_on_position(self, positions: torch.Tensor, target_position: torch.Tensor) -> torch.Tensor:
        """Check if agents are on target position (exact match in 3D)."""
        return (positions == target_position).all(dim=-1)

    def _encode_relative(
        self,
        positions: torch.Tensor,
        affordances: dict[str, torch.Tensor],
    ) -> torch.Tensor:
        """Encode positions as normalized coordinates [0, 1].

        Args:
            positions: Agent positions [num_agents, 3]
            affordances: Affordance positions (currently unused)

        Returns:
            [num_agents, 3] normalized positions
        """
        num_agents = positions.shape[0]
        device = positions.device

        normalized = torch.zeros((num_agents, 3), dtype=torch.float32, device=device)
        normalized[:, 0] = positions[:, 0].float() / max(self.width - 1, 1)
        normalized[:, 1] = positions[:, 1].float() / max(self.height - 1, 1)
        normalized[:, 2] = positions[:, 2].float() / max(self.depth - 1, 1)

        return normalized

    def _encode_scaled(
        self,
        positions: torch.Tensor,
        affordances: dict[str, torch.Tensor],
    ) -> torch.Tensor:
        """Encode positions as normalized coordinates + range metadata.

        Args:
            positions: Agent positions [num_agents, 3]
            affordances: Affordance positions (currently unused)

        Returns:
            [num_agents, 6] normalized positions + range sizes
            First 3 dims: normalized [0, 1]
            Last 3 dims: (width, height, depth)
        """
        num_agents = positions.shape[0]
        device = positions.device

        # Get normalized positions
        relative = self._encode_relative(positions, affordances)

        # Add range metadata
        ranges = (
            torch.tensor(
                [float(self.width), float(self.height), float(self.depth)],
                dtype=torch.float32,
                device=device,
            )
            .unsqueeze(0)
            .expand(num_agents, -1)
        )

        return torch.cat([relative, ranges], dim=1)

    def _encode_absolute(
        self,
        positions: torch.Tensor,
        affordances: dict[str, torch.Tensor],
    ) -> torch.Tensor:
        """Encode positions as raw unnormalized coordinates.

        Args:
            positions: Agent positions [num_agents, 3]
            affordances: Affordance positions (currently unused)

        Returns:
            [num_agents, 3] raw coordinates (as float)
        """
        return positions.float()

    @property
    def supports_partial_vision(self) -> bool:
        return True

    def get_vision_radius(self, vision_range: float) -> int:
        """Radius from the declared fraction of the longest axis (min 1)."""
        span = max(self.width, self.height, self.depth)
        return max(1, int(math.ceil(vision_range * (span / 2.0))))

    # --- Token visibility / egocentric contract (token-obs unit 3, Task 8) -----

    def _token_axis_sizes(self, device: torch.device) -> torch.Tensor:
        return torch.tensor([float(self.width), float(self.height), float(self.depth)], dtype=torch.float32, device=device)

    def visible(self, self_pos: torch.Tensor, entity_pos: torch.Tensor, vision_range: float | None) -> torch.Tensor:
        """Declared-metric visibility; wrap-aware (toroidal shortest path under `wrap`)."""
        require_position_batch(self_pos, self.position_dim, argument="self_pos")
        require_position_batch(entity_pos, self.position_dim, argument="entity_pos")
        if vision_range is None:
            return torch.ones((self_pos.shape[0], entity_pos.shape[0]), dtype=torch.bool, device=self_pos.device)
        radius = float(self.get_vision_radius(vision_range))
        wrap = self._token_axis_sizes(self_pos.device) if self.boundary == "wrap" else None
        deltas = pairwise_axis_deltas(self_pos, entity_pos, wrap)
        return combine_metric(deltas.abs(), self.distance_metric) <= radius

    def egocentric_delta(self, self_pos: torch.Tensor, entity_pos: torch.Tensor) -> torch.Tensor:
        """Bounded entity − self per axis, using the shortest path under wrap."""
        require_position_batch(self_pos, self.position_dim, argument="self_pos")
        require_position_batch(entity_pos, self.position_dim, argument="entity_pos")
        wrap = self._token_axis_sizes(self_pos.device) if self.boundary == "wrap" else None
        deltas = pairwise_axis_deltas(self_pos, entity_pos, wrap)
        denominators = torch.tensor(
            [
                float(max(self.width - 1, 1)),
                float(max(self.height - 1, 1)),
                float(max(self.depth - 1, 1)),
            ],
            dtype=torch.float32,
            device=deltas.device,
        )
        return deltas / denominators

    def normalize_positions(self, positions: torch.Tensor) -> torch.Tensor:
        """Normalize positions to the canonical [0, 1] coordinate range.

        Args:
            positions: [num_agents, 3] grid positions

        Returns:
            [num_agents, 3] normalized to [0, 1]
        """
        return self._encode_relative(positions, {})

    def get_all_positions(self) -> list[list[int]]:
        """Get all valid positions in 3D grid."""
        positions = []
        for z in range(self.depth):
            for y in range(self.height):
                for x in range(self.width):
                    positions.append([x, y, z])
        return positions

    def get_capacity(self) -> int:
        """Calculate total positions analytically (width × height × depth)."""
        return self.width * self.height * self.depth

    def get_valid_neighbors(self, position: torch.Tensor) -> list[torch.Tensor]:
        """Get 6 cardinal neighbors in 3D (±x, ±y, ±z).

        Args:
            position: Position tensor [3] or list of [x, y, z]

        Returns:
            List of neighbor position tensors
        """
        if isinstance(position, torch.Tensor):
            x, y, z = position.tolist()
        else:
            x, y, z = position

        neighbors = [
            [x, y - 1, z],  # Negative Y
            [x, y + 1, z],  # Positive Y
            [x - 1, y, z],  # Negative X
            [x + 1, y, z],  # Positive X
            [x, y, z - 1],  # Negative Z
            [x, y, z + 1],  # Positive Z
        ]

        if self.boundary == "clamp":
            neighbors = [n for n in neighbors if 0 <= n[0] < self.width and 0 <= n[1] < self.height and 0 <= n[2] < self.depth]

        return [torch.tensor(n, dtype=torch.long) for n in neighbors]

    def supports_enumerable_positions(self) -> bool:
        """Grid3D has a finite set of discrete cells that can be enumerated."""
        return True
