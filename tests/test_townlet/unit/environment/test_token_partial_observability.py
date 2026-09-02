"""Partial observability filters tokens without allocating raster windows."""

import torch

from tests.test_townlet.helpers.config_builder import mutate_curriculum_yaml, mutate_stratum_yaml
from tests.test_townlet.utils.builders import make_vectorized_env_from_pack


def test_gridnd_4d_partial_observability_is_supported(config_pack_factory) -> None:
    config_dir = config_pack_factory(name="gridnd_4d_partial")

    def set_gridnd(data: dict) -> None:
        data["stratum"]["substrate"] = {
            "type": "gridnd",
            "gridnd": {
                "dimension_sizes": [5, 5, 5, 5],
                "boundary": "clamp",
                "distance_metric": "manhattan",
                "topology": "hypercube",
            },
        }

    mutate_stratum_yaml(config_dir, set_gridnd)
    mutate_curriculum_yaml(config_dir, lambda data: data["curriculum"].update({"active_vision": "partial", "vision_range": 0.5}))

    env = make_vectorized_env_from_pack(
        config_dir,
        level_name="L0_test",
        num_agents=1,
        device=torch.device("cpu"),
    )

    assert env.partial_observability is True
    assert env.substrate.position_dim == 4
    assert not hasattr(env, "local_window_size")
    assert not hasattr(env, "vision_radius")
