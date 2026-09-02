"""TokenSetQNetwork — the token-native Q-network (token-obs spec §4; unit 3 Task 9).

Pins the load-bearing contracts:
- per-type projection encoders in an ``nn.ModuleDict`` keyed by token type NAME;
  capacity-0 types get no encoder (the ModuleDict key set IS the live roster);
- learned per-type embedding added post-projection;
- ONE mixed pooled set; aggregator ``mean`` | ``attention`` (explicit QKV +
  ``F.scaled_dot_product_attention`` — never ``nn.MultiheadAttention``);
- output-side masking: exact-zero contribution AND exact-zero gradient for absent
  tokens, per aggregator type (the grad-through tests);
- the all-empty unmask guard;
- permutation invariance re-pinned on the MIXED-TYPE set.
"""

from __future__ import annotations

import pytest
import torch
import torch.nn as nn
from torch.nn.attention import SDPBackend

from townlet.agent.network_factory import NetworkFactory
from townlet.agent.networks import TokenSetQNetwork
from townlet.config.brain_config import SetAggregatorConfig, TokenSetConfig
from townlet.universe.dto.token_spec import (
    PAYLOAD_SCHEMAS,
    TOKEN_TRANSPORT_VERSION,
    SlotBinding,
    TokenSpec,
    build_token_type,
)


def _static(count: int, type_name: str) -> tuple[SlotBinding, ...]:
    return tuple(
        SlotBinding(
            slot_index=i,
            filler_kind="static",
            filler_ref=f"{type_name}:{i}",
        )
        for i in range(count)
    )


def _dynamic(count: int, prefix: str) -> tuple[SlotBinding, ...]:
    return tuple(SlotBinding(slot_index=i, filler_kind="dynamic", filler_ref=f"{prefix}:{i}") for i in range(count))


def _type(type_name: str, bindings: tuple[SlotBinding, ...]):
    return build_token_type(
        type_name,
        bindings,
        slot_context_payloads=tuple((0.0,) * len(PAYLOAD_SCHEMAS[type_name]) for _ in bindings),
        effect_catalog_contexts=(),
    )


def make_spec(*, meters: int = 3, affordances: int = 2, items: int = 2) -> TokenSpec:
    """A mixed-type spec: self + meters + affordances + agent(0) + items."""
    return TokenSpec(
        types=(
            _type("self", _static(1, "self")),
            _type("meter", _static(meters, "meter")),
            _type("affordance", _static(affordances, "affordance")),
            _type("agent", ()),
            _type("item", _dynamic(items, "item")),
        ),
        position_rank=2,
        transport_version=TOKEN_TRANSPORT_VERSION,
    )


def make_network(spec: TokenSpec, *, aggregator: str = "mean", num_heads: int | None = None) -> TokenSetQNetwork:
    return TokenSetQNetwork(
        token_spec=spec,
        action_dim=5,
        token_embed_dim=16,
        q_head_hidden_dim=32,
        aggregator_type=aggregator,
        num_heads=num_heads,
    )


def row_layout_slices(spec: TokenSpec) -> dict[tuple[str, int], tuple[int, int]]:
    """(type_name, slot) -> (start, end) flat slice, presence at start."""
    return {(name, slot): (start, end) for name, slot, start, end in spec.row_layout()}


def make_obs(spec: TokenSpec, batch_size: int, *, present: set[tuple[str, int]], seed: int = 0) -> torch.Tensor:
    """A flat observation with the given rows present (random payloads), rest absent-zero."""
    generator = torch.Generator().manual_seed(seed)
    obs = torch.zeros(batch_size, spec.total_dims)
    for (name, slot), (start, end) in row_layout_slices(spec).items():
        if (name, slot) in present:
            obs[:, start] = 1.0
            obs[:, start + 1 : end] = torch.rand(batch_size, end - start - 1, generator=generator)
    return obs


def present_rows(spec: TokenSpec) -> set[tuple[str, int]]:
    """self + all meters + first affordance + first item present; rest absent."""
    rows = {("self", 0), ("affordance", 0), ("item", 0)}
    meter_type = spec.get_type("meter")
    assert meter_type is not None
    rows |= {("meter", i) for i in range(meter_type.capacity)}
    return rows


