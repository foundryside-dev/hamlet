"""Token-net training-dynamical diagnostics (token-obs spec §3b / §6; unit 3 Task 9).

Recorded metrics riding the net — per-type encoder grad norms, the cold-token
injection hook, presence-flip counting and conditioning (TD-error / intrinsic
reward vs flips), pooled-embedding norm, online-vs-target cosine. The probe
EXPERIMENTS (flat-vs-token A/B etc.) are unit-4/5 scope and not tested here.
"""

from __future__ import annotations

import pytest
import torch

from townlet.agent.networks import TokenSetQNetwork
from townlet.agent.token_diagnostics import (
    cold_token_injection,
    condition_on_presence_flips,
    online_target_cosine,
    per_type_encoder_grad_norms,
    pooled_embedding_norm,
    presence_flip_count,
    token_diagnostic_metrics,
)
from townlet.universe.dto.token_spec import PAYLOAD_SCHEMAS, TOKEN_TRANSPORT_VERSION, SlotBinding, TokenSpec, build_token_type


def _static(count: int, prefix: str) -> tuple[SlotBinding, ...]:
    return tuple(SlotBinding(slot_index=i, filler_kind="static", filler_ref=f"{prefix}:{i}") for i in range(count))


def _dynamic(count: int, prefix: str) -> tuple[SlotBinding, ...]:
    return tuple(SlotBinding(slot_index=i, filler_kind="dynamic", filler_ref=f"{prefix}:{i}") for i in range(count))


def _type(type_name: str, bindings: tuple[SlotBinding, ...]):
    return build_token_type(
        type_name,
        bindings,
        slot_context_payloads=tuple((0.0,) * len(PAYLOAD_SCHEMAS[type_name]) for _ in bindings),
        effect_catalog_contexts=(),
    )


@pytest.fixture()
def spec() -> TokenSpec:
    return TokenSpec(
        types=(
            _type("self", _static(1, "self")),
            _type("meter", _static(2, "meter")),
            _type("item", _dynamic(2, "item")),
        ),
        position_rank=2,
        transport_version=TOKEN_TRANSPORT_VERSION,
    )


@pytest.fixture()
def net(spec: TokenSpec) -> TokenSetQNetwork:
    torch.manual_seed(13)
    return TokenSetQNetwork(
        token_spec=spec,
        action_dim=4,
        token_embed_dim=8,
        q_head_hidden_dim=16,
        aggregator_type="mean",
        num_heads=None,
    )


def obs_with(spec: TokenSpec, batch_size: int, present: set[tuple[str, int]], *, seed: int = 0) -> torch.Tensor:
    generator = torch.Generator().manual_seed(seed)
    obs = torch.zeros(batch_size, spec.total_dims)
    for name, slot, start, end in spec.row_layout():
        if (name, slot) in present:
            obs[:, start] = 1.0
            obs[:, start + 1 : end] = torch.rand(batch_size, end - start - 1, generator=generator)
    return obs


PRESENT = {("self", 0), ("meter", 0), ("meter", 1)}


class TestGradNorms:
    def test_absent_type_reads_exactly_zero_present_types_nonzero(self, spec, net):
        obs = obs_with(spec, 3, PRESENT)  # items absent
        net(obs).sum().backward()
        norms = per_type_encoder_grad_norms(net)
        assert set(norms) == {"self", "meter", "item"}
        assert norms["item"] == 0.0
        assert norms["meter"] > 0.0
        assert norms["self"] > 0.0

    def test_before_backward_all_zero(self, spec, net):
        assert all(v == 0.0 for v in per_type_encoder_grad_norms(net).values())


