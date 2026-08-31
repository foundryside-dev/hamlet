"""The committed token_set pack compiles and drives the token-native brain (hamlet-fa6bb6da4a).

The pack was a `set_encoder` exerciser until the unit-3 cut; `set_encoder` sliced a single
flattened token FIELD out of the compiled ObservationSpec, which no longer exists. It now
declares `token_set`, which consumes the compiled TokenSpec directly.
"""

from __future__ import annotations

from pathlib import Path

from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/test/set_encoder_smoke")
LEVEL = "L0_test"


def test_pack_drives_the_token_set_architecture() -> None:
    universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)

    assert universe.brain.architecture.type == "token_set"
    token_set = universe.brain.architecture.token_set
    assert token_set is not None
    # The roster is COMPILED, never authored: nothing in the brain names a token type
    # or a capacity.
    assert not hasattr(token_set, "token_field_name")
    token_spec = universe.get_level(LEVEL).token_spec
    assert token_spec.total_dims > 0
    # This pack is the live `variable_element` exerciser — it authors exposed variables.
    assert token_spec.get_type("variable_element").capacity > 0


def test_pack_declares_the_mean_aggregator() -> None:
    universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)
    token_set = universe.brain.architecture.token_set
    assert token_set is not None and token_set.aggregator.type == "mean"


def test_attention_level_overrides_the_aggregator_and_forks_the_brain() -> None:
    """L1_attention declares attention via a level brain.yaml — the override mechanism
    carrying a genuinely different mind (PDR-0027 + PDR-0109 in one pack)."""
    compiler = UniverseCompiler()
    mean_universe = compiler.compile(PACK, primary_level=LEVEL, use_cache=False)
    attention_universe = compiler.compile(PACK, primary_level="L1_attention", use_cache=False)

    token_set = attention_universe.brain.architecture.token_set
    assert token_set is not None
    assert token_set.aggregator.type == "attention"
    assert token_set.aggregator.num_heads == 4
    assert attention_universe.brain_hash != mean_universe.brain_hash
    assert attention_universe.brain_forked is True