class TestConstruction:
    def test_moduledict_keys_are_the_live_roster(self):
        net = make_network(make_spec())
        assert set(net.encoder.encoders.keys()) == {"self", "meter", "affordance", "item"}
        assert set(net.encoder.type_embeddings.keys()) == {"self", "meter", "affordance", "item"}
        assert net.token_type_names == ("self", "meter", "affordance", "item")

    def test_capacity_zero_type_gets_no_encoder(self):
        net = make_network(make_spec())
        assert "agent" not in net.encoder.encoders

    def test_encoder_widths_match_payload_schemas(self):
        net = make_network(make_spec())
        for name, encoder in net.encoder.encoders.items():
            assert isinstance(encoder, nn.Linear)
            assert encoder.in_features == len(PAYLOAD_SCHEMAS[name])
            assert encoder.out_features == 16

    def test_compiled_assembler_buffers_are_not_checkpoint_state(self):
        net = make_network(make_spec())
        assert any(name.startswith("encoder.input_assembler.") for name, _buffer in net.named_buffers())
        assert not any(name.startswith("encoder.input_assembler.") for name in net.state_dict())

    def test_empty_roster_refuses(self):
        empty = TokenSpec(
            types=(_type("agent", ()),),
            position_rank=2,
            transport_version=TOKEN_TRANSPORT_VERSION,
        )
        with pytest.raises(ValueError, match="capacity > 0"):
            make_network(empty)

    def test_attention_requires_num_heads(self):
        with pytest.raises(ValueError, match="requires num_heads"):
            make_network(make_spec(), aggregator="attention")

    def test_mean_takes_no_num_heads(self):
        with pytest.raises(ValueError, match="takes no num_heads"):
            make_network(make_spec(), aggregator="mean", num_heads=2)

    def test_unknown_aggregator_refuses(self):
        with pytest.raises(ValueError, match="Unknown aggregator_type"):
            make_network(make_spec(), aggregator="max")

    def test_attention_head_divisibility(self):
        with pytest.raises(ValueError, match="divisible"):
            make_network(make_spec(), aggregator="attention", num_heads=3)

    def test_no_multihead_attention_module_anywhere(self):
        net = make_network(make_spec(), aggregator="attention", num_heads=4)
        assert not any(isinstance(m, nn.MultiheadAttention) for m in net.modules())

    def test_no_layer_over_concatenated_set_width(self):
        """No Linear/LayerNorm sees the concatenated set width (Global Constraints)."""
        spec = make_spec()
        n_tokens = sum(t.capacity for t in spec.types)
        set_width = n_tokens * 16
        for aggregator, heads in (("mean", None), ("attention", 4)):
            net = make_network(spec, aggregator=aggregator, num_heads=heads)
            for module in net.modules():
                if isinstance(module, nn.Linear):
                    assert module.in_features != set_width
                if isinstance(module, nn.LayerNorm):
                    assert module.normalized_shape[0] != set_width


