"""The five pack-scope content hashes are stamped AND compared (hamlet-2dde1015fe, F2).

`experiment_hash`, `stratum_hash`, `environment_hash`, `actions_hash` and `items_hash` were
computed, serialized and required on load since the compiler was written — and compared
against a checkpoint by nobody. Grid geometry is pack scope and no level can override it, so
a `stratum.yaml` edit such as `boundary: clamp -> wrap` moved NO level hash, no token layout
and no action count: `assert_checkpoint_identity(clamp-world checkpoint, wrap-world universe)`
returned True and a policy whose wall behaviour was learned on clamp resumed into wrap with
no signal at all.

This is the review's `gate_cov.py` as a test. Each case is one edit to a scratch copy of a
shipped pack; the legs are: **mover** (the named pack hash moves and reaches the checkpoint)
→ **narrowness** (for the two stratum edits, it is the ONLY compared field that moves — the
sharper half of the finding) → **negative control** (the unedited pack resumes) → **guard**
(the edited universe is refused through the composed gate, by name).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest

from townlet.training.checkpoint_utils import (
    CHECKPOINT_FORMAT_VERSION,
    PACK_HASH_KEYS,
    assert_checkpoint_identity,
    attach_universe_metadata,
)
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

REPO = Path(__file__).resolve().parents[3]

# Every field `assert_checkpoint_identity` hard-compares. `observation_schema_hash` and
# `meter_count` are stamped for the nested population gate, not compared here.
COMPARED = frozenset(
    {
        "vfs_hash",
        "action_dim",
        "layout_hash",
        "token_type_schema_hash",
        "drive_hash",
        "brain_hash",
        "curriculum_hash",
        "bars_hash",
        "affordances_hash",
        "training_hash",
        "primary_level",
        *PACK_HASH_KEYS,
    }
)


@dataclass(frozen=True)
class Edit:
    name: str
    pack: Path
    level: str
    file: str
    old: str
    new: str
    mover: str
    #: True when the edit must move the named pack hash and NOTHING else the gate compares:
    #: before this guard such an edit resumed silently.
    only_mover: bool


SIMPLE = REPO / "configs" / "simple"
ITEMS_SMOKE = REPO / "configs" / "test" / "items_smoke"

EDITS = (
    Edit("stratum_boundary_clamp_to_wrap", SIMPLE, "L0_simple", "stratum.yaml", "boundary: clamp", "boundary: wrap", "stratum_hash", True),
    Edit(
        "stratum_metric_manhattan_to_chebyshev",
        SIMPLE,
        "L0_simple",
        "stratum.yaml",
        "distance_metric: manhattan",
        "distance_metric: chebyshev",
        "stratum_hash",
        True,
    ),
    Edit(
        "stratum_diagonals_true_to_false",
        SIMPLE,
        "L0_simple",
        "stratum.yaml",
        "diagonals: true",
        "diagonals: false",
        "stratum_hash",
        False,
    ),
    Edit(
        "actions_wait_enabled_by_default_false",
        SIMPLE,
        "L0_simple",
        "actions.yaml",
        "enabled_by_default: true",
        "enabled_by_default: false",
        "actions_hash",
        False,
    ),
    Edit(
        "environment_first_meter_minmax_to_binary",
        SIMPLE,
        "L0_simple",
        "environment.yaml",
        "      range_type:\n        kind: minmax\n        clip: true\n",
        "      range_type:\n        kind: binary\n        threshold: 0.5\n",
        "environment_hash",
        False,
    ),
    Edit(
        "experiment_name_changed",
        SIMPLE,
        "L0_simple",
        "experiment.yaml",
        'experiment_name: "Simple"',
        'experiment_name: "Simple (renamed)"',
        "experiment_hash",
        True,
    ),
    Edit("items_medkit_duration_changed", ITEMS_SMOKE, "L0_smoke", "items.yaml", "duration: 100", "duration: 200", "items_hash", False),
)


def _pack(tmp_path: Path, source: Path, name: str) -> Path:
    """Copy a shipped pack, stripping every compiled artifact (stale-cache hazard)."""
    dest = tmp_path / name
    shutil.copytree(source, dest)
    for compiled in dest.rglob(".compiled"):
        shutil.rmtree(compiled, ignore_errors=True)
    for artifact in dest.rglob("*.msgpack"):
        artifact.unlink()
    return dest


def _apply(pack: Path, edit: Edit) -> None:
    path = pack / edit.file
    text = path.read_text()
    assert edit.old in text, f"{edit.file} no longer contains {edit.old!r}; re-derive the edit"
    path.write_text(text.replace(edit.old, edit.new, 1))


def _compile(pack: Path, level: str) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _stamped(universe: CompiledUniverse) -> dict[str, object]:
    checkpoint: dict[str, object] = {"version": CHECKPOINT_FORMAT_VERSION}
    attach_universe_metadata(checkpoint, universe)
    return checkpoint


@pytest.mark.parametrize("edit", EDITS, ids=[edit.name for edit in EDITS])
def test_pack_edit_moves_a_compared_hash_and_refuses_resume(tmp_path: Path, edit: Edit) -> None:
    base_pack = _pack(tmp_path, edit.pack, "base")
    mutated_pack = _pack(tmp_path, edit.pack, "mutated")
    _apply(mutated_pack, edit)

    base = _compile(base_pack, edit.level)
    mutated = _compile(mutated_pack, edit.level)
    base_checkpoint = _stamped(base)
    mutated_checkpoint = _stamped(mutated)

    # LEG 1 — mover: the named pack hash moves and the stamp carries it.
    assert base_checkpoint[edit.mover] == getattr(base, edit.mover)
    moved = {key for key in COMPARED if base_checkpoint[key] != mutated_checkpoint[key]}
    assert edit.mover in moved, f"{edit.mover} did not move; moved={sorted(moved)}"

    # LEG 2 — narrowness: before this guard these edits moved nothing the gate compared.
    if edit.only_mover:
        assert moved == {edit.mover}, f"edit is no longer narrow: moved={sorted(moved)}"

    # LEG 3 — negative control: the unedited pack resumes.
    assert assert_checkpoint_identity(base_checkpoint, base, force_new_vfs=False) is True

    # LEG 4 — guard: the edited universe is refused through the composed gate. A narrow
    # edit is refused by the pack-hash leg itself, by name.
    expected = f"{edit.mover} mismatch" if edit.only_mover else "mismatch"
    with pytest.raises(ValueError, match=expected):
        assert_checkpoint_identity(base_checkpoint, mutated, force_new_vfs=False)
