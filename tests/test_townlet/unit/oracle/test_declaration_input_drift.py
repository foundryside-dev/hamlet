"""Preserve Cut A/B history and pin the current static-access input inventory."""

import hashlib
import json
from pathlib import Path

import pytest

from townlet.oracle.harness import ORACLE_PACK_ROOT, _pack_files, pack_drift
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
                "differing": [
                    "effects.yaml",
                    "environment.yaml",
                    "stratum.yaml",
                    "vfs_profiles.yaml",
                ],
            },
        ),
    ],
)
def test_cut_a_recorded_input_delta_is_preserved(pack: str, delta: dict[str, list[str]]) -> None:
    """B replaces the live transport; the banked parent proves A's old reading."""
    root = Path(__file__).parents[4]
    parent = json.loads((root / "docs/product/evidence/declaration-cut-b/before-inputs.json").read_text())
    assert parent["source_commit"] == "599cad15706ac8824c3f8e38276da6440c4816a3"
    prefix = f"{pack}/"
    old_live = {name.removeprefix(prefix): digest for name, digest in parent["files"].items() if name.startswith(prefix)}
    frozen = {name: hashlib.sha256(data).hexdigest() for name, data in _pack_files(root / ORACLE_PACK_ROOT / pack).items()}
    actual = {}
    for kind, names in (
        ("only_in_frozen", sorted(frozen.keys() - old_live.keys())),
        ("only_in_live", sorted(old_live.keys() - frozen.keys())),
        (
            "differing",
            sorted(name for name in frozen.keys() & old_live.keys() if frozen[name] != old_live[name]),
        ),
    ):
        if names:
            actual[kind] = names
    assert actual == delta


def test_cut_b_historical_input_inventory_is_preserved() -> None:
    """Static access supersedes the binding without rewriting Cut B's evidence."""
    root = Path(__file__).parents[4]
    historical = json.loads((root / "docs/oracle/declaration-cut-b-inputs.json").read_text())
    before_access = json.loads((root / "docs/product/evidence/static-epistemic-access/before/before-inputs.json").read_text())
    expected_packs = {cell.params.pack for cell in default_cells()}
    assert historical["register_ref"] == "DIV-014"
    assert historical["baseline_source"] == "599cad15706ac8824c3f8e38276da6440c4816a3"
    assert historical["canonical_source_commit"] == "8060ef19b820ddada047570825865b69e6b38b3b"
    assert before_access["source_commit"] == "0fdb16eadfa7e4096a238959ba113e92e90fb5af"
    assert historical["packs"].keys() == expected_packs
    for pack, record in historical["packs"].items():
        prefix = f"{pack}/"
        parent_files = {
            name.removeprefix(prefix): data["sha256"] for name, data in before_access["files"].items() if name.startswith(prefix)
        }
        frozen = {name: hashlib.sha256(data).hexdigest() for name, data in _pack_files(root / ORACLE_PACK_ROOT / pack).items()}
        assert parent_files == record["live_files"], f"{pack}: historical Cut B live bytes were rewritten"
        assert frozen == record["frozen_files"], f"{pack}: frozen oracle input changed"
        actual_delta = {}
        for kind, names in (
            ("only_in_frozen", sorted(frozen.keys() - parent_files.keys())),
            ("only_in_live", sorted(parent_files.keys() - frozen.keys())),
            (
                "differing",
                sorted(name for name in frozen.keys() & parent_files.keys() if frozen[name] != parent_files[name]),
            ),
        ):
            if names:
                actual_delta[kind] = names
        assert actual_delta == record["delta"]


def test_static_access_input_binding_matches_complete_pinned_bytes() -> None:
    """The complete current inventory catches edits outside measured DIV-015."""
    root = Path(__file__).parents[4]
    inventory = json.loads((root / "docs/product/evidence/static-epistemic-access/frozen-live-inputs.json").read_text())
    expected_packs = {cell.params.pack for cell in default_cells()}
    assert inventory["register_ref"] == "DIV-015"
    assert inventory["frozen_tag"] == "oracle-2026-08-17"
    assert inventory["source_commit"] == "9137484965b05c26ceed1740ee9aab39a364a61c"
    records = {record["pack"]: record for record in inventory["packs"]}
    assert len(records) == len(inventory["packs"]) == 6
    assert records.keys() == expected_packs
    for pack, record in records.items():
        live = {name: hashlib.sha256(data).hexdigest() for name, data in _pack_files(root / pack).items()}
        frozen = {name: hashlib.sha256(data).hexdigest() for name, data in _pack_files(root / ORACLE_PACK_ROOT / pack).items()}
        assert live == record["live_files"], f"{pack}: live bytes moved outside the registered inventory"
        assert frozen == record["frozen_files"], f"{pack}: frozen oracle input changed"
        assert pack_drift(root / ORACLE_PACK_ROOT, root, pack) == record["delta"]
        readers = [cell for cell in default_cells() if cell.params.pack == pack]
        assert all(cell.pack_divergence == "DIV-015" for cell in readers)
        assert all(entry.register_ref != "DIV-013" for cell in readers for entry in cell.hash_divergences)
        assert all(cell.stream_divergence is not None and cell.stream_divergence.register_ref == "DIV-008" for cell in readers)
        assert all(cell.stream_divergence.declared == {"obs"} for cell in readers)
