"""The substrate→observation-dim seam, end to end (WS-7 first knockdown).

These are the DIV-003 configurations (docs/oracle/known-divergences.md): three
declared, schema-valid packs that used to compile and then crash at
env.reset() because the compiler derived observation dims from substrate.type
strings instead of asking the substrate instance. Post-cut they must compile
AND run — the assessment's precise gap was that no test drove a config through
compiler + env for any non-default substrate value.

The packs under configs/differential/ are the same fixtures the differential
harness's DIV-003 matrix cells run; keep them frozen (see
test_matrix.py::test_div003_fixture_packs_vary_only_the_declared_axis).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from tests.test_townlet.utils.builders import make_vectorized_env_from_pack

_REPO_ROOT = Path(__file__).resolve().parents[3]

_DIV003_PACKS = (
    ("div003_scaled", "L1_full_observability"),
    ("div003_cubic_partial", "L2_partial_observability"),
    ("div003_rect", "L1_full_observability"),
)


@pytest.mark.parametrize(("pack_name", "level"), _DIV003_PACKS)
def test_div003_config_compiles_resets_and_steps(pack_name: str, level: str) -> None:
    """Each registered crashing config now runs, and every step's observation
    width equals the compiled spec — the invariant whose violation was the
    crash."""
    env = make_vectorized_env_from_pack(
        _REPO_ROOT / "configs" / "differential" / pack_name,
        level_name=level,
        num_agents=4,
        device=torch.device("cpu"),
    )
    obs = env.reset()
    assert obs.shape == (4, env.observation_spec.total_dims)
    for _ in range(5):
        actions = torch.randint(0, env.action_dim, (env.num_agents,))
        obs, rewards, dones, _ = env.step(actions)
        assert obs.shape == (4, env.observation_spec.total_dims)


def test_scaled_position_field_width_comes_from_the_substrate() -> None:
    """The 'scaled' pack's obs_position is 4 wide (x, y, width, height) because
    Grid2D's scaled encoder emits 4 features — the compiler must have asked."""
    env = make_vectorized_env_from_pack(
        _REPO_ROOT / "configs" / "differential" / "div003_scaled",
        level_name="L1_full_observability",
        num_agents=4,
        device=torch.device("cpu"),
    )
    field = env.observation_spec.get_field_by_name("obs_position")
    assert field.dims == 4


def test_cubic_partial_window_is_a_cube() -> None:
    """The cubic pack's obs_local_window is (2r+1)^3 = 125, matching
    Grid3D.encode_partial_observation's actual output."""
    env = make_vectorized_env_from_pack(
        _REPO_ROOT / "configs" / "differential" / "div003_cubic_partial",
        level_name="L2_partial_observability",
        num_agents=4,
        device=torch.device("cpu"),
    )
    field = env.observation_spec.get_field_by_name("obs_local_window")
    assert field.dims == 125


def test_rect_boundary_masks_use_each_axis_own_extent() -> None:
    """On a non-square grid the y axis must be masked with HEIGHT and the x
    axis with WIDTH. The old single grid_size masked both axes with width,
    so on 8×6 an agent on the bottom row (y=5) would not have had its
    downward moves masked (5 != 8-1). Expectations are derived from the
    env's own movement deltas so the test holds for any action vocabulary.
    (Written green against the fixed builder; verified by the knockdown's
    mutation battery — reintroducing the square assumption must fail here.)"""
    env = make_vectorized_env_from_pack(
        _REPO_ROOT / "configs" / "differential" / "div003_rect",
        level_name="L1_full_observability",
        num_agents=3,
        device=torch.device("cpu"),
    )
    env.reset()
    # (0,0) top-left, (7,5) bottom-right corner of the 8×6 grid, (3,2) interior
    env.positions = torch.tensor([[0, 0], [7, 5], [3, 2]], dtype=env.positions.dtype, device=env.device)
    masks = env.get_action_masks()
    deltas = env._movement_deltas

    moves_up = deltas[:, 1] < 0
    moves_down = deltas[:, 1] > 0
    moves_left = deltas[:, 0] < 0
    moves_right = deltas[:, 0] > 0

    assert not masks[0, moves_up].any(), "top row: upward moves must be masked"
    assert not masks[0, moves_left].any(), "left column: leftward moves must be masked"
    assert not masks[1, moves_down].any(), "bottom row (y == height-1): downward moves must be masked"
    assert not masks[1, moves_right].any(), "right column (x == width-1): rightward moves must be masked"
    assert masks[2, moves_up | moves_down | moves_left | moves_right].all(), "interior agent: all movement allowed"


def test_grid3d_type_literal_is_gone() -> None:
    """`type: grid3d` never had a factory branch; the working 3-D path is
    `type: grid` + `topology: cubic`. Zero-BC disposition: the dead literal
    fails schema validation loudly instead of compiling toward a factory
    crash (assessment §3; the fourth crash PDR-0035 carries)."""
    from pydantic import ValidationError

    from townlet.config.stratum_config import SubstrateConfig

    with pytest.raises(ValidationError):
        SubstrateConfig.model_validate(
            {
                "type": "grid3d",
                "grid": {
                    "topology": "cubic",
                    "width": 8,
                    "height": 8,
                    "depth": 3,
                    "boundary": "clamp",
                    "distance_metric": "manhattan",
                    "observation_encoding": "relative",
                    "diagonals": True,
                },
            }
        )
