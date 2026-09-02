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
    METER_SIGNATURE_FEATURES,
    PAYLOAD_SCHEMAS,
    TOKEN_TYPE_ROSTER,
    SlotBinding,
    TokenSpec,
    TokenTypeSchema,
    build_token_type,
    meter_signature,
    variable_element_bindings,
)
from townlet.universe.token_hashes import (
    canonical_token_layout,
    compute_observation_schema_hash,
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


def _selected(universe: CompiledUniverse) -> CompiledUniverse.LevelMetadata:
    return universe.get_level(universe.metadata.primary_level)


class TestL1TokenEmission:
    """The compiled L1 artifact matches the worked table measured 2026-09-02 after
    `day_phase` (PDR-0143)."""

    def test_census_matches_task6_worked_table(self, l1_universe):
        assert _selected(l1_universe).token_spec.census == {
            "self": 1,
            "meter": 8,
            "affordance": 14,
            "agent": 0,  # no shared-world declaration exists; never keyed on num_agents
            "item": 2,  # max_items_in_world 1 + max_items_per_agent 1 x 1 agent/world
            "effect": 0,
            # The authored day_phase clock is now ONE exposed cyclical token (PDR-0143).
            "variable_element": 1,
        }

    def test_total_dims_is_task6_measurement(self, l1_universe):
        # Compact dynamic transport excludes immutable context and rank padding.
        assert _selected(l1_universe).token_spec.census["variable_element"] == 1
        assert _selected(l1_universe).token_spec.total_dims == 118
        assert _selected(l1_universe).token_spec.fixed_total_dims == 4142

    def test_all_roster_types_present_in_engine_order(self, l1_universe):
        assert tuple(t.type_name for t in _selected(l1_universe).token_spec.types) == TOKEN_TYPE_ROSTER

    def test_meter_slots_bind_bars_declaration_order(self, l1_universe):
        meter_type = _selected(l1_universe).token_spec.get_type("meter")
        bound = [b.filler_ref for b in meter_type.slot_bindings]
        declared = [m.name for m in l1_universe.get_level("L1_full_observability").bars.meters]
        assert bound == declared

    def test_affordance_slots_bind_metadata_count_not_positions(self, l1_universe):
        # Ruling 3: capacity = metadata.affordance_count; deployment.positions are
        # per-instance payload inputs (L1 lists 2 EAT positions vs count 14).
        affordance_type = _selected(l1_universe).token_spec.get_type("affordance")
        assert affordance_type.capacity == l1_universe.metadata.affordance_count == 14
        assert [b.filler_ref for b in affordance_type.slot_bindings] == list(l1_universe.metadata.affordance_ids)

    def test_dynamic_types_carry_dynamic_bindings(self, l1_universe):
        item_type = _selected(l1_universe).token_spec.get_type("item")
        assert all(b.filler_kind == "dynamic" for b in item_type.slot_bindings)

    def test_no_advisories_for_default_curriculum(self, l1_universe):
        # Empty effect catalog and no exposed variable-element declarations. Advisories
        # fire only when one token type exceeds MEAN_CENSUS_ADVISORY (64) rows.
        assert _selected(l1_universe).token_advisories == ()

    def test_hashes_present_and_hex(self, l1_universe):
        assert len(_selected(l1_universe).token_type_schema_hash) == _HEX64
        assert len(_selected(l1_universe).layout_hash) == _HEX64
        int(_selected(l1_universe).token_type_schema_hash, 16)
        int(_selected(l1_universe).layout_hash, 16)

    def test_every_level_carries_token_spec(self, l1_universe):
        for name in l1_universe.available_levels:
            level = l1_universe.get_level(name)
            assert level.token_spec is not None, name
            assert level.token_type_schema_hash and level.layout_hash, name

    def test_every_level_carries_meter_runtime_declarations_matching_its_token_slots(self, l1_universe):
        for name in l1_universe.available_levels:
            level = l1_universe.get_level(name)
            meter_type = level.token_spec.get_type("meter")
            bindings = meter_type.slot_bindings
            assert tuple(meter.name for meter in level.meter_declarations) == tuple(binding.filler_ref for binding in bindings), name
            assert tuple(meter_signature(meter) for meter in level.meter_declarations) == tuple(
                tuple(context[PAYLOAD_SCHEMAS["meter"].index(feature)] for feature in METER_SIGNATURE_FEATURES)
                for context in meter_type.slot_context_payloads
            ), name

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
        assert _selected(effects_universe).token_spec.get_type("effect").capacity > 0

    def test_no_budget_advisory_survives(self, effects_universe):
        assert not any("max_active_effects" in a for a in _selected(effects_universe).token_advisories)

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
                            "reapply_policy": "renew",
                            "observable": True,
                            "on_spawn": [],
                            "on_tick": [],
                            "on_despawn": [],
                            "on_interrupt": [],
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
        assert _selected(l1_universe).token_spec.get_type("effect").capacity == 0


class TestTransferContractAcrossPacks:
    def test_type_schema_hash_is_engine_wide(self, l1_universe, effects_universe):
        # The transfer contract hashes type SCHEMAS, not capacities: any two universes
        # compiled by this engine with the full roster share it (spec §1 first invariant —
        # entity variation goes into token count, never payload width).
        assert _selected(l1_universe).token_type_schema_hash == _selected(effects_universe).token_type_schema_hash

    def test_layout_hash_is_universe_specific(self, l1_universe, effects_universe):
        assert _selected(l1_universe).layout_hash != _selected(effects_universe).layout_hash

    def test_type_schema_is_cross_rank_while_compact_layout_is_rank_specific(self):
        authorities = (
            (Path("configs/trial002_money_log_gdp"), "L0_simple", 2),
            (Path("configs/differential/div003_cubic_partial"), "L2_partial_observability", 3),
            (Path("configs/aspatial_test"), "L0", 0),
        )
        levels = tuple(
            UniverseCompiler().compile(path, primary_level=level_name, use_cache=False).get_level(level_name)
            for path, level_name, _rank in authorities
        )

        assert tuple(level.token_spec.position_rank for level in levels) == tuple(rank for _path, _level, rank in authorities)
        assert len({level.token_type_schema_hash for level in levels}) == 1
        assert len({level.layout_hash for level in levels}) == len(authorities)


def _spec_with(meter_refs: tuple[str, ...], *, item_capacity: int = 0) -> TokenSpec:
    types = []
    for type_name in TOKEN_TYPE_ROSTER:
        if type_name == "self":
            bindings = (SlotBinding(slot_index=0, filler_kind="static", filler_ref="self"),)
        elif type_name == "meter":
            bindings = tuple(
                SlotBinding(
                    slot_index=i,
                    filler_kind="static",
                    filler_ref=ref,
                )
                for i, ref in enumerate(meter_refs)
            )
        elif type_name == "item":
            bindings = tuple(SlotBinding(slot_index=i, filler_kind="dynamic", filler_ref=f"item:{i}") for i in range(item_capacity))
        else:
            bindings = ()
        contexts = () if type_name == "effect" else tuple((0.0,) * len(PAYLOAD_SCHEMAS[type_name]) for _ in bindings)
        types.append(
            build_token_type(
                type_name,
                bindings,
                slot_context_payloads=contexts,
                effect_catalog_contexts=(),
            )
        )
    return TokenSpec(types=tuple(types), position_rank=2, transport_version="compact-1")


class TestHashNarrowness:
    """PDR-0033: each hash moves exactly when its declared content moves."""

    def test_equal_specs_hash_equal(self):
        a = _spec_with(("energy", "health"))
        b = _spec_with(("energy", "health"))
        assert compute_token_type_schema_hash(a) == compute_token_type_schema_hash(b)
        assert compute_token_layout_hash(a) == compute_token_layout_hash(b)

    def test_layout_payload_excludes_fixed_projected_schema_identity(self):
        payload = canonical_token_layout(_spec_with(("energy",)))

        assert set(payload) == {"transport_version", "position_rank", "total_dims", "types"}
        assert all(
            set(token_type)
            == {
                "type_name",
                "dynamic_features",
                "capacity",
                "slot_binding_refs",
                "effect_catalog_context_refs",
            }
            for token_type in payload["types"]
        )

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

    def test_slot_context_moves_observation_hash_only(self):
        # Fixed context is observation content, not compact layout or projected type schema.
        base = _spec_with(())
        context_a = (0.5,) + (0.0,) * (len(PAYLOAD_SCHEMAS["meter"]) - 1)
        context_b = (0.0,) * len(PAYLOAD_SCHEMAS["meter"])
        meter_a = TokenTypeSchema(
            type_name="meter",
            payload_features=PAYLOAD_SCHEMAS["meter"],
            capacity=1,
            slot_bindings=(SlotBinding(slot_index=0, filler_kind="static", filler_ref="energy"),),
            slot_context_payloads=(context_a,),
            effect_catalog_contexts=(),
        )
        meter_b = TokenTypeSchema(
            type_name="meter",
            payload_features=PAYLOAD_SCHEMAS["meter"],
            capacity=1,
            slot_bindings=(SlotBinding(slot_index=0, filler_kind="static", filler_ref="energy"),),
            slot_context_payloads=(context_b,),
            effect_catalog_contexts=(),
        )
        spec_a = TokenSpec(types=(base.types[0], meter_a) + base.types[2:], position_rank=2, transport_version="compact-1")
        spec_b = TokenSpec(types=(base.types[0], meter_b) + base.types[2:], position_rank=2, transport_version="compact-1")
        assert compute_token_layout_hash(spec_a) == compute_token_layout_hash(spec_b)
        assert compute_token_type_schema_hash(spec_a) == compute_token_type_schema_hash(spec_b)
        assert compute_observation_schema_hash(spec_a) != compute_observation_schema_hash(spec_b)

    def test_roster_subset_moves_type_schema(self):
        # A universe instantiating fewer types IS a different type schema.
        full = _spec_with(())
        subset = TokenSpec(types=full.types[:3], position_rank=2, transport_version="compact-1")
        assert compute_token_type_schema_hash(full) != compute_token_type_schema_hash(subset)
        assert compute_token_layout_hash(full) != compute_token_layout_hash(subset)

    def test_noncanonical_encoding_version_refuses(self):
        a = _spec_with(())
        with pytest.raises(ValueError, match="encoding_version"):
            TokenSpec(types=a.types, position_rank=2, transport_version="compact-1", encoding_version="token-9.9-test")


class TestSerialization:
    def test_round_trip_preserves_token_block(self, effects_universe, tmp_path):
        cache_path = tmp_path / "u.msgpack"
        effects_universe.save_to_cache(cache_path)
        restored = CompiledUniverse.load_from_cache(cache_path)
        assert _selected(restored).token_spec == _selected(effects_universe).token_spec
        assert _selected(restored).token_type_schema_hash == _selected(effects_universe).token_type_schema_hash
        assert _selected(restored).layout_hash == _selected(effects_universe).layout_hash
        assert _selected(restored).token_advisories == _selected(effects_universe).token_advisories
        for name in effects_universe.available_levels:
            assert restored.get_level(name).token_spec == effects_universe.get_level(name).token_spec
            assert restored.get_level(name).meter_declarations == effects_universe.get_level(name).meter_declarations

    def test_round_trip_recomputes_identical_hashes(self, effects_universe, tmp_path):
        cache_path = tmp_path / "u.msgpack"
        effects_universe.save_to_cache(cache_path)
        restored = CompiledUniverse.load_from_cache(cache_path)
        assert compute_token_type_schema_hash(_selected(restored).token_spec) == _selected(restored).token_type_schema_hash
        assert compute_token_layout_hash(_selected(restored).token_spec) == _selected(restored).layout_hash

    def test_stale_previous_token_artifact_refuses(self, effects_universe, tmp_path):
        payload = effects_universe.to_dict()
        payload["compiled_schema_version"] = "1.23"
        stale_path = tmp_path / "stale.msgpack"
        stale_path.write_bytes(msgpack.packb(payload, use_bin_type=True))
        with pytest.raises(ValueError, match="schema mismatch") as excinfo:
            CompiledUniverse.load_from_cache(stale_path)
        assert "1.23" in str(excinfo.value)
        assert COMPILED_SCHEMA_VERSION in str(excinfo.value)

    def test_missing_level_token_block_refuses(self, effects_universe):
        payload = effects_universe.to_dict()
        primary_level = effects_universe.metadata.primary_level
        payload["all_levels"][primary_level].pop("token_spec")
        with pytest.raises(ValueError, match=f"missing required field 'all_levels.{primary_level}.token_spec'"):
            CompiledUniverse.from_dict(payload)

    def test_tampered_payload_schema_refuses(self, effects_universe):
        # The artifact is self-describing: a cache whose payload features disagree with
        # the running engine's schema refuses on load (spec §1 fixed-width invariant).
        payload = effects_universe.to_dict()
        payload["all_levels"][effects_universe.metadata.primary_level]["token_spec"]["types"][1]["payload_features"] = [
            "not_the_engine_schema"
        ]
        with pytest.raises(ValueError, match="does not match the engine constant"):
            CompiledUniverse.from_dict(payload)


def _env_stub(*names_and_types: tuple[str, str]):
    """Minimal EnvConfigV21 stand-in: `variable_element_bindings` reads only
    `environment.environment.variables[*].name / .semantic_type`."""
    return SimpleNamespace(environment=SimpleNamespace(variables=[SimpleNamespace(name=n, semantic_type=t) for n, t in names_and_types]))


def _variable_def(
    name: str,
    *,
    dims: int | None = None,
    normalization: NormalizationSpec | None,
    default: object = 0.0,
    initial_value_mode: str | None = None,
    initial_value_params: dict[str, float] | None = None,
) -> VariableDef:
    return VariableDef(
        id=name,
        scope="agent",
        type="vecNf" if dims and dims > 1 else "scalar",
        dims=dims,
        lifetime="tick",
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        default=[0.0] * dims if dims and dims > 1 and default == 0.0 else default,
        description=name,
        normalization=normalization,
        initial_value_mode=initial_value_mode,
        initial_value_params=initial_value_params,
    )


_BOUNDED = NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=True)


