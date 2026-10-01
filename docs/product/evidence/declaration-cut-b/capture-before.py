"""Capture Cut B's immutable parent hash, declaration and CPU trace baseline."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import subprocess
from pathlib import Path

import torch
import yaml

import townlet
from townlet.determinism import seed_all
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.oracle.harness import run_side
from townlet.oracle.matrix import default_cells
from townlet.oracle.trace_io import load_trace
from townlet.universe.compiler import UniverseCompiler

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
SOURCE = "599cad15706ac8824c3f8e38276da6440c4816a3"
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == SOURCE
assert Path(townlet.__file__).resolve().parent.parent == ROOT / "src"


def write_json(name, payload):
    (EVIDENCE / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def tensor_payload(value):
    return {"dtype": str(value.dtype), "shape": list(value.shape), "values": value.cpu().tolist()}


baseline = json.loads((ROOT / "docs/product/evidence/declaration-cut-a/before-hashes.json").read_text())
cases = []
compiled = []
for case in baseline["cases"]:
    universe = UniverseCompiler().compile(ROOT / case["pack"], primary_level=case["primary_level"], use_cache=False)
    hashes = {field.name: getattr(universe, field.name) for field in dataclasses.fields(universe) if field.name.endswith("_hash")}
    hashes["metadata.config_hash"] = universe.metadata.config_hash
    for level_name, level in universe.all_levels.items():
        for field in dataclasses.fields(level):
            if field.name.endswith("_hash"):
                hashes[f"all_levels.{level_name}.{field.name}"] = getattr(level, field.name)
    assert hashes.keys() == case["hashes"].keys()
    cases.append({"pack": case["pack"], "primary_level": case["primary_level"], "hashes": hashes})
    compiled.append(
        {
            "pack": case["pack"],
            "primary_level": case["primary_level"],
            "levels": {
                name: {
                    "variables": [definition.model_dump(mode="json") for definition in level.vfs_variables],
                    "token_spec": dataclasses.asdict(level.token_spec),
                }
                for name, level in universe.all_levels.items()
            },
        }
    )
    print(f"captured {case['pack']}:{case['primary_level']}", flush=True)
write_json(
    "before-hashes.json",
    {"source_commit": SOURCE, "case_count": len(cases), "reading_count": sum(len(case["hashes"]) for case in cases), "cases": cases},
)
write_json("before-variable-products.json", {"source_commit": SOURCE, "cases": compiled})

inputs = {}
variable_documents = []
for file in sorted((ROOT / "configs").rglob("*")):
    if not file.is_file() or file.suffix not in {".yaml", ".yml"}:
        continue
    relative = file.relative_to(ROOT).as_posix()
    inputs[relative] = hashlib.sha256(file.read_bytes()).hexdigest()
    data = yaml.safe_load(file.read_text())
    if isinstance(data, dict) and any(key in data for key in ("variables", "global", "agent", "item_profiles")):
        variable_documents.append({"path": relative, "payload": data})
write_json("before-inputs.json", {"source_commit": SOURCE, "files": inputs})
write_json("before-variable-transports.json", {"source_commit": SOURCE, "documents": variable_documents})

run_dir = ROOT / "runs/differential/declaration-cut-b-before-599cad15"
run_dir.mkdir(parents=True, exist_ok=False)
traces = []
for cell in default_cells():
    if cell.params.device != "cpu":
        continue
    output = run_dir / f"{cell.cell_id}.npz"
    failure = run_side(
        driver=ROOT / "src/townlet/oracle/driver.py", src=ROOT / "src", params=cell.params, out=output, repo_root=ROOT, pack_root=ROOT
    )
    if failure is not None:
        raise RuntimeError(f"before trace failed {cell.cell_id}: {failure}")
    trace = load_trace(output)
    traces.append(
        {
            "cell_id": cell.cell_id,
            "params": dataclasses.asdict(trace.params),
            "hashes": trace.hashes,
            "code_root": trace.code_root,
            "pack_root": trace.pack_root,
            "action_source": trace.action_source,
            "file": output.relative_to(ROOT).as_posix(),
            "file_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "streams": {
                name: {
                    "dtype": str(getattr(trace, name).dtype),
                    "shape": list(getattr(trace, name).shape),
                    "sha256": hashlib.sha256(getattr(trace, name).tobytes()).hexdigest(),
                }
                for name in ("obs", "actions", "dones", "rewards")
            },
        }
    )
    print(f"traced {cell.cell_id}", flush=True)
write_json(
    "before-cpu-traces.json",
    {
        "source_commit": SOURCE,
        "cells": traces,
        "cuda": "not executed; ten declared CUDA cells remain to be reported as skips by the acceptance matrix",
    },
)

reset_readings = []
selected = {(cell.params.pack, cell.params.level) for cell in default_cells() if cell.params.device == "cpu"}
selected.add(("configs/L5_multi_agent", "L5_multi_agent"))
for pack, level_name in sorted(selected):
    universe = UniverseCompiler().compile(ROOT / pack, primary_level=level_name, use_cache=False)
    seed_all(42)
    env = VectorizedHamletEnv(universe=universe, level_name=level_name, num_agents=4, device=torch.device("cpu"))
    env.reset()
    initial = {name: tensor_payload(value) for name, value in env._current_vfs_state().items()}
    for _ in range(3):
        env.step(torch.full((4,), env.action_dim - 1, dtype=torch.int64))
    stepped = {name: tensor_payload(value) for name, value in env._current_vfs_state().items()}
    env.reset()
    reset = {name: tensor_payload(value) for name, value in env._current_vfs_state().items()}
    reset_readings.append(
        {
            "pack": pack,
            "level": level_name,
            "seed": 42,
            "num_agents": 4,
            "action": env.action_dim - 1,
            "action_basis": "existing fleet smoke's final action index, not assumed WAIT",
            "steps": 3,
            "initial": initial,
            "after_steps": stepped,
            "after_reset": reset,
        }
    )
    print(f"reset census {pack}:{level_name}", flush=True)
write_json("before-resets.json", {"source_commit": SOURCE, "cases": reset_readings})
print(
    f"BANKED {len(cases)} cases; {sum(len(case['hashes']) for case in cases)} hash readings; "
    f"{len(traces)} CPU traces; {len(reset_readings)} resets",
    flush=True,
)
