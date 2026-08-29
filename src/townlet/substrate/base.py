"""Abstract base class for spatial substrates."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from townlet.environment.action_config import ActionConfig


def pairwise_axis_deltas(
    self_pos: torch.Tensor,
    entity_pos: torch.Tensor,
    wrap_extents: torch.Tensor | None,
) -> torch.Tensor:
    """Signed per-axis deltas ``entity − self`` as ``[N, M, D]`` float32.

    Shared helper for the token visibility/egocentric contract (token-obs unit 3 Task 8).
    Under wrap (``wrap_extents`` = per-axis extent tensor ``[D]``) each axis delta is the
    toroidal shortest signed path: ``((d + e/2) mod e) − e/2``. The half-extent tie on an
    even extent maps deterministically to the NEGATIVE half (remainder arithmetic) —
    pinned by test, part of the contract.
    """
    deltas = entity_pos.to(dtype=torch.float32).unsqueeze(0) - self_pos.to(dtype=torch.float32).unsqueeze(1)
    if wrap_extents is not None:
        extents = wrap_extents.to(dtype=torch.float32, device=deltas.device)
        deltas = torch.remainder(deltas + extents / 2.0, extents) - extents / 2.0
    return deltas


def combine_metric(abs_deltas: torch.Tensor, distance_metric: str) -> torch.Tensor:
    """Reduce ``[N, M, D]`` absolute per-axis deltas to ``[N, M]`` declared-metric distance."""
    if distance_metric == "manhattan":
        return abs_deltas.sum(dim=-1)
    if distance_metric == "euclidean":
        return torch.sqrt((abs_deltas**2).sum(dim=-1))
    if distance_metric == "chebyshev":
        if abs_deltas.shape[-1] == 0:
            return abs_deltas.sum(dim=-1)
        return abs_deltas.max(dim=-1)[0]
    raise ValueError(f"Unknown distance metric: {distance_metric}")


def require_position_batch(positions: torch.Tensor, position_dim: int, *, argument: str) -> None:
    """Refuse a position batch whose trailing width is not the substrate's position_dim."""
    if positions.dim() != 2 or positions.shape[1] != position_dim:
        raise ValueError(f"{argument} must have shape [batch, position_dim={position_dim}], got {tuple(positions.shape)}")