class TestPresenceFlips:
    def test_counts_flips_both_directions(self, spec):
        before = obs_with(spec, 2, PRESENT)
        after = obs_with(spec, 2, {("self", 0), ("meter", 0), ("item", 1)})
        # meter[1] present→absent, item[1] absent→present = 2 flips per sample.
        assert presence_flip_count(spec, before, after).tolist() == [2, 2]

    def test_no_flips_is_zero(self, spec):
        obs = obs_with(spec, 2, PRESENT)
        assert presence_flip_count(spec, obs, obs).tolist() == [0, 0]

    def test_payload_change_is_not_a_flip(self, spec):
        before = obs_with(spec, 1, PRESENT, seed=1)
        after = obs_with(spec, 1, PRESENT, seed=2)
        assert presence_flip_count(spec, before, after).tolist() == [0]

    def test_shape_mismatch_refuses(self, spec):
        with pytest.raises(ValueError, match="shapes differ"):
            presence_flip_count(spec, torch.zeros(1, spec.total_dims), torch.zeros(2, spec.total_dims))

    def test_conditioning_groups_by_flip_count(self, spec):
        values = torch.tensor([1.0, 3.0, 10.0])
        flips = torch.tensor([0, 0, 2])
        conditioned = condition_on_presence_flips(values, flips)
        assert conditioned == {0: 2.0, 2: 10.0}


class TestColdTokenInjection:
    def test_returns_finite_perturbation(self, spec, net):
        obs = obs_with(spec, 3, PRESENT)
        delta = cold_token_injection(net, spec, obs, type_name="item", slot_index=0)
        assert delta >= 0.0
        assert torch.isfinite(torch.tensor(delta))

    def test_injection_does_not_mutate_obs(self, spec, net):
        obs = obs_with(spec, 2, PRESENT)
        snapshot = obs.clone()
        cold_token_injection(net, spec, obs, type_name="item", slot_index=1)
        assert torch.equal(obs, snapshot)

    def test_custom_payload_width_validated(self, spec, net):
        obs = obs_with(spec, 1, PRESENT)
        with pytest.raises(ValueError, match="payload width"):
            cold_token_injection(net, spec, obs, type_name="item", slot_index=0, payload=torch.zeros(3))

    def test_unknown_type_refuses(self, spec, net):
        obs = obs_with(spec, 1, PRESENT)
        with pytest.raises(ValueError, match="not in the network roster"):
            cold_token_injection(net, spec, obs, type_name="effect", slot_index=0)


class TestEmbeddingDiagnostics:
    def test_pooled_norm_positive_for_nonempty(self, spec, net):
        assert pooled_embedding_norm(net, obs_with(spec, 2, PRESENT)) > 0.0

    def test_cosine_is_one_against_identical_target(self, spec, net):
        obs = obs_with(spec, 2, PRESENT)
        assert online_target_cosine(net, net, obs) == pytest.approx(1.0, abs=1e-6)

    def test_cosine_differs_for_diverged_target(self, spec, net):
        torch.manual_seed(99)
        target = TokenSetQNetwork(
            token_spec=spec,
            action_dim=4,
            token_embed_dim=8,
            q_head_hidden_dim=16,
            aggregator_type="mean",
            num_heads=None,
        )
        obs = obs_with(spec, 2, PRESENT)
        assert online_target_cosine(net, target, obs) < 1.0 - 1e-4


class TestMetricBundle:
    def test_one_flat_dict_with_all_families(self, spec, net):
        obs = obs_with(spec, 3, PRESENT)
        next_obs = obs_with(spec, 3, {("self", 0), ("meter", 0), ("item", 0)})
        net(obs).sum().backward()
        metrics = token_diagnostic_metrics(
            online=net,
            target=net,
            token_spec=spec,
            obs=obs,
            next_obs=next_obs,
            td_errors=torch.rand(3),
            intrinsic_rewards=torch.rand(3),
        )
        assert {"TokenNet/GradNorm/self", "TokenNet/GradNorm/meter", "TokenNet/GradNorm/item"} <= set(metrics)
        assert metrics["TokenNet/PresenceFlips_Mean"] == 2.0
        assert metrics["TokenNet/PooledNorm"] > 0.0
        assert metrics["TokenNet/OnlineTargetCosine"] == pytest.approx(1.0, abs=1e-6)
        assert any(key.startswith("TokenNet/TDError_At") for key in metrics)
        assert any(key.startswith("TokenNet/Intrinsic_At") for key in metrics)
        assert all(isinstance(v, float) for v in metrics.values())