@pytest.mark.parametrize(("aggregator", "num_heads"), [("mean", None), ("attention", 4)])
class TestForward:
    def test_forward_shape(self, aggregator, num_heads):
        spec = make_spec()
        net = make_network(spec, aggregator=aggregator, num_heads=num_heads)
        obs = make_obs(spec, 3, present=present_rows(spec))
        assert net(obs).shape == (3, 5)

    def test_wrong_width_refuses(self, aggregator, num_heads):
        spec = make_spec()
        net = make_network(spec, aggregator=aggregator, num_heads=num_heads)
        with pytest.raises(ValueError, match="Expected observations"):
            net(torch.zeros(2, spec.total_dims + 1))

    def test_absent_token_payload_contributes_exactly_zero(self, aggregator, num_heads):
        """Two observations differing only in an ABSENT row's payload produce
        byte-identical Q-values — exact-zero contribution, not approximately-zero."""
        spec = make_spec()
        net = make_network(spec, aggregator=aggregator, num_heads=num_heads)
        present = present_rows(spec)
        obs_a = make_obs(spec, 2, present=present)
        obs_b = obs_a.clone()
        # ("item", 1) is absent: garbage its payload lanes, keep presence 0.
        start, end = row_layout_slices(spec)[("item", 1)]
        obs_b[:, start + 1 : end] = 123.456
        assert torch.equal(net(obs_a), net(obs_b))

    def test_absent_token_gets_exact_zero_gradient(self, aggregator, num_heads):
        """The grad-through test: backward through the Q-values leaves EXACTLY zero
        gradient on every absent row's payload lanes, and nonzero gradient on at
        least one present row's payload."""
        spec = make_spec()
        net = make_network(spec, aggregator=aggregator, num_heads=num_heads)
        present = present_rows(spec)
        obs = make_obs(spec, 2, present=present)
        obs.requires_grad_(True)
        net(obs).sum().backward()
        assert obs.grad is not None
        slices = row_layout_slices(spec)
        for (name, slot), (start, end) in slices.items():
            if (name, slot) in present:
                continue
            payload_grad = obs.grad[:, start + 1 : end]
            assert torch.equal(payload_grad, torch.zeros_like(payload_grad)), f"absent row {name}[{slot}] leaked gradient"
        # Present rows must carry real gradient (the test would pass vacuously otherwise).
        meter_start, meter_end = slices[("meter", 0)]
        assert obs.grad[:, meter_start + 1 : meter_end].abs().sum() > 0

    def test_fully_absent_type_encoder_gets_exact_zero_weight_grad(self, aggregator, num_heads):
        """A type with no present token in the batch contributes exact-zero gradient
        to its projection encoder and type embedding."""
        spec = make_spec()
        net = make_network(spec, aggregator=aggregator, num_heads=num_heads)
        # Items entirely absent from the batch.
        present = present_rows(spec) - {("item", 0)}
        obs = make_obs(spec, 2, present=present)
        net(obs).sum().backward()
        item_encoder = net.encoder.encoders["item"]
        assert isinstance(item_encoder, nn.Linear)
        assert item_encoder.weight.grad is not None
        assert torch.equal(item_encoder.weight.grad, torch.zeros_like(item_encoder.weight.grad))
        assert item_encoder.bias.grad is not None
        assert torch.equal(item_encoder.bias.grad, torch.zeros_like(item_encoder.bias.grad))
        embedding_grad = net.encoder.type_embeddings["item"].grad
        assert embedding_grad is not None
        assert torch.equal(embedding_grad, torch.zeros_like(embedding_grad))
        # A present type's encoder DID learn something.
        meter_encoder = net.encoder.encoders["meter"]
        assert isinstance(meter_encoder, nn.Linear)
        assert meter_encoder.weight.grad is not None
        assert meter_encoder.weight.grad.abs().sum() > 0

    def test_all_empty_set_survives_the_unmask_guard(self, aggregator, num_heads):
        """A batch row with zero present tokens forwards finite (no softmax NaN) and
        pools to an exact-zero embedding."""
        spec = make_spec()
        net = make_network(spec, aggregator=aggregator, num_heads=num_heads)
        obs = torch.zeros(2, spec.total_dims)
        # Row 0 all-empty; row 1 has content (the mixed batch is the hard case).
        obs[1] = make_obs(spec, 1, present=present_rows(spec))[0]
        q_values = net(obs)
        assert torch.isfinite(q_values).all()
        pooled = net.pooled_embedding(obs)
        assert torch.equal(pooled[0], torch.zeros_like(pooled[0]))
        assert pooled[1].abs().sum() > 0

    def test_permutation_invariance_on_the_mixed_type_set(self, aggregator, num_heads):
        """Permuting whole rows (presence + payload) within each type's block leaves
        the Q-values unchanged — the set reading, re-pinned on the MIXED-TYPE set."""
        torch.manual_seed(7)
        spec = make_spec(meters=4, affordances=3, items=3)
        net = make_network(spec, aggregator=aggregator, num_heads=num_heads)
        slices = row_layout_slices(spec)
        obs = make_obs(
            spec,
            3,
            present={("self", 0), ("meter", 0), ("meter", 2), ("affordance", 1), ("item", 0), ("item", 2)},
            seed=11,
        )
        permuted = obs.clone()
        permutations = {"meter": [2, 0, 3, 1], "affordance": [1, 2, 0], "item": [2, 1, 0]}
        for type_name, order in permutations.items():
            blocks = [obs[:, slice(*slices[(type_name, s)])] for s in range(len(order))]
            for dst, src in enumerate(order):
                start, end = slices[(type_name, dst)]
                permuted[:, start:end] = blocks[src]
        torch.testing.assert_close(net(obs), net(permuted), rtol=1e-5, atol=1e-6)


class TestTokenSetConfig:
    def test_aggregator_declaration_validates_attention_heads(self):
        with pytest.raises(Exception, match="num_heads"):
            SetAggregatorConfig(type="attention")

        with pytest.raises(Exception, match="num_heads"):
            SetAggregatorConfig(type="mean", num_heads=2)

    def test_all_fields_required(self):
        with pytest.raises(Exception, match="token_embed_dim"):
            TokenSetConfig(q_head_hidden_dim=32, aggregator=SetAggregatorConfig(type="mean"))

    def test_attention_geometry_validated_at_config(self):
        with pytest.raises(ValueError, match="divisible"):
            TokenSetConfig(
                token_embed_dim=16,
                q_head_hidden_dim=32,
                aggregator=SetAggregatorConfig(type="attention", num_heads=3),
            )

    def test_architecture_type_requires_block(self):
        from townlet.config.brain_config import ArchitectureConfig

        with pytest.raises(ValueError, match="requires token_set config"):
            ArchitectureConfig(type="token_set")

    def test_architecture_dump_has_only_current_fields(self):
        """The pre-release ABI has one exact current shape, with no legacy omission."""
        from townlet.config.brain_config import ArchitectureConfig, FeedforwardConfig

        flat = ArchitectureConfig(
            type="feedforward",
            feedforward=FeedforwardConfig(hidden_layers=[8], activation="relu", dropout=0.0, layer_norm=False),
        )
        dump = flat.model_dump()
        assert dump["token_set"] is None
        assert set(dump) == {"type", "feedforward", "recurrent", "dueling", "token_set"}

        token = ArchitectureConfig(
            type="token_set",
            token_set=TokenSetConfig(
                token_embed_dim=16,
                q_head_hidden_dim=32,
                aggregator=SetAggregatorConfig(type="mean"),
            ),
        )
        assert token.model_dump()["token_set"]["token_embed_dim"] == 16

    def test_legacy_set_encoder_architecture_is_not_in_the_schema(self):
        from pydantic import ValidationError

        from townlet.config import brain_config
        from townlet.config.brain_config import ArchitectureConfig

        assert not hasattr(brain_config, "SetEncoderConfig")
        with pytest.raises(ValidationError, match="type"):
            ArchitectureConfig(type="set_encoder")

    def test_legacy_set_encoder_network_is_deleted(self):
        import townlet.agent.networks as networks

        assert not hasattr(networks, "SetEncoderQNetwork")

    def test_legacy_set_encoder_vfs_layout_is_deleted(self):
        import townlet.vfs as vfs
        import townlet.vfs.dynamic_needs as dynamic_needs

        for name in ("DynamicNeedTokenLayout", "dynamic_need_token_layout"):
            assert not hasattr(vfs, name)
            assert not hasattr(dynamic_needs, name)


