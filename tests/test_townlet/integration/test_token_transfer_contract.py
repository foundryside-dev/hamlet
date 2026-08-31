"""The token-net transfer contract (token-obs spec §5; unit 3 Task 9).

Three committed fixture packs under `configs/test/` with disjoint token vocabularies
(beyond the always-live core — `self`/`meter`/`affordance` are structurally present
in any runnable pack; full disjointness is impossible by construction):

- ``token_transfer_a``: + ``variable_element`` (a bound exposed variable), no items;
- ``token_transfer_b``: + ``item`` (a declared item budget), no exposed variables;
- ``token_transfer_c``: core only — the payload-schema-mismatch vehicle.

The contract: train-step a token net on A; its weights load BY ModuleDict TYPE KEY
on B (intersection, both directions reported loudly) and forward cleanly; the
type-schema hash is engine-wide (the token gate passes across universes) while the
layout hash is universe-bound (the flat gate refuses); a payload-schema mismatch
refuses. Zero-shot *competence* is a research observation, never asserted here.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.agent.network_factory import NetworkFactory
from townlet.agent.networks import TokenSetQNetwork
from townlet.config.brain_config import load_brain_config
from townlet.training.checkpoint_utils import (
    assert_checkpoint_layout_hash,
    assert_checkpoint_token_type_schema_hash,
    attach_universe_metadata,
    load_token_network_state_by_type,
)
from townlet.universe.compiler import UniverseCompiler

PACKS = {
    "a": Path("configs/test/token_transfer_a"),
    "b": Path("configs/test/token_transfer_b"),
    "c": Path("configs/test/token_transfer_c"),
}


@pytest.fixture(scope="module")
def universes():
    return {name: UniverseCompiler().compile(path, primary_level="L0_transfer", use_cache=False) for name, path in PACKS.items()}


def _level(universe):
    return universe.get_level(universe.metadata.primary_level)


def build_net(pack: str, universes) -> TokenSetQNetwork:
    brain = load_brain_config(PACKS[pack])
    assert brain.architecture.type == "token_set", f"fixture pack {pack} must drive token_set"
    assert brain.architecture.token_set is not None
    universe = universes[pack]
    return NetworkFactory.build_token_set(
        config=brain.architecture.token_set,
        action_dim=universe.metadata.action_count,
        token_spec=_level(universe).token_spec,
    )


def make_obs(universe, batch_size: int, *, seed: int = 0) -> torch.Tensor:
    """All rows present with random bounded payloads — the shape contract, not content."""
    generator = torch.Generator().manual_seed(seed)
    obs = torch.zeros(batch_size, _level(universe).token_spec.total_dims)
    for _name, _slot, start, end in _level(universe).token_spec.row_layout():
        obs[:, start] = 1.0
        obs[:, start + 1 : end] = torch.rand(batch_size, end - start - 1, generator=generator)
    return obs


class TestFixtureRosters:
    """Guard the fixtures against drift — the vocabulary DISJOINTNESS is the test bed."""

    def test_pack_a_has_variable_element_and_no_items(self, universes) -> None:
        census = _level(universes["a"]).token_spec.census
        assert census["variable_element"] > 0
        assert census["item"] == 0

    def test_pack_b_has_items_and_no_variable_element(self, universes) -> None:
        census = _level(universes["b"]).token_spec.census
        assert census["item"] > 0
        assert census["variable_element"] == 0

    def test_pack_c_is_core_only(self, universes) -> None:
        census = _level(universes["c"]).token_spec.census
        assert census["item"] == 0 and census["variable_element"] == 0
        assert census["self"] == 1 and census["meter"] > 0 and census["affordance"] > 0

    def test_no_token_advisories(self, universes) -> None:
        for name, universe in universes.items():
            assert _level(universe).token_advisories == (), f"pack {name}: {_level(universe).token_advisories}"

    def test_type_schema_hash_is_engine_wide_layout_is_not(self, universes) -> None:
        hashes = {_level(u).token_type_schema_hash for u in universes.values()}
        assert len(hashes) == 1, "type-schema hash must be engine-wide (transfer contract)"
        layouts = {_level(u).layout_hash for u in universes.values()}
        assert len(layouts) == 3, "layout hash must be universe-bound (flat contract)"


class TestTransferContract:
    def test_train_step_on_a_then_load_by_type_and_forward_on_b(self, universes) -> None:
        torch.manual_seed(5)
        net_a = build_net("a", universes)
        assert net_a.token_type_names == ("self", "meter", "affordance", "variable_element")

        # A real train step on pack A: TD-style regression, backward, optimizer step.
        optimizer = torch.optim.Adam(net_a.parameters(), lr=1e-3)
        obs = make_obs(universes["a"], batch_size=8, seed=1)
        before = net_a.encoder.encoders["meter"].weight.detach().clone()
        q_values = net_a(obs)
        loss = torch.nn.functional.mse_loss(q_values, torch.rand_like(q_values))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        assert torch.isfinite(loss)
        assert not torch.equal(net_a.encoder.encoders["meter"].weight, before), "the train step must move the weights"

        # Load by ModuleDict type key on pack B: intersection, both directions reported.
        net_b = build_net("b", universes)
        assert net_b.token_type_names == ("self", "meter", "affordance", "item")
        report = load_token_network_state_by_type(net_b, net_a.state_dict())
        assert report.loaded_types == ("affordance", "meter", "self")
        assert report.cold_started_types == ("item",)
        assert report.dropped_types == ("variable_element",)
        assert torch.equal(net_b.encoder.encoders["meter"].weight, net_a.encoder.encoders["meter"].weight)

        # Forward cleanly on B's universe.
        q_b = net_b(make_obs(universes["b"], batch_size=4, seed=2))
        assert q_b.shape == (4, universes["b"].metadata.action_count)
        assert torch.isfinite(q_b).all()

    def test_token_gate_passes_across_universes_flat_gate_refuses(self, universes) -> None:
        """A checkpoint stamped on pack A gates CLEAN on pack B for a token net (the
        type-schema hash is the engine's, not the pack's) while the flat layout gate
        refuses — the two contracts the gates were split for."""
        checkpoint: dict[str, object] = {}
        attach_universe_metadata(checkpoint, universes["a"])
        # The named gates carry the two contracts. (`assert_checkpoint_dimensions`
        # composes the token gate with the same-universe content-hash legs — the
        # RESUME path; a cross-universe load routes through the roster loader and
        # these named gates instead.)
        assert_checkpoint_token_type_schema_hash(checkpoint, universes["b"])
        with pytest.raises(ValueError, match="layout_hash mismatch"):
            assert_checkpoint_layout_hash(checkpoint, universes["b"])

    def test_flat_view_forward_feedforward_and_dueling(self, universes) -> None:
        """The flat view is a supported second, universe-bound ABI (spec §4): the same
        serialization reads as a flat vector for the vector networks, guarded by the
        layout-hash gate (tested above/in the unit gates), not by the type schema."""
        from townlet.config.brain_config import DuelingConfig, DuelingStreamConfig, FeedforwardConfig

        universe = universes["a"]
        flat_dim = _level(universe).token_spec.total_dims
        obs = make_obs(universe, batch_size=3, seed=9)

        feedforward = NetworkFactory.build_feedforward(
            config=FeedforwardConfig(hidden_layers=[32, 16], activation="relu", dropout=0.0, layer_norm=True),
            obs_dim=flat_dim,
            action_dim=universe.metadata.action_count,
        )
        assert feedforward(obs).shape == (3, universe.metadata.action_count)

        dueling = NetworkFactory.build_dueling(
            config=DuelingConfig(
                shared_layers=[32],
                value_stream=DuelingStreamConfig(hidden_layers=[16], activation="relu"),
                advantage_stream=DuelingStreamConfig(hidden_layers=[16], activation="relu"),
                activation="relu",
                dropout=0.0,
                layer_norm=True,
            ),
            obs_dim=flat_dim,
            action_dim=universe.metadata.action_count,
        )
        q_values = dueling(obs)
        assert q_values.shape == (3, universe.metadata.action_count)
        assert torch.isfinite(q_values).all()

    def test_payload_schema_mismatch_on_pack_c_refuses_loudly(self, universes) -> None:
        """Pack C's checkpoint, doctored to a different meter payload width, must
        REFUSE on load — payload widths are engine constants (spec §1), so a width
        difference means a foreign engine's checkpoint, never a pack difference."""
        net_c = build_net("c", universes)
        doctored = dict(net_c.state_dict())
        doctored["encoder.encoders.meter.weight"] = doctored["encoder.encoders.meter.weight"][:, :-3]
        net_b = build_net("b", universes)
        with pytest.raises(ValueError, match="payload-schema mismatch"):
            load_token_network_state_by_type(net_b, doctored)
