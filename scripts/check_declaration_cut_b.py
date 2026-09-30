"""Compare Cut B with its committed parent census and replay its exact CPU actions.

The frozen-oracle matrix is a separate gate. This direct-parent comparison never
inherits historical output allowances: each changed hash/reset reading needs an
exact, attributed entry and every trace stream stays byte-exact.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import torch

import townlet
from townlet.determinism import seed_all
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.oracle.harness import pack_drift, run_side
from townlet.oracle.trace_io import RunParams, load_trace
from townlet.universe.compiler import UniverseCompiler

BASELINE_SOURCE = "599cad15706ac8824c3f8e38276da6440c4816a3"
STREAMS = ("obs", "actions", "dones", "rewards")
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/product/evidence/declaration-cut-b"
_MISSING = object()


def json_value(value: Any) -> Any:
    return json.loads(json.dumps(value))


def differences(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    """Exhaustive structural changes; missing values remain distinct from null."""
    if isinstance(before, dict) and isinstance(after, dict):
        changes = []
        for name in sorted(before.keys() | after.keys()):
            changes.extend(differences(before.get(name, _MISSING), after.get(name, _MISSING), f"{path}/{name}"))
        return changes
    if isinstance(before, list) and isinstance(after, list):
        changes = []
        for index in range(max(len(before), len(after))):
            old = before[index] if index < len(before) else _MISSING
            new = after[index] if index < len(after) else _MISSING
            changes.extend(differences(old, new, f"{path}/{index}"))
        return changes
    if before is not _MISSING and after is not _MISSING and type(before) is type(after) and before == after:
        return []
    row = {"path": path, "before_present": before is not _MISSING, "after_present": after is not _MISSING}
    if before is not _MISSING:
        row["before"] = before
    if after is not _MISSING:
        row["after"] = after
    return [row]


def compare_stream(before: np.ndarray, after: np.ndarray) -> dict[str, Any]:
    """Compare real byte content, including signed zero and identical NaN payloads."""
    equal = before.shape == after.shape and before.dtype == after.dtype and before.tobytes() == after.tobytes()
    result = {
        "equal": equal,
        "before": {"dtype": str(before.dtype), "shape": list(before.shape), "sha256": hashlib.sha256(before.tobytes()).hexdigest()},
        "after": {"dtype": str(after.dtype), "shape": list(after.shape), "sha256": hashlib.sha256(after.tobytes()).hexdigest()},
    }
    if not equal and before.shape == after.shape and before.dtype == after.dtype:
        byte_width = before.dtype.itemsize
        old = np.ascontiguousarray(before).view(np.uint8).reshape(*before.shape, byte_width)
        new = np.ascontiguousarray(after).view(np.uint8).reshape(*after.shape, byte_width)
        differing_elements = np.any(old != new, axis=-1)
        indices = np.argwhere(differing_elements)
        result["differing_element_count"] = int(differing_elements.sum())
        result["first_indices"] = indices[:10].tolist()
    return result


def classify_changes(changes: list[dict[str, Any]], approvals: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """An exact reading/value pair is authorized once; stale entries also fail."""
    by_key = {}
    for entry in approvals:
        key = (entry["kind"], entry["pack"], entry["level"], entry["path"])
        if key in by_key:
            raise ValueError(f"Duplicate attribution: {key}")
        if not all(entry.get(name) for name in ("cause", "causing_commit", "register_ref")):
            raise ValueError(f"Attribution lacks explicit cause, causing_commit or register_ref: {key}")
        if not all(name in entry for name in ("before_present", "after_present")):
            raise ValueError(f"Attribution omits value-presence flags: {key}")
        by_key[key] = entry
    unexplained = []
    for change in changes:
        key = (change["kind"], change["pack"], change["level"], change["path"])
        entry = by_key.pop(key, None)
        comparable = ("before_present", "after_present", "before", "after")
        if entry is None or any(
            (name in change) != (name in entry)
            or json.dumps(change.get(name), sort_keys=True) != json.dumps(entry.get(name), sort_keys=True)
            for name in comparable
        ):
            unexplained.append(change)
        else:
            change["attribution"] = {name: entry[name] for name in ("cause", "causing_commit", "register_ref")}
    return unexplained, list(by_key.values())


def read_baseline(filename: str) -> dict[str, Any]:
    payload = json.loads((EVIDENCE / filename).read_text())
    if payload["source_commit"] != BASELINE_SOURCE:
        raise ValueError(f"Wrong source baseline in {filename}")
    return payload


def product(level: Any) -> dict[str, Any]:
    return json_value(
        {
            "variables": [variable.model_dump(mode="json") for variable in level.vfs_variables],
            "token_spec": dataclasses.asdict(level.token_spec),
        }
    )


def tensor_payload(value: torch.Tensor) -> dict[str, Any]:
    return {"dtype": str(value.dtype), "shape": list(value.shape), "values": value.cpu().tolist()}


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def run_census(output: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    baseline = read_baseline("before-hashes.json")
    baseline_products = {(row["pack"], row["primary_level"]): row for row in read_baseline("before-variable-products.json")["cases"]}
    changes = []
    cases = []
    readings = 0
    for record in baseline["cases"]:
        pack, primary = record["pack"], record["primary_level"]
        universe = UniverseCompiler().compile(ROOT / pack, primary_level=primary, use_cache=False)
        hashes = {field.name: getattr(universe, field.name) for field in dataclasses.fields(universe) if field.name.endswith("_hash")}
        hashes["metadata.config_hash"] = universe.metadata.config_hash
        products = {}
        for name, level in universe.all_levels.items():
            hashes.update(
                {
                    f"all_levels.{name}.{field.name}": getattr(level, field.name)
                    for field in dataclasses.fields(level)
                    if field.name.endswith("_hash")
                }
            )
            products[name] = product(level)
        readings += len(hashes)
        hash_changes = differences(record["hashes"], hashes)
        for change in hash_changes:
            changes.append({"kind": "hash", "pack": pack, "level": primary, **change})
        product_changes = differences(baseline_products[(pack, primary)]["levels"], products)
        cases.append(
            {"pack": pack, "primary_level": primary, "hashes": hashes, "hash_changes": hash_changes, "product_changes": product_changes}
        )
        print(f"census {pack}:{primary}: {len(hash_changes)} hash / {len(product_changes)} product differences", flush=True)
    census = {"case_count": len(cases), "reading_count": readings, "cases": cases}
    if len(cases) != baseline["case_count"] or readings != baseline["reading_count"]:
        raise ValueError("Hash inventory cardinality changed; inspect before extending the accepted surface")
    write_json(output / "after-census.json", census)
    old_inputs = read_baseline("before-inputs.json")["files"]
    inputs = {
        file.relative_to(ROOT).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in sorted((ROOT / "configs").rglob("*"))
        if file.is_file() and file.suffix in {".yaml", ".yml"}
    }
    input_changes = differences(old_inputs, inputs)
    frozen_deltas = {
        row["params"]["pack"]: pack_drift(ROOT / "oracle_fixtures", ROOT, row["params"]["pack"])
        for row in read_baseline("before-cpu-traces.json")["cells"]
    }
    write_json(
        output / "after-inputs.json", {"files": inputs, "changes_from_parent": input_changes, "complete_frozen_deltas": frozen_deltas}
    )
    return changes, census


def run_resets(output: Path) -> list[dict[str, Any]]:
    changes = []
    results = []
    for record in read_baseline("before-resets.json")["cases"]:
        pack, level_name = record["pack"], record["level"]
        universe = UniverseCompiler().compile(ROOT / pack, primary_level=level_name, use_cache=False)
        seed_all(record["seed"])
        env = VectorizedHamletEnv(universe=universe, level_name=level_name, num_agents=record["num_agents"], device=torch.device("cpu"))
        if record["action"] != env.action_dim - 1:
            raise ValueError(f"Action inventory changed for {pack}:{level_name}")
        env.reset()
        current = {"initial": {name: tensor_payload(value) for name, value in env._current_vfs_state().items()}}
        for _ in range(record["steps"]):
            env.step(torch.full((record["num_agents"],), record["action"], dtype=torch.int64))
        current["after_steps"] = {name: tensor_payload(value) for name, value in env._current_vfs_state().items()}
        env.reset()
        current["after_reset"] = {name: tensor_payload(value) for name, value in env._current_vfs_state().items()}
        old = {name: record[name] for name in ("initial", "after_steps", "after_reset")}
        delta = differences(old, current)
        changes.extend({"kind": "reset", "pack": pack, "level": level_name, **row} for row in delta)
        results.append({"pack": pack, "level": level_name, "readings": current, "changes": delta})
    write_json(output / "after-resets.json", {"cases": results})
    return changes


def run_cpu(output: Path) -> tuple[list[dict[str, Any]], bool]:
    changes = []
    results = []
    failed = False
    for record in read_baseline("before-cpu-traces.json")["cells"]:
        params = RunParams(**record["params"])
        old_path = ROOT / record["file"]
        if hashlib.sha256(old_path.read_bytes()).hexdigest() != record["file_sha256"]:
            raise ValueError(f"Before trace file changed: {old_path}")
        old = load_trace(old_path)
        if dataclasses.asdict(old.params) != record["params"] or old.hashes != record["hashes"]:
            raise ValueError(f"Before trace metadata changed: {old_path}")
        for name in STREAMS:
            array = getattr(old, name)
            reading = {"dtype": str(array.dtype), "shape": list(array.shape), "sha256": hashlib.sha256(array.tobytes()).hexdigest()}
            if reading != record["streams"][name]:
                raise ValueError(f"Before stream changed: {old_path}:{name}")
        new_path = output / f"{record['cell_id']}.npz"
        failure = run_side(
            driver=ROOT / "src/townlet/oracle/driver.py",
            src=ROOT / "src",
            params=params,
            out=new_path,
            repo_root=ROOT,
            pack_root=ROOT,
            actions=old_path,
        )
        if failure is not None:
            results.append({"cell_id": record["cell_id"], "failure": dataclasses.asdict(failure)})
            failed = True
            continue
        new = load_trace(new_path)
        if new.params != old.params or new.code_root != str(ROOT / "src") or new.pack_root != str(ROOT):
            raise ValueError(f"After trace identity mismatch: {new_path}")
        stream_readings = {name: compare_stream(getattr(old, name), getattr(new, name)) for name in STREAMS}
        failed = failed or any(not reading["equal"] for reading in stream_readings.values())
        hash_changes = differences(old.hashes, new.hashes)
        changes.extend({"kind": "trace_hash", "pack": params.pack, "level": params.level, **row} for row in hash_changes)
        results.append(
            {
                "cell_id": record["cell_id"],
                "hash_changes": hash_changes,
                "streams": stream_readings,
                "code_root": new.code_root,
                "pack_root": new.pack_root,
                "action_source": new.action_source,
            }
        )
        print(
            f"parent replay {record['cell_id']}: {'FAIL' if any(not r['equal'] for r in stream_readings.values()) else 'byte-exact'}",
            flush=True,
        )
    write_json(output / "after-cpu-traces.json", {"cells": results, "failed": failed})
    return changes, failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new directory for complete reports and after traces")
    parser.add_argument("--attributions", type=Path, help="exact changed readings with cause, causing_commit and register_ref")
    parser.add_argument("--skip-cpu", action="store_true", help="diagnostic census only; cannot qualify CPU behavior")
    args = parser.parse_args()
    if Path(townlet.__file__).resolve().parent.parent != ROOT / "src":
        raise ValueError("Wrong imported townlet source root")
    args.output.mkdir(parents=True, exist_ok=False)
    provenance = {
        "baseline_source": BASELINE_SOURCE,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "working_tree_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "cpu_executed": not args.skip_cpu,
    }
    changed_execution_files = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD", "--", "src", "configs", "scripts", "tests"], cwd=ROOT, text=True
    ).splitlines()
    untracked_execution_files = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "--", "src", "configs", "scripts", "tests"], cwd=ROOT, text=True
    ).splitlines()
    provenance["uncommitted_execution_files"] = sorted(set(changed_execution_files + untracked_execution_files))
    provenance["clean_execution_tree"] = not provenance["uncommitted_execution_files"]
    write_json(args.output / "provenance.json", provenance)
    changes, census = run_census(args.output)
    changes.extend(run_resets(args.output))
    trace_failed = False
    if not args.skip_cpu:
        trace_changes, trace_failed = run_cpu(args.output)
        changes.extend(trace_changes)
    # A trace selected-level hash and its census reading are distinct evidence;
    # attribution must explicitly include both. Duplicate identical trace readings
    # occur only when the same pack/level is deliberately repeated in the matrix.
    approvals = json.loads(args.attributions.read_text())["entries"] if args.attributions else []
    unexplained, stale = classify_changes(changes, approvals)
    report = {
        "provenance": provenance,
        "case_count": census["case_count"],
        "reading_count": census["reading_count"],
        "changes": changes,
        "unattributed": unexplained,
        "stale_attributions": stale,
        "trace_failed": trace_failed,
        "qualified": not args.skip_cpu and not unexplained and not stale and not trace_failed and provenance["clean_execution_tree"],
    }
    write_json(args.output / "report.json", report)
    print(f"{len(changes)} changed readings; {len(unexplained)} unattributed; {len(stale)} stale; trace_failed={trace_failed}", flush=True)
    return int(bool(unexplained or stale or trace_failed or args.skip_cpu or not provenance["clean_execution_tree"]))


if __name__ == "__main__":
    raise SystemExit(main())