class TestFactory:
    def test_build_token_set(self):
        spec = make_spec()
        config = TokenSetConfig(
            token_embed_dim=16,
            q_head_hidden_dim=32,
            aggregator=SetAggregatorConfig(type="attention", num_heads=4),
        )
        net = NetworkFactory.build_token_set(config, action_dim=6, token_spec=spec)
        assert isinstance(net, TokenSetQNetwork)
        assert net.token_type_names == ("self", "meter", "affordance", "item")
        obs = make_obs(spec, 2, present=present_rows(spec))
        assert net(obs).shape == (2, 6)


class TestReviewRound1Pins:
    """Task-9 review fix round: M1 (present-count denominator) and I2 (bitwise replay)."""

    def test_mean_divides_by_present_count_not_capacity(self):
        """One present token ⇒ pooled mean IS that token's embedding. A capacity
        denominator would scale it by 1/n_tokens (task-9 review M1)."""
        spec = make_spec()
        net = make_network(spec)
        obs = make_obs(spec, 1, present={("meter", 0)}, seed=5)
        layout = spec.compact_layout().get_type("meter")
        assert layout is not None
        dynamic_rows = obs[:, layout.start : layout.end].view(1, layout.capacity, layout.compact_row_width)
        with torch.no_grad():
            payload = net.encoder.input_assembler.expand_type("meter", dynamic_rows)[:, 0, 1:]
            expected = net.encoder.encoders["meter"](payload) + net.encoder.type_embeddings["meter"]
            pooled = net.pooled_embedding(obs)
        assert torch.allclose(pooled, expected, atol=1e-6)

    def test_attention_runs_under_the_pinned_math_backend(self, monkeypatch):
        """Spec §6 byte-exact replay: the SDPA call runs under the MATH backend
        (task-9 review I2).

        The MECHANISM is pinned, not the outcome: on this platform default dispatch
        happens to agree with MATH bitwise, so an output-equality test would pass with
        the pin deleted (re-review M8). Deleting the ``sdpa_kernel`` wrapper fails
        this test.
        """
        import townlet.agent.networks as networks_module

        entered: list[list[SDPBackend]] = []
        real_sdpa_kernel = networks_module.sdpa_kernel

        def recording_sdpa_kernel(backends, *args, **kwargs):
            entered.append(list(backends))
            return real_sdpa_kernel(backends, *args, **kwargs)

        monkeypatch.setattr(networks_module, "sdpa_kernel", recording_sdpa_kernel)

        spec = make_spec()
        net = make_network(spec, aggregator="attention", num_heads=2)
        with torch.no_grad():
            net(make_obs(spec, 3, present=present_rows(spec), seed=9))

        assert entered == [[SDPBackend.MATH]]

    def test_mean_aggregator_takes_no_sdpa_backend(self, monkeypatch):
        """The pin belongs to the attention path only — the mean path never enters it."""
        import townlet.agent.networks as networks_module

        entered: list[object] = []
        real_sdpa_kernel = networks_module.sdpa_kernel

        def recording_sdpa_kernel(backends, *args, **kwargs):
            entered.append(backends)
            return real_sdpa_kernel(backends, *args, **kwargs)

        monkeypatch.setattr(networks_module, "sdpa_kernel", recording_sdpa_kernel)

        spec = make_spec()
        net = make_network(spec)
        with torch.no_grad():
            net(make_obs(spec, 3, present=present_rows(spec), seed=9))

        assert entered == []
