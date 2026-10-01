"""Bank and compare static-access behavior against an explicit unchanged parent.

The inherited recipes describe the comparison surface; they do not authorize
output changes. Every observation/action/reward/done byte and reset reading
must remain exact. Only identity readings admit exact, causal attribution.
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import torch

import townlet
from townlet.determinism import seed_all
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.oracle.harness import run_side
from townlet.oracle.trace_io import RunParams, Trace, load_trace
from townlet.universe.compiler import UniverseCompiler

STREAMS = ("obs", "actions", "dones", "rewards")
RECIPE_ORIGIN = "docs/product/evidence/declaration-cut-b"
_MISSING = object()


def git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], cwd=root, text=True).strip()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def differences(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    if isinstance(before, dict) and isinstance(after, dict):
        return [
            change
            for name in sorted(before.keys() | after.keys())
            for change in differences(before.get(name, _MISSING), after.get(name, _MISSING), f"{path}/{name}")
        ]
    if isinstance(before, list) and isinstance(after, list):
        return [
            change
            for i in range(max(len(before), len(after)))
            for change in differences(before[i] if i < len(before) else _MISSING, after[i] if i < len(after) else _MISSING, f"{path}/{i}")
        ]
    if before is not _MISSING and after is not _MISSING and type(before) is type(after) and before == after:
        return []
    change = {"path": path, "before_present": before is not _MISSING, "after_present": after is not _MISSING}
    if before is not _MISSING:
        change["before"] = before
    if after is not _MISSING:
        change["after"] = after
    return [change]


def compare_stream(before: np.ndarray, after: np.ndarray) -> dict[str, Any]:
    def reading(value: np.ndarray) -> dict[str, Any]:
        return {"dtype": str(value.dtype), "shape": list(value.shape), "sha256": sha256(value.tobytes())}

    return {
        "equal": before.shape == after.shape and before.dtype == after.dtype and before.tobytes() == after.tobytes(),
        "before": reading(before),
        "after": reading(after),
    }


def attribution_result(
    changes: list[dict[str, Any]], entries: list[dict[str, Any]], *, trace_failed: bool, reset_failed: bool
) -> dict[str, Any]:
    keys = ("kind", "pack", "level", "path")
    readings = ("before_present", "after_present", "before", "after")
    by_key = {}
    for entry in entries:
        if not all(entry.get(name) for name in (*keys, "cause", "causing_commit", "register_ref")):
            raise ValueError("Attribution requires exact reading identity and provenance")
        if entry["kind"] not in {"hash", "trace_hash"}:
            raise ValueError("Only identity hashes may be attributed; output changes cannot be excused")
        if not re.fullmatch(r"[0-9a-f]{40}", entry["causing_commit"]) or not re.fullmatch(r"DIV-\d+", entry["register_ref"]):
            raise ValueError("Attribution provenance requires a full causing commit and DIV reference")
        if not all(isinstance(entry.get(name), bool) for name in ("before_present", "after_present")):
            raise ValueError("Attribution requires explicit value-presence flags")
        key = tuple(entry[name] for name in keys)
        if key in by_key:
            raise ValueError(f"Duplicate attribution: {key}")
        by_key[key] = entry
    unattributed = []
    for change in changes:
        key = tuple(change[name] for name in keys)
        entry = by_key.get(key)
        matches = entry is not None and all(
            (name in change) == (name in entry)
            and json.dumps(change.get(name), sort_keys=True) == json.dumps(entry.get(name), sort_keys=True)
            for name in readings
        )
        if matches:
            by_key.pop(key)
        else:
            unattributed.append(change)
    stale = list(by_key.values())
    return {
        "changes": changes,
        "unattributed": unattributed,
        "stale_attributions": stale,
        "trace_failed": trace_failed,
        "reset_failed": reset_failed,
        "qualified": not (unattributed or stale or trace_failed or reset_failed),
    }


def require_inventory(actual: list[dict[str, Any]], expected: list[dict[str, Any]], fields: tuple[str, ...], label: str) -> None:
    try:
        keys = [tuple(row[name] for name in fields) for row in actual]
        expected_keys = [tuple(row[name] for name in fields) for row in expected]
    except (KeyError, TypeError) as error:
        raise ValueError(f"{label} inventory lacks required identity") from error
    if len(set(keys)) != len(keys) or len(set(expected_keys)) != len(expected_keys) or set(keys) != set(expected_keys):
        raise ValueError(f"{label} inventory missing, duplicate or substituted cases")


def validate_source_commit(root: Path, source: str) -> None:
    if not isinstance(source, str) or not re.fullmatch(r"[0-9a-f]{40}", source):
        raise ValueError("Invalid baseline source: full commit SHA required")
    check = subprocess.run(["git", "merge-base", "--is-ancestor", source, "HEAD"], cwd=root, capture_output=True)
    if check.returncode != 0 or git(root, "rev-parse", f"{source}^{{commit}}") != source:
        raise ValueError("Invalid baseline source: existing ancestor required")


def clean_source(root: Path) -> str:
    modified = git(root, "diff", "--name-only", "HEAD", "--", "src", "configs", "scripts", "tests", "pyproject.toml", "uv.lock")
    untracked = git(
        root, "ls-files", "--others", "--exclude-standard", "--", "src", "configs", "scripts", "tests", "pyproject.toml", "uv.lock"
    )
    if modified or untracked:
        raise ValueError(f"Dirty execution-bearing tree: {modified}\n{untracked}")
    source = git(root, "rev-parse", "HEAD")
    validate_source_commit(root, source)
    return source


def verified_trace(record: dict[str, Any], trace_base: Path) -> Trace:
    path = (trace_base / record["file"]).resolve()
    if not path.is_file() or sha256(path.read_bytes()) != record["file_sha256"]:
        raise ValueError(f"Before trace file digest mismatch: {path}")
    trace = load_trace(path)
    if dataclasses.asdict(trace.params) != record["params"] or trace.hashes != record["hashes"]:
        raise ValueError(f"Before trace metadata mismatch: {path}")
    for field in ("code_root", "pack_root", "action_source"):
        if field in record and getattr(trace, field) != record[field]:
            raise ValueError(f"Before trace provenance mismatch: {path}:{field}")
    for name in STREAMS:
        if compare_stream(getattr(trace, name), getattr(trace, name))["before"] != record["streams"][name]:
            raise ValueError(f"Before trace stream digest mismatch: {path}:{name}")
    return trace


def inherited_recipes(root: Path, source: str) -> dict[str, Any]:
    def committed(filename: str) -> dict[str, Any]:
        return json.loads(git(root, "show", f"{source}:{RECIPE_ORIGIN}/{filename}"))

    census = committed("before-hashes.json")["cases"]
    traces = committed("before-cpu-traces.json")["cells"]
    resets = committed("before-resets.json")["cases"]
    recipe = {
        "census": [{"pack": row["pack"], "primary_level": row["primary_level"]} for row in census],
        "traces": [{"cell_id": row["cell_id"], "params": row["params"]} for row in traces],
        "resets": [
            {name: row[name] for name in ("pack", "level", "seed", "num_agents", "action", "action_basis", "steps")} for row in resets
        ],
    }
    for name, count, fields in (("census", 31, ("pack", "primary_level")), ("traces", 10, ("cell_id",)), ("resets", 11, ("pack", "level"))):
        if len(recipe[name]) != count:
            raise ValueError(f"Inherited {name} inventory must contain {count} cases")
        require_inventory(recipe[name], recipe[name], fields, name)
    return recipe


def validate_census_inventory(root: Path, source: str, hashes: list[dict[str, Any]], product_rows: list[dict[str, Any]]) -> None:
    """The bank cannot narrow hash keys or compiled level rosters retroactively."""
    expected_hashes = json.loads(git(root, "show", f"{source}:{RECIPE_ORIGIN}/before-hashes.json"))
    expected_products = json.loads(git(root, "show", f"{source}:{RECIPE_ORIGIN}/before-variable-products.json"))
    fields = ("pack", "primary_level")
    require_inventory(hashes, expected_hashes["cases"], fields, "hash")
    require_inventory(product_rows, expected_products["cases"], fields, "product")
    indexed_hashes = {(r["pack"], r["primary_level"]): r for r in expected_hashes["cases"]}
    indexed_products = {(r["pack"], r["primary_level"]): r for r in expected_products["cases"]}
    for row in hashes:
        if set(row["hashes"]) != set(indexed_hashes[(row["pack"], row["primary_level"])]["hashes"]):
            raise ValueError(f"Per-case hash reading inventory changed: {row['pack']}:{row['primary_level']}")
    for row in product_rows:
        if set(row["levels"]) != set(indexed_products[(row["pack"], row["primary_level"])]["levels"]):
            raise ValueError(f"Compiled level product inventory changed: {row['pack']}:{row['primary_level']}")
    if sum(len(r["hashes"]) for r in hashes) != expected_hashes["reading_count"]:
        raise ValueError("Inherited hash reading inventory cardinality changed")


def products(level: Any) -> dict[str, Any]:
    return json.loads(
        json.dumps(
            {"variables": [v.model_dump(mode="json") for v in level.vfs_variables], "token_spec": dataclasses.asdict(level.token_spec)}
        )
    )


def census_case(root: Path, recipe: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    universe = UniverseCompiler().compile(root / recipe["pack"], primary_level=recipe["primary_level"], use_cache=False)
    hashes = {field.name: getattr(universe, field.name) for field in dataclasses.fields(universe) if field.name.endswith("_hash")}
    hashes["metadata.config_hash"] = universe.metadata.config_hash
    levels = {}
    for name, level in universe.all_levels.items():
        hashes.update(
            {
                f"all_levels.{name}.{field.name}": getattr(level, field.name)
                for field in dataclasses.fields(level)
                if field.name.endswith("_hash")
            }
        )
        levels[name] = products(level)
    print(f"census {recipe['pack']}:{recipe['primary_level']}", flush=True)
    return {**recipe, "hashes": hashes}, {**recipe, "levels": levels}


def reset_case(root: Path, recipe: dict[str, Any]) -> dict[str, Any]:
    universe = UniverseCompiler().compile(root / recipe["pack"], primary_level=recipe["level"], use_cache=False)
    seed_all(recipe["seed"])
    env = VectorizedHamletEnv(universe=universe, level_name=recipe["level"], num_agents=recipe["num_agents"], device=torch.device("cpu"))
    if recipe["action"] != env.action_dim - 1:
        raise ValueError(f"Reset action inventory changed: {recipe['pack']}:{recipe['level']}")

    def state() -> dict[str, Any]:
        return {
            name: {
                "dtype": str(value.dtype),
                "shape": list(value.shape),
                "values": value.cpu().tolist(),
                "sha256": sha256(value.detach().cpu().numpy().tobytes()),
            }
            for name, value in env._current_vfs_state().items()
        }

    env.reset()
    initial = state()
    for _ in range(recipe["steps"]):
        env.step(torch.full((recipe["num_agents"],), recipe["action"], dtype=torch.int64))
    stepped = state()
    env.reset()
    print(f"reset {recipe['pack']}:{recipe['level']}", flush=True)
    return {**recipe, "initial": initial, "after_steps": stepped, "after_reset": state()}


def trace_record(path: Path, base: Path, cell_id: str, trace: Trace) -> dict[str, Any]:
    return {
        "cell_id": cell_id,
        "file": path.relative_to(base).as_posix(),
        "file_sha256": sha256(path.read_bytes()),
        "params": dataclasses.asdict(trace.params),
        "hashes": trace.hashes,
        "code_root": trace.code_root,
        "pack_root": trace.pack_root,
        "action_source": trace.action_source,
        "streams": {name: compare_stream(getattr(trace, name), getattr(trace, name))["before"] for name in STREAMS},
    }


def generate_trace(root: Path, output: Path, recipe: dict[str, Any], actions: Path | None) -> Trace:
    failure = run_side(
        driver=root / "src/townlet/oracle/driver.py",
        src=root / "src",
        params=RunParams(**recipe["params"]),
        out=output,
        repo_root=root,
        pack_root=root,
        actions=actions,
    )
    if failure is not None:
        raise RuntimeError(f"CPU trace failed {recipe['cell_id']}: {failure}")
    trace = load_trace(output)
    if dataclasses.asdict(trace.params) != recipe["params"] or trace.code_root != str(root / "src") or trace.pack_root != str(root):
        raise ValueError(f"CPU trace source identity mismatch: {output}")
    print(f"traced {recipe['cell_id']}", flush=True)
    return trace


def capture(root: Path, output: Path) -> None:
    source = clean_source(root)
    recipes = inherited_recipes(root, source)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    payloads: dict[str, Any] = {"recipes": recipes}
    rows, product_rows = [], []
    for recipe in recipes["census"]:
        row, product_row = census_case(root, recipe)
        rows.append(row)
        product_rows.append(product_row)
    validate_census_inventory(root, source, rows, product_rows)
    payloads["hashes"] = {"cases": rows, "case_count": len(rows), "reading_count": sum(len(r["hashes"]) for r in rows)}
    payloads["products"] = {"cases": product_rows}
    inputs = {}
    for file in sorted((root / "configs").rglob("*")):
        if file.is_file() and file.suffix in {".yaml", ".yml"}:
            raw = file.read_bytes()
            inputs[file.relative_to(root).as_posix()] = {"sha256": sha256(raw), "bytes_base64": base64.b64encode(raw).decode("ascii")}
    payloads["inputs"] = {"files": inputs}
    payloads["resets"] = {"cases": [reset_case(root, recipe) for recipe in recipes["resets"]]}
    traces = []
    for index, recipe in enumerate(recipes["traces"]):
        path = output / f"cpu-{index:02d}.npz"
        traces.append(trace_record(path, output, recipe["cell_id"], generate_trace(root, path, recipe, None)))
    payloads["traces"] = {"cells": traces, "cuda": "not executed; this bank captures the ten inherited CPU recipes only"}
    if clean_source(root) != source:
        raise ValueError("Execution source changed during capture")
    reports = {}
    for name, payload in payloads.items():
        path = output / f"before-{name}.json"
        write_json(path, {"source_commit": source, **payload})
        reports[name] = {"file": path.name, "sha256": sha256(path.read_bytes())}
    write_json(
        output / "manifest.json",
        {"format_version": 1, "source_commit": source, "source_root": str(root), "trace_base": str(output), "reports": reports},
    )
    print(f"BANKED {source}: 31 inventories, 10 CPU traces, 11 resets", flush=True)


def validate_inputs(root: Path, source: str, files: dict[str, Any]) -> None:
    committed_paths = {
        name
        for name in git(root, "ls-tree", "-r", "--name-only", source, "--", "configs").splitlines()
        if Path(name).suffix in {".yaml", ".yml"}
    }
    if set(files) != committed_paths:
        raise ValueError("Baseline config input inventory differs from committed source")
    for name, record in files.items():
        try:
            raw = base64.b64decode(record["bytes_base64"], validate=True)
        except (KeyError, ValueError) as error:
            raise ValueError(f"Invalid exact config bytes: {name}") from error
        committed = subprocess.check_output(["git", "show", f"{source}:{name}"], cwd=root)
        if sha256(raw) != record["sha256"] or raw != committed:
            raise ValueError(f"Baseline config bytes/digest mismatch: {name}")


def load_before(root: Path, before: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    manifest_path = before / "manifest.json" if before.is_dir() else before
    manifest = json.loads(manifest_path.read_text())
    if manifest["format_version"] != 1:
        raise ValueError("Unsupported static-access bank format")
    source = manifest["source_commit"]
    validate_source_commit(root, source)
    expected = inherited_recipes(root, source)
    payloads = {}
    for name in ("recipes", "hashes", "products", "inputs", "resets", "traces"):
        reference = manifest["reports"][name]
        path = manifest_path.parent / reference["file"]
        if sha256(path.read_bytes()) != reference["sha256"]:
            raise ValueError(f"Before report digest mismatch: {name}")
        payload = json.loads(path.read_text())
        if payload["source_commit"] != source:
            raise ValueError(f"Wrong baseline source in {name}")
        payloads[name] = payload
    recipes = {name: payloads["recipes"][name] for name in expected}
    if recipes != expected:
        raise ValueError("Inherited recipe inventory or parameters changed")
    for name, key, expected_name, fields in (
        ("hashes", "cases", "census", ("pack", "primary_level")),
        ("products", "cases", "census", ("pack", "primary_level")),
        ("resets", "cases", "resets", ("pack", "level")),
        ("traces", "cells", "traces", ("cell_id",)),
    ):
        require_inventory(payloads[name][key], expected[expected_name], fields, name)
    hash_rows = payloads["hashes"]["cases"]
    validate_census_inventory(root, source, hash_rows, payloads["products"]["cases"])
    if payloads["hashes"]["case_count"] != 31 or payloads["hashes"]["reading_count"] != sum(len(r["hashes"]) for r in hash_rows):
        raise ValueError("Baseline hash inventory cardinality mismatch")
    for key, expected_name, identity in (("resets", "resets", ("pack", "level")), ("traces", "traces", ("cell_id",))):
        indexed = {tuple(r[f] for f in identity): r for r in payloads[key]["cells" if key == "traces" else "cases"]}
        for recipe in expected[expected_name]:
            record = indexed[tuple(recipe[f] for f in identity)]
            if any(record[name] != value for name, value in recipe.items()):
                raise ValueError(f"Baseline {key} recipe parameters changed")
    validate_inputs(root, source, payloads["inputs"]["files"])
    trace_base = Path(manifest["trace_base"])
    if not trace_base.is_absolute():
        trace_base = (manifest_path.parent / trace_base).resolve()
    for record in payloads["traces"]["cells"]:
        verified_trace(record, trace_base)
    return manifest, payloads, trace_base


def compare(root: Path, before: Path, output: Path, attributions: Path) -> int:
    source = clean_source(root)
    manifest, baseline, trace_base = load_before(root, before)
    approvals = json.loads(attributions.read_text())["entries"]
    # Validate provenance against real ancestor commits before executing the bank.
    for entry in approvals:
        validate_source_commit(root, entry["causing_commit"])
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    changes, census, product_changes, current_products = [], [], [], []
    old_products = {(r["pack"], r["primary_level"]): r for r in baseline["products"]["cases"]}
    for record in baseline["hashes"]["cases"]:
        recipe = {name: record[name] for name in ("pack", "primary_level")}
        row, product_row = census_case(root, recipe)
        delta = differences(record["hashes"], row["hashes"])
        changes.extend({"kind": "hash", "pack": row["pack"], "level": row["primary_level"], **r} for r in delta)
        census.append(row)
        current_products.append(product_row)
        product_changes.extend(
            {"pack": row["pack"], "level": row["primary_level"], **r}
            for r in differences(old_products[(row["pack"], row["primary_level"])]["levels"], product_row["levels"])
        )
    validate_census_inventory(root, manifest["source_commit"], census, current_products)
    write_json(output / "after-census.json", {"cases": census, "product_changes": product_changes})
    reset_results = []
    for record in baseline["resets"]["cases"]:
        recipe = {name: record[name] for name in ("pack", "level", "seed", "num_agents", "action", "action_basis", "steps")}
        new = reset_case(root, recipe)
        reset_results.append({"pack": recipe["pack"], "level": recipe["level"], "readings": new, "changes": differences(record, new)})
    reset_failed = any(r["changes"] for r in reset_results)
    write_json(output / "after-resets.json", {"cases": reset_results, "failed": reset_failed})
    trace_results, trace_failed = [], False
    for index, record in enumerate(baseline["traces"]["cells"]):
        old = verified_trace(record, trace_base)
        new_path = output / f"cpu-{index:02d}.npz"
        new = generate_trace(root, new_path, record, trace_base / record["file"])
        streams = {name: compare_stream(getattr(old, name), getattr(new, name)) for name in STREAMS}
        trace_failed |= any(not value["equal"] for value in streams.values())
        delta = differences(old.hashes, new.hashes)
        changes.extend({"kind": "trace_hash", "pack": new.params.pack, "level": new.params.level, **r} for r in delta)
        trace_results.append({**trace_record(new_path, output, record["cell_id"], new), "comparison": streams})
    write_json(output / "after-traces.json", {"cells": trace_results, "failed": trace_failed})
    old_inputs = {name: record["sha256"] for name, record in baseline["inputs"]["files"].items()}
    current_inputs = {
        file.relative_to(root).as_posix(): sha256(file.read_bytes())
        for file in sorted((root / "configs").rglob("*"))
        if file.is_file() and file.suffix in {".yaml", ".yml"}
    }
    write_json(output / "after-inputs.json", {"files": current_inputs, "changes": differences(old_inputs, current_inputs)})
    if clean_source(root) != source:
        raise ValueError("Execution source changed during comparison")
    report = {
        **attribution_result(changes, approvals, trace_failed=trace_failed, reset_failed=reset_failed),
        "source_commit": source,
        "baseline_source": manifest["source_commit"],
        "case_count": len(census),
        "reading_count": sum(len(r["hashes"]) for r in census),
        "cpu_count": len(trace_results),
        "reset_count": len(reset_results),
    }
    write_json(output / "report.json", report)
    print(
        f"{len(changes)} changed identities; {len(report['unattributed'])} unattributed; "
        f"{len(report['stale_attributions'])} stale; trace_failed={trace_failed}; reset_failed={reset_failed}",
        flush=True,
    )
    return int(not report["qualified"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    bank = commands.add_parser("capture", help="capture the unchanged parent before product edits")
    bank.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("compare", help="compare against a supplied manifest and retained raw traces")
    check.add_argument("--before", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    check.add_argument("--attributions", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(__file__).resolve().parents[1]
    if Path(townlet.__file__).resolve().parent.parent != root / "src":
        raise ValueError("Wrong imported townlet source root")
    if args.command == "capture":
        capture(root, args.output)
        return 0
    return compare(root, args.before, args.output, args.attributions)


if __name__ == "__main__":
    raise SystemExit(main())
