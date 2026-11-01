"""Authored training sidecars must survive lowering without losing validation or origins."""

from __future__ import annotations

from copy import deepcopy
from math import copysign
from pathlib import Path
from shutil import copyfile
from typing import Any

import pytest
import yaml

from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.declarations import DeclarationStore
from townlet.universe.errors import CompilationError

LEVEL = "L0_0_minimal"
SIDECARS = {"recording": {"enabled": True}, "run_metadata": {"output_subdir": "authored-sidecars"}}


@pytest.fixture
def authored_pack(tmp_path: Path) -> Path:
    """Copy YAML DATA only, retaining one complete authored level."""
    source = Path(__file__).resolve().parents[4] / "configs/test/bac_remediation/feedforward"
    pack = tmp_path / "pack"
    for document in source.rglob("*"):
        if not document.is_file() or document.suffix not in {".yaml", ".yml"}:
            continue
        relative = document.relative_to(source)
        if relative.parts[0] == "levels" and relative.parts[1] != LEVEL:
            continue
        destination = pack / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        copyfile(document, destination)
    return pack


def _write_training(pack: Path, *, top: dict[str, Any], nested: dict[str, Any]) -> tuple[Path, str]:
    path = pack / "levels" / LEVEL / "training.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    for sidecar in SIDECARS:
        document.pop(sidecar, None)
        document["training"].pop(sidecar, None)
    document.update(deepcopy(top))
    document["training"].update(deepcopy(nested))
    text = yaml.safe_dump(document, sort_keys=False)
    path.write_text(text, encoding="utf-8")
    return path, text


def _origin(path: Path, text: str, key: str, indent: int) -> str:
    prefix = f"{' ' * indent}{key}:"
    matches = [number for number, line in enumerate(text.splitlines(), 1) if line.startswith(prefix)]
    assert len(matches) == 1, f"Expected one authored {prefix!r}, found {matches}"
    return f"{path}:{matches[0]}"


def _compile(pack: Path) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _assert_sidecars(compiled: CompiledUniverse, sidecars: tuple[str, ...]) -> None:
    training = compiled.all_levels[LEVEL].training
    if "recording" in sidecars:
        assert training.recording is not None
        assert training.recording.enabled is True
    if "run_metadata" in sidecars:
        assert training.run_metadata is not None
        assert training.run_metadata.output_subdir == "authored-sidecars"


@pytest.mark.parametrize("sidecars", [("recording",), ("run_metadata",), ("recording", "run_metadata")])
@pytest.mark.parametrize("placement", ["top", "nested"])
def test_nested_sidecars_survive(authored_pack: Path, tmp_path: Path, sidecars: tuple[str, ...], placement: str) -> None:
    """Dropping either accepted placement loses its DTO values and training identity."""
    _write_training(authored_pack, top={}, nested={})
    baseline = _compile(authored_pack)
    values = {name: SIDECARS[name] for name in sidecars}
    _write_training(authored_pack, top=values if placement == "top" else {}, nested=values if placement == "nested" else {})
    compiled = _compile(authored_pack)
    _assert_sidecars(compiled, sidecars)
    assert compiled.all_levels[LEVEL].training_hash != baseline.all_levels[LEVEL].training_hash

    # Both accepted placements lower to the same consumer DTO and semantic identity.
    _write_training(authored_pack, top=values if placement == "nested" else {}, nested=values if placement == "top" else {})
    relocated = _compile(authored_pack)
    _assert_sidecars(relocated, sidecars)
    assert relocated.all_levels[LEVEL].training == compiled.all_levels[LEVEL].training
    assert relocated.all_levels[LEVEL].training_hash == compiled.all_levels[LEVEL].training_hash

    dto_restored = CompiledUniverse.from_dict(compiled.to_dict())
    _assert_sidecars(dto_restored, sidecars)
    assert dto_restored.all_levels[LEVEL].training_hash == compiled.all_levels[LEVEL].training_hash
    cache = tmp_path / "sidecars.msgpack"
    compiled.save_to_cache(cache)
    cache_restored = CompiledUniverse.load_from_cache(cache)
    _assert_sidecars(cache_restored, sidecars)
    assert cache_restored.all_levels[LEVEL].training_hash == compiled.all_levels[LEVEL].training_hash


