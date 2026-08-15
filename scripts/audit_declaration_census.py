"""Ambiguity census: perturb each closed-vocabulary declaration, see what the compiler notices.

METHOD. For each probe below, copy configs/default_curriculum, change ONE declared value to
another LEGAL member of its own vocabulary, recompile, and record which of the five provenance
hashes move. Nothing else changes, so any difference is attributable to that one declaration.

BUCKETS ARE ASSIGNED HERE, BEFORE ANY RESULT IS SEEN (PDR-0049: assigning buckets after seeing
results is how a static sweep launders itself into a measurement).

  "structural" = this declaration CLAIMS to describe structure or semantics the compiled artifact
                 should encode. Moving no hash makes it an ambiguity candidate.
  "control"    = this legitimately affects runtime/presentation only. Moving no hash is CORRECT.
                 Controls exist to test the prober: a control that moves a hash means the
                 prober's own reasoning is wrong.
"""

import shutil
import sys
import tempfile
import traceback
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "configs/default_curriculum"
TMP = Path(tempfile.gettempdir()) / "townlet-declaration-census"
LEVEL = "L1_full_observability"

HASHES = ("observation_schema_hash", "action_schema_hash", "vfs_hash", "variable_schema_hash", "transition_graph_hash")

# (id, relative file, dotted path into the YAML, new value, bucket, note)
PROBES = [
    (
        "boundary",
        "stratum.yaml",
        "stratum.substrate.grid.boundary",
        "wrap",
        "structural",
        "clamp->wrap: edge behaviour",
    ),
    (
        "distance_metric",
        "stratum.yaml",
        "stratum.substrate.grid.distance_metric",
        "euclidean",
        "structural",
        "manhattan->euclidean",
    ),
    (
        "observation_encoding",
        "stratum.yaml",
        "stratum.substrate.grid.observation_encoding",
        "scaled",
        "structural",
        "relative->scaled: coord encoding",
    ),
    (
        "diagonals",
        "stratum.yaml",
        "stratum.substrate.grid.diagonals",
        False,
        "structural",
        "true->false: changes legal moves",
    ),
    (
        "observation_mode",
        "stratum.yaml",
        "stratum.observation_mode.mode",
        "max_compact",
        "structural",
        "full_auto->max_compact",
    ),
    (
        "temporal_support",
        "stratum.yaml",
        "stratum.temporal_support",
        "disabled",
        "structural",
        "enabled->disabled",
    ),
    (
        "vision_support",
        "stratum.yaml",
        "stratum.vision_support",
        "global",
        "control",
        "declares SUPPORTED modes; gates validity, not structure",
    ),
    (
        "range_type",
        "environment.yaml",
        "environment.meters.0.range_type",
        "integer",
        "structural",
        "normalized->integer on meter 0",
    ),
    (
        "norm_method",
        "environment.yaml",
        "environment.variables.0.normalization.method",
        "normalize",
        "structural",
        "clip->normalize",
    ),
    (
        "var_scope",
        "environment.yaml",
        "environment.variables.0.scope",
        "global",
        "structural",
        "agent->global",
    ),
    (
        "active_vision",
        f"levels/{LEVEL}/curriculum.yaml",
        "curriculum.active_vision",
        "partial",
        "structural",
        "global->partial (POMDP)",
    ),
    (
        "label_preset",
        "actions.yaml",
        "actions.labels.preset",
        "cardinal",
        "control",
        "action NAMES only",
    ),
    (
        "learning_rate",
        f"levels/{LEVEL}/training.yaml",
        "training.population.size",
        16,
        "control",
        "hyperparameter",
    ),
]


def dotted_set(doc, path, value):
    parts = path.split(".")
    cur = doc
    for p in parts[:-1]:
        cur = cur[int(p)] if p.isdigit() else cur[p]
    last = parts[-1]
    key = int(last) if last.isdigit() else last
    old = cur[key]
    cur[key] = value
    return old


def compile_hashes(pack: Path):
    from townlet.universe.compiler import UniverseCompiler

    u = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    return {h: getattr(u, h) for h in HASHES}, u


def main():
    sys.path.insert(0, str(REPO / "src"))
    if TMP.exists():
        shutil.rmtree(TMP)

    base_dir = TMP / "_base"
    base_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC, base_dir)
    base, _ = compile_hashes(base_dir)
    print(f"baseline compiled OK ({LEVEL})\n")

    rows = []
    for pid, relfile, path, newval, bucket, note in PROBES:
        work = TMP / pid
        shutil.copytree(SRC, work)
        target = work / relfile
        doc = yaml.safe_load(target.read_text())
        try:
            old = dotted_set(doc, path, newval)
        except Exception as exc:
            rows.append((pid, bucket, path, "PATH-NOT-FOUND", f"{type(exc).__name__}: {exc}", note))
            continue
        target.write_text(yaml.safe_dump(doc, sort_keys=False))
        try:
            got, _ = compile_hashes(work)
        except Exception as exc:
            msg = str(exc).strip().splitlines()[-1][:110]
            rows.append((pid, bucket, path, "REJECTED", f"{old!r}->{newval!r}: {msg}", note))
            continue
        moved = [h.replace("_hash", "") for h in HASHES if got[h] != base[h]]
        rows.append((pid, bucket, path, ",".join(moved) if moved else "NOTHING", f"{old!r}->{newval!r}", note))

    print(f"{'probe':<20} {'bucket':<11} {'hashes moved':<46} change")
    print("-" * 130)
    for pid, bucket, path, moved, change, note in rows:
        print(f"{pid:<20} {bucket:<11} {moved:<46} {change}")

    print("\n=== VERDICTS ===")
    for pid, bucket, path, moved, change, note in rows:
        if moved in ("REJECTED", "PATH-NOT-FOUND"):
            v = "n/a — could not probe"
        elif bucket == "structural" and moved == "NOTHING":
            v = "*** AMBIGUITY CANDIDATE — structural declaration the compiler does not encode"
        elif bucket == "structural":
            v = "ok — encoded"
        elif bucket == "control" and moved == "NOTHING":
            v = "ok — control behaved as predicted"
        else:
            v = "!!! PROBER WRONG — a control moved a hash; re-examine the bucket assignment"
        print(f"  {pid:<20} {v}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
