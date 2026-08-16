"""VFS profile variables compile to their own observation fields, read by scope, and the
runtime no longer knows the `obs_vfs` block by name (PDR-0075, DIV-006, hamlet-f0ed709ecf).

Before this cut every exposed profile variable was flattened into ONE compiled field `obs_vfs`
(one `custom` value for all of them, so the per-variable declaration DIV-005 removed could reach
nothing), and `ObservationEncoder._build_observation_field_from_vfs` branched on
`field_name != "obs_vfs"` — the name-branch shape PDR-0045 forbids.

Pinned here:
  1. one field per exposed global/agent profile variable, named after the variable, in its
     declared scope, carrying the AUTHOR'S semantic type — proven by execution: the value the
     registry holds lands at the compiled offset, in the declared group's slice;
  2. the item sub-block is ONE compiler-emitted feature, `obs_item_slots`, sized from the
     compiled VFS observation spec; item variables take no semantic type;
  3. `bars` and a name collision are compile errors naming the rule;
  4. no `obs_vfs` field, primitive, or name branch survives.
"""

from __future__ import annotations

import inspect
import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.environment import observation_encoder as encoder_module
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compilers.observation import ITEM_SLOTS_OBSERVATION_FIELD

REPO_ROOT = Path(__file__).resolve().parents[4]
EFFECTS_PACK = REPO_ROOT / "configs" / "test" / "effects_smoke"
ITEMS_PACK = REPO_ROOT / "configs" / "test" / "items_smoke"


def _compile(pack: Path, level: str):
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _copy_pack(src: Path, tmp_path: Path) -> Path:
    dest = tmp_path / src.name
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".compiled"))
    return dest


def _set_global_profile_var(pack: Path, name: str, **overrides) -> None:
    path = pack / "vfs_profiles.yaml"
    data = yaml.safe_load(path.read_text())
    for var in data["global_profile"]["variables"]:
        if var["name"] == name:
            var.update(overrides)
            break
    else:
        raise AssertionError(f"{name} not in {path}")
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def _add_agent_profile_var(pack: Path, **var) -> None:
    path = pack / "vfs_profiles.yaml"
    data = yaml.safe_load(path.read_text())
    if not data.get("agent_profile"):
        data["agent_profile"] = {"variables": []}
    data["agent_profile"]["variables"].append(var)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


# ------------------------------------------------------------------ 1. per-variable fields, by scope


class TestProfileVariablesCompileToTheirOwnFields:
    def test_a_global_profile_variable_is_its_own_field_in_the_declared_group(self, tmp_path: Path) -> None:
        # effects_smoke exposes one global variable, `day_count`. Declare it `temporal` and the
        # compiler must lay it out in the temporal slice; declare it `custom` (the shipped
        # pack) and it sits where the old block sat. Either way, ONE field named after it.
        pack = _copy_pack(EFFECTS_PACK, tmp_path)
        _set_global_profile_var(pack, "day_count", semantic_type="temporal")
        universe = _compile(pack, "L0_effects")
        by_name = {f.name: f for f in universe.observation_spec.fields}
        assert "obs_vfs" not in by_name
        field = by_name["day_count"]
        assert field.scope == "global"
        assert field.dims == 1
        assert field.semantic_type == "temporal"
        temporal = universe.observation_activity.group_slices["temporal"]
        assert temporal.start <= field.start_index < temporal.stop
        # total width is unchanged by the declaration — the group partition moves the field,
        # not the tensor size.
        assert universe.observation_spec.total_dims == _compile(EFFECTS_PACK, "L0_effects").observation_spec.total_dims

        # RUNTIME: the encoder reads the field by its source variable's declared scope
        # (global -> broadcast to the batch) and the value lands at the compiled offset.
        env = VectorizedHamletEnv(universe=universe, level_name="L0_effects", num_agents=3, device=torch.device("cpu"))
        env.reset()
        env.vfs_registry.set("day_count", torch.tensor(42.0), writer="engine")
        obs = env._get_observations()
        assert obs.shape == (3, universe.observation_spec.total_dims)
        assert torch.equal(obs[:, field.start_index], torch.tensor([42.0, 42.0, 42.0]))

    def test_an_agent_profile_variable_is_its_own_field_read_per_agent(self, tmp_path: Path) -> None:
        pack = _copy_pack(EFFECTS_PACK, tmp_path)
        _add_agent_profile_var(
            pack,
            name="motivation",
            semantic_type="custom",
            type="float",
            initial_value=0.5,
            exposed_to=["agent"],
        )
        universe = _compile(pack, "L0_effects")
        by_name = {f.name: f for f in universe.observation_spec.fields}
        field = by_name["motivation"]
        assert field.scope == "agent"
        assert field.semantic_type == "custom"
        env = VectorizedHamletEnv(universe=universe, level_name="L0_effects", num_agents=2, device=torch.device("cpu"))
        env.reset()
        env.vfs_registry.set("motivation", torch.tensor([0.25, 0.75]), writer="engine")
        obs = env._get_observations()
        assert torch.allclose(obs[:, field.start_index], torch.tensor([0.25, 0.75]))

    def test_no_primitive_is_minted_for_a_profile_backed_field(self) -> None:
        # The registry holds `day_count` once, as the GLOBAL profile variable — not also as an
        # engine-written agent primitive named after the field (which is what `obs_vfs` was).
        universe = _compile(EFFECTS_PACK, "L0_effects")
        by_id = {v.id: v for v in universe.vfs_variables}
        assert "obs_vfs" not in by_id
        assert by_id["day_count"].scope == "global"
        assert [v.id for v in universe.vfs_variables].count("day_count") == 1


