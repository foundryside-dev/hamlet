"""Compiler emission of the TokenSpec artifact.

Since the unit-3 Task-10 cut the TokenSpec IS the compiler's observation product: the
ObservationSpec/ObservationActivity/VFS-mirror family it compiled beside is deleted, and
`observation_schema_hash` is computed over the TokenSpec. `token_type_schema_hash`
(transfer contract) and `layout_hash` (flat-net contract) carry PDR-0033 narrowness:
each moves exactly when its declared content moves, both directions pinned below.
"""

from pathlib import Path
from types import SimpleNamespace

import msgpack
import pytest

from townlet.universe.compiled import COMPILED_SCHEMA_VERSION, CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compilers.observation import ObservationCompiler
from townlet.universe.dto.token_spec import (
    DESCRIPTOR_BLOCK_WIDTH,
    PAYLOAD_SCHEMAS,
    TOKEN_TYPE_ROSTER,
    SlotBinding,
    TokenSpec,
    TokenTypeSchema,
    build_token_type,
)
from townlet.universe.token_hashes import (
    compute_token_layout_hash,
    compute_token_type_schema_hash,
)
from townlet.vfs.schema import NormalizationSpec, VariableDef

_HEX64 = 64


@pytest.fixture(scope="module")
def l1_universe() -> CompiledUniverse:
    return UniverseCompiler().compile(Path("configs/default_curriculum"), primary_level="L1_full_observability", use_cache=False)


@pytest.fixture(scope="module")
def effects_universe() -> CompiledUniverse:
    return UniverseCompiler().compile(Path("configs/test/effects_smoke"), primary_level="L0_effects", use_cache=False)


class TestL1TokenEmission:
    """The compiled L1 artifact matches Task 6's measured worked table."""

    def test_census_matches_task6_worked_table(self, l1_universe):
        assert l1_universe.token_spec is not None
        assert l1_universe.token_spec.census == {
            "self": 1,
            "meter": 8,
            "affordance": 14,
            "agent": 0,  # no shared-world declaration exists; never keyed on num_agents
            "item": 2,  # max_items_in_world 1 + max_items_per_agent 1 x 1 agent/world
            "effect": 0,
            "variable_element": 0,
        }

    def test_total_dims_is_task6_measurement(self, l1_universe):
        assert l1_universe.token_spec.total_dims == 1080

    def test_all_roster_types_present_in_engine_order(self, l1_universe):
        assert tuple(t.type_name for t in l1_universe.token_spec.types) == TOKEN_TYPE_ROSTER

    def test_meter_slots_bind_bars_declaration_order(self, l1_universe):
        meter_type = l1_universe.token_spec.get_type("meter")
        bound = [b.filler_ref for b in meter_type.slot_bindings]
        declared = [m.name for m in l1_universe.get_level("L1_full_observability").bars.meters]
        assert bound == declared

    def test_affordance_slots_bind_metadata_count_not_positions(self, l1_universe):
        # Ruling 3: capacity = metadata.affordance_count; deployment.positions are
        # per-instance payload inputs (L1 lists 2 EAT positions vs count 14).
        affordance_type = l1_universe.token_spec.get_type("affordance")
        assert affordance_type.capacity == l1_universe.metadata.affordance_count == 14
        assert [b.filler_ref for b in affordance_type.slot_bindings] == list(l1_universe.metadata.affordance_ids)

    def test_dynamic_types_carry_dynamic_bindings(self, l1_universe):
        item_type = l1_universe.token_spec.get_type("item")
        assert all(b.filler_kind == "dynamic" for b in item_type.slot_bindings)

    def test_no_advisories_for_default_curriculum(self, l1_universe):
        # Empty effect catalog, zero exposed profile variables: nothing to advise.
        assert l1_universe.token_advisories == ()

    def test_hashes_present_and_hex(self, l1_universe):
        assert len(l1_universe.token_type_schema_hash) == _HEX64
        assert len(l1_universe.layout_hash) == _HEX64
        int(l1_universe.token_type_schema_hash, 16)
        int(l1_universe.layout_hash, 16)

    def test_every_level_carries_token_spec(self, l1_universe):
        for name in l1_universe.available_levels:
            level = l1_universe.get_level(name)
            assert level.token_spec is not None, name
            assert level.token_type_schema_hash and level.layout_hash, name

    def test_byte_identical_levels_share_layout_hash(self, l1_universe):
        # L0_0/L0_5/L1 differ only in training hyperparameters (CLAUDE.md, verified by
        # diff 2026-08-12) — their token layouts must be identical.
        l0 = l1_universe.get_level("L0_0_minimal")
        l1 = l1_universe.get_level("L1_full_observability")
        assert l0.layout_hash == l1.layout_hash
        assert l0.token_type_schema_hash == l1.token_type_schema_hash