@pytest.mark.parametrize("top_sidecar", ["recording", "run_metadata"])
def test_mixed_sidecar_placements_are_additive(authored_pack: Path, top_sidecar: str) -> None:
    """Lowering one sidecar must not overwrite a different nested sidecar."""
    nested_sidecar = "run_metadata" if top_sidecar == "recording" else "recording"
    _write_training(authored_pack, top=SIDECARS, nested={})
    top_only = _compile(authored_pack)
    _write_training(authored_pack, top={top_sidecar: SIDECARS[top_sidecar]}, nested={nested_sidecar: SIDECARS[nested_sidecar]})
    mixed = _compile(authored_pack)
    _assert_sidecars(mixed, ("recording", "run_metadata"))
    assert mixed.all_levels[LEVEL].training == top_only.all_levels[LEVEL].training
    assert mixed.all_levels[LEVEL].training_hash == top_only.all_levels[LEVEL].training_hash


@pytest.mark.parametrize("sidecar", ["recording", "run_metadata"])
@pytest.mark.parametrize("malformed_placement", ["top", "nested"])
def test_malformed_shadowed_sidecar_refuses(authored_pack: Path, sidecar: str, malformed_placement: str) -> None:
    """Validating only the chosen duplicate would silently discard an invalid mapping."""
    valid = deepcopy(SIDECARS[sidecar])
    invalid = {**valid, "invalid_option": True}
    path, text = _write_training(
        authored_pack,
        top={sidecar: invalid if malformed_placement == "top" else valid},
        nested={sidecar: invalid if malformed_placement == "nested" else valid},
    )
    invalid_origin = _origin(path, text, "invalid_option", 2 if malformed_placement == "top" else 4)
    with pytest.raises(CompilationError) as caught:
        _compile(authored_pack)
    diagnostic = str(caught.value)
    assert "invalid_option" in diagnostic
    assert invalid_origin in diagnostic


@pytest.mark.parametrize("sidecar,field,other", [("recording", "enabled", False), ("run_metadata", "output_subdir", "different")])
def test_conflict_names_both_origins(authored_pack: Path, sidecar: str, field: str, other: Any) -> None:
    """A differing duplicate must refuse instead of selecting the top or nested value."""
    path, text = _write_training(
        authored_pack,
        top={sidecar: SIDECARS[sidecar]},
        nested={sidecar: {field: other}},
    )
    top_origin = _origin(path, text, field, 2)
    nested_origin = _origin(path, text, field, 4)
    with pytest.raises(CompilationError) as caught:
        _compile(authored_pack)
    diagnostic = str(caught.value)
    assert sidecar in diagnostic
    assert top_origin in diagnostic
    assert nested_origin in diagnostic


@pytest.mark.parametrize("sidecar,field", [("recording", "enabled"), ("run_metadata", "output_subdir")])
def test_equal_duplicates_preserve_both_origins(authored_pack: Path, sidecar: str, field: str) -> None:
    """Accepting equal duplicates must retain both authored mappings and leaf locations."""
    path, text = _write_training(authored_pack, top={sidecar: SIDECARS[sidecar]}, nested={sidecar: SIDECARS[sidecar]})
    store = DeclarationStore.discover(authored_pack)
    canonical = f"levels/{LEVEL}/training:{sidecar}"
    authored_nested = f"levels/{LEVEL}/training:training.{sidecar}"
    assert store.source_map.lookup(canonical) == _origin(path, text, sidecar, 0)
    assert store.source_map.lookup(authored_nested) == _origin(path, text, sidecar, 2)
    assert store.source_map.lookup(f"{canonical}.{field}") == _origin(path, text, field, 2)
    assert store.source_map.lookup(f"{authored_nested}.{field}") == _origin(path, text, field, 4)
    _assert_sidecars(_compile(authored_pack), (sidecar,))


