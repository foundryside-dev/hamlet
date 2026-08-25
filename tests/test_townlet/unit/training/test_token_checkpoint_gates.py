"""Token checkpoint gates + cross-universe token-net load (token-obs unit 3 Task 9).

Additive alongside the existing gates (nothing here replaces the live obs-dim/uuid
path — that severing is Task 10):

- `attach_universe_metadata` stamps `token_type_schema_hash` + `layout_hash`;
- `assert_checkpoint_dimensions(architecture_type="token_set")` gates on the
  type-schema hash INSTEAD of obs-dim/uuids (the token-net path, dead until Task 10);
- `assert_checkpoint_dimensions(architecture_type="feedforward"|...)` adds the
  layout-hash gate ALONGSIDE the obs-dim/uuid legs (the flat-net capability);
- `load_token_network_state_by_type` loads by ModuleDict type key: intersection,
  both directions reported, payload-schema mismatch refuses;
- `VectorizedPopulation.load_token_network_cross_universe` resets optimizer,
  re-copies the target net, and resets RND state through its existing surface.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from townlet.agent.networks import TokenSetQNetwork
from townlet.agent.optimizer_factory import OptimizerFactory
from townlet.config.brain_config import (
    ArchitectureConfig,
    BrainConfig,
    LossConfig,
    OptimizerConfig,
    QLearningConfig,
    ReplayConfig,
    ScheduleConfig,
    SetAggregatorConfig,
    TokenSetConfig,
)
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.rnd import RNDExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.checkpoint_utils import (
    assert_checkpoint_dimensions,
    assert_checkpoint_layout_hash,
    assert_checkpoint_token_type_schema_hash,
    attach_universe_metadata,
    load_token_network_state_by_type,
)
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto.token_spec import SlotBinding, TokenSpec, build_token_type


@pytest.fixture(scope="module")
def compiled_universe():
    return UniverseCompiler().compile(Path("configs/test/model_config"), primary_level="L0_test")


@pytest.fixture()
def checkpoint(compiled_universe) -> dict[str, object]:
    payload: dict[str, object] = {}
    attach_universe_metadata(payload, compiled_universe)
    return payload


def _static(count: int, prefix: str) -> tuple[SlotBinding, ...]:
    return tuple(SlotBinding(slot_index=i, filler_kind="static", filler_ref=f"{prefix}:{i}") for i in range(count))


def _dynamic(count: int, prefix: str) -> tuple[SlotBinding, ...]:
    return tuple(SlotBinding(slot_index=i, filler_kind="dynamic", filler_ref=f"{prefix}:{i}") for i in range(count))


def spec_with_affordances() -> TokenSpec:
    return TokenSpec(
        types=(
            build_token_type("self", _static(1, "self")),
            build_token_type("meter", _static(2, "meter")),
            build_token_type("affordance", _static(2, "aff")),
        )
    )


def spec_with_items() -> TokenSpec:
    return TokenSpec(
        types=(
            build_token_type("self", _static(1, "self")),
            build_token_type("meter", _static(3, "meter")),
            build_token_type("item", _dynamic(2, "item")),
        )
    )


def make_net(spec: TokenSpec, *, action_dim: int = 5) -> TokenSetQNetwork:
    return TokenSetQNetwork(
        token_spec=spec,
        action_dim=action_dim,
        token_embed_dim=16,
        q_head_hidden_dim=32,
        aggregator_type="mean",
        num_heads=None,
    )


class TestAttachStampsTokenHashes:
    def test_both_hashes_stamped(self, checkpoint, compiled_universe) -> None:
        assert checkpoint["token_type_schema_hash"] == compiled_universe.token_type_schema_hash
        assert checkpoint["layout_hash"] == compiled_universe.layout_hash

    def test_existing_fields_all_stay(self, checkpoint, compiled_universe) -> None:
        """ADDITIVE: nothing the pre-Task-9 stamp wrote is dropped (Task 10 owns that)."""
        for field in (
            "config_hash",
            "primary_level",
            "observation_dim",
            "action_dim",
            "meter_count",
            "observation_field_uuids",
            "observation_schema_hash",
            "drive_hash",
            "curriculum_hash",
            "bars_hash",
            "affordances_hash",
            "training_hash",
            "brain_hash",
            "pack_brain_hash",
            "vfs_hash",
        ):
            assert field in checkpoint, f"pre-existing checkpoint field {field!r} went missing"


class TestTokenNetGate:
    def test_matching_hash_passes_without_uuid_or_obs_dim(self, checkpoint, compiled_universe) -> None:
        """The token path replaces the obs-dim/uuid legs: a checkpoint with neither
        still passes when the type-schema hash matches."""
        del checkpoint["observation_field_uuids"]
        del checkpoint["observation_dim"]
        assert_checkpoint_dimensions(checkpoint, compiled_universe, architecture_type="token_set")

    def test_mismatch_produces_the_banner(self, checkpoint, compiled_universe) -> None:
        checkpoint["token_type_schema_hash"] = "deadbeef" * 8
        with pytest.raises(ValueError, match="token_type_schema_hash mismatch"):
            assert_checkpoint_dimensions(checkpoint, compiled_universe, architecture_type="token_set")

    def test_missing_hash_refuses(self, checkpoint, compiled_universe) -> None:
        del checkpoint["token_type_schema_hash"]
        with pytest.raises(ValueError, match="missing token_type_schema_hash"):
            assert_checkpoint_token_type_schema_hash(checkpoint, compiled_universe)

    def test_action_dim_still_gated_on_the_token_path(self, checkpoint, compiled_universe) -> None:
        checkpoint["action_dim"] = 999
        with pytest.raises(ValueError, match="action_dim mismatch"):
            assert_checkpoint_dimensions(checkpoint, compiled_universe, architecture_type="token_set")


class TestFlatNetLayoutGate:
    def test_matching_layout_passes(self, checkpoint, compiled_universe) -> None:
        assert_checkpoint_dimensions(checkpoint, compiled_universe, architecture_type="feedforward")

    def test_layout_mismatch_refuses_for_flat_nets(self, checkpoint, compiled_universe) -> None:
        checkpoint["layout_hash"] = "deadbeef" * 8
        with pytest.raises(ValueError, match="layout_hash mismatch"):
            assert_checkpoint_dimensions(checkpoint, compiled_universe, architecture_type="feedforward")

    def test_missing_layout_hash_refuses(self, checkpoint, compiled_universe) -> None:
        del checkpoint["layout_hash"]
        with pytest.raises(ValueError, match="missing layout_hash"):
            assert_checkpoint_layout_hash(checkpoint, compiled_universe)

    def test_default_path_is_untouched(self, checkpoint, compiled_universe) -> None:
        """Every live caller passes no architecture_type; a moved layout_hash must NOT
        gate there this task (the promotion is Task 10)."""
        checkpoint["layout_hash"] = "deadbeef" * 8
        assert_checkpoint_dimensions(checkpoint, compiled_universe)

    def test_uuid_gate_still_runs_alongside(self, checkpoint, compiled_universe) -> None:
        checkpoint["observation_field_uuids"] = list(reversed(checkpoint["observation_field_uuids"]))
        with pytest.raises(ValueError, match="order-sensitive"):
            assert_checkpoint_dimensions(checkpoint, compiled_universe, architecture_type="feedforward")


class TestLoadByTypeKey:
    def test_intersection_loads_shared_types_only(self) -> None:
        torch.manual_seed(3)
        source_net = make_net(spec_with_affordances())
        target_net = make_net(spec_with_items())
        fresh_item_weight = target_net.encoders["item"].weight.detach().clone()

        report = load_token_network_state_by_type(target_net, source_net.state_dict())

        assert report.loaded_types == ("meter", "self")
        assert report.cold_started_types == ("item",)
        assert report.dropped_types == ("affordance",)
        # Shared types carry the SOURCE weights (meter capacity differs — 2 vs 3 —
        # and must not matter: capacities are entity variation, not weight shape).
        assert torch.equal(target_net.encoders["meter"].weight, source_net.encoders["meter"].weight)
        assert torch.equal(target_net.type_embeddings["self"], source_net.type_embeddings["self"])
        # The cold-started type keeps its fresh init.
        assert torch.equal(target_net.encoders["item"].weight, fresh_item_weight)
        # Q-head shapes match here, so it transfers mechanically.
        assert report.cold_started_modules == ()
        assert not report.is_clean

    def test_report_is_loud(self, caplog) -> None:
        source_net = make_net(spec_with_affordances())
        target_net = make_net(spec_with_items())
        with caplog.at_level("WARNING"):
            load_token_network_state_by_type(target_net, source_net.state_dict())
        assert any("roster mismatch" in record.message for record in caplog.records)

    def test_payload_schema_mismatch_refuses(self) -> None:
        """A shared type whose parameter shapes differ means the checkpoint came from
        an engine with different payload schemas (widths are engine constants) —
        refuse, never partially load."""
        source_net = make_net(spec_with_affordances())
        target_net = make_net(spec_with_items())
        doctored = dict(source_net.state_dict())
        doctored["encoders.meter.weight"] = doctored["encoders.meter.weight"][:, :-2]
        with pytest.raises(ValueError, match="payload-schema mismatch"):
            load_token_network_state_by_type(target_net, doctored)

    def test_action_dim_mismatch_cold_starts_q_head(self) -> None:
        source_net = make_net(spec_with_affordances(), action_dim=7)
        target_net = make_net(spec_with_items(), action_dim=5)
        report = load_token_network_state_by_type(target_net, source_net.state_dict())
        assert any(key.startswith("q_head.3.") for key in report.cold_started_modules)

    def test_identical_roster_loads_clean(self) -> None:
        source_net = make_net(spec_with_items())
        target_net = make_net(spec_with_items())
        report = load_token_network_state_by_type(target_net, source_net.state_dict())
        assert report.is_clean
        for key, tensor in source_net.state_dict().items():
            assert torch.equal(target_net.state_dict()[key], tensor)

    def test_refuses_non_token_networks(self) -> None:
        with pytest.raises(ValueError, match="requires a TokenSetQNetwork"):
            load_token_network_state_by_type(torch.nn.Linear(4, 4), {})


def _token_brain_config() -> BrainConfig:
    return BrainConfig(
        version="1.0",
        description="token_set cross-universe load seam test",
        architecture=ArchitectureConfig(
            type="token_set",
            token_set=TokenSetConfig(
                token_embed_dim=16,
                q_head_hidden_dim=32,
                aggregator=SetAggregatorConfig(type="mean"),
            ),
        ),
        optimizer=OptimizerConfig(
            type="adam",
            learning_rate=1e-3,
            adam_beta1=0.9,
            adam_beta2=0.999,
            adam_eps=1e-8,
            weight_decay=0.0,
            schedule=ScheduleConfig(type="constant"),
        ),
        loss=LossConfig(type="mse"),
        q_learning=QLearningConfig(gamma=0.99, target_update_frequency=100, use_double_dqn=False),
        replay=ReplayConfig(capacity=100, prioritized=False),
    )


class TestCrossUniverseLoadResets:
    def _bare_population(self, net: TokenSetQNetwork) -> VectorizedPopulation:
        """The Task-10 integration seam, tested at the seam: a token_set population
        cannot be constructed against a live env until the cut (the obs-width guard
        in _build_network refuses), so the method is pinned on a bare instance."""
        population = object.__new__(VectorizedPopulation)
        population.is_token_set = True
        population.brain_config = _token_brain_config()
        population.q_network = net
        population.target_network = make_net(spec_with_items())
        population.exploration = RNDExploration(obs_dim=net.obs_dim, embed_dim=8, device=torch.device("cpu"))
        population.env = SimpleNamespace(set_exploration_module=lambda module: None)
        population.optimizer, population.scheduler = OptimizerFactory.build(
            config=population.brain_config.optimizer,
            parameters=net.parameters(),
        )
        population.training_step_counter = 7
        return population

    def test_resets_optimizer_target_and_rnd(self) -> None:
        torch.manual_seed(11)
        target_universe_net = make_net(spec_with_items())
        population = self._bare_population(target_universe_net)

        # Dirty every piece of state the cross-universe load must reset.
        obs = torch.rand(2, target_universe_net.obs_dim)
        population.q_network(obs).sum().backward()
        population.optimizer.step()
        assert len(population.optimizer.state) > 0
        population.exploration.reward_rms.update(torch.rand(64).numpy())
        stale_predictor = {k: v.detach().clone() for k, v in population.exploration.predictor_network.state_dict().items()}
        stale_rms_count = population.exploration.reward_rms.count
        stale_exploration = population.exploration

        source_net = make_net(spec_with_affordances())
        report = population.load_token_network_cross_universe(source_net.state_dict())

        assert report.loaded_types == ("meter", "self")
        # Target re-copied from the freshly loaded online net.
        for key, tensor in population.q_network.state_dict().items():
            assert torch.equal(population.target_network.state_dict()[key], tensor)
        # Optimizer moments reset.
        assert len(population.optimizer.state) == 0
        assert population.training_step_counter == 0
        # RND reset through its existing construction surface: a fresh instance with
        # fresh statistics (rnd.py itself is byte-untouched this task).
        assert population.exploration is not stale_exploration
        assert population.exploration.reward_rms.count < stale_rms_count
        fresh_predictor = population.exploration.predictor_network.state_dict()
        assert any(not torch.equal(fresh_predictor[k], stale_predictor[k]) for k in stale_predictor)

    def test_refuses_non_token_population(self) -> None:
        population = object.__new__(VectorizedPopulation)
        population.is_token_set = False
        population.brain_config = _token_brain_config()
        with pytest.raises(ValueError, match="token_set"):
            population.load_token_network_cross_universe({})


class TestReviewRound1Pins:
    """Task-9 review fix round: M2 (two-way module loudness), M5 (attach guard),
    I1 (adaptive wrapper reset)."""

    def test_target_only_modules_are_reported_cold(self) -> None:
        """Non-per-type parameters the TARGET has but the checkpoint lacks (attention
        projections loading from a mean checkpoint) keep fresh init and must be
        reported, not silent (task-9 review M2)."""
        source_net = make_net(spec_with_items())
        target_net = TokenSetQNetwork(
            token_spec=spec_with_items(),
            action_dim=5,
            token_embed_dim=16,
            q_head_hidden_dim=32,
            aggregator_type="attention",
            num_heads=2,
        )
        report = load_token_network_state_by_type(target_net, source_net.state_dict())
        assert any("q_proj" in key for key in report.cold_started_modules)
        assert not report.is_clean

    def test_attach_refuses_universe_without_token_hashes(self, compiled_universe) -> None:
        """Declared guard (task-9 review M5): a universe missing the token hashes must
        refuse at save — a checkpoint no gate can check must not exist."""
        crippled = dataclasses.replace(compiled_universe, token_type_schema_hash=None)
        with pytest.raises(ValueError, match="token_type_schema_hash"):
            attach_universe_metadata({}, crippled)

    def test_adaptive_wrapper_annealing_state_resets(self) -> None:
        """Cross-universe load resets the AdaptiveIntrinsicExploration WRAPPER's
        annealing/survival statistics, not just the inner RND (task-9 review I1)."""
        torch.manual_seed(13)
        target_universe_net = make_net(spec_with_items())
        population = TestCrossUniverseLoadResets()._bare_population(target_universe_net)
        adaptive = AdaptiveIntrinsicExploration(
            obs_dim=target_universe_net.obs_dim, embed_dim=8, device=torch.device("cpu")
        )
        adaptive.current_intrinsic_weight = 0.25
        adaptive.survival_history.extend([10.0, 20.0, 30.0])
        stale_inner = adaptive.rnd
        population.exploration = adaptive

        source_net = make_net(spec_with_affordances())
        population.load_token_network_cross_universe(source_net.state_dict())

        assert population.exploration is adaptive
        assert adaptive.rnd is not stale_inner
        assert adaptive.current_intrinsic_weight == adaptive.initial_intrinsic_weight
        assert adaptive.survival_history == []