class TestEffectCapacityFromDeclaredBudget:
    """`max_active_effects` is required in effects.yaml iff any effect is declared, and
    the `effect` token capacity is Sigma(scope budget x scope denominator). The Task-7
    advisory is a REFUSAL since the cut."""

    def test_effects_smoke_capacity_comes_from_the_declared_budget(self, effects_universe):
        assert effects_universe.token_spec.get_type("effect").capacity > 0

    def test_no_budget_advisory_survives(self, effects_universe):
        assert not any("max_active_effects" in a for a in effects_universe.token_advisories)

    def test_declaring_effects_without_a_budget_refuses(self, tmp_path):
        from townlet.config.effects_config import EffectsConfig

        with pytest.raises(ValueError, match="max_active_effects"):
            EffectsConfig.model_validate(
                {
                    "version": "1.0",
                    "effect_definitions": [
                        {
                            "id": "e",
                            "scope": "agent",
                            "duration": 1,
                            "intensity": 1.0,
                            "reapply_policy": "renew",
                            "observable": True,
                        }
                    ],
                }
            )

    def test_empty_catalog_declaring_a_budget_refuses(self):
        from townlet.config.effects_config import EffectsConfig

        with pytest.raises(ValueError, match="reaches nothing"):
            EffectsConfig.model_validate(
                {
                    "version": "1.0",
                    "effect_definitions": [],
                    "max_active_effects": {"global": 0, "agent": 1, "item": 0, "affordance": 0},
                }
            )

    def test_empty_catalog_has_zero_effect_capacity(self, l1_universe):
        assert l1_universe.token_spec.get_type("effect").capacity == 0


class TestTransferContractAcrossPacks:
    def test_type_schema_hash_is_engine_wide(self, l1_universe, effects_universe):
        # The transfer contract hashes type SCHEMAS, not capacities: any two universes
        # compiled by this engine with the full roster share it (spec §1 first invariant —
        # entity variation goes into token count, never payload width).
        assert l1_universe.token_type_schema_hash == effects_universe.token_type_schema_hash

    def test_layout_hash_is_universe_specific(self, l1_universe, effects_universe):
        assert l1_universe.layout_hash != effects_universe.layout_hash


def _spec_with(meter_refs: tuple[str, ...], *, item_capacity: int = 0) -> TokenSpec:
    types = []
    for type_name in TOKEN_TYPE_ROSTER:
        if type_name == "self":
            bindings = (SlotBinding(slot_index=0, filler_kind="static", filler_ref="self"),)
        elif type_name == "meter":
            bindings = tuple(SlotBinding(slot_index=i, filler_kind="static", filler_ref=ref) for i, ref in enumerate(meter_refs))
        elif type_name == "item":
            bindings = tuple(SlotBinding(slot_index=i, filler_kind="dynamic", filler_ref=f"item:{i}") for i in range(item_capacity))
        else:
            bindings = ()
        types.append(build_token_type(type_name, bindings))
    return TokenSpec(types=tuple(types))