@pytest.mark.parametrize("present_placement", ["top", "nested"])
def test_missing_criteria_key_is_not_equal_to_explicit_null(authored_pack: Path, present_placement: str) -> None:
    """Conflating a missing key with None discards a working authored training identity."""
    present = {"enabled": True, "criteria": {"leaf": None}}
    absent = {"enabled": True, "criteria": {}}
    _write_training(authored_pack, top={"recording": present}, nested={})
    with_leaf = _compile(authored_pack)
    _write_training(authored_pack, top={}, nested={"recording": absent})
    without_leaf = _compile(authored_pack)
    assert with_leaf.all_levels[LEVEL].training.recording.criteria == {"leaf": None}
    assert without_leaf.all_levels[LEVEL].training.recording.criteria == {}
    assert with_leaf.all_levels[LEVEL].training_hash != without_leaf.all_levels[LEVEL].training_hash

    path, text = _write_training(
        authored_pack,
        top={"recording": present if present_placement == "top" else absent},
        nested={"recording": present if present_placement == "nested" else absent},
    )
    present_origin = _origin(path, text, "leaf", 4 if present_placement == "top" else 6)
    absent_origin = _origin(path, text, "criteria", 4 if present_placement == "top" else 2)
    with pytest.raises(CompilationError) as caught:
        _compile(authored_pack)
    diagnostic = str(caught.value)
    assert "recording.criteria.leaf" in diagnostic
    assert present_origin in diagnostic
    assert absent_origin in diagnostic


def test_mixed_nested_criteria_keys_refuse_with_located_diagnostic(authored_pack: Path) -> None:
    """Mixed keys already refuse downstream; lowering must issue a located diagnostic."""
    path, text = _write_training(
        authored_pack,
        top={"recording": {"enabled": True, "criteria": {"deep": {1: "top", "leaf": "same"}}}},
        nested={"recording": {"enabled": True, "criteria": {"deep": {1: "nested", "leaf": "same"}}}},
    )
    top_origin = _origin(path, text, "1", 6)
    nested_origin = _origin(path, text, "1", 8)
    # Exercise declaration lowering only: this does not expand the downstream
    # recording provider's existing restriction to string dictionary keys.
    with pytest.raises(CompilationError) as caught:
        DeclarationStore.discover(authored_pack)
    diagnostic = str(caught.value)
    assert "recording.criteria.deep.1" in diagnostic
    assert top_origin in diagnostic
    assert nested_origin in diagnostic


def _assert_exact_authored_value(actual: Any, expected: Any) -> None:
    assert type(actual) is type(expected)
    if isinstance(expected, list):
        assert len(actual) == len(expected)
        for actual_item, expected_item in zip(actual, expected, strict=True):
            _assert_exact_authored_value(actual_item, expected_item)
    else:
        assert actual == expected
        if isinstance(expected, float):
            assert copysign(1.0, actual) == copysign(1.0, expected)


@pytest.mark.parametrize(
    "top_value,nested_value",
    [(True, 1), (1, 1.0), ([[True]], [[1]]), (-0.0, 0.0)],
    ids=["bool-int", "int-float", "nested-list-bool-int", "signed-zero"],
)
def test_criteria_typed_values_with_distinct_training_identity_conflict(authored_pack: Path, top_value: Any, nested_value: Any) -> None:
    """Python equality must not silently select between distinct authored identities."""
    top = {"enabled": True, "criteria": {"leaf": top_value}}
    nested = {"enabled": True, "criteria": {"leaf": nested_value}}
    _write_training(authored_pack, top={"recording": top}, nested={})
    top_only = _compile(authored_pack)
    _write_training(authored_pack, top={}, nested={"recording": nested})
    nested_only = _compile(authored_pack)
    _assert_exact_authored_value(top_only.all_levels[LEVEL].training.recording.criteria["leaf"], top_value)
    _assert_exact_authored_value(nested_only.all_levels[LEVEL].training.recording.criteria["leaf"], nested_value)
    assert top_only.all_levels[LEVEL].training_hash != nested_only.all_levels[LEVEL].training_hash

    path, text = _write_training(authored_pack, top={"recording": top}, nested={"recording": nested})
    top_origin = _origin(path, text, "leaf", 4)
    nested_origin = _origin(path, text, "leaf", 6)
    with pytest.raises(CompilationError) as caught:
        _compile(authored_pack)
    diagnostic = str(caught.value)
    assert "recording.criteria.leaf" in diagnostic
    assert top_origin in diagnostic
    assert nested_origin in diagnostic
