"""Effect dynamics and level spawn rules are checkpoint identity (compiler re-review N5).

Before this guard, `probes/gate_e2e.py` stamped a checkpoint from items_smoke and
`assert_checkpoint_identity` ACCEPTED a universe whose effect `wear_and_tear` had gone from
`1.0 * intensity` to `50.0 * intensity`, and one whose apple spawn rule had gone from
`spawn_count 3 / period 100` to `9 / 5`: no pack hash covered the `effects` family and no
level hash covered `items_appearance`. The item `on_use` control edit was refused on
`items_hash`. Same four legs as the pack-hash guard: mover, narrowness, negative control,
refusal by name.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest

from townlet.training.checkpoint_utils import (
    CHECKPOINT_FORMAT_VERSION,
    DEMO_CHECKPOINT_KEYS,
    LEVEL_HASH_KEYS,
    PACK_HASH_KEYS,
    assert_checkpoint_identity,
    attach_universe_metadata,
)
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

REPO = Path(__file__).resolve().parents[3]
ITEMS_SMOKE = REPO / "configs" / "test" / "items_smoke"
LEVEL = "L0_smoke"

COMPARED = frozenset(
    {
        "vfs_hash",
        "action_dim",
        "layout_hash",
        "token_type_schema_hash",
        "drive_hash",
        "brain_hash",
        "primary_level",
        *(key for key, _ in LEVEL_HASH_KEYS),
        *PACK_HASH_KEYS,
    }
)


@dataclass(frozen=True)
class Edit:
    name: str
    file: str
    old: str
    new: str
    mover: str
    only_mover: bool


EDITS = (
    Edit(
        "effect_body_wear_and_tear_1_to_50_times_intensity",
        "effects.yaml",
        '"item.condition - (1.0 * intensity)"',
        '"item.condition - (50.0 * intensity)"',
        "effects_hash",
        True,
    ),
    Edit(
        "appearance_apple_spawn_count_3_to_9",
        "levels/L0_smoke/items.yaml",
        "spawn_count: 3",
        "spawn_count: 9",
        "items_appearance_hash",
        True,
    ),
    Edit("appearance_apple_period_100_to_5", "levels/L0_smoke/items.yaml", "period: 100", "period: 5", "items_appearance_hash", True),
    Edit("control_item_on_use_edit", "items.yaml", "value: bar.energy + 0.3", "value: bar.energy + 0.4", "items_hash", False),
)


def _pack(tmp_path: Path, name: str) -> Path:
    dest = tmp_path / name
    shutil.copytree(ITEMS_SMOKE, dest, ignore=shutil.ignore_patterns(".compiled", "*.msgpack"))
    return dest


def _apply(pack: Path, edit: Edit) -> None:
    path = pack / edit.file
    text = path.read_text()
    assert edit.old in text, f"{edit.file} no longer contains {edit.old!r}; re-derive the edit"
    path.write_text(text.replace(edit.old, edit.new, 1))


def _compile(pack: Path) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _stamped(universe: CompiledUniverse) -> dict[str, object]:
    checkpoint: dict[str, object] = {"version": CHECKPOINT_FORMAT_VERSION}
    attach_universe_metadata(checkpoint, universe)
    return checkpoint


def test_both_new_hashes_are_stamped_and_in_the_closed_checkpoint_schema() -> None:
    assert "effects_hash" in PACK_HASH_KEYS and "effects_hash" in DEMO_CHECKPOINT_KEYS
    assert ("items_appearance_hash", "items_appearance") in LEVEL_HASH_KEYS and "items_appearance_hash" in DEMO_CHECKPOINT_KEYS


@pytest.mark.parametrize("edit", EDITS, ids=[edit.name for edit in EDITS])
def test_effect_or_appearance_edit_moves_a_compared_hash_and_refuses_resume(tmp_path: Path, edit: Edit) -> None:
    base = _compile(_pack(tmp_path, "base"))
    mutated_pack = _pack(tmp_path, "mutated")
    _apply(mutated_pack, edit)
    mutated = _compile(mutated_pack)
    base_checkpoint = _stamped(base)
    mutated_checkpoint = _stamped(mutated)

    # LEG 1 — mover: the named hash moves and the stamp carries it.
    source = base.get_level(LEVEL) if edit.mover == "items_appearance_hash" else base
    assert base_checkpoint[edit.mover] == getattr(source, edit.mover)
    moved = {key for key in COMPARED if base_checkpoint[key] != mutated_checkpoint[key]}
    assert edit.mover in moved, f"{edit.mover} did not move; moved={sorted(moved)}"

    # LEG 2 — narrowness: before this guard these edits moved nothing the gate compared.
    if edit.only_mover:
        assert moved == {edit.mover}, f"edit is no longer narrow: moved={sorted(moved)}"

    # LEG 3 — negative control: the unedited pack resumes.
    assert assert_checkpoint_identity(base_checkpoint, base, force_new_vfs=False) is True

    # LEG 4 — guard: the edited universe is refused through the composed gate, by name.
    with pytest.raises(ValueError, match=f"{edit.mover} mismatch"):
        assert_checkpoint_identity(base_checkpoint, mutated, force_new_vfs=False)


def test_effect_expression_respelling_moves_nothing(tmp_path: Path) -> None:
    """The hash is canonical content: a respaced expression is the same effect."""
    base = _compile(_pack(tmp_path, "base"))
    respelled_pack = _pack(tmp_path, "respelled")
    _apply(
        respelled_pack,
        Edit("respell", "effects.yaml", '"item.condition - (1.0 * intensity)"', '"item.condition-(1.0*intensity)"', "", False),
    )
    respelled = _compile(respelled_pack)
    assert respelled.effects_hash == base.effects_hash
    assert assert_checkpoint_identity(_stamped(base), respelled, force_new_vfs=False) is True


def test_none_versus_value_is_a_change_for_both_nullable_hashes(tmp_path: Path) -> None:
    base = _compile(_pack(tmp_path, "base"))
    assert base.effects_hash is not None and base.get_level(LEVEL).items_appearance_hash is not None
    checkpoint = _stamped(base)

    effects_vanished = dict(checkpoint)
    effects_vanished["effects_hash"] = None
    with pytest.raises(ValueError, match="effects_hash mismatch: checkpoint=None, current="):
        assert_checkpoint_identity(effects_vanished, base, force_new_vfs=False)

    rules_vanished = dict(checkpoint)
    rules_vanished["items_appearance_hash"] = None
    with pytest.raises(ValueError, match="items_appearance_hash mismatch: checkpoint=None, current="):
        assert_checkpoint_identity(rules_vanished, base, force_new_vfs=False)

    # A pack without effects or spawn rules stamps None for both and resumes against itself.
    bare = UniverseCompiler().compile(REPO / "configs" / "test" / "token_transfer_a", primary_level="L0_transfer", use_cache=False)
    assert bare.effects_hash is None and bare.get_level("L0_transfer").items_appearance_hash is None
    bare_checkpoint = _stamped(bare)
    assert bare_checkpoint["effects_hash"] is None and bare_checkpoint["items_appearance_hash"] is None
    assert assert_checkpoint_identity(bare_checkpoint, bare, force_new_vfs=False) is True


def test_both_hashes_survive_the_artifact_round_trip(tmp_path: Path) -> None:
    base = _compile(_pack(tmp_path, "base"))
    restored = CompiledUniverse.from_dict(base.to_dict())
    assert restored.effects_hash == base.effects_hash
    assert restored.get_level(LEVEL).items_appearance_hash == base.get_level(LEVEL).items_appearance_hash
