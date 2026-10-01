"""Negative controls for the static-access evidence instrument."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from scripts.check_epistemic_access import (
    attribution_result,
    build_parser,
    compare_stream,
    require_inventory,
    validate_source_commit,
    verified_trace,
)
from townlet.oracle.trace_io import RunParams, Trace, save_trace


def _change() -> dict:
    return {
        "kind": "hash",
        "pack": "configs/example",
        "level": "L0",
        "path": "/vfs_hash",
        "before_present": True,
        "after_present": True,
        "before": "old",
        "after": "new",
    }


def _attribution() -> dict:
    return {**_change(), "cause": "authored permission enters semantic identity", "causing_commit": "a" * 40, "register_ref": "DIV-015"}


def test_no_changes_with_no_allowances_qualifies() -> None:
    assert attribution_result([], [], trace_failed=False, reset_failed=False)["qualified"]


def test_exact_attribution_qualifies() -> None:
    result = attribution_result([_change()], [_attribution()], trace_failed=False, reset_failed=False)
    assert result["qualified"]
    assert not result["unattributed"]


def test_missing_attribution_cannot_qualify() -> None:
    result = attribution_result([_change()], [], trace_failed=False, reset_failed=False)
    assert not result["qualified"]
    assert result["unattributed"] == [_change()]


def test_stale_attribution_cannot_qualify() -> None:
    result = attribution_result([], [_attribution()], trace_failed=False, reset_failed=False)
    assert not result["qualified"]
    assert result["stale_attributions"] == [_attribution()]


@pytest.mark.parametrize("field,value", [("before", "wrong"), ("after", "wrong"), ("before_present", False)])
def test_attribution_must_match_values_and_presence(field: str, value: object) -> None:
    attribution = _attribution()
    attribution[field] = value
    assert not attribution_result([_change()], [attribution], trace_failed=False, reset_failed=False)["qualified"]


@pytest.mark.parametrize("field", ["cause", "causing_commit", "register_ref"])
def test_attribution_requires_provenance(field: str) -> None:
    entry = _attribution()
    entry.pop(field)
    with pytest.raises(ValueError, match="provenance"):
        attribution_result([_change()], [entry], trace_failed=False, reset_failed=False)


def test_duplicate_attribution_refuses() -> None:
    with pytest.raises(ValueError, match="Duplicate attribution"):
        attribution_result([_change()], [_attribution(), _attribution()], trace_failed=False, reset_failed=False)


@pytest.mark.parametrize("failed", ["trace", "reset"])
def test_hash_allowances_cannot_excuse_changed_outputs(failed: str) -> None:
    result = attribution_result([_change()], [_attribution()], trace_failed=failed == "trace", reset_failed=failed == "reset")
    assert not result["qualified"]


@pytest.mark.parametrize("stream", ["obs", "actions", "rewards", "dones"])
def test_every_stream_requires_byte_exact_values(stream: str) -> None:
    dtype = {"obs": np.float32, "actions": np.int64, "rewards": np.float32, "dones": np.bool_}[stream]
    old = np.zeros((2, 2), dtype=dtype)
    new = old.copy()
    new[0, 0] = 1
    assert not compare_stream(old, new)["equal"]
    assert compare_stream(old, old.copy())["equal"]


def test_stream_checks_signed_zero_shape_and_dtype() -> None:
    assert not compare_stream(np.array([0.0], dtype=np.float32), np.array([-0.0], dtype=np.float32))["equal"]
    assert not compare_stream(np.zeros(2), np.zeros((1, 2)))["equal"]
    assert not compare_stream(np.zeros(2, dtype=np.float32), np.zeros(2, dtype=np.float64))["equal"]


@pytest.mark.parametrize("actual", [[{"id": "a"}], [{"id": "a"}, {"id": "a"}], [{"id": "a"}, {"id": "c"}]])
def test_missing_duplicate_or_substituted_case_refuses(actual: list[dict]) -> None:
    with pytest.raises(ValueError, match="inventory"):
        require_inventory(actual, [{"id": "a"}, {"id": "b"}], ("id",), "CPU")


def test_reordered_complete_inventory_is_valid() -> None:
    require_inventory([{"id": "b"}, {"id": "a"}], [{"id": "a"}, {"id": "b"}], ("id",), "CPU")


@pytest.fixture
def git_root(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "source.txt").write_text("baseline")
    subprocess.run(["git", "add", "source.txt"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.test", "commit", "-qm", "baseline"], cwd=tmp_path, check=True
    )
    return tmp_path


def test_baseline_source_must_be_exact_existing_ancestor(git_root: Path) -> None:
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=git_root, text=True).strip()
    validate_source_commit(git_root, source)
    for wrong in ("HEAD", source[:8], "f" * 40):
        with pytest.raises(ValueError, match="baseline source"):
            validate_source_commit(git_root, wrong)


def test_retained_trace_file_and_stream_digests_are_checked(tmp_path: Path) -> None:
    path = tmp_path / "cell.npz"
    params = RunParams("configs/example", "L0", 1, 1, 42, "cpu")
    trace = Trace(
        params,
        {"vfs_hash": "value"},
        np.zeros((2, 1, 1), dtype=np.float32),
        np.zeros((1, 1), dtype=np.float32),
        np.zeros((1, 1), dtype=np.bool_),
        np.zeros((1, 1), dtype=np.int64),
        "/source",
        "/packs",
        "seeded-random",
    )
    save_trace(path, trace)
    record = {
        "file": path.name,
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "params": params.__dict__,
        "hashes": trace.hashes,
        "code_root": trace.code_root,
        "pack_root": trace.pack_root,
        "streams": {
            name: compare_stream(getattr(trace, name), getattr(trace, name))["before"] for name in ("obs", "actions", "dones", "rewards")
        },
    }
    assert verified_trace(record, tmp_path).params == params
    altered = json.loads(json.dumps(record))
    altered["streams"]["rewards"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="stream digest"):
        verified_trace(altered, tmp_path)
    record["file_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="file digest"):
        verified_trace(record, tmp_path)


@pytest.mark.parametrize("arguments", [["capture"], ["compare", "--output", "out"], ["compare", "--before", "before", "--output", "out"]])
def test_cli_requires_baseline_and_attributions(arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as error:
        build_parser().parse_args(arguments)
    assert error.value.code == 2


def test_cli_parses_complete_compare() -> None:
    args = build_parser().parse_args(["compare", "--before", "before", "--output", "out", "--attributions", "why.json"])
    assert isinstance(args, argparse.Namespace)
    assert args.command == "compare"


@pytest.fixture
def before_bank(git_root: Path) -> tuple[Path, Path]:
    """A complete bank with real source/input identity and retained trace bytes."""
    import base64

    from scripts.check_epistemic_access import trace_record, write_json

    config = git_root / "configs/example/world.yaml"
    config.parent.mkdir(parents=True)
    config.write_bytes(b"value: 1\n")
    history = git_root / "docs/product/evidence/declaration-cut-b"
    history.mkdir(parents=True)
    census = [{"pack": "configs/example", "primary_level": f"L{i}"} for i in range(31)]
    traces = [
        {
            "cell_id": f"cell-{i}",
            "params": {"pack": "configs/example", "level": f"L{i}", "num_agents": 1, "steps": 1, "seed": 42, "device": "cpu"},
        }
        for i in range(10)
    ]
    resets = [
        {
            "pack": "configs/example",
            "level": f"L{i}",
            "seed": 42,
            "num_agents": 1,
            "action": 0,
            "action_basis": "declared final action",
            "steps": 1,
        }
        for i in range(11)
    ]
    for name, key, rows in (("hashes", "cases", census), ("cpu-traces", "cells", traces), ("resets", "cases", resets)):
        write_json(
            history / f"before-{name}.json",
            {
                key: [{**r, "hashes": {"vfs_hash": "same"}} for r in rows] if name == "hashes" else rows,
                **({"reading_count": 31} if name == "hashes" else {}),
            },
        )
    write_json(history / "before-variable-products.json", {"cases": [{**r, "levels": {r["primary_level"]: {}}} for r in census]})
    subprocess.run(["git", "add", "configs", "docs"], cwd=git_root, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.test", "commit", "-qm", "recipes"], cwd=git_root, check=True
    )
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=git_root, text=True).strip()
    bank = git_root / "bank"
    bank.mkdir()
    payloads = {
        "recipes": {"census": census, "traces": traces, "resets": resets},
        "hashes": {"cases": [{**r, "hashes": {"vfs_hash": "same"}} for r in census], "case_count": 31, "reading_count": 31},
        "products": {"cases": [{**r, "levels": {r["primary_level"]: {}}} for r in census]},
        "inputs": {
            "files": {
                "configs/example/world.yaml": {
                    "sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
                    "bytes_base64": base64.b64encode(config.read_bytes()).decode("ascii"),
                }
            }
        },
        "resets": {"cases": [{**r, "initial": {}, "after_steps": {}, "after_reset": {}} for r in resets]},
    }
    records = []
    for i, recipe in enumerate(traces):
        path = bank / f"trace-{i}.npz"
        trace = Trace(
            RunParams(**recipe["params"]),
            {"vfs_hash": "same"},
            np.zeros((2, 1, 1), dtype=np.float32),
            np.zeros((1, 1), dtype=np.float32),
            np.zeros((1, 1), dtype=np.bool_),
            np.zeros((1, 1), dtype=np.int64),
            "/source",
            "/packs",
            "seeded-random",
        )
        save_trace(path, trace)
        records.append(trace_record(path, bank, recipe["cell_id"], trace))
    payloads["traces"] = {"cells": records}
    reports = {}
    for name, payload in payloads.items():
        path = bank / f"before-{name}.json"
        write_json(path, {"source_commit": source, **payload})
        reports[name] = {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    write_json(bank / "manifest.json", {"format_version": 1, "source_commit": source, "trace_base": ".", "reports": reports})
    return git_root, bank


def _rewrite_report(bank: Path, name: str, mutate) -> None:
    from scripts.check_epistemic_access import write_json

    manifest = json.loads((bank / "manifest.json").read_text())
    path = bank / manifest["reports"][name]["file"]
    payload = json.loads(path.read_text())
    mutate(payload)
    write_json(path, payload)
    manifest["reports"][name]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    write_json(bank / "manifest.json", manifest)


def test_complete_bank_resolves_relative_trace_base(before_bank: tuple[Path, Path]) -> None:
    from scripts.check_epistemic_access import load_before

    root, bank = before_bank
    manifest, payloads, trace_base = load_before(root, bank / "manifest.json")
    assert trace_base == bank
    assert len(payloads["traces"]["cells"]) == 10
    assert manifest["source_commit"] == subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


@pytest.mark.parametrize("report,key", [("hashes", "cases"), ("products", "cases"), ("resets", "cases"), ("traces", "cells")])
@pytest.mark.parametrize("failure", ["missing", "duplicate"])
def test_bank_case_completeness_cannot_be_rewritten(before_bank: tuple[Path, Path], report: str, key: str, failure: str) -> None:
    from scripts.check_epistemic_access import load_before

    root, bank = before_bank

    def mutate(payload):
        if failure == "missing":
            payload[key].pop()
        else:
            payload[key].append(payload[key][0])

    _rewrite_report(bank, report, mutate)
    with pytest.raises(ValueError, match="inventory"):
        load_before(root, bank)


def test_modified_report_refuses_even_with_valid_json(before_bank: tuple[Path, Path]) -> None:
    from scripts.check_epistemic_access import load_before

    root, bank = before_bank
    path = bank / "before-hashes.json"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="report digest"):
        load_before(root, bank)


def test_wrong_report_source_refuses(before_bank: tuple[Path, Path]) -> None:
    from scripts.check_epistemic_access import load_before

    root, bank = before_bank
    _rewrite_report(bank, "products", lambda d: d.update(source_commit="0" * 40))
    with pytest.raises(ValueError, match="baseline source"):
        load_before(root, bank)


def test_config_byte_bank_must_match_source_commit(before_bank: tuple[Path, Path]) -> None:
    import base64

    from scripts.check_epistemic_access import load_before

    root, bank = before_bank

    def mutate(payload):
        raw = b"value: 2\n"
        payload["files"]["configs/example/world.yaml"] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes_base64": base64.b64encode(raw).decode("ascii"),
        }

    _rewrite_report(bank, "inputs", mutate)
    with pytest.raises(ValueError, match="config bytes/digest"):
        load_before(root, bank)


def test_bank_config_inventory_must_include_all_source_yaml(before_bank: tuple[Path, Path]) -> None:
    from scripts.check_epistemic_access import load_before

    root, bank = before_bank
    _rewrite_report(bank, "inputs", lambda d: d["files"].clear())
    with pytest.raises(ValueError, match="config input inventory"):
        load_before(root, bank)


@pytest.mark.parametrize("report,key", [("recipes", "traces"), ("traces", "cells")])
def test_replay_recipe_parameters_cannot_be_substituted(before_bank: tuple[Path, Path], report: str, key: str) -> None:
    from scripts.check_epistemic_access import load_before

    root, bank = before_bank

    def mutate(payload):
        payload[key][0]["params"]["seed"] = 999

    _rewrite_report(bank, report, mutate)
    with pytest.raises(ValueError, match="recipe"):
        load_before(root, bank)


def test_dirty_execution_tree_cannot_capture(git_root: Path, tmp_path: Path) -> None:
    from scripts.check_epistemic_access import capture

    product = git_root / "src/future.py"
    product.parent.mkdir()
    product.write_text("changed = True\n")
    with pytest.raises(ValueError, match="Dirty execution-bearing tree"):
        capture(git_root, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_rewritten_hash_count_cannot_hide_missing_reading(before_bank: tuple[Path, Path]) -> None:
    from scripts.check_epistemic_access import load_before

    root, bank = before_bank

    def mutate(payload):
        payload["cases"][0]["hashes"].clear()
        payload["reading_count"] -= 1

    _rewrite_report(bank, "hashes", mutate)
    with pytest.raises(ValueError, match="hash.*inventory"):
        load_before(root, bank)


def test_missing_product_level_refuses(before_bank: tuple[Path, Path]) -> None:
    from scripts.check_epistemic_access import load_before

    root, bank = before_bank
    _rewrite_report(bank, "products", lambda d: d["cases"][0]["levels"].clear())
    with pytest.raises(ValueError, match="level.*inventory"):
        load_before(root, bank)
