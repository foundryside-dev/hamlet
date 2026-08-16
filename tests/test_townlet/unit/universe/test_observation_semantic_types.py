"""`semantic_type` has ONE closed vocabulary and the author's declaration is authoritative
(PDR-0047, DIV-005, hamlet-2fe1c34ebb).

Before this cut the field had three disagreeing vocabularies and no authority: five schema
classes declared `Literal[bars, spatial, affordance, temporal, custom]` with `default="custom"`,
the compiler hardcoded a literal per block INCLUDING `"effects"` (outside the declared set —
nothing caught it because the DTO field was `str | None`), the VFS mirror silently remapped
`effects -> custom` so ONE field carried TWO values, and no author declaration reached any
compiled field.

Rules pinned here (PDR-0047):
  1. the vocabulary is closed and defined once;
  2. where an author declares, the compiler obeys;
  3. the compiler emits only from the same set — a value an author may not write is a value
     the compiler may not emit, and (the reserved case) `bars` is the meter block, so an
     authored variable may not join it.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import get_args

import pytest
import yaml
from pydantic import ValidationError

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.config.environment_config import VariableConfig
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto.observation_spec import ObservationField as CompiledObservationField
from townlet.vfs.schema import ObservationField as VFSObservationField
from townlet.vfs.schema import VariableDef
from townlet.vfs.semantic_type import SEMANTIC_GROUP_ORDER, SEMANTIC_TYPES, SemanticType

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PACK = REPO_ROOT / "configs" / "default_curriculum"
EFFECTS_PACK = REPO_ROOT / "configs" / "test" / "effects_smoke"


# --------------------------------------------------------------------------- rule 1: one closed set


class TestOneClosedVocabulary:
    def test_the_vocabulary_is_exactly_these_six_members(self) -> None:
        # `effects` is ADMITTED deliberately (DIV-005 / PDR-0016): it names a real compiled
        # block with its own group slice. Adding a seventh member is a decision, not a drive-by.
        assert SEMANTIC_TYPES == frozenset({"bars", "spatial", "affordance", "effects", "temporal", "custom"})
        assert frozenset(get_args(SemanticType)) == SEMANTIC_TYPES

    def test_group_order_is_a_permutation_of_the_vocabulary(self) -> None:
        assert frozenset(SEMANTIC_GROUP_ORDER) == SEMANTIC_TYPES
        assert len(SEMANTIC_GROUP_ORDER) == len(SEMANTIC_TYPES)

    @pytest.mark.parametrize(
        "model, field_name",
        [
            (VariableConfig, "semantic_type"),
            (VFSObservationField, "semantic_type"),
        ],
    )
    def test_every_declaring_schema_references_the_one_vocabulary(self, model, field_name: str) -> None:
        annotation = model.model_fields[field_name].annotation
        assert frozenset(get_args(annotation)) == SEMANTIC_TYPES, (
            f"{model.__name__}.{field_name} declares its own vocabulary {get_args(annotation)!r}; "
            "it must reference townlet.vfs.semantic_type.SemanticType"
        )

    def test_the_compiled_dto_rejects_a_value_outside_the_vocabulary(self) -> None:
        # The DTO used to be `str | None`, which is how the compiler emitted `"effects"`
        # unnoticed for months. Now the DTO constrains the compiler too.
        with pytest.raises(ValueError, match="semantic_type"):
            CompiledObservationField(
                uuid=None,
                name="obs_position",
                type="vector",
                dims=2,
                start_index=0,
                end_index=2,
                scope="agent",
                description="pos",
                semantic_type="position",  # type: ignore[arg-type]
            )

    def test_the_compiled_dto_requires_semantic_type(self) -> None:
        with pytest.raises(TypeError):
            CompiledObservationField(  # type: ignore[call-arg]
                uuid=None,
                name="obs_position",
                type="vector",
                dims=2,
                start_index=0,
                end_index=2,
                scope="agent",
                description="pos",
            )


# --------------------------------------------------------------- no default, no orphaned declaration


class TestNoDefaultAndNoOrphanedDeclaration:
    def test_environment_variable_requires_semantic_type(self) -> None:
        payload = {
            "name": "deficit_energy",
            "type": "scalar",
            "dims": 1,
            "scope": "agent",
            "description": "x",
            "normalization": {"method": "normalize", "clip": False, "range": [0.0, 1.0]},
        }
        with pytest.raises(ValidationError, match="semantic_type"):
            VariableConfig.model_validate(payload)
        VariableConfig.model_validate({**payload, "semantic_type": "custom"})
        with pytest.raises(ValidationError, match="semantic_type"):
            VariableConfig.model_validate({**payload, "semantic_type": "meter"})

    def test_vfs_observation_field_requires_semantic_type(self) -> None:
        payload = {"id": "f", "source_variable": "v", "exposed_to": ["agent"], "shape": []}
        with pytest.raises(ValidationError, match="semantic_type"):
            VFSObservationField.model_validate(payload)
        VFSObservationField.model_validate({**payload, "semantic_type": "custom"})

    def test_variable_def_no_longer_carries_a_semantic_type(self) -> None:
        # A state variable has no observation grouping; the grouping lives on the observation
        # field that reads it. The old field on VariableDef reached nothing.
        payload = {
            "id": "trust",
            "scope": "pair",
            "type": "scalar",
            "lifetime": "episode",
            "readable_by": ["agent"],
            "writable_by": ["engine"],
            "default": 0.5,
            "semantic_type": "custom",
        }
        with pytest.raises(ValidationError, match="semantic_type"):
            VariableDef.model_validate(payload)

    @pytest.mark.parametrize("cls_name", ["GlobalVFSVariableConfig", "AgentVFSVariableConfig"])
    def test_global_and_agent_profile_variables_require_a_semantic_type(self, cls_name: str) -> None:
        # PDR-0075: each exposed global/agent profile variable compiles to its OWN observation
        # field, so the declaration reaches the tensor and is REQUIRED — no default, no None.
        import townlet.config.vfs_profiles_config as m

        cls = getattr(m, cls_name)
        payload = {"name": "day_count", "type": "int", "initial_value": 0}
        with pytest.raises(ValidationError, match="semantic_type"):
            cls.model_validate(payload)
        with pytest.raises(ValidationError, match="semantic_type"):
            cls.model_validate({**payload, "semantic_type": "not-a-member"})
        assert cls.model_validate({**payload, "semantic_type": "temporal"}).semantic_type == "temporal"

    def test_item_profile_variables_still_carry_no_semantic_type(self) -> None:
        # Item variables are observed through the single `obs_item_slots` feature (slot ×
        # profile-position), so a per-variable group could reach nothing — and a declaration
        # that can reach nothing is removed, not defaulted (PDR-0066, PDR-0075;
        # hamlet-1ad6383186 holds the layout question).
        from townlet.config.vfs_profiles_config import ItemVFSVariableConfig

        payload = {"name": "freshness", "type": "float", "initial_value": 1.0, "semantic_type": "custom"}
        with pytest.raises(ValidationError, match="semantic_type"):
            ItemVFSVariableConfig.model_validate(payload)


# --------------------------------------------------------------- rules 2 + 3 in the compiler


def _compile(pack: Path, level: str):
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _copy_pack(src: Path, tmp_path: Path) -> Path:
    dest = tmp_path / src.name
    shutil.copytree(src, dest)
    return dest


def _set_variable_semantic(pack: Path, variable_name: str, semantic: str) -> None:
    env_path = pack / "environment.yaml"
    data = yaml.safe_load(env_path.read_text())
    for var in data["environment"]["variables"]:
        if var["name"] == variable_name:
            var["semantic_type"] = semantic
            break
    else:
        raise AssertionError(f"{variable_name} not in {env_path}")
    env_path.write_text(yaml.safe_dump(data, sort_keys=False))


class TestCompilerEmitsOnlyFromTheVocabularyAndMirrorsFaithfully:
    @pytest.mark.parametrize("pack, level", [(DEFAULT_PACK, "L1_full_observability"), (EFFECTS_PACK, "L0_effects")])
    def test_every_compiled_field_is_in_the_vocabulary(self, pack: Path, level: str) -> None:
        universe = _compile(pack, level)
        off = [(f.name, f.semantic_type) for f in universe.observation_spec.fields if f.semantic_type not in SEMANTIC_TYPES]
        assert off == []

    def test_the_vfs_mirror_carries_the_field_value_not_a_remap(self) -> None:
        # At the oracle tag `obs_effects` was `effects` on the spec and `custom` on the mirror
        # (DIV-005: one field, two values). The remap is gone.
        universe = _compile(EFFECTS_PACK, "L0_effects")
        spec = {f.name: f.semantic_type for f in universe.observation_spec.fields}
        mirror = {f.id: f.semantic_type for f in universe.vfs_observation_fields}
        assert spec["obs_effects"] == "effects"
        assert mirror == spec

    def test_default_curriculum_layout_is_unchanged_by_the_cut(self) -> None:
        # The stable partition by group order is the IDENTITY on today's layout: every shipped
        # pack already emits its blocks in group order. Pinning the L1 field order and slices
        # exactly as measured at the pre-cut tree (fb60d581) is what makes that a fact.
        universe = _compile(DEFAULT_PACK, "L1_full_observability")
        assert [f.name for f in universe.observation_spec.fields] == [
            "obs_grid_encoding",
            "obs_local_window",
            "obs_position",
            "obs_velocity",
            "obs_meter_energy",
            "obs_meter_health",
            "obs_meter_satiation",
            "obs_meter_hygiene",
            "obs_meter_money",
            "obs_meter_fitness",
            "obs_meter_mood",
            "obs_meter_social",
            "obs_affordance_at_position",
            "deficit_energy",
            "deficit_satiation",
            "time_since_last_eat",
            "time_since_last_sleep",
            "obs_temporal",
        ]
        groups = {k: (v.start, v.stop) for k, v in universe.observation_activity.group_slices.items()}
        assert groups == {"spatial": (0, 93), "bars": (93, 101), "affordance": (101, 116), "custom": (116, 120), "temporal": (120, 124)}
        assert universe.observation_spec.total_dims == 124


class TestTheAuthorDeclarationIsAuthoritative:
    def test_a_declared_temporal_variable_lands_in_the_temporal_group(self, tmp_path: Path) -> None:
        # Rule 2. `time_since_last_eat` is an agent clock; an author may say so. The compiler
        # emits the declared value and lays the field out with its group, so the groups stay
        # contiguous and the runtime (which assembles by field order) needs no special case.
        pack = _copy_pack(DEFAULT_PACK, tmp_path)
        _set_variable_semantic(pack, "time_since_last_eat", "temporal")
        universe = _compile(pack, "L1_full_observability")
        by_name = {f.name: f for f in universe.observation_spec.fields}
        assert by_name["time_since_last_eat"].semantic_type == "temporal"
        temporal = universe.observation_activity.group_slices["temporal"]
        assert temporal.start <= by_name["time_since_last_eat"].start_index < temporal.stop
        # Group order held: custom then temporal, and the temporal group grew by exactly one dim.
        custom = universe.observation_activity.group_slices["custom"]
        assert custom.stop == temporal.start
        assert temporal.stop - temporal.start == 4 + 1
        assert universe.observation_spec.total_dims == 124

        # And the RUNTIME agrees: the encoder assembles by walking the compiled fields in
        # order and resolves each by its source variable, so the moved field's value lands
        # at the compiled offset. Drive the variable to a known value and read it back at
        # `start_index` — a wrong offset would read a neighbour (a temporal feature, or a
        # `custom` variable) instead.
        import torch

        from townlet.environment.vectorized_env import VectorizedHamletEnv

        env = VectorizedHamletEnv(universe=universe, level_name="L1_full_observability", num_agents=2, device=torch.device("cpu"))
        env.reset()
        moved = by_name["time_since_last_eat"]
        env.vfs_registry.set("time_since_last_eat", torch.tensor([37.0, 61.0]), writer="engine")
        obs = env._get_observations()
        assert obs.shape == (2, 124)
        # The pack declares `normalize` over [0, 100] for this variable.
        assert torch.allclose(obs[:, moved.start_index], torch.tensor([0.37, 0.61]), atol=1e-6)

    def test_a_declared_bars_variable_is_a_compile_error(self, tmp_path: Path) -> None:
        # Rule 3, reserved case: `bars` is the meter block — the runtime publishes meter columns
        # into every bars-group field and would raise at the first observation. That failure
        # belongs at compile time, with the rule in the message.
        pack = _copy_pack(DEFAULT_PACK, tmp_path)
        _set_variable_semantic(pack, "deficit_energy", "bars")
        with pytest.raises(Exception, match="bars"):
            _compile(pack, "L1_full_observability")

    def test_a_pack_omitting_semantic_type_fails_to_compile(self, tmp_path: Path) -> None:
        pack = _copy_pack(DEFAULT_PACK, tmp_path)
        env_path = pack / "environment.yaml"
        data = yaml.safe_load(env_path.read_text())
        del data["environment"]["variables"][0]["semantic_type"]
        env_path.write_text(yaml.safe_dump(data, sort_keys=False))
        with pytest.raises(Exception, match="semantic_type"):
            _compile(pack, "L1_full_observability")


class TestPreparedPacksDeclareIt:
    def test_the_test_helper_pack_compiles(self, tmp_path: Path) -> None:
        # The helper-built pack is copied from default_curriculum's files, so it inherits the
        # declaration; this pins that the helper did not grow its own stale environment.yaml.
        pack = prepare_config_dir(tmp_path, name="semantic")
        universe = _compile(pack, PRIMARY_LEVEL_NAME)
        assert all(f.semantic_type in SEMANTIC_TYPES for f in universe.observation_spec.fields)
