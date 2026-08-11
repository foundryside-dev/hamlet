"""WS-1 task 4: the four per-level content hashes are stamped AND compared.

`curriculum_hash`, `bars_hash`, `affordances_hash` and `training_hash` have been computed,
serialized and round-tripped through the compile cache since the compiler was written — and
**compared against a checkpoint by nobody**. A level's bars, affordances, curriculum or
training config could change underneath a checkpoint and resume would accept it silently.
That is breach 2 of 3 on the Provenance-integrity guardrail (`PDR-0008`).

**SEVEN tests, not six** (plan §0.3 correction 12): four config-edit tests carrying the full
six-leg template, two `brain_hash` semantics tests of two legs each, and one cross-level
collision test. The six-leg template applies to the config-edit tests only — padding legs onto
the `brain_hash` tests gives them no meaning.

The six legs, in order: **runtime** (the edit changes behaviour, so the config is not inert)
→ **blindness witness** (the hashes that exist today do NOT move, so nothing else catches it)
→ **mover** (the target hash DOES move) → **stamp** (it reaches the checkpoint) → **negative
control** (an unedited pack still resumes) → **guard** (the edit is rejected, by name).

`brain_hash` is fixed here too: it hashed `brain.yaml` RAW, so a `training.yaml` override that
changes the network that actually trains left it byte-identical.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import torch
import yaml

from townlet.config.brain_config import apply_training_overrides, compute_brain_hash
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.training.checkpoint_utils import assert_checkpoint_dimensions, attach_universe_metadata
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

SOURCE_PACK = Path("configs/default_curriculum")
L0 = "L0_0_minimal"
L1 = "L1_full_observability"
L0_5 = "L0_5_dual_resource"
L3 = "L3_temporal_mechanics"


def _pack(tmp_path: Path, name: str = "pack") -> Path:
    """Copy the shipped pack, stripping every compiled artifact.

    Cache validity keys on config hash + provenance, and provenance uses `git rev-parse HEAD`
    rather than dirty state, so a stale artifact would be judged valid and report the OLD hash.
    """
    dest = tmp_path / name
    shutil.copytree(SOURCE_PACK, dest)
    for compiled in dest.rglob(".compiled"):
        shutil.rmtree(compiled, ignore_errors=True)
    for artifact in dest.rglob("*.msgpack"):
        artifact.unlink()
    return dest


def _edit(pack: Path, level: str, filename: str, mutator: Callable[[dict], None]) -> None:
    path = pack / "levels" / level / filename
    data = yaml.safe_load(path.read_text())
    mutator(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def _compile(pack: Path, level: str) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _meter(data: dict, name: str) -> dict:
    return next(m for m in data["bars"]["meters"] if m["name"] == name)


def _affordance(data: dict, name: str) -> dict:
    return next(a for a in data["affordances"]["affordances"] if a["name"] == name)


# The hashes that exist today and are already compared. A content edit that moves NONE of
# these is exactly the blindness this task closes.
#
# NOTE: these equalities are EXPECTED TO FLIP when WS-1(ii) widens hash coverage. That is the
# hash coverage improving, not a regression — do not "fix" this by deleting the witness.
_PRE_EXISTING = ("vfs_hash", "observation_schema_hash", "transition_graph_hash", "action_schema_hash")


def _blindness_witness(base: CompiledUniverse, mutated: CompiledUniverse) -> None:
    for field in _PRE_EXISTING:
        assert getattr(base, field) == getattr(mutated, field), f"{field} moved — this edit is no longer a blindness witness"


def _six_legs(
    tmp_path: Path,
    level: str,
    filename: str,
    mutator: Callable[[dict], None],
    hash_field: str,
    runtime_leg: Callable[[VectorizedHamletEnv, VectorizedHamletEnv], None] | None,
) -> None:
    base_pack = _pack(tmp_path, "base")
    mut_pack = _pack(tmp_path, "mutated")
    _edit(mut_pack, level, filename, mutator)

    base = _compile(base_pack, level)
    mutated = _compile(mut_pack, level)

    # LEG 1 — runtime. The edit changes observable behaviour, so the config is not inert and
    # the hash is guarding something real.
    if runtime_leg is not None:
        base_env = VectorizedHamletEnv(universe=base, level_name=level, num_agents=1, device=torch.device("cpu"))
        mut_env = VectorizedHamletEnv(universe=mutated, level_name=level, num_agents=1, device=torch.device("cpu"))
        base_env.reset()
        mut_env.reset()
        runtime_leg(base_env, mut_env)

    # LEG 2 — blindness witness. Nothing that existed before this task catches it.
    _blindness_witness(base, mutated)

    # LEG 3 — mover. The target hash does move.
    assert getattr(base, hash_field) is not None, f"{hash_field} is not stamped at all"
    assert getattr(base, hash_field) != getattr(mutated, hash_field), f"{hash_field} did not move"

    # LEG 4 — stamp. It reaches the checkpoint.
    checkpoint: dict = {}
    attach_universe_metadata(checkpoint, base)
    assert checkpoint[hash_field] == getattr(base, hash_field)

    # LEG 5 — negative control. An unedited pack still resumes.
    assert_checkpoint_dimensions(checkpoint, base)

    # LEG 6 — guard. The edited universe is rejected, and the message names the field.
    with pytest.raises(ValueError, match=f"{hash_field} mismatch"):
        assert_checkpoint_dimensions(checkpoint, mutated)


def test_bars_edit_is_caught(tmp_path: Path) -> None:
    """`energy.initial 1.0 -> 0.5` on L1. Pinned BECAUSE it is vfs-invisible."""

    def runtime(base_env: VectorizedHamletEnv, mut_env: VectorizedHamletEnv) -> None:
        idx = base_env.meter_name_to_index["energy"]
        assert base_env.meters[0, idx].item() == pytest.approx(1.0)
        assert mut_env.meters[0, idx].item() == pytest.approx(0.5)

    _six_legs(tmp_path, L1, "bars.yaml", lambda d: _meter(d, "energy").__setitem__("initial", 0.5), "bars_hash", runtime)


def test_affordances_edit_is_caught(tmp_path: Path) -> None:
    """`EAT` money cost 5.0 -> 50.0 on L1.

    L1 declares `money.initial: 0.0`, so seed money before asserting affordability — otherwise
    both sides are all-False and the leg is vacuous. Since WS-1(e) money survives the tick, so
    a plain `can_afford` assertion is the discriminating runtime leg (plan §0.3 correction 16).
    """

    def mutate(data: dict) -> None:
        costs = _affordance(data, "EAT")["costs"]
        assert costs["money"] == 5.0, f"fixture drifted: EAT money cost is {costs['money']}"
        costs["money"] = 50.0

    def runtime(base_env: VectorizedHamletEnv, mut_env: VectorizedHamletEnv) -> None:
        for env in (base_env, mut_env):
            env.meters[:, env.meter_name_to_index["money"]] = 22.5
        assert bool(base_env.affordance_engine.can_afford("EAT", base_env.meters)[0].item()) is True
        assert bool(mut_env.affordance_engine.can_afford("EAT", mut_env.meters)[0].item()) is False

    _six_legs(tmp_path, L1, "affordances.yaml", mutate, "affordances_hash", runtime)


def test_training_edit_is_caught(tmp_path: Path) -> None:
    """Drop `DOCTOR` from L1 `enabled_affordances`.

    NOT a q_learning edit — that moves `brain_hash` too and makes the message ambiguous.

    Plan §0.3 correction 17 claimed this edit is "compile-time inert" and specified no runtime
    leg. **That correction was wrong**, measured 2026-08-12: the edit deterministically removes
    DOCTOR from the deployed affordance set (14 → 13, stable across trials). The runtime leg is
    restored, so this test is not structurally blind to `enabled_affordances` becoming a dead
    config key — the exact inert-surface class WS-1 keeps finding.

    The affordance SET is the right witness; the observation tensor and action mask are not.
    L1 declares `randomize_affordances: true`, so those differ run to run even base-vs-base.
    """

    def mutate(data: dict) -> None:
        enabled = data["training"]["enabled_affordances"]
        assert "DOCTOR" in enabled, "fixture drifted: DOCTOR is not in enabled_affordances"
        enabled.remove("DOCTOR")

    def runtime(base_env: VectorizedHamletEnv, mut_env: VectorizedHamletEnv) -> None:
        assert "DOCTOR" in base_env.affordances
        assert "DOCTOR" not in mut_env.affordances
        assert len(mut_env.affordances) == len(base_env.affordances) - 1

    _six_legs(tmp_path, L1, "training.yaml", mutate, "training_hash", runtime)


def test_curriculum_edit_is_caught(tmp_path: Path) -> None:
    """`day_length 24 -> 12` on **L3**. L1 has `active_temporal: false`, so the edit is
    runtime-inert there and the test would pin nothing."""

    def runtime(base_env: VectorizedHamletEnv, mut_env: VectorizedHamletEnv) -> None:
        assert base_env.day_length == 24
        assert mut_env.day_length == 12

    _six_legs(tmp_path, L3, "curriculum.yaml", lambda d: d["curriculum"].__setitem__("day_length", 12), "curriculum_hash", runtime)


def test_brain_hash_covers_the_effective_training_config(tmp_path: Path) -> None:
    """`brain_hash` is the hash of the EFFECTIVE brain config, not of `brain.yaml`.

    Authored against **L0_0_minimal** deliberately: it is the only `default_curriculum` level
    whose `training.yaml` actually overrides `brain.yaml` (`use_double_dqn: false`,
    `target_update_frequency: 500` against `true`/`1000`). On L0_5/L1/L2/L3 the shipped
    overrides are no-ops, so this assertion is vacuously green there. **Do not parametrize
    this over levels and do not "harmonize" it onto L1** — it silently stops discriminating.
    """
    universe = _compile(_pack(tmp_path), L0)
    level = universe.get_level(L0)

    # Vacuity guard: the overrides must actually change something, or leg 1 proves nothing.
    effective = apply_training_overrides(universe.brain, level.training)
    assert effective != universe.brain, "L0_0 no longer overrides brain.yaml — this test is now vacuous"

    # LEG 1 — the discriminating one. It pins the INPUT (effective, not raw) and the FUNCTION
    # (compute_brain_hash, not the compiler's _compute_pydantic_hash) simultaneously.
    assert universe.brain_hash == compute_brain_hash(effective)

    # LEG 2 — passes even if only the training_hash half shipped. Keep leg 1.
    assert universe.brain_hash != compute_brain_hash(universe.brain)


def test_brain_hash_follows_the_primary_level(tmp_path: Path) -> None:
    """`brain_hash` is the effective config of the level the universe was COMPILED AT.

    Sibling to the test above, and it exists because that one cannot cash this claim: it
    compiles only L0_0, which is also the level `next(iter(raw.levels))` yields. A wrong-level
    bug — reading the overrides from the first level rather than the primary one — is therefore
    invisible to it, and was measured to leave the full suite green.

    L0_0 is the only `default_curriculum` level whose `training.yaml` overrides `brain.yaml`,
    so L0_0 and the rest MUST land on different hashes. If a future edit makes every level's
    overrides identical, the inequality below fails loudly rather than silently un-pinning.
    """
    pack = _pack(tmp_path)
    hashes = {}
    for level in (L0, L0_5, L1, L3):
        universe = _compile(pack, level)
        expected = compute_brain_hash(apply_training_overrides(universe.brain, universe.get_level(level).training))
        assert universe.brain_hash == expected, f"{level}: brain_hash is not that level's effective config"
        hashes[level] = universe.brain_hash

    assert hashes[L0] != hashes[L1], "L0_0 and L1 no longer differ — this test can no longer detect a wrong-level hash"


def test_overridden_brain_yaml_value_does_not_block_resume(tmp_path: Path) -> None:
    """A `brain.yaml` edit that the level's `training.yaml` fully overrides is a NO-OP.

    Pins the absence of the false positive: before this task, editing an overridden
    `brain.yaml` value raised `brain_hash mismatch` on a run that was bit-identical.
    """
    base_pack = _pack(tmp_path, "base")
    mut_pack = _pack(tmp_path, "mutated")

    brain_path = mut_pack / "brain.yaml"
    data = yaml.safe_load(brain_path.read_text())
    overridden = data["q_learning"]["target_update_frequency"]
    assert overridden == 1000, f"fixture drifted: brain.yaml target_update_frequency is {overridden}"
    data["q_learning"]["target_update_frequency"] = 777
    brain_path.write_text(yaml.safe_dump(data, sort_keys=False))

    # L0_0's training.yaml pins target_update_frequency to 500, overriding both values.
    base = _compile(base_pack, L0)
    mutated = _compile(mut_pack, L0)
    assert base.brain_hash == mutated.brain_hash, "an overridden brain.yaml value still moved brain_hash"

    checkpoint: dict = {}
    attach_universe_metadata(checkpoint, base)
    assert_checkpoint_dimensions(checkpoint, mutated)


def test_two_levels_collide_on_almost_every_identity_field(tmp_path: Path) -> None:
    """D5's documentation half: why `primary_level` has to be stamped at all.

    `L0_5_dual_resource` and `L1_full_observability` are indistinguishable on nearly every
    identity field the system computes. `primary_level` (stamped in task 2) is what separates
    them.

    **This test does NOT assert rejection.** The comparison that rejects a cross-level resume
    is `assert_checkpoint_identity`, which task 5 introduces — it does not exist yet (its only
    mention in the repo today is a comment in `checkpoint_utils.py`). Task 5 owns that leg.

    `training_hash` is the one content hash that DOES differ, and only because
    `run_metadata.output_subdir` is a different string — not because the training config
    differs in any way that affects learning. L0_5 and L1 `training.yaml` are otherwise
    byte-identical.
    """
    pack = _pack(tmp_path)
    a = _compile(pack, L0_5)
    b = _compile(pack, L1)

    for field in ("curriculum_hash", "bars_hash", "affordances_hash"):
        assert getattr(a, field) == getattr(b, field), f"{field} unexpectedly differs — the collision this documents has changed"
    for field in ("vfs_hash", "drive_hash", "brain_hash", "observation_schema_hash", "transition_graph_hash"):
        assert getattr(a, field) == getattr(b, field), f"{field} unexpectedly differs"

    assert a.training_hash != b.training_hash, "training_hash no longer differs — output_subdir was the only separator"
    assert a.metadata.primary_level == L0_5
    assert b.metadata.primary_level == L1

    checkpoint: dict = {}
    attach_universe_metadata(checkpoint, a)
    assert checkpoint["primary_level"] == L0_5
