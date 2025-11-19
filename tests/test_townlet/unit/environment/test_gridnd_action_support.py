"""Tests for N-dimensional substrate support in VectorizedHamletEnv.

These tests guard against regressions when enabling GridND/ContinuousND
substrates with position_dim >= 4. They focus on action execution and masking,
which are critical for the new high-dimensional environments.
"""

from __future__ import annotations

import itertools
import shutil
from pathlib import Path

import pytest
import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv


@pytest.fixture
def gridnd_4d_config_pack(tmp_path: Path) -> Path:
    """Create a temporary config pack backed by a 4D GridND substrate."""
    project_root = Path(__file__).parent.parent.parent.parent.parent
    source_config = project_root / "configs" / "test" / "gridnd_4d_pack"
    dest_config = tmp_path / "gridnd_4d_support"

    shutil.copytree(source_config, dest_config)
    cache_dir = dest_config / ".compiled"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    return dest_config


@pytest.fixture
def gridnd_env(
    gridnd_4d_config_pack: Path,
    cpu_device: torch.device,
) -> VectorizedHamletEnv:
    """Instantiate a 4D GridND environment for action support tests."""
    from townlet.universe.compiler import UniverseCompiler

    universe = UniverseCompiler().compile(gridnd_4d_config_pack, use_cache=False)
    return VectorizedHamletEnv.from_universe(
        universe,
        level_name="L0_test",
        num_agents=1,
        device=cpu_device,
    )


class TestGridNDActions:
    """Validate VectorizedHamletEnv behavior for N-dimensional substrates."""

    def test_interact_mask_uses_nd_index(self, gridnd_env: VectorizedHamletEnv) -> None:
        """INTERACT mask should live at index 2 * position_dim for GridND."""
        env = gridnd_env
        env.reset()

        interact_idx = 2 * env.substrate.position_dim

        # Find a position that is guaranteed to be off all affordances.
        occupied_positions = {tuple(pos.tolist()) for pos in env.affordances.values()}
        candidate_position_tensor = None
        for candidate in itertools.product(*(range(size) for size in env.substrate.dimension_sizes)):
            if candidate not in occupied_positions:
                candidate_position_tensor = torch.tensor(candidate, dtype=env.positions.dtype, device=env.device)
                break

        assert candidate_position_tensor is not None, "Expected at least one free cell in GridND test config"

        env.positions[0] = candidate_position_tensor
        action_masks = env.get_action_masks()

        assert not action_masks[0, interact_idx], "INTERACT should be masked off-affordance at index 2 * position_dim"

    def test_execute_actions_supports_high_dim_movements(self, gridnd_env: VectorizedHamletEnv) -> None:
        """_execute_actions should handle ± movements for every GridND axis."""
        env = gridnd_env
        env.reset()

        dim_sizes = env.substrate.dimension_sizes
        last_dim = env.substrate.position_dim - 1

        start_position = torch.tensor(
            [size // 2 for size in dim_sizes],
            dtype=env.positions.dtype,
            device=env.device,
        )
        env.positions[0] = start_position.clone()

        positive_action_index = env.substrate.position_dim + last_dim  # D{last_dim}_POS
        actions = torch.tensor([positive_action_index], device=env.device)

        env.step(actions)

        expected_position = start_position.clone()
        expected_position[last_dim] = min(dim_sizes[last_dim] - 1, start_position[last_dim].item() + 1)

        assert torch.equal(env.positions[0], expected_position), "High-dimensional movement should update the targeted axis"
