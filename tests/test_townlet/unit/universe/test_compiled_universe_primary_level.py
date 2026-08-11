"""``CompiledUniverse.from_dict`` must resolve its primary level by name.

WS-1(a), trap 2. Before the fix, ``from_dict`` reconstructs the top-level
projection by SCANNING ``all_levels`` for the first level whose
``(transition_graph_hash, vfs_hash, action_schema_hash)`` triple matches the
payload, and takes that level's bars/affordances/drive.

That is not sound by construction, it is sound by luck: ``L0_5_dual_resource``
and ``L1_full_observability`` genuinely collide on all three hashes in the
shipped pack (measured — both are ``65ba046e134a2e90``). Whichever the dict
iteration reaches first wins, with no raise.

This defect survives the filename fix on its own, so it needs its own pin.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/default_curriculum")


def _compile(tmp_path: Path, level: str) -> CompiledUniverse:
    target = tmp_path / "pack"
    if not target.exists():
        shutil.copytree(PACK, target)
        shutil.rmtree(target / ".compiled", ignore_errors=True)
    return UniverseCompiler().compile(target, primary_level=level, use_cache=False)


def test_the_collision_this_guard_exists_for_is_real(tmp_path: Path) -> None:
    """Vacuity guard: if L0_5 and L1 ever stop colliding, the pin below is moot.

    Kept as a live assertion rather than a comment so that a future widening of
    hash coverage (WS-1(ii)) turns this red and forces a decision, instead of
    silently making the guard untested.
    """
    a = _compile(tmp_path, "L0_5_dual_resource")
    b = _compile(tmp_path, "L1_full_observability")

    assert a.vfs_hash == b.vfs_hash
    assert a.transition_graph_hash == b.transition_graph_hash
    assert a.action_schema_hash == b.action_schema_hash
    assert a.metadata.primary_level != b.metadata.primary_level, "primary_level is the ONLY field separating these two projections"


def test_from_dict_round_trips_the_declared_primary_level(tmp_path: Path) -> None:
    """The positive companion: a well-formed payload restores its own level."""
    universe = _compile(tmp_path, "L1_full_observability")

    restored = CompiledUniverse.from_dict(universe.to_dict())

    assert restored.metadata.primary_level == "L1_full_observability"
    assert restored.vfs_hash == universe.vfs_hash
    assert restored.transition_graph_hash == universe.transition_graph_hash


def test_from_dict_rejects_a_payload_whose_declared_primary_level_is_absent(tmp_path: Path) -> None:
    """Removing the declared level must raise, not silently reconstruct a sibling.

    Before the fix this does not raise at all: the hash-triple scan finds
    ``L0_5_dual_resource``, which collides with L1 on every scanned field, and
    rebuilds the projection from the wrong level's bars.
    """
    universe = _compile(tmp_path, "L1_full_observability")
    payload = universe.to_dict()

    removed = payload["all_levels"].pop("L1_full_observability", None)
    assert removed is not None, "fixture assumption broken: primary level not present in all_levels"
    assert "L0_5_dual_resource" in payload["all_levels"], "the colliding sibling must remain, or this test proves nothing"

    with pytest.raises(ValueError, match="primary_level"):
        CompiledUniverse.from_dict(payload)


def test_metadata_for_level_reprojects_primary_level(tmp_path: Path) -> None:
    """``metadata_for_level`` must realign primary_level with the other eight fields.

    Found by adversarial verification of the WS-1(a) fix, and missed by it: this is
    the FIFTH UniverseMetadata construction site (via ``dataclasses.replace``), and
    the only one that does not go through ``UniverseMetadata(...)`` directly, so a
    grep for the constructor does not find it.

    It re-projects meter_count, meter_names, meter_name_to_index, affordance_count,
    affordance_ids, affordance_id_to_index, action_count, observation_dim and
    ticks_per_day onto the requested level. Leaving primary_level pointing at the
    COMPILED level made the returned object internally inconsistent — and since
    VectorizedHamletEnv.__init__ does ``self.metadata = universe.metadata_for_level(
    level_name)``, a live env built at level B from a universe compiled at level A
    carried A's identity.

    Reachable through the documented multi-level API (``create_environment`` /
    ``from_universe``), which is the entire reason ``all_levels`` exists.
    """
    universe = _compile(tmp_path, "L0_0_minimal")

    for level in ("L0_0_minimal", "L0_5_dual_resource", "L1_full_observability"):
        projected = universe.metadata_for_level(level)
        assert projected.primary_level == level, (
            f"metadata_for_level({level!r}) reports primary_level={projected.primary_level!r} — "
            "the level the universe was compiled at, not the one requested"
        )
