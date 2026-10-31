"""Compiler WP6 (C9, C10, C11): CLI diagnostics, inspect layout/freshness, cache identity.

C10 — every CLI refusal returns 1 with a ``[CODE] file:line - message`` diagnostic;
``main()`` never raises (that is the no-traceback contract).
C9 — ``inspect --format json`` exposes the token row layout, slot bindings and filler refs.
C11 — the cache fingerprint is path-aware and source-aware, independent of the cwd, and
``inspect`` says clearly when an artifact is stale against its source pack.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import msgpack  # type: ignore[import]
import pytest

from townlet.universe import __main__ as cli
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.declarations import DeclarationStore
from townlet.universe.raw_configs_v21 import RawConfigsV21

LEVEL = "L0_test"


def _pack(tmp_path: Path, name: str = "model_config") -> Path:
    dest = tmp_path / name
    shutil.copytree(Path("configs/test/model_config"), dest, ignore=shutil.ignore_patterns(".compiled"))
    return dest


def _refused(capsys: pytest.CaptureFixture[str], argv: list[str], code: str) -> str:
    assert cli.main(argv) == 1
    captured = capsys.readouterr()
    assert "Traceback" not in captured.out + captured.err
    assert f"[{code}] " in captured.err, captured.err
    return captured.err


def _count_lowerings(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    original = RawConfigsV21.from_declarations
    counter = {"calls": 0}

    def _wrapped(_cls: type[RawConfigsV21], store: DeclarationStore) -> RawConfigsV21:
        counter["calls"] += 1
        return original(store)

    monkeypatch.setattr(RawConfigsV21, "from_declarations", classmethod(_wrapped))
    return counter


# --------------------------------------------------------------------------- C10


def test_unknown_primary_level_is_a_coded_refusal(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pack = _pack(tmp_path)
    err = _refused(capsys, ["validate", str(pack), "--primary-level", "NOPE"], "PRIMARY_LEVEL_UNKNOWN")
    assert f"{pack / 'levels'}:1 - Primary level 'NOPE' not found" in err


def test_stray_file_in_levels_is_not_a_level(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pack = _pack(tmp_path)
    (pack / "levels" / "README.md").write_text("not a level\n")
    err = _refused(capsys, ["validate", str(pack), "--primary-level", "README.md"], "PRIMARY_LEVEL_UNKNOWN")
    assert f"Available: ['{LEVEL}']" in err


def test_missing_config_dir_is_a_coded_refusal(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _refused(capsys, ["compile", str(tmp_path / "absent"), "--primary-level", LEVEL], "CONFIG_PATH_INVALID")


def test_inspect_pack_dir_without_primary_level(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pack = _pack(tmp_path)
    _refused(capsys, ["inspect", str(pack)], "CLI_PRIMARY_LEVEL_REQUIRED")


def test_inspect_missing_artifact(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pack = _pack(tmp_path)
    _refused(capsys, ["inspect", str(pack), "--primary-level", LEVEL], "ARTIFACT_NOT_FOUND")


@pytest.mark.parametrize("corruption", ["older_schema", "not_msgpack", "experiment_dir_int", "payload_is_int"])
def test_inspect_unloadable_artifact(tmp_path: Path, capsys: pytest.CaptureFixture[str], corruption: str) -> None:
    pack = _pack(tmp_path)
    UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=True)
    artifact = pack / ".compiled" / f"universe-{LEVEL}.msgpack"
    if corruption == "older_schema":
        payload = msgpack.unpackb(artifact.read_bytes(), raw=False, strict_map_key=False)
        payload["compiled_schema_version"] = "0.0"
        artifact.write_bytes(msgpack.packb(payload, use_bin_type=True))
    elif corruption == "experiment_dir_int":
        payload = msgpack.unpackb(artifact.read_bytes(), raw=False, strict_map_key=False)
        payload["experiment_dir"] = 12345
        artifact.write_bytes(msgpack.packb(payload, use_bin_type=True))
    elif corruption == "payload_is_int":
        artifact.write_bytes(msgpack.packb(7))
    else:
        artifact.write_bytes(b"not msgpack")
    err = _refused(capsys, ["inspect", str(artifact)], "ARTIFACT_LOAD_REFUSED")
    assert f"{artifact}:1 - " in err


# --------------------------------------------------------------------------- C9


def test_inspect_json_exposes_row_layout_bindings_and_filler_refs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pack = _pack(tmp_path)
    compiled = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=True)
    spec = compiled.get_level(LEVEL).token_spec
    capsys.readouterr()

    assert cli.main(["inspect", str(pack), "--primary-level", LEVEL, "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    rows = payload["token_rows"]
    expected_bindings = [(t.type_name, b) for t in spec.types for b in t.slot_bindings]
    assert [(r["type_name"], r["slot_index"], r["start"], r["end"]) for r in rows] == list(spec.row_layout())
    assert [(r["fixed_start"], r["fixed_end"]) for r in rows] == [(row[2], row[3]) for row in spec.fixed_row_layout()]
    assert [(r["type_name"], r["filler_kind"], r["filler_ref"]) for r in rows] == [
        (type_name, b.filler_kind, b.filler_ref) for type_name, b in expected_bindings
    ]
    # Offsets tile the flat view exactly.
    assert rows[0]["start"] == 0
    assert all(a["end"] == b["start"] for a, b in zip(rows, rows[1:], strict=False))
    assert rows[-1]["end"] == payload["token_compact_total_dims"]
    assert rows[-1]["fixed_end"] == payload["token_fixed_boundary_total_dims"]
    # Per-type schema makes the offsets interpretable.
    types = {t["type_name"]: t for t in payload["token_types"]}
    assert set(types) == {t.type_name for t in spec.types}
    for t in spec.types:
        assert types[t.type_name]["payload_features"] == list(t.payload_features)
        assert types[t.type_name]["capacity"] == t.capacity


# --------------------------------------------------------------------------- C11


def test_inspect_reports_fresh_then_stale_after_pack_edit(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pack = _pack(tmp_path)
    UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=True)
    capsys.readouterr()

    assert cli.main(["inspect", str(pack), "--primary-level", LEVEL, "--format", "json"]) == 0
    fresh = json.loads(capsys.readouterr().out)["freshness"]
    assert fresh == {"status": "fresh", "source_pack": str(pack.resolve()), "source_pack_origin": "argument", "reasons": []}

    bars = pack / "levels" / LEVEL / "bars.yaml"
    bars.write_text(bars.read_text() + "\n# edited after compile\n")

    assert cli.main(["inspect", str(pack), "--primary-level", LEVEL]) == 0
    captured = capsys.readouterr()
    assert f"Freshness: STALE, checked against {pack.resolve()} (argument)" in captured.out
    assert "WARNING: artifact freshness is STALE" in captured.err

    bars.write_text(bars.read_text().replace("initial: 1.0", "initial: 0.5", 1))
    assert cli.main(["inspect", str(pack), "--primary-level", LEVEL, "--format", "json"]) == 0
    stale = json.loads(capsys.readouterr().out)["freshness"]
    assert stale["status"] == "stale"
    assert any("config_hash differs" in reason for reason in stale["reasons"])


def test_inspect_artifact_whose_source_pack_is_gone_is_unknown(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pack = _pack(tmp_path)
    UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=True)
    kept = tmp_path / "kept.msgpack"
    shutil.copyfile(pack / ".compiled" / f"universe-{LEVEL}.msgpack", kept)
    shutil.rmtree(pack)
    capsys.readouterr()

    assert cli.main(["inspect", str(kept), "--format", "json"]) == 0
    freshness = json.loads(capsys.readouterr().out)["freshness"]
    assert freshness["status"] == "unknown"
    assert freshness["source_pack_origin"] == "recorded in artifact"


def test_inspect_file_form_names_the_recorded_source_pack(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = _pack(tmp_path, "source")
    UniverseCompiler().compile(source, primary_level=LEVEL, use_cache=True)
    copy = tmp_path / "copy"
    shutil.copytree(source, copy)
    capsys.readouterr()

    assert cli.main(["inspect", str(copy / ".compiled" / f"universe-{LEVEL}.msgpack")]) == 0
    assert f"Freshness: FRESH, checked against {source.resolve()} (recorded in artifact)" in capsys.readouterr().out


def test_copied_pack_with_its_cache_is_a_miss_bound_to_the_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _pack(tmp_path, "source")
    UniverseCompiler().compile(source, primary_level=LEVEL, use_cache=True)
    copy = tmp_path / "copy"
    shutil.copytree(source, copy)  # .compiled travels with it

    counter = _count_lowerings(monkeypatch)
    compiled = UniverseCompiler().compile(copy, primary_level=LEVEL, use_cache=True)

    assert counter["calls"] == 1, "a cache built for another path was served"
    assert compiled.experiment_dir == copy.resolve()


def test_fingerprint_and_git_sha_do_not_depend_on_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pack = _pack(tmp_path)
    compiler = UniverseCompiler()
    here = (compiler._build_cache_fingerprint(pack), compiler._get_git_sha())
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert (compiler._build_cache_fingerprint(pack), compiler._get_git_sha()) == here


def test_cache_hit_from_another_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pack = _pack(tmp_path)
    UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=True)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    counter = _count_lowerings(monkeypatch)
    UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=True)
    assert counter["calls"] == 0


def test_uncommitted_source_edit_moves_provenance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_root = tmp_path / "townlet_src"
    (fake_root / "universe").mkdir(parents=True)
    module = fake_root / "universe" / "compiler.py"
    module.write_text("X = 1\n")
    monkeypatch.setattr(UniverseCompiler, "_package_root", staticmethod(lambda: fake_root))
    pack = _pack(tmp_path)
    compiler = UniverseCompiler()

    before = compiler._build_cache_fingerprint(pack)
    module.write_text("X = 2\n")
    after = compiler._build_cache_fingerprint(pack)

    assert before[0] == after[0], "config_hash is pack content only"
    assert before[1] != after[1], "an uncommitted source edit must move provenance"


def test_cache_staleness_is_the_compile_fast_path_rule(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    compiled = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=True)
    reloaded = CompiledUniverse.load_from_cache(pack / ".compiled" / f"universe-{LEVEL}.msgpack")
    compiler = UniverseCompiler()

    assert compiler.cache_staleness(compiled, pack) == []
    assert compiler.cache_staleness(reloaded, pack) == []
    other = _pack(tmp_path, "other")
    assert any("compiled from" in reason for reason in compiler.cache_staleness(reloaded, other))
