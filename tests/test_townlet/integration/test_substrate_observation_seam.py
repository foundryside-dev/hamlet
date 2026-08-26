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
