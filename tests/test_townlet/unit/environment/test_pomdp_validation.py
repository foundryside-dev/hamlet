"""Tests for POMDP validation in VectorizedHamletEnv (v2.1 packs)."""

import pytest
import torch

from tests.test_townlet.helpers.config_builder import mutate_curriculum_yaml, mutate_stratum_yaml
from tests.test_townlet.utils.builders import make_vectorized_env_from_pack


def _set_partial(curriculum):
    curriculum["curriculum"]["active_vision"] = "partial"


class TestGridNDPOMDPValidation:
    """Test POMDP rejection for N≥4 dimensional grids."""

    @pytest.fixture
    def gridnd_4d_config_pack(self, config_pack_factory):
        """Create minimal 4D GridND config pack."""
        config_dir = config_pack_factory(name="gridnd_4d")

        # Set substrate to 4D gridnd
        def mutate_stratum(data: dict) -> None:
            stratum = data["stratum"]
            stratum["substrate"] = {
                "type": "gridnd",
                "gridnd": {
                    "dimension_sizes": [5, 5, 5, 5],
                    "boundary": "clamp",
                    "distance_metric": "manhattan",
                    "topology": "hypercube",
                },
            }

        mutate_stratum_yaml(config_dir, mutate_stratum)
        mutate_curriculum_yaml(config_dir, _set_partial)
        return config_dir

    def test_gridnd_4d_pomdp_rejected(self, gridnd_4d_config_pack):
        """GridND should reject partial observability."""
        with pytest.raises(ValueError, match=r"Partial observability .* 4D substrates"):
            make_vectorized_env_from_pack(
                gridnd_4d_config_pack,
                level_name="L0_test",
                num_agents=1,
                device=torch.device("cpu"),
            )


class TestGrid3DPOMDPValidation:
    """Test vision_range validation for Grid3D POMDP."""

    @pytest.fixture
    def grid3d_config_pack(self, config_pack_factory):
        """Create Grid3D config pack."""
        config_dir = config_pack_factory(name="grid3d")

        def mutate_stratum(data: dict) -> None:
            grid = data["stratum"]["substrate"]["grid"]
            grid["topology"] = "cubic"
            grid["width"] = 8
            grid["height"] = 8
            grid["depth"] = 8

        mutate_stratum_yaml(config_dir, mutate_stratum)
        return config_dir

    def test_grid3d_pomdp_accepts_window_5(self, grid3d_config_pack):
        """Grid3D POMDP should accept window 5 (vision_range normalized to 0.5 for 8³)."""
        mutate_curriculum_yaml(
            grid3d_config_pack,
            lambda c: c["curriculum"].update({"active_vision": "partial", "vision_range": 0.5}),
        )

        env = make_vectorized_env_from_pack(
            grid3d_config_pack,
            level_name="L0_test",
            num_agents=1,
            device=torch.device("cpu"),
        )
        assert env.partial_observability is True
        assert env.local_window_size == 5
        assert env.substrate.position_dim == 3

    def test_grid3d_pomdp_rejects_window_7(self, grid3d_config_pack):
        """Grid3D POMDP should reject window 7 (vision_range=0.75 on 8³ -> radius 3, window 7)."""
        mutate_curriculum_yaml(
            grid3d_config_pack,
            lambda c: c["curriculum"].update({"active_vision": "partial", "vision_range": 0.75}),
        )

        with pytest.raises(ValueError, match="Grid3D POMDP.*requires 343 cells"):
            make_vectorized_env_from_pack(
                grid3d_config_pack,
                level_name="L0_test",
                num_agents=1,
                device=torch.device("cpu"),
            )