# ------------------------------------------------------------------ 2. the item-slot feature


class TestTheItemSlotsFeature:
    def test_item_variables_are_observed_through_one_named_feature(self) -> None:
        universe = _compile(ITEMS_PACK, "L0_smoke")
        by_name = {f.name: f for f in universe.observation_spec.fields}
        assert "obs_vfs" not in by_name
        feature = by_name[ITEM_SLOTS_OBSERVATION_FIELD]
        assert feature.dims == universe.vfs_observation_spec.item_vfs_dim
        assert feature.semantic_type == "custom"
        # the feature IS a primitive: engine-written, read back through the generic path
        by_id = {v.id: v for v in universe.vfs_variables}
        assert by_id[ITEM_SLOTS_OBSERVATION_FIELD].writable_by == ["engine"]

    def test_the_feature_name_is_one_shared_symbol_not_two_literals(self) -> None:
        # The encoder imports the compiler's constant; a second literal would be the drift
        # the sibling primitives already suffer from.
        src = inspect.getsource(encoder_module)
        assert "ITEM_SLOTS_OBSERVATION_FIELD" in src
        assert '"obs_item_slots"' not in src


# ------------------------------------------------------------------ 3. compile errors, with the rule


class TestCompileErrorsNameTheRule:
    def test_bars_is_reserved_on_profile_variables_too(self, tmp_path: Path) -> None:
        pack = _copy_pack(EFFECTS_PACK, tmp_path)
        _set_global_profile_var(pack, "day_count", semantic_type="bars")
        with pytest.raises(Exception, match="bars"):
            _compile(pack, "L0_effects")

    def test_omitting_semantic_type_on_a_global_variable_fails_to_load(self, tmp_path: Path) -> None:
        pack = _copy_pack(EFFECTS_PACK, tmp_path)
        path = pack / "vfs_profiles.yaml"
        data = yaml.safe_load(path.read_text())
        del data["global_profile"]["variables"][0]["semantic_type"]
        path.write_text(yaml.safe_dump(data, sort_keys=False))
        with pytest.raises(Exception, match="semantic_type"):
            _compile(pack, "L0_effects")

    def test_a_profile_variable_colliding_with_a_compiler_block_is_a_compile_error(self, tmp_path: Path) -> None:
        pack = _copy_pack(EFFECTS_PACK, tmp_path)
        _add_agent_profile_var(
            pack,
            name="obs_effects",
            semantic_type="custom",
            type="float",
            initial_value=0.0,
            exposed_to=["agent"],
        )
        with pytest.raises(Exception, match="collision"):
            _compile(pack, "L0_effects")


# ------------------------------------------------------------------ 4. the name branch is gone


def test_the_encoder_has_no_obs_vfs_name_branch() -> None:
    # The build path is one generic read: mirror field -> source variable -> declared scope.
    src = inspect.getsource(encoder_module.ObservationEncoder._build_observation_field_from_vfs)
    assert 'field_name != "obs_vfs"' not in src
    assert '== "obs_vfs"' not in src
    assert "declared.scope" in src