class TestHashNarrowness:
    """PDR-0033: each hash moves exactly when its declared content moves."""

    def test_equal_specs_hash_equal(self):
        a = _spec_with(("energy", "health"))
        b = _spec_with(("energy", "health"))
        assert compute_token_type_schema_hash(a) == compute_token_type_schema_hash(b)
        assert compute_token_layout_hash(a) == compute_token_layout_hash(b)

    def test_capacity_change_moves_layout_not_type_schema(self):
        a = _spec_with(("energy", "health"))
        b = _spec_with(("energy", "health"), item_capacity=3)
        assert compute_token_type_schema_hash(a) == compute_token_type_schema_hash(b)
        assert compute_token_layout_hash(a) != compute_token_layout_hash(b)

    def test_binding_identity_change_moves_layout_not_type_schema(self):
        # Same widths, same capacities — a re-bound slot changes what a flat dim MEANS.
        a = _spec_with(("energy", "health"))
        b = _spec_with(("health", "energy"))
        assert compute_token_type_schema_hash(a) == compute_token_type_schema_hash(b)
        assert compute_token_layout_hash(a) != compute_token_layout_hash(b)

    def test_static_signature_moves_neither(self):
        # Signature is slot CONTENT (what the descriptor publishes), not layout.
        base = _spec_with(())
        signed_meter = TokenTypeSchema(
            type_name="meter",
            payload_features=PAYLOAD_SCHEMAS["meter"],
            capacity=1,
            slot_bindings=(SlotBinding(slot_index=0, filler_kind="static", filler_ref="energy", static_signature=(0.5, 1.0)),),
        )
        unsigned_meter = TokenTypeSchema(
            type_name="meter",
            payload_features=PAYLOAD_SCHEMAS["meter"],
            capacity=1,
            slot_bindings=(SlotBinding(slot_index=0, filler_kind="static", filler_ref="energy"),),
        )
        with_sig = TokenSpec(types=(base.types[0], signed_meter) + base.types[2:])
        without_sig = TokenSpec(types=(base.types[0], unsigned_meter) + base.types[2:])
        assert compute_token_layout_hash(with_sig) == compute_token_layout_hash(without_sig)
        assert compute_token_type_schema_hash(with_sig) == compute_token_type_schema_hash(without_sig)

    def test_roster_subset_moves_type_schema(self):
        # A universe instantiating fewer types IS a different type schema.
        full = _spec_with(())
        subset = TokenSpec(types=full.types[:3])
        assert compute_token_type_schema_hash(full) != compute_token_type_schema_hash(subset)
        assert compute_token_layout_hash(full) != compute_token_layout_hash(subset)

    def test_encoding_version_moves_both(self):
        a = _spec_with(())
        b = TokenSpec(types=a.types, encoding_version="token-9.9-test")
        assert compute_token_type_schema_hash(a) != compute_token_type_schema_hash(b)
        assert compute_token_layout_hash(a) != compute_token_layout_hash(b)


class TestSerialization:
    def test_round_trip_preserves_token_block(self, effects_universe, tmp_path):
        cache_path = tmp_path / "u.msgpack"
        effects_universe.save_to_cache(cache_path)
        restored = CompiledUniverse.load_from_cache(cache_path)
        assert restored.token_spec == effects_universe.token_spec
        assert restored.token_type_schema_hash == effects_universe.token_type_schema_hash
        assert restored.layout_hash == effects_universe.layout_hash
        assert restored.token_advisories == effects_universe.token_advisories
        for name in effects_universe.available_levels:
            assert restored.get_level(name).token_spec == effects_universe.get_level(name).token_spec

    def test_round_trip_recomputes_identical_hashes(self, effects_universe, tmp_path):
        cache_path = tmp_path / "u.msgpack"
        effects_universe.save_to_cache(cache_path)
        restored = CompiledUniverse.load_from_cache(cache_path)
        assert compute_token_type_schema_hash(restored.token_spec) == restored.token_type_schema_hash
        assert compute_token_layout_hash(restored.token_spec) == restored.layout_hash

    def test_stale_pre_cut_artifact_refuses(self, effects_universe, tmp_path):
        payload = effects_universe.to_dict()
        payload["compiled_schema_version"] = "1.21"
        stale_path = tmp_path / "stale.msgpack"
        stale_path.write_bytes(msgpack.packb(payload, use_bin_type=True))
        with pytest.raises(ValueError, match="schema mismatch") as excinfo:
            CompiledUniverse.load_from_cache(stale_path)
        assert "1.21" in str(excinfo.value)
        assert COMPILED_SCHEMA_VERSION in str(excinfo.value)

    def test_missing_token_block_refuses(self, effects_universe):
        payload = effects_universe.to_dict()
        payload.pop("token_spec")
        with pytest.raises(ValueError, match="missing required field 'token_spec'"):
            CompiledUniverse.from_dict(payload)

    def test_tampered_payload_schema_refuses(self, effects_universe):
        # The artifact is self-describing: a cache whose payload features disagree with
        # the running engine's schema refuses on load (spec §1 fixed-width invariant).
        payload = effects_universe.to_dict()
        payload["token_spec"]["types"][1]["payload_features"] = ["not_the_engine_schema"]
        with pytest.raises(ValueError, match="does not match the engine constant"):
            CompiledUniverse.from_dict(payload)