class SpatialSubstrate(ABC):
    """Abstract interface for spatial substrates.

    A spatial substrate defines:
    - How positions are represented (dimensionality, dtype)
    - How positions are initialized (random, fixed, etc.)
    - How movement is applied (deltas, boundaries)
    - How distance is computed (Manhattan, Euclidean, graph distance)
    - How positions are encoded in observations

    Key insight: The substrate is OPTIONAL. Aspatial universes (pure state
    machines without positioning) are valid and reveal that meters (bars)
    are the true universe.

    Design Principles:
    - Conceptual Agnosticism: Don't assume 2D, Euclidean, or grid-based
    - Permissive Semantics: Allow 3D, hexagonal, continuous, graph, aspatial
    - Structural Enforcement: Validate tensor shapes, boundary behaviors
    """

    @property
    @abstractmethod
    def position_dim(self) -> int:
        """Dimensionality of position vectors.

        Returns:
            0 for aspatial (no positioning)
            2 for 2D grids
            3 for 3D grids
            N for N-dimensional continuous spaces
        """
        pass

    @property
    @abstractmethod
    def position_dtype(self) -> torch.dtype:
        """Data type of position tensors.

        Returns:
            torch.long for discrete grids (integer coordinates)
            torch.float32 for continuous spaces (float coordinates)

        This enables substrates to mix int and float positioning without dtype errors.

        Example:
            Grid2D: torch.long (positions are integers)
            Continuous2D: torch.float32 (positions are floats)
        """
        pass

    @property
    def action_space_size(self) -> int:
        """Return number of discrete actions supported by this substrate.

        Implementations define their default actions via get_default_actions().
        This property returns the length of that action list so grid substrates
        can expose diagonals/vertical movement and continuous substrates can
        define arbitrary action sets.

        Returns:
            Integer count of discrete actions
        """
        return len(self.get_default_actions())

    @abstractmethod
    def get_default_actions(self) -> list["ActionConfig"]:
        """Return substrate's default action space with default costs.

        **CANONICAL ORDERING CONTRACT:**
        All substrates MUST emit actions in this order:
        1. Movement actions (substrate-specific)
        2. INTERACT (second-to-last position)
        3. WAIT (last position)

        This ordering enables downstream systems (ActionSpaceBuilder, environment)
        to consistently identify meta-actions by position:
        - actions[-2] is always INTERACT
        - actions[-1] is always WAIT
        - actions[:-2] are always movement actions (if any)

        Special case: Aspatial substrates have NO movement actions, only [INTERACT, WAIT].

        Returns:
            List of ActionConfig instances with substrate-provided actions.
            IDs are temporary (will be reassigned by ActionSpaceBuilder).

        Examples:
            Grid2D: [UP, DOWN, LEFT, RIGHT, UP_LEFT, UP_RIGHT, DOWN_LEFT, DOWN_RIGHT, INTERACT, WAIT]
            Grid3D: [UP, DOWN, LEFT, RIGHT, UP_LEFT, UP_RIGHT, DOWN_LEFT, DOWN_RIGHT, UP_Z, DOWN_Z, INTERACT, WAIT]
            GridND(7D): [DIM0_NEG, DIM0_POS, ..., DIM6_POS, INTERACT, WAIT]
            Aspatial: [INTERACT, WAIT] (no movement)
        """
        pass

    @abstractmethod
    def initialize_positions(self, num_agents: int, device: torch.device) -> torch.Tensor:
        """Initialize random positions for agents.

        Args:
            num_agents: Number of agents to initialize
            device: PyTorch device (cuda/cpu)

        Returns:
            Tensor of shape [num_agents, position_dim]
            For aspatial substrates: [num_agents, 0]
        """
        pass

    @abstractmethod
    def apply_movement(
        self,
        positions: torch.Tensor,
        deltas: torch.Tensor,
    ) -> torch.Tensor:
        """Apply movement deltas to positions, respecting boundaries.

        Args:
            positions: [num_agents, position_dim] current positions
            deltas: [num_agents, position_dim] movement deltas

        Returns:
            [num_agents, position_dim] new positions after movement

        Boundary handling (clamp, wrap, bounce) is substrate-specific.
        """
        pass

    @abstractmethod
    def compute_distance(
        self,
        pos1: torch.Tensor,
        pos2: torch.Tensor,
    ) -> torch.Tensor:
        """Compute distance between positions.

        Args:
            pos1: [num_agents, position_dim] or [position_dim]
            pos2: [num_agents, position_dim] or [position_dim]

        Returns:
            [num_agents] tensor of distances

        Distance metric is substrate-specific:
        - Grid: Manhattan, Euclidean, or Chebyshev
        - Graph: Shortest path distance
        - Aspatial: Zero (no meaningful distance)
        """
        pass

    # --- Vision contract -----------------------------------------------------
    #
    # What survives of the WS-7 observation-shape contract after the unit-3 token
    # cut. The raster half — `encode_observation`, `get_observation_dim`,
    # `get_grid_encoding_dim`, `get_position_feature_dim`, `get_partial_window_dim`,
    # `encode_partial_observation` — is DELETED with the fixed-width superset ABI it
    # existed to size; nothing asks a substrate for an observation width any more.
    # The token path asks for `position_dim`, `normalize_positions`,
    # `egocentric_delta` and `visible` instead, and POMDP is the same TokenSpec with
    # a radius handed to `visible`.

    @property
    @abstractmethod
    def supports_partial_vision(self) -> bool:
        """Whether this substrate can emit a local vision window (POMDP).

        True only where encode_partial_observation is a real encoding
        (Grid2D, Grid3D). Substrates returning False never receive
        get_vision_radius / get_partial_window_dim calls.
        """
        pass

    @abstractmethod
    def get_vision_radius(self, vision_range: float) -> int:
        """Radius (in cells) for a declared vision_range fraction.

        The single home of the historical `ceil(vision_range * grid_size/2)`
        formula, generalized to the longest axis (identical on squares).
        Substrates without partial vision raise ValueError.
        """
        pass

    @abstractmethod
    def normalize_positions(self, positions: torch.Tensor) -> torch.Tensor:
        """Normalize positions to [0, 1] range (always relative encoding).

        This method ALWAYS returns relative encoding (normalized to [0,1]),
        regardless of the substrate's observation_encoding mode.

        Used by POMDP for position context in recurrent networks, which
        requires normalized positions regardless of how full observations
        are encoded.

        Args:
            positions: [num_agents, position_dim] agent positions

        Returns:
            [num_agents, position_dim] normalized to [0, 1]
            For aspatial substrates: [num_agents, 0] (empty)

        Example:
            Grid2D (8×8): position [3, 4] → [3/7, 4/7] ≈ [0.43, 0.57]
            Continuous2D: position [5.5, 3.2] on [0,10] → [0.55, 0.32]
            Aspatial: any position → [] (empty)
        """
        pass

    @abstractmethod
    def get_valid_neighbors(
        self,
        position: torch.Tensor,
    ) -> list[torch.Tensor]:
        """Get valid neighbor positions for action validation.

        Args:
            position: [position_dim] single position

        Returns:
            List of [position_dim] neighbor positions

        Used for action masking (boundary checks).
        """
        pass

    @abstractmethod
    def is_on_position(
        self,
        agent_positions: torch.Tensor,
        target_position: torch.Tensor,
    ) -> torch.Tensor:
        """Check if agents are on the target position (for interactions).

        Args:
            agent_positions: [num_agents, position_dim]
            target_position: [position_dim]

        Returns:
            [num_agents] bool tensor (True if on target)

        For discrete grids: exact match
        For continuous spaces: proximity threshold
        For aspatial: always True (no positioning concept)
        """
        pass

    @abstractmethod
    def get_all_positions(self) -> list[list[int]] | list[list[float]]:
        """Return all valid positions in the substrate.

        Returns:
            List of positions, where each position is [x, y, ...] (position_dim elements).
            For aspatial substrates, returns empty list.
            For discrete grids (3×3), returns [[0,0], [0,1], [0,2], [1,0], ...] (9 positions) as ints.
            For continuous spaces, raises NotImplementedError (infinite positions).

        Used for affordance randomization to ensure valid placement.
        """
        pass

    @abstractmethod
    def get_capacity(self) -> int | None:
        """Return total number of positions without enumerating them.

        Returns:
            Total positions for finite substrates (discrete grids).
            None for infinite substrates (continuous spaces, aspatial).

        This is more efficient than len(get_all_positions()) for large discrete grids,
        as it calculates capacity analytically without generating all positions.

        Examples:
            - Grid2D (10×10): returns 100
            - GridND ([5,5,5,5]): returns 625
            - Continuous: returns None (infinite positions)
            - Aspatial: returns None (no positions)

        Used for capacity validation in affordance placement.
        """
        pass

    # --- Token visibility / egocentric contract (token-obs unit 3, Task 8) -----
    #
    # The PDR-0041 shape again: the runtime learns spatial-token visibility by asking
    # the substrate instance. These two members are the token path's ONLY spatial
    # gate — `supports_partial_vision` and the window encoders above remain the OLD
    # raster contract, untouched until the unit-3 Task-10 swap retires them.

    @abstractmethod
    def visible(
        self,
        self_pos: torch.Tensor,
        entity_pos: torch.Tensor,
        vision_range: float | None,
    ) -> torch.Tensor:
        """Which entities each agent can see under the declared metric + boundary mode.

        Args:
            self_pos: [N, position_dim] observer positions
            entity_pos: [M, position_dim] entity positions
            vision_range: normalized fraction of the longest axis (the POMDP meaning),
                or None for full observability (pass-all)

        Returns:
            [N, M] bool — True where the entity is within the vision radius of the
            observer. Distance is the DECLARED metric; only `wrap` boundary mode changes
            it (toroidal shortest path) — clamp/bounce/sticky are in-bounds position
            regimes with plain metric distance. Aspatial substrates return all-True
            (no positions, nothing to hide).
        """

    @abstractmethod
    def egocentric_delta(self, self_pos: torch.Tensor, entity_pos: torch.Tensor) -> torch.Tensor:
        """Per-axis ``entity − self`` deltas, shortest-path under wrap.

        Args:
            self_pos: [N, position_dim] observer positions
            entity_pos: [M, position_dim] entity positions

        Returns:
            [N, M, position_dim] float32, normalized per the declared observation
            encoding mode: `relative` divides by the same denominator as
            normalize_positions (span − 1 for grids, extent for continuous), so deltas
            land in [−1, 1]; `scaled` and `absolute` return raw axis units. Aspatial:
            zeros of width 0.
        """
