"""The committed set_encoder pack compiles and exposes the token field (hamlet-fa6bb6da4a)."""

from __future__ import annotations

from pathlib import Path

from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/test/set_encoder_smoke")
LEVEL = "L0_test"


def test_set_encoder_pack_compiles_with_token_field() -> None:
    universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)

    assert universe.brain.architecture.type == "set_encoder"
    se = universe.brain.architecture.set_encoder
    assert se is not None and se.token_field_name == "need_tokens"

    field = universe.observation_spec.get_field_by_name("need_tokens")
    assert field.dims == se.max_tokens * se.token_dim == 12