def _env_stub(*names_and_types: tuple[str, str]):
    """Minimal EnvConfigV21 stand-in: `_variable_element_bindings` reads only
    `environment.environment.variables[*].name / .semantic_type`."""
    return SimpleNamespace(
        environment=SimpleNamespace(variables=[SimpleNamespace(name=n, semantic_type=t) for n, t in names_and_types])
    )


def _variable_def(name: str, *, dims: int | None = None, normalization: NormalizationSpec | None) -> VariableDef:
    return VariableDef(
        id=name,
        scope="agent",
        type="vecNf" if dims and dims > 1 else "scalar",
        dims=dims,
        lifetime="tick",
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        default=[0.0] * dims if dims and dims > 1 else 0.0,
        description=name,
        normalization=normalization,
    )


_BOUNDED = NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=True)


class TestVariableElementBindings:
    """Direct-call coverage of `_variable_element_bindings`. Every branch that ADVISED
    while the token path ran alongside the old one is a compile REFUSAL since the cut."""

    def test_passing_declarations_bind_slots_in_registry_order(self):
        env = _env_stub(("temp", "custom"), ("wind", "custom"))
        defs = (
            _variable_def("temp", normalization=_BOUNDED),
            _variable_def("wind", dims=3, normalization=NormalizationSpec(kind="minmax", min=0.0, max=10.0, clip=True)),
        )
        bindings = ObservationCompiler._variable_element_bindings(env, None, defs)
        assert [b.filler_ref for b in bindings] == ["temp", "wind[0]", "wind[1]", "wind[2]"]
        assert [b.slot_index for b in bindings] == [0, 1, 2, 3]
        assert all(b.filler_kind == "static" for b in bindings)
        for binding in bindings:
            assert binding.static_signature is not None
            assert len(binding.static_signature) == DESCRIPTOR_BLOCK_WIDTH
        # The bound set constructs a live variable_element type at the derived capacity.
        assert build_token_type("variable_element", bindings).capacity == 4

    def test_unnormalized_variable_refuses(self):
        env = _env_stub(("raw_var", "custom"))
        defs = (_variable_def("raw_var", normalization=None),)
        with pytest.raises(ValueError, match="declares no normalization"):
            ObservationCompiler._variable_element_bindings(env, None, defs)

    def test_unbounded_kind_refuses_with_the_boundedness_rule(self):
        env = _env_stub(("z", "custom"))
        defs = (_variable_def("z", normalization=NormalizationSpec(kind="zscore", mean=0.0, std=1.0)),)
        with pytest.raises(ValueError, match="bounded normalization kind"):
            ObservationCompiler._variable_element_bindings(env, None, defs)

    def test_rank_scaled_refuses_at_exposure(self):
        env = _env_stub(("r", "custom"))
        defs = (_variable_def("r", normalization=NormalizationSpec(kind="rank_scaled")),)
        with pytest.raises(ValueError, match="rank_scaled"):
            ObservationCompiler._variable_element_bindings(env, None, defs)

    def test_indistinguishable_pair_refuses_naming_both(self):
        # Identical declarations apart from the id: identical static signatures.
        env = _env_stub(("twin_a", "custom"), ("twin_b", "custom"))
        defs = (_variable_def("twin_a", normalization=_BOUNDED), _variable_def("twin_b", normalization=_BOUNDED))
        with pytest.raises(ValueError, match="indistinguishable") as excinfo:
            ObservationCompiler._variable_element_bindings(env, None, defs)
        assert "twin_a" in str(excinfo.value) and "twin_b" in str(excinfo.value)

    def test_unexposed_variable_binds_nothing(self):
        # Explicit exposure: a registry variable no environment.yaml or profile exposure
        # names is UNEXPOSED and occupies no slot (the fail-open default is deleted).
        defs = (_variable_def("hidden", normalization=None),)
        assert ObservationCompiler._variable_element_bindings(_env_stub(), None, defs) == ()


