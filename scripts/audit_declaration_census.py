"""Ambiguity census: perturb each closed-vocabulary declaration, see what the compiler notices.

METHOD. For each probe below, copy configs/default_curriculum, change ONE declared value to
another LEGAL member of its own vocabulary, recompile, and record which of the five provenance
hashes move. Nothing else changes, so any difference is attributable to that one declaration.

BUCKETS ARE ASSIGNED HERE, BEFORE ANY RESULT IS SEEN (PDR-0049: assigning buckets after seeing
results is how a static sweep launders itself into a measurement).

  "structural" = this declaration CLAIMS to describe structure or semantics the compiled artifact
                 should encode.
  "control"    = this legitimately affects runtime/presentation only.

TWO HASH FAMILIES, AND CONFLATING THEM IS WHAT BROKE THE FIRST VERSION OF THIS SCRIPT:

  RAW    — stratum_hash, environment_hash, actions_hash, training_hash, bars_hash, ... Each is
           _compute_pydantic_hash over a whole config file, so EVERY declared value in that file
           moves it by construction. A raw-hash move proves only "this value is in a file that
           gets hashed". It is provenance for checkpoint safety, and it is never evidence that
           the compiler UNDERSTOOD the declaration.
  DERIVED — observation_schema_hash, action_schema_hash, vfs_hash, variable_schema_hash,
           transition_graph_hash. These cover what the compiler BUILT, so a move here means the
           declaration reached a compiled artifact.

WHAT THIS SCRIPT DOES *NOT* DO: emit a verdict. The first version compared five hand-picked
hashes, found `boundary` and `distance_metric` moving none of them, and reported them as
unhashed — a false finding (both move stratum_hash). Widening to all 16 then made the CONTROLS
move hashes too, because raw-file hashes move for everything. Either way the automated verdict
was wrong, because "should this declaration reach a derived artifact?" is a judgement about
intent that no perturbation can settle: `boundary` changes dynamics and legitimately reaches no
schema, while `range_type` claims to be a TYPE and should.

So this prints a MAP and stops. Read it, and bring the judgement yourself.
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

# Hashes over COMPILED artifacts rather than over a raw config file. See the
# module docstring: only a move here shows the compiler acted on a declaration.
_DERIVED = {"observation_schema", "action_schema", "vfs", "variable_schema", "transition_graph"}

# EVERY *_hash field, by reflection — never a hardcoded list.
#
# The first version of this script compared five hashes chosen by hand and so
# reported `boundary` and `distance_metric` as "structural declarations the
# compiler does not encode". Both are in fact hashed, into `stratum_hash`,
# which the hardcoded list omitted. A census that decides what to look at in
# advance measures its own list, not the tree. driver.py already had this
# right (collect_provenance_hashes); this now matches it.

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
        {"kind": "log_scaled", "clip": True},
        "structural",
        "minmax->log_scaled on meter 0",
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
    import dataclasses

    from townlet.universe.compiler import UniverseCompiler

    u = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    return {f.name: getattr(u, f.name) for f in dataclasses.fields(u) if f.name.endswith("_hash")}, u


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
        moved = [h.replace("_hash", "") for h in sorted(set(base) | set(got)) if got.get(h) != base.get(h)]
        rows.append((pid, bucket, path, ",".join(moved) if moved else "NOTHING", f"{old!r}->{newval!r}", note))

    print(f"{'probe':<20} {'bucket':<11} {'hashes moved':<46} change")
    print("-" * 130)
    for pid, bucket, path, moved, change, note in rows:
        print(f"{pid:<20} {bucket:<11} {moved:<46} {change}")

    print("\n=== READ THIS AS A MAP, NOT A VERDICT ===")
    print("RAW hashes move for every value in their file — they prove provenance, not comprehension.")
    print("DERIVED hashes (observation_schema/action_schema/vfs/variable_schema/transition_graph)")
    print("show the declaration reached a compiled artifact.\n")
    for pid, bucket, path, moved, change, note in rows:
        if moved in ("REJECTED", "PATH-NOT-FOUND"):
            print(f"  {pid:<20} not probed ({moved})")
            continue
        families = [m for m in moved.split(",") if m] if moved != "NOTHING" else []
        derived = sorted(set(families) & _DERIVED)
        raw = sorted(set(families) - _DERIVED)
        print(f"  {pid:<20} derived={derived or '[]':<40} raw={raw}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
