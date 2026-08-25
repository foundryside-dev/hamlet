"""Compiler emission of the TokenSpec artifact (unit 3 Task 7 — ALONGSIDE ruling).

The pipeline compiles a TokenSpec per level beside the unchanged ObservationSpec family:
nothing here may move any pre-existing hash (config_hash, observation_schema_hash, the
vfs_hash composition). The two NEW hashes — `token_type_schema_hash` (transfer contract)
and `layout_hash` (flat-net contract) — join the inventory with PDR-0033 narrowness:
each moves exactly when its declared content moves, both directions pinned below.
"""

from pathlib import Path

import msgpack
import pytest

from townlet.universe.compiled import COMPILED_SCHEMA_VERSION, CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto.token_spec import (
    PAYLOAD_SCHEMAS,
    TOKEN_TYPE_ROSTER,
    SlotBinding,
    TokenSpec,
    TokenTypeSchema,
    build_token_type,
)
from townlet.vfs.schema_hashes import (
    compute_token_layout_hash,
    compute_token_type_schema_hash,
)

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


class TestEffectCapacityAdvisory:
    """Alongside ruling: no `max_active_effects` surface exists yet, so a non-empty
    effect catalog compiles at capacity 0 with an ADVISORY (Task 10 makes it a refusal)."""

    def test_effects_smoke_compiles_with_capacity_zero(self, effects_universe):
        assert effects_universe.token_spec.get_type("effect").capacity == 0

    def test_effects_smoke_records_budget_advisory(self, effects_universe):
        budget_notes = [a for a in effects_universe.token_advisories if "max_active_effects" in a]
        assert len(budget_notes) == 1
        assert "capacity 0" in budget_notes[0]
        assert "Task 10" in budget_notes[0]

    def test_empty_catalog_gets_no_effect_advisory(self, l1_universe):
        assert not any("max_active_effects" in a for a in l1_universe.token_advisories)


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

    def test_stale_1_20_artifact_refuses(self, effects_universe, tmp_path):
        payload = effects_universe.to_dict()
        payload["compiled_schema_version"] = "1.20"
        stale_path = tmp_path / "stale.msgpack"
        stale_path.write_bytes(msgpack.packb(payload, use_bin_type=True))
        with pytest.raises(ValueError, match="schema mismatch") as excinfo:
            CompiledUniverse.load_from_cache(stale_path)
        assert "1.20" in str(excinfo.value)
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
        assert "ADVISORY" in out  # effects_smoke carries the budget advisory

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