class TestMeanCensusAdvisoryWiring:
    """build_token_spec's census branch (review I1d): a set-pooling brain declaring
    `{type: mean}` against a census with a type over the threshold advises; other
    architectures do not."""

    @staticmethod
    def _wide_bars(count: int):
        from townlet.config.bars_v2_config import (
            BarsV2Config,
            MeterBoundsConfig,
            MeterConfig,
            MeterDepletionConfig,
            MeterRecoveryConfig,
        )

        return BarsV2Config(
            version="1.0",
            meters=[
                MeterConfig(
                    name=f"m{i}",
                    initial=1.0,
                    depletion=MeterDepletionConfig(passive=0.0, move=0.0, interact=0.0),
                    recovery=MeterRecoveryConfig(natural=0.0),
                    bounds=MeterBoundsConfig(min=0.0, max=1.0, lethal_min=False, lethal_max=False),
                )
                for i in range(count)
            ],
            cascades=[],
        )

    @staticmethod
    def _token_set_mean_brain():
        import yaml

        from townlet.config.brain_config import BrainConfig

        payload = yaml.safe_load(Path("configs/test/set_encoder_smoke/brain.yaml").read_text())
        assert payload["architecture"]["token_set"]["aggregator"]["type"] == "mean"
        return BrainConfig.model_validate(payload)

    def _build(self, l1_universe, bars, brain):
        from townlet.universe.dto import AffordanceMetadata

        return ObservationCompiler().build_token_spec(
            l1_universe.stratum,
            bars,
            AffordanceMetadata(affordances=()),
            None,
            None,
            None,
            l1_universe.environment,
            None,
            (),
            brain,
        )

    def test_mean_aggregator_over_threshold_advises(self, l1_universe):
        spec, advisories = self._build(l1_universe, self._wide_bars(65), self._token_set_mean_brain())
        assert spec.census["meter"] == 65
        census_notes = [a for a in advisories if "aggregator 'mean'" in a]
        assert len(census_notes) == 1
        assert "meter=65" in census_notes[0]

    def test_mean_aggregator_under_threshold_advises_nothing(self, l1_universe):
        _spec, advisories = self._build(l1_universe, self._wide_bars(8), self._token_set_mean_brain())
        assert not any("aggregator 'mean'" in a for a in advisories)

    def test_non_set_encoder_brain_never_census_advises(self, l1_universe):
        # L1's own brain is feedforward; even a 65-meter census must not advise.
        spec, advisories = self._build(l1_universe, self._wide_bars(65), l1_universe.brain)
        assert spec.census["meter"] == 65
        assert advisories == ()


class TestInspectCensus:
    def test_inspect_prints_token_census(self, effects_universe, tmp_path, capsys):
        from townlet.universe.__main__ import main

        artifact = tmp_path / "universe.msgpack"
        effects_universe.save_to_cache(artifact)
        assert main(["inspect", str(artifact)]) == 0
        out = capsys.readouterr().out
        assert "Token census:" in out
        assert "affordance" in out
        assert "total_dims" in out
        # effects_smoke's budget advisory is a refusal since the cut, so it carries none.
        assert "ADVISORY" not in out

    def test_inspect_json_carries_census(self, effects_universe, tmp_path, capsys):
        import json

        from townlet.universe.__main__ import main

        artifact = tmp_path / "universe.msgpack"
        effects_universe.save_to_cache(artifact)
        assert main(["inspect", str(artifact), "--format", "json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["token_census"] == effects_universe.token_spec.census
        assert payload["token_total_dims"] == effects_universe.token_spec.total_dims
        assert payload["token_type_schema_hash"] == effects_universe.token_type_schema_hash
        assert payload["layout_hash"] == effects_universe.layout_hash