class TestVariableElementBindings:
    """Direct-call coverage of `variable_element_bindings`. Every branch that ADVISED
    while the token path ran alongside the old one is a compile REFUSAL since the cut."""

    def test_passing_declarations_bind_slots_in_registry_order(self):
        env = _env_stub(("temp", "custom"), ("wind", "custom"))
        defs = (
            _variable_def("temp", normalization=_BOUNDED),
            _variable_def("wind", dims=3, normalization=NormalizationSpec(kind="minmax", min=0.0, max=10.0, clip=True)),
        )
        bindings = variable_element_bindings(env, None, defs, item_capacity_value=0)
        assert [b.filler_ref for b in bindings] == ["temp", "wind[0]", "wind[1]", "wind[2]"]
        assert [b.slot_index for b in bindings] == [0, 1, 2, 3]
        assert all(b.filler_kind == "static" for b in bindings)
        assert all(not hasattr(binding, "static_signature") for binding in bindings)
        # The bound set constructs a live variable_element type at the derived capacity.
        assert (
            build_token_type(
                "variable_element",
                bindings,
                slot_context_payloads=tuple((0.0,) * len(PAYLOAD_SCHEMAS["variable_element"]) for _ in bindings),
                effect_catalog_contexts=(),
            ).capacity
            == 4
        )

    def test_unnormalized_variable_refuses(self):
        env = _env_stub(("raw_var", "custom"))
        defs = (_variable_def("raw_var", normalization=None),)
        with pytest.raises(ValueError, match="declares no normalization"):
            variable_element_bindings(env, None, defs, item_capacity_value=0)

    def test_unbounded_kind_refuses_with_the_boundedness_rule(self):
        env = _env_stub(("z", "custom"))
        defs = (_variable_def("z", normalization=NormalizationSpec(kind="zscore", mean=0.0, std=1.0)),)
        with pytest.raises(ValueError, match="bounded normalization kind"):
            variable_element_bindings(env, None, defs, item_capacity_value=0)

    def test_rank_scaled_refuses_at_exposure(self):
        env = _env_stub(("r", "custom"))
        defs = (_variable_def("r", normalization=NormalizationSpec(kind="rank_scaled")),)
        with pytest.raises(ValueError, match="rank_scaled"):
            variable_element_bindings(env, None, defs, item_capacity_value=0)

    def test_indistinguishable_pair_refuses_naming_both(self):
        # Identical declarations apart from the id: identical static signatures.
        env = _env_stub(("twin_a", "custom"), ("twin_b", "custom"))
        defs = (_variable_def("twin_a", normalization=_BOUNDED), _variable_def("twin_b", normalization=_BOUNDED))
        with pytest.raises(ValueError, match="indistinguishable") as excinfo:
            variable_element_bindings(env, None, defs, item_capacity_value=0)
        assert "twin_a" in str(excinfo.value) and "twin_b" in str(excinfo.value)

    def test_unexposed_variable_binds_nothing(self):
        # Explicit exposure: a registry variable no environment.yaml or profile exposure
        # names is UNEXPOSED and occupies no slot (the fail-open default is deleted).
        defs = (_variable_def("hidden", normalization=None),)
        assert variable_element_bindings(_env_stub(), None, defs, item_capacity_value=0) == ()

    def test_exposed_variable_without_explicit_default_refuses(self):
        env = _env_stub(("implicit", "custom"))
        defs = (_variable_def("implicit", normalization=_BOUNDED, default=None),)

        with pytest.raises(ValueError, match=r"implicit.*explicit declared default"):
            variable_element_bindings(env, None, defs, item_capacity_value=0)

    @pytest.mark.parametrize(
        ("mode", "params"),
        (
            ("zeros", None),
            (None, {"unused": 1.0}),
            ("ones", {"unused": 1.0}),
        ),
    )
    def test_exposed_variable_with_residual_initializer_surface_refuses(
        self,
        mode: str | None,
        params: dict[str, float] | None,
    ):
        env = _env_stub(("parallel_init", "custom"))
        defs = (
            _variable_def(
                "parallel_init",
                normalization=_BOUNDED,
                initial_value_mode=mode,
                initial_value_params=params,
            ),
        )

        with pytest.raises(ValueError, match=r"parallel_init.*initial_value_mode.*initial_value_params"):
            variable_element_bindings(env, None, defs, item_capacity_value=0)


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

        payload = yaml.safe_load(Path("configs/test/token_set_smoke/brain.yaml").read_text())
        assert payload["architecture"]["token_set"]["aggregator"]["type"] == "mean"
        return BrainConfig.model_validate(payload)

    def _build(self, l1_universe, bars, brain):
        from townlet.config.affordances_v2_config import AffordancesV2Config
        from townlet.config.environment_config import MeterConfig as EnvironmentMeterConfig

        environment = l1_universe.environment.model_copy(
            update={
                "environment": l1_universe.environment.environment.model_copy(
                    update={
                        "meters": [
                            EnvironmentMeterConfig(
                                name=meter.name,
                                description=meter.name,
                                range_type={"kind": "minmax", "clip": True},
                            )
                            for meter in bars.meters
                        ]
                    }
                )
            }
        )
        compiler = ObservationCompiler()
        meter_declarations = compiler.compile_meter_declarations(environment, bars)
        return compiler.build_token_spec(
            l1_universe.stratum,
            meter_declarations,
            AffordancesV2Config(version="1.0", affordances=[], modulations=[]),
            None,
            None,
            environment,
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

    def test_non_token_set_brain_never_census_advises(self, l1_universe):
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
        assert "compact row" in out
        assert "fixed network boundary" in out
        assert "compact total" in out
        assert "fixed boundary" in out
        # effects_smoke's budget advisory is a refusal since the cut, so it carries none.
        assert "ADVISORY" not in out

    def test_inspect_json_carries_census(self, effects_universe, tmp_path, capsys):
        import json

        from townlet.universe.__main__ import main

        artifact = tmp_path / "universe.msgpack"
        effects_universe.save_to_cache(artifact)
        assert main(["inspect", str(artifact), "--format", "json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["token_census"] == _selected(effects_universe).token_spec.census
        assert payload["token_compact_total_dims"] == _selected(effects_universe).token_spec.total_dims
        assert payload["token_fixed_boundary_total_dims"] == _selected(effects_universe).token_spec.fixed_total_dims
        assert payload["token_type_schema_hash"] == _selected(effects_universe).token_type_schema_hash
        assert payload["layout_hash"] == _selected(effects_universe).layout_hash
