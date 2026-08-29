"""The compile cache must return the projection of the level you asked for.

WS-1(a). Before the fix, ``.compiled/universe.msgpack`` is one artifact per config
pack with no level in its name and no level in its cache key: the fingerprint is
``config_hash`` + ``provenance_id`` + ``config_mtime``, none of which encode which
level was requested. Whichever level compiled last is served to every subsequent
request.

Measured against the poisoned artifact that shipped in the working tree, four of
the five ``default_curriculum`` levels were served L0_0_minimal's universe:

    L0_0_minimal              9ddda35aebfb2357  ==  fresh   OK
    L0_5_dual_resource        9ddda35aebfb2357  !=  65ba046e134a2e90
    L1_full_observability     9ddda35aebfb2357  !=  65ba046e134a2e90
    L2_partial_observability  9ddda35aebfb2357  !=  5f9d74fb587df5ed
    L3_temporal_mechanics     9ddda35aebfb2357  !=  174a1760fbc37b1b

Note L0_5 and L1 share a fresh ``vfs_hash``. That collision is why the identity
guard has to compare ``primary_level`` and cannot rely on content hashes (D5/H1).

Every test here runs with ``use_cache=True`` deliberately. The old cache "hits"
were wrong answers, not a speed feature.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/default_curriculum")
LEVELS = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)

# The identity of a compiled projection, as far as a caller can observe it.
IDENTITY_HASHES = (
    "observation_schema_hash",
    "variable_schema_hash",
    "action_schema_hash",
    "transition_graph_hash",
    "vfs_hash",
    "drive_hash",
)


def _pack(tmp_path: Path, name: str = "pack") -> Path:
    """Copy the shipped pack somewhere writable, without its compile cache."""
    target = tmp_path / name
    shutil.copytree(PACK, target)
    shutil.rmtree(target / ".compiled", ignore_errors=True)
    return target


def test_cache_returns_requested_level_projection_for_every_level(tmp_path: Path) -> None:
    """A cache hit must be the same projection a fresh compile would produce.

    Asserts the invariant rather than hash literals: the cached projection's
    identity must equal that of the level actually requested. Compiling every
    level in sequence against a shared cache directory is what makes this bite —
    each compile leaves an artifact the next request can wrongly hit.
    """
    cached_pack = _pack(tmp_path, "cached")
    fresh_pack = _pack(tmp_path, "fresh")
    compiler = UniverseCompiler()

    truth = {level: compiler.compile(fresh_pack, primary_level=level, use_cache=False) for level in LEVELS}

    wrong: list[str] = []
    for level in LEVELS:
        got = compiler.compile(cached_pack, primary_level=level, use_cache=True)
        expected = truth[level]

        if got.metadata.primary_level != level:
            wrong.append(f"{level}: metadata.primary_level == {got.metadata.primary_level!r}")
            continue
        for field in IDENTITY_HASHES:
            if getattr(got, field) != getattr(expected, field):
                wrong.append(f"{level}: {field} {getattr(got, field)!r} != fresh {getattr(expected, field)!r}")
        if got.token_spec.total_dims != expected.token_spec.total_dims:
            wrong.append(f"{level}: observation_dim {got.token_spec.total_dims} != {expected.token_spec.total_dims}")

    assert not wrong, "cache served another level's projection:\n  " + "\n  ".join(wrong)

    # One artifact per level, each naming its own identity.
    artifacts = sorted(p.name for p in (cached_pack / ".compiled").glob("*.msgpack"))
    assert artifacts == sorted(f"universe-{level}.msgpack" for level in LEVELS), f"cache directory does not key on level: {artifacts}"


def test_yaml_edit_reaches_runtime_and_survives_a_level_switch(tmp_path: Path) -> None:
    """Config-in / behaviour-out, with an intervening compile of a different level.

    Two legs. The runtime leg is the control: it proves the edited YAML value
    actually reaches the compiled observation activity. The identity leg is the
    one that fails before the fix.

    The intervening compile is what makes this bite. Without it the changed
    ``config_hash`` alone invalidates the cache and masks the defect.
    """
    pack = _pack(tmp_path)
    compiler = UniverseCompiler()

    curriculum_path = pack / "levels" / "L2_partial_observability" / "curriculum.yaml"
    before = compiler.compile(pack, primary_level="L2_partial_observability", use_cache=True)

    doc = yaml.safe_load(curriculum_path.read_text())
    block = doc["curriculum"] if "curriculum" in doc else doc
    assert block["active_vision"] == "partial", f"fixture assumption broken: active_vision == {block['active_vision']!r}"
    block["active_vision"] = "global"
    curriculum_path.write_text(yaml.safe_dump(doc, sort_keys=False))

    # Compile a DIFFERENT level in between, so a level-blind cache is poisoned.
    compiler.compile(pack, primary_level="L0_0_minimal", use_cache=True)

    after = compiler.compile(pack, primary_level="L2_partial_observability", use_cache=True)

    assert (
        after.metadata.primary_level == "L2_partial_observability"
    ), f"identity leg: got {after.metadata.primary_level!r} after compiling L0 in between"
    # `curriculum_hash`, not `vfs_hash`: since the unit-3 token cut one pack has ONE
    # TokenSpec, and `active_vision` changes the visibility RADIUS handed to the
    # substrate, never the observation layout — so the VFS ABI is deliberately identical
    # across L1 and L2. `curriculum_hash` is what an `active_vision` edit moves, and it
    # is the projection field this leg is actually about.
    assert after.curriculum_hash != before.curriculum_hash, "runtime leg: editing active_vision did not reach the compiled projection"
    assert after.get_level("L2_partial_observability").curriculum.curriculum.active_vision == "global"


def test_artifact_stamped_with_a_foreign_primary_level_is_fatal(tmp_path: Path) -> None:
    """A mislabelled artifact must raise, not be swallowed as a cache miss.

    Pins the guard's PLACEMENT, not merely its existence. The cache read is
    wrapped in a broad ``except Exception`` that downgrades failures to a warning
    and recompiles; a guard left inside that block ships inert and silently
    passes this file's other tests.
    """
    pack = _pack(tmp_path)
    compiler = UniverseCompiler()

    compiler.compile(pack, primary_level="L0_0_minimal", use_cache=True)

    cache_dir = pack / ".compiled"
    l0_artifact = cache_dir / "universe-L0_0_minimal.msgpack"
    assert l0_artifact.exists(), f"expected per-level artifact, found {[p.name for p in cache_dir.iterdir()]}"

    # Masquerade L0's artifact as L1's.
    shutil.copyfile(l0_artifact, cache_dir / "universe-L1_full_observability.msgpack")

    with pytest.raises(ValueError, match="primary_level"):
        compiler.compile(pack, primary_level="L1_full_observability", use_cache=True)


def test_checkpoint_is_stamped_with_the_requested_levels_identity(tmp_path: Path) -> None:
    """The bytes-out expression of the defect.

    A cache hit stamps checkpoint provenance, so a level-blind cache does not
    merely return the wrong object — it writes the wrong identity into every
    artifact produced by that run.
    """
    from townlet.training.checkpoint_utils import attach_universe_metadata

    pack = _pack(tmp_path)
    compiler = UniverseCompiler()

    compiler.compile(pack, primary_level="L0_0_minimal", use_cache=True)
    universe = compiler.compile(pack, primary_level="L1_full_observability", use_cache=True)

    checkpoint: dict = {}
    attach_universe_metadata(checkpoint, universe)

    assert (
        checkpoint["primary_level"] == "L1_full_observability"
    ), f"checkpoint stamped with {checkpoint.get('primary_level')!r} for an L1 run"
