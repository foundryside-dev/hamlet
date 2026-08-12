"""
Sequential Replay Buffer for LSTM Training.

CRIT-07: Updated to use single 'rewards' field for DAC-composed totals.
Episodes store pre-composed total rewards with optional component breakdown.

format_version 4: Requires 'next_observations' (WS-1(c): the successor of the
last index of a sampled window, needed for the boundary bootstrap).
format_version 3 included optional reward components (rewards_extrinsic,
rewards_intrinsic, rewards_shaping) for TensorBoard analysis.

Unlike standard replay buffers that sample individual transitions,
this buffer stores complete episodes and samples sequences of consecutive
transitions to maintain temporal structure for recurrent networks.
"""

from __future__ import annotations

import random
from collections import deque  # MED-02: Use deque for O(1) popleft
from typing import Any

import torch

Episode = dict[str, torch.Tensor]


class SequentialReplayBuffer:
    """
    Replay buffer that maintains temporal structure for LSTM training.

    Episodes store single 'rewards' field with DAC-composed totals, plus optional
    component breakdown (rewards_extrinsic, rewards_intrinsic, rewards_shaping).

    Stores complete episodes and samples sequences of consecutive transitions.
    This is essential for training recurrent networks which need temporal context.

    Attributes:
        capacity: Maximum number of transitions to store
        device: Device to store tensors on
        episodes: List of stored episodes (each is a dict of tensors)
        num_transitions: Total number of transitions stored
    """

    def __init__(self, capacity: int, device: torch.device):
        """
        Initialize sequential replay buffer.

        Args:
            capacity: Maximum number of transitions to store
            device: Device to store tensors on (CPU or CUDA)

        Raises:
            ValueError: If capacity <= 0
        """
        # LOW-02: Validate positive capacity
        if capacity <= 0:
            raise ValueError(f"Buffer capacity must be positive, got {capacity}")

        self.capacity = capacity
        self.device = device
        self.episodes: deque[Episode] = deque()  # MED-02: deque for O(1) popleft
        self.num_transitions = 0

    def __len__(self) -> int:
        """Return number of episodes stored."""
        return len(self.episodes)

    def clear(self) -> None:
        """Reset buffer to empty state and deallocate all episode storage.

        Clears the episode deque and resets transition count to 0.
        Buffer can be reused after clearing.
        """
        self.episodes = deque()  # MED-02: Reset to empty deque
        self.num_transitions = 0

    def stats(self) -> dict[str, Any]:
        """Return buffer statistics for introspection.

        Returns:
            Dictionary with keys:
                - size: Total number of transitions stored (same as num_transitions)
                - capacity: Maximum buffer capacity in transitions
                - occupancy_ratio: num_transitions / capacity (0.0 to 1.0)
                - memory_bytes: Approximate memory usage in bytes
                - device: Device string (e.g., 'cpu', 'cuda:0')
                - num_episodes: Number of episodes stored
                - num_transitions: Total transitions across all episodes
        """
        # Calculate memory usage across all episodes
        memory_bytes = 0
        for episode in self.episodes:
            for tensor in episode.values():
                memory_bytes += tensor.element_size() * tensor.numel()

        # Calculate occupancy ratio
        occupancy_ratio = self.num_transitions / self.capacity if self.capacity > 0 else 0.0

        return {
            "size": self.num_transitions,
            "capacity": self.capacity,
            "occupancy_ratio": occupancy_ratio,
            "memory_bytes": memory_bytes,
            "device": str(self.device),
            "num_episodes": len(self.episodes),
            "num_transitions": self.num_transitions,
        }

    def store_episode(self, episode: Episode) -> None:
        """
        Store a complete episode.

        CRIT-07: Now requires 'rewards' key with pre-composed totals.
        WS-1(c): 'next_observations' is REQUIRED - the boundary bootstrap needs the
        successor of every timestep, and a missing key must fail loudly, not default.
        Component keys (rewards_extrinsic, rewards_intrinsic, rewards_shaping) are optional.

        Args:
            episode: Dict with keys:
                - 'observations': [seq_len, obs_dim]
                - 'actions': [seq_len]
                - 'rewards': [seq_len] - DAC-composed total rewards
                - 'dones': [seq_len]
                - 'next_observations': [seq_len, obs_dim] - successor observations
                - 'rewards_extrinsic': [seq_len] (optional) - extrinsic component
                - 'rewards_intrinsic': [seq_len] (optional) - intrinsic component
                - 'rewards_shaping': [seq_len] (optional) - shaping component

        Raises:
            ValueError: If episode structure is invalid
        """
        # Validate episode structure
        required_keys = {"observations", "actions", "rewards", "dones", "next_observations"}
        optional_component_keys = {"rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"}

        missing_keys = required_keys - set(episode.keys())
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")

        # LOW-01: Validate episode has positive length
        seq_len = len(episode["observations"])
        if seq_len == 0:
            raise ValueError("Cannot store zero-length episode (no transitions)")

        # LOW-15: Validate tensor shapes for consistency
        for key, tensor in episode.items():
            if len(tensor) != seq_len:
                raise ValueError(f"Episode tensor length mismatch: observations has {seq_len} steps, but {key} has {len(tensor)} steps")

        # LOW-15: Validate tensor dimensionality
        if episode["observations"].ndim != 2:
            raise ValueError(f"observations must be 2D [seq_len, obs_dim], got shape {episode['observations'].shape}")
        if episode["actions"].ndim != 1:
            raise ValueError(f"actions must be 1D [seq_len], got shape {episode['actions'].shape}")
        if episode["rewards"].ndim != 1:
            raise ValueError(f"rewards must be 1D [seq_len], got shape {episode['rewards'].shape}")
        if episode["dones"].ndim != 1:
            raise ValueError(f"dones must be 1D [seq_len], got shape {episode['dones'].shape}")
        if episode["next_observations"].ndim != 2:
            raise ValueError(f"next_observations must be 2D [seq_len, obs_dim], got shape {episode['next_observations'].shape}")

        # Validate optional component keys if present
        for component_key in optional_component_keys:
            if component_key in episode:
                if episode[component_key].ndim != 1:
                    raise ValueError(f"{component_key} must be 1D [seq_len], got shape {episode[component_key].shape}")
                if len(episode[component_key]) != seq_len:
                    comp_len = len(episode[component_key])
                    raise ValueError(
                        f"Episode tensor length mismatch: observations has {seq_len} steps, " f"but {component_key} has {comp_len} steps"
                    )

        # Move episode to correct device
        episode_on_device: Episode = {key: tensor.to(self.device) for key, tensor in episode.items()}

        # Add episode
        self.episodes.append(episode_on_device)
        self.num_transitions += seq_len

        # MED-02: Evict oldest episodes if over capacity (O(1) popleft with deque)
        while self.num_transitions > self.capacity and len(self.episodes) > 0:
            oldest_episode = self.episodes.popleft()  # O(1) instead of O(n) pop(0)
            self.num_transitions -= len(oldest_episode["observations"])

    def sample_sequences(self, batch_size: int, seq_len: int) -> dict[str, torch.Tensor]:
        """
        Sample a batch of sequential transitions.

        CRIT-07: Rewards are already composed by DAC before storage.
        MED-13: Removed dead intrinsic_weight parameter (always 1.0 post-DAC).

        Args:
            batch_size: Number of sequences to sample
            seq_len: Length of each sequence

        Returns:
            Dict with keys:
                - 'observations': [batch_size, seq_len, obs_dim]
                - 'actions': [batch_size, seq_len]
                - 'rewards': [batch_size, seq_len]
                - 'dones': [batch_size, seq_len]
                - 'next_observations': [batch_size, seq_len, obs_dim] - successors
                  (WS-1(c): [:, -1] is the window-boundary bootstrap target)
                - 'mask': [batch_size, seq_len] bool - True for valid timesteps,
                          False after terminal (for post-terminal masking in loss)

        Raises:
            ValueError: If not enough data to sample
        """
        # Check if we have enough data
        if len(self.episodes) == 0:
            raise ValueError("Cannot sample: buffer is empty (not enough data)")

        # Find episodes long enough for the requested sequence length
        valid_episodes = [ep for ep in self.episodes if len(ep["observations"]) >= seq_len]

        if not valid_episodes:
            # Provide detailed error message for debugging
            episode_lengths = [len(ep["observations"]) for ep in self.episodes]
            max_length = max(episode_lengths) if episode_lengths else 0
            raise ValueError(
                f"Cannot sample: no episodes long enough for seq_len={seq_len}. "
                f"Buffer has {len(self.episodes)} episodes with lengths: {episode_lengths[:10]}"
                f"{' (showing first 10)' if len(episode_lengths) > 10 else ''}. "
                f"Max episode length: {max_length}. "
                f"Hint: If this occurs in tests that don't intend to test training, "
                f"disable training with train_frequency=10000 or use the "
                f"non_training_recurrent_population fixture."
            )

        # Sample batch_size sequences
        sampled_sequences = []

        # LOW-14: Weight episode selection by length for uniform transition sampling
        # Without weighting, short episodes are oversampled relative to their contribution
        episode_lengths = [len(ep["observations"]) for ep in valid_episodes]

        for _ in range(batch_size):
            # Randomly select an episode weighted by length (uniform transition sampling)
            episode = random.choices(valid_episodes, weights=episode_lengths, k=1)[0]

            # Randomly select a starting position (ensuring we can get seq_len transitions)
            ep_len = episode["observations"].shape[0]
            max_start = ep_len - seq_len
            start_idx = random.randint(0, max_start)
            end_idx = start_idx + seq_len

            # Extract sequence
            sequence = {
                "observations": episode["observations"][start_idx:end_idx],
                "actions": episode["actions"][start_idx:end_idx],
                "rewards": episode["rewards"][start_idx:end_idx],  # CRIT-07: Use pre-composed rewards
                "dones": episode["dones"][start_idx:end_idx],
                "next_observations": episode["next_observations"][start_idx:end_idx],
            }

            # Create validity mask (P2.2: Post-terminal masking)
            # Mask is True up to and including terminal, False after
            dones_seq = episode["dones"][start_idx:end_idx]
            mask = torch.ones(seq_len, dtype=torch.bool, device=self.device)

            # Find first terminal in sequence
            terminal_positions = torch.nonzero(dones_seq, as_tuple=False)
            if terminal_positions.numel() > 0:
                terminal_idx = int(terminal_positions[0].item())
                # Mask out everything AFTER terminal (terminal itself is valid)
                if terminal_idx < seq_len - 1:
                    mask[terminal_idx + 1 :] = False

            sequence["mask"] = mask

            sampled_sequences.append(sequence)

        # Stack sequences into batch
        batch = {
            "observations": torch.stack([s["observations"] for s in sampled_sequences]),
            "actions": torch.stack([s["actions"] for s in sampled_sequences]),
            "rewards": torch.stack([s["rewards"] for s in sampled_sequences]),
            "dones": torch.stack([s["dones"] for s in sampled_sequences]),
            "next_observations": torch.stack([s["next_observations"] for s in sampled_sequences]),
            "mask": torch.stack([s["mask"] for s in sampled_sequences]),
        }

        return batch

    def serialize(self) -> dict[str, Any]:
        """
        Serialize episode buffer for checkpointing (P1.1).

        format_version 4 requires 'next_observations' (WS-1(c)).

        Returns:
            Dictionary with all episodes on CPU for saving
        """
        if len(self.episodes) == 0:
            return {
                "format_version": 4,  # Version 4 requires next_observations (WS-1(c))
                "num_transitions": 0,
                "episodes": [],
                "capacity": self.capacity,
            }

        # Convert episodes to CPU tensors
        serialized_episodes: list[dict[str, torch.Tensor]] = []
        for episode in self.episodes:
            serialized_episode = {
                "observations": episode["observations"].cpu(),
                "actions": episode["actions"].cpu(),
                "rewards": episode["rewards"].cpu(),
                "dones": episode["dones"].cpu(),
                "next_observations": episode["next_observations"].cpu(),
            }
            # Add components if present
            for key in ["rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"]:
                if key in episode:
                    serialized_episode[key] = episode[key].cpu()
            serialized_episodes.append(serialized_episode)

        return {
            "format_version": 4,  # Version 4 requires next_observations (WS-1(c))
            "num_transitions": self.num_transitions,
            "episodes": serialized_episodes,
            "capacity": self.capacity,
        }

    def load_from_serialized(self, state: dict[str, Any]) -> None:
        """
        Restore episode buffer from serialized state (P1.1).

        Now requires format_version >= 4. Legacy formats not supported.

        Args:
            state: Dictionary from serialize()

        Raises:
            ValueError: If loading legacy format (version < 4)
        """
        # Reject legacy format (per CLAUDE.md: zero backwards compatibility)
        format_version = state.get("format_version", 1)
        if format_version < 4:
            raise ValueError(
                "Cannot load legacy sequential buffer checkpoint (format_version < 4). "
                "Regenerate checkpoint with current Townlet version."
            )

        self.num_transitions = state["num_transitions"]

        # MED-17: Validate capacity similar to replay_buffer.py HIGH-02 fix
        if self.num_transitions > self.capacity:
            raise ValueError(
                f"Cannot load buffer: loaded num_transitions ({self.num_transitions}) exceeds buffer capacity ({self.capacity}). "
                f"Either increase buffer capacity in config or regenerate checkpoint with smaller buffer."
            )

        self.episodes = deque()  # MED-02: Use deque consistently

        # Restore episodes to device
        for ep_state in state["episodes"]:
            episode = {
                "observations": ep_state["observations"].to(self.device),
                "actions": ep_state["actions"].to(self.device),
                "rewards": ep_state["rewards"].to(self.device),
                "dones": ep_state["dones"].to(self.device),
                "next_observations": ep_state["next_observations"].to(self.device),
            }
            # Restore components if present
            for key in ["rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"]:
                if key in ep_state:
                    episode[key] = ep_state[key].to(self.device)
            self.episodes.append(episode)
