"""The observer's presentation surface: declared bounds/cascades forwarded, presentation opt-in.

`build_meter_metadata` derives everything the frontend needs to render HONESTLY from the compiled
artifact — bounds, lethality, cascade edges — with no meter singled out by name.
`load_presentation` reads an optional pack-level `presentation.yaml`; absent → None (the honest
default), present → validated against the compiled universe's meter and affordance names so a
typo is a loud error rather than a silently ignored declaration.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from townlet.demo.presentation import (
    PresentationError,
    build_meter_metadata,
    load_presentation,
    presentation_payload,
)
from townlet.universe.compiler import UniverseCompiler


@pytest.fixture(scope="module")
def universe(test_config_pack_path: Path):
    return UniverseCompiler().compile(test_config_pack_path, primary_level="L0_test")


def test_meter_metadata_is_in_compiled_order_and_carries_declared_bounds(universe) -> None:
    rows = build_meter_metadata(universe)
    assert [r["index"] for r in rows] == list(range(len(rows)))
    assert [r["name"] for r in rows] == list(universe.metadata.meter_names)
    money = next(r for r in rows if r["name"] == "money")
    assert money["bounds"] == {"min": 0.0, "max": 999999.0}
    assert money["lethal_min"] is False and money["lethal_max"] is False
    energy = next(r for r in rows if r["name"] == "energy")
    assert energy["bounds"] == {"min": 0.0, "max": 1.0}
    assert energy["lethal_min"] is True


def test_meter_metadata_carries_declared_cascade_edges_both_ways(universe) -> None:
    rows = {r["name"]: r for r in build_meter_metadata(universe)}
    # bars.yaml of L0_test declares satiation→health, satiation→energy, mood→energy,
    # hygiene→mood, hygiene→social — in that order
    assert rows["satiation"]["cascades_to"] == ["health", "energy"]
    assert rows["mood"]["cascades_to"] == ["energy"]
    assert rows["hygiene"]["cascades_to"] == ["mood", "social"]
    assert rows["energy"]["cascades_from"] == ["satiation", "mood"]
    assert rows["mood"]["cascades_from"] == ["hygiene"]
    assert rows["money"]["cascades_to"] == [] and rows["money"]["cascades_from"] == []
    assert rows["hygiene"]["cascades_from"] == []


def test_meter_metadata_rows_have_exactly_the_contract_keys(universe) -> None:
    for row in build_meter_metadata(universe):
        assert set(row) == {"name", "index", "bounds", "lethal_min", "lethal_max", "cascades_to", "cascades_from"}


def test_absent_presentation_file_is_the_honest_default(universe, tmp_path: Path) -> None:
    assert load_presentation(tmp_path, universe) is None
    assert presentation_payload(None) is None


def _pack_with_presentation(src: Path, dst: Path, text: str) -> Path:
    shutil.copytree(src, dst)
    (dst / "presentation.yaml").write_text(text)
    return dst


def test_declared_presentation_reaches_the_payload(universe, test_config_pack_path: Path, tmp_path: Path) -> None:
    pack = _pack_with_presentation(
        test_config_pack_path,
        tmp_path / "pack",
        """
version: "1.0"
meters:
  money:
    label: Money
    format: {kind: currency, symbol: "$", decimals: 0}
    color: "#fbbf24"
affordances:
  EAT: {label: Eat, icon: "E"}
""",
    )
    cfg = load_presentation(pack, universe)
    assert cfg is not None
    payload = presentation_payload(cfg)
    assert payload == {
        "meters": {"money": {"label": "Money", "format": {"kind": "currency", "symbol": "$", "decimals": 0}, "color": "#fbbf24"}},
        "affordances": {"EAT": {"label": "Eat", "icon": "E"}},
    }


def test_presentation_for_an_undeclared_meter_is_loud(universe, test_config_pack_path: Path, tmp_path: Path) -> None:
    pack = _pack_with_presentation(
        test_config_pack_path,
        tmp_path / "pack",
        """
version: "1.0"
meters:
  gold:
    label: Gold
    format: {kind: plain, decimals: 1}
    color: "#fbbf24"
affordances: {}
""",
    )
    with pytest.raises(PresentationError, match="gold"):
        load_presentation(pack, universe)


def test_presentation_for_an_undeclared_affordance_is_loud(universe, test_config_pack_path: Path, tmp_path: Path) -> None:
    pack = _pack_with_presentation(
        test_config_pack_path,
        tmp_path / "pack",
        """
version: "1.0"
meters: {}
affordances:
  DANCE: {label: Dance, icon: "D"}
""",
    )
    with pytest.raises(PresentationError, match="DANCE"):
        load_presentation(pack, universe)


def test_malformed_presentation_is_loud(universe, test_config_pack_path: Path, tmp_path: Path) -> None:
    pack = _pack_with_presentation(test_config_pack_path, tmp_path / "pack", "version: '1.0'\nmeters: {}\n")
    with pytest.raises(PresentationError, match="affordances"):
        load_presentation(pack, universe)


def test_the_compiler_never_reads_presentation(universe, test_config_pack_path: Path, tmp_path: Path) -> None:
    """Presentation is observer-only: compiling with or without the file yields identical
    behavioural provenance. (The raw pack cache key may differ; no compiled hash may.)"""
    pack = _pack_with_presentation(
        test_config_pack_path,
        tmp_path / "pack",
        'version: "1.0"\nmeters: {}\naffordances:\n  EAT: {label: Eat, icon: "E"}\n',
    )
    with_file = UniverseCompiler().compile(pack, primary_level="L0_test")
    assert with_file.environment_hash == universe.environment_hash

    with_file_level = with_file.get_level(with_file.metadata.primary_level)
    universe_level = universe.get_level(universe.metadata.primary_level)
    for field in (
        "bars_hash",
        "affordances_hash",
        "vfs_hash",
        "observation_schema_hash",
        "action_schema_hash",
        "transition_graph_hash",
    ):
        assert getattr(with_file_level, field) == getattr(universe_level, field), field
