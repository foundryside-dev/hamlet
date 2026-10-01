"""Reproduce the measured DIV-015 attribution from the retained diagnostic bank."""

import hashlib
import json
import subprocess
from pathlib import Path

from townlet.oracle.harness import _pack_files, pack_drift
from townlet.oracle.matrix import default_cells
from townlet.universe.compiler import UniverseCompiler
from townlet.vfs.schema import VariableDef
from townlet.vfs.schema_hashes import canonical_variable_schema, compute_vfs_hash


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def entry(variable):
    norm = variable.normalization
    return {
        "id": variable.id,
        "type": variable.type,
        "scope": str(variable.scope),
        "dims": variable.dims,
        "lifetime": variable.lifetime,
        "readable_by": sorted(variable.readable_by),
        "writable_by": sorted(variable.writable_by),
        "range": [norm.min, norm.max] if norm is not None and norm.kind == "minmax" else None,
    }


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


root = Path.cwd()
out = root / "docs/product/evidence/static-epistemic-access"
diagnostic = root / "runs/static-epistemic-access/diagnostic-91374849"
report = json.loads((diagnostic / "report.json").read_text())
assert not report["trace_failed"] and not report["reset_failed"]
assert len(report["changes"]) == 150
commits = {
    key: subprocess.check_output(["git", "rev-parse", ref], text=True).strip()
    for key, ref in [("policy", "30b6adaa"), ("identity", "3db56521")]
}
entries = []
for change in report["changes"]:
    if change["path"] == "/metadata.config_hash":
        cause = "Required explicit role fields were added to the unchanged variable declarations; raw YAML transport fingerprint changes."
        commit = commits["policy"]
    elif change["path"].endswith("variable_schema_hash"):
        cause = (
            "Tagged registry identity and qualified item type/lifetime/role/range descriptors replace the registry-only canonical payload. "
            "Permissions remain unchanged for inherited scenarios."
        )
        commit = commits["identity"]
    elif change["path"].endswith("vfs_hash"):
        cause = (
            "Existing four-term VFS composition receives the changed variable schema hash; "
            "observation, action and transition inputs remain identical."
        )
        commit = commits["identity"]
    else:
        raise ValueError(change)
    entries.append({**change, "cause": cause, "causing_commit": commit, "register_ref": "DIV-015"})
write(
    out / "attributions.json",
    {"diagnostic_source": report["source_commit"], "baseline_source": report["baseline_source"], "entries": entries},
)
before = json.loads((out / "before/before-products.json").read_text())["cases"]
hashes = json.loads((out / "before/before-hashes.json").read_text())["cases"]
by_case = {(v["pack"], v["primary_level"]): v["hashes"] for v in hashes}
records = []
for case in before:
    universe = UniverseCompiler().compile(root / case["pack"], primary_level=case["primary_level"], use_cache=False)
    oldhash = by_case[(case["pack"], case["primary_level"])]
    for name, products in case["levels"].items():
        olddefs = [VariableDef.model_validate(v) for v in products["variables"]]
        oldpayload = [entry(v) for v in sorted(olddefs, key=lambda v: v.id)]
        level = universe.get_level(name)
        profiles = universe.compiled_vfs_profiles
        assert profiles is not None and profiles.item_profiles is not None
        payload = canonical_variable_schema(level.vfs_variables, profiles.item_profiles)
        # Old ordinary descriptor semantics are unchanged, including sorted roles.
        ordinary = [row["definition"] for row in payload if row["identity"][0] == "registry"]
        assert ordinary == oldpayload, (case["pack"], name)
        oldkey = "all_levels." + name + ".variable_schema_hash"
        assert digest(oldpayload) == oldhash[oldkey], (case["pack"], name, "old hash")
        assert digest(payload) == level.variable_schema_hash, (case["pack"], name, "new hash")
        for field in ["observation_schema_hash", "action_schema_hash", "transition_graph_hash"]:
            assert oldhash["all_levels." + name + "." + field] == getattr(level, field), (case["pack"], name, field)
        assert (
            compute_vfs_hash(
                level.variable_schema_hash, level.observation_schema_hash, level.action_schema_hash, level.transition_graph_hash
            )
            == level.vfs_hash
        )
        records.append(
            {
                "pack": case["pack"],
                "primary_level": case["primary_level"],
                "level": name,
                "before": oldpayload,
                "after": payload,
                "before_hash": digest(oldpayload),
                "after_hash": digest(payload),
                "ordinary_semantics_unchanged": True,
                "other_vfs_inputs_unchanged": True,
            }
        )
write(out / "canonical-schema-attribution.json", {"source_commit": report["source_commit"], "cases": records})
packs = sorted({cell.params.pack for cell in default_cells()})
inventory = []
for pack in packs:
    oldfiles = _pack_files(root / "oracle_fixtures" / pack)
    newfiles = _pack_files(root / pack)
    inventory.append(
        {
            "pack": pack,
            "delta": pack_drift(root / "oracle_fixtures", root, pack),
            "frozen_files": {k: hashlib.sha256(v).hexdigest() for k, v in oldfiles.items()},
            "live_files": {k: hashlib.sha256(v).hexdigest() for k, v in newfiles.items()},
        }
    )
write(
    out / "frozen-live-inputs.json",
    {"source_commit": report["source_commit"], "frozen_tag": "oracle-2026-08-17", "register_ref": "DIV-015", "packs": inventory},
)
print("exact attributions", len(entries), "canonical projections", len(records), "matrix input packs", len(inventory))
