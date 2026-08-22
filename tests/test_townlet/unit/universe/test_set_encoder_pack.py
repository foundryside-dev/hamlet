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


def test_pack_declares_the_mean_aggregator() -> None:
    universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)
    se = universe.brain.architecture.set_encoder
    assert se is not None and se.aggregator.type == "mean"


def test_attention_level_overrides_the_aggregator_and_forks_the_brain(tmp_path) -> None:
    """L1_attention declares attention via a level brain.yaml — the override mechanism
    carrying a genuinely different mind (PDR-0027 + PDR-0109 in one pack)."""
    compiler = UniverseCompiler()
    mean_universe = compiler.compile(PACK, primary_level=LEVEL, use_cache=False)
    attention_universe = compiler.compile(PACK, primary_level="L1_attention", use_cache=False)

    se = attention_universe.brain.architecture.set_encoder
    assert se is not None
    assert se.aggregator.type == "attention"
    assert se.aggregator.num_heads == 4
    assert attention_universe.brain_hash != mean_universe.brain_hash
    assert attention_universe.brain_forked is True
