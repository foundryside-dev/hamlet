"""Compiled observation fields carry a typed FEATURE, and the runtime dispatches on it — not on
the field's name (WS-4 unit 4, hamlet-39e1fe3c6d; the general fix PDR-0075 named).

Before this cut the observation encoder had nine sync steps each finding its field by a
hardcoded `obs_<x>` string, the meter step parsed the meter's name back out of the field's
name, `RecurrentSpatialQNetwork` located its slices by literal name, two demo sites sized the
vision window from a field literally called `obs_local_window`, and the compiler decided
"feature or authored variable" by whether a field's NAME appeared in the authored-variable
name sets. Every one of those is the PDR-0045 shape.

Pinned here:
  1. the DTO requires `feature` from ONE closed vocabulary; a `meter` field must name its
     meter in `feature_ref` and nothing else may carry one;
  2. the compiler stamps every emitted field — the four shipped shapes (default_curriculum
     full/partial/temporal, effects_smoke's global profile variable, items_smoke's item
     slots) — and the meter's `feature_ref` IS the meter's name;
  3. the runtime encoder, the recurrent network and the demo entry points contain no
     `"obs_..."` name literal and no name-prefix parse; the encoder's dispatch table covers
     every engine-published member of the vocabulary; the recurrent network finds its blocks
     under any name (test_network_factory names them unconventionally on purpose).
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

from townlet.agent import networks as networks_module
from townlet.demo import live_inference as live_inference_module
from townlet.demo import runner as runner_module
from townlet.environment import observation_encoder as encoder_module
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compilers import observation as observation_compiler_module
from townlet.universe.dto import ObservationField, ObservationSpec
from townlet.universe.dto.observation_feature import (
    OBSERVATION_FEATURES,
    VARIABLE_FEATURE,
    ObservationFeature,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
CURRICULUM = REPO_ROOT / "configs" / "default_curriculum"
EFFECTS_PACK = REPO_ROOT / "configs" / "test" / "effects_smoke"
ITEMS_PACK = REPO_ROOT / "configs" / "test" / "items_smoke"


def _compile(pack: Path, level: str):
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _field(name: str, feature: str, **overrides) -> ObservationField:
    kwargs = dict(
        uuid=None,
        name=name,
        type="scalar",
        dims=1,
        start_index=0,
        end_index=1,
        scope="agent",
        description=name,
        semantic_type="custom",
        feature=feature,
    )
    kwargs.update(overrides)
    return ObservationField(**kwargs)  # type: ignore[arg-type]


# ------------------------------------------------------------------ 1. the DTO holds the compiler to the vocabulary


class TestTheDtoRequiresAFeature:
    def test_feature_is_required(self) -> None:
        with pytest.raises(TypeError):
            ObservationField(  # type: ignore[call-arg]
                uuid=None,
                name="x",
                type="scalar",
                dims=1,
                start_index=0,
                end_index=1,
                scope="agent",
                description="x",
                semantic_type="custom",
            )

    def test_feature_outside_the_vocabulary_is_rejected_with_the_rule(self) -> None:
        with pytest.raises(ValueError, match="closed vocabulary"):
            _field("x", "obs_position")

    def test_a_meter_field_must_name_its_meter(self) -> None:
        with pytest.raises(ValueError, match="names no meter"):
            _field("obs_meter_energy", "meter", semantic_type="bars")
        ok = _field("obs_meter_energy", "meter", semantic_type="bars", feature_ref="energy")
        assert ok.feature_ref == "energy"

    def test_only_a_meter_field_carries_a_referent(self) -> None:
        with pytest.raises(ValueError, match="names no referent"):
            _field("obs_temporal", "temporal", semantic_type="temporal", feature_ref="clock")

    def test_the_literal_type_and_the_frozenset_are_one_vocabulary(self) -> None:
        from typing import get_args

        assert frozenset(get_args(ObservationFeature)) == OBSERVATION_FEATURES
        assert VARIABLE_FEATURE in OBSERVATION_FEATURES

    def test_feature_is_not_part_of_the_field_identity(self) -> None:
        # The discriminator says who FILLS the field; it is engine plumbing, not ABI. Two
        # fields that differ only by feature share a UUID — deliberately, so this cut moves
        # no observation_field_uuids in any checkpoint and no provenance hash (PDR-0056:
        # measured at the harness, and this is the unit-level statement of the same claim).
        a = _field("x", "variable")
        b = _field("x", "temporal", semantic_type="custom")
        assert a.uuid == b.uuid


# ------------------------------------------------------------------ 2. the compiler stamps every field


class TestTheCompilerStampsEveryField:
    @pytest.mark.parametrize(
        ("pack", "level", "expected"),
        [
            # default_curriculum ships no effect catalog, so no `effects` block; its
            # environment.yaml variables are the `variable` fields.
            (
                CURRICULUM,
                "L1_full_observability",
                {"grid_encoding", "local_window", "position", "velocity", "meter", "affordance_at_position", "temporal", "variable"},
            ),
            (
                CURRICULUM,
                "L2_partial_observability",
                {"grid_encoding", "local_window", "position", "velocity", "meter", "affordance_at_position", "temporal", "variable"},
            ),
            # effects_smoke: an effect catalog AND an exposed global profile variable.
            (EFFECTS_PACK, "L0_effects", {"effects", "variable"}),
            # items_smoke: the one shipped pack whose item profiles reach the observation.
            (ITEMS_PACK, "L0_smoke", {"item_slots", "effects"}),
        ],
    )
    def test_the_expected_features_are_present(self, pack: Path, level: str, expected: set[str]) -> None:
        universe = _compile(pack, level)
        features = {f.feature for f in universe.observation_spec.fields}
        assert expected <= features, features - expected
        assert features <= OBSERVATION_FEATURES

    def test_a_meter_field_refers_to_its_meter_and_nothing_else_has_a_referent(self) -> None:
        universe = _compile(CURRICULUM, "L1_full_observability")
        meter_names = set(universe.metadata.meter_names)
        for f in universe.observation_spec.fields:
            if f.feature == "meter":
                assert f.feature_ref in meter_names, f.name
                assert f.semantic_type == "bars"
            else:
                assert f.feature_ref is None, f.name
        assert {f.feature_ref for f in universe.observation_spec.get_fields_by_feature("meter")} == meter_names

    def test_the_bars_group_and_the_meter_feature_are_the_same_set(self) -> None:
        # Two views of one fact: the semantic group says WHERE the meters are, the feature
        # says WHO fills them. They must agree, or one of them is lying.
        universe = _compile(CURRICULUM, "L3_temporal_mechanics")
        by_group = {f.name for f in universe.observation_spec.get_fields_by_semantic_type("bars")}
        by_feature = {f.name for f in universe.observation_spec.get_fields_by_feature("meter")}
        assert by_group == by_feature

    def test_variable_fields_get_no_engine_primitive_and_every_other_feature_gets_one(self) -> None:
        # `build_vfs_variables` mints one tick-lifetime, engine-written AGENT primitive per
        # engine-published feature and none for a `variable` field — the registry already
        # holds those (an env variable, or a profile variable under its own declared scope).
        # The decision reads `field.feature`; it used to test the field's NAME against the
        # authored-variable name sets.
        universe = _compile(EFFECTS_PACK, "L0_effects")
        ids = [v.id for v in universe.vfs_variables]
        by_id = {v.id: v for v in universe.vfs_variables}
        for f in universe.observation_spec.fields:
            assert ids.count(f.name) == 1, f.name
            var = by_id[f.name]
            if f.feature == VARIABLE_FEATURE:
                assert not (var.lifetime == "tick" and var.description.startswith("System observation primitive")), f.name
            else:
                assert var.scope == "agent" and var.writable_by == ["engine"] and var.lifetime == "tick", f.name
        # and the profile variable is held once, under ITS scope, not re-minted as a primitive
        assert by_id["day_count"].scope == "global"

    def test_single_instance_lookup_finds_the_window_under_any_name(self) -> None:
        universe = _compile(CURRICULUM, "L2_partial_observability")
        window = universe.observation_spec.get_single_field_by_feature("local_window")
        assert window is not None
        assert window.dims == 25  # 5x5, vision_range 2
        # renaming the field changes nothing about how it is found
        renamed = ObservationSpec.from_fields(
            [
                ObservationField(
                    uuid=f.uuid,
                    name=(f"renamed_{i}" if f is window else f.name),
                    type=f.type,
                    dims=f.dims,
                    start_index=f.start_index,
                    end_index=f.end_index,
                    scope=f.scope,
                    description=f.description,
                    semantic_type=f.semantic_type,
                    feature=f.feature,
                    feature_ref=f.feature_ref,
                    curriculum_active=f.curriculum_active,
                )
                for i, f in enumerate(universe.observation_spec.fields)
            ]
        )
        assert networks_module.recurrent_vision_window_side(renamed) == 5

    def test_the_prefix_inverse_is_gone(self) -> None:
        assert not hasattr(observation_compiler_module, "meter_name_from_observation_field")


# ------------------------------------------------------------------ 3. no consumer branches on a name


_NAME_LITERAL = re.compile(r"""["']obs_[a-z_]+["']""")


@pytest.mark.parametrize(
    "module",
    [encoder_module, networks_module, runner_module, live_inference_module],
    ids=lambda m: m.__name__,
)
def test_no_observation_consumer_carries_a_field_name_literal(module) -> None:
    src = inspect.getsource(module)
    # Strip docstrings and comments: the history is allowed to be TOLD; a name may not be
    # BRANCHED on. Anything left is code.
    code_only = re.sub(r'"""[\s\S]*?"""', "", src)
    code_only = "\n".join(line.split("#", 1)[0] for line in code_only.splitlines())
    hits = _NAME_LITERAL.findall(code_only)
    assert hits == [], f"{module.__name__} still names observation fields in code: {hits}"


def test_the_encoder_publishes_every_engine_feature_and_no_variable() -> None:
    publishers = encoder_module.ObservationEncoder._FEATURE_PUBLISHERS
    assert set(publishers) == OBSERVATION_FEATURES - {VARIABLE_FEATURE}


def test_the_encoder_dispatches_on_the_feature_not_the_name() -> None:
    src = inspect.getsource(encoder_module.ObservationEncoder._sync_observation_primitives_to_vfs)
    assert "field.feature" in src
    assert "field.name ==" not in src
    assert "startswith" not in src
