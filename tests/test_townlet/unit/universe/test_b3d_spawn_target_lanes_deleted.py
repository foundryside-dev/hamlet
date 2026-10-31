"""The affordance identity's spawn-target lanes are deleted (phase B3d).

`spawn_target_index_zero` could never be set: a constant spawn target refuses at compile
([EFFECT-SPAWN-TARGET], S1), so an affordance's spawn_effect can only name `target`. A
one-value one-hot carries nothing beyond the `spawn_effect_*` write source, so the whole
axis leaves `SpawnedEffectIdentity` and the affordance payload. The width moves by
`census["affordance"] × EFFECT_SUMMARY_K × 2` lanes on every pack; no checkpoint exists.
"""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from townlet.effects import affordance_identity
from townlet.effects.affordance_identity import SpawnedEffectIdentity
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto.token_spec import (
    AFFORDANCE_SIGNATURE_WIDTH,
    PAYLOAD_SCHEMAS,
    SPAWN_EFFECT_IDENTITY_FEATURES,
)
from townlet.universe.token_hashes import compute_token_type_schema_hash

REPO = Path(__file__).resolve().parents[4]
TRANSFER_PACKS = (
    (REPO / "configs" / "default_curriculum", "L1_full_observability"),
    (REPO / "configs" / "aspatial_test", "L0"),
    (REPO / "configs" / "differential" / "div003_cubic_partial", "L2_partial_observability"),
    (REPO / "configs" / "test" / "token_transfer_a", "L0_transfer"),
    (REPO / "configs" / "test" / "token_transfer_b", "L0_transfer"),
    (REPO / "configs" / "test" / "token_transfer_c", "L0_transfer"),
)


def test_no_spawn_target_lane_in_the_affordance_payload() -> None:
    assert not any(feature.startswith("spawn_target") for feature in SPAWN_EFFECT_IDENTITY_FEATURES)
    assert not any("spawn_target" in feature for feature in PAYLOAD_SCHEMAS["affordance"])
    assert SPAWN_EFFECT_IDENTITY_FEATURES[:2] == ("spawn_intensity", "spawn_duration")


def test_spawned_effect_identity_has_no_target_axis() -> None:
    assert [field.name for field in fields(SpawnedEffectIdentity)] == ["intensity", "duration", "scope", "reapply_policy", "observable"]
    assert not hasattr(affordance_identity, "SPAWN_EFFECT_TARGETS")
    assert not hasattr(affordance_identity, "SpawnEffectTarget")


def test_affordance_signature_width_follows_the_payload_schema() -> None:
    assert AFFORDANCE_SIGNATURE_WIDTH == sum(
        1 for feature in PAYLOAD_SCHEMAS["affordance"] if not feature.startswith(("position_", "egocentric_"))
    )


def test_the_transfer_contract_is_one_hash_across_substrates() -> None:
    """The type schema, not the width, is the transfer contract (CLAUDE.md carries the value)."""
    hashes = set()
    for pack, level in TRANSFER_PACKS:
        spec = UniverseCompiler().compile(pack, primary_level=level, use_cache=False).get_level(level).token_spec
        hashes.add(compute_token_type_schema_hash(spec))
    assert len(hashes) == 1, hashes
