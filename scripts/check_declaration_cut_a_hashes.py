"""Compare the complete Cut A hash inventory with its committed before snapshot."""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path

from townlet.universe.compiler import UniverseCompiler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    baseline = json.loads((root / "docs/product/evidence/declaration-cut-a/before-hashes.json").read_text())
    changes = []
    readings = 0
    for record in baseline["cases"]:
        universe = UniverseCompiler().compile(root / record["pack"], primary_level=record["primary_level"], use_cache=False)
        hashes = {field.name: getattr(universe, field.name) for field in dataclasses.fields(universe) if field.name.endswith("_hash")}
        hashes["metadata.config_hash"] = universe.metadata.config_hash
        for name, metadata in universe.all_levels.items():
            hashes.update(
                {
                    f"all_levels.{name}.{field.name}": getattr(metadata, field.name)
                    for field in dataclasses.fields(metadata)
                    if field.name.endswith("_hash")
                }
            )
        if hashes.keys() != record["hashes"].keys():
            raise RuntimeError(f"Hash inventory changed for {record['pack']}:{record['primary_level']}")
        readings += len(hashes)
        for key, value in record["hashes"].items():
            if hashes[key] != value:
                changes.append(
                    {"pack": record["pack"], "level": record["primary_level"], "field": key, "before": value, "after": hashes[key]}
                )
    unexpected = [
        row
        for row in changes
        if row["field"] != "metadata.config_hash" or row["pack"] not in {"configs/default_curriculum", "configs/test/items_smoke"}
    ]
    report = {
        "baseline_source": baseline.get("source_commit"),
        "cases": len(baseline["cases"]),
        "readings": readings,
        "changes": changes,
        "unexpected": unexpected,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['cases']} cases, {readings} readings, {len(changes)} permitted input-hash changes, {len(unexpected)} unexpected")
    return int(bool(unexpected))


if __name__ == "__main__":
    raise SystemExit(main())
