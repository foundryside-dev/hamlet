"""Cut A's input-only registration must describe the exact byte deltas."""

from pathlib import Path

import pytest

from townlet.oracle.harness import ORACLE_PACK_ROOT, pack_drift
from townlet.oracle.matrix import default_cells


@pytest.mark.parametrize(
    ("pack", "delta"),
    [
        (
            "configs/default_curriculum",
            {
                "differing": [
                    "environment.yaml",
                    "levels/L2_partial_observability/curriculum.yaml",
                    "levels/L3_temporal_mechanics/curriculum.yaml",
                    "stratum.yaml",
                    "vfs_profiles.yaml",
                ]
            },
        ),
        (
            "configs/test/items_smoke",
            {
                "only_in_frozen": [
                    "affordances.yaml",
                    "bars.yaml",
                    "drive_as_code.yaml",
                    "levels/L0_smoke/brain.yaml",
                    "substrate.yaml",
                    "training.yaml",
                ],
                "differing": ["effects.yaml", "environment.yaml", "stratum.yaml", "vfs_profiles.yaml"],
            },
        ),
    ],
)
def test_cut_a_input_binding_is_narrow(pack: str, delta: dict[str, list[str]]) -> None:
    root = Path(__file__).parents[4]
    assert pack_drift(root / ORACLE_PACK_ROOT, root, pack) == delta
    for cell in default_cells():
        if cell.params.pack == pack:
            assert cell.pack_divergence == "DIV-013"
            assert all(entry.register_ref != "DIV-013" for entry in cell.hash_divergences)
            assert cell.stream_divergence is not None
            assert cell.stream_divergence.register_ref != "DIV-013"
