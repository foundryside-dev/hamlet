"""The observer's presentation surface: declared bounds/cascades forwarded, presentation opt-in.

`build_meter_metadata` derives everything the frontend needs to render HONESTLY from the compiled
artifact — bounds, lethality, cascade edges — with no meter singled out by name.

Presentation is one vocabulary (PDR-0025, findings_compiler F7): the compiler discovers the
`presentation` declaration by content, resolves its meter and affordance references in stage 5,
and carries the parsed config on the artifact as `CompiledUniverse.presentation`. The observer
reads the artifact; nothing re-opens a fixed filename. Absent → None (the honest default).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import msgpack  # type: ignore[import-untyped]
import pytest

from townlet.demo.presentation import build_meter_metadata, presentation_payload
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError

LEVEL = "L0_test"

# The declaration lives in `display.yaml`, not `presentation.yaml`: filenames are transport.
DECLARED = """
version: "1.0"
meters:
  money:
    label: Money
    format: {kind: currency, symbol: "$", decimals: 0}
    color: "#fbbf24"
affordances:
  EAT: {label: Eat, icon: "E"}
"""


@pytest.fixture(scope="module")
def universe(test_config_pack_path: Path):
    return UniverseCompiler().compile(test_config_pack_path, primary_level=LEVEL)


def _pack_with_presentation(src: Path, dst: Path, text: str) -> Path:
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".compiled"))
    (dst / "display.yaml").write_text(text)
    return dst


def _compile(pack: Path) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


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


def test_absent_presentation_is_the_honest_default(universe) -> None:
    assert universe.presentation is None
    assert presentation_payload(universe.presentation) is None


def test_declared_presentation_reaches_the_artifact_and_the_payload(test_config_pack_path: Path, tmp_path: Path) -> None:
    """F7: the `pres` scratch pack — presentation declared in `display.yaml` — is read at runtime
    through the artifact, not through a filename."""
    compiled = _compile(_pack_with_presentation(test_config_pack_path, tmp_path / "pack", DECLARED))

    assert compiled.presentation is not None
    assert presentation_payload(compiled.presentation) == {
        "meters": {"money": {"label": "Money", "format": {"kind": "currency", "symbol": "$", "decimals": 0}, "color": "#fbbf24"}},
        "affordances": {"EAT": {"label": "Eat", "icon": "E"}},
    }


def test_presentation_survives_the_artifact_round_trip(test_config_pack_path: Path, tmp_path: Path) -> None:
    compiled = _compile(_pack_with_presentation(test_config_pack_path, tmp_path / "pack", DECLARED))

    payload = msgpack.packb(compiled.to_dict(), use_bin_type=True)
    restored = CompiledUniverse.from_dict(msgpack.unpackb(payload, raw=False, strict_map_key=False))

    assert restored.presentation == compiled.presentation


def _single_refusal(pack: Path) -> CompilationError:
    with pytest.raises(CompilationError) as caught:
        _compile(pack)
    assert len(caught.value.issues) == 1, str(caught.value)
    return caught.value


def test_presentation_for_an_undeclared_meter_refuses_at_compile(test_config_pack_path: Path, tmp_path: Path) -> None:
    pack = _pack_with_presentation(
        test_config_pack_path,
        tmp_path / "pack",
        """
version: "1.0"
meters:
  NO_SUCH_METER:
    label: Gold
    format: {kind: plain, decimals: 1}
    color: "#fbbf24"
affordances: {}
""",
    )
    error = _single_refusal(pack)
    issue = error.issues[0]
    assert error.stage == "Stage 5: Resolve references"
    assert issue.code == ErrorCode.UAC_RES_PRESENTATION
    assert "NO_SUCH_METER" in issue.message
    # Located inside the offending entry (the source map marks a block-mapping value at its
    # first line), in the file the declaration was actually written in.
    assert issue.location is not None
    assert issue.location.startswith(f"{pack / 'display.yaml'}:")
    assert int(issue.location.rsplit(":", 1)[1]) in range(4, 8)


def test_presentation_for_an_undeclared_affordance_refuses_at_compile(test_config_pack_path: Path, tmp_path: Path) -> None:
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
    issue = _single_refusal(pack).issues[0]
    assert issue.code == ErrorCode.UAC_RES_PRESENTATION
    assert "DANCE" in issue.message
    assert issue.location == f"{pack / 'display.yaml'}:5"


def test_malformed_presentation_refuses_at_discovery(test_config_pack_path: Path, tmp_path: Path) -> None:
    """Without all three signature keys the document is not a presentation declaration at all,
    so it is refused as unknown content at its own location rather than silently ignored."""
    pack = _pack_with_presentation(test_config_pack_path, tmp_path / "pack", "version: '1.0'\nmeters: {}\n")
    with pytest.raises(CompilationError) as caught:
        _compile(pack)
    issue = caught.value.issues[0]
    assert issue.code == ErrorCode.DECLARATION_UNKNOWN
    assert issue.location == f"{pack / 'display.yaml'}:1"


def test_presentation_enters_no_semantic_hash(universe, test_config_pack_path: Path, tmp_path: Path) -> None:
    """The compiler carries presentation, but it is observer-only: compiling with and without the
    declaration yields identical behavioural provenance."""
    with_declaration = _compile(_pack_with_presentation(test_config_pack_path, tmp_path / "pack", DECLARED))
    assert with_declaration.presentation is not None
    for field in ("experiment_hash", "stratum_hash", "environment_hash", "actions_hash", "items_hash", "variables_hash", "brain_hash"):
        assert getattr(with_declaration, field) == getattr(universe, field), field

    declared_level = with_declaration.get_level(with_declaration.metadata.primary_level)
    universe_level = universe.get_level(universe.metadata.primary_level)
    for field in (
        "bars_hash",
        "affordances_hash",
        "vfs_hash",
        "observation_schema_hash",
        "action_schema_hash",
        "transition_graph_hash",
        "drive_hash",
    ):
        assert getattr(declared_level, field) == getattr(universe_level, field), field
